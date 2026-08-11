#!/usr/bin/env python3
"""Offline regression checks for the serial crawler retry state machine.

Run this file directly.  Every response is synthetic: it creates temporary
SQLite state and never opens a network connection.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import unittest
import urllib.robotparser
import uuid
from pathlib import Path

from crawl_official_sites import (
    MIN_RETRY_AFTER_SECONDS,
    ROBOTS_RETRY_EXHAUSTED,
    SOFT_404_RECLASSIFICATION_KEY,
    CrawlDatabase,
    FetchResult,
    OfficialCrawler,
    reclassify_stored_soft_404,
    retry_after_seconds,
    write_report,
)


def result(url: str, status: int, *, retry_after: str | None = None) -> FetchResult:
    headers = {"retry-after": retry_after} if retry_after is not None else {}
    return FetchResult(
        requested_url=url,
        final_url=url,
        status=status,
        content_type="text/html",
        body=b"",
        headers=headers,
        error=f"HTTP {status}",
    )


class SyntheticCrawler(OfficialCrawler):
    """A crawler whose request method returns configured local responses only."""

    def __init__(self, *args: object, robots_status: int = 404, page_status: int = 200, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.robots_status = robots_status
        self.page_status = page_status
        self.request_urls: list[str] = []

    def request(self, url: str) -> FetchResult:
        self.request_urls.append(url)
        if url.endswith("/robots.txt"):
            return result(url, self.robots_status, retry_after="0")
        return result(url, self.page_status, retry_after="0")


class CrawlRetrySemanticsTests(unittest.TestCase):
    def setUp(self) -> None:
        # Keep test state inside the checkout so Windows sandboxing and the
        # crawler's own path rules match the environments used by maintainers.
        temporary_root = Path(__file__).resolve().parents[3] / ".cache" / "crawl-retry-tests"
        temporary_root.mkdir(parents=True, exist_ok=True)
        self.state_dir = temporary_root / f"run-{uuid.uuid4().hex}"
        self.state_dir.mkdir()
        self.database = CrawlDatabase(self.state_dir / "crawl.sqlite3")

    def tearDown(self) -> None:
        self.database.close()
        shutil.rmtree(self.state_dir)

    def crawler(self, max_attempts: int = 2, **kwargs: object) -> SyntheticCrawler:
        return SyntheticCrawler(
            database=self.database,
            state_dir=self.state_dir,
            delay=1.0,
            timeout=1.0,
            max_bytes=1_024,
            max_attempts=max_attempts,
            **kwargs,
        )

    def allow_host_without_network(self, host: str) -> None:
        self.database.ensure_host(host)
        self.database.mark_robots(
            host,
            "not_found",
            f"https://{host}/robots.txt",
            404,
            None,
            None,
            0,
            None,
            attempted=True,
            reset_attempts=True,
        )

    def page(self, url: str) -> object:
        return self.database.connection.execute(
            "SELECT * FROM urls WHERE url=?", (url,)
        ).fetchone()

    def test_retry_after_zero_is_floored_and_429_budget_is_bounded(self) -> None:
        self.assertEqual(
            retry_after_seconds({"retry-after": "0"}), MIN_RETRY_AFTER_SECONDS
        )
        host = "rate-limit.cityu.edu.mo"
        url = f"https://{host}/page"
        self.allow_host_without_network(host)
        self.database.enqueue(url, 0, None, "test")
        crawler = self.crawler(page_status=429)

        crawler.fetch_one(self.database.next_pending(2))
        first = self.page(url)
        self.assertEqual(first["state"], "deferred")
        self.assertEqual(first["attempts"], 1)
        self.assertGreater(first["next_attempt_at"], 0)

        self.database.connection.execute(
            "UPDATE urls SET next_attempt_at=0 WHERE url=?", (url,)
        )
        self.database.connection.commit()
        crawler.fetch_one(self.database.next_pending(2))
        second = self.page(url)
        self.assertEqual(second["state"], "failed")
        self.assertEqual(second["attempts"], 2)
        self.assertIn("retry budget exhausted", second["error"])
        self.assertIsNone(self.database.next_pending(2))

    def test_robots_unavailable_uses_host_budget_without_page_attempts(self) -> None:
        host = "robots-timeout.cityu.edu.mo"
        urls = [f"https://{host}/one", f"https://{host}/two"]
        for url in urls:
            self.database.enqueue(url, 0, None, "test")
        crawler = self.crawler(robots_status=429)

        crawler.fetch_one(self.database.next_pending(2))
        crawler.fetch_one(self.database.next_pending(2))
        self.assertEqual(crawler.request_urls, [f"https://{host}/robots.txt"])
        self.assertEqual(self.database.host_row(host)["robots_attempts"], 1)
        self.assertEqual({self.page(url)["attempts"] for url in urls}, {0})
        self.assertEqual({self.page(url)["state"] for url in urls}, {"deferred"})

        self.database.connection.execute(
            "UPDATE hosts SET robots_next_attempt_at=0 WHERE host=?", (host,)
        )
        self.database.connection.execute(
            "UPDATE urls SET next_attempt_at=0 WHERE host=?", (host,)
        )
        self.database.connection.commit()
        crawler.fetch_one(self.database.next_pending(2))

        self.assertEqual(
            crawler.request_urls,
            [f"https://{host}/robots.txt", f"https://{host}/robots.txt"],
        )
        self.assertEqual(
            self.database.host_row(host)["robots_attempts"],
            ROBOTS_RETRY_EXHAUSTED,
        )
        self.assertEqual(
            {self.page(url)["state"] for url in urls}, {"robots_unavailable"}
        )
        self.assertEqual({self.page(url)["attempts"] for url in urls}, {0})
        self.assertIsNone(self.database.next_pending(2))

        higher_budget = self.crawler(max_attempts=3, robots_status=429)
        higher_budget.robots_for(host, "https")
        self.assertEqual(higher_budget.request_urls, [])

        self.database.connection.execute(
            "UPDATE hosts SET robots_next_attempt_at=0 WHERE host=?", (host,)
        )
        self.database.connection.commit()
        reset_hosts, reset_urls = self.database.reset_unavailable_robots(2)
        self.assertEqual((reset_hosts, reset_urls), (1, 2))
        self.assertEqual(self.database.host_row(host)["robots_attempts"], 0)
        self.assertEqual({self.page(url)["state"] for url in urls}, {"pending"})

    def test_legacy_robot_deferred_urls_require_explicit_reset(self) -> None:
        legacy_dir = self.state_dir / "legacy"
        legacy_dir.mkdir()
        legacy_path = legacy_dir / "crawl.sqlite3"
        host = "legacy-robots.cityu.edu.mo"
        url = f"https://{host}/page"
        interrupted_url = f"https://{host}/interrupted"
        connection = sqlite3.connect(legacy_path)
        try:
            connection.executescript(
                """
                CREATE TABLE urls (
                    url TEXT PRIMARY KEY,
                    host TEXT NOT NULL,
                    state TEXT NOT NULL,
                    depth INTEGER NOT NULL DEFAULT 0,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    next_attempt_at REAL NOT NULL DEFAULT 0,
                    http_status INTEGER,
                    error TEXT
                );
                CREATE TABLE hosts (
                    host TEXT PRIMARY KEY,
                    robots_state TEXT NOT NULL,
                    robots_next_attempt_at REAL NOT NULL DEFAULT 0,
                    robots_error TEXT
                );
                """
            )
            connection.execute(
                """
                INSERT INTO urls(url, host, state, attempts, next_attempt_at, http_status, error)
                VALUES (?, ?, 'deferred', 8, 0, 0, 'robots.txt unavailable: HTTP 429')
                """,
                (url, host),
            )
            connection.execute(
                """
                INSERT INTO urls(url, host, state, attempts, next_attempt_at, http_status, error)
                VALUES (?, ?, 'fetching', 8, 0, NULL, NULL)
                """,
                (interrupted_url, host),
            )
            connection.execute(
                """
                INSERT INTO hosts(host, robots_state, robots_next_attempt_at, robots_error)
                VALUES (?, 'unavailable', 0, 'HTTP 429')
                """,
                (host,),
            )
            connection.commit()
        finally:
            connection.close()

        legacy = CrawlDatabase(legacy_path)
        try:
            migrated = {
                row["url"]: row
                for row in legacy.connection.execute(
                    "SELECT url, state, attempts, error FROM urls WHERE host=?",
                    (host,),
                )
            }
            self.assertEqual(migrated[url]["state"], "robots_unavailable")
            self.assertEqual(migrated[interrupted_url]["state"], "robots_unavailable")
            self.assertEqual({row["attempts"] for row in migrated.values()}, {0})
            self.assertIn("explicit --retry-errors required", migrated[url]["error"])
            self.assertEqual(
                legacy.host_row(host)["robots_attempts"],
                ROBOTS_RETRY_EXHAUSTED,
            )

            self.assertIsNone(legacy.next_pending(2))
            self.assertEqual(legacy.reset_unavailable_robots(2), (1, 2))
            reset_rows = legacy.connection.execute(
                "SELECT state, attempts FROM urls WHERE host=?", (host,)
            ).fetchall()
            self.assertEqual(
                {(row["state"], row["attempts"]) for row in reset_rows},
                {("pending", 0)},
            )
        finally:
            legacy.close()

    def test_recovered_page_at_budget_becomes_terminal(self) -> None:
        host = "interrupted.cityu.edu.mo"
        url = f"https://{host}/page"
        self.allow_host_without_network(host)
        self.database.enqueue(url, 0, None, "test")
        self.database.connection.execute(
            """
            UPDATE urls
            SET state='fetching', attempts=2, error=NULL
            WHERE url=?
            """,
            (url,),
        )
        self.database.connection.commit()
        database_path = self.state_dir / "crawl.sqlite3"
        self.database.close()
        self.database = CrawlDatabase(database_path)

        self.assertEqual(self.page(url)["state"], "pending")
        self.assertEqual(self.database.exhaust_page_attempt_budget(2), 1)
        recovered = self.page(url)
        self.assertEqual(recovered["state"], "failed")
        self.assertIn("page retry budget exhausted (2/2)", recovered["error"])
        self.assertIsNone(self.database.next_pending(2))

    def test_robots_denial_does_not_count_as_page_attempt(self) -> None:
        host = "denied.cityu.edu.mo"
        url = f"https://{host}/private"
        self.database.ensure_host(host)
        crawler = self.crawler()
        parser = urllib.robotparser.RobotFileParser()
        parser.parse(["User-agent: *", "Disallow: /"])
        crawler.robots[host] = parser
        self.database.enqueue(url, 0, None, "test")

        crawler.fetch_one(self.database.next_pending(2))
        page = self.page(url)
        self.assertEqual(page["state"], "robots_denied")
        self.assertEqual(page["attempts"], 0)
        self.assertEqual(crawler.request_urls, [])

    def test_not_found_remains_a_visible_strict_completion_blocker(self) -> None:
        host = "missing.cityu.edu.mo"
        url = f"https://{host}/missing"
        self.allow_host_without_network(host)
        self.database.enqueue(url, 0, None, "test")
        crawler = self.crawler(page_status=404)

        crawler.fetch_one(self.database.next_pending(2))
        self.assertEqual(self.page(url)["state"], "not_found")
        self.assertIn(
            "not_found",
            {row["state"] for row in self.database.unresolved()},
        )

    def test_soft_404_legacy_scan_is_persistently_completed_once(self) -> None:
        host = "legacy-soft-404.cityu.edu.mo"
        url = f"https://{host}/missing"
        body = b"<html><title>404 error - page not found</title></html>"
        digest = "legacy-soft-404"
        relative_body_path = Path("bodies") / "legacy-soft-404.html"
        body_path = self.state_dir / relative_body_path
        body_path.parent.mkdir(parents=True, exist_ok=True)
        body_path.write_bytes(body)
        self.database.ensure_host(host)
        self.database.enqueue(url, 0, None, "test")
        self.database.mark_result(
            url,
            "fetched",
            FetchResult(
                requested_url=url,
                final_url=url,
                status=200,
                content_type="text/html",
                body=body,
                headers={},
            ),
            digest,
            str(relative_body_path),
            None,
        )

        self.assertEqual(
            reclassify_stored_soft_404(self.database, self.state_dir),
            1,
        )
        self.assertEqual(self.page(url)["state"], "soft_404")
        marker = self.database.connection.execute(
            "SELECT value FROM metadata WHERE key=?",
            (SOFT_404_RECLASSIFICATION_KEY,),
        ).fetchone()
        self.assertEqual(marker[0], "complete")

        self.database.connection.execute(
            "UPDATE urls SET state='fetched' WHERE url=?",
            (url,),
        )
        self.database.connection.commit()
        body_path.unlink()
        self.assertEqual(
            reclassify_stored_soft_404(self.database, self.state_dir),
            0,
        )
        self.assertEqual(self.page(url)["state"], "fetched")

    def test_report_exposes_terminal_coverage_states(self) -> None:
        host = "coverage-state.cityu.edu.mo"
        unavailable_url = f"https://{host}/robots-blocked"
        missing_url = f"https://{host}/missing"
        self.database.enqueue(unavailable_url, 0, None, "test")
        self.database.enqueue(missing_url, 0, None, "test")
        self.database.mark_result(
            unavailable_url,
            "robots_unavailable",
            result(unavailable_url, 0),
            None,
            None,
            "robots.txt retry budget exhausted",
        )
        self.database.mark_result(
            missing_url,
            "not_found",
            result(missing_url, 404),
            None,
            None,
            "HTTP 404",
        )

        report_path = self.state_dir / "report.json"
        write_report(self.database, report_path)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        host_report = next(item for item in report["hosts"] if item["host"] == host)
        self.assertEqual(host_report["robots_unavailable"], 1)
        self.assertEqual(host_report["not_found"], 1)
        self.assertFalse(report["complete"])


if __name__ == "__main__":
    unittest.main()
