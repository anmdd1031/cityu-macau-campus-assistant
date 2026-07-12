#!/usr/bin/env python3
"""Build or check recent FDS publication evidence using Crossref metadata.

Only records whose author name exactly matches and whose author affiliation
contains City University of Macau are accepted. This deliberately conservative
rule avoids mixing publications from homonymous researchers. Paper topics are
derived from titles and Crossref abstracts when available. Crossref does not
provide reliable author-contribution statements, so author position is stored
as weak evidence and never converted into a specific technical role.
"""

from __future__ import annotations

import argparse
import html
import http.client
import json
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from update_fds_faculty import TAG_RULES, clean_text


CROSSREF_API = "https://api.crossref.org/works"
USER_AGENT = (
    "cityu-macau-campus-assistant/1.0 "
    "(https://github.com/anmdd1031/cityu-macau-campus-assistant)"
)
CITYU_AFFILIATIONS = (
    "city university of macau",
    "universidade da cidade de macau",
)

PAPER_TAG_EXTRAS: dict[str, tuple[str, ...]] = {
    "人工智能与机器学习": (
        "transformer", "mamba", "lstm", "attention", "classification", "forecasting",
        "prediction", "detection", "segmentation", "knowledge distillation", "zero-shot",
        "few-shot", "continual learning", "anomaly detection", "neuro-symbolic", "bert",
        "emotion recognition", "pose estimation", "question generation",
    ),
    "大语言模型与生成式 AI": (
        "llm", "multi-llm", "retrieval-augmented", "rag", "diffusion model",
        "text-to-image", "generative", "chain-of-thought",
    ),
    "数据科学与数据挖掘": (
        "clustering", "analytics", "time series", "forecasting", "fraud detection",
        "user segmentation", "feature fusion",
    ),
    "自然语言处理": (
        "language", "sentiment", "rhetoric", "text encoder", "corpus", "speech",
        "retrieval-augmented", "machine translation", "question generation", "multi-hop",
    ),
    "计算机视觉与多媒体": (
        "image", "vision", "video", "face", "visual", "person re-identification",
        "object detection", "watermark", "biometric", "pose estimation", "retinopathy",
    ),
    "隐私计算与联邦学习": (
        "unlearning", "federated", "privacy", "private", "forget knowledge",
    ),
    "网络空间安全与 AI 安全": (
        "attack", "defense", "threat", "backdoor", "adversarial", "botnet", "malware",
        "secure", "security", "steganography", "fraud detection", "watermark",
    ),
    "密码学、区块链与可信计算": (
        "searchable encryption", "dsse", "blockchain", "multi-chain", "ethereum",
        "cryptographic", "access control",
    ),
    "云计算、分布式系统与边缘计算": (
        "edge device", "resource footprint", "hardware and software", "cloud", "gpu",
        "distributed", "scheduling",
    ),
    "物联网与无线通信": (
        "iot", "wireless", "network", "smart grid", "sensor", "micro-doppler",
        "cellular", "communication",
    ),
    "机器人与智能交通": (
        "robot", "vehicle", "drone", "autonomous", "transportation", "navigation",
        "embodied", "trajectory",
    ),
    "医疗健康与生物信息": (
        "medical", "clinical", "brain", "alzheimer", "icu", "biomedical", "health",
        "disease", "pathological", "sarcopenia", "retinopathy", "diagnosis",
    ),
    "优化、运筹与计算数学": (
        "optimization", "algorithm", "equation", "hypergeometric", "modeling", "control",
        "pricing model", "game theory", "rotation", "torus",
    ),
    "统计学习与概率建模": ("bayesian", "statistical", "probability", "probabilistic"),
    "数据库、知识图谱与信息检索": (
        "database", "retrieval", "knowledge graph", "recommendation", "vector database",
    ),
    "软件工程与程序分析": (
        "software", "code", "program", "bug", "testing", "vulnerability",
    ),
    "人机交互与教育技术": (
        "student", "education", "learning behavior", "user", "human activity",
        "human-computer", "collaborative learning",
    ),
    "信号处理与时序分析": (
        "signal", "radar", "speech", "acoustic", "aural", "micro-doppler", "time series",
    ),
    "科学智能与计算物理": (
        "physics", "cosmology", "scientific discovery", "curvature perturbation", "inflation",
    ),
    "信息系统与数字化应用": ("information system", "digital transformation"),
    "智慧城市与空间计算": (
        "urban", "remote sensing", "spatial", "climate", "meteorology", "smart grid",
        "tourism", "geographic",
    ),
    "金融与商业数据": (
        "credit card", "financial", "finance", "pricing", "bond", "fraud", "marketing",
        "e-commerce",
    ),
}


