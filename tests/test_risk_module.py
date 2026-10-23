"""
Tests for the risk module. All data is small and synthetic — the real
DataCo file is never loaded in tests.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.risk.train import (
    ALL_FEATURES, TARGET_COLUMN, FORBIDDEN_FEATURES,
    build_preprocessing_pipeline, chronological_split, train, evaluate,
    predict_risk, save_model_artifact, load_model_artifact,
    RiskModuleError, _assert_no_forbidden_features,
)
from src.risk.baseline import MajorityClassBaseline, ShippingModeRuleBaseline


def _synthetic_orders(n=200, seed=0) -> pd.DataFrame:
    rng = np.random.RandomState(seed)
    modes = rng.choice(["Standard Class", "First Class", "Second Class", "Same Day"], size=n)
    # Late rate deliberately varies by mode, mirroring the real pattern,
    # so a trained model has something real to learn from.
    late_prob = pd.Series(modes).map({
        "Standard Class": 0.2, "Same Day": 0.4, "Second Class": 0.7, "First Class": 0.9,
    }).to_numpy()
    target = (rng.rand(n) < late_prob).astype(int)

    dates = pd.date_range("2016-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "Shipping Mode": modes,
        "Type": rng.choice(["DEBIT", "TRANSFER", "PAYMENT", "CASH"], size=n),
        "Market": rng.choice(["LATAM", "Europe", "USCA"], size=n),
        "Customer Segment": rng.choice(["Consumer", "Corporate", "Home Office"], size=n),
        "Category Name": rng.choice(["Cleats", "Shoes", "Fitness"], size=n),
        "Department Name": rng.choice(["Footwear", "Fitness"], size=n),
        "Order Item Quantity": rng.randint(1, 5, size=n),
        "Order Item Product Price": rng.uniform(10, 200, size=n),
        "Order Item Discount Rate": rng.uniform(0, 0.3, size=n),
        "order date (DateOrders)": dates,
        "Late_delivery_risk": target,
    })


def test_forbidden_features_are_never_in_all_features():
    """The module-level safety net: ALL_FEATURES never contains a
    forbidden/leaky column."""
    assert set(ALL_FEATURES).isdisjoint(FORBIDDEN_FEATURES)


def test_assert_no_forbidden_features_raises_when_violated():
    with pytest.raises(RiskModuleError):
        _assert_no_forbidden_features(["Shipping Mode", "Late_delivery_risk"])


def test_chronological_split_orders_by_date_not_randomly():
    df = _synthetic_orders(n=100)
    train_df, test_df = chronological_split(df, train_fraction=0.8)
    assert len(train_df) == 80
    assert len(test_df) == 20
    # every train date must be <= every test date
    assert train_df["order date (DateOrders)"].max() <= test_df["order date (DateOrders)"].min()


def test_chronological_split_missing_date_column_raises():
    df = _synthetic_orders(n=10).drop(columns=["order date (DateOrders)"])
    with pytest.raises(RiskModuleError):
        chronological_split(df)


def test_train_missing_required_column_raises():
    df = _synthetic_orders(n=50).drop(columns=["Shipping Mode"])
    with pytest.raises(RiskModuleError, match="Shipping Mode"):
        train(LogisticRegression(), df)


def test_train_and_evaluate_end_to_end():
    df = _synthetic_orders(n=300, seed=1)
    train_df, test_df = chronological_split(df, train_fraction=0.7)
    pipeline = train(LogisticRegression(max_iter=1000), train_df)
    result = evaluate(pipeline, test_df[ALL_FEATURES], test_df[TARGET_COLUMN])

    assert 0.0 <= result.accuracy <= 1.0
    assert 0.0 <= result.precision <= 1.0
    assert 0.0 <= result.recall <= 1.0
    assert 0.0 <= result.f1 <= 1.0
    assert 0.0 <= result.roc_auc <= 1.0
    assert result.confusion.shape == (2, 2)
    assert result.n_samples == len(test_df)


def test_pipeline_handles_unknown_categorical_value_at_prediction_time():
    """A category never seen during training (e.g. a new Market) must
    not crash prediction — OneHotEncoder(handle_unknown='ignore') should
    silently zero out that feature instead."""
    df = _synthetic_orders(n=200, seed=2)
    train_df, _ = chronological_split(df, train_fraction=1.0)  # all as train
    pipeline = train(LogisticRegression(max_iter=1000), train_df)

    order = {
        "Shipping Mode": "Teleportation",  # never seen in training
        "Type": "DEBIT",
        "Market": "LATAM",
        "Customer Segment": "Consumer",
        "Category Name": "Cleats",
        "Department Name": "Footwear",
        "Order Item Quantity": 2,
        "Order Item Product Price": 50.0,
        "Order Item Discount Rate": 0.1,
    }
    result = predict_risk(pipeline, order, model_version="test-v0")
    assert 0.0 <= result.late_delivery_probability <= 1.0
    assert result.predicted_class in (0, 1)


def test_predict_risk_missing_feature_raises():
    df = _synthetic_orders(n=100, seed=3)
    pipeline = train(LogisticRegression(max_iter=1000), df)
    incomplete_order = {"Shipping Mode": "First Class"}  # missing most required fields
    with pytest.raises(RiskModuleError):
        predict_risk(pipeline, incomplete_order, model_version="test-v0")


def test_predict_risk_output_schema():
    df = _synthetic_orders(n=100, seed=4)
    pipeline = train(LogisticRegression(max_iter=1000), df)
    order = df.iloc[0][ALL_FEATURES].to_dict()
    result = predict_risk(pipeline, order, model_version="test-v0")

    assert hasattr(result, "late_delivery_probability")
    assert hasattr(result, "predicted_class")
    assert hasattr(result, "model_version")
    assert result.model_version == "test-v0"


def test_save_and_load_model_artifact_roundtrip(tmp_path):
    df = _synthetic_orders(n=150, seed=5)
    pipeline = train(LogisticRegression(max_iter=1000), df)

    model_path = tmp_path / "test_model.joblib"
    save_model_artifact(pipeline, model_path, metadata={"model_name": "test", "version": "v0"})

    assert model_path.exists()
    assert model_path.with_suffix(".json").exists()

    loaded = load_model_artifact(model_path)
    order = df.iloc[0][ALL_FEATURES].to_dict()
    result = predict_risk(loaded, order, model_version="v0")
    assert 0.0 <= result.late_delivery_probability <= 1.0


def test_load_model_artifact_rejects_non_joblib_path(tmp_path):
    fake_path = tmp_path / "not_a_model.txt"
    fake_path.write_text("not a model")
    with pytest.raises(RiskModuleError, match=r"\.joblib"):
        load_model_artifact(fake_path)


def test_load_model_artifact_missing_file_raises(tmp_path):
    with pytest.raises(RiskModuleError, match="not found"):
        load_model_artifact(tmp_path / "does_not_exist.joblib")


def test_majority_class_baseline():
    target = pd.Series([1, 1, 1, 0])
    baseline = MajorityClassBaseline.fit(target)
    assert baseline.majority_class == 1
    assert (baseline.predict(5) == 1).all()


def test_shipping_mode_rule_baseline():
    df = pd.DataFrame({
        "Shipping Mode": ["First Class"] * 8 + ["Standard Class"] * 8,
        "Late_delivery_risk": [1] * 7 + [0] + [0] * 7 + [1],
    })
    baseline = ShippingModeRuleBaseline.fit(df, "Shipping Mode", "Late_delivery_risk")
    preds = baseline.predict(pd.Series(["First Class", "Standard Class", "Unseen Mode"]))
    assert list(preds) == [1, 0, 0]  # unseen mode defaults conservatively to 0
