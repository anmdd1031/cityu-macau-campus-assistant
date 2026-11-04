"""Local adapter benchmark: process startup versus a reused process, no LLM."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--rounds', type=int, default=10)
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error('--rounds must be positive')
    runtime = args.root.resolve() / 'skills/cityu-macau-campus-assistant/runtime'
    command = [sys.executable, str(runtime / 'host.py')]
    cases = [
        {'action': 'building', 'code': 'B1'},
        {'action': 'contact', 'name': '眭相傑'},
        {'action': 'tuition', 'course': '人工智能硕士', 'year': '2027/2028', 'audience': 'mainland'},
        {'action': 'recommend', 'query': '计算机视觉', 'level': 'master'},
    ]
    start = time.perf_counter()
    worker = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    def exchange(request):
        worker.stdin.write((json.dumps(request, ensure_ascii=False) + '\n').encode('utf-8'))
        worker.stdin.flush()
        response = worker.stdout.readline()
        if not response:
            raise RuntimeError('Worker exited before producing a response')
        result = json.loads(response)
        if result['status'] != 'answer':
            raise RuntimeError(result)
        return result
    rows = []
    try:
        exchange(cases[0])
        first_seconds = time.perf_counter() - start
        for request in cases:
            cold, warm = [], []
            for _ in range(args.rounds):
                payload = (json.dumps(request, ensure_ascii=False) + '\n').encode('utf-8')
                start = time.perf_counter()
                run = subprocess.run(command, input=payload, capture_output=True, check=True, timeout=15)
                cold.append(time.perf_counter() - start)
                expected = json.loads(run.stdout)
                start = time.perf_counter()
                actual = exchange(request)
                warm.append(time.perf_counter() - start)
                if actual != expected:
                    raise AssertionError('Persistent and fresh responses differ')
            rows.append({'request': request, 'fresh_process_seconds': cold,
                         'persistent_seconds': warm,
                         'fresh_median_ms': statistics.median(cold) * 1000,
                         'persistent_median_ms': statistics.median(warm) * 1000,
                         'responses_identical': True})
    finally:
        worker.stdin.close()
        worker.wait(timeout=15)
        worker.stdout.close()
    result = {'scope': 'Local structured request to complete JSON response; excludes classification, model, network and UI.',
              'rounds_per_case': args.rounds, 'persistent_first_request_seconds': first_seconds,
              'runtime_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in runtime.glob('*.py')},
              'results': rows}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for row in rows:
        print(row['request']['action'], round(row['fresh_median_ms'], 3), round(row['persistent_median_ms'], 3))


if __name__ == '__main__':
    main()
