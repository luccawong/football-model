# MODEL_1 Agent Handoff — 2026-09-16

Status: **ACTIVE OPERATING HANDOFF**
Model: `MODEL_1`
Authority: user-authorized targeted override layered on top of the frozen MODEL_1 baseline.
Active override manifest: `config/model_1_active_overrides_20260914.json`
Single-H1 falsification policy: `config/model_1_single_h1_falsification_policy.json`
Preflight gate: `gpt/preflight_gate.py`

This document exists so another AI agent can execute the same football-analysis process without relying on chat memory.

---

## 1. Core operating principle

MODEL_1 is not a storytelling engine. The objective is to identify the most stable pre-match executable direction from the available evidence while explicitly testing whether the evidence chain is wrong.

Always separate:

- **FACT** — observed data, confirmed lineup, verified competition rules, actual bookmaker quote/timeline, official schedule/weather/injury information.
- **INFERENCE** — interpretation of pricing, market intent, tactical effect, attraction, motivation.
- **ASSUMPTION** — an unverified bridge needed to connect facts.
- **CONCLUSION** — final market/line/side.

Do not protect a prior conclusion merely because it was generated earlier.

Repeated correlated errors are treated first as a possible **MODEL / EXECUTION FAILURE** until structural checks show otherwise. Do not lead with randomness, variance, early goals, weather, referee, or generic football unpredictability as an excuse.

---

## 2. Current formal output policy

For each fully analysed match:

- exactly **one** formal main ticket;
- no non-main ticket;
- no automatic final PASS under the active MODEL_1 ticket policy;
- low confidence is expressed through grade and execution conditions;
- near kickoff, output ticket first, explanation second;
- once an actionable formal ticket is issued, it is locked;
- any later directional change must be explicitly labelled `CORRECTION old -> new`;
- never silently rewrite the original ticket after market movement or result information.

The user's personal bet/no-bet decision is separate from model accuracy.

---

## 3. Current 18-slot analysis order

The baseline MODEL_1 order remains 18 slots, but **slot 17 no longer contains H2**.

1. Fundamentals
2. Market snapshot
3. Opening first impression
4. Opening rationality / odds lifecycle
5. Off-field / weather / schedule / relationship context
6. Lineup / tactics
7. 1X2 + 实开/韬开 audit
8. Asian handicap + 欧亚转换 consistency audit
9. Totals / OU independent module
10. Cross-market coherence
11. Market attraction
12. External draw-exclusion + winner audit
13. Underdog outright audit
14. Correct-score Poisson / Dixon-Coles / Bayesian market engine
15. Uncertainty audit / neutral evidence ledger
16. Freeze H1
17. **Single-H1 falsification audit**
18. Formal main ticket

### Slot 17 changed on 2026-09-16

Old behaviour: construct an independent blind H2 and then adjudicate H1 vs H2.

Current behaviour:

- keep **one working hypothesis only**;
- freeze H1 after stages 1–15;
- aggressively try to falsify H1;
- do **not** construct a mandatory second candidate/ticket;
- if material counterevidence breaks H1, discard H1 and rebuild it directly;
- the rebuilt thesis becomes the only H1;
- then re-run the falsification gate before ticketing.

Valid falsification outcomes:

- `SURVIVES`
- `DOWNGRADE`
- `UPGRADE`
- `OVERTURN_AND_REBUILD`

The model must not use a second formal candidate as a procedural prop.

---

## 4. Mandatory falsification checks

Before a ticket is allowed, the agent must do all of the following:

1. Record the **three strongest counterevidence items** against H1.
2. State explicit **H1 failure conditions**: what pre-match structure would make H1 wrong or materially weaker.
3. Test at least two plausible alternative match paths without turning them into a second ticket.
4. Test whether the market explanation is genuine evidence or merely a story that fits H1.
5. Test favourite win probability vs handicap-cover probability separately.
6. Test the draw path whenever draw has not been externally excluded.
7. Test underdog outright for deep favourites.
8. Reinterpret the opening/lifecycle from the opposite market reading.
9. Check same-time-slice company divergence.
10. Check 1X2 / AH / OU conflicts rather than averaging them away.
11. Test recent-form evidence against the market view.
12. Verify competition rules and resulting game-state incentives.
13. Identify missing/weak data that could reverse the conclusion.
14. Ask: **does the thesis explain anomalies, or merely narrate them away?**

If these are incomplete, preflight returns `PRECHECK_BLOCKED_NO_TICKET`.

