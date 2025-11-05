# Location: scripts/tbcv/main.py
r"""
Unified entry point for the TBCV system.

- API mode: launches the FastAPI app via uvicorn
- Sanity checks for the active interpreter and uvicorn installation
- Helpful diagnostics for import shadowing or path issues
- NEW: auto-purge of __pycache__/ and *.pyc to avoid stale bytecode

Usage:
  (llm) D:\onedrive\Documents\GitHub\aspose.net\scripts\tbcv> python main.py --mode api
  (llm) D:\onedrive\Documents\GitHub\aspose.net\scripts\tbcv> python main.py --mode api --host 0.0.0.0 --port 8080 --reload
"""

from __future__ import annotations

import argparse
import sys
import os
import shutil
from pathlib import Path
from typing import Optional, Tuple

def _ensure_project_on_path() -> Path:
    """
    Ensure the project root (folder that contains the 'tbcv' package) is on sys.path.
    We assume this file lives at scripts/tbcv/main.py, so the package root is scripts/.
    Returns the project_root Path for reuse.
    """
    here = Path(__file__).resolve()
    scripts_dir = here.parent  # .../scripts/tbcv
    project_root = scripts_dir.parent  # .../scripts
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return project_root

def _print_env_header() -> None:
    """Print a short header describing the active Python and cwd for quick debugging."""
    print(f"Python: {sys.executable}")
    print(f"Version: {sys.version.split()[0]}")
    print(f"CWD: {os.getcwd()}")

def _purge_bytecode(project_root: Path) -> Tuple[int, int]:
    """
    Remove stale Python bytecode so imports don't see ghost modules:
      - Deletes all __pycache__/ directories under project_root
      - Deletes all *.pyc files under project_root
    Returns (dirs_removed, files_removed) for a concise summary.
    """
    dirs_removed = 0
    files_removed = 0

    # 1) Remove __pycache__ folders first
    for cache_dir in project_root.rglob("__pycache__"):
        try:
            shutil.rmtree(cache_dir, ignore_errors=True)
            dirs_removed += 1
        except Exception:
            # Ignore deletion issues; we only want best-effort cleanup
            pass

    # 2) Remove .pyc files (in case any remain outside __pycache__)
    for pyc in project_root.rglob("*.pyc"):
        try:
            pyc.unlink(missing_ok=True)
            files_removed += 1
        except Exception:
            pass

    return dirs_removed, files_removed

def _validate_schemas() -> bool:
    """
    Validate JSON schemas for truth tables at startup.
    Returns True if all schemas are valid, False otherwise.
    """
    try:
        import json
        from pathlib import Path
        
        # Find truth table files
        project_root = Path(__file__).parent
        truth_files = list(project_root.glob("truth/*.json"))
        rule_files = list(project_root.glob("rules/*.json"))
        
        print(f"Validating {len(truth_files)} truth files and {len(rule_files)} rule files...")
        
        for file_path in truth_files + rule_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Basic validation - ensure it's valid JSON and has expected structure
                if isinstance(data, dict) and len(data) > 0:
                    print(f"✓ Schema valid: {file_path.name}")
                else:
                    print(f"✗ Schema invalid: {file_path.name} - empty or invalid structure")
                    return False
            except json.JSONDecodeError as e:
                print(f"✗ JSON error in {file_path.name}: {e}")
                return False
            except Exception as e:
                print(f"✗ Error validating {file_path.name}: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"Error during schema validation: {e}")
        return False

def _import_uvicorn_or_die():
    """
    Import uvicorn with clear diagnostics.
    - Detects module shadowing (e.g., a local file/folder named 'uvicorn.py' or 'uvicorn')
    """
    try:
        import uvicorn  # type: ignore
    except Exception as e:
        print("Error: uvicorn is required for API mode. Install with: pip install uvicorn")
        print(f"Import details: {type(e).__name__}: {e}")
        # Extra hint: check for shadowing
        suspicious = []
        for p in map(Path, sys.path):
            if (p / "uvicorn.py").exists() or (p / "uvicorn" / "__init__.py").exists():
                suspicious.append(str(p))
        if suspicious:
            print("Hint: You may have a local module shadowing uvicorn in one of these paths:")
            for s in suspicious:
                print(f"  - {s}")
        sys.exit(1)
    else:
        # Confirm where uvicorn is imported from
        try:
            print(f"uvicorn loaded from: {uvicorn.__file__}")
        except Exception:
            pass
        return uvicorn

def run_api(host: str, port: int, reload: bool, log_level: str, clean: bool) -> None:
    """
    Start the FastAPI server (tbcv.api.server:app) using uvicorn.
    If 'clean' is True, purge stale bytecode before launching to avoid duplicate/ghost imports.
    """
    project_root = _ensure_project_on_path()

    if clean:
        d, f = _purge_bytecode(project_root)
        print(f"Bytecode purge: removed {d} __pycache__ dirs, {f} *.pyc files under {project_root}")

    # Validate schemas at startup (Requirement A03)
    print("Validating truth table and rule schemas...")
    if not _validate_schemas():
        print("Error: Schema validation failed. Aborting startup.")
        sys.exit(1)
    print("✓ All schemas validated successfully")

    uvicorn = _import_uvicorn_or_die()

    # Light sanity check: can we import the app?
    try:
        # Try direct import first, then fallback to module path
        try:
            from api.server import app
            print(f"Starting API: Direct import at http://{host}:{port} (reload={reload}, log_level={log_level})")
            uvicorn.run(
                app,
                host=host,
                port=port,
                reload=reload,
                log_level=log_level,
            )
        except ImportError:
            app_path = "tbcv.api.server:app"
            print(f"Starting API: {app_path} at http://{host}:{port} (reload={reload}, log_level={log_level})")
            uvicorn.run(
                app_path,
                host=host,
                port=port,
                reload=reload,
                log_level=log_level,
            )
    except Exception as e:
        print(f"Failed to start API: {e}")
        # If import failed, give helpful hints
        print("Troubleshooting tips:")
        print("  1) Ensure you run from the 'scripts' folder or a repo root that has 'tbcv' on PYTHONPATH.")
        print("  2) Verify that 'scripts/tbcv/api/server.py' exists and defines 'app'.")
        print("  3) Avoid naming any local files/folders 'uvicorn' or 'fastapi'.")
        sys.exit(1)

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TBCV entry point")
    parser.add_argument(
        "--mode",
        choices=["api"],
        required=True,
        help="Run mode. Use 'api' to start the FastAPI server.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind (default: 8080)")
    parser.add_argument("--reload", action="store_true", help="Enable auto reload")
    parser.add_argument("--log-level", default="info", help="Uvicorn log level (default: info)")
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip purging __pycache__ and *.pyc before launching (default is to purge).",
    )
    return parser.parse_args(argv)

def main(argv: Optional[list[str]] = None) -> None:
    _print_env_header()
    args = parse_args(argv)

    if args.mode == "api":
        run_api(args.host, args.port, args.reload, args.log_level, clean=not args.no_clean)
    else:
        print("Unknown mode. Use --mode api")
        sys.exit(2)

if __name__ == "__main__":
    main()
