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
| `use_screens` | 画面設計書（`docs/specs/screens` と 画面×UC×API 対応表）を使うか。API専用/バッチ案件は `false` | `true` |
| `use_figma` | Figma 連携スクリプト（`scripts/figma-export`）を同梱するか（`use_screens=true` の時だけ質問） | `use_screens` と同じ |
| `source_dirs` | 実装ソースのディレクトリ（スペース区切り）。docs 未更新警告と docs-sync の対象範囲 | `src app lib api server packages` |
| `docs_sync_agent` | docs 自動同期に使うエージェント（`claude` / `codex` / `opencode` / `custom` / `none`） | `claude` |
| `docs_sync_cmd` | `docs_sync_agent=custom` のとき実行するコマンド（プロンプトが最後の引数） | （空） |
| `use_claude_hook` | Claude Code の Stop フックで docs 自動メンテを有効にするか（`docs_sync_agent=claude` の時だけ質問） | `true` |
| `hook_manager` | pre-push ゲートの配線先（none / husky / lefthook） | `none` |

`use_screens=false` のとき、`docs/specs/screens/` と Figma 連携は配布されず、対応表は
`docs/traceability/uc-api.md`（UC×API）になり、`docs/WORKFLOW.md` は画面工程を含まない API 版に差し替わる。
検証スクリプトは `screen-uc-api.md` / `uc-api.md` のどちらでも動く。

`docs_sync_agent` は `.docs-scaffold/config.sh` の `DOCS_SYNC_AGENT` に書き出され、`sync-docs.sh` が
`claude -p` / `codex exec` / `opencode run` / 任意コマンド を起動し分ける。差分は常に
`.docs-scaffold/last-diff.patch` に書き出してプロンプトから参照させるため（stdin 依存にしない）、
エージェントを乗り換えてもスクリプト側の変更は不要。`none` と未インストール時は差分だけ出して exit 0。
`claude` 以外を選ぶと `.claude/`（Stop フック・スラッシュコマンド）は配布されない。

`source_dirs` の回答は `.docs-scaffold/config.sh` の `DOCS_SOURCE_DIRS` に書き出され、
`.githooks/pre-push`（docs 未更新警告）と `scripts/docs-sync/sync-docs.sh`（同期対象の git diff）が参照する。
Go なら `cmd internal pkg`、monorepo なら `apps packages` のように案件の構成へ合わせる。
このファイルは `_skip_if_exists` で保護されるので、展開後に手で書き換えてよい（`copier update` で戻らない）。
ファイルが無い旧リポジトリでは既定値にフォールバックする。

`hook_manager` の挙動（`scripts/docs-hooks/install.sh` が実施。何度実行しても同じ結果）:

| 回答 | 配線 | 既存設定の扱い |
|---|---|---|
| `none` | `git config core.hooksPath .githooks` | 既に別の `core.hooksPath` があれば**上書きせず**、追記すべき1行を表示 |
| `husky` | `.husky/pre-push` に `bash .githooks/pre-push` を追記 | `core.hooksPath` は**触らない**（husky の `.husky` を壊さない）。`.husky` が無ければ案内のみ |
| `lefthook` | `lefthook.yml` が無ければ作成して配線 | 既存の lefthook 設定は**自動編集せず**、貼り付け用スニペットを表示 |

### `--trust` について
展開後に以下の `_tasks` を実行するため `--trust` が必要（付けないと確認を求められるか、タスクが実行されない）:
- `bash scripts/docs-hooks/install.sh <hook_manager>`（git リポジトリ内でのみ配線。非gitならスキップ）
- `chmod +x .githooks/* scripts/**`

`git init` 前に展開した場合、または husky を後から導入した場合は、手動で実行する:
```sh
bash scripts/docs-hooks/install.sh none      # または husky / lefthook
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

## リポジトリ構成
- `template/` … 利用者へ展開される本体（copier の `_subdirectory`）
- `copier.yml` … 質問・`_tasks`・上書き保護の定義
- `meta/` … **テンプレート自体の資料**（ライフサイクルのシーケンス図など）。展開先には配布されない。詳細は [`meta/README.md`](meta/README.md)

## 特徴
- `scripts/docs-validate/validate-docs.py` で docs の構造整合を機械検査（pre-push でブロック）
- 既存ファイルは `_skip_if_exists` で上書きしない（docs/, README, CLAUDE, .claude/settings.json）
- git フックは `.githooks/` に置き `.git/hooks` を汚さない。husky / lefthook 併用時は `core.hooksPath` を奪わず、各管理ツールから呼ぶ形で配線する
- `.copier-answers.yml` に版を記録し `copier update` で3-wayマージ追従
