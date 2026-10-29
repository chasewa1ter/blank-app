# Validation

All numbers below come from `scripts/04_validate.py` and the csv files it writes to `data/`.

## 1. Team seasons 1926 to 2025: game logs vs Lahman Teams

* Team seasons compared: 2306. Exact match on all four of games, wins, runs scored and runs allowed: 2269 of 2306 (98.4%).
* Games match: 2304 of 2306. Wins match: 2292 of 2306. Runs match: 2303 of 2306. Runs allowed match: 2287 of 2306.
* Largest absolute gaps: games 1, wins 1, runs 2, runs allowed 4.
* Summed over all mismatched team seasons the runs gap is 2 and the runs allowed gap is 2 out of 1,617,098 runs.

Every mismatch (game logs minus Lahman):

| Season | Team | dG | dW | dR | dRA |
|---|---|---|---|---|---|
| 1931 | SLA | 0 | 0 | -1 | 0 |
| 1931 | WS1 | 0 | 0 | 0 | -1 |
| 1932 | NYA | 0 | 1 | 0 | 0 |
| 1937 | CIN | 0 | 0 | 0 | -1 |
| 1937 | NYA | 0 | 1 | 0 | 0 |
| 1937 | PIT | 0 | 0 | 0 | 1 |
| 1937 | SLN | 0 | -1 | 0 | 0 |
| 1938 | CHN | 0 | 0 | 0 | -1 |
| 1938 | SLN | 0 | 0 | 0 | 1 |
| 1939 | CHA | 0 | 1 | 0 | 0 |
| 1940 | CHA | 0 | 1 | 0 | 0 |
| 1941 | BOS | 0 | -1 | 0 | 0 |
| 1941 | WS1 | 0 | 1 | 0 | 0 |
| 1942 | BRO | 0 | 0 | 0 | 2 |
| 1942 | BSN | 0 | -1 | 0 | 0 |
| 1942 | NY1 | 0 | 1 | 0 | 0 |
| 1942 | SLN | 0 | 0 | 0 | -2 |
| 1943 | BRO | 0 | 0 | 0 | 1 |
| 1943 | CHN | 0 | 0 | 0 | -1 |
| 1945 | NY1 | 0 | 0 | 0 | 1 |
| 1945 | SLN | 0 | 0 | 0 | -1 |
| 1947 | BRO | 0 | 0 | 0 | -1 |
| 1947 | BSN | 0 | 0 | 0 | 4 |
| 1947 | CHN | 0 | 0 | 2 | 0 |
| 1947 | PIT | 0 | 0 | 1 | 0 |
| 1948 | BRO | 0 | 0 | 0 | 2 |
| 1948 | CHN | 0 | 0 | 0 | -1 |
| 1948 | CIN | 0 | 0 | 0 | -1 |
| 1948 | NY1 | 0 | 0 | 0 | -1 |
| 1948 | PHI | 0 | 0 | 0 | -1 |
| 1948 | PIT | 0 | 0 | 0 | 2 |
| 1954 | PHI | 0 | -1 | 0 | 0 |
| 1971 | NYA | 0 | -1 | 0 | 0 |
| 1971 | WS2 | 0 | 1 | 0 | 0 |
| 1974 | TEX | 0 | -1 | 0 | 0 |
| 1979 | CHA | 1 | 0 | 0 | 0 |
| 1979 | DET | 1 | -1 | 0 | 0 |

## 2. 2026 team records

The MLB Stats API standings endpoint was blocked in this container. Two substitutes were used.

* Wins and losses vs the final 2026 standings (Baseball Reference standings page, read through a web search on October 29, 2026 and saved in `raw/manual/standings_2026_websearch.csv`): 30 of 30 teams match exactly. Total wins 2429, total games 2429.
* Runs scored and runs allowed vs the separate daily games file of the box score mirror (`feed/games_2026-*.json`): 30 of 30 teams match exactly. No external source for 2026 runs could be reached, so this is a consistency check between two files built from the Stats API.

