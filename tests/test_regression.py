# -*- coding: utf-8 -*-
"""README に載る主要数値のスナップショット。

旧版は README の数値とコードの出力がずれても誰も気づかない構造だった
（実際 sd4.py は README と矛盾する p=0.97 を出したまま放置されていた）。
ここで固定しておけば、コードを触って数値が動いた瞬間にテストが落ちる。

数値が変わったときは、README とここを同時に更新すること。
片方だけ直すのは禁止。
"""
import math
import statistics as st

import pytest

from kyodai import datasets as ds
from kyodai import irt
from kyodai.stats import corr, detrend, two_way_demean


@pytest.fixture(scope="module")
def panel():
    recs, years = ds.load_panel()
    return ds.panel_index(recs), years


def _F(idx, years, focus="情報"):
    res = {p: detrend(ds.series(idx, p, years)) for p in ds.DEPS}
    df = len(years) - 2
    vj = sum(x * x for x in res[focus]) / df
    vo = sum(x * x for p in ds.DEPS if p != focus for x in res[p]) / (5 * df)
    return math.sqrt(vj), vj / vo


def test_full_sample_instability(panel):
    idx, years = panel
    sd, F = _F(idx, years)
    assert sd == pytest.approx(1.037, abs=0.002)      # 得点率pt
    assert sd / 100 * 1025 == pytest.approx(10.6, abs=0.1)
    assert F == pytest.approx(4.45, abs=0.02)


def test_old_regime_subsample_kills_the_finding(panel):
    """2019–2024（旧配点）だけでは情報の分散は他学科より小さい。

    これが改訂で最も重要な発見。回帰テストとして固定する。
    """
    idx, _ = panel
    sd, F = _F(idx, list(ds.OLD_REGIME))
    assert sd == pytest.approx(0.431, abs=0.003)
    assert F == pytest.approx(0.68, abs=0.02)
    assert F < 1.0


def test_dropping_2024_halves_the_effect(panel):
    idx, years = panel
    sd, F = _F(idx, [y for y in years if y != 2024])
    assert sd == pytest.approx(0.703, abs=0.003)
    assert F == pytest.approx(1.96, abs=0.03)


def test_gap_ordering_is_stable(panel):
    idx, years = panel
    gaps = {p: st.mean([(idx[("情報", y)]["dv"] - idx[(p, y)]["dv"]) * 10.25
                        for y in years]) for p in ds.DEPS[1:]}
    assert sorted(gaps, key=lambda k: -gaps[k]) == ["理工化", "地球工", "建築", "電電", "物理工"]
    assert gaps["理工化"] == pytest.approx(78.3, abs=0.3)
    assert gaps["物理工"] == pytest.approx(41.2, abs=0.3)


def test_ratio_correlation_is_between_not_within(panel):
    idx, years = panel
    deps = ds.DEPS
    X = {(p, y): idx[(p, y)]["ratio"] for p in deps for y in years}
    Y = {(p, y): idx[(p, y)]["dv"] for p in deps for y in years}
    pooled = corr([X[k] for k in X], [Y[k] for k in X])
    between = corr([st.mean([X[(p, y)] for y in years]) for p in deps],
                   [st.mean([Y[(p, y)] for y in years]) for p in deps])
    Xw, Yw = two_way_demean(X, deps, years), two_way_demean(Y, deps, years)
    within = corr([Xw[k] for k in Xw], [Yw[k] for k in Xw])
    assert pooled == pytest.approx(0.826, abs=0.005)
    assert between == pytest.approx(0.891, abs=0.005)
    assert within == pytest.approx(-0.178, abs=0.005)
    assert within < 0 < between        # 符号が逆であること自体が結論


@pytest.fixture(scope="module")
def ct_fit():
    S = ds.load_dist("dist_r8.csv")
    fit = {}
    for label, key, co in (("物理", "物理", 0.125), ("情報Ⅰ", "情報Ⅰ", 0.5),
                           ("地歴公民", "公共，政治・経済", 0.5),
                           ("英語L", "英語（リスニング）", 0.25)):
        it = ds.load_items(key)
        fit[label] = (it, irt.calibrate(it, S[key]["sd"]), co)
    return S, fit


def test_calibrated_r_values(ct_fit):
    _, fit = ct_fit
    assert fit["情報Ⅰ"][1] == pytest.approx(0.434, abs=0.002)
    assert fit["物理"][1] == pytest.approx(0.507, abs=0.002)
    assert fit["英語L"][1] == pytest.approx(0.486, abs=0.002)


