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
