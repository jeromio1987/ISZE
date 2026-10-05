"""_b_patch_c.py -- reliable text patches to build_v20c_fix.py."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_Scripts\build_v20c_fix.py"
s = open(P, encoding='utf-8').read()
orig = s

# 1) the four-row comparison table: A -> C, r90 unchanged
old = """         "adjudication named change as follows (A = candidate a, B = this candidate):")"""
new = """         "adjudication named change as follows (A = candidate a, C = this candidate):")"""
assert old in s, "1a"
s = s.replace(old, new)

old = """A.append(md(['Row', 'Market / class', 'A (candidate a 2026-2030)', 'B (this candidate)', 'Note'],"""
new = """A.append(md(['Row', 'Market / class', 'A (candidate a 2026-2030)', 'C (this candidate)', 'Note'],"""
assert old in s, "1b"
s = s.replace(old, new)

old = """             [90, 'CYPRUS LCV LCV', '2238 / 2339 / 2445 / 2521 / 2614', '3252 / 3506 / 3708 / 3811 / 3868',
              'FIX 3 — seam 2014. The negative cohort retired.']]))"""
new = """             [90, 'CYPRUS LCV LCV', '2238 / 2339 / 2445 / 2521 / 2614', '2238 / 2339 / 2445 / 2521 / 2614',
              '**Deliberately UNCHANGED.** The seam re-base was attempted and reverted — it does not reconcile. Flagged UNRECONSTRUCTABLE, see §4.11.']]))"""
assert old in s, "1c"
s = s.replace(old, new)

# 2) the "what is still open on these two rows" paragraph
old = """A.append("**What is still open on these two rows.** The pre-seam series is an IML backbone stitched "
         "onto a real-registration cohort model, and it **cannot be decomposed into cohorts without "
         "producing a negative cohort**. The seam years themselves are therefore **UNRECONSTRUCTABLE** "
         "from the sources on disk, not merely unknown, and neither row is given a positive-number "
         "guess. Both are flagged `INPUT DERIVED - seam year`. The candidate is disclosed, not papered "
         "over. Sources read and their verdicts are in §4.9.")"""
new = """A.append("**What is still open on these two rows.** The pre-seam series is an IML backbone stitched "
         "onto a real-registration cohort model, and on r54 it **cannot be decomposed into cohorts "
         "without producing a negative cohort**. The r54 seam year is therefore **UNRECONSTRUCTABLE** "
         "from the sources on disk, not merely unknown, and it is given no positive-number guess. On "
         "r90 the re-base does not reconcile at all (§4.11), so that row keeps its reconciling build "
         "and is flagged UNRECONSTRUCTABLE for the 2014 gap. The candidate is disclosed, not papered "
         "over. Sources read and their verdicts are in §4.9.")"""
assert old in s, "2"
s = s.replace(old, new)

# 3) section 6 seam table: r90 no longer re-based
old = """             [54, '**Portugal LCV**', '**2005**', 'IML backbone, no real-registration cohort model named', 'Same — added in this pass (was missing)'],
             [90, '**Cyprus LCV**', '**2014**', 'IML backbone, no real-registration cohort model named', 'Same — added in this pass (was missing)']]))"""
new = """             [54, '**Portugal LCV**', '**2005**', 'IML backbone, no real-registration cohort model named', 'Same — added in this pass (was missing)'],
             [90, '**Cyprus LCV**', '2014 (gap — not a re-base point)', 'IML backbone, no real-registration cohort model named', '**Not re-based.** Re-basing at 2014 does not reconcile (residual −862) and double-counts the cohort; the row keeps its 1990-on build and the 2014 gap is flagged UNRECONSTRUCTABLE (§4.11)']]))"""
assert old in s, "3"
s = s.replace(old, new)

# 4) section 7 verification table rows for r54/r90
old = """             ['r54 Portugal LCV 2026-2030', '**%s** — seam 2005, all three negative cohorts retired' % plan[54]['v20']],
             ['r90 Cyprus LCV 2026-2030', '**%s** — seam 2014, the negative cohort retired' % plan[90]['v20']],"""
new = """             ['r54 Portugal LCV 2026-2030', '**%s** — seam 2005, all three negative cohorts retired' % plan[54]['v20']],
             ['r90 Cyprus LCV 2026-2030', '**%s** — unchanged; seam re-base attempted and reverted (does not reconcile)' % plan[90]['v20']],"""
assert old in s, "4"
s = s.replace(old, new)

# 5) FIX 2 sheet note: correct the negative-input section reference already patched; no-op here

open(P, 'w', encoding='utf-8').write(s)
print("patched; changed:", s != orig)
print("remaining 'candidate b' mentions:", s.count("candidate b"))
import re
for m in re.finditer(r'.*candidate b.*', s):
    print("   " + m.group(0)[:120])
