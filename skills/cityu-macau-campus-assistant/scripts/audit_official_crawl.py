#!/usr/bin/env python3
"""Build an evidence inventory from a completed official-site crawl.

This script sends no network requests. It reads the persistent SQLite crawl
state and content-addressed response bodies produced by
``crawl_official_sites.py``. The JSON report is exhaustive; the Markdown report
is a concise review queue for maintainers.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import html
import io
import json
import os
import re
import shutil
import sqlite3
import struct
import subprocess
import tempfile
import urllib.parse
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

from crawl_official_sites import (
    FetchResult,
    advisory_lock_is_held,
    is_official_host,
    iter_http_urls,
    normalize_url,
    now_beijing,
    soft_404_reason,
)

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None  # type: ignore[assignment]

try:
    import olefile
except ImportError:
    olefile = None  # type: ignore[assignment]

try:
    import xlrd
except ImportError:
    xlrd = None  # type: ignore[assignment]


CATEGORY_KEYWORDS = {
    "admission": (
        "招生",
        "申请",
        "申請",
        "报名",
        "報名",
        "录取",
        "錄取",
        "admission",
        "application",
    ),
    "tuition_finance": (
        "学费",
        "學費",
        "费用",
        "費用",
        "缴费",
        "繳費",
        "奖学金",
        "獎學金",
        "tuition",
        "fee",
        "scholarship",
    ),
    "registration_calendar": (
        "注册",
        "註冊",
        "选科",
        "選科",
        "校历",
        "校曆",
        "行事历",
        "行事曆",
        "开学",
        "開學",
        "registration",
        "calendar",
    ),
    "visa_and_stay": (
        "签注",
        "簽注",
        "逗留",
        "居留",
        "visa",
        "stay permit",
    ),
    "housing": (
        "宿舍",
        "住宿",
        "dormitory",
        "accommodation",
        "housing",
    ),
    "academic_rules": (
        "课程",
        "課程",
        "学分",
        "學分",
        "毕业",
        "畢業",
        "论文",
        "論文",
        "培养",
        "培養",
        "转专业",
        "轉專業",
        "转入",
        "轉入",
        "programme",
        "program",
        "course",
        "credit",
        "graduat",
        "transfer",
    ),
    "faculty_and_mentors": (
        "师资",
        "師資",
        "教师",
        "教師",
        "导师",
        "導師",
        "faculty",
        "staff",
        "member",
        "supervisor",
    ),
    "campus_services": (
        "校园服务",
        "校園服務",
        "图书馆",
        "圖書館",
        "餐饮",
        "餐飲",
        "食堂",
        "校巴",
        "巴士",
        "library",
        "canteen",
        "shuttle",
    ),
    "exchange_and_career": (
        "交换",
        "交換",
        "暑期项目",
        "暑期項目",
        "实习计划",
        "實習計劃",
        "创业就业",
        "創業就業",
        "exchange",
        "summer programme",
        "summer program",
        "internship",
        "career",
    ),
    "weather": (
        "台风",
        "颱風",
        "暴雨",
        "恶劣天气",
        "惡劣天氣",
        "typhoon",
        "rainstorm",
    ),
}
# Maintenance scripts contain crawl seed URLs, not knowledge citations.  Linking
# them as Skill sources would turn intentionally probed host roots into false
# source failures, so only user-facing Skill/reference text participates here.
TEXT_FILE_SUFFIXES = {".md", ".yaml", ".yml"}
HTML_TYPES = {"application/xhtml+xml", "text/html"}
DOCUMENT_SUFFIXES = {
    ".doc",
    ".docx",
    ".odt",
    ".pdf",
    ".ppt",
    ".pptx",
    ".rtf",
    ".xls",
    ".xlsx",
}
RASTER_IMAGE_TYPES = {
    "image/bmp",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
}
RASTER_IMAGE_SUFFIXES = {
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}
TEXTUAL_MEDIA_TYPES = {
    "application/atom+xml",
    "application/json",
    "application/ld+json",
    "application/rss+xml",
    "application/xml",
    "text/csv",
    "text/plain",
    "text/xml",
}
SUSPICIOUS_CONTENT_MARKERS = (
    "gacor",
    "pulsa303",
    "virtus88",
    "kokototo",
    "pokerkoko",
    "slot deposit pulsa",
)


class PageTextExtractor(HTMLParser):
    """Extract titles, headings, canonical URLs, and visible page text."""

    HIDDEN_TAGS = {"script", "style", "noscript", "svg", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.title_chunks: list[str] = []
        self.heading_chunks: list[str] = []
        self.text_chunks: list[str] = []
        self.canonical_url: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self.stack.append(tag)
        values = {key.lower(): value for key, value in attrs if value}
        if tag == "link" and values.get("rel", "").lower() == "canonical":
            self.canonical_url = values.get("href")

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        values = {key.lower(): value for key, value in attrs if value}
        if tag.lower() == "link" and values.get("rel", "").lower() == "canonical":
            self.canonical_url = values.get("href")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag not in self.stack:
            return
        reverse_index = self.stack[::-1].index(tag)
        index = len(self.stack) - reverse_index - 1
        self.stack = self.stack[:index]

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if not value or any(tag in self.HIDDEN_TAGS for tag in self.stack):
            return
        if self.stack and self.stack[-1] == "title":
            self.title_chunks.append(value)
        if self.stack and self.stack[-1] in {"h1", "h2", "h3"}:
            self.heading_chunks.append(value)
        self.text_chunks.append(value)


def decode_body(body: bytes) -> str:
    """Decode common CityU page encodings while minimizing replacement text."""

    prefix = body[:8192]
    match = re.search(
        br"(?:charset\s*=\s*|encoding\s*=\s*[\"'])([-A-Za-z0-9_]+)",
        prefix,
        re.IGNORECASE,
    )
    candidates = ["utf-8-sig"]
    if match:
        candidates.insert(0, match.group(1).decode("ascii", errors="ignore"))
    candidates.extend(["big5", "gb18030"])

    decoded: list[tuple[int, str]] = []
    for encoding in dict.fromkeys(candidates):
        try:
            text = body.decode(encoding, errors="replace")
        except LookupError:
            continue
        decoded.append((text.count("\ufffd"), text))
    if not decoded:
        return body.decode("utf-8", errors="replace")
    return min(decoded, key=lambda item: item[0])[1]


def parse_html(body: bytes, base_url: str) -> dict[str, object]:
    parser = PageTextExtractor()
    text = decode_body(body)
    try:
        parser.feed(text)
    except Exception:
        pass
    title = " ".join(parser.title_chunks)
    headings = list(dict.fromkeys(parser.heading_chunks))
    visible_text = " ".join(parser.text_chunks)
    canonical = normalize_url(parser.canonical_url, base_url) if parser.canonical_url else None
    return {
        "title": title,
        "headings": headings,
        "canonical_url": canonical,
        "text": visible_text,
    }


def extract_pdf(body: bytes) -> dict[str, object]:
    if PdfReader is None:
        return {
            "kind": "pdf",
            "pages": None,
            "text": "",
            "text_source": None,
            "issue": "pypdf is not installed; PDF text was not extracted",
            "requires_visual_review": True,
        }
    try:
        reader = PdfReader(io.BytesIO(body), strict=False)
        if reader.is_encrypted:
            reader.decrypt("")
        page_text = [(page.extract_text() or "") for page in reader.pages]
        text = "\n\n".join(page_text)
        visible_characters = sum(not char.isspace() for char in text)
        page_visible_characters = [
            sum(not char.isspace() for char in value)
            for value in page_text
        ]
        low_text_pages = [
            index + 1
            for index, count in enumerate(page_visible_characters)
            if count < 20
        ]
        minimum_characters = max(100, len(reader.pages) * 40)
        issue = None
        if visible_characters < minimum_characters or low_text_pages:
            page_detail = (
                f"; low-text pages: {', '.join(str(value) for value in low_text_pages)}"
                if low_text_pages
                else ""
            )
            issue = (
                "too little extractable PDF text; OCR and visual review required "
                f"({visible_characters} characters across {len(reader.pages)} pages{page_detail})"
            )
        return {
            "kind": "pdf",
            "pages": len(reader.pages),
            "text": text,
            "text_source": "embedded_pdf_text",
            "issue": issue,
            "low_text_pages": low_text_pages,
            "requires_visual_review": True,
        }
    except Exception as error:
        return {
            "kind": "pdf",
            "pages": None,
            "text": "",
            "text_source": None,
            "issue": f"PDF extraction failed: {type(error).__name__}: {error}",
            "low_text_pages": None,
            "requires_visual_review": True,
        }


def extract_docx(body: bytes) -> dict[str, object]:
    try:
        chunks: list[str] = []
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            names = [
                name
                for name in archive.namelist()
                if re.fullmatch(
                    r"word/(?:document|footnotes|endnotes|comments|"
                    r"header\d+|footer\d+)\.xml",
                    name,
                )
            ]
            for name in sorted(names):
                xml = archive.read(name).decode("utf-8", errors="replace")
                for paragraph in re.split(r"</w:p\s*>", xml):
                    values = re.findall(r"<w:t\b[^>]*>(.*?)</w:t\s*>", paragraph, re.DOTALL)
                    if values:
                        chunks.append(
                            "".join(html.unescape(value) for value in values)
                        )
        text = "\n".join(chunks)
        issue = None if text.strip() else "DOCX contains no extractable text"
        return {
            "kind": "docx",
            "pages": None,
            "text": text,
            "text_source": "docx_xml",
            "issue": issue,
            "requires_visual_review": True,
        }
    except Exception as error:
        return {
            "kind": "docx",
            "pages": None,
            "text": "",
            "text_source": None,
            "issue": f"DOCX extraction failed: {type(error).__name__}: {error}",
            "requires_visual_review": True,
        }


def document_result(
    kind: str,
    text: str,
    source: str | None,
    issue: str | None = None,
) -> dict[str, object]:
    """Return the common result shape used by non-PDF document extractors."""

    if not text.strip() and issue is None:
        issue = f"{kind.upper()} contains no extractable text"
    return {
        "kind": kind,
        "pages": None,
        "text": text,
        "text_source": source,
        "issue": issue,
        "requires_visual_review": True,
    }


def find_antiword() -> Path | None:
    """Locate antiword without changing the user's shell environment."""

    executable = shutil.which("antiword")
    if executable:
        return Path(executable)
    if os.name == "nt":
        candidates = [
            Path(r"C:\Program Files\Git\mingw64\bin\antiword.exe"),
            Path(r"C:\Program Files (x86)\Git\mingw32\bin\antiword.exe"),
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
    return None


def extract_doc(body: bytes) -> dict[str, object]:
    """Extract legacy Word 97-2003 text through the local antiword binary."""

    executable = find_antiword()
    if executable is None:
        return document_result(
            "doc",
            "",
            None,
            "antiword is not installed; legacy DOC text was not extracted",
        )
    try:
        with tempfile.TemporaryDirectory(prefix="cityu-official-audit-doc-") as temp:
            document_path = Path(temp) / "document.doc"
            document_path.write_bytes(body)
            environment = os.environ.copy()
            antiword_home = executable.parent.parent / "share" / "antiword"
            if antiword_home.is_dir():
                environment["ANTIWORDHOME"] = str(antiword_home)
            completed = subprocess.run(
                [str(executable), "-m", "UTF-8.txt", str(document_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=60,
                env=environment,
            )
        text = completed.stdout.decode("utf-8", errors="replace")
        if completed.returncode != 0 and not text.strip():
            error = completed.stderr.decode("utf-8", errors="replace").strip()
            return document_result(
                "doc",
                "",
                None,
                f"antiword failed with exit {completed.returncode}: {error}",
            )
        return document_result("doc", text, "antiword")
    except Exception as error:
        return document_result(
            "doc",
            "",
            None,
            f"DOC extraction failed: {type(error).__name__}: {error}",
        )


def zip_xml_text(
    body: bytes,
    member_pattern: str,
    text_tag: str,
    kind: str,
    source: str,
) -> dict[str, object]:
    """Extract ordered text nodes from OOXML slide-like packages."""

    try:
        pattern = re.compile(member_pattern)
        chunks: list[str] = []
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            names = sorted(name for name in archive.namelist() if pattern.fullmatch(name))
            for name in names:
                root = ET.fromstring(archive.read(name))
                values = [
                    element.text or ""
                    for element in root.iter()
                    if element.tag.rsplit("}", 1)[-1] == text_tag
                ]
                if any(value.strip() for value in values):
                    chunks.append(" ".join(value for value in values if value.strip()))
        return document_result(kind, "\n".join(chunks), source)
    except Exception as error:
        return document_result(
            kind,
            "",
            None,
            f"{kind.upper()} extraction failed: {type(error).__name__}: {error}",
        )


def extract_pptx(body: bytes) -> dict[str, object]:
    return zip_xml_text(
        body,
        r"ppt/(?:slides/slide\d+|notesSlides/notesSlide\d+)\.xml",
        "t",
        "pptx",
        "pptx_xml",
    )


def extract_odt(body: bytes) -> dict[str, object]:
    try:
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            root = ET.fromstring(archive.read("content.xml"))
        chunks: list[str] = []
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] not in {"h", "p"}:
                continue
            value = "".join(element.itertext()).strip()
            if value:
                chunks.append(value)
        return document_result("odt", "\n".join(chunks), "odt_xml")
    except Exception as error:
        return document_result(
            "odt",
            "",
            None,
            f"ODT extraction failed: {type(error).__name__}: {error}",
        )


def extract_xlsx(body: bytes) -> dict[str, object]:
    """Extract XLSX cell values with the standard library only."""

    try:
        lines: list[str] = []
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            shared: list[str] = []
            if "xl/sharedStrings.xml" in archive.namelist():
                root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
                for item in root.iter():
                    if item.tag.rsplit("}", 1)[-1] != "si":
                        continue
                    shared.append(
                        "".join(
                            child.text or ""
                            for child in item.iter()
                            if child.tag.rsplit("}", 1)[-1] == "t"
                        )
                    )
            sheet_names = sorted(
                name
                for name in archive.namelist()
                if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name)
            )
            for sheet_name in sheet_names:
                root = ET.fromstring(archive.read(sheet_name))
                lines.append(f"[{Path(sheet_name).stem}]")
                for row in root.iter():
                    if row.tag.rsplit("}", 1)[-1] != "row":
                        continue
                    values: list[str] = []
                    for cell in row:
                        if cell.tag.rsplit("}", 1)[-1] != "c":
                            continue
                        cell_type = cell.attrib.get("t")
                        raw = ""
                        if cell_type == "inlineStr":
                            raw = "".join(
                                child.text or ""
                                for child in cell.iter()
                                if child.tag.rsplit("}", 1)[-1] == "t"
                            )
                        else:
                            value_element = next(
                                (
                                    child
                                    for child in cell
                                    if child.tag.rsplit("}", 1)[-1] == "v"
                                ),
                                None,
                            )
                            raw = value_element.text or "" if value_element is not None else ""
                            if cell_type == "s" and raw.isdigit():
                                index = int(raw)
                                raw = shared[index] if index < len(shared) else raw
                        values.append(raw)
                    if any(value.strip() for value in values):
                        lines.append("\t".join(values))
        return document_result("xlsx", "\n".join(lines), "xlsx_xml")
    except Exception as error:
        return document_result(
            "xlsx",
            "",
            None,
            f"XLSX extraction failed: {type(error).__name__}: {error}",
        )


def extract_xls(body: bytes) -> dict[str, object]:
    if xlrd is None:
        return document_result(
            "xls",
            "",
            None,
            "xlrd is not installed; legacy XLS text was not extracted",
        )
    try:
        workbook = xlrd.open_workbook(file_contents=body, on_demand=True)
        lines: list[str] = []
        for sheet in workbook.sheets():
            lines.append(f"[{sheet.name}]")
            for row_index in range(sheet.nrows):
                values = [str(value) for value in sheet.row_values(row_index)]
                if any(value.strip() for value in values):
                    lines.append("\t".join(values))
        workbook.release_resources()
        return document_result("xls", "\n".join(lines), "xlrd")
    except Exception as error:
        return document_result(
            "xls",
            "",
            None,
            f"XLS extraction failed: {type(error).__name__}: {error}",
        )


def extract_ppt(body: bytes) -> dict[str, object]:
    """Extract text atoms from legacy binary PowerPoint files."""

    if olefile is None:
        return document_result(
            "ppt",
            "",
            None,
            "olefile is not installed; legacy PPT text was not extracted",
        )
    try:
        with olefile.OleFileIO(io.BytesIO(body)) as document:
            stream = document.openstream("PowerPoint Document").read()
        chunks: list[str] = []

        def collect_records(data: bytes, depth: int = 0) -> None:
            if depth > 20:
                return
            position = 0
            while position + 8 <= len(data):
                version_instance, record_type, record_length = struct.unpack_from(
                    "<HHI", data, position
                )
                start = position + 8
                end = start + record_length
                if end > len(data):
                    break
                payload = data[start:end]
                record_version = version_instance & 0x000F
                if record_type == 4000:
                    value = payload.decode("utf-16le", errors="replace").strip("\x00")
                    if value.strip():
                        chunks.append(value)
                elif record_type == 4008:
                    value = decode_body(payload).strip("\x00")
                    if value.strip():
                        chunks.append(value)
                elif record_version == 0x000F:
                    collect_records(payload, depth + 1)
                position = end

        collect_records(stream)
        text = "\n".join(dict.fromkeys(chunk for chunk in chunks if chunk.strip()))
        return document_result("ppt", text, "ppt_binary_text_atoms")
    except Exception as error:
        return document_result(
            "ppt",
            "",
            None,
            f"PPT extraction failed: {type(error).__name__}: {error}",
        )


def extract_rtf(body: bytes) -> dict[str, object]:
    """Extract common RTF plain text, including Unicode and hex escapes."""

    try:
        text = body.decode("latin-1", errors="replace")

        def unicode_character(match: re.Match[str]) -> str:
            value = int(match.group(1))
            if value < 0:
                value += 65536
            return chr(value)

        text = re.sub(r"\\u(-?\d+)\??", unicode_character, text)
        text = re.sub(
            r"\\'([0-9a-fA-F]{2})",
            lambda match: bytes([int(match.group(1), 16)]).decode(
                "cp1252", errors="replace"
            ),
            text,
        )
        text = re.sub(r"\\(?:par|line)\b", "\n", text)
        text = re.sub(r"\\tab\b", "\t", text)
        text = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", text)
        text = re.sub(r"[{}]", "", text)
        return document_result("rtf", html.unescape(text), "rtf_controls")
    except Exception as error:
        return document_result(
            "rtf",
            "",
            None,
            f"RTF extraction failed: {type(error).__name__}: {error}",
        )


def detect_ooxml_kind(body: bytes) -> str | None:
    """Detect OOXML packages whose public URL still uses a legacy extension."""

    if not body.startswith(b"PK"):
        return None
    try:
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            names = set(archive.namelist())
        if "word/document.xml" in names:
            return "docx"
        if "xl/workbook.xml" in names:
            return "xlsx"
        if "ppt/presentation.xml" in names:
            return "pptx"
    except (OSError, zipfile.BadZipFile):
        return None
    return None


def extract_document(
    body: bytes,
    url: str,
    content_type: str,
    ocr_text: str | None = None,
) -> dict[str, object]:
    suffix = Path(urllib.parse.urlsplit(url).path).suffix.lower()
    media_type = content_type.partition(";")[0].strip().lower()
    ooxml_kind = detect_ooxml_kind(body)
    result: dict[str, object]
    if media_type == "application/pdf" or body.startswith(b"%PDF"):
        result = extract_pdf(body)
    elif media_type in HTML_TYPES or b"<html" in body[:2048].lower():
        return {
            "kind": None,
            "pages": None,
            "text": "",
            "text_source": None,
            "issue": None,
            "requires_visual_review": False,
        }
    elif media_type in TEXTUAL_MEDIA_TYPES or media_type.startswith("text/"):
        return {
            "kind": "text",
            "pages": None,
            "text": decode_body(body),
            "text_source": "plain_text",
            "issue": None,
            "requires_visual_review": False,
        }
    elif ooxml_kind == "docx" or suffix == ".docx" or content_type == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        result = extract_docx(body)
    elif suffix == ".doc":
        result = extract_doc(body)
    elif ooxml_kind == "pptx" or suffix == ".pptx":
        result = extract_pptx(body)
    elif suffix == ".ppt":
        result = extract_ppt(body)
    elif ooxml_kind == "xlsx" or suffix == ".xlsx":
        result = extract_xlsx(body)
    elif suffix == ".xls":
        result = extract_xls(body)
    elif suffix == ".odt":
        result = extract_odt(body)
    elif suffix == ".rtf":
        result = extract_rtf(body)
    elif is_raster_image(url, content_type) and ocr_text and ocr_text.strip():
        result = document_result("image", ocr_text, "image_ocr")
    elif suffix in DOCUMENT_SUFFIXES:
        result = {
            "kind": suffix.lstrip("."),
            "pages": None,
            "text": "",
            "text_source": None,
            "issue": f"{suffix or 'document'} extraction is not implemented",
            "requires_visual_review": True,
        }
    else:
        return {
            "kind": None,
            "pages": None,
            "text": "",
            "text_source": None,
            "issue": None,
            "requires_visual_review": False,
        }
    if result["issue"] and ocr_text and ocr_text.strip():
        result["text"] = ocr_text
        result["text_source"] = "supplemental_text_cache"
        result["issue"] = None
    return result


def is_raster_image(url: str, content_type: str) -> bool:
    suffix = Path(urllib.parse.unquote(urllib.parse.urlsplit(url).path)).suffix.lower()
    media_type = content_type.partition(";")[0].strip().lower()
    if media_type:
        if media_type.startswith("image/"):
            return media_type in RASTER_IMAGE_TYPES
        if media_type not in {"application/octet-stream", "binary/octet-stream"}:
            return False
    return suffix in RASTER_IMAGE_SUFFIXES


def safe_cached_body_path(state_dir: Path, body_path: object) -> Path | None:
    """Resolve a cached body only when it remains inside ``state_dir``."""

    if not body_path:
        return None
    relative = Path(str(body_path))
    if relative.is_absolute():
        return None
    root = state_dir.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def read_verified_cached_body(
    state_dir: Path,
    *,
    body_path: object,
    sha256: object,
    body_bytes: object,
    label: str,
    require_hash: bool,
) -> tuple[bytes | None, str | None]:
    """Read a content-addressed body and return a hard integrity error, if any."""

    expected_bytes: int | None
    try:
        expected_bytes = int(body_bytes) if body_bytes is not None else None
    except (TypeError, ValueError):
        return None, f"{label} has an invalid recorded body length"
    expected_hash = str(sha256 or "").lower()
    if not body_path:
        if expected_bytes in (None, 0) and not expected_hash:
            return b"", None
        return None, f"{label} is missing its content-addressed body path"
    cached_path = safe_cached_body_path(state_dir, body_path)
    if cached_path is None:
        return None, f"{label} body path escapes the crawl state directory"
    if not cached_path.is_file():
        return None, f"{label} body is missing from the content-addressed cache"
    try:
        body = cached_path.read_bytes()
    except OSError as error:
        return None, f"{label} body cannot be read: {type(error).__name__}: {error}"
    if expected_bytes is not None and len(body) != expected_bytes:
        return body, (
            f"{label} body length mismatch: recorded {expected_bytes}, "
            f"actual {len(body)}"
        )
    if not expected_hash:
        if require_hash:
            return body, f"{label} is missing its recorded SHA-256"
        return body, None
    if not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        return body, f"{label} has an invalid recorded SHA-256"
    actual_hash = hashlib.sha256(body).hexdigest()
    if actual_hash != expected_hash:
        return body, (
            f"{label} SHA-256 mismatch: recorded {expected_hash}, "
            f"actual {actual_hash}"
        )
    return body, None


def skill_url_sources(skill_root: Path) -> dict[str, list[str]]:
    sources: dict[str, set[str]] = collections.defaultdict(set)
    for path in sorted(skill_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_FILE_SUFFIXES:
            continue
        if any(part in {".cache", "__pycache__"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for candidate in iter_http_urls(text):
            normalized = normalize_url(candidate)
            if not normalized:
                continue
            host = urllib.parse.urlsplit(normalized).hostname or ""
            if is_official_host(host):
                sources[normalized].add(path.relative_to(skill_root).as_posix())
    return {url: sorted(paths) for url, paths in sorted(sources.items())}


def categories_for(value: str) -> list[str]:
    value = value.lower()
    return [
        category
        for category, keywords in CATEGORY_KEYWORDS.items()
        if any(keyword.lower() in value for keyword in keywords)
    ]


def content_integrity_issue(body: bytes | None) -> str | None:
    """Flag repeated, high-confidence indicators of injected SEO/spam content."""

    if not body:
        return None
    text = decode_body(body).lower()
    found = [marker for marker in SUSPICIOUS_CONTENT_MARKERS if marker in text]
    if len(found) < 2:
        return None
    return "suspected injected gambling/SEO spam: " + ", ".join(found)


def deduplicate_candidate_pages(
    candidates: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Collapse exact-body candidate aliases while preserving their URLs.

    The full page inventory and duplicate-content section remain lossless.  This
    helper only reduces the human review queue so the same response body reached
    through trailing-slash, language, or redirect aliases is not presented as
    several independent omissions.
    """

    groups: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    for page in candidates:
        key = str(page["sha256"] or page["url"])
        groups[key].append(page)

    deduplicated: list[dict[str, object]] = []
    for group in groups.values():
        def preference(page: dict[str, object]) -> tuple[bool, bool, int, str]:
            url = str(page["url"])
            parsed = urllib.parse.urlsplit(url)
            path = parsed.path.lower().rstrip("/")
            english_alias = path == "/en" or path.startswith("/en/")
            return english_alias, bool(parsed.query), len(url), url

        representative = min(group, key=preference)
        item = dict(representative)
        item["duplicate_urls"] = sorted(
            str(page["url"])
            for page in group
            if page is not representative
        )
        deduplicated.append(item)
    return sorted(
        deduplicated,
        key=lambda page: (str(page["host"]), str(page["url"])),
    )


def markdown_cell(value: object, limit: int = 160) -> str:
    text = " ".join(str(value or "").split()).replace("|", r"\|")
    if len(text) > limit:
        return f"{text[: limit - 1]}…"
    return text


def build_report(
    database_path: Path,
    state_dir: Path,
    skill_root: Path,
    ocr_dir: Path,
) -> dict[str, object]:
    known_sources = skill_url_sources(skill_root)
    ocr_text_by_sha: dict[str, str] = {}
    ocr_manifest_by_sha: dict[str, dict[str, object]] = {}
    manifest_path = ocr_dir / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            manifest = []
        for item in manifest if isinstance(manifest, list) else []:
            if not isinstance(item, dict):
                continue
            digest = str(item.get("sha256") or "")
            if digest:
                ocr_manifest_by_sha[digest] = item
            normalized = ocr_dir / digest / "combined.normalized.txt"
            raw = ocr_dir / digest / "combined.txt"
            source = normalized if normalized.is_file() else raw
            if digest and item.get("status") == "success" and source.is_file():
                ocr_text_by_sha[digest] = source.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
    connection = sqlite3.connect(
        f"{database_path.resolve().as_uri()}?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    connection.execute("BEGIN")
    pages: list[dict[str, object]] = []
    document_cache: dict[
        tuple[str, str, str], dict[str, object]
    ] = {}
    try:
        for row in connection.execute("SELECT * FROM urls ORDER BY url"):
            item = dict(row)
            body_path = item.get("body_path")
            body, body_integrity_error = read_verified_cached_body(
                state_dir,
                body_path=body_path,
                sha256=item.get("sha256"),
                body_bytes=item.get("body_bytes"),
                label=f"URL {item['url']}",
                require_hash=(
                    item["state"] == "fetched"
                    and (bool(body_path) or int(item.get("body_bytes") or 0) > 0)
                ),
            )
            trusted_body = body if body_integrity_error is None else None

            parsed: dict[str, object] = {
                "title": "",
                "headings": [],
                "canonical_url": None,
                "text": "",
            }
            content_type = str(item.get("content_type") or "")
            if trusted_body and (
                content_type in HTML_TYPES
                or b"<html" in trusted_body[:2048].lower()
            ):
                parsed = parse_html(trusted_body, str(item["final_url"] or item["url"]))
            digest = str(item.get("sha256") or "")
            document_url = str(item["final_url"] or item["url"])
            document_cache_key = (
                digest,
                content_type.partition(";")[0].strip().lower(),
                Path(urllib.parse.urlsplit(document_url).path).suffix.lower(),
            )
            if trusted_body is not None:
                document = (
                    document_cache.get(document_cache_key) if digest else None
                )
                if document is None:
                    document = extract_document(
                        trusted_body,
                        document_url,
                        content_type,
                        ocr_text_by_sha.get(digest),
                    )
                    if digest:
                        document_cache[document_cache_key] = document
            else:
                document = {
                    "kind": None,
                    "pages": None,
                    "text": "",
                    "text_source": None,
                    "issue": None,
                    "low_text_pages": None,
                    "requires_visual_review": False,
                }

            result = None
            if trusted_body and item.get("http_status"):
                result = FetchResult(
                    requested_url=str(item["url"]),
                    final_url=str(item["final_url"] or item["url"]),
                    status=int(item["http_status"]),
                    content_type=content_type,
                    body=trusted_body,
                    headers={},
            )
            soft_error = soft_404_reason(result) if result else None
            integrity_error = content_integrity_issue(trusted_body)
            title = str(parsed["title"])
            title_focus = re.split(r"\s+-\s+澳門城市大學", title, maxsplit=1)[0]
            focus_text = " ".join(
                [
                    urllib.parse.unquote(str(item["url"])),
                    title_focus,
                    " ".join(str(value) for value in parsed["headings"]),
                    str(document["text"])[:20_000],
                ]
            )
            evidence_text = " ".join(
                [
                    focus_text,
                    str(parsed["text"])[:20_000],
                    str(document["text"])[:100_000],
                ]
            )
            item_url = str(item["url"])
            references = set(known_sources.get(item_url, []))
            canonical_item_url = normalize_url(item_url)
            if canonical_item_url:
                references.update(known_sources.get(canonical_item_url, []))
            sorted_references = sorted(references)
            pages.append(
                {
                    "url": item["url"],
                    "host": item["host"],
                    "state": item["state"],
                    "attempts": item["attempts"],
                    "http_status": item["http_status"],
                    "content_type": content_type,
                    "is_html": bool(
                        trusted_body
                        and (
                            content_type in HTML_TYPES
                            or b"<html" in trusted_body[:2048].lower()
                        )
                    ),
                    "final_url": item["final_url"],
                    "sha256": item["sha256"],
                    "body_path": item["body_path"],
                    "body_bytes": item["body_bytes"],
                    "error": item["error"],
                    "body_integrity_issue": body_integrity_error,
                    "title": title,
                    "headings": parsed["headings"],
                    "canonical_url": parsed["canonical_url"],
                    "soft_404_reason": soft_error,
                    "content_integrity_issue": integrity_error,
                    "categories": categories_for(focus_text),
                    "content_categories": categories_for(evidence_text),
                    "candidate_categories": list(
                        dict.fromkeys(
                            categories_for(focus_text)
                            + categories_for(evidence_text)
                        )
                    ),
                    "document_kind": document["kind"],
                    "document_pages": document["pages"],
                    "document_low_text_pages": document.get("low_text_pages"),
                    "document_text_chars": len(str(document["text"])),
                    "document_text": document["text"],
                    "document_text_source": document["text_source"],
                    "document_issue": document["issue"],
                    "requires_visual_review": document["requires_visual_review"],
                    "referenced_by": sorted_references,
                    "is_skill_source": bool(sorted_references),
                    "discovered_from": item["discovered_from"],
                    "discovery_context": item["discovery_context"],
                }
            )

        hosts = [
            dict(row)
            for row in connection.execute(
                """
                SELECT h.*,
                       SUM(CASE WHEN u.state='fetched' THEN 1 ELSE 0 END) AS fetched,
                       SUM(CASE WHEN u.state='pending' THEN 1 ELSE 0 END) AS pending,
                       SUM(CASE WHEN u.state='failed' THEN 1 ELSE 0 END) AS failed,
                       SUM(CASE WHEN u.state='deferred' THEN 1 ELSE 0 END) AS deferred,
                       SUM(CASE WHEN u.state='robots_denied' THEN 1 ELSE 0 END)
                           AS robots_denied,
                       SUM(CASE WHEN u.state='soft_404' THEN 1 ELSE 0 END)
                           AS soft_404,
                       SUM(CASE WHEN u.state='skipped' THEN 1 ELSE 0 END) AS skipped
                FROM hosts h
                LEFT JOIN urls u ON u.host=h.host
                GROUP BY h.host
                ORDER BY h.host
                """
            )
        ]
        robots_integrity_issues: list[dict[str, object]] = []
        for host in hosts:
            if host.get("robots_state") != "fetched":
                continue
            robots_path = host.get("robots_body_path")
            fallback_hash = (
                Path(str(robots_path)).stem if robots_path else None
            )
            _robots_body, robots_error = read_verified_cached_body(
                state_dir,
                body_path=robots_path,
                sha256=host.get("robots_sha256") or fallback_hash,
                body_bytes=host.get("robots_body_bytes"),
                label=f"robots.txt for {host['host']}",
                require_hash=True,
            )
            if robots_error:
                robots_integrity_issues.append(
                    {
                        "host": host["host"],
                        "robots_url": host.get("robots_url"),
                        "robots_body_path": robots_path,
                        "robots_integrity_issue": robots_error,
                    }
                )
        link_count = int(connection.execute("SELECT COUNT(*) FROM links").fetchone()[0])
    finally:
        connection.close()

    by_url = {str(page["url"]): page for page in pages}
    resolved_skill_source_aliases: list[dict[str, object]] = []
    resolved_alias_urls: set[str] = set()
    resolved_alias_target_hashes: set[str] = set()
    for page in pages:
        if not page["is_skill_source"] or page["state"] != "skipped":
            continue
        error = str(page["error"] or "")
        prefix = "canonicalized to "
        if not error.startswith(prefix):
            continue
        target_url = error[len(prefix) :].strip()
        target = by_url.get(target_url)
        if (
            not target
            or target["state"] != "fetched"
            or target["body_integrity_issue"]
            or target["soft_404_reason"]
            or target["content_integrity_issue"]
        ):
            continue
        alias_url = str(page["url"])
        resolved_alias_urls.add(alias_url)
        if target["sha256"]:
            resolved_alias_target_hashes.add(str(target["sha256"]))
        resolved_skill_source_aliases.append(
            {
                "url": alias_url,
                "canonical_url": target_url,
                "referenced_by": page["referenced_by"],
            }
        )
    missing_skill_sources = [
        {"url": url, "referenced_by": referenced_by}
        for url, referenced_by in known_sources.items()
        if url not in by_url
    ]
    unresolved_states = {
        "deferred",
        "failed",
        "fetching",
        "pending",
        "robots_denied",
        "soft_404",
    }
    unresolved = [
        page
        for page in pages
        if (
            page["state"] in unresolved_states
            or page["body_integrity_issue"]
            or page["soft_404_reason"]
        )
    ]
    skill_source_issues = [
        page
        for page in pages
        if page["is_skill_source"]
        and str(page["url"]) not in resolved_alias_urls
        and (
            page["state"] != "fetched"
            or page["body_integrity_issue"]
            or page["soft_404_reason"]
            or page["content_integrity_issue"]
        )
    ]
    content_integrity_issues = [
        page
        for page in pages
        if page["state"] == "fetched" and page["content_integrity_issue"]
    ]
    body_integrity_issues = [
        page
        for page in pages
        if page["state"] == "fetched" and page["body_integrity_issue"]
    ]
    covered_source_hashes = {
        page["sha256"]
        for page in pages
        if page["state"] == "fetched"
        and page["is_skill_source"]
        and page["sha256"]
        and not page["body_integrity_issue"]
        and not page["soft_404_reason"]
        and not page["content_integrity_issue"]
    }
    covered_source_hashes.update(resolved_alias_target_hashes)
    raw_discovered_candidates = [
        page
        for page in pages
        if page["state"] == "fetched"
        and not page["is_skill_source"]
        and not page["body_integrity_issue"]
        and not page["soft_404_reason"]
        and not page["content_integrity_issue"]
        and page["sha256"] not in covered_source_hashes
        and page["candidate_categories"]
        and (
            page["content_type"] in HTML_TYPES
            or page["document_kind"] is not None
        )
        and not urllib.parse.urlsplit(str(page["url"])).path.lower().endswith(
            "/sitemap.xml"
        )
    ]
    discovered_candidates = deduplicate_candidate_pages(raw_discovered_candidates)
    document_issues = [
        page
        for page in pages
        if page["state"] == "fetched" and page["document_issue"]
    ]
    unparsed_asset_issues = [
        page
        for page in pages
        if page["state"] == "fetched"
        and not page["body_integrity_issue"]
        and int(page["body_bytes"] or 0) > 0
        and not page["is_html"]
        and page["document_kind"] is None
        and not is_raster_image(str(page["url"]), str(page["content_type"]))
    ]
    visual_review_advisories = [
        page
        for page in pages
        if page["state"] == "fetched"
        and page["requires_visual_review"]
        and not page["body_integrity_issue"]
    ]
    image_groups: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    for page in pages:
        if (
            page["state"] == "fetched"
            and page["sha256"]
            and is_raster_image(str(page["url"]), str(page["content_type"]))
        ):
            image_groups[str(page["sha256"])].append(page)
    image_ocr_counts: collections.Counter[str] = collections.Counter()
    image_ocr_issues: list[dict[str, object]] = []
    image_ocr_warnings: list[dict[str, object]] = []
    accepted_image_statuses = {"success", "no_text", "excluded_small"}
    for digest, group in sorted(image_groups.items()):
        entry = ocr_manifest_by_sha.get(digest, {})
        status = (
            str(entry.get("status") or "unprocessed")
            if entry.get("kind") == "image"
            else "unprocessed"
        )
        image_ocr_counts[status] += 1
        if status not in accepted_image_statuses:
            issue = dict(group[0])
            issue["image_ocr_status"] = status
            issue["image_ocr_error"] = entry.get("error") or "no image OCR record"
            issue["duplicate_urls"] = [str(page["url"]) for page in group[1:]]
            image_ocr_issues.append(issue)
        decode_warnings = entry.get("decode_warnings")
        if isinstance(decode_warnings, list) and decode_warnings:
            warning = dict(group[0])
            warning["image_ocr_status"] = status
            warning["image_ocr_provider"] = entry.get("inference_provider")
            warning["image_ocr_warning"] = "; ".join(
                str(value) for value in decode_warnings
            )
            warning["duplicate_urls"] = [
                str(page["url"]) for page in group[1:]
            ]
            image_ocr_warnings.append(warning)
    content_groups: dict[str, list[str]] = collections.defaultdict(list)
    for page in pages:
        if page["state"] == "fetched" and page["sha256"]:
            content_groups[str(page["sha256"])].append(str(page["url"]))
    duplicate_content = [
        {"sha256": digest, "urls": urls}
        for digest, urls in sorted(content_groups.items())
        if len(urls) > 1
    ]
    counts = dict(collections.Counter(str(page["state"]) for page in pages))
    complete = (
        not unresolved
        and not missing_skill_sources
        and not document_issues
        and not image_ocr_issues
        and not content_integrity_issues
        and not body_integrity_issues
        and not robots_integrity_issues
        and not unparsed_asset_issues
    )
    return {
        "generated_at": now_beijing(),
        "database": str(database_path),
        "state_dir": str(state_dir),
        "skill_root": str(skill_root),
        "ocr_dir": str(ocr_dir),
        "complete": complete,
        "counts": counts,
        "known_skill_source_count": len(known_sources),
        "page_count": len(pages),
        "link_count": link_count,
        "host_count": len(hosts),
        "hosts": hosts,
        "missing_skill_sources": missing_skill_sources,
        "resolved_skill_source_aliases": resolved_skill_source_aliases,
        "skill_source_issues": skill_source_issues,
        "content_integrity_issues": content_integrity_issues,
        "body_integrity_issues": body_integrity_issues,
        "robots_integrity_issues": robots_integrity_issues,
        "document_issues": document_issues,
        "unparsed_asset_issues": unparsed_asset_issues,
        "visual_review_advisories": visual_review_advisories,
        "image_ocr_counts": dict(image_ocr_counts),
        "image_ocr_issues": image_ocr_issues,
        "image_ocr_warnings": image_ocr_warnings,
        "unresolved": unresolved,
        "discovered_relevant_candidate_url_count": len(raw_discovered_candidates),
        "discovered_relevant_candidates": discovered_candidates,
        "duplicate_content": duplicate_content,
        "pages": pages,
    }


def markdown_report(report: dict[str, object]) -> str:
    counts = report["counts"]
    hosts = report["hosts"]
    issues = report["skill_source_issues"]
    missing = report["missing_skill_sources"]
    resolved_aliases = report["resolved_skill_source_aliases"]
    candidates = report["discovered_relevant_candidates"]
    unresolved = report["unresolved"]
    document_issues = report["document_issues"]
    image_ocr_issues = report["image_ocr_issues"]
    image_ocr_warnings = report["image_ocr_warnings"]
    integrity_issues = report["content_integrity_issues"]
    body_integrity_issues = report["body_integrity_issues"]
    robots_integrity_issues = report["robots_integrity_issues"]
    unparsed_asset_issues = report["unparsed_asset_issues"]
    visual_review_advisories = report["visual_review_advisories"]
    lines = [
        "# 澳门城市大学官网抓取审计",
        "",
        f"> 生成时间（北京时间）：{report['generated_at']}",
        "",
        "## 结论",
        "",
        f"- 完整性验证：{'通过' if report['complete'] else '未通过'}",
        f"- 官方主机：{report['host_count']}",
        f"- URL：{report['page_count']}；链接关系：{report['link_count']}",
        f"- Skill 已引用的去重官方来源：{report['known_skill_source_count']}",
        f"- 状态计数：`{json.dumps(counts, ensure_ascii=False, sort_keys=True)}`",
        f"- 未解决 URL：{len(unresolved)}",
        f"- Skill 来源问题：{len(issues) + len(missing)}",
        f"- 已由成功规范化目标覆盖的 Skill 来源别名：{len(resolved_aliases)}",
        f"- 内容完整性问题：{len(integrity_issues)}",
        f"- 正文哈希/长度完整性问题：{len(body_integrity_issues)}",
        f"- robots.txt 缓存完整性问题：{len(robots_integrity_issues)}",
        f"- 附件正文提取问题：{len(document_issues)}",
        f"- 未支持或未解析资产：{len(unparsed_asset_issues)}",
        f"- 需视觉复核的已提取附件（提示，不等同于传输失败）：{len(visual_review_advisories)}",
        (
            "- 去重图片 OCR 状态："
            f"`{json.dumps(report['image_ocr_counts'], ensure_ascii=False, sort_keys=True)}`；"
            f"未解决：{len(image_ocr_issues)}；解码警告：{len(image_ocr_warnings)}"
        ),
        (
            "- 新发现且与 Skill 范围相关的候选正文："
            f"{len(candidates)}（原始 URL "
            f"{report['discovered_relevant_candidate_url_count']}）"
        ),
        "",
        "完整 JSON 清单包含每个 URL、抓取状态、内容哈希、正文路径、标题、",
        "栏目、来源文件、发现入口和相关主题。本报告的“完整性验证”只表示",
        "可访问范围内的传输与自动提取完整性，不等同于每一页已经人工事实审读。",
        "它不把 HTTP 200 的软 404、疑似注入的 SEO/博彩垃圾、缺失或损坏正文、",
        "未支持资产、robots.txt 禁止或网络失败解释为成功覆盖。",
        "",
        "## 主机覆盖",
        "",
        "| 主机 | robots | 成功 | 待处理 | 失败 | 暂缓 | 禁止 | 软 404 | 跳过/规范化 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for host in hosts:
        lines.append(
            "| {host} | {robots_state} | {fetched} | {pending} | {failed} | "
            "{deferred} | {robots_denied} | {soft_404} | {skipped} |".format(
                **{key: host.get(key) or 0 for key in host}
            )
        )

    lines.extend(
        [
            "",
            "## Skill 已引用来源的问题",
            "",
            "| 状态 | HTTP | URL | 引用文件 | 错误 |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for page in issues:
        lines.append(
            f"| {markdown_cell(page['state'])} | "
            f"{markdown_cell(page['http_status'])} | "
            f"{markdown_cell(page['url'], 240)} | "
            f"{markdown_cell(', '.join(page['referenced_by']), 220)} | "
            f"{markdown_cell(page['body_integrity_issue'] or page['content_integrity_issue'] or page['soft_404_reason'] or page['error'])} |"
        )
    for item in missing:
        lines.append(
            f"| 未入队 |  | {markdown_cell(item['url'], 240)} | "
            f"{markdown_cell(', '.join(item['referenced_by']), 220)} | "
            "Skill URL 未进入抓取清单 |"
        )
    if not issues and not missing:
        lines.append("| 无 |  |  |  |  |")

    lines.extend(
        [
            "",
            "## 新发现的范围内候选页",
            "",
            "| 主题 | 标题 | URL | 发现自 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for page in candidates:
        lines.append(
            f"| {markdown_cell(', '.join(page['candidate_categories']))} | "
            f"{markdown_cell(page['title'] or ' / '.join(page['headings']))} | "
            f"{markdown_cell(page['url'], 240)} | "
            f"{markdown_cell(page['discovered_from'], 200)} |"
        )
    if not candidates:
        lines.append("| 无 |  |  |  |")

    lines.extend(
        [
            "",
            "## 内容完整性问题",
            "",
            "| 主机 | URL | 问题 |",
            "| --- | --- | --- |",
        ]
    )
    for page in integrity_issues:
        lines.append(
            f"| {markdown_cell(page['host'])} | "
            f"{markdown_cell(page['url'], 240)} | "
            f"{markdown_cell(page['content_integrity_issue'])} |"
        )
    if not integrity_issues:
        lines.append("| 无 |  |  |")

    lines.extend(
        [
            "",
            "## 正文缓存完整性问题",
            "",
            "| 主机 | URL | 问题 |",
            "| --- | --- | --- |",
        ]
    )
    for page in body_integrity_issues:
        lines.append(
            f"| {markdown_cell(page['host'])} | "
            f"{markdown_cell(page['url'], 240)} | "
            f"{markdown_cell(page['body_integrity_issue'])} |"
        )
    if not body_integrity_issues:
        lines.append("| 无 |  |  |")

    lines.extend(
        [
            "",
            "## robots.txt 缓存完整性问题",
            "",
            "| 主机 | robots URL | 问题 |",
            "| --- | --- | --- |",
        ]
    )
    for item in robots_integrity_issues:
        lines.append(
            f"| {markdown_cell(item['host'])} | "
            f"{markdown_cell(item['robots_url'], 240)} | "
            f"{markdown_cell(item['robots_integrity_issue'])} |"
        )
    if not robots_integrity_issues:
        lines.append("| 无 |  |  |")

    lines.extend(
        [
            "",
            "## 附件正文提取问题",
            "",
            "| 类型 | 页数 | URL | 问题 |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for page in document_issues:
        lines.append(
            f"| {markdown_cell(page['document_kind'])} | "
            f"{markdown_cell(page['document_pages'])} | "
            f"{markdown_cell(page['url'], 240)} | "
            f"{markdown_cell(page['document_issue'])} |"
        )
    if not document_issues:
        lines.append("| 无 |  |  |  |")

    lines.extend(
        [
            "",
            "## 未支持或未解析资产",
            "",
            "| 媒体类型 | URL | 说明 |",
            "| --- | --- | --- |",
        ]
    )
    for page in unparsed_asset_issues:
        lines.append(
            f"| {markdown_cell(page['content_type'])} | "
            f"{markdown_cell(page['url'], 240)} | "
            "该资产未被 HTML、文本、附件或栅格图片管线解析 |"
        )
    if not unparsed_asset_issues:
        lines.append("| 无 |  |  |")

    lines.extend(
        [
            "",
            "## 图片 OCR 覆盖问题",
            "",
            "| 状态 | URL | 问题 |",
            "| --- | --- | --- |",
        ]
    )
    for page in image_ocr_issues:
        lines.append(
            f"| {markdown_cell(page['image_ocr_status'])} | "
            f"{markdown_cell(page['url'], 240)} | "
            f"{markdown_cell(page['image_ocr_error'])} |"
        )
    if not image_ocr_issues:
        lines.append("| 无 |  |  |")

    lines.extend(
        [
            "",
            "## 图片 OCR 解码警告",
            "",
            "| 状态 | 推理来源 | URL | 警告 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for page in image_ocr_warnings:
        lines.append(
            f"| {markdown_cell(page['image_ocr_status'])} | "
            f"{markdown_cell(page['image_ocr_provider'])} | "
            f"{markdown_cell(page['url'], 240)} | "
            f"{markdown_cell(page['image_ocr_warning'])} |"
        )
    if not image_ocr_warnings:
        lines.append("| 无 |  |  |  |")

    lines.extend(
        [
            "",
            "## 未解决 URL",
            "",
            "| 状态 | HTTP | URL | 错误 |",
            "| --- | ---: | --- | --- |",
        ]
    )
    for page in unresolved:
        lines.append(
            f"| {markdown_cell(page['state'])} | "
            f"{markdown_cell(page['http_status'])} | "
            f"{markdown_cell(page['url'], 240)} | "
            f"{markdown_cell(page['soft_404_reason'] or page['error'])} |"
        )
    if not unresolved:
        lines.append("| 无 |  |  |  |")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    script_path = Path(__file__).resolve()
    skill_root = script_path.parent.parent
    repository_root = skill_root.parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=repository_root / ".cache" / "cityu-official-crawl",
    )
    parser.add_argument("--skill-root", type=Path, default=skill_root)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=repository_root / ".cache" / "cityu-official-audit",
    )
    parser.add_argument(
        "--ocr-dir",
        type=Path,
        default=None,
        help="OCR cache; defaults to STATE_DIR/ocr",
    )
    parser.add_argument(
        "--verify-complete",
        action="store_true",
        help=(
            "Exit nonzero when URLs or Skill sources remain unresolved, or when "
            "body-cache, document extraction, image OCR, or unsupported-asset "
            "issues remain; refuses a final snapshot while the crawler lock is held"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state_dir = args.state_dir.resolve()
    database_path = state_dir / "crawl.sqlite3"
    if not database_path.is_file():
        raise SystemExit(f"Crawl database not found: {database_path}")
    if args.verify_complete and advisory_lock_is_held(state_dir / "crawl.lock"):
        raise SystemExit(
            "Cannot verify a final audit snapshot while the crawler process lock is held"
        )
    skill_root = args.skill_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    ocr_dir = args.ocr_dir.resolve() if args.ocr_dir else state_dir / "ocr"

    report = build_report(database_path, state_dir, skill_root, ocr_dir)
    json_path = output_dir / "official-site-audit.json"
    markdown_path = output_dir / "official-site-audit.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(markdown_report(report), encoding="utf-8")
    print(f"JSON {json_path}")
    print(f"MARKDOWN {markdown_path}")
    print(
        "SUMMARY "
        f"complete={report['complete']} "
        f"pages={report['page_count']} "
        f"unresolved={len(report['unresolved'])} "
        f"skill_source_issues="
        f"{len(report['skill_source_issues']) + len(report['missing_skill_sources'])} "
        f"resolved_skill_source_aliases="
        f"{len(report['resolved_skill_source_aliases'])} "
        f"content_integrity_issues={len(report['content_integrity_issues'])} "
        f"body_integrity_issues={len(report['body_integrity_issues'])} "
        f"robots_integrity_issues={len(report['robots_integrity_issues'])} "
        f"document_issues={len(report['document_issues'])} "
        f"unparsed_asset_issues={len(report['unparsed_asset_issues'])} "
        f"visual_review_advisories={len(report['visual_review_advisories'])} "
        f"image_ocr_issues={len(report['image_ocr_issues'])} "
        f"image_ocr_warnings={len(report['image_ocr_warnings'])} "
        f"new_candidate_urls={report['discovered_relevant_candidate_url_count']} "
        f"new_candidate_bodies={len(report['discovered_relevant_candidates'])}"
    )
    if args.verify_complete and not report["complete"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
