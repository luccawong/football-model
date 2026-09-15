# MODEL_1 RECENT_FORM V1

Titan-only, research-layer calibration. Stage14 fixed weights remain unchanged.

## Frozen design

- Train: 2021-22–2023-24; Validation: 2024-25; Test: 2025-26.
- All feature/ridge choices and release thresholds were frozen before Test.
- Source results obey `source_match_kickoff < target_match_kickoff`; same-kickoff records are batched.
- Market baseline is the Stage14 correlated Pinnacle + Bet365 + Macau log-rate cluster, separately for OPENING/CLOSING.

## OOS results

| League | Phase | Split | N | Base NLL | Recent NLL | Delta NLL | Base/Recent Top3 | Base/Recent 1X2 Brier | Base/Recent RPS | Base/Recent OU Brier | Base/Recent AH Brier | Activation |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 英超 | OPENING | validation | 380 | 2.9679 | 2.9683 | 0.0004 | 0.318/0.324 | 0.5867/0.5867 | 0.2009/0.2009 | 0.2446/0.2448 | 0.2159/0.2159 | SHADOW |
| 英超 | OPENING | test | 380 | 2.8758 | 2.8761 | 0.0004 | 0.355/0.345 | 0.6112/0.6113 | 0.2057/0.2057 | 0.2458/0.2459 | 0.2094/0.2094 | SHADOW |
| 英超 | CLOSING | validation | 380 | 2.9475 | 2.9479 | 0.0003 | 0.316/0.318 | 0.5761/0.5761 | 0.1963/0.1963 | 0.2430/0.2432 | 0.2083/0.2083 | SHADOW |
| 英超 | CLOSING | test | 380 | 2.8691 | 2.8695 | 0.0005 | 0.337/0.337 | 0.6082/0.6082 | 0.2044/0.2044 | 0.2432/0.2433 | 0.2098/0.2098 | SHADOW |
| 西甲 | OPENING | validation | 380 | 2.7474 | 2.7471 | -0.0004 | 0.384/0.384 | 0.5664/0.5663 | 0.1909/0.1908 | 0.2376/0.2376 | 0.2050/0.2048 | SHADOW |
| 西甲 | OPENING | test | 380 | 2.7735 | 2.7735 | -0.0000 | 0.395/0.397 | 0.5698/0.5699 | 0.1956/0.1957 | 0.2432/0.2433 | 0.1982/0.1982 | SHADOW |
| 西甲 | CLOSING | validation | 380 | 2.7288 | 2.7286 | -0.0003 | 0.405/0.408 | 0.5584/0.5584 | 0.1870/0.1870 | 0.2339/0.2340 | 0.1999/0.1998 | SHADOW |
| 西甲 | CLOSING | test | 380 | 2.7676 | 2.7676 | 0.0000 | 0.408/0.411 | 0.5703/0.5704 | 0.1953/0.1953 | 0.2391/0.2391 | 0.1993/0.1993 | SHADOW |
| 意甲 | OPENING | validation | 380 | 2.7629 | 2.7629 | -0.0000 | 0.395/0.395 | 0.5706/0.5706 | 0.1846/0.1846 | 0.2465/0.2466 | 0.1975/0.1974 | SHADOW |
| 意甲 | OPENING | test | 380 | 2.7499 | 2.7497 | -0.0001 | 0.371/0.371 | 0.5836/0.5835 | 0.1964/0.1963 | 0.2543/0.2543 | 0.2034/0.2033 | SHADOW |
| 意甲 | CLOSING | validation | 380 | 2.7428 | 2.7428 | -0.0000 | 0.395/0.395 | 0.5675/0.5675 | 0.1840/0.1840 | 0.2419/0.2419 | 0.1947/0.1947 | SHADOW |
| 意甲 | CLOSING | test | 380 | 2.7424 | 2.7425 | 0.0001 | 0.361/0.361 | 0.5837/0.5836 | 0.1965/0.1965 | 0.2546/0.2546 | 0.2028/0.2027 | SHADOW |
| 德甲 | OPENING | validation | 306 | 3.1130 | 3.1148 | 0.0018 | 0.242/0.242 | 0.5997/0.5997 | 0.2059/0.2059 | 0.2328/0.2329 | 0.2139/0.2139 | SHADOW |
| 德甲 | OPENING | test | 306 | 3.0459 | 3.0456 | -0.0004 | 0.301/0.304 | 0.5663/0.5663 | 0.1920/0.1920 | 0.2239/0.2238 | 0.2032/0.2031 | SHADOW |
| 德甲 | CLOSING | validation | 306 | 3.0767 | 3.0772 | 0.0006 | 0.242/0.239 | 0.5913/0.5914 | 0.2022/0.2022 | 0.2235/0.2236 | 0.2108/0.2107 | SHADOW |
| 德甲 | CLOSING | test | 306 | 3.0421 | 3.0418 | -0.0003 | 0.294/0.294 | 0.5624/0.5624 | 0.1901/0.1901 | 0.2239/0.2239 | 0.2029/0.2028 | SHADOW |
| 法甲 | OPENING | validation | 306 | 2.9860 | 2.9860 | 0.0000 | 0.297/0.297 | 0.5674/0.5676 | 0.2034/0.2035 | 0.2392/0.2392 | 0.2136/0.2137 | SHADOW |
| 法甲 | OPENING | test | 306 | 3.0196 | 3.0198 | 0.0002 | 0.291/0.291 | 0.5821/0.5820 | 0.2003/0.2002 | 0.2407/0.2409 | 0.2085/0.2084 | SHADOW |
| 法甲 | CLOSING | validation | 306 | 2.9669 | 2.9670 | 0.0000 | 0.297/0.294 | 0.5641/0.5642 | 0.2012/0.2012 | 0.2380/0.2380 | 0.2108/0.2108 | SHADOW |
| 法甲 | CLOSING | test | 306 | 3.0134 | 3.0136 | 0.0002 | 0.317/0.320 | 0.5816/0.5815 | 0.2001/0.2001 | 0.2356/0.2357 | 0.2080/0.2079 | SHADOW |

## Scope

- UCL: `NOT_CALIBRATED_V1`; no Big5 coefficient transfer.
- A SHADOW artifact is intentionally not loadable by the runtime.
