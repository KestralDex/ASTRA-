from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

FILE_PATH = Path(__file__).resolve()
PROJECT_ROOT = FILE_PATH.parents[2] if len(FILE_PATH.parents) >= 3 else Path.cwd()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.ui_theme import apply_astra_theme, render_astra_sidebar

st.set_page_config(
    page_title="ASTRA | Governance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_astra_theme("Governance & Security")
render_astra_sidebar("governance")

st.title("ASTRA Governance & Compliance")
st.caption(
    "Research prototype governance • Security boundaries • Privacy • Human oversight"
)

st.info(
    "ASTRA v0.1 is a research decision-support prototype. This page documents "
    "implemented controls, planned controls, non-applicable commercial requirements, "
    "and items that must be verified before any public or production deployment."
)

st.warning(
    "This page is a project governance record, not a legal certification or claim "
    "of regulatory compliance."
)

status_rows = [
    ("Privacy notice", "IMPLEMENTED", "Research-prototype privacy notice drafted."),
    ("Terms of use", "IMPLEMENTED", "Prototype terms drafted; not legal advice."),
    ("Refund policy", "N/A", "ASTRA has no payments or commercial billing."),
    ("Cookie policy", "N/A / RECHECK IF DEPLOYED", "No custom advertising/analytics cookies are used by ASTRA v0.1."),
    ("Cookie consent", "N/A / RECHECK IF DEPLOYED", "Reassess if public deployment adds analytics or tracking."),
    ("Form consent", "PARTIAL", "Current prototype avoids unnecessary personal-data collection; explicit consent is required before future persistent uploads/feedback."),
    ("Data minimization", "IMPLEMENTED", "Dashboard preview excludes unnecessary personal/customer fields."),
    ("Third-party dependency review", "PENDING", "Perform dependency/license/security audit before public deployment."),
    ("Dark patterns", "IMPLEMENTED BY DESIGN", "No forced choices, disguised consent, or deceptive controls."),
    ("Hidden fees", "N/A", "No payments."),
    ("Fake reviews", "N/A", "No review/testimonial system."),
    ("Unsupported claims", "IMPLEMENTED BY DESIGN", "ASTRA is labelled as research decision support; no autonomous-execution or causal guarantees."),
    ("Accessibility / alt text", "PARTIAL", "Final UI accessibility pass remains pending."),
    ("Color contrast", "PENDING FINAL UI", "Verify during final presentation UI pass."),
    ("Keyboard navigation", "PENDING FINAL UI", "Verify Streamlit controls during final accessibility test."),
    ("Project details", "IMPLEMENTED", "Project purpose and prototype boundaries are stated."),
    ("Children's data consent", "N/A CURRENTLY", "ASTRA does not intentionally collect children's personal data."),
    ("Email unsubscribe", "N/A", "No marketing email system."),
    ("Font/image licensing", "PARTIAL", "Use only project-owned/open/licensed assets; verify any future custom media."),
    ("Deletion request process", "PLANNED IF PERSISTENCE ADDED", "Current prototype does not persist user-uploaded personal datasets through the dashboard."),
]

st.subheader("Governance Status")

header = st.columns([2.2, 1.5, 5])
header[0].markdown("**Requirement**")
header[1].markdown("**Status**")
header[2].markdown("**ASTRA v0.1 position**")

for requirement, status, note in status_rows:
    cols = st.columns([2.2, 1.5, 5])
    cols[0].write(requirement)
    cols[1].write(status)
    cols[2].write(note)

st.divider()
st.subheader("Security Controls")

security_rows = [
    ("Secrets", "Environment variables; do not store API keys in source or dashboard output."),
    ("Model loading", "Only fixed project-local M3 model/metadata paths are accepted."),
    ("Prediction leakage", "Post-outcome fields are excluded from M3 inference and Scenario Lab."),
    ("Data minimization", "Normal dashboard preview avoids raw customer-identifying fields."),
    ("Error handling", "User-facing UI avoids displaying internal traceback/path details."),
    ("Scenario execution", "Scenario Lab changes model inputs only; it performs no external operational action."),
    ("Human-in-the-loop", "Scenario results require explicit human review."),
    ("Auditability", "Model version, baseline/scenario probabilities and review decision are surfaced; persistent audit storage remains future work."),
    ("Authentication/RBAC", "Planned for any multi-user or production deployment; not claimed as implemented in v0.1."),
    ("External APIs", "Not part of the current October 1 core demo; future connectors require scoped credentials, validation and logging."),
]

for control, detail in security_rows:
    st.markdown(f"**{control}** — {detail}")

st.divider()
st.subheader("Model & Research Boundaries")

st.markdown(
    """
- M3 produces a **historical model-based late-delivery probability**, not a guarantee.
- Scenario Lab reports **model sensitivity**, not causal treatment effects.
- DataCo rows represent **order-item records**, not unique orders.
- ASTRA v0.1 does **not** autonomously purchase, route, contact suppliers, modify inventory, or execute transactions.
- Demand forecasting, external disruption intelligence, RAG and multi-agent reasoning remain future/planned modules unless separately implemented and verified.
- Dataset provenance/licensing must be verified before public redistribution of raw data.
"""
)

st.divider()
st.subheader("Human Review Boundary")

st.success(
    "October 1 demo boundary: DETECT → ANALYZE → SIMULATE → HUMAN REVIEW. "
    "No autonomous execution."
)

st.caption(
    "ASTRA v0.1 • Governance record for academic/research demonstration"
)
