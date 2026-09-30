from PyQt5.QtCore import QThread, pyqtSignal
import time
import json
import os
import sys
import multiprocessing as mp
import ctypes
from ui.utils.language_manager import lang_manager

# 4-chunk grid: a player-reported coordinate may correspond to one of 4 origin chunks:
# (cx,cz), (cx,cz+1), (cx+1,cz), (cx+1,cz+1).
# Only structures with complex generation rules need the grid; others use the exact
# origin chunk (single offset repeated to fill the uniform NUM_OFFSETS slots).
NUM_OFFSETS = 4
FOUR_GRID_STRUCTURES = {"village", "igloo", "pillager_outpost", "ruined_portal_overworld", "ruined_portal_nether"}

# Sampling window (seeds) for the pre-check that estimates the total candidate
# count before the full-range scan; skipped when the search range is smaller
SAMPLE_SEEDS = 1 << 24


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

                # Validate config is a dictionary
                if not isinstance(config, dict):
                    raise ValueError("crack_config.json must contain a JSON object")

                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
            # Log the error but don't crash - use defaults
            print(f"[WARNING] Failed to load config file: {e}")
            print(f"[WARNING] Using default configuration")
        except Exception as e:
            # Catch any other unexpected errors
            print(f"[WARNING] Unexpected error loading config: {e}")
            print(f"[WARNING] Using default configuration")

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
    """CPU worker for multiprocessing (per-structure offsets; 4-chunk grid where applicable)"""
    start, end, r_base, ox, oz, offset_range, spread_type, num_offsets = args

    dll_path = get_dll_path(opencl=False)

    # Check if DLL exists before loading
    if not os.path.exists(dll_path):
        raise RuntimeError(f"crack_low32 DLL not found: {dll_path}")

    lib = ctypes.CDLL(dll_path, winmode=0x00000008)

    lib.crack_low32_grid.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32,
        ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
    ]
    lib.crack_low32_grid.restype = ctypes.c_int

    num_structures = len(offset_range)
    grid_count = num_structures * num_offsets
    r_base_arr = (ctypes.c_uint32 * grid_count)(*r_base)
    ox_arr = (ctypes.c_uint32 * grid_count)(*ox)
    oz_arr = (ctypes.c_uint32 * grid_count)(*oz)
    offset_range_arr = (ctypes.c_uint32 * num_structures)(*offset_range)
    spread_type_arr = (ctypes.c_int * num_structures)(*spread_type)
    results_arr = (ctypes.c_uint32 * 1000)()

    found = lib.crack_low32_grid(start, end, r_base_arr, ox_arr, oz_arr, offset_range_arr, spread_type_arr, num_structures, num_offsets, results_arr, 1000)

    # Check for native function errors
    if found < 0:
        raise RuntimeError(f"crack_low32_grid failed for range {start}-{end} (return code {found})")

    return [results_arr[i] for i in range(found)]


