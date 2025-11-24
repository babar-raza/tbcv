# file: tbcv/api/services/recommendation_consolidator.py
"""
Service to consolidate validation results into structured recommendations.
Deduplicates and normalizes recommendations for LLM consumption.
"""

from __future__ import annotations

import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from core.database import db_manager, Recommendation, RecommendationStatus
    from core.logging import get_logger
except ImportError:
    from core.database import db_manager, Recommendation, RecommendationStatus
    from core.logging import get_logger

logger = get_logger(__name__)


def _location_hash(location: Dict[str, Any]) -> str:
    """Generate hash for location to detect duplicates."""
    path = location.get('path', '')
    line = location.get('line', '')
    column = location.get('column', '')
    selector = location.get('selector', '')
    loc_str = f"{path}:{line}:{column}:{selector}"
    return hashlib.md5(loc_str.encode()).hexdigest()


def _determine_type(rule_id: str, suggestion: str, validation_type: str) -> str:
    """Infer recommendation type from rule_id and suggestion."""
    rule_lower = rule_id.lower()
    suggestion_lower = suggestion.lower() if suggestion else ""
    
    if 'rewrite' in rule_lower or 'rephrase' in suggestion_lower:
        return "rewrite"
    elif 'add' in rule_lower or 'insert' in suggestion_lower or 'missing' in rule_lower:
        return "add"
    elif 'remove' in rule_lower or 'delete' in suggestion_lower:
        return "remove"
    elif 'refactor' in rule_lower or 'restructure' in suggestion_lower:
        return "refactor"
    elif 'metadata' in rule_lower or 'frontmatter' in rule_lower or 'yaml' in validation_type.lower():
        return "metadata"
    elif 'format' in rule_lower or 'style' in rule_lower:
        return "format"
    else:
        return "rewrite"  # default


def _determine_selector(location: Dict[str, Any]) -> str:
    """Generate selector string from location."""
    if 'selector' in location:
        return location['selector']
    
    parts = []
    if location.get('section'):
        parts.append(location['section'])
    if location.get('line'):
        line = location['line']
        if location.get('line_end'):
            parts.append(f"body[{line}:{location['line_end']}]")
        else:
            parts.append(f"body[{line}]")
    
    return ".".join(parts) if parts else "body"


def _extract_original_content(validation_results: Dict[str, Any], location: Dict[str, Any]) -> str:
    """Extract original content from validation results."""
    # Try to find the original content in validation results
    if isinstance(validation_results, dict):
        issues = validation_results.get('issues', [])
        for issue in issues:
            if issue.get('location') == location:
                return issue.get('original_text', '')
    
    # Fallback: use location context if available
    return location.get('context', '')


