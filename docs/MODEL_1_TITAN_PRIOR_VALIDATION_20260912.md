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

## Domestic Prior V2

This section supersedes the domestic V1 results above; the three European models and their gates remain frozen.

### Protocol and provenance

- Mother SQLite SHA256: `cb409b3ceb882491671c08abbf6815fdfbaa398010de0377ad1d7bcf0d1531a7`; **13,090 raw matches**. Only five domestic competitions were refitted.
- Train: 2021-22 through 2023-24. Inner season-forward evaluation: 2022-23 and 2023-24. Validation: 2024-25; Test: 2025-26. No random split.
- The selected structure, half-life, team SD, transition SD, rho, process covariance and phase-specific kappa were frozen and hashed before constructing outer OOS records. No selection was revised after observing Test.
- Search compares monthly Laplace random-walk filtering and rolling 30/60/90-day refits. All candidates refresh at month start using strictly earlier results. Rolling windows use the previous-season posterior as their anchor, not the overlapping previous rolling window.
- Attack/defence are jointly opponent-adjusted. Competition baseline/HFA, full Laplace parameter covariance, previous-season transitions, and hierarchical shrinkage are retained. A new team uses the Train-estimated domestic entrant class when six historical entrant team-seasons exist; otherwise competition mean plus current-season evidence.
- Train selection minimizes conditional Dixon–Coles correct-score predictive NLL; Top3, 1X2 Brier and RPS are recorded for each candidate and constrained at release. The search uses two deterministic coordinate passes per structure, not an exhaustive global optimum claim.
- Rho is fitted on first Train inner-OOS scores, its shrinkage factor is selected by the second Train season, then its estimate is refit on pooled Train inner-OOS records. A selected zero is evidence-driven shrinkage, not hard-coded rho=0. Rho bounds [-0.16, 0.027] guarantee positive DC cells over the existing runtime lambda support [0.05, 6].
- Process covariance is the positive-semidefinite projection of Train inner-OOS log-rate residual second moments after subtracting Poisson and Laplace uncertainty. Effective prior covariance is `kappa * (Laplace + process)`; symmetric/PD checks apply. Kappa is fitted separately for opening and closing with full lognormal predictive NLL; it never modifies the prior mean.
- A uses the existing correlated Pinnacle/Bet365/Macau market reconstruction. C uses its Bayesian normal update with the historical prior. B uses historical Laplace + process uncertainty without phase-specific market trust scaling, so B is identical on equal opening/closing samples.
- Full lognormal integration uses deterministic 12×12 Gauss–Hermite nodes and the existing [0.05, 6] lambda support. A 24×24 C audit is included below; runtime retains its existing Monte Carlo predictive integrator. No manual prior/market weights are introduced.
- Opening 1X2/OU and closing 1X2/OU are loaded independently. AH evaluation uses the corresponding archived phase-specific core-book line and five-outcome settlement-equivalent calibration. Opening/closing archives are not synchronized timestamped intraday observations; no intraday decay policy is claimed.
- Gate uses the intersection of the old policy/report: C NLL <= A in **both** Validation/Test; Top3 harm <= 1 pp; no 1X2 Brier or RPS deterioration; OU/AH Brier harm <= 0.005; at least 80 common samples per period; no unresolved Train boundary. SHADOW blocks formal Stage14, including explicit SHADOW packets. Raw posterior mass and existing AH execution hard gate are unchanged.
- All Train grid boundaries stay visible. They were not extended or retuned after Test. No league is activated simply because its point estimate improves in one period.

### Test comparison

| Competition | Open A NLL | Open C NLL | Close A NLL | Close C NLL | Top3 open A/C | Top3 close A/C | ΔNLL open/close | bootstrap CI open / close | activation |
|---|---:|---:|---:|---:|---|---|---|---|---|
| 英超 | 2.870518 | 2.873864 | 2.864379 | 2.868232 | 34.211%/30.526% | 33.947%/32.368% | +0.003346/+0.003853 | [-0.006343, +0.012987] / [-0.005246, +0.012705] | SHADOW |
| 西甲 | 2.767499 | 2.769967 | 2.762750 | 2.765473 | 40.000%/38.947% | 41.316%/39.737% | +0.002468/+0.002723 | [-0.004395, +0.009293] / [-0.004745, +0.010141] | SHADOW |
| 意甲 | 2.746523 | 2.746047 | 2.739903 | 2.741519 | 37.368%/35.000% | 36.316%/35.263% | -0.000477/+0.001615 | [-0.007674, +0.006516] / [-0.006973, +0.010095] | SHADOW |
| 德甲 | 3.044512 | 3.047164 | 3.039508 | 3.040536 | 30.392%/29.739% | 29.412%/29.085% | +0.002652/+0.001028 | [-0.005611, +0.010503] / [-0.005689, +0.007242] | SHADOW |
| 法甲 | 3.019951 | 3.021223 | 3.014175 | 3.008473 | 29.085%/31.046% | 31.373%/31.699% | +0.001272/-0.005702 | [-0.007081, +0.009746] / [-0.011953, +0.000492] | SHADOW |

