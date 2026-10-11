#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU Feature Detection Tool

Checks if the current CPU supports AVX2 instructions and displays
which implementation will be used by the seed cracker.
"""

import ctypes
import platform
import sys
from pathlib import Path

def native_lib_candidates(base):
    """Return platform-specific shared library filename candidates in priority order
    (standalone copy: this diagnostic tool does not import config_loader)."""
    machine = platform.machine().lower()
    arch = 'arm64' if machine in ('arm64', 'aarch64') else 'x86_64'
    if sys.platform == 'win32':
        return [f'{base}_win_{arch}.dll', base + '.dll']
    os_tag = 'macos' if sys.platform == 'darwin' else 'linux'
    return [f'{base}_{os_tag}_{arch}.so', base + '.so']

script_dir = Path(__file__).parent.resolve()
native_dir = script_dir / 'native'
dll_candidates = [native_dir / name for name in native_lib_candidates("crack_high32")]
dll_path = next((p for p in dll_candidates if p.exists()), dll_candidates[0])

class CPUChecker:
    def __init__(self):
        self.has_avx2 = False
        self.cpu_info = {}
        self._detect_cpu_features()
    
    def _detect_cpu_features(self):
        """Detect CPU features using Python."""
        try:
            # Try to read from /proc/cpuinfo on Linux
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                self.cpu_info['vendor'] = self._extract_cpuinfo_field(cpuinfo, 'vendor_id')
                self.cpu_info['model'] = self._extract_cpuinfo_field(cpuinfo, 'model name')
                self.cpu_info['family'] = self._extract_cpuinfo_field(cpuinfo, 'cpu family')
                self.cpu_info['flags'] = self._extract_cpuinfo_flags(cpuinfo)
                self.has_avx2 = 'avx2' in self.cpu_info['flags']
        except:
            # Fallback: try loading DLL and check via C
            if dll_path.exists():
                try:
                    dll = ctypes.CDLL(str(dll_path))
                    dll.get_cpu_capabilities.argtypes = []
                    dll.get_cpu_capabilities.restype = ctypes.c_char_p
                    result = dll.get_cpu_capabilities().decode('utf-8')
                    self.has_avx2 = 'AVX2 supported' in result
                except:
                    pass
    
    def _extract_cpuinfo_field(self, cpuinfo, field):
        """Extract a field from /proc/cpuinfo."""
        for line in cpuinfo.split('\n'):
            if line.startswith(field):
                return line.split(':')[1].strip()
        return 'Unknown'
    
    def _extract_cpuinfo_flags(self, cpuinfo):
        """Extract CPU flags from /proc/cpuinfo."""
        for line in cpuinfo.split('\n'):
            if line.startswith('flags'):
                return line.split(':')[1].strip().split()
        return []
    
    def print_report(self):
        """Print CPU capability report."""
        print("=" * 70)
        print("CPU Feature Detection Report")
        print("=" * 70)
        
        if self.cpu_info:
            print(f"\nCPU Information:")
            print(f"  Vendor:  {self.cpu_info.get('vendor', 'Unknown')}")
            print(f"  Model:   {self.cpu_info.get('model', 'Unknown')}")
            print(f"  Family:  {self.cpu_info.get('family', 'Unknown')}")
        
        print(f"\nAVX2 Support:")
        if self.has_avx2:
            print(f"  Status:  ✓ Supported")
            print(f"  Impact:  AVX2 optimizations will be used")
            print(f"  Speedup: Up to 2-4x faster than SSE version")
        else:
            print(f"  Status:  ✗ Not Supported")
            print(f"  Impact:  Using SOA (Structure of Arrays) implementation")
            print(f"  Note:    AVX2 requires Intel Haswell (2013+) or AMD Excavator (2015+)")
        
        print(f"\nImplementation:")
        if self.has_avx2:
            print(f"  Selected: AVX2 Optimized Version")
        else:
            print(f"  Selected: SOA Version (fallback)")
        
        print("\n" + "=" * 70)
        
        # Test DLL if available
        if dll_path.exists():
            print(f"\n[*] Testing compiled library...")
            try:
                dll = ctypes.CDLL(str(dll_path))
                
                # Get implementation name
                try:
                    dll.get_implementation_name.argtypes = []
                    dll.get_implementation_name.restype = ctypes.c_char_p
                    impl_name = dll.get_implementation_name().decode('utf-8')
                    print(f"[+] Implementation: {impl_name}")
                except:
                    pass
                
                # Get CPU capabilities from C
                try:
                    dll.get_cpu_capabilities.argtypes = []
                    dll.get_cpu_capabilities.restype = ctypes.c_char_p
                    cpu_caps = dll.get_cpu_capabilities().decode('utf-8')
                    print(f"[+] DLL Detection: {cpu_caps}")
                except:
                    pass
                
            except Exception as e:
                print(f"[ERROR] Failed to load DLL: {e}")
        else:
            print(f"\n[!] Library not found: {dll_path}")
            print(f"[!] Run the build script first (build.bat on Windows, ./build.sh on Linux/macOS)")
        
        print("\n" + "=" * 70)

def main():
    checker = CPUChecker()
    checker.print_report()
    return 0

if __name__ == "__main__":
    sys.exit(main())