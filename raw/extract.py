import re,html,glob,os,json
SUB={'国語':100,'数学':200,'理科':200,'英語':150,'外国語':150}
def posts():
    for f in sorted(glob.glob('anc/*.html'), key=lambda x:int(os.path.basename(x)[:-5])):
        n=int(os.path.basename(f)[:-5])
        try: s=open(f,'rb').read().decode('cp932',errors='replace')
        except: continue
        t=re.sub(r'<script[\s\S]*?</script>','',s); t=re.sub(r'<[^>]+>','\n',t); t=html.unescape(t)
        L=[re.sub(r'[ \t]+',' ',x).strip() for x in t.split('\n') if x.strip()]
        idx=[k for k,x in enumerate(L) if x==str(n)]
        if not idx: continue
        i=idx[-1]
        date=L[i+2] if i+2<len(L) else ''
        yield n, date, '\n'.join(L[i:i+32])

rows=[]
for n,date,b in posts():
    d={}
    for m in re.finditer(r'(国語|数学|理科|英語|外国語)\s*[　: ]*(?:\d+(?:\.\d+)?\s*[（(])?(\d+(?:\.\d+)?)\s*[/／]\s*(\d+)', b):
        k,v,mx=m.group(1),float(m.group(2)),int(m.group(3))
        k='英語' if k=='外国語' else k
        if SUB.get(k)==mx: d[k]=v
    if len(d)<4: continue
    fac=re.search(r'(工学部|理学部|医学部|農学部|薬学部|総合人間|経済学部|法学部|文学部|教育学部)', b)
    res='合格' if re.search(r'(?<!不)合格', b.replace('合格最低','').replace('合格者平均','')) else ''
    if '不合格' in b or '落ち' in b: res='不合格'
    yr=re.match(r'(\d{4})/', date)
    rows.append(dict(res_no=n, year=int(yr.group(1)) if yr else None,
                     faculty=fac.group(1) if fac else '?', result=res or '?', **d))
json.dump(rows, open('kaiji_rows.json','w'), ensure_ascii=False)
print(f"抽出 {len(rows)} 件（理系4科目そろい）")
print(f"  {'#':>4}{'年':>6}{'学部':>8}{'合否':>7}{'国語':>7}{'数学':>7}{'理科':>7}{'英語':>7}")
for r in rows:
    print(f"  {r['res_no']:>4}{r['year'] or 0:>6}{r['faculty']:>8}{r['result']:>7}"
          f"{r['国語']:>7.0f}{r['数学']:>7.0f}{r['理科']:>7.0f}{r['英語']:>7.0f}")
