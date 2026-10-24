# 画面設計書（画面単位）

RDRA の画面一覧（rdra/03-boundary）と 1対1 で対応させる。
1ファイル=1画面。ファイル名: `SCR-xxx-<name>.md`。雛形は `_template.md`。

## 節構成（実運用フォーマット）
1. 基本情報（画面名/ID/パス/認証/レイアウト/SSR-SSG 等）
2. 操作権限（ユーザー×認証状態×動作）
3. 前提条件（環境変数・クエリ・ストレージ依存）
4. イベント一覧（採番ルールを明記）
5. イベント処理詳細（定義箇所・API通信表・エラー分岐）
6. 画面遷移（mermaid。流入元はGrep根拠を明記）
7. 状態管理（ローカルstate/グローバルstore/URLパラメータ）
8. 備考・要確認事項（デッドコード・未使用・要確認）
9. 画面レイアウト（screenshotリンク。リンク切れ検出用）
10. デザインレビュー履歴（Figma客先FBの結論・対応を記録）

## frontmatter
`source`（対応ソースパス）と `source_commit`（基づくgit SHA）を必須にする。
doc-sync はこの `source_commit` と現行HEADの差分を見て更新要否を判定する。

## デザイン(Figma)連携
- frontmatter に `figma_url` / `figma_node_id` / `design_status`(draft|in-review|approved) / `design_version` を持つ。
- 客先フィードバックは Figma に残し、結論だけを「10. デザインレビュー履歴」に転記。
- 確定画像は `scripts/figma-export/export.sh` で screenshots/ に取得（要 FIGMA_TOKEN）。
- design_status はマージをブロックしない（記録のみ）。ワークフロー全体は docs/WORKFLOW.md 参照。

## 原則
- Why はここに書かず ADR に集約し `ADR-xxxx` で参照。
- 共通仕様は転記せず docs/specs/common/ を「N節参照」で参照。
