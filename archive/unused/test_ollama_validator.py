# tests/core/test_ollama_validator.py
"""
Unit tests for core/ollama_validator.py - OllamaValidator.
Target coverage: 100% (Currently 0%)

CRITICAL: ALL LLM CALLS ARE MOCKED - NO REAL NETWORK REQUESTS.
"""
import pytest
import json
import os
from unittest.mock import Mock, MagicMock, AsyncMock, patch, ANY
from pathlib import Path

from core.ollama_validator import OllamaValidator, ollama_validator


@pytest.mark.unit
class TestOllamaValidatorInitialization:
    """Test OllamaValidator initialization."""

    def test_initialization_default_config(self):
        """Test OllamaValidator initialization with default config."""
        with patch('core.ollama_validator.aiohttp', None):
            validator = OllamaValidator()

            assert validator.model == 'mistral'
            assert validator.base_url == 'http://localhost:11434'
            assert validator.enabled is False  # Disabled when aiohttp not available
            assert validator.timeout == 30

    def test_initialization_with_env_config(self):
        """Test initialization with environment variables."""
        env_vars = {
            'OLLAMA_MODEL': 'llama2',
            'OLLAMA_URL': 'http://custom:8080',
            'OLLAMA_ENABLED': 'true',
            'OLLAMA_TIMEOUT': '60'
        }

        with patch.dict(os.environ, env_vars):
            with patch('core.ollama_validator.aiohttp', MagicMock()):
                validator = OllamaValidator()

                assert validator.model == 'llama2'
                assert validator.base_url == 'http://custom:8080'
                assert validator.enabled is True
                assert validator.timeout == 60

    def test_initialization_disabled_when_aiohttp_missing(self):
        """Test that validator is disabled when aiohttp is not available."""
        with patch('core.ollama_validator.aiohttp', None):
            with patch('core.ollama_validator.logger') as mock_logger:
                validator = OllamaValidator()

                assert validator.enabled is False
                mock_logger.warning.assert_called_once()
                assert "aiohttp not available" in mock_logger.warning.call_args[0][0]

    def test_initialization_disabled_env_var(self):
        """Test initialization with OLLAMA_ENABLED=false."""
        with patch.dict(os.environ, {'OLLAMA_ENABLED': 'false'}):
            with patch('core.ollama_validator.aiohttp', MagicMock()):
                validator = OllamaValidator()

                assert validator.enabled is False


