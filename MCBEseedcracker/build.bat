@echo off
REM MCBEseedcracker Windows Build Script
REM Requires MinGW-w64 GCC

echo ==============================================
echo MCBEseedcracker Windows Build Script
echo ==============================================
echo.

cd /d "%~dp0"

echo [1/2] Building crack_low32.dll...
cd crack_low32
gcc -O3 -shared -o crack_low32.dll crack_low32.c
if exist crack_low32.dll (
    echo     [OK] crack_low32.dll created
) else (
    echo     [ERROR] Failed to build crack_low32.dll
    exit /b 1
)
cd ..

echo.
echo [2/2] Building crack_high32.dll...
cd crack_high32
gcc -O3 -shared -o crack_high32.dll crack_high32.c ^
    cubiomes/biomes.c ^
    cubiomes/biomenoise.c ^
    cubiomes/generator.c ^
    cubiomes/layers.c ^
    cubiomes/noise.c ^
    cubiomes/quadbase.c ^
    cubiomes/util.c ^
    cubiomes/finders.c ^
    -lm
if exist crack_high32.dll (
    echo     [OK] crack_high32.dll created
) else (
    echo     [ERROR] Failed to build crack_high32.dll
    exit /b 1
)
cd ..

echo.
echo ==============================================
echo Build Complete!
echo ==============================================
echo.
echo Generated files:
echo   - crack_low32\crack_low32.dll
echo   - crack_high32\crack_high32.dll
echo.
pause
