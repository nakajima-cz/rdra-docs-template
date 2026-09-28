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

## デザイン作成フェーズの認証境界（重要）

Figmaへの「作成・編集（アートボード生成）」は REST API/個人アクセストークン(PAT)ではできない。
PATは**読み取り専用**（画像export・コメント・変数read程度）。キャンバスへ書けるのは次の2経路のみ:
- Plugin API（Figma Desktop内・単一ユーザー・ヘッドレス不可）
- Figma MCP server の `generate_figma_design` / `use_figma`（allowlist済みMCPクライアント限定・アカウント単位の対話OAuth・Dev/Fullシート・将来有料）

このため役割ごとに操作を分ける（認証境界を崩さないため）:

| 役割 | Figma認証 | やること |
|------|-----------|---------|
| Designer（共通プロファイル） | **持たない** | HTMLモック案(claude-design/sketch)＋画面specの作成まで。Figmaは触らない |
| 実装エージェント層（Claude Code / Codex） | **Figma MCP(OAuth)を接続** | モックFIX後、HTML+specからFigmaアートボードを生成・編集 |
| PM（案件別プロファイル） | PAT(read) | 実装エージェントにFigma起こしを指示・駆動。export.shで画像取得 |

- Figma MCPのOAuthは**案件ごとのFigmaアカウント**で行う。共通Designerには絶対に載せない（1アカウント固定で案件別分離が壊れる）。
- OAuthは初回にブラウザ同意が1回必要（完全ヘッドレスにはならない）。

## デザイン作成の流れ（モックFIX → agentがFigma化）

1. Designer が HTMLモック案（claude-design / sketch）＋画面spec を作成 → 客先レビュー → **モックFIX**
2. PM が実装エージェント層（Claude Code / Codex）に「このHTMLモック＋specでFigmaに起こして」と指示
3. 実装エージェントが Figma MCP `generate_figma_design`（HTML→編集可能レイヤー変換）→ 必要なら `use_figma`（デザインシステムのcomponent/variableで調整）でアートボード生成
4. 生成後 `design_status: approved`、`export.sh`（PAT read）で確定画像を screenshots/ に取得 → 画面設計書9節へ

補足: HTMLモック起点にしているため `generate_figma_design` への変換コストが低い。逆順（先にFigmaを作る）にしないのが肝。

## Why の扱い

設計判断の「なぜ」は各specに書かず `adr/` に集約し、spec からは `ADR-xxxx` で参照する。
デザイン上の重要判断（IA・主要導線の決定理由など）も ADR に残すとトレースが切れない。
