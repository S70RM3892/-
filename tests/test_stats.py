# -*- coding: utf-8 -*-
"""統計ユーティリティの単体テスト。旧版にはテストが1本も無かった。"""
import math

import pytest

from kyodai import stats


def test_cdf_known_values():
    assert stats.cdf(0.0) == pytest.approx(0.5)
    assert stats.cdf(1.0) == pytest.approx(0.8413447, abs=1e-6)
    assert stats.cdf(2.0) == pytest.approx(0.9772499, abs=1e-6)
    assert stats.cdf(-3.0) == pytest.approx(0.0013499, abs=1e-6)


def test_inv_cdf_round_trip():
    for p in (0.001, 0.01, 0.02, 0.1, 0.5, 0.9, 0.977, 0.999):
        assert stats.cdf(stats.inv_cdf(p)) == pytest.approx(p, abs=2e-7)


def test_inv_cdf_rejects_out_of_range():
    for bad in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ValueError):
            stats.inv_cdf(bad)


def test_pdf_integrates_to_one():
    n, lo, hi = 20001, -10.0, 10.0
    h = (hi - lo) / (n - 1)
    total = sum(stats.pdf(lo + i * h) for i in range(n)) * h
    assert total == pytest.approx(1.0, abs=1e-6)


def test_ols_recovers_line():
    xs = list(range(10))
    ys = [3.0 + 2.5 * x for x in xs]
    a, b = stats.ols(xs, ys)
    assert a == pytest.approx(3.0)
    assert b == pytest.approx(2.5)


def test_detrend_removes_linear_trend():
    ys = [1.0 + 0.5 * i for i in range(8)]
    assert all(abs(r) < 1e-9 for r in stats.detrend(ys))


def test_corr_bounds():
    xs = [1, 2, 3, 4, 5]
    assert stats.corr(xs, xs) == pytest.approx(1.0)
    assert stats.corr(xs, [-x for x in xs]) == pytest.approx(-1.0)


def test_two_way_demean_kills_both_effects():
    rows, cols = ["a", "b", "c"], [1, 2, 3, 4]
    row_fx = {"a": 1.0, "b": -2.0, "c": 0.5}
    col_fx = {1: 0.3, 2: -1.1, 3: 2.0, 4: 0.0}
    v = {(r, c): 7.0 + row_fx[r] + col_fx[c] for r in rows for c in cols}
    w = stats.two_way_demean(v, rows, cols)
    assert all(abs(x) < 1e-9 for x in w.values())


def test_order_statistic_sd_monotone_in_pool_sd():
    a = stats.order_statistic_sd(6.0, 90, 388)
    b = stats.order_statistic_sd(8.0, 90, 388)
    assert b > a
    assert b / a == pytest.approx(8.0 / 6.0)


def test_permutation_p_never_zero():
    """p=0 を報告しないための +1/+1 補正が効いていること。"""
    p = stats.permutation_p(1e9, lambda rng: rng.gauss(0, 1), n=100, seed=1)
    assert 0 < p <= 1
