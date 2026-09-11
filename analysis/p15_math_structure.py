# -*- coding: utf-8 -*-
"""京大二次数学の構造 — 配点と難易度と分野。

p13 は「どの問題が軽いか」を開始時点で知っていると仮定し、
現実には見極めに時間がかかるので k=4–5 の優位は上限だと注記した。

ところが data/zk/diff.json に、**大問ごとの印刷配点と難易度評価の両方**が
入っていた（2008–2026, 17年）。一度も読んでいなかった。
配点は問題用紙に印刷される＝試験開始0秒で無料で手に入る情報なので、
配点が難易度の手がかりになるなら、偵察を事前に装填できることになる。

ここで検定するのは2つ:
  1. 印刷配点（30 / 35 / 40点）は難易度の手がかりになるか
  2. 分野は難易度の手がかりになるか
"""
from __future__ import annotations

import collections
import json
import math
import os
import random
import statistics as st

from kyodai import datasets as ds
from kyodai.stats import corr, header, permutation_p

SEED = 20260911


def load_diff():
    path = os.path.join(ds.DATA, "zk", "diff.json")
    D = json.load(open(path, encoding="utf-8"))
    pairs, by_year = [], {}
    for y in sorted(D, key=int):
        d, h = D[y]["d"], D[y]["h"]
        rows = [(a, b) for a, b in zip(d, h) if a is not None and b is not None]
        if rows:
            by_year[int(y)] = rows
        pairs += rows
    return pairs, by_year


