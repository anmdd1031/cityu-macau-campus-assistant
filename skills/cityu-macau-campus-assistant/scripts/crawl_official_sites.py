#!/usr/bin/env python3
"""Crawl City University of Macau official sites strictly serially.

The crawler is intentionally conservative:

- one process lock prevents simultaneous crawls using the same state directory;
- one global rate limiter spaces every request start by at least one second;
- no thread pool, asyncio, multiprocessing, or parallel request path exists;
- HTTP 403 is never retried automatically;
- HTTP 429 respects Retry-After and is deferred instead of retried immediately;
- every discovered URL and fetch result is persisted in SQLite for resumption;
- formal document attachments, then content pages, are prioritized within each
  discovery depth; images and non-presentation support assets remain queued and
  are fetched last;
- response bodies are content-addressed so later audits can cite exact evidence.

The default scope is public HTTP(S) content on ``cityu.edu.mo`` and its
subdomains. The crawler submits no forms and does not attempt authenticated
pages.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import html
import http.client
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass, field
from datetime import datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo


OFFICIAL_SUFFIX = "cityu.edu.mo"
USER_AGENT = (
    "cityu-macau-campus-assistant-audit/1.0 "
    "(https://github.com/anmdd1031/cityu-macau-campus-assistant; "
    "strictly serial public-site audit)"
)
BEIJING = ZoneInfo("Asia/Shanghai")
TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "spm",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}
SESSION_QUERY_KEYS = {
    "jsessionid",
    "phpsessid",
    "session",
    "sessionid",
    "sid",
}
# The public faculty sites use ``p`` as a single pagination cursor. Some pages
# accidentally append a second ``p`` to the current URL (for example
# ``?p=1&p=2``). Treating both values as distinct creates an unbounded crawl
# trap as every subsequent page can append another value. The server-side
# navigation intends the last value to be the destination page.
SINGLE_VALUE_QUERY_KEYS = {"p"}
SKIP_SCHEMES = {"data", "javascript", "mailto", "tel", "wechat"}
SKIP_EXTENSIONS = {
    ".css",
    ".eot",
    ".otf",
    ".ttf",
    ".woff",
    ".woff2",
}
RETRYABLE_HTTP = {408, 425, 429, 500, 502, 503, 504}
MAX_REDIRECT_HOPS = 8
URL_START_PATTERN = re.compile(r"https?://", re.IGNORECASE)
URL_STOP_CHARACTERS = frozenset(
    "<>\"'`[]{}，。；：、（）【】《》“”‘’"
)
ROOT_RELATIVE_PATTERN = re.compile(r"""["'](/(?!/)[^"'<>\\\s]{2,})["']""")
SITEMAP_LOC_PATTERN = re.compile(r"<loc\b[^>]*>(.*?)</loc>", re.IGNORECASE | re.DOTALL)
META_REFRESH_URL_PATTERN = re.compile(r"\burl\s*=\s*['\"]?([^;'\"\s]+)", re.IGNORECASE)
SOFT_404_PATTERNS = (
    re.compile(r"\b404\b.{0,40}(?:錯誤|错误|error|not found)", re.IGNORECASE),
    re.compile(r"(?:錯誤|错误|error).{0,40}\b404\b", re.IGNORECASE),
    re.compile(r"\bpage\s+not\s+found\b", re.IGNORECASE),
    re.compile(r"(?:頁面|页面)(?:不存在|未找到)", re.IGNORECASE),
    re.compile(r"找不到(?:該|该)?(?:頁面|页面)", re.IGNORECASE),
)


DEFAULT_ROOTS = (
    "https://www.cityu.edu.mo/",
    "https://ado.cityu.edu.mo/",
    "https://fds.cityu.edu.mo/",
    "https://fob.cityu.edu.mo/",
    "https://fof.cityu.edu.mo/",
    "https://fhw.cityu.edu.mo/",
    "https://soe.cityu.edu.mo/",
    "https://sol.cityu.edu.mo/",
    "https://fitm.cityu.edu.mo/",
    "https://fhss.cityu.edu.mo/",
    "https://fiad.cityu.edu.mo/",
    "https://honors.cityu.edu.mo/",
    "https://registry.cityu.edu.mo/",
    "https://gs.cityu.edu.mo/",
    "https://sao.cityu.edu.mo/",
    "https://oga.cityu.edu.mo/",
    "https://lib.cityu.edu.mo/",
    "https://fid.cityu.edu.mo/",
    "https://disw.cityu.edu.mo/",
    "https://iap.cityu.edu.mo/",
    "https://imed.cityu.edu.mo/",
    "https://admission.cityu.edu.mo/",
)


def now_beijing() -> str:
    return datetime.now(BEIJING).isoformat(timespec="seconds")


def _acquire_advisory_lock(descriptor: int) -> None:
    """Acquire a non-blocking, process-held exclusive lock for ``descriptor``.

    A path-existence lock is vulnerable to a stale-lock race: one process can
    delete a newly-created lock belonging to another process.  Keep an OS lock
    on the open descriptor for the entire run instead.  The lock-file contents
    are only diagnostic metadata and are never used to decide ownership.
    """

    if os.name == "nt":
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        if os.fstat(descriptor).st_size == 0:
            os.write(descriptor, b"\0")
        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        return

    import fcntl

    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)


def _release_advisory_lock(descriptor: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        return

    import fcntl

    fcntl.flock(descriptor, fcntl.LOCK_UN)


def advisory_lock_is_held(path: Path) -> bool:
    """Return whether a current-format lock is held without changing metadata."""

    if not path.exists():
        return False
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR)
    try:
        try:
            _acquire_advisory_lock(descriptor)
        except OSError:
            return True
        try:
            _release_advisory_lock(descriptor)
        except OSError:
            pass
        return False
    finally:
        os.close(descriptor)


class AdvisoryProcessLock:
    """An OS-held exclusive lock with persistent, informational metadata."""

    def __init__(self, path: Path, purpose: str) -> None:
        self.path = path
        self.purpose = purpose
        self.descriptor: int | None = None

    def __enter__(self) -> "AdvisoryProcessLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.path, os.O_CREAT | os.O_RDWR)
        try:
            _acquire_advisory_lock(descriptor)
        except OSError as error:
            os.close(descriptor)
            detail = ""
            with contextlib.suppress(OSError):
                detail = self.path.read_text(
                    encoding="utf-8", errors="replace"
                ).strip()
            suffix = f"; metadata: {detail}" if detail else ""
            raise RuntimeError(
                f"Another {self.purpose} process is active; lock: {self.path}{suffix}"
            ) from error

        self.descriptor = descriptor
        payload = {
            "pid": os.getpid(),
            "purpose": self.purpose,
            "started_at": now_beijing(),
            "argv": sys.argv,
        }
        encoded = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        os.lseek(descriptor, 0, os.SEEK_SET)
        os.write(descriptor, encoded)
        with contextlib.suppress(OSError):
            os.ftruncate(descriptor, len(encoded))
        with contextlib.suppress(OSError):
            os.fsync(descriptor)
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.descriptor is None:
            return
        descriptor = self.descriptor
        self.descriptor = None
        with contextlib.suppress(OSError):
            _release_advisory_lock(descriptor)
        os.close(descriptor)


class CrawlLock(AdvisoryProcessLock):
    """Prevent two crawler processes from sharing one state directory."""

    def __init__(self, path: Path) -> None:
        super().__init__(path, "crawler")


class RateLimiter:
    def __init__(self, database: "CrawlDatabase", minimum_delay: float) -> None:
        if minimum_delay < 1.0:
            raise ValueError("minimum_delay must be at least 1.0 second")
        self.database = database
        self.minimum_delay = minimum_delay
        self.last_started_at = database.last_request_started_at()

    def wait(self) -> None:
        remaining = self.minimum_delay - (time.time() - self.last_started_at)
        if remaining > 0:
            time.sleep(remaining)
        self.last_started_at = time.time()
        # Persist before each outbound request so a later serial process also
        # respects the delay after this one exits unexpectedly.
        self.database.record_request_started_at(self.last_started_at)


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.base_href: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value for key, value in attrs if value}
        tag = tag.lower()
        if tag == "base" and values.get("href") and self.base_href is None:
            self.base_href = values["href"]

        for attribute in ("href", "src", "data-src", "poster"):
            value = values.get(attribute)
            if value:
                self.links.append((value, f"{tag}:{attribute}"))

        srcset = values.get("srcset")
        if srcset:
            for candidate in srcset.split(","):
                value = candidate.strip().split(" ", 1)[0]
                if value:
                    self.links.append((value, f"{tag}:srcset"))

        if tag == "meta" and values.get("http-equiv", "").lower() == "refresh":
            content = values.get("content", "")
            match = META_REFRESH_URL_PATTERN.search(content)
            if match:
                self.links.append((match.group(1), "meta:refresh"))


@dataclass
class FetchResult:
    requested_url: str
    final_url: str
    status: int
    content_type: str
    body: bytes
    headers: dict[str, str]
    error: str | None = None
    oversized: bool = False
    redirects: list[tuple[str, str]] = field(default_factory=list)


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Expose each redirect to the crawler instead of following it implicitly."""

    def redirect_request(
        self,
        request: urllib.request.Request,
        fp: object,
        code: int,
        message: str,
        headers: object,
        newurl: str,
    ) -> None:
        return None


