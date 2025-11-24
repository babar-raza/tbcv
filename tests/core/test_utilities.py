# tests/core/test_utilities.py
"""
Unit tests for core/utilities.py - Utility functions.
Target coverage: 100% (Currently 21%)
"""
import pytest
import re
from typing import Dict, Any, List

from core.utilities import (
    ConfigWithDefaults,
    llm_kb_to_topic_adapter,
    process_embeddings,
    validate_api_compliance
)


@pytest.mark.unit
class TestConfigWithDefaults:
    """Test ConfigWithDefaults class."""

    def test_initialization_empty(self):
        """Test ConfigWithDefaults initialization with no data."""
        config = ConfigWithDefaults()

        assert len(config) == 0
        assert dict(config) == {}

    def test_initialization_with_data(self):
        """Test ConfigWithDefaults initialization with data."""
        data = {"key1": "value1", "key2": 123}
        config = ConfigWithDefaults(data)

        assert len(config) == 2
        assert config["key1"] == "value1"
        assert config["key2"] == 123

    def test_getitem_existing_key(self):
        """Test __getitem__ with existing key."""
        config = ConfigWithDefaults({"name": "test", "count": 5})

        assert config["name"] == "test"
        assert config["count"] == 5

    def test_getitem_missing_key_returns_default(self):
        """Test __getitem__ with missing key returns 'default'."""
        config = ConfigWithDefaults({"existing": "value"})

        assert config["missing_key"] == "default"
        assert config["another_missing"] == "default"

    def test_get_existing_key(self):
        """Test get() method with existing key."""
        config = ConfigWithDefaults({"name": "test"})

        assert config.get("name") == "test"

    def test_get_missing_key_no_default(self):
        """Test get() with missing key and no default specified."""
        config = ConfigWithDefaults({"existing": "value"})

        assert config.get("missing") == "default"

    def test_get_missing_key_with_default(self):
        """Test get() with missing key and custom default."""
        config = ConfigWithDefaults({"existing": "value"})

        assert config.get("missing", "custom") == "custom"
        assert config.get("missing", 123) == 123
        assert config.get("missing", None) == "default"  # None -> use "default"

    def test_getattr_existing_key(self):
        """Test __getattr__ with existing key."""
        config = ConfigWithDefaults({"name": "test", "port": 8080})

        assert config.name == "test"
        assert config.port == 8080

    def test_getattr_missing_key_returns_default(self):
        """Test __getattr__ with missing key returns 'default'."""
        config = ConfigWithDefaults({"existing": "value"})

        assert config.missing_attr == "default"
        assert config.another_missing == "default"

    def test_getattr_private_attribute_raises(self):
        """Test __getattr__ with private attribute raises AttributeError."""
        config = ConfigWithDefaults({"name": "test"})

        with pytest.raises(AttributeError):
            _ = config._private

        with pytest.raises(AttributeError):
            _ = config._data_backup

    def test_iter(self):
        """Test iteration over config keys."""
        data = {"key1": "val1", "key2": "val2", "key3": "val3"}
        config = ConfigWithDefaults(data)

        keys = list(config)
        assert set(keys) == {"key1", "key2", "key3"}

    def test_len(self):
        """Test length of config."""
        config1 = ConfigWithDefaults()
        assert len(config1) == 0

        config2 = ConfigWithDefaults({"a": 1})
        assert len(config2) == 1

        config3 = ConfigWithDefaults({"a": 1, "b": 2, "c": 3})
        assert len(config3) == 3

    def test_mapping_protocol(self):
        """Test that ConfigWithDefaults implements Mapping protocol."""
        from collections.abc import Mapping

        config = ConfigWithDefaults({"key": "value"})

        assert isinstance(config, Mapping)
        assert "key" in config
        assert config["key"] == "value"


@pytest.mark.unit
class TestLlmKbToTopicAdapter:
    """Test llm_kb_to_topic_adapter function."""

    def test_short_content_expanded(self):
        """Test short content is expanded to minimum 100 chars."""
        short_text = "Short"
        result = llm_kb_to_topic_adapter(short_text)

        assert len(result) >= 100
        assert "Short" in result
        assert "expanded to meet minimum length" in result

    def test_medium_content_expanded(self):
        """Test medium content (< 100 chars) is expanded."""
        medium_text = "This is a medium length text that is less than one hundred characters"
        result = llm_kb_to_topic_adapter(medium_text)

        assert len(result) >= 100
        assert medium_text in result

    def test_long_content_not_expanded(self):
        """Test long content (>= 100 chars) is not expanded."""
        long_text = "This is a very long text that already exceeds one hundred characters in length and should not need any expansion"
        result = llm_kb_to_topic_adapter(long_text)

        assert len(result) >= 100
        assert result == ' '.join(long_text.split())  # Just whitespace normalized
        assert "expanded to meet minimum length" not in result

    def test_whitespace_normalization(self):
        """Test whitespace is normalized."""
        text_with_whitespace = "Text   with    multiple     spaces\n\nand\nnewlines"
        result = llm_kb_to_topic_adapter(text_with_whitespace)

        assert "   " not in result
        assert "\n" not in result
        assert result.startswith("Text with multiple spaces")

    def test_empty_string_expanded(self):
        """Test empty string is expanded to minimum length."""
        result = llm_kb_to_topic_adapter("")

        assert len(result) >= 100
        assert "expanded to meet minimum length" in result

    def test_exactly_100_chars(self):
        """Test content with exactly 100 chars."""
        # Create exactly 100 char string
        exact_text = "a" * 100
        result = llm_kb_to_topic_adapter(exact_text)

        assert len(result) == 100
        assert result == exact_text

    def test_strip_leading_trailing_whitespace(self):
        """Test leading and trailing whitespace is stripped."""
        text = "   Some text with spaces   "
        result = llm_kb_to_topic_adapter(text)

        assert result.startswith("Some")
        assert len(result) >= 100


