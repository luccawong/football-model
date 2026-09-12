# MODEL_1 Titan Historical Bayesian Prior Validation — 2026-09-12

## Raw Data Audit

- Source: `titan数据库.zip -> football_odds_2021_2026.sqlite`
- SQLite SHA256: `cb409b3ceb882491671c08abbf6815fdfbaa398010de0377ad1d7bcf0d1531a7`
- Raw matches: **13,090**; completed-score rows: **13,090**; missing FT scores: **0**.
- Date range: **2021-06-23 02:00 → 2026-05-31 00:00**.
- Raw `SELECT DISTINCT competition FROM matches` universe: **德甲, 意甲, 欧冠, 欧协联, 欧罗巴, 法甲, 英超, 西甲**.
- No Excel/JSON/report was used to infer the raw schema or competition universe.

## Competition Coverage

| Competition | N | Completed | Seasons | Teams | HG mean | AG mean | TG mean | Missing | Data QC |
|---|---:|---:|---|---:|---:|---:|---:|---:|---|
| 德甲 | 1530 | 1530 | 2021-2022, 2022-2023, 2023-2024, 2024-2025, 2025-2026 | 25 | 1.767 | 1.409 | 3.176 | 0 | VALID |
| 意甲 | 1890 | 1890 | 2021-2022, 2022-2023, 2023-2024, 2024-2025, 2025-2026 | 27 | 1.392 | 1.212 | 2.604 | 0 | VALID |
| 欧冠 | 1178 | 1178 | 2021-2022, 2022-2023, 2023-2024, 2024-2025, 2025-2026 | 178 | 1.713 | 1.290 | 3.003 | 0 | VALID |
| 欧协联 | 1963 | 1963 | 2021-2022, 2022-2023, 2023-2024, 2024-2025, 2025-2026 | 366 | 1.586 | 1.119 | 2.705 | 0 | VALID |
| 欧罗巴 | 1051 | 1051 | 2021-2022, 2022-2023, 2023-2024, 2024-2025, 2025-2026 | 188 | 1.598 | 1.178 | 2.775 | 0 | VALID |
| 法甲 | 1678 | 1678 | 2021-2022, 2022-2023, 2023-2024, 2024-2025, 2025-2026 | 25 | 1.541 | 1.280 | 2.821 | 0 | VALID |
| 英超 | 1900 | 1900 | 2021-2022, 2022-2023, 2023-2024, 2024-2025, 2025-2026 | 27 | 1.597 | 1.329 | 2.927 | 0 | VALID |
| 西甲 | 1900 | 1900 | 2021-2022, 2022-2023, 2023-2024, 2024-2025, 2025-2026 | 26 | 1.477 | 1.117 | 2.595 | 0 | VALID |

## Model

- Competition-specific hierarchical Poisson: `log(lambda_H)=mu_competition+HFA_competition+Attack_H-Defense_A`; `log(lambda_A)=mu_competition+Attack_A-Defense_H`.
- `mu_league` / `hfa_league` remain legacy API field names only; their runtime semantics are competition-specific.
- Attack/defence are joint opponent-adjusted team-season latent states with Gaussian shrinkage and consecutive-season transition priors.
- New/promoted/domestic-new or first-seen European clubs fall back to the competition baseline; no lower-league or domestic-league strength is copied into another competition.
- Time weighting: `0.5^(age_days / half_life_days)`; hyperparameters selected inside Train only with season-forward folds.
- Base parameter uncertainty: sparse Hessian/Laplace precision propagation to the requested fixture. Added process uncertainty is estimated only from Train inner-OOS goal residuals; no bookmaker fields enter that estimate.
- Market likelihood remains the existing correlated Pinnacle/Bet365/Macau cluster. It is applied after the historical prior.

## Frozen Hyperparameters / Activation

