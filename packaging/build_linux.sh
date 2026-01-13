#!/bin/bash
# Build Forge for Linux
# Creates a portable tarball and optional AppImage

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APP_NAME="Forge"
VERSION="${VERSION:-1.0.0}"
DIST_DIR="$PROJECT_DIR/dist/$APP_NAME-Linux"

echo ""
echo "🔥 Building Forge for Linux v$VERSION"
echo ""

# Clean previous build
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR/forge"

# Copy application files
echo "Copying application files..."
cp "$PROJECT_DIR/forge_nicegui.py" "$DIST_DIR/forge/"
cp "$PROJECT_DIR/forge_backend.py" "$DIST_DIR/forge/"
cp "$PROJECT_DIR/forge_progress.py" "$DIST_DIR/forge/" 2>/dev/null || true
cp "$PROJECT_DIR/requirements.txt" "$DIST_DIR/forge/"
cp "$PROJECT_DIR/forge_config.example.json" "$DIST_DIR/forge/"
cp -r "$PROJECT_DIR/workflows" "$DIST_DIR/forge/" 2>/dev/null || true
cp -r "$PROJECT_DIR/voices" "$DIST_DIR/forge/" 2>/dev/null || mkdir -p "$DIST_DIR/forge/voices"
cp -r "$PROJECT_DIR/docs" "$DIST_DIR/forge/" 2>/dev/null || true

# Create launcher script
cat > "$DIST_DIR/forge.sh" << 'LAUNCHER'
#!/bin/bash
# Forge Launcher for Linux

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FORGE_DIR="$SCRIPT_DIR/forge"
VENV_DIR="$SCRIPT_DIR/venv"
CONFIG_DIR="$HOME/.config/forge"
LOG_FILE="$CONFIG_DIR/forge.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Ensure config directory
mkdir -p "$CONFIG_DIR"

echo -e "${BLUE}🔥 Forge${NC}"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed.${NC}"
    echo "Install with: sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

# Create virtual environment if needed
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Setting up Forge for first use...${NC}"
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip >> "$LOG_FILE" 2>&1
    pip install -r "$FORGE_DIR/requirements.txt" >> "$LOG_FILE" 2>&1
    echo -e "${GREEN}✓ Setup complete${NC}"
fi

source "$VENV_DIR/bin/activate"

# Copy config if needed
if [ ! -f "$CONFIG_DIR/forge_config.json" ]; then
    cp "$FORGE_DIR/forge_config.example.json" "$CONFIG_DIR/forge_config.json"
fi

# Check ComfyUI
check_comfyui() {
    curl -s --connect-timeout 2 "http://127.0.0.1:8188" > /dev/null 2>&1
}

find_comfyui() {
    # Check config
    if [ -f "$CONFIG_DIR/forge_config.json" ]; then
        COMFYUI_PATH=$(python3 -c "import json; c=json.load(open('$CONFIG_DIR/forge_config.json')); print(c.get('comfyui_path','').replace('~','$HOME'))" 2>/dev/null || echo "")
        if [ -n "$COMFYUI_PATH" ] && [ -f "$COMFYUI_PATH/main.py" ]; then
            echo "$COMFYUI_PATH"
            return 0
        fi
    fi

    # Common locations
    for path in "$HOME/ComfyUI" "$HOME/comfyui" "$HOME/AI/ComfyUI" "/opt/ComfyUI"; do
        if [ -f "$path/main.py" ]; then
            echo "$path"
            return 0
        fi
    done
    return 1
}

if ! check_comfyui; then
    COMFYUI_PATH=$(find_comfyui || echo "")

    if [ -z "$COMFYUI_PATH" ]; then
        echo -e "${YELLOW}ComfyUI not found.${NC}"
        echo ""
        echo "ComfyUI is required for AI generation."
        echo "Install from: https://github.com/comfyanonymous/ComfyUI"
        echo ""
        read -p "Enter ComfyUI path (or press Enter to exit): " COMFYUI_PATH
        if [ -z "$COMFYUI_PATH" ] || [ ! -f "$COMFYUI_PATH/main.py" ]; then
            exit 1
        fi
        # Save to config
        python3 -c "
import json
config_path = '$CONFIG_DIR/forge_config.json'
with open(config_path, 'r') as f:
    config = json.load(f)
config['comfyui_path'] = '$COMFYUI_PATH'
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
"
    fi

    echo -e "Starting ComfyUI from ${BLUE}$COMFYUI_PATH${NC}..."
    cd "$COMFYUI_PATH"
    [ -f "venv/bin/activate" ] && source venv/bin/activate
    python3 main.py --listen 127.0.0.1 --port 8188 >> "$LOG_FILE" 2>&1 &

    # Wait for ComfyUI
    for i in {1..60}; do
        check_comfyui && break
        sleep 1
    done

    if ! check_comfyui; then
        echo -e "${RED}ComfyUI failed to start. Check $LOG_FILE${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ ComfyUI started${NC}"
fi

echo -e "${GREEN}✓ ComfyUI running${NC}"
echo ""
echo -e "Starting Forge at ${BLUE}http://localhost:7861${NC}"

# Try to open browser
(sleep 2 && xdg-open "http://localhost:7861" 2>/dev/null || sensible-browser "http://localhost:7861" 2>/dev/null || true) &

cd "$FORGE_DIR"
export FORGE_CONFIG="$CONFIG_DIR/forge_config.json"
python3 forge_nicegui.py
LAUNCHER

chmod +x "$DIST_DIR/forge.sh"

# Create desktop entry
cat > "$DIST_DIR/forge.desktop" << DESKTOP
[Desktop Entry]
Name=Forge
Comment=Local AI Creative Suite
Exec=FORGE_PATH/forge.sh
Icon=FORGE_PATH/forge/icon.png
Terminal=true
Type=Application
Categories=Graphics;AudioVideo;
DESKTOP

# Create README
cat > "$DIST_DIR/README.md" << 'README'
# Forge for Linux

## Quick Start

1. Make sure ComfyUI is installed
2. Run `./forge.sh`
3. Open http://localhost:7861 in your browser

## Requirements

- Linux (Ubuntu 20.04+, Debian 11+, Fedora 35+, Arch, etc.)
- Python 3.10+
- ComfyUI (https://github.com/comfyanonymous/ComfyUI)
- At least one AI model

## Installation

```bash
# Extract the tarball
tar -xzf Forge-Linux.tar.gz
cd Forge-Linux

# Run
./forge.sh
```

## Desktop Integration (Optional)

```bash
# Edit the .desktop file to set the correct path
sed -i "s|FORGE_PATH|$(pwd)|g" forge.desktop

# Copy to applications
cp forge.desktop ~/.local/share/applications/
```

## Configuration

Config file: `~/.config/forge/forge_config.json`
README

# Create tarball
echo "Creating tarball..."
cd "$PROJECT_DIR/dist"
tar -czf "$APP_NAME-Linux-$VERSION.tar.gz" "$APP_NAME-Linux"

echo ""
echo "✅ Build complete!"
echo ""
echo "   Folder: $DIST_DIR"
echo "   Tarball: $PROJECT_DIR/dist/$APP_NAME-Linux-$VERSION.tar.gz"
echo ""
echo "To distribute, share the .tar.gz file"
