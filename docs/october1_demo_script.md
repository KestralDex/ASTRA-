# ASTRA October 1 Demo Script

## Target length: 4–6 minutes

### 1. Command Center — 30 seconds

“ASTRA is our supply-chain decision-support prototype. For this milestone, the
working core uses real DataCo historical data and a validated delivery-risk
model. The system does not autonomously execute operational actions; human
review remains required.”

Show:
- Data Integration: ACTIVE
- Operational Risk: ACTIVE
- Scenario Intelligence: AVAILABLE
- Governance: AVAILABLE
- Model version: `v1.0-milestone3`

### 2. Data Explorer — 60–90 seconds

Open **Data Explorer**.

“DataCo contains 180,519 order-item records representing 65,752 unique orders.
We keep those two units separate.”

Briefly show:
- global filters;
- one Delivery or Temporal chart;
- Order Inspector.

Do not spend time clicking every graph.

### 3. Real M3 prediction — 60 seconds

Select a real Order ID and Order Item.

“The model is evaluated at DataCo record/order-item representation level. We
extract only the documented nine prediction-time features. Actual shipping
duration, shipping date and the historical target are displayed only for
retrospective inspection and are excluded from model input.”

Show:
- M3 probability;
- predicted class;
- historical outcome;
- model version;
- model evidence/limitations.

### 4. Scenario Lab — 60–90 seconds

Open **Scenario Lab**.

“This is a model-based what-if simulator. We change a legitimate planning input,
such as Shipping Mode, then rerun the same trained M3 model.”

Change Shipping Mode and run.

Show:
- baseline probability;
- scenario probability;
- probability-point delta.

Say:

“The difference is model sensitivity, not proof that the changed shipping mode
causes the outcome.”

### 5. Human Review — 30 seconds

Record **Accept scenario for consideration** or **Needs further review**.

“ASTRA stops here. It records the human review but executes no procurement,
routing, supplier, inventory or financial action.”

### 6. Governance — 30 seconds

Open **Governance & Security**.

“We document privacy, data minimization, model limitations, leakage prevention,
licensing checks, human oversight, and which production controls are still
planned. We do not claim legal certification or enterprise readiness.”

### Closing line

“ASTRA v0.1 demonstrates a validated end-to-end decision-support loop:
real historical data → risk prediction → what-if simulation → human review.
Demand forecasting, external disruption intelligence, RAG and multi-agent
reasoning remain later modules.”