---

## 5. Formal market-source rules

Formal 1X2/AH/OU market source = **Titan only**.

JCB / Sporttery:

- disabled from formal MODEL_1;
- not auxiliary in current formal analysis;
- archived historical work does not enter current ticket formation.

Betfair / OddsPapi:

- `SHADOW_RESEARCH` only;
- missing exchange data is not negative evidence;
- no formal ticket impact until separately activated and validated.

External draw-exclusion website is a separate execution constraint, not an odds source.

---

## 6. Fundamentals first

Before interpreting prices:

- review recent matches one by one;
- weight opponent quality;
- distinguish repeatable performance from flattering scoreline;
- include home/away context;
- use shots/xG/chance quality when available;
- audit future 7–10 day schedule and priority;
- audit travel/rotation/expected core minutes;
- for deep favourites, explicitly test **economic win vs cover**.

League-level priors may be used as priors/risk filters only, not single-match betting conclusions.

Do not convert 'stronger team' directly into 'covers deep line'.

---

## 7. Opening and lifecycle discipline

Opening first impression must use opening structure only.

Then separately audit:

- true opening vs stale/invalid opening;
- information re-openings;
- ordinary movement;
- intervening matches after an early quote;
- closest common time slice when companies opened at different times;
- adjacent counterfactual price/line;
- line movement and water movement together.

A late synchronized buyback or retreat can invalidate an earlier lifecycle story. It must trigger re-testing, not be rationalized away.

Do not say 'the market strengthened X' unless the relevant companies and aligned time slices actually support that statement.

---

## 8. 1X2 company roles

Titan company roles:

- William Hill + Ladbrokes UK = primary pair
- WH = draw-price location/protection/inducement audit
- Ladbrokes = win-tail difference
- Interwetten = cold-side/upset-risk check
- Pinnacle = capital anchor, **not automatic smart money**
- Macau = Asian signal/divergence
- Bet365 = key comparator
- HKJC = Asian/local comparator

Always separate raw odds from de-vig probability.

Use same-time-slice comparisons.

Do not conclude `lower favourite price = favourite wins`.

---

## 9. Asian handicap

Run after 1X2.

Mandatory questions:

- Does 1X2 strength convert coherently to AH?
- Is the line deep enough for the 1X2 view?
- Is water consistent with the line level?
- Did a deeper upgrade fail?
- Did the market touch a ceiling and retreat?
- Is favourite-win probability being confused with cover probability?

For deep favourites separate four paths:

1. favourite wins and covers;
2. favourite wins but does not cover;
3. draw;
4. underdog wins outright.

One-goal favourite wins are especially important around -0.75 / -1 / -1.25 / -1.5 structures.

---

## 10. Totals / OU

OU is an independent core module.

Dynamic mainstream core:

- Macau
- Pinnacle
- Bet365

WH/Lad 2.5 is a **Base-2.5 probability anchor**, not directly comparable to dynamic 2.75/3/3.25/3.5 displays.

Use the full OU ladder and price normalization where possible.

A low total line does **not** automatically mean a low-event match. A low line with over protection may mean high probability mass near the line. Example failure mode: treating a 2.25/2.5 structure as if it strongly predicted 0–2 total goals when the market may actually center near 2.4–2.6.

Do not infer OU mechanically from AH.

---

## 11. Cross-market coherence

1X2, AH and OU are linked prices, not three independent votes.

Test whether they imply compatible match paths.

Examples of real conflict:

- 1X2 strongly favours a team but AH refuses to deepen;
- favourite price strengthens but OU collapses in a way that changes cover path;
- AH retreats while weak-side outright price also shortens;
- OU line moves but price normalization shows no meaningful latent-total change.

Conflicts are information; do not hide them through averaging.

---

## 12. Market attraction

Before interpreting weak-side price behaviour, determine whether the weak side has a public betting story.

Possible attraction sources:

- recent narrow loss to elite opposition;
- high-profile player/manager narrative;
- recent upset;
- historical matchup story;
- favourite rotation/schedule concerns;
- visible market retreat that invites dog buyers.

Weak-side non-lowering odds do not automatically mean bookmaker rejection if the weak side has little attraction.

Conversely, a hot favourite with an obvious public story requires a favourite-tax audit.

---

## 13. External draw-exclusion forward test

Current one-month forward test:

- JC = primary execution layer
- BD = secondary validation layer

JC=1:

- remove draw from execution branch;
- immediately audit HOME WIN vs AWAY WIN;
- then separately determine AH cover vs win-no-cover.

