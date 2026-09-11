# -*- coding: utf-8 -*-
"""共テと二次を同じ土俵に載せ、『点/時間』で並べ替える。

旧版に無かった2つ目の柱。旧版は一貫して「点がどこに残っているか」を測り、
「どこの点が安いか」を一度も測っていなかった。情報Ⅰの 10点 と 物理の 2.9点 を
並べても、回収に要する時間が 10 倍違えば結論は逆になる。

ここの時間見積もりは全て params.json の study_cost（status=USER）である。
公開情報からは決まらない。自分の学習ログで置き換えること。
出力の主眼は「順位」ではなく「順位がひっくり返る損益分岐点」にある。
"""
from __future__ import annotations

import json
import math
import os

from kyodai import datasets as ds
from kyodai.stats import header

# 二次で「あと1つ取れるようにする」単位と、その1025換算価値
NIJI_UNITS = [
    ("二次数学", "大問1つ(35素点)", 35 * 1.25),
    ("二次理科", "大問1つ(33素点)", (200 / 6) * 1.25),
    ("二次英語", "大問1つ(37.5素点)", 37.5 * (200 / 150)),
    ("二次国語", "大問1つ(33素点)", (100 / 3) * 1.0),
]
CT_LABEL = {
    "情報Ⅰ": "共テ情報Ⅰ", "地歴公民": "共テ地歴公民(政経)", "英語L": "共テ英語リスニング",
    "物理": "共テ物理", "数学ⅠA": "共テ数学ⅠA", "数学ⅡBC": "共テ数学ⅡBC",
    "化学": "共テ化学", "英語R": "共テ英語リーディング",
}


