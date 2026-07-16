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