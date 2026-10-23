from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st


# -----------------------------------------------------------------------------
# Page configuration
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="ASTRA | Scenario Lab",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

LOGGER = logging.getLogger(__name__)

FILE_PATH = Path(__file__).resolve()
PROJECT_ROOT = FILE_PATH.parents[2] if len(FILE_PATH.parents) >= 3 else Path.cwd()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.ui_theme import apply_astra_theme, render_astra_sidebar

apply_astra_theme("Scenario Lab")
render_astra_sidebar("scenario_lab")

MODELS_DIR = (PROJECT_ROOT / "models").resolve()
RISK_MODEL_PATH = MODELS_DIR / "risk_random_forest_v1.joblib"
RISK_METADATA_PATH = MODELS_DIR / "risk_random_forest_v1.json"

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

KNOWN_SHIPPING_MODES = [
    "Standard Class",
    "Second Class",
    "First Class",
    "Same Day",
]

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
except Exception as exc:
    RISK_MODEL_FEATURES = []
    RiskModuleError = RuntimeError
    load_model_artifact = None
    predict_risk = None
    RISK_IMPORT_ERROR = exc


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def style_figure(figure, *, height: int = 430):
    figure.update_layout(
        autosize=True,
        height=height,
        margin=dict(l=30, r=30, t=70, b=55),
        title=dict(x=0.01, xanchor="left", font=dict(size=18)),
        showlegend=False,
    )
    figure.update_xaxes(automargin=True, title_standoff=12)
    figure.update_yaxes(automargin=True, title_standoff=12)
    return figure


def clean_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the exact M3 contract with stable Python scalar types."""

    missing = [feature for feature in MODEL_FEATURES if feature not in payload]
    if missing:
        raise ValueError(
            "Scenario baseline is missing required M3 features: "
            + ", ".join(missing)
        )

    cleaned: dict[str, Any] = {}

    for feature in MODEL_FEATURES:
        value = payload[feature]

        if value is None or pd.isna(value):
            raise ValueError(f"Scenario baseline has a missing value for {feature}.")

        if feature in {
            "Order Item Quantity",
            "Order Item Product Price",
            "Order Item Discount Rate",
        }:
            cleaned[feature] = float(value)
        else:
            cleaned[feature] = str(value)

    return cleaned


@st.cache_resource(show_spinner="Loading ASTRA M3 risk model...")
def load_m3_risk_assets(
    model_path_string: str,
    metadata_path_string: str,
    model_modified_ns: int,
    metadata_modified_ns: int,
):
    """Load only ASTRA's fixed, project-local M3 model and metadata."""

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
            "Scenario Lab feature contract does not match model metadata."
        )

    if list(RISK_MODEL_FEATURES) != MODEL_FEATURES:
        raise RuntimeError(
            "Scenario Lab feature contract does not match src.risk.train.ALL_FEATURES."
        )

    return pipeline, metadata


def reset_scenario_widgets() -> None:
    for key in (
        "scenario_shipping_mode",
        "scenario_quantity",
        "scenario_price",
        "scenario_discount_rate",
        "astra_scenario_result",
        "astra_review_decision",
        "astra_review_note",
        "astra_review_record",
    ):
        st.session_state.pop(key, None)


# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------

st.title("ASTRA Scenario Lab")
st.caption(
    "Model-based what-if simulation • M3 Operational Risk • Human review required"
)

st.info(
    "Scenario Lab changes legitimate prediction-time inputs and reruns the same "
    "trained M3 model. A lower or higher probability is a model response to the "
    "changed input profile — not proof that the change causes the outcome."
)


# -----------------------------------------------------------------------------
# Handoff validation
# -----------------------------------------------------------------------------

baseline_raw = st.session_state.get("astra_risk_input")
selected_order_id = st.session_state.get("astra_selected_order_id")
selected_item_id = st.session_state.get("astra_selected_item_id")

