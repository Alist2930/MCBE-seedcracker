# -*- coding: utf-8 -*-
"""
Biome Version Filter
"""
import json
from pathlib import Path
from .language_manager import lang_manager


VERSION_BIOMES = {
    '1.17': [],
    '1.18': [174, 175, 177, 178, 179, 180, 181, 182],
    '1.19': [183, 184],
    '1.20': [185],
    '1.21': [186],
}

VERSION_ORDER = ['1.17', '1.18', '1.19', '1.20', '1.21']


def get_biome_version(biome_id):
    for version, biome_ids in VERSION_BIOMES.items():
        if biome_id in biome_ids:
            return version
    return '1.17'


def is_biome_available(biome_id, mc_version):
    biome_version = get_biome_version(biome_id)
    biome_idx = VERSION_ORDER.index(biome_version) if biome_version in VERSION_ORDER else 0
    mc_idx = VERSION_ORDER.index(mc_version) if mc_version in VERSION_ORDER else len(VERSION_ORDER) - 1
    return biome_idx <= mc_idx


def get_available_biomes(mc_version, biome_data):
    available_biomes = {}
    for biome_name, biome_info in biome_data.items():
        biome_id = biome_info.get('id')
        if biome_id is not None and is_biome_available(biome_id, mc_version):
            available_biomes[biome_name] = biome_info
    return available_biomes


def check_biome_version_compatibility(biomes, mc_version, biome_data):
    warnings = []
    for biome in biomes:
        biome_name = biome.get('type')
        biome_info = biome_data.get(biome_name, {})
        biome_id = biome_info.get('id')
        
        if biome_id is not None:
            biome_version = get_biome_version(biome_id)
            if not is_biome_available(biome_id, mc_version):
                biome_display_name = biome_info.get('name_zh', biome_name) if lang_manager.language == "zh_CN" else biome_info.get('name_en', biome_name)
                if lang_manager.language == "zh_CN":
                    message = f"{biome_display_name} 需要 {biome_version}+ 版本，当前版本 {mc_version}"
                else:
                    message = f"{biome_display_name} requires {biome_version}+ version, current version is {mc_version}"
                
                warnings.append({
                    'biome': biome_name,
                    'biome_id': biome_id,
                    'required_version': biome_version,
                    'current_version': mc_version,
                    'message': message
                })
    
    return warnings


def get_version_display_name(version):
    version_names = {
        '1.17': '1.17 (洞穴与山崖 Part 1)',
        '1.18': '1.18 (洞穴与山崖 Part 2)',
        '1.19': '1.19 (荒野更新)',
        '1.20': '1.20 (足迹与故事)',
        '1.21': '1.21 (棘巧试炼)',
    }
    return version_names.get(version, version)
