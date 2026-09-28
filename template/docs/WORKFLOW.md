# 設計ワークフロー（RDRA → Figma → 画面設計 → API設計）

要件から実装可能なドキュメントに落とすまでの標準手順。各成果物の置き場所と、
デザインのフィードバックループの回し方を定める。

## 全体フロー

1. **RDRA で画面一覧を確定** — `rdra/03-boundary/`
   - どの画面が必要か＋UC対応だけを決める（中身はまだ不要）。画面IDを採番（SCR-xxx）。

2. **Figma でデザインモック作成**（画面ごと、Figmaが唯一の正）
   - ワイヤーフレーム（要素・配置）→ ビジュアルモック（色・トンマナ確定）の2段階。
   - 各画面設計書 `specs/screens/SCR-xxx.md` の frontmatter に `figma_url` / `figma_node_id` を記入し、`design_status: draft` にする。

3. **客先レビュー**（Figmaのコメント機能でフィードバックを受ける）
   - `design_status: in-review` に更新。
   - やり取り自体はFigmaに残す。**結論だけ**を SCR-xxx の「10. デザインレビュー履歴」に転記する。

4. **フィードバック取り込み → Figma更新**（ループ）
   - Figmaを修正し、`design_version` を更新。履歴表に「反映/見送り(理由)/要確認」を記録。
   - 合意が取れたら `design_status: approved`。

5. **確定デザインの画像を取り込み** — `specs/screens/screenshots/`
   - `scripts/figma-export/export.sh SCR-xxx`（要 FIGMA_TOKEN）でPNG自動取得、またはFigmaから手動書き出し。
   - 命名: `<SCR-ID>_<状態>.png`。

6. **画面設計書を記述** — `specs/screens/SCR-xxx.md`
   - approved なモックを見ながら 9節（基本情報〜画面レイアウト）を埋める。

7. **API詳細設計書を記述** — `specs/apis/API-xxx.md`
   - 画面の「5. イベント処理詳細」で出たAPIを起点に設計。`traceability/screen-uc-api.md` で画面↔UC↔APIを突合。

## design_status の意味（記録のみ・マージはブロックしない）

| 状態 | 意味 |
|------|------|
| draft | モック作成中・社内検討段階 |
| in-review | 客先レビュー中（フィードバック待ち） |
| approved | 客先合意済み。画面設計書の記述・実装に進んでよい |

注: 本テンプレでは design_status はマージ条件に**絡めない**（情報として持つだけ）。
運用が固まったら pre-push 警告や CI ガードへ格上げ可能。

## Why の扱い

設計判断の「なぜ」は各specに書かず `adr/` に集約し、spec からは `ADR-xxxx` で参照する。
デザイン上の重要判断（IA・主要導線の決定理由など）も ADR に残すとトレースが切れない。
