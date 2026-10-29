# Decisions

Every judgment call made while the job ran unattended. Newest decisions are appended at the bottom of each section.

## Location and storage

* The job ran in a cloud container, not on the Mac. `~/Desktop/Nationals/Lineup Study/` was created as a symlink to `blank-app/Nationals/Lineup Study/` inside the `chasewa1ter/blank-app` repository so the work could be committed and pushed to branch `claude/mlb-lineups-power-contact-vff02x`. Large raw downloads (`raw/`) are listed in `.gitignore` and are rebuilt by `scripts/01_download.py`.

## Data sources (the network policy of this container blocked several of the named hosts)

* retrosheet.org, statsapi.mlb.com, baseballsavant.mlb.com, baseball-reference.com and seanlahman.com all returned a proxy refusal (see `raw/source_status.txt` and `PROBLEMS.md`). Public GitHub repositories could be cloned, so every source below is a GitHub mirror.
* Game logs 1926 to 2025: the Chadwick Bureau Retrosheet mirror (`github.com/chadwickbureau/retrosheet`, branch master, files `seasons/YYYY/GLYYYY.TXT`). This is the fallback named in the brief.
* `glfields.txt` could not be downloaded from retrosheet.org. The field layout in the brief was checked against the data instead: field 106 holds a Retrosheet player ID, 107 a name, 108 a position code 1 to 10, field 161 the acquisition flag (Y, T, D, N), and visiting and home scores summed to team season runs match Lahman (see VALIDATION.md).
* Lahman: `github.com/chadwickbureau/baseballdatabank` is no longer reachable. The Lahman R package repository (`github.com/cdalzell/Lahman`, version 14.0-0 dated 2026-02-11, the 2026 edition of the database) covers 1871 to 2025 and was used. Its `.RData` tables were converted to CSV with the `rdata` Python package. No season needed the Retrosheet plays fallback.
* 2026 season: the MLB Stats API and Savant were blocked. Two public mirrors of the Stats API were used:
  * `github.com/lancebroz/mlb-pitcher-data`: every pitch of every 2026 game from the Stats API live feed (`/api/v1.1/game/{gamePk}/feed/live`), with gamePk, batter and pitcher MLBAM IDs, inning, half inning, atBatIndex, the play result `eventType`, launch speed and launch angle. Starting lineups, batting lines, pitcher lines and the xwOBA inputs were rebuilt from it.
  * `github.com/toolstem/daily-box-score`: daily Stats API box score summaries keyed by gamePk, with line scores and the game type label. Used for final scores and to keep regular season games only.
* Baseball Reference spot check: blocked at the first request (no request ever reached the site, so rule 0.5 was never at risk). Fallback: the same 30 randomly drawn team seasons were checked against Retrosheet's separately compiled event files (play by play, deduced and box score files), comparing date, score and all nine starters in order for the first 20 games. This is an internal consistency check, not a fully independent source, and is labeled that way.

## Building 2026 lineups from the live feed

* Starting lineups were rebuilt from the order of plate appearances: each team's plate appearances in a game are numbered in sequence and slot = position in the sequence modulo 9. A plate appearance that ended on a caught stealing or pickoff for the third out, with the same batter leading off the next inning, does not advance the order.
* The feed stores only plays with at least one tracked pitch. Automatic intentional walks have no pitch, so they leave a gap in the at bat index (498 gaps in 371 games). A gap inside a half inning was restored as an intentional walk for the batter whose turn it was. A gap at a half inning boundary is ambiguous (inning ending pickoff with no pitch, or a leadoff intentional walk). It is first treated as a non plate appearance; if that breaks the batting order cycle it is treated as a plate appearance for the next half inning instead.
* A lineup was kept when the first nine plate appearances had nine distinct batters, and either the whole game passed the cycle check or no plays were missing before the ninth batter came up. 4,855 of 4,858 team games passed. The three excluded lineups come from games where the feed lost pitch tracking for whole innings before the order turned over.
* A starter replaced before his first plate appearance would be recorded as his replacement. This cannot be detected without the boxscore batting order, and it affects very few games.
* Opponent starting pitcher = first pitcher the team faced. Pitcher innings were counted from the out count recorded before each play.
* 2026 FIP constant: there is no earned run data in the feed, so league ERA was set to 0.92 times league runs per 9 innings. The constant only shifts every pitcher equally within the season, so it has no effect on the within season model.
* Game length in outs for 2026 is approximate (3 outs per half inning batted). It is not used by any test.

## Hitter tags and talent

* Shrinkage uses PA as the sample size: shrunk = (PA × value + prior × pool mean) / (PA + prior), with prior 200 for SLG and ISO and 60 for K%. The pool mean is the simple mean of the 250+ PA pool.
* Percentiles use the brief's formula against the pool's raw (unshrunk) values.
* Tag (b) robustness: Savant's xSLG could not be downloaded. xSLG and xwOBA were computed here from launch speed and launch angle in the live feed mirror (2023 to 2026 only, the seasons the mirror holds). Each batted ball gets the season average total bases (or wOBA value) of batted balls in its 2 mph by 3 degree bin, falling back to a 6 mph by 9 degree bin when a fine bin has fewer than 25 balls. 2015 to 2022 could not be covered, so tag (b) is reported for 2023 to 2026 only.
* xwOBA weights (unintentional BB 0.69, HBP 0.72, 1B 0.88, 2B 1.25, 3B 1.58, HR 2.03) are fixed recent FanGraphs style values.
* Lineup talent: relative OPS = OBP/lgOBP + SLG/lgSLG − 1, with league = the player's primary league that season (most PA). It is shrunk with a 200 PA prior toward the PA weighted mean of his group that season. Pitchers (more than half of their games as pitcher in Lahman Appearances) shrink toward the pitcher mean, everyone else toward the position player mean, so a pitcher's weak bat is not pulled up to league average.
* Opponent starter rate: FIP style = (13 HR + 3 (BB + HBP) − 2 SO) / IP + season constant, shrunk with a 50 IP prior toward league ERA.
* Expected runs model, fitted separately for each season: OLS of runs on talent, opponent starter FIP, opponent season RA per game, home and park dummies.

