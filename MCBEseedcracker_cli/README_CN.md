# MCBEseedcracker (CLI)

[English](README.md) | 简体中文

Minecraft 基岩版种子破解器 - 跨平台命令行版本（Windows / Linux / macOS）

> Windows 图形界面版请见 [MCBEseedcracker_win_ui](../MCBEseedcracker_win_ui/README_CN.md)

---

## 目录结构

```
MCBEseedcracker_cli/       # 跨平台命令行版
├── config.json            # 配置文件（低32位和高32位）
├── config_loader.py       # 配置加载器
├── build.sh               # 编译脚本（Linux / macOS）
├── build.bat              # 编译脚本（Windows）
├── crack_low32/
│   ├── crack_low32.c      # 编译源码
│   ├── crack_low32_opencl.c  # GPU 版本
│   ├── crack_low32.cl     # OpenCL 内核
│   ├── crack_low32.py     # 命令行脚本
│   └── （编译产物：crack_low32.so / crack_low32.dll、
│        crack_low32_opencl.so / crack_low32_opencl.dll）
└── crack_high32/
    ├── crack_high32.c     # 编译源码
    ├── crack_high32.py    # 命令行脚本
    ├── cubiomes/          # 群系生成库
    └── （编译产物：crack_high32.so / crack_high32.dll）
```

---

## 环境要求

- **操作系统**：Windows 10+ / Linux (x86_64, aarch64) / macOS 10.15+
- **Python**：3.6+
- **编译工具**：MinGW-w64 GCC（Windows）或 GCC/Clang（Linux/macOS）；GPU 加速需 OpenCL SDK（可选）
- **游戏版本**：1.18/1.19/1.20/1.21/26.XX（支持小版本）

---

### 配置文件说明

CLI 版本使用 **`config.json`** 统一管理所有配置参数（低32位和高32位破解）。

**首次运行时会自动创建 `config.json` 文件，请根据需求编辑该文件。**

## 快速开始

### 低32位破解

```bash
cd crack_low32
python3 crack_low32.py                    # 完整破解 (0 - 2^32-1)
python3 crack_low32.py --test             # 测试模式 (0 - 100M)
python3 crack_low32.py --start 1000 --end 2000  # 指定范围
python3 crack_low32.py --processes 8      # 指定进程数（CPU模式）
```

**找到的种子输出：**
所有找到的种子会自动保存到 `crack_low32/found_seeds.txt`，包含时间戳。程序启动时创建该文件，破解过程中实时追加找到的种子。

### 低32位破解命令行参数

| 参数          | 说明                                         |
| ------------- | -------------------------------------------- |
| `--start`     | 起始低32位值（默认: 0）                      |
| `--end`       | 结束低32位值（默认: 2^32-1）                 |
| `--test`      | 测试模式（0 - 100M）                         |
| `--cpu`       | 强制使用CPU模式                              |
| `--gpu`       | 强制使用GPU模式（不可用时自动回退CPU）       |
| `--processes` | 进程数（仅CPU模式有效，建议不超过CPU核心数） |

#### 低32位破解配置

编辑 `config.json` 的 `low32` 部分：

```json
{
  "low32": {
    "test_mode": false,
    "start": 0,
    "end": 4294967296,
    "use_gpu": true,
    "auto_fallback": true,
    "seeds_per_thread": 256,
    "max_results": 10000,
    "processes": null,
    "targets": [
      { "structure": "swamp_hut", "x": 2136, "z": -1176 },
      { "structure": "jungle_temple", "x": -360, "z": -248 },
      { "structure": "desert_temple", "x": -936, "z": 4744 },
      { "structure": "ocean_monument", "x": 792, "z": -792 },
      { "structure": "end_city", "x": 1352, "z": -1208 }
    ]
  }
}
```

**配置项说明：**

