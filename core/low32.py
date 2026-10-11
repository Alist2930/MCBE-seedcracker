# -*- coding: utf-8 -*-
"""Minecraft Bedrock Low 32-bit Seed Cracker (core).

Pure cracking logic shared by CLI, GUI and future frontends. Supports both
CPU (multiprocessing) and GPU (OpenCL) acceleration.

Import-safe under multiprocessing spawn: importing this module never loads a
native library, reads config.json or starts a pool. All events are emitted
through a Reporter (see core.reporter); pause/stop is honored via Control.
"""
import ctypes
import time
import json
import multiprocessing as mp
import os
import signal
from dataclasses import dataclass, field
from pathlib import Path

from . import config_loader
from .reporter import Reporter, Control

CONST_A = 2570712328
CONST_B = 4048968661

# 4-chunk grid: a player-reported coordinate may correspond to one of 4 origin chunks:
# (cx,cz), (cx,cz+1), (cx+1,cz), (cx+1,cz+1).
# Only structures with complex generation rules need the grid; others use the exact
# origin chunk (single offset repeated to fill the uniform NUM_OFFSETS slots).
NUM_OFFSETS = 4
FOUR_GRID_STRUCTURES = {"village", "igloo", "pillager_outpost", "ruined_portal_overworld", "ruined_portal_nether"}

# Sampling window (seeds) for the pre-check that estimates the total candidate
# count before the full-range scan; skipped when the search range is smaller
SAMPLE_SEEDS = 1 << 24

_REGISTRY = None


def load_structure_registry():
    """Load the structure registry from core/data/structures.json (cached).

    Returns the full registry dict keyed by structure name. Regular structures
    carry salt/spacing/separation/spread_type; special (decoration RNG)
    structures carry special=true, sp_type, salt and rarity; Java LCG
    structures (high32-only) carry rng_type='java_lcg'.
    """
    global _REGISTRY
    if _REGISTRY is None:
        path = Path(__file__).resolve().parent / "data" / "structures.json"
        with open(path, "r", encoding="utf-8") as f:
            _REGISTRY = json.load(f)
    return _REGISTRY


def _low32_structures():
    """Split the registry into (regular, special) configs usable by the low32 path.

    Java LCG structures are high32-only and excluded from both.
    """
    regular, special = {}, {}
    for name, cfg in load_structure_registry().items():
        if cfg.get("rng_type") == "java_lcg":
            continue
        if cfg.get("special"):
            special[name] = cfg
        else:
            regular[name] = cfg
    return regular, special


@dataclass
class PreparedTargets:
    """Flattened cracking parameters produced by prepare_targets.

    All fields are plain lists/dicts of ints/strs so worker task tuples stay
    picklable under spawn.
    """
    r_base: list = field(default_factory=list)
    ox: list = field(default_factory=list)
    oz: list = field(default_factory=list)
    offset_range: list = field(default_factory=list)
    spread_type: list = field(default_factory=list)
    structure_info: list = field(default_factory=list)
    num_offsets: int = 1
    has_zero_sample: bool = False
    sp_type: list = field(default_factory=list)
    sp_cx: list = field(default_factory=list)
    sp_cz: list = field(default_factory=list)
    sp_dx: list = field(default_factory=list)
    sp_dz: list = field(default_factory=list)
    special_info: list = field(default_factory=list)


def has_opencl_gpu(reporter=None):
    """Check if OpenCL GPU is available. Returns (available, device_info_str)."""
    try:
        opencl_lib = config_loader.resolve_native_lib(config_loader.native_dir(), 'crack_low32_opencl')

        lib = ctypes.CDLL(str(opencl_lib))

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
            if reporter:
                reporter.info(f"GPU compute units: {compute_units}")

            # GPUs with <10 compute units are considered too old for GPU acceleration
            if compute_units < 10:
                if reporter:
                    reporter.warn(f"GPU has only {compute_units} compute units (too old for GPU mode)")
                    reporter.info("Recommending CPU mode for this GPU")
                return False, f"{gpu_info} (old GPU, use CPU mode)"

            return True, gpu_info

        return False, "No OpenCL GPU found"
    except Exception as e:
        return False, str(e)


