"""
Custom exception types for ASTRA.

WHY THIS FILE EXISTS
---------------------
Using Python's generic Exception everywhere makes it impossible to catch
"a data validation problem" without also accidentally catching bugs like
typos or missing imports. Defining specific exception classes lets later
code write `except DataValidationError:` and know exactly what kind of
failure it's handling, without swallowing unrelated errors.

These are intentionally minimal for Milestone 0 — more will be added as
later milestones need them (e.g. RetrievalError in Milestone 8).
"""


class AstraError(Exception):
    """Base class for all ASTRA-specific exceptions. Catch this to mean
    'something ASTRA-specific went wrong', as opposed to a generic bug."""


class ConfigError(AstraError):
    """Raised when configuration (settings.yaml, .env) is missing or invalid."""


class DataValidationError(AstraError):
    """Raised when input data fails a required validation check
    (missing columns, wrong dtypes, impossible values, etc.).
    Used starting Milestone 1."""
