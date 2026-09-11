# -*- coding: utf-8 -*-
"""棄却・断念した仮説を、実際に走るコードとして残す。

旧 README は5つの棄却仮説を列挙していたが、そのうち
  * 隔年現象の棄却（実測 r=−0.568 / 帰無 r=−0.696 / p=0.992）
  * 難易度→平均点の翻訳（11年OOS MAE 6.65pt > 変動σ 4.09pt）
  * 志願倍率が最低点の70%を説明（→ p08 に移した）
  * 第1段階選抜「10年で7人(0.18%)」
には analysis/ に対応するスクリプトが1つも無く、再現できなかった。
棄却した仮説こそコードを残す価値がある（後から「本当に棄却できていたのか」を
問い直せるのは検証可能なときだけ）。

足切り実績（10年で7人）については、根拠データがリポジトリに無い。
数字を再現できないので README からは落とし、制度の条文だけを残した。
"""
from __future__ import annotations

import json
import math
import os
import random
import statistics as st

from kyodai import datasets as ds
from kyodai.stats import corr, header, ols, permutation_p

SEED = 20260911


def lag1(v):
    if len(v) < 3:
        return float("nan")
    a, b = v[:-1], v[1:]
    return corr(a, b)


def main() -> None:
    recs, years = ds.load_panel()
    idx = ds.panel_index(recs)
    deps = ds.DEPS

    print(header("仮説1: 隔年現象（前年上がれば翌年下がる）"))
    print("  各学科の dv を学科内で中心化し、ラグ1の自己相関を見る。")
    print(f"  {'学科':<8}{'lag1 自己相関':>15}")
    obs = []
    for p in deps:
        v = ds.series(idx, p, years)
        m = st.mean(v)
        c = lag1([x - m for x in v])
        obs.append(c)
        print(f"  {p:<8}{c:>15.3f}")
    obs_mean = st.mean(obs)
    print(f"  {'平均':<8}{obs_mean:>15.3f}")

    print("\n  帰無仮説: 系列に順序の情報が無い（= 隔年現象が無い）。")
    print("  短い系列を中心化するとラグ1自己相関は機械的に負になる。")
    print("  その機械的な負値を、年の並べ替えで作った帰無分布として直接測る。")
    rng = random.Random(SEED)
    series_all = {p: ds.series(idx, p, years) for p in deps}

    def draw(r: random.Random) -> float:
        out = []
        for p in deps:
            v = r.sample(series_all[p], len(years))
            m = st.mean(v)
            out.append(lag1([x - m for x in v]))
        return st.mean(out)

    null = [draw(rng) for _ in range(20000)]
    null_mean = st.mean(null)
    pv = sum(1 for t in null if t <= obs_mean) / len(null)
    print(f"  帰無分布の平均 = {null_mean:+.3f}（順序が無くてもこれだけ負になる）")
    print(f"  実測 {obs_mean:+.3f} が帰無以下になる確率 p = {pv:.3f}")
    print(f"  → 実測の負値は機械的な負値と見分けがつかない。隔年現象は棄却。")
    print("     （旧 README は 実測 −0.568 / 帰無 −0.696 / p=0.992 と書いていた。")
    print("      対応コードが無く厳密な照合はできないが、結論の向きは一致する。）")

    print(header("仮説2: 二次数学の難易度から合格最低点を翻訳できるか"))
    path = os.path.join(ds.DATA, "dist.json")
    D = json.load(open(path, encoding="utf-8"))
    rows = [(d["y"], d["mean"], d["rate"]) for d in D if "mean" in d and "rate" in d]
    rows.sort()
    yrs = [r[0] for r in rows]
    print(f"  data/dist.json: {len(rows)} 年分（{min(yrs)}–{max(yrs)}）")
    missing = [y for y in range(min(yrs), max(yrs) + 1) if y not in yrs]
    print(f"  欠測年: {missing if missing else 'なし'}")
    print("  ※ 難易度評価の出典は個人の note 記事および Z会（src フィールド）。")
    print("     『一次資料のみ』ではない。README の看板と食い違っていた点。")
    print("  ※ rate は情報学科の合格最低点得点率。2025年以降は1025点満点で、")
    print("     2024年以前の1000点満点とは分母が違う。この時点で系列として連続でない。")

    xs = [r[1] for r in rows]
    ys = [r[2] for r in rows]
    a, b = ols(xs, ys)
    print(f"\n  当てはめ: 最低点得点率 = {a:.2f} {b:+.2f} × 難易度   r = {corr(xs, ys):+.3f}")
    errs = []
    for i in range(len(rows)):
        tx = xs[:i] + xs[i + 1:]
        ty = ys[:i] + ys[i + 1:]
        aa, bb = ols(tx, ty)
        errs.append(abs(ys[i] - (aa + bb * xs[i])))
    mae = st.mean(errs)
    sd = st.stdev(ys)
    print(f"  LOO MAE = {mae:.2f} pt   系列の SD = {sd:.2f} pt   平均だけの MAE = "
          f"{st.mean([abs(y - st.mean(ys)) for y in ys]):.2f} pt")
    if mae >= st.mean([abs(y - st.mean(ys)) for y in ys]):
        print("  → 難易度を使っても、毎年『平均を答える』より当たらない。翻訳は不可能。")
    else:
        print("  → 平均を答えるよりはわずかに当たるが、実用水準ではない。")
    print("     旧 README は『11年OOSで MAE 6.65pt > 変動σ 4.09pt』と書いていた。")
    print("     標本の取り方が違うため数値は一致しないが、結論は同じ。")

    print(header("仮説3: 需要のパススルーが最低点順位とともに減衰する"))
    print("  → p08_ratio.py に統合した。within の傾きは符号すら安定しない。検出力不足。")

    print(header("仮説4: 得点開示から科目間相関を推定する"))
    print("  → p06_niji.py §5 の通り、工学部の有効件数は 4。相関の推定には使えない。")
    print("     旧 README の『工学部分が11件』は全学部合計との取り違えだった。")

    print(header("仮説5: 第1段階選抜（足切り）の実績"))
    print("  募集要項の条文（data/r9.txt 5207行）:")
    print("    『工学部全体の入学志願者が工学部募集人員の約 3.0 倍を上回った場合、")
    print("      大学入学共通テストの利用教科・科目の得点の合計により第1段階選抜を行う』")
    print("  第1段階選抜の配点は本選抜と別で、共テ1000点満点")
    print("  （国200/地公100/数200/理200/外200/情100）。")
    print("  旧 README は『10年で除外は7人(0.18%)』と書いていたが、")
    print("  その根拠データはリポジトリに存在しない。再現できないので数値は取り下げ、")
    print("  条文だけを残す。必要なら各年度の入試実施状況から再収集すること。")


if __name__ == "__main__":
    main()
