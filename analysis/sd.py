import json,itertools,math,random
D=json.load(open('dep.json'))
deps=["情報","物理工","電電","建築","地球工","理工化"]
yrs=sorted(set(d['y'] for d in D))
R={(d['dep'],d['y']):d for d in D}

# 1. cutoff order per year
print("=== 年ごとの最低点順位（dv=年平均からの乖離, 得点率pt） ===")
for y in yrs:
    o=sorted(deps,key=lambda p:-R[(p,y)]['dv'])
    print(y, " > ".join(f"{p}{R[(p,y)]['dv']:+.2f}" for p in o))

print()
print("=== 志願倍率順位 ===")
for y in yrs:
    o=sorted(deps,key=lambda p:-R[(p,y)]['ratio'])
    print(y, " > ".join(f"{p}{R[(p,y)]['ratio']:.2f}" for p in o))
