# MCBEseedcracker (Linux)

English | [简体中文](README_CN.md)

Minecraft Bedrock Edition Seed Cracker - Linux Command Line Version

> For Windows GUI version, see [MCBEseedcracker_win_ui](../MCBEseedcracker_win_ui/README.md)

---

## Requirements

- **OS**: Linux (x86_64)
- **Python**: 3.6+
- **Game Version**: 1.18/1.19/1.20/1.21/26.XX (sub-version support)

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
python3 crack_high32.py --start 0 --end 1000000000  # Custom range
```

---

## Low 32-bit Cracker

Crack the low 32 bits of the seed using structure locations.

### GPU Acceleration (OpenCL)

**Automatically detects and uses GPU if available, with automatic fallback to CPU.**

| Feature             | GPU Mode       | CPU Mode     |
| ------------------- | -------------- | ------------ |
| **Speed**           | ~150M seeds/s  | ~10M seeds/s |
| **Full Range Time** | ~30 seconds    | ~7 minutes   |
| **Speedup**         | **15x faster** | Baseline     |

**GPU Requirements:**

- NVIDIA GPU with Compute Capability 2.0+ (Fermi architecture or newer)
- AMD GPU with OpenCL 1.1+ support
- **Recommended**: RTX 20/30/40 series for best performance

**Old GPU Behavior:**

- GPUs with <10 compute units (e.g., MX330, GTX 550 Ti) are automatically detected and will use CPU mode
- This prevents timeout/crash issues on low-end GPUs

### Command Line Arguments

| Argument  | Description                                          |
| --------- | ---------------------------------------------------- |
| `--start` | Start low32 value (default: 0)                       |
| `--end`   | End low32 value (default: 2^32-1)                    |
| `--test`  | Test mode (0 - 100M)                                 |
| `--cpu`   | Force CPU mode                                       |
| `--gpu`   | Force GPU mode (auto-fallback to CPU if unavailable) |

### GPU Configuration

Edit `crack_config.json` to customize GPU behavior:

```json
{
  "use_gpu": true,
  "auto_fallback": true,
  "seeds_per_thread": 256,
  "max_results": 10000
}
```

| Setting            | Description                                            |
| ------------------ | ------------------------------------------------------ |
| `use_gpu`          | Enable/disable GPU acceleration (default: true)        |
| `auto_fallback`    | Auto-fallback to CPU if GPU fails (default: true)      |
| `seeds_per_thread` | Seeds per GPU thread (auto-adjusted by GPU capability) |
| `max_results`      | Maximum results to store (default: 10000)              |

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

Edit the beginning of `crack_high32.py` to configure low32 value, MC version, and biome samples:

```python
# Biome samples (recommended: 5, each sample includes X, Z, Y coordinates and biome ID)
SAMPLES = [
    (-1922, 1231, 200, 185),   # cherry_grove
    (-4706, 3302, 200, 132),   # flower_forest
    (-935, 2592, 200, 5),      # taiga
    (-2697, 1363, 200, 4),     # forest
    (-270, 470, 200, 186),     # pale_garden
]

# Low 32-bit value (from crack_low32 result)
LOW32 = 1818588773

