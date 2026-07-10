# MCBEseedcracker (Linux)

English | [简体中文](README_CN.md)

Minecraft Bedrock Edition Seed Cracker - Linux Command Line Version

> For Windows GUI version, see [MCBEseedcracker_win_ui](../MCBEseedcracker_win_ui/README.md)

---

## Requirements

- **OS**: Linux (x86_64)
- **Python**: 3.6+
- **Game Version**: 1.18/1.19/1.20/1.21/26.XX

---

## Quick Start

### Low 32-bit Cracking

```bash
cd crack_low32
python3 crack_low32.py                    # Full crack (0 - 2^32-1)
python3 crack_low32.py --test             # Test mode (0 - 100M)
python3 crack_low32.py --start 1000 --end 2000  # Custom range
```

### High 32-bit Cracking

```bash
cd crack_high32
python3 crack_high32.py                         # Full crack (0 ~ 2^32-1)
python3 crack_high32.py --test                  # Test mode (0 ~ 100M)
python3 crack_high32.py --low32 1818588773      # Specify low32 value
```

---

## Low 32-bit Cracker

Crack the low 32 bits of the seed using structure locations.

### Command Line Arguments

| Argument  | Description                       |
| --------- | --------------------------------- |
| `--start` | Start low32 value (default: 0)    |
| `--end`   | End low32 value (default: 2^32-1) |
| `--test`  | Test mode (0 - 100M)              |

### Configure Target Structures

Edit `TARGETS` at the beginning of `crack_low32.py` (recommended: 5 structures):

```python
TARGETS = [
    {"structure": "swamp_hut", "x": 2136, "z": -1176},
    {"structure": "jungle_temple", "x": -360, "z": -248},
    {"structure": "desert_temple", "x": -936, "z": 4744},
    {"structure": "ocean_monument", "x": 792, "z": -792},
    {"structure": "end_city", "x": 1352, "z": -1208},
]
```

### Supported Structures

| Name             | Description             | Spread Type |
| ---------------- | ----------------------- | ----------- |
| village          | Village/Zombie Village  | triangular  |
| mansion          | Woodland Mansion        | triangular  |
| end_city         | End City                | triangular  |
| ocean_monument   | Ocean Monument          | triangular  |
| ancient_city     | Ancient City            | triangular  |
| ocean_ruins      | Ocean Ruins             | **linear**  |
| shipwreck        | Shipwreck               | **linear**  |
| nether_complexes | Nether Fortress/Bastion | **linear**  |
| desert_temple    | Desert Temple           | **linear**  |
| igloo            | Igloo                   | **linear**  |
| swamp_hut        | Witch Hut               | **linear**  |
| jungle_temple    | Jungle Temple           | **linear**  |

Coordinates just need to be within the same chunk.

> **Tip**: Prioritize **linear** type structures (Desert Temple, Witch Hut, Jungle Temple, Shipwreck). The program automatically sorts linear types first for processing, requiring less computation and faster cracking.

### Structure Chunk Location Method

- **Desert Temple**: Chunk containing the center position
- **Ocean Monument**: Chunk containing the center position
- **Witch Hut**: Chunk with the largest building area
- **Jungle Temple**: Chunk with the largest building area
- **End City**: Chunk with the largest shulker box structure area at entrance
- **Shipwreck**: For complete ships, use the bow chunk (bow is roughly at the chunk boundary); for incomplete ships, use the chunk with the largest ship area

---

## High 32-bit Cracker

Crack the high 32 bits of the seed using biome samples.

### Command Line Arguments

| Argument      | Description                              |
| ------------- | ---------------------------------------- |
| `--start`     | Start high32 value (default: 0)          |
| `--end`       | End high32 value (default: 2^32-1)       |
| `--test`      | Test mode (0 - 100M)                     |
| `--low32`     | Low 32-bit value                         |
| `--processes` | Number of processes (default: CPU cores) |

### Automatic Rarity Sorting

The program automatically sorts samples by biome rarity, checking the rarest biomes first. If the first sample doesn't match, it immediately skips the current seed, greatly improving efficiency:

```
[*] Biome samples (sorted by rarity, rarest first):
    1. (-270, 470) -> pale_garden (ID: 186, 0.0786%)
    2. (-1922, 1231) -> cherry_grove (ID: 185, 0.2805%)
    3. (-4706, 3302) -> flower_forest (ID: 132, 0.6529%)
    ...
```

### Configuration

Edit the beginning of `crack_high32.py`:

```python
# Low 32-bit value (from crack_low32 result)
LOW32 = 1818588773

# MC version
MC_VERSION_STR = "1.21"  # Options: "1.18", "1.19", "1.20", "1.21" (for 26.XX, use "1.21")

# Biome samples (recommended: 5)
SAMPLES = [
    (-1922, 1231, 185),   # cherry_grove
    (-4706, 3302, 132),   # flower_forest
    (-935, 2592, 5),      # taiga
    (-2697, 1363, 4),     # forest
    (-270, 470, 186),     # pale_garden
]

Y_COORD = 200  # Sampling height (surface recommended Y>=200, avoid underground biome interference)
```

