# ASTRA
**Autonomous Supply Chain Transformation, Resilience & Adaptive Intelligence Platform**

ASTRA is our final-year B.E. AIML major project. It is being built as a research decision-support prototype for supply-chain intelligence: detecting risk signals, analysing them, supporting what-if scenarios, and later producing evidence-grounded recommendations for human review.

It does **not** autonomously place orders or modify enterprise systems.

## Current progress

- **Milestone 0 — Foundation:** complete
- **Milestone 1 — DataCo ingestion and validation:** complete
- **Milestone 2 — Exploratory data analysis:** complete
- **Milestone 3 — Operational / delivery risk intelligence:** current

The first three milestones establish the project structure, validate the real DataCo dataset, define the prediction contract, check privacy and target leakage, and explore which order-time variables are useful for delivery-risk modelling.

## ASTRA architecture

The project is being developed toward the architecture proposed in our synopsis and presentation:

- DataCo → Operational / Delivery Risk Intelligence
- M5 → Demand Intelligence
- External context → Disruption Intelligence
- RAG → Evidence / Knowledge Layer
- Specialized agents → Multi-Agent Decision Layer
- Scenario Simulator → What-if resilience analysis
- Security & Governance → protection, traceability and human review
- Dashboard → ASTRA Command Center

Supplier-specific intelligence remains data-dependent and will not be fabricated if the available public datasets cannot support it.

## Local setup

Python 3.11+ is recommended. Development so far has used Python 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest tests/ -v
```

The Milestone 2 review confirmed **36/36 tests passing**.

## Data

Large raw datasets are intentionally not committed to GitHub.

Expected locally:

- `DataCoSupplyChainDataset.csv`
- `DescriptionDataCoSupplyChain.csv`
- M5 dataset later in the demand-intelligence milestone

`tokenized_access_logs.csv` remains out of scope.

## Development approach

Each milestone is developed separately, tested, reviewed, and only then treated as stable project progress. We keep leakage checks, privacy, reproducibility, and explainability as part of the implementation rather than adding them only at the end.

## Safety and scope

ASTRA is a decision-support system. Recommendations produced by later AI components will require human review and will not directly execute procurement, routing, payments, permissions, or other real-world actions.
