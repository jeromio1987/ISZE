#!/usr/bin/env python3
"""Validate an R1 return package's structure and hashes, not business correctness.

Usage: python VALIDATE_R1_RETURN.py PATH_TO_R1_RETURN
The script reads only. It does not modify, execute or upload returned files.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

REQUIRED = {
    'R1_REVIEW.md', 'MANIFEST.json', 'SOURCE_MANIFEST.json',
    'TASK_DISPOSITION.json', 'DATA_CHECKS.json',
    'EVIDENCE/HOST_AND_REUSE.md', 'EVIDENCE/RECONCILIATION.md',
    'EVIDENCE/IDENTITY_AND_COVERAGE.md', 'EVIDENCE/TONNAGE_V2_DELTA.md',
    'EVIDENCE/COMMANDS_AND_RESULTS.md', 'EVIDENCE/INTERACTION_TESTS.md',
    'EVIDENCE/PRIVACY_AND_CHANGE_REVIEW.md', 'PROTOTYPE/index.html',
    'PROTOTYPE/context_contract.json',
}
STATUSES = {'pass', 'fail', 'blocked', 'not_run', 'not_applicable'}
CHECK_FIELDS = {'id', 'scope', 'status', 'expected', 'actual', 'command',
                'input_hashes', 'evidence_refs'}


def validate(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    root = root.resolve()
    if not root.is_dir():
        return {'structural_pass': False, 'errors': ['Return directory not found.']}
    actual: set[str] = set()
    for p in root.rglob('*'):
        if p.is_symlink():
            errors.append(f'Symlink is not allowed: {p.relative_to(root).as_posix()}')
        elif p.is_file():
            actual.add(p.relative_to(root).as_posix())
    for name in sorted(REQUIRED - actual):
        errors.append(f'Missing required file: {name}')

    def read_json(name: str) -> dict[str, Any] | None:
        if name not in actual:
            return None
        try:
            obj = json.loads((root/name).read_text(encoding='utf-8-sig'))
            if not isinstance(obj, dict):
                raise ValueError('Top level must be an object.')
            return obj
        except (ValueError, OSError) as exc:
            errors.append(f'{name}: {exc}')
            return None

    manifest = read_json('MANIFEST.json')
    listed: set[str] = set()
    if manifest is not None:
        entries = manifest.get('files')
        if not isinstance(entries, list):
            errors.append('MANIFEST.json must contain a files array.')
            entries = []
        for entry in entries:
            if not isinstance(entry, dict):
                errors.append('Manifest entry must be an object.')
                continue
            name, expected_hash = entry.get('path'), entry.get('sha256')
            if not isinstance(name, str) or not name:
                errors.append('Manifest entry has invalid path.')
                continue
            posix = PurePosixPath(name)
            if posix.is_absolute() or '..' in posix.parts or '\\' in name or ':' in name:
                errors.append(f'Unsafe/non-relative manifest path: {name}')
                continue
            if name in listed:
                errors.append(f'Duplicate manifest entry: {name}')
            listed.add(name)
            if name == 'MANIFEST.json':
                errors.append('Manifest must not hash itself.')
                continue
            path = root/name
            if not path.resolve().is_relative_to(root):
                errors.append(f'Manifest path escapes return root: {name}')
                continue
            if name not in actual:
                errors.append(f'Manifest file missing: {name}')
                continue
            if not isinstance(expected_hash, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_hash):
                errors.append(f'Invalid SHA-256: {name}')
            elif hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
                errors.append(f'Hash mismatch: {name}')
        for name in sorted(actual - listed - {'MANIFEST.json'}):
            errors.append(f'Unmanifested file: {name}')
        for field in ('redactions', 'missing_items'):
            if not isinstance(manifest.get(field), list):
                errors.append(f'MANIFEST.json requires a {field} array (may be empty).')

    source = read_json('SOURCE_MANIFEST.json')
    if source is not None and not isinstance(source.get('sources'), list):
        errors.append('SOURCE_MANIFEST.json requires a sources array.')
    disposition = read_json('TASK_DISPOSITION.json')
    if disposition is not None and not isinstance(disposition.get('tasks'), list):
        errors.append('TASK_DISPOSITION.json requires a tasks array.')
    read_json('PROTOTYPE/context_contract.json')
    checks = read_json('DATA_CHECKS.json')
    counts = {s: 0 for s in sorted(STATUSES)}
    if checks is not None:
        items = checks.get('tests')
        if not isinstance(items, list) or not items:
            errors.append('DATA_CHECKS.json requires a non-empty tests array.')
            items = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f'Test {i} is not an object.')
                continue
            missing = CHECK_FIELDS - item.keys()
            if missing:
                errors.append(f'Test {i} missing fields: {sorted(missing)}')
            status = item.get('status')
            if status not in STATUSES:
                errors.append(f'Test {i} has invalid status: {status!r}')
            else:
                counts[status] += 1
                if status != 'pass' and not item.get('reason'):
                    errors.append(f'Test {i} needs a reason for status {status}.')
            if not isinstance(item.get('evidence_refs'), list):
                errors.append(f'Test {i} evidence_refs must be an array.')
            if not isinstance(item.get('input_hashes'), (dict, list)):
                errors.append(f'Test {i} input_hashes must be an object or array.')
    if counts['fail'] or counts['blocked'] or counts['not_run']:
        warnings.append('Unresolved test outcomes are present. They are not structural errors, but prevent automatic business acceptance.')
    warnings.append('This script does not certify data correctness, mapping approval, permissions, privacy, browser behaviour or release readiness.')
    return {'structural_pass': not errors, 'files_found': len(actual),
            'files_hashed_in_manifest': len(listed), 'reported_test_status_counts': counts,
            'errors': errors, 'warnings': warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('return_directory', type=Path)
    args = parser.parse_args()
    result = validate(args.return_directory)
    print(json.dumps(result, indent=2))
    return 0 if result['structural_pass'] else 1


if __name__ == '__main__':
    sys.exit(main())
