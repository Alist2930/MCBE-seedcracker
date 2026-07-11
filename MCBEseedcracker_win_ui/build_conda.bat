@echo off
echo ========================================
echo MCBE Seed Cracker - Build Script (Conda)
echo ========================================
echo.

echo Activating conda environment...
call D:\main\anaconda\anaconda\Scripts\activate.bat mc_seed
if errorlevel 1 (
    echo Error: Failed to activate conda environment!
    pause
    exit /b 1
)

echo.
echo Checking Python environment...
python --version
if errorlevel 1 (
    echo Error: Python not found!
    pause
    exit /b 1
)

echo.
echo Installing dependencies...
pip install PyQt5 pyinstaller
if errorlevel 1 (
    echo Error: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo Cleaning previous build...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo Building executable...
pyinstaller build.spec --noconfirm
if errorlevel 1 (
    echo Error: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo Executable location: dist\MCBE Seed Cracker\
echo ========================================
echo.

pause