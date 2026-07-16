# MCBE Seed Cracker UI

[English](README.md) | 简体中文

Windows 桌面应用程序版本，提供图形化界面，无需命令行操作。

---

## 项目结构

```
MCBEseedcracker_win_ui/
├── ui/                          # UI源代码
│   ├── main_window.py           # 主窗口
│   ├── workers/                 # 工作线程
│   │   ├── low32_worker.py      # 低32位破解（GPU/CPU）
│   │   └── high32_worker.py     # 高32位破解
│   ├── widgets/                 # UI组件
│   ├── data/                    # 数据文件
│   └── utils/                   # 工具类
├── crack_low32/                 # 低32位破解库
│   ├── crack_low32.c            # CPU版本源码
│   ├── crack_low32_opencl.c     # GPU版本源码
│   ├── crack_low32.cl           # OpenCL内核
│   └── compile_opencl.bat       # OpenCL编译脚本
├── crack_high32/                # 高32位破解库
│   ├── crack_high32.c           # 高32位源码
│   └── cubiomes/                # 群系生成库
├── dll/                         # 编译后的库文件
│   ├── crack_low32/
│   │   ├── crack_low32.dll      # CPU版本
│   │   ├── crack_low32_opencl.dll  # GPU版本
│   │   └── crack_low32.cl       # OpenCL内核
│   └── crack_high32/
│       └── crack_high32.dll     # 高32位库
├── compile.bat                  # 编译脚本
├── build.bat                    # PyInstaller打包脚本
├── crack_config.json            # GPU配置文件
└── main.py                      # 应用程序入口
```

---

## 功能特性

- ✅ **图形化界面** - 直观的 Windows 桌面应用
- ✅ **GPU加速** - 低32位破解支持OpenCL GPU加速（15倍速度提升）
- ✅ **低32位破解** - 使用建筑坐标破解种子低32位
- ✅ **高32位破解** - 使用群系样本破解种子高32位
- ✅ **进度保存/恢复** - 支持中断后继续破解
- ✅ **中英文切换** - 支持中文和英文界面
- ✅ **小版本支持** - 支持基岩版小版本选择（如 1.21.50, 1.21-1.21.40）

### GPU加速（低32位破解）

**自动检测并使用GPU，如不可用自动回退到CPU模式。**

| 特性             | GPU模式       | CPU模式      |
| ---------------- | ------------- | ------------ |
| **速度**         | ~150M seeds/s | ~10M seeds/s |
| **完整范围时间** | ~30秒         | ~7分钟       |
| **性能提升**     | **15倍加速**  | 基准         |

**GPU要求：**

- NVIDIA GPU，Compute Capability 2.0+（Fermi架构或更新）
- AMD GPU，支持OpenCL 1.1+
- **推荐**：RTX 20/30/40系列以获得最佳性能

**旧显卡行为：**

- Compute units < 10的显卡（如MX330、GTX 550 Ti）会自动检测并使用CPU模式
- 状态栏显示当前计算设备（GPU/CPU）
- 无需手动配置

**配置文件：**

编辑应用程序目录中的 `crack_config.json`：

```json
{
  "use_gpu": true,
  "auto_fallback": true,
  "seeds_per_thread": 256,
  "max_results": 10000
}
```

---

## 使用说明

### 1. 低32位破解（建筑坐标）

1. 在游戏中收集建筑坐标（推荐 5 个不同类型的建筑）
2. 点击「添加建筑」按钮，输入建筑类型和坐标
3. 选择破解范围（测试模式 0-100M 或全量模式 0-4.3B）
4. 点击「开始破解」
5. 等待破解完成，查看候选低32位值

**支持的建筑类型：**

| 建筑类型         | 中文名            | 分布类型   |
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

> **提示**：优先使用 linear 类型建筑（如沙漠神殿、女巫小屋），计算量更小，破解更快。

**坐标只要是在一个区块内都行。**

**建筑定位区块确定方法：**

