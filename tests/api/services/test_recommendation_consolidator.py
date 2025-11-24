# tests/api/services/test_recommendation_consolidator.py
"""
Unit tests for api/services/recommendation_consolidator.py - Recommendation consolidation service.
Target coverage: 90%+ (Currently 0%)
"""
import pytest
import hashlib
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List

from api.services.recommendation_consolidator import (
    _location_hash,
    _determine_type,
    _determine_selector,
    _extract_original_content,
    consolidate_recommendations,
    rebuild_recommendations
)
from core.database import RecommendationStatus


@pytest.mark.unit
class TestLocationHash:
    """Test _location_hash helper function."""

    def test_location_hash_all_fields(self):
        """Test hash generation with all fields present."""
        location = {
            "path": "file.md",
            "line": 10,
            "column": 5,
            "selector": "body[10]"
        }

        hash_result = _location_hash(location)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 32  # MD5 hash length

    def test_location_hash_minimal_fields(self):
        """Test hash generation with minimal fields."""
        location = {"path": "file.md"}

        hash_result = _location_hash(location)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 32

    def test_location_hash_empty_dict(self):
        """Test hash generation with empty dict."""
        location = {}

        hash_result = _location_hash(location)

        assert isinstance(hash_result, str)
        # Should generate hash for empty strings
        expected = hashlib.md5(":::".encode()).hexdigest()
        assert hash_result == expected

    def test_location_hash_deterministic(self):
        """Test that same location produces same hash."""
        location = {"path": "test.md", "line": 5}

        hash1 = _location_hash(location)
        hash2 = _location_hash(location)

        assert hash1 == hash2

    def test_location_hash_different_locations(self):
        """Test that different locations produce different hashes."""
        location1 = {"path": "file1.md", "line": 1}
        location2 = {"path": "file2.md", "line": 1}

        hash1 = _location_hash(location1)
        hash2 = _location_hash(location2)

        assert hash1 != hash2


@pytest.mark.unit
class TestDetermineType:
    """Test _determine_type helper function."""

    def test_determine_type_rewrite(self):
        """Test type determination for rewrite."""
        assert _determine_type("rewrite_rule", "", "") == "rewrite"
        assert _determine_type("some_rule", "rephrase this", "") == "rewrite"

    def test_determine_type_add(self):
        """Test type determination for add."""
        assert _determine_type("add_section", "", "") == "add"
        assert _determine_type("missing_content", "", "") == "add"
        assert _determine_type("rule", "insert text here", "") == "add"

    def test_determine_type_remove(self):
        """Test type determination for remove."""
        assert _determine_type("remove_duplicate", "", "") == "remove"
        assert _determine_type("rule", "delete this section", "") == "remove"

    def test_determine_type_refactor(self):
        """Test type determination for refactor."""
        assert _determine_type("refactor_code", "", "") == "refactor"
        assert _determine_type("rule", "restructure the content", "") == "refactor"

    def test_determine_type_metadata(self):
        """Test type determination for metadata."""
        assert _determine_type("metadata_rule", "", "") == "metadata"
        assert _determine_type("frontmatter_issue", "", "") == "metadata"
        assert _determine_type("rule", "", "yaml_validator") == "metadata"

    def test_determine_type_format(self):
        """Test type determination for format."""
        assert _determine_type("format_rule", "", "") == "format"
        assert _determine_type("style_issue", "", "") == "format"

    def test_determine_type_default(self):
        """Test type determination defaults to rewrite."""
        assert _determine_type("unknown_rule", "", "") == "rewrite"
        assert _determine_type("rule", "unknown suggestion", "") == "rewrite"

    def test_determine_type_case_insensitive(self):
        """Test type determination is case insensitive."""
        assert _determine_type("REWRITE_RULE", "", "") == "rewrite"
        assert _determine_type("rule", "REPHRASE THIS", "") == "rewrite"