def test_sample_strictness(structure, config, x, z, num_test_seeds=100000, reporter=None):
    """
    Test the strictness (matching probability) of a structure sample.
    Returns the number of matches in num_test_seeds attempts.

    4-chunk grid structures match if ANY of the 4 origin chunks produces the
    target (ox, oz); other structures match the exact origin chunk only.
    """
    spacing = config["spacing"]
    separation = config["separation"]

    cx, cz = x >> 4, z >> 4
    offset_range = spacing - separation
    spread_type_int = 1 if config.get("spread_type", "linear") == "triangular" else 0

    # Grid structures: 4 origin chunks; others: exact origin chunk only
    use_grid = structure in FOUR_GRID_STRUCTURES
    num_offsets = NUM_OFFSETS if use_grid else 1
    r_base_vals, ox_vals, oz_vals = [], [], []
    for dx in ([0, 1] if use_grid else [0]):
        for dz in ([0, 1] if use_grid else [0]):
            origin_cx = cx + dx
            origin_cz = cz + dz
            rx = origin_cx // spacing
            rz = origin_cz // spacing
            ox_vals.append(origin_cx % spacing)
            oz_vals.append(origin_cz % spacing)
            r_base_vals.append((rx * CONST_A + rz * CONST_B + config["salt"]) & 0xFFFFFFFF)

    # Load C library for fast testing
    try:
        lib_path = config_loader.resolve_native_lib(config_loader.native_dir(), 'crack_low32')
        lib = ctypes.CDLL(str(lib_path))
        lib.crack_low32_grid.argtypes = [
            ctypes.c_uint32, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
        ]
        lib.crack_low32_grid.restype = ctypes.c_int

        r_base_arr = (ctypes.c_uint32 * num_offsets)(*r_base_vals)
        ox_arr = (ctypes.c_uint32 * num_offsets)(*ox_vals)
        oz_arr = (ctypes.c_uint32 * num_offsets)(*oz_vals)
        offset_range_arr = (ctypes.c_uint32 * 1)(offset_range)
        spread_type_arr = (ctypes.c_int * 1)(spread_type_int)
        results_arr = (ctypes.c_uint32 * num_test_seeds)()

        found = lib.crack_low32_grid(
            0, num_test_seeds,
            r_base_arr, ox_arr, oz_arr, offset_range_arr, spread_type_arr,
            1, num_offsets,  # num_structures=1, num_offsets per grid membership
            results_arr, num_test_seeds
        )

        return found
    except Exception as e:
        if reporter:
            reporter.warn(f"Failed to test strictness with C library: {e}")
        return 0


def test_special_strictness(sp_type, cx, cz, dx, dz, reporter=None):
    """Test strictness of a special (decoration RNG) sample.

    Desert wells match only 1/128000 seeds, so they need a larger test
    window (2^20) than regular structures; geodes (1/24) use 100000.

    Returns (matches, num_test_seeds).
    """
    num_test_seeds = (1 << 20) if sp_type == 0 else 100000
    try:
        lib_path = config_loader.resolve_native_lib(config_loader.native_dir(), 'crack_low32')
        lib = ctypes.CDLL(str(lib_path))
        lib.crack_low32_grid_special.argtypes = [
            ctypes.c_uint32, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int), ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
        ]
        lib.crack_low32_grid_special.restype = ctypes.c_int

        sp_type_arr = (ctypes.c_int * 1)(sp_type)
        sp_cx_arr = (ctypes.c_int * 1)(cx)
        sp_cz_arr = (ctypes.c_int * 1)(cz)
        sp_dx_arr = (ctypes.c_int * 1)(dx)
        sp_dz_arr = (ctypes.c_int * 1)(dz)
        results_arr = (ctypes.c_uint32 * num_test_seeds)()

        # Special-only test: num_structures=0 skips the regular structure loop
        found = lib.crack_low32_grid_special(
            0, num_test_seeds,
            None, None, None, None, None, 0, 1,
            sp_type_arr, sp_cx_arr, sp_cz_arr, sp_dx_arr, sp_dz_arr, 1,
            results_arr, num_test_seeds)

        if found < 0:
            raise RuntimeError(f"crack_low32_grid_special failed (return code {found})")
        return found, num_test_seeds
    except Exception as e:
        if reporter:
            reporter.warn(f"Failed to test strictness with C library: {e}")
        return 0, num_test_seeds


