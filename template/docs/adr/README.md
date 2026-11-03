# ADR (Architecture Decision Records)

設計判断の**なぜ(Why)**を集約する場所。設計書(specs)の個票には Why を書かず、ここへ集約し `ADR-xxxx` で参照する。

書式: Michael Nygard 提唱の連番方式（`NNNN-title.md`）。

## 一覧
| ID | タイトル | ステータス | 日付 |
|------|----------|-----------|------|
| ADR-0001 | Record architecture decisions | Accepted | YYYY-MM-DD |
| ADR-0002 | 要件定義に RDRA を採用 | Accepted | YYYY-MM-DD |

ステータス: Proposed / Accepted / Deprecated / Superseded by ADR-xxxx

この一覧は `validate-docs.py` が検査する。ADR 本体と一覧の行は**双方向で一致させる**
（本体があって行が無い／行があって本体が無い／ステータスの食い違い はいずれも ERROR）。
