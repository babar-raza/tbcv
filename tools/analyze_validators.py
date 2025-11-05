#!/usr/bin/env python
"""
Validator Inventory Analysis Tool
Analyzes content_validator and llm_validator to document capabilities.
"""

import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Any

def extract_methods(file_path: Path) -> List[Dict[str, Any]]:
    """Extract method definitions from a Python file."""
    methods = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get docstring
                docstring = ast.get_docstring(node) or ""
                
                # Extract parameters
                params = []
                for arg in node.args.args:
                    if arg.arg != 'self':
                        params.append(arg.arg)
                
                methods.append({
                    "name": node.name,
                    "line": node.lineno,
                    "params": params,
                    "docstring": docstring[:200],  # truncate long docs
                    "is_public": not node.name.startswith('_'),
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                })
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    
    return methods

def analyze_validator(file_path: Path) -> Dict[str, Any]:
    """Analyze a validator file and extract capabilities."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract imports
    imports = []
    for line in content.split('\n'):
        if line.strip().startswith(('import ', 'from ')):
            imports.append(line.strip())
    
    # Extract methods
    methods = extract_methods(file_path)
    
    # Extract handler registrations
    handler_pattern = r'self\.register_handler\(["\'](\w+)["\']'
    handlers = re.findall(handler_pattern, content)
    
    # Extract capabilities mentioned
    capabilities = []
    if 'validate_yaml' in content:
        capabilities.append('YAML/Front-matter validation')
    if 'validate_markdown' in content:
        capabilities.append('Markdown structure validation')
    if 'validate_code' in content:
        capabilities.append('Code quality validation')
    if 'validate_links' in content:
        capabilities.append('Link validation')
    if 'validate_structure' in content:
        capabilities.append('Content structure validation')
    if 'llm' in content.lower() or 'ollama' in content.lower():
        capabilities.append('LLM-based validation')
    if 'plugin' in content.lower():
        capabilities.append('Plugin detection/validation')
    if 'recommendation' in content.lower():
        capabilities.append('Recommendation generation')
    if 'truth' in content.lower():
        capabilities.append('Truth table usage')
    if 'rule' in content.lower():
        capabilities.append('Rule-based validation')
    
    # Check for DB interactions
    uses_db = 'db_manager' in content or 'database' in content
    
    # Check for validation result storage
    stores_results = 'create_validation_result' in content or 'store_validation' in content
    
    return {
        "file": str(file_path.name),
        "full_path": str(file_path),
        "line_count": len(content.split('\n')),
        "imports": imports[:10],  # First 10 imports
        "methods": methods,
        "public_methods": [m for m in methods if m['is_public']],
        "async_methods": [m for m in methods if m['is_async']],
        "registered_handlers": handlers,
        "capabilities": capabilities,
        "uses_db": uses_db,
        "stores_results": stores_results,
    }

def main():
    """Main analysis function."""
    project_root = Path('/home/claude')
    agents_dir = project_root / 'agents'
    
    inventory = {
        "analysis_timestamp": "2025-11-01T03:30:00Z",
        "validators": {}
    }
    
    # Analyze content_validator
    content_validator_path = agents_dir / 'content_validator.py'
    if content_validator_path.exists():
        print(f"Analyzing {content_validator_path}...")
        inventory["validators"]["content_validator"] = analyze_validator(content_validator_path)
    
    # Analyze llm_validator
    llm_validator_path = agents_dir / 'llm_validator.py'
    if llm_validator_path.exists():
        print(f"Analyzing {llm_validator_path}...")
        inventory["validators"]["llm_validator"] = analyze_validator(llm_validator_path)
    
    # Save inventory
    output_path = project_root / 'reports' / 'inventory' / 'validators_inventory.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8', newline='\r\n') as f:
        json.dump(inventory, f, indent=2)
    
    print(f"\nInventory saved to: {output_path}")
    print("\nSummary:")
    print(f"  content_validator: {len(inventory['validators']['content_validator']['capabilities'])} capabilities")
    print(f"  llm_validator: {len(inventory['validators']['llm_validator']['capabilities'])} capabilities")
    
    return inventory

if __name__ == '__main__':
    main()
