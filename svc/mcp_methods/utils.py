"""JSON-RPC utility functions."""

from typing import Dict, Any, Tuple, Optional

JSONRPC_VERSION = "2.0"

# JSON-RPC 2.0 Error Codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# Custom error codes (application-specific)
VALIDATION_FAILED = -32000
RESOURCE_NOT_FOUND = -32001
UNAUTHORIZED = -32002
RATE_LIMITED = -32003


def validate_json_rpc_request(request: Dict[str, Any]) -> Tuple[str, Dict, Any]:
    """
    Validate JSON-RPC 2.0 request structure.

    Args:
        request: Request dictionary

    Returns:
        Tuple of (method, params, request_id)

    Raises:
        ValueError: If request is invalid
    """
    if not isinstance(request, dict):
        raise ValueError("Request must be a dictionary")

    if request.get("jsonrpc") != JSONRPC_VERSION:
        raise ValueError(f"Invalid JSON-RPC version: {request.get('jsonrpc')}")

    method = request.get("method")
    if not method or not isinstance(method, str):
        raise ValueError("Method must be a non-empty string")

    params = request.get("params", {})
    if not isinstance(params, dict):
        raise ValueError("Params must be a dictionary")

    request_id = request.get("id")

    return method, params, request_id


def create_json_rpc_response(result: Any, request_id: Any) -> Dict[str, Any]:
    """
    Create JSON-RPC 2.0 success response.

    Args:
        result: Result to return
        request_id: Request ID from original request

    Returns:
        JSON-RPC response dictionary
    """
    return {
        "jsonrpc": JSONRPC_VERSION,
        "result": result,
        "id": request_id
    }


def create_json_rpc_error(
    code: int,
    message: str,
    request_id: Any,
    data: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Create JSON-RPC 2.0 error response.

    Args:
        code: Error code
        message: Error message
        request_id: Request ID from original request
        data: Optional additional error data

    Returns:
        JSON-RPC error response dictionary
    """
    error = {
        "code": code,
        "message": message
    }
    if data is not None:
        error["data"] = data

    return {
        "jsonrpc": JSONRPC_VERSION,
        "error": error,
        "id": request_id
    }