def prepare_targets(targets, skip_strictness=False, reporter=None):
    """Validate targets, compute flattened cracking parameters and test strictness.

    Returns a PreparedTargets with lists sorted strictest-first (linear group
    before triangular group; special samples strictest first).
    """
    structure_configs, special_configs = _low32_structures()

    # Validate all structure names first (regular + special)
    invalid_structures = []
    for i, t in enumerate(targets):
        structure_name = t.get("structure")
        if not structure_name:
            raise ValueError(f"Target {i} missing 'structure' field")
        if structure_name not in structure_configs and structure_name not in special_configs:
            invalid_structures.append(structure_name)

    if invalid_structures:
        valid_structures = ", ".join(sorted(structure_configs.keys()) + sorted(special_configs.keys()))
        raise ValueError(
            f"Invalid structure name(s): {', '.join(invalid_structures)}\n"
            f"Valid structures are: {valid_structures}"
        )

    # Split into regular (structure RNG) and special (decoration RNG) targets
    special_targets = [t for t in targets if t["structure"] in special_configs]
    targets = [t for t in targets if t["structure"] in structure_configs]

    # First sort by spread_type (linear first)
    sorted_targets = sorted(targets, key=lambda t: 0 if structure_configs[t["structure"]].get("spread_type", "linear") == "linear" else 1)

    # Calculate parameters for all targets
    # r_base/ox/oz are flattened: [num_targets * num_offsets]
    # offset_range/spread_type/structure_info are per-target: [num_targets]
    # If no target needs the 4-chunk grid, use num_offsets=1 (saves 4x MT19937 work in C/GPU)
    any_grid = any(t["structure"] in FOUR_GRID_STRUCTURES for t in targets)
    num_offsets = NUM_OFFSETS if any_grid else 1
    prep = PreparedTargets(num_offsets=num_offsets)
    r_base_list, ox_list, oz_list = [], [], []
    offset_range_list, spread_type_list, structure_info = [], [], []

    for t in sorted_targets:
        config = structure_configs[t["structure"]]
        x, z = t["x"], t["z"]
        spacing, separation = config["spacing"], config["separation"]

        cx, cz = x >> 4, z >> 4
        spread_type_int = 1 if config.get("spread_type", "linear") == "triangular" else 0

        # Grid structures: 4 origin chunks (cx,cz), (cx,cz+1), (cx+1,cz), (cx+1,cz+1)
        # Others: exact origin chunk only (repeated only when some structure uses the grid,
        # to keep the uniform num_offsets layout required by the C/OpenCL interface)
        use_grid = t["structure"] in FOUR_GRID_STRUCTURES
        first_rx = first_rz = None
        for dx in ([0, 1] if use_grid else [0]):
            for dz in ([0, 1] if use_grid else [0]):
                origin_cx = cx + dx
                origin_cz = cz + dz
                rx = origin_cx // spacing
                rz = origin_cz // spacing
                ox = origin_cx % spacing
                oz = origin_cz % spacing
                r_base = (rx * CONST_A + rz * CONST_B + config["salt"]) & 0xFFFFFFFF
                r_base_list.append(r_base)
                ox_list.append(ox)
                oz_list.append(oz)
                if first_rx is None:
                    first_rx, first_rz = rx, rz

        if not use_grid and num_offsets > 1:
            # Repeat the single exact-chunk offset to fill num_offsets slots
            r_base_list.extend([r_base_list[-1]] * (num_offsets - 1))
            ox_list.extend([ox_list[-1]] * (num_offsets - 1))
            oz_list.extend([oz_list[-1]] * (num_offsets - 1))

        offset_range_list.append(spacing - separation)
        spread_type_list.append(spread_type_int)
        structure_info.append({"name": config.get("name_en", t["structure"]), "name_zh": config.get("name_zh", ""),
                               "x": x, "z": z, "rx": first_rx, "rz": first_rz,
                               "spread_type": config.get("spread_type", "linear"), "grid": use_grid})

    # Test strictness and sort (strictest first)
    # Skip if requested (when search range size < 100000)
    strictness_scores = []

    if skip_strictness:
        if reporter:
            reporter.info("Search range size < 100000, skipping strictness test")
        strictness_scores = [0] * len(sorted_targets)
    else:
        if reporter:
            reporter.info(f"Testing sample strictness ({len(sorted_targets)} samples, 100000 seeds each):")
        for i, t in enumerate(sorted_targets):
            config = structure_configs[t["structure"]]
            x, z = t["x"], t["z"]
            spread_name = "triangular" if config.get("spread_type", "linear") == "triangular" else "linear"

            matches = test_sample_strictness(t["structure"], config, x, z, num_test_seeds=100000, reporter=reporter)
            strictness_scores.append(matches)
            rate = matches / 100000 * 100
            if reporter:
                reporter.detail(f"    {i + 1}. {config.get('name_en', t['structure'])} at ({x}, {z}): {matches}/100000 matches ({rate:.4f}%) [{spread_name}]")
            if matches == 0:
                prep.has_zero_sample = True
                if reporter:
                    reporter.warn(f"Sample {config.get('name_en', t['structure'])} at ({x}, {z}) matched 0/100000 test seeds - it may be invalid, check coordinates/type!")

    # Sort by strictness (fewer matches = stricter = higher priority)
    # But maintain linear-first ordering
    indices = list(range(len(sorted_targets)))

    # Separate linear and triangular
    linear_indices = [i for i in indices if spread_type_list[i] == 0]
    triangular_indices = [i for i in indices if spread_type_list[i] == 1]

    # Sort each group by strictness (ascending = stricter first)
    # When skip_strictness, all scores are 0 so sort is a no-op (stable sort preserves order)
    linear_indices.sort(key=lambda i: strictness_scores[i])
    triangular_indices.sort(key=lambda i: strictness_scores[i])

    # Combine: linear first, then triangular
    sorted_indices = linear_indices + triangular_indices

    # Reorder all lists (r_base/ox/oz are flattened with num_offsets entries per target)
    prep.r_base = [v for i in sorted_indices for v in r_base_list[i*num_offsets:(i+1)*num_offsets]]
    prep.ox = [v for i in sorted_indices for v in ox_list[i*num_offsets:(i+1)*num_offsets]]
    prep.oz = [v for i in sorted_indices for v in oz_list[i*num_offsets:(i+1)*num_offsets]]
    prep.offset_range = [offset_range_list[i] for i in sorted_indices]
    prep.spread_type = [spread_type_list[i] for i in sorted_indices]
    prep.structure_info = [structure_info[i] for i in sorted_indices]

    # Special (decoration RNG) targets: sort strictest first (well 1/128000 before geode 1/24)
    special_sorted = sorted(special_targets, key=lambda t: -special_configs[t["structure"]]["rarity"])

    for t in special_sorted:
        config = special_configs[t["structure"]]
        x, z = t["x"], t["z"]
        sp_type = config["sp_type"]
        # Wells: /tp coordinates are the exact anchor -> chunk origin + (dx, dz);
        # geodes: any block inside the geode -> origin chunk only, offsets unused
        sp_cx, sp_cz = x >> 4, z >> 4
        sp_dx, sp_dz = (x & 15, z & 15) if sp_type == 0 else (0, 0)

        if not skip_strictness:
            matches, num_test = test_special_strictness(sp_type, sp_cx, sp_cz, sp_dx, sp_dz, reporter=reporter)
            if matches == 0:
                prep.has_zero_sample = True
                if reporter:
                    reporter.warn(f"Sample {config.get('name_en', t['structure'])} at ({x}, {z}) matched 0/{num_test} test seeds - it may be invalid, check coordinates/type!")

        prep.sp_type.append(sp_type)
        prep.sp_cx.append(sp_cx)
        prep.sp_cz.append(sp_cz)
        prep.sp_dx.append(sp_dx)
        prep.sp_dz.append(sp_dz)
        prep.special_info.append({"name": config.get("name_en", t["structure"]), "name_zh": config.get("name_zh", ""),
                                  "x": x, "z": z, "sp_type": sp_type})

    return prep


