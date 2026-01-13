#!/bin/bash
# Create a DMG installer for Forge
# Requires: build_app.sh to be run first

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APP_NAME="Forge"
VERSION="${VERSION:-1.0.0}"
DMG_NAME="$APP_NAME-$VERSION-macOS"
APP_PATH="$PROJECT_DIR/dist/$APP_NAME.app"

echo ""
echo "🔥 Creating Forge DMG installer"
echo ""

# Check if app exists
if [ ! -d "$APP_PATH" ]; then
    echo "App not found. Building first..."
    "$SCRIPT_DIR/build_app.sh"
fi

# Create temporary directory for DMG contents
DMG_TEMP="$PROJECT_DIR/dist/dmg_temp"
rm -rf "$DMG_TEMP"
mkdir -p "$DMG_TEMP"

# Copy app
cp -R "$APP_PATH" "$DMG_TEMP/"

# Create Applications symlink
ln -s /Applications "$DMG_TEMP/Applications"

# Create background and instructions (optional)
cat > "$DMG_TEMP/README.txt" << 'README'
Forge - Local AI Creative Suite

INSTALLATION:
Drag Forge.app to Applications folder

FIRST RUN:
1. Double-click Forge in Applications
2. If asked about unidentified developer:
   - Go to System Preferences > Privacy & Security
   - Click "Open Anyway"
3. Forge will set up and launch

REQUIREMENTS:
- macOS 11 (Big Sur) or later
- Python 3.10+ (will prompt to install if missing)
- ComfyUI (Forge will help you set it up)

MORE INFO:
https://github.com/dabirdwell/forge
README

# Create DMG
echo "Creating DMG..."
DMG_PATH="$PROJECT_DIR/dist/$DMG_NAME.dmg"
rm -f "$DMG_PATH"

# Use hdiutil to create DMG
hdiutil create -volname "$APP_NAME" \
    -srcfolder "$DMG_TEMP" \
    -ov -format UDZO \
    "$DMG_PATH"

# Clean up
rm -rf "$DMG_TEMP"

echo ""
echo "✅ DMG created!"
echo ""
echo "   Location: $DMG_PATH"
echo "   Size: $(du -h "$DMG_PATH" | cut -f1)"
echo ""
echo "To distribute:"
echo "   1. Upload to GitHub Releases"
echo "   2. Or share directly"
