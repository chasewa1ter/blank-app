import itertools
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TAB = ROOT / "out" / "tables"
SHAPES = {"A": "PPCCPCCPC", "B": "PCPCPCCPC", "C": "CPCPCCPCP"}
ALL_SHAPES = ["".join(b) for b in itertools.product("PC", repeat=9)]
ERAS = ["Pre DH 1926 to 1972", "AL DH 1973 to 2021", "NL non DH 1973 to 2021", "Universal DH 2022 to 2026"]


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} 06_core_tests {msg}"
    print(line)
    with open(ROOT / "logs" / "run.log", "a") as f:
        f.write(line + "\n")


def load():
    cols = ["season", "date", "game_key", "team", "opponent", "home", "park", "runs", "runs_allowed", "win", "era",
            "decade", "dh_game", "pattern", "n_nonX", "talent", "opp_talent", "opp_fip", "opp_ra_g", "exp_runs", "rot",
            "rot_x", "talent_x", "team_season"] + [f"dist_{s}" for s in SHAPES]
    cols += [f"{a}{k}_{b}" for k in range(1, 10) for a, b in [("p", "id"), ("p", "name"), ("s", "SLG"), ("s", "K_pct"), ("s", "OBP")]]
    lu = pd.read_parquet(DATA / "lineup_model.parquet", columns=cols)
    nx = lu.pattern.str.count("X")
    nn = lu.pattern.str.count("N")
    lu["sample"] = np.where((nx == 0) & (nn == 0), "main",
                            np.where((nx == 1) & (nn == 0) & ~lu.dh_game, "secondary", "other"))
    lu["decade_label"] = lu.decade.astype(str) + "s"
    lu["rpg_both"] = lu.runs + lu.runs_allowed
    return lu


def rpw(d):
    return 10 * np.sqrt(d.rpg_both.mean() / 9)


def cluster_slope(x, y, groups):
    X = sm.add_constant(np.asarray(x, dtype=float))
    m = sm.OLS(np.asarray(y, dtype=float), X).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(groups)[0]})
    return m.params[1], m.bse[1]


def slope_rows(d, label, group, sample):
    rows = []
    if len(d) < 50:
        return rows
    w = rpw(d)
    for s in SHAPES:
        b, se = cluster_slope(d[f"dist_{s}"], d.rot, d.team_season)
        rows.append({"group_type": label, "group": group, "sample": sample, "shape": s, "lineups": len(d),
                     "team_seasons": d.team_season.nunique(), "mean_dist": d[f"dist_{s}"].mean(),
                     "slope_runs_per_game": b, "se": se, "t": b / se, "runs_per_win": w,
                     "runs_per_162": b * 162, "se_runs_per_162": se * 162,
                     "wins_per_162": b * 162 / w, "se_wins_per_162": se * 162 / w})
    return rows


def groups_iter(lu):
    for sample in ["main", "secondary", "combined"]:
        d = lu[lu["sample"] == sample] if sample != "combined" else lu[lu["sample"].isin(["main", "secondary"])]
        yield "overall", "1926 to 2026", sample, d
        for e in ERAS:
            yield "era", e, sample, d[d.era == e]
        for dec, x in d.groupby("decade_label"):
            yield "decade", dec, sample, x
        yield "season", "2026", sample, d[d.season == 2026]


def shape_slopes(d, shapes=ALL_SHAPES):
    isP = np.array([[c == "P" for c in p] for p in d.pattern], dtype=bool)
    cnt = np.array([[c in "PC" for c in p] for p in d.pattern], dtype=bool)
    key = pd.Series([a.tobytes() + b.tobytes() for a, b in zip(isP, cnt)])
    cl = pd.factorize(d.team_season.values)[0]
    y = d.rot.values.astype(float)
    tmp = pd.DataFrame({"k": pd.factorize(key)[0], "c": cl, "y": y})
    agg = tmp.groupby(["c", "k"]).y.agg(["size", "sum"]).reset_index()
    first = pd.Series(range(len(key))).groupby(pd.factorize(key)[0]).first().values
    P = isP[first][agg.k.values]
    C = cnt[first][agg.k.values]
    n = agg["size"].values.astype(float)
    sy = agg["sum"].values
    N, ybar = n.sum(), sy.sum() / n.sum()
    G = agg.c.nunique()
    out = []
    S = np.array([[c == "P" for c in s] for s in shapes], dtype=bool)
    for i in range(0, len(shapes), 64):
        Sb = S[i:i + 64]
        D = ((P[:, None, :] != Sb[None, :, :]) & C[:, None, :]).sum(2).astype(float)
        dbar = (D * n[:, None]).sum(0) / N
        sxx = (D ** 2 * n[:, None]).sum(0) - N * dbar ** 2
        sxy = (D * sy[:, None]).sum(0) - dbar * sy.sum()
        b = sxy / sxx
        a = ybar - b * dbar
        xe = (D - dbar) * (sy[:, None] - n[:, None] * (a + b * dbar)) - b * (D - dbar) ** 2 * n[:, None]
        ce = pd.DataFrame(xe).groupby(agg.c.values).sum().values
        se = np.sqrt((ce ** 2).sum(0)) / sxx * np.sqrt(G / (G - 1) * (N - 1) / (N - 2))
        within = D <= 2
        g2 = (within * n[:, None]).sum(0)
        r2 = (within * sy[:, None]).sum(0) / np.where(g2 > 0, g2, np.nan)
        for j in range(len(Sb)):
            out.append({"shape": shapes[i + j], "slope": b[j], "se": se[j], "games_within_2": int(g2[j]),
                        "mean_rot_within_2": r2[j]})
    r = pd.DataFrame(out)
    r["rank"] = r.slope.rank(method="min").astype(int)
    return r


