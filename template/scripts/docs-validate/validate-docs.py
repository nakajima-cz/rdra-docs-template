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

# 対応表のファイル名候補（先に見つかった方を使う）
TRACEABILITY_NAMES = ("screen-uc-api.md", "uc-api.md")

# 未置換のプレースホルダとみなすパターン
PLACEHOLDER_RE = re.compile(r"^\s*(YYYY-MM-DD|<[^>]*>|TBD|TODO)\s*$", re.IGNORECASE)

ID_PATTERNS = {
    "SCR": re.compile(r"\bSCR-(\d{3,})\b"),
    "API": re.compile(r"\bAPI-(\d{3,})\b"),
    "UC": re.compile(r"\bUC-(\d{3,})\b"),
    "ADR": re.compile(r"\bADR-(\d{4,})\b"),
}
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")

# ID の直後に書かれた名称を拾うためのパターン
#   セル内併記: | UC-001 会員を登録する | ...
# 先頭列からの採用は「2列目が名称列である表」に限る（下の NAME_HEADER_RE を参照）。
# 地の文（「UC-001 の扱いを決めた」等）は名称の定義とみなさない。誤検出の元になるため。
NAME_CELL_RE = r"\|\s*{id}[ \u3000]+([^|]+?)\s*\|"

# 「2列目が名称列」と判定するヘッダ（これ以外の補助表は名称の定義元とみなさない）
NAME_HEADER_RE = re.compile(r"^(名称|名前|.*名)$")
ID_HEADER_RE = re.compile(r"(ID|Id|id)$|^(UC|画面|情報|状態|API|要求)$")

# 名称として採用しない先頭文字列（助詞などで始まるものは説明文であって名称ではない）
NAME_REJECT_PREFIX = (
    "と", "は", "が", "を", "に", "の", "や", "も", "へ", "で", "から", "まで",
    "および", "及び", "または", "等", "など", "について", "により", "による",
)

# 名称として採用しない末尾文字（助詞で終わるものは文の一部であって名称ではない）
NAME_REJECT_SUFFIX = ("は", "が", "を", "に", "へ", "と", "も", "や", "で", "の", "から", "まで")


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


def traceability_path(docs: Path) -> Path:
    """対応表のパス。画面ありは screen-uc-api.md、画面なし構成は uc-api.md。"""
    for name in TRACEABILITY_NAMES:
        p = docs / "traceability" / name
        if p.exists():
            return p
    return docs / "traceability" / TRACEABILITY_NAMES[0]


def check_traceability(docs: Path, defined: dict[str, set[str]], rep: Report) -> None:
    tr = traceability_path(docs)
    rel = str(tr.relative_to(docs.parent))
    if not tr.exists():
        rep.error(rel, f"対応表が存在しません（{' または '.join(TRACEABILITY_NAMES)}）")
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


ADR_STATUS_RE = re.compile(r"^-\s*(?:ステータス|Status)\s*[:：]\s*(.+?)\s*$", re.MULTILINE)
STATUS_HEADER_RE = re.compile(r"^(ステータス|Status|状態)$", re.IGNORECASE)


def adr_index_path(docs: Path) -> Path:
    return docs / "adr" / "README.md"


def adr_status_of(path: Path) -> str:
    """ADR 本体の `- ステータス: X` を返す（取れなければ空文字）。"""
    m = ADR_STATUS_RE.search(strip_code_and_comments(path.read_text(encoding="utf-8")))
    return normalize_status(m.group(1)) if m else ""


def normalize_status(raw: str) -> str:
    """比較用にステータスを正規化する。雛形の選択肢列挙（`A | B | C`）は比較対象外。"""
    s = " ".join(raw.replace("**", "").split()).strip()
    if "|" in s or "/" in s or PLACEHOLDER_RE.match(s):
        return ""
    return s


