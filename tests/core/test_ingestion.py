# tests/core/test_ingestion.py
"""
Unit tests for core/ingestion.py - MarkdownIngestion.
Target coverage: 100% (Currently 0%)
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from core.ingestion import MarkdownIngestion


@pytest.mark.unit
class TestMarkdownIngestion:
    """Test MarkdownIngestion class."""

    def test_initialization(self, db_manager):
        """Test MarkdownIngestion initialization."""
        with patch('core.ingestion.RuleManager') as mock_rule_mgr:
            ingestion = MarkdownIngestion(db_manager, mock_rule_mgr)

            assert ingestion.db_manager == db_manager
            assert ingestion.rule_manager == mock_rule_mgr

    def test_ingest_folder_nonexistent(self, db_manager):
        """Test ingesting a nonexistent folder raises error."""
        with patch('core.ingestion.RuleManager') as mock_rule_mgr:
            ingestion = MarkdownIngestion(db_manager, mock_rule_mgr)

            with pytest.raises(ValueError, match="Folder does not exist"):
                ingestion.ingest_folder("/nonexistent/path")

    def test_ingest_folder_empty(self, db_manager, temp_dir):
        """Test ingesting an empty folder."""
        with patch('core.ingestion.RuleManager') as mock_rule_mgr:
            with patch('core.ingestion.list_markdown_files', return_value=[]):
                ingestion = MarkdownIngestion(db_manager, mock_rule_mgr)

                result = ingestion.ingest_folder(str(temp_dir))

                assert result["files_found"] == 0
                assert result["files_processed"] == 0
                assert result["files_failed"] == 0
                assert result["validations_created"] == 0
                assert "start_time" in result
                assert "end_time" in result
                assert "duration_seconds" in result

    def test_ingest_folder_single_file(self, db_manager, temp_dir, sample_markdown):
        """Test ingesting a folder with a single markdown file."""
        # Create a test file
        test_file = temp_dir / "test.md"
        test_file.write_text(sample_markdown)

        with patch('core.ingestion.RuleManager') as mock_rule_mgr:
            with patch('core.ingestion.list_markdown_files', return_value=[test_file]):
                with patch('core.ingestion.read_text', return_value=sample_markdown):
                    with patch('core.ingestion.family_detector') as mock_family:
                        mock_family.detect_family.return_value = "words"

                        ingestion = MarkdownIngestion(db_manager, mock_rule_mgr)
                        result = ingestion.ingest_folder(str(temp_dir))

                        assert result["files_found"] == 1
                        assert result["files_processed"] == 1
                        assert result["files_failed"] == 0
                        assert len(result["file_results"]) == 1
                        assert "words" in result["families_detected"]

    def test_ingest_folder_multiple_files(self, db_manager, temp_dir):
        """Test ingesting multiple files."""
        test_files = [
            temp_dir / "file1.md",
            temp_dir / "file2.md",
            temp_dir / "file3.md"
        ]
        for f in test_files:
            f.write_text("# Test")

        with patch('core.ingestion.RuleManager') as mock_rule_mgr:
            with patch('core.ingestion.list_markdown_files', return_value=test_files):
                with patch('core.ingestion.read_text', return_value="# Test"):
                    with patch('core.ingestion.family_detector') as mock_family:
                        mock_family.detect_family.return_value = "words"

                        ingestion = MarkdownIngestion(db_manager, mock_rule_mgr)
                        result = ingestion.ingest_folder(str(temp_dir))

                        assert result["files_found"] == 3
                        assert result["files_processed"] == 3
                        assert result["files_failed"] == 0

    def test_ingest_folder_with_errors(self, db_manager, temp_dir):
        """Test ingestion handles file processing errors."""
        test_file = temp_dir / "error.md"
        test_file.write_text("# Test")

        with patch('core.ingestion.RuleManager') as mock_rule_mgr:
            with patch('core.ingestion.list_markdown_files', return_value=[test_file]):
                with patch('core.ingestion.read_text', side_effect=Exception("Read error")):
                    ingestion = MarkdownIngestion(db_manager, mock_rule_mgr)
                    result = ingestion.ingest_folder(str(temp_dir))

                    assert result["files_found"] == 1
                    assert result["files_failed"] == 1
                    assert len(result["errors"]) == 1
                    assert "Read error" in result["errors"][0]["error"]

    def test_ingest_folder_recursive_vs_nonrecursive(self, db_manager, temp_dir):
        """Test recursive vs non-recursive scanning."""
        # Create nested structure
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (temp_dir / "root.md").write_text("# Root")
        (subdir / "nested.md").write_text("# Nested")

        with patch('core.ingestion.RuleManager') as mock_rule_mgr:
            ingestion = MarkdownIngestion(db_manager, mock_rule_mgr)

            # Test recursive
            with patch('core.ingestion.list_markdown_files') as mock_list:
                mock_list.return_value = [temp_dir / "root.md", subdir / "nested.md"]
                with patch.object(ingestion, '_process_file', return_value={"validation_created": False}):
                    result_recursive = ingestion.ingest_folder(str(temp_dir), recursive=True)
                    mock_list.assert_called_with(Path(temp_dir), recursive=True)

            # Test non-recursive
            with patch('core.ingestion.list_markdown_files') as mock_list:
                mock_list.return_value = [temp_dir / "root.md"]
                with patch.object(ingestion, '_process_file', return_value={"validation_created": False}):
                    result_nonrecursive = ingestion.ingest_folder(str(temp_dir), recursive=False)
                    mock_list.assert_called_with(Path(temp_dir), recursive=False)

    def test_process_file_with_yaml(self, db_manager, temp_dir):
        """Test processing a file with YAML frontmatter."""
        test_file = temp_dir / "with_yaml.md"
        content_with_yaml = """---
