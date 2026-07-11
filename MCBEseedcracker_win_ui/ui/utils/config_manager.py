import json
import os
import sys


def get_base_path():
    """Get absolute path of program directory"""
    if getattr(sys, 'frozen', False):
        # Path after PyInstaller packaging
        return os.path.dirname(sys.executable)
    # Development environment path
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ConfigManager:
    def __init__(self, config_file=None):
        if config_file is None:
            self.config_file = os.path.join(get_base_path(), "config.json")
        else:
            self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load config file: {e}")
                return self.get_default_config()
        else:
            return self.get_default_config()
    
    def get_default_config(self):
        return {
            "language": "zh_CN",
            "mc_version": "1.21",
            "process_count": 4,
            "low32": {
                "start": 0,
                "end": 4294967295,
                "test_mode": False
            },
            "high32": {
                "start": 0,
                "end": 4294967295,
                "test_mode": False,
                "low32_value": None
            }
        }
    
    def save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save config file: {e}")
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()
    
    def get_low32_config(self):
        return self.config.get("low32", {})
    
    def set_low32_config(self, config):
        self.config["low32"] = config
        self.save_config()
    
    def get_high32_config(self):
        return self.config.get("high32", {})
    
    def set_high32_config(self, config):
        self.config["high32"] = config
        self.save_config()