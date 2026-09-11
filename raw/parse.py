import re,math
def load(fn):
    raw=open(fn,'rb').read()
    for enc in ('cp932','utf-8-sig','euc-jp'):
        try: t=raw.decode(enc); break
        except Exception: pass
    subs={}; cur=None
    for l in t.splitlines():
        f=[x.strip() for x in l.split(',')]
        if len(f)>6 and f[1].isdigit() and re.match(r'^[\d.]+$',f[4] or 'x'):
            try:
                cur={'max':int(f[1]),'mean':float(f[4]),'sd':float(f[5]),'n':int(f[6]),'d':[]}
                subs[f[0].replace('　','')]=cur; continue
            except Exception: pass
        if cur is not None and len(f)>2 and re.match(r'^\d+$',f[0]) and re.match(r'^\d+$',f[1]):
            cur['d'].append((int(f[0]),int(f[1])))
    return subs
def pct(s,top):
    tot=sum(c for _,c in s['d']); need=tot*top; acc=0
    for sc,c in sorted(s['d'],reverse=True):
        acc+=c
        if acc>=need: return float(sc)
    return 0.0
def trunc_stats(s,top):
    """上位top割合だけを取り出したときの平均と標準偏差（実測）"""
    tot=sum(c for _,c in s['d']); need=tot*top
    acc=0; pts=[]
    for sc,c in sorted(s['d'],reverse=True):
        if acc>=need: break
        take=min(c,need-acc)
        if take<=0: continue          # 人数0の点数は飛ばす（break してはいけない）
        pts.append((sc,take)); acc+=take
    N=sum(w for _,w in pts)
    m=sum(sc*w for sc,w in pts)/N
    v=sum(w*(sc-m)**2 for sc,w in pts)/N
    return m,math.sqrt(v)
