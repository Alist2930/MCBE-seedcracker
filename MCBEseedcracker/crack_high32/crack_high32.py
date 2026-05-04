# -*- coding: utf-8 -*-
"""
Minecraft Bedrock High 32-bit Seed Cracker

Usage:
    python crack_high32.py              # Full search
    python crack_high32.py --test       # Test mode (0 ~ 100M)
    python crack_high32.py --start 0 --end 1000000  # Custom range
"""
import ctypes
import time
import sys
import os
import argparse
import multiprocessing as mp
from pathlib import Path

script_dir = Path(__file__).parent.resolve()
dll_path = script_dir / "crack_high32.dll"

os.add_dll_directory(str(script_dir))

BIOME_IDS = {
    'ocean': {'id': 0, 'rarity': {'1.18': 0.06883430, '1.19': 0.07081740, '1.20': 0.06959600, '1.21': 0.06865850}},
    'plains': {'id': 1, 'rarity': {'1.18': 0.10660260, '1.19': 0.10651130, '1.20': 0.10665340, '1.21': 0.10519710}},
    'desert': {'id': 2, 'rarity': {'1.18': 0.02353480, '1.19': 0.02318180, '1.20': 0.02315620, '1.21': 0.02471080}},
    'windswept_hills': {'id': 3, 'rarity': {'1.18': 0.00274980, '1.19': 0.00285080, '1.20': 0.00274630, '1.21': 0.00273670}},
    'forest': {'id': 4, 'rarity': {'1.18': 0.12118830, '1.19': 0.12192850, '1.20': 0.12179220, '1.21': 0.12070520}},
    'taiga': {'id': 5, 'rarity': {'1.18': 0.03464820, '1.19': 0.03443280, '1.20': 0.03502180, '1.21': 0.03414500}},
    'swamp': {'id': 6, 'rarity': {'1.18': 0.01524060, '1.19': 0.01048190, '1.20': 0.00986360, '1.21': 0.00998030}},
    'river': {'id': 7, 'rarity': {'1.18': 0.06208020, '1.19': 0.06204710, '1.20': 0.06197610, '1.21': 0.06173880}},
    'nether_wastes': {'id': 8, 'rarity': {}},
    'the_end': {'id': 9, 'rarity': {}},
    'frozen_ocean': {'id': 10, 'rarity': {'1.18': 0.02302610, '1.19': 0.02255790, '1.20': 0.02238450, '1.21': 0.02269140}},
    'frozen_river': {'id': 11, 'rarity': {'1.18': 0.00841050, '1.19': 0.00832640, '1.20': 0.00839990, '1.21': 0.00823050}},
    'snowy_plains': {'id': 12, 'rarity': {'1.18': 0.02818270, '1.19': 0.02799720, '1.20': 0.02802380, '1.21': 0.02785780}},
    'snowy_mountains': {'id': 13, 'rarity': {}},
    'mushroom_fields': {'id': 14, 'rarity': {'1.18': 0.00145790, '1.19': 0.00140860, '1.20': 0.00142810, '1.21': 0.00141960}},
    'beach': {'id': 16, 'rarity': {'1.18': 0.02664350, '1.19': 0.02673220, '1.20': 0.02674990, '1.21': 0.02673920}},
    'desert_hills': {'id': 17, 'rarity': {}},
    'wooded_hills': {'id': 18, 'rarity': {}},
    'taiga_hills': {'id': 19, 'rarity': {}},
    'jungle': {'id': 21, 'rarity': {'1.18': 0.01898790, '1.19': 0.01908080, '1.20': 0.01906120, '1.21': 0.01901830}},
    'jungle_hills': {'id': 22, 'rarity': {}},
    'sparse_jungle': {'id': 23, 'rarity': {'1.18': 0.01254590, '1.19': 0.01259620, '1.20': 0.01262130, '1.21': 0.01258250}},
    'deep_ocean': {'id': 24, 'rarity': {'1.18': 0.04364550, '1.19': 0.04448230, '1.20': 0.04433620, '1.21': 0.04382860}},
    'stony_shore': {'id': 25, 'rarity': {'1.18': 0.01193090, '1.19': 0.01198030, '1.20': 0.01187230, '1.21': 0.01187870}},
    'snowy_beach': {'id': 26, 'rarity': {'1.18': 0.00352320, '1.19': 0.00351620, '1.20': 0.00353220, '1.21': 0.00353820}},
    'birch_forest': {'id': 27, 'rarity': {'1.18': 0.02153490, '1.19': 0.02157010, '1.20': 0.02147580, '1.21': 0.02141640}},
    'birch_forest_hills': {'id': 28, 'rarity': {}},
    'dark_forest': {'id': 29, 'rarity': {'1.18': 0.02005990, '1.19': 0.02009390, '1.20': 0.02009000, '1.21': 0.02001480}},
    'snowy_taiga': {'id': 30, 'rarity': {'1.18': 0.02569520, '1.19': 0.02571140, '1.20': 0.02564280, '1.21': 0.02563410}},
    'old_growth_pine_taiga': {'id': 32, 'rarity': {'1.18': 0.00682330, '1.19': 0.00682250, '1.20': 0.00685920, '1.21': 0.00677310}},
    'windswept_forest': {'id': 34, 'rarity': {'1.18': 0.00189080, '1.19': 0.00198030, '1.20': 0.00194970, '1.21': 0.00191330}},
    'savanna': {'id': 35, 'rarity': {'1.18': 0.04082720, '1.19': 0.03970920, '1.20': 0.04011960, '1.21': 0.03997160}},
    'savanna_plateau': {'id': 36, 'rarity': {'1.18': 0.00402740, '1.19': 0.00385280, '1.20': 0.00400960, '1.21': 0.00402530}},
    'badlands': {'id': 37, 'rarity': {'1.18': 0.00848480, '1.19': 0.00842020, '1.20': 0.00837960, '1.21': 0.00901250}},
    'wooded_badlands': {'id': 38, 'rarity': {'1.18': 0.00595350, '1.19': 0.00615770, '1.20': 0.00593240, '1.21': 0.00637180}},
    'badlands_plateau': {'id': 39, 'rarity': {}},
    'warm_ocean': {'id': 44, 'rarity': {'1.18': 0.02141150, '1.19': 0.02035970, '1.20': 0.02069320, '1.21': 0.02241260}},
    'lukewarm_ocean': {'id': 45, 'rarity': {'1.18': 0.04549210, '1.19': 0.04430840, '1.20': 0.04502280, '1.21': 0.04607490}},
    'cold_ocean': {'id': 46, 'rarity': {'1.18': 0.04569830, '1.19': 0.04543550, '1.20': 0.04648820, '1.21': 0.04510310}},
    'deep_warm_ocean': {'id': 47, 'rarity': {}},
    'deep_lukewarm_ocean': {'id': 48, 'rarity': {'1.18': 0.02414840, '1.19': 0.02306920, '1.20': 0.02374440, '1.21': 0.02454670}},
    'deep_cold_ocean': {'id': 49, 'rarity': {'1.18': 0.02404640, '1.19': 0.02424240, '1.20': 0.02434420, '1.21': 0.02396680}},
    'deep_frozen_ocean': {'id': 50, 'rarity': {'1.18': 0.01230010, '1.19': 0.01179670, '1.20': 0.01152850, '1.21': 0.01207150}},
    'sunflower_plains': {'id': 129, 'rarity': {'1.18': 0.00677230, '1.19': 0.00666230, '1.20': 0.00663100, '1.21': 0.00663730}},
    'desert_lakes': {'id': 130, 'rarity': {}},
    'windswept_gravelly_hills': {'id': 131, 'rarity': {'1.18': 0.00099090, '1.19': 0.00101740, '1.20': 0.00097430, '1.21': 0.00096950}},
    'flower_forest': {'id': 132, 'rarity': {'1.18': 0.00650960, '1.19': 0.00647790, '1.20': 0.00648900, '1.21': 0.00652940}},
    'ice_spikes': {'id': 140, 'rarity': {'1.18': 0.00221900, '1.19': 0.00216960, '1.20': 0.00236230, '1.21': 0.00231340}},
    'old_growth_birch_forest': {'id': 155, 'rarity': {'1.18': 0.02068730, '1.19': 0.02134130, '1.20': 0.02107020, '1.21': 0.02091630}},
    'old_growth_spruce_taiga': {'id': 160, 'rarity': {'1.18': 0.00682330, '1.19': 0.00682250, '1.20': 0.00685920, '1.21': 0.00677310}},
    'windswept_savanna': {'id': 163, 'rarity': {'1.18': 0.00214110, '1.19': 0.00217620, '1.20': 0.00216400, '1.21': 0.00218520}},
    'eroded_badlands': {'id': 165, 'rarity': {'1.18': 0.00285390, '1.19': 0.00295490, '1.20': 0.00303530, '1.21': 0.00326410}},
    'bamboo_jungle': {'id': 168, 'rarity': {'1.18': 0.00640070, '1.19': 0.00648950, '1.20': 0.00642610, '1.21': 0.00653340}},
    'soul_sand_valley': {'id': 170, 'rarity': {}},
    'crimson_forest': {'id': 171, 'rarity': {}},
    'warped_forest': {'id': 172, 'rarity': {}},
    'basalt_deltas': {'id': 173, 'rarity': {}},
    'dripstone_caves': {'id': 174, 'rarity': {}},
    'lush_caves': {'id': 175, 'rarity': {}},
    'meadow': {'id': 177, 'rarity': {'1.18': 0.01444760, '1.19': 0.01483050, '1.20': 0.01180500, '1.21': 0.01181040}},
    'grove': {'id': 178, 'rarity': {'1.18': 0.00725410, '1.19': 0.00750920, '1.20': 0.00733450, '1.21': 0.00750000}},
    'snowy_slopes': {'id': 179, 'rarity': {'1.18': 0.00389140, '1.19': 0.00386220, '1.20': 0.00382970, '1.21': 0.00389680}},
    'jagged_peaks': {'id': 180, 'rarity': {'1.18': 0.00145390, '1.19': 0.00146290, '1.20': 0.00143470, '1.21': 0.00148760}},
    'frozen_peaks': {'id': 181, 'rarity': {'1.18': 0.00145250, '1.19': 0.00146110, '1.20': 0.00148070, '1.21': 0.00149530}},
    'stony_peaks': {'id': 182, 'rarity': {'1.18': 0.00096520, '1.19': 0.00095350, '1.20': 0.00096540, '1.21': 0.00100140}},
    'deep_dark': {'id': 183, 'rarity': {}},
    'mangrove_swamp': {'id': 184, 'rarity': {'1.18': 1.00000000, '1.19': 0.00514440, '1.20': 0.00503250, '1.21': 0.00522440}},
    'cherry_grove': {'id': 185, 'rarity': {'1.18': 1.00000000, '1.19': 1.00000000, '1.20': 0.00278580, '1.21': 0.00280480}},
    'pale_garden': {'id': 186, 'rarity': {'1.18': 1.00000000, '1.19': 1.00000000, '1.20': 1.00000000, '1.21': 0.00078550}},
}
BIOME_NAMES = {v['id']: k for k, v in BIOME_IDS.items()}

