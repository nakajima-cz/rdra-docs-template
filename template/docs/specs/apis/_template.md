# API-XXX: <API名>

- エンドポイント: `METHOD /path`
- 対応UC: UC-xxx / 使用画面: SCR-xxx（対応表参照）
- 認証: 要/不要（common/auth.md）
- 権限: （common/auth.md）

## 概要
このAPIの責務。

## リクエスト
### パスパラメータ / クエリ
| 名前 | 型 | 必須 | 説明 |
|------|----|------|------|
### ボディ
```json
{}
```

## レスポンス
### 200
```json
{}
```
### エラー
common/error-handling.md 準拠。固有コードのみ以下に記載。

## バリデーション
common/validation.md 準拠。固有ルールのみ記載。

## 処理シーケンス / 副作用
- 参照/更新する情報: INFO-xxx
- 状態遷移: ST-xxx

## 関連
- ADR: ADR-xxxx（Why）
