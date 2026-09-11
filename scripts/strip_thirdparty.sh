#!/usr/bin/env bash
# 第三者のページ保存を削除する。公開前チェックリスト（raw/PROVENANCE.md）用。
# 解析コードは raw/ を読まないので、結果は変わらない。
# 実行後に run_all.sh が通ることを必ず確認すること。
set -euo pipefail
cd "$(dirname "$0")/.."

echo "削除対象（第三者ページの保存物）:"
git ls-files 'raw/*.html' 'raw/*.js' 'data/zk/*.js' 'data/toshin.json' | sed 's/^/  /'
read -r -p "削除して続行しますか? [y/N] " ans
[[ "$ans" == "y" || "$ans" == "Y" ]] || { echo "中止した。"; exit 1; }

git rm -q --cached $(git ls-files 'raw/*.html' 'raw/*.js' 'data/zk/*.js' 'data/toshin.json')
rm -f $(git ls-files --deleted 2>/dev/null) 2>/dev/null || true

cat >> .gitignore <<'EOF'

# 第三者ページの保存物（strip_thirdparty.sh で除去済み）
raw/*.html
raw/*.js
data/zk/*.js
data/toshin.json
EOF

echo
echo "追跡から外した。run_all.sh を実行して結果が変わらないことを確認すること。"
echo "注意: 過去のコミットには残る。完全に消すには git filter-repo が要る。"
