#!/usr/bin/env python3
"""
Model code -> tonnage band, and the banded EPC decode.

Why
---
`03_analytics/Isuzu/pms-pilot/parse_epc_results.py` carries `SERIES_TO_GVW`, an unsourced regex
dictionary that turns a model code into a weight class. It is where the Malta / Cyprus NMR88 error
came from (NMR88 read as a 3.5 t N35), and one of its entries is provably wrong: `'NMR': 'LCV 5.5t'`
sits beside `'NLR': 'LCV 3.5t'`, yet the ITUK UIO lookup labels NLR/NMR 3.5 t and the N35 fix itself
says the opposite. So the tonnage band for a part number is currently an inference.

This script replaces that inference with a sourced table.

Outputs
-------
1. `03_analytics/Isuzu/prism/data/model_code_to_tonnage.csv`
      one row per model code: band, weight label, source, quote, confidence.
      Bands are exactly: LCV_D-Max | 3.5t_N35 | 7.5t_N50_N62_N75 | F_series_MD_heavy | other.
2. `03_analytics/Isuzu/prism/data/model_code_to_tonnage.meta.json`
      counts + the list of unresolved codes, so the coverage number is reproducible.
3. `01_data/00_derived/epc_decode_batch1_banded_20260919.csv`
      the 260 part numbers of the batch-1 decode with a resolved band, band_count and ambiguous.

Sources, and how confidence is set
----------------------------------
* **Duncan Young / ITUK PMS brake deck**, slide 14 "Appendix: Service Intervals" —
  `01_data/90_INBOX/_ituk_brake_spa_20260915/pptx_dump.txt`.
* **René Paul / GIDSS workshop-manual prints** —
  `01_data/03_PMS/service_schedules/GIDSS_maint_{N,F}_MY{14,24}.pdf`.
  Jerome's rule (2026-09-18): René's files are the reference unless a distributor says different.
* Supporting only, used when the two above are silent and marked as such in `evidence_source`:
  the JP VIN register series -> GVW map (`01_data/07_UIO/vin/build_vin_register.py`,
  `model_dimension.csv`) and the EPC family / code pairings in the decode itself.

  high       quoted by name in the Duncan deck or a René GIDSS header, or a measured register
             value and an EPC family that agree.
  medium     one supporting source (a measured register value, or a consistent EPC pairing).
  low        indirect only (a code that shares an EPC edition with a known code).
  unresolved the sources do not say. The band is left blank on purpose — no guess.

Reads : 01_data/00_derived/epc_decode_batch1_20260919.json
        01_data/00_derived/epc_decode_worklist.csv      (billed euro per part number)
Writes: the three files above.

Run: python 03_analytics/Isuzu/prism/scripts/build_model_code_to_tonnage.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ROOT / "01_data" / "00_derived"
PRISM_DATA = ROOT / "03_analytics" / "Isuzu" / "prism" / "data"

DECODE = DERIVED / "epc_decode_batch1_20260919.json"
WORKLIST = DERIVED / "epc_decode_worklist.csv"
TABLE_CSV = PRISM_DATA / "model_code_to_tonnage.csv"
TABLE_META = PRISM_DATA / "model_code_to_tonnage.meta.json"
BANDED_CSV = DERIVED / "epc_decode_batch1_banded_20260919.csv"

sys.path.insert(0, str(ROOT / "03_analytics" / "Isuzu" / "prism"))
from modules import vehicle_bands  # noqa: E402

# The bands this table is allowed to write. Derived from the one authored map
# (`data/series_to_band.csv`, read through `modules/vehicle_bands.py`) instead of being typed
# out here, so this list cannot drift away from the map again. `"other"` is added explicitly
# because it is this file's own name for a code the map marks `not_in_scope` — see
# `_load_table` — and the map holds no band by that name.
#
# The map's *candidate* bands for a code still awaiting a ruling are added as well. They are not
# bands this table invents: the map already carries them for that code, and `_load_table` holds
# a quarantined code's band at whatever this file last wrote, so the vocabulary has to be able
# to name it. Without this, holding a pending band would trip the guard below.
def _vocabulary() -> list[str]:
    out = [vehicle_bands.BAND_LCV, vehicle_bands.BAND_N35, vehicle_bands.BAND_N50,
           vehicle_bands.BAND_N75, vehicle_bands.BAND_F, "other"]
    for code in vehicle_bands.pending_ruling_codes():
        for band in vehicle_bands.quarantine_candidates(code):
            if band not in out:
                out.append(band)
    return out


BANDS = _vocabulary()
BANDS_FILE = "03_analytics/Isuzu/prism/scripts/build_model_code_to_tonnage.py"
VOCABULARY_FILE = "03_analytics/Isuzu/prism/modules/vehicle_bands.py " \
                  "(from 03_analytics/Isuzu/prism/data/series_to_band.csv)"

# Evidence strings, kept once so the CSV rows stay short and consistent.
DUNCAN = "Duncan Young / ITUK PMS brake deck, slide 14 'Appendix: Service Intervals' — pptx_dump.txt"
RENE_N24 = "René Paul / GIDSS GIDSS_maint_N_MY24.pdf (01_data/03_PMS/service_schedules/)"
RENE_N14 = "René Paul / GIDSS GIDSS_maint_N_MY14.pdf"
RENE_F24 = "René Paul / GIDSS GIDSS_maint_F_MY24.pdf"
REGISTER = "JP VIN register series -> GVW map — 01_data/07_UIO/vin/build_vin_register.py (SERIES_GVW_T), model_dimension.csv"
EPC = "EPC decode — the model string the EPC returns for this part number (epc_decode_batch1_20260919.json)"
XREF = "Isuzu genuine/BVP cross-reference vehicle_model column — 01_data/00_derived/genuine_bvp_crossref.csv"
V20 = "06_uio/_CURRENT/V20_SPEC.md §Problem 6 'The Isuzu weight ladder'"
KS = "KS International aftermarket catalogue model index — 02_dashboards/Data/90_INBOX/ks_pms_scan_20260818/models.json"

# ---------------------------------------------------------------------------------------------
# The table. One tuple per model code:
#   (band, weight_class_label, evidence_source, evidence_quote, confidence)
# ---------------------------------------------------------------------------------------------
N35_LABEL = "3.5 t GVW (N35 Grafter)"
N75_LABEL = "7.5 t class (N50 / N55 / N62 / N65 / N75 ladder)"
F_LABEL = "F&G series medium / heavy"
LCV_LABEL = "LCV — D-Max class pickup / SUV"
OTHER_LABEL = "outside the four ISZE bands (bus, heavy C&E, industrial or export-only name)"

# ---------------------------------------------------------------------------------------------
# The table is NO LONGER held here.
#
# Until 2026-09-23 this file carried its own `TABLE` of model code -> band, which disagreed with
# the N-series bander's table: this one put `NMR` on the 7.5 t band while its own weight label on
# the same row read 5.5 t, and it put `NKR` at 3.5 t where the retired probe put it at 5.5 t.
#
# The single authored source is now `03_analytics/Isuzu/prism/data/series_to_band.csv`, read
# through `modules/vehicle_bands.py`. This file keeps NO dictionary. To change a mapping, edit the
# CSV - not this script.
# ---------------------------------------------------------------------------------------------
N35_LABEL = "3.5 t GVW (N35 Grafter)"
N75_LABEL = "7.5 t class (N50 / N55 / N62 / N65 / N75 ladder)"
F_LABEL = "F&G series medium / heavy"
LCV_LABEL = "LCV - D-Max class pickup / SUV"
OTHER_LABEL = "outside the four ISZE bands (bus, heavy C&E, industrial or export-only name)"

TABLE: dict[str, tuple[str, str, str, str, str]] = {}


def _load_table() -> dict[str, tuple[str, str, str, str, str]]:
    """Every code the canonical map knows, in this file's own column order."""
    out: dict[str, tuple[str, str, str, str, str]] = {}
    for code, r in vehicle_bands.load_map().items():
        band = (r.get("tonnage_band") or "").strip()
        if band == vehicle_bands.UNRESOLVED:
            band = ""
        elif band == vehicle_bands.NOT_IN_SCOPE:
            band = "other"
        out[code] = (
            band,
            (r.get("weight_label") or "").strip(),
            (r.get("evidence_source") or "").strip(),
            (r.get("evidence_quote") or "").strip(),
            (r.get("confidence") or "").strip(),
        )
    return out


