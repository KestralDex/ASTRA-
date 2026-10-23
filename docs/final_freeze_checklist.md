# ASTRA Final Freeze Checklist

## Before UI freeze
- [x] Critical smoke test passed.
- [x] Full test suite passed: 57 tests.
- [x] Real DataCo schema verified.
- [x] M3 artifact and 9-feature contract verified.
- [x] Scenario rerun verified.
- [x] Human-review/no-execution boundary verified.
- [ ] Apply final visual-polish pack.
- [ ] Re-run smoke test after visual changes.
- [ ] Re-run `python -m pytest -q`.

## Manual rehearsal
- [ ] Complete the exact demo flow twice consecutively.
- [ ] Verify charts at presentation resolution.
- [ ] Verify no stale record/session values.
- [ ] Verify Scenario Lab handles fresh session without crashing.
- [ ] Verify Governance page opens.
- [ ] Verify no browser traceback or sensitive path is shown.

## Freeze
- [ ] Run `python scripts/create_demo_backup.py`.
- [ ] Keep the generated ZIP in a second location.
- [ ] Commit the final working code to Git.
- [ ] Record the final commit SHA.
- [ ] Do not retrain or replace the M3 artifact after freeze.
- [ ] Do not add new major modules after freeze.

## Presentation machine
- [ ] Python 3.12 environment active.
- [ ] scikit-learn 1.5.2 confirmed.
- [ ] DataCo archive present locally.
- [ ] `streamlit run dashboard/app.py` tested.
- [ ] Browser tab already open.
- [ ] Laptop charger available.
- [ ] Core demo works without internet.

## Final demo-ready definition

The build is ready when the visual-polish version:
1. passes the smoke test;
2. passes all pytest tests;
3. completes the full browser flow twice;
4. has a backup and final Git commit.
