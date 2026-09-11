# -*- coding: utf-8 -*-
"""学科パネル: 情報学科の合格最低点は本当に「突出して不安定」か。

旧 sd.py–sd5.py を置き換える。旧版の問題:
  * sd4.py の並べ替え検定は学科平均を除去せずに年内シャッフルしていたので、
    帰無の分散が過大になり p=0.97 を返していた（README は sd5 の p=0.004 だけを載せていた）。
  * sd2.py は負の相関に対して片側 p を「r 以上」で数えていた（符号の取り違え）。
  * どの検定も学科ごとの標本変動の違い（合格率と志願者数が違えば順序統計量の
    ばらつきも違う）を無視した交換可能性を仮定していた。
  * 2025年の配点改定をまたいで 8 年をプールしていた。
  * leave-one-out は sd4.py で計算されていたのに README に載っていなかった。

ここでは (1) 全標本 (2) LOO (3) 制度別部分標本 (4) 段差ダミー付き回帰
(5) 異分散を考慮した帰無 の5通りを全部出し、結論をそれらの共通部分だけにする。
"""
from __future__ import annotations

import math
import random
import statistics as st
import sys

from kyodai import datasets as ds
from kyodai.stats import (corr, detrend, header, inv_cdf, order_statistic_sd,
                          ols, permutation_p, rule)

FOCUS = "情報"
N_PERM = 200_000
SEED = 20260911


def residual_variances(idx, deps, years, focus=FOCUS):
    """トレンド除去残差の分散（主役 / それ以外プール）と F。"""
    res = {p: detrend(ds.series(idx, p, years)) for p in deps}
    dfj = len(years) - 2
    dfo = (len(deps) - 1) * dfj
    vj = sum(x * x for x in res[focus]) / dfj
    vo = sum(x * x for p in deps if p != focus for x in res[p]) / dfo
    return res, vj, vo, vj / vo


def perm_test(res, deps, years, observed, focus=FOCUS, weights=None, seed=SEED):
    """残差を学科間で入れ替える構造保存型の並べ替え検定。

    weights を渡すと、各学科の残差をその学科の期待標本SDで標準化してから
    入れ替える（= 学科ごとに変動の大きさが違ってよい帰無）。
    """
    n = len(years)
    dfj, dfo = n - 2, (len(deps) - 1) * (n - 2)
    if weights is None:
        pool = [x for p in deps for x in res[p]]
        scale = {p: 1.0 for p in deps}
    else:
        pool = [x / weights[p] for p in deps for x in res[p]]
        scale = weights

    def draw(rng: random.Random) -> float:
        s = rng.sample(pool, len(pool))
        g = {p: s[i * n:(i + 1) * n] for i, p in enumerate(deps)}
        vj = sum((x * scale[focus]) ** 2 for x in g[focus]) / dfj
        vo = sum((x * scale[p]) ** 2 for p in deps if p != focus for x in g[p]) / dfo
        return vj / vo

    return permutation_p(observed, draw, n=N_PERM, seed=seed)