TABLE = _load_table()


# ---------------------------------------------------------------- the pending-ruling hold
# A code the map marks `pending_ruling` has no settled band. Its map band is an interim value,
# and this table must not move it: writing a band onto a row that carries a code awaiting a
# ruling *is* the ruling, taken as a side effect of a rebuild. So for those codes the values this
# file already carries are held unchanged, and the label says the value is interim.
#
# What is held, and what is not:
#   band, confidence   held from the previous build. Both are statements about where the code
#                      currently sits and how well that is sourced; neither may move for a parked
#                      code. Confidence is held for the same reason as the band - it was
#                      `unresolved` in the map only *because* the map's band was unresolved, and
#                      carrying it forward is what stops the row reading "band 7.5 t, unresolved".
#   label              regenerated from the held band, not held. The original defect was a row
#                      whose band column and weight label told different stories; rebuilding both
#                      from the held value means they cannot disagree again.
#   source, quote      taken from the map and stamped with the quarantine note, so the evidence
#                      stays current and a reader cannot miss that the value is not settled.
#
# The two files deliberately disagree for `NMR` and `NMR85`: the map holds the European interim
# value the shipped pipeline uses (5.5 t for `NMR`, 7.5 t for `NMR85`), while this table keeps the
# 7.5 t it has always written for both. That divergence is the point - the map must not be moved
# to match this table either, because downstream band files read the map and would shift with it.
# Do not reconcile them by editing either file; reconcile them by ruling on `NMR`.
def _apply_pending_hold(tbl: dict[str, tuple[str, str, str, str, str]]) -> dict[str, tuple[str, str, str, str, str]]:
    """Keep each pending-ruling code's existing band and confidence, whatever the map now says."""
    held: dict[str, tuple[str, str, str, str, str]] = {}
    pending = [c for c in vehicle_bands.pending_ruling_codes() if c in tbl]
    if not pending or not TABLE_CSV.is_file():
        return tbl
    try:
        with open(TABLE_CSV, encoding="utf-8-sig", newline="") as fh:
            previous = {r["model_code"]: r for r in csv.DictReader(fh)}
    except (OSError, KeyError):
        return tbl
    notes = []
    for code in sorted(pending):
        prev = previous.get(code)
        if not prev:
            continue
        prev_band = (prev.get("tonnage_band") or "").strip()
        prev_conf = (prev.get("confidence") or "").strip()
        band, _label, source, quote, conf = tbl[code]
        if prev_band == band and prev_conf == conf:
            continue
        held_label = (vehicle_bands.BAND_LABEL.get(prev_band, prev_band) if prev_band
                      else "no band - awaiting ruling")
        cands = " | ".join(vehicle_bands.quarantine_candidates(code)) or "(none recorded)"
        note = (f"PENDING RULING: this table keeps the band it already carried "
                f"({prev_band or 'none'}) because {code} awaits a ruling; the canonical map's "
                f"interim value is {band or 'none'}. Candidates: {cands}.")
        held[code] = (prev_band, f"{held_label} — INTERIM, PENDING RULING",
                      source, f"{quote} || {note}".strip(" |"), prev_conf)
        notes.append(f"{code}: held at band {prev_band or 'none'} / confidence "
                     f"{prev_conf or 'none'} (map says {band or 'none'} / {conf or 'none'})")
    if notes:
        print("  pending-ruling hold:")
        for n in notes:
            print(f"    {n}")
    return {**tbl, **held}


