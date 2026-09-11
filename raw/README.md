# raw/ — 収集時の作業場

`analysis/` と `data/` が再現対象で、ここは**再現対象外**。収集した生ページと、
そのとき書き捨てたスクリプトを残してある。何がどの成果物を作ったかの対応は
当時取っていないので、以下は中身から事後的に分類したもの。

## データ抽出パイプライン（現役。これだけは残す価値がある）

| ファイル | 役割 |
|---|---|
| `kx.py` | PDF を pdfminer で座標つきテキスト化。`data/r9.txt` などの生成元。要 `pylibs/`（.gitignore 済み） |
| `tbl.py` | 同じく PDF から表を抜く版 |
| `parse.py` | 大学入試センターの科目別成績分布 CSV のローダ。`analysis/kt.py` の `load()` の原型 |
| `extract.py` | 二次の科目配点（国100/数200/理200/英150）を HTML から抜く |
| `nijikei.py` / `nijikei_fix.py` | 二次の切断正規による受験者σ復元。`artifacts/kyodai-score-sheet.html` の σ=80.1／68.7 の出所 |
| `planD.py` / `planD2.py` | `kyodai_official.json` を読む学部横断の配点比較 |
| `err.py` | 2026 工学部情報学科の共テ換算構造の検算 |

## 出題地図のデータ（`data/zk/` と重複）

`_all.js`（PMAP 物理）, `_mjs.js`（MAP 数学）, `_cjs.js`（KMAP 化学）は
`artifacts/kyodai-map.html` に埋め込まれている分野マップの元データ。
`data/zk/MAP.js` ほかと同系統だが同一ではない（版が違う）。
完全重複だった `c_script.js`（=`_cjs.js`）と `m_script.js`（=`_mjs.js`）は削除済み。

## Playwright のワンショット（すべて死んでいる）

`batch.js` `c2.js` `c3.js` `chip.js` `chk.js` `chk2.js` `chk3.js` `cn.js` `crop.js`
`grab.js` `insp.js` `one.js` `pdfcrop.js` `pdffull.js` `pdfshot.js` `redo.js`
`rend.js` `rend2.js` `render.js` `rules.js` `sel.js` `shot.js` `shot2.js`
`tabfit.js` `tabshot.js` `two.js` `wide.js` `wide2.js` `zoom.js`

PDF やページのスクリーンショットを撮るための使い捨て。うち 5 本
（`batch.js` `one.js` `redo.js` `render.js` `two.js`）は存在しない
`/root/.claude/uploads/...` を直に参照しており、そのままでは動かない。
残りも出力先がハードコードされている。**新しく撮るなら書き直した方が早い。**

## 生スクレイプ

| ファイル | 出所 |
|---|---|
| `k_r3`–`k_r7.html`, `dnc7.html`, `wb_r5b.html`, `suii.html`, `suiiR3.html` | 大学入試センター 試験情報データ・平均点推移 |
| `bn_356` `bn_380` `bn_399` `kl.html` | 東進 京大本番レベル模試の案内（各141KB、内容は少しずつ違う） |
| `a_50` `a_200` `a_400` `kaiji.html` `idx_kyoto.html` | 京大受験掲示板の得点開示スレ（cp932）。`data/kaiji2.json` の元 |
| `kstat.html` `pe.html` `r8eq.html` `u.html` | 模試・統計系のページ |
| `yz7.html` | 代々木ゼミナール 入試情報（合格最低点の2ソース目） |
| `_body.html` `bak17.html` `new_panels.html` `now_sec.html` `drill_panel.html` `_yearly.html` | `artifacts/` の各 HTML の作業中スナップショット |

## 削除済み

取得に失敗した HTTP レスポンス（403 / 404 / Access Denied / egress ブロック /
「現在ご利用いただけない状態」）で、中身が 0 のもの 9 件を削除:
`bn_426` `bn_446` `bn_467` `r426` `t` `idx` `pr` `kj` `wb_r5`（すべて .html）。
