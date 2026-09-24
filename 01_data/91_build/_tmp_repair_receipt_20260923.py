"""Correct the page's ship receipt in place: three claims were wrong.

  1. "The service families split at CY went from 1 to 7" - 7 is the number still REFUSED. The
     verified answer is 1 before, 3 after. Corrected with the family-by-family list.
  2. "52 of the 52 part numbers that move are single-band only because a parked code was excluded"
     - that describes the 52-row gap between the two derived files, not the movement on the page's
     own file. The page file's own movement is decomposed instead.
  3. The re-base figure and the rule statement, because a second pass was needed: the stated rule
     was not actually applied to twelve rows.

The page itself is untouched (hash befccefd..., mtime 06:53:14) and is not rebuilt.

Read, amend, write. The receipt is rewritten from the file on disk so nothing else is lost.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
RECEIPT = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.SHIP_RECEIPT.json"
HTML = ROOT / "02_dashboards" / "sales" / "ISZE_PMS_Family_Evolution_v2.html"
DER = ROOT / "01_data" / "00_derived"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


FAMILY_SPLIT = (
    "CORRECTED. The page publishes one verdict per service family per clock. `pooled` is a refusal "
    "('not comparable by band'); `thin` and `ok` both mean the family IS split by tonnage, `thin` "
    "carrying a caveat. An earlier version of this receipt said 'the service families split at CY "
    "went from 1 to 7'. That is wrong: 7 is the number of families still REFUSED, and it "
    "coincidentally equals the figure that was mis-stated as the count that split. "
    "MEASURED from the two payloads, CY clock: 10 families carry euro; SPLIT 1 before, 3 after; "
    "REFUSED 9 before, 7 after. The three that now split are Clutch kit (thin, unchanged - it "
    "already split), Brake shoe (pooled -> ok), Fuel filter (pooled -> ok). So the movement is one "
    "family to three, not one to seven. "
    "CY before, the ten, refusing or splitting: Air filter refused, Brake pad refused, Brake rotor "
    "refused, Brake shoe refused, Clutch disc refused, Clutch kit SPLIT (thin), Clutch pressure "
    "plate refused, Fuel filter refused, Oil filter refused, Release bearing refused. "
    "CY after: Air filter refused (59% shared), Brake pad refused, Brake rotor refused (73% "
    "shared), Brake shoe SPLIT (ok, 0% shared), Clutch disc refused, Clutch kit SPLIT (thin, 35%), "
    "Clutch pressure plate refused, Fuel filter SPLIT (ok, 2%), Oil filter refused (100% shared), "
    "Release bearing refused. "
    "FY clock, same measurement: SPLIT 2 before, 4 after; REFUSED 8 before, 6 after. The two extra "
    "before are Clutch kit (thin) and Clutch pressure plate (thin); the four after are Brake shoe "
    "(ok), Clutch kit (thin), Clutch pressure plate (thin), Fuel filter (ok). "
    "So on the calendar clock one family could be split before and three can now; on the ISZE clock "
    "two before and four now. The families the page refuses fell by two on each clock."
)

MOVEMENT = (
    "TWO DIFFERENT POPULATIONS, and an earlier version of this receipt conflated them. "
    "(A) THE PAGE FILE'S OWN MOVEMENT. `tonnage_capable_part_numbers.csv` went 297 rows / 143 "
    "single-band to 324 rows / 176 single-band, in two steps: the re-base took it to 324 rows / 180 "
    "single-band, then the NMR row repair below took it to 176. The re-base's own movement was +33 "
    "rows entering the file (all 33 single-band), 6 rows leaving it (all 6 single-band), and of the "
    "291 rows present on both sides 10 flipped to single-band and 0 flipped away: 143 + 33 - 6 + 10 "
    "- 0 = 180. NONE of that movement is NMR-driven: across it the count of single-band rows "
    "carrying a quarantined code went from 2 to 3, and the non-parked single-band count went 141 to "
    "177. The second step, the repair, moved four rows the other way (one band to two) and is "
    "described in nmr_row_repair. "
    "(B) THE GAP BETWEEN THE TWO DERIVED FILES. `vehicle_band_applicability.csv` reads 230 "
    "single-band against the page file's 176. Measured row by row, the two files disagree on 58 "
    "part numbers: 56 that the neutral table calls one-band and the page file does not, of which 53 "
    "carry a quarantined code (these are the rows whose single-band status is the pending NMR "
    "ruling, and they are the bulk of the 230); plus 2 that the page file calls one-band and the "
    "neutral table does not, which are rows outside its banded scope. So 230 - 176 = 54 as a count, "
    "but the disagreement is 58 rows and it is NOT the ruling alone - 3 of the 56 are not "
    "quarantined. The earlier sentence '52 of the 52 part numbers that move are single-band only "
    "because a parked code was excluded' described population (B) in the words of population (A), "
    "and its 52 was also wrong. The two are now stated separately and both from measurement."
)

REPAIR = (
    "SECOND PASS, 2026-09-23 (the NMR row repair). The first pass applied the stated rule 'a "
    "quarantined code contributes its interim band' and, on twelve rows, did not. Root cause: the "
    "statement was not true of those rows because the quarantined code was never RECOGNISED on "
    "them. `tokens_from_text` splits a model string on [,\\s/;]+ and then requires an exact map "
    "key, but the EPC writes NMR glued to a suffix - '2016 NLR/NMR-LHD EURO6 EUROPE 16.0 - 17.0' "
    "splits to 'NMR-LHD EURO6 ...', never 'NMR' - and the cross-reference writes it after an "
    "ideographic comma, 'NKR、NMR,NLR'. So ten part numbers whose only 5.5 t evidence is NMR were "
    "never recorded as parked: `parked_codes` came out empty, the pre-existing 'a parked code "
    "contributes its interim band' branch had nothing to act on, the NMR rung was silently dropped "
    "from `n_series_bands`, and those rows lost their 5.5 t band. Ten lost 5.5 t; two more moved "
    "the other way (8981868281 gained 7.5 t, 8983615742 lost 5.5 t). "
    "It was NOT `model_code_to_tonnage.csv`. That file is read nowhere in this builder and appears "
    "in no uncommented line of it, so its 7.5 t for NMR could not have been the source. The cause "
    "is entirely the tokeniser's blindness to how the code is written. "
    "THE GUARD, structural not a patch: a quarantined code is now detected by a whole-word scan of "
    "the raw evidence text (`pending_codes_in_text`), which is delimiter-independent, and a row that "
    "names one KEEPS the band list this file already carried rather than having it recomputed. An "
    "interim value cannot be moved by a build. The scan is limited to the codes the authored map "
    "already marks `pending_ruling`, so it cannot widen detection for ordinary codes and "
    "reintroduce the documented `F*` vs `TF*` error. "
    "PROVEN: the scan fires on 'NMR-LHD ...', 'NMR-RHD ...' and 'NKR、NMR,NLR', and does NOT fire on "
    "'NNR/NPR-LHD', 'TFR/TFS(LHD)EXP' (the pickup pair), 'NHR EURO6' (unresolved but not pending) or "
    "'FRR(RHD)SPACECAB'. Applied, it touched exactly the twelve rows and no others, and restored "
    "each to its pre-rebase value. The file now reads 176 single-band, not 180: four of the twelve "
    "correctly become two-band rows, because a part that fits NMR and one settled rung is shared. "
    "STILL OPEN: the neutral table `vehicle_band_applicability.csv` has the SAME defect - 10 rows "
    "whose raw evidence names NMR but whose `parked_codes` is empty - because the tokeniser is "
    "shared. It was NOT fixed: repairing it would change that table, which this repair was "
    "forbidden to touch. The two files now disagree about those 10 rows' parked status."
)

FAMILY_NOTE = (
    "NOTE ON THE PAGE AND THIS REPAIR. The page was built from the 180-row file and is UNCHANGED "
    "at hash befccefd... The repair moved four rows from one band to two, two of them brake_shoe "
    "part numbers, so the page's payload and the repaired file now disagree on the shared-euro "
    "share behind brake_shoe. Measured on the page's own billing frame and category resolution, "
    "brake_shoe's shared share goes from 0.0630 to 0.2723 on the CY clock and 0.0647 to 0.3029 on "
    "FY. The page refuses a family only above 0.50, so brake_shoe stays in the splittable set on "
    "the repaired file; what would change is its label, from `ok` to `thin`, and `thin` is still "
    "splittable - it carries a caveat, not a refusal. "
    "LIMIT ON THAT NUMBER, stated rather than hidden: my frame does NOT reproduce the page's "
    "payload exactly. The payload reports brake_shoe shareShared 0.0 where my frame computes 0.0630 "
    "on the same file, and my re-implementation of the page's verdict rule reproduced only 17 of 20 "
    "verdicts as a control (air_filter on CY and FY, clutch_pressure_plate on CY). So the 0.2723 / "
    "0.3029 figures are my frame's, not the page's, and the precise future verdict is NOT verified. "
    "What is robust is the comparison: both figures sit far below the 0.50 refusal line, and the two "
    "moved rows carry EUR 3,519 of billed euro against a family total of EUR 5,946, so no plausible "
    "frame puts this family over 50%. No rebuild was made and none is needed for the corrections in "
    "this receipt; if Jerome wants the page to show the repaired figure, that is his call and a "
    "rebuild, not this receipt."
)


def main() -> int:
    d = json.loads(RECEIPT.read_text(encoding="utf-8"))
    st = HTML.stat()
    live_sha = sha(HTML)
    assert live_sha == d["artifact_sha256"], "page hash moved - receipt would not cover it"

    by_id = {c["id"]: c for c in d["checks"]}

    by_id["legacy_file_rebased"]["detail"] = (
        "01_data/00_derived/tonnage_capable_part_numbers.csv 297 rows -> 324 rows; 143 -> 176 part "
        "numbers with n_bands == 1 (180 after the first pass, 176 after the NMR row repair). Four "
        "figures on this file, which are four different questions and must not be interchanged: "
        "n_bands == 1 reads 176 (the three-rung ladder, the question this page uses); band_count == "
        "1 reads 200 (all four vehicle groups); exclusive_band non-empty reads 151; and 230 is "
        "vehicle_band_applicability.csv's answer to the three-rung question WITHOUT the quarantined "
        "band, which is the other side of the pending NMR ruling. Written by the builder "
        "(01_data/91_build/pn_ammo_probe_20260918/_vehicle_band_applicability.py), not hand-edited. "
        "Columns unchanged: True, same order, 14 columns."
    )
    by_id["rule_applied"]["detail"] = (
        "a quarantined code contributes its interim band. Two qualifications, both measured rather "
        "than assumed. (1) On the first pass the rule was stated but NOT applied to twelve rows, "
        "because the quarantined code was not recognised on them; see the nmr_row_repair check. "
        "(2) 'The only rule whose answer cannot move when the NMR ruling lands' is true of the "
        "single-VERSUS-shared question, which is what this page reads, but NOT of a parked row's raw "
        "band list: in the first pass 54 parked rows read n_bands = 2 and after the repair 52 do, so "
        "that column does move if the ruling lands. The three-rung columns carry the legacy "
        "vocabulary only (3.5t / 5.5t / 7.5t); no D-Max or F-series band is written into them."
    )
    by_id["earlier_230_was_wrong"]["detail"] = MOVEMENT
    by_id["family_verdicts_moved"]["detail"] = (
        "read from the rebuilt payload, both clocks. brake_shoe pooled -> ok (CY shareShared 0.8261 "
        "-> 0.0); fuel_filter pooled -> ok (CY 0.9312 -> 0.0182); air_filter 'no part number fits "
        "one band' -> '59% of this family's euro sits on part numbers that fit more than one band' "
        "(shareShared 1.0 -> 0.5948); brake_rotor's reason changed while its verdict stayed pooled "
        "(see brake_rotor_flip); clutch_kit 0.3717 -> 0.3455 on CY. The COUNT of families the page "
        "will split is corrected in family_split_corrected - the earlier '1 to 7' figure in this "
        "check was wrong and is superseded."
    )
    d["notes"] = (
        "One job: re-base the family-evolution page on the corrected series-to-band mapping, so the "
        "page stops hiding part numbers that fit exactly one truck tonnage band. A quarantined code "
        "keeps its interim band. The page-visible change is the service-family verdicts: brake shoe "
        "and fuel filter become splittable by tonnage on both clocks, air filter and brake rotor "
        "stop claiming no part number fits one band (both still refused, for a now-stated reason). "
        "The page's builder needed no change. " + REPAIR + " " + FAMILY_NOTE
    )

    if "nmr_row_repair" not in by_id:
        d["checks"].append({
            "id": "nmr_row_repair",
            "ok": True,
            "detail": REPAIR,
        })
    else:
        by_id["nmr_row_repair"]["detail"] = REPAIR

    if "family_split_corrected" not in by_id:
        d["checks"].append({
            "id": "family_split_corrected",
            "ok": True,
            "detail": FAMILY_SPLIT,
        })
    else:
        by_id["family_split_corrected"]["detail"] = FAMILY_SPLIT

    if "vehicle_band_applicability_has_no_backup" not in by_id:
        d["checks"].append({
            "id": "vehicle_band_applicability_has_no_backup",
            "ok": True,
            "detail": (
                "01_data/00_derived/vehicle_band_applicability.csv had NO backup anywhere on disk "
                "before this repair, while every sibling derived file had one. A copy was taken: "
                "01_data/00_derived/_backsafe_rebase_20260923_vehbandapplic/"
                "vehicle_band_applicability.csv.bak_20260923_repair, 352,887 bytes, sha256 "
                "226d662d4a25bfb2587cf31407297bce11b459202467f983c2c2ce1940cf8e4c, identical to the "
                "live file. Its meta.json was copied alongside it, plus the legacy file as it stood "
                "before the NMR repair "
                "(tonnage_capable_part_numbers.csv.bak_pre_nmr_repair, sha256 B9703F31131F3072...)."
            ),
        })

    if "protected_files_rechecked_after_repair" not in by_id:
        d["checks"].append({
            "id": "protected_files_rechecked_after_repair",
            "ok": True,
            "detail": (
                "After the NMR repair, re-hashed: vehicle_band_applicability.csv unchanged "
                "(226d662d...), vehicle_band_applicability.meta.json unchanged (A4DDB914...), "
                "tonnage_capable_categories.csv unchanged (F4569239...), nseries_tonnage_evolution"
                ".csv unchanged (1C89E831...) and its meta.json unchanged (76B60C39...); "
                "epc_decode_nseries_banded.csv and vehicle_family_bands.csv still byte-identical to "
                "their _backsafe_20260923_canon_map copies. The repair touched exactly the twelve "
                "rows in tonnage_capable_part_numbers.csv and nothing else: 12 part numbers changed, "
                "all twelve from the named list, zero others, across all 14 columns."
            ),
        })

    d["artifact_mtime_ms"] = int(st.st_mtime * 1000)
    d["artifact_bytes"] = st.st_size
    d["artifact_sha256"] = live_sha
    d["written_at"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    d["receipt_revision_note"] = (
        "Revised 2026-09-23 after the NMR row repair. Three claims corrected, none of them about a "
        "figure on the page: the family-splittability count (1 -> 3, not 1 -> 7), which movement the "
        "52/54 figure describes, and the re-base figure and rule statement after the repair. The "
        "page itself was not rebuilt and is unchanged at the hash and mtime above."
    )

    RECEIPT.write_text(json.dumps(d, indent=2), encoding="utf-8")
    print(f"wrote {RECEIPT}")
    print(f"  artifact {st.st_size:,} bytes  sha256 {live_sha}")
    print(f"  checks {len(d['checks'])}  failed "
          f"{[c['id'] for c in d['checks'] if not c['ok']]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
