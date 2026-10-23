from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv


# -----------------------------------------------------------------------------
# Page configuration
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="ASTRA | Data Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

LOGGER = logging.getLogger(__name__)

FILE_PATH = Path(__file__).resolve()
PROJECT_ROOT = FILE_PATH.parents[2] if len(FILE_PATH.parents) >= 3 else Path.cwd()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.ui_theme import apply_astra_theme, render_astra_sidebar

apply_astra_theme("Data Explorer")
render_astra_sidebar("data_explorer")

load_dotenv(PROJECT_ROOT / ".env")

MODELS_DIR = (PROJECT_ROOT / "models").resolve()
RISK_MODEL_PATH = MODELS_DIR / "risk_random_forest_v1.joblib"
RISK_METADATA_PATH = MODELS_DIR / "risk_random_forest_v1.json"

DATASET_FILENAME = "DataCoSupplyChainDataset.csv"
DERIVED_DATE_COLUMN = "Order Date Parsed"

FILTER_KEYS = (
    "filter_market",
    "filter_shipping",
    "filter_segment",
    "filter_category",
    "filter_region",
    "filter_date_range",
)

MODEL_FEATURES = [
    "Shipping Mode",
    "Type",
    "Market",
    "Customer Segment",
    "Category Name",
    "Department Name",
    "Order Item Quantity",
    "Order Item Product Price",
    "Order Item Discount Rate",
]

REQUIRED_COLUMNS = {
    "Order Id",
    "Order Item Id",
    "order date (DateOrders)",
    "shipping date (DateOrders)",
    "Market",
    "Shipping Mode",
    "Customer Segment",
    "Category Name",
    "Department Name",
    "Order Region",
    "Order Country",
    "Order Status",
    "Days for shipment (scheduled)",
    "Days for shipping (real)",
    "Late_delivery_risk",
    "Sales",
    "Type",
    "Order Item Quantity",
    "Order Item Product Price",
    "Order Item Discount",
    "Order Item Discount Rate",
    "Order Item Total",
}

FILTER_CATEGORY_COLUMNS = [
    "Market",
    "Shipping Mode",
    "Customer Segment",
    "Category Name",
    "Department Name",
    "Order Region",
    "Order Country",
    "Type",
]

SAFE_PREVIEW_COLUMNS = [
    "Order Id",
    "Order Item Id",
    "order date (DateOrders)",
    "Market",
    "Order Region",
    "Order Country",
    "Customer Segment",
    "Category Name",
    "Department Name",
    "Type",
    "Shipping Mode",
    "Days for shipment (scheduled)",
    "Order Item Quantity",
    "Order Item Product Price",
    "Order Item Discount Rate",
    "Sales",
    "Late_delivery_risk",
]

SENSITIVE_COLUMN_NAMES = {
    "Customer Email",
    "Customer Fname",
    "Customer Id",
    "Customer Lname",
    "Customer Password",
    "Customer Street",
    "Customer Zipcode",
    "Latitude",
    "Longitude",
    "Order Customer Id",
    "Order Zipcode",
}

PLOTLY_CONFIG = {
    "displaylogo": False,
    "responsive": True,
}

try:
    from src.risk.train import (
        ALL_FEATURES as RISK_MODEL_FEATURES,
        RiskModuleError,
        load_model_artifact,
        predict_risk,
    )
    RISK_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # Keep historical analytics usable if the model layer is unavailable.
    RISK_MODEL_FEATURES = []
    RiskModuleError = RuntimeError
    load_model_artifact = None
    predict_risk = None
    RISK_IMPORT_ERROR = exc


# -----------------------------------------------------------------------------
# Data loading and validation
# -----------------------------------------------------------------------------


def resolve_dataset_path() -> Path | None:
    """Resolve the DataCo CSV without hard-coding a personal Windows path."""

    env_path = os.getenv("ASTRA_DATACO_PATH")

    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path).expanduser())

    candidates.extend(
        [
            PROJECT_ROOT.parent / "archive" / DATASET_FILENAME,
            PROJECT_ROOT / "data" / "raw" / DATASET_FILENAME,
            Path.cwd() / "archive" / DATASET_FILENAME,
            Path.cwd() / "data" / "raw" / DATASET_FILENAME,
        ]
    )

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue

        if resolved.is_file() and resolved.suffix.lower() == ".csv":
            return resolved

    return None


