# GPT Quant Protocol — v0.1.0

## Role

`GPT-QUANT` is a deterministic mathematical evidence layer. It **must not** create, upgrade, downgrade, or overturn a ticket by itself.

## Input contract

For each bookmaker snapshot, preserve original timestamp and company identity. Company comparisons require the closest valid same-time slice. Never compare materially different timestamps as if synchronous.

## Pipeline

1. Validate decimal odds.
2. Compute multiplicative, power and Shin 1X2 de-vig outputs.
3. Select configured method (`power` in v0.1.0) for cross-company comparison.
4. Express company divergence versus Pinnacle in percentage points.
5. De-vig quoted O/U pair.
6. When one company has usable synchronous 1X2 and O/U, fit Dixon-Coles `lambda_home`, `lambda_away`, `rho`.
7. Produce one normalized score grid.
8. Derive 1X2, AH, O/U and correct-score probabilities from that same grid.
9. Run hard mathematical validation.
10. Freeze Quant Packet before narrative market interpretation.

## O/U hierarchy

- Macau + Pinnacle + Bet365: primary dynamic O/U structure.
- William Hill / Ladbrokes fixed 2.5: Base-2.5 probability anchors, not evidence that the dynamic market is 2.5.
- A displayed line difference is not automatically a difference in latent total-goal expectation.

## Hard failure rules

If a hard mathematical check fails, Quant evidence is unavailable for that match. GPT must state this and continue qualitative SOP without pretending the Quant Layer succeeded. Missing or unsynchronised company timelines must be disclosed by company name.

## Interpretation boundary

Market-implied distribution reconstructs bookmaker prices; it is not objective team strength. It must still be tested against fundamentals, opening rationality, attraction, lifecycle behaviour, schedule/motivation and cross-market coherence.

## Attribution

The design uses established football-modelling techniques also exposed by the MIT-licensed open-source `martineastwood/penaltyblog` project, including de-vigging, Dixon-Coles style score modelling, market probability grids and goal-expectancy reconstruction. This repository keeps a small versioned implementation to preserve reproducibility and avoid silent upstream behavioural changes.