@pytest.mark.unit
class TestDetermineSelector:
    """Test _determine_selector helper function."""

    def test_selector_from_location(self):
        """Test selector extraction when present in location."""
        location = {"selector": "body[5:10]"}

        selector = _determine_selector(location)

        assert selector == "body[5:10]"

    def test_selector_from_section_and_line(self):
        """Test selector generation from section and line."""
        location = {"section": "intro", "line": 5}

        selector = _determine_selector(location)

        assert selector == "intro.body[5]"

    def test_selector_from_line_range(self):
        """Test selector generation from line range."""
        location = {"line": 10, "line_end": 15}

        selector = _determine_selector(location)

        assert selector == "body[10:15]"

    def test_selector_from_line_only(self):
        """Test selector generation from single line."""
        location = {"line": 7}

        selector = _determine_selector(location)

        assert selector == "body[7]"

    def test_selector_from_section_only(self):
        """Test selector generation from section only."""
        location = {"section": "conclusion"}

        selector = _determine_selector(location)

        assert selector == "conclusion"

    def test_selector_default(self):
        """Test default selector when no location info."""
        location = {}

        selector = _determine_selector(location)

        assert selector == "body"


@pytest.mark.unit
class TestExtractOriginalContent:
    """Test _extract_original_content helper function."""

    def test_extract_from_issues(self):
        """Test extracting original content from issues."""
        location = {"line": 5}
        validation_results = {
            "issues": [
                {"location": {"line": 5}, "original_text": "old content"}
            ]
        }

        content = _extract_original_content(validation_results, location)

        assert content == "old content"

    def test_extract_from_context(self):
        """Test extracting original content from location context."""
        location = {"line": 5, "context": "context content"}
        validation_results = {"issues": []}

        content = _extract_original_content(validation_results, location)

        assert content == "context content"

    def test_extract_no_match(self):
        """Test extraction when no match found."""
        location = {"line": 5}
        validation_results = {
            "issues": [
                {"location": {"line": 10}, "original_text": "other content"}
            ]
        }

        content = _extract_original_content(validation_results, location)

        assert content == ""

    def test_extract_non_dict_validation_results(self):
        """Test extraction with non-dict validation results."""
        location = {"context": "fallback"}
        validation_results = "not a dict"

        content = _extract_original_content(validation_results, location)

        assert content == "fallback"