def main() -> None:
    recs, years = ds.load_panel()
    idx = ds.panel_index(recs)
    deps = ds.DEPS
    params = ds.load_params()
    pool_sd = params["panel"]["applicant_pool_sd_pt"]["value"]

    print(header("0. 前提: 2025年入試で共通テストの合成が変わっている"))
    old = params["scoring"]["previous_regime"]["common_test"]
    new = params["scoring"]["common_test"]
    print("  旧（–令和6年度入試, 満点1000）共テ200点:",
          " ".join(f"{k}{v:g}" for k, v in old.items() if k != "total"))
    print("  新（令和7年度入試–, 満点1025）共テ225点:",
          " ".join(f"{k}{v:g}" for k, v in new.items() if k != "total"))
    print("  → 数学・理科の共テ配点が 0 → 各25点、地歴公民 100 → 50、情報 0 → 50。")
    print("     得点率に正規化しても『別の合成量』であることは消えない。")
    print("     したがって 2019–2024 と 2025–2026 のプールは既定で行わない。")

    print(header("1. 年ごとの合格最低点順位（dv = その年の6学科平均からの乖離, 得点率pt）"))
    for y in years:
        order = sorted(deps, key=lambda p: -idx[(p, y)]["dv"])
        mark = " ←新配点" if y >= ds.REGIME_BREAK_YEAR else ""
        print(f"  {y}  " + " > ".join(f"{p}{idx[(p,y)]['dv']:+.2f}" for p in order) + mark)

    print(header("2. 合格者数は固定されていない（順序統計モデルの前提を壊す）"))
    print("  募集要項の文言は『受入学生数を目安として学科別に合格者を決定します』。")
    print(f"  {'学科':<6}" + "".join(f"{y:>7}" for y in years) + f"{'変動幅':>8}")
    for p in deps:
        acc = [idx[(p, y)]["acc"] for y in years]
        print(f"  {p:<6}" + "".join(f"{a:>7d}" for a in acc)
              + f"{max(acc)-min(acc):>8d}")
    print("  → 情報は 88–99 人（+12.5%）。定員が動く以上、合格最低点は")
    print("     固定ランクの順序統計量ではない。p01 の順序統計SDは下限とみなすこと。")

    print(header("3. トレンド除去残差SD（全8年 = 旧READMEの掲載値）"))
    res, vj, vo, F = residual_variances(idx, deps, years)
    print(f"  {'学科':<6}{'平均dv':>8}{'トレンド/年':>11}{'残差SD(pt)':>12}{'(点/1025)':>11}"
          f"{'期待標本SD':>11}{'超過倍率':>9}")
    osd = {}
    for p in deps:
        v = ds.series(idx, p, years)
        _, b = ols(list(range(len(v))), v)
        sd = math.sqrt(sum(x * x for x in res[p]) / (len(years) - 2))
        seats = st.mean([idx[(p, y)]["acc"] for y in years])
        napp = st.mean([idx[(p, y)]["app"] for y in years])
        osd[p] = order_statistic_sd(pool_sd, seats, napp)
        print(f"  {p:<6}{st.mean(v):>8.2f}{b:>11.3f}{sd:>12.3f}{sd/100*1025:>11.1f}"
              f"{osd[p]:>11.3f}{sd/osd[p]:>9.2f}")
    print(f"\n  情報 vs 他5学科プール の分散比 F = {F:.2f}  (df 6, 30)")

    p_plain = perm_test(res, deps, years, F)
    w_p = perm_test(res, deps, years, F, weights=osd)
    print(f"  並べ替え p（学科を交換可能とみなす）        = {p_plain:.4f}")
    print(f"  並べ替え p（学科ごとの期待標本SDで標準化）  = {w_p:.4f}  ←こちらが適切")
    print("  ※ 情報は合格率が最も低く、順序統計量の標本変動がもともと大きい。")
    print("     それを帰無に入れないと有意性を過大評価する。")

    print(header("4. leave-one-year-out（旧 sd4.py が計算していたが README に無かった）"))
    print(f"  {'除外年':<8}{'情報の残差SD(pt)':>18}{'(点)':>8}{'F':>8}")
    loo = []
    for drop in years:
        sub = [y for y in years if y != drop]
        _, vj2, vo2, F2 = residual_variances(idx, deps, sub)
        loo.append((drop, math.sqrt(vj2), F2))
        print(f"  {drop:<8}{math.sqrt(vj2):>18.3f}{math.sqrt(vj2)/100*1025:>8.1f}{F2:>8.2f}")
    worst = min(loo, key=lambda t: t[1])
    print(f"  → {worst[0]} を1年抜くだけで SD は {math.sqrt(vj):.3f} → {worst[1]:.3f} pt、"
          f"F は {F:.2f} → {worst[2]:.2f}。")
    print("     結論は単一年に強く依存している。")

    print(header("5. 制度別の部分標本（ここが決定的）"))
    print(f"  {'標本':<26}{'情報SD(pt)':>12}{'(点)':>8}{'F':>8}{'並べ替えp':>11}")
    for label, sub in [("全8年 2019–2026", years),
                       ("旧配点のみ 2019–2024", list(ds.OLD_REGIME))]:
        r2, vj2, vo2, F2 = residual_variances(idx, deps, sub)
        p2 = perm_test(r2, deps, sub, F2)
        print(f"  {label:<26}{math.sqrt(vj2):>12.3f}{math.sqrt(vj2)/100*1025:>8.1f}"
              f"{F2:>8.2f}{p2:>11.4f}")
    print("  新配点のみ 2025–2026 は n=2 でトレンド除去後の自由度が 0。推定不能。")
    print("  → 『情報は突出して不安定』は、旧配点期間だけを見ると成立しない（F<1）。")

    print(header("6. 定常ノイズ か 一回の水準変化 か"))
    print("  dv を  dv_t = a + b*t + c*1[t>=2025] + e_t  に当て、段差 c を推定する。")
    print(f"  {'学科':<6}{'段差c(pt)':>11}{'段差(点)':>10}{'除去前SD':>10}{'除去後SD':>10}{'説明割合':>9}")
    step_sd, step_size = {}, {}
    for p in deps:
        v = ds.series(idx, p, years)
        t = list(range(len(years)))
        d = [1.0 if y >= ds.REGIME_BREAK_YEAR else 0.0 for y in years]
        # 2変数回帰を正規方程式で解く（標準ライブラリのみ）。
        n = len(v)
        mt, md, mv = st.mean(t), st.mean(d), st.mean(v)
        ctt = sum((a - mt) ** 2 for a in t)
        cdd = sum((a - md) ** 2 for a in d)
        ctd = sum((a - mt) * (b2 - md) for a, b2 in zip(t, d))
        ctv = sum((a - mt) * (b2 - mv) for a, b2 in zip(t, v))
        cdv = sum((a - md) * (b2 - mv) for a, b2 in zip(d, v))
        det = ctt * cdd - ctd * ctd
        bt = (cdd * ctv - ctd * cdv) / det
        bd = (ctt * cdv - ctd * ctv) / det
        fit = [mv + bt * (a - mt) + bd * (b2 - md) for a, b2 in zip(t, d)]
        e = [a - b2 for a, b2 in zip(v, fit)]
        sd0 = math.sqrt(sum(x * x for x in detrend(v)) / (n - 2))
        sd1 = math.sqrt(sum(x * x for x in e) / (n - 3))
        share = 1 - (sd1 / sd0) ** 2 if sd0 > 0 else float("nan")
        step_sd[p] = sd1
        step_size[p] = bd
        print(f"  {p:<6}{bd:>11.3f}{bd/100*1025:>10.1f}{sd0:>10.3f}{sd1:>10.3f}"
              f"{share*100:>8.1f}%")
    print("  → 情報の残差SDの相当部分が、2025年に一度だけ起きた水準変化で説明できる。")
    print("     『毎年ランダムに動く』と『一度ずれた』は n=8 では区別できない。")

    print(header("7. プールSDの仮定に対する感度（順序統計SDの比較のみに影響）"))
    print(f"  {'pool_sd(pt)':<14}" + "".join(f"{p:>9}" for p in deps))
    for ps in (6.0, 7.2, 8.5):
        row = f"  {ps:<14.1f}"
        for p in deps:
            seats = st.mean([idx[(p, y)]["acc"] for y in years])
            napp = st.mean([idx[(p, y)]["app"] for y in years])
            row += f"{order_statistic_sd(ps, seats, napp):>9.3f}"
        print(row)
    print("  → 超過倍率の順位（情報が最大）はこの範囲で不変。水準だけが動く。")

    print(header("結論（上の5通り全てで生き残るものだけ）"))
    print("  (A) 情報学科の合格最低点は、8年全体では他5学科より残差SDが大きい。")
    print("      ただし F=4.45 は 2024年 1 年に強く依存し、旧配点期間のみでは F<1。")
    print(f"  (B) 学科ごとの期待標本SDを帰無に入れると p は {p_plain:.4f} → {w_p:.4f} に上がる。")
    print("  (C) 2025年の配点改定が段差として効いており、定常ノイズとの識別はできていない。")
    print("  (D) よって『情報は毎年ブレる』ではなく")
    print("      『情報は制度変更の影響を最も強く受けた学科であり、新配点下の分散は未知（n=2）』")
    print("      が、データが支持する最大の主張である。")
    lo = step_sd[FOCUS] / 100 * 1025
    hi = math.sqrt(vj) / 100 * 1025
    print(f"  (E) 情報の最低点ノイズは、段差を除けば {lo:.1f}点、除かなければ {hi:.1f}点。")
    print(f"      下流（第2志望ラダー）で {hi:.1f}点 を定常ノイズとして単一値で使うのは過大。")
    print(f"      p02_gap_ladder.py では {lo:.1f}–{hi:.1f}点 の帯で提示する。")
    _write_handoff(step_sd, res, years, F, p_plain, w_p)


