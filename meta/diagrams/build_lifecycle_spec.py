#!/usr/bin/env python3
"""lifecycle-sequence.spec.json を組み立てる。

文言の直しは必ず来るので、JSON を手で編集せずこのスクリプトを直して再生成する。
番号（丸数字）とフレームの step インデックスは自動で振るので、step を途中へ
挿入しても手で数え直さなくてよい。

  python3 build_lifecycle_spec.py           # spec を書き出す
  python3 ../../../gen_sequence.py ...      # 実際の生成は run.sh 側
"""
import json
import pathlib

TEMPLATE_VERSION = "v2.1.0"

# ① から順に振る丸数字。50 まで。
CIRCLED = [chr(0x2460 + i) for i in range(20)] + [chr(0x3251 + i) for i in range(15)] \
          + [chr(0x32B1 + i) for i in range(15)]

_n = 0


def num():
    """呼ぶたびに次の丸数字を返す。"""
    global _n
    v = CIRCLED[_n]
    _n += 1
    return v


def call(f, t, label, kind="call"):
    return {"kind": kind, "from": f, "to": t, "num": num(), "label": label}


def ret(f, t, label):
    return call(f, t, label, kind="return")


def fail(f, t, label):
    return call(f, t, label, kind="fail")


def sep(label):
    return {"kind": "separator", "label": label, "span": ["user", "remote"]}


def note(span, color, text, width=430):
    return {"kind": "note", "span": span, "color": color, "text": text, "width": width}


participants = [
    {"id": "user", "label": "中嶋<br>(Slack)"},
    {"id": "hermes", "label": "Hermes<br>PMプロファイル"},
    {"id": "tmpl", "label": "rdra-docs-template<br>(copier テンプレ)"},
    {"id": "figma", "label": "Figma"},
    {"id": "coder", "label": "実装エージェント<br>Claude Code / Codex / Orca"},
    {"id": "repo", "label": "案件リポジトリ<br>docs/ · src/"},
    {"id": "hook", "label": "pre-push hook<br>docs-validate"},
    {"id": "remote", "label": "GitHub remote"},
]

