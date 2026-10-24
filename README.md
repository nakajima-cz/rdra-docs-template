# rdra-docs-template (copier template)

RDRA + ADR ベースのドキュメント構造と、実装連動の doc 自動メンテ機構を、
新規・既存どちらのリポジトリにも競合なく展開する copier テンプレート。

- リポジトリ: https://github.com/nakajima-cz/rdra-docs-template

## 要件
- Python 3.10+ / Git 2.27+ / copier 9+

copier のインストール（どれか1つ）:
```sh
uv tool install copier
# または
pipx install copier
```
確認: `copier --version` が 9.x 以上であること。

## セットアップ

### 新規リポジトリに展開する
```sh
mkdir my-project && cd my-project
git init
copier copy --trust https://github.com/nakajima-cz/rdra-docs-template.git .
git add -A && git commit -m "docs: scaffold from rdra-docs-template"
```

### 既存リポジトリに展開する
対象リポジトリのルートで（未コミットの変更がない状態で実行すること）:
```sh
cd /path/to/target-repo
copier copy --trust https://github.com/nakajima-cz/rdra-docs-template.git .
git status   # 追加されたファイルを確認してからコミット
```
既存の `README.md` / `CLAUDE.md` / `.claude/settings.json` などは上書きされない（後述）。

### 質問への回答
展開時に以下を聞かれる（Enter でデフォルト）:

| 質問 | 内容 | デフォルト |
|---|---|---|
| `project_name` | ルート README の見出しに使うプロジェクト名 | `My Project` |
| `use_claude_hook` | Claude Code の Stop フックで docs 自動メンテを有効にするか | `true` |
| `hook_manager` | 既存の git フック管理（none / husky / lefthook） | `none` |

### `--trust` について
展開後に以下の `_tasks` を実行するため `--trust` が必要（付けないと確認を求められるか、タスクが実行されない）:
- `git config core.hooksPath .githooks`（git リポジトリ内でのみ）
- `chmod +x .githooks/*`

`git init` 前に展開した場合は、後から手動で実行する:
```sh
git config core.hooksPath .githooks
chmod +x .githooks/*
```

### バージョンを指定して展開する
デフォルトは最新タグ（タグがなければ `main` の HEAD）。特定バージョンに固定する場合:
```sh
copier copy --trust --vcs-ref v1.4.0 https://github.com/nakajima-cz/rdra-docs-template.git .
```

## 更新の追従
展開先リポジトリのルートで（未コミットの変更がない状態で）:
```sh
copier update --trust
```
`.copier-answers.yml` に記録されたテンプレート URL と版をもとに 3-way マージする。
コンフリクトが出たら通常の git と同様に解消してコミットする。
`.copier-answers.yml` は手で編集せず、必ずコミットしておくこと。

## ローカルのテンプレートから展開する（テンプレート開発者向け）
```sh
git clone https://github.com/nakajima-cz/rdra-docs-template.git
copier copy --trust ./rdra-docs-template /path/to/target-repo
```
未コミットの変更を含めて試す場合は `--vcs-ref HEAD` を付ける。

## 整合性チェック（docs-validate）
展開先リポジトリのルートで:
```sh
python3 scripts/docs-validate/validate-docs.py          # 人間向け出力
python3 scripts/docs-validate/validate-docs.py --json   # CI 向け
python3 scripts/docs-validate/validate-docs.py --strict # WARN も失敗扱い
```
- **ERROR**（構造の破綻・push をブロック）: frontmatter 必須キー欠落 / `design_status` 不正値 / `ADR-`・`SCR-`・`API-` の dangling 参照 / 対応表と個票の双方向不一致
- **WARN**（表示のみ）: プレースホルダ未置換（`YYYY-MM-DD` 等） / 画像リンク切れ / `docs/rdra/` に定義の無い `UC-` 参照
- pre-push から自動実行される。一時回避は `DOCS_VALIDATE_SOFT=1 git push` または `git push --no-verify`
- 依存は python3 のみ（未検出なら検査をスキップして push を通す）

## 特徴
- `scripts/docs-validate/validate-docs.py` で docs の構造整合を機械検査（pre-push でブロック）
- 既存ファイルは `_skip_if_exists` で上書きしない（docs/, README, CLAUDE, .claude/settings.json）
- git フックは `.githooks/`（`core.hooksPath`）に置き `.git/hooks` を汚さない
- `.copier-answers.yml` に版を記録し `copier update` で3-wayマージ追従
