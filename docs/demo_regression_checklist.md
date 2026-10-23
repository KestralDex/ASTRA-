# ASTRA October 1 Demo Regression Checklist

Complete this after the automated smoke test and `pytest` both pass.

## Freeze target

The October 1 working prototype is:

**Real DataCo → validated M3 risk model → Streamlit Command Center → live risk analysis → model-based what-if simulation → human review**

Do not add a new major intelligence module during this regression pass.

## 1. Cold start

- [ ] Activate the project `.venv`.
- [ ] Start with `streamlit run dashboard/app.py`.
- [ ] No Python traceback appears in the browser.
- [ ] Command Center loads without refreshing twice.
- [ ] M3 status is `ACTIVE`.
- [ ] Scenario Intelligence is `AVAILABLE`.
- [ ] Governance is `AVAILABLE`.
- [ ] Model version shown is `v1.0-milestone3`.

## 2. Command Center live risk analysis

- [ ] Run the default manual risk example.
- [ ] Probability is between 0% and 100%.
- [ ] Predicted class is `LATE DELIVERY` or `NOT LATE`.
- [ ] Model version is visible.
- [ ] No LOW/MEDIUM/HIGH tier is invented.
- [ ] Prediction disclaimer remains visible.
- [ ] `Use This Prediction in Scenario Lab` opens Scenario Lab successfully.

## 3. Data Explorer

- [ ] DataCo loads successfully.
- [ ] Records and unique orders are distinguished correctly.
- [ ] Filters work for Market, Shipping Mode, Segment, Category and Region.
- [ ] Date filter works.
- [ ] Delivery tab renders cleanly.
- [ ] Geography tab renders cleanly.
- [ ] Products tab renders cleanly.
- [ ] Temporal tab renders cleanly at Month, Quarter and Year.
- [ ] No charts overlap or become unreadable at presentation resolution.
- [ ] Order Inspector accepts a valid Order ID.
- [ ] A multi-item order can display multiple items.
- [ ] Historical outcome fields are clearly separated from prediction inputs.
- [ ] Selecting an item produces the exact 9 M3 features.
- [ ] M3 probability appears for the selected item.
- [ ] Model evidence/limitations can be expanded.
- [ ] No raw customer-sensitive dataset dump is shown in the normal preview.

## 4. Scenario Lab

- [ ] Open Scenario Lab from a Data Explorer prediction.
- [ ] Correct selected Order / Item context is shown.
- [ ] Baseline probability is recomputed successfully.
- [ ] Change Shipping Mode.
- [ ] Run scenario successfully.
- [ ] Baseline probability is shown.
- [ ] Scenario probability is shown.
- [ ] Delta is shown in percentage points.
- [ ] Wording says model sensitivity / what-if estimate, not causal effect.
- [ ] Changing a value back to baseline does not create a fake difference.
- [ ] Human Review controls appear.
- [ ] Record `Needs further review`.
- [ ] Record `Accept scenario for consideration`.
- [ ] Record `Reject scenario`.
- [ ] UI confirms no operational action was executed.
- [ ] Review is clearly described as session-local.

## 5. Governance

- [ ] Governance page opens.
- [ ] Privacy notice status is visible.
- [ ] Security controls are visible.
- [ ] Human-in-the-loop boundary is visible.
- [ ] Pending/N/A controls are not falsely shown as implemented.
- [ ] Page does not claim legal certification or production compliance.

## 6. Error-path checks

Perform these carefully and restore the working state afterward.

- [ ] Enter an invalid/nonexistent Order ID; Data Explorer handles it without traceback.
- [ ] Apply filters producing zero records; page handles it cleanly.
- [ ] Open Scenario Lab in a fresh browser session without a handoff; it asks for a Data Explorer record instead of crashing.
- [ ] Empty Category/Department in Command Center is rejected cleanly.
- [ ] User-facing errors do not expose local model paths, secrets or traceback details.

## 7. Presentation-machine check

- [ ] Run on the actual laptop that will be used on October 1.
- [ ] Browser zoom set to a readable level.
- [ ] Projector/screen resolution does not cramp charts.
- [ ] Internet is not required for the core demo.
- [ ] Dataset, model and environment are present locally.
- [ ] Keep one terminal already activated in `.venv`.
- [ ] Keep one browser tab already open to the Command Center.

## 8. Backup / freeze

- [ ] Commit the working code to Git.
- [ ] Keep a second local ZIP backup.
- [ ] Do not modify model artifacts after the final regression pass.
- [ ] Record the final commit SHA used for the presentation.
- [ ] Re-run `scripts\run_demo_checks.ps1` after any code change.

## Demo-ready definition

ASTRA is ready to freeze only when:

1. automated smoke test passes;
2. full pytest suite passes;
3. the exact presentation path succeeds twice consecutively without a crash;
4. a backup and final Git commit exist.
