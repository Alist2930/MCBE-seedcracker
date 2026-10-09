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


def test_biome_strictness(sample, low32, mc_version, num_test_seeds=100000):
    """
    Test the strictness (matching probability) of a biome sample.
    Tests num_test_seeds high32 candidates and counts how many produce the target biome.
    Returns the match count (lower = stricter = rarer = higher priority).

    Args:
        sample: (x, z, y, biome_id) tuple
        low32: Known low 32-bit value
        mc_version: cubiomes version constant (integer)
        num_test_seeds: Number of high32 candidates to test (default 100000)

    Returns:
        Number of matches (lower = stricter)
    """
    if len(sample) == 4:
        x, z, y, biome_id = sample
    else:
        x, z, biome_id = sample
        y = 200

    dll_path = get_dll_path()
    if not os.path.exists(dll_path):
        print(f"[ERROR] DLL not found: {dll_path}")
        return 0

    dll = ctypes.CDLL(dll_path, winmode=0x00000008)

    dll.crack_high32_soa.argtypes = [
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_int,
        ctypes.POINTER(BiomeSample), ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint64), ctypes.c_int, ctypes.c_int
    ]
    dll.crack_high32_soa.restype = ctypes.c_int

    sample_array = (BiomeSample * 1)()
    sample_array[0].x = x
    sample_array[0].z = z
    sample_array[0].y = y
    sample_array[0].biome_id = biome_id

    results = (ctypes.c_uint64 * num_test_seeds)()

    found = dll.crack_high32_soa(
        0, num_test_seeds, low32, 0,
        sample_array, 1,
        results, num_test_seeds, mc_version
    )

    if found < 0:
        print(f"[ERROR] crack_high32_soa failed during strictness test (return code {found})")
        return 0

    return found


# ===== Java LCG structure cracking (phase 2: bits 32-47) =====
# Java LCG constants (cubiomes-bedrock algorithm)
JLCG_K = 0x5DEECE66D
JLCG_M48 = (1 << 48) - 1
JLCG_B = 0xB
JLCG_A_REG = 341873128712
JLCG_B_REG = 132897987541


def crack_high16_java_lcg(low32, lcg_structures, search_start=0, search_end=0xFFFFFFFF):
    """
    Phase 2: Brute-force bits 32-47 using Java LCG structures.
    Only searches h16 values whose range overlaps with [search_start, search_end].

    Args:
        low32: Known lower 32 bits of the seed.
        lcg_structures: List of dicts with keys: type, x, z (block coordinates)
        search_start: User's high32 search start (inclusive)
        search_end: User's high32 search end (inclusive)

    Returns:
        List of 16-bit values (bits 32-47) that match all targets.
    """
    # Load structure configs from structures.json
    data_file = os.path.join(os.path.dirname(__file__), "..", "data", "structures.json")
    with open(data_file, 'r', encoding='utf-8') as f:
        all_structures = json.load(f)

    # Prepare constraints: per-structure list of 4 (r_const, target_ox, target_oz) offsets.
    # 4-chunk grid: a player-reported coordinate may correspond to one of 4 origin chunks:
    # (cx,cz), (cx,cz+1), (cx+1,cz), (cx+1,cz+1). A structure matches if ANY offset matches.
    structure_constraints = []  # [(chunk_range, [(r_const, target_ox, target_oz), ...4]), ...]
    for s in lcg_structures:
        stype = s.get('type')
        config = all_structures.get(stype)
        if not config or config.get('rng_type') != 'java_lcg':
            continue
        spacing = config['spacing']
        separation = config['separation']
        chunk_range = spacing - separation
        salt = config['salt']
        cx = s['x'] >> 4  # block to chunk
        cz = s['z'] >> 4

        offsets = []
        for dx in [0, 1]:
            for dz in [0, 1]:
                origin_cx = cx + dx
                origin_cz = cz + dz
                rx = origin_cx // spacing
                rz = origin_cz // spacing
                target_ox = origin_cx % spacing
                target_oz = origin_cz % spacing
                r_const = (rx * JLCG_A_REG + rz * JLCG_B_REG + salt) & JLCG_M48
                offsets.append((r_const, target_ox, target_oz))
        structure_constraints.append((chunk_range, offsets))

    if not structure_constraints:
        return []

    # Brute-force h16 candidates (bits 32-47)
    # h16 is valid iff its minimum possible high32 (h16 itself, upper=0) <= end
    # and its maximum possible high32 (0xFFFF0000 + h16, upper=0xFFFF) >= start
    min_h16 = 0
    if search_start > 0xFFFF0000:
        min_h16 = search_start - 0xFFFF0000
    max_h16 = min(0xFFFF, search_end)

    candidates = []
    for h16 in range(min_h16, max_h16 + 1):
        candidate_48 = (h16 << 32) | low32
        all_match = True
        for chunk_range, offsets in structure_constraints:
            structure_matched = False
            for r_const, target_ox, target_oz in offsets:
                region_seed = (candidate_48 + r_const) & JLCG_M48
                seed = region_seed ^ JLCG_K
                seed = (seed * JLCG_K + JLCG_B) & JLCG_M48
                ox = (seed >> 17) % chunk_range
                if ox != target_ox:
                    continue
                seed = (seed * JLCG_K + JLCG_B) & JLCG_M48
                oz = (seed >> 17) % chunk_range
                if oz != target_oz:
                    continue
                structure_matched = True
                break
            if not structure_matched:
                all_match = False
                break
        if all_match:
            candidates.append(h16)

    return candidates


