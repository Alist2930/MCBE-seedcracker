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
    'ocean':               {'id': 0,   'rarity': 0.08384000},
    'plains':              {'id': 1,   'rarity': 0.10468000},
    'desert':              {'id': 2,   'rarity': 0.01468000},
    'windswept_hills':     {'id': 3,   'rarity': 0.00284800},
    'forest':              {'id': 4,   'rarity': 0.11568000},
    'taiga':               {'id': 5,   'rarity': 0.03476000},
    'swamp':               {'id': 6,   'rarity': 0.01084000},
    'river':               {'id': 7,   'rarity': 0.06892000},
    'nether_wastes':       {'id': 8,   'rarity': 1.0},
    'the_end':             {'id': 9,   'rarity': 1.0},
    'frozen_ocean':        {'id': 10,  'rarity': 0.02066000},
    'frozen_river':        {'id': 11,  'rarity': 0.00750800},
    'snowy_plains':        {'id': 12,  'rarity': 0.02428000},
    'snowy_mountains':     {'id': 13,  'rarity': 1.0},
    'mushroom_fields':     {'id': 14,  'rarity': 0.00157600},
    'beach':               {'id': 16,  'rarity': 0.02696000},
    'desert_hills':        {'id': 17,  'rarity': 1.0},
    'wooded_hills':        {'id': 18,  'rarity': 1.0},
    'taiga_hills':         {'id': 19,  'rarity': 1.0},
    'jungle':              {'id': 21,  'rarity': 0.02064000},
    'jungle_hills':        {'id': 22,  'rarity': 1.0},
    'sparse_jungle':       {'id': 23,  'rarity': 0.01413600},
    'deep_ocean':          {'id': 24,  'rarity': 0.04396000},
    'stony_shore':         {'id': 25,  'rarity': 0.01194000},
    'snowy_beach':         {'id': 26,  'rarity': 0.00310000},
    'birch_forest':        {'id': 27,  'rarity': 0.02136000},
    'birch_forest_hills':  {'id': 28,  'rarity': 1.0},
    'dark_forest':         {'id': 29,  'rarity': 0.02018000},
    'snowy_taiga':         {'id': 30,  'rarity': 0.02584000},
    'old_growth_pine_taiga':       {'id': 32, 'rarity': 0.00699600},
    'windswept_forest':           {'id': 34, 'rarity': 0.00207600},
    'savanna':                    {'id': 35, 'rarity': 0.03308000},
    'savanna_plateau':            {'id': 36, 'rarity': 0.00374800},
    'badlands':                   {'id': 37, 'rarity': 0.01118000},
    'wooded_badlands':            {'id': 38, 'rarity': 0.00722000},
    'badlands_plateau':           {'id': 39, 'rarity': 1.0},
    'warm_ocean':                 {'id': 44, 'rarity': 0.01524000},
    'lukewarm_ocean':             {'id': 45, 'rarity': 0.04228000},
    'cold_ocean':                 {'id': 46, 'rarity': 0.05820000},
    'deep_warm_ocean':            {'id': 47, 'rarity': 1.0},
    'deep_lukewarm_ocean':        {'id': 48, 'rarity': 0.01916000},
    'deep_cold_ocean':            {'id': 49, 'rarity': 0.04144000},
    'deep_frozen_ocean':          {'id': 50, 'rarity': 0.01010000},
    'sunflower_plains':           {'id': 129, 'rarity': 0.00690000},
    'desert_lakes':               {'id': 130, 'rarity': 1.0},
    'windswept_gravelly_hills':   {'id': 131, 'rarity': 0.00104000},
    'flower_forest':              {'id': 132, 'rarity': 0.00648800},
    'ice_spikes':                 {'id': 140, 'rarity': 0.00208000},
    'old_growth_birch_forest':    {'id': 155, 'rarity': 0.01998000},
    'old_growth_spruce_taiga':    {'id': 160, 'rarity': 0.00606800},
    'windswept_savanna':          {'id': 163, 'rarity': 0.00232400},
    'eroded_badlands':            {'id': 165, 'rarity': 0.00425600},
    'bamboo_jungle':              {'id': 168, 'rarity': 0.00745200},
    'soul_sand_valley':           {'id': 170, 'rarity': 1.0},
    'crimson_forest':             {'id': 171, 'rarity': 1.0},
    'warped_forest':              {'id': 172, 'rarity': 1.0},
    'basalt_deltas':              {'id': 173, 'rarity': 1.0},
    'dripstone_caves':            {'id': 174, 'rarity': 1.0},
    'lush_caves':                 {'id': 175, 'rarity': 1.0},
    'meadow':                     {'id': 177, 'rarity': 0.01149200},
    'grove':                      {'id': 178, 'rarity': 0.00661600},
    'snowy_slopes':               {'id': 179, 'rarity': 0.00345200},
    'jagged_peaks':               {'id': 180, 'rarity': 0.00139600},
    'frozen_peaks':               {'id': 181, 'rarity': 0.00142800},
    'stony_peaks':                {'id': 182, 'rarity': 0.00105600},
    'deep_dark':                  {'id': 183, 'rarity': 1.0},
    'mangrove_swamp':             {'id': 184, 'rarity': 0.00612400},
    'cherry_grove':               {'id': 185, 'rarity': 0.00255200},
    'pale_garden':                {'id': 186, 'rarity': 0.00072400},
}
BIOME_NAMES = {v['id']: k for k, v in BIOME_IDS.items()}
BIOME_RARITIES = {v['id']: v['rarity'] for v in BIOME_IDS.values()}

