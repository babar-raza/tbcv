# tests/core/test_ollama.py
"""
Unit tests for core/ollama.py - Ollama LLM integration.
Target coverage: 95% (Currently 0%)

⚠️  CRITICAL: ALL LLM CALLS MUST BE MOCKED - NO REAL NETWORK CALLS
"""
import pytest
import json
from unittest.mock import Mock, MagicMock, patch, mock_open
from urllib.error import URLError, HTTPError

from core.ollama import (
    Ollama,
    OllamaError,
    OllamaConnectionError,
    OllamaAPIError
)


@pytest.mark.unit
class TestOllamaExceptions:
    """Test Ollama exception classes."""

    def test_ollama_error(self):
        """Test OllamaError exception."""
        error = OllamaError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_ollama_connection_error(self):
        """Test OllamaConnectionError exception."""
        error = OllamaConnectionError("Connection failed")
        assert str(error) == "Connection failed"
        assert isinstance(error, OllamaError)

    def test_ollama_api_error(self):
        """Test OllamaAPIError exception."""
        error = OllamaAPIError("API error")
        assert str(error) == "API error"
        assert isinstance(error, OllamaError)


@pytest.mark.unit
class TestOllamaInitialization:
    """Test Ollama client initialization."""

    def test_default_initialization(self):
        """Test Ollama initialization with defaults."""
        with patch.dict('os.environ', {
            'OLLAMA_BASE_URL': 'http://localhost:11434',
            'OLLAMA_MODEL': 'mistral',
            'OLLAMA_TIMEOUT': '30',
            'OLLAMA_ENABLED': 'true'
        }):
            client = Ollama()

            assert client.base_url == 'http://localhost:11434/'
            assert client.model == 'mistral'
            assert client.timeout == 30
            assert client.enabled is True

    def test_custom_initialization(self):
        """Test Ollama initialization with custom values."""
        client = Ollama(
            base_url='http://custom:8080',
            model='llama2',
            timeout=60,
            enabled=False
        )

        assert client.base_url == 'http://custom:8080/'
        assert client.model == 'llama2'
        assert client.timeout == 60
        assert client.enabled is False

    def test_base_url_trailing_slash(self):
        """Test that base_url gets trailing slash added."""
        client = Ollama(base_url='http://localhost:11434')
        assert client.base_url.endswith('/')

        client2 = Ollama(base_url='http://localhost:11434/')
        assert client2.base_url.endswith('/')

    def test_enabled_from_env_true(self):
        """Test enabled flag from environment variable (true)."""
        with patch.dict('os.environ', {'OLLAMA_ENABLED': 'true'}):
            client = Ollama()
            assert client.enabled is True

    def test_enabled_from_env_false(self):
        """Test enabled flag from environment variable (false)."""
        with patch.dict('os.environ', {'OLLAMA_ENABLED': 'false'}):
            client = Ollama()
            assert client.enabled is False

    def test_timeout_from_env(self):
        """Test timeout from environment variable."""
        with patch.dict('os.environ', {'OLLAMA_TIMEOUT': '45'}):
            client = Ollama()
            assert client.timeout == 45


