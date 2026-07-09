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
        return os.path.join(base_path, "_internal", "dll", "crack_high32", "crack_high32.dll")
    return os.path.join(os.path.dirname(__file__), "..", "..", "dll", "crack_high32", "crack_high32.dll")


def get_base_path():
    """获取程序所在目录的绝对路径"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BiomeSample(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("z", ctypes.c_int), ("biome_id", ctypes.c_int)]


def crack_batch(args):
    try:
        start_high, end_high, low32, samples, y_coord, mc_version = args
        
        dll_path = get_dll_path()
        
        if not os.path.exists(dll_path):
            print(f"[ERROR] DLL not found: {dll_path}")
            return []
        
        dll = ctypes.CDLL(dll_path, winmode=0x00000008)
        
        dll.crack_high32_soa.argtypes = [
            ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int,
            ctypes.POINTER(BiomeSample), ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint64), ctypes.c_int, ctypes.c_int
        ]
        dll.crack_high32_soa.restype = ctypes.c_int
        
        num_samples = len(samples)
        sample_array = (BiomeSample * num_samples)()
        for i, (x, z, biome_id) in enumerate(samples):
            sample_array[i].x = x
            sample_array[i].z = z
            sample_array[i].biome_id = biome_id
        
        MAX_RESULTS = 1000
        results = (ctypes.c_uint64 * MAX_RESULTS)()
        
        found = dll.crack_high32_soa(
            start_high, end_high, low32, y_coord,
            sample_array, num_samples,
            results, MAX_RESULTS, mc_version
        )
        
        seeds = [results[i] for i in range(found)]
        if seeds:
            print(f"[DEBUG] Found {len(seeds)} seeds in batch {start_high}-{end_high}")
        
        return seeds
    except Exception as e:
        print(f"[ERROR] crack_batch exception: {e}")
        return []


class High32Worker(QThread):
    progress_updated = pyqtSignal(float, int, int)
    found_seed = pyqtSignal(object)
    finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    VERSION_MAP = {
        "1.17": 0,
        "1.18": 22,
        "1.19": 24,
        "1.20": 25,
        "1.21": 28,
    }
    
    def __init__(self, low32_value, biomes, start=0, end=4294967295, test_mode=False, mc_version="1.21"):
        super().__init__()
        self.low32_value = low32_value
        self.biomes = biomes
        self.start_value = start
        self.original_start_value = start
        self.end_value = end
        self.test_mode = test_mode
        self.mc_version_str = mc_version
        self.mc_version = self.VERSION_MAP.get(mc_version, 28)
        self.is_paused = False
        self.is_stopped = False
        self.results = []
        
        if test_mode:
            self.end_value = min(end, 100000000)
        
        self.progress_file = os.path.join(get_base_path(), "progress_high32.json")
    
    def run(self):
        try:
            biome_data_path = os.path.join(os.path.dirname(__file__), "..", "data", "biomes.json")
            with open(biome_data_path, 'r', encoding='utf-8') as f:
                biome_data = json.load(f)
            
            biome_samples = []
            for b in self.biomes:
                biome_name = b['type']
                biome_id = biome_data.get(biome_name, {}).get('id')
                if biome_id is not None:
                    biome_samples.append((b['x'], b['z'], biome_id))
            
            if not biome_samples:
                self.error_occurred.emit("没有有效的群系数据")
                return
            
            num_processes = mp.cpu_count()
            batch_size = 1000000
            dll_path = get_dll_path()
            
            print(f"[HIGH32 INFO] Using {num_processes} processes for parallel cracking")
            print(f"[HIGH32 INFO] Low32 value: {self.low32_value}")
            print(f"[HIGH32 INFO] Start value: {self.start_value}")
            print(f"[HIGH32 INFO] End value: {self.end_value}")
            print(f"[HIGH32 INFO] Total range: {self.end_value - self.original_start_value:,}")
            print(f"[HIGH32 INFO] Biome samples: {len(biome_samples)}")
            print(f"[HIGH32 INFO] DLL path: {dll_path}")
            print(f"[HIGH32 INFO] DLL exists: {os.path.exists(dll_path)}")
            
            if not os.path.exists(dll_path):
                self.error_occurred.emit(f"DLL not found: {dll_path}")
                return
            
            tasks = []
            current = self.start_value
            while current <= self.end_value:
                batch_end = min(current + batch_size - 1, self.end_value)
                tasks.append((current, batch_end + 1, self.low32_value, biome_samples, 200, self.mc_version))
                current = batch_end + 1
            
            total_tasks = len(tasks)
            completed_tasks = 0
            start_time = time.time()
            last_progress_time = start_time
            last_progress_completed = 0
            last_save_time = start_time
            
            print(f"[HIGH32 INFO] Total tasks: {total_tasks}")
            
            ctx = mp.get_context('spawn')
            with ctx.Pool(num_processes) as pool:
                for result in pool.imap_unordered(crack_batch, tasks):
                    if self.is_stopped:
                        break
                    
                    while self.is_paused:
                        time.sleep(0.1)
                        if self.is_stopped:
                            return
                    
                    if result:
                        for seed in result:
                            self.results.append(seed)
                            self.found_seed.emit(seed)
                    
                    completed_tasks += 1
                    
                    now = time.time()
                    step_elapsed = now - last_progress_time
                    step_processed = (completed_tasks - last_progress_completed) * batch_size
                    
                    current_position = self.start_value + completed_tasks * batch_size
                    progress = (completed_tasks / total_tasks) * 100
                    speed = int(step_processed / step_elapsed) if step_elapsed > 0 else 0
                    eta = int((total_tasks - completed_tasks) * batch_size / speed) if speed > 0 else 0
                    
                    print(f"[HIGH32 PROGRESS] {progress:.2f}% | Completed: {completed_tasks}/{total_tasks} | Speed: {speed:,}/s | ETA: {eta}s")
                    
                    self.progress_updated.emit(progress, speed, eta)
                    
                    last_progress_time = now
                    last_progress_completed = completed_tasks
                    
                    if now - last_save_time >= 60:
                        print(f"[HIGH32 SAVE] Saving progress at {current_position:,}")
                        self.save_progress(current_position)
                        last_save_time = now
            
            if not self.is_stopped:
                print(f"[HIGH32 COMPLETE] Finished! Found {len(self.results)} seeds")
                self.finished.emit(self.results)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))
    
    def save_progress(self, current):
        progress_data = {
            "mode": "high32",
            "status": "running",
            "low32_value": self.low32_value,
            "current_position": current,
            "start_value": self.start_value,
            "end_value": self.end_value,
            "test_mode": self.test_mode,
            "biomes": self.biomes,
            "results": self.results,
            "timestamp": time.time()
        }
        
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2)
            print(f"[HIGH32 SAVE SUCCESS] Progress saved to {self.progress_file}")
        except Exception as e:
            print(f"[HIGH32 SAVE ERROR] Failed to save progress: {e}")
    
    def pause(self):
        self.is_paused = True
    
    def resume(self):
        self.is_paused = False
    
    def stop(self):
        self.is_stopped = True
