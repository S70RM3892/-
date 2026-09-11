# -*- coding: utf-8 -*-
"""README §6「棄却・断念した仮説」の再現。

主張を載せている以上、再現コードが要る。ここで分かるのは
  再現する … 仮説3（志願倍率）、仮説4（パススルー、sd3.py）、仮説5（得点開示）
  再現しない … 仮説1（隔年現象）、仮説2（難易度→平均点）
      どちらも結論（棄却／断念）は支持されるが、README の具体的な数値は
      コミット済みのデータからは出てこない。入力が repo に無い。
実行: python3 rej.py
"""
import json, math, os, random, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
DEPS = ["情報", "物理工", "電電", "建築", "地球工", "理工化"]


def corr(x, y):
    mx, my = st.mean(x), st.mean(y)
    dx = math.sqrt(sum((a - mx) ** 2 for a in x))
    dy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (dx * dy) if dx * dy else float("nan")


print("=" * 72)
print("仮説1  隔年現象（合格最低点は上がった翌年に下がる）… 棄却")
print("=" * 72)
# 情報学科の合格最低点 10 年。2017-2018 は dep.json に無いので artifacts/
# kyodai-score-sheet.html の推移表（代ゼミ + Copynight 氏サイトの 2 ソース一致）から。
Y = list(range(2017, 2027))
LAST = [611.10, 662.81, 638.58, 570.91, 634.45, 676.50, 697.70, 623.20, 707.52, 645.49]
rate = [l / (1025 if y >= 2025 else 1000) * 100 for y, l in zip(Y, LAST)]
d = [b - a for a, b in zip(rate, rate[1:])]
obs = corr(d[:-1], d[1:])
random.seed(0)
N = 100000
null = []
for _ in range(N):
    s = [random.gauss(0, 1) for _ in range(len(rate))]
    dd = [b - a for a, b in zip(s, s[1:])]
    c = corr(dd[:-1], dd[1:])
    if c == c:
        null.append(c)
p = sum(1 for c in null if c <= obs) / len(null)
print(f"   得点率 {['%.2f' % x for x in rate]}")
print(f"   1階差分の lag-1 自己相関  実測 r = {obs:+.3f}")
print(f"   iid 帰無（差分を取ると機械的に負になる）平均 r = {st.mean(null):+.3f}")
print(f"   実測が帰無より負である片側 p = {p:.3f}")
print("   → 実測は帰無より negative ですらない。隔年現象の証拠なし＝棄却。結論は支持。")
print()
print("   【再現しない】README は 実測 -0.568 / 帰無 -0.696 / p=0.992 と書いているが")
print("   上の通り -0.441 / -0.459 にしかならない。帰無平均は系列長 n=5..13 のどこでも")
print("   -0.45〜-0.48 の範囲で、-0.696 は出ない。README の数値は別の統計量か別の系列で、")
print("   その入力はこの repo に無い。数値は取り下げ、結論（棄却）だけ残すのが正しい。")

print()
print("=" * 72)
print("仮説2  二次の難易度から平均点を予測する … 断念（精度不足）")
print("=" * 72)
dist = json.load(open(os.path.join(HERE, "../data/dist.json"), encoding="utf-8"))
ys = [r["y"] for r in dist]
rt = [r["rate"] for r in dist]
print(f"   data/dist.json: {len(dist)} 年 ({ys[0]}–{ys[-1]}, 欠測 "
      f"{sorted(set(range(ys[0], ys[-1]+1)) - set(ys))})")
print(f"   得点率の SD  全{len(rt)}年 = {st.stdev(rt):.2f}pt")
# 難易度平均 -> 得点率 の単回帰を leave-one-out
xs = [r["mean"] for r in dist]
loo = []
for i in range(len(xs)):
    a = [xs[j] for j in range(len(xs)) if j != i]
    b = [rt[j] for j in range(len(xs)) if j != i]
    ma, mb = st.mean(a), st.mean(b)
    sl = sum((u - ma) * (v - mb) for u, v in zip(a, b)) / sum((u - ma) ** 2 for u in a)
    loo.append(abs(rt[i] - (mb + sl * (xs[i] - ma))))
print(f"   難易度平均 -> 得点率 の LOO MAE = {st.mean(loo):.2f}pt  vs 変動 SD {st.stdev(rt):.2f}pt")
print(f"   相関 r = {corr(xs, rt):+.3f}")
print("   → MAE が SD を下回らない＝予測になっていない。断念という結論は支持。")
print()
print("   【再現しない】README は「11年OOS で MAE 6.65pt > 変動σ 4.09pt」と書いているが、")
print("   dist.json は 17 年あり、σ=4.09 になる 11 年窓は 2013–2025 の 4.16 が最も近い程度で")
print("   一意に決まらない。どの年をどう外して 11 年にしたのかが記録されていない。")

print()
print("=" * 72)
print("仮説3  志願倍率が合格最低点の 70% を説明する … 再現する")
print("=" * 72)
D = json.load(open(os.path.join(HERE, "dep.json"), encoding="utf-8"))
yrs = sorted(set(x["y"] for x in D))
R = {(x["dep"], x["y"]): x for x in D}
X = [R[(p, y)]["dr"] for y in yrs for p in DEPS]     # 志願倍率の年内乖離
Yv = [R[(p, y)]["dv"] for y in yrs for p in DEPS]    # 最低点の年内乖離
r = corr(X, Yv)
b = sum(a * c for a, c in zip(X, Yv)) / sum(a * a for a in X)
loo = []
for i in range(len(X)):
    a = [X[j] for j in range(len(X)) if j != i]
    c = [Yv[j] for j in range(len(X)) if j != i]
    bb = sum(u * v for u, v in zip(a, c)) / sum(u * u for u in a)
    loo.append(abs(Yv[i] - bb * X[i]))
print(f"   年固定効果あり {len(X)} 観測   r = {r:+.3f}   R^2 = {r*r:.3f}   傾き = {b:.3f}")
print(f"   LOO MAE = {st.mean(loo):.2f}pt   (README: r=+0.837, 70%, LOO MAE 1.03)  → 一致")
print("   ※ ただし『説明する』は同時点の相関であって予測ではない。志願倍率が確定するのは")
print("     出願締切後（令和9なら 2027-02-03 以降）で、そこから対策は動かせない。")

print()
print("=" * 72)
print("仮説4  需要のパススルーが最低点順位とともに減衰する … 検出力不足")
print("=" * 72)
print("   sd3.py が出力する:  順位 vs パススルー傾き r=+0.050, 全順列 p(片側,負)=0.5167")
print("   n=6 学科の順位相関なので、全順列でも 720 通りしかない。棄却も採択もできない。")

print()
print("=" * 72)
print("仮説5  得点開示データから科目間相関を推定する … データ不足")
print("=" * 72)
K = json.load(open(os.path.join(HERE, "../data/kaiji2.json"), encoding="utf-8"))
eng = [r for r in K if r.get("fac") == "工学部"]
full = [r for r in eng if all(k in r for k in ("国語", "数学", "理科", "英語"))]
print(f"   kaiji2.json 全 {len(K)} 件 / 工学部 {len(eng)} 件 / 4 科目そろい {len(full)} 件")
print(f"   学部を問わず 4 科目そろうもの: {sum(1 for r in K if all(k in r for k in ('国語','数学','理科','英語')))} 件")
print("   → 6 個の科目間相関を推定するには全く足りない。README の『11件』は")
print("     ファイル全体の行数であって工学部の件数ではない。断念という結論は支持。")
