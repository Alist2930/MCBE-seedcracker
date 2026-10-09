/**
 * Minecraft Bedrock Low 32-bit Seed Cracker
 *
 * Compile:
 *   gcc -O3 -fPIC -shared -o crack_low32.dll crack_low32.c
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MT_MAGIC 0x9908b0df
#define MT_UPPER_MASK 0x80000000
#define MT_LOWER_MASK 0x7FFFFFFF

#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

typedef struct {
    uint32_t r_base;
    uint32_t ox;
    uint32_t oz;
    uint32_t offset_range;
    int spread_type;
} TargetInfo;

static inline uint32_t mt_temper(uint32_t y) {
    y ^= (y >> 11);
    y ^= (y << 7) & 0x9d2c5680U;
    y ^= (y << 15) & 0xefc60000U;
    y ^= (y >> 18);
    return y;
}

static inline int check_mt_seed_linear(uint32_t r_seed, uint32_t target_ox, uint32_t target_oz, uint32_t offset_range) {
    uint32_t m_prev = r_seed;
    uint32_t m_1 = 0, m_2 = 0, m_397 = 0, m_398 = 0;

    for (int i = 1; i < 399; i++) {
        uint32_t m_curr = (0x6c078965U * (m_prev ^ (m_prev >> 30)) + (uint32_t)i) & 0xFFFFFFFFU;

        if (i == 1) m_1 = m_curr;
        else if (i == 2) m_2 = m_curr;
        else if (i == 397) m_397 = m_curr;
        else if (i == 398) m_398 = m_curr;

        m_prev = m_curr;
    }

    uint32_t y0 = (r_seed & MT_UPPER_MASK) | (m_1 & MT_LOWER_MASK);
    uint32_t val0 = m_397 ^ (y0 >> 1);
    if (y0 & 1) val0 ^= MT_MAGIC;

    uint32_t t0 = mt_temper(val0);
    if ((t0 % offset_range) != target_ox) return 0;

    uint32_t y1 = (m_1 & MT_UPPER_MASK) | (m_2 & MT_LOWER_MASK);
    uint32_t val1 = m_398 ^ (y1 >> 1);
    if (y1 & 1) val1 ^= MT_MAGIC;

    uint32_t t1 = mt_temper(val1);
    if ((t1 % offset_range) != target_oz) return 0;

    return 1;
}

static inline int check_mt_seed_triangular(uint32_t r_seed, uint32_t target_ox, uint32_t target_oz, uint32_t offset_range) {
    uint32_t mt[624];
    mt[0] = r_seed;

    for (int i = 1; i < 624; i++) {
        mt[i] = (0x6c078965U * (mt[i-1] ^ (mt[i-1] >> 30)) + (uint32_t)i) & 0xFFFFFFFFU;
    }

    for (int i = 0; i < 227; i++) {
        uint32_t y = (mt[i] & MT_UPPER_MASK) | (mt[i+1] & MT_LOWER_MASK);
        mt[i] = mt[i+397] ^ (y >> 1);
        if (y & 1) mt[i] ^= MT_MAGIC;
    }

    for (int i = 227; i < 623; i++) {
        uint32_t y = (mt[i] & MT_UPPER_MASK) | (mt[i+1] & MT_LOWER_MASK);
        mt[i] = mt[i-227] ^ (y >> 1);
        if (y & 1) mt[i] ^= MT_MAGIC;
    }

    uint32_t y623 = (mt[623] & MT_UPPER_MASK) | (mt[0] & MT_LOWER_MASK);
    mt[623] = mt[396] ^ (y623 >> 1);
    if (y623 & 1) mt[623] ^= MT_MAGIC;

    uint32_t t0 = mt_temper(mt[0]);
    uint32_t t1 = mt_temper(mt[1]);
    uint32_t t2 = mt_temper(mt[2]);
    uint32_t t3 = mt_temper(mt[3]);

    uint32_t ox = (t0 % offset_range + t1 % offset_range) / 2;
    uint32_t oz = (t2 % offset_range + t3 % offset_range) / 2;

    if (ox != target_ox || oz != target_oz) return 0;

    return 1;
}

static inline int check_mt_seed(uint32_t r_seed, uint32_t target_ox, uint32_t target_oz,
                                 uint32_t offset_range, int spread_type) {
    if (spread_type == 1) {
        return check_mt_seed_triangular(r_seed, target_ox, target_oz, offset_range);
    } else {
        return check_mt_seed_linear(r_seed, target_ox, target_oz, offset_range);
    }
}

EXPORT int crack_low32(
    uint32_t start,
    uint32_t end,
    uint32_t* r_base,
    uint32_t* ox,
    uint32_t* oz,
    uint32_t* offset_range,
    int* spread_type,
    int num_targets,
    uint32_t* results,
    int max_results
) {
    /* Security hardening: validate all inputs before use */
    if (!r_base || !ox || !oz || !offset_range || !spread_type || !results) {
        return -1;  /* Reject NULL pointers */
    }

    if (num_targets <= 0 || max_results <= 0) {
        return -1;  /* Reject invalid counts */
    }

    /* Validate offset_range for all targets to prevent SIGFPE (divide by zero) */
    for (int i = 0; i < num_targets; i++) {
        if (offset_range[i] == 0) {
            return -1;  /* Reject offset_range=0 (spacing == separation) */
        }
    }

    int found_count = 0;

    for (uint64_t w_seed = start; w_seed < end && found_count < max_results; w_seed++) {
        uint32_t w = (uint32_t)w_seed;
        uint32_t r0 = w + r_base[0];

        if (check_mt_seed(r0, ox[0], oz[0], offset_range[0], spread_type[0])) {
            int all_match = 1;

            for (int i = 1; i < num_targets; i++) {
                uint32_t rn = w + r_base[i];
                if (!check_mt_seed(rn, ox[i], oz[i], offset_range[i], spread_type[i])) {
                    all_match = 0;
                    break;
                }
            }

            if (all_match) {
                results[found_count++] = w;
            }
        }
    }

    return found_count;
}

