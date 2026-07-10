# MCBEseedcracker (Linux)

[English](README.md) | 简体中文

Minecraft 基岩版种子破解器 - Linux 命令行版本

> Windows 图形界面版请见 [MCBEseedcracker_win_ui](../MCBEseedcracker_win_ui/README_CN.md)

---

## 环境要求

- **操作系统**：Linux (x86_64)
- **Python**：3.6+
- **游戏版本**：1.21+（推荐），也支持 1.18/1.19/1.20

---

## 快速开始

### 低32位破解

```bash
cd crack_low32
python3 crack_low32.py                    # 完整破解 (0 - 2^32-1)
python3 crack_low32.py --test             # 测试模式 (0 - 100M)
python3 crack_low32.py --start 1000 --end 2000  # 指定范围
```

### 高32位破解

```bash
cd crack_high32
python3 crack_high32.py                         # 完整破解 (0 ~ 2^32-1)
python3 crack_high32.py --test                  # 测试模式 (0 ~ 100M)
python3 crack_high32.py --low32 1818588773      # 指定低32位值
```

---

## 低32位破解器

通过结构位置破解种子的低32位。

### 命令行参数

| 参数      | 说明                         |
| --------- | ---------------------------- |
| `--start` | 起始低32位值（默认: 0）      |
| `--end`   | 结束低32位值（默认: 2^32-1） |
| `--test`  | 测试模式（0 - 100M）         |

### 配置目标结构

编辑 `crack_low32.py` 开头的 `TARGETS`（建议5个结构）：

```python
TARGETS = [
    {"structure": "swamp_hut", "x": 2136, "z": -1176},
    {"structure": "jungle_temple", "x": -360, "z": -248},
    {"structure": "desert_temple", "x": -936, "z": 4744},
    {"structure": "ocean_monument", "x": 792, "z": -792},
    {"structure": "end_city", "x": 1352, "z": -1208},
]
```

### 支持的结构

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

> **提示**：优先寻找 **linear** 类型的结构（如沙漠神殿、女巫屋、丛林神庙、沉船等）。程序会自动将 linear 类型排序优先处理，计算量更少，破解速度更快。

### 结构定位区块确定方法

- **沙漠神殿**：中心位置所在的区块
- **海底神殿**：中心位置所在的区块
- **女巫屋**：建筑占区块面积最大的区块
- **丛林神庙**：建筑占区块面积最大的区块
- **末地城**：入口潜影贝方形结构占区块面积最大的区块
- **沉船**：完整沉船取船头所在区块（船头大概是刚好顶到区块边界的那端），残缺沉船取船占区块面积最大的区块

---

## 高32位破解器

通过群系样本破解种子的高32位。

### 命令行参数

| 参数          | 说明                         |
| ------------- | ---------------------------- |
| `--start`     | 起始高32位值（默认: 0）      |
| `--end`       | 结束高32位值（默认: 2^32-1） |
| `--test`      | 测试模式（0 ~ 100M）         |
| `--low32`     | 低32位值                     |
| `--processes` | 进程数（默认: CPU核心数）    |

### 稀有度自动排序

程序会自动按群系稀有度排序样本，最稀有的群系优先检查，一旦不匹配立即跳过当前种子，大幅提高效率：

```
[*] Biome samples (sorted by rarity, rarest first):
    1. (-270, 470) -> pale_garden (ID: 186, 0.0786%)
    2. (-1922, 1231) -> cherry_grove (ID: 185, 0.2805%)
    3. (-4706, 3302) -> flower_forest (ID: 132, 0.6529%)
    ...
```

### 配置参数

编辑 `crack_high32.py` 开头：

```python
# 低32位值（来自 crack_low32 结果）
LOW32 = 1818588773

# MC版本
MC_VERSION_STR = "1.21"  # 可选: "1.18", "1.19", "1.20", "1.21"

# 群系样本（建议5个）
SAMPLES = [
    (-1922, 1231, 185),   # cherry_grove
    (-4706, 3302, 132),   # flower_forest
    (-935, 2592, 5),      # taiga
    (-2697, 1363, 4),     # forest
    (-270, 470, 186),     # pale_garden
]

Y_COORD = 200  # 采样高度（地表建议 Y>=200，避免地下群系干扰）
```

