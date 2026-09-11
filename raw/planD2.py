exec(open('parse.py').read())
import json,math
REC=json.load(open('kyodai_official.json')); YEARS=[2026,2025,2024,2023,2022,2021,2020,2019]
D={2024:load('dist_r6.csv'),2025:load('dist_r7.csv'),2026:load('dist_r8.csv')}
CT_SUB={'国語':(['国語'],200),'社会':(['地理総合，地理探究','地理Ｂ'],100),
 '数学':(['数学Ⅰ，数学Ａ','数学Ⅰ・数学Ａ'],100,['数学Ⅱ，数学Ｂ，数学Ｃ','数学Ⅱ・数学Ｂ'],100),
 '理科':(['物理'],100,['化学'],100),'英R':(['英語（リーディング）'],100),
 '英L':(['英語（リスニング）'],100),'情報':(['情報Ⅰ'],100)}
ORDER=['国語','社会','数学','理科','英R','英L','情報']
SEC=['国語','数学','理科','外国語']; RAW={'国語':100,'数学':200,'理科':200,'外国語':150}
TEIIN={'総合人間学部(理)':45,'教育学部(理)':10,'経済学部(理)':25,'理学部':306,'医学部(医学科)':102,
 '医学部(人間健康学科)':100,'薬学部':78,'工学部(地球工学科)':185,'工学部(建築学科)':80,
 '工学部(物理工学科)':235,'工学部(電気電子工学科)':130,'工学部(情報学科)':90,
 '工学部(理工化学科(旧工化))':230,'農学部':300}
def q(y,n): 
    S=D[y]; s=next((S[x] for x in n if x in S),None); return pct(s,0.02) if s else None
def ratio(y):
    r={}
    for k,v in CT_SUB.items():
        if len(v)==2: a=q(y,v[0]); r[k]=None if a is None else a/v[1]
        else:
            a=q(y,v[0]); b=q(y,v[2]); r[k]=None if(a is None or b is None) else (a+b)/(v[1]+v[3])
    return r
NIJI={}
for y in (2024,2025,2026):
    r=ratio(y); wk='center' if y<2025 else 'c25'
    for f in REC:
        if f['fac'] in TEIIN:
            NIJI[(f['fac'],y)]=f['last'][YEARS.index(y)]-sum(f[wk][i]*r[ORDER[i]] for i in range(7) if f[wk][i])
def wls(A,b,w,cols,ridge=0.0):
    n=len(cols)
    M=[[sum(w[i]*A[i][r]*A[i][c] for i in range(len(A)))+(ridge if r==c else 0) for c in range(n)]
        +[sum(w[i]*A[i][r]*b[i] for i in range(len(A)))] for r in range(n)]
    for i in range(n):
        p=max(range(i,n),key=lambda k:abs(M[k][i])); M[i],M[p]=M[p],M[i]
        for k in range(n):
            if k!=i and M[i][i]: 
                f=M[k][i]/M[i][i]
                for j in range(i,n+1): M[k][j]-=f*M[i][j]
    return [M[i][n]/M[i][i] for i in range(n)]
def build(y0,y1,cols):
    A=[];b=[];w=[];lab=[]
    for f in REC:
        if f['fac'] not in TEIIN: continue
        A.append([f['second'][SEC.index(k)]/RAW[k] for k in cols])
        b.append(NIJI[(f['fac'],y1)]-NIJI[(f['fac'],y0)])
        w.append(TEIIN[f['fac']]); lab.append(f['fac'])
    return A,b,w,lab
for (y0,y1) in ((2024,2025),(2025,2026)):
    for cols,tag in ((SEC,'4科目'),(['数学','理科','外国語'],'国語=0固定・3科目')):
        A,b,w,lab=build(y0,y1,cols)
        x=wls(A,b,w,cols)
        print(f"\n■ {y0}→{y1}  {tag}  定員ウェイト付き最小二乗")
        print("   "+"  ".join(f"{k} {v:+7.1f}" for k,v in zip(cols,x)))
        # jackknife: 1学部ずつ除外
        J={k:[] for k in cols}
        for d in range(len(A)):
            AA=[A[i] for i in range(len(A)) if i!=d]; bb=[b[i] for i in range(len(A)) if i!=d]
            ww=[w[i] for i in range(len(A)) if i!=d]
            xx=wls(AA,bb,ww,cols)
            for k,v in zip(cols,xx): J[k].append((lab[d],v))
        print(f"   {'科目':<6}{'全体':>9}{'JK最小':>10}{'JK最大':>10}{'振れ幅':>9}   最大の影響を持つ学部")
        for k,v in zip(cols,x):
            vals=[t[1] for t in J[k]]
            worst=max(J[k],key=lambda t:abs(t[1]-v))
            print(f"   {k:<6}{v:>+9.1f}{min(vals):>+10.1f}{max(vals):>+10.1f}{max(vals)-min(vals):>9.1f}   {worst[0]} ({worst[1]:+.1f})")