@st.cache_data(show_spinner="Loading DataCo supply-chain dataset...")
def load_dataco(path_string: str, modified_ns: int) -> pd.DataFrame:
    """Load and lightly optimize the DataCo dataset for historical analysis."""

    del modified_ns  # Included only to invalidate the cache when the file changes.
    path = Path(path_string)

    frame = pd.read_csv(
        path,
        encoding="latin-1",
        low_memory=False,
    )

    raw_column_count = len(frame.columns)

    if "order date (DateOrders)" in frame.columns:
        frame[DERIVED_DATE_COLUMN] = pd.to_datetime(
            frame["order date (DateOrders)"],
            errors="coerce",
        )

    for column in FILTER_CATEGORY_COLUMNS:
        if column in frame.columns:
            frame[column] = frame[column].astype("category")

    frame.attrs["raw_column_count"] = raw_column_count
    frame.attrs["duplicate_rows"] = int(
        frame.drop(columns=[DERIVED_DATE_COLUMN], errors="ignore").duplicated().sum()
    )
    frame.attrs["invalid_order_dates"] = int(
        frame[DERIVED_DATE_COLUMN].isna().sum()
        if DERIVED_DATE_COLUMN in frame.columns
        else len(frame)
    )

    return frame


def validate_required_schema(frame: pd.DataFrame) -> list[str]:
    """Return required DataCo fields that are missing."""

    return sorted(REQUIRED_COLUMNS.difference(frame.columns))


def sorted_options(frame: pd.DataFrame, column: str) -> list[str]:
    values = frame[column].dropna().astype(str).unique().tolist()
    return sorted(values)


def consistent_value(frame: pd.DataFrame, column: str) -> Any:
    """Return the single order-level value, '-', or 'MIXED' if inconsistent."""

    values = frame[column].dropna().unique().tolist()
    if len(values) == 0:
        return "-"
    if len(values) == 1:
        return values[0]
    return "MIXED"


def style_figure(
    figure,
    *,
    unified_hover: bool = False,
    height: int = 440,
):
    """Apply a consistent, spacious layout so charts never feel compressed."""

    figure.update_layout(
        autosize=True,
        height=height,
        margin=dict(l=30, r=30, t=70, b=55),
        legend_title_text="",
        title=dict(
            x=0.01,
            xanchor="left",
            font=dict(size=18),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.22,
            xanchor="left",
            x=0,
        ),
    )

    figure.update_xaxes(
        automargin=True,
        title_standoff=12,
    )
    figure.update_yaxes(
        automargin=True,
        title_standoff=12,
    )

    if unified_hover:
        figure.update_layout(hovermode="x unified")

    return figure


def normalize_prediction_input(row: pd.Series) -> dict[str, Any]:
    """Build the exact M3 input contract with predictable Python scalar types."""

    categorical_features = {
        "Shipping Mode",
        "Type",
        "Market",
        "Customer Segment",
        "Category Name",
        "Department Name",
    }
    numeric_features = {
        "Order Item Quantity",
        "Order Item Product Price",
        "Order Item Discount Rate",
    }

    payload: dict[str, Any] = {}

    for feature in MODEL_FEATURES:
        value = row[feature]

        if pd.isna(value):
            payload[feature] = None
        elif feature in categorical_features:
            payload[feature] = str(value)
        elif feature in numeric_features:
            payload[feature] = float(value)
        else:
            payload[feature] = value

    return payload


@st.cache_resource(show_spinner="Loading ASTRA M3 risk model...")
def load_m3_risk_assets(
    model_path_string: str,
    metadata_path_string: str,
    model_modified_ns: int,
    metadata_modified_ns: int,
):
    """Load only ASTRA's fixed, project-local M3 model and aggregate metadata."""

    del model_modified_ns, metadata_modified_ns

    if RISK_IMPORT_ERROR is not None:
        raise RuntimeError("ASTRA risk module could not be imported.") from RISK_IMPORT_ERROR

    if load_model_artifact is None:
        raise RuntimeError("ASTRA risk model loader is unavailable.")

    model_path = Path(model_path_string).resolve()
    metadata_path = Path(metadata_path_string).resolve()

    if model_path.parent != MODELS_DIR or metadata_path.parent != MODELS_DIR:
        raise RuntimeError("Risk artifacts must remain inside ASTRA's models directory.")

    if model_path.name != "risk_random_forest_v1.joblib":
        raise RuntimeError("Unexpected risk-model artifact name.")

    if metadata_path.name != "risk_random_forest_v1.json":
        raise RuntimeError("Unexpected risk-model metadata name.")

    pipeline = load_model_artifact(model_path)

    with metadata_path.open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)

    if not isinstance(metadata, dict):
        raise RuntimeError("Risk-model metadata is not a valid object.")

    model_version = str(metadata.get("model_version", "")).strip()
    if not model_version:
        raise RuntimeError("Risk-model metadata is missing model_version.")

    metadata_features = (
        list(metadata.get("features_categorical", []))
        + list(metadata.get("features_numeric", []))
    )

    if metadata_features and metadata_features != MODEL_FEATURES:
        raise RuntimeError(
            "Dashboard prediction contract does not match the model metadata."
        )

    if list(RISK_MODEL_FEATURES) != MODEL_FEATURES:
        raise RuntimeError(
            "Dashboard prediction contract does not match src.risk.train.ALL_FEATURES."
        )

    return pipeline, metadata


