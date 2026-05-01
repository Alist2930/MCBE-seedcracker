# -*- coding: utf-8 -*-
"""
Minecraft Bedrock Low 32-bit Seed Cracker

Usage:
    python crack_low32.py          # Full crack (2^32)
    python crack_low32.py --test   # Test mode (100M seeds)
"""
import ctypes
import time
import argparse
import multiprocessing as mp
from pathlib import Path

CONST_A = 2570712328
CONST_B = 4048968661

STRUCTURE_CONFIGS = {
    "village": {"name": "Village", "salt": 10387312, "spacing": 34, "separation": 8, "spread_type": "triangular"},
    "mansion": {"name": "Woodland Mansion", "salt": 10387319, "spacing": 80, "separation": 20, "spread_type": "triangular"},
    "end_city": {"name": "End City", "salt": 10387313, "spacing": 20, "separation": 11, "spread_type": "triangular"},
    "ocean_monument": {"name": "Ocean Monument", "salt": 10387313, "spacing": 32, "separation": 5, "spread_type": "triangular"},
    "ancient_city": {"name": "Ancient City", "salt": 20083232, "spacing": 24, "separation": 8, "spread_type": "triangular"},
    "ocean_ruins": {"name": "Ocean Ruins", "salt": 14357621, "spacing": 20, "separation": 8, "spread_type": "linear"},
    "shipwreck": {"name": "Shipwreck", "salt": 165745295, "spacing": 24, "separation": 4, "spread_type": "linear"},
    "nether_complexes": {"name": "Nether Fortress/Bastion", "salt": 30084232, "spacing": 30, "separation": 4, "spread_type": "linear"},
    "desert_temple": {"name": "Desert Temple", "salt": 14357617, "spacing": 32, "separation": 8, "spread_type": "linear"},
    "igloo": {"name": "Igloo", "salt": 14357617, "spacing": 32, "separation": 8, "spread_type": "linear"},
    "swamp_hut": {"name": "Swamp Hut", "salt": 14357617, "spacing": 32, "separation": 8, "spread_type": "linear"},
    "jungle_temple": {"name": "Jungle Temple", "salt": 14357617, "spacing": 32, "separation": 8, "spread_type": "linear"},
}

# ===== 在这里填写目标结构（建议5个）=====
TARGETS = [
    {"structure": "swamp_hut", "x": 2136, "z": -1176},
    {"structure": "jungle_temple", "x": -360, "z": -248},
    {"structure": "desert_temple", "x": -936, "z": 4744},
    {"structure": "ocean_monument", "x": 792, "z": -792},
    {"structure": "end_city", "x": 1352, "z": -1208},
]

def prepare_targets(targets):
    r_base_list, ox_list, oz_list = [], [], []
    offset_range_list, spread_type_list, structure_info = [], [], []
    
    for t in targets:
        config = STRUCTURE_CONFIGS[t["structure"]]
        x, z = t["x"], t["z"]
        spacing, separation = config["spacing"], config["separation"]
        
        cx, cz = x >> 4, z >> 4
        rx, rz = cx // spacing, cz // spacing
        ox, oz = cx % spacing, cz % spacing
        
        r_base = (rx * CONST_A + rz * CONST_B + config["salt"]) & 0xFFFFFFFF
        spread_type_int = 1 if config.get("spread_type", "linear") == "triangular" else 0
        
        r_base_list.append(r_base)
        ox_list.append(ox)
        oz_list.append(oz)
        offset_range_list.append(spacing - separation)
        spread_type_list.append(spread_type_int)
        structure_info.append({"name": config["name"], "x": x, "z": z, "rx": rx, "rz": rz})
    
    return r_base_list, ox_list, oz_list, offset_range_list, spread_type_list, structure_info

R_BASE, OX, OZ, OFFSET_RANGE, SPREAD_TYPE, STRUCTURE_INFO = prepare_targets(TARGETS)

