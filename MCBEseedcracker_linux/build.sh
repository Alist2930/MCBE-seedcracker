#!/bin/bash
# MCBEseedcracker Linux Build Script

set -e

echo "=============================================="
echo "MCBEseedcracker Linux Build Script"
echo "=============================================="

cd "$(dirname "$0")"

echo ""
echo "[1/2] Building crack_low32.so..."
cd crack_low32
gcc -O3 -fPIC -shared -o crack_low32.so crack_low32.c
if [ -f crack_low32.so ]; then
    echo "    [OK] crack_low32.so created"
else
    echo "    [ERROR] Failed to build crack_low32.so"
    exit 1
fi
cd ..

echo ""
echo "[2/2] Building crack_high32.so..."
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
    -lm -fopenmp
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
echo "  - crack_low32/crack_low32.so"
echo "  - crack_high32/crack_high32.so"
echo ""
echo "Usage:"
echo "  cd crack_low32 && python crack_low32.py --test"
echo "  cd crack_high32 && python crack_high32.py --test"