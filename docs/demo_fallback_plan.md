# ASTRA Demo Fallback Plan

## If Streamlit fails to start
1. Confirm `.venv` is active.
2. Run `python --version` and confirm Python 3.12.
3. Run `python scripts/demo_smoke_test.py`.
4. Restart with `streamlit run dashboard/app.py`.

## If DataCo is not found
Confirm:
`C:\Users\Sakshi\Desktop\ASTRA\archive\DataCoSupplyChainDataset.csv`

Do not move or rename the archive on presentation day.

## If Scenario Lab opens without a baseline
Return to Data Explorer, select an Order Item, wait for the M3 prediction, then
open Scenario Lab again.

## If a graph becomes cramped
Use the tabbed Visual Intelligence workspace and browser zoom around 90–100%.
Do not rewrite layout code during the presentation.

## If the live demo cannot be recovered quickly
Present the validated architecture and state clearly that the automated
pre-demo checks passed. Do not invent live results.

## Never do during the presentation
- retrain the model;
- modify package versions;
- install new libraries;
- edit the source live;
- expose `.env`, API keys, raw credentials or customer-sensitive fields.
