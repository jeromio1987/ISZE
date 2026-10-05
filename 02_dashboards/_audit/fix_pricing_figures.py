"""Report (and optionally fix) the euro unit bug and nan cells in the pricing findings dashboard.

Default is report-only. Pass --fix to write.
"""
import argparse
import pathlib
import re

P = pathlib.Path(
    r"C:\Users\jerom\Desktop\claude\ISZE\02_dashboards\pricing"
    r"\ISZE_Pricing_History_Findings_Dashboard.html"
)

# A value like EUR 30,422,371.9M is already in units, with an M suffix bolted on.
BAD = re.compile(r"(?:&euro;|€)\s?([0-9]{1,3}(?:,[0-9]{3})+(?:\.[0-9]+)?)M")


def to_millions(raw: str) -> str:
    val = float(raw.replace(",", "")) / 1_000_000
    return f"€{val:,.2f}M".replace(".00M", "M")


ap = argparse.ArgumentParser()
ap.add_argument("--fix", action="store_true")
args = ap.parse_args()

src = P.read_text("utf-8", errors="surrogateescape")
lines = src.split("\n")

print(f"file: {P.name}  ({len(src):,} chars, {len(lines)} lines)")
print()

# ---- euro unit bug ----
hits = []
for m in BAD.finditer(src):
    start = src.rfind("\n", 0, m.start())
    end = src.find("\n", m.end())
    line_no = src.count("\n", 0, m.start()) + 1
    ctx = src[start + 1:end]
    hits.append((line_no, m.group(0), to_millions(m.group(1)), ctx))

print(f"BAD EURO VALUES: {len(hits)}")
for n, bad, good, _ in hits:
    print(f"  L{n:<5} {bad:<22} -> {good}")

# ---- stray nan ----
nan_hits = []
for m in re.finditer(r"(?<![A-Za-z])nan(?![A-Za-z])", src):
    line_no = src.count("\n", 0, m.start()) + 1
    s = max(0, m.start() - 60)
    nan_hits.append((line_no, src[s:m.end() + 25].replace("\n", " ")))

print()
print(f"STRAY nan CELLS: {len(nan_hits)}")
for n, ctx in nan_hits:
    print(f"  L{n:<5} ...{ctx}")

if not args.fix:
    print("\n(report only; pass --fix to write)")
    raise SystemExit(0)

fixed = BAD.sub(lambda m: to_millions(m.group(1)), src)
fixed, n_nan = re.subn(r"(?<![A-Za-z])nan(?![A-Za-z])", "—", fixed)

# keep a backup next to the file
bak = P.with_suffix(".html.bak_20260916")
bak.write_text(src, encoding="utf-8", errors="surrogateescape")
P.write_text(fixed, encoding="utf-8", errors="surrogateescape")

print(f"\nWROTE {P}")
print(f"backup {bak.name}")
print(f"euro values corrected: {len(hits)}   nan cells replaced: {n_nan}")
