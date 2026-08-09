# -*- coding: utf-8 -*-
"""Shared pytest fixtures and import helpers.

The project is not packaged, so the modules under test are imported from their
source paths after the relevant source directories are added to ``sys.path``.

``config_loader`` reads and writes ``config.json`` next to its own source file.
Tests redirect that by pointing the module's ``__file__`` at a temp directory,
which keeps the repository untouched while still exercising the real module.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
LINUX_DIR = REPO_ROOT / "MCBEseedcracker_linux"
WIN_UI_DIR = REPO_ROOT / "MCBEseedcracker_win_ui"

# Importable at collection time so tests can `from ui.utils import ...`.
for _source_dir in (WIN_UI_DIR, LINUX_DIR):
    if str(_source_dir) not in sys.path:
        sys.path.insert(0, str(_source_dir))


def load_module_from_path(module_name, file_path):
    """Import a module from an explicit file path under the given name."""
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def config_loader(tmp_path, monkeypatch):
    """``config_loader`` with its ``config.json`` redirected to ``tmp_path``."""
    module = load_module_from_path("config_loader", LINUX_DIR / "config_loader.py")
    monkeypatch.setattr(module, "__file__", str(tmp_path / "config_loader.py"))
    return module


@pytest.fixture(scope="session")
def crack_high32(tmp_path_factory):
    """The ``crack_high32`` script, imported with a temp ``config.json``.

    Importing it runs ``config_loader.get_high32_config()`` at module scope, so
    the config location is redirected before the import happens.
    """
    tmp_path = tmp_path_factory.mktemp("crack_high32_config")
    loader = load_module_from_path("config_loader", LINUX_DIR / "config_loader.py")
    original_file = loader.__file__
    loader.__file__ = str(tmp_path / "config_loader.py")
    try:
        yield load_module_from_path(
            "crack_high32", LINUX_DIR / "crack_high32" / "crack_high32.py"
        )
    finally:
        loader.__file__ = original_file
        sys.modules.pop("crack_high32", None)
        sys.modules.pop("config_loader", None)


@pytest.fixture(scope="session")
def crack_low32(tmp_path_factory):
    """The ``crack_low32`` script, imported with a temp ``config.json``.

    Importing it runs ``config_loader.get_low32_config()`` and ``prepare_targets``
    at module scope, so the config location is redirected before the import.
    """
    tmp_path = tmp_path_factory.mktemp("crack_low32_config")
    loader = load_module_from_path("config_loader", LINUX_DIR / "config_loader.py")
    original_file = loader.__file__
    loader.__file__ = str(tmp_path / "config_loader.py")
    try:
        yield load_module_from_path(
            "crack_low32", LINUX_DIR / "crack_low32" / "crack_low32.py"
        )
    finally:
        loader.__file__ = original_file
        sys.modules.pop("crack_low32", None)
        sys.modules.pop("config_loader", None)


@pytest.fixture(scope="session")
def linux_biome_filter():
    return load_module_from_path(
        "linux_biome_version_filter",
        LINUX_DIR / "crack_high32" / "biome_version_filter.py",
    )
