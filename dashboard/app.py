from __future__ import annotations

import html
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.ui_theme import apply_astra_dashboard_theme, render_astra_sidebar

LOGGER = logging.getLogger(__name__)

MODELS_DIR = (PROJECT_ROOT / "models").resolve()
MODEL_PATH = MODELS_DIR / "risk_random_forest_v1.joblib"
METADATA_PATH = MODELS_DIR / "risk_random_forest_v1.json"

DATA_EXPLORER_PAGE = PROJECT_ROOT / "dashboard" / "pages" / "1_Data_Explorer.py"
SCENARIO_LAB_PAGE = PROJECT_ROOT / "dashboard" / "pages" / "2_Scenario_Lab.py"
GOVERNANCE_PAGE = PROJECT_ROOT / "dashboard" / "pages" / "3_Governance.py"

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


st.set_page_config(
    page_title="ASTRA | Supply Chain Intelligence",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_astra_dashboard_theme()


@st.cache_resource(show_spinner="Loading ASTRA M3 risk model...")
def load_astra_model(model_path_string: str, model_modified_ns: int):
    del model_modified_ns

    if RISK_IMPORT_ERROR is not None:
        raise RuntimeError("ASTRA risk module could not be imported.") from RISK_IMPORT_ERROR

    if load_model_artifact is None:
        raise RuntimeError("ASTRA risk model loader is unavailable.")

    model_path = Path(model_path_string).resolve()

    if model_path.parent != MODELS_DIR:
        raise RuntimeError("Risk model must remain inside ASTRA's models directory.")

    if model_path.name != "risk_random_forest_v1.joblib":
        raise RuntimeError("Unexpected ASTRA risk-model artifact.")

    return load_model_artifact(model_path)


@st.cache_data(show_spinner=False)
def load_metadata(metadata_path_string: str, metadata_modified_ns: int) -> dict[str, Any]:
    del metadata_modified_ns

    metadata_path = Path(metadata_path_string).resolve()

    if metadata_path.parent != MODELS_DIR:
        raise RuntimeError("Risk metadata must remain inside ASTRA's models directory.")

    if metadata_path.name != "risk_random_forest_v1.json":
        raise RuntimeError("Unexpected ASTRA risk-model metadata.")

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
            "Command Center prediction contract does not match model metadata."
        )

    if list(RISK_MODEL_FEATURES) != MODEL_FEATURES:
        raise RuntimeError(
            "Command Center prediction contract does not match "
            "src.risk.train.ALL_FEATURES."
        )

    return metadata


def page_available(path: Path) -> bool:
    return path.is_file()


def set_manual_scenario_handoff(
    order: dict[str, Any],
    probability: float,
    predicted_class: int,
    model_version: str,
) -> None:
    st.session_state["astra_selected_order_id"] = None
    st.session_state["astra_selected_item_id"] = None
    st.session_state["astra_risk_input"] = order.copy()
    st.session_state["astra_baseline_probability"] = float(probability)
    st.session_state["astra_baseline_predicted_class"] = int(predicted_class)
    st.session_state["astra_risk_model_version"] = str(model_version)
    st.session_state["astra_prediction_source"] = "command_center_manual_input"


def safe_percent(value: Any, fallback: str = "N/A") -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return fallback


model = None
metadata: dict[str, Any] = {}
model_ready = False

try:
    if not MODEL_PATH.is_file() or not METADATA_PATH.is_file():
        raise RuntimeError("Required M3 model artifact or metadata file is missing.")

    model = load_astra_model(str(MODEL_PATH), MODEL_PATH.stat().st_mtime_ns)
    metadata = load_metadata(
        str(METADATA_PATH),
        METADATA_PATH.stat().st_mtime_ns,
    )
    model_ready = True

except Exception:
    LOGGER.exception("ASTRA Command Center could not initialize the M3 model.")


test_metrics = metadata.get("metrics_test_set", {}) if model_ready else {}
roc_auc = test_metrics.get("roc_auc")
f1 = test_metrics.get("f1")
accuracy = test_metrics.get("accuracy")
n_samples = test_metrics.get("n_samples")
model_version = str(metadata.get("model_version", "unavailable")) if model_ready else "unavailable"

core_ready = (
    model_ready
    and page_available(DATA_EXPLORER_PAGE)
    and page_available(SCENARIO_LAB_PAGE)
    and page_available(GOVERNANCE_PAGE)
)


