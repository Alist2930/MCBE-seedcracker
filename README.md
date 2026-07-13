# MCBEseedcracker

English | [简体中文](README_CN.md)

Minecraft Bedrock Edition Seed Research Tool (Windows / Linux)

> **Disclaimer**: This tool is for educational and research purposes only. It is designed to help players understand Minecraft's biome generation algorithms and verify seeds for single-player worlds. It is NOT intended for cheating on multiplayer servers or exploiting game mechanics.
>
> Similar open-source projects exist on GitHub:
>
> - [cubiomes](https://github.com/Cubitect/cubiomes) - Minecraft biome generation simulation library
> - [SeedcrackerX](https://github.com/19MisterX98/SeedcrackerX) - Java Edition seed finder
>
> I'm a Minecraft newbie. Most of this code was written by AI, and I'm mainly responsible for testing and feature requests. Feedback and corrections are welcome.
>
> **Project Status**: Work in progress, currently for personal use. Feedback and suggestions are welcome.

---

## Features

Research tool for understanding Minecraft's world generation algorithms through seed verification and biome analysis.

---

## Requirements

- **OS**: Windows 10+ or Linux (x86_64)
- **Game Version**: 1.18/1.19/1.20/1.21/26.XX

> **Version Notes**:
>
> - **Low 32-bit cracking (structure locating)**: No version compatibility issues. The structure generation algorithm's dependency on the low 32 bits is stable.
> - **High 32-bit cracking (biomes)**: Version compatibility has been handled (based on cubiomes library). Please report any issues.

---

## Quick Start

| Platform    | Version      | Interface | Usage                              |
| ----------- | ------------ | --------- | ---------------------------------- |
| **Windows** | GUI Version  | GUI       | Run from source, see details below |
| **Linux**   | Command Line | Terminal  | Edit config files then run         |

### Windows Users (Recommended)

**Windows GUI Version** - no command line or code editing needed!

See [MCBEseedcracker_win_ui/README.md](MCBEseedcracker_win_ui/README.md) for details.

**Features:**

- ✅ Graphical interface - no coding required
- ✅ Low 32-bit & High 32-bit cracking
- ✅ Progress save/restore
- ✅ Chinese/English support
- ✅ MC 1.18/1.19/1.20/1.21/26.XX support

### Linux Users

Use the command line version. See [MCBEseedcracker_linux/README.md](MCBEseedcracker_linux/README.md) for details.

---

## Directory Structure

```
MCBEseedcracker_win_ui/    # Windows GUI version (recommended)
├── dist/                  # Pre-built executable
├── ui/                    # UI source code
└── dll/                   # Pre-compiled DLLs

MCBEseedcracker_linux/     # Linux command line version
├── build.sh
├── crack_low32/
│   ├── crack_low32.so
│   ├── crack_low32.c
│   └── crack_low32.py
└── crack_high32/
    ├── crack_high32.so
    ├── crack_high32.c
    ├── crack_high32.py
    └── cubiomes/
```

> **Note**: The Windows command line version (`MCBEseedcracker/`) is no longer maintained. Please use the GUI version (`MCBEseedcracker_win_ui/`).

---

## Principles

### Low 32-bit Cracking Principle

Minecraft Bedrock Edition uses a 64-bit integer as the world seed. When generating structures, the system calculates a "region seed" based on region coordinates and the seed, then uses the MT19937 random number generator to determine the structure's offset position within the region.

#### Region Seed Calculation Formula

```
Region coords: rx = chunk_x / spacing, rz = chunk_z / spacing
Region seed: r_base = (rx × 2570712328 + rz × 4048968661 + salt) & 0xFFFFFFFF
Actual seed: r_seed = world_seed_low32 + r_base
```

Where `salt` is a structure-specific constant, for example:

- Desert Temple: 14357617
- Ocean Monument: 10387313
- Shipwreck: 165745295

#### Structure Generation Parameters

Each structure has two key parameters:

- **spacing (region size)**: The side length of the structure generation region, measured in chunks. The world is divided into `spacing × spacing` region grids, with at most one structure per region.
- **separation (minimum distance)**: The minimum distance between structures, measured in chunks. This determines the possible offset range within a region.

Offset range: `offset_range = spacing - separation`

For example, Desert Temple has `spacing=32`, `separation=8`, so the offset range is `32-8=24` chunks.

#### Structure Offset Calculation

Using MT19937 to generate random numbers, calculate offsets based on distribution type:

- **Linear mode**: `offset_x = temper(mt[0]) % offset_range`
- **Triangular mode**: `offset_x = (temper(mt[0]) % range + temper(mt[1]) % range) / 2`

#### Cracking Method

Iterate through all possible low 32-bit values (0 - 2³²-1, about 4.3 billion). For each candidate:

1. Calculate region seed `r_seed = w + r_base`
2. Initialize MT19937 and generate offset values
3. Check if offsets match actual structure positions

Multiple structures matching simultaneously can significantly narrow down candidates, typically completing within half an hour.

#### Supported Structures

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

> **Tip**: Prioritize **linear** type structures (Desert Temple, Witch Hut, Jungle Temple, Shipwreck). Linear types require less computation and crack faster.

**Coordinates just need to be within the same chunk.**

#### Structure Chunk Location Method

- **Desert Temple**: Chunk containing the center position
- **Ocean Monument**: Chunk containing the center position
- **Witch Hut**: Chunk with the largest building area
- **Jungle Temple**: Chunk with the largest building area
- **End City**: Chunk with the largest shulker box structure area at entrance
- **Shipwreck**: For complete ships, use the bow chunk (bow is roughly at the chunk boundary); for incomplete ships, use the chunk with the largest ship area

---

### High 32-bit Cracking Principle

After determining the low 32 bits, the high 32 bits are still needed to get the complete seed. Biome generation depends on the complete 64-bit seed, calculating biome type at each coordinate through multi-layer noise functions.

#### Why Use cubiomes Library

This project uses the [cubiomes](https://github.com/Cubitect/cubiomes) library for biome calculation. This is a C library specifically designed to simulate Minecraft Java Edition biome generation.

Starting from version 1.18, Minecraft Java and Bedrock Edition terrain generation algorithms are completely unified, using the same noise functions, climate parameter systems (temperature, humidity, continentalness, erosion, depth, weirdness), and Voronoi coordinate perturbation mapping. Therefore, the cubiomes library can be directly used to calculate Bedrock biomes without reimplementing complex noise generation algorithms.

#### Biome Generation Process (1.18+)

1. **Seed Initialization**: Initialize noise parameters using Xoroshiro RNG
2. **Climate Parameter Calculation**: Calculate 6 climate parameters
   - Temperature
   - Humidity
   - Continentalness
   - Erosion
   - Depth
   - Weirdness
3. **Noise Sampling**: Each parameter uses DoublePerlinNoise (multi-layer Perlin noise overlay)
4. **Biome Mapping**: Determine biome type based on climate parameter combinations

#### Voronoi Coordinate Mapping

Biome noise is calculated at 1:4 scale (one sample point per 4x4 block area). To get the biome at a specific 1:1 block coordinate, Voronoi perturbation must be applied for coordinate mapping:

```
sha256_hash = SHA256(seed)
voronoi_offset = voronoiAccess3D(sha256_hash, x, y, z)
actual_sample_coord = (x + voronoi_x, y + voronoi_y, z + voronoi_z)
```

This is the standard algorithm used in Java and Bedrock 1.18+.

#### Cracking Method

Iterate through all possible high 32-bit values (0 - 2³²-1). For each candidate seed:

1. Calculate complete 64-bit seed: `seed = (high32 << 32) | low32`
2. Initialize noise generator
3. Calculate biome ID for each sample coordinate
4. Compare with actual collected biome samples

Due to the need for complete traversal and complex biome calculations, it takes a long time, usually several hours.

> **Important**: Biome samples must use **Overworld** biomes only. Do not use biomes from the Nether or End.

#### Version Mapping

| Bedrock Version      | Corresponding Java Version | Supported Biomes                                |
| -------------------- | -------------------------- | ----------------------------------------------- |
| **1.21.60-1.21.132** | Java 1.21.5-1.21.11        | ✅ Pale Garden (expanded range)                 |
| **1.21.50**          | Java 1.21.4 (Winter Drop)  | ✅ Pale Garden (smaller range)                  |
| **1.21-1.21.40**     | Java 1.21.3                | ❌ No Pale Garden                               |
| **1.20.60-1.20.81**  | Java 1.20                  | ✅ Cherry Grove                                 |
| **1.20.0-1.20.51**   | Java 1.20                  | ✅ Cherry Grove                                 |
| **1.19**             | Java 1.19                  | ✅ Deep Dark, Mangrove Swamp                    |
| **1.18**             | Java 1.18                  | ✅ Dripstone Caves, Lush Caves, Mountain biomes |

#### Pale Garden Version Differences

⚠️ **Important**: Pale Garden generation range differs between versions:

| MC Version           | Pale Garden Generation                    |
| -------------------- | ----------------------------------------- |
| **1.21-1.21.40**     | ❌ Doesn't exist, position is Dark Forest |
| **1.21.50**          | ⚠️ Exists but smaller range               |
| **1.21.60-1.21.132** | ✅ Expanded generation range              |

**Latest version (Bedrock 1.21.60-1.21.132)**:

- Corresponds to Java 1.21.5-1.21.11
- Pale Garden has expanded generation range (weirdness threshold lowered)
- Best for Pale Garden-based cracking
- Rarity: ~0.12% (increased from 1.21.50's ~0.08%)

**If using 1.21.50**:

- Pale Garden exists but with smaller generation range
- If cracking fails, recommend using Dark Forest (roofed_forest, ID: 29)

#### Bedrock vs Java Differences

Even with same version number, Java and Bedrock have biome generation differences:

- **Y-axis Biome Changes**: Java biomes change significantly on Y-axis, Bedrock is more stable
- **Biome Boundaries**: Biome boundary positions may differ slightly between versions
- **New Version Differences**: Bedrock 1.26.x has minor differences from Java 1.21 biome algorithms

#### Biome Sample Selection Tips

- **Choose coordinates at biome centers**, at least 3 blocks away from biome boundaries
- **Avoid sampling near biome boundaries**
- If cracking fails, try different coordinates within the same biome

#### Important Limitation

**High 32-bit cracking is based on cubiomes library, which supports up to Java 1.21.11 (via community fork).**

| cubiomes Info  | Details                                        |
| -------------- | ---------------------------------------------- |
| Latest Version | 4.1.2 (fork)                                   |
| Last Update    | January 2025 (fork)                            |
| Max Supported  | Java 1.21.5-1.21.11 (Bedrock 1.21.60-1.21.132) |

**cubiomes Update Status:**

- Official cubiomes stopped updating after November 2024
- Integrated Praveenkumar801's fork for 1.21.5+ support
- Supports Pale Garden expanded generation range in 1.21.60+
- Does not support Bedrock 1.26+ (sulfur_caves biome)

#### Overworld Biome ID Reference (1.21.60-1.21.132)

| Biome                    | ID  | Rarity | Biome                 | ID  | Rarity |
| ------------------------ | --- | ------ | --------------------- | --- | ------ |
| extreme_hills_mutated    | 131 | 0.10%  | stony_peaks           | 182 | 0.10%  |
| pale_garden              | 186 | 0.12%  | mushroom_island       | 14  | 0.14%  |
| frozen_peaks             | 181 | 0.16%  | jagged_peaks          | 180 | 0.18%  |
| extreme_hills_plus_trees | 34  | 0.19%  | savanna_mutated       | 163 | 0.21%  |
| ice_spikes               | 140 | 0.24%  | extreme_hills         | 3   | 0.26%  |
| cherry_grove             | 185 | 0.29%  | mesa_bryce            | 165 | 0.33%  |
| cold_beach               | 26  | 0.36%  | snowy_slopes          | 179 | 0.39%  |
| savanna_plateau          | 36  | 0.40%  | mangrove_swamp        | 184 | 0.51%  |
| mesa_plateau_stone       | 38  | 0.62%  | bamboo_jungle         | 168 | 0.64%  |
| sunflower_plains         | 129 | 0.67%  | mega_taiga            | 32  | 0.69%  |
| flower_forest            | 132 | 0.69%  | redwood_taiga_mutated | 160 | 0.71%  |
| grove                    | 178 | 0.72%  | frozen_river          | 11  | 0.83%  |
| mesa                     | 37  | 0.89%  | swamp                 | 6   | 0.98%  |
| meadow                   | 177 | 1.16%  | stone_beach           | 25  | 1.17%  |
| deep_frozen_ocean        | 50  | 1.25%  | jungle_edge           | 23  | 1.38%  |
| roofed_forest            | 29  | 1.84%  | jungle                | 21  | 2.04%  |
| warm_ocean               | 44  | 2.13%  | birch_forest_mutated  | 155 | 2.15%  |
| frozen_ocean             | 10  | 2.26%  | birch_forest          | 27  | 2.29%  |
| desert                   | 2   | 2.33%  | deep_lukewarm_ocean   | 48  | 2.37%  |
| cold_taiga               | 30  | 2.40%  | deep_cold_ocean       | 49  | 2.42%  |
| beach                    | 16  | 2.45%  | ice_plains            | 12  | 2.78%  |
| taiga                    | 5   | 3.40%  | deep_ocean            | 24  | 3.60%  |
| savanna                  | 35  | 3.91%  | lukewarm_ocean        | 45  | 4.55%  |
| cold_ocean               | 46  | 4.59%  | river                 | 7   | 6.22%  |
| ocean                    | 0   | 6.87%  | plains                | 1   | 10.69% |
| forest                   | 4   | 12.31% | dripstone_caves       | 174 | -      |
| lush_caves               | 175 | -      | deep_dark             | 183 | -      |

> **Note**: Rarity based on surface Y=200 sampling. Underground biomes (dripstone_caves, lush_caves, deep_dark, sulfur_caves) are not included in rarity sorting, default rarity is 1.

> **Warning**: `sulfur_caves` (Sulfur Caves) is a new biome added in MC 1.26+. cubiomes library does not support this biome. Avoid using sulfur_caves samples for cracking.

> **Note**: Biome names on ChunkBase and similar sites follow Java Edition naming, which differs from Bedrock. For example: Java's `stony_shore` is `stone_beach` in Bedrock, Java's `dark_forest` is `roofed_forest` in Bedrock. Please note the distinction when verifying.

---

## Complete Workflow

### Windows (GUI)

1. Run the GUI application (see [MCBEseedcracker_win_ui/README.md](MCBEseedcracker_win_ui/README.md))
2. Add structures → Start Low 32-bit cracking
3. Add biomes → Start High 32-bit cracking
4. Verify seed on [ChunkBase](https://www.chunkbase.com/apps/seed-map)

### Linux (Command Line)

1. Edit `crack_low32.py` → Add structures → Run
2. Edit `crack_high32.py` → Add biomes → Run
3. Verify seed on [ChunkBase](https://www.chunkbase.com/apps/seed-map)

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
3. **Improper sampling height** - Recommend Y >= 200 to avoid underground biome interference (some underground biomes can extend above Y=150)
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

## Performance Reference

Test device: Intel Core i5-2500K @ 3.30GHz, 4 cores

| Cracker     | Speed  | Estimated Time (2^32) |
| ----------- | ------ | --------------------- |
| Low 32-bit  | ~3M/s  | ~24 minutes           |
| High 32-bit | ~70K/s | ~17 hours             |

---

## Related Links & References

- [Windows GUI Version](MCBEseedcracker_win_ui/README.md)
- [Linux Command Line Version](MCBEseedcracker_linux/README.md)
- [cubiomes](https://github.com/Cubitect/cubiomes) - Minecraft biome generation simulation library, used for biome calculation in high 32-bit cracking; integrated [Praveenkumar801's fork](https://github.com/Praveenkumar801/cubiomes) for 1.21.5+ biome generation support
- [Mersenne Twister (MT19937)](https://en.wikipedia.org/wiki/Mersenne_Twister) - Random number generator used in low 32-bit cracking for structure offset calculation

---

## License

This project is for learning and research purposes only.

---

Most of the code in this project was completed with AI assistance. I am mainly responsible for design concepts and testing verification.