def consolidate_recommendations(validation_id: str) -> List[Dict[str, Any]]:
    """
    Consolidate all validation items into structured recommendations.
    
    Args:
        validation_id: ID of the validation to consolidate
        
    Returns:
        List of consolidated recommendation dictionaries
    """
    try:
        # Get validation result
        validation = db_manager.get_validation_result(validation_id)
        if not validation:
            logger.warning(f"Validation {validation_id} not found")
            return []
        
        # Get validation results
        validation_results = validation.validation_results or {}
        
        # Check if we already have recommendations
        existing_recs = db_manager.list_recommendations(validation_id=validation_id)
        if existing_recs:
            logger.info(f"Found {len(existing_recs)} existing recommendations for validation {validation_id}")
            return [rec.to_dict() for rec in existing_recs]
        
        # Build recommendations from validation results
        recommendations = []
        seen_hashes = set()
        
        # Parse validation results to extract issues
        issues = []
        if isinstance(validation_results, dict):
            # Extract issues from different validation types
            for validator_name, validator_results in validation_results.items():
                if isinstance(validator_results, dict):
                    validator_issues = validator_results.get('issues', [])
                    if isinstance(validator_issues, list):
                        for issue in validator_issues:
                            issue['validator'] = validator_name
                            issues.append(issue)
        
        logger.info(f"Extracted {len(issues)} issues from validation results for {validation_id}")
        
        if not issues:
            logger.warning(f"No issues found in validation results for {validation_id}. Validation results structure: {list(validation_results.keys()) if isinstance(validation_results, dict) else type(validation_results)}")
        
        # Convert issues to recommendations
        for issue in issues:
            rule_id = issue.get('rule_id', issue.get('type', issue.get('category', 'unknown')))
            location = issue.get('location', {})
            # Check all possible suggestion field names
            suggestion = (
                issue.get('suggestion') or
                issue.get('fix') or
                issue.get('fix_suggestion') or
                ''
            )

            if not suggestion:
                continue  # Skip issues without suggestions
            
            # Generate deduplication hash
            loc_hash = _location_hash(location)
            dedup_key = f"{rule_id}:{loc_hash}:{suggestion[:50]}"
            dedup_hash = hashlib.md5(dedup_key.encode()).hexdigest()
            
            if dedup_hash in seen_hashes:
                continue  # Skip duplicates
            
            seen_hashes.add(dedup_hash)
            
            # Determine recommendation type
            validator_name = issue.get('validator', '')
            rec_type = _determine_type(rule_id, suggestion, validator_name)
            
            # Build target selector
            selector = _determine_selector(location)
            
            # Extract original content
            original = _extract_original_content(validation_results, location)
            
            # Determine severity/priority from various field names
            severity = (
                issue.get('severity') or
                issue.get('level') or
                issue.get('priority') or
                'medium'
            )

            # Build recommendation
            rec_data = {
                "validation_id": validation_id,
                "type": rec_type,
                "title": issue.get('message', f"Fix {rule_id}"),
                "description": issue.get('description', issue.get('message', '')),
                "original_content": original,
                "proposed_content": suggestion,
                "diff": f"- {original}\n+ {suggestion}" if original else f"+ {suggestion}",
                "confidence": float(issue.get('confidence', issue.get('severity_score', 0.5))),
                "priority": severity,
                "status": RecommendationStatus.PENDING,
                "metadata": {
                    "source": {
                        "validation_id": validation_id,
                        "item_id": issue.get('id', ''),
                        "rule_id": rule_id,
                        "validator": validator_name,
                        "category": issue.get('category', ''),
                    },
                    "target": {
                        "path": validation.file_path,
                        "selector": selector,
                    },
                    "rationale": issue.get('rationale', issue.get('reason', issue.get('reasoning', ''))),
                    "location": location,
                    "auto_fixable": issue.get('auto_fixable', False),
                }
            }
            
            # Save recommendation
            try:
                recommendation = db_manager.create_recommendation(**rec_data)
                recommendations.append(recommendation.to_dict())
                logger.debug(f"Created recommendation {recommendation.id} for validation {validation_id}")
            except Exception as e:
                logger.error(f"Failed to create recommendation: {e}")
                continue
        
        if not recommendations:
            logger.warning(f"No recommendations could be generated for validation {validation_id}. Total issues: {len(issues)}, Issues with suggestions: {sum(1 for i in issues if i.get('suggestion') or i.get('fix'))}")
        
        logger.info(f"Consolidated {len(recommendations)} recommendations for validation {validation_id}")
        return recommendations
        
    except Exception:
        logger.exception(f"Failed to consolidate recommendations for validation {validation_id}")
        return []


def rebuild_recommendations(validation_id: str) -> List[Dict[str, Any]]:
    """
    Force rebuild recommendations by deleting existing ones and regenerating.
    
    Args:
        validation_id: ID of the validation to rebuild
        
    Returns:
        List of rebuilt recommendation dictionaries
    """
    try:
        # Delete existing recommendations
        existing_recs = db_manager.list_recommendations(validation_id=validation_id)
        for rec in existing_recs:
            try:
                db_manager.delete_recommendation(rec.id)
            except Exception as e:
                logger.error(f"Failed to delete recommendation {rec.id}: {e}")
        
        logger.info(f"Deleted {len(existing_recs)} existing recommendations for validation {validation_id}")
        
        # Regenerate
        return consolidate_recommendations(validation_id)
        
    except Exception:
        logger.exception(f"Failed to rebuild recommendations for validation {validation_id}")
        return []
