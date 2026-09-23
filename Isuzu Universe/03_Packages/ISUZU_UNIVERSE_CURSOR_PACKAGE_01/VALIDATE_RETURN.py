#!/usr/bin/env python3
"""Read-only structural check for a Cursor R0 return package.

Usage: python VALIDATE_RETURN.py /path/to/R0_RETURN
A pass checks packaging only. It does not approve business evidence or close G0.
Uses only the Python standard library. No network, writes or application execution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

HEADINGS = [
    'Executive summary', 'Inspected baseline', 'Original paper and critique',
    'Protected feature baseline', 'Source packs and data eligibility',
    'Code reuse and PRISM', 'Executed checks', 'Backlog disposition',
    'Open questions and next work order',
]
REQUIRED = ['R0_REVIEW.md', 'SOURCE_MANIFEST.json', 'TASK_DISPOSITION.json', 'MANIFEST.json']
INSPECTION = {'evidence_returned', 'blocked', 'not_run'}
DISPOSITION = {'already_satisfied', 'required', 'blocked', 'conditional', 'not_relevant', 'not_reviewed'}


def validate(root: Path) -> list[str]:
    """Return validation errors without modifying the directory."""
    errors: list[str] = []
    root = root.resolve()
    if not root.is_dir():
        return ['Return directory does not exist.']
    for name in REQUIRED:
        if not (root / name).is_file():
            errors.append('Missing required file: ' + name)
    if errors:
        return errors
    try:
        report = (root / 'R0_REVIEW.md').read_text(encoding='utf-8-sig')
        sm = json.loads((root / 'SOURCE_MANIFEST.json').read_text(encoding='utf-8-sig'))
        td = json.loads((root / 'TASK_DISPOSITION.json').read_text(encoding='utf-8-sig'))
        manifest = json.loads((root / 'MANIFEST.json').read_text(encoding='utf-8-sig'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return ['Unreadable report or JSON: ' + str(exc)]
    if any(not isinstance(x, dict) for x in [sm, td, manifest]):
        return ['JSON top-level values must be objects.']
    for name, data in [('SOURCE_MANIFEST', sm), ('TASK_DISPOSITION', td), ('MANIFEST', manifest)]:
        if data.get('work_order') != 'R0':
            errors.append(name + ': work_order must be R0.')
    pos = -1
    for heading in HEADINGS:
        found = report.find('## ' + heading, pos + 1)
        if found < 0:
            errors.append('Missing or out-of-order report heading: ' + heading)
        else:
            pos = found
    placeholders = ['[actual timestamp]', '[actual revision / snapshot]', '[Ten complete, unnumbered lines.']
    if any(marker in report for marker in placeholders):
        errors.append('Report still contains supplied template placeholders.')
    if not isinstance(sm.get('sources'), list) or not isinstance(sm.get('missing_inputs'), list):
        errors.append('SOURCE_MANIFEST: sources and missing_inputs must be lists.')
    elif not sm['sources'] and not sm['missing_inputs']:
        errors.append('SOURCE_MANIFEST: provide inspected sources or explicit missing inputs.')
    if not sm.get('inspected_at'):
        errors.append('SOURCE_MANIFEST: actual inspected_at is required.')
    source_keys = {
        'source_id','path','kind','version','sha256','modified_at','commercial_level',
        'row_grain','period_start','period_end','reporting_clock','row_count',
        'schema','value_basis','supersedes','status','limitations','evidence_refs',
    }
    for i, source in enumerate(sm.get('sources', [])):
        if not isinstance(source, dict):
            errors.append(f'Source {i}: expected an object.')
            continue
        missing = source_keys - source.keys()
        if missing:
            errors.append(f'Source {i}: missing fields: ' + ', '.join(sorted(missing)))
        digest = source.get('sha256')
        if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r'[a-fA-F0-9]{64}', digest)):
            errors.append(f'Source {i}: invalid SHA-256; use null with an explanation if unknown.')
    task_rows = td.get('tasks')
    if not isinstance(task_rows, list):
        errors.append('TASK_DISPOSITION: tasks must be a list.')
        task_rows = []
    seen: set[str] = set()
    for i, task in enumerate(task_rows):
        if not isinstance(task, dict):
            errors.append(f'Task {i}: expected an object.')
            continue
        task_id = task.get('id', '')
        if not isinstance(task_id, str) or not re.fullmatch(r'(C(?:0[1-9]|[1-3][0-9]|4[0-2])|A(?:0[1-9]|1[0-9]|2[0-4]))', task_id):
            errors.append(f'Task {i}: invalid task ID.')
            continue
        if task_id in seen:
            errors.append('Duplicate task ID: ' + task_id)
        seen.add(task_id)
        if task.get('inspection_status') not in INSPECTION:
            errors.append(task_id + ': invalid inspection_status.')
        if task.get('product_disposition') not in DISPOSITION:
            errors.append(task_id + ': invalid product_disposition.')
        if not isinstance(task.get('evidence_refs'), list):
            errors.append(task_id + ': evidence_refs must be a list.')
        elif (task.get('inspection_status') == 'evidence_returned' or task.get('product_disposition') == 'already_satisfied') and not task['evidence_refs']:
            errors.append(task_id + ': evidence is required for this disposition.')
        if not isinstance(task.get('finding'), str) or not task['finding'].strip():
            errors.append(task_id + ': finding or explicit limitation is required.')
    for task_id in [f'C{i:02d}' for i in range(1, 8)]:
        if task_id not in seen:
            errors.append('Missing selected task: ' + task_id)
    entries = manifest.get('files')
    if not isinstance(entries, list) or not entries:
        errors.append('MANIFEST: non-empty files list is required.')
        entries = []
    listed: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            errors.append('MANIFEST: file entries must be objects.')
            continue
        rel = entry.get('path')
        if not isinstance(rel, str) or not rel:
            errors.append('MANIFEST: file path must be a non-empty string.')
            continue
        rel_path = Path(rel)
        if rel_path.is_absolute() or '..' in rel_path.parts or '\\' in rel or re.match(r'^[A-Za-z]:', rel):
            errors.append('MANIFEST: unsafe path: ' + rel)
            continue
        target = (root / rel_path).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            errors.append('MANIFEST: path escapes return directory: ' + rel)
            continue
        if not target.is_file():
            errors.append('MANIFEST: file not found: ' + rel)
            continue
        if rel in listed:
            errors.append('MANIFEST: duplicate file: ' + rel)
        listed.add(rel)
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != str(entry.get('sha256', '')).lower():
            errors.append('MANIFEST: hash mismatch: ' + rel)
        if not entry.get('purpose'):
            errors.append('MANIFEST: missing purpose: ' + rel)
    actual_files = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p.name != 'MANIFEST.json'}
    for unlisted in sorted(actual_files - listed):
        errors.append('MANIFEST: unlisted return file: ' + unlisted)
    privacy = manifest.get('privacy_review')
    if not isinstance(privacy, dict) or privacy.get('status') != 'completed' or not privacy.get('notes'):
        errors.append('MANIFEST: completed privacy review with notes is required before sharing.')
    if not manifest.get('inspected_build'):
        errors.append('MANIFEST: record the inspected build or explain why its identity is unknown.')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('return_directory', type=Path)
    args = parser.parse_args()
    try:
        errors = validate(args.return_directory)
    except (OSError, TypeError, ValueError) as exc:
        print('STRUCTURAL CHECK FAILED: ' + str(exc), file=sys.stderr)
        return 2
    if errors:
        print('STRUCTURAL CHECK FAILED')
        for error in errors:
            print('- ' + error)
        return 1
    print('STRUCTURAL CHECK PASSED. Business evidence, permissions and G0 still require review.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
