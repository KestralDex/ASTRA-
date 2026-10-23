# DataCo Data Quality Report (Milestone 1)
Generated from an actual load and analysis of `DataCoSupplyChainDataset.csv` — every figure below was computed from the real file, not estimated.
## Dimensions
- Rows: **180,519**
- Columns: **53**
- In-memory size (deep): **298.92 MB**
## Duplicates
- Fully duplicate rows: **0**
## Missing values (columns with any missing, all others are 0%)
| Column | Missing count | Missing % |
|---|---|---|
| Product Description | 180,519 | 100.0% |
| Order Zipcode | 155,679 | 86.24% |
| Customer Lname | 8 | 0.004% |
| Customer Zipcode | 3 | 0.002% |

## Constant / near-constant columns
- **Fully constant (1 unique value):** `Customer Email`, `Customer Password`, `Product Description`, `Product Status`
  - `Customer Email` and `Customer Password` are constant at the placeholder value `XXXXXXXXX` in every row — the source dataset has already been pre-masked, these are not real customer emails/passwords.
  - `Product Status` is constant at `0` in every row.

## Duplicate/redundant columns (confirmed by exact equality check)
- `Order Customer Id` is identical to `Customer Id` in every row.
- `Product Category Id` is identical to `Category Id` in every row.
- `Order Item Cardprod Id` is identical to `Product Card Id` in every row.

## High-cardinality / identifier-like columns
- `Order Item Id` — behave as row/order identifiers, not predictive features.

## Date/time parsing
- `order date (DateOrders)`: 100.0% parse success (0 failed), range 2015-01-01 00:00:00 to 2018-01-31 23:38:00.
- `shipping date (DateOrders)`: 100.0% parse success (0 failed), range 2015-01-03 00:00:00 to 2018-02-06 22:14:00.
- Rows where shipping date precedes order date: **0**.

## Impossible / notable numeric values
- `Benefit per order` and `Order Profit Per Order` are negative in **33,784** rows — this reflects genuine business losses, not a data error, and was not treated as an impossible value.
- No negative values found in Sales, prices, discounts, or quantities.

## Description-file discrepancies
- `Order Zipcode` exists in the dataset but has **no corresponding entry** in `DescriptionDataCoSupplyChain.csv` — undocumented column.
- `shipping date (DateOrders)` (dataset, lowercase 's') vs `Shipping date (DateOrders)` (description file, uppercase 'S') — a case mismatch, not a missing field; resolved by case-insensitive matching.
- Every other dataset column has a matching (whitespace-normalized) entry in the description file.

## Potential privacy/security-relevant columns
- `Customer Fname`, `Customer Lname`, `Customer Street`, `Customer City`, `Customer State`, `Customer Zipcode`, `Latitude`, `Longitude` could represent personally identifying information in a real deployment. `Customer Email` and `Customer Password` are already masked to a constant placeholder and are not sensitive in this file as supplied.
- These values are not reproduced in this report, in logs, or in the notebook beyond single illustrative examples where necessary — flagged for later privacy handling, not deleted at this stage.

## Target-leakage-relevant finding
- A naive derived rule (`Days for shipping (real) > Days for shipment (scheduled)`) matches the supplied `Late_delivery_risk` label in **97.55%** of rows — meaning `Days for shipping (real)` and `shipping date (DateOrders)` are almost fully determined by (or determine) the outcome, and are only knowable **after** delivery. See the schema summary for the full leakage discussion.

## Automated validation result (src/data/validation.py)
- `is_valid`: **True**
- Errors: none
- Warnings: ["Column 'Product Description' is 100% missing (consistent with Milestone 1 finding)."]
