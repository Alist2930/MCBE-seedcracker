# -*- coding: utf-8 -*-
"""Tests for MCBEseedcracker_win_ui/ui/utils/config_manager.py"""
import json
import os
import sys

import pytest

from ui.utils.config_manager import ConfigManager, get_base_path


@pytest.fixture
def config_file(tmp_path):
    return str(tmp_path / "config.json")


class TestGetBasePath:
    def test_development_path_is_the_win_ui_root(self):
        assert os.path.basename(get_base_path()) == "MCBEseedcracker_win_ui"

    def test_frozen_path_is_the_executable_directory(self, monkeypatch):
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "executable", os.path.join("bundle", "app.exe"))

        assert get_base_path() == "bundle"


class TestLoadConfig:
    def test_defaults_when_file_missing(self, config_file):
        manager = ConfigManager(config_file)

        assert manager.config == manager.get_default_config()
        assert manager.get("language") == "zh_CN"
        assert not os.path.exists(config_file)

    def test_reads_existing_file(self, config_file):
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"language": "en_US"}, f)

        assert ConfigManager(config_file).config == {"language": "en_US"}

    def test_falls_back_to_defaults_on_corrupt_file(self, config_file, capsys):
        with open(config_file, "w", encoding="utf-8") as f:
            f.write("{corrupt")

        manager = ConfigManager(config_file)

        assert manager.config == manager.get_default_config()
        assert "Failed to load config file" in capsys.readouterr().out

    def test_default_config_path_is_next_to_the_program(self):
        assert ConfigManager().config_file == os.path.join(get_base_path(), "config.json")


class TestGetSet:
    def test_get_returns_default_for_unknown_key(self, config_file):
        assert ConfigManager(config_file).get("nope", "fallback") == "fallback"

    def test_set_persists_value_to_disk(self, config_file):
        manager = ConfigManager(config_file)

        manager.set("language", "en_US")

        assert manager.get("language") == "en_US"
        assert ConfigManager(config_file).get("language") == "en_US"

    def test_save_config_keeps_unicode_readable(self, config_file):
        manager = ConfigManager(config_file)
        manager.set("note", "群系")

        with open(config_file, "r", encoding="utf-8") as f:
            assert "群系" in f.read()

    def test_save_failure_is_reported_not_raised(self, tmp_path, capsys):
        manager = ConfigManager(str(tmp_path / "missing_dir" / "config.json"))

        manager.set("language", "en_US")

        assert "Failed to save config file" in capsys.readouterr().out
        assert manager.get("language") == "en_US"


class TestSectionAccessors:
    def test_low32_roundtrip(self, config_file):
        manager = ConfigManager(config_file)

        manager.set_low32_config({"start": 1, "end": 2, "test_mode": True})

        assert ConfigManager(config_file).get_low32_config() == {"start": 1, "end": 2, "test_mode": True}

    def test_high32_roundtrip(self, config_file):
        manager = ConfigManager(config_file)

        manager.set_high32_config({"start": 3, "low32_value": 1818588773})

        assert ConfigManager(config_file).get_high32_config() == {"start": 3, "low32_value": 1818588773}

    def test_missing_sections_return_empty_dicts(self, config_file):
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({}, f)

        manager = ConfigManager(config_file)

        assert manager.get_low32_config() == {}
        assert manager.get_high32_config() == {}
