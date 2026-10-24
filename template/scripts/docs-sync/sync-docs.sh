#!/usr/bin/env bash
# docs-scaffold: 実装差分から docs の What/How を同期（Why は生成しない）
# ガード: 前回同期SHA以降にソース変更が無ければ何もしない
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

marker=".docs-scaffold/last-sync-sha"
patchfile=".docs-scaffold/last-diff.patch"
mkdir -p .docs-scaffold

# 設定（.docs-scaffold/config.sh が無ければ既定値）
DOCS_SOURCE_DIRS="src app lib api server packages"
DOCS_SYNC_AGENT="claude"
DOCS_SYNC_CMD=""
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

# 差分はファイルに置き、プロンプトから参照させる（stdin 依存だとエージェントごとに挙動が違うため）
git --no-pager diff "$base..HEAD" -- "${pathspec[@]}" > "$patchfile"

prompt="あなたはこのリポジトリの docs メンテナです。${patchfile} のコード差分を読み、
docs/specs 配下と docs/traceability の該当ファイルの What/How のみ更新してください。
更新対象の見つけ方: 各 spec の frontmatter の source: が指すソースパスが差分に含まれるものを更新する。
制約:
- Why(なぜその設計か)は絶対に創作しない。必要なら本文に TODO(Why): ADR-xxxx? のスタブだけ残す。
- docs/ 配下以外は変更しない。common/ の重複記述は作らず参照に留める。
- 変更は最小限、既存の節構成・書式・ID規約(SCR-/API-/UC-)に従う。
- 更新した spec は frontmatter の updated: を今日の日付に、画面specは source_commit: を現行HEADのSHAに更新する。"

# エージェント別の起動コマンド（プロンプトを最後の引数で渡す）
case "$DOCS_SYNC_AGENT" in
  none)
    echo "docs-sync: DOCS_SYNC_AGENT=none。差分を ${patchfile} に出力しました。手動で docs を更新してください。"
    echo "$head" > "$marker"
    exit 0
    ;;
  claude)   agent_bin="claude"; set -- claude -p "$prompt" --allowedTools 'Read,Edit' --max-turns 20 ;;
  codex)    agent_bin="codex";  set -- codex exec "$prompt" ;;
  opencode) agent_bin="opencode"; set -- opencode run "$prompt" ;;
  custom)
    if [ -z "$DOCS_SYNC_CMD" ]; then
      echo "docs-sync: DOCS_SYNC_AGENT=custom ですが DOCS_SYNC_CMD が空です（.docs-scaffold/config.sh を確認）。スキップ。"
      exit 0
    fi
    agent_bin=${DOCS_SYNC_CMD%% *}
    set -- sh -c "$DOCS_SYNC_CMD \"\$1\"" sh "$prompt"
    ;;
  *)
    echo "docs-sync: 未知の DOCS_SYNC_AGENT='${DOCS_SYNC_AGENT}'（claude / codex / opencode / custom / none）。スキップ。"
    exit 0
    ;;
esac

if ! command -v "$agent_bin" >/dev/null 2>&1; then
  echo "docs-sync: ${agent_bin} が見つかりません。差分は ${patchfile} にあります。手動で docs を更新してください。"
  exit 0
fi

echo "docs-sync: ${DOCS_SYNC_AGENT} をヘッドレス起動して docs を更新します..."
"$@" || true

echo "$head" > "$marker"
echo "docs-sync: 完了。git diff で結果を確認し、doc-sync として独立コミットしてください。"
