#!/bin/bash

# Build script for FootTraceProcessor
pip3 install pyinstaller

cat > FootTraceProcessor.spec << 'EOL'
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(['foot_trace_gui.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=['PIL', 'PIL._imagingtk', 'PIL._tkinter_finder', 'tkinter'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='FootTraceProcessor',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='FootTraceProcessor')

app = BUNDLE(coll,
            name='FootTraceProcessor.app',
            icon=None,
            bundle_identifier='com.foottrace.processor')
EOL

pyinstaller --clean FootTraceProcessor.spec
rm -rf build __pycache__