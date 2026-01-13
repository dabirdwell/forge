#!/bin/bash
# Forge Launcher - Starts ComfyUI (if needed) and launches Forge
# Usage: ./start.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

FORGE_DIR="$(cd "$(dirname "$0")" && pwd)"
COMFYUI_URL="${COMFYUI_URL:-http://127.0.0.1:8188}"
FORGE_PORT="${FORGE_PORT:-7861}"

echo -e "${BLUE}🔥 Forge Launcher${NC}"
echo ""

# Function to check if ComfyUI is running
check_comfyui() {
    curl -s --connect-timeout 2 "$COMFYUI_URL" > /dev/null 2>&1
}

# Function to find ComfyUI installation
find_comfyui() {
    # Check config file first
    if [ -f "$FORGE_DIR/forge_config.json" ]; then
        # Extract first model path and go up to find ComfyUI
        CONFIG_PATH=$(python3 -c "import json; c=json.load(open('$FORGE_DIR/forge_config.json')); print(c.get('model_paths',[''])[0].replace('~','$HOME'))" 2>/dev/null || echo "")
        if [ -n "$CONFIG_PATH" ] && [ -d "${CONFIG_PATH%/models}" ]; then
            COMFYUI_PATH="${CONFIG_PATH%/models}"
            if [ -f "$COMFYUI_PATH/main.py" ]; then
                echo "$COMFYUI_PATH"
                return 0
            fi
        fi
    fi

    # Common locations to check
    COMMON_PATHS=(
        "$HOME/ComfyUI"
        "$HOME/comfyui"
        "$HOME/AI/ComfyUI"
        "$HOME/Projects/ComfyUI"
        "$HOME/Documents/ComfyUI"
        "/opt/ComfyUI"
        "/Applications/ComfyUI"
    )

    for path in "${COMMON_PATHS[@]}"; do
        if [ -f "$path/main.py" ]; then
            echo "$path"
            return 0
        fi
    done

    # Try to find it anywhere
    FOUND=$(find "$HOME" -maxdepth 4 -name "main.py" -path "*ComfyUI*" 2>/dev/null | head -1)
    if [ -n "$FOUND" ]; then
        echo "$(dirname "$FOUND")"
        return 0
    fi

    return 1
}

# Check if ComfyUI is already running
if check_comfyui; then
    echo -e "${GREEN}✓ ComfyUI is running${NC} at $COMFYUI_URL"
else
    echo -e "${YELLOW}ComfyUI not detected at $COMFYUI_URL${NC}"

    # Try to find and start ComfyUI
    COMFYUI_PATH=$(find_comfyui || echo "")

    if [ -n "$COMFYUI_PATH" ]; then
        echo -e "Found ComfyUI at: ${BLUE}$COMFYUI_PATH${NC}"
        echo -e "Starting ComfyUI in background..."

        # Start ComfyUI in background
        cd "$COMFYUI_PATH"

        # Activate venv if it exists
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
        fi

        # Start with common Mac-friendly flags
        python3 main.py --listen 127.0.0.1 --port 8188 > /tmp/comfyui.log 2>&1 &
        COMFYUI_PID=$!

        echo -e "Waiting for ComfyUI to start (PID: $COMFYUI_PID)..."

        # Wait up to 30 seconds for ComfyUI to start
        for i in {1..30}; do
            if check_comfyui; then
                echo -e "${GREEN}✓ ComfyUI started successfully${NC}"
                break
            fi
            sleep 1
            echo -n "."
        done
        echo ""

        if ! check_comfyui; then
            echo -e "${RED}✗ ComfyUI failed to start${NC}"
            echo "Check /tmp/comfyui.log for errors"
            echo ""
            echo "You can start ComfyUI manually:"
            echo "  cd $COMFYUI_PATH && python main.py"
            exit 1
        fi

        cd "$FORGE_DIR"
    else
        echo -e "${RED}✗ Could not find ComfyUI installation${NC}"
        echo ""
        echo "Please either:"
        echo "  1. Start ComfyUI manually before running Forge"
        echo "  2. Set COMFYUI_PATH environment variable"
        echo "  3. Install ComfyUI in ~/ComfyUI"
        echo ""
        echo "Install ComfyUI: https://github.com/comfyanonymous/ComfyUI"
        exit 1
    fi
fi

# Activate Forge venv if it exists
cd "$FORGE_DIR"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Activated Forge virtual environment${NC}"
fi

# Check dependencies
if ! python3 -c "import nicegui" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt -q
fi

echo ""
echo -e "${GREEN}🔥 Starting Forge...${NC}"
echo -e "   Open ${BLUE}http://localhost:$FORGE_PORT${NC} in your browser"
echo ""

# Start Forge
python3 forge_nicegui.py
