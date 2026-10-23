"""
Milestone 0 tests.

These don't test any ASTRA logic yet (there isn't any) — they test that
the *foundation* works: the package imports, config loads, logging
works, and required folders exist. This is what "Python runs / dependencies
import / project modules import / tests execute" means concretely.
"""

from pathlib import Path

import pytest

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


def test_logger_actually_writes_to_log_file():
    """
    The earlier test only checked that logging didn't raise — it never
    confirmed a line actually landed in the file. This does: log a
    unique, greppable message and confirm it's present in the configured
    log file afterward, instead of relying on someone manually opening
    logs/astra.log to check.
    """
    from src.utils.config import load_config, resolve_path

    config = load_config()
    log_file_path = resolve_path(config["logging"]["log_file"])

    logger = get_logger("test_logger_file_output")
    unique_marker = "MILESTONE0_LOGGER_FILE_TEST_MARKER"
    logger.info(unique_marker)

    # Flush handlers so the write is on disk before we read it back —
    # otherwise this test can flake depending on buffering.
    for handler in logger.root.handlers:
        handler.flush()

    assert log_file_path.exists(), f"Expected log file at {log_file_path}"
    log_contents = log_file_path.read_text(encoding="utf-8")
    assert unique_marker in log_contents


def test_config_rejects_empty_file(tmp_path):
    """An empty config file should raise ConfigError, not a confusing
    downstream TypeError from treating None as a dict."""
    empty_config = tmp_path / "empty.yaml"
    empty_config.write_text("", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(config_path=empty_config)


def test_config_rejects_malformed_yaml(tmp_path):
    """Genuinely broken YAML syntax should raise ConfigError with a
    useful message, not an unhandled yaml.YAMLError."""
    bad_config = tmp_path / "bad.yaml"
    bad_config.write_text("project: [unclosed", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(config_path=bad_config)


def test_config_rejects_non_mapping_yaml(tmp_path):
    """A YAML file that parses to a list rather than a mapping of
    sections is structurally invalid for ASTRA's config format."""
    list_config = tmp_path / "list.yaml"
    list_config.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_config(config_path=list_config)


def test_config_rejects_missing_required_section(tmp_path):
    """A config missing a section every module is allowed to assume
    exists (e.g. 'logging') should fail at load time, not deep inside
    whichever module first tries to read that section."""
    incomplete_config = tmp_path / "incomplete.yaml"
    incomplete_config.write_text(
        "project:\n  name: ASTRA\npaths:\n  data_raw: data/raw\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="logging"):
        load_config(config_path=incomplete_config)


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
