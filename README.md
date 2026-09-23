# rdra-docs-template (copier template)

RDRA + ADR ベースのドキュメント構造と、実装連動の doc 自動メンテ機構を、
新規・既存どちらのリポジトリにも競合なく展開する copier テンプレート。

## 使い方

初回展開（対象リポジトリのルートで）:
```
copier copy gh:<you>/rdra-docs-template .
# ローカルパスからも可:
copier copy /path/to/rdra-docs-template /path/to/target-repo
```

更新の追従:
```
copier update
```

## 特徴
- 既存ファイルは `_skip_if_exists` で上書きしない（docs/, README, CLAUDE, .claude/settings.json）
- git フックは `.githooks/`（`core.hooksPath`）に置き `.git/hooks` を汚さない
- `.copier-answers.yml` に版を記録し `copier update` で3-wayマージ追従

## 要件
- Python 3.10+ / Git 2.27+ / copier 9+（`uv tool install copier` or `pipx install copier`）
