# 小版本功能实现计划

## 📋 实现目标

### 1. 支持Java版小版本切换
- ✅ cubiomes已支持：MC_1_21, MC_1_21_WD (Winter Drop = 1.21.4)
- ⏳ 需要添加：MC_1_21_3, MC_1_21_2, MC_1_21_1

### 2. 支持基岩版版本自动映射
- ⏳ UI显示基岩版版本
- ⏳ 后台自动映射到对应的Java版版本

### 3. 添加苍白之园版本警告
- ⏳ 选择1.21.5+时显示警告
- ⏳ 建议使用黑森林而不是苍白之园

---

## 🔍 当前版本映射关系（基于ChunkBase）

### Java版小版本

| Java版本 | cubiomes代码 | 群系支持 | 说明 |
|---------|-------------|---------|------|
| 1.21.4 | MC_1_21_WD | ✅ 苍白之园（范围较小） | Winter Drop |
| 1.21.3 | MC_1_21_3 | ❌ 无苍白之园 | 黑森林 |
| 1.21.2 | MC_1_21_2 | ❌ 无苍白之园 | 黑森林 |
| 1.21.1 | MC_1_21_1 | ❌ 无苍白之园 | 黑森林 |
| 1.21 | MC_1_21 | ❌ 无苍白之园 | 黑森林 |

### 基岩版版本自动映射

| 基岩版版本 | 对应Java版本 | cubiomes代码 | 备注 |
|-----------|------------|-------------|------|
| **26.XX** | 1.21 | MC_1_21 | 硫磺洞穴不支持 |
| **1.21.50** | 1.21.4 | MC_1_21_WD | 苍白之园范围较小 |
| **1.21.60-1.21.84** | 1.21.4 | MC_1_21_WD | 苍白之园范围扩大⚠️ |
| **1.21.90-1.21.101** | 1.21.4 | MC_1_21_WD | 苍白之园范围扩大⚠️ |
| **1.21.111-1.21.114** | 1.21.4 | MC_1_21_WD | 苍白之园范围扩大⚠️ |
| **1.21.120-1.21.132** | 1.21.4 | MC_1_21_WD | 苍白之园范围扩大⚠️ |
| **1.21.40** | 1.21.3 | MC_1_21_3 | 无苍白之园 |
| **1.21-1.21.40** | 1.21.3 | MC_1_21_3 | 无苍白之园 |
| **1.20.60-1.20.81** | 1.20 | MC_1_20 | 樱花林 |
| **1.20.0-1.20.51** | 1.20 | MC_1_20 | 樱花林 |
| **1.19** | 1.19 | MC_1_19 | 深暗古城、红树林沼泽 |
| **1.18** | 1.18 | MC_1_18 | 溶洞、繁茂洞穴 |

---

## 📊 实现步骤

### Step 1: 扩展cubiomes版本定义

**需要检查cubiomes是否已经支持MC_1_21_3等版本**

```python
# 预期的版本映射
VERSION_MAP = {
    # Java版
    "1.18": MC_1_18,
    "1.19": MC_1_19,
    "1.20": MC_1_20,
    "1.21": MC_1_21,
    "1.21.1": MC_1_21_1,  # 需确认是否存在
    "1.21.2": MC_1_21_2,  # 需确认是否存在
    "1.21.3": MC_1_21_3,  # 需确认是否存在
    "1.21.4": MC_1_21_WD,
    
    # 岩版（自动映射）
    "bedrock_26_xx": MC_1_21,
    "bedrock_1_21_50": MC_1_21_WD,
    "bedrock_1_21_60_84": MC_1_21_WD,  # ⚠️ 苍白之园警告
    ...
}
```

### Step 2: 修改WinUI版本选择器

**当前版本选择器（main_window.py）**：
```python
self.mc_version_combo.addItem(lang_manager.get("mc_1_17"), "1.17")
self.mc_version_combo.addItem(lang_manager.get("mc_1_18"), "1.18")
self.mc_version_combo.addItem(lang_manager.get("mc_1_19"), "1.19")
self.mc_version_combo.addItem(lang_manager.get("mc_1_20"), "1.20")
self.mc_version_combo.addItem(lang_manager.get("mc_1_21"), "1.21")
```

