@echo off
echo ========================================
echo MCBE Seed Cracker - Clean Script
echo ========================================
echo.

echo Cleaning build artifacts...
if exist "build" (
    echo Removing build directory...
    rmdir /s /q "build"
)
if exist "dist" (
    echo Removing dist directory...
    rmdir /s /q "dist"
)
if exist "*.spec" (
    echo Removing spec files...
    del /q "*.spec"
)

echo.
echo Cleaning Python cache...
if exist "__pycache__" rmdir /s /q "__pycache__"
for /r %%i in (__pycache__) do @if exist "%%i" rmdir /s /q "%%i"

echo.
echo Cleaning progress files...
if exist "progress_low32.json" del /q "progress_low32.json"
if exist "progress_high32.json" del /q "progress_high32.json"
if exist "config.json" del /q "config.json"

echo.
echo ========================================
echo Clean completed!
echo ========================================
echo.

pause
