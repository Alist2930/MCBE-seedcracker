# -*- coding: utf-8 -*-
"""Minecraft Bedrock High 32-bit Seed Cracker (core).

Pure cracking logic shared by CLI, GUI and future frontends. Biome-sample
based search (SOA) plus the Java LCG two-phase mode (phase 2: bits 32-47,
phase 3: biome verify of bits 48-63).

Import-safe under multiprocessing spawn: importing this module never loads a
native library, reads config.json or starts a pool. All events are emitted
through a Reporter (see core.reporter); pause/stop is honored via Control.
"""
import ctypes
import time
import json
import signal
import multiprocessing as mp
from dataclasses import dataclass, field
from pathlib import Path

from . import config_loader
from .reporter import Reporter, Control

# Disable output buffering concerns belong to frontends; core never prints.

script_dir = Path(__file__).parent.resolve()

# Load biome data from biomes.json for ID->name mapping (display only)
_BIOME_DATA = None
_BIOME_ID_TO_NAME = {}


def _load_biome_data():
    """Load biome data from core/data/biomes.json (for ID->name display only)"""
    global _BIOME_DATA, _BIOME_ID_TO_NAME
    if _BIOME_DATA is not None:
        return
    biome_file = Path(__file__).parent / "data" / "biomes.json"
    if biome_file.exists():
        with open(biome_file, 'r', encoding='utf-8') as f:
            _BIOME_DATA = json.load(f)
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

# Batch size for multiprocessing
# Lower value = more frequent progress updates, but slightly slower
# Higher value = less frequent updates, but slightly faster
# Recommended: 100000-500000 for production, 10000-50000 for testing
BATCH_SIZE = 100000  # Reduced from 500000 for more frequent progress updates
MAX_RESULTS = 1000

# Sampling window (high32 values) for the pre-check that estimates the final
# candidate count before the full-range biome-only scan
SAMPLE_SEEDS_HIGH = 1 << 17

# ===== Java LCG constants (cubiomes-bedrock algorithm) =====
JLCG_K = 0x5DEECE66D
JLCG_M48 = (1 << 48) - 1
JLCG_B = 0xB
JLCG_A_REG = 341873128712
JLCG_B_REG = 132897987541

_JAVA_LCG_REGISTRY = None


def load_java_lcg_structures():
    """Load Java LCG structure configs from core/data/structures.json (cached).

    Returns {name: {'name_en', 'salt', 'spacing', 'separation'}} for the three
    Java LCG structures (Trail Ruins, Trial Chamber, Abandoned Camp).
    """
    global _JAVA_LCG_REGISTRY
    if _JAVA_LCG_REGISTRY is None:
        registry_file = Path(__file__).parent / "data" / "structures.json"
        with open(registry_file, "r", encoding="utf-8") as f:
            registry = json.load(f)
        _JAVA_LCG_REGISTRY = {
            name: cfg for name, cfg in registry.items()
            if cfg.get("rng_type") == "java_lcg"
        }
    return _JAVA_LCG_REGISTRY


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


class BiomeSample(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("z", ctypes.c_int), ("y", ctypes.c_int), ("biome_id", ctypes.c_int)]


def init_dll():
    """Load the crack_high32 native library (lazy, called inside workers only)."""
    dll_path = config_loader.resolve_native_lib(config_loader.native_dir(), "crack_high32")
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


def _worker_init():
    # Spawned workers must ignore Ctrl+C: on Windows the console delivers
    # CTRL_C_EVENT to every process in the group, and a worker interrupted
    # mid-startup dies with "Fatal Python error: init_sys_streams" spam.
    # The parent handles KeyboardInterrupt and terminates the pool instead.
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def normalize_mc_version(mc_version_str, warn=None):
    """Validate and normalize an MC version string.

    Returns (normalized_str, cubiomes_version_constant). Unknown versions
    partially match on major.minor, else fall back to the latest (26.50).
    """
    if mc_version_str not in VERSION_MAP:
        # Try partial match (e.g., '1.21.60' matches '1.21.60-26.23')
        parts = mc_version_str.split('.')
        matched = None
        if len(parts) >= 2:
            major_minor = f"{parts[0]}.{parts[1]}"
            for ver_key in VERSION_MAP:
                if ver_key.startswith(major_minor):
                    matched = ver_key
                    break
        if matched:
            if warn:
                warn(f"MC version '{mc_version_str}' matched to '{matched}'")
            mc_version_str = matched
        else:
            if warn:
                warn(f"Unknown MC version '{mc_version_str}', defaulting to '26.50'")
            mc_version_str = "26.50"
    return mc_version_str, VERSION_MAP[mc_version_str]


