# file: api/services/enhancement_comparison.py
"""
Enhancement Comparison Service

Provides comprehensive comparison data for before/after content enhancement,
including side-by-side diffs, statistics, and applied recommendations tracking.
"""

from typing import Dict, Any, List, Optional, Tuple
import difflib
from dataclasses import dataclass, asdict
from datetime import datetime
from core.logging import get_logger
from core.database import db_manager

logger = get_logger(__name__)


@dataclass
class EnhancementStats:
    """Statistics about the enhancement operation."""
    original_length: int
    enhanced_length: int
    lines_added: int
    lines_removed: int
    lines_modified: int
    recommendations_applied: int
    recommendations_total: int
    enhancement_timestamp: Optional[str] = None


@dataclass
class DiffLine:
    """A single line in the diff view."""
    line_number_original: Optional[int]
    line_number_enhanced: Optional[int]
    content: str
    change_type: str  # 'added', 'removed', 'modified', 'unchanged'
    recommendation_ids: List[str]  # IDs of recommendations that caused this change


@dataclass
class EnhancementComparison:
    """Complete comparison data for enhancement visualization."""
    validation_id: str
    file_path: str
    original_content: str
    enhanced_content: str
    diff_lines: List[Dict[str, Any]]  # DiffLine as dict
    stats: Dict[str, Any]  # EnhancementStats as dict
    applied_recommendations: List[Dict[str, Any]]
    unified_diff: str
    status: str  # 'success', 'error', 'not_enhanced'
    error_message: Optional[str] = None


