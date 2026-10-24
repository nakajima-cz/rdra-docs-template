# プロジェクトドキュメント

このリポジトリのドキュメント全体の地図。上から下へ「なぜ→何を→どう」の順に辿れる。

## 構成
- `glossary.md` — 用語集 / ユビキタス言語（全ドキュメント整合の土台）
- `adr/` — 設計判断の記録（**なぜ / Why**）
- `rdra/` — 要件定義（RDRA 4レイヤー。**何を作るか / What**）
- `specs/` — 設計書（**どう作るか / How**）
  - `common/` — 横断規約の単一情報源（認証・エラー・命名等）
  - `screens/` — 画面設計書（画面単位）
  - `apis/` — 詳細設計書（API/エンドポイント単位）
- `traceability/` — 画面×UC×API 対応表（多対多を橋渡し）
- `assets/` — 図・画像の実体

## 整合性チェック
`python3 scripts/docs-validate/validate-docs.py` で docs/ の構造を検査する（`--json` / `--strict` あり）。
pre-push で自動実行され、ERROR があれば push がブロックされる（回避: `DOCS_VALIDATE_SOFT=1 git push`）。
- ERROR: frontmatter 必須キー欠落 / design_status 不正 / ID の dangling 参照 / 対応表と個票の不一致
- WARN: プレースホルダ未置換 / 画像リンク切れ / 未定義 UC 参照

## 読み方
1. `rdra/` で要件（What）を掴む
2. `specs/screens` `specs/apis` で設計（How）を見る
3. 判断根拠（Why）が知りたければ各所の `ADR-xxxx` 参照を辿る
4. 画面とAPIの対応は `traceability/screen-uc-api.md`

## ID規約
- 要求: `REQ-xxx` / ユースケース: `UC-xxx` / 情報: `INFO-xxx`
- 画面: `SCR-xxx` / API: `API-xxx` / 状態: `ST-xxx`
- 意思決定: `ADR-xxxx`