| Competition | half-life | team SD | transition SD | process SD H/A | Calibration | Activation | Reason |
|---|---:|---:|---:|---|---|---|---|
| 德甲 | 1e+09 | 0.25 | 0.005 | 0.188/0.135 | BOUNDARY_UNRESOLVED | SHADOW | UNRESOLVED_HYPERPARAMETER_BOUNDARY |
| 意甲 | 120 | 0.35 | 4 | 0.000/0.000 | BOUNDARY_UNRESOLVED | SHADOW | UNRESOLVED_HYPERPARAMETER_BOUNDARY |
| 欧冠 | 270 | 0.35 | 0.12 | 0.388/0.417 | INTERIOR | ACTIVE | SCORE_OOS_GATE_PASS |
| 欧协联 | 730 | 0.25 | 0.005 | 0.371/0.468 | BOUNDARY_UNRESOLVED | SHADOW | UNRESOLVED_HYPERPARAMETER_BOUNDARY |
| 欧罗巴 | 540 | 0.25 | 0.005 | 0.476/0.000 | BOUNDARY_UNRESOLVED | SHADOW | UNRESOLVED_HYPERPARAMETER_BOUNDARY |
| 法甲 | 2190 | 0.25 | 0.08 | 0.000/0.205 | INTERIOR | SHADOW | SCORE_OOS_GATE_FAIL |
| 英超 | 60 | 0.35 | 0.03 | 0.287/0.285 | INTERIOR | SHADOW | SCORE_OOS_GATE_FAIL |
| 西甲 | 730 | 0.35 | 0.12 | 0.151/0.125 | INTERIOR | SHADOW | SCORE_OOS_GATE_FAIL |

Boundary handling: whenever the original research grid winner landed on an edge, the grid was extended. 德甲, 意甲, 欧协联 and 欧罗巴 remained edge-seeking after extension and therefore stay `SHADOW`; their numeric hyperparameters are research-only provisional values, not production claims.

## OOS A/B/C — Validation 2024-25

| Competition | N | A NLL | B NLL | C NLL | A Top3 | B Top3 | C Top3 | A 1X2 Brier | C 1X2 Brier | A RPS | C RPS | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 德甲 | 306 | 3.0780 | 3.1344 | 3.0784 | 0.242 | 0.235 | 0.229 | 0.5914 | 0.5934 | 0.2022 | 0.2033 | SHADOW |
| 意甲 | 380 | 2.7392 | 4.0161 | 2.7426 | 0.395 | 0.266 | 0.397 | 0.5672 | 0.5673 | 0.1839 | 0.1839 | SHADOW |
| 欧冠 | 251 | 3.0827 | 3.2767 | 3.0813 | 0.263 | 0.211 | 0.271 | 0.5023 | 0.5035 | 0.1844 | 0.1850 | ACTIVE |
| 欧协联 | 311 | 2.8864 | 3.0090 | 2.8851 | 0.347 | 0.334 | 0.347 | 0.5731 | 0.5722 | 0.2030 | 0.2026 | SHADOW |
| 欧罗巴 | 269 | 2.8915 | 3.0740 | 2.8966 | 0.320 | 0.249 | 0.316 | 0.5458 | 0.5475 | 0.1909 | 0.1919 | SHADOW |
| 法甲 | 306 | 2.9653 | 3.0374 | 2.9678 | 0.294 | 0.268 | 0.291 | 0.5642 | 0.5650 | 0.2012 | 0.2013 | SHADOW |
| 英超 | 380 | 2.9435 | 3.1368 | 2.9470 | 0.321 | 0.274 | 0.321 | 0.5760 | 0.5761 | 0.1963 | 0.1963 | SHADOW |
| 西甲 | 380 | 2.7249 | 2.8217 | 2.7317 | 0.405 | 0.382 | 0.400 | 0.5582 | 0.5617 | 0.1869 | 0.1887 | SHADOW |

## OOS A/B/C — Test 2025-26