| Team | W | L | W standings | L standings | R | RA | R games file | RA games file |
|---|---|---|---|---|---|---|---|---|
| ANA | 62 | 100 | 62 | 100 | 655 | 752 | 655 | 752 |
| ARI | 86 | 76 | 86 | 76 | 739 | 730 | 739 | 730 |
| ATH | 64 | 98 | 64 | 98 | 699 | 937 | 699 | 937 |
| ATL | 94 | 68 | 94 | 68 | 742 | 626 | 742 | 626 |
| BAL | 79 | 82 | 79 | 82 | 718 | 739 | 718 | 739 |
| BOS | 87 | 75 | 87 | 75 | 689 | 611 | 689 | 611 |
| CHA | 84 | 78 | 84 | 78 | 776 | 720 | 776 | 720 |
| CHN | 89 | 73 | 89 | 73 | 850 | 703 | 850 | 703 |
| CIN | 75 | 87 | 75 | 87 | 666 | 826 | 666 | 826 |
| CLE | 85 | 77 | 85 | 77 | 678 | 667 | 678 | 667 |
| COL | 58 | 104 | 58 | 104 | 752 | 944 | 752 | 944 |
| DET | 76 | 86 | 76 | 86 | 723 | 652 | 723 | 652 |
| HOU | 81 | 81 | 81 | 81 | 734 | 766 | 734 | 766 |
| KCA | 69 | 93 | 69 | 93 | 690 | 810 | 690 | 810 |
| LAN | 100 | 62 | 100 | 62 | 801 | 600 | 801 | 600 |
| MIA | 80 | 82 | 80 | 82 | 715 | 712 | 715 | 712 |
| MIL | 103 | 59 | 103 | 59 | 832 | 618 | 832 | 618 |
| MIN | 77 | 85 | 77 | 85 | 739 | 797 | 739 | 797 |
| NYA | 93 | 68 | 93 | 68 | 739 | 601 | 739 | 601 |
| NYN | 74 | 88 | 74 | 88 | 699 | 731 | 699 | 731 |
| PHI | 88 | 74 | 88 | 74 | 713 | 698 | 713 | 698 |
| PIT | 82 | 80 | 82 | 80 | 767 | 739 | 767 | 739 |
| SDN | 91 | 71 | 91 | 71 | 722 | 681 | 722 | 681 |
| SEA | 76 | 86 | 76 | 86 | 664 | 722 | 664 | 722 |
| SFN | 65 | 97 | 65 | 97 | 669 | 760 | 669 | 760 |
| SLN | 77 | 85 | 77 | 85 | 720 | 749 | 720 | 749 |
| TBA | 98 | 64 | 98 | 64 | 736 | 650 | 736 | 650 |
| TEX | 80 | 82 | 80 | 82 | 673 | 719 | 673 | 719 |
| TOR | 79 | 83 | 79 | 83 | 648 | 694 | 648 | 694 |
| WAS | 77 | 85 | 77 | 85 | 821 | 815 | 821 | 815 |

## 3. Spot check of 30 random team seasons (Baseball Reference substitute)

Baseball Reference refused the connection at the first request (`raw/source_status.txt`), so no Baseball Reference page could be fetched and the 6 second rule never came into play. The same 30 team seasons (3 drawn at random from each decade, seed 2026, list in `raw/spotcheck_seasons.csv`) were checked against Retrosheet's event files instead: play by play, deduced and box score files that Retrosheet compiles separately from the game logs. Scores come from the line score in box score files and from runs counted in the play strings otherwise.

* Games checked: 600. Found in the event files: 600 of 600.
* Date and game number match: 600 of 600. Score match: 600 of 600.
* Starting lineup slots match (player and order): 5400 of 5400.
* Games matching on date, score and all nine slots: 600 of 600.

| Season | Team | Games | Score ok | Slots ok |
|---|---|---|---|---|
| 1926 | CHN | 20 | 20 | 180 of 180 |
| 1927 | PIT | 20 | 20 | 180 of 180 |
| 1934 | CLE | 20 | 20 | 180 of 180 |
| 1936 | PIT | 20 | 20 | 180 of 180 |
| 1939 | PHI | 20 | 20 | 180 of 180 |
| 1940 | NYA | 20 | 20 | 180 of 180 |
| 1953 | BOS | 20 | 20 | 180 of 180 |
| 1953 | SLA | 20 | 20 | 180 of 180 |
| 1954 | CHA | 20 | 20 | 180 of 180 |
| 1957 | WS1 | 20 | 20 | 180 of 180 |
| 1962 | SLN | 20 | 20 | 180 of 180 |
| 1964 | NYA | 20 | 20 | 180 of 180 |
| 1967 | SFN | 20 | 20 | 180 of 180 |
| 1973 | HOU | 20 | 20 | 180 of 180 |
| 1975 | NYA | 20 | 20 | 180 of 180 |
| 1982 | BAL | 20 | 20 | 180 of 180 |
| 1982 | DET | 20 | 20 | 180 of 180 |
| 1983 | MON | 20 | 20 | 180 of 180 |
| 1992 | MON | 20 | 20 | 180 of 180 |
| 1992 | PHI | 20 | 20 | 180 of 180 |
| 1994 | COL | 20 | 20 | 180 of 180 |
| 1997 | NYN | 20 | 20 | 180 of 180 |
| 1998 | SLN | 20 | 20 | 180 of 180 |
| 1999 | KCA | 20 | 20 | 180 of 180 |
| 2006 | TEX | 20 | 20 | 180 of 180 |
| 2011 | CLE | 20 | 20 | 180 of 180 |
| 2014 | MIA | 20 | 20 | 180 of 180 |
| 2016 | BOS | 20 | 20 | 180 of 180 |
| 2022 | NYA | 20 | 20 | 180 of 180 |
| 2024 | COL | 20 | 20 | 180 of 180 |

## 4. Lineup completeness

