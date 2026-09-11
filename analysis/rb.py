# -*- coding: utf-8 -*-
"""頑健性チェック（robustness）。

既存の sd*/kt*/irt* が出す結論のうち、前提を変えると壊れるものを洗い出す。
結論を置き換えるためではなく、README のどの数字を信じてよいかを決めるための
スクリプト。stdlib のみ。  実行: python3 rb.py
"""
import json, math, os, random, statistics as st, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "dep.json"), encoding="utf-8"))
DEPS = ["情報", "物理工", "電電", "建築", "地球工", "理工化"]
YRS = sorted(set(d["y"] for d in D))
R = {(d["dep"], d["y"]): d for d in D}
K = (1025 / 100) ** 2          # 得点率pt^2 -> 1025点満点の点^2
ndf = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))


def detr(ys):
    n = len(ys); xs = list(range(n)); mx = st.mean(xs); my = st.mean(ys)
    b = sum((a - mx) * (c - my) for a, c in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs)
    return [c - (my + b * (a - mx)) for a, c in zip(xs, ys)]


def Fstat(g, star="情報", df=6):
    vj = sum(x * x for x in g[star]) / df
    vo = sum(x * x for p in DEPS if p != star for x in g[p]) / (5 * df)
    return vj / vo


print("=" * 72)
print("1. dv は構成上ゼロ和 — 6 学科は独立標本ではない")
print("=" * 72)
for y in YRS:
    print(f"   {y}  Σdv = {sum(R[(p, y)]['dv'] for p in DEPS):+.1e}")
print("   → F 検定が仮定する df=(6,30) は過大。情報が上振れした年は他 5 学科が")
print("     機械的に下振れするので、sd7 が出す cov<0 の一部は実質のない副産物。")

print()
print("=" * 72)
print("2. 『情報の合格最低点は突出して不安定』は学部内乖離に限った話")
print("=" * 72)
print(f"   {'基準':<26}{'F(情報 vs 他5)':>14}   学科別トレンド除去SD(pt)")
for key, lab in (("rate", "rate  絶対得点率"), ("dv", "dv    学部平均からの乖離")):
    res = {p: detr([R[(p, y)][key] for y in YRS]) for p in DEPS}
    sds = {p: math.sqrt(sum(x * x for x in res[p]) / 6) for p in DEPS}
    print(f"   {lab:<26}{Fstat(res):>14.2f}   " + " ".join(f"{p}{sds[p]:.2f}" for p in DEPS))
print("   → 絶対値で見ると 6 学科とも SD≒4.2pt(≒43点/1025) で横並び、F=0.97。")
print("     合格最低点の年変動そのものは全学科共通（全国の難易度ショック）であって、")
print("     情報に固有なのは『学部平均からどれだけ離れるか』の部分だけ。")
print("     README の σ=1.04pt=10.6点 は “受験生自身の得点も学部平均と 1:1 で”")
print("     “連動する” と仮定したときの実効ブレであり、絶対ブレは 4 倍大きい。")

print()
print("=" * 72)
print("3. 並べ替え検定は帰無の組み方で p が 0.004 から 0.97 まで動く")
print("=" * 72)
res = {p: detr([R[(p, y)]["dv"] for y in YRS]) for p in DEPS}
obs = Fstat(res)
random.seed(1); N = 200000

pool = [x for p in DEPS for x in res[p]]; c = 0
for _ in range(N):
    s = random.sample(pool, len(pool))
    if Fstat({p: s[i * 8:(i + 1) * 8] for i, p in enumerate(DEPS)}) >= obs: c += 1
p_pool = c / N

byyear = [[res[p][i] for p in DEPS] for i in range(len(YRS))]; c = 0
for _ in range(N):
    pm = [random.sample(col, 6) for col in byyear]
    if Fstat({p: [pm[i][k] for i in range(len(YRS))] for k, p in enumerate(DEPS)}) >= obs: c += 1
p_year = c / N