| Competition | N | A NLL | B NLL | C NLL | A Top3 | B Top3 | C Top3 | A 1X2 Brier | C 1X2 Brier | A RPS | C RPS | OU Brier A/C | AH Brier A/C | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| 德甲 | 306 | 3.0395 | 3.0775 | 3.0411 | 0.294 | 0.278 | 0.275 | 0.5621 | 0.5633 | 0.1900 | 0.1905 | 0.2240/0.2264 | 0.2029/0.2020 | SHADOW |
| 意甲 | 380 | 2.7399 | 3.8555 | 2.7425 | 0.363 | 0.300 | 0.363 | 0.5837 | 0.5837 | 0.1965 | 0.1965 | 0.2547/0.2547 | 0.2027/0.2027 | SHADOW |
| 欧冠 | 281 | 3.0969 | 3.2478 | 3.0875 | 0.278 | 0.249 | 0.281 | 0.5255 | 0.5259 | 0.1880 | 0.1882 | 0.2251/0.2254 | 0.2099/0.2082 | ACTIVE |
| 欧协联 | 409 | 2.8734 | 3.0408 | 2.8717 | 0.333 | 0.298 | 0.328 | 0.5677 | 0.5668 | 0.1978 | 0.1974 | 0.2503/0.2494 | 0.2112/0.2101 | SHADOW |
| 欧罗巴 | 271 | 2.8514 | 3.0326 | 2.8515 | 0.328 | 0.292 | 0.317 | 0.5461 | 0.5472 | 0.1945 | 0.1951 | 0.2475/0.2463 | 0.2028/0.2033 | SHADOW |
| 法甲 | 306 | 3.0142 | 3.0458 | 3.0125 | 0.314 | 0.268 | 0.301 | 0.5816 | 0.5829 | 0.2001 | 0.2006 | 0.2353/0.2359 | 0.2080/0.2066 | SHADOW |
| 英超 | 380 | 2.8644 | 3.0097 | 2.8669 | 0.339 | 0.295 | 0.334 | 0.6082 | 0.6079 | 0.2044 | 0.2043 | 0.2432/0.2430 | 0.2098/0.2092 | SHADOW |
| 西甲 | 380 | 2.7627 | 2.8263 | 2.7661 | 0.413 | 0.361 | 0.411 | 0.5701 | 0.5702 | 0.1952 | 0.1953 | 0.2391/0.2395 | 0.1993/0.1987 | SHADOW |

### Overall common-sample weighted metrics

| Period | Model | N | Score NLL | Top1 | Top3 | 1X2 Brier | RPS | OU Brier | AH Brier |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| validation | A | 2583 | 2.9010 | 0.125 | 0.329 | 0.5619 | 0.1935 | 0.2405 | 0.2062 |
| validation | B | 2583 | 3.1994 | 0.099 | 0.282 | 0.6250 | 0.2220 | 0.2485 | 0.2280 |
| validation | C | 2583 | 2.9036 | 0.123 | 0.327 | 0.5629 | 0.1940 | 0.2406 | 0.2062 |
| test | A | 2713 | 2.8935 | 0.119 | 0.337 | 0.5704 | 0.1962 | 0.2408 | 0.2059 |
| test | B | 2713 | 3.1458 | 0.111 | 0.295 | 0.6215 | 0.2180 | 0.2478 | 0.2208 |
| test | C | 2713 | 2.8935 | 0.123 | 0.330 | 0.5706 | 0.1964 | 0.2409 | 0.2052 |

Activation gate is score-task aligned and frozen before final status assignment: interior Train calibration; `C score NLL <= A` in both OOS seasons; Top3 may not deteriorate by >1 percentage point in either season; 1X2 Brier/RPS/OU/AH Brier may not deteriorate by >0.005 absolute in either season. This gate leaves only **欧冠 ACTIVE**.

## Paired OOS Audit

- 德甲 — validation ΔNLL(C−A)=+0.00040, bootstrap95=[-0.01952,+0.01602]; test +0.00156 [-0.01087,+0.01376].
- 意甲 — validation +0.00341 [+0.00122,+0.00547]; test +0.00260 [+0.00072,+0.00438].
- 欧冠 — validation -0.00137 [-0.00736,+0.00373]; test -0.00948 [-0.02298,+0.00065].
- 欧协联 — validation -0.00129 [-0.00637,+0.00422]; test -0.00170 [-0.01010,+0.00534].
- 欧罗巴 — validation +0.00509 [-0.00168,+0.01138]; test +0.00010 [-0.00718,+0.00725].
- 法甲 — validation +0.00252 [-0.00774,+0.01319]; test -0.00164 [-0.01152,+0.00814].
- 英超 — validation +0.00346 [-0.00036,+0.00698]; test +0.00255 [-0.00046,+0.00547].
- 西甲 — validation +0.00682 [+0.00124,+0.01233]; test +0.00334 [-0.00112,+0.00772].

