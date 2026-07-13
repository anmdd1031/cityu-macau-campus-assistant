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
import http.client
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
    "研究方向",
    "研究興趣",
    "研究兴趣",
    "研究領域",
    "研究领域",
}

EDUCATION_LABELS = {
    "education", "education experience", "educational background",
    "educational experience", "educational qualifications", "academic qualifications",
}
COURSE_LABELS = {
    "course taught", "courses taught", "subjects taught", "teaching course",
    "teaching courses", "course s taught", "teaching course s", "courses", "teaching",
}
PROJECT_LABELS = {
    "research project", "research projects", "scientific research project",
    "scientific research projects", "select scientific research projects",
    "科研項目", "科研项目", "科研專案", "科研专案", "研究項目", "研究项目",
}
PUBLICATION_LABELS = {
    "publication", "publications", "selected publications",
    "select publication in recent three years", "research and publishing",
    "research and publications in recent years", "research and publication",
    "研究及出版", "研究與出版", "研究与出版", "近年研究及出版",
    "部分研究及出版", "研究成果", "論文成果", "论文成果", "近三年部分研究成果",
}
EXPERIENCE_LABELS = {
    "research experience", "scientific research experience",
    "科研經歷", "科研经历", "研究經歷", "研究经历",
}
PROFILE_SECTION_LABELS = (
    RESEARCH_LABELS | EDUCATION_LABELS | COURSE_LABELS | PROJECT_LABELS |
    PUBLICATION_LABELS | EXPERIENCE_LABELS | {
        "position", "incumbent", "current", "work experience", "scientific research experience",
        "personal profile", "profile", "academic appointment /service",
        "academic appointment/service", "honors and awards", "awards", "patent",
        "patents", "recruitment", "contact information",
        "研究及出版", "研究與出版", "研究与出版", "科研項目", "科研项目",
        "學術獎項", "学术奖项", "專業屬會", "专业属会",
        "近三年部分研究成果", "近年研究及出版", "部分研究及出版",
        "研究成果", "論文成果", "论文成果", "任教科目", "教授科目",
        "學術組識", "学术组织", "科研專案", "科研专案",
        "現任", "现任", "曾任教科目",
    }
)

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
    "研究及出版",
    "研究與出版",
    "研究与出版",
    "科研項目",
    "科研项目",
    "科研專案",
    "科研专案",
    "學術獎項",
    "学术奖项",
    "專業屬會",
    "专业属会",
    "科研經歷",
    "科研经历",
    "研究經歷",
    "研究经历",
    "近三年部分研究成果",
    "近年研究及出版",
    "部分研究及出版",
    "研究成果",
    "論文成果",
    "论文成果",
    "任教科目",
    "教授科目",
    "學術組識",
    "学术组织",
    "現任",
    "现任",
    "曾任教科目",
    "上一個",
    "上一个",
    "返回",
    "下一個",
    "下一个",
    "prev",
    "back",
    "next",
}

