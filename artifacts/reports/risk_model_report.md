# ASTRA Risk Model Report (Milestone 3)

## Research question
Using information legitimately available at order/shipping-planning time,
how well can ASTRA estimate the probability that an order will
eventually experience late delivery?

**Target:** `Late_delivery_risk`. **Prediction moment:** order/shipping-
planning time. Full audit: `artifacts/reports/risk_feature_manifest.csv`,
`docs/prediction_contract.md`.

## Split strategy

MEASURED RESULT: Chronological split — earliest 80% of orders by
`order date (DateOrders)` (2015-01-01 to ~2017-08-06) as training
(144,415 rows), most recent 20% (~2017-08-06 to 2018-01-31) as test
(36,104 rows).

INTERPRETATION: A random split would let future orders leak into
training relative to test orders — an unrealistic advantage ASTRA would
never have operationally, since it must predict orders that haven't
happened yet using only historical data. Chronological split matches
real deployment conditions.

LIMITATION: The chronological test period is only ~6 months, all
within the same historical dataset — this is not equivalent to
validating against genuinely new, out-of-distribution future data.

## Final feature set

**Categorical (OneHotEncoder):** `Shipping Mode`, `Type`, `Market`,
`Customer Segment`, `Category Name`, `Department Name`
**Numeric (StandardScaler):** `Order Item Quantity`, `Order Item
Product Price`, `Order Item Discount Rate`

**Shipping variable decision:** `Shipping Mode` was chosen over `Days
for shipment (scheduled)` (perfectly collinear per Milestone 2) as the
more interpretable, business-facing representation. `Order Region` was
excluded as a hierarchical subset of `Market`.

## Baseline results

MEASURED RESULT:

