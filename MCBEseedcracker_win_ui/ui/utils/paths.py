# -*- coding: utf-8 -*-
"""
Path helpers - single source of truth for program, DLL and data locations
"""
import os
import sys

LOW32_COMPONENT = "crack_low32"
HIGH32_COMPONENT = "crack_high32"

LOW32_DLL = "crack_low32.dll"
LOW32_OPENCL_DLL = "crack_low32_opencl.dll"
LOW32_CL_KERNEL = "crack_low32.cl"
HIGH32_DLL = "crack_high32.dll"


def get_base_path():
    """Get absolute path of program directory"""
    if getattr(sys, 'frozen', False):
        # Path after PyInstaller packaging
        return os.path.dirname(sys.executable)
    # Development environment path
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_bundle_path():
    """Get directory holding bundled resources (DLLs, data files)"""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "_internal")
    return get_base_path()


def get_dll_path(component, dll_name):
    """Get path of a bundled DLL / OpenCL kernel"""
    return os.path.join(get_bundle_path(), "dll", component, dll_name)


def get_data_path(filename):
    """Get path of a file in ui/data"""
    ui_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(ui_dir, "data", filename)


def get_progress_path(mode):
    """Get progress file path for a crack mode ("low32" / "high32")"""
    return os.path.join(get_base_path(), f"progress_{mode}.json")


def get_session_path():
    """Get session data file path"""
    return os.path.join(get_base_path(), "session_data.json")
