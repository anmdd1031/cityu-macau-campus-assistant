import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

RUNTIME = Path(__file__).resolve().parents[1] / 'skills/cityu-macau-campus-assistant/runtime'
sys.path.insert(0, str(RUNTIME))
import host


class HostTests(unittest.TestCase):
    def test_direct_answers_preserve_source_result(self):
        cases = [
            {'action': 'building', 'code': 'B1'},
            {'action': 'contact', 'name': '眭相傑'},
            {'action': 'tuition', 'course': '人工智能硕士', 'year': '2027/2028', 'audience': 'mainland'},
            {'action': 'recommend', 'query': '计算机视觉', 'level': 'master'},
        ]
        for request in cases:
            result = host.dispatch(request)
            direct = host.ROUTES[request['action']][0](**{k: v for k, v in request.items() if k != 'action'})
            self.assertEqual(result['status'], 'answer')
            self.assertEqual(result['answer'], direct['answer'])
            self.assertEqual(result.get('sources'), direct.get('sources'))
            self.assertEqual(result.get('source_sha256'), direct.get('source_sha256'))

    def test_unsupported_or_partial_requests_do_not_get_partial_answers(self):
        for request in [None, [], {}, {'action': []},
                        {'action': 'building'}, {'action': 'building', 'code': 'B1', 'question': '还有学费呢'},
                        {'action': 'building', 'code': 1},
                        {'action': 'tuition', 'course': '人工智能硕士', 'year': '2026/2027', 'audience': 'mainland'},
                        {'action': 'recommend', 'query': '视觉', 'level': 'unknown'},
                        {'action': 'recommend', 'query': '视觉', 'level': 'master', 'limit': True}]:
            result = host.dispatch(request)
            self.assertEqual(result['status'], 'fallback', request)
            self.assertNotIn('answer', result)

    def test_source_changes_visible_in_same_process(self):
        original = host.query.ROOT
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            text = (original / 'campus_map.md').read_text(encoding='utf-8-sig')
            source = root / 'campus_map.md'
            source.write_text(text, encoding='utf-8')
            with patch.object(host.query, 'ROOT', root):
                first = host.dispatch({'action': 'building', 'code': 'B1'})
                source.write_text(text.replace('第一座', '测试楼宇'), encoding='utf-8')
                second = host.dispatch({'action': 'building', 'code': 'B1'})
                self.assertIn('测试楼宇', second['answer'])
                self.assertNotEqual(first['source_sha256'], second['source_sha256'])

    def test_bad_line_does_not_stop_following_requests(self):
        payload = b'{broken\n' + json.dumps({'action': 'contact', 'name': '眭相傑'}, ensure_ascii=False).encode('utf-8') + b'\n'
        result = subprocess.run([sys.executable, str(RUNTIME / 'host.py')], input=payload,
                                capture_output=True, check=True, timeout=10)
        rows = [json.loads(line) for line in result.stdout.decode('utf-8').splitlines()]
        self.assertEqual(rows[0]['status'], 'error')
        self.assertEqual(rows[1]['status'], 'answer')
        self.assertIn('眭相傑', rows[1]['answer'])


if __name__ == '__main__':
    unittest.main()