def estimate_candidate_count(sample_start, total_span, r_base, ox, oz, offset_range, spread_type, num_offsets, num_processes):
    """Sampling pre-check: scan a small window with the CPU pool and extrapolate
    the total candidate count over the user's full range (total_span seeds).

    Reuses crack_worker_cpu so the estimate includes the same per-structure
    offsets / 4-chunk grid logic as the real scan.

    Returns (predicted, sampled_found, saturated): saturated is True when a
    worker hit its 1000-result buffer cap, meaning the real count is far higher
    than the extrapolation.
    """
    sample_span = min(total_span, SAMPLE_SEEDS)
    sample_end_exclusive = sample_start + sample_span

    ctx = mp.get_context('spawn')
    pool = ctx.Pool(num_processes)
    sampled_found = 0
    saturated = False
    try:
        step_size = max(1, sample_span // 8)
        processed = sample_start
        while processed < sample_end_exclusive and not saturated:
            step_end = min(processed + step_size, sample_end_exclusive)
            chunk = max(1, (step_end - processed) // num_processes)

            tasks = []
            for i in range(num_processes):
                s = processed + i * chunk
                e = min(processed + (i + 1) * chunk, step_end) if i < num_processes - 1 else step_end
                if s < e:
                    tasks.append((s, e, r_base, ox, oz, offset_range, spread_type, num_offsets))

            for found in pool.map(crack_worker_cpu, tasks):
                sampled_found += len(found)
                if len(found) >= 1000:  # worker result buffer cap reached
                    saturated = True

            processed = step_end
    finally:
        pool.close()
        pool.join()

    predicted = round(sampled_found * total_span / sample_span)
    return predicted, sampled_found, saturated


class Low32Worker(QThread):
    progress_updated = pyqtSignal(float, int, int)
    found_seed = pyqtSignal(object)
    finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    compute_device_info = pyqtSignal(str)  # Signal for GPU/CPU device info
    structure_info_updated = pyqtSignal(str)  # Signal for structure sorting info
    estimate_hint_updated = pyqtSignal(str)  # Signal for candidate-count estimate hint

    def __init__(self, structures, start=0, end=4294967295, test_mode=False, force_gpu=None, process_count=None):
        super().__init__()
        self.structures = structures
        self.start_value = start
        self.original_start_value = start
        self.end_value = end
        self.test_mode = test_mode
        self.force_gpu = force_gpu  # None=auto, True=force GPU, False=force CPU
        self.user_process_count = process_count  # User-specified process count
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
            r_base, ox, oz, offset_range, spread_type, num_offsets, has_zero_sample = self.prepare_structures()

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

            # Determine process count
            # User can specify process count, but it's limited to 16 to avoid resource exhaustion
            max_processes = min(mp.cpu_count(), 16)

            if self.user_process_count is not None:
                # User specified process count
                num_processes = min(self.user_process_count, max_processes)
                if self.user_process_count > max_processes:
                    print(f"[WARNING] Limiting processes from {self.user_process_count} to {max_processes} (to prevent resource exhaustion)")
            else:
                # Default: use maximum allowed (up to 16)
                num_processes = max_processes

            if mp.cpu_count() > 16:
                print(f"[INFO] Limiting processes from {mp.cpu_count()} to {num_processes} (to prevent resource exhaustion)")

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

            # Sampling pre-check: estimate the candidate count before the full scan
            total_span = self.end_value - self.original_start_value + 1
            if total_span > SAMPLE_SEEDS:
                try:
                    est_text = lang_manager.get("estimate_sampling").format(f"{SAMPLE_SEEDS:,}")
                    print(f"[INFO] {est_text}")
                    self.estimate_hint_updated.emit("\n" + est_text + "\n")
                    predicted, sampled, saturated = estimate_candidate_count(
                        self.original_start_value, total_span, r_base, ox, oz,
                        offset_range, spread_type, num_offsets, num_processes)
                    if saturated:
                        hint = lang_manager.get("estimate_saturated").format("10,000")
                    elif predicted <= 0:
                        if has_zero_sample:
                            hint = lang_manager.get("estimate_zero_invalid")
                        else:
                            hint = lang_manager.get("estimate_zero")
                    elif predicted > 10000:
                        hint = lang_manager.get("estimate_many").format(f"{predicted:,}")
                    else:
                        hint = lang_manager.get("estimate_ok").format(f"{predicted:,}")
                    print(f"[INFO] {hint}")
                    self.estimate_hint_updated.emit(hint + "\n")
                except Exception as e:
                    print(f"[WARNING] Candidate estimation skipped: {e}")

            if use_gpu:
                self._run_gpu(r_base, ox, oz, offset_range, spread_type, num_offsets, config)
            else:
                self._run_cpu(r_base, ox, oz, offset_range, spread_type, num_offsets, num_processes)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.error_occurred.emit(str(e))

    def _run_cpu(self, r_base, ox, oz, offset_range, spread_type, num_offsets, num_processes):
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
                        tasks.append((task_start, task_end + 1, r_base, ox, oz, offset_range, spread_type, num_offsets))

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
                # Clamp progress to valid range [0, 100]
                progress = max(0, min(100, progress))
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

    def _run_gpu(self, r_base, ox, oz, offset_range, spread_type, num_offsets, config):
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

            lib.crack_low32_grid_opencl.argtypes = [
                ctypes.c_uint32, ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
                ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int,
                ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
            ]
            lib.crack_low32_grid_opencl.restype = ctypes.c_int

            num_structures = len(offset_range)
            grid_count = num_structures * num_offsets
            r_base_arr = (ctypes.c_uint32 * grid_count)(*r_base)
            ox_arr = (ctypes.c_uint32 * grid_count)(*ox)
            oz_arr = (ctypes.c_uint32 * grid_count)(*oz)
            offset_range_arr = (ctypes.c_uint32 * num_structures)(*offset_range)
            spread_type_arr = (ctypes.c_int * num_structures)(*spread_type)

            max_results = config.get('max_results', 10000)
            results_arr = (ctypes.c_uint32 * max_results)()

            total_range = self.end_value - self.start_value + 1

            # Debug: print structure parameters (only once)
            print(f"[GPU DEBUG] num_structures: {num_structures}, num_offsets: {num_offsets}, grid_count: {grid_count}")
            for s in range(num_structures):
                print(f"[GPU DEBUG] Structure {s}: offset_range={offset_range[s]}, spread_type={spread_type[s]}")
                for g in range(num_offsets):
                    idx = s * num_offsets + g
                    print(f"[GPU DEBUG]   offset {g}: r_base={r_base[idx]:,}, ox={ox[idx]}, oz={oz[idx]}")

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
                progress_pct = (processed - self.original_start_value) / total_range * 100
                # Clamp progress to valid range [0, 100]
                progress_pct = max(0, min(100, progress_pct))
                elapsed = time.time() - global_start
                speed = (processed - self.start_value) / elapsed if elapsed > 0 else 0
                eta = (self.end_value - processed) / speed if speed > 0 else 0
                self.progress_updated.emit(progress_pct, int(speed), int(eta))

                found = lib.crack_low32_grid_opencl(
                    batch_start, batch_end,
                    r_base_arr, ox_arr, oz_arr, offset_range_arr, spread_type_arr,
                    num_structures, num_offsets, results_arr, max_results
                )

                if found < 0:
                    print(f"[ERROR] GPU crack failed at batch {processed:,}")
                    if config.get('auto_fallback', True):
                        print("[INFO] Falling back to CPU mode...")
                        # Use user-specified process count when falling back to CPU
                        max_processes = min(mp.cpu_count(), 16)
                        if self.user_process_count is not None:
                            num_processes = min(self.user_process_count, max_processes)
                        else:
                            num_processes = max_processes
                        if mp.cpu_count() > 16:
                            print(f"[INFO] Limiting processes from {mp.cpu_count()} to {num_processes}")
                        self._run_cpu(r_base, ox, oz, offset_range, spread_type, num_offsets, num_processes)
                    else:
                        self.error_occurred.emit(f"GPU crack failed: {found}")
                    return

                for i in range(found):
                    seed = results_arr[i]
                    self.results.append(seed)
                    self.found_seed.emit(seed)

                processed = batch_end + 1

                # Progress report (simplified, similar to CPU)
                progress_pct = (processed - self.original_start_value) / total_range * 100
                # Clamp progress to valid range [0, 100]
                progress_pct = max(0, min(100, progress_pct))
                elapsed = time.time() - global_start
                speed = (processed - self.start_value) / elapsed if elapsed > 0 else 0
                eta = (self.end_value - processed) / speed if speed > 0 else 0

                print(f"[-] {processed - self.original_start_value:,}/{total_range:,} ({progress_pct:5.1f}%) | Speed: {speed:,.0f}/s | ETA: {eta:.0f}s")

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
                self._run_cpu(r_base, ox, oz, offset_range, spread_type, num_offsets, num_processes)
            else:
                self.error_occurred.emit(str(e))
        finally:
            os.chdir(original_dir)

    def prepare_structures(self):
        CONST_A = 2570712328
        CONST_B = 4048968661

        # Validate all structure types first
        invalid_structures = []
        for i, structure in enumerate(self.structures):
            structure_type = structure.get("type")
            if not structure_type:
                self.error_occurred.emit(f"Structure {i} missing 'type' field")
                return [], [], [], [], [], []

            if structure_type not in self.structure_data:
                invalid_structures.append(structure_type)

        if invalid_structures:
            valid_structures = ", ".join(sorted(self.structure_data.keys()))
            error_msg = (
                f"Invalid structure type(s): {', '.join(invalid_structures)}\n"
                f"Valid structures are: {valid_structures}"
            )
            self.error_occurred.emit(error_msg)
            return [], [], [], [], [], []

        # First sort by spread_type (linear first)
        sorted_structures = sorted(self.structures, key=lambda s: 0 if self.structure_data.get(s["type"], {}).get("spread_type", "linear") == "linear" else 1)

        # Calculate parameters for all structures
        # r_base_list/ox_list/oz_list are flattened: [num_structures * num_offsets]
        # offset_range_list/spread_type_list are per-structure: [num_structures]
        # If no structure needs the 4-chunk grid, use num_offsets=1 (saves 4x MT19937 work in DLL/GPU)
        any_grid = any(s.get("type") in FOUR_GRID_STRUCTURES for s in self.structures)
        num_offsets = NUM_OFFSETS if any_grid else 1
        r_base_list, ox_list, oz_list, offset_range_list, spread_type_list = [], [], [], [], []
        # per_structure_offsets[i] = [(r_base, ox, oz), ...] for strictness test (4 for grid structures, 1 otherwise)
        per_structure_offsets = []

        for structure in sorted_structures:
            structure_type = structure["type"]
            x, z = structure["x"], structure["z"]

            config = self.structure_data.get(structure_type, {})
            spacing = config.get("spacing", 32)
            separation = config.get("separation", 8)
            salt = config.get("salt", 14357617)
            spread_type_str = config.get("spread_type", "linear")

            cx, cz = x >> 4, z >> 4
            spread_type_int = 1 if spread_type_str == "triangular" else 0

            # Grid structures: 4 origin chunks (cx,cz), (cx,cz+1), (cx+1,cz), (cx+1,cz+1)
            # Others: exact origin chunk only (repeated only when some structure uses the grid,
            # to keep the uniform num_offsets layout required by the DLL/OpenCL interface)
            use_grid = structure_type in FOUR_GRID_STRUCTURES
            offsets_for_structure = []
            for dx in ([0, 1] if use_grid else [0]):
                for dz in ([0, 1] if use_grid else [0]):
                    origin_cx = cx + dx
                    origin_cz = cz + dz
                    rx = origin_cx // spacing
                    rz = origin_cz // spacing
                    ox = origin_cx % spacing
                    oz = origin_cz % spacing
                    r_base = (rx * CONST_A + rz * CONST_B + salt) & 0xFFFFFFFF
                    r_base_list.append(r_base)
                    ox_list.append(ox)
                    oz_list.append(oz)
                    offsets_for_structure.append((r_base, ox, oz))

            if not use_grid and num_offsets > 1:
                # Repeat the single exact-chunk offset to fill num_offsets slots
                only = offsets_for_structure[0]
                r_base_list.extend([only[0]] * (num_offsets - 1))
                ox_list.extend([only[1]] * (num_offsets - 1))
                oz_list.extend([only[2]] * (num_offsets - 1))
                offsets_for_structure = [only]

            offset_range_list.append(spacing - separation)
            spread_type_list.append(spread_type_int)
            per_structure_offsets.append(offsets_for_structure)

        # Skip strictness test if search range size < 100000 (test would be redundant)
        skip_strictness = (self.end_value - self.start_value < 100000)

        if skip_strictness:
            print(f"\n[INFO] Search range size < 100000 ({self.end_value - self.start_value}), skipping strictness test")
        else:
            print("\n[INFO] Testing sample strictness (0-100000 seeds)...")

        strictness_scores = []
        structure_info_lines = []
        has_zero_sample = False
        structure_info_lines.append("=" * 80)
        if skip_strictness:
            structure_info_lines.append("Structure samples (strictness test skipped, range size < 100000):")
        else:
            structure_info_lines.append("Structure samples (testing strictness, strictest first):")
        structure_info_lines.append("=" * 80)

        for i, structure in enumerate(sorted_structures):
            structure_type = structure["type"]
            x, z = structure["x"], structure["z"]

            config = self.structure_data.get(structure_type, {})
            spacing = config.get("spacing", 32)
            separation = config.get("separation", 8)

            # Get per-structure offsets (already computed above; 4 for grid structures, 1 otherwise)
            offsets = per_structure_offsets[i]  # [(r_base, ox, oz), ... tuples]
            spread_type_int = spread_type_list[i]
            offset_range = offset_range_list[i]

            if skip_strictness:
                # Skip C library test, just record structure info
                strictness_scores.append(0)
                name = config.get("name_zh", structure_type)
                spread_type_str = "linear" if spread_type_int == 0 else "triangular"
                info_line = f"    {i+1}. {name} at ({x}, {z}) [{spread_type_str}]"
                print(info_line)
                structure_info_lines.append(info_line)
                continue

            # Test using C library (single structure; 4-chunk grid where applicable)
            try:
                dll_path = get_dll_path(opencl=False)
                if os.path.exists(dll_path):
                    lib = ctypes.CDLL(dll_path, winmode=0x00000008)
                    lib.crack_low32_grid.argtypes = [
                        ctypes.c_uint32, ctypes.c_uint32,
                        ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
                        ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
                        ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int,
                        ctypes.POINTER(ctypes.c_uint32), ctypes.c_int
                    ]
                    lib.crack_low32_grid.restype = ctypes.c_int

                    num_offsets = len(offsets)
                    r_base_arr = (ctypes.c_uint32 * num_offsets)(*[o[0] for o in offsets])
                    ox_arr = (ctypes.c_uint32 * num_offsets)(*[o[1] for o in offsets])
                    oz_arr = (ctypes.c_uint32 * num_offsets)(*[o[2] for o in offsets])
                    offset_range_arr = (ctypes.c_uint32 * 1)(offset_range)
                    spread_type_arr = (ctypes.c_int * 1)(spread_type_int)
                    results_arr = (ctypes.c_uint32 * 100000)()

                    found = lib.crack_low32_grid(
                        0, 100000,
                        r_base_arr, ox_arr, oz_arr, offset_range_arr, spread_type_arr,
                        1, num_offsets,  # num_structures=1, num_offsets per grid membership
                        results_arr, 100000
                    )

                    strictness_scores.append(found)
                    name = config.get("name_zh", structure_type)
                    spread_type_str = "linear" if spread_type_int == 0 else "triangular"
                    match_rate = found / 100000 * 100

                    info_line = f"    {i+1}. {name} at ({x}, {z}): {found}/100000 matches ({match_rate:.4f}%) [{spread_type_str}]"
                    print(info_line)
                    structure_info_lines.append(info_line)
                    if found == 0:
                        has_zero_sample = True
                        zero_line = "    " + lang_manager.get("strictness_zero_sample").format(f"{name} ({x}, {z})")
                        print(zero_line)
                        structure_info_lines.append(zero_line)
                else:
                    strictness_scores.append(0)
                    warning_line = f"    {i+1}. [WARNING] DLL not found for strictness test"
                    print(warning_line)
                    structure_info_lines.append(warning_line)
            except Exception as e:
                strictness_scores.append(0)
                error_line = f"    {i+1}. [WARNING] Failed to test strictness: {e}"
                print(error_line)
                structure_info_lines.append(error_line)

        structure_info_lines.append("=" * 80)

        # Sort by strictness (fewer matches = stricter = higher priority)
        # But maintain linear-first ordering
        indices = list(range(len(sorted_structures)))

        # Separate linear and triangular
        linear_indices = [i for i in indices if spread_type_list[i] == 0]
        triangular_indices = [i for i in indices if spread_type_list[i] == 1]

        # Sort each group by strictness (ascending = stricter first)
        linear_indices.sort(key=lambda i: strictness_scores[i])
        triangular_indices.sort(key=lambda i: strictness_scores[i])

        # Combine: linear first, then triangular
        sorted_indices = linear_indices + triangular_indices

        # Reorder all lists (r_base/ox/oz are flattened with num_offsets entries per structure)
        r_base_list = [v for i in sorted_indices for v in r_base_list[i*num_offsets:(i+1)*num_offsets]]
        ox_list = [v for i in sorted_indices for v in ox_list[i*num_offsets:(i+1)*num_offsets]]
        oz_list = [v for i in sorted_indices for v in oz_list[i*num_offsets:(i+1)*num_offsets]]
        offset_range_list = [offset_range_list[i] for i in sorted_indices]
        spread_type_list = [spread_type_list[i] for i in sorted_indices]

        # Print optimized order
        if skip_strictness:
            structure_info_lines.append("\nSample order (strictness test skipped, linear first):")
        else:
            structure_info_lines.append("\nOptimized sample order (strictest first, linear优先):")
        structure_info_lines.append("=" * 80)
        order_info = []
        for i, idx in enumerate(sorted_indices):
            structure = sorted_structures[idx]
            config = self.structure_data.get(structure["type"], {})
            name = config.get("name_zh", structure["type"])
            spread_type = "linear" if spread_type_list[i] == 0 else "triangular"
            strictness = strictness_scores[idx]
            match_rate = strictness / 100000 * 100
            grid_flag = "4-grid" if len(per_structure_offsets[idx]) > 1 else "exact"

            if skip_strictness:
                order_line = f"    {i+1}. {name} at ({structure['x']}, {structure['z']}) [{spread_type}, {grid_flag}]"
            else:
                order_line = f"    {i+1}. {name} at ({structure['x']}, {structure['z']}) [{spread_type}, {grid_flag}] - {strictness}/100000 ({match_rate:.4f}%)"
            print(order_line)
            structure_info_lines.append(order_line)

            # Simplified format for UI: "(x, z) -> 结构名 (spread_type)"
            # Use appropriate language for structure name
            if lang_manager.language == "zh_CN":
                display_name = config.get("name_zh", structure["type"])
            else:
                display_name = config.get("name_en", structure["type"])

            order_info.append({
                "x": structure['x'],
                "z": structure['z'],
                "name": display_name,
                "spread_type": spread_type
            })
        structure_info_lines.append("=" * 80)

        # Send structure info to UI
        structure_info_text = "\n" + "\n".join(structure_info_lines) + "\n"
        print(structure_info_text)  # Keep console output for debugging

        # Send simplified order info as JSON string
        import json
        self.structure_info_updated.emit(json.dumps(order_info))

        return r_base_list, ox_list, oz_list, offset_range_list, spread_type_list, num_offsets, has_zero_sample

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