@pytest.mark.unit
class TestValidateContentContradictions:
    """Test validate_content_contradictions method."""

    @pytest.mark.asyncio
    async def test_validate_contradictions_when_disabled(self):
        """Test contradiction validation returns empty when disabled."""
        validator = OllamaValidator()
        validator.enabled = False

        result = await validator.validate_content_contradictions(
            "Test content",
            [{"name": "plugin1"}],
            {"api_patterns": {}}
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_validate_contradictions_success(self):
        """Test successful contradiction validation (MOCKED LLM)."""
        validator = OllamaValidator()
        validator.enabled = True

        mock_response = '{"contradictions": [{"issue": "Wrong API usage", "severity": "high", "location": "code"}]}'

        with patch.object(validator, '_call_ollama', new_callable=AsyncMock, return_value=mock_response):
            result = await validator.validate_content_contradictions(
                "Test content with wrong API",
                [{"name": "pdf_plugin"}],
                {"api_patterns": {"save": ["Save", "SaveAs"]}}
            )

            assert len(result) == 1
            assert result[0]['level'] == 'error'  # high severity -> error
            assert result[0]['category'] == 'llm_contradiction'
            assert 'Wrong API usage' in result[0]['message']
            assert result[0]['source'] == 'ollama'

    @pytest.mark.asyncio
    async def test_validate_contradictions_multiple_issues(self):
        """Test handling multiple contradictions (MOCKED LLM)."""
        validator = OllamaValidator()
        validator.enabled = True

        mock_response = json.dumps({
            "contradictions": [
                {"issue": "Issue 1", "severity": "high", "location": "code"},
                {"issue": "Issue 2", "severity": "medium", "location": "text"},
                {"issue": "Issue 3", "severity": "low", "location": "yaml"}
            ]
        })

        with patch.object(validator, '_call_ollama', new_callable=AsyncMock, return_value=mock_response):
            result = await validator.validate_content_contradictions("content", [], {})

            assert len(result) == 3
            assert result[0]['level'] == 'error'    # high -> error
            assert result[1]['level'] == 'warning'  # medium -> warning
            assert result[2]['level'] == 'info'     # low -> info

    @pytest.mark.asyncio
    async def test_validate_contradictions_exception_handling(self):
        """Test exception handling during contradiction validation."""
        validator = OllamaValidator()
        validator.enabled = True

        with patch.object(validator, '_call_ollama', new_callable=AsyncMock, side_effect=Exception("Network error")):
            with patch('core.ollama_validator.logger') as mock_logger:
                result = await validator.validate_content_contradictions("content", [], {})

                assert result == []
                mock_logger.warning.assert_called_once()
                assert "contradiction validation failed" in mock_logger.warning.call_args[0][0]


@pytest.mark.unit
class TestValidateContentOmissions:
    """Test validate_content_omissions method."""

    @pytest.mark.asyncio
    async def test_validate_omissions_when_disabled(self):
        """Test omission validation returns empty when disabled."""
        validator = OllamaValidator()
        validator.enabled = False

        result = await validator.validate_content_omissions(
            "Test content",
            [{"name": "plugin1"}],
            {"validation_requirements": {}}
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_validate_omissions_success(self):
        """Test successful omission validation (MOCKED LLM)."""
        validator = OllamaValidator()
        validator.enabled = True

        mock_response = json.dumps({
            "omissions": [{
                "missing": "Error handling",
                "importance": "critical",
                "suggestion": "Add try-catch blocks"
            }]
        })

        with patch.object(validator, '_call_ollama', new_callable=AsyncMock, return_value=mock_response):
            result = await validator.validate_content_omissions(
                "Code without error handling",
                [{"name": "plugin"}],
                {"validation_requirements": {}}
            )

            assert len(result) == 1
            assert result[0]['level'] == 'error'  # critical -> error
            assert result[0]['category'] == 'llm_omission'
            assert 'Error handling' in result[0]['message']
            assert 'try-catch' in result[0]['suggestion']

    @pytest.mark.asyncio
    async def test_validate_omissions_importance_levels(self):
        """Test omission importance level mapping (MOCKED LLM)."""
        validator = OllamaValidator()
        validator.enabled = True

        mock_response = json.dumps({
            "omissions": [
                {"missing": "Critical item", "importance": "critical", "suggestion": "Fix now"},
                {"missing": "Important item", "importance": "important", "suggestion": "Fix soon"},
                {"missing": "Nice item", "importance": "nice-to-have", "suggestion": "Consider"}
            ]
        })

        with patch.object(validator, '_call_ollama', new_callable=AsyncMock, return_value=mock_response):
            result = await validator.validate_content_omissions("content", [], {})

            assert len(result) == 3
            assert result[0]['level'] == 'error'    # critical -> error
            assert result[1]['level'] == 'warning'  # important -> warning
            assert result[2]['level'] == 'info'     # nice-to-have -> info

    @pytest.mark.asyncio
    async def test_validate_omissions_exception_handling(self):
        """Test exception handling during omission validation."""
        validator = OllamaValidator()
        validator.enabled = True

        with patch.object(validator, '_call_ollama', new_callable=AsyncMock, side_effect=Exception("LLM error")):
            with patch('core.ollama_validator.logger') as mock_logger:
                result = await validator.validate_content_omissions("content", [], {})

                assert result == []
                mock_logger.warning.assert_called_once()


@pytest.mark.unit
class TestPromptBuilders:
    """Test prompt building methods."""

    def test_build_contradiction_prompt(self):
        """Test building contradiction detection prompt."""
        validator = OllamaValidator()

        content = "Sample content for testing"
        plugin_info = [{"name": "pdf_plugin", "version": "1.0"}]
        family_rules = {
            "api_patterns": {"save": ["Save", "SaveAs"]},
            "validation_requirements": {"min_length": 100}
        }

        prompt = validator._build_contradiction_prompt(content, plugin_info, family_rules)

        assert "Sample content" in prompt
        assert "pdf_plugin" in prompt
        assert "Save" in prompt
        assert "min_length" in prompt
        assert "contradictions" in prompt.lower()

    def test_build_contradiction_prompt_truncates_content(self):
        """Test that contradiction prompt truncates long content."""
        validator = OllamaValidator()

        long_content = "X" * 5000  # Very long content
        prompt = validator._build_contradiction_prompt(long_content, [], {})

        # Content should be truncated to 2000 chars
        assert len([line for line in prompt.split('\n') if 'X' in line][0]) <= 2000

    def test_build_omission_prompt(self):
        """Test building omission detection prompt."""
        validator = OllamaValidator()

        content = "Code sample"
        plugin_info = [{"name": "cells_plugin"}]
        family_rules = {
            "validation_requirements": {"error_handling": True},
            "code_quality_rules": {"forbidden_patterns": {}}
        }

        prompt = validator._build_omission_prompt(content, plugin_info, family_rules)

        assert "Code sample" in prompt
        assert "cells_plugin" in prompt
        assert "error_handling" in prompt
        assert "omissions" in prompt.lower()

    def test_build_omission_prompt_handles_missing_rules(self):
        """Test omission prompt with missing rule keys."""
        validator = OllamaValidator()

        prompt = validator._build_omission_prompt("content", [], {})

        # Should not crash with empty rules
        assert "omissions" in prompt.lower()
        assert "content" in prompt


@pytest.mark.unit
class TestCallOllama:
    """Test _call_ollama method (ALL MOCKED)."""

    @pytest.mark.asyncio
    async def test_call_ollama_success(self):
        """Test successful Ollama API call (MOCKED)."""
        validator = OllamaValidator()
        validator.enabled = True

        mock_response_data = {
            "response": "This is the LLM response",
            "model": "mistral",
            "done": True
        }

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_response_data)

        # Create async context manager
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_ctx)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('core.ollama_validator.aiohttp.ClientSession', return_value=mock_session):
            result = await validator._call_ollama("Test prompt")

            assert result == "This is the LLM response"

    @pytest.mark.asyncio
    async def test_call_ollama_when_aiohttp_missing(self):
        """Test _call_ollama when aiohttp is not available."""
        validator = OllamaValidator()

        with patch('core.ollama_validator.aiohttp', None):
            result = await validator._call_ollama("Test prompt")

            assert result == ""

    @pytest.mark.asyncio
    async def test_call_ollama_non_200_status(self):
        """Test handling non-200 response (MOCKED)."""
        validator = OllamaValidator()
        validator.enabled = True

        mock_response = AsyncMock()
        mock_response.status = 500

        # Create async context manager
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_ctx)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch('core.ollama_validator.aiohttp.ClientSession', return_value=mock_session):
            with patch('core.ollama_validator.logger') as mock_logger:
                result = await validator._call_ollama("Test prompt")

                assert result == ""
                mock_logger.warning.assert_called_once()
                assert "status 500" in mock_logger.warning.call_args[0][0]

    @pytest.mark.asyncio
    async def test_call_ollama_network_error(self):
        """Test handling network errors (MOCKED)."""
        validator = OllamaValidator()
        validator.enabled = True

        mock_session = AsyncMock()
        mock_session.post = AsyncMock(side_effect=Exception("Connection refused"))

        with patch('core.ollama_validator.aiohttp.ClientSession', return_value=mock_session):
            with patch('core.ollama_validator.logger') as mock_logger:
                result = await validator._call_ollama("Test prompt")

                assert result == ""
                mock_logger.info.assert_called_once()
                assert "not available" in mock_logger.info.call_args[0][0]

    @pytest.mark.asyncio
    async def test_call_ollama_timeout(self):
        """Test handling timeout errors (MOCKED)."""
        validator = OllamaValidator()
        validator.enabled = True
        validator.timeout = 10

        import asyncio
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch('core.ollama_validator.aiohttp.ClientSession', return_value=mock_session):
            result = await validator._call_ollama("Test prompt")

            assert result == ""