# -----------------------------------------------------------------------------
# Persistent navigation
# -----------------------------------------------------------------------------

render_astra_sidebar("dashboard")


# -----------------------------------------------------------------------------
# Header
# -----------------------------------------------------------------------------

now_text = datetime.now().strftime("%d %b %Y · %H:%M")

st.markdown(
    f"""
    <div class="astra-header">
        <div>
            <div class="astra-title">ASTRA</div>
            <div class="astra-subtitle">Supply Chain Intelligence Dashboard</div>
        </div>
        <div class="astra-header-actions">
            <div class="astra-top-control">01 Oct 2026 · Demo build</div>
            <div class="astra-top-control">M3 · {html.escape(model_version)}</div>
            <div class="astra-top-control">
                <span class="astra-live-dot"></span>
                {'Core ready' if core_ready else 'Check required'}
            </div>
            <div class="astra-top-control">Updated {html.escape(now_text)}</div>
        </div>
    </div>
    <div class="astra-flow-line">
        October 1 Demo Flow · Real DataCo → M3 Risk → What-if Simulation → Human Review
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Five compact executive cards — same visual rhythm as reference
# -----------------------------------------------------------------------------

k1, k2, k3, k4, k5 = st.columns(5, gap="small")

with k1:
    st.markdown(
        """
        <div class="astra-card astra-kpi">
            <div class="astra-kpi-head">
                <span class="astra-mini-icon mi-green">D</span>
                <span class="astra-kpi-name">DataCo Records</span>
            </div>
            <div class="astra-kpi-main">
                <span class="astra-kpi-value astra-kpi-accent-green">180,519</span>
            </div>
            <div class="astra-kpi-caption">
                Order-item records in the reference operational dataset
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k2:
    st.markdown(
        """
        <div class="astra-card astra-kpi">
            <div class="astra-kpi-head">
                <span class="astra-mini-icon mi-blue">O</span>
                <span class="astra-kpi-name">Unique Orders</span>
            </div>
            <div class="astra-kpi-main">
                <span class="astra-kpi-value astra-kpi-accent-blue">65,752</span>
            </div>
            <div class="astra-kpi-caption">
                Kept separate from record-level M3 inference
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k3:
    st.markdown(
        """
        <div class="astra-card astra-kpi">
            <div class="astra-kpi-head">
                <span class="astra-mini-icon mi-red">L</span>
                <span class="astra-kpi-name">Historical Late Rate</span>
            </div>
            <div class="astra-kpi-main">
                <span class="astra-kpi-value astra-kpi-accent-red">54.8%</span>
            </div>
            <div class="astra-kpi-caption">
                Historical DataCo target prevalence · descriptive only
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k4:
    roc_text = f"{float(roc_auc):.3f}" if roc_auc is not None else "N/A"
    f1_text = f"{float(f1):.3f}" if f1 is not None else "N/A"
    st.markdown(
        f"""
        <div class="astra-card astra-kpi">
            <div class="astra-kpi-head">
                <span class="astra-mini-icon mi-amber">M</span>
                <span class="astra-kpi-name">M3 Model Evidence</span>
            </div>
            <div class="astra-kpi-main">
                <span class="astra-kpi-value astra-kpi-accent-amber">{roc_text}</span>
                <span class="astra-kpi-unit">ROC-AUC</span>
            </div>
            <div class="astra-kpi-caption">
                F1 {f1_text} · chronological holdout evaluation
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k5:
    status_text = "READY" if core_ready else "CHECK"
    status_class = "astra-kpi-accent-green" if core_ready else "astra-kpi-accent-red"
    st.markdown(
        f"""
        <div class="astra-card astra-kpi">
            <div class="astra-kpi-head">
                <span class="astra-mini-icon mi-cyan">✓</span>
                <span class="astra-kpi-name">Core Demo Status</span>
            </div>
            <div class="astra-kpi-main">
                <span class="astra-kpi-value {status_class}">{status_text}</span>
            </div>
            <div class="astra-kpi-caption">
                Risk · Scenario · Human review · Governance
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown("<div style='height:.72rem'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Reference-inspired alert / explanation / recommended-next-steps row
# -----------------------------------------------------------------------------

saved_result = st.session_state.get("astra_command_center_result")
baseline_probability = st.session_state.get("astra_baseline_probability")
baseline_class = st.session_state.get("astra_baseline_predicted_class")

if saved_result is not None:
    signal_probability = float(saved_result["probability"])
    signal_class = int(signal_probability >= 0.5)
    signal_label = "Late-delivery signal" if signal_class == 1 else "Lower late-delivery signal"
    signal_number = f"{signal_probability * 100:.1f}%"
    signal_body = (
        "Current manual M3 estimate using the documented nine prediction-time features."
    )
    signal_tag = "PREDICTED LATE" if signal_class == 1 else "PREDICTED NOT LATE"
    risk_number_class = "" if signal_class == 1 else "astra-risk-number-neutral"
    tag_class = "tag-red" if signal_class == 1 else "tag-blue"
else:
    signal_label = "No active manual risk signal"
    signal_number = "—"
    signal_body = (
        "Run the compact M3 analyzer below, or inspect a real order-item in Data Explorer."
    )
    signal_tag = "AWAITING INPUT"
    risk_number_class = "astra-risk-number-neutral"
    tag_class = "tag-muted"

r1, r2, r3 = st.columns([1.08, 1.15, 1.22], gap="small")

with r1:
    st.markdown(
        f"""
        <div class="astra-card astra-card-pad astra-signal-card astra-signal-red">
            <div class="astra-card-title" style="color:#c9343f;">ACTIVE RISK SIGNAL</div>
            <div class="astra-signal-heading">{html.escape(signal_label)}</div>
            <div class="astra-risk-number {risk_number_class}">{html.escape(signal_number)}</div>
            <div class="astra-tag {tag_class}">{html.escape(signal_tag)}</div>
            <div class="astra-signal-copy">{html.escape(signal_body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r2:
    if saved_result is not None:
        p = float(saved_result["probability"])
        mode = str(saved_result["order"].get("Shipping Mode", "current shipping mode"))
        if p >= 0.75:
            interpretation = (
                f"M3 is assigning a high late-delivery probability to this record. "
                f"The current Shipping Mode is {mode}. In DataCo, Shipping Mode is the "
                f"strongest legitimate feature signal, but this estimate is predictive, not causal."
            )
        elif p >= 0.50:
            interpretation = (
                f"M3 is assigning an elevated late-delivery probability to this record. "
                f"Shipping Mode is a dominant historical signal in the trained model, while "
                f"the remaining legitimate features add more modest incremental information."
            )
        else:
            interpretation = (
                f"M3 currently estimates a lower probability of late delivery for this record. "
                f"The output remains a historical model estimate and should be reviewed alongside "
                f"the actual order context."
            )
    else:
        interpretation = (
            "M3 uses nine leakage-safe planning-time features. Shipping Mode carries most of "
            "the legitimate signal in DataCo: the full feature set improves ROC-AUC only "
            "modestly beyond Shipping Mode alone."
        )

    st.markdown(
        f"""
        <div class="astra-card astra-card-pad astra-signal-card astra-signal-blue">
            <div class="astra-card-title" style="color:#1768d2;">MODEL INTERPRETATION</div>
            <div class="astra-signal-heading">Evidence-aware risk context</div>
            <div class="astra-signal-copy">{html.escape(interpretation)}</div>
            <div class="astra-tag tag-blue">NOT A CAUSAL CLAIM</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with r3:
    st.markdown(
        """
        <div class="astra-card astra-card-pad astra-signal-card astra-signal-green">
            <div class="astra-card-title" style="color:#0a8a61;">NEXT DECISION STEPS</div>
            <div class="astra-next-row">
                <div class="astra-next-index">1</div>
                <div>
                    <div class="astra-next-title">Inspect a real DataCo order-item</div>
                    <div class="astra-next-sub">Validate context before acting on model output</div>
                </div>
            </div>
            <div class="astra-next-row">
                <div class="astra-next-index">2</div>
                <div>
                    <div class="astra-next-title">Run a model-based scenario</div>
                    <div class="astra-next-sub">Compare M3 sensitivity to a changed planning input</div>
                </div>
            </div>
            <div class="astra-next-row">
                <div class="astra-next-index">3</div>
                <div>
                    <div class="astra-next-title">Record human review</div>
                    <div class="astra-next-sub">ASTRA executes no operational action</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    n1, n2 = st.columns(2)

with n1:
    if page_available(DATA_EXPLORER_PAGE):
        st.page_link(
            "pages/1_Data_Explorer.py",
            label="Open Data Explorer",
            use_container_width=True,
        )

with n2:
    if page_available(SCENARIO_LAB_PAGE):
        st.page_link(
            "pages/2_Scenario_Lab.py",
            label="Open Scenario Lab",
            use_container_width=True,
        )



st.markdown("<div style='height:.72rem'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Compact manual analyzer — preserved functionality, no longer dominates UI
# -----------------------------------------------------------------------------

with st.expander("Manual M3 risk analysis", expanded=False):
    st.caption(
        "Optional Command Center input. The presentation path can also start from a real "
        "DataCo order-item in Data Explorer."
    )

    if not model_ready:
        st.error("M3 is unavailable. Check the local terminal log before presenting.")
    else:
        with st.form("risk_analysis_form"):
            a, b, c = st.columns(3)

            with a:
                shipping_mode = st.selectbox(
                    "Shipping Mode",
                    ["Standard Class", "Second Class", "First Class", "Same Day"],
                )
                transaction_type = st.selectbox(
                    "Transaction Type",
                    ["DEBIT", "TRANSFER", "PAYMENT", "CASH"],
                )
                market = st.selectbox(
                    "Market",
                    ["LATAM", "Europe", "Pacific Asia", "USCA", "Africa"],
                )

            with b:
                customer_segment = st.selectbox(
                    "Customer Segment",
                    ["Consumer", "Corporate", "Home Office"],
                )
                category_name = st.text_input(
                    "Category Name",
                    value="Sporting Goods",
                    max_chars=120,
                )
                department_name = st.text_input(
                    "Department Name",
                    value="Fitness",
                    max_chars=120,
                )

            with c:
                quantity = st.number_input(
                    "Order Item Quantity",
                    min_value=1,
                    max_value=100,
                    value=1,
                    step=1,
                )
                product_price = st.number_input(
                    "Product Price",
                    min_value=0.01,
                    max_value=1_000_000.0,
                    value=100.0,
                    step=1.0,
                )
                discount_rate = st.number_input(
                    "Discount Rate",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.10,
                    step=0.01,
                )

            analyze = st.form_submit_button(
                "Analyze Risk",
                type="primary",
                use_container_width=True,
            )

        if analyze:
            clean_category = category_name.strip()
            clean_department = department_name.strip()

            if not clean_category or not clean_department:
                st.error("Category Name and Department Name cannot be empty.")
            else:
                order = {
                    "Shipping Mode": shipping_mode,
                    "Type": transaction_type,
                    "Market": market,
                    "Customer Segment": customer_segment,
                    "Category Name": clean_category,
                    "Department Name": clean_department,
                    "Order Item Quantity": int(quantity),
                    "Order Item Product Price": float(product_price),
                    "Order Item Discount Rate": float(discount_rate),
                }

                try:
                    result = predict_risk(
                        pipeline=model,
                        order=order,
                        model_version=str(metadata["model_version"]),
                    )

                    probability = float(result.late_delivery_probability)
                    prediction_text = (
                        "LATE DELIVERY"
                        if int(result.predicted_class) == 1
                        else "NOT LATE"
                    )

                    set_manual_scenario_handoff(
                        order=order,
                        probability=probability,
                        predicted_class=int(result.predicted_class),
                        model_version=result.model_version,
                    )

                    st.session_state["astra_command_center_result"] = {
                        "probability": probability,
                        "prediction_text": prediction_text,
                        "model_version": result.model_version,
                        "order": order,
                    }

                    st.success(
                        f"M3 result: {probability * 100:.1f}% late-delivery probability "
                        f"· {prediction_text}."
                    )
                    st.rerun()

                except (
                    RiskModuleError,
                    ValueError,
                    TypeError,
                    KeyError,
                    RuntimeError,
                ):
                    LOGGER.exception("ASTRA Command Center M3 prediction failed.")
                    st.error(
                        "ASTRA could not generate the prediction. "
                        "The technical error was logged locally."
                    )


st.markdown("<div style='height:.72rem'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Reference-inspired four-panel intelligence row
# -----------------------------------------------------------------------------

q1, q2, q3, q4 = st.columns([1.12, 1.03, 1.08, 1.12], gap="small")

with q1:
    scenario_prob = st.session_state.get("astra_baseline_probability")
    scenario_class = st.session_state.get("astra_baseline_predicted_class")
    source_text = st.session_state.get("astra_prediction_source", "No baseline selected")

    st.markdown(
        f"""
        <div class="astra-card astra-card-pad astra-lower-card">
            <div class="astra-card-title" style="color:#1768d2;">SCENARIO SIMULATOR</div>
            <div class="astra-signal-heading" style="font-size:.82rem;">
                Current baseline
            </div>
            <div class="astra-rule"></div>
            <div class="astra-metric-row">
                <span class="astra-metric-name">Late-delivery probability</span>
                <span class="astra-metric-val">
                    {f"{float(scenario_prob)*100:.1f}%" if scenario_prob is not None else "—"}
                </span>
            </div>
            <div class="astra-metric-row">
                <span class="astra-metric-name">Predicted class</span>
                <span class="astra-metric-val">
                    {("Late" if int(scenario_class) == 1 else "Not late") if scenario_class is not None else "—"}
                </span>
            </div>
            <div class="astra-metric-row">
                <span class="astra-metric-name">Source</span>
                <span class="astra-metric-val">
                    {html.escape(str(source_text).replace("_"," ").title())}
                </span>
            </div>
            <div class="astra-signal-copy">
                Change a legitimate planning input and rerun the same trained M3 model.
                The delta is sensitivity, not a causal treatment effect.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if page_available(SCENARIO_LAB_PAGE):
        st.page_link(
            "pages/2_Scenario_Lab.py",
            label="Simulate Option",
            use_container_width=True,
        )

with q2:
    auc_width = int(max(0, min(100, float(roc_auc) * 100))) if roc_auc is not None else 0
    f1_width = int(max(0, min(100, float(f1) * 100))) if f1 is not None else 0
    acc_width = int(max(0, min(100, float(accuracy) * 100))) if accuracy is not None else 0
    st.markdown(
        f"""
        <div class="astra-card astra-card-pad astra-lower-card">
            <div class="astra-card-title" style="color:#1768d2;">MODEL PERFORMANCE</div>
            <div class="astra-signal-heading" style="font-size:.82rem;">
                Chronological holdout
            </div>
            <div class="astra-rule"></div>
            <div class="astra-metric-row">
                <span class="astra-metric-name">ROC-AUC</span>
                <span class="astra-metric-val">{f"{float(roc_auc):.3f}" if roc_auc is not None else "N/A"}</span>
            </div>
            <div class="astra-bar-track">
                <div class="astra-bar-fill-blue" style="width:{auc_width}%"></div>
            </div>
            <div style="height:.45rem"></div>
            <div class="astra-metric-row">
                <span class="astra-metric-name">F1</span>
                <span class="astra-metric-val">{f"{float(f1):.3f}" if f1 is not None else "N/A"}</span>
            </div>
            <div class="astra-bar-track">
                <div class="astra-bar-fill-cyan" style="width:{f1_width}%"></div>
            </div>
            <div style="height:.45rem"></div>
            <div class="astra-metric-row">
                <span class="astra-metric-name">Accuracy</span>
                <span class="astra-metric-val">{safe_percent(accuracy)}</span>
            </div>
            <div class="astra-bar-track">
                <div class="astra-bar-fill-green" style="width:{acc_width}%"></div>
            </div>
            <div class="astra-signal-copy">
                Historical evaluation only
                {f" · {int(n_samples):,} holdout records" if n_samples is not None else ""}.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with q3:
    st.markdown(
        """
        <div class="astra-card astra-card-pad astra-lower-card">
            <div class="astra-card-title" style="color:#1768d2;">
                SHIPPING MODE SIGNAL
            </div>
            <div class="astra-signal-heading" style="font-size:.82rem;">
                Historical DataCo profile
            </div>
            <table class="astra-table">
                <thead>
                    <tr>
                        <th>Mode</th>
                        <th>Scheduled days</th>
                        <th>Late rate</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Standard Class</td>
                        <td>4</td>
                        <td class="astra-heat-low">38.1%</td>
                    </tr>
                    <tr>
                        <td>Same Day</td>
                        <td>0</td>
                        <td class="astra-heat-low">45.7%</td>
                    </tr>
                    <tr>
                        <td>Second Class</td>
                        <td>2</td>
                        <td class="astra-heat-med">76.6%</td>
                    </tr>
                    <tr>
                        <td>First Class</td>
                        <td>1</td>
                        <td class="astra-heat-high">95.3%</td>
                    </tr>
                </tbody>
            </table>
            <div class="astra-signal-copy">
                Descriptive association, not causal impact. Shipping Mode and scheduled
                shipping days are perfectly collinear in this dataset.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with q4:
    latest_review = st.session_state.get("astra_human_review_record")
    review_label = "No review recorded"
    if isinstance(latest_review, dict):
        review_label = str(
            latest_review.get("decision")
            or latest_review.get("review_status")
            or latest_review.get("status")
            or "Review recorded"
        )

    st.markdown(
        f"""
        <div class="astra-card astra-card-pad astra-lower-card">
            <div class="astra-card-title" style="color:#1768d2;">GOVERNANCE & REVIEW</div>
            <div class="astra-signal-heading" style="font-size:.82rem;">
                Decision boundary
            </div>
            <div class="astra-rule"></div>
            <div class="astra-status-item">
                <span class="astra-status-name">Leakage-safe feature contract</span>
                <span class="astra-status-badge tag-green">VERIFIED</span>
            </div>
            <div class="astra-status-item">
                <span class="astra-status-name">Prediction features</span>
                <span class="astra-status-badge tag-blue">9 FEATURES</span>
            </div>
            <div class="astra-status-item">
                <span class="astra-status-name">Operational execution</span>
                <span class="astra-status-badge tag-muted">DISABLED</span>
            </div>
            <div class="astra-status-item">
                <span class="astra-status-name">Latest human review</span>
                <span class="astra-status-badge tag-blue">{html.escape(review_label[:24])}</span>
            </div>
            <div class="astra-signal-copy">
                ASTRA supports human decision-making. It does not place orders, modify
                routes, change inventory or make payments.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if page_available(GOVERNANCE_PAGE):
        st.page_link(
            "pages/3_Governance.py",
            label="View Governance",
            use_container_width=True,
        )


st.markdown("<div style='height:.72rem'></div>", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Bottom evidence + human review row
# -----------------------------------------------------------------------------

b1, b2 = st.columns([2.1, 1], gap="small")

with b1:
    st.markdown(
        """
        <div class="astra-card astra-card-pad">
            <div class="astra-card-title" style="color:#1768d2;">EVIDENCE & DATA SOURCES</div>
            <div class="astra-source-grid">
                <div class="astra-source">
                    <span class="astra-source-name">DataCo operational history</span>
                    <span class="astra-source-state">ACTIVE</span>
                </div>
                <div class="astra-source">
                    <span class="astra-source-name">M3 model artifact</span>
                    <span class="astra-source-state">ACTIVE</span>
                </div>
                <div class="astra-source">
                    <span class="astra-source-name">M3 metadata contract</span>
                    <span class="astra-source-state">VERIFIED</span>
                </div>
                <div class="astra-source">
                    <span class="astra-source-name">Scenario Lab</span>
                    <span class="astra-source-state">AVAILABLE</span>
                </div>
                <div class="astra-source">
                    <span class="astra-source-name">Governance documentation</span>
                    <span class="astra-source-state">AVAILABLE</span>
                </div>
                <div class="astra-source">
                    <span class="astra-source-name">Demand / weather / RAG / agents</span>
                    <span class="astra-source-state astra-source-planned">PLANNED</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with b2:
    review_available = page_available(SCENARIO_LAB_PAGE)
    st.markdown(
        """
        <div class="astra-card astra-card-pad">
            <div class="astra-card-title" style="color:#1768d2;">REVIEW & APPROVAL</div>
            <div class="astra-signal-copy" style="margin-top:.58rem;">
                Review the current model evidence and scenario result before recording
                a human decision. Approval does not execute an operational action.
            </div>
            <div class="astra-tag tag-green">HUMAN-IN-THE-LOOP</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if review_available:
        st.page_link(
            "pages/2_Scenario_Lab.py",
            label="Open Human Review",
            use_container_width=True,
        )


st.caption(
    "ASTRA v0.1 · Research decision-support prototype · "
    "Real DataCo → validated M3 risk → what-if sensitivity → human review"
)