raw = {y: [R[(p, y)]["dv"] for p in DEPS] for y in YRS}
obs_sd = math.sqrt(sum(x * x for x in res["情報"]) / 6); c = 0
for _ in range(N // 2):
    pm = {y: random.sample(raw[y], 6) for y in YRS}
    if math.sqrt(sum(x * x for x in detr([pm[y][0] for y in YRS])) / 6) >= obs_sd: c += 1
p_raw = c / (N // 2)

print(f"   観測 F = {obs:.2f}")
print(f"   (a) 残差をプールしてランダムに 6 群へ    p = {p_pool:.4f}   ← sd5.py が採用、README の数字")
print(f"   (b) 残差を『年内で』学科ラベル入替      p = {p_year:.4f}   ← 年のゼロ和とヘテロを保存。妥当")
print(f"   (c) 生 dv を年内で学科ラベル入替        p = {p_raw:.4f}   ← sd4.py が出力している値")
print("   → (c) の帰無は『6 学科の水準が全部同じ』。情報が毎年 +5pt 高いことは")
print("     争点ではないので、この帰無は誰も信じておらず p=0.97 は検定として無意味。")
print("     sd4.py はこれを注記なしで F=4.45 の直後に印字しており、読み手を誤らせる。")
print(f"   → 構造を保存した (b) でも p={p_year:.4f} なので、結論自体は (a) と整合。")

print()
print("=" * 72)
print("4. その結論は 2024 年 1 点にぶら下がっている")
print("=" * 72)
print(f"   {'除外年':<8}{'F':>7}{'情報SD(pt)':>12}{'p(プール入替)':>14}{'Bonferroni x6':>15}")
random.seed(5)
for drop in [None] + YRS:
    yy = [y for y in YRS if y != drop]; df = len(yy) - 2
    rr = {p: detr([R[(p, y)]["dv"] for y in yy]) for p in DEPS}
    o = Fstat(rr, df=df)
    pl = [x for p in DEPS for x in rr[p]]; c = 0; n2 = 20000
    for _ in range(n2):
        s = random.sample(pl, len(pl))
        if Fstat({p: s[i * len(yy):(i + 1) * len(yy)] for i, p in enumerate(DEPS)}, df=df) >= o: c += 1
    pv = c / n2
    print(f"   {str(drop or '(なし)'):<8}{o:>7.2f}"
          f"{math.sqrt(sum(x*x for x in rr['情報'])/df):>12.3f}{pv:>14.4f}{min(1,6*pv):>15.3f}")
print("   → 2024 を落とすと F は 4.45→1.96、Bonferroni 後の p は 0.025→0.21。")
print("     『情報だけ不安定』は 8 年全部を使ったときにだけ有意で、外れ値 1 年に依存する。")

print()
print("=" * 72)
print("5. 第2志望ラダーの確率は、出所不明の定数 2 つがほぼ全部を決めている")
print("=" * 72)
sT, muT = 65.4, -0.553 * 65.4
VJ = st.pvariance([R[("情報", y)]["dv"] for y in YRS]) * K
VS = sT ** 2 - VJ
print(f"   sd7.py の前提: sT={sT} 点, muT={muT:+.1f} 点 (P(情報単願)={ndf(-0.553)*100:.1f}%)")
print(f"   この 2 つの出所はリポジトリのどこにも無い。README は『自分の模試成績は")
print(f"   使っていない』と書いているが、muT は特定の受験生の立ち位置そのもの。")
print(f"   情報学科の実際の席/志願 = {st.mean([R[('情報',y)]['acc']/R[('情報',y)]['app'] for y in YRS])*100:.1f}%"
      f" なので『平均的志願者』でもない。")
print(f"   分散の内訳: sT^2={sT**2:.0f} = 受験生自身の得点 {VS:.0f} + 情報の最低点 {VJ:.0f} (点^2)")
print(f"   → 97.7% が受験生側。ラダーの数字は事実上この 1 個の仮定の関数。")
print()
print(f"   {'第2志望':<6}{'8年平均差':>10}{'2026のみ':>9}{'sd7のSD':>9}{'補正SD':>8}{'sd7 P':>8}{'補正 P':>8}")
for p in DEPS[1:]:
    g = [R[("情報", y)]["dv"] - R[(p, y)]["dv"] for y in YRS]
    gm = st.mean(g) / 100 * 1025; gs = st.stdev(g) / 100 * 1025; g26 = g[-1] / 100 * 1025
    VP = st.pvariance([R[(p, y)]["dv"] for y in YRS]) * K
    s_old = math.sqrt(sT ** 2 + gs ** 2); s_new = math.sqrt(VS + VP)
    print(f"   {p:<6}{gm:>10.1f}{g26:>9.1f}{s_old:>9.1f}{s_new:>8.1f}"
          f"{ndf((muT+gm)/s_old)*100:>7.1f}%{ndf((muT+gm)/s_new)*100:>7.1f}%")
print("   → sd7 は sqrt(sT^2 + gap^2) を使うが、gap = (情報の最低点 − X の最低点) には")
print("     情報の最低点が入っており、sT にも入っている。足すと二重計上になる。")
print("     正しくは sqrt(Var(受験生) + Var(X の最低点))。相手の最低点は情報より静かなので")
print("     真の SD は sT より小さく、sd7 は分散を過大評価している（影響は +0.1〜0.6pt と小）。")
print()
print("   muT 感度（補正 SD で計算）:")
print(f"   {'P(情報単願)':>11}" + "".join(f"{p:>9}" for p in DEPS[1:]))
for pj in (0.10, 0.20, 0.29, 0.40, 0.50, 0.65):
    mu = st.NormalDist().inv_cdf(pj) * sT
    line = f"   {pj*100:>10.0f}%"
    for p in DEPS[1:]:
        g = [R[("情報", y)]["dv"] - R[(p, y)]["dv"] for y in YRS]
        VP = st.pvariance([R[(p, y)]["dv"] for y in YRS]) * K
        line += f"{ndf((mu+st.mean(g)/100*1025)/math.sqrt(VS+VP))*100:>8.1f}%"
    print(line)
print("   → 順序（理工化 > 地球工 > 建築 > 電電 > 物理工）はどこでも不変。")
print("     水準は全く当てにならない。README は順序だけを主張に使うべき。")

print()
print("=" * 72)
print("6. 8 年パネルは配点 regime と定員の断層を跨いでいる")
print("=" * 72)
print("   2019-2024 入試 … 1000 点満点 / 共通テストに『情報』なし")
print("   2025-2026 入試 … 1025 点満点 / 共通テスト『情報Ⅰ』50 点（新課程）")
print("   → 現行配点のデータはまだ 2 年。σ=1.04pt は 6 年分が旧配点。")
print("     しかも kt2.py は『情報Ⅰ が共テ分散の 48.4% を占める』と言っている。")
print("     情報Ⅰ の新設は最低点の分散を増やす向きに効くはずで、旧配点由来の")
print("     σ を令和9 の予測にそのまま使うのは下振れ側に偏る。")
sd_kt = 3.72                       # kt2.py 令和8: 共テ合計の上位10%層内 SD（1025点換算）
share_joho = 0.484
sd_wo = sd_kt * math.sqrt(1 - share_joho)
sig = math.sqrt(sum(x * x for x in detr([R[("情報", y)]["dv"] for y in YRS])) / 6) / 100 * 1025
print(f"     粗い見積り: 共テ合計SD {sd_kt:.2f}点 → 情報Ⅰ 抜きなら {sd_wo:.2f}点。")
print(f"     最低点 σ={sig:.1f}点 の分散に占める共テ寄与は {sd_kt**2/sig**2*100:.0f}% なので、")
print(f"     regime 変更による σ の押し上げは {math.sqrt(sig**2-sd_kt**2+sd_wo**2):.1f}→{sig:.1f}点、+3% 程度で済む。")
print()
print("   定員の断層（こちらは効く）:")
print(f"   {'年':<6}{'情報 席':>8}{'志願':>7}{'倍率':>7}{'物理工との差(点)':>17}")
for y in YRS:
    g = (R[("情報", y)]["dv"] - R[("物理工", y)]["dv"]) / 100 * 1025
    r = R[("情報", y)]
    print(f"   {y:<6}{r['acc']:>8.0f}{r['app']:>7.0f}{r['ratio']:>7.2f}{g:>17.1f}")
print("   募集要項の受入学生数目安: 令和6=87 人 → 令和9=94 人（r6senbatsu.txt / r9.txt）")
print("   → 席が増えれば最低点は下がり、他学科との差は縮む。実際 2026 の差は")
print("     8 年で最小クラス。sd7 が 8 年平均差を採用するのは、既知の構造変化を")
print("     わざわざ平均で薄めている。令和9 予測には直近側に重みを置くべき。")

print()
print("=" * 72)
print("7. IRT の『まだ落としている 23.7 点』は較正基準に丸ごと依存する")
print("=" * 72)
os.chdir(HERE)
g = {}
exec(open("irt.py", encoding="utf-8").read(), g)
exec(open("kt.py", encoding="utf-8").read().split("# 令和9年度")[0], g)
items, calib, at, pct, load = g["items"], g["calib"], g["at"], g["pct"], g["load"]
S = load("dist_r8.csv")
SPEC = [("数学Ⅰ，数学Ａ", .125), ("物理", .125), ("化学", .125),
        ("英語（リーディング）", .25), ("英語（リスニング）", .25),
        ("情報Ⅰ", .5), ("公共，政治・経済", .5)]


def calib_to(it, target, z):
    lo, hi = 0.05, 0.99
    for _ in range(60):
        mid = (lo + hi) / 2
        if at(it, mid, z) < target: lo = mid
        else: hi = mid
    return (lo + hi) / 2


print("   設問データの前提チェック:")
nb = nt = 0
cur = None
for l in open(os.path.join(HERE, "../data/q_r8.csv"), "rb").read().decode("cp932", "replace").splitlines():
    f = [x.strip() for x in l.split(",")]
    if f[0].startswith("科目＝"): cur = f[0][3:]; continue
    if cur != "情報Ⅰ" or len(f) < 6 or f[1] in ("解答番号", "合計") or f[0] == "大問": continue
    try: nt += 1; nb += abs(float(f[4]) - float(f[5])) > 1e-9
    except ValueError: nt -= 1
print(f"     情報Ⅰ: 部分点のある設問 {nb}/{nt} → ベルヌーイ近似は概ね妥当")
for key, _ in SPEC:
    it = items("../data/q_r8.csv", key)
    assert abs(sum(x[2] for x in it) - S[key]["max"]) < 1e-6, f"{key} の配点合計が満点と不一致"
print("     全科目で 配点合計 == 公表満点 を assert 済み（パース欠落なし）")
print()
print(f"   {'科目':<16}{'r(SD較正)':>10}{'落し':>6}{'r(p90較正)':>11}{'落し':>6}{'r(p97.7較正)':>13}{'落し':>6}")
T = [0.0, 0.0, 0.0]
for key, co in SPEC:
    it = items("../data/q_r8.csv", key); s = S[key]; mx = sum(x[2] for x in it)
    rs = (calib(it, s["sd"]), calib_to(it, pct(s, 90), 1.2816), calib_to(it, pct(s, 97.7), 2.0))
    gs = [(mx - at(it, r, 2.0)) * co for r in rs]
    T = [a + b for a, b in zip(T, gs)]
    print(f"   {key:<16}{rs[0]:>10.3f}{gs[0]:>6.1f}{rs[1]:>11.3f}{gs[1]:>6.1f}{rs[2]:>13.3f}{gs[2]:>6.1f}")
print(f"   {'合計(数ⅡBC除く)':<16}{'':>10}{T[0]:>6.1f}{'':>11}{T[1]:>6.1f}{'':>13}{T[2]:>6.1f}")
print("   → SD で較正すると r が毎科目いちばん小さくなる。単一の識別力 r では")
print("     『分布全体の SD』と『上位裾』を同時に再現できず、SD を合わせにいくと")
print("     裾を外す。上位 2.3% の話をしたいなら裾で較正した r(p97.7) が筋。")
print("     README が併記する 23.7 / 16.6 点は別手法の上下限ではなく、")
print("     同じ模型を別の的に合わせただけ。採るべき中心値は 16 点台。")
print()
print("   z を動かしたときの取りこぼし（1025点換算、p97.7 較正）:")
print(f"   {'科目':<16}" + "".join(f"{'z=+'+str(z):>9}" for z in (1.5, 2.0, 2.5)))
tot = [0.0, 0.0, 0.0]
for key, co in SPEC:
    it = items("../data/q_r8.csv", key); s = S[key]; mx = sum(x[2] for x in it)
    r = calib_to(it, pct(s, 97.7), 2.0)
    gs = [(mx - at(it, r, z)) * co for z in (1.5, 2.0, 2.5)]
    tot = [a + b for a, b in zip(tot, gs)]
    print(f"   {key:<16}" + "".join(f"{v:>9.1f}" for v in gs))
print(f"   {'合計':<16}" + "".join(f"{v:>9.1f}" for v in tot))
print("   → 全科目一律 z=+2 は『どの科目でも全国上位2.3%』という受験生像。")
print("     京大工の志願者は二次 800 点が数学・理科・英語なのでその 3 つに選抜が")
print("     かかっており、実像は 数学理科で z 高め・情報Ⅰ/地歴公民で z 低め。")
print("     その方向に補正すると取りこぼしの情報Ⅰ/地歴公民への集中はさらに強まる。")
print("     つまり『配点の歪みゆえ情報Ⅰと地歴公民が効く』という結論は頑健で、")
print("     数字 23.7 点の方が脆い。")
