# 共通エラー体系

## エラーレスポンス形式
```json
{ "code": "STRING", "message": "STRING", "details": [] }
```

## エラーコード一覧
| code | HTTP | 意味 |
|------|------|------|
| VALIDATION_ERROR | 400 | 入力検証エラー |
| UNAUTHORIZED | 401 | 未認証 |
| FORBIDDEN | 403 | 権限なし |
| NOT_FOUND | 404 | 対象なし |
| INTERNAL_ERROR | 500 | サーバ内部エラー |