# -----------------------------------------------------------------------------
# Page header and dataset checks
# -----------------------------------------------------------------------------

st.title("ASTRA Data Explorer")
st.caption("Supply Chain Visual Intelligence • Historical Data Analysis")

st.info(
    "This page analyzes historical DataCo records. Historical outcome fields "
    "are intentionally kept separate from ASTRA's prediction-time feature set."
)

DATASET_PATH = resolve_dataset_path()

if DATASET_PATH is None:
    st.error(
        "ASTRA could not locate DataCoSupplyChainDataset.csv. Set "
        "ASTRA_DATACO_PATH in .env, or place the file in the project's "
        "data/raw folder or the sibling archive folder."
    )
    st.stop()

try:
    source_stat = DATASET_PATH.stat()
    data = load_dataco(str(DATASET_PATH), source_stat.st_mtime_ns)
except Exception:
    LOGGER.exception("ASTRA failed to load the DataCo dataset.")
    st.error(
        "ASTRA could not load the DataCo dataset. Check the terminal log for "
        "the technical error; internal path details are not displayed here."
    )
    st.stop()

missing_columns = validate_required_schema(data)
if missing_columns:
    st.error(
        "The selected CSV does not match the required DataCo schema. "
        "ASTRA stopped before running analytics."
    )
    with st.expander("Missing required columns"):
        st.write(missing_columns)
    st.stop()

st.success("DataCo dataset loaded and schema-checked successfully.")


# -----------------------------------------------------------------------------
# Dataset health summary
# -----------------------------------------------------------------------------

with st.expander("Dataset Health", expanded=False):
    health1, health2, health3, health4, health5 = st.columns(5)

    with health1:
        st.metric("Records", f"{len(data):,}")
    with health2:
        st.metric("Source Features", f"{data.attrs.get('raw_column_count', 0):,}")
    with health3:
        st.metric("Unique Orders", f"{data['Order Id'].nunique():,}")
    with health4:
        st.metric("Duplicate Rows", f"{data.attrs.get('duplicate_rows', 0):,}")
    with health5:
        st.metric(
            "Invalid Order Dates",
            f"{data.attrs.get('invalid_order_dates', 0):,}",
        )

    st.caption(
        "DataCo is represented at order-item record level. Record counts and "
        "unique order counts are therefore reported separately."
    )


# -----------------------------------------------------------------------------
# Filters
# -----------------------------------------------------------------------------

st.subheader("Explore Supply Chain Data")
st.caption(
    "All historical analytics and the Order Inspector respond to this scope."
)

min_order_date = data[DERIVED_DATE_COLUMN].min()
max_order_date = data[DERIVED_DATE_COLUMN].max()

if pd.isna(min_order_date) or pd.isna(max_order_date):
    st.error("ASTRA could not establish a valid order-date range.")
    st.stop()

full_date_range = (min_order_date.date(), max_order_date.date())


def clear_filters() -> None:
    st.session_state["filter_market"] = []
    st.session_state["filter_shipping"] = []
    st.session_state["filter_segment"] = []
    st.session_state["filter_category"] = []
    st.session_state["filter_region"] = []
    st.session_state["filter_date_range"] = full_date_range


filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    selected_markets = st.multiselect(
        "Market",
        options=sorted_options(data, "Market"),
        placeholder="All markets",
        key="filter_market",
    )

with filter_col2:
    selected_shipping_modes = st.multiselect(
        "Shipping Mode",
        options=sorted_options(data, "Shipping Mode"),
        placeholder="All shipping modes",
        key="filter_shipping",
    )

with filter_col3:
    selected_segments = st.multiselect(
        "Customer Segment",
        options=sorted_options(data, "Customer Segment"),
        placeholder="All customer segments",
        key="filter_segment",
    )

filter_col4, filter_col5, filter_col6 = st.columns(3)

with filter_col4:
    selected_categories = st.multiselect(
        "Product Category",
        options=sorted_options(data, "Category Name"),
        placeholder="All categories",
        key="filter_category",
    )

with filter_col5:
    selected_regions = st.multiselect(
        "Order Region",
        options=sorted_options(data, "Order Region"),
        placeholder="All regions",
        key="filter_region",
    )

with filter_col6:
    selected_date_range = st.date_input(
        "Order Date Range",
        value=full_date_range,
        min_value=full_date_range[0],
        max_value=full_date_range[1],
        key="filter_date_range",
    )

st.button("Clear All Filters", on_click=clear_filters)

mask = pd.Series(True, index=data.index)

