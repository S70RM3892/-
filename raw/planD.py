exec(open('parse.py').read())
import json,math
REC=json.load(open('kyodai_official.json'))
YEARS=[2026,2025,2024,2023,2022,2021,2020,2019]
D={2024:load('dist_r6.csv'),2025:load('dist_r7.csv'),2026:load('dist_r8.csv')}
# 共テ科目（理系・地理選択・物化）: (キー候補, 満点)
CT_SUB={
 '国語':(['国語'],200),
 '社会':(['地理総合，地理探究','地理Ｂ'],100),
 '数学':(['数学Ⅰ，数学Ａ','数学Ⅰ・数学Ａ'],100,['数学Ⅱ，数学Ｂ，数学Ｃ','数学Ⅱ・数学Ｂ'],100),
 '理科':(['物理'],100,['化学'],100),
 '英R':(['英語（リーディング）'],100),
 '英L':(['英語（リスニング）'],100),
 '情報':(['情報Ⅰ'],100),
}
ORDER=['国語','社会','数学','理科','英R','英L','情報']
def q(y,names,top):
    S=D[y]
    s=next((S[n] for n in names if n in S),None)
    return pct(s,top) if s else None
def ct_ratio(y,top):
    """各共テ科目の『得点率』を上位topの実測分位点から"""
    r={}
    for k,v in CT_SUB.items():
        if len(v)==2:
            a=q(y,v[0],top); r[k]=None if a is None else a/v[1]
        else:
            a=q(y,v[0],top); b=q(y,v[2],top)
            r[k]=None if (a is None or b is None) else (a+b)/(v[1]+v[3])
    return r
RAW={'国語':100,'数学':200,'理科':200,'外国語':150}   # 二次素点満点
SEC=['国語','数学','理科','外国語']
RIKEI=[r for r in REC if r['fac'] in
 ['総合人間学部(理)','教育学部(理)','経済学部(理)','理学部','医学部(医学科)','医学部(人間健康学科)',
  '薬学部','工学部(地球工学科)','工学部(建築学科)','工学部(物理工学科)','工学部(電気電子工学科)',
  '工学部(情報学科)','工学部(理工化学科(旧工化))','農学部']]
def solve(A,b):
    n=len(A[0])
    M=[[sum(A[i][r]*A[i][c] for i in range(len(A))) for c in range(n)]+[sum(A[i][r]*b[i] for i in range(len(A)))] for r in range(n)]
    for i in range(n):
        p=max(range(i,n),key=lambda k:abs(M[k][i])); M[i],M[p]=M[p],M[i]
        for k in range(n):
            if k!=i and M[i][i]!=0:
                f=M[k][i]/M[i][i]
                for j in range(i,n+1): M[k][j]-=f*M[i][j]
    return [M[i][n]/M[i][i] for i in range(n)]

def run(top):
    print("="*78)
    print(f"■ 共テ層＝上位{top*100:.0f}%（全受験者中）と仮定")
    print("="*78)
    NIJI={}
    for y in (2024,2025,2026):
        r=ct_ratio(y,top); wkey='center' if y<2025 else 'c25'
        for f in RIKEI:
            c=f[wkey]
            ct=sum(c[i]*r[ORDER[i]] for i in range(7) if c[i])
            NIJI[(f['fac'],y)]=f['last'][YEARS.index(y)]-ct
    print(f"  {'学部':<22}"+"".join(f"{y:>10}" for y in (2024,2025,2026))+f"{'Δ24→25':>10}{'Δ25→26':>10}")
    for f in RIKEI:
        v=[NIJI[(f['fac'],y)] for y in (2024,2025,2026)]
        print(f"  {f['fac']:<22}"+"".join(f"{x:>10.1f}" for x in v)+f"{v[1]-v[0]:>10.1f}{v[2]-v[1]:>10.1f}")
    for (y0,y1) in ((2024,2025),(2025,2026)):
        A=[];b=[];lab=[]
        for f in RIKEI:
            A.append([f['second'][SEC.index(k)]/RAW[k] for k in SEC])
            b.append(NIJI[(f['fac'],y1)]-NIJI[(f['fac'],y0)]); lab.append(f['fac'])
        x=solve(A,b)
        pred=[sum(A[i][j]*x[j] for j in range(4)) for i in range(len(A))]
        ss=sum((b[i]-pred[i])**2 for i in range(len(b))); mb=sum(b)/len(b)
        tot=sum((v-mb)**2 for v in b)
        print(f"\n  ── {y0}→{y1} 素点ベースの科目別難易度シフト Δm（最小二乗, n={len(A)}学部） ──")
        for k,v in zip(SEC,x): print(f"     {k:<5}{v:>+9.1f}点 / 満点{RAW[k]}   ({v/RAW[k]*100:>+6.1f}%)")
        print(f"     R² = {1-ss/tot:.3f}   残差RMS = {math.sqrt(ss/len(b)):.1f}点")
        print(f"     {'学部':<22}{'実測Δ':>9}{'予測Δ':>9}{'残差':>8}")
        for i,l in enumerate(lab):
            print(f"     {l:<22}{b[i]:>9.1f}{pred[i]:>9.1f}{b[i]-pred[i]:>8.1f}")
for t in (0.02,):
    run(t)
