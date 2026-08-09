# -*- coding: utf-8 -*-
"""
Data loader - access to ui/data/biomes.json and ui/data/structures.json
"""
import json
import os

from .language_manager import lang_manager
from .paths import get_data_path

BIOME_DATA_FILE = "biomes.json"
STRUCTURE_DATA_FILE = "structures.json"


def load_data_file(filename, default=None):
    """Load a JSON data file, falling back to `default` when missing"""
    data_file = get_data_path(filename)
    if os.path.exists(data_file):
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default if default is not None else {}


def load_biome_data(default=None):
    return load_data_file(BIOME_DATA_FILE, default)


def load_structure_data(default=None):
    return load_data_file(STRUCTURE_DATA_FILE, default)


def get_biome_id(biome_data, biome_name):
    """Get the numeric id of a biome, or None when unknown"""
    return biome_data.get(biome_name, {}).get('id')


def get_biome_name(biome_data, biome_id):
    """Get the internal name of a biome id, or None when unknown"""
    for name, info in biome_data.items():
        if info.get('id') == biome_id:
            return name
    return None


def get_rarity(entry_info, mc_version):
    """Get the rarity of a biome entry for a Bedrock version (1.0 when unknown)"""
    rarity_dict = entry_info.get('rarity', {})
    if not isinstance(rarity_dict, dict):
        return 1.0
    return rarity_dict.get(mc_version, 1.0)


def get_biome_rarity(biome_data, biome_name, mc_version):
    """Get the rarity of a biome name for a Bedrock version"""
    return get_rarity(biome_data.get(biome_name, {}), mc_version)


def get_display_name(entry_info, fallback):
    """Get the localized display name of a biome / structure entry"""
    if lang_manager.language == "zh_CN":
        return entry_info.get('name_zh', fallback)
    return entry_info.get('name_en', fallback)


def get_bilingual_name(entry_info, fallback):
    """Get the display name of an entry, keeping the English name in Chinese UI"""
    if lang_manager.language == "zh_CN":
        return f"{entry_info.get('name_zh', fallback)} ({entry_info.get('name_en', '')})"
    return entry_info.get('name_en', fallback)
