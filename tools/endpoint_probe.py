# file: tbcv/tools/endpoint_probe.py
"""
Endpoint probing utilities - compatibility layer for tests.
Part of TBCV system endpoint testing framework.
"""

import json
import time
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import http.client
import urllib.parse

from core.io_win import write_text_crlf


class ProbeMode(Enum):
    """Probe mode enumeration."""
    OFFLINE = "offline"
    LIVE = "live"


class EndpointDiscovery:
    """Discover endpoints from application or static analysis."""
    
    def __init__(self):
        self.discovered_endpoints = []
    
    def discover_from_app(self, app) -> List[Dict[str, Any]]:
        """Discover endpoints from FastAPI app instance."""
        endpoints = []
        for route in getattr(app, "routes", []):
            path = getattr(route, "path", None)
            methods = list(getattr(route, "methods", [])) or ["*"]
            name = getattr(route, "name", None)
            if path:
                endpoints.append({
                    "path": path,
                    "methods": sorted(methods),
                    "name": name
                })
        self.discovered_endpoints = endpoints
        return endpoints
    
    def discover_registered(self, app) -> List[Dict[str, Any]]:
        """Alias for discover_from_app for compatibility."""
        return self.discover_from_app(app)
    
    def discover_static(self, project_root: str = ".") -> List[Dict[str, Any]]:
        """Discover endpoints through static analysis."""
        # Import the static scan function from endpoint_check
        import os
        import re
        
        results = []
        for dirpath, _, filenames in os.walk(project_root):
            for fn in filenames:
                if fn.endswith(".py"):
                    p = os.path.join(dirpath, fn)
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as f:
                            src = f.read()
                    except Exception:
                        continue
                    
                    # Find route decorators
                    for m in re.finditer(r"@(?:[a-zA-Z_][\w\.]*)\.(get|post|put|patch|delete|options|head)\(\s*([\"\'])(/[^\"\']*)\2", src):
                        method = m.group(1).upper()
                        path = m.group(3)
                        results.append({
                            "path": path, 
                            "methods": [method], 
                            "module": os.path.relpath(p, project_root).replace('\\','/')
                        })
        
        self.discovered_endpoints = results
        return results


class EndpointProber:
    """Probe endpoints for live testing."""
    
    def __init__(self, mode: ProbeMode, base_url: Optional[str] = None):
        self.mode = mode
        self.base_url = base_url or "http://127.0.0.1:8080"
        
    def probe_endpoints(self, endpoints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Probe a list of endpoints."""
        results = []
        for endpoint in endpoints:
            path = endpoint.get("path", "")
            if self.mode == ProbeMode.LIVE:
                result = self._http_probe(path)
                results.append({
                    "path": path,
                    "methods": endpoint.get("methods", []),
                    "probe_result": result
                })
            else:
                # Offline mode - just return the endpoint info
                results.append({
                    "path": path,
                    "methods": endpoint.get("methods", []),
                    "offline": True
                })
        return results
    
    def _http_probe(self, path: str, timeout: float = 3.0) -> Dict[str, Any]:
        """Perform HTTP probe of an endpoint."""
        url = urllib.parse.urljoin(self.base_url.rstrip('/') + '/', path.lstrip('/'))
        parsed = urllib.parse.urlparse(url)
        
        conn = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=timeout)
        headers = {}
        
        start_time = time.time()
        try:
            conn.request("GET", parsed.path + (("?" + parsed.query) if parsed.query else ""), headers=headers)
            resp = conn.getresponse()
            body = resp.read()
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            try:
                preview = body.decode("utf-8", errors="ignore")[:512]
                json_data = None
                try:
                    json_data = json.loads(preview)
                except Exception:
                    pass
                
                return {
                    "status_code": resp.status,
                    "elapsed_ms": elapsed_ms,
                    "body_preview": preview,
                    "json": json_data,
                    "success": True
                }
            except Exception as e:
                return {
                    "status_code": resp.status,
                    "elapsed_ms": elapsed_ms,
                    "error": str(e),
                    "success": False
                }
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "status_code": None,
                "elapsed_ms": elapsed_ms,
                "error": str(e),
                "success": False
            }
        finally:
            try:
                conn.close()
            except Exception:
                pass


class ReportGenerator:
    """Generate endpoint probe reports."""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, 
                       results: List[Dict[str, Any]], 
                       discovery: EndpointDiscovery, 
                       mode: ProbeMode, 
                       base_url: Optional[str] = None) -> Path:
        """Generate a comprehensive probe report."""
        
        report = {
            "mode": mode.value,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "base_url": base_url,
            "summary": {
                "total_endpoints": len(results),
                "discovered_endpoints": len(discovery.discovered_endpoints)
            },
            "endpoints": results,
            "discovered": discovery.discovered_endpoints
        }
        
        if mode == ProbeMode.LIVE:
            # Add success/failure stats for live probes
            successful = sum(1 for r in results if r.get("probe_result", {}).get("success", False))
            report["summary"]["successful_probes"] = successful
            report["summary"]["failed_probes"] = len(results) - successful
        
        # Generate filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"endpoint_probe_{mode.value}_{timestamp}.json"
        output_path = self.output_dir / filename
        
        # Write report with CRLF line endings
        report_json = json.dumps(report, indent=2)
        write_text_crlf(output_path, report_json)
        
        return output_path
