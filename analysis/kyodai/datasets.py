# -*- coding: utf-8 -*-
"""データの読み込みと、読み込み時点での最低限の検証。

パスはリポジトリルートからの相対で解決するので、どの作業ディレクトリから
呼んでも動く（旧版は analysis/ から起動しないと ../data/ を見失った）。
"""
from __future__ import annotations

import csv
import json
import math
import os
import statistics as st
from typing import Dict, List, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ANALYSIS = os.path.dirname(HERE)
ROOT = os.path.dirname(ANALYSIS)
DATA = os.path.join(ROOT, "data")
OUTPUTS = os.path.join(ROOT, "outputs")

DEPS = ["情報", "物理工", "電電", "建築", "地球工", "理工化"]

# 令和7年度入試（2025年2月）から共通テストの配点構成そのものが変わった。
# 旧: 共テ200点（国50/地公100/外R37.5/外L12.5、数学と理科は共テ0点）＋二次800点 = 1000点
# 新: 共テ225点（国25/地公50/数25/理25/外R25/外L25/情報50）＋二次800点 = 1025点
# 得点率に直しても「中身が違う合成量」であることは消えないので、
# この年をまたいだプールは既定では行わない。
REGIME_BREAK_YEAR = 2025
OLD_REGIME = tuple(range(2019, 2025))   # 2019–2024
NEW_REGIME = (2025, 2026)


# --------------------------------------------------------------- 学科パネル
def load_panel(path: str | None = None) -> Tuple[List[dict], List[int]]:
    """dep.json を読み、(レコード列, 年の昇順リスト) を返す。

    レコードの意味:
      dep   学科名
      y     入試年（2026 = 2026年2月実施）
      rate  合格最低点の得点率（%）。2024年以前は1000点満点、2025年以降は1025点満点。
      app   志願者数, acc  合格者数, ratio 志願倍率
      dv    その年の6学科平均得点率からの乖離（pt）。年効果を除いた量。
    """
    path = path or os.path.join(ANALYSIS, "dep.json")
    with open(path, encoding="utf-8") as fh:
        recs = json.load(fh)
    years = sorted({r["y"] for r in recs})
    _check_panel(recs, years)
    return recs, years


def _check_panel(recs: Sequence[dict], years: Sequence[int]) -> None:
    if len(recs) != len(DEPS) * len(years):
        raise ValueError(f"パネルが不完全: {len(recs)} 件 (期待 {len(DEPS)*len(years)})")
    by_year: Dict[int, List[dict]] = {}
    for r in recs:
        by_year.setdefault(r["y"], []).append(r)
    for y, rows in by_year.items():
        m = st.mean([r["rate"] for r in rows])
        for r in rows:
            if abs((r["rate"] - m) - r["dv"]) > 1e-6:
                raise ValueError(f"dv が rate の年内乖離と一致しない: {r['dep']} {y}")


def panel_index(recs: Sequence[dict]) -> Dict[Tuple[str, int], dict]:
    return {(r["dep"], r["y"]): r for r in recs}


def series(idx: Dict[Tuple[str, int], dict], dep: str, years: Sequence[int],
           key: str = "dv") -> List[float]:
    return [idx[(dep, y)][key] for y in years]


# ------------------------------------------------- 共通テスト 科目別成績分布
def load_dist(fname: str) -> Dict[str, dict]:
    """大学入試センター公表の科目別成績分布 CSV を読む。

    返り値は科目名 -> {max, mean, sd, n, h(=[(素点, 人数), ...])}。
    ファイルは cp932。行の形が2種類（科目ヘッダ行と度数行）混在している。
    """
    path = fname if os.path.isabs(fname) else os.path.join(ANALYSIS, fname)
    with open(path, "rb") as fh:
        raw = fh.read().decode("cp932", errors="replace")
    subs: List[dict] = []
    cur = None
    for line in raw.splitlines():
        f = [x.strip() for x in line.split(",")]
        if (len(f) >= 8 and f[0] and f[0] not in ("得点", "科目名")
                and f[1].replace(".", "").isdigit() and f[6].isdigit()):
            cur = {"name": f[0].replace("　", ""), "max": float(f[1]),
                   "mean": float(f[4]), "sd": float(f[5]), "n": int(f[6]), "h": []}
            subs.append(cur)
        elif cur is not None and len(f) >= 3 and f[0].isdigit() and f[1].isdigit():
            cur["h"].append((int(f[0]), int(f[1])))
    out = {s["name"]: s for s in subs}
    if not out:
        raise ValueError(f"{path}: 科目を1つも読めなかった（文字コードか書式の変更を疑う）")
    return out


