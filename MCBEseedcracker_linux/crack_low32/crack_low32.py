# -*- coding: utf-8 -*-
"""
Minecraft Bedrock Low 32-bit Seed Cracker (Linux)

Supports both CPU (multiprocessing) and GPU (OpenCL) acceleration.

Usage:
    python crack_low32.py              # Load config from config.json
    python crack_low32.py --test       # Test mode (100M seeds), overrides config
    python crack_low32.py --cpu        # Force CPU mode
    python crack_low32.py --gpu        # Force GPU mode
    python crack_low32.py --start 1000 --end 2000  # Custom range, overrides config

Configuration file: ../config.json
"""
import ctypes
import time
import argparse
import multiprocessing as mp
import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import config_loader
sys.path.insert(0, str(Path(__file__).parent.parent))
import config_loader

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
    "pillager_outpost": {"name": "Pillager Outpost", "salt": 165745296, "spacing": 80, "separation": 24, "spread_type": "triangular", "rng_type": "bedrock"},
    "ruined_portal_overworld": {"name": "Ruined Portal (Overworld)", "salt": 40552231, "spacing": 40, "separation": 15, "spread_type": "linear", "rng_type": "bedrock"},
    "ruined_portal_nether": {"name": "Ruined Portal (Nether)", "salt": 40552231, "spacing": 25, "separation": 10, "spread_type": "linear", "rng_type": "bedrock"},
    "buried_treasure": {"name": "Buried Treasure", "salt": 16842397, "spacing": 4, "separation": 2, "spread_type": "triangular"},
}

# ===== Target structures (loaded from config.json) =====
# Load from config file (users can edit config.json)
_cfg = config_loader.get_low32_config()
TARGETS = _cfg.get('targets', [
    {"structure": "swamp_hut", "x": 2136, "z": -1176},
    {"structure": "jungle_temple", "x": -360, "z": -248},
    {"structure": "desert_temple", "x": -936, "z": 4744},
    {"structure": "ocean_monument", "x": 792, "z": -792},
    {"structure": "end_city", "x": 1352, "z": -1208},
])

def load_gpu_config():
    """Load GPU configuration from main config.json"""
    cfg = config_loader.get_low32_config()
    return {
        'use_gpu': cfg.get('use_gpu', True),
        'auto_fallback': cfg.get('auto_fallback', True),
        'seeds_per_thread': cfg.get('seeds_per_thread', 256),
        'max_results': cfg.get('max_results', 10000)
    }

def has_opencl_gpu():
    """Check if OpenCL GPU is available"""
    try:
        script_dir = Path(__file__).parent
        opencl_so = script_dir / 'crack_low32_opencl.so'

        if not opencl_so.exists():
            return False, "OpenCL SO not found"

        lib = ctypes.CDLL(str(opencl_so))

        lib.has_opencl_gpu.argtypes = []
        lib.has_opencl_gpu.restype = ctypes.c_int

        result = lib.has_opencl_gpu()
        if result:
            lib.get_opencl_device_info.argtypes = [ctypes.c_char_p, ctypes.c_int]
            lib.get_opencl_device_info.restype = ctypes.c_int

            buffer = ctypes.create_string_buffer(256)
            lib.get_opencl_device_info(buffer, 256)
            gpu_info = buffer.value.decode('utf-8')

            # Check compute units to detect old GPUs
            lib.get_gpu_compute_units.argtypes = []
            lib.get_gpu_compute_units.restype = ctypes.c_int

            compute_units = lib.get_gpu_compute_units()
            print(f"[INFO] GPU compute units: {compute_units}")

            # GPUs with <10 compute units are considered too old for GPU acceleration
            if compute_units < 10:
                print(f"[WARNING] GPU has only {compute_units} compute units (too old for GPU mode)")
                print(f"[INFO] Recommending CPU mode for this GPU")
                return False, f"{gpu_info} (old GPU, use CPU mode)"

            return True, gpu_info

        return False, "No OpenCL GPU found"
    except Exception as e:
        return False, str(e)

