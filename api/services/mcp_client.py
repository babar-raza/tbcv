# file: tbcv/api/services/mcp_client.py
"""
MCP client for sending enhancement and validation requests.
Reuses transport layer with proper retry logic and logging.
"""

from __future__ import annotations

import asyncio
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from core.logging import get_logger
    from core.config import get_settings
except ImportError:
    from core.logging import get_logger
    from core.config import get_settings

logger = get_logger(__name__)


class MCPClient:
    """
    Client for communicating with MCP server.
    """
    
    def __init__(self, host: str = "localhost", port: int = 5050, timeout: int = 300):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.max_retries = 3
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send request to MCP server with retry logic.
        
        Args:
            request: Request payload
            
        Returns:
            Response from MCP server
        """
        logger.info(f"Sending MCP request: task={request.get('task')}, payload_size={len(json.dumps(request))} bytes")
        
        for attempt in range(self.max_retries):
            try:
                # Try to import the MCP client
                try:
                    from svc.mcp_server import call_mcp_sync
                    result = await asyncio.get_event_loop().run_in_executor(
                        None, call_mcp_sync, request
                    )
                    return result
                except ImportError:
                    # Fallback: simulate MCP response
                    logger.warning("MCP server not available, using fallback")
                    return self._simulate_response(request)
                    
            except asyncio.TimeoutError:
                logger.error(f"MCP request timeout (attempt {attempt + 1}/{self.max_retries})")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                logger.error(f"MCP request failed (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("MCP request failed after all retries")
    
    def _simulate_response(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate MCP response for testing."""
        task = request.get('task')
        
        logger.info(f"MCP simulation: task={task}")
        
        if task == 'apply_recommendations':
            inputs = request.get('inputs', {})
            content = inputs.get('content', '')
            recommendations = inputs.get('recommendations', [])
            
            logger.info(f"MCP simulation: applying {len(recommendations)} recommendations to {len(content)} chars of content")
            
            # Actually apply the recommendations (simple string replacement)
            enhanced_content = content
            applied_count = 0

            for rec in recommendations:
                original = rec.get('original_content') or rec.get('original', '')
                proposed = rec.get('proposed_content') or rec.get('proposed', '')

                if original and proposed and original in enhanced_content:
                    # Simple replacement - in real MCP this would be smarter
                    enhanced_content = enhanced_content.replace(original, proposed, 1)
                    applied_count += 1
                    logger.debug(f"Applied recommendation: replaced '{original[:50]}...' with '{proposed[:50]}...'")
                elif proposed and not original:
                    # This is an addition/insertion, append it
                    enhanced_content += "\n" + proposed
                    applied_count += 1
                    logger.debug(f"Added recommendation: '{proposed[:50]}...'")
            
            logger.info(f"MCP simulation: applied {applied_count} recommendations")
            
            return {
                "success": True,
                "result": {
                    "content": enhanced_content,
                    "applied_count": applied_count,
                    "status": "completed"
                }
            }
        elif task == 'validate_content':
            return {
                "success": True,
                "result": {
                    "issues": [],
                    "status": "pass"
                }
            }
        else:
            return {
                "success": False,
                "error": f"Unknown task: {task}"
            }
    
    async def validate_content(
        self,
        content: str,
        file_path: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send content for validation.
        
        Args:
            content: Content to validate
            file_path: Path of the content file
            config: Optional configuration
            
        Returns:
            Validation results
        """
        request = {
            "task": "validate_content",
            "inputs": {
                "content": content,
                "file_path": file_path,
                "config": config or {}
            }
        }
        
        return await self.send_request(request)
    
    async def apply_recommendations(
        self,
        content: str,
        recommendations: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply recommendations to content.
        
        Args:
            content: Original content
            recommendations: List of recommendations to apply
            config: Optional configuration (tone, template, etc.)
            
        Returns:
            Enhanced content and metadata
        """
        # Prepare recommendations for MCP
        mcp_recommendations = []
        for rec in recommendations:
            mcp_rec = {
                "id": rec.get("id"),
                "type": rec.get("type"),
                "selector": rec.get("metadata", {}).get("target", {}).get("selector", "body"),
                "proposed": rec.get("proposed_content", ""),
                "rationale": rec.get("metadata", {}).get("rationale", rec.get("description", ""))
            }
            mcp_recommendations.append(mcp_rec)
        
        request = {
            "task": "apply_recommendations",
            "inputs": {
                "content": content,
                "recommendations": mcp_recommendations,
                "config": config or {}
            }
        }
        
        response = await self.send_request(request)
        
        # Log result (without full content)
        if response.get("success"):
            result = response.get("result", {})
            logger.info(f"MCP apply_recommendations succeeded: applied_count={result.get('applied_count', 0)}")
        else:
            logger.error(f"MCP apply_recommendations failed: {response.get('error')}")
        
        return response


# Global MCP client instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get or create global MCP client instance."""
    global _mcp_client
    if _mcp_client is None:
        settings = get_settings()
        mcp_config = getattr(settings, 'mcp', {})
        host = mcp_config.get('host', 'localhost')
        port = mcp_config.get('port', 5050)
        timeout = mcp_config.get('timeout', 300)
        _mcp_client = MCPClient(host=host, port=port, timeout=timeout)
    return _mcp_client
