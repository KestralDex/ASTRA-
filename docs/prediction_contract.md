# ASTRA Prediction Contract (Milestone 2)

## TARGET
`Late_delivery_risk` (0 = not late, 1 = late). Not modified from Milestone 1.

## PREDICTION MOMENT
**Order / shipping-planning time** — the point at which an order has
been placed and its shipping plan (mode, scheduled window) has been
decided, but the shipment has not yet occurred.

## QUESTION
What is the probability that this order will eventually experience late delivery?

---

## Column classification

Categories: **AVAILABLE** (known at prediction moment), **UNCERTAIN**
(timing/derivation not confirmed from the data alone), **UNAVAILABLE /
LEAKY** (only known post-outcome), **TARGET**, **REDUNDANT** (exact
duplicate of another column), **PRIVACY-EXCLUDED**, **LOW-INFORMATION**
(constant, empty, or a raw identifier with no generalizable signal).

Availability is **not** assumed by default — every non-obvious column
below has an explicit reason, and several that might look safe on the
column name alone are marked UNCERTAIN or PRIVACY-EXCLUDED instead.

| Column | Classification | Reason | Operational timing |
|---|---|---|---|
| `Late_delivery_risk` | TARGET | The prediction target | Known only after delivery |
| `Delivery Status` | UNAVAILABLE / LEAKY | Deterministic alternate encoding of the target (Milestone 1 finding) | After delivery resolves |
| `Days for shipping (real)` | UNAVAILABLE / LEAKY | Actual shipping duration; 97.55% match with target (Milestone 1 finding) | After shipment completes |
| `shipping date (DateOrders)` | UNAVAILABLE / LEAKY | Actual shipment date/time | After shipment completes |
| `Days for shipment (scheduled)` | AVAILABLE | Planned delivery window, set when order is placed | Order time |
| `Shipping Mode` | AVAILABLE | Chosen when the order is placed | Order time |
| `Type` | AVAILABLE | Transaction/payment type, set at order entry | Order time |
| `order date (DateOrders)` | AVAILABLE | Basis for temporal features (year/month/day-of-week) | Order time |
| `Order Item Quantity` | AVAILABLE | Set when the order line is created | Order time |
| `Order Item Product Price` | AVAILABLE | Listed price at order time | Order time |
| `Product Price` | REDUNDANT | 100% identical to `Order Item Product Price` (new finding) | — |
| `Order Item Discount` | AVAILABLE | Applied at order time | Order time |
| `Order Item Discount Rate` | AVAILABLE | Applied at order time | Order time |
| `Order Item Total` | AVAILABLE | Line total computed at order time | Order time |
| `Sales per customer` | REDUNDANT | 100% identical to `Order Item Total` (new finding) | — |
| `Sales` | AVAILABLE | Distinct from `Sales per customer`/`Order Item Total` (only 5.6% overlap) — a separate, order-time value figure | Order time |
| `Benefit per order` | UNCERTAIN | Per-order profit figure. Plausibly computed from known price/cost at order time, but the supplied dictionary doesn't state whether it can include later adjustments (e.g. returns) — not confirmed independent of outcome | Unconfirmed |
| `Order Profit Per Order` | REDUNDANT | 100% identical to `Benefit per order` (new finding) — inherits the same UNCERTAIN concern | — |
| `Order Item Profit Ratio` | UNCERTAIN | Same concern as `Benefit per order` — a ratio derived from profit, timing not confirmed | Unconfirmed |
| `Order Status` | UNCERTAIN | Includes states that only apply *after* order placement (`PROCESSING`, `ON_HOLD`, `PAYMENT_REVIEW`, `SUSPECTED_FRAUD`, `COMPLETE`, `CLOSED`) — the value at the true prediction moment (order entry) is not necessarily the value stored in this row (which reflects a later, possibly final, status) | Partially post-order — not confirmed as order-time |
| `Market` | AVAILABLE | Destination market group, known at order time | Order time |
| `Order Region` | AVAILABLE | Destination region, known at order time | Order time |
| `Order Country` | AVAILABLE | Destination country, known at order time | Order time |
| `Order State` | AVAILABLE | Destination state; legitimate but high cardinality (1,089) — recommend grouping before use | Order time |
| `Order City` | AVAILABLE | Destination city; legitimate but very high cardinality (3,597) — recommend grouping/exclusion rather than raw use | Order time |
| `Order Zipcode` | LOW-INFORMATION | 86.24% missing (Milestone 1 finding) — too sparse to be a reliable feature as-is | Order time (but mostly absent) |
| `Customer Segment` | AVAILABLE | Consumer/Corporate/Home Office, set at account/order level | Order time |
| `Category Name` | AVAILABLE | Product attribute | Order time |
| `Department Name` | AVAILABLE | Product/store attribute | Order time |
| `Product Name` | AVAILABLE | High cardinality — usable but should be checked for generalization risk | Order time |
| `Category Id`, `Department Id`, `Product Card Id`, `Customer Id`, `Order Id`, `Order Item Id` | LOW-INFORMATION | Raw identifiers — unique/near-unique codes with no generalizable pattern by themselves (Milestone 1 role: IDENTIFIER); `Category Name`/`Department Name` carry the same information in usable form for the first two | Order time (but not useful as direct features) |
| `Order Customer Id` | REDUNDANT | 100% identical to `Customer Id` (Milestone 1 finding) | — |
| `Product Category Id` | REDUNDANT | 100% identical to `Category Id` (Milestone 1 finding) | — |
| `Order Item Cardprod Id` | REDUNDANT | 100% identical to `Product Card Id` (Milestone 1 finding) | — |
| `Product Description` | LOW-INFORMATION | 100% missing (Milestone 1 finding) | — |
| `Product Image` | LOW-INFORMATION | A URL string, not a predictive attribute | — |
| `Product Status` | LOW-INFORMATION | Constant (`0`) across all rows (Milestone 1 finding) | — |
| `Customer Fname`, `Customer Lname` | PRIVACY-EXCLUDED | Direct personal information (customer name) | Order time, but excluded regardless |
| `Customer Email`, `Customer Password` | PRIVACY-EXCLUDED | Masked/constant in this file, but named as personal fields — excluded on principle, not just because they're currently uninformative | — |
| `Customer City`, `Customer State`, `Customer Street`, `Customer Zipcode`, `Customer Country` | PRIVACY-EXCLUDED | **Ambiguous/contradictory documentation** (see below) plus cardinality evidence inconsistent with the "store location" claim — treated as customer-identifying pending clarification | Order time, but excluded regardless |
| `Latitude`, `Longitude` | PRIVACY-EXCLUDED | Same ambiguity/evidence conflict as above (see below) | Order time, but excluded regardless |