# Ordered broad-to-specific tags. Multiple matches are retained.
TAG_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("人工智能与机器学习", ("ai", "人工智能", "人工智慧", "機器學習", "机器学习", "深度學習", "深度学习", "強化學習", "强化学习", "圖神經網絡", "图神经网络", "連續學習", "连续学习", "類腦智能", "类脑智能", "具身智能", "artificial intelligence", "machine learning", "deep learning", "neural network", "reinforcement learning", "multi-agent learning", "brain-inspired intelligence", "ai for science", "swarm intelligence")),
    ("大语言模型与生成式 AI", ("大語言模型", "大语言模型", "生成式人工智能", "生成式人工智慧", "檢索增強生成", "检索增强生成", "模型上下文協議", "模型上下文协议", "多模態生成", "多模态生成", "large language model", "large model", "llm", "genai", "generative ai", "generative model", "generate model", "multimodal generation", "multi-modal generation", "visual content generation", "aigc")),
    ("数据科学与数据挖掘", ("數據科學", "数据科学", "數據挖掘", "数据挖掘", "大數據", "大数据", "聚類分析", "聚类分析", "預測分析", "预测分析", "data science", "data mining", "data analytics", "big data", "data analysis", "business intelligence", "cluster analysis", "predictive analytics")),
    ("自然语言处理", ("自然語言處理", "自然语言处理", "natural language processing", "text mining", "sentiment analysis", "language model")),
    ("计算机视觉与多媒体", ("計算機視覺", "计算机视觉", "圖像處理", "图像处理", "圖像質量", "图像质量", "視覺顯著", "视觉显著", "深度僞造", "深度伪造", "多模態", "多模态", "多媒體", "多媒体", "computer vision", "image processing", "video", "3d reconstruction", "point cloud", "multimedia", "visual recognition", "medical image")),
    ("隐私计算与联邦学习", ("隱私計算", "隐私计算", "隱私保護", "隐私保护", "聯邦學習", "联邦学习", "差分隱私", "差分隐私", "privacy", "federated learning", "federated", "machine unlearning", "differential privacy", "privacy computing")),
    ("网络空间安全与 AI 安全", ("網絡安全", "网络安全", "網絡空間安全", "网络空间安全", "信息安全", "對抗網絡", "对抗网络", "cybersecurity", "cyber security", "cyberspace security", "network security", "information security", "ai security", "artificial intelligence security", "system security", "model security", "model backdoor", "model attack", "adversarial machine learning", "adversarial attack", "malware")),
    ("密码学、区块链与可信计算", ("密碼學", "密码学", "區塊鏈", "区块链", "cryptography", "encryption", "blockchain", "trusted computing", "access control", "authentication")),
    ("云计算、分布式系统与边缘计算", ("cloud computing", "distributed system", "edge computing", "mobile computing", "parallel computing", "gpu computing", "mlsys", "resource scheduling")),
    ("物联网与无线通信", ("internet of things", "iot", "wireless", "communication network", "sensor network", "vehicular network")),
    ("机器人与智能交通", ("機器人", "机器人", "具身智能", "智能交通", "無人機", "无人机", "低空態勢", "低空态势", "集群決策", "集群决策", "robot", "embodied ai", "embodied intelligence", "uav", "drone", "swarm intelligence", "autonomous driving", "intelligent transportation", "smart transportation", "navigation", "vehicle")),
    ("医疗健康与生物信息", ("智慧醫療", "智慧医疗", "智能醫療", "智能医疗", "醫療", "医疗", "生物信息", "數字健康", "数字健康", "healthcare", "medical", "biomedicine", "biomedical", "bioinformatics", "health data", "digital health")),
    ("优化、运筹与计算数学", ("優化", "优化", "汎函分析", "泛函分析", "微分方程", "optimization", "operations research", "operational research", "algorithm", "game theory", "mathematical", "probability", "functional analysis", "differential equation")),
    ("统计学习与概率建模", ("貝葉斯統計", "贝叶斯统计", "bayesian statistics", "statistical learning", "probabilistic model", "statistical inference")),
    ("数据库、知识图谱与信息检索", ("智能推薦", "智能推荐", "推薦系統", "推荐系统", "知識圖譜", "知识图谱", "語義集成", "语义集成", "database", "knowledge graph", "information retrieval", "recommendation", "recommender system", "semantic integration", "semantic web")),
    ("软件工程与程序分析", ("software engineering", "program analysis", "software testing", "programming language", "code generation")),
    ("人机交互与教育技术", ("智能語音交互", "智能语音交互", "情感計算", "情感计算", "使用者行為", "用户行为", "human-computer interaction", "human computer interaction", "education", "learning analytics", "smart education", "voice interaction", "affective computing", "user behavior")),
    ("信号处理与时序分析", ("signal processing", "time series analysis")),
    ("科学智能与计算物理", ("high energy physics", "cosmology", "physics for ai", "ai for science")),
    ("信息系统与数字化应用", ("資訊系統", "信息系统", "資訊科技應用", "信息科技应用", "電子商務技術", "电子商务技术", "information system", "information technology applications", "technology and user behavior")),
    ("智慧城市与空间计算", ("空間信息", "空间信息", "smart city", "smart cities", "urban", "geospatial", "spatial", "geographic information")),
    ("金融与商业数据", ("金融", "電力市場", "电力市场", "風險規避", "风险规避", "電子商務", "电子商务", "financial", "finance", "fintech", "marketing", "e-commerce", "e -commerce", "economics")),
]

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
    official_evidence_summary: str
    official_experience: str | None
    official_experience_source: str | None
    official_projects: str | None
    official_projects_source: str | None
    official_publications: str | None
    official_publications_source: str | None
    recruitment_summary: str
    evidence: str
    official_url: str
    chinese_url: str
    english_url: str
    personal_url: str | None


