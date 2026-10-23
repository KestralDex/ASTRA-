"""
Tests for src/data/loaders.py.

All fixtures here are tiny, synthetic CSVs created on the fly with
pytest's tmp_path — the real 96MB DataCo file is never copied into the
test suite or loaded during tests.
"""

import pandas as pd
import pytest

from src.data.loaders import load_csv, file_discovery_report, _validate_file_before_reading
from src.utils.exceptions import DataValidationError


def _write_csv(tmp_path, name: str, content: str):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_load_valid_small_csv(tmp_path):
    """A well-formed small CSV loads into a DataFrame with the expected shape."""
    path = _write_csv(tmp_path, "valid.csv", "a,b,c\n1,2,3\n4,5,6\n")
    df = load_csv(path)
    assert df.shape == (2, 3)
    assert list(df.columns) == ["a", "b", "c"]


def test_load_missing_file_raises(tmp_path):
    """A path that doesn't exist raises DataValidationError, not a raw
    FileNotFoundError, so callers can catch one ASTRA-specific type."""
    missing_path = tmp_path / "does_not_exist.csv"
    with pytest.raises(DataValidationError, match="not found"):
        load_csv(missing_path)


def test_load_wrong_extension_raises(tmp_path):
    """A non-.csv file is rejected before pandas ever touches it."""
    path = _write_csv(tmp_path, "not_a_csv.txt", "a,b\n1,2\n")
    with pytest.raises(DataValidationError, match=r"\.csv"):
        load_csv(path)


def test_load_empty_csv_raises(tmp_path):
    """A genuinely empty file (no header, no rows) raises DataValidationError
    via pandas.errors.EmptyDataError, not an unhandled exception."""
    path = _write_csv(tmp_path, "empty.csv", "")
    with pytest.raises(DataValidationError):
        load_csv(path)


def test_load_malformed_csv_raises(tmp_path):
    """A row with more fields than the header declares is a parser
    error under the default C engine — must surface as a clear
    DataValidationError, not a raw pandas.errors.ParserError.

    Note: this deliberately does NOT pass engine='python', because that
    engine silently reinterprets extra trailing fields as an implicit
    row index instead of raising — which would make this test pass for
    the wrong reason. The default (C) engine raises ParserError as
    expected, which is exactly what this test needs to verify is
    translated into DataValidationError."""
    path = _write_csv(
        tmp_path,
        "malformed.csv",
        "a,b,c\n1,2,3\n4,5,6,7,8,9\n",  # second data row has too many fields
    )
    with pytest.raises(DataValidationError):
        load_csv(path)


def test_load_directory_instead_of_file_raises(tmp_path):
    """Passing a directory (not a file) must fail with a clear message,
    not an OS-level error from pandas."""
    directory = tmp_path / "a_directory.csv"
    directory.mkdir()
    with pytest.raises(DataValidationError, match="not a regular file"):
        load_csv(directory)


def test_load_latin1_fallback_encoding(tmp_path):
    """A file that isn't valid UTF-8 should still load via the latin-1
    fallback rather than failing outright — this is exactly what
    happened with the real DataCo file."""
    path = tmp_path / "latin1.csv"
    # Write bytes that are invalid UTF-8 but valid latin-1 (0xe9 = 'é' in latin-1)
    path.write_bytes(b"name,note\n" + "café".encode("latin-1") + b",ok\n")
    df = load_csv(path)
    assert df.shape[0] == 1


def test_file_discovery_report_existing_file(tmp_path):
    """file_discovery_report reports metadata without raising, for a
    file that exists."""
    path = _write_csv(tmp_path, "exists.csv", "a,b\n1,2\n")
    report = file_discovery_report(path)
    assert report["exists"] is True
    assert report["is_file"] is True
    assert report["is_readable"] is True
    assert report["size_bytes"] > 0


def test_file_discovery_report_missing_file(tmp_path):
    """file_discovery_report reports exists=False rather than raising,
    for a file that doesn't exist — Step 1 is meant to be observational."""
    path = tmp_path / "missing.csv"
    report = file_discovery_report(path)
    assert report["exists"] is False
    assert report["is_file"] is False
    assert report["is_readable"] is False