TABLE = _apply_pending_hold(TABLE)


def _assert_bands_in_vocabulary() -> None:
    """Fail loudly if the map can produce a band this file's own list cannot name.

    The failure this guards against was silent: the file wrote a `tonnage_band` value that was
    not in its own declared list, and nothing complained. A build that stops is worth more than
    a build that quietly invents a rung, so this raises rather than warning.
    """
    missing = sorted({row[0] for row in TABLE.values() if row[0] and row[0] not in BANDS})
    if not missing:
        return
    offending = [(c, row[0]) for c, row in sorted(TABLE.items()) if row[0] in missing]
    lines = "\n".join(f"    {c} -> {b!r}" for c, b in offending[:20])
    if len(offending) > 20:
        lines += f"\n    ... and {len(offending) - 20} more"
    raise RuntimeError(
        "tonnage_band vocabulary mismatch.\n"
        f"The map names band(s) {missing!r}, which this file's declared vocabulary cannot "
        f"express.\n"
        f"Codes and bands that would have been written:\n{lines}\n"
        f"The vocabulary is declared as BANDS in {BANDS_FILE} and comes from "
        f"{VOCABULARY_FILE}.\n"
        "Add the missing band there (or to the authored map if the map itself is wrong) "
        "before this table is written; do not let it be filed onto a rung that does exist."
    )


_assert_bands_in_vocabulary()

