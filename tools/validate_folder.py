#!/usr/bin/env python
"""
Validate Folder Tool
Recursively validates .md files in a folder using the merged validator.
Usage: python tools/validate_folder.py --input PATH_TO_MD_FOLDER
"""

import sys
import asyncio
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.base import agent_registry
from agents.orchestrator import OrchestratorAgent
from core.database import db_manager
from core.logging import setup_logging, get_logger

logger = get_logger(__name__)

async def validate_folder(input_path: str) -> dict:
    """Validate all markdown files in a folder."""
    
    # Initialize logging
    setup_logging()
    
    # Initialize database
    try:
        db_manager.connect()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return {
            "status": "error",
            "message": f"Database connection failed: {e}",
            "files_validated": 0
        }
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent("cli_orchestrator")
    
    try:
        # Validate directory
        result = await orchestrator.handle_validate_directory({
            "directory_path": input_path,
            "file_pattern": "*.md",
            "max_workers": 4,
            "family": "words"
        })
        
        logger.info(f"Validation completed: {result.get('files_validated', 0)} files")
        
        return result
        
    except Exception as e:
        logger.exception("Validation failed")
        return {
            "status": "error",
            "message": str(e),
            "files_validated": 0
        }
    finally:
        # Cleanup
        try:
            db_manager.disconnect()
        except:
            pass

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Validate markdown files in a folder')
    parser.add_argument('--input', required=True, help='Path to folder containing .md files')
    parser.add_argument('--output', default='reports/validation_summary.json', 
                       help='Output path for validation summary')
    
    args = parser.parse_args()
    
    # Validate input path
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    
    if not input_path.is_dir():
        print(f"Error: Input path is not a directory: {input_path}")
        sys.exit(1)
    
    print(f"Validating markdown files in: {input_path}")
    print("=" * 60)
    
    # Run validation
    result = asyncio.run(validate_folder(str(input_path)))
    
    # Display results
    print(f"\nStatus: {result.get('status', 'unknown')}")
    print(f"Files total: {result.get('files_total', 0)}")
    print(f"Files validated: {result.get('files_validated', 0)}")
    print(f"Files failed: {result.get('files_failed', 0)}")
    
    if result.get('errors'):
        print(f"\nErrors:")
        for error in result.get('errors', [])[:5]:
            print(f"  - {error}")
    
    # Save summary
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "input_path": str(input_path),
        "result": result
    }
    
    with open(output_path, 'w', encoding='utf-8', newline='\r\n') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: {output_path}")
    
    # Exit code based on validation status
    if result.get('status') == 'completed' and result.get('files_failed', 0) == 0:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
