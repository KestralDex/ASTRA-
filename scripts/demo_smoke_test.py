from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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

REQUIRED_DATA_COLUMNS = set(EXPECTED_FEATURES) | {
    "Order Id",
    "Order Item Id",
    "order date (DateOrders)",
    "Late_delivery_risk",
}

MODEL_PATH = ROOT / "models" / "risk_random_forest_v1.joblib"
METADATA_PATH = ROOT / "models" / "risk_random_forest_v1.json"

failures: list[str] = []
warnings: list[str] = []


def pass_check(name: str, detail: str = "") -> None:
    suffix = f" — {detail}" if detail else ""
    print(f"[PASS] {name}{suffix}")


def fail_check(name: str, detail: str) -> None:
    failures.append(f"{name}: {detail}")
    print(f"[FAIL] {name} — {detail}")


def warn_check(name: str, detail: str) -> None:
    warnings.append(f"{name}: {detail}")
    print(f"[WARN] {name} — {detail}")


def find_dataco() -> Path | None:
    candidates: list[Path] = []

    env_value = os.getenv("ASTRA_DATACO_PATH", "").strip()
    if env_value:
        candidates.append(Path(env_value).expanduser())

    candidates.extend(
        [
            ROOT.parent / "archive" / "DataCoSupplyChainDataset.csv",
            ROOT / "data" / "raw" / "DataCoSupplyChainDataset.csv",
        ]
    )

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue
        if resolved.is_file():
            return resolved

    return None


print("=" * 72)
print("ASTRA OCTOBER 1 DEMO SMOKE TEST")
print("=" * 72)

if sys.version_info[:2] == (3, 12):
    pass_check("Python version", sys.version.split()[0])
else:
    warn_check(
        "Python version",
        f"found {sys.version.split()[0]}; project demo environment was validated on Python 3.12",
    )

try:
    import sklearn

    if sklearn.__version__ == "1.5.2":
        pass_check("scikit-learn version", sklearn.__version__)
    else:
        fail_check(
            "scikit-learn version",
            f"found {sklearn.__version__}; M3 artifact was trained with 1.5.2",
        )
except Exception as exc:
    fail_check("scikit-learn import", str(exc))

try:
    import streamlit

    pass_check("Streamlit import", getattr(streamlit, "__version__", "version unknown"))
except Exception as exc:
    fail_check("Streamlit import", str(exc))

pages = [
    ROOT / "dashboard" / "app.py",
    ROOT / "dashboard" / "pages" / "1_Data_Explorer.py",
    ROOT / "dashboard" / "pages" / "2_Scenario_Lab.py",
    ROOT / "dashboard" / "pages" / "3_Governance.py",
]

for page in pages:
    if not page.is_file():
        fail_check("Demo page", f"missing {page.relative_to(ROOT)}")
        continue

    try:
        compile(page.read_text(encoding="utf-8"), str(page), "exec")
        pass_check("Page syntax", str(page.relative_to(ROOT)))
    except Exception as exc:
        fail_check("Page syntax", f"{page.relative_to(ROOT)}: {exc}")

try:
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    metadata_features = (
        list(metadata.get("features_categorical", []))
        + list(metadata.get("features_numeric", []))
    )

    if metadata_features == EXPECTED_FEATURES:
        pass_check("M3 metadata feature contract", "9 expected features")
    else:
        fail_check(
            "M3 metadata feature contract",
            f"expected {EXPECTED_FEATURES}, got {metadata_features}",
        )

    model_version = str(metadata.get("model_version", "")).strip()
    if model_version:
        pass_check("Model metadata version", model_version)
    else:
        fail_check("Model metadata version", "missing model_version")
except Exception as exc:
    metadata = {}
    fail_check("M3 metadata", str(exc))

dataset_path = find_dataco()

if dataset_path is None:
    fail_check(
        "DataCo dataset",
        "not found. Expected ASTRA_DATACO_PATH, ../archive/DataCoSupplyChainDataset.csv, or data/raw/DataCoSupplyChainDataset.csv",
    )
else:
    pass_check("DataCo dataset", str(dataset_path))

    try:
        import pandas as pd

        sample = pd.read_csv(
            dataset_path,
            encoding="latin-1",
            nrows=5,
            low_memory=False,
        )

        missing_columns = sorted(REQUIRED_DATA_COLUMNS - set(sample.columns))

        if missing_columns:
            fail_check(
                "DataCo schema",
                "missing columns: " + ", ".join(missing_columns),
            )
        else:
            pass_check("DataCo schema", "required demo columns present")
    except Exception as exc:
        fail_check("DataCo sample read", str(exc))

