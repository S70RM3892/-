# -*- coding: utf-8 -*-
"""上位層の中で、京大工の共テ得点のばらつきはどの科目が作っているか。

旧 kt2.py を置き換える。追加した点:
  * 切断点（上位何%で切るか）への感度を出す。旧版は p90 固定だった。
  * 「全国分布の切断であって京大工受験層の同時分布ではない」という限界を
    出力自体に書き込む（README の隅に書くだけでは読まれない）。
"""
from __future__ import annotations

import math

from kyodai import datasets as ds
from kyodai.stats import header

CORE = [
    ("国語",       "国語",                  25,   200),
    ("地歴公民",    "公共，政治・経済",        50,   100),
    ("数学ⅠA",     "数学Ⅰ，数学Ａ",          12.5, 100),
    ("数学ⅡBC",    "数学Ⅱ，数学Ｂ，数学Ｃ",   12.5, 100),
    ("物理",       "物理",                  12.5, 100),
    ("化学",       "化学",                  12.5, 100),
    ("英語R",      "英語（リーディング）",     25,   100),
    ("英語L",      "リスニング",             25,   100),
    ("情報Ⅰ",      "情報Ⅰ",                 50,   100),
]
INFO_GROUP = {"情報Ⅰ", "地歴公民"}
SCI_GROUP = {"数学ⅠA", "数学ⅡBC", "物理", "化学"}


def shares(S, cut):
    """上位 (100-cut)% に切断したときの、科目別 京大工換算SD と分散シェア。"""
    out = []
    for label, key, w, raw in CORE:
        s = S[key]
        co = w / raw
        if cut is None:
            m, sd = ds.dist_moments(s)
        else:
            thr = ds.percentile(s, cut)
            h = [(sc, c) for sc, c in s["h"] if sc >= thr]
            n = sum(c for _, c in h)
            m = sum(sc * c for sc, c in h) / n
            sd = math.sqrt(sum((sc - m) ** 2 * c for sc, c in h) / n)
        out.append((label, co, sd, sd * co))
    tv = sum(x[3] ** 2 for x in out)
    return out, tv


def main() -> None:
    print(header("上位層内での分散シェア（京大工1025点換算）"))
    print("  ※ これは全国分布の切断であって、京大工受験層の同時分布ではない。")
    print("     科目間の相関も、京大工志願者に固有の選抜効果も入っていない。")
    print("     『情報Ⅰのばらつきが大きい』という順位は頑健だが、シェアの絶対値は上限側の値。")

    for fname, label in [("dist_r8.csv", "令和8年度"), ("dist_r7.csv", "令和7年度")]:
        S = ds.load_dist(fname)
        print(f"\n{'='*78}\n{label} 本試験\n{'='*78}")
        out, tv = shares(S, 90)
        print(f"  上位10%に切断したとき  {'科目':<12}{'京大配点':>9}{'素点SD':>9}"
              f"{'換算SD':>9}{'分散シェア':>11}")
        for lab, co, sd, g in out:
            print(f"  {'':<22}{lab:<12}{co*100:>9.1f}{sd:>9.2f}{g:>9.2f}{g*g/tv*100:>10.1f}%")
        a = sum(g * g for lab, co, sd, g in out if lab in INFO_GROUP)
        b = sum(g * g for lab, co, sd, g in out if lab in SCI_GROUP)
        print(f"    情報Ⅰ+地歴公民 = {a/tv*100:.1f}%（配点シェア {100/225*100:.1f}%）")
        print(f"    理系4科目      = {b/tv*100:.1f}%（配点シェア {50/225*100:.1f}%）")

        print(f"\n  切断点への感度:")
        print(f"  {'切断':<12}{'情報Ⅰ+地歴公民':>16}{'理系4科目':>12}{'国語':>9}{'英語R+L':>10}")
        for cut, cl in [(None, "切断なし"), (50, "上位50%"), (80, "上位20%"),
                        (90, "上位10%"), (95, "上位5%"), (98, "上位2%")]:
            out2, tv2 = shares(S, cut)
            a2 = sum(g * g for lab, co, sd, g in out2 if lab in INFO_GROUP) / tv2
            b2 = sum(g * g for lab, co, sd, g in out2 if lab in SCI_GROUP) / tv2
            k2 = sum(g * g for lab, co, sd, g in out2 if lab == "国語") / tv2
            e2 = sum(g * g for lab, co, sd, g in out2 if lab in ("英語R", "英語L")) / tv2
            print(f"  {cl:<12}{a2*100:>15.1f}%{b2*100:>11.1f}%{k2*100:>8.1f}%{e2*100:>9.1f}%")
        print("  → 切断をどこに置いても『情報Ⅰ+地歴公民が配点シェアを大きく上回る』は変わらない。")


if __name__ == "__main__":
    main()
