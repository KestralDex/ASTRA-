# DataCo EDA Summary (Milestone 2)

## Research question
Using information legitimately available when an order's shipping
decision is being planned, can ASTRA estimate the probability that the
order will eventually experience late delivery?

## Prediction moment
Order / shipping-planning time — after the order is placed and its
shipping mode/window is decided, before the shipment has occurred. Full
per-column classification: `docs/prediction_contract.md`.

## Target
`Late_delivery_risk` — 98,977 late (54.83%) vs 81,542 not late (45.17%).

OBSERVATION: The two classes are close to balanced (54.8% / 45.2%).
INTERPRETATION: This is not a severe class-imbalance problem — accuracy
alone won't be trivially misleading the way it would be at, say, a
95/5 split — but precision/recall/F1 should still drive evaluation
(Milestone 3), since the business cost of a false negative (missed
late-delivery risk) vs. a false positive likely differs. See `fig01_target_distribution.png`.

## Important relationships found

### Shipping Mode — the dominant signal
OBSERVATION: Late-delivery rate varies sharply by `Shipping Mode`:
Standard Class 38.1% (n=107,752), Same Day 45.7% (n=9,737), Second
Class 76.6% (n=35,216), First Class 95.3% (n=27,814). See
`fig02_late_rate_by_shipping_mode.png`.
INTERPRETATION: `Shipping Mode` appears strongly associated with
late-delivery risk in this data. This does **not** mean faster shipping
"causes" lateness — see the Shipping Mode section below for why this
pattern more likely reflects how the "late" label itself is defined
relative to a tighter promised window.

### Most other categorical variables are nearly flat
OBSERVATION: `Market` (54.6%–55.2%), `Customer Segment` (54.7%–55.1%),
`Order Region` (48.8%–58.0% across 23 regions, mostly clustered near
the 54.8% overall rate), and `Type` (48.5%–57.5%) all show late rates
close to the overall 54.8% average, with no single category standing
out sharply the way `Shipping Mode` does.
INTERPRETATION: Geography, customer segment, and payment type appear
to carry comparatively little independent association with lateness in
this dataset — `Shipping Mode` and its correlate `Days for shipment
(scheduled)` are where the real signal concentrates.

### Numeric order-value variables show no observed relationship
OBSERVATION: `Order Item Quantity`, `Order Item Product Price`, `Order
Item Discount`, `Order Item Discount Rate`, `Sales`, and `Order Item
Total` all have nearly identical means between the late and not-late
groups (e.g. Order Item Total: 183.61 vs 182.69). See
`fig08_order_item_total_by_target.png`.
INTERPRETATION: Order size/value does not appear to be associated with
delivery lateness in this data — this is a genuine null finding, not
an omission.

### Temporal variables show no observed relationship
OBSERVATION: Late-delivery rate by order year (54.5%–56.3%), month
(54.1%–55.8%), day of week (54.3%–55.2%), and hour (50.9%–59.5%) all
stay close to the overall average with no clear trend or cycle. See
`fig04_late_rate_by_month.png`.
INTERPRETATION: Time-based features derived from `order date
(DateOrders)` do not appear informative on their own in this data —
also a genuine null finding.

## Shipping-mode findings (Section 11 deep dive)

OBSERVATION: `Shipping Mode` and `Days for shipment (scheduled)` are
**perfectly collinear** in this dataset — every `Same Day` order has
`scheduled = 0`, every `First Class` order has `scheduled = 1`, every
`Second Class` order has `scheduled = 2`, every `Standard Class` order
has `scheduled = 4`, with zero exceptions across all 180,519 rows. See
`fig06_shipping_mode_vs_scheduled_days.png`.

INTERPRETATION: These two columns are not two independent predictors —
they are two representations of one planning decision (which shipping
tier was chosen). Using both as separate model features would not add
independent information; a future modeling step should treat them as
one signal, not two. This also explains the `Shipping Mode` late-rate
pattern above: faster/shorter promised windows (`First Class` = 1 day
promised) leave less slack before a shipment counts as "late," which
is a *definitional* mechanical relationship, not evidence that fast
shipping causes problems. We do not call this causal.

## Leakage demonstration (Section 12)

OBSERVATION: Comparing the PLANNED duration (`Days for shipment
(scheduled)`) against the ACTUAL duration (`Days for shipping (real)`)
by target class: for not-late orders, `real - scheduled` ranges from
-2 to 4 (median -1, i.e. delivered before or at the scheduled window in
most cases); for late orders, `real - scheduled` ranges from 1 to 4
(median 1, i.e. **always** at least one day over the scheduled window).
See `fig07_leakage_real_vs_scheduled_by_target.png`.

