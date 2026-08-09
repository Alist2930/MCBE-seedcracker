# -*- coding: utf-8 -*-
"""Tests for MCBEseedcracker_win_ui/ui/utils/version_config.py"""
import pytest

from ui.utils import version_config


class TestGetCubiomesVersion:
    @pytest.mark.parametrize(
        "bedrock_version,expected",
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
    def test_known_versions(self, bedrock_version, expected):
        assert version_config.get_cubiomes_version(bedrock_version) == expected

    def test_unknown_version_defaults_to_latest(self):
        assert version_config.get_cubiomes_version("1.16") == 38

    def test_cubiomes_codes_increase_with_version_recency(self):
        codes = [
            version_config.get_cubiomes_version(key)
            for key in ["1.18", "1.19", "1.20.0-51", "1.21-1.21.40", "1.21.50",
                        "1.21.60-26.23", "26.30+"]
        ]
        assert codes == sorted(codes)


class TestGetVersionWarning:
    def test_no_warning_for_supported_versions(self):
        assert version_config.get_version_warning("26.30+") is None

    def test_no_warning_for_unknown_version(self):
        assert version_config.get_version_warning("1.16") is None

    def test_warning_is_returned_when_configured(self, monkeypatch):
        monkeypatch.setitem(
            version_config.BEDROCK_VERSION_MAP,
            "1.18",
            {"cubiomes_code": 22, "warning": "legacy generation"},
        )

        assert version_config.get_version_warning("1.18") == "legacy generation"


class TestWinUiVersionOptions:
    def test_every_option_maps_to_a_known_version(self):
        for option in version_config.WINUI_VERSION_OPTIONS:
            assert option["data"] in version_config.BEDROCK_VERSION_MAP

    def test_options_cover_all_supported_versions(self):
        assert {o["data"] for o in version_config.WINUI_VERSION_OPTIONS} == set(
            version_config.BEDROCK_VERSION_MAP
        )

    def test_options_expose_both_languages(self):
        for option in version_config.WINUI_VERSION_OPTIONS:
            assert option["text_zh"] and option["text_en"]
            assert option["type"] == "bedrock"
