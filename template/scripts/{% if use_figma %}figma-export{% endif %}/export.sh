#!/usr/bin/env bash
# docs-scaffold: Figmaの指定フレームをPNG書き出しして screenshots/ に保存する
# 使い方:
#   export FIGMA_TOKEN=figd_xxx          # Figma個人アクセストークン
#   scripts/figma-export/export.sh SCR-001   # 引数=画面ID（省略時は全screens spec）
# 依存: bash / curl / python3（jsonパース用。stdlibのみ）
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

SPEC_DIR="docs/specs/screens"
SS_DIR="$SPEC_DIR/screenshots"
SCALE="${FIGMA_SCALE:-2}"
FORMAT="png"

if [ -z "${FIGMA_TOKEN:-}" ]; then
  echo "figma-export: FIGMA_TOKEN 未設定。export FIGMA_TOKEN=figd_... を設定してください。"
  exit 0
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "figma-export: curl が必要です。"; exit 0
fi

# 対象spec収集（引数=SCR-ID、なければ全SCR-*.md）
targets=()
if [ "${1:-}" != "" ]; then
  f=$(ls "$SPEC_DIR"/"$1"*.md 2>/dev/null | head -1 || true)
  [ -n "$f" ] && targets+=("$f")
else
  while IFS= read -r f; do targets+=("$f"); done < <(ls "$SPEC_DIR"/SCR-*.md 2>/dev/null || true)
fi
[ "${#targets[@]}" -eq 0 ] && { echo "figma-export: 対象specが見つかりません。"; exit 0; }

mkdir -p "$SS_DIR"

# frontmatter から key=value を1つ取り出す（先頭---ブロック内のみ）
fm() { awk -v k="$1" 'f&&/^---/{exit} /^---/{f=1;next} f&&$0 ~ "^"k":"{sub("^"k":[ \t]*","");print;exit}' "$2"; }

# figma_url から fileKey を抽出（.../file/KEY/... or .../design/KEY/...）
filekey_from_url() { echo "$1" | sed -nE 's#.*/(file|design)/([A-Za-z0-9]+)/.*#\2#p'; }

for spec in "${targets[@]}"; do
  scr_id=$(basename "$spec" | sed -E 's/^(SCR-[0-9]+).*/\1/')
  node_id=$(fm figma_node_id "$spec")
  furl=$(fm figma_url "$spec")
  if [ -z "$node_id" ] || [ -z "$furl" ]; then
    echo "figma-export: $scr_id は figma_url / figma_node_id が未設定。スキップ。"; continue
  fi
  file_key=$(filekey_from_url "$furl")
  if [ -z "$file_key" ]; then echo "figma-export: $scr_id の figma_url から fileKey を抽出できません。スキップ。"; continue; fi

  echo "figma-export: $scr_id node=$node_id file=$file_key を取得..."
  # 1) 画像URLを取得
  api="https://api.figma.com/v1/images/$file_key?ids=$node_id&scale=$SCALE&format=$FORMAT"
  resp=$(curl -sS -H "X-Figma-Token: $FIGMA_TOKEN" "$api")
  img_url=$(printf '%s' "$resp" | python3 -c "import sys,json;d=json.load(sys.stdin);print((d.get('images') or {}).get('$node_id') or '')" 2>/dev/null || true)
  if [ -z "$img_url" ] || [ "$img_url" = "None" ]; then
    echo "figma-export: $scr_id の画像URL取得失敗。応答: $(printf '%s' "$resp" | head -c 200)"; continue
  fi
  # 2) ダウンロード
  out="$SS_DIR/${scr_id}_default.$FORMAT"
  curl -sS -o "$out" "$img_url"
  echo "figma-export: 保存 $out"
done

echo "figma-export: 完了。git diff で画像差分を確認し、コミットしてください。"