VERSION_BIOMES = {
    '1.18': [174, 175, 177, 178, 179, 180, 181, 182],
    '1.19': [183, 184],
    '1.20': [185],
    '1.21': [186],
}

def get_biome_name(biome_id):
    return BIOME_NAMES.get(biome_id, f"biome_{biome_id}")

def get_biome_rarity(biome_id, mc_version):
    biome_name = BIOME_NAMES.get(biome_id)
    if biome_name and biome_name in BIOME_IDS:
        rarity_dict = BIOME_IDS[biome_name].get('rarity', {})
        if rarity_dict:
            return rarity_dict.get(mc_version, 1.0)
    return 1.0

def sort_samples_by_rarity(samples, mc_version):
    return sorted(samples, key=lambda s: get_biome_rarity(s[2], mc_version))

def get_biome_version(biome_id):
    for version, biome_ids in VERSION_BIOMES.items():
        if biome_id in biome_ids:
            return version
    return '1.17'

def check_biome_version(samples, mc_version):
    version_order = ['1.17', '1.18', '1.19', '1.20', '1.21']
    mc_idx = version_order.index(mc_version) if mc_version in version_order else len(version_order) - 1
    warnings = []
    
    for x, z, biome_id in samples:
        biome_version = get_biome_version(biome_id)
        biome_idx = version_order.index(biome_version)
        if biome_idx > mc_idx:
            biome_name = get_biome_name(biome_id)
            warnings.append(f"  ({x}, {z}) -> {biome_name} (ID: {biome_id}) requires {biome_version}+, but current version is {mc_version}")
    
    return warnings