@pytest.mark.unit
class TestParseContradictionResponse:
    """Test _parse_contradiction_response method."""

    def test_parse_contradiction_valid_json(self):
        """Test parsing valid contradiction JSON response."""
        validator = OllamaValidator()

        response = '{"contradictions": [{"issue": "Test issue", "severity": "high", "location": "code"}]}'
        result = validator._parse_contradiction_response(response)

        assert len(result) == 1
        assert result[0]['level'] == 'error'
        assert result[0]['category'] == 'llm_contradiction'
        assert 'Test issue' in result[0]['message']

    def test_parse_contradiction_with_text_prefix(self):
        """Test parsing JSON with text prefix."""
        validator = OllamaValidator()

        response = 'Here is the analysis: {"contradictions": [{"issue": "Problem", "severity": "medium"}]}'
        result = validator._parse_contradiction_response(response)

        assert len(result) == 1
        assert result[0]['level'] == 'warning'  # medium -> warning

    def test_parse_contradiction_severity_mapping(self):
        """Test severity to level mapping."""
        validator = OllamaValidator()

        # Test all severity levels
        test_cases = [
            ("high", "error"),
            ("medium", "warning"),
            ("low", "info"),
            ("unknown", "info")  # Default to info (no match -> else clause)
        ]

        for severity, expected_level in test_cases:
            response = json.dumps({"contradictions": [{"issue": "Test", "severity": severity}]})
            result = validator._parse_contradiction_response(response)
            assert result[0]['level'] == expected_level

    def test_parse_contradiction_invalid_json(self):
        """Test handling invalid JSON."""
        validator = OllamaValidator()

        # Invalid JSON that can be extracted but not parsed
        result = validator._parse_contradiction_response("Invalid JSON {{{")

        # Should return empty list without crashing
        assert result == []

    def test_parse_contradiction_missing_contradictions_key(self):
        """Test response without contradictions key."""
        validator = OllamaValidator()

        response = '{"some_other_key": "value"}'
        result = validator._parse_contradiction_response(response)

        assert result == []

    def test_parse_contradiction_empty_array(self):
        """Test response with empty contradictions array."""
        validator = OllamaValidator()

        response = '{"contradictions": []}'
        result = validator._parse_contradiction_response(response)

        assert result == []


