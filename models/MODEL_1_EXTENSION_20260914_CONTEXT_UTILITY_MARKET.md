# MODEL_1 targeted extension — Context Utility & Market Distortion

**Effective date:** 2026-09-14  
**Authorization:** explicit targeted user instruction to research and incorporate the six uploaded rules into MODEL_1.  
**Global freeze:** remains active through 2026-10-10 Asia/Shanghai.  
**Fixed numeric weight:** NOT AUTHORIZED.  
**Canonical policy:** `config/model_1_context_utility_market_policy.json`

## Why this extension exists

The six requested ideas are directionally useful, but their raw wording creates a major post-hoc risk:

1. whether the market is "creating cold" or "creating heat";
2. season phase / points urgency / multi-competition priorities / squad depth / dominant leaders conserving resources;
3. operator patterns, odds signals and public betting probability;
4. domestic-home/away x European-home/away schedule combinations;
5. club finances and qualification/advancement bonuses;
6. whether connected clubs or networks may provide reciprocal help at important table nodes.

MODEL_1 therefore does **not** encode these as six free-form narrative bonuses. They are converted into auditable variables, explicit UNKNOWN states and counterfactual tests.

## Research basis

### 1. Market bias exists, but bookmaker intent is not directly observable

Relevant literature finds persistent favourite-longshot, hot-hand and sentiment effects in European football fixed-odds markets. Some work also gives mechanisms by which bookmakers may shade prices in response to bettor demand or adverse selection. However, recent evidence comparing market structures reports that favourite-longshot bias found in 1X2-style betting does not automatically appear in Asian Handicap markets.

Implication for MODEL_1:

- never infer "the bookmaker is deliberately trapping bettors" from a line move alone;
- separate 1X2, AH and OU microstructure;
- separate **observed public demand** from **narrative attraction estimated by the model**;
- if actual ticket/handle percentages are unavailable under the current Titan-only formal-source contract, the field is UNKNOWN rather than estimated as a fake percentage.

Representative research:

- Franke (2019), *Do market participants misprice lottery-type assets? Evidence from the European soccer betting market*, Quarterly Review of Economics and Finance, DOI 10.1016/j.qref.2019.05.016.
- Goto & Yamada (2023), *What drives biased odds in sports betting markets: Bettors' irrationality and the role of bookmakers*, International Review of Economics & Finance, DOI 10.1016/j.iref.2023.03.002.
- Braun & Kvasnicka (2013), *National Sentiment and Economic Behavior: Evidence From Online Betting on European Football*, Journal of Sports Economics, DOI 10.1177/1527002511414718.
- Hegarty & Whelan (2026), *Market structure and prices in online betting markets: theory and evidence*, Oxford Economic Papers.

### 2. "Motivation" should be marginal match importance, not league-table storytelling

A 2025 Journal of Sports Economics paper formalises **Monetary Match Importance (MMI)** as the difference in expected financial award conditional on winning versus losing. EPL incentives can arise from rank payments, UEFA qualification and relegation. Separate European-football research on roughly 25,000 matches finds betting prices differ for clubs whose table position leaves them with little remaining promotion/Europe/relegation incentive, including already-crowned champions and already-relegated teams.

Implication for MODEL_1:

- early/middle/late season is only a descriptor;
- the real variable is the remaining opportunity set and the W/D/L marginal value of the current match;
- "midtable = no motivation" is forbidden;
- a dominant Bayern/PSG-type leader is analysed as **domestic objective saturation + next-match priority + rotation capacity**, not as an automatic point-drop or non-cover rule.

Representative research:

- Cisyk, Courty & Kouhbor (2025), *Are English Premier League Teams Paid Like Bureaucrats? An Incentive Analysis of Monetary Match Importance*, Journal of Sports Economics, DOI 10.1177/15270025251348181.
- *Contest incentives, team effort, and betting market outcomes in European football*, European Sport Management Quarterly, DOI 10.1080/16184742.2021.1898432.

## 3. Congestion is real, but there is no universal "tired team loses" coefficient

Systematic reviews find fixture congestion can raise match-injury incidence, while evidence on performance itself is mixed: total distance is not consistently reduced, and teams may change pacing or tactical behaviour. A 2025 Bundesliga study reports heterogeneous effects across teams/seasons and shows that the identity of the opponent faced under congestion matters.

Implication for MODEL_1:

- encode schedule exposure, selection pressure and rotation/resource allocation rather than subtracting a generic fatigue coefficient;
- preserve the already-validated `post_europe_residual_flag` as its own formal extension;
- do not double-penalise that exposure with generic fatigue;
- the four domestic/European venue quadrants are interaction features only until separately validated;
- sequence must be explicit: PRE_EUROPE and POST_EUROPE are not the same mechanism.

Representative research:

- Julian et al. (2020), *The Effect of Fixture Congestion on Performance During Professional Male Soccer Match-Play: A Systematic Critical Review with Meta-Analysis*, Sports Medicine, DOI 10.1007/s40279-020-01359-9.
- Page et al. (2022/2023), *The Effects of Fixture Congestion on Injury in Professional Male Soccer: A Systematic Review*, Sports Medicine, DOI 10.1007/s40279-022-01799-5.
- Stüttgen (2025), *The Impact of Scheduling and Match Congestion on Team Performance in Professional Soccer*, Journal of Sports Economics, DOI 10.1177/15270025251369423.

