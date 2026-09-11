import math

# 2026 工学部 情報学科の共テ換算構造
# (科目, 全国σ(素点), κ)  ※σは近年の公表値のおおよその水準
subj = [
 ("国語",        35, 25/200),
 ("地歴公民",    18, 50/100),
 ("数学IA+IIBC", 33, 25/200),
 ("理科2科目",   33, 25/200),
 ("外国語R+L",   33, 50/200),
 ("情報I",       20, 50/100),
]

print("=== 感度: z_k が 1.0 ずれたとき換算点が何点動くか ===")
tot=0
for n,s,k in subj:
    sens = s*k
    tot += sens
    print(f"  {n:<12} σ={s:>3}  κ={k:.3f}  感度={sens:>5.2f} 点/z")
print(f"  {'合計':<12}                       {tot:>5.2f} 点/z")
print(f"  → z が共通に ±0.2 ずれると c_t は ±{tot*0.2:.1f} 点")

# 高κ3科目の寄与
hi = sum(s*k for n,s,k in subj if k>=0.25)
print(f"  → うち 地歴・外国語・情報I の3科目で {hi:.1f} 点 ({hi/tot*100:.0f}%)")

print()
print("=== 京大工受験層内での換算点のばらつき σ_ct ===")
# 上位約30%に切断された正規分布の内部SDは元の約0.55倍
trunc = 0.55
v=0
for n,s,k in subj:
    sd = s*trunc*k
    v += sd*sd
    print(f"  {n:<12} 層内σ(換算) = {sd:>5.2f}")
sd_indep = math.sqrt(v)
sd_ct = sd_indep*1.25   # 科目間の正の相関を粗く反映
print(f"  独立合成 {sd_indep:.1f} → 相関考慮 σ_ct ≈ {sd_ct:.1f}")

print()
print("=== 合格者切断による c_t の上振れ（系統バイアス）===")
def Phi(x): return 0.5*(1+math.erf(x/math.sqrt(2)))
def phi(x): return math.exp(-x*x/2)/math.sqrt(2*math.pi)
def inv(p):
    lo,hi=-8,8
    for _ in range(200):
        m=(lo+hi)/2
        if Phi(m)<p: lo=m
        else: hi=m
    return (lo+hi)/2

sd_ni = 68.0
for rho_ni in (0.25,0.35,0.45):
    cov = sd_ct**2 + rho_ni*sd_ct*sd_ni
    sd_tot = math.sqrt(sd_ct**2 + sd_ni**2 + 2*rho_ni*sd_ct*sd_ni)
    rho_tot = cov/(sd_ct*sd_tot)
    for p in (0.30,0.35,0.40):
        a = inv(1-p); lam = phi(a)/(1-Phi(a))
        shift = rho_tot*sd_ct*lam
        if rho_ni==0.35 and p==0.35:
            print(f"  ρ(二次,共テ)={rho_ni}  合格率={p}  →  σ_total={sd_tot:.1f}  ρ(共テ,総点)={rho_tot:.2f}  上振れ={shift:.1f}点  ★基準")
        else:
            print(f"  ρ(二次,共テ)={rho_ni}  合格率={p}  →  上振れ={shift:.1f}点")

print()
print("=== 分散寄与 ===")
rho_ni=0.35
sd_tot = math.sqrt(sd_ct**2 + sd_ni**2 + 2*rho_ni*sd_ct*sd_ni)
print(f"  Var(共テ)/Var(総点) = {sd_ct**2/sd_tot**2*100:.1f}%")
print(f"  σ_total = {sd_tot:.1f} (予備校集計から逆算した ~72 と整合)")