def is_official_host(host: str, suffix: str = OFFICIAL_SUFFIX) -> bool:
    host = host.lower().rstrip(".")
    return host == suffix or host.endswith(f".{suffix}")


def iter_http_urls(text: str) -> Iterable[str]:
    """Yield text URLs while respecting balanced filename parentheses.

    A negated-character regex either truncates legitimate names such as
    ``GS-09a(2025).pdf`` or consumes the closing parenthesis and following
    prose from a Markdown link. This scanner includes balanced parentheses
    inside a URL and stops at the first unmatched closing parenthesis.
    """

    position = 0
    while match := URL_START_PATTERN.search(text, position):
        start = match.start()
        cursor = start
        parentheses = 0
        while cursor < len(text):
            character = text[cursor]
            if character.isspace() or character in URL_STOP_CHARACTERS:
                break
            if character == "(":
                parentheses += 1
            elif character == ")":
                if parentheses == 0:
                    break
                parentheses -= 1
            cursor += 1

        candidate = text[start:cursor]
        if candidate and parentheses == 0:
            yield candidate
        position = max(cursor, match.end())


def normalize_url(raw: str, base_url: str | None = None) -> str | None:
    raw = html.unescape(raw.strip()).rstrip("`'\".,;:，。；：、》】”’")
    # A Markdown destination contributes one unmatched closing parenthesis;
    # balanced parentheses can be part of an official attachment filename.
    while raw.endswith(")") and raw.count(")") > raw.count("("):
        raw = raw[:-1]
    if not raw or raw.startswith(("#", "{", "}")):
        return None
    try:
        if base_url:
            raw = urllib.parse.urljoin(base_url, raw)
        parsed = urllib.parse.urlsplit(raw)
    except (UnicodeError, ValueError):
        # Broken markup can place prose containing ``//`` in an href.  In
        # that case urllib may interpret the prose as a network location and
        # reject characters whose NFKC form changes URL delimiters.  A single
        # malformed link must not terminate an otherwise resumable crawl.
        return None
    scheme = parsed.scheme.lower()
    if scheme in SKIP_SCHEMES or scheme not in {"http", "https"}:
        return None
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        return None
    if scheme == "http" and is_official_host(host):
        scheme = "https"
    try:
        port = parsed.port
    except ValueError:
        return None
    netloc = host
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        netloc = f"{host}:{port}"

    path = parsed.path or "/"
    path = re.sub(r"/{2,}", "/", path)
    try:
        # Percent-encode parentheses even when the source spells them literally.
        # Several CityU attachment servers return HTTP 400 for the literal form.
        path = urllib.parse.quote(urllib.parse.unquote(path), safe="/:@!$&'*+,;=-._~%")
    except UnicodeError:
        return None

    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    filtered: list[tuple[str, str]] = []
    for key, value in query_pairs:
        lowered = key.lower()
        if lowered in TRACKING_QUERY_KEYS or lowered in SESSION_QUERY_KEYS:
            continue
        if lowered in SINGLE_VALUE_QUERY_KEYS:
            filtered = [
                (existing_key, existing_value)
                for existing_key, existing_value in filtered
                if existing_key.lower() != lowered
            ]
        filtered.append((key, value))
    filtered.sort()
    query = urllib.parse.urlencode(filtered, doseq=True)
    return urllib.parse.urlunsplit((scheme, netloc, path, query, ""))


def should_skip_by_extension(url: str) -> bool:
    suffix = Path(urllib.parse.urlsplit(url).path).suffix.lower()
    return suffix in SKIP_EXTENSIONS


def soft_404_reason(result: FetchResult) -> str | None:
    """Return a reason when a nominal success response is actually an error page."""

    final_path = urllib.parse.urlsplit(result.final_url).path.lower().rstrip("/")
    if final_path.endswith("/error_404"):
        return f"soft 404: redirected to {result.final_url}"

    is_html = result.content_type in {"text/html", "application/xhtml+xml"}
    if not is_html and b"<html" not in result.body[:2048].lower():
        return None

    text = result.body[:262_144].decode("utf-8", errors="replace")
    candidates: list[str] = []
    for pattern in (
        r"<title\b[^>]*>(.*?)</title>",
        r"<h[1-6]\b[^>]*>(.*?)</h[1-6]>",
    ):
        for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
            value = re.sub(r"<[^>]+>", " ", match.group(1))
            value = " ".join(html.unescape(value).split())
            if value:
                candidates.append(value)

    for value in candidates:
        if any(pattern.search(value) for pattern in SOFT_404_PATTERNS):
            return f"soft 404 heading: {value[:160]}"
    return None


def retry_after_seconds(headers: dict[str, str]) -> float:
    value = headers.get("retry-after", "").strip()
    if not value:
        return 5.0
    if value.isdigit():
        return min(float(value), 3600.0)
    try:
        target = parsedate_to_datetime(value)
        return max(5.0, min(target.timestamp() - time.time(), 3600.0))
    except (TypeError, ValueError, OverflowError):
        return 5.0


