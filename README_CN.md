# MCBEseedcracker

[English](README.md) | 简体中文

Minecraft 基岩版种子研究工具 (Windows / Linux)

> **免责声明**：本工具仅供教育和研究目的使用。旨在帮助玩家理解 Minecraft 的群系生成算法，并验证单人世界的种子。本工具不用于多人服务器作弊或利用游戏机制。
>
> GitHub 上存在类似的开源项目：
>
> - [cubiomes](https://github.com/Cubitect/cubiomes) - Minecraft 群系生成模拟库
> - [SeedcrackerX](https://github.com/19MisterX98/SeedcrackerX) - Java 版种子查找器
>
> 作者是个MC小白，这个工具大部分代码是AI写的，我只是负责测试和提需求。如有问题欢迎指正。
>
> **项目状态**：半成品，目前仅自用。欢迎反馈问题和建议。

---

## 功能

通过种子验证和群系分析，研究 Minecraft 的世界生成算法。

---

## 环境要求

- **操作系统**：Windows 10+ 或 Linux (x86_64)
- **游戏版本**：1.21+（推荐），也支持 1.18/1.19/1.20（如有问题请反馈）

> **版本说明**：
>
> - **低32位破解（结构定位）**：无版本兼容问题。结构生成算法对低32位的依赖是稳定的。
> - **高32位破解（群系）**：已做版本兼容处理（基于cubiomes工具），如有问题请反馈。

---

## 快速开始

| 平台        | 版本       | 界面 | 使用方式                 |
| ----------- | ---------- | ---- | ------------------------ |
| **Windows** | 图形界面版 | GUI  | 从源码运行，详见下方说明 |
| **Linux**   | 命令行版   | 终端 | 编辑配置文件后运行       |

### Windows 用户（推荐）

**Windows 图形界面版**，无需命令行操作，无需编辑配置文件！

详见 [MCBEseedcracker_win_ui/README_CN.md](MCBEseedcracker_win_ui/README_CN.md)。

**功能特性：**

- ✅ 图形化界面 - 无需编程
- ✅ 低32位和高32位破解
- ✅ 进度保存/恢复
- ✅ 中英文切换
- ✅ 支持 MC 1.18/1.19/1.20/1.21
- ✅ 建筑图标和群系颜色标识

### Linux 用户

使用命令行版本。详见 [MCBEseedcracker_linux/README_CN.md](MCBEseedcracker_linux/README_CN.md)。

---

## 目录结构

```
MCBEseedcracker_win_ui/    # Windows 图形界面版（推荐）
├── dist/                  # 预编译可执行文件
├── ui/                    # UI 源代码
└── dll/                   # 预编译 DLL

MCBEseedcracker_linux/     # Linux 命令行版
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

> **注意**：Windows 命令行版本（`MCBEseedcracker/`）已不再维护，请使用图形界面版本（`MCBEseedcracker_win_ui/`）。

---

## 原理说明

### 低32位破解原理

Minecraft基岩版使用64位整数作为世界种子。结构生成时，系统会根据区域坐标和种子计算"区域种子"（region seed），然后使用MT19937随机数生成器确定结构在区域内的偏移位置。

#### 区域种子计算公式

```
区域坐标: rx = 区块x / spacing, rz = 区块z / spacing
区域种子: r_base = (rx × 2570712328 + rz × 4048968661 + salt) & 0xFFFFFFFF
实际种子: r_seed = 世界种子低32位 + r_base
```

其中 `salt` 是每种结构特有的常数，例如：

- 沙漠神殿: 14357617
- 海底神殿: 10387313
- 沉船: 165745295

#### 结构生成参数

每种结构有两个关键参数：

- **spacing（区域大小）**：结构生成区域的边长，以区块为单位。世界被划分为 `spacing × spacing` 的区域网格，每个区域最多生成一个结构。
- **separation（最小间距）**：结构之间的最小距离，以区块为单位。这决定了结构在区域内可能的偏移范围。

偏移范围：`offset_range = spacing - separation`

例如，沙漠神殿的 `spacing=32`，`separation=8`，所以偏移范围为 `32-8=24` 区块。

#### 结构偏移计算

使用MT19937生成随机数，根据分布类型计算偏移：

- **Linear模式**：`offset_x = temper(mt[0]) % offset_range`
- **Triangular模式**：`offset_x = (temper(mt[0]) % range + temper(mt[1]) % range) / 2`

#### 破解方法

遍历低32位的所有可能值（0 ~ 2³²-1，约43亿），对每个候选值：

1. 计算区域种子 `r_seed = w + r_base`
2. 初始化MT19937并生成偏移值
3. 检查偏移是否与实际结构位置匹配

多个结构同时匹配可大幅缩小候选范围，通常半小时内完成。

#### 支持的结构

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

> **提示**：优先寻找 **linear** 类型的结构（如沙漠神殿、女巫屋、丛林神庙、沉船等）。Linear 类型计算量更少，破解速度更快。

---

### 高32位破解原理

低32位确定后，还需要确定高32位才能得到完整种子。群系生成依赖于完整的64位种子，通过多层噪声函数计算每个坐标的群系类型。

#### 为什么使用 cubiomes 库

本项目使用 [cubiomes](https://github.com/Cubitect/cubiomes) 库进行群系计算。这是一个用 C 语言编写的库，专门模拟 Minecraft Java 版的生物群系生成。

从 1.18 版本开始，Minecraft Java 版和基岩版的地形生成算法完全统一，两者使用相同的噪声函数、气候参数系统（温度、湿度、大陆性、侵蚀、深度、怪异度）以及 Voronoi 扰动坐标映射。因此，可以直接使用 cubiomes 库来计算基岩版的群系，无需重新实现复杂的噪声生成算法。

#### 群系生成流程（1.18+）

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

#### Voronoi 坐标映射

群系噪声在 1:4 尺度计算（每 4x4 方块区域一个采样点）。要获取具体 1:1 方块坐标的群系，需要应用 Voronoi 扰动进行坐标映射：

```
sha256_hash = SHA256(种子)
voronoi_offset = voronoiAccess3D(sha256_hash, x, y, z)
实际采样坐标 = (x + voronoi_x, y + voronoi_y, z + voronoi_z)
```

这是 Java 版和基岩版 1.18+ 使用的标准算法。

#### 破解方法

遍历高32位的所有可能值（0 ~ 2³²-1），对每个候选种子：

1. 计算完整64位种子：`seed = (high32 << 32) | low32`
2. 初始化噪声生成器
3. 对每个样本坐标计算群系ID
4. 与实际采集的群系样本比对

由于需要完整遍历且群系计算复杂，耗时较长，通常需要数小时。

#### 群系ID参考（1.21）

| 群系                                 | ID  | 稀有度 | 群系                                  | ID  | 稀有度 |
| ------------------------------------ | --- | ------ | ------------------------------------- | --- | ------ |
| pale_garden（苍白之园）              | 186 | 0.08%  | extreme_hills_mutated（风袭沙砾丘陵） | 131 | 0.10%  |
| stony_peaks（裸岩山峰）              | 182 | 0.10%  | jagged_peaks（尖峭山峰）              | 180 | 0.15%  |
| frozen_peaks（冰封山峰）             | 181 | 0.15%  | mushroom_island（蘑菇岛）             | 14  | 0.14%  |
| extreme_hills_plus_trees（风袭森林） | 34  | 0.19%  | cherry_grove（樱花树林）              | 185 | 0.28%  |
| ice_spikes（冰刺之地）               | 140 | 0.23%  | extreme_hills（风袭丘陵）             | 3   | 0.27%  |
| savanna_mutated（风袭热带草原）      | 163 | 0.22%  | mesa_bryce（风蚀恶地）                | 165 | 0.33%  |
| snowy_slopes（积雪山坡）             | 179 | 0.39%  | savanna_plateau（热带高原）           | 36  | 0.40%  |
| mangrove_swamp（红树林沼泽）         | 184 | 0.52%  | flower_forest（繁花森林）             | 132 | 0.65%  |
| bamboo_jungle（竹林）                | 168 | 0.65%  | sunflower_plains（向日葵平原）        | 129 | 0.66%  |
| mega_taiga（原始松木针叶林）         | 32  | 0.68%  | mesa_plateau_stone（繁茂的恶地高原）  | 38  | 0.64%  |
| grove（雪林）                        | 178 | 0.75%  | mesa（恶地）                          | 37  | 0.90%  |
| swamp（沼泽）                        | 6   | 1.00%  | cold_beach（积雪沙滩）                | 26  | 0.35%  |
| stone_beach（石岸）                  | 25  | 1.19%  | jungle_edge（稀疏丛林）               | 23  | 1.26%  |
| deep_frozen_ocean（冰冻深海）        | 50  | 1.21%  | meadow（草甸）                        | 177 | 1.18%  |
| roofed_forest（黑森林）              | 29  | 2.00%  | jungle（丛林）                        | 21  | 1.90%  |
| birch_forest（桦木森林）             | 27  | 2.14%  | desert（沙漠）                        | 2   | 2.47%  |
| cold_taiga（积雪针叶林）             | 30  | 2.56%  | frozen_river（冻河）                  | 11  | 0.82%  |
| warm_ocean（暖水海洋）               | 44  | 2.24%  | deep_lukewarm_ocean（温水深海）       | 48  | 2.45%  |
| deep_cold_ocean（冷水深海）          | 49  | 2.40%  | frozen_ocean（冻洋）                  | 10  | 2.27%  |
| beach（沙滩）                        | 16  | 2.67%  | ice_plains（雪原）                    | 12  | 2.79%  |
| taiga（针叶林）                      | 5   | 3.41%  | savanna（热带草原）                   | 35  | 4.00%  |
| deep_ocean（深海）                   | 24  | 4.38%  | lukewarm_ocean（温水海洋）            | 45  | 4.61%  |
| cold_ocean（冷水海洋）               | 46  | 4.51%  | river（河流）                         | 7   | 6.17%  |
| ocean（海洋）                        | 0   | 6.87%  | plains（平原）                        | 1   | 10.52% |
| forest（森林）                       | 4   | 12.07% | birch_forest_mutated（原始桦木森林）  | 155 | 2.09%  |
| dripstone_caves（溶洞）              | 174 | -      | lush_caves（繁茂洞穴）                | 175 | -      |
| deep_dark（深暗之域）                | 183 | -      |                                       |     |        |

> **注**：稀有度基于地表 Y=200 采样统计。地下群系（dripstone_caves、lush_caves、deep_dark）不参与稀有度排序，默认稀有度为1。

---

## 完整流程

### Windows（图形界面）

1. 运行图形界面程序（详见 [MCBEseedcracker_win_ui/README_CN.md](MCBEseedcracker_win_ui/README_CN.md)）
2. 添加建筑 → 开始低32位破解
3. 添加群系 → 开始高32位破解
4. 在 [ChunkBase](https://www.chunkbase.com/apps/seed-map) 验证种子

### Linux（命令行）

1. 编辑 `crack_low32.py` → 添加建筑 → 运行
2. 编辑 `crack_high32.py` → 添加群系 → 运行
3. 在 [ChunkBase](https://www.chunkbase.com/apps/seed-map) 验证种子

> **注意**：ChunkBase 等网站上的群系命名是按照 Java 版的，与基岩版有所不同。例如：Java 版的 `stony_shore` 在基岩版中是 `stone_beach`，Java 版的 `dark_forest` 在基岩版中是 `roofed_forest`。验证时请注意区分。

---

## 常见问题

### 低32位破解失败（没有找到匹配的种子）

**可能原因：**

1. **结构坐标错误** - 坐标填写不正确，或区块定位方法有误
2. **结构数量不足** - 结构数量不足会导致找到过多的候选种子，建议至少提供 5 个不同类型的结构
3. **结构类型选择不当** - 某些结构（如村庄）生成规则复杂，建议优先使用：
   - 沙漠神殿、女巫屋、丛林神庙（生成规则简单稳定）
   - 海底神殿、末地城
4. **版本不兼容** - 如果目标世界是旧版本（1.18以下）生成的，结构位置可能与当前版本不同

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
5. **样本选择不当** - 应选择稀有群系（如樱花林），避免常见群系（如平原、海洋）

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

## 性能参考

| 破解器 | 速度   | 预计时间 (2^32) |
| ------ | ------ | --------------- |
| 低32位 | ~3M/s  | ~24 分钟        |
| 高32位 | ~70K/s | ~17 小时        |

---

## 版本兼容性

### ⚠️ 重要限制

**高32位破解基于 cubiomes 库，仅支持到 Java 版 1.21.3，2024年11月后停止更新。**

| cubiomes 信息  | 详情                      |
| -------------- | ------------------------- |
| 最新版本       | 4.1.2                     |
| 最后更新       | 2024年11月10日            |
| 支持的最高版本 | Java 版 1.21.3 (苍白之园) |

**不支持：**

- 2025年及之后的 Minecraft 版本（基岩版 1.26+）

### 群系样本选择建议

- **选择群系中心区域的坐标**，远离群系边界至少3格以上
- **避免在群系边界附近采集样本**
- 如果破解失败，尝试更换同一群系内的其他坐标

### 苍白之园 (Pale Garden) 版本差异说明

**重要**：cubiomes 库目前仅支持到 MC 1.21.4 (Winter Drop)，而 MC 1.21.5+ 对苍白之园的生成范围进行了调整。

| MC 版本       | cubiomes 支持 | 苍白之园生成情况                 |
| ------------- | ------------- | -------------------------------- |
| 1.21.3 及以前 | ✅ (代码 27)  | 不存在，原位置为黑森林           |
| 1.21.4        | ✅ (代码 28)  | 存在，但范围较小                 |
| 1.21.5+       | ❌ 暂不支持   | 范围扩大，部分黑森林变为苍白之园 |

**如果你在 1.21.5+ 版本中采集了苍白之园样本但破解失败**：

这很可能是因为 cubiomes 的 1.21 版本（代码 28）对应的是 1.21.4，其苍白之园生成范围比 1.21.5+ 小。在 1.21.5+ 中，一些原本是黑森林的位置变成了苍白之园。

**解决方法**：

将苍白之园样本改为黑森林 (roofed_forest, ID: 29) 再尝试破解。

---

## 相关链接与参考资料

- [Windows 图形界面版](MCBEseedcracker_win_ui/README_CN.md)
- [Linux 命令行版](MCBEseedcracker_linux/README_CN.md)
- [cubiomes](https://github.com/Cubitect/cubiomes) - Minecraft 群系生成模拟库，用于高32位破解中的群系计算
- [Mersenne Twister (MT19937)](https://en.wikipedia.org/wiki/Mersenne_Twister) - 低32位破解中使用的随机数生成器，用于结构偏移计算

---

## 许可证

本项目仅供学习和研究使用。

---

本项目大部分代码由 AI 辅助完成，本人主要负责思路设计和测试验证。
