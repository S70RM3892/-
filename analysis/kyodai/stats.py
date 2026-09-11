# -*- coding: utf-8 -*-
"""標準ライブラリだけで済ませる統計ユーティリティ。

旧 sd2.py / irt.py に重複していた正規分布の実装をここに一本化した。
"""
from __future__ import annotations

import math
import random
import statistics as st
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

SQRT2PI = math.sqrt(2 * math.pi)


# ---------------------------------------------------------------- 正規分布
def pdf(x: float) -> float:
    """標準正規の密度。"""
    return math.exp(-x * x / 2) / SQRT2PI


def cdf(x: float) -> float:
    """標準正規の累積分布。math.erf 経由なので倍精度いっぱいまで正確。"""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# Acklam の逆正規近似（相対誤差 ~1.15e-9）。
_A = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
      1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
_B = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
      6.680131188771972e+01, -1.328068155288572e+01]
_C = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
      -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
_D = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
      3.754408661907416e+00]
_PLOW = 0.02425


def inv_cdf(p: float) -> float:
    """標準正規の分位点関数。0<p<1。"""
    if not 0.0 < p < 1.0:
        raise ValueError(f"inv_cdf: p は (0,1) でなければならない: {p}")
    if p < _PLOW:
        q = math.sqrt(-2 * math.log(p))
        return ((((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5])
                / ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1))
    if p > 1 - _PLOW:
        q = math.sqrt(-2 * math.log(1 - p))
        return -((((((_C[0] * q + _C[1]) * q + _C[2]) * q + _C[3]) * q + _C[4]) * q + _C[5])
                 / ((((_D[0] * q + _D[1]) * q + _D[2]) * q + _D[3]) * q + 1))
    q = p - 0.5
    r = q * q
    return ((((((_A[0] * r + _A[1]) * r + _A[2]) * r + _A[3]) * r + _A[4]) * r + _A[5]) * q
            / (((((_B[0] * r + _B[1]) * r + _B[2]) * r + _B[3]) * r + _B[4]) * r + 1))


# ------------------------------------------------------------------ 回帰
def ols(xs: Sequence[float], ys: Sequence[float]) -> Tuple[float, float]:
    """単回帰 y = a + b x を返す（a, b）。"""
    if len(xs) != len(ys) or len(xs) < 2:
        raise ValueError("ols: 長さが合わないか標本が足りない")
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        raise ValueError("ols: x に分散がない")
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return my - b * mx, b


def detrend(ys: Sequence[float]) -> List[float]:
    """時間トレンド（等間隔）を除いた残差。"""
    xs = list(range(len(ys)))
    a, b = ols(xs, ys)
    return [y - (a + b * x) for x, y in zip(xs, ys)]


def demean(ys: Sequence[float]) -> List[float]:
    m = st.mean(ys)
    return [y - m for y in ys]


def corr(xs: Sequence[float], ys: Sequence[float]) -> float:
    mx, my = st.mean(xs), st.mean(ys)
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den = math.sqrt(sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys))
    if den == 0:
        return float("nan")
    return num / den


def two_way_demean(v: Dict[Tuple[str, int], float], rows: Sequence[str],
                   cols: Sequence[int], iters: int = 200) -> Dict[Tuple[str, int], float]:
    """二元固定効果（行・列）を交互に除去する。バランスドパネルなら収束する。"""
    w = dict(v)
    for _ in range(iters):
        for c in cols:
            m = st.mean([w[(r, c)] for r in rows])
            for r in rows:
                w[(r, c)] -= m
        for r in rows:
            m = st.mean([w[(r, c)] for c in cols])
            for c in cols:
                w[(r, c)] -= m
    return w


# ---------------------------------------------------------- 並べ替え検定
def permutation_p(observed: float, draw: Callable[[random.Random], float],
                  n: int = 200_000, seed: int = 0, tail: str = "greater") -> float:
    """`draw` が返す帰無統計量の分布で observed の片側 p を出す。

    tail="greater" なら P(T >= observed)、"less" なら P(T <= observed)。
    """
    rng = random.Random(seed)
    hit = 0
    for _ in range(n):
        t = draw(rng)
        if (tail == "greater" and t >= observed) or (tail == "less" and t <= observed):
            hit += 1
    # +1/+1 補正。並べ替え検定で p=0 を報告しないための標準的な処理。
    return (hit + 1) / (n + 1)


def order_statistic_sd(pool_sd: float, seats: float, applicants: float) -> float:
    """合格者数 `seats` / 志願者数 `applicants` のとき、
    合格最低点（= 上から seats 番目の順序統計量）の標本変動 SD。

    得点が SD=pool_sd の正規分布に従う仮定での漸近式:
        SD = pool_sd * sqrt(p(1-p)/n) / phi(z_p)
    """
    p = seats / applicants
    if not 0.0 < p < 1.0:
        raise ValueError("order_statistic_sd: 合格率が (0,1) にない")
    z = inv_cdf(1 - p)
    return pool_sd * math.sqrt(p * (1 - p) / applicants) / pdf(z)


# ------------------------------------------------------------------ 表示
def fmt_band(lo: float, hi: float, unit: str = "", digits: int = 1) -> str:
    """帯を「a–b 単位」で。単一値に見せない。"""
    return f"{lo:.{digits}f}–{hi:.{digits}f}{unit}"


def rule(char: str = "-", width: int = 78) -> str:
    return char * width


def header(title: str) -> str:
    return f"\n{rule('=')}\n{title}\n{rule('=')}"
