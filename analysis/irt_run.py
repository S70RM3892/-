# -*- coding: utf-8 -*-
import math,itertools  # 設問別得点状況から項目反応模型を較正し、京大工レベルの取りこぼしを設問単位で出す
exec(open('irt.py',encoding='utf-8').read())
exec(open('kt.py',encoding='utf-8').read().split('# 令和9年度')[0])
S=load('dist_r8.csv')
def sel(it,keep): return [x for x in it if x[0] in keep]
# 数学ⅡBC: 第1-3問必答(52点) + 第4-7問から3問選択(16x3=48点)
base=items('../data/q_r8.csv','数学Ⅱ，数学Ｂ，数学Ｃ')
combos=[('1','2','3')+c for c in itertools.combinations(('4','5','6','7'),3)]
SPEC=[('数学Ⅰ，数学Ａ','数学Ⅰ，数学Ａ',None,0.125),
      ('数学ⅡBC','数学Ⅱ，数学Ｂ，数学Ｃ',combos,0.125),
      ('物理','物理',None,0.125),('化学','化学',None,0.125),
      ('英語（リーディング）','英語（リーディング）',None,0.25),
      ('英語（リスニング）','英語（リスニング）',None,0.25),
      ('情報Ⅰ','情報Ⅰ',None,0.5),('公共，政治・経済','公共，政治・経済',None,0.5)]
print(f"{'科目':<16}{'満点':>5}{'較正r':>7}{'公表SD':>7}{'平均(模型/公表)':>16}{'p90':>11}{'p97.7':>11}")
FIT={}
for lab,key,cmb,co in SPEC:
    s=S[key]
    if cmb:
        # 4通りの選択パターンで較正し中央値をとる
        res=[]
        for c in cmb:
            it=sel(base,set(c)); r=calib(it,s['sd']); res.append((at(it,r,2.0),it,r,model(it,r)))
        res.sort(key=lambda t:t[0]); e2,it,r,(m,sd)=res[len(res)//2]
    else:
        it=items('../data/q_r8.csv',key); check_max(it,s['max'])
        r=calib(it,s['sd']); m,sd=model(it,r)
    FIT[lab]=(it,r,co)
    mx=sum(x[2] for x in it)
    print(f"{lab:<16}{mx:>5.0f}{r:>7.3f}{s['sd']:>7.2f}{m:>8.1f}/{s['mean']:>7.2f}"
          f"{at(it,r,1.2816):>6.1f}/{pct(s,90):>4}{at(it,r,2.0):>6.1f}/{pct(s,97.7):>4}")

print("\n=== 京大工レベル(z=+2.0 ≒ 全国上位2.3%)で まだ落としている点 ===")
print(f"{'科目':<16}{'満点':>5}{'期待素点':>9}{'取りこぼし':>10}{'係数':>6}{'京大工点':>9}")
rows=[(l,sum(x[2] for x in it),at(it,r,2.0),co) for l,(it,r,co) in FIT.items()]
tot=0
for l,mx,e,co in sorted(rows,key=lambda x:-(x[1]-x[2])*x[3]):
    g=(mx-e)*co; tot+=g
    print(f"{l:<16}{mx:>5.0f}{e:>9.1f}{mx-e:>10.1f}{co:>6.3f}{g:>9.1f}")
print(f"{'合計':<16}{'':>5}{'':>9}{'':>10}{'':>6}{tot:>9.1f}")
a=sum((mx-e)*co for l,mx,e,co in rows if l in('情報Ⅰ','公共，政治・経済'))
b=sum((mx-e)*co for l,mx,e,co in rows if l in('数学Ⅰ，数学Ａ','数学ⅡBC','物理','化学'))
print(f"  情報Ⅰ+地歴公民 = {a:.1f}点 ({a/tot*100:.0f}%)   理系4科目 = {b:.1f}点 ({b/tot*100:.0f}%)")

print("\n=== 情報Ⅰ：z=+2でも落とす期待値が大きい設問 上位10 ===")
it,r,co=FIT['情報Ⅰ']
L=sorted(((mx*(1-ndf((iphi(p)+r*2.0)/math.sqrt(1-r*r))),d,q,mx,p) for d,q,mx,p in it),reverse=True)
print(f"{'大問':>4}{'解答':>8}{'配点':>5}{'全国得点率':>10}{'z=+2得点率':>11}{'期待失点':>9}{'京大工点':>9}")
for loss,d,q,mx,p in L[:10]:
    print(f"{d:>4}{q:>8}{mx:>5.0f}{p:>10.3f}{ndf((iphi(p)+r*2.0)/math.sqrt(1-r*r)):>11.3f}{loss:>9.2f}{loss*co:>9.2f}")
print(f"  上位10設問だけで 情報Ⅰの取りこぼしの {sum(x[0] for x in L[:10])/sum(x[0] for x in L)*100:.0f}%")

print("\n=== 大問別: z=+2 の期待失点（京大工点換算）===")
for lab in ['情報Ⅰ','公共，政治・経済','物理','化学','数学Ⅰ，数学Ａ']:
    it,r,co=FIT[lab]; d={}
    for dd,q,mx,p in it:
        d.setdefault(dd,[0,0])
        d[dd][0]+=mx*(1-ndf((iphi(p)+r*2.0)/math.sqrt(1-r*r))); d[dd][1]+=mx
    tl=sum(v[0] for v in d.values())
    print(f"  {lab:<14}"+"  ".join(f"第{k}問 {v[0]*co:.2f}点({v[0]/tl*100:.0f}%)" for k,v in sorted(d.items())))

print("\n=== 集計の二重確認: 模型 vs 公表分位点（どちらも全科目で全国上位2.3%相当を基準）===")
print(f"{'科目':<16}{'模型z=+2':>9}{'実測p97.7':>10}{'係数':>6}{'模型':>7}{'実測':>7}")
t1=t2=0
for l,(it,r,co) in FIT.items():
    key={'数学ⅡBC':'数学Ⅱ，数学Ｂ，数学Ｃ'}.get(l,l); s=S[key]
    mx=sum(x[2] for x in it); e=at(it,r,2.0); o=pct(s,97.7)
    if l=='数学ⅡBC': o=min(o,100)
    g1=(mx-e)*co; g2=(100-o)*co; t1+=g1; t2+=g2
    print(f"{l:<16}{e:>9.1f}{o:>10}{co:>6.3f}{g1:>7.1f}{g2:>7.1f}")
print(f"{'合計':<16}{'':>9}{'':>10}{'':>6}{t1:>7.1f}{t2:>7.1f}")
print("\n※ この 2 列は独立した 2 手法ではない。左は総得点SDに、右は実質的に上位裾に")
print("  合わせた同じ模型。単一 r ではSDと裾を同時に再現できないので左が上振れする。")
print("  上位 2.3% の議論に使うなら裾で較正した側（右, 16.6点）が中心値。rb.py 7. 参照。")
