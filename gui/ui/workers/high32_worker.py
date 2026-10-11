# -*- coding: utf-8 -*-
"""High 32-bit cracking worker (GUI frontend, thin shell over core.high32).

The QThread shell and all signals are kept identical to the old self-contained
worker; all cracking logic (sample prep, strictness testing, Java LCG two-phase
mode, biome-only SOA scan) lives in core.high32 and is driven through a
Reporter bridge + Control events. Localized UI text (conflict errors, LCG phase
messages, estimate hints) is produced in this bridge; core stays English-only.
"""
import json
import os
import re
import sys
import threading
import time
import traceback

from PyQt5.QtCore import QThread, pyqtSignal

# Make the repo root importable (needed for `core.*`; spawn workers inherit it)
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[3]))

from ui.utils.config_manager import get_base_path
from ui.utils.language_manager import lang_manager
from core import high32 as core_high32
from core.reporter import Reporter, Control

# Sampling window (high32 values) for the estimate pre-message; core skips the
# estimate itself when the range is smaller, so the condition must match
SAMPLE_SEEDS_HIGH = core_high32.SAMPLE_SEEDS_HIGH


class WorkerBridge(Reporter):
    """Forwards core events to the worker's Qt signals (parent process only)."""

    def __init__(self, worker):
        self.worker = worker
        self.last_current = worker.start_value
        self.last_save_time = time.time()
        self.lcg_mode = False
        self.phase2_empty = False
        self._p2_elapsed = None

    def info(self, text):
        print(f"[HIGH32 INFO] {text}")
        # LCG phase transitions: re-emit the localized UI messages at the same
        # points as the old worker (core stays English-only)
        if text.startswith("Phase 2: Java LCG"):
            self.lcg_mode = True
            msg = "\n" + lang_manager.get("lcg_phase2_start") + "\n"
            self.worker.biome_info_updated.emit(msg)
            self.worker.progress_updated.emit(0, 0, 0)
        elif "Phase 2 done in" in text:
            m = re.search(r"done in ([\d.]+)s", text)
            self._p2_elapsed = float(m.group(1)) if m else 0.0
        elif "candidate(s) for bits 32-47" in text:
            m = re.search(r"Found (\d+) candidate", text)
            n = int(m.group(1)) if m else 0
            if n == 0:
                self.phase2_empty = True
            else:
                msg = "\n" + lang_manager.get("lcg_phase2_done").format(n, self._p2_elapsed or 0.0) + "\n"
                self.worker.biome_info_updated.emit(msg)
        elif text.startswith("Phase 3: Biome verify"):
            msg = "\n" + lang_manager.get("lcg_phase3_start") + "\n"
            self.worker.biome_info_updated.emit(msg)

    def detail(self, text):
        print(text)

    def warn(self, text):
        print(f"[HIGH32 WARNING] {text}")

    def error(self, text):
        print(f"[HIGH32 ERROR] {text}")

    def sample_info(self, samples, scores):
        # Full localized biome listing block (same format as the old worker)
        skip = not scores
        lines = ["=" * 60]
        if skip:
            lines.append("Biome samples (strictness test skipped, range size < 100000):")
        else:
            lines.append("Biome samples (sorted by strictness, rarest first):")
        lines.append("=" * 60)
        for i, sample in enumerate(samples, 1):
            x, z, y, biome_id = core_high32._sample_xyz(sample)
            name = self.worker.biome_display(biome_id)
            if skip:
                lines.append(f"    {i}. ({x}, {z}, Y={y}) -> {name} (ID: {biome_id})")
            else:
                score = scores[i - 1]
                match_pct = score / 100000 * 100
                lines.append(f"    {i}. ({x}, {z}, Y={y}) -> {name} (ID: {biome_id}) - {score}/100000 matches ({match_pct:.4f}%)")
                if score == 0:
                    lines.append("    " + lang_manager.get("strictness_zero_sample").format(f"{name} ({x}, {z})", "100000"))
        lines.append("=" * 60)
        self.worker.biome_info_updated.emit("\n" + "\n".join(lines) + "\n")

    def progress(self, current, total, speed, eta, found=None, note=None):
        worker = self.worker
        if self.lcg_mode:
            # LCG mode: current/total are upper16 counts, not seed positions
            progress = current / max(total, 1) * 100
            progress = max(0, min(100, progress))
            note_str = f" | {note}" if note else ""
            print(f"[HIGH32 LCG PROGRESS] {progress:.1f}%{note_str} | Speed: {int(speed):,}/s | ETA: {int(eta)}s | Found: {found or 0}")
            worker.progress_updated.emit(progress, int(speed), int(eta))
            return
        absolute = worker.start_value + current
        self.last_current = absolute
        total_range = worker.end_value - worker.original_start_value + 1
        progress = (absolute - worker.original_start_value) / total_range * 100 if total_range > 0 else 100
        # Clamp progress to valid range [0, 100]
        progress = max(0, min(100, progress))
        print(f"[HIGH32 PROGRESS] {progress:.2f}% | Position: {absolute:,}/{worker.end_value:,} | Speed: {int(speed):,}/s | ETA: {int(eta)}s")
        worker.progress_updated.emit(progress, int(speed), int(eta))
        # Throttled session save (60s), same cadence as the old worker loop
        now = time.time()
        if now - self.last_save_time >= 60:
            print(f"[HIGH32 SAVE] Saving progress at {absolute:,}")
            worker.save_progress(absolute)
            self.last_save_time = now

    def result(self, seed):
        self.worker.found_seed.emit(seed)

    def estimation(self, est):
        # Four-tier hint: levels decided in core, text localized here
        if est.get('saturated'):
            hint = lang_manager.get("estimate_saturated").format("10,000")
        elif est.get('predicted', 0) <= 0:
            if est.get('has_zero_sample'):
                hint = lang_manager.get("estimate_zero_invalid")
            else:
                hint = lang_manager.get("estimate_zero")
        elif est.get('predicted', 0) > 10000:
            hint = lang_manager.get("estimate_many").format(f"{est['predicted']:,}")
        else:
            hint = lang_manager.get("estimate_ok").format(f"{est['predicted']:,}")
        print(f"[HIGH32 INFO] {hint}")
        self.worker.biome_info_updated.emit(hint + "\n")


