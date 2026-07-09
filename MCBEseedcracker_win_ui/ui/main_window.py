from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStatusBar, QMenuBar,
    QMenu, QAction, QMessageBox, QSplitter,
    QLineEdit, QSpinBox, QGroupBox, QFormLayout,
    QApplication,
    QListWidget, QListWidgetItem, QComboBox, QFileDialog,
    QApplication, QTabWidget
)
from PyQt5.QtCore import Qt
from ui.widgets.structure_list_widget import StructureListWidget
from ui.widgets.biome_list_widget import BiomeListWidget
from ui.widgets.progress_widget import ProgressWidget
from ui.utils.config_manager import ConfigManager, get_base_path
from ui.utils.language_manager import lang_manager
from ui.workers.low32_worker import Low32Worker
from ui.workers.high32_worker import High32Worker
import json
import os


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.low32_worker = None
        self.high32_worker = None
        self.low32_results = []
        self.high32_results = []
        
        lang_manager.set_language(self.config_manager.get("language", "zh_CN"))
        
        self.init_ui()
        self.setup_menu()
        self.load_session_data()
        
    def retranslate_ui(self):
        self.setWindowTitle(lang_manager.get("app_name"))
        self.tab_widget.setTabText(0, lang_manager.get("low32_tab"))
        self.tab_widget.setTabText(1, lang_manager.get("high32_tab"))
        
        self.file_menu.setTitle(lang_manager.get("file_menu"))
        self.exit_action.setText(lang_manager.get("exit"))
        self.settings_menu.setTitle(lang_manager.get("settings_menu"))
        self.language_menu.setTitle(lang_manager.get("language_menu"))
        self.help_menu.setTitle(lang_manager.get("help_menu"))
        self.about_action.setText(lang_manager.get("about"))
        
        self.low32_settings_group.setTitle(lang_manager.get("advanced_settings"))
        self.low32_results_group.setTitle(lang_manager.get("results_list"))
        self.high32_settings_group.setTitle(lang_manager.get("advanced_settings"))
        self.high32_results_group.setTitle(lang_manager.get("results_list"))
        
        self.low32_test_mode_btn.setText(lang_manager.get("test_mode"))
        self.low32_full_mode_btn.setText(lang_manager.get("full_mode"))
        self.copy_low32_btn.setText(lang_manager.get("copy_selected"))
        self.export_low32_btn.setText(lang_manager.get("export_results"))
        self.start_low32_btn.setText(lang_manager.get("start_cracking"))
        self.pause_low32_btn.setText(lang_manager.get("pause"))
        self.restart_low32_btn.setText(lang_manager.get("restart"))
        
        self.high32_test_mode_btn.setText(lang_manager.get("test_mode"))
        self.high32_full_mode_btn.setText(lang_manager.get("full_mode"))
        self.copy_high32_btn.setText(lang_manager.get("copy_selected"))
        self.export_high32_btn.setText(lang_manager.get("export_results"))
        self.start_high32_btn.setText(lang_manager.get("start_cracking"))
        self.pause_high32_btn.setText(lang_manager.get("pause"))
        self.restart_high32_btn.setText(lang_manager.get("restart"))
        
        self.low32_status_label.setText(lang_manager.get("ready"))
        self.high32_status_label.setText(lang_manager.get("ready"))
        
        self.structure_list.retranslate_ui()
        self.biome_list.retranslate_ui()
        self.low32_progress.retranslate_ui()
        self.high32_progress.retranslate_ui()
        
        self.update_mc_version_combo()
        
    def init_ui(self):
        self.setWindowTitle(lang_manager.get("app_name"))
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        
        self.low32_widget = self.create_low32_panel()
        self.high32_widget = self.create_high32_panel()
        
        self.tab_widget.addTab(self.low32_widget, lang_manager.get("low32_tab"))
        self.tab_widget.addTab(self.high32_widget, lang_manager.get("high32_tab"))
        
        main_layout.addWidget(self.tab_widget)
        
    def create_low32_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.structure_list = StructureListWidget()
        layout.addWidget(self.structure_list)
        
        self.low32_progress = ProgressWidget()
        layout.addWidget(self.low32_progress)
        
        self.low32_settings_group = QGroupBox(lang_manager.get("advanced_settings"))
        settings_layout = QHBoxLayout(self.low32_settings_group)
        
        range_layout = QFormLayout()
        self.low32_start_input = QLineEdit("0")
        self.low32_start_input.setPlaceholderText("0 ~ 4294967295")
        self.low32_start_input.setToolTip(lang_manager.get("start_seed_tooltip"))
        
        self.low32_end_input = QLineEdit("4294967295")
        self.low32_end_input.setPlaceholderText("0 ~ 4294967295")
        self.low32_end_input.setToolTip(lang_manager.get("end_seed_tooltip"))
        
        range_layout.addRow(lang_manager.get("start_value"), self.low32_start_input)
        range_layout.addRow(lang_manager.get("end_value"), self.low32_end_input)
        
        settings_layout.addLayout(range_layout)
        
        mode_layout = QVBoxLayout()
        self.low32_test_mode_btn = QPushButton(lang_manager.get("test_mode"))
        self.low32_test_mode_btn.clicked.connect(self.enable_low32_test_mode)
        mode_layout.addWidget(self.low32_test_mode_btn)
        
        self.low32_full_mode_btn = QPushButton(lang_manager.get("full_mode"))
        self.low32_full_mode_btn.clicked.connect(self.enable_low32_full_mode)
        mode_layout.addWidget(self.low32_full_mode_btn)
        
        settings_layout.addLayout(mode_layout)
        
        config_layout = QFormLayout()
        self.low32_process_count_input = QSpinBox()
        self.low32_process_count_input.setRange(1, 32)
        self.low32_process_count_input.setValue(4)
        config_layout.addRow(lang_manager.get("process_count"), self.low32_process_count_input)
        
        settings_layout.addLayout(config_layout)
        
        layout.addWidget(self.low32_settings_group)
        
        self.low32_results_group = QGroupBox(lang_manager.get("results_list"))
        results_layout = QVBoxLayout(self.low32_results_group)
        self.low32_results_list = QListWidget()
        self.low32_results_list.itemDoubleClicked.connect(self.copy_low32_seed)
        results_layout.addWidget(self.low32_results_list)
        
        result_btn_layout = QHBoxLayout()
        self.copy_low32_btn = QPushButton(lang_manager.get("copy_selected"))
        self.copy_low32_btn.clicked.connect(self.copy_selected_low32_seed)
        self.export_low32_btn = QPushButton(lang_manager.get("export_results"))
        self.export_low32_btn.clicked.connect(self.export_low32_results)
        result_btn_layout.addWidget(self.copy_low32_btn)
        result_btn_layout.addWidget(self.export_low32_btn)
        results_layout.addLayout(result_btn_layout)
        
        layout.addWidget(self.low32_results_group)
        
        button_layout = QHBoxLayout()
        self.start_low32_btn = QPushButton(lang_manager.get("start_cracking"))
        self.start_low32_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.pause_low32_btn = QPushButton(lang_manager.get("pause"))
        self.pause_low32_btn.setEnabled(False)
        self.restart_low32_btn = QPushButton(lang_manager.get("restart"))
        self.restart_low32_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        
        button_layout.addWidget(self.start_low32_btn)
        button_layout.addWidget(self.pause_low32_btn)
        button_layout.addWidget(self.restart_low32_btn)
        layout.addLayout(button_layout)
        
        self.low32_status_label = QLabel(lang_manager.get("ready"))
        self.low32_status_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }")
        layout.addWidget(self.low32_status_label)
        
        self.start_low32_btn.clicked.connect(self.start_low32_cracking)
        self.pause_low32_btn.clicked.connect(self.pause_low32_cracking)
        self.restart_low32_btn.clicked.connect(self.restart_low32_cracking)
        
        return widget
    
    def create_high32_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        input_layout = QFormLayout()
        
        self.low32_value_input = QLineEdit()
        self.low32_value_input.setPlaceholderText(lang_manager.get("low32_value_placeholder"))
        input_layout.addRow(lang_manager.get("low32_value"), self.low32_value_input)
        
        self.mc_version_combo = QComboBox()
        self.update_mc_version_combo()
        self.mc_version_combo.setCurrentIndex(4)
        self.mc_version_combo.currentIndexChanged.connect(self.on_mc_version_changed)
        input_layout.addRow(lang_manager.get("mc_version"), self.mc_version_combo)
        
        layout.addLayout(input_layout)
        
        self.biome_list = BiomeListWidget()
        layout.addWidget(self.biome_list)
        
        self.high32_progress = ProgressWidget()
        layout.addWidget(self.high32_progress)
        
        self.high32_settings_group = QGroupBox(lang_manager.get("advanced_settings"))
        settings_layout = QHBoxLayout(self.high32_settings_group)
        
        range_layout = QFormLayout()
        self.high32_start_input = QLineEdit("0")
        self.high32_start_input.setPlaceholderText("0 ~ 4294967295")
        self.high32_start_input.setToolTip(lang_manager.get("start_seed_tooltip"))
        
        self.high32_end_input = QLineEdit("4294967295")
        self.high32_end_input.setPlaceholderText("0 ~ 4294967295")
        self.high32_end_input.setToolTip(lang_manager.get("end_seed_tooltip"))
        
        range_layout.addRow(lang_manager.get("start_value"), self.high32_start_input)
        range_layout.addRow(lang_manager.get("end_value"), self.high32_end_input)
        
        settings_layout.addLayout(range_layout)
        
        mode_layout = QVBoxLayout()
        self.high32_test_mode_btn = QPushButton(lang_manager.get("test_mode"))
        self.high32_test_mode_btn.clicked.connect(self.enable_high32_test_mode)
        mode_layout.addWidget(self.high32_test_mode_btn)
        
        self.high32_full_mode_btn = QPushButton(lang_manager.get("full_mode"))
        self.high32_full_mode_btn.clicked.connect(self.enable_high32_full_mode)
        mode_layout.addWidget(self.high32_full_mode_btn)
        
        settings_layout.addLayout(mode_layout)
        
        config_layout = QFormLayout()
        self.high32_process_count_input = QSpinBox()
        self.high32_process_count_input.setRange(1, 32)
        self.high32_process_count_input.setValue(4)
        config_layout.addRow(lang_manager.get("process_count"), self.high32_process_count_input)
        
        settings_layout.addLayout(config_layout)
        
        layout.addWidget(self.high32_settings_group)
        
        self.high32_results_group = QGroupBox(lang_manager.get("results_list"))
        results_layout = QVBoxLayout(self.high32_results_group)
        self.high32_results_list = QListWidget()
        self.high32_results_list.itemDoubleClicked.connect(self.copy_high32_seed)
        results_layout.addWidget(self.high32_results_list)
        
        result_btn_layout = QHBoxLayout()
        self.copy_high32_btn = QPushButton(lang_manager.get("copy_selected"))
        self.copy_high32_btn.clicked.connect(self.copy_selected_high32_seed)
        self.export_high32_btn = QPushButton(lang_manager.get("export_results"))
        self.export_high32_btn.clicked.connect(self.export_high32_results)
        result_btn_layout.addWidget(self.copy_high32_btn)
        result_btn_layout.addWidget(self.export_high32_btn)
        results_layout.addLayout(result_btn_layout)
        
        layout.addWidget(self.high32_results_group)
        
        button_layout = QHBoxLayout()
        self.start_high32_btn = QPushButton(lang_manager.get("start_cracking"))
        self.start_high32_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.pause_high32_btn = QPushButton(lang_manager.get("pause"))
        self.pause_high32_btn.setEnabled(False)
        self.restart_high32_btn = QPushButton(lang_manager.get("restart"))
        self.restart_high32_btn.setStyleSheet("background-color: #FF9800; color: white; font-weight: bold;")
        
        button_layout.addWidget(self.start_high32_btn)
        button_layout.addWidget(self.pause_high32_btn)
        button_layout.addWidget(self.restart_high32_btn)
        layout.addLayout(button_layout)
        
        self.high32_status_label = QLabel(lang_manager.get("ready"))
        self.high32_status_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 5px; border: 1px solid #ccc; }")
        layout.addWidget(self.high32_status_label)
        
        self.start_high32_btn.clicked.connect(self.start_high32_cracking)
        self.pause_high32_btn.clicked.connect(self.pause_high32_cracking)
        self.restart_high32_btn.clicked.connect(self.restart_high32_cracking)
        
        return widget
    
    def setup_menu(self):
        menubar = self.menuBar()
        
        self.file_menu = menubar.addMenu(lang_manager.get("file_menu"))
        
        self.exit_action = QAction(lang_manager.get("exit"), self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.exit_action)
        
        self.settings_menu = menubar.addMenu(lang_manager.get("settings_menu"))
        
        self.language_menu = self.settings_menu.addMenu(lang_manager.get("language_menu"))
        
        self.zh_action = QAction("中文", self)
        self.zh_action.triggered.connect(lambda: self.change_language("zh_CN"))
        self.language_menu.addAction(self.zh_action)
        
        self.en_action = QAction("English", self)
        self.en_action.triggered.connect(lambda: self.change_language("en_US"))
        self.language_menu.addAction(self.en_action)
        
        self.update_language_menu()
        
        self.help_menu = menubar.addMenu(lang_manager.get("help_menu"))
        
        self.about_action = QAction(lang_manager.get("about"), self)
        self.about_action.triggered.connect(self.show_about)
        self.help_menu.addAction(self.about_action)
    
    def start_low32_cracking(self):
        if self.high32_worker and self.high32_worker.isRunning() and not self.high32_worker.is_paused:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("high32_running_stop_first"))
            return
        
        if self.low32_worker and self.low32_worker.isRunning() and not self.low32_worker.is_paused:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("low32_running"))
            return
        
        structures = self.structure_list.get_structures()
        if not structures:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("add_structure_first"))
            return
        
        try:
            start = int(self.low32_start_input.text())
            end = int(self.low32_end_input.text())
            
            if start < 0 or start > 4294967295:
                QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("start_value_range"))
                return
            
            if end < 0 or end > 4294967295:
                QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("end_value_range"))
                return
            
            if start > end:
                QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("start_less_than_end"))
                return
                
        except ValueError:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("invalid_number"))
            return
        
        original_start = start
        progress_file = os.path.join(get_base_path(), "progress_low32.json")
        if os.path.exists(progress_file):
            print(f"[UI] Found progress file: {progress_file}")
            reply = QMessageBox.question(
                self, lang_manager.get("continue_cracking"),
                lang_manager.get("progress_detected"),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    with open(progress_file, 'r', encoding='utf-8') as f:
                        progress_data = json.load(f)
                    
                    print(f"[UI] Progress data loaded: {progress_data}")
                    
                    saved_start = progress_data.get("current_position", start)
                    original_start = progress_data.get("original_start_value", start)
                    
                    print(f"[UI] Saved start: {saved_start:,}")
                    print(f"[UI] Original start: {original_start:,}")
                    print(f"[UI] Current start: {start:,}")
                    
                    if saved_start > start:
                        start = saved_start
                        print(f"[UI] Resuming from position: {start:,}")
                        print(f"[UI] Original start value: {original_start:,}")
                    
                    total_range = end - original_start
                    progress = (start - original_start) / total_range * 100
                    print(f"[UI] Calculated progress: {progress:.2f}%")
                    self.low32_progress.update_progress(progress, 0, 0)
                    self.low32_status_label.setText(lang_manager.get("resume_from_progress_percent").format(progress))
                except Exception as e:
                    print(f"[UI ERROR] Failed to load progress: {e}")
            else:
                print(f"[UI] User chose to start from beginning, removing progress file")
                if os.path.exists(progress_file):
                    os.remove(progress_file)
        
        self.structure_list.set_enabled(False)
        self.set_low32_settings_enabled(False)
        self.start_low32_btn.setEnabled(False)
        self.pause_low32_btn.setEnabled(True)
        self.restart_low32_btn.setEnabled(True)
        
        self.start_high32_btn.setEnabled(False)
        self.pause_high32_btn.setEnabled(False)
        self.restart_high32_btn.setEnabled(True)
        
        self.low32_worker = Low32Worker(structures, start, end)
        self.low32_worker.original_start_value = original_start
        self.low32_worker.progress_updated.connect(self.update_low32_progress)
        self.low32_worker.found_seed.connect(self.add_low32_result)
        self.low32_worker.finished.connect(self.low32_finished)
        self.low32_worker.error_occurred.connect(self.show_error)
        
        self.low32_worker.start()
        self.low32_status_label.setText(lang_manager.get("start_low32_cracking"))
    
    def pause_low32_cracking(self):
        if self.low32_worker:
            text = self.pause_low32_btn.text()
            if text == lang_manager.get("pause"):
                self.low32_worker.pause()
                self.pause_low32_btn.setText(lang_manager.get("continue"))
                self.start_high32_btn.setEnabled(True)
                self.restart_high32_btn.setEnabled(True)
                self.low32_status_label.setText(lang_manager.get("cracking_paused"))
            else:
                self.low32_worker.resume()
                self.pause_low32_btn.setText(lang_manager.get("pause"))
                self.start_high32_btn.setEnabled(False)
                self.restart_high32_btn.setEnabled(False)
                self.low32_status_label.setText(lang_manager.get("cracking_resumed"))
    
    def restart_low32_cracking(self):
        reply = QMessageBox.question(
            self, lang_manager.get("confirm"),
            lang_manager.get("confirm_restart"),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            print(f"[UI] Restarting low32 cracking...")
            
            if self.low32_worker:
                print(f"[UI] Stopping worker...")
                self.low32_worker.stop()
                self.low32_worker.wait(1000)
                self.low32_worker = None
                print(f"[UI] Worker stopped and cleared")
            
            progress_low32_file = os.path.join(get_base_path(), "progress_low32.json")
            if os.path.exists(progress_low32_file):
                print(f"[UI] Removing progress file")
                os.remove(progress_low32_file)
            
            self.start_low32_btn.setEnabled(True)
            self.pause_low32_btn.setEnabled(False)
            self.pause_low32_btn.setText(lang_manager.get("pause"))
            self.restart_low32_btn.setEnabled(False)
            
            self.start_high32_btn.setEnabled(True)
            self.pause_high32_btn.setEnabled(False)
            self.restart_high32_btn.setEnabled(False)
            
            self.structure_list.set_enabled(True)
            self.set_low32_settings_enabled(True)
            self.low32_progress.reset()
            self.low32_results_list.clear()
            self.low32_results.clear()
            self.low32_status_label.setText(lang_manager.get("reset"))
            print(f"[UI] Restart complete")
    
    def start_high32_cracking(self):
        if self.low32_worker and self.low32_worker.isRunning() and not self.low32_worker.is_paused:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("low32_running_stop_first"))
            return
        
        if self.high32_worker and self.high32_worker.isRunning() and not self.high32_worker.is_paused:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("high32_running"))
            return
        
        low32_text = self.low32_value_input.text().strip()
        if not low32_text:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("input_low32_value_first"))
            return
        
        try:
            low32_value = int(low32_text)
        except ValueError:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("low32_value_must_be_integer"))
            return
        
        biomes = self.biome_list.get_biomes()
        if not biomes:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("add_biome_first"))
            return
        
        try:
            start = int(self.high32_start_input.text())
            end = int(self.high32_end_input.text())
            
            if start < 0 or start > 4294967295:
                QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("start_value_range"))
                return
            
            if end < 0 or end > 4294967295:
                QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("end_value_range"))
                return
            
            if start > end:
                QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("start_less_than_end"))
                return
                
        except ValueError:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("invalid_number"))
            return
        
        progress_file = os.path.join(get_base_path(), "progress_high32.json")
        if os.path.exists(progress_file):
            print(f"[UI] Found high32 progress file: {progress_file}")
            reply = QMessageBox.question(
                self, lang_manager.get("continue_cracking"),
                lang_manager.get("progress_detected"),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    with open(progress_file, 'r', encoding='utf-8') as f:
                        progress_data = json.load(f)
                    
                    print(f"[UI] High32 progress data loaded: {progress_data}")
                    
                    saved_start = progress_data.get("current_position", 0)
                    
                    print(f"[UI] Saved start: {saved_start:,}")
                    print(f"[UI] Current start: {start:,}")
                    
                    if saved_start > start:
                        start = saved_start
                        print(f"[UI] Resuming from position: {start:,}")
                    
                    total_range = end - 0
                    progress = (start - 0) / total_range * 100
                    print(f"[UI] Calculated progress: {progress:.2f}%")
                    self.high32_progress.update_progress(progress, 0, 0)
                    self.high32_status_label.setText(lang_manager.get("resume_from_progress_percent").format(progress))
                except Exception as e:
                    print(f"[UI ERROR] Failed to load high32 progress: {e}")
            else:
                print(f"[UI] User chose to start from beginning, removing high32 progress file")
                if os.path.exists(progress_file):
                    os.remove(progress_file)
        
        self.biome_list.set_enabled(False)
        self.set_high32_settings_enabled(False)
        self.set_high32_inputs_enabled(False)
        
        self.start_high32_btn.setEnabled(False)
        self.pause_high32_btn.setEnabled(True)
        self.restart_high32_btn.setEnabled(True)
        
        self.start_low32_btn.setEnabled(False)
        self.pause_low32_btn.setEnabled(False)
        self.restart_low32_btn.setEnabled(True)
        
        self.high32_worker = High32Worker(low32_value, biomes, start, end, mc_version=self.mc_version_combo.currentData())
        self.high32_worker.progress_updated.connect(self.update_high32_progress)
        self.high32_worker.found_seed.connect(self.add_high32_result)
        self.high32_worker.finished.connect(self.high32_finished)
        self.high32_worker.error_occurred.connect(self.show_error)
        
        self.high32_worker.start()
        self.high32_status_label.setText(lang_manager.get("start_high32_cracking"))
    
    def pause_high32_cracking(self):
        if self.high32_worker:
            text = self.pause_high32_btn.text()
            if text == lang_manager.get("pause"):
                self.high32_worker.pause()
                self.pause_high32_btn.setText(lang_manager.get("continue"))
                self.set_high32_inputs_enabled(True)
                self.start_low32_btn.setEnabled(True)
                self.restart_low32_btn.setEnabled(True)
                self.high32_status_label.setText(lang_manager.get("cracking_paused"))
            else:
                self.high32_worker.resume()
                self.pause_high32_btn.setText(lang_manager.get("pause"))
                self.set_high32_inputs_enabled(False)
                self.start_low32_btn.setEnabled(False)
                self.restart_low32_btn.setEnabled(False)
                self.high32_status_label.setText(lang_manager.get("cracking_resumed"))
    
    def restart_high32_cracking(self):
        reply = QMessageBox.question(
            self, lang_manager.get("confirm"),
            lang_manager.get("confirm_restart"),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.high32_worker:
                self.high32_worker.stop()
                self.high32_worker = None
            
            progress_high32_file = os.path.join(get_base_path(), "progress_high32.json")
            if os.path.exists(progress_high32_file):
                os.remove(progress_high32_file)
            
            self.start_high32_btn.setEnabled(True)
            self.pause_high32_btn.setEnabled(False)
            self.pause_high32_btn.setText(lang_manager.get("pause"))
            self.restart_high32_btn.setEnabled(True)
            
            self.start_low32_btn.setEnabled(True)
            self.pause_low32_btn.setEnabled(False)
            self.restart_low32_btn.setEnabled(True)
            
            self.biome_list.set_enabled(True)
            self.set_high32_settings_enabled(True)
            self.set_high32_inputs_enabled(True)
            self.high32_results_list.clear()
            self.high32_results.clear()
            self.high32_status_label.setText(lang_manager.get("reset"))
            self.pause_high32_btn.setEnabled(False)
            self.pause_high32_btn.setText(lang_manager.get("pause"))
            self.high32_progress.reset()
            self.high32_results_list.clear()
            self.high32_results.clear()
            self.high32_status_label.setText(lang_manager.get("reset"))
    
    def update_low32_progress(self, progress, speed, eta):
        self.low32_progress.update_progress(progress, speed, eta)
    
    def update_high32_progress(self, progress, speed, eta):
        self.high32_progress.update_progress(progress, speed, eta)
    
    def add_low32_result(self, seed):
        self.low32_results.append(seed)
        self.low32_results_list.addItem(f"{lang_manager.get('seed')}: {seed}")
    
    def add_high32_result(self, seed):
        self.high32_results.append(seed)
        SIGNED64_MAX = 9223372036854775807
        UINT64_MAX = 18446744073709551615
        display_seed = seed if seed <= SIGNED64_MAX else seed - UINT64_MAX - 1
        self.high32_results_list.addItem(f"{lang_manager.get('full_seed')}: {display_seed}")
    
    def low32_finished(self, results):
        self.start_low32_btn.setEnabled(True)
        self.pause_low32_btn.setEnabled(False)
        self.pause_low32_btn.setText(lang_manager.get("pause"))
        self.restart_low32_btn.setEnabled(True)
        
        self.start_high32_btn.setEnabled(True)
        self.pause_high32_btn.setEnabled(False)
        self.restart_high32_btn.setEnabled(True)
        
        self.structure_list.set_enabled(True)
        self.set_low32_settings_enabled(True)
        
        self.low32_status_label.setText(lang_manager.get("low32_finished_msg").format(len(results)))
        
        try:
            from PyQt5.QtMultimedia import QSound
            sound_path = os.path.join(os.path.dirname(__file__), "..", "sounds", "complete.wav")
            if os.path.exists(sound_path):
                QSound.play(sound_path)
            else:
                QApplication.beep()
        except:
            QApplication.beep()
    
    def high32_finished(self, results):
        self.start_high32_btn.setEnabled(True)
        self.pause_high32_btn.setEnabled(False)
        self.pause_high32_btn.setText(lang_manager.get("pause"))
        self.restart_high32_btn.setEnabled(True)
        
        self.start_low32_btn.setEnabled(True)
        self.pause_low32_btn.setEnabled(False)
        self.restart_low32_btn.setEnabled(True)
        
        self.biome_list.set_enabled(True)
        self.set_high32_settings_enabled(True)
        self.set_high32_inputs_enabled(True)
        
        self.high32_status_label.setText(lang_manager.get("high32_finished_msg").format(len(results)))
        
        try:
            from PyQt5.QtMultimedia import QSound
            sound_path = os.path.join(os.path.dirname(__file__), "..", "sounds", "complete.wav")
            if os.path.exists(sound_path):
                QSound.play(sound_path)
            else:
                QApplication.beep()
        except:
            QApplication.beep()
    
    def show_error(self, error_msg):
        QMessageBox.critical(self, lang_manager.get("error"), lang_manager.get("cracking_error_msg").format(error_msg))
        self.statusBar().showMessage(lang_manager.get("cracking_error"))
    
    def enable_low32_test_mode(self):
        self.low32_start_input.setText("0")
        self.low32_end_input.setText("100000000")
        QMessageBox.information(self, lang_manager.get("info"), lang_manager.get("test_mode_enabled"))
    
    def enable_low32_full_mode(self):
        self.low32_start_input.setText("0")
        self.low32_end_input.setText("4294967295")
        QMessageBox.information(self, lang_manager.get("info"), lang_manager.get("full_mode_enabled"))
    
    def enable_high32_test_mode(self):
        self.high32_start_input.setText("0")
        self.high32_end_input.setText("100000000")
        QMessageBox.information(self, lang_manager.get("info"), lang_manager.get("test_mode_enabled"))
    
    def enable_high32_full_mode(self):
        self.high32_start_input.setText("0")
        self.high32_end_input.setText("4294967295")
        QMessageBox.information(self, lang_manager.get("info"), lang_manager.get("full_mode_enabled"))
    
    def set_low32_settings_enabled(self, enabled):
        self.low32_start_input.setEnabled(enabled)
        self.low32_end_input.setEnabled(enabled)
        self.low32_test_mode_btn.setEnabled(enabled)
        self.low32_full_mode_btn.setEnabled(enabled)
        self.low32_process_count_input.setEnabled(enabled)
    
    def set_high32_settings_enabled(self, enabled):
        self.high32_start_input.setEnabled(enabled)
        self.high32_end_input.setEnabled(enabled)
        self.high32_test_mode_btn.setEnabled(enabled)
        self.high32_full_mode_btn.setEnabled(enabled)
        self.high32_process_count_input.setEnabled(enabled)
    
    def set_high32_inputs_enabled(self, enabled):
        self.low32_value_input.setEnabled(enabled)
        self.mc_version_combo.setEnabled(enabled)
    
    def change_language(self, lang):
        self.config_manager.set("language", lang)
        self.update_language_menu()
        QMessageBox.information(
            self, lang_manager.get("info"),
            lang_manager.get("restart_required", "语言设置已更改，重启程序后生效！")
        )
    
    def update_language_menu(self):
        current_lang = self.config_manager.get("language", "zh_CN")
        
        self.zh_action.setText("• 中文" if current_lang == "zh_CN" else "中文")
        self.en_action.setText("• English" if current_lang == "en_US" else "English")
    
    def update_mc_version_combo(self):
        self.mc_version_combo.blockSignals(True)
        
        current_data = self.mc_version_combo.currentData()
        self.mc_version_combo.clear()
        self.mc_version_combo.addItem(lang_manager.get("mc_1_17"), "1.17")
        self.mc_version_combo.addItem(lang_manager.get("mc_1_18"), "1.18")
        self.mc_version_combo.addItem(lang_manager.get("mc_1_19"), "1.19")
        self.mc_version_combo.addItem(lang_manager.get("mc_1_20"), "1.20")
        self.mc_version_combo.addItem(lang_manager.get("mc_1_21"), "1.21")
        
        if current_data:
            index = self.mc_version_combo.findData(current_data)
            if index >= 0:
                self.mc_version_combo.setCurrentIndex(index)
        
        self.mc_version_combo.blockSignals(False)
    
    def on_mc_version_changed(self):
        mc_version = self.mc_version_combo.currentData()
        self.biome_list.set_mc_version(mc_version)
        
        biomes = self.biome_list.get_biomes()
        
        if biomes:
            from ui.utils.biome_version_filter import check_biome_version_compatibility
            warnings = check_biome_version_compatibility(biomes, mc_version, self.biome_list.biome_data)
            
            if warnings:
                warning_msgs = []
                for w in warnings:
                    warning_msgs.append(w['message'])
                
                reply = QMessageBox.warning(
                    self, lang_manager.get("version_compatibility_warning"),
                    lang_manager.get("biomes_not_available").format(mc_version, "\n".join(warning_msgs)),
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    self.biome_list.clear_biomes()
    
    def show_about(self):
        QMessageBox.about(
            self, lang_manager.get("about_title"),
            f"MCBE Seed Cracker v1.0.0\n\n{lang_manager.get('about_text')}"
        )
    
    def copy_low32_seed(self, item):
        text = item.text()
        seed = text.split(": ")[1]
        clipboard = QApplication.clipboard()
        clipboard.setText(seed)
        self.statusBar().showMessage(f"{lang_manager.get('seed_copied')}: {seed}")
    
    def copy_high32_seed(self, item):
        text = item.text()
        seed = text.split(": ")[1]
        clipboard = QApplication.clipboard()
        clipboard.setText(seed)
        self.statusBar().showMessage(f"{lang_manager.get('seed_copied')}: {seed}")
    
    def copy_selected_low32_seed(self):
        current_item = self.low32_results_list.currentItem()
        if current_item:
            self.copy_low32_seed(current_item)
        else:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("select_seed_first"))
    
    def copy_selected_high32_seed(self):
        current_item = self.high32_results_list.currentItem()
        if current_item:
            self.copy_high32_seed(current_item)
        else:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("select_seed_first"))
    
    def export_low32_results(self):
        if not self.low32_results:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("no_results_to_export"))
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, lang_manager.get("export_low32_title"), "low32_results.txt", lang_manager.get("text_files")
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"{lang_manager.get('export_low32_header')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"{lang_manager.get('mc_version_label')}: {self.mc_version_combo.currentText()}\n")
                    f.write(f"{lang_manager.get('found_seeds').format(len(self.low32_results), lang_manager.get('candidate_seed'))}\n\n")
                    f.write(f"{lang_manager.get('candidate_seeds_list')}:\n")
                    for i, seed in enumerate(self.low32_results, 1):
                        f.write(f"{i}. {seed}\n")
                
                QMessageBox.information(self, lang_manager.get("success"), lang_manager.get("results_exported_msg").format(file_path))
                self.statusBar().showMessage(lang_manager.get("results_exported").format(""))
            except Exception as e:
                QMessageBox.critical(self, lang_manager.get("error"), lang_manager.get("export_failed_msg").format(str(e)))
    
    def export_high32_results(self):
        if not self.high32_results:
            QMessageBox.warning(self, lang_manager.get("warning"), lang_manager.get("no_results_to_export"))
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, lang_manager.get("export_high32_title"), "high32_results.txt", lang_manager.get("text_files")
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"{lang_manager.get('export_high32_header')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(f"{lang_manager.get('mc_version_label')}: {self.mc_version_combo.currentText()}\n")
                    f.write(f"{lang_manager.get('low32_value_label')}: {self.low32_value_input.text()}\n")
                    f.write(f"{lang_manager.get('found_seeds').format(len(self.high32_results), lang_manager.get('full_seed'))}\n\n")
                    f.write(f"{lang_manager.get('full_seeds_list')}:\n")
                    SIGNED64_MAX = 9223372036854775807
                    UINT64_MAX = 18446744073709551615
                    for i, seed in enumerate(self.high32_results, 1):
                        display_seed = seed if seed <= SIGNED64_MAX else seed - UINT64_MAX - 1
                        f.write(f"{i}. {display_seed}\n")
                
                QMessageBox.information(self, lang_manager.get("success"), lang_manager.get("results_exported_msg").format(file_path))
                self.statusBar().showMessage(lang_manager.get("results_exported").format(""))
            except Exception as e:
                QMessageBox.critical(self, lang_manager.get("error"), lang_manager.get("export_failed_msg").format(str(e)))
    
    def closeEvent(self, event):
        if self.low32_worker and self.low32_worker.isRunning():
            reply = QMessageBox.question(
                self, lang_manager.get("confirm"),
                lang_manager.get("confirm_exit_low32"),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self.low32_worker.stop()
        
        if self.high32_worker and self.high32_worker.isRunning():
            reply = QMessageBox.question(
                self, lang_manager.get("confirm"),
                lang_manager.get("confirm_exit_high32"),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self.high32_worker.stop()
        
        self.save_session_data()
    
    def save_session_data(self):
        session_data = {
            "structures": self.structure_list.get_structures(),
            "biomes": self.biome_list.get_biomes(),
            "low32_results": self.low32_results,
            "high32_results": self.high32_results,
            "low32_value": self.low32_value_input.text(),
            "low32_start_value": self.low32_start_input.text(),
            "low32_end_value": self.low32_end_input.text(),
            "high32_start_value": self.high32_start_input.text(),
            "high32_end_value": self.high32_end_input.text(),
            "mc_version": self.mc_version_combo.currentText(),
            "low32_process_count": self.low32_process_count_input.value(),
            "high32_process_count": self.high32_process_count_input.value()
        }
        
        try:
            session_file = os.path.join(get_base_path(), "session_data.json")
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] Failed to save session data: {e}")
    
    def load_session_data(self):
        session_file = os.path.join(get_base_path(), "session_data.json")
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if "structures" in data:
                    self.structure_list.structures = data["structures"]
                    self.structure_list.update_table()
                
                if "biomes" in data:
                    self.biome_list.biomes = data["biomes"]
                    self.biome_list.update_table()
                
                if "low32_results" in data:
                    self.low32_results = data["low32_results"]
                    self.low32_results_list.clear()
                    for seed in self.low32_results:
                        self.low32_results_list.addItem(f"{lang_manager.get('candidate_seed')}: {seed}")
                
                if "high32_results" in data:
                    self.high32_results = data["high32_results"]
                    self.high32_results_list.clear()
                    for seed in self.high32_results:
                        self.high32_results_list.addItem(f"{lang_manager.get('full_seed')}: {seed}")
                
                if "low32_value" in data:
                    self.low32_value_input.setText(data["low32_value"])
                
                if "low32_start_value" in data:
                    self.low32_start_input.setText(data["low32_start_value"])
                
                if "low32_end_value" in data:
                    self.low32_end_input.setText(data["low32_end_value"])
                
                if "high32_start_value" in data:
                    self.high32_start_input.setText(data["high32_start_value"])
                
                if "high32_end_value" in data:
                    self.high32_end_input.setText(data["high32_end_value"])
                
                if "mc_version" in data:
                    self.mc_version_combo.blockSignals(True)
                    index = self.mc_version_combo.findText(data["mc_version"])
                    if index >= 0:
                        self.mc_version_combo.setCurrentIndex(index)
                    self.mc_version_combo.blockSignals(False)
                
                if "low32_process_count" in data:
                    self.low32_process_count_input.setValue(data["low32_process_count"])
                
                if "high32_process_count" in data:
                    self.high32_process_count_input.setValue(data["high32_process_count"])
                
                progress_low32_file = os.path.join(get_base_path(), "progress_low32.json")
                if os.path.exists(progress_low32_file):
                    self.restore_low32_progress_ui()
                
                progress_high32_file = os.path.join(get_base_path(), "progress_high32.json")
                if os.path.exists(progress_high32_file):
                    self.restore_high32_progress_ui()
                
            except Exception as e:
                print(f"[ERROR] Failed to load session data: {e}")
    
    def restore_low32_progress_ui(self):
        try:
            print(f"[UI] Restoring low32 progress UI...")
            progress_file = os.path.join(get_base_path(), "progress_low32.json")
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            
            print(f"[UI] Progress data: {progress_data}")
            
            start = progress_data.get("start_value", 0)
            end = progress_data.get("end_value", 4294967295)
            current = progress_data.get("current_position", start)
            original_start = progress_data.get("original_start_value", start)
            
            print(f"[UI] Start: {start:,}")
            print(f"[UI] End: {end:,}")
            print(f"[UI] Current: {current:,}")
            print(f"[UI] Original start: {original_start:,}")
            
            if current >= end:
                print(f"[UI] Progress already completed, skipping restore")
                return
            
            progress = (current - original_start) / (end - original_start) * 100 if end > original_start else 0
            print(f"[UI] Calculated progress: {progress:.2f}%")
            self.low32_progress.update_progress(progress, 0, 0)
            
            self.low32_status_label.setText(lang_manager.get("progress_restored"))
            print(f"[UI] Low32 progress UI restored successfully")
            
        except Exception as e:
            print(f"[ERROR] Failed to restore low32 progress UI: {e}")
    
    def restore_high32_progress_ui(self):
        try:
            progress_file = os.path.join(get_base_path(), "progress_high32.json")
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            
            start = progress_data.get("start_value", 0)
            end = progress_data.get("end_value", 4294967295)
            current = progress_data.get("current_position", start)
            
            if current >= end:
                return
            
            progress = (current - start) / (end - start) * 100 if end > start else 0
            self.high32_progress.update_progress(progress, 0, 0)
            
            self.high32_status_label.setText(lang_manager.get("progress_restored"))
            
        except Exception as e:
            print(f"[ERROR] Failed to restore high32 progress UI: {e}")
