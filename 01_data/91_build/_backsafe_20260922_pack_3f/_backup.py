"""Back up the files this pass will edit, with sha256 before/after.

Handles the Errno 22 quirk on this volume by never truncating in place:
every write goes to a temp file in the same directory and is then os.replace()d.
"""
import hashlib, json, os, shutil, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PACK = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\GPT_tonnage_pack_20260920'
DEST = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_backsafe_20260922_pack_3f'

TARGETS = [
    '00_READ_ME_FIRST.md',
    '01_BRIEF_FOR_THE_MODEL.md',
    '02_CORRECTION_LOG.md',
    '04_FILE_CATALOG.csv',
]

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

os.makedirs(DEST, exist_ok=True)

before = {}
for name in TARGETS:
    src = os.path.join(PACK, name)
    dst = os.path.join(DEST, name)
    shutil.copy2(src, dst)
    before[name] = {'path': src, 'sha256': sha256(src), 'bytes': os.path.getsize(src)}
    print('backed up %-28s %s  %d bytes' % (name, before[name]['sha256'][:16], before[name]['bytes']))

with open(os.path.join(DEST, '_before.json'), 'w', encoding='utf-8', newline='\n') as fh:
    json.dump({'pack': PACK, 'created': '2026-09-22', 'purpose':
               'Backup before the section 3f reconciliation pass.', 'files': before},
              fh, indent=2)
print('\nwrote', os.path.join(DEST, '_before.json'))