if selected_markets:
    mask &= data["Market"].astype(str).isin(selected_markets)
if selected_shipping_modes:
    mask &= data["Shipping Mode"].astype(str).isin(selected_shipping_modes)
if selected_segments:
    mask &= data["Customer Segment"].astype(str).isin(selected_segments)
if selected_categories:
    mask &= data["Category Name"].astype(str).isin(selected_categories)
if selected_regions:
    mask &= data["Order Region"].astype(str).isin(selected_regions)

if isinstance(selected_date_range, (tuple, list)) and len(selected_date_range) == 2:
    start_date, end_date = selected_date_range
    start_timestamp = pd.Timestamp(start_date)
    end_timestamp = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    mask &= data[DERIVED_DATE_COLUMN].between(start_timestamp, end_timestamp)

filtered_data = data.loc[mask]

if filtered_data.empty:
    st.warning("No records match the selected filters. Change or clear a filter.")
    st.stop()

filtered_unique_orders = filtered_data["Order Id"].nunique()
st.write(
    f"**Showing {len(filtered_data):,} of {len(data):,} historical records, "
    f"representing {filtered_unique_orders:,} unique orders.**"
)


# -----------------------------------------------------------------------------
# Executive overview
# -----------------------------------------------------------------------------

st.divider()
st.header("Supply Chain Visual Intelligence")
st.caption("Metrics below are recalculated from the current historical scope.")

total_records = len(filtered_data)
late_records = int((filtered_data["Late_delivery_risk"] == 1).sum())
late_rate = (late_records / total_records) * 100 if total_records else 0.0
total_sales = float(filtered_data["Sales"].sum())
unique_countries = int(filtered_data["Order Country"].nunique())
unique_categories = int(filtered_data["Category Name"].nunique())

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric("Records Analyzed", f"{total_records:,}")
with kpi2:
    st.metric("Unique Orders Represented", f"{filtered_unique_orders:,}")
with kpi3:
    st.metric("Historical Late Rate", f"{late_rate:.2f}%")

kpi4, kpi5, kpi6 = st.columns(3)
with kpi4:
    st.metric("Total Sales", f"${total_sales:,.0f}")
with kpi5:
    st.metric("Countries", f"{unique_countries:,}")
with kpi6:
    st.metric("Product Categories", f"{unique_categories:,}")

st.caption(
    "Late rate is descriptive and record-level; it is not the output of the "
    "M3 predictive model."
)


# -----------------------------------------------------------------------------
# Visual intelligence workspace
# -----------------------------------------------------------------------------

st.divider()
st.subheader("Visual Intelligence Workspace")
st.caption(
    "Charts are separated into focused tabs so every visualization gets the "
    "full page width and remains readable on laptops and projectors."
)

delivery_tab, geography_tab, product_tab, temporal_tab = st.tabs(
    ["Delivery", "Geography", "Products", "Temporal"]
)


# -----------------------------------------------------------------------------
# Delivery intelligence
# -----------------------------------------------------------------------------

with delivery_tab:
    st.markdown("### Delivery Intelligence")
    st.caption(
        "Historical delivery outcomes and record-level late-delivery behavior."
    )

    delivery_counts = (
        filtered_data["Late_delivery_risk"]
        .map({0: "Not Late", 1: "Late"})
        .value_counts()
        .rename_axis("Delivery Outcome")
        .reset_index(name="Records")
    )

    fig_delivery = px.pie(
        delivery_counts,
        names="Delivery Outcome",
        values="Records",
        hole=0.55,
        title="Historical Delivery Outcomes",
    )
    fig_delivery.update_traces(
        textposition="inside",
        textinfo="percent+label",
    )
    st.plotly_chart(
        style_figure(fig_delivery, height=460),
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key="delivery_outcome_chart",
    )

    shipping_risk = (
        filtered_data.groupby("Shipping Mode", observed=True, as_index=False)[
            "Late_delivery_risk"
        ]
        .mean()
        .rename(columns={"Late_delivery_risk": "Late Rate"})
    )
    shipping_risk["Late Rate (%)"] = shipping_risk["Late Rate"] * 100

    fig_shipping = px.bar(
        shipping_risk,
        x="Shipping Mode",
        y="Late Rate (%)",
        title="Historical Late Rate by Shipping Mode",
        text_auto=".1f",
    )
    fig_shipping.update_yaxes(
        range=[0, 100],
        title="Late Rate (%)",
    )
    fig_shipping.update_traces(
        textposition="outside",
        cliponaxis=False,
    )
    st.plotly_chart(
        style_figure(fig_shipping, height=470),
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key="shipping_risk_chart",
    )


# -----------------------------------------------------------------------------
# Geographic intelligence
# -----------------------------------------------------------------------------

