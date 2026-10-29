import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
DATA = ROOT / "data"
SLOTS = range(1, 10)

MLB_TO_RETRO = {"LAA": "ANA", "AZ": "ARI", "ARI": "ARI", "ATH": "ATH", "OAK": "ATH", "ATL": "ATL", "BAL": "BAL",
                "BOS": "BOS", "CWS": "CHA", "CHC": "CHN", "CIN": "CIN", "CLE": "CLE", "COL": "COL", "DET": "DET",
                "HOU": "HOU", "KC": "KCA", "LAD": "LAN", "MIA": "MIA", "MIL": "MIL", "MIN": "MIN", "NYY": "NYA",
                "NYM": "NYN", "PHI": "PHI", "PIT": "PIT", "SD": "SDN", "SEA": "SEA", "SF": "SFN", "STL": "SLN",
                "TB": "TBA", "TEX": "TEX", "TOR": "TOR", "WSH": "WAS"}
AL = {"ANA", "ATH", "BAL", "BOS", "CHA", "CLE", "DET", "HOU", "KCA", "MIN", "NYA", "SEA", "TBA", "TEX", "TOR"}
NOT_PA_END = {"caught_stealing_2b", "caught_stealing_3b", "caught_stealing_home", "pickoff_1b", "pickoff_2b",
              "pickoff_3b", "pickoff_caught_stealing_2b", "pickoff_caught_stealing_3b",
              "pickoff_caught_stealing_home", "other_out", "stolen_base_2b", "stolen_base_3b", "stolen_base_home",
              "wild_pitch", "passed_ball", "balk", "other_advance", "pickoff_error_1b", "pickoff_error_2b",
              "pickoff_error_3b", "runner_double_play", "caught_stealing", "pickoff", "game_advisory",
              "defensive_indiff", "error"}


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} 02_build_games {msg}"
    print(line)
    with open(ROOT / "logs" / "run.log", "a") as f:
        f.write(line + "\n")


def retro_games():
    rows = []
    for y in range(1926, 2026):
        f = [x for x in (RAW / "retrosheet_repo" / "seasons" / str(y)).iterdir() if x.name.upper() == f"GL{y}.TXT"][0]
        g = pd.read_csv(f, header=None, dtype=str, keep_default_na=False)
        g["season"] = y
        rows.append(g)
    g = pd.concat(rows, ignore_index=True)
    out = pd.DataFrame({
        "season": g["season"],
        "date": pd.to_datetime(g[0], format="%Y%m%d"),
        "game_num": g[1],
        "vis": g[3], "vis_lg": g[4], "home": g[6], "home_lg": g[7],
        "vis_score": pd.to_numeric(g[9]), "home_score": pd.to_numeric(g[10]),
        "outs": pd.to_numeric(g[11], errors="coerce"),
        "completion": g[13], "forfeit": g[14], "park": g[16],
        "vis_sp_id": g[101], "vis_sp_name": g[102], "home_sp_id": g[103], "home_sp_name": g[104],
        "acquisition": g[160],
    })
    out["game_key"] = out.home + g[0] + out.game_num
    for side, base in [("vis", 105), ("home", 132)]:
        for s in SLOTS:
            i = base + (s - 1) * 3
            out[f"{side}_p{s}_id"] = g[i]
            out[f"{side}_p{s}_name"] = g[i + 1]
            out[f"{side}_p{s}_pos"] = pd.to_numeric(g[i + 2], errors="coerce")
    out = out[out.vis_lg.isin(["AL", "NL"]) & out.home_lg.isin(["AL", "NL"])].reset_index(drop=True)
    out["source"] = "retrosheet"
    return out


def feed_pitches():
    files = sorted((RAW / "pitchfeed_repo" / "data" / "raw" / "2026" / "monthly").glob("*.parquet"))
    cols = ["game_pk", "game_date", "home_team", "away_team", "venue", "inning", "top_bottom", "pitcher_id",
            "pitcher_name", "batter_id", "batter_name", "batter_hand", "pitcher_hand", "outs", "at_bat_number",
            "pitch_number", "events", "is_in_play", "launch_speed", "launch_angle", "call_description"]
    return pd.concat([pd.read_parquet(f, columns=cols) for f in files], ignore_index=True)


