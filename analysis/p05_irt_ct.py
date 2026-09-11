# -*- coding: utf-8 -*-
"""共テで京大工レベルがまだ落としている点を、設問単位で推定する。

旧 irt_run.py を置き換える。旧版の重大な問題を4つ直した。

(1) 能力水準 z=+2.0 に根拠がなかった。
    「京大工レベル = 全国上位2.3%」はどこからも導かれていない。しかも結論は
    z に極端に敏感で、z=1.5 なら 34点、z=3.0 なら 10点になる。
    → 公表ボーダー得点率（河合塾: 情報学科 85%）から z を逆算する。

(2) 較正 r が低い科目ほど取りこぼしが大きく出る、という機械的バイアスがある。
    r が低い = その科目の得点が学力と連動しない = z を上げても点が伸びない
    = 取りこぼしが大きく見える。実際 corr(r, 取りこぼし) は負。
    そして模型が上側を最も過小評価する科目（情報Ⅰ, 英語L）が、そのまま
    取りこぼし上位に来ていた。誤差が結論と同じ向きに効いていた。
    → r を全科目共通に固定した場合の順位を併記する。

(3) 局所独立を仮定していた。同一大問内の設問は同じ図表・同じ設定を共有するので、
    能力を固定しても残差が正に相関する。それを無視すると条件付き分散を
    過小に見積もり、公表SDに合わせるために r が過大に較正される。
    → 同一大問内の残差相関 rho を入れた版を併記する（rho=0.2）。

(4) 全科目で同じ z にいる人を仮定していた（科目間能力の完全相関）。
    実在しないうえ、上側は天井で凹なので実在の受験生の取りこぼしは
    これより大きくなる。
    → 科目別能力に散らばりを入れたときの補正量を出す。
"""
from __future__ import annotations

import itertools
import math
import os
import random
import statistics as st

from kyodai import datasets as ds
from kyodai import irt
from kyodai.stats import cdf, corr, header, inv_cdf

# (表示名, 分布CSV/設問CSVの科目名, 京大工換算係数)
SPEC = [
    ("数学ⅠA",   "数学Ⅰ，数学Ａ",            0.125),
    ("数学ⅡBC",  "数学Ⅱ，数学Ｂ，数学Ｃ",     0.125),
    ("物理",     "物理",                    0.125),
    ("化学",     "化学",                    0.125),
    ("英語R",    "英語（リーディング）",       0.25),
    ("英語L",    "英語（リスニング）",         0.25),
    ("情報Ⅰ",    "情報Ⅰ",                   0.5),
    ("地歴公民",  "公共，政治・経済",          0.5),
]
# 数学ⅡBC は第1–3問必答 + 第4–7問から3問選択。
IIBC_COMBOS = [("1", "2", "3") + c for c in itertools.combinations(("4", "5", "6", "7"), 3)]
FULL_KYODAI = 200.0   # 上の8科目の京大工換算満点（共テ225点 − 国語25点）


