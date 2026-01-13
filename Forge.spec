# -*- mode: python ; coding: utf-8 -*-
"""
Forge.spec - PyInstaller specification for macOS .app bundle

This creates a self-contained Forge.app that:
- Opens a native window (not a browser)
- Auto-detects and starts ComfyUI
- Bundles all dependencies

Build with:
    pyinstaller Forge.spec

Output:
    dist/Forge.app
"""

import sys
from pathlib import Path

block_cipher = None

# Get the project directory
project_dir = Path(SPECPATH)

# Data files to include
datas = [
    # Core application files
    (str(project_dir / 'forge_nicegui.py'), '.'),
    (str(project_dir / 'forge_backend.py'), '.'),
    (str(project_dir / 'forge_progress.py'), '.'),
    (str(project_dir / 'forge_config.example.json'), '.'),

    # Workflows (ComfyUI templates)
    (str(project_dir / 'workflows'), 'workflows'),

    # Voice presets
    (str(project_dir / 'voices'), 'voices'),

    # Documentation
    (str(project_dir / 'docs'), 'docs'),
]

# Filter out non-existent paths
datas = [(src, dst) for src, dst in datas if Path(src).exists()]

# Hidden imports for NiceGUI and its dependencies
hiddenimports = [
    # NiceGUI
    'nicegui',
    'nicegui.elements',
    'nicegui.ui',

    # Asyncio
    'asyncio',
    'uvicorn',
    'starlette',
    'fastapi',

    # Web
    'websocket',
    'websockets',
    'httpx',

    # pywebview
    'webview',

    # Our modules
    'forge_backend',
    'forge_progress',
]

a = Analysis(
    [str(project_dir / 'forge_launcher.py')],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude large packages we don't need bundled
        'torch',
        'torchaudio',
        'tensorflow',
        'matplotlib',
        'PIL',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Forge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=True,  # macOS argv emulation
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Forge',
)

app = BUNDLE(
    coll,
    name='Forge.app',
    icon=str(project_dir / 'packaging' / 'AppIcon.icns') if (project_dir / 'packaging' / 'AppIcon.icns').exists() else None,
    bundle_identifier='com.dabirdwell.forge',
    info_plist={
        'CFBundleName': 'Forge',
        'CFBundleDisplayName': 'Forge',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSMinimumSystemVersion': '11.0',
        'LSApplicationCategoryType': 'public.app-category.graphics-design',
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'Copyright © 2026 David Birdwell. MIT License.',
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
    },
)
