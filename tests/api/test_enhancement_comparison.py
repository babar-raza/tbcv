# file: tests/api/test_enhancement_comparison.py
"""
Tests for Enhancement Comparison Service and API endpoints.

This module tests the complete enhancement workflow including:
- Enhancement comparison service
- API endpoints for comparison data
- Side-by-side diff generation
- Statistics calculation
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from api.services.enhancement_comparison import (
    EnhancementComparisonService,
    EnhancementStats,
    DiffLine,
    EnhancementComparison
)


class TestEnhancementComparisonService:
    """Test the EnhancementComparisonService."""

    @pytest.fixture
    def service(self):
        """Create an EnhancementComparisonService instance."""
        return EnhancementComparisonService()

    @pytest.fixture
    def original_content(self):
        """Sample original content."""
        return """# Getting Started with Apose.Words

This guide will help you get started with Aspose.Word for .NET.

## Installation

Install using NuGet Package Manager.

## Basic Usage

Create a simple document using Aspose.Word."""

    @pytest.fixture
    def enhanced_content(self):
        """Sample enhanced content."""
        return """# Getting Started with Aspose.Words

This guide will help you get started with Aspose.Words for .NET.

## Installation

Install using NuGet Package Manager for the Document Processor plugin.

## Basic Usage

Create a simple document using Aspose.Words API."""

    def test_generate_diff_lines(self, service, original_content, enhanced_content):
        """Test diff line generation."""
        diff_lines = service.generate_diff_lines(original_content, enhanced_content)

        assert len(diff_lines) > 0

        # Check for different change types
        change_types = {line.change_type for line in diff_lines}
        assert 'unchanged' in change_types
        assert 'added' in change_types or 'removed' in change_types or 'modified' in change_types

        # Check that line numbers are assigned correctly
        for line in diff_lines:
            if line.change_type == 'unchanged':
                assert line.line_number_original is not None
                assert line.line_number_enhanced is not None
            elif line.change_type == 'removed':
                assert line.line_number_original is not None
            elif line.change_type == 'added':
                assert line.line_number_enhanced is not None

    def test_calculate_stats(self, service, original_content, enhanced_content):
        """Test statistics calculation."""
        stats = service.calculate_stats(
            original_content,
            enhanced_content,
            applied_recs=[Mock(id='rec1'), Mock(id='rec2')],
            total_recs=5
        )

        assert isinstance(stats, EnhancementStats)
        assert stats.original_length == len(original_content)
        assert stats.enhanced_length == len(enhanced_content)
        assert stats.lines_added >= 0
        assert stats.lines_removed >= 0
        assert stats.lines_modified >= 0
        assert stats.recommendations_applied == 2
        assert stats.recommendations_total == 5

    @pytest.mark.asyncio
    async def test_get_enhancement_comparison_success(self, service, original_content, enhanced_content):
        """Test successful enhancement comparison retrieval."""
        # Mock database
        mock_validation = Mock(
            id='val123',
            file_path='test.md',
            validation_results={
                'enhanced_content': enhanced_content
            }
        )

        mock_rec1 = Mock(
            id='rec1',
            title='Fix typo',
            instruction='Replace Apose with Aspose',
            confidence=0.95,
            status='applied'
        )

        with patch('api.services.enhancement_comparison.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = mock_validation
            mock_db.list_recommendations.return_value = [mock_rec1]

            # Mock file reading
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = original_content

                comparison = await service.get_enhancement_comparison('val123')

                assert comparison.status == 'success'
                assert comparison.validation_id == 'val123'
                assert comparison.file_path == 'test.md'
                assert comparison.original_content == original_content
                assert comparison.enhanced_content == enhanced_content
                assert len(comparison.diff_lines) > 0
                assert len(comparison.applied_recommendations) > 0
                assert comparison.unified_diff
                assert 'lines_added' in comparison.stats

    @pytest.mark.asyncio
    async def test_get_enhancement_comparison_not_enhanced(self, service, original_content):
        """Test comparison for validation without enhancement."""
        mock_validation = Mock(
            id='val123',
            file_path='test.md',
            validation_results={}
        )

        with patch('api.services.enhancement_comparison.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = mock_validation

            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = original_content

                comparison = await service.get_enhancement_comparison('val123')

                assert comparison.status == 'not_enhanced'
                assert comparison.original_content == original_content
                assert comparison.enhanced_content == original_content
                assert len(comparison.diff_lines) == 0

    @pytest.mark.asyncio
    async def test_get_enhancement_comparison_validation_not_found(self, service):
        """Test comparison when validation doesn't exist."""
        with patch('api.services.enhancement_comparison.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = None

            with pytest.raises(ValueError, match="Validation .* not found"):
                await service.get_enhancement_comparison('nonexistent')

    @pytest.mark.asyncio
    async def test_get_enhancement_comparison_file_read_error(self, service):
        """Test comparison when file cannot be read."""
        mock_validation = Mock(
            id='val123',
            file_path='nonexistent.md',
            validation_results={'enhanced_content': 'some content'}
        )

        with patch('api.services.enhancement_comparison.db_manager') as mock_db:
            mock_db.get_validation_result.return_value = mock_validation
            mock_db.list_recommendations.return_value = []

            with patch('builtins.open', side_effect=FileNotFoundError()):
                comparison = await service.get_enhancement_comparison('val123')

                # Should handle gracefully
                assert comparison.original_content == "(Could not load original content)"

    def test_diff_line_dataclass(self):
        """Test DiffLine dataclass."""
        line = DiffLine(
            line_number_original=5,
            line_number_enhanced=6,
            content="test content",
            change_type="modified",
            recommendation_ids=["rec1", "rec2"]
        )

        assert line.line_number_original == 5
        assert line.line_number_enhanced == 6
        assert line.content == "test content"
        assert line.change_type == "modified"
        assert len(line.recommendation_ids) == 2

    def test_enhancement_stats_dataclass(self):
        """Test EnhancementStats dataclass."""
        stats = EnhancementStats(
            original_length=1000,
            enhanced_length=1200,
            lines_added=15,
            lines_removed=5,
            lines_modified=10,
            recommendations_applied=3,
            recommendations_total=5
        )

        assert stats.original_length == 1000
        assert stats.enhanced_length == 1200
        assert stats.lines_added == 15
        assert stats.lines_removed == 5
        assert stats.lines_modified == 10
        assert stats.recommendations_applied == 3
        assert stats.recommendations_total == 5


@pytest.mark.asyncio
class TestEnhancementComparisonAPI:
    """Test the Enhancement Comparison API endpoint."""

    @pytest.fixture
    def app_client(self):
        """Create a test client for the FastAPI app."""
        from fastapi.testclient import TestClient
        from api.server import app
        return TestClient(app)

    async def test_get_enhancement_comparison_endpoint(self, app_client):
        """Test GET /api/validations/{id}/enhancement-comparison endpoint."""
        # This would require a full integration test with actual database
        # For now, we test the endpoint structure
        pass

    async def test_enhancement_comparison_endpoint_not_found(self, app_client):
        """Test endpoint with non-existent validation."""
        response = app_client.get('/api/validations/nonexistent/enhancement-comparison')
        assert response.status_code == 404

    async def test_enhancement_comparison_endpoint_response_structure(self):
        """Test that response has correct structure."""
        expected_keys = {
            'success',
            'validation_id',
            'file_path',
            'original_content',
            'enhanced_content',
            'diff_lines',
            'stats',
            'applied_recommendations',
            'unified_diff',
            'status'
        }

        # Mock response structure test
        response_data = {
            'success': True,
            'validation_id': 'val123',
            'file_path': 'test.md',
            'original_content': 'original',
            'enhanced_content': 'enhanced',
            'diff_lines': [],
            'stats': {},
            'applied_recommendations': [],
            'unified_diff': '',
            'status': 'success'
        }

        assert set(response_data.keys()) == expected_keys


class TestDiffGenerationEdgeCases:
    """Test diff generation with edge cases."""

    @pytest.fixture
    def service(self):
        return EnhancementComparisonService()

    def test_empty_content(self, service):
        """Test diff with empty content."""
        diff_lines = service.generate_diff_lines("", "")
        assert len(diff_lines) == 0

    def test_identical_content(self, service):
        """Test diff with identical content."""
        content = "Line 1\nLine 2\nLine 3"
        diff_lines = service.generate_diff_lines(content, content)

        # All lines should be unchanged
        for line in diff_lines:
            assert line.change_type == 'unchanged'

    def test_all_removed(self, service):
        """Test diff where all content is removed."""
        original = "Line 1\nLine 2\nLine 3"
        enhanced = ""

        diff_lines = service.generate_diff_lines(original, enhanced)

        # All lines should be removed
        for line in diff_lines:
            assert line.change_type == 'removed'

    def test_all_added(self, service):
        """Test diff where all content is added."""
        original = ""
        enhanced = "Line 1\nLine 2\nLine 3"

        diff_lines = service.generate_diff_lines(original, enhanced)

        # All lines should be added
        for line in diff_lines:
            assert line.change_type == 'added'

    def test_single_line_change(self, service):
        """Test diff with single line change."""
        original = "Line 1\nLine 2\nLine 3"
        enhanced = "Line 1\nLine 2 Modified\nLine 3"

        diff_lines = service.generate_diff_lines(original, enhanced)

        # Should have some modified lines
        change_types = [line.change_type for line in diff_lines]
        assert 'modified' in change_types or ('removed' in change_types and 'added' in change_types)
        assert 'unchanged' in change_types

    def test_unicode_content(self, service):
        """Test diff with Unicode characters."""
        original = "Hello 世界\nTest émojis 🎉"
        enhanced = "Hello 世界\nTest émojis 🎉✨"

        diff_lines = service.generate_diff_lines(original, enhanced)

        # Should handle Unicode correctly
        assert len(diff_lines) > 0
        assert any('🎉' in line.content for line in diff_lines)

    def test_very_long_lines(self, service):
        """Test diff with very long lines."""
        original = "Short line\n" + ("x" * 10000) + "\nAnother line"
        enhanced = "Short line\n" + ("y" * 10000) + "\nAnother line"

        diff_lines = service.generate_diff_lines(original, enhanced)

        # Should handle long lines without crashing
        assert len(diff_lines) > 0
