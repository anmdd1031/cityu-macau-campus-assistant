"""Read-only evidence bundles and exact mentor identity rendering (stdlib only)."""
import argparse
import hashlib
import html
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


def mentors(query, level, view="full"):
    records, digest, context = load_mentors()
    terms = VISION if query.casefold() in {"视觉", "计算机视觉", "cv", "computer vision"} else [query.casefold()]
    if not query.strip():
        raise ValueError("Provide a non-empty research keyword.")
    required = {"master": "硕士生导师", "phd": "博士生导师", "research": ""}[level]
    matched = [r for r in records if required in r["qualification"] and any(
        term.casefold() in (r["direction"] + " " + r["tags"]).casefold() for term in terms)]
    rules = read_packet(ROOT, ["mentors/fds_rules.md::*", "mentors/fds_matching_policy.md::*"])
    result = {"schema": "records contains candidate objects; verbatim_table contains identity fields only; rules contains required matching policy.", "query": query, "level": level, "match_terms": terms, "count": len(matched),
            "scope": "Literal keyword matches in official directions and tags, filtered by explicit qualification. Not an exhaustive semantic match or an availability/ranking claim. Source order retained.",
            "source_sha256": digest, "source_context": context, "rules": rules,
            "records": matched, "verbatim_table": render(matched)}
    result["check_template"] = "python runtime/query.py --ascii check --ids <SELECTED_IDS> --sha256 " + digest
    result["check_input"] = "UTF-8 stdin containing only the actual planned four-column table. No prose, help lookup or temporary file required. Paths are relative to the skill directory."
    result["identity_codepoints"] = {r["id"]: " ".join(f"U+{ord(c):04X}" for c in re.split(r"[（(]", r["name"], maxsplit=1)[0]) for r in matched}
    if view == "selection":
        # Identity fields stay in the canonical source until final rendering.
        result.pop("verbatim_table")
        result["records"] = [{k: r[k] for k in ("id", "direction", "tags", "qualification", "verified")} for r in matched]
        result["schema"] = "Select IDs with reasons from records; finalize with the returned source_sha256. Identity fields are rendered locally."
    return result


def finalize(ids, digest, reasons):
    """Host-callable final stage: render canonical identities without an LLM roundtrip."""
    records, current, _ = load_mentors()
    if digest != current:
        raise ValueError("Mentor source changed; rerun mentors before finalizing.")
    selected = pick(records, ids)
    if not isinstance(reasons, dict) or set(reasons) != {r["id"] for r in selected}:
        raise ValueError("Supply exactly one reason for each selected ID.")
    if not all(isinstance(v, str) and v.strip() for v in reasons.values()):
        raise ValueError("Reasons must be non-empty strings.")
    table = render(selected)
    return {"source_sha256": current, "verbatim_table": table,
            "reasons": reasons, "valid": check_table(table, selected)["valid"],
            "scope": "Identity table generated from source; reasons are caller supplied and not fact-checked. Preserve table unchanged when sending."}


def contact(name):
    """Exact name/ID lookup only; no fuzzy identity guesses."""
    records, digest, _ = load_mentors()
    name = name.strip()
    matched = [r for r in records if name and name in
               (r["id"], r["name"], re.split(r"[（(]", r["name"], maxsplit=1)[0].strip())]
    if len(matched) != 1:
        raise ValueError("Name must identify exactly one teacher; use the original Chinese name or ID from the source.")
    r = matched[0]
    return {"answer": f"{r['name']}的公开工作邮箱：{r['email']}。\n官方主页：{r['url']}\n本地核验日期：{r['verified']}；未实时核验。",
            "source_sha256": digest, "source_line": r["source_line"]}


def building(code):
    raw = (ROOT / "campus_map.md").read_bytes()
    text = raw.decode("utf-8-sig")
    rows = [line for line in text.splitlines() if line.startswith("|")]
    pairs = [tuple(c.strip() for c in line.strip("|").split("|")) for line in rows]
    matches = [pair for pair in pairs if len(pair) == 2 and pair[0] == code.strip().upper()]
    if len(matches) != 1 or matches[0][0] in ("地图标识", "---"):
        raise ValueError("Unknown building code; read campus_map.md for the full map.")
    code, name = matches[0]
    # Scope and dates come from the source, not a second maintained fact store.
    if "## 官方校园地图入口与适用范围" not in text or "这是官方地图图例" not in text:
        raise ValueError("Map source structure changed; inspect campus_map.md before direct lookup.")
    intro = text.split("## 官方校园地图入口与适用范围", 1)[1].split("\n## ", 1)[0].strip()
    caveat = text.split("这是官方地图图例", 1)[1].split("\n\n", 1)[0]
    return {"answer": f"氹仔校区官方地图标识 {code}：{name}。\n\n这是官方地图图例{caveat}\n\n{intro}",
            "source_sha256": hashlib.sha256(raw).hexdigest()}


