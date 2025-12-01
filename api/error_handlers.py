"""FastAPI exception handlers for consistent error responses.

This module provides centralized exception handling for the FastAPI application,
ensuring consistent error responses across all endpoints.

Exception Handlers:
- MCPError: MCP-specific errors (converted to appropriate HTTP status)
- ValidationError: Pydantic validation errors (422)
- HTTPException: FastAPI HTTP exceptions (pass through)
- Generic Exception: Unexpected errors (500)

Example:
    from fastapi import FastAPI
    from api.error_handlers import register_error_handlers

    app = FastAPI()
    register_error_handlers(app)
"""

from typing import Union, Dict, Any
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from svc.mcp_exceptions import MCPError
from api.mcp_helpers import mcp_error_to_http_exception
from core.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Exception Handlers
# =============================================================================


async def mcp_exception_handler(
    request: Request,
    exc: MCPError
) -> JSONResponse:
    """
    Handle MCP-specific exceptions.

    Converts MCP errors to appropriate HTTP responses with standard
    error formatting. Logs the error for debugging and monitoring.

    Status Code Mapping:
    - MCPMethodNotFoundError → 501 Not Implemented
    - MCPInvalidParamsError → 400 Bad Request
    - MCPResourceNotFoundError → 404 Not Found
    - MCPTimeoutError → 504 Gateway Timeout
    - MCPValidationError → 422 Unprocessable Entity
    - MCPInternalError → 500 Internal Server Error
    - MCPError (generic) → 500 Internal Server Error

    Args:
        request: The FastAPI request object
        exc: The MCP exception that was raised

    Returns:
        JSONResponse: Formatted error response

    Example Response:
        {
            "error": "Validation not found",
            "type": "MCPResourceNotFoundError",
            "code": -32001,
            "meta": {
                "path": "/api/validations/abc123",
                "method": "GET",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    """
    # Convert MCP error to HTTP exception
    http_exc = mcp_error_to_http_exception(exc)

    # Build error response
    error_response = http_exc.detail.copy() if isinstance(http_exc.detail, dict) else {
        "error": str(exc),
        "type": type(exc).__name__,
    }

    # Add request metadata
    error_response["meta"] = {
        "path": str(request.url.path),
        "method": request.method,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Log the error
    logger.error(
        f"MCP error on {request.method} {request.url.path}: {exc}",
        extra={
            "error_type": type(exc).__name__,
            "error_code": exc.code,
            "request_method": request.method,
            "request_path": str(request.url.path),
            "status_code": http_exc.status_code,
        }
    )

    return JSONResponse(
        status_code=http_exc.status_code,
        content=error_response
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Returns 422 Unprocessable Entity with detailed validation error
    information. Useful for debugging invalid request payloads.

    Args:
        request: The FastAPI request object
        exc: The validation exception

    Returns:
        JSONResponse: Formatted validation error response

    Example Response:
        {
            "error": "Validation failed",
            "type": "ValidationError",
            "validation_errors": [
                {
                    "loc": ["body", "file_path"],
                    "msg": "field required",
                    "type": "value_error.missing"
                }
            ],
            "meta": {
                "path": "/api/validations",
                "method": "POST",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    """
    # Extract validation errors
    if isinstance(exc, RequestValidationError):
        errors = exc.errors()
    else:
        errors = exc.errors()

    # Build error response
    error_response = {
        "error": "Validation failed",
        "type": "ValidationError",
        "validation_errors": errors,
        "meta": {
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }

    # Log the validation error
    logger.warning(
        f"Validation error on {request.method} {request.url.path}: {len(errors)} error(s)",
        extra={
            "error_count": len(errors),
            "request_method": request.method,
            "request_path": str(request.url.path),
            "validation_errors": errors,
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=error_response
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Returns 500 Internal Server Error for any unhandled exceptions.
    Logs the full exception for debugging while providing a safe
    error message to clients.

    Args:
        request: The FastAPI request object
        exc: The exception that was raised

    Returns:
        JSONResponse: Formatted error response

    Example Response:
        {
            "error": "An unexpected error occurred",
            "type": "Exception",
            "message": "division by zero",
            "meta": {
                "path": "/api/validations/process",
                "method": "POST",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    """
    # Build error response (don't expose internal details in production)
    error_response = {
        "error": "An unexpected error occurred",
        "type": type(exc).__name__,
        "message": str(exc),
        "meta": {
            "path": str(request.url.path),
            "method": request.method,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }

    # Log the full exception with traceback
    # Handle potential Unicode encoding issues in error messages
    try:
        error_msg = str(exc)
    except Exception:
        error_msg = repr(exc)

    try:
        logger.exception(
            f"Unexpected error on {request.method} {request.url.path}: {error_msg}",
            extra={
                "error_type": type(exc).__name__,
                "request_method": request.method,
                "request_path": str(request.url.path),
            }
        )
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Fallback: log without the exception details if encoding fails
        logger.error(
            f"Unexpected error on {request.method} {request.url.path} (encoding error in details)",
            extra={
                "error_type": type(exc).__name__,
                "request_method": request.method,
                "request_path": str(request.url.path),
            }
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


# =============================================================================
# Registration Helper
# =============================================================================


def register_error_handlers(app: FastAPI) -> None:
    """
    Register all error handlers with the FastAPI application.

    This should be called during application startup to ensure all
    exception types are properly handled.

    Args:
        app: The FastAPI application instance

    Example:
        from fastapi import FastAPI
        from api.error_handlers import register_error_handlers

        app = FastAPI()
        register_error_handlers(app)

        @app.get("/")
        async def root():
            return {"message": "Hello World"}
    """
    # Register MCP error handler
    app.add_exception_handler(MCPError, mcp_exception_handler)

    # Register validation error handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # Register generic error handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Registered FastAPI error handlers")


# =============================================================================
# Testing Utilities
# =============================================================================


def get_error_response_schema() -> Dict[str, Any]:
    """
    Get the standard error response schema.

    Useful for API documentation and testing.

    Returns:
        Dict[str, Any]: Error response schema

    Example:
        {
            "error": "string",
            "type": "string",
            "code": "integer (optional)",
            "data": "any (optional)",
            "validation_errors": "array (optional)",
            "meta": {
                "path": "string",
                "method": "string",
                "timestamp": "string (ISO 8601)"
            }
        }
    """
    return {
        "error": "string",
        "type": "string",
        "code": "integer (optional)",
        "data": "any (optional)",
        "validation_errors": "array (optional)",
        "meta": {
            "path": "string",
            "method": "string",
            "timestamp": "string (ISO 8601)"
        }
    }


def create_test_error_response(
    error_message: str,
    error_type: str = "MCPError",
    status_code: int = 500,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a test error response for unit testing.

    Args:
        error_message: The error message
        error_type: The error type name
        status_code: HTTP status code
        **kwargs: Additional fields to include

    Returns:
        Dict[str, Any]: Test error response

    Example:
        response = create_test_error_response(
            "Validation not found",
            error_type="MCPResourceNotFoundError",
            status_code=404,
            code=-32001
        )
    """
    response = {
        "error": error_message,
        "type": error_type,
        "meta": {
            "path": "/test/path",
            "method": "GET",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }

    # Add any additional fields
    for key, value in kwargs.items():
        if key != "meta":
            response[key] = value

    return response
