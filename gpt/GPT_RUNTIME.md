# GPT Runtime Contract — MODEL_1 Default / Full Stack 1.5

This repository is the persistent cross-chat source of truth for the GPT football analysis stack.

## Model selection

- Read `config/model_registry.json` first.
- Default model is `MODEL_1` unless the user explicitly selects or creates another model.
- MODEL_1 identity must never be overwritten by a future rebuild. If performance later fails to meet expectations, freeze MODEL_1 and create MODEL_2/3/etc with separate rules, activation date and validation.
- Current MODEL_1 profile: `models/MODEL_1_DEFAULT.md`.

## Full-SOP trigger

When the user supplies football match data and requests full SOP + independent Red Team, automatically execute the current default model without requiring the user to name individual modules.

## Mandatory weather rule

- Weather is a mandatory visible output inside Stage 5 `Off-field factors / weather`; it must never be silently omitted.
- For every pre-match analysis, check the match-location weather as close to kickoff as practical, with priority on live/current conditions and short-horizon forecast. When materially relevant, also check precipitation/radar context, wind, temperature, humidity, thunderstorm risk, and pitch/surface implications.
- If heavy rain, thunderstorm, snow, extreme heat/cold, strong wind, or rapidly changing conditions are present, explicitly assess impacts on tempo, passing/first touch, footing, goalkeeper handling, crossing/set pieces, pressing intensity, error rate, finishing quality, substitution/rotation risk, and OU/score-tail distribution.
- Weather must be treated as a context variable, not a mechanical betting direction. Distinguish verified current conditions, forecast, and inference.
- If weather data cannot be verified, output `WEATHER DATA MISSING` rather than omitting the module.

## Canonical loading order

1. `config/model_registry.json`
2. active model profile, currently `models/MODEL_1_DEFAULT.md`
3. `gpt/FOOTBALL_CANONICAL_MEMORY.md`
4. `config/active_decision_policy.json`
5. `gpt/FOOTBALL_SOP.md`
6. `config/module_registry.json`
7. `config/model_1_trace_contract.json`
8. `config/model_1_supporting_contracts.json`
9. `gpt/MEMORY_GAP_AUDIT_2026-09-09.md` as supporting audit only; ACTIVE items may supplement but research/legacy/conflict items cannot override formal policy
10. `config/full_stack_config.json`
11. dedicated Exchange / draw-exclusion files

## MODEL_1 formal analysis order

The formal trace must follow exactly:

1. Fundamentals
2. Market snapshot
3. Opening first impression
4. Opening rationality / lifecycle
5. Off-field factors / weather
6. Lineup / tactics
7. 1X2 + real-open/camouflage-open（实开/韬开）audit after fundamentals
8. Asian handicap + explicit 1X2 -> AH European/Asian conversion consistency audit
9. Totals / OU
10. Cross-market coherence
11. Market attraction
12. External draw-exclusion website + winner audit
13. Underdog outright audit
14. Correct score using repository Poisson/Dixon-Coles/Bayesian framework
15. Uncertainty audit
16. Freeze H1
17. Independent Red Team H2
18. Exactly one formal main ticket

`gpt/decision_engine.py` validates policy gates. `gpt/formal_trace.py` validates and serializes the complete 18-stage audit trace. Research/shadow modules run outside the frozen formal trace and cannot reorder it.

## Formal runtime packets