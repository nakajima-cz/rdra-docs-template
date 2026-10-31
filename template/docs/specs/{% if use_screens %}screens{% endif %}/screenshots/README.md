# screenshots

画面設計書（SCR-xxx）が参照する確定デザインのスクリーンショット置き場。

## 命名規約
`<SCR-ID>_<状態>.png`
- 例: `SCR-900_default.png`, `SCR-900_error.png`, `SCR-900_loading.png`
- 状態はイベント一覧・エラーハンドリングの表示パターンに対応させる

## 取得方法
- 手動: Figmaで該当フレームをPNG書き出しし、上記命名で保存
- 自動: `scripts/figma-export/export.sh <SCR-ID>` で対象specのfrontmatter figma_node_id から取得