with geography_tab:
    st.markdown("### Geographic Intelligence")
    st.caption(
        "Compare historical record volume and late-delivery behavior across markets."
    )

    market_records = (
        filtered_data["Market"]
        .value_counts()
        .rename_axis("Market")
        .reset_index(name="Records")
    )

    fig_market = px.bar(
        market_records,
        x="Market",
        y="Records",
        title="Record Volume by Market",
        text_auto=True,
    )
    fig_market.update_traces(
        textposition="outside",
        cliponaxis=False,
    )
    st.plotly_chart(
        style_figure(fig_market, height=470),
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key="market_volume_chart",
    )

    market_risk = (
        filtered_data.groupby("Market", observed=True, as_index=False)[
            "Late_delivery_risk"
        ]
        .mean()
        .rename(columns={"Late_delivery_risk": "Late Rate"})
    )
    market_risk["Late Rate (%)"] = market_risk["Late Rate"] * 100

    fig_market_risk = px.bar(
        market_risk,
        x="Market",
        y="Late Rate (%)",
        title="Historical Late Rate by Market",
        text_auto=".1f",
    )
    fig_market_risk.update_yaxes(
        range=[0, 100],
        title="Late Rate (%)",
    )
    fig_market_risk.update_traces(
        textposition="outside",
        cliponaxis=False,
    )
    st.plotly_chart(
        style_figure(fig_market_risk, height=470),
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key="market_risk_chart",
    )


# -----------------------------------------------------------------------------
# Product intelligence
# -----------------------------------------------------------------------------

with product_tab:
    st.markdown("### Product Intelligence")
    st.caption(
        "Top product categories within the currently selected historical scope."
    )

    category_records = (
        filtered_data["Category Name"]
        .value_counts()
        .head(10)
        .rename_axis("Category")
        .reset_index(name="Records")
    )

    fig_categories = px.bar(
        category_records.sort_values("Records"),
        x="Records",
        y="Category",
        orientation="h",
        title="Top 10 Product Categories by Record Volume",
        text_auto=True,
    )
    fig_categories.update_traces(
        textposition="outside",
        cliponaxis=False,
    )
    fig_categories.update_layout(
        yaxis=dict(categoryorder="total ascending"),
    )
    st.plotly_chart(
        style_figure(fig_categories, height=560),
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key="product_category_chart",
    )


# -----------------------------------------------------------------------------
# Temporal intelligence
# -----------------------------------------------------------------------------

with temporal_tab:
    st.markdown("### Temporal Intelligence")
    st.caption(
        "Order date is the historical time reference. Change granularity without "
        "reloading the source file."
    )

    granularity = st.radio(
        "Time Granularity",
        options=["Month", "Quarter", "Year"],
        horizontal=True,
        key="temporal_granularity",
    )

    period_codes = {"Month": "M", "Quarter": "Q", "Year": "Y"}
    period_code = period_codes[granularity]

    temporal_data = filtered_data.loc[
        filtered_data[DERIVED_DATE_COLUMN].notna(),
        [DERIVED_DATE_COLUMN, "Late_delivery_risk", "Sales", "Order Id"],
    ].copy()

    if temporal_data.empty:
        st.warning("No valid order dates are available for the current filters.")
    else:
        temporal_data["Period"] = (
            temporal_data[DERIVED_DATE_COLUMN]
            .dt.to_period(period_code)
            .dt.to_timestamp()
        )

        temporal_intelligence = (
            temporal_data.groupby("Period", as_index=False)
            .agg(
                Records=("Late_delivery_risk", "size"),
                Unique_Orders=("Order Id", "nunique"),
                Late_Records=("Late_delivery_risk", "sum"),
                Sales=("Sales", "sum"),
            )
            .sort_values("Period")
        )

        temporal_intelligence["Late Rate (%)"] = (
            temporal_intelligence["Late_Records"]
            / temporal_intelligence["Records"]
            * 100
        )

        fig_records_time = px.line(
            temporal_intelligence,
            x="Period",
            y="Records",
            title=f"{granularity}ly Record Activity",
            markers=True,
        )
        fig_records_time.update_layout(
            xaxis_title=granularity,
            yaxis_title="Records",
        )
        st.plotly_chart(
            style_figure(
                fig_records_time,
                unified_hover=True,
                height=470,
            ),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="temporal_record_activity_chart",
        )

        fig_sales_time = px.line(
            temporal_intelligence,
            x="Period",
            y="Sales",
            title=f"{granularity}ly Sales Activity",
            markers=True,
        )
        fig_sales_time.update_layout(
            xaxis_title=granularity,
            yaxis_title="Sales",
        )
        st.plotly_chart(
            style_figure(
                fig_sales_time,
                unified_hover=True,
                height=470,
            ),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="temporal_sales_chart",
        )

        fig_late_time = px.line(
            temporal_intelligence,
            x="Period",
            y="Late Rate (%)",
            title="Historical Late Delivery Rate Over Time",
            markers=True,
        )
        fig_late_time.update_layout(
            xaxis_title=granularity,
            yaxis_title="Late Rate (%)",
            yaxis_range=[0, 100],
        )
        st.plotly_chart(
            style_figure(
                fig_late_time,
                unified_hover=True,
                height=470,
            ),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="temporal_late_rate_chart",
        )


