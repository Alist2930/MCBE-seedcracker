# MCBEseedcracker

Minecraft 基岩版种子破解器 (Windows / Linux)

> 作者是个MC小白，这个工具大部分代码是AI写的，我只是负责测试和提需求。如有问题欢迎指正。
>
> Java 版种子破解器推荐使用 [SeedcrackerX](https://github.com/19MisterX98/SeedcrackerX)。至于基岩版，我一直想要一个类似的工具，但至今没人做。虽然我这个实现可能不是最好的，但总得有人开头。
>
> **项目状态**：半成品，目前仅自用。欢迎反馈问题和建议。

---

## 功能

通过服务器上的建筑位置和群系信息，反推出世界的种子。

---

## 环境要求

- **操作系统**：Windows 10+ 或 Linux (x86_64)
- **Python 3.8+**
- **游戏版本**：1.21+（推荐），也支持 1.18/1.19/1.20（如有问题请反馈）

> **版本说明**：
>
> - **低32位破解（结构定位）**：无版本兼容问题。结构生成算法对低32位的依赖是稳定的，高版本的结构更新不会影响破解。需要注意的是，如果低版本生成的结构在高版本群系更新后不再满足生成条件（如群系变化），该结构可能在高版本中不存在，但这在逻辑上不影响破解流程——因为破解的是结构生成时的种子，而非当前版本的结构存在性。
> - **高32位破解（群系）**：已做版本兼容处理（cubiomes工具），如有问题请反馈。

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

多个结构同时匹配可大幅缩小候选范围，通常几分钟内完成。

```bash
# Windows
cd MCBEseedcracker/crack_low32
python crack_low32.py

# Linux
cd MCBEseedcracker_linux/crack_low32
python3 crack_low32.py
```

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

| 英文名           | 中文名            |
| ---------------- | ----------------- |
| village          | 村庄/僵尸村庄     |
| mansion          | 林地府邸          |
| end_city         | 末地城            |
| ocean_monument   | 海底神殿          |
| ancient_city     | 远古城市          |
| ocean_ruins      | 海底废墟          |
| shipwreck        | 沉船              |
| nether_complexes | 下界要塞/堡垒遗迹 |
| desert_temple    | 沙漠神殿          |
| igloo            | 雪屋              |
| swamp_hut        | 女巫屋            |
| jungle_temple    | 丛林神庙          |

坐标只要是在一个区块内都行。

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
python crack_high32.py

# Linux
cd MCBEseedcracker_linux/crack_high32
python3 crack_high32.py
```

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
    (1500, -800, 37),     # badlands
]

Y_COORD = 150  # 采样高度（地表建议 Y>=150）
```

---

## 完整流程

1. **收集结构坐标** - 在目标世界获取建筑坐标（建议5个）
2. **运行低32位破解** - 得到候选的低32位值
3. **收集群系样本** - 获取不同位置的群系ID（建议5个）
4. **运行高32位破解** - 得到完整种子
5. **验证** - 使用 [ChunkBase](https://www.chunkbase.com/apps/seed-map) 验证种子

---

## 群系ID参考

| 群系            | ID  | 群系         | ID  |
| --------------- | --- | ------------ | --- |
| ocean           | 0   | plains       | 1   |
| desert          | 2   | forest       | 4   |
| taiga           | 5   | swamp        | 6   |
| deep_ocean      | 24  | jungle       | 21  |
| dark_forest     | 29  | badlands     | 37  |
| flower_forest   | 132 | ice_spikes   | 140 |
| dripstone_caves | 174 | lush_caves   | 175 |
| meadow          | 177 | deep_dark    | 183 |
| mangrove_swamp  | 184 | cherry_grove | 185 |
| pale_garden     | 186 |              |     |

完整列表见 `crack_high32.py` 开头的 `BIOME_IDS` 字典。

---

## 版本兼容性

程序会检测群系样本与MC版本的兼容性：

```
[!] Warning: Some biomes are not available in MC 1.18:
  (-1922, 1231) -> cherry_grove (ID: 185) 需要 1.20+
```

| 版本 | 新增群系                              |
| ---- | ------------------------------------- |
| 1.18 | dripstone_caves, lush_caves, 山地群系 |
| 1.19 | deep_dark, mangrove_swamp             |
| 1.20 | cherry_grove                          |
| 1.21 | pale_garden                           |

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
| 低32位 | ~200万/秒 | ~36分钟         |
| 高32位 | ~7万/秒   | ~17小时         |

测试环境：Windows 10, Intel Core i5-2500K @ 3.30GHz (4核)

---

## 参考资料

- [ChunkBase Seed Map](https://www.chunkbase.com/apps/seed-map)
- [SodaMC Seed Map](https://sodamc.com/tools/Seed_Map.htm)
- [cubiomes](https://github.com/Cubitect/cubiomes)

---

## 后续计划

- [ ] **完善代码** - 完善代码，优化性能，修复bug
- [ ] **CUDA加速** - 使用GPU并行计算，预计可提升10-100倍性能
- [ ] **自动群系识别** - 在游戏内能自动识别群系类型和坐标
- [ ] **更早版本支持** - 支持1.17及更早版本的群系生成算法

---

## MC种子科普[参考：https://www.bilibili.com/video/BV1r1N3ezEXU/]

### 种子值范围

Minecraft使用64位整数作为世界种子，范围：`-2⁶³ ~ 2⁶³-1`（约-922亿亿 ~ 922亿亿）。

### 种子输入规则

**1. 不输入种子**

系统随机生成一个64位范围内的种子。

**2. 输入数字**

- 如果数字在 `-2⁶³ ~ 2⁶³-1` 范围内，直接使用该数字作为种子
- 如果数字超出范围，则按字符串处理

**3. 输入字符串**

字符串会被转换为数字种子，计算公式：

```
seed = Σ(Unicode(字符i) × 31^(长度-i))
```

例如：

- `"d"` → Unicode=100 → seed=100
- `"dd"` → 31×100 + 100 = 3200

计算结果会被截断到32位整数范围（`-2³¹ ~ 2³¹-1`）。

### 为什么需要分两步破解？

64位种子空间太大（约1.8×10¹⁹种可能），直接遍历不现实。

但结构生成算法只依赖种子的低32位，所以：

1. **低32位**：通过结构位置快速缩小范围（约43亿种可能）
2. **高32位**：通过群系样本精确定位（约43亿种可能）

两步结合，将问题分解为两个可处理的子问题。

---

## 许可证

本项目仅供学习研究使用。

---

## 致谢

本项目大部分代码由 AI 辅助完成，本人主要负责思路设计和测试验证。
