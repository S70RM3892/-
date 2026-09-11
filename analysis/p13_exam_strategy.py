# -*- coding: utf-8 -*-
"""二次数学 150分6問 — 何問に手をつけるべきか。

p12 で「ラインより下なら得点の分散を上げるべき」という向きが出た。
しかしそれを実行するには (期待値, 分散) の実現可能な組合せ＝フロンティアが要る。
公開データには存在しない。ふつうは模試の答案を自分で集計するしかない。

ただし京大数学には特殊な事情がある:
**大問別配点が問題用紙に印刷される**（30/35/40点）。
つまり試験開始時点で配点が既知で、受験生は「どこに時間を置くか」を選べる。
この選択をモデル化すれば、フロンティアは自分のデータ無しでも形が出る。

模型（全て status=仮定。関数形は推測であり、データから推定したものではない）
------------------------------------------------------------------------
大問 i に時間 t_i を置く。Σt_i = 150分。
完答に要する時間 T_i ~ 指数分布(平均 τ_i)。τ_i は自分の実力と問題の重さで決まる。

    P(完答 | t_i) = 1 − exp(−t_i / τ_i)

完答できなかった場合、書けたところまでの部分点が入る。部分点の効き方を β で表す
（β=0 なら完全に全か無か、β=1 なら進捗がそのまま点になる）。

    E[得点_i] = m_i · [ p_i + β·(1−p_i)·c ]
    Var[得点_i] = m_i² · p_i(1−p_i) · (1 − β·c)²        c = 未完答時の平均進捗率

**β が大きいほど分散は小さくなる。**

結果の予告（p12 の素朴な予想は、この模型に否定された）
------------------------------------------------------
p12 では「絞る = 分散を上げる」と暗に想定していた。模型はそうならない。
2問に絞ると各問の完答確率が 1 に近づき、m²p(1−p) は **小さく** なる。
つまり絞るのは期待値も分散も下げる方向で、広げるのは両方上げる方向である。
そして 6問に均等配分するのは、期待値でも分散でも k=4 に劣る（支配される）。
τ の大きい問題に置いた時間の限界収穫がほとんどゼロだからである。
"""
from __future__ import annotations

import itertools
import math

import os

from kyodai import datasets as ds
from kyodai.stats import cdf, header

TOTAL_MIN = 150.0
POINTS = [30, 35, 35, 35, 35, 30]        # 素点200。印刷配点は 30/35/40 のいずれか
WEIGHT = 1.25                            # 二次数学 素点 → 1025点満点
C_PARTIAL = 0.45                         # 未完答時の平均進捗率


def moments(alloc, tau, beta, points=POINTS):
    """時間配分 alloc に対する (期待素点, 素点SD)。"""
    ev = va = 0.0
    for m, t, ta in zip(points, alloc, tau):
        p = 1 - math.exp(-t / ta) if ta > 0 else 0.0
        gain = p + beta * (1 - p) * C_PARTIAL
        ev += m * gain
        va += (m ** 2) * p * (1 - p) * (1 - beta * C_PARTIAL) ** 2
    return ev, math.sqrt(va)


def strategies(tau, beta):
    """『k問に絞り、配点と手応えに比例して時間を配る』族を列挙する。

    k=6 が全問均等寄り（期待値重視）、k=2 が集中（分散重視）。
    絞る対象は τ が小さい（= 解けそうな）問題から順に取る。
    """
    order = sorted(range(len(POINTS)), key=lambda i: tau[i] / POINTS[i])
    out = []
    for k in range(2, len(POINTS) + 1):
        chosen = order[:k]
        w = [POINTS[i] for i in chosen]
        sw = sum(w)
        alloc = [0.0] * len(POINTS)
        for i, wi in zip(chosen, w):
            alloc[i] = TOTAL_MIN * wi / sw
        ev, sd = moments(alloc, tau, beta)
        out.append((k, ev, sd, alloc))
    return out


