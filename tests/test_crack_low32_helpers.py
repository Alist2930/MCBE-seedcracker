# -*- coding: utf-8 -*-
"""Tests for the target preparation logic in MCBEseedcracker_linux/crack_low32/crack_low32.py"""
import pytest


@pytest.fixture
def deterministic_strictness(crack_low32, monkeypatch):
    """Replace the C-library strictness probe with a lookup table.

    ``scores`` maps a structure name to the number of matches to report, so the
    ordering logic in ``prepare_targets`` can be tested without the shared library.
    """
    scores = {}

    def fake_test_sample_strictness(config, x, z, num_test_seeds=100000):
        return scores.get(config["name"], 0)

    monkeypatch.setattr(crack_low32, "test_sample_strictness", fake_test_sample_strictness)
    return scores


def expected_r_base(crack_low32, structure, x, z):
    config = crack_low32.STRUCTURE_CONFIGS[structure]
    cx, cz = x >> 4, z >> 4
    rx, rz = cx // config["spacing"], cz // config["spacing"]
    return (rx * crack_low32.CONST_A + rz * crack_low32.CONST_B + config["salt"]) & 0xFFFFFFFF


class TestStructureConfigs:
    def test_separation_is_smaller_than_spacing(self, crack_low32):
        for name, config in crack_low32.STRUCTURE_CONFIGS.items():
            assert 0 < config["separation"] < config["spacing"], name

    def test_only_known_spread_types(self, crack_low32):
        for name, config in crack_low32.STRUCTURE_CONFIGS.items():
            assert config["spread_type"] in {"linear", "triangular"}, name


class TestPrepareTargets:
    def test_region_math_for_a_single_target(self, crack_low32, deterministic_strictness):
        target = {"structure": "swamp_hut", "x": 2136, "z": -1176}

        r_base, ox, oz, offset_range, spread_type, info = crack_low32.prepare_targets([target])

        # swamp_hut: spacing 32, separation 8; chunk coords 133, -74
        assert ox == [133 % 32]
        assert oz == [(-74) % 32]
        assert offset_range == [32 - 8]
        assert spread_type == [0]
        assert r_base == [expected_r_base(crack_low32, "swamp_hut", 2136, -1176)]
        assert info[0] == {
            "name": "Swamp Hut",
            "x": 2136,
            "z": -1176,
            "rx": 133 // 32,
            "rz": -74 // 32,
            "spread_type": "linear",
        }

    def test_negative_coordinates_use_floor_division(self, crack_low32, deterministic_strictness):
        _, ox, oz, _, _, info = crack_low32.prepare_targets(
            [{"structure": "desert_temple", "x": -936, "z": 4744}]
        )

        # -936 >> 4 == -59, and -59 // 32 == -2 (floor), leaving a positive offset
        assert info[0]["rx"] == -2
        assert 0 <= ox[0] < 32
        assert 0 <= oz[0] < 32

    def test_triangular_structures_are_flagged_and_ordered_last(self, crack_low32, deterministic_strictness):
        targets = [
            {"structure": "end_city", "x": 1352, "z": -1208},  # triangular
            {"structure": "shipwreck", "x": 100, "z": 100},  # linear
        ]

        _, _, _, _, spread_type, info = crack_low32.prepare_targets(targets)

        assert spread_type == [0, 1]
        assert [i["spread_type"] for i in info] == ["linear", "triangular"]

    def test_stricter_samples_come_first_within_a_spread_group(self, crack_low32, deterministic_strictness):
        deterministic_strictness.update({"Swamp Hut": 500, "Desert Temple": 10, "Igloo": 100})
        targets = [
            {"structure": "swamp_hut", "x": 2136, "z": -1176},
            {"structure": "desert_temple", "x": -936, "z": 4744},
            {"structure": "igloo", "x": 512, "z": 512},
        ]

        _, _, _, _, _, info = crack_low32.prepare_targets(targets)

        assert [i["name"] for i in info] == ["Desert Temple", "Igloo", "Swamp Hut"]

    def test_all_returned_lists_stay_aligned(self, crack_low32, deterministic_strictness):
        deterministic_strictness.update({"End City": 5, "Ocean Monument": 50, "Buried Treasure": 1})
        targets = [
            {"structure": "ocean_monument", "x": 792, "z": -792},
            {"structure": "end_city", "x": 1352, "z": -1208},
            {"structure": "buried_treasure", "x": -40, "z": 24},
        ]

        r_base, ox, oz, offset_range, spread_type, info = crack_low32.prepare_targets(targets)

        assert len({len(r_base), len(ox), len(oz), len(offset_range), len(spread_type), len(info)}) == 1
        for i, entry in enumerate(info):
            assert r_base[i] == expected_r_base(crack_low32, _structure_of(crack_low32, entry["name"]), entry["x"], entry["z"])

    def test_empty_target_list(self, crack_low32, deterministic_strictness):
        assert crack_low32.prepare_targets([]) == ([], [], [], [], [], [])


class TestLoadGpuConfig:
    def test_defaults(self, crack_low32):
        config = crack_low32.load_gpu_config()

        assert set(config) == {"use_gpu", "auto_fallback", "seeds_per_thread", "max_results"}
        assert config["seeds_per_thread"] == 256
        assert config["max_results"] == 10000


def _structure_of(crack_low32, display_name):
    for key, config in crack_low32.STRUCTURE_CONFIGS.items():
        if config["name"] == display_name:
            return key
    raise AssertionError(f"unknown structure {display_name!r}")