### 英超

- Selected state: **monthly**; half-life **365 days**; team SD **0.35**; transition SD **0.08**.
- Historical rho **0.00000000**; Train forward shrinkage **0**; searched **89** candidate settings; unresolved boundaries: `[]`.
- Process covariance: `[[0.008389454794912347, -0.01262199684095501], [-0.01262199684095501, 0.01898988768014964]]`.
- Kappa opening **0.691733**, closing **1.352573**; trust boundaries opening/closing: `False/False`.
- Promoted/new entrant class: `{"status": "ESTIMATED", "mean": [-0.13545956587385727, -0.19381168679272212], "covariance": [[0.04625999902586396, 0.013631383629633695], [0.013631383629633695, 0.05396858229178283]], "n": 6, "scope": "TRAIN_DOMESTIC_ENTRANTS_ONLY"}`.
- Frozen Train SHA256: `2648f584e0788a2480b068c236274638218ddb5ecc857999df60a91408b4d1b3`.

| Period | Phase | Model | N | Score NLL | Top1 | Top3 | 1X2 Brier | RPS | OU Brier | OU logloss | OU ECE | AH Brier | AH ECE |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| validation | opening | A | 380 | 2.963995 | 0.115789 | 0.323684 | 0.586852 | 0.201002 | 0.244350 | 0.681773 | 0.047627 | 0.124321 | 0.035313 |
| validation | opening | B | 380 | 2.988438 | 0.121053 | 0.310526 | 0.593689 | 0.204930 | 0.242787 | 0.678443 | 0.039100 | 0.127831 | 0.050091 |
| validation | opening | C | 380 | 2.964186 | 0.126316 | 0.323684 | 0.586531 | 0.200870 | 0.243138 | 0.679234 | 0.039737 | 0.124377 | 0.053437 |
| validation | closing | A | 380 | 2.943498 | 0.147368 | 0.321053 | 0.576042 | 0.196268 | 0.242941 | 0.678933 | 0.049059 | 0.121927 | 0.034283 |
| validation | closing | B | 380 | 2.988438 | 0.121053 | 0.310526 | 0.593689 | 0.204930 | 0.242787 | 0.678443 | 0.039100 | 0.127715 | 0.045703 |
| validation | closing | C | 380 | 2.945220 | 0.128947 | 0.315789 | 0.577173 | 0.196614 | 0.242297 | 0.677511 | 0.037382 | 0.122146 | 0.031988 |
| test | opening | A | 380 | 2.870518 | 0.128947 | 0.342105 | 0.611346 | 0.205809 | 0.245834 | 0.684897 | 0.017437 | 0.135689 | 0.033825 |
| test | opening | B | 380 | 2.912573 | 0.115789 | 0.307895 | 0.624637 | 0.211670 | 0.253374 | 0.700243 | 0.070120 | 0.139369 | 0.061853 |
| test | opening | C | 380 | 2.873864 | 0.139474 | 0.305263 | 0.612589 | 0.205879 | 0.246989 | 0.687264 | 0.027004 | 0.135640 | 0.030807 |
| test | closing | A | 380 | 2.864379 | 0.123684 | 0.339474 | 0.608156 | 0.204418 | 0.243187 | 0.679524 | 0.045556 | 0.136567 | 0.038769 |
| test | closing | B | 380 | 2.912573 | 0.115789 | 0.307895 | 0.624637 | 0.211670 | 0.253374 | 0.700243 | 0.070120 | 0.141430 | 0.073205 |
| test | closing | C | 380 | 2.868232 | 0.115789 | 0.323684 | 0.609508 | 0.204566 | 0.244126 | 0.681458 | 0.035840 | 0.136442 | 0.043046 |

