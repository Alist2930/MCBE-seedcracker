from PyQt5.QtCore import QThread, pyqtSignal
import time
import os
import multiprocessing as mp
from ui.utils import native, progress_store
from ui.utils.data_loader import get_biome_id, get_biome_name, get_display_name, get_rarity, load_biome_data
from ui.utils.paths import HIGH32_COMPONENT, HIGH32_DLL, get_dll_path
from ui.utils.parallel import resolve_process_count
from ui.utils.seed_utils import TEST_MODE_END
from ui.utils.version_config import get_cubiomes_version


def crack_batch(args):
    try:
        start_high, end_high, low32, samples, y_coord, mc_version = args

        dll_path = get_dll_path(HIGH32_COMPONENT, HIGH32_DLL)

        if not os.path.exists(dll_path):
            print(f"[ERROR] DLL not found: {dll_path}")
            return []

        crack_high32_soa = native.bind_high32(native.load_library(dll_path))

        seeds = native.call_high32(
            crack_high32_soa, start_high, end_high, low32, samples, y_coord, mc_version
        )
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

    def __init__(self, low32_value, biomes, start=0, end=4294967295, original_start=None, test_mode=False, mc_version="1.21.50", process_count=None):
        super().__init__()
        self.low32_value = low32_value
        self.biomes = biomes
        self.start_value = start
        self.original_start_value = original_start if original_start is not None else start  # Use provided or fallback to start
        self.end_value = end
        self.test_mode = test_mode
        self.mc_version_str = mc_version
        self.mc_version = get_cubiomes_version(mc_version)
        self.user_process_count = process_count  # User-specified process count
        self.is_paused = False
        self.is_stopped = False
        self.results = []

        if test_mode:
            self.end_value = min(end, TEST_MODE_END)

    def run(self):
        try:
            biome_data = load_biome_data()

            biome_samples = []
            for b in self.biomes:
                biome_id = get_biome_id(biome_data, b['type'])
                y_coord = b.get('y', 200)  # Default to 200 if Y not provided
                if biome_id is not None:
                    biome_samples.append((b['x'], b['z'], y_coord, biome_id))

            if not biome_samples:
                self.error_occurred.emit("No valid biome data")
                return

            # Sort by rarity (lower rarity = more rare = higher priority)
            # Use mc_version_str (e.g., "1.21.50") instead of mc_version (integer code)
            def biome_rarity(biome_id):
                biome_name = get_biome_name(biome_data, biome_id)
                return get_rarity(biome_data.get(biome_name, {}), self.mc_version_str)

            biome_samples_sorted = sorted(biome_samples, key=lambda s: biome_rarity(s[3]))  # s[3] is biome_id

            # Print sorted biome info (temporary verification)
            biome_info_lines = []
            biome_info_lines.append("="*60)
            biome_info_lines.append("Biome samples (sorted by rarity, rarest first):")
            biome_info_lines.append("="*60)
            for i, (x, z, y, biome_id) in enumerate(biome_samples_sorted, 1):
                biome_name = get_biome_name(biome_data, biome_id)
                rarity = biome_rarity(biome_id)
                if biome_name:
                    biome_display_name = get_display_name(biome_data[biome_name], biome_name)
                    biome_info_lines.append(f"    {i}. ({x}, {z}, Y={y}) -> {biome_display_name} (ID: {biome_id}, {rarity*100:.4f}%)")
            biome_info_lines.append("="*60)

            # Send biome info to UI
            biome_info_text = "\n" + "\n".join(biome_info_lines) + "\n"
            print(biome_info_text)  # Keep console output for debugging
            self.biome_info_updated.emit(biome_info_text)

            num_processes = resolve_process_count(self.user_process_count, log_prefix="HIGH32 WARNING")

            batch_size = 1000000
            dll_path = get_dll_path(HIGH32_COMPONENT, HIGH32_DLL)

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
                    total_range = self.end_value - self.original_start_value + 1
                    processed_range = current_position - self.original_start_value
                    progress = (processed_range / total_range) * 100 if total_range > 0 else 100
                    # Clamp progress to valid range [0, 100]
                    progress = max(0, min(100, progress))

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
        progress_store.save_progress("high32", {
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
        }, log_prefix="HIGH32 SAVE")


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
