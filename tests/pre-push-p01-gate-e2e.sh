#!/usr/bin/env bash
# pre-push の P01 ゲート検査（check-p01-gates.py）の既定挙動を scaffold 済みリポジトリで検証する。
#   - 既定: 注記の無い4節行は WARNING のみ（push はブロックしない）
#   - DOCS_P01_GATE_STRICT=1: 同じ違反を ERROR としてブロックする
#   - 注記のある4節行では検査が何も言わない
set -uo pipefail

repo_root=$(cd "$(dirname "$0")/.." && pwd)
work_root=$(mktemp -d "${TMPDIR:-/tmp}/rdra-p01gate-e2e.XXXXXX")
test_repo="$work_root/repo"
remote="$work_root/remote.git"
normal_path="/opt/homebrew/bin:$HOME/.local/bin:$PATH"
git_bin=$(PATH="$normal_path" command -v git)

mkdir -p "$test_repo" "$remote"
"$git_bin" -C "$remote" init --bare -q
"$git_bin" -C "$test_repo" init -q -b main
cd "$test_repo"
PATH="$normal_path" copier copy --trust --vcs-ref HEAD --defaults "$repo_root" . >/dev/null

hooks_path=$("$git_bin" config core.hooksPath)
if [ "$hooks_path" != ".githooks" ]; then
  echo "FAIL hooksPath: expected=.githooks actual=$hooks_path" >&2
  exit 1
fi

"$git_bin" add -A
"$git_bin" -c user.email=t@t -c user.name=t commit -qm init
"$git_bin" remote add origin "$remote"

run_push() {
  local label=$1
  shift
  PATH="$normal_path" "$@" "$git_bin" push origin main >"$work_root/$label.log" 2>&1
  local rc=$?
  cat "$work_root/$label.log"
  echo "${label}_EXIT=$rc"
  return "$rc"
}

# ケース0: 初期 scaffold（4節は「未記入」のみ）→ 検査は何も言わず push 成功
run_push CASE0_CLEAN
rc=$?
if [ "$rc" -ne 0 ]; then echo "FAIL CASE0: clean scaffold push should succeed" >&2; exit 1; fi
if grep -q 'check-p01-gates' "$work_root/CASE0_CLEAN.log"; then
  echo "FAIL CASE0: gate check should stay silent on placeholder-only section4" >&2
  exit 1
fi

# 注記の無い4節行を仕込む
sed -i '' 's/^- （未記入）$/- （未記入）\n- 対象ユーザーは社内の経理部門のみとする/' docs/p00-brief.md 2>/dev/null \
  || sed -i 's/^- （未記入）$/- （未記入）\n- 対象ユーザーは社内の経理部門のみとする/' docs/p00-brief.md
grep -q '対象ユーザーは社内の経理部門のみとする$' docs/p00-brief.md || { echo "FAIL: injection failed" >&2; exit 1; }
"$git_bin" add -A
"$git_bin" -c user.email=t@t -c user.name=t commit -qm case1-unannotated

# ケース1: 既定（警告のみ）→ push は成功するが ERROR 行が出力される
run_push CASE1_WARN_ONLY
rc=$?
if [ "$rc" -ne 0 ]; then
  echo "FAIL CASE1: default mode must not block push" >&2
  exit 1
fi
if ! grep -q 'check-p01-gates: ERROR 1' "$work_root/CASE1_WARN_ONLY.log"; then
  echo "FAIL CASE1: expected the gate check to report the unannotated line" >&2
  exit 1
fi
if ! grep -q 'WARNING' "$work_root/CASE1_WARN_ONLY.log"; then
  echo "FAIL CASE1: expected a WARNING label, not a blocking ERROR" >&2
  exit 1
fi

# ケース2: DOCS_P01_GATE_STRICT=1 → 同じ違反でブロックされる
run_push CASE2_STRICT_BLOCKS /usr/bin/env DOCS_P01_GATE_STRICT=1
rc=$?
if [ "$rc" -ne 1 ]; then
  echo "FAIL CASE2: DOCS_P01_GATE_STRICT=1 must block the push" >&2
  exit 1
fi
if ! grep -q 'DOCS_P01_GATE_STRICT=1' "$work_root/CASE2_STRICT_BLOCKS.log"; then
  echo "FAIL CASE2: expected the strict-mode message" >&2
  exit 1
fi

# 注記を付けて解消する
sed -i '' 's/^- 対象ユーザーは社内の経理部門のみとする$/- 対象ユーザーは社内の経理部門のみとする（REQ-003）/' docs/p00-brief.md 2>/dev/null \
  || sed -i 's/^- 対象ユーザーは社内の経理部門のみとする$/- 対象ユーザーは社内の経理部門のみとする（REQ-003）/' docs/p00-brief.md
"$git_bin" add -A
"$git_bin" -c user.email=t@t -c user.name=t commit -qm case3-annotated

# ケース3: 注記ありの行は検査が反応しない
run_push CASE3_ANNOTATED_SILENT
rc=$?
if [ "$rc" -ne 0 ]; then echo "FAIL CASE3: annotated push should succeed" >&2; exit 1; fi
if grep -q 'check-p01-gates' "$work_root/CASE3_ANNOTATED_SILENT.log"; then
  echo "FAIL CASE3: gate check should stay silent once the line is annotated" >&2
  exit 1
fi

echo "PASS pre-push P01 gate E2E"
echo "E2E_DIR=$work_root"