> **Important**: Biome samples must use **Overworld** biomes only. Do not use biomes from the Nether or End.

### Biome Sample Selection Tips

- **Choose coordinates at biome centers**, at least 3 blocks away from biome boundaries
- **Avoid sampling near biome boundaries**
- If cracking fails, try different coordinates within the same biome

---

## Biome ID Reference (1.21)

| Biome                    | ID  | Rarity | Biome                 | ID  | Rarity |
| ------------------------ | --- | ------ | --------------------- | --- | ------ |
| pale_garden              | 186 | 0.08%  | extreme_hills_mutated | 131 | 0.10%  |
| stony_peaks              | 182 | 0.10%  | jagged_peaks          | 180 | 0.15%  |
| frozen_peaks             | 181 | 0.15%  | mushroom_island       | 14  | 0.14%  |
| extreme_hills_plus_trees | 34  | 0.19%  | cherry_grove          | 185 | 0.28%  |
| ice_spikes               | 140 | 0.23%  | extreme_hills         | 3   | 0.27%  |
| savanna_mutated          | 163 | 0.22%  | mesa_bryce            | 165 | 0.33%  |
| snowy_slopes             | 179 | 0.39%  | savanna_plateau       | 36  | 0.40%  |
| mangrove_swamp           | 184 | 0.52%  | flower_forest         | 132 | 0.65%  |
| bamboo_jungle            | 168 | 0.65%  | sunflower_plains      | 129 | 0.66%  |
| mega_taiga               | 32  | 0.68%  | mesa_plateau_stone    | 38  | 0.64%  |
| grove                    | 178 | 0.75%  | mesa                  | 37  | 0.90%  |
| swamp                    | 6   | 1.00%  | cold_beach            | 26  | 0.35%  |
| stone_beach              | 25  | 1.19%  | jungle_edge           | 23  | 1.26%  |
| deep_frozen_ocean        | 50  | 1.21%  | meadow                | 177 | 1.18%  |
| roofed_forest            | 29  | 2.00%  | jungle                | 21  | 1.90%  |
| birch_forest             | 27  | 2.14%  | desert                | 2   | 2.47%  |
| cold_taiga               | 30  | 2.56%  | frozen_river          | 11  | 0.82%  |
| warm_ocean               | 44  | 2.24%  | deep_lukewarm_ocean   | 48  | 2.45%  |
| deep_cold_ocean          | 49  | 2.40%  | frozen_ocean          | 10  | 2.27%  |
| beach                    | 16  | 2.67%  | ice_plains            | 12  | 2.79%  |
| taiga                    | 5   | 3.41%  | savanna               | 35  | 4.00%  |
| deep_ocean               | 24  | 4.38%  | lukewarm_ocean        | 45  | 4.61%  |
| cold_ocean               | 46  | 4.51%  | river                 | 7   | 6.17%  |
| ocean                    | 0   | 6.87%  | plains                | 1   | 10.52% |
| forest                   | 4   | 12.07% | birch_forest_mutated  | 155 | 2.09%  |
| dripstone_caves          | 174 | -      | lush_caves            | 175 | -      |
| deep_dark                | 183 | -      | sulfur_caves          | -   | -      |

> **Note**: Rarity based on surface Y=200 sampling. Underground biomes (dripstone_caves, lush_caves, deep_dark, sulfur_caves) are not included in rarity sorting, default rarity is 1.

> **Warning**: `sulfur_caves` (Sulfur Caves) is a new biome added in MC 1.26+. cubiomes library does not support this biome. Avoid using sulfur_caves samples for cracking.

> **Note**: Biome names on ChunkBase and similar sites follow Java Edition naming, which differs from Bedrock. For example: Java's `stony_shore` is `stone_beach` in Bedrock, Java's `dark_forest` is `roofed_forest` in Bedrock. Please note the distinction when verifying.

---

## Version Compatibility

### Version Mapping

| MC Version | New Biomes                                   |
| ---------- | -------------------------------------------- |
| 1.18       | Dripstone Caves, Lush Caves, Mountain biomes |
| 1.19       | Deep Dark, Mangrove Swamp                    |
| 1.20       | Cherry Grove                                 |
| 1.21       | Pale Garden                                  |

### Bedrock vs Java Differences

Even with same version number, Java and Bedrock have biome generation differences:

- **Y-axis Biome Changes**: Java biomes change significantly on Y-axis, Bedrock is more stable
- **Biome Boundaries**: Biome boundary positions may differ slightly between versions
- **New Version Differences**: Bedrock 1.26.x has minor differences from Java 1.21 biome algorithms

