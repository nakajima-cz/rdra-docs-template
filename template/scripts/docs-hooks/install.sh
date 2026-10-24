#!/usr/bin/env bash
# docs-scaffold: pre-push ゲート（.githooks/pre-push）を各フック管理方式へ配線する。
#
# 使い方:
#   bash scripts/docs-hooks/install.sh none      # 素の core.hooksPath を使う（既定）
#   bash scripts/docs-hooks/install.sh husky     # husky(.husky/pre-push) から呼ぶ
#   bash scripts/docs-hooks/install.sh lefthook  # lefthook.yml から呼ぶ
#
# 設計方針:
# - 何度実行しても同じ結果（idempotent）。
# - 他ツールの設定を壊さない。husky/lefthook 選択時は core.hooksPath を触らない
#   （husky は core.hooksPath=.husky を自前で設定するため、.githooks を入れると husky が無効化される）。
# - 自動で安全に書けない場合はブロックせず、手順を表示して exit 0 する。
set -uo pipefail

MANAGER="${1:-none}"
MARKER="docs-scaffold"
HOOK_BODY="bash .githooks/pre-push"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "docs-hooks: git リポジトリではないため配線をスキップしました。"
  echo "  git init 後に  bash scripts/docs-hooks/install.sh ${MANAGER}  を実行してください。"
  exit 0
fi

cd "$(git rev-parse --show-toplevel)" || exit 0
chmod +x .githooks/* 2>/dev/null

case "$MANAGER" in
  none)
    current=$(git config core.hooksPath 2>/dev/null || echo "")
    if [ -n "$current" ] && [ "$current" != ".githooks" ]; then
      echo "docs-hooks: core.hooksPath が既に '${current}' です。上書きしませんでした。"
      echo "  '${current}/pre-push' に次の1行を追加してください: ${HOOK_BODY}"
      exit 0
    fi
    git config core.hooksPath .githooks
    echo "docs-hooks: core.hooksPath=.githooks を設定しました。"
    ;;

  husky)
    if [ ! -d .husky ]; then
      echo "docs-hooks: .husky が見つかりません（husky 未導入）。core.hooksPath は変更していません。"
      echo "  husky 導入後に次を実行してください:"
      echo "    bash scripts/docs-hooks/install.sh husky"
      exit 0
    fi
    target=".husky/pre-push"
    if [ -f "$target" ] && grep -q "$MARKER" "$target"; then
      echo "docs-hooks: ${target} は配線済みです。"
      exit 0
    fi
    {
      echo ""
      echo "# ${MARKER}: docs 構造検査（回避は DOCS_VALIDATE_SOFT=1 git push）"
      echo "$HOOK_BODY"
    } >> "$target"
    chmod +x "$target" 2>/dev/null
    echo "docs-hooks: ${target} へ pre-push ゲートを追記しました（core.hooksPath は husky のまま）。"
    ;;

  lefthook)
    cfg=""
    for c in lefthook.yml lefthook.yaml .lefthook.yml .lefthook.yaml; do
      [ -f "$c" ] && cfg="$c" && break
    done
    if [ -n "$cfg" ]; then
      if grep -q "$MARKER" "$cfg"; then
        echo "docs-hooks: ${cfg} は配線済みです。"
        exit 0
      fi
      echo "docs-hooks: 既存の ${cfg} は自動編集しません。次を pre-push に追記してください:"
      echo ""
      echo "pre-push:"
      echo "  commands:"
      echo "    ${MARKER}:"
      echo "      run: ${HOOK_BODY}"
      echo ""
      exit 0
    fi
    cat > lefthook.yml <<EOF
pre-push:
  commands:
    ${MARKER}:
      run: ${HOOK_BODY}
EOF
    echo "docs-hooks: lefthook.yml を作成し pre-push ゲートを配線しました。"
    echo "  有効化: lefthook install"
    ;;

  *)
    echo "docs-hooks: 未知のフック管理 '${MANAGER}'。配線をスキップしました（none / husky / lefthook）。"
    ;;
esac

exit 0
