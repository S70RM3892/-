import json,math,statistics as st
D=json.load(open('dep.json'))
deps=["情報","物理工","電電","建築","地球工","理工化"]
yrs=sorted(set(d['y'] for d in D)); R={(d['dep'],d['y']):d for d in D}
def phi(x): return math.exp(-x*x/2)/math.sqrt(2*math.pi)
def iphi(p):  # inverse normal
    a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00]
    b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,6.680131188771972e+01,-1.328068155288572e+01]
    c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,-2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00]
    d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00]
    pl=0.02425
    if p<pl:
        q=math.sqrt(-2*math.log(p)); return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p>1-pl:
        q=math.sqrt(-2*math.log(1-p)); return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q=p-0.5; r=q*q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

SIG=7.2  # 志願者の総合得点率SD(pt)  ※2025 68.7/1025=6.70, 2026 80.1/1025=7.81 の中間
print(f"{'学科':<5}{'最低点順位':>7}{'席':>5}{'志願':>6}{'1/倍率':>7}{'観測残差SD':>10}{'順序統計SD':>10}{'超過':>8}")
rows=[]
for p in deps:
    v=[R[(p,y)]['dv'] for y in yrs]
    resid=st.stdev([x-st.mean(v) for x in v])
    seats=st.mean([R[(p,y)]['acc'] for y in yrs]); napp=st.mean([R[(p,y)]['app'] for y in yrs])
    pr=seats/napp; z=iphi(1-pr)
    osd=SIG*math.sqrt(pr*(1-pr)/napp)/phi(z)
    rank=[sorted(deps,key=lambda q:-R[(q,y)]['dv']).index(p)+1 for y in yrs]
    rows.append((p,st.mean(rank),seats,napp,pr,resid,osd,resid/osd))
    print(f"{p:<5}{st.mean(rank):>7.2f}{seats:>5.0f}{napp:>6.0f}{pr:>7.3f}{resid:>10.3f}{osd:>10.3f}{resid/osd:>8.2f}")
# 相関: 最低点順位 vs 超過ノイズ
import itertools
xs=[r[1] for r in rows]; ys=[r[7] for r in rows]
mx,my=st.mean(xs),st.mean(ys)
r=sum((a-mx)*(b-my) for a,b in zip(xs,ys))/math.sqrt(sum((a-mx)**2 for a in xs)*sum((b-my)**2 for b in ys))
print(f"\n最低点順位（1=最上位）と『超過ノイズ倍率』の相関 r = {r:+.3f}  (n=6)")
# 順位相関の全順列検定
perm=[]
for pm in itertools.permutations(ys):
    rr=sum((a-mx)*(b-my) for a,b in zip(xs,pm))/math.sqrt(sum((a-mx)**2 for a in xs)*sum((b-my)**2 for b in ys))
    perm.append(rr)
pv=sum(1 for q in perm if q>=r)/len(perm)
print(f"全順列検定 p(片側) = {pv:.4f}  ({len(perm)}通り)")
