from PyQt5.QtCore import QThread, pyqtSignal
import time
import json
import os
import sys
import multiprocessing as mp
import ctypes


def get_dll_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        return os.path.join(base_path, "_internal", "dll", "crack_low32", "crack_low32.dll")
    return os.path.join(os.path.dirname(__file__), "..", "..", "dll", "crack_low32", "crack_low32.dll")


def get_base_path():
    """Get absolute path of program directory"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def crack_worker(args):
    try:
        start, end, r_base, ox, oz, offset_range, spread_type = args
        
        dll_path = get_dll_path()
        
        if not os.path.exists(dll_path):
            print(f"[ERROR] DLL not found: {dll_path}")
            return []
        
        lib = ctypes.CDLL(dll_path, winmode=0x00000008)
        
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
    except Exception as e:
        print(f"[ERROR] crack_worker exception: {e}")
        return []


class Low32Worker(QThread):
    progress_updated = pyqtSignal(float, int, int)
    found_seed = pyqtSignal(object)
    finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, structures, start=0, end=4294967295, test_mode=False):
        super().__init__()
        self.structures = structures
        self.start_value = start
        self.original_start_value = start
        self.end_value = end
        self.test_mode = test_mode
        self.is_paused = False
        self.is_stopped = False
        self.results = []
        
        if test_mode:
            self.end_value = min(end, 100000000)
        
        self.progress_file = os.path.join(get_base_path(), "progress_low32.json")
        
        data_file = os.path.join(
            os.path.dirname(__file__), "..", "data", "structures.json"
        )
        with open(data_file, 'r', encoding='utf-8') as f:
            self.structure_data = json.load(f)
    
    def run(self):
        try:
            r_base, ox, oz, offset_range, spread_type = self.prepare_structures()
            
            num_processes = mp.cpu_count()
            dll_path = get_dll_path()
            
            print(f"[INFO] Using {num_processes} processes for parallel cracking")
            print(f"[INFO] Start value: {self.start_value}")
            print(f"[INFO] Original start value: {self.original_start_value}")
            print(f"[INFO] End value: {self.end_value}")
            print(f"[INFO] Total range: {self.end_value - self.original_start_value:,}")
            print(f"[INFO] DLL path: {dll_path}")
            print(f"[INFO] DLL exists: {os.path.exists(dll_path)}")
            
            if not os.path.exists(dll_path):
                self.error_occurred.emit(f"DLL not found: {dll_path}")
                return
            
            total_range = self.end_value - self.original_start_value + 1
            step_size = 200_000_000
            current = self.start_value
            
            start_time = time.time()
            last_progress_time = start_time
            last_progress_current = current
            last_save_time = start_time
            last_result_save_time = start_time
            
            ctx = mp.get_context('spawn')
            with ctx.Pool(num_processes) as pool:
                end_inclusive = self.end_value
                while current <= end_inclusive and not self.is_stopped:
                    while self.is_paused:
                        time.sleep(0.1)
                        if self.is_stopped:
                            return
                    
                    step_start = current
                    step_end = min(current + step_size - 1, end_inclusive)
                    chunk_size = max(1, (step_end - step_start + 1) // num_processes)
                    
                    tasks = []
                    for i in range(num_processes):
                        task_start = step_start + i * chunk_size
                        task_end = min(step_start + (i + 1) * chunk_size - 1, step_end) if i < num_processes - 1 else step_end
                        if task_start <= task_end:
                            tasks.append((task_start, task_end + 1, r_base, ox, oz, offset_range, spread_type))
                    
                    try:
                        results_list = pool.map(crack_worker, tasks)
                        
                        for found in results_list:
                            if found:
                                self.results.extend(found)
                                for seed in found:
                                    self.found_seed.emit(seed)
                        
                    except Exception as e:
                        print(f"[ERROR] Pool map exception: {e}")
                        self.error_occurred.emit(str(e))
                        return
                    
                    current = step_end + 1
                    
                    now = time.time()
                    step_elapsed = now - last_progress_time
                    step_processed = current - last_progress_current
                    
                    processed = min(current, self.end_value + 1)
                    progress = (processed - self.original_start_value) / total_range * 100
                    speed = int(step_processed / step_elapsed) if step_elapsed > 0 else 0
                    eta = int((self.end_value - processed + 1) / speed) if speed > 0 else 0
                    
                    print(f"[PROGRESS] {progress:.2f}% | Current: {current:,} | Speed: {speed:,}/s | ETA: {eta}s")
                    
                    self.progress_updated.emit(progress, speed, eta)

                    # Save current position for stop() to use
                    self.last_current_position = current

                    last_progress_time = now
                    last_progress_current = current
                    
                    if now - last_save_time >= 60:
                        print(f"[SAVE] Saving progress at {current:,}")
                        self.save_progress(current)
                        last_save_time = now
                    
                    if now - last_result_save_time >= 30:
                        print(f"[RESULT SAVE] Found {len(self.results)} seeds so far")
                        last_result_save_time = now
            
            if not self.is_stopped:
                print(f"[COMPLETE] Finished! Found {len(self.results)} seeds")
                self.finished.emit(self.results)
            else:
                print(f"[STOPPED] Worker stopped by user at {current:,}")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))
    
    def prepare_structures(self):
        CONST_A = 2570712328
        CONST_B = 4048968661
        
        sorted_structures = sorted(self.structures, key=lambda s: 0 if self.structure_data.get(s["type"], {}).get("spread_type", "linear") == "linear" else 1)
        
        r_base_list, ox_list, oz_list, offset_range_list, spread_type_list = [], [], [], [], []
        
        for structure in sorted_structures:
            structure_type = structure["type"]
            x, z = structure["x"], structure["z"]
            
            config = self.structure_data.get(structure_type, {})
            spacing = config.get("spacing", 32)
            separation = config.get("separation", 8)
            salt = config.get("salt", 14357617)
            spread_type_str = config.get("spread_type", "linear")
            
            cx, cz = x >> 4, z >> 4
            rx, rz = cx // spacing, cz // spacing
            ox, oz = cx % spacing, cz % spacing
            
            r_base = (rx * CONST_A + rz * CONST_B + salt) & 0xFFFFFFFF
            spread_type_int = 1 if spread_type_str == "triangular" else 0
            
            r_base_list.append(r_base)
            ox_list.append(ox)
            oz_list.append(oz)
            offset_range_list.append(spacing - separation)
            spread_type_list.append(spread_type_int)
        
        return r_base_list, ox_list, oz_list, offset_range_list, spread_type_list
    
    def save_progress(self, current):
        progress_data = {
            "mode": "low32",
            "status": "running",
            "current_position": current,
            "original_start_value": self.original_start_value,
            "start_value": self.start_value,
            "end_value": self.end_value,
            "test_mode": self.test_mode,
            "structures": self.structures,
            "results": self.results,
            "timestamp": time.time()
        }
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2)
            print(f"[SAVE SUCCESS] Progress saved to {self.progress_file}")
        except Exception as e:
            print(f"[SAVE ERROR] Failed to save progress: {e}")
    
    def pause(self):
        self.is_paused = True
    
    def resume(self):
        self.is_paused = False
    
    def stop(self):
        self.is_stopped = True
        # Force save progress before stopping
        if hasattr(self, 'last_current_position'):
            self.save_progress(self.last_current_position)
            print(f"[LOW32 STOP] Saved progress before stopping: {self.last_current_position:,}")
