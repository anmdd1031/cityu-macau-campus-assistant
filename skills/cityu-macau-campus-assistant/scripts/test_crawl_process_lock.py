#!/usr/bin/env python3
"""Offline checks for the machine-wide official-site crawl guard."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import crawl_official_sites as crawler


class FakeDatabase:
    def __init__(self, last_started_at: float) -> None:
        self.last_started_at = last_started_at
        self.recorded: list[float] = []

    def last_request_started_at(self) -> float:
        return self.last_started_at

    def record_request_started_at(self, value: float) -> None:
        self.recorded.append(value)


class FakeGlobalLock:
    def __init__(self, last_started_at: float) -> None:
        self.metadata = {"last_request_started_at": last_started_at}

    def update_metadata(self, **values: object) -> None:
        self.metadata.update(values)


class CrawlProcessLockTests(unittest.TestCase):
    def test_different_state_directories_share_global_lock_path(self) -> None:
        state_a = Path("state-a")
        state_b = Path("state-b")
        lock_a = crawler.crawl_process_lock_paths(state_a)
        lock_b = crawler.crawl_process_lock_paths(state_b)

        self.assertEqual(lock_a[0], lock_b[0])
        self.assertNotEqual(lock_a[1], lock_b[1])

    def test_seed_discovery_ignores_urls_in_scripts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cityu-seed-source-test-") as temp:
            root = Path(temp)
            (root / "references").mkdir()
            (root / "scripts").mkdir()
            (root / "references" / "source.md").write_text(
                "Official source: https://fds.cityu.edu.mo/source\n",
                encoding="utf-8",
            )
            (root / "scripts" / "test.py").write_text(
                'url = "https://fds.cityu.edu.mo/test-fixture"\n',
                encoding="utf-8",
            )

            discovered = list(crawler.iter_skill_urls(root))

        self.assertEqual(discovered, ["https://fds.cityu.edu.mo/source"])

    def test_reference_refresh_follows_citations_and_formal_documents_only(self) -> None:
        cited = {"https://fds.cityu.edu.mo/faculty/photo.jpg"}

        self.assertTrue(
            crawler.should_follow_reference_refresh_link(
                "https://fds.cityu.edu.mo/faculty/photo.jpg", cited
            )
        )
        self.assertTrue(
            crawler.should_follow_reference_refresh_link(
                "https://fds.cityu.edu.mo/files/handbook.pdf", cited
            )
        )
        self.assertTrue(
            crawler.should_follow_reference_refresh_link(
                "https://fds.cityu.edu.mo/files/fees.xlsx", cited
            )
        )
        self.assertFalse(
            crawler.should_follow_reference_refresh_link(
                "https://fds.cityu.edu.mo/uploads_thumb/list/photo_1000X1000.jpg",
                cited,
            )
        )
        self.assertFalse(
            crawler.should_follow_reference_refresh_link(
                "https://fds.cityu.edu.mo/en/another-page", cited
            )
        )

    def test_explicit_refresh_urls_are_repeatable_and_normalized(self) -> None:
        with patch.object(
            crawler.sys,
            "argv",
            [
                "crawl_official_sites.py",
                "--refresh-url",
                "https://fds.cityu.edu.mo/current",
                "--refresh-url",
                "https://registry.cityu.edu.mo/calendar",
            ],
        ):
            args = crawler.parse_args()

        self.assertEqual(
            args.refresh_url,
            [
                "https://fds.cityu.edu.mo/current",
                "https://registry.cityu.edu.mo/calendar",
            ],
        )

    def test_reference_refresh_queue_ignores_unrelated_full_crawl_pending(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cityu-reference-target-test-") as temp:
            database = crawler.CrawlDatabase(Path(temp) / "crawl.sqlite3")
            direct = "https://fds.cityu.edu.mo/faculty"
            unrelated = "https://fof.cityu.edu.mo/uploads_thumb/logo.jpg"
            document = "https://fds.cityu.edu.mo/files/handbook.pdf"
            database.enqueue(direct, 0, None, "reference-refresh")
            database.enqueue(unrelated, 1, direct, "img:src")
            database.set_reference_refresh_targets({direct})

            first = database.next_pending(max_attempts=2)
            self.assertEqual(first["url"], direct)
            database.connection.execute(
                "UPDATE urls SET state='fetched' WHERE url=?", (direct,)
            )
            database.connection.commit()
            database.add_reference_refresh_target(document)
            database.enqueue(document, 1, direct, "a:href")

            second = database.next_pending(max_attempts=2)
            states = {
                row["url"]: row["state"]
                for row in database.connection.execute(
                    "SELECT url,state FROM urls"
                ).fetchall()
            }
            database.close()

        self.assertEqual(second["url"], document)
        self.assertEqual(states[unrelated], "pending")

    def test_second_process_is_blocked_across_state_directories(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cityu-crawl-lock-test-") as temp:
            root = Path(temp)
            state_a = root / "state-a"
            state_b = root / "state-b"
            global_path = root / "global.lock"
            state_a.mkdir()
            state_b.mkdir()
            child_code = (
                "import sys, time\n"
                "from pathlib import Path\n"
                "from crawl_official_sites import crawl_process_locks\n"
                "with crawl_process_locks("
                "Path(sys.argv[1]), global_lock_path=Path(sys.argv[2])):\n"
                "    print('LOCKED', flush=True)\n"
                "    time.sleep(30)\n"
            )
            process = subprocess.Popen(
                [sys.executable, "-c", child_code, str(state_a), str(global_path)],
                cwd=Path(__file__).resolve().parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            ready = threading.Event()
            output: list[str] = []

            def read_ready_line() -> None:
                assert process.stdout is not None
                output.append(process.stdout.readline())
                ready.set()

            reader = threading.Thread(target=read_ready_line, daemon=True)
            reader.start()
            try:
                self.assertTrue(ready.wait(10), "lock holder did not start")
                self.assertEqual(output, ["LOCKED\n"])
                with self.assertRaisesRegex(RuntimeError, "process is active"):
                    with crawler.crawl_process_locks(
                        state_b, global_lock_path=global_path
                    ):
                        self.fail("second process acquired the global lock")
            finally:
                process.terminate()
                _, stderr = process.communicate(timeout=10)
                reader.join(timeout=1)
            self.assertEqual(stderr, "")

    def test_rate_limiter_keeps_global_cooldown_across_state_databases(self) -> None:
        database = FakeDatabase(last_started_at=90.0)
        global_lock = FakeGlobalLock(last_started_at=100.0)
        limiter = crawler.RateLimiter(database, 1.2, global_lock)

        with (
            patch.object(crawler.time, "time", side_effect=[100.5, 101.2]),
            patch.object(crawler.time, "sleep") as sleep,
        ):
            limiter.wait()

        sleep.assert_called_once()
        self.assertAlmostEqual(sleep.call_args.args[0], 0.7)
        self.assertEqual(database.recorded, [101.2])
        self.assertEqual(global_lock.metadata["last_request_started_at"], 101.2)

    def test_reference_refresh_preserves_robots_blocks_and_cooldowns(self) -> None:
        with tempfile.TemporaryDirectory(prefix="cityu-reference-refresh-test-") as temp:
            database = crawler.CrawlDatabase(Path(temp) / "crawl.sqlite3")
            urls = {
                "fetched": "https://fds.cityu.edu.mo/source",
                "deferred": "https://fob.cityu.edu.mo/deferred",
                "robots": "https://fitm.cityu.edu.mo/robots-blocked",
                "forbidden": "https://fh.cityu.edu.mo/forbidden",
                "new": "https://registry.cityu.edu.mo/new-source",
            }
            for url in urls.values():
                database.enqueue(url, 0, None, "test")
            database.connection.execute(
                "UPDATE urls SET state='fetched' WHERE url=?", (urls["fetched"],)
            )
            database.connection.execute(
                """UPDATE urls SET state='deferred', next_attempt_at=?, error='HTTP 429'
                   WHERE url=?""",
                (crawler.time.time() + 3600, urls["deferred"]),
            )
            database.connection.execute(
                "UPDATE urls SET state='robots_unavailable' WHERE url=?",
                (urls["robots"],),
            )
            database.connection.execute(
                "UPDATE urls SET state='failed', http_status=403 WHERE url=?",
                (urls["forbidden"],),
            )
            database.connection.commit()

            counts = database.refresh_reference_urls(urls.values())
            states = {
                row["url"]: row["state"]
                for row in database.connection.execute(
                    "SELECT url,state FROM urls"
                ).fetchall()
            }
            database.close()

        self.assertEqual(counts["unique"], 5)
        self.assertEqual(counts["requeued"], 1)
        self.assertEqual(counts["already_pending"], 1)
        self.assertEqual(counts["protected"], 3)
        self.assertEqual(states[urls["fetched"]], "pending")
        self.assertEqual(states[urls["new"]], "pending")
        self.assertEqual(states[urls["deferred"]], "deferred")
        self.assertEqual(states[urls["robots"]], "robots_unavailable")
        self.assertEqual(states[urls["forbidden"]], "failed")


if __name__ == "__main__":
    unittest.main()
