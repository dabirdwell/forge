#!/bin/bash
# Build NeoVak.app - Native macOS Application
# Creates a double-click app like LM Studio - no terminal needed
#
# Usage: ./packaging/build_app.sh
#
# The resulting NeoVak.app:
# - Opens a native window (not a browser)
# - Auto-detects and starts ComfyUI
# - First-run setup wizard
# - No command line required

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APP_NAME="NeoVak"
APP_DIR="$PROJECT_DIR/dist/$APP_NAME.app"
VERSION="${VERSION:-1.1.0}"

echo ""
echo "💡 NeoVak App Builder v$VERSION"
echo "   Creating native macOS application..."
echo ""

cd "$PROJECT_DIR"

# Find Python - try python3 first, then python
PYTHON=""
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    if python --version 2>&1 | grep -q "Python 3"; then
        PYTHON="python"
    fi
fi

if [ -z "$PYTHON" ]; then
    echo "❌ Python 3 is required but not installed."
    echo "   Install from: https://www.python.org/downloads/"
    exit 1
fi

# Create/activate virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating build environment..."
    $PYTHON -m venv venv
fi

source venv/bin/activate

# Install build dependencies
echo "Installing build dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install pillow > /dev/null 2>&1

# Create icon if it doesn't exist
if [ ! -f "$SCRIPT_DIR/AppIcon.icns" ]; then
    echo "Creating app icon..."
    python3 "$SCRIPT_DIR/create_icon.py" 2>/dev/null || echo "  (Icon creation skipped)"
fi

# Clean previous build
echo "Cleaning previous build..."
rm -rf "$PROJECT_DIR/dist/$APP_NAME.app"
mkdir -p "$PROJECT_DIR/dist"

# Create app bundle structure
echo "Creating app bundle..."
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"
mkdir -p "$APP_DIR/Contents/Resources/neovak"

# Copy application files
echo "Copying application files..."
cp "$PROJECT_DIR/neovak_launcher.py" "$APP_DIR/Contents/Resources/neovak/"
cp "$PROJECT_DIR/neovak_ui.py" "$APP_DIR/Contents/Resources/neovak/"
cp "$PROJECT_DIR/neovak_backend.py" "$APP_DIR/Contents/Resources/neovak/"
cp "$PROJECT_DIR/neovak_progress.py" "$APP_DIR/Contents/Resources/neovak/" 2>/dev/null || true
cp "$PROJECT_DIR/requirements.txt" "$APP_DIR/Contents/Resources/neovak/"
cp "$PROJECT_DIR/neovak_config.example.json" "$APP_DIR/Contents/Resources/neovak/"
cp -r "$PROJECT_DIR/workflows" "$APP_DIR/Contents/Resources/neovak/" 2>/dev/null || true
cp -r "$PROJECT_DIR/voices" "$APP_DIR/Contents/Resources/neovak/" 2>/dev/null || mkdir -p "$APP_DIR/Contents/Resources/neovak/voices"
cp -r "$PROJECT_DIR/docs" "$APP_DIR/Contents/Resources/neovak/" 2>/dev/null || true

# Create the main launcher script
# This opens a NATIVE WINDOW (not a browser) - like LM Studio
cat > "$APP_DIR/Contents/MacOS/NeoVak" << 'LAUNCHER'
#!/bin/bash
# NeoVak Native Launcher
# Opens app in a native window - no browser, no terminal

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
RESOURCES="$APP_DIR/Resources"
NEOVAK_DIR="$RESOURCES/neovak"
VENV_DIR="$RESOURCES/venv"
CONFIG_DIR="$HOME/.config/neovak"
LOG_FILE="$CONFIG_DIR/neovak.log"

# Ensure config directory exists
mkdir -p "$CONFIG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

show_error() {
    osascript -e "display dialog \"$1\" buttons {\"OK\"} default button \"OK\" with title \"NeoVak Error\" with icon stop"
}

show_progress() {
    osascript -e "display notification \"$1\" with title \"NeoVak\""
}

log "Starting NeoVak..."

# Check for Python
if ! command -v python3 &> /dev/null; then
    show_error "Python 3 is required but not installed.\n\nPlease install Python from python.org or via Homebrew:\n\nbrew install python3"
    exit 1
fi

# Create virtual environment if needed (first run)
if [ ! -d "$VENV_DIR" ]; then
    log "First run - creating environment..."
    show_progress "Setting up NeoVak for first use... (this takes a minute)"

    python3 -m venv "$VENV_DIR" 2>> "$LOG_FILE"
    source "$VENV_DIR/bin/activate"

    log "Installing dependencies..."
    pip install --upgrade pip >> "$LOG_FILE" 2>&1
    pip install -r "$NEOVAK_DIR/requirements.txt" >> "$LOG_FILE" 2>&1

    if [ $? -ne 0 ]; then
        show_error "Failed to install dependencies.\n\nCheck log at:\n$LOG_FILE"
        exit 1
    fi
    log "Setup complete"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Copy default config if needed
if [ ! -f "$CONFIG_DIR/neovak_config.json" ]; then
    cp "$NEOVAK_DIR/neovak_config.example.json" "$CONFIG_DIR/neovak_config.json"
fi

# Run NeoVak with native window
cd "$NEOVAK_DIR"
export NEOVAK_CONFIG="$CONFIG_DIR/neovak_config.json"

log "Launching NeoVak..."
exec python3 neovak_launcher.py >> "$LOG_FILE" 2>&1
LAUNCHER

chmod +x "$APP_DIR/Contents/MacOS/NeoVak"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>NeoVak</string>
    <key>CFBundleDisplayName</key>
    <string>NeoVak</string>
    <key>CFBundleIdentifier</key>
    <string>com.dabirdwell.neovak</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleExecutable</key>
    <string>NeoVak</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSMinimumSystemVersion</key>
    <string>11.0</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.graphics-design</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSHumanReadableCopyright</key>
    <string>Copyright © 2026 David Birdwell. MIT License.</string>
</dict>
</plist>
PLIST

# Create a simple icon (will be replaced with proper icon if available)
if [ -f "$PROJECT_DIR/packaging/AppIcon.icns" ]; then
    cp "$PROJECT_DIR/packaging/AppIcon.icns" "$APP_DIR/Contents/Resources/"
else
    echo "Note: No AppIcon.icns found. Using default icon."
    # Create a placeholder icon using built-in macOS tools
    # This creates a simple colored square icon
fi

echo ""
echo "✅ Build complete!"
echo ""
echo "   App location: $APP_DIR"
echo ""
echo "To install:"
echo "   1. Drag NeoVak.app to /Applications"
echo "   2. Double-click to run"
echo ""
echo "To create a DMG installer:"
echo "   ./packaging/create_dmg.sh"
