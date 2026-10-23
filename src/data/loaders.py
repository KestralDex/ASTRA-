"""
Reusable, defensive CSV loading for ASTRA.

WHY THIS FILE EXISTS
---------------------
Every milestone from here on loads CSV files (DataCo now, M5 later,
external context caches eventually). Writing `pd.read_csv(path)`
directly in each place means every place also has to remember to check
the file exists, is actually a CSV, isn't corrupted, and doesn't have
an encoding surprise — and in practice that checking gets forgotten
somewhere. This module does it once, so every caller gets the same
safety guarantees.

SECURITY / SAFE INPUT-HANDLING NOTES
-------------------------------------
- We never execute anything from the file's content (no eval/exec, no
  pickle, no dynamic imports based on column names or values).
- We never build shell commands or file paths out of *values inside*
  the CSV — only the path the caller explicitly passed in is touched.
- We validate the path is a real, existing, regular file with a .csv
  extension *before* asking pandas to parse it.
- We log metadata about a load (path, size, row/column counts) but
  never dump full file contents or full rows into the log — this
  matters both for readability and because a dataset can contain
  values that shouldn't end up duplicated in a plaintext log file.

USAGE
-----
    from pathlib import Path
    from src.data.loaders import load_csv

    df = load_csv(Path("data/raw/DataCoSupplyChainDataset.csv"))
"""

from pathlib import Path

import pandas as pd

from src.utils.exceptions import DataValidationError
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_csv(
    file_path: Path,
    encoding: str = "utf-8",
    fallback_encodings: tuple[str, ...] = ("latin-1",),
    **read_csv_kwargs,
) -> pd.DataFrame:
    """
    Safely load a CSV file into a pandas DataFrame.

    INPUT:
        file_path — path to the CSV file (pathlib.Path).
        encoding — encoding to try first (defaults to utf-8).
        fallback_encodings — encodings to try, in order, if the first
            one fails to decode the file. DataCo-style exports are
            sometimes Latin-1/Windows-encoded rather than UTF-8, so this
            defaults to trying latin-1 next rather than failing outright.
        **read_csv_kwargs — forwarded to pandas.read_csv (e.g. dtype=,
            parse_dates=) for callers that need more control.

    OUTPUT:
        pandas DataFrame with the file's contents.

    Raises DataValidationError (not a raw pandas/OS exception) if the
    file doesn't exist, isn't a regular file, doesn't have a .csv
    extension, can't be decoded with any tried encoding, or pandas
    can't parse it as CSV (malformed rows, etc.) — always with a
    message that says *what* went wrong and *which file*, not just a
    generic traceback.
    """
    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    _validate_file_before_reading(file_path)

    encodings_to_try = (encoding,) + tuple(
        e for e in fallback_encodings if e != encoding
    )

    last_error: Exception | None = None
    for attempt_encoding in encodings_to_try:
        try:
            df = pd.read_csv(file_path, encoding=attempt_encoding, **read_csv_kwargs)
        except UnicodeDecodeError as e:
            last_error = e
            logger.warning(
                "Failed to decode %s with encoding=%s, trying next fallback.",
                file_path.name,
                attempt_encoding,
            )
            continue
        except pd.errors.ParserError as e:
            # A parser error is a malformed-CSV problem, not an encoding
            # problem — retrying with a different encoding won't fix it,
            # so fail immediately with a clear, specific exception.
            raise DataValidationError(
                f"Could not parse '{file_path.name}' as CSV "
                f"(malformed rows or structure): {e}"
            ) from e
        except pd.errors.EmptyDataError as e:
            raise DataValidationError(
                f"'{file_path.name}' is empty or has no parseable columns."
            ) from e
        else:
            logger.info(
                "Loaded %s: %d rows x %d columns (encoding=%s)",
                file_path.name,
                df.shape[0],
                df.shape[1],
                attempt_encoding,
            )
            return df

    # Every encoding attempt failed to decode the file.
    raise DataValidationError(
        f"Could not decode '{file_path.name}' with any of "
        f"{encodings_to_try}: {last_error}"
    ) from last_error


def _validate_file_before_reading(file_path: Path) -> None:
    """
    Existence/type/extension checks run before pandas ever touches the
    file, so a bad path fails with a clear ASTRA exception instead of a
    confusing pandas/OS-level error.
    """
    if not file_path.exists():
        raise DataValidationError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise DataValidationError(
            f"Path exists but is not a regular file: {file_path}"
        )

    if file_path.suffix.lower() != ".csv":
        raise DataValidationError(
            f"Expected a .csv file, got '{file_path.suffix}': {file_path}"
        )


def file_discovery_report(file_path: Path) -> dict:
    """
    Report basic, non-sensitive metadata about a file WITHOUT reading
    its contents — used for Milestone 1 Step 1 (file discovery) before
    any actual parsing happens.

    OUTPUT: dict with filename, exists, is_file, is_readable, size_bytes,
    size_mb. Never includes file contents.
    """
    exists = file_path.exists()
    is_file = file_path.is_file() if exists else False

    readable = False
    if is_file:
        try:
            with open(file_path, "rb") as f:
                f.read(1)
            readable = True
        except OSError:
            readable = False

    size_bytes = file_path.stat().st_size if is_file else None

    return {
        "filename": file_path.name,
        "path": str(file_path),
        "exists": exists,
        "is_file": is_file,
        "is_readable": readable,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 2) if size_bytes else None,
    }
