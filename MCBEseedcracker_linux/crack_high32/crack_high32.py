# -*- coding: utf-8 -*-
"""
Minecraft Bedrock High 32-bit Seed Cracker

Usage:
    python crack_high32.py              # Load config from config.json
    python crack_high32.py --test       # Test mode (0 ~ 100M), overrides config
    python crack_high32.py --start 0 --end 1000000  # Custom range, overrides config
"""
import ctypes
import time
import sys
import os
import argparse
import multiprocessing as mp
from pathlib import Path
from datetime import datetime

# Disable output buffering for real-time progress updates
# This is critical for multiprocessing to show progress immediately
import functools
print = functools.partial(print, flush=True)  # Always flush print output

# Add parent directory to path to import config_loader
sys.path.insert(0, str(Path(__file__).parent.parent))
import config_loader

script_dir = Path(__file__).parent.resolve()
dll_path = script_dir / "crack_high32.so"

# Load biome data from biomes.json for ID->name mapping (display only)
import json as _json
_BIOME_DATA = None
_BIOME_ID_TO_NAME = {}

def _load_biome_data():
    """Load biome data from biomes.json (for ID->name display only)"""
    global _BIOME_DATA, _BIOME_ID_TO_NAME
    if _BIOME_DATA is not None:
        return
    biome_file = Path(__file__).parent / "biomes.json"
    if biome_file.exists():
        with open(biome_file, 'r', encoding='utf-8') as f:
            _BIOME_DATA = _json.load(f)
        # Build ID->name map
        for name, data in _BIOME_DATA.items():
            _BIOME_ID_TO_NAME[data.get('id')] = name

def get_biome_name(biome_id):
    """Get biome name from biomes.json (for display only)"""
    _load_biome_data()
    return _BIOME_ID_TO_NAME.get(biome_id, f"biome_{biome_id}")

VERSION_BIOMES = {
    '1.18': [174, 175, 177, 178, 179, 180, 181, 182],  # Lush Caves, Dripstone Caves
    '1.19': [183, 184],  # Deep Dark, Mangrove Swamp
    '1.20.0-51': [185],  # Cherry Grove
    '1.20.60-81': [185],  # Cherry Grove
    '1.21-1.21.40': [],  # No new biomes
    '1.21.50': [186],  # Pale Garden
    '1.21.60-26.23': [186],  # Pale Garden (expanded range)
    '26.30-26.40': [187],  # Sulfur Caves
    '26.50': [188],  # Dappled Forest
}

SIGNED64_MAX = 9223372036854775807
UINT64_MAX = 18446744073709551615

def to_signed64(seed):
    if seed > SIGNED64_MAX:
        return seed - UINT64_MAX - 1
    return seed

def format_seed_output(seed, low32):
    high32 = seed >> 32
    display_seed = to_signed64(seed)
    
    lines = [
        f"\n[FOUND] Seed found!",
        f"    Low 32-bit:  {low32} (0x{low32:08X})",
        f"    High 32-bit: {high32} (0x{high32:08X})",
        f"    Full seed:   {display_seed} (0x{seed:016X})",
    ]
    
    return '\n'.join(lines)

def test_sample_strictness(sample, low32, mc_version, num_test_seeds=100000):
    """
    Test the strictness (matching probability) of a biome sample.
    Tests num_test_seeds high32 candidates and counts how many produce the target biome.
    Returns the match count (lower = stricter = rarer = higher priority).

    Args:
        sample: (x, z, y, biome_id) tuple
        low32: Known low 32-bit value
        mc_version: cubiomes version constant (e.g., MC_26_3=35)
        num_test_seeds: Number of high32 candidates to test (default 100000)

    Returns:
        Number of matches (lower = stricter)
    """
    if len(sample) == 4:
        x, z, y, biome_id = sample
    else:
        x, z, biome_id = sample
        y = 200

    # Load C library
    dll = init_dll()

    # Create single-sample array
    sample_array = (BiomeSample * 1)()
    sample_array[0].x = x
    sample_array[0].z = z
    sample_array[0].y = y
    sample_array[0].biome_id = biome_id

    # Allocate results buffer (max = num_test_seeds, worst case all match)
    results = (ctypes.c_uint64 * num_test_seeds)()

    found = dll.crack_high32_soa(
        0, num_test_seeds, low32, 0,
        sample_array, 1,
        results, num_test_seeds, mc_version
    )

    # Check for native function errors
    if found < 0:
        raise RuntimeError(f"crack_high32_soa failed during strictness test (return code {found})")

    return found

