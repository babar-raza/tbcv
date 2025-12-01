"""Tests for FastAPI error handlers.

Tests cover:
- MCP error handling
- Validation error handling
- Generic error handling
- Error response formatting
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import FastAPI, Request, status
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError, BaseModel, Field

from svc.mcp_exceptions import (
    MCPError,
    MCPMethodNotFoundError,
    MCPResourceNotFoundError,
    MCPTimeoutError,
    MCPValidationError,
)
from api.error_handlers import (
    mcp_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
    register_error_handlers,
    get_error_response_schema,
    create_test_error_response,
)


class TestMCPExceptionHandler:
    """Test MCP exception handling."""

    @pytest.mark.asyncio
    async def test_mcp_error_basic(self):
        """Test basic MCP error handling."""
        request = Mock(spec=Request)
        request.url.path = "/api/validations/test"
        request.method = "GET"

        error = MCPError("Test error", code=-32000)
        response = await mcp_exception_handler(request, error)

        assert response.status_code == 500
        assert "error" in response.body.decode()
        assert "MCPError" in response.body.decode()

    @pytest.mark.asyncio
    async def test_mcp_resource_not_found(self):
        """Test resource not found error handling."""
        request = Mock(spec=Request)
        request.url.path = "/api/validations/notfound"
        request.method = "GET"

        error = MCPResourceNotFoundError(
            "Validation not found",
            code=-32001,
            data={"validation_id": "notfound"}
        )
        response = await mcp_exception_handler(request, error)

        assert response.status_code == 404
        body = response.body.decode()
        assert "Validation not found" in body
        assert "notfound" in body

    @pytest.mark.asyncio
    async def test_mcp_method_not_found(self):
        """Test method not found error handling."""
        request = Mock(spec=Request)
        request.url.path = "/api/unknown"
        request.method = "POST"

        error = MCPMethodNotFoundError("Method not found", code=-32601)
        response = await mcp_exception_handler(request, error)

        assert response.status_code == 501

    @pytest.mark.asyncio
    async def test_mcp_timeout_error(self):
        """Test timeout error handling."""
        request = Mock(spec=Request)
        request.url.path = "/api/validations/slow"
        request.method = "GET"

        error = MCPTimeoutError("Request timeout")
        response = await mcp_exception_handler(request, error)

        assert response.status_code == 504

    @pytest.mark.asyncio
    async def test_mcp_validation_error(self):
        """Test validation error handling."""
        request = Mock(spec=Request)
        request.url.path = "/api/validations"
        request.method = "POST"

        error = MCPValidationError("Validation failed", code=-32000)
        response = await mcp_exception_handler(request, error)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_error_response_includes_metadata(self):
        """Test that error response includes request metadata."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "POST"

        error = MCPError("Test error")
        response = await mcp_exception_handler(request, error)

        body_str = response.body.decode()
        assert "/api/test" in body_str
        assert "POST" in body_str
        assert "timestamp" in body_str


