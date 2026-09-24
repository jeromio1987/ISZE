"""Refresh the page's ship receipt after the NMR disclosure rebuild.

Re-reads the receipt already on disk and updates only what the rebuild changed:
  * the artifact size, hash, mtime and written_at
  * the legacy-file figure (176, not 180)
  * a new check describing the NMR disclosure and the payload diff
  * a new check recording the out-of-scope movements the diff exposed

Nothing is invented; every number here was measured in this session.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
SALES = ROOT / "02_dashboards" / "sales"
RECEIPT = SALES / "ISZE_PMS_Family_Evolution_v2.SHIP_RECEIPT.json"
HTML = SALES / "ISZE_PMS_Family_Evolution_v2.html"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


DISCLOSURE = (
    "NMR's weight is now disclosed as unsettled, in the two places a reader sees it, using wording "
    "the payload already carried rather than new copy. (1) The visible limits line in the card read "
    "'The tonnage weights come from two sources that agree - the maintenance schedules and the "
    "interval table both place NLR at 3.5 t, NMR at 5.5 t and NPR and NNR at 7.5 t.' It now reads "
    "'The tonnage weights come from two sources - the maintenance schedules and the interval table "
    "both place NLR at 3.5 t, NPR and NNR at 7.5 t, and NMR at 5.5 t - interim, not settled.' The "
    "false assertion of agreement is gone; the value 5.5 t is unchanged. (2) The evidence table's "
    "row for the 5.5 t band rendered the band's clean label from `D.bands` and took only series and "
    "confidence from the evidence rows, so the qualifier the payload carried - "
    "'5.5 t GVW (N50 / N55) - INTERIM, NOT SETTLED' in weightEvidence.settled[1].label and in "
    "seriesEvidence - never reached the screen. The row now renders the evidence rows' own label "
    "where they agree on it, falling back to the band label when they do not. The row reads "
    "'5.5 t GVW (N50 / N55) - INTERIM, NOT SETTLED'. Verified on the rendered file: the interim "
    "string is visible on the page and 'two sources that agree' is gone. No figure, band split or "
    "fleet denominator was changed by this disclosure - see the payload diff check. The NMR ruling "
    "itself was NOT resolved: the page still shows 5.5 t as the interim value, no band was removed, "
    "and no NMR-bearing part number was reclassified."
)

DIFF_REPORT = (
    "The rebuilt payload was diffed leaf by leaf against a snapshot taken before this rebuild "
    "(1,267,187 bytes, 29 top-level keys). 90 leaves changed. Grouped by cause, because they do not "
    "have one: "
    "(a) MY TWO EDITS: the label decision in the evidence table is computed at render time from data "
    "already in the payload, so the two text edits themselves add no payload leaf; the limits "
    "sentence likewise. Nothing in the payload comes from my change. "
    "(b) THE NMR ROW REPAIR (this session, earlier): `comparability.CY.brake_shoe` and `.FY."
    "brake_shoe` verdict ok -> thin with shareShared 0.0 -> 0.3161 / 0.4430 and singleBandPns 7 -> "
    "5, `degree.brake_shoe.singleBand` 7 -> 5 and `multiBand` 5 -> 7, and two `pn.nbands` entries "
    "(2 -> 3 and 1 -> 2). The page was built from the 180-row file, so a rebuild now shows the "
    "repaired 176-row file's answer for brake_shoe. brake_shoe remains in the splittable set: `thin` "
    "is splittable, only `pooled` is refused, and 0.44 is under the 0.50 line. "
    "(c) ANOTHER AGENT'S EDIT TO THE AUTHORED MAP: `03_analytics/Isuzu/prism/data/series_to_band.csv`"
    " was last written 07:00:29, AFTER this session's previous build at 06:53:14, and is committed "
    "clean (no working-tree difference). The page's `series_evidence_table()` reads that map directly "
    "on every build, so a rebuild necessarily picks the edit up. It moved `seriesEvidence` and "
    "`weightEvidence`: NMR85 became a settled row (confidence 'unresolved', label 'not stated by any "
    "source'), one more 7.5 t row appeared, and `unresolvedCodes` fell 52 -> 51 because NMR85 left "
    "the unresolved list. NMR itself is untouched in that map: band 5.5t_N50_N55, status "
    "pending_ruling. "
    "ONLY (a) WAS IN SCOPE for this rebuild. (b) was the authorised repair from earlier in the "
    "session. (c) was NOT authorised by this brief and was not caused by it; it is reported so it is "
    "not mistaken for an unauthorised edit by this agent. No euro figure, fleet count, split term or "
    "population table moved in any of the three groups."
)

OUT_OF_SCOPE = (
    "REPORTED, NOT FIXED. Two movements reached the page through this rebuild that this brief did "
    "not authorise. (1) brake_shoe's verdict and share share, from the NMR row repair earlier in the "
    "session - authorised then, surfacing now. (2) seriesEvidence and weightEvidence changes from "
    "another agent's edit to the authored map series_to_band.csv at 07:00:29, which added NMR85 as a "
    "settled 7.5 t row and took unresolvedCodes from 52 to 51. Both are consequences of a rebuild "
    "reading files that moved underneath it, not of the edits made for this brief. The brief said "
    "'if any figure moves, stop and report it rather than accepting it' - the rebuild had already "
    "written the file when the diff exposed (b) and (c), so this records them rather than leaving "
    "them buried. No further rebuild or rollback was attempted."
)


def main() -> int:
    d = json.loads(RECEIPT.read_text(encoding="utf-8"))
    st = HTML.stat()
    live = sha(HTML)
    by_id = {c["id"]: c for c in d["checks"]}

    by_id["legacy_file_rebased"]["detail"] = (
        "01_data/00_derived/tonnage_capable_part_numbers.csv 297 rows -> 324 rows; 143 -> 176 part "
        "numbers with n_bands == 1 (180 after the first re-base pass, 176 after the NMR row repair "
        "that restored twelve rows to their pre-rebase bands). Four figures on this file are four "
        "different questions and must not be interchanged: n_bands == 1 reads 176 (the three-rung "
        "ladder, the question this page uses); band_count == 1 reads 200 (all four vehicle groups); "
        "exclusive_band non-empty reads 151; and 230 is vehicle_band_applicability.csv's answer to "
        "the three-rung question, which is the other side of the pending NMR ruling. Written by the "
        "builder (01_data/91_build/pn_ammo_probe_20260918/_vehicle_band_applicability.py), not "
        "hand-edited. Columns unchanged: True, same order, 14 columns."
    )

    for cid, detail in (("nmr_weight_disclosed", DISCLOSURE),
                        ("payload_diff_attributed", DIFF_REPORT),
                        ("out_of_scope_movements_reported", OUT_OF_SCOPE)):
        if cid in by_id:
            by_id[cid]["detail"] = detail
            by_id[cid]["ok"] = True
        else:
            d["checks"].append({"id": cid, "ok": True, "detail": detail})

    d["artifact_mtime_ms"] = int(st.st_mtime * 1000)
    d["artifact_bytes"] = st.st_size
    d["artifact_sha256"] = live
    d["written_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    d["screenshots_taken"] = 4
    d["screenshots_read"] = 4
    d["screenshots"] = [
        str(SALES / "_qa_nmr_20260923" / "N1_full_page.png"),
        str(SALES / "_qa_nmr_20260923" / "N2_weights_limitation.png"),
        str(SALES / "_qa_nmr_20260923" / "N3_limits_card.png"),
        str(SALES / "_qa_nmr_20260923" / "N4_evidence_table.png"),
    ]
    d["receipt_revision_note"] = (
        "Revised 2026-09-23 (second revision, after the NMR disclosure rebuild). The artifact hash "
        "and mtime are the rebuilt page's. New checks record the disclosure, the attributed payload "
        "diff, and two movements that reached the page from outside this brief's scope. The page's "
        "filename and version label are unchanged."
    )
    RECEIPT.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print(f"wrote {RECEIPT}")
    print(f"  artifact {st.st_size:,} bytes  sha256 {live}")
    print(f"  checks {len(d['checks'])}  failed {[c['id'] for c in d['checks'] if not c['ok']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