#### Biome Sample Selection Tips

- **Choose coordinates at biome centers**, at least 3 blocks away from biome boundaries
- **Avoid sampling near biome boundaries**
- If cracking fails, try different coordinates within the same biome

### ⚠️ Important Limitation

**High 32-bit cracking is based on cubiomes library, which only supports up to Java 1.21.4 (Winter Drop) and stopped updating after November 2024.**

| cubiomes Info  | Details                   |
| -------------- | ------------------------- |
| Latest Version | 4.1.2                     |
| Last Update    | November 10, 2024         |
| Max Supported  | Java 1.21.4 (Winter Drop) |

**cubiomes Update Status:**

- cubiomes **stopped updating** after releasing 4.1.2 in November 2024
- Does not support Bedrock 1.26+
- Does not support Minecraft versions from 2025 onwards

#### Pale Garden Version Differences

**Important**: cubiomes library currently only supports up to MC 1.21.4 (Winter Drop), while MC 1.21.5+ has adjusted Pale Garden generation range.

| MC Version         | cubiomes Support | Pale Garden Generation                               |
| ------------------ | ---------------- | ---------------------------------------------------- |
| 1.21.3 and earlier | ✅ (code 27)     | Doesn't exist, position is Dark Forest               |
| 1.21.4             | ✅ (code 28)     | Exists, but smaller range                            |
| 1.21.5+            | ❌ Not supported | Expanded range, some Dark Forest becomes Pale Garden |

**If you collected Pale Garden samples in 1.21.5+ but cracking failed**:

This is likely because cubiomes 1.21 version (code 28) corresponds to 1.21.4, which has a smaller Pale Garden generation range than 1.21.5+.

**Solution**:

Change Pale Garden samples to Dark Forest (roofed_forest, ID: 29) and try again.

---

## Building

Pre-compiled library files are included. To build yourself:

```bash
# Install dependencies
sudo apt install -y gcc libomp-dev  # Debian/Ubuntu
sudo dnf install -y gcc libgomp-devel  # Fedora/RHEL

# Build
chmod +x build.sh
./build.sh
```

---

## Performance Reference

Test device: Intel Core i5-2500K @ 3.30GHz, 4 cores

| Cracker     | Speed  | Estimated Time (2^32) |
| ----------- | ------ | --------------------- |
| Low 32-bit  | ~3M/s  | ~24 minutes           |
| High 32-bit | ~70K/s | ~17 hours             |

---

## FAQ

### Low 32-bit cracking failed (no matching seeds found)

**Possible causes:**

1. **Incorrect structure coordinates** - Coordinates are wrong, or chunk location method is incorrect
2. **Insufficient structures** - Too few structures will result in too many candidate seeds, recommend at least 5 different structure types
3. **Poor structure type selection** - Some structures (like villages) have complex generation rules. Recommended:
   - Desert Temple, Witch Hut, Jungle Temple (simple and stable generation rules)
   - Ocean Monument, End City
4. **Version incompatibility** - If the target world was generated in an older version (pre-1.18), structure positions may differ from current version

**Solutions:**

- Verify coordinates are correct
- Add more structures
- Change structure types
- Confirm the target world's generation version

### High 32-bit cracking failed (no matching seeds found)

**Possible causes:**

1. **Incorrect low 32-bit value** - Low 32-bit cracking result is wrong
2. **Incorrect biome samples** - Coordinates or biome IDs are wrong
3. **Improper sampling height** - Recommend Y >= 200 to avoid underground biome interference
4. **Insufficient biome samples** - Recommend at least 5 samples
5. **Poor sample selection** - Should choose rare biomes (like Cherry Grove), avoid common biomes (like Plains, Ocean)

**Solutions:**

- Confirm low 32-bit value is correct
- Verify biome sample coordinates and IDs
- Increase sampling height
- Choose rare biomes as samples

### Cracking takes too long

**Low 32-bit cracking:** Normally about 20-30 minutes (4-core CPU)

**High 32-bit cracking:** Normally about 10-20 hours (4-core CPU)

If significantly longer:

- Check CPU usage to confirm multi-threading is working
- Reduce biome sample count (but will lower accuracy)
- Use `--test` parameter for small range testing first

---

## Verify Seed

After cracking, verify the seed on [ChunkBase](https://www.chunkbase.com/apps/seed-map).

---

## Related Links

- [cubiomes](https://github.com/Cubitect/cubiomes) - Minecraft biome generation simulation library, used for biome calculation in high 32-bit cracking
- [Mersenne Twister (MT19937)](https://en.wikipedia.org/wiki/Mersenne_Twister) - Random number generator used in low 32-bit cracking for structure offset calculation

---

## License

This project is for learning and research purposes only.