# The per-code `add()` calls that used to sit here are gone. The table is built from the
# canonical map in `modules/vehicle_bands.py` (`data/series_to_band.csv`), so this file holds
# no dictionary of its own. Edit the CSV to change a mapping.

# ---------------------------------------------------------------- deliberately unresolved
UNRESOLVED_NOTES = {
    "NHR": "EPC returns NHR only alongside NKR ('1997.5-2007 NHR/NKR TAIWAN', crossref "
           "'NHR,NKR,NLR,NMR'). NKR is 3.5 t in the register; the pairing is not proof, and neither "
           "Duncan nor René names NHR.",
    "NJR": "EPC 'NJR/NKR 13.0 - 14.0' and 'NJR/NKR 23.0 - 24.0' span two weight ranges, so the "
           "pairing with NKR does not settle it.",
    "NJS": "Appears only as 'NJS/NKS' at two different ranges. No source names it.",
    "NK": "Appears only as 'NJ/NK/NL/NMR-HYBRID'. Grouped with NMR (above it) but also with NJ/NL, "
          "which have no source.",
    "NKS": "Appears only as 'NJS/NKS'. No source names it.",
    "NL": "Appears only as 'NJ/NK/NL/NMR-HYBRID'. No source names it.",
    "NJ": "Appears only as 'NJ/NK/NL/NMR-HYBRID'. No source names it.",
    "NLS": "René N_MY14 p1 puts 'NLR85/NLS85/NMR85/NNR85/NPR85' on one schedule, which spans 3.5 t "
           "to 7.5 t and therefore cannot separate NLS from NLR or NPR.",
    "NMS": "Appears only as 'NLS/NMS'. No source names it.",
    "NMS85": "EPC '2012 NMR85 RHD...' pairs it with NMR85 only; NMS itself is not named in either "
             "source.",
    "NNS": "Appears only as 'NNS/NPS', and NPS is itself only resolved by pairing. Two pairings "
           "deep is not evidence.",
    "NN": "EPC '15- NN/NP/NQR EURO5,5B+,6 LHD' groups NN with NQR, but the EPC also carries bare "
          "'NN' and 'NP' prefixes, so the grouping is not a stored code we can bind.",
    "NP": "Same as NN — grouped with NQR in the EPC, but carried as a bare prefix elsewhere.",
    "NQS": "Appears once, as '2026 NPS/NQS AUST/NZ 26.0 -'. No source names it.",
    "NHS": "Appears as 'NHS 11.0 - 12.0' ... 'NHS 25.0 -' — seven ranges across the whole weight "
           "span, so the code does not identify one class.",
    "QKR": "Appears only in crossref pairings ('N*R,QKR', 'NKR,QKR,TBR,TFR,TFS'). No source on disk "
           "states what QKR is.",
    "QLR": "EPC '2021 QLR/QMR LHD 21.0 -'. No source on disk states what QLR/QMR are.",
    "QMR": "EPC '2021 QLR/QMR LHD 21.0 -'. No source names it.",
    "PHR": "EPC '2018 PHR INDONESIA 18.0 - 21.0'. Export-market code, not named in either source.",
    "TBR": "Appears only in crossref pairings with TF*/PHR/QKR. Not named in either source.",
    "CHR": "Appears only in crossref 'EXZ,CHR,CVR,CX*,FV*'. Not named in either source.",
    "PFR": "Appears only in crossref 'PFR,TBR,TF*'. Not named in either source.",
    "FRD": "Appears only in crossref 'FRD,FRR,FTR,FVR' — a one-row variant of FRR. Held unresolved "
           "rather than assumed equal to FRR.",
    "UE": "Appears once as crossref 'UE*'. No source names it.",
    "UES": "Appears once as crossref 'UES'. No source names it.",
    "TF": "A wildcard prefix in the crossref ('TF*'), not a model code.",
    "NQ": "A wildcard prefix in the crossref ('NQ*'), not a model code.",
    "NQ ": "A wildcard prefix in the crossref ('NQ*'), not a model code.",
    "UB ": "A wildcard prefix ('UB*').",
    "UC": "A wildcard prefix in the crossref ('UC*'), not a model code.",
    "CX": "A wildcard prefix in the crossref ('CX*'), not a model code.",
    "CY": "A wildcard prefix in the crossref ('CY*'), not a model code.",
    "EX": "A wildcard prefix in the crossref ('EX*'), not a model code.",
    "FR": "A wildcard prefix in the crossref ('FR*'), not a model code.",
    "FS": "A wildcard prefix in the crossref ('FS*'), not a model code.",
    "FT": "A wildcard prefix in the crossref ('FT*'), not a model code.",
    "FV": "A wildcard prefix in the crossref ('FV*'), not a model code.",
    "FX": "A wildcard prefix in the crossref ('FX*'), not a model code.",
    "FY": "A wildcard prefix in the crossref ('FY*'), not a model code.",
    "GV": "A wildcard prefix in the crossref ('GV*'), not a model code.",
    "GX": "A wildcard prefix in the crossref ('GX*'), not a model code.",
    "GXR": "Appears once in crossref 'FXR,FXZ,GXR,GXZ'. No source names it.",
    "CV": "A wildcard prefix in the crossref ('CV*'), not a model code.",
    "R": "A stray single letter in the crossref vehicle_model column, not a model code.",
    "S": "A stray single letter in the crossref vehicle_model column, not a model code.",
    "D": "A stray single letter in the crossref vehicle_model column, not a model code.",
    "E": "A stray single letter in the crossref vehicle_model column, not a model code.",
    "Z": "A stray single letter in the crossref vehicle_model column, not a model code.",
    "X2": "A drive-configuration token ('X2'/'X4') in the crossref, not a model code.",
    "X4": "A drive-configuration token ('X2'/'X4') in the crossref, not a model code.",
    "R4": "A stray token in the crossref, not a model code.",
    "RG": "Appears in the crossref vehicle_model ('TFR,TFS (RT,RG)') and names the D-Max pickup "
          "platform generation, but no source states a GVW for it as a code.",
    "RT": "Same as RG — a pickup platform generation, quoted only as part of a crossref pairing.",
}