def test_sample_strictness(config, x, z, num_test_seeds=100000):
    """
    Test the strictness (matching probability) of a structure sample.
    Returns the number of matches in num_test_seeds attempts.

    Args:
        config: Structure configuration dict
        x: Block X coordinate
        z: Block Z coordinate
        num_test_seeds: Number of seeds to test (default 100000)

    Returns:
        Number of matches (lower = stricter)
    """
    spacing = config["spacing"]
    separation = config["separation"]

    # Calculate target parameters
    cx, cz = x >> 4, z >> 4
    rx, rz = cx // spacing, cz // spacing
    target_ox, target_oz = cx % spacing, cz % spacing

    # Calculate r_base
    r_base = (rx * CONST_A + rz * CONST_B + config["salt"]) & 0xFFFFFFFF

    # Load C library for fast testing
    lib_path = Path(__file__).parent / 'crack_low32.so'
    try:
        lib = ctypes.CDLL(str(lib_path))
        lib.crack_low32.argtypes = [
            ctypes.c_uint32, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_int), ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
        ]
        lib.crack_low32.restype = ctypes.c_int

        # Test using C library
        offset_range = spacing - separation
        spread_type_int = 1 if config.get("spread_type", "linear") == "triangular" else 0

        r_base_arr = (ctypes.c_uint32 * 1)(r_base)
        ox_arr = (ctypes.c_uint32 * 1)(target_ox)
        oz_arr = (ctypes.c_uint32 * 1)(target_oz)
        offset_range_arr = (ctypes.c_uint32 * 1)(offset_range)
        spread_type_arr = (ctypes.c_int * 1)(spread_type_int)
        results_arr = (ctypes.c_uint32 * num_test_seeds)()

        found = lib.crack_low32(
            0, num_test_seeds,
            r_base_arr, ox_arr, oz_arr, offset_range_arr, spread_type_arr,
            1, results_arr, num_test_seeds
        )

        return found
    except Exception as e:
        print(f"[WARNING] Failed to test strictness with C library: {e}")
        return 0


def prepare_targets(targets):
    # First sort by spread_type (linear first)
    sorted_targets = sorted(targets, key=lambda t: 0 if STRUCTURE_CONFIGS[t["structure"]].get("spread_type", "linear") == "linear" else 1)

    # Calculate parameters for all targets
    r_base_list, ox_list, oz_list = [], [], []
    offset_range_list, spread_type_list, structure_info = [], [], []

    for t in sorted_targets:
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
        structure_info.append({"name": config["name"], "x": x, "z": z, "rx": rx, "rz": rz, "spread_type": config.get("spread_type", "linear")})

    # Test strictness and sort (strictest first)
    strictness_scores = []

    for i, t in enumerate(sorted_targets):
        config = STRUCTURE_CONFIGS[t["structure"]]
        x, z = t["x"], t["z"]

        matches = test_sample_strictness(config, x, z, num_test_seeds=100000)
        strictness_scores.append(matches)

    # Sort by strictness (fewer matches = stricter = higher priority)
    # But maintain linear-first ordering
    indices = list(range(len(sorted_targets)))

    # Separate linear and triangular
    linear_indices = [i for i in indices if spread_type_list[i] == 0]
    triangular_indices = [i for i in indices if spread_type_list[i] == 1]

    # Sort each group by strictness (ascending = stricter first)
    linear_indices.sort(key=lambda i: strictness_scores[i])
    triangular_indices.sort(key=lambda i: strictness_scores[i])

    # Combine: linear first, then triangular
    sorted_indices = linear_indices + triangular_indices

    # Reorder all lists
    r_base_list = [r_base_list[i] for i in sorted_indices]
    ox_list = [ox_list[i] for i in sorted_indices]
    oz_list = [oz_list[i] for i in sorted_indices]
    offset_range_list = [offset_range_list[i] for i in sorted_indices]
    spread_type_list = [spread_type_list[i] for i in sorted_indices]
    structure_info = [structure_info[i] for i in sorted_indices]

    return r_base_list, ox_list, oz_list, offset_range_list, spread_type_list, structure_info

