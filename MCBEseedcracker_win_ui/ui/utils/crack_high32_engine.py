# -*- coding: utf-8 -*-
"""
High 32-bit Cracking Implementation for UI Version
"""
import ctypes
import os
import multiprocessing as mp
from pathlib import Path

script_dir = Path(__file__).parent.parent.parent.resolve()
dll_path = script_dir / "dll" / "crack_high32" / "crack_high32.dll"

if not dll_path.exists():
    legacy_path = script_dir.parent / "MCBEseedcracker" / "crack_high32" / "crack_high32.dll"
    if legacy_path.exists():
        dll_path = legacy_path

MAX_RESULTS = 1000
MC_1_18 = 22
MC_1_19 = 24
MC_1_20 = 25
MC_1_21_3 = 27
MC_1_21_WD = 28
MC_1_21_5 = 29

VERSION_MAP = {
    "1.21.60-1.21.132": MC_1_21_5,
    "1.21.50": MC_1_21_WD,
    "1.21-1.21.40": MC_1_21_3,
    "1.20.60-81": MC_1_20,
    "1.20.0-51": MC_1_20,
    "1.19": MC_1_19,
    "1.18": MC_1_18,
}

class BiomeSample(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("z", ctypes.c_int), ("biome_id", ctypes.c_int)]

def init_dll():
    if not dll_path.exists():
        raise FileNotFoundError(f"DLL not found: {dll_path}")
    
    os.add_dll_directory(str(dll_path.parent))
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
    try:
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
    except Exception as e:
        print(f"[ERROR] crack_batch_soa failed: {e}")
        return []

def crack_high32_parallel(low32, samples, start=0, end=0xFFFFFFFF, y_coord=200, mc_version="1.21.60-1.21.132", num_processes=None):
    if not samples:
        return []

    mc_version_int = VERSION_MAP.get(mc_version, MC_1_21_WD)
    num_processes = num_processes or mp.cpu_count()
    
    batch_size = 500000
    tasks = []
    
    current = start
    while current <= end:
        batch_end = min(current + batch_size - 1, end)
        tasks.append((current, batch_end, low32, samples, y_coord, mc_version_int))
        current = batch_end + 1
    
    with mp.Pool(num_processes) as pool:
        results_list = pool.map(crack_batch_soa, tasks)
    
    all_results = []
    for results in results_list:
        all_results.extend(results)
    
    return all_results
