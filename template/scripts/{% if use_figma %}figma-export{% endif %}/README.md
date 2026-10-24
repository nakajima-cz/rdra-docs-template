# figma-export

画面設計書(SCR-xxx)の frontmatter `figma_url` / `figma_node_id` から
FigmaのフレームをPNG書き出しして `docs/specs/screens/screenshots/` に保存する。

## 前提
- Figma個人アクセストークン: `export FIGMA_TOKEN=figd_xxx`
- 各SCR-xxx.md の frontmatter に figma_url と figma_node_id を記入済み

## 使い方
```
scripts/figma-export/export.sh SCR-001   # 特定画面
scripts/figma-export/export.sh           # 全SCR-*.md 一括
```
環境変数: `FIGMA_SCALE`（既定2）で書き出し倍率を調整。

## 挙動
- FIGMA_TOKEN 未設定・curl不在・node_id未設定は graceful skip（エラーで止めない）
- 保存名は `<SCR-ID>_default.png`（複数状態は手動で _error 等にリネーム運用）