@dataclass
class Teacher:
    order: int
    chinese_name: str
    english_name: str
    official_url: str


@dataclass
class Paper:
    title: str
    year: int
    month: int
    day: int
    venue: str
    doi: str
    url: str
    tags: list[str]
    evidence: str
    author_position: str
    contribution_evidence: str
    contribution_note: str


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def strip_markup(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    return clean_text(value)


def table_text(value: str) -> str:
    return clean_text(value).replace("|", "\\|")


def read_teachers(path: Path) -> list[Teacher]:
    teachers: list[Teacher] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\| \d+ \|", line):
            continue
        cells = line.split("|")
        order = int(cells[1].strip())
        teacher = cells[2].strip()
        name_match = re.match(r"(.+?)（([^）]+)）$", teacher)
        official_match = re.search(r"\[官方页\]\((https://fds\.cityu\.edu\.mo/en/members/\d+)\)", line)
        if not name_match or not official_match:
            raise RuntimeError(f"Unable to parse faculty row {order}")
        teachers.append(
            Teacher(
                order=order,
                chinese_name=name_match.group(1),
                english_name=name_match.group(2),
                official_url=official_match.group(1),
            )
        )
    if len(teachers) != 58 or [item.order for item in teachers] != list(range(1, 59)):
        raise RuntimeError(f"Expected 58 sequential faculty rows, found {len(teachers)}")
    return teachers


def request_json(url: str, timeout: float, retries: int) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code == 429 and attempt < retries:
                retry_after = error.headers.get("Retry-After")
                wait = float(retry_after) if retry_after and retry_after.isdigit() else 3.0 * (attempt + 1)
                time.sleep(min(wait, 30.0))
                continue
            if 500 <= error.code < 600 and attempt < retries:
                time.sleep(2 ** attempt)
                continue
            break
        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
            http.client.IncompleteRead,
        ) as error:
            last_error = error
            if attempt < retries:
                time.sleep(2 ** attempt)
                continue
            break
    raise RuntimeError(f"Unable to fetch {url}: {last_error}")


def publication_date(item: dict) -> tuple[int, int, int]:
    for field in ("published", "published-online", "published-print", "issued", "created"):
        parts = item.get(field, {}).get("date-parts", [])
        if parts and parts[0]:
            values = list(parts[0]) + [0, 0]
            return int(values[0]), int(values[1]), int(values[2])
    return 0, 0, 0


def matched_cityu_author(item: dict, teacher: Teacher) -> tuple[int, int] | None:
    expected = normalize_name(teacher.english_name)
    authors = item.get("author", [])
    for position, author in enumerate(authors, 1):
        full_name = f"{author.get('given', '')} {author.get('family', '')}".strip()
        affiliations = " ".join(
            affiliation.get("name", "") for affiliation in author.get("affiliation", [])
        ).lower()
        if normalize_name(full_name) == expected and any(
            marker in affiliations for marker in CITYU_AFFILIATIONS
        ):
            return position, len(authors)
    return None


def topic_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags = []
    for tag, terms in TAG_RULES:
        combined_terms = terms + PAPER_TAG_EXTRAS.get(tag, ())
        if any(term in lowered for term in combined_terms):
            tags.append(tag)
    return tags or ["论文主题待人工归类"]


def query_teacher(
    teacher: Teacher,
    since_year: int,
    rows: int,
    max_papers: int,
    timeout: float,
    retries: int,
    cache_path: Path,
    refresh: bool,
) -> tuple[list[Paper], int]:
    parameters = urllib.parse.urlencode(
        {
            "query.author": teacher.english_name,
            "query.affiliation": "City University of Macau",
            "filter": f"from-pub-date:{since_year}-01-01",
            "rows": str(rows),
            "select": "DOI,title,author,published,published-online,published-print,issued,container-title,URL,abstract",
        }
    )
    if cache_path.exists() and not refresh:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        payload = request_json(f"{CROSSREF_API}?{parameters}", timeout, retries)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", newline="\n", delete=False, dir=cache_path.parent
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False)
            temporary = Path(handle.name)
        temporary.replace(cache_path)
    matched: list[tuple[dict, int, int]] = []
    seen_dois: set[str] = set()
    for item in payload.get("message", {}).get("items", []):
        doi = (item.get("DOI") or "").lower().strip()
        author_match = matched_cityu_author(item, teacher)
        if not doi or doi in seen_dois or author_match is None:
            continue
        year, _, _ = publication_date(item)
        if year < since_year:
            continue
        seen_dois.add(doi)
        matched.append((item, author_match[0], author_match[1]))

    matched.sort(key=lambda entry: publication_date(entry[0]), reverse=True)
    papers: list[Paper] = []
    for item, author_index, author_total in matched[:max_papers]:
        title = strip_markup((item.get("title") or [""])[0])
        abstract = strip_markup(item.get("abstract") or "")
        year, month, day = publication_date(item)
        doi = item["DOI"].lower()
        papers.append(
            Paper(
                title=title,
                year=year,
                month=month,
                day=day,
                venue=strip_markup((item.get("container-title") or [""])[0]) or "Crossref 未提供",
                doi=doi,
                url=f"https://doi.org/{urllib.parse.quote(doi, safe='/:()[];._-')}",
                tags=topic_tags(f"{title} {abstract}"),
                evidence="标题和摘要" if abstract else "标题",
                author_position=f"第 {author_index}/{author_total} 作者",
                contribution_evidence="E（未公开作者贡献声明）",
                contribution_note="仅能确认参与该论文主题，不能确认具体负责模块",
            )
        )
    return papers, len(matched)