# ---------------------------------------------------------------- parsing
CODE_RE = re.compile(r"^[A-Z]{2,5}\d{0,3}$")
# Words that look like codes but are markets / emission levels / features / fragments.
STOP = {
    "AIOS", "AIR", "ALAND", "AMER", "AMERI", "AND", "AST", "AUST", "AUSTR", "BRAKE", "BUS", "CAB",
    "CENTR", "CHASS", "CHEV", "CHEVR", "CHINA", "CNG", "COMP", "COMPO", "DOC", "EAST", "EGYPT",
    "ESIA", "EU", "EU2", "EU4", "EU5", "EURO1", "EURO2", "EURO3", "EURO4", "EURO5", "EURO6",
    "EUROP", "EV", "EVSC", "EXC", "EXP", "FC", "FICAT", "FINAL", "FORWA", "FRAME", "GAS", "GASOL",
    "GM", "HD", "HOLDE", "HYBRI", "HYDRA", "INDIA", "INDON", "INE", "ION", "IRAN", "IS", "ISRAE",
    "JIANG", "KENYA", "LDWS", "LHD", "LNG", "LONG", "MALAY", "MEXIC", "MHEV", "MIDDL", "MM", "ND",
    "NENT", "NEW", "NEWZE", "NORTH", "NZ", "OLET", "PARTS", "PHILI", "PPINE", "RD", "REFLE",
    "RETAR", "RHD", "RUNG", "RUSSI", "SCAB", "SGL", "SHORT", "SIA", "SOU", "SOUTH", "SPACE",
    "SPECI", "STEPS", "STRIP", "TAIWA", "TERM", "THAI", "THAIL", "TIS", "ULIC", "US", "USA",
    "VC17", "VC19", "VIETN", "WB", "WEDGE", "XD", "XI", "ZEALA", "AL", "AM", "CA", "DER", "DIESE",
    "HK1", "JNLT05", "JNLT09", "LT434", "MS1", "MR1", "MODEL", "MODELS", "SERIES", "ENGINE",
    "TRUCKS", "BUSES", "PASSENGER", "VEHICLE", "PICK", "UP", "SUV", "INDUSTRIAL", "CYLINDER",
    "MARINE", "COMPONENT", "FORWARD", "GRAFTER", "ELF", "CATIONS", "CATION", "ENG", "EXT", "GL",
    "LIC", "MINUS", "NOM", "PLUS", "PTO", "RECTION", "SION", "SPEC", "STOR", "TION", "TURK",
    "TURKE", "ABS", "ECU", "EPB", "LDW",
}


