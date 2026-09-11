# -*- coding: utf-8 -*-
"""第2志望ラダー: どの学科を第2志望に書くとどれだけ得か。

旧 sd6.py / sd7.py を置き換える。旧版の問題:
  * `sT=65.4; muT=-0.553*sT` が行内ハードコードで出典不明。
    しかも README 末尾には「ユーザー自身の模試成績は結論に使っていない」と
    書かれていたが、この2つは明らかに個人の得点分布パラメータだった。
  * 合格確率を 0.1% 刻みの単一値で出していた（原理的に存在しない精度）。
  * 「自分の得点 − 情報最低点」と「情報最低点 − 相手最低点」を独立として
    分散を足していた。両者は情報最低点を共有するので負相関する。
    しかも §ギャップ分散分解 で「ギャップ分散の 67–95% は情報の変動」と
    自分で示していたのに、式はそれと矛盾していた。
  * 8年平均ギャップを使っていたが、2025年に配点が変わっている。

ここでは共分散を正しく入れ、USER パラメータは帯で提示し、
配点改定前後を分けて出す。
"""
from __future__ import annotations

import json
import math
import os
import statistics as st

from kyodai import datasets as ds
from kyodai.stats import cdf, header, rule

FOCUS = "情報"
PT = 1025 / 100.0          # 得点率pt → 1025点満点での点


def gaps(idx, deps, years):
    """情報 − 各学科 の合格最低点差（点）。"""
    return {p: [(idx[(FOCUS, y)]["dv"] - idx[(p, y)]["dv"]) * PT for y in years]
            for p in deps if p != FOCUS}