@pytest.mark.unit
class TestOllamaMakeRequest:
    """Test Ollama _make_request method with MOCKED HTTP calls."""

    def test_make_request_disabled(self):
        """Test that request fails when Ollama is disabled."""
        client = Ollama(enabled=False)

        with pytest.raises(OllamaError, match="Ollama is disabled"):
            client._make_request("api/generate", {})

    def test_make_request_post_success(self):
        """Test successful POST request (MOCKED)."""
        client = Ollama(enabled=True)

        mock_response = Mock()
        mock_response.read.return_value = json.dumps({"response": "test"}).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch('core.ollama.urlopen', return_value=mock_response):
            result = client._make_request("api/generate", {"prompt": "test"})

            assert result == {"response": "test"}

    def test_make_request_get_success(self):
        """Test successful GET request (MOCKED)."""
        client = Ollama(enabled=True)

        mock_response = Mock()
        mock_response.read.return_value = json.dumps({"models": []}).encode('utf-8')
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch('core.ollama.urlopen', return_value=mock_response):
            result = client._make_request("api/tags", {}, method="GET")

            assert result == {"models": []}

    def test_make_request_connection_error(self):
        """Test connection error handling (MOCKED)."""
        client = Ollama(enabled=True)

        with patch('core.ollama.urlopen', side_effect=URLError("Connection refused")):
            with pytest.raises(OllamaConnectionError, match="Cannot connect to Ollama"):
                client._make_request("api/generate", {})

    def test_make_request_http_error(self):
        """Test HTTP error handling (MOCKED).

        Note: The code catches URLError (parent of HTTPError) and raises
        OllamaConnectionError for all URL-related errors, including HTTP errors.
        """
        client = Ollama(enabled=True)

        mock_error = HTTPError(url="http://test", code=500, msg="Internal Server Error", hdrs=None, fp=None)

        with patch('core.ollama.urlopen', side_effect=mock_error):
            with pytest.raises(OllamaConnectionError, match="Cannot connect to Ollama"):
                client._make_request("api/generate", {})

    def test_make_request_invalid_json(self):
        """Test invalid JSON response handling (MOCKED)."""
        client = Ollama(enabled=True)

        mock_response = Mock()
        mock_response.read.return_value = b"invalid json {{"
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch('core.ollama.urlopen', return_value=mock_response):
            with pytest.raises(OllamaAPIError, match="Invalid JSON response"):
                client._make_request("api/generate", {})

    def test_make_request_unexpected_error(self):
        """Test unexpected error handling (MOCKED)."""
        client = Ollama(enabled=True)

        with patch('core.ollama.urlopen', side_effect=Exception("Unexpected")):
            with pytest.raises(OllamaError, match="Unexpected error"):
                client._make_request("api/generate", {})


@pytest.mark.unit
class TestOllamaGenerate:
    """Test Ollama generate method with MOCKED LLM calls."""

    def test_generate_success(self):
        """Test successful text generation (MOCKED LLM)."""
        client = Ollama(model='mistral', enabled=True)

        mock_response = {
            "model": "mistral",
            "response": "This is a generated response",
            "done": True
        }

        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.generate(prompt="Test prompt")

            assert result["response"] == "This is a generated response"
            assert result["done"] is True

    def test_generate_with_custom_model(self):
        """Test generation with custom model (MOCKED LLM)."""
        client = Ollama(model='mistral', enabled=True)

        mock_response = {"response": "Custom model response", "done": True}

        with patch.object(client, '_make_request', return_value=mock_response) as mock_req:
            result = client.generate(model="llama2", prompt="Test")

            # Verify custom model was used
            call_args = mock_req.call_args
            assert call_args[0][1]["model"] == "llama2"

    def test_generate_with_options(self):
        """Test generation with custom options (MOCKED LLM)."""
        client = Ollama(enabled=True)

        mock_response = {"response": "Response", "done": True}

        with patch.object(client, '_make_request', return_value=mock_response) as mock_req:
            result = client.generate(
                prompt="Test",
                options={"temperature": 0.7, "top_k": 40}
            )

            # Verify options were passed
            call_args = mock_req.call_args
            assert call_args[0][1]["options"]["temperature"] == 0.7

    def test_generate_stream_false(self):
        """Test that stream is always False in stdlib implementation (MOCKED LLM)."""
        client = Ollama(enabled=True)

        mock_response = {"response": "Test", "done": True}

        with patch.object(client, '_make_request', return_value=mock_response) as mock_req:
            result = client.generate(prompt="Test", stream=True)

            # Verify stream is always False
            call_args = mock_req.call_args
            assert call_args[0][1]["stream"] is False


@pytest.mark.unit
class TestOllamaChat:
    """Test Ollama chat method with MOCKED LLM calls."""

    def test_chat_success(self):
        """Test successful chat (MOCKED LLM)."""
        client = Ollama(model='mistral', enabled=True)

        mock_response = {
            "model": "mistral",
            "message": {"role": "assistant", "content": "Hello!"},
            "done": True
        }

        with patch.object(client, '_make_request', return_value=mock_response):
            messages = [
                {"role": "user", "content": "Hi"}
            ]
            result = client.chat(messages=messages)

            assert result["message"]["content"] == "Hello!"
            assert result["done"] is True

    def test_chat_with_custom_model(self):
        """Test chat with custom model (MOCKED LLM)."""
        client = Ollama(model='mistral', enabled=True)

        mock_response = {
            "message": {"role": "assistant", "content": "Response"},
            "done": True
        }

        with patch.object(client, '_make_request', return_value=mock_response) as mock_req:
            result = client.chat(model="llama2", messages=[])

            # Verify custom model was used
            call_args = mock_req.call_args
            assert call_args[0][1]["model"] == "llama2"

    def test_chat_empty_messages(self):
        """Test chat with empty messages list (MOCKED LLM)."""
        client = Ollama(enabled=True)

        mock_response = {
            "message": {"role": "assistant", "content": "Default"},
            "done": True
        }

        with patch.object(client, '_make_request', return_value=mock_response) as mock_req:
            result = client.chat()

            # Verify empty messages list was sent
            call_args = mock_req.call_args
            assert call_args[0][1]["messages"] == []

    def test_chat_with_options(self):
        """Test chat with custom options (MOCKED LLM)."""
        client = Ollama(enabled=True)

        mock_response = {"message": {"role": "assistant", "content": "OK"}, "done": True}

        with patch.object(client, '_make_request', return_value=mock_response) as mock_req:
            result = client.chat(
                messages=[{"role": "user", "content": "Test"}],
                options={"temperature": 0.5}
            )

            # Verify options were passed
            call_args = mock_req.call_args
            assert call_args[0][1]["options"]["temperature"] == 0.5


