from PyQt5.QtCore import QThread, pyqtSignal
import time
import json
import os
import sys
import multiprocessing as mp
import ctypes
from ui.utils.language_manager import lang_manager


def get_dll_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        return os.path.join(base_path, "_internal", "dll", "crack_high32", "crack_high32.dll")
    return os.path.join(os.path.dirname(__file__), "..", "..", "dll", "crack_high32", "crack_high32.dll")


def get_base_path():
    """Get absolute path of program directory"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BiomeSample(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("z", ctypes.c_int), ("y", ctypes.c_int), ("biome_id", ctypes.c_int)]


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
        for i, (x, z, y, biome_id) in enumerate(samples):
            sample_array[i].x = x
            sample_array[i].z = z
            sample_array[i].y = y
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
    progress_updated = pyqtSignal(float, int, int)  # progress%, speed, eta
    found_seed = pyqtSignal(object)  # Use object to support large uint64 seeds
    finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    biome_info_updated = pyqtSignal(str)  # New signal for biome sorting info
    
    VERSION_MAP = {
        # Bedrock version auto-mapping (based on ChunkBase)
        "26.30+": 38,  # MC_26_2 (Java 26.2, Sulfur Caves)
        "1.21.60-26.23": 29,  # MC_1_21_5 (1.21.5-1.21.11, Pale Garden expanded range)
        "1.21.50": 28,  # MC_1_21_WD (Pale Garden supported with narrow range)
        "1.21-1.21.40": 27,  # MC_1_21_3 (Pale Garden not supported)
        "1.20.60-81": 25,  # MC_1_20
        "1.20.0-51": 25,  # MC_1_20
        "1.19": 24,  # MC_1_19
        "1.18": 22,  # MC_1_18
    }
    
    def __init__(self, low32_value, biomes, start=0, end=4294967295, original_start=None, test_mode=False, mc_version="1.21.50"):
        super().__init__()
        self.low32_value = low32_value
        self.biomes = biomes
        self.start_value = start
        self.original_start_value = original_start if original_start is not None else start  # Use provided or fallback to start
        self.end_value = end
        self.test_mode = test_mode
        self.mc_version_str = mc_version
        self.mc_version = self.VERSION_MAP.get(mc_version, 38)  # Default to 26.30+
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
                y_coord = b.get('y', 200)  # Default to 200 if Y not provided
                if biome_id is not None:
                    biome_samples.append((b['x'], b['z'], y_coord, biome_id))

            if not biome_samples:
                self.error_occurred.emit("No valid biome data")
                return

            # Sort by rarity (lower rarity = more rare = higher priority)
            def get_rarity(biome_id):
                biome_name = None
                for name, data in biome_data.items():
                    if data.get('id') == biome_id:
                        biome_name = name
                        break
                if biome_name and biome_name in biome_data:
                    rarity_dict = biome_data[biome_name].get('rarity', {})
                    # Use mc_version_str (e.g., "1.21.50") instead of mc_version (integer code)
                    return rarity_dict.get(self.mc_version_str, 1.0)
                return 1.0

            biome_samples_sorted = sorted(biome_samples, key=lambda s: get_rarity(s[3]))  # s[3] is biome_id

            # Print sorted biome info (temporary verification)
            biome_info_lines = []
            biome_info_lines.append("="*60)
            biome_info_lines.append("Biome samples (sorted by rarity, rarest first):")
            biome_info_lines.append("="*60)
            for i, (x, z, y, biome_id) in enumerate(biome_samples_sorted, 1):
                biome_name = None
                for name, data in biome_data.items():
                    if data.get('id') == biome_id:
                        biome_name = name
                        break
                rarity = get_rarity(biome_id)
                if biome_name:
                    # Use appropriate language for biome name
                    if lang_manager.language == "zh_CN":
                        biome_display_name = biome_data[biome_name].get('name_zh', biome_name)
                    else:
                        biome_display_name = biome_data[biome_name].get('name_en', biome_name)
                    biome_info_lines.append(f"    {i}. ({x}, {z}, Y={y}) -> {biome_display_name} (ID: {biome_id}, {rarity*100:.4f}%)")
            biome_info_lines.append("="*60)

            # Send biome info to UI
            biome_info_text = "\n" + "\n".join(biome_info_lines) + "\n"
            print(biome_info_text)  # Keep console output for debugging
            self.biome_info_updated.emit(biome_info_text)

            num_processes = mp.cpu_count()
            batch_size = 1000000
            dll_path = get_dll_path()

            print(f"[HIGH32 INFO] Using {num_processes} processes for parallel cracking")
            print(f"[HIGH32 INFO] Low32 value: {self.low32_value}")
            print(f"[HIGH32 INFO] Start value: {self.start_value}")
            print(f"[HIGH32 INFO] End value: {self.end_value}")
            print(f"[HIGH32 INFO] Total range: {self.end_value - self.original_start_value:,}")
            print(f"[HIGH32 INFO] Biome samples: {len(biome_samples_sorted)}")
            print(f"[HIGH32 INFO] DLL path: {dll_path}")
            print(f"[HIGH32 INFO] DLL exists: {os.path.exists(dll_path)}")
            
            if not os.path.exists(dll_path):
                self.error_occurred.emit(f"DLL not found: {dll_path}")
                return
            
            tasks = []
            current = self.start_value
            while current <= self.end_value:
                batch_end = min(current + batch_size - 1, self.end_value)
                tasks.append((current, batch_end + 1, self.low32_value, biome_samples_sorted, 0, self.mc_version))  # Y coord is now per-sample
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

                    # Calculate progress relative to original start value (user's initial setting)
                    total_range = self.end_value - self.original_start_value
                    processed_range = current_position - self.original_start_value
                    progress = (processed_range / total_range) * 100 if total_range > 0 else 100

                    # Calculate speed (seeds per second)
                    speed = int(step_processed / step_elapsed) if step_elapsed > 0 else 0

                    # Calculate ETA (seconds remaining)
                    remaining_seeds = self.end_value - current_position
                    eta = int(remaining_seeds / speed) if speed > 0 else 0

                    print(f"[HIGH32 PROGRESS] {progress:.2f}% | Position: {current_position:,}/{self.end_value:,} | Speed: {speed:,}/s | ETA: {eta}s")

                    self.progress_updated.emit(progress, speed, eta)

                    # Save current position for stop() to use
                    self.last_current_position = current_position

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
            "original_start_value": self.original_start_value,  # Save original user-set start value
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
        # Force save progress before stopping
        if hasattr(self, 'last_current_position'):
            self.save_progress(self.last_current_position)
            print(f"[HIGH32 STOP] Saved progress before stopping: {self.last_current_position:,}")