def tuition(course, year, audience):
    """Exact lookup in the explicitly supported mainland FDS fee table."""
    if year != "2027/2028" or audience != "mainland":
        raise ValueError("Direct tuition lookup supports only 2027/2028 mainland FDS applicants; read the matching source for other cohorts.")
    packet = read_packet(ROOT, BUNDLES["fds-fees-mainland-2027"])
    content = "\n".join(e["text"] for f in packet["files"] if f["file"] == "fds.md" for e in f["excerpts"])
    marker = "### 3.2 2027/2028 内地硕博招生与学费"
    if marker not in content:
        raise ValueError("Tuition source structure changed; inspect the source table.")
    section = content.split(marker, 1)[1].split("\n#### ", 1)[0]
    if "HKD/学年" not in section:
        raise ValueError("Tuition currency or billing period changed; inspect the source.")
    rows = [[c.strip() for c in line.strip("|").split("|")] for line in section.splitlines() if line.startswith("|")]
    matches = [r for r in rows if len(r) == 3 and r[0] == course.strip() and re.fullmatch(r"[\d,]+", r[1])]
    if len(matches) != 1:
        raise ValueError("Use an exact course name from the FDS mainland postgraduate fee table.")
    row = matches[0]
    row_boundary = row[2]
    if row_boundary == "同上":
        preceding = [r for r in rows[:rows.index(row)] if len(r) == 3 and re.fullmatch(r"[\d,]+", r[1]) and r[2] != "同上"]
        if not preceding:
            raise ValueError("Cannot resolve tuition row scope; read the full source.")
        row_boundary = preceding[-1][2]
    boundary = section.split("以上只适用于", 1)
    if len(boundary) != 2:
        raise ValueError("Missing tuition scope; inspect the source.")
    date = re.search(r"\d{4}-\d{2}-\d{2}", section)
    risk_text = "\n".join(e["text"] for f in packet["files"] if f["file"] == "freshman.md" for e in f["excerpts"])
    status = next((line for line in risk_text.splitlines() if line.startswith("| 课程、学院、专业名称 |")), "")
    if not date or not status:
        raise ValueError("Missing verification date or course-status rule; read the full evidence bundle.")
    return {"answer": f"{year} 学年内地申请人，FDS {row[0]}：HKD {row[1]}/学年，不是全程总学费。"
            f"\n简章课程列项边界：{row_boundary}。\n核验日期：{date[0]}；未实时核验。\n\n以上只适用于{boundary[1].strip()}\n\n新课程标签说明：\n{status}",
            "sources": [{"file": f["file"], "sha256": f["sha256"]} for f in packet["files"]]}


def recommend(query, level, limit=5):
    """Deterministic initial shortlist; explicit lexical relevance, not a quality rank."""
    if limit < 0:
        raise ValueError("Use a positive limit or 0 to show all matches.")
    pool = mentors(query, level)
    terms = pool["match_terms"]
    def score(record):
        direction = record["direction"].casefold()
        tags = record["tags"].casefold()
        return (sum(t.casefold() in direction for t in terms),
                sum(t.casefold() in tags for t in terms))
    ranked = sorted(pool["records"], key=score, reverse=True)
    selected = ranked[:limit] if limit else ranked
    table = render(selected)
    dates = ", ".join(dict.fromkeys(r["verified"] for r in selected))
    answer = (f"按公开方向及标签关键词召回，并按明确导师资格筛选：共 {len(ranked)} 人，"
              f"展示 {len(selected)} 人，未展开 {len(ranked)-len(selected)} 人。可要求显示全部相关教师。\n"
              "排序口径：官网方向命中的不同关键词数优先，其次标签命中数；同分沿用官网顺序。"
              "这是字面匹配初选，不代表全部语义相关教师、个人适配程度或学术水平排名。\n\n" + table +
              "\n\n官网方向依据（本地原表记录，部分为摘要；完整项目或成果须另查官网证据）：\n" + "\n".join(
                  f"- {r['name']}：{r['direction']}" for r in selected) +
              f"\n\n本地记录核验日期：{dates or '无匹配记录'}；未实时核验。"
              "当前招生名额和接收意愿待确认。结果仅为公开资料方向匹配，不构成学校、学院或教师的官方推荐、评价或录取承诺。")
    return {"answer": answer, "rules": pool["rules"], "source_sha256": pool["source_sha256"],
            "selected_ids": [r["id"] for r in selected], "count": len(ranked),
            "check_command": "python runtime/query.py --ascii check --ids " + ",".join(r["id"] for r in selected) + " --sha256 " + pool["source_sha256"] if selected else None,
            "check_input": "Pass ONLY the actual four-column table planned for the final answer as UTF-8 stdin; no prose or temporary file needed. Command is relative to the skill directory. Do not substitute generated reference rows for the actual draft.",
            "identity_table_valid": check_table(table, selected)["valid"],
            "scope": "Generated table checked before returning; later edits are not checked. Use mentors --view selection for personalized analysis."}


