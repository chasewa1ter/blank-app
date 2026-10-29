import time
from datetime import datetime
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TAB = ROOT / "out" / "tables"
EV = ["r1B", "r2B", "r3B", "rHR", "rBB", "rK", "rOUT"]
SHAPE_A = "PPCCPCCPC"
P_SCORE_2_ON_1B, P_1_TO_3_ON_1B, P_SCORE_1_ON_2B = 0.6, 0.3, 0.4
P_DP, P_SCORE_3_ON_OUT, P_2_TO_3_ON_OUT = 0.22, 0.3, 0.3
N_HIST, SEED = 50000, 2026


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} 07_markov {msg}"
    print(line)
    with open(ROOT / "logs" / "run.log", "a") as f:
        f.write(line + "\n")


def outcomes(e, o, b):
    r1, r2, r3 = b & 1, (b >> 1) & 1, (b >> 2) & 1
    if e == "r1B":
        res = []
        for s2, p2 in ([(1, P_SCORE_2_ON_1B), (0, 1 - P_SCORE_2_ON_1B)] if r2 else [(0, 1)]):
            third_free = not (r2 and not s2)
            opts = [(1, P_1_TO_3_ON_1B), (0, 1 - P_1_TO_3_ON_1B)] if (r1 and third_free) else [(0, 1)]
            for t13, p13 in opts:
                runs = r3 + (r2 and s2)
                nb = 1
                if r2 and not s2:
                    nb |= 4
                if r1:
                    nb |= 4 if t13 else 2
                res.append((o, nb, runs, p2 * p13))
        return res
    if e == "r2B":
        if r1:
            return [(o, 2 | 0, r3 + r2 + 1, P_SCORE_1_ON_2B), (o, 2 | 4, r3 + r2, 1 - P_SCORE_1_ON_2B)]
        return [(o, 2, r3 + r2, 1)]
    if e == "r3B":
        return [(o, 4, r1 + r2 + r3, 1)]
    if e == "rHR":
        return [(o, 0, r1 + r2 + r3 + 1, 1)]
    if e == "rBB":
        if not r1:
            return [(o, b | 1, 0, 1)]
        if not r2:
            return [(o, b | 3, 0, 1)]
        if not r3:
            return [(o, 7, 0, 1)]
        return [(o, 7, 1, 1)]
    if e == "rK":
        return [(o + 1, b, 0, 1)]
    if o == 2:
        return [(3, 0, 0, 1)]
    res = []
    pdp = P_DP if r1 else 0
    if pdp:
        if o + 2 >= 3:
            res.append((3, 0, 0, pdp))
        else:
            res.append((o + 2, 4 if r2 else 0, r3, pdp))
    for s3, p3 in ([(1, P_SCORE_3_ON_OUT), (0, 1 - P_SCORE_3_ON_OUT)] if r3 else [(0, 1)]):
        free3 = (not r3) or s3
        for a2, p2 in ([(1, P_2_TO_3_ON_OUT), (0, 1 - P_2_TO_3_ON_OUT)] if (r2 and free3) else [(0, 1)]):
            nb = (r1 * 1) | ((r2 and not a2) * 2) | (((r3 and not s3) or (r2 and a2)) * 4)
            res.append((o + 1, nb, s3, (1 - pdp) * p3 * p2))
    return res


def tables():
    M = np.zeros((7, 3, 3, 8, 8))
    A = np.zeros((7, 3, 8))
    R = np.zeros((7, 3, 8))
    for ei, e in enumerate(EV):
        for o in range(3):
            for b in range(8):
                tot = 0
                for o2, b2, runs, p in outcomes(e, o, b):
                    tot += p
                    R[ei, o, b] += p * runs
                    if o2 >= 3:
                        A[ei, o, b] += p
                    else:
                        M[ei, o, o2 - o, b, b2] += p
                assert abs(tot - 1) < 1e-9
    return M, A, R


M_T, A_T, R_T = tables()


def game_runs(p):
    L = p.shape[0]
    X = {}
    eye = np.eye(8)[None]
    for o in (2, 1, 0):
        B = [np.einsum("le,ebc->lbc", p[:, i, :], M_T[:, o, 0]) for i in range(9)]
        R = []
        for i in range(9):
            j = (i + 1) % 9
            r = np.zeros((L, 8, 10))
            r[:, :, 0] = p[:, i, :] @ R_T[:, o, :]
            r[:, :, 1 + j] = p[:, i, :] @ A_T[:, o, :]
            for k in range(1, 3 - o):
                r += np.einsum("le,ebc->lbc", p[:, i, :], M_T[:, o, k]) @ X[o + k][:, j]
            R.append(r)
        prod = np.tile(eye, (L, 1, 1))
        S = np.zeros((L, 8, 10))
        for i in range(9):
            S += prod @ R[i]
            prod = prod @ B[i]
        x = np.zeros((L, 9, 8, 10))
        x[:, 0] = np.linalg.solve(eye - prod, S)
        for i in range(8, 0, -1):
            x[:, i] = R[i] + B[i] @ x[:, (i + 1) % 9]
        X[o] = x
    E = X[0][:, :, 0, 0]
    F = X[0][:, :, 0, 1:]
    pi = np.zeros((L, 9))
    pi[:, 0] = 1
    total = np.zeros(L)
    for _ in range(9):
        total += (pi * E).sum(1)
        pi = np.einsum("li,lij->lj", pi, F)
    return total


