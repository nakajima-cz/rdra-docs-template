#!/usr/bin/env python3
"""P01 ゲートの追加検査: docs/p00-brief.md「4. 確定していること」と REQ の突き合わせ。

validate-docs.py は ID の実在と ADR 整合は見るが、「4節の各項目が要求として
採番されているか／要求ではないと注記されているか」は見ない（4節と REQ 表は別ファイルに
あり、文面の対応づけ自体は機械では決められないため）。

この検査が見るのは、文面の対応づけではなく「注記の有無」という機械で測れる部分だけ。
運用規約（docs/prompts/p01-requirements.md 着手前チェック チェック2）により、
4節の各行の行末には次のどちらかが付いている必要がある。

  （REQ-xxx）            ... 要求として採番済み
  （要求ではない: 理由） ... 要求として振らないと決めた理由

差し戻しのたびに4節へ項目が増えるのに、再実行の指示が「今回反映する決定」だけを
見て4節全体を読み直さないと、この注記が付かないまま項目が残る。これは実測で
複数回（5回の差し戻しのうち2回）再発した欠落の型であり、文面の対応づけを機械化
できない以上、注記という運用規約のほうを機械で強制する。

使い方:
  python3 scripts/docs-validate/check-p01-gates.py
  python3 scripts/docs-validate/check-p01-gates.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 行末の注記。全角/半角の括弧どちらも許す。
ANNOTATION_RE = re.compile(
    r"[\(（]\s*(?:REQ-\d{3,}|要求ではない\s*[:：].+?)\s*[\)）]\s*$"
)
SECTION4_HEADING_RE = re.compile(r"^##\s*4\.\s*確定していること")
NEXT_HEADING_RE = re.compile(r"^##\s")
BULLET_RE = re.compile(r"^\s*-\s+(.*)$")
PLACEHOLDER_ITEMS = {"（未記入）", "(未記入)", "未記入"}


def extract_section4_items(text: str) -> list[str]:
    """「## 4. 確定していること」セクション直下の箇条書き本文を返す。"""
    lines = text.splitlines()
    in_section = False
    items: list[str] = []
    for line in lines:
        if SECTION4_HEADING_RE.match(line):
            in_section = True
            continue
        if in_section and NEXT_HEADING_RE.match(line):
            break
        if not in_section:
            continue
        m = BULLET_RE.match(line)
        if m:
            items.append(m.group(1).strip())
    return items


def check_req_annotations(brief: Path) -> list[str]:
    if not brief.exists():
        return []
    text = brief.read_text(encoding="utf-8")
    errors: list[str] = []
    for item in extract_section4_items(text):
        if not item.strip() or item in PLACEHOLDER_ITEMS:
            continue
        if ANNOTATION_RE.search(item):
            continue
        errors.append(
            "4節の項目に REQ 番号も「要求ではない」注記も付いていません: "
            f"「{item}」（行末に `（REQ-xxx）` または `（要求ではない: 理由）` を追記する）"
        )
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(
        description="P01 ゲートの追加検査（4節 ↔ REQ の突き合わせ）"
    )
    ap.add_argument("--docs", default="docs", help="docs ディレクトリ（既定: docs）")
    ap.add_argument("--json", action="store_true", help="JSON で出力する")
    args = ap.parse_args()

    docs = Path(args.docs).resolve()
    brief = docs / "p00-brief.md"
    errors = check_req_annotations(brief)

    rel = "docs/p00-brief.md"
    if args.json:
        print(
            json.dumps(
                {"ok": not errors, "counts": {"error": len(errors)}, "errors": errors},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for e in errors:
            print(f"ERROR {rel}: {e}")
        print(f"check-p01-gates: ERROR {len(errors)}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
