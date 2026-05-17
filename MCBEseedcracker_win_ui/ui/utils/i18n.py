import os
from PyQt5.QtCore import QTranslator, QCoreApplication


class I18N:
    _translator = None
    _current_language = "zh_CN"
    
    @classmethod
    def init(cls, language="zh_CN"):
        cls._current_language = language
        cls.load_translation(language)
    
    @classmethod
    def load_translation(cls, language):
        if cls._translator:
            QCoreApplication.removeTranslator(cls._translator)
        
        cls._translator = QTranslator()
        
        if language != "en_US":
            translation_file = os.path.join(
                os.path.dirname(__file__),
                "..", "resources", "translations", f"{language}.qm"
            )
            
            if os.path.exists(translation_file):
                cls._translator.load(translation_file)
                QCoreApplication.installTranslator(cls._translator)
        
        cls._current_language = language
    
    @classmethod
    def get_language(cls):
        return cls._current_language
    
    @classmethod
    def tr(cls, text):
        return QCoreApplication.translate("MainWindow", text)
