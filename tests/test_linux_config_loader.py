# -*- coding: utf-8 -*-
"""Tests for MCBEseedcracker_linux/config_loader.py"""
import json
from pathlib import Path

import pytest


def config_path(module):
    return Path(module.__file__).parent / "config.json"


class TestLoadConfig:
    def test_creates_default_config_when_missing(self, config_loader):
        assert not config_path(config_loader).exists()

        config = config_loader.load_config()

        written = json.loads(config_path(config_loader).read_text(encoding="utf-8"))
        assert written == config
        assert set(config) == {"low32", "high32"}
        assert len(config["low32"]["targets"]) == 5
        assert len(config["high32"]["samples"]) == 5

    def test_reads_existing_config(self, config_loader):
        config_path(config_loader).write_text(
            json.dumps({"low32": {"start": 42}}), encoding="utf-8"
        )

        assert config_loader.load_config() == {"low32": {"start": 42}}

    def test_exits_on_invalid_json(self, config_loader):
        config_path(config_loader).write_text("{not valid json", encoding="utf-8")

        with pytest.raises(SystemExit) as exc_info:
            config_loader.load_config()

        assert exc_info.value.code == 1

    def test_exits_on_unreadable_config(self, config_loader, monkeypatch):
        config_path(config_loader).write_text("{}", encoding="utf-8")

        def boom(*args, **kwargs):
            raise OSError("permission denied")

        monkeypatch.setattr("builtins.open", boom)

        with pytest.raises(SystemExit) as exc_info:
            config_loader.load_config()

        assert exc_info.value.code == 1


class TestGetLow32Config:
    def test_defaults_when_section_missing(self, config_loader):
        config_path(config_loader).write_text(json.dumps({"high32": {}}), encoding="utf-8")

        config = config_loader.get_low32_config()

        assert config["start"] == 0
        assert config["end"] == 4294967296
        assert config["use_gpu"] is True
        assert config["seeds_per_thread"] == 256

    def test_user_values_win_and_missing_keys_are_filled(self, config_loader):
        config_path(config_loader).write_text(
            json.dumps({"low32": {"start": 100, "use_gpu": False}}), encoding="utf-8"
        )

        config = config_loader.get_low32_config()

        assert config["start"] == 100
        assert config["use_gpu"] is False
        assert config["max_results"] == 10000
        assert len(config["targets"]) == 5


class TestGetHigh32Config:
    def test_defaults_when_section_missing(self, config_loader):
        config_path(config_loader).write_text(json.dumps({"low32": {}}), encoding="utf-8")

        config = config_loader.get_high32_config()

        assert config["low32"] == 1818588773
        assert config["mc_version"] == "1.21.60"
        assert config["end"] == 100000000

    def test_user_values_win_and_missing_keys_are_filled(self, config_loader):
        config_path(config_loader).write_text(
            json.dumps({"high32": {"mc_version": "1.18", "samples": []}}), encoding="utf-8"
        )

        config = config_loader.get_high32_config()

        assert config["mc_version"] == "1.18"
        assert config["samples"] == []
        assert config["test_mode"] is False


class TestMcVersionToCubiomes:
    @pytest.mark.parametrize(
        "mc_version,expected",
        [
            ("26.30+", 38),
            ("1.21.60-26.23", 29),
            ("1.21.50", 28),
            ("1.21-1.21.40", 27),
            ("1.20.60-81", 25),
            ("1.20.0-51", 25),
            ("1.19", 24),
            ("1.18", 22),
        ],
    )
    def test_exact_versions(self, config_loader, mc_version, expected):
        assert config_loader.mc_version_to_cubiomes(mc_version) == expected

    def test_partial_match_falls_back_to_major_minor(self, config_loader):
        # '1.19.80' has no exact entry but shares '1.19' with a known key
        assert config_loader.mc_version_to_cubiomes("1.19.80") == 24

    def test_unknown_version_defaults_to_latest(self, config_loader, capsys):
        assert config_loader.mc_version_to_cubiomes("9.9") == 38
        assert "Unknown MC version" in capsys.readouterr().out
