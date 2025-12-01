# file: core/file_utils.py
"""
File utilities for validation file path handling.

Provides functions to:
- Normalize file paths to absolute paths
- Copy temporary files to permanent storage
- Validate file existence
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime

from core.logging import get_logger

logger = get_logger(__name__)


def get_validation_storage_dir() -> Path:
    """
    Get or create the permanent storage directory for validated files.

    Returns:
        Path to validation storage directory
    """
    storage_dir = Path("data/validated_files")
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


def is_temp_file(file_path: str) -> bool:
    """
    Check if a file path is in a temporary directory.

    Args:
        file_path: Path to check

    Returns:
        True if file is in temp directory
    """
    temp_dir = tempfile.gettempdir()
    try:
        path = Path(file_path).resolve()
        temp_path = Path(temp_dir).resolve()
        return str(path).startswith(str(temp_path))
    except Exception:
        return False


def normalize_file_path(file_path: str, content: Optional[str] = None, copy_temp: bool = True) -> Tuple[str, bool]:
    """
    Normalize a file path for validation storage.

    Handles:
    1. Converts relative paths to absolute paths
    2. Copies temp files to permanent storage
    3. Validates file existence

    Args:
        file_path: Original file path (can be relative, absolute, or temp)
        content: Optional file content (used if temp file needs to be saved)
        copy_temp: If True, copy temp files to permanent storage

    Returns:
        Tuple of (normalized_absolute_path, was_temp_file)
    """
    try:
        path = Path(file_path)

        # Check if it's a temp file
        is_temp = is_temp_file(str(path))

        # If it's a temp file and we have content, save it permanently
        if is_temp and copy_temp:
            logger.info(f"Detected temp file: {file_path}, copying to permanent storage")

            # Create a permanent copy
            storage_dir = get_validation_storage_dir()

            # Generate a unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            original_name = path.stem
            extension = path.suffix
            permanent_name = f"{original_name}_{timestamp}{extension}"
            permanent_path = storage_dir / permanent_name

            # Copy or save content
            if path.exists():
                shutil.copy2(path, permanent_path)
                logger.info(f"Copied temp file to: {permanent_path}")
            elif content:
                permanent_path.write_text(content, encoding='utf-8')
                logger.info(f"Saved content to: {permanent_path}")
            else:
                logger.warning(f"Temp file doesn't exist and no content provided: {file_path}")
                # Return absolute path anyway
                return str(path.resolve()), is_temp

            return str(permanent_path.resolve()), is_temp

        # If not temp, just convert to absolute path
        if not path.is_absolute():
            abs_path = path.resolve()
            logger.debug(f"Converted relative path to absolute: {file_path} -> {abs_path}")
            return str(abs_path), is_temp

        # Already absolute
        return str(path), is_temp

    except Exception as e:
        logger.error(f"Error normalizing file path '{file_path}': {e}")
        # Fallback: try to make it absolute
        try:
            return str(Path(file_path).resolve()), False
        except Exception:
            # Last resort: return as-is
            return file_path, False


def validate_file_exists(file_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a file exists and is readable.

    Args:
        file_path: Path to validate

    Returns:
        Tuple of (exists, error_message)
        - (True, None) if file exists and is readable
        - (False, error_message) if there's a problem
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return False, f"File not found: {file_path}"

        if not path.is_file():
            return False, f"Path is not a file: {file_path}"

        # Try to read the file to ensure it's accessible
        try:
            with open(path, 'r', encoding='utf-8') as f:
                f.read(1)  # Just read one character to test
        except Exception as e:
            return False, f"File not readable: {file_path} ({e})"

        return True, None

    except Exception as e:
        return False, f"Error validating file: {file_path} ({e})"


def get_file_info(file_path: str) -> dict:
    """
    Get detailed information about a file for error messages.

    Args:
        file_path: Path to analyze

    Returns:
        Dict with file information
    """
    info = {
        "path": file_path,
        "exists": False,
        "is_absolute": False,
        "is_temp": False,
        "resolved_path": None,
    }

    try:
        path = Path(file_path)
        info["is_absolute"] = path.is_absolute()
        info["is_temp"] = is_temp_file(file_path)

        try:
            info["resolved_path"] = str(path.resolve())
            info["exists"] = path.exists()

            if info["exists"]:
                info["is_file"] = path.is_file()
                info["size"] = path.stat().st_size if path.is_file() else None
        except Exception as e:
            info["error"] = str(e)

    except Exception as e:
        info["error"] = str(e)

    return info
