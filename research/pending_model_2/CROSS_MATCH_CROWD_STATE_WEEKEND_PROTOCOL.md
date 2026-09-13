# Cross-Match Crowd State — Weekend Protocol

Status: RESEARCH_ONLY / ZERO_FORMAL_MODEL_1_IMPACT
Created: 2026-09-13
Motivation case: 2026-09-12 EPL matchday, especially Sunderland vs Arsenal

## Purpose

MODEL_1 currently interprets each match primarily as an independent pre-match pricing problem. This research layer tests whether earlier completed matches on the same day can alter bettor psychology, public-side demand and the sales function of later prices.

The hypothesis is not that results have a quota or that a sequence of underdogs mechanically implies a later favourite. The testable hypothesis is:

> Earlier completed results can change bettor beliefs and crowd demand for later matches; bookmakers/markets may then reprice in a way that reflects demand management or narrative reinforcement rather than only new football information.

This matters most on dense weekend slates, when multiple matches from the same league are played sequentially and bettors can immediately carry lessons from early matches into later kickoffs.

## Hard anti-leakage rule

For each target match, Cross-Match Crowd State may use only matches whose final result was already known before the target match kickoff and only market snapshots timestamped before the target kickoff.

No later match result may be used. No same-time unfinished match may be treated as a completed crowd signal.

## Why weekends receive special attention

Saturday/Sunday slates often create:

- several same-league matches before a late kickoff;
- high recreational betting concentration;
- repeated exposure to the same narrative class (favourites, home sides, draw exclusion, underdogs, Over/Under trends);
- rapid social/media amplification of "today favourites are failing", "today underdogs keep covering", "today draws are everywhere", etc.;
- a late flagship match in which the public can transfer the day's experience into a new wager.

Weekend status itself is not a signal. It is an amplification context. The layer still requires observable sequential evidence.

## Required inputs

### A. Prior-result state

At target kickoff, record for already completed same-day matches:

- same league first, then same competition family / major top-flight context as secondary;
- favourite win rate;
- favourite AH cover rate;
- underdog AH cover rate;
- draw rate;
- home/draw/away distribution;
- count of large public-side failures;
- count of repeated result archetypes (e.g. multiple favourites fail, multiple home favourites fail, multiple draws).

### B. Current-match public-story attractiveness

Record whether the current weak side or favourite has an easy human narrative, such as:

- home underdog;
- favourite on short rest / European travel;
- recent underdog form or headline result;
- favourite rotation / injuries;
- line already moved toward the underdog;
- OU movement that visually supports a close game;
- draw-exclusion / external labels reinforcing the same story;
- media narrative consistent with the crowd direction.

This is a psychology/sales variable, not a claim that the story is true.

### C. Post-result market response

The most important field.

For the target match, compare market snapshots from BEFORE and AFTER meaningful earlier results finished.

Track at minimum:

- Macau AH line + water;
- Pinnacle AH / 1X2;
- Bet365 AH / 1X2;
- HKJC when available;
- William Hill / Ladbrokes 1X2;
- OU main line and prices.

Ask:

1. Did the price move only because of new team information?
2. Did the move occur after the earlier result cluster with no matching fundamental news?
3. Did the move make the already-attractive public story even easier to believe or buy?
4. Did different bookmaker types move together or diverge?

## Repricing interpretation classes

### INFORMATION_DRIVEN

Movement is reasonably explained by identifiable football information: lineup, injury, suspension, schedule confirmation, weather, etc.

### DEMAND_DRIVEN_CANDIDATE

Movement follows an already popular side and occurs without enough new football information to explain the magnitude.

### NARRATIVE_SALES_CANDIDATE

The new price/line makes an already compelling crowd story more persuasive. Example structure: repeated earlier underdog/favourite-failure results + current underdog has an obvious story + favourite line retreats / odds drift in a way that visibly validates the crowd's new belief.

### MIXED / AMBIGUOUS

Cannot separate information and demand effects.

No class is treated as proven bookmaker intent.

## Cross-Match Crowd State labels

### NORMAL

No material sequential crowd condition.

### CROWD_CHASING_UNDERDOG

