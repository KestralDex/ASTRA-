"""
Small reusable helpers for exploratory data analysis (Milestone 2+).

WHY THIS FILE EXISTS
---------------------
Milestone 2 repeatedly needs the same computation: "for each category of
column X, how many rows are there, and what fraction have
Late_delivery_risk == 1?" Writing this once here means every EDA
section (categorical, geographic, shipping-mode) uses identical logic
and is testable — instead of six slightly-different groupby snippets
scattered across a notebook that can't be unit tested.

This module is observational only — it computes and returns summary
tables, it does not train anything or modify the source data.
"""

import pandas as pd


def group_rate_table(
    df: pd.DataFrame,
    group_col: str,
    target_col: str,
    min_count_warning_threshold: int = 30,
) -> pd.DataFrame:
    """
    For each category in group_col, compute sample count, positive
    (target==1) count, and positive rate.

    INPUT:
        df — source DataFrame.
        group_col — categorical column to group by (e.g. "Shipping Mode").
        target_col — binary (0/1) column to compute the rate of
            (e.g. "Late_delivery_risk").
        min_count_warning_threshold — categories with fewer rows than
            this get flagged in the 'low_sample_warning' column, since a
            rate computed from very few rows is unstable and shouldn't
            be read as a reliable pattern.

    OUTPUT:
        DataFrame with columns: group_col, 'sample_count', 'positive_count',
        'positive_rate', 'low_sample_warning' — sorted by sample_count
        descending (largest, most reliable groups first).

    Raises ValueError if either column doesn't exist, or if target_col
    contains values other than 0/1 — this function is specifically for
    binary rate tables, not general aggregation.
    """
    if group_col not in df.columns:
        raise ValueError(f"group_col '{group_col}' not found in DataFrame.")
    if target_col not in df.columns:
        raise ValueError(f"target_col '{target_col}' not found in DataFrame.")

    unique_target_values = set(df[target_col].dropna().unique().tolist())
    if not unique_target_values.issubset({0, 1}):
        raise ValueError(
            f"target_col '{target_col}' must be binary (0/1), "
            f"found values: {unique_target_values}"
        )

    grouped = df.groupby(group_col, dropna=False)[target_col].agg(
        sample_count="count",
        positive_count="sum",
    )
    grouped["positive_rate"] = (grouped["positive_count"] / grouped["sample_count"]).round(4)
    grouped["low_sample_warning"] = grouped["sample_count"] < min_count_warning_threshold

    result = grouped.reset_index().sort_values("sample_count", ascending=False)
    return result.reset_index(drop=True)
