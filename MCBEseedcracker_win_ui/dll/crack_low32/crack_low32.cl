/**
 * OpenCL Kernel for Minecraft Bedrock Low 32-bit Seed Cracker
 *
 * Each GPU thread checks a batch of seeds for structure matches.
 */

#define MT_MAGIC 0x9908b0dfU
#define MT_UPPER_MASK 0x80000000U
#define MT_LOWER_MASK 0x7FFFFFFFU

// MT19937 temper function
uint mt_temper(uint y)
{
    y ^= (y >> 11);
    y ^= (y << 7) & 0x9d2c5680U;
    y ^= (y << 15) & 0xefc60000U;
    y ^= (y >> 18);
    return y;
}

// Check MT seed for linear spread type (optimized)
int check_mt_seed_linear(uint r_seed, uint target_ox, uint target_oz, uint offset_range)
{
    uint m_prev = r_seed;
    uint m_1 = 0, m_2 = 0, m_397 = 0, m_398 = 0;

    for (int i = 1; i < 399; i++)
    {
        uint m_curr = (0x6c078965U * (m_prev ^ (m_prev >> 30)) + (uint)i) & 0xFFFFFFFFU;

        if (i == 1)
            m_1 = m_curr;
        else if (i == 2)
            m_2 = m_curr;
        else if (i == 397)
            m_397 = m_curr;
        else if (i == 398)
            m_398 = m_curr;

        m_prev = m_curr;
    }

    uint y0 = (r_seed & MT_UPPER_MASK) | (m_1 & MT_LOWER_MASK);
    uint val0 = m_397 ^ (y0 >> 1);
    if (y0 & 1)
        val0 ^= MT_MAGIC;

    uint t0 = mt_temper(val0);
    if ((t0 % offset_range) != target_ox)
        return 0;

    uint y1 = (m_1 & MT_UPPER_MASK) | (m_2 & MT_LOWER_MASK);
    uint val1 = m_398 ^ (y1 >> 1);
    if (y1 & 1)
        val1 ^= MT_MAGIC;

    uint t1 = mt_temper(val1);
    if ((t1 % offset_range) != target_oz)
        return 0;

    return 1;
}

// Check MT seed for triangular spread type
int check_mt_seed_triangular(uint r_seed, uint target_ox, uint target_oz, uint offset_range)
{
    uint mt[624];
    mt[0] = r_seed;

    for (int i = 1; i < 624; i++)
    {
        mt[i] = (0x6c078965U * (mt[i - 1] ^ (mt[i - 1] >> 30)) + (uint)i) & 0xFFFFFFFFU;
    }

    for (int i = 0; i < 227; i++)
    {
        uint y = (mt[i] & MT_UPPER_MASK) | (mt[i + 1] & MT_LOWER_MASK);
        mt[i] = mt[i + 397] ^ (y >> 1);
        if (y & 1)
            mt[i] ^= MT_MAGIC;
    }

    for (int i = 227; i < 623; i++)
    {
        uint y = (mt[i] & MT_UPPER_MASK) | (mt[i + 1] & MT_LOWER_MASK);
        mt[i] = mt[i - 227] ^ (y >> 1);
        if (y & 1)
            mt[i] ^= MT_MAGIC;
    }

    uint y623 = (mt[623] & MT_UPPER_MASK) | (mt[0] & MT_LOWER_MASK);
    mt[623] = mt[396] ^ (y623 >> 1);
    if (y623 & 1)
        mt[623] ^= MT_MAGIC;

    uint t0 = mt_temper(mt[0]);
    uint t1 = mt_temper(mt[1]);
    uint t2 = mt_temper(mt[2]);
    uint t3 = mt_temper(mt[3]);

    uint ox = (t0 % offset_range + t1 % offset_range) / 2;
    uint oz = (t2 % offset_range + t3 % offset_range) / 2;

    if (ox != target_ox || oz != target_oz)
        return 0;

    return 1;
}

// Check MT seed based on spread type
int check_mt_seed(uint r_seed, uint target_ox, uint target_oz, uint offset_range, int spread_type)
{
    if (spread_type == 1)
    {
        return check_mt_seed_triangular(r_seed, target_ox, target_oz, offset_range);
    }
    else
    {
        return check_mt_seed_linear(r_seed, target_ox, target_oz, offset_range);
    }
}