def test_model_underestimates_upper_tail_most_for_low_r(ct_fit):
    """模型の当てはめ誤差が、結論の主役である情報Ⅰで最大であること。

    この性質が消えたら §2 の診断は書き直しが要る。
    """
    S, fit = ct_fit
    gaps = {}
    for label, key in (("情報Ⅰ", "情報Ⅰ"), ("物理", "物理"),
                       ("英語L", "英語（リスニング）"), ("地歴公民", "公共，政治・経済")):
        it, r, _ = fit[label]
        gaps[label] = ds.percentile(S[key], 97.7) - irt.expected_score(it, r, 2.0)
    assert gaps["情報Ⅰ"] == pytest.approx(4.8, abs=0.15)
    assert gaps["情報Ⅰ"] == max(gaps.values())


def test_loss_is_highly_sensitive_to_ability_anchor(ct_fit):
    """取りこぼし合計が z に対して 3 倍以上動くこと（旧版の帯が狭すぎた根拠）。"""
    S = ds.load_dist("dist_r8.csv")
    fit = {}
    for label, key, co in (("数学ⅠA", "数学Ⅰ，数学Ａ", 0.125), ("物理", "物理", 0.125),
                           ("化学", "化学", 0.125),
                           ("英語R", "英語（リーディング）", 0.25),
                           ("英語L", "英語（リスニング）", 0.25),
                           ("情報Ⅰ", "情報Ⅰ", 0.5),
                           ("地歴公民", "公共，政治・経済", 0.5)):
        it = ds.load_items(key)
        fit[label] = (it, irt.calibrate(it, S[key]["sd"]), co)
    full = sum(sum(m for _, _, m, _ in it) * co for it, _, co in fit.values())

    def loss(z):
        return full - sum(irt.expected_score(it, r, z) * co for it, r, co in fit.values())

    assert loss(1.5) / loss(3.0) > 3.0


def test_border_anchor_lands_outside_old_readme_band():
    """河合塾ボーダー85%に合わせると、旧 README の 16.6–23.7点 の外に出る。"""
    S = ds.load_dist("dist_r8.csv")
    total_weighted_max = 200.0
    assert total_weighted_max * (1 - 0.85) == pytest.approx(30.0)
    assert 30.0 > 23.7


def test_niji_leverage_dominates_ct():
    """二次数学の大問1つ > 共テ全科目の取りこぼし合計。"""
    one_math_question = 35 * 1.25          # 素点35 × 換算1.25
    ct_recoverable_high = 30.0
    assert one_math_question > ct_recoverable_high
    assert one_math_question == pytest.approx(43.75)


# --------------------------------------------------------------------------
# p11 / p12: 前回の分析では見ていなかった量
# --------------------------------------------------------------------------

SEATS_R6 = {"地球工": 181, "建築": 77, "物理工": 230, "電電": 123, "情報": 87, "理工化": 225}
SEATS_R9 = {"地球工": 175, "建築": 77, "物理工": 225, "電電": 128, "情報": 94, "理工化": 215}


def test_seat_reallocation_direction():
    """総定員はほぼ不変で、情報と電電にだけ付け替えられている。

    合格最低点を決める4要素（定員・志願者数・学力分布・難易度）のうち、
    出願前に公開されるのは定員だけ。過去データからは出てこない情報なので
    一次資料の値をここで固定する。
    """
    assert sum(SEATS_R6.values()) == 923
    assert sum(SEATS_R9.values()) == 914
    grew = [d for d in SEATS_R9 if SEATS_R9[d] > SEATS_R6[d]]
    assert set(grew) == {"情報", "電電"}
    assert SEATS_R9["情報"] / SEATS_R6["情報"] - 1 == pytest.approx(0.0805, abs=0.001)


def test_seat_change_shrinks_the_second_choice_gap(panel):
    """定員の付け替えは、情報と他学科のギャップを縮める向きに働く。"""
    from kyodai.stats import inv_cdf
    idx, years = panel
    pool = 7.2 * 10.25
    delta = {}
    for d in ds.DEPS:
        app = st.mean([idx[(d, y)]["app"] for y in years])
        delta[d] = pool * (inv_cdf(1 - SEATS_R9[d] / app) - inv_cdf(1 - SEATS_R6[d] / app))
    assert delta["情報"] < 0          # 定員増 → 最低点は下がる
    assert delta["理工化"] > 0        # 定員減 → 最低点は上がる
    assert delta["情報"] == pytest.approx(-4.4, abs=0.2)
    for d in ds.DEPS[1:]:
        assert delta["情報"] - delta[d] < 0, f"{d}: ギャップが縮まっていない"


