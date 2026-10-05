"""One more precision fix to 14f: the cross-reference counts DO reproduce, under an
undocumented definition. Say that, rather than saying they cannot be reproduced."""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PACK = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\GPT_tonnage_pack_20260920'
READ = os.path.join(PACK, '00_READ_ME_FIRST.md')

with open(READ, 'rb') as fh:
    t = fh.read().decode('utf-8').replace('\r\n', '\n')

old = """**What could not be sourced, and has therefore been removed rather than replaced.** The scoping CSV's `route1_decode` column for clutch booster and urea filter, and the route hits of "3" for blower filter and "1" for urea filter, cannot be reproduced from the files they claim to read. The corrected table in §3f shows the reproducible measurement and names the discrepancy rather than carrying a figure forward. **The probe's behaviour cannot be stated as "first route only"** — it reads both the EPC editions and the cross-reference — and the text now says what it actually does."""

new = """**What could not be sourced, and has therefore been removed rather than replaced.** The scoping CSV's `route1_decode` column does not reproduce for clutch booster and urea filter, so no figure is carried forward from it; §3f prints the reproducible measurement and names the discrepancy. The cross-reference route counts **do** reproduce — as a match on `genuine_pn` alone, `1 / 3 / 1 / 28 / 2` — but that definition appears nowhere on disk, while the workspace's own family file reads the same source with `bvp_pn` included and gets `1 / 6 / 2 / 37 / 3`. **Both readings are now printed side by side rather than one being silently preferred.** And **the probe's behaviour cannot be stated as "first route only"** — it reads both the EPC editions and the cross-reference — so the text now says what it actually does."""

n = t.count(old)
assert n == 1, 'anchor matched %d times' % n
t = t.replace(old, new)
print('  [ok] 14f: cross-reference counts reproduce under an undocumented definition')

tmp = READ + '.__tmp_3f__'
with open(tmp, 'wb') as fh:
    fh.write(t.replace('\n', '\r\n').encode('utf-8'))
os.replace(tmp, READ)
print('  wrote 00_READ_ME_FIRST.md', os.path.getsize(READ), 'bytes')
