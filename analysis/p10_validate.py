# -*- coding: utf-8 -*-
"""データ検証。壊れた入力に気づかないまま結論を出さないための関門。

旧版はデータ検証を一切持っていなかった。その結果:
  * kaiji2.json に5段階評価の行（国語5/数学6/理科7/英語5）が得点として混入していた
  * kyodai_official.json の "last" が新しい年から並んでいることがどこにも書かれておらず、
    素直に zip すると年が逆順になる（実際にこの改訂作業中に踏んだ）
  * README の「工学部分が11件」は全学部合計との取り違えだった

exit code は、致命的な不整合があれば 1。run_all.sh がここで止まる。
"""
from __future__ import annotations

import json
import math
import os
import statistics as st
import sys

from kyodai import datasets as ds
from kyodai.stats import header

FAIL: list[str] = []
WARN: list[str] = []


def ok(cond, msg, fatal=True):
    if cond:
        print(f"  [OK]   {msg}")
    else:
        print(f"  [{'FAIL' if fatal else 'WARN'}] {msg}")
        (FAIL if fatal else WARN).append(msg)


def main() -> None:
    params = ds.load_params()

    print(header("1. 配点の検算"))
    sc = params["scoring"]
    ct = sum(v for k, v in sc["common_test"].items() if k != "total")
    ok(ct == sc["common_test"]["total"] == 225, f"共テ配点の縦計 = {ct} (期待 225)")
    ie = sc["individual_exam"]
    w = sum(ie[k]["weighted"] for k in ("国語", "数学", "理科", "英語"))
    raw = sum(ie[k]["raw"] for k in ("国語", "数学", "理科", "英語"))
    ok(abs(w - 800) < 1e-9, f"二次換算計 = {w:g} (期待 800)")
    ok(raw == ie["raw_total"] == 650, f"二次素点計 = {raw} (期待 650)")
    ok(sc["common_test"]["total"] + ie["total"] == sc["total"] == 1025,
       f"総計 = {sc['common_test']['total'] + ie['total']} (期待 1025)")
    for k in ("国語", "数学", "理科", "英語"):
        e = ie[k]["raw"] * ie[k]["factor"]
        ok(abs(e - ie[k]["weighted"]) < 1e-6,
           f"二次 {k}: {ie[k]['raw']} × {ie[k]['factor']:.4f} = {e:.2f}")

    print(header("2. 学科パネル（dep.json）"))
    recs, years = ds.load_panel()   # load_panel 自体が dv の整合を検証する
    ok(True, f"48観測・dv = 年内乖離 の整合を確認（{len(recs)}件, {min(years)}–{max(years)}）")
    idx = ds.panel_index(recs)
    for p in ds.DEPS:
        for y in years:
            r = idx[(p, y)]
            ok(abs(r["ratio"] - r["app"] / r["acc"]) < 1e-6,
               f"{p} {y}: 倍率 {r['ratio']:.4f} = {r['app']}/{r['acc']}", fatal=False)

    print(header("3. 合格最低点（kyodai_official.json）の並び順"))
    for fac in ("工学部(情報学科)", "工学部(地球工学科)", "工学部(理工化学科(旧工化))"):
        try:
            ds.official_cutoffs(fac, years)
            ok(True, f"{fac}: last は新しい年が先頭。dep.json の得点率と一致")
        except ValueError as e:
            ok(False, f"{fac}: {e}")

    print(header("4. 共通テスト成績分布 CSV"))
    for fname in ("dist_r6.csv", "dist_r7.csv", "dist_r8.csv"):
        S = ds.load_dist(fname)
        bad = 0
        for name, s in S.items():
            n = sum(c for _, c in s["h"])
            if n != s["n"]:
                bad += 1
                continue
            m, sd = ds.dist_moments(s)
            if abs(m - s["mean"]) > 0.05 or abs(sd - s["sd"]) > 0.05:
                bad += 1
        ok(bad == 0, f"{fname}: {len(S)}科目、度数分布から再計算した平均/SD/人数が公表値と一致"
                     + (f"（不一致 {bad} 科目）" if bad else ""), fatal=False)

    print(header("5. 設問別得点状況（q_r8.csv）"))
    for subj, expect_max in (("情報Ⅰ", 100), ("物理", 100), ("公共，政治・経済", 100),
                             ("数学Ⅰ，数学Ａ", 100), ("英語（リーディング）", 100),
                             ("英語（リスニング）", 100), ("化学", 100)):
        it = ds.load_items(subj)
        tot = sum(m for _, _, m, _ in it)
        ok(abs(tot - expect_max) < 1e-6, f"{subj}: 配点合計 {tot:g} (期待 {expect_max})")
        bad_p = [q for _, q, _, p in it if not 0.0 <= p <= 1.0]
        ok(not bad_p, f"{subj}: 得点率が全て [0,1]", fatal=True)
    it = ds.load_items("数学Ⅱ，数学Ｂ，数学Ｃ")
    agg = {}
    for d, _, m, _ in it:
        agg[d] = agg.get(d, 0.0) + m
    required = sum(v for k, v in agg.items() if k in ("1", "2", "3"))
    optional = sorted(v for k, v in agg.items() if k in ("4", "5", "6", "7"))
    ok(abs(required - 52) < 1e-6, f"数学ⅡBC: 必答(第1–3問)の配点 {required:g} (期待 52)")
    ok(len(optional) == 4 and all(abs(v - 16) < 1e-6 for v in optional),
       f"数学ⅡBC: 選択(第4–7問)は各16点 x 4問 → {optional}")
    ok(abs(required + 3 * 16 - 100) < 1e-6,
       "数学ⅡBC: 必答52 + 選択3問×16 = 実効満点100")
    ok(abs(sum(agg.values()) - 116) < 1e-6,
       f"数学ⅡBC: CSV上の全大問合計は {sum(agg.values()):g}"
       "（選択4問すべてを含むため100を超える。選択の組合せを取る前に足してはいけない）")

    print(header("6. 得点開示データの汚染検出"))
    LIMS = {"国語": 100, "数学": 200, "理科": 200, "英語": 150}
    total_rows = clean_rows = 0
    for fname, fac_key in (("kaiji2.json", "fac"), ("kaiji_rows.json", "faculty")):
        data = json.load(open(os.path.join(ds.DATA, fname), encoding="utf-8"))
        for r in data:
            total_rows += 1
            vals = {k: r.get(k) for k in LIMS}
            if any(v is None for v in vals.values()):
                continue
            over = [k for k, v in vals.items() if v > LIMS[k]]
            tiny = max(vals.values()) <= 10
            if over:
                WARN.append(f"{fname} no={r.get('no', r.get('res_no'))}: 満点超え {over}")
                print(f"  [WARN] {fname} no={r.get('no', r.get('res_no'))}: 満点超え {over}")
            elif tiny:
                WARN.append(f"{fname} no={r.get('no', r.get('res_no'))}: 5段階評価の混入疑い {vals}")
                print(f"  [WARN] {fname} no={r.get('no', r.get('res_no'))}: "
                      f"全科目が一桁。5段階評価の混入疑い {vals}")
            else:
                clean_rows += 1
    print(f"  → 全 {total_rows} 行中、4科目そろって妥当な範囲なのは {clean_rows} 行。")
    eng = 0
    for fname, fac_key in (("kaiji2.json", "fac"), ("kaiji_rows.json", "faculty")):
        eng += sum(1 for r in json.load(open(os.path.join(ds.DATA, fname), encoding="utf-8"))
                   if r.get(fac_key) == "工学部")
    ok(eng < 20, f"工学部の行数は {eng}（重複込み）。相関推定には全く足りない", fatal=False)

    print(header("7. params.json のステータス表明"))
    user_params = []
    def walk(node, path=""):
        if isinstance(node, dict):
            if node.get("status") == "USER":
                user_params.append(path)
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)
    walk(params)
    print(f"  status=USER（公開情報からは決まらない）のパラメータ: {len(user_params)} 個")
    for u in user_params:
        print(f"    - {u}")
    ok(bool(user_params),
       "USER パラメータが明示されている（旧版は行内ハードコードで区別が付かなかった）")

    print(header("結果"))
    print(f"  FAIL {len(FAIL)} 件 / WARN {len(WARN)} 件")
    for m in FAIL:
        print(f"    FAIL: {m}")
    if FAIL:
        sys.exit(1)
    print("  致命的な不整合なし。")


if __name__ == "__main__":
    main()