def test_sample_strictness(sample, low32, mc_version, num_test_seeds=100000):
    """
    Test the strictness (matching probability) of a biome sample.
    Tests num_test_seeds high32 candidates and counts how many produce the target biome.
    Returns the match count (lower = stricter = rarer = higher priority).
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


def check_biome_version(samples, mc_version_str):
    """
    Check if all biome samples are compatible with the current MC version
    Returns warning lines for incompatible biomes.
    Sample format: (x, z, y, biome_id) or legacy (x, z, biome_id)
    """
    # Version order for comparison (use small versions)
    version_order = ['1.18', '1.19', '1.20.0-51', '1.20.60-81', '1.21-1.21.40', '1.21.50', '1.21.60-26.23', '26.30-26.40', '26.50']
    mc_idx = version_order.index(mc_version_str) if mc_version_str in version_order else len(version_order) - 1
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
            warnings.append(f"  ({x}, {z}) -> {biome_name} (ID: {biome_id}) requires {biome_version}+, but current version is {mc_version_str}")

    return warnings


def check_biome_conflicts(samples):
    """Detect contradictory samples: one (x, z, y) point cannot hold two biomes.

    Returns a list of human-readable conflict lines (empty when valid).
    """
    point_biomes = {}
    for sample in samples:
        if len(sample) == 4:
            x, z, y, biome_id = sample
        else:
            x, z, biome_id = sample
            y = 200
        ids = point_biomes.setdefault((x, z, y), [])
        if biome_id not in ids:
            ids.append(biome_id)
    conflict_lines = []
    for (x, z, y), ids in point_biomes.items():
        if len(ids) > 1:
            joined = ", ".join(f"{get_biome_name(bid)} (ID: {bid})" for bid in sorted(ids))
            conflict_lines.append(f"({x}, {z}, Y={y}): {joined}")
    return conflict_lines


def crack_batch_soa(args):
    start_high, end_high, low32, samples, y_coord, mc_version = args
    dll = init_dll()

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
    java_lcg_configs = load_java_lcg_structures()

    # Prepare constraints: per-structure list of 4 (r_const, target_ox, target_oz) offsets.
    # 4-chunk grid: a player-reported coordinate may correspond to one of 4 origin chunks:
    # (cx,cz), (cx,cz+1), (cx+1,cz), (cx+1,cz+1). A structure matches if ANY offset matches.
    structure_constraints = []  # [(chunk_range, [(r_const, target_ox, target_oz), ...4]), ...]
    for s in lcg_structures:
        stype = s.get('type')
        config = java_lcg_configs.get(stype)
        if not config:
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


def estimate_candidate_count_high32(search_start, total_span, sorted_samples, low32, mc_version, num_processes):
    """Sampling pre-check for biome-only mode: scan a small high32 window with the
    same worker as the real scan (crack_batch_soa) and extrapolate the candidate
    count over the full range.

    Returns (predicted, sampled_found, saturated): saturated is True when a
    worker hit its MAX_RESULTS buffer cap, meaning the real count is far higher
    than the extrapolation.
    """
    sample_span = min(total_span, SAMPLE_SEEDS_HIGH)
    sample_end_exclusive = search_start + sample_span

    pool = mp.get_context('spawn').Pool(num_processes, initializer=_worker_init)
    sampled_found = 0
    saturated = False
    try:
        chunk = max(1, sample_span // num_processes)
        pos = search_start
        while pos < sample_end_exclusive and not saturated:
            tasks = []
            for i in range(num_processes):
                s = pos + i * chunk
                e = min(pos + (i + 1) * chunk, sample_end_exclusive) if i < num_processes - 1 else sample_end_exclusive
                if s < e:
                    tasks.append((s, e, low32, sorted_samples, 0, mc_version))
            if tasks:
                for found in pool.map(crack_batch_soa, tasks):
                    sampled_found += len(found)
                    if len(found) >= MAX_RESULTS:  # worker result buffer cap reached
                        saturated = True
            pos += chunk * num_processes
    finally:
        pool.terminate()
        pool.join()

    predicted = round(sampled_found * total_span / sample_span)
    return predicted, sampled_found, saturated


def resolve_processes_high32(cfg, requested=None, reporter=None):
    """Resolve the CPU process count for high32 (auto-limit: min(cores, 16, cores/4))."""
    if requested:
        num_processes = min(requested, 16)  # Never exceed 16
        if requested > 16 and reporter:
            reporter.warn(f"Limiting processes from {requested} to 16 (to prevent resource exhaustion)")
        source = "command-line"
    elif cfg.get('processes', None) is not None:
        num_processes = min(cfg.get('processes'), 16)  # Never exceed 16
        if cfg.get('processes') > 16 and reporter:
            reporter.warn(f"Limiting processes from {cfg.get('processes')} to 16 (to prevent resource exhaustion)")
        source = "config file"
    else:
        # Auto-limit: use min(cpu_count, 16), but never more than 1/4 of cores
        cpu_count = mp.cpu_count()
        num_processes = min(cpu_count, 16, max(1, cpu_count // 4))
        source = "auto-detect"

    if reporter:
        reporter.info(f"Processes: {num_processes} ({source}, limited to 16)")
    return num_processes


@dataclass
class PreparedSamples:
    """Sorted biome samples plus strictness scores (biome-only scan input)."""
    samples: list = field(default_factory=list)  # [(x, z, y, biome_id), ...]
    scores: list = field(default_factory=list)
    sample_info: list = field(default_factory=list)  # display dicts
    has_zero_sample: bool = False


def prepare_samples(samples, low32, mc_version_str, mc_version, skip_strictness=False, reporter=None):
    """Sort biome samples by strictness and build display info.

    Returns PreparedSamples. Emits strictness details and the sample listing
    through the reporter.
    """
    if reporter is None:
        reporter = Reporter()

    num_test_seeds = 100000
    prep = PreparedSamples()

    if skip_strictness:
        reporter.info(f"Search range size < {num_test_seeds:,}, skipping strictness test")
        prep.samples = list(samples)
        prep.scores = []
        reporter.info(f"Biome samples (strictness test skipped, range size < {num_test_seeds:,}):")
        for i, sample in enumerate(prep.samples):
            x, z, y, biome_id = _sample_xyz(sample)
            reporter.detail(f"    {i+1}. ({x}, {z}, Y={y}) -> {get_biome_name(biome_id)} (ID: {biome_id})")
    else:
        # Sort by empirical strictness (fewest matches = rarest = first)
        reporter.info(f"Testing biome sample strictness (0-{num_test_seeds:,} high32 seeds)...")
        prep.samples, prep.scores = sort_samples_by_strictness(samples, low32, mc_version, num_test_seeds=num_test_seeds)

        reporter.info("Biome samples (sorted by strictness, rarest first):")
        for i, (sample, score) in enumerate(zip(prep.samples, prep.scores)):
            x, z, y, biome_id = _sample_xyz(sample)
            match_pct = score / num_test_seeds * 100
            reporter.detail(f"    {i+1}. ({x}, {z}, Y={y}) -> {get_biome_name(biome_id)} (ID: {biome_id}) - {score}/{num_test_seeds} matches ({match_pct:.4f}%)")
            if score == 0:
                prep.has_zero_sample = True
                reporter.warn(f"Sample ({x}, {z}, Y={y}) {get_biome_name(biome_id)} (ID: {biome_id}) matched 0/{num_test_seeds} test seeds - it may be invalid, check coordinates/type!")

    reporter.sample_info(prep.samples, prep.scores)

    return prep


def _sample_xyz(sample):
    """Normalize a sample tuple to (x, z, y, biome_id)."""
    if len(sample) == 4:
        return sample
    x, z, biome_id = sample
    return (x, z, 200, biome_id)


def run_cpu(prep, low32, mc_version, search_start, search_end, num_processes, reporter=None, control=None):
    """Biome-only SOA scan over a contiguous high32 range.

    Returns (results, elapsed). Honors control.should_stop() between batches.
    """
    if reporter is None:
        reporter = Reporter()
    if control is None:
        control = Control()

    search_end_exclusive = search_end + 1
    total_search = search_end - search_start + 1

    all_results = []
    found_count = 0

    start_time = time.time()
    total_done = 0
    batch_size = BATCH_SIZE

    pool = mp.get_context('spawn').Pool(num_processes, initializer=_worker_init)
    reporter.info(f"Initializing {num_processes} worker processes (using spawn)...")
    reporter.info("Workers initialized! Starting crack...")

    try:
        for batch_start in range(search_start, search_end_exclusive, batch_size * num_processes):
            control.wait_if_paused()
            if control.should_stop():
                break
            batch_end = min(batch_start + batch_size * num_processes, search_end_exclusive)

            tasks = []
            chunk = batch_size
            for i in range(num_processes):
                start = batch_start + i * chunk
                end = start + chunk
                if start < batch_end:
                    actual_end = min(end, batch_end)
                    tasks.append((start, actual_end, low32, prep.samples, 0, mc_version))  # Y coord is now per-sample

            if tasks:
                for r in pool.imap_unordered(crack_batch_soa, tasks):
                    for seed in r:
                        all_results.append(seed)
                        found_count += 1
                        reporter.result(seed)

            total_done = batch_end - search_start
            elapsed = time.time() - start_time
            speed = total_done / elapsed if elapsed > 0 else 0
            eta = (total_search - total_done) / speed if speed > 0 else 0
            reporter.progress(total_done, total_search, speed, eta, found=found_count)
    finally:
        pool.terminate()
        pool.join()

    return all_results, time.time() - start_time


def run_lcg(prep, low32, lcg_structures, search_start, search_end, num_processes, mc_version, reporter=None, control=None):
    """Java LCG two-phase mode: phase 2 (bits 32-47) then phase 3 (biome verify).

    Returns (results, elapsed_phase3). Raises ValueError when phase 2 finds no
    candidates or when no LCG structure is usable.
    """
    if reporter is None:
        reporter = Reporter()
    if control is None:
        control = Control()

    reporter.info(f"Phase 2: Java LCG brute-force bits 32-47 (2^16 candidates)")
    reporter.info(f"  Structures: {len(lcg_structures)}")
    java_lcg_configs = load_java_lcg_structures()
    for s in lcg_structures:
        cfg_name = java_lcg_configs.get(s['type'], {}).get('name_en', s['type'])
        reporter.detail(f"    {cfg_name}: ({s['x']}, {s['z']})")

    t0 = time.time()
    h16_candidates = crack_high16_java_lcg(low32, lcg_structures, search_start, search_end)
    elapsed_p2 = time.time() - t0

    reporter.info(f"  Phase 2 done in {elapsed_p2:.2f}s")
    reporter.info(f"  Found {len(h16_candidates)} candidate(s) for bits 32-47")

    if not h16_candidates:
        raise ValueError("Java LCG phase found no candidates. Check coordinates or use biome-only mode.")

    # Phase 3: Biome verify bits 48-63 per candidate
    reporter.info("Phase 3: Biome verify bits 48-63 (2^16 per candidate)")

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
    reporter.info(f"Initializing {num_processes} worker processes (using spawn)...")
    pool = mp.get_context('spawn').Pool(num_processes, initializer=_worker_init)
    reporter.info("Workers initialized! Starting biome verify...")

    tasks = [(h, low32, min_u, max_u, prep.samples, mc_version)
             for (h, min_u, max_u, _rs) in valid_candidates]

    all_results = []
    found_count = 0
    done_uppers = 0
    start_time = time.time()

    try:
        for i, results in enumerate(pool.imap(crack_batch_lcg_phase3, tasks)):
            h16, min_upper, max_upper, range_size = valid_candidates[i]
            done_uppers += range_size

            for seed in results:
                all_results.append(seed)
                found_count += 1
                reporter.result(seed)

            # Progress with speed and ETA (same style as the normal path)
            elapsed = time.time() - start_time
            speed = done_uppers / elapsed if elapsed > 0 else 0
            eta = (total_uppers - done_uppers) / speed if speed > 0 else 0
            note = f"Candidate {i+1}/{len(valid_candidates)}"
            reporter.progress(done_uppers, total_uppers, speed, eta, found=found_count, note=note)
    finally:
        pool.terminate()
        pool.join()

    return all_results, time.time() - start_time


def run_high32(cfg, samples, low32, mc_version_str, search_start, search_end,
               lcg_structures=None, requested_processes=None, reporter=None, control=None):
    """High-level high32 orchestration shared by all frontends.

    Normalizes the MC version, validates samples (conflicts, version
    compatibility), resolves processes, optionally runs the Java LCG two-phase
    mode, estimates the candidate count (biome-only mode) and cracks.

    Returns (results, elapsed). Raises ValueError/RuntimeError on invalid input.
    """
    if reporter is None:
        reporter = Reporter()
    if control is None:
        control = Control()
    if lcg_structures is None:
        lcg_structures = []

    # Validate and normalize MC version
    mc_version_str, mc_version = normalize_mc_version(mc_version_str, warn=reporter.warn)

    num_processes = resolve_processes_high32(cfg, requested=requested_processes, reporter=reporter)

    reporter.info(f"Low 32-bit: {low32}")
    reporter.info(f"MC Version: {mc_version_str}")
    if lcg_structures:
        reporter.info(f"Java LCG structures: {len(lcg_structures)} (enables phase 2+3 mode)")
    else:
        reporter.info(f"Java LCG structures: none (biome-only mode)")

    # A single (x, z, y) point cannot hold two different biomes - block contradictory input
    conflict_lines = check_biome_conflicts(samples)
    if conflict_lines:
        raise ValueError(
            "The following sample points have multiple different biomes "
            "(one point cannot hold multiple biomes):\n    "
            + "\n    ".join(conflict_lines)
            + "\nRemove or fix the contradictory samples and retry!")

    # Check biome version compatibility BEFORE strictness testing
    version_warnings = check_biome_version(samples, mc_version_str)
    if version_warnings:
        raise ValueError(
            f"Some biomes are not available in MC {mc_version_str}:\n"
            + "\n".join(version_warnings)
            + "\nThese samples will never match! Please update mc_version or remove these samples.")

    # Skip strictness test if search range size < 100000 (test would be redundant)
    skip_strictness = (search_end - search_start < 100000)
    prep = prepare_samples(samples, low32, mc_version_str, mc_version,
                           skip_strictness=skip_strictness, reporter=reporter)

    # ===== Java LCG phase 2+3 (if structures provided) =====
    if lcg_structures:
        return run_lcg(prep, low32, lcg_structures, search_start, search_end,
                       num_processes, mc_version, reporter=reporter, control=control)

    # Sampling pre-check: estimate the final candidate count before the full scan
    total_span = search_end - search_start + 1
    if total_span > SAMPLE_SEEDS_HIGH:
        try:
            reporter.info(f"Estimating candidate count (sampling {SAMPLE_SEEDS_HIGH:,} high32 values)...")
            predicted, sampled, saturated = estimate_candidate_count_high32(
                search_start, total_span, prep.samples, low32, mc_version, num_processes)
            reporter.estimation({'predicted': predicted, 'sampled': sampled,
                                 'saturated': saturated, 'has_zero_sample': prep.has_zero_sample})
        except Exception as e:
            reporter.warn(f"Candidate estimation skipped: {e}")

    reporter.info("Cracking with SOA optimization (4 seeds per batch)...")

    return run_cpu(prep, low32, mc_version, search_start, search_end, num_processes,
                   reporter=reporter, control=control)
