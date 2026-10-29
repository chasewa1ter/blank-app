import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
DATA = ROOT / "data"
OUT = ROOT / "out"
MLB_TO_RETRO = {"LAA": "ANA", "AZ": "ARI", "ATH": "ATH", "OAK": "ATH", "CWS": "CHA", "CHC": "CHN", "KC": "KCA",
                "LAD": "LAN", "NYY": "NYA", "NYM": "NYN", "SD": "SDN", "SF": "SFN", "STL": "SLN", "TB": "TBA",
                "WSH": "WAS"}


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} 04_validate {msg}"
    print(line)
    with open(ROOT / "logs" / "run.log", "a") as f:
        f.write(line + "\n")


def team_seasons(lu):
    t = lu[lu.season <= 2025].groupby(["season", "team"]).agg(
        G=("runs", "size"), W=("win", lambda x: (x == 1).sum()), R=("runs", "sum"), RA=("runs_allowed", "sum")).reset_index()
    lah = pd.read_csv(RAW / "lahman_csv" / "Teams.csv")
    lah = lah[(lah.yearID >= 1926) & (lah.yearID <= 2025) & lah.lgID.isin(["AL", "NL"])]
    lah = lah.rename(columns={"yearID": "season", "teamIDretro": "team"})[["season", "team", "name", "G", "W", "R", "RA"]]
    m = lah.merge(t, on=["season", "team"], how="outer", suffixes=("_lahman", "_gl"))
    for c in ["G", "W", "R", "RA"]:
        m[f"d{c}"] = m[f"{c}_gl"] - m[f"{c}_lahman"]
    m["exact"] = (m[["dG", "dW", "dR", "dRA"]] == 0).all(axis=1)
    return m


def standings_2026(lu):
    l = lu[lu.season == 2026]
    t = l.groupby("team").agg(G=("runs", "size"), W=("win", lambda x: (x == 1).sum()), R=("runs", "sum"), RA=("runs_allowed", "sum"))
    t["L"] = t.G - t.W
    s = pd.read_csv(RAW / "manual" / "standings_2026_websearch.csv").set_index("team")
    rows = []
    for f in sorted((RAW / "boxfeed_repo" / "feed").glob("games_2026-*.json")):
        for g in json.loads(f.read_text()):
            rows.append({"date": f.stem.split("_")[1], "away": MLB_TO_RETRO.get(g["away_abbrev"], g["away_abbrev"]),
                         "home": MLB_TO_RETRO.get(g["home_abbrev"], g["home_abbrev"]),
                         "a": g["away_score"], "h": g["home_score"]})
    gf = pd.DataFrame(rows)
    gf = gf[gf.away.isin(t.index) & gf.home.isin(t.index)]
    reg_dates = l.date.dt.strftime("%Y-%m-%d").unique()
    gf = gf[gf.date.isin(reg_dates) & gf.date.le(l.date.max().strftime("%Y-%m-%d"))]
    r1 = gf.groupby("away").agg(R=("a", "sum"), RA=("h", "sum"))
    r2 = gf.groupby("home").agg(R=("h", "sum"), RA=("a", "sum"))
    tg = r1.add(r2, fill_value=0)
    m = t.join(s[["W", "L"]], rsuffix="_standings").join(tg, rsuffix="_gamesfeed")
    m["wl_match"] = (m.W == m.W_standings) & (m.L == m.L_standings)
    m["runs_match"] = (m.R == m.R_gamesfeed) & (m.RA == m.RA_gamesfeed)
    return m.reset_index()


def count_runs(play):
    basic, _, adv = play.partition(".")
    runs = 0
    toks = [t for t in adv.split(";") if t]
    batter_explicit = False
    third_explicit = False
    for t in toks:
        m = re.match(r"([B123])([-X])([123H])(.*)", t)
        if not m:
            continue
        if m.group(1) == "B":
            batter_explicit = True
        if m.group(1) == "3":
            third_explicit = True
        if m.group(3) == "H":
            if m.group(2) == "-":
                runs += 1
            elif "E" in m.group(4).split(")")[0]:
                runs += 1
    head = re.split(r"[/.]", basic)[0]
    if re.match(r"^(HR|H)(\d|$)", head) and not batter_explicit:
        runs += 1
    if "SBH" in basic and not third_explicit:
        runs += basic.count("SBH")
    return runs


