"""_b_log_clean.py -- remove the duplicated section-12 block and fix %% artefacts."""
import io, sys, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

P = r"C:\Users\jerom\Desktop\claude\ISZE\06_uio\_CURRENT\UIO_V20_ASSUMPTIONS_2026-09-22b.md"
lines = open(P, encoding='utf-8').read().split('\n')
print("lines before:", len(lines))

idx = [i for i, l in enumerate(lines) if l.startswith('### 12.1 Harness result')]
print("occurrences of '### 12.1 Harness result':", idx)
if len(idx) == 2:
    # drop the first copy: from its start up to (but not including) the second copy,
    # then also drop the blank run immediately before the second copy
    a, b = idx
    while b - 1 > a and lines[b-1].strip() == '':
        b -= 1
    del lines[a:b]
    print("removed lines %d..%d (first copy)" % (a, b-1))

# fix %% escaping artefacts (markdown, not printf)
txt = '\n'.join(lines)
n_esc = txt.count('%%')
txt = txt.replace('%%', '%')
print("replaced %% occurrences:", n_esc)

# ensure a blank line before the three-way table that follows the 12.4 heading
txt = re.sub(r'(### 12\.4 Grand Total 2026-2030 — three-way)\n\|', r'\1\n\n|', txt)

open(P, 'w', encoding='utf-8').write(txt)
print("lines after:", len(txt.split('\n')))
print("\n--- headings ---")
for l in txt.split('\n'):
    if l.startswith('#'):
        print("  " + l)
