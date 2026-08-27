@echo off
setlocal
cd /d "%~dp0\.."

echo [1/5] Preparing virtual environment...
if not exist "others\.venv\Scripts\python.exe" (
    py -m venv "others\.venv"
    if errorlevel 1 goto :err
)

echo [2/5] Installing dependencies and PyInstaller...
"others\.venv\Scripts\python.exe" -m pip install -r "others\requirements.txt" pyinstaller
if errorlevel 1 goto :err

echo [3/5] Building app (onedir mode)...
"others\.venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm --distpath . --workpath "others\build" "others\RPsoft.spec"
if errorlevel 1 goto :err

echo [3.5/5] Moving launcher to project root...
if exist "_internal" rmdir /s /q "_internal"
if exist "RPsoft\RPsoft.exe" move /Y "RPsoft\RPsoft.exe" "RPsoft.exe" >nul
if exist "RPsoft\_internal" move /Y "RPsoft\_internal" "_internal" >nul
if exist "RPsoft" rmdir /s /q "RPsoft"

echo [4/5] Building installer with Inno Setup...
if not exist "others\inno\ISCC.exe" (
    echo   Inno Setup not found at others\inno\ISCC.exe
    echo   Download it and run: is.exe /VERYSILENT /PORTABLE=1 /DIR=others\inno
    goto :err
)
"others\inno\ISCC.exe" "others\installer.iss"
if errorlevel 1 goto :err

echo.
echo [5/5] Done!
echo   Installer: dist\RPS-setup-0.0.0-win-amd64.exe
pause
exit /b 0

:err
echo.
echo Build failed. See the error messages above.
pause
exit /b 1