def sort_samples_by_strictness(samples, low32, mc_version, num_test_seeds=100000):
    """
    Sort samples by empirical strictness (fewest matches first = rarest first).
    Tests each sample independently against num_test_seeds high32 candidates.

    Args:
        samples: List of (x, z, y, biome_id) tuples
        low32: Known low 32-bit value
        mc_version: cubiomes version constant
        num_test_seeds: Number of high32 candidates to test per sample

    Returns:
        (sorted_samples, strictness_scores) tuple
    """
    strictness_scores = []
    for sample in samples:
        matches = test_sample_strictness(sample, low32, mc_version, num_test_seeds)
        strictness_scores.append(matches)

    # Sort ascending (fewer matches = stricter = first)
    paired = list(zip(strictness_scores, samples))
    paired.sort(key=lambda p: p[0])
    sorted_samples = [s for _, s in paired]
    sorted_scores = [sc for sc, _ in paired]

    return sorted_samples, sorted_scores

def get_biome_version(biome_id):
    """Get the minimum version required for a biome"""
    for version, biome_ids in VERSION_BIOMES.items():
        if biome_id in biome_ids:
            return version
    return '1.18'  # Default: biomes not in VERSION_BIOMES exist since 1.18 (oldest supported version)

def check_biome_version(samples, mc_version):
    """
    Check if all biome samples are compatible with the current MC version
    Returns warning messages for incompatible biomes
    Sample format: (x, z, y, biome_id)
    """
    # Version order for comparison (use small versions)
    version_order = ['1.18', '1.19', '1.20.0-51', '1.20.60-81', '1.21-1.21.40', '1.21.50', '1.21.60-26.23', '26.30-26.40', '26.50']
    mc_idx = version_order.index(mc_version) if mc_version in version_order else len(version_order) - 1
    warnings = []
    
    for sample in samples:
        # Handle both 4-tuple (x, z, y, biome_id) and legacy 3-tuple (x, z, biome_id)
        if len(sample) == 4:
            x, z, y, biome_id = sample
        else:
            x, z, biome_id = sample
        biome_version = get_biome_version(biome_id)
        # Handle version not in list (should not happen with valid biomes)
        try:
            biome_idx = version_order.index(biome_version)
        except ValueError:
            biome_idx = 0  # Treat unknown versions as oldest
        if biome_idx > mc_idx:
            biome_name = get_biome_name(biome_id)
            warnings.append(f"  ({x}, {z}) -> {biome_name} (ID: {biome_id}) requires {biome_version}+, but current version is {mc_version}")
    
    return warnings

# ===== Configuration (loaded from config.json) =====
_cfg = config_loader.get_high32_config()

# Biome samples (x, z, y, biome_id)
# Load from config file
_cfg_samples = _cfg.get('samples', [])
SAMPLES = [(s['x'], s['z'], s['y'], s['biome_id']) for s in _cfg_samples] if _cfg_samples else [
    (-1922, 1231, 200, 185),   # cherry_grove
    (-4706, 3302, 200, 132),   # flower_forest
    (-935, 2592, 200, 5),      # taiga
    (-2697, 1363, 200, 4),     # forest
    (-270, 470, 200, 186),     # pale_garden
]

LOW32 = _cfg.get('low32', 1818588773)

# MC Version (string like '1.21.60', '1.21.50', etc.)
MC_VERSION_STR = _cfg.get('mc_version', '26.50')

# MC version validation and normalization happens after VERSION_MAP is defined below

MC_1_18 = 22
MC_1_19 = 24
MC_1_20 = 25
MC_1_21_3 = 27  # Java 1.21-1.21.3
MC_1_21_WD = 28  # Java 1.21.4 (Winter Drop, Bedrock 1.21.50)
MC_1_21_5 = 29  # Java 1.21.5-26.1 (Pale Garden expanded range, Bedrock 1.21.60-26.23)
MC_26_2 = 34  # Java 26.2 (Chaos Cubed Drop, Bedrock 26.30-26.40)
MC_26_3 = 35  # Java 26.3 (Goes Wild, Bedrock 26.50)