VERSION_BIOMES = {
    '1.18': [174, 175, 177, 178, 179, 180, 181, 182],
    '1.19': [183, 184],
    '1.20': [185],
    '1.21': [186],
}

def get_biome_name(biome_id):
    return BIOME_NAMES.get(biome_id, f"biome_{biome_id}")

def get_biome_rarity(biome_id):
    return BIOME_RARITIES.get(biome_id, 1.0)

def sort_samples_by_rarity(samples):
    return sorted(samples, key=lambda s: get_biome_rarity(s[2]))

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
            warnings.append(f"  ({x}, {z}) -> {biome_name} (ID: {biome_id}) 需要 {biome_version}+，但当前版本是 {mc_version}")
    
    return warnings

SAMPLES = [
    (-1922, 1231, 185),   # cherry_grove
    (-4706, 3302, 132),   # flower_forest
    (-935, 2592, 5),      # taiga
    (-2697, 1363, 4),     # forest
    (-270, 470, 186),     # pale_garden
]

# ===== 在这里填写低32位值（来自 crack_low32 结果）=====
LOW32 = 1818588773
Y_COORD = 150

# ===== MC版本设置 =====
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

class BiomeSample(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("z", ctypes.c_int), ("biome_id", ctypes.c_int)]

def init_dll():
    dll = ctypes.CDLL(str(dll_path))
    
    dll.phase1_filter_avx2.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int,
        ctypes.POINTER(BiomeSample), ctypes.POINTER(ctypes.c_uint64), ctypes.c_int, ctypes.c_int
    ]
    dll.phase1_filter_avx2.restype = ctypes.c_int
    
    dll.phase2_verify.argtypes = [
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_int, ctypes.c_uint32, ctypes.c_int,
        ctypes.POINTER(BiomeSample), ctypes.c_int, ctypes.POINTER(ctypes.c_uint64), ctypes.c_int, ctypes.c_int
    ]
    dll.phase2_verify.restype = ctypes.c_int
    
    return dll

def phase1_batch(args):
    start_high, end_high, low32, rare_sample, y_coord, mc_version = args
    dll = init_dll()
    
    rare = BiomeSample(rare_sample[0], rare_sample[1], rare_sample[2])
    max_candidates = (end_high - start_high) // 10 + 100
    candidates_arr = (ctypes.c_uint64 * max_candidates)()
    
    found = dll.phase1_filter_avx2(start_high, end_high, low32, y_coord, ctypes.byref(rare), candidates_arr, max_candidates, mc_version)
    return [candidates_arr[i] for i in range(found)]

