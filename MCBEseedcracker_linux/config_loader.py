# -*- coding: utf-8 -*-
"""
Configuration Loader for MCBEseedcracker Linux

Reads configuration from config.json file.
If config.json doesn't exist, creates default configuration.
"""
import copy
import json
import sys
from pathlib import Path

MC_1_18 = 22
MC_1_19 = 24
MC_1_20 = 25
MC_1_21_3 = 27  # Java 1.21-1.21.3
MC_1_21_WD = 28  # Java 1.21.4 (Winter Drop, Bedrock 1.21.50)
MC_1_21_5 = 29  # Java 1.21.5-26.1 (Pale Garden expanded range, Bedrock 1.21.60-26.23)
MC_26_2 = 38  # Java 26.2 (Chaos Cubed Drop, Bedrock 26.30+)

# Bedrock version to cubiomes version constant (based on ChunkBase)
CUBIOMES_VERSION_MAP = {
    '26.30+': MC_26_2,  # Java 26.2 (Sulfur Caves)
    '1.21.60-26.23': MC_1_21_5,  # Java 1.21.5-26.1 (Pale Garden expanded range)
    '1.21.50': MC_1_21_WD,  # Java 1.21.4 (Pale Garden supported)
    '1.21-1.21.40': MC_1_21_3,  # Does not support Pale Garden
    '1.20.60-81': MC_1_20,
    '1.20.0-51': MC_1_20,
    '1.19': MC_1_19,
    '1.18': MC_1_18,
}
LATEST_VERSION = '26.30+'

DEFAULT_TARGETS = [
    {"structure": "swamp_hut", "x": 2136, "z": -1176},
    {"structure": "jungle_temple", "x": -360, "z": -248},
    {"structure": "desert_temple", "x": -936, "z": 4744},
    {"structure": "ocean_monument", "x": 792, "z": -792},
    {"structure": "end_city", "x": 1352, "z": -1208},
]

DEFAULT_SAMPLES = [
    {"x": -270, "z": 470, "y": 200, "biome_id": 186, "name": "pale_garden"},
    {"x": -1922, "z": 1231, "y": 200, "biome_id": 185, "name": "cherry_grove"},
    {"x": -4706, "z": 3302, "y": 200, "biome_id": 132, "name": "flower_forest"},
    {"x": -935, "z": 2592, "y": 200, "biome_id": 5, "name": "taiga"},
    {"x": -2697, "z": 1363, "y": 200, "biome_id": 4, "name": "forest"},
]

DEFAULT_LOW32_CONFIG = {
    'test_mode': False,
    'start': 0,
    'end': 4294967296,  # 2^32
    'use_gpu': True,
    'auto_fallback': True,
    'seeds_per_thread': 256,
    'max_results': 10000,
    'targets': DEFAULT_TARGETS,
}

DEFAULT_HIGH32_CONFIG = {
    'test_mode': False,
    'start': 0,
    'end': 100000000,  # 100M
    'low32': 1818588773,
    'mc_version': LATEST_VERSION,
    'samples': DEFAULT_SAMPLES,
}

def load_config():
    """Load configuration from config.json
    
    Raises:
        SystemExit: If config.json has syntax errors
    """
    config_dir = Path(__file__).parent
    config_file = config_dir / 'config.json'
    
    # Load config file
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"\n{'=' * 60}")
            print(f"[ERROR] config.json has syntax errors!")
            print(f"{'=' * 60}")
            print(f"File: {config_file}")
            print(f"Error: {e}")
            print(f"\nPlease fix the JSON syntax error and try again.")
            print(f"Common issues:")
            print(f"  - Missing comma between items")
            print(f"  - Missing closing bracket ] or }}")
            print(f"  - Unquoted strings")
            print(f"{'=' * 60}")
            sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] Failed to load config.json: {e}")
            sys.exit(1)
    
    # If config.json doesn't exist, create it with default values
    print(f"\n[INFO] config.json not found, creating default configuration...")
    default_config = copy.deepcopy({
        "low32": DEFAULT_LOW32_CONFIG,
        "high32": DEFAULT_HIGH32_CONFIG,
    })
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"[INFO] Created: {config_file}")
    print(f"[INFO] Please edit config.json to configure your search parameters.\n")
    
    return default_config

def get_section_config(section, default):
    """Get a config section, filling in any missing key from the defaults"""
    config = load_config()
    default = copy.deepcopy(default)

    if config and section in config:
        for key, value in default.items():
            if key not in config[section]:
                config[section][key] = value
        return config[section]

    return default

def get_low32_config():
    """Get low32-bit cracker configuration

    Returns:
        dict with keys: test_mode, start, end, use_gpu, auto_fallback, seeds_per_thread, max_results, targets
    """
    return get_section_config('low32', DEFAULT_LOW32_CONFIG)

def get_high32_config():
    """Get high32-bit cracker configuration"""
    return get_section_config('high32', DEFAULT_HIGH32_CONFIG)

def mc_version_to_cubiomes(mc_version):
    """Convert MC version string to cubiomes version constant
    
    Supported versions:
    - "26.30+" (Sulfur Caves, latest)
    - "1.21.60-26.23" (Pale Garden expanded range)
    - "1.21.50" (Pale Garden supported)
    - "1.21-1.21.40" (No Pale Garden)
    - "1.20.60-81" (Cherry Grove)
    - "1.20.0-51" (Cherry Grove)
    - "1.19" (Deep Dark, Mangrove Swamp)
    - "1.18" (Lush Caves, Dripstone Caves)
    
    Args:
        mc_version: String like '1.21.60', '1.21.50', '1.21-1.21.40', '26.30+', etc.
    
    Returns:
        Integer version constant for cubiomes
    """
    # Check if exact version is in map
    if mc_version in CUBIOMES_VERSION_MAP:
        return CUBIOMES_VERSION_MAP[mc_version]
    
    # Try partial match (e.g., '1.21.60' should match '1.21.60-26.23')
    parts = mc_version.split('.')
    if len(parts) >= 2:
        major_minor = f"{parts[0]}.{parts[1]}"
        # Try to find closest match
        for ver_key in CUBIOMES_VERSION_MAP:
            if ver_key.startswith(major_minor):
                return CUBIOMES_VERSION_MAP[ver_key]
    
    # Default to latest version
    print(f"[WARNING] Unknown MC version '{mc_version}', using latest ({LATEST_VERSION})")
    return CUBIOMES_VERSION_MAP[LATEST_VERSION]