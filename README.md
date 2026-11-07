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
| `components` | このプロジェクトが持つ構成要素。**複数選択**（画面 / API / バッチ） | 画面 + API |
| `use_figma` | Figma 連携スクリプト（`scripts/figma-export`）を同梱するか（画面を選んだ時だけ質問） | 画面を選んだなら `true` |
| `source_dirs` | 実装ソースのディレクトリ（スペース区切り）。docs 未更新警告と docs-sync の対象範囲 | `src app lib api server packages` |
| `docs_sync_agent` | docs 自動同期に使うエージェント（`claude` / `codex` / `opencode` / `custom` / `none`） | `claude` |
| `docs_sync_cmd` | `docs_sync_agent=custom` のとき実行するコマンド（プロンプトが最後の引数） | （空） |
| `use_claude_hook` | Claude Code の Stop フックで docs 自動メンテを有効にするか（`docs_sync_agent=claude` の時だけ質問） | `true` |
| `hook_manager` | pre-push ゲートの配線先（none / husky / lefthook） | `none` |

#### `components` で何が変わるか

選んだ構成要素のものだけが配布される。7通りすべてで `validate-docs.py` の ERROR 0 を実測済み。

| 選択 | 配られる指示テンプレ | 設計書の置き場 | 対応表 |
|---|---|---|---|
| 画面 | `p02-structure` `p03-design` `p04-detail` `p05-domain` `p06-handoff` | `docs/specs/screens/` `docs/design/` | `screen-uc-api.md` |
| API | `p04-detail` `p05-domain` `p06-handoff` | `docs/specs/apis/` | `uc-api.md`（画面が無いとき） |
| バッチ | `p02-structure` `p04-detail` `p05-domain` `p06-handoff` | `docs/specs/batches/` | `uc-batch.md` |

`p01-requirements` と `p01-steps` はどの構成でも配られる。要件定義は構成要素に依存しない。

- **フロントエンドのみ**（画面だけ）… API は別チームが持つ前提。画面個票に API 名は書くが `API-xxx` は採番しない
- **API のみ** … P02・P03 は無い。API の採番は P04
- **バッチのみ** … `BATCH-xxx` を P02 で採番し、P04 で処理の流れと失敗時の扱いを書く
- **全部** … 画面・API・バッチが1つの対応表群で追跡される

`use_screens` / `use_apis` / `use_batch` は `components` から導出されるので質問されない。
`use_screens` で答えていた既存プロジェクトが `copier update` すると、その値から初期選択が決まる
（`true` → 画面+API、`false` → API）。

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

## 使い方：導入から1サイクル回すまで

展開しただけでは何も始まらない。このテンプレートの本体は `docs/prompts/` の**指示テンプレ**で、
それを AI に1フェーズずつ渡して成果物をファイルに積み上げていく。ここではその回し方を書く。

### 守る決まり

- **1フェーズ1指示、1セッション。** 前フェーズの会話を引き継がない。入力は常にファイル。
- **会話ではなくファイルがインターフェース。** 口頭で足した前提は、ファイルへ書くまで存在しない扱い。
- **指示テンプレ（`docs/prompts/*`）を案件ごとに書き換えない。** 書き換えたくなったら
  テンプレ側の不足なので、このリポジトリへ issue を立てて指示文そのものを直す。
- **各ステップの終わりに commit する。** どのステップで何が増えたかを後から追えるようにする。

### 全体の流れ

```
P00 ブリーフ          ← 人が書く（1〜5節）
   ↓
P01 要件定義 ──────→ G1 要件FIX          ← 人が承認
   ↓
P02 基本設計 ──────→ G2 整合             ← 機械のみ
   ↓
P03 デザイン ──────→ G3 デザインFIX      ← 人が承認
   ↓
P04 詳細設計 ──────→ G4 整合             ← 機械のみ
   ↓
P05 ドメインモデリング                     ← 人が承認（ゲートではない）
   ↓
P06 実装ハンドオフ                        ← 人が承認（ゲートではない）
   ↓
実装
```

**人が止まるのは5地点だけ。** P02・P04 では聞かれない。P03・P05・P06 もフェーズの途中では聞かれず、
確認したいことは `docs/p00-brief.md` の「7. 未決事項」に溜まり、フェーズの終わりに1回まとめて提示される。

### ゲートウェイ

成果物はどちらでもリポジトリのファイルとして残る。混ぜてもよい（P01 は Slack、P03 は CLI など）。

