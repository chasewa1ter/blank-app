# Slides

## Slide 1: The headline rule

**Title:** No batting order shape beats talent, and shape A was a one season pattern

**Chart:** `out/chart_b_shapeA_slope_by_decade.png`

* 2026: 13.2 runs per 162 per slot closer to A, the season the shape was picked from.
* 1926 to 2025: 0.03 runs per 162 per slot across 362,487 lineups, flat in every decade.
* Shuffled tags produce a best shape this strong 12% of the time.

**Speaker note:** A was chosen as the best of 512 patterns in one season. The other 100 seasons are a fair test, and the pattern is not there.

## Slide 2: Order vs composition

**Title:** Batting order alone is worth a fraction of a run per slot

**Chart:** `out/chart_d_empirical_vs_markov.png`

* Moving the same nine hitters one slot toward A costs 0.33 runs per 162.
* The best possible order beats what managers used by 5.2 runs per 162, at the low end of the 5 to 15 run benchmark.
* The 2026 edge came from who was in the lineup and from chance, not from where they batted.

## Slide 3: The manager card

**Title:** Best on base hitters first, power in 2 to 4, and do not sweat 6 to 9

| Slot | Lean | Typical OBP in best orders | Firm or bends |
|---|---|---|---|
| 1 | contact (36% P in best orders; 33% in 1973 to 2025 DH lineups) | OBP 0.354 | firm (neighbor swap 0.60 runs per 162) |
| 2 | power (74% P in best orders; 73% in 1973 to 2025 DH lineups) | OBP 0.361 | firm (neighbor swap 0.75 runs per 162) |
| 3 | power (88% P in best orders; 85% in 1973 to 2025 DH lineups) | OBP 0.333 | firm (neighbor swap 0.73 runs per 162) |
| 4 | power (69% P in best orders; 73% in 1973 to 2025 DH lineups) | OBP 0.327 | firm (neighbor swap 0.58 runs per 162) |
| 5 | either (41% P in best orders; 50% in 1973 to 2025 DH lineups) | OBP 0.319 | firm (neighbor swap 0.62 runs per 162) |
| 6 | either (57% P in best orders; 57% in 1973 to 2025 DH lineups) | OBP 0.302 | bends (neighbor swap 0.56 runs per 162) |
| 7 | either (55% P in best orders; 54% in 1973 to 2025 DH lineups) | OBP 0.280 | bends (neighbor swap 0.44 runs per 162) |
| 8 | contact (30% P in best orders; 31% in 1973 to 2025 DH lineups) | OBP 0.279 | bends (neighbor swap 0.44 runs per 162) |
| 9 | contact (19% P in best orders; 19% in 1973 to 2025 DH lineups) | OBP 0.297 | bends (neighbor swap 0.46 runs per 162) |

Firm = average cost of swapping with a neighbor at or above the median (0.58 runs per 162). All swaps are small: the whole best order is worth about 5 runs a season over current practice.
