# GPT Football Full Stack Protocol v1.0

This is the exhaustive registry-driven protocol for pre-match GPT football analysis. New modules must enter the registry and changelog; they must not be silently introduced ad hoc.

## Evidence states
Every module must be labelled `ACTIVE`, `PARTIAL`, `MISSING`, `STALE`, `CONFLICT`, or `RESEARCH_ONLY`. Missing evidence is not negative evidence. Critical stale/conflicting inputs can block the affected module.

## Facts before inference
Separate **fact → inference → assumption → conclusion**. Never present inferred club relationships, motivation, injuries, starting XI or bookmaker intent as verified fact.

## Anti-double-counting
Correlated signals in one dedupe group are cross-checks, not additive independent confirmations. Elo/Pi/ClubElo/xG/recent results overlap team strength; 1X2/AH/OU are linked market prices; market value/lineup/injury overlap squad strength; xG/shots/big chances/xT/VAEP overlap chance creation.

## Market stack
Opening rationality; opening validity/re-openings; same-time 1X2 de-vig; WH/Lad draw protection; Interwetten cold-side check; Pinnacle anchor; Macau signal; Bet365 comparator; AH lifecycle; failed upgrades/reversals; OU ladder latent mean; WH/Lad Base-2.5 anchor; counterfactual pricing; cross-market coherence; market attraction; favourite failure; Draw Exclusion default KEEP.

## Independent strength prior
When reliable data exist, construct a market-independent prior using league HFA/home-away residual plus at most one primary rating family. Elo/Pi/ClubElo alternatives are cross-checks. xG/npxG/xGA may update the prior but must not be duplicated through recent score form.

## Squad/tactical
Official lineup has highest authority; predicted lineup is labelled predicted. Injury/suspension impact uses role/expected minutes when available; raw market value is auxiliary. xT/VAEP, tactical, set-piece, pressing and goalkeeper evidence activate only with adequate coverage.

## Schedule/context
Audit rest, future 7–10 day priority, travel, rotation, weather/pitch, referee, motivation and verified relationship/ownership/agent/transfer networks. No arbitrary probability/goal adjustment without historical calibration.

## Quant + uncertainty
GPT-QUANT reconstructs market probabilities, lambda, score grid and AH/OU settlement. GPT-FEATURE measures reversals, failed upgrades, freshness, disagreement, entropy and gates. Market-implied lambda is not objective team strength.

## Calibration
Track Brier, RPS, log loss and reliability/ECE on adequate chronological samples. Model changes require walk-forward comparison. Prefer league-specific calibration; Chinese competitions remain a separate research/calibration pool.

## Conditional open-source integrations
- penaltyblog: methods/reference; upstream changes never silently rewrite local historical outputs.
- soccerdata: ClubElo/FBref/Football-Data.co.uk/Sofascore/Understat/WhoScored adapter with per-run freshness/QC.
- transfermarkt-datasets: historical structural/transfer/valuation/network data only while the 2026 update pause persists.
- socceraction + kloppy: optional event normalization/xT/VAEP when event data exist.
- StatsBomb open data: research/training/benchmark where coverage/licence permit.

## Decision
Freeze Quant Packet and Feature Packet before interpretation. Freeze H1 before Red Team. H2 must be the strongest coherent alternative and may CONFIRM/DOWNGRADE/OVERTURN. Formal actionable tickets are locked; later changes are explicit corrections. More modules do not force a bet; PASS is valid when evidence conflicts or execution/data quality fails.