def crack_worker_cpu(args):
    """CPU worker for multiprocessing (regular structures + special decoration samples).

    Module-level and fully picklable: args is a tuple of ints and int lists.
    """
    (start, end, r_base, ox, oz, offset_range, spread_type, num_offsets,
     sp_type, sp_cx, sp_cz, sp_dx, sp_dz) = args

    lib_path = config_loader.resolve_native_lib(config_loader.native_dir(), 'crack_low32')

    lib = ctypes.CDLL(str(lib_path))

    lib.crack_low32_grid_special.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
        ctypes.POINTER(ctypes.c_int), ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
    ]
    lib.crack_low32_grid_special.restype = ctypes.c_int

    num_structures = len(offset_range)
    grid_count = num_structures * num_offsets
    r_base_arr = (ctypes.c_uint32 * grid_count)(*r_base) if num_structures > 0 else None
    ox_arr = (ctypes.c_uint32 * grid_count)(*ox) if num_structures > 0 else None
    oz_arr = (ctypes.c_uint32 * grid_count)(*oz) if num_structures > 0 else None
    offset_range_arr = (ctypes.c_uint32 * num_structures)(*offset_range) if num_structures > 0 else None
    spread_type_arr = (ctypes.c_int * num_structures)(*spread_type) if num_structures > 0 else None

    num_special = len(sp_type)
    sp_type_arr = (ctypes.c_int * num_special)(*sp_type) if num_special > 0 else None
    sp_cx_arr = (ctypes.c_int * num_special)(*sp_cx) if num_special > 0 else None
    sp_cz_arr = (ctypes.c_int * num_special)(*sp_cz) if num_special > 0 else None
    sp_dx_arr = (ctypes.c_int * num_special)(*sp_dx) if num_special > 0 else None
    sp_dz_arr = (ctypes.c_int * num_special)(*sp_dz) if num_special > 0 else None

    results_arr = (ctypes.c_uint32 * 1000)()

    found = lib.crack_low32_grid_special(
        start, end, r_base_arr, ox_arr, oz_arr, offset_range_arr, spread_type_arr,
        num_structures, num_offsets,
        sp_type_arr, sp_cx_arr, sp_cz_arr, sp_dx_arr, sp_dz_arr, num_special,
        results_arr, 1000)

    # Check for native function errors
    if found < 0:
        raise RuntimeError(f"crack_low32_grid_special failed for range {start}-{end} (return code {found})")

    return [results_arr[i] for i in range(found)]


