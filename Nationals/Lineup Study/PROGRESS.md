# Progress

Job started 2026-10-29 02:16 UTC in a cloud container.

## Phase 1: data acquisition (done 02:47, about 30 minutes including source hunting)

* `01_download.py` (231 s first run): Retrosheet game logs 1926 to 2025 plus event files for the 29 spot check seasons, Lahman 2026 edition (through 2025), Chadwick register, 2026 live feed pitch mirror (2023 to 2026), 2026 box score mirror. Blocked hosts logged in `PROBLEMS.md`.
* `02_build_games.py` (107 s): `data/games.parquet` 183,752 games (181,323 from Retrosheet, 2,429 for 2026); `data/lineups.parquet` 367,504 team games; `data/pa_2026.parquet` 184,284 plate appearance rows rebuilt from the feed.
* `03_player_seasons.py` (17 s): `data/player_seasons.parquet` 88,977 player seasons with tags; `data/pitcher_seasons.parquet` 42,637 pitcher seasons.

## Phase 2: validation (done 02:52, 25 s run)

* `04_validate.py` wrote `out/VALIDATION.md`.
* Team seasons 1926 to 2025 vs Lahman: 2,269 of 2,306 exact on all four fields; no gap larger than 4 runs.
* 2026 wins and losses vs final standings: 30 of 30. 2026 runs vs the box score mirror's games file: 30 of 30.
* Spot check (Retrosheet event files in place of Baseball Reference): 600 of 600 games, 5,400 of 5,400 slots.
* Lineups complete: 367,495 of 367,504. Player coverage at least 99.91% in every decade.

## Phase 3 and 4: tags, patterns, runs over talent (done 02:54)

* Tags built inside `03_player_seasons.py`; `05_lineup_model.py` (30 s) wrote `data/lineup_model.parquet` with 367,495 complete lineups and `data/model_fit.csv` (101 season fits plus the 2026 xwOBA fit; mean R squared 0.076).
* 2026 replication: 2,429 games, 4,855 lineups; shape A −0.082 (SE 0.035) rank 3, B −0.070 rank 12, C +0.023 rank 369; exact A 14 games, 11 and 3. Differences explained in DECISIONS.md.

## Phase 5: core tests (done 03:03, 67 s)

* `06_core_tests.py` wrote 12 tables to `out/tables/`. 1926 to 2026 combined sample: shape A slope −0.001 (SE 0.0035).

## Phase 6: rigor (done 03:17)

* `07_markov.py` (266 s): 54,850 lineups (all 2026 plus 49,995 sampled 1926 to 2025) with actual, shape A and local search best orders.
* `08_rigor.py` (87 s): permutation p value for the best of 512 = 0.117; out of sample A = +0.0002 (SE 0.0036); within team season A 1926 to 2025 = +0.003 (SE 0.004); robustness and manager card tables.

## Phase 8: first version of every deliverable (done 03:23)

* `09_report.py` (13 s): workbook with 9 tabs, 28,386 formulas, 0 errors after LibreOffice recalculation; 5 charts; REPORT.md; SLIDES.md; CHECKS.md (10 of 10 second way checks agree).

## Phase 7: nice to have (done 03:30)

* Handedness: count of adjacent same handed pairs (Lahman `bats`, 2026 from the feed) added as a control. Shape A's slope does not move (1926 to 2025: 0.0002 with or without it; 2026: 0.0816 vs 0.0815 runs per game per slot). Each same handed pair is worth 0.0023 runs per game (SE 0.0026). Table `out/tables/handedness.csv`.
* Leadoff and number 2 profiles by decade (OBP, SLG, K%, P share, each against all starters): `out/tables/leadoff_two_profiles.csv`. Number 2 hitters went from a 29% to 44% P share (1920s to 2010s) to 60% in 2020 to 2026, with SLG 10% above the average starter.
* Interactive page: `out/interactive_charts.html` (Plotly 2.35.2 inlined, works offline; checked in Chromium at desktop and phone width with no script errors).
* Workbook gained a "Rigor Tests" tab and a "Phase 7 Extras" tab beyond the nine requested.

## Reproducibility check (03:31 to 03:42)

* `RUN_ALL.sh --fresh` in a clean copy (sharing `raw/`) ran all nine scripts in 10 minutes 46 seconds with no errors. Headline numbers, rigor numbers, VALIDATION.md, CHECKS.md and eight result tables were identical to the committed run (largest numeric difference 0).

## Phase 9 checklist

| Item | Status | Evidence |
|---|---|---|
| Team season validation reported with match rate | Pass | 2,269 of 2,306 exact (98.4%), every mismatch listed in `out/VALIDATION.md` |
| 2026 matches standings 30 of 30 | Pass, with a substitute source | Wins and losses 30 of 30 vs the final standings (Stats API blocked; Baseball Reference standings read through web search). Runs 30 of 30 vs the box score mirror's games file |
| Baseball Reference spot check reported or block logged | Block logged, substitute run | Baseball Reference refused at the first request (`raw/source_status.txt`, `PROBLEMS.md`). Same 30 team seasons checked against Retrosheet event files: 600 of 600 games, 5,400 of 5,400 slots |
| 2026 replication within rounding | Partly; differences explained | Games 2,429 match; lineups 4,855 vs 4,858; exact A 14 games, 11 and 3 match exactly; A −0.082 (SE 0.035) rank 3 vs −0.090 (0.032) rank 1; B −0.070 rank 12 vs −0.064 rank 22; C +0.023 rank 369 vs +0.019 rank 347. Cause and the 19 variant sweep are in `DECISIONS.md` and `out/tables/sensitivity_2026.csv` |
| Every headline number recomputed a second way | Pass | `out/CHECKS.md`, 10 of 10 agree |
| Workbook opens, recalculates with zero errors, every tab has data | Pass | 11 tabs, 28,653 formulas, 0 errors after LibreOffice recalculation, no empty tab (`out/tables/workbook_check.json`) |
| All five charts exist and read clearly at phone size | Pass | `out/chart_a` to `chart_e`, 1920 by 1080, white, 30 point tick labels and 44 point titles; each checked visually |
| PROGRESS.md ends with runtime, row counts, anything undone | Pass | below |

## Final state

* Total runtime: job started 02:16 UTC and finished 03:43 UTC on October 29, 2026, about 1 hour 27 minutes including source hunting. A clean rerun of the pipeline takes about 11 minutes once `raw/` is downloaded.
* Row counts: `games` 183,752; `lineups` 367,504 (367,495 complete); `lineup_model` 367,495; `player_seasons` 88,977; `pitcher_seasons` 42,637; `pa_2026` 184,284; `markov_lineups` 54,850; `all_512_shapes` 3,584; `exact_shapes` 3,387; `team_seasons` 2,336.
* Left undone or changed from the brief:
  * The MLB Stats API, Savant, Retrosheet's own site, Baseball Reference and the Lahman site were unreachable. Every source came from a GitHub mirror (see `DECISIONS.md`).
  * Savant's own xwOBA and xSLG were replaced by values computed from launch speed and angle, available for 2023 to 2026 only, so tag robustness (b) does not cover 2015 to 2022.
  * The 2026 replication matches on games and exact shape A results but not on A's rank (3 rather than 1), for the reasons documented.
  * The largest csv copies (`lineups.csv`, `lineup_model.csv`, `player_seasons.csv`, `games.csv`) and `lineup_model.parquet` are rebuilt by the scripts rather than committed, to keep the repository small.