# MC version (sub-version support)
MC_VERSION_STR = "26.30+"  # See version mapping table below
```

> **Note**:
>
> - Sample format: `(x, z, y, biome_id)`
> - Surface sampling recommended `Y>=200`, avoid underground biome interference
> - Cave biomes (e.g., Sulfur Caves) require low Y coordinates (`Y≤60`)
> - High 32-bit cracker only supports CPU mode (multiprocessing), no GPU acceleration

#### Version Mapping

| Bedrock Version   | MC_VERSION_STR Value | Supported Biomes                                |
| ----------------- | -------------------- | ----------------------------------------------- |
| **26.30+**        | `"26.30+"`           | ✅ Sulfur Caves (new cave biome)                |
| **1.21.60-26.23** | `"1.21.60-26.23"`    | ✅ Pale Garden (expanded range)                 |
| **1.21.50**       | `"1.21.50"`          | ✅ Pale Garden (smaller range)                  |
| **1.21-1.21.40**  | `"1.21-1.21.40"`     | ❌ No Pale Garden                               |
| **1.20.60-81**    | `"1.20.60-81"`       | ✅ Cherry Grove                                 |
| **1.20.0-51**     | `"1.20.0-51"`        | ✅ Cherry Grove                                 |
| **1.19**          | `"1.19"`             | ✅ Deep Dark, Mangrove Swamp                    |
| **1.18**          | `"1.18"`             | ✅ Dripstone Caves, Lush Caves, Mountain biomes |

#### Pale Garden Version Differences

⚠️ **Important**: Pale Garden generation range differs between versions:

| MC Version        | Pale Garden Generation                    |
| ----------------- | ----------------------------------------- |
| **1.21-1.21.40**  | ❌ Doesn't exist, position is Dark Forest |
| **1.21.50**       | ⚠️ Exists but smaller range               |
| **1.21.60-26.23** | ✅ Expanded generation range              |

**Latest version (Bedrock 26.30+)**:

- Corresponds to Java 26.2 (Chaos Cubed Drop)
- New biome: Sulfur Caves (ID: 187)
- Requires low Y coordinate (Y≤60) for cave biome cracking
- Recommended: Use surface biomes for cracking (rarity data available)

**Version 1.21.60-26.23**:

- Corresponds to Java 1.21.5-26.1
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

#### Important Limitation

**High 32-bit cracking is based on cubiomes library, which supports up to Java 1.21.11 (via community fork).**

| cubiomes Info  | Details                                  |
| -------------- | ---------------------------------------- |
| Latest Version | 4.1.2 (fork)                             |
| Last Update    | January 2025 (fork)                      |
| Max Supported  | Java 1.21.5-26.1 (Bedrock 1.21.60-26.23) |

**cubiomes Update Status:**

- Official cubiomes stopped updating after November 2024
- Integrated SeedMapper's cubiomes fork for 1.21.5+ and 26.2+ support
- Supports Pale Garden (1.21.50+) and Sulfur Caves (26.30+)

> **Important**: Biome samples must use **Overworld** biomes only. Do not use biomes from the Nether or End.

### Overworld Biome ID Reference (1.21.60-26.23)

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
| sulfur_caves             | 187 | -      |                       |     |        |

> **Note**: Rarity based on surface Y=200 sampling. Underground biomes (dripstone_caves, lush_caves, deep_dark, sulfur_caves) are not included in rarity sorting, default rarity is 1.

> **Note**: Sulfur Caves (ID: 187) is now supported for cracking. Use low Y coordinate (Y≤60) for accurate detection. Cave biomes are not recommended for primary cracking due to lack of rarity data.

> **Note**: Biome names on ChunkBase and similar sites follow Java Edition naming, which differs from Bedrock. For example: Java's `stony_shore` is `stone_beach` in Bedrock, Java's `dark_forest` is `roofed_forest` in Bedrock. Please note the distinction when verifying.

### Biome Sample Selection Tips

- **Choose coordinates at biome centers**, at least 3 blocks away from biome boundaries
- **Avoid sampling near biome boundaries**
- If cracking fails, try different coordinates within the same biome

---

## Building

Pre-compiled library files are included. To build yourself:

### CPU Version

```bash
# Install dependencies
sudo apt install -y gcc libomp-dev  # Debian/Ubuntu
sudo dnf install -y gcc libgomp-devel  # Fedora/RHEL

# Build
chmod +x build.sh
./build.sh
```

### GPU Version (OpenCL)

**For GPU acceleration, install OpenCL development packages:**

```bash
# Ubuntu/Debian
sudo apt install -y ocl-icd-opencl-dev ocl-icd-libopencl1

# Fedora/RHEL
sudo dnf install -y ocl-icd-devel

# Arch Linux
sudo pacman -S ocl-icd
```

**For NVIDIA GPUs:**

```bash
# Ensure NVIDIA driver is installed
nvidia-smi  # Check GPU status

# If OpenCL is not detected, manually configure:
sudo mkdir -p /etc/OpenCL/vendors
echo "libnvidia-opencl.so.1" | sudo tee /etc/OpenCL/vendors/nvidia.icd
```

Then rebuild with GPU support:

```bash
chmod +x build.sh
./build.sh
# Should see: [OK] crack_low32_opencl.so created
```

---

## Performance Reference

Test Environment: Intel Xeon Gold 6330 (112 cores) + NVIDIA RTX 3090

| Cracker     | Mode | Speed   | Est. Time (2^32) | Notes               |
| ----------- | ---- | ------- | ---------------- | ------------------- |
| Low 32-bit  | GPU  | ~156M/s | **~30 seconds**  | RTX 3090 OpenCL     |
| Low 32-bit  | CPU  | ~12M/s  | ~6 minutes       | 112 cores parallel  |
| High 32-bit | CPU  | ~250K/s | ~5 hours         | 32 processes (auto) |

**Note**: Old GPUs (compute units < 10) automatically use CPU mode for stability.

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

- [cubiomes](https://github.com/Cubitect/cubiomes) - Minecraft biome generation simulation library, used for biome calculation in high 32-bit cracking; integrated [SeedMapper's fork](https://github.com/xpple/SeedMapper) for 1.21.5+ and 26.2+ biome generation support
- [Mersenne Twister (MT19937)](https://en.wikipedia.org/wiki/Mersenne_Twister) - Random number generator used in low 32-bit cracking for structure offset calculation

---

## License

This project is for learning and research purposes only.