def parse_codes(text: str) -> list[str]:
    """Leading model code(s) of an EPC model string.

    The EPC prefixes each model string with a model year or a year range — '2022 TFR/TFS...',
    '2009-2011 TFR/TFS(RHD)EXP 09.0 - 11.0', '19-FRR/FSR(LHD)EU', '(990-)NKR(RHD)THAILAND',
    '13FRR(LHD)SPACECAB', '1997.5-2007 NHR/NKR TAIWAN', '085-110 TFR/TFS(CHEV.) HOLDEN'. All of
    those have to come off before the code is at the front, so this strips in a loop rather than
    once.
    """
    t = str(text or "").strip().upper()
    for _ in range(6):
        before = t
        t = re.sub(r"^\(?\d{2,4}\.\d\s*-?\s*", "", t)      # '1997.5-2007 '
        t = re.sub(r"^\(?\d{2,4}\s*\)?\s*-+\s*", "", t)    # '2022 ' / '19-' / '(990-)' / '085-110 '
        t = re.sub(r"^\d{2,4}\s+(?=[A-Z])", "", t)         # '2022 TFR' -> 'TFR'
        t = re.sub(r"^\(?\d{2,4}\)?\s*", "", t)            # a bare leading year with no dash
        t = re.sub(r"^\d{2,3}(?=[A-Z]{2})", "", t)         # '13FRR(' -> 'FRR('
        if t == before:
            break
    tok = t.split("(", 1)[0].split()[0] if t else ""
    tok = tok.replace("-", "/")
    out: list[str] = []
    for part in tok.split("/"):
        part = part.strip()
        if not part or part in STOP:
            continue
        if CODE_RE.match(part):
            out.append(part)
    return out


def band_for(code: str) -> tuple[str, str, str, str, str]:
    """(band, label, source, quote, confidence) — unresolved when the canonical map is silent."""
    row = TABLE.get(code)
    if row:
        return row
    note = UNRESOLVED_NOTES.get(code, "Not named in Duncan slide 14 or in any René GIDSS sheet, and "
                                     "no measured register value or consistent EPC pairing found.")
    return ("", "not stated in the two authoritative sources",
            "no source — left blank on purpose", note, "unresolved")


def collect_codes() -> list[str]:
    """Every code the table must carry: the EPC decode plus the crossref vehicle_model column."""
    codes: set[str] = set(TABLE)
    dec = json.load(open(DECODE, encoding="utf-8"))
    for r in dec:
        for m in r.get("models", []):
            codes.update(parse_codes(m))
    xr = list(csv.DictReader(open(DERIVED / "genuine_bvp_crossref.csv", encoding="utf-8-sig")))
    for r in xr:
        vm = str(r.get("vehicle_model") or "").upper()
        # vehicle_model values look like 'NPR,NQR' / 'TF*,UBS,UC*' / 'TFR,TFS (190, RT)' /
        # 'NHR,NKR,NLR,NMR,\nQKR'. Strip punctuation and the newline before splitting, or 'RT)'
        # and '(190' never match and real codes go missing.
        vm = re.sub(r"[()\[\]{}\n\r]", " ", vm)
        for tok in re.split(r"[,\s]+", vm):
            for p2 in tok.replace(".", ",").split(","):
                p2 = p2.strip().rstrip("*")
                if not p2 or p2 in STOP:
                    continue
                if CODE_RE.match(p2):
                    codes.add(p2)
    # Bus and pickup platform codes the task named, which live only in the EPC family labels
    # ('BUSES LT, LV', 'TFR,TFS (190, RT)').
    codes.update({"LT", "LV", "RT", "RG", "LF", "MR", "GR"})
    # a few stray one-letter / token entries the crossref carries
    codes.update({"TF", "NQ", "UB", "UC", "CX", "CY", "EX", "FR", "FS", "FT", "FV", "FX", "FY",
                  "GV", "GX", "CV", "R", "S", "D", "E", "Z", "X2", "X4"})
    codes.discard("")
    return sorted(codes)


