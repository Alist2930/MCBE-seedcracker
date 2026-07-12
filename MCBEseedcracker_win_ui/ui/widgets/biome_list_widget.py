from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QSpinBox, QDialog, QFormLayout,
    QDialogButtonBox, QGroupBox, QMessageBox, QLabel,
    QCompleter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import json
import os
from ..utils.language_manager import lang_manager
from ..utils.biome_icon_loader import biome_icon_loader


class BiomeListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.biomes = []
        self.biome_data = self.load_biome_data()
        self.mc_version = "1.21.50"  # 默认使用支持苍白之园的版本
        self.init_ui()
    
    def load_biome_data(self):
        data_file = os.path.join(
            os.path.dirname(__file__), "..", "data", "biomes.json"
        )
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "plains": {"name_zh": "平原", "name_en": "Plains", "id": 1, "rarity": {"1.18": 0.10660260, "1.19": 0.10651130, "1.20.0-51": 0.10665340, "1.20.60-81": 0.10665340, "1.21-1.21.40": 0.10665340, "1.21.50": 0.10519710}},
                "forest": {"name_zh": "森林", "name_en": "Forest", "id": 4, "rarity": {"1.18": 0.12118830, "1.19": 0.12192850, "1.20.0-51": 0.12179220, "1.20.60-81": 0.12179220, "1.21-1.21.40": 0.12179220, "1.21.50": 0.12070520}},
                "desert": {"name_zh": "沙漠", "name_en": "Desert", "id": 2, "rarity": {"1.18": 0.02353480, "1.19": 0.02318180, "1.20.0-51": 0.02315620, "1.20.60-81": 0.02315620, "1.21-1.21.40": 0.02315620, "1.21.50": 0.02471080}},
                "cherry_grove": {"name_zh": "樱花树林", "name_en": "Cherry Grove", "id": 185, "rarity": {"1.18": 1.00000000, "1.19": 1.00000000, "1.20.0-51": 0.00278580, "1.20.60-81": 0.00278580, "1.21-1.21.40": 0.00278580, "1.21.50": 0.00280480}},
                "pale_garden": {"name_zh": "苍白之园", "name_en": "Pale Garden", "id": 186, "rarity": {"1.18": 1.00000000, "1.19": 1.00000000, "1.20.0-51": 1.00000000, "1.20.60-81": 1.00000000, "1.21-1.21.40": 1.00000000, "1.21.50": 0.00078550}}
            }

    def get_biome_rarity(self, biome_name, mc_version="1.21.50"):
        """Get biome rarity for specific version"""
        try:
            if biome_name in self.biome_data:
                biome_info = self.biome_data[biome_name]
                if isinstance(biome_info, dict):
                    rarity_dict = biome_info.get('rarity', {})
                    if isinstance(rarity_dict, dict):
                        return rarity_dict.get(mc_version, 1.0)
        except Exception:
            pass
        return 1.0
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.group_box = QGroupBox(lang_manager.get("biome_list"))
        group_layout = QVBoxLayout(self.group_box)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            lang_manager.get("biome_type"),
            lang_manager.get("x_coord"),
            lang_manager.get("z_coord"),
            lang_manager.get("y_coord")
        ])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellDoubleClicked.connect(self.edit_biome)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        group_layout.addWidget(self.table)
        
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton(lang_manager.get("add_biome"))
        self.remove_btn = QPushButton(lang_manager.get("remove_selected"))
        self.clear_btn = QPushButton(lang_manager.get("clear_list"))
        
        self.add_btn.clicked.connect(self.add_biome)
        self.remove_btn.clicked.connect(self.remove_biome)
        self.clear_btn.clicked.connect(self.clear_biomes)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addWidget(self.clear_btn)
        
        group_layout.addLayout(button_layout)
        layout.addWidget(self.group_box)
    
    def retranslate_ui(self):
        self.group_box.setTitle(lang_manager.get("biome_list"))
        self.table.setHorizontalHeaderLabels([
            lang_manager.get("biome_type"),
            lang_manager.get("x_coord"),
            lang_manager.get("z_coord"),
            lang_manager.get("y_coord")
        ])
        self.add_btn.setText(lang_manager.get("add_biome"))
        self.remove_btn.setText(lang_manager.get("remove_selected"))
        self.clear_btn.setText(lang_manager.get("clear_list"))
        
        self.update_table()
    
    def add_biome(self):
        dialog = AddBiomeDialog(self.biome_data, self.mc_version, self, edit_mode=False)
        if dialog.exec_() == QDialog.Accepted:
            biome_type, x, z, y = dialog.get_data()
            
            self.biomes.append({
                "type": biome_type,
                "x": x,
                "z": z,
                "y": y
            })
            self.update_table()
    
    def set_mc_version(self, version):
        self.mc_version = version
    
    def remove_biome(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.biomes.pop(current_row)
            self.update_table()
    
    def clear_biomes(self):
        if self.biomes:
            reply = QMessageBox.question(
                self, lang_manager.get("confirm"),
                lang_manager.get("clear_biomes"),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.biomes.clear()
                self.update_table()
    
    def update_table(self):
        self.table.setRowCount(len(self.biomes))
        for i, biome in enumerate(self.biomes):
            biome_info = self.biome_data.get(biome["type"], {})
            
            if lang_manager.language == "zh_CN":
                name = f"{biome_info.get('name_zh', biome['type'])} ({biome_info.get('name_en', '')})"
            else:
                name = biome_info.get('name_en', biome['type'])
            
            item = QTableWidgetItem(name)
            
            icon = biome_icon_loader.get_icon(biome["type"])
            if icon:
                item.setIcon(icon)
            
            self.table.setItem(i, 0, item)
            self.table.setItem(i, 1, QTableWidgetItem(str(biome["x"])))
            self.table.setItem(i, 2, QTableWidgetItem(str(biome["z"])))
            self.table.setItem(i, 3, QTableWidgetItem(str(biome["y"])))
    
    def edit_biome(self, row, column):
        if row < 0 or row >= len(self.biomes):
            return
        
        biome = self.biomes[row]
        dialog = AddBiomeDialog(self.biome_data, self.mc_version, self, edit_mode=True)
        
        index = dialog.type_combo.findData(biome["type"])
        if index >= 0:
            dialog.type_combo.setCurrentIndex(index)
        dialog.x_spin.setValue(biome["x"])
        dialog.z_spin.setValue(biome["z"])
        dialog.y_spin.setValue(biome["y"])
        
        if dialog.exec_() == QDialog.Accepted:
            biome_type, x, z, y = dialog.get_data()
            self.biomes[row] = {
                "type": biome_type,
                "x": x,
                "z": z,
                "y": y
            }
            self.update_table()
    
    def set_enabled(self, enabled):
        self.add_btn.setEnabled(enabled)
        self.remove_btn.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
        self.table.blockSignals(not enabled)
    
    def get_biomes(self):
        return self.biomes


class AddBiomeDialog(QDialog):
    def __init__(self, biome_data, mc_version="1.21.50", parent=None, edit_mode=False):
        super().__init__(parent)
        self.biome_data = biome_data
        self.mc_version = mc_version
        self.edit_mode = edit_mode
        self.init_ui()
    
    def init_ui(self):
        if self.edit_mode:
            self.setWindowTitle(lang_manager.get("edit_biome_title"))
        else:
            self.setWindowTitle(lang_manager.get("add_biome_title"))
        self.setModal(True)
        self.setMinimumWidth(450)
        
        layout = QFormLayout(self)
        
        self.type_combo = QComboBox()
        self.type_combo.setEditable(True)
        self.type_combo.setInsertPolicy(QComboBox.NoInsert)
        
        completer_model = QStandardItemModel()
        # Sort by rarity (lower rarity = more rare = higher priority for seed cracking)
        try:
            sorted_biomes = sorted(self.biome_data.items(),
                                   key=lambda x: self.get_biome_rarity(x[0], self.mc_version))
        except Exception:
            # Fallback to ID sorting if rarity sorting fails
            sorted_biomes = sorted(self.biome_data.items(), key=lambda x: x[1].get('id', 999))

        for key, value in sorted_biomes:
            if lang_manager.language == "zh_CN":
                display_name = f"{value['name_zh']} ({value['name_en']}) - ID: {value['id']}"
            else:
                display_name = f"{value['name_en']} - ID: {value['id']}"
            
            self.type_combo.addItem(display_name, key)
            
            icon = biome_icon_loader.get_icon(key)
            if icon:
                self.type_combo.setItemIcon(self.type_combo.count() - 1, icon)
            
            item = QStandardItem(display_name)
            if icon:
                item.setIcon(icon)
            completer_model.appendRow(item)
        
        completer = QCompleter()
        completer.setModel(completer_model)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.popup().setIconSize(QComboBox().iconSize())
        self.type_combo.setCompleter(completer)
        
        self.type_combo.lineEdit().setPlaceholderText(
            lang_manager.get("biome_type") + "..."
        )
        
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-30000000, 30000000)
        self.x_spin.setValue(0)
        
        self.z_spin = QSpinBox()
        self.z_spin.setRange(-30000000, 30000000)
        self.z_spin.setValue(0)
        
        self.y_spin = QSpinBox()
        self.y_spin.setRange(-64, 320)
        self.y_spin.setValue(200)
        
        self.type_label = lang_manager.get("biome_type")
        self.x_label = lang_manager.get("x_coord")
        self.z_label = lang_manager.get("z_coord")
        self.y_label = lang_manager.get("y_coord")
        
        layout.addRow(f"{self.type_label}:", self.type_combo)
        layout.addRow(f"{self.x_label}:", self.x_spin)
        layout.addRow(f"{self.z_label}:", self.z_spin)
        layout.addRow(f"{self.y_label}:", self.y_spin)
        
        self.hint_label = QLabel(lang_manager.get("biome_hint"))
        self.hint_label.setStyleSheet("color: gray; font-size: 10px;")
        self.hint_label.setWordWrap(True)
        layout.addRow(self.hint_label)
        
        self.help_label = QLabel(lang_manager.get("biome_recommend"))
        self.help_label.setStyleSheet("color: #4CAF50; font-size: 10px;")
        self.help_label.setWordWrap(True)
        layout.addRow(self.help_label)
        
        self.warning_label = QLabel(lang_manager.get("biome_warning"))
        self.warning_label.setStyleSheet("color: #FF9800; font-size: 10px;")
        self.warning_label.setWordWrap(True)
        layout.addRow(self.warning_label)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def _validate_and_accept(self):
        biome_type = self._get_biome_type()
        if biome_type is None:
            QMessageBox.warning(self, lang_manager.get("warning"),
                                lang_manager.get("invalid_biome_type"))
            return
        
        # 检查群系版本兼容性
        from ui.utils.biome_version_filter import check_single_biome_version
        result = check_single_biome_version(biome_type, self.mc_version, self.biome_data)
        
        if not result['available']:
            # 低版本不存在高版本群系，直接禁止添加
            QMessageBox.critical(
                self, 
                lang_manager.get("version_compatibility_warning"),
                result['message'],
                QMessageBox.Ok
            )
            return  # 直接返回，不允许添加
        
        self.accept()
    
    def _get_biome_type(self):
        biome_type = self.type_combo.currentData()
        if biome_type is not None:
            return biome_type
        text = self.type_combo.currentText()
        for i in range(self.type_combo.count()):
            if self.type_combo.itemText(i) == text:
                return self.type_combo.itemData(i)
        return None
    
    def get_data(self):
        biome_type = self._get_biome_type()
        x = self.x_spin.value()
        z = self.z_spin.value()
        y = self.y_spin.value()
        return biome_type, x, z, y