VERSION_MAP = {
    # Bedrock version auto-mapping (based on ChunkBase)
    "26.50": MC_26_3,  # Java 26.3 (Dappled Forest)
    "26.30-26.40": MC_26_2,  # Java 26.2 (Sulfur Caves)
    "1.21.60-26.23": MC_1_21_5,  # Java 1.21.5-26.1 (Pale Garden expanded range)
    "1.21.50": MC_1_21_WD,  # Java 1.21.4 (Pale Garden supported)
    "1.21-1.21.40": MC_1_21_3,  # Does not support Pale Garden
    "1.20.60-81": MC_1_20,
    "1.20.0-51": MC_1_20,
    "1.19": MC_1_19,
    "1.18": MC_1_18,
}

# Validate and normalize MC version string
if MC_VERSION_STR not in VERSION_MAP:
    # Try partial match (e.g., '1.21.60' matches '1.21.60-26.23')
    parts = MC_VERSION_STR.split('.')
    matched = None
    if len(parts) >= 2:
        major_minor = f"{parts[0]}.{parts[1]}"
        for ver_key in VERSION_MAP:
            if ver_key.startswith(major_minor):
                matched = ver_key
                break
    if matched:
        print(f"[INFO] MC version '{MC_VERSION_STR}' matched to '{matched}'")
        MC_VERSION_STR = matched
    else:
        print(f"[WARNING] Unknown MC version '{MC_VERSION_STR}', defaulting to '26.50'")
        MC_VERSION_STR = "26.50"
MC_VERSION = VERSION_MAP[MC_VERSION_STR]

# Batch size for multiprocessing
# Lower value = more frequent progress updates, but slightly slower
# Higher value = less frequent updates, but slightly faster
# Recommended: 100000-500000 for production, 10000-50000 for testing
BATCH_SIZE = 100000  # Reduced from 500000 for more frequent progress updates
MAX_RESULTS = 1000

class BiomeSample(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("z", ctypes.c_int), ("y", ctypes.c_int), ("biome_id", ctypes.c_int)]

def init_dll():
    dll = ctypes.CDLL(str(dll_path))

    dll.crack_high32_soa.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int,
        ctypes.POINTER(BiomeSample), ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_int, ctypes.c_int
    ]
    dll.crack_high32_soa.restype = ctypes.c_int

    # Phase 3 of Java LCG: non-contiguous high32 search (fixed h16, vary bits 48-63)
    dll.crack_high32_lcg_phase3.argtypes = [
        ctypes.c_uint16,    # h16 (fixed bits 32-47)
        ctypes.c_uint32,    # low32
        ctypes.c_uint16,    # min_upper (bits 48-63, inclusive)
        ctypes.c_uint16,    # max_upper (bits 48-63, inclusive)
        ctypes.POINTER(BiomeSample), ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_int, ctypes.c_int
    ]
    dll.crack_high32_lcg_phase3.restype = ctypes.c_int

    return dll

def crack_batch_soa(args):
    start_high, end_high, low32, samples, y_coord, mc_version = args
    dll = init_dll()

    # Check if DLL loaded successfully
    if dll is None:
        raise RuntimeError(f"crack_high32 library not found or failed to load")

    num_samples = len(samples)
    sample_array = (BiomeSample * num_samples)()
    for i, sample in enumerate(samples):
        if len(sample) == 4:
            x, z, y, biome_id = sample
        else:
            x, z, biome_id = sample
            y = 200  # Default Y for backward compatibility
        sample_array[i].x = x
        sample_array[i].z = z
        sample_array[i].y = y
        sample_array[i].biome_id = biome_id

    results = (ctypes.c_uint64 * MAX_RESULTS)()

    found = dll.crack_high32_soa(
        start_high, end_high, low32, y_coord,
        sample_array, num_samples,
        results, MAX_RESULTS, mc_version
    )

    # Check for native function errors
    if found < 0:
        raise RuntimeError(f"crack_high32_soa failed for range {start_high}-{end_high} (return code {found})")

    return [results[i] for i in range(found)]


