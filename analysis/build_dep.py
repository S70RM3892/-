# -*- coding: utf-8 -*-
"""dep.json を一次資料から再生成し、コミット済みのものと一致するか検算する。

  入力  ../data/kyodai_official.json  … 京大公式の学科別合格者最低点（fac, last）
        ../data/ratio.json            … 学科×年の志願倍率（app / 受入学生数目安）
  出力  dep.json（--write 指定時のみ上書き。既定では検算のみ）

満点の regime に注意（この分析の最大の構造断層）:
  2019–2024 年度入試 … 1000 点満点（共通テストに『情報』が無い）
  2025 年度入試以降  … 1025 点満点（新課程。共通テスト『情報Ⅰ』50 点が加わる）
  last は満点そのままの素点なので、得点率に直すときに年で割る数が変わる。
  8 年のうち現行配点はまだ 2 年しかない。dv の年跨ぎ比較・分散推定は
  この断層を跨いでいる（rb.py の 6. を参照）。

dep.json のスキーマ:
  dep    学科名
  y      入試年度（2026 = 令和8年度入試）
  rate   合格者最低点の得点率 (%)           = last / 満点(y) * 100
  dv     rate の当年 6 学科平均からの乖離 (pt)  ※構成上 6 学科で必ず 0 和
  ratio  志願倍率 = app / acc
  dr     ratio の当年 6 学科平均からの乖離
  app    志願者数
  acc    学科別の席数。京大公式の「受入学生数（目安）」に特色入試の残余を
         加えた実数ベースの値で、募集要項の目安とは 1–2 人ずれる年がある。
         sd2.py / sd3.py はこれを合格者数として順序統計の SD に使っている。
"""
import json, sys, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
DEPS = ["情報", "物理工", "電電", "建築", "地球工", "理工化"]
FAC = {"地球工": "工学部(地球工学科)", "建築": "工学部(建築学科)",
       "物理工": "工学部(物理工学科)", "電電": "工学部(電気電子工学科)",
       "情報": "工学部(情報学科)", "理工化": "工学部(理工化学科(旧工化))"}
YRS = list(range(2019, 2027))


def full_marks(y):
    return 1025.0 if y >= 2025 else 1000.0


def build():
    off = {r["fac"]: r["last"] for r in
           json.load(open(os.path.join(HERE, "../data/kyodai_official.json"), encoding="utf-8"))}
    rat = json.load(open(os.path.join(HERE, "../data/ratio.json"), encoding="utf-8"))["R"]
    # last は新しい年が先頭（2026, 2025, …, 2019）
    rate = {(p, y): off[FAC[p]][len(YRS) - 1 - i] / full_marks(y) * 100
            for p in DEPS for i, y in enumerate(YRS)}
    ratio = {(p, y): rat[p][str(y)] for p in DEPS for y in YRS}
    out = []
    for y in YRS:
        mr = st.mean(rate[(p, y)] for p in DEPS)
        md = st.mean(ratio[(p, y)] for p in DEPS)
        for p in DEPS:
            out.append({"dep": p, "y": y, "ratio": ratio[(p, y)], "rate": rate[(p, y)],
                        "dv": rate[(p, y)] - mr, "dr": ratio[(p, y)] - md})
    return out


def main():
    built = {(d["dep"], d["y"]): d for d in build()}
    cur = json.load(open(os.path.join(HERE, "dep.json"), encoding="utf-8"))
    bad = 0
    for d in cur:
        b = built[(d["dep"], d["y"])]
        # dep.json は元データを 0.01pt 単位に丸めた値で入っている年がある
        for k, tol in (("rate", 6e-3), ("dv", 8e-3), ("ratio", 1e-9), ("dr", 1e-9)):
            if abs(d[k] - b[k]) > tol:
                print(f"  不一致 {d['dep']} {d['y']} {k}: dep.json={d[k]!r} 再生成={b[k]!r}")
                bad += 1
    print(f"検算: {len(cur)} レコード x 4 項目中 {bad} 件が許容差を超過"
          f"（rate の丸め差は最大 0.005pt = 1025 点中 0.05 点）")
    print("  app / acc は一次資料が repo に無く、dep.json の値をそのまま踏襲している。"
          "\n  acc は『合格者数』として使われているが、募集要項の受入学生数目安"
          "（令和6 情報 87 人 / 令和9 情報 94 人）とは 1-2 人ずれる。")
    if "--write" in sys.argv:
        merged = []
        for d in cur:
            b = dict(built[(d["dep"], d["y"])])
            b["app"], b["acc"] = d["app"], d["acc"]
            merged.append(b)
        json.dump(merged, open(os.path.join(HERE, "dep.json"), "w", encoding="utf-8"),
                  ensure_ascii=False)
        print("dep.json を書き出した")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