def clean_text(value: str) -> str:
    value = html.unescape(value).replace("\xa0", " ")
    value = re.sub(r"\b([A-Z])\s+([a-z]{2,})", r"\1\2", value)
    return re.sub(r"\s+", " ", value).strip()


def normalized_label(value: str) -> str:
    value = clean_text(value).lower().rstrip(":：")
    return re.sub(r"[^a-z0-9\u3400-\u9fff& /-]", "", value).strip()


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
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError) as error:
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
            inline_boundary = re.search(r"(?:主持\s*)?科研\s*(?:項目|项目|專案|专案)", line)
            if inline_boundary:
                prefix = clean_text(line[: inline_boundary.start()])
                if prefix and prefix not in collected:
                    collected.append(prefix)
                break
            label = normalized_label(line)
            other_sections = PROFILE_SECTION_LABELS - RESEARCH_LABELS
            if (
                label in SECTION_ENDINGS
                or any(label.startswith(item) for item in SECTION_ENDINGS)
                or label in other_sections
                or any(label.startswith(item + " ") for item in other_sections)
                or re.match(r"(?i)^currently\s+recruiting\b", line)
                or re.match(r"^目前招聘", line)
            ):
                break
            if line not in collected:
                collected.append(line)
        text = clean_text(" ".join(collected))
        if text:
            return text, True

    for line in lines:
        match = re.search(r"(?i)\b(?:specializes|specialises)\s+in\s+(.+?)(?:\.|$)", line)
        if match:
            return clean_text(match.group(1)), True

    return "", False


def find_section(lines: list[str], labels: set[str], limit: int | None = None) -> str | None:
    """Extract an official-profile section without crossing into another heading."""
    start: int | None = None
    inline = ""
    for index, line in enumerate(lines):
        if labels is PROJECT_LABELS:
            project_heading = re.search(r"(?:主持\s*)?科研\s*(?:項目|项目|專案|专案)", line)
            if project_heading:
                inline = clean_text(line[project_heading.end():].lstrip(":： "))
                start = index + 1
                break
        label = normalized_label(line)
        if label in labels:
            start = index + 1
            break
        for candidate in labels:
            if label.startswith(candidate + " "):
                inline = clean_text(line[len(candidate):].lstrip(":： "))
                start = index + 1
                break
        if start is not None:
            break
    if start is None:
        return None

    collected = [inline] if inline else []
    for line in lines[start:]:
        label = normalized_label(line)
        if (
            label in PROFILE_SECTION_LABELS
            or any(label.startswith(heading + " ") for heading in PROFILE_SECTION_LABELS)
            or label in SECTION_ENDINGS
            or any(label.startswith(heading + " ") for heading in SECTION_ENDINGS)
        ):
            break
        if line not in collected:
            collected.append(line)
        if limit is not None and len(" ".join(collected)) >= limit:
            break
    value = clean_text(" ".join(collected))
    if not value:
        return None
    return short_summary(value, limit) if limit is not None else value.replace("|", "\\|")


def find_recruitment(lines: list[str]) -> str | None:
    for line in lines:
        if normalized_label(line) == "recruitment":
            continue
        if re.search(r"(?i)\bcurrently\s+recruiting|scholarships?\s+are\s+offered", line):
            return short_summary(line, 220)
    return None


def choose_section(
    chinese_lines: list[str], english_lines: list[str], labels: set[str]
) -> tuple[str | None, str | None]:
    chinese_value = find_section(chinese_lines, labels)
    if chinese_value:
        return chinese_value, "中文官网"
    english_value = find_section(english_lines, labels)
    return (english_value, "英文官网") if english_value else (None, None)


