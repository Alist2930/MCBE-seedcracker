# -*- coding: utf-8 -*-
"""Reporter and Control protocols shared by all frontends (CLI / GUI / web).

Core cracking functions never print and never touch Qt: they emit events
through a Reporter and honor pause/stop through a Control. Frontends provide
their own implementations:
- CLI: ConsoleReporter prints English text and writes found_seeds.txt
- GUI: a bridge object forwards events to Qt signals
- Reporter/Control instances never cross the multiprocessing boundary; only
  the parent process calls them while aggregating worker results.
"""
import time


class Reporter:
    """Event sink for core cracking functions. Default implementation is a no-op."""

    def info(self, text):
        """Plain status line (console chatter, English)."""

    def detail(self, text):
        """Indented listing line printed verbatim (no prefix) by the console."""

    def warn(self, text):
        """Warning line."""

    def error(self, text):
        """Error line."""

    def progress(self, current, total, speed, eta, found=None, note=None):
        """Scan progress: current/total seeds scanned, speed seeds/s, eta seconds,
        optional found count and optional note text (e.g. 'Candidate 2/5')."""

    def result(self, seed):
        """A matching seed was found."""

    def device_info(self, info):
        """Compute device decision: {'use_gpu': bool, 'gpu': str|None, 'cores': int|None}."""

    def structure_info(self, regular, special):
        """Prepared target listing: regular/special are lists of info dicts."""

    def sample_info(self, samples, scores):
        """Prepared biome sample listing (high32): samples is the sorted
        [(x, z, y, biome_id), ...] list, scores the matching strictness scores
        (empty when the strictness test was skipped)."""

    def estimation(self, est):
        """Candidate-count estimate (level computed in core):
        {'predicted': int, 'sampled': int, 'saturated': bool, 'has_zero_sample': bool}."""

    def warning(self, warning):
        """Structured warning dict (version compatibility, invalid samples, ...)."""


class Control:
    """Pause/stop signals for long-running scans. Default: never pause, never stop."""

    def __init__(self, stop_event=None, pause_event=None):
        self.stop_event = stop_event
        self.pause_event = pause_event

    def should_stop(self):
        return self.stop_event is not None and self.stop_event.is_set()

    def wait_if_paused(self):
        # Spin-wait while paused; keep it responsive so stop() is honored
        while self.pause_event is not None and self.pause_event.is_set():
            if self.should_stop():
                return
            time.sleep(0.1)
