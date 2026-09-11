import sys,re; sys.path.insert(0,'./pylibs')
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LAParams
def rows(path,page=0,tol=3.0):
    out=[]
    for pg in extract_pages(path,page_numbers=[page],laparams=LAParams(char_margin=1.5,line_margin=0.25,word_margin=0.1)):
        cells=[]
        for el in pg:
            if isinstance(el,LTTextContainer):
                for ln in el:
                    t=ln.get_text().strip()
                    if t: cells.append((round(ln.y0,1),round(ln.x0,1),t))
        cells.sort(key=lambda c:(-c[0],c[1]))
        g=[]
        for y,x,t in cells:
            for r in g:
                if abs(r[0]-y)<=tol: r[1].append((x,t)); break
            else: g.append([y,[(x,t)]])
        out=[(y,[t for _,t in sorted(v)]) for y,v in g]
        break
    return out
if __name__=="__main__":
    p=sys.argv[1]; pg=int(sys.argv[2]) if len(sys.argv)>2 else 0
    for y,r in rows(p,pg): print(f"{y:7.1f}  "+" | ".join(r))
