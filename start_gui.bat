@echo off
REM Launch script for EPUB Repair GUI (Windows)

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Activate virtual environment if it exists
if exist "%SCRIPT_DIR%venv\Scripts\activate.bat" (
    call "%SCRIPT_DIR%venv\Scripts\activate.bat"
)

REM Launch the GUI
epub-repair-gui

REM If the command above fails, try running as a module
if errorlevel 1 (
    echo Trying alternative launch method...
    python -m epub_repair.gui
)

pause
