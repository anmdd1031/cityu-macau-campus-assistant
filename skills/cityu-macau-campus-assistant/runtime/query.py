"""Read-only evidence bundles and exact mentor identity rendering (stdlib only)."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from read_sections import ROOT, RetrievalError, read_packet

BUNDLES = {
    "map": ["campus_map.md::*"],
    "fds-fees-mainland-2027": ["fds.md::3.2", "freshman.md::0.2"],
    "iusd-phd-2026": ["iusd.md::0.", "iusd.md::3.8", "iusd.md::11."],
}
VISION = ["视觉", "視覺", "图像", "圖像", "computer vision", "image"]


def load_mentors():
    raw = (ROOT / "mentors/fds_mentors.md").read_bytes()
    text = raw.decode("utf-8-sig")
    records = []
    for number, line in enumerate(text.splitlines(), 1):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.startswith("|") or not cells[0].isdigit():
            continue
        if len(cells) != 13:
            raise ValueError("Mentor table schema changed; inspect source before reading.")
        email = re.search(r"mailto:([^\s)]+)", cells[4])
        url = re.search(r"\]\((https://[^)]+)\)", cells[11])
        if not email or not url:
            raise ValueError("Missing public email or official page in mentor row " + cells[0])
        records.append({"id": cells[0], "name": cells[1], "qualification": cells[3],
                        "email": email[1], "direction": cells[5], "tags": cells[6],
                        "recruitment": cells[8], "verified": cells[10], "url": url[1],
                        "source_line": number})
    if not records or len({r["id"] for r in records}) != len(records):
        raise ValueError("Empty mentor table or duplicate row IDs.")
    return records, hashlib.sha256(raw).hexdigest(), text.split("## 师资索引", 1)[0]


def pick(records, ids):
    selected = ids.split(",")
    if len(selected) != len(set(selected)) or not selected or any(i not in {r["id"] for r in records} for i in selected):
        raise ValueError("Use distinct IDs from the current mentor results.")
    lookup = {r["id"]: r for r in records}
    return [lookup[i] for i in selected]


def render(records):
    # Copy canonical fields without normalization or model rewriting.
    lines = ["| 教师 | 导师资格 | 公开工作邮箱 | 官方主页 |",
             "|---|---|---|---|"]
    for r in records:
        lines.append(f"| {r['name']} | {r['qualification']} | {r['email']} | {r['url']} |")
    return "\n".join(lines)


def mentors(query, level):
    records, digest, context = load_mentors()
    terms = VISION if query.casefold() in {"视觉", "计算机视觉", "cv", "computer vision"} else [query.casefold()]
    if not query.strip():
        raise ValueError("Provide a non-empty research keyword.")
    required = {"master": "硕士生导师", "phd": "博士生导师", "research": ""}[level]
    matched = [r for r in records if required in r["qualification"] and any(
        term.casefold() in (r["direction"] + " " + r["tags"]).casefold() for term in terms)]
    rules = read_packet(ROOT, ["mentors/fds_rules.md::*", "mentors/fds_matching_policy.md::*"])
    return {"schema": "records contains candidate objects; verbatim_table contains identity fields only; rules contains required matching policy.", "query": query, "level": level, "match_terms": terms, "count": len(matched),
            "scope": "Literal keyword matches in official directions and tags, filtered by explicit qualification. Not an exhaustive semantic match or an availability/ranking claim. Source order retained.",
            "source_sha256": digest, "source_context": context, "rules": rules,
            "records": matched, "verbatim_table": render(matched)}


def check_table(answer, selected):
    rows = [line for line in answer.splitlines() if line.lstrip().startswith("|")]
    expected = render(selected).splitlines()[2:]
    issues = []
    # Deliberately require exact generated rows, catching substitutions, swaps and additions.
    for canonical in expected:
        if canonical not in rows:
            issues.append({"kind": "missing_or_modified_row", "expected_row": canonical})
    if len(rows) != len(selected) + 2 or any(row not in render(selected).splitlines() for row in rows):
        issues.append({"kind": "unexpected_or_duplicate_table_rows"})
    return {"valid": not issues, "issues": issues, "canonical_table": render(selected),
            "scope": "Validates the generated table only, not claims in surrounding prose or later model edits."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ascii", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    bundle = sub.add_parser("bundle")
    bundle.add_argument("topic", choices=BUNDLES)
    match = sub.add_parser("mentors")
    match.add_argument("--query", required=True)
    match.add_argument("--level", choices=["master", "phd", "research"], required=True)
    for command in ["render", "check"]:
        p = sub.add_parser(command)
        p.add_argument("--ids", required=True)
        p.add_argument("--sha256", required=True, help="Mentor source hash returned by mentors")
        if command == "check":
            p.add_argument("--answer-file", help="UTF-8 draft file; omit to read UTF-8 stdin")
    args = parser.parse_args()
    code = 0
    try:
        if args.command == "bundle":
            result = read_packet(ROOT, BUNDLES[args.topic])
        elif args.command == "mentors":
            result = mentors(args.query, args.level)
        else:
            records, digest, _ = load_mentors()
            if args.sha256 != digest:
                raise ValueError("Mentor source changed; rerun mentors before rendering/checking.")
            selected = pick(records, args.ids)
            if args.command == "render":
                result = {"source_sha256": digest, "verbatim_table": render(selected)}
            else:
                answer = Path(args.answer_file).read_text(encoding="utf-8-sig") if args.answer_file else sys.stdin.buffer.read().decode("utf-8-sig")
                result = check_table(answer, selected)
                code = 0 if result["valid"] else 2
    except (ValueError, OSError, UnicodeError) as error:
        result = {"error": str(error)}
        if isinstance(error, RetrievalError):
            result.update(error.details)
        code = 2
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=args.ascii, indent=2) + "\n").encode("utf-8"))
    return code


if __name__ == "__main__":
    sys.exit(main())
