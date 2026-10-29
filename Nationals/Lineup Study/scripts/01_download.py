import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import rdata
import requests

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} 01_download {msg}"
    print(line)
    with open(ROOT / "logs" / "run.log", "a") as f:
        f.write(line + "\n")


def problem(msg):
    log("PROBLEM " + msg)
    with open(ROOT / "PROBLEMS.md", "a") as f:
        f.write(f"* {datetime.now():%Y-%m-%d %H:%M} (01_download) {msg}\n")


def git(args, cwd=None):
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"}
    return subprocess.run(["git"] + args, cwd=cwd, env=env, capture_output=True, text=True, timeout=1800)


def sparse_clone(url, dest, patterns):
    if not (dest / ".git").exists():
        r = git(["clone", "--depth", "1", "--filter=blob:none", "--sparse", url, str(dest)])
        if r.returncode != 0:
            problem(f"clone failed {url}: {r.stderr[-300:]}")
            return False
    r = git(["sparse-checkout", "set", "--no-cone"] + patterns, cwd=dest)
    if r.returncode != 0:
        problem(f"sparse checkout failed {url}: {r.stderr[-300:]}")
        return False
    sha = git(["rev-parse", "HEAD"], cwd=dest).stdout.strip()
    log(f"{url} at {sha}")
    return True


def lahman():
    repo = RAW / "lahman_repo"
    if not (repo / ".git").exists():
        r = git(["clone", "--depth", "1", "https://github.com/cdalzell/Lahman", str(repo)])
        if r.returncode != 0:
            problem("Lahman clone failed: " + r.stderr[-300:])
            return
    out = RAW / "lahman_csv"
    out.mkdir(exist_ok=True)
    for t in ["Batting", "Pitching", "People", "Teams", "Appearances", "Fielding"]:
        f = out / f"{t}.csv"
        if f.exists():
            continue
        parsed = rdata.parser.parse_file(repo / "data" / f"{t}.RData")
        conv = rdata.conversion.convert(parsed)
        df = list(conv.values())[0]
        df = df.rename(columns={"X2B": "2B", "X3B": "3B"})
        df.to_csv(f, index=False)
        log(f"Lahman {t}: {len(df)} rows, seasons {df['yearID'].min() if 'yearID' in df else ''} to {df['yearID'].max() if 'yearID' in df else ''}")


def pick_spotcheck():
    f = RAW / "spotcheck_seasons.csv"
    if f.exists():
        return pd.read_csv(f)
    teams = pd.read_csv(RAW / "lahman_csv" / "Teams.csv")
    teams = teams[(teams.yearID >= 1926) & (teams.yearID <= 2025) & teams.lgID.isin(["AL", "NL"])]
    rng = np.random.default_rng(2026)
    picks = []
    for start in range(1926, 2026, 10):
        pool = teams[(teams.yearID >= start) & (teams.yearID < start + 10)]
        picks.append(pool.iloc[rng.choice(len(pool), 3, replace=False)])
    sel = pd.concat(picks)[["yearID", "lgID", "teamID", "teamIDBR", "teamIDretro", "name"]]
    sel.to_csv(f, index=False)
    return sel


def retrosheet(spot):
    pats = ["/README.md", "/reference/*", "/seasons/*/GL*.TXT", "/seasons/*/gl*.txt"]
    pats += [f"/seasons/{y}/*" for y in sorted(spot.yearID.unique())]
    sparse_clone("https://github.com/chadwickbureau/retrosheet", RAW / "retrosheet_repo", pats)
    n = len([f for f in (RAW / "retrosheet_repo" / "seasons").glob("*/*") if f.name.upper().startswith("GL")])
    log(f"Retrosheet game log files: {n}")


def register():
    repo = RAW / "register_repo"
    if not (repo / ".git").exists():
        r = git(["clone", "--depth", "1", "https://github.com/chadwickbureau/register", str(repo)])
        if r.returncode != 0:
            problem("Chadwick register clone failed: " + r.stderr[-300:])


def feeds():
    sparse_clone("https://github.com/lancebroz/mlb-pitcher-data", RAW / "pitchfeed_repo",
                 ["/README.md", "/src/*", "/data/last_update.json", "/data/raw/2023/monthly/*",
                  "/data/raw/2024/monthly/*", "/data/raw/2025/monthly/*", "/data/raw/2026/monthly/*"])
    sparse_clone("https://github.com/toolstem/daily-box-score", RAW / "boxfeed_repo",
                 ["/feed/boxscore_2026-*", "/feed/games_2026-*"])


def try_get(url, dest):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
    except Exception as e:
        return f"error {type(e).__name__}: {str(e)[:150]}"
    if r.status_code == 200:
        dest.write_bytes(r.content)
    return f"HTTP {r.status_code}"


def blocked_sources():
    (RAW / "bref").mkdir(exist_ok=True)
    (RAW / "mlbapi").mkdir(exist_ok=True)
    status = RAW / "source_status.txt"
    if status.exists():
        return
    lines = []
    tests = [
        ("retrosheet.org", "https://www.retrosheet.org/gamelogs/glfields.txt", RAW / "glfields.txt"),
        ("statsapi.mlb.com", "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026", RAW / "mlbapi" / "standings_2026.json"),
        ("baseballsavant.mlb.com", "https://baseballsavant.mlb.com/leaderboard/expected_statistics?type=batter&year=2026&position=&team=&filterType=pa&min=1&csv=true", RAW / "mlbapi" / "savant_expected_2026.csv"),
        ("baseball-reference.com", "https://www.baseball-reference.com/teams/WSN/2019-batting-orders.shtml", RAW / "bref" / "WSN_2019.shtml"),
    ]
    for name, url, dest in tests:
        res = try_get(url, dest)
        lines.append(f"{name}\t{url}\t{res}")
        log(f"{name}: {res}")
        if not res.startswith("HTTP 200"):
            problem(f"{name} unreachable ({res}). Fallback used, see DECISIONS.md.")
        time.sleep(6)
    status.write_text("\n".join(lines) + "\n")


def plotly():
    dest = RAW / "plotly"
    if (dest / "package" / "plotly.min.js").exists():
        return
    dest.mkdir(exist_ok=True)
    url = "https://registry.npmjs.org/plotly.js-dist-min/-/plotly.js-dist-min-2.35.2.tgz"
    r = requests.get(url, timeout=120)
    if r.status_code != 200:
        problem(f"plotly download failed: HTTP {r.status_code}")
        return
    (dest / "plotly.tgz").write_bytes(r.content)
    import tarfile
    with tarfile.open(dest / "plotly.tgz") as t:
        t.extract("package/plotly.min.js", dest, filter="data")
    log("plotly.js 2.35.2 downloaded")


def main():
    t0 = time.time()
    for d in ["raw", "data", "out", "logs"]:
        (ROOT / d).mkdir(exist_ok=True)
    blocked_sources()
    lahman()
    spot = pick_spotcheck()
    retrosheet(spot)
    register()
    feeds()
    plotly()
    log(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