# -----------------------------------------------------------------------------
# Order Inspector
# -----------------------------------------------------------------------------

st.divider()
st.header("Order Inspector")
st.caption(
    "Choose an order represented by the current filters. The inspector then "
    "shows the complete order from the original DataCo dataset so item-level "
    "filters do not silently hide sibling items."
)

candidate_order_ids = pd.Index(filtered_data["Order Id"].dropna().unique())
if candidate_order_ids.empty:
    st.warning("No orders are available for the current filters.")
    st.stop()

candidate_order_ids_int = sorted(int(value) for value in candidate_order_ids)
candidate_order_id_set = set(candidate_order_ids_int)
default_order_id = candidate_order_ids_int[0]

st.caption(f"{len(candidate_order_ids_int):,} unique orders match the current scope.")

order_id_text = st.text_input(
    "Order ID",
    value=str(default_order_id),
    help="Enter a DataCo Order Id. Text input is used instead of a 65k-item dropdown for speed.",
)

try:
    selected_order_id = int(order_id_text.strip())
except ValueError:
    st.warning("Order ID must be an integer.")
    st.stop()

if selected_order_id not in candidate_order_id_set:
    st.warning(
        "That order is not represented by the current filters. Clear filters "
        "or enter another Order ID."
    )
    st.stop()

selected_order = data.loc[data["Order Id"] == selected_order_id].copy()

if selected_order.empty:
    st.warning("ASTRA could not retrieve the selected order.")
    st.stop()

# Fields expected to be consistent across sibling order-item rows.
order_level_fields = [
    "order date (DateOrders)",
    "Market",
    "Order Region",
    "Order Country",
    "Customer Segment",
    "Shipping Mode",
    "Days for shipment (scheduled)",
    "Days for shipping (real)",
    "Order Status",
    "Late_delivery_risk",
]

inconsistent_fields = [
    field
    for field in order_level_fields
    if selected_order[field].nunique(dropna=False) > 1
]

if inconsistent_fields:
    st.warning(
        "This order contains inconsistent values in fields normally treated as "
        "order-level context. ASTRA displays MIXED rather than silently taking "
        "the first row."
    )
    with st.expander("Inconsistent order-level fields"):
        st.write(inconsistent_fields)

st.subheader(f"Order #{selected_order_id}")
summary1, summary2, summary3, summary4 = st.columns(4)

with summary1:
    st.metric("Order-Item Records", f"{len(selected_order):,}")
with summary2:
    st.metric("Market", str(consistent_value(selected_order, "Market")))
with summary3:
    st.metric(
        "Customer Segment",
        str(consistent_value(selected_order, "Customer Segment")),
    )
with summary4:
    st.metric("Shipping Mode", str(consistent_value(selected_order, "Shipping Mode")))

st.subheader("Order Profile")
profile1, profile2, profile3 = st.columns(3)

with profile1:
    st.write("**Order Date**")
    st.write(str(consistent_value(selected_order, "order date (DateOrders)")))
    st.write("**Market**")
    st.write(str(consistent_value(selected_order, "Market")))

with profile2:
    st.write("**Region**")
    st.write(str(consistent_value(selected_order, "Order Region")))
    st.write("**Country**")
    st.write(str(consistent_value(selected_order, "Order Country")))

with profile3:
    st.write("**Customer Segment**")
    st.write(str(consistent_value(selected_order, "Customer Segment")))
    st.write("**Order Status**")
    st.write(str(consistent_value(selected_order, "Order Status")))

st.subheader("Historical Delivery Outcome")
delivery1, delivery2, delivery3, delivery4 = st.columns(4)

scheduled_days = consistent_value(selected_order, "Days for shipment (scheduled)")
actual_days = consistent_value(selected_order, "Days for shipping (real)")
historical_late_value = consistent_value(selected_order, "Late_delivery_risk")

if historical_late_value == "MIXED":
    historical_label = "MIXED"
elif historical_late_value == "-":
    historical_label = "-"
else:
    historical_label = "LATE" if int(historical_late_value) == 1 else "NOT LATE"

with delivery1:
    st.metric("Shipping Mode", str(consistent_value(selected_order, "Shipping Mode")))
with delivery2:
    st.metric("Scheduled Days", str(scheduled_days))
with delivery3:
    st.metric("Actual Days", str(actual_days))