### Ambiguous/contradictory documentation — geography fields

The supplied data dictionary's own text is internally inconsistent:
`Customer State` and `Customer Street` are described as belonging to
**"the store where the purchase is registered"**, while `Customer
City` and `Customer Country` are described as **"where the customer
made the purchase."** These read as two different referents (store vs.
customer) for what should be a consistent `Customer *` field group.

The actual data doesn't support the "store" reading: `Customer Street`
has **7,458 unique values** and `Latitude`/`Longitude` have **11,250 /
4,487 unique values** (11,835 unique coordinate pairs) — far too many
distinct values for a real business's physical store network. This
directly contradicts the "store location" description.

**Treatment:** because the documentation is ambiguous and the data
itself is inconsistent with the one reading that would make these
fields non-personal, all `Customer *` geography fields and
`Latitude`/`Longitude` are classified **PRIVACY-EXCLUDED** rather than
resolving the ambiguity in favor of availability. This should be
confirmed with whoever can clarify the field semantics before Milestone 3.

---

## Redundant column pairs — representative field going forward

| Pair | Representative field to retain later | Rationale |
|---|---|---|
| `Order Customer Id` ≡ `Customer Id` | `Customer Id` | Shorter name, same role (LOW-INFORMATION identifier either way) |
| `Product Category Id` ≡ `Category Id` | `Category Id` | Same as above |
| `Order Item Cardprod Id` ≡ `Product Card Id` | `Product Card Id` | Same as above |
| `Sales per customer` ≡ `Order Item Total` | `Order Item Total` | Clearer, unambiguous name |
| `Benefit per order` ≡ `Order Profit Per Order` | `Benefit per order` | Shorter; both inherit the same UNCERTAIN timing concern |
| `Product Price` ≡ `Order Item Product Price` | `Order Item Product Price` | Name makes order-time context explicit |

No columns or the original dataset have been deleted or modified — this
table documents an intended future treatment only.
