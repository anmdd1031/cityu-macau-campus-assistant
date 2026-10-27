import importlib.util
from pathlib import Path
import sys
import subprocess
import json
import unittest

RUNTIME = Path(__file__).resolve().parents[1] / "skills/cityu-macau-campus-assistant/runtime"
sys.path.insert(0, str(RUNTIME))
spec = importlib.util.spec_from_file_location("query", RUNTIME / "query.py")
query = importlib.util.module_from_spec(spec)
spec.loader.exec_module(query)


class QueryTests(unittest.TestCase):
    def test_source_records_and_exact_name(self):
        records, digest, context = query.load_mentors()
        self.assertEqual(len(records), 58)
        target = query.pick(records, "36")[0]
        self.assertIn("眭相傑", target["name"])
        self.assertEqual(target["email"], "xjsui@cityu.edu.mo")
        self.assertEqual(target["url"], "https://fds.cityu.edu.mo/members/390")
        self.assertEqual(len(digest), 64)
        self.assertIn("2026-07-13", context)

    def test_render_check_catches_real_typo_and_identity_swap(self):
        selected = query.pick(query.load_mentors()[0], "8,36")
        table = query.render(selected)
        self.assertTrue(query.check_table(table, selected)["valid"])
        for altered in [table.replace("眭相傑", "睭相傑"),
                        table.replace("xjsui@cityu.edu.mo", "jiagu@cityu.edu.mo"),
                        table.replace("members/390", "members/338"),
                        table + "\n" + table.splitlines()[-1], ""]:
            self.assertFalse(query.check_table(altered, selected)["valid"])

    def test_deterministic_keyword_pool_and_qualification(self):
        first = query.mentors("计算机视觉", "master")
        second = query.mentors("CV", "master")
        self.assertEqual(first["records"], second["records"])
        self.assertEqual(first["count"], len(first["records"]))
        self.assertTrue(all("硕士生导师" in r["qualification"] for r in first["records"]))
        self.assertIn("36", [r["id"] for r in first["records"]])
        self.assertNotIn("6", [r["id"] for r in first["records"]])

    def test_ids_reject_unknown_and_duplicate(self):
        records = query.load_mentors()[0]
        for ids in ["8,8", "999", ""]:
            with self.assertRaises(ValueError):
                query.pick(records, ids)

    def test_cli_checks_utf8_stdin_and_stale_source(self):
        records, digest, _ = query.load_mentors()
        table = query.render(query.pick(records, "36"))
        command = [sys.executable, str(RUNTIME / "query.py"), "check", "--ids", "36", "--sha256", digest]
        for text, expected in [(table, 0), (table.replace("眭相傑", "睭相傑"), 2)]:
            result = subprocess.run(command, input=text.encode("utf-8"), capture_output=True)
            self.assertEqual(result.returncode, expected)
            self.assertEqual(json.loads(result.stdout.decode("utf-8"))["valid"], expected == 0)
        result = subprocess.run(command[:-1] + ["0" * 64], input=table.encode("utf-8"), capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("source changed", json.loads(result.stdout.decode("utf-8"))["error"])

    def test_bundles_keep_year_and_sources(self):
        for topic, selectors in query.BUNDLES.items():
            packet = query.read_packet(query.ROOT, selectors)
            text = "\n".join(e["text"] for f in packet["files"] for e in f["excerpts"])
            self.assertIn("https://", text)
            if topic == "iusd-phd-2026":
                self.assertIn("第一或第二署名单位", text)
            if topic == "fds-fees-mainland-2027":
                self.assertIn("125,000", text)


if __name__ == "__main__":
    unittest.main()
