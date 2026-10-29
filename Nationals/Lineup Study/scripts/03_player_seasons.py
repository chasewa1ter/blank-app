import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
DATA = ROOT / "data"
LAH = RAW / "lahman_csv"
BAT = ["AB", "H", "2B", "3B", "HR", "BB", "IBB", "HBP", "SF", "SH", "SO", "GIDP"]
HITS = {"single": 1, "double": 2, "triple": 3, "home_run": 4}
AB_OUTS = {"field_out", "force_out", "grounded_into_double_play", "grounded_into_triple_play", "double_play",
           "triple_play", "fielders_choice", "fielders_choice_out", "field_error", "strikeout",
           "strikeout_double_play", "strikeout_triple_play", "batter_interference"}
KS = {"strikeout", "strikeout_double_play", "strikeout_triple_play"}
WOBA_W = {"BB": 0.69, "HBP": 0.72, 1: 0.88, 2: 1.25, 3: 1.58, 4: 2.03}
AL = {"ANA", "ATH", "BAL", "BOS", "CHA", "CLE", "DET", "HOU", "KCA", "MIN", "NYA", "SEA", "TBA", "TEX", "TOR"}
MLB_TO_RETRO = {"LAA": "ANA", "AZ": "ARI", "ATH": "ATH", "OAK": "ATH", "CWS": "CHA", "CHC": "CHN", "KC": "KCA",
                "LAD": "LAN", "NYY": "NYA", "NYM": "NYN", "SD": "SDN", "SF": "SFN", "STL": "SLN", "TB": "TBA",
                "WSH": "WAS"}


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} 03_player_seasons {msg}"
    print(line)
    with open(ROOT / "logs" / "run.log", "a") as f:
        f.write(line + "\n")


def pct_against(values, pool):
    pool = np.sort(np.asarray(pool, dtype=float))
    lo = np.searchsorted(pool, values, side="left")
    hi = np.searchsorted(pool, values, side="right")
    return (lo + 0.5 * (hi - lo)) / len(pool) * 100


def rates(df):
    df["PA"] = df.AB + df.BB + df.HBP + df.SF + df.SH
    df["TB"] = df.H + df["2B"] + 2 * df["3B"] + 3 * df.HR
    df["SLG"] = np.where(df.AB > 0, df.TB / df.AB.where(df.AB > 0), np.nan)
    df["ISO"] = np.where(df.AB > 0, (df.TB - df.H) / df.AB.where(df.AB > 0), np.nan)
    den = df.AB + df.BB + df.HBP + df.SF
    df["OBP"] = np.where(den > 0, (df.H + df.BB + df.HBP) / den.where(den > 0), np.nan)
    df["K_pct"] = np.where(df.PA > 0, df.SO / df.PA.where(df.PA > 0), np.nan)
    return df


def lahman_batting():
    b = pd.read_csv(LAH / "Batting.csv")
    b = b[(b.yearID >= 1926) & (b.yearID <= 2025) & b.lgID.isin(["AL", "NL"])]
    for c in BAT:
        b[c] = pd.to_numeric(b[c], errors="coerce").fillna(0)
    b["PA_stint"] = b.AB + b.BB + b.HBP + b.SF + b.SH
    prim = b.sort_values("PA_stint", ascending=False).drop_duplicates(["playerID", "yearID"])[["playerID", "yearID", "lgID"]]
    s = b.groupby(["playerID", "yearID"], as_index=False)[BAT].sum().merge(prim, on=["playerID", "yearID"])
    ppl = pd.read_csv(LAH / "People.csv", usecols=["playerID", "retroID", "nameFirst", "nameLast", "bats"])
    s = s.merge(ppl, on="playerID", how="left")
    app = pd.read_csv(LAH / "Appearances.csv", usecols=["yearID", "playerID", "G_all", "G_p"])
    app = app.groupby(["playerID", "yearID"], as_index=False)[["G_all", "G_p"]].sum()
    s = s.merge(app, on=["playerID", "yearID"], how="left")
    s["is_pitcher"] = s.G_p.fillna(0) > 0.5 * s.G_all.fillna(0)
    s = s.rename(columns={"yearID": "season", "lgID": "league"})
    s["player_id"] = s.retroID
    s["name"] = s.nameFirst.fillna("") + " " + s.nameLast.fillna("")
    s["source"] = "lahman"
    return s.drop(columns=["nameFirst", "nameLast"])


