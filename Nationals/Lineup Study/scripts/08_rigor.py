import importlib.util
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import norm

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TAB = ROOT / "out" / "tables"
SHAPES = {"A": "PPCCPCCPC", "B": "PCPCPCCPC", "C": "CPCPCCPCP"}
ERAS = ["Pre DH 1926 to 1972", "AL DH 1973 to 2021", "NL non DH 1973 to 2021", "Universal DH 2022 to 2026"]
N_PERM, SEED = 1000, 2026

spec = importlib.util.spec_from_file_location("core", Path(__file__).parent / "06_core_tests.py")
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} 08_rigor {msg}"
    print(line)
    with open(ROOT / "logs" / "run.log", "a") as f:
        f.write(line + "\n")


def load():
    cols = ["season", "game_key", "team", "home", "era", "decade", "dh_game", "pattern", "pattern_iso", "pattern_xslg",
            "pattern_strict", "n_nonX", "n_counted_strict", "talent", "rot", "rot_x", "runs", "runs_allowed", "win",
            "team_season", "acquisition", "league"]
    cols += [f"dist_{s}{x}" for s in SHAPES for x in ["", "_iso", "_xslg", "_strict"]]
    cols += [f"p{k}_id" for k in range(1, 10)]
    lu = pd.read_parquet(DATA / "lineup_model.parquet", columns=cols)
    nx, nn = lu.pattern.str.count("X"), lu.pattern.str.count("N")
    lu["sample"] = np.where((nx == 0) & (nn == 0), "main", np.where((nx == 1) & (nn == 0) & ~lu.dh_game, "secondary", "other"))
    lu["rpg_both"] = lu.runs + lu.runs_allowed
    return lu[lu["sample"] != "other"].copy()


def slope(d, xcol, ycol="rot", fe=False, controls=()):
    x = d[xcol].astype(float)
    y = d[ycol].astype(float)
    X = pd.DataFrame({xcol: x})
    for c in controls:
        X[c] = d[c].astype(float)
    if fe:
        g = d.team_season
        X = X - X.groupby(g).transform("mean")
        y = y - y.groupby(g).transform("mean")
    else:
        X = sm.add_constant(X)
    m = sm.OLS(y.values, X.values).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.team_season)[0]})
    i = list(X.columns).index(xcol)
    return m.params[i], m.bse[i]


def rec(kind, group, shape, d, b, se, extra=None):
    w = core.rpw(d)
    r = {"test": kind, "group": group, "shape": shape, "lineups": len(d), "slope": b, "se": se, "t": b / se,
         "runs_per_162": b * 162, "se_runs_per_162": se * 162, "wins_per_162": b * 162 / w, "runs_per_win": w}
    if extra:
        r.update(extra)
    return r


def permutation(lu, ps):
    d = lu[(lu.season == 2026) & (lu["sample"] == "main")].reset_index(drop=True)
    tag = ps[ps.season == 2026].set_index("player_id").tag
    ids = d[[f"p{k}_id" for k in range(1, 10)]].to_numpy()
    ts = d.team_season.to_numpy()
    keys = pd.Series([f"{t}|{p}" for t, row in zip(ts, ids) for p in row])
    codes, uniq = pd.factorize(keys)
    codes = codes.reshape(-1, 9)
    u_team = np.array([u.split("|")[0] for u in uniq])
    u_tag = np.array([tag.get(u.split("|")[1], "C") == "P" for u in uniq])
    groups = [np.where(u_team == t)[0] for t in np.unique(u_team)]
    shapes = np.arange(512)
    bitw = 1 << np.arange(8, -1, -1)
    pop = np.array([bin(i).count("1") for i in range(512)])
    y = d.rot.to_numpy(float)
    yc = y - y.mean()

    def best(utag):
        pat = (utag[codes] * bitw).sum(1)
        D = pop[pat[:, None] ^ shapes[None, :]].astype(float)
        Dc = D - D.mean(0)
        return (Dc * yc[:, None]).sum(0) / (Dc ** 2).sum(0)

    real = best(u_tag)
    shape_str = [format(s, "09b").replace("1", "P").replace("0", "C") for s in shapes]
    a_idx = shape_str.index(SHAPES["A"])
    rng = np.random.default_rng(SEED)
    null = np.zeros(N_PERM)
    null_a = np.zeros(N_PERM)
    for i in range(N_PERM):
        t = u_tag.copy()
        for g in groups:
            t[g] = t[rng.permutation(g)]
        s = best(t)
        null[i] = s.min()
        null_a[i] = s[a_idx]
    out = pd.DataFrame({"perm": range(N_PERM), "best_slope": null, "slope_A": null_a})
    summ = {"real_best_shape": shape_str[int(real.argmin())], "real_best_slope": float(real.min()),
            "real_slope_A": float(real[a_idx]), "null_best_mean": float(null.mean()),
            "null_best_p05": float(np.quantile(null, 0.05)), "null_best_p50": float(np.quantile(null, 0.5)),
            "p_value_best": float((null <= real.min()).mean()), "p_value_A_vs_best_null": float((null <= real[a_idx]).mean()),
            "p_value_A_vs_A_null": float((null_a <= real[a_idx]).mean()), "n_perm": N_PERM,
            "bonferroni_z": float(norm.ppf(1 - 0.05 / (2 * 512))), "null_A_sd": float(null_a.std()),
            "z_A_vs_A_null": float(real[a_idx] / null_a.std())}
    return out, summ


