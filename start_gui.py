#!/usr/bin/env python3
"""
Launch script for EPUB Repair GUI.
This script can be used on any platform and will activate the virtual environment if present.
"""

import sys
import os
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Try user's venv first
    user_venv = Path.home() / "venv"
    venv_path = None
    
    if user_venv.exists():
        venv_path = user_venv
    elif (script_dir / "venv").exists():
        venv_path = script_dir / "venv"
    
    if venv_path:
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
        
        if python_exe.exists():
            # Use venv Python
            os.execv(str(python_exe), [str(python_exe), "-m", "epub_repair.gui"] + sys.argv[1:])
    
    # Fall back to system Python
    try:
        from epub_repair.gui import main as gui_main
        gui_main()
    except ImportError as e:
        print(f"Error: Could not import epub_repair.gui")
        print(f"Make sure the package is installed: pip install -e .")
        print(f"Error details: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
