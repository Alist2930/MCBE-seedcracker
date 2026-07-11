# -*- coding: utf-8 -*-
"""
Structure Icon Loader - Structure icon loader
Supports loading icons from local files, uses solid color blocks as fallback when files are missing
"""
import os
from PyQt5.QtGui import QPixmap, QIcon, QColor, QPainter
from PyQt5.QtCore import Qt

STRUCTURE_COLORS = {
    "village": (141, 179, 96),
    "mansion": (64, 81, 26),
    "end_city": (232, 201, 128),
    "ocean_monument": (64, 96, 192),
    "ancient_city": (48, 48, 64),
    "ocean_ruins": (96, 128, 176),
    "shipwreck": (160, 128, 80),
    "nether_complexes": (112, 48, 48),
    "desert_temple": (216, 180, 96),
    "igloo": (200, 220, 240),
    "swamp_hut": (128, 112, 80),
    "jungle_temple": (83, 148, 48),
}

STRUCTURE_ICON_FILES = {
    "village": "village.png",
    "mansion": "woodland-mansion.png",
    "end_city": "end-city.png",
    "ocean_monument": "ocean-monument.png",
    "ancient_city": "ancient-city.png",
    "ocean_ruins": "ocean-ruins.png",
    "shipwreck": "shipwreck.png",
    "nether_complexes": "nether-fortress.png",
    "desert_temple": "desert-temple.png",
    "igloo": "igloo.png",
    "swamp_hut": "swamp-hut.png",
    "jungle_temple": "jungle-temple.png",
}


class StructureIconLoader:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.icons = {}
        self.icon_size = 16
        self.icons_dir = os.path.join(os.path.dirname(__file__), "structure_icons")
    
    def _create_color_icon(self, color_rgb):
        """Create a colored square icon as fallback"""
        pixmap = QPixmap(self.icon_size, self.icon_size)
        pixmap.fill(QColor(0, 0, 0, 0))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, False)
        
        color = QColor(*color_rgb)
        painter.setPen(color.darker(130))
        painter.setBrush(color)
        
        painter.drawRect(0, 0, self.icon_size - 1, self.icon_size - 1)
        
        painter.end()
        
        return QIcon(pixmap)
    
    def _load_file_icon(self, structure_type):
        """Try to load icon from file"""
        filename = STRUCTURE_ICON_FILES.get(structure_type)
        if not filename:
            return None
        
        icon_path = os.path.join(self.icons_dir, filename)
        if not os.path.exists(icon_path):
            return None
        
        pixmap = QPixmap(icon_path)
        if pixmap.isNull():
            return None
        
        scaled = pixmap.scaled(
            self.icon_size, self.icon_size,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        return QIcon(scaled)
    
    def get_icon(self, structure_type):
        """Get icon for a specific structure type"""
        if structure_type in self.icons:
            return self.icons[structure_type]
        
        icon = self._load_file_icon(structure_type)
        
        if icon is None:
            color_rgb = STRUCTURE_COLORS.get(structure_type)
            if color_rgb:
                icon = self._create_color_icon(color_rgb)
        
        if icon is not None:
            self.icons[structure_type] = icon
        
        return icon
    
    def has_file_icon(self, structure_type):
        """Check if a file icon exists for the structure"""
        filename = STRUCTURE_ICON_FILES.get(structure_type)
        if not filename:
            return False
        return os.path.exists(os.path.join(self.icons_dir, filename))


structure_icon_loader = StructureIconLoader()