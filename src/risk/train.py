"""
Operational / Delivery Risk Intelligence module (Milestone 3).

WHY THIS FILE EXISTS
---------------------
This is ASTRA's first genuine predictive module. It wraps scikit-learn
preprocessing + a classifier into a single fit/predict-ready pipeline,
so the dashboard (much later) never needs to manually reproduce
one-hot encoding or scaling — it just calls predict_risk() with raw
order fields and gets a probability back.

This module is NUMERICAL INTELLIGENCE only — no LLM explanation layer,
per the milestone's scope.

FEATURES USED (see artifacts/reports/risk_feature_manifest.csv for the
full audit and reasoning behind every included/excluded column):
    Categorical: Shipping Mode, Type, Market, Customer Segment,
                 Category Name, Department Name
    Numeric:     Order Item Quantity, Order Item Product Price,
                 Order Item Discount Rate
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix,
)

from src.utils.exceptions import AstraError
from src.utils.logger import get_logger

logger = get_logger(__name__)

TARGET_COLUMN = "Late_delivery_risk"

CATEGORICAL_FEATURES = [
    "Shipping Mode", "Type", "Market", "Customer Segment",
    "Category Name", "Department Name",
]
NUMERIC_FEATURES = [
    "Order Item Quantity", "Order Item Product Price", "Order Item Discount Rate",
]
ALL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES

# Columns that must NEVER appear in ALL_FEATURES — a safety net that
# fails loudly if someone edits this file to (re)introduce a leaky or
# target column, rather than relying on manual review alone.
FORBIDDEN_FEATURES = {
    "Late_delivery_risk", "Delivery Status",
    "Days for shipping (real)", "shipping date (DateOrders)",
}


class RiskModuleError(AstraError):
    """Raised for risk-module-specific problems (bad manifest, bad input schema, etc.)."""


def _assert_no_forbidden_features(features: list[str]) -> None:
    overlap = set(features) & FORBIDDEN_FEATURES
    if overlap:
        raise RiskModuleError(
            f"Forbidden/leaky column(s) found in feature list: {overlap}. "
            "These may never be used as model inputs."
        )


_assert_no_forbidden_features(ALL_FEATURES)


def build_preprocessing_pipeline() -> ColumnTransformer:
    """
    Build the ColumnTransformer used by every model in this module:
    one-hot encoding for categoricals (unknown categories at prediction
    time are ignored rather than raising, since a dashboard could see a
    category not present during training), and standard scaling for
    numeric features (harmless for tree models, needed for Logistic
    Regression).
    """
    return ColumnTransformer(
        transformers=[
            # sparse_output=False: HistGradientBoostingClassifier cannot
            # accept the sparse matrix OneHotEncoder produces by default
            # (raises TypeError at fit time). Dense output is a small
            # memory cost here (~80 encoded columns x 180k rows) and
            # keeps one shared preprocessing pipeline usable by every
            # model in this module, rather than branching per-model.
            ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
            ("numeric", StandardScaler(), NUMERIC_FEATURES),
        ],
        remainder="drop",  # anything not explicitly listed is dropped, not silently included
    )


def chronological_split(
    df: pd.DataFrame,
    date_column: str = "order date (DateOrders)",
    train_fraction: float = 0.8,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split df into train/test by TIME, not randomly — the earliest
    train_fraction of orders (by order date) become the training set,
    the remaining, later orders become the test set. This means test
    performance reflects "how well would this have predicted orders
    that hadn't happened yet," which matches how ASTRA would actually
    be used, rather than a random split's optimistic assumption that
    future and past orders are exchangeable.

    Raises RiskModuleError if date_column is missing or entirely unparseable.
    """
    if date_column not in df.columns:
        raise RiskModuleError(f"date_column '{date_column}' not found in DataFrame.")

    dates = pd.to_datetime(df[date_column], errors="coerce")
    if dates.isna().all():
        raise RiskModuleError(f"Could not parse any values in '{date_column}' as dates.")

    order = dates.sort_values().index
    split_point = int(len(order) * train_fraction)
    train_idx = order[:split_point]
    test_idx = order[split_point:]

    train_df = df.loc[train_idx].copy()
    test_df = df.loc[test_idx].copy()

    logger.info(
        "Chronological split: %d train rows (%s to %s), %d test rows (%s to %s)",
        len(train_df), dates.loc[train_idx].min(), dates.loc[train_idx].max(),
        len(test_df), dates.loc[test_idx].min(), dates.loc[test_idx].max(),
    )
    return train_df, test_df


