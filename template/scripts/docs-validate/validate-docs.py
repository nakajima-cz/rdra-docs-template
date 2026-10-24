#!/usr/bin/env python3
"""docs-scaffold: docs/ の構造整合を検査する。

検査対象は docs/ 配下のみ。コードの正しさは見ない（spec 同士・ID 参照の整合のみ）。

ERROR (exit 1): 構造の破綻。frontmatter 必須キー欠落 / design_status 不正 /
                ID の dangling 参照 / traceability との不一致。
WARN  (exit 0): 埋め忘れ。プレースホルダ未置換 / 画像リンク切れ / UC 未定義。

使い方:
  python3 scripts/docs-validate/validate-docs.py
  python3 scripts/docs-validate/validate-docs.py --json
  python3 scripts/docs-validate/validate-docs.py --strict   # WARN も exit 1
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---- 設定 ----------------------------------------------------------------

REQUIRED_FRONTMATTER = {
    "screen": ["source", "updated", "source_commit", "design_status"],
    "api": ["source", "updated"],
}
DESIGN_STATUS_VALUES = {"draft", "in-review", "approved"}

# 未置換のプレースホルダとみなすパターン
PLACEHOLDER_RE = re.compile(r"^\s*(YYYY-MM-DD|<[^>]*>|TBD|TODO)\s*$", re.IGNORECASE)

ID_PATTERNS = {
    "SCR": re.compile(r"\bSCR-(\d{3,})\b"),
    "API": re.compile(r"\bAPI-(\d{3,})\b"),
    "UC": re.compile(r"\bUC-(\d{3,})\b"),
    "ADR": re.compile(r"\bADR-(\d{4,})\b"),
}
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


class Report:
    def __init__(self) -> None:
        self.errors: list[dict] = []
        self.warns: list[dict] = []

    def error(self, path: str, msg: str) -> None:
        self.errors.append({"level": "error", "file": path, "message": msg})

    def warn(self, path: str, msg: str) -> None:
        self.warns.append({"level": "warn", "file": path, "message": msg})


# ---- ユーティリティ -------------------------------------------------------


def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """最小限の YAML frontmatter パーサ（key: value のみ。ネストは無視）。"""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end]
    body = text[end + 4 :]
    fm: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t", "-")):  # リスト要素（tags 等）はスキップ
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        fm[key.strip()] = value.split("#", 1)[0].strip()
    return fm, body


def strip_code_and_comments(text: str) -> str:
    """ID 参照の誤検出を避けるため、コードブロックと HTML コメントを除去する。"""
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return text


def ids_in(text: str, kind: str) -> set[str]:
    return {f"{kind}-{m}" for m in ID_PATTERNS[kind].findall(text)}


# ---- 検査本体 -------------------------------------------------------------


def collect_defined_ids(docs: Path) -> dict[str, set[str]]:
    """ファイル名・見出しから「定義済み」とみなせる ID を集める。"""
    defined: dict[str, set[str]] = {"SCR": set(), "API": set(), "UC": set(), "ADR": set()}

    for f in sorted((docs / "specs" / "screens").glob("SCR-*.md")):
        m = re.match(r"(SCR-\d{3,})", f.name)
        if m:
            defined["SCR"].add(m.group(1))
    for f in sorted((docs / "specs" / "apis").glob("API-*.md")):
        m = re.match(r"(API-\d{3,})", f.name)
        if m:
            defined["API"].add(m.group(1))
    for f in sorted((docs / "adr").glob("[0-9]*.md")):
        m = re.match(r"(\d{4,})", f.name)
        if m:
            defined["ADR"].add(f"ADR-{m.group(1)}")
    # UC は RDRA 03-boundary 配下で定義される（ファイル or 表の行）
    rdra = docs / "rdra"
    if rdra.is_dir():
        for f in rdra.rglob("*.md"):
            defined["UC"] |= ids_in(strip_code_and_comments(f.read_text(encoding="utf-8")), "UC")
    return defined


def check_spec(path: Path, kind: str, rel: str, rep: Report) -> None:
    text = path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)

    if not fm:
        rep.error(rel, "frontmatter がありません（--- で囲まれた先頭ブロックが必要）")
        return

    for key in REQUIRED_FRONTMATTER[kind]:
        if key not in fm:
            rep.error(rel, f"frontmatter に必須キー `{key}` がありません")
        elif fm[key] == "":
            rep.warn(rel, f"frontmatter `{key}` が空です")
        elif PLACEHOLDER_RE.match(fm[key]):
            rep.warn(rel, f"frontmatter `{key}` がプレースホルダのままです: {fm[key]}")

    status = fm.get("design_status", "")
    if kind == "screen" and status and not PLACEHOLDER_RE.match(status):
        if status not in DESIGN_STATUS_VALUES:
            rep.error(
                rel,
                f"design_status が不正です: `{status}`（許可値: {'/'.join(sorted(DESIGN_STATUS_VALUES))}）",
            )

    # 画像リンク切れ
    for link in IMAGE_RE.findall(body):
        if link.startswith(("http://", "https://", "data:")):
            continue
        if not (path.parent / link).exists():
            rep.warn(rel, f"画像リンク切れ: {link}")


def check_traceability(docs: Path, defined: dict[str, set[str]], rep: Report) -> None:
    tr = docs / "traceability" / "screen-uc-api.md"
    rel = str(tr.relative_to(docs.parent))
    if not tr.exists():
        rep.error(rel, "対応表が存在しません")
        return

    text = strip_code_and_comments(tr.read_text(encoding="utf-8"))
    listed_scr = ids_in(text, "SCR")
    listed_api = ids_in(text, "API")

    for missing in sorted(listed_scr - defined["SCR"]):
        rep.error(rel, f"{missing} が対応表にあるが docs/specs/screens/{missing}-*.md が存在しません")
    for missing in sorted(listed_api - defined["API"]):
        rep.error(rel, f"{missing} が対応表にあるが docs/specs/apis/{missing}-*.md が存在しません")
    for orphan in sorted(defined["SCR"] - listed_scr):
        rep.error(rel, f"{orphan} の設計書があるが対応表に行がありません")
    for orphan in sorted(defined["API"] - listed_api):
        rep.error(rel, f"{orphan} の設計書があるが対応表に行がありません")
    for uc in sorted(ids_in(text, "UC") - defined["UC"]):
        rep.warn(rel, f"{uc} が対応表にあるが docs/rdra/ 配下に定義が見つかりません")


def check_references(docs: Path, defined: dict[str, set[str]], rep: Report) -> None:
    """docs 全体の ADR-/SCR-/API- 参照が実在するかを見る。"""
    skip_names = {"_template.md", "template.md"}
    traceability = docs / "traceability" / "screen-uc-api.md"
    for f in sorted(docs.rglob("*.md")):
        if f.name in skip_names or f == traceability:
            continue  # 対応表は check_traceability で見るので二重報告しない
        rel = str(f.relative_to(docs.parent))
        text = strip_code_and_comments(f.read_text(encoding="utf-8"))
        for kind in ("ADR", "SCR", "API"):
            for ref in sorted(ids_in(text, kind) - defined[kind]):
                rep.error(rel, f"{ref} を参照していますが実体が存在しません")
        # UC は docs/rdra/ 側の記述揺れがありうるので WARN 止まり
        if f.parent.name != "rdra" and "rdra" not in f.parts:
            for ref in sorted(ids_in(text, "UC") - defined["UC"]):
                rep.warn(rel, f"{ref} を参照していますが docs/rdra/ 配下に定義が見つかりません")


def main() -> int:
    ap = argparse.ArgumentParser(description="docs/ の構造整合を検査する")
    ap.add_argument("--docs", default="docs", help="docs ディレクトリ（既定: docs）")
    ap.add_argument("--json", action="store_true", help="JSON で出力する")
    ap.add_argument("--strict", action="store_true", help="WARN も失敗扱いにする")
    args = ap.parse_args()

    docs = Path(args.docs).resolve()
    rep = Report()

    if not docs.is_dir():
        print(f"docs-validate: {docs} が見つかりません", file=sys.stderr)
        return 2

    defined = collect_defined_ids(docs)

    for f in sorted((docs / "specs" / "screens").glob("SCR-*.md")):
        check_spec(f, "screen", str(f.relative_to(docs.parent)), rep)
    for f in sorted((docs / "specs" / "apis").glob("API-*.md")):
        check_spec(f, "api", str(f.relative_to(docs.parent)), rep)

    check_traceability(docs, defined, rep)
    check_references(docs, defined, rep)

    if args.json:
        print(
            json.dumps(
                {
                    "ok": not rep.errors and (not rep.warns or not args.strict),
                    "counts": {"error": len(rep.errors), "warn": len(rep.warns)},
                    "findings": rep.errors + rep.warns,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for item in rep.errors:
            print(f"ERROR {item['file']}: {item['message']}")
        for item in rep.warns:
            print(f"WARN  {item['file']}: {item['message']}")
        total = (
            f"docs-validate: ERROR {len(rep.errors)} / WARN {len(rep.warns)}"
            f"（検査: {len(defined['SCR'])} screens, {len(defined['API'])} apis,"
            f" {len(defined['ADR'])} adr, {len(defined['UC'])} uc）"
        )
        print(total)

    if rep.errors:
        return 1
    if args.strict and rep.warns:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
