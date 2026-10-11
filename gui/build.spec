# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

conda_lib = Path(r"D:\main\anaconda\anaconda\envs\mc_seed\Library\bin")

a = Analysis(
    ['main.py'],
    pathex=['..'],
    binaries=[
        (str(conda_lib / 'ffi.dll'), '.'),
        (str(conda_lib / 'liblzma.dll'), '.'),
        (str(conda_lib / 'libbz2.dll'), '.'),
        (str(conda_lib / 'libexpat.dll'), '.'),
    ],
    datas=[
        ('ui/data/structures.json', 'ui/data'),
        ('ui/data/biomes.json', 'ui/data'),
        ('ui/resources/translations/*.ts', 'ui/resources/translations'),
        ('ui/utils/structure_icons/*.png', 'ui/utils/structure_icons'),
        ('../core/data/structures.json', 'core/data'),
        ('../core/data/biomes.json', 'core/data'),
        ('../core/native/crack_low32_win_x86_64.dll', 'core/native'),
        ('../core/native/crack_low32_opencl_win_x86_64.dll', 'core/native'),
        ('../core/native/crack_low32.cl', 'core/native'),
        ('../core/native/crack_high32_win_x86_64.dll', 'core/native'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
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
    name='MCBE Seed Cracker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MCBE Seed Cracker',
)
