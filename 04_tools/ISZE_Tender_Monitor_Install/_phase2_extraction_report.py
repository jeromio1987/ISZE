"""Phase 2 deadline/value split + fleet lift + R&M sample — audit only."""
from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

from isze_core_v3 import RM_CONTRACT_TERMS, extract_fleet_size, keyword_hits

DATA = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json")
d = json.loads(DATA.read_text(encoding="utf-8"))
notices = d["notices"]

# Fleet before/after on current titles+descriptions
old_style = 0  # approximate: only English title patterns already in data
new_hits = 0
for n in notices:
    if n.get("fleet_size") not in (None, 0, "", "0"):
        old_style += 1
    v = extract_fleet_size(n.get("Title") or "", n.get("Description") or "")
    if v:
        new_hits += 1

# Deadline / value by source
by_src = Counter()
dl_by = Counter()
val_by = Counter()
for n in notices:
    src = n.get("Source") or "?"
    by_src[src] += 1
    if n.get("Deadline") or n.get("Deadline Date"):
        dl_by[src] += 1
    if n.get("value_amount") not in (None, "", 0, 0.0):
        val_by[src] += 1

print("=== FLEET ===")
print(f"currently sized in JSON: {old_style}/{len(notices)}")
print(f"multilingual extractor on title+desc: {new_hits}/{len(notices)}")

print("\n=== DEADLINE by source (populated / total) ===")
for src, tot in by_src.most_common():
    print(f"  {src}: {dl_by[src]}/{tot} ({100*dl_by[src]/tot:.0f}%)")

print("\n=== VALUE by source ===")
for src, tot in by_src.most_common():
    print(f"  {src}: {val_by[src]}/{tot} ({100*val_by[src]/tot:.0f}%)")

# R&M sample of 20
rm_true = [n for n in notices if n.get("rm_contract") is True]
rm_false = [n for n in notices if n.get("rm_contract") is False]
sample = []
random.seed(42)
sample.extend(random.sample(rm_true, min(10, len(rm_true))))
sample.extend(random.sample(rm_false, min(10, len(rm_false))))
print("\n=== R&M MANUAL SAMPLE (20) — review precision ===")
agree = 0
for n in sample:
    blob = " ".join([n.get("Title") or "", n.get("Description") or "", n.get("CPV Desc") or ""]).lower()
    hits = keyword_hits(blob, RM_CONTRACT_TERMS)
    cpv = str(n.get("CPV Code") or "")
    cpv_rm = cpv.startswith("501")
    flagged = bool(n.get("rm_contract"))
    # heuristic judge: true if clear R&M phrase or 501 CPV
    should = bool(hits) or cpv_rm
    ok = flagged == should
    agree += int(ok)
    print(f"{'OK' if ok else 'DIFF'} flag={flagged} should~={should} hits={hits[:3]} cpv={cpv[:10]} | {(n.get('Title') or '')[:70]}")
print(f"precision proxy (flag matches term/CPV rule): {agree}/{len(sample)}")

out = {
    "fleet_currently_sized": old_style,
    "fleet_extractor_hits": new_hits,
    "n": len(notices),
    "deadline_by_source": {k: {"have": dl_by[k], "total": by_src[k]} for k in by_src},
    "value_by_source": {k: {"have": val_by[k], "total": by_src[k]} for k in by_src},
    "rm_sample_agree": agree,
    "rm_sample_n": len(sample),
}
Path(__file__).with_name("_phase2_extraction_report.json").write_text(
    json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
)
print("wrote _phase2_extraction_report.json")