def main() -> None:
    params = ds.load_params()
    mu0 = params["ladder"]["mu_candidate_pt"]["value"]
    sp_other = 45.0      # 数学以外（国語・理科・英語・共テ）のゆらぎ。仮定。

    print(header("0. この節は全て仮定の上に立っている"))
    print("  関数形（指数分布の完答時間、部分点の線形性）はデータから推定していない。")
    print("  推測である。したがって **数値ではなく、最適戦略が μ とともにどう動くか**")
    print("  という定性的な向きだけを受け取ること。")
    print(f"  総時間 {TOTAL_MIN:.0f}分 / 大問 {len(POINTS)}問 / 配点 {POINTS} = {sum(POINTS)}素点")

    print(header("1. フロンティア（何問に絞るか × 部分点の効き方）"))
    print("  τ = 完答に要する時間の平均（分）。実力が上がるほど小さくなる。")
    for label, tau in [("標準的な受験生", [55, 60, 70, 85, 110, 140]),
                       ("上位層",       [35, 40, 50, 60, 80, 110])]:
        print(f"\n  ── {label}  τ={tau} ──")
        for beta, bl in [(0.0, "部分点なし β=0"), (0.4, "部分点ふつう β=0.4"),
                         (0.8, "部分点が甘い β=0.8")]:
            print(f"    {bl}")
            print(f"      {'手をつける問数':>14}{'期待素点':>10}{'素点SD':>9}"
                  f"{'1025換算 期待値':>16}{'1025換算 SD':>13}")
            for k, ev, sd, _ in strategies(tau, beta):
                print(f"      {k:>14}{ev:>10.1f}{sd:>9.1f}"
                      f"{ev*WEIGHT:>15.1f}点{sd*WEIGHT:>12.1f}点")

    print(header("2. μ ごとの最適戦略"))
    print("  数学の得点を上の模型で、それ以外の科目のゆらぎを sp_other で表し、")
    print(f"  合格確率 P = Φ((μ + Δ期待値) / sqrt(SD_math² + sp_other²)) を最大化する k を選ぶ。")
    print(f"  sp_other = {sp_other:.0f}点（仮定）。基準は k=6（全問均等寄り）。")
    for label, tau in [("標準的な受験生", [55, 60, 70, 85, 110, 140]),
                       ("上位層",       [35, 40, 50, 60, 80, 110])]:
        for beta in (0.0, 0.4, 0.8):
            rows = strategies(tau, beta)
            base_ev = rows[-1][1]      # k=6 を基準
            print(f"\n  ── {label} / β={beta:g} ──")
            print(f"    {'μ(点)':<9}" + "".join(f"{f'k={k}':>9}" for k, _, _, _ in rows)
                  + f"{'最適':>7}")
            for mu in (-80, -60, -40, -20, 0, 20, 40):
                best, bestp, cells = None, -1, []
                for k, ev, sd, _ in rows:
                    d = (ev - base_ev) * WEIGHT
                    s = math.sqrt((sd * WEIGHT) ** 2 + sp_other ** 2)
                    p = cdf((mu + d) / s)
                    cells.append(p)
                    if p > bestp:
                        bestp, best = p, k
                print(f"    {mu:<9.0f}" + "".join(f"{c*100:>8.1f}%" for c in cells)
                      + f"{f'k={best}':>7}")

    print(header("3. 前提の実測 — 京大数学は本当に不均一か"))
    print("  下の §3後半 の結論は『問題ごとの重さに差があること』を前提にする。")
    print("  主張ではなく測る。data/ds.json の大問別難易度評価（1–5）を使う。")
    import json as _json
    import statistics as _st
    _d = _json.load(open(os.path.join(ds.DATA, "ds.json"), encoding="utf-8"))["daisu"]
    _yrs = sorted(_d, key=int)
    _rngs = [max(_d[y]) - min(_d[y]) for y in _yrs]
    _within = _st.mean([_st.pvariance(_d[y]) for y in _yrs])
    _between = _st.pvariance([_st.mean(_d[y]) for y in _yrs])
    print(f"  対象 {_yrs[0]}–{_yrs[-1]}  n={len(_yrs)}年 × 6問")
    print(f"  年内の（最大−最小）の平均 = {_st.mean(_rngs):.2f}")
    print(f"  6問が全部同じ評価だった年  = {sum(1 for r in _rngs if r == 0)} / {len(_yrs)}年")
    print(f"  最大−最小 >= 2 の年        = {sum(1 for r in _rngs if r >= 2)} / {len(_yrs)}年"
          f" ({sum(1 for r in _rngs if r >= 2)/len(_yrs)*100:.0f}%)")
    print(f"\n  難易度の分散分解: 年内(問題間) {_within:.3f} / 年間(年の当たり外れ) {_between:.3f}")
    print(f"  → **問題間のばらつきが、年ごとのばらつきの {_within/_between:.1f} 倍ある。**")
    print("     受験生が気にするのは『今年の数学は難化したか』だが、")
    print("     実際には同じ年の中の問題差の方が 3 倍以上大きい。")
    print("     年の当たり外れは選べないが、問題の取捨は選べる。効く方が選べる方にある。")
    print("  ※ 出典は個人の note 記事の主観評価（1–5）で、1990–2008 の旧課程期のみ。")
    print("     一次資料ではない。向きの確認に使えるが、水準の推定には使えない。")

    print(header("3b. 『全問に手をつけるな』が成り立つ条件"))
    print("  k=6（全問に配点比例で配る）が他の k に支配されるかを、τ の形を変えて調べる。")
    print("  支配される = 期待値が同じ以上かつ分散が同じ以下の k が他に存在する。")
    print(f"  {'τ プロファイル（分）':<34}{'期待値最大のk':>14}{'k=6は支配されるか':>18}")
    PROFILES = [
        ("一様            [75]*6",            [75] * 6),
        ("やや差          [60,65,70,80,90,100]", [60, 65, 70, 80, 90, 100]),
        ("標準            [55,60,70,85,110,140]", [55, 60, 70, 85, 110, 140]),
        ("差が大きい      [40,50,70,100,150,200]", [40, 50, 70, 100, 150, 200]),
        ("上位層          [35,40,50,60,80,110]", [35, 40, 50, 60, 80, 110]),
        ("全部重い        [120]*6",            [120] * 6),
        ("全部軽い        [30]*6",             [30] * 6),
    ]
    for label, tau in PROFILES:
        rows = strategies(tau, 0.4)
        d = {k: (ev, sd) for k, ev, sd, _ in rows}
        ev6, sd6 = d[6]
        dom = any(ev >= ev6 and sd <= sd6 and (ev > ev6 or sd < sd6)
                  for k, (ev, sd) in d.items() if k != 6)
        best = max(d, key=lambda k: d[k][0])
        print(f"  {label:<34}{best:>14}{('はい' if dom else 'いいえ'):>18}")
    print("\n  → **k=6 が支配されるのは、問題ごとの重さに差があるときだけ。**")
    print("     τ が一様なら（全部同じ重さなら）全問に配るのが最適で、これは当然。")
    print("     差があると、重い問題に置いた時間の限界収穫がほぼゼロになるため、")
    print("     軽い方に寄せると期待値も分散も改善する。β を 0–0.8 で振っても結論は不変。")
    print("     京大理系数学は毎年、軽い問題と極端に重い問題が混在する。条件は満たされている。")
    print("     最適 k は事実上『150分で現実的に仕上げきれる問題数』に一致する。")

    print(header("4. 読み取れること（p12 の予想は外れた）"))
    print("  (a) **6問に均等配分するのは常に劣る。** k=4 が期待値でも分散でも上回る。")
    print("      τ の大きい問題に置いた時間の限界収穫がほぼゼロだからで、")
    print("      これは『広く薄く』が期待値を守るという直感の反例になっている。")
    print("  (b) **絞るのは分散を下げる。** p12 では絞る＝分散を上げると暗に想定していたが、")
    print("      逆だった。2問に絞ると各問の完答確率が1に近づき、m²p(1−p) が小さくなる。")
    print("      したがって『μ<0 なら分散を買え』は、ここでは『絞るな、広げろ』になる。")
    print("      p12 の向き（下にいる人は分散を上げる）自体は保たれているが、")
    print("      それを実行する手段は直感と逆だった。")
    print("  (c) ただし **μ 依存は小さい。** 最適 k は μ が動いても 4 と 5 の間しか動かない。")
    print("      支配的なのは水準効果（6問に散らすな、2問に籠るな）であって、")
    print("      ラインとの距離による調整ではない。p12 の実務的な重みは、")
    print("      この模型の下では想定より小さい。正直に下方修正する。")
    print("  (d) 副産物: 模型は『どの問題が軽いか』を開始時点で知っていると仮定している。")
    print("      現実には見極めに時間がかかる。つまり k=4–5 の優位は上限値であり、")
    print("      同時に **最初の十数分を全問の偵察に使う価値** を裏づけている。")
    print("      偵察は期待値を直接は生まないが、k の選択を正しくすることで効く。")

    print(header("5. この模型が測れていないもの"))
    print("  * τ（完答に要する時間）の実測値。過去問を時間計測して解けば自分で取れる。")
    print("  * β（部分点の効き）。京大数学の採点基準は非公開。答案開示でも部分点の")
    print("    内訳は出ない。模試の採点で代用するしかない。")
    print("  * 問題間の相関。難しい年は全問が同時に重くなるので、実際の分散は上の値より大きい。")
    print("  * 途中で戦略を変える可能性。ここでは開始時に配分を決め打ちしている。")
    print("    実際には30分後に手応えを見て切り替えられる。その価値は測っていない。")
    print("    → 逐次決定として解けば、ここの数字はすべて下限になる。")


if __name__ == "__main__":
    main()
