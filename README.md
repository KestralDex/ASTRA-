# ASTRA
**Autonomous Supply Chain Transformation, Resilience & Adaptive Intelligence Platform**

Final-year B.E. AIML major project. ASTRA is a **decision-support research
prototype** — it detects supply-chain risk signals, analyzes them,
explains them, simulates what-if scenarios, and recommends mitigations.
It does **not** autonomously place orders or modify enterprise systems.

Built incrementally, one milestone at a time, with each milestone
executed, tested, and approved before the next begins.

## Project status

**Milestone 0 (Foundation) — complete.**
Milestones 1–16 are not yet started. See `docs/milestones.md` (added as
milestones progress) for the full plan.

## Setup

Requires Python 3.11+ (developed and tested on 3.12).

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in API keys **when they're
needed** (not required until Milestone 7+). Never commit `.env`.

## Verify the setup

```bash
python -m pytest tests/ -v
```

All tests should pass. This confirms the package imports, config loads,
logging works, and the expected folder structure exists — it does not
yet test any ASTRA-specific logic, because none exists yet.

## Project structure

```
astra/
├── config/settings.yaml      # central config (paths, logging, random seed)
├── data/                     # raw / interim / processed / external — see below
├── notebooks/                # exploration notebooks, added from Milestone 1 on
├── src/
│   ├── utils/                # config loader, logger, custom exceptions
│   ├── data/                 # loaders, validation, preprocessing (Milestone 1+)
│   ├── features/             # feature engineering (Milestone 3+)
│   ├── forecasting/          # demand forecasting (Milestone 5+)
│   ├── risk/                 # risk classification (Milestone 3+)
│   ├── context/               # external APIs — weather, news (Milestone 7+)
│   ├── rag/                  # retrieval layer (Milestone 8+)
│   ├── agents/                # specialized LLM agents (Milestone 10+)
│   └── simulation/           # scenario simulator (Milestone 11+)
├── models/                    # trained model artifacts (git-ignored)
├── artifacts/{figures,metrics,reports}/  # generated outputs (git-ignored)
├── dashboard/                 # Streamlit app (Milestone 12+)
├── tests/                     # pytest suite
├── logs/                      # runtime logs (git-ignored)
└── docs/                      # error log, data notes, viva material
```

`src/data`, `src/features`, `src/forecasting`, `src/risk`, `src/context`,
`src/rag`, `src/agents`, and `src/simulation` are currently empty
(package placeholders only) — they're populated milestone by milestone,
not all at once.

## Datasets

- **DataCoSupplyChainDataset.csv** — primary dataset, used starting
  Milestone 1 (risk/delivery classification).
- **DescriptionDataCoSupplyChain.csv** — supporting data dictionary for
  the above; used alongside it in Milestone 1, but not assumed accurate
  without checking against the real schema.
- **M5 Forecasting dataset** — to be supplied later, used starting
  Milestone 4 (demand forecasting).
- **tokenized_access_logs.csv** — supplied alongside the DataCo files,
  but **out of scope for now**. Not deleted, not loaded, not part of
  the current architecture. Would only be incorporated later if a
  technically justified ASTRA use case for it is identified.

## Technology (Stage 1)

Python, pandas, NumPy, scikit-learn, matplotlib, Plotly, Jupyter,
Streamlit, SQLite (later), Git. See `requirements.txt` for pinned
versions. Later-stage technologies (FastAPI, PostgreSQL, an LLM API,
FAISS/Chroma, a single lightweight orchestration mechanism) are
introduced only in the milestone that needs them — see the synopsis's
"Technology Principles" for what's explicitly excluded at this stage
(Neo4j, Docker, Kubernetes, Redis, Kafka, multiple agent frameworks,
multiple vector databases) unless a later milestone demonstrates an
actual need.
