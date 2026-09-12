# MODEL_1 — Game Script, Narrative Premium & Officiating Overlay

Status: FORMAL_MODEL_1_OVERLAY  
Effective date: 2026-09-12  
Scope: full football pre-match analysis under MODEL_1  
User-authorized freeze override: YES

## Purpose

MODEL_1 must not predict only the terminal result. It must also test the plausible process by which that result is reached.

The core question becomes:

> If the final direction is correct, how does the match most plausibly get there? If it fails, what coherent match path defeats it?

This overlay is qualitative/structural until prospective calibration supports numeric transition probabilities. It must not invent precise percentages.

## 1. Game Script / Match Pathway Layer

For every full analysis, construct at least:

1. PRIMARY_SCRIPT — the most coherent path supporting H1;
2. ALTERNATE_SCRIPT — another plausible path that can reach the same terminal direction;
3. FAILURE_SCRIPT — the strongest coherent path by which H1 loses.

Recommended football time blocks:

- 0–20 minutes
- 20–HT
- 45–70
- 70–FT

Each script should state, where relevant:

- expected territorial/pressing pattern;
- who is more likely to score first and why;
- how an early goal changes the next state;
- whether the favourite can economically protect a lead rather than chase margin;
- whether the underdog must open up when behind;
- substitution/bench effects;
- fatigue and schedule effects;
- red/yellow-card sensitivity;
- set-piece dependence;
- late-game chase / game-management behavior;
- implications for 1X2, AH, OU and correct score.

A terminal conclusion without a coherent path is incomplete.

## 2. Match-State Transition Layer

Treat the match as a sequence of states rather than one static 90-minute projection.

State variables may include:

- score differential;
- time remaining;
- red-card manpower state;
- yellow-card/foul constraint on key defenders or pressing players;
- substitutions and role changes;
- xG/xT/shot-pressure signals where available;
- pace/tempo and territorial control;
- fatigue/travel/weather interaction;
- two-leg aggregate state when applicable.

The model should ask transition questions such as:

- If the favourite leads 1–0 by 25', does it continue pressing or reduce risk?
- If the underdog scores first, does the favourite's attack become more productive or merely more exposed?
- If a key defender is booked early, does the matchup mechanism change materially?
- If the favourite does not score by 60', which handicap/total paths deteriorate fastest?

This layer is a pathway audit, not live betting advice.

## 3. Officiating × Match-State Interaction

Referee information is allowed only as an evidence-conditioned path modifier.

Preferred measurable inputs:

- fouls per match;
- yellow/red-card rates;
- penalties awarded;
- home/away differentials with sample size;
- VAR intervention where available;
- added-time tendencies where data quality is adequate;
- interaction with the teams' tactical styles.

Do NOT use unsupported labels such as `referee helps Team A` or `referee is biased toward Team B` as a formal feature.

Any referee-team interaction must be heavily shrunk when sample size is small and must distinguish correlation from causation.

Examples of valid interaction logic:

- strict card profile × underdog physical low block -> higher probability of defender constraint / set-piece exposure;
- lenient profile × pressing derby -> more continuous transition play;
- high penalty tendency × high box-touch favourite -> possible increase in favourite scoring tail.

Examples of invalid logic:

- referee X historically saw Team A win 4/5, therefore Team A receives a positive adjustment;
- social-media claims of favoritism without auditable evidence.

## 4. Narrative Premium vs Real Performance Impact

Separate two different objects:

### REAL_IMPACT
Actual expected performance change from roster, tactics, fitness, role, chemistry and quality.

### NARRATIVE_PREMIUM
Extra market attraction created by a story that may be larger than the real performance change.

Typical football narratives:

- star return / star absence;
- new manager bounce;
- revenge story;
- derby emotion;
- must-win table situation;
- recent upset of a strong team;
- host-face / ceremonial narrative;
- club relationship / reciprocity story;
- famous transfer or academy return.

The same fact must not be counted once in fundamentals and again at full strength in market attraction.

Mandatory question:

> How much of this information changes the team's real expected performance, and how much merely makes one side easier to buy?

## 5. Attraction Resistance

A high-attraction side is not automatically wrong.

However, when a side has an obvious public story, inspect whether the market:

- makes that side cheaper/easier to buy;
- resists the story and moves against it;
- raises the entry barrier on the opposite side;
- shows company-level disagreement after same-time normalization.

`ATTRACTION_RESISTANCE` is a diagnostic label, not a mechanical bet signal.

Especially important:

- underdog has a strong public story yet favourite line strengthens;
- favourite has overwhelming public popularity yet market refuses to deepen;
- narrative strength and market direction diverge.

## 6. Motivation / Competition Importance

Competition importance must be player- and team-specific where possible.

Do not assume every player values league, cup, continental tournament, national-team friendly or secondary international tournament equally.

Use evidence such as:

- club-season timing;
- contract/club release pressure;
- expected minutes and rotation;
- public coach/player comments;
- qualification consequences;
- travel and recovery burden.

If unsupported, mark motivation as an assumption and keep its formal weight small.

## 7. Cross-Market Path Coherence

The selected script must be compatible with the selected markets.

Examples:

- favourite -1.25 requires at least one credible multi-goal path, not merely 'favourite probably wins';
- Under 2.5 should not be justified by a script whose main mechanism is an early goal followed by an open transition game;
- a 2–0 correct-score recommendation should be traceable to a script that suppresses the underdog scoring path.

If the H1 direction requires an implausible sequence of multiple favorable transitions while H2 requires only one ordinary state transition, downgrade H1.

## 8. Red Team Requirement

Red Team H2 must now provide a counter-script, not just a list of risks.

H2 should state:

1. opening state;
2. critical transition(s);
3. why those transitions are plausible;
4. final score/margin/total profile;
5. which market evidence supports that path.

A Red Team that cannot construct a coherent opposite match process is incomplete.

## 9. Output Contract

Before the final ticket, full MODEL_1 analysis should expose a compact pathway block:

```text
GAME SCRIPT
Primary path:
Alternate path:
Failure path:
Critical transition:
Officiating modifier:
Narrative premium / attraction:
Market implication:
```

Missing officiating data must be shown as `OFFICIATING_DATA_MISSING`, not guessed.

## 10. Validation Discipline

Until enough forward samples exist:

- no fixed numeric referee bonus/penalty;
- no fixed narrative-premium points;
- no deterministic 'strict referee = over/under' rule;
- no automatic favorite/underdog action from attraction resistance;
- preserve the pre-match script and compare it with the actual match path after settlement.

Post-match review should score both terminal prediction and process prediction:

- terminal direction correct/incorrect;
- primary script matched / partially matched / failed;
- failure script occurred or not;
- referee interaction material / immaterial / unknown;
- narrative premium overestimated / underestimated / indeterminate.

## 11. Open-source research inspirations

This overlay adopts architectural ideas, not copied betting rules or code, from public research/projects including:

- minute-level football state modeling using score, cards and pressure features with simulation;
- state-machine / Markov game modeling;
- possession/sequence Monte Carlo frameworks where terminal markets are derived coherently from shared simulated paths;
- football betting research that treats referee tendencies as features but evaluates them with walk-forward validation.

Public repositories are research references only. Their reported results do not automatically transfer into MODEL_1 parameters.