| Period | Phase | Mean C−A NLL | Median C−A NLL | Paired bootstrap 95% CI | C higher actual-score probability |
|---|---|---:|---:|---|---:|
| validation | opening | +0.000191 | +0.008863 | [-0.008965, +0.009045] | 42.895% |
| validation | closing | +0.001721 | +0.012017 | [-0.007649, +0.010749] | 38.421% |
| test | opening | +0.003346 | +0.016879 | [-0.006343, +0.012987] | 39.474% |
| test | closing | +0.003853 | +0.012491 | [-0.005246, +0.012705] | 36.316% |

- **opening status: SHADOW**. Reasons: validation:SCORE_NLL_WORSE, test:SCORE_NLL_WORSE, test:TOP3_HARM, test:1X2_Brier_HARM, test:RPS_HARM.

- **closing status: SHADOW**. Reasons: validation:SCORE_NLL_WORSE, validation:1X2_Brier_HARM, validation:RPS_HARM, test:SCORE_NLL_WORSE, test:TOP3_HARM, test:1X2_Brier_HARM, test:RPS_HARM.
- **Final activation: SHADOW**.

### 西甲

- Selected state: **monthly**; half-life **730 days**; team SD **0.25**; transition SD **0.08**.
- Historical rho **0.00000000**; Train forward shrinkage **0**; searched **100** candidate settings; unresolved boundaries: `['half_life_days']`.
- Process covariance: `[[0.0028395509297324223, 0.0017666034043926498], [0.00176660340439265, 0.0010990778702834499]]`.
- Kappa opening **2.016727**, closing **4.041826**; trust boundaries opening/closing: `False/False`.
- Promoted/new entrant class: `{"status": "ESTIMATED", "mean": [-0.07045944251024205, -0.12502814844827786], "covariance": [[0.06731826775409132, -0.0011139705714197721], [-0.0011139705714197721, 0.06074786969115213]], "n": 6, "scope": "TRAIN_DOMESTIC_ENTRANTS_ONLY"}`.
- Frozen Train SHA256: `9f396576c0388c8eb3a49dc045251b6bbbb768e9932ff4615541a5aa8495c590`.

| Period | Phase | Model | N | Score NLL | Top1 | Top3 | 1X2 Brier | RPS | OU Brier | OU logloss | OU ECE | AH Brier | AH ECE |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| validation | opening | A | 380 | 2.743966 | 0.147368 | 0.381579 | 0.566208 | 0.190794 | 0.237493 | 0.667707 | 0.020764 | 0.119669 | 0.046969 |
| validation | opening | B | 380 | 2.786168 | 0.121053 | 0.402632 | 0.583688 | 0.197735 | 0.240841 | 0.675168 | 0.078648 | 0.125022 | 0.043133 |
| validation | opening | C | 380 | 2.746446 | 0.150000 | 0.397368 | 0.568551 | 0.191540 | 0.237261 | 0.667235 | 0.006597 | 0.120387 | 0.038849 |
| validation | closing | A | 380 | 2.724877 | 0.131579 | 0.405263 | 0.558239 | 0.186943 | 0.234002 | 0.660690 | 0.047233 | 0.117403 | 0.040024 |
| validation | closing | B | 380 | 2.786168 | 0.121053 | 0.402632 | 0.583688 | 0.197735 | 0.240841 | 0.675168 | 0.078648 | 0.123936 | 0.041706 |
| validation | closing | C | 380 | 2.724846 | 0.165789 | 0.413158 | 0.559797 | 0.187454 | 0.233965 | 0.660589 | 0.029403 | 0.117830 | 0.041642 |
| test | opening | A | 380 | 2.767499 | 0.168421 | 0.400000 | 0.569720 | 0.195621 | 0.243137 | 0.679689 | 0.013227 | 0.127253 | 0.032224 |
| test | opening | B | 380 | 2.800796 | 0.171053 | 0.363158 | 0.584431 | 0.201626 | 0.243040 | 0.678565 | 0.047027 | 0.130315 | 0.048959 |
| test | opening | C | 380 | 2.769967 | 0.184211 | 0.389474 | 0.571796 | 0.196196 | 0.242700 | 0.678631 | 0.013716 | 0.127563 | 0.033514 |
| test | closing | A | 380 | 2.762750 | 0.163158 | 0.413158 | 0.570108 | 0.195180 | 0.239082 | 0.670888 | 0.029045 | 0.134151 | 0.037717 |
| test | closing | B | 380 | 2.800796 | 0.171053 | 0.363158 | 0.584431 | 0.201626 | 0.243040 | 0.678565 | 0.047027 | 0.138377 | 0.043613 |
| test | closing | C | 380 | 2.765473 | 0.173684 | 0.397368 | 0.571194 | 0.195478 | 0.238998 | 0.670653 | 0.029944 | 0.134570 | 0.044572 |

