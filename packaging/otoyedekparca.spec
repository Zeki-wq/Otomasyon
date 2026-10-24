# -*- mode: python ; coding: utf-8 -*-
# Oto Yedek Parça Otomasyonu - PyInstaller Spec Dosyası

import sys
from pathlib import Path

block_cipher = None
kok_dizin = Path.cwd()

a = Analysis(
    [str(kok_dizin / 'app' / 'main.py')],
    pathex=[str(kok_dizin)],
    binaries=[],
    datas=[
        (str(kok_dizin / 'app' / 'db' / 'migrations' / '0001_initial.sql'), 'app/db/migrations'),
        (str(kok_dizin / 'legacy' / 'urunler12.db'), 'legacy'),
    ],
    hiddenimports=[
        'openpyxl',
        'reportlab',
        'reportlab.platypus',
        'reportlab.lib',
        'reportlab.lib.colors',
        'sqlite3',
        'hashlib',
        'decimal'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pandas', 'tkinter', 'matplotlib'],
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
    name='OtoYedekParca',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OtoYedekParca',
)