with delivery4:
    st.metric("Historical Outcome", historical_label)

st.info(
    "Delivery Status, actual shipping duration, shipping date and the historical "
    "late-delivery outcome are post-outcome information. They are displayed for "
    "historical inspection only and are not forwarded to the M3 model."
)

st.subheader("Order Items")
item_columns = [
    "Order Item Id",
    "Category Name",
    "Department Name",
    "Type",
    "Order Item Quantity",
    "Order Item Product Price",
    "Order Item Discount",
    "Order Item Discount Rate",
    "Order Item Total",
    "Late_delivery_risk",
]

st.dataframe(
    selected_order[item_columns],
    use_container_width=True,
    hide_index=True,
)

total_quantity = float(selected_order["Order Item Quantity"].sum())
total_item_value = float(selected_order["Order Item Total"].sum())
order_total1, order_total2 = st.columns(2)

with order_total1:
    st.metric("Total Item Quantity", f"{total_quantity:,.0f}")
with order_total2:
    st.metric("Recorded Item Total", f"${total_item_value:,.2f}")


# -----------------------------------------------------------------------------
# Prediction-ready record + M3 Risk Intelligence
# -----------------------------------------------------------------------------

st.subheader("Prediction-Ready Record")
st.caption(
    "M3 was trained at DataCo record/order-item representation level. Select one "
    "record to inspect the exact nine legitimate prediction-time features and "
    "run ASTRA's trained Random Forest."
)

item_ids = selected_order["Order Item Id"].dropna().tolist()
selected_item_id = st.selectbox(
    "Order Item Id",
    options=item_ids,
    format_func=lambda value: f"Item #{int(value)}",
)

selected_item = selected_order.loc[
    selected_order["Order Item Id"] == selected_item_id
].iloc[0]

prediction_input = normalize_prediction_input(selected_item)

prediction_input_frame = pd.DataFrame(
    {
        "Feature": list(prediction_input.keys()),
        "Value": [
            "-" if value is None else str(value)
            for value in prediction_input.values()
        ],
    }
)

st.dataframe(
    prediction_input_frame,
    use_container_width=True,
    hide_index=True,
)

missing_prediction_features = [
    feature
    for feature, value in prediction_input.items()
    if value is None
]

if missing_prediction_features:
    st.warning(
        "This record has missing values in required M3 features: "
        + ", ".join(missing_prediction_features)
    )
else:
    st.success(
        "This record contains all nine legitimate M3 prediction-time features."
    )

with st.expander("Prediction Safety Boundary"):
    st.write(
        "Only the nine features shown above are prepared for M3 inference. "
        "Historical outcome and post-outcome fields remain excluded."
    )
    st.write("**Excluded examples:**")
    st.write(
        [
            "Delivery Status",
            "Days for shipping (real)",
            "shipping date (DateOrders)",
            "Late_delivery_risk",
        ]
    )


# -----------------------------------------------------------------------------
# Live M3 inference
# -----------------------------------------------------------------------------

st.subheader("M3 Operational Risk Intelligence")

model_ready = (
    not missing_prediction_features
    and RISK_IMPORT_ERROR is None
    and RISK_MODEL_PATH.is_file()
    and RISK_METADATA_PATH.is_file()
)

if RISK_IMPORT_ERROR is not None:
    LOGGER.exception(
        "ASTRA could not import the M3 risk module.",
        exc_info=RISK_IMPORT_ERROR,
    )
    st.error(
        "The M3 risk module could not be imported. Historical analytics remain "
        "available; check the terminal log for the technical error."
    )

elif not RISK_MODEL_PATH.is_file() or not RISK_METADATA_PATH.is_file():
    st.error(
        "The trusted M3 model or metadata file is missing from the project's "
        "models directory."
    )

elif missing_prediction_features:
    st.info(
        "M3 inference is disabled until all nine required prediction-time "
        "features are present."
    )