def official_evidence_summary(
    index: int,
    experience: str | None,
    experience_source: str | None,
    project: str | None,
    project_source: str | None,
    publication: str | None,
    publication_source: str | None,
) -> str:
    def status(label: str, value: str | None, source: str | None) -> str:
        return f"{label}：有（{source}）" if value else f"{label}：官网未提供"

    return "；".join([
        status("科研经历", experience, experience_source),
        status("研究项目", project, project_source),
        status("论文成果", publication, publication_source),
        f"[读取本地完整资料](fds_official_evidence.md#teacher-{index})",
    ])


def supervisor_qualification(text: str) -> str:
    lowered = text.lower()
    doctoral = bool(re.search(r"(?:ph\.?d\.?|doctoral|doctor)\s*(?:student\s*)?supervisor|博士生?[導导]師", lowered))
    master = bool(re.search(r"master(?:'s)?\s*(?:student\s*)?supervisor|[碩硕]士生?[導导]師", lowered))
    if doctoral and master:
        return "博士生导师、硕士生导师"
    if doctoral:
        return "博士生导师"
    if master:
        return "硕士生导师"
    return "官网未明确标注导师资格"


def match_tags(research_text: str) -> list[str]:
    lowered = research_text.lower()
    def matches(term: str) -> bool:
        return bool(re.search(r"\bai\b", lowered)) if term == "ai" else term in lowered

    return [tag for tag, terms in TAG_RULES if any(matches(term) for term in terms)]


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
    chinese_profile_urls = [f"{BASE_URL}/members/{member_id}" for member_id, _ in chinese]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        sources = list(executor.map(lambda url: fetch(url, timeout, retries, delay), profile_urls))
        chinese_sources = list(executor.map(lambda url: fetch(url, timeout, retries, delay), chinese_profile_urls))

    for position, (member_id, listing_title) in enumerate(english):
        chinese_id, chinese_title = chinese[position]
        official_url = profile_urls[position]
        source = sources[position]
        document = parse_document(source)
        chinese_source = chinese_sources[position]
        chinese_document = parse_document(chinese_source)
        chinese_research, chinese_explicit = find_research_section(chinese_document.lines)
        english_research, english_explicit = find_research_section(document.lines)
        if chinese_explicit and chinese_research:
            research_text, explicit, direction_source = chinese_research, True, "中文官网明确"
            official_url = chinese_profile_urls[position]
        else:
            research_text, explicit, direction_source = english_research, english_explicit, "英文官网明确" if english_explicit else "官网未明确列出研究方向"
        experience, experience_source = choose_section(
            chinese_document.lines, document.lines, EXPERIENCE_LABELS
        )
        project, project_source = choose_section(
            chinese_document.lines, document.lines, PROJECT_LABELS
        )
        publication, publication_source = choose_section(
            chinese_document.lines, document.lines, PUBLICATION_LABELS
        )
        tags = match_tags(research_text)
        if not tags:
            tags = ["官网未明确列出研究方向"]
            review.append(f"{member_id} {listing_title}: no normalized research tag")
        if not explicit:
            review.append(f"{member_id} {listing_title}: direction inferred from profile/outputs")
        if len(research_text) < 4:
            review.append(f"{member_id} {listing_title}: research summary is too short")

        email = find_official_email(chinese_source) or find_official_email(source)
        email_note = EMAIL_WARNINGS.get(member_id) if not email else None
        if email_note:
            review.append(f"{member_id} {listing_title}: {email_note}")

        faculty.append(
            Faculty(
                member_id=member_id,
                chinese_name=clean_chinese_name(chinese_title),
                english_name=clean_english_name(listing_title),
                role=listing_title,
                qualification=supervisor_qualification(" ".join(chinese_document.lines + document.lines)),
                email=email,
                email_note=email_note,
                tags=tags,
                research_summary=short_summary(research_text) if research_text else "官网未明确列出研究方向",
                official_evidence_summary=official_evidence_summary(
                    position + 1,
                    experience,
                    experience_source,
                    project,
                    project_source,
                    publication,
                    publication_source,
                ),
                official_experience=experience,
                official_experience_source=experience_source,
                official_projects=project,
                official_projects_source=project_source,
                official_publications=publication,
                official_publications_source=publication_source,
                recruitment_summary=find_recruitment(document.lines) or "官网未公开招募说明",
                evidence=direction_source,
                official_url=official_url,
                chinese_url=f"{BASE_URL}/members/{chinese_id}",
                english_url=f"{BASE_URL}/en/members/{member_id}",
                personal_url=find_personal_homepage(source),
            )
        )
    return faculty, review


