# -*- coding: utf-8 -*-
"""
Biome Version Filter for Linux CLI
Biome version compatibility checking for command-line version
"""

# Biome version mapping (based on Bedrock version)
VERSION_BIOMES = {
    '1.18': [174, 175, 177, 178, 179, 180, 181, 182],  # Dripstone Caves, Lush Caves, Mountain biomes
    '1.19': [183, 184],  # Deep Dark, Mangrove Swamp
    '1.20': [185],  # Cherry Grove
    '1.21.50': [186],  # Pale Garden (added in Bedrock 1.21.50)
    '1.21.60-26.23': [186],  # Pale Garden (expanded range)
    '26.30+': [187],  # Sulfur Caves (added in Bedrock 26.30+)
}

VERSION_ORDER = ['1.18', '1.19', '1.20', '1.21.40', '1.21.50', '1.21.60-26.23', '26.30+']


def normalize_version(version_key):
    """Map user-selected version string to VERSION_ORDER
    
    Bedrock version to cubiomes version mapping:
    - 26.30+ = Java 26.2 (MC_26_2) - Sulfur Caves
    - 1.21.60-26.23 = Java 1.21.5-26.1 (MC_1_21_5) - Pale Garden expanded range
    - 1.21.50 = Java 1.21.4 Winter Drop (MC_1_21_WD) - Supports Pale Garden
    - 1.21-1.21.40 = Java 1.21.3 (MC_1_21_3) - Does not support Pale Garden
    
    Examples:
        "26.30+" → "26.30+" (Sulfur Caves)
        "1.21.60-26.23" → "1.21.60-26.23" (Pale Garden expanded range)
        "1.21.50" → "1.21.50" (supports Pale Garden)
        "1.21-1.21.40" → "1.21.40" (does not support Pale Garden)
        "1.20.60-81" → "1.20"
        "1.20.0-51" → "1.20"
    """
    # Version mapping (based on biome generation characteristics)
    VERSION_MAPPING = {
        # 26.30+: Supports Sulfur Caves (corresponds to cubiomes MC_26_2)
        "26.30+": "26.30+",
        
        # 1.21.60-26.23: Pale Garden expanded range (corresponds to cubiomes MC_1_21_5)
        "1.21.60-26.23": "1.21.60-26.23",
        
        # 1.21.50: Supports Pale Garden (corresponds to cubiomes MC_1_21_WD)
        "1.21.50": "1.21.50",
        
        # 1.21-1.21.40: Does not support Pale Garden (corresponds to cubiomes MC_1_21_3)
        "1.21-1.21.40": "1.21.40",
        
        # 1.20 versions
        "1.20.60-81": "1.20",
        "1.20.0-51": "1.20",
        
        # 1.19 version
        "1.19": "1.19",
        
        # 1.18 version
        "1.18": "1.18",
    }
    
    return VERSION_MAPPING.get(version_key, "26.30+")


def get_biome_version(biome_id):
    """Get minimum version required for a biome"""
    for version, biome_ids in VERSION_BIOMES.items():
        if biome_id in biome_ids:
            return version
    return '1.18'  # Default: versions below 1.18 are all supported


def is_biome_available(biome_id, mc_version):
    """Check if a biome is available in the specified version"""
    biome_version = get_biome_version(biome_id)
    
    # First map user-selected version string to standard version
    normalized_version = normalize_version(mc_version)
    
    biome_idx = VERSION_ORDER.index(biome_version) if biome_version in VERSION_ORDER else 0
    mc_idx = VERSION_ORDER.index(normalized_version) if normalized_version in VERSION_ORDER else len(VERSION_ORDER) - 1
    
    return biome_idx <= mc_idx


def check_biome_version_compatibility_cli(biome_ids, mc_version):
    """Check biome version compatibility (command-line version)"""
    warnings = []
    for biome_id in biome_ids:
        biome_version = get_biome_version(biome_id)
        if not is_biome_available(biome_id, mc_version):
            warnings.append({
                'biome_id': biome_id,
                'required_version': biome_version,
                'current_version': mc_version,
                'message': f"⚠️  Biome ID {biome_id} requires {biome_version}+ version, current version is {mc_version}"
            })
    
    return warnings


def print_version_warnings(warnings):
    """Print version warning messages"""
    if warnings:
        print("\n" + "=" * 80)
        print("Version Compatibility Warning")
        print("=" * 80)
        for w in warnings:
            print(w['message'])
        print("\nRecommendations:")
        print("  - Continuing with these biome samples may cause cracking failure")
        print("  - Please switch to biome samples supported by the current version")
        print("=" * 80)
        return True
    return False