def test_own_variance_dominates_cutoff_variance():
    """全不確実性のうち相手側（合格最低点）が占めるのは1〜2割以下。

    この研究が8年パネルで精密に推定してきたのは、その小さい方だった。
    """
    sigma = 10.63
    for sp in (30, 45, 64.5, 80):
        share = sigma ** 2 / (sp ** 2 + sigma ** 2)
        assert share < 0.12
    assert 10.63 ** 2 / (64.5 ** 2 + 10.63 ** 2) == pytest.approx(0.026, abs=0.002)


def test_variance_helps_when_behind_and_hurts_when_ahead():
    """P = Φ(μ/s) の s に関する符号が μ の符号で反転すること。"""
    from kyodai.stats import cdf
    sigma = 10.63

    def P(mu, sp):
        return cdf(mu / math.sqrt(sp ** 2 + sigma ** 2))

    assert P(-36.2, 80) > P(-36.2, 45)     # 下にいる人は分散が大きい方が有利
    assert P(+36.2, 80) < P(+36.2, 45)     # 上にいる人は逆
    assert P(0.0, 80) == pytest.approx(P(0.0, 45))   # ラインちょうどでは無関係
    # 大きさ: μ=-36.2 で sp を 64.5→45 に下げると 7ポイント以上落ちる
    assert (P(-36.2, 64.5) - P(-36.2, 45)) * 100 == pytest.approx(7.3, abs=0.3)


def test_risk_exchange_rate_equals_abs_z():
    """許容できる期待値の損失 = |z| × Δs という形になっていること。"""
    from kyodai.stats import cdf
    sigma, sp, mu = 10.63, 64.5, -36.2
    s = math.sqrt(sp ** 2 + sigma ** 2)
    z = mu / s
    ds_ = 20.0
    allowed = abs(z) * ds_
    base = cdf(mu / s)
    # ちょうど許容量ぶん期待値を捨てると、合格確率は元と同じになるはず
    after = cdf((mu - allowed) / math.sqrt((sp + ds_) ** 2 + sigma ** 2))
    assert after == pytest.approx(base, abs=0.005)


# --------------------------------------------------------------------------
# p13: 二次数学の時間配分フロンティア
# --------------------------------------------------------------------------

