import os
import shutil
import sys
from argparse import ArgumentParser
from pathlib import Path

def get_platform():
    if sys.platform.startswith('linux'):
        return 'linux'
    elif sys.platform.startswith('win'):
        return 'windows'
    return 'unknown'

def create_linux_desktop_file(install_path):
    desktop_file = f"""[Desktop Entry]
Name=FaceFusion
Comment=Next generation face swapper and enhancer
Exec={sys.executable} {os.path.join(install_path, 'facefusion.py')} run
Icon={os.path.join(install_path, 'facefusion.ico')}
Terminal=true
Type=Application
Categories=Graphics;Video;
"""
    
    desktop_path = os.path.expanduser('~/.local/share/applications/facefusion.desktop')
    os.makedirs(os.path.dirname(desktop_path), exist_ok=True)
    
    with open(desktop_path, 'w') as f:
        f.write(desktop_file)
    
    print(f"Created Linux desktop entry at: {desktop_path}")
    print("You may need to log out and back in or run 'update-desktop-database' for it to appear.")

def create_windows_launcher(install_path):
    # simpler approach: create a run.bat and a FaceFusion.url shortcut
    bat_content = f"""@echo off
cd /d "{install_path}"
"{sys.executable}" facefusion.py run
pause
"""
    bat_path = os.path.join(install_path, 'run.bat')
    with open(bat_path, 'w') as f:
        f.write(bat_content)
    
    print(f"Created Windows batch launcher at: {bat_path}")
    print("You can right-click 'run.bat' and 'Send to Desktop (create shortcut)'")

def create_user_config(install_path):
    user_config_path = os.path.join(install_path, 'user.ini')
    if os.path.exists(user_config_path):
        print(f"user.ini already exists at: {user_config_path}, skipping creation.")
        return

    documents_path = os.path.expanduser('~/Documents')
    if sys.platform.startswith('win'):
        import ctypes.wintypes
        CSIDL_PERSONAL = 5       # My Documents
        SHGFP_TYPE_CURRENT = 0   # Get current, not default value
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf)
        documents_path = buf.value

    facefusion_docs = os.path.join(documents_path, 'FaceFusion')
    output_path = os.path.join(facefusion_docs, 'Output')
    # jobs_path = os.path.join(facefusion_docs, 'Jobs') # optional

    config_content = f"""[paths]
output_path = {output_path}

[uis]
# ui_theme = ocean

# Add other overrides here
"""
    with open(user_config_path, 'w') as f:
        f.write(config_content)
    
    print(f"Created standard user.ini at: {user_config_path}")
    print(f"Output path set to: {output_path}")

def main():
    install_path = os.path.dirname(os.path.abspath(__file__))
    # Assuming this script is in root or scripts/. Let's assume root for now or handle it.
    # If in scripts/, parent is root.
    if os.path.basename(install_path) == 'scripts':
        install_path = os.path.dirname(install_path)

    create_user_config(install_path)

    platform = get_platform()
    if platform == 'linux':
        create_linux_desktop_file(install_path)
    elif platform == 'windows':
        create_windows_launcher(install_path)
    else:
        print(f"Unsupported platform: {platform}")

if __name__ == '__main__':
    main()
