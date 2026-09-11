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
# --- 第2志望ラダー再計算: 8年平均ギャップ + 最低点ノイズ ---
sT=65.4; muT=-0.553*sT
print(f"前提: 候補者スコア−情報最低点 の平均 {muT:+.1f}点, SD {sT:.1f}点 → P(情報)={ndf(muT/sT)*100:.1f}%")
print(f"\n{'第2志望':<6}{'2026年のみ':>11}{'8年平均差':>10}{'差のSD':>8}{'合格確率':>9}{'旧(2026)':>9}")
G26={}; 
for p in deps[1:]:
    g=[R[('情報',y)]['dv']-R[(p,y)]['dv'] for y in yrs]
    gm=st.mean(g)/100*1025; gs=st.stdev(g)/100*1025; g26=g[-1]/100*1025
    s=math.sqrt(sT**2+gs**2)
    new=ndf((muT+gm)/s)*100; old=ndf((muT+g26)/sT)*100
    print(f"{p:<6}{g26:>11.1f}{gm:>10.1f}{gs:>8.1f}{new:>8.1f}%{old:>8.1f}%")
print(f"{'なし':<6}{'—':>11}{'—':>10}{'—':>8}{ndf(muT/sT)*100:>8.1f}%{ndf(muT/sT)*100:>8.1f}%")
