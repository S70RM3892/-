#!/usr/bin/env bash
# 全解析を順に実行し、出力を outputs/ に保存する。
#
#   ./run_all.sh          標準出力に流しつつ outputs/*.txt に保存
#   ./run_all.sh --quiet  ファイルにだけ保存
#
# 依存は Python 3.9+ の標準ライブラリのみ（テストだけ pytest を使う）。
set -euo pipefail

cd "$(dirname "$0")"
mkdir -p outputs
QUIET=${1:-}

run() {
  local script=$1
  local out="outputs/${script%.py}.txt"
  echo "=== ${script} ==="
  if [[ "$QUIET" == "--quiet" ]]; then
    ( cd analysis && python3 "$script" ) > "$out"
  else
    ( cd analysis && python3 "$script" ) | tee "$out"
  fi
}

# p10 は検証。ここで落ちたら以降は走らせない。
run p10_validate.py

# p01 → p02 と p05 → p06/p07 に依存がある（outputs/*_handoff.json 経由）。
run p01_panel.py
run p02_gap_ladder.py
run p03_ct_weights.py
run p04_ct_variance.py
run p05_irt_ct.py
run p06_niji.py
run p07_budget.py
run p08_ratio.py
run p09_rejected.py
run p11_seats.py
run p12_risk.py

echo
echo "=== tests ==="
python3 -m pytest tests/ -q

echo
echo "完了。出力は outputs/ を参照。"