class CrawlDatabase:
    def __init__(
        self,
        path: Path,
        *,
        recover_interrupted: bool = True,
        readonly: bool = False,
    ) -> None:
        self.readonly = readonly
        if readonly:
            self.connection = sqlite3.connect(
                f"{path.resolve().as_uri()}?mode=ro",
                uri=True,
            )
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA query_only=ON")
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self._create_schema()
        if recover_interrupted:
            self.connection.execute(
                "UPDATE urls SET state='pending', error='interrupted before completion' "
                "WHERE state='fetching'"
            )
            self.connection.commit()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS urls (
                url TEXT PRIMARY KEY,
                host TEXT NOT NULL,
                state TEXT NOT NULL DEFAULT 'pending',
                depth INTEGER NOT NULL DEFAULT 0,
                discovered_from TEXT,
                discovery_context TEXT,
                discovered_at TEXT NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                next_attempt_at REAL NOT NULL DEFAULT 0,
                fetched_at TEXT,
                http_status INTEGER,
                content_type TEXT,
                final_url TEXT,
                sha256 TEXT,
                body_path TEXT,
                body_bytes INTEGER,
                error TEXT
            );
            CREATE INDEX IF NOT EXISTS urls_state_index
                ON urls(state, next_attempt_at, depth, url);
            CREATE INDEX IF NOT EXISTS urls_host_index ON urls(host, state);

            CREATE TABLE IF NOT EXISTS links (
                source_url TEXT NOT NULL,
                target_url TEXT NOT NULL,
                context TEXT NOT NULL,
                discovered_at TEXT NOT NULL,
                PRIMARY KEY (source_url, target_url, context)
            );

            CREATE TABLE IF NOT EXISTS hosts (
                host TEXT PRIMARY KEY,
                robots_state TEXT NOT NULL DEFAULT 'pending',
                robots_url TEXT,
                robots_status INTEGER,
                robots_body_path TEXT,
                robots_sha256 TEXT,
                robots_body_bytes INTEGER,
                robots_fetched_at TEXT,
                robots_next_attempt_at REAL NOT NULL DEFAULT 0,
                robots_error TEXT
            );

            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_at TEXT NOT NULL,
                event_type TEXT NOT NULL,
                url TEXT,
                detail TEXT
            );
            """
        )
        host_columns = {
            str(row[1])
            for row in self.connection.execute("PRAGMA table_info(hosts)")
        }
        for name, definition in (
            ("robots_sha256", "TEXT"),
            ("robots_body_bytes", "INTEGER"),
            ("robots_next_attempt_at", "REAL NOT NULL DEFAULT 0"),
        ):
            if name not in host_columns:
                self.connection.execute(
                    f"ALTER TABLE hosts ADD COLUMN {name} {definition}"
                )
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def event(self, event_type: str, url: str | None, detail: str) -> None:
        self.connection.execute(
            "INSERT INTO events(event_at, event_type, url, detail) VALUES (?, ?, ?, ?)",
            (now_beijing(), event_type, url, detail),
        )
        self.connection.commit()

    def last_request_started_at(self) -> float:
        row = self.connection.execute(
            "SELECT value FROM metadata WHERE key='last_request_started_at'"
        ).fetchone()
        if row is None:
            return 0.0
        try:
            return float(row[0])
        except (TypeError, ValueError):
            return 0.0

    def record_request_started_at(self, started_at: float) -> None:
        self.connection.execute(
            """
            INSERT INTO metadata(key, value) VALUES ('last_request_started_at', ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (repr(started_at),),
        )
        self.connection.commit()

    def ensure_host(self, host: str) -> bool:
        cursor = self.connection.execute(
            "INSERT OR IGNORE INTO hosts(host) VALUES (?)",
            (host,),
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def enqueue(
        self,
        url: str,
        depth: int,
        discovered_from: str | None,
        context: str,
    ) -> bool:
        parsed = urllib.parse.urlsplit(url)
        host = (parsed.hostname or "").lower()
        if not is_official_host(host):
            return False
        if should_skip_by_extension(url):
            self.connection.execute(
                """
                INSERT OR IGNORE INTO urls(
                    url, host, state, depth, discovered_from, discovery_context,
                    discovered_at, error
                ) VALUES (?, ?, 'skipped', ?, ?, ?, ?, 'skipped display-only dependency extension')
                """,
                (url, host, depth, discovered_from, context, now_beijing()),
            )
            self.connection.commit()
            return False
        self.ensure_host(host)
        cursor = self.connection.execute(
            """
            INSERT OR IGNORE INTO urls(
                url, host, state, depth, discovered_from, discovery_context,
                discovered_at
            ) VALUES (?, ?, 'pending', ?, ?, ?, ?)
            """,
            (url, host, depth, discovered_from, context, now_beijing()),
        )
        self.connection.commit()
        return cursor.rowcount > 0

    def record_link(self, source: str, target: str, context: str) -> None:
        self.connection.execute(
            """
            INSERT OR IGNORE INTO links(source_url, target_url, context, discovered_at)
            VALUES (?, ?, ?, ?)
            """,
            (source, target, context, now_beijing()),
        )

    def canonicalize_queued_urls(self) -> int:
        """Replace queued URLs whose canonical form changed after an upgrade.

        Historical fetched rows remain immutable evidence. Only pending rows
        and legacy HTTP-400 URL artifacts are superseded, so resuming a crawl
        never discards a successful response body.
        """

        rows = self.connection.execute(
            """
            SELECT url, host, depth, discovered_from, discovery_context,
                   discovered_at, state, http_status
            FROM urls
            WHERE state='pending'
               OR (state='failed' AND http_status=400 AND INSTR(url, '(') > 0)
            ORDER BY depth, url
            """
        ).fetchall()
        canonicalized = 0
        event_at = now_beijing()
        for row in rows:
            if row["state"] == "failed" and row["url"].count("(") != row["url"].count(")"):
                self.connection.execute(
                    """
                    UPDATE urls
                    SET state='skipped', next_attempt_at=0,
                        error='legacy URL extraction artifact: unbalanced parentheses'
                    WHERE url=? AND state='failed'
                    """,
                    (row["url"],),
                )
                self.connection.execute(
                    """
                    INSERT INTO events(event_at, event_type, url, detail)
                    VALUES (?, 'canonicalized', ?, 'skipped unbalanced legacy URL')
                    """,
                    (event_at, row["url"]),
                )
                canonicalized += 1
                continue

            canonical = normalize_url(row["url"])
            if not canonical or canonical == row["url"]:
                continue

            canonical_host = (
                urllib.parse.urlsplit(canonical).hostname or row["host"]
            ).lower()
            self.connection.execute(
                """
                INSERT OR IGNORE INTO urls(
                    url, host, state, depth, discovered_from,
                    discovery_context, discovered_at
                ) VALUES (?, ?, 'pending', ?, ?, ?, ?)
                """,
                (
                    canonical,
                    canonical_host,
                    row["depth"],
                    row["discovered_from"],
                    row["discovery_context"],
                    row["discovered_at"],
                ),
            )
            self.connection.execute(
                """
                UPDATE urls
                SET depth=MIN(depth, ?)
                WHERE url=? AND state='pending'
                """,
                (row["depth"], canonical),
            )
            self.connection.execute(
                """
                UPDATE urls
                SET state='skipped', next_attempt_at=0,
                    error=?
                WHERE url=? AND state IN ('pending', 'failed')
                """,
                (f"canonicalized to {canonical}", row["url"]),
            )
            self.connection.execute(
                """
                INSERT INTO events(event_at, event_type, url, detail)
                VALUES (?, 'canonicalized', ?, ?)
                """,
                (event_at, row["url"], canonical),
            )
            canonicalized += 1
        self.connection.commit()
        return canonicalized

    def discard_legacy_unmatched_closing_urls(self) -> int:
        """Skip URLs polluted by prose after an old Markdown-link parser."""

        rows = self.connection.execute(
            """
            SELECT url, discovered_from, discovery_context
            FROM urls
            WHERE state NOT IN ('skipped', 'robots_denied')
            """
        ).fetchall()
        unbalanced: dict[str, sqlite3.Row] = {}
        for row in rows:
            decoded_path = urllib.parse.unquote(
                urllib.parse.urlsplit(row["url"]).path
            )
            opening = decoded_path.count("(") + decoded_path.count("\uff08")
            closing = decoded_path.count(")") + decoded_path.count("\uff09")
            if closing > opening:
                unbalanced[row["url"]] = row

        # Restrict the migration to bad historical Skill seeds and their
        # descendants. A real server is still allowed to publish an unusual
        # unmatched-parenthesis URL in an HTML href.
        legacy_urls = {
            url
            for url, row in unbalanced.items()
            if row["discovery_context"] == "seed"
        }
        changed = True
        while changed:
            changed = False
            for url, row in unbalanced.items():
                if url not in legacy_urls and row["discovered_from"] in legacy_urls:
                    legacy_urls.add(url)
                    changed = True

        discarded = 0
        event_at = now_beijing()
        for url in sorted(legacy_urls):
            self.connection.execute(
                """
                UPDATE urls
                SET state='skipped', next_attempt_at=0,
                    error='legacy URL extraction artifact: unmatched closing parenthesis'
                WHERE url=?
                """,
                (url,),
            )
            self.connection.execute(
                """
                INSERT INTO events(event_at, event_type, url, detail)
                VALUES (?, 'canonicalized', ?, 'skipped unmatched closing URL')
                """,
                (event_at, url),
            )
            discarded += 1
        self.connection.commit()
        return discarded

    def requeue_newly_supported_assets(self) -> int:
        """Requeue informational assets skipped by an older extension policy."""

        rows = self.connection.execute(
            """
            SELECT url
            FROM urls
            WHERE state='skipped'
              AND error IN (
                    'skipped media or static extension',
                    'skipped presentation-only extension',
                    'skipped display-only dependency extension'
                  )
            """
        ).fetchall()
        supported = [row["url"] for row in rows if not should_skip_by_extension(row["url"])]
        event_at = now_beijing()
        for url in supported:
            self.connection.execute(
                """
                UPDATE urls
                SET state='pending', next_attempt_at=0, error=NULL
                WHERE url=? AND state='skipped'
                """,
                (url,),
            )
            self.connection.execute(
                """
                INSERT INTO events(event_at, event_type, url, detail)
                VALUES (?, 'requeued_supported_asset', ?, 'extension is no longer skipped')
                """,
                (event_at, url),
            )
        self.connection.commit()
        return len(supported)

    def next_pending(self) -> sqlite3.Row | None:
        return self.connection.execute(
            """
            SELECT * FROM urls
            WHERE state IN ('pending', 'deferred') AND next_attempt_at <= ?
            ORDER BY
                depth,
                CASE
                    WHEN LOWER(url) LIKE '%.pdf'
                      OR LOWER(url) LIKE '%.pdf?%'
                      OR LOWER(url) LIKE '%.doc'
                      OR LOWER(url) LIKE '%.doc?%'
                      OR LOWER(url) LIKE '%.docx'
                      OR LOWER(url) LIKE '%.docx?%'
                      OR LOWER(url) LIKE '%.xls'
                      OR LOWER(url) LIKE '%.xls?%'
                      OR LOWER(url) LIKE '%.xlsx'
                      OR LOWER(url) LIKE '%.xlsx?%'
                      OR LOWER(url) LIKE '%.ppt'
                      OR LOWER(url) LIKE '%.ppt?%'
                      OR LOWER(url) LIKE '%.pptx'
                      OR LOWER(url) LIKE '%.pptx?%'
                    THEN 0
                    WHEN LOWER(url) LIKE '%.jpg'
                      OR LOWER(url) LIKE '%.jpg?%'
                      OR LOWER(url) LIKE '%.jpeg'
                      OR LOWER(url) LIKE '%.jpeg?%'
                      OR LOWER(url) LIKE '%.png'
                      OR LOWER(url) LIKE '%.png?%'
                      OR LOWER(url) LIKE '%.gif'
                      OR LOWER(url) LIKE '%.gif?%'
                      OR LOWER(url) LIKE '%.webp'
                      OR LOWER(url) LIKE '%.webp?%'
                      OR LOWER(url) LIKE '%.svg'
                      OR LOWER(url) LIKE '%.svg?%'
                      OR LOWER(url) LIKE '%.ico'
                      OR LOWER(url) LIKE '%.ico?%'
                      OR LOWER(url) LIKE '%.css'
                      OR LOWER(url) LIKE '%.css?%'
                      OR LOWER(url) LIKE '%.js'
                      OR LOWER(url) LIKE '%.js?%'
                      OR LOWER(url) LIKE '%.woff'
                      OR LOWER(url) LIKE '%.woff?%'
                      OR LOWER(url) LIKE '%.woff2'
                      OR LOWER(url) LIKE '%.woff2?%'
                      OR LOWER(url) LIKE '%.ttf'
                      OR LOWER(url) LIKE '%.ttf?%'
                      OR LOWER(url) LIKE '%.eot'
                      OR LOWER(url) LIKE '%.eot?%'
                      OR LOWER(url) LIKE '%.3gp'
                      OR LOWER(url) LIKE '%.3gp?%'
                      OR LOWER(url) LIKE '%.aac'
                      OR LOWER(url) LIKE '%.aac?%'
                      OR LOWER(url) LIKE '%.mp3'
                      OR LOWER(url) LIKE '%.mp3?%'
                      OR LOWER(url) LIKE '%.mp4'
                      OR LOWER(url) LIKE '%.mp4?%'
                      OR LOWER(url) LIKE '%.mov'
                      OR LOWER(url) LIKE '%.mov?%'
                      OR LOWER(url) LIKE '%.avi'
                      OR LOWER(url) LIKE '%.avi?%'
                      OR LOWER(url) LIKE '%.flac'
                      OR LOWER(url) LIKE '%.flac?%'
                      OR LOWER(url) LIKE '%.flv'
                      OR LOWER(url) LIKE '%.flv?%'
                      OR LOWER(url) LIKE '%.m4a'
                      OR LOWER(url) LIKE '%.m4a?%'
                      OR LOWER(url) LIKE '%.m4v'
                      OR LOWER(url) LIKE '%.m4v?%'
                      OR LOWER(url) LIKE '%.mkv'
                      OR LOWER(url) LIKE '%.mkv?%'
                      OR LOWER(url) LIKE '%.mpeg'
                      OR LOWER(url) LIKE '%.mpeg?%'
                      OR LOWER(url) LIKE '%.mpg'
                      OR LOWER(url) LIKE '%.mpg?%'
                      OR LOWER(url) LIKE '%.ogg'
                      OR LOWER(url) LIKE '%.ogg?%'
                      OR LOWER(url) LIKE '%.ogv'
                      OR LOWER(url) LIKE '%.ogv?%'
                      OR LOWER(url) LIKE '%.wav'
                      OR LOWER(url) LIKE '%.wav?%'
                      OR LOWER(url) LIKE '%.webm'
                      OR LOWER(url) LIKE '%.webm?%'
                      OR LOWER(url) LIKE '%.zip'
                      OR LOWER(url) LIKE '%.zip?%'
                      OR LOWER(url) LIKE '%.rar'
                      OR LOWER(url) LIKE '%.rar?%'
                      OR LOWER(url) LIKE '%.7z'
                      OR LOWER(url) LIKE '%.7z?%'
                      OR LOWER(url) LIKE '%.tar'
                      OR LOWER(url) LIKE '%.tar?%'
                    THEN 2
                    ELSE 1
                END,
                url
            LIMIT 1
            """,
            (time.time(),),
        ).fetchone()

    def mark_fetching(self, url: str) -> None:
        self.connection.execute(
            "UPDATE urls SET state='fetching', attempts=attempts+1, error=NULL WHERE url=?",
            (url,),
        )
        self.connection.commit()

    def mark_result(
        self,
        url: str,
        state: str,
        result: FetchResult,
        sha256: str | None,
        body_path: str | None,
        error: str | None,
        next_attempt_at: float = 0,
    ) -> None:
        self.connection.execute(
            """
            UPDATE urls SET
                state=?,
                next_attempt_at=?,
                fetched_at=?,
                http_status=?,
                content_type=?,
                final_url=?,
                sha256=?,
                body_path=?,
                body_bytes=?,
                error=?
            WHERE url=?
            """,
            (
                state,
                next_attempt_at,
                now_beijing(),
                result.status,
                result.content_type,
                result.final_url,
                sha256,
                body_path,
                len(result.body),
                error,
                url,
            ),
        )
        self.connection.commit()

    def mark_robots(
        self,
        host: str,
        state: str,
        robots_url: str,
        status: int | None,
        body_path: str | None,
        sha256: str | None,
        body_bytes: int | None,
        error: str | None,
        next_attempt_at: float = 0,
    ) -> None:
        self.connection.execute(
            """
            UPDATE hosts SET
                robots_state=?,
                robots_url=?,
                robots_status=?,
                robots_body_path=?,
                robots_sha256=?,
                robots_body_bytes=?,
                robots_fetched_at=?,
                robots_next_attempt_at=?,
                robots_error=?
            WHERE host=?
            """,
            (
                state,
                robots_url,
                status,
                body_path,
                sha256,
                body_bytes,
                now_beijing(),
                next_attempt_at,
                error,
                host,
            ),
        )
        self.connection.commit()

    def host_row(self, host: str) -> sqlite3.Row:
        row = self.connection.execute("SELECT * FROM hosts WHERE host=?", (host,)).fetchone()
        if row is None:
            raise KeyError(host)
        return row

    def requeue_errors(self, max_attempts: int) -> int:
        cursor = self.connection.execute(
            f"""
            UPDATE urls
            SET state='pending', next_attempt_at=0
            WHERE state='failed'
              AND attempts < ?
              AND (
                    http_status IN ({','.join('?' for _ in RETRYABLE_HTTP)})
                    OR http_status = 0
                    OR http_status IS NULL
                  )
            """,
            (max_attempts, *sorted(RETRYABLE_HTTP)),
        )
        self.connection.commit()
        return cursor.rowcount

    def reset_unavailable_robots(self) -> int:
        """Retry a host's robots request only in an explicit later retry run.

        An unavailable robots.txt response is cached conservatively for the current
        run so no page on that host is fetched without a policy decision. When the
        operator explicitly requests ``--retry-errors`` in a later, still-serial
        run, the host state must return to ``pending`` as well as its deferred URLs;
        otherwise every URL would be deferred again without sending a new robots
        request.
        """

        cursor = self.connection.execute(
            """
            UPDATE hosts
            SET robots_state='pending', robots_next_attempt_at=0
            WHERE robots_state='unavailable'
            """
        )
        self.connection.commit()
        return cursor.rowcount

    def refresh_completed_seeds(self) -> int:
        """Revisit depth-zero sources after a long crawl to close freshness drift."""

        cursor = self.connection.execute(
            """
            UPDATE urls
            SET state='pending', next_attempt_at=0, error=NULL
            WHERE depth=0
              AND state IN ('fetched', 'soft_404')
            """
        )
        self.connection.commit()
        return cursor.rowcount

    def counts(self) -> dict[str, int]:
        rows = self.connection.execute(
            "SELECT state, COUNT(*) AS count FROM urls GROUP BY state ORDER BY state"
        ).fetchall()
        return {row["state"]: row["count"] for row in rows}

    def unresolved(self) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            SELECT url, state, attempts, http_status, error
            FROM urls
            WHERE state IN (
                'pending',
                'fetching',
                'deferred',
                'failed',
                'robots_denied',
                'soft_404'
            )
            ORDER BY state, url
            """
        ).fetchall()


class OfficialCrawler:
    def __init__(
        self,
        database: CrawlDatabase,
        state_dir: Path,
        delay: float,
        timeout: float,
        max_bytes: int,
    ) -> None:
        self.database = database
        self.state_dir = state_dir
        self.bodies_dir = state_dir / "bodies"
        self.bodies_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limiter = RateLimiter(database, delay)
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.robots: dict[str, urllib.robotparser.RobotFileParser] = {}
        self.opener = urllib.request.build_opener(NoRedirectHandler())

    def store_body(self, body: bytes) -> tuple[str, str]:
        digest = hashlib.sha256(body).hexdigest()
        relative = Path("bodies") / digest[:2] / f"{digest}.bin"
        destination = self.state_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        existing_is_valid = False
        if destination.is_file():
            try:
                if destination.stat().st_size == len(body):
                    hasher = hashlib.sha256()
                    with destination.open("rb") as stream:
                        while chunk := stream.read(1_048_576):
                            hasher.update(chunk)
                    existing_is_valid = hasher.hexdigest() == digest
            except OSError:
                existing_is_valid = False
        if not existing_is_valid:
            temporary = destination.with_name(
                f".{destination.name}.{os.getpid()}.{time.time_ns()}.tmp"
            )
            try:
                with temporary.open("xb") as stream:
                    stream.write(body)
                    stream.flush()
                    os.fsync(stream.fileno())
                with temporary.open("rb") as stream:
                    actual = hashlib.file_digest(stream, "sha256").hexdigest()
                if actual != digest:
                    raise RuntimeError("content hash changed while storing response body")
                os.replace(temporary, destination)
            finally:
                with contextlib.suppress(FileNotFoundError):
                    temporary.unlink()
        return digest, relative.as_posix()

    def _request_once(self, url: str) -> FetchResult:
        self.rate_limiter.wait()
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "application/pdf;q=0.8,*/*;q=0.5"
                ),
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.5",
            },
        )
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                status = int(response.status)
                headers = {key.lower(): value for key, value in response.headers.items()}
                content_type = headers.get("content-type", "").split(";", 1)[0].lower()
                body = response.read(self.max_bytes + 1)
                oversized = len(body) > self.max_bytes
                if oversized:
                    body = body[: self.max_bytes]
                return FetchResult(
                    requested_url=url,
                    final_url=url,
                    status=status,
                    content_type=content_type,
                    body=body,
                    headers=headers,
                    oversized=oversized,
                )
        except urllib.error.HTTPError as error:
            headers = {
                key.lower(): value
                for key, value in (error.headers.items() if error.headers else [])
            }
            content_type = headers.get("content-type", "").split(";", 1)[0].lower()
            body = b""
            with contextlib.suppress(OSError):
                body = error.read(min(self.max_bytes, 1_048_576))
            return FetchResult(
                requested_url=url,
                final_url=url,
                status=int(error.code),
                content_type=content_type,
                body=body,
                headers=headers,
                error=f"HTTP {error.code}: {error.reason}",
            )
        except (
            urllib.error.URLError,
            http.client.HTTPException,
            TimeoutError,
            OSError,
        ) as error:
            return FetchResult(
                requested_url=url,
                final_url=url,
                status=0,
                content_type="",
                body=b"",
                headers={},
                error=f"{type(error).__name__}: {error}",
            )

    def request(self, url: str) -> FetchResult:
        """Fetch an official URL with an explicit, rate-limited redirect chain."""

        current = normalize_url(url)
        if not current or not is_official_host(
            urllib.parse.urlsplit(current).hostname or ""
        ):
            return FetchResult(
                requested_url=url,
                final_url=url,
                status=0,
                content_type="",
                body=b"",
                headers={},
                error="refusing to request a non-official or invalid URL",
            )

        redirects: list[tuple[str, str]] = []
        seen = {current}
        for _hop in range(MAX_REDIRECT_HOPS + 1):
            result = self._request_once(current)
            result.requested_url = url
            result.final_url = current
            result.redirects = list(redirects)
            if not 300 <= result.status < 400:
                return result

            if len(redirects) >= MAX_REDIRECT_HOPS:
                result.error = f"redirect limit exceeded ({MAX_REDIRECT_HOPS} hops)"
                return result
            location = result.headers.get("location", "").strip()
            if not location:
                result.error = (
                    f"HTTP {result.status} redirect without a Location header"
                )
                return result
            target = normalize_url(location, current)
            if not target:
                result.error = (
                    f"HTTP {result.status} redirect has an invalid Location: {location!r}"
                )
                return result
            target_host = urllib.parse.urlsplit(target).hostname or ""
            if not is_official_host(target_host):
                result.error = (
                    f"HTTP {result.status} redirect leaves official scope: {target}"
                )
                return result
            if target in seen:
                result.error = f"HTTP {result.status} redirect loop: {target}"
                return result
            redirects.append((current, target))
            seen.add(target)
            current = target

        return FetchResult(
            requested_url=url,
            final_url=current,
            status=0,
            content_type="",
            body=b"",
            headers={},
            error=f"redirect limit exceeded ({MAX_REDIRECT_HOPS} hops)",
            redirects=redirects,
        )

    def robots_for(self, host: str, scheme: str) -> urllib.robotparser.RobotFileParser:
        if host in self.robots:
            return self.robots[host]

        self.database.ensure_host(host)
        row = self.database.host_row(host)
        robots_url = f"{scheme}://{host}/robots.txt"
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)

        if row["robots_state"] == "fetched" and row["robots_body_path"]:
            try:
                body = (self.state_dir / row["robots_body_path"]).read_bytes()
                expected = str(
                    row["robots_sha256"]
                    or Path(str(row["robots_body_path"])).stem
                )
                if (
                    not re.fullmatch(r"[0-9a-f]{64}", expected)
                    or hashlib.sha256(body).hexdigest() != expected
                ):
                    raise OSError("cached robots body hash does not match")
                parser.parse(body.decode("utf-8", errors="replace").splitlines())
                self.robots[host] = parser
                return parser
            except (OSError, ValueError):
                # A failed process must not cause a partial robots response to
                # be trusted on every later resume.  Re-fetch it conservatively.
                self.database.mark_robots(
                    host,
                    "pending",
                    robots_url,
                    None,
                    None,
                    None,
                    None,
                    "cached robots body is missing or has an invalid hash",
                )
        if row["robots_state"] == "not_found":
            parser.parse(["User-agent: *", "Disallow:"])
            self.robots[host] = parser
            return parser
        if (
            row["robots_state"] == "unavailable"
            and float(row["robots_next_attempt_at"] or 0) > time.time()
        ):
            parser.parse(["User-agent: *", "Disallow: /"])
            self.robots[host] = parser
            return parser

        result = self.request(robots_url)
        body_path: str | None = None
        digest: str | None = None
        if result.body:
            digest, body_path = self.store_body(result.body)
        for source, target in result.redirects:
            self.database.record_link(source, target, "http:redirect")
        if result.redirects:
            self.database.connection.commit()

        if 200 <= result.status < 300:
            text = result.body.decode("utf-8", errors="replace")
            parser.parse(text.splitlines())
            self.database.mark_robots(
                host,
                "fetched",
                robots_url,
                result.status,
                body_path,
                digest,
                len(result.body),
                None,
            )
            for line in text.splitlines():
                if line.lower().startswith("sitemap:"):
                    candidate = normalize_url(line.split(":", 1)[1].strip(), robots_url)
                    if candidate and is_official_host(
                        urllib.parse.urlsplit(candidate).hostname or ""
                    ):
                        self.database.enqueue(candidate, 0, robots_url, "robots:sitemap")
        elif result.status in {404, 410}:
            parser.parse(["User-agent: *", "Disallow:"])
            self.database.mark_robots(
                host,
                "not_found",
                robots_url,
                result.status,
                body_path,
                digest,
                len(result.body),
                result.error,
            )
        else:
            parser.parse(["User-agent: *", "Disallow: /"])
            wait_seconds = (
                retry_after_seconds(result.headers)
                if result.status == 429
                else 300.0
            )
            self.database.mark_robots(
                host,
                "unavailable",
                robots_url,
                result.status or None,
                body_path,
                digest,
                len(result.body),
                result.error or "robots.txt unavailable",
                next_attempt_at=time.time() + wait_seconds,
            )
        self.robots[host] = parser
        return parser

    def discover_text_links(
        self,
        source_url: str,
        text: str,
        context: str,
        depth: int,
    ) -> int:
        discovered = 0
        candidates: list[tuple[str, str]] = [
            (candidate, f"{context}:absolute")
            for candidate in iter_http_urls(text)
        ]
        candidates.extend(
            (match.group(1), f"{context}:root-relative")
            for match in ROOT_RELATIVE_PATTERN.finditer(text)
        )
        for raw, link_context in candidates:
            normalized = normalize_url(raw, source_url)
            if not normalized:
                continue
            self.database.record_link(source_url, normalized, link_context)
            host = urllib.parse.urlsplit(normalized).hostname or ""
            if is_official_host(host) and self.database.enqueue(
                normalized, depth + 1, source_url, link_context
            ):
                discovered += 1
        self.database.connection.commit()
        return discovered

    def discover_links(
        self,
        source_url: str,
        body: bytes,
        content_type: str,
        depth: int,
    ) -> int:
        if not body:
            return 0
        text_types = {
            "application/atom+xml",
            "application/javascript",
            "application/json",
            "application/ld+json",
            "application/rss+xml",
            "application/xhtml+xml",
            "application/xml",
            "text/html",
            "text/javascript",
            "text/plain",
            "text/xml",
        }
        path_suffix = Path(urllib.parse.urlsplit(source_url).path).suffix.lower()
        is_text = (
            content_type in text_types
            or content_type.startswith("text/")
            or path_suffix in {".asp", ".aspx", ".htm", ".html", ".js", ".json", ".php", ".xml"}
        )
        if not is_text:
            return 0

        text = body.decode("utf-8", errors="replace")
        discovered = 0
        if content_type in {"text/html", "application/xhtml+xml"} or "<html" in text[:2048].lower():
            parser = LinkExtractor()
            with contextlib.suppress(Exception):
                parser.feed(text)
            base = normalize_url(parser.base_href, source_url) if parser.base_href else source_url
            base = base or source_url
            for raw, link_context in parser.links:
                normalized = normalize_url(raw, base)
                if not normalized:
                    continue
                self.database.record_link(source_url, normalized, link_context)
                host = urllib.parse.urlsplit(normalized).hostname or ""
                if is_official_host(host) and self.database.enqueue(
                    normalized, depth + 1, source_url, link_context
                ):
                    discovered += 1

        for match in SITEMAP_LOC_PATTERN.finditer(text):
            normalized = normalize_url(html.unescape(match.group(1).strip()), source_url)
            if not normalized:
                continue
            self.database.record_link(source_url, normalized, "xml:loc")
            host = urllib.parse.urlsplit(normalized).hostname or ""
            if is_official_host(host) and self.database.enqueue(
                normalized, depth + 1, source_url, "xml:loc"
            ):
                discovered += 1

        discovered += self.discover_text_links(source_url, text, "text", depth)
        self.database.connection.commit()
        return discovered

    def fetch_one(self, row: sqlite3.Row) -> None:
        url = row["url"]
        host = row["host"]
        depth = int(row["depth"])
        parsed = urllib.parse.urlsplit(url)
        self.database.mark_fetching(url)

        robots = self.robots_for(host, parsed.scheme)
        robots_row = self.database.host_row(host)
        if robots_row["robots_state"] == "unavailable":
            result = FetchResult(url, url, 0, "", b"", {})
            retry_at = float(robots_row["robots_next_attempt_at"] or 0)
            if retry_at <= time.time():
                retry_at = time.time() + 300
            self.database.mark_result(
                url,
                "deferred",
                result,
                None,
                None,
                f"robots.txt unavailable: {robots_row['robots_error']}",
                next_attempt_at=retry_at,
            )
            self.database.event(
                "robots_unavailable",
                url,
                str(robots_row["robots_error"] or "robots.txt unavailable"),
            )
            print(f"DEFER robots-unavailable {url}", flush=True)
            return
        if not robots.can_fetch(USER_AGENT, url):
            result = FetchResult(url, url, 0, "", b"", {})
            self.database.mark_result(
                url,
                "robots_denied",
                result,
                None,
                None,
                "disallowed by robots.txt",
            )
            self.database.event("robots_skip", url, "robots policy denied fetch")
            print(f"BLOCK robots {url}", flush=True)
            return

        result = self.request(url)
        for source, target in result.redirects:
            self.database.record_link(source, target, "http:redirect")
        if result.redirects:
            self.database.connection.commit()
        digest: str | None = None
        body_path: str | None = None
        if result.body:
            digest, body_path = self.store_body(result.body)

        if result.oversized:
            self.database.mark_result(
                url,
                "failed",
                result,
                digest,
                body_path,
                f"response exceeded --max-bytes ({self.max_bytes})",
            )
            print(f"FAIL oversized {url}", flush=True)
            return

        soft_error = soft_404_reason(result) if 200 <= result.status < 400 else None
        if soft_error:
            self.database.mark_result(
                url, "soft_404", result, digest, body_path, soft_error
            )
            print(f"FAIL soft-404 {url}", flush=True)
            return

        if 200 <= result.status < 400:
            self.database.mark_result(
                url, "fetched", result, digest, body_path, result.error
            )
            final_normalized = normalize_url(result.final_url)
            if final_normalized and final_normalized != url:
                self.database.enqueue(
                    final_normalized, depth, url, "http:redirect"
                )
            new_links = self.discover_links(
                final_normalized or url,
                result.body,
                result.content_type,
                depth,
            )
            print(
                f"OK {result.status} links+{new_links} bytes={len(result.body)} {url}",
                flush=True,
            )
            return

        if result.status == 429:
            wait = retry_after_seconds(result.headers)
            self.database.mark_result(
                url,
                "deferred",
                result,
                digest,
                body_path,
                result.error,
                next_attempt_at=time.time() + wait,
            )
            print(f"DEFER 429 wait={wait:.0f}s {url}", flush=True)
            return

        if result.status == 403:
            self.database.mark_result(
                url, "failed", result, digest, body_path, result.error
            )
            print(f"FAIL 403 no-retry {url}", flush=True)
            return

        state = "failed"
        self.database.mark_result(
            url, state, result, digest, body_path, result.error or "request failed"
        )
        print(
            f"FAIL status={result.status or 'network'} {result.error or ''} {url}",
            flush=True,
        )

    def run(self, max_fetches: int) -> int:
        completed = 0
        while True:
            if max_fetches and completed >= max_fetches:
                break
            row = self.database.next_pending()
            if row is None:
                break
            self.fetch_one(row)
            completed += 1
        return completed


def iter_skill_urls(skill_root: Path) -> Iterable[str]:
    for path in sorted(skill_root.rglob("*")):
        if not path.is_file() or any(part in {".cache", "__pycache__"} for part in path.parts):
            continue
        if path.suffix.lower() not in {".md", ".py", ".yaml", ".yml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for candidate in iter_http_urls(text):
            normalized = normalize_url(candidate)
            if normalized:
                host = urllib.parse.urlsplit(normalized).hostname or ""
                if is_official_host(host):
                    yield normalized


def seed_database(
    database: CrawlDatabase,
    skill_root: Path,
    extra_seeds: Iterable[str],
) -> dict[str, int]:
    added = 0
    seen_hosts: set[str] = set()

    candidates = list(DEFAULT_ROOTS)
    candidates.extend(iter_skill_urls(skill_root))
    candidates.extend(extra_seeds)
    for raw in candidates:
        normalized = normalize_url(raw)
        if not normalized:
            continue
        host = urllib.parse.urlsplit(normalized).hostname or ""
        if not is_official_host(host):
            continue
        seen_hosts.add(host)
        if database.enqueue(normalized, 0, None, "seed"):
            added += 1

    # A subdomain can first appear as a deep link (for example a login or
    # document URL) after the initial seed pass. On every resume, bootstrap the
    # root and sitemap of every official host already recorded in the crawl so
    # that a deep discovery cannot leave the public host entry point unvisited.
    seen_hosts.update(
        str(row[0])
        for row in database.connection.execute("SELECT host FROM hosts ORDER BY host")
        if is_official_host(str(row[0]))
    )

    for host in sorted(seen_hosts):
        for scheme in ("https",):
            for path in ("/", "/sitemap.xml"):
                normalized = normalize_url(f"{scheme}://{host}{path}")
                if normalized and database.enqueue(normalized, 0, None, "host-bootstrap"):
                    added += 1
    return {"added": added, "hosts": len(seen_hosts)}


def reclassify_stored_soft_404(
    database: CrawlDatabase,
    state_dir: Path,
) -> int:
    """Reclassify stored HTML fetched by an older crawler version."""

    changed = 0
    rows = database.connection.execute(
        """
        SELECT url, final_url, http_status, content_type, body_path
        FROM urls
        WHERE state='fetched'
          AND body_path IS NOT NULL
          AND http_status BETWEEN 200 AND 399
          AND (
                lower(content_type) IN ('text/html', 'application/xhtml+xml')
             OR lower(content_type) LIKE 'text/%'
             OR content_type IS NULL
             OR content_type = ''
          )
        """
    ).fetchall()
    for index, row in enumerate(rows, start=1):
        body_path = state_dir / row["body_path"]
        if not body_path.is_file():
            continue
        with body_path.open("rb") as stream:
            body_prefix = stream.read(262_144)
        result = FetchResult(
            requested_url=row["url"],
            final_url=row["final_url"] or row["url"],
            status=int(row["http_status"]),
            content_type=row["content_type"] or "",
            body=body_prefix,
            headers={},
        )
        reason = soft_404_reason(result)
        if not reason:
            continue
        database.connection.execute(
            "UPDATE urls SET state='soft_404', error=? WHERE url=?",
            (reason, row["url"]),
        )
        changed += 1
        if index % 1000 == 0:
            print(
                f"RECLASSIFY scan={index}/{len(rows)} changed={changed}",
                flush=True,
            )
    database.connection.commit()
    return changed


def write_report(database: CrawlDatabase, path: Path) -> None:
    counts = database.counts()
    unresolved = database.unresolved()
    host_rows = database.connection.execute(
        """
        SELECT h.host, h.robots_state,
               SUM(CASE WHEN u.state='fetched' THEN 1 ELSE 0 END) AS fetched,
               SUM(CASE WHEN u.state='pending' THEN 1 ELSE 0 END) AS pending,
               SUM(CASE WHEN u.state='failed' THEN 1 ELSE 0 END) AS failed,
               SUM(CASE WHEN u.state='deferred' THEN 1 ELSE 0 END) AS deferred,
               SUM(CASE WHEN u.state='robots_denied' THEN 1 ELSE 0 END) AS robots_denied,
               SUM(CASE WHEN u.state='soft_404' THEN 1 ELSE 0 END) AS soft_404,
               SUM(CASE WHEN u.state='skipped' THEN 1 ELSE 0 END) AS skipped
        FROM hosts h
        LEFT JOIN urls u ON u.host=h.host
        GROUP BY h.host, h.robots_state
        ORDER BY h.host
        """
    ).fetchall()
    payload = {
        "generated_at": now_beijing(),
        "counts": counts,
        "complete": not unresolved,
        "hosts": [dict(row) for row in host_rows],
        "unresolved": [dict(row) for row in unresolved],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    script_path = Path(__file__).resolve()
    skill_root = script_path.parent.parent
    repository_root = skill_root.parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=repository_root / ".cache" / "cityu-official-crawl",
        help="Ignored persistent crawl state and body store",
    )
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=skill_root,
        help="Skill folder whose official URLs are used as seeds",
    )
    parser.add_argument("--seed", action="append", default=[], help="Additional seed URL")
    parser.add_argument(
        "--delay",
        type=float,
        default=1.2,
        help="Minimum seconds between every request start; must be >= 1.0",
    )
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=100 * 1024 * 1024,
        help="Maximum response bytes; oversized responses remain unresolved",
    )
    parser.add_argument(
        "--max-fetches",
        type=int,
        default=0,
        help="Stop after N URL fetches; 0 means run until the current queue is empty",
    )
    parser.add_argument(
        "--retry-errors",
        action="store_true",
        help="Requeue retryable failures with fewer than --max-attempts attempts",
    )
    parser.add_argument(
        "--refresh-seeds",
        action="store_true",
        help=(
            "Re-fetch completed depth-zero Skill sources, host roots, and "
            "sitemaps once after a long crawl"
        ),
    )
    parser.add_argument("--max-attempts", type=int, default=2)
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write report.json without sending network requests",
    )
    parser.add_argument(
        "--verify-complete",
        action="store_true",
        help=(
            "Exit nonzero unless no pending, deferred, failed, fetching, "
            "robots-denied, or soft-404 URLs remain"
        ),
    )
    args = parser.parse_args()
    if args.delay < 1.0:
        parser.error("--delay must be at least 1.0 second")
    if args.max_bytes < 1:
        parser.error("--max-bytes must be positive")
    if args.max_fetches < 0:
        parser.error("--max-fetches cannot be negative")
    if args.max_attempts < 1:
        parser.error("--max-attempts must be positive")
    return args


def main() -> int:
    args = parse_args()
    state_dir = args.state_dir.resolve()
    state_dir.mkdir(parents=True, exist_ok=True)
    database_path = state_dir / "crawl.sqlite3"

    if args.report_only:
        if not database_path.is_file():
            raise SystemExit(f"Crawl database not found: {database_path}")
        lock_held = advisory_lock_is_held(state_dir / "crawl.lock")
        if args.verify_complete and lock_held:
            print(
                "Cannot verify a final crawl snapshot while the crawler process lock is held",
                file=sys.stderr,
            )
            return 2
        if lock_held:
            print("SNAPSHOT active_crawler_lock=true (non-final)", flush=True)
        database = CrawlDatabase(
            database_path,
            recover_interrupted=False,
            readonly=True,
        )
        try:
            write_report(database, state_dir / "report.json")
            counts = database.counts()
            print(
                f"COUNTS {json.dumps(counts, ensure_ascii=False, sort_keys=True)}",
                flush=True,
            )
            unresolved = database.unresolved()
            if args.verify_complete and unresolved:
                print(f"INCOMPLETE unresolved={len(unresolved)}", file=sys.stderr)
                return 2
            return 0
        finally:
            database.close()

    # Acquire the process lock before opening a writable database. This keeps an
    # accidental second invocation from resetting an active row or seeding URLs
    # before it discovers that another crawler is already running.
    with CrawlLock(state_dir / "crawl.lock"):
        database = CrawlDatabase(database_path)
        try:
            canonicalized = database.canonicalize_queued_urls()
            if canonicalized:
                print(f"CANONICALIZE queued={canonicalized}", flush=True)
            discarded = database.discard_legacy_unmatched_closing_urls()
            if discarded:
                print(f"DISCARD legacy_unmatched_closing={discarded}", flush=True)
            requeued_assets = database.requeue_newly_supported_assets()
            if requeued_assets:
                print(f"REQUEUE supported_assets={requeued_assets}", flush=True)
            seeded = seed_database(database, args.skill_root.resolve(), args.seed)
            print(
                f"SEED added={seeded['added']} hosts={seeded['hosts']} "
                f"state={state_dir}",
                flush=True,
            )
            reclassified = reclassify_stored_soft_404(database, state_dir)
            if reclassified:
                print(f"RECLASSIFY soft_404={reclassified}", flush=True)
            if args.retry_errors:
                reset_robots = database.reset_unavailable_robots()
                requeued = database.requeue_errors(args.max_attempts)
                print(
                    f"REQUEUE count={requeued} robots_unavailable={reset_robots}",
                    flush=True,
                )
            if args.refresh_seeds:
                refreshed = database.refresh_completed_seeds()
                print(f"REFRESH seeds={refreshed}", flush=True)

            crawler = OfficialCrawler(
                database=database,
                state_dir=state_dir,
                delay=args.delay,
                timeout=args.timeout,
                max_bytes=args.max_bytes,
            )
            completed = crawler.run(args.max_fetches)
            print(f"RUN fetched_attempts={completed}", flush=True)

            write_report(database, state_dir / "report.json")
            counts = database.counts()
            print(
                f"COUNTS {json.dumps(counts, ensure_ascii=False, sort_keys=True)}",
                flush=True,
            )
            unresolved = database.unresolved()
            if args.verify_complete and unresolved:
                print(f"INCOMPLETE unresolved={len(unresolved)}", file=sys.stderr)
                return 2
            return 0
        finally:
            database.close()


if __name__ == "__main__":
    raise SystemExit(main())