@pytest.mark.unit
class TestProcessEmbeddings:
    """Test process_embeddings function."""

    def test_empty_list(self):
        """Test processing empty list returns empty list."""
        result = process_embeddings([])

        assert result == []
        assert isinstance(result, list)

    def test_single_text(self):
        """Test processing single text."""
        texts = ["hello world"]
        result = process_embeddings(texts)

        assert len(result) == 1
        assert len(result[0]) == 3  # 3-dimensional vector
        assert all(isinstance(v, float) for v in result[0])
        assert all(0.0 <= v <= 1.0 for v in result[0])

    def test_multiple_texts(self):
        """Test processing multiple texts."""
        texts = ["text one", "text two", "text three"]
        result = process_embeddings(texts)

        assert len(result) == 3
        for embedding in result:
            assert len(embedding) == 3
            assert all(isinstance(v, float) for v in embedding)

    def test_different_texts_different_embeddings(self):
        """Test different texts produce different embeddings."""
        texts = ["hello", "world", "test"]
        result = process_embeddings(texts)

        # Embeddings should be different for different texts
        assert result[0] != result[1]
        assert result[1] != result[2]
        assert result[0] != result[2]

    def test_same_text_same_embedding(self):
        """Test same text produces same embedding (deterministic)."""
        text = "consistent text"
        result1 = process_embeddings([text])
        result2 = process_embeddings([text])

        assert result1 == result2
        assert result1[0] == result2[0]

    def test_embedding_values_in_range(self):
        """Test all embedding values are in [0, 1] range."""
        texts = ["text1", "text2", "text3", "text4", "text5"]
        result = process_embeddings(texts)

        for embedding in result:
            for value in embedding:
                assert 0.0 <= value <= 1.0

    def test_long_text(self):
        """Test processing long text."""
        long_text = "a" * 1000
        result = process_embeddings([long_text])

        assert len(result) == 1
        assert len(result[0]) == 3
        assert all(0.0 <= v <= 1.0 for v in result[0])

    def test_special_characters(self):
        """Test processing text with special characters."""
        texts = ["hello@world", "test#123", "special!chars$"]
        result = process_embeddings(texts)

        assert len(result) == 3
        for embedding in result:
            assert len(embedding) == 3


