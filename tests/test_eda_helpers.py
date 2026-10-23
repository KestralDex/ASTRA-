"""Tests for src/data/eda_helpers.py, using small synthetic DataFrames."""

import pandas as pd
import pytest

from src.data.eda_helpers import group_rate_table


def test_group_rate_table_basic_counts_and_rates():
    df = pd.DataFrame({
        "mode": ["A", "A", "A", "B", "B"],
        "late": [1, 1, 0, 0, 0],
    })
    result = group_rate_table(df, "mode", "late")
    row_a = result[result["mode"] == "A"].iloc[0]
    row_b = result[result["mode"] == "B"].iloc[0]

    assert row_a["sample_count"] == 3
    assert row_a["positive_count"] == 2
    assert row_a["positive_rate"] == pytest.approx(2 / 3, rel=1e-3)

    assert row_b["sample_count"] == 2
    assert row_b["positive_count"] == 0
    assert row_b["positive_rate"] == 0.0


def test_group_rate_table_sorted_by_sample_count_descending():
    df = pd.DataFrame({
        "mode": ["A", "B", "B", "B", "B"],
        "late": [1, 0, 1, 0, 1],
    })
    result = group_rate_table(df, "mode", "late")
    assert list(result["mode"]) == ["B", "A"]


def test_group_rate_table_low_sample_warning_flag():
    df = pd.DataFrame({
        "mode": ["A"] * 5 + ["B"] * 40,
        "late": [1, 0, 1, 0, 1] + [0] * 40,
    })
    result = group_rate_table(df, "mode", "late", min_count_warning_threshold=30)
    row_a = result[result["mode"] == "A"].iloc[0]
    row_b = result[result["mode"] == "B"].iloc[0]
    assert row_a["low_sample_warning"] == True
    assert row_b["low_sample_warning"] == False


def test_group_rate_table_missing_group_col_raises():
    df = pd.DataFrame({"late": [1, 0]})
    with pytest.raises(ValueError, match="group_col"):
        group_rate_table(df, "nonexistent", "late")


def test_group_rate_table_missing_target_col_raises():
    df = pd.DataFrame({"mode": ["A", "B"]})
    with pytest.raises(ValueError, match="target_col"):
        group_rate_table(df, "mode", "nonexistent")


def test_group_rate_table_non_binary_target_raises():
    df = pd.DataFrame({"mode": ["A", "B"], "late": [1, 2]})
    with pytest.raises(ValueError, match="binary"):
        group_rate_table(df, "mode", "late")
