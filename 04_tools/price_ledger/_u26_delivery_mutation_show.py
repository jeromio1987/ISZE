# -*- coding: utf-8 -*-
"""Print both mutation outputs side by side, read from the JSON on disk."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
p = Path(__file__).resolve().parents[2] / "01_data" / "91_build" / "_u26_delivery_mutation_20261007.json"
d = json.loads(p.read_text(encoding="utf-8"))


def show(title, block):
    print(title)
    print(f"  {'case':<10} {'mapped delivery':<16} {'eligible':<9} reason_codes")
    for k in ("as_read", "stripped", "restored"):
        v = block[k]
        print(f"  {k:<10} {str(v['mapped_delivery_included']):<16} "
              f"{str(v['eligible']):<9} {v['reason_codes']}")
    print()


show("OUTPUT 1 — REAL BASIS (the row exactly as the copy on disk maps it)", d["real_basis"])
print("  field_is_read_on_this_row:", d["real_basis"]["field_is_read_on_this_row"])
print("  note:", d["real_basis"]["note"])
print()
show("OUTPUT 2 — FORCED-YES WIRING PROOF (same row, delivery_included='yes')",
     d["forced_yes_wiring_proof"])
print("  wiring_proven   :", d["forced_yes_wiring_proof"]["wiring_proven"])
print("  mapping_is_wired:", d["mapping_is_wired"])
print()
print("VERDICT:", d["verdict"])
