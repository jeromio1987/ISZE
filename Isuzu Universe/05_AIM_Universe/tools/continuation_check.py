"""Repeat only the bounded continuation checks, with explicit synthetic inputs.

This is NOT the full acceptance suite and does not certify the retained UI,
production identity, restricted source values or an actual commercial decision.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def counts(text, rc):
    for line in reversed(text.splitlines()):
        if line.startswith('{'):
            try:
                data = json.loads(line)
                if 'pass' in data and 'fail' in data:
                    return {'pass': data['pass'], 'fail': data['fail'],
                            'skip': data.get('skip', data.get('skipped', 0))}
            except json.JSONDecodeError:
                pass
    passed, failed = re.search(r'^# pass (\d+)$', text, re.M), re.search(r'^# fail (\d+)$', text, re.M)
    if passed and failed:
        skipped = re.search(r'^# skipped (\d+)$', text, re.M)
        return {'pass': int(passed[1]), 'fail': int(failed[1]), 'skip': int(skipped[1]) if skipped else 0}
    ran = re.search(r'Ran (\d+) tests?', text)
    if ran and rc == 0:
        return {'pass': int(ran[1]), 'fail': 0, 'skip': 0}
    return None

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default=str(ROOT/'tests/accept/_out/continuation'),
                        help='Local evidence folder. No progress or acceptance record is overwritten.')
    args = parser.parse_args()
    node = shutil.which('node')
    if not node:
        print('Node.js is required; no tests were run.', file=sys.stderr)
        return 2
    out = Path(args.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    fixture = str(ROOT/'tests/fixtures/synthetic_payload.json')
    commands = [
        ('continuation_finance', [node, '--test', 'tests/continuation_finance.test.cjs']),
        ('continuation_build', [sys.executable, 'tests/continuation_build_test.py']),
        ('original_regression', [node, 'tests/run_tests.cjs', '--payload', fixture]),
        ('original_finance', [node, 'tests/fin_math.test.mjs', fixture]),
    ]
    env = dict(os.environ)
    for key in ['AIM_ENGINE_UNDER_TEST', 'AIM_BUILD_UNDER_TEST']:
        env.pop(key, None)
    results=[]
    for name, command in commands:
        try:
            run = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                                 text=True, timeout=120)
            text = run.stdout + '\nSTDERR\n' + run.stderr
            rc = run.returncode
        except subprocess.TimeoutExpired as exc:
            text = 'TIMEOUT: ' + str(exc)
            rc = 124
        (out/(name+'.log')).write_text(text, encoding='utf-8')
        result = {'check': name, 'command': command, 'returncode': rc,
                  'counts': counts(text, rc), 'log': name+'.log'}
        results.append(result)
        print(name + ': ' + ('PASS' if rc == 0 else 'FAIL') + ' ' + json.dumps(result['counts']))
    pin_files = list((ROOT/'src').rglob('*.js')) + [
        ROOT/'tools/build.py', ROOT/'tools/continuation_check.py',
        ROOT/'tests/continuation_finance.test.cjs', ROOT/'tests/continuation_build_test.py',
        ROOT/'tests/run_tests.cjs', ROOT/'tests/fin_math.test.mjs', Path(fixture)]
    report = {'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
              'scope': 'BOUNDED SYNTHETIC CHECKS ONLY; not UI or production acceptance',
              'known_exclusions': ['The restricted payload is not opened.',
                'The frozen shell and original assembled dashboard are not rebuilt.',
                'Restricted-case checks in original_finance must remain SKIP.',
                'The original UI suites still have fixture and retained-artifact gaps.'],
              'python': sys.version, 'node': subprocess.check_output([node,'--version'],text=True).strip(),
              'source_sha256': {str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in sorted(set(pin_files))},
              'checks':results}
    (out/'continuation_results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Evidence: ' + str(out/'continuation_results.json'))
    print('Passing this command does not approve a deployment, price or distributor-facing output.')
    return 0 if all(r['returncode']==0 for r in results) else 1

if __name__=='__main__':
    raise SystemExit(main())
