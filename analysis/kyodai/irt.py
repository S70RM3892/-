# -*- coding: utf-8 -*-
"""設問別得点状況に当てる正規オジャイブ模型。

模型
----
潜在能力 z ~ N(0,1)。設問 j の配点 m_j、全国得点率 p_j に対し

    P_j(z) = Phi( ( Phi^{-1}(p_j) + r * z ) / sqrt(1 - r^2) )

全設問で共通のディスクリミネーション r をひとつだけ持つ。r は
「模型が再現する総得点 SD が公表 SD に一致する」ように較正する。

旧版からの変更点
----------------
1. 局所独立の緩和。設問を素点のまま独立に扱うと、同一大問内の強い相関を
   無視することになる。`total_moments`/`calibrate` に rho（同一大問内の
   残差相関）を渡せるようにした。rho>0 だと公表SDに合わせる r が小さくなり、
   上位層の期待得点が下がる＝取りこぼしは保守側（大きめ）に出る。
   大問をまるごと1項目に束ねる `to_testlets` も残してあるが、これは
   大問内の難易度のばらつきまで潰してしまうので、感度分析の主役にはしない。
2. 較正 r を外から固定できるようにした（`fixed_r`）。取りこぼしの科目順位が
   r の低さの artifact でないかを確かめるため。
3. 能力水準 z を外から決め打ちせず、目標得点率から解けるようにした
   （`solve_z_for_score`）。
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence, Tuple

from .stats import cdf, inv_cdf

Item = Tuple[str, str, float, float]   # (大問, 解答番号, 配点, 全国得点率)

# z ~ N(0,1) 上のガウス求積（等間隔＋密度重み）。
_NQ = 81
_Z = [-5 + 10 * i / (_NQ - 1) for i in range(_NQ)]
_W0 = [math.exp(-z * z / 2) / math.sqrt(2 * math.pi) for z in _Z]
_SW = sum(_W0)
_W = [w / _SW for w in _W0]

_EPS = 1e-4


def _clip(p: float) -> float:
    return min(max(p, _EPS), 1 - _EPS)


def prob(p: float, r: float, z: float) -> float:
    """全国得点率 p の設問を、能力 z の受験者が取る期待得点率。"""
    if r <= 0:
        return _clip(p)
    return cdf((inv_cdf(_clip(p)) + r * z) / math.sqrt(1 - r * r))


def expected_score(items: Sequence[Item], r: float, z: float) -> float:
    """能力 z における期待素点。"""
    return sum(m * prob(p, r, z) for _, _, m, p in items)


def total_moments(items: Sequence[Item], r: float, rho: float = 0.0) -> Tuple[float, float]:
    """模型が含意する総得点の (平均, SD)。

    SD は「能力による分散」＋「能力を固定したときの残差分散」の和。

    rho は同一大問内の設問間に残す残差相関。rho=0 が局所独立（旧版の仮定）。
    同じ大問の設問は同じ図表・同じ設定を共有するので、能力を固定しても
    残差は正に相関する。その分だけ条件付き分散が増え、公表SDに合わせるための
    r は小さくなる（= 得点と学力の連動を弱く見積もる = 保守側）。

        V(z) = Σ_d [ Σ_{j∈d} m_j^2 q_j + rho * Σ_{j≠k∈d} m_j m_k sqrt(q_j q_k) ]
        ただし q_j = p_j(z) (1 - p_j(z))
    """
    if not 0.0 <= rho < 1.0:
        raise ValueError("rho は [0,1) でなければならない")
    groups: Dict[str, List[int]] = {}
    for i, (d, _, _, _) in enumerate(items):
        groups.setdefault(d, []).append(i)

    ev = ev2 = 0.0
    for z, w in zip(_Z, _W):
        pp = [prob(p, r, z) for _, _, _, p in items]
        t = sum(m * q for (_, _, m, _), q in zip(items, pp))
        v = 0.0
        for idxs in groups.values():
            s_sd = 0.0
            for i in idxs:
                m = items[i][2]
                q = pp[i] * (1 - pp[i])
                v += m * m * q
                s_sd += m * math.sqrt(q)
            if rho > 0:
                # Σ_{j≠k} m_j m_k sqrt(q_j q_k) = (Σ m_j sqrt(q_j))^2 − Σ m_j^2 q_j
                own = sum(items[i][2] ** 2 * pp[i] * (1 - pp[i]) for i in idxs)
                v += rho * (s_sd * s_sd - own)
        ev += w * t
        ev2 += w * (t * t + v)
    return ev, math.sqrt(max(ev2 - ev * ev, 0.0))


def calibrate(items: Sequence[Item], target_sd: float, rho: float = 0.0,
              lo: float = 0.01, hi: float = 0.98, iters: int = 80) -> float:
    """総得点 SD が target_sd に一致する r を二分法で求める。

    SD は r について単調増加なので二分法でよい。到達不能なら端点を返す
    （その場合は呼び出し側で「較正が飽和した」と分かるよう端点のまま返す）。
    """
    if total_moments(items, hi, rho)[1] < target_sd:
        return hi
    if total_moments(items, lo, rho)[1] > target_sd:
        return lo
    for _ in range(iters):
        mid = (lo + hi) / 2
        if total_moments(items, mid, rho)[1] < target_sd:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def to_testlets(items: Sequence[Item]) -> List[Item]:
    """大問ごとに束ねて1設問とみなす（局所独立の緩和）。

    大問の配点は合計、得点率は配点加重平均。同一大問内の設問間相関を
    「完全相関」と置くので、素点独立版と挟み撃ちにできる。
    """
    agg: Dict[str, List[float]] = {}
    for d, _, m, p in items:
        cell = agg.setdefault(d, [0.0, 0.0])
        cell[0] += m
        cell[1] += m * p
    return [(d, "大問", tot, sc / tot) for d, (tot, sc) in sorted(agg.items())]


def solve_z_for_score(items_by_subject: Dict[str, Tuple[Sequence[Item], float, float]],
                      target_rate: float, lo: float = -1.0, hi: float = 5.0,
                      iters: int = 80) -> float:
    """複数科目をまとめた京大工換算得点率が target_rate になる z を解く。

    items_by_subject: 科目 -> (設問列, 較正r, 京大工換算係数)
    target_rate: 0–1（例 0.85）。満点は係数×満点の総和。
    """
    full = sum(sum(m for _, _, m, _ in it) * co for it, _, co in items_by_subject.values())

    def rate(z: float) -> float:
        got = sum(expected_score(it, r, z) * co for it, r, co in items_by_subject.values())
        return got / full

    if rate(hi) < target_rate:
        return hi
    if rate(lo) > target_rate:
        return lo
    for _ in range(iters):
        mid = (lo + hi) / 2
        if rate(mid) < target_rate:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def item_losses(items: Sequence[Item], r: float, z: float) -> List[Tuple[float, Item, float]]:
    """(期待失点, 設問, z での期待得点率) を失点の大きい順に。"""
    out = []
    for it in items:
        _, _, m, p = it
        pz = prob(p, r, z)
        out.append((m * (1 - pz), it, pz))
    out.sort(key=lambda t: -t[0])
    return out
