# DataCo Schema Summary &amp; Target-Candidate Analysis (Milestone 1)

All findings below come from loading and inspecting the real
`DataCoSupplyChainDataset.csv` (180,519 rows × 53 columns). No values
are invented or assumed from column names alone.

## Column role breakdown (provisional, see `dataco_data_dictionary.csv` for per-column detail)

| Role | Count | Examples |
|---|---|---|
| CATEGORICAL | 19 | `Type`, `Customer Segment`, `Shipping Mode`, `Order Status` |
| NUMERIC | 16 | `Sales`, `Order Item Quantity`, `Benefit per order` |
| IDENTIFIER | 11 | `Order Id`, `Customer Id`, `Product Card Id` |
| UNKNOWN | 3 | `Customer Email`, `Customer Password` (constant/masked), `Product Description` (100% empty) |
| POSSIBLE_TARGET | 2 | `Late_delivery_risk`, `Delivery Status` |
| DATETIME | 2 | `order date (DateOrders)`, `shipping date (DateOrders)` |

"Provisional" is doing real work here — role is inferred from dtype,
name, and cardinality, not confirmed business meaning.

## Target candidates

### `Late_delivery_risk` (int, values 0/1)
- Data dictionary: "indicates if sending is late (1), it is not late (0)".
- Actual distribution: 98,977 rows = 1 (late), 81,542 rows = 0 — a
  reasonably balanced binary target (54.8% / 45.2%).
- **Directly derived from `Delivery Status`**: every row where
  `Delivery Status == "Late delivery"` has `Late_delivery_risk == 1`,
  and every other status (`Advance shipping`, `Shipping on time`,
  `Shipping canceled`) has `Late_delivery_risk == 0`, with **no
  exceptions** in the real file (confirmed by full crosstab). These
  two columns are the same information in two encodings, not two
  independent signals.
- When would it become known? Only once the order has actually shipped
  and delivery status is resolved — i.e. **after the outcome**, not at
  order time.

### `Delivery Status` (categorical, 4 classes)
- Values: `Late delivery` (98,977), `Advance shipping` (41,592),
  `Shipping on time` (32,196), `Shipping canceled` (7,754).
- Same operational-timing problem as `Late_delivery_risk` — it's the
  outcome, not an input.

### Why not `Order Status`?
- `Order Status` (9 classes: COMPLETE, PENDING, CLOSED, ..., 
  SUSPECTED_FRAUD, CANCELED) does not cleanly separate by
  `Late_delivery_risk` (e.g. `CLOSED` rows split ~8,507 vs 11,109
  between the two classes) — it doesn't look like a leakage-free proxy
  for lateness, and conflates several distinct concerns (payment state,
  fraud suspicion, order lifecycle) with delivery timing. Not
  recommended as a target from this initial look.

## Target-leakage review (initial — not exhaustive, revisit at Milestone 3)

**Flagged as post-outcome / high leakage risk if used as a feature for
predicting delivery lateness:**

| Column | Why it's flagged |
|---|---|
| `Days for shipping (real)` | The *actual* shipping duration — only known once the order has shipped. A simple derived rule (`real > scheduled`) matches `Late_delivery_risk` in **97.55%** of rows, meaning this column is nearly a restatement of the target. |
| `shipping date (DateOrders)` | The actual shipment date/time — likewise only known post-shipment. Its gap from `order date (DateOrders)` tracks `Days for shipping (real)` almost exactly (means 3.499 vs 3.498). |
| `Delivery Status` | As above — this *is* the alternate encoding of the target. |

**NOT flagged — appear to be known at order time, so are legitimate
candidate features:**
- `Days for shipment (scheduled)` — the *planned* delivery window, set
  at order time.
- `Shipping Mode` — chosen at order time; strongly associated with
  lateness (e.g. First Class: 95.3% late vs Standard Class: 38.1% late
  in this data), which makes it a genuinely informative, non-leaky
  feature rather than a leakage source.
- `Market`, `Order Region`, `Customer Segment`, `Order Item Quantity`,
  product/category fields, and the geographic fields — all knowable
  when the order is placed.

This is an **initial** review, as instructed — a full audit belongs to
Milestone 3, immediately before model training.

## Redundant / low-value columns confirmed

- `Order Customer Id` ≡ `Customer Id` (100% identical)
- `Product Category Id` ≡ `Category Id` (100% identical)
- `Order Item Cardprod Id` ≡ `Product Card Id` (100% identical)
- `Customer Email`, `Customer Password`, `Product Status` — constant
  across all 180,519 rows, no predictive information.
- `Product Description` — 100% missing, no observed values at all.

These aren't deleted at this stage (Milestone 1 is observational) but
are candidates for exclusion at feature-engineering time.

## Date/time findings

Both `order date (DateOrders)` and `shipping date (DateOrders)` parsed
successfully for 100% of rows (0 failures), spanning 2015-01-01 to
2018-02-06. Shipping date is never earlier than order date in any row
— internally consistent.

---

## Required output: What can ASTRA legitimately predict using this dataset WITHOUT target leakage?

Based on the actual schema, the data dictionary, real class distributions,
and the operational timing of each variable:

**ASTRA can legitimately predict `Late_delivery_risk` (or equivalently
recast `Delivery Status`) as a binary late/not-late classification
problem, provided the feature set excludes `Days for shipping (real)`,
`shipping date (DateOrders)`, and `Delivery Status` itself** (the last
being the target's alternate encoding, not a feature). The remaining
fields — `Days for shipment (scheduled)`, `Shipping Mode`, `Market`,
`Order Region`/`Order Country`/`Order State`, `Customer Segment`,
product/category identifiers and pricing, `Order Item Quantity`, and
order-time geography — are all knowable at order placement and show
real association with the outcome (Shipping Mode especially), so there
is a genuine, non-trivial prediction problem here, not just a restated
label.

This is a recommendation for what to *investigate* in Milestone 2/3,
not a final, trained decision — a full leakage audit (Milestone 3's
first step) and EDA (Milestone 2) still need to happen before any
model is built.