def win_models(lu):
    rows = []
    sets = [("overall", "1926 to 2026", lu[lu["sample"].isin(["main", "secondary"])])]
    sets += [("era", e, lu[(lu.era == e) & lu["sample"].isin(["main", "secondary"])]) for e in ERAS]
    sets += [("season", "2026", lu[(lu.season == 2026) & (lu["sample"] == "main")])]
    for label, group, d in sets:
        d = d[d.win.notna()].dropna(subset=["talent", "opp_talent", "opp_fip", "opp_ra_g"])
        parks = d.park.value_counts()
        park = d.park.where(d.park.isin(parks[parks >= 200].index), "other")
        base = pd.get_dummies(park, prefix="park", drop_first=True, dtype=float)
        w = rpw(d)
        for s in SHAPES:
            X = pd.concat([d[[f"dist_{s}", "talent", "opp_talent", "opp_fip", "opp_ra_g", "home"]].astype(float), base], axis=1)
            X = sm.add_constant(X)
            g = pd.factorize(d.team_season)[0]
            lpm = sm.OLS(d.win.values, X).fit(cov_type="cluster", cov_kwds={"groups": g})
            lg = sm.Logit(d.win.values, X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": g}, maxiter=200)
            pr = lg.predict(X)
            dens = float(np.mean(pr * (1 - pr)))
            rows.append({"group_type": label, "group": group, "shape": s, "games": len(d),
                         "lpm_coef": lpm.params[f"dist_{s}"], "lpm_se": lpm.bse[f"dist_{s}"],
                         "lpm_wins_per_162": lpm.params[f"dist_{s}"] * 162, "lpm_se_wins_per_162": lpm.bse[f"dist_{s}"] * 162,
                         "logit_coef": lg.params[f"dist_{s}"], "logit_se": lg.bse[f"dist_{s}"],
                         "logit_ame_wins_per_162": lg.params[f"dist_{s}"] * dens * 162, "logit_ame_se_wins_per_162": lg.bse[f"dist_{s}"] * dens * 162,
                         "talent_lpm": lpm.params["talent"], "runs_per_win": w})
    return pd.DataFrame(rows)


def buckets(lu):
    rows = []
    d0 = lu[lu["sample"].isin(["main", "secondary"])].copy()
    d0["bucket"] = pd.cut(d0.dist_A, [-1, 1, 2, 3, 4, 99], labels=["0 to 1", "2", "3", "4", "5+"])
    for label, group, d in [("overall", "1926 to 2026", d0)] + [("era", e, d0[d0.era == e]) for e in ERAS] + [("season", "2026", d0[d0.season == 2026])]:
        for b, x in d.groupby("bucket", observed=True):
            rows.append({"group_type": label, "group": group, "bucket": b, "games": len(x), "wins": x.win.sum(),
                         "decisions": x.win.notna().sum(), "runs": x.runs.sum(), "runs_allowed": x.runs_allowed.sum(),
                         "exp_runs": x.exp_runs.sum(), "win_pct": x.win.mean(), "r_g": x.runs.mean(), "rot": x.rot.mean()})
    return pd.DataFrame(rows)


def slot_effects(lu):
    rows = []
    sets = [("overall", "1926 to 2026", lu[lu["sample"].isin(["main", "secondary"])])]
    sets += [("era", e, lu[(lu.era == e) & lu["sample"].isin(["main", "secondary"])]) for e in ERAS]
    sets += [("season", "2026", lu[(lu.season == 2026) & (lu["sample"] == "main")])]
    for label, group, d in sets:
        X = pd.DataFrame({f"P{k}": (d.pattern.str[k - 1] == "P").astype(float) for k in range(1, 10)}, index=d.index)
        m = sm.OLS(d.rot.values, sm.add_constant(X)).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.team_season)[0]})
        for k in range(1, 10):
            rows.append({"group_type": label, "group": group, "slot": k, "p_share": X[f"P{k}"].mean(),
                         "coef_P": m.params[f"P{k}"], "se": m.bse[f"P{k}"], "shape_A": SHAPES["A"][k - 1]})
    return pd.DataFrame(rows)


