# -*- coding: utf-8 -*-
"""募集人員の付け替え — 過去データに入っていない唯一の前向き情報。

合格最低点を決めるのは（定員, 志願者数, 志願者の学力分布, 問題の難易度）の4つ。
このうち出願前に公開されているのは **定員だけ** である。
志願者数の速報は出願締切後、学力分布と難易度は原理的に事前には分からない。

つまり「過去の最低点をいくら精密に分析しても出てこないが、
募集要項を読めば分かる」情報は定員しかない。そして旧版も改訂版も、
定員を『順序統計量の n』としてしか使っておらず、
**年をまたぐ定員の変化を一度も見ていなかった。**

令和6年度と令和9年度の募集要項を比べると、工学部の総定員はほぼ不変なのに
学科間で付け替えが起きている。
"""
from __future__ import annotations

import statistics as st

from kyodai import datasets as ds
from kyodai.stats import header, inv_cdf

# 募集人員（前期日程・受入学生数目安）。出典は各年度の募集要項。
SEATS = {
    "令和6年度": {"地球工": 181, "建築": 77, "物理工": 230, "電電": 123, "情報": 87, "理工化": 225},
    "令和9年度": {"地球工": 175, "建築": 77, "物理工": 225, "電電": 128, "情報": 94, "理工化": 215},
}
SRC = {"令和6年度": "data/r6senbatsu.txt", "令和9年度": "data/r9.txt"}


def main() -> None:
    recs, years = ds.load_panel()
    idx = ds.panel_index(recs)
    params = ds.load_params()
    pool = params["panel"]["applicant_pool_sd_pt"]["value"] * 10.25   # 点/1025

    print(header("1. 募集人員の推移（一次資料）"))
    for k, v in SRC.items():
        print(f"  {k}: {v}")
    a, b = SEATS["令和6年度"], SEATS["令和9年度"]
    print(f"\n  工学部計  {sum(a.values())} → {sum(b.values())}  ({sum(b.values())-sum(a.values()):+d})")
    print(f"  {'学科':<7}{'令和6':>7}{'令和9':>7}{'増減':>7}{'変化率':>9}")
    for d in ds.DEPS:
        print(f"  {d:<7}{a[d]:>7}{b[d]:>7}{b[d]-a[d]:>+7}{(b[d]/a[d]-1)*100:>8.1f}%")
    print("\n  → 総定員はほぼ不変。情報(+8.0%)と電電(+4.1%)に、")
    print("     理工化(-4.4%)・地球工(-3.3%)・物理工(-2.2%)から付け替えられている。")

    print(header("2. 定員変化が合格最低点に与える機械的な効果"))
    print("  合格最低点は『上から定員番目』の順序統計量。定員が増えれば順位の線が下がる。")
    print(f"  志願者数は直近8年平均で固定し、志願者の反応はゼロと置く（上限ケース）。")
    print(f"  志願者プールの得点SD = {pool:.1f}点/1025")
    print(f"\n  {'学科':<7}{'志願者':>8}{'合格率R6':>10}{'合格率R9':>10}{'最低点の変化':>14}")
    delta = {}
    for d in ds.DEPS:
        app = st.mean([idx[(d, y)]["app"] for y in years])
        p6, p9 = a[d] / app, b[d] / app
        delta[d] = pool * (inv_cdf(1 - p9) - inv_cdf(1 - p6))
        print(f"  {d:<7}{app:>8.0f}{p6:>10.3f}{p9:>10.3f}{delta[d]:>+13.1f}点")

    print(header("3. これは第2志望ラダー（p02）の前提を動かす"))
    print("  ラダーは『情報 − 相手学科』の8年平均ギャップを使っている。")
    print("  定員の付け替えは、そのギャップを機械的に縮める方向に働く。")
    print(f"  {'第2志望':<8}{'8年平均ギャップ':>16}{'定員効果':>11}{'補正後':>10}{'変化率':>9}")
    for d in ds.DEPS[1:]:
        g = st.mean([(idx[("情報", y)]["dv"] - idx[(d, y)]["dv"]) * 10.25 for y in years])
        shift = delta["情報"] - delta[d]
        print(f"  {d:<8}{g:>15.1f}点{shift:>+10.1f}{g+shift:>9.1f}{(shift/g)*100:>8.1f}%")
    _g = st.mean([(idx[("情報", y)]["dv"] - idx[("理工化", y)]["dv"]) * 10.25 for y in years])
    _s = delta["情報"] - delta["理工化"]
    print(f"\n  → 情報と理工化の差は {_g:.1f}点 から {abs(_s):.1f}点 縮んで {_g+_s:.1f}点。")
    print("     第2志望の価値は、過去データが示すより小さい。")
    print("     順序（理工化 > 地球工 > 建築 > 電電 > 物理工）は変わらない。")

    print(header("4. 限界"))
    print("  * 志願者は定員増に反応して増えうる。その分だけ効果は相殺される。")
    print("    2019–2026 のパネルでは定員と志願者数の相関は下記の通り。")
    for d in ds.DEPS:
        acc = [idx[(d, y)]["acc"] for y in years]
        app = [idx[(d, y)]["app"] for y in years]
        ma, mb = st.mean(acc), st.mean(app)
        num = sum((x - ma) * (y - mb) for x, y in zip(acc, app))
        den = (sum((x - ma) ** 2 for x in acc) * sum((y - mb) ** 2 for y in app)) ** 0.5
        print(f"      {d:<7} corr(合格者数, 志願者数) = {num/den if den else float('nan'):+.2f}")
    print("  * 『受入学生数目安』であって固定定員ではない。実際の合格者数は目安から外れる。")
    print("    情報の実績は 88–99 人で、令和9年度の目安 94 はその範囲内。")
    print("  * 正規分布の順序統計量近似を使っている。裾では誤差が出る。")
    print("  * 令和7・8年度の募集要項が手元に無く、2点間の比較になっている。")
    print("    中間年を足せば付け替えが連続的か一度きりかが分かる。→ 次の作業")


if __name__ == "__main__":
    main()
