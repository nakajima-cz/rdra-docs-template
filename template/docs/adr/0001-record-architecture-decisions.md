# ADR-0001: Record architecture decisions

- ステータス: Accepted
- 日付: YYYY-MM-DD

## コンテキスト
設計判断の根拠(Why)が各設計書に散在すると重複・食い違いが起きる。

## 決定
アーキテクチャ上重要な判断は ADR として `docs/adr/` に連番で記録する。

## 理由
- Why を単一情報源に集約し、設計書は What/How に専念できる
- 判断の履歴（変更・棄却）を追える

## 影響
- 各設計書は判断根拠を `ADR-xxxx` で参照する
- 判断が覆る場合は新ADRを起こし旧ADRを Superseded にする