def all_shapes(lu):
    parts = []
    sets = [("overall", "1926 to 2026 main", lu[lu["sample"] == "main"]),
            ("overall", "1926 to 2026 secondary", lu[lu["sample"] == "secondary"])]
    for e in ERAS:
        smp = "main" if e in ("AL DH 1973 to 2021", "Universal DH 2022 to 2026") else "secondary"
        sets.append(("era", e, lu[(lu.era == e) & (lu["sample"] == smp)]))
    sets.append(("season", "2026", lu[(lu.season == 2026) & (lu["sample"] == "main")]))
    for label, group, d in sets:
        r = shape_slopes(d)
        r.insert(0, "group", group)
        r.insert(0, "group_type", label)
        parts.append(r)
    return pd.concat(parts, ignore_index=True)


def exact_shapes(lu):
    d = lu[lu["sample"].isin(["main", "secondary"])]
    rows = []
    for label, group, x in [("overall", "1926 to 2026", d)] + [("era", e, d[d.era == e]) for e in ERAS] + [("season", "2026", d[d.season == 2026])]:
        g = x.groupby("pattern").agg(G=("runs", "size"), W=("win", lambda v: (v == 1).sum()), L=("win", lambda v: (v == 0).sum()),
                                     R=("runs", "sum"), RA=("runs_allowed", "sum"), exp_R=("exp_runs", "sum"),
                                     teams=("team_season", "nunique")).reset_index()
        g["win_pct"] = g.W / (g.W + g.L)
        g["r_g"] = g.R / g.G
        g["ra_g"] = g.RA / g.G
        g["rot_g"] = (g.R - g.exp_R) / g.G
        g.insert(0, "group", group)
        g.insert(0, "group_type", label)
        rows.append(g)
    return pd.concat(rows, ignore_index=True)


def trends(lu):
    d = lu[lu["sample"] != "other"]
    rows = []
    for dec, x in lu.groupby("decade_label"):
        for k in range(1, 10):
            t = x.pattern.str[k - 1]
            nonx = t.isin(["P", "C"])
            slg = x[f"s{k}_SLG"].where(nonx)
            kp = x[f"s{k}_K_pct"].where(nonx)
            rows.append({"decade": dec, "slot": k, "lineups": len(x), "p_share": (t[nonx] == "P").mean(),
                         "x_share": (t == "X").mean(), "mean_slg": slg.mean(), "mean_k_pct": kp.mean(),
                         "mean_obp": x[f"s{k}_OBP"].where(nonx).mean()})
    tr = pd.DataFrame(rows)
    dist = d.groupby("decade_label").agg(lineups=("dist_A", "size"), mean_dist_A=("dist_A", "mean"),
                                         mean_counted=("n_nonX", "mean"), exact_A=("dist_A", lambda v: (v == 0).sum()),
                                         mean_dist_B=("dist_B", "mean"), mean_dist_C=("dist_C", "mean")).reset_index()
    dist["mean_dist_A_per_9"] = dist.mean_dist_A / dist.mean_counted * 9
    return tr, dist


def examples(lu):
    d = lu[lu["sample"].isin(["main", "secondary"])].copy()
    d["is_AB"] = (d.dist_A == 0) | (d.dist_B == 0)
    ts = lu.groupby("team_season").agg(G=("runs", "size"), W=("win", lambda v: (v == 1).sum()), L=("win", lambda v: (v == 0).sum()),
                                       R=("runs", "sum"), RA=("runs_allowed", "sum"))
    rows = []
    for dec, x in d.groupby("decade_label"):
        c = x.groupby("team_season").agg(n_AB=("is_AB", "sum"), n_A=("dist_A", lambda v: (v == 0).sum()),
                                         n_B=("dist_B", lambda v: (v == 0).sum()))
        top = c.sort_values(["n_AB", "n_A"], ascending=False).head(3)
        for tsn, r in top.iterrows():
            y = x[(x.team_season == tsn) & x.is_AB]
            if y.empty:
                continue
            ids = y[[f"p{k}_id" for k in range(1, 10)]].astype(str).agg("|".join, axis=1)
            best = ids.value_counts().index[0]
            z = y[ids == best].iloc[0]
            rec = {"decade": dec, "team_season": tsn, "season": int(z.season), "team": z.team, "games_A_or_B": int(r.n_AB),
                   "games_A": int(r.n_A), "games_B": int(r.n_B), "uses_of_this_lineup": int((ids == best).sum()),
                   "shape": "A" if z.dist_A == 0 else "B", "pattern": z.pattern,
                   "W": int(ts.loc[tsn, "W"]), "L": int(ts.loc[tsn, "L"]), "R": int(ts.loc[tsn, "R"]), "RA": int(ts.loc[tsn, "RA"])}
            for k in range(1, 10):
                rec[f"slot{k}"] = f"{z[f'p{k}_name']} ({z.pattern[k - 1]}, SLG {z[f's{k}_SLG']:.3f}, K {z[f's{k}_K_pct']:.1%})"
            rows.append(rec)
    return pd.DataFrame(rows)