def publication_summaries(path: Path) -> dict[int, str]:
    """Read compact topic summaries from the optional paper index."""
    if not path.exists():
        return {}
    summaries: dict[int, str] = {}
    current: int | None = None
    count: int | None = None
    themes: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"## (\d+)\. ", line)
        if heading:
            if current is not None and count is not None:
                summaries[current] = f"{themes or '主题待人工归类'}；Crossref 索引 {count} 篇；外部资料有限（E 级）"
            current, count, themes = int(heading.group(1)), None, None
            continue
        matched = re.match(r"- Crossref 高置信匹配：共 (\d+) 篇", line)
        if matched:
            count = int(matched.group(1))
        matched = re.match(r"- 论文佐证方向：(.+?)。$", line)
        if matched:
            themes = matched.group(1)
    if current is not None and count is not None:
        summaries[current] = f"{themes or '主题待人工归类'}；Crossref 索引 {count} 篇；外部资料有限（E 级）"
    return summaries


def official_evidence_markdown(faculty: list[Faculty], verified: str) -> str:
    lines = [
        "# 澳门城市大学数据科学学院导师官网科研证据",
        "",
        "> 数据来源：澳门城市大学数据科学学院中英文教师个人页。",
        f"> 核验日期：{verified}。",
        "> 本文件保存官网公开的完整科研经历、研究项目和论文成果栏目，供官网访问失败或需要完整上下文时按教师读取。",
        "> 官网页面可能未及时更新，也不保证列出全部成果；本地内容只能作为参考，不能证明项目仍在进行、成果列表完整或教师当前招生。",
        "> 默认导师匹配请先读取 [fds_mentors.md](fds_mentors.md)；只有需要科研证据详情时再读取本文件中的对应教师章节。",
        "",
        "## 快速索引",
        "",
    ]
    for start in range(0, len(faculty), 10):
        group = faculty[start : start + 10]
        lines.append("- " + "；".join(
            f"[{index}. {item.chinese_name}](#teacher-{index})"
            for index, item in enumerate(group, start + 1)
        ))

    for index, item in enumerate(faculty, 1):
        lines.extend([
            "",
            f'<a id="teacher-{index}"></a>',
            "",
            f"## {index}. {item.chinese_name}（{item.english_name}）",
            "",
            f"- 中文官网：[访问]({item.chinese_url})",
            f"- 英文官网：[访问]({item.english_url})",
            f"- 核验日期：{verified}",
            "",
            "### 科研经历",
            "",
            f"来源：{item.official_experience_source or '官网未提供'}。",
            "",
            item.official_experience or "官网未提供。",
            "",
            "### 研究项目",
            "",
            f"来源：{item.official_projects_source or '官网未提供'}。",
            "",
            item.official_projects or "官网未提供。",
            "",
            "### 论文成果",
            "",
            f"来源：{item.official_publications_source or '官网未提供'}。",
            "",
            item.official_publications or "官网未提供。",
        ])
    lines.append("")
    return "\n".join(lines)