def write_table() -> dict:
    codes = collect_codes()
    PRISM_DATA.mkdir(parents=True, exist_ok=True)
    rows = []
    resolved = unresolved = 0
    unresolved_codes, resolved_codes = [], []
    for c in codes:
        band, label, source, quote, conf = band_for(c)
        if conf == "unresolved" or not band:
            unresolved += 1
            unresolved_codes.append(c)
        else:
            resolved += 1
            resolved_codes.append(c)
        rows.append({"model_code": c, "tonnage_band": band, "weight_class_label": label,
                     "evidence_source": source, "evidence_quote": quote, "confidence": conf})
    # The guard above checks the map; this checks the rows actually about to be written, which
    # is the same question asked one step later and costs nothing. It has to run BEFORE the
    # file is opened, or a build that raises would still have half-written its own output.
    # A build that stops is worth more than a build that quietly invents a rung.
    stray = sorted({r["tonnage_band"] for r in rows
                    if r["tonnage_band"] and r["tonnage_band"] not in BANDS})
    if stray:
        names = ", ".join(f"{r['model_code']} -> {r['tonnage_band']!r}"
                          for r in rows if r["tonnage_band"] in stray)
        raise RuntimeError(
            f"refusing to write {TABLE_CSV.name}: the table would carry tonnage_band "
            f"{stray!r}, which is not in this file's declared vocabulary.\n"
            f"{names}\n"
            f"The vocabulary is declared as BANDS in {BANDS_FILE} and comes from "
            f"{VOCABULARY_FILE}."
        )
    with open(TABLE_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["model_code", "tonnage_band", "weight_class_label",
                                          "evidence_source", "evidence_quote", "confidence"])
        w.writeheader()
        w.writerows(rows)

    by_band = Counter(r["tonnage_band"] or "(blank)" for r in rows)
    by_conf = Counter(r["confidence"] for r in rows)
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "generated_by": "03_analytics/Isuzu/prism/scripts/build_model_code_to_tonnage.py",
        "table": str(TABLE_CSV),
        "bands": BANDS,
        "rows": len(rows),
        "resolved": resolved,
        "unresolved": unresolved,
        "by_band": dict(by_band),
        "by_confidence": dict(by_conf),
        "resolved_codes": resolved_codes,
        "unresolved_codes": unresolved_codes,
        "sources": [
            DUNCAN,
            "René Paul / GIDSS GIDSS_maint_{N,F}_MY{14,24}.pdf — 01_data/03_PMS/service_schedules/",
            REGISTER,
            "01_data/00_derived/epc_decode_batch1_20260919.json",
            "01_data/00_derived/genuine_bvp_crossref.csv",
        ],
        "rules": [
            "Jerome 2026-09-18: René's files are the reference unless a distributor says it is "
            "different. Where Duncan and René disagree, René wins and evidence_source says so.",
            "A code the sources do not name is left with an empty band and confidence=unresolved. "
            "An unresolved code is a better answer than a plausible one.",
            "The numeric suffix (75 / 85 / 87 / 88 / 90) is a generation code, not a weight: NLR "
            "appears as 85, 87 and 88 and all three are 3.5 t (Duncan slide 14 names NLR87 N35.125 "
            "and NLR88 N35.150); FRR90 and FSR90 share the suffix 90 at 11 t and 13.5 t.",
        ],
    }
    TABLE_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def write_banded() -> dict:
    """Apply the table to every part number in the batch-1 decode."""
    dec = json.load(open(DECODE, encoding="utf-8"))
    wl = list(csv.DictReader(open(WORKLIST, encoding="utf-8")))
    euro = {}
    for r in wl:
        pn = str(r["part_number"]).strip().lstrip("0") or "0"
        euro[pn] = (float(r["eur_all"] or 0), float(r["units_all"] or 0))

    rows = []
    unresolved_counter: Counter = Counter()
    seen: dict[str, dict] = {}
    for r in dec:
        pn = str(r["pn"])
        models = r.get("models", []) or []
        e, u = euro.get(pn.lstrip("0") or "0", (0.0, 0.0))
        if not models:
            # 18 of the 260 batch-1 records came back found=false with no models array. The EPC
            # could not place them on a vehicle, so no band is possible. They are kept in the file
            # with band_status=no_vehicle rather than dropped, so the count reconciles.
            rows.append({
                "pn": pn, "families": "", "models": "", "model_codes": "",
                "tonnage_band": "", "band_count": 0, "ambiguous": "True",
                "band_status": "no_vehicle_epc_not_found",
                "billed_eur_all": f"{e:.2f}", "billed_units_all": f"{u:.0f}",
                "duplicate_records": 1,
            })
            continue
        codes: list[str] = []
        for m in models:
            for c in parse_codes(m):
                if c not in codes:
                    codes.append(c)
        bands: list[str] = []
        for c in codes:
            b = band_for(c)[0]
            if b and b not in bands:
                bands.append(b)
            elif not b:
                unresolved_counter[c] += 1
        bands_sorted = sorted(bands)
        band_count = len(bands_sorted)
        if band_count == 1:
            band_str, ambiguous, status = bands_sorted[0], "False", "single_band"
        elif band_count == 0:
            band_str, ambiguous, status = "", "True", "no_band_all_codes_unresolved"
        else:
            band_str, ambiguous, status = "|".join(bands_sorted), "True", "shared"
        row = {
            "pn": pn,
            "families": "; ".join(r.get("families", []) or []),
            "models": " | ".join(models),
            "model_codes": ", ".join(codes),
            "tonnage_band": band_str,
            "band_count": band_count,
            "ambiguous": ambiguous,
            "band_status": status,
            "billed_eur_all": f"{e:.2f}",
            "billed_units_all": f"{u:.0f}",
        }
        if pn in seen:
            # The decode carries 260 records but only 250 distinct part numbers; 10 appear twice.
            # The second copy is identical in families and models for every one of them, so keep
            # the first and record the duplication instead of double-counting the euro.
            if seen[pn]["tonnage_band"] != band_str or seen[pn]["band_count"] != band_count:
                raise RuntimeError(f"duplicate PN {pn} disagrees between records — investigate")
            seen[pn]["duplicate_records"] = int(seen[pn]["duplicate_records"]) + 1
            continue
        row["duplicate_records"] = 1
        seen[pn] = row
        rows.append(row)
    rows.sort(key=lambda x: -float(x["billed_eur_all"]))
    with open(BANDED_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["pn", "families", "models", "model_codes", "tonnage_band",
                                          "band_count", "ambiguous", "band_status", "billed_eur_all",
                                          "billed_units_all", "duplicate_records"])
        w.writeheader()
        w.writerows(rows)

    # Everything reported below is PN-level, so it matches the file exactly. The loop above counts
    # records, and 10 part numbers appear twice; reporting the record counts would overstate the
    # denominator by 10 and the euro by EUR 12.7M.
    by_status: dict[str, list] = defaultdict(list)
    for r in rows:
        by_status[r["band_status"]].append(r)
    def _n(s: str) -> int:
        return len(by_status.get(s, []))
    def _e(s: str) -> float:
        return sum(float(r["billed_eur_all"]) for r in by_status.get(s, []))
    total = sum(float(r["billed_eur_all"]) for r in rows)
    return {
        "records_in_decode": len(dec),
        "pns_written": len(rows),
        "duplicate_records_collapsed": len(dec) - len(rows),
        "pns_epc_found_nothing": _n("no_vehicle_epc_not_found"),
        "pns_with_a_vehicle": len(rows) - _n("no_vehicle_epc_not_found"),
        "single_band": _n("single_band"),
        "shared": _n("shared"),
        "no_band_all_codes_unresolved": _n("no_band_all_codes_unresolved"),
        "eur_single": _e("single_band"),
        "eur_shared": _e("shared"),
        "eur_with_vehicle": _e("single_band") + _e("shared"),
        "eur_epc_found_nothing": _e("no_vehicle_epc_not_found"),
        "eur_total_distinct_pns": total,
        "top_unresolved_codes": unresolved_counter.most_common(25),
    }


