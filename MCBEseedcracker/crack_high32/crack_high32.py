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
    'ocean': 0, 'plains': 1, 'desert': 2, 'windswept_hills': 3,
    'forest': 4, 'taiga': 5, 'swamp': 6, 'river': 7, 'nether_wastes': 8,
    'the_end': 9, 'frozen_ocean': 10, 'frozen_river': 11, 'snowy_plains': 12,
    'snowy_mountains': 13, 'mushroom_fields': 14, 'beach': 16, 'desert_hills': 17,
    'wooded_hills': 18, 'taiga_hills': 19, 'jungle': 21, 'jungle_hills': 22,
    'sparse_jungle': 23, 'deep_ocean': 24, 'stony_shore': 25, 'snowy_beach': 26,
    'birch_forest': 27, 'birch_forest_hills': 28, 'dark_forest': 29, 'snowy_taiga': 30,
    'old_growth_pine_taiga': 32, 'windswept_forest': 34, 'savanna': 35,
    'savanna_plateau': 36, 'badlands': 37, 'wooded_badlands': 38, 'badlands_plateau': 39,
    'warm_ocean': 44, 'lukewarm_ocean': 45, 'cold_ocean': 46, 'deep_warm_ocean': 47,
    'deep_lukewarm_ocean': 48, 'deep_cold_ocean': 49, 'deep_frozen_ocean': 50,
    'sunflower_plains': 129, 'desert_lakes': 130, 'windswept_gravelly_hills': 131,
    'flower_forest': 132, 'ice_spikes': 140, 'old_growth_birch_forest': 155,
    'old_growth_spruce_taiga': 160, 'windswept_savanna': 163, 'eroded_badlands': 165,
    'bamboo_jungle': 168, 'soul_sand_valley': 170, 'crimson_forest': 171,
    'warped_forest': 172, 'basalt_deltas': 173, 'dripstone_caves': 174, 'lush_caves': 175,
    'meadow': 177, 'grove': 178, 'snowy_slopes': 179, 'jagged_peaks': 180,
    'frozen_peaks': 181, 'stony_peaks': 182, 'deep_dark': 183, 'mangrove_swamp': 184,
    'cherry_grove': 185, 'pale_garden': 186,
}
BIOME_NAMES = {v: k for k, v in BIOME_IDS.items()}

VERSION_BIOMES = {
    '1.18': [174, 175, 177, 178, 179, 180, 181, 182],
    '1.19': [183, 184],
    '1.20': [185],
    '1.21': [186],
}

def get_biome_name(biome_id):
    return BIOME_NAMES.get(biome_id, f"biome_{biome_id}")

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
    (-1922, 1231, 185),
    (-4706, 3302, 132),
    (-935, 2592, 5),
    (-2697, 1363, 4),
    (-270, 470, 186),
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
    parser.add_argument('--processes', type=int, default=2, help='Number of processes')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Minecraft Bedrock High 32-bit Seed Cracker")
    print("=" * 60)
    
    search_start = args.start
    search_end = 100000000 if args.test else args.end
    num_processes = args.processes if args.processes else mp.cpu_count()
    
    print(f"\n[*] Low 32-bit: {args.low32}")
    print(f"[*] Y coordinate: {Y_COORD}")
    print(f"[*] MC Version: {MC_VERSION_STR}")
    print(f"[*] Processes: {num_processes}")
    
    print(f"\n[*] Biome samples:")
    for i, (x, z, biome_id) in enumerate(SAMPLES):
        print(f"    {i+1}. ({x}, {z}) -> {get_biome_name(biome_id)} (ID: {biome_id})")
    
    version_warnings = check_biome_version(SAMPLES, MC_VERSION_STR)
    if version_warnings:
        print(f"\n[!] Warning: Some biomes are not available in MC {MC_VERSION_STR}:")
        for w in version_warnings:
            print(w)
        print("[!] These samples will never match! Please update MC_VERSION_STR or remove these samples.")
    
    rare_sample = SAMPLES[0]
    other_samples = SAMPLES[1:]
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
    results = pool.map(phase2_batch, tasks)
    pool.close()
    pool.join()
    
    phase2_elapsed = time.time() - phase2_start
    
    all_results = []
    for r in results:
        all_results.extend(r)
    
    phase2_speed = len(all_candidates) / phase2_elapsed if phase2_elapsed > 0 else 0
    
    print(f"\n[Phase 2 Complete]")
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