@pytest.mark.unit
class TestConsolidateRecommendations:
    """Test consolidate_recommendations function."""

    def test_validation_not_found(self):
        """Test consolidation when validation doesn't exist."""
        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = None

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = consolidate_recommendations("nonexistent_id")

            assert result == []
            mock_db.get_validation_result.assert_called_once_with("nonexistent_id")

    def test_existing_recommendations_returned(self):
        """Test that existing recommendations are returned without regeneration."""
        mock_validation = MagicMock()
        mock_validation.validation_results = {}

        mock_rec1 = MagicMock()
        mock_rec1.to_dict.return_value = {"id": "rec1", "title": "Fix 1"}
        mock_rec2 = MagicMock()
        mock_rec2.to_dict.return_value = {"id": "rec2", "title": "Fix 2"}

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = [mock_rec1, mock_rec2]

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = consolidate_recommendations("val_123")

            assert len(result) == 2
            assert result[0]["id"] == "rec1"
            assert result[1]["id"] == "rec2"

    def test_no_issues_in_validation_results(self):
        """Test consolidation with no issues in validation results."""
        mock_validation = MagicMock()
        mock_validation.validation_results = {"confidence": 0.9, "issues": []}

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = consolidate_recommendations("val_123")

            assert result == []

    def test_create_recommendations_from_issues(self):
        """Test creating recommendations from validation issues."""
        mock_validation = MagicMock()
        mock_validation.file_path = "test.md"
        mock_validation.validation_results = {
            "validator1": {
                "issues": [
                    {
                        "rule_id": "rewrite_rule",
                        "message": "Fix this content",
                        "description": "Content needs improvement",
                        "location": {"line": 5, "path": "test.md"},
                        "suggestion": "Improved content",
                        "confidence": 0.8,
                        "severity": "high"
                    }
                ]
            }
        }

        mock_rec = MagicMock()
        mock_rec.id = "rec_new"
        mock_rec.to_dict.return_value = {"id": "rec_new", "title": "Fix this content"}

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []
        mock_db.create_recommendation.return_value = mock_rec

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = consolidate_recommendations("val_123")

            assert len(result) == 1
            assert result[0]["id"] == "rec_new"
            mock_db.create_recommendation.assert_called_once()

    def test_skip_issues_without_suggestions(self):
        """Test that issues without suggestions are skipped."""
        mock_validation = MagicMock()
        mock_validation.file_path = "test.md"
        mock_validation.validation_results = {
            "validator1": {
                "issues": [
                    {
                        "rule_id": "error_rule",
                        "message": "Error found",
                        "location": {"line": 5}
                        # No suggestion or fix field
                    }
                ]
            }
        }

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = consolidate_recommendations("val_123")

            assert result == []
            mock_db.create_recommendation.assert_not_called()

    def test_deduplication(self):
        """Test that duplicate recommendations are filtered out."""
        mock_validation = MagicMock()
        mock_validation.file_path = "test.md"
        mock_validation.validation_results = {
            "validator1": {
                "issues": [
                    {
                        "rule_id": "same_rule",
                        "message": "Fix this",
                        "location": {"line": 5, "path": "test.md"},
                        "suggestion": "Same fix"
                    },
                    {
                        "rule_id": "same_rule",
                        "message": "Fix this",
                        "location": {"line": 5, "path": "test.md"},
                        "suggestion": "Same fix"
                    }
                ]
            }
        }

        mock_rec = MagicMock()
        mock_rec.id = "rec1"
        mock_rec.to_dict.return_value = {"id": "rec1"}

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []
        mock_db.create_recommendation.return_value = mock_rec

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = consolidate_recommendations("val_123")

            # Should only create one recommendation (duplicate filtered)
            assert len(result) == 1
            assert mock_db.create_recommendation.call_count == 1

    def test_use_fix_field_if_no_suggestion(self):
        """Test that 'fix' field is used if 'suggestion' is missing."""
        mock_validation = MagicMock()
        mock_validation.file_path = "test.md"
        mock_validation.validation_results = {
            "validator1": {
                "issues": [
                    {
                        "rule_id": "rule1",
                        "message": "Fix needed",
                        "location": {"line": 5},
                        "fix": "This is the fix"  # Using 'fix' instead of 'suggestion'
                    }
                ]
            }
        }

        mock_rec = MagicMock()
        mock_rec.id = "rec1"
        mock_rec.to_dict.return_value = {"id": "rec1"}

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []
        mock_db.create_recommendation.return_value = mock_rec

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = consolidate_recommendations("val_123")

            assert len(result) == 1

    def test_error_creating_recommendation_continues(self):
        """Test that errors creating individual recommendations don't stop processing."""
        mock_validation = MagicMock()
        mock_validation.file_path = "test.md"
        mock_validation.validation_results = {
            "validator1": {
                "issues": [
                    {
                        "rule_id": "rule1",
                        "message": "Fix 1",
                        "location": {"line": 5},
                        "suggestion": "Fix A"
                    },
                    {
                        "rule_id": "rule2",
                        "message": "Fix 2",
                        "location": {"line": 10},
                        "suggestion": "Fix B"
                    }
                ]
            }
        }

        mock_rec2 = MagicMock()
        mock_rec2.id = "rec2"
        mock_rec2.to_dict.return_value = {"id": "rec2"}

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []

        # First call fails, second succeeds
        mock_db.create_recommendation.side_effect = [
            Exception("Database error"),
            mock_rec2
        ]

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = consolidate_recommendations("val_123")

            # Should have one recommendation (second one succeeded)
            assert len(result) == 1
            assert result[0]["id"] == "rec2"

    def test_non_dict_validator_results_skipped(self):
        """Test that non-dict validator results are skipped."""
        mock_validation = MagicMock()
        mock_validation.file_path = "test.md"
        mock_validation.validation_results = {
            "validator1": "not a dict",
            "validator2": {
                "issues": [
                    {
                        "rule_id": "rule1",
                        "message": "Fix",
                        "location": {"line": 5},
                        "suggestion": "Fix it"
                    }
                ]
            }
        }

        mock_rec = MagicMock()
        mock_rec.id = "rec1"
        mock_rec.to_dict.return_value = {"id": "rec1"}

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []
        mock_db.create_recommendation.return_value = mock_rec

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = consolidate_recommendations("val_123")

            # Should only process validator2
            assert len(result) == 1

    def test_exception_handling(self):
        """Test that exceptions are caught and logged."""
        mock_db = MagicMock()
        mock_db.get_validation_result.side_effect = Exception("Database error")

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = consolidate_recommendations("val_123")

            assert result == []


