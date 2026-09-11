# -*- coding: utf-8 -*-
"""二次試験800点の定量分析。旧版に存在しなかった部分。

旧版は共通テスト225点（全体の22%）に設問単位の項目反応模型まで作り込み、
二次800点（全体の78%）には定量模型をひとつも持っていなかった。
artifacts/kyodai-map.html は出題分野の地図であって、
「どこで何点落としているか」の推定ではない。

ここで出すもの:
  1. 合格最低点から逆算した、必要な二次得点（共テ得点率の関数）
  2. 大問1つの価値（1025点満点での点、および合格最低点ノイズの何σか）
  3. 共テの取りこぼし全部と、二次の1大問との交換レート
  4. 得点開示データ（n 小）から見た二次の実際の得点分布。限界を明示して扱う。
"""
from __future__ import annotations

import json
import math
import os
import statistics as st

from kyodai import datasets as ds
from kyodai.stats import header

FOCUS = "情報"

# 二次の大問構成。配点は問題用紙に印刷される（募集要項ではなく本番の問題冊子）。
# 数学は6問で計200素点、印刷配点は 30/35/40 のいずれか。
# 理科は物理・化学 各100素点で各3大問程度。
STRUCTURE = [
    # (科目, 素点満点, 換算係数, 大問数, 大問1つの代表素点)
    ("数学",   200, 1.25,          6, 200 / 6),
    ("理科",   200, 1.25,          6, 200 / 6),
    ("英語",   150, 200 / 150,     4, 150 / 4),
    ("国語",   100, 1.0,           3, 100 / 3),
]