| Baseline | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Majority class (always predict "late") | 0.5466 | 0.5466 | 1.0000 | 0.7068 |
| Shipping-mode rule (predict late if mode's own training late-rate ≥ 0.5) | 0.6921 | 0.8421 | 0.5373 | 0.6560 |

INTERPRETATION: The majority-class baseline's high F1 is an artifact of
always predicting the positive class on a majority-positive test set —
not a sign of a useful model. The shipping-mode rule, despite being a
one-line rule a person could write by hand, already reaches
meaningfully higher accuracy and precision.

## Logistic Regression

MEASURED RESULT (test set, n=36,104): accuracy 0.6921, precision
0.8421, recall 0.5373, F1 0.6560, ROC-AUC 0.7382.
Train-set metrics (n=144,415): accuracy 0.6961, F1 0.6616, ROC-AUC
0.7416 — close to test metrics, no large train/test gap.

## Decision Tree (max_depth=6)

MEASURED RESULT (test): accuracy 0.6911, precision 0.8327, recall
0.5441, F1 0.6582, ROC-AUC 0.7406.
Train: accuracy 0.6970, F1 0.6672, ROC-AUC 0.7462.
INTERPRETATION: Train and test performance are close — this depth-6
tree does not show obvious overfitting.

## Random Forest (n_estimators=200, max_depth=10)

MEASURED RESULT (test): accuracy 0.6919, precision 0.8326, recall
0.5460, F1 0.6595, ROC-AUC **0.7412** (best of the four ML models).
Train: accuracy 0.7016, F1 0.6731, ROC-AUC 0.7677 — a modestly larger
train/test gap than the single tree, consistent with an ensemble
fitting training data somewhat more closely, but not dramatic.

## HistGradientBoostingClassifier (optional, max_depth=6)

MEASURED RESULT (test): accuracy 0.6916, precision 0.8355, recall
0.5426, F1 0.6579, ROC-AUC 0.7410.

## Model comparison

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Baseline: Majority Class | 0.5466 | 0.5466 | 1.0000 | 0.7068 | N/A |
| Baseline: Shipping-Mode Rule | 0.6921 | 0.8421 | 0.5373 | 0.6560 | N/A |
| Logistic Regression | 0.6921 | 0.8421 | 0.5373 | 0.6560 | 0.7382 |
| Decision Tree | 0.6911 | 0.8327 | 0.5441 | 0.6582 | 0.7406 |
| **Random Forest** | 0.6919 | 0.8326 | 0.5460 | 0.6595 | **0.7412** |
| HistGradientBoosting | 0.6916 | 0.8355 | 0.5426 | 0.6579 | 0.7410 |

See `fig09_model_comparison.png`, `fig11_roc_curves.png`.

INTERPRETATION: All four ML models perform almost identically — within
about 0.003 F1 and 0.003 ROC-AUC of each other. **Not declared a winner
on accuracy alone** — Random Forest is selected as the candidate model
for its marginally best ROC-AUC and F1, and because it also produced
usable feature importances, not because it dominates the comparison.

FALSE NEGATIVE (ASTRA predicts safe, shipment becomes late) and FALSE
POSITIVE (ASTRA predicts risk, shipment would have been on time) both
occur at meaningful rates given recall ≈ 0.55 and precision ≈ 0.83 — no
business cost is assumed for either direction, since no such cost was
supplied this milestone.

## Critical DataCo limitation test: Shipping-only vs Full-feature model

MEASURED RESULT (Random Forest, same settings, test set):

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Model A: Shipping-plan only (`Shipping Mode`) | 0.6921 | 0.8421 | 0.5373 | 0.6560 | 0.7273 |
| Model B: Full legitimate features | 0.6919 | 0.8326 | 0.5460 | 0.6595 | 0.7412 |

See `fig13_shipping_only_vs_full.png`.

INTERPRETATION (reported honestly, not hidden): the full feature set's
advantage over `Shipping Mode` alone is small — about 0.014 ROC-AUC,
0.0035 F1. **The other legitimate DataCo features (Type, Market,
Customer Segment, category/department, order value) provide only
modest incremental predictive value beyond `Shipping Mode` in this
dataset.** This matches Milestone 2's finding that most non-shipping
categorical/numeric variables showed flat or negligible relationships
with the target.

## Temporal generalization

MEASURED RESULT: splitting the chronological test set (36,104 rows) in
half by date — earlier half (2017-04-22 to 2017-08-06, n=18,052):
ROC-AUC 0.7374, F1 0.6543; later half (2017-08-06 to 2018-01-31,
n=18,052): ROC-AUC 0.7445, F1 0.6646.

INTERPRETATION: performance is similar (not degrading) across the two
halves of the test period — no evidence of the model becoming
noticeably stale within this ~10-month test window.

LIMITATION: this is not a claim of production generalization — DataCo
covers historical 2015–2018 data only, and no data exists in this
project beyond January 2018 to test genuine future generalization.

## Confusion matrix (Random Forest, test set)

See `fig10_confusion_matrix_random_forest.png`. Recall of 0.546 means
roughly 45% of genuinely late orders are missed (predicted not-late);
precision of 0.833 means about 17% of orders flagged as at-risk turn
out to have been on time.

## Explainability

MEASURED RESULT — Logistic Regression coefficients most positive
(toward LATE): `Shipping Mode_First Class` (+2.28), `Shipping
Mode_Second Class` (+0.41), `Type_PAYMENT` (+0.22). Most negative
(toward NOT LATE): `Shipping Mode_Standard Class` (−1.28), `Shipping
Mode_Same Day` (−1.02), `Type_TRANSFER` (−0.23).

Random Forest feature importances, top 4: `Shipping Mode_Standard
Class` (0.439), `Shipping Mode_First Class` (0.302), `Shipping
Mode_Second Class` (0.138), `Shipping Mode_Same Day` (0.040) — together
accounting for over 90% of total importance. See
`fig12_rf_feature_importance.png`.

INTERPRETATION: both models rely overwhelmingly on `Shipping Mode`.
This is a description of which encoded categories the models weight
most, **not** a claim that shipping mode causes lateness — as Milestone
2 established, faster/shorter promised windows mechanically leave less
slack before a shipment is labeled "late."

## Saved model artifact

`models/risk_random_forest_v1.joblib` (fitted preprocessing + Random
Forest pipeline together) with sibling metadata
`models/risk_random_forest_v1.json` containing model name/version,
training timestamp, dataset, target, prediction moment, feature
manifest reference, test-set metrics, and known limitations. No raw
training data or PII is included in the metadata file.

## Security controls applied

- `load_model_artifact()` only accepts a `.joblib` file at an explicit,
  trusted local path — no arbitrary user-uploaded serialized model
  files are accepted.
- No customer records or PII are logged; `src/data/loaders.py`'s
  existing logging-metadata-only practice continues.
- No direct PII (`Customer Fname/Lname/Email/Password/Street/etc.`) is
  in the training feature set — enforced both by the manifest and by
  the module-level `FORBIDDEN_FEATURES` check that runs at import time.
- Model metadata contains aggregate metrics/limitations only, never raw
  rows.

## Errors/fixes this milestone

1. **`HistGradientBoostingClassifier` rejected sparse `OneHotEncoder` output** — fixed by setting `sparse_output=False` in the shared preprocessing pipeline. Logged in `docs/error_log.md`.
2. **Temporal-generalization analysis initially sorted by the raw date string, not a parsed datetime** — produced a nonsensical "earlier half" date range. Fixed by parsing with `pd.to_datetime()` before sorting. Logged in `docs/error_log.md`. (Note: `chronological_split()` itself was never affected — it parsed dates correctly from the start; only this separate analysis step had the bug.)

## Limitations

- DataCo covers 2015–2018 only; no production/current-day generalization claimed.
- All four ML models perform nearly identically — this dataset may
  genuinely not support much beyond what `Shipping Mode` provides.
- `Order Status`, `Benefit per order`, `Order Item Profit Ratio`
  excluded for unconfirmed operational timing, not confirmed leakage —
  a real clarification could change this in a future milestone.
- No LOW/MEDIUM/HIGH risk tiers defined — only a raw probability and
  the model's default 0.5-threshold class, per instruction not to
  invent a threshold policy.
- No business cost assigned to false positives vs. false negatives.
