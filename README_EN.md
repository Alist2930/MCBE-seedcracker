# MCBEseedcracker

English | [简体中文](README.md)

Minecraft Bedrock Edition Seed Cracker (Windows / Linux)

> I'm a Minecraft newbie. Most of this code was written by AI, and I'm mainly responsible for testing and feature requests. Feedback and corrections are welcome.
>
> For Java Edition seed cracking, I recommend [SeedcrackerX](https://github.com/19MisterX98/SeedcrackerX). As for Bedrock Edition, I've always wanted a similar tool, but no one has made one yet. While my implementation may not be the best, someone has to start somewhere.
>
> **Project Status**: Work in progress, currently for personal use. Feedback and suggestions are welcome.

---

## Features

Reverse-engineer world seeds using structure locations and biome samples from servers.

---

## Requirements

- **OS**: Windows 10+ or Linux (x86_64)
- **Python 3.8+**
- **Game Version**: 1.21+ (recommended), also supports 1.18/1.19/1.20 (please report issues)

> **Version Notes**:
>
> - **Low 32-bit cracking (structure locating)**: No version compatibility issues. The structure generation algorithm's dependency on the low 32 bits is stable. Note that if a structure generated in an older version no longer meets the generation conditions after a biome update, it may not exist in the newer version, but this doesn't affect the cracking process logically—because we're cracking the seed at the time of structure generation, not the structure's existence in the current version.
> - **High 32-bit cracking (biomes)**: Version compatibility has been handled (based on cubiomes library). Please report any issues.

---

## Directory Structure

```
MCBEseedcracker/           # Windows version
├── build.bat              # Build script
├── crack_low32/
│   ├── crack_low32.dll
│   ├── crack_low32.c
│   └── crack_low32.py
└── crack_high32/
    ├── crack_high32.dll
    ├── crack_high32.c
    ├── crack_high32.py
    └── cubiomes/

MCBEseedcracker_linux/     # Linux version
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

---

## Usage

### Low 32-bit Cracker

Crack the low 32 bits of the seed using structure locations.

**Principle:**

Minecraft Bedrock uses 64-bit integers as world seeds. When generating structures, the system calculates a "region seed" based on region coordinates and the seed, then uses the MT19937 random number generator to determine the structure's offset within the region.

**Region Seed Calculation:**

```
Region coords: rx = chunk_x / spacing, rz = chunk_z / spacing
Region seed: r_base = (rx × 2570712328 + rz × 4048968661 + salt) & 0xFFFFFFFF
Actual seed: r_seed = world_seed_low32 + r_base
```

Where `salt` is a constant specific to each structure type, for example:

- Desert Temple: 14357617
- Ocean Monument: 10387313
- Shipwreck: 165745295

**Structure Generation Parameters:**

Each structure has two key parameters:

- **spacing**: The side length of structure generation regions, in chunks. The world is divided into `spacing × spacing` region grids, with at most one structure per region.
- **separation**: The minimum distance between structures, in chunks. This determines the possible offset range within a region.

Offset range: `offset_range = spacing - separation`

For example, Desert Temple has `spacing=32`, `separation=8`, so the offset range is `32-8=24` chunks.

**Structure Offset Calculation:**

Using MT19937 to generate random numbers, offsets are calculated based on distribution type:

- **Linear mode**: `offset_x = temper(mt[0]) % offset_range`
- **Triangular mode**: `offset_x = (temper(mt[0]) % range + temper(mt[1]) % range) / 2`

**Cracking Method:**

Iterate through all possible low 32-bit values (0 ~ 2³²-1, about 4.3 billion). For each candidate:

1. Calculate region seed `r_seed = w + r_base`
2. Initialize MT19937 and generate offset values
3. Check if offsets match actual structure positions

Multiple structures matching simultaneously can greatly narrow down candidates, typically completing within half an hour.

```bash
# Windows
cd MCBEseedcracker/crack_low32
python crack_low32.py                    # Full crack (0 ~ 2^32-1)
python crack_low32.py --test             # Test mode (0 ~ 100M)
python crack_low32.py --start 1000 --end 2000  # Custom range

# Linux
cd MCBEseedcracker_linux/crack_low32
python3 crack_low32.py
```

**Command Line Arguments:**

| Argument  | Description                       |
| --------- | --------------------------------- |
| `--start` | Start low32 value (default: 0)    |
| `--end`   | End low32 value (default: 2^32-1) |
| `--test`  | Test mode (0 ~ 100M)              |

**Configure Target Structures:**

Edit `TARGETS` at the beginning of `crack_low32.py` (recommended: 5 structures):

```python
# Example: structure coordinates for seed 1818588773
TARGETS = [
    {"structure": "swamp_hut", "x": 2136, "z": -1176},
    {"structure": "jungle_temple", "x": -360, "z": -248},
    {"structure": "desert_temple", "x": -936, "z": 4744},
    {"structure": "ocean_monument", "x": 792, "z": -792},
    {"structure": "end_city", "x": 1352, "z": -1208},
]
```

**Supported Structures:**

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

> **💡 Tip**: Prioritize finding **linear** type structures (such as Desert Temple, Witch Hut, Jungle Temple, Shipwreck, etc.). The program automatically sorts linear types first for processing, requiring less computation and faster cracking speed.

**Chunk Location Method:**

- **Desert Temple**: Chunk containing the center position
- **Ocean Monument**: Chunk containing the center position
- **Witch Hut**: Chunk with the largest building area
- **Jungle Temple**: Chunk with the largest building area
- **End City**: Chunk with the largest area of the entrance shulker box structure
- **Shipwreck**: For complete shipwrecks, use the chunk containing the bow (the bow is roughly at the chunk boundary); for incomplete shipwrecks, use the chunk with the largest ship area

### High 32-bit Cracker

Crack the high 32 bits of the seed using biome samples.

**Principle:**

After determining the low 32 bits, the high 32 bits are needed to get the complete seed. Biome generation depends on the complete 64-bit seed, calculating biome types at each coordinate through multi-layer noise functions.

**Why Use cubiomes Library:**

This project uses the [cubiomes](https://github.com/Cubitect/cubiomes) library for biome calculation. This is a C library specifically designed to simulate Minecraft Java Edition biome generation.

Starting from version 1.18, Minecraft Java and Bedrock Edition terrain generation algorithms are basically unified, both using the same noise functions and climate parameter system (temperature, humidity, continentalness, erosion, depth, weirdness). The only difference is that Bedrock Edition applies Voronoi perturbation to coordinates before biome sampling, which this tool has handled. Therefore, the cubiomes library can be directly used to calculate Bedrock Edition biomes without reimplementing complex noise generation algorithms.

**Biome Generation Process (1.18+):**

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

**Bedrock Edition Special Handling:**

Bedrock Edition applies Voronoi perturbation to coordinates before biome calculation:

```
sha256_hash = SHA256(seed)
voronoi_offset = voronoiAccess3D(sha256_hash, x, y, z)
actual_sampling_coords = (x + voronoi_x, y + voronoi_y, z + voronoi_z)
```

**Cracking Method:**

Iterate through all possible high 32-bit values (0 ~ 2³²-1). For each candidate seed:

1. Calculate complete 64-bit seed: `seed = (high32 << 32) | low32`
2. Initialize noise generator
3. Calculate biome ID for each sample coordinate
4. Compare with actual collected biome samples

Due to the need for complete iteration and complex biome calculations, this takes a long time, usually several hours.

```bash
# Windows
cd MCBEseedcracker/crack_high32
python crack_high32.py                         # Full crack (0 ~ 2^32-1)
python crack_high32.py --test                  # Test mode (0 ~ 100M)
python crack_high32.py --start 1000 --end 2000 # Custom range
python crack_high32.py --low32 1818588773      # Specify low32 value

# Linux
cd MCBEseedcracker_linux/crack_high32
python3 crack_high32.py
```

**Command Line Arguments:**

| Argument      | Description                              |
| ------------- | ---------------------------------------- |
| `--start`     | Start high32 value (default: 0)          |
| `--end`       | End high32 value (default: 2^32-1)       |
| `--test`      | Test mode (0 ~ 100M)                     |
| `--low32`     | Low 32-bit value                         |
| `--processes` | Number of processes (default: CPU cores) |

**Automatic Rarity Sorting:**

The program automatically sorts samples by biome rarity. The rarest biome is used for Phase 1 filtering, greatly improving efficiency:

```
[*] Biome samples (sorted by rarity, rarest first):
    1. (-270, 470) -> pale_garden (ID: 186, 0.0724%)
    2. (-1922, 1231) -> cherry_grove (ID: 185, 0.2552%)
    3. (-4706, 3302) -> flower_forest (ID: 132, 0.6488%)
    ...
```

**Configuration:**

Edit the beginning of `crack_high32.py`:

```python
# Low 32-bit value (from crack_low32 result)
LOW32 = 1818588773

# MC version
MC_VERSION_STR = "1.21"  # Options: "1.18", "1.19", "1.20", "1.21"

# Example: biome samples for seed 18998457957 (low32 is 1818588773)
SAMPLES = [
    (-1922, 1231, 185),   # cherry_grove
    (-4706, 3302, 132),   # flower_forest
    (-935, 2592, 5),      # taiga
    (-2697, 1363, 4),     # forest
    (-270, 470, 186),     # pale_garden
]

Y_COORD = 150  # Sampling height (surface recommended Y>=150)
```

> **⚠️ Important**: Biome samples must use **Overworld** biomes only. Do not use biomes from the Nether, End, or other dimensions. This tool is based on Overworld biome generation algorithms; biomes from other dimensions cannot be used for cracking.

---

## Complete Workflow

1. **Collect structure coordinates** - Get building coordinates from target world (recommended: 5)
2. **Run low 32-bit cracking** - Get candidate low 32-bit values
3. **Collect biome samples** - Get biome IDs from different locations (recommended: 5)
4. **Run high 32-bit cracking** - Get complete seed
5. **Verify** - Use [ChunkBase](https://www.chunkbase.com/apps/seed-map) to verify seed

---

## FAQ

### Low 32-bit cracking failed (no matching seeds found)

**Possible causes:**

1. **Incorrect structure coordinates** - Coordinates are wrong, or chunk location method is incorrect
2. **Insufficient structures** - Recommend at least 5 different structure types
3. **Poor structure type selection** - Some structures (like villages) have complex generation rules. Recommended:
   - Desert Temple, Witch Hut, Jungle Temple (simple and stable generation rules)
   - Ocean Monument, End City
4. **Version incompatibility** - If the target world was generated in an older version, structure positions may differ from current version

**Solutions:**

- Verify coordinates are correct
- Add more structures
- Change structure types
- Confirm the target world's generation version

### High 32-bit cracking failed (no matching seeds found)

**Possible causes:**

1. **Incorrect low 32-bit value** - Low 32-bit cracking result is wrong
2. **Incorrect biome samples** - Coordinates or biome IDs are wrong
3. **Improper sampling height** - Recommend Y >= 150 to avoid underground biome interference
4. **Insufficient biome samples** - Recommend at least 5 samples
5. **Poor sample selection** - Should choose rare biomes (like Cherry Grove, Pale Garden), avoid common biomes (like Plains, Ocean)

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

## Biome ID Reference

| Biome           | ID  | Rarity | Biome          | ID  | Rarity |
| --------------- | --- | ------ | -------------- | --- | ------ |
| pale_garden     | 186 | 0.07%  | cherry_grove   | 185 | 0.26%  |
| flower_forest   | 132 | 0.65%  | ice_spikes     | 140 | 0.88%  |
| badlands        | 37  | 1.05%  | jungle         | 21  | 1.47%  |
| desert          | 2   | 1.47%  | dark_forest    | 29  | 2.42%  |
| taiga           | 5   | 3.48%  | swamp          | 6   | 4.29%  |
| deep_ocean      | 24  | 5.67%  | forest         | 4   | 11.57% |
| plains          | 1   | 10.47% | ocean          | 0   | 8.38%  |
| meadow          | 177 | -      | mangrove_swamp | 184 | -      |
| dripstone_caves | 174 | -      | lush_caves     | 175 | -      |
| deep_dark       | 183 | -      |                |     |        |

> **Note**: Rarity is based on surface Y=150 sampling statistics. Underground biomes (dripstone_caves, lush_caves, deep_dark) are not included in rarity sorting.

See the `BIOME_IDS` dictionary at the beginning of `crack_high32.py` for the complete list with IDs and rarity information.

---

## Version Compatibility

The program checks biome sample compatibility with MC version:

```
[!] Warning: Some biomes are not available in MC 1.18:
  (-1922, 1231) -> cherry_grove (ID: 185) requires 1.20+
```

| Version | New Biomes                                   |
| ------- | -------------------------------------------- |
| 1.18    | dripstone_caves, lush_caves, mountain biomes |
| 1.19    | deep_dark, mangrove_swamp                    |
| 1.20    | cherry_grove                                 |
| 1.21    | pale_garden                                  |

---

## Building (Optional)

Pre-compiled library files are included in the project and can be used directly. To build yourself:

### Windows

Install [MinGW-w64](https://www.mingw-w64.org/) and ensure `gcc` is in PATH.

```bash
cd MCBEseedcracker
build.bat
```

### Linux

```bash
# Install dependencies
sudo apt install -y gcc libomp-dev  # Debian/Ubuntu
sudo dnf install -y gcc libgomp-devel  # Fedora/RHEL

# Build
cd MCBEseedcracker_linux
chmod +x build.sh
./build.sh
```

---

## Performance Reference

| Cracker     | Speed  | Estimated Time (2^32) |
| ----------- | ------ | --------------------- |
| Low 32-bit  | ~3M/s  | ~24 minutes           |
| High 32-bit | ~70K/s | ~17 hours             |

Test environment: Windows 10, Intel Core i5-2500K @ 3.30GHz (4 cores)

> **💡 Tip**: Low 32-bit cracking speed is affected by structure types. Using linear type structures (such as Desert Temple, Witch Hut, etc.) is faster.

---

## References

- [ChunkBase Seed Map](https://www.chunkbase.com/apps/seed-map)
- [SodaMC Seed Map](https://sodamc.com/tools/Seed_Map.htm)
- [cubiomes](https://github.com/Cubitect/cubiomes)

---

## Future Plans

- [ ] **Code improvement** - Improve code, optimize performance, fix bugs
- [ ] **CUDA acceleration** - Use GPU parallel computing, expected 10-100x performance boost
- [ ] **Automatic biome recognition** - Automatically identify biome types and coordinates in-game
- [ ] **Earlier version support** - Support biome generation algorithms for 1.17 and earlier

---

## Minecraft Seed Science [Reference: https://www.bilibili.com/video/BV1r1N3ezEXU/]

### Seed Value Range

Minecraft uses 64-bit integers as world seeds, range: `-2⁶³ ~ 2⁶³-1` (approximately -922 quintillion ~ 922 quintillion).

### Seed Input Rules

**1. No seed input**

The system randomly generates a seed within the 64-bit range.

**2. Number input**

- If the number is within `-2⁶³ ~ 2⁶³-1` range, it's used directly as the seed
- If the number exceeds the range, it's treated as a string

**3. String input**

Strings are converted to numeric seeds using the formula:

```
seed = Σ(Unicode(char_i) × 31^(length-i))
```

For example:

- `"d"` → Unicode=100 → seed=100
- `"dd"` → 31×100 + 100 = 3200

The result is truncated to 32-bit integer range (`-2³¹ ~ 2³¹-1`).

### Why Two-Step Cracking?

The 64-bit seed space is too large (about 1.8×10¹⁹ possibilities), making direct iteration impractical.

However, the structure generation algorithm only depends on the low 32 bits of the seed, so:

1. **Low 32 bits**: Quickly narrow down through structure positions (about 4.3 billion possibilities)
2. **High 32 bits**: Precisely locate through biome samples (about 4.3 billion possibilities)

Combining both steps breaks the problem into two manageable sub-problems.

---

## License

This project is for learning and research purposes only.

---

## Acknowledgments

Most of the code in this project was completed with AI assistance. I'm mainly responsible for design concepts and testing verification.