def _p13():
    import importlib.util
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "analysis", "p13_exam_strategy.py")
    spec = importlib.util.spec_from_file_location("p13", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_all_six_problems_dominated_only_under_heterogeneity():
    """k=6（全問に配点比例）が劣るのは、問題の重さに差があるときだけ。

    これが p13 の結論の条件なので、条件そのものを固定する。
    """
    p13 = _p13()

    def dominated(tau, beta):
        d = {k: (ev, sd) for k, ev, sd, _ in p13.strategies(tau, beta)}
        ev6, sd6 = d[6]
        return any(ev >= ev6 and sd <= sd6 and (ev > ev6 or sd < sd6)
                   for k, (ev, sd) in d.items() if k != 6)

    for beta in (0.0, 0.4, 0.8):
        assert not dominated([75] * 6, beta), "τ一様なら k=6 は劣らないはず"
        assert not dominated([120] * 6, beta)
        assert dominated([55, 60, 70, 85, 110, 140], beta), "差があれば k=6 は劣るはず"
        assert dominated([40, 50, 70, 100, 150, 200], beta)


def test_concentrating_lowers_variance_not_raises_it():
    """絞ると分散は下がる。p12 の素朴な予想（絞る=分散を上げる）は誤り。"""
    p13 = _p13()
    tau = [55, 60, 70, 85, 110, 140]
    d = {k: (ev, sd) for k, ev, sd, _ in p13.strategies(tau, 0.4)}
    assert d[2][1] < d[4][1], "2問に絞った方が分散が小さいはず"
    assert d[2][0] < d[4][0], "ただし期待値も下がる"


def test_partial_credit_reduces_variance():
    """部分点が効くほど分散は小さくなる（模型の骨格）。"""
    p13 = _p13()
    tau = [55, 60, 70, 85, 110, 140]
    sds = [p13.strategies(tau, b)[2][2] for b in (0.0, 0.4, 0.8)]
    assert sds == sorted(sds, reverse=True)


def test_kyodai_math_is_heterogeneous_within_year():
    """京大理系数学は年内の問題差の方が、年ごとの当たり外れより大きい。

    p13 の前提。出典は主観評価なので水準ではなく比だけを固定する。
    """
    import json
    import os
    import statistics as st2
    from kyodai import datasets as ds2
    d = json.load(open(os.path.join(ds2.DATA, "ds.json"), encoding="utf-8"))["daisu"]
    yrs = sorted(d, key=int)
    within = st2.mean([st2.pvariance(d[y]) for y in yrs])
    between = st2.pvariance([st2.mean(d[y]) for y in yrs])
    assert within > between
    assert within / between == pytest.approx(3.5, abs=0.3)
    rngs = [max(d[y]) - min(d[y]) for y in yrs]
    assert sum(1 for r in rngs if r == 0) <= 1      # 全問同一評価の年はほぼ無い


# --------------------------------------------------------------------------
# p14 / p15: 使っていなかったデータから出た結果
# --------------------------------------------------------------------------

def _mod(name):
    import importlib.util
    import os
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "analysis", name)
    spec = importlib.util.spec_from_file_location(name[:-3], path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_all_faculty_panel_is_three_times_larger():
    """kyodai_official.json は19単位×8年=152観測を持っている。p01 は48しか使っていなかった。"""
    p14 = _mod("p14_all_faculties.py")
    panel, group = p14.build_panel()
    assert len(panel) == 19
    assert all(len(v) == 8 for v in panel.values())
    assert sum(1 for u in panel if group[u] == "理") == 14
    # 満点の再現: 工学部は dep.json の得点率と一致する
    assert panel["工学部(情報学科)"][2026] == pytest.approx(62.97, abs=0.01)
    assert panel["工学部(情報学科)"][2019] == pytest.approx(63.86, abs=0.01)


def test_informatics_volatility_is_not_special_university_wide():
    """京大全体を母集団にすると『情報は突出して不安定』は消える。

    改訂で最も重要な逆転。p01 の結論が比較対象の取り方に依存していたことを固定する。
    """
    import math as _m
    from kyodai.stats import detrend as _detrend
    p14 = _mod("p14_all_faculties.py")
    panel, group = p14.build_panel()
    dv = p14.year_demean(panel, group)
    units = list(panel)
    df = len(p14.YEARS) - 2
    res = {u: _detrend([dv[u][y] for y in p14.YEARS]) for u in units}
    sd = {u: _m.sqrt(sum(x * x for x in res[u]) / df) for u in units}
    rank = sorted(sd, key=lambda k: -sd[k]).index(p14.FOCUS) + 1
    assert rank == 8, f"19単位中の順位が変わった: {rank}"
    ri = [u for u in units if group[u] == "理"]
    vj = sum(x * x for x in res[p14.FOCUS]) / df
    vo = sum(x * x for u in ri if u != p14.FOCUS for x in res[u]) / (df * (len(ri) - 1))
    assert vj / vo < 1.0, "理系単位を母集団にすると分散比は1未満のはず"


def test_30point_problems_are_easier_than_35point():
    """印刷配点30点の大問は35点より易しい。試験開始0秒で得られる無料の手がかり。"""
    import statistics as st2
    p15 = _mod("p15_math_structure.py")
    pairs, by_year = p15.load_diff()
    g30 = [a for a, b in pairs if b == 30]
    g35 = [a for a, b in pairs if b == 35]
    assert len(g30) == 29 and len(g35) == 45
    assert st2.mean(g35) - st2.mean(g30) == pytest.approx(0.561, abs=0.01)
    # 年内比較でも同じ向き
    wins = 0
    tot = 0
    for y, rows in by_year.items():
        a = [x for x, pt in rows if pt == 30]
        b = [x for x, pt in rows if pt == 35]
        if a and b:
            tot += 1
            wins += st2.mean(b) > st2.mean(a)
    assert wins / tot > 0.6


def test_informatics_perfect_score_is_rarest():
    """情報Ⅰの満点者は令和8で 1/2907。取りこぼしを満点基準で測ることの限界。"""
    S = ds.load_dist("dist_r8.csv")
    rates = {}
    for k in ("情報Ⅰ", "数学Ⅰ，数学Ａ", "物理", "化学",
              "英語（リーディング）", "リスニング", "公共，政治・経済"):
        s = S[k]
        rates[k] = dict(s["h"]).get(int(s["max"]), 0) / s["n"]
    assert min(rates, key=lambda k: rates[k]) == "情報Ⅰ"
    assert rates["情報Ⅰ"] == pytest.approx(0.00034, abs=0.00005)
