#!/usr/bin/env python3
"""
FaceFusion Installer Entry Point
================================
Tries Qt6 installer first, falls back to Tkinter, then CLI.
"""

import os
import sys

# macOS compatibility
os.environ['SYSTEM_VERSION_COMPAT'] = '0'


def run_qt_installer() -> bool:
    """Try to run the Qt6 installer."""
    try:
        from facefusion.qt_installer.main import run
        sys.exit(run())
    except ImportError as e:
        print(f"Qt6 installer not available: {e}")
        return False
    except Exception as e:
        print(f"Qt6 installer failed: {e}")
        return False


def run_tkinter_installer() -> bool:
    """Try to run the Tkinter installer."""
    try:
        from facefusion import gui_installer
        gui_installer.run()
        return True
    except ImportError:
        print("Tkinter installer not available")
        return False
    except Exception as e:
        print(f"Tkinter installer failed: {e}")
        return False


def run_cli_installer() -> bool:
    """Run the CLI installer as last resort."""
    try:
        from facefusion import installer
        installer.cli()
        return True
    except Exception as e:
        print(f"CLI installer failed: {e}")
        return False


def main():
    """Main entry point with graceful fallback chain."""
    print("FaceFusion Installer")
    print("=" * 40)
    
    # Check for --cli flag to skip GUI
    if '--cli' in sys.argv:
        print("Running CLI installer (--cli flag detected)")
        run_cli_installer()
        return
    
    # Try installers in order of preference
    print("Attempting Qt6 installer...")
    if not run_qt_installer():
        print("Attempting Tkinter installer...")
        if not run_tkinter_installer():
            print("Falling back to CLI installer...")
            run_cli_installer()


if __name__ == '__main__':
    main()
