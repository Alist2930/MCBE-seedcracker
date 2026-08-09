import ctypes
import json
import os
import traceback
from pathlib import Path


class CrackEngine:
    def __init__(self):
        self.low32_lib = None
        self.high32_lib = None
        self.low32_error = None
        self.high32_error = None
        self.load_libraries()
    
    def load_libraries(self):
        base_path = Path(__file__).parent.parent.parent
        
        low32_dll = base_path / "dll" / "crack_low32" / "crack_low32.dll"
        high32_dll = base_path / "dll" / "crack_high32" / "crack_high32.dll"
        
        if not low32_dll.exists():
            legacy_path = base_path.parent / "MCBEseedcracker"
            low32_dll = legacy_path / "crack_low32" / "crack_low32.dll"
            high32_dll = legacy_path / "crack_high32" / "crack_high32.dll"
        
        print(f"[DEBUG] Looking for low32 DLL: {low32_dll}")
        print(f"[DEBUG] DLL exists: {low32_dll.exists()}")
        
        if low32_dll.exists():
            try:
                os.add_dll_directory(str(low32_dll.parent))
                self.low32_lib = ctypes.CDLL(str(low32_dll), winmode=0x00000008)
                self.setup_low32_functions()
                print(f"[DEBUG] Low 32-bit library loaded successfully")
            except Exception as e:
                self.low32_error = f"Failed to load {low32_dll}: {type(e).__name__}: {e}"
                print(f"[ERROR] {self.low32_error}")
                traceback.print_exc()
        else:
            self.low32_error = f"Low 32-bit DLL not found at: {low32_dll}"
            print(f"[ERROR] {self.low32_error}")
        
        if high32_dll.exists():
            try:
                os.add_dll_directory(str(high32_dll.parent))
                self.high32_lib = ctypes.CDLL(str(high32_dll), winmode=0x00000008)
                self.setup_high32_functions()
                print(f"[DEBUG] High 32-bit library loaded successfully")
            except Exception as e:
                self.high32_error = f"Failed to load {high32_dll}: {type(e).__name__}: {e}"
                print(f"[ERROR] {self.high32_error}")
                traceback.print_exc()
        else:
            self.high32_error = f"High 32-bit DLL not found at: {high32_dll}"
            print(f"[ERROR] {self.high32_error}")
    
    def setup_low32_functions(self):
        self.low32_lib.crack_low32.argtypes = [
            ctypes.c_uint32, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_int), ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
        ]
        self.low32_lib.crack_low32.restype = ctypes.c_int
    
    def setup_high32_functions(self):
        pass
    
    def crack_low32(self, start, end, r_base, ox, oz, offset_range, spread_type, max_results=1000):
        if not self.low32_lib:
            raise RuntimeError(
                f"Low 32-bit library not loaded: {self.low32_error or 'unknown error'}"
            )
        
        num_targets = len(r_base)
        r_base_arr = (ctypes.c_uint32 * num_targets)(*r_base)
        ox_arr = (ctypes.c_uint32 * num_targets)(*ox)
        oz_arr = (ctypes.c_uint32 * num_targets)(*oz)
        offset_range_arr = (ctypes.c_uint32 * num_targets)(*offset_range)
        spread_type_arr = (ctypes.c_int * num_targets)(*spread_type)
        results_arr = (ctypes.c_uint32 * max_results)()
        
        try:
            found = self.low32_lib.crack_low32(
                start, end,
                r_base_arr, ox_arr, oz_arr,
                offset_range_arr, spread_type_arr,
                num_targets, results_arr, max_results
            )
            
            if found < 0:
                raise RuntimeError(f"crack_low32 failed for range {start}-{end} (return code {found})")

            return [results_arr[i] for i in range(found)]
        except Exception as e:
            print(f"[ERROR] crack_low32 call failed: {e}")
            traceback.print_exc()
            raise
    
    def crack_high32(self, low32_value, samples, start, end, mc_version="1.21.60-26.23"):
        """Crack the high 32 bits

        Raises:
            RuntimeError: If biome data cannot be read or a sample uses an
                unknown biome. Dropping samples would silently weaken the
                search and yield candidate seeds that are not real matches.
        """
        from ui.utils.crack_high32_engine import crack_high32_parallel

        biome_data_path = Path(__file__).parent.parent / "data" / "biomes.json"
        try:
            with open(biome_data_path, 'r', encoding='utf-8') as f:
                biome_data = json.load(f)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to load biome data {biome_data_path}: {e}") from e

        biome_samples = []
        unknown_biomes = []
        for s in samples:
            biome_name = s['type']
            biome_id = biome_data.get(biome_name, {}).get('id')
            if biome_id is None:
                unknown_biomes.append(biome_name)
                continue
            biome_samples.append((s['x'], s['z'], biome_id))

        if unknown_biomes:
            raise RuntimeError("Unknown biome type(s): " + ", ".join(sorted(set(unknown_biomes))))

        return crack_high32_parallel(
            low32=low32_value,
            samples=biome_samples,
            start=start,
            end=end,
            y_coord=200,
            mc_version=mc_version
        )


crack_engine = CrackEngine()