def iter_adr_index_rows(text: str):
    """ADR 一覧表の (ID セル, ステータスセル) を列挙する。

    ヘッダに ID 列とステータス列がある表だけを一覧とみなす。列順は固定しない。
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if not lines[i].lstrip().startswith("|"):
            i += 1
            continue
        block = []
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            block.append(lines[i])
            i += 1
        if len(block) < 3:
            continue
        header = [c.strip() for c in block[0].strip().strip("|").split("|")]
        if not ID_HEADER_RE.search(header[0]):
            continue
        status_col = next(
            (n for n, h in enumerate(header) if STATUS_HEADER_RE.match(h)), None
        )
        for row in block[2:]:
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            if not cells:
                continue
            status = cells[status_col] if status_col is not None and status_col < len(cells) else ""
            yield cells[0], status


def check_adr_index(docs: Path, defined: dict[str, set[str]], rep: Report) -> None:
    """docs/adr/README.md の一覧と ADR 本体を双方向で突き合わせる。

    索引を更新しない ADR は、読み手から見れば存在しないのと同じ。ステータスの
    食い違い（本体が Superseded なのに一覧が Accepted のまま）も同じ理由で ERROR。
    """
    idx = adr_index_path(docs)
    if not idx.exists():
        if defined["ADR"]:
            rep.error("docs/adr/README.md", "ADR の一覧（README.md）が存在しません")
        return

    rel = str(idx.relative_to(docs.parent))
    text = strip_code_and_comments(idx.read_text(encoding="utf-8"))

    listed: dict[str, str] = {}
    for id_cell, status_cell in iter_adr_index_rows(text):
        m = ID_PATTERNS["ADR"].search(id_cell)
        if m:
            listed[f"ADR-{m.group(1)}"] = normalize_status(status_cell)

    files = {
        f"ADR-{m.group(1)}": f
        for f in sorted((docs / "adr").glob("[0-9]*.md"))
        if (m := re.match(r"(\d{4,})", f.name))
    }

    for missing in sorted(set(listed) - set(files)):
        rep.error(rel, f"{missing} が一覧にあるが docs/adr/{missing[4:]}-*.md が存在しません")
    for orphan in sorted(set(files) - set(listed)):
        rep.error(rel, f"{orphan} の本体があるが一覧に行がありません")

    for ident in sorted(set(listed) & set(files)):
        want = listed[ident]
        got = adr_status_of(files[ident])
        if want and got and want != got:
            rep.error(
                rel,
                f"{ident} のステータスが一覧と本体で一致しません: 一覧 `{want}` / 本体 `{got}`",
            )


def check_references(docs: Path, defined: dict[str, set[str]], rep: Report) -> None:
    """docs 全体の ADR-/SCR-/API- 参照が実在するかを見る。"""
    skip_names = {"_template.md", "template.md"}
    traceability = traceability_path(docs)
    adr_index = adr_index_path(docs)
    for f in sorted(docs.rglob("*.md")):
        if f.name in skip_names or f == traceability or f == adr_index:
            continue  # 対応表と ADR 一覧は専用チェックで見るので二重報告しない
        rel = str(f.relative_to(docs.parent))
        text = strip_code_and_comments(f.read_text(encoding="utf-8"))
        for kind in ("ADR", "SCR", "API"):
            for ref in sorted(ids_in(text, kind) - defined[kind]):
                rep.error(rel, f"{ref} を参照していますが実体が存在しません")
        # UC は docs/rdra/ 側の記述揺れがありうるので WARN 止まり
        if f.parent.name != "rdra" and "rdra" not in f.parts:
            for ref in sorted(ids_in(text, "UC") - defined["UC"]):
                rep.warn(rel, f"{ref} を参照していますが docs/rdra/ 配下に定義が見つかりません")


def iter_name_tables(text: str):
    """「1列目が ID 列、2列目が名称列」の表だけを取り出し、(ID セル, 名称セル) を列挙する。

    補助表（`| UC | 入力となる画面 |` など ID を先頭列に置くが2列目が名称でない表）を
    名称の定義元と誤認しないため、ヘッダ行を見て判定する。
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if not lines[i].lstrip().startswith("|"):
            i += 1
            continue
        block = []
        while i < len(lines) and lines[i].lstrip().startswith("|"):
            block.append(lines[i])
            i += 1
        if len(block) < 3:
            continue
        header = [c.strip() for c in block[0].strip().strip("|").split("|")]
        if len(header) < 2:
            continue
        if not (ID_HEADER_RE.search(header[0]) and NAME_HEADER_RE.match(header[1])):
            continue
        for row in block[2:]:
            cells = [c.strip() for c in row.strip().strip("|").split("|")]
            if len(cells) >= 2:
                yield cells[0], cells[1]


