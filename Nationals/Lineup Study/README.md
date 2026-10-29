# Power vs contact batting order study, 1926 to 2026

One hundred years of MLB starting lineups, tagged power lean (P) or contact lean (C) within each season, tested against the 2026 finding that the shape P P C C P C C P C scores more than lineup talent predicts.

Start with `out/REPORT.md` (one page) and `out/Lineup_Study_1926_2026.xlsx`.

## Run order

`./RUN_ALL.sh` runs everything in order; `./RUN_ALL.sh --fresh` clears `data/`, `out/` and `logs/` first. Each script skips work whose output already exists, so a crash resumes where it stopped. Delete a script's outputs to force it to run again.

| Script | What it does | Main outputs | Time on 4 cores |
|---|---|---|---|
| `01_download.py` | Clones the GitHub mirrors, converts Lahman, picks the 30 spot check team seasons, records which hosts are blocked | `raw/` | 4 minutes |
| `02_build_games.py` | Retrosheet game logs 1926 to 2025 plus 2026 rebuilt from the live feed mirror | `data/games.parquet`, `data/lineups.parquet`, `data/pa_2026.parquet` | 2 minutes |
| `03_player_seasons.py` | Player batting and pitching seasons, xSLG and xwOBA from launch data, P and C tags, talent inputs, event rates | `data/player_seasons.parquet`, `data/pitcher_seasons.parquet` | 20 seconds |
| `04_validate.py` | All validation checks | `out/VALIDATION.md`, `data/validation_*.csv` | 25 seconds |
| `05_lineup_model.py` | Patterns, distances to shapes A, B and C, lineup talent, within season expected runs model | `data/lineup_model.parquet`, `data/model_fit.csv` | 30 seconds |
| `06_core_tests.py` | Phase 5 tests | `out/tables/*.csv`, `out/tables/headline.json` | 1 minute |
| `07_markov.py` | Markov run expectancy for actual, shape A and best orders | `data/markov_lineups.parquet` | 5 minutes |
| `08_rigor.py` | Permutation test, out of sample, team season fixed effects, robustness, manager card | `out/tables/*.csv`, `out/tables/rigor_headline.json` | 1.5 minutes |
| `09_report.py` | Charts, workbook (with LibreOffice recalculation), report, slides, second way checks | `out/` | 15 seconds |

Python 3 with pandas, numpy, statsmodels, scipy, matplotlib, openpyxl, pyarrow, requests and rdata. LibreOffice is used to recalculate the workbook.

## Data sources

The container this ran in could not reach retrosheet.org, statsapi.mlb.com, baseballsavant.mlb.com, baseball-reference.com or seanlahman.com, so every source is a public GitHub mirror. See `DECISIONS.md` for each choice and `PROBLEMS.md` for what was blocked.

* Retrosheet game logs and event files: github.com/chadwickbureau/retrosheet (the information used here was obtained free of charge from and is copyrighted by Retrosheet, www.retrosheet.org).
* Lahman database 2026 edition (1871 to 2025): github.com/cdalzell/Lahman, the Lahman R package.
* Chadwick register for MLBAM to Retrosheet IDs: github.com/chadwickbureau/register.
* 2026 pitch by pitch MLB Stats API live feed: github.com/lancebroz/mlb-pitcher-data.
* 2026 box score summaries from the Stats API: github.com/toolstem/daily-box-score.
* 2026 final standings (wins and losses only), read from the Baseball Reference standings page through a web search: `raw/manual/standings_2026_websearch.csv`.

## Folder layout

* `raw/` downloads, untouched (not committed except `raw/manual/`, rebuilt by `01_download.py`)
* `data/` cleaned tables (the largest csv copies and `lineup_model.parquet` are not committed; rerun to rebuild them)
* `scripts/` the nine numbered scripts
* `out/` deliverables: `REPORT.md`, `SLIDES.md`, `VALIDATION.md`, `CHECKS.md`, the workbook, five charts and `tables/`
* `logs/run.log`, `PROGRESS.md`, `DECISIONS.md`, `PROBLEMS.md`