class EnhancementComparisonService:
    """Service for generating enhancement comparison data."""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def generate_diff_lines(
        self,
        original: str,
        enhanced: str,
        recommendation_map: Optional[Dict[int, List[str]]] = None
    ) -> List[DiffLine]:
        """
        Generate line-by-line diff with change types.

        Args:
            original: Original content
            enhanced: Enhanced content
            recommendation_map: Optional mapping of line numbers to recommendation IDs

        Returns:
            List of DiffLine objects
        """
        original_lines = original.splitlines(keepends=False)
        enhanced_lines = enhanced.splitlines(keepends=False)

        diff_lines = []

        # Use SequenceMatcher for detailed diff
        matcher = difflib.SequenceMatcher(None, original_lines, enhanced_lines)

        orig_line_num = 1
        enh_line_num = 1

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Unchanged lines
                for i in range(i1, i2):
                    diff_lines.append(DiffLine(
                        line_number_original=orig_line_num,
                        line_number_enhanced=enh_line_num,
                        content=original_lines[i],
                        change_type='unchanged',
                        recommendation_ids=[]
                    ))
                    orig_line_num += 1
                    enh_line_num += 1

            elif tag == 'delete':
                # Removed lines
                for i in range(i1, i2):
                    recs = recommendation_map.get(orig_line_num, []) if recommendation_map else []
                    diff_lines.append(DiffLine(
                        line_number_original=orig_line_num,
                        line_number_enhanced=None,
                        content=original_lines[i],
                        change_type='removed',
                        recommendation_ids=recs
                    ))
                    orig_line_num += 1

            elif tag == 'insert':
                # Added lines
                for j in range(j1, j2):
                    recs = recommendation_map.get(enh_line_num, []) if recommendation_map else []
                    diff_lines.append(DiffLine(
                        line_number_original=None,
                        line_number_enhanced=enh_line_num,
                        content=enhanced_lines[j],
                        change_type='added',
                        recommendation_ids=recs
                    ))
                    enh_line_num += 1

            elif tag == 'replace':
                # Modified lines (delete old, add new)
                for i in range(i1, i2):
                    recs = recommendation_map.get(orig_line_num, []) if recommendation_map else []
                    diff_lines.append(DiffLine(
                        line_number_original=orig_line_num,
                        line_number_enhanced=None,
                        content=original_lines[i],
                        change_type='modified',
                        recommendation_ids=recs
                    ))
                    orig_line_num += 1

                for j in range(j1, j2):
                    recs = recommendation_map.get(enh_line_num, []) if recommendation_map else []
                    diff_lines.append(DiffLine(
                        line_number_original=None,
                        line_number_enhanced=enh_line_num,
                        content=enhanced_lines[j],
                        change_type='modified',
                        recommendation_ids=recs
                    ))
                    enh_line_num += 1

        return diff_lines

    def calculate_stats(
        self,
        original: str,
        enhanced: str,
        applied_recs: List[Any],
        total_recs: int
    ) -> EnhancementStats:
        """
        Calculate enhancement statistics.

        Args:
            original: Original content
            enhanced: Enhanced content
            applied_recs: List of applied recommendations
            total_recs: Total number of recommendations

        Returns:
            EnhancementStats object
        """
        original_lines = original.splitlines()
        enhanced_lines = enhanced.splitlines()

        # Count changes using difflib
        matcher = difflib.SequenceMatcher(None, original_lines, enhanced_lines)

        lines_added = 0
        lines_removed = 0
        lines_modified = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'delete':
                lines_removed += (i2 - i1)
            elif tag == 'insert':
                lines_added += (j2 - j1)
            elif tag == 'replace':
                lines_modified += max(i2 - i1, j2 - j1)

        return EnhancementStats(
            original_length=len(original),
            enhanced_length=len(enhanced),
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_modified=lines_modified,
            recommendations_applied=len(applied_recs),
            recommendations_total=total_recs,
            enhancement_timestamp=datetime.utcnow().isoformat()
        )

    async def get_enhancement_comparison(
        self,
        validation_id: str
    ) -> EnhancementComparison:
        """
        Get comprehensive enhancement comparison data for a validation.

        Args:
            validation_id: Validation result ID

        Returns:
            EnhancementComparison object with all comparison data

        Raises:
            ValueError: If validation not found or not enhanced
        """
        try:
            # Get validation
            validation = db_manager.get_validation_result(validation_id)
            if not validation:
                raise ValueError(f"Validation {validation_id} not found")

            # Get original content from file
            try:
                with open(validation.file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            except Exception as e:
                self.logger.error(f"Failed to read original file {validation.file_path}: {e}")
                original_content = "(Could not load original content)"

            # Check for enhanced content in validation results
            enhanced_content = None
            if validation.validation_results and isinstance(validation.validation_results, dict):
                enhanced_content = validation.validation_results.get('enhanced_content')

            # If no enhancement data, return not-enhanced status
            if not enhanced_content:
                return EnhancementComparison(
                    validation_id=validation_id,
                    file_path=validation.file_path,
                    original_content=original_content,
                    enhanced_content=original_content,
                    diff_lines=[],
                    stats=asdict(EnhancementStats(
                        original_length=len(original_content),
                        enhanced_length=len(original_content),
                        lines_added=0,
                        lines_removed=0,
                        lines_modified=0,
                        recommendations_applied=0,
                        recommendations_total=0
                    )),
                    applied_recommendations=[],
                    unified_diff="",
                    status="not_enhanced"
                )

            # Get recommendations for this validation
            all_recommendations = db_manager.list_recommendations(
                validation_id=validation_id,
                limit=1000
            )

            applied_recommendations = [
                rec for rec in all_recommendations
                if rec.status in ['applied', 'actioned', 'accepted']
            ]

            # Generate unified diff
            unified_diff = '\n'.join(difflib.unified_diff(
                original_content.splitlines(keepends=False),
                enhanced_content.splitlines(keepends=False),
                fromfile='original',
                tofile='enhanced',
                lineterm=''
            ))

            # Generate line-by-line diff
            diff_lines = self.generate_diff_lines(original_content, enhanced_content)

            # Calculate stats
            stats = self.calculate_stats(
                original_content,
                enhanced_content,
                applied_recommendations,
                len(all_recommendations)
            )

            # Convert recommendations to dict format
            applied_recs_dict = [
                {
                    'id': rec.id,
                    'title': rec.title,
                    'instruction': rec.instruction if hasattr(rec, 'instruction') else rec.title,
                    'confidence': rec.confidence,
                    'status': rec.status
                }
                for rec in applied_recommendations
            ]

            return EnhancementComparison(
                validation_id=validation_id,
                file_path=validation.file_path,
                original_content=original_content,
                enhanced_content=enhanced_content,
                diff_lines=[asdict(line) for line in diff_lines],
                stats=asdict(stats),
                applied_recommendations=applied_recs_dict,
                unified_diff=unified_diff,
                status="success"
            )

        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to generate enhancement comparison: {e}", exc_info=True)
            return EnhancementComparison(
                validation_id=validation_id,
                file_path="unknown",
                original_content="",
                enhanced_content="",
                diff_lines=[],
                stats={},
                applied_recommendations=[],
                unified_diff="",
                status="error",
                error_message=str(e)
            )


# Singleton instance
_service_instance: Optional[EnhancementComparisonService] = None


def get_enhancement_comparison_service() -> EnhancementComparisonService:
    """Get the singleton instance of EnhancementComparisonService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = EnhancementComparisonService()
    return _service_instance
