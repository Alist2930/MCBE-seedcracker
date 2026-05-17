from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QGroupBox
)
from ..utils.language_manager import lang_manager


class ProgressWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.progress_group = QGroupBox(lang_manager.get("progress"))
        progress_layout = QVBoxLayout(self.progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)
        
        info_layout = QHBoxLayout()
        
        self.speed_label = QLabel(f"{lang_manager.get('speed')}: 0/s")
        self.eta_label = QLabel(f"{lang_manager.get('eta')}: --:--:--")
        self.progress_label = QLabel(f"{lang_manager.get('progress')}: 0.00%")
        
        info_layout.addWidget(self.speed_label)
        info_layout.addWidget(self.eta_label)
        info_layout.addWidget(self.progress_label)
        
        progress_layout.addLayout(info_layout)
        
        layout.addWidget(self.progress_group)
    
    def update_progress(self, value, speed=0, eta=0):
        self.progress_bar.setValue(int(value))
        self.progress_label.setText(f"{lang_manager.get('progress')}: {value:.2f}%")
        
        if speed > 0:
            if speed >= 1000000:
                speed_text = f"{lang_manager.get('speed')}: {speed/1000000:.2f}M/s"
            elif speed >= 1000:
                speed_text = f"{lang_manager.get('speed')}: {speed/1000:.2f}K/s"
            else:
                speed_text = f"{lang_manager.get('speed')}: {speed}/s"
            self.speed_label.setText(speed_text)
        
        if eta > 0:
            hours = eta // 3600
            minutes = (eta % 3600) // 60
            seconds = eta % 60
            self.eta_label.setText(f"{lang_manager.get('eta')}: {hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def reset(self):
        self.progress_bar.setValue(0)
        self.speed_label.setText(f"{lang_manager.get('speed')}: 0/s")
        self.eta_label.setText(f"{lang_manager.get('eta')}: --:--:--")
        self.progress_label.setText(f"{lang_manager.get('progress')}: 0.00%")
    
    def retranslate_ui(self):
        self.progress_group.setTitle(lang_manager.get("progress"))
        self.speed_label.setText(f"{lang_manager.get('speed')}: 0/s")
        self.eta_label.setText(f"{lang_manager.get('eta')}: --:--:--")
        self.progress_label.setText(f"{lang_manager.get('progress')}: 0.00%")
