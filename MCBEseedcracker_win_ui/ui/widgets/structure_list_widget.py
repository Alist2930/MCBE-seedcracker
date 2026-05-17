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
from ..utils.structure_icon_loader import structure_icon_loader


class StructureListWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.structures = []
        self.structure_data = self.load_structure_data()
        self.init_ui()
    
    def load_structure_data(self):
        data_file = os.path.join(
            os.path.dirname(__file__), "..", "data", "structures.json"
        )
        if os.path.exists(data_file):
            with open(data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return {
                "desert_temple": {"name_zh": "沙漠神殿", "name_en": "Desert Temple", "id": 1},
                "swamp_hut": {"name_zh": "女巫屋", "name_en": "Swamp Hut", "id": 2},
                "jungle_temple": {"name_zh": "丛林神庙", "name_en": "Jungle Temple", "id": 3},
                "ocean_monument": {"name_zh": "海底神殿", "name_en": "Ocean Monument", "id": 4},
                "end_city": {"name_zh": "末地城", "name_en": "End City", "id": 5}
            }
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.group_box = QGroupBox(lang_manager.get("structure_list"))
        group_layout = QVBoxLayout(self.group_box)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels([
            lang_manager.get("structure_type"),
            lang_manager.get("x_coord"),
            lang_manager.get("z_coord")
        ])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellDoubleClicked.connect(self.edit_structure)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        group_layout.addWidget(self.table)
        
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton(lang_manager.get("add_structure"))
        self.remove_btn = QPushButton(lang_manager.get("remove_selected"))
        self.clear_btn = QPushButton(lang_manager.get("clear_list"))
        
        self.add_btn.clicked.connect(self.add_structure)
        self.remove_btn.clicked.connect(self.remove_structure)
        self.clear_btn.clicked.connect(self.clear_structures)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addWidget(self.clear_btn)
        
        group_layout.addLayout(button_layout)
        layout.addWidget(self.group_box)
    
    def retranslate_ui(self):
        self.group_box.setTitle(lang_manager.get("structure_list"))
        self.table.setHorizontalHeaderLabels([
            lang_manager.get("structure_type"),
            lang_manager.get("x_coord"),
            lang_manager.get("z_coord")
        ])
        self.add_btn.setText(lang_manager.get("add_structure"))
        self.remove_btn.setText(lang_manager.get("remove_selected"))
        self.clear_btn.setText(lang_manager.get("clear_list"))
        
        self.update_table()
    
    def add_structure(self):
        dialog = AddStructureDialog(self.structure_data, self, edit_mode=False)
        if dialog.exec_() == QDialog.Accepted:
            structure_type, x, z = dialog.get_data()
            self.structures.append({
                "type": structure_type,
                "x": x,
                "z": z
            })
            self.update_table()
    
    def remove_structure(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.structures.pop(current_row)
            self.update_table()
    
    def clear_structures(self):
        if self.structures:
            reply = QMessageBox.question(
                self, lang_manager.get("confirm"),
                lang_manager.get("clear_structures"),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.structures.clear()
                self.update_table()
    
    def update_table(self):
        self.table.setRowCount(len(self.structures))
        for i, structure in enumerate(self.structures):
            structure_info = self.structure_data.get(structure["type"], {})
            
            if lang_manager.language == "zh_CN":
                name = f"{structure_info.get('name_zh', structure['type'])} ({structure_info.get('name_en', '')})"
            else:
                name = structure_info.get('name_en', structure['type'])
            
            item = QTableWidgetItem(name)
            
            icon = structure_icon_loader.get_icon(structure["type"])
            if icon:
                item.setIcon(icon)
            
            self.table.setItem(i, 0, item)
            self.table.setItem(i, 1, QTableWidgetItem(str(structure["x"])))
            self.table.setItem(i, 2, QTableWidgetItem(str(structure["z"])))
    
    def edit_structure(self, row, column):
        if row < 0 or row >= len(self.structures):
            return
        
        structure = self.structures[row]
        dialog = AddStructureDialog(self.structure_data, self, edit_mode=True)
        
        index = dialog.type_combo.findData(structure["type"])
        if index >= 0:
            dialog.type_combo.setCurrentIndex(index)
        dialog.x_spin.setValue(structure["x"])
        dialog.z_spin.setValue(structure["z"])
        
        if dialog.exec_() == QDialog.Accepted:
            structure_type, x, z = dialog.get_data()
            self.structures[row] = {
                "type": structure_type,
                "x": x,
                "z": z
            }
            self.update_table()
    
    def set_enabled(self, enabled):
        self.add_btn.setEnabled(enabled)
        self.remove_btn.setEnabled(enabled)
        self.clear_btn.setEnabled(enabled)
        self.table.blockSignals(not enabled)
    
    def get_structures(self):
        return self.structures


class AddStructureDialog(QDialog):
    def __init__(self, structure_data, parent=None, edit_mode=False):
        super().__init__(parent)
        self.structure_data = structure_data
        self.edit_mode = edit_mode
        self.init_ui()
    
    def init_ui(self):
        if self.edit_mode:
            self.setWindowTitle(lang_manager.get("edit_structure_title"))
        else:
            self.setWindowTitle(lang_manager.get("add_structure_title"))
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        self.type_combo = QComboBox()
        self.type_combo.setEditable(True)
        self.type_combo.setInsertPolicy(QComboBox.NoInsert)
        
        completer_model = QStandardItemModel()
        for key, value in self.structure_data.items():
            if lang_manager.language == "zh_CN":
                display_name = f"{value['name_zh']} ({value['name_en']})"
            else:
                display_name = value['name_en']
            
            self.type_combo.addItem(display_name, key)
            
            icon = structure_icon_loader.get_icon(key)
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
            lang_manager.get("structure_type") + "..."
        )
        
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-30000000, 30000000)
        self.x_spin.setValue(0)
        
        self.z_spin = QSpinBox()
        self.z_spin.setRange(-30000000, 30000000)
        self.z_spin.setValue(0)
        
        self.type_label = lang_manager.get("structure_type")
        self.x_label = lang_manager.get("x_coord")
        self.z_label = lang_manager.get("z_coord")
        
        layout.addRow(f"{self.type_label}:", self.type_combo)
        layout.addRow(f"{self.x_label}:", self.x_spin)
        layout.addRow(f"{self.z_label}:", self.z_spin)
        
        self.hint_label = QLabel(lang_manager.get("structure_hint"))
        self.hint_label.setStyleSheet("color: gray; font-size: 10px;")
        self.hint_label.setWordWrap(True)
        layout.addRow(self.hint_label)
        
        self.help_label = QLabel(lang_manager.get("structure_recommend"))
        self.help_label.setStyleSheet("color: #2196F3; font-size: 10px;")
        self.help_label.setWordWrap(True)
        layout.addRow(self.help_label)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def _validate_and_accept(self):
        if self._get_structure_type() is None:
            QMessageBox.warning(self, lang_manager.get("warning"),
                                lang_manager.get("invalid_structure_type"))
            return
        self.accept()
    
    def _get_structure_type(self):
        structure_type = self.type_combo.currentData()
        if structure_type is not None:
            return structure_type
        text = self.type_combo.currentText()
        for i in range(self.type_combo.count()):
            if self.type_combo.itemText(i) == text:
                return self.type_combo.itemData(i)
        return None
    
    def get_data(self):
        structure_type = self._get_structure_type()
        x = self.x_spin.value()
        z = self.z_spin.value()
        return structure_type, x, z
