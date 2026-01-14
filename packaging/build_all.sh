#!/bin/bash
# Build NeoVak for all platforms
# Run on macOS to build macOS version, or on Linux for Linux version

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION="${VERSION:-1.1.0}"

echo ""
echo "💡 NeoVak Build System v$VERSION"
echo ""

# Detect platform
case "$(uname -s)" in
    Darwin)
        PLATFORM="macOS"
        ;;
    Linux)
        PLATFORM="Linux"
        ;;
    MINGW*|CYGWIN*|MSYS*)
        PLATFORM="Windows"
        ;;
    *)
        echo "Unknown platform: $(uname -s)"
        exit 1
        ;;
esac

echo "Detected platform: $PLATFORM"
echo ""

build_macos() {
    echo "Building macOS app bundle..."
    "$SCRIPT_DIR/build_app.sh"

    echo ""
    read -p "Create DMG installer? [y/N] " CREATE_DMG
    if [[ "$CREATE_DMG" =~ ^[Yy]$ ]]; then
        "$SCRIPT_DIR/create_dmg.sh"
    fi
}

build_linux() {
    echo "Building Linux package..."
    "$SCRIPT_DIR/build_linux.sh"
}

build_windows() {
    echo "Building Windows package..."
    if command -v cmd.exe &> /dev/null; then
        cmd.exe /c "$SCRIPT_DIR\\build_windows.bat"
    else
        echo "Windows build requires Windows or WSL with cmd.exe access"
        exit 1
    fi
}

# Build menu
echo "What would you like to build?"
echo ""
echo "  1) Build for current platform ($PLATFORM)"
echo "  2) Build for macOS only"
echo "  3) Build for Linux only"
echo "  4) Build for Windows only"
echo "  5) Build all (requires running on each platform)"
echo ""
read -p "Choice [1]: " CHOICE
CHOICE="${CHOICE:-1}"

case "$CHOICE" in
    1)
        case "$PLATFORM" in
            macOS) build_macos ;;
            Linux) build_linux ;;
            Windows) build_windows ;;
        esac
        ;;
    2)
        if [ "$PLATFORM" = "macOS" ]; then
            build_macos
        else
            echo "macOS build must be run on macOS"
            exit 1
        fi
        ;;
    3)
        if [ "$PLATFORM" = "Linux" ]; then
            build_linux
        else
            echo "Running Linux build (may work via Docker/VM)..."
            build_linux
        fi
        ;;
    4)
        build_windows
        ;;
    5)
        echo "Building all platforms..."
        [ "$PLATFORM" = "macOS" ] && build_macos
        build_linux 2>/dev/null || echo "Linux build skipped (run on Linux)"
        build_windows 2>/dev/null || echo "Windows build skipped (run on Windows)"
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Build complete!"
echo ""
echo "Outputs in: $PROJECT_DIR/dist/"
ls -la "$PROJECT_DIR/dist/" 2>/dev/null || true