JC=0:

- does not mean draw is predicted;
- draw remains active and receives enhanced audit.

JC missing:

- stays UNKNOWN;
- do not let BD alone substitute for JC.

The competition itself allowing a draw at 90 minutes is a separate rule question. Never confuse draw-exclusion labels with competition regulations.

---

## 14. Underdog outright audit

Mandatory when favourite AH is -0.75 or deeper, and central when draw is externally excluded.

Use WH / Lad / Bet365 / Pinnacle / Interwetten / Macau / HKJC at comparable time slices.

Do not use absolute underdog-win probability as the only test.

Look for:

- weak-side outright protection;
- unusual company residual vs match median;
- AH deepening while outright upset protection strengthens;
- AH retreat while underdog win price shortens;
- same-company AH + 1X2 confirmation.

AH support for the underdog is **not** automatically outright-upset evidence.

---

## 15. Competition-rules gate

For every cup/knockout match, verify rules **before interpreting tactical incentives**.

Must distinguish:

- single-leg vs two-leg;
- aggregate score state when two-leg;
- 90-minute market settlement vs advancement;
- extra time vs direct penalties;
- whether away goals exist;
- whether a draw is strategically acceptable near 90 minutes;
- whether a favourite leading by one has any incentive to chase a second goal.

### Important example: English League Cup / Carabao Cup

Early rounds including Round 3 are single-match ties. A 90-minute draw can proceed directly to penalties under the current competition rules; 'a winner must advance' does **not** mean the 90-minute 1X2 draw path disappears.

This affects deep-handicap and late-game cover probability.

---

## 16. Stage14 correct-score engine

Formal score engine currently uses a MARKET_ONLY formal mode for leagues/competitions without an approved historical prior.

Core market reconstruction uses Pinnacle + Bet365 + Macau as **one correlated market likelihood cluster**, not independent votes.

Reconstruct λH/λA/rho from current 1X2 + dynamic OU, then produce the Dixon-Coles/Poisson predictive distribution.

Do not count Stage14 as independent confirmation of the same market inputs used earlier. It is a quantitative representation of the market state, not a separate bookmaker vote.

Final score Top3 must pass the final 1X2/AH/OU direction-consistency gate.

For deep favourites, downgrade non-cover score paths if the final formal AH requires a cover.

---

## 17. Two mandatory research/shadow checks

When the user says `按Model_1分析`, these must be explicitly checked every match even if they have zero formal weight.

### A. Team Goal Baseline

- historical team-goal baseline research layer;
- strict no-future-leakage;
- do not combine with another historical prior as if independent;
- if unavailable/out of scope, state `MISSING_RUNTIME` or `OUT_OF_SCOPE`;
- never fabricate λ;
- formal weight remains NONE unless separately activated.

### B. Prematch Context / Recent Form V1

- SHADOW calibration layer;
- formal weight NONE unless a competition-specific artifact has passed activation criteria;
- narrative claims cannot become arbitrary ±λ adjustments;
- if no competition artifact exists, say so explicitly.

Missing shadow modules do not justify inventing numbers.

---

## 18. Current model-drift diagnostics

As of 2026-09-16 the user has observed a multi-match period in which MODEL_1 analysis appeared systematically off-course.

Do not frame this as one isolated result.

Primary failure hypotheses to audit prospectively:

1. **H1 anchoring** — once a direction forms, later modules become supporting narrative.
2. **Market-explanation drift** — the model explains why the market moved instead of testing whether its interpretation is correct.
3. **Weak adversarial function** — the former Red Team/H2 layer often downgraded rather than truly invalidating H1.
4. **Market over-reliance** — MARKET_ONLY formal score logic can overweight current pricing relative to real tactical/scoring shifts.
5. **OU center anchoring** — totals and score prediction may be dragged toward the market center without sufficiently testing tail/event volatility.
6. **Correlated directional errors** — repeated misses in the same structural direction are more serious than an ordinary losing streak.

Current remediation is **process correction, not numeric recalibration**:

- H2 removed;
- single-H1 falsification hard gate added;
- repeated errors default to model/execution fault until disproven;
- no small-sample parameter tuning;
- no result-aware rewriting of old reasoning.

---

## 19. Recent case lessons

These are diagnostic lessons, not new fixed weights.

### Rayo Vallecano vs Espanyol — failure-mode example

Prematch model supported Espanyol +0.25 and Under 2.5. During the match, Rayo reached an early 2-0 lead.