steps = [
    # ───────────────────────── ① 展開
    sep("① 展開 — copier copy"),
    call("user", "hermes", "Slack: 案件を立ち上げて"),
    call("hermes", "tmpl", f"copier copy --trust --vcs-ref {TEMPLATE_VERSION}"),
    call("tmpl", "repo", "docs/ · scripts/ · .githooks/ を生成"),
    note(["tmpl", "repo"], "blue",
         "_tasks: install.sh {{ hook_manager }} / chmod +x<br>"
         "source_dirs・docs_sync_agent → .docs-scaffold/config.sh<br>"
         "components で画面spec・API個票・バッチ個票を取捨<br>"
         "impl_guide に実装規約リポジトリのURL（P05・P06 が参照）<br>"
         "_skip_if_exists: 人が書く docs は全部保護（更新で変わらない）"),
    call("tmpl", "hook", "scripts/docs-hooks/install.sh 〈hook_manager〉 で pre-push を配線"),
    note(["tmpl", "hook"], "green",
         "v1.6.0: hook_manager の回答で配線先が決まる（冪等）<br>"
         "none → core.hooksPath=.githooks<br>"
         "husky → .husky/pre-push へ1行追記（core.hooksPath は奪わない）<br>"
         "lefthook → lefthook.yml を作成して配線<br>"
         "既存の core.hooksPath / lefthook 設定がある場合は上書きせず手順表示のみ"),
    ret("repo", "hermes", "展開直後から validate-docs は ERROR 0"),

    # ───────────────────────── ② 要件定義
    sep("② 要件定義 — RDRA 4レイヤー（P01〜P03）"),
    call("user", "hermes", "Slackで壁打ち（要求・業務フロー・制約）"),
    note(["user", "hermes"], "green",
         "Slackのやり取りが意思決定の一次ソース。<br>"
         "結論だけを ADR-xxxx / rdra 配下へ転記し、<br>"
         "spec 本文には Why を書かず ID 参照に留める", width=330),
    call("hermes", "repo", "rdra/01-system-value: REQ-xxx・システムコンテキスト図"),
    call("hermes", "repo", "rdra/04-system: INFO-xxx 情報モデル・ST-xxx 状態モデル"),
    call("hermes", "repo", "rdra/03-boundary: UC-xxx / 画面一覧 SCR-xxx を採番"),
    ret("hermes", "user", "G1 要件FIX（人の承認ゲート）"),

    # ───────────────────────── ③ デザイン
    sep("③ デザイン — Figma 往復"),
    call("user", "hermes", "デザイン方針・客先要望"),
    call("hermes", "coder", "HTMLモック＋画面spec から Figma 起こしを指示"),
    call("coder", "figma", "generate_figma_design / use_figma（OAuth）"),
    ret("figma", "hermes", "客先レビュー指摘（やり取りは Figma に残す）"),
    note(["figma", "repo"], "yellow",
         "design_status: draft → in-review → approved<br>"
         "結論だけを SCR-xxx「10. デザインレビュー履歴」へ転記<br>"
         "合意後 export.sh(PAT read) で確定PNGを screenshots/ へ<br>"
         "※ ③④のフェーズは components に screens を含む案件のみ", width=400),
    call("hermes", "repo", "確定PNG取り込み・design_status: approved（G3 デザインFIX）"),

    # ───────────────────────── ④ 設計書
    sep("④ 設計書 — specs / traceability / ADR（P04）"),
    call("hermes", "repo", "specs/screens/SCR-xxx.md ・ specs/apis/API-xxx.md"),
    call("hermes", "repo", "traceability に行追加 ／ Why は ADR-xxxx へ集約"),

    # ───────────────────────── ⑤ ドメインモデリング（v2.1.0 新設）
    sep("⑤ ドメインモデリング — RDRA → DDD（P05・v2.1.0 で新設）"),
    call("hermes", "tmpl", "docs/prompts/p05-domain.md の4ステップを実行"),
    note(["tmpl", "repo"], "blue",
         "Step1 集約を切る: 状態を持つ INFO が集約ルート、残りはマスタ/VO/イベント記録へ<br>"
         "Step2 整合方式: 2つ以上の情報の状態を同時に変える UC を同一Tx／結果整合に振る<br>"
         "Step3 状態遷移: 状態モデルの (状態, UC) の組ごとに1行、ガード条件を引く<br>"
         "Step4 UseCase 対応: UC → UseCase、実装規約（impl_guide）の命名へ寄せる<br>"
         "RDRA に無いのは集約境界だけ。それがこのフェーズの主務", width=520),
    call("hermes", "repo", "docs/domain/README.md（集約・整合方式・遷移・UseCase対応）"),
    call("hermes", "repo", "ADR: 集約境界 ／ 集約をまたぐ整合方式"),
    note(["repo", "hook"], "yellow",
         "規約の正本は実装側リポジトリ（impl_guide）に置き、<br>"
         "テンプレは対応関係と参照先だけを持つ<br>"
         "読めない（未設定・404）ときは暫定名＋未決へ上げ、作業は止めない<br>"
         "新しい人のゲートは設けない — 完了時にまとめて承認", width=400),
    ret("hermes", "user", "集約の切り方・整合方式・未決事項をまとめて承認依頼"),

    # ───────────────────────── ⑥ 実装 → docs 同期
    sep("⑥ 実装 → docs 同期（P06 ハンドオフ）"),
    call("user", "hermes", "実装フェーズへ移行を指示"),
    call("hermes", "repo", "docs/prompts/p06-handoff.md: ロット L1..Ln へ分割"),
    note(["hermes", "repo"], "blue",
         "入力に docs/domain/README.md が入る（v2.1.0）<br>"
         "ロット＝実装担当へ渡す作業の単位、集約＝整合性を保つ範囲。軸が違う<br>"
         "1つの集約が複数ロットにまたがってよい（蔵書は L4・L5・L6）", width=430),
    call("hermes", "coder", "タスク委譲（Orca / Claude Code / Codex）"),
    call("coder", "repo", "DOCS_SOURCE_DIRS のディレクトリを変更（既定: src app lib api server packages）"),
    call("coder", "repo", "scripts/docs-sync/sync-docs.sh（DOCS_SYNC_AGENT で起動先を切替）"),
    note(["coder", "repo"], "blue",
         "差分を .docs-scaffold/last-diff.patch に書き出し、プロンプトから参照させる<br>"
         "DOCS_SYNC_AGENT: claude -p / codex exec / opencode run / 任意コマンド / none<br>"
         "frontmatter の source: が差分に含まれる spec の What/How のみ更新<br>"
         "対象 pathspec は DOCS_SOURCE_DIRS から生成（Go: cmd internal / monorepo: apps packages）<br>"
         "エージェント未インストール時は差分だけ出して exit 0（ブロックしない）", width=520),

    # ───────────────────────── ⑦ push ゲート
    sep("⑦ push — docs-validate ゲート"),
    call("coder", "hook", "git push（none=.githooks / husky=.husky / lefthook から同一スクリプト起動）"),
    call("hook", "repo", "validate-docs.py: frontmatter / ID参照 / 対応表の双方向突合"),
    fail("repo", "hook", "ERROR: dangling ADR-xxxx・対応表と個票の不一致"),
    fail("hook", "coder", "push 中止（exit 1）"),
    note(["hermes", "hook"], "red",
         "ERROR のみブロック。WARN（プレースホルダ・画像リンク切れ・<br>"
         "未定義UC）は表示のみ。緊急回避は DOCS_VALIDATE_SOFT=1 git push<br>"
         "／ git push --no-verify。python3 のみに依存しエージェント非依存<br>"
         "docs/domain/ の表は検査しない（ID の実在と ADR 索引の整合のみ）", width=340),
    call("coder", "repo", "/validate-docs で ERROR を修正しコミット"),
    call("hook", "remote", "ERROR 0 → push 実行"),
    ret("remote", "hermes", "リモート反映"),
    ret("hermes", "user", "Slackへ完了報告（差分・残WARN）"),

    # ───────────────────────── ⑧ テンプレ更新
    sep("⑧ テンプレ更新の追従"),
    {"kind": "note", "at": "tmpl", "color": "green", "width": 640,
     "text": "テンプレ側を改善し新タグを切る（最新: " + TEMPLATE_VERSION + "）<br>"
             "v1.6.0 hook_manager ／ v1.7.0 source_dirs ／ v1.8.0 components ／ "
             "v1.9.0 docs_sync_agent ／ v1.10.0 上書き保護の見直し<br>"
             "v2.0.0 フェーズ駆動の指示テンプレ（P01〜P05）／ "
             "v2.1.0 P05 ドメインモデリング新設・旧P05→P06 へ改称・impl_guide 追加<br>"
             "v2.1.0 の検証: 図書館システムで指示テンプレを14周実走し欠陥0件へ収束"},
    call("hermes", "tmpl", "copier update --trust"),
    call("tmpl", "repo", "伝播するのは scripts / .githooks / _template.md 系のみ"),
    ret("repo", "hermes", "validate-docs を再実行して整合を確認"),
]