SAMPLES = [
    (-1922, 1231, 185),   # cherry_grove
    (-4706, 3302, 132),   # flower_forest
    (-935, 2592, 5),      # taiga
    (-2697, 1363, 4),     # forest
    (-270, 470, 186),     # pale_garden
]

LOW32 = 1818588773
Y_COORD = 200

MC_VERSION_STR = "1.21"

MC_1_18 = 22
MC_1_19 = 24
MC_1_20 = 25
MC_1_21 = 28

VERSION_MAP = {
    "1.18": MC_1_18,
    "1.19": MC_1_19,
    "1.20": MC_1_20,
    "1.21": MC_1_21,
}

MC_VERSION = VERSION_MAP.get(MC_VERSION_STR, MC_1_21)

BATCH_SIZE = 500000
MAX_RESULTS = 1000

class BiomeSample(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("z", ctypes.c_int), ("biome_id", ctypes.c_int)]

def init_dll():
    dll = ctypes.CDLL(str(dll_path), winmode=0x00000008)
    
    dll.crack_high32_soa.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int,
        ctypes.POINTER(BiomeSample), ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_int, ctypes.c_int
    ]
    dll.crack_high32_soa.restype = ctypes.c_int
    
    return dll

def crack_batch_soa(args):
    start_high, end_high, low32, samples, y_coord, mc_version = args
    dll = init_dll()
    
    num_samples = len(samples)
    sample_array = (BiomeSample * num_samples)()
    for i, (x, z, biome_id) in enumerate(samples):
        sample_array[i].x = x
        sample_array[i].z = z
        sample_array[i].biome_id = biome_id
    
    results = (ctypes.c_uint64 * MAX_RESULTS)()
    
    found = dll.crack_high32_soa(
        start_high, end_high, low32, y_coord,
        sample_array, num_samples,
        results, MAX_RESULTS, mc_version
    )
    
    return [results[i] for i in range(found)]

