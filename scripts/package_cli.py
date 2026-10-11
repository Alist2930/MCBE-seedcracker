#!/usr/bin/env python3
"""Package the cross-platform CLI release into a distributable zip.

The CLI release contains only the shared core and the thin CLI frontends
(no GUI code, no READMEs, no assets), plus the tracked cli/config.json
template. Runtime artifacts (__pycache__, found-seeds logs, session data,
progress files) are excluded.

Usage:
    python scripts/package_cli.py                 # dist/MCBEseedcracker_cli_v<version>.zip
    python scripts/package_cli.py --out <dir>     # custom output directory
"""

import argparse
import re
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VERSION_INFO = PROJECT_ROOT / 'gui' / 'version_info.txt'

# Top-level folder name inside the zip
ARCHIVE_ROOT = 'MCBEseedcracker'

# Directories never packed (any depth, matched on the directory name)
EXCLUDED_DIRS = {'__pycache__', 'build', 'dist', '.git', 'sounds'}
# File names never packed (any depth)
EXCLUDED_FILES = {
    'session_data.json',
    'crack_config.json',
}
# File patterns never packed (any depth)
EXCLUDED_PATTERNS = ['*.py[cod]', 'progress_*.json', 'README*.md', 'found_seeds*.txt']

# Contents packed from the repository root
INCLUDE_DIRS = ['cli', 'core']

# Files that must exist in the archive for a valid CLI release
REQUIRED_IN_ARCHIVE = [
    'cli/config.json',       # generated default configuration
    'cli/low32.py',
    'cli/high32.py',
    'core/low32.py',
    'core/high32.py',
    'core/reporter.py',
    'core/config_loader.py',
    'core/check_cpu.py',
    'core/data/structures.json',
    'core/data/biomes.json',
    'core/native/crack_low32.cl',
    'core/native_src/crack_low32.c',
    'core/native_src/crack_high32.c',
    'core/build.sh',
    'core/build.bat',
]

# Native library name fragments expected per platform (warn when missing)
PLATFORM_LIB_HINTS = {
    'Windows': 'win_x86_64',
    'Linux': 'linux_x86_64',
    'macOS': 'macos_arm64',
}


def read_version():
    """Extract the product version from gui/version_info.txt (fallback: none)."""
    try:
        text = VERSION_INFO.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return None
    m = re.search(r'filevers=\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)', text)
    if m:
        return '.'.join(m.groups())
    return None


def is_excluded(path, base):
    """Return True when path (relative to base) must not be packed."""
    rel = path.relative_to(base)
    if any(part in EXCLUDED_DIRS for part in rel.parts[:-1]):
        return True
    if path.name in EXCLUDED_FILES:
        return True
    for pat in EXCLUDED_PATTERNS:
        if path.match(pat):
            return True
    return False


def collect_files():
    """Yield (source_path, archive_path) pairs for every file to pack."""
    for name in INCLUDE_DIRS:
        src_dir = PROJECT_ROOT / name
        if not src_dir.is_dir():
            raise SystemExit(f'[ERROR] required directory missing: {src_dir}')
        for path in sorted(src_dir.rglob('*')):
            if path.is_file() and not is_excluded(path, PROJECT_ROOT):
                yield path, f'{ARCHIVE_ROOT}/{name}/{path.relative_to(src_dir).as_posix()}'


def main():
    parser = argparse.ArgumentParser(description='Package the CLI release zip')
    parser.add_argument('--out', default=str(PROJECT_ROOT / 'dist'),
                        help='output directory (default: dist/)')
    args = parser.parse_args()

    version = read_version()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_name = 'MCBEseedcracker_cli' + (f'_v{version}' if version else '') + '.zip'
    zip_path = out_dir / zip_name

    pairs = list(collect_files())
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for src, arcname in pairs:
            zf.write(src, arcname)

    # Post-write verification
    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        missing = [f'{ARCHIVE_ROOT}/{rel}' for rel in REQUIRED_IN_ARCHIVE
                   if f'{ARCHIVE_ROOT}/{rel}' not in names]
        if missing:
            print('[ERROR] archive is incomplete, missing:')
            for rel in missing:
                print(f'  - {rel}')
            sys.exit(1)

        native_prefix = f'{ARCHIVE_ROOT}/core/native/'
        native_names = [n for n in names if n.startswith(native_prefix)]
        for platform, hint in PLATFORM_LIB_HINTS.items():
            if not any(hint in n for n in native_names):
                print(f'[WARNING] no {platform} native library in core/native/ '
                      f'(expected a *{hint}* prebuilt library)')

        total = sum(zi.file_size for zi in zf.infolist())
        print(f'[OK] {zip_path}')
        print(f'     {len(names)} files, {total / 1024 / 1024:.1f} MiB '
              f'(uncompressed), archive {zip_path.stat().st_size / 1024 / 1024:.1f} MiB')


if __name__ == '__main__':
    main()
