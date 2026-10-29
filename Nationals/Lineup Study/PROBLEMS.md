# Problems

Blocks and failures hit during the run, with the fallback used. Lines starting with a timestamp were written by the scripts.

* 2026-10-29 02:34 (01_download) retrosheet.org unreachable (error ProxyError: HTTPSConnectionPool(host='www.retrosheet.org', port=443): Max retries exceeded with url: /gamelogs/glfields.txt (Caused by ProxyError('Unable to conne). Fallback used, see DECISIONS.md.
* 2026-10-29 02:34 (01_download) statsapi.mlb.com unreachable (error ProxyError: HTTPSConnectionPool(host='statsapi.mlb.com', port=443): Max retries exceeded with url: /api/v1/standings?leagueId=103,104&season=2026 (Caused by Proxy). Fallback used, see DECISIONS.md.
* 2026-10-29 02:34 (01_download) baseballsavant.mlb.com unreachable (error ProxyError: HTTPSConnectionPool(host='baseballsavant.mlb.com', port=443): Max retries exceeded with url: /leaderboard/expected_statistics?type=batter&year=2026&po). Fallback used, see DECISIONS.md.
* 2026-10-29 02:34 (01_download) baseball-reference.com unreachable (error ProxyError: HTTPSConnectionPool(host='www.baseball-reference.com', port=443): Max retries exceeded with url: /teams/WSN/2019-batting-orders.shtml (Caused by Proxy). Fallback used, see DECISIONS.md.
* 2026-10-29 02:20 (setup) seanlahman.com refused by the proxy; github.com/chadwickbureau/baseballdatabank is no longer available (404 on raw files, add_repo reports no access). Fallback: Lahman R package repository, 2026 edition.
* 2026-10-29 02:20 (setup) Savant leaderboards (percentile rankings, expected stats, EV, sprint speed) unreachable. Fallback: xSLG and xwOBA computed from launch speed and angle in the live feed mirror for 2023 to 2026. Percentile rankings and sprint speed were not used anywhere.
* 2026-10-29 02:20 (setup) retrosheet.org `glfields.txt` unreachable. The field layout was checked against the data instead (see DECISIONS.md).
* 2026-10-29 02:44 (02_build_games) 52 of 4,858 rebuilt 2026 lineups first failed the batting order cycle check. Cause: plays with no tracked pitch at half inning boundaries were credited to the wrong team. Fixed with the two pass rule in DECISIONS.md; 3 lineups remain excluded because the feed lost whole innings.
* 2026-10-29 02:58 (06_core_tests) killed for running out of memory inside statsmodels' logit marginal effects. Fixed by computing the average marginal effect in closed form (coefficient times mean p(1 minus p)) and loading fewer columns.
* 2026-10-29 03:07 (07_markov) first solver took 2 ms per lineup order, too slow for the local search. Rewritten to use the cyclic batting order structure (8 by 8 blocks); results identical to 1e-14, 25 times faster.
* 2026 replication differs slightly from the brief (see DECISIONS.md, "2026 replication").
