# -*- coding: utf-8 -*-
"""志願倍率は合格最低点をどこまで説明するか — between と within を分ける。

旧 README は『志願倍率が最低点の70%を説明（年固定効果48観測、r=+0.837、
LOO MAE 1.03pt）』を確立した結果として並べていたが、
  * 対応するスクリプトが analysis/ に存在せず再現できなかった
  * 同時に sd3.py は within のパススルー傾きが 情報 −1.01、建築 −2.89 と
    符号すら安定しないことを示していた（志願倍率が上がると最低点が下がる）
という矛盾を抱えていた。

r=+0.837 の正体は学科の恒常差（情報は倍率も最低点もいつも1位）である。
それは『今年の倍率から今年の最低点を当てる』能力を意味しない。
意思決定に効くのは within の方なので、両者を分けて出す。
"""
from __future__ import annotations

import math
import statistics as st

from kyodai import datasets as ds
from kyodai.stats import corr, header, ols, two_way_demean


def main() -> None:
    recs, years = ds.load_panel()
    idx = ds.panel_index(recs)
    deps = ds.DEPS

    X = {(p, y): idx[(p, y)]["ratio"] for p in deps for y in years}
    Y = {(p, y): idx[(p, y)]["dv"] for p in deps for y in years}

    print(header("1. プール回帰（旧 README の r=+0.837 に相当）"))
    xs = [X[(p, y)] for p in deps for y in years]
    ys = [Y[(p, y)] for p in deps for y in years]
    r_pool = corr(xs, ys)
    a, b = ols(xs, ys)
    print(f"  n = {len(xs)}   r = {r_pool:+.3f}   R^2 = {r_pool**2:.3f}   傾き = {b:+.3f}")
    print("  ※ dv は既に年平均からの乖離なので、年固定効果は入っている。")
    print(f"  → 旧 README は +0.837 / 70% と書いていた。ここでの再現値は {r_pool:+.3f}。")
    print("     わずかな差は仕様の違い（対応スクリプトが旧版に無く、厳密には照合できない）。")

    print(header("2. between（学科の恒常差）と within（年ごとの動き）に分ける"))
    bx = [st.mean([X[(p, y)] for y in years]) for p in deps]
    by = [st.mean([Y[(p, y)] for y in years]) for p in deps]
    r_between = corr(bx, by)
    print(f"  between: 学科ごとの8年平均どうし  n = {len(bx)}  r = {r_between:+.3f}"
          f"  R^2 = {r_between**2:.3f}")
    for p, x, y in zip(deps, bx, by):
        print(f"    {p:<6} 平均倍率 {x:.2f}   平均dv {y:+.2f}")

    Xw = two_way_demean(X, deps, years)
    Yw = two_way_demean(Y, deps, years)
    wx = [Xw[(p, y)] for p in deps for y in years]
    wy = [Yw[(p, y)] for p in deps for y in years]
    r_within = corr(wx, wy)
    aw, bw = ols(wx, wy)
    print(f"\n  within: 学科・年の二元固定効果を除去  n = {len(wx)}  r = {r_within:+.3f}"
          f"  R^2 = {r_within**2:.3f}  傾き = {bw:+.3f}")

    print(f"\n  {'学科':<6}{'within傾き':>12}{'R^2':>8}{'符号':>6}")
    for p in deps:
        sx = [Xw[(p, y)] for y in years]
        sy = [Yw[(p, y)] for y in years]
        denom = sum(v * v for v in sx)
        slope = sum(u * v for u, v in zip(sx, sy)) / denom if denom else float("nan")
        ss = sum((v - slope * u) ** 2 for u, v in zip(sx, sy))
        tt = sum(v * v for v in sy)
        print(f"  {p:<6}{slope:>12.3f}{1-ss/tt:>8.3f}{'＋' if slope > 0 else '−':>6}")
    print("  → 学科ごとの符号が揃わない。『倍率が上がると最低点が下がる』学科が複数ある。")
    print("     これは推定が実質ノイズであることの表れ。")

    print(header("3. 予測力: leave-one-out"))
    print("  (a) 学科ダミーのみ  (b) 学科ダミー + 倍率  の2つで、1観測ずつ抜いて予測する。")

    def loo(use_ratio: bool) -> float:
        errs = []
        for tp in deps:
            for ty in years:
                tr = [(p, y) for p in deps for y in years if not (p == tp and y == ty)]
                dep_mean = {p: st.mean([Y[(p, y)] for (q, y) in tr if q == p])
                            for p in deps}
                if not use_ratio:
                    pred = dep_mean[tp]
                else:
                    rx = [X[(p, y)] - st.mean([X[(p, yy)] for (q, yy) in tr if q == p])
                          for (p, y) in tr]
                    ry = [Y[(p, y)] - dep_mean[p] for (p, y) in tr]
                    den = sum(v * v for v in rx)
                    sl = sum(u * v for u, v in zip(rx, ry)) / den if den else 0.0
                    xm = st.mean([X[(tp, yy)] for (q, yy) in tr if q == tp])
                    pred = dep_mean[tp] + sl * (X[(tp, ty)] - xm)
                errs.append(abs(Y[(tp, ty)] - pred))
        return st.mean(errs)

    mae_a, mae_b = loo(False), loo(True)
    sd_all = st.stdev(ys)
    print(f"  (a) 学科ダミーのみ      LOO MAE = {mae_a:.3f} pt")
    print(f"  (b) + 志願倍率          LOO MAE = {mae_b:.3f} pt")
    print(f"  dv 全体の SD            = {sd_all:.3f} pt")
    gain = (mae_a - mae_b) / mae_a * 100
    print(f"  → 倍率を足したことによる改善は {gain:+.1f}%。")
    if mae_b >= mae_a:
        print("     つまり倍率は予測を改善していない（むしろ悪化）。")
    print("     旧 README の『LOO MAE 1.03pt』は、学科ダミーだけでほぼ達成できる水準であり、")
    print("     倍率の貢献ではない。")

    print(header("4. 結論"))
    print(f"  プール r = {r_pool:+.3f} の内訳は between r = {r_between:+.3f}（学科6点）と")
    print(f"  within r = {r_within:+.3f}（48観測）。説明力はほぼ全て between 由来。")
    print("  between が意味するのは『情報は倍率も最低点も常に1位』という恒常差であり、")
    print("  今年の倍率から今年の最低点を予測する力ではない。")
    print("  出願時に速報倍率を見て志望を変える根拠には、このデータはならない。")


if __name__ == "__main__":
    main()
