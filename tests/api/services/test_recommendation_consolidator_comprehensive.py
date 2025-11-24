# file: tbcv/tests/api/services/test_recommendation_consolidator_comprehensive.py
"""
Comprehensive tests for recommendation consolidation.
Tests that all validator notes are properly converted to recommendations.
"""

import pytest
import json
from datetime import datetime
from api.services.recommendation_consolidator import consolidate_recommendations, rebuild_recommendations
from core.database import db_manager


@pytest.fixture
def validation_with_multiple_validators(db_session):
    """Create a validation result with issues from multiple validators."""
    # Create a validation with issues from various validators
    validation_results = {
        "content_validation": {
            "issues": [
                {
                    "rule_id": "yaml-date-format",
                    "message": "Field 'date' should be a string in YYYY-MM-DD format",
                    "suggestion": "Change date format to YYYY-MM-DD",
                    "severity": "warning",
                    "location": {"line": 5}
                },
                {
                    "rule_id": "md-blank-lines",
                    "message": "Multiple consecutive blank lines",
                    "suggestion": "Remove extra blank lines",
                    "severity": "info",
                    "location": {"line": 61}
                }
            ]
        },
        "llm_validation": {
            "issues": [
                {
                    "category": "missing_plugin",
                    "message": "Document Converter plugin is required but not mentioned",
                    "fix_suggestion": "Add mention of Document Converter plugin in prerequisites",
                    "level": "high",
                    "plugin_id": "document_converter",
                    "auto_fixable": True
                },
                {
                    "category": "missing_plugin",
                    "message": "HTML Converter plugin is required",
                    "fix_suggestion": "Add HTML Converter plugin to prerequisites",
                    "level": "medium",
                    "plugin_id": "html_converter",
                    "auto_fixable": True
                },
                {
                    "category": "incorrect_plugin",
                    "message": "Detected 'words_save_operations' is not a real plugin",
                    "fix_suggestion": "Replace with 'Word Processor'",
                    "level": "warning",
                    "auto_fixable": False
                }
            ]
        },
        "fuzzy_detection": {
            "issues": [
                {
                    "type": "terminology",
                    "message": "Inconsistent plugin naming",
                    "fix": "Use consistent plugin names throughout document",
                    "priority": "low"
                }
            ]
        }
    }

    validation = db_manager.create_validation_result(
        workflow_id="test-workflow-id",
        file_path="test-document.md",
        rules_applied=["yaml", "markdown", "llm"],
        validation_results=validation_results,
        notes="Test validation with multiple validators",
        severity="warning",
        status="fail"
    )

    return validation


def test_all_validator_notes_included(validation_with_multiple_validators):
    """Test that notes from all validators are included in recommendations."""
    validation_id = validation_with_multiple_validators.id

    # Consolidate recommendations
    recs = consolidate_recommendations(validation_id)

    # Should have recommendations from all validators
    assert len(recs) >= 6, f"Expected at least 6 recommendations, got {len(recs)}"

    # Get validator sources from recommendations
    validators_found = set()
    for rec in recs:
        metadata = rec.get('metadata', {})
        source = metadata.get('source', {})
        validator = source.get('validator', '')
        if validator:
            validators_found.add(validator)

    # Should have recommendations from all three validators
    assert 'content_validation' in validators_found, "Missing content_validation recommendations"
    assert 'llm_validation' in validators_found, "Missing llm_validation recommendations"
    assert 'fuzzy_detection' in validators_found, "Missing fuzzy_detection recommendations"


def test_llm_validation_fix_suggestion_field(validation_with_multiple_validators):
    """Test that LLM validator's 'fix_suggestion' field is properly extracted."""
    validation_id = validation_with_multiple_validators.id

    recs = consolidate_recommendations(validation_id)

    # Find LLM validation recommendations
    llm_recs = [
        rec for rec in recs
        if rec.get('metadata', {}).get('source', {}).get('validator') == 'llm_validation'
    ]

    assert len(llm_recs) == 3, f"Expected 3 LLM recommendations, got {len(llm_recs)}"

    # Check that fix_suggestions are present in the proposed_content
    messages = [rec.get('title', '') for rec in llm_recs]
    assert any('Document Converter' in msg for msg in messages), \
        "Missing Document Converter recommendation"
    assert any('HTML Converter' in msg for msg in messages), \
        "Missing HTML Converter recommendation"
    assert any('words_save_operations' in msg for msg in messages), \
        "Missing incorrect plugin recommendation"


def test_severity_level_mapping(validation_with_multiple_validators):
    """Test that LLM validator's 'level' field is properly mapped to priority/severity."""
    validation_id = validation_with_multiple_validators.id

    recs = consolidate_recommendations(validation_id)

    # Find the high-priority LLM recommendation
    high_priority_recs = [
        rec for rec in recs
        if rec.get('priority') == 'high' and
        rec.get('metadata', {}).get('source', {}).get('validator') == 'llm_validation'
    ]

    assert len(high_priority_recs) == 1, \
        f"Expected 1 high-priority LLM recommendation, got {len(high_priority_recs)}"

    # Should be the Document Converter one
    assert 'Document Converter' in high_priority_recs[0].get('title', ''), \
        "High-priority recommendation should be about Document Converter"


