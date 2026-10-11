#!/bin/bash
# MCBEseedcracker Build Script (Linux/macOS)
# Windows users: use build.bat instead
#
# Builds the native libraries into native/ from the sources in native_src/.

set -e

OS="$(uname -s)"
ARCH="$(uname -m)"

echo "=============================================="
echo "MCBEseedcracker Build Script"
if [ "$OS" = "Darwin" ]; then
    echo "Platform: macOS ($ARCH)"
else
    echo "Platform: Linux ($ARCH)"
fi
echo "=============================================="

cd "$(dirname "$0")"

# Platform-tagged library names so prebuilt Linux/macOS libraries can be
# shipped side by side; Python's config_loader.resolve_native_lib() picks
# the matching one and falls back to the bare name for older local builds.
if [ "$OS" = "Darwin" ]; then
    LIB_OS="macos"
else
    LIB_OS="linux"
fi
case "$ARCH" in
    aarch64|arm64) ARCH_TAG="arm64" ;;
    *)             ARCH_TAG="x86_64" ;;
esac
LIB_TAG="${LIB_OS}_${ARCH_TAG}"
LIB_LOW32="crack_low32_${LIB_TAG}.so"
LIB_OPENCL="crack_low32_opencl_${LIB_TAG}.so"
LIB_HIGH32="crack_high32_${LIB_TAG}.so"

echo ""
echo "[1/3] Building ${LIB_LOW32} (CPU version)..."
gcc -O3 -fPIC -shared -o "native/${LIB_LOW32}" native_src/crack_low32.c
if [ -f "native/${LIB_LOW32}" ]; then
    echo "    [OK] ${LIB_LOW32} created"
else
    echo "    [ERROR] Failed to build ${LIB_LOW32}"
    exit 1
fi

echo ""
echo "[2/3] Building ${LIB_OPENCL} (GPU version)..."
OPENCL_FOUND=0
OPENCL_LIBS=""

if [ "$OS" = "Darwin" ]; then
    # macOS: OpenCL framework ships with the OS SDK
    if [ -d /System/Library/Frameworks/OpenCL.framework ]; then
        OPENCL_FOUND=1
        OPENCL_LIBS="-framework OpenCL"
        echo "    [INFO] OpenCL framework found"
    fi
else
    # Linux: try header, pkg-config, then shared object
    if [ -f /usr/include/CL/cl.h ] || [ -f /usr/local/include/CL/cl.h ]; then
        OPENCL_FOUND=1
        echo "    [INFO] OpenCL headers found"
    fi

    if [ $OPENCL_FOUND -eq 0 ]; then
        if pkg-config --exists OpenCL 2>/dev/null; then
            OPENCL_FOUND=1
            echo "    [INFO] OpenCL found via pkg-config"
        fi
    fi

    if [ $OPENCL_FOUND -eq 0 ]; then
        if [ -f /usr/lib/x86_64-linux-gnu/libOpenCL.so ] || \
           [ -f /usr/lib/aarch64-linux-gnu/libOpenCL.so ] || \
           [ -f /usr/lib/libOpenCL.so ] || \
           [ -f /usr/local/lib/libOpenCL.so ]; then
            OPENCL_FOUND=1
            echo "    [INFO] OpenCL library found"
        fi
    fi
    OPENCL_LIBS="-lOpenCL"
fi

if [ $OPENCL_FOUND -eq 1 ]; then
    # gcc inside the if-condition: a failed build must not abort the script
    # under set -e; the else branch then degrades to CPU-only mode
    if gcc -O3 -fPIC -shared -o "native/${LIB_OPENCL}" native_src/crack_low32_opencl.c $OPENCL_LIBS 2>/dev/null; then
        echo "    [OK] ${LIB_OPENCL} created"
        echo "    [INFO] GPU acceleration enabled"
    else
        echo "    [WARNING] Failed to compile ${LIB_OPENCL}"
        echo "    [INFO] Check if gcc and OpenCL are properly installed"
        echo "    [INFO] GPU acceleration disabled (CPU only mode)"
    fi
else
    echo "    [WARNING] OpenCL not found - skipping GPU version"
    if [ "$OS" = "Darwin" ]; then
        echo "    [INFO] macOS ships OpenCL in the system SDK; update Xcode Command Line Tools"
    else
        echo "    [INFO] To enable GPU acceleration, install OpenCL:"
        echo "          Ubuntu/Debian: sudo apt-get install ocl-icd-opencl-dev"
        echo "          Fedora/RHEL: sudo dnf install ocl-icd-devel"
        echo "          Arch Linux: sudo pacman -S ocl-icd"
    fi
    echo "    [INFO] GPU acceleration disabled (CPU only mode)"
fi

echo ""
echo "[3/3] Building ${LIB_HIGH32}..."

# Performance optimization flags
# -march=native -mtune=native: Optimize for current CPU architecture
#   (Apple Silicon does not support -march; use -mcpu instead)
# -flto: Link-time optimization for better inlining
# -fomit-frame-pointer: Free up a register for better performance
# -ffast-math -fno-math-errno: Faster floating-point operations (safe for biome noise)
# -funroll-loops: Unroll small loops for better instruction-level parallelism
# -fno-semantic-interposition -fno-plt: Better function inlining (GCC 10+, Linux only)

if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    OPT_FLAGS="-O3 -mcpu=native -flto -fomit-frame-pointer -ffast-math -fno-math-errno -funroll-loops"
else
    OPT_FLAGS="-O3 -march=native -mtune=native \
    -flto -fomit-frame-pointer \
    -ffast-math -fno-math-errno \
    -funroll-loops \
    -fno-semantic-interposition -fno-plt"
fi

echo "    [INFO] Building with aggressive optimization flags..."
# shellcheck disable=SC2086
gcc $OPT_FLAGS \
    -fPIC -shared -o "native/${LIB_HIGH32}" native_src/crack_high32.c \
    native_src/cubiomes/biomes.c \
    native_src/cubiomes/biomenoise.c \
    native_src/cubiomes/layers.c \
    native_src/cubiomes/noise.c \
    -lm
if [ -f "native/${LIB_HIGH32}" ]; then
    echo "    [OK] ${LIB_HIGH32} created"
else
    echo "    [ERROR] Failed to build ${LIB_HIGH32}"
    exit 1
fi

# The OpenCL kernel is loaded from the library directory at runtime
cp native_src/crack_low32.cl native/crack_low32.cl
echo "    [OK] native/crack_low32.cl (OpenCL kernel)"

echo ""
echo "=============================================="
echo "Build Complete!"
echo "=============================================="
echo ""
echo "Generated files:"
echo "  - native/${LIB_LOW32} (CPU version)"
if [ -f "native/${LIB_OPENCL}" ]; then
    echo "  - native/${LIB_OPENCL} (GPU version)"
fi
echo "  - native/${LIB_HIGH32}"
echo "  - native/crack_low32.cl (OpenCL kernel)"
echo ""
echo "Usage (from the repository root):"
echo "  python cli/low32.py --test"
echo "  python cli/high32.py --test"
echo ""
echo "GPU acceleration:"
echo "  Auto-detect: python cli/low32.py"
echo "  Force CPU:   python cli/low32.py --cpu"
echo "  Force GPU:   python cli/low32.py --gpu"