@pytest.mark.unit
class TestParseOmissionResponse:
    """Test _parse_omission_response method."""

    def test_parse_omission_valid_json(self):
        """Test parsing valid omission JSON response."""
        validator = OllamaValidator()

        response = json.dumps({
            "omissions": [{
                "missing": "Error handling",
                "importance": "critical",
                "suggestion": "Add try-catch"
            }]
        })
        result = validator._parse_omission_response(response)

        assert len(result) == 1
        assert result[0]['level'] == 'error'
        assert result[0]['category'] == 'llm_omission'
        assert 'Error handling' in result[0]['message']
        assert 'try-catch' in result[0]['suggestion']

    def test_parse_omission_importance_mapping(self):
        """Test importance to level mapping."""
        validator = OllamaValidator()

        test_cases = [
            ("critical", "error"),
            ("important", "warning"),
            ("nice-to-have", "info"),
            ("unknown", "info")  # Default to info
        ]

        for importance, expected_level in test_cases:
            response = json.dumps({
                "omissions": [{
                    "missing": "Test",
                    "importance": importance,
                    "suggestion": "Fix"
                }]
            })
            result = validator._parse_omission_response(response)
            assert result[0]['level'] == expected_level

    def test_parse_omission_with_prefix_text(self):
        """Test parsing JSON with prefix text."""
        validator = OllamaValidator()

        response = 'Analysis complete: {"omissions": [{"missing": "Item", "importance": "important", "suggestion": "Add it"}]}'
        result = validator._parse_omission_response(response)

        assert len(result) == 1
        assert result[0]['level'] == 'warning'

    def test_parse_omission_invalid_json(self):
        """Test handling invalid JSON."""
        validator = OllamaValidator()

        # Invalid JSON should return empty list
        result = validator._parse_omission_response("Not valid JSON")

        # Should return empty list without crashing
        assert result == []

    def test_parse_omission_missing_keys(self):
        """Test handling missing keys in omission objects."""
        validator = OllamaValidator()

        # Missing 'suggestion' key
        response = '{"omissions": [{"missing": "Something", "importance": "critical"}]}'
        result = validator._parse_omission_response(response)

        assert len(result) == 1
        assert 'Consider adding' in result[0]['suggestion']  # Default suggestion