def main() -> None:
    params = ds.load_params()
    hours = params["study_cost"]["hours"]

    cth = os.path.join(ds.OUTPUTS, "ct_handoff.json")
    if not os.path.exists(cth):
        raise SystemExit("先に p05_irt_ct.py を実行すること")
    ct = json.load(open(cth, encoding="utf-8"))
    per = ct["per_subject"]

    print(header("0. この節が入れている仮定"))
    print(f"  時間見積もりは params.json の study_cost（status="
          f"{params['study_cost']['status']}）。公開情報からは決まらない。")
    print("  『その科目を今の水準から現実的な上限まで詰めるのに要する総時間』の粗い目安で、")
    print("  限界生産性が一定であることも暗に仮定している（本当は逓減する）。")
    print("  従って以下の順位は、自分の時間見積もりを入れ替えれば変わる。")
    print("  重要なのは順位そのものではなく、§3 の損益分岐点である。")

    print(header("1. 回収可能点あたりの時間（共テ）"))
    print("  回収可能点は p05 の帯（下限=公表分位点, 上限=rho入り模型）を使う。")
    print(f"  {'項目':<22}{'回収可能点':>12}{'想定時間':>9}{'点/100時間':>13}")
    rows = []
    for key, label in CT_LABEL.items():
        lo, hi = per[key]
        h = hours.get(label)
        if h is None:
            continue
        mid = (lo + hi) / 2
        rows.append((label, lo, hi, h, mid / h * 100))
    for label, lo, hi, h, rate in sorted(rows, key=lambda t: -t[4]):
        print(f"  {label:<22}{f'{lo:.1f}–{hi:.1f}':>12}{h:>9}{rate:>13.2f}")

    print(header("2. 回収可能点あたりの時間（二次）"))
    print("  二次は『満点との差』ではなく『あと1つ取れるようになる』単位で測る。")
    print("  取りこぼしを満点基準で測ると二次は 300点以上になり、意味のある数字にならない。")
    print(f"  {'項目':<22}{'1単位の価値':>12}{'想定時間':>9}{'単位数':>8}{'点/100時間':>13}")
    niji_rows = []
    for label, unit, val in NIJI_UNITS:
        h = hours[label]
        # 想定時間は「その科目を一通り引き上げる」総時間。1単位あたりに割り戻す。
        # 数学400時間で大問1つ分（=6分の1の得点力）が動くと置くのは楽観的すぎるので、
        # 総時間で 2 単位ぶん動くという保守的な換算にする。
        units = 2.0
        rate = val * units / h * 100
        niji_rows.append((label, unit, val, h, units, rate))
    for label, unit, val, h, units, rate in sorted(niji_rows, key=lambda t: -t[5]):
        print(f"  {label:<22}{val:>12.1f}{h:>9}{units:>8.1f}{rate:>13.2f}")
    print("  ※『総時間で2単位ぶん動く』は仮定。1単位なら上の値は半分、4単位なら倍になる。")

    print(header("3. 損益分岐点（ここが本題）"))
    print("  『共テ情報Ⅰに X 時間かけるくらいなら二次数学に回した方がよい』の X を求める。")
    lo_i, hi_i = per["情報Ⅰ"]
    mid_i = (lo_i + hi_i) / 2
    h_math = hours["二次数学"]
    for units in (1.0, 2.0, 4.0):
        math_rate = 35 * 1.25 * units / h_math      # 点/時間
        breakeven = mid_i / math_rate
        print(f"  二次数学が総{h_math}時間で大問{units:.0f}単位動くと置くと、"
              f"二次数学は {math_rate*100:.2f}点/100時間。")
        print(f"    → 共テ情報Ⅰ（回収可能 {mid_i:.1f}点）は {breakeven:.0f} 時間以内で")
        print(f"      仕上がるなら二次数学より割がよい。{breakeven:.0f} 時間を超えるなら逆転する。")
    h_info = hours["共テ情報Ⅰ"]
    be2 = mid_i / (35 * 1.25 * 2.0 / h_math)
    verdict = "情報Ⅰが勝つ" if h_info <= be2 else "二次数学が勝つ"
    print(f"\n  params.json の既定は 共テ情報Ⅰ={h_info}時間、2単位仮定での分岐点は {be2:.0f}時間。")
    print(f"  → 既定の見積もりのもとでは {verdict}（{h_info} 時間 "
          f"{'<=' if h_info <= be2 else '>'} {be2:.0f} 時間）。")
    print("  だがこれは『情報Ⅰが60時間で仕上がる』『二次数学が400時間で2単位動く』という")
    print("  2つの仮定の比較であって、データが言っていることではない。")
    print("  ここを自分の学習ログで置き換えるまで、この研究は勉強計画としては未完成である。")

    print(header("4. 全項目の統合ランキング（既定の時間見積もりのもとで）"))
    print(f"  {'項目':<22}{'点':>10}{'時間':>8}{'点/100時間':>13}{'種別':>8}")
    allrows = [(l, (lo + hi) / 2, h, r, "共テ") for l, lo, hi, h, r in rows]
    allrows += [(l, v * u, h, r, "二次") for l, _, v, h, u, r in niji_rows]
    for label, pts, h, rate, kind in sorted(allrows, key=lambda t: -t[3]):
        print(f"  {label:<22}{pts:>10.1f}{h:>8}{rate:>13.2f}{kind:>8}")
    ct_tot = sum(r[1] for r in allrows if r[4] == "共テ")
    ct_h = sum(r[2] for r in allrows if r[4] == "共テ")
    alt = 35 * 1.25 * 2.0 / h_math * ct_h
    print(f"\n  共テ側を全部やり切ると {ct_tot:.1f}点 / {ct_h}時間。")
    print(f"  同じ {ct_h} 時間を二次数学に回すと {alt:.1f}点（2単位仮定）。")
    winner = "共テ側" if ct_tot >= alt else "二次数学"
    print(f"  → 既定の仮定では {winner} が勝つ（{ct_tot:.1f}点 vs {alt:.1f}点）。")
    be_units = ct_tot * h_math / (35 * 1.25 * ct_h)
    print("     ただし二次側の『総時間で2単位動く』が最も根拠の薄い仮定である。")
    print(f"     逆転するのは {be_units:.2f} 単位を下回ったとき、")
    print(f"     つまり二次数学に {h_math} 時間かけて大問 {be_units:.2f} 問ぶんしか")
    print("     伸びない場合に限られる。それが現実的かどうかは自分にしか分からない。")
    print("     どちらが勝つかは、このリポジトリのデータでは決まらない。")

    print(header("5. 正直な結論"))
    print("  この節の数字は、公開情報 0%・個人の仮定 100% でできている。")
    print("  それでも置く価値があるのは、旧版が『点がどこにあるか』だけを示して")
    print("  『だから情報Ⅰをやれ』と読ませる構造になっていたからである。")
    print("  費用の列を空欄のまま置いておくと、読み手は暗黙に費用を一定と仮定してしまう。")
    print("  空欄を可視化することがこの節の目的であって、順位を確定させることではない。")


if __name__ == "__main__":
    main()
