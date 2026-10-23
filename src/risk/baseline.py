"""
Simple, non-ML baselines for the risk module (Milestone 3, Step 5).

WHY THIS FILE EXISTS
---------------------
Before trusting any ML model's metrics, we need to know whether it
actually beats a rule a person could write in five minutes. If Logistic
Regression only matches a majority-class guess, that's important to
know honestly, not something to gloss over.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.utils.exceptions import AstraError


class BaselineError(AstraError):
    """Raised for baseline-construction problems."""


@dataclass
class MajorityClassBaseline:
    """Always predicts the majority class seen in training data."""
    majority_class: int

    @classmethod
    def fit(cls, train_target: pd.Series) -> "MajorityClassBaseline":
        counts = train_target.value_counts()
        return cls(majority_class=int(counts.idxmax()))

    def predict(self, n: int) -> np.ndarray:
        return np.full(n, self.majority_class)

    def predict_proba_positive(self, n: int) -> np.ndarray:
        """A constant 'probability' equal to the training positive rate
        would be the more honest baseline probability, but since this
        baseline only ever emits one class, we return that class as a
        hard 0/1 'probability' — ROC-AUC is not meaningful for this
        baseline and is reported as N/A rather than computed."""
        return np.full(n, float(self.majority_class))


@dataclass
class ShippingModeRuleBaseline:
    """
    Predicts late (1) if the shipping mode's OWN training late-rate is
    >= 0.5, else not late (0) — a simple, auditable rule a person could
    actually write by hand from Milestone 2's findings, not a hidden model.
    """
    mode_to_prediction: dict

    @classmethod
    def fit(cls, train_df: pd.DataFrame, mode_col: str, target_col: str) -> "ShippingModeRuleBaseline":
        rates = train_df.groupby(mode_col)[target_col].mean()
        mode_to_prediction = {mode: int(rate >= 0.5) for mode, rate in rates.items()}
        return cls(mode_to_prediction=mode_to_prediction)

    def predict(self, modes: pd.Series) -> np.ndarray:
        # Unseen mode at prediction time -> conservative default of 0
        # (not late), logged implicitly via the .get() fallback rather
        # than raising, since this is a simple rule, not a strict schema.
        return modes.map(lambda m: self.mode_to_prediction.get(m, 0)).to_numpy()
