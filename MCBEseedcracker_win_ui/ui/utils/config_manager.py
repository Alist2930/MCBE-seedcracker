import json
import os
import sys
import traceback


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
        if not os.path.exists(self.config_file):
            return self.get_default_config()

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"[WARNING] Failed to load config file {self.config_file}: {e}")
            print("[WARNING] Using default configuration; the file will be overwritten on the next save")
            return self.get_default_config()

        if not isinstance(config, dict):
            print(f"[WARNING] {self.config_file} must contain a JSON object, got {type(config).__name__}")
            return self.get_default_config()

        return config
    
    def get_default_config(self):
        return {
            "language": "zh_CN",
            "mc_version": "1.21.60-26.23",
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
        """Persist the configuration

        Returns:
            True if the configuration was written, False otherwise.
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except (OSError, TypeError, ValueError) as e:
            print(f"[ERROR] Failed to save config file {self.config_file}: {e}")
            traceback.print_exc()
            return False
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        return self.save_config()
    
    def get_low32_config(self):
        return self.config.get("low32", {})
    
    def set_low32_config(self, config):
        self.config["low32"] = config
        return self.save_config()
    
    def get_high32_config(self):
        return self.config.get("high32", {})
    
    def set_high32_config(self, config):
        self.config["high32"] = config
        return self.save_config()