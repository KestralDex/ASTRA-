# ASTRA Data & Model Governance

## Core principles

ASTRA follows five design principles for the current prototype:

- Data minimization
- Prediction-time leakage prevention
- Least privilege
- Traceability
- Human-in-the-loop decision support

## Data handling

- Treat external datasets and future uploads as untrusted input.
- Validate required schema and types before analytics or model inference.
- Avoid exposing raw customer-identifying fields in normal dashboard views.
- Do not commit raw datasets, credentials, `.env` files, or private logs to source control.
- Verify dataset provenance and licensing before redistribution.

## Model governance

The M3 late-delivery model must be used through its documented nine-feature prediction contract. Historical outcome/post-outcome fields must not enter inference.

Every displayed M3 result should surface the model version. Evaluation metrics must be described as historical holdout results rather than production guarantees.

## Scenario governance

Scenario Lab:
- reruns the same M3 model on a changed legitimate input profile;
- reports probability changes in percentage points;
- labels results as model sensitivity rather than causal impact;
- performs no operational execution;
- requires human review.

## Future AI / RAG / agent modules

Future LLM or agent components must:
- treat prompts and retrieved documents as untrusted data;
- preserve evidence/provenance;
- avoid unrestricted shell, filesystem, database, credential, or transaction tools;
- require explicit human approval before any real-world action.

## Auditability

The current prototype surfaces selected record identifiers, model version, baseline/scenario probabilities and the human-review decision. Persistent tamper-resistant audit logging remains future work.