| | Hermes 経由（Slack） | Claude Code CLI |
|---|---|---|
| 向く場面 | 壁打ち、移動中、複数人で結果を見る | 長時間の生成、モックの大量作成 |
| 渡し方 | チャンネルで依頼する。リポジトリの**絶対パス**を書く | リポジトリのルートで `claude` を起動して依頼する |
| 成果物 | ワークスペースのリポジトリに直接コミットされる | 同じ |
| 注意 | フェーズごとに**新しいスレッド**を立てる | フェーズごとに `/clear` するか起動し直す |

### Step 0　展開して初期コミットする

```sh
cd /path/to/target-repo
copier copy --trust https://github.com/nakajima-cz/rdra-docs-template.git .
# components で 画面 / API / バッチ を選ぶ
python3 scripts/docs-validate/validate-docs.py   # ERROR 0 を確認
git add -A && git commit -m "docs: scaffold from rdra-docs-template"
```

既存リポジトリでも同じ。`_skip_if_exists` で既存の `README.md` / `CLAUDE.md` は上書きされない。

### Step 1　ブリーフを書く（人／AI に任せない）

`docs/p00-brief.md` の **1〜5節**を埋める。6節（仮定）と7節（未決事項）は AI が書くので触らない。

ここが全体の品質を決める。特に **2節「やること / やらないこと」の「やらないこと」側**を具体的に書く。
検証では、ここを埋めたことで `[UC件数に影響]` の未決が **11件 → 1件**に落ちた。
「やらないこと」が空のまま P01 を走らせると、AI は対象範囲を自分で広げる。

書けないものは無理に埋めず空のままにする。P01 が未決として拾い上げる。

### Step 2　P01 要件定義を走らせる

`docs/prompts/p01-requirements.md` を開き、**共通指示のコードブロック＋Step1 のコードブロック**を
1つのメッセージとして渡す。Step1 が終わったら commit し、次に Step2 を渡す。Step9 まで繰り返す。

依頼の文面は、どちらのゲートウェイでもこれで足りる。

```text
/path/to/target-repo で docs/prompts/p01-requirements.md を読み、
共通指示と Step1 を実行してください。このファイルが指示の全てであり、判定基準の正本です。
終わったら判定項目の ○/× と、指示に不足があればそれも報告してください。
```

**指示文より依頼文を優先させない。** 依頼文は「どのファイルのどのステップか」を指すだけにして、
判定基準を会話側に書かない。会話に書いた条件は次のセッションに残らない。

### Step 3　G1 で承認する（人）

`validate-docs.py` の ERROR 0 は**必要条件であって十分条件ではない**。構造が通っても中身は空でありうる。

見る順はこう。

1. **仮定リスト（6節）と未決リスト（7節）を先に読む。** ここに業務の肝が紛れていたら差し戻し。
   両方合わせて0件なら、情報不足を事実で埋めている可能性があるので中身を疑う
2. **未決の確認先が役割名で書かれているか。**「担当者」では足りない
3. **UC 一覧を確定してよいか。** 揺れたまま P02 へ進むと、以降の成果物ごと作り直しになる

差し戻すときは、**どの仮定が誤りかを名指しして `docs/p00-brief.md` の4節へ書き足してから**
同じ指示を再実行する。指示文の方を書き換えて調整しない。

通すときは、未決への回答を7節に追記してコミットする。

### Step 4　P02 以降を同じ要領で回す

渡し方は P01 と同じ。フェーズごとに新しいセッションを立て、1ステップずつ渡して commit する。

| フェーズ | 指示テンプレ | 終わりに見るもの |
|---|---|---|
| P02 基本設計 | `p02-structure.md` | `validate-docs.py` の ERROR 0 と**節構成 WARN 0** |
| P03 デザイン | `p03-design.md` | モックをブラウザで開いて初期表示を確認（PC 幅 1280px 以上） |
| P04 詳細設計 | `p04-detail.md` | ERROR 0 と節構成 WARN 0、対応表の未記入0件 |
| P05 ドメインモデリング | `p05-domain.md` | 集約の切り方・整合方式・未決のガード条件（人がまとめて承認） |
| P06 ハンドオフ | `p06-handoff.md` | `docs/handoff/` の完了条件が判定できる形になっているか |

G2・G4 では人は何もしない。`validate-docs.py` が通れば次へ進む。

G3 では、どの案を採るか・Figma へ起こすか・未決への回答を**まとめて1回で聞かれる**。
承認したら画面個票の `design_status` を `approved` に変え、10節へ承認の行を足す。