def idx_of(label_part):
    """num ラベルではなく label の部分一致で step インデックスを引く。"""
    for i, s in enumerate(steps):
        if label_part in (s.get("label") or ""):
            return i
    raise KeyError(label_part)


spec = {
    "name": "rdra-docs-template ライフサイクル",
    "title": "rdra-docs-template リポジトリのライフサイクル（Hermes を含む役割分担）",
    "subtitle": (
        "出典: README.md / copier.yml / docs/prompts/p01-requirements.md〜p06-handoff.md / "
        "docs/domain/README.md / scripts/docs-hooks/install.sh / .docs-scaffold/config.sh / "
        ".githooks/pre-push / scripts/docs-sync/sync-docs.sh / "
        f"scripts/docs-validate/validate-docs.py（{TEMPLATE_VERSION} 時点）"
    ),
    "font": "Hiragino Sans",
    "participants": participants,
    "steps": steps,
    "frames": [{
        "label": "loop [ERROR 0 になるまで]",
        "from_step": idx_of("git push（none=.githooks"),
        "to_step": idx_of("/validate-docs で ERROR を修正しコミット"),
        "left": "hermes", "right": "hook",
    }],
    "legend": [
        {"color": "green", "text": "リポジトリ内の実ファイル・実コマンドで確認済み"},
        {"color": "blue", "text": "設定/スクリプト・指示テンプレ由来（copier.yml・docs/prompts/）"},
        {"color": "yellow", "text": "WORKFLOW.md の運用規約（人手の運用）"},
        {"color": "red", "text": "検証 ERROR・push ブロック"},
    ],
}

out = pathlib.Path(__file__).with_name("lifecycle-sequence.spec.json")
out.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {out}  steps={len(steps)}  numbered={_n}  frame={spec['frames'][0]}")