def main():
    parser = argparse.ArgumentParser(description='Minecraft Bedrock High 32-bit Seed Cracker')
    parser.add_argument('--start', type=int, default=0, help='Start high value')
    parser.add_argument('--end', type=int, default=0x100000000, help='End high value (exclusive, use 0x100000000 for full range)')
    parser.add_argument('--test', action='store_true', help='Test mode: 0 ~ 100M')
    parser.add_argument('--low32', type=int, default=LOW32, help='Low 32-bit value')
    parser.add_argument('--processes', type=int, default=None, help='Number of processes')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Minecraft Bedrock High 32-bit Seed Cracker")
    print("=" * 60)
    
    search_start = args.start
    search_end = 100000000 if args.test and args.end == 0x100000000 else args.end
    num_processes = args.processes if args.processes else mp.cpu_count()
    
    print(f"\n[*] Low 32-bit: {args.low32}")
    print(f"[*] Y coordinate: {Y_COORD}")
    print(f"[*] MC Version: {MC_VERSION_STR}")
    print(f"[*] Processes: {num_processes}")
    
    sorted_samples = sort_samples_by_rarity(SAMPLES, MC_VERSION_STR)
    
    print(f"\n[*] Biome samples (sorted by rarity, rarest first):")
    for i, (x, z, biome_id) in enumerate(sorted_samples):
        rarity = get_biome_rarity(biome_id, MC_VERSION_STR)
        rarity_pct = rarity * 100
        print(f"    {i+1}. ({x}, {z}) -> {get_biome_name(biome_id)} (ID: {biome_id}, {rarity_pct:.4f}%)")
    
    version_warnings = check_biome_version(sorted_samples, MC_VERSION_STR)
    if version_warnings:
        print(f"\n[!] Warning: Some biomes are not available in MC {MC_VERSION_STR}:")
        for w in version_warnings:
            print(w)
        print("[!] These samples will never match! Please update MC_VERSION_STR or remove these samples.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    total_search = search_end - search_start
    
    print(f"\n[*] Search range: {search_start:,} ~ {search_end:,}")
    print("-" * 60)
    print("[*] Cracking with SOA optimization (4 seeds per batch)...")
    print("-" * 60)
    
    all_results = []
    found_count = 0
    
    start_time = time.time()
    total_done = 0
    batch_size = BATCH_SIZE
    
    pool = mp.Pool(num_processes)
    
    for batch_start in range(search_start, search_end, batch_size * num_processes):
        batch_end = min(batch_start + batch_size * num_processes, search_end)
        
        tasks = []
        chunk = batch_size
        for i in range(num_processes):
            start = batch_start + i * chunk
            end = start + chunk
            if start < batch_end:
                actual_end = min(end, batch_end)
                tasks.append((start, actual_end, args.low32, sorted_samples, Y_COORD, MC_VERSION))
        
        if tasks:
            for r in pool.imap_unordered(crack_batch_soa, tasks):
                if r:
                    for seed in r:
                        all_results.append(seed)
                        found_count += 1
                        print(f"\n[FOUND] Seed: {seed} (0x{seed:016X})")
        
        total_done = batch_end - search_start
        elapsed = time.time() - start_time
        speed = total_done / elapsed if elapsed > 0 else 0
        eta = (total_search - total_done) / speed if speed > 0 else 0
        percent = total_done / total_search * 100
        
        bar_len = 30
        filled = int(bar_len * percent / 100)
        bar = '#' * filled + '-' * (bar_len - filled)
        
        sys.stdout.write(f'\r  [{bar}] {percent:.1f}% | {total_done:,}/{total_search:,} | {speed:,.0f}/s | ETA: {eta/60:.1f}min | Found: {found_count}')
        sys.stdout.flush()
    
    pool.close()
    pool.join()
    
    total_elapsed = time.time() - start_time
    total_speed = total_search / total_elapsed if total_elapsed > 0 else 0
    
    print(f"\n\n[Complete]")
    print(f"  Time: {total_elapsed:.1f}s ({total_elapsed/60:.1f}min)")
    print(f"  Speed: {total_speed:,.0f}/s")
    print(f"  Found: {len(all_results)} seed(s)")
    
    print("\n" + "=" * 60)
    print("Search Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
