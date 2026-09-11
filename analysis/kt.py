import sys
def load(fn):
    raw=open(fn,'rb').read().decode('cp932',errors='replace')
    subs=[];cur=None
    for l in raw.splitlines():
        f=[x.strip() for x in l.split(',')]
        if len(f)>=8 and f[0] and f[0] not in('得点','科目名') and f[1].replace('.','').isdigit() and f[6].isdigit():
            cur={'name':f[0].replace('　',''),'max':float(f[1]),'mean':float(f[4]),'sd':float(f[5]),'n':int(f[6]),'h':[]}
            subs.append(cur)
        elif cur is not None and len(f)>=3 and f[0].isdigit() and f[1].isdigit():
            cur['h'].append((int(f[0]),int(f[1])))
    return {s['name']:s for s in subs}
def pct(s,p):  # 下からpパーセンタイルの素点
    tot=sum(c for _,c in s['h']); tgt=tot*(p/100.0); acc=0
    for sc,c in s['h']:
        acc+=c
        if acc>=tgt: return sc
    return s['max']
# 令和9年度 京大工 共通テスト換算（1素点あたりの1025点満点での価値）
K=[("国語","国語",25/200),("地歴公民(地理)","地理総合，地理探究",50/100),("地歴公民(政経)","公共，政治・経済",50/100),
   ("数学ⅠA","数学Ⅰ，数学Ａ",25/200),("数学ⅡBC","数学Ⅱ，数学Ｂ，数学Ｃ",25/200),
   ("物理","物理",25/200),("化学","化学",25/200),
   ("英語R","英語（リーディング）",25/100*1.0),("英語L","リスニング",25/100*1.0),("情報Ⅰ","情報Ⅰ",50/100)]
# 英語は200素点→50点なので 0.25/素点
K=[(a,b,(0.25 if a.startswith('英語') else c)) for a,b,c in K]
for fn,lab in [('dist_r8.csv','令和8年度'),('dist_r7.csv','令和7年度')]:
    S=load(fn)
    print(f"\n================ {lab} 本試験 ================")
    print(f"{'科目':<14}{'係数':>6}{'p50':>6}{'p80':>6}{'p90':>6}{'p95':>6}{'p99':>6}{'p90→p99素点':>12}{'京大工点':>9}")
    rows=[]
    for lab2,key,co in K:
        s=S.get(key)
        if not s: print(lab2,"なし"); continue
        v={p:pct(s,p) for p in (50,80,90,95,99)}
        d=v[99]-v[90]; g=d*co
        rows.append((lab2,co,v,d,g))
        print(f"{lab2:<14}{co:>6.3f}{v[50]:>6}{v[80]:>6}{v[90]:>6}{v[95]:>6}{v[99]:>6}{d:>12}{g:>9.1f}")
    print("\n  → 京大工1025点満点での『全国上位10%→上位1%』の価値 順位")
    for lab2,co,v,d,g in sorted(rows,key=lambda r:-r[4]):
        print(f"     {lab2:<14}{g:>6.1f}点")
