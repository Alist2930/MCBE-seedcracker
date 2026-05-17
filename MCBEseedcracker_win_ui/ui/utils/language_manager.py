# -*- coding: utf-8 -*-
"""
Language Manager for UI
"""

class LanguageManager:
    def __init__(self, language="zh_CN"):
        self.language = language
        self.translations = {
            "zh_CN": {
                # 应用标题
                "app_name": "MCBE 种子破解器",
                "low32_tab": "低32位破解",
                "high32_tab": "高32位破解",
                
                # 列表标题
                "structure_list": "建筑列表",
                "biome_list": "群系列表",
                "results_list": "结果列表",
                
                # 按钮文本
                "add_structure": "添加建筑",
                "remove_selected": "删除选中",
                "clear_list": "清空列表",
                "start_cracking": "开始破解",
                "pause": "暂停",
                "resume": "继续",
                "restart": "重新开始",
                "test_mode": "测试模式 (0 ~ 100M)",
                "full_mode": "全量模式 (0 ~ 4294967295)",
                "copy_selected": "复制选中",
                "export_results": "导出结果",
                
                # 高级设置
                "advanced_settings": "高级设置",
                "start_value": "起始值:",
                "end_value": "结束值:",
                "process_count": "进程数:",
                "low32_value": "低32位值:",
                "mc_version": "MC版本:",
                
                # 表格标题
                "structure_type": "建筑类型",
                "x_coord": "X坐标",
                "z_coord": "Z坐标",
                "y_coord": "Y坐标",
                "biome_type": "群系类型",
                
                # 进度信息
                "progress": "进度",
                "speed": "速度",
                "eta": "预计剩余时间",
                
                # 结果
                "seed": "种子",
                "full_seed": "完整种子",
                "candidate_seed": "候选种子",
                "seed_copied": "已复制种子",
                "low32_finished_msg": "低32位破解完成，找到 {} 个候选种子",
                "high32_finished_msg": "高32位破解完成，找到 {} 个完整种子",
                "candidate_seeds_list": "候选种子列表",
                "full_seeds_list": "完整种子列表",
                "found_seeds": "找到 {} 个{}种子",
                
                # 菜单
                "file": "文件",
                "file_menu": "文件",
                "exit": "退出",
                "settings": "设置",
                "settings_menu": "设置",
                "language": "语言",
                "language_menu": "语言",
                "chinese": "中文",
                "english": "English",
                "help": "帮助",
                "help_menu": "帮助",
                "about": "关于",
                
                # MC版本
                "mc_1_17": "1.17 (洞穴与山崖 Part 1)",
                "mc_1_18": "1.18 (洞穴与山崖 Part 2)",
                "mc_1_19": "1.19 (荒野更新)",
                "mc_1_20": "1.20 (足迹与故事)",
                "mc_1_21": "1.21 (棘巧试炼)",
                
                # 对话框标题
                "warning": "警告",
                "confirm": "确认",
                "error": "错误",
                "info": "提示",
                
                # 对话框按钮
                "yes": "是",
                "no": "否",
                "ok": "确定",
                "cancel": "取消",
                
                # 添加对话框
                "add_structure_title": "添加建筑",
                "add_biome_title": "添加群系",
                "edit_structure_title": "修改建筑",
                "edit_biome_title": "修改群系",
                "add_biome": "添加群系",
                "invalid_structure_type": "请从列表中选择一个有效的建筑类型！",
                "invalid_biome_type": "请从列表中选择一个有效的群系类型！",
                "structure_hint": "提示: 坐标只要在一个区块内即可，无需精确到方块坐标",
                "structure_recommend": "推荐使用: 沙漠神殿、女巫屋、丛林神庙（生成规则稳定）",
                "biome_hint": "提示: 群系检测需要精确的坐标，建议使用F3调试屏幕查看",
                "biome_recommend": "推荐使用: 恶地、冰刺之地、蘑菇岛（独特性高）",
                "biome_warning": "注意: 避免使用地下群系（溶洞、繁茂洞穴、深暗之域）",
                
                # 工具提示
                "start_seed_tooltip": "起始种子值（0 到 4294967295）",
                "end_seed_tooltip": "结束种子值（0 到 4294967295）",
                "low32_value_placeholder": "输入低32位值（例如：1818588773）",
                
                # 关于对话框
                "about_title": "关于",
                "about_text": "Minecraft 基岩版种子破解工具\n\n用于通过建筑位置和群系信息反推世界种子",
                
                # 文件对话框
                "export_low32_title": "导出低32位结果",
                "export_high32_title": "导出高32位结果",
                "text_files": "文本文件 (*.txt)",
                
                # 导出文件内容
                "export_low32_header": "MCBE Seed Cracker - 低32位破解结果",
                "export_high32_header": "MCBE Seed Cracker - 高32位破解结果",
                "mc_version_label": "MC版本",
                "low32_value_label": "低32位值",
                
                # 消息
                "no_structures": "请先添加至少一个建筑！",
                "no_biomes": "请先添加至少一个群系！",
                "invalid_low32": "请先输入低32位值！",
                "invalid_number": "请输入有效的数字！",
                "invalid_range": "起始值必须小于结束值！",
                "range_out_of_bounds": "值必须在 0 到 4294967295 之间！",
                "low32_running": "低32位破解正在进行中！",
                "high32_running": "高32位破解正在进行中！",
                
                # 状态消息
                "ready": "就绪",
                "cracking": "破解中...",
                "cracking_started": "开始破解...",
                "cracking_paused": "已暂停",
                "cracking_resumed": "继续破解...",
                "resuming_progress": "恢复进度中...",
                "progress_restored": "进度已恢复",
                "cracking_reset": "已重置",
                "low32_finished": "低32位破解完成，找到 {} 个候选种子",
                "high32_finished": "高32位破解完成，找到 {} 个完整种子",
                "cracking_error": "破解出错",
                "start_low32_cracking": "开始低32位破解...",
                "start_high32_cracking": "开始高32位破解...",
                "resume_from_progress_percent": "从进度 {:.2f}% 继续...",
                "continue": "继续",
                
                # 确认消息
                "confirm_restart": "确定要重新开始吗？当前进度将被清除。",
                "clear_structures": "确定要清空所有建筑吗？",
                "clear_biomes": "确定要清空所有群系吗？",
                "continue_cracking": "继续破解",
                "progress_detected": "检测到未完成的破解进度，是否继续？\n选择'No'将从头开始。",
                
                # 版本兼容性
                "version_compatibility_warning": "版本兼容性警告",
                "biome_not_available": "群系 '{}' 需要 {} 或更高版本，\n当前选择的版本是 {}。\n\n是否仍然添加此群系？",
                "biomes_not_available": "以下群系在 {} 版本中不可用：\n\n{}\n\n是否继续保留这些群系？",
                
                # 其他
                "restart_required": "语言设置已更改，重启程序后生效！",
                "test_mode_enabled": "已启用测试模式（0 ~ 100M）",
                "full_mode_enabled": "已启用全量模式（0 ~ 4294967295）",
                "resume_from_progress": "从进度 {:.2f}% 继续...",
                "reset": "已重置",
                "select_seed_first": "请先选择一个种子！",
                "no_results_to_export": "没有结果可导出！",
                "success": "成功",
                "results_exported": "结果已导出到: {}",
                "export_failed": "导出失败: {}",
                
                # 验证错误
                "high32_running_stop_first": "高32位破解正在进行中，请先停止高32位破解！",
                "low32_running": "低32位破解正在进行中！",
                "add_structure_first": "请先添加至少一个建筑！",
                "start_value_range": "起始值必须在 0 到 4294967295 之间！",
                "end_value_range": "结束值必须在 0 到 4294967295 之间！",
                "start_less_than_end": "起始值必须小于结束值！",
                "invalid_number": "请输入有效的数字！",
                "low32_running_stop_first": "低32位破解正在进行中，请先停止低32位破解！",
                "high32_running": "高32位破解正在进行中！",
                "input_low32_value_first": "请先输入低32位值！",
                "low32_value_must_be_integer": "低32位值必须是整数！",
                "add_biome_first": "请先添加至少一个群系！",
                "cracking_error_msg": "破解出错：{}",
                "results_exported_msg": "结果已导出到: {}",
                "export_failed_msg": "导出失败: {}",
                
                # 关闭确认
                "confirm_exit_low32": "低32位破解正在进行中，确定要退出吗？",
                "confirm_exit_high32": "高32位破解正在进行中，确定要退出吗？",
            },
            "en_US": {
                # App Title
                "app_name": "MCBE Seed Cracker",
                "low32_tab": "Low 32-bit Cracking",
                "high32_tab": "High 32-bit Cracking",
                
                # List Titles
                "structure_list": "Structure List",
                "biome_list": "Biome List",
                "results_list": "Results List",
                
                # Button Text
                "add_structure": "Add Structure",
                "remove_selected": "Remove Selected",
                "clear_list": "Clear List",
                "start_cracking": "Start Cracking",
                "pause": "Pause",
                "resume": "Resume",
                "restart": "Restart",
                "test_mode": "Test Mode (0 ~ 100M)",
                "full_mode": "Full Mode (0 ~ 4294967295)",
                "copy_selected": "Copy Selected",
                "export_results": "Export Results",
                
                # Advanced Settings
                "advanced_settings": "Advanced Settings",
                "start_value": "Start Value:",
                "end_value": "End Value:",
                "process_count": "Processes:",
                "low32_value": "Low 32-bit Value:",
                "mc_version": "MC Version:",
                
                # Table Headers
                "structure_type": "Structure Type",
                "x_coord": "X Coordinate",
                "z_coord": "Z Coordinate",
                "y_coord": "Y Coordinate",
                "biome_type": "Biome Type",
                
                # Progress Info
                "progress": "Progress",
                "speed": "Speed",
                "eta": "ETA",
                
                # Results
                "seed": "Seed",
                "full_seed": "Full Seed",
                "candidate_seed": "Candidate Seed",
                "seed_copied": "Seed copied",
                "low32_finished_msg": "Low 32-bit cracking completed, found {} candidate seeds",
                "high32_finished_msg": "High 32-bit cracking completed, found {} full seeds",
                "candidate_seeds_list": "Candidate Seeds List",
                "full_seeds_list": "Full Seeds List",
                "found_seeds": "Found {} {} seeds",
                
                # Menu
                "file": "File",
                "file_menu": "File",
                "exit": "Exit",
                "settings": "Settings",
                "settings_menu": "Settings",
                "language": "Language",
                "language_menu": "Language",
                "chinese": "中文",
                "english": "English",
                "help": "Help",
                "help_menu": "Help",
                "about": "About",
                
                # MC Version
                "mc_1_17": "1.17 (Caves & Cliffs Part 1)",
                "mc_1_18": "1.18 (Caves & Cliffs Part 2)",
                "mc_1_19": "1.19 (The Wild Update)",
                "mc_1_20": "1.20 (Trails & Tales)",
                "mc_1_21": "1.21 (Tricky Trials)",
                
                # Dialog Titles
                "warning": "Warning",
                "confirm": "Confirm",
                "error": "Error",
                "info": "Info",
                
                # Dialog Buttons
                "yes": "Yes",
                "no": "No",
                "ok": "OK",
                "cancel": "Cancel",
                
                # Add Dialogs
                "add_structure_title": "Add Structure",
                "add_biome_title": "Add Biome",
                "edit_structure_title": "Edit Structure",
                "edit_biome_title": "Edit Biome",
                "add_biome": "Add Biome",
                "invalid_structure_type": "Please select a valid structure type from the list!",
                "invalid_biome_type": "Please select a valid biome type from the list!",
                "structure_hint": "Tip: Coordinates only need to be within a chunk, no need to be precise to block coordinates",
                "structure_recommend": "Recommended: Desert Temple, Witch Hut, Jungle Temple (stable generation rules)",
                "biome_hint": "Tip: Biome detection requires precise coordinates, recommend using F3 debug screen",
                "biome_recommend": "Recommended: Badlands, Ice Spikes, Mushroom Island (high uniqueness)",
                "biome_warning": "Note: Avoid using underground biomes (Lush Caves, Dripstone Caves, Deep Dark)",
                
                # Tooltips
                "start_seed_tooltip": "Start seed value (0 to 4294967295)",
                "end_seed_tooltip": "End seed value (0 to 4294967295)",
                "low32_value_placeholder": "Enter low 32-bit value (e.g., 1818588773)",
                
                # About Dialog
                "about_title": "About",
                "about_text": "Minecraft Bedrock Edition Seed Cracker\n\nA tool for reverse engineering world seeds from structure locations and biome information",
                
                # File Dialogs
                "export_low32_title": "Export Low 32-bit Results",
                "export_high32_title": "Export High 32-bit Results",
                "text_files": "Text Files (*.txt)",
                
                # Export File Content
                "export_low32_header": "MCBE Seed Cracker - Low 32-bit Cracking Results",
                "export_high32_header": "MCBE Seed Cracker - High 32-bit Cracking Results",
                "mc_version_label": "MC Version",
                "low32_value_label": "Low 32-bit Value",
                
                # Messages
                "no_structures": "Please add at least one structure!",
                "no_biomes": "Please add at least one biome!",
                "invalid_low32": "Please enter a low 32-bit value!",
                "invalid_number": "Please enter a valid number!",
                "invalid_range": "Start value must be less than end value!",
                "range_out_of_bounds": "Value must be between 0 and 4294967295!",
                "low32_running": "Low 32-bit cracking is running!",
                "high32_running": "High 32-bit cracking is running!",
                
                # Status Messages
                "ready": "Ready",
                "cracking": "Cracking...",
                "cracking_started": "Cracking started...",
                "cracking_paused": "Paused",
                "cracking_resumed": "Resumed...",
                "resuming_progress": "Resuming progress...",
                "progress_restored": "Progress restored",
                "cracking_reset": "Reset",
                "low32_finished": "Low 32-bit cracking completed, found {} candidate seeds",
                "high32_finished": "High 32-bit cracking completed, found {} full seeds",
                "cracking_error": "Cracking error",
                "start_low32_cracking": "Starting low 32-bit cracking...",
                "start_high32_cracking": "Starting high 32-bit cracking...",
                "resume_from_progress_percent": "Resuming from progress {:.2f}%...",
                "continue": "Continue",
                
                # Confirm Messages
                "confirm_restart": "Are you sure you want to restart? Current progress will be cleared.",
                "clear_structures": "Are you sure you want to clear all structures?",
                "clear_biomes": "Are you sure you want to clear all biomes?",
                "continue_cracking": "Continue Cracking",
                "progress_detected": "Unfinished cracking progress detected. Continue?\nSelect 'No' to start from the beginning.",
                
                # Version Compatibility
                "version_compatibility_warning": "Version Compatibility Warning",
                "biome_not_available": "Biome '{}' requires {} or higher version,\nbut current version is {}.\n\nAdd this biome anyway?",
                "biomes_not_available": "The following biomes are not available in version {}:\n\n{}\n\nKeep these biomes?",
                
                # Others
                "restart_required": "Language setting changed. Restart the program to take effect!",
                "test_mode_enabled": "Test mode enabled (0 ~ 100M)",
                "full_mode_enabled": "Full mode enabled (0 ~ 4294967295)",
                "resume_from_progress": "Resuming from progress {:.2f}%...",
                "reset": "Reset",
                "select_seed_first": "Please select a seed first!",
                "no_results_to_export": "No results to export!",
                "success": "Success",
                "results_exported": "Results exported to: {}",
                "export_failed": "Export failed: {}",
                
                # Validation Errors
                "high32_running_stop_first": "High 32-bit cracking is in progress, please stop it first!",
                "low32_running": "Low 32-bit cracking is in progress!",
                "add_structure_first": "Please add at least one structure first!",
                "start_value_range": "Start value must be between 0 and 4294967295!",
                "end_value_range": "End value must be between 0 and 4294967295!",
                "start_less_than_end": "Start value must be less than end value!",
                "invalid_number": "Please enter a valid number!",
                "low32_running_stop_first": "Low 32-bit cracking is in progress, please stop it first!",
                "high32_running": "High 32-bit cracking is in progress!",
                "input_low32_value_first": "Please input low 32-bit value first!",
                "low32_value_must_be_integer": "Low 32-bit value must be an integer!",
                "add_biome_first": "Please add at least one biome first!",
                "cracking_error_msg": "Cracking error: {}",
                "results_exported_msg": "Results exported to: {}",
                "export_failed_msg": "Export failed: {}",
                
                # Close Confirmation
                "confirm_exit_low32": "Low 32-bit cracking is in progress, are you sure you want to exit?",
                "confirm_exit_high32": "High 32-bit cracking is in progress, are you sure you want to exit?",
            }
        }
    
    def get(self, key, *args):
        text = self.translations.get(self.language, {}).get(key, key)
        if args:
            return text.format(*args)
        return text
    
    def set_language(self, language):
        self.language = language

lang_manager = LanguageManager()
