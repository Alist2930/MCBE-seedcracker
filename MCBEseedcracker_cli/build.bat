@echo off
REM ============================================
REM MCBEseedcracker CLI Build Script (Windows)
REM
REM Requirements:
REM   - MinGW-w64 GCC on PATH (e.g. from mingw-w64.org or MSYS2)
REM   - OpenCL SDK for GPU build (NVIDIA CUDA Toolkit / AMD APP SDK /
REM     Intel OpenCL SDK); GPU build is skipped gracefully if absent
REM ============================================

cd /d "%~dp0"

echo ==============================================
echo MCBEseedcracker CLI Build Script (Windows)
echo ==============================================

where gcc >nul 2>&1
if errorlevel 1 (
    echo [ERROR] GCC not found. Install MinGW-w64 and add it to PATH.
    exit /b 1
)

echo.
echo [1/3] Building crack_low32.dll (CPU version)...
gcc -O3 -shared -o crack_low32\crack_low32.dll crack_low32\crack_low32.c
if errorlevel 1 (
    echo     [ERROR] Failed to build crack_low32.dll
    exit /b 1
)
echo     [OK] crack_low32.dll created

echo.
echo [2/3] Building crack_low32_opencl.dll (GPU version)...
REM Detect an OpenCL SDK (include + import lib)
set "OPENCL_INCLUDE="
set "OPENCL_LIB="

REM NVIDIA CUDA Toolkit (latest version wins)
if exist "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA" (
    for /d %%d in ("C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*") do (
        if exist "%%d\include\CL\cl.h" (
            set "OPENCL_INCLUDE=%%d\include"
            set "OPENCL_LIB=%%d\lib\x64"
        )
    )
)

REM AMD APP SDK
if "%OPENCL_INCLUDE%"=="" if exist "C:\Program Files (x86)\AMD APP SDK\include\CL\cl.h" (
    set "OPENCL_INCLUDE=C:\Program Files (x86)\AMD APP SDK\include"
    set "OPENCL_LIB=C:\Program Files (x86)\AMD APP SDK\lib\x86_64"
)

REM Intel OpenCL SDK
if "%OPENCL_INCLUDE%"=="" if exist "C:\Program Files (x86)\Intel\OpenCL SDK\include\CL\cl.h" (
    set "OPENCL_INCLUDE=C:\Program Files (x86)\Intel\OpenCL SDK\include"
    set "OPENCL_LIB=C:\Program Files (x86)\Intel\OpenCL SDK\lib\x64"
)

if "%OPENCL_INCLUDE%"=="" (
    echo     [WARNING] OpenCL SDK not found - skipping GPU version
    echo     [INFO] To enable GPU acceleration, install one of:
    echo           NVIDIA CUDA Toolkit / AMD APP SDK / Intel OpenCL SDK
    echo     [INFO] GPU acceleration disabled (CPU only mode)
) else (
    echo     [INFO] OpenCL include: %OPENCL_INCLUDE%
    gcc -O3 -shared -o crack_low32\crack_low32_opencl.dll crack_low32\crack_low32_opencl.c -I"%OPENCL_INCLUDE%" -L"%OPENCL_LIB%" -lOpenCL
    if errorlevel 1 (
        echo     [WARNING] Failed to compile crack_low32_opencl.dll
        echo     [INFO] Check if gcc and the OpenCL SDK are properly installed
        echo     [INFO] GPU acceleration disabled (CPU only mode)
    ) else (
        echo     [OK] crack_low32_opencl.dll created
        echo     [INFO] GPU acceleration enabled
    )
)

echo.
echo [3/3] Building crack_high32.dll...
echo     [INFO] Building with aggressive optimization flags...
gcc -O3 -march=native -mtune=native -flto -fomit-frame-pointer -ffast-math -fno-math-errno -funroll-loops -fno-semantic-interposition -fno-plt -shared -o crack_high32\crack_high32.dll crack_high32\crack_high32.c crack_high32\cubiomes\biomes.c crack_high32\cubiomes\biomenoise.c crack_high32\cubiomes\layers.c crack_high32\cubiomes\noise.c -Icrack_high32\cubiomes
if errorlevel 1 (
    echo     [WARNING] Aggressive flags failed, falling back to -O3...
    gcc -O3 -shared -o crack_high32\crack_high32.dll crack_high32\crack_high32.c crack_high32\cubiomes\biomes.c crack_high32\cubiomes\biomenoise.c crack_high32\cubiomes\layers.c crack_high32\cubiomes\noise.c -Icrack_high32\cubiomes
    if errorlevel 1 (
        echo     [ERROR] Failed to build crack_high32.dll
        exit /b 1
    )
)
echo     [OK] crack_high32.dll created

echo.
echo ==============================================
echo Build Complete!
echo ==============================================
echo.
echo Generated files:
echo   - crack_low32\crack_low32.dll (CPU version)
if exist crack_low32\crack_low32_opencl.dll echo   - crack_low32\crack_low32_opencl.dll (GPU version)
echo   - crack_high32\crack_high32.dll
echo.
echo Usage:
echo   cd crack_low32 ^&^& python crack_low32.py --test
echo   cd crack_high32 ^&^& python crack_high32.py --test
echo.
echo GPU acceleration:
echo   Auto-detect: python crack_low32.py
echo   Force CPU:   python crack_low32.py --cpu
echo   Force GPU:   python crack_low32.py --gpu
