# -*- coding: utf-8 -*-
"""Tests for the pure helpers in MCBEseedcracker_linux/crack_high32/crack_high32.py"""
import pytest


class TestBiomeNames:
    def test_known_id(self, crack_high32):
        assert crack_high32.get_biome_name(4) == "forest"
        assert crack_high32.get_biome_name(187) == "sulfur_caves"

    def test_unknown_id_falls_back_to_generic_name(self, crack_high32):
        assert crack_high32.get_biome_name(9999) == "biome_9999"

    def test_name_table_is_the_inverse_of_the_id_table(self, crack_high32):
        for name, info in crack_high32.BIOME_IDS.items():
            assert crack_high32.BIOME_NAMES[info["id"]] == name


class TestToSigned64:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (0, 0),
            (123456789, 123456789),
            (9223372036854775807, 9223372036854775807),
            (9223372036854775808, -9223372036854775808),
            (18446744073709551615, -1),
        ],
    )
    def test_wraps_above_signed_max(self, crack_high32, value, expected):
        assert crack_high32.to_signed64(value) == expected


class TestFormatSeedOutput:
    def test_reports_split_and_signed_seed(self, crack_high32):
        seed = (0x12345678 << 32) | 0x9ABCDEF0

        output = crack_high32.format_seed_output(seed, 0x9ABCDEF0)

        assert "Low 32-bit:  2596069104 (0x9ABCDEF0)" in output
        assert "High 32-bit: 305419896 (0x12345678)" in output
        assert f"Full seed:   {seed} (0x123456789ABCDEF0)" in output

    def test_negative_display_for_seeds_above_signed_max(self, crack_high32):
        seed = 0xFFFFFFFFFFFFFFFF

        assert "Full seed:   -1 (0xFFFFFFFFFFFFFFFF)" in crack_high32.format_seed_output(seed, 0xFFFFFFFF)


class TestBiomeRarity:
    def test_known_biome_and_version(self, crack_high32):
        assert crack_high32.get_biome_rarity(4, "1.18") == pytest.approx(0.12118830)

    def test_unknown_version_is_treated_as_common(self, crack_high32):
        assert crack_high32.get_biome_rarity(4, "0.1") == 1.0

    def test_unknown_biome_is_treated_as_common(self, crack_high32):
        assert crack_high32.get_biome_rarity(9999, "1.18") == 1.0


class TestSortSamplesByRarity:
    def test_rarest_sample_first(self, crack_high32):
        # forest (0.123) is far more common than pale_garden (0.00121) in 26.30+
        samples = [(0, 0, 200, 4), (1, 1, 200, 186), (2, 2, 200, 5)]

        ordered = crack_high32.sort_samples_by_rarity(samples, "26.30+")

        assert [s[3] for s in ordered] == [186, 5, 4]

    def test_legacy_three_tuple_samples(self, crack_high32):
        samples = [(0, 0, 4), (1, 1, 186)]

        ordered = crack_high32.sort_samples_by_rarity(samples, "26.30+")

        assert [s[2] for s in ordered] == [186, 4]


class TestGetBiomeVersion:
    @pytest.mark.parametrize(
        "biome_id,expected",
        [
            (174, "1.18"),
            (183, "1.19"),
            (185, "1.20.0-51"),
            (186, "1.21.50"),
            (187, "26.30+"),
        ],
    )
    def test_first_version_introducing_the_biome(self, crack_high32, biome_id, expected):
        assert crack_high32.get_biome_version(biome_id) == expected

    def test_biomes_outside_the_table_default_to_oldest(self, crack_high32):
        assert crack_high32.get_biome_version(4) == "1.18"


class TestCheckBiomeVersion:
    def test_no_warnings_when_all_samples_are_supported(self, crack_high32):
        samples = [(0, 0, 200, 4), (1, 1, 200, 185)]

        assert crack_high32.check_biome_version(samples, "1.20.0-51") == []

    def test_warns_for_biome_newer_than_selected_version(self, crack_high32):
        samples = [(10, -20, 200, 187)]

        warnings = crack_high32.check_biome_version(samples, "1.21.50")

        assert len(warnings) == 1
        assert "(10, -20)" in warnings[0]
        assert "sulfur_caves" in warnings[0]
        assert "requires 26.30++" in warnings[0]

    def test_legacy_three_tuple_samples(self, crack_high32):
        warnings = crack_high32.check_biome_version([(10, -20, 186)], "1.19")

        assert len(warnings) == 1
        assert "pale_garden" in warnings[0]

    def test_unknown_version_is_treated_as_newest(self, crack_high32):
        assert crack_high32.check_biome_version([(0, 0, 200, 187)], "not-a-version") == []
