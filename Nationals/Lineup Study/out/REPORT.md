# Power vs contact batting order, 1926 to 2026

**Verdict: Shape A (P P C C P C C P C) does not hold up: its 2026 edge is the kind of result that picking the best of 512 shapes in one season produces by chance, across 362,487 lineups from 1926 to 2025 it is worth 0.03 runs per 162 games per slot, in effect zero, and batting order on its own is worth well under one run per slot.**

## Is the shape real?

* In 2026 each slot closer to shape A came with 13.2 more runs per 162 games than lineup talent predicted (SE 5.7). That is the pattern the shape was picked from. In this rebuild A ranked 3 of 512 shapes, B 12 and C 369.
* Picking the best of 512 shapes inflates the winner. When P and C tags are shuffled among each team's own hitters, the best shuffled shape is at least as strong as the real 2026 best 12% of the time (1,000 shuffles). Shape A's t statistic of 2.3 is below the 3.9 bar that 512 tries require.
* Every season from 1926 to 2025 is out of sample. There the effect is 0.03 runs per 162 per slot (SE 0.58), and the 95% interval runs from 1.1 runs gained to 1.2 runs lost for each slot closer to A. No decade gets past 1.3 SE, and comparing a team only with its own other games gives 0.46 runs per 162 per slot (against A).

## How big in wins?

* Taken at face value, 2026 says 1.32 wins per 162 per slot (10.0 runs per win). The average 2026 lineup sat 4.5 slots from A, so full adoption would be worth about 59 runs. The published research puts the gap between the best and a typical order at 5 to 15 runs for the whole order, so the 2026 number is several times too large to be a batting order effect.
* History says 0.003 wins per 162 per slot. The win model over all 1926 to 2026 lineups gives 0.13 wins per 162 per slot (SE 0.11).
* The Markov run model, which holds the nine hitters fixed and only changes the order, says the best possible order beats the order managers actually used by 5.2 runs per 162 in 2026 and 7.2 runs from 1926 to 2025, inside the 5 to 15 run benchmark. Rearranging the same hitters into shape A costs 1.2 runs per 162 in 2026. Per slot moved toward A the pure order effect is 0.33 runs per 162 (fewer), so the 2026 slope is about 40 times larger and points the other way. The 2026 result comes from which hitters were in the lineup and from chance, not from their order.

## What a manager should do

* Do not set lineups by a power and contact pattern. No shape, A, B or C, moves runs by more than about one run per 162 per slot in 100 years of games.
* Order by on base skill first, then power. In the Markov best orders for 2026, slots 2, 3 and 4 hold power lean hitters 74%, 88% and 69% of the time, while slots 1, 8 and 9 lean contact (P share 36%, 30%, 19%). The leadoff and number 2 hitters carry the highest OBP (0.354 and 0.361).
* Do not sweat the bottom. Swapping neighbors in slots 6 to 9 costs 0.4 to 0.5 runs per 162; even the costliest swap at the top costs 0.9 runs.

## Caveats

* The MLB Stats API, Savant and Baseball Reference were blocked where this ran. 2026 lineups, scores and batting lines were rebuilt from public mirrors of the Stats API feed; wins and losses match the final standings for all 30 teams. The rebuild gives shape A 0.082 runs per game per slot (rank 3) against 0.090 (rank 1) in the earlier analysis quoted in the brief, and the same 14 exact shape A games at 11 and 3. With xwOBA talent A ranks 1. The conclusion does not depend on these small differences.
* The Markov model leaves out steals, errors and extra innings, so it reads 13% low in 2026 and 18% low historically; its order effects are scaled up by those factors.
* Tags are relative to each season's hitters, and lineup talent is measured with the same season's stats, so a hitter's tag and talent share the noise of that season.

Every number above is computed by `scripts/09_report.py` from files in `out/tables/` and checked a second way in `out/CHECKS.md`.
