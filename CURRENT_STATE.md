# CURRENT STATE — Football Model

Last updated: 2026-09-13
Canonical repository: `luccawong/football-model`
Default model: `MODEL_1`

## Formal status

MODEL_1 remains the active default model. Its one-month freeze remains active through 2026-10-10 Beijing time except for specifically documented user-authorized targeted overrides.

Current active extension registry:
- `docs/MODEL_1_EXTENSION_REGISTRY_20260912.md`

Latest targeted formal addition:
- `models/MODEL_1_EXTENSION_20260913_POST_EUROPE_RESIDUAL.md`
- `config/post_europe_residual_policy.json`

## Latest completed research

### Post-Europe Market Residual Effect

Final research status: `PASS`
MODEL_1 decision: `ADMIT`
Formal name: `POST_EUROPE_MARKET_RESIDUAL_EFFECT`
Interface field: `post_europe_residual_flag`
Evidence root: `research/post_europe_residual/`

Final calibration evidence:
- 2021–2026, five seasons;
- 1,833 canonical post-Europe observations;
- 8,672 controls from the same European-participating club universe;
- 59 clubs;
- adjusted non-win residual: +4.10pp;
- two-way cluster p=0.0001;
- within-team GEE OR=1.204, p=0.0004;
- wild-cluster p<0.0001;
- 4/5 seasons adjusted positive;
- 5/5 leagues adjusted positive;
- PPG residual -0.0715 points/match, p=0.0014;
- PPG residual negative in 5/5 seasons and 5/5 leagues.

Runtime interpretation:
- validated schedule-risk/context feature;
- no fixed +4.1pp or -0.0715 mechanical adjustment;
- Big-Five calibration only;
- first Big-Five league match after UCL/UEL/UECL, 0<hours<=168;
- UNKNOWN when sequence evidence cannot be verified;
- NOT_CALIBRATED outside validated scope;
- if both teams qualify, compare relative context and do not double-count a fixed penalty;
- opening-only first impression remains uncontaminated.

Not promoted from this research:
- shallow-favourite AH effect remains WATCH;
- post-Europe × TRUE_RETREAT incremental interaction unresolved due insufficient control sample;
- Europe-away × league-away standalone rule rejected;
- UECL sandwich standalone rule rejected;
- rest bucket standalone rule rejected;
- rotation/XI-carryover mechanism not validated from historical data.

## Archival state

Canonical text research artifacts and final statistical tables are under `research/post_europe_residual/`.

Large/binary artifact archival remains a maintenance item. See `research/post_europe_residual/ARTIFACT_MANIFEST.md`; do not assume every source XLSX or the 1,833-row match-level CSV has already been committed to GitHub.

## Next engineering follow-up

The research admission is complete. A deterministic runtime extractor/test for `post_europe_residual_flag` can be added later without changing the research conclusion. Until such code is verified, the flag must be derived only from reliable pre-match schedule/identity evidence and must never be fabricated.

No further statistical re-mining of this effect is currently required.
