# -*- coding: utf-8 -*-
"""
Biome Version Filter - Biome version checking with sub-version support
"""
from .language_manager import lang_manager


# ==================== Biome Version Mapping (Based on Bedrock Version) ====================

VERSION_BIOMES = {
    '1.18': [
        174, 175,  # Dripstone Caves, Lush Caves
        177, 178, 179, 180, 181, 182  # Mountain biomes (Meadow, Grove, Snowy Slopes, Jagged Peaks, Frozen Peaks, Stony Peaks)
    ],
    '1.19': [
        183, 184  # Deep Dark, Mangrove Swamp
    ],
    '1.20': [
        185  # Cherry Grove
    ],
    '1.21.50': [
        186  # Pale Garden (Added in Bedrock 1.21.50, corresponds to Java 1.21.4 Winter Drop)
    ],
}

VERSION_ORDER = ['1.18', '1.19', '1.20', '1.21.40', '1.21.50']


def normalize_version(version_key):
    """Map user-selected version string to VERSION_ORDER
    
    Bedrock version to cubiomes version mapping:
    - 1.21.50 = Java 1.21.4 Winter Drop (MC_1_21_WD) - Supports Pale Garden
    - 1.21-1.21.40 = Java 1.21.3 (MC_1_21_3) - Does not support Pale Garden
    
    Examples:
        "1.21.50" → "1.21.50" (supports Pale Garden)
        "1.21-1.21.40" → "1.21.40" (does not support Pale Garden)
        "1.20.60-81" → "1.20"
        "1.20.0-51" → "1.20"
    """
    # Version mapping (based on biome generation characteristics)
    VERSION_MAPPING = {
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
    
    return VERSION_MAPPING.get(version_key, "1.18")


def get_biome_version(biome_id):
    """Get the minimum version required for a biome"""
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


def check_biome_version_compatibility(biomes, mc_version, biome_data):
    """Check biome version compatibility (supports Chinese and English)"""
    warnings = []
    for biome in biomes:
        biome_name = biome.get('type')
        biome_info = biome_data.get(biome_name, {})
        biome_id = biome_info.get('id')
        
        if biome_id is not None:
            biome_version = get_biome_version(biome_id)
            # Use normalized version for comparison
            normalized_version = normalize_version(mc_version)
            if not is_biome_available(biome_id, mc_version):
                # Select display name based on language
                biome_display_name = biome_info.get('name_zh', biome_name) if lang_manager.language == "zh_CN" else biome_info.get('name_en', biome_name)
                
                # Select warning message based on language
                if lang_manager.language == "zh_CN":
                    message = f"群系「{biome_display_name}」需要 {biome_version}+ 版本，当前选择的版本是 {mc_version}。"
                else:
                    message = f"Biome '{biome_display_name}' requires {biome_version}+ version, current version is {mc_version}."
                
                warnings.append({
                    'biome': biome_name,
                    'biome_id': biome_id,
                    'required_version': biome_version,
                    'current_version': mc_version,
                    'message': message
                })
    
    return warnings


def check_single_biome_version(biome_name, mc_version, biome_data):
    """Check single biome version compatibility (immediate check when adding biome)
    If version is incompatible, return unavailable (do not allow adding)
    """
    biome_info = biome_data.get(biome_name, {})
    biome_id = biome_info.get('id')
    
    if biome_id is not None:
        biome_version = get_biome_version(biome_id)
        if not is_biome_available(biome_id, mc_version):
            # Select display name based on language
            biome_display_name = biome_info.get('name_zh', biome_name) if lang_manager.language == "zh_CN" else biome_info.get('name_en', biome_name)
            
            # Select warning message based on language (do not allow adding, return error directly)
            if lang_manager.language == "zh_CN":
                return {
                    'available': False,
                    'message': f"群系「{biome_display_name}」需要 {biome_version}+ 版本才能生成。\n当前选择的版本是 {mc_version}，该群系不存在。\n\n请切换到 {biome_version}+ 版本后再添加此群系。",
                    'allow_add': False  # Do not allow adding
                }
            else:
                return {
                    'available': False,
                    'message': f"Biome '{biome_display_name}' requires {biome_version}+ version to generate.\nCurrent version is {mc_version}, this biome does not exist.\n\nPlease switch to {biome_version}+ version before adding this biome.",
                    'allow_add': False  # Do not allow adding
                }
    
    return {'available': True, 'message': None}