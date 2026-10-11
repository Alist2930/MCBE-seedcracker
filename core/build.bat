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

REM Platform-tagged library names so prebuilt Windows libraries can be
REM shipped alongside the Linux/macOS ones; Python's config_loader
REM resolve_native_lib() picks the matching one and falls back to the
REM bare name for older local builds.
set "LIB_TAG=win_x86_64"
set "LIB_LOW32=crack_low32_%LIB_TAG%.dll"
set "LIB_OPENCL=crack_low32_opencl_%LIB_TAG%.dll"
set "LIB_HIGH32=crack_high32_%LIB_TAG%.dll"

echo ==============================================
echo MCBEseedcracker CLI Build Script (Windows)
echo ==============================================

where gcc >nul 2>&1
if errorlevel 1 (
    echo [ERROR] GCC not found. Install MinGW-w64 and add it to PATH.
    exit /b 1
)

echo.
echo [1/4] Building %LIB_LOW32% (CPU version)...
gcc -O3 -shared -o native\%LIB_LOW32% native_src\crack_low32.c
if errorlevel 1 (
    echo     [ERROR] Failed to build %LIB_LOW32%
    exit /b 1
)
echo     [OK] %LIB_LOW32% created

echo.
echo [2/4] Building %LIB_OPENCL% (GPU version)...
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
    gcc -O3 -shared -o native\%LIB_OPENCL% native_src\crack_low32_opencl.c -I"%OPENCL_INCLUDE%" -L"%OPENCL_LIB%" -lOpenCL
    if errorlevel 1 (
        echo     [WARNING] Failed to compile %LIB_OPENCL%
        echo     [INFO] Check if gcc and the OpenCL SDK are properly installed
        echo     [INFO] GPU acceleration disabled (CPU only mode)
    ) else (
        echo     [OK] %LIB_OPENCL% created
        echo     [INFO] GPU acceleration enabled
    )
)

echo.
echo [3/4] Building %LIB_HIGH32%...
echo     [INFO] Building with aggressive optimization flags...
gcc -O3 -march=native -mtune=native -flto -fomit-frame-pointer -ffast-math -fno-math-errno -funroll-loops -fno-semantic-interposition -fno-plt -shared -o native\%LIB_HIGH32% native_src\crack_high32.c native_src\cubiomes\biomes.c native_src\cubiomes\biomenoise.c native_src\cubiomes\layers.c native_src\cubiomes\noise.c -Inative_src\cubiomes
if errorlevel 1 (
    echo     [WARNING] Aggressive flags failed, falling back to -O3...
    gcc -O3 -shared -o native\%LIB_HIGH32% native_src\crack_high32.c native_src\cubiomes\biomes.c native_src\cubiomes\biomenoise.c native_src\cubiomes\layers.c native_src\cubiomes\noise.c -Inative_src\cubiomes
    if errorlevel 1 (
        echo     [ERROR] Failed to build %LIB_HIGH32%
        exit /b 1
    )
)
echo     [OK] %LIB_HIGH32% created

echo.
echo [4/4] Copying OpenCL kernel next to the GPU library...
copy /Y native_src\crack_low32.cl native\crack_low32.cl >nul
echo     [OK] native\crack_low32.cl

echo.
echo ==============================================
echo Build Complete!
echo ==============================================
echo.
echo Generated files:
echo   - native\%LIB_LOW32% (CPU version)
if exist native\%LIB_OPENCL% echo   - native\%LIB_OPENCL% (GPU version)
echo   - native\%LIB_HIGH32%
echo   - native\crack_low32.cl (OpenCL kernel)
echo.
echo Usage (from the repository root):
echo   python cli\low32.py --test
echo   python cli\high32.py --test
echo.
echo GPU acceleration:
echo   Auto-detect: python cli\low32.py
echo   Force CPU:   python cli\low32.py --cpu
echo   Force GPU:   python cli\low32.py --gpu
