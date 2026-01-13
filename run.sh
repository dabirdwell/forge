#!/bin/bash
# Forge - One-click launcher
# Just run: ./run.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Find Python - try python3 first, then python
PYTHON=""
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    # Make sure it's Python 3
    if python --version 2>&1 | grep -q "Python 3"; then
        PYTHON="python"
    fi
fi

if [ -z "$PYTHON" ]; then
    echo ""
    echo "❌ Python 3 is required but not found."
    echo ""
    echo "Install Python from: https://www.python.org/downloads/"
    echo "Or via Homebrew:     brew install python3"
    echo ""
    exit 1
fi

echo ""
echo "🔥 Starting Forge..."
echo ""

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "First run - setting up environment..."
    $PYTHON -m venv venv
    source venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt
    echo ""
    echo "Setup complete!"
    echo ""
else
    source venv/bin/activate
fi

# Run Forge
$PYTHON forge_nicegui.py