def feed_pa_2026():
    pa = pd.read_parquet(DATA / "pa_2026.parquet")
    return pa[~pa.carried & pa.batter_id.notna()].copy()


def event_counts(pa, key):
    e = pa.event
    pa["AB"] = (e.isin(HITS.keys()) | e.isin(AB_OUTS)).astype(int)
    pa["H"] = e.isin(HITS.keys()).astype(int)
    pa["2B"] = (e == "double").astype(int)
    pa["3B"] = (e == "triple").astype(int)
    pa["HR"] = (e == "home_run").astype(int)
    pa["IBB"] = (e.isin(["intent_walk", "missing"])).astype(int)
    pa["BB"] = (e.isin(["walk", "intent_walk", "missing"])).astype(int)
    pa["HBP"] = (e == "hit_by_pitch").astype(int)
    pa["SF"] = e.isin(["sac_fly", "sac_fly_double_play"]).astype(int)
    pa["SH"] = e.isin(["sac_bunt", "sac_bunt_double_play"]).astype(int)
    pa["SO"] = e.isin(KS).astype(int)
    pa["GIDP"] = (e == "grounded_into_double_play").astype(int)
    return pa.groupby(key, as_index=False)[BAT].sum()


def batting_2026():
    pa = feed_pa_2026()
    pa["team"] = np.where(pa.bat_side == "away", pa.away_team, pa.home_team)
    pa["team"] = pa.team.map(lambda t: MLB_TO_RETRO.get(t, t))
    s = event_counts(pa, ["batter_id"])
    tm = pa.groupby(["batter_id", "team"]).size().reset_index(name="n").sort_values("n").drop_duplicates("batter_id", keep="last")
    nm = pa.groupby("batter_id").agg(name=("batter_name", "first"), bats=("batter_hand", lambda x: "B" if x.nunique() > 1 else x.iloc[0]))
    s = s.merge(tm[["batter_id", "team"]], on="batter_id").merge(nm, on="batter_id")
    s["league"] = np.where(s.team.isin(AL), "AL", "NL")
    s["season"] = 2026
    s["player_id"] = s.batter_id.astype(int).astype(str)
    s["playerID"] = s.player_id
    s["is_pitcher"] = False
    s["source"] = "mlb_feed"
    return s.drop(columns=["batter_id", "team"])


def batted_balls(season):
    files = sorted((RAW / "pitchfeed_repo" / "data" / "raw" / str(season) / "monthly").glob("*.parquet"))
    cols = ["game_pk", "game_date", "at_bat_number", "pitch_number", "batter_id", "events", "is_in_play",
            "launch_speed", "launch_angle"]
    p = pd.concat([pd.read_parquet(f, columns=cols) for f in files], ignore_index=True)
    if season < 2026:
        g = pd.read_parquet(DATA / "games.parquet", columns=["season", "date"])
        last_day = g[g.season == season].date.max()
        p = p[pd.to_datetime(p.game_date) <= last_day]
    p = p.sort_values(["game_pk", "at_bat_number", "pitch_number"])
    last = p.groupby(["game_pk", "at_bat_number"]).tail(1)
    return last


