# -*- coding: utf-8 -*-
"""Tests for MCBEseedcracker_win_ui/ui/utils/language_manager.py"""
import pytest

from ui.utils.language_manager import LanguageManager, lang_manager


@pytest.fixture
def manager():
    return LanguageManager()


class TestDefaults:
    def test_default_language_is_chinese(self, manager):
        assert manager.language == "zh_CN"

    def test_module_level_singleton_is_ready_to_use(self):
        assert isinstance(lang_manager, LanguageManager)
        assert lang_manager.get("app_name")

    def test_both_languages_are_available(self, manager):
        assert set(manager.translations) == {"zh_CN", "en_US"}


class TestGet:
    def test_returns_translation_for_current_language(self, manager):
        assert manager.get("app_name") == "MCBE 种子破解器"

    def test_unknown_key_returns_the_key_itself(self, manager):
        assert manager.get("no_such_key") == "no_such_key"

    def test_formats_positional_arguments(self, manager):
        assert "7" in manager.get("low32_finished_msg", 7)

    def test_unknown_key_with_arguments_returns_the_key(self, manager):
        assert manager.get("no_such_key {}", "x") == "no_such_key x"

    def test_unknown_language_falls_back_to_the_key(self, manager):
        manager.set_language("fr_FR")

        assert manager.get("app_name") == "app_name"


class TestSetLanguage:
    def test_switching_language_changes_translations(self, manager):
        zh = manager.get("start_cracking")

        manager.set_language("en_US")

        assert manager.get("start_cracking") != zh
        assert manager.language == "en_US"

    def test_instances_do_not_share_language_state(self, manager):
        other = LanguageManager()

        manager.set_language("en_US")

        assert other.language == "zh_CN"


class TestTranslationTables:
    def test_english_and_chinese_expose_the_same_keys(self, manager):
        assert set(manager.translations["zh_CN"]) == set(manager.translations["en_US"])

    def test_no_empty_translations(self, manager):
        for language, table in manager.translations.items():
            for key, value in table.items():
                assert value, f"empty translation for {key!r} in {language}"

    def test_placeholder_counts_match_across_languages(self, manager):
        for key, zh_text in manager.translations["zh_CN"].items():
            assert zh_text.count("{}") == manager.translations["en_US"][key].count("{}"), key