R_BASE, OX, OZ, OFFSET_RANGE, SPREAD_TYPE, STRUCTURE_INFO = prepare_targets(TARGETS)

def crack_worker_cpu(args):
    """CPU worker for multiprocessing"""
    start, end, r_base, ox, oz, offset_range, spread_type = args
    
    lib_path = Path(__file__).parent / 'crack_low32.so'
    lib = ctypes.CDLL(str(lib_path))
    
    lib.crack_low32.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_int), ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
    ]
    lib.crack_low32.restype = ctypes.c_int
    
    num_targets = len(r_base)
    r_base_arr = (ctypes.c_uint32 * num_targets)(*r_base)
    ox_arr = (ctypes.c_uint32 * num_targets)(*ox)
    oz_arr = (ctypes.c_uint32 * num_targets)(*oz)
    offset_range_arr = (ctypes.c_uint32 * num_targets)(*offset_range)
    spread_type_arr = (ctypes.c_int * num_targets)(*spread_type)
    results_arr = (ctypes.c_uint32 * 1000)()
    
    found = lib.crack_low32(start, end, r_base_arr, ox_arr, oz_arr, offset_range_arr, spread_type_arr, num_targets, results_arr, 1000)
    return [results_arr[i] for i in range(found)]

def run_crack_cpu(search_start, search_end, num_processes, all_results):
    """Run crack using CPU multiprocessing"""
    global_start = time.time()
    processed = search_start
    total_seeds = search_end - search_start + 1
    search_end_exclusive = search_end + 1
    step_size = 200_000_000
    
    pool = mp.Pool(num_processes)
    
    while processed <= search_end:
        step_start = processed
        step_end = min(processed + step_size, search_end_exclusive)
        chunk_size = (step_end - step_start) // num_processes
        
        tasks = []
        for i in range(num_processes):
            start = step_start + i * chunk_size
            end = step_start + (i + 1) * chunk_size if i < num_processes - 1 else step_end
            if start < end:
                tasks.append((start, end, R_BASE, OX, OZ, OFFSET_RANGE, SPREAD_TYPE))
        
        results = pool.map(crack_worker_cpu, tasks)
        
        for r in results:
            all_results.extend(r)
            for seed in r:
                print(f">>> [!] Found seed: {seed} (0x{seed:08X})")
        
        processed = step_end
        elapsed = time.time() - global_start
        speed = (processed - search_start) / elapsed if elapsed > 0 else 0
        progress = (processed - search_start) / total_seeds * 100
        eta = (search_end_exclusive - processed) / speed if speed > 0 else 0
        
        eta_str = f"{eta/3600:.1f}h" if eta > 3600 else f"{eta/60:.1f}min" if eta > 60 else f"{eta:.0f}s"
        print(f"[-] {processed - search_start:,}/{total_seeds:,} ({progress:5.1f}%) | Speed: {speed:,.0f}/s | ETA: {eta_str}")
    
    pool.close()
    pool.join()
    
    return time.time() - global_start

