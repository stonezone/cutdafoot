#!/bin/bash
# Universal Binary Build and Sign script for FootTraceProcessor

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

# Create PyInstaller spec file for Universal Binary
cat > ${APP_NAME}.spec << EOL
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

def make_analysis(arch):
    return Analysis(['foot_trace_gui.py'],
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

# Create analyses for both architectures
a_arm64 = make_analysis('arm64')
a_x86_64 = make_analysis('x86_64')

# Create PYZ archives for both architectures
pyz_arm64 = PYZ(a_arm64.pure, a_arm64.zipped_data, cipher=block_cipher)
pyz_x86_64 = PYZ(a_x86_64.pure, a_x86_64.zipped_data, cipher=block_cipher)

# Create EXEs for both architectures
exe_arm64 = EXE(pyz_arm64,
          a_arm64.scripts,
          [],
          exclude_binaries=True,
          name='${APP_NAME}-arm64',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          target_arch='arm64')

exe_x86_64 = EXE(pyz_x86_64,
          a_x86_64.scripts,
          [],
          exclude_binaries=True,
          name='${APP_NAME}-x86_64',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          target_arch='x86_64')

# Create collections for both architectures
coll_arm64 = COLLECT(exe_arm64,
               a_arm64.binaries,
               a_arm64.zipfiles,
               a_arm64.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='${APP_NAME}-arm64')

coll_x86_64 = COLLECT(exe_x86_64,
               a_x86_64.binaries,
               a_x86_64.zipfiles,
               a_x86_64.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='${APP_NAME}-x86_64')

# Create universal app bundle
app = BUNDLE(coll_arm64,  # We'll merge x86_64 later
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

# Build for both architectures
echo "Building Universal Binary application..."
env ARCHFLAGS="-arch arm64" pyinstaller --clean ${APP_NAME}.spec --target-architecture arm64
env ARCHFLAGS="-arch x86_64" pyinstaller --clean ${APP_NAME}.spec --target-architecture x86_64

# Create universal binary
echo "Creating Universal Binary..."
cd dist
mkdir -p "${APP_NAME}.app/Contents/MacOS"
lipo "dist/${APP_NAME}-arm64/${APP_NAME}" "dist/${APP_NAME}-x86_64/${APP_NAME}" \
     -create -output "${APP_NAME}.app/Contents/MacOS/${APP_NAME}"

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

# Sign the universal binary application
echo "Signing Universal Binary application..."
codesign --force --options runtime --sign "Developer ID Application: ${TEAM_ID}" \
         --entitlements ../entitlements.plist \
         --deep "${APP_NAME}.app"

# Verify signature
echo "Verifying signature..."
codesign --verify --deep --strict "${APP_NAME}.app"
spctl --assess --type execute "${APP_NAME}.app"

# Create DMG for distribution
echo "Creating DMG..."
hdiutil create -volname "${APP_NAME}" -srcfolder "${APP_NAME}.app" -ov -format UDZO "${APP_NAME}-universal.dmg"

# Sign DMG
codesign --sign "Developer ID Application: ${TEAM_ID}" "${APP_NAME}-universal.dmg"

# Notarize the DMG
echo "Submitting for notarization..."
xcrun notarytool submit "${APP_NAME}-universal.dmg" \
      --apple-id "${APPLE_ID}" \
      --password "${APP_PASSWORD}" \
      --team-id "${TEAM_ID}" \
      --wait

# Staple the notarization ticket
xcrun stapler staple "${APP_NAME}-universal.dmg"

echo "Build complete! Your signed and notarized Universal Binary application is in dist/${APP_NAME}-universal.dmg"

# Cleanup
cd ..
rm -rf build __pycache__ *.spec entitlements.plist