def _worker_init():
    # Spawned workers must ignore Ctrl+C: on Windows the console delivers
    # CTRL_C_EVENT to every process in the group, and a worker interrupted
    # mid-startup dies with "Fatal Python error: init_sys_streams" spam.
    # The parent handles KeyboardInterrupt and terminates the pool instead.
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def _make_pool(num_processes):
    # Spawn context everywhere (GUI already used it; fork caused instability on Linux)
    return mp.get_context('spawn').Pool(num_processes, initializer=_worker_init)


def run_cpu(prep, search_start, search_end, num_processes, reporter=None, control=None):
    """Run crack using CPU multiprocessing.

    Returns (results, elapsed). Honors control.should_stop() between steps
    (partial results are returned) and control.wait_if_paused() before steps.
    """
    if control is None:
        control = Control()
    global_start = time.time()
    processed = search_start
    total_seeds = search_end - search_start + 1
    search_end_exclusive = search_end + 1
    step_size = 200_000_000

    all_results = []
    pool = _make_pool(num_processes)

    try:
        while processed <= search_end:
            control.wait_if_paused()
            if control.should_stop():
                break
            step_start = processed
            step_end = min(processed + step_size, search_end_exclusive)
            chunk_size = (step_end - step_start) // num_processes

            tasks = []
            for i in range(num_processes):
                start = step_start + i * chunk_size
                end = step_start + (i + 1) * chunk_size if i < num_processes - 1 else step_end
                if start < end:
                    tasks.append((start, end, prep.r_base, prep.ox, prep.oz, prep.offset_range, prep.spread_type,
                                  prep.num_offsets, prep.sp_type, prep.sp_cx, prep.sp_cz, prep.sp_dx, prep.sp_dz))

            results = pool.map(crack_worker_cpu, tasks)

            for r in results:
                all_results.extend(r)
                if reporter:
                    for seed in r:
                        reporter.result(seed)

            processed = step_end
            elapsed = time.time() - global_start
            speed = (processed - search_start) / elapsed if elapsed > 0 else 0
            eta = (search_end_exclusive - processed) / speed if speed > 0 else 0
            if reporter:
                reporter.progress(processed - search_start, total_seeds, speed, eta)
    finally:
        pool.terminate()
        pool.join()

    return all_results, time.time() - global_start


