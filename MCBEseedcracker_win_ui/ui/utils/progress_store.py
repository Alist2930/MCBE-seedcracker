# -*- coding: utf-8 -*-
"""
Progress store - persistence of crack progress and progress percentage math
"""
import json
import os

from .paths import get_progress_path


def compute_progress(current, original_start, end):
    """Progress percentage of `current` within [original_start, end], clamped to 0-100"""
    total_range = end - original_start + 1
    if total_range <= 0:
        return 100.0
    progress = (current - original_start) / total_range * 100
    return max(0.0, min(100.0, progress))


def save_progress(mode, progress_data, log_prefix="SAVE"):
    """Write progress data for a crack mode ("low32" / "high32")"""
    progress_file = get_progress_path(mode)
    try:
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2)
        print(f"[{log_prefix} SUCCESS] Progress saved to {progress_file}")
    except Exception as e:
        print(f"[{log_prefix} ERROR] Failed to save progress: {e}")


def load_progress(mode):
    """Read progress data for a crack mode, or None when absent/unreadable"""
    progress_file = get_progress_path(mode)
    if not os.path.exists(progress_file):
        return None
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load {mode} progress: {e}")
        return None


def clear_progress(mode):
    """Remove the progress file of a crack mode"""
    progress_file = get_progress_path(mode)
    if os.path.exists(progress_file):
        os.remove(progress_file)
