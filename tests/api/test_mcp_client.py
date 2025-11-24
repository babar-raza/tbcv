"""
Tests for MCP client simulation fixes.

Tests cover:
- Recommendation application (fix for no-op replacement bug)
- Content enhancement
- Simulation mode functionality
"""

import pytest
from api.services.mcp_client import MCPClient


class TestMCPClientSimulation:
    """Tests for MCP client simulation mode."""

    @pytest.fixture
    def mcp_client(self):
        """Create MCP client instance."""
        return MCPClient()

    def test_simulate_response_apply_recommendations(self, mcp_client):
        """Simulation should apply recommendations correctly."""
        content = "The old text that needs to be updated."

        recommendations = [
            {
                "original_content": "old text",
                "proposed_content": "new text"
            }
        ]

        request = {
            "task": "apply_recommendations",
            "inputs": {
                "content": content,
                "recommendations": recommendations
            }
        }

        result = mcp_client._simulate_response(request)

        assert result["success"] is True
        assert "result" in result
        assert "content" in result["result"]

        # Check that the replacement actually happened
        enhanced_content = result["result"]["content"]
        assert "new text" in enhanced_content
        assert "old text" not in enhanced_content

    def test_simulate_response_multiple_recommendations(self, mcp_client):
        """Simulation should apply multiple recommendations."""
        content = "First item and second item need changes."

        recommendations = [
            {
                "original_content": "First",
                "proposed_content": "1st"
            },
            {
                "original_content": "second",
                "proposed_content": "2nd"
            }
        ]

        request = {
            "task": "apply_recommendations",
            "inputs": {
                "content": content,
                "recommendations": recommendations
            }
        }

        result = mcp_client._simulate_response(request)
        enhanced_content = result["result"]["content"]

        assert "1st" in enhanced_content
        assert "2nd" in enhanced_content
        assert "First" not in enhanced_content
        assert "second" not in enhanced_content
        assert result["result"]["applied_count"] == 2

    def test_simulate_response_no_op_bug_fixed(self, mcp_client):
        """
        Test that the no-op bug is fixed.
        Previously the code was: replace(proposed, proposed, 1)
        Which is a no-op. Now it should be: replace(original, proposed, 1)
        """
        content = "Original text here"

        recommendations = [
            {
                "original_content": "Original",
                "proposed_content": "Updated"
            }
        ]

        request = {
            "task": "apply_recommendations",
            "inputs": {
                "content": content,
                "recommendations": recommendations
            }
        }

        result = mcp_client._simulate_response(request)
        enhanced_content = result["result"]["content"]

        # Verify the bug is fixed: content should actually change
        assert enhanced_content != content
        assert "Updated" in enhanced_content
        assert "Original" not in enhanced_content

    def test_simulate_response_proposed_only(self, mcp_client):
        """Test recommendations with proposed content only (additions)."""
        content = "Existing content."

        recommendations = [
            {
                "proposed_content": "New addition"
            }
        ]

        request = {
            "task": "apply_recommendations",
            "inputs": {
                "content": content,
                "recommendations": recommendations
            }
        }

        result = mcp_client._simulate_response(request)
        enhanced_content = result["result"]["content"]

        # Should append the new content
        assert "Existing content." in enhanced_content
        assert "New addition" in enhanced_content
        assert result["result"]["applied_count"] == 1

    def test_simulate_response_empty_recommendations(self, mcp_client):
        """Test with empty recommendations list."""
        content = "Original content"

        request = {
            "task": "apply_recommendations",
            "inputs": {
                "content": content,
                "recommendations": []
            }
        }

        result = mcp_client._simulate_response(request)

        assert result["success"] is True
        assert result["result"]["content"] == content
        assert result["result"]["applied_count"] == 0

    def test_simulate_response_original_not_found(self, mcp_client):
        """Test recommendations where original content not found in text."""
        content = "Some text here"

        recommendations = [
            {
                "original_content": "nonexistent text",
                "proposed_content": "replacement"
            }
        ]

        request = {
            "task": "apply_recommendations",
            "inputs": {
                "content": content,
                "recommendations": recommendations
            }
        }

        result = mcp_client._simulate_response(request)
        enhanced_content = result["result"]["content"]

        # Content should remain unchanged
        assert enhanced_content == content
        assert result["result"]["applied_count"] == 0

    def test_simulate_response_partial_matches(self, mcp_client):
        """Test with some matching and some non-matching recommendations."""
        content = "First item, second item, third item"

        recommendations = [
            {
                "original_content": "First",
                "proposed_content": "1st"
            },
            {
                "original_content": "nonexistent",
                "proposed_content": "replacement"
            },
            {
                "original_content": "third",
                "proposed_content": "3rd"
            }
        ]

        request = {
            "task": "apply_recommendations",
            "inputs": {
                "content": content,
                "recommendations": recommendations
            }
        }

        result = mcp_client._simulate_response(request)
        enhanced_content = result["result"]["content"]

        assert "1st" in enhanced_content
        assert "3rd" in enhanced_content
        assert "second" in enhanced_content  # unchanged
        assert result["result"]["applied_count"] == 2

    def test_simulate_response_validate_content_task(self, mcp_client):
        """Test validation task simulation."""
        request = {
            "task": "validate_content"
        }

        result = mcp_client._simulate_response(request)

        assert result["success"] is True
        assert "result" in result
        assert result["result"]["status"] == "pass"

    def test_simulate_response_unknown_task(self, mcp_client):
        """Test with unknown task."""
        request = {
            "task": "unknown_task"
        }

        result = mcp_client._simulate_response(request)

        assert result["success"] is False
        assert "error" in result

    def test_recommendation_with_both_formats(self, mcp_client):
        """Test that both original_content and original are supported."""
        content = "Test content here"

        # Test with 'original' key
        recommendations_1 = [
            {
                "original": "Test",
                "proposed": "Sample"
            }
        ]

        request_1 = {
            "task": "apply_recommendations",
            "inputs": {
                "content": content,
                "recommendations": recommendations_1
            }
        }

        result_1 = mcp_client._simulate_response(request_1)
        assert "Sample" in result_1["result"]["content"]

        # Test with 'original_content' key
        recommendations_2 = [
            {
                "original_content": "content",
                "proposed_content": "material"
            }
        ]

        request_2 = {
            "task": "apply_recommendations",
            "inputs": {
                "content": content,
                "recommendations": recommendations_2
            }
        }

        result_2 = mcp_client._simulate_response(request_2)
        assert "material" in result_2["result"]["content"]

    def test_replacement_only_first_occurrence(self, mcp_client):
        """Test that replacement only affects first occurrence."""
        content = "test test test"

        recommendations = [
            {
                "original_content": "test",
                "proposed_content": "demo"
            }
        ]

        request = {
            "task": "apply_recommendations",
            "inputs": {
                "content": content,
                "recommendations": recommendations
            }
        }

        result = mcp_client._simulate_response(request)
        enhanced_content = result["result"]["content"]

        # Only first occurrence should be replaced
        assert enhanced_content.count("demo") == 1
        assert enhanced_content.count("test") == 2

    def test_complex_recommendation_scenario(self, mcp_client):
        """Test complex scenario with multiple types of recommendations."""
        content = """
        # Documentation

        This is the old introduction that needs updating.
        Some content in the middle.
        Old conclusion here.
        """

        recommendations = [
            {
                "original_content": "old introduction",
                "proposed_content": "new introduction"
            },
            {
                "original_content": "Old conclusion",
                "proposed_content": "New conclusion"
            },
            {
                "proposed_content": "\nAdditional notes section"
            }
        ]

        request = {
            "task": "apply_recommendations",
            "inputs": {
                "content": content,
                "recommendations": recommendations
            }
        }

        result = mcp_client._simulate_response(request)
        enhanced_content = result["result"]["content"]

        assert "new introduction" in enhanced_content
        assert "New conclusion" in enhanced_content
        assert "Additional notes section" in enhanced_content
        assert result["result"]["applied_count"] == 3


class TestMCPClientIntegration:
    """Integration tests for MCP client."""

    @pytest.fixture
    def mcp_client(self):
        """Create MCP client instance."""
        return MCPClient()

    @pytest.mark.asyncio
    async def test_apply_recommendations_async(self, mcp_client):
        """Test async apply_recommendations method."""
        content = "Original text"
        recommendations = [
            {
                "original_content": "Original",
                "proposed_content": "Modified"
            }
        ]

        result = await mcp_client.apply_recommendations(
            content=content,
            recommendations=recommendations
        )

        # Result is wrapped in success/result structure
        assert result["success"] is True
        assert "result" in result
        assert "content" in result["result"]

    @pytest.mark.asyncio
    async def test_validate_content_async(self, mcp_client):
        """Test async validate_content method."""
        result = await mcp_client.validate_content(
            content="Test content",
            file_path="test.md"
        )

        # Result is wrapped in success/result structure
        assert result["success"] is True
        assert "result" in result
        assert "issues" in result["result"]
        assert "status" in result["result"]
