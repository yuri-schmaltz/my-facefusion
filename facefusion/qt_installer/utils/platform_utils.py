"""
FaceFusion Qt6 Installer - Platform Utilities
==============================================
Cross-platform path resolution and command utilities.
"""

import os
import sys
import shutil
from typing import Optional, List
from pathlib import Path


def is_windows() -> bool:
    return sys.platform.startswith('win')


def is_linux() -> bool:
    return sys.platform.startswith('linux')


def is_macos() -> bool:
    return sys.platform == 'darwin'


def get_python_executable() -> str:
    """Get the path to the Python executable."""
    return sys.executable


def get_pip_executable() -> str:
    """Get the path to pip, preferring the venv version."""
    # Check if we're in a venv
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # We're in a virtual environment
        if is_windows():
            pip_path = Path(sys.prefix) / 'Scripts' / 'pip.exe'
        else:
            pip_path = Path(sys.prefix) / 'bin' / 'pip'
        if pip_path.exists():
            return str(pip_path)
    
    # Fallback to python -m pip
    return f"{sys.executable} -m pip"


def which(command: str) -> Optional[str]:
    """Cross-platform which command."""
    return shutil.which(command)


def get_ffmpeg_path() -> Optional[str]:
    """Get path to FFmpeg executable."""
    return which('ffmpeg')


def get_npm_path() -> Optional[str]:
    """Get path to npm executable."""
    return which('npm')


def get_node_path() -> Optional[str]:
    """Get path to Node.js executable."""
    return which('node')


def get_install_path() -> Path:
    """Get the FaceFusion installation directory."""
    # Assume we're running from the project root
    return Path(os.getcwd())


def get_web_path() -> Path:
    """Get the web frontend directory."""
    return get_install_path() / 'web'


def get_requirements_path() -> Path:
    """Get the requirements.txt path."""
    return get_install_path() / 'requirements.txt'


def get_user_documents_path() -> Path:
    """Get the user's Documents folder, cross-platform."""
    if is_windows():
        try:
            import ctypes.wintypes
            CSIDL_PERSONAL = 5
            SHGFP_TYPE_CURRENT = 0
            buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
            ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
            return Path(buf.value)
        except Exception:
            pass
    
    return Path.home() / 'Documents'


def get_facefusion_data_path() -> Path:
    """Get FaceFusion user data directory."""
    return get_user_documents_path() / 'FaceFusion'


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def get_python_version() -> str:
    """Get Python version string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_python_version_tuple() -> tuple:
    """Get Python version as tuple (major, minor, micro)."""
    return (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)


def is_venv_active() -> bool:
    """Check if running inside a virtual environment."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)


def is_conda_active() -> bool:
    """Check if running inside a conda environment."""
    return 'CONDA_PREFIX' in os.environ