## Case Studies

Actual results below are post-hoc validation only; never inputs to pre-match calculations.

- 德甲 `2799407` 拜仁慕尼黑 vs RB莱比锡, actual 6-0. Prior λ 2.401/1.280; market 3.159/0.935; posterior 3.040/1.035; C Top3 3-1 / 2-1 / 3-0.
- 意甲 `2784485` 热那亚 vs 莱切, actual 0-0. Prior λ 1.217/0.704; market 1.512/0.711; posterior 1.512/0.711; C Top3 1-0 / 1-1 / 2-0.
- 欧冠 `2788747` 古比斯 vs 米沙米, actual 1-0. Prior λ 1.641/1.256; market 2.454/0.711; posterior 2.426/0.726; C Top3 2-0 / 3-0 / 1-0.
- 欧协联 `2789523` 乔瑟芬FC vs 克里夫顿维尔, actual 2-2. Prior λ 1.513/1.128; market 1.492/0.904; posterior 1.492/0.918; C Top3 1-0 / 1-1 / 2-0.
- 欧罗巴 `2788775` 沙巴巴库 vs 采列, actual 2-3. Prior λ 1.630/1.128; market 1.423/1.199; posterior 1.430/1.191; C Top3 1-1 / 1-0 / 2-1.
- 法甲 `2800027` 雷恩 vs 马赛, actual 1-0. Prior λ 1.568/1.605; market 1.183/1.777; posterior 1.296/1.760; C Top3 1-1 / 1-2 / 0-2.
- 英超 `2789129` 利物浦 vs 伯恩茅斯, actual 4-2. Prior λ 1.702/1.297; market 2.712/0.900; posterior 2.646/0.917; C Top3 2-0 / 2-1 / 3-0.
- 西甲 `2804299` 赫罗纳 vs 巴列卡诺, actual 1-3. Prior λ 1.556/1.007; market 1.266/1.081; posterior 1.312/1.061; C Top3 1-1 / 1-0 / 0-0.

The historical raw database has no archived formal MODEL_1 execution ticket for those fixtures, so the AH execution hard gate is not retroactively fabricated in case studies. The hard gate is tested independently.

## AH × Scoreline / OU execution semantics

- Raw posterior score mass is preserved.
- Final displayed Top3 passes through the formal execution filter. For a formal favorite `-1`, push-only scores such as 1-0 / 2-1 / 3-2 are ineligible; for `-1.75`, 2-1 is ineligible.
- OU remains auxiliary score consistency; it does not mutate posterior lambda or reverse the formal ticket.

## Limitations

- Historical market validation uses Titan closing snapshots, not a complete timestamped intraday lifecycle.
- The raw database contains only the eight audited competitions; no claim is made for competitions absent from this SQLite.
- Four competitions still seek a hyperparameter-grid boundary after extension and therefore remain SHADOW regardless of point-estimate OOS improvement.
- `ACTIVE` does not mean statistical proof of superiority on every metric. For 欧冠, paired bootstrap intervals for ΔNLL still overlap zero; activation reflects consistent directional correct-score NLL improvement plus secondary-market non-inferiority within the frozen gate.
- Future seasons are new OOS evidence; 2025-26 must not be reused for retuning frozen hyperparameters.

## Production Decision

- `欧冠 = ACTIVE`.
- `英超 / 西甲 / 意甲 / 德甲 / 法甲 / 欧罗巴 / 欧协联 = SHADOW`.
- `BAYESIAN_PRIOR_REQUIRED` remains. A SHADOW competition cannot silently use market lambda as a prior.
- Runtime store uses split competition JSON files with sparse precision matrices and fixture-level covariance solves; the 1.47 GB raw SQLite is not committed.