def shape_a_order(tags, ops, slg):
    idx = [k for k in range(9) if tags[k] in "PC"]
    target = [SHAPE_A[k] for k in idx]
    need = target.count("P")
    P = [k for k in idx if tags[k] == "P"]
    C = [k for k in idx if tags[k] == "C"]
    if len(P) >= need:
        pg = sorted(sorted(P, key=lambda k: -ops[k])[:need])
    else:
        pg = sorted(P + sorted(C, key=lambda k: -slg[k])[:need - len(P)])
    cg = [k for k in idx if k not in pg]
    order = list(range(9))
    pi, ci = iter(pg), iter(cg)
    for k, t in zip(idx, target):
        order[k] = next(pi) if t == "P" else next(ci)
    return order


def local_search(rates):
    L = rates.shape[0]
    orders = np.tile(np.arange(9), (L, 1))
    best = game_runs(rates)
    swaps = [(a, b) for a in range(9) for b in range(a + 1, 9)]
    active = np.ones(L, bool)
    for _ in range(12):
        ids = np.where(active)[0]
        if len(ids) == 0:
            break
        cand = np.repeat(orders[ids], len(swaps), axis=0).reshape(len(ids), len(swaps), 9)
        for s, (a, b) in enumerate(swaps):
            cand[:, s, [a, b]] = cand[:, s, [b, a]]
        flat = cand.reshape(-1, 9)
        r = rates[np.repeat(ids, len(swaps))[:, None], flat]
        val = game_runs(r).reshape(len(ids), len(swaps))
        j = val.argmax(1)
        gain = val[np.arange(len(ids)), j] - best[ids]
        imp = gain > 1e-9
        orders[ids[imp]] = cand[np.arange(len(ids)), j][imp]
        best[ids[imp]] = val[np.arange(len(ids)), j][imp]
        active[ids[~imp]] = False
    return best, orders


def work(chunk):
    rates, tags, ops, slg = chunk
    actual = game_runs(rates)
    a_orders = np.array([shape_a_order(t, o, s) for t, o, s in zip(tags, ops, slg)])
    shape_a = game_runs(rates[np.arange(len(rates))[:, None], a_orders])
    best, b_orders = local_search(rates)
    a_tags = np.array([[t[k] for k in o] for t, o in zip(tags, a_orders)])
    return actual, shape_a, best, a_tags, b_orders


def sample_lineups():
    cols = ["season", "game_key", "team", "home", "era", "decade", "pattern", "n_nonX", "dh_game", "dist_A", "talent", "rot",
            "runs", "exp_runs", "team_season"] + [f"s{k}_{e}" for k in range(1, 10) for e in EV + ["rel_ops_s", "SLG"]] + [f"p{k}_name" for k in range(1, 10)]
    lu = pd.read_parquet(DATA / "lineup_model.parquet", columns=cols)
    nx, nn = lu.pattern.str.count("X"), lu.pattern.str.count("N")
    ok = ((nx == 0) | ((nx == 1) & ~lu.dh_game)) & (nn == 0)
    lu = lu[ok]
    rng = np.random.default_rng(SEED)
    hist = lu[lu.season <= 2025]
    per = N_HIST // hist.decade.nunique()
    parts = [x.iloc[rng.choice(len(x), min(per, len(x)), replace=False)] for _, x in hist.groupby("decade")]
    s = pd.concat(parts + [lu[lu.season == 2026]])
    return s.dropna(subset=[f"s{k}_{e}" for k in range(1, 10) for e in EV]).reset_index(drop=True)


def main():
    t0 = time.time()
    TAB.mkdir(parents=True, exist_ok=True)
    out = DATA / "markov_lineups.parquet"
    if out.exists():
        log("output exists, skipping")
        return
    s = sample_lineups()
    log(f"sample: {len(s)} lineups ({(s.season == 2026).sum()} from 2026)")
    rates = np.stack([s[[f"s{k}_{e}" for e in EV]].to_numpy(float) for k in range(1, 10)], axis=1)
    tags = s.pattern.to_numpy()
    ops = s[[f"s{k}_rel_ops_s" for k in range(1, 10)]].to_numpy(float)
    slg = s[[f"s{k}_SLG" for k in range(1, 10)]].fillna(0).to_numpy(float)
    n = 200
    chunks = [(rates[i:i + n], tags[i:i + n], ops[i:i + n], slg[i:i + n]) for i in range(0, len(s), n)]
    with Pool(4) as pool:
        res = []
        for k, r in enumerate(pool.imap(work, chunks)):
            res.append(r)
            if k % 25 == 0:
                log(f"chunk {k + 1} of {len(chunks)} after {time.time() - t0:.0f}s")
    s["m_actual"] = np.concatenate([r[0] for r in res])
    s["m_shapeA"] = np.concatenate([r[1] for r in res])
    s["m_best"] = np.concatenate([r[2] for r in res])
    a_tags = np.concatenate([r[3] for r in res])
    s["pattern_shapeA"] = ["".join(t) for t in a_tags]
    s["best_order"] = ["".join(str(x + 1) for x in o) for o in np.concatenate([r[4] for r in res])]
    s["dist_A_after"] = [sum(1 for k in range(9) if p[k] in "PC" and p[k] != SHAPE_A[k]) for p in s.pattern_shapeA]
    s["slots_moved_toward_A"] = s.dist_A - s.dist_A_after
    keep = [c for c in s.columns if not c.startswith("s") or c in ("season", "slots_moved_toward_A")]
    s[keep].to_parquet(out, index=False)
    log(f"markov done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
