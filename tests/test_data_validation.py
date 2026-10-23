"""
Tests for src/data/validation.py. All inputs are small, hand-built
DataFrames — never the real DataCo file.
"""

import pandas as pd

from src.data.validation import (
    ValidationResult,
    validate_dataframe_not_empty,
    validate_required_columns,
    validate_no_duplicate_column_names,
    validate_no_fully_duplicate_rows,
    validate_known_empty_columns,
    validate_shipping_date_not_before_order_date,
    validate_dataco_schema,
    REQUIRED_DATACO_COLUMNS,
)


def _minimal_valid_dataco_df() -> pd.DataFrame:
    """A tiny DataFrame containing every REQUIRED_DATACO_COLUMNS, with
    values that satisfy every check (no duplicate rows, shipping date
    after order date)."""
    return pd.DataFrame({
        "Type": ["DEBIT", "TRANSFER"],
        "Days for shipping (real)": [3, 4],
        "Days for shipment (scheduled)": [2, 4],
        "Delivery Status": ["Late delivery", "Shipping on time"],
        "Late_delivery_risk": [1, 0],
        "Order Id": [1001, 1002],
        "Order Item Id": [1, 2],
        "Customer Id": [501, 502],
        "order date (DateOrders)": ["1/1/2018 10:00", "1/2/2018 11:00"],
        "shipping date (DateOrders)": ["1/4/2018 10:00", "1/6/2018 11:00"],
    })


def test_validate_dataframe_not_empty_passes_on_normal_df():
    result = ValidationResult()
    validate_dataframe_not_empty(_minimal_valid_dataco_df(), result)
    assert result.errors == []


def test_validate_dataframe_not_empty_flags_zero_rows():
    empty_df = pd.DataFrame(columns=["a", "b"])
    result = ValidationResult()
    validate_dataframe_not_empty(empty_df, result)
    assert any("zero rows" in e for e in result.errors)


def test_validate_required_columns_passes_when_all_present():
    result = ValidationResult()
    validate_required_columns(_minimal_valid_dataco_df(), REQUIRED_DATACO_COLUMNS, result)
    assert result.errors == []


def test_validate_required_columns_flags_missing_column():
    df = _minimal_valid_dataco_df().drop(columns=["Late_delivery_risk"])
    result = ValidationResult()
    validate_required_columns(df, REQUIRED_DATACO_COLUMNS, result)
    assert any("Late_delivery_risk" in e for e in result.errors)


def test_validate_no_duplicate_column_names_flags_dupes():
    df = _minimal_valid_dataco_df()
    df.columns = list(df.columns[:-1]) + [df.columns[0]]  # force a duplicate name
    result = ValidationResult()
    validate_no_duplicate_column_names(df, result)
    assert len(result.errors) == 1


def test_validate_no_fully_duplicate_rows_warns_on_dupes():
    df = _minimal_valid_dataco_df()
    df_with_dupe = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    result = ValidationResult()
    validate_no_fully_duplicate_rows(df_with_dupe, result)
    assert any("duplicate row" in w for w in result.warnings)


def test_validate_no_fully_duplicate_rows_clean_case():
    result = ValidationResult()
    validate_no_fully_duplicate_rows(_minimal_valid_dataco_df(), result)
    assert result.warnings == []


def test_validate_known_empty_columns_warns_when_100pct_missing():
    df = _minimal_valid_dataco_df()
    df["Product Description"] = [None, None]
    result = ValidationResult()
    validate_known_empty_columns(df, result)
    assert any("100% missing" in w for w in result.warnings)


def test_validate_shipping_before_order_date_flags_violation():
    df = _minimal_valid_dataco_df()
    # deliberately make shipping date earlier than order date
    df.loc[0, "shipping date (DateOrders)"] = "12/31/2017 10:00"
    result = ValidationResult()
    validate_shipping_date_not_before_order_date(df, result)
    assert any("shipping date before order date" in w for w in result.warnings)


def test_validate_dataco_schema_end_to_end_valid():
    """The full validator returns is_valid=True on a clean minimal df."""
    result = validate_dataco_schema(_minimal_valid_dataco_df())
    assert result.is_valid is True
    assert result.errors == []


def test_validate_dataco_schema_end_to_end_invalid():
    """The full validator returns is_valid=False when a required column
    is missing."""
    df = _minimal_valid_dataco_df().drop(columns=["Order Id"])
    result = validate_dataco_schema(df)
    assert result.is_valid is False
    assert any("Order Id" in e for e in result.errors)