| Period | Phase | Mean C−A NLL | Median C−A NLL | Paired bootstrap 95% CI | C higher actual-score probability |
|---|---|---:|---:|---|---:|
| validation | opening | +0.002480 | +0.011065 | [-0.003960, +0.009086] | 38.947% |
| validation | closing | -0.000031 | +0.010349 | [-0.006875, +0.007126] | 40.526% |
| test | opening | +0.002468 | +0.011571 | [-0.004395, +0.009293] | 37.895% |
| test | closing | +0.002723 | +0.009275 | [-0.004745, +0.010141] | 36.053% |

- **opening status: SHADOW**. Reasons: UNRESOLVED_TRAIN_BOUNDARY, validation:SCORE_NLL_WORSE, validation:1X2_Brier_HARM, validation:RPS_HARM, test:SCORE_NLL_WORSE, test:TOP3_HARM, test:1X2_Brier_HARM, test:RPS_HARM.

- **closing status: SHADOW**. Reasons: UNRESOLVED_TRAIN_BOUNDARY, validation:1X2_Brier_HARM, validation:RPS_HARM, test:SCORE_NLL_WORSE, test:TOP3_HARM, test:1X2_Brier_HARM, test:RPS_HARM.
- **Final activation: SHADOW**.

### 意甲

- Selected state: **monthly**; half-life **730 days**; team SD **0.25**; transition SD **0.08**.
- Historical rho **-0.00000000**; Train forward shrinkage **0**; searched **100** candidate settings; unresolved boundaries: `['half_life_days']`.
- Process covariance: `[[0.0, 0.0], [0.0, 0.0]]`.
- Kappa opening **1.154464**, closing **993.787350**; trust boundaries opening/closing: `False/True`.
- Promoted/new entrant class: `{"status": "ESTIMATED", "mean": [-0.07208574911933349, -0.07140628792090054], "covariance": [[0.05025177191736663, 0.0019935793372770406], [0.0019935793372770406, 0.059925662533548744]], "n": 6, "scope": "TRAIN_DOMESTIC_ENTRANTS_ONLY"}`.
- Frozen Train SHA256: `f2b322eee9662fcc033785fabdb945f8c9e668e68b56f00b5fd3e31bb900e497`.

| Period | Phase | Model | N | Score NLL | Top1 | Top3 | 1X2 Brier | RPS | OU Brier | OU logloss | OU ECE | AH Brier | AH ECE |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| validation | opening | A | 380 | 2.758251 | 0.136842 | 0.394737 | 0.570215 | 0.184446 | 0.246358 | 0.685811 | 0.043043 | 0.106284 | 0.058041 |
| validation | opening | B | 380 | 2.807105 | 0.160526 | 0.350000 | 0.591162 | 0.194066 | 0.252796 | 0.698870 | 0.082056 | 0.111789 | 0.056255 |
| validation | opening | C | 380 | 2.762961 | 0.152632 | 0.381579 | 0.573688 | 0.185838 | 0.247167 | 0.687419 | 0.031035 | 0.107246 | 0.052479 |
| validation | closing | A | 380 | 2.739175 | 0.173684 | 0.394737 | 0.567209 | 0.183889 | 0.241868 | 0.676776 | 0.041902 | 0.109857 | 0.043880 |
| validation | closing | B | 380 | 2.807105 | 0.160526 | 0.350000 | 0.591162 | 0.194066 | 0.252796 | 0.698870 | 0.082056 | 0.113877 | 0.054816 |
| validation | closing | C | 380 | 2.740744 | 0.165789 | 0.381579 | 0.569271 | 0.184278 | 0.241896 | 0.676839 | 0.054413 | 0.109987 | 0.043370 |
| test | opening | A | 380 | 2.746523 | 0.126316 | 0.373684 | 0.583537 | 0.196429 | 0.254250 | 0.702021 | 0.068897 | 0.121814 | 0.042999 |
| test | opening | B | 380 | 2.768635 | 0.113158 | 0.342105 | 0.597067 | 0.202499 | 0.251883 | 0.697372 | 0.044362 | 0.127361 | 0.051775 |
| test | opening | C | 380 | 2.746047 | 0.155263 | 0.350000 | 0.585480 | 0.197020 | 0.253266 | 0.700000 | 0.055463 | 0.122723 | 0.043015 |
| test | closing | A | 380 | 2.739903 | 0.123684 | 0.363158 | 0.583707 | 0.196511 | 0.254669 | 0.703083 | 0.073537 | 0.117907 | 0.052319 |
| test | closing | B | 380 | 2.768635 | 0.113158 | 0.342105 | 0.597067 | 0.202499 | 0.251883 | 0.697372 | 0.044362 | 0.123886 | 0.047043 |
| test | closing | C | 380 | 2.741519 | 0.142105 | 0.352632 | 0.585194 | 0.196757 | 0.254596 | 0.702892 | 0.083382 | 0.118338 | 0.056730 |