def expected_values(last):
    bb = last[last.is_in_play.astype(bool)].copy()
    bb["tb"] = bb.events.map(HITS).fillna(0)
    bb["wv"] = bb.tb.map({0: 0.0, 1: WOBA_W[1], 2: WOBA_W[2], 3: WOBA_W[3], 4: WOBA_W[4]})
    ok = bb.launch_speed.notna() & bb.launch_angle.notna()
    fine = (bb.launch_speed // 2).astype("Int64").astype(str) + "_" + (bb.launch_angle // 3).astype("Int64").astype(str)
    coarse = (bb.launch_speed // 6).astype("Int64").astype(str) + "_" + (bb.launch_angle // 9).astype("Int64").astype(str)
    bb["fine"], bb["coarse"] = fine, coarse
    res = {}
    for col in ["tb", "wv"]:
        f = bb[ok].groupby("fine")[col].agg(["mean", "size"])
        c = bb[ok].groupby("coarse")[col].agg(["mean", "size"])
        x = bb.fine.map(f["mean"].where(f["size"] >= 25))
        x = x.fillna(bb.coarse.map(c["mean"].where(c["size"] >= 25)))
        x = x.where(ok, bb[col]).fillna(bb[col].mean())
        res[col] = x
    bb["x_tb"], bb["x_wv"] = res["tb"], res["wv"]
    return bb


def expected_stats(season, pa_counts):
    last = batted_balls(season)
    bb = expected_values(last)
    x = bb.groupby("batter_id").agg(x_tb=("x_tb", "sum"), x_wv=("x_wv", "sum"), bip=("x_tb", "size"))
    out = pa_counts.set_index("batter_id").join(x, how="left").fillna({"x_tb": 0, "x_wv": 0, "bip": 0})
    out["xSLG"] = np.where(out.AB > 0, out.x_tb / out.AB.where(out.AB > 0), np.nan)
    ubb = out.BB - out.IBB
    den = out.AB + ubb + out.SF + out.HBP
    out["xwOBA"] = np.where(den > 0, (WOBA_W["BB"] * ubb + WOBA_W["HBP"] * out.HBP + out.x_wv) / den.where(den > 0), np.nan)
    return out.reset_index()


def feed_counts(season):
    if season == 2026:
        pa = feed_pa_2026()
        pa["event"] = pa.event
        return event_counts(pa, ["batter_id"])
    last = batted_balls(season)
    last = last.rename(columns={"events": "event"})
    return event_counts(last, ["batter_id"])


def mlbam_to_retro():
    parts = [pd.read_csv(f, usecols=["key_mlbam", "key_retro"], dtype=str) for f in sorted((RAW / "register_repo" / "data").glob("people-*.csv"))]
    reg = pd.concat(parts).dropna()
    return dict(zip(reg.key_mlbam.astype(float).astype(int), reg.key_retro))


def league_rates(seasons_bat):
    t = pd.read_csv(LAH / "Teams.csv")
    t = t[(t.yearID >= 1926) & t.lgID.isin(["AL", "NL"])]
    for c in ["AB", "H", "2B", "3B", "HR", "BB", "HBP", "SF"]:
        t[c] = pd.to_numeric(t[c], errors="coerce").fillna(0)
    lg = t.groupby(["yearID", "lgID"], as_index=False)[["AB", "H", "2B", "3B", "HR", "BB", "HBP", "SF"]].sum()
    lg = lg.rename(columns={"yearID": "season", "lgID": "league"})
    b26 = seasons_bat[seasons_bat.season == 2026].groupby(["season", "league"], as_index=False)[["AB", "H", "2B", "3B", "HR", "BB", "HBP", "SF"]].sum()
    lg = pd.concat([lg, b26], ignore_index=True)
    lg["lgOBP"] = (lg.H + lg.BB + lg.HBP) / (lg.AB + lg.BB + lg.HBP + lg.SF)
    lg["lgSLG"] = (lg.H + lg["2B"] + 2 * lg["3B"] + 3 * lg.HR) / lg.AB
    return lg[["season", "league", "lgOBP", "lgSLG"]]


def shrink(value, n, prior_mean, prior_n):
    v = np.where(np.isnan(value), prior_mean, value)
    return (v * n + prior_mean * prior_n) / (n + prior_n)


def tag_season(d, value_col, k_col="K_pct"):
    pool = d[d.PA >= 250]
    out = {}
    for col, prior in [(value_col, 200), (k_col, 60)]:
        m = pool[col].mean()
        out[col] = shrink(d[col].values.astype(float), d.PA.values, m, prior)
    v_pct = pct_against(out[value_col], pool[value_col].dropna())
    c_pct = 100 - pct_against(out[k_col], pool[k_col].dropna())
    return out[value_col], out[k_col], v_pct, c_pct


def build_tags(ps):
    parts = []
    for y, d in ps.groupby("season"):
        d = d.copy()
        d["SLG_s"], d["K_s"], d["slg_pct"], d["con_pct"] = tag_season(d, "SLG")
        d["ISO_s"], _, d["iso_pct"], _ = tag_season(d, "ISO")
        if d.xSLG.notna().sum() > 100:
            dd = d.copy()
            dd["xSLG"] = dd.xSLG.fillna(dd.SLG)
            d["xSLG_s"], _, d["xslg_pct"], _ = tag_season(dd, "xSLG")
        else:
            d["xSLG_s"], d["xslg_pct"] = np.nan, np.nan
        parts.append(d)
    ps = pd.concat(parts, ignore_index=True)
    ps["tag"] = np.where(ps.slg_pct > ps.con_pct, "P", "C")
    ps["tag_iso"] = np.where(ps.iso_pct > ps.con_pct, "P", "C")
    ps["tag_xslg"] = np.where(ps.xslg_pct.isna(), "", np.where(ps.xslg_pct > ps.con_pct, "P", "C"))
    gap = ps.slg_pct - ps.con_pct
    ps["tag_strict"] = np.where(gap >= 10, "P", np.where(gap <= -10, "C", "N"))
    return ps


def talent(ps, lg):
    ps = ps.merge(lg, on=["season", "league"], how="left")
    ps["rel_ops"] = ps.OBP / ps.lgOBP + ps.SLG / ps.lgSLG - 1
    parts = []
    for (y, pit), d in ps.groupby(["season", "is_pitcher"]):
        d = d.copy()
        w = d.PA.where(d.rel_ops.notna(), 0)
        m = np.average(d.rel_ops.fillna(0), weights=w) if w.sum() > 0 else 1.0
        d["rel_ops_s"] = shrink(d.rel_ops.values.astype(float), d.PA.values, m, 200)
        if d.xwOBA.notna().sum() > 100:
            lgx = np.average(d.xwOBA.fillna(0), weights=d.PA.where(d.xwOBA.notna(), 0))
            d["rel_xwoba"] = d.xwOBA / lgx
            mx = np.average(d.rel_xwoba.fillna(0), weights=d.PA.where(d.rel_xwoba.notna(), 0))
            d["rel_xwoba_s"] = shrink(d.rel_xwoba.values.astype(float), d.PA.values, mx, 200)
        parts.append(d)
    return pd.concat(parts, ignore_index=True)


def event_rates(ps):
    ps["oth_out"] = ps.PA - ps.H - ps.BB - ps.HBP - ps.SO
    ev = {"r1B": ps.H - ps["2B"] - ps["3B"] - ps.HR, "r2B": ps["2B"], "r3B": ps["3B"], "rHR": ps.HR,
          "rBB": ps.BB + ps.HBP, "rK": ps.SO, "rOUT": ps.oth_out}
    for k, v in ev.items():
        ps[k + "_n"] = v
    parts = []
    for (y, pit), d in ps.groupby(["season", "is_pitcher"]):
        d = d.copy()
        tot = sum(d[k + "_n"].sum() for k in ev)
        for k in ev:
            m = d[k + "_n"].sum() / tot
            d[k] = (d[k + "_n"] + 100 * m) / (d.PA.clip(lower=0) + 100)
        s = d[list(ev)].sum(axis=1)
        for k in ev:
            d[k] = d[k] / s
        parts.append(d)
    return pd.concat(parts, ignore_index=True).drop(columns=[k + "_n" for k in ev])


def pitcher_seasons():
    p = pd.read_csv(LAH / "Pitching.csv")
    p = p[(p.yearID >= 1926) & p.lgID.isin(["AL", "NL"])]
    for c in ["HR", "BB", "HBP", "SO", "IPouts", "ER", "BFP"]:
        p[c] = pd.to_numeric(p[c], errors="coerce").fillna(0)
    s = p.groupby(["playerID", "yearID"], as_index=False)[["HR", "BB", "HBP", "SO", "IPouts", "ER", "BFP"]].sum()
    ppl = pd.read_csv(LAH / "People.csv", usecols=["playerID", "retroID"])
    s = s.merge(ppl, on="playerID", how="left").rename(columns={"yearID": "season", "retroID": "player_id"})
    pa = pd.read_parquet(DATA / "pa_2026.parquet")
    pa = pa[~pa.carried]
    pa = pa.sort_values(["game_pk", "bat_side", "at_bat_number"])
    nxt = pa.groupby(["game_pk", "bat_side", "inning"]).outs_start.shift(-1)
    last = nxt.isna()
    pa["outs_made"] = np.where(last, 3 - pa.outs_start, nxt - pa.outs_start)
    walkoff = (pa.bat_side == "home") & last & (pa.inning >= 9)
    gm = pa.groupby("game_pk").inning.transform("max")
    pa.loc[walkoff & (pa.inning == gm), "outs_made"] = np.nan
    pa["outs_made"] = pa.outs_made.clip(lower=0)
    e = pa.event
    q = pd.DataFrame({"player_id": pa.pitcher_id.astype(int).astype(str), "HR": (e == "home_run").astype(int),
                      "BB": e.isin(["walk", "intent_walk", "missing"]).astype(int), "HBP": (e == "hit_by_pitch").astype(int),
                      "SO": e.isin(KS).astype(int), "IPouts": pa.outs_made.fillna(0), "BFP": 1})
    q = q.groupby("player_id", as_index=False).sum()
    q["season"] = 2026
    q["playerID"] = q.player_id
    q["ER"] = np.nan
    s = pd.concat([s, q], ignore_index=True)
    s["IP"] = s.IPouts / 3
    core = (13 * s.HR + 3 * (s.BB + s.HBP) - 2 * s.SO)
    lg = s.groupby("season").agg(core=("HR", lambda x: 0), IP=("IP", "sum"), ER=("ER", "sum"))
    lg["core"] = (13 * s.groupby("season").HR.sum() + 3 * (s.groupby("season").BB.sum() + s.groupby("season").HBP.sum()) - 2 * s.groupby("season").SO.sum()) / lg.IP
    lg["ERA"] = 9 * lg.ER / lg.IP
    g = pd.read_parquet(DATA / "lineups.parquet", columns=["season", "runs", "outs"])
    r26 = g[g.season == 2026]
    lg.loc[2026, "ERA"] = 0.92 * 27 * r26.runs.sum() / (r26.outs.sum() / 2 * 1.0) if len(r26) else np.nan
    lg["cFIP"] = lg.ERA - lg.core
    s = s.merge(lg[["cFIP", "ERA"]].rename(columns={"ERA": "lgERA"}), left_on="season", right_index=True)
    s["FIP"] = np.where(s.IP > 0, core / s.IP.where(s.IP > 0) + s.cFIP, np.nan)
    s["FIP_s"] = shrink(s.FIP.values.astype(float), s.IP.values, s.lgERA.values, 50)
    return s


def main():
    t0 = time.time()
    if (DATA / "player_seasons.parquet").exists() and (DATA / "pitcher_seasons.parquet").exists():
        log("outputs exist, skipping")
        return
    lb = lahman_batting()
    b26 = batting_2026()
    ps = pd.concat([lb, b26], ignore_index=True)
    for c in BAT:
        ps[c] = ps[c].fillna(0)
    ps = rates(ps)
    m2r = mlbam_to_retro()
    xs = []
    for y in [2023, 2024, 2025, 2026]:
        x = expected_stats(y, feed_counts(y))
        x["season"] = y
        x["player_id"] = x.batter_id.astype(int).map(m2r) if y < 2026 else x.batter_id.astype(int).astype(str)
        xs.append(x[["season", "player_id", "xSLG", "xwOBA", "bip"]].dropna(subset=["player_id"]))
        log(f"expected stats {y}: {len(x)} batters")
    xs = pd.concat(xs).drop_duplicates(["season", "player_id"])
    ps = ps.merge(xs, on=["season", "player_id"], how="left")
    ps = build_tags(ps)
    lg = league_rates(ps)
    ps = talent(ps, lg)
    ps = event_rates(ps)
    ps.to_parquet(DATA / "player_seasons.parquet", index=False)
    ps.to_csv(DATA / "player_seasons.csv", index=False)
    pit = pitcher_seasons()
    pit.to_parquet(DATA / "pitcher_seasons.parquet", index=False)
    pit.to_csv(DATA / "pitcher_seasons.csv", index=False)
    lg.to_csv(DATA / "league_rates.csv", index=False)
    log(f"player seasons {len(ps)}, pitcher seasons {len(pit)}, in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
