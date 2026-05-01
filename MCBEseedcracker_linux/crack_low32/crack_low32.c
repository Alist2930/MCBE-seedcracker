/**
 * Minecraft Bedrock Low 32-bit Seed Cracker
 * 
 * Compile:
 *   gcc -O3 -fPIC -shared -o crack_low32.so crack_low32.c
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
    int32_t* results,
    int max_results
) {
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
                results[found_count++] = (int32_t)w;
            }
        }
    }
    
    return found_count;
}
