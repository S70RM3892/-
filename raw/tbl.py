import sys,re,glob,os; sys.path.insert(0,'./pylibs')
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LAParams

SUBJ=['英語','国語(理系)','数学(理系)','物理','化学','生物','地学','英数(理系)','英数(理系)理1','英数(理系)理2']

def cells(path):
    out=[]
    for page in extract_pages(path, page_numbers=[0], laparams=LAParams(char_margin=1.2, line_margin=0.3)):
        for el in page:
            if isinstance(el, LTTextContainer):
                for line in el:
                    txt=line.get_text().strip()
                    if txt:
                        out.append((round(line.y0,1), round(line.x0,1), txt))
        break
    return out

def rows(cs, tol=2.5):
    cs=sorted(cs, key=lambda c:(-c[0], c[1]))
    grouped=[]
    for y,x,t in cs:
        for g in grouped:
            if abs(g[0]-y)<=tol:
                g[1].append((x,t)); break
        else:
            grouped.append([y,[(x,t)]])
    return [(g[0],[t for _,t in sorted(g[1])]) for g in grouped]

for f in sorted(glob.glob('/root/.claude/uploads/758c6425-18f6-53b4-87c2-064c127a0125/*_0_0.pdf')):
    rs=rows(cells(f))
    lbl=[t for _,r in rs for t in r if '京大本番レベル' in t]
    print(f"\n===== {os.path.basename(f)[:12]} | {lbl[0] if lbl else '?'} =====")
    for y,r in rs:
        joined=' | '.join(r)
        if any(s in joined for s in ['英語','国語(理系)','数学(理系)','物理','化学']) and re.search(r'\d+\.\d\d', joined):
            print('  ', joined[:150])