else:
    try:
        model_stat = RISK_MODEL_PATH.stat()
        metadata_stat = RISK_METADATA_PATH.stat()

        risk_pipeline, risk_metadata = load_m3_risk_assets(
            str(RISK_MODEL_PATH),
            str(RISK_METADATA_PATH),
            model_stat.st_mtime_ns,
            metadata_stat.st_mtime_ns,
        )

        model_version = str(risk_metadata["model_version"])

        prediction = predict_risk(
            risk_pipeline,
            prediction_input,
            model_version=model_version,
        )

        probability = float(prediction.late_delivery_probability)
        predicted_class = int(prediction.predicted_class)
        predicted_label = "LATE" if predicted_class == 1 else "NOT LATE"

        historical_value = selected_item.get("Late_delivery_risk")
        historical_class = (
            int(historical_value)
            if pd.notna(historical_value)
            else None
        )
        historical_item_label = (
            "LATE"
            if historical_class == 1
            else "NOT LATE"
            if historical_class == 0
            else "UNKNOWN"
        )

        risk_col1, risk_col2, risk_col3, risk_col4 = st.columns(4)

        with risk_col1:
            st.metric(
                "Late-Delivery Probability",
                f"{probability * 100:.1f}%",
            )

        with risk_col2:
            st.metric("Predicted Class", predicted_label)

        with risk_col3:
            st.metric("Historical Outcome", historical_item_label)

        with risk_col4:
            st.metric("Model Version", prediction.model_version)

        st.progress(
            max(0.0, min(1.0, probability)),
            text=f"M3 estimated late-delivery probability: {probability * 100:.1f}%",
        )

        if historical_class is not None:
            if predicted_class == historical_class:
                st.success(
                    "Retrospective class agreement: the M3 default 0.5-threshold "
                    "class matches this record's historical outcome."
                )
            else:
                st.warning(
                    "Retrospective class disagreement: the M3 default 0.5-threshold "
                    "class differs from this record's historical outcome. This is "
                    "expected for some records and should not be hidden."
                )

        st.info(
            "This probability is a historical model estimate, not a causal "
            "guarantee and not an autonomous logistics action."
        )

        # Store the exact, non-leaky handoff for the forthcoming Scenario Lab.
        st.session_state["astra_selected_order_id"] = int(selected_order_id)
        st.session_state["astra_selected_item_id"] = int(selected_item_id)
        st.session_state["astra_risk_input"] = prediction_input.copy()
        st.session_state["astra_baseline_probability"] = probability
        st.session_state["astra_baseline_predicted_class"] = predicted_class
        st.session_state["astra_risk_model_version"] = prediction.model_version

        metrics = risk_metadata.get("metrics_test_set", {})
        limitations = risk_metadata.get("known_limitations", [])

        with st.expander("Model Evidence & Limitations"):
            evidence1, evidence2, evidence3, evidence4 = st.columns(4)

            with evidence1:
                roc_auc = metrics.get("roc_auc")
                st.metric(
                    "Test ROC-AUC",
                    f"{float(roc_auc):.3f}" if roc_auc is not None else "-",
                )

            with evidence2:
                f1 = metrics.get("f1")
                st.metric(
                    "Test F1",
                    f"{float(f1):.3f}" if f1 is not None else "-",
                )

            with evidence3:
                accuracy = metrics.get("accuracy")
                st.metric(
                    "Test Accuracy",
                    f"{float(accuracy) * 100:.1f}%"
                    if accuracy is not None
                    else "-",
                )

            with evidence4:
                n_samples = metrics.get("n_samples")
                st.metric(
                    "Holdout Records",
                    f"{int(n_samples):,}" if n_samples is not None else "-",
                )

            st.write(
                "**Evaluation:** chronological holdout on historical DataCo data."
            )

            if limitations:
                st.write("**Known limitations:**")
                for limitation in limitations:
                    st.write(f"- {limitation}")

            st.caption(
                "The displayed test metrics describe the historical evaluation "
                "population and do not establish production generalization."
            )

    except (RiskModuleError, OSError, ValueError, TypeError, KeyError, RuntimeError):
        LOGGER.exception("ASTRA M3 inference failed.")
        st.error(
            "ASTRA could not complete M3 inference for this record. The error "
            "was logged locally; no internal model path or traceback is exposed "
            "in the dashboard."
        )


# -----------------------------------------------------------------------------
# Privacy-safe preview and schema inspection
# -----------------------------------------------------------------------------

st.divider()
st.subheader("Privacy-Safe Data Preview")
st.caption(
    "The raw dataset contains customer-related fields. ASTRA does not expose "
    "those values in the general dashboard preview."
)

preview_columns = [
    column for column in SAFE_PREVIEW_COLUMNS if column in filtered_data.columns
]

preview_limit = st.slider(
    "Preview records",
    min_value=10,
    max_value=200,
    value=50,
    step=10,
)

st.dataframe(
    filtered_data[preview_columns].head(preview_limit),
    use_container_width=True,
    hide_index=True,
)

with st.expander("View Dataset Schema"):
    schema_rows = []
    for column in data.columns:
        if column == DERIVED_DATE_COLUMN:
            continue
        classification = (
            "Sensitive / restricted preview"
            if column in SENSITIVE_COLUMN_NAMES
            else "Standard historical field"
        )
        schema_rows.append(
            {
                "Column": column,
                "Data Type": str(data[column].dtype),
                "Preview Classification": classification,
            }
        )

    st.dataframe(
        pd.DataFrame(schema_rows),
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    "ASTRA Data Explorer is historical decision-support tooling. It does not "
    "execute procurement, logistics or supplier actions."
)