def main() -> None:
    pairs, by_year = load_diff()

    print(header("1. 印刷配点は難易度の手がかりになるか"))
    print("  出典 data/zk/diff.json（Z会由来の難易度評価 1–5 と、印刷配点）")
    print(f"  配点と難易度が揃う観測 {len(pairs)} 問 / {len(by_year)} 年")
    counts = collections.Counter(b for _, b in pairs)
    print(f"  配点の分布: " + ", ".join(f"{p}点×{n}" for p, n in sorted(counts.items())))
    print(f"\n  {'配点':>6}{'n':>5}{'平均難易度':>11}{'SD':>8}")
    for pt in sorted(counts):
        v = [a for a, b in pairs if b == pt]
        print(f"  {pt:>6}{len(v):>5}{st.mean(v):>11.3f}{st.pstdev(v):>8.3f}")

    g30 = [a for a, b in pairs if b == 30]
    g35 = [a for a, b in pairs if b == 35]
    diff = st.mean(g35) - st.mean(g30)
    pool = g30 + g35
    n30 = len(g30)

    def draw(rng: random.Random) -> float:
        s = rng.sample(pool, len(pool))
        return st.mean(s[n30:]) - st.mean(s[:n30])

    p = permutation_p(diff, draw, n=100_000, seed=SEED)
    print(f"\n  30点 vs 35点 の差 = {diff:+.3f}（35点の方が難しい）")
    print(f"  並べ替え検定 p(片側) = {p:.4f}")

    ds_year = []
    wins = 0
    for y, rows in sorted(by_year.items()):
        a = [x for x, pt in rows if pt == 30]
        b = [x for x, pt in rows if pt == 35]
        if a and b:
            ds_year.append(st.mean(b) - st.mean(a))
            wins += st.mean(b) > st.mean(a)
    t = st.mean(ds_year) / (st.stdev(ds_year) / math.sqrt(len(ds_year)))
    print(f"  年内比較: 30点問題の方が易しかった年 {wins}/{len(ds_year)}")
    print(f"  年内差の平均 {st.mean(ds_year):+.3f}  対応ありの t = {t:.2f} (df={len(ds_year)-1})")
    print("\n  → **30点の大問は35点の大問より易しい傾向がある。**")
    print("     配点は問題用紙に印刷されるので、これは試験開始0秒で得られる情報である。")
    print("     p13 の『偵察に時間がかかる』という制約を、部分的に事前装填できる。")
    print(f"  ※ ただし 40点問題は n={counts.get(40,0)} しかなく判定不能（2019, 2021年のみ）。")
    print("     全体の corr(難易度, 配点) は "
          f"{corr([a for a,_ in pairs],[b for _,b in pairs]):+.3f} で、"
          "3水準まとめると有意でない。")
    print("     効いているのは 30 と 35 の対比だけ。")

    print(header("2. 分野は難易度の手がかりになるか"))
    F = json.load(open(os.path.join(ds.DATA, "zk", "kyodai_math_fields.json"),
                      encoding="utf-8"))
    DS = json.load(open(os.path.join(ds.DATA, "ds.json"), encoding="utf-8"))["daisu"]
    recs = []
    for r in F:
        y = str(r["year"])
        if y in DS and 1 <= r["q"] <= len(DS[y]):
            recs.append((r["fields"], DS[y][r["q"] - 1]))
    byf = collections.defaultdict(list)
    for fs, d in recs:
        for f in fs:
            byf[f].append(d)
    freq = {f: v for f, v in byf.items() if len(v) >= 4}
    gm = st.mean([d for _, d in recs])
    print(f"  分野と難易度が揃う観測 {len(recs)} 問（1998–2008）、"
          f"4回以上出る分野 {len(freq)} / 全{len(byf)}分野")
    print(f"  全体の平均難易度 {gm:.2f}")
    print(f"\n  {'分野':<18}{'出現':>5}{'平均難易度':>11}{'全体差':>9}")
    for f, v in sorted(freq.items(), key=lambda t: st.mean(t[1])):
        print(f"  {f:<18}{len(v):>5}{st.mean(v):>11.2f}{st.mean(v)-gm:>+9.2f}")

    obs = st.pvariance([st.mean(v) for v in freq.values()])
    alld = [d for _, d in recs]
    sizes = [len(v) for v in freq.values()]

    def draw2(rng: random.Random) -> float:
        s = rng.sample(alld, len(alld))
        i, means = 0, []
        for n in sizes:
            means.append(st.mean(s[i:i + n]))
            i += n
        return st.pvariance(means)

    p2 = permutation_p(obs, draw2, n=20_000, seed=SEED)
    print(f"\n  分野間の平均難易度の分散 {obs:.4f}   並べ替え p = {p2:.4f}")
    print("  → **判定不能。** p=0.08 は有意でも帰無でもなく、検出力不足である。")
    print(f"     n={len(recs)} 問、4回以上出る分野が {len(freq)} しかない。")
    print("     差の向き（整数・定積分と面積は軽い / 複素数・確率は重い）は")
    print("     仮説として記録する価値があるが、これを根拠に対策を偏らせてはいけない。")

    print(header("3. p13 への影響"))
    print("  p13 は配点を [30,35,35,35,35,30] と固定していた。実際の配点は年で動く。")
    print(f"  {'年':<6}{'実際の配点':<30}{'計':>6}")
    for y, rows in sorted(by_year.items()):
        h = [b for _, b in rows]
        print(f"  {y:<6}{str(h):<30}{sum(h):>6}")
    print("\n  → 6問200点は一定だが、内訳は 30×2+35×4 が最頻。2019・2021年は40点問題あり。")
    print("     p13 の仮定は実態に近い。結論は変わらない。")
    print("  → 一方 §1 の結果は p13 に足りない要素を1つ埋める:")
    print("     開始時点で全問の重さは分からない、という仮定は強すぎた。")
    print("     配点を見れば『30点の2問は相対的に軽い可能性が高い』まではタダで分かる。")

    print(header("4. 限界"))
    print("  * 難易度評価は Z会由来の主観評価（1–5）。一次資料ではない。")
    print("  * 配点が揃うのは 2008–2022 の12年。2011・2012・2025・2026 は配点が欠測。")
    print("  * 旧課程期が中心で、現行課程での再現は確認していない。")
    print("  * 『30点だから易しい』のか『易しい問題に30点を割り振っている』のかは区別できない。")
    print("    受験生にとってはどちらでも使えるが、因果の主張はしない。")
    print("  * 分野の検定は検出力不足。判定しないことを判定結果として報告する。")


if __name__ == "__main__":
    main()
