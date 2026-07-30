#include "layers.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <float.h>

//==============================================================================
// Voronoi Functions for 1.18+ Biome Generation
//==============================================================================

static inline void getVoronoiCell(uint64_t sha, int a, int b, int c,
                                  int *x, int *y, int *z)
{
    uint64_t s = sha;
    s = mcStepSeed(s, a);
    s = mcStepSeed(s, b);
    s = mcStepSeed(s, c);
    s = mcStepSeed(s, a);
    s = mcStepSeed(s, b);
    s = mcStepSeed(s, c);

    *x = (((s >> 24) & 1023) - 512) * 36;
    s = mcStepSeed(s, sha);
    *y = (((s >> 24) & 1023) - 512) * 36;
    s = mcStepSeed(s, sha);
    *z = (((s >> 24) & 1023) - 512) * 36;
}

uint64_t getVoronoiSHA(uint64_t seed)
{
    static const uint32_t K[64] = {
        0x428a2f98,
        0x71374491,
        0xb5c0fbcf,
        0xe9b5dba5,
        0x3956c25b,
        0x59f111f1,
        0x923f82a4,
        0xab1c5ed5,
        0xd807aa98,
        0x12835b01,
        0x243185be,
        0x550c7dc3,
        0x72be5d74,
        0x80deb1fe,
        0x9bdc06a7,
        0xc19bf174,
        0xe49b69c1,
        0xefbe4786,
        0x0fc19dc6,
        0x240ca1cc,
        0x2de92c6f,
        0x4a7484aa,
        0x5cb0a9dc,
        0x76f988da,
        0x983e5152,
        0xa831c66d,
        0xb00327c8,
        0xbf597fc7,
        0xc6e00bf3,
        0xd5a79147,
        0x06ca6351,
        0x14292967,
        0x27b70a85,
        0x2e1b2138,
        0x4d2c6dfc,
        0x53380d13,
        0x650a7354,
        0x766a0abb,
        0x81c2c92e,
        0x92722c85,
        0xa2bfe8a1,
        0xa81a664b,
        0xc24b8b70,
        0xc76c51a3,
        0xd192e819,
        0xd6990624,
        0xf40e3585,
        0x106aa070,
        0x19a4c116,
        0x1e376c08,
        0x2748774c,
        0x34b0bcb5,
        0x391c0cb3,
        0x4ed8aa4a,
        0x5b9cca4f,
        0x682e6ff3,
        0x748f82ee,
        0x78a5636f,
        0x84c87814,
        0x8cc70208,
        0x90befffa,
        0xa4506ceb,
        0xbef9a3f7,
        0xc67178f2,
    };
    static const uint32_t B[8] = {
        0x6a09e667,
        0xbb67ae85,
        0x3c6ef372,
        0xa54ff53a,
        0x510e527f,
        0x9b05688c,
        0x1f83d9ab,
        0x5be0cd19,
    };

    uint32_t m[64];
    uint32_t a0, a1, a2, a3, a4, a5, a6, a7;
    uint32_t i, x, y;
    m[0] = BSWAP32((uint32_t)(seed));
    m[1] = BSWAP32((uint32_t)(seed >> 32));
    m[2] = 0x80000000;
    for (i = 3; i < 15; i++)
        m[i] = 0;
    m[15] = 0x00000040;

    for (i = 16; i < 64; ++i)
    {
        m[i] = m[i - 7] + m[i - 16];
        x = m[i - 15];
        m[i] += rotr32(x, 7) ^ rotr32(x, 18) ^ (x >> 3);
        x = m[i - 2];
        m[i] += rotr32(x, 17) ^ rotr32(x, 19) ^ (x >> 10);
    }

    a0 = B[0];
    a1 = B[1];
    a2 = B[2];
    a3 = B[3];
    a4 = B[4];
    a5 = B[5];
    a6 = B[6];
    a7 = B[7];

    for (i = 0; i < 64; i++)
    {
        x = a7 + K[i] + m[i];
        x += rotr32(a4, 6) ^ rotr32(a4, 11) ^ rotr32(a4, 25);
        x += (a4 & a5) ^ (~a4 & a6);

        y = rotr32(a0, 2) ^ rotr32(a0, 13) ^ rotr32(a0, 22);
        y += (a0 & a1) ^ (a0 & a2) ^ (a1 & a2);

        a7 = a6;
        a6 = a5;
        a5 = a4;
        a4 = a3 + x;
        a3 = a2;
        a2 = a1;
        a1 = a0;
        a0 = x + y;
    }

    a0 += B[0];
    a1 += B[1];

    return BSWAP32(a0) | ((uint64_t)BSWAP32(a1) << 32);
}

void voronoiAccess3D(uint64_t sha, int x, int y, int z, int *x4, int *y4, int *z4)
{
    x -= 2;
    y -= 2;
    z -= 2;
    int pX = x >> 2;
    int pY = y >> 2;
    int pZ = z >> 2;
    int dx = (x & 3) * 10240;
    int dy = (y & 3) * 10240;
    int dz = (z & 3) * 10240;
    int ax = 0, ay = 0, az = 0;
    uint64_t dmin = (uint64_t)-1;
    int i;

    for (i = 0; i < 8; i++)
    {
        int bx = (i & 4) != 0;
        int by = (i & 2) != 0;
        int bz = (i & 1) != 0;
        int cx = pX + bx;
        int cy = pY + by;
        int cz = pZ + bz;
        int rx, ry, rz;

        getVoronoiCell(sha, cx, cy, cz, &rx, &ry, &rz);

        rx += dx - 40 * 1024 * bx;
        ry += dy - 40 * 1024 * by;
        rz += dz - 40 * 1024 * bz;

        uint64_t d = rx * (uint64_t)rx + ry * (uint64_t)ry + rz * (uint64_t)rz;
        if (d < dmin)
        {
            dmin = d;
            ax = cx;
            ay = cy;
            az = cz;
        }
    }

    if (x4)
        *x4 = ax;
    if (y4)
        *y4 = ay;
    if (z4)
        *z4 = az;
}

void mapVoronoiPlane(uint64_t sha, int *out, int *src,
                     int x, int z, int w, int h, int y, int px, int pz, int pw, int ph)
{
    int i, j;
    for (j = 0; j < h; j++)
    {
        for (i = 0; i < w; i++)
        {
            int bx, by, bz;
            voronoiAccess3D(sha, x + i, y, z + j, &bx, &by, &bz);
            int ip = bx - px;
            int jp = bz - pz;
            if (ip >= 0 && ip < pw && jp >= 0 && jp < ph)
            {
                out[j * w + i] = src[jp * pw + ip];
            }
            else
            {
                out[j * w + i] = 0; // Default biome if out of range
            }
        }
    }
}

//==============================================================================
// Stub Functions for Unused Legacy Layer System
//==============================================================================
// Only mapVoronoi114 is needed - it's declared in layers.h but not used
// for 1.18+ Overworld biome cracking (which uses VoronoiPlane instead)

int mapVoronoi114(const Layer *layer, int *out, int x, int z, int w, int h)
{
    // Stub: Not used for 1.18+ Overworld biome cracking
    // 1.18+ uses mapVoronoiPlane() instead
    (void)layer;
    (void)out;
    (void)x;
    (void)z;
    (void)w;
    (void)h;
    return 0;
}

// Note: mapEnd, mapEndBiome, mapNether3D, mapNether2D are defined in biomenoise.c
// They are used for End/Nether generation but not for Overworld biome cracking