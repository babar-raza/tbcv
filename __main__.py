# file: tbcv/__main__.py
"""
CLI entry point for TBCV that works from any current working directory (O01).
Provides package-based imports and proper path handling.

Usage:
    python -m tbcv validate file.md
    python -m tbcv enhance file.md --preview
    python -m tbcv start-api --port 8080
"""

from __future__ import annotations

import sys
import os
from pathlib import Path

def ensure_package_imports():
    """Ensure TBCV package is importable from any working directory."""
    # Add the parent directory of this package to sys.path if needed
    package_dir = Path(__file__).parent.parent
    if str(package_dir) not in sys.path:
        sys.path.insert(0, str(package_dir))

def main():
    """Main CLI entry point that works from any directory."""
    ensure_package_imports()
    
    # Import CLI after ensuring proper path setup
    try:
        from cli.main import cli
        cli(obj={})
    except ImportError as e:
        print(f"Error importing TBCV CLI: {e}")
        print("Make sure you're running from a directory where TBCV is installed.")
        print("Try: python -m pip install -e . (from the project root)")
        sys.exit(1)

if __name__ == "__main__":
    main()