- **沙漠神殿**：中心位置所在的区块
- **海底神殿**：中心位置所在的区块
- **女巫屋**：建筑占区块面积最大的区块
- **丛林神庙**：建筑占区块面积最大的区块
- **末地城**：入口潜影贝方形结构占区块面积最大的区块
- **沉船**：完整沉船取船头所在区块（船头大概是刚好顶到区块边界的那端），残缺沉船取船占区块面积最大的区块

### 2. 高32位破解（群系样本）

> **重要**：群系样本必须使用**主世界（Overworld）**的群系，不要使用下界、末地等其他维度的群系。

1. 在游戏中收集群系样本坐标（推荐 5 个不同群系）
2. **选择基岩版版本**（见下方版本对应表）
3. 点击「添加群系」按钮，输入坐标和群系类型
4. 输入低32位值（从低32位破解结果获取）
5. 点击「开始破解」
6. 等待破解完成，查看完整种子

#### 版本对应关系

| 基岩版版本          | 对应 Java 版本            | 支持的群系                  |
| ------------------- | ------------------------- | --------------------------- |
| **26.30+**          | Java 26.2 (Chaos Cubed)   | ✅ 硫磺洞穴（新地下群系）   |
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

**最新版本（基岩版 26.30+）**：

- 对应 Java 26.2（混沌立方更新）
- 新增群系：硫磺洞穴（ID: 187）
- 洞穴群系破解需使用低 Y 坐标（Y≤60）
- 推荐：使用地表群系进行破解（有稀有度数据）

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

#### 重要限制

**高32位破解功能基于 cubiomes 库，支持到 Java 版 1.21.11（通过社区 fork 版本）。**

| cubiomes 信息  | 详情                                          |
| -------------- | --------------------------------------------- |
| 最新版本       | 4.1.2 (fork 版本)                             |
| 最后更新       | 2025年1月 (fork 版本)                         |
| 支持的最高版本 | Java 版 1.21.5-1.21.11 (基岩版 1.21.60-26.23) |

**cubiomes 更新状态：**

- 官方 cubiomes 在 2024年11月后停止更新
- 集成 SeedMapper 的 cubiomes fork 版本支持 1.21.5+ 和 26.2+
- 支持苍白之园（1.21.50+）和硫磺洞穴（26.30+）

#### 版本选择建议

- **最新版本优先**：建议选择你游戏实际使用的版本
- **群系版本匹配**：确保选择的版本支持你采集的群系
- **默认推荐**：程序默认选择 1.21.60-26.23（最新版本，苍白之园范围扩大）

**主世界群系ID参考（1.21.60-26.23）**

| 群系                     | ID  | 稀有度 | 群系                  | ID  | 稀有度 |
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

---

> **注**：稀有度基于地表 Y=200 采样统计。地下群系（dripstone_caves、lush_caves、deep_dark、sulfur_caves）不参与稀有度排序，默认稀有度为1。

> **注**：硫磺洞穴（ID: 187）现已支持破解。请使用低 Y 坐标（Y≤60）以获得准确检测。由于缺乏稀有度数据，不推荐作为主要破解群系。

> **注意**：ChunkBase 等网站使用 Java 版群系名称，与基岩版不同。例如：Java 的 `stony_shore` 在基岩版是 `stone_beach`，Java 的 `dark_forest` 在基岩版是 `roofed_forest`。验证时请注意区分。

## 性能参考

测试环境：Intel Xeon Gold 6330 (112核) + NVIDIA RTX 3090

| 破解器 | 模式 | 速度    | 预计时间 (2^32) | 备注                |
| ------ | ---- | ------- | --------------- | ------------------- |
| 低32位 | GPU  | ~156M/s | **~30秒**       | RTX 3090 OpenCL加速 |
| 低32位 | CPU  | ~12M/s  | ~6 分钟         | 112核并行           |
| 高32位 | CPU  | ~250K/s | ~5 小时         | 32进程（自动限制）  |

**注**：旧显卡（计算单元 < 10）会自动使用CPU模式以确保稳定性。

