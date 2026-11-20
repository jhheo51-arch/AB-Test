"""R01 local HTTP regression; no real Hermes/model/credential access.
Run: python tests/verify_issue_allowlist.py
The CLI sentinel never launches a child process; it raises OSError for path
probes and returns one explicitly labelled fixed fixture for metadata checks.
"""
from pathlib import Path
import copy
import importlib.util
import json
import os
import re
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('r01_server', ROOT / 'server.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

BASE = {
    'analysis_status': 'limited', 'overall_decision': 'hold',
    'segments': [{'id': 'G1', 'decision': 'hold'}, {'id': 'G2', 'decision': 'not_tested'}],
    'interaction': 'not_tested', 'guardrail': 'not_assessed',
    'design_user_confirmed': True, 'adjustment': 'holm', 'issues': []
}

def request(server, body):
    url = 'http://127.0.0.1:' + str(server.server_port)
    req = urllib.request.Request(url + '/api/explain', data=json.dumps(body).encode(),
                                 headers={'Content-Type': 'application/json', 'Origin': url})
    # Bypass any configured HTTP proxy, even for loopback.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=5) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def run():
    evidence = {'requirement': 'R01', 'real_model_calls': 0,
                'network_scope': 'ephemeral 127.0.0.1 HTTP only; proxy disabled',
                'credential_access': 'none', 'cases': []}
    source = (ROOT / 'engine.js').read_text(encoding='utf-8')
    allowlist = json.loads((ROOT / 'engine-issue-codes.json').read_text(encoding='utf-8'))
    literal_codes = set(re.findall(r"(?:issue|fail)\(\s*'([A-Z][A-Z0-9_]*)'", source))
    # Audit every constructor first argument, including functions' declarations.
    arguments = re.findall(r'\b(?:issue|fail)\(\s*([^,\n]+)', source)
    dynamic = [arg.strip() for arg in arguments if not arg.strip().startswith("'")]
    assert dynamic == ['code', 'code', "e.code || 'PARSE_ERROR'", 'e.code'], dynamic
    expected = literal_codes | {'PARSE_ERROR'}
    assert set(allowlist['codes']) == expected == set(bridge.ISSUE_CODES)
    assert allowlist['engine_version'] == bridge.EXPECTED_ENGINE_VERSION == '0.2.0'
    assert re.search(r"const VERSION = '0\.2\.0';", source)
    evidence['allowlist'] = allowlist
    evidence['allowlist_count'] = len(expected)
    evidence['constructor_audit'] = {
        'literal_code_count': len(literal_codes),
        'nonliteral_first_arguments': dynamic,
        'review': [
            'issue(code) and fail(code) are constructor declarations, not additional constants.',
            "prepare catches parseTable fail codes via e.code, with PARSE_ERROR fallback.",
            'analyze copies prepared.issues e.code: arbitrary caller-supplied values are possible; server rejects any value outside this allowlist, not silently filters.'
        ]
    }
    # Version and malformed allowlist failures are exercised using scratch fixtures.
    with tempfile.TemporaryDirectory(prefix='r01-', dir=os.environ['TMPDIR']) as tmp:
        root = Path(tmp)
        (root / 'engine.js').write_text(source, encoding='utf-8')
        for name, changed in [
            ('engine_version_mismatch', source.replace("const VERSION = '0.2.0';", "const VERSION = '9.9.9';")),
            ('missing_engine_version', source.replace("const VERSION = '0.2.0';", '')),
        ]:
            (root / 'engine.js').write_text(changed, encoding='utf-8')
            (root / 'engine-issue-codes.json').write_text(json.dumps(allowlist), encoding='utf-8')
            try:
                bridge.load_issue_codes(root)
            except ValueError as error:
                evidence['cases'].append({'case': name, 'rejected': True, 'message': str(error)})
            else:
                raise AssertionError(name)
        (root / 'engine.js').write_text(source, encoding='utf-8')
        for name, mutate in [
            ('allowlist_version_mismatch', lambda x: x.update(engine_version='9.9.9')),
            ('allowlist_extra_key', lambda x: x.update(extra=True)),
            ('allowlist_duplicate_code', lambda x: x['codes'].append(x['codes'][0])),
            ('allowlist_nonstring_code', lambda x: x['codes'].append({})),
            ('allowlist_boolean_schema', lambda x: x.update(schema_version=True)),
        ]:
            altered = copy.deepcopy(allowlist)
            mutate(altered)
            (root / 'engine-issue-codes.json').write_text(json.dumps(altered), encoding='utf-8')
            try:
                bridge.load_issue_codes(root)
            except ValueError as error:
                evidence['cases'].append({'case': name, 'rejected': True, 'message': str(error)})
            else:
                raise AssertionError(name)

    bad = []
    for name, issues in [
        ('unknown_code', ['UNREGISTERED_ISSUE']),
        ('identifier_like_code', ['CUSTOMER_ALICE_12345']),
        ('mixed_known_unknown', ['EMPTY_INPUT', 'CUSTOMER_ALICE_12345']),
        ('code_with_email', ['alice@example.test']),
        ('lowercase_code', ['empty_input']), ('whitespace_code', ['EMPTY_INPUT ']),
        ('newline_code', ['EMPTY_INPUT\n']), ('empty_code', ['']),
        ('object_code', [{}]), ('list_code', [[]]), ('numeric_code', [123]),
        ('null_code', [None]), ('boolean_code', [True]),
        ('issues_not_list', 'EMPTY_INPUT'), ('too_many_issues', ['EMPTY_INPUT'] * 31),
    ]:
        facts = copy.deepcopy(BASE)
        facts['issues'] = issues
        bad.append((name, {'confirmed': True, 'facts': facts}))
    for name, mutate in [
        ('extra_facts_key', lambda x: x.update(raw_data='private')),
        ('missing_facts_key', lambda x: x.pop('guardrail')),
        ('identifier_segment', lambda x: x['segments'][0].update(id='CUSTOMER_ALICE')),
        ('extra_segment_key', lambda x: x['segments'][0].update(label='private')),
        ('wrong_state', lambda x: x.update(analysis_status='customer_name')),
        ('malformed_state_type', lambda x: x.update(analysis_status=[])),
        ('nonboolean_confirmation', lambda x: x.update(design_user_confirmed=1)),
    ]:
        facts = copy.deepcopy(BASE)
        mutate(facts)
        bad.append((name, {'confirmed': True, 'facts': facts}))
    bad.extend([
        ('extra_envelope_key', {'confirmed': True, 'facts': BASE, 'raw_data': 'private'}),
        ('missing_envelope_key', {'facts': BASE}),
        ('unconfirmed_envelope', {'confirmed': False, 'facts': BASE}),
    ])
    calls = []
    fixture_mode = {'enabled': False}
    def sentinel(argv, **kwargs):
        calls.append({'argv0': argv[0], 'input': kwargs['input']})
        if fixture_mode['enabled']:
            # Explicit test fixture, not a model response or connectivity evidence.
            return bridge.subprocess.CompletedProcess(argv, 0, stdout=json.dumps({
                'summary': '검증용 고정 문장입니다.', 'cautions': ['실제 모델 출력이 아닙니다.'],
                'next_steps': ['원래 판정을 확인하세요.'], 'evidence_refs': ['overall', 'issues']
            }, ensure_ascii=False), stderr='')
        raise OSError('R01_TEST_CLI_SENTINEL: no subprocess executed')

    with patch.object(bridge.subprocess, 'run', side_effect=sentinel):
        for mode, hermes in [('hermes_none', None), ('cli_sentinel', 'R01_TEST_SENTINEL_NOT_AN_EXECUTABLE')]:
            server = bridge.AppServer(('127.0.0.1', 0), bridge.Handler, hermes, 'test-no-credentials')
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                for name, body in bad:
                    before = len(calls)
                    status, payload = request(server, body)
                    assert status == 400 and payload['error'] == 'PAYLOAD_REJECTED', (name, status, payload)
                    assert len(calls) == before, name
                    evidence['cases'].append({'mode': mode, 'case': name, 'http_status': status,
                                              'response': payload, 'cli_calls_delta': len(calls) - before})
                for code in [None, *sorted(expected)]:
                    facts = copy.deepcopy(BASE)
                    facts['issues'] = [] if code is None else [code]
                    assert bridge.validate_facts(facts) == facts
                    before = len(calls)
                    status, payload = request(server, {'confirmed': True, 'facts': facts})
                    want = 503 if hermes is None else 502
                    assert status == want, (code, status, payload)
                    assert len(calls) - before == (0 if hermes is None else 1)
                    if hermes is not None:
                        sent_facts = json.loads(calls[-1]['input'].split('사실 상태 JSON:\n', 1)[1])
                        assert sent_facts == facts  # No silent filtering or widening.
                        assert payload['error'] == 'LLM_RESPONSE_REJECTED'
                        assert 'R01_TEST_CLI_SENTINEL' in payload['message']
                    else:
                        assert payload['error'] == 'LLM_UNAVAILABLE'
                    evidence['cases'].append({'mode': mode, 'case': 'valid_code', 'code': code,
                                              'http_status': status, 'response': payload,
                                              'validation_accepted': True, 'cli_calls_delta': len(calls) - before})
                if hermes is not None:
                    fixture_mode['enabled'] = True
                    before = len(calls)
                    status, payload = request(server, {'confirmed': True, 'facts': BASE})
                    assert status == 200 and len(calls) - before == 1
                    assert 'raw_data_sent' not in payload
                    assert payload['facts_validation'] == bridge.facts_validation_metadata()
                    assert set(payload['sent_fields']) == set(BASE)
                    evidence['cases'].append({'mode': 'explicit_cli_response_fixture',
                        'case': 'success_response_metadata', 'http_status': status,
                        'fixture_not_actual_model_output': True, 'response': payload,
                        'cli_calls_delta': len(calls) - before})
                    fixture_mode['enabled'] = False
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)

    metadata = bridge.facts_validation_metadata()
    assert set(metadata['checked_fields']) == set(BASE)
    assert metadata['issue_code_allowlist_count'] == len(expected)
    assert 'not engine provenance' in metadata['scope']
    assert 'raw_data_sent' not in (ROOT / 'server.py').read_text(encoding='utf-8')
    evidence['response_metadata'] = metadata
    evidence['cli_sentinel_invocations'] = len(calls)
    evidence['cli_sentinel_behavior'] = 'Raises OSError for validation-path probes; one explicitly labelled fixed response fixture exercises success metadata. No child process or real model is executed.'
    evidence['case_count'] = len(evidence['cases'])
    evidence['passed'] = True
    (ROOT / 'R01_VERIFICATION.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'passed': True, 'allowlist_count': len(expected), 'case_count': len(evidence['cases']),
                      'cli_sentinel_invocations': len(calls), 'evidence': str(ROOT / 'R01_VERIFICATION.json')}, ensure_ascii=False))

if __name__ == '__main__':
    run()
