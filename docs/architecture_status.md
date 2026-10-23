# ASTRA Architecture Status

Tracks every major module against the synopsis/presentation's proposed
architecture. Updated honestly as development progresses — a status
here reflects what has actually been built and tested, not aspiration.

| Module | ASTRA role | Status | Notes |
|---|---|---|---|
| Data Integration | Ingests raw sources | **IMPLEMENTED / evolving** | DataCo ingestion + validation done (Milestone 1). M5 ingestion not started. |
| Operational / Delivery Risk Intelligence | Predicts late-delivery risk from DataCo | **PARTIALLY IMPLEMENTED** | Milestone 3: trained, evaluated, saved model + `predict_risk()` API. Not yet wired into any downstream layer. |
| Demand Intelligence | Forecasts product demand from M5 | **PLANNED** | Milestone 4/5. No M5 data received yet. |
| Disruption Intelligence | External context (weather/news) | **PLANNED** | Milestone 7. No API integration started. |
| Supplier Risk Intelligence | Supplier-level risk signals | **DATA-DEPENDENT** | No supplier-level dataset identified yet — synopsis does not currently specify a source for this. |
| RAG Evidence Layer | Retrieval-grounded evidence | **PLANNED** | Milestone 8. |
| LLM Reasoning / Explanation | Evidence-grounded explanation & recommendation | **PLANNED** | Milestone 9. Milestone 3's risk module is numerical-only — no LLM layer yet. |
| Impact Analysis | Cross-signal reasoning | **PLANNED** | Milestone 9-ish per synopsis's conceptual flow; depends on multiple intelligence modules existing first. |
| Multi-Agent Decision Layer | Specialized agents coordinating outputs | **PLANNED** | Milestone 10. |
| Scenario Simulator | What-if disruption simulation | **PLANNED** | Milestone 11. |
| Security & Governance | Cross-cutting protection/traceability | **PARTIALLY IMPLEMENTED** | Secrets handling (`.env`), safe file loading, PII exclusion from ML/logs, and trusted-artifact-only model loading are in place. No authentication/RBAC (explicitly out of scope until justified per synopsis). |
| ASTRA Command Center (dashboard) | Streamlit UI | **PLANNED** | Milestone 12. |

## What Milestone 3 actually delivers

Operational / Delivery Risk Intelligence moves from PLANNED to
**PARTIALLY IMPLEMENTED**: a trained, evaluated risk-classification
model with a clean `predict_risk()` function returning a probability +
class + model version. It is a working module on its own — it is not
yet connected to Impact Analysis, Agents, Simulation, or the Dashboard,
none of which exist yet. No functionality described above is
fabricated to look more complete than it is; PLANNED means genuinely
not started.
