from pathlib import Path

lines = Path(r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md").read_text(
    encoding="utf-8").splitlines()

out = []
for i, l in enumerate(lines, 1):
    if l.count("|") > 6:
        out.append(f"line {i}: pipes={l.count('|')}  starts={l[:70]!r}")

out.append("")
mine = [i for i, l in enumerate(lines, 1) if "PR00 IE40 write-back STOPPED" in l]
out.append(f"my row line(s): {mine}")
for i in mine:
    out.append(f"  pipes={lines[i-1].count('|')}  (table needs 6)")
    out.append(f"  cells={[c.strip()[:40] for c in lines[i-1].strip().strip('|').split('|')]}")

Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_tmp_apply_export_pr00_20260924\_board_check.txt").write_text(
    "\n".join(out), encoding="utf-8")
print("written")
