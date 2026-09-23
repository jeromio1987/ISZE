"""Three precision fixes to the corrected section 3f, after reading it back."""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

PACK = r'C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\GPT_tonnage_pack_20260920'
READ = os.path.join(PACK, '00_READ_ME_FIRST.md')

with open(READ, 'rb') as fh:
    raw = fh.read()
t = raw.decode('utf-8').replace('\r\n', '\n')


def sub(text, old, new, label):
    n = text.count(old)
    assert n == 1, 'anchor %r matched %d times' % (label, n)
    print('  [ok] %s' % label)
    return text.replace(old, new)


# 1. "sixteen a band" -> sixteen a reference, seven a band
t = sub(t,
"""But the EPC route gives the other sixteen a band: `3.5t_N35|5.5t_N50_N55|7.5t_N50_N62_N75` on five part numbers,""",
"""But the EPC route gives sixteen of them an EPC reference, and seven of those carry a band: `3.5t_N35|5.5t_N50_N55|7.5t_N50_N62_N75` on five part numbers,""",
'brake rotor: sixteen references, seven bands')

# 2. the commercial paragraph contradicted itself — one of the seven IS band-exclusive
t = sub(t,
"""The tonnage view as it stands covers filters and clutch. Of the brake families it holds seven rotor part numbers under a blank label and no band-exclusive part at all.""",
"""The tonnage view as it stands covers filters and clutch. Of the brake families it holds seven rotor part numbers under a blank label — one of them band-exclusive, and six pooled across all three rungs — and nothing else.""",
'commercial paragraph: one of the seven is exclusive')

# 3. the route table column said "with a band" but carried a row count
t = sub(t,
"""| Family | Part numbers | Euro | With a band in `15_band_by_part_number.csv` | With a cross-reference string, `genuine_pn` only / incl. `bvp_pn` | Rows in the family file | Of those, under this family |
|---|---:|---:|---|---:|---:|---:|
| brake rotor | 109 | 4,457,248 | 8 · **7 of them banded, EUR 1,061,419** on that file's own basis | 1 / 1 | 109 | 109 |""",
"""| Family | Part numbers | Euro | Rows in `15_band_by_part_number.csv`, of which banded | With a cross-reference string, `genuine_pn` only / incl. `bvp_pn` | Rows in the family file | Of those, under this family |
|---|---:|---:|---|---:|---:|---:|
| brake rotor | 109 | 4,457,248 | 8, of which **7 banded at EUR 1,061,419** on that file's own basis | 1 / 1 | 109 | 109 |""",
'route table: row count, not band count')

t = sub(t,
"""| blower filter | 7 | 1,349,479 | 0 | 3 / 6 | 12 | 7 |
| urea filter | 7 | 134,108 | 0 | 1 / 2 | 5 | 2 |
| clutch booster | 48 | 47,151 | 0 | 28 / 37 | 48 | 48 |
| pilot bearing | 3 | 2,947 | 0 | 2 / 3 | 3 | 3 |""",
"""| blower filter | 7 | 1,349,479 | 0 | 3 / 6 | 12 | 7 |
| urea filter | 7 | 134,108 | 0, of which 0 banded | 1 / 2 | 5 | 2 |
| clutch booster | 48 | 47,151 | 0 | 28 / 37 | 48 | 48 |
| pilot bearing | 3 | 2,947 | 0 | 2 / 3 | 3 | 3 |""",
'route table: urea row made explicit')

tmp = READ + '.__tmp_3f__'
with open(tmp, 'wb') as fh:
    fh.write(t.replace('\n', '\r\n').encode('utf-8'))
os.replace(tmp, READ)
print('  wrote 00_READ_ME_FIRST.md', os.path.getsize(READ), 'bytes')