def aggregate_tags(papers: list[Paper]) -> list[str]:
    counts = Counter(tag for paper in papers for tag in paper.tags if tag != "论文主题待人工归类")
    tag_order = {tag: index for index, (tag, _terms) in enumerate(TAG_RULES)}
    return [
        tag for tag, _count in sorted(
            counts.items(), key=lambda item: (-item[1], tag_order.get(item[0], 999), item[0])
        )
    ]


def render(
    results: list[tuple[Teacher, list[Paper], int]],
    verified: str,
    since_year: int,
    max_papers: int,
    errors: list[str],
) -> str:
    matched_teachers = sum(bool(papers) for _teacher, papers, _total in results)
    shown_papers = sum(len(papers) for _teacher, papers, _total in results)
    lines = [
        "# 澳门城市大学数据科学学院教师近期论文与研究主题证据库",
        "",
        "> 教师身份来源：澳门城市大学数据科学学院 Academic Staff 与官方个人页。",
        "> 论文元数据来源：Crossref REST API；仅保留作者姓名准确匹配且作者隶属明确包含 City University of Macau 的记录。",
        f"> 核验日期：{verified}；检索范围：{since_year} 年至今；每位教师最多展示 {max_papers} 篇。",
        "> 本表论文来源等级：4（DOI/出版社元数据索引）；论文主题只作为官网研究方向的补充证据。",
        "> 贡献证据：当前 Crossref 记录未提供可靠的 Author Contributions/CRediT 声明；作者位置仅作弱证据，不能反推算法、代码、实验或数据分析角色。",
        "> 导师匹配规则：[fds_mentor_recommendation.md](fds_mentor_recommendation.md)。",
        f"> 当前覆盖：{matched_teachers}/58 名教师，展示 {shown_papers} 篇高置信论文。",
        "",
        "## 使用规则",
        "",
        "- 论文主题只用于补充官网研究方向，不代表教师当前一定招生，也不用于按论文数量、引用量或职称排名。",
        "- 主题标签根据论文标题及 Crossref 可用摘要生成；标为“标题”时没有使用摘要，不应过度推断全文内容。",
        "- Crossref 可能缺少尚未登记 DOI、作者隶属未填写或中文出版物。未匹配不等于教师没有近期成果。",
        "- 同名作者、作者隶属不清或无法证明属于澳城大该教师的论文一律不收录。",
        "- 回答导师推荐时，先看 `fds_faculty.md` 的官网身份、导师资格和邮箱，再用本文件的论文主题作为补充证据。",
        "- 当前论文记录均标为 E 级贡献证据：只能确认参与论文主题；没有明确贡献声明时，不得写成导师亲自负责某个技术模块。",
        "",
    ]

    lines.extend(["## 快速索引", ""])
    for start in range(0, len(results), 10):
        group = results[start : start + 10]
        links = [
            f"[{teacher.order}. {teacher.chinese_name}](#teacher-{teacher.order})"
            for teacher, _papers, _total in group
        ]
        lines.append(f"- {'；'.join(links)}")
    lines.extend(["", "## 教师论文详情", ""])

    for teacher, papers, total in results:
        lines.extend(
            [
                f"<a id=\"teacher-{teacher.order}\"></a>",
                "",
                f"## {teacher.order}. {teacher.chinese_name}（{teacher.english_name}）",
                "",
                f"- [澳城大官方主页]({teacher.official_url})",
            ]
        )
        if not papers:
            lines.extend(
                [
                    "- Crossref 高置信匹配：未找到。为避免同名误收，不展示外部论文；请继续参考官方主页或个人主页。",
                    "",
                ]
            )
            continue

        themes = aggregate_tags(papers)
        lines.extend(
            [
                f"- Crossref 高置信匹配：共 {total} 篇符合条件，当前展示最近 {len(papers)} 篇。",
                f"- 论文佐证方向：{'；'.join(themes) if themes else '论文主题待人工归类'}。",
                "",
                "| 年份 | 代表论文 | 论文内容主题 | 作者位置 | 贡献证据 | 判断依据 | 刊物/会议 | 来源等级 | 核验日期 | 来源 |",
                "|---:|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for paper in papers:
            lines.append(
                f"| {paper.year} | {table_text(paper.title)} | {'；'.join(paper.tags)} | "
                f"{paper.author_position} | {paper.contribution_evidence}：{paper.contribution_note} | "
                f"{paper.evidence} | {table_text(paper.venue)} | 4（DOI/出版社元数据） | {verified} | [DOI]({paper.url}) |"
            )
        lines.append("")

    lines.extend(["## 人工复核记录", ""])
    if errors:
        lines.extend(f"- {error}" for error in errors)
    else:
        lines.append("- 本次查询未发生接口错误；无高置信论文的教师已在各自条目中说明。")
    lines.extend(
        [
            "",
            "## 数据入口",
            "",
            "- [Crossref REST API](https://api.crossref.org/works)",
            "- [Crossref REST API 文档](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)",
            "- [FDS Academic Staff](https://fds.cityu.edu.mo/en/members)",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    skill_dir = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--faculty", type=Path, default=skill_dir / "references" / "mentors" / "fds_faculty.md")
    parser.add_argument("--output", type=Path, default=skill_dir / "references" / "mentors" / "fds_faculty_publications.md")
    parser.add_argument("--check", action="store_true", help="Do not write; fail if generated content differs")
    parser.add_argument("--date", help="Verification date in YYYY-MM-DD; defaults to today when writing")
    parser.add_argument("--since-year", type=int, default=2023)
    parser.add_argument("--max-papers", type=int, default=5)
    parser.add_argument("--rows", type=int, default=50, choices=range(10, 101))
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.8, help="Delay between Crossref requests")
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(__file__).resolve().parent / ".cache" / "crossref",
        help="Ignored local cache used to resume interrupted runs",
    )
    parser.add_argument("--refresh", action="store_true", help="Ignore cached Crossref responses")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.since_year < 2000 or not 1 <= args.max_papers <= 10:
        raise SystemExit("Invalid --since-year or --max-papers")

    verified = args.date
    if verified is None and args.check and args.output.exists():
        current = args.output.read_text(encoding="utf-8")
        match = re.search(r"核验日期：(\d{4}-\d{2}-\d{2})", current)
        verified = match.group(1) if match else None
    verified = verified or date.today().isoformat()

    teachers = read_teachers(args.faculty)
    results: list[tuple[Teacher, list[Paper], int]] = []
    errors: list[str] = []
    for index, teacher in enumerate(teachers, 1):
        try:
            papers, total = query_teacher(
                teacher,
                args.since_year,
                args.rows,
                args.max_papers,
                args.timeout,
                args.retries,
                args.cache_dir
                / f"v1-{verified}-{teacher.order:02d}-{args.since_year}-{args.rows}.json",
                args.refresh,
            )
        except RuntimeError as error:
            papers, total = [], 0
            errors.append(f"{teacher.order} {teacher.english_name}: {error}")
        results.append((teacher, papers, total))
        print(f"[{index:02d}/58] {teacher.english_name}: {len(papers)} shown / {total} matched", file=sys.stderr)
        if index < len(teachers) and args.delay:
            time.sleep(args.delay)

    if errors:
        print("Crossref update aborted; generated reference was not changed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    rendered = render(results, verified, args.since_year, args.max_papers, errors)
    if args.check:
        if not args.output.exists():
            print(f"Missing generated reference: {args.output}", file=sys.stderr)
            return 1
        current = args.output.read_text(encoding="utf-8").replace("\r\n", "\n")
        if current != rendered:
            print(f"FDS publication reference is stale: {args.output}", file=sys.stderr)
            return 1
        print(f"FDS publication reference is current: {len(teachers)} teachers; {len(errors)} errors")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=args.output.parent
    ) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    temporary.replace(args.output)
    print(f"Wrote {args.output}: {len(teachers)} teachers; {len(errors)} errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
