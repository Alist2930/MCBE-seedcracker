# -*- coding: utf-8 -*-
"""
Minecraft Bedrock Version Mapping Configuration
For WinUI and Linux version selection
"""

# ==================== Version Mapping ====================

# Bedrock version -> cubiomes code mapping (based on ChunkBase version correspondence)
BEDROCK_VERSION_MAP = {
    # Bedrock 1.21.50
    "1.21.50": {
        "cubiomes_code": 21,  # MC_1_21_WD
        "warning": None
    },
    
    # Bedrock 1.21-1.21.40 (no Pale Garden)
    "1.21-1.21.40": {
        "cubiomes_code": 21,  # MC_1_21_3
        "warning": None
    },
    
    # Bedrock 1.20.60-1.20.81
    "1.20.60-81": {
        "cubiomes_code": 20,  # MC_1_20
        "warning": None
    },
    
    # Bedrock 1.20.0-1.20.51
    "1.20.0-51": {
        "cubiomes_code": 20,  # MC_1_20
        "warning": None
    },
    
    # Bedrock 1.19
    "1.19": {
        "cubiomes_code": 19,  # MC_1_19
        "warning": None
    },
    
    # Bedrock 1.18
    "1.18": {
        "cubiomes_code": 18,  # MC_1_18
        "warning": None
    }
}

# WinUI version selector display options (only show Bedrock versions)
WINUI_VERSION_OPTIONS = [
    # Bedrock options
    {"text_zh": "1.21.50", "text_en": "1.21.50", "data": "1.21.50", "type": "bedrock"},
    {"text_zh": "1.21-1.21.40", "text_en": "1.21-1.21.40", "data": "1.21-1.21.40", "type": "bedrock"},
    {"text_zh": "1.20.60-1.20.81", "text_en": "1.20.60-1.20.81", "data": "1.20.60-81", "type": "bedrock"},
    {"text_zh": "1.20.0-1.20.51", "text_en": "1.20.0-1.20.51", "data": "1.20.0-51", "type": "bedrock"},
    {"text_zh": "1.19", "text_en": "1.19", "data": "1.19", "type": "bedrock"},
    {"text_zh": "1.18", "text_en": "1.18", "data": "1.18", "type": "bedrock"},
]

def get_cubiomes_version(bedrock_version_key):
    """Get cubiomes version code"""
    mapping = BEDROCK_VERSION_MAP.get(bedrock_version_key)
    if mapping:
        return mapping.get("cubiomes_code", 21)
    return 21  # Default to latest version

def get_version_warning(version_key):
    """Get version warning message"""
    mapping = BEDROCK_VERSION_MAP.get(version_key)
    if mapping and mapping.get("warning"):
        return mapping["warning"]
    return None