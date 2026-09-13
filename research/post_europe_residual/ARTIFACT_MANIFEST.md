# Artifact Manifest — Post-Europe Residual Research

Canonical research root: `research/post_europe_residual/`
Final decision: `PASS / ADMIT`
Date: 2026-09-13

## Source database

Historical source database identity used by the research:

- logical file: `football_odds_2021_2026.sqlite` / `titan数据库.sqlite`
- SHA-256: `cb409b3ceb882491671c08abbf6815fdfbaa398010de0377ad1d7bcf0d1531a7`
- matches: 13,090
- coverage: 2021–2026

The raw SQLite database is intentionally not committed in this small-text integration commit. Large raw data should be preserved through Git LFS / release asset / external archival with hash verification rather than ordinary Git history.

## Canonical text artifacts committed here

- `README.md`
- `EURO_POST_LEAGUE_2021_2026_ROBUSTNESS_V3_2.md`
- `EURO_POST_LEAGUE_2021_2026_ACCEPTANCE_V3_2.md`
- `POST_EURO_EFFECT_BY_SEASON.csv`
- `POST_EURO_EFFECT_BY_LEAGUE.csv`
- `EURO_POST_LEAGUE_2021_2026_REPORT_V3_1_FINAL.md`
- `EURO_POST_LEAGUE_2021_2026_ACCEPTANCE_V3_1_FINAL.md`
- `EURO_POST_LEAGUE_2021_2026_V3_TO_V3_1_PATCH.md`
- `INTERNAL_CONSISTENCY_QC.csv`

These text artifacts are sufficient to recover the final statistical conclusion, the audit trail that changed V3 to V3.1, the final V3.2 robustness gate, and the league/season heterogeneity tables.

## Source artifacts not embedded in this commit

The following conversation artifacts existed during the research but are not embedded by this connector pass:

- `EURO_POST_LEAGUE_2021_2026_MATCH_LEVEL_V3_FINAL.csv` — 1,833 match-level rows plus header;
- `EURO_POST_LEAGUE_2021_2026_SUMMARY_V3_1_FINAL.xlsx`;
- `EURO_POST_LEAGUE_2021_2026_ROBUSTNESS_V3_2.xlsx`;
- earlier V1/V2 intermediate outputs and QC files.

Reason: the active GitHub connector writes UTF-8 text but does not provide a direct binary/file-stream upload path from the conversation attachment store, while the local container runtime was unavailable during this integration pass.

**Do not treat this manifest as claiming those binary/large artifacts are already archived in GitHub.**

Recommended next engineering maintenance, when Codex/local Git is available:
1. archive the 1,833-row match-level CSV under this directory or Git LFS;
2. archive the final XLSX convenience workbooks under Git LFS or a release asset;
3. verify hashes and update this manifest;
4. do not change the already-frozen statistical conclusions merely because archival format changes.

## Formal model files

- `../../models/MODEL_1_EXTENSION_20260913_POST_EUROPE_RESIDUAL.md`
- `../../config/post_europe_residual_policy.json`
- `../../docs/MODEL_1_EXTENSION_REGISTRY_20260912.md`

These files define formal MODEL_1 use. Research estimates are not fixed runtime weights.
