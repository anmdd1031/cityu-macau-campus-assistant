"""Offline tests for evidence-preserving legacy HTTP classification."""
import tempfile
import unittest
import io
from pathlib import Path
from unittest.mock import patch

from crawl_official_sites import CrawlDatabase, normalize_url, read_bounded_response


class LegacyErrorTests(unittest.TestCase):
    def test_response_size_limit(self):
        self.assertEqual(read_bounded_response(io.BytesIO(b"abcdef"), 4, 60), b"abcd")

    def test_slow_drip_deadline(self):
        with patch('crawl_official_sites.time.monotonic', side_effect=[0, 1, 61]):
            with self.assertRaisesRegex(TimeoutError, 'transfer budget'):
                read_bounded_response(io.BytesIO(b"partial"), 100, 60)

    def test_alias_requires_fetched_target_and_keeps_old_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            db = CrawlDatabase(Path(directory) / "crawl.sqlite3")
            try:
                old = "https://test.cityu.edu.mo/file(1).pdf"
                canonical = normalize_url(old)
                self.assertNotEqual(old, canonical)
                db.enqueue(old, 0, None, "fixture")
                db.enqueue(canonical, 0, None, "fixture")
                db.connection.execute(
                    "UPDATE urls SET state='failed', http_status=0, error='network error' WHERE url=?", (old,)
                )
                db.connection.commit()
                self.assertEqual(db.reconcile_recovered_aliases(), 0)
                db.connection.execute(
                    "UPDATE urls SET state='fetched', sha256='digest', body_path='body.bin' WHERE url=?", (canonical,)
                )
                db.connection.commit()
                self.assertEqual(db.reconcile_recovered_aliases(), 1)
                self.assertEqual(db.reconcile_recovered_aliases(), 0)
                row = db.connection.execute("SELECT state,error FROM urls WHERE url=?", (old,)).fetchone()
                self.assertEqual(row['state'], 'skipped')
                self.assertEqual(row['error'], f'canonicalized to {canonical}')
                self.assertEqual(db.connection.execute("SELECT COUNT(*) FROM events WHERE event_type='recovered_alias'").fetchone()[0], 1)
            finally:
                db.close()

    def test_terminal_errors_preserve_evidence_and_are_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            db = CrawlDatabase(Path(directory) / "crawl.sqlite3")
            try:
                for status in (0, 400, 403, 404, 410, 429, 500):
                    url = f"https://test.cityu.edu.mo/{status}"
                    db.enqueue(url, 0, None, "fixture")
                    db.connection.execute(
                        "UPDATE urls SET state='failed', http_status=?, error='original', "
                        "body_path='evidence.bin', sha256='digest', attempts=2 WHERE url=?",
                        (status, url),
                    )
                db.connection.commit()
                self.assertEqual(db.reconcile_legacy_http_errors(), 2)
                self.assertEqual(db.reconcile_legacy_http_errors(), 0)
                for row in db.connection.execute("SELECT * FROM urls"):
                    self.assertEqual(row["state"], "not_found" if row["http_status"] in (404, 410) else "failed")
                    self.assertEqual(row["error"], "original")
                    self.assertEqual(row["body_path"], "evidence.bin")
                    self.assertEqual(row["sha256"], "digest")
                    self.assertEqual(row["attempts"], 2)
            finally:
                db.close()


if __name__ == "__main__":
    unittest.main()