def check_id_names(docs: Path, rep: Report) -> None:
    """同じ ID が別々の名称で書かれていないかを検査する。

    ID の存在だけを見ていると、採番し直したときに対応表と定義で指す対象がずれても
    気づけない（対応表の `UC-001 認証する` と定義の `UC-001 会員を登録する` が共存しうる）。
    初出の名称を正本とし、食い違う名称を ERROR にする。
    """
    skip_names = {"_template.md", "template.md"}
    # id -> 名称 -> 最初に見つかった "ファイル" の表示名
    names: dict[str, dict[str, str]] = {}

    for f in sorted(docs.rglob("*.md")):
        if f.name in skip_names:
            continue
        rel = str(f.relative_to(docs.parent))
        text = strip_code_and_comments(f.read_text(encoding="utf-8"))

        # 1) 「ID 列 + 名称列」の表から拾う
        table_names: dict[str, set[str]] = {}
        for id_cell, name_cell in iter_name_tables(text):
            for kind, pattern in ID_PATTERNS.items():
                m = pattern.fullmatch(id_cell.strip())
                if m:
                    name = normalize_name(name_cell)
                    if name:
                        table_names.setdefault(f"{kind}-{m.group(1)}", set()).add(name)
                    break

        for kind in ID_PATTERNS:
            for num in sorted(set(ID_PATTERNS[kind].findall(text))):
                ident = f"{kind}-{num}"
                found = sorted(table_names.get(ident, ()))
                if not found:
                    # 表で取れなかったときだけ、セル内併記（| UC-001 名称 |）を見る
                    found = [
                        n
                        for n in (
                            normalize_name(raw)
                            for raw in re.findall(
                                NAME_CELL_RE.format(id=re.escape(ident)), text
                            )
                        )
                        if n
                    ]
                for name in found:
                    names.setdefault(ident, {}).setdefault(name, rel)

    for ident, found in sorted(names.items()):
        if len(found) <= 1:
            continue
        detail = " / ".join(f"`{n}`（{src}）" for n, src in sorted(found.items(), key=lambda kv: kv[1]))
        rep.error(
            sorted(found.values())[0],
            f"{ident} の名称が一致しません: {detail}",
        )


def normalize_name(raw: str) -> str:
    """ID の直後の文字列を名称として採用できるか判定し、正規化して返す（不可なら空文字）。"""
    name = " ".join(raw.split()).strip(" 　-—:：")
    if len(name) < 2 or len(name) > 40:
        return ""
    if name.startswith(NAME_REJECT_PREFIX):
        return ""
    if name.endswith(NAME_REJECT_SUFFIX):
        return ""
    # 他の ID を含む文字列は説明文なので名称として扱わない
    for pattern in ID_PATTERNS.values():
        if pattern.search(name):
            return ""
    # Markdown のリンク・強調・パス表記は名称ではない
    if any(ch in name for ch in "`*![]/"):
        return ""
    if PLACEHOLDER_RE.match(name):
        return ""
    return name


def spec_sections(path: Path) -> list[str]:
    """`## ` 見出しの一覧を返す（節構成の比較用）。"""
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("## ")
    ]


def check_spec_sections(docs: Path, rep: Report) -> None:
    """個票の節構成が `_template.md` と一致しているかを見る（`##` レベルのみ）。

    節の過不足は「設計書としての形が崩れている」合図だが、案件固有の節を足すのは
    正当にありうるので WARN に留める。P02 のゲートではこの WARN を 0 件にする。
    """
    for folder, prefix in (("screens", "SCR-"), ("apis", "API-")):
        tpl = docs / "specs" / folder / "_template.md"
        if not tpl.exists():
            continue
        expected = spec_sections(tpl)
        if not expected:
            continue
        for f in sorted((docs / "specs" / folder).glob(f"{prefix}*.md")):
            rel = str(f.relative_to(docs.parent))
            actual = spec_sections(f)
            missing = [s for s in expected if s not in actual]
            extra = [s for s in actual if s not in expected]
            if missing:
                rep.warn(rel, f"雛形にある節がありません: {' / '.join(missing)}")
            if extra:
                rep.warn(rel, f"雛形に無い節があります: {' / '.join(extra)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="docs/ の構造整合を検査する")
    ap.add_argument("--docs", default="docs", help="docs ディレクトリ（既定: docs）")
    ap.add_argument("--json", action="store_true", help="JSON で出力する")
    ap.add_argument("--strict", action="store_true", help="WARN も失敗扱いにする")
    ap.add_argument(
        "--step",
        type=int,
        default=None,
        metavar="N",
        help=(
            "P01 のステップ番号（1-9）。1〜4（RDRAフェーズ1）では ERROR を報告するが "
            "exit 0 にする。この段階は欠落があって正常なため"
        ),
    )
    args = ap.parse_args()

    lenient = args.step is not None and 1 <= args.step <= 4

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
    check_adr_index(docs, defined, rep)
    check_id_names(docs, rep)
    check_spec_sections(docs, rep)

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
        if lenient and rep.errors:
            print(
                f"（--step {args.step} は RDRAフェーズ1 のため ERROR を失敗扱いにしません。"
                "Step5 以降で解消すること）"
            )

    if rep.errors and not lenient:
        return 1
    if args.strict and rep.warns and not lenient:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
