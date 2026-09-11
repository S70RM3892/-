import json,math,statistics as st,random
D=json.load(open('dep.json'))
deps=["情報","物理工","電電","建築","地球工","理工化"]
yrs=sorted(set(d['y'] for d in D)); R={(d['dep'],d['y']):d for d in D}
def fit(ys):
    n=len(ys); xs=list(range(n)); mx=st.mean(xs); my=st.mean(ys)
    b=sum((a-mx)*(c-my) for a,c in zip(xs,ys))/sum((a-mx)**2 for a in xs)
    a0=my-b*mx; res=[c-(a0+b*a) for a,c in zip(xs,ys)]
    return b,res
print(f"{'学科':<5}{'平均dv':>8}{'トレンド/年':>10}{'定数除去SD':>10}{'トレンド除去SD':>13}")
sds={}
for p in deps:
    v=[R[(p,y)]['dv'] for y in yrs]
    b,res=fit(v)
    s0=st.stdev([x-st.mean(v) for x in v]); s1=math.sqrt(sum(x*x for x in res)/(len(v)-2))
    sds[p]=(s0,s1)
    print(f"{p:<5}{st.mean(v):>8.2f}{b:>10.3f}{s0:>10.3f}{s1:>13.3f}")

# F検定: 情報のトレンド除去残差分散 vs 他5学科プール
a=[ ]; 
for p in deps:
    v=[R[(p,y)]['dv'] for y in yrs]; b,res=fit(v)
    if p=='情報': ji=res
    else: a+=res
vj=sum(x*x for x in ji)/6; vo=sum(x*x for x in a)/(5*6)
print(f"\n情報 トレンド除去分散 {vj:.4f} (df6) vs 他5学科プール {vo:.4f} (df30)  F={vj/vo:.2f}")
# 並べ替え: 学科ラベルを年内でシャッフルし、情報のトレンド除去SDがこれ以上になる確率
random.seed(11); obs=math.sqrt(vj); cnt=0; N=100000
base={y:[R[(p,y)]['dv'] for p in deps] for y in yrs}
for _ in range(N):
    perm={y:random.sample(base[y],6) for y in yrs}
    v=[perm[y][0] for y in yrs]; b,res=fit(v)
    if math.sqrt(sum(x*x for x in res)/6)>=obs: cnt+=1
print(f"年内ラベル並べ替え検定 p={cnt/N:.4f}  (N={N})")

# leave-one-year-out
print("\n1年ずつ除いたときの情報のトレンド除去SD:")
for k,yy in enumerate(yrs):
    v=[R[('情報',y)]['dv'] for y in yrs if y!=yy]
    b,res=fit(v); print(f"  {yy}除外: {math.sqrt(sum(x*x for x in res)/(len(v)-2)):.3f}", end="")
print()
# 点数換算
for s,lab in [(sds['情報'][1],'情報'),(sds['地球工'][1],'地球工')]:
    print(f"{lab}: 合格最低点のブレ σ={s:.2f}得点率pt = {s/100*1025:.1f}点/1025 = 2σで±{2*s/100*1025:.0f}点")
