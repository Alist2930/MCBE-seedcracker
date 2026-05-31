# MCBE Seed Cracker UI

English | [简体中文](README_CN.md)

Windows desktop application with graphical interface, no command line required.

---

## Features

- ✅ **Graphical Interface** - Intuitive Windows desktop app
- ✅ **Low 32-bit Cracking** - Crack seed low 32 bits using structure coordinates
- ✅ **High 32-bit Cracking** - Crack seed high 32 bits using biome samples
- ✅ **Progress Save/Restore** - Resume cracking after interruption
- ✅ **Chinese/English Support** - Bilingual interface
- ✅ **Multi-version Support** - MC 1.18/1.19/1.20/1.21
- ✅ **Structure Icons** - Display icons for structure types
- ✅ **Biome Colors** - Display colors for biome types

---

## Installation

### Option 1: Get Executable from Releases (Recommended)

See [Releases](../../releases) for the latest version. Extract and run `MCBE Seed Cracker.exe`.

### Option 2: Run from Source

```bash
# Install dependencies
pip install PyQt5

# Run program
python main.py
```

---

## Usage

### 1. Low 32-bit Cracking (Structures)

1. Collect structure coordinates in-game (recommend 5 different structure types)
2. Click "Add Structure" button, enter structure type and coordinates
3. Select cracking range (test mode 0~100M or full mode 0~4.3B)
4. Click "Start Cracking"
5. Wait for completion, view candidate low 32-bit values

**Supported Structures:**

| Structure Type   | Description      | Spread Type |
| ---------------- | ---------------- | ----------- |
| desert_temple    | Desert Temple    | linear      |
| swamp_hut        | Witch Hut        | linear      |
| jungle_temple    | Jungle Temple    | linear      |
| shipwreck        | Shipwreck        | linear      |
| ocean_ruins      | Ocean Ruins      | linear      |
| igloo            | Igloo            | linear      |
| ocean_monument   | Ocean Monument   | triangular  |
| end_city         | End City         | triangular  |
| village          | Village          | triangular  |
| mansion          | Woodland Mansion | triangular  |
| ancient_city     | Ancient City     | triangular  |
| pillager_outpost | Pillager Outpost | triangular  |
| nether_fortress  | Nether Fortress  | linear      |
| bastion_remnant  | Bastion Remnant  | linear      |

> **Tip**: Prioritize linear type structures (Desert Temple, Witch Hut), less computation and faster cracking.

### 2. High 32-bit Cracking (Biomes)

1. Collect biome sample coordinates in-game (recommend 5 different biomes)
2. Select MC version (1.18/1.19/1.20/1.21)
3. Click "Add Biome" button, enter coordinates and biome type
4. Enter low 32-bit value (from low 32-bit cracking result)
5. Click "Start Cracking"
6. Wait for completion, view complete seed

**Sampling Tips:**

- Sampling height Y >= 200 recommended (avoid underground biome interference)
- Rare biomes (Cherry Grove, Pale Garden) work better
- Avoid common biomes (Plains, Ocean)
- **Choose coordinates at biome centers**, at least 3 blocks away from biome boundaries

### 3. Verify Seed

After cracking, verify the seed on [ChunkBase](https://www.chunkbase.com/apps/seed-map).

> **Note**: Biome names on ChunkBase follow Java Edition naming, which differs from Bedrock. For example: Java's `stony_shore` is `stone_beach` in Bedrock, Java's `dark_forest` is `roofed_forest` in Bedrock. Please note the distinction when verifying.

---

## Performance Reference

| Cracker     | Speed  | Estimated Time (2^32) |
| ----------- | ------ | --------------------- |
| Low 32-bit  | ~3M/s  | ~24 minutes           |
| High 32-bit | ~70K/s | ~17 hours             |

---

## Project Structure

```
MCBEseedcracker_win_ui/
├── main.py                  # Main entry point
├── ui/
│   ├── main_window.py       # Main window
│   ├── widgets/             # Custom widgets
│   │   ├── biome_list_widget.py
│   │   ├── structure_list_widget.py
│   │   └── progress_widget.py
│   ├── workers/             # Background tasks
│   │   ├── low32_worker.py
│   │   └── high32_worker.py
│   ├── utils/               # Utility functions
│   │   ├── crack_engine.py
│   │   ├── crack_high32_engine.py
│   │   ├── i18n.py
│   │   └── ...
│   ├── data/                # Data files
│   │   ├── biomes.json
│   │   └── structures.json
│   └── resources/           # Resource files
│       └── translations/    # Translation files
├── dll/                     # Pre-compiled DLLs
│   ├── crack_low32/
│   └── crack_high32/
├── build.spec               # PyInstaller config
└── requirements.txt         # Python dependencies
```

---

## Building

To build executable yourself:

```bash
# Install dependencies
pip install PyQt5 pyinstaller

# Build
pyinstaller build.spec --noconfirm
```

Build output is in `dist/MCBE Seed Cracker/` directory.

---

## Version Compatibility

### ⚠️ Important Limitation

**High 32-bit cracking is based on cubiomes library, which only supports up to Java 1.21.3 and stopped updating after November 2024.**

| cubiomes Info  | Details                   |
| -------------- | ------------------------- |
| Latest Version | 4.1.2                     |
| Last Update    | November 10, 2024         |
| Max Supported  | Java 1.21.3 (Pale Garden) |

**cubiomes Update Status:**

- cubiomes **stopped updating** after releasing 4.1.2 in November 2024
- Does not support Java 1.22+ or Bedrock 1.22+
- Does not support Minecraft versions from 2025 onwards

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
- **New Version Differences**: Bedrock 1.26.x has significant differences from Java 1.21 biome algorithms

**Recommendation**: Use Bedrock 1.21.0, closest to cubiomes-supported Java 1.21 biome algorithms.

---

## FAQ

### Low 32-bit Cracking Failed

**Possible causes:**

1. Incorrect structure coordinates
2. Insufficient structures (recommend at least 5)
3. Poor structure type selection (prioritize linear types)

**Solutions:**

- Verify coordinates are correct
- Add more structures
- Change structure types

### High 32-bit Cracking Failed

**Possible causes:**

1. Incorrect low 32-bit value
2. Incorrect biome sample coordinates or IDs
3. Improper sampling height (recommend Y >= 200)
4. Version incompatibility (Bedrock 1.26.x vs Java 1.21 differences)

**Solutions:**

- Confirm low 32-bit value is correct
- Verify biome samples
- Increase sampling height
- Use Bedrock 1.21.0 version

---

## Related Links

- [cubiomes Library](https://github.com/Cubitect/cubiomes)

---

## License

This project is for learning and research purposes only.