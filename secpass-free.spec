# -*- mode: python ; coding: utf-8 -*-
from os.path import join, abspath

ROOT = abspath(".")
block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[ROOT],
    binaries=[],
    datas=[],
    hiddenimports=[
        "cryptography",
        "cryptography.hazmat",
        "cryptography.hazmat.primitives",
        "cryptography.hazmat.primitives.asymmetric",
        "cryptography.hazmat.primitives.ciphers",
        "cryptography.hazmat.primitives.kdf",
        "argon2",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tests",
        "pytest",
        "unittest",
        "setuptools",
        "pip",
    ],
    noarchive=False,
)

for pkg in ["crypto", "secure", "storage", "gui"]:
    a.datas += Tree(
        join(ROOT, pkg),
        prefix=pkg,
        excludes=["__pycache__", "*.pyc"],
    )

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="secpass-free",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="secpass.ico",
)