def out_of_sample(lu):
    rows = []
    h = lu[lu.season <= 2025]
    dec = []
    for dc, x in h.groupby("decade"):
        for s in SHAPES:
            b, se = slope(x, f"dist_{s}")
            rows.append(rec("oos_decade", f"{dc}s", s, x, b, se))
    t = pd.DataFrame(rows)
    comb = []
    for s in SHAPES:
        x = t[t["shape"] == s]
        w = 1 / x.se ** 2
        b = (x.slope * w).sum() / w.sum()
        se = np.sqrt(1 / w.sum())
        comb.append(rec("oos_combined_inverse_variance", "1926 to 2025", s, h, b, se))
        b2, se2 = slope(h, f"dist_{s}")
        comb.append(rec("oos_pooled", "1926 to 2025", s, h, b2, se2))
    split = []
    early, late = h[h.season <= 1999], h[h.season >= 2000]
    for name, fit, test in [("fit 1926 to 1999, test 2000 to 2025", early, late), ("fit 2000 to 2025, test 1926 to 1999", late, early)]:
        r = core.shape_slopes(fit)
        bs = r.sort_values("slope").iloc[0]["shape"]
        rt = core.shape_slopes(test, shapes=[bs, SHAPES["A"]])
        rk = core.shape_slopes(test)
        rank_in_test = int(rk.set_index("shape").loc[bs, "rank"])
        for _, q in rt.iterrows():
            split.append({"split": name, "shape": q["shape"], "is_fit_best": q["shape"] == bs,
                          "fit_slope": float(r.set_index("shape").loc[q["shape"], "slope"]),
                          "test_slope": q.slope, "test_se": q.se, "test_t": q.slope / q.se,
                          "rank_in_test": int(rk.set_index("shape").loc[q["shape"], "rank"]),
                          "test_lineups": len(test), "best_in_fit_rank_in_test": rank_in_test})
    return pd.concat([t, pd.DataFrame(comb)], ignore_index=True), pd.DataFrame(split)


def fixed_effects(lu):
    rows = []
    sets = [("1926 to 2025", lu[lu.season <= 2025]), ("2026", lu[lu.season == 2026]), ("1926 to 2026", lu)]
    sets += [(e, lu[lu.era == e]) for e in ERAS]
    for g, d in sets:
        for s in SHAPES:
            b, se = slope(d, f"dist_{s}")
            bf, sef = slope(d, f"dist_{s}", fe=True)
            rows.append(rec("pooled", g, s, d, b, se))
            rows.append(rec("team_season_fixed_effects", g, s, d, bf, sef))
    return pd.DataFrame(rows)