| Period | Phase | Mean C−A NLL | Median C−A NLL | Paired bootstrap 95% CI | C higher actual-score probability |
|---|---|---:|---:|---|---:|
| validation | opening | +0.004709 | +0.017512 | [-0.002728, +0.012184] | 36.316% |
| validation | closing | +0.001570 | +0.009032 | [-0.006902, +0.009943] | 36.316% |
| test | opening | -0.000477 | +0.009442 | [-0.007674, +0.006516] | 40.789% |
| test | closing | +0.001615 | +0.006097 | [-0.006973, +0.010095] | 41.316% |

- **opening status: SHADOW**. Reasons: UNRESOLVED_TRAIN_BOUNDARY, validation:SCORE_NLL_WORSE, validation:TOP3_HARM, validation:1X2_Brier_HARM, validation:RPS_HARM, test:TOP3_HARM, test:1X2_Brier_HARM, test:RPS_HARM.

- **closing status: SHADOW**. Reasons: UNRESOLVED_TRAIN_BOUNDARY, validation:SCORE_NLL_WORSE, validation:TOP3_HARM, validation:1X2_Brier_HARM, validation:RPS_HARM, test:SCORE_NLL_WORSE, test:TOP3_HARM, test:1X2_Brier_HARM, test:RPS_HARM.
- **Final activation: SHADOW**.

### 德甲

- Selected state: **monthly**; half-life **730 days**; team SD **0.25**; transition SD **0.03**.
- Historical rho **-0.13089780**; Train forward shrinkage **1**; searched **100** candidate settings; unresolved boundaries: `['half_life_days', 'transition_sd']`.
- Process covariance: `[[0.031334298702984716, -0.01860186127908764], [-0.018601861279087643, 0.01104314624451638]]`.
- Kappa opening **15.572585**, closing **5.999064**; trust boundaries opening/closing: `False/False`.
- Promoted/new entrant class: `{"status": "FALLBACK", "mean": [0.0, 0.0], "n": 4, "reason": "FEWER_THAN_SIX_TRAIN_ENTRANTS"}`.
- Frozen Train SHA256: `44f26b724ae5b6c998280173db22d52553b2c7c46c60c44c877f3442b59ccbf7`.

