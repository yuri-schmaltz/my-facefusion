# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# Dynamically gather hidden imports for local modules
hidden_modules = [
    'facefusion.locales',
    'facefusion.app_context',
    'facefusion.conda',
    'facefusion.core',
    'facefusion.state_manager',
    'facefusion.program',
    'facefusion.args',
    'facefusion.jobs',
    'facefusion.filesystem',
    'facefusion.logger',
    'facefusion.translator',
    'facefusion.process_manager',
    'facefusion.inference_manager',
    'facefusion.execution',
    'facefusion.exit_helper',
    'facefusion.time_helper',
    'facefusion.common_helper',
    'facefusion.types',
    'facefusion.metadata',
]

# Processors
processors_dir = os.path.join('facefusion', 'processors', 'modules')
if os.path.exists(processors_dir):
    for entry in os.listdir(processors_dir):
        entry_path = os.path.join(processors_dir, entry)
        if os.path.isdir(entry_path) and not entry.startswith('__'):
            hidden_modules.append(f'facefusion.processors.modules.{entry}')
            hidden_modules.append(f'facefusion.processors.modules.{entry}.core')
            hidden_modules.append(f'facefusion.processors.modules.{entry}.locales')

# Layouts
layouts_dir = os.path.join('facefusion', 'uis', 'layouts')
if os.path.exists(layouts_dir):
    for entry in os.listdir(layouts_dir):
        if entry.endswith('.py') and not entry.startswith('__'):
            name = entry[:-3]
            hidden_modules.append(f'facefusion.uis.layouts.{name}')

hidden_imports_list = [
    'uvicorn',
    'sqlalchemy',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.orm',
    'fastapi',
    'fastapi.staticfiles',
    'pydantic',
    'multipart',
    'onnxruntime',
    'cv2',
    'numpy',
    'scipy',
    'tqdm',
    'sqlite3',
] + hidden_modules

a = Analysis(
    ['run_api.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('facefusion/processors/modules', 'facefusion/processors/modules'),
        ('facefusion/uis/layouts', 'facefusion/uis/layouts'),
        ('frontend/out', 'frontend/out'),
    ],
    hiddenimports=hidden_imports_list,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='facefusion-app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