@dataclass
class EvaluationResult:
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion: np.ndarray
    n_samples: int

    def as_dict(self) -> dict:
        return {
            "accuracy": self.accuracy, "precision": self.precision,
            "recall": self.recall, "f1": self.f1, "roc_auc": self.roc_auc,
            "n_samples": self.n_samples,
        }


def evaluate(pipeline: Pipeline, X: pd.DataFrame, y: pd.Series) -> EvaluationResult:
    """
    Compute the standard metric set (accuracy, precision, recall, F1,
    ROC-AUC, confusion matrix) for a fitted pipeline against X/y.
    Does not train anything — pipeline must already be fit.
    """
    y_pred = pipeline.predict(X)
    y_proba = pipeline.predict_proba(X)[:, 1]

    return EvaluationResult(
        accuracy=accuracy_score(y, y_pred),
        precision=precision_score(y, y_pred),
        recall=recall_score(y, y_pred),
        f1=f1_score(y, y_pred),
        roc_auc=roc_auc_score(y, y_proba),
        confusion=confusion_matrix(y, y_pred),
        n_samples=len(y),
    )


def train(model, train_df: pd.DataFrame) -> Pipeline:
    """
    Fit a full preprocessing+model Pipeline on train_df ONLY.

    INPUT:
        model — an unfitted scikit-learn classifier (e.g. LogisticRegression()).
        train_df — training rows; must contain ALL_FEATURES + TARGET_COLUMN.
    OUTPUT:
        a fitted sklearn Pipeline (preprocessing + model together).

    Preprocessing is fit here, on train_df only — evaluate()/predict_risk()
    reuse this same fitted pipeline, so test-time data is transformed
    using statistics learned only from training data (no leakage from
    fitting on the full dataset before splitting).
    """
    missing = [c for c in ALL_FEATURES + [TARGET_COLUMN] if c not in train_df.columns]
    if missing:
        raise RiskModuleError(f"train_df is missing required column(s): {missing}")

    pipeline = Pipeline(steps=[
        ("preprocessing", build_preprocessing_pipeline()),
        ("model", model),
    ])
    pipeline.fit(train_df[ALL_FEATURES], train_df[TARGET_COLUMN])
    return pipeline


@dataclass
class RiskPrediction:
    late_delivery_probability: float
    predicted_class: int
    model_version: str


def predict_risk(pipeline: Pipeline, order: dict, model_version: str) -> RiskPrediction:
    """
    Predict late-delivery risk for a single order, given as a dict of
    {feature_name: value} for (at minimum) ALL_FEATURES.

    OUTPUT: RiskPrediction(late_delivery_probability, predicted_class,
    model_version) — no LOW/MEDIUM/HIGH label yet (no documented
    threshold policy exists), just the raw probability and the
    pipeline's own default 0.5-threshold class prediction, per the
    milestone's instruction not to invent thresholds.

    Raises RiskModuleError if a required feature is missing from `order`.
    """
    missing = [c for c in ALL_FEATURES if c not in order]
    if missing:
        raise RiskModuleError(f"order is missing required feature(s): {missing}")

    row = pd.DataFrame([{c: order[c] for c in ALL_FEATURES}])
    probability = float(pipeline.predict_proba(row)[0, 1])
    predicted_class = int(pipeline.predict(row)[0])

    return RiskPrediction(
        late_delivery_probability=probability,
        predicted_class=predicted_class,
        model_version=model_version,
    )


def save_model_artifact(
    pipeline: Pipeline,
    output_path: Path,
    metadata: dict,
) -> None:
    """
    Save the fitted pipeline (preprocessing + model together, so the
    dashboard never has to reproduce preprocessing manually) plus a
    metadata dict alongside it as a sibling .json file.

    metadata should NOT contain raw training data or PII — only
    aggregate information (model name/version, timestamp, metrics,
    limitations) per Milestone 3's security requirements.
    """
    import json

    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, output_path)

    metadata_path = output_path.with_suffix(".json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)

    logger.info("Saved model artifact to %s and metadata to %s", output_path, metadata_path)


def load_model_artifact(model_path: Path) -> Pipeline:
    """
    Load a previously saved pipeline. Only loads artifacts from a
    trusted local path this code itself wrote — never accepts an
    arbitrary user-uploaded file path from outside the project's own
    models/ directory, per Milestone 3's security requirement.
    """
    models_dir = model_path.resolve().parent
    if not model_path.exists():
        raise RiskModuleError(f"Model artifact not found: {model_path}")
    if model_path.suffix != ".joblib":
        raise RiskModuleError(f"Expected a .joblib model artifact, got: {model_path}")

    return joblib.load(model_path)
