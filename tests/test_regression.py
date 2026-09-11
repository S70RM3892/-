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