def parse_events(year):
    games = {}
    d = RAW / "retrosheet_repo" / "seasons" / str(year)
    files = [f for f in d.iterdir() if re.search(r"\.(EV|EB|ED)[ANE]$", f.name.upper()) and "WS" not in f.name.upper()[4:7]]
    for f in files:
        cur = None
        for line in f.read_text(errors="replace").splitlines():
            p = line.split(",")
            if p[0] == "id":
                cur = {"id": p[1], "start": {0: {}, 1: {}}, "runs": [0, 0], "line": [None, None], "file": f.name}
                games[p[1]] = cur
            elif cur is None:
                continue
            elif p[0] == "start" and len(p) >= 6:
                cur["start"][int(p[3])][int(p[4])] = p[1]
            elif p[0] == "play" and len(p) >= 7:
                cur["runs"][int(p[2])] += count_runs(",".join(p[6:]))
            elif p[0] == "line" and len(p) >= 3:
                cur["line"][int(p[1])] = sum(int(x) for x in p[2:] if x.strip().lstrip("-").isdigit())
    return games


def spot_check(lu):
    spot = pd.read_csv(RAW / "spotcheck_seasons.csv")
    rows = []
    cache = {}
    for _, s in spot.iterrows():
        y = int(s.yearID)
        if y not in cache:
            cache[y] = parse_events(y)
        ev = cache[y]
        x = lu[(lu.season == y) & (lu.team == s.teamIDretro)].sort_values(["date", "game_key"]).head(20)
        for _, r in x.iterrows():
            e = ev.get(r.game_key)
            side = int(r.home)
            if e is None:
                rows.append({"season": y, "team": r.team, "game_key": r.game_key, "found": False, "date_ok": False,
                             "score_ok": False, "slots_ok": 0, "file": ""})
                continue
            lines = e["line"]
            score = (lines[side], lines[1 - side]) if lines[0] is not None else (e["runs"][side], e["runs"][1 - side])
            slots_ok = sum(e["start"][side].get(k) == r[f"p{k}_id"] for k in range(1, 10))
            rows.append({"season": y, "team": r.team, "game_key": r.game_key, "found": True, "date_ok": True,
                         "score_ok": score == (r.runs, r.runs_allowed), "gl_score": f"{int(r.runs)}-{int(r.runs_allowed)}",
                         "ev_score": f"{score[0]}-{score[1]}", "slots_ok": slots_ok, "file": e["file"]})
    return pd.DataFrame(rows)


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z ]", "", s)


def feed_name_check(lu):
    g = pd.read_parquet(DATA / "games.parquet", columns=["game_key", "game_pk", "source"])
    g = g[g.source == "mlb_feed"].set_index("game_key").game_pk
    box = {}
    for f in sorted((RAW / "boxfeed_repo" / "feed").glob("boxscore_2026-*.json")):
        for b in json.loads(f.read_text()):
            box[b["pk"]] = b
    l = lu[(lu.season == 2026) & lu.complete]
    hit = tot = 0
    for _, r in l.iterrows():
        b = box.get(int(g[r.game_key]))
        if b is None:
            continue
        side = "home" if r.home == 1 else "away"
        sur = [norm(x["name"].split(",")[0]) for x in b[side]["batting"]]
        for k in range(1, 10):
            full = norm(r[f"p{k}_name"])
            tot += 1
            hit += any(s and s.strip() in full for s in sur)
    return hit, tot


def feed_batting_check():
    pa = pd.read_parquet(DATA / "pa_2026.parquet")
    pa = pa[~pa.carried & pa.batter_id.notna()]
    pa["team"] = np.where(pa.bat_side == "away", pa.away_team, pa.home_team)
    e = pa.event
    pa["H"] = e.isin(["single", "double", "triple", "home_run"]).astype(int)
    pa["HR"] = (e == "home_run").astype(int)
    pa["BB"] = e.isin(["walk", "intent_walk", "missing"]).astype(int)
    pa["SO"] = e.isin(["strikeout", "strikeout_double_play", "strikeout_triple_play"]).astype(int)
    ours = pa.groupby("team")[["H", "HR", "BB", "SO"]].sum()
    reg = set(pd.read_parquet(DATA / "games.parquet", columns=["game_pk"]).game_pk.dropna().astype(int))
    rows = []
    for f in sorted((RAW / "boxfeed_repo" / "feed").glob("boxscore_2026-*.json")):
        for b in json.loads(f.read_text()):
            if b["pk"] not in reg or b.get("series") != "Regular Season":
                continue
            for side in ["away", "home"]:
                for x in b[side]["batting"]:
                    rows.append({"team": b[side]["abbrev"], "H": x["H"], "HR": x["HR"], "BB": x["BB"], "SO": x["SO"]})
    bx = pd.DataFrame(rows).groupby("team").sum()
    return ours.join(bx, rsuffix="_box")