def percentile(s: dict, p: float) -> int:
    """下から p パーセンタイルにあたる素点。度数分布から直接取る。"""
    tot = sum(c for _, c in s["h"])
    tgt = tot * (p / 100.0)
    acc = 0
    for sc, c in s["h"]:
        acc += c
        if acc >= tgt:
            return sc
    return int(s["max"])


def dist_moments(s: dict) -> Tuple[float, float]:
    """度数分布から平均と SD を再計算する（公表値との照合用）。"""
    n = sum(c for _, c in s["h"])
    m = sum(sc * c for sc, c in s["h"]) / n
    v = sum((sc - m) ** 2 * c for sc, c in s["h"]) / n
    return m, math.sqrt(v)


# ------------------------------------------------------------ 設問別得点状況
def load_items(subject: str, path: str | None = None) -> List[Tuple[str, str, float, float]]:
    """設問別得点状況から (大問, 解答番号, 配点, 全国得点率) の列を返す。"""
    path = path or os.path.join(DATA, "q_r8.csv")
    with open(path, "rb") as fh:
        lines = fh.read().decode("cp932", errors="replace").splitlines()
    out: List[Tuple[str, str, float, float]] = []
    on = False
    for line in lines:
        f = [x.strip() for x in line.split(",")]
        if f[0].startswith("科目＝"):
            on = (f[0][3:] == subject)
            continue
        if not on or len(f) < 6 or f[1] in ("解答番号", "合計") or f[0] == "大問":
            continue
        try:
            out.append((f[0], f[1], float(f[3]), float(f[4])))
        except ValueError:
            pass
    if not out:
        raise ValueError(f"設問データが空: 科目={subject}")
    return out


# ----------------------------------------------------------------- 京大公式
def load_official(path: str | None = None) -> List[dict]:
    """学部別の配点と、8年分の合格最低点（実点）。"""
    path = path or os.path.join(DATA, "kyodai_official.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def official_by_faculty(name: str) -> dict:
    for r in load_official():
        if r["fac"] == name:
            return r
    raise KeyError(name)


def official_cutoffs(fac: str, years: Sequence[int]) -> Dict[int, float]:
    """学部・学科の合格最低点（実点）を {年: 点} で返す。

    kyodai_official.json の "last" は **新しい年が先頭** に入っている。
    素直に years と zip すると年がひっくり返る（実際に一度やった）。
    ここで並べ替えたうえで、dep.json の得点率と突き合わせて検証する。
    """
    rec = official_by_faculty(fac)
    last = rec["last"]
    if len(last) != len(years):
        raise ValueError(f"{fac}: last が {len(last)} 件、years が {len(years)} 件")
    out = {y: v for y, v in zip(sorted(years, reverse=True), last)}

    dep = {"工学部(地球工学科)": "地球工", "工学部(建築学科)": "建築",
           "工学部(物理工学科)": "物理工", "工学部(電気電子工学科)": "電電",
           "工学部(情報学科)": "情報", "工学部(理工化学科(旧工化))": "理工化"}.get(fac)
    if dep:
        recs, yrs = load_panel()
        idx = panel_index(recs)
        for y in years:
            denom = 1025 if y >= REGIME_BREAK_YEAR else 1000
            expected = idx[(dep, y)]["rate"] / 100 * denom
            if abs(expected - out[y]) > 0.6:
                raise ValueError(
                    f"{fac} {y}: kyodai_official の {out[y]:.2f} と "
                    f"dep.json 由来の {expected:.2f} が一致しない（並び順を疑う）")
    return out


# ------------------------------------------------------------- パラメータ
def load_params(path: str | None = None) -> dict:
    """params.json。出典が確定していない値は status で区別される。"""
    path = path or os.path.join(ANALYSIS, "params.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def param(params: dict, dotted: str):
    """'ladder.sigma_candidate.value' のようなキーで取り出す。"""
    node = params
    for part in dotted.split("."):
        node = node[part]
    return node
