# file: tbcv/core/io_win.py
"""
Windows-specific I/O utilities with CRLF line ending preservation.
Part of TBCV system - ensures Windows line endings are preserved across all file operations.
"""

import os
import tempfile
from pathlib import Path
from typing import Union, Optional


def read_text(file_path: Union[str, Path], encoding: str = "utf-8") -> str:
    """
    Read text file preserving original line endings.
    
    Args:
        file_path: Path to the file to read
        encoding: Text encoding (default: utf-8)
        
    Returns:
        File content as string with preserved line endings
    """
    with open(file_path, "r", encoding=encoding, newline="") as f:
        return f.read()


def write_text_crlf(
    file_path: Union[str, Path], 
    content: str, 
    encoding: str = "utf-8",
    atomic: bool = False
) -> None:
    """
    Write text file with Windows CRLF line endings.
    
    Args:
        file_path: Path to the file to write
        content: Text content to write
        encoding: Text encoding (default: utf-8)
        atomic: If True, use atomic write (temp file + rename)
    """
    # Normalize to CRLF
    content = content.replace("\r\n", "\n").replace("\n", "\r\n")
    
    if atomic:
        # Atomic write using temp file
        file_path = Path(file_path)
        temp_path = None
        try:
            # Create temp file in same directory
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding=encoding,
                newline="",
                dir=file_path.parent,
                delete=False,
                suffix=".tmp"
            ) as temp_file:
                temp_path = temp_file.name
                temp_file.write(content)
            
            # Atomic rename
            os.replace(temp_path, file_path)
            
        except Exception:
            # Cleanup temp file on error
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            raise
    else:
        # Direct write
        with open(file_path, "w", encoding=encoding, newline="") as f:
            f.write(content)


def ensure_directory(dir_path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, creating it if necessary.
    
    Args:
        dir_path: Directory path to ensure
        
    Returns:
        Path object for the directory
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_markdown_files(root_path: Union[str, Path], recursive: bool = True) -> list[Path]:
    """
    List all Markdown files in a directory.
    
    Args:
        root_path: Root directory to search
        recursive: If True, search recursively
        
    Returns:
        List of Path objects for .md files
    """
    root = Path(root_path)
    if not root.exists():
        return []
    
    if recursive:
        return list(root.rglob("*.md"))
    else:
        return list(root.glob("*.md"))


def backup_file(file_path: Union[str, Path], suffix: str = ".bak") -> Optional[Path]:
    """
    Create a backup copy of a file.
    
    Args:
        file_path: File to backup
        suffix: Backup file suffix
        
    Returns:
        Path to backup file, or None if original doesn't exist
    """
    source = Path(file_path)
    if not source.exists():
        return None
    
    backup_path = source.with_suffix(source.suffix + suffix)
    content = read_text(source)
    write_text_crlf(backup_path, content)
    
    return backup_path