INTERPRETATION: This cleanly illustrates why `Days for shipping (real)`
is target leakage — the "late" label is essentially defined by whether
the actual duration exceeded the planned one, so a feature built from
the actual duration is functionally restating the answer, not
predicting it. `Days for shipment (scheduled)` shows the same
underlying planning information but *without* revealing the outcome,
which is why it stays a legitimate candidate feature and `Days for
shipping (real)` does not.

## Geographic findings

OBSERVATION: Across the 23 `Order Region` values, late-delivery rate
ranges from 48.8% (Canada, n=959) to 58.0% (Central Africa, n=1,677),
clustered fairly tightly around the 54.8% overall rate; no region
shows a dramatic outlier the way `Shipping Mode` categories do. See
`fig05_late_rate_by_order_region.png`.

Several regions have modest sample sizes (e.g. Canada n=959, Central
Asia n=553, Southern Africa n=1,157) — their rates should be read with
more caution than large-sample regions like Central America
(n=28,341) or Western Europe (n=27,109), even though none fell below
this notebook's 30-row stability threshold.

INTERPRETATION: Geography (at Market/Region/Country granularity)
doesn't show a strong independent relationship with lateness in this
data, unlike Shipping Mode.

## Potential useful features (from this milestone's evidence)

- `Shipping Mode` (or the collinear `Days for shipment (scheduled)` —
  not both)
- `Type` (mild variation, worth including as a candidate)
- Product/category fields (`Category Name`, `Department Name`) — not
  yet directly tested against the target this milestone, carried
  forward as CONSIDER pending Milestone 3 analysis

## Features to exclude

- **Leakage:** `Days for shipping (real)`, `shipping date
  (DateOrders)`, `Delivery Status`
- **Redundant:** `Order Customer Id`, `Product Category Id`, `Order
  Item Cardprod Id`, `Sales per customer`, `Product Price`, `Order
  Profit Per Order` (see `docs/prediction_contract.md` for
  representative fields)
- **Identifiers (no generalizable signal):** `Category Id`,
  `Department Id`, `Product Card Id`, `Customer Id`, `Order Id`, `Order
  Item Id`
- **Constant/empty:** `Product Description`, `Product Image`, `Product
  Status`
- **Privacy:** `Customer Fname`, `Customer Lname`, `Customer Email`,
  `Customer Password`, `Customer City`, `Customer State`, `Customer
  Street`, `Customer Zipcode`, `Customer Country`, `Latitude`,
  `Longitude` — see privacy section below

## Leakage risks (summary — full table in `docs/prediction_contract.md`)

`Days for shipping (real)` and `shipping date (DateOrders)` are HIGH
leakage risk (post-outcome, near-deterministic relationship to
target). `Delivery Status` is HIGH risk as an alternate target
encoding. `Benefit per order`, `Order Profit Per Order`, and `Order
Item Profit Ratio` are UNCERTAIN — not confirmed available at
prediction time, not analyzed against the target this milestone, and
should not be assumed safe by default.

## Privacy exclusions

`Customer Fname`, `Customer Lname` — direct personal information.
`Customer Email`, `Customer Password` — masked/constant in this file
but personal fields by nature. `Customer City`, `Customer State`,
`Customer Street`, `Customer Zipcode`, `Customer Country`, `Latitude`,
`Longitude` — the supplied data dictionary's own text is inconsistent
about whether these describe the customer or the store, and the actual
cardinality (e.g. 7,458 unique `Customer Street` values, 11,250 unique
`Latitude` values) contradicts the "store location" reading — treated
as customer-identifying pending clarification. No real customer names
or addresses are reproduced anywhere in this notebook or these
reports.

## Data limitations

- This is a single historical dataset (2015–2018) from one source —
  findings describe patterns in this data, not causal or universal
  claims about shipping/delivery behavior in general.
- `Order Zipcode` is 86.24% missing — any analysis needing it would be
  working from a small, possibly non-representative subset.
- The "store vs. customer" ambiguity in geography fields could not be
  resolved from the data alone — treated conservatively (excluded), but
  a real clarification from whoever supplied the dictionary would be
  better than an assumption either way.
- `Benefit per order`/profit-related fields' operational timing remains
  unconfirmed — Milestone 3's leakage audit should resolve this before
  any of them are used.
- Sample-size caution applies to smaller `Order Region` categories.

## EDA conclusions

`Shipping Mode` (equivalently, `Days for shipment (scheduled)`, since
they're collinear) is by far the strongest observed signal for
`Late_delivery_risk` in this dataset. Geography, customer segment,
payment type, order value, and time-based features show comparatively
weak or no observed relationship. The target itself is reasonably
balanced. The leakage boundary identified in Milestone 1 holds up under
closer inspection — `Days for shipping (real)` and `shipping date
(DateOrders)` are cleanly demonstrated to be near-restatements of the
outcome, not predictors of it.