@pytest.mark.unit
class TestValidateApiCompliance:
    """Test validate_api_compliance function."""

    def test_valid_api_spec(self):
        """Test valid API specification."""
        api_spec = {
            "version": "1.0.0",
            "endpoints": [
                {"path": "/api/users", "method": "GET"},
                {"path": "/api/users", "method": "POST"}
            ],
            "authentication": "bearer"
        }

        assert validate_api_compliance(api_spec) is True

    def test_valid_api_spec_minimal(self):
        """Test minimal valid API specification."""
        api_spec = {
            "version": "1.0",
            "endpoints": [{"path": "/", "method": "GET"}],
            "authentication": "none"
        }

        assert validate_api_compliance(api_spec) is True

    def test_valid_api_spec_dict_auth(self):
        """Test valid API spec with dict authentication."""
        api_spec = {
            "version": "2.1.5",
            "endpoints": [{"path": "/api", "method": "POST"}],
            "authentication": {"type": "oauth2", "flow": "implicit"}
        }

        assert validate_api_compliance(api_spec) is True

    def test_missing_version_field(self):
        """Test API spec missing version field."""
        api_spec = {
            "endpoints": [{"path": "/api", "method": "GET"}],
            "authentication": "bearer"
        }

        assert validate_api_compliance(api_spec) is False

    def test_missing_endpoints_field(self):
        """Test API spec missing endpoints field."""
        api_spec = {
            "version": "1.0.0",
            "authentication": "bearer"
        }

        assert validate_api_compliance(api_spec) is False

    def test_missing_authentication_field(self):
        """Test API spec missing authentication field."""
        api_spec = {
            "version": "1.0.0",
            "endpoints": [{"path": "/api", "method": "GET"}]
        }

        assert validate_api_compliance(api_spec) is False

    def test_invalid_version_format(self):
        """Test invalid version format."""
        invalid_versions = ["v1.0", "1", "abc", "1.0.0.0", ""]

        for version in invalid_versions:
            api_spec = {
                "version": version,
                "endpoints": [{"path": "/api", "method": "GET"}],
                "authentication": "bearer"
            }
            assert validate_api_compliance(api_spec) is False

    def test_valid_version_formats(self):
        """Test various valid version formats."""
        valid_versions = ["1.0", "1.0.0", "2.3.4", "10.20.30"]

        for version in valid_versions:
            api_spec = {
                "version": version,
                "endpoints": [{"path": "/api", "method": "GET"}],
                "authentication": "bearer"
            }
            assert validate_api_compliance(api_spec) is True

    def test_empty_endpoints_list(self):
        """Test empty endpoints list is invalid."""
        api_spec = {
            "version": "1.0.0",
            "endpoints": [],
            "authentication": "bearer"
        }

        assert validate_api_compliance(api_spec) is False

    def test_endpoints_not_list(self):
        """Test endpoints not being a list is invalid."""
        api_spec = {
            "version": "1.0.0",
            "endpoints": "not a list",
            "authentication": "bearer"
        }

        assert validate_api_compliance(api_spec) is False

    def test_endpoint_missing_path(self):
        """Test endpoint missing path field."""
        api_spec = {
            "version": "1.0.0",
            "endpoints": [{"method": "GET"}],
            "authentication": "bearer"
        }

        assert validate_api_compliance(api_spec) is False

    def test_endpoint_missing_method(self):
        """Test endpoint missing method field."""
        api_spec = {
            "version": "1.0.0",
            "endpoints": [{"path": "/api"}],
            "authentication": "bearer"
        }

        assert validate_api_compliance(api_spec) is False

    def test_endpoint_not_dict(self):
        """Test endpoint not being a dict."""
        api_spec = {
            "version": "1.0.0",
            "endpoints": ["/api/users"],
            "authentication": "bearer"
        }

        assert validate_api_compliance(api_spec) is False

    def test_authentication_empty_string(self):
        """Test empty string authentication is invalid."""
        api_spec = {
            "version": "1.0.0",
            "endpoints": [{"path": "/api", "method": "GET"}],
            "authentication": ""
        }

        assert validate_api_compliance(api_spec) is False

    def test_authentication_none_value(self):
        """Test None authentication is invalid."""
        api_spec = {
            "version": "1.0.0",
            "endpoints": [{"path": "/api", "method": "GET"}],
            "authentication": None
        }

        assert validate_api_compliance(api_spec) is False

    def test_authentication_invalid_type(self):
        """Test authentication with invalid type."""
        api_spec = {
            "version": "1.0.0",
            "endpoints": [{"path": "/api", "method": "GET"}],
            "authentication": 123
        }

        assert validate_api_compliance(api_spec) is False

    def test_multiple_endpoints(self):
        """Test API spec with multiple endpoints."""
        api_spec = {
            "version": "1.2.3",
            "endpoints": [
                {"path": "/api/users", "method": "GET"},
                {"path": "/api/users/{id}", "method": "GET"},
                {"path": "/api/users", "method": "POST"},
                {"path": "/api/users/{id}", "method": "PUT"},
                {"path": "/api/users/{id}", "method": "DELETE"}
            ],
            "authentication": {"type": "jwt"}
        }

        assert validate_api_compliance(api_spec) is True


@pytest.mark.integration
class TestUtilitiesIntegration:
    """Integration tests for utilities module."""

    def test_config_with_embeddings_workflow(self):
        """Test using ConfigWithDefaults with embeddings processing."""
        config = ConfigWithDefaults({
            "model": "text-embedding-v1",
            "dimensions": 3
        })

        texts = ["config test", "embedding test"]
        embeddings = process_embeddings(texts)

        assert config.model == "text-embedding-v1"
        assert len(embeddings) == len(texts)
        assert all(len(e) == 3 for e in embeddings)

    def test_topic_adapter_with_validation(self):
        """Test topic adapter with API validation."""
        # Prepare content
        short_content = "API spec"
        adapted = llm_kb_to_topic_adapter(short_content)

        # Validate API spec
        api_spec = {
            "version": "1.0.0",
            "endpoints": [{"path": "/api", "method": "GET"}],
            "authentication": "bearer"
        }

        assert len(adapted) >= 100
        assert validate_api_compliance(api_spec) is True

    def test_complete_workflow(self):
        """Test complete workflow with all utilities."""
        # 1. Config setup
        config = ConfigWithDefaults({
            "api_version": "2.0.0",
            "min_content_length": 100
        })

        # 2. Process content
        content = "Short content"
        adapted_content = llm_kb_to_topic_adapter(content)

        # 3. Generate embeddings
        embeddings = process_embeddings([adapted_content])

        # 4. Validate API spec
        api_spec = {
            "version": config.api_version,
            "endpoints": [{"path": "/process", "method": "POST"}],
            "authentication": config.get("auth_method", "token")
        }

        assert len(adapted_content) >= config.get("min_content_length", 100)
        assert len(embeddings) == 1
        assert validate_api_compliance(api_spec) is True
