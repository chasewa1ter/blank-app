import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SLOTS = list(range(1, 10))
WEIGHTS = np.array([4.65, 4.55, 4.44, 4.33, 4.22, 4.10, 3.99, 3.87, 3.75])
SHAPES = {"A": "PPCCPCCPC", "B": "PCPCPCCPC", "C": "CPCPCCPCP"}
PCOLS = ["tag", "tag_iso", "tag_xslg", "tag_strict", "rel_ops_s", "rel_xwoba_s", "SLG", "K_pct", "OBP", "PA",
         "is_pitcher", "bats", "name", "r1B", "r2B", "r3B", "rHR", "rBB", "rK", "rOUT", "SLG_s", "K_s"]


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} 05_lineup_model {msg}"
    print(line)
    with open(ROOT / "logs" / "run.log", "a") as f:
        f.write(line + "\n")


def era_of(season, dh):
    if season <= 1972:
        return "Pre DH 1926 to 1972"
    if season >= 2022:
        return "Universal DH 2022 to 2026"
    return "AL DH 1973 to 2021" if dh else "NL non DH 1973 to 2021"


def distance(pattern_arr, shape):
    s = np.array(list(shape))
    counted = (pattern_arr == "P") | (pattern_arr == "C")
    return ((pattern_arr != s) & counted).sum(axis=1)


def attach_players(lu, ps):
    ps = ps.set_index(["season", "player_id"])[PCOLS]
    ps = ps[~ps.index.duplicated()]
    cols = {}
    for k in SLOTS:
        idx = pd.MultiIndex.from_arrays([lu.season, lu[f"p{k}_id"]])
        x = ps.reindex(idx)
        for c in PCOLS:
            cols[f"s{k}_{c}"] = x[c].values
    return pd.concat([lu, pd.DataFrame(cols, index=lu.index)], axis=1)