/**
 * Main kernel: Check seeds in parallel
 *
 * Each GPU thread checks 'seeds_per_thread' consecutive seeds.
 * Matching seeds are written to results buffer using atomic counter.
 */
__kernel void crack_low32_kernel(
    __global uint *results,          // Output: matching seeds
    __global uint *result_count,     // Output: atomic counter for results
    const uint start_seed,           // Start seed value
    const uint end_seed,             // End seed value (inclusive)
    const uint seeds_per_thread,     // Number of seeds each thread checks
    __global const uint *r_base,     // Structure r_base values
    __global const uint *ox,         // Structure ox values
    __global const uint *oz,         // Structure oz values
    __global const uint *offset_range, // Structure offset_range values
    __global const int *spread_type, // Structure spread_type values
    const uint num_targets,          // Number of structures
    const uint max_results           // Maximum results to store
)
{
    uint gid = get_global_id(0);
    uint thread_start = start_seed + gid * seeds_per_thread;

    // Boundary check - handle wrap-around for full 2^32 range
    if (start_seed <= end_seed)
    {
        // Normal case: start <= end
        if (thread_start > end_seed || thread_start < start_seed)
            return;
    }
    else
    {
        // Wrap-around case: start > end (shouldn't happen in practice)
        return;
    }

    // Check seeds_per_thread seeds
    for (uint i = 0; i < seeds_per_thread; i++)
    {
        uint seed = thread_start + i;

        // Boundary check for seed
        if (seed > end_seed)
            break;

        // Check first structure
        uint r0 = seed + r_base[0];
        if (check_mt_seed(r0, ox[0], oz[0], offset_range[0], spread_type[0]))
        {
            int all_match = 1;

            // Check remaining structures
            for (uint j = 1; j < num_targets; j++)
            {
                uint rn = seed + r_base[j];
                if (!check_mt_seed(rn, ox[j], oz[j], offset_range[j], spread_type[j]))
                {
                    all_match = 0;
                    break;
                }
            }

            // All structures match - add to results
            if (all_match)
            {
                uint idx = atomic_inc(result_count);
                if (idx < max_results)
                {
                    results[idx] = seed;
                }
            }
        }
    }
}

/**
 * Grid kernel: Check seeds with 4-chunk grid offset support.
 * For each structure, checks num_offsets possible (r_base, ox, oz) combinations.
 * A seed is valid if each structure matches at least one of its offsets.
 *
 * Array layout: r_base/ox/oz are [num_structures * num_offsets] (flattened by structure then offset).
 * offset_range/spread_type are [num_structures] (shared across offsets of same structure).
 */
__kernel void crack_low32_grid_kernel(
    __global uint *results,
    __global uint *result_count,
    const uint start_seed,
    const uint end_seed,
    const uint seeds_per_thread,
    __global const uint *r_base,        // [num_structures * num_offsets]
    __global const uint *ox,            // [num_structures * num_offsets]
    __global const uint *oz,            // [num_structures * num_offsets]
    __global const uint *offset_range,  // [num_structures]
    __global const int *spread_type,    // [num_structures]
    const uint num_structures,
    const uint num_offsets,
    const uint max_results
)
{
    uint gid = get_global_id(0);
    uint thread_start = start_seed + gid * seeds_per_thread;

    if (start_seed <= end_seed)
    {
        if (thread_start > end_seed || thread_start < start_seed)
            return;
    }
    else
    {
        return;
    }

    for (uint i = 0; i < seeds_per_thread; i++)
    {
        uint seed = thread_start + i;
        if (seed > end_seed)
            break;

        int all_match = 1;

        for (uint s = 0; s < num_structures; s++)
        {
            if (!all_match)
                break;

            int structure_matched = 0;
            for (uint g = 0; g < num_offsets; g++)
            {
                uint idx = s * num_offsets + g;
                uint r = seed + r_base[idx];
                if (check_mt_seed(r, ox[idx], oz[idx], offset_range[s], spread_type[s]))
                {
                    structure_matched = 1;
                    break;
                }
            }
            if (!structure_matched)
            {
                all_match = 0;
            }
        }

        if (all_match)
        {
            uint idx = atomic_inc(result_count);
            if (idx < max_results)
            {
                results[idx] = seed;
            }
        }
    }
}

