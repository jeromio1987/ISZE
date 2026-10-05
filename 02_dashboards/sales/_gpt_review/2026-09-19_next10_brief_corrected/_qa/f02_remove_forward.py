"""F02 payload surgery — remove the 18 dead 'forward' (2030 ceiling) blocks.

Evidence they are unreachable (all checked on the pre-edit bytes):
  - '"forward"' as a property name: 18 occurrences, all inside the __LEAK__ object literal.
  - '.forward' (dot access):            0
  - ['forward'] / ["forward"]:          0
  - 'ceiling_2030':                     only as the key name itself, no read
  - export/download/csv/blob/print:     0
The live ceiling the page uses is the separate `ceiling` object (ceiling_total_eur 55,253,312),
which is NOT touched here.

Deletes per block: the 7-line block, and the trailing comma on the preceding line.
Backup is written before anything changes.
"""
import re, shutil, sys

P = r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\sales\_gpt_review\2026-09-19_next10_brief_corrected\02_ISZE_Leakage_Cockpit.html"
BAK = P + ".bak_pre_defectfix_20260919"

with open(P, encoding="utf-8", newline="") as f:
    t = f.read()
before_bytes = len(t.encode("utf-8"))

assert '"forward": {' in t
assert 'ceiling_2030_eur' in t
assert t.count('"forward": {') == 18, t.count('"forward": {')
assert t.count('ceiling_2030_eur') == 18
assert re.search(r'\.forward\b', t) is None
assert '["forward"]' not in t and "['forward']" not in t

lines = t.split("\r\n")
assert len(lines) > 1
out = []
i = 0
removed = 0
while i < len(lines):
    line = lines[i]
    if line.strip() == '"forward": {':
        # the block: forward:{ , year, ceiling_2030_eur, vs_2024_pct, cum_ceiling_eur, modelled, }
        blk = lines[i:i + 7]
        assert blk[1].strip().startswith('"year": 2030'), blk[1]
        assert blk[2].strip().startswith('"ceiling_2030_eur"'), blk[2]
        assert blk[3].strip().startswith('"vs_2024_pct"'), blk[3]
        assert blk[4].strip().startswith('"cum_ceiling_eur"'), blk[4]
        assert blk[5].strip().startswith('"modelled": true'), blk[5]
        assert blk[6].strip() == "}", blk[6]
        # strip the comma that the removed property left on the previous emitted line
        prev = out[-1]
        assert prev.rstrip().endswith("},"), repr(prev)
        out[-1] = prev.rstrip()[:-1]
        i += 7
        removed += 1
        continue
    out.append(line)
    i += 1

print("blocks removed:", removed)
new = "\r\n".join(out)
after_bytes = len(new.encode("utf-8"))
print("bytes before/after:", before_bytes, after_bytes, "delta", after_bytes - before_bytes)
assert '"forward"' not in new
assert "ceiling_2030_eur" not in new

with open(P, "w", encoding="utf-8", newline="") as f:
    f.write(new)
print("written (backup already exists at", BAK, ")")
