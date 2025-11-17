# file: tbcv/core/path_validator.py
"""
File path validation and sanitization utilities
"""
from pathlib import Path
from typing import Optional, Union
import re
import os

class PathValidator:
    """Validates and sanitizes file paths to prevent directory traversal attacks"""
    
    # Dangerous patterns that could indicate path traversal
    DANGEROUS_PATTERNS = [
        r'\.\.',  # Parent directory
        r'~',     # Home directory
        r'\$',    # Environment variables
        r'%',     # Windows environment variables
    ]
    
    # System-critical paths that should never be written to
    PROTECTED_PATHS = [
        '/etc',
        '/sys',
        '/proc',
        '/dev',
        '/boot',
        'C:\Windows',
        'C:\System32',
    ]
    
    @staticmethod
    def is_safe_path(path: Union[str, Path], base_dir: Optional[Path] = None) -> bool:
        """
        Check if a path is safe to use
        
        Args:
            path: Path to validate
            base_dir: Optional base directory to constrain paths to
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            path_obj = Path(path).resolve()
            
            # Check for dangerous patterns
            path_str = str(path_obj)
            for pattern in PathValidator.DANGEROUS_PATTERNS:
                if re.search(pattern, str(path)):  # Check original path
                    return False
            
            # Check against protected paths
            for protected in PathValidator.PROTECTED_PATHS:
                if str(path_obj).startswith(protected):
                    return False
            
            # If base_dir provided, ensure path is within it
            if base_dir:
                base_resolved = Path(base_dir).resolve()
                try:
                    path_obj.relative_to(base_resolved)
                except ValueError:
                    return False  # Path is outside base_dir
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def sanitize_path(path: Union[str, Path], base_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Sanitize and validate a path
        
        Args:
            path: Path to sanitize
            base_dir: Optional base directory to constrain paths to
            
        Returns:
            Sanitized Path object or None if path is unsafe
        """
        if not PathValidator.is_safe_path(path, base_dir):
            return None
        
        try:
            return Path(path).resolve()
        except Exception:
            return None
    
    @staticmethod
    def validate_write_path(path: Union[str, Path], create_dirs: bool = False) -> bool:
        """
        Validate that a path is safe for writing
        
        Args:
            path: Path to validate
            create_dirs: If True, create parent directories
            
        Returns:
            True if path is safe for writing
        """
        if not PathValidator.is_safe_path(path):
            return False
        
        path_obj = Path(path)
        
        # Check parent directory exists or can be created
        if create_dirs:
            try:
                path_obj.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                return False
        elif not path_obj.parent.exists():
            return False
        
        # Check we have write permission
        try:
            if path_obj.exists():
                return os.access(path_obj, os.W_OK)
            else:
                return os.access(path_obj.parent, os.W_OK)
        except Exception:
            return False

# Convenience functions
def is_safe_path(path: Union[str, Path], base_dir: Optional[Path] = None) -> bool:
    """Check if a path is safe to use"""
    return PathValidator.is_safe_path(path, base_dir)

def sanitize_path(path: Union[str, Path], base_dir: Optional[Path] = None) -> Optional[Path]:
    """Sanitize and validate a path"""
    return PathValidator.sanitize_path(path, base_dir)

def validate_write_path(path: Union[str, Path], create_dirs: bool = False) -> bool:
    """Validate that a path is safe for writing"""
    return PathValidator.validate_write_path(path, create_dirs)
