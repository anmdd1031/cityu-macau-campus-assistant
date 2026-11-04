import importlib.util
from pathlib import Path
import sys
import subprocess
import json
import unittest
import html

RUNTIME = Path(__file__).resolve().parents[1] / "skills/cityu-macau-campus-assistant/runtime"
sys.path.insert(0, str(RUNTIME))
spec = importlib.util.spec_from_file_location("query", RUNTIME / "query.py")
query = importlib.util.module_from_spec(spec)
spec.loader.exec_module(query)


class QueryTests(unittest.TestCase):
    def test_portable_names_are_lossless_and_still_reject_typos(self):
        records = query.load_mentors()[0]
        selected = query.pick(records, "8,36,50")
        canonical = query.render(selected)
        transported = query.portable_names({"verbatim_table": canonical})["verbatim_table"]
        self.assertEqual(html.unescape(transported), canonical)
        self.assertIn("&#x772D;", transported)
        self.assertTrue(query.check_table(transported, selected)["valid"])
        self.assertFalse(query.check_table(transported.replace("&#x772D;", "&#x776D;"), selected)["valid"])
        self.assertFalse(query.check_table(transported.replace("&#x772D;", "&amp;#x772D;"), selected)["valid"])
        for r in records:
            encoded = query.portable_names({"name": r["name"]})["name"]
            self.assertEqual(html.unescape(encoded), r["name"])

    def test_direct_tuition_does_not_cross_cohorts(self):
        result = query.tuition("人工智能硕士", "2027/2028", "mainland")
        for fact in ["125,000", "HKD", "学年", "2026-10-01", "list-26/257", "标签本身不说明审批状态"]:
            self.assertIn(fact, result["answer"])
        self.assertEqual(len(result["sources"]), 2)
        self.assertIn("105,000", query.tuition("计算机科学博士", "2027/2028", "mainland")["answer"])
        for args in [("人工智能硕士", "2026/2027", "mainland"), ("人工智能硕士", "2027/2028", "local"),
                     ("人工智能博士", "2027/2028", "mainland"), ("人工智能", "2027/2028", "mainland")]:
            with self.assertRaises(ValueError):
                query.tuition(*args)

    def test_contact_exact_identity_and_unknown(self):
        answer = query.contact("眭相傑")["answer"]
        self.assertIn("xjsui@cityu.edu.mo", answer)
        self.assertIn("members/390", answer)
        for name in ["", "眭", "睭相傑", "不存在"]:
            with self.assertRaises(ValueError):
                query.contact(name)

    def test_building_keeps_scope_and_source(self):
        answer = query.building("b1")["answer"]
        for fact in ["第一座", "不能解释为地下一层", "2026-10-06", "map.png", "不是金龙"]:
            self.assertIn(fact, answer)
        for code in ["", "B2", "地图标识"]:
            with self.assertRaises(ValueError):
                query.building(code)

    def test_recommend_preserves_candidates_and_identity(self):
        pool = query.mentors("计算机视觉", "master")
        result = query.recommend("计算机视觉", "master")
        self.assertEqual(result["count"], len(pool["records"]))
        self.assertEqual(len(result["selected_ids"]), 5)
        selected = query.pick(query.load_mentors()[0], ",".join(result["selected_ids"]))
        self.assertTrue(query.check_table(result["answer"], selected)["valid"])
        for r in selected:
            self.assertIn(r["direction"], result["answer"])
            self.assertIn("硕士生导师", r["qualification"])
        all_result = query.recommend("CV", "master", 0)
        self.assertEqual(set(all_result["selected_ids"]), {r["id"] for r in pool["records"]})
        self.assertIn("未展开 0 人", all_result["answer"])
        self.assertEqual(query.recommend("unmatched_xyz", "master")["count"], 0)
        with self.assertRaises(ValueError):
            query.recommend("CV", "master", -1)

    def test_selection_and_host_finalize(self):
        selection = query.mentors("CV", "master", "selection")
        self.assertNotIn("verbatim_table", selection)
        self.assertNotIn("email", selection["records"][0])
        result = query.finalize("36", selection["source_sha256"], {"36": "caller supplied explanation"})
        self.assertTrue(result["valid"])
        self.assertIn("眭相傑", result["verbatim_table"])
        for digest, reasons in [("0"*64, {"36": "reason"}), (selection["source_sha256"], {}),
                                (selection["source_sha256"], {"36": ""})]:
            with self.assertRaises(ValueError):
                query.finalize("36", digest, reasons)

    def test_evidence_is_lossless(self):
        for topic, selectors in query.BUNDLES.items():
            compact = query.evidence_text(topic)
            for f in query.read_packet(query.ROOT, selectors)["files"]:
                self.assertIn(f["sha256"], compact)
                for excerpt in f["excerpts"]:
                    self.assertIn(excerpt["text"], compact)

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
        self.assertIn(first["source_sha256"], first["check_template"])
        self.assertTrue(first["identity_codepoints"]["36"].startswith("U+772D"))
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
