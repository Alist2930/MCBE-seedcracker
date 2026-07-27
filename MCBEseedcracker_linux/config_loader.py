# -*- coding: utf-8 -*-
"""
Configuration Loader for MCBEseedcracker Linux

Reads configuration from config.json file.
If config.json doesn't exist, creates default configuration.
"""
import json
import sys
import shutil
from pathlib import Path

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
    default_config = {
        "low32": {
            "test_mode": False,
            "start": 0,
            "end": 4294967296,
            "use_gpu": True,
            "targets": [
                {"structure": "swamp_hut", "x": 2136, "z": -1176},
                {"structure": "jungle_temple", "x": -360, "z": -248},
                {"structure": "desert_temple", "x": -936, "z": 4744},
                {"structure": "ocean_monument", "x": 792, "z": -792},
                {"structure": "end_city", "x": 1352, "z": -1208}
            ]
        },
        "high32": {
            "test_mode": False,
            "start": 0,
            "end": 100000000,
            "low32": 1818588773,
            "mc_version": "26.30+",
            "samples": [
                {"x": -270, "z": 470, "y": 200, "biome_id": 186, "name": "pale_garden"},
                {"x": -1922, "z": 1231, "y": 200, "biome_id": 185, "name": "cherry_grove"},
                {"x": -4706, "z": 3302, "y": 200, "biome_id": 132, "name": "flower_forest"},
                {"x": -935, "z": 2592, "y": 200, "biome_id": 5, "name": "taiga"},
                {"x": -2697, "z": 1363, "y": 200, "biome_id": 4, "name": "forest"}
            ]
        }
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2)
    
    print(f"[INFO] Created: {config_file}")
    print(f"[INFO] Please edit config.json to configure your search parameters.\n")
    
    return default_config

def get_low32_config():
    """Get low32-bit cracker configuration

    Returns:
        dict with keys: test_mode, start, end, use_gpu, auto_fallback, seeds_per_thread, max_results, targets
    """
    config = load_config()

    default = {
        'test_mode': False,
        'start': 0,
        'end': 4294967296,  # 2^32
        'use_gpu': True,
        'auto_fallback': True,
        'seeds_per_thread': 256,
        'max_results': 10000,
        'targets': [
            {"structure": "swamp_hut", "x": 2136, "z": -1176},
            {"structure": "jungle_temple", "x": -360, "z": -248},
            {"structure": "desert_temple", "x": -936, "z": 4744},
            {"structure": "ocean_monument", "x": 792, "z": -792},
            {"structure": "end_city", "x": 1352, "z": -1208},
        ]
    }

    if config and 'low32' in config:
        # Merge with defaults
        for key, value in default.items():
            if key not in config['low32']:
                config['low32'][key] = value
        return config['low32']

    return default

def get_high32_config():
    """Get high32-bit cracker configuration"""
    config = load_config()
    
    default = {
        'test_mode': False,
        'start': 0,
        'end': 100000000,  # 100M
        'low32': 1818588773,
        'mc_version': '1.21.60',
        'samples': [
            {"x": -270, "z": 470, "y": 200, "biome_id": 186, "name": "pale_garden"},
            {"x": -1922, "z": 1231, "y": 200, "biome_id": 185, "name": "cherry_grove"},
            {"x": -4706, "z": 3302, "y": 200, "biome_id": 132, "name": "flower_forest"},
            {"x": -935, "z": 2592, "y": 200, "biome_id": 5, "name": "taiga"},
            {"x": -2697, "z": 1363, "y": 200, "biome_id": 4, "name": "forest"}
        ]
    }
    
    if config and 'high32' in config:
        # Merge with defaults
        for key, value in default.items():
            if key not in config['high32']:
                config['high32'][key] = value
        return config['high32']
    
    return default

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
    # Version mapping (only supported versions)
    version_map = {
        '26.30+': 38,  # MC_26_2
        '1.21.60-26.23': 29,  # MC_1_21_5
        '1.21.50': 28,  # MC_1_21_WD
        '1.21-1.21.40': 27,  # MC_1_21_3
        '1.20.60-81': 25,  # MC_1_20
        '1.20.0-51': 25,  # MC_1_20
        '1.19': 24,  # MC_1_19
        '1.18': 22,  # MC_1_18
    }
    
    # Check if exact version is in map
    if mc_version in version_map:
        return version_map[mc_version]
    
    # Try partial match (e.g., '1.21.60' should match '1.21.60-26.23')
    parts = mc_version.split('.')
    if len(parts) >= 2:
        major_minor = f"{parts[0]}.{parts[1]}"
        # Try to find closest match
        for ver_key in version_map:
            if ver_key.startswith(major_minor):
                return version_map[ver_key]
    
    # Default to latest version
    print(f"[WARNING] Unknown MC version '{mc_version}', using latest (26.30+)")
    return 38  # MC_26_2