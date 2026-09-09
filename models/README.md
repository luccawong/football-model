# Football Model Profiles

Canonical model registry: `config/model_registry.json`.

## Current default

- **MODEL_1** — ACTIVE_DEFAULT — effective 2026-09-09
- Profile: `models/MODEL_1_DEFAULT.md`

MODEL_1 must remain historically stable. If its forward performance later fails to meet expectations, freeze MODEL_1 and create a new independent model profile:

- MODEL_2
- MODEL_3
- ...

Do not rewrite MODEL_1 historical decisions with later model logic. Each new model should have its own effective date, changelog entry, policy/config references and validation sample so MODEL_1 vs later models can be compared cleanly.
