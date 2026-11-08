#!/usr/bin/env bash
# pre-push の Python 解決とスキップ動作を scaffold 済みリポジトリで検証する。
set -uo pipefail

repo_root=$(cd "$(dirname "$0")/.." && pwd)
work_root=$(mktemp -d "${TMPDIR:-/tmp}/rdra-prepush-e2e.XXXXXX")
test_repo="$work_root/repo"
remote="$work_root/remote.git"
normal_path="/opt/homebrew/bin:$HOME/.local/bin:$PATH"
git_bin=$(PATH="$normal_path" command -v git)

mkdir -p "$test_repo" "$remote" "$work_root/no-python" "$work_root/shim"
"$git_bin" -C "$remote" init --bare -q
"$git_bin" -C "$test_repo" init -q -b main
cd "$test_repo"
PATH="$normal_path" copier copy --trust --vcs-ref HEAD --defaults "$repo_root" . >/dev/null

hooks_path=$("$git_bin" config core.hooksPath)
if [ "$hooks_path" != ".githooks" ]; then
  echo "FAIL hooksPath: expected=.githooks actual=$hooks_path" >&2
  exit 1
fi

echo "HOOKS_PATH=$hooks_path"
"$git_bin" add -A
"$git_bin" -c user.email=t@t -c user.name=t commit -qm init
"$git_bin" remote add origin "$remote"

run_push() {
  local label=$1
  local path=$2
  shift 2
  PATH="$path" "$@" git push origin main >"$work_root/$label.log" 2>&1
  local rc=$?
  cat "$work_root/$label.log"
  echo "${label}_EXIT=$rc"
  return "$rc"
}

run_push CASE1_WARN "$normal_path" /usr/bin/env
rc=$?
if [ "$rc" -ne 0 ]; then exit 1; fi

cp docs/glossary.md "$work_root/glossary.clean"
printf '\nDangling decision: ADR-0042\n' >> docs/glossary.md
"$git_bin" add docs/glossary.md
"$git_bin" -c user.email=t@t -c user.name=t commit -qm dangling-adr
run_push CASE1_ERROR "$normal_path" /usr/bin/env
rc=$?
if [ "$rc" -ne 1 ]; then exit 1; fi
run_push CASE1_SOFT "$normal_path" /usr/bin/env DOCS_VALIDATE_SOFT=1
rc=$?
if [ "$rc" -ne 0 ]; then exit 1; fi

cp "$work_root/glossary.clean" docs/glossary.md
"$git_bin" add docs/glossary.md
"$git_bin" -c user.email=t@t -c user.name=t commit -qm restore-clean-docs

for cmd in bash git tr sed grep; do
  cmd_path=$(PATH="$normal_path" command -v "$cmd")
  ln -s "$cmd_path" "$work_root/no-python/$cmd"
done
printf '#!/bin/sh\necho "python fallback must not run" >&2\nexit 126\n' > "$work_root/no-python/python"
chmod +x "$work_root/no-python/python"

printf '\ncase2\n' >> README.md
"$git_bin" add README.md
"$git_bin" -c user.email=t@t -c user.name=t commit -qm case2
run_push CASE2_NO_PYTHON "$work_root/no-python" /usr/bin/env
rc=$?
if [ "$rc" -ne 0 ]; then exit 1; fi
if ! grep -q 'docs/ の構造を検査します' "$work_root/CASE2_NO_PYTHON.log"; then
  echo "FAIL CASE2: absolute-path fallback did not run validator" >&2
  exit 1
fi

cp -R "$work_root/no-python/." "$work_root/shim/"
printf '#!/bin/sh\necho "No version is set for command python3" >&2\nexit 126\n' > "$work_root/shim/python3"
chmod +x "$work_root/shim/python3"
printf '\ncase3\n' >> README.md
"$git_bin" add README.md
"$git_bin" -c user.email=t@t -c user.name=t commit -qm case3
run_push CASE3A_SHIM_FALLBACK "$work_root/shim" /usr/bin/env
rc=$?
if [ "$rc" -ne 0 ]; then exit 1; fi
if ! grep -q 'docs/ の構造を検査します' "$work_root/CASE3A_SHIM_FALLBACK.log"; then
  echo "FAIL CASE3A: fallback did not run validator" >&2
  exit 1
fi

printf '\nDangling decision: ADR-0042\n' >> docs/glossary.md
"$git_bin" add docs/glossary.md
"$git_bin" -c user.email=t@t -c user.name=t commit -qm case3a-dangling-adr
run_push CASE3A_SHIM_ERROR "$work_root/shim" /usr/bin/env
rc=$?
if [ "$rc" -ne 1 ]; then
  echo "FAIL CASE3A: validator did not block dangling reference" >&2
  exit 1
fi

cp "$work_root/glossary.clean" docs/glossary.md
"$git_bin" add docs/glossary.md
"$git_bin" -c user.email=t@t -c user.name=t commit -qm restore-clean-docs-for-case3b

cat > "$work_root/disable-python-candidates.sh" <<'EOF'
function /usr/bin/python3 { return 126; }
function /opt/homebrew/bin/python3 { return 126; }
function python { return 126; }
EOF
run_push CASE3B_ALL_UNUSABLE "$work_root/shim" /usr/bin/env BASH_ENV="$work_root/disable-python-candidates.sh"
rc=$?
if [ "$rc" -ne 0 ]; then exit 1; fi
if ! grep -q 'python3 は見つかりましたが実行できないため検査をスキップしました' "$work_root/CASE3B_ALL_UNUSABLE.log"; then
  echo "FAIL CASE3B: found-but-unusable skip message not found" >&2
  exit 1
fi
if grep -q 'ERROR のため push を中止しました' "$work_root/CASE3B_ALL_UNUSABLE.log"; then
  echo "FAIL CASE3B: dependency failure was treated as validator error" >&2
  exit 1
fi

cp .githooks/pre-push "$work_root/pre-push.clean"
sed 's/python3 \/usr\/bin\/python3 \/opt\/homebrew\/bin\/python3 python/missing-python3 missing-python/' \
  "$work_root/pre-push.clean" > .githooks/pre-push
chmod +x .githooks/pre-push
printf '\ncase3c\n' >> README.md
"$git_bin" add README.md
"$git_bin" -c user.email=t@t -c user.name=t commit -qm case3c
run_push CASE3C_NOT_FOUND "$normal_path" /usr/bin/env
rc=$?
if [ "$rc" -ne 0 ]; then exit 1; fi
if ! grep -q 'python3 が見つからないため検査をスキップしました' "$work_root/CASE3C_NOT_FOUND.log"; then
  echo "FAIL CASE3C: not-found skip message not found" >&2
  exit 1
fi

echo "PASS pre-push Python resolution E2E"
echo "E2E_DIR=$work_root"
