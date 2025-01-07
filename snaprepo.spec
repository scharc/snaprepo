# -*- mode: python ; coding: utf-8 -*-

import os
import site
import sys
from PyInstaller.utils.hooks import collect_submodules, get_package_paths

block_cipher = None

packages_to_import = [
    'click',
    'chardet',
    'tiktoken',
    'rich',
    'tiktoken_ext',
    'tiktoken_ext.openai_public',
    'rich.console',
    'rich.panel',
    'rich.syntax',
    'pkg_resources',
    'regex',
    'snaprepo'
]

# Get all submodules for these packages
hidden_imports = []
for package in packages_to_import:
    try:
        hidden_imports.extend(collect_submodules(package))
    except Exception:
        hidden_imports.append(package)

# Include snaprepo package
datas = [
    ('completions', 'completions'),
    ('snaprepo', 'snaprepo'),  # Include entire snaprepo package
]

# Include external dependencies
for package in ['click', 'chardet', 'tiktoken', 'rich']:
    try:
        pkg_dir = site.getsitepackages()[0]
        pkg_path = os.path.join(pkg_dir, package)
        if os.path.exists(pkg_path):
            datas.append((pkg_path, package))
    except Exception as e:
        print(f"Warning: could not find path for {package}: {e}")

a = Analysis(
    ['snaprepo/main.py'],
    pathex=[os.path.abspath(SPECPATH)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
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
    name='snaprepo',
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