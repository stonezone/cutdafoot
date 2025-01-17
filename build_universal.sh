#!/bin/bash
# Universal Binary Build script for FootTraceProcessor (unsigned test version)

# Configuration
APP_NAME="FootTraceProcessor"
BUNDLE_ID="com.foottrace.processor"

# Install required tools
pip3 install pyinstaller

# Create PyInstaller spec file for Universal Binary
cat > ${APP_NAME}.spec << EOL
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['foot_trace_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PIL', 'PIL._imagingtk', 'PIL._tkinter_finder', 'tkinter'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='${APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='${APP_NAME}'
)

app = BUNDLE(
    coll,
    name='${APP_NAME}.app',
    icon=None,
    bundle_identifier='${BUNDLE_ID}'
)
EOL

# Build universal binary
echo "Building Universal Binary application..."
ARCHFLAGS="-arch arm64 -arch x86_64" pyinstaller --clean ${APP_NAME}.spec

echo "Build complete! Your application is in dist/${APP_NAME}.app"

# Cleanup
rm -rf build __pycache__ *.spec