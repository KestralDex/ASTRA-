"""
Milestone 0 tests.

These don't test any ASTRA logic yet (there isn't any) — they test that
the *foundation* works: the package imports, config loads, logging
works, and required folders exist. This is what "Python runs / dependencies
import / project modules import / tests execute" means concretely.
"""

from pathlib import Path

from src.utils.config import load_config, resolve_path
from src.utils.logger import get_logger
from src.utils.exceptions import AstraError, ConfigError, DataValidationError


def test_config_loads():
    """settings.yaml parses and has the sections we expect."""
    config = load_config()
    assert config["project"]["name"] == "ASTRA"
    assert "paths" in config
    assert "logging" in config
    assert config["random_seed"] == 42


def test_resolve_path_is_absolute():
    """resolve_path turns a config-relative path into an absolute one
    anchored at the project root, regardless of current working directory."""
    path = resolve_path("data/raw")
    assert path.is_absolute()
    assert path.name == "raw"


def test_logger_returns_logger():
    """get_logger returns a usable logger and doesn't raise."""
    logger = get_logger(__name__)
    logger.info("Milestone 0 test log line")
    assert logger is not None


def test_exceptions_are_importable_and_related():
    """Custom exceptions exist and inherit from AstraError as intended,
    so `except AstraError` will catch ConfigError/DataValidationError too."""
    assert issubclass(ConfigError, AstraError)
    assert issubclass(DataValidationError, AstraError)


def test_expected_folders_exist():
    """Core project folders from the synopsis's directory structure exist."""
    from src.utils.config import PROJECT_ROOT

    expected = [
        "config", "data/raw", "data/interim", "data/processed", "data/external",
        "src", "models", "artifacts/figures", "artifacts/metrics",
        "artifacts/reports", "dashboard", "tests", "logs",
    ]
    for rel_path in expected:
        assert (PROJECT_ROOT / rel_path).exists(), f"Missing folder: {rel_path}"