### Step 5　実装へ渡す

P06 を通すと `docs/handoff/` にロットごとの指示ができる。実装担当（人でも AI でも）には
**そのロットのファイル1枚**を渡す。`docs/` 全体を読ませない。

`docs/handoff/README.md` の冒頭に「**全ロットの着手を止める未決**」があれば、
その時点では実装に着手できない。先にそれを埋める。

実装側が docs を更新してよいのは `source` / `source_commit` / `updated` と、
各個票の「定義箇所」「エントリポイント」「ページコンポーネント」だけ。
設計が実態と合わないと気づいたときは、**docs を直さずに報告させる**。
直すと、ゲートを通った決定が記録なしに書き換わる。

### つまずきやすいところ

- **指示文を案件向けに書き換えてしまう。** 一度やるとテンプレとして再利用できなくなる。
  不足は成果物側（ブリーフ）か、このリポジトリ側で直す
- **フェーズをまたいで同じセッションを使う。** 前フェーズの文脈が残ると、AI は次フェーズの
  判定基準より会話の記憶を優先する
- **ERROR 0 を合格と読む。** 機械判定は構造しか見ない。人のゲートでは必ず中身を読む
- **ステークホルダーとの議論を docs でやる。** その場で書き換える議論に Markdown と git は向かない。
  議論は表や図で行い、合意した**結果**だけを docs へ落とす

各フェーズの判定項目・やらないこと・差し戻しの合図は `docs/prompts/` の各ファイルが正本。
ここに書き写さない。

## 上書き保護の方針（どのファイルがテンプレ更新で変わるか）

| 区分 | 例 | `copier update` の挙動 |
|---|---|---|
| 人が書く docs（保護） | `docs/README.md` `docs/WORKFLOW.md` `docs/rdra/*/README.md` `docs/specs/common/*.md` `docs/specs/*/README.md` `docs/adr/README.md` `SCR-*` `API-*` `ADR-[0-9]*` 対応表 `glossary.md` `LOG.md` | **変更されない**（利用者の記述がそのまま残る） |
| 雛形（伝播） | `docs/specs/screens/_template.md` `docs/specs/apis/_template.md` `docs/adr/template.md` | テンプレ改善が反映される（手で変えていると3-wayマージ） |
| 仕組み（伝播） | `scripts/**` `.githooks/**` `.claude/commands/**` | テンプレ改善が反映される |
| 設定（保護） | `.docs-scaffold/config.sh` `.claude/settings.json` ルート `README.md` `CLAUDE.md` | **変更されない** |

実リポジトリでの検証結果: 利用者が書き換えた10ファイルすべてが更新後も保持され衝突0、
`_template.md` 2件と `validate-docs.py` にはテンプレ改善が反映された。

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
- **ERROR**（構造の破綻・push をブロック）: frontmatter 必須キー欠落 / `design_status` 不正値 / `ADR-`・`SCR-`・`API-` の dangling 参照 / 対応表と個票の双方向不一致 / ADR 本体と `docs/adr/README.md` 一覧の双方向不一致・ステータス食い違い
- **WARN**（表示のみ）: プレースホルダ未置換（`YYYY-MM-DD` 等） / 画像リンク切れ / `docs/rdra/` に定義の無い `UC-` 参照
- pre-push から自動実行される。一時回避は `DOCS_VALIDATE_SOFT=1 git push` または `git push --no-verify`
- 依存は python3 のみ（未検出なら検査をスキップして push を通す）

## リポジトリ構成
- `template/` … 利用者へ展開される本体（copier の `_subdirectory`）
- `copier.yml` … 質問・`_tasks`・上書き保護の定義
- `meta/` … **テンプレート自体の資料**（ライフサイクルのシーケンス図など）。展開先には配布されない。詳細は [`meta/README.md`](meta/README.md)

## 特徴
- `scripts/docs-validate/validate-docs.py` で docs の構造整合を機械検査（pre-push でブロック）
- 人が書く docs は `_skip_if_exists` で保護され、`copier update` で衝突しない（伝播するのは仕組みと `_template.md` 系だけ）
- git フックは `.githooks/` に置き `.git/hooks` を汚さない。husky / lefthook 併用時は `core.hooksPath` を奪わず、各管理ツールから呼ぶ形で配線する
- `.copier-answers.yml` に版を記録し `copier update` で3-wayマージ追従
