# -*- coding: utf-8 -*-
"""項目反応模型のテスト。"""
import math

import pytest

from kyodai import irt

ITEMS = [("1", "ア", 4.0, 0.3), ("1", "イ", 3.0, 0.5),
         ("2", "ウ", 5.0, 0.7), ("2", "エ", 2.0, 0.9)]


def test_marginal_probability_equals_national_rate():
    """模型の要:  z ~ N(0,1) で平均を取ると全国得点率 p に戻る。

    z=0 での値は p と一致しない（リンクが非線形なので当然）。一致すべきなのは
    母集団平均の方で、公表されている『全国得点率』はまさにそれ。
    この不変量が壊れると較正の意味が失われる。
    """
    for r in (0.2, 0.434, 0.7):
        for _, _, _, p in ITEMS:
            marginal = sum(w * irt.prob(p, r, z) for z, w in zip(irt._Z, irt._W))
            assert marginal == pytest.approx(p, abs=1e-4)


def test_prob_at_zero_is_not_p_when_r_positive():
    """上の裏返し。z=0 と p を取り違えないための明示的な回帰テスト。"""
    assert irt.prob(0.3, 0.5, 0.0) != pytest.approx(0.3, abs=1e-3)


def test_prob_monotone_in_ability():
    vals = [irt.prob(0.3, 0.5, z) for z in (-2, -1, 0, 1, 2)]
    assert vals == sorted(vals)


def test_expected_score_bounded_by_max():
    mx = sum(m for _, _, m, _ in ITEMS)
    assert 0 < irt.expected_score(ITEMS, 0.5, 3.0) < mx


def test_total_moments_mean_matches_items_at_r_small():
    m, sd = irt.total_moments(ITEMS, 0.05)
    naive = sum(mm * p for _, _, mm, p in ITEMS)
    assert m == pytest.approx(naive, abs=0.05)
    assert sd > 0


def test_sd_increases_with_r():
    sds = [irt.total_moments(ITEMS, r)[1] for r in (0.1, 0.3, 0.5, 0.7)]
    assert sds == sorted(sds)


def test_rho_increases_conditional_variance():
    """同一大問内の残差相関を入れると総得点SDは増える。"""
    base = irt.total_moments(ITEMS, 0.4, rho=0.0)[1]
    corr = irt.total_moments(ITEMS, 0.4, rho=0.3)[1]
    assert corr > base


def test_calibrate_hits_target_sd():
    target = irt.total_moments(ITEMS, 0.42)[1]
    r = irt.calibrate(ITEMS, target)
    assert r == pytest.approx(0.42, abs=1e-3)


def test_calibrate_with_rho_gives_smaller_r():
    """同じ公表SDに合わせるなら、残差相関を認めた方が r は小さくなる。"""
    target = irt.total_moments(ITEMS, 0.5, rho=0.0)[1]
    r0 = irt.calibrate(ITEMS, target, rho=0.0)
    r1 = irt.calibrate(ITEMS, target, rho=0.25)
    assert r1 < r0


def test_rho_out_of_range_rejected():
    for bad in (-0.1, 1.0, 1.5):
        with pytest.raises(ValueError):
            irt.total_moments(ITEMS, 0.4, rho=bad)


def test_to_testlets_preserves_total_points():
    t = irt.to_testlets(ITEMS)
    assert sum(m for _, _, m, _ in t) == pytest.approx(sum(m for _, _, m, _ in ITEMS))
    assert len(t) == 2


def test_solve_z_for_score_round_trip():
    fit = {"s": (ITEMS, 0.5, 1.0)}
    full = sum(m for _, _, m, _ in ITEMS)
    z = irt.solve_z_for_score(fit, 0.8)
    assert irt.expected_score(ITEMS, 0.5, z) / full == pytest.approx(0.8, abs=1e-3)


def test_item_losses_sorted_descending():
    L = irt.item_losses(ITEMS, 0.5, 1.5)
    assert [x[0] for x in L] == sorted([x[0] for x in L], reverse=True)
