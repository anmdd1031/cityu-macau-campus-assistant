#!/usr/bin/env python3
"""Build or check the FDS faculty reference from official public pages.

This script intentionally uses only the Python standard library. It crawls the
Chinese and English Academic Staff listings, aligns profiles by official list order, and
extracts public role, supervisor qualification, research directions, and
homepage links. It stores only publicly verifiable CityU work emails and never
stores phone numbers or office locations.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path


BASE_URL = "https://fds.cityu.edu.mo"
LIST_PAGES = 6
USER_AGENT = "cityu-macau-campus-assistant/1.0 (+public knowledge maintenance)"

RESEARCH_LABELS = {
    "research direction",
    "research directions",
    "research interest",
    "research interests",
    "research area",
    "research areas",
    "research field",
    "research fields",
    "research focus",
    "research focuses",
    "research expertise",
    "research and expertise",
}

SECTION_ENDINGS = {
    "research and publication",
    "research and publications",
    "research and publishing",
    "research project",
    "research projects",
    "research experience",
    "scientific research experience",
    "research & publications",
    "research publications",
    "selected publications",
    "select publication in recent three years",
    "publication",
    "publications",
    "academic awards",
    "professional association",
    "scientific research projects",
    "project fund",
    "projects",
    "paper results",
    "patents",
    "prev",
    "back",
    "next",
}

# Ordered broad-to-specific tags. Multiple matches are retained.
TAG_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("人工智能与机器学习", ("artificial intelligence", "machine learning", "deep learning", "neural network", "reinforcement learning", "multi-agent learning", "ai for science")),
    ("大语言模型与生成式 AI", ("large language model", "large model", "generative ai", "generative model", "multimodal generation", "aigc")),
    ("数据科学与数据挖掘", ("data science", "data mining", "data analytics", "big data", "data analysis", "business intelligence", "cluster analysis", "predictive analytics")),
    ("自然语言处理", ("natural language processing", "text mining", "sentiment analysis", "language model")),
    ("计算机视觉与多媒体", ("computer vision", "image processing", "video", "3d reconstruction", "point cloud", "multimedia", "visual recognition", "medical image")),
    ("隐私计算与联邦学习", ("privacy", "federated learning", "federated", "machine unlearning", "differential privacy", "privacy computing")),
    ("网络空间安全与 AI 安全", ("cybersecurity", "cyber security", "cyberspace security", "network security", "information security", "ai security", "artificial intelligence security", "system security", "model attack", "adversarial attack", "malware")),
    ("密码学、区块链与可信计算", ("cryptography", "encryption", "blockchain", "trusted computing", "access control", "authentication")),
    ("云计算、分布式系统与边缘计算", ("cloud computing", "distributed system", "edge computing", "parallel computing", "gpu computing", "mlsys", "resource scheduling")),
    ("物联网与无线通信", ("internet of things", "iot", "wireless", "communication network", "sensor network", "vehicular network")),
    ("机器人与智能交通", ("robot", "autonomous driving", "intelligent transportation", "smart transportation", "navigation", "vehicle")),
    ("医疗健康与生物信息", ("healthcare", "medical", "biomedical", "bioinformatics", "health data", "digital health")),
    ("优化、运筹与计算数学", ("optimization", "operations research", "operational research", "algorithm", "game theory", "mathematical", "probability", "functional analysis", "differential equation")),
    ("统计学习与概率建模", ("bayesian statistics", "statistical learning", "probabilistic model", "statistical inference")),
    ("数据库、知识图谱与信息检索", ("database", "knowledge graph", "information retrieval", "recommendation system", "recommender system", "semantic web")),
    ("软件工程与程序分析", ("software engineering", "program analysis", "software testing", "programming language", "code generation")),
    ("人机交互与教育技术", ("human-computer interaction", "human computer interaction", "education", "learning analytics", "smart education", "voice interaction", "affective computing", "user behavior")),
    ("信号处理与时序分析", ("signal processing", "time series analysis")),
    ("科学智能与计算物理", ("high energy physics", "cosmology", "physics for ai", "ai for science")),
    ("信息系统与数字化应用", ("information system", "information technology applications", "technology and user behavior")),
    ("智慧城市与空间计算", ("smart city", "smart cities", "urban", "geospatial", "spatial", "geographic information")),
    ("金融与商业数据", ("financial", "finance", "fintech", "marketing", "e-commerce", "economics")),
]

# Keep explicit, reviewable exceptions close to the extractor. Values are only
# used when the official page does not expose a recognizable research section.
TAG_OVERRIDES: dict[str, tuple[str, ...]] = {
    "177": ("网络空间安全与 AI 安全", "隐私计算与联邦学习", "云计算、分布式系统与边缘计算"),
}

# Do not silently repair malformed addresses shown by a source.
EMAIL_WARNINGS: dict[str, str] = {
    "428": "官网当前显示 hgzhu@cityu.edu，域名格式疑似不完整，请通过官方主页确认",
}


@dataclass
class Link:
    text: str
    href: str


class TextAndLinkParser(HTMLParser):
    BLOCKS = {
        "h1", "h2", "h3", "h4", "h5", "p", "li", "div", "section",
        "article", "td", "th", "br",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self.links: list[Link] = []
        self._buffer: list[str] = []
        self._anchor_href: str | None = None
        self._anchor_text: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
            return
        if self._ignored_depth:
            return
        if tag in self.BLOCKS:
            self._flush()
        if tag == "a":
            self._anchor_href = dict(attrs).get("href")
            self._anchor_text = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            if self._ignored_depth:
                self._ignored_depth -= 1
            return
        if self._ignored_depth:
            return
        if tag == "a" and self._anchor_href:
            self.links.append(Link(clean_text(" ".join(self._anchor_text)), self._anchor_href))
            self._anchor_href = None
            self._anchor_text = []
        if tag in self.BLOCKS:
            self._flush()

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        self._buffer.append(data)
        if self._anchor_href is not None:
            self._anchor_text.append(data)

    def close(self) -> None:
        super().close()
        self._flush()

    def _flush(self) -> None:
        text = clean_text(" ".join(self._buffer))
        if text and (not self.lines or self.lines[-1] != text):
            self.lines.append(text)
        self._buffer = []


@dataclass
class Faculty:
    member_id: str
    chinese_name: str
    english_name: str
    role: str
    qualification: str
    email: str | None
    email_note: str | None
    tags: list[str]
    research_summary: str
    evidence: str
    official_url: str
    personal_url: str | None


def clean_text(value: str) -> str:
    value = html.unescape(value).replace("\xa0", " ")
    value = re.sub(r"\b([A-Z])\s+([a-z]{2,})", r"\1\2", value)
    return re.sub(r"\s+", " ", value).strip()


def normalized_label(value: str) -> str:
    value = clean_text(value).lower().rstrip(":：")
    return re.sub(r"[^a-z0-9& /-]", "", value).strip()


def fetch(url: str, timeout: float, retries: int, delay: float) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                result = response.read().decode(charset, errors="replace")
            if delay:
                time.sleep(delay)
            return result
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(min(2 ** attempt, 4))
    raise RuntimeError(f"Unable to fetch {url}: {last_error}")


def parse_document(source: str) -> TextAndLinkParser:
    parser = TextAndLinkParser()
    parser.feed(source)
    parser.close()
    return parser


def listing_url(language: str, page: int) -> str:
    prefix = "/en" if language == "en" else ""
    query = "" if page == 1 else f"?p={page}"
    return f"{BASE_URL}{prefix}/members{query}"


def collect_listing(language: str, timeout: float, retries: int, delay: float) -> list[tuple[str, str]]:
    members: list[tuple[str, str]] = []
    seen: set[str] = set()
    path_prefix = "/en/members/" if language == "en" else "/members/"
    for page in range(1, LIST_PAGES + 1):
        document = parse_document(fetch(listing_url(language, page), timeout, retries, delay))
        for link in document.links:
            absolute = urllib.parse.urljoin(BASE_URL, link.href)
            parsed = urllib.parse.urlparse(absolute)
            if path_prefix not in parsed.path or not link.text:
                continue
            match = re.search(r"/members/(\d+)$", parsed.path)
            if match and match.group(1) not in seen:
                seen.add(match.group(1))
                members.append((match.group(1), link.text))
    return members


def find_research_section(lines: list[str]) -> tuple[str, bool]:
    start = None
    for index, line in enumerate(lines):
        label = normalized_label(line)
        if label in RESEARCH_LABELS:
            start = index + 1
            break
        for candidate in RESEARCH_LABELS:
            if label.startswith(candidate + " "):
                return clean_text(line[len(candidate):].lstrip(":： ")), True
    if start is not None:
        collected: list[str] = []
        for line in lines[start:]:
            label = normalized_label(line)
            if label in SECTION_ENDINGS or any(label.startswith(item) for item in SECTION_ENDINGS):
                break
            if line not in collected:
                collected.append(line)
        text = clean_text(" ".join(collected))
        if text:
            return text, True

    # Use only the member body after its title, not the site navigation.
    body_start = next((i for i, line in enumerate(lines) if "professor" in line.lower()), 0)
    body = " ".join(lines[body_start:])
    body = re.split(r"\b(?:Prev|Back|Next)\b", body, maxsplit=1, flags=re.IGNORECASE)[0]
    return clean_text(body), False


def supervisor_qualification(text: str) -> str:
    lowered = text.lower()
    doctoral = bool(re.search(r"(?:ph\.?d\.?|doctoral|doctor)\s*(?:student\s*)?supervisor", lowered))
    master = bool(re.search(r"master(?:'s)?\s*(?:student\s*)?supervisor", lowered))
    if doctoral and master:
        return "博士生导师、硕士生导师"
    if doctoral:
        return "博士生导师"
    if master:
        return "硕士生导师"
    return "官网未明确标注导师资格"


def match_tags(member_id: str, research_text: str) -> list[str]:
    lowered = research_text.lower()
    tags = [tag for tag, terms in TAG_RULES if any(term in lowered for term in terms)]
    for tag in TAG_OVERRIDES.get(member_id, ()):
        if tag not in tags:
            tags.append(tag)
    return tags


def find_personal_homepage(source: str) -> str | None:
    match = re.search(
        r"(?is)personal\s*(?:home\s*page|homepage|website)[\s\S]{0,600}?href=[\"']([^\"']+)[\"']",
        source,
    )
    if not match:
        return None
    value = html.unescape(match.group(1)).strip()
    absolute = urllib.parse.urljoin(BASE_URL, value)
    parsed = urllib.parse.urlparse(absolute)
    return absolute if parsed.scheme in {"http", "https"} else None


def find_official_email(source: str) -> str | None:
    # Several profiles split the local part, @ sign, and domain across spans.
    # Strip markup before matching so those official addresses remain readable.
    visible_text = html.unescape(re.sub(r"(?is)<[^>]+>", "", source))
    emails = re.findall(
        r"(?i)\b[A-Z0-9._%+-]+@(?:[A-Z0-9-]+\.)*(?:cityu\.edu\.mo|cityu\.mo)\b",
        visible_text,
    )
    return emails[0].lower() if emails else None


def short_summary(text: str, limit: int = 240) -> str:
    text = clean_text(text).replace("|", "\\|")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip(" ,;，；。") + "…"


def clean_chinese_name(value: str) -> str:
    value = re.sub(r"(?:教授|副教授|助理教授|講師|學院負責人|副院長|課程主任|副校長).*$", "", value).strip()
    return value or "官网未提供"


def clean_english_name(value: str) -> str:
    value = re.sub(
        r"^(?:Professor|Associate Professor(?: \(research\))?|Assistant Professor(?: \(Research\))?|Lecturer|Prof)\s+",
        "",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(r"\s+(?:Vice President|Faculty Head|Vice Dean|Programme Coordinator)$", "", value, flags=re.IGNORECASE)
    return value.strip() or "Not provided"


def build_faculty(timeout: float, retries: int, delay: float, workers: int) -> tuple[list[Faculty], list[str]]:
    english = collect_listing("en", timeout, retries, delay)
    chinese = collect_listing("zh", timeout, retries, delay)
    if len(english) != 58:
        raise RuntimeError(f"Expected 58 English Academic Staff profiles, found {len(english)}")
    if len(chinese) != 58:
        raise RuntimeError(f"Expected 58 Chinese Academic Staff profiles, found {len(chinese)}")

    review: list[str] = []
    faculty: list[Faculty] = []
    profile_urls = [f"{BASE_URL}/en/members/{member_id}" for member_id, _ in english]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        sources = list(executor.map(lambda url: fetch(url, timeout, retries, delay), profile_urls))

    for position, (member_id, listing_title) in enumerate(english):
        _chinese_id, chinese_title = chinese[position]
        official_url = profile_urls[position]
        source = sources[position]
        document = parse_document(source)
        research_text, explicit = find_research_section(document.lines)
        tags = match_tags(member_id, research_text)
        if not tags:
            tags = ["官网方向待人工归类"]
            review.append(f"{member_id} {listing_title}: no normalized research tag")
        if not explicit:
            review.append(f"{member_id} {listing_title}: direction inferred from profile/outputs")
        if len(research_text) < 8:
            review.append(f"{member_id} {listing_title}: research summary is too short")

        email = find_official_email(source)
        email_note = EMAIL_WARNINGS.get(member_id)
        if email_note:
            review.append(f"{member_id} {listing_title}: {email_note}")

        faculty.append(
            Faculty(
                member_id=member_id,
                chinese_name=clean_chinese_name(chinese_title),
                english_name=clean_english_name(listing_title),
                role=listing_title,
                qualification=supervisor_qualification(" ".join(document.lines)),
                email=email,
                email_note=email_note,
                tags=tags,
                research_summary=short_summary(research_text),
                evidence="官网明确" if explicit else "根据官网简介、授课或成果推断",
                official_url=official_url,
                personal_url=find_personal_homepage(source),
            )
        )
    return faculty, review


def markdown(faculty: list[Faculty], review: list[str], verified: str) -> str:
    lines = [
        "# 澳门城市大学数据科学学院师资与导师方向索引",
        "",
        "> 数据来源：澳门城市大学数据科学学院官网 Academic Staff 及教师个人页。",
        f"> 核验日期：{verified}。",
        f"> 当前收录：{len(faculty)} 名本校 Academic Staff；不含 Academic Advisors、External Instructors 和行政人员。",
        "> 近期论文证据：[fds_faculty_publications.md](fds_faculty_publications.md)。",
        "",
        "## 使用边界",
        "",
        "- 本索引用于按公开研究方向筛选候选教师，不构成录取、招生名额或接收意愿判断。",
        "- 只有官网明确标注博士生导师或硕士生导师时，才能使用相应称谓；否则只能称为方向相关教师。",
        "- 研究方向可以有多个。`根据官网简介、授课或成果推断` 不等同于教师本人声明。",
        "- 联系方式只使用官网公开的 `cityu.edu.mo` / `cityu.mo` 工作邮箱，并同时提供官方主页；不收录私人邮箱、电话或办公室信息。",
        "",
        "## 推荐与展示规则",
        "",
        "1. 先按本科科研、硕士或博士阶段筛选导师资格，再匹配研究方向。",
        "2. 按官网明确方向、多关键词匹配、简介或成果补充、间接关联的顺序判断相关度，不输出虚假百分比。",
        "3. 需要导师推荐或最新研究主题时，再读取论文证据库；官网明确方向优先，论文主题只作补充，不按论文数量排名。",
        "4. 匹配不超过 5 人时列出全部；超过 5 人时默认列出相关度最高的 5 人，信息较少时可列 3 人。",
        "5. 省略候选时写明总人数、展示人数、未展开人数，并提示用户可以要求“显示全部相关教师”。",
        "6. 同等相关度按下表官网顺序展示，不按职称、论文数量或知名度排序。",
        "7. 用户明确要求全部名单时，列出所有符合条件者。",
        "",
        "## 师资索引",
        "",
        "| 序号 | 教师 | 职称/职务 | 导师资格 | 校内工作邮箱 | 标准化研究方向 | 官网方向摘要 | 依据 | 官方主页 | 个人主页 |",
        "|---:|---|---|---|---|---|---|---|---|---|",
    ]
    for index, item in enumerate(faculty, 1):
        personal = f"[访问]({item.personal_url})" if item.personal_url else "官网未提供"
        email_link = (
            f"[{item.email}](mailto:{item.email})"
            if item.email
            else item.email_note or "官网未提供可验证邮箱"
        )
        lines.append(
            f"| {index} | {item.chinese_name}（{item.english_name}） | {item.role} | "
            f"{item.qualification} | {email_link} | {'；'.join(item.tags)} | {item.research_summary} | "
            f"{item.evidence} | [官方页]({item.official_url}) | {personal} |"
        )

    lines.extend([
        "",
        "## 人工复核记录",
        "",
    ])
    if review:
        lines.extend(f"- {entry}" for entry in review)
    else:
        lines.append("- 本次自动提取未发现待复核项目。")
    lines.extend([
        "",
        "## 官方入口",
        "",
        f"- [FDS Academic Staff]({BASE_URL}/en/members)",
        f"- [FDS 师资队伍]({BASE_URL}/members)",
        "- 教师名单、职称、导师资格、研究方向和主页可能变化，使用时应优先核验上述入口。",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    default_output = Path(__file__).resolve().parents[1] / "references" / "fds_faculty.md"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--check", action="store_true", help="Do not write; fail if generated content differs")
    parser.add_argument("--date", help="Verification date in YYYY-MM-DD; defaults to today when writing")
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--delay", type=float, default=0.15, help="Delay after each successful request")
    parser.add_argument("--workers", type=int, default=4, choices=range(1, 9), help="Concurrent profile requests")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    verified = args.date
    if verified is None and args.check and args.output.exists():
        existing = args.output.read_text(encoding="utf-8")
        match = re.search(r"核验日期：(\d{4}-\d{2}-\d{2})", existing)
        verified = match.group(1) if match else None
    verified = verified or date.today().isoformat()
    faculty, review = build_faculty(args.timeout, args.retries, args.delay, args.workers)
    rendered = markdown(faculty, review, verified)

    if args.check:
        if not args.output.exists():
            print(f"Missing generated reference: {args.output}", file=sys.stderr)
            return 1
        current = args.output.read_text(encoding="utf-8").replace("\r\n", "\n")
        if current != rendered:
            print(f"FDS faculty reference is stale: {args.output}", file=sys.stderr)
            return 1
        print(f"FDS faculty reference is current: {len(faculty)} profiles; {len(review)} review notes")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=args.output.parent) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    temporary.replace(args.output)
    print(f"Wrote {args.output}: {len(faculty)} profiles; {len(review)} review notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
