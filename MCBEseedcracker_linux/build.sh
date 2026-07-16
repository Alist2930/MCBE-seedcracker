#!/bin/bash
# MCBEseedcracker Linux Build Script

set -e

echo "=============================================="
echo "MCBEseedcracker Linux Build Script"
echo "=============================================="

cd "$(dirname "$0")"

echo ""
echo "[1/3] Building crack_low32.so (CPU version)..."
cd crack_low32
gcc -O3 -fPIC -shared -o crack_low32.so crack_low32.c
if [ -f crack_low32.so ]; then
    echo "    [OK] crack_low32.so created"
else
    echo "    [ERROR] Failed to build crack_low32.so"
    exit 1
fi

echo ""
echo "[2/3] Building crack_low32_opencl.so (GPU version)..."
# Check if OpenCL is available (try multiple methods)
OPENCL_FOUND=0

# Method 1: Check if header exists
if [ -f /usr/include/CL/cl.h ] || [ -f /usr/local/include/CL/cl.h ]; then
    OPENCL_FOUND=1
    echo "    [INFO] OpenCL headers found"
fi

# Method 2: Try pkg-config
if [ $OPENCL_FOUND -eq 0 ]; then
    if pkg-config --exists OpenCL 2>/dev/null; then
        OPENCL_FOUND=1
        echo "    [INFO] OpenCL found via pkg-config"
    fi
fi

# Method 3: Check if libOpenCL.so exists
if [ $OPENCL_FOUND -eq 0 ]; then
    if [ -f /usr/lib/x86_64-linux-gnu/libOpenCL.so ] || \
       [ -f /usr/lib/libOpenCL.so ] || \
       [ -f /usr/local/lib/libOpenCL.so ]; then
        OPENCL_FOUND=1
        echo "    [INFO] OpenCL library found"
    fi
fi

if [ $OPENCL_FOUND -eq 1 ]; then
    gcc -O3 -fPIC -shared -o crack_low32_opencl.so crack_low32_opencl.c -lOpenCL 2>/dev/null
    if [ -f crack_low32_opencl.so ]; then
        echo "    [OK] crack_low32_opencl.so created"
        echo "    [INFO] GPU acceleration enabled"
    else
        echo "    [WARNING] Failed to compile crack_low32_opencl.so"
        echo "    [INFO] Check if gcc and OpenCL are properly installed"
        echo "    [INFO] GPU acceleration disabled (CPU only mode)"
    fi
else
    echo "    [WARNING] OpenCL not found - skipping GPU version"
    echo "    [INFO] To enable GPU acceleration, install OpenCL:"
    echo "          Ubuntu/Debian: sudo apt-get install ocl-icd-opencl-dev"
    echo "          Fedora/RHEL: sudo dnf install ocl-icd-devel"
    echo "          Arch Linux: sudo pacman -S ocl-icd"
    echo "    [INFO] GPU acceleration disabled (CPU only mode)"
fi
cd ..

echo ""
echo "[3/3] Building crack_high32.so..."
cd crack_high32
gcc -O3 -fPIC -shared -o crack_high32.so crack_high32.c \
    cubiomes/biomes.c \
    cubiomes/biomenoise.c \
    cubiomes/generator.c \
    cubiomes/layers.c \
    cubiomes/noise.c \
    cubiomes/quadbase.c \
    cubiomes/util.c \
    cubiomes/finders.c \
    -lm
if [ -f crack_high32.so ]; then
    echo "    [OK] crack_high32.so created"
else
    echo "    [ERROR] Failed to build crack_high32.so"
    exit 1
fi
cd ..

echo ""
echo "=============================================="
echo "Build Complete!"
echo "=============================================="
echo ""
echo "Generated files:"
echo "  - crack_low32/crack_low32.so (CPU version)"
if [ -f crack_low32/crack_low32_opencl.so ]; then
    echo "  - crack_low32/crack_low32_opencl.so (GPU version)"
fi
echo "  - crack_high32/crack_high32.so"
echo ""
echo "Usage:"
echo "  cd crack_low32 && python crack_low32.py --test"
echo "  cd crack_high32 && python crack_high32.py --test"
echo ""
echo "GPU acceleration:"
echo "  Auto-detect: python crack_low32.py"
echo "  Force CPU:   python crack_low32.py --cpu"
echo "  Force GPU:   python crack_low32.py --gpu"