class High32Worker(QThread):
    progress_updated = pyqtSignal(float, int, int)  # progress%, speed, eta
    found_seed = pyqtSignal(object)  # Use object to support large uint64 seeds
    finished = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    biome_info_updated = pyqtSignal(str)  # Signal for biome sorting info

    def __init__(self, low32_value, biomes, start=0, end=4294967295, original_start=None, test_mode=False, mc_version="1.21.50", process_count=None, lcg_structures=None):
        super().__init__()
        self.low32_value = low32_value
        self.biomes = biomes
        self.start_value = start
        self.original_start_value = original_start if original_start is not None else start  # Use provided or fallback to start
        self.end_value = end
        self.test_mode = test_mode
        self.mc_version_str = mc_version  # Core normalizes and maps to cubiomes constant
        self.user_process_count = process_count  # User-specified process count
        self.lcg_structures = lcg_structures or []  # Optional Java LCG structures for phase 2
        self.results = []
        self._biome_data = {}

        if test_mode:
            self.end_value = min(end, 100000000)

        self.progress_file = os.path.join(get_base_path(), "progress_high32.json")

        # Pause/stop honored inside core via Control
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.control = Control(stop_event=self.stop_event, pause_event=self.pause_event)
        self._bridge = None

    def biome_display(self, biome_id):
        """Localized biome display name from biomes.json (ID lookup)."""
        for name, data in self._biome_data.items():
            if isinstance(data, dict) and data.get('id') == biome_id:
                key = 'name_zh' if lang_manager.language == "zh_CN" else 'name_en'
                return data.get(key, name)
        return str(biome_id)

    def run(self):
        try:
            # Biome name -> ID mapping from the core registry (display data too)
            biome_file = os.path.join(os.path.dirname(core_high32.__file__), "data", "biomes.json")
            with open(biome_file, 'r', encoding='utf-8') as f:
                self._biome_data = json.load(f)

            biome_samples = []
            for b in self.biomes:
                biome_id = self._biome_data.get(b['type'], {}).get('id')
                y_coord = b.get('y', 200)  # Default to 200 if Y not provided
                if biome_id is not None:
                    biome_samples.append((b['x'], b['z'], y_coord, biome_id))

            if not biome_samples:
                self.error_occurred.emit("No valid biome data")
                return

            # One (x, z, y) point cannot hold two biomes - localized error here,
            # core only re-validates (in English) as a safety net
            conflict_lines = core_high32.check_biome_conflicts(biome_samples)
            if conflict_lines:
                localized = []
                for line in conflict_lines:
                    def _localize(m):
                        return self.biome_display(int(m.group(1)))
                    localized.append(re.sub(r"ID: (\d+)", _localize, line))
                err = lang_manager.get("conflicting_biome_samples").format("\n".join(localized))
                print(f"[HIGH32 ERROR] {err}")
                self.error_occurred.emit(err)
                return

            # Localized "estimating..." pre-message (hint comes through
            # bridge.estimation); condition matches core's own skip rule
            if self.end_value - self.start_value + 1 > SAMPLE_SEEDS_HIGH:
                est_text = lang_manager.get("estimate_sampling").format(f"{SAMPLE_SEEDS_HIGH:,}")
                print(f"[HIGH32 INFO] {est_text}")
                self.biome_info_updated.emit("\n" + est_text + "\n")

            self._bridge = WorkerBridge(self)
            results, elapsed = core_high32.run_high32(
                {}, biome_samples, self.low32_value, self.mc_version_str,
                self.start_value, self.end_value,
                lcg_structures=self.lcg_structures,
                requested_processes=self.user_process_count,
                reporter=self._bridge, control=self.control)
            self.results = results

            if not self.stop_event.is_set():
                print(f"[HIGH32 COMPLETE] Finished! Found {len(results)} seeds")
                self.finished.emit(results)
            else:
                print(f"[HIGH32 STOPPED] Worker stopped by user")
        except ValueError as e:
            # Phase 2 found no candidates: show the old localized message
            if self._bridge is not None and self._bridge.phase2_empty:
                msg = lang_manager.get("lcg_phase2_no_candidates")
                print(f"[HIGH32 ERROR] {msg}")
                self.error_occurred.emit(msg)
            else:
                traceback.print_exc()
                self.error_occurred.emit(str(e))
        except Exception as e:
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
        self.pause_event.set()

    def resume(self):
        self.pause_event.clear()

    def stop(self):
        self.stop_event.set()
        # Force save progress before stopping
        if self._bridge is not None:
            print(f"[HIGH32 STOP] Saved progress before stopping: {self._bridge.last_current:,}")
            self.save_progress(self._bridge.last_current)