def phase2_batch(args):
    candidates_chunk, low32, other_samples, y_coord, mc_version = args
    dll = init_dll()
    
    candidates_arr = (ctypes.c_uint64 * len(candidates_chunk))(*candidates_chunk)
    other_arr = (BiomeSample * len(other_samples))(*[BiomeSample(x, z, bid) for x, z, bid in other_samples])
    results_arr = (ctypes.c_uint64 * 1000)()
    
    found = dll.phase2_verify(candidates_arr, len(candidates_chunk), low32, y_coord, other_arr, len(other_samples), results_arr, 1000, mc_version)
    return [results_arr[i] for i in range(found)]

def main():
    parser = argparse.ArgumentParser(description='Minecraft Bedrock High 32-bit Seed Cracker')
    parser.add_argument('--start', type=int, default=0, help='Start high value')
    parser.add_argument('--end', type=int, default=0xFFFFFFFF, help='End high value')
    parser.add_argument('--test', action='store_true', help='Test mode: 0 ~ 100M')
    parser.add_argument('--low32', type=int, default=LOW32, help='Low 32-bit value')
    parser.add_argument('--processes', type=int, default=None, help='Number of processes')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Minecraft Bedrock High 32-bit Seed Cracker")
    print("=" * 60)
    
    search_start = args.start
    search_end = 100000000 if args.test and args.end == 0xFFFFFFFF else args.end
    num_processes = args.processes if args.processes else mp.cpu_count()
    
    print(f"\n[*] Low 32-bit: {args.low32}")
    print(f"[*] Y coordinate: {Y_COORD}")
    print(f"[*] MC Version: {MC_VERSION_STR}")
    print(f"[*] Processes: {num_processes}")
    
    sorted_samples = sort_samples_by_rarity(SAMPLES)
    
    print(f"\n[*] Biome samples (sorted by rarity, rarest first):")
    for i, (x, z, biome_id) in enumerate(sorted_samples):
        rarity = get_biome_rarity(biome_id)
        rarity_pct = rarity * 100
        print(f"    {i+1}. ({x}, {z}) -> {get_biome_name(biome_id)} (ID: {biome_id}, {rarity_pct:.4f}%)")
    
    version_warnings = check_biome_version(sorted_samples, MC_VERSION_STR)
    if version_warnings:
        print(f"\n[!] Warning: Some biomes are not available in MC {MC_VERSION_STR}:")
        for w in version_warnings:
            print(w)
        print("[!] These samples will never match! Please update MC_VERSION_STR or remove these samples.")
    
    rare_sample = sorted_samples[0]
    other_samples = sorted_samples[1:]
    total_search = search_end - search_start
    
    print(f"\n[*] Search range: {search_start:,} ~ {search_end:,}")
    
    print("-" * 60)
    print(f"[Phase 1] Filtering with {get_biome_name(rare_sample[2])}...")
    print("-" * 60)
    
    all_candidates = []
    phase1_start = time.time()
    total_done = 0
    batch_size = BATCH_SIZE * num_processes
    
    pool = mp.Pool(num_processes)
    
    for batch_start in range(search_start, search_end, batch_size):
        batch_end = min(batch_start + batch_size, search_end)
        
        tasks = []
        chunk = (batch_end - batch_start) // num_processes
        for i in range(num_processes):
            start = batch_start + i * chunk
            end = batch_start + (i + 1) * chunk if i < num_processes - 1 else batch_end
            if start < end:
                tasks.append((start, end, args.low32, rare_sample, Y_COORD, MC_VERSION))
        
        if tasks:
            results = pool.map(phase1_batch, tasks)
            for r in results:
                all_candidates.extend(r)
        
        total_done = batch_end - search_start
        elapsed = time.time() - phase1_start
        speed = total_done / elapsed if elapsed > 0 else 0
        eta = (total_search - total_done) / speed if speed > 0 else 0
        percent = total_done / total_search * 100
        
        bar_len = 30
        filled = int(bar_len * percent / 100)
        bar = '#' * filled + '-' * (bar_len - filled)
        
        sys.stdout.write(f'\r  [{bar}] {percent:.1f}% | {total_done:,}/{total_search:,} | {speed:,.0f}/s | ETA: {eta/60:.1f}min')
        sys.stdout.flush()
    
    pool.close()
    pool.join()
    
    phase1_elapsed = time.time() - phase1_start
    phase1_speed = total_search / phase1_elapsed if phase1_elapsed > 0 else 0
    
    print(f"\n\n[Phase 1 Complete]")
    print(f"  Time: {phase1_elapsed:.1f}s")
    print(f"  Speed: {phase1_speed:,.0f}/s")
    print(f"  Candidates: {len(all_candidates):,} ({len(all_candidates)/total_search*100:.4f}%)")
    
    if not all_candidates:
        print("\nNo candidates found. Search ended.")
        return
    
    print("-" * 60)
    print(f"[Phase 2] Verifying {len(all_candidates):,} candidates...")
    print(f"  Verification order (rarest first):")
    for i, (x, z, biome_id) in enumerate(other_samples):
        print(f"    {i+1}. ({x}, {z}) -> {get_biome_name(biome_id)} (ID: {biome_id}, {get_biome_rarity(biome_id)*100:.4f}%)")
    print("-" * 60)
    
    phase2_start = time.time()
    
    batch_size = max(1, len(all_candidates) // num_processes)
    tasks = []
    for i in range(num_processes):
        start_idx = i * batch_size
        end_idx = start_idx + batch_size if i < num_processes - 1 else len(all_candidates)
        if start_idx < len(all_candidates):
            tasks.append((all_candidates[start_idx:end_idx], args.low32, other_samples, Y_COORD, MC_VERSION))
    
    pool = mp.Pool(num_processes)
    all_results = []
    total_tasks = len(tasks)
    completed_tasks = 0
    
    for result in pool.imap_unordered(phase2_batch, tasks):
        all_results.extend(result)
        completed_tasks += 1
        elapsed = time.time() - phase2_start
        speed = len(all_candidates) * completed_tasks / total_tasks / elapsed if elapsed > 0 else 0
        percent = completed_tasks / total_tasks * 100
        
        bar_len = 30
        filled = int(bar_len * percent / 100)
        bar = '#' * filled + '-' * (bar_len - filled)
        
        sys.stdout.write(f'\r  [{bar}] {percent:.1f}% | {completed_tasks}/{total_tasks} batches | {speed:,.0f}/s | Found: {len(all_results)}')
        sys.stdout.flush()
    
    pool.close()
    pool.join()
    
    phase2_elapsed = time.time() - phase2_start
    phase2_speed = len(all_candidates) / phase2_elapsed if phase2_elapsed > 0 else 0
    
    print(f"\n\n[Phase 2 Complete]")
    print(f"  Time: {phase2_elapsed:.1f}s")
    print(f"  Speed: {phase2_speed:,.0f} candidates/s")
    print(f"  Matches: {len(all_results)}")
    
    total_elapsed = phase1_elapsed + phase2_elapsed
    
    print("\n" + "=" * 60)
    print("Search Complete!")
    print("=" * 60)
    print(f"\n[*] Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f}min)")
    print(f"[*] Found {len(all_results)} matching seed(s)")
    
    if all_results:
        print("\n[*] All matching full seeds:")
        for seed in all_results:
            high32 = seed >> 32
            low32 = seed & 0xFFFFFFFF
            print(f"    Seed: {seed}")
            print(f"    High 32-bit: {high32}")
            print(f"    Low 32-bit: {low32}")
            print()

if __name__ == "__main__":
    main()
