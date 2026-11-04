"""Summarize existing local benchmark metadata; never initiates model calls."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    skill = args.root / 'skills/cityu-macau-campus-assistant'
    sys.path.insert(0, str(skill / 'runtime'))
    import query
    records = query.load_mentors()[0]
    rows = []
    # Only explicit benchmark directories; never recurse into crawling caches.
    phases = ['before', 'before-http', 'before-http-custom', 'after-http',
              'final-mentors', 'final-all', 'utf8-before', 'utf8-after',
              'utf8-before-retry', 'utf8-after-retry',
              'retained-agent-results', 'portable-results']
    for phase in phases:
        for path in sorted((args.cache / phase).glob('*-meta.json')):
            meta = json.loads(path.read_text(encoding='utf-8'))
            row = {key: meta.get(key) for key in
                   ('name', 'seconds', 'completed', 'returncode', 'command_count',
                    'tool_output_chars', 'usage', 'timeout')}
            row['phase'] = phase
            errors = meta.get('errors', [])
            row['errors'] = errors
            row['timing_eligible'] = bool(meta.get('completed')) and not errors
            if not row['timing_eligible']:
                row['exclusion'] = 'Incomplete response or transport/provider/quota error; not a clean timing sample.'
            answers = meta.get('answers', [])
            if 'mentors' in meta.get('name', '') and row['timing_eligible'] and answers:
                answer = answers[-1]
                selected = [r for r in records if r['email'] in answer]
                check = query.check_table(answer, selected)
                row['final_identity_valid'] = bool(selected) and check['valid']
                row['identity_issues'] = check['issues']
                row['identified_source_ids'] = [r['id'] for r in selected]
                row['final_answer'] = answer
                row['answer_sha256'] = hashlib.sha256(answer.encode('utf-8')).hexdigest()
                row['quality_eligible'] = row['final_identity_valid']
            rows.append(row)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        'scope': 'Serial live experiments, not randomized; timing eligibility is not answer correctness. Identity check excludes surrounding prose.',
        'results': rows}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Wrote {len(rows)} samples to {args.out}')


if __name__ == '__main__':
    main()
