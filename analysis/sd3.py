import json,math,statistics as st,itertools,random
exec(open('sd2.py').read().split('SIG=')[0].split("print(f\"{'学科'")[0])
D=json.load(open('dep.json'))
deps=["情報","物理工","電電","建築","地球工","理工化"]
yrs=sorted(set(d['y'] for d in D)); R={(d['dep'],d['y']):d for d in D}
SIG=7.2
# 学部全体プールで決まるとしたときの順序統計SD
for y in yrs[:1]: pass
tot_app=st.mean([sum(R[(p,y)]['app'] for p in deps) for y in yrs])
tot_seat=st.mean([sum(R[(p,y)]['acc'] for p in deps) for y in yrs])
pr=tot_seat/tot_app; z=iphi(1-pr)
pool_sd=SIG*math.sqrt(pr*(1-pr)/tot_app)/phi(z)
print(f"学部全体プール: 志願{tot_app:.0f} 席{tot_seat:.0f} 合格率{pr:.3f} → 学部限界点の順序統計SD = {pool_sd:.3f} pt")
print(f"（実測）地球工 0.236 / 理工化 0.418 → 学部限界点のSD {pool_sd:.3f} に近い")
print(f"（実測）情報 1.030 → 自プール順序統計 0.506 の2.0倍\n")

# --- パススルー試験: 自学科需要の変化がどれだけ最低点に伝わるか ---
# 2元固定効果で除去した残差どうしの傾き
def demean2(key):
    v={(p,y):R[(p,y)][key] for p in deps for y in yrs}
    for _ in range(50):
        for y in yrs:
            m=st.mean(v[(p,y)] for p in deps)
            for p in deps: v[(p,y)]-=m
        for p in deps:
            m=st.mean(v[(p,y)] for y in yrs)
            for y in yrs: v[(p,y)]-=m
    return v
X=demean2('ratio'); Y=demean2('rate')
print(f"{'学科':<5}{'最低点順位':>7}{'パススルー傾き':>13}{'R2':>7}")
slp=[]
for p in deps:
    xs=[X[(p,y)] for y in yrs]; ys=[Y[(p,y)] for y in yrs]
    b=sum(a*c for a,c in zip(xs,ys))/sum(a*a for a in xs)
    ss=sum((c-b*a)**2 for a,c in zip(xs,ys)); tt=sum(c*c for c in ys)
    rank=st.mean([sorted(deps,key=lambda q:-R[(q,y)]['dv']).index(p)+1 for y in yrs])
    slp.append((p,rank,b,1-ss/tt)); print(f"{p:<5}{rank:>7.2f}{b:>13.3f}{1-ss/tt:>7.3f}")
xs=[s[1] for s in slp]; ys=[s[2] for s in slp]
mx,my=st.mean(xs),st.mean(ys)
r=sum((a-b)*(c-d) for a,b,c,d in zip(xs,[mx]*6,ys,[my]*6))/math.sqrt(sum((a-mx)**2 for a in xs)*sum((c-my)**2 for c in ys))
perm=[sum((a-mx)*(c-my) for a,c in zip(xs,pm))/math.sqrt(sum((a-mx)**2 for a in xs)*sum((c-my)**2 for c in ys)) for pm in itertools.permutations(ys)]
print(f"\n順位 vs パススルー傾き r={r:+.3f}  全順列 p(片側,負)={sum(1 for q in perm if q<=r)/len(perm):.4f}")

# --- 情報の残差SDが最大であることの並べ替え検定 ---
res={p:[R[(p,y)]['dv'] for y in yrs] for p in deps}
res={p:[x-st.mean(v) for x in v] for p,v in res.items()}
obs=st.stdev(res['情報'])
allr=[x for p in deps for x in res[p]]
random.seed(7); cnt=0;N=200000
for _ in range(N):
    s=random.sample(allr,8)
    if st.stdev(s)>=obs: cnt+=1
print(f"情報の残差SD {obs:.3f} pt が6学科中最大: 無作為抽出でこれ以上になる確率 p={cnt/N:.4f}")
