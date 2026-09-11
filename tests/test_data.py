# -*- coding: utf-8 -*-
"""データ層の不変量。p10_validate.py の中核をテストとしても固定する。"""
import json
import os

import pytest

from kyodai import datasets as ds


def test_panel_is_balanced_and_dv_consistent():
    recs, years = ds.load_panel()          # 不整合なら load_panel が例外を投げる
    assert len(recs) == 48
    assert years == list(range(2019, 2027))
    assert set(r["dep"] for r in recs) == set(ds.DEPS)


def test_scoring_adds_up():
    p = ds.load_params()
    ct = p["scoring"]["common_test"]
    ie = p["scoring"]["individual_exam"]
    assert sum(v for k, v in ct.items() if k != "total") == ct["total"] == 225
    assert sum(ie[k]["weighted"] for k in ("国語", "数学", "理科", "英語")) == 800
    assert ct["total"] + ie["total"] == p["scoring"]["total"] == 1025
    for k in ("国語", "数学", "理科", "英語"):
        assert ie[k]["raw"] * ie[k]["factor"] == pytest.approx(ie[k]["weighted"])


def test_official_cutoffs_are_newest_first():
    """kyodai_official.json の last は新しい年が先頭。

    素直に years と zip すると年が逆順になる。実際に一度踏んだバグなので
    回帰テストとして固定する。
    """
    recs, years = ds.load_panel()
    cuts = ds.official_cutoffs("工学部(情報学科)", years)
    raw = ds.official_by_faculty("工学部(情報学科)")["last"]
    assert cuts[2026] == raw[0]      # 先頭が最新年
    assert cuts[2019] == raw[-1]
    # 2025年以降は1025点満点、2024年以前は1000点満点
    assert cuts[2025] / 1025 == pytest.approx(0.6902, abs=1e-3)
    assert cuts[2024] / 1000 == pytest.approx(0.6232, abs=1e-3)


def test_official_cutoffs_rejects_wrong_length():
    with pytest.raises(ValueError):
        ds.official_cutoffs("工学部(情報学科)", [2019, 2020])


def test_dist_csv_histograms_match_published_moments():
    for fname in ("dist_r6.csv", "dist_r7.csv", "dist_r8.csv"):
        S = ds.load_dist(fname)
        assert len(S) > 30
        for name, s in S.items():
            assert sum(c for _, c in s["h"]) == s["n"], f"{fname} {name}: 人数不一致"
            m, sd = ds.dist_moments(s)
            assert m == pytest.approx(s["mean"], abs=0.05), f"{fname} {name}: 平均"
            assert sd == pytest.approx(s["sd"], abs=0.05), f"{fname} {name}: SD"


def test_dist_r8_matches_official_published_means():
    """河合塾 Kei-Net 掲載のセンター公表値との照合（2026年度本試験）。"""
    S = ds.load_dist("dist_r8.csv")
    expected = {
        "情報Ⅰ": 56.59, "数学Ⅰ，数学Ａ": 47.20, "数学Ⅱ，数学Ｂ，数学Ｃ": 54.52,
        "物理": 45.55, "化学": 56.86, "英語（リーディング）": 62.81,
        "リスニング": 54.65, "公共，政治・経済": 63.59,
    }
    for k, v in expected.items():
        assert S[k]["mean"] == pytest.approx(v, abs=0.01), k


def test_item_points_sum_to_full_marks():
    for subj in ("情報Ⅰ", "物理", "化学", "数学Ⅰ，数学Ａ",
                 "公共，政治・経済", "英語（リーディング）", "英語（リスニング）"):
        it = ds.load_items(subj)
        assert sum(m for _, _, m, _ in it) == pytest.approx(100.0), subj
        assert all(0.0 <= p <= 1.0 for _, _, _, p in it), subj


def test_math_iibc_choice_structure():
    """必答52 + 選択4問×16。組合せを取る前に足すと100を超える。"""
    it = ds.load_items("数学Ⅱ，数学Ｂ，数学Ｃ")
    agg = {}
    for d, _, m, _ in it:
        agg[d] = agg.get(d, 0.0) + m
    assert sum(agg[k] for k in ("1", "2", "3")) == pytest.approx(52.0)
    assert all(agg[k] == pytest.approx(16.0) for k in ("4", "5", "6", "7"))
    assert sum(agg.values()) == pytest.approx(116.0)


def test_disclosure_contamination_is_detected():
    """kaiji2.json no=133 は5段階評価が得点として混入した行。

    これを『得点』として集計に入れると二次の平均が壊れる。
    検出ロジックが生きていることを固定する。
    """
    rows = json.load(open(os.path.join(ds.DATA, "kaiji2.json"), encoding="utf-8"))
    bad = [r for r in rows if r.get("no") == 133][0]
    vals = [bad[k] for k in ("国語", "数学", "理科", "英語")]
    assert max(vals) <= 10        # 明らかに得点ではない


def test_user_params_are_labelled():
    """公開情報から決まらないパラメータが USER と明示されていること。"""
    p = ds.load_params()
    assert p["ladder"]["mu_candidate_pt"]["status"] == "USER"
    assert p["ladder"]["sigma_performance_pt"]["status"] == "USER"
    assert p["study_cost"]["status"] == "USER"
    assert p["common_test_level"]["anchor_rate"]["status"] == "PUBLISHED"
    assert "_url" in p["common_test_level"]["anchor_rate"]
