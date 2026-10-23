"""
Reusable validation checks for ASTRA datasets.

WHY THIS FILE EXISTS
---------------------
Milestone 1's analysis of the real DataCo file surfaced concrete,
observed issues (an entirely empty column, a mostly-empty column,
columns duplicated under a different name, columns that are only known
after an order is delivered). Rather than re-checking for these by hand
every time the dataset is reloaded, this module codifies checks a
future loader can run automatically. Every check here is grounded in
something actually observed in Milestone 1 — none of it is a guessed or
imaginary business rule.

Checks are grouped into three severities:
    ERROR   — the data is unusable / structurally broken (e.g. dataset
              is empty, a genuinely required column is missing).
    WARNING — the data is usable but has a known quality issue worth a
              human's attention (e.g. a column is entirely missing).
    INFO    — an observation worth recording, not a problem
              (e.g. confirming a column has no duplicates).

USAGE
-----
    from src.data.validation import validate_dataco_schema
    result = validate_dataco_schema(df)
    for issue in result.errors:
        ...
"""

from dataclasses import dataclass, field

import pandas as pd

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Columns Milestone 1 confirmed the DataCo file always has. Used to catch
# a truncated/corrupted/different-version file early, not to encode any
# unverified assumption about what the columns *mean*.
REQUIRED_DATACO_COLUMNS = [
    "Type",
    "Days for shipping (real)",
    "Days for shipment (scheduled)",
    "Delivery Status",
    "Late_delivery_risk",
    "Order Id",
    "Order Item Id",
    "Customer Id",
    "order date (DateOrders)",
    "shipping date (DateOrders)",
]

# Confirmed via Milestone 1 analysis: entirely empty in the real file.
KNOWN_FULLY_EMPTY_COLUMNS = ["Product Description"]


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """No ERROR-level issues — WARNING/INFO don't block usability."""
        return len(self.errors) == 0

    def log_summary(self) -> None:
        for e in self.errors:
            logger.error(e)
        for w in self.warnings:
            logger.warning(w)
        for i in self.info:
            logger.info(i)


def validate_dataframe_not_empty(df: pd.DataFrame, result: ValidationResult) -> None:
    """ERROR if the dataframe has zero rows or zero columns."""
    if df.shape[0] == 0:
        result.errors.append("Dataset has zero rows.")
    if df.shape[1] == 0:
        result.errors.append("Dataset has zero columns.")


def validate_required_columns(
    df: pd.DataFrame, required: list[str], result: ValidationResult
) -> None:
    """ERROR for each required column that's missing — this is what
    would catch loading a truncated or wrong-version file."""
    missing = [c for c in required if c not in df.columns]
    for col in missing:
        result.errors.append(f"Required column missing: '{col}'")
    if not missing:
        result.info.append(f"All {len(required)} required columns present.")


def validate_no_duplicate_column_names(df: pd.DataFrame, result: ValidationResult) -> None:
    """ERROR if the same column name appears twice — this would silently
    corrupt any column-based lookup downstream."""
    seen = set()
    dupes = set()
    for col in df.columns:
        if col in seen:
            dupes.add(col)
        seen.add(col)
    for col in dupes:
        result.errors.append(f"Duplicate column name: '{col}'")


def validate_no_fully_duplicate_rows(df: pd.DataFrame, result: ValidationResult) -> None:
    """WARNING (not ERROR) if fully duplicate rows exist — usable but
    worth flagging, since Milestone 1 found zero in the real file."""
    n_dupes = int(df.duplicated().sum())
    if n_dupes > 0:
        result.warnings.append(f"{n_dupes} fully duplicate row(s) found.")
    else:
        result.info.append("No fully duplicate rows found.")


def validate_known_empty_columns(df: pd.DataFrame, result: ValidationResult) -> None:
    """
    WARNING for columns Milestone 1 confirmed are 100% missing in the
    real file (e.g. Product Description). This isn't guessing a rule —
    it's flagging that a specific, previously-observed condition still
    holds (or doesn't) on whatever file was just loaded.
    """
    for col in KNOWN_FULLY_EMPTY_COLUMNS:
        if col in df.columns:
            missing_pct = df[col].isna().mean() * 100
            if missing_pct == 100.0:
                result.warnings.append(
                    f"Column '{col}' is 100% missing (consistent with Milestone 1 finding)."
                )
            elif missing_pct > 0:
                result.info.append(
                    f"Column '{col}' is {missing_pct:.1f}% missing "
                    f"(previously observed as 100% missing — this file differs)."
                )


def validate_shipping_date_not_before_order_date(
    df: pd.DataFrame, result: ValidationResult
) -> None:
    """
    WARNING if any shipping date precedes its order date — Milestone 1
    confirmed zero such rows in the real file, so this is a genuine
    data-integrity check, not an invented rule.
    """
    if "order date (DateOrders)" not in df.columns or "shipping date (DateOrders)" not in df.columns:
        return
    order_dates = pd.to_datetime(df["order date (DateOrders)"], errors="coerce")
    ship_dates = pd.to_datetime(df["shipping date (DateOrders)"], errors="coerce")
    violations = int((ship_dates < order_dates).sum())
    if violations > 0:
        result.warnings.append(
            f"{violations} row(s) have shipping date before order date."
        )
    else:
        result.info.append("No rows with shipping date before order date.")


def validate_dataco_schema(df: pd.DataFrame) -> ValidationResult:
    """
    Run the full set of DataCo-specific checks and return a ValidationResult.
    This is observational (Milestone 1 scope) — it does not modify df.
    """
    result = ValidationResult()
    validate_dataframe_not_empty(df, result)
    validate_required_columns(df, REQUIRED_DATACO_COLUMNS, result)
    validate_no_duplicate_column_names(df, result)
    validate_no_fully_duplicate_rows(df, result)
    validate_known_empty_columns(df, result)
    validate_shipping_date_not_before_order_date(df, result)
    result.log_summary()
    return result