def test_different_suggestion_field_names():
    """Test that different suggestion field names are all handled correctly."""
    validation_results = {
        "validator_a": {
            "issues": [
                {"message": "Issue A", "suggestion": "Fix A", "severity": "high"}
            ]
        },
        "validator_b": {
            "issues": [
                {"message": "Issue B", "fix": "Fix B", "severity": "medium"}
            ]
        },
        "validator_c": {
            "issues": [
                {"message": "Issue C", "fix_suggestion": "Fix C", "level": "low"}
            ]
        }
    }

    validation = db_manager.create_validation_result(
        workflow_id="test-workflow-id",
        file_path="test-field-names.md",
        rules_applied=["a", "b", "c"],
        validation_results=validation_results,
        notes="Test different suggestion field names",
        severity="warning",
        status="fail"
    )

    recs = consolidate_recommendations(validation.id)

    # Should have all three recommendations
    assert len(recs) == 3, f"Expected 3 recommendations, got {len(recs)}"

    # Check that all fixes are present
    titles = [rec.get('title', '') for rec in recs]
    assert any('Issue A' in title for title in titles), "Missing Issue A"
    assert any('Issue B' in title for title in titles), "Missing Issue B"
    assert any('Issue C' in title for title in titles), "Missing Issue C"


def test_recommendation_deduplication():
    """Test that duplicate recommendations are properly deduplicated."""
    validation_results = {
        "validator_1": {
            "issues": [
                {
                    "rule_id": "same-issue",
                    "message": "Duplicate issue",
                    "suggestion": "Fix this",
                    "location": {"line": 10}
                }
            ]
        },
        "validator_2": {
            "issues": [
                {
                    "rule_id": "same-issue",
                    "message": "Duplicate issue",
                    "suggestion": "Fix this",
                    "location": {"line": 10}
                }
            ]
        }
    }

    validation = db_manager.create_validation_result(
        workflow_id="test-workflow-id",
        file_path="test-dedup.md",
        rules_applied=["1", "2"],
        validation_results=validation_results,
        notes="Test deduplication",
        severity="warning",
        status="fail"
    )

    recs = consolidate_recommendations(validation.id)

    # Should only have one recommendation (deduplicated)
    assert len(recs) == 1, f"Expected 1 deduplicated recommendation, got {len(recs)}"


def test_rebuild_recommendations(validation_with_multiple_validators):
    """Test that rebuild_recommendations properly deletes and recreates recommendations."""
    validation_id = validation_with_multiple_validators.id

    # First consolidation
    recs1 = consolidate_recommendations(validation_id)
    initial_count = len(recs1)
    initial_ids = {rec['id'] for rec in recs1}

    # Rebuild should delete old and create new
    recs2 = rebuild_recommendations(validation_id)
    rebuilt_count = len(recs2)
    rebuilt_ids = {rec['id'] for rec in recs2}

    # Should have same number of recommendations
    assert rebuilt_count == initial_count, \
        f"Rebuilt count {rebuilt_count} != initial count {initial_count}"

    # Should have different IDs (new recommendations created)
    assert rebuilt_ids != initial_ids, "Rebuild should create new recommendation IDs"


def test_metadata_preservation():
    """Test that important metadata from validators is preserved in recommendations."""
    validation_results = {
        "llm_validation": {
            "issues": [
                {
                    "category": "missing_plugin",
                    "message": "Plugin X required",
                    "fix_suggestion": "Add Plugin X",
                    "level": "high",
                    "plugin_id": "plugin_x",
                    "auto_fixable": True,
                    "reasoning": "Code uses Plugin X features"
                }
            ]
        }
    }

    validation = db_manager.create_validation_result(
        workflow_id="test-workflow-id",
        file_path="test-metadata.md",
        rules_applied=["llm"],
        validation_results=validation_results,
        notes="Test metadata preservation",
        severity="high",
        status="fail"
    )

    recs = consolidate_recommendations(validation.id)

    assert len(recs) == 1
    rec = recs[0]
    metadata = rec.get('metadata', {})

    # Check metadata preservation
    assert metadata.get('source', {}).get('category') == 'missing_plugin'
    assert metadata.get('source', {}).get('validator') == 'llm_validation'
    assert metadata.get('auto_fixable') is True
    assert metadata.get('rationale') == 'Code uses Plugin X features'


def test_no_recommendations_for_passing_validation():
    """Test that passing validations don't generate recommendations."""
    validation_results = {
        "content_validation": {
            "status": "pass",
            "issues": []
        }
    }

    validation = db_manager.create_validation_result(
        workflow_id="test-workflow-id",
        file_path="test-passing.md",
        rules_applied=["content"],
        validation_results=validation_results,
        notes="All checks passed",
        severity="info",
        status="pass"
    )

    recs = consolidate_recommendations(validation.id)

    # Should have no recommendations for passing validation
    assert len(recs) == 0, f"Expected 0 recommendations for passing validation, got {len(recs)}"


def test_skip_issues_without_suggestions():
    """Test that issues without suggestion/fix/fix_suggestion fields are skipped."""
    validation_results = {
        "validator_x": {
            "issues": [
                {
                    "rule_id": "some-rule",
                    "message": "This issue has no fix suggestion",
                    "severity": "medium"
                    # Note: no suggestion, fix, or fix_suggestion field
                }
            ]
        }
    }

    validation = db_manager.create_validation_result(
        workflow_id="test-workflow-id",
        file_path="test-no-suggestion.md",
        rules_applied=["x"],
        validation_results=validation_results,
        notes="Test skipping issues without suggestions",
        severity="medium",
        status="fail"
    )

    recs = consolidate_recommendations(validation.id)

    # Should skip issues without suggestions
    assert len(recs) == 0, f"Expected 0 recommendations for issues without suggestions, got {len(recs)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
