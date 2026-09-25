"""Append one row to the delegator board, UTF-8 no BOM, CRLF, read-check-write."""
import io
import os
import shutil
from datetime import datetime

BOARD = r"C:\Users\jerom\Desktop\claude\ISZE\00_docs\agent\DELEGATOR_BOARD.md"
STAMP = "2026-09-25 06:55"

ROW = (
    f"| {STAMP} | cursor (release wiring + retest) | "
    "**The approved release was re-tested and the gate was deliberately NOT repointed. The approval "
    "is a label because no reader in the chain names a release at all, and repointing the gate would "
    "have made it certify the release with the wrong file's evidence.** Lineage, read-only: the gate "
    "reads `aim_pn_classification_v2.csv` (164,667 rows, written 20 Sep 20:47, read by nothing else) "
    "at `verify_aim_classification.py:29` and reads its meta from a hard-coded path at `:201`; "
    "`build_aim_master.py` reads pr00 + sales + the AIM workbook and never the release; the master "
    "the packs read is edited in place by a chain of `apply_*` scripts; the four AIM comparison / "
    "deep-dive pages read `AIM_Master_PN_Categories_Figkey_20260924.csv`, whose builder reads the "
    "overlay `aim_pn_classification_20260920.csv` first and the master second. Nothing calls "
    "`assert_release` anywhere in the Universe build. Retest on billed 2025 parts (EUR 32,330,198.32 "
    "on 16,831 part numbers, after freight / rebate / interest / service-fee and lubricant lines are "
    "out): catalogue tree **0 rows changed** against the live overlay, AIM labels **1,159 rows / "
    "EUR 469,278.08**, and **1,147 of those rows and EUR 410,396.98 move residual -> named with 0 "
    "rows the other way**; the CAB ASM class, the orphan appends and the lubricants sit only in the "
    "live file, so the release is behind on the axes that matter and identical on the one it wins. "
    "White-paper examples: (a) the brake-pad group reproduces to the cent, EUR 357,044.75 -> "
    "304,257.91 on the release; (b) Portugal clutch components against true kits still does not "
    "hold, kits are 14.0% of the clutch group in 2024 and 11.9% in 2025; (c) air-filter euro under "
    "'Air conditioning' is EUR 10,048.83 / 0.367%, **one part number 8980913940 whose own figure "
    "key 130-006 is labelled Air filter**, and the leaf check is met because the release carries "
    "177 leaves including `Filters > Filter element` (part 5864052180, EUR 0 billed). Faults: the 4 "
    "Shell PNs under Wheel Rim are **still there on the AIM axis only** (the live master has fixed "
    "them to Fluids Chemicals > Lubricants), the guide pin 8980475290 is **still on "
    "`Brake parts > Brake pad`** on the catalogue axis while its AIM label is correct, the bumper "
    "bars are **clean on the release's own tree** but survive in the separate maintenance tag (151 "
    "parts, EUR 95,318.68 of 2025 billing), and the Cab Assembly class is absent from the release as "
    "it must be. **The gate-leaf conclusion: 177 is right and the baseline already says so** - "
    "`aim_classification_leaf_baseline.json` carries `axis_a_l3_approved: 177`, revision "
    "`catalog_symbolic_leaf_20260920`, `released_by_jerome: true`; the 176 is the stale reading of "
    "the file nothing reads, so the failure message is out of date and no baseline change is needed. "
    "A read-only simulation of a full repoint gives **12 of 15**, with two of the three new failures "
    "artefacts of the repoint (`pr00_copy_integrity` reads v2's meta by a hard-coded path and "
    "reports `None`; `two_axes_contract` greps for the literal string `axis_b`, which the release's "
    "meta never uses), so I stopped rather than change the gate's meaning. Correction to two "
    "documents: 'the one rule that punishes the improvement itself' is wrong, and "
    "'EUR 111,125 of the cab billing on 7552044930' does not reproduce - that row is EUR 36,232.55 "
    "and EUR 11,125.03 is 7551847570. Also: `RELEASES.json`'s `2026-09-24-candidate` hash "
    "`e5824683...` belongs to `aim_pn_classification_20260920.csv.bak_pre_cab_class_20260924_192113`, "
    "not to the live overlay at its own recorded path, and the approved release is byte-identical to "
    "`...bak_pre_export_aim_eq_20260924_20260924_142051`. No classification file, gate file, "
    "baseline, builder or page was changed; hashes before and after are in the memo. "
    "| `00_docs/AIM_RELEASE_RETEST_2026-09-25.md` (new), `01_data/91_build/_blockD_*_20260925.py` "
    "and their `_blockD_*.json` / `.txt` / `.out.txt` probes (new), "
    "`01_data/91_build/_blockD_gate_sim_release.json` (new) "
    "| Jerome to decide three things: (1) the gate fix, which is four edits and needs his word - "
    "point `CLASS_V2` at the approved release, resolve the meta from the file being checked, keep a "
    "per-release drift baseline, and leave the 177 leaf baseline alone; (2) whether the pages stay on "
    "the live overlay, which is what I recommend, because repointing them would silently drop the "
    "Cab Assembly class, the orphan appends and EUR 469,278.08 of named families; (3) whether a new "
    "release should be cut from the settled master plus this catalogue tree, since the pillar board's "
    "condition 3 asks for one build-from release and 2026-09-20 cannot be it while it is four days "
    "behind. Still unestablished: the cab EUR 111,125, and about EUR 43,250 of the memo's "
    "EUR 1,420,628 exclusion list. |"
)

with io.open(BOARD, encoding="utf-8", newline="") as f:
    before = f.read()
assert "\ufeff" not in before[:1]
pre_lines = before.count("\n")
assert ROW[:60] not in before, "row already appended"

shutil.copyfile(BOARD, BOARD + ".bak_pre_blockD_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
with io.open(BOARD, "a", encoding="utf-8", newline="") as f:
    f.write(ROW + "\r\n")

with io.open(BOARD, encoding="utf-8", newline="") as f:
    after = f.read()
print(f"before lines {pre_lines}  after lines {after.count(chr(10))}")
print(f"row present exactly once: {after.count('cursor (release wiring + retest)')}")
print(f"still valid UTF-8, no BOM: {'\ufeff' not in after[:1]}")
print(f"bytes {os.path.getsize(BOARD):,}")
print("last 120 chars:", repr(after[-120:]))
