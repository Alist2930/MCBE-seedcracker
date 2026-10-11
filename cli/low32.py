# -*- coding: utf-8 -*-
"""Minecraft Bedrock Low 32-bit Seed Cracker (CLI frontend).

Thin console shell over core.low32: argparse + English console rendering.
All cracking logic lives in core/; this file only formats output and handles
the found_seeds_low32.txt log.
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Make the repo root importable (needed for `core.*` and spawn workers)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import config_loader
from core.low32 import run_low32
from core.reporter import Reporter, Control

SCRIPT_DIR = Path(__file__).resolve().parent


class ConsoleReporter(Reporter):
    """Renders core events as English console lines and writes found_seeds_low32.txt."""

    def __init__(self, found_seeds_file=None):
        self.found_seeds_file = found_seeds_file

    def info(self, text):
        print(f"[*] {text}")

    def detail(self, text):
        print(text)

    def warn(self, text):
        print(f"[!] {text}")

    def error(self, text):
        print(f"[!] {text}")

    def progress(self, current, total, speed, eta):
        eta_str = f"{eta/3600:.1f}h" if eta > 3600 else f"{eta/60:.1f}min" if eta > 60 else f"{eta:.0f}s"
        print(f"[-] {current:,}/{total:,} ({current/total*100:5.1f}%) | Speed: {speed:,.0f}/s | ETA: {eta_str}")

    def result(self, seed):
        seed_info = f">>> [!] Found seed: {seed} (0x{seed:08X})"
        print(seed_info)
        if self.found_seeds_file:
            with open(self.found_seeds_file, 'a', encoding='utf-8') as f:
                f.write(seed_info + '\n')
                f.write(f"Found at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 60 + '\n')

    def device_info(self, info):
        device = f"GPU ({info['gpu']})" if info['use_gpu'] else f"CPU ({info['cores']} cores)"
        print(f"[*] Compute device: {device}")

    def structure_info(self, regular, special):
        print(f"[*] Target structures ({len(regular)}) [sorted: linear first]:")
        for i, info in enumerate(regular):
            mode_str = "4-chunk grid" if info.get("grid") else "exact chunk"
            print(f"    {i+1}. {info['name']} ({info['x']}, {info['z']}) [{info['spread_type']}, {mode_str}]")
        if special:
            print(f"[*] Special decoration samples ({len(special)}) [sorted: strictest first]:")
            for i, info in enumerate(special):
                sp_desc = "desert well (exact anchor)" if info["sp_type"] == 0 else "amethyst geode (1.18+)"
                print(f"    {i+1}. {info['name']} ({info['x']}, {info['z']}) [{sp_desc}]")

    def estimation(self, est):
        predicted, sampled = est['predicted'], est['sampled']
        if est['saturated']:
            print("[!] Estimated candidates: far more than 10,000 (sampling buffer saturated)")
            print("[!] Too few structures - many false positives are expected!")
        elif predicted <= 0:
            if est['has_zero_sample']:
                print("[!] Estimated candidates: ~0 - some sample(s) matched 0 test seeds (possibly invalid), "
                      "no results expected - check sample coordinates/type!")
            else:
                print(f"[*] Estimated candidates: ~0 (sampled {sampled:,} seeds)")
                print("[*] Samples are fine - expect only 0-1 candidates over the full range")
        elif predicted > 10000:
            print(f"[!] Estimated candidates: ~{predicted:,} (sampled {sampled:,} seeds)")
            print("[!] Too few structures - many false positives are expected!")
        else:
            print(f"[*] Estimated candidates: ~{predicted:,} (sampled {sampled:,} seeds)")


def init_found_seeds_file(search_start, search_end):
    """Create/clear found_seeds_low32.txt and return its path."""
    found_seeds_file = SCRIPT_DIR / "found_seeds_low32.txt"
    start_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(found_seeds_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("Minecraft Bedrock Low 32-bit Seed Cracker - Found Seeds\n")
        f.write("=" * 60 + "\n")
        f.write(f"Start Time: {start_time_str}\n")
        f.write(f"Search Range: {search_start:,} ~ {search_end:,}\n")
        f.write("=" * 60 + "\n\n")
    return found_seeds_file


def main():
    parser = argparse.ArgumentParser(description="Minecraft Bedrock Low 32-bit Seed Cracker (CLI)")
    parser.add_argument("--start", type=int, default=None, help="Start low32 value (inclusive), overrides config")
    parser.add_argument("--end", type=int, default=None, help="End low32 value (inclusive), overrides config")
    parser.add_argument("--test", action="store_true", help="Test mode (100M seeds), overrides config")
    parser.add_argument("--cpu", action="store_true", help="Force CPU mode")
    parser.add_argument("--gpu", action="store_true", help="Force GPU mode")
    parser.add_argument("--processes", type=int, default=None, help="Number of CPU processes (only for CPU mode)")
    args = parser.parse_args()

    # Load configuration
    try:
        cfg = config_loader.get_low32_config(config_dir=SCRIPT_DIR)
    except config_loader.ConfigError as e:
        print(f"\n[!] {e}")
        sys.exit(1)

    # Override config with command-line arguments
    if args.test:
        test_mode = True
        search_start = 0
        search_end = 100000000
    else:
        test_mode = cfg.get('test_mode', False)
        search_start = args.start if args.start is not None else cfg.get('start', 0)
        search_end = args.end if args.end is not None else cfg.get('end', 0xFFFFFFFF)

    print("=" * 60)
    print("Minecraft Bedrock Low 32-bit Seed Cracker (CLI)")
    print("=" * 60)

    # Create/Clear found seeds file
    found_seeds_file = init_found_seeds_file(search_start, search_end)
    print(f"[*] Found seeds will be saved to: {found_seeds_file}")

    total_seeds = search_end - search_start + 1
    print(f"\n[*] Mode: {'Test' if test_mode else 'Full'}")
    print(f"[*] Search range: {search_start:,} ~ {search_end:,} ({total_seeds:,} seeds)")

    reporter = ConsoleReporter(found_seeds_file)
    try:
        all_results, elapsed = run_low32(cfg, cfg.get('targets', []), search_start, search_end,
                                         force_cpu=args.cpu, force_gpu=args.gpu,
                                         requested_processes=args.processes,
                                         reporter=reporter, control=Control())
    except (ValueError, RuntimeError) as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)

    print(f"\n[*] Done! Time: {elapsed:.1f}s ({elapsed/60:.1f}min)")
    print(f"[*] Speed: {total_seeds/elapsed:,.0f} seeds/s")
    print(f"[*] Found {len(all_results)} matching seeds")
    print(f"[*] Results saved to: {found_seeds_file}")

    for seed in all_results:
        print(f"    Low 32-bit: {seed} (0x{seed:08X})")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Children ignore SIGINT (_worker_init); the pool was already
        # terminated in run_cpu's finally block
        print("\n[!] Interrupted by user")