class TestValidationExceptionHandler:
    """Test validation exception handling."""

    @pytest.mark.asyncio
    async def test_request_validation_error(self):
        """Test handling of RequestValidationError."""
        request = Mock(spec=Request)
        request.url.path = "/api/validations"
        request.method = "POST"

        # Create validation error
        class TestModel(BaseModel):
            file_path: str = Field(..., min_length=1)
            family: str = "words"

        try:
            TestModel(family="test")  # Missing required file_path
        except ValidationError as ve:
            response = await validation_exception_handler(request, ve)

            assert response.status_code == 422
            body_str = response.body.decode()
            assert "Validation failed" in body_str
            assert "validation_errors" in body_str

    @pytest.mark.asyncio
    async def test_validation_error_includes_details(self):
        """Test that validation errors include detailed error info."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "POST"

        class TestModel(BaseModel):
            value: int = Field(..., ge=0, le=100)

        try:
            TestModel(value=200)  # Invalid value
        except ValidationError as ve:
            response = await validation_exception_handler(request, ve)

            assert response.status_code == 422
            body_str = response.body.decode()
            assert "value" in body_str


class TestGenericExceptionHandler:
    """Test generic exception handling."""

    @pytest.mark.asyncio
    async def test_generic_exception(self):
        """Test handling of generic exceptions."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"

        error = Exception("Unexpected error")
        response = await generic_exception_handler(request, error)

        assert response.status_code == 500
        body_str = response.body.decode()
        assert "unexpected error occurred" in body_str.lower()

    @pytest.mark.asyncio
    async def test_generic_exception_includes_type(self):
        """Test that generic errors include exception type."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"

        error = ValueError("Invalid value")
        response = await generic_exception_handler(request, error)

        assert response.status_code == 500
        body_str = response.body.decode()
        assert "ValueError" in body_str

    @pytest.mark.asyncio
    async def test_generic_exception_includes_metadata(self):
        """Test that generic errors include request metadata."""
        request = Mock(spec=Request)
        request.url.path = "/api/error"
        request.method = "DELETE"

        error = RuntimeError("Runtime error")
        response = await generic_exception_handler(request, error)

        body_str = response.body.decode()
        assert "/api/error" in body_str
        assert "DELETE" in body_str
        assert "timestamp" in body_str


class TestErrorHandlerRegistration:
    """Test error handler registration."""

    def test_register_error_handlers(self):
        """Test registering error handlers with FastAPI app."""
        app = FastAPI()

        # Register handlers
        register_error_handlers(app)

        # Verify handlers are registered
        assert len(app.exception_handlers) > 0

    def test_registered_handlers_work(self):
        """Test that registered handlers actually work in app."""
        app = FastAPI()
        register_error_handlers(app)

        @app.get("/test-mcp-error")
        async def test_mcp_error():
            from svc.mcp_exceptions import MCPResourceNotFoundError
            raise MCPResourceNotFoundError("Test not found", code=-32001)

        @app.get("/test-generic-error")
        async def test_generic_error():
            raise ValueError("Test generic error")

        client = TestClient(app, raise_server_exceptions=False)

        # Test MCP error handling
        response = client.get("/test-mcp-error")
        assert response.status_code == 404
        assert "Test not found" in response.text

        # Test generic error handling
        response = client.get("/test-generic-error")
        assert response.status_code == 500
        assert "ValueError" in response.text


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_error_response_schema(self):
        """Test getting error response schema."""
        schema = get_error_response_schema()

        assert "error" in schema
        assert "type" in schema
        assert "meta" in schema
        assert "path" in schema["meta"]
        assert "method" in schema["meta"]
        assert "timestamp" in schema["meta"]

    def test_create_test_error_response(self):
        """Test creating test error response."""
        response = create_test_error_response(
            "Test error",
            error_type="TestError",
            status_code=404,
            code=-32001
        )

        assert response["error"] == "Test error"
        assert response["type"] == "TestError"
        assert response["code"] == -32001
        assert "meta" in response
        assert "timestamp" in response["meta"]


class TestIntegrationScenarios:
    """Test integration scenarios with FastAPI."""

    def test_complete_error_flow(self):
        """Test complete error flow in FastAPI app."""
        app = FastAPI()
        register_error_handlers(app)

        @app.get("/validations/{validation_id}")
        async def get_validation(validation_id: str):
            from svc.mcp_exceptions import MCPResourceNotFoundError
            if validation_id == "notfound":
                raise MCPResourceNotFoundError(
                    "Validation not found",
                    code=-32001,
                    data={"validation_id": validation_id}
                )
            return {"validation_id": validation_id}

        client = TestClient(app)

        # Test successful request
        response = client.get("/validations/test123")
        assert response.status_code == 200
        assert response.json()["validation_id"] == "test123"

        # Test error request
        response = client.get("/validations/notfound")
        assert response.status_code == 404
        data = response.json()
        assert "Validation not found" in data["error"]
        assert data["type"] == "MCPResourceNotFoundError"

    def test_validation_error_flow(self):
        """Test validation error flow in FastAPI app."""
        from pydantic import BaseModel, Field

        app = FastAPI()
        register_error_handlers(app)

        class ValidateRequest(BaseModel):
            file_path: str = Field(..., min_length=1)
            family: str = "words"

        @app.post("/validate")
        async def validate(request: ValidateRequest):
            return {"file_path": request.file_path}

        client = TestClient(app)

        # Test invalid request (missing required field)
        response = client.post("/validate", json={"family": "test"})
        assert response.status_code == 422
        data = response.json()
        assert "Validation failed" in data["error"]
        assert "validation_errors" in data

        # Test valid request
        response = client.post("/validate", json={
            "file_path": "/path/to/file.md"
        })
        assert response.status_code == 200

    def test_multiple_error_types(self):
        """Test handling multiple error types in same app."""
        app = FastAPI()
        register_error_handlers(app)

        @app.get("/mcp-error")
        async def mcp_error():
            from svc.mcp_exceptions import MCPTimeoutError
            raise MCPTimeoutError("Request timeout")

        @app.get("/generic-error")
        async def generic_error():
            raise RuntimeError("Something went wrong")

        @app.post("/validation-error")
        async def validation_error():
            from pydantic import BaseModel, Field
            class Model(BaseModel):
                value: int = Field(..., ge=0)
            return Model(value=-1)

        client = TestClient(app, raise_server_exceptions=False)

        # Test MCP error
        response = client.get("/mcp-error")
        assert response.status_code == 504

        # Test generic error
        response = client.get("/generic-error")
        assert response.status_code == 500

        # Test validation error
        response = client.post("/validation-error")
        assert response.status_code == 422


class TestErrorResponseFormat:
    """Test error response formatting consistency."""

    @pytest.mark.asyncio
    async def test_all_errors_have_consistent_format(self):
        """Test that all error types return consistent format."""
        request = Mock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"

        # Test MCP error format
        mcp_error = MCPError("Test MCP error")
        mcp_response = await mcp_exception_handler(request, mcp_error)
        mcp_data = mcp_response.body.decode()
        assert "error" in mcp_data
        assert "type" in mcp_data
        assert "meta" in mcp_data

        # Test generic error format
        generic_error = Exception("Test generic error")
        generic_response = await generic_exception_handler(request, generic_error)
        generic_data = generic_response.body.decode()
        assert "error" in generic_data
        assert "type" in generic_data
        assert "meta" in generic_data

    @pytest.mark.asyncio
    async def test_metadata_consistency(self):
        """Test that all errors include consistent metadata."""
        request = Mock(spec=Request)
        request.url.path = "/api/consistent"
        request.method = "POST"

        errors = [
            MCPError("Test"),
            Exception("Test"),
        ]

        for error in errors:
            if isinstance(error, MCPError):
                response = await mcp_exception_handler(request, error)
            else:
                response = await generic_exception_handler(request, error)

            body_str = response.body.decode()
            assert "/api/consistent" in body_str
            assert "POST" in body_str
            assert "timestamp" in body_str
