import math
exec(open('kt.py').read().split('# 令和9年度')[0])
K=[("国語","国語",0.125),("地歴公民(地理)","地理総合，地理探究",0.5),("地歴公民(政経)","公共，政治・経済",0.5),
   ("数学ⅠA","数学Ⅰ，数学Ａ",0.125),("数学ⅡBC","数学Ⅱ，数学Ｂ，数学Ｃ",0.125),
   ("物理","物理",0.125),("化学","化学",0.125),
   ("英語R","英語（リーディング）",0.25),("英語L","リスニング",0.25),("情報Ⅰ","情報Ⅰ",0.5)]
CORE=["国語","地歴公民(政経)","数学ⅠA","数学ⅡBC","物理","化学","英語R","英語L","情報Ⅰ"]
for fn,lab in [('dist_r8.csv','令和8年度'),('dist_r7.csv','令和7年度')]:
    S=load(fn)
    print(f"\n===== {lab}：全国上位10%層に限ったときのばらつき（京大工1025点換算）=====")
    print(f"{'科目':<14}{'京大配点':>8}{'上位10%内の素点SD':>18}{'→京大工点SD':>12}{'分散シェア':>10}")
    out=[]
    for l2,key,co in K:
        if l2 not in CORE: continue
        s=S[key]; thr=pct(s,90)
        h=[(sc,c) for sc,c in s['h'] if sc>=thr]
        n=sum(c for _,c in h); m=sum(sc*c for sc,c in h)/n
        sd=math.sqrt(sum((sc-m)**2*c for sc,c in h)/n)
        out.append((l2,co,sd,sd*co))
    tv=sum(x[3]**2 for x in out)
    haiten={"国語":25,"地歴公民(政経)":50,"数学ⅠA":12.5,"数学ⅡBC":12.5,"物理":12.5,"化学":12.5,"英語R":25,"英語L":25,"情報Ⅰ":50}
    for l2,co,sd,g in out:
        print(f"{l2:<14}{haiten[l2]:>8.1f}{sd:>18.2f}{g:>12.2f}{g*g/tv*100:>9.1f}%")
    print(f"{'合計':<14}{sum(haiten.values()):>8.1f}{'':>18}{math.sqrt(tv):>12.2f}{100.0:>9.1f}%")
    a=sum(g*g for l2,co,sd,g in out if l2 in("情報Ⅰ","地歴公民(政経)"))
    b=sum(g*g for l2,co,sd,g in out if l2 in("数学ⅠA","数学ⅡBC","物理","化学"))
    print(f"  情報Ⅰ+地歴公民 の分散シェア = {a/tv*100:.1f}%   （配点シェア {100/225*100:.1f}%）")
    print(f"  数学ⅠA+ⅡBC+物理+化学 の分散シェア = {b/tv*100:.1f}%   （配点シェア {50/225*100:.1f}%）")
