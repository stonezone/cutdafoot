#!/bin/bash
# Build and Sign script for FootTraceProcessor

# Configuration
APP_NAME="FootTraceProcessor"
BUNDLE_ID="com.foottrace.processor"
ENROLLMENT_ID="H48CA4927M"

# Prompt for required information
echo "Please enter your Apple Developer credentials:"
read -p "Apple ID Email: " APPLE_ID
read -sp "App-specific Password: " APP_PASSWORD
echo
read -p "Team ID (from developer.apple.com): " TEAM_ID

# Install required tools
pip3 install pyinstaller

# Create PyInstaller spec file
cat > ${APP_NAME}.spec << EOL
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
          name='${APP_NAME}',
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
               name='${APP_NAME}')
app = BUNDLE(coll,
            name='${APP_NAME}.app',
            icon=None,
            bundle_identifier='${BUNDLE_ID}',
            info_plist={
                'CFBundleShortVersionString': '1.0.0',
                'CFBundleVersion': '1',
                'NSHighResolutionCapable': True,
                'LSMinimumSystemVersion': '10.12.0'
            })
EOL

# Build the application
echo "Building application..."
pyinstaller --clean ${APP_NAME}.spec

# Create entitlements file
cat > entitlements.plist << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
</dict>
</plist>
EOL

# Sign the application
echo "Signing application..."
cd dist
codesign --force --options runtime --sign "Developer ID Application: ${TEAM_ID}" \
         --entitlements ../entitlements.plist \
         --deep "${APP_NAME}.app"

# Verify signature
echo "Verifying signature..."
codesign --verify --deep --strict "${APP_NAME}.app"
spctl --assess --type execute "${APP_NAME}.app"

# Create DMG for distribution
echo "Creating DMG..."
hdiutil create -volname "${APP_NAME}" -srcfolder "${APP_NAME}.app" -ov -format UDZO "${APP_NAME}.dmg"

# Sign DMG
codesign --sign "Developer ID Application: ${TEAM_ID}" "${APP_NAME}.dmg"

# Notarize the DMG
echo "Submitting for notarization..."
xcrun notarytool submit "${APP_NAME}.dmg" \
      --apple-id "${APPLE_ID}" \
      --password "${APP_PASSWORD}" \
      --team-id "${TEAM_ID}" \
      --wait

# Staple the notarization ticket
xcrun stapler staple "${APP_NAME}.dmg"

echo "Build complete! Your signed and notarized application is in dist/${APP_NAME}.dmg"

# Cleanup
cd ..
rm -rf build __pycache__ *.spec entitlements.plist