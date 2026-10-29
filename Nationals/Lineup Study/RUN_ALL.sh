#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ "${1:-}" = "--fresh" ]; then
  rm -rf data/* out/* logs/*
fi
mkdir -p raw data out logs
for s in 01_download 02_build_games 03_player_seasons 04_validate 05_lineup_model 06_core_tests 07_markov 08_rigor 09_report; do
  echo "== $s"
  python3 "scripts/$s.py"
done
