# football-model

Private, versioned persistent source of truth for the GPT-assisted football model. It is not the Codex web application.

## Current stack
- Model: `GPT-FOOTBALL-FULLSTACK-1.0.0`
- Quant engine: `GPT-QUANT-0.1.0`
- Feature/QC engine: `GPT-FEATURE-1.0.0`

The stack covers deterministic market maths, lifecycle/reversal detection, source freshness/gating, uncertainty/disagreement, independent strength/squad/context modules, open-source adapters, anti-double-counting, calibration/walk-forward validation and independent Red Team adjudication.

## Core rule
More modules do not mean more forced confidence. Missing/stale/conflicting evidence is surfaced; correlated signals are not counted repeatedly; unvalidated context is never converted into arbitrary goal/probability adjustments. Final tickets remain a structured decision after the full evidence stack and Red Team.