def main() -> int:
    meta = write_table()
    print(f"table      : {meta['rows']} model codes -> {TABLE_CSV}")
    print(f"  resolved : {meta['resolved']}   unresolved: {meta['unresolved']}")
    print(f"  by band  : {meta['by_band']}")
    print(f"  by conf  : {meta['by_confidence']}")
    banded = write_banded()
    print(f"banded     : {banded['pns_written']} PNs -> {BANDED_CSV}")
    print(f"  records  : {banded['records_in_decode']} in decode, "
          f"{banded['duplicate_records_collapsed']} duplicate records collapsed, "
          f"{banded['pns_epc_found_nothing']} PNs the EPC found nothing for")
    print(f"  with vehicle : {banded['pns_with_a_vehicle']}  EUR {banded['eur_with_vehicle']:,.0f}")
    print(f"    single band: {banded['single_band']}  EUR {banded['eur_single']:,.0f}")
    print(f"    shared     : {banded['shared']}  EUR {banded['eur_shared']:,.0f}")
    print(f"  no vehicle   : {banded['pns_epc_found_nothing']}  "
          f"EUR {banded['eur_epc_found_nothing']:,.0f}")
    print(f"  decoded book EUR {banded['eur_total_distinct_pns']:,.0f}")
    print(f"  unresolved codes on PNs: {banded['top_unresolved_codes'][:12]}")
    meta["banded"] = banded
    TABLE_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
