# -*- coding: utf-8 -*-
"""Tests for MCBEseedcracker_linux/crack_high32/biome_version_filter.py"""
import pytest


class TestNormalizeVersion:
    @pytest.mark.parametrize(
        "version_key,expected",
        [
            ("26.30+", "26.30+"),
            ("1.21.60-26.23", "1.21.60-26.23"),
            ("1.21.50", "1.21.50"),
            ("1.21-1.21.40", "1.21.40"),
            ("1.20.60-81", "1.20"),
            ("1.20.0-51", "1.20"),
            ("1.19", "1.19"),
            ("1.18", "1.18"),
        ],
    )
    def test_known_versions(self, linux_biome_filter, version_key, expected):
        assert linux_biome_filter.normalize_version(version_key) == expected

    def test_unknown_version_defaults_to_latest(self, linux_biome_filter):
        assert linux_biome_filter.normalize_version("1.16") == "26.30+"

    def test_every_normalized_value_is_in_version_order(self, linux_biome_filter):
        for version_key in ["26.30+", "1.21.60-26.23", "1.21.50", "1.21-1.21.40",
                            "1.20.60-81", "1.20.0-51", "1.19", "1.18"]:
            assert linux_biome_filter.normalize_version(version_key) in linux_biome_filter.VERSION_ORDER


class TestGetBiomeVersion:
    @pytest.mark.parametrize(
        "biome_id,expected",
        [
            (174, "1.18"),
            (182, "1.18"),
            (184, "1.19"),
            (185, "1.20"),
            (186, "1.21.50"),
            (187, "26.30+"),
        ],
    )
    def test_first_version_introducing_the_biome(self, linux_biome_filter, biome_id, expected):
        assert linux_biome_filter.get_biome_version(biome_id) == expected

    def test_biomes_outside_the_table_default_to_oldest(self, linux_biome_filter):
        assert linux_biome_filter.get_biome_version(0) == "1.18"


class TestIsBiomeAvailable:
    def test_old_biome_available_everywhere(self, linux_biome_filter):
        assert linux_biome_filter.is_biome_available(1, "1.18") is True

    def test_new_biome_unavailable_on_old_version(self, linux_biome_filter):
        assert linux_biome_filter.is_biome_available(187, "1.21.50") is False

    def test_new_biome_available_on_its_own_version(self, linux_biome_filter):
        assert linux_biome_filter.is_biome_available(187, "26.30+") is True

    def test_pale_garden_needs_at_least_1_21_50(self, linux_biome_filter):
        assert linux_biome_filter.is_biome_available(186, "1.21-1.21.40") is False
        assert linux_biome_filter.is_biome_available(186, "1.21.50") is True

    def test_unknown_version_is_treated_as_newest(self, linux_biome_filter):
        assert linux_biome_filter.is_biome_available(187, "unknown") is True


class TestCheckBiomeVersionCompatibilityCli:
    def test_no_warnings_for_compatible_biomes(self, linux_biome_filter):
        assert linux_biome_filter.check_biome_version_compatibility_cli([1, 174, 185], "1.20.0-51") == []

    def test_warning_payload_for_incompatible_biome(self, linux_biome_filter):
        warnings = linux_biome_filter.check_biome_version_compatibility_cli([1, 187], "1.19")

        assert len(warnings) == 1
        assert warnings[0]["biome_id"] == 187
        assert warnings[0]["required_version"] == "26.30+"
        assert warnings[0]["current_version"] == "1.19"
        assert "187" in warnings[0]["message"]

    def test_multiple_incompatible_biomes(self, linux_biome_filter):
        warnings = linux_biome_filter.check_biome_version_compatibility_cli([186, 187], "1.18")

        assert [w["biome_id"] for w in warnings] == [186, 187]


class TestPrintVersionWarnings:
    def test_returns_false_and_prints_nothing_without_warnings(self, linux_biome_filter, capsys):
        assert linux_biome_filter.print_version_warnings([]) is False
        assert capsys.readouterr().out == ""

    def test_prints_each_warning_message(self, linux_biome_filter, capsys):
        warnings = linux_biome_filter.check_biome_version_compatibility_cli([187], "1.18")

        assert linux_biome_filter.print_version_warnings(warnings) is True

        out = capsys.readouterr().out
        assert "Version Compatibility Warning" in out
        assert warnings[0]["message"] in out
