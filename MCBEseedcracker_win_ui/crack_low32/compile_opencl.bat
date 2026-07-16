@echo off
REM Build script for OpenCL version of crack_low32
REM
REM Prerequisites:
REM   1. MinGW-w64 GCC installed
REM   2. NVIDIA CUDA Toolkit installed (for OpenCL headers and libs)
REM      OR AMD APP SDK / Intel OpenCL SDK
REM
REM Usage: build_opencl.bat

echo ========================================
echo Building crack_low32 OpenCL version
echo ========================================

REM Try to find OpenCL SDK
set "OPENCL_INCLUDE="
set "OPENCL_LIB="

REM Check NVIDIA CUDA Toolkit
if exist "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA" (
    for /d %%d in ("C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*") do (
        if exist "%%d\include\CL\cl.h" (
            set "OPENCL_INCLUDE=%%d\include"
            set "OPENCL_LIB=%%d\lib\x64"
            goto :found_nvidia
        )
    )
)

REM Check AMD APP SDK
if exist "C:\Program Files (x86)\AMD APP SDK\include\CL\cl.h" (
    set "OPENCL_INCLUDE=C:\Program Files (x86)\AMD APP SDK\include"
    set "OPENCL_LIB=C:\Program Files (x86)\AMD APP SDK\lib\x86_64"
    goto :found_amd
)

REM Check Intel OpenCL SDK
if exist "C:\Program Files (x86)\Intel\OpenCL SDK\include\CL\cl.h" (
    set "OPENCL_INCLUDE=C:\Program Files (x86)\Intel\OpenCL SDK\include"
    set "OPENCL_LIB=C:\Program Files (x86)\Intel\OpenCL SDK\lib\x64"
    goto :found_intel
)

echo [ERROR] OpenCL SDK not found!
echo Please install one of the following:
echo   - NVIDIA CUDA Toolkit
echo   - AMD APP SDK
echo   - Intel OpenCL SDK
pause
exit /b 1

:found_nvidia
echo [INFO] Found NVIDIA CUDA Toolkit
goto :build

:found_amd
echo [INFO] Found AMD APP SDK
goto :build

:found_intel
echo [INFO] Found Intel OpenCL SDK
goto :build

:build
echo [INFO] OpenCL include: %OPENCL_INCLUDE%
echo [INFO] OpenCL lib: %OPENCL_LIB%

REM Compile OpenCL version
echo.
echo Compiling crack_low32_opencl.dll...
gcc -O3 -shared -o crack_low32_opencl.dll crack_low32_opencl.c ^
    -I"%OPENCL_INCLUDE%" -L"%OPENCL_LIB%" -lOpenCL

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Compilation failed!
    pause
    exit /b 1
)

echo [SUCCESS] crack_low32_opencl.dll created!

REM Also compile CPU version
echo.
echo Compiling crack_low32.dll (CPU version)...
gcc -O3 -shared -o crack_low32.dll crack_low32.c

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] CPU version compilation failed!
    pause
    exit /b 1
)

echo [SUCCESS] crack_low32.dll created!

echo.
echo ========================================
echo Build complete!
echo   - crack_low32.dll (CPU version)
echo   - crack_low32_opencl.dll (GPU version)
echo ========================================
pause