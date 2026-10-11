# -*- coding: utf-8 -*-
"""Minecraft Bedrock High 32-bit Seed Cracker (CLI frontend).

Thin console shell over core.high32: argparse + English console rendering
(in-place progress bar). All cracking logic lives in core/.
"""
import sys
import functools
import argparse
from pathlib import Path
from datetime import datetime

# Make the repo root importable (needed for `core.*` and spawn workers)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import config_loader
from core.high32 import run_high32, format_seed_output, load_java_lcg_structures
from core.reporter import Reporter, Control

SCRIPT_DIR = Path(__file__).resolve().parent

_print = functools.partial(print, flush=True)  # Always flush print output


def _pause():
    """Keep the console open when launched by double-click (no-op on EOF)."""
    try:
        input("\nPress Enter to exit...")
    except (EOFError, OSError):
        pass


class ConsoleReporter(Reporter):
    """Renders core events as English console lines and writes found_seeds.txt."""

    def __init__(self, found_seeds_file=None):
        self.found_seeds_file = found_seeds_file

    def info(self, text):
        _print(f"[*] {text}")

    def detail(self, text):
        _print(text)

    def warn(self, text):
        _print(f"[!] {text}")

    def error(self, text):
        _print(f"[!] {text}")

    def progress(self, current, total, speed, eta, found=None, note=None):
        # In-place progress bar with speed and ETA (same style as before)
        total = max(total, 1)
        percent = current / total * 100
        bar_len = 30
        filled = int(bar_len * percent / 100)
        bar = '#' * filled + '-' * (bar_len - filled)
        found_str = f" | Found: {found}" if found is not None else ""
        _print(f"\r  [{bar}] {percent:.1f}% | {current:,}/{total:,} | {speed:,.0f}/s | ETA: {eta/60:.1f}min{found_str}", end='')
        if note:
            _print(f" | {note}", end='')
        _print('', end='', flush=True)

    def _clear_line(self):
        sys.stdout.write('\r\033[K')  # Clear entire line
        sys.stdout.flush()

    def result(self, seed):
        seed_info = format_seed_output(seed, self.low32)
        self._clear_line()
        _print(seed_info)
        if self.found_seeds_file:
            with open(self.found_seeds_file, 'a', encoding='utf-8') as f:
                f.write(seed_info + '\n')
                f.write(f"Found at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 60 + '\n')

    def estimation(self, est):
        predicted, sampled = est['predicted'], est['sampled']
        if est['saturated']:
            _print("[!] Estimated candidates: far more than 10,000 (sampling buffer saturated)")
            _print("[!] Too few biome samples - many false positives are expected!")
        elif predicted <= 0:
            if est['has_zero_sample']:
                _print("[!] Estimated candidates: ~0 - some sample(s) matched 0/100000 (possibly invalid), "
                       "no results expected - check sample coordinates/type!")
            else:
                _print(f"[*] Estimated candidates: ~0 (sampled {sampled:,} high32 values)")
                _print("[*] Samples are fine - expect only 0-1 candidates over the full range")
        elif predicted > 10000:
            _print(f"[!] Estimated candidates: ~{predicted:,} (sampled {sampled:,} high32 values)")
            _print("[!] Too few biome samples - many false positives are expected!")
        else:
            _print(f"[*] Estimated candidates: ~{predicted:,} (sampled {sampled:,} high32 values)")

    low32 = 0  # set by main() for seed display


def init_found_seeds_file():
    """Create/clear found_seeds.txt and return its path."""
    found_seeds_file = SCRIPT_DIR / "found_seeds.txt"
    start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(found_seeds_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("Minecraft Bedrock High 32-bit Seed Cracker - Found Seeds\n")
        f.write("=" * 60 + "\n")
        f.write(f"Start Time: {start_time_str}\n")
        f.write("=" * 60 + "\n\n")
    return found_seeds_file


def parse_lcg_structures(args, cfg):
    """Parse Java LCG structures: CLI args override config.json."""
    java_lcg_configs = load_java_lcg_structures()
    lcg_structures = []
    if args.lcg_structure:
        for s in args.lcg_structure:
            parts = s.split(':')
            if len(parts) == 3:
                name = parts[0]
                try:
                    x, z = int(parts[1]), int(parts[2])
                except ValueError:
                    _print(f"[!] Invalid coordinates in: {s}, skipping")
                    continue
                if name in java_lcg_configs:
                    lcg_structures.append({"type": name, "x": x, "z": z})
                else:
                    valid = ", ".join(sorted(java_lcg_configs.keys()))
                    _print(f"[!] Unknown Java LCG structure '{name}'. Valid: {valid}")
            else:
                _print(f"[!] Invalid format (expected name:x:z): {s}")
    else:
        cfg_lcg = cfg.get('lcg_structures', [])
        for s in cfg_lcg:
            stype = s.get('type')
            if stype in java_lcg_configs:
                lcg_structures.append({"type": stype, "x": s['x'], "z": s['z']})
            else:
                valid = ", ".join(sorted(java_lcg_configs.keys()))
                _print(f"[!] Unknown Java LCG structure '{stype}' in config.json. Valid: {valid}")
    return lcg_structures


def main():
    parser = argparse.ArgumentParser(description='Minecraft Bedrock High 32-bit Seed Cracker')
    parser.add_argument('--start', type=int, default=None, help='Start high value (inclusive), overrides config')
    parser.add_argument('--end', type=int, default=None, help='End high value (inclusive), overrides config')
    parser.add_argument('--test', action='store_true', help='Test mode: 0 ~ 100M, overrides config')
    parser.add_argument('--low32', type=int, default=None, help='Low 32-bit value, overrides config')
    parser.add_argument('--processes', type=int, default=None, help='Number of processes')
    parser.add_argument('--lcg-structure', action='append', default=None,
                        help='Java LCG structure (format: name:x:z, e.g., trail_ruins:3069:2883). Repeatable. Enables phase 2 (32-47 bit) + phase 3 (48-63 bit) flow.')
    args = parser.parse_args()

    # Load configuration
    try:
        cfg = config_loader.get_high32_config(config_dir=SCRIPT_DIR)
    except config_loader.ConfigError as e:
        _print(f"\n[!] {e}")
        sys.exit(1)

    # Parse Java LCG structures: CLI args override config.json
    lcg_structures = parse_lcg_structures(args, cfg)

    # Override config with command-line arguments
    if args.test:
        test_mode = True
        search_start = 0
        search_end = 100000000
    else:
        test_mode = cfg.get('test_mode', False)
        search_start = args.start if args.start is not None else cfg.get('start', 0)
        search_end = args.end if args.end is not None else cfg.get('end', 0xFFFFFFFF)

    low32 = args.low32 if args.low32 is not None else cfg.get('low32', 1818588773)
    mc_version_str = cfg.get('mc_version', '26.50')
    samples = [(s['x'], s['z'], s['y'], s['biome_id']) for s in cfg.get('samples', [])]

    _print("=" * 60)
    _print("Minecraft Bedrock High 32-bit Seed Cracker")
    _print("=" * 60)

    # Create/Clear found seeds file
    found_seeds_file = init_found_seeds_file()

    reporter = ConsoleReporter(found_seeds_file)
    reporter.low32 = low32

    try:
        all_results, elapsed = run_high32(cfg, samples, low32, mc_version_str, search_start, search_end,
                                          lcg_structures=lcg_structures,
                                          requested_processes=args.processes,
                                          reporter=reporter, control=Control())
    except (ValueError, RuntimeError) as e:
        _print(f"\n[!] ERROR: {e}")
        _pause()
        sys.exit(1)

    _print('\r\033[K', end='')  # Clear the progress line
    _print(f"\n[Complete]")
    _print(f"  Time: {elapsed:.1f}s ({elapsed/60:.1f}min)")
    _print(f"  Found: {len(all_results)} seed(s)")

    if all_results:
        _print("\n" + "=" * 60)
        _print("All found seeds:")
        _print("=" * 60)
        for seed in all_results:
            _print(format_seed_output(seed, low32))

    _print("\n" + "=" * 60)
    _print("Search Complete!")
    _print("=" * 60)
    _print(f"[*] Found seeds saved to: {found_seeds_file}")

    _pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Children ignore SIGINT (_worker_init); the pool was already
        # terminated in the core run functions' finally blocks
        _print("\n[!] Interrupted by user")