def team_level(lu):
    d = lu[lu["sample"].isin(["main", "secondary"])]
    a = d.groupby("team_season").agg(season=("season", "first"), team=("team", "first"), era=("era", lambda v: v.mode().iloc[0]),
                                     lineups=("dist_A", "size"), mean_dist_A=("dist_A", "mean"), rot_g=("rot", "mean"))
    t = lu.groupby("team_season").agg(G=("runs", "size"), W=("win", lambda v: (v == 1).sum()), L=("win", lambda v: (v == 0).sum()),
                                      R=("runs", "sum"), RA=("runs_allowed", "sum"))
    a = a.join(t)
    a["pyth_w"] = (a.W + a.L) * a.R ** 1.83 / (a.R ** 1.83 + a.RA ** 1.83)
    a["w_minus_pyth"] = a.W - a.pyth_w
    a = a.reset_index()
    rows = []
    for label, group, x in [("overall", "1926 to 2026", a)] + [("era", e, a[a.era == e]) for e in ERAS]:
        for ycol in ["rot_g", "w_minus_pyth"]:
            m = sm.OLS(x[ycol].values, sm.add_constant(x.mean_dist_A.values)).fit(cov_type="HC1")
            rows.append({"group_type": label, "group": group, "outcome": ycol, "team_seasons": len(x),
                         "slope_per_slot": m.params[1], "se": m.bse[1], "corr": np.corrcoef(x.mean_dist_A, x[ycol])[0, 1]})
    return a, pd.DataFrame(rows)


def main():
    t0 = time.time()
    TAB.mkdir(parents=True, exist_ok=True)
    if (TAB / "headline.json").exists():
        log("outputs exist, skipping")
        return
    lu = load()
    rows = []
    for label, group, sample, d in groups_iter(lu):
        rows += slope_rows(d, label, group, sample)
    sl = pd.DataFrame(rows)
    sl.to_csv(TAB / "shape_slopes.csv", index=False)
    log(f"shape slopes {len(sl)} rows")
    wm = win_models(lu)
    wm.to_csv(TAB / "win_models.csv", index=False)
    log("win models done")
    buckets(lu).to_csv(TAB / "distance_buckets.csv", index=False)
    slot_effects(lu).to_csv(TAB / "slot_effects.csv", index=False)
    sh = all_shapes(lu)
    sh.to_csv(TAB / "all_512_shapes.csv", index=False)
    log("512 shapes done")
    ex = exact_shapes(lu)
    ex.to_csv(TAB / "exact_shapes.csv", index=False)
    tr, dist = trends(lu)
    tr.to_csv(TAB / "trends_by_slot_decade.csv", index=False)
    dist.to_csv(TAB / "distance_by_decade.csv", index=False)
    examples(lu).to_csv(TAB / "examples.csv", index=False)
    ts, tsr = team_level(lu)
    ts.to_csv(TAB / "team_seasons.csv", index=False)
    tsr.to_csv(TAB / "team_level_regressions.csv", index=False)
    d26 = lu[(lu.season == 2026) & (lu["sample"] == "main")]
    s26 = sh[sh.group == "2026"].set_index("shape")
    e26 = ex[(ex.group == "2026") & (ex.pattern == SHAPES["A"])]
    head = {"games_2026": int(d26.game_key.nunique()), "lineups_2026": int(len(d26)),
            "lineups_2026_all": int((lu.season == 2026).sum())}
    for s, p in SHAPES.items():
        head[f"slope_{s}_2026"] = float(s26.loc[p, "slope"])
        head[f"se_{s}_2026"] = float(s26.loc[p, "se"])
        head[f"rank_{s}_2026"] = int(s26.loc[p, "rank"])
    head["exact_A_2026_G"] = int(e26.G.iloc[0]) if len(e26) else 0
    head["exact_A_2026_W"] = int(e26.W.iloc[0]) if len(e26) else 0
    head["exact_A_2026_L"] = int(e26.L.iloc[0]) if len(e26) else 0
    head["best_shape_2026"] = s26.slope.idxmin()
    (TAB / "headline.json").write_text(json.dumps(head, indent=2))
    log(f"core tests done in {time.time() - t0:.0f}s: {head}")


if __name__ == "__main__":
    main()
