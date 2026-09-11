import json,math,statistics as st,random
D=json.load(open('dep.json'))
deps=["情報","物理工","電電","建築","地球工","理工化"]
yrs=sorted(set(d['y'] for d in D)); R={(d['dep'],d['y']):d for d in D}
def detr(ys):
    n=len(ys); xs=list(range(n)); mx=st.mean(xs); my=st.mean(ys)
    b=sum((a-mx)*(c-my) for a,c in zip(xs,ys))/sum((a-mx)**2 for a in xs)
    return [c-(my+b*(a-mx)) for a,c in zip(xs,ys)]
res={p:detr([R[(p,y)]['dv'] for y in yrs]) for p in deps}
def Fstat(g):  # g: dict dep->residuals
    vj=sum(x*x for x in g['情報'])/6
    vo=sum(x*x for p in deps if p!='情報' for x in g[p])/30
    return vj/vo
obs=Fstat(res)
pool=[x for p in deps for x in res[p]]
random.seed(3); N=200000; cnt=0
for _ in range(N):
    s=random.sample(pool,len(pool))
    g={p:s[i*8:(i+1)*8] for i,p in enumerate(deps)}
    if Fstat(g)>=obs: cnt+=1
print(f"情報 vs 他5学科 の分散比 F = {obs:.2f}")
print(f"残差の学科ラベル並べ替え検定（構造保存） p = {cnt/N:.5f}  (N={N})")
print(f"Bonferroni×6 = {min(1,6*cnt/N):.4f}")
print()
# 各学科を主役にしたときのF（情報が本当に特異か）
print("各学科を『主役』にしたときの分散比:")
for p in deps:
    vj=sum(x*x for x in res[p])/6
    vo=sum(x*x for q in deps if q!=p for x in res[q])/30
    print(f"  {p:<5} F={vj/vo:>5.2f}")
print()
# 倍率順位 vs 最低点順位
print("8年平均の順位（1が最上位）:")
for p in deps:
    rr=st.mean([sorted(deps,key=lambda q:-R[(q,y)]['ratio']).index(p)+1 for y in yrs])
    rv=st.mean([sorted(deps,key=lambda q:-R[(q,y)]['dv']).index(p)+1 for y in yrs])
    print(f"  {p:<5} 志願倍率順位 {rr:.2f}  合格最低点順位 {rv:.2f}  ずれ {rv-rr:+.2f}")