def crack_worker(args):
    start, end, r_base, ox, oz, offset_range, spread_type = args
    
    lib_path = Path(__file__).parent / 'crack_low32.dll'
    lib = ctypes.CDLL(str(lib_path))
    
    lib.crack_low32.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_int), ctypes.c_int,
        ctypes.POINTER(ctypes.c_int32), ctypes.c_int
    ]
    lib.crack_low32.restype = ctypes.c_int
    
    num_targets = len(r_base)
    r_base_arr = (ctypes.c_uint32 * num_targets)(*r_base)
    ox_arr = (ctypes.c_uint32 * num_targets)(*ox)
    oz_arr = (ctypes.c_uint32 * num_targets)(*oz)
    offset_range_arr = (ctypes.c_uint32 * num_targets)(*offset_range)
    spread_type_arr = (ctypes.c_int * num_targets)(*spread_type)
    results_arr = (ctypes.c_int32 * 1000)()
    
    found = lib.crack_low32(start, end, r_base_arr, ox_arr, oz_arr, offset_range_arr, spread_type_arr, num_targets, results_arr, 1000)
    return [results_arr[i] for i in range(found)]

def run_crack(search_start, search_end, num_processes, all_results):
    global_start = time.time()
    processed = search_start
    total_seeds = search_end - search_start
    step_size = 200_000_000
    
    pool = mp.Pool(num_processes)
    
    while processed < search_end:
        step_start = processed
        step_end = min(processed + step_size, search_end)
        chunk_size = (step_end - step_start) // num_processes
        
        tasks = []
        for i in range(num_processes):
            start = step_start + i * chunk_size
            end = step_start + (i + 1) * chunk_size if i < num_processes - 1 else step_end
            if start < end:
                tasks.append((start, end, R_BASE, OX, OZ, OFFSET_RANGE, SPREAD_TYPE))
        
        results = pool.map(crack_worker, tasks)
        
        for r in results:
            all_results.extend(r)
            for seed in r:
                print(f">>> [!] Found seed: {seed} (0x{seed:08X})")
        
        processed = step_end
        elapsed = time.time() - global_start
        speed = (processed - search_start) / elapsed if elapsed > 0 else 0
        progress = (processed - search_start) / total_seeds * 100
        eta = (search_end - processed) / speed if speed > 0 else 0
        
        eta_str = f"{eta/3600:.1f}h" if eta > 3600 else f"{eta/60:.1f}min" if eta > 60 else f"{eta:.0f}s"
        print(f"[-] {processed - search_start:,}/{total_seeds:,} ({progress:5.1f}%) | Speed: {speed:,.0f}/s | ETA: {eta_str}")
    
    pool.close()
    pool.join()
    
    return time.time() - global_start

def main():
    parser = argparse.ArgumentParser(description="Minecraft Bedrock Low 32-bit Seed Cracker")
    parser.add_argument("--start", type=int, default=0, help="Start low32 value")
    parser.add_argument("--end", type=int, default=0xFFFFFFFF, help="End low32 value")
    parser.add_argument("--test", action="store_true", help="Test mode (100M seeds)")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Minecraft Bedrock Low 32-bit Seed Cracker")
    print("=" * 60)
    
    print(f"\n[*] Target structures ({len(TARGETS)}):")
    for i, info in enumerate(STRUCTURE_INFO):
        print(f"    {i+1}. {info['name']} ({info['x']}, {info['z']})")
    
    num_processes = mp.cpu_count()
    print(f"\n[*] Processes: {num_processes}")
    
    lib_path = Path(__file__).parent / 'crack_low32.dll'
    if not lib_path.exists():
        print(f"\n[!] Error: DLL not found: {lib_path}")
        return
    
    search_start = args.start
    search_end = 100000000 if args.test and args.end == 0xFFFFFFFF else args.end
    total_seeds = search_end - search_start
    
    print(f"\n[*] Mode: {'Test' if args.test else 'Full'}")
    print(f"[*] Search range: {search_start:,} ~ {search_end:,} ({total_seeds:,} seeds)")
    
    print("\n" + "-" * 60)
    print("Starting crack...")
    print("-" * 60)
    
    all_results = []
    elapsed = run_crack(search_start, search_end, num_processes, all_results)
    
    print(f"\n[*] Done! Time: {elapsed:.1f}s ({elapsed/60:.1f}min)")
    print(f"[*] Speed: {total_seeds/elapsed:,.0f} seeds/s")
    print(f"[*] Found {len(all_results)} matching seeds")
    
    for seed in all_results:
        print(f"    Low 32-bit: {seed} (0x{seed:08X})")

if __name__ == "__main__":
    main()
