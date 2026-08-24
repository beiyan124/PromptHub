@echo off
rem ============================================
rem  Prompt Manager - build standalone exe
rem  Output: dist\提示词管理器.exe (with icon from logo\)
rem ============================================
cd /d "%~dp0"

if not exist ".venv\Scripts\pyinstaller.exe" (
    echo [ERROR] pyinstaller not found. Run: .venv\Scripts\python -m pip install pyinstaller pillow
    pause
    exit /b 1
)

echo Merging icons (logo\*.ico -> logo\app.ico) ...
.venv\Scripts\python.exe merge_icons.py
if errorlevel 1 (
    echo [ERROR] icon merge failed
    pause
    exit /b 1
)

echo Building exe (onefile, windowed) ...
.venv\Scripts\pyinstaller --noconfirm --clean prompt_manager.spec
if errorlevel 1 (
    echo [ERROR] build failed
    pause
    exit /b 1
)

echo.
echo Done. exe at: dist\提示词管理器.exe
pause