* Team games with nine identified starters: 367,495 of 367,504 (99.998%). Incomplete lineups (9) are excluded from every test.
* Seasons below 100%: 1937 (2 missing), 1954 (2 missing), 1979 (2 missing), 2026 (3 missing)
* 2026: 4855 of 4858 lineups complete. Three 2026 lineups fall in stretches where the feed lost pitch tracking before the ninth batter came up and are excluded.

## 5. Player coverage

Share of lineup slots whose player season has batting stats:

| Decade | Slots | With stats | Share |
|---|---|---|---|
| 1920s | 88,740 | 88,736 | 99.9955% |
| 1930s | 221,598 | 221,572 | 99.9883% |
| 1940s | 222,768 | 222,752 | 99.9928% |
| 1950s | 222,732 | 222,540 | 99.9138% |
| 1960s | 287,298 | 287,278 | 99.9930% |
| 1970s | 356,508 | 356,477 | 99.9913% |
| 1980s | 366,066 | 366,035 | 99.9915% |
| 1990s | 388,692 | 388,683 | 99.9977% |
| 2000s | 437,238 | 437,219 | 99.9957% |
| 2010s | 437,346 | 437,309 | 99.9915% |
| 2020s | 278,550 | 278,523 | 99.9903% |

## 6. Extra 2026 checks of the rebuilt lineups and batting lines

* Starters whose surname appears in that team's batting list in the box score mirror for the same gamePk: 43,695 of 43,695 (100.00%).
* Team season hits, home runs, walks and strikeouts rebuilt from the live feed vs the sum of the box score mirror (the box score counts include automatic intentional walks, which the pitch feed has no pitch for and which were restored from gaps in the at bat index):

| Team | H | H box | HR | HR box | BB | BB box | SO | SO box |
|---|---|---|---|---|---|---|---|---|
| ATH | 1344 | 1345 | 194 | 194 | 519 | 520 | 1371 | 1373 |
| ATL | 1348 | 1348 | 204 | 204 | 465 | 465 | 1310 | 1310 |
| AZ | 1341 | 1341 | 166 | 166 | 541 | 541 | 1194 | 1195 |
| BAL | 1256 | 1256 | 199 | 199 | 586 | 586 | 1518 | 1518 |
| BOS | 1327 | 1327 | 163 | 163 | 517 | 517 | 1326 | 1326 |
| CHC | 1398 | 1398 | 220 | 220 | 674 | 674 | 1344 | 1345 |
| CIN | 1230 | 1231 | 212 | 213 | 557 | 557 | 1543 | 1544 |
| CLE | 1288 | 1291 | 162 | 162 | 573 | 574 | 1270 | 1271 |
| COL | 1399 | 1399 | 180 | 180 | 500 | 500 | 1409 | 1409 |
| CWS | 1281 | 1282 | 210 | 211 | 589 | 589 | 1493 | 1494 |
| DET | 1315 | 1315 | 181 | 181 | 585 | 585 | 1411 | 1411 |
| HOU | 1320 | 1320 | 226 | 226 | 530 | 530 | 1343 | 1343 |
| KC | 1346 | 1346 | 170 | 170 | 512 | 512 | 1272 | 1272 |
| LAA | 1265 | 1266 | 154 | 154 | 511 | 511 | 1549 | 1550 |
| LAD | 1399 | 1399 | 204 | 204 | 628 | 628 | 1267 | 1267 |
| MIA | 1347 | 1347 | 168 | 168 | 552 | 552 | 1337 | 1337 |
| MIL | 1421 | 1422 | 153 | 154 | 666 | 668 | 1381 | 1383 |
| MIN | 1337 | 1337 | 187 | 187 | 507 | 507 | 1297 | 1297 |
| NYM | 1308 | 1308 | 204 | 204 | 528 | 528 | 1361 | 1361 |
| NYY | 1249 | 1250 | 222 | 223 | 572 | 572 | 1477 | 1480 |
| PHI | 1301 | 1301 | 182 | 182 | 529 | 529 | 1318 | 1318 |
| PIT | 1404 | 1404 | 186 | 186 | 568 | 568 | 1505 | 1505 |
| SD | 1314 | 1314 | 183 | 183 | 554 | 554 | 1310 | 1310 |
| SEA | 1253 | 1253 | 182 | 182 | 557 | 557 | 1399 | 1400 |
| SF | 1341 | 1341 | 178 | 178 | 449 | 449 | 1342 | 1342 |
| STL | 1305 | 1306 | 167 | 167 | 510 | 511 | 1306 | 1306 |
| TB | 1398 | 1405 | 169 | 169 | 512 | 514 | 1136 | 1145 |
| TEX | 1296 | 1296 | 183 | 183 | 525 | 525 | 1389 | 1389 |
| TOR | 1346 | 1346 | 152 | 152 | 459 | 459 | 1149 | 1149 |
| WSH | 1355 | 1355 | 210 | 210 | 556 | 555 | 1350 | 1350 |
| All | 39832 | 39849 | 5571 | 5575 | 16331 | 16337 | 40677 | 40700 |
