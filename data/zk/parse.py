import re,html,json,glob,os
def lines(p):
    s=open(p,encoding='utf-8',errors='replace').read()
    s=re.sub(r'<script.*?</script>','',s,flags=re.S);s=re.sub(r'<style.*?</style>','',s,flags=re.S)
    t=html.unescape(re.sub('<[^>]+>','\n',s)).replace('　',' ')
    return [l.strip() for l in t.split('\n') if l.strip()]

PAT=re.compile(r'^第\s*([０-９0-9一二三四五六七八九Ⅰ-Ⅴ]+)\s*問\s*[：:]\s*(.+?)\s*[［\[]\s*([^］\]]+?)\s*[］\]]\s*$')
Z2A=str.maketrans('０１２３４５６７８９','0123456789')
KAN={'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
def num(x):
    x=x.translate(Z2A)
    if x.isdigit():return int(x)
    return KAN.get(x,0)

out=[]
for p in sorted(glob.glob('*-20*.html')):
    sub,yr=os.path.basename(p)[:-5].rsplit('-',1)
    for l in lines(p):
        m=PAT.match(l)
        if m: out.append({"subject":sub,"year":int(yr),"q":num(m.group(1)),
                          "field":m.group(2).strip(),"diff":m.group(3).strip()})
json.dump(out,open('qdb.json','w'),ensure_ascii=False,indent=1)
from collections import Counter
print('rows',len(out))
print(Counter((r['subject'],r['year']) for r in out))
