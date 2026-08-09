# -*- coding: utf-8 -*-
"""Tests for MCBEseedcracker_win_ui/ui/utils/biome_version_filter.py"""
import pytest

from ui.utils import biome_version_filter as bvf
from ui.utils.language_manager import lang_manager

BIOME_DATA = {
    "forest": {"id": 4, "name_zh": "森林", "name_en": "Forest"},
    "pale_garden": {"id": 186, "name_zh": "苍白之园", "name_en": "Pale Garden"},
    "sulfur_caves": {"id": 187, "name_zh": "硫磺洞穴", "name_en": "Sulfur Caves"},
    "unmapped": {"name_zh": "未知", "name_en": "Unknown"},
}


@pytest.fixture
def english(monkeypatch):
    monkeypatch.setattr(lang_manager, "language", "en_US")


@pytest.fixture
def chinese(monkeypatch):
    monkeypatch.setattr(lang_manager, "language", "zh_CN")


class TestNormalizeVersion:
    @pytest.mark.parametrize(
        "version_key",
        ["26.30+", "1.21.60-26.23", "1.21.50", "1.21-1.21.40", "1.20.60-81",
         "1.20.0-51", "1.19", "1.18"],
    )
    def test_known_versions_map_to_themselves(self, version_key):
        assert bvf.normalize_version(version_key) == version_key
        assert bvf.normalize_version(version_key) in bvf.VERSION_ORDER

    def test_unknown_version_defaults_to_latest(self):
        assert bvf.normalize_version("1.16") == "26.30+"


class TestGetBiomeVersion:
    @pytest.mark.parametrize(
        "biome_id,expected",
        [(174, "1.18"), (183, "1.19"), (185, "1.20.0-51"), (186, "1.21.50"), (187, "26.30+")],
    )
    def test_first_version_introducing_the_biome(self, biome_id, expected):
        assert bvf.get_biome_version(biome_id) == expected

    def test_biomes_outside_the_table_default_to_oldest(self, biome_id=4):
        assert bvf.get_biome_version(biome_id) == "1.18"


class TestIsBiomeAvailable:
    @pytest.mark.parametrize(
        "biome_id,mc_version,expected",
        [
            (4, "1.18", True),
            (186, "1.21-1.21.40", False),
            (186, "1.21.50", True),
            (186, "26.30+", True),
            (187, "1.21.60-26.23", False),
            (187, "26.30+", True),
            (185, "1.19", False),
        ],
    )
    def test_availability(self, biome_id, mc_version, expected):
        assert bvf.is_biome_available(biome_id, mc_version) is expected

    def test_unknown_version_is_treated_as_newest(self):
        assert bvf.is_biome_available(187, "1.16") is True


class TestCheckBiomeVersionCompatibility:
    def test_no_warnings_when_all_biomes_exist(self, english):
        biomes = [{"type": "forest"}, {"type": "pale_garden"}]

        assert bvf.check_biome_version_compatibility(biomes, "1.21.50", BIOME_DATA) == []

    def test_warning_payload_for_incompatible_biome(self, english):
        warnings = bvf.check_biome_version_compatibility(
            [{"type": "forest"}, {"type": "sulfur_caves"}], "1.21.50", BIOME_DATA
        )

        assert len(warnings) == 1
        assert warnings[0]["biome"] == "sulfur_caves"
        assert warnings[0]["biome_id"] == 187
        assert warnings[0]["required_version"] == "26.30+"
        assert warnings[0]["current_version"] == "1.21.50"
        assert "Sulfur Caves" in warnings[0]["message"]

    def test_chinese_messages_use_chinese_biome_names(self, chinese):
        warnings = bvf.check_biome_version_compatibility(
            [{"type": "sulfur_caves"}], "1.18", BIOME_DATA
        )

        assert "硫磺洞穴" in warnings[0]["message"]

    def test_biomes_without_an_id_are_skipped(self, english):
        assert bvf.check_biome_version_compatibility(
            [{"type": "unmapped"}, {"type": "missing"}], "1.18", BIOME_DATA
        ) == []


class TestCheckSingleBiomeVersion:
    def test_available_biome(self, english):
        assert bvf.check_single_biome_version("forest", "1.18", BIOME_DATA) == {
            "available": True,
            "message": None,
        }

    def test_unavailable_biome_cannot_be_added(self, english):
        result = bvf.check_single_biome_version("pale_garden", "1.19", BIOME_DATA)

        assert result["available"] is False
        assert result["allow_add"] is False
        assert "Pale Garden" in result["message"]
        assert "1.21.50" in result["message"]

    def test_chinese_message(self, chinese):
        result = bvf.check_single_biome_version("pale_garden", "1.19", BIOME_DATA)

        assert "苍白之园" in result["message"]

    def test_biome_without_an_id_is_treated_as_available(self, english):
        assert bvf.check_single_biome_version("unmapped", "1.18", BIOME_DATA)["available"] is True

    def test_unknown_biome_is_treated_as_available(self, english):
        assert bvf.check_single_biome_version("missing", "1.18", BIOME_DATA)["available"] is True
