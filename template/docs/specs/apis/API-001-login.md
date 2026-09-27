---
tags:
  - api-design
  - backend
  - account
source: src/handlers/account/login
updated: YYYY-MM-DD
---

# 詳細設計書 - ユーザーログイン

> **注記**: ファイルパス・行番号は updated 時点のソースに基づく。

## 1. 基本情報

| 項目 | 内容 |
|------|------|
| 機能名 | ユーザーログイン |
| ハンドラ/関数 | LoginHandler |
| エントリポイント | `src/handlers/account/login` |
| HTTPメソッド / パス | POST /api/d/account/login |
| 認証 | 不要 |

## 2. Input

### リクエストヘッダー
| ヘッダー | 必須 | 値 | 備考 |
|---------|------|-----|------|
| Content-Type | ○ | application/json | |

### パスパラメータ
なし

### クエリパラメータ
なし

### リクエストボディ
| フィールド | 型 | 必須 | 制約 | 説明 | 検証箇所 |
|-----------|-----|------|------|------|---------|
| username | String | ○ | メール形式 | ログインID | JSONスキーマ |
| password | String | ○ | — | パスワード | JSONスキーマ |

リクエスト例:
```json
{ "username": "user@example.com", "password": "P@ssw0rd" }
```

### 暗黙的Input（リクエスト外から取得）
| データ | 取得元 | 用途 | 取得箇所 |
|--------|-------|------|---------|
| client_ip | リクエストコンテキスト | 検証のリモートIP | handler |

## 3. Output

### 成功レスポンス (200)
| フィールド | 型 | 説明 | 生成箇所 |
|-----------|-----|------|---------|
| message | String | "success" | handler |
| session | String | セッション | handler |

レスポンス例:
```json
{ "message": "success", "session": "..." }
```

### エラーレスポンス
| ステータス | レスポンス | 発生条件 | 発生箇所 |
|-----------|-----------|---------|---------|
| 400 | Bad request | バリデーション不合格 | handler |
| 401 | Invalid username or password | 認証失敗 | handler |
| 423 | Account is locked | アカウントロック | handler |

### バリデーション詳細
| # | チェック内容 | 条件 | 失敗時の処理 | 参照データ | 箇所 |
|---|------------|------|------------|----------|------|
| 1 | JSONスキーマ検証 | 不合格 | 400 | login_schema.json | handler |

### 副作用（DB・キュー等への出力）
なし

## 4. 処理フロー

### 4.1 バリデーション
`src/handlers/account/login`
- リクエストボディをJSONスキーマで検証

### 4.2 認証
`src/handlers/account/login`
- 認証基盤で username/password を検証しセッションを取得

## 5. 依存関係

### DB操作
なし

### 共通ライブラリ
| モジュール | 用途 | パス |
|-----------|------|------|
| | | |

### 外部連携
| 連携先 | 種別 | 内容 | 箇所 |
|--------|------|------|------|
| 認証基盤 | API | 認証 | handler |

## 6. 備考・要確認事項

- 対応画面: SCR-001（対応表: ../../traceability/screen-uc-api.md）
