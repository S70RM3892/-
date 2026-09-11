import json,math,statistics as st
D=json.load(open('dep.json'))
deps=["情報","物理工","電電","建築","地球工","理工化"]
yrs=sorted(set(d['y'] for d in D)); R={(d['dep'],d['y']):d for d in D}
def ndf(x): return 0.5*(1+math.erf(x/math.sqrt(2)))
# --- ギャップ分散の分解: 情報の動き vs 相手の動き ---
print("情報−X のギャップ分散の分解（年平均からの乖離dvを使用）")
J=[R[('情報',y)]['dv'] for y in yrs]; Jd=[x-st.mean(J) for x in J]
for p in deps[1:]:
    P=[R[(p,y)]['dv'] for y in yrs]; Pd=[x-st.mean(P) for x in P]
    g=[a-b for a,b in zip(Jd,Pd)]
    vJ=st.pvariance(Jd); vP=st.pvariance(Pd)
    cov=sum(a*b for a,b in zip(Jd,Pd))/len(Jd)
    vg=st.pvariance(g)
    print(f"  情報−{p:<4} ギャップ分散{vg:6.3f} = 情報{vJ:5.3f} + {p}{vP:5.3f} − 2cov{cov:+6.3f}  → 情報の寄与 {vJ/(vJ+vP)*100:4.1f}%")
print()
# --- 第2志望ラダー: 合格確率 ---
#
# 【前提の出所】 sT / muT はこのリポジトリの一次資料からは出てこない外生の仮定。
#   sT  = 65.4点  … 受験生の総合得点 − 情報学科の合格最低点 の SD（1025点満点）
#   muT = -0.553*sT = -36.2点 … 同じ差の期待値。P(情報単願で合格)=29.0% に相当。
#   情報学科の実際の席/志願は8年平均 23.3% なので「平均的な志願者」ではなく、
#   特定の受験生の立ち位置を置いた値。README の「自分の模試成績は使っていない」は
#   この節には当てはまらない。水準を主張に使わず、学科の順序だけを読むこと。
#   muT を動かしたときの感度は rb.py の 5. に表がある。
sT=65.4; muT=-0.553*sT
K=(1025/100)**2          # 得点率pt^2 -> 点^2
VJ=st.pvariance([R[('情報',y)]['dv'] for y in yrs])*K   # 情報の最低点の分散
VS=sT**2-VJ                                            # 受験生自身の得点の分散
print(f"前提: 候補者スコア−情報最低点 の平均 {muT:+.1f}点, SD {sT:.1f}点 → P(情報)={ndf(muT/sT)*100:.1f}%")
print(f"      内訳 sT^2={sT**2:.0f} = 受験生 {VS:.0f} + 情報の最低点 {VJ:.0f} (点^2) … 97.7%は受験生側")
print()
print("X を第2志望に書いたときの『工学部のどこかに受かる』確率")
print("  誤: sqrt(sT^2+gapSD^2)  … gap にも sT にも情報の最低点が入っており二重計上")
print("  正: sqrt(Var(受験生)+Var(X の最低点))")
print(f"\n{'第2志望':<6}{'2026年のみ':>11}{'8年平均差':>10}{'差のSD':>8}{'誤SD':>7}{'正SD':>7}{'確率(正)':>9}{'確率(誤)':>9}{'2026のみ':>9}")
for p in deps[1:]:
    g=[R[('情報',y)]['dv']-R[(p,y)]['dv'] for y in yrs]
    gm=st.mean(g)/100*1025; gs=st.stdev(g)/100*1025; g26=g[-1]/100*1025
    VP=st.pvariance([R[(p,y)]['dv'] for y in yrs])*K
    s_bad=math.sqrt(sT**2+gs**2); s_ok=math.sqrt(VS+VP)
    print(f"{p:<6}{g26:>11.1f}{gm:>10.1f}{gs:>8.1f}{s_bad:>7.1f}{s_ok:>7.1f}"
          f"{ndf((muT+gm)/s_ok)*100:>8.1f}%{ndf((muT+gm)/s_bad)*100:>8.1f}%{ndf((muT+g26)/s_ok)*100:>8.1f}%")
print(f"{'なし':<6}{'—':>11}{'—':>10}{'—':>8}{sT:>7.1f}{sT:>7.1f}{ndf(muT/sT)*100:>8.1f}%{ndf(muT/sT)*100:>8.1f}%{ndf(muT/sT)*100:>8.1f}%")
print()
print("※ 令和9は情報学科の受入学生数目安が 87人(令和6)→94人 に増えており、2026 の")
print("  合格者は 99人。席が増えれば最低点は下がって差は縮むので、8年平均差は")
print("  構造変化を平均で薄めている。右端の『2026のみ』列の方が令和9に近い。rb.py 6.")
