# MCBEseedcracker

[English](README_EN.md) | 简体中文

Minecraft 基岩版种子破解器 (Windows / Linux)

> 作者是个MC小白，这个工具大部分代码是AI写的，我只是负责测试和提需求。如有问题欢迎指正。
>
> Java 版种子破解器推荐使用 [SeedcrackerX](https://github.com/19MisterX98/SeedcrackerX)。至于基岩版，我一直想要一个类似的工具，但至今没人做。虽然我这个实现可能不是最好的，但总得有人开头。
>
> **项目状态**：半成品，目前仅自用。欢迎反馈问题和建议。

---

## 功能

通过服务器上的建筑位置和群系位置，反推出世界的种子。

---

## 环境要求

- **操作系统**：Windows 10+ 或 Linux (x86_64)
- **Python 3.8+**
- **游戏版本**：1.21+（推荐），也支持 1.18/1.19/1.20（如有问题请反馈）

> **版本说明**：
>
> - **低32位破解（结构定位）**：无版本兼容问题。结构生成算法对低32位的依赖是稳定的。需要注意的是，如果低版本生成的结构在高版本群系更新后不再满足该结构的生成条件，该结构可能在高版本中不存在，但这在逻辑上不影响破解流程——因为破解的是结构生成时的种子，而非当前版本的结构存在性。
> - **高32位破解（群系）**：已做版本兼容处理（基于cubiomes工具），如有问题请反馈。

---

## 目录结构

```
MCBEseedcracker/           # Windows版
├── build.bat              # 编译脚本
├── crack_low32/
│   ├── crack_low32.dll
│   ├── crack_low32.c
│   └── crack_low32.py
└── crack_high32/
    ├── crack_high32.dll
    ├── crack_high32.c
    ├── crack_high32.py
    └── cubiomes/

MCBEseedcracker_linux/     # Linux版
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

## 使用方法

### 低32位破解器

通过结构位置破解种子的低32位。

**原理：**

Minecraft基岩版使用64位整数作为世界种子。结构生成时，系统会根据区域坐标和种子计算"区域种子"（region seed），然后使用MT19937随机数生成器确定结构在区域内的偏移位置。

**区域种子计算公式：**

```
区域坐标: rx = 区块x / spacing, rz = 区块z / spacing
区域种子: r_base = (rx × 2570712328 + rz × 4048968661 + salt) & 0xFFFFFFFF
实际种子: r_seed = 世界种子低32位 + r_base
```

其中 `salt` 是每种结构特有的常数，例如：

- 沙漠神殿: 14357617
- 海底神殿: 10387313
- 沉船: 165745295

**结构生成参数：**

每种结构有两个关键参数：

- **spacing（区域大小）**：结构生成区域的边长，以区块为单位。世界被划分为 `spacing × spacing` 的区域网格，每个区域最多生成一个结构。
- **separation（最小间距）**：结构之间的最小距离，以区块为单位。这决定了结构在区域内可能的偏移范围。

偏移范围：`offset_range = spacing - separation`

例如，沙漠神殿的 `spacing=32`，`separation=8`，所以偏移范围为 `32-8=24` 区块。

**结构偏移计算：**

使用MT19937生成随机数，根据分布类型计算偏移：

- **Linear模式**：`offset_x = temper(mt[0]) % offset_range`
- **Triangular模式**：`offset_x = (temper(mt[0]) % range + temper(mt[1]) % range) / 2`

**破解方法：**

遍历低32位的所有可能值（0 ~ 2³²-1，约43亿），对每个候选值：

1. 计算区域种子 `r_seed = w + r_base`
2. 初始化MT19937并生成偏移值
3. 检查偏移是否与实际结构位置匹配

多个结构同时匹配可大幅缩小候选范围，通常半小时内完成。

```bash
# Windows
cd MCBEseedcracker/crack_low32
python crack_low32.py                    # 完整破解 (0 ~ 2^32-1)
python crack_low32.py --test             # 测试模式 (0 ~ 100M)
python crack_low32.py --start 1000 --end 2000  # 指定范围

# Linux
cd MCBEseedcracker_linux/crack_low32
python3 crack_low32.py
```

**命令行参数：**

| 参数      | 说明                         |
| --------- | ---------------------------- |
| `--start` | 起始低32位值（默认: 0）      |
| `--end`   | 结束低32位值（默认: 2^32-1） |
| `--test`  | 测试模式（0 ~ 100M）         |

**配置目标结构：**

编辑 `crack_low32.py` 开头的 `TARGETS`（建议5个结构）：

```python
# 示例：种子 1818588773 的结构坐标
TARGETS = [
    {"structure": "swamp_hut", "x": 2136, "z": -1176},
    {"structure": "jungle_temple", "x": -360, "z": -248},
    {"structure": "desert_temple", "x": -936, "z": 4744},
    {"structure": "ocean_monument", "x": 792, "z": -792},
    {"structure": "end_city", "x": 1352, "z": -1208},
]
```

**支持的结构：**

| 英文名           | 中文名            | 分布类型   |
| ---------------- | ----------------- | ---------- |
| village          | 村庄/僵尸村庄     | triangular |
| mansion          | 林地府邸          | triangular |
| end_city         | 末地城            | triangular |
| ocean_monument   | 海底神殿          | triangular |
| ancient_city     | 远古城市          | triangular |
| ocean_ruins      | 海底废墟          | **linear** |
| shipwreck        | 沉船              | **linear** |
| nether_complexes | 下界要塞/堡垒遗迹 | **linear** |
| desert_temple    | 沙漠神殿          | **linear** |
| igloo            | 雪屋              | **linear** |
| swamp_hut        | 女巫屋            | **linear** |
| jungle_temple    | 丛林神庙          | **linear** |

坐标只要是在一个区块内都行。

> **💡 提示**：优先寻找 **linear** 类型的结构（如沙漠神殿、女巫屋、丛林神庙、沉船等）。程序会自动将 linear 类型排序优先处理，计算量更少，破解速度更快。

**结构定位区块确定方法：**

- **沙漠神殿**：中心位置所在的区块
- **海底神殿**：中心位置所在的区块
- **女巫屋**：建筑占区块面积最大的区块
- **丛林神庙**：建筑占区块面积最大的区块
- **末地城**：入口潜影贝方形结构占区块面积最大的区块
- **沉船**：完整沉船取船头所在区块（船头大概是刚好顶到区块边界的那端），残缺沉船取船占区块面积最大的区块

### 高32位破解器

通过群系样本破解种子的高32位。

**原理：**

低32位确定后，还需要确定高32位才能得到完整种子。群系生成依赖于完整的64位种子，通过多层噪声函数计算每个坐标的群系类型。

**为什么使用 cubiomes 库：**

本项目使用 [cubiomes](https://github.com/Cubitect/cubiomes) 库进行群系计算。这是一个用 C 语言编写的库，专门模拟 Minecraft Java 版的生物群系生成。

从 1.18 版本开始，Minecraft Java 版和基岩版的地形生成算法已基本统一，两者使用相同的噪声函数和气候参数系统（温度、湿度、大陆性、侵蚀、深度、怪异度）。唯一的区别是基岩版在群系采样前会对坐标进行 Voronoi 扰动，本工具已对此做了兼容处理。因此，可以直接使用 cubiomes 库来计算基岩版的群系，无需重新实现复杂的噪声生成算法。

**群系生成流程（1.18+）：**

1. **种子初始化**：使用Xoroshiro RNG初始化噪声参数
2. **气候参数计算**：计算6个气候参数
   - Temperature（温度）
   - Humidity（湿度）
   - Continentalness（大陆性）
   - Erosion（侵蚀）
   - Depth（深度）
   - Weirdness（怪异度）
3. **噪声采样**：每个参数使用DoublePerlinNoise（多层Perlin噪声叠加）
4. **群系映射**：根据气候参数组合确定群系类型

**基岩版特殊处理：**

基岩版在群系计算前会对坐标进行Voronoi扰动：

```
sha256_hash = SHA256(种子)
voronoi_offset = voronoiAccess3D(sha256_hash, x, y, z)
实际采样坐标 = (x + voronoi_x, y + voronoi_y, z + voronoi_z)
```

**破解方法：**

遍历高32位的所有可能值（0 ~ 2³²-1），对每个候选种子：

1. 计算完整64位种子：`seed = (high32 << 32) | low32`
2. 初始化噪声生成器
3. 对每个样本坐标计算群系ID
4. 与实际采集的群系样本比对

由于需要完整遍历且群系计算复杂，耗时较长，通常需要数小时。

```bash
# Windows
cd MCBEseedcracker/crack_high32
python crack_high32.py                         # 完整破解 (0 ~ 2^32-1)
python crack_high32.py --test                  # 测试模式 (0 ~ 100M)
python crack_high32.py --start 1000 --end 2000 # 指定范围
python crack_high32.py --low32 1818588773      # 指定低32位值

# Linux
cd MCBEseedcracker_linux/crack_high32
python3 crack_high32.py
```

**命令行参数：**

| 参数          | 说明                         |
| ------------- | ---------------------------- |
| `--start`     | 起始高32位值（默认: 0）      |
| `--end`       | 结束高32位值（默认: 2^32-1） |
| `--test`      | 测试模式（0 ~ 100M）         |
| `--low32`     | 低32位值                     |
| `--processes` | 进程数（默认: CPU核心数）    |

**稀有度自动排序：**

程序会自动按群系稀有度排序样本，最稀有的群系优先检查，一旦不匹配立即跳过当前种子，大幅提高效率：

```
[*] Biome samples (sorted by rarity, rarest first):
    1. (-270, 470) -> pale_garden (ID: 186, 0.0724%)
    2. (-1922, 1231) -> cherry_grove (ID: 185, 0.2552%)
    3. (-4706, 3302) -> flower_forest (ID: 132, 0.6488%)
    ...
```

**破解策略：**

对每个高32位值，按稀有度顺序依次检查所有群系样本。第一个群系不匹配则立即跳过，避免不必要的计算。

**配置参数：**

编辑 `crack_high32.py` 开头：

```python
# 低32位值（来自 crack_low32 结果）
LOW32 = 1818588773

# MC版本
MC_VERSION_STR = "1.21"  # 可选: "1.18", "1.19", "1.20", "1.21"

# 示例：种子 18998457957 （低32位是1818588773）的群系样本
SAMPLES = [
    (-1922, 1231, 185),   # cherry_grove
    (-4706, 3302, 132),   # flower_forest
    (-935, 2592, 5),      # taiga
    (-2697, 1363, 4),     # forest
    (-270, 470, 186),     # pale_garden
]

Y_COORD = 200  # 采样高度（地表建议 Y>=200，避免地下群系干扰）
```

> **⚠️ 重要**：群系样本必须使用**主世界（Overworld）**的群系，不要使用下界、末地等其他维度的群系。本工具基于主世界群系生成算法，其他维度的群系无法用于破解。

---

## 完整流程

1. **收集结构坐标** - 在目标世界获取建筑坐标（建议5个）
2. **运行低32位破解** - 得到候选的低32位值
3. **收集群系样本** - 获取不同位置的群系ID（建议5个）
4. **运行高32位破解** - 得到完整种子
5. **验证** - 使用 [ChunkBase](https://www.chunkbase.com/apps/seed-map) 验证种子

---

## 常见问题

### 低32位破解失败（没有找到匹配的种子）

**可能原因：**

1. **结构坐标错误** - 坐标填写不正确，或区块定位方法有误
2. **结构数量不足** - 建议至少提供 5 个不同类型的结构
3. **结构类型选择不当** - 某些结构（如村庄）生成规则复杂，建议优先使用：
   - 沙漠神殿、女巫屋、丛林神庙（生成规则简单稳定）
   - 海底神殿、末地城
4. **版本不兼容** - 如果目标世界是旧版本生成的，结构位置可能与当前版本不同

**解决方法：**

- 核对坐标是否正确
- 增加结构数量
- 更换结构类型
- 确认目标世界的生成版本

### 高32位破解失败（没有找到匹配的种子）

**可能原因：**

1. **低32位值错误** - 低32位破解结果不正确
2. **群系样本错误** - 坐标或群系ID填写不正确
3. **采样高度不当** - 建议 Y >= 200，避免地下群系干扰（某些地下群系可延伸至 Y=150 以上）
4. **群系样本数量不足** - 建议至少 5 个样本
5. **样本选择不当** - 应选择稀有群系（如樱花林、苍白之园），避免常见群系（如平原、海洋）

**解决方法：**

- 确认低32位值正确
- 核对群系样本坐标和ID
- 提高采样高度
- 选择稀有群系作为样本

### 破解时间过长

**低32位破解：** 正常情况下约 20-30 分钟（4核CPU）

**高32位破解：** 正常情况下约 10-20 小时（4核CPU）

如果时间明显超出：

- 检查 CPU 占用率，确认多线程正常工作
- 减少群系样本数量（但会降低准确性）
- 使用 `--test` 参数先进行小范围测试

---

## 群系ID参考

| 群系            | ID  | 稀有度 | 群系           | ID  | 稀有度 |
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

> **注**：稀有度基于地表 Y=200 采样统计。地下群系（dripstone_caves、lush_caves、deep_dark）不参与稀有度排序。

完整列表见 `crack_high32.py` 开头的 `BIOME_IDS` 字典，包含 ID 和稀有度信息。

---

## 版本兼容性

程序会检测群系样本与MC版本的兼容性：

```
[!] Warning: Some biomes are not available in MC 1.18:
  (-1922, 1231) -> cherry_grove (ID: 185) requires 1.20+
```

| 版本 | 新增群系                              |
| ---- | ------------------------------------- |
| 1.18 | dripstone_caves, lush_caves, 山地群系 |
| 1.19 | deep_dark, mangrove_swamp             |
| 1.20 | cherry_grove                          |
| 1.21 | pale_garden                           |

### 支持的版本详情

高32位破解基于 cubiomes 库，支持以下版本：

| 版本号 | 枚举值 | 说明                   |
| ------ | ------ | ---------------------- |
| 1.18   | 22     | 包含 1.18.2            |
| 1.19   | 24     | 包含 1.19.4            |
| 1.20   | 25     | 包含 1.20.6            |
| 1.21   | 28     | 最新版本 (Winter Drop) |

> **注**：目前仅支持主版本号，小版本间群系生成差异较小。如需更精确的小版本支持（如 1.19.2、1.21.3 等），欢迎提 Issue 反馈。

---

## 编译（可选）

预编译的库文件已包含在项目中，可直接使用。如需自行编译：

### Windows

需要安装 [MinGW-w64](https://www.mingw-w64.org/)，确保 `gcc` 在 PATH 中。

```bash
cd MCBEseedcracker
build.bat
```

### Linux

```bash
# 安装依赖
sudo apt install -y gcc libomp-dev  # Debian/Ubuntu
sudo dnf install -y gcc libgomp-devel  # Fedora/RHEL

# 编译
cd MCBEseedcracker_linux
chmod +x build.sh
./build.sh
```

---

## 性能参考

| 破解器 | 速度      | 预计时间 (2^32) |
| ------ | --------- | --------------- |
| 低32位 | ~300万/秒 | ~24分钟         |
| 高32位 | ~7万/秒   | ~17小时         |

测试环境：Windows 10, Intel Core i5-2500K @ 3.30GHz (4核)

> **💡 提示**：低32位破解速度受结构类型影响，使用 linear 类型结构（如沙漠神殿、女巫屋等）速度更快。

---

## 参考资料

- [cubiomes](https://github.com/Cubitect/cubiomes) - Minecraft 群系生成模拟库，用于高32位破解中的群系计算
- [Mersenne Twister (MT19937)](https://en.wikipedia.org/wiki/Mersenne_Twister) - 低32位破解中使用的随机数生成器，用于结构偏移计算
- [Xoroshiro128](https://prng.di.unimi.it/) - 高32位破解中使用的随机数生成器，用于噪声参数初始化
- [SHA-256](https://en.wikipedia.org/wiki/SHA-2) - 用于基岩版 Voronoi 扰动计算（基岩版特有）
- [Minecraft Wiki](https://minecraft.wiki/) - Minecraft 相关科普知识参考
- [MC种子科普视频](https://www.bilibili.com/video/BV1r1N3ezEXU) - 介绍 Minecraft 种子机制的基础知识

---

## 后续计划

- [ ] **完善代码** - 完善代码，优化性能，修复bug
- [ ] **CUDA加速** - 使用GPU并行计算，预计可提升10-100倍性能
- [ ] **自动群系识别** - 在游戏内能自动识别群系类型和坐标
- [ ] **更早版本支持** - 支持1.17及更早版本的群系生成算法
- [ ] **小版本支持** - 支持更精确的小版本号（如1.19.2、1.21.3等）

---

## 许可证

本项目仅供学习研究使用。

---

## 致谢

本项目大部分代码由 AI 辅助完成，本人主要负责思路设计和测试验证。
