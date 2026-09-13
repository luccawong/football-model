# AI HANDOFF — Football Model

Purpose: make this repository sufficient for a new ChatGPT/Claude/Codex/DeepSeek/other agent to continue the football project without relying on account-specific chat memory.

## Authority

**GitHub is the Single Source of Truth for formal football-project state.**

Chat history and model memory are auxiliary. A newer explicit user instruction may temporarily supersede GitHub, but the change must then be written back to GitHub before it is considered durable project state.

Never silently reconstruct missing rules from general football knowledge.

## Required read order for a new agent

1. `AI_HANDOFF.md`
2. `CURRENT_STATE.md`
3. `models/MODEL_1_DEFAULT.md`
4. `docs/MODEL_1_EXTENSION_REGISTRY_20260912.md`
5. every active extension referenced by that registry
6. `gpt/FOOTBALL_CANONICAL_MEMORY.md`
7. `gpt/FOOTBALL_SOP.md`
8. `config/model_1_freeze.json`
9. `config/module_registry.json`
10. task-specific research/config files cited by the active extension or current task

If the baseline MODEL_1 file and an active extension differ, treat the extension as the later explicit overlay; do not rewrite historical MODEL_1 identity.

## Current model discipline

- Default formal model: `MODEL_1`.
- Formal source/market authority and execution order are defined by MODEL_1 files, not this handoff summary.
- The one-month MODEL_1 freeze remains active unless an explicit user-authorized targeted override is recorded.
- Do not add fixed weights, thresholds or new formal modules merely because a research result looks promising.
- A research finding becomes formal only when its admission is explicitly recorded in the extension registry/policy.

## Current newly admitted research feature

As of 2026-09-13, the post-Europe residual study passed its final robustness gate and is a targeted formal extension:

- formal name: `POST_EUROPE_MARKET_RESIDUAL_EFFECT`
- interface field: `post_europe_residual_flag`
- policy: `config/post_europe_residual_policy.json`
- formal extension: `models/MODEL_1_EXTENSION_20260913_POST_EUROPE_RESIDUAL.md`
- evidence: `research/post_europe_residual/`

Critical interpretation: ADMIT does **not** authorize a fixed +4.1pp non-win penalty or -0.0715 PPG deduction. These are historical estimates. Runtime use is contextual and must be reconciled with the actual match.

## Non-negotiable audit behaviour

- Separate FACT / INFERENCE / HYPOTHESIS / CONCLUSION.
- Challenge user and model hypotheses; do not agree for convenience.
- No future leakage.
- Preserve opening-only analysis where the SOP requires it.
- Missing evidence remains MISSING/UNKNOWN; never manufacture a complete timeline, lineup or schedule state.
- Do not use post-match information to rewrite a pre-match freeze.
- Once an actionable formal ticket is issued, any later change must be an explicit correction.

## Portability rule

When a new football rule, accepted research finding, crawler contract, database definition or execution policy changes:

1. discuss/audit it;
2. obtain required user authorization where it changes formal semantics;
3. commit the durable state to GitHub;
4. update the relevant registry/current-state/changelog or manifest;
5. only then treat the change as portable across agents/accounts.

Do not let critical project state exist only in one chat.
