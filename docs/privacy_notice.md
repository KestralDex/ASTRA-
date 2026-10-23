# ASTRA Research Prototype Privacy Notice

**Project:** Autonomous Supply Chain Transformation, Resilience & Adaptive Intelligence Platform (ASTRA)

**Purpose:** ASTRA v0.1 is an academic/research decision-support prototype used to analyze historical supply-chain data, estimate late-delivery risk, run model-based what-if scenarios, and support human review.

## Data used in the current prototype

The October 1 prototype uses the DataCo supply-chain dataset as its current operational reference dataset. The dashboard is designed to minimize exposure of unnecessary customer-identifying fields during normal use.

ASTRA does not need passwords, secrets, payment-card information, or other sensitive credentials for the current demonstration. Users should not enter such information into notes, forms, or future upload features.

## Model inputs and outputs

The M3 delivery-risk model uses a documented set of legitimate prediction-time features. Post-outcome information, including the historical late-delivery target, actual shipping duration, and shipping date, is excluded from prediction input.

Model outputs are estimates based on historical data. They are not guarantees and are not used for autonomous operational execution.

## Storage

The current prototype primarily operates on local project files and Streamlit session state. Human-review records in the current Scenario Lab are session-local unless a future persistent audit store is explicitly implemented.

## Future uploads and personal data

If ASTRA later accepts organizational datasets, persistent uploads, accounts, analytics, or feedback, the privacy notice and consent process must be updated before deployment. Collection should follow data-minimization and purpose-limitation principles.

## Contact / project responsibility

For the current academic prototype, project questions should be handled through the project team/institutional review process.

**Status:** Prototype privacy notice; not a legal certification.