Earlier completed matches repeatedly rewarded underdog/favourite-failure positions and the current underdog also has an easy narrative.

### CROWD_CHASING_FAVOURITE

Earlier matches rewarded obvious favourites / favourite covers and the current favourite is the natural continuation trade.

### CROWD_CHASING_DRAW_OR_NOTLOSE

Earlier results and current story make draw / +AH / favourite-non-win the dominant public narrative.

### REVERSAL_CANDIDATE

Crowd state is already strongly one-sided, current market action continues to make that same story easy to buy, while the opposite side's underlying football case has not deteriorated enough to justify the full move.

This is the key Red-Team state for cases like the 2026-09-12 Arsenal late match hypothesis.

### AMBIGUOUS

Narrative exists but observable market response does not support a clean interpretation.

## Weekend amplification flag

Research field only:

- `WEEKEND_DENSE_SLATE = 1` when the target is on Saturday/Sunday and multiple relevant matches have already completed before kickoff.
- `LATE_SLOT = 1` when the target is meaningfully later than the main same-league block.
- `FLAGSHIP_FAVOURITE = 1` for a major public favourite / brand whose match is likely to attract carry-over betting attention.

The combination `WEEKEND_DENSE_SLATE + LATE_SLOT + FLAGSHIP_FAVOURITE` should trigger mandatory Cross-Match Crowd State review, but does not determine the betting direction.

## Sunderland vs Arsenal research interpretation

Pre-target context: the earlier EPL slate produced repeated favourite/home-side failures and draws. By the late Arsenal kickoff, Sunderland had an unusually coherent public story: home underdog, Arsenal short recovery after Europe, Arsenal price drift, AH retreat from around -1 toward -0.75 and lower-total repricing.

The research hypothesis is that MODEL_1 treated most of those price changes as independent negative Arsenal information. Cross-Match Crowd State would instead ask whether part of the repricing was crowd-demand / narrative-sales driven after the earlier EPL outcomes had already conditioned bettors to chase the underdog/non-favourite side.

This does NOT prove deliberate bookmaker manipulation. It creates a pre-match competing hypothesis that must be evaluated against football information and bookmaker divergence.

## Mandatory Red-Team questions when REVERSAL_CANDIDATE is triggered

1. If the crowd did NOT know the earlier same-day results, would this current market move still look equally strong?
2. What new football information actually arrived between the pre-cluster snapshot and the post-cluster snapshot?
3. Is the current underdog/favourite story now too easy to explain to a recreational bettor?
4. Is the market making the crowd side easier to buy, harder to buy, or merely validating it narratively?
5. Does Pinnacle behave differently from Bet365/HKJC/Macau/WH/Lad?
6. Is the favourite's fair football case genuinely worse, or merely less fashionable after the day's sequence?
7. Can the opposite-side hypothesis explain the same AH + 1X2 + OU structure without relying on hindsight?

## Validation plan

From 2026-09-13 onward, log this layer prospectively for dense weekend slates.

For each reviewed target, store:

- target match_id;
- prior-result cut-off timestamp;
- completed prior matches used;
- prior favourite/underdog/draw state;
- current public-story direction;
- bookmaker snapshots before/after prior results;
- repricing class;
- Crowd State label;
- whether REVERSAL_CANDIDATE fired;
- MODEL_1 formal ticket (unchanged during freeze);
- shadow alternative direction;
- final result / AH settlement after match.

Evaluate only after a meaningful sample. Do not promote thresholds or use this to rewrite MODEL_1 during the freeze.

## Failure modes to guard against

- gambler's fallacy: "too many underdogs already, so favourite must be next";
- post-hoc storytelling;
- using results that were not known before kickoff;
- assuming every drift/retreat is manipulation;
- assuming bookmakers have one coordinated intention;
- confusing public attractiveness with actual betting share when no flow data exist;
- treating Saturday/Sunday alone as predictive.

## Current research priority

HIGH.

Reason: MODEL_1's 2026-09-12 failure cluster suggests a missing cross-match correlation layer. The most important question is not whether the model can read one isolated price move, but whether it can recognize when a whole day's earlier results have changed what later bettors want to buy and therefore changed what the same price movement means.