def run_crack_gpu(search_start, search_end, all_results, config):
    """Run crack using GPU (OpenCL) with batch processing"""
    lib_path = Path(__file__).parent / 'crack_low32_opencl.so'

    # Change working directory to find crack_low32.cl
    original_dir = os.getcwd()
    os.chdir(lib_path.parent)

    try:
        lib = ctypes.CDLL(str(lib_path))

        lib.crack_low32_opencl.argtypes = [
            ctypes.c_uint32, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_int), ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
        ]
        lib.crack_low32_opencl.restype = ctypes.c_int

        num_targets = len(R_BASE)
        r_base_arr = (ctypes.c_uint32 * num_targets)(*R_BASE)
        ox_arr = (ctypes.c_uint32 * num_targets)(*OX)
        oz_arr = (ctypes.c_uint32 * num_targets)(*OZ)
        offset_range_arr = (ctypes.c_uint32 * num_targets)(*OFFSET_RANGE)
        spread_type_arr = (ctypes.c_int * num_targets)(*SPREAD_TYPE)

        max_results = config.get('max_results', 10000)
        results_arr = (ctypes.c_uint32 * max_results)()

        # Calculate batch size based on GPU capability
        # Modern GPUs can handle ~1B seeds per batch efficiently
        batch_size = 1_000_000_000  # 1B seeds per batch

        total_seeds = search_end - search_start + 1
        total_batches = (total_seeds + batch_size - 1) // batch_size

        print(f"[GPU] Running GPU crack: {search_start:,} ~ {search_end:,}")
        print(f"[GPU] Batch mode: {total_batches} batches of {batch_size:,} seeds")

        global_start = time.time()
        processed = search_start

        while processed <= search_end:
            batch_start = processed
            batch_end = min(processed + batch_size - 1, search_end)

            batch_elapsed_start = time.time()

            found = lib.crack_low32_opencl(
                batch_start, batch_end,
                r_base_arr, ox_arr, oz_arr, offset_range_arr, spread_type_arr,
                num_targets, results_arr, max_results
            )

            batch_elapsed = time.time() - batch_elapsed_start

            if found < 0:
                print(f"[ERROR] GPU crack failed at batch {processed:,}")
                return -1

            for i in range(found):
                seed = results_arr[i]
                all_results.append(seed)
                print(f">>> [!] Found seed: {seed} (0x{seed:08X})")

            processed = batch_end + 1

            # Progress report (similar to CPU format)
            progress = (processed - search_start) / total_seeds * 100
            elapsed = time.time() - global_start
            speed = (processed - search_start) / elapsed if elapsed > 0 else 0
            eta = (search_end - processed) / speed if speed > 0 else 0

            print(f"[-] {processed - search_start:,}/{total_seeds:,} ({progress:5.1f}%) | "
                  f"Speed: {speed:,.0f}/s | ETA: {eta:.0f}s")

        elapsed = time.time() - global_start
        speed = total_seeds / elapsed if elapsed > 0 else 0

        print(f"\n[GPU COMPLETE] Found {len(all_results)} seeds in {elapsed:.1f}s ({elapsed/60:.1f}min)")
        print(f"[GPU SPEED] {speed/1e6:.0f}M seeds/s")

        return elapsed

    except Exception as e:
        print(f"[ERROR] GPU crack exception: {e}")
        return -1
    finally:
        os.chdir(original_dir)

