"""
Loads config/settings.yaml into a plain Python dict.

WHY THIS FILE EXISTS
---------------------
Without this, every module that needs a path or setting would open and
parse settings.yaml itself. That means the parsing logic (and any bugs in
it) is duplicated everywhere. Centralizing it here means every module
gets the same dict, and if the config file format ever changes, only
this one function needs to change.

USAGE
-----
    from src.utils.config import load_config
    config = load_config()
    raw_data_path = config["paths"]["data_raw"]
"""

from pathlib import Path
import yaml

from src.utils.exceptions import ConfigError

# PROJECT_ROOT resolves to the astra/ folder regardless of which
# directory the script was launched from. __file__ is this file's own
# path; .parent three times walks up: src/utils/config.py -> src/utils
# -> src -> astra/ (project root).
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"

# Top-level sections every part of ASTRA is allowed to assume exist.
# If a new section becomes load-bearing for some module, add it here so
# a missing/renamed section fails loudly at load time instead of as a
# confusing KeyError deep inside unrelated code later.
REQUIRED_SECTIONS = ["project", "paths", "logging", "random_seed"]


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """
    Read settings.yaml and return it as a dict.

    INPUT:  config_path — where the YAML file lives (defaults to the
            project's config/settings.yaml, overridable for tests).
    OUTPUT: dict matching the YAML structure, e.g. config["paths"]["models"].

    Raises FileNotFoundError if the file is missing, or ConfigError if it
    exists but is empty, malformed, not a mapping, or missing a section
    every module is allowed to assume exists (REQUIRED_SECTIONS) — this is
    what "avoid silent exception swallowing" means in practice: we don't
    let a bad config file surface as a cryptic error three modules away.
    """
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found at {config_path}. "
            "Did you run this from within the astra/ project, "
            "and does config/settings.yaml exist?"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    try:
        config = yaml.safe_load(raw_text)
    except yaml.YAMLError as e:
        raise ConfigError(
            f"Config file at {config_path} is not valid YAML: {e}"
        ) from e

    # An empty file parses to None, not {} — catch that explicitly rather
    # than letting the next line's config["..."] raise a TypeError later.
    if config is None:
        raise ConfigError(f"Config file at {config_path} is empty.")

    # A YAML file can validly parse to a list or a scalar instead of a
    # mapping (e.g. a file containing just "- a\n- b"). ASTRA's config
    # is always meant to be a mapping of sections, so anything else is
    # a structural error, not just a missing-key one.
    if not isinstance(config, dict):
        raise ConfigError(
            f"Config file at {config_path} must be a YAML mapping "
            f"(key: value sections), got {type(config).__name__}."
        )

    missing = [section for section in REQUIRED_SECTIONS if section not in config]
    if missing:
        raise ConfigError(
            f"Config file at {config_path} is missing required "
            f"section(s): {missing}."
        )

    return config


def resolve_path(relative_path: str) -> Path:
    """
    Turn a config-relative path (e.g. 'data/raw') into an absolute Path
    anchored at the project root, so code doesn't break depending on the
    current working directory it was run from.
    """
    return PROJECT_ROOT / relative_path
