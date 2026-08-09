# -*- coding: utf-8 -*-
"""
Native library bindings - shared ctypes glue for the crack DLLs
"""
import ctypes
import os

MAX_RESULTS = 1000

LOW32_ARGTYPES = [
    ctypes.c_uint32, ctypes.c_uint32,
    ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
    ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
    ctypes.POINTER(ctypes.c_int), ctypes.c_int,
    ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
]


class BiomeSample(ctypes.Structure):
    """Mirrors the BiomeSample struct of crack_high32.c"""
    _fields_ = [
        ("x", ctypes.c_int),
        ("z", ctypes.c_int),
        ("y", ctypes.c_int),
        ("biome_id", ctypes.c_int),
    ]


def load_library(dll_path):
    """Load a DLL, adding its directory to the Windows DLL search path"""
    dll_dir = os.path.dirname(os.path.abspath(dll_path))
    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(dll_dir)
    return ctypes.CDLL(str(dll_path), winmode=0x00000008)


def bind_low32(lib, opencl=False):
    """Declare the signature of crack_low32 / crack_low32_opencl"""
    func = lib.crack_low32_opencl if opencl else lib.crack_low32
    func.argtypes = LOW32_ARGTYPES
    func.restype = ctypes.c_int
    return func


def bind_high32(lib):
    """Declare the signature of crack_high32_soa"""
    lib.crack_high32_soa.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int,
        ctypes.POINTER(BiomeSample), ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_int, ctypes.c_int
    ]
    lib.crack_high32_soa.restype = ctypes.c_int
    return lib.crack_high32_soa


def build_structure_arrays(r_base, ox, oz, offset_range, spread_type):
    """Convert structure target lists into the C arrays crack_low32 expects"""
    num_targets = len(r_base)
    return (
        (ctypes.c_uint32 * num_targets)(*r_base),
        (ctypes.c_uint32 * num_targets)(*ox),
        (ctypes.c_uint32 * num_targets)(*oz),
        (ctypes.c_uint32 * num_targets)(*offset_range),
        (ctypes.c_int * num_targets)(*spread_type),
    )


def call_low32(func, start, end, r_base, ox, oz, offset_range, spread_type, max_results=MAX_RESULTS):
    """Run a crack_low32-compatible function over [start, end) and return the seeds"""
    arrays = build_structure_arrays(r_base, ox, oz, offset_range, spread_type)
    results_arr = (ctypes.c_uint32 * max_results)()

    found = func(
        start, end, *arrays,
        len(r_base), results_arr, max_results
    )
    if found < 0:
        return found, []
    return found, [results_arr[i] for i in range(found)]


def build_biome_samples(samples):
    """Convert (x, z, y, biome_id) tuples into a BiomeSample array"""
    sample_array = (BiomeSample * len(samples))()
    for i, (x, z, y, biome_id) in enumerate(samples):
        sample_array[i].x = x
        sample_array[i].z = z
        sample_array[i].y = y
        sample_array[i].biome_id = biome_id
    return sample_array


def call_high32(func, start_high, end_high, low32, samples, y_coord, mc_version, max_results=MAX_RESULTS):
    """Run crack_high32_soa over [start_high, end_high) and return the seeds"""
    sample_array = build_biome_samples(samples)
    results = (ctypes.c_uint64 * max_results)()

    found = func(
        start_high, end_high, low32, y_coord,
        sample_array, len(samples),
        results, max_results, mc_version
    )
    if found < 0:
        return []
    return [results[i] for i in range(found)]