/**
 * Crack low32 with grid offset support (4-chunk grid).
 * For each structure, checks num_offsets possible (r_base, ox, oz) combinations.
 * A seed is valid if each structure matches at least one of its offsets.
 *
 * Array layout: r_base/ox/oz are [num_structures * num_offsets] (flattened by structure then offset).
 * offset_range/spread_type are [num_structures] (shared across offsets of same structure).
 */
EXPORT int crack_low32_grid(
    uint32_t start,
    uint32_t end,
    uint32_t* r_base,        /* [num_structures * num_offsets] */
    uint32_t* ox,            /* [num_structures * num_offsets] */
    uint32_t* oz,            /* [num_structures * num_offsets] */
    uint32_t* offset_range,  /* [num_structures] */
    int* spread_type,        /* [num_structures] */
    int num_structures,
    int num_offsets,
    uint32_t* results,
    int max_results
) {
    if (!r_base || !ox || !oz || !offset_range || !spread_type || !results) {
        return -1;
    }
    if (num_structures <= 0 || num_offsets <= 0 || max_results <= 0) {
        return -1;
    }
    for (int i = 0; i < num_structures; i++) {
        if (offset_range[i] == 0) {
            return -1;
        }
    }

    int found_count = 0;

    for (uint64_t w_seed = start; w_seed < end && found_count < max_results; w_seed++) {
        uint32_t w = (uint32_t)w_seed;
        int all_match = 1;

        for (int s = 0; s < num_structures && all_match; s++) {
            int structure_matched = 0;
            for (int g = 0; g < num_offsets; g++) {
                int idx = s * num_offsets + g;
                uint32_t r = w + r_base[idx];
                if (check_mt_seed(r, ox[idx], oz[idx], offset_range[s], spread_type[s])) {
                    structure_matched = 1;
                    break;
                }
            }
            if (!structure_matched) {
                all_match = 0;
            }
        }

        if (all_match) {
            results[found_count++] = w;
        }
    }

    return found_count;
}

/* ===== Special structures (per-chunk decoration RNG, low32-only constraints) =====
 *
 * Desert Well and Amethyst Geode use the decoration RNG:
 *   setDecorationSeed(w, cx, cz, salt):
 *     setSeed(w); a = next() = MT(w) out0 >> 1; b = next() = MT(w) out1 >> 1;
 *     ds = (cx*(a|1) + cz*(b|1)) ^ w;                 (uint32 wrap)
 *     ds = ((ds>>2) + (ds<<6) + salt - 1640531527) ^ ds;
 *   then MT(ds) outputs are consumed by nextInt (raw output % n, no shift).
 *
 * Placement (verified against a real seed, docs/special_structures_test.c):
 *   Desert Well (salt -1160484816): nextInt(500)==0, first nextInt(16) is dz,
 *     second is dx (real-game order), anchor=(cx*16+dx, cz*16+dz)
 *   Amethyst Geode (salt 1974035328, 1.18+ rarity 24): nextInt(24)==0,
 *     anchor=(cx*16+4, cz*16+4), fixed, no extra RNG
 *
 * Both checks depend only on the low 32 bits of the world seed (setSeed
 * truncates to uint32). */
