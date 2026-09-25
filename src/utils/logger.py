"""
Sets up a single, consistent logger for the whole ASTRA project.

WHY THIS FILE EXISTS
---------------------
Using print() statements makes it impossible to tell severity (is this
informational, or a warning?) and impossible to turn off/redirect output
later without editing every file. A logger fixes both: every module
gets timestamps, severity levels, and writes to both the terminal and a
persistent log file (logs/astra.log), which matters for milestone
reports and debugging failed runs after the fact.

USAGE
-----
    from src.utils.logger import get_logger
    logger = get_logger(__name__)
    logger.info("Loaded %d rows", len(df))
    logger.warning("Column X has missing values")
    logger.error("Failed to load file", exc_info=True)
"""

import logging
from pathlib import Path

from src.utils.config import load_config, resolve_path

_configured = False  # module-level flag so we only attach handlers once


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger configured per config/settings.yaml.

    INPUT:  name — usually __name__, so log lines show which module
            they came from (e.g. "src.data.loaders").
    OUTPUT: a standard library logging.Logger, ready to use.

    Python's logging module is global by module name, so calling this
    from multiple files does not create duplicate log files — it's safe
    to call get_logger(__name__) at the top of every module.
    """
    global _configured

    if not _configured:
        _configure_root_logger()
        _configured = True

    return logging.getLogger(name)


def _configure_root_logger() -> None:
    """Attach a console handler and a file handler to the root logger, once."""
    config = load_config()
    level_name = config["logging"]["level"]
    log_file_relative = config["logging"]["log_file"]

    log_file_path: Path = resolve_path(log_file_relative)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, level_name.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