/* ===== Special decoration structures (desert well / amethyst geode) =====
 *
 * Decoration RNG (verified against a real seed, docs/special_structures_test.c):
 *   a = MT(w) out0 >> 1, b = MT(w) out1 >> 1 (fork next());
 *   ds = (cx*(a|1) + cz*(b|1)) ^ w;
 *   ds = ((ds>>2) + (ds<<6) + salt - 1640531527) ^ ds;   (uint32 wrap)
 *   nextInt(n) = raw MT(ds) output % n (no shift).
 * Desert Well: nextInt(500)==0, first nextInt(16) is dz, second is dx.
 * Amethyst Geode (1.18+): nextInt(24)==0, anchor fixed at chunk corner+(4,4).
 */

#define SP_WELL 0
#define SP_GEODE 1
#define SP_WELL_SALT 3134482480U   /* (uint32_t)(-1160484816) */
#define SP_WELL_RARITY 500U
#define SP_GEODE_SALT 1974035328U
#define SP_GEODE_RARITY 24U

// First two MT(w) outputs >> 1, shared by all special checks of one seed
void compute_deco_ab(uint w, uint *a_out, uint *b_out)
{
    uint m_prev = w;
    uint m_1 = 0, m_2 = 0, m_397 = 0, m_398 = 0;

    for (int i = 1; i < 399; i++)
    {
        uint m_curr = (0x6c078965U * (m_prev ^ (m_prev >> 30)) + (uint)i) & 0xFFFFFFFFU;

        if (i == 1) m_1 = m_curr;
        else if (i == 2) m_2 = m_curr;
        else if (i == 397) m_397 = m_curr;
        else if (i == 398) m_398 = m_curr;

        m_prev = m_curr;
    }

    uint y0 = (w & MT_UPPER_MASK) | (m_1 & MT_LOWER_MASK);
    uint val0 = m_397 ^ (y0 >> 1);
    if (y0 & 1) val0 ^= MT_MAGIC;

    uint y1 = (m_1 & MT_UPPER_MASK) | (m_2 & MT_LOWER_MASK);
    uint val1 = m_398 ^ (y1 >> 1);
    if (y1 & 1) val1 ^= MT_MAGIC;

    *a_out = mt_temper(val0) >> 1;
    *b_out = mt_temper(val1) >> 1;
}

uint deco_seed(uint w, int cx, int cz, uint salt, uint a, uint b)
{
    uint ds = ((uint)cx * (a | 1u) + (uint)cz * (b | 1u)) ^ w;
    ds = ((ds >> 2) + (ds << 6) + salt - 1640531527U) ^ ds;
    return ds;
}

// Desert Well: nextInt(500)==0, first nextInt(16) is dz, second is dx
int check_special_well(uint ds, int dx, int dz)
{
    uint m_prev = ds;
    uint m_1 = 0, m_2 = 0, m_3 = 0, m_397 = 0, m_398 = 0, m_399 = 0;

    for (int i = 1; i < 400; i++)
    {
        uint m_curr = (0x6c078965U * (m_prev ^ (m_prev >> 30)) + (uint)i) & 0xFFFFFFFFU;

        if (i == 1) m_1 = m_curr;
        else if (i == 2) m_2 = m_curr;
        else if (i == 3) m_3 = m_curr;
        else if (i == 397) m_397 = m_curr;
        else if (i == 398) m_398 = m_curr;
        else if (i == 399) m_399 = m_curr;

        m_prev = m_curr;
    }

    uint y0 = (ds & MT_UPPER_MASK) | (m_1 & MT_LOWER_MASK);
    uint val0 = m_397 ^ (y0 >> 1);
    if (y0 & 1) val0 ^= MT_MAGIC;
    if ((mt_temper(val0) % SP_WELL_RARITY) != 0) return 0;

    uint y1 = (m_1 & MT_UPPER_MASK) | (m_2 & MT_LOWER_MASK);
    uint val1 = m_398 ^ (y1 >> 1);
    if (y1 & 1) val1 ^= MT_MAGIC;
    if ((mt_temper(val1) % 16U) != (uint)dz) return 0;

    uint y2 = (m_2 & MT_UPPER_MASK) | (m_3 & MT_LOWER_MASK);
    uint val2 = m_399 ^ (y2 >> 1);
    if (y2 & 1) val2 ^= MT_MAGIC;
    if ((mt_temper(val2) % 16U) != (uint)dx) return 0;

    return 1;
}

