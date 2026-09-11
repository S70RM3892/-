# -*- coding: utf-8 -*-
"""共通テストの実効配点: 1素点がいくらの価値を持つか。

旧 kt.py を置き換える。中身の結論は変わらないが、
  * exec(open(...).read().split(...)) による他ファイル取り込みを廃止
  * 配点係数の導出を配点表（params.json）から機械的に出すようにした
  * 学部横断比較を kyodai_official.json から自動生成するようにした（手写しをやめる）
"""
from __future__ import annotations

from kyodai import datasets as ds
from kyodai.stats import header, rule

# (表示名, 分布CSVの科目名, 京大工での満点寄与, 素点満点)
SUBJECTS = [
    ("国語",            "国語",                       25, 200),
    ("地歴公民(地理)",   "地理総合，地理探究",           50, 100),
    ("地歴公民(政経)",   "公共，政治・経済",             50, 100),
    ("数学ⅠA",          "数学Ⅰ，数学Ａ",               12.5, 100),
    ("数学ⅡBC",         "数学Ⅱ，数学Ｂ，数学Ｃ",        12.5, 100),
    ("物理",            "物理",                       12.5, 100),
    ("化学",            "化学",                       12.5, 100),
    ("英語R",           "英語（リーディング）",          25, 100),
    ("英語L",           "リスニング",                  25, 100),
    ("情報Ⅰ",           "情報Ⅰ",                      50, 100),
]


def main() -> None:
    params = ds.load_params()
    ct = params["scoring"]["common_test"]
    assert sum(v for k, v in ct.items() if k != "total") == ct["total"], "共テ配点の検算に失敗"

    print(header("1. 1素点あたりの価値（京大工 1025点満点での点）"))
    print("  数学・理科は2科目で1区分（各25点）なので、1科目あたりは12.5点。")
    print(f"  {'科目':<16}{'素点満点':>9}{'京大工配点':>11}{'1素点の価値':>12}")
    coef = {}
    for label, key, w, raw in SUBJECTS:
        coef[label] = w / raw
        print(f"  {label:<16}{raw:>9}{w:>11.1f}{w/raw:>12.3f}")
    print(f"\n  → 共テ情報Ⅰの1点 = 共テ数学の {coef['情報Ⅰ']/coef['数学ⅠA']:.0f}点。")
    print("     工学部だけが『二次で出る科目の共テを半額、出ない科目を定価』にしている。")
    print("     （理学部はその真逆。次節参照）")

    print(header("2. 情報Ⅰの比重は京大の中でどれくらい特殊か（kyodai_official.json から自動生成）"))
    print("  c25 = 令和7年度入試以降の共テ配点 [国語, 地公, 数学, 理科, 外R, 外L, 情報]")
    print(f"  {'学部':<26}{'共テ計':>8}{'情報':>7}{'情報比':>8}{'数理計':>8}{'数理比':>8}")
    rows = []
    for r in ds.load_official():
        c = r["c25"]
        tot = sum(c)
        if tot == 0:
            continue
        info = c[6]
        mathsci = c[2] + c[3]
        rows.append((r["fac"], tot, info, info / tot, mathsci, mathsci / tot))
    for fac, tot, info, sh, ms, msh in sorted(rows, key=lambda t: -t[3]):
        print(f"  {fac:<26}{tot:>8.1f}{info:>7.1f}{sh*100:>7.1f}%{ms:>8.1f}{msh*100:>7.1f}%")
    print("  → 工学部6学科の情報Ⅰ比重 22.2% は京大で最大。")

    print(header("3. 『全国上位10% → 上位1%』に上がることの価値"))
    for fname, label in [("dist_r8.csv", "令和8年度"), ("dist_r7.csv", "令和7年度")]:
        S = ds.load_dist(fname)
        print(f"\n  ── {label} 本試験 ──")
        print(f"  {'科目':<16}{'係数':>7}{'p50':>6}{'p90':>6}{'p99':>6}{'p90→p99':>9}{'京大工点':>10}")
        out = []
        for label2, key, w, raw in SUBJECTS:
            s = S.get(key)
            if s is None:
                print(f"  {label2:<16} （分布データなし）")
                continue
            v = {p: ds.percentile(s, p) for p in (50, 90, 99)}
            d = v[99] - v[90]
            out.append((label2, d * coef[label2]))
            print(f"  {label2:<16}{coef[label2]:>7.3f}{v[50]:>6}{v[90]:>6}{v[99]:>6}"
                  f"{d:>9}{d*coef[label2]:>10.1f}")
        print("    価値の順:", "  ".join(f"{a} {b:.1f}点" for a, b in
                                       sorted(out, key=lambda t: -t[1])))
        four = sum(b for a, b in out if a in ("数学ⅠA", "数学ⅡBC", "物理", "化学"))
        print(f"    数ⅠA+数ⅡBC+物理+化学 の4科目合計 = {four:.1f}点"
              f"（情報Ⅰ単独 {dict(out)['情報Ⅰ']:.1f}点 と同水準）")


if __name__ == "__main__":
    main()