def feed_boxscores():
    rows = []
    for f in sorted((RAW / "boxfeed_repo" / "feed").glob("boxscore_2026-*.json")):
        day = f.stem.split("_")[1]
        for g in json.loads(f.read_text()):
            ls = g.get("linescore") or {}
            rows.append({"game_pk": g["pk"], "box_date": day, "series": g.get("series"),
                         "away_abbrev": g["away"]["abbrev"], "home_abbrev": g["home"]["abbrev"],
                         "away_runs": ls.get("a_r"), "home_runs": ls.get("h_r"),
                         "innings": len(ls.get("innings") or []),
                         "home_batted_last": (ls.get("home") or [None])[-1] is not None})
    return pd.DataFrame(rows).drop_duplicates("game_pk", keep="last")


def plate_appearances(p):
    p = p.sort_values(["game_pk", "at_bat_number", "pitch_number"])
    pa = p.groupby(["game_pk", "at_bat_number"], as_index=False).agg(
        game_date=("game_date", "first"), home_team=("home_team", "first"), away_team=("away_team", "first"),
        venue=("venue", "first"), inning=("inning", "first"), top_bottom=("top_bottom", "first"),
        pitcher_id=("pitcher_id", "first"), pitcher_name=("pitcher_name", "first"),
        batter_id=("batter_id", "first"), batter_name=("batter_name", "first"),
        batter_hand=("batter_hand", "first"), outs_start=("outs", "first"), event=("events", "last"))
    pa["gap"] = False
    pa["boundary"] = False
    add = []
    for gpk, x in pa.groupby("game_pk", sort=False):
        nums = x.at_bat_number.to_numpy()
        have = set(nums.tolist())
        for m in range(int(nums.max()) + 1):
            if m in have:
                continue
            after = x[x.at_bat_number > m].head(1)
            before = x[x.at_bat_number < m].tail(1)
            ref = after.iloc[0] if len(after) else before.iloc[0]
            boundary = bool(len(after) and len(before) and (after.iloc[0].inning, after.iloc[0].top_bottom) != (before.iloc[0].inning, before.iloc[0].top_bottom))
            add.append({"game_pk": gpk, "at_bat_number": m, "game_date": ref.game_date,
                        "home_team": ref.home_team, "away_team": ref.away_team, "venue": ref.venue,
                        "inning": ref.inning, "top_bottom": ref.top_bottom, "pitcher_id": ref.pitcher_id,
                        "pitcher_name": ref.pitcher_name, "batter_id": np.nan, "batter_name": "",
                        "batter_hand": "", "outs_start": np.nan, "event": "missing", "gap": True,
                        "boundary": boundary})
    pa = pd.concat([pa, pd.DataFrame(add)], ignore_index=True).sort_values(["game_pk", "at_bat_number"])
    pa["bat_side"] = np.where(pa.top_bottom == "Top", "away", "home")
    return pa.reset_index(drop=True)


def slot_group(x, use_boundary):
    b = x.batter_id.to_numpy(dtype=float).copy()
    ev = x.event.to_numpy()
    inn = x.inning.to_numpy()
    gap = x.gap.to_numpy()
    bnd = x.boundary.to_numpy()
    n = len(x)
    carried = np.zeros(n, bool)
    for i in range(n):
        if gap[i] and bnd[i] and not use_boundary:
            carried[i] = True
        elif ev[i] in NOT_PA_END and not gap[i]:
            j = i + 1
            while j < n and gap[j] and bnd[j]:
                j += 1
            if j < n and b[j] == b[i] and inn[j] > inn[i]:
                carried[i] = True
    slot = np.full(n, np.nan)
    k = 0
    for i in range(n):
        if not carried[i]:
            slot[i] = k % 9 + 1
            k += 1
    for i in range(n - 2, -1, -1):
        if np.isnan(slot[i]):
            slot[i] = slot[i + 1]
    names = x.batter_name.to_numpy().copy()
    hands = x.batter_hand.to_numpy().copy()
    for i in np.where(gap & ~carried)[0]:
        same = [j for j in range(n) if slot[j] == slot[i] and not gap[j] and not carried[j]]
        prev = [j for j in same if j < i]
        nxt = [j for j in same if j > i]
        c = prev[-1] if prev else (nxt[0] if nxt else None)
        if c is not None:
            b[i], names[i], hands[i] = b[c], names[c], hands[c]
    ok = True
    real = ~carried & ~np.isnan(b)
    seen_slot = {}
    for i in np.where(real)[0]:
        if seen_slot.setdefault(b[i], slot[i]) != slot[i]:
            ok = False
    for s in range(1, 10):
        seq = [b[i] for i in np.where(real & (slot == s))[0]]
        runs = [v for j, v in enumerate(seq) if j == 0 or seq[j - 1] != v]
        if len(runs) != len(set(runs)):
            ok = False
    y = x.copy()
    y["batter_id"], y["batter_name"], y["batter_hand"] = b, names, hands
    y["carried"], y["slot"] = carried, slot
    return y, ok


