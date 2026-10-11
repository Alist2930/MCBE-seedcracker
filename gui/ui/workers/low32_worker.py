# -*- coding: utf-8 -*-
"""Low 32-bit cracking worker (GUI frontend, thin shell over core.low32).

The QThread shell and all signals are kept identical to the old self-contained
worker; all cracking logic (structure prep, strictness testing, candidate
estimation, CPU/GPU scans) lives in core.low32 and is driven through a
Reporter bridge + Control events. Reporter/Control never cross the
multiprocessing boundary - only plain task tuples do (spawn-safe).
"""
import json
import os
import sys
import threading
import time
import traceback

from PyQt5.QtCore import QThread, pyqtSignal

# Make the repo root importable (needed for `core.*`; spawn workers inherit it)
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[3]))

from ui.utils.config_manager import get_base_path
from ui.utils.language_manager import lang_manager
from core import low32 as core_low32
from core.reporter import Reporter, Control


def load_config():
    """Load crack_config.json (GUI-specific flat config, same as before)."""
    config_path = os.path.join(get_base_path(), "crack_config.json")
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
                if not isinstance(config, dict):
                    raise ValueError("crack_config.json must contain a JSON object")
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"[WARNING] Failed to load config file: {e}")
            print(f"[WARNING] Using default configuration")
        except Exception as e:
            print(f"[WARNING] Unexpected error loading config: {e}")
            print(f"[WARNING] Using default configuration")

    return default_config


class WorkerBridge(Reporter):
    """Forwards core events to the worker's Qt signals (parent process only)."""

    def __init__(self, worker):
        self.worker = worker
        self.last_current = worker.start_value
        self.last_save_time = time.time()

    def info(self, text):
        print(f"[INFO] {text}")

    def warn(self, text):
        print(f"[WARNING] {text}")

    def error(self, text):
        print(f"[ERROR] {text}")

    def progress(self, current, total, speed, eta, found=None, note=None):
        worker = self.worker
        absolute = worker.start_value + current
        self.last_current = absolute
        total_range = worker.end_value - worker.original_start_value + 1
        progress = (absolute - worker.original_start_value) / total_range * 100
        # Clamp progress to valid range [0, 100]
        progress = max(0, min(100, progress))
        print(f"[PROGRESS] {progress:.2f}% | Current: {absolute:,} | Speed: {int(speed):,}/s | ETA: {int(eta)}s")
        worker.progress_updated.emit(progress, int(speed), int(eta))
        # Throttled session save (60s), same cadence as the old worker loops
        now = time.time()
        if now - self.last_save_time >= 60:
            print(f"[SAVE] Saving progress at {absolute:,}")
            worker.save_progress(absolute)
            self.last_save_time = now

    def result(self, seed):
        self.worker.found_seed.emit(seed)

    def device_info(self, info):
        if info.get('use_gpu'):
            device_str = f"GPU ({info.get('gpu')})"
        else:
            device_str = f"CPU ({info.get('cores')} cores)"
        print(f"[INFO] Compute device: {device_str}")
        self.worker.compute_device_info.emit(device_str)

    def structure_info(self, regular, special):
        # Simplified JSON for the UI: "(x, z) -> structure name (spread_type)",
        # localized names; special samples carry the "decoration" marker
        zh = (lang_manager.language == "zh_CN")
        order_info = []
        for d in regular:
            name = d.get("name_zh", d["name"]) if zh else d["name"]
            order_info.append({"x": d["x"], "z": d["z"], "name": name,
                               "spread_type": d["spread_type"]})
        for d in special:
            name = d.get("name_zh", d["name"]) if zh else d["name"]
            order_info.append({"x": d["x"], "z": d["z"], "name": name,
                               "spread_type": "decoration"})
        self.worker.structure_info_updated.emit(json.dumps(order_info))

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
        print(f"[INFO] {hint}")
        self.worker.estimate_hint_updated.emit(hint + "\n")


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
        self.results = []

        if test_mode:
            self.end_value = min(end, 100000000)

        self.progress_file = os.path.join(get_base_path(), "progress_low32.json")

        # Pause/stop honored inside core via Control (GPU checks stop only)
        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.control = Control(stop_event=self.stop_event, pause_event=self.pause_event)
        self._bridge = None

    def run(self):
        try:
            config = load_config()

            # GUI structures use {"type": ...}; core expects {"structure": ...}
            targets = [{"structure": s["type"], "x": s["x"], "z": s["z"]}
                       for s in self.structures]

            # Localized "estimating..." pre-message (the four-tier hint comes
            # later through bridge.estimation); condition matches core's own
            # skip rule so the hint is never left hanging
            if self.end_value - self.start_value + 1 > core_low32.SAMPLE_SEEDS:
                est_text = lang_manager.get("estimate_sampling").format(f"{core_low32.SAMPLE_SEEDS:,}")
                print(f"[INFO] {est_text}")
                self.estimate_hint_updated.emit("\n" + est_text + "\n")

            self._bridge = WorkerBridge(self)
            results, elapsed = core_low32.run_low32(
                config, targets, self.start_value, self.end_value,
                force_cpu=(self.force_gpu is False),
                force_gpu=(self.force_gpu is True),
                requested_processes=self.user_process_count,
                reporter=self._bridge, control=self.control)
            self.results = results

            if not self.stop_event.is_set():
                print(f"[COMPLETE] Finished! Found {len(results)} seeds")
                self.finished.emit(results)
            else:
                print(f"[STOPPED] Worker stopped by user")
        except Exception as e:
            traceback.print_exc()
            self.error_occurred.emit(str(e))

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
        self.pause_event.set()

    def resume(self):
        self.pause_event.clear()

    def stop(self):
        self.stop_event.set()
        if self._bridge is not None:
            print(f"[LOW32 STOP] Saved progress before stopping: {self._bridge.last_current:,}")
            self.save_progress(self._bridge.last_current)
