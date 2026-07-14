# -*- coding: utf-8 -*-
"""
Biome Icon Loader - Solid color block icons
"""
from PyQt5.QtGui import QPixmap, QIcon, QColor, QPainter
from PyQt5.QtCore import QSize, Qt

BIOME_COLORS = {
    "ocean": (0, 0, 170),
    "plains": (141, 179, 96),
    "desert": (216, 148, 64),
    "extreme_hills": (96, 96, 96),
    "forest": (77, 128, 51),
    "taiga": (102, 128, 51),
    "swamp": (107, 148, 85),
    "river": (0, 0, 255),
    "hell": (255, 0, 0),
    "the_end": (128, 128, 128),
    "frozen_ocean": (144, 144, 192),
    "frozen_river": (128, 128, 255),
    "ice_plains": (170, 200, 255),
    "snowy_mountains": (170, 200, 255),
    "mushroom_island": (255, 0, 255),
    "beach": (245, 222, 149),
    "desert_hills": (216, 148, 64),
    "wooded_hills": (77, 128, 51),
    "taiga_hills": (102, 128, 51),
    "jungle": (83, 158, 33),
    "jungle_hills": (83, 158, 33),
    "jungle_edge": (98, 158, 33),
    "deep_ocean": (0, 0, 112),
    "stone_beach": (162, 162, 132),
    "cold_beach": (250, 240, 192),
    "birch_forest": (104, 148, 64),
    "birch_forest_hills": (104, 148, 64),
    "roofed_forest": (64, 81, 26),
    "cold_taiga": (102, 140, 140),
    "mega_taiga": (89, 115, 51),
    "extreme_hills_plus_trees": (80, 112, 80),
    "savanna": (189, 178, 95),
    "savanna_plateau": (189, 178, 95),
    "mesa": (217, 134, 64),
    "mesa_plateau_stone": (176, 132, 72),
    "badlands_plateau": (200, 142, 60),
    "warm_ocean": (0, 128, 255),
    "lukewarm_ocean": (0, 96, 192),
    "cold_ocean": (32, 64, 160),
    "deep_warm_ocean": (0, 96, 192),
    "deep_lukewarm_ocean": (0, 64, 144),
    "deep_cold_ocean": (32, 48, 128),
    "deep_frozen_ocean": (64, 64, 144),
    "sunflower_plains": (181, 199, 96),
    "desert_lakes": (200, 138, 56),
    "extreme_hills_mutated": (128, 128, 128),
    "flower_forest": (77, 148, 51),
    "ice_spikes": (180, 220, 255),
    "birch_forest_mutated": (104, 158, 64),
    "redwood_taiga_mutated": (89, 125, 51),
    "savanna_mutated": (175, 168, 85),
    "mesa_bryce": (232, 148, 72),
    "bamboo_jungle": (83, 168, 33),
    "soul_sand_valley": (96, 64, 64),
    "crimson_forest": (192, 48, 48),
    "warped_forest": (48, 128, 128),
    "basalt_deltas": (64, 64, 64),
    "dripstone_caves": (128, 112, 80),
    "lush_caves": (80, 160, 80),
    "meadow": (160, 200, 96),
    "grove": (112, 144, 112),
    "snowy_slopes": (192, 216, 240),
    "jagged_peaks": (176, 192, 208),
    "frozen_peaks": (192, 208, 224),
    "stony_peaks": (144, 144, 128),
    "deep_dark": (32, 32, 48),
    "mangrove_swamp": (80, 112, 64),
    "cherry_grove": (255, 160, 192),
    "pale_garden": (160, 160, 176),
    "sulfur_caves": (200, 210, 50),
}


class BiomeIconLoader:
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
        self.icon_size = 13
    
    def _create_color_icon(self, color_rgb):
        """Create a colored square icon"""
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
    
    def get_icon(self, biome_type):
        """Get icon for a specific biome type"""
        if biome_type in self.icons:
            return self.icons[biome_type]
        
        color_rgb = BIOME_COLORS.get(biome_type)
        if not color_rgb:
            return None
        
        icon = self._create_color_icon(color_rgb)
        self.icons[biome_type] = icon
        
        return icon
    
    def has_icons(self):
        """Check if icons are available"""
        return len(BIOME_COLORS) > 0


biome_icon_loader = BiomeIconLoader()