#define SP_WELL 0
#define SP_GEODE 1
#define SP_WELL_SALT    3134482480U   /* (uint32_t)(-1160484816) */
#define SP_WELL_RARITY  500U
#define SP_GEODE_SALT   1974035328U
#define SP_GEODE_RARITY 24U           /* 1.18+ (1.17 uses 53) */

/* First two MT(w) outputs >> 1 (fork next()), shared by all special checks
 * of one seed; partial init m[1..398] as in check_mt_seed_linear */
static inline void compute_deco_ab(uint32_t w, uint32_t *a_out, uint32_t *b_out) {
    uint32_t m_prev = w;
    uint32_t m_1 = 0, m_2 = 0, m_397 = 0, m_398 = 0;

    for (int i = 1; i < 399; i++) {
        uint32_t m_curr = (0x6c078965U * (m_prev ^ (m_prev >> 30)) + (uint32_t)i) & 0xFFFFFFFFU;

        if (i == 1) m_1 = m_curr;
        else if (i == 2) m_2 = m_curr;
        else if (i == 397) m_397 = m_curr;
        else if (i == 398) m_398 = m_curr;

        m_prev = m_curr;
    }

    uint32_t y0 = (w & MT_UPPER_MASK) | (m_1 & MT_LOWER_MASK);
    uint32_t val0 = m_397 ^ (y0 >> 1);
    if (y0 & 1) val0 ^= MT_MAGIC;

    uint32_t y1 = (m_1 & MT_UPPER_MASK) | (m_2 & MT_LOWER_MASK);
    uint32_t val1 = m_398 ^ (y1 >> 1);
    if (y1 & 1) val1 ^= MT_MAGIC;

    *a_out = mt_temper(val0) >> 1;
    *b_out = mt_temper(val1) >> 1;
}

/* Decoration seed mixing (setDecorationSeed without the cached a/b look-up) */
static inline uint32_t deco_seed(uint32_t w, int cx, int cz, uint32_t salt, uint32_t a, uint32_t b) {
    uint32_t ds = ((uint32_t)cx * (a | 1u) + (uint32_t)cz * (b | 1u)) ^ w;
    ds = ((ds >> 2) + (ds << 6) + salt - 1640531527U) ^ ds;
    return ds;
}

/* Desert Well: nextInt(500)==0, first nextInt(16) is dz, second is dx.
 * (dx, dz) = expected chunk offset of the well anchor from the user sample. */
static inline int check_special_well(uint32_t ds, int dx, int dz) {
    /* Partial init of MT(ds): m[1..399]; outputs 0,1,2 need m[397..399] */
    uint32_t m_prev = ds;
    uint32_t m_1 = 0, m_2 = 0, m_3 = 0, m_397 = 0, m_398 = 0, m_399 = 0;

    for (int i = 1; i < 400; i++) {
        uint32_t m_curr = (0x6c078965U * (m_prev ^ (m_prev >> 30)) + (uint32_t)i) & 0xFFFFFFFFU;

        if (i == 1) m_1 = m_curr;
        else if (i == 2) m_2 = m_curr;
        else if (i == 3) m_3 = m_curr;
        else if (i == 397) m_397 = m_curr;
        else if (i == 398) m_398 = m_curr;
        else if (i == 399) m_399 = m_curr;

        m_prev = m_curr;
    }

    uint32_t y0 = (ds & MT_UPPER_MASK) | (m_1 & MT_LOWER_MASK);
    uint32_t val0 = m_397 ^ (y0 >> 1);
    if (y0 & 1) val0 ^= MT_MAGIC;
    if ((mt_temper(val0) % SP_WELL_RARITY) != 0) return 0;

    uint32_t y1 = (m_1 & MT_UPPER_MASK) | (m_2 & MT_LOWER_MASK);
    uint32_t val1 = m_398 ^ (y1 >> 1);
    if (y1 & 1) val1 ^= MT_MAGIC;
    if ((mt_temper(val1) % 16U) != (uint32_t)dz) return 0;

    uint32_t y2 = (m_2 & MT_UPPER_MASK) | (m_3 & MT_LOWER_MASK);
    uint32_t val2 = m_399 ^ (y2 >> 1);
    if (y2 & 1) val2 ^= MT_MAGIC;
    if ((mt_temper(val2) % 16U) != (uint32_t)dx) return 0;

    return 1;
}