def robustness(lu):
    rows = []
    h = lu[lu.season <= 2025]
    y26 = lu[lu.season == 2026]
    for s in SHAPES:
        for name, d in [("baseline 1926 to 2025", h), ("baseline 2026", y26)]:
            b, se = slope(d, f"dist_{s}")
            rows.append(rec("baseline", name, s, d, b, se))
        for tag in ["iso", "xslg"]:
            for name, d in [("1926 to 2025", h), ("2026", y26)]:
                x = d[d[f"pattern_{tag}"].str.count("N") == 0]
                if tag == "xslg":
                    x = x[x.season >= 2023]
                    name = "2023 to 2025" if name == "1926 to 2025" else name
                if len(x) < 100:
                    continue
                b, se = slope(x, f"dist_{s}_{tag}")
                rows.append(rec(f"tag {tag.upper()}", name, s, x, b, se))
        for name, d in [("1926 to 2025", h), ("2026", y26)]:
            x = d[d.n_counted_strict > 0]
            b, se = slope(x, f"dist_{s}_strict", controls=["n_counted_strict"])
            rows.append(rec("tag strict 10 point gap (N excluded, n counted as control)", name, s, x, b, se,
                            {"mean_counted": x.n_counted_strict.mean()}))
        x = h[h.acquisition == "Y"]
        b, se = slope(x, f"dist_{s}")
        rows.append(rec("drop deduced or partial games", "1926 to 2025", s, x, b, se))
        sched = np.where((h.season <= 1960) | ((h.season == 1961) & (h.league == "NL")), "154 game seasons",
                         np.where(h.season.isin([1972, 1981, 1994, 1995, 2020]), "shortened seasons", "162 game seasons"))
        for g in ["154 game seasons", "162 game seasons", "shortened seasons"]:
            x = h[sched == g]
            b, se = slope(x, f"dist_{s}")
            rows.append(rec("season length", g, s, x, b, se))
        x = y26.dropna(subset=["rot_x"])
        b, se = slope(x, f"dist_{s}", ycol="rot_x")
        rows.append(rec("2026 xwOBA talent", "2026", s, x, b, se))
    rx = core.shape_slopes(y26[y26["sample"] == "main"].assign(rot=y26.rot_x).dropna(subset=["rot"]))
    return pd.DataFrame(rows), rx


def markov_summary(lu):
    f = DATA / "markov_lineups.parquet"
    if not f.exists():
        return None, None
    m = pd.read_parquet(f)
    m["d_A"] = m.m_shapeA - m.m_actual
    m["d_best"] = m.m_best - m.m_actual
    m["order_loss"] = m.m_actual - m.m_best
    m["group"] = np.where(m.season == 2026, "2026", "1926 to 2025 sample")
    rows, dec = [], []
    sets = [("2026", m[m.season == 2026]), ("1926 to 2025 sample", m[m.season <= 2025]), ("all", m)]
    sets += [(e, m[(m.era == e) & (m.season <= 2025)]) for e in ERAS]
    sets += [(f"{d}s", x) for d, x in m[m.season <= 2025].groupby("decade")]
    for g, x in sets:
        if len(x) < 50:
            continue
        cal = x.runs.mean() / x.m_actual.mean()
        moved = x[x.slots_moved_toward_A > 0]
        per_slot = moved.d_A.sum() / moved.slots_moved_toward_A.sum() if len(moved) else np.nan
        b_emp, se_emp = slope(x, "dist_A")
        b_ord, se_ord = slope(x, "dist_A", ycol="order_loss")
        xx = x.copy()
        xx["m_resid"] = xx.m_actual - xx.groupby("season").m_actual.transform("mean")
        xx["t_resid"] = xx.talent - xx.groupby("season").talent.transform("mean")
        b_tot, se_tot = slope(xx, "dist_A", ycol="m_resid", controls=["t_resid"])
        rows.append({"group": g, "lineups": len(x), "mean_actual_runs": x.runs.mean(), "markov_actual": x.m_actual.mean(),
                     "markov_shapeA": x.m_shapeA.mean(), "markov_best": x.m_best.mean(), "calibration": cal,
                     "shapeA_minus_actual_per_game": x.d_A.mean(), "shapeA_minus_actual_per_162": x.d_A.mean() * 162,
                     "best_minus_actual_per_game": x.d_best.mean(), "best_minus_actual_per_162": x.d_best.mean() * 162,
                     "share_shapeA_beats_actual": (x.d_A > 0).mean(), "mean_slots_moved": x.slots_moved_toward_A.mean(),
                     "markov_per_slot_toward_A": per_slot, "markov_per_slot_toward_A_calibrated": per_slot * cal,
                     "empirical_slope": b_emp, "empirical_se": se_emp,
                     "markov_order_loss_slope": b_ord, "markov_order_loss_se": se_ord,
                     "markov_total_slope_talent_adj": b_tot, "markov_total_slope_se": se_tot})
    return pd.DataFrame(rows), m


