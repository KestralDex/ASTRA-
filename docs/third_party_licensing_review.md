# ASTRA Third-Party & Licensing Review

## Current known software categories

The project currently uses common Python/data-science tooling such as:
- Python
- pandas
- NumPy
- scikit-learn
- Plotly
- Streamlit
- pytest
- python-dotenv / PyYAML where applicable

Before any public or production deployment:
- verify package licenses against the pinned dependency versions;
- run a dependency vulnerability audit;
- remove unused packages;
- keep dependencies pinned and reproducible;
- do not expose API keys or service credentials.

## Dataset / media review

- Verify DataCo dataset provenance and redistribution permissions before publishing raw data.
- Do not commit raw datasets to the public repository.
- Use only project-owned, licensed, or appropriately open fonts/images/media.
- Record the source/license of any future icons, logos, illustrations or datasets.

## Current prototype status

This document records the review requirement. It does not claim that every third-party dependency or dataset has completed formal legal/security review.