@pytest.mark.unit
class TestOllamaEmbed:
    """Test Ollama embed method with MOCKED LLM calls."""

    def test_embed_single_input(self):
        """Test embedding single text (MOCKED LLM)."""
        client = Ollama(enabled=True)

        mock_response = {
            "embeddings": [[0.1, 0.2, 0.3]]
        }

        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.embed(inputs="Test text")

            assert "embeddings" in result
            assert len(result["embeddings"]) == 1

    def test_embed_multiple_inputs(self):
        """Test embedding multiple texts (MOCKED LLM)."""
        client = Ollama(enabled=True)

        mock_response = {
            "embeddings": [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]
        }

        with patch.object(client, '_make_request', return_value=mock_response):
            result = client.embed(inputs=["Text 1", "Text 2", "Text 3"])

            assert len(result["embeddings"]) == 3

    def test_embed_with_custom_model(self):
        """Test embedding with custom model (MOCKED LLM)."""
        client = Ollama(model='mistral', enabled=True)

        mock_response = {"embeddings": [[0.1]]}

        with patch.object(client, '_make_request', return_value=mock_response) as mock_req:
            result = client.embed(model="custom-embed", inputs="Test")

            # Verify custom model was used
            call_args = mock_req.call_args
            assert call_args[0][1]["model"] == "custom-embed"


@pytest.mark.integration
class TestOllamaIntegration:
    """Integration tests for Ollama client (ALL MOCKED)."""

    def test_full_workflow_mocked(self):
        """Test complete workflow with mocked responses."""
        client = Ollama(
            base_url='http://localhost:11434',
            model='mistral',
            timeout=30,
            enabled=True
        )

        # Mock all LLM calls
        with patch.object(client, '_make_request') as mock_req:
            # Test generate
            mock_req.return_value = {"response": "Generated", "done": True}
            gen_result = client.generate(prompt="Test")
            assert gen_result["response"] == "Generated"

            # Test chat
            mock_req.return_value = {
                "message": {"role": "assistant", "content": "Chat response"},
                "done": True
            }
            chat_result = client.chat(messages=[{"role": "user", "content": "Hi"}])
            assert chat_result["message"]["content"] == "Chat response"

            # Test embed
            mock_req.return_value = {"embeddings": [[0.1, 0.2]]}
            embed_result = client.embed(inputs="Embed this")
            assert len(embed_result["embeddings"]) == 1

    def test_error_handling_workflow(self):
        """Test error handling throughout workflow (MOCKED)."""
        client = Ollama(enabled=True)

        # Test connection error
        with patch.object(client, '_make_request', side_effect=OllamaConnectionError("Connection failed")):
            with pytest.raises(OllamaConnectionError):
                client.generate(prompt="Test")

        # Test API error
        with patch.object(client, '_make_request', side_effect=OllamaAPIError("API error")):
            with pytest.raises(OllamaAPIError):
                client.chat(messages=[])

    def test_disabled_client(self):
        """Test that disabled client raises errors."""
        client = Ollama(enabled=False)

        with pytest.raises(OllamaError, match="disabled"):
            client.generate(prompt="Test")

        with pytest.raises(OllamaError, match="disabled"):
            client.chat(messages=[])

        with pytest.raises(OllamaError, match="disabled"):
            client.embed(inputs="Test")


# ⚠️  CRITICAL NOTE:
# This test file NEVER makes real LLM calls.
# All HTTP requests are mocked using patch('core.ollama.urlopen').
# All LLM methods use patch.object(client, '_make_request').
# This ensures tests are deterministic, fast, and offline.
