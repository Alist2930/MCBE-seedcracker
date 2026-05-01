# -*- coding: utf-8 -*-
"""
Minecraft Bedrock Biome Query Tool

Query the biome ID at a specific coordinate for a given seed.

Usage:
    python get_biome.py --seed 123456789 --x 100 --y 64 --z -200
    python get_biome.py --seed 123456789 --x 100 --y 64 --z -200 --version 1.21
"""
import ctypes
import argparse
from pathlib import Path

BIOME_IDS = {
    0: 'ocean', 1: 'plains', 2: 'desert', 3: 'windswept_hills',
    4: 'forest', 5: 'taiga', 6: 'swamp', 7: 'river', 8: 'nether_wastes',
    9: 'the_end', 10: 'frozen_ocean', 11: 'frozen_river', 12: 'snowy_plains',
    13: 'snowy_mountains', 14: 'mushroom_fields', 15: 'unknown', 16: 'beach',
    17: 'desert_hills', 18: 'wooded_hills', 19: 'taiga_hills', 20: 'unknown',
    21: 'jungle', 22: 'jungle_hills', 23: 'sparse_jungle', 24: 'deep_ocean',
    25: 'stony_shore', 26: 'snowy_beach', 27: 'birch_forest', 28: 'birch_forest_hills',
    29: 'dark_forest', 30: 'snowy_taiga', 31: 'unknown', 32: 'old_growth_pine_taiga',
    33: 'unknown', 34: 'windswept_forest', 35: 'savanna',
    36: 'savanna_plateau', 37: 'badlands', 38: 'wooded_badlands', 39: 'badlands_plateau',
    40: 'unknown', 41: 'unknown', 42: 'unknown', 43: 'unknown',
    44: 'warm_ocean', 45: 'lukewarm_ocean', 46: 'cold_ocean', 47: 'deep_warm_ocean',
    48: 'deep_lukewarm_ocean', 49: 'deep_cold_ocean', 50: 'deep_frozen_ocean',
    129: 'sunflower_plains', 130: 'desert_lakes', 131: 'windswept_gravelly_hills',
    132: 'flower_forest', 140: 'ice_spikes', 155: 'old_growth_birch_forest',
    160: 'old_growth_spruce_taiga', 163: 'windswept_savanna', 165: 'eroded_badlands',
    168: 'bamboo_jungle', 170: 'soul_sand_valley', 171: 'crimson_forest',
    172: 'warped_forest', 173: 'basalt_deltas', 174: 'dripstone_caves', 175: 'lush_caves',
    177: 'meadow', 178: 'grove', 179: 'snowy_slopes', 180: 'jagged_peaks',
    181: 'frozen_peaks', 182: 'stony_peaks', 183: 'deep_dark', 184: 'mangrove_swamp',
    185: 'cherry_grove', 186: 'pale_garden',
}

VERSION_MAP = {
    "1.18": 22,
    "1.19": 24,
    "1.20": 25,
    "1.21": 28,
}

def get_biome_at_seed(dll_path: Path, seed: int, x: int, y: int, z: int, mc_version: int) -> int:
    lib = ctypes.CDLL(str(dll_path))
    
    lib.getBiomeAtSeed.argtypes = [
        ctypes.c_uint64, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int
    ]
    lib.getBiomeAtSeed.restype = ctypes.c_int
    
    return lib.getBiomeAtSeed(seed, x, y, z, mc_version)

def main():
    parser = argparse.ArgumentParser(description='Minecraft Bedrock Biome Query Tool')
    parser.add_argument('--seed', type=int, required=True, help='Full 64-bit seed')
    parser.add_argument('--x', type=int, required=True, help='X coordinate (block)')
    parser.add_argument('--y', type=int, required=True, help='Y coordinate (block)')
    parser.add_argument('--z', type=int, required=True, help='Z coordinate (block)')
    parser.add_argument('--version', type=str, default='1.21', help='MC version (1.18, 1.19, 1.20, 1.21)')
    args = parser.parse_args()
    
    dll_path = Path(__file__).parent / 'MCBEseedcracker' / 'crack_high32' / 'crack_high32.dll'
    
    if not dll_path.exists():
        print(f"[!] Error: DLL not found: {dll_path}")
        return
    
    mc_version = VERSION_MAP.get(args.version, 28)
    
    biome_id = get_biome_at_seed(dll_path, args.seed, args.x, args.y, args.z, mc_version)
    biome_name = BIOME_IDS.get(biome_id, f"unknown_{biome_id}")
    
    print(f"\n[*] Seed: {args.seed}")
    print(f"[*] Position: ({args.x}, {args.y}, {args.z})")
    print(f"[*] MC Version: {args.version}")
    print(f"\n[+] Biome ID: {biome_id}")
    print(f"[+] Biome Name: {biome_name}")

if __name__ == "__main__":
    main()