def main():
    parser = argparse.ArgumentParser(description="Minecraft Bedrock Low 32-bit Seed Cracker (Linux)")
    parser.add_argument("--start", type=int, default=None, help="Start low32 value (inclusive), overrides config")
    parser.add_argument("--end", type=int, default=None, help="End low32 value (inclusive), overrides config")
    parser.add_argument("--test", action="store_true", help="Test mode (100M seeds), overrides config")
    parser.add_argument("--cpu", action="store_true", help="Force CPU mode")
    parser.add_argument("--gpu", action="store_true", help="Force GPU mode")
    parser.add_argument("--processes", type=int, default=None, help="Number of CPU processes (only for CPU mode)")
    args = parser.parse_args()
    
    # Load configuration
    cfg = config_loader.get_low32_config()
    
    # Override config with command-line arguments
    if args.test:
        test_mode = True
        search_start = 0
        search_end = 100000000
    else:
        test_mode = args.test if args.test is not None else cfg.get('test_mode', False)
        search_start = args.start if args.start is not None else cfg.get('start', 0)
        search_end = args.end if args.end is not None else cfg.get('end', 0xFFFFFFFF)
    
    print("=" * 60)
    print("Minecraft Bedrock Low 32-bit Seed Cracker (Linux)")
    print("=" * 60)
    
    print(f"\n[*] Target structures ({len(TARGETS)}) [sorted: linear first]:")
    for i, info in enumerate(STRUCTURE_INFO):
        spread_type_str = f" [{info['spread_type']}]"
        print(f"    {i+1}. {info['name']} ({info['x']}, {info['z']}){spread_type_str}")
    
    # Determine compute mode
    use_gpu = False
    gpu_device = "N/A"
    
    if args.cpu:
        print("\n[*] CPU mode forced")
        use_gpu = False
    elif args.gpu:
        print("\n[*] GPU mode forced")
        use_gpu = True
    elif cfg.get('use_gpu', True):
        has_gpu, gpu_info = has_opencl_gpu()
        if has_gpu:
            print(f"\n[*] GPU detected: {gpu_info}")
            use_gpu = True
            gpu_device = gpu_info
        else:
            print(f"\n[*] GPU not available: {gpu_info}")
            if cfg.get('auto_fallback', True):
                print("[*] Auto-fallback to CPU mode")
                use_gpu = False
            else:
                print("[!] GPU not available and auto-fallback disabled")
                return
    else:
        print("\n[*] CPU mode (from config)")
        use_gpu = False

    # Get process count: command-line > config > auto-detect
    if args.processes is not None:
        num_processes = args.processes
        source = "command-line"
    elif cfg.get('processes', None) is not None:
        num_processes = cfg.get('processes')
        source = "config file"
    else:
        num_processes = mp.cpu_count()
        source = "auto-detect"

    print(f"[*] Processes: {num_processes} ({source})")

    compute_device = f"GPU ({gpu_device})" if use_gpu else f"CPU ({num_processes} cores)"
    print(f"[*] Compute device: {compute_device}")
    
    # Check library files
    if use_gpu:
        lib_path = Path(__file__).parent / 'crack_low32_opencl.so'
        if not lib_path.exists():
            print(f"\n[!] Error: OpenCL library not found: {lib_path}")
            print("[!] Run 'gcc -O3 -fPIC -shared -o crack_low32_opencl.so crack_low32_opencl.c -lOpenCL' first")
            return
    else:
        lib_path = Path(__file__).parent / 'crack_low32.so'
        if not lib_path.exists():
            print(f"\n[!] Error: CPU library not found: {lib_path}")
            print("[!] Please run 'bash build.sh' first to compile the library.")
            return
    
    total_seeds = search_end - search_start + 1
    
    print(f"\n[*] Mode: {'Test' if test_mode else 'Full'}")
    print(f"[*] Search range: {search_start:,} ~ {search_end:,} ({total_seeds:,} seeds)")
    
    print("\n" + "-" * 60)
    print("Starting crack...")
    print("-" * 60)

    all_results = []

    # Load GPU config from main config.json
    config = load_gpu_config()

    if use_gpu:
        elapsed = run_crack_gpu(search_start, search_end, all_results, config)
        if elapsed < 0 and config.get('auto_fallback', True):
            print("\n[*] Falling back to CPU mode...")
            elapsed = run_crack_cpu(search_start, search_end, num_processes, all_results)
    else:
        elapsed = run_crack_cpu(search_start, search_end, num_processes, all_results)
    
    print(f"\n[*] Done! Time: {elapsed:.1f}s ({elapsed/60:.1f}min)")
    print(f"[*] Speed: {total_seeds/elapsed:,.0f} seeds/s")
    print(f"[*] Found {len(all_results)} matching seeds")
    
    for seed in all_results:
        print(f"    Low 32-bit: {seed} (0x{seed:08X})")

if __name__ == "__main__":
    main()