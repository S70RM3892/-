# -*- coding: utf-8 -*-
"""大学入試センター公表の設問別得点状況から、
   共通のディスクリミネーション r を持つ正規オジャイブ模型を当て、
   京大工レベル(z=+2)の受験生の期待得点と『まだ落としている設問』を出す。
   r は、模型が再現する総得点SDが公表SDに一致するように較正する（自己検証つき）。"""
import math
def ndf(x): return 0.5*(1+math.erf(x/math.sqrt(2)))
def iphi(p):
    a=[-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00]
    b=[-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,6.680131188771972e+01,-1.328068155288572e+01]
    c=[-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,-2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00]
    d=[7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00]
    pl=0.02425
    if p<pl:
        q=math.sqrt(-2*math.log(p)); return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p>1-pl:
        q=math.sqrt(-2*math.log(1-p)); return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q=p-0.5; rr=q*q
    return (((((a[0]*rr+a[1])*rr+a[2])*rr+a[3])*rr+a[4])*rr+a[5])*q/(((((b[0]*rr+b[1])*rr+b[2])*rr+b[3])*rr+b[4])*rr+1)

def items(fn,subject):
    raw=open(fn,'rb').read().decode('cp932',errors='replace').splitlines()
    out=[];on=False
    for l in raw:
        f=[x.strip() for x in l.split(',')]
        if f[0].startswith('科目＝'):
            on = (f[0][3:]==subject); continue
        if not on or len(f)<6 or f[1] in('解答番号','合計') or f[0]=='大問': continue
        try: out.append((f[0],f[1],float(f[3]),float(f[4])))
        except ValueError: pass   # 数値でない行（注記など）だけを捨てる
    if not out: raise KeyError(f"{fn}: 科目『{subject}』の設問が 1 つも取れない")
    return out

# 34点ガウス求積で z~N(0,1) 上の積分
NQ=81
Z=[-5+10*i/(NQ-1) for i in range(NQ)]
W=[math.exp(-z*z/2)/math.sqrt(2*math.pi) for z in Z]
s=sum(W); W=[w/s for w in W]

def model(it,r):
    """returns (mean, sd) of total score under the model"""
    m=0.0; ev=0.0; ev2=0.0
    for z,w in zip(Z,W):
        t=0.0; v=0.0
        for _,_,mx,p in it:
            pp=ndf((iphi(min(max(p,1e-4),1-1e-4))+r*z)/math.sqrt(1-r*r))
            t+=mx*pp; v+=mx*mx*pp*(1-pp)
        ev+=w*t; ev2+=w*(t*t+v)
    return ev, math.sqrt(max(ev2-ev*ev,0))

def calib(it,target_sd):
    lo,hi=0.05,0.95
    for _ in range(60):
        mid=(lo+hi)/2
        if model(it,mid)[1]<target_sd: lo=mid
        else: hi=mid
    return (lo+hi)/2

def check_max(it,expected):
    """配点合計が公表満点と一致するか（設問のパース欠落の検出）"""
    got=sum(x[2] for x in it)
    assert abs(got-expected)<1e-6, f"配点合計 {got} != 公表満点 {expected}: 設問を取りこぼしている"

def at(it,r,z):
    return sum(mx*ndf((iphi(min(max(p,1e-4),1-1e-4))+r*z)/math.sqrt(1-r*r)) for _,_,mx,p in it)
