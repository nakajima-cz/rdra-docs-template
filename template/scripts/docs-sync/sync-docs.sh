#!/usr/bin/env bash
# docs-scaffold: 実装差分から docs の What/How を同期（Why は生成しない）
# ガード: 前回同期SHA以降にソース変更が無ければ何もしない
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

marker=".docs-scaffold/last-sync-sha"
mkdir -p .docs-scaffold

# 対象ソースディレクトリ（.docs-scaffold/config.sh が無ければ既定値）
DOCS_SOURCE_DIRS="src app lib api server packages"
if [ -f .docs-scaffold/config.sh ]; then
  # shellcheck disable=SC1091
  . .docs-scaffold/config.sh
fi
pathspec=()
for d in $DOCS_SOURCE_DIRS; do pathspec+=("${d}/**"); done
if [ "${#pathspec[@]}" -eq 0 ]; then
  echo "docs-sync: DOCS_SOURCE_DIRS が空です（.docs-scaffold/config.sh を確認）。スキップ。"
  exit 0
fi
last=$(cat "$marker" 2>/dev/null || echo "")
head=$(git rev-parse HEAD)

if [ "$last" = "$head" ]; then
  echo "docs-sync: 既に最新 (${head})。スキップ。"
  exit 0
fi

base=${last:-HEAD~1}
diff=$(git diff "$base..HEAD" -- "${pathspec[@]}" 2>/dev/null || true)
if [ -z "$diff" ]; then
  echo "docs-sync: 対象ソース変更なし（対象: ${DOCS_SOURCE_DIRS}）。スキップ。"
  echo "$head" > "$marker"
  exit 0
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "docs-sync: claude CLI 未検出。手動で docs を更新してください。"
  exit 0
fi

prompt='あなたはこのリポジトリの docs メンテナです。直近のコード差分(git diff)を読み、
docs/specs/screens・docs/specs/apis・docs/traceability の該当ファイルの What/How のみ更新してください。
更新対象の見つけ方: 各 spec の frontmatter の source: が指すソースパスが差分に含まれるものを更新する。
制約:
- Why(なぜその設計か)は絶対に創作しない。必要なら本文に TODO(Why): ADR-xxxx? のスタブだけ残す。
- docs/ 配下以外は変更しない。common/ の重複記述は作らず参照に留める。
- 変更は最小限、既存の節構成・書式・ID規約(SCR-/API-/UC-)に従う。
- 更新した spec は frontmatter の updated: を今日の日付に、画面specは source_commit: を現行HEADのSHAに更新する。'

echo "docs-sync: claude をヘッドレス起動して docs を更新します..."
git --no-pager diff "$base..HEAD" -- "${pathspec[@]}" | \
  claude -p "$prompt" --allowedTools 'Read,Edit,Bash(git diff*)' --max-turns 20 || true

echo "$head" > "$marker"
echo "docs-sync: 完了。git diff で結果を確認し、doc-sync として独立コミットしてください。"