@pytest.mark.unit
class TestRebuildRecommendations:
    """Test rebuild_recommendations function."""

    def test_rebuild_deletes_and_recreates(self):
        """Test that rebuild deletes existing recs and creates new ones."""
        # Existing recommendations to delete
        mock_rec1 = MagicMock()
        mock_rec1.id = "old_rec1"
        mock_rec2 = MagicMock()
        mock_rec2.id = "old_rec2"

        # New validation and recommendation
        mock_validation = MagicMock()
        mock_validation.file_path = "test.md"
        mock_validation.validation_results = {
            "validator1": {
                "issues": [
                    {
                        "rule_id": "rule1",
                        "message": "New fix",
                        "location": {"line": 5},
                        "suggestion": "New content"
                    }
                ]
            }
        }

        mock_new_rec = MagicMock()
        mock_new_rec.id = "new_rec1"
        mock_new_rec.to_dict.return_value = {"id": "new_rec1", "title": "New fix"}

        mock_db = MagicMock()
        mock_db.list_recommendations.side_effect = [
            [mock_rec1, mock_rec2],  # First call returns existing
            []  # Second call (in consolidate) returns empty
        ]
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.create_recommendation.return_value = mock_new_rec

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = rebuild_recommendations("val_123")

            # Should have deleted old recommendations
            assert mock_db.delete_recommendation.call_count == 2
            mock_db.delete_recommendation.assert_any_call("old_rec1")
            mock_db.delete_recommendation.assert_any_call("old_rec2")

            # Should have created new recommendations
            assert len(result) == 1
            assert result[0]["id"] == "new_rec1"

    def test_rebuild_handles_delete_errors(self):
        """Test that rebuild continues even if deletion fails."""
        mock_rec1 = MagicMock()
        mock_rec1.id = "rec1"
        mock_rec2 = MagicMock()
        mock_rec2.id = "rec2"

        mock_validation = MagicMock()
        mock_validation.file_path = "test.md"
        mock_validation.validation_results = {}

        mock_db = MagicMock()
        mock_db.list_recommendations.side_effect = [
            [mock_rec1, mock_rec2],
            []
        ]
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.delete_recommendation.side_effect = [
            Exception("Delete failed"),
            None  # Second delete succeeds
        ]

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = rebuild_recommendations("val_123")

            # Should have attempted to delete both
            assert mock_db.delete_recommendation.call_count == 2

    def test_rebuild_exception_handling(self):
        """Test that rebuild handles exceptions gracefully."""
        mock_db = MagicMock()
        mock_db.list_recommendations.side_effect = Exception("Database error")

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = rebuild_recommendations("val_123")

            assert result == []


@pytest.mark.integration
class TestRecommendationConsolidatorIntegration:
    """Integration tests for recommendation consolidator."""

    def test_full_consolidation_workflow(self):
        """Test complete consolidation workflow."""
        mock_validation = MagicMock()
        mock_validation.file_path = "test.md"
        mock_validation.validation_results = {
            "style_validator": {
                "issues": [
                    {
                        "rule_id": "rewrite_passive",
                        "message": "Use active voice",
                        "description": "Passive voice detected",
                        "location": {"line": 5, "path": "test.md"},
                        "suggestion": "Changed to active voice",
                        "original_text": "It was done",
                        "confidence": 0.9,
                        "severity": "medium"
                    }
                ]
            },
            "grammar_validator": {
                "issues": [
                    {
                        "rule_id": "add_comma",
                        "message": "Add missing comma",
                        "location": {"line": 10, "section": "intro"},
                        "suggestion": "Text, with comma",
                        "confidence": 0.95,
                        "priority": "high"
                    }
                ]
            }
        }

        mock_rec1 = MagicMock()
        mock_rec1.id = "rec1"
        mock_rec1.to_dict.return_value = {
            "id": "rec1",
            "type": "rewrite",
            "title": "Use active voice"
        }

        mock_rec2 = MagicMock()
        mock_rec2.id = "rec2"
        mock_rec2.to_dict.return_value = {
            "id": "rec2",
            "type": "add",
            "title": "Add missing comma"
        }

        mock_db = MagicMock()
        mock_db.get_validation_result.return_value = mock_validation
        mock_db.list_recommendations.return_value = []
        mock_db.create_recommendation.side_effect = [mock_rec1, mock_rec2]

        with patch('api.services.recommendation_consolidator.db_manager', mock_db):
            result = consolidate_recommendations("val_123")

            assert len(result) == 2
            assert result[0]["type"] == "rewrite"
            assert result[1]["type"] == "add"
            assert mock_db.create_recommendation.call_count == 2