def crack_batch_lcg_phase3(args):
    """Phase 3 wrapper: Call crack_high32_lcg_phase3 for non-contiguous high32 search.

    Iterates bits_48_63 (upper) with fixed h16 (bits 32-47).
    high32 = (upper << 16) | h16, so valid high32 values are spaced 65536 apart.
    """
    try:
        h16, low32, min_upper, max_upper, samples, mc_version = args

        dll_path = get_dll_path()

        if not os.path.exists(dll_path):
            print(f"[ERROR] DLL not found: {dll_path}")
            return []

        dll = ctypes.CDLL(dll_path, winmode=0x00000008)

        dll.crack_high32_lcg_phase3.argtypes = [
            ctypes.c_uint16,    # h16 (fixed bits 32-47)
            ctypes.c_uint32,    # low32
            ctypes.c_uint16,    # min_upper (bits 48-63, inclusive)
            ctypes.c_uint16,    # max_upper (bits 48-63, inclusive)
            ctypes.POINTER(BiomeSample), ctypes.c_int,
            ctypes.POINTER(ctypes.c_uint64), ctypes.c_int, ctypes.c_int
        ]
        dll.crack_high32_lcg_phase3.restype = ctypes.c_int

        num_samples = len(samples)
        sample_array = (BiomeSample * num_samples)()
        for i, (x, z, y, biome_id) in enumerate(samples):
            sample_array[i].x = x
            sample_array[i].z = z
            sample_array[i].y = y
            sample_array[i].biome_id = biome_id

        MAX_RESULTS = 1000
        results = (ctypes.c_uint64 * MAX_RESULTS)()

        found = dll.crack_high32_lcg_phase3(
            h16, low32, min_upper, max_upper,
            sample_array, num_samples,
            results, MAX_RESULTS, mc_version
        )

        if found < 0:
            print(f"[ERROR] crack_high32_lcg_phase3 failed (return code {found})")
            return []

        seeds = [results[i] for i in range(found)]
        if seeds:
            print(f"[DEBUG] Found {len(seeds)} seeds for h16=0x{h16:04X}")

        return seeds
    except Exception as e:
        print(f"[ERROR] crack_batch_lcg_phase3 exception: {e}")
        return []


# Sampling window (high32 values) for the pre-check that estimates the final
# candidate count before the full-range biome-only scan
SAMPLE_SEEDS_HIGH = 1 << 17


