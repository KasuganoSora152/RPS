@echo off
setlocal
cd /d "%~dp0\.."

echo [0/3] Preparing virtual environment...
if not exist "others\.venv\Scripts\python.exe" (
    py -m venv "others\.venv"
    if errorlevel 1 goto :err
)

echo [1/3] Installing dependencies and PyInstaller...
"others\.venv\Scripts\python.exe" -m pip install -r "others\requirements.txt" pyinstaller
if errorlevel 1 goto :err

echo [2/3] Building (onedir mode)...
"others\.venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm --distpath . --workpath "others\build" "others\RPsoft.spec"
if errorlevel 1 goto :err

echo [2.5/3] Moving launcher to project root...
if exist "_internal" rmdir /s /q "_internal"
move /Y "RPsoft\RPsoft.exe" "RPsoft.exe" >nul
move /Y "RPsoft\_internal" "_internal" >nul
rmdir /s /q "RPsoft"

echo.
echo [3/3] Done! Launcher: RPsoft.exe
echo Double-click RPsoft.exe to run. Your data lives in the "data" folder.
pause
exit /b 0

:err
echo.
echo Build failed. See the error messages above.
pause
exit /b 1
