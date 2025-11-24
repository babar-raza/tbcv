# file: core/ollama.py
"""
Unified Ollama LLM integration for all agents.
Uses only Python standard library (urllib.request) for HTTP calls.
Provides synchronous and asynchronous interfaces for compatibility.
"""

import os
import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from urllib.request import Request, urlopen
from urllib.parse import urljoin
from urllib.error import URLError, HTTPError
import threading

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Base exception for Ollama-related errors."""
    pass


class OllamaConnectionError(OllamaError):
    """Raised when cannot connect to Ollama server."""
    pass


class OllamaAPIError(OllamaError):
    """Raised when Ollama API returns an error."""
    pass


class Ollama:
    """
    Unified Ollama integration using only Python standard library.
    
    Provides methods for:
    - chat(model, messages, stream=False)
    - generate(model, prompt, stream=False)
    - embed(model, inputs)
    - model_info(model)
    
    Configuration via environment variables:
    - OLLAMA_BASE_URL (default: http://127.0.0.1:11434)
    - OLLAMA_MODEL (default: mistral)
    - OLLAMA_TIMEOUT (default: 30)
    - OLLAMA_ENABLED (default: true)
    """
    
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None, 
                 timeout: Optional[int] = None, enabled: Optional[bool] = None):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama server URL (overrides OLLAMA_BASE_URL)
            model: Default model name (overrides OLLAMA_MODEL)
            timeout: Request timeout in seconds (overrides OLLAMA_TIMEOUT)
            enabled: Whether Ollama is enabled (overrides OLLAMA_ENABLED)
        """
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
        self.model = model or os.getenv('OLLAMA_MODEL', 'mistral')
        self.timeout = timeout or int(os.getenv('OLLAMA_TIMEOUT', '30'))
        self.enabled = enabled if enabled is not None else os.getenv('OLLAMA_ENABLED', 'true').lower() == 'true'
        
        # Ensure base_url ends with /
        if not self.base_url.endswith('/'):
            self.base_url += '/'
    
    def _make_request(self, endpoint: str, data: Dict[str, Any], method: str = "POST") -> Dict[str, Any]:
        """
        Make HTTP request to Ollama API using urllib.request.
        
        Args:
            endpoint: API endpoint (e.g., 'api/generate')
            data: Request payload (ignored for GET requests)
            method: HTTP method (POST or GET)
            
        Returns:
            Response data as dictionary
            
        Raises:
            OllamaConnectionError: When cannot connect to server
            OllamaAPIError: When API returns error
        """
        if not self.enabled:
            raise OllamaError("Ollama is disabled")
        
        url = urljoin(self.base_url, endpoint)
        
        if method.upper() == "GET":
            # GET request - no body
            request = Request(
                url,
                headers={
                    'Accept': 'application/json'
                }
            )
        else:
            # POST request - with JSON body
            json_data = json.dumps(data).encode('utf-8')
            request = Request(
                url,
                data=json_data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            )
        
        try:
            with urlopen(request, timeout=self.timeout) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
        except URLError as e:
            logger.warning(f"Ollama connection failed: {e}")
            raise OllamaConnectionError(f"Cannot connect to Ollama at {url}: {e}")
        except HTTPError as e:
            logger.warning(f"Ollama HTTP error {e.code}: {e.reason}")
            raise OllamaAPIError(f"Ollama API error {e.code}: {e.reason}")
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON response from Ollama: {e}")
            raise OllamaAPIError(f"Invalid JSON response: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error calling Ollama: {e}")
            raise OllamaError(f"Unexpected error: {e}")
    
    def generate(self, model: Optional[str] = None, prompt: str = "", 
                 stream: bool = False, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate text using Ollama.
        
        Args:
            model: Model name (uses default if None)
            prompt: Input prompt
            stream: Whether to stream response (not implemented for stdlib)
            options: Additional generation options
            
        Returns:
            Generation response containing 'response' field
        """
        model = model or self.model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,  # Always False for stdlib implementation
            "options": options or {}
        }
        
        return self._make_request("api/generate", payload)
    
    def chat(self, model: Optional[str] = None, messages: List[Dict[str, str]] = None,
             stream: bool = False, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Chat using Ollama.
        
        Args:
            model: Model name (uses default if None)
            messages: List of chat messages with 'role' and 'content'
            stream: Whether to stream response (not implemented for stdlib)
            options: Additional generation options
            
        Returns:
            Chat response containing 'message' field
        """
        model = model or self.model
        messages = messages or []
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,  # Always False for stdlib implementation
            "options": options or {}
        }
        
        return self._make_request("api/chat", payload)
    
    def embed(self, model: Optional[str] = None, inputs: Union[str, List[str]] = None) -> Dict[str, Any]:
        """
        Generate embeddings using Ollama.
        
        Args:
            model: Model name (uses default if None)
            inputs: Text input(s) to embed
            
        Returns:
            Embeddings response containing 'embeddings' field
        """
        model = model or self.model
        
        if isinstance(inputs, str):
            inputs = [inputs]
        
        payload = {
            "model": model,
            "input": inputs or []
        }
        
        return self._make_request("api/embed", payload)
    
    def model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Get model information from Ollama.
        
        Args:
            model: Model name (uses default if None)
            
        Returns:
            Model information
        """
        model = model or self.model
        
        payload = {
            "name": model
        }
        
        return self._make_request("api/show", payload)
    
    def list_models(self) -> Dict[str, Any]:
        """
        List available models.
        
        Returns:
            List of available models
        """
        return self._make_request("api/tags", {}, method="GET")
    
    def is_available(self) -> bool:
        """
        Check if Ollama server is available.
        
        Returns:
            True if server is available, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            self.list_models()
            return True
        except Exception as e:
            logger.debug(f"Ollama availability check failed: {e}")
            return False
    
    # Async compatibility methods
    async def async_generate(self, model: Optional[str] = None, prompt: str = "", 
                            stream: bool = False, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Async wrapper for generate method.
        Runs in thread pool to maintain compatibility with async code.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate, model, prompt, stream, options)
    
    async def async_chat(self, model: Optional[str] = None, messages: List[Dict[str, str]] = None,
                        stream: bool = False, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Async wrapper for chat method.
        Runs in thread pool to maintain compatibility with async code.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.chat, model, messages, stream, options)
    
    async def async_embed(self, model: Optional[str] = None, inputs: Union[str, List[str]] = None) -> Dict[str, Any]:
        """
        Async wrapper for embed method.
        Runs in thread pool to maintain compatibility with async code.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed, model, inputs)
    
    async def async_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Async wrapper for model_info method.
        Runs in thread pool to maintain compatibility with async code.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.model_info, model)


# Global instance for backward compatibility
ollama = Ollama()


# Legacy compatibility functions for existing code
def validate_content_contradictions(content: str, plugin_info: List[Dict], 
                                  family_rules: Dict[str, Any]) -> List[Dict]:
    """
    Legacy compatibility function for contradiction validation.
    This is synchronous and should be called from sync contexts.
    """
    if not ollama.enabled or not ollama.is_available():
        return []
    
    try:
        prompt = _build_contradiction_prompt(content, plugin_info, family_rules)
        response = ollama.generate(prompt=prompt, options={
            "temperature": 0.1,
            "top_p": 0.9,
            "stop": ["```", "---"]
        })
        return _parse_contradiction_response(response.get('response', ''))
    except Exception as e:
        logger.warning(f"Ollama contradiction validation failed: {e}")
        return []


def validate_content_omissions(content: str, plugin_info: List[Dict],
                             family_rules: Dict[str, Any]) -> List[Dict]:
    """
    Legacy compatibility function for omission validation.
    This is synchronous and should be called from sync contexts.
    """
    if not ollama.enabled or not ollama.is_available():
        return []
    
    try:
        prompt = _build_omission_prompt(content, plugin_info, family_rules)
        response = ollama.generate(prompt=prompt, options={
            "temperature": 0.1,
            "top_p": 0.9,
            "stop": ["```", "---"]
        })
        return _parse_omission_response(response.get('response', ''))
    except Exception as e:
        logger.warning(f"Ollama omission validation failed: {e}")
        return []


async def async_validate_content_contradictions(content: str, plugin_info: List[Dict], 
                                              family_rules: Dict[str, Any]) -> List[Dict]:
    """
    Async legacy compatibility function for contradiction validation.
    """
    if not ollama.enabled or not ollama.is_available():
        return []
    
    try:
        prompt = _build_contradiction_prompt(content, plugin_info, family_rules)
        response = await ollama.async_generate(prompt=prompt, options={
            "temperature": 0.1,
            "top_p": 0.9,
            "stop": ["```", "---"]
        })
        return _parse_contradiction_response(response.get('response', ''))
    except Exception as e:
        logger.warning(f"Ollama contradiction validation failed: {e}")
        return []


async def async_validate_content_omissions(content: str, plugin_info: List[Dict],
                                         family_rules: Dict[str, Any]) -> List[Dict]:
    """
    Async legacy compatibility function for omission validation.
    """
    if not ollama.enabled or not ollama.is_available():
        return []
    
    try:
        prompt = _build_omission_prompt(content, plugin_info, family_rules)
        response = await ollama.async_generate(prompt=prompt, options={
            "temperature": 0.1,
            "top_p": 0.9,
            "stop": ["```", "---"]
        })
        return _parse_omission_response(response.get('response', ''))
    except Exception as e:
        logger.warning(f"Ollama omission validation failed: {e}")
        return []


def _build_contradiction_prompt(content: str, plugin_info: List[Dict], 
                              family_rules: Dict[str, Any]) -> str:
    """Build prompt for contradiction detection using centralized prompts."""
    from core.prompt_loader import get_contradiction_prompt
    
    api_patterns = family_rules.get('api_patterns', {})
    validation_reqs = family_rules.get('validation_requirements', {})
    
    return get_contradiction_prompt(content, plugin_info, api_patterns, validation_reqs)


def _build_omission_prompt(content: str, plugin_info: List[Dict],
                         family_rules: Dict[str, Any]) -> str:
    """Build prompt for omission detection using centralized prompts."""
    from core.prompt_loader import get_omission_prompt
    
    validation_reqs = family_rules.get('validation_requirements', {})
    code_rules = family_rules.get('code_quality_rules', {})
    
    return get_omission_prompt(content, plugin_info, validation_reqs, code_rules)


def _parse_contradiction_response(response: str) -> List[Dict]:
    """Parse LLM response for contradictions."""
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            issues = []
            for contradiction in data.get('contradictions', []):
                severity = contradiction.get('severity', 'medium')
                level = 'error' if severity == 'high' else 'warning' if severity == 'medium' else 'info'
                
                issues.append({
                    'level': level,
                    'category': 'llm_contradiction',
                    'message': contradiction.get('issue', 'Content contradiction detected'),
                    'suggestion': 'Review and correct the identified contradiction',
                    'source': 'ollama'
                })
            return issues
    except Exception as e:
        logger.debug(f"Failed to parse Ollama contradiction response: {e}")
    return []
        

def _parse_omission_response(response: str) -> List[Dict]:
    """Parse LLM response for omissions."""
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            issues = []
            for omission in data.get('omissions', []):
                importance = omission.get('importance', 'nice-to-have')
                level = 'error' if importance == 'critical' else 'warning' if importance == 'important' else 'info'
                
                issues.append({
                    'level': level,
                    'category': 'llm_omission', 
                    'message': omission.get('missing', 'Missing information detected'),
                    'suggestion': omission.get('suggestion', 'Consider adding the missing information'),
                    'source': 'ollama'
                })
            return issues
    except Exception as e:
        logger.debug(f"Failed to parse Ollama omission response: {e}")
    return []


class OllamaClient:
    """
    Client wrapper for Ollama with helper methods for startup checks.
    Provides is_available() and list_models() for health checks.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize OllamaClient."""
        self.ollama = Ollama(base_url=base_url)
    
    def is_available(self) -> bool:
        """
        Check if Ollama server is reachable.
        
        Returns:
            True if server is reachable, False otherwise
        """
        try:
            # Try to list models as a health check
            models = self.list_models()
            return True
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models from Ollama.
        
        Returns:
            List of model names
        """
        try:
            result = self.ollama._make_request('api/tags', {}, method='GET')
            models = result.get('models', [])
            return [m.get('name', '') for m in models if 'name' in m]
        except Exception as e:
            logger.warning(f"Failed to list Ollama models: {e}")
            return []
    
    def chat(self, model: str, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """Proxy to Ollama.chat()"""
        return self.ollama.chat(model, messages, **kwargs)
    
    def generate(self, model: str, prompt: str, **kwargs) -> str:
        """Proxy to Ollama.generate()"""
        return self.ollama.generate(model, prompt, **kwargs)
    
    def embed(self, model: str, inputs: Union[str, List[str]]) -> List[List[float]]:
        """Proxy to Ollama.embed()"""
        return self.ollama.embed(model, inputs)


# Create default global instance
_default_client = None

def get_ollama_client() -> OllamaClient:
    """Get or create default OllamaClient instance."""
    global _default_client
    if _default_client is None:
        _default_client = OllamaClient()
    return _default_client