def manager_card():
    f = DATA / "markov_lineups.parquet"
    if not f.exists():
        return None
    spec2 = importlib.util.spec_from_file_location("mk", Path(__file__).parent / "07_markov.py")
    mk = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(mk)
    m = pd.read_parquet(f, columns=["season", "game_key", "home", "pattern", "best_order", "n_nonX", "runs", "m_actual"])
    m = m[m.n_nonX == 9]
    cols = ["game_key", "home"] + [f"s{k}_{e}" for k in range(1, 10) for e in mk.EV + ["OBP", "SLG"]]
    lm = pd.read_parquet(DATA / "lineup_model.parquet", columns=cols)
    m = m.merge(lm, on=["game_key", "home"], how="left")
    rows = []
    for g, x in [("2026", m[m.season == 2026]), ("1973 to 2025 DH lineups in sample", m[m.season <= 2025])]:
        rates = np.stack([x[[f"s{k}_{e}" for e in mk.EV]].to_numpy(float) for k in range(1, 10)], axis=1)
        order = np.array([[int(c) - 1 for c in o] for o in x.best_order])
        best = rates[np.arange(len(x))[:, None], order]
        base = mk.game_runs(best)
        cal = x.runs.mean() / x.m_actual.mean()
        obp = x[[f"s{k}_OBP" for k in range(1, 10)]].to_numpy(float)
        slg = x[[f"s{k}_SLG" for k in range(1, 10)]].to_numpy(float)
        pat = np.array([list(p) for p in x.pattern])
        bpat = pat[np.arange(len(x))[:, None], order]
        bobp = obp[np.arange(len(x))[:, None], order]
        bslg = slg[np.arange(len(x))[:, None], order]
        for k in range(9):
            r = {"group": g, "lineups": len(x), "slot": k + 1, "p_share_actual": (pat[:, k] == "P").mean(),
                 "p_share_markov_best": (bpat[:, k] == "P").mean(), "obp_actual": np.nanmean(obp[:, k]),
                 "obp_markov_best": np.nanmean(bobp[:, k]), "slg_actual": np.nanmean(slg[:, k]),
                 "slg_markov_best": np.nanmean(bslg[:, k]), "shape_A": SHAPES["A"][k]}
            if k < 8:
                sw = best.copy()
                sw[:, [k, k + 1]] = sw[:, [k + 1, k]]
                r["swap_with_next_cost_per_162"] = float((base - mk.game_runs(sw)).mean() * 162 * cal)
            rows.append(r)
    return pd.DataFrame(rows)


def main():
    t0 = time.time()
    if (TAB / "rigor_headline.json").exists():
        log("outputs exist, skipping")
        return
    lu = load()
    ps = pd.read_parquet(DATA / "player_seasons.parquet", columns=["season", "player_id", "tag"])
    null, perm = permutation(lu, ps)
    null.to_csv(TAB / "permutation_null.csv", index=False)
    log(f"permutation done: {perm}")
    oos, split = out_of_sample(lu)
    oos.to_csv(TAB / "out_of_sample.csv", index=False)
    split.to_csv(TAB / "out_of_sample_split.csv", index=False)
    log("out of sample done")
    fe = fixed_effects(lu)
    fe.to_csv(TAB / "fixed_effects.csv", index=False)
    rb, rx = robustness(lu)
    rb.to_csv(TAB / "robustness.csv", index=False)
    rx.to_csv(TAB / "shapes_2026_xwoba.csv", index=False)
    log("fixed effects and robustness done")
    mk, _ = markov_summary(lu)
    if mk is not None:
        mk.to_csv(TAB / "markov_summary.csv", index=False)
    card = manager_card()
    if card is not None:
        card.to_csv(TAB / "manager_card.csv", index=False)
    head = {"permutation": perm}
    for s in SHAPES:
        for key, test in [("oos_pooled", "oos_pooled"), ("oos_ivw", "oos_combined_inverse_variance")]:
            r = oos[(oos.test == test) & (oos["shape"] == s)].iloc[0]
            head[f"{key}_{s}"] = {"slope": float(r.slope), "se": float(r.se)}
    for g in ["1926 to 2025", "2026"]:
        r = fe[(fe.test == "team_season_fixed_effects") & (fe.group == g) & (fe["shape"] == "A")].iloc[0]
        head[f"fe_A_{g}"] = {"slope": float(r.slope), "se": float(r.se)}
    head["rank_A_2026_xwoba"] = int(rx.set_index("shape").loc[SHAPES["A"], "rank"])
    head["slope_A_2026_xwoba"] = float(rx.set_index("shape").loc[SHAPES["A"], "slope"])
    if mk is not None:
        head["markov"] = mk.set_index("group").loc[["2026", "1926 to 2025 sample"]].to_dict(orient="index")
    (TAB / "rigor_headline.json").write_text(json.dumps(head, indent=2, default=float))
    log(f"rigor done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