| Period | Phase | Model | N | Score NLL | Top1 | Top3 | 1X2 Brier | RPS | OU Brier | OU logloss | OU ECE | AH Brier | AH ECE |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| validation | opening | A | 306 | 3.117386 | 0.081699 | 0.245098 | 0.599778 | 0.206025 | 0.232672 | 0.658015 | 0.032432 | 0.135486 | 0.066602 |
| validation | opening | B | 306 | 3.120111 | 0.078431 | 0.225490 | 0.616767 | 0.214760 | 0.229062 | 0.649857 | 0.033221 | 0.144042 | 0.081030 |
| validation | opening | C | 306 | 3.110110 | 0.081699 | 0.232026 | 0.598700 | 0.205829 | 0.232583 | 0.657752 | 0.032940 | 0.135600 | 0.066957 |
| validation | closing | A | 306 | 3.077933 | 0.091503 | 0.241830 | 0.591360 | 0.202231 | 0.223300 | 0.637323 | 0.068639 | 0.135451 | 0.066035 |
| validation | closing | B | 306 | 3.120111 | 0.078431 | 0.225490 | 0.616767 | 0.214760 | 0.229062 | 0.649857 | 0.033221 | 0.144734 | 0.082299 |
| validation | closing | C | 306 | 3.073576 | 0.098039 | 0.235294 | 0.590781 | 0.202286 | 0.223869 | 0.638488 | 0.092484 | 0.135698 | 0.064018 |
| test | opening | A | 306 | 3.044512 | 0.111111 | 0.303922 | 0.566124 | 0.191930 | 0.223886 | 0.637821 | 0.033528 | 0.126285 | 0.043004 |
| test | opening | B | 306 | 3.083193 | 0.114379 | 0.277778 | 0.586822 | 0.201582 | 0.229419 | 0.650311 | 0.071579 | 0.131530 | 0.072314 |
| test | opening | C | 306 | 3.047164 | 0.120915 | 0.297386 | 0.565659 | 0.191868 | 0.224046 | 0.638177 | 0.050527 | 0.126475 | 0.040798 |
| test | closing | A | 306 | 3.039508 | 0.098039 | 0.294118 | 0.562110 | 0.190022 | 0.223974 | 0.638071 | 0.035738 | 0.118930 | 0.063502 |
| test | closing | B | 306 | 3.083193 | 0.114379 | 0.277778 | 0.586822 | 0.201582 | 0.229419 | 0.650311 | 0.071579 | 0.127113 | 0.077402 |
| test | closing | C | 306 | 3.040536 | 0.101307 | 0.290850 | 0.562989 | 0.190356 | 0.224009 | 0.638138 | 0.025782 | 0.119254 | 0.059957 |

| Period | Phase | Mean C−A NLL | Median C−A NLL | Paired bootstrap 95% CI | C higher actual-score probability |
|---|---|---:|---:|---|---:|
| validation | opening | -0.007276 | +0.009594 | [-0.029575, +0.007275] | 38.235% |
| validation | closing | -0.004357 | +0.006713 | [-0.021188, +0.007525] | 37.908% |
| test | opening | +0.002652 | +0.010149 | [-0.005611, +0.010503] | 38.562% |
| test | closing | +0.001028 | +0.011862 | [-0.005689, +0.007242] | 37.582% |

- **opening status: SHADOW**. Reasons: UNRESOLVED_TRAIN_BOUNDARY, validation:TOP3_HARM, test:SCORE_NLL_WORSE.

- **closing status: SHADOW**. Reasons: UNRESOLVED_TRAIN_BOUNDARY, validation:RPS_HARM, test:SCORE_NLL_WORSE, test:1X2_Brier_HARM, test:RPS_HARM.
- **Final activation: SHADOW**.

### 法甲

- Selected state: **rolling90**; half-life **365 days**; team SD **0.25**; transition SD **0.08**.
- Historical rho **-0.07862571**; Train forward shrinkage **1**; searched **88** candidate settings; unresolved boundaries: `[]`.
- Process covariance: `[[0.00035411969658861894, 0.001759378299656755], [0.001759378299656755, 0.00874114609021321]]`.
- Kappa opening **0.923642**, closing **2.382007**; trust boundaries opening/closing: `False/False`.
- Promoted/new entrant class: `{"status": "FALLBACK", "mean": [0.0, 0.0], "n": 5, "reason": "FEWER_THAN_SIX_TRAIN_ENTRANTS"}`.
- Frozen Train SHA256: `2204929d0691658724eb64f335ca79fad5c15b7860d4742bdda0773596b444ec`.