def crack_batch_lcg_phase3(args):
    """Phase 3 wrapper: Call crack_high32_lcg_phase3 for non-contiguous high32 search.

    Iterates bits_48_63 (upper) with fixed h16 (bits 32-47).
    high32 = (upper << 16) | h16, so valid high32 values are spaced 65536 apart.
    """
    h16, low32, min_upper, max_upper, samples, mc_version = args
    dll = init_dll()

    if dll is None:
        raise RuntimeError("crack_high32 library not found or failed to load")

    num_samples = len(samples)
    sample_array = (BiomeSample * num_samples)()
    for i, sample in enumerate(samples):
        if len(sample) == 4:
            x, z, y, biome_id = sample
        else:
            x, z, biome_id = sample
            y = 200
        sample_array[i].x = x
        sample_array[i].z = z
        sample_array[i].y = y
        sample_array[i].biome_id = biome_id

    results = (ctypes.c_uint64 * MAX_RESULTS)()

    found = dll.crack_high32_lcg_phase3(
        h16, low32, min_upper, max_upper,
        sample_array, num_samples,
        results, MAX_RESULTS, mc_version
    )

    if found < 0:
        raise RuntimeError(f"crack_high32_lcg_phase3 failed for h16=0x{h16:04X} (return code {found})")

    return [results[i] for i in range(found)]


# ===== Java LCG structure cracking (phase 2: bits 32-47) =====
# Java LCG constants (cubiomes-bedrock algorithm)
JLCG_K = 0x5DEECE66D
JLCG_M48 = (1 << 48) - 1
JLCG_B = 0xB
JLCG_A_REG = 341873128712
JLCG_B_REG = 132897987541

# Java LCG structure configs (Trail Ruins, Trial Chambers, Abandoned Camp)
JAVA_LCG_STRUCTURES = {
    "trail_ruins": {"name": "Trail Ruins", "salt": 83469867, "spacing": 34, "separation": 8},
    "trial_chamber": {"name": "Trial Chamber", "salt": 94251327, "spacing": 34, "separation": 12},
    "abandoned_camp": {"name": "Abandoned Camp", "salt": 91231127, "spacing": 37, "separation": 8},
}


def crack_high16_java_lcg(low32, lcg_structures, search_start=0, search_end=0xFFFFFFFF):
    """
    Phase 2: Brute-force bits 32-47 using Java LCG structures.
    Only searches h16 values whose range overlaps with [search_start, search_end].

    Args:
        low32: Known lower 32 bits of the seed.
        lcg_structures: List of dicts with keys: type, x, z (block coordinates)
        search_start: User's high32 search start (inclusive)
        search_end: User's high32 search end (inclusive)

    Returns:
        List of 16-bit values (bits 32-47) that match all targets.
    """
    # Prepare constraints: per-structure list of 4 (r_const, target_ox, target_oz) offsets.
    # 4-chunk grid: a player-reported coordinate may correspond to one of 4 origin chunks:
    # (cx,cz), (cx,cz+1), (cx+1,cz), (cx+1,cz+1). A structure matches if ANY offset matches.
    structure_constraints = []  # [(chunk_range, [(r_const, target_ox, target_oz), ...4]), ...]
    for s in lcg_structures:
        stype = s.get('type')
        config = JAVA_LCG_STRUCTURES.get(stype)
        if not config:
            print(f"[WARNING] Unknown Java LCG structure: {stype}, skipping")
            continue
        spacing = config['spacing']
        separation = config['separation']
        chunk_range = spacing - separation
        salt = config['salt']
        cx = s['x'] >> 4  # block to chunk
        cz = s['z'] >> 4

        offsets = []
        for dx in [0, 1]:
            for dz in [0, 1]:
                origin_cx = cx + dx
                origin_cz = cz + dz
                rx = origin_cx // spacing
                rz = origin_cz // spacing
                target_ox = origin_cx % spacing
                target_oz = origin_cz % spacing
                r_const = (rx * JLCG_A_REG + rz * JLCG_B_REG + salt) & JLCG_M48
                offsets.append((r_const, target_ox, target_oz))
        structure_constraints.append((chunk_range, offsets))

    if not structure_constraints:
        return []

    # Brute-force h16 candidates (bits 32-47)
    # h16 is valid iff its minimum possible high32 (h16 itself, upper=0) <= end
    # and its maximum possible high32 (0xFFFF0000 + h16, upper=0xFFFF) >= start
    min_h16 = 0
    if search_start > 0xFFFF0000:
        min_h16 = search_start - 0xFFFF0000
    max_h16 = min(0xFFFF, search_end)

    candidates = []
    for h16 in range(min_h16, max_h16 + 1):
        candidate_48 = (h16 << 32) | low32
        all_match = True
        for chunk_range, offsets in structure_constraints:
            structure_matched = False
            for r_const, target_ox, target_oz in offsets:
                region_seed = (candidate_48 + r_const) & JLCG_M48
                seed = region_seed ^ JLCG_K
                seed = (seed * JLCG_K + JLCG_B) & JLCG_M48
                ox = (seed >> 17) % chunk_range
                if ox != target_ox:
                    continue
                seed = (seed * JLCG_K + JLCG_B) & JLCG_M48
                oz = (seed >> 17) % chunk_range
                if oz != target_oz:
                    continue
                structure_matched = True
                break
            if not structure_matched:
                all_match = False
                break
        if all_match:
            candidates.append(h16)

    return candidates


