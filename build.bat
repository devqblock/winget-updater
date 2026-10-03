@echo off
:: Removes artifacts from previous builds for a clean start.
if exist dist rmdir /S /Q dist
if exist build rmdir /S /Q build
if exist WingetUpdater.spec del /Q WingetUpdater.spec
if exist checksums.txt del /Q checksums.txt

:: Checks if PyInstaller is installed
python -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

echo Compiling WingetUpdater (this may take a couple of minutes)...
:: We add --clean to avoid cache issues.
pyinstaller --clean --noconfirm --onefile --windowed --name WingetUpdater --icon icono.ico --add-data "icono.ico;." --manifest admin.manifest WingetUpdater.py

echo.
echo Verifying if the executable was created...
if exist dist\WingetUpdater.exe (
    echo [OK] Executable found. Moving to root...
    copy /Y dist\WingetUpdater.exe .
    
    echo Generating SHA256 hash with Python...
    python -c "import hashlib; h = hashlib.sha256(open('WingetUpdater.exe','rb').read()).hexdigest(); open('checksums.txt','w').write(f'{h}  WingetUpdater.exe\n')"

    echo Deleting temporary folders...
    rmdir /S /Q build
    rmdir /S /Q dist
    del /Q WingetUpdater.spec
    echo =======================================================
    echo PROCESS COMPLETED SUCCESSFULLY.
    echo =======================================================
) else (
    echo =======================================================
    echo [ERROR] PyInstaller FAILED to create the .exe file
    echo Check the lines above in this console to see the actual error.
    echo =======================================================
)
pause