if baseline_raw is None:
    st.warning(
        "No prediction-ready record has been handed to Scenario Lab yet. "
        "Open Data Explorer, inspect an order item, and obtain an M3 prediction first."
    )

    if st.button("Go to Data Explorer", type="primary"):
        try:
            st.switch_page("pages/1_Data_Explorer.py")
        except Exception:
            st.info(
                "Use the Streamlit page navigation to open Data Explorer."
            )
    st.stop()

try:
    baseline_input = clean_payload(dict(baseline_raw))
except (TypeError, ValueError) as exc:
    LOGGER.exception("Scenario baseline validation failed.")
    st.error(
        "The selected record cannot be used for Scenario Lab because its "
        "prediction handoff is incomplete. Return to Data Explorer and select it again."
    )
    st.stop()

if RISK_IMPORT_ERROR is not None:
    LOGGER.exception(
        "ASTRA could not import the M3 risk module.",
        exc_info=RISK_IMPORT_ERROR,
    )
    st.error(
        "The M3 risk module could not be imported. Check the local terminal log."
    )
    st.stop()

if not RISK_MODEL_PATH.is_file() or not RISK_METADATA_PATH.is_file():
    st.error(
        "The trusted M3 model or metadata file is missing from ASTRA's models directory."
    )
    st.stop()


# -----------------------------------------------------------------------------
# Load model + recompute baseline under the current artifact
# -----------------------------------------------------------------------------

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

    baseline_prediction = predict_risk(
        risk_pipeline,
        baseline_input,
        model_version=model_version,
    )

    baseline_probability = float(
        baseline_prediction.late_delivery_probability
    )
    baseline_class = int(baseline_prediction.predicted_class)

except (RiskModuleError, OSError, ValueError, TypeError, KeyError, RuntimeError):
    LOGGER.exception("ASTRA could not prepare Scenario Lab.")
    st.error(
        "ASTRA could not prepare the Scenario Lab with the current M3 artifact. "
        "The technical error was logged locally."
    )
    st.stop()


# -----------------------------------------------------------------------------
# Baseline context
# -----------------------------------------------------------------------------

st.subheader("Baseline Record")

context1, context2, context3, context4 = st.columns(4)

with context1:
    st.metric(
        "Order",
        f"#{int(selected_order_id)}"
        if selected_order_id is not None
        else "-",
    )

with context2:
    st.metric(
        "Order Item",
        f"#{int(selected_item_id)}"
        if selected_item_id is not None
        else "-",
    )

with context3:
    st.metric(
        "Baseline Late Probability",
        f"{baseline_probability * 100:.1f}%",
    )

with context4:
    st.metric(
        "Model Version",
        baseline_prediction.model_version,
    )

baseline_context = pd.DataFrame(
    {
        "Feature": MODEL_FEATURES,
        "Baseline": [baseline_input[feature] for feature in MODEL_FEATURES],
        "Scenario Role": [
            "Editable operational input",
            "Context — read only",
            "Context — read only",
            "Context — read only",
            "Context — read only",
            "Context — read only",
            "Editable sensitivity input",
            "Editable sensitivity input",
            "Editable sensitivity input",
        ],
    }
)

with st.expander("View Baseline M3 Input Contract"):
    st.dataframe(
        baseline_context,
        use_container_width=True,
        hide_index=True,
    )


# -----------------------------------------------------------------------------
# What-if controls
# -----------------------------------------------------------------------------

st.divider()
st.subheader("What-If Configuration")

st.caption(
    "Shipping Mode is treated as the primary operational scenario lever. "
    "Quantity, price and discount rate are included as model sensitivity inputs. "
    "Market, segment, category, department and transaction type remain read only."
)

shipping_options = list(KNOWN_SHIPPING_MODES)
baseline_shipping = str(baseline_input["Shipping Mode"])

if baseline_shipping not in shipping_options:
    shipping_options.insert(0, baseline_shipping)

if st.button("Reset Scenario to Baseline"):
    reset_scenario_widgets()
    st.rerun()