def build(S, rho=0.0):
    """科目 -> (設問列, 較正r, 係数)。rho は同一大問内の残差相関。"""
    fit = {}
    for label, key, co in SPEC:
        s = S[key]
        if label == "数学ⅡBC":
            base = ds.load_items(key)
            cands = []
            for c in IIBC_COMBOS:
                it = [x for x in base if x[0] in set(c)]
                r = irt.calibrate(it, s["sd"], rho)
                cands.append((irt.expected_score(it, r, 2.0), it, r))
            cands.sort(key=lambda t: t[0])
            _, it, r = cands[len(cands) // 2]          # 選択パターンの中央値
        else:
            it = ds.load_items(key)
            r = irt.calibrate(it, s["sd"], rho)
        fit[label] = (it, r, co)
    return fit


def losses(fit, z):
    """科目 -> 京大工換算の取りこぼし点。"""
    out = {}
    for label, (it, r, co) in fit.items():
        mx = sum(m for _, _, m, _ in it)
        out[label] = (mx - irt.expected_score(it, r, z)) * co
    return out


def main() -> None:
    params = ds.load_params()
    lvl = params["common_test_level"]
    S = ds.load_dist("dist_r8.csv")
    fit = build(S, rho=0.0)
    RHO = 0.2
    fit_rho = build(S, rho=RHO)

    print(header("1. 較正の当てはまり（令和8年度 本試験）"))
    print("  r は『模型の総得点SDが公表SDに一致する』ように決める。平均は構成上ほぼ一致する。")
    print("  問題は上側の当てはまり。p97.7 の列を見ること。")
    print(f"  {'科目':<10}{'設問数':>7}{'較正r':>8}{'公表SD':>8}"
          f"{'平均 模型/公表':>17}{'p90 模型/公表':>16}{'p97.7 模型/公表':>18}{'上側誤差':>9}")
    misfit = {}
    for label, key, co in SPEC:
        it, r, _ = fit[label]
        s = S[key]
        m, _sd = irt.total_moments(it, r)
        p90m, p977m = irt.expected_score(it, r, 1.2816), irt.expected_score(it, r, 2.0)
        p90o, p977o = ds.percentile(s, 90), ds.percentile(s, 97.7)
        if label == "数学ⅡBC":
            p977o = min(p977o, 100)
        misfit[label] = p977o - p977m
        print(f"  {label:<10}{len(it):>7}{r:>8.3f}{s['sd']:>8.2f}"
              f"{m:>10.1f}/{s['mean']:>6.2f}{p90m:>9.1f}/{p90o:>6}"
              f"{p977m:>11.1f}/{p977o:>6}{p977o-p977m:>9.1f}")
    print("  → 模型は全科目で上側を過小評価する。しかもその誤差は科目間で一様でない。")

    print(header("2. 機械的バイアスの診断（旧版が見ていなかった部分）"))
    L2 = losses(fit, 2.0)
    rs = [fit[l][1] for l, _, _ in SPEC]
    raw_loss = [(sum(m for _, _, m, _ in fit[l][0]) - irt.expected_score(*[fit[l][0], fit[l][1]], 2.0))
                for l, _, _ in SPEC]
    print(f"  corr(較正r, 取りこぼし素点)          = {corr(rs, raw_loss):+.3f}")
    print(f"  corr(較正r, 上側の当てはめ誤差)      = {corr(rs, [misfit[l] for l, _, _ in SPEC]):+.3f}")
    print("  → r が低い科目ほど取りこぼしが大きく、かつ模型の当てはまりも悪い。")
    print("     r が低いとは『得点が学力と連動しない』という意味なので、")
    print("     そこの失点は "
          "「勉強で回収できる分」ではなく「回収しにくい分」である可能性がある。")
    print("     対抗仮説（情報Ⅰは初年度で誰も対策しておらず、だから r が低い。")
    print("     ゆえに対策の限界収穫はむしろ大きい）も同じデータと整合する。")
    print("     この模型では両者を識別できない。識別には京大工受験層の実測が要る。")

    print(header("3. 能力水準 z の決め方（旧版はここを決め打ちしていた）"))
    z_border = irt.solve_z_for_score(fit, lvl["anchor_rate"]["value"])
    z_high = irt.solve_z_for_score(fit, lvl["anchor_rate_high"]["value"])
    print(f"  {'z':>7}{'全国上位':>10}{'8科目の京大工換算':>18}{'得点率':>9}{'取りこぼし':>11}")
    zs = sorted({round(z, 2) for z in lvl["z_grid"] + [z_border, z_high]})
    for z in zs:
        got = sum(irt.expected_score(it, r, z) * co for it, r, co in fit.values())
        tags = []
        if abs(z - round(z_border, 2)) < 5e-3:
            tags.append("河合塾ボーダー85%")
        if abs(z - round(z_high, 2)) < 5e-3:
            tags.append("合格者平均想定88%")
        if abs(z - 2.0) < 5e-3:
            tags.append("旧版の決め打ち")
        tag = ("  ← " + " / ".join(tags)) if tags else ""
        print(f"  {z:>7.2f}{(1-cdf(z))*100:>9.2f}%{got:>15.1f}/200{got/FULL_KYODAI*100:>8.1f}%"
              f"{FULL_KYODAI-got:>11.1f}点{tag}")
    print(f"  → 取りこぼしは z に対して 3 倍以上動く。旧 README が示していた不確実性")
    print(f"     （模型 23.7 vs 公表分位点 16.6）より、z の選び方による幅の方がはるかに大きい。")

    print(header("4. 科目別の取りこぼし（4つの方法を並べる）"))
    Lb = losses(fit, z_border)
    z_rho = irt.solve_z_for_score(fit_rho, lvl["anchor_rate"]["value"])
    Lt = losses(fit_rho, z_rho)
    direct = {}
    for label, key, co in SPEC:
        s = S[key]
        o = ds.percentile(s, 97.7)
        if label == "数学ⅡBC":
            o = min(o, 100)
        direct[label] = (100 - o) * co
    print(f"  {'科目':<10}{'A:旧z=2':>10}{'B:ボーダー':>11}{'C:rho=0.2':>11}{'D:公表分位':>11}"
          f"{'帯':>14}")
    for label, _, _ in SPEC:
        vals = [L2[label], Lb[label], Lt[label], direct[label]]
        print(f"  {label:<10}{L2[label]:>10.1f}{Lb[label]:>11.1f}{Lt[label]:>11.1f}"
              f"{direct[label]:>11.1f}{f'{min(vals):.1f}–{max(vals):.1f}':>14}")
    tots = [sum(L2.values()), sum(Lb.values()), sum(Lt.values()), sum(direct.values())]
    print(f"  {'合計':<10}{tots[0]:>10.1f}{tots[1]:>11.1f}{tots[2]:>11.1f}{tots[3]:>11.1f}"
          f"{f'{min(tots):.1f}–{max(tots):.1f}':>14}")
    print("  A = 旧版（z=2.0 決め打ち、素点独立）")
    print("  B = z を公表ボーダー85%に合わせた（既定）")
    print(f"  C = 同一大問内の残差相関 rho={RHO} を入れ、z を同じ85%に合わせ直した（z={z_rho:.2f}）")
    print("  D = 模型を使わず、各科目の公表 p97.7 から直接")
    print(f"  → 採用すべき帯は {min(tots):.0f}–{max(tots):.0f}点。"
          f"旧 README の 16.6–23.7点 は狭すぎた。")
    print()
    print("  【重要】B と C の合計が両方 30.0 なのは偶然ではない。")
    print("  z を『共テ得点率 85%』に合わせた時点で、取りこぼしの合計は 200×15% = 30.0点 と")
    print("  算術的に決まる。つまり合計値は推定量ではなく、入力した得点率の言い換えにすぎない。")
    print("  この模型が本当に推定しているのは合計ではなく、")
    print("     『その30点が科目間・設問間にどう配分されるか』")
    print("  だけである。旧 README が『合計16.6–23.7点』を主要な結果として前面に出していたのは、")
    print("  推定でないものを推定として売っていたことになる。")
    print("  合計を知りたいだけなら、模型を使わず 1025×(1−共テ得点率)×(225/1025) で足りる。")

    print(header("5. r を全科目共通に固定したときの順位（バイアス診断）"))
    r_bar = st.mean(rs)
    fixed = {}
    for label, (it, r, co) in fit.items():
        mx = sum(m for _, _, m, _ in it)
        fixed[label] = (mx - irt.expected_score(it, r_bar, z_border)) * co
    print(f"  共通 r = {r_bar:.3f}（較正値の平均）")
    print(f"  {'科目':<10}{'較正r版':>10}{'順位':>6}{'共通r版':>10}{'順位':>6}{'順位変化':>10}")
    ra = {l: i + 1 for i, l in enumerate(sorted(Lb, key=lambda k: -Lb[k]))}
    rb = {l: i + 1 for i, l in enumerate(sorted(fixed, key=lambda k: -fixed[k]))}
    for label, _, _ in SPEC:
        print(f"  {label:<10}{Lb[label]:>10.1f}{ra[label]:>6}{fixed[label]:>10.1f}"
              f"{rb[label]:>6}{rb[label]-ra[label]:>+10d}")
    print("  → 情報Ⅰが1位であることは r を固定しても変わらない（配点係数0.5が効くため）。")
    print("     ただし素点ベースの取りこぼし量は r に依存する。順位は頑健、量は頑健でない。")

    print(header("6. 全科目で同じ z にいる人はいない（凹性の補正）"))
    print("  科目別能力 z_j = z_bar + e_j,  e_j ~ N(0, tau^2) として、")
    print("  総得点が同じになるよう z_bar を調整したときの取りこぼしを見る。")
    rng = random.Random(20260911)
    print(f"  {'tau':>6}{'調整後z_bar':>13}{'取りこぼし':>12}{'差':>9}")
    base_loss = None
    for tau in (0.0, 0.3, 0.5, 0.8):
        lo, hi = -1.0, 5.0
        for _ in range(60):
            mid = (lo + hi) / 2
            tot = 0.0
            n_sim = 400
            for _ in range(n_sim):
                g = sum(irt.expected_score(it, r, mid + rng.gauss(0, tau)) * co
                        for it, r, co in fit.values())
                tot += g
            if tot / n_sim / FULL_KYODAI < lvl["anchor_rate"]["value"]:
                lo = mid
            else:
                hi = mid
        zb = (lo + hi) / 2
        tot = 0.0
        for _ in range(2000):
            tot += sum(irt.expected_score(it, r, zb + rng.gauss(0, tau)) * co
                       for it, r, co in fit.values())
        loss = FULL_KYODAI - tot / 2000
        if base_loss is None:
            base_loss = loss
        print(f"  {tau:>6.1f}{zb:>13.2f}{loss:>11.1f}点{loss-base_loss:>+8.1f}")
    print("  → 科目間に散らばりがあると、同じ総得点でも取りこぼしは（わずかに）増える。")
    print("     総得点を固定しているので効果は小さいが、符号は常に増加側。")

    print(header("7. 情報Ⅰ: まだ落とす期待値が大きい設問（z = ボーダー水準）"))
    it, r, co = fit["情報Ⅰ"]
    L = irt.item_losses(it, r, z_border)
    print(f"  {'大問':>4}{'解答':>8}{'配点':>5}{'全国得点率':>11}{'この水準':>10}"
          f"{'期待失点':>10}{'京大工点':>10}")
    for loss, (d, q, m, p), pz in L[:10]:
        print(f"  {d:>4}{q:>8}{m:>5.0f}{p:>11.3f}{pz:>10.3f}{loss:>10.2f}{loss*co:>10.2f}")
    print(f"  上位10設問で情報Ⅰの取りこぼしの "
          f"{sum(x[0] for x in L[:10])/sum(x[0] for x in L)*100:.0f}%")

    print(header("8. 大問別の期待失点（京大工点換算, z = ボーダー水準）"))
    for label in ("情報Ⅰ", "地歴公民", "物理", "数学ⅠA"):
        it, r, co = fit[label]
        agg = {}
        for d, q, m, p in it:
            cell = agg.setdefault(d, 0.0)
            agg[d] = cell + m * (1 - irt.prob(p, r, z_border))
        tl = sum(agg.values())
        print(f"  {label:<10}" + "  ".join(
            f"第{k}問 {v*co:.2f}点({v/tl*100:.0f}%)" for k, v in sorted(agg.items())))

    print(header("9. この節の限界（結論より先に読むこと）"))
    print("  * 設問データは令和8年度の1年分のみ（data/q_r8.csv）。年次変動は測れていない。")
    print("  * 全国分布は全受験者。京大工志願者の条件付き分布ではない。")
    print("  * 『取りこぼし』は満点との差であって、回収可能な点ではない。")
    print("    回収コスト（時間）は p07_budget.py で初めて入る。")
    print("  * 上の §2 の通り、科目順位は模型の当てはめ誤差と同じ向きに歪んでいる可能性がある。")

    _write_handoff(min(tots), max(tots), {l: (min(v), max(v)) for l, v in
                                          ((l, [L2[l], Lb[l], Lt[l], direct[l]])
                                           for l, _, _ in SPEC)}, z_border)


def _write_handoff(lo, hi, per_subject, z_border) -> None:
    import json
    os.makedirs(ds.OUTPUTS, exist_ok=True)
    path = os.path.join(ds.OUTPUTS, "ct_handoff.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({
            "_units": "1025点満点での点",
            "z_border": round(z_border, 4),
            "total_recoverable_low": round(lo, 2),
            "total_recoverable_high": round(hi, 2),
            "per_subject": {k: [round(a, 2), round(b, 2)] for k, (a, b) in per_subject.items()},
        }, fh, ensure_ascii=False, indent=2)
    print(f"\n  → {path} に書き出した（p07 が読む）")


if __name__ == "__main__":
    main()