def assign_slots(pa):
    out, bad = [], set()
    for (g, side), x in pa.groupby(["game_pk", "bat_side"], sort=False):
        y, ok = slot_group(x, False)
        if not ok and x.boundary.any():
            y2, ok2 = slot_group(x, True)
            if ok2:
                y, ok = y2, ok2
        if not ok:
            bad.add((g, side))
        out.append(y)
    return pd.concat(out, ignore_index=True), bad


def feed_games():
    p = feed_pitches()
    box = feed_boxscores()
    reg = box[box.series == "Regular Season"]
    p = p[p.game_pk.isin(reg.game_pk)]
    log(f"2026 feed: {p.game_pk.nunique()} regular season games with pitches, {len(reg)} regular season box scores")
    pa, bad = assign_slots(plate_appearances(p))
    pa.to_parquet(DATA / "pa_2026.parquet", index=False)
    rows = []
    for gpk, x in pa.groupby("game_pk"):
        b = reg[reg.game_pk == gpk]
        if b.empty:
            continue
        b = b.iloc[0]
        r0 = x.iloc[0]
        home = MLB_TO_RETRO.get(r0.home_team, r0.home_team)
        vis = MLB_TO_RETRO.get(r0.away_team, r0.away_team)
        rec = {"season": 2026, "date": pd.to_datetime(r0.game_date), "game_num": "0", "vis": vis,
               "vis_lg": "AL" if vis in AL else "NL", "home": home, "home_lg": "AL" if home in AL else "NL",
               "vis_score": b.away_runs, "home_score": b.home_runs, "completion": "", "forfeit": "",
               "park": r0.venue, "acquisition": "Y", "game_pk": gpk}
        outs = 0
        for side, opp in [("vis", "home"), ("home", "vis")]:
            bs = "away" if side == "vis" else "home"
            y = x[(x.bat_side == bs) & ~x.carried].sort_values("at_bat_number")
            first9 = y.head(9)
            ok = len(first9) == 9 and first9.batter_id.notna().all() and first9.batter_id.nunique() == 9
            if ok and (gpk, bs) in bad:
                ok = not (x.gap & (x.at_bat_number < first9.at_bat_number.max())).any()
            for s in SLOTS:
                rr = first9[first9.slot == s]
                rec[f"{side}_p{s}_id"] = str(int(rr.batter_id.iloc[0])) if len(rr) and pd.notna(rr.batter_id.iloc[0]) else ""
                rec[f"{side}_p{s}_name"] = rr.batter_name.iloc[0] if len(rr) else ""
                rec[f"{side}_p{s}_pos"] = np.nan
            rec[f"{side}_lineup_ok"] = ok
            rec[f"{side}_gap_in_first9"] = bool(first9.gap.any())
            opp_bs = "home" if bs == "away" else "away"
            sp = x[x.bat_side == opp_bs].sort_values("at_bat_number").iloc[0]
            rec[f"{opp}_sp_id"] = str(int(sp.pitcher_id))
            rec[f"{opp}_sp_name"] = sp.pitcher_name
        innings_away = int(x[x.bat_side == "away"].inning.max())
        innings_home = int(x[x.bat_side == "home"].inning.max()) if (x.bat_side == "home").any() else 0
        rec["outs"] = 3 * innings_away + 3 * innings_home
        rows.append(rec)
    g = pd.DataFrame(rows)
    g["game_key"] = g.home + g.date.dt.strftime("%Y%m%d") + g.game_pk.astype(str)
    g["source"] = "mlb_feed"
    log(f"2026 games built: {len(g)}; lineups flagged by cycle check: {len(bad)}")
    return g


