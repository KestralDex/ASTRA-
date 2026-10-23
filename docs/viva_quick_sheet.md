# ASTRA Viva Quick Sheet

## What is ASTRA today?

A research decision-support prototype for supply-chain intelligence. The current
working milestone focuses on real DataCo analysis, delivery-risk prediction,
model-based what-if simulation and human review.

## What data is currently implemented?

DataCo is the current operational reference dataset. It has **180,519
order-item records** representing **65,752 unique orders**.

## What is M3 predicting?

Probability that a DataCo record/order-item representation eventually
experiences late delivery, using information considered legitimate at the
planning/inference point.

## What model is used?

Random Forest, version `v1.0-milestone3`.

Historical chronological-holdout performance is approximately:
- ROC-AUC: 0.741
- F1: 0.660
- Accuracy: 69.2%

These are historical evaluation metrics, not production guarantees.

## Why is Shipping Mode so influential?

During feature analysis, Shipping Mode carried most of the legitimate predictive
signal. Shipping Mode alone reached roughly ROC-AUC 0.727 while the full
legitimate feature set reached roughly 0.741. The other features add only modest
incremental signal.

## Why not include scheduled shipping days as another feature?

In DataCo, `Shipping Mode` and `Days for shipment (scheduled)` were perfectly
collinear. Including both would duplicate the same underlying planning signal.

## How did you prevent leakage?

We defined the operational prediction point first, then excluded information
unavailable at that time, including actual shipping duration, shipping date,
Delivery Status and the late-delivery target.

## Why does the Scenario Lab mainly react to Shipping Mode?

Because the trained model learned much stronger signal from Shipping Mode than
from the other legitimate features. Small numeric changes can also remain within
the same Random Forest decision leaves and therefore produce no visible change.

## Does the scenario prove an intervention will work?

No. It is a model-based sensitivity analysis. A probability difference is not a
causal treatment effect.

## Does ASTRA autonomously execute actions?

No. The October 1 prototype stops at human review. It does not place orders,
change routes, contact suppliers, modify inventory, make payments or execute
other operational actions.

## Why are RAG, agents and M5 not in the October 1 core?

The project vision includes them, but the milestone prioritizes a reliable,
validated vertical slice before expanding scope. Those modules remain planned
unless separately implemented and tested.

## What is the strongest engineering point?

The system is not only a notebook model. It connects data validation, a
leakage-safe prediction contract, trained ML, a Streamlit interface, real record
inspection, what-if reruns, governance and automated tests.

## What testing has passed?

Current confirmed state:
- critical demo smoke test: passed;
- pytest: **57 passed**;
- page syntax, model artifact, feature contract, DataCo schema, live prediction,
  scenario rerun and human-review boundary: verified.