**修改后的版本选择器**：
```python
# Java版选项
self.mc_version_combo.addItem("Java 1.21.4 (Winter Drop)", "1.21.4")
self.mc_version_combo.addItem("Java 1.21.3", "1.21.3")
self.mc_version_combo.addItem("Java 1.21.2", "1.21.2")
self.mc_version_combo.addItem("Java 1.21.1", "1.21.1")
self.mc_version_combo.addItem("Java 1.21", "1.21")
self.mc_version_combo.addItem("Java 1.20", "1.20")
self.mc_version_combo.addItem("Java 1.19", "1.19")
self.mc_version_combo.addItem("Java 1.18", "1.18")

# 基岩版选项（自动映射）
self.mc_version_combo.addItem("Bedrock 26.XX (用Java 1.21)", "bedrock_26_xx")
self.mc_version_combo.addItem("Bedrock 1.21.50 (用Java 1.21.4)", "bedrock_1_21_50")
self.mc_version_combo.addItem("Bedrock 1.21.60-84 ⚠️苍白之园范围扩大", "bedrock_1_21_60_84")
self.mc_version_combo.addItem("Bedrock 1.21.90-101 ⚠️苍白之园范围扩大", "bedrock_1_21_90_101")
self.mc_version_combo.addItem("Bedrock 1.21-1.21.40 (用Java 1.21.3)", "bedrock_1_21_40")
self.mc_version_combo.addItem("Bedrock 1.20.60-81 (用Java 1.20)", "bedrock_1_20_60_81")
self.mc_version_combo.addItem("Bedrock 1.20.0-51 (用Java 1.20)", "bedrock_1_20_0_51")
self.mc_version_combo.addItem("Bedrock 1.19 (用Java 1.19)", "bedrock_1_19")
self.mc_version_combo.addItem("Bedrock 1.18 (用Java 1.18)", "bedrock_1_18")
```

### Step 3: 实现苍白之园版本警告

**在on_mc_version_changed()中添加警告**：
```python
def on_mc_version_changed(self):
    version_key = self.mc_version_combo.currentData()
    
    # 苍白之园范围扩大警告
    pale_garden_warning_versions = [
        "bedrock_1_21_60_84",
        "bedrock_1_21_90_101",
        "bedrock_1_21_111_114",
        "bedrock_1_21_120_132",
    ]
    
    if version_key in pale_garden_warning_versions:
        QMessageBox.warning(
            self,
            "苍白之园版本警告",
            "⚠️ 此版本的苍白之园生成范围比cubiomes支持的更大。\n\n"
            "如果破解失败，建议将苍白之园样本改为黑森林 (roofed_forest, ID: 29)。\n\n"
            "详情见：https://www.chunkbase.com/apps/seed-map"
        )
```

### Step 4: 修改Linux版本选择

**在crack_high32.py中添加**：
```python
# 小版本映射
VERSION_MAP = {
    "1.18": MC_1_18,
    "1.19": MC_1_19,
    "1.20": MC_1_20,
    "1.21": MC_1_21,
    "1.21.4": MC_1_21_WD,  # Winter Drop
    "1.21.3": MC_1_21_3,   # 需确认
    # 基岩版自动映射
    "bedrock_26_xx": MC_1_21,
    "bedrock_1_21_50": MC_1_21_WD,
    ...
}

MC_VERSION_STR = "1.21.4"  # 默认版本
```

---

## 🎯 实现优先级

### 🟢 高优先级（立即实现）

1. **添加Java 1.21.4选项**（Winter Drop）
   - ✅ cubiomes已支持MC_1_21_WD
   - ⏳ UI添加选项

2. **添加基岩版26.XX映射**
   - ⏳ UI显示"Bedrock 26.XX"
   - ⏳ 后台使用MC_1_21

3. **添加苍白之园警告**
   - ⏳ 识别版本显示警告
   - ⏳ 提供解决方案

### 🟡 中优先级（后续实现）

1. **添加更多Java小版本**
   - 需确认cubiomes是否支持MC_1_21_3等

2. **完善基岩版版本映射**
   - 根据ChunkBase版本列表完善映射

---

## ⚠️ 关键注意事项

### 1. cubiomes版本支持限制

**需要确认**：
- cubiomes是否支持MC_1_21_3等中间版本？
- 如果不支持，可能需要用MC_1_21代替

### 2. 苍白之园问题

**现状**：
- cubiomes的MC_1_21_WD对应Java 1.21.4
- 苍白之园生成范围较小
- 基岩版1.21.5+范围扩大，破解可能失败

**解决方案**：
- 显示警告提醒用户
- 建议使用黑森林代替苍白之园

### 3. 硫磺洞穴问题

**现状**：
- 基岩版26.XX新增硫磺洞穴
- cubiomes不支持此群系
- 使用26.XX版本可能导致破解失败

**解决方案**：
- UI显示警告
- 建议避免使用硫磺洞穴样本

---

## 📝 下一步行动

### 立即执行：

1. **检查cubiomes版本支持**
   - 查看`biomes.h`中的MC_VERSION枚举
   - 确认是否支持MC_1_21_3等

2. **修改WinUI版本选择器**
   - 添加Java小版本选项
   - 添加基岩版选项
   - 实现苍白之园警告

3. **修改Linux版本映射**
   - 扩展VERSION_MAP
   - 更新默认版本

---

**创建日期**: 2026-07-11  
**状态**: 规划完成，准备实施