def to_lineups(g):
    parts = []
    for side, opp in [("vis", "home"), ("home", "vis")]:
        d = pd.DataFrame({
            "season": g.season, "date": g.date, "game_key": g.game_key, "team": g[side], "opponent": g[opp],
            "league": g[f"{side}_lg"], "opp_league": g[f"{opp}_lg"], "home": int(side == "home"), "park": g.park,
            "runs": g[f"{side}_score"], "runs_allowed": g[f"{opp}_score"], "outs": g.outs,
            "opp_sp_id": g[f"{opp}_sp_id"], "opp_sp_name": g[f"{opp}_sp_name"], "own_sp_id": g[f"{side}_sp_id"],
            "acquisition": g.acquisition, "forfeit": g.forfeit, "source": g.source})
        for s in SLOTS:
            d[f"p{s}_id"] = g[f"{side}_p{s}_id"].values
            d[f"p{s}_name"] = g[f"{side}_p{s}_name"].values
            d[f"p{s}_pos"] = g[f"{side}_p{s}_pos"].values
        if f"{side}_lineup_ok" in g:
            d["feed_cycle_ok"] = g[f"{side}_lineup_ok"].values
            d["feed_gap_first9"] = g[f"{side}_gap_in_first9"].values
        parts.append(d)
    lu = pd.concat(parts, ignore_index=True)
    lu["win"] = np.where(lu.runs > lu.runs_allowed, 1.0, np.where(lu.runs < lu.runs_allowed, 0.0, np.nan))
    lu["tie"] = lu.runs == lu.runs_allowed
    ids = lu[[f"p{s}_id" for s in SLOTS]]
    pos = lu[[f"p{s}_pos" for s in SLOTS]]
    missing = (ids == "").any(axis=1) | ids.isna().any(axis=1)
    retro_pos_missing = (lu.source == "retrosheet") & (pos.isna() | (pos < 1) | (pos > 10)).any(axis=1)
    lu["complete"] = ~(missing | retro_pos_missing)
    if "feed_cycle_ok" in lu:
        lu.loc[lu.source == "mlb_feed", "complete"] &= lu.loc[lu.source == "mlb_feed", "feed_cycle_ok"].astype(bool)
    lu["n_pitchers_batting"] = (pos == 1).sum(axis=1)
    return lu.sort_values(["season", "date", "game_key", "home"]).reset_index(drop=True)


def main():
    t0 = time.time()
    if (DATA / "lineups.parquet").exists() and (DATA / "games.parquet").exists():
        log("outputs exist, skipping")
        return
    g = retro_games()
    log(f"Retrosheet games 1926 to 2025: {len(g)}")
    g26 = feed_games()
    games = pd.concat([g, g26], ignore_index=True)
    vis_ids = games[[f"vis_p{s}_id" for s in SLOTS]]
    home_ids = games[[f"home_p{s}_id" for s in SLOTS]]
    games["missing_starter"] = (vis_ids == "").any(axis=1) | (home_ids == "").any(axis=1)
    lu = to_lineups(games)
    games.to_parquet(DATA / "games.parquet", index=False)
    lu.to_parquet(DATA / "lineups.parquet", index=False)
    lu.drop(columns=[c for c in lu.columns if c.endswith("_name")]).to_csv(DATA / "lineups.csv", index=False)
    games[["season", "date", "game_key", "vis", "home", "vis_score", "home_score", "outs", "park", "acquisition",
           "missing_starter"]].to_csv(DATA / "games.csv", index=False)
    log(f"games {len(games)}, lineups {len(lu)}, complete {int(lu.complete.sum())}, in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
