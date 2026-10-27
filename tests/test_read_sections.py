import importlib.util
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/cityu-macau-campus-assistant/runtime/read_sections.py"
spec = importlib.util.spec_from_file_location("retrieval", SCRIPT)
retrieval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(retrieval)


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "sample.md").write_text(
            "# 文档\n版本：2026\n## 3. 学费\n仅适用内地生\n"
            "### 3.2 当届\n| 币种 | 金额 |\n|---|---|\n| HKD | 125000 |\n"
            "注：每学年\n```md\n## 假标题\n```\n"
            "### 3.20 旧届\n2025 规则\n## 4. 来源\nhttps://example.com\n",
            encoding="utf-8")

    def test_scope_table_and_fence_preserved(self):
        packet = retrieval.read_packet(self.root, ["sample.md::3.2"])
        text = "\n".join(e["text"] for e in packet["files"][0]["excerpts"])
        self.assertIn("版本：2026", text)
        self.assertIn("仅适用内地生", text)
        self.assertIn("| HKD | 125000 |\n注：每学年", text)
        self.assertIn("## 假标题", text)
        self.assertNotIn("2025 规则", text)
        self.assertNotIn("假标题", [h["title"] for h in retrieval.catalog(self.root, "sample.md")["sections"]])

    def test_batch_deduplicates_and_keeps_sources(self):
        packet = retrieval.read_packet(self.root, ["sample.md::3.2", "sample.md::3.2", "sample.md::4."])
        text = "\n".join(e["text"] for e in packet["files"][0]["excerpts"])
        self.assertEqual(text.count("125000"), 1)
        self.assertIn("https://example.com", text)

    def test_no_truncation(self):
        with self.assertRaisesRegex(ValueError, "No text was truncated"):
            retrieval.read_packet(self.root, ["sample.md::*"], max_chars=10)

    def test_ambiguous_sections_fail(self):
        with (self.root / "sample.md").open("a", encoding="utf-8") as file:
            file.write("\n## 3.2 重复编号\n")
        with self.assertRaisesRegex(ValueError, "exactly once"):
            retrieval.read_packet(self.root, ["sample.md::3.2"])

    def test_changes_visible_without_rebuilding(self):
        before = retrieval.catalog(self.root, "sample.md")["sha256"]
        with (self.root / "sample.md").open("a", encoding="utf-8") as file:
            file.write("\n## 5. 新内容\n")
        after = retrieval.catalog(self.root, "sample.md")
        self.assertNotEqual(before, after["sha256"])
        self.assertEqual(after["sections"][-1]["title"], "5. 新内容")

    def test_duplicate_titles_resolve_by_path_and_id(self):
        (self.root / "duplicate.md").write_text(
            "# 学院\n## 甲教师\n### 科研项目\n甲项目\n"
            "## 乙教师\n### 科研项目\n乙项目\n", encoding="utf-8")
        catalog = retrieval.catalog(self.root, "duplicate.md")
        sections = [h for h in catalog["sections"] if h["title"] == "科研项目"]
        self.assertNotEqual(sections[0]["id"], sections[1]["id"])
        for heading, expected, excluded in [(sections[0], "甲项目", "乙项目"), (sections[1], "乙项目", "甲项目")]:
            for selector in [heading["id"], "path:" + json.dumps(heading["path"], ensure_ascii=False)]:
                packet = retrieval.read_packet(self.root, ["duplicate.md::" + selector])
                text = "\n".join(e["text"] for e in packet["files"][0]["excerpts"])
                self.assertIn(expected, text)
                self.assertNotIn(excluded, text)
        with self.assertRaises(retrieval.RetrievalError) as caught:
            retrieval.read_packet(self.root, ["duplicate.md::科研项目"])
        self.assertEqual(len(caught.exception.details["candidates"]), 2)

    def test_identical_paths_still_have_distinct_ids(self):
        (self.root / "duplicate.md").write_text("# 同名\n甲\n# 同名\n乙\n", encoding="utf-8")
        headings = retrieval.catalog(self.root, "duplicate.md")["sections"]
        self.assertEqual(headings[0]["path"], headings[1]["path"])
        for heading in headings:
            packet = retrieval.read_packet(self.root, ["duplicate.md::" + heading["id"]])
            self.assertEqual(packet["files"][0]["excerpts"][0]["start_line"], heading["line"])

    def test_stale_id_rejected_even_with_whole_file(self):
        sid = retrieval.catalog(self.root, "sample.md")["sections"][0]["id"]
        with (self.root / "sample.md").open("a", encoding="utf-8") as file:
            file.write("\nnew version\n")
        for selectors in [["sample.md::" + sid], ["sample.md::*", "sample.md::" + sid]]:
            with self.assertRaises(retrieval.RetrievalError) as caught:
                retrieval.read_packet(self.root, selectors)
            self.assertEqual(caught.exception.details["kind"], "stale_id")

    def test_over_limit_candidates_are_readable_and_exact_size(self):
        for selector in ["sample.md::*", "sample.md::文档"]:
            with self.assertRaises(retrieval.RetrievalError) as caught:
                retrieval.read_packet(self.root, [selector], max_chars=80)
            candidates = caught.exception.details["candidates"]
            self.assertTrue(candidates)
            for candidate in candidates:
                packet = retrieval.read_packet(self.root, [candidate["selector"]], max_chars=10000)
                self.assertEqual(candidate["text_chars"], packet["text_chars"])
                self.assertEqual(candidate["fits_budget"], packet["text_chars"] <= 80)

    def test_bad_id_path_and_budget(self):
        for selector in ["@bad", "path:wrong", "path:123"]:
            with self.assertRaises(retrieval.RetrievalError):
                retrieval.read_packet(self.root, ["sample.md::" + selector])
        with self.assertRaises(ValueError):
            retrieval.read_packet(self.root, ["sample.md::*"], max_chars=0)

    def test_cli_over_limit_returns_actionable_json(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "read", "--select",
                                 "freshman.md::*"], capture_output=True)
        packet = json.loads(result.stdout.decode("utf-8"))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(packet["kind"], "over_limit")
        self.assertTrue(packet["candidates"])
        self.assertNotIn("files", packet)

    def test_all_corpus_duplicate_titles_read_by_id(self):
        checked = 0
        for path in retrieval.ROOT.rglob("*.md"):
            name = path.relative_to(retrieval.ROOT).as_posix()
            if name in retrieval.DISABLED:
                continue
            headings = retrieval.catalog(retrieval.ROOT, name)["sections"]
            counts = Counter(h["title"] for h in headings)
            lines = path.read_text(encoding="utf-8-sig").splitlines()
            for heading in headings:
                if counts[heading["title"]] <= 1:
                    continue
                packet = retrieval.read_packet(retrieval.ROOT, [name + "::" + heading["id"]])
                spans = packet["files"][0]["excerpts"]
                self.assertTrue(any(e["start_line"] <= heading["line"] <= heading["end"] <= e["end_line"] for e in spans))
                for excerpt in spans:
                    self.assertEqual(excerpt["text"], "\n".join(lines[excerpt["start_line"]-1:excerpt["end_line"]]))
                checked += 1
        self.assertGreater(checked, 0)

    def test_over_limit_batch_retains_leaf_candidates(self):
        for name in ["one.md", "two.md"]:
            (self.root / name).write_text("# Leaf\n" + "x" * 40, encoding="utf-8")
        with self.assertRaises(retrieval.RetrievalError) as caught:
            retrieval.read_packet(self.root, ["one.md::Leaf", "two.md::Leaf"], max_chars=60)
        candidates = caught.exception.details["candidates"]
        self.assertEqual(len(candidates), 2)
        for candidate in candidates:
            self.assertTrue(candidate["fits_budget"])
            retrieval.read_packet(self.root, [candidate["selector"]], max_chars=60)

    def test_disabled_and_outside_paths(self):
        for name in ["../outside.md", "mentors/fds_papers.md", "sample.txt"]:
            with self.assertRaises(ValueError):
                retrieval.document(self.root, name)

    def test_utf8_and_ascii_round_trip_real_names(self):
        packets = []
        for flags in [[], ["--ascii"]]:
            result = subprocess.run([sys.executable, str(SCRIPT), *flags, "read", "--select",
                                     "mentors/fds_mentors.md::*"], capture_output=True, check=True)
            packets.append(json.loads(result.stdout.decode("utf-8")))
        self.assertEqual(packets[0], packets[1])
        self.assertIn("眭相傑", packets[0]["files"][0]["excerpts"][0]["text"])

    def test_real_2026_rules_and_sources(self):
        packet = retrieval.read_packet(retrieval.ROOT, ["iusd.md::3.8"])
        text = "\n".join(e["text"] for e in packet["files"][0]["excerpts"])
        self.assertIn("第一或第二署名单位", text)
        self.assertIn("2026 级博士生", text)
        self.assertNotIn("### 3.6", text)


if __name__ == "__main__":
    unittest.main()
