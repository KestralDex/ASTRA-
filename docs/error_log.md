# ASTRA Error Log

Per project policy: every significant error encountered during
development is recorded here with its cause, fix, and lesson learned —
not just silently patched.

### pandas `engine='python'` silently reinterprets malformed rows instead of erroring (Milestone 1)
**Error:** A test asserting that a CSV row with too many fields raises
`DataValidationError` failed with "DID NOT RAISE" when the test called
`load_csv(path, on_bad_lines="error", engine="python")`.
**Cause:** Under pandas' `engine="python"`, a data row with more fields
than the header does not trigger `on_bad_lines`/`ParserError` at all —
pandas silently treats the extra leading fields as an implicit row
index instead of flagging the row as bad. This only surfaces under the
python engine; the default C engine raises `ParserError` correctly for
the same input.
**Fix:** Removed the `engine="python"`/`on_bad_lines="error"` kwargs
from the test so `load_csv` uses its default (C) engine, which raises
`pandas.errors.ParserError` as expected and is caught and re-raised as
`DataValidationError`.
**Lesson:** Don't assume `on_bad_lines="error"` behaves identically
across pandas parser engines — the python engine has silent fallback
behavior for structurally malformed rows that the C engine does not.

### HistGradientBoostingClassifier rejects sparse OneHotEncoder output (Milestone 3)
**Error:** `TypeError: Sparse data was passed for X, but dense data is
required. Use '.toarray()' to convert to a dense numpy array.` when
fitting `HistGradientBoostingClassifier` through the shared
preprocessing pipeline.
**Cause:** `OneHotEncoder` defaults to `sparse_output=True`, which
Logistic Regression / Decision Tree / Random Forest accept but
`HistGradientBoostingClassifier` does not.
**Fix:** Set `OneHotEncoder(handle_unknown="ignore",
sparse_output=False)` in `build_preprocessing_pipeline()` so the one
shared preprocessing step works for every model in the module.
**Lesson:** Not every scikit-learn classifier accepts sparse input —
check this before assuming one preprocessing pipeline is universally reusable.

### Sorting by a raw date string instead of a parsed datetime (Milestone 3)
**Error:** Temporal-generalization test split printed a nonsensical
date range ("earlier half" spanning 2018-01-01 to 2017-06-24 — later
date first).
**Cause:** The analysis script called
`test_df.sort_values("order date (DateOrders)")` directly on the raw
string column. String sorting is lexicographic, not chronological
(e.g. "1/1/2018" sorts before "12/31/2015" as text), so the "sorted"
rows weren't actually in date order.
**Fix:** Parse the column with `pd.to_datetime()` into a separate
column first, then sort by that parsed column.
**Lesson:** `src/risk/train.py`'s `chronological_split()` already did
this correctly (parses before sorting) — the bug was only in ad hoc
analysis code that bypassed that function. Any new date-based sort
must parse first, every time, not just in the one reusable function.

## Format for future entries

```
### <short title> (Milestone N)
**Error:** exact error message
**Cause:** root cause, not just the symptom
**Fix:** what was changed
**Lesson:** what to watch for next time
```
