# -*- coding: utf-8 -*-
"""
Structure Icon Loader - Structure icon loader
Supports loading icons from local files, uses solid color blocks as fallback when files are missing
"""
import os
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import Qt
from .icon_loader import ColorIconLoader

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
    "pillager_outpost": (120, 80, 80),
    "ruined_portal_overworld": (80, 40, 40),
    "ruined_portal_nether": (64, 32, 32),
    "buried_treasure": (255, 215, 0),
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
    "pillager_outpost": "pillager-outpost.png",
    "ruined_portal_overworld": "ruined-portal.png",
    "ruined_portal_nether": "ruined-portal.png",
    "buried_treasure": "buried-treasure.png",
}


STRUCTURE_ICONS_DIR = os.path.join(os.path.dirname(__file__), "structure_icons")


class StructureIconLoader(ColorIconLoader):
    colors = STRUCTURE_COLORS
    icon_size = 16
    icons_dir = STRUCTURE_ICONS_DIR

    def _load_file_icon(self, structure_type):
        """Try to load icon from file"""
        icon_path = self._icon_file_path(structure_type)
        if icon_path is None or not os.path.exists(icon_path):
            return None

        pixmap = QPixmap(icon_path)
        if pixmap.isNull():
            return None

        scaled = pixmap.scaled(
            self.icon_size, self.icon_size,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        return QIcon(scaled)

    def _load_icon(self, structure_type):
        icon = self._load_file_icon(structure_type)
        if icon is not None:
            return icon
        return super()._load_icon(structure_type)

    def _icon_file_path(self, structure_type):
        filename = STRUCTURE_ICON_FILES.get(structure_type)
        if not filename:
            return None
        return os.path.join(self.icons_dir, filename)

    def has_file_icon(self, structure_type):
        """Check if a file icon exists for the structure"""
        icon_path = self._icon_file_path(structure_type)
        return icon_path is not None and os.path.exists(icon_path)


structure_icon_loader = StructureIconLoader()