@pytest.mark.unit
class TestGlobalInstance:
    """Test global ollama_validator instance."""

    def test_global_instance_exists(self):
        """Test that global ollama_validator exists."""
        from core.ollama_validator import ollama_validator

        assert ollama_validator is not None
        assert isinstance(ollama_validator, OllamaValidator)


@pytest.mark.integration
class TestOllamaValidatorIntegration:
    """Integration tests for OllamaValidator."""

    @pytest.mark.asyncio
    async def test_full_contradiction_workflow(self):
        """Test complete contradiction detection workflow (MOCKED)."""
        validator = OllamaValidator()
        validator.enabled = True

        content = """
        using Aspose.Pdf;
        Document doc = new Document();
        doc.Save("output.pdf");  // Wrong - should use SaveAs
        """

        plugin_info = [{"name": "Aspose.PDF", "version": "24.1"}]
        family_rules = {
            "api_patterns": {"save": ["SaveAs"]},
            "validation_requirements": {"min_length": 50}
        }

        mock_llm_response = json.dumps({
            "contradictions": [{
                "issue": "Using Save instead of SaveAs",
                "severity": "high",
                "location": "code"
            }]
        })

        with patch.object(validator, '_call_ollama', new_callable=AsyncMock, return_value=mock_llm_response):
            result = await validator.validate_content_contradictions(content, plugin_info, family_rules)

            assert len(result) == 1
            assert result[0]['level'] == 'error'
            assert 'SaveAs' in result[0]['message']

    @pytest.mark.asyncio
    async def test_full_omission_workflow(self):
        """Test complete omission detection workflow (MOCKED)."""
        validator = OllamaValidator()
        validator.enabled = True

        content = """
        Document doc = new Document();
        doc.Save("output.pdf");
        """

        plugin_info = [{"name": "Aspose.PDF"}]
        family_rules = {
            "validation_requirements": {"error_handling": True},
            "code_quality_rules": {"required_patterns": {"using_statements": []}}
        }

        mock_llm_response = json.dumps({
            "omissions": [
                {
                    "missing": "using statement for resource disposal",
                    "importance": "critical",
                    "suggestion": "Wrap Document in using statement"
                },
                {
                    "missing": "Error handling",
                    "importance": "important",
                    "suggestion": "Add try-catch block"
                }
            ]
        })

        with patch.object(validator, '_call_ollama', new_callable=AsyncMock, return_value=mock_llm_response):
            result = await validator.validate_content_omissions(content, plugin_info, family_rules)

            assert len(result) == 2
            assert result[0]['level'] == 'error'    # critical
            assert result[1]['level'] == 'warning'  # important
            assert any('using statement' in r['message'] for r in result)

    @pytest.mark.asyncio
    async def test_disabled_validator_no_calls(self):
        """Test that disabled validator makes no LLM calls."""
        validator = OllamaValidator()
        validator.enabled = False

        # These should all return empty without making any calls
        contradictions = await validator.validate_content_contradictions("content", [], {})
        omissions = await validator.validate_content_omissions("content", [], {})

        assert contradictions == []
        assert omissions == []