Do not reduce the lesson to 'an early goal happened'. The pre-match diagnostic concern was that:

- AH retreat from Rayo -0.5 to -0.25/PK was interpreted mainly as Rayo weakening;
- late synchronized Rayo 1X2 buyback was observed but not allowed to re-open the directional thesis strongly enough;
- low OU was treated too confidently as a low-event signal;
- later modules reinforced the initial weak-side thesis instead of challenging the lifecycle interpretation.

This is the canonical example of **explaining the market vs testing the market interpretation**.

### Deep favourite lesson

A favourite can be extremely likely to win while a -1.5/-2/-3.25 ticket remains only marginal. Always calculate/inspect the margin path separately.

### Cup rule lesson

Single-match knockout structure may reduce late incentive to extend a one-goal lead if a lead is already sufficient for advancement. Conversely, when tied, both teams may accept penalties depending on matchup and game state. Competition rules must enter the path analysis before the AH conclusion.

---

## 20. User challenge layer

The user often challenges the model pre-match and has recently reported a high short-run hit rate when doing so.

Do **not** assume this is a proven long-run edge.

Do **not** dismiss it either.

Current treatment:

- `SHADOW_DIAGNOSTIC_ONLY`;
- formal model weight = NONE;
- user challenge does not automatically flip a ticket;
- when the user gives a reason, preserve the reason exactly enough to classify the failure mode later;
- real-money validation is explicitly **not required**;
- use settled historical cases and prospective paper tracking to identify recurring omitted variables.

The useful question is not 'was the user opposite again?' but:

> What recurring structural feature caused the user to reject the model, and did that feature predict model failure prospectively?

If a recurring pattern survives a sufficient prospective sample, research it as a candidate future model layer rather than silently changing MODEL_1.

---

## 21. Anti-excuse / anti-backfit rules

After a loss:

First ask whether the problem was:

- model logic;
- opening/lifecycle interpretation;
- same-time-slice error;
- missing data;
- lineup/formation error;
- competition-rule error;
- schedule/priority error;
- market-attraction misread;
- draw-path deletion error;
- underdog outright omission;
- OU interpretation error;
- H1 anchoring;
- preflight/process failure.

Only after these are checked may variance/randomness be used as the residual explanation.

Never use the result to reconstruct a pre-match signal that was not actually available.

Live/unfinished matches may trigger a diagnostic warning but are not final settled labels.

---

## 22. Missing data

Missing means missing.

If a key company timeline or module is unavailable:

- name the company/module;
- state whether the missingness affects direction or grade;
- never interpolate missing timeline nodes;
- opening/current is not a full lifecycle;
- `SOURCE_NO_DATA` is not negative evidence.

---

## 23. Statistical/recording workflow

Analysis chat:

- analyze;
- run falsification;
- output ticket;
- explain.

Do not update central stats automatically.

If user says `记录` / `存档`:

- freeze the prematch conclusion only.

Central database/Excel update requires an explicit unified-update instruction.

Database = fact source.
Excel = reporting/output layer.

Formal-model accuracy is primary; user's actual bet/no-bet is secondary.

---

## 24. What another agent must never do

Never:

- skip mandatory stages because kickoff is close;
- use quick scan as deep analysis;
- silently change a locked ticket;
- create fake H2 output after the 2026-09-16 override;
- call a second directional candidate 'required Red Team';
- use Stage14 as independent confirmation of the same market inputs;
- treat Pinnacle as automatically smart money;
- compare WH/Lad fixed 2.5 directly with dynamic 3.25 as if same line;
- compare companies opened days apart without time alignment;
- infer 'cup must have winner' => '90-minute draw impossible';
- convert favourite win probability directly into cover probability;
- fabricate missing shadow modules;
- explain repeated losses away before checking structural drift;
- backfit pre-match logic from the final score.

---

## 25. Current execution summary

When instructed `按Model_1分析`:

1. Load base MODEL_1 + active override manifest.
2. Verify Titan match identity and state.
3. Verify competition rules if cup/knockout.
4. Run all formal stages 1–15.
5. Force-check Team Goal Baseline and Recent Form/Context shadow layers.
6. Freeze a single H1.
7. Run the Stage-17 single-H1 falsification audit.
8. If falsified, discard/rebuild H1 and re-check it.
9. Preflight must PASS.
10. Output exactly one formal main ticket.
11. Lock it.

That is the current MODEL_1 execution contract for all agents.