def main() -> None:
    recs, years = ds.load_panel()
    idx = ds.panel_index(recs)
    deps = ds.DEPS
    params = ds.load_params()
    lad = params["ladder"]
    mu0 = lad["mu_candidate_pt"]["value"]
    sp0 = lad["sigma_performance_pt"]["value"]
    grid_mu = lad["sensitivity_grid"]["mu_candidate_pt"]
    grid_sp = lad["sensitivity_grid"]["sigma_performance_pt"]

    hand_path = os.path.join(ds.OUTPUTS, "panel_handoff.json")
    if not os.path.exists(hand_path):
        raise SystemExit("先に p01_panel.py を実行すること（outputs/panel_handoff.json が要る）")
    hand = json.load(open(hand_path, encoding="utf-8"))
    NOISE = hand["cutoff_noise_points"]        # 単位は 1025点満点での点
    sig_lo = NOISE[FOCUS]["no_step"]
    sig_hi = NOISE[FOCUS]["with_step"]

    print(header("0. この表がどのパラメータに依存しているか"))
    print(f"  mu   = 自分の実力 − 情報の合格最低点  : {mu0:+.1f}点  [status={lad['mu_candidate_pt']['status']}]")
    print(f"  sp   = 自分の当日ゆらぎ SD            : {sp0:.1f}点  [status={lad['sigma_performance_pt']['status']}]")
    print(f"  sig  = 情報の最低点ノイズ SD          : {sig_lo:.1f}–{sig_hi:.1f}点  [p01 由来]")
    print("  mu と sp は公開情報からは決まらない。以下の確率は『自分用の値を入れて読む表』であって、")
    print("  誰にでも当てはまる数値ではない。")
    print(f"  ※ 参考: 志願者プール全体の得点SDは約 {params['panel']['applicant_pool_sd_pt']['value']*PT:.0f}点。")
    print(f"     sp={sp0:.1f}点 はその {sp0/(params['panel']['applicant_pool_sd_pt']['value']*PT)*100:.0f}% で、"
          "個人の当日ゆらぎとしては大きすぎる可能性が高い。")

    print(header("1. 第2志望の流れが一方向であることの前提（定理ではなく仮説）"))
    print("  主張: c を第1志望として落ち d に第2志望で受かった人は 得点 < cutoff_c かつ 得点 >= cutoff_d。")
    print("        よって cutoff_c > cutoff_d。流入は最低点の高い学科から低い学科へしか起こらない。")
    print("  この導出は『学部全体を1本の点数順に並べ、各学科の定員まで順に取る』")
    print("  （serial dictatorship）を仮定している。しかし募集要項の文言は")
    print("    『工学部は、学部として募集しますが、受入学生数を目安として学科別に合格者を決定します』")
    print("  だけで、割り振り機構は書かれていない（data/r9.txt 614–618行）。")
    print("  第1志望者優先枠や同点処理の規定があれば定理は崩れる。")
    print("  → 『確定した制度事実』ではなく『作業仮説』として扱う。")
    print("  補強材料: 情報学科は 2019–2026 の8年すべてで最低点1位。")
    print("            仮説が正しければ情報への第2志望流入はゼロで、定員は100%が第1志望者。")

    print(header("2. 情報 − 各学科 の合格最低点差（点/1025）"))
    G = gaps(idx, deps, years)
    print(f"  {'年':<8}" + "".join(f"{p:>10}" for p in deps[1:]))
    for i, y in enumerate(years):
        mark = "*" if y >= ds.REGIME_BREAK_YEAR else " "
        print(f"  {y}{mark:<3}" + "".join(f"{G[p][i]:>10.1f}" for p in deps[1:]))
    print("  (* = 新配点)")
    print(f"\n  {'学科':<8}{'8年平均':>10}{'8年SD':>8}{'旧配点平均':>12}{'新配点平均':>12}{'差':>8}")
    n_old = len(ds.OLD_REGIME)
    for p in deps[1:]:
        g = G[p]
        o, nw = st.mean(g[:n_old]), st.mean(g[n_old:])
        print(f"  {p:<8}{st.mean(g):>10.1f}{st.stdev(g):>8.1f}{o:>12.1f}{nw:>12.1f}{nw-o:>8.1f}")
    print("  → 新配点の2年は全学科でギャップが縮んでいる。8年平均は旧配点期の値に引っ張られる。")

    print(header("3. ギャップ分散の分解（情報自身の動きが占める割合）"))
    Jd = [x - st.mean(ds.series(idx, FOCUS, years)) for x in ds.series(idx, FOCUS, years)]
    for p in deps[1:]:
        P = ds.series(idx, p, years)
        Pd = [x - st.mean(P) for x in P]
        vJ, vP = st.pvariance(Jd), st.pvariance(Pd)
        cov = sum(a * b for a, b in zip(Jd, Pd)) / len(Jd)
        vg = st.pvariance([a - b for a, b in zip(Jd, Pd)])
        print(f"  情報−{p:<5} ギャップ分散 {vg:6.3f} = 情報 {vJ:5.3f} + {p} {vP:5.3f} "
              f"− 2cov {cov:+6.3f}   情報の寄与 {vJ/(vJ+vP)*100:4.1f}%")
    print("  → ギャップのばらつきは主に情報自身の動き。")
    print("     つまり『自分の得点 − 情報最低点』と『ギャップ』は独立ではない。次節で効かせる。")

    print(header("4. 合格確率の式 — 旧版はギャップのSDを分母に入れていたが、それは誤り"))
    print("  T = 自分の得点 − cutoff_J,  gap = cutoff_J − cutoff_P （J = 情報, P = 第2志望）")
    print("  第2志望 P での合否は  T + gap >= 0。ところが")
    print("      T + gap = (得点 − cutoff_J) + (cutoff_J − cutoff_P) = 得点 − cutoff_P")
    print("  なので cutoff_J は完全に相殺される。よって")
    print("      Var(T + gap) = sp^2 + Var(cutoff_P)            ← 効くのは相手学科のノイズだけ")
    print("  旧 sd7.py は  sqrt(sp^2 + sig_J^2 + SD(gap)^2)  を分母にしていた。")
    print("  SD(gap) の 67–95% は情報自身の変動（§3）なのに、それを相殺せず足していたため、")
    print("  分母を二重どころか三重に膨らませていた。")
    print(f"\n  分母のうち『最低点に由来する部分』の大きさ（点）:")
    print(f"  {'学科':<8}{'旧版':>10}{'正しい値':>10}{'倍率':>8}"
          f"{'確率差 sp=30':>14}{'確率差 sp=64.5':>16}")
    for p in deps[1:]:
        g = G[p]
        gs = st.stdev(g)
        old_noise = math.sqrt(sig_hi ** 2 + gs ** 2)
        new_noise = NOISE[p]["with_step"]
        gm = st.mean(g)
        d30 = (cdf((mu0 + gm) / math.sqrt(30 ** 2 + new_noise ** 2))
               - cdf((mu0 + gm) / math.sqrt(30 ** 2 + old_noise ** 2))) * 100
        d64 = (cdf((mu0 + gm) / math.sqrt(sp0 ** 2 + new_noise ** 2))
               - cdf((mu0 + gm) / math.sqrt(sp0 ** 2 + old_noise ** 2))) * 100
        print(f"  {p:<8}{old_noise:>10.1f}{new_noise:>10.1f}{old_noise/new_noise:>7.1f}x"
              f"{d30:>+13.1f}pt{d64:>+15.1f}pt")
    print("  → 旧版は最低点由来のノイズを 2–6 倍に見積もっていた。")
    print("     ただし sp（自分の当日ゆらぎ）が支配的なので、最終確率への影響は数ポイント。")
    print("     式としては誤りだが、旧版の結論を数値的にひっくり返すほどではない。正直に言う。")

    def prob_at(mu, sp, sigma_dep, shift=0.0):
        return cdf((mu + shift) / math.sqrt(sp * sp + sigma_dep * sigma_dep))

    print(header("5. 第2志望ラダー（帯で提示）"))
    print(f"  mu={mu0:+.0f}点 固定。各セルは 段差除去後 / 除去前 の2通りの最低点ノイズによる帯。")
    print("  平均差は 8年平均 と 新配点2年 の両方で出す（配点改定でギャップは縮んでいる）。")
    for gap_mode, sl in (("8年平均", slice(None)), ("新配点2年", slice(n_old, None))):
        print(f"\n  【{gap_mode}】")
        print(f"  {'第2志望':<8}{'平均差':>8}" + "".join(f"{f'sp={s:g}':>12}" for s in grid_sp))
        for p in deps[1:]:
            shift = st.mean(G[p][sl])
            row = f"  {p:<8}{shift:>8.0f}"
            for sp in grid_sp:
                a = prob_at(mu0, sp, NOISE[p]["no_step"], shift) * 100
                b = prob_at(mu0, sp, NOISE[p]["with_step"], shift) * 100
                row += f"{f'{min(a,b):.0f}–{max(a,b):.0f}%':>12}"
            print(row)
        row = f"  {'（なし）':<8}{'—':>8}"
        for sp in grid_sp:
            a = prob_at(mu0, sp, sig_lo) * 100
            b = prob_at(mu0, sp, sig_hi) * 100
            row += f"{f'{min(a,b):.0f}–{max(a,b):.0f}%':>12}"
        print(row)

    print(f"\n  mu を振ったとき（sp={sp0:g}, 最低点ノイズは段差除去前, ギャップは8年平均）")
    print(f"  {'mu(点)':<9}" + "".join(f"{p:>10}" for p in deps[1:]) + f"{'なし':>10}")
    for mu in grid_mu:
        row = f"  {mu:<9.0f}"
        for p in deps[1:]:
            row += f"{prob_at(mu, sp0, NOISE[p]['with_step'], st.mean(G[p]))*100:>9.0f}%"
        row += f"{prob_at(mu, sp0, sig_hi)*100:>9.0f}%"
        print(row)

    print(header("6. この表から読み取ってよいこと / いけないこと"))
    order = sorted(deps[1:], key=lambda p: -st.mean(G[p]))
    print("  読み取ってよい（mu, sp, sig のどの値でも順序が変わらない）:")
    print(f"    第2志望の価値の順序 = {' > '.join(order)}")
    print("    これは平均ギャップの順序そのもので、つまり『最低点が最も低い学科を書け』に等しい。")
    print("    志願倍率で選ぶのは誤り（建築は倍率2.12位に対し最低点3.62位）。")
    print("    自分の第1志望より最低点が高い学科を第2志望に書いても、仮説1の下では物理的に無効。")
    print("  読み取ってはいけない:")
    print("    個々のセルの確率の絶対値。mu を -80 から +20 に振るだけで物理工は 3 倍近く動く。")
    print("    旧 README の『53.0%』のような 0.1% 刻みの表示は、精度の偽装だった。")


if __name__ == "__main__":
    main()
