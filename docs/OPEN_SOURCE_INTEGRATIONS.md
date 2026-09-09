# Open-source Integration Registry

## Production-method reference: penaltyblog
Mathematical reference/optional library for de-vig, Poisson-family and Dixon-Coles models, Bayesian goal models, ratings and RPS. Licence: MIT. GPT runtime keeps deterministic local implementations versioned so upstream changes do not rewrite historical analysis.

## Betfair Exchange stack: betfairlightweight + betfairutil + flumine
`betcode-org/betfair` (`betfairlightweight`) is the preferred API-NG/streaming adapter for Betfair market books and historical streams. `mberk/betfairutil` is the preferred utility layer for prices files, book percentages and historical extraction. `betcode-org/flumine` is the preferred event-based replay/simulation/paper-trading framework. The GPT football model uses these as CONDITIONAL data/microstructure adapters; automated order execution remains RESEARCH_ONLY.

## Conditional data adapter: soccerdata
Normalized access to ClubElo, FBref, Football-Data.co.uk, Sofascore, Understat and WhoScored. Scraper breakage and source terms require per-run QC. Supplementary to Titan, not a Titan market-timeline replacement.

## Historical adapter: transfermarkt-datasets
Transfers, market values, appearances, lineups and relationship graphs. As of the 2026-09-07 integration audit, published metadata warns updates are paused and 2026/27 squads are not covered; current-season live use is blocked until freshness recovers.

## Event-data stack: kloppy + socceraction
Kloppy standardizes heterogeneous tracking/event formats. Socceraction provides SPADL/atomic-SPADL and xT/VAEP action values. Use as player/action evidence, never as an automatic match-price adjustment.

## StatsBomb open-data workflows
Use for event/xG research, benchmarking and training where competition coverage exists. Coverage limitations must be explicit.

## Rejected as automatic production inputs
Random tipster/predictor repos without time-ordered validation/model cards/reproducibility; black-box ML merely because reported accuracy is high; fixed Kelly staking as direction engine; any model with closing-odds leakage into earlier pre-match predictions; any Betfair bot whose profit claim cannot be independently reproduced.
