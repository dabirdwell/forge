#!/bin/bash
# Start ACE-Step 1.5 API server for NeoVak
ACESTEP_DIR="${ACESTEP_DIR:-$HOME/ACE-Step-1.5}"

if [ ! -d "$ACESTEP_DIR" ]; then
    echo "ACE-Step not found at $ACESTEP_DIR. Installing..."
    cd "$HOME"
    git clone https://github.com/ACE-Step/ACE-Step-1.5.git
    cd ACE-Step-1.5
    chmod +x start_api_server_macos.sh
fi

cd "$ACESTEP_DIR"
exec ./start_api_server_macos.sh
