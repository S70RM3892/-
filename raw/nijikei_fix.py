exec(open('parse.py').read())
import math
def Phi(x): return .5*(1+math.erf(x/math.sqrt(2)))
def phi(x): return math.exp(-x*x/2)/math.sqrt(2*math.pi)
def invPhi(p):
    lo,hi=-8.,8.
    for _ in range(300):
        m=(lo+hi)/2
        if Phi(m)<p: lo=m
        else: hi=m
    return (lo+hi)/2

D={'2024':load('dist_r6.csv'),'2025':load('dist_r7.csv'),'2026':load('dist_r8.csv')}
# 概要PDFから読み取った μ,σ（画像で確認済み）
MS={'2021':{'国語':(117.51,34.67),'地理':(60.06,14.68),'英R':(58.80,21.44),'英L':(56.16,16.45)},
    '2022':{'国語':(110.26,31.94),'地理':(58.99,16.23),'英R':(61.80,20.30),'英L':(59.45,18.16)},
    '2023':{'国語':(105.74,34.10),'地理':(60.46,14.32),'英R':(53.81,20.99),'英L':(62.35,18.82)}}
KEY={'国語':['国語'],'地理':['地理総合，地理探究','地理Ｂ'],'英R':['英語（リーディング）'],'英L':['英語（リスニング）'],
     '数IA':['数学Ⅰ，数学Ａ','数学Ⅰ・数学Ａ'],'数IIBC':['数学Ⅱ，数学Ｂ，数学Ｃ','数学Ⅱ・数学Ｂ'],
     '物理':['物理'],'化学':['化学'],'情報':['情報Ⅰ']}
def sub(y,k):
    S=D.get(y)
    if S is None: return None
    return next((S[n] for n in KEY[k] if n in S),None)

def calib(k,top):
    """2024-2026の分布から、実測分位点 −(μ+zσ) の平均を較正値として返す"""
    z=invPhi(1-top); v=[]
    for y in D:
        s=sub(y,k)
        if s: v.append(pct(s,top)-(s['mean']+z*s['sd']))
    return sum(v)/len(v)

# 京大 情報学科：志願者数・合格者数
KYO={'2021':(352,88,634.45,686.87,1000),'2022':(402,89,676.50,721.63,1000),
     '2023':(408,89,697.70,739.16,1000),'2024':(363,89,623.20,676.54,1000),
     '2025':(372,89,707.52,748.86,1025),'2026':(400,99,645.49,694.29,1025)}
OLD_W={"国語":50/200,"地理":100/100,"英R":37.5/100,"英L":12.5/100}
NEW_W={'国語':25/200,'地理':50/100,'数IA':25/200,'数IIBC':25/200,'物理':25/200,'化学':25/200,
       '英R':50/200,'英L':50/200,'情報':50/100}

def ct(y,top):
    z=invPhi(1-top)
    W = NEW_W if y in ('2025','2026') else OLD_W
    tot=0; src=''
    for k,w in W.items():
        s=sub(y,k)
        if s is not None:
            q=pct(s,top); src='分布直読'
        else:
            mu,sd=MS[y][k]; q=mu+z*sd+calib(k,top); src='μσ＋較正'
        tot+=q*w
    return tot,src

def series(top,absent=0.07):
    print(f"\n===== 京大工 情報学科：二次平均の推定（京大工層＝上位{top*100:.0f}%と仮定）=====")
    print(f"  {'年度':<6}{'満点':>6}{'合格率p':>9}{'受験者σ':>9}{'受験者μ':>10}{'c_t':>8}{'二次平均':>10}{'/800':>8}  出所")
    out={}
    for y,(shigan,goukaku,L,xbar,full) in KYO.items():
        p=goukaku/(shigan*(1-absent))
        a=invPhi(1-p); lam=phi(a)/(1-Phi(a))
        sg=(xbar-L)/(lam-a); mu=L-a*sg
        c,src=ct(y,top)
        niji=mu-c
        out[y]=niji
        print(f"  {y:<6}{full:>6}{p:>9.3f}{sg:>9.1f}{mu:>10.1f}{c:>8.1f}{niji:>10.1f}{niji/800*100:>7.1f}%  {src}")
    v=list(out.values())
    print(f"\n  二次平均の幅 {min(v):.1f}〜{max(v):.1f}（{max(v)-min(v):.1f}点の変動）  平均 {sum(v)/len(v):.1f}")
    return out

for t in (0.02,):
    series(t)