## Samples and eras

* Main sample = lineups with nine P or C tags (no pitcher batting, no missing tag). Secondary sample = non DH lineups with exactly one pitcher batting; the pitcher's slot is skipped when measuring distance (8 counted slots).
* Era is set by the DH rule actually used in the game: a lineup with a DH starter in 1973 to 2021 is AL DH, one without is NL non DH. Interleague games follow the home park's rule, and 2020 (universal DH) falls under AL DH. All 2022 to 2026 games are universal DH.
* Pre DH 1926 to 1972 and NL non DH results come from the secondary sample, because almost no lineup from those games is free of a batting pitcher.

## 2026 replication (checklist item)

| Quantity | Brief | This study | Note |
|---|---|---|---|
| Games, lineups | 2,429 and 4,858 | 2,429 and 4,855 | 3 lineups dropped where the feed lost whole innings |
| Shape A slope (SE), rank | −0.090 (0.032), 1 | −0.082 (0.035), 3 | best is P P C P P C C P C at −0.088; A is 0.006 behind |
| Shape B slope (SE), rank | −0.064 (0.030), 22 | −0.070 (0.027), 12 | |
| Shape C slope, rank | +0.019, 347 | +0.023, 369 | |
| Exact shape A lineups | 14 games, 11 and 3 | 14 games, 11 and 3 | exact match |

Why they differ, and what was tried. Every variant was run on 2026 by `scripts/sensitivity_2026.py` (not part of RUN_ALL), results in `out/tables/sensitivity_2026.csv`:
* The tags agree: the 14 exact shape A games and their 11 and 3 record match exactly.
* The talent definition does not matter: shrinking toward 1.0 instead of the group mean, no shrinkage, raw OPS, or OPS shrunk to the mean all give A between −0.079 and −0.083 with rank 2 or 3.
* The tag pool and shrinkage do not matter much: 200 or 300 PA pools, PA weighted pool mean and shrinking by AB give −0.081 to −0.083, rank 2 to 4. Removing shrinkage altogether drops A to −0.056 (rank 50), so the brief's numbers clearly used shrinkage.
* The expected runs model matters most: dropping park dummies gives −0.091 (rank 2), dropping opponent RA per game −0.086, and the xwOBA talent version gives −0.085 with rank 1.
* Remaining causes are data differences: batting lines rebuilt from the feed rather than the official Stats API season totals (team hits differ by 17 of 39,849), opponent starter lines rebuilt from the feed, and the 3 excluded lineups. Because the top shapes sit within 0.006 runs of each other, these small differences reorder ranks 1 to 3.
* Decision: keep the specification written in the brief. None of the variants changes any conclusion, and all out of sample results are flat under every variant.

## Rigor choices

* Permutation test: within each 2026 team season, the P and C tags of the team's hitters are shuffled among those same hitters (team P and C counts preserved), patterns are rebuilt, the 512 slopes are recomputed and the most negative is kept. 1,000 shuffles, seed 2026. The real best is compared with the null distribution of the best.
* Bonferroni style bar: z for a two sided 0.05 test spread over 512 shapes, 3.90.
* Out of sample decade estimates use 1926 to 2025 only (the 2020s bin stops at 2025). Combined estimate = inverse variance weighted mean of decade slopes, reported next to the pooled regression.
* Fit and test splits pick the shape with the most negative slope in one period and report its slope and rank in the other.
* Strict tag: N when the SLG and contact percentiles are within 10 points. N slots are skipped like pitchers and the number of counted slots is added as a control.
* Season length groups: 154 game seasons are 1926 to 1960 and the 1961 NL; shortened seasons are 1972, 1981, 1994, 1995 and 2020; all others 162.
* Markov model: event rates per player season shrunk with a 100 PA prior toward his group (pitchers or position players). Advancement: runner on 2nd scores on a single 60%, runner on 1st to 3rd on a single 30% when 3rd is open, runner on 1st scores on a double 40%, double play on 22% of non strikeout outs with a runner on 1st and fewer than 2 outs, runner on 3rd scores and runner on 2nd advances on 30% of other outs with fewer than 2 outs. Expected runs over exactly 9 innings with the batter carried. The model reads 11% to 25% low because it has no steals, errors or extra innings, so order effects are multiplied by actual runs over Markov runs for the same lineups.
* Shape A rearrangement: within the non pitcher slots, A's P slots get the P hitters (best by relative OPS if there are too many; the C hitters with the highest SLG fill in if there are too few), A's C slots get the rest, and each group keeps the manager's original relative order.
* Best order: local search from the actual order, trying all 36 swaps and keeping the best, until no swap helps (at most 12 rounds).
* Historical Markov sample: 5,000 random complete lineups from each decade 1926 to 2025 (seed 2026), 49,995 after dropping 5 with a missing event rate, plus all 4,855 lineups of 2026.
* Logistic win model: average marginal effect computed as coefficient times the mean of p(1 minus p); its SE uses the same scaling. Parks with fewer than 200 games in the sample are pooled into one dummy.