def evidence_text(topic):
    """Lossless plain evidence: no duplicate JSON metadata around each excerpt."""
    packet = read_packet(ROOT, BUNDLES[topic])
    return "\n\n".join(f"来源文件：{f['file']}；版本：{f['sha256']}\n" +
                       "\n\n".join(f"原文行 {e['start_line']}-{e['end_line']}：\n{e['text']}" for e in f["excerpts"])
                       for f in packet["files"])


def check_table(answer, selected):
    # CommonMark renders numeric character references as the original characters.
    # Compare decoded values, not their equivalent transport spelling.
    rows = [html.unescape(line) for line in answer.splitlines() if line.lstrip().startswith("|")]
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


def portable_names(result):
    """Lossless CommonMark name transport for clients that misread escaped CJK."""
    records, _, _ = load_mentors()
    names = {re.split(r"[（(]", r["name"], maxsplit=1)[0]: None for r in records}
    replacements = [(name, "".join(f"&#x{ord(c):X};" if ord(c) > 127 else c for c in name)) for name in names]
    def convert(value):
        if isinstance(value, str):
            for original, encoded in replacements:
                value = value.replace(original, encoded)
            return value.replace("runtime/query.py --ascii check", "runtime/query.py --portable-names --ascii check")
        if isinstance(value, list):
            return [convert(v) for v in value]
        if isinstance(value, dict):
            return {k: convert(v) for k, v in value.items()}
        return value
    converted = convert(result)
    if isinstance(converted, dict):
        converted["name_transport"] = "CommonMark numeric character references: copy name strings literally, including &#x...; sequences, in the final Markdown table and prose. They render as the original Chinese names. Do NOT manually decode or replace them. Plain-text consumers should omit --portable-names."
    return converted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ascii", action="store_true")
    parser.add_argument("--portable-names", action="store_true", help="Encode Chinese names as lossless CommonMark numeric character references; for Markdown output only")
    sub = parser.add_subparsers(dest="command", required=True)
    bundle = sub.add_parser("bundle")
    bundle.add_argument("topic", choices=BUNDLES)
    evidence = sub.add_parser("evidence")
    evidence.add_argument("topic", choices=BUNDLES)
    lookup = sub.add_parser("contact")
    lookup.add_argument("--name", required=True)
    map_lookup = sub.add_parser("building")
    map_lookup.add_argument("--code", required=True)
    fee_lookup = sub.add_parser("tuition")
    fee_lookup.add_argument("--course", required=True)
    fee_lookup.add_argument("--year", required=True)
    fee_lookup.add_argument("--audience", required=True)
    recommendation = sub.add_parser("recommend")
    recommendation.add_argument("--query", required=True)
    recommendation.add_argument("--level", choices=["master", "phd", "research"], required=True)
    recommendation.add_argument("--limit", type=int, default=5, help="0 returns all matches")
    match = sub.add_parser("mentors")
    match.add_argument("--query", required=True)
    match.add_argument("--level", choices=["master", "phd", "research"], required=True)
    match.add_argument("--view", choices=["full", "selection"], default="full")
    finish = sub.add_parser("finalize")
    finish.add_argument("--ids", required=True)
    finish.add_argument("--sha256", required=True)
    finish.add_argument("--reasons-file", required=True, help="UTF-8 JSON object mapping selected IDs to reasons")
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
        elif args.command == "evidence":
            result = evidence_text(args.topic)
        elif args.command == "contact":
            result = contact(args.name)
        elif args.command == "building":
            result = building(args.code)
        elif args.command == "tuition":
            result = tuition(args.course, args.year, args.audience)
        elif args.command == "recommend":
            result = recommend(args.query, args.level, args.limit)
        elif args.command == "finalize":
            result = finalize(args.ids, args.sha256, json.loads(Path(args.reasons_file).read_text(encoding="utf-8-sig")))
        elif args.command == "mentors":
            result = mentors(args.query, args.level, args.view)
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
    if args.portable_names and args.command in ("mentors", "recommend", "render", "check", "finalize", "contact") and (code == 0 or "canonical_table" in result):
        result = portable_names(result)
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=args.ascii, indent=2) + "\n").encode("utf-8"))
    return code


if __name__ == "__main__":
    sys.exit(main())
