from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_FEATURES = [
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

FORBIDDEN_PREDICTION_FIELDS = {
    "Late_delivery_risk",
    "Delivery Status",
    "Days for shipping (real)",
    "shipping date (DateOrders)",
}


def test_demo_pages_exist_and_compile():
    page_paths = [
        ROOT / "dashboard" / "app.py",
        ROOT / "dashboard" / "pages" / "1_Data_Explorer.py",
        ROOT / "dashboard" / "pages" / "2_Scenario_Lab.py",
        ROOT / "dashboard" / "pages" / "3_Governance.py",
    ]

    for path in page_paths:
        assert path.is_file(), f"Missing demo page: {path}"
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


def test_m3_artifacts_exist():
    assert (ROOT / "models" / "risk_random_forest_v1.joblib").is_file()
    assert (ROOT / "models" / "risk_random_forest_v1.json").is_file()


def test_m3_metadata_matches_dashboard_contract():
    metadata = json.loads(
        (ROOT / "models" / "risk_random_forest_v1.json").read_text(
            encoding="utf-8"
        )
    )

    features = (
        list(metadata.get("features_categorical", []))
        + list(metadata.get("features_numeric", []))
    )

    assert metadata.get("model_version") == "v1.0-milestone3"
    assert features == EXPECTED_FEATURES
    assert not (set(features) & FORBIDDEN_PREDICTION_FIELDS)


def test_risk_module_contract_matches_dashboard_contract():
    from src.risk.train import ALL_FEATURES, FORBIDDEN_FEATURES

    assert list(ALL_FEATURES) == EXPECTED_FEATURES
    assert not (set(ALL_FEATURES) & FORBIDDEN_PREDICTION_FIELDS)
    assert FORBIDDEN_PREDICTION_FIELDS.issubset(set(FORBIDDEN_FEATURES))


def test_scenario_lab_keeps_human_review_and_no_execution_boundary():
    source = (
        ROOT / "dashboard" / "pages" / "2_Scenario_Lab.py"
    ).read_text(encoding="utf-8")

    assert "Human Review" in source
    assert '"execution_performed": False' in source
    assert "predict_risk(" in source
    assert "causal" in source.lower()


def test_command_center_exposes_october_demo_flow():
    source = (ROOT / "dashboard" / "app.py").read_text(encoding="utf-8")

    assert "October 1 Demo Flow" in source
    assert "Open Data Explorer" in source
    assert "Open Scenario Lab" in source
    assert "pages/3_Governance.py" in source


def test_governance_documents_exist():
    expected = [
        "privacy_notice.md",
        "prototype_terms.md",
        "data_model_governance.md",
        "accessibility_checklist.md",
        "third_party_licensing_review.md",
    ]

    for name in expected:
        assert (ROOT / "docs" / name).is_file(), f"Missing governance doc: {name}"
