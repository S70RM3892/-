import json,math,statistics as st
D=json.load(open('dep.json'))
deps=["情報","物理工","電電","建築","地球工","理工化"]
yrs=sorted(set(d['y'] for d in D)); R={(d['dep'],d['y']):d for d in D}
print("情報 − 各学科 の合格最低点差（得点率pt / 1025点換算）")
print(f"{'年':<6}"+"".join(f"{p:>12}" for p in deps[1:]))
G={p:[] for p in deps[1:]}
for y in yrs:
    line=f"{y:<6}"
    for p in deps[1:]:
        g=R[('情報',y)]['dv']-R[(p,y)]['dv']; G[p].append(g)
        line+=f"{g:>6.2f}/{g/100*1025:>5.1f}"
    print(line)
print()
print(f"{'学科':<6}{'平均差pt':>9}{'平均差(点)':>11}{'SD pt':>8}{'SD(点)':>8}")
for p in deps[1:]:
    m=st.mean(G[p]); s=st.stdev(G[p])
    print(f"{p:<6}{m:>9.2f}{m/100*1025:>11.1f}{s:>8.2f}{s/100*1025:>8.1f}")
