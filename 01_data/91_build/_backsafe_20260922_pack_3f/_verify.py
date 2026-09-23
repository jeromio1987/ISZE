"""Verify the 3f corrections landed, the catalog parses, and the pack count is 20."""
import csv, hashlib, io, os, sys, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PACK = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\GPT_tonnage_pack_20260920'
DEST = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_pack_3f'
EDITED = ['00_READ_ME_FIRST.md', '01_BRIEF_FOR_THE_MODEL.md', '02_CORRECTION_LOG.md', '04_FILE_CATALOG.csv']

def sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for c in iter(lambda: fh.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

print('=== 1. content files vs the five v4 backups ===')
entries = sorted(os.listdir(PACK))
dirs = [e for e in entries if os.path.isdir(os.path.join(PACK, e))]
baks = [e for e in entries if e.endswith('.bak_before_v4_20260922')]
content = []
for d in dirs:
    for f in sorted(os.listdir(os.path.join(PACK, d))):
        if os.path.isfile(os.path.join(PACK, d, f)):
            content.append(d + '/' + f)
for e in entries:
    if os.path.isfile(os.path.join(PACK, e)) and not e.endswith('.bak_before_v4_20260922'):
        content.append(e)
print('  subdirectories      :', len(dirs), dirs)
print('  v4 backup files     :', len(baks))
print('  content files       :', len(content))
print('  total files in folder:', len(content) + len(baks))
assert len(content) == 20, 'content file count is not 20'
assert len(baks) == 5
for c in sorted(content):
    print('     ', c)

print('\n=== 2. 04_FILE_CATALOG.csv parses ===')
with open(os.path.join(PACK, '04_FILE_CATALOG.csv'), encoding='utf-8-sig', newline='') as fh:
    rows = list(csv.DictReader(fh))
print('  columns:', list(rows[0].keys()))
print('  data rows:', len(rows))
assert len(rows) == 20
self_row = [r for r in rows if r['folder'] == '04_FILE_CATALOG.csv'][0]
print('  the row for this catalog, key by key:')
for k, v in self_row.items():
    print('     %-12s %s' % (k, (v[:110] + '...') if v else v))
caveat = self_row['use_for']
print('  file-count claim now reads: %s' % caveat)
assert '25 files' in caveat and '20 content files' in caveat
# pre-existing property, not introduced here: the five doc rows carry 6 fields against 7 headers
raw_rows = list(csv.reader(open(os.path.join(PACK, '04_FILE_CATALOG.csv'), encoding='utf-8-sig', newline='')))
short = [i for i, r in enumerate(raw_rows[1:], 1) if len(r) != len(raw_rows[0])]
print('  rows with a different field count than the header:', short, '(5 doc rows — pre-existing)')

print('\n=== 3. the corrected cells are present ===')
read = open(os.path.join(PACK, '00_READ_ME_FIRST.md'), encoding='utf-8').read()
brief = open(os.path.join(PACK, '01_BRIEF_FOR_THE_MODEL.md'), encoding='utf-8').read()
log = open(os.path.join(PACK, '02_CORRECTION_LOG.md'), encoding='utf-8').read()
checks = [
    ('read-me 3f heading', read, 'almost no tonnage candidates'),
    ('read-me: old 3f heading gone', read, '### 3f. Five service families have no tonnage candidates at all'),
    ('read-me: largest not second', read, 'Brake rotor is the largest service family by euro, not the second'),
    ('read-me: 85.6%', read, '85.6%'),
    ('read-me: 3,815,676', read, '3,815,676'),
    ('read-me: 641,572', read, '641,572'),
    ('read-me: 14f section', read, '### 14f.'),
    ('read-me: probe reads both', read, 'reads the EPC editions **and**'),
    ('read-me: 12 rows blower', read, '| blower filter | 7 | 1,349,479 | 12 | 7 |'),
    ('read-me: 5 rows urea', read, '| urea filter | 7 | 134,108 | 5 | 2 |'),
    ('read-me: 3a families row', read, 'almost no** band candidates'),
    ('brief: corrected', brief, '**[corrected 2026-09-22 evening]**'),
    ('brief: largest', brief, 'the **largest** family by euro and not the second'),
    ('log: dated section', log, 'Later still on 2026-09-22 — §3f reconciled against the source files'),
    ('log: 3f-2', log, '### 3f-2. "92 of 109" — tested, and refuted as the family verdict'),
    ('log: 3f-3', log, '### 3f-3. "The family carries exactly one vehicle string" — refuted'),
    ('log: 3f-4', log, '### 3f-4. "The second-largest family by euro" — wrong'),
    ('log: 3f-5', log, '### 3f-5. The probe claim — qualified, not confirmed'),
    ('log: 3f-6', log, '### 3f-6. What could not be sourced'),
    ('log: scoping result corrected', log, 'partly wrong, and corrected the same evening'),
]
bad = 0
for label, text, needle in checks:
    present = needle in text
    if label.startswith('read-me: old '):
        if present:
            print('  [FAIL] %s (still present)' % label); bad += 1
        else:
            print('  [ok]   %s (removed)' % label)
    else:
        if present:
            print('  [ok]   %s' % label)
        else:
            print('  [FAIL] %s' % label); bad += 1
assert bad == 0, '%d check(s) failed' % bad

print('\n=== 4. withdrawal of the old figures actually happened ===')
gone = [
    ('read-me: "92 of 109" old bullet', read, '**92 of 109: "no vehicle reference"**'),
    ('read-me: "second-largest service family"', read, 'second-largest service family in the service list by euro'),
    ('brief: "second-largest family by euro"', brief, 'the second-largest family by euro'),
    ('brief: "92 of its 109" unqualified', brief, 'For brake rotor this is a dead end rather than a fixable join: 92 of its 109'),
    ('log: old "no tonnage data"', log, 'Brake rotor has no tonnage data — 109 part numbers, EUR 4.46M, the second-largest'),
]
for label, text, needle in gone:
    if needle in text:
        print('  [FAIL] %s still present' % label); bad += 1
    else:
        print('  [ok]   %s removed' % label)
assert bad == 0

print('\n=== 5. hashes after ===')
after = {}
for name in EDITED:
    fp = os.path.join(PACK, name)
    after[name] = {'path': fp, 'sha256': sha256(fp), 'bytes': os.path.getsize(fp)}
    print('  %-28s %s  %d bytes' % (name, after[name]['sha256'][:16], after[name]['bytes']))

with open(os.path.join(DEST, '_after.json'), 'w', encoding='utf-8', newline='\n') as fh:
    json.dump({'pack': PACK, 'created': '2026-09-22',
               'purpose': 'Hashes after the section 3f reconciliation pass.',
               'files': after}, fh, indent=2)
print('\n  wrote _after.json')

print('\n=== 6. before vs after differ on all four ===')
before = json.load(open(os.path.join(DEST, '_before.json'), encoding='utf-8'))['files']
for name in EDITED:
    same = before[name]['sha256'] == after[name]['sha256']
    print('  %-28s %s' % (name, 'UNCHANGED (bad)' if same else 'changed'))
    assert not same or name == '03_EVIDENCE_OF_CORRECTION.md'

print('\nAll verification checks passed.')