def build(lu, ps, pit):
    lu = lu[lu.complete].copy().reset_index(drop=True)
    lu = attach_players(lu, ps)
    pos = lu[[f"p{k}_pos" for k in SLOTS]].to_numpy()
    lu["dh_game"] = (pos == 10).any(axis=1) | (lu.season == 2026)
    lu["era"] = [era_of(s, d) for s, d in zip(lu.season, lu.dh_game)]
    lu["decade"] = (lu.season // 10) * 10
    for name, col in [("pattern", "tag"), ("pattern_iso", "tag_iso"), ("pattern_xslg", "tag_xslg"), ("pattern_strict", "tag_strict")]:
        t = lu[[f"s{k}_{col}" for k in SLOTS]].fillna("").to_numpy().astype(object)
        t = np.where(pos == 1, "X", t)
        t = np.where(t == "", "N", t)
        lu[name] = ["".join(r) for r in t]
        arr = np.array([list(p) for p in lu[name]])
        suffix = name.replace("pattern", "")
        for sh, s in SHAPES.items():
            lu[f"dist_{sh}{suffix}"] = distance(arr, s)
        lu[f"n_counted{suffix}"] = ((arr == "P") | (arr == "C")).sum(axis=1)
    lu["n_nonX"] = lu.pattern.str.count("P") + lu.pattern.str.count("C")
    rel = lu[[f"s{k}_rel_ops_s" for k in SLOTS]].to_numpy(dtype=float)
    fill = pd.Series(np.nanmean(rel, axis=1)).fillna(1.0).to_numpy()
    rel = np.where(np.isnan(rel), fill[:, None], rel)
    lu["talent"] = rel @ WEIGHTS / WEIGHTS.sum()
    rx = lu[[f"s{k}_rel_xwoba_s" for k in SLOTS]].to_numpy(dtype=float)
    lu["talent_x"] = np.where(np.isnan(rx).any(axis=1), np.nan, np.nan_to_num(rx) @ WEIGHTS / WEIGHTS.sum())
    p = pit.set_index(["season", "player_id"]).FIP_s
    p = p[~p.index.duplicated()]
    lu["opp_fip"] = p.reindex(pd.MultiIndex.from_arrays([lu.season, lu.opp_sp_id])).values
    lgfip = pit.groupby("season").lgERA.first()
    lu["opp_fip"] = lu.opp_fip.fillna(lu.season.map(lgfip))
    allg = pd.read_parquet(DATA / "lineups.parquet", columns=["season", "team", "runs_allowed"])
    ra = allg.groupby(["season", "team"]).runs_allowed.mean().rename("opp_ra_g")
    lu = lu.join(ra, on=["season", "opponent"])
    opp = lu[["game_key", "home", "talent", "talent_x"]].copy()
    opp["home"] = 1 - opp.home
    lu = lu.merge(opp.rename(columns={"talent": "opp_talent", "talent_x": "opp_talent_x"}), on=["game_key", "home"], how="left")
    return lu


def fit_season(d, talent_col):
    X = pd.get_dummies(d[["park"]].astype(str), drop_first=True, dtype=float)
    X[talent_col] = d[talent_col].values
    X["opp_fip"] = d.opp_fip.values
    X["opp_ra_g"] = d.opp_ra_g.values
    X["home"] = d.home.values.astype(float)
    X = sm.add_constant(X, has_constant="add")
    m = sm.OLS(d.runs.values.astype(float), X.values).fit()
    names = list(X.columns)
    return m, names


def main():
    t0 = time.time()
    if (DATA / "lineup_model.parquet").exists():
        log("output exists, skipping")
        return
    lu = pd.read_parquet(DATA / "lineups.parquet")
    ps = pd.read_parquet(DATA / "player_seasons.parquet")
    pit = pd.read_parquet(DATA / "pitcher_seasons.parquet")
    lu = build(lu, ps, pit).copy()
    lu["exp_runs"] = np.nan
    lu["exp_runs_x"] = np.nan
    fits = []
    for y, d in lu.groupby("season"):
        m, names = fit_season(d, "talent")
        lu.loc[d.index, "exp_runs"] = m.fittedvalues
        i = names.index("talent")
        rec = {"season": y, "n": int(m.nobs), "r2": m.rsquared, "rmse": np.sqrt(m.mse_resid),
               "b_talent": m.params[i], "se_talent": m.bse[i], "b_opp_fip": m.params[names.index("opp_fip")],
               "b_opp_ra_g": m.params[names.index("opp_ra_g")], "b_home": m.params[names.index("home")],
               "n_parks": sum(1 for n in names if n.startswith("park_")) + 1, "talent_def": "rel OPS"}
        fits.append(rec)
        if y == 2026:
            mx, nx = fit_season(d.dropna(subset=["talent_x"]), "talent_x")
            lu.loc[d.dropna(subset=["talent_x"]).index, "exp_runs_x"] = mx.fittedvalues
            j = nx.index("talent_x")
            fits.append({"season": y, "n": int(mx.nobs), "r2": mx.rsquared, "rmse": np.sqrt(mx.mse_resid),
                         "b_talent": mx.params[j], "se_talent": mx.bse[j], "b_opp_fip": mx.params[nx.index("opp_fip")],
                         "b_opp_ra_g": mx.params[nx.index("opp_ra_g")], "b_home": mx.params[nx.index("home")],
                         "n_parks": sum(1 for n in nx if n.startswith("park_")) + 1, "talent_def": "rel xwOBA"})
    lu = lu.copy()
    lu["rot"] = lu.runs - lu.exp_runs
    lu["rot_x"] = lu.runs - lu.exp_runs_x
    lu["team_season"] = lu.season.astype(str) + "_" + lu.team
    fits = pd.DataFrame(fits)
    fits.to_csv(DATA / "model_fit.csv", index=False)
    lu.to_parquet(DATA / "lineup_model.parquet", index=False)
    keep = ["season", "date", "game_key", "team", "opponent", "league", "home", "park", "era", "decade", "runs",
            "runs_allowed", "win", "pattern", "n_nonX", "dist_A", "dist_B", "dist_C", "talent", "opp_talent",
            "opp_fip", "opp_ra_g", "exp_runs", "rot", "talent_x", "rot_x"]
    lu[keep].to_csv(DATA / "lineup_model.csv", index=False)
    log(f"lineup model rows {len(lu)}, seasons {lu.season.nunique()}, mean r2 {fits[fits.talent_def == 'rel OPS'].r2.mean():.3f}, in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