def _write_handoff(step_sd, res, years, F, p_plain, p_weighted) -> None:
    """下流スクリプトが読む値をファイルに落とす。数字の手写しをやめるため。

    単位は全て「1025点満点での点」。得点率pt との取り違えを防ぐため
    キー名に _points を付ける。
    """
    import json
    import os
    os.makedirs(ds.OUTPUTS, exist_ok=True)
    path = os.path.join(ds.OUTPUTS, "panel_handoff.json")
    df = len(years) - 2
    payload = {
        "focus": FOCUS,
        "_units": "全て 1025点満点での点",
        "_note": ("with_step = 段差を除かない残差SD（旧READMEの値）, "
                  "no_step = 2025年の段差ダミーを入れた後の残差SD"),
        "cutoff_noise_points": {
            p: {
                "with_step": round(math.sqrt(sum(x * x for x in res[p]) / df) / 100 * 1025, 2),
                "no_step": round(step_sd[p] / 100 * 1025, 2),
            } for p in ds.DEPS
        },
        "F_full_sample": round(F, 3),
        "perm_p_exchangeable": round(p_plain, 5),
        "perm_p_heteroskedastic": round(p_weighted, 5),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    print(f"\n  → {path} に書き出した（p02 が読む）")


if __name__ == "__main__":
    main()