title: Test
family: words
---
# Content"""
        test_file.write_text(content_with_yaml)

        with patch('core.ingestion.RuleManager') as mock_rule_mgr:
            with patch('core.ingestion.read_text', return_value=content_with_yaml):
                with patch('core.ingestion.family_detector') as mock_family:
                    mock_family.detect_family.return_value = "words"

                    ingestion = MarkdownIngestion(db_manager, mock_rule_mgr)

                    with patch.object(ingestion, '_parse_content', return_value=({"title": "Test"}, "# Content")):
                        with patch.object(ingestion, '_validate_yaml', return_value={"valid": True}):
                            with patch.object(ingestion, '_validate_markdown', return_value={"valid": True}):
                                with patch.object(ingestion, '_create_validation_record', return_value="val_123"):
                                    result = ingestion._process_file(test_file)

                                    assert result["file_path"] == str(test_file)
                                    assert result["family"] == "words"
                                    assert result["yaml_valid"] is True
                                    assert result["markdown_valid"] is True
                                    assert result["validation_created"] is True
                                    assert result["validation_id"] == "val_123"

    def test_process_file_without_yaml(self, db_manager, temp_dir):
        """Test processing a file without YAML frontmatter."""
        test_file = temp_dir / "no_yaml.md"
        content = "# Just Markdown"
        test_file.write_text(content)

        with patch('core.ingestion.RuleManager') as mock_rule_mgr:
            with patch('core.ingestion.read_text', return_value=content):
                with patch('core.ingestion.family_detector') as mock_family:
                    mock_family.detect_family.return_value = "words"

                    ingestion = MarkdownIngestion(db_manager, mock_rule_mgr)

                    with patch.object(ingestion, '_parse_content', return_value=(None, "# Just Markdown")):
                        with patch.object(ingestion, '_validate_markdown', return_value={"valid": True}):
                            with patch.object(ingestion, '_create_validation_record', return_value="val_456"):
                                result = ingestion._process_file(test_file)

                                assert result["yaml_valid"] is False
                                assert result["markdown_valid"] is True

    def test_process_file_handles_error(self, db_manager, temp_dir):
        """Test that file processing errors are captured."""
        test_file = temp_dir / "error.md"
        test_file.write_text("# Test")

        with patch('core.ingestion.RuleManager') as mock_rule_mgr:
            with patch('core.ingestion.read_text', side_effect=IOError("Cannot read file")):
                ingestion = MarkdownIngestion(db_manager, mock_rule_mgr)
                result = ingestion._process_file(test_file)

                assert result["error"] is not None
                assert "Cannot read file" in result["error"]
                assert result["validation_created"] is False

    def test_families_detected_aggregation(self, db_manager, temp_dir):
        """Test that families are aggregated correctly."""
        files = [temp_dir / f"file{i}.md" for i in range(5)]
        for f in files:
            f.write_text("# Test")

        families = ["words", "cells", "words", "pdf", "words"]

        with patch('core.ingestion.RuleManager') as mock_rule_mgr:
            with patch('core.ingestion.list_markdown_files', return_value=files):
                with patch('core.ingestion.read_text', return_value="# Test"):
                    with patch('core.ingestion.family_detector') as mock_family:
                        mock_family.detect_family.side_effect = families

                        ingestion = MarkdownIngestion(db_manager, mock_rule_mgr)
                        result = ingestion.ingest_folder(str(temp_dir))

                        assert result["families_detected"]["words"] == 3
                        assert result["families_detected"]["cells"] == 1
                        assert result["families_detected"]["pdf"] == 1

    def test_validation_record_creation_error(self, db_manager, temp_dir):
        """Test handling of validation record creation errors."""
        test_file = temp_dir / "test.md"
        test_file.write_text("# Test")

        with patch('core.ingestion.RuleManager') as mock_rule_mgr:
            with patch('core.ingestion.read_text', return_value="# Test"):
                with patch('core.ingestion.family_detector') as mock_family:
                    mock_family.detect_family.return_value = "words"

                    ingestion = MarkdownIngestion(db_manager, mock_rule_mgr)

                    with patch.object(ingestion, '_parse_content', return_value=(None, "# Test")):
                        with patch.object(ingestion, '_validate_markdown', return_value={"valid": True}):
                            with patch.object(ingestion, '_create_validation_record', side_effect=Exception("DB Error")):
                                result = ingestion._process_file(test_file)

                                assert result["validation_created"] is False
                                assert "DB Error" in result["error"]


@pytest.mark.integration
class TestMarkdownIngestionIntegration:
    """Integration tests for MarkdownIngestion."""

    def test_full_ingestion_workflow(self, db_manager, sample_files_dir):
        """Test complete ingestion workflow with real files."""
        with patch('core.ingestion.RuleManager') as mock_rule_mgr:
            with patch('core.ingestion.list_markdown_files') as mock_list:
                # Mock file listing
                files = list(sample_files_dir.glob("*.md"))
                mock_list.return_value = files

                with patch('core.ingestion.family_detector') as mock_family:
                    mock_family.detect_family.return_value = "words"

                    ingestion = MarkdownIngestion(db_manager, mock_rule_mgr)
                    result = ingestion.ingest_folder(str(sample_files_dir))

                    assert result["files_found"] == len(files)
                    assert result["files_processed"] >= 0
                    assert "duration_seconds" in result
                    assert result["duration_seconds"] >= 0
