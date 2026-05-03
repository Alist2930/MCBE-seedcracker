/**
 * Minecraft Bedrock Edition High 32-bit Seed Cracker
 *
 * This file implements the SOA (Structure of Arrays) optimized biome noise
 * calculation for cracking the high 32 bits of a 64-bit world seed.
 *
 * Build Commands:
 *   Windows (MinGW-w64):
 *     gcc -O3 -shared -o crack_high32.dll crack_high32.c ^
 *         cubiomes/biomes.c cubiomes/biomenoise.c cubiomes/generator.c ^
 *         cubiomes/layers.c cubiomes/noise.c cubiomes/quadbase.c ^
 *         cubiomes/util.c cubiomes/finders.c -lm -fopenmp
 *
 *   Linux:
 *     gcc -O3 -shared -fPIC -o libcrack_high32.so crack_high32.c \
 *         cubiomes/biomes.c cubiomes/biomenoise.c cubiomes/generator.c \
 *         cubiomes/layers.c cubiomes/noise.c cubiomes/quadbase.c \
 *         cubiomes/util.c cubiomes/finders.c -lm -fopenmp
 *
 * Bug Fixes (2024):
 *   1. Fixed SHIFT noise parameter order in sampleBiomeNoiseSOA():
 *      - Original bug: pz used (z, 0, x) instead of (z, x, 0)
 *      - This caused coordinate offset errors in biome calculation
 *   2. Added missing getSpline() offset for depth parameter:
 *      - Original bug: depth calculation was missing the spline offset
 *      - This caused incorrect biome detection for underground biomes
 *        (dripstone_caves, lush_caves) at lower Y coordinates
 *
 * Note: These were code bugs, not double precision issues in SOA implementation.
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <immintrin.h>
#include <omp.h>

#include "cubiomes/biomes.h"
#include "cubiomes/generator.h"
#include "cubiomes/biomenoise.h"
#include "cubiomes/layers.h"
#include "cubiomes/rng.h"

typedef struct
{
    int x;
    int z;
    int biome_id;
} BiomeSample;

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

#define SIMD_WIDTH 4

typedef struct
{
    uint8_t d[4][257];
    double a[4], b[4], c[4];
    double amplitude[4];
    double lacunarity[4];
    int h2[4];
    double d2[4], t2[4];
} PerlinNoiseSOA;

typedef struct
{
    PerlinNoiseSOA *octaves;
    int octcnt;
    double amplitude[4];
} OctaveNoiseSOA;

typedef struct
{
    OctaveNoiseSOA octA, octB;
    double amplitude[4];
} DoublePerlinNoiseSOA;

typedef struct
{
    DoublePerlinNoiseSOA climate[NP_MAX];
    PerlinNoiseSOA *oct;
    int oct_count;
    int nptype;
} BiomeNoiseSOA;

static void xPerlinInitSOA(PerlinNoiseSOA *noise, Xoroshiro xr[4])
{
    for (int s = 0; s < 4; s++)
    {
        noise->a[s] = xNextDouble(&xr[s]) * 256.0;
        noise->b[s] = xNextDouble(&xr[s]) * 256.0;
        noise->c[s] = xNextDouble(&xr[s]) * 256.0;
        noise->amplitude[s] = 1.0;
        noise->lacunarity[s] = 1.0;

        for (int i = 0; i < 256; i++)
            noise->d[s][i] = (uint8_t)i;

        for (int i = 0; i < 256; i++)
        {
            int j = xNextInt(&xr[s], 256 - i) + i;
            uint8_t n = noise->d[s][i];
            noise->d[s][i] = noise->d[s][j];
            noise->d[s][j] = n;
        }
        noise->d[s][256] = noise->d[s][0];

        double b_val = noise->b[s];
        double i2 = floor(b_val);
        double d2_val = b_val - i2;
        noise->h2[s] = (int)i2;
        noise->d2[s] = d2_val;
        noise->t2[s] = d2_val * d2_val * d2_val * (d2_val * (d2_val * 6.0 - 15.0) + 10.0);
    }
}

static int xOctaveInitSOA(OctaveNoiseSOA *noise, Xoroshiro xr[4],
                          PerlinNoiseSOA *octaves, const double *amplitudes, int omin, int len, int nmax)
{
    static const uint64_t md5_octave_n[][2] = {
        {0xb198de63a8012672, 0x7b84cad43ef7b5a8},
        {0x0fd787bfbc403ec3, 0x74a4a31ca21b48b8},
        {0x36d326eed40efeb2, 0x5be9ce18223c636a},
        {0x082fe255f8be6631, 0x4e96119e22dedc81},
        {0x0ef68ec68504005e, 0x48b6bf93a2789640},
        {0xf11268128982754f, 0x257a1d670430b0aa},
        {0xe51c98ce7d1de664, 0x5f9478a733040c45},
        {0x6d7b49e7e429850a, 0x2e3063c622a24777},
        {0xbd90d5377ba1b762, 0xc07317d419a7548d},
        {0x53d39c6752dac858, 0xbcd1c5a80ab65b3e},
        {0xb4a24d7a84e7677b, 0x023ff9668e89b5c4},
        {0xdffa22b534c5f608, 0xb9b67517d3665ca9},
        {0xd50708086cef4d7c, 0x6e1651ecc7f43309},
    };
    static const double lacuna_ini[] = {
        1,
        .5,
        .25,
        1. / 8,
        1. / 16,
        1. / 32,
        1. / 64,
        1. / 128,
        1. / 256,
        1. / 512,
        1. / 1024,
        1. / 2048,
        1. / 4096,
    };
    static const double persist_ini[] = {
        0,
        1,
        2. / 3,
        4. / 7,
        8. / 15,
        16. / 31,
        32. / 63,
        64. / 127,
        128. / 255,
        256. / 511,
    };

    int i = 0, n = 0;
    double lacuna = lacuna_ini[-omin];
    double persist = persist_ini[len];

    uint64_t xlo[4], xhi[4];
    for (int s = 0; s < 4; s++)
    {
        xlo[s] = xNextLong(&xr[s]);
        xhi[s] = xNextLong(&xr[s]);
    }

    noise->octaves = octaves;
    noise->octcnt = 0;

    for (; i < len && n != nmax; i++, lacuna *= 2.0, persist *= 0.5)
    {
        if (amplitudes[i] == 0)
            continue;
        Xoroshiro xr_copy[4];
        for (int s = 0; s < 4; s++)
        {
            xr_copy[s].lo = xlo[s] ^ md5_octave_n[12 + omin + i][0];
            xr_copy[s].hi = xhi[s] ^ md5_octave_n[12 + omin + i][1];
        }
        xPerlinInitSOA(&octaves[n], xr_copy);
        for (int s = 0; s < 4; s++)
        {
            octaves[n].amplitude[s] = amplitudes[i] * persist;
            octaves[n].lacunarity[s] = lacuna;
        }
        n++;
    }

    noise->octcnt = n;
    return n;
}

static int xDoublePerlinInitSOA(DoublePerlinNoiseSOA *noise, Xoroshiro xr[4],
                                PerlinNoiseSOA *octaves, const double *amplitudes, int omin, int len, int nmax)
{
    int na = -1, nb = -1;
    if (nmax > 0)
    {
        na = (nmax + 1) >> 1;
        nb = nmax - na;
    }

    int n = 0;
    n += xOctaveInitSOA(&noise->octA, xr, octaves + n, amplitudes, omin, len, na);
    n += xOctaveInitSOA(&noise->octB, xr, octaves + n, amplitudes, omin, len, nb);

    int i;
    int trim_len = len;
    for (i = trim_len - 1; i >= 0 && amplitudes[i] == 0.0; i--)
        trim_len--;
    for (i = 0; i < trim_len && amplitudes[i] == 0.0; i++)
        trim_len--;
    static const double amp_ini[] = {
        0,
        5. / 6,
        10. / 9,
        15. / 12,
        20. / 15,
        25. / 18,
        30. / 21,
        35. / 24,
        40. / 27,
        45. / 30,
    };
    double amp = (trim_len >= 1 && trim_len <= 9) ? amp_ini[trim_len] : (10.0 / 6.0) * trim_len / (trim_len + 1);
    for (int s = 0; s < 4; s++)
        noise->amplitude[s] = amp;
    return n;
}

static int init_climate_seed_soa(DoublePerlinNoiseSOA *dpn, PerlinNoiseSOA *oct,
                                 uint64_t xlo[4], uint64_t xhi[4], int large, int nptype, int nmax)
{
    Xoroshiro pxr[4];

    static const double amp_temp[] = {1.5, 0, 1, 0, 0, 0};
    static const double amp_humid[] = {1, 1, 0, 0, 0, 0};
    static const double amp_cont[] = {1, 1, 2, 2, 2, 1, 1, 1, 1};
    static const double amp_erosion[] = {1, 1, 0, 1, 1};
    static const double amp_shift[] = {1, 1, 1, 0};
    static const double amp_weirdness[] = {1, 2, 1, 0, 0, 0};

    static const struct
    {
        uint64_t lo, hi;
        const double *amp;
        int omin, len;
    } climate_params[] = {
        [NP_TEMPERATURE] = {0x5c7e6b29735f0d7f, 0xf7d86f1bbc734988, amp_temp, -10, 6},
        [NP_HUMIDITY] = {0x81bb4d22e8dc168e, 0xf1c8b4bea16303cd, amp_humid, -8, 6},
        [NP_CONTINENTALNESS] = {0x83886c9d0ae3a662, 0xafa638a61b42e8ad, amp_cont, -9, 9},
        [NP_EROSION] = {0xd02491e6058f6fd8, 0x4792512c94c17a80, amp_erosion, -9, 5},
        [NP_SHIFT] = {0x080518cf6af25384, 0x3f3dfb40a54febd5, amp_shift, -3, 4},
        [NP_WEIRDNESS] = {0xefc8ef4d36102b34, 0x1beeeb324a0f24ea, amp_weirdness, -7, 6},
    };

    for (int s = 0; s < 4; s++)
    {
        pxr[s].lo = xlo[s] ^ climate_params[nptype].lo;
        pxr[s].hi = xhi[s] ^ climate_params[nptype].hi;
    }

    return xDoublePerlinInitSOA(dpn, pxr, oct, climate_params[nptype].amp,
                                climate_params[nptype].omin, climate_params[nptype].len, nmax);
}

static void setBiomeSeedSOA(BiomeNoiseSOA *bn, uint64_t seeds[4], int large)
{
    Xoroshiro pxr[4];
    uint64_t xlo[4], xhi[4];

    for (int s = 0; s < 4; s++)
    {
        xSetSeed(&pxr[s], seeds[s]);
        xlo[s] = xNextLong(&pxr[s]);
        xhi[s] = xNextLong(&pxr[s]);
    }

    int n = 0;
    for (int i = 0; i < NP_MAX; i++)
    {
        n += init_climate_seed_soa(&bn->climate[i], bn->oct + n, xlo, xhi, large, i, -1);
    }

    bn->oct_count = n;
    bn->nptype = -1;
}

static inline double indexedLerpSOA(uint8_t idx, double a, double b, double c)
{
    switch (idx & 0xf)
    {
    case 0:
        return a + b;
    case 1:
        return -a + b;
    case 2:
        return a - b;
    case 3:
        return -a - b;
    case 4:
        return a + c;
    case 5:
        return -a + c;
    case 6:
        return a - c;
    case 7:
        return -a - c;
    case 8:
        return b + c;
    case 9:
        return -b + c;
    case 10:
        return b - c;
    case 11:
        return -b - c;
    case 12:
        return a + b;
    case 13:
        return -b + c;
    case 14:
        return -a + b;
    case 15:
        return -b - c;
    }
    return 0;
}

static inline double samplePerlinSOA(const PerlinNoiseSOA *noise, double d1, double d2, double d3, int idx)
{
    uint8_t h1, h2, h3;
    double t1, t2, t3;

    if (d2 == 0.0)
    {
        d2 = noise->d2[idx];
        h2 = (uint8_t)noise->h2[idx];
        t2 = noise->t2[idx];
    }
    else
    {
        d2 += noise->b[idx];
        double i2 = floor(d2);
        d2 -= i2;
        h2 = (uint8_t)i2;
        t2 = d2 * d2 * d2 * (d2 * (d2 * 6.0 - 15.0) + 10.0);
    }

    d1 += noise->a[idx];
    d3 += noise->c[idx];

    double i1 = floor(d1);
    double i3 = floor(d3);
    d1 -= i1;
    d3 -= i3;

    h1 = (uint8_t)i1;
    h3 = (uint8_t)i3;

    t1 = d1 * d1 * d1 * (d1 * (d1 * 6.0 - 15.0) + 10.0);
    t3 = d3 * d3 * d3 * (d3 * (d3 * 6.0 - 15.0) + 10.0);

    const uint8_t *p = noise->d[idx];

    uint8_t a1 = p[h1] + h2;
    uint8_t b1 = p[h1 + 1] + h2;

    uint8_t a2 = p[a1] + h3;
    uint8_t b2 = p[b1] + h3;
    uint8_t a3 = p[a1 + 1] + h3;
    uint8_t b3 = p[b1 + 1] + h3;

    double l1 = indexedLerpSOA(p[a2], d1, d2, d3);
    double l2 = indexedLerpSOA(p[b2], d1 - 1, d2, d3);
    double l3 = indexedLerpSOA(p[a3], d1, d2 - 1, d3);
    double l4 = indexedLerpSOA(p[b3], d1 - 1, d2 - 1, d3);
    double l5 = indexedLerpSOA(p[a2 + 1], d1, d2, d3 - 1);
    double l6 = indexedLerpSOA(p[b2 + 1], d1 - 1, d2, d3 - 1);
    double l7 = indexedLerpSOA(p[a3 + 1], d1, d2 - 1, d3 - 1);
    double l8 = indexedLerpSOA(p[b3 + 1], d1 - 1, d2 - 1, d3 - 1);

    l1 = l1 + t1 * (l2 - l1);
    l3 = l3 + t1 * (l4 - l3);
    l5 = l5 + t1 * (l6 - l5);
    l7 = l7 + t1 * (l8 - l7);

    l1 = l1 + t2 * (l3 - l1);
    l5 = l5 + t2 * (l7 - l5);

    return l1 + t3 * (l5 - l1);
}

static inline double sampleOctaveSOA(const OctaveNoiseSOA *noise, double x, double y, double z, int idx)
{
    double v = 0;
    for (int i = 0; i < noise->octcnt; i++)
    {
        const PerlinNoiseSOA *p = &noise->octaves[i];
        double lf = p->lacunarity[idx];
        double ax = maintainPrecision(x * lf);
        double ay = maintainPrecision(y * lf);
        double az = maintainPrecision(z * lf);
        double pv = samplePerlinSOA(p, ax, ay, az, idx);
        v += p->amplitude[idx] * pv;
    }
    return v;
}

static double sampleDoublePerlinSOA(const DoublePerlinNoiseSOA *noise, double x, double y, double z, int idx)
{
    const double f = 337.0 / 331.0;
    double v = 0;
    v += sampleOctaveSOA(&noise->octA, x, y, z, idx);
    v += sampleOctaveSOA(&noise->octB, x * f, y * f, z * f, idx);
    return v * noise->amplitude[idx];
}

static void sampleBiomeNoiseSOA(const BiomeNoiseSOA *bn, int64_t np[4][6], int x4[4], int y4[4], int z4[4], int mc_version)
{
    BiomeNoise bn_tmp;
    memset(&bn_tmp, 0, sizeof(bn_tmp));
    initBiomeNoise(&bn_tmp, mc_version);

    for (int s = 0; s < 4; s++)
    {
        for (int i = 0; i < 6; i++)
            np[s][i] = 0;
    }

    double px[4], pz[4];
    for (int s = 0; s < 4; s++)
    {
        px[s] = x4[s] + sampleDoublePerlinSOA(&bn->climate[NP_SHIFT], x4[s], 0, z4[s], s) * 4.0;
        pz[s] = z4[s] + sampleDoublePerlinSOA(&bn->climate[NP_SHIFT], z4[s], x4[s], 0, s) * 4.0;
    }

    for (int s = 0; s < 4; s++)
    {
        double t = sampleDoublePerlinSOA(&bn->climate[NP_TEMPERATURE], px[s], 0, pz[s], s);
        double h = sampleDoublePerlinSOA(&bn->climate[NP_HUMIDITY], px[s], 0, pz[s], s);
        double c = sampleDoublePerlinSOA(&bn->climate[NP_CONTINENTALNESS], px[s], 0, pz[s], s);
        double e = sampleDoublePerlinSOA(&bn->climate[NP_EROSION], px[s], 0, pz[s], s);
        double w = sampleDoublePerlinSOA(&bn->climate[NP_WEIRDNESS], px[s], 0, pz[s], s);

        float np_param[] = {
            (float)c,
            (float)e,
            -3.0F * (fabsf(fabsf((float)w) - 0.6666667F) - 0.33333334F),
            (float)w,
        };
        double off = getSpline(bn_tmp.sp, np_param) + 0.015F;
        double d = 1.0 - (y4[s] * 4) / 128.0 - 83.0 / 160.0 + off;

        np[s][0] = (int64_t)(t * 10000.0);
        np[s][1] = (int64_t)(h * 10000.0);
        np[s][2] = (int64_t)(c * 10000.0);
        np[s][3] = (int64_t)(e * 10000.0);
        np[s][4] = (int64_t)(d * 10000.0);
        np[s][5] = (int64_t)(w * 10000.0);
    }
}

static int climateToBiomeSOA(int mc, int64_t np[6])
{
    BiomeNoise bn;
    memset(&bn, 0, sizeof(bn));
    initBiomeNoise(&bn, mc);
    return climateToBiome(mc, (const uint64_t *)np, NULL);
}

EXPORT int phase1_filter_avx2(
    uint32_t start_high,
    uint32_t end_high,
    uint32_t low32,
    int y_coord,
    BiomeSample *rare_sample,
    uint64_t *candidates,
    int max_candidates,
    int mc_version)
{
    if (start_high >= end_high)
        return 0;

    int x = rare_sample->x;
    int z = rare_sample->z;
    int target_id = rare_sample->biome_id;

    int total = 0;

#pragma omp parallel
    {
        BiomeNoiseSOA *bn_soa = (BiomeNoiseSOA *)malloc(sizeof(BiomeNoiseSOA));
        memset(bn_soa, 0, sizeof(BiomeNoiseSOA));
        bn_soa->oct = (PerlinNoiseSOA *)malloc(256 * sizeof(PerlinNoiseSOA));
        memset(bn_soa->oct, 0, 256 * sizeof(PerlinNoiseSOA));

        uint64_t seeds[4];
        uint64_t sha[4];
        int x4[4], y4[4], z4[4];
        int64_t np[4][6];

#pragma omp for schedule(dynamic, 10000)
        for (uint64_t high = start_high; high < end_high; high += 4)
        {
            int batch_size = 4;
            if (high + 4 > end_high)
                batch_size = end_high - high;

            for (int s = 0; s < batch_size; s++)
            {
                seeds[s] = (((uint64_t)(high + s)) << 32) | low32;
                sha[s] = getVoronoiSHA(seeds[s]);
                voronoiAccess3D(sha[s], x, y_coord, z, &x4[s], &y4[s], &z4[s]);
            }

            setBiomeSeedSOA(bn_soa, seeds, 0);

            sampleBiomeNoiseSOA(bn_soa, np, x4, y4, z4, mc_version);

            for (int s = 0; s < batch_size; s++)
            {
                int biome_id = climateToBiomeSOA(mc_version, np[s]);

                if (biome_id == target_id)
                {
#pragma omp critical
                    {
                        if (total < max_candidates)
                        {
                            candidates[total++] = high + s;
                        }
                    }
                }
            }
        }

        free(bn_soa->oct);
        free(bn_soa);
    }

    return total;
}

EXPORT int phase2_verify(
    uint64_t *candidates,
    int num_candidates,
    uint32_t low32,
    int y_coord,
    BiomeSample *other_samples,
    int num_other_samples,
    uint64_t *results,
    int max_results,
    int mc_version)
{
    if (num_candidates == 0)
        return 0;

    int found_count = 0;

    BiomeNoiseSOA *bn_soa = (BiomeNoiseSOA *)malloc(sizeof(BiomeNoiseSOA));
    if (!bn_soa)
        return 0;
    memset(bn_soa, 0, sizeof(BiomeNoiseSOA));
    bn_soa->oct = (PerlinNoiseSOA *)malloc(256 * sizeof(PerlinNoiseSOA));
    if (!bn_soa->oct)
    {
        free(bn_soa);
        return 0;
    }
    memset(bn_soa->oct, 0, 256 * sizeof(PerlinNoiseSOA));

    uint64_t seeds[4];
    uint64_t sha[4];

    for (int c = 0; c < num_candidates && found_count < max_results; c += 4)
    {
        int batch_size = 4;
        if (c + 4 > num_candidates)
            batch_size = num_candidates - c;

        for (int s = 0; s < batch_size; s++)
        {
            seeds[s] = (((uint64_t)candidates[c + s]) << 32) | low32;
            sha[s] = getVoronoiSHA(seeds[s]);
        }

        setBiomeSeedSOA(bn_soa, seeds, 0);

        int all_match[4] = {1, 1, 1, 1};

        for (int i = 0; i < num_other_samples; i++)
        {
            int x4[4], y4[4], z4[4];
            int64_t np[4][6];

            for (int s = 0; s < batch_size; s++)
            {
                voronoiAccess3D(sha[s], other_samples[i].x, y_coord, other_samples[i].z, &x4[s], &y4[s], &z4[s]);
            }

            sampleBiomeNoiseSOA(bn_soa, np, x4, y4, z4, mc_version);

            for (int s = 0; s < batch_size; s++)
            {
                if (all_match[s])
                {
                    int actual_id = climateToBiomeSOA(mc_version, np[s]);
                    if (actual_id != other_samples[i].biome_id)
                        all_match[s] = 0;
                }
            }
        }

        for (int s = 0; s < batch_size; s++)
        {
            if (all_match[s])
            {
                results[found_count++] = seeds[s];
            }
        }
    }

    free(bn_soa->oct);
    free(bn_soa);
    return found_count;
}

EXPORT int getBiomeAtSeed(
    uint64_t seed,
    int x,
    int y,
    int z,
    int mc_version)
{
    BiomeNoise bn;
    memset(&bn, 0, sizeof(bn));
    initBiomeNoise(&bn, mc_version);
    setBiomeSeed(&bn, seed, 0);
    uint64_t sha = getVoronoiSHA(seed);

    int x4, y4, z4;
    voronoiAccess3D(sha, x, y, z, &x4, &y4, &z4);

    int64_t np[6];
    sampleBiomeNoise(&bn, np, x4, y4, z4, NULL, 0);
    return climateToBiome(mc_version, (const uint64_t *)np, NULL);
}