def main() -> None:
    params = ds.load_params()
    recs, years = ds.load_panel()
    idx = ds.panel_index(recs)
    ie = params["scoring"]["individual_exam"]
    ct = params["scoring"]["common_test"]
    total = params["scoring"]["total"]

    assert ie["total"] == 800 and ct["total"] == 225 and total == 1025
    assert abs(sum(ie[k]["weighted"] for k in ("国語", "数学", "理科", "英語")) - 800) < 1e-9

    print(header("0. 配点の検算"))
    print(f"  共テ {ct['total']} + 二次 {ie['total']} = {total}  ✓")
    print(f"  二次素点 {ie['raw_total']} → 800:", "  ".join(
        f"{k} {ie[k]['raw']}×{ie[k]['factor']:.4g}={ie[k]['weighted']:g}"
        for k in ("国語", "数学", "理科", "英語")))
    print(f"  二次は全体の {ie['total']/total*100:.1f}%。共テは {ct['total']/total*100:.1f}%。")

    print(header("1. 1素点あたりの価値: 共テ vs 二次"))
    print(f"  {'区分':<20}{'素点満点':>9}{'1025換算':>10}{'1素点の価値':>12}")
    rows = []
    for name, raw, f, _, _ in STRUCTURE:
        rows.append((f"二次 {name}", raw, raw * f, f))
    rows += [("共テ 情報Ⅰ", 100, 50, 0.5), ("共テ 地歴公民", 100, 50, 0.5),
             ("共テ 英語(R+L)", 200, 50, 0.25), ("共テ 国語", 200, 25, 0.125),
             ("共テ 数学(2科目)", 200, 25, 0.125), ("共テ 理科(2科目)", 200, 25, 0.125)]
    for name, raw, w, f in sorted(rows, key=lambda t: -t[3]):
        print(f"  {name:<20}{raw:>9.0f}{w:>10.1f}{f:>12.4f}")
    print("  → 共テ情報Ⅰの1素点(0.50)は二次数学の1素点(1.25)の 40%。")
    print("     旧 README の『情報Ⅰの1点＝共テ数学の4点』は共テ内部の比較であって、")
    print("     共テと二次の間の交換レートではない。後者こそが勉強時間の配分を決める。")

    print(header("2. 大問1つの価値"))
    hand = os.path.join(ds.OUTPUTS, "panel_handoff.json")
    if not os.path.exists(hand):
        raise SystemExit("先に p01_panel.py を実行すること")
    noise = json.load(open(hand, encoding="utf-8"))["cutoff_noise_points"]
    sigma = noise[FOCUS]["with_step"]
    sigma_lo = noise[FOCUS]["no_step"]
    print(f"  情報学科の合格最低点の年変動 σ = {sigma_lo:.1f}–{sigma:.1f}点（p01）")
    print(f"  {'科目':<8}{'大問数':>7}{'代表素点':>10}{'1025換算':>10}{'σの何倍':>12}")
    for name, raw, f, nq, per in STRUCTURE:
        w = per * f
        print(f"  {name:<8}{nq:>7}{per:>10.1f}{w:>10.1f}"
              f"{f'{w/sigma:.1f}–{w/sigma_lo:.1f}σ':>12}")
    print("  ※ 数学の印刷配点は 30/35/40 点。代表値ではなく実際の配点で見ると:")
    for pts in (30, 35, 40):
        print(f"     数学 {pts}点満点の大問 = {pts*1.25:.1f}点/1025 = "
              f"{pts*1.25/sigma:.1f}–{pts*1.25/sigma_lo:.1f}σ")

    print(header("3. 共テの取りこぼし全部 vs 二次の大問1つ"))
    cth = os.path.join(ds.OUTPUTS, "ct_handoff.json")
    if os.path.exists(cth):
        c = json.load(open(cth, encoding="utf-8"))
        lo, hi = c["total_recoverable_low"], c["total_recoverable_high"]
    else:
        lo, hi = 16.6, 30.0
        print("  （p05 未実行のため既定値を使用）")
    print(f"  共テ8科目の取りこぼし合計   : {lo:.1f}–{hi:.1f}点/1025")
    print(f"  二次数学の大問1つ(35点)     : {35*1.25:.1f}点/1025")
    print(f"  二次理科の大問1つ(33点)     : {200/6*1.25:.1f}点/1025")
    print(f"  → 二次数学を1問多く完答することは、共テ全科目の取りこぼしを")
    print(f"     {35*1.25/hi:.1f}–{35*1.25/lo:.1f} 回ぶん回収するのに等しい。")
    print("  この比較が旧 README に無かったことが、意思決定文書としての最大の欠陥だった。")

    print(header("4. 合格最低点から逆算する『必要な二次得点』"))
    print("  必要二次点 = 合格最低点 − 共テ換算点。共テ得点率を振って見る。")
    cuts = ds.official_cutoffs("工学部(情報学科)", years)
    recent = [cuts[y] for y in years if y >= ds.REGIME_BREAK_YEAR]
    print("  情報学科の合格最低点（新配点2年, 1025点満点）: "
          + "  ".join(f"{y}年 {cuts[y]:.1f}" for y in years if y >= ds.REGIME_BREAK_YEAR))
    print("  （旧配点の6年は1000点満点なので、水準の比較には使えない）")
    cut = st.mean(recent)
    print(f"  平均 {cut:.1f}/1025（得点率 {cut/1025*100:.1f}%）を基準にする。")
    print(f"\n  {'共テ得点率':>10}{'共テ点':>9}{'必要二次点':>11}{'必要二次得点率':>15}{'必要素点(650)':>14}")
    for rate in (0.80, 0.83, 0.85, 0.88, 0.90, 0.93):
        ctp = 225 * rate
        need = cut - ctp
        print(f"  {rate*100:>9.0f}%{ctp:>9.1f}{need:>11.1f}{need/800*100:>14.1f}%"
              f"{need/800*650:>14.1f}")
    print("  → 共テ得点率を 85% から 90% に上げても、必要な二次得点率は")
    d85 = (cut - 225 * 0.85) / 800 * 100
    d90 = (cut - 225 * 0.90) / 800 * 100
    print(f"     {d85:.1f}% → {d90:.1f}% と {d85-d90:.1f} ポイントしか下がらない。")
    print(f"     共テ5ポイント = 二次 {(225*0.05):.1f}点 = 二次素点 {(225*0.05)/800*650:.1f}点分。")
    print(f"     二次数学の大問1つ（35素点）の方が大きい。")

    print(header("5. 二次の得点分布（得点開示, n が小さい。参考値）"))
    eng = []
    seen = set()
    for fname, fac_key in (("kaiji2.json", "fac"), ("kaiji_rows.json", "faculty")):
        for r in json.load(open(os.path.join(ds.DATA, fname), encoding="utf-8")):
            if r.get(fac_key) != "工学部":
                continue
            sig = (r.get("year"), r.get("国語"), r.get("数学"), r.get("理科"), r.get("英語"))
            if sig in seen:
                continue
            seen.add(sig)
            eng.append(r)
    clean, dirty = [], []
    for r in eng:
        vals = [r.get(k) for k in ("国語", "数学", "理科", "英語")]
        if any(v is None for v in vals):
            dirty.append(r)
        elif (vals[0] > 100 or vals[1] > 200 or vals[2] > 200 or vals[3] > 150
              or max(vals) <= 10):
            # 満点超え、または全科目が一桁（5段階評価の混入）
            dirty.append(r)
        else:
            clean.append(r)
    print(f"  data/kaiji2.json と data/kaiji_rows.json を統合・重複除去した結果、")
    print(f"  工学部は {len(eng)} 件。うち検証を通ったのは {len(clean)} 件（除外 {len(dirty)} 件）。")
    print("  ※ 旧 README は『工学部分が11件』と書いていたが、11 は kaiji2.json の全学部合計で、")
    print("     工学部はそのうち4件だった。件数の記述そのものが誤っていた。")
    for r in dirty:
        print(f"    除外: {r}")
    if clean:
        print(f"\n  {'科目':<6}{'n':>4}{'平均':>8}{'最小':>8}{'最大':>8}{'満点':>6}{'得点率':>8}")
        for k, mx in (("国語", 100), ("数学", 200), ("理科", 200), ("英語", 150)):
            v = [r[k] for r in clean]
            print(f"  {k:<6}{len(v):>4}{st.mean(v):>8.1f}{min(v):>8.1f}{max(v):>8.1f}"
                  f"{mx:>6}{st.mean(v)/mx*100:>7.1f}%")
        tot = [r["国語"] + r["数学"] * 1.25 + r["理科"] * 1.25 + r["英語"] * (200 / 150)
               for r in clean]
        print(f"  {'二次計':<6}{len(tot):>4}{st.mean(tot):>8.1f}{min(tot):>8.1f}"
              f"{max(tot):>8.1f}{800:>6}{st.mean(tot)/800*100:>7.1f}%")
    print(f"\n  ※ n={len(clean)} は科目間相関の推定にも、分布の推定にも足りない。")
    print("     合否も自己申告で、母集団は『開示を投稿した人』という強い選択が入っている。")
    print("     この表は『二次の得点水準の桁感』以上の用途に使ってはいけない。")

    print(header("6. 結論"))
    print("  (A) 二次は全体の78%。共テ全科目の取りこぼしを完全に回収しても、")
    print(f"      二次数学の大問 {35*1.25/hi:.1f}–{35*1.25/lo:.1f} 問ぶんにしかならない。")
    print("  (B) 1素点あたりの価値は 二次数学・理科(1.25) > 二次英語(1.33) > 共テ情報Ⅰ(0.50)。")
    print("      共テ内部の相対価値（情報Ⅰ = 数学の4倍）と混同してはいけない。")
    print("  (C) ただし『価値が高い = 優先すべき』ではない。回収に要する時間を")
    print("      入れないと順位は決まらない。それを p07_budget.py でやる。")


if __name__ == "__main__":
    main()