def estimate_candidate_count_high32(sample_start, total_span, samples, low32, num_processes, mc_version):
    """Sampling pre-check for biome-only mode: scan a small high32 window with the
    same worker as the real scan (crack_batch) and extrapolate the candidate
    count over the user's full range (total_span values).

    Returns (predicted, sampled_found, saturated): saturated is True when a
    worker hit its 1000-result buffer cap, meaning the real count is far higher
    than the extrapolation.
    """
    sample_span = min(total_span, SAMPLE_SEEDS_HIGH)
    sample_end_exclusive = sample_start + sample_span

    ctx = mp.get_context('spawn')
    pool = ctx.Pool(num_processes)
    sampled_found = 0
    saturated = False
    try:
        chunk = max(1, sample_span // num_processes)
        pos = sample_start
        while pos < sample_end_exclusive and not saturated:
            tasks = []
            for i in range(num_processes):
                s = pos + i * chunk
                e = min(pos + (i + 1) * chunk, sample_end_exclusive) if i < num_processes - 1 else sample_end_exclusive
                if s < e:
                    tasks.append((s, e, low32, samples, 0, mc_version))
            if tasks:
                for found in pool.map(crack_batch, tasks):
                    sampled_found += len(found)
                    if len(found) >= 1000:  # worker result buffer cap reached
                        saturated = True
            pos += chunk * num_processes
    finally:
        pool.close()
        pool.join()

    predicted = round(sampled_found * total_span / sample_span)
    return predicted, sampled_found, saturated


class High32Worker(QThread):
    progress_updated = pyqtSignal(float, int, int)  # progress%, speed, eta
    found_seed = pyqtSignal(object)  # Use object to support large uint64 seeds
    finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    biome_info_updated = pyqtSignal(str)  # New signal for biome sorting info
    
    VERSION_MAP = {
        # Bedrock version auto-mapping (based on ChunkBase)
        "26.50": 35,  # MC_26_3 (Java 26.3, Dappled Forest)
        "26.30-26.40": 34,  # MC_26_2 (Java 26.2, Sulfur Caves)
        "1.21.60-26.23": 29,  # MC_1_21_5 (1.21.5-1.21.11, Pale Garden expanded range)
        "1.21.50": 28,  # MC_1_21_WD (Pale Garden supported with narrow range)
        "1.21-1.21.40": 27,  # MC_1_21_3 (Pale Garden not supported)
        "1.20.60-81": 25,  # MC_1_20
        "1.20.0-51": 25,  # MC_1_20
        "1.19": 24,  # MC_1_19
        "1.18": 22,  # MC_1_18
    }
    
    def __init__(self, low32_value, biomes, start=0, end=4294967295, original_start=None, test_mode=False, mc_version="1.21.50", process_count=None, lcg_structures=None):
        super().__init__()
        self.low32_value = low32_value
        self.biomes = biomes
        self.start_value = start
        self.original_start_value = original_start if original_start is not None else start  # Use provided or fallback to start
        self.end_value = end
        self.test_mode = test_mode
        self.mc_version_str = mc_version
        self.mc_version = self.VERSION_MAP.get(mc_version, 35)  # Default to 26.50
        self.user_process_count = process_count  # User-specified process count
        self.lcg_structures = lcg_structures or []  # Optional Java LCG structures for phase 2
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

            # A single (x, z, y) point cannot hold two different biomes - block contradictory input
            point_biomes = {}
            for sample in biome_samples:
                x, z, y, biome_id = sample
                point_biomes.setdefault((x, z, y), set()).add(biome_id)

            def _biome_display(bid):
                for name, data in biome_data.items():
                    if isinstance(data, dict) and data.get('id') == bid:
                        key = 'name_zh' if lang_manager.language == "zh_CN" else 'name_en'
                        return data.get(key, name)
                return str(bid)

            conflict_lines = []
            for (x, z, y), ids in point_biomes.items():
                if len(ids) > 1:
                    joined = ", ".join(f"{_biome_display(bid)} (ID: {bid})" for bid in sorted(ids))
                    conflict_lines.append(f"({x}, {z}, Y={y}): {joined}")
            if conflict_lines:
                err = lang_manager.get("conflicting_biome_samples").format("\n".join(conflict_lines))
                print(f"[HIGH32 ERROR] {err}")
                self.error_occurred.emit(err)
                return

            # Skip strictness test if search range size < 100000 (test would be redundant)
            skip_strictness = (self.end_value - self.start_value < 100000)

            if skip_strictness:
                print(f"\n[HIGH32 INFO] Search range size < 100000 ({self.end_value - self.start_value}), skipping strictness test")
                biome_samples_sorted = biome_samples
                sorted_scores = []
            else:
                # Sort by empirical strictness (fewest matches = rarest = first)
                print(f"\n[HIGH32 INFO] Testing biome sample strictness (0-100000 high32 seeds)...")
                strictness_scores = []
                for sample in biome_samples:
                    matches = test_biome_strictness(sample, self.low32_value, self.mc_version, num_test_seeds=100000)
                    strictness_scores.append(matches)

                # Sort ascending (fewer matches = stricter = first)
                paired = list(zip(strictness_scores, biome_samples))
                paired.sort(key=lambda p: p[0])
                biome_samples_sorted = [s for _, s in paired]
                sorted_scores = [sc for sc, _ in paired]

            # Print biome info
            biome_info_lines = []
            biome_info_lines.append("="*60)
            if skip_strictness:
                biome_info_lines.append("Biome samples (strictness test skipped, range size < 100000):")
            else:
                biome_info_lines.append("Biome samples (sorted by strictness, rarest first):")
            biome_info_lines.append("="*60)
            for i, (x, z, y, biome_id) in enumerate(biome_samples_sorted, 1):
                biome_name = None
                for name, data in biome_data.items():
                    if data.get('id') == biome_id:
                        biome_name = name
                        break
                if biome_name:
                    # Use appropriate language for biome name
                    if lang_manager.language == "zh_CN":
                        biome_display_name = biome_data[biome_name].get('name_zh', biome_name)
                    else:
                        biome_display_name = biome_data[biome_name].get('name_en', biome_name)
                    if skip_strictness:
                        biome_info_lines.append(f"    {i}. ({x}, {z}, Y={y}) -> {biome_display_name} (ID: {biome_id})")
                    else:
                        score = sorted_scores[i-1]
                        match_pct = score / 100000 * 100
                        biome_info_lines.append(f"    {i}. ({x}, {z}, Y={y}) -> {biome_display_name} (ID: {biome_id}) - {score}/100000 matches ({match_pct:.4f}%)")
                        if score == 0:
                            biome_info_lines.append("    " + lang_manager.get("strictness_zero_sample").format(f"{biome_display_name} ({x}, {z})", "100000"))
            biome_info_lines.append("="*60)

            # Send biome info to UI
            biome_info_text = "\n" + "\n".join(biome_info_lines) + "\n"
            print(biome_info_text)  # Keep console output for debugging
            self.biome_info_updated.emit(biome_info_text)

            # Determine process count
            # User can specify process count, but it's limited to 16 to avoid resource exhaustion
            # On systems with >16 cores, using all cores causes:
            # - DLL loading conflicts (multiple processes loading same .dll)
            # - Memory bandwidth saturation
            # - Cache contention
            max_processes = min(mp.cpu_count(), 16)

            if self.user_process_count is not None:
                # User specified process count
                num_processes = min(self.user_process_count, max_processes)
                if self.user_process_count > max_processes:
                    print(f"[HIGH32 WARNING] Limiting processes from {self.user_process_count} to {max_processes} (to prevent resource exhaustion)")
            else:
                # Default: use maximum allowed (up to 16)
                num_processes = max_processes

            if mp.cpu_count() > 16:
                print(f"[HIGH32 INFO] Limiting processes from {mp.cpu_count()} to {num_processes} (to prevent resource exhaustion)")

            # ===== Java LCG phase 2+3 (if structures provided) =====
            if self.lcg_structures:
                # Phase 2: Java LCG brute-force bits 32-47 (2^16 candidates)
                phase2_msg = "\n" + lang_manager.get("lcg_phase2_start") + "\n"
                print(phase2_msg)
                self.biome_info_updated.emit(phase2_msg)
                self.progress_updated.emit(0, 0, 0)

                t0 = time.time()
                h16_candidates = crack_high16_java_lcg(self.low32_value, self.lcg_structures, self.start_value, self.end_value)
                elapsed_p2 = time.time() - t0

                if not h16_candidates:
                    msg = lang_manager.get("lcg_phase2_no_candidates")
                    print(f"[HIGH32 ERROR] {msg}")
                    self.error_occurred.emit(msg)
                    return

                phase2_done_msg = "\n" + lang_manager.get("lcg_phase2_done").format(len(h16_candidates), elapsed_p2) + "\n"
                print(phase2_done_msg)
                self.biome_info_updated.emit(phase2_done_msg)

                # Phase 3: Biome verify bits 48-63 per candidate (2^16 each)
                phase3_msg = "\n" + lang_manager.get("lcg_phase3_start") + "\n"
                print(phase3_msg)
                self.biome_info_updated.emit(phase3_msg)

                # Precompute valid upper ranges per candidate (high32 = (upper << 16) | h16)
                valid_candidates = []
                total_uppers = 0
                for h16 in h16_candidates:
                    # Need start <= high32 <= end
                    if self.end_value < h16:
                        continue
                    if self.start_value <= h16:
                        min_upper = 0
                    else:
                        min_upper = (self.start_value - h16 + 65535) // 65536
                    max_upper = min(0xFFFF, (self.end_value - h16) // 65536)
                    if min_upper > max_upper:
                        continue
                    range_size = max_upper - min_upper + 1
                    valid_candidates.append((h16, min_upper, max_upper, range_size))
                    total_uppers += range_size

                total_candidates = len(valid_candidates)
                dll_path = get_dll_path()
                if not os.path.exists(dll_path):
                    self.error_occurred.emit(f"DLL not found: {dll_path}")
                    return

                start_time = time.time()
                done_uppers = 0

                # Parallel Phase 3: same spawn process pool as the normal path
                ctx = mp.get_context('spawn')
                tasks = [(h, self.low32_value, min_u, max_u, biome_samples_sorted, self.mc_version)
                         for (h, min_u, max_u, _rs) in valid_candidates]

                with ctx.Pool(num_processes) as pool:
                    for i, seeds in enumerate(pool.imap(crack_batch_lcg_phase3, tasks)):
                        if self.is_stopped:
                            break

                        while self.is_paused:
                            time.sleep(0.1)
                            if self.is_stopped:
                                return

                        done_uppers += valid_candidates[i][3]

                        for seed in seeds:
                            self.results.append(seed)
                            self.found_seed.emit(seed)

                        # Progress per candidate
                        progress = ((i + 1) / total_candidates) * 100 if total_candidates else 100
                        elapsed = time.time() - start_time
                        speed = int(done_uppers / elapsed) if elapsed > 0 else 0
                        eta = int((total_uppers - done_uppers) / speed) if speed > 0 else 0
                        self.progress_updated.emit(progress, speed, eta)

                        print(f"[HIGH32 LCG PROGRESS] {progress:.1f}% | Candidate {i+1}/{total_candidates} | Speed: {speed:,}/s | ETA: {eta}s | Found: {len(self.results)}")

                if not self.is_stopped:
                    print(f"[HIGH32 LCG COMPLETE] Finished! Found {len(self.results)} seeds")
                    self.finished.emit(self.results)
                return
            # ===== End Java LCG phase =====

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
            
            # Sampling pre-check: estimate the final candidate count before the full scan
            total_span = self.end_value - self.original_start_value + 1
            has_zero_sample = any(sc == 0 for sc in sorted_scores)
            if total_span > SAMPLE_SEEDS_HIGH:
                try:
                    est_text = lang_manager.get("estimate_sampling").format(f"{SAMPLE_SEEDS_HIGH:,}")
                    print(f"[HIGH32 INFO] {est_text}")
                    self.biome_info_updated.emit("\n" + est_text + "\n")
                    predicted, sampled, saturated = estimate_candidate_count_high32(
                        self.original_start_value, total_span, biome_samples_sorted,
                        self.low32_value, num_processes, self.mc_version)
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
                    print(f"[HIGH32 INFO] {hint}")
                    self.biome_info_updated.emit(hint + "\n")
                except Exception as e:
                    print(f"[WARNING] Candidate estimation skipped: {e}")

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