| Period | Phase | Model | N | Score NLL | Top1 | Top3 | 1X2 Brier | RPS | OU Brier | OU logloss | OU ECE | AH Brier | AH ECE |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| validation | opening | A | 306 | 2.983793 | 0.101307 | 0.300654 | 0.567573 | 0.203396 | 0.239147 | 0.670917 | 0.017508 | 0.139686 | 0.033517 |
| validation | opening | B | 306 | 3.033478 | 0.094771 | 0.264706 | 0.588975 | 0.212913 | 0.245073 | 0.683469 | 0.027951 | 0.140736 | 0.030602 |
| validation | opening | C | 306 | 2.986996 | 0.094771 | 0.297386 | 0.569798 | 0.203981 | 0.239286 | 0.671245 | 0.029432 | 0.138845 | 0.037760 |
| validation | closing | A | 306 | 2.965325 | 0.088235 | 0.294118 | 0.564240 | 0.201176 | 0.237997 | 0.668786 | 0.030005 | 0.136116 | 0.051276 |
| validation | closing | B | 306 | 3.033478 | 0.094771 | 0.264706 | 0.588975 | 0.212913 | 0.245073 | 0.683469 | 0.027951 | 0.138321 | 0.046145 |
| validation | closing | C | 306 | 2.966275 | 0.098039 | 0.300654 | 0.564050 | 0.201263 | 0.238033 | 0.668832 | 0.030028 | 0.135828 | 0.048339 |
| test | opening | A | 306 | 3.019951 | 0.098039 | 0.290850 | 0.582090 | 0.200291 | 0.240395 | 0.673961 | 0.039884 | 0.136445 | 0.028962 |
| test | opening | B | 306 | 3.067912 | 0.084967 | 0.258170 | 0.607951 | 0.212713 | 0.250403 | 0.694979 | 0.037340 | 0.144740 | 0.055797 |
| test | opening | C | 306 | 3.021223 | 0.101307 | 0.310458 | 0.583361 | 0.201059 | 0.241377 | 0.675929 | 0.050756 | 0.137265 | 0.035354 |
| test | closing | A | 306 | 3.014175 | 0.120915 | 0.313725 | 0.581611 | 0.200131 | 0.235341 | 0.663488 | 0.038114 | 0.140340 | 0.065198 |
| test | closing | B | 306 | 3.067912 | 0.084967 | 0.258170 | 0.607951 | 0.212713 | 0.250403 | 0.694979 | 0.037340 | 0.147785 | 0.051103 |
| test | closing | C | 306 | 3.008473 | 0.111111 | 0.316993 | 0.580699 | 0.200105 | 0.236025 | 0.664879 | 0.042645 | 0.140413 | 0.066358 |

| Period | Phase | Mean C−A NLL | Median C−A NLL | Paired bootstrap 95% CI | C higher actual-score probability |
|---|---|---:|---:|---|---:|
| validation | opening | +0.003203 | +0.013546 | [-0.005267, +0.011707] | 39.869% |
| validation | closing | +0.000950 | +0.011013 | [-0.004652, +0.006374] | 36.928% |
| test | opening | +0.001272 | +0.010035 | [-0.007081, +0.009746] | 42.157% |
| test | closing | -0.005702 | +0.009397 | [-0.011953, +0.000492] | 39.869% |

- **opening status: SHADOW**. Reasons: validation:SCORE_NLL_WORSE, validation:1X2_Brier_HARM, validation:RPS_HARM, test:SCORE_NLL_WORSE, test:1X2_Brier_HARM, test:RPS_HARM.

- **closing status: SHADOW**. Reasons: validation:SCORE_NLL_WORSE, validation:RPS_HARM.
- **Final activation: SHADOW**.

### Numerical replay audit

| Competition | Period | Metric replay max error | 24-node minus 12-node mean C NLL | Max absolute per-match C NLL error |
|---|---|---:|---:|---:|
| 英超 | validation | 0 | -2.97e-10 | 6.68e-08 |
| 英超 | test | 0 | -1.25e-14 | 4.94e-12 |
| 西甲 | validation | 0 | 7.95e-10 | 6.6e-07 |
| 西甲 | test | 0 | 2e-09 | 1.24e-06 |
| 意甲 | validation | 0 | -1.7e-11 | 1.31e-08 |
| 意甲 | test | 0 | -2.76e-15 | 1.77e-12 |
| 德甲 | validation | 0 | -8.2e-08 | 4.73e-05 |
| 德甲 | test | 0 | -4.29e-08 | 2e-05 |
| 法甲 | validation | 0 | -7.26e-11 | 4.19e-08 |
| 法甲 | test | 0 | 8.26e-11 | 3.09e-08 |

### Evidence and limitations