/* Amethyst Geode (1.18+): nextInt(24)==0; anchor fixed at chunk corner+(4,4) */
static inline int check_special_geode(uint32_t ds) {
    /* Partial init of MT(ds): m[1..397]; output 0 needs m[397] */
    uint32_t m_prev = ds;
    uint32_t m_1 = 0, m_397 = 0;

    for (int i = 1; i < 398; i++) {
        uint32_t m_curr = (0x6c078965U * (m_prev ^ (m_prev >> 30)) + (uint32_t)i) & 0xFFFFFFFFU;

        if (i == 1) m_1 = m_curr;
        else if (i == 397) m_397 = m_curr;

        m_prev = m_curr;
    }

    uint32_t y0 = (ds & MT_UPPER_MASK) | (m_1 & MT_LOWER_MASK);
    uint32_t val0 = m_397 ^ (y0 >> 1);
    if (y0 & 1) val0 ^= MT_MAGIC;

    return (mt_temper(val0) % SP_GEODE_RARITY) == 0;
}

/**
 * Crack low32 with 4-chunk grid regular structures PLUS special decoration
 * structures (desert well / amethyst geode).
 *
 * Regular structures are checked first (cheaper); only seeds passing ALL
 * regular structures are tested against the special structures. With
 * num_structures == 0 this becomes a special-only scan.
 *
 * sp_type[i]: 0 = desert well, 1 = amethyst geode.
 * Wells: (sp_cx, sp_cz) = origin chunk, (sp_dx, sp_dz) = expected anchor
 * offset within the chunk. Geodes: (sp_cx, sp_cz) = origin chunk, sp_dx and
 * sp_dz unused (pass 0). Wells should be listed before geodes (stricter).
 *
 * Returns the number of matching seeds, or -1 on invalid input.
 */
EXPORT int crack_low32_grid_special(
    uint32_t start,
    uint32_t end,
    uint32_t* r_base,        /* [num_structures * num_offsets] */
    uint32_t* ox,            /* [num_structures * num_offsets] */
    uint32_t* oz,            /* [num_structures * num_offsets] */
    uint32_t* offset_range,  /* [num_structures] */
    int* spread_type,        /* [num_structures] */
    int num_structures,
    int num_offsets,
    int* sp_type,            /* [num_special] */
    int* sp_cx,              /* [num_special] */
    int* sp_cz,              /* [num_special] */
    int* sp_dx,              /* [num_special] */
    int* sp_dz,              /* [num_special] */
    int num_special,
    uint32_t* results,
    int max_results
) {
    if (!results || max_results <= 0) {
        return -1;
    }
    if (num_structures < 0 || num_special < 0 || num_structures + num_special <= 0) {
        return -1;
    }
    if (num_structures > 0) {
        if (!r_base || !ox || !oz || !offset_range || !spread_type) {
            return -1;
        }
        if (num_offsets <= 0) {
            return -1;
        }
        for (int i = 0; i < num_structures; i++) {
            if (offset_range[i] == 0) {
                return -1;
            }
        }
    }
    if (num_special > 0) {
        if (!sp_type || !sp_cx || !sp_cz || !sp_dx || !sp_dz) {
            return -1;
        }
        for (int i = 0; i < num_special; i++) {
            if (sp_type[i] != SP_WELL && sp_type[i] != SP_GEODE) {
                return -1;
            }
        }
    }

    int found_count = 0;

    for (uint64_t w_seed = start; w_seed < end && found_count < max_results; w_seed++) {
        uint32_t w = (uint32_t)w_seed;
        int all_match = 1;

        /* Regular structures first (cheaper per check) */
        for (int s = 0; s < num_structures && all_match; s++) {
            int structure_matched = 0;
            for (int g = 0; g < num_offsets; g++) {
                int idx = s * num_offsets + g;
                uint32_t r = w + r_base[idx];
                if (check_mt_seed(r, ox[idx], oz[idx], offset_range[s], spread_type[s])) {
                    structure_matched = 1;
                    break;
                }
            }
            if (!structure_matched) {
                all_match = 0;
            }
        }

        /* Special decoration structures (a/b computed once per seed) */
        if (all_match && num_special > 0) {
            uint32_t a, b;
            compute_deco_ab(w, &a, &b);
            for (int i = 0; i < num_special && all_match; i++) {
                if (sp_type[i] == SP_WELL) {
                    uint32_t ds = deco_seed(w, sp_cx[i], sp_cz[i], SP_WELL_SALT, a, b);
                    if (!check_special_well(ds, sp_dx[i], sp_dz[i])) all_match = 0;
                } else {
                    uint32_t ds = deco_seed(w, sp_cx[i], sp_cz[i], SP_GEODE_SALT, a, b);
                    if (!check_special_geode(ds)) all_match = 0;
                }
            }
        }

        if (all_match) {
            results[found_count++] = w;
        }
    }

    return found_count;
}