def markdown(
    faculty: list[Faculty], review: list[str], verified: str, paper_summaries: dict[int, str]
) -> str:
    chinese_directions = sum(item.evidence == "中文官网明确" for item in faculty)
    english_fallbacks = sum(item.evidence == "英文官网明确" for item in faculty)
    lines = [
        "# 澳门城市大学数据科学学院导师基础画像",
        "",
        "> 数据来源：澳门城市大学数据科学学院官网 Academic Staff 及教师个人页。",
        f"> 核验日期：{verified}。",
        "> 本表来源等级：1（学院官方教师主页）；个人主页仅作为官方页公开的补充入口。",
        f"> 当前收录：{len(faculty)} 名本校 Academic Staff；不含 Academic Advisors、External Instructors 和行政人员。",
        f"> 方向来源：中文官网优先（{chinese_directions} 人）；中文页未明确时回退英文官网（{english_fallbacks} 人）。",
        "> 官网完整科研证据：[fds_official_evidence.md](fds_official_evidence.md)；论文检索索引：[fds_papers.md](fds_papers.md)；导师匹配规则：[fds_rules.md](fds_rules.md)。",
        "",
        "## 使用边界",
        "",
        "- 本索引用于按公开研究方向筛选候选教师，不构成录取、招生名额或接收意愿判断。",
        "- 只有官网明确标注博士生导师或硕士生导师时，才能使用相应称谓；否则只能称为方向相关教师。",
        "- `标准化检索标签` 只根据官网个人页明确展示的研究方向或明确的专业方向表述映射，不使用教育背景、授课或论文成果补充标签。",
        "- 科研证据列只显示三类资料是否存在及来源；完整正文按需读取 `fds_official_evidence.md`，不再使用可能遗漏关键信息的截断摘要。",
        "- 官网列出的科研经历、研究项目和论文成果可能没有及时更新，也不一定完整，只能作为方向匹配的参考，不能据此判断当前研究活跃度或招生状态。",
        "- 招募说明按核验日记录，不等于实时名额或接收承诺，申请前必须向教师或学院确认。",
        "- 联系方式只使用官网公开的 `cityu.edu.mo` / `cityu.mo` 工作邮箱，并同时提供官方主页；不收录私人邮箱、电话或办公室信息。",
        "- 导师职务、导师资格、研究方向和邮箱均按本次核验日期记录；没有日期的招生信息不能推断当前有名额或接收意愿。",
        "",
        "## 师资索引",
        "",
        "| 序号 | 教师 | 职称/职务 | 导师资格 | 校内工作邮箱 | 官网研究方向 | 标准化检索标签 | 官网科研证据覆盖 | 官网招募说明 | 近期外部证据摘要 | 方向依据 | 核验日期 | 官方主页 | 个人主页 |",
        "|---:|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for index, item in enumerate(faculty, 1):
        personal = f"[访问]({item.personal_url})" if item.personal_url else "官网未提供"
        email_link = (
            f"[{item.email}](mailto:{item.email})"
            if item.email
            else item.email_note or "官网未提供可验证邮箱"
        )
        recent = paper_summaries.get(index, "外部论文索引未覆盖；不能据此判断没有近期成果")
        lines.append(
            f"| {index} | {item.chinese_name}（{item.english_name}） | {item.role} | "
            f"{item.qualification} | {email_link} | {item.research_summary} | {'；'.join(item.tags)} | "
            f"{item.official_evidence_summary} | {item.recruitment_summary} | {recent} | "
            f"{item.evidence}（学院教师主页） | {verified} | "
            f"[官方页]({item.official_url}) | {personal} |"
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
    skill_dir = Path(__file__).resolve().parents[1]
    default_output = skill_dir / "references" / "mentors" / "fds_mentors.md"
    default_evidence_output = skill_dir / "references" / "mentors" / "fds_official_evidence.md"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=default_output)
    parser.add_argument("--evidence-output", type=Path, default=default_evidence_output)
    parser.add_argument("--papers", type=Path, default=skill_dir / "references" / "mentors" / "fds_papers.md")
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
    rendered = markdown(faculty, review, verified, publication_summaries(args.papers))
    evidence_rendered = official_evidence_markdown(faculty, verified)

    if args.check:
        expected = ((args.output, rendered), (args.evidence_output, evidence_rendered))
        for path, content in expected:
            if not path.exists():
                print(f"Missing generated reference: {path}", file=sys.stderr)
                return 1
            current = path.read_text(encoding="utf-8").replace("\r\n", "\n")
            if current != content:
                print(f"FDS faculty reference is stale: {path}", file=sys.stderr)
                return 1
        print(f"FDS faculty references are current: {len(faculty)} profiles; {len(review)} review notes")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=args.output.parent) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False, dir=args.evidence_output.parent) as handle:
        handle.write(evidence_rendered)
        evidence_temporary = Path(handle.name)
    temporary.replace(args.output)
    evidence_temporary.replace(args.evidence_output)
    print(f"Wrote {args.output} and {args.evidence_output}: {len(faculty)} profiles; {len(review)} review notes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