> **重要**：群系样本必须使用**主世界（Overworld）**的群系，不要使用下界、末地等其他维度的群系。

### 群系样本选择建议

- **选择群系中心区域的坐标**，远离群系边界至少3格以上
- **避免在群系边界附近采集样本**
- 如果破解失败，尝试更换同一群系内的其他坐标

---

## 群系ID参考（1.21）

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
| deep_dark（深暗之域）                | 183 | -      | sulfur_caves（硫磺洞穴）              | -   | -      |

> **注**：稀有度基于地表 Y=200 采样统计。地下群系（dripstone_caves、lush_caves、deep_dark、sulfur_caves）不参与稀有度排序，默认稀有度为1。

> **警告**：`sulfur_caves`（硫磺洞穴）是 MC 1.26+ 新增的地下群系，cubiomes 库暂不支持此群系。请避免使用硫磺洞穴样本进行破解。

> **注意**：ChunkBase 等网站使用 Java 版群系名称，与基岩版不同。例如：Java 的 `stony_shore` 在基岩版是 `stone_beach`，Java 的 `dark_forest` 在基岩版是 `roofed_forest`。验证时请注意区分。

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

| 版本号 | 枚举值 | 说明                 |
| ------ | ------ | -------------------- |
| 1.18   | 22     | 包含 1.18.2          |
| 1.19   | 24     | 包含 1.19.4          |
| 1.20   | 25     | 包含 1.20.6          |
| 1.21   | 28     | Winter Drop (1.21.4) |

> **注**：目前仅支持主版本号，小版本间群系生成可能存在差异。

### 重要限制

**高32位破解基于 cubiomes 库，仅支持到 Java 版 1.21.3，2024年11月后停止更新。**

| cubiomes 信息  | 详情                      |
| -------------- | ------------------------- |
| 最新版本       | 4.1.2                     |
| 最后更新       | 2024年11月10日            |
| 支持的最高版本 | Java 版 1.21.3 (苍白之园) |

**不支持：**

- 基岩版 1.26+
- 2025年及之后的 Minecraft 版本

### 苍白之园 (Pale Garden) 版本差异说明

**重要**：cubiomes 库目前仅支持到 MC 1.21.4 (Winter Drop)，而 MC 1.21.5+ 对苍白之园的生成范围进行了调整。

| MC 版本       | cubiomes 支持 | 苍白之园生成情况                 |
| ------------- | ------------- | -------------------------------- |
| 1.21.3 及以前 | ✅ (代码 27)  | 不存在，原位置为黑森林           |
| 1.21.4        | ✅ (代码 28)  | 存在，但范围较小                 |
| 1.21.5+       | ❌ 暂不支持   | 范围扩大，部分黑森林变为苍白之园 |

**如果你在 1.21.5+ 版本中采集了苍白之园样本但破解失败**：

这很可能是因为 cubiomes 的 1.21 版本（代码 28）对应的是 1.21.4，其苍白之园生成范围比 1.21.5+ 小。

**解决方法**：

将苍白之园样本改为黑森林 (roofed_forest, ID: 29) 再尝试破解。

---

## 编译

预编译的库文件已包含在项目中，可直接使用。如需自行编译：

```bash
# 安装依赖
sudo apt install -y gcc libomp-dev  # Debian/Ubuntu
sudo dnf install -y gcc libgomp-devel  # Fedora/RHEL

# 编译
chmod +x build.sh
./build.sh
```

---

## 性能参考

测试设备：Intel Core i5-2500K @ 3.30GHz，4核

| 破解器 | 速度   | 预计时间 (2^32) |
| ------ | ------ | --------------- |
| 低32位 | ~3M/s  | ~24 分钟        |
| 高32位 | ~70K/s | ~17 小时        |

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
3. **采样高度不当** - 建议 Y >= 200，避免地下群系干扰
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

## 验证种子

破解完成后，在 [ChunkBase](https://www.chunkbase.com/apps/seed-map) 验证种子是否正确。

---

## 相关链接

- [cubiomes](https://github.com/Cubitect/cubiomes) - Minecraft 群系生成模拟库，用于高32位破解中的群系计算
- [Mersenne Twister (MT19937)](https://en.wikipedia.org/wiki/Mersenne_Twister) - 低32位破解中使用的随机数生成器，用于结构偏移计算

---

## 许可证

本项目仅供学习和研究使用。