## 4. Financial incentives must be marginal and season-specific

Nominal prize money is not itself a performance coefficient. A €2m marginal reward can have very different utility for a giant club and a cash-constrained smaller club; sporting prestige and future qualification value may dominate the immediate cash payment.

UEFA's 2026/27 competition regulations establish competition-revenue distribution rules and state that season-specific available amounts are communicated by circular. Therefore MODEL_1 must use the current official season's regulations/circular where possible and must not carry stale prize values from one season into another.

Implication for MODEL_1:

- estimate the **change in expected award under W/D/L**, not the total competition purse;
- keep `sporting_marginal_value` and `financial_marginal_value` separable;
- verified liquidity stress, wage arrears, sanctions, bonuses or ownership constraints may alter the utility of cash, but rumours remain non-formal.

## 5. Relationship networks are integrity context, not proof of a fixed result

UEFA's current Article 5 multi-club ownership rules explicitly restrict control/influence across clubs in UEFA competitions to protect competition integrity. This supports monitoring common control as a legitimate integrity variable. It does **not** establish that related clubs coordinate a particular match result.

Implication for MODEL_1:

- replace "派系送温暖" with `relationship_integrity_risk`;
- record ownership/control, directors, management/agent networks, repeated loans/transfers, academy/satellite and documented commercial/local ties;
- keep relationship evidence and coordination evidence separate;
- historical head-to-head anomalies or asymmetric points need cannot prove reciprocity;
- any live reciprocity hypothesis must be challenged by a non-coordination explanation in Red Team H2.

Current rule reference: UEFA club competition regulations 2026/27, Article 5 — Integrity of the competition / multi-club ownership.

## Formal placement inside the frozen 18-stage MODEL_1

No stage order changes.

### Stage 1 — Fundamentals

Add structured outputs:

- `competitive_incentive_state`
- `schedule_priority_resource_allocation`

Required thought process:

1. identify each realistic sporting endpoint;
2. evaluate how W/D/L changes access to that endpoint;
3. compare current-match importance with the previous and next high-priority match;
4. separate rotation propensity from rotation cost (deep squad = easier rotation, not necessarily worse result);
5. avoid duplicate use of the formal post-Europe residual extension.

### Stage 5 — Off-field / weather

Add structured outputs:

- `financial_marginal_match_value`
- `relationship_integrity_risk`

The existing relationship module remains active, but this extension adds evidence tiers and a strict firewall between relationship and coordination.

### Stage 11 — Market attraction

Add structured outputs:

- `price_popularity_distortion`
- `bookmaker_pattern_audit`

The word **public** may be used as an observed-data label only when genuine bet-share data are available from an authorised source. Under the current Titan-only formal market-source contract, external ticket/handle percentages are shadow context only.

### Stage 17 — Red Team H2

Mandatory challenges:

- provide a non-intent explanation for every claimed heat/cold market state;
- test whether motivation information was already priced in;
- test deep-squad/opponent-quality counterexamples to schedule claims;
- test cash-versus-prestige alternatives to financial narratives;
- provide the strongest non-coordination explanation for every club-relationship hypothesis.

## Execution labels

### Price / popularity

- `POPULARITY_AND_PRICE_SUPPORT_ALIGNED`
- `POPULARITY_HIGH_PRICE_RESISTS`
- `LOW_NARRATIVE_ATTRACTION_PRICE_STRENGTHENS`
- `PRICE_MOVE_WITHOUT_DEMAND_EVIDENCE`
- `CROSS_BOOK_MIXED`
- `UNKNOWN`

### Relationship / integrity

- `VERIFIED_RELATIONSHIP_NO_COORDINATION_EVIDENCE`
- `VERIFIED_RELATIONSHIP_PLUS_SPECIFIC_RECIPROCITY_EVIDENCE`
- `REPUTABLE_HYPOTHESIS_ONLY`
- `RUMOR_ONLY`
- `NONE_FOUND`
- `UNKNOWN`

## Explicitly rejected shortcuts

- "升盘 = 真看好" or "降盘 = 真不看好".
- "热门 = 一定诱上".
- "赛季末中游 = 无战意".
- "三天一赛 = 自动状态差/小球".
- "客场欧战 + 客场联赛 = 自动扣分".
- "奖金高 = 一定拼命".
- "同老板/长期租借/关系好 = 会送分".
- "关系叙事 + 一次异常盘口 = 内幕".

## Promotion discipline

The extension is formal as an **audit contract**, not as a set of numerical coefficients. Any future fixed probability, goal, grade or handicap adjustment requires:

1. time-safe historical construction with no result leakage;
2. league/competition controls and team-strength controls;
3. same-time market baselines where relevant;
4. out-of-sample validation across seasons;
5. a prospective forward block;
6. explicit user authorisation for numerical promotion.

Until those conditions are met, the six rules may change interpretation only through an explicit evidence chain; they may not silently manufacture precision.