def main():
    t0 = time.time()
    if (OUT / "VALIDATION.md").exists():
        log("output exists, skipping")
        return
    lu = pd.read_parquet(DATA / "lineups.parquet")
    ps = pd.read_parquet(DATA / "player_seasons.parquet", columns=["season", "player_id", "PA"])
    ts = team_seasons(lu)
    ts.to_csv(DATA / "validation_team_seasons.csv", index=False)
    st = standings_2026(lu)
    st.to_csv(DATA / "validation_2026_standings.csv", index=False)
    sc = spot_check(lu)
    sc.to_csv(DATA / "validation_spotcheck.csv", index=False)
    comp = lu.groupby("season").agg(team_games=("complete", "size"), complete=("complete", "sum")).reset_index()
    comp["share"] = comp.complete / comp.team_games
    comp.to_csv(DATA / "validation_completeness.csv", index=False)
    have = set(zip(ps[ps.PA > 0].season, ps[ps.PA > 0].player_id))
    rows = []
    for k in range(1, 10):
        x = lu[["season", f"p{k}_id"]].rename(columns={f"p{k}_id": "pid"})
        x["has"] = [(s, p) in have for s, p in zip(x.season, x.pid)]
        rows.append(x)
    cov = pd.concat(rows)
    cov["decade"] = (cov.season // 10) * 10
    covd = cov.groupby("decade").agg(slots=("has", "size"), with_stats=("has", "sum")).reset_index()
    covd["share"] = covd.with_stats / covd.slots
    covd.to_csv(DATA / "validation_coverage.csv", index=False)
    hit, tot = feed_name_check(lu)
    fb = feed_batting_check()
    fb.to_csv(DATA / "validation_2026_batting.csv")

    n = len(ts)
    exact = int(ts.exact.sum())
    mism = ts[~ts.exact].copy()
    L = ["# Validation", "", "All numbers below come from `scripts/04_validate.py` and the csv files it writes to `data/`.", ""]
    L += ["## 1. Team seasons 1926 to 2025: game logs vs Lahman Teams", "",
          f"* Team seasons compared: {n}. Exact match on all four of games, wins, runs scored and runs allowed: {exact} of {n} ({exact / n:.1%}).",
          f"* Games match: {int((ts.dG == 0).sum())} of {n}. Wins match: {int((ts.dW == 0).sum())} of {n}. Runs match: {int((ts.dR == 0).sum())} of {n}. Runs allowed match: {int((ts.dRA == 0).sum())} of {n}.",
          f"* Largest absolute gaps: games {int(ts.dG.abs().max())}, wins {int(ts.dW.abs().max())}, runs {int(ts.dR.abs().max())}, runs allowed {int(ts.dRA.abs().max())}.",
          f"* Summed over all mismatched team seasons the runs gap is {int(mism.dR.sum())} and the runs allowed gap is {int(mism.dRA.sum())} out of {int(ts.R_lahman.sum()):,} runs.",
          "", "Every mismatch (game logs minus Lahman):", "",
          "| Season | Team | dG | dW | dR | dRA |", "|---|---|---|---|---|---|"]
    for _, r in mism.sort_values(["season", "team"]).iterrows():
        L.append(f"| {int(r.season)} | {r.team} | {int(r.dG)} | {int(r.dW)} | {int(r.dR)} | {int(r.dRA)} |")
    wl = int(st.wl_match.sum())
    rm = int(st.runs_match.sum())
    L += ["", "## 2. 2026 team records", "",
          "The MLB Stats API standings endpoint was blocked in this container. Two substitutes were used.", "",
          f"* Wins and losses vs the final 2026 standings (Baseball Reference standings page, read through a web search on October 29, 2026 and saved in `raw/manual/standings_2026_websearch.csv`): {wl} of 30 teams match exactly. Total wins {int(st.W.sum())}, total games {int(st.G.sum() / 2)}.",
          f"* Runs scored and runs allowed vs the separate daily games file of the box score mirror (`feed/games_2026-*.json`): {rm} of 30 teams match exactly. No external source for 2026 runs could be reached, so this is a consistency check between two files built from the Stats API.",
          "", "| Team | W | L | W standings | L standings | R | RA | R games file | RA games file |", "|---|---|---|---|---|---|---|---|---|"]
    for _, r in st.sort_values("team").iterrows():
        L.append(f"| {r.team} | {int(r.W)} | {int(r.L)} | {int(r.W_standings)} | {int(r.L_standings)} | {int(r.R)} | {int(r.RA)} | {int(r.R_gamesfeed)} | {int(r.RA_gamesfeed)} |")
    found = sc[sc.found]
    gm = int((found.score_ok & (found.slots_ok == 9)).sum())
    L += ["", "## 3. Spot check of 30 random team seasons (Baseball Reference substitute)", "",
          "Baseball Reference refused the connection at the first request (`raw/source_status.txt`), so no Baseball Reference page could be fetched and the 6 second rule never came into play. The same 30 team seasons (3 drawn at random from each decade, seed 2026, list in `raw/spotcheck_seasons.csv`) were checked against Retrosheet's event files instead: play by play, deduced and box score files that Retrosheet compiles separately from the game logs. Scores come from the line score in box score files and from runs counted in the play strings otherwise.", "",
          f"* Games checked: {len(sc)}. Found in the event files: {int(sc.found.sum())} of {len(sc)}.",
          f"* Date and game number match: {int(sc.date_ok.sum())} of {len(sc)}. Score match: {int(sc.score_ok.sum())} of {len(sc)}.",
          f"* Starting lineup slots match (player and order): {int(sc.slots_ok.sum())} of {len(sc) * 9}.",
          f"* Games matching on date, score and all nine slots: {gm} of {len(sc)}.", "",
          "| Season | Team | Games | Score ok | Slots ok |", "|---|---|---|---|---|"]
    for (y, tm), x in sc.groupby(["season", "team"]):
        L.append(f"| {y} | {tm} | {len(x)} | {int(x.score_ok.sum())} | {int(x.slots_ok.sum())} of {len(x) * 9} |")
    bad = sc[sc.found & ~sc.score_ok]
    if len(bad):
        L += ["", "Score mismatches (game log vs event file, own team first):", ""]
        for _, r in bad.iterrows():
            L.append(f"* {r.game_key} ({r.team}): game log {r.gl_score}, event file {r.ev_score} ({r.file})")
    L += ["", "## 4. Lineup completeness", "",
          f"* Team games with nine identified starters: {int(comp.complete.sum()):,} of {int(comp.team_games.sum()):,} ({comp.complete.sum() / comp.team_games.sum():.3%}). Incomplete lineups ({int(comp.team_games.sum() - comp.complete.sum())}) are excluded from every test.",
          f"* Seasons below 100%: " + ", ".join(f"{int(r.season)} ({int(r.team_games - r.complete)} missing)" for _, r in comp[comp.share < 1].iterrows()),
          f"* 2026: {int(comp[comp.season == 2026].complete.iloc[0])} of {int(comp[comp.season == 2026].team_games.iloc[0])} lineups complete. Three 2026 lineups fall in stretches where the feed lost pitch tracking before the ninth batter came up and are excluded.",
          "", "## 5. Player coverage", "", "Share of lineup slots whose player season has batting stats:", "",
          "| Decade | Slots | With stats | Share |", "|---|---|---|---|"]
    for _, r in covd.iterrows():
        L.append(f"| {int(r.decade)}s | {int(r.slots):,} | {int(r.with_stats):,} | {r.share:.4%} |")
    L += ["", "## 6. Extra 2026 checks of the rebuilt lineups and batting lines", "",
          f"* Starters whose surname appears in that team's batting list in the box score mirror for the same gamePk: {hit:,} of {tot:,} ({hit / tot:.2%}).",
          "* Team season hits, home runs, walks and strikeouts rebuilt from the live feed vs the sum of the box score mirror (the box score counts include automatic intentional walks, which the pitch feed has no pitch for and which were restored from gaps in the at bat index):", "",
          "| Team | H | H box | HR | HR box | BB | BB box | SO | SO box |", "|---|---|---|---|---|---|---|---|---|"]
    for tm, r in fb.iterrows():
        L.append(f"| {tm} | {int(r.H)} | {int(r.H_box)} | {int(r.HR)} | {int(r.HR_box)} | {int(r.BB)} | {int(r.BB_box)} | {int(r.SO)} | {int(r.SO_box)} |")
    tot_line = fb.sum()
    L += [f"| All | {int(tot_line.H)} | {int(tot_line.H_box)} | {int(tot_line.HR)} | {int(tot_line.HR_box)} | {int(tot_line.BB)} | {int(tot_line.BB_box)} | {int(tot_line.SO)} | {int(tot_line.SO_box)} |"]
    (OUT / "VALIDATION.md").write_text("\n".join(L) + "\n")
    log(f"team seasons exact {exact}/{n}; 2026 W-L {wl}/30, runs {rm}/30; spot games {gm}/{len(sc)}; in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
