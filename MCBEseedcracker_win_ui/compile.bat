@echo off
echo ================================================
echo MCBE Seed Cracker Windows Compilation
echo ================================================
echo.

REM Check GCC
where gcc >nul 2>&1
if errorlevel 1 (
    echo [ERROR] GCC not found
    pause
    exit /b 1
)

REM Check CUDA
set CUDA_PATH=
if exist "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v9.0" set CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v9.0

if "%CUDA_PATH%"=="" (
    echo [WARNING] CUDA not found, GPU disabled
) else (
    echo [INFO] CUDA: %CUDA_PATH%
)

echo.
echo [1/4] Compiling crack_low32.dll...
gcc -O3 -shared -fPIC -o crack_low32\crack_low32.dll crack_low32\crack_low32.c -lgomp
if errorlevel 1 (
    echo [ERROR] Failed
    pause
    exit /b 1
)
echo [OK] crack_low32.dll

if not "%CUDA_PATH%"=="" (
    echo.
    echo [2/4] Compiling GPU version...
    gcc -O3 -shared -fPIC -o crack_low32\crack_low32_opencl.dll crack_low32\crack_low32_opencl.c -I"%CUDA_PATH%\include" -L"%CUDA_PATH%\lib\x64" -lOpenCL
    if errorlevel 1 (
        echo [WARNING] GPU compile failed
    ) else (
        echo [OK] crack_low32_opencl.dll
    )
) else (
    echo.
    echo [2/4] Skipping GPU (CUDA not found)
)

echo.
echo [3/4] Compiling crack_high32.dll...
gcc -O3 -shared -fPIC -o crack_high32\crack_high32.dll crack_high32\crack_high32.c crack_high32\cubiomes\biomenoise.c crack_high32\cubiomes\biomes.c crack_high32\cubiomes\finders.c crack_high32\cubiomes\generator.c crack_high32\cubiomes\layers.c crack_high32\cubiomes\noise.c crack_high32\cubiomes\quadbase.c crack_high32\cubiomes\util.c -Icrack_high32\cubiomes -lgomp
if errorlevel 1 (
    echo [ERROR] Failed
    pause
    exit /b 1
)
echo [OK] crack_high32.dll

echo.
echo [4/4] Copying to dll directory...
if not exist dll\crack_low32 mkdir dll\crack_low32
if not exist dll\crack_high32 mkdir dll\crack_high32

copy /Y crack_low32\crack_low32.dll dll\crack_low32\ >nul
copy /Y crack_low32\crack_low32.cl dll\crack_low32\ >nul
if exist crack_low32\crack_low32_opencl.dll copy /Y crack_low32\crack_low32_opencl.dll dll\crack_low32\ >nul
copy /Y crack_high32\crack_high32.dll dll\crack_high32\ >nul

echo [DONE]

echo.
echo ================================================
echo Complete!
echo ================================================
echo Files:
echo   - dll\crack_low32\crack_low32.dll
if not "%CUDA_PATH%"=="" echo   - dll\crack_low32\crack_low32_opencl.dll
echo   - dll\crack_high32\crack_high32.dll
echo.
pause