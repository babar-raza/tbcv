# file: core\ollama_validator.py
"""
Ollama LLM integration for content validation.
Provides contradiction detection and omission checking.
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger(__name__)

class OllamaValidator:
    """Integration with local Ollama for content validation."""
    
    def __init__(self):
        self.model = os.getenv('OLLAMA_MODEL', 'mistral')
        self.base_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        self.enabled = os.getenv('OLLAMA_ENABLED', 'true').lower() == 'true' and aiohttp is not None
        self.timeout = int(os.getenv('OLLAMA_TIMEOUT', '30'))
        
        if not aiohttp:
            self.enabled = False
            logger.warning("aiohttp not available, Ollama validation disabled")
        
    async def validate_content_contradictions(self, content: str, plugin_info: List[Dict], 
                                            family_rules: Dict[str, Any]) -> List[Dict]:
        """Check content for contradictions using LLM."""
        if not self.enabled:
            return []
            
        try:
            prompt = self._build_contradiction_prompt(content, plugin_info, family_rules)
            response = await self._call_ollama(prompt)
            return self._parse_contradiction_response(response)
        except Exception as e:
            logger.warning(f"Ollama contradiction validation failed: {e}")
            return []
            
    async def validate_content_omissions(self, content: str, plugin_info: List[Dict],
                                       family_rules: Dict[str, Any]) -> List[Dict]:
        """Check content for missing information using LLM."""
        if not self.enabled:
            return []
            
        try:
            prompt = self._build_omission_prompt(content, plugin_info, family_rules)
            response = await self._call_ollama(prompt)
            return self._parse_omission_response(response)
        except Exception as e:
            logger.warning(f"Ollama omission validation failed: {e}")
            return []
            
    def _build_contradiction_prompt(self, content: str, plugin_info: List[Dict], 
                                  family_rules: Dict[str, Any]) -> str:
        """Build prompt for contradiction detection."""
        api_patterns = family_rules.get('api_patterns', {})
        validation_reqs = family_rules.get('validation_requirements', {})
        
        return f"""
Analyze this technical content for factual contradictions:

CONTENT:
{content[:2000]}

DETECTED PLUGINS:
{json.dumps(plugin_info, indent=2)}

API PATTERNS EXPECTED:
{json.dumps(api_patterns, indent=2)}

VALIDATION REQUIREMENTS:
{json.dumps(validation_reqs, indent=2)}

Check for:
1. Incorrect API usage patterns
2. Wrong format claims  
3. Incompatible plugin combinations
4. Outdated method references
5. Missing required imports or dependencies

Respond with JSON: {{"contradictions": [{{"issue": "description", "severity": "high|medium|low", "location": "code|text|yaml"}}]}}
"""

    def _build_omission_prompt(self, content: str, plugin_info: List[Dict],
                             family_rules: Dict[str, Any]) -> str:
        """Build prompt for omission detection."""
        validation_reqs = family_rules.get('validation_requirements', {})
        code_rules = family_rules.get('code_quality_rules', {})
        
        return f"""
Analyze this technical content for missing important information:

CONTENT:
{content[:2000]}

DETECTED PLUGINS:
{json.dumps(plugin_info, indent=2)}

VALIDATION REQUIREMENTS:
{json.dumps(validation_reqs, indent=2)}

CODE QUALITY RULES:
{json.dumps(code_rules, indent=2)}

Check for missing:
1. Required using/import statements
2. Error handling patterns
3. Resource disposal (using statements)
4. Plugin dependencies explanation
5. Performance considerations
6. Security best practices

Respond with JSON: {{"omissions": [{{"missing": "description", "importance": "critical|important|nice-to-have", "suggestion": "how to fix"}}]}}
"""

    async def _call_ollama(self, prompt: str) -> str:
        """Make API call to Ollama."""
        if not aiohttp:
            return ""
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,
                            "top_p": 0.9,
                            "stop": ["```", "---"]
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '')
                    else:
                        logger.warning(f"Ollama returned status {response.status}")
                        return ""
        except Exception as e:
            logger.info(f"Ollama service not available: {e}")
            return ""
                
    def _parse_contradiction_response(self, response: str) -> List[Dict]:
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
            
    def _parse_omission_response(self, response: str) -> List[Dict]:
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

# Global instance
ollama_validator = OllamaValidator()