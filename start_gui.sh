#!/bin/bash
# Launch script for EPUB Repair GUI

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Try to use the user's venv first (if it exists)
if [ -d "$HOME/venv" ]; then
    source "$HOME/venv/bin/activate"
# Otherwise try local venv
elif [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Launch the GUI
if command -v epub-repair-gui &> /dev/null; then
    epub-repair-gui
else
    # If the command above fails, try running as a module
    echo "Using Python module..."
    python3 -m epub_repair.gui
fi