if MODEL_PATH.is_file():
    pass_check("M3 model artifact", str(MODEL_PATH.relative_to(ROOT)))
else:
    fail_check("M3 model artifact", "risk_random_forest_v1.joblib missing")

try:
    from src.risk.train import ALL_FEATURES, load_model_artifact, predict_risk

    if list(ALL_FEATURES) == EXPECTED_FEATURES:
        pass_check("Risk module feature contract", "matches dashboard")
    else:
        fail_check(
            "Risk module feature contract",
            f"got {list(ALL_FEATURES)}",
        )

    pipeline = load_model_artifact(MODEL_PATH)

    baseline = {
        "Shipping Mode": "Standard Class",
        "Type": "DEBIT",
        "Market": "Europe",
        "Customer Segment": "Consumer",
        "Category Name": "Sporting Goods",
        "Department Name": "Fitness",
        "Order Item Quantity": 1,
        "Order Item Product Price": 100.0,
        "Order Item Discount Rate": 0.10,
    }

    baseline_result = predict_risk(
        pipeline,
        baseline,
        model_version=str(metadata.get("model_version", "unknown")),
    )

    baseline_probability = float(baseline_result.late_delivery_probability)

    if 0.0 <= baseline_probability <= 1.0 and int(baseline_result.predicted_class) in (0, 1):
        pass_check(
            "Live M3 baseline prediction",
            f"{baseline_probability * 100:.1f}% / class {baseline_result.predicted_class}",
        )
    else:
        fail_check(
            "Live M3 baseline prediction",
            f"invalid output {baseline_result}",
        )

    scenario = baseline.copy()
    scenario["Shipping Mode"] = "First Class"

    scenario_result = predict_risk(
        pipeline,
        scenario,
        model_version=str(metadata.get("model_version", "unknown")),
    )

    scenario_probability = float(scenario_result.late_delivery_probability)

    if 0.0 <= scenario_probability <= 1.0:
        pass_check(
            "Scenario rerun",
            f"{scenario_probability * 100:.1f}% after Shipping Mode change",
        )
    else:
        fail_check(
            "Scenario rerun",
            f"invalid probability {scenario_probability}",
        )

    delta_pp = (scenario_probability - baseline_probability) * 100

    if abs(delta_pp) < 0.0001:
        warn_check(
            "Scenario sensitivity",
            "this sample produced no displayed probability change; this is not automatically a defect",
        )
    else:
        pass_check(
            "Scenario sensitivity",
            f"{delta_pp:+.1f} percentage points",
        )

except Exception as exc:
    fail_check(
        "Live M3 runtime",
        f"{type(exc).__name__}: {exc}",
    )

required_governance = [
    ROOT / "docs" / "privacy_notice.md",
    ROOT / "docs" / "prototype_terms.md",
    ROOT / "docs" / "data_model_governance.md",
    ROOT / "docs" / "accessibility_checklist.md",
    ROOT / "docs" / "third_party_licensing_review.md",
]

missing_governance = [
    str(path.relative_to(ROOT))
    for path in required_governance
    if not path.is_file()
]

if missing_governance:
    fail_check(
        "Governance documentation",
        "missing: " + ", ".join(missing_governance),
    )
else:
    pass_check("Governance documentation", "5 required documents found")

try:
    scenario_source = (
        ROOT / "dashboard" / "pages" / "2_Scenario_Lab.py"
    ).read_text(encoding="utf-8")

    if '"execution_performed": False' in scenario_source and "Human Review" in scenario_source:
        pass_check("Human-review / no-execution boundary")
    else:
        fail_check(
            "Human-review / no-execution boundary",
            "required markers not found",
        )
except Exception as exc:
    fail_check("Scenario safety source check", str(exc))

print()
print("-" * 72)

if warnings:
    print(f"{len(warnings)} warning(s) recorded.")

if failures:
    print(f"{len(failures)} FAILURE(S). Demo is NOT ready to freeze.")
    for failure in failures:
        print(f"  - {failure}")
    raise SystemExit(1)

print("ALL CRITICAL SMOKE CHECKS PASSED.")
print("Proceed to the manual end-to-end rehearsal checklist.")
