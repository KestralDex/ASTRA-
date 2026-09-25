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

# PROJECT_ROOT resolves to the astra/ folder regardless of which
# directory the script was launched from. __file__ is this file's own
# path; .parent three times walks up: src/utils/config.py -> src/utils
# -> src -> astra/ (project root).
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> dict:
    """
    Read settings.yaml and return it as a dict.

    INPUT:  config_path — where the YAML file lives (defaults to the
            project's config/settings.yaml, overridable for tests).
    OUTPUT: dict matching the YAML structure, e.g. config["paths"]["models"].

    Raises FileNotFoundError with a clear message if the file is missing,
    rather than letting a cryptic yaml/OS error surface — this is what
    "avoid silent exception swallowing" means in practice: we don't hide
    the error, we make it clearer.
    """
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found at {config_path}. "
            "Did you run this from within the astra/ project, "
            "and does config/settings.yaml exist?"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def resolve_path(relative_path: str) -> Path:
    """
    Turn a config-relative path (e.g. 'data/raw') into an absolute Path
    anchored at the project root, so code doesn't break depending on the
    current working directory it was run from.
    """
    return PROJECT_ROOT / relative_path
