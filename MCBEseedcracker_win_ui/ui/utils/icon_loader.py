# -*- coding: utf-8 -*-
"""
Icon loader base - cached icons with solid color blocks as fallback
"""
from PyQt5.QtGui import QPixmap, QIcon, QColor, QPainter


def create_color_icon(color_rgb, size):
    """Create a colored square icon"""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, False)

    color = QColor(*color_rgb)
    painter.setPen(color.darker(130))
    painter.setBrush(color)

    painter.drawRect(0, 0, size - 1, size - 1)

    painter.end()

    return QIcon(pixmap)


class ColorIconLoader:
    """Singleton icon cache keyed by type name, backed by a color table"""
    _instances = {}

    colors = {}
    icon_size = 16

    def __new__(cls):
        if cls not in cls._instances:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instances[cls] = instance
        return cls._instances[cls]

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.icons = {}

    def _load_icon(self, type_name):
        """Build the icon for a type, or None when unavailable"""
        color_rgb = self.colors.get(type_name)
        if not color_rgb:
            return None
        return create_color_icon(color_rgb, self.icon_size)

    def get_icon(self, type_name):
        """Get the cached icon for a specific type"""
        if type_name in self.icons:
            return self.icons[type_name]

        icon = self._load_icon(type_name)
        if icon is not None:
            self.icons[type_name] = icon

        return icon
