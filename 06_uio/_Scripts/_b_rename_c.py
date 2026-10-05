"""_b_rename_c.py -- rename candidate-b symbols to candidate-c in build_v20c_fix.py."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\build_v20c_fix.py"
s = open(P, encoding='utf-8').read()

reps = [
    ("CAND_B = os.path.join", "CAND_C = os.path.join"),
    ("CAND_B", "CAND_C"),
    ("'full precision -> what candidate b uses'", "'full precision -> what candidate c uses'"),
    ("**After (candidate b):**", "**After (this candidate):**"),
    ('print("  candidate c: %s" % CAND_C)', 'print("  candidate c: %s" % CAND_C)'),
    ('print("  candidate b: %s" % CAND_C)', 'print("  candidate c: %s" % CAND_C)'),
    ("copied candidate A -> %s", "copied candidate b -> %s"),
]
for a, b in reps:
    s = s.replace(a, b)

# CAND_A should point at candidate b now (the file we derive from)
s = s.replace('CAND_A = os.path.join(CUR, "ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22.xlsx")',
              'CAND_PREV = os.path.join(CUR, "ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22b.xlsx")')
s = s.replace("CAND_A", "CAND_PREV")
s = s.replace('BASESUP = "ISUZU_UIO_Overview_2026_V20_CANDIDATE_2026-09-22b.xlsx"', "")

# assumptions-log header wording
s = s.replace('A.append("**Supersedes:** `%s` (kept intact)  " % CAND_PREV)',
              'A.append("**Supersedes:** `%s` (kept intact)  " % CAND_PREV)')

# A->C comparison should read the PREVIOUS candidate (b), which is what CAND_PREV holds
s = s.replace("A_ROWS", "PREV_ROWS").replace("wsa", "wsprev").replace("A_GT", "PREV_GT")

open(P, 'w', encoding='utf-8').write(s)
print("renamed. CAND_C/CAND_PREV occurrences:", s.count("CAND_C"), s.count("CAND_PREV"))
print("leftover CAND_A:", s.count("CAND_A"), "| leftover CAND_B:", s.count("CAND_B"))