def estimate_candidate_count(prep, search_start, search_end, num_processes, reporter=None):
    """Sampling pre-check: scan a small window with the CPU pool and extrapolate
    the total candidate count over the full range.

    Reuses crack_worker_cpu so the estimate includes the same per-structure
    offsets / 4-chunk grid logic as the real scan.

    Returns (predicted, sampled_found, saturated): saturated is True when a
    worker hit its 1000-result buffer cap, meaning the real count is far higher
    than the extrapolation.
    """
    total_span = search_end - search_start + 1
    sample_span = min(total_span, SAMPLE_SEEDS)
    sample_end_exclusive = search_start + sample_span

    pool = _make_pool(num_processes)
    sampled_found = 0
    saturated = False
    try:
        step_size = max(1, sample_span // 8)
        processed = search_start
        while processed < sample_end_exclusive and not saturated:
            step_end = min(processed + step_size, sample_end_exclusive)
            chunk = max(1, (step_end - processed) // num_processes)

            tasks = []
            for i in range(num_processes):
                s = processed + i * chunk
                e = min(processed + (i + 1) * chunk, step_end) if i < num_processes - 1 else step_end
                if s < e:
                    tasks.append((s, e, prep.r_base, prep.ox, prep.oz, prep.offset_range, prep.spread_type,
                                  prep.num_offsets, prep.sp_type, prep.sp_cx, prep.sp_cz, prep.sp_dx, prep.sp_dz))

            for found in pool.map(crack_worker_cpu, tasks):
                sampled_found += len(found)
                if len(found) >= 1000:  # worker result buffer cap reached
                    saturated = True

            processed = step_end
    finally:
        pool.terminate()
        pool.join()

    predicted = round(sampled_found * total_span / sample_span)
    return predicted, sampled_found, saturated


def run_gpu(prep, search_start, search_end, config, reporter=None, control=None):
    """Run crack using GPU (OpenCL) with batch processing.

    Returns (results, elapsed); elapsed is -1 on failure (caller decides on
    CPU fallback). Honors control.should_stop() at batch boundaries only
    (GPU pause is not supported).
    """
    if control is None:
        control = Control()
    lib_path = config_loader.resolve_native_lib(config_loader.native_dir(), 'crack_low32_opencl')

    # Change working directory to find crack_low32.cl
    original_dir = os.getcwd()
    os.chdir(lib_path.parent)

    all_results = []
    try:
        lib = ctypes.CDLL(str(lib_path))

        lib.crack_low32_grid_special_opencl.argtypes = [
            ctypes.c_uint32, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int), ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
        ]
        lib.crack_low32_grid_special_opencl.restype = ctypes.c_int

        num_structures = len(prep.offset_range)
        num_offsets = prep.num_offsets
        grid_count = num_structures * num_offsets
        r_base_arr = (ctypes.c_uint32 * grid_count)(*prep.r_base) if num_structures > 0 else None
        ox_arr = (ctypes.c_uint32 * grid_count)(*prep.ox) if num_structures > 0 else None
        oz_arr = (ctypes.c_uint32 * grid_count)(*prep.oz) if num_structures > 0 else None
        offset_range_arr = (ctypes.c_uint32 * num_structures)(*prep.offset_range) if num_structures > 0 else None
        spread_type_arr = (ctypes.c_int * num_structures)(*prep.spread_type) if num_structures > 0 else None

        num_special = len(prep.sp_type)
        sp_type_arr = (ctypes.c_int * num_special)(*prep.sp_type) if num_special > 0 else None
        sp_cx_arr = (ctypes.c_int * num_special)(*prep.sp_cx) if num_special > 0 else None
        sp_cz_arr = (ctypes.c_int * num_special)(*prep.sp_cz) if num_special > 0 else None
        sp_dx_arr = (ctypes.c_int * num_special)(*prep.sp_dx) if num_special > 0 else None
        sp_dz_arr = (ctypes.c_int * num_special)(*prep.sp_dz) if num_special > 0 else None

        max_results = config.get('max_results', 10000)
        results_arr = (ctypes.c_uint32 * max_results)()

        # Calculate batch size based on GPU capability
        # Modern GPUs can handle ~1B seeds per batch efficiently
        batch_size = 1_000_000_000  # 1B seeds per batch

        total_seeds = search_end - search_start + 1
        total_batches = (total_seeds + batch_size - 1) // batch_size

        if reporter:
            reporter.info(f"Running GPU crack: {search_start:,} ~ {search_end:,}")
            reporter.info(f"Batch mode: {total_batches} batches of {batch_size:,} seeds")
            reporter.info(f"num_structures={num_structures}, num_offsets={num_offsets}, grid_count={grid_count}")

        global_start = time.time()
        processed = search_start
        stopped = False

        while processed <= search_end:
            if control.should_stop():
                stopped = True
                break
            batch_start = processed
            batch_end = min(processed + batch_size - 1, search_end)

            batch_elapsed_start = time.time()

            found = lib.crack_low32_grid_special_opencl(
                batch_start, batch_end,
                r_base_arr, ox_arr, oz_arr, offset_range_arr, spread_type_arr,
                num_structures, num_offsets,
                sp_type_arr, sp_cx_arr, sp_cz_arr, sp_dx_arr, sp_dz_arr, num_special,
                results_arr, max_results
            )

            batch_elapsed = time.time() - batch_elapsed_start

            if found < 0:
                if reporter:
                    reporter.error(f"GPU crack failed at batch {processed:,}")
                return [], -1

            for i in range(found):
                seed = results_arr[i]
                all_results.append(seed)
                if reporter:
                    reporter.result(seed)

            processed = batch_end + 1

            # Progress report (same format as CPU)
            progress = (processed - search_start) / total_seeds * 100
            elapsed = time.time() - global_start
            speed = (processed - search_start) / elapsed if elapsed > 0 else 0
            eta = (search_end - processed) / speed if speed > 0 else 0
            if reporter:
                reporter.progress(processed - search_start, total_seeds, speed, eta)

        elapsed = time.time() - global_start
        speed = (processed - search_start) / elapsed if elapsed > 0 else 0

        if reporter and not stopped:
            reporter.info(f"GPU COMPLETE: Found {len(all_results)} seeds in {elapsed:.1f}s ({elapsed/60:.1f}min)")
            reporter.info(f"GPU SPEED: {speed/1e6:.0f}M seeds/s")

        return all_results, elapsed

    except Exception as e:
        if reporter:
            reporter.error(f"GPU crack exception: {e}")
        return [], -1
    finally:
        os.chdir(original_dir)


def resolve_mode(cfg, force_cpu=False, force_gpu=False, reporter=None):
    """Decide CPU vs GPU mode. Returns (use_gpu, gpu_device_str)."""
    if force_cpu:
        if reporter:
            reporter.info("CPU mode forced")
        return False, "N/A"
    if force_gpu:
        if reporter:
            reporter.info("GPU mode forced")
        return True, "N/A"
    if cfg.get('use_gpu', True):
        has_gpu, gpu_info = has_opencl_gpu(reporter=reporter)
        if has_gpu:
            if reporter:
                reporter.info(f"GPU detected: {gpu_info}")
            return True, gpu_info
        if reporter:
            reporter.info(f"GPU not available: {gpu_info}")
        if cfg.get('auto_fallback', True):
            if reporter:
                reporter.info("Auto-fallback to CPU mode")
            return False, "N/A"
        raise RuntimeError("GPU not available and auto-fallback disabled")
    if reporter:
        reporter.info("CPU mode (from config)")
    return False, "N/A"


def resolve_processes(cfg, requested=None, reporter=None):
    """Resolve the CPU process count.

    CRITICAL: Limit processes to prevent resource exhaustion. On high-core
    systems (>16 cores), using all cores causes library loading conflicts,
    memory exhaustion and lock contention. Priority: request > config > auto.
    """
    if requested is not None:
        num_processes = min(requested, 16)  # Never exceed 16
        if requested > 16 and reporter:
            reporter.warn(f"Limiting processes from {requested} to 16 (to prevent resource exhaustion)")
        source = "command-line"
    elif cfg.get('processes', None) is not None:
        cfg_processes = cfg.get('processes')
        num_processes = min(cfg_processes, 16)  # Never exceed 16
        if cfg_processes > 16 and reporter:
            reporter.warn(f"Limiting processes from {cfg_processes} to 16 (to prevent resource exhaustion)")
        source = "config file"
    else:
        # Auto-limit: use min(cpu_count, 16)
        num_processes = min(mp.cpu_count(), 16)
        source = "auto-detect"

    if mp.cpu_count() > 16 and reporter:
        reporter.info(f"Limiting processes from {mp.cpu_count()} to {num_processes} (to prevent resource exhaustion)")

    if reporter:
        reporter.info(f"Processes: {num_processes} ({source}, limited to 16)")
    return num_processes


def run_low32(cfg, targets, search_start, search_end, force_cpu=False, force_gpu=False,
              requested_processes=None, reporter=None, control=None):
    """High-level low32 orchestration shared by all frontends.

    Resolves mode and process count, prepares targets (with strictness
    testing), runs the candidate-count estimate and cracks. GPU failures fall
    back to CPU when auto_fallback is enabled.

    Returns (results, elapsed). Raises on invalid config/targets/libraries.
    """
    if reporter is None:
        reporter = Reporter()
    if control is None:
        control = Control()

    total_seeds = search_end - search_start + 1

    # Initialize targets (skip strictness test if search range size < 100000)
    skip_strictness = (search_end - search_start < 100000)
    prep = prepare_targets(targets, skip_strictness=skip_strictness, reporter=reporter)
    reporter.structure_info(prep.structure_info, prep.special_info)

    # Determine compute mode and process count
    use_gpu, gpu_device = resolve_mode(cfg, force_cpu=force_cpu, force_gpu=force_gpu, reporter=reporter)
    num_processes = resolve_processes(cfg, requested=requested_processes, reporter=reporter)
    reporter.device_info({'use_gpu': use_gpu, 'gpu': gpu_device, 'cores': num_processes})

    # Check library files
    try:
        if use_gpu:
            config_loader.resolve_native_lib(config_loader.native_dir(), 'crack_low32_opencl')
        else:
            config_loader.resolve_native_lib(config_loader.native_dir(), 'crack_low32')
    except RuntimeError as e:
        raise RuntimeError(str(e))

    # Sampling pre-check: estimate the candidate count before the full scan
    if total_seeds > SAMPLE_SEEDS:
        try:
            reporter.info(f"Estimating candidate count (sampling {SAMPLE_SEEDS:,} seeds)...")
            predicted, sampled, saturated = estimate_candidate_count(prep, search_start, search_end, num_processes)
            reporter.estimation({'predicted': predicted, 'sampled': sampled,
                                 'saturated': saturated, 'has_zero_sample': prep.has_zero_sample})
        except Exception as e:
            reporter.warn(f"Candidate estimation skipped: {e}")

    reporter.info("Starting crack...")

    if use_gpu:
        results, elapsed = run_gpu(prep, search_start, search_end, cfg, reporter=reporter, control=control)
        if elapsed < 0 and cfg.get('auto_fallback', True):
            reporter.info("Falling back to CPU mode...")
            results, elapsed = run_cpu(prep, search_start, search_end, num_processes,
                                       reporter=reporter, control=control)
    else:
        results, elapsed = run_cpu(prep, search_start, search_end, num_processes,
                                   reporter=reporter, control=control)

    return results, elapsed
