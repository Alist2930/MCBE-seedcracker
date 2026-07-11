# cubiomes维护与版本支持计划

## 📋 目录

1. [当前状况分析](#当前状况分析)
2. [小版本切换实现计划](#小版本切换实现计划)
3. [第三方工具技术栈分析](#第三方工具技术栈分析)
4. [高版本cubiomes维护计划](#高版本cubiomes维护计划)
5. [实施时间表](#实施时间表)

---

## 当前状况分析

### cubiomes停止更新情况

| 项目信息 | 详情 |
|---------|------|
| **最后更新** | 2024年11月10日 |
| **最后版本** | 4.1.2 |
| **支持版本** | Java 1.21.4 (Winter Drop) |
| **GitHub** | https://github.com/Cubitect/cubiomes |

### 版本对应关系（ChunkBase标准）

#### Java版版本对照表

| ChunkBase版本选项 | cubiomes版本代码 | 群系生成变化 | 结构生成变化 |
|------------------|-----------------|-------------|-------------|
| Java 26.2 | ❌ 不支持 | 硫磺洞穴（sulfur_caves） | 新增结构 |
| Java 26.1 | ❌ 不支持 | 无群系变化 | 代码不再混淆 |
| Java 1.21.9 - 1.21.11 | ❌ 不支持 | 无群系变化 | 新增铜箱子、铜傀儡 |
| Java 1.21.6 - 1.21.8 | ❌ 不支持 | 无群系变化 | 无结构变化 |
| Java 1.21.5 | ❌ 不支持 | **苍白之园范围扩大** | 无结构变化 |
| Java 1.21.4 | ✅ MC_1_21_4 (代码28) | 苍白之园首次加入 | 无结构变化 |
| Java 1.21.2 - 1.21.3 | ✅ MC_1_21_3 (代码27) | 无苍白之园 | 无结构变化 |
| Java 1.21 - 1.21.1 | ✅ MC_1_21 | 无苍白之园 | 无结构变化 |
| Java 1.20 | ✅ MC_1_20 | 樱花树林 | 无结构变化 |
| Java 1.19.3 - 1.19.4 | ✅ MC_1_19_4 | 无群系变化 | 无结构变化 |
| Java 1.19 - 1.19.2 | ✅ MC_1_19 | 深暗古城、红树林沼泽 | 无结构变化 |
| Java 1.18 | ✅ MC_1_18 | 溶洞、繁茂洞穴、山地群系 | 无结构变化 |

#### 基岩版版本对照表

| 基岩版版本范围 | 对应Java版本 | 群系生成差异 | 结构生成差异 |
|---------------|-------------|-------------|-------------|
| Bedrock 26.30 - 26.32 | Java 26.2 | 硫磺洞穴 | MT19937算法 |
| Bedrock 26.0 - 26.23 | Java 26.1 | 无群系差异 | MT19937算法 |
| Bedrock 1.21.120 - 1.21.132 | Java 1.21.9+ | 无群系差异 | MT19937算法 |
| Bedrock 1.21.111 - 1.21.114 | Java 1.21.6+ | 无群系差异 | MT19937算法 |
| Bedrock 1.21.90 - 1.21.101 | Java 1.21.5+ | **苍白之园范围差异** | MT19937算法 |
| Bedrock 1.21.60 - 1.21.84 | Java 1.21.5+ | 苍白之园范围差异 | MT19937算法 |
| Bedrock 1.21.50 | Java 1.21.4 | 苍白之园首次加入 | MT19937算法 |
| Bedrock 1.21 - 1.21.40 | Java 1.21.3 | 无苍白之园 | MT19937算法 |
| Bedrock 1.20.60 - 1.20.81 | Java 1.20 | 樱花树林 | MT19937算法 |
| Bedrock 1.20.0 - 1.20.51 | Java 1.20 | 樱花树林 | MT19937算法 |
| Bedrock 1.19 | Java 1.19 | 深暗古城、红树林沼泽 | MT19937算法 |
| Bedrock 1.18 | Java 1.18 | 溶洞、繁茂洞穴、山地群系 | MT19937算法 |

---

## 小版本切换实现计划

### 阶段一：Java 1.21.x小版本支持（优先级：高）

#### 需要实现的小版本

| 版本 | cubiomes代码 | 主要变化 | 实现难度 |
|-----|-------------|---------|---------|
| 1.21.4 | MC_1_21_4 (28) | 苍白之园首次加入 | ⭐ 简单（已支持） |
| 1.21.3 | MC_1_21_3 (27) | 无苍白之园 | ⭐ 简单（已支持） |
| 1.21.2 | MC_1_21_2 | 无变化 | ⭐ 简单（已支持） |
| 1.21.1 | MC_1_21 | 无变化 | ⭐ 简单（已支持） |
| 1.21 | MC_1_21 | 无变化 | ⭐ 简单（已支持） |

#### 实现方案

**WinUI版本：**
```python
# ui/data/version_codes.json
{
    "java": {
        "1.21.4": {"code": 28, "cubiomes": "MC_1_21_4"},
        "1.21.3": {"code": 27, "cubiomes": "MC_1_21_3"},
        "1.21.2": {"code": 27, "cubiomes": "MC_1_21_2"},
        "1.21.1": {"code": 27, "cubiomes": "MC_1_21"},
        "1.21": {"code": 27, "cubiomes": "MC_1_21"}
    }
}
```

**Linux版本：**
```python
# crack_high32/crack_high32.py
MC_VERSION_CODES = {
    "1.21.4": 28,  # Winter Drop
    "1.21.3": 27,
    "1.21.2": 27,
    "1.21.1": 27,
    "1.21": 27,
}
```

### 阶段二：对应基岩版版本映射（优先级：高）

#### 版本映射规则

```python
# 版本映射表
BEDROCK_TO_JAVA_MAPPING = {
    # 基岩版版本范围 -> 推荐使用的Java版本
    "26.30-26.32": "1.21.4",  # 等待cubiomes更新
    "26.0-26.23": "1.21.4",
    "1.21.120-1.21.132": "1.21.4",
    "1.21.111-1.21.114": "1.21.4",
    "1.21.90-1.21.101": "1.21.4",  # 注意苍白之园差异
    "1.21.60-1.21.84": "1.21.4",   # 注意苍白之园差异
    "1.21.50": "1.21.4",
    "1.21-1.21.40": "1.21.3",      # 无苍白之园
    "1.20.60-1.20.81": "1.20",
    "1.20.0-1.20.51": "1.20",
    "1.19": "1.19",
    "1.18": "1.18",
}
```

#### 特殊处理：苍白之园版本差异

**问题：**
- Java 1.21.4：苍白之园首次加入，范围较小
- Java 1.21.5+：苍白之园范围扩大，部分黑森林变为苍白之园
- 基岩版 1.21.50：对应Java 1.21.4
- 基岩版 1.21.60+：对应Java 1.21.5+，但cubiomes不支持

**解决方案：**
```python
def get_biome_id_for_version(biome_name, version):
    """
    根据版本返回正确的群系ID
    """
    # 如果用户在1.21.5+采集苍白之园，但cubiomes只支持到1.21.4
    if biome_name == "pale_garden" and version >= "1.21.5":
        # 提示用户：cubiomes不支持1.21.5+
        # 建议使用黑森林(roofed_forest, ID: 29)代替
        return 29  # roofed_forest
    return BIOME_IDS[biome_name]
```

### 阶段三：UI版本选择器实现（优先级：中）

#### WinUI版本选择器设计

```
版本选择界面：
┌─────────────────────────────────────┐
│ 选择MC版本：                         │
│ ┌─────────────────────────────────┐ │
│ │ Java Edition                    │ │
│ │  ├─ 1.21.4 (Winter Drop)        │ │
│ │  ├─ 1.21.3                      │ │
│ │  ├─ 1.21.2                      │ │
│ │  ├─ 1.21.1                      │ │
│ │  └─ 1.21                        │ │
│ │ Bedrock Edition                 │ │
│ │  ├─ 1.21.50 (→使用Java 1.21.4)  │ │
│ │  ├─ 1.21-1.21.40 (→使用Java 1.21.3) │
│ │  ├─ 1.20.60-1.20.81 (→使用Java 1.20) │
│ │  └─ 1.20.0-1.20.51 (→使用Java 1.20) │
│ └─────────────────────────────────┘ │
│                                     │
│ ℹ️ 提示：基岩版版本将自动映射到对应   │
│    Java版群系算法                   │
└─────────────────────────────────────┘
```

#### 实现代码示例

```python
# ui/widgets/version_selector.py

class VersionSelector(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 版本选择器
        self.version_combo = QComboBox()
        
        # 添加Java版本
        self.version_combo.addItem("Java 1.21.4 (Winter Drop)", "java:1.21.4")
        self.version_combo.addItem("Java 1.21.3", "java:1.21.3")
        # ...
        
        # 添加基岩版版本（带映射提示）
        self.version_combo.addItem("Bedrock 1.21.50 → Java 1.21.4", "bedrock:1.21.50")
        self.version_combo.addItem("Bedrock 1.21-1.21.40 → Java 1.21.3", "bedrock:1.21.40")
        # ...
        
        layout.addWidget(self.version_combo)
        self.setLayout(layout)
    
    def get_selected_version(self):
        """返回选中的版本信息"""
        version_str = self.version_combo.currentData()
        edition, version = version_str.split(":")
        
        if edition == "bedrock":
            # 基岩版自动映射到Java版
            java_version = BEDROCK_TO_JAVA_MAPPING.get(version)
            return {
                "edition": "bedrock",
                "version": version,
                "java_version": java_version,
                "cubiomes_code": MC_VERSION_CODES[java_version]
            }
        else:
            return {
                "edition": "java",
                "version": version,
                "cubiomes_code": MC_VERSION_CODES[version]
            }
```

---

## 第三方工具技术栈分析

### ChunkBase vs minecraftsearch.com

#### ChunkBase技术栈（推测）

| 组件 | 技术方案 | 说明 |
|-----|---------|------|
| **群系生成** | cubiomes（自维护） | 定期从MC源代码提取最新算法 |
| **结构生成（Java）** | 自实现Java LCG算法 | 复现Java的Random类 |
| **结构生成（Bedrock）** | 自实现MT19937算法 | 复现基岩版的MT19937 |

#### minecraftsearch.com技术栈（开源）

| 组件 | 技术方案 | GitHub | 说明 |
|-----|---------|--------|------|
| **群系生成（Java）** | cubiomes | [Cubitect/cubiomes](https://github.com/Cubitect/cubiomes) | 官方版本，支持到1.21.4 |
| **群系生成（Bedrock）** | cubiomes (Bedrock fork) | Reed A. Cartwright的分支 | 支持基岩版1.16和1.17 |
| **结构生成（Bedrock）** | bedrockified | [Earthcomputer/bedrockified](https://github.com/Earthcomputer/bedrockified) | 基岩版结构算法 |
| **结构生成（Bedrock）** | MCBEStructureFinder | [xiaohengying/MCBEStructureFinder](https://github.com/xiaohengying/MCBEStructureFinder) | 补充基岩版结构逻辑 |

### 关键发现

**minecraftsearch.com的优势：**
- ✅ 使用了专门的基岩版结构生成库（bedrockified + MCBEStructureFinder）
- ✅ 开源透明，技术栈清晰
- ✅ 持续更新到最新版本（26.2 + 硫磺洞穴）

**对我们项目的启示：**
1. **结构生成部分**：我们已经有正确的MT19937实现（与bedrockified/MCBEStructureFinder类似）
2. **群系生成部分**：可以参考minecraftsearch.com的方式，整合多个开源库
3. **版本更新**：minecraftsearch.com能够快速支持新版本，说明他们的维护策略值得学习

### 我们项目与第三方工具对比

| 功能模块 | 我们项目 | ChunkBase | minecraftsearch.com |
|---------|---------|-----------|---------------------|
| **低32位破解（结构）** | ✅ 自实现MT19937 | ✅ 自实现 | ✅ bedrockified + MCBEStructureFinder |
| **高32位破解（群系）** | ✅ cubiomes（官方） | ✅ cubiomes（自维护） | ✅ cubiomes + Bedrock fork |
| **版本支持** | ⚠️ 1.21.4止步 | ✅ 最新版本 | ✅ 最新版本 |
| **小版本切换** | ❌ 未实现 | ✅ 完整支持 | ✅ 完整支持 |
| **基岩版映射** | ⚠️ 手动选择 | ✅ 自动映射 | ✅ 自动映射 |

---

## 高版本cubiomes维护计划

### 阶段一：紧急修复 - 苍白之园1.21.5问题（优先级：紧急）

#### 问题描述

```
问题：Java 1.21.5扩大了苍白之园的生成范围
      cubiomes只支持到1.21.4（苍白之园范围较小）
结果：用户在1.21.5+采集苍白之园样本，破解失败
```

#### 解决方案

**方案A：参数调整（短期）**
```python
# 修改苍白之园的气候参数范围
PALE_GARDEN_PARAMS_1_21_5 = {
    "temperature": (-0.5, 0.5),     # 扩大范围
    "humidity": (0.4, 0.9),         # 扩大范围
    "continentalness": (0.0, 0.5),  # 扩大范围
    "erosion": (0.0, 1.0),          # 扩大范围
}
```

**方案B：群系映射（推荐）**
```python
def handle_pale_garden_sample(biome_name, version):
    """
    处理苍白之园样本的版本兼容问题
    """
    if biome_name == "pale_garden" and version >= "1.21.5":
        # 显示警告
        show_warning("""
        ⚠️ 版本兼容性警告
        
        你选择的是 1.21.5+ 版本，但选择了苍白之园样本。
        
        cubiomes库仅支持到1.21.4版本，其中苍白之园的生成范围比1.21.5+小。
        这可能导致破解失败。
        
        建议解决方案：
        1. 将苍白之园样本改为黑森林 (roofed_forest, ID: 29)
        2. 或选择其他稀有群系（樱花树林、冰刺之地等）
        
        是否继续使用苍白之园样本？
        """)
        
        if user_confirms():
            return 186  # pale_garden
        else:
            return 29   # 改用roofed_forest
    
    return BIOME_IDS[biome_name]
```

#### 实施步骤

1. **WinUI版本**：
   - 添加版本检测逻辑
   - 当用户选择1.21.5+且选择苍白之园时，显示警告对话框
   - 提供"继续"和"改用黑森林"两个选项

2. **Linux版本**：
   - 在`crack_high32.py`中添加版本检查
   - 自动将苍白之园样本转换为黑森林

3. **测试验证**：
   - 使用已知种子在1.21.5版本中采集苍白之园坐标
   - 使用黑森林样本进行破解
   - 验证破解结果

### 阶段二：Fork并建立维护分支（优先级：高）

#### 步骤1：Fork cubiomes项目

```bash
# 在GitHub上Fork https://github.com/Cubitect/cubiomes
git clone https://github.com/你的用户名/cubiomes.git
cd cubiomes

# 创建维护分支
git checkout -b feature/bedrock-support

# 添加原始仓库为上游
git remote add upstream https://github.com/Cubitect/cubiomes.git
```

#### 步骤2：添加新群系支持

**示例：添加硫磺洞穴（sulfur_caves）**

```c
// biomes.h
enum biome {
    ...
    biome_sulfur_caves = 187,  // 新增ID（需要从MC源代码确认）
};

// biomes.c
static struct biome_info_s biome_list[] = {
    ...
    {
        biome_sulfur_caves, 
        "sulfur_caves",
        /*temperature*/ 0.5,
        /*humidity*/ 0.5,
        /*continentalness*/ 0.0,
        /*erosion*/ 0.5,
        /*depth*/ -1.0,  // 地下群系
        /*weirdness*/ 0.0,
    },
};
```

#### 步骤3：获取MC源代码并提取变化

**方法1：使用DecompilerMC**
```bash
git clone https://gitcode.com/gh_mirrors/de/DecompilerMC
cd DecompilerMC
python main.py --mcversion 26.2 --side client

# 输出在 ./src/net/minecraft/world/biome/
```

**方法2：使用McDeob**
```bash
# 下载McDeob.jar
java -jar McDeob.jar
# GUI选择：version 26.2 → client → decompile
```

**方法3：使用Minecraft Dev MCP（AI辅助）**
```bash
npm install -g @mcdxai/minecraft-dev-mcp

# 让AI帮你分析源代码变化
# 例如：找出1.21.4和26.2之间的群系生成差异
```

#### 步骤4：对比并更新算法

```bash
# 对比关键文件
diff -r src_1.21.4/net/minecraft/world/biome/ src_26.2/net/minecraft/world/biome/

# 重点关注的文件：
# - Biomes.java（群系定义）
# - BiomeSource.java（群系生成逻辑）
# - Climate.java（气候参数）
# - NoiseBasedChunkGenerator.java（噪声生成器）
```

#### 步骤5：编译测试

```bash
# 编译cubiomes
make clean
make

# 运行测试
python test_biomes.py --version 26.2 --seed 12345
```

#### 步骤6：发布更新

```bash
# 提交更改
git add .
git commit -m "feat: Add sulfur_caves biome support for MC 26.2"
git push origin feature/bedrock-support

# 在GitHub上创建Pull Request或直接发布Release
```

### 阶段三：建立持续维护流程（优先级：中）

#### MC新版本发布后的工作流程

```
MC新版本发布
    ↓
[Step 1] 反编译源代码（使用DecompilerMC/McDeob）
    ↓
[Step 2] 对比群系生成算法变化
    ├─ 对比 Biomes.java
    ├─ 对比 BiomeSource.java
    ├─ 对比 Climate.java
    └─ 记录新群系ID和参数
    ↓
[Step 3] 更新你的cubiomes fork
    ├─ 添加新群系定义
    ├─ 更新气候参数
    └─ 更新生成算法（如有变化）
    ↓
[Step 4] 测试验证
    ├─ 使用已知种子测试
    ├─ 在ChunkBase对比验证
    └─ 实际游戏验证
    ↓
[Step 5] 发布更新
    ├─ 更新项目依赖引用
    ├─ 更新README版本支持说明
    └─ 发布新的Release
```

#### 维护工具箱

| 工具 | 用途 | 优先级 |
|-----|------|--------|
| **DecompilerMC** | 反编译MC源代码 | ⭐⭐⭐ 必需 |
| **McDeob** | GUI反编译工具 | ⭐⭐ 推荐 |
| **Minecraft Dev MCP** | AI辅助分析 | ⭐⭐⭐ 推荐 |
| **git diff** | 对比版本差异 | ⭐⭐⭐ 必需 |
| **ChunkBase** | 验证群系生成正确性 | ⭐⭐⭐ 必需 |

---

## 实施时间表

### 短期目标（1-2周）

| 任务 | 预计时间 | 优先级 | 负责人 |
|-----|---------|--------|--------|
| **实现Java 1.21.x小版本切换** | 3天 | ⭐⭐⭐ 紧急 | - |
| **实现基岩版版本自动映射** | 2天 | ⭐⭐⭐ 紧急 | - |
| **添加苍白之园版本警告** | 1天 | ⭐⭐⭐ 紧急 | - |
| **Fork cubiomes项目** | 0.5天 | ⭐⭐ 高 | - |
| **反编译26.2源代码** | 1天 | ⭐⭐ 高 | - |

### 中期目标（1-2月）

| 任务 | 预计时间 | 优先级 | 负责人 |
|-----|---------|--------|--------|
| **添加硫磺洞穴支持** | 1周 | ⭐⭐ 高 | - |
| **修复苍白之园参数** | 3天 | ⭐⭐ 高 | - |
| **完善WinUI版本选择器** | 1周 | ⭐ 中 | - |
| **编写版本兼容性文档** | 2天 | ⭐ 中 | - |
| **建立自动化测试流程** | 1周 | ⭐ 中 | - |

### 长期目标（3-6月）

| 任务 | 预计时间 | 优先级 | 负责人 |
|-----|---------|--------|--------|
| **建立持续维护流程** | 持续 | ⭐⭐⭐ 紧急 | - |
| **整合bedrockified库** | 2周 | ⭐ 低 | - |
| **参考MCBEStructureFinder优化结构破解** | 1周 | ⭐ 低 | - |
| **发布独立维护的cubiomes版本** | 1周 | ⭐⭐ 高 | - |

---

## 附录

### A. cubiomes版本代码对照表

```c
// 完整的版本代码列表
#define MC_1_18        18
#define MC_1_18_2      182
#define MC_1_19        19
#define MC_1_19_2      192
#define MC_1_19_3      193
#define MC_1_19_4      194
#define MC_1_20        20
#define MC_1_20_1      201
#define MC_1_20_2      202
#define MC_1_20_3      203
#define MC_1_20_4      204
#define MC_1_21        21
#define MC_1_21_1      211
#define MC_1_21_2      212
#define MC_1_21_3      213   // 代码27
#define MC_1_21_4      214   // 代码28 (Winter Drop)
// MC_1_21_5+ 暂不支持
// MC_26.XX 暂不支持
```

### B. 关键文件路径参考

```
Minecraft源代码关键文件：
src/net/minecraft/
├── world/
│   ├── biome/
│   │   ├── BiomeSource.java      # 群系生成核心逻辑
│   │   ├── Biomes.java           # 群系定义和ID
│   │   └── Climate.java          # 气候参数系统
│   └── gen/
│       ├── NoiseBasedChunkGenerator.java  # 噪声生成器
│       ├── Carving.java          # 洞穴雕刻
│       └── SurfaceRule.java      # 表面生成规则
└── data/
    └── worldgen/
        └── biome/                # 群系JSON定义

cubiomes关键文件：
cubiomes/
├── biomes.h                      # 群系定义
├── biomes.c                      # 群系参数
├── find_biome.c                  # 群系查找算法
└── util.h                        # 工具函数
```

### C. 参考资源

1. **DecompilerMC**: https://gitcode.com/gh_mirrors/de/DecompilerMC
2. **McDeob**: https://www.9minecraft.net/minecraft-java-deobfuscation-tool/
3. **Minecraft Dev MCP**: https://www.npmjs.com/package/@mcdxai/minecraft-dev-mcp
4. **cubiomes GitHub**: https://github.com/Cubitect/cubiomes
5. **bedrockified**: https://github.com/Earthcomputer/bedrockified
6. **MCBEStructureFinder**: https://github.com/xiaohengying/MCBEStructureFinder
7. **ChunkBase**: https://www.chunkbase.com/apps/seed-map
8. **minecraftsearch.com**: https://minecraftsearch.com/tools/seed-map

---

**文档版本**: 1.0  
**创建日期**: 2026-07-11  
**最后更新**: 2026-07-11  
**维护者**: [项目维护者]