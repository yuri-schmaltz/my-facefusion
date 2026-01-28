"""
Path Security and Validation
----------------------------
Prevents path traversal, symlink attacks, and access outside allowed directories.
"""
import os
from typing import List, Optional


class PathSecurityError(Exception):
    """Raised when a path fails security validation."""
    pass


# Default allowed directories
DEFAULT_ALLOWED_DIRS = [
    os.path.expanduser("~"),
    "/tmp",
]


def get_workspace_root() -> str:
    """Get the FaceFusion workspace root directory."""
    # Try to get from environment or use current directory
    return os.environ.get('FACEFUSION_WORKSPACE', os.getcwd())


def get_allowed_directories() -> List[str]:
    """Get list of allowed directories for file operations."""
    allowed = list(DEFAULT_ALLOWED_DIRS)
    
    # Add workspace root
    workspace = get_workspace_root()
    if workspace not in allowed:
        allowed.append(workspace)
    
    # Add jobs directory
    jobs_dir = os.path.join(workspace, '.jobs')
    if jobs_dir not in allowed:
        allowed.append(jobs_dir)
    
    return allowed


def validate_path(
    path: str,
    allowed_dirs: Optional[List[str]] = None,
    must_exist: bool = False,
    allow_create: bool = False
) -> str:
    """
    Validate and normalize a path for security.
    
    Args:
        path: The path to validate
        allowed_dirs: List of allowed root directories (None = use defaults)
        must_exist: If True, path must exist
        allow_create: If True and must_exist is False, parent must exist
    
    Returns:
        Normalized absolute path
        
    Raises:
        PathSecurityError: If path fails validation
    """
    if not path:
        raise PathSecurityError("Empty path")
    
    # Normalize and resolve to absolute path
    path = path.strip().strip('"\'')
    
    # Block obvious traversal attempts before resolution
    if '..' in path.split(os.sep):
        raise PathSecurityError(f"Path traversal detected (..): {path}")
    
    # Resolve to absolute path (follows symlinks)
    try:
        real_path = os.path.realpath(os.path.abspath(path))
    except (OSError, ValueError) as e:
        raise PathSecurityError(f"Invalid path: {path} ({e})")
    
    # Get allowed directories
    allowed = allowed_dirs or get_allowed_directories()
    allowed_real = [os.path.realpath(os.path.abspath(d)) for d in allowed]
    
    # Check if path is within allowed directories
    is_allowed = any(
        real_path == allowed_dir or real_path.startswith(allowed_dir + os.sep)
        for allowed_dir in allowed_real
    )
    
    if not is_allowed:
        raise PathSecurityError(
            f"Path outside allowed directories: {path}\n"
            f"Allowed: {allowed}"
        )
    
    # Check existence requirements
    if must_exist and not os.path.exists(real_path):
        raise PathSecurityError(f"Path does not exist: {path}")
    
    if allow_create and not must_exist:
        parent = os.path.dirname(real_path)
        if parent and not os.path.exists(parent):
            raise PathSecurityError(f"Parent directory does not exist: {parent}")
    
    return real_path


def validate_input_path(path: str) -> str:
    """Validate an input file path (must exist and be readable)."""
    real_path = validate_path(path, must_exist=True)
    
    if not os.path.isfile(real_path):
        raise PathSecurityError(f"Not a file: {path}")
    
    if not os.access(real_path, os.R_OK):
        raise PathSecurityError(f"File not readable: {path}")
    
    return real_path


def validate_output_path(path: str) -> str:
    """Validate an output file path (parent must exist and be writable)."""
    real_path = validate_path(path, must_exist=False, allow_create=True)
    
    parent = os.path.dirname(real_path)
    if parent and not os.access(parent, os.W_OK):
        raise PathSecurityError(f"Directory not writable: {parent}")
    
    return real_path


def validate_directory_path(path: str, must_exist: bool = True) -> str:
    """Validate a directory path."""
    real_path = validate_path(path, must_exist=must_exist)
    
    if must_exist and not os.path.isdir(real_path):
        raise PathSecurityError(f"Not a directory: {path}")
    
    return real_path


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing dangerous characters.
    
    Only allows alphanumeric, dash, underscore, and dot.
    """
    # Get just the filename part
    basename = os.path.basename(filename)
    
    # Replace dangerous characters
    sanitized = ""
    for char in basename:
        if char.isalnum() or char in '-_.':
            sanitized += char
        else:
            sanitized += '_'
    
    # Prevent hidden files
    if sanitized.startswith('.'):
        sanitized = '_' + sanitized[1:]
    
    # Ensure not empty
    if not sanitized:
        sanitized = "unnamed"
    
    return sanitized