with st.form("astra_scenario_form"):
    scenario_left, scenario_right = st.columns(2)

    with scenario_left:
        scenario_shipping_mode = st.selectbox(
            "Shipping Mode",
            options=shipping_options,
            index=shipping_options.index(baseline_shipping),
            key="scenario_shipping_mode",
        )

        scenario_quantity = st.number_input(
            "Order Item Quantity",
            min_value=0.0,
            value=float(baseline_input["Order Item Quantity"]),
            step=1.0,
            key="scenario_quantity",
        )

    with scenario_right:
        scenario_price = st.number_input(
            "Order Item Product Price",
            min_value=0.0,
            value=float(baseline_input["Order Item Product Price"]),
            step=1.0,
            format="%.2f",
            key="scenario_price",
        )

        scenario_discount_rate = st.number_input(
            "Order Item Discount Rate",
            min_value=0.0,
            max_value=1.0,
            value=float(baseline_input["Order Item Discount Rate"]),
            step=0.01,
            format="%.3f",
            key="scenario_discount_rate",
        )

    submitted = st.form_submit_button(
        "Run Model-Based Scenario",
        type="primary",
        use_container_width=True,
    )


# -----------------------------------------------------------------------------
# Scenario inference
# -----------------------------------------------------------------------------

if submitted:
    scenario_input = baseline_input.copy()

    scenario_input["Shipping Mode"] = str(scenario_shipping_mode)
    scenario_input["Order Item Quantity"] = float(scenario_quantity)
    scenario_input["Order Item Product Price"] = float(scenario_price)
    scenario_input["Order Item Discount Rate"] = float(scenario_discount_rate)

    try:
        scenario_prediction = predict_risk(
            risk_pipeline,
            scenario_input,
            model_version=model_version,
        )

        scenario_probability = float(
            scenario_prediction.late_delivery_probability
        )
        scenario_class = int(scenario_prediction.predicted_class)
        delta_probability_points = (
            scenario_probability - baseline_probability
        ) * 100

        changed_features = [
            feature
            for feature in MODEL_FEATURES
            if scenario_input[feature] != baseline_input[feature]
        ]

        st.session_state["astra_scenario_result"] = {
            "scenario_input": scenario_input,
            "baseline_probability": baseline_probability,
            "baseline_class": baseline_class,
            "scenario_probability": scenario_probability,
            "scenario_class": scenario_class,
            "delta_probability_points": delta_probability_points,
            "changed_features": changed_features,
            "model_version": scenario_prediction.model_version,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }

        # A new simulation invalidates an earlier human review.
        st.session_state.pop("astra_review_record", None)

    except (RiskModuleError, ValueError, TypeError, KeyError, RuntimeError):
        LOGGER.exception("ASTRA scenario inference failed.")
        st.error(
            "ASTRA could not evaluate this scenario. The technical error was "
            "logged locally and no traceback is exposed in the dashboard."
        )


# -----------------------------------------------------------------------------
# Scenario comparison
# -----------------------------------------------------------------------------

scenario_result = st.session_state.get("astra_scenario_result")

