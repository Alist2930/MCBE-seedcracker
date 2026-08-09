# -*- coding: utf-8 -*-
"""
Shared helpers for the Linux crackers

Holds the pieces both crack_low32.py and crack_high32.py need: the low32
native binding, seed formatting, CLI/config resolution and progress output.
"""
import ctypes
import multiprocessing as mp

MAX_UINT32 = 0xFFFFFFFF
# Upper bound of the reduced range used by test mode
TEST_MODE_END = 100000000
SIGNED64_MAX = 9223372036854775807
UINT64_MAX = 18446744073709551615

# Processes beyond this count cause library loading conflicts and lock
# contention instead of extra throughput
PROCESS_LIMIT = 16

LOW32_ARGTYPES = [
    ctypes.c_uint32, ctypes.c_uint32,
    ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
    ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
    ctypes.POINTER(ctypes.c_int), ctypes.c_int,
    ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
]


def to_signed64(seed):
    """Convert an unsigned 64-bit seed to the value shown in-game"""
    if seed > SIGNED64_MAX:
        return seed - UINT64_MAX - 1
    return seed


def format_seed_output(seed, low32):
    """Describe a full seed the way both the console and the log file want it"""
    high32 = seed >> 32
    display_seed = to_signed64(seed)

    return '\n'.join([
        "\n[FOUND] Seed found!",
        f"    Low 32-bit:  {low32} (0x{low32:08X})",
        f"    High 32-bit: {high32} (0x{high32:08X})",
        f"    Full seed:   {display_seed} (0x{seed:016X})",
    ])


def load_low32_lib(lib_path, opencl=False):
    """Load a low32 library and declare the signature of its entry point"""
    lib = ctypes.CDLL(str(lib_path))
    entry = lib.crack_low32_opencl if opencl else lib.crack_low32
    entry.argtypes = LOW32_ARGTYPES
    entry.restype = ctypes.c_int
    return lib


def build_target_arrays(r_base, ox, oz, offset_range, spread_type):
    """Convert the per-target parameter lists into C arrays"""
    num_targets = len(r_base)
    return (
        num_targets,
        (ctypes.c_uint32 * num_targets)(*r_base),
        (ctypes.c_uint32 * num_targets)(*ox),
        (ctypes.c_uint32 * num_targets)(*oz),
        (ctypes.c_uint32 * num_targets)(*offset_range),
        (ctypes.c_int * num_targets)(*spread_type),
    )


def call_low32(lib, start, end, target_arrays, max_results, opencl=False):
    """Run a low32 search, returning the found seeds or None on failure"""
    num_targets, r_base_arr, ox_arr, oz_arr, offset_range_arr, spread_type_arr = target_arrays
    results_arr = (ctypes.c_uint32 * max_results)()

    entry = lib.crack_low32_opencl if opencl else lib.crack_low32
    found = entry(
        start, end,
        r_base_arr, ox_arr, oz_arr, offset_range_arr, spread_type_arr,
        num_targets, results_arr, max_results
    )

    if found < 0:
        return None

    return [results_arr[i] for i in range(found)]


def resolve_search_range(args, cfg):
    """Resolve the search range from CLI arguments and config defaults"""
    if args.test:
        return True, 0, TEST_MODE_END

    test_mode = cfg.get('test_mode', False)
    start = args.start if args.start is not None else cfg.get('start', 0)
    end = args.end if args.end is not None else cfg.get('end', MAX_UINT32)
    return test_mode, start, end


def resolve_process_count(cli_processes, cfg, limit=None, quarter_on_auto=False):
    """Resolve the process count from CLI arguments and config defaults

    Returns (process_count, source). When limit is set the requested count is
    capped, and quarter_on_auto additionally keeps auto-detection to a quarter
    of the available cores.
    """
    for requested, source in ((cli_processes, "command-line"), (cfg.get('processes'), "config file")):
        if requested is None:
            continue
        if limit and requested > limit:
            print(f"[WARNING] Limiting processes from {requested} to {limit} (to prevent resource exhaustion)")
            return limit, source
        return requested, source

    cpu_count = mp.cpu_count()
    if quarter_on_auto:
        return min(cpu_count, limit, max(1, cpu_count // 4)), "auto-detect"
    if limit:
        return min(cpu_count, limit), "auto-detect"
    return cpu_count, "auto-detect"


def format_progress_bar(percent, bar_len=30):
    """Render a text progress bar for the given completion percentage"""
    filled = int(bar_len * percent / 100)
    return '#' * filled + '-' * (bar_len - filled)


def format_eta(seconds):
    """Format a remaining duration using the largest sensible unit"""
    if seconds > 3600:
        return f"{seconds / 3600:.1f}h"
    if seconds > 60:
        return f"{seconds / 60:.1f}min"
    return f"{seconds:.0f}s"