---

## 项目结构

```
MCBEseedcracker_win_ui/
├── main.py                  # 主程序入口
├── ui/
│   ├── main_window.py       # 主窗口
│   ├── widgets/             # 自定义组件
│   │   ├── biome_list_widget.py
│   │   ├── structure_list_widget.py
│   │   └── progress_widget.py
│   ├── workers/             # 后台任务
│   │   ├── low32_worker.py
│   │   └── high32_worker.py
│   ├── utils/               # 工具函数
│   │   ├── crack_engine.py
│   │   ├── crack_high32_engine.py
│   │   ├── i18n.py
│   │   └── ...
│   ├── data/                # 数据文件
│   │   ├── biomes.json
│   │   └── structures.json
│   └── resources/           # 资源文件
│       └── translations/    # 翻译文件
├── dll/                     # 预编译 DLL
│   ├── crack_low32/
│   └── crack_high32/
├── build.spec               # PyInstaller 配置
└── requirements.txt         # Python 依赖
```

---

## 编译说明

### 前置要求

1. **GCC编译器**：[MinGW-w64](https://github.com/niXman/mingw-builds-binaries/releases) 或 TDM-GCC
2. **OpenCL支持**（GPU可选）：[CUDA Toolkit](https://developer.nvidia.com/cuda-downloads)

### 编译DLL

运行编译脚本：

```cmd
compile.bat
```

这将生成：

- `dll/crack_low32/crack_low32.dll` - CPU版本
- `dll/crack_low32/crack_low32_opencl.dll` - GPU版本（如已安装CUDA）
- `dll/crack_high32/crack_high32.dll` - 高32位库

### 手动编译

**低32位（CPU）：**

```cmd
cd crack_low32
gcc -O3 -shared -fPIC -o crack_low32.dll crack_low32.c -lgomp
```

**低32位（GPU）：**

```cmd
cd crack_low32
gcc -O3 -shared -fPIC -o crack_low32_opencl.dll crack_low32_opencl.c -I"CUDA_PATH\include" -lOpenCL
```

**高32位：**

```cmd
cd crack_high32
gcc -O3 -shared -fPIC -o crack_high32.dll crack_high32.c -Icubiomes -lgomp
```

---

## 从源码运行 / 打包说明

### 从源码运行

```bash
# 安装依赖
pip install PyQt5

# 运行程序
python main.py
```

### 打包可执行文件

如需自行打包可执行文件：

```bash
# 安装依赖
pip install PyQt5 pyinstaller

# 打包
pyinstaller build.spec --noconfirm
```

打包结果位于 `dist/MCBE Seed Cracker/` 目录。

---

## 常见问题

### 低32位破解失败

**可能原因：**

1. **建筑坐标错误** - 坐标填写不正确，或区块定位方法有误
2. **建筑数量不足** - 建筑数量不足会导致找到过多的候选种子，建议至少提供 5 个不同类型的建筑
3. **建筑类型选择不当** - 某些建筑（如村庄）生成规则复杂，建议优先使用：
   - 沙漠神殿、女巫屋、丛林神庙（生成规则简单稳定）
   - 海底神殿、末地城
4. **版本不兼容** - 如果目标世界是旧版本（1.18以下）生成的，建筑位置可能与当前版本不同

**解决方法：**

- 核对坐标是否正确
- 增加建筑数量
- 更换建筑类型
- 确认目标世界的生成版本

### 高32位破解失败

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

---

## 相关链接

- [cubiomes](https://github.com/Cubitect/cubiomes) - Minecraft 群系生成模拟库，用于高32位破解中的群系计算；集成 [SeedMapper 的 fork 版本](https://github.com/xpple/SeedMapper) 支持 1.21.5+ 和 26.2+ 群系生成
- [Mersenne Twister (MT19937)](https://en.wikipedia.org/wiki/Mersenne_Twister) - 低32位破解中使用的随机数生成器，用于结构偏移计算

---

## 许可证

本项目仅供学习和研究使用。
