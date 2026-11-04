"""Persistent UTF-8 JSON-lines adapter for explicitly routed local queries.

Each input line produces one output line. No model calls, network or answer cache.
The host must classify the entire user request before selecting a direct action.
"""
import json
import sys

import query


ROUTES = {
    'building': (query.building, {'code': str}),
    'contact': (query.contact, {'name': str}),
    'tuition': (query.tuition, {'course': str, 'year': str, 'audience': str}),
    'recommend': (query.recommend, {'query': str, 'level': str}),
}


def dispatch(request):
    """Return an answer only for an explicit, fully supported structured request."""
    if not isinstance(request, dict):
        return {'status': 'fallback', 'reason': 'Expected a structured request object.'}
    action = request.get('action')
    if not isinstance(action, str) or action not in ROUTES:
        return {'status': 'fallback', 'reason': 'Unsupported action; use the normal Skill workflow.'}
    function, required = ROUTES[action]
    optional = {'limit': int} if action == 'recommend' else {}
    allowed = {'action'} | set(required) | set(optional)
    if set(request) - allowed or any(key not in request for key in required):
        return {'status': 'fallback', 'reason': 'Missing or extra fields; do not silently drop part of the request.'}
    args = {key: value for key, value in request.items() if key != 'action'}
    for key, kind in {**required, **optional}.items():
        if key in args and (type(args[key]) is not kind or (kind is str and not args[key].strip())):
            return {'status': 'fallback', 'reason': 'Invalid parameter: ' + key}
    if action == 'recommend' and args['level'] not in ('master', 'phd', 'research'):
        return {'status': 'fallback', 'reason': 'Unsupported study level.'}
    try:
        result = function(**args)
    except ValueError as error:
        return {'status': 'fallback', 'reason': str(error)}
    except (OSError, UnicodeError) as error:
        return {'status': 'error', 'reason': str(error)}
    # Keep source provenance and scope, but do not send already-consumed rules or
    # draft-check commands back to a host displaying the generated answer directly.
    result = {key: value for key, value in result.items()
              if key not in ('rules', 'check_command', 'check_input')}
    return {'status': 'answer', 'action': action, **result}


def main():
    for line in sys.stdin.buffer:
        try:
            request = json.loads(line.decode('utf-8-sig'))
            response = dispatch(request)
        except (ValueError, UnicodeError) as error:
            response = {'status': 'error', 'reason': str(error)}
        sys.stdout.buffer.write((json.dumps(response, ensure_ascii=False) + '\n').encode('utf-8'))
        sys.stdout.buffer.flush()


if __name__ == '__main__':
    main()
