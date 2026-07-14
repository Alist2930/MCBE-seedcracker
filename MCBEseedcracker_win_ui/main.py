import sys
import os
import multiprocessing
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTranslator, QLocale
from ui.main_window import MainWindow
from ui.utils.config_manager import ConfigManager

multiprocessing.freeze_support()


def get_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def main():
    multiprocessing.set_start_method('spawn', force=True)
    
    app = QApplication(sys.argv)
    
    app.setApplicationName("MCBE Seed Cracker")
    app.setApplicationVersion("1.3.0")
    app.setOrganizationName("MCBE Seed Cracker")
    
    config_manager = ConfigManager()
    language = config_manager.get("language", "zh_CN")
    
    translator = QTranslator()
    if language == "zh_CN":
        translation_file = os.path.join(
            os.path.dirname(__file__),
            "ui", "resources", "translations", "zh_CN.qm"
        )
        if os.path.exists(translation_file):
            translator.load(translation_file)
            app.installTranslator(translator)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