// Amethyst Geode (1.18+): nextInt(24)==0
int check_special_geode(uint ds)
{
    uint m_prev = ds;
    uint m_1 = 0, m_397 = 0;

    for (int i = 1; i < 398; i++)
    {
        uint m_curr = (0x6c078965U * (m_prev ^ (m_prev >> 30)) + (uint)i) & 0xFFFFFFFFU;

        if (i == 1) m_1 = m_curr;
        else if (i == 397) m_397 = m_curr;

        m_prev = m_curr;
    }

    uint y0 = (ds & MT_UPPER_MASK) | (m_1 & MT_LOWER_MASK);
    uint val0 = m_397 ^ (y0 >> 1);
    if (y0 & 1) val0 ^= MT_MAGIC;

    return (mt_temper(val0) % SP_GEODE_RARITY) == 0;
}

/**
 * Grid + special kernel: regular 4-chunk grid structures checked first, then
 * special decoration structures. num_structures may be 0 (special-only scan).
 *
 * Array layout: r_base/ox/oz are [num_structures * num_offsets] (flattened by
 * structure then offset); offset_range/spread_type are [num_structures];
 * sp_* arrays are [num_special].
 */
__kernel void crack_low32_grid_special_kernel(
    __global uint *results,
    __global uint *result_count,
    const uint start_seed,
    const uint end_seed,
    const uint seeds_per_thread,
    __global const uint *r_base,        // [num_structures * num_offsets]
    __global const uint *ox,            // [num_structures * num_offsets]
    __global const uint *oz,            // [num_structures * num_offsets]
    __global const uint *offset_range,  // [num_structures]
    __global const int *spread_type,    // [num_structures]
    const uint num_structures,
    const uint num_offsets,
    __global const int *sp_type,        // [num_special] 0=well, 1=geode
    __global const int *sp_cx,          // [num_special]
    __global const int *sp_cz,          // [num_special]
    __global const int *sp_dx,          // [num_special]
    __global const int *sp_dz,          // [num_special]
    const uint num_special,
    const uint max_results
)
{
    uint gid = get_global_id(0);
    uint thread_start = start_seed + gid * seeds_per_thread;

    if (start_seed <= end_seed)
    {
        if (thread_start > end_seed || thread_start < start_seed)
            return;
    }
    else
    {
        return;
    }

    for (uint i = 0; i < seeds_per_thread; i++)
    {
        uint seed = thread_start + i;
        if (seed > end_seed)
            break;

        int all_match = 1;

        // Regular structures first (cheaper per check)
        for (uint s = 0; s < num_structures && all_match; s++)
        {
            int structure_matched = 0;
            for (uint g = 0; g < num_offsets; g++)
            {
                uint idx = s * num_offsets + g;
                uint r = seed + r_base[idx];
                if (check_mt_seed(r, ox[idx], oz[idx], offset_range[s], spread_type[s]))
                {
                    structure_matched = 1;
                    break;
                }
            }
            if (!structure_matched)
            {
                all_match = 0;
            }
        }

        // Special decoration structures (a/b computed once per seed)
        if (all_match && num_special > 0)
        {
            uint a, b;
            compute_deco_ab(seed, &a, &b);
            for (uint j = 0; j < num_special && all_match; j++)
            {
                if (sp_type[j] == SP_WELL)
                {
                    uint ds = deco_seed(seed, sp_cx[j], sp_cz[j], SP_WELL_SALT, a, b);
                    if (!check_special_well(ds, sp_dx[j], sp_dz[j]))
                        all_match = 0;
                }
                else
                {
                    uint ds = deco_seed(seed, sp_cx[j], sp_cz[j], SP_GEODE_SALT, a, b);
                    if (!check_special_geode(ds))
                        all_match = 0;
                }
            }
        }

        if (all_match)
        {
            uint idx = atomic_inc(result_count);
            if (idx < max_results)
            {
                results[idx] = seed;
            }
        }
    }
}