if scenario_result is not None:
    st.divider()
    st.subheader("Scenario Comparison")

    scenario_probability = float(
        scenario_result["scenario_probability"]
    )
    delta_points = float(
        scenario_result["delta_probability_points"]
    )

    compare1, compare2, compare3, compare4 = st.columns(4)

    with compare1:
        st.metric(
            "Baseline Probability",
            f"{baseline_probability * 100:.1f}%",
        )

    with compare2:
        st.metric(
            "Scenario Probability",
            f"{scenario_probability * 100:.1f}%",
        )

    with compare3:
        st.metric(
            "Probability Change",
            f"{delta_points:+.1f} pp",
        )

    with compare4:
        st.metric(
            "Scenario Class",
            "LATE"
            if int(scenario_result["scenario_class"]) == 1
            else "NOT LATE",
        )

    comparison_frame = pd.DataFrame(
        {
            "Case": ["Baseline", "Scenario"],
            "Late-Delivery Probability (%)": [
                baseline_probability * 100,
                scenario_probability * 100,
            ],
        }
    )

    fig_compare = px.bar(
        comparison_frame,
        x="Case",
        y="Late-Delivery Probability (%)",
        title="M3 Baseline vs What-If Probability",
        text_auto=".1f",
    )
    fig_compare.update_yaxes(
        range=[0, 100],
        title="Late-Delivery Probability (%)",
    )
    fig_compare.update_traces(
        textposition="outside",
        cliponaxis=False,
    )

    st.plotly_chart(
        style_figure(fig_compare),
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key="scenario_probability_comparison",
    )

    changed_features = list(scenario_result["changed_features"])

    if not changed_features:
        st.info(
            "No scenario input changed from the baseline, so this run is a "
            "same-input reproducibility check."
        )
    elif delta_points < 0:
        st.success(
            f"The changed input profile produced a {abs(delta_points):.1f} "
            "percentage-point lower M3 late-delivery estimate than baseline."
        )
    elif delta_points > 0:
        st.warning(
            f"The changed input profile produced a {delta_points:.1f} "
            "percentage-point higher M3 late-delivery estimate than baseline."
        )
    else:
        st.info(
            "The changed input profile produced no measurable probability change "
            "at the displayed precision."
        )

    st.caption(
        "Interpret this as model sensitivity under a changed input profile. "
        "Do not interpret the probability difference as a causal treatment effect."
    )

    scenario_input = dict(scenario_result["scenario_input"])

    changed_rows = []
    for feature in MODEL_FEATURES:
        baseline_value = baseline_input[feature]
        scenario_value = scenario_input[feature]
        if baseline_value != scenario_value:
            changed_rows.append(
                {
                    "Feature": feature,
                    "Baseline": baseline_value,
                    "Scenario": scenario_value,
                }
            )

    if changed_rows:
        st.markdown("#### Changed Inputs")
        st.dataframe(
            pd.DataFrame(changed_rows),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Scenario Safety & Evidence"):
        st.write(
            f"**Model:** {scenario_result['model_version']}"
        )
        st.write(
            "**Inference unit:** DataCo record/order-item representation."
        )
        st.write(
            "**Excluded from simulation:** actual shipping duration, shipping date, "
            "Delivery Status and Late_delivery_risk."
        )
        st.write(
            "**Execution boundary:** Scenario Lab does not modify inventory, route "
            "shipments, contact suppliers, place orders, or call external action tools."
        )


    # -------------------------------------------------------------------------
    # Human review
    # -------------------------------------------------------------------------

    st.divider()
    st.subheader("Human Review")

    st.caption(
        "ASTRA stops at decision support. A person must review the scenario before "
        "it can be considered for any downstream operational process."
    )

    review_choice = st.radio(
        "Review Decision",
        options=[
            "Needs further review",
            "Accept scenario for consideration",
            "Reject scenario",
        ],
        key="astra_review_decision",
    )

    review_note = st.text_area(
        "Reviewer Note (optional)",
        max_chars=500,
        placeholder=(
            "Record reasoning only. Do not enter passwords, secrets, or unnecessary "
            "personal information."
        ),
        key="astra_review_note",
    )

    if st.button(
        "Record Human Review",
        type="primary",
        use_container_width=True,
    ):
        review_record = {
            "decision": review_choice,
            "note": review_note.strip(),
            "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
            "order_id": selected_order_id,
            "order_item_id": selected_item_id,
            "baseline_probability": baseline_probability,
            "scenario_probability": scenario_probability,
            "delta_probability_points": delta_points,
            "model_version": scenario_result["model_version"],
            "execution_performed": False,
        }

        st.session_state["astra_review_record"] = review_record

    review_record = st.session_state.get("astra_review_record")

    if review_record is not None:
        st.success(
            "Human review recorded for this session. No operational action was executed."
        )

        review1, review2 = st.columns(2)

        with review1:
            st.write("**Decision**")
            st.write(review_record["decision"])

        with review2:
            st.write("**Execution Performed**")
            st.write("No")

        if review_record["note"]:
            st.write("**Reviewer Note**")
            st.write(review_record["note"])

        st.caption(
            "Current prototype behavior: the review record is session-local and "
            "is not yet persisted to a production audit database."
        )


# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------

st.divider()
st.caption(
    "ASTRA v0.1 • Research decision-support prototype • "
    "Model-based scenario simulation • Human-in-the-loop"
)
