from PyQt5.QtCore import QThread, pyqtSignal
import time
import json
import os
import sys
import multiprocessing as mp
import ctypes


def get_dll_path(opencl=False):
    """Get DLL path for CPU or GPU version"""
    dll_name = "crack_low32_opencl.dll" if opencl else "crack_low32.dll"
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        return os.path.join(base_path, "_internal", "dll", "crack_low32", dll_name)
    return os.path.join(os.path.dirname(__file__), "..", "..", "dll", "crack_low32", dll_name)


def get_cl_path():
    """Get OpenCL kernel file path"""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
        return os.path.join(base_path, "_internal", "dll", "crack_low32", "crack_low32.cl")
    return os.path.join(os.path.dirname(__file__), "..", "..", "dll", "crack_low32", "crack_low32.cl")


def get_base_path():
    """Get absolute path of program directory"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_config_path():
    """Get configuration file path"""
    return os.path.join(get_base_path(), "crack_config.json")


def load_config():
    """Load configuration from crack_config.json"""
    config_path = get_config_path()
    default_config = {
        "use_gpu": True,
        "auto_fallback": True,
        "seeds_per_thread": 256,
        "max_results": 10000
    }

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except:
            pass

    return default_config


def has_opencl_gpu():
    """Check if OpenCL GPU is available"""
    try:
        dll_path = get_dll_path(opencl=True)
        if not os.path.exists(dll_path):
            return False, "OpenCL DLL not found"

        lib = ctypes.CDLL(dll_path, winmode=0x00000008)

        lib.has_opencl_gpu.argtypes = []
        lib.has_opencl_gpu.restype = ctypes.c_int

        result = lib.has_opencl_gpu()
        if result:
            lib.get_opencl_device_info.argtypes = [ctypes.c_char_p, ctypes.c_int]
            lib.get_opencl_device_info.restype = ctypes.c_int

            buffer = ctypes.create_string_buffer(256)
            lib.get_opencl_device_info(buffer, 256)
            gpu_info = buffer.value.decode('utf-8')

            # Check compute units to detect old GPUs
            lib.get_gpu_compute_units.argtypes = []
            lib.get_gpu_compute_units.restype = ctypes.c_int

            compute_units = lib.get_gpu_compute_units()
            print(f"[INFO] GPU compute units: {compute_units}")

            # GPUs with <10 compute units are considered too old for GPU acceleration
            if compute_units < 10:
                print(f"[WARNING] GPU has only {compute_units} compute units (too old for GPU mode)")
                print(f"[INFO] Recommending CPU mode for this GPU")
                return False, f"{gpu_info} (old GPU, use CPU mode)"

            return True, gpu_info

        return False, "No OpenCL GPU found"
    except Exception as e:
        return False, str(e)


def crack_worker_cpu(args):
    """CPU worker for multiprocessing"""
    try:
        start, end, r_base, ox, oz, offset_range, spread_type = args

        dll_path = get_dll_path(opencl=False)

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
    compute_device_info = pyqtSignal(str)  # Signal for GPU/CPU device info

    def __init__(self, structures, start=0, end=4294967295, test_mode=False, force_gpu=None):
        super().__init__()
        self.structures = structures
        self.start_value = start
        self.original_start_value = start
        self.end_value = end
        self.test_mode = test_mode
        self.force_gpu = force_gpu  # None=auto, True=force GPU, False=force CPU
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

            # Load configuration
            config = load_config()

            # Determine compute mode
            use_gpu = False
            gpu_device = "N/A"

            if self.force_gpu is False:
                print("[INFO] CPU mode forced")
                use_gpu = False
            elif self.force_gpu is True:
                print("[INFO] GPU mode forced")
                use_gpu = True
            elif config.get('use_gpu', True):
                has_gpu, gpu_info = has_opencl_gpu()
                if has_gpu:
                    print(f"[INFO] GPU detected: {gpu_info}")
                    use_gpu = True
                    gpu_device = gpu_info
                else:
                    print(f"[INFO] GPU not available: {gpu_info}")
                    if config.get('auto_fallback', True):
                        print("[INFO] Auto-fallback to CPU mode")
                        use_gpu = False
                    else:
                        self.error_occurred.emit("GPU not available and auto-fallback disabled")
                        return
            else:
                print("[INFO] CPU mode (from config)")
                use_gpu = False

            num_processes = mp.cpu_count()
            print(f"[INFO] CPU cores: {num_processes}")

            # Compute device info
            compute_device_str = f"GPU ({gpu_device})" if use_gpu else f"CPU ({num_processes} cores)"
            print(f"[INFO] Compute device: {compute_device_str}")

            # Emit compute device info signal
            self.compute_device_info.emit(compute_device_str)

            dll_path = get_dll_path(opencl=use_gpu)

            print(f"[INFO] Start value: {self.start_value}")
            print(f"[INFO] Original start value: {self.original_start_value}")
            print(f"[INFO] End value: {self.end_value}")
            print(f"[INFO] Total range: {self.end_value - self.original_start_value:,}")
            print(f"[INFO] DLL path: {dll_path}")
            print(f"[INFO] DLL exists: {os.path.exists(dll_path)}")

            if not os.path.exists(dll_path):
                self.error_occurred.emit(f"DLL not found: {dll_path}")
                return

            if use_gpu:
                self._run_gpu(r_base, ox, oz, offset_range, spread_type, config)
            else:
                self._run_cpu(r_base, ox, oz, offset_range, spread_type, num_processes)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))

    def _run_cpu(self, r_base, ox, oz, offset_range, spread_type, num_processes):
        """Run crack using CPU multiprocessing"""
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
                    results_list = pool.map(crack_worker_cpu, tasks)

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

    def _run_gpu(self, r_base, ox, oz, offset_range, spread_type, config):
        """Run crack using GPU (OpenCL)"""
        dll_path = get_dll_path(opencl=True)
        cl_path = get_cl_path()

        # Get absolute path BEFORE changing directory
        abs_dll_path = os.path.abspath(dll_path)

        # Change to DLL directory for kernel file
        original_dir = os.getcwd()
        dll_dir = os.path.dirname(abs_dll_path)
        os.chdir(dll_dir)

        try:
            # Add DLL search path for Windows
            if sys.platform == 'win32':
                os.add_dll_directory(dll_dir)

            print(f"[GPU] Loading DLL from: {abs_dll_path}")
            lib = ctypes.CDLL(abs_dll_path, winmode=0x00000008)

            lib.crack_low32_opencl.argtypes = [
                ctypes.c_uint32, ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_int), ctypes.c_int,
                ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
            ]
            lib.crack_low32_opencl.restype = ctypes.c_int

            num_targets = len(r_base)
            r_base_arr = (ctypes.c_uint32 * num_targets)(*r_base)
            ox_arr = (ctypes.c_uint32 * num_targets)(*ox)
            oz_arr = (ctypes.c_uint32 * num_targets)(*oz)
            offset_range_arr = (ctypes.c_uint32 * num_targets)(*offset_range)
            spread_type_arr = (ctypes.c_int * num_targets)(*spread_type)

            max_results = config.get('max_results', 10000)
            results_arr = (ctypes.c_uint32 * max_results)()

            total_range = self.end_value - self.start_value + 1

            # Debug: print structure parameters (only once)
            print(f"[GPU DEBUG] num_targets: {num_targets}")
            for i in range(num_targets):
                print(f"[GPU DEBUG] Structure {i}: r_base={r_base[i]:,}, ox={ox[i]}, oz={oz[i]}, offset_range={offset_range[i]}, spread_type={spread_type[i]}")

            # Batch processing for large ranges
            batch_size = 1_000_000_000  # 1B seeds per batch
            total_batches = (total_range + batch_size - 1) // batch_size

            print(f"[GPU] Running GPU crack: {self.start_value:,} ~ {self.end_value:,}")
            if total_batches > 1:
                print(f"[GPU] Batch mode: {total_batches} batches")

            global_start = time.time()
            processed = self.start_value
            last_save_time = global_start

            while processed <= self.end_value and not self.is_stopped:
                batch_start = processed
                batch_end = min(processed + batch_size - 1, self.end_value)

                batch_start_time = time.time()

                # Emit progress before batch
                progress_pct = (processed - self.start_value) / total_range * 100
                elapsed = time.time() - global_start
                speed = (processed - self.start_value) / elapsed if elapsed > 0 else 0
                eta = (self.end_value - processed) / speed if speed > 0 else 0
                self.progress_updated.emit(progress_pct, int(speed), int(eta))

                found = lib.crack_low32_opencl(
                    batch_start, batch_end,
                    r_base_arr, ox_arr, oz_arr, offset_range_arr, spread_type_arr,
                    num_targets, results_arr, max_results
                )

                if found < 0:
                    print(f"[ERROR] GPU crack failed at batch {processed:,}")
                    if config.get('auto_fallback', True):
                        print("[INFO] Falling back to CPU mode...")
                        num_processes = mp.cpu_count()
                        self._run_cpu(r_base, ox, oz, offset_range, spread_type, num_processes)
                    else:
                        self.error_occurred.emit(f"GPU crack failed: {found}")
                    return

                for i in range(found):
                    seed = results_arr[i]
                    self.results.append(seed)
                    self.found_seed.emit(seed)

                processed = batch_end + 1

                # Progress report (simplified, similar to CPU)
                progress_pct = (processed - self.start_value) / total_range * 100
                elapsed = time.time() - global_start
                speed = (processed - self.start_value) / elapsed if elapsed > 0 else 0
                eta = (self.end_value - processed) / speed if speed > 0 else 0

                print(f"[-] {processed - self.start_value:,}/{total_range:,} ({progress_pct:5.1f}%) | Speed: {speed:,.0f}/s | ETA: {eta:.0f}s")

                self.progress_updated.emit(progress_pct, int(speed), int(eta))

                # Save progress every 60s
                now = time.time()
                if now - last_save_time >= 60:
                    print(f"[SAVE] Saving progress at {processed:,}")
                    self.save_progress(processed)
                    last_save_time = now

            elapsed = time.time() - global_start
            speed = total_range / elapsed if elapsed > 0 else 0

            if not self.is_stopped:
                print(f"[GPU COMPLETE] Found {len(self.results)} seeds in {elapsed:.1f}s ({elapsed/60:.1f}min)")
                print(f"[GPU SPEED] {speed:,.0f} seeds/s")
                self.progress_updated.emit(100, int(speed), 0)
                self.finished.emit(self.results)
            else:
                print(f"[STOPPED] GPU crack stopped at {processed:,}")

        except Exception as e:
            print(f"[ERROR] GPU crack exception: {e}")
            import traceback
            traceback.print_exc()

            if config.get('auto_fallback', True):
                print("[INFO] Falling back to CPU mode...")
                num_processes = mp.cpu_count()
                self._run_cpu(r_base, ox, oz, offset_range, spread_type, num_processes)
            else:
                self.error_occurred.emit(str(e))
        finally:
            os.chdir(original_dir)

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
        if hasattr(self, 'last_current_position'):
            self.save_progress(self.last_current_position)
            print(f"[LOW32 STOP] Saved progress before stopping: {self.last_current_position:,}")