| 配置项             | 说明                                           |
| ------------------ | ---------------------------------------------- |
| `test_mode`        | 测试模式（false: 正常模式，true: 测试模式）    |
| `start`            | 起始低32位值（默认: 0）                        |
| `end`              | 结束低32位值（默认: 2^32-1）                   |
| `use_gpu`          | 启用/禁用GPU加速（默认: true）                 |
| `auto_fallback`    | GPU失败时自动回退CPU（默认: true）             |
| `seeds_per_thread` | 每个GPU线程处理的种子数（根据GPU能力自动调整） |
| `max_results`      | 最大结果存储数量（默认: 10000）                |
| `processes`        | CPU进程数（null: 自动检测所有CPU核心）         |
| `targets`          | 目标结构列表（建议5个结构）                    |

#### 支持的结构

| 英文名                  | 中文名               | 分布类型   |
| ----------------------- | -------------------- | ---------- |
| village                 | 村庄/僵尸村庄        | triangular |
| mansion                 | 林地府邸             | triangular |
| end_city                | 末地城               | triangular |
| ocean_monument          | 海底神殿             | triangular |
| ancient_city            | 远古城市             | triangular |
| pillager_outpost        | 掠夺者哨塔           | triangular |
| buried_treasure         | 埋藏的宝藏           | triangular |
| ocean_ruins             | 海底废墟             | **linear** |
| shipwreck               | 沉船                 | **linear** |
| nether_complexes        | 下界要塞/堡垒遗迹    | **linear** |
| desert_temple           | 沙漠神殿             | **linear** |
| igloo                   | 雪屋                 | **linear** |
| swamp_hut               | 女巫屋               | **linear** |
| jungle_temple           | 丛林神庙             | **linear** |
| ruined_portal_overworld | 废弃传送门（主世界） | **linear** |
| ruined_portal_nether    | 废弃传送门（下界）   | **linear** |
| desert_well             | 沙漠水井             | **special** |
| amethyst_geode          | 紫晶洞（1.18+）      | **special** |

> **提示**：优先寻找 **linear** 类型的结构（如沙漠神殿、女巫屋、丛林神庙、沉船）。Linear 类型计算量更少，破解速度更快。生成规则复杂的结构（村庄、雪屋、掠夺者哨塔、废弃传送门）在游戏中可能有一个区块的偏移——4宫格会自动处理，可放心使用。
>
> **为什么使用 4宫格**：这类结构由跨越多个区块的建筑片段组成，游戏中观察到的位置可能位于与真实生成原点区块相邻的区块，仅凭坐标无法判断真正的原点区块是哪一个。因此破解器会对每个输入坐标自动测试 4 个可能的原点区块（输入区块及其相邻的 3 个区块），任一匹配即视为有效样本。
>
> **注意**：古迹废墟、试炼密室、废弃营地使用 Java LCG 随机数生成器，用于**高32位破解**阶段的可选加速，详见 [Java LCG 结构](#java-lcg-结构可选加速) 一节。
>
> **特殊结构**：**沙漠水井**和**紫晶洞**使用区块装饰随机数生成器（纯低32位约束，可直接用于低32位破解）。沙漠水井填入精确的水井坐标（/tp 位置）；紫晶洞（1.18+）填入洞内任意方块坐标。
>
> ⚠️ **关于埋藏的宝藏**：虽然参数正确，但由于生成密度极高（spacing=4区块），单独使用容易产生大量候选种子。实测使用4个埋藏宝箱样本，在0-10000种子范围内得到400个候选种子。建议仅在其他结构样本不足时作为补充，或作为验证使用。

**填入的建筑坐标只需在结构定位的区块内的任意坐标即可。**

#### 结构定位区块确定方法

- **沙漠神殿**：中心位置所在的区块

  ![沙漠神殿区块确定](../assets/imgs/desert_temple.png)

- **海底神殿**：中心位置所在的区块

  ![海底神殿区块确定](../assets/imgs/ocean_monument.jpg)

- **女巫屋**：建筑占区块面积最大的区块

  ![女巫屋区块确定](../assets/imgs/swamp_hut.png)

- **丛林神庙**：建筑占区块面积最大的区块

  ![丛林神庙区块确定](../assets/imgs/jungle_temple.png)

- **末地城**：入口潜影贝方形结构占区块面积最大的区块

  ![末地城区块确定](../assets/imgs/end_city.png)

- **沉船**：完整沉船取船头所在区块（船头大概是刚好顶到区块边界的那端），残缺沉船取船占区块面积最大的区块

  完整沉船：

  ![完整沉船区块确定](../assets/imgs/shipwreck_complete.png)

  残缺沉船：

  ![残缺沉船区块确定](../assets/imgs/shipwreck_incomplete.png)

- **海底废墟**：单个的海底废墟为其占区块面积最大的区块，若为海底废墟群则为中间的海底废墟占区块面积最大的区块

  单个海底废墟：

  ![单个海底废墟区块确定](../assets/imgs/ocean_ruins.png)

  海底废墟群：

  ![海底废墟群区块确定](../assets/imgs/ocean_ruins_group.png)

- **村庄**：（区块确定方法待补充）

  ![村庄区块确定](../assets/imgs/village.png)

- **雪屋**：（区块确定方法待补充）

  ![雪屋区块确定](../assets/imgs/igloo.png)

- **掠夺者前哨站**：（区块确定方法待补充）

  ![掠夺者前哨站区块确定](../assets/imgs/pillager_outpost.png)

- **林地府邸**：（区块确定方法待补充）

  ![林地府邸区块确定](../assets/imgs/mansion.png)

- **废弃传送门**：（区块确定方法待补充）

  ![废弃传送门区块确定](../assets/imgs/ruined_portal.png)

- **远古城市**：（区块确定方法待补充）

  ![远古城市区块确定](../assets/imgs/ancient_city.png)

---

### 高32位破解

```bash
cd crack_high32
python3 crack_high32.py                         # 完整破解 (0 ~ 2^32-1)
python3 crack_high32.py --test                  # 测试模式 (0 ~ 100M)
python3 crack_high32.py --low32 1818588773      # 指定低32位值
python3 crack_high32.py --start 0 --end 1000000000  # 自定义范围
python3 crack_high32.py --processes 16          # 指定进程数（最大16）
python3 crack_high32.py --lcg-structure trail_ruins:123:456 --lcg-structure trial_chamber:-200:300  # Java LCG 结构模式
```

**[Java LCG 结构模式](#java-lcg-结构可选加速)（推荐）：**
添加一个或多个 `--lcg-structure` 参数（格式：`name:x:z`，支持的名称：`trail_ruins` / `trial_chamber` / `abandoned_camp`）后进入两阶段模式：阶段一直接由结构推导第 32-47 位；阶段二在搜索范围内遍历第 48-63 位并用群系样本验证。只需 1-2 个结构，相比纯暴力破解大幅提速。详见 [Java LCG 结构](#java-lcg-结构可选加速)。

**阶段二进度输出示例：**

```
  [#-----------------------------] 4.4% | Candidate 24/541 | 98,453/s | ETA: 8.2min | Found: 0
  [#-----------------------------] 4.6% | Candidate 25/541 | 101,372/s | ETA: 7.9min | Found: 0
  [#-----------------------------] 4.8% | Candidate 26/541 | 103,914/s | ETA: 7.7min | Found: 0
```

**找到的种子输出：**
所有找到的种子会自动保存到 `crack_high32/found_seeds.txt`，包含时间戳和详细信息。程序启动时会创建/清空此文件，确保即使进度输出过多也不会遗漏找到的种子。

---

### 高32位破解命令行参数

| 参数              | 说明                                                                                                                   |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `--start`         | 起始高32位值（默认: 0）                                                                                                |
| `--end`           | 结束高32位值（默认: 2^32-1）                                                                                           |
| `--test`          | 测试模式（0 ~ 100M）                                                                                                   |
| `--low32`         | 低32位值                                                                                                               |
| `--processes`     | 进程数（默认: CPU核心数）                                                                                              |
| `--lcg-structure` | [Java LCG 结构](#java-lcg-结构可选加速)，格式 `name:x:z`，可重复（`trail_ruins` / `trial_chamber` / `abandoned_camp`） |

#### 高32位破解配置

编辑 `config.json` 的 `high32` 部分：

```json
{
  "high32": {
    "test_mode": false,
    "start": 0,
    "end": 4294967295,
    "low32": 1818588773,
    "mc_version": "26.50",
    "processes": null,
    "samples": [
      { "x": -270, "z": 470, "y": 200, "biome_id": 186 },
      { "x": -1922, "z": 1231, "y": 200, "biome_id": 185 },
      { "x": -4706, "z": 3302, "y": 200, "biome_id": 132 },
      { "x": -935, "z": 2592, "y": 200, "biome_id": 5 },
      { "x": -2697, "z": 1363, "y": 200, "biome_id": 4 }
    ],
    "lcg_structures": [{ "type": "trial_chamber", "x": 633, "z": 311 }]
  }
}
```

**配置项说明：**

| 配置项           | 说明                                                                               |
| ---------------- | ---------------------------------------------------------------------------------- |
| `test_mode`      | 测试模式（false: 正常模式，true: 测试模式）                                        |
| `start`          | 起始高32位值（默认: 0）                                                            |
| `end`            | 结束高32位值（默认: 2^32-1）                                                       |
| `low32`          | 低32位值（已破解得到）                                                             |
| `mc_version`     | MC版本字符串（见下方版本对应表）                                                   |
| `processes`      | 进程数（null: 自动检测，最大16）                                                   |
| `samples`        | 群系样本列表（建议5个样本）                                                        |
| `lcg_structures` | 可选的 Java LCG 结构列表（两阶段模式，见 [Java LCG 结构](#java-lcg-结构可选加速)） |

**群系样本格式：**

每个样本包含以下字段：

- `x`、`z`、`y`：坐标（Y建议200+，避免地下群系干扰）
- `biome_id`：群系ID（见下方群系ID参考表）

> **注意**：`name`字段已移除，程序会自动根据`biome_id`识别群系名称。

> **注意**：
>
> - 每个样本格式：`(x, z, y, biome_id)`
> - 地表采样建议 `Y>=200`，避免地下群系干扰
> - 洞穴群系（如硫磺洞穴）需使用低Y坐标（`Y≤60`）
> - 高32位破解仅支持CPU模式（多进程并行），不支持GPU加速

### 预计候选数提示

破解开始前，程序会先对少量种子进行采样预检，快速估算全范围的真实候选数量，帮助判断输入样本是否足够：

- **低32位破解**：采样 2^24 个种子（GPU 约 0.1 秒，CPU 约 1.4 秒）
- **高32位破解（纯群系模式）**：采样 2^17 个种子（约 0.3 秒）
- **高32位破解（Java LCG 模式）**：跳过预检——两阶段模式的阶段一本身就会输出精确的候选数

估算结果分四档提示：

| 提示 | 含义 | 建议 |
| --- | --- | --- |
| 预计候选数约为 0：样本正常，全范围预计仅 0~1 个候选 | 严格样本的正常表现 | 正常等待结果即可 |
| 预计候选数约为 0：存在匹配率为 0 的样本（可能无效） | 某样本在 10 万测试种子中匹配 0 次 | 检查样本坐标/类型 |
| 预计候选数远超 10000（采样结果已饱和） | 结构/样本偏少，可能产生大量误报 | 增加结构/群系样本数量 |
| 预计候选数约为 N | 正常估算值 | N 较大时建议增加样本 |
---

## Java LCG 结构（可选加速）

有三个结构在基岩版使用 Java LCG 随机数生成器（而非标准 MT19937）：**古迹废墟**、**试炼密室**、**废弃营地**。

在高32位破解阶段添加这些结构后，将启用两阶段模式：

1. **阶段一（第 32-47 位）**：Java LCG 结构位置直接约束种子的第 32-47 位。每个结构可将候选数缩减约 65536 倍；**只需 1-2 个结构**。
2. **阶段二（第 48-63 位）**：对每个幸存候选，遍历第 48-63 位（最多 65536 个候选），并在搜索范围内用群系样本验证。

相比默认的纯暴力搜索第 32-47 位，此模式大幅提速。

| 英文名         | 中文名   | 分布类型 |
| ------------- | -------- | -------- |
| trail_ruins   | 古迹废墟 | linear   |
| trial_chamber | 试炼密室 | linear   |
| abandoned_camp| 废弃营地 | linear   |

**定位区块确定方法：**

与常规结构相同，填写结构所在区块内的位置即可（参见[结构定位区块确定方法](#结构定位区块确定方法)一节）。三个结构的具体区块确定方法（含图示）后续补充：

- **古迹废墟**：（区块确定方法待补充）

  ![古迹废墟区块确定](../assets/imgs/trail_ruins.png)

- **试炼密室**：（区块确定方法待补充）

  ![试炼密室区块确定](../assets/imgs/trial_chamber.png)

- **废弃营地**：（区块确定方法待补充）

  ![废弃营地区块确定](../assets/imgs/abandoned_camp.png)

---

#### 版本对应关系

| 基岩版版本          | 对应 Java 版本            | 支持的群系                  |
| ------------------- | ------------------------- | --------------------------- |
| **26.50**           | Java 26.3 (MC_26_3)       | ✅ 斑驳森林（新群系）       |
| **26.30-26.40**          | Java 26.2 (Chaos Cubed)   | ✅ 硫磺洞穴（新地下群系）   |
| **1.21.60-26.23**   | Java 1.21.5-26.1          | ✅ 苍白之园（扩大范围）     |
| **1.21.50**         | Java 1.21.4 (Winter Drop) | ✅ 苍白之园（较小范围）     |
| **1.21-1.21.40**    | Java 1.21.3               | ❌ 不支持苍白之园           |
| **1.20.60-1.20.81** | Java 1.20                 | ✅ 樱花树林                 |
| **1.20.0-1.20.51**  | Java 1.20                 | ✅ 樱花树林                 |
| **1.19**            | Java 1.19                 | ✅ 深暗之域、红树林沼泽     |
| **1.18**            | Java 1.18                 | ✅ 溶洞、繁茂洞穴、山地群系 |

#### 苍白之园版本差异

⚠️ **重要**：苍白之园在不同版本的生成范围不同：

| MC 版本           | 苍白之园生成情况          |
| ----------------- | ------------------------- |
| **1.21-1.21.40**  | ❌ 不存在，原位置为黑森林 |
| **1.21.50**       | ⚠️ 存在但范围较小         |
| **1.21.60-26.23** | ✅ 扩大的生成范围         |

**最新版本（基岩版 26.50）**：

- 对应 Java 26.3
- 新增群系：斑驳森林（ID: 188）
- 推荐：使用地表群系进行破解（有稀有度数据）

**版本 26.30-26.40**：

- 对应 Java 26.2（混沌立方更新）
- 新增群系：硫磺洞穴（ID: 187）
- 洞穴群系破解需使用低 Y 坐标（Y≤60）

**版本 1.21.60-26.23**：

- 对应 Java 1.21.5-26.1
- 苍白之园生成范围扩大（weirdness阈值降低）
- 最适合用于苍白之园破解
- 稀有度：约0.12%（从1.21.50的约0.08%增加）

**如果使用 1.21.50 版本**：

- 苍白之园已存在，但生成范围较小
- 如果破解失败，建议改用黑森林 (roofed_forest, ID: 29)

#### 基岩版 vs Java 版差异

即使版本号相同，Java 版和基岩版的群系生成也存在差异：

- **Y 轴群系变化**：Java 版群系在 Y 轴上变化显著，基岩版较稳定
- **群系边界**：两版本的群系边界位置可能略有差异
- **新版本差异**：基岩版 1.26.x 与 Java 版 1.21 群系算法有较小差异

#### ⚠️ 群系样本选择建议

- **选择群系中心区域的坐标**，远离群系边界至少3格以上
- **避免在群系边界附近采集样本**
- 如果破解失败，尝试更换同一群系内的其他坐标

#### 重要限制

**高32位破解功能基于 cubiomes 库，集成了 SeedMapper 的 MC 26.3 支持。**

| cubiomes 信息  | 详情                                 |
| -------------- | ------------------------------------ |
| 最新版本       | 4.1.2 (fork 版本，支持 MC 26.3)      |
| 最后更新       | 2026年7月 (集成 SeedMapper btree262) |
| 支持的最高版本 | Java 26.3 (基岩版 26.50)             |

**cubiomes 更新状态：**

- 官方 cubiomes 在 2024年11月后停止更新
- 集成 SeedMapper 的 cubiomes fork 版本支持 1.21.5+ 和 26.3+
- 支持苍白之园（1.21.50+）、硫磺洞穴（26.30-26.40）和斑驳森林（26.50）

### 稀有度自动排序

程序会自动按群系稀有度排序样本，最稀有的群系优先检查，一旦不匹配立即跳过当前种子，大幅提高效率：

```
[*] Biome samples (sorted by rarity, rarest first):
    1. (-270, 470, Y=200) -> pale_garden (ID: 186, 0.1210%)
    2. (-1922, 1231, Y=200) -> cherry_grove (ID: 185, 0.2950%)
    3. (-4706, 3302, Y=200) -> flower_forest (ID: 132, 0.6940%)
    ...
```

**注意**：当搜索范围大小（`end - start`）小于 100,000 时，会自动跳过严格度测试，按原始顺序检查群系样本。

#### 主世界群系ID参考（1.21.60-26.50）

| 群系                                  | ID  | 稀有度 | 群系                                    | ID  | 稀有度 |
| ------------------------------------- | --- | ------ | --------------------------------------- | --- | ------ |
| extreme_hills_mutated（风袭沙砾丘陵） | 131 | 0.10%  | stony_peaks（裸岩山峰）                 | 182 | 0.10%  |
| pale_garden（苍白之园）               | 186 | 0.12%  | mushroom_island（蘑菇岛）               | 14  | 0.14%  |
| frozen_peaks（冰封山峰）              | 181 | 0.16%  | jagged_peaks（尖峭山峰）                | 180 | 0.18%  |
| extreme_hills_plus_trees（风袭森林）  | 34  | 0.19%  | savanna_mutated（风袭热带草原）         | 163 | 0.21%  |
| ice_spikes（冰刺之地）                | 140 | 0.24%  | extreme_hills（风袭丘陵）               | 3   | 0.26%  |
| cherry_grove（樱花树林）              | 185 | 0.29%  | mesa_bryce（风蚀恶地）                  | 165 | 0.33%  |
| cold_beach（积雪沙滩）                | 26  | 0.36%  | snowy_slopes（积雪山坡）                | 179 | 0.39%  |
| savanna_plateau（热带高原）           | 36  | 0.40%  | dappled_forest（斑驳森林）              | 188 | 0.45%  |
| mangrove_swamp（红树林沼泽）          | 184 | 0.51%  | mesa_plateau_stone（繁茂的恶地高原）    | 38  | 0.62%  |
| bamboo_jungle（竹林）                 | 168 | 0.64%  | sunflower_plains（向日葵平原）          | 129 | 0.67%  |
| mega_taiga（原始松木针叶林）          | 32  | 0.69%  | flower_forest（繁花森林）               | 132 | 0.69%  |
| redwood_taiga_mutated（原始云杉针叶林） | 160 | 0.71% | grove（雪林）                           | 178 | 0.72%  |
| frozen_river（冻河）                  | 11  | 0.83%  | mesa（恶地）                            | 37  | 0.89%  |
| swamp（沼泽）                         | 6   | 0.98%  | meadow（草甸）                          | 177 | 1.16%  |
| stone_beach（石岸）                   | 25  | 1.17%  | deep_frozen_ocean（冰冻深海）           | 50  | 1.25%  |
| jungle_edge（稀疏丛林）               | 23  | 1.38%  | roofed_forest（黑森林）                 | 29  | 1.84%  |
| jungle（丛林）                        | 21  | 2.04%  | warm_ocean（暖水海洋）                  | 44  | 2.13%  |
| birch_forest_mutated（原始桦木森林）  | 155 | 2.15%  | frozen_ocean（冻洋）                    | 10  | 2.26%  |
| birch_forest（桦木森林）              | 27  | 2.29%  | desert（沙漠）                          | 2   | 2.33%  |
| deep_lukewarm_ocean（温水深海）       | 48  | 2.37%  | cold_taiga（积雪针叶林）                | 30  | 2.40%  |
| deep_cold_ocean（冷水深海）           | 49  | 2.42%  | beach（沙滩）                           | 16  | 2.45%  |
| ice_plains（雪原）                    | 12  | 2.78%  | taiga（针叶林）                         | 5   | 3.40%  |
| deep_ocean（深海）                    | 24  | 3.60%  | savanna（热带草原）                     | 35  | 3.91%  |
| lukewarm_ocean（温水海洋）            | 45  | 4.55%  | cold_ocean（冷水海洋）                  | 46  | 4.59%  |
| river（河流）                         | 7   | 6.22%  | ocean（海洋）                           | 0   | 6.87%  |
| plains（平原）                        | 1   | 10.69% | forest（森林）                          | 4   | 12.31% |
| dripstone_caves（溶洞）               | 174 | -      | lush_caves（繁茂洞穴）                  | 175 | -      |
| deep_dark（深暗之域）                 | 183 | -      | sulfur_caves（硫磺洞穴）                | 187 | -      |

> **注**：稀有度基于地表 Y=200 采样统计。地下群系（dripstone_caves、lush_caves、deep_dark、sulfur_caves）不参与稀有度排序，默认稀有度为1。

> **注**：硫磺洞穴（ID: 187）现已支持破解。请使用低 Y 坐标（Y≤60）以获得准确检测。由于缺乏稀有度数据，不推荐作为主要破解群系。

> **注意**：ChunkBase 等网站使用 Java 版群系名称，与基岩版不同。例如：Java 的 `stony_shore` 在基岩版是 `stone_beach`，Java 的 `dark_forest` 在基岩版是 `roofed_forest`。验证时请注意区分。

---

## 编译

首次使用前需根据平台运行对应脚本编译原生库。

### Windows (build.bat)

```bat
:: 需要 MinGW-w64 GCC 在 PATH 中
build.bat
:: 生成 crack_low32\crack_low32.dll、crack_high32\crack_high32.dll，
:: 以及（检测到 OpenCL SDK 时的）crack_low32\crack_low32_opencl.dll
```

**Windows GPU 编译**：脚本会自动探测 NVIDIA CUDA Toolkit / AMD APP SDK / Intel OpenCL SDK。OpenCL 运行时（`OpenCL.dll`）随显卡驱动自带。

### Linux / macOS (build.sh)

```bash
# 编译
chmod +x build.sh
./build.sh
```

**GPU版本 (OpenCL)：**

- **Ubuntu/Debian**: `sudo apt install -y ocl-icd-opencl-dev ocl-icd-libopencl1`
- **Fedora/RHEL**: `sudo dnf install -y ocl-icd-devel`
- **Arch Linux**: `sudo pacman -S ocl-icd`
- **macOS**: 系统自带 OpenCL SDK，无需额外安装

**NVIDIA GPU用户（Linux）：**

```bash
# 确保NVIDIA驱动已安装
nvidia-smi  # 检查GPU状态

# 如果OpenCL未检测到，手动配置：
sudo mkdir -p /etc/OpenCL/vendors
echo "libnvidia-opencl.so.1" | sudo tee /etc/OpenCL/vendors/nvidia.icd
```

然后重新编译：

```bash
./build.sh
# 应该看到: [OK] crack_low32_opencl.so created
```

**macOS 注意事项**：

- Apple Silicon（M1/M2/...）：脚本会自动使用 `-mcpu=native` 替代 `-march=native`
- macOS 上 OpenCL 已被弃用但仍可用；Apple Silicon GPU 的性能低于独立显卡

---

## 性能参考

测试环境：Intel Xeon Gold 6330 (112核) + NVIDIA RTX 3090

| 破解器 | 模式 | 速度    | 预计时间 (2^32) | 备注                |
| ------ | ---- | ------- | --------------- | ------------------- |
| 低32位 | GPU  | ~156M/s | **~30秒**       | RTX 3090 OpenCL加速 |
| 低32位 | CPU  | ~12M/s  | ~6 分钟         | 112核并行           |
| 高32位 | CPU  | ~432K/s | ~2.5 小时       | 16进程（自动限制）  |
| 高32位 | Java LCG | ~98K/s | ~8 分钟 (2^16) | 只需 1-2 个结构，群系验证候选缩减至 ≤ 2^16 |

**注**：

- 低32位破解支持 OpenCL GPU 加速，兼容 NVIDIA/AMD/Intel 显卡
- 旧显卡（计算单元 < 10）会自动使用 CPU 模式以确保稳定性
- 高32位破解因算法复杂度高暂不支持 GPU 加速，但可通过可选的 Java LCG 结构模式大幅加速：只需 1-2 个结构（见 [Java LCG 结构](#java-lcg-结构可选加速)）

---

## 常见问题

### 低32位破解失败

**可能原因：**

1. **结构坐标错误** - 坐标填写不正确，或区块定位方法有误
2. **结构数量不足** - 结构数量不足会导致找到过多的候选种子，建议至少提供 5 个不同类型的结构
3. **结构类型选择不当** - Linear 类型结构计算量更少，速度更快：
   - 推荐：沙漠神殿、女巫屋、丛林神庙、沉船、海底神殿、末地城
   - 复杂结构（村庄、雪屋、掠夺者前哨站、废弃传送门）也可以使用
4. **版本不兼容** - 如果目标世界是旧版本（1.18以下）生成的，结构位置可能与当前版本不同

**解决方法：**

- 核对坐标是否正确
- 增加结构数量
- 更换结构类型
- 确认目标世界的生成版本

### 高32位破解失败

**可能原因：**

1. **版本不匹配** - 群系样本的游戏版本与实际生成版本不一致
2. **低32位值错误** - 低32位破解结果不正确
3. **群系样本错误** - 坐标或群系ID填写不正确
4. **采样高度不当** - 建议 Y >= 200，避免地下群系干扰（某些地下群系可延伸至 Y=150 以上）
5. **群系样本数量不足** - 建议至少 5 个样本
6. **样本选择不当** - 应选择稀有群系（如樱花林），避免常见群系（如平原、海洋）

**解决方法：**

- 确认低32位值正确
- 核对群系样本坐标和ID
- 提高采样高度
- 选择稀有群系作为样本

### 破解时间过长

**低32位破解：** GPU约30秒，CPU约6分钟（112核）

**高32位破解（纯群系模式）：** 约2.5小时（112核，16进程）

**高32位破解（[Java LCG 模式](#java-lcg-结构可选加速)）：** Phase 2（32-47位）只需数秒；Phase 3 群系验证仅对幸存候选进行，通常数分钟内完成

如果时间明显超出：

- 检查 CPU 占用率，确认多线程正常工作
- 减少群系样本数量（但会降低准确性）
- 使用 `--test` 参数先进行小范围测试

---

## 验证种子

破解完成后，在 [ChunkBase](https://www.chunkbase.com/apps/seed-map) 验证种子是否正确。

---

## 相关链接与参考资料

- [Windows 图形界面版](../MCBEseedcracker_win_ui/README_CN.md)
- [命令行版](README_CN.md)
- [cubiomes](https://github.com/Cubitect/cubiomes) - Minecraft 群系生成模拟库，用于高32位破解中的群系计算；集成 [SeedMapper 的 fork 版本](https://github.com/xpple/SeedMapper) 支持 1.21.5+ 和 26.2+ 群系生成
- [Mersenne Twister (MT19937)](https://en.wikipedia.org/wiki/Mersenne_Twister) - 低32位破解中使用的随机数生成器，用于结构偏移计算

---

## 许可证

本项目仅供学习和研究使用。