- `docs/data/domestic_prior_v2/` contains every Train search result, the frozen Train certificates, full OOS metrics/calibration bins, and compressed match-level predictions with both market phases. The paired bootstrap uses 5,000 match resamples with seed 20260912. Intervals are not adjusted for within-week/team dependence or multiple comparisons.
- OOS Top1/Top3 above measure the raw predictive distribution. The separate production smoke artifact uses a pregame market-favorite execution path and archived AH magnitude to exercise the formal positive-settlement hard gate; it is a routing/output smoke, not an accuracy re-evaluation.
- Rho, process uncertainty and kappa are estimated from the limited two Train inner-OOS seasons. Train search is finite; boundary winners stay SHADOW and are not evidence of a resolved optimum.
- The historical-prior resolver requires kickoff, rejects a model containing future results, verifies packaged model hashes, and rechecks phase-specific OOS evidence before ACTIVE. `DomesticPriorResolver(store).resolve_prior(competition, season, home_team, away_team, kickoff)` defaults to the conservative closing phase; explicit `snapshot_phase='opening'` is supported. The production score resolver preserves explicit opening/closing metadata and otherwise reports `current`.
- The packaged state includes completed results through May 2026. New results require a new historical-state build with the frozen Train parameters; this package does not scrape live results.
- **All five domestic competitions remain SHADOW.** Test observations above are evaluation evidence only and must not be recycled into parameter tuning. European ACTIVE/SHADOW decisions and frozen parameters are unchanged. The missing legacy full-store chunks are marked as an incomplete archive; the ACTIVE UCL final runtime state is reproducibly rebuilt from the frozen UCL hyperparameters and frozen Train-only process covariance, with its own checked sparse-precision artifact.

## Stage14 production score engine

Stage14 now has three explicit production modes. `AUTO` is the default. An ACTIVE historical prior routes to `HISTORICAL_BAYESIAN`; SHADOW, DISABLED, INSUFFICIENT_HISTORY, or an unavailable historical model routes to `MARKET_ONLY_FORMAL`. Explicit `HISTORICAL_BAYESIAN` calls still fail with `BAYESIAN_PRIOR_REQUIRED` when no approved prior is available. Only an insufficient Pinnacle/Bet365/Macau core cluster may make the AUTO score model missing.

`MARKET_ONLY_FORMAL` uses `build_market_cluster_likelihood()` as one correlated log-rate likelihood and then reuses the same lognormal predictive integration, Dixon-Coles grid, Top10, 1X2/OU derivation, and execution filter as the Bayesian path. It emits `prior_used=false`, keeps `historical_prior=null`, and never labels the market distribution as a historical Bayesian prior. Both modes require strictly positive AH settlement for final Top3 when a formal AH path is supplied; raw score probabilities and lambdas remain unchanged by AH or OU filtering.

The first prior-usefulness gate is conservative. It exposes only pregame covariance, dispersion, reconstruction, phase, season-progress, entrant, prior-distance, sample-size, and uncertainty features. Runtime score/result/Test/JCB/post-kickoff fields are rejected recursively. No final Test target was used to tune the gate; domestic competitions continue to choose the formal market model.

### Real Titan closing-market production smoke

Source: `docs/data/stage14_production_smoke.json`. The artifact contains market packets, fixture metadata, and a kickoff-cutoff UCL prior packet; actual scores/results are excluded. The UCL historical state uses only matches strictly before kickoff. Its AH path is derived from the pregame market favorite and archived AH magnitude solely to exercise the production gate.

| Competition | Match | Mode | Prior | Lambda H/A | Rho | Formal Top3 | AH gate |
|---|---|---|---|---:|---:|---|---|
| 英超 | 2789129 利物浦–伯恩茅斯 | MARKET_ONLY_FORMAL | SHADOW / unused | 2.711574 / 0.900094 | 0.019525 | 2-0, 3-0, 3-1 | positive settlement |
| 西甲 | 2804299 赫罗纳–巴列卡诺 | MARKET_ONLY_FORMAL | SHADOW / unused | 1.266301 / 1.081267 | -0.078846 | 1-0, 2-1, 2-0 | positive settlement |
| 意甲 | 2784485 热那亚–莱切 | MARKET_ONLY_FORMAL | SHADOW / unused | 1.511801 / 0.711160 | -0.106737 | 1-0, 2-0, 2-1 | positive settlement |
| 德甲 | 2799407 拜仁慕尼黑–RB莱比锡 | MARKET_ONLY_FORMAL | SHADOW / unused | 3.159349 / 0.935130 | -0.011591 | 3-0, 4-0, 4-1 | positive settlement |
| 法甲 | 2800027 雷恩–马赛 | MARKET_ONLY_FORMAL | SHADOW / unused | 1.182884 / 1.776509 | -0.128020 | 1-2, 0-2, 0-1 | positive settlement |
| 欧冠 | 2788747 古比斯–米沙米 | HISTORICAL_BAYESIAN | ACTIVE / used | 2.426341 / 0.725655 | -0.078956 | 2-0, 3-0, 3-1 | positive settlement |

Full release validation: **194 passed**.
