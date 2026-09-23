# API-001: ログイン

- エンドポイント: `POST /auth/login`
- 対応UC: UC-001 / 使用画面: SCR-001
- 認証: 不要
- 権限: なし

## 概要
資格情報を検証しアクセストークンを発行する。

## リクエスト
### ボディ
```json
{ "email": "string", "password": "string" }
```

## レスポンス
### 200
```json
{ "accessToken": "string", "expiresIn": 3600 }
```
### エラー
- 401 UNAUTHORIZED: 資格情報不一致（common/error-handling.md）

## バリデーション
- email/password: common/validation.md

## 処理シーケンス / 副作用
- 参照する情報: INFO-001（ユーザー）
- 副作用: なし（トークン発行のみ）

## 関連
- ADR: -