def main():
    # Create/Clear found seeds file
    found_seeds_file = Path(__file__).parent / "found_seeds.txt"
    start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(found_seeds_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("Minecraft Bedrock High 32-bit Seed Cracker - Found Seeds\n")
        f.write("=" * 60 + "\n")
        f.write(f"Start Time: {start_time_str}\n")
        f.write("=" * 60 + "\n\n")

    parser = argparse.ArgumentParser(description='Minecraft Bedrock High 32-bit Seed Cracker')
    parser.add_argument('--start', type=int, default=None, help='Start high value (inclusive), overrides config')
    parser.add_argument('--end', type=int, default=None, help='End high value (inclusive), overrides config')
    parser.add_argument('--test', action='store_true', help='Test mode: 0 ~ 100M, overrides config')
    parser.add_argument('--low32', type=int, default=None, help='Low 32-bit value, overrides config')
    parser.add_argument('--processes', type=int, default=None, help='Number of processes')
    parser.add_argument('--lcg-structure', action='append', default=None,
                        help='Java LCG structure (format: name:x:z, e.g., trail_ruins:3069:2883). Repeatable. Enables phase 2 (32-47 bit) + phase 3 (48-63 bit) flow.')
    args = parser.parse_args()

    # Load configuration
    cfg = config_loader.get_high32_config()

    # Parse Java LCG structures: CLI args override config.json
    lcg_structures = []
    if args.lcg_structure:
        # CLI args provided, use them
        for s in args.lcg_structure:
            parts = s.split(':')
            if len(parts) == 3:
                name = parts[0]
                try:
                    x, z = int(parts[1]), int(parts[2])
                except ValueError:
                    print(f"[WARNING] Invalid coordinates in: {s}, skipping")
                    continue
                if name in JAVA_LCG_STRUCTURES:
                    lcg_structures.append({"type": name, "x": x, "z": z})
                else:
                    valid = ", ".join(sorted(JAVA_LCG_STRUCTURES.keys()))
                    print(f"[WARNING] Unknown Java LCG structure '{name}'. Valid: {valid}")
            else:
                print(f"[WARNING] Invalid format (expected name:x:z): {s}")
    else:
        # Load from config.json
        cfg_lcg = cfg.get('lcg_structures', [])
        for s in cfg_lcg:
            stype = s.get('type')
            if stype in JAVA_LCG_STRUCTURES:
                lcg_structures.append({"type": stype, "x": s['x'], "z": s['z']})
            else:
                valid = ", ".join(sorted(JAVA_LCG_STRUCTURES.keys()))
                print(f"[WARNING] Unknown Java LCG structure '{stype}' in config.json. Valid: {valid}")

    # Override config with command-line arguments
    if args.test:
        test_mode = True
        search_start = 0
        search_end = 100000000
    else:
        test_mode = args.test if args.test is not None else cfg.get('test_mode', False)
        search_start = args.start if args.start is not None else cfg.get('start', 0)
        search_end = args.end if args.end is not None else cfg.get('end', 0xFFFFFFFF)
    
    low32 = args.low32 if args.low32 is not None else cfg.get('low32', LOW32)
    
    print("=" * 60)
    print("Minecraft Bedrock High 32-bit Seed Cracker")
    print("=" * 60)

    search_end_exclusive = search_end + 1

    # CRITICAL: Limit processes to prevent resource exhaustion
    # On high-core systems (>32 cores), using all cores causes:
    # - DLL loading conflicts (multiple processes loading same .so)
    # - Memory exhaustion
    # - Lock contention
    # Solution: Use max 8-16 processes regardless of core count

    # Priority: command-line args > config file > auto-detect
    if args.processes:
        max_processes = min(args.processes, 16)  # Never exceed 16
        if args.processes > 16:
            print(f"[WARNING] Limiting processes from {args.processes} to 16 (to prevent resource exhaustion)")
        source = "command-line"
    elif cfg.get('processes', None) is not None:
        max_processes = min(cfg.get('processes'), 16)  # Never exceed 16
        if cfg.get('processes') > 16:
            print(f"[WARNING] Limiting processes from {cfg.get('processes')} to 16 (to prevent resource exhaustion)")
        source = "config file"
    else:
        # Auto-limit: use min(cpu_count, 16), but never more than 1/4 of cores
        cpu_count = mp.cpu_count()
        max_processes = min(cpu_count, 16, max(1, cpu_count // 4))
        source = "auto-detect"

    print(f"\n[*] Low 32-bit: {low32}")
    print(f"[*] MC Version: {MC_VERSION_STR}")
    print(f"[*] Processes: {max_processes} ({source}, limited to 16)")
    if lcg_structures:
        print(f"[*] Java LCG structures: {len(lcg_structures)} (enables phase 2+3 mode)")
    else:
        print(f"[*] Java LCG structures: none (biome-only mode)")
    
    # Check biome version compatibility BEFORE strictness testing
    version_warnings = check_biome_version(SAMPLES, MC_VERSION_STR)
    if version_warnings:
        print(f"\n[!] Warning: Some biomes are not available in MC {MC_VERSION_STR}:")
        for w in version_warnings:
            print(w)
        print("[!] These samples will never match! Please update MC_VERSION_STR or remove these samples.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Skip strictness test if search range size < 100000 (test would be redundant)
    num_test_seeds = 100000
    skip_strictness = (search_end - search_start < num_test_seeds)

    if skip_strictness:
        print(f"\n[*] Search range size < {num_test_seeds:,} ({search_end - search_start}), skipping strictness test")
        sorted_samples = SAMPLES
        strictness_scores = []
        print(f"\n[*] Biome samples (strictness test skipped, range size < {num_test_seeds:,}):")
        for i, sample in enumerate(sorted_samples):
            if len(sample) == 4:
                x, z, y, biome_id = sample
            else:
                x, z, biome_id = sample
                y = 200
            print(f"    {i+1}. ({x}, {z}, Y={y}) -> {get_biome_name(biome_id)} (ID: {biome_id})")
    else:
        # Sort by empirical strictness (fewest matches = rarest = first)
        print(f"\n[*] Testing biome sample strictness (0-{num_test_seeds:,} high32 seeds)...")
        sorted_samples, strictness_scores = sort_samples_by_strictness(SAMPLES, low32, MC_VERSION, num_test_seeds=num_test_seeds)

        print(f"\n[*] Biome samples (sorted by strictness, rarest first):")
        for i, (sample, score) in enumerate(zip(sorted_samples, strictness_scores)):
            if len(sample) == 4:
                x, z, y, biome_id = sample
            else:
                x, z, biome_id = sample
                y = 200
            match_pct = score / num_test_seeds * 100
            print(f"    {i+1}. ({x}, {z}, Y={y}) -> {get_biome_name(biome_id)} (ID: {biome_id}) - {score}/{num_test_seeds} matches ({match_pct:.4f}%)")

    # ===== Java LCG phase 2+3 (if structures provided) =====
    if lcg_structures:
        print(f"\n{'=' * 60}")
        print("Phase 2: Java LCG brute-force bits 32-47 (2^16 candidates)")
        print(f"{'=' * 60}")
        print(f"  Structures: {len(lcg_structures)}")
        for s in lcg_structures:
            cfg_name = JAVA_LCG_STRUCTURES.get(s['type'], {}).get('name', s['type'])
            print(f"    {cfg_name}: ({s['x']}, {s['z']})")

        t0 = time.time()
        h16_candidates = crack_high16_java_lcg(low32, lcg_structures, search_start, search_end)
        elapsed_p2 = time.time() - t0

        print(f"\n  Phase 2 done in {elapsed_p2:.2f}s")
        print(f"  Found {len(h16_candidates)} candidate(s) for bits 32-47")

        if not h16_candidates:
            print("\n[!] Java LCG phase found no candidates. Check coordinates or use biome-only.")
            input("\nPress Enter to exit...")
            sys.exit(1)

        # Phase 3: Biome verify bits 48-63 per candidate
        print(f"\n{'=' * 60}")
        print("Phase 3: Biome verify bits 48-63 (2^16 per candidate)")
        print(f"{'=' * 60}")

        # Precompute valid upper ranges per candidate (high32 = (upper << 16) | h16)
        valid_candidates = []
        total_uppers = 0
        for h16 in h16_candidates:
            # Need start <= high32 <= end
            if search_end < h16:
                continue

            if search_start <= h16:
                min_upper = 0
            else:
                min_upper = (search_start - h16 + 65535) // 65536

            max_upper = min(0xFFFF, (search_end - h16) // 65536)

            if min_upper > max_upper:
                continue

            range_size = max_upper - min_upper + 1
            valid_candidates.append((h16, min_upper, max_upper, range_size))
            total_uppers += range_size

        # Parallel Phase 3: same spawn process pool as the normal path
        ctx = mp.get_context('spawn')
        print(f"\n[*] Initializing {max_processes} worker processes (using spawn)...")
        pool = ctx.Pool(max_processes)
        print("[*] Workers initialized! Starting biome verify...")

        tasks = [(h, low32, min_u, max_u, sorted_samples, MC_VERSION)
                 for (h, min_u, max_u, _rs) in valid_candidates]

        all_results = []
        found_count = 0
        done_uppers = 0
        start_time = time.time()
        bar_len = 30

        try:
            for i, results in enumerate(pool.imap(crack_batch_lcg_phase3, tasks)):
                h16, min_upper, max_upper, range_size = valid_candidates[i]
                done_uppers += range_size

                for seed in results:
                    all_results.append(seed)
                    found_count += 1
                    seed_info = format_seed_output(seed, low32)
                    sys.stdout.write('\r\033[K')
                    sys.stdout.flush()
                    print(seed_info)
                    with open(found_seeds_file, 'a', encoding='utf-8') as f:
                        f.write(seed_info + '\n')
                        f.write(f"Found at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("-" * 60 + '\n')

                # In-place progress with speed and ETA (same style as the normal path)
                progress = (i + 1) / len(valid_candidates) * 100
                elapsed = time.time() - start_time
                speed = done_uppers / elapsed if elapsed > 0 else 0
                eta = (total_uppers - done_uppers) / speed if speed > 0 else 0
                filled = int(bar_len * progress / 100)
                bar = '#' * filled + '-' * (bar_len - filled)
                sys.stdout.write(f"\r  [{bar}] {progress:.1f}% | Candidate {i+1}/{len(valid_candidates)} | {speed:,.0f}/s | ETA: {eta/60:.1f}min | Found: {found_count}")
                sys.stdout.flush()
        finally:
            pool.close()
            pool.join()

        # Clear the progress line after completion
        sys.stdout.write('\r\033[K')
        sys.stdout.flush()

        total_elapsed = time.time() - start_time
        print(f"\n{'=' * 60}")
        print("[Complete]")
        print(f"{'=' * 60}")
        print(f"  Phase 2 + 3 Time: {total_elapsed:.1f}s")
        print(f"  Found: {len(all_results)} seed(s)")

        if all_results:
            print("\n" + "=" * 60)
            print("All found seeds:")
            print("=" * 60)
            for seed in all_results:
                high32 = seed >> 32
                display_seed = to_signed64(seed)
                print(f"\n  Low 32-bit:  {low32} (0x{low32:08X})")
                print(f"  High 32-bit: {high32} (0x{high32:08X})")
                print(f"  Full seed:   {display_seed} (0x{seed:016X})")

        input("\nPress Enter to exit...")
        sys.exit(0)
    # ===== End Java LCG phase =====

    total_search = search_end - search_start + 1

    print(f"\n[*] Search range: {search_start:,} ~ {search_end:,}")
    print("-" * 60)
    print("[*] Cracking with SOA optimization (4 seeds per batch)...")
    print("-" * 60)

    all_results = []
    found_count = 0

    start_time = time.time()
    total_done = 0
    batch_size = BATCH_SIZE

    # Use 'spawn' context to avoid issues with fork and DLL loading
    # This is CRITICAL for stability on high-core systems
    ctx = mp.get_context('spawn')
    print(f"\n[*] Initializing {max_processes} worker processes (using spawn)...")
    pool = ctx.Pool(max_processes)
    print("[*] Workers initialized! Starting crack...")
    print("[*] Progress will be updated in real-time...")
    print(f"[*] Found seeds will be saved to: {found_seeds_file}\n")

    # Progress heartbeat: output progress even if no seeds found
    last_output_time = time.time()
    output_interval = 2.0  # Output progress every 2 seconds

    for batch_start in range(search_start, search_end_exclusive, batch_size * max_processes):
        batch_end = min(batch_start + batch_size * max_processes, search_end_exclusive)

        tasks = []
        chunk = batch_size
        for i in range(max_processes):
            start = batch_start + i * chunk
            end = start + chunk
            if start < batch_end:
                actual_end = min(end, batch_end)
                tasks.append((start, actual_end, low32, sorted_samples, 0, MC_VERSION))  # Y coord is now per-sample
        
        if tasks:
            for r in pool.imap_unordered(crack_batch_soa, tasks):
                if r:
                    for seed in r:
                        all_results.append(seed)
                        found_count += 1

                        # Format seed info
                        seed_info = format_seed_output(seed, low32)

                        # Clear current line before outputting seed info
                        sys.stdout.write('\r\033[K')  # Clear entire line
                        sys.stdout.flush()

                        # Print seed info to console
                        sys.stdout.write(seed_info + '\n')
                        sys.stdout.flush()

                        # Write to found seeds file
                        with open(found_seeds_file, 'a', encoding='utf-8') as f:
                            f.write(seed_info + '\n')
                            f.write(f"Found at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write("-" * 60 + '\n')

                # Progress heartbeat: output every 2 seconds even if batch is not complete
                current_time = time.time()
                if current_time - last_output_time >= output_interval:
                    elapsed = current_time - start_time
                    estimated_done = int(elapsed * speed) if 'speed' in dir() else total_done
                    percent = estimated_done / total_search * 100
                    bar_len = 30
                    filled = int(bar_len * percent / 100)
                    bar = '#' * filled + '-' * (bar_len - filled)
                    sys.stdout.write(f'\r  [{bar}] {percent:.1f}% | ~{estimated_done:,}/{total_search:,} | Working... | Found: {found_count}')
                    sys.stdout.flush()
                    last_output_time = current_time
        
        total_done = batch_end - search_start
        elapsed = time.time() - start_time
        speed = total_done / elapsed if elapsed > 0 else 0
        eta = (total_search - total_done) / speed if speed > 0 else 0
        percent = total_done / total_search * 100
        
        bar_len = 30
        filled = int(bar_len * percent / 100)
        bar = '#' * filled + '-' * (bar_len - filled)

        # Clear line before progress update to avoid artifacts
        sys.stdout.write('\r\033[K')  # Clear entire line
        sys.stdout.write(f'\r  [{bar}] {percent:.1f}% | {total_done:,}/{total_search:,} | {speed:,.0f}/s | ETA: {eta/60:.1f}min | Found: {found_count}')
        sys.stdout.flush()
        last_output_time = time.time()  # Reset heartbeat timer
    
    pool.close()
    pool.join()
    
    total_elapsed = time.time() - start_time
    total_speed = total_search / total_elapsed if total_elapsed > 0 else 0
    
    print(f"\n\n[Complete]")
    print(f"  Time: {total_elapsed:.1f}s ({total_elapsed/60:.1f}min)")
    print(f"  Speed: {total_speed:,.0f}/s")
    print(f"  Found: {len(all_results)} seed(s)")
    
    if all_results:
        print("\n" + "=" * 60)
        print("All found seeds:")
        print("=" * 60)
        for seed in all_results:
            high32 = seed >> 32
            display_seed = to_signed64(seed)
            print(f"\n  Low 32-bit:  {low32} (0x{low32:08X})")
            print(f"  High 32-bit: {high32} (0x{high32:08X})")
            print(f"  Full seed:   {display_seed} (0x{seed:016X})")
    
    print("\n" + "=" * 60)
    print("Search Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
