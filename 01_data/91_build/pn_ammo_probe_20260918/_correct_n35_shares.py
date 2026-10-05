"""Correct uio_ld_n35_share.csv against the basis each row names, and write a before/after audit.

Authority: Jerome, 2026-09-18 — "do corrections everywhere if needed".

What was found (every number below recomputed from source, not quoted):

  IRELAND   named SIMI but carried the JP VIN number. SIMI scrap-adjusted PARC at 2025 is
            N35 464 / N75 1,038 -> 0.3089. The 0.063 is 36/570 from the JP VIN register.
  BELGIUM   register destination BE holds 49 rows, NLR 42 -> 0.8571, not 45/49 = 0.918.
  PORTUGAL  N35/N-series = 1299/1883 = 0.6899; the row divides by all 2,111 rows instead.
  CYPRUS    register NL 3.5 t = 0; the only N35-class chassis is NMR (5.5 t), which is not an
            N35. Marked unmeasured -> rate kept.
  MALTA     NMR88 9.5 t (48 units) is NOT an N35. The NMR-class count is not evidence of a
            3.5 t parc; 130 shipments. Marked unmeasured -> rate kept.
  GREECE    4 shipments, NMR 2 (5.5 t) + NPR 2 (7.5 t), zero 3.5 t, cv_std 37. Confirmed 0.0.
  GERMANY   153 / 697 = 0.2195 -> 0.220 confirmed from the Helwig bands.
  ITUK      live workbook read, 10,900 / 21,584 -> 0.5051 confirmed.
  UTI       zero NLR across 2,360 CV claim VINs, ministry table starts at 6.5-7.5 t. Confirmed 0.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PD = ROOT / "03_analytics" / "Isuzu" / "prism" / "data"
SHARE_CSV = PD / "uio_ld_n35_share.csv"
AUDIT_CSV = ROOT / "01_data" / "00_derived" / "n35_share_audit_20260918.csv"
BACKUP = PD / "uio_ld_n35_share.csv.bak_pre_ireland_fix_20260918"

before = pd.read_csv(SHARE_CSV)

# market -> (new share, new basis, evidence note)
CORRECTIONS: dict[str, tuple[float, str, str]] = {
    "IRELAND": (
        0.3089,
        "simi_bands_parc",
        "SIMI national registrations (01_data/07_UIO/isuzuregdata.xlsx sheet Sheet2, 2010-2025) "
        "convolved against the ISZE scrap-adjusted CV curve, evaluated at 2025: N35 464 of "
        "N35+N75 1,502 = 0.3089. Flow basis for reference: 663/1,963 = 0.3377; 663/(663+1300+122) "
        "= 0.3180. Basis is the parc, because the split is applied to a parc. The previous 0.063 "
        "was NOT the SIMI number: it is 36/570 from the JP VIN register (IE), which is a shipment "
        "flow of 647 trucks. Fixed 2026-09-18.",
    ),
    "BELGIUM": (
        0.8571,
        "jp_vin_shipments",
        "JP VIN register destination BE: 49 shipments, NLR 42 (all 3.5 t) -> 42/49 = 0.8571. "
        "The previous 0.918 read 45/49 but the register holds 42 NLR, 3 NMR (5.5 t), 4 NPR "
        "(7.5 t) and no F. Corrected 2026-09-18. Sample is small (49) but the wallet is almost "
        "all D-Max (LCV 9,480 vs cv_std 113) so the effect is immaterial either way.",
    ),
    "PORTUGAL": (
        0.6899,
        "jp_vin_shipments",
        "JP VIN register destination PT: N35 (NLR) 1,299 of 1,883 N-series = 0.6899. The previous "
        "0.620 divided by all 2,111 register rows, which includes 198 FRR + 30 FSR F-series (228) "
        "that are not N-series trucks. Corrected 2026-09-18. Still a shipment mix applied to a "
        "parc and still an approximation; no Portuguese parc-band source exists in the workspace.",
    ),
    "CYPRUS": (
        0.053,
        "unmeasured",
        "Unmeasured. JP VIN register destination CY holds 114 shipments and ZERO at 3.5 t: "
        "NPR 7.5 t 60, NNR 6.5 t 48, NMR 5.5 t 6. NMR is not an N35 (N35 = NLR/NMR 3.5 t only). "
        "There is no parc basis for Cyprus. The current rate is kept rather than guessing; a "
        "measured or distributor-confirmed figure is needed before this market is split.",
    ),
    "MALTA": (
        0.369,
        "unmeasured",
        "Unmeasured. JP VIN register destination MT holds 130 shipments: NPR75 73, NMR88 / NMR85 "
        "48, FRR 9. NMR88 is a 9.5 t truck, not a 3.5 t N35, so the NMR-class count is NOT "
        "evidence of a 3.5 t parc. The previous 0.369 rested on reading 48 NMR as N35. No parc "
        "basis exists for Malta. The current rate is kept rather than guessing.",
    ),
    "GREECE": (
        0.0,
        "jp_vin_shipments",
        "Confirmed zero. JP VIN register destination GR holds 4 shipments: NMR85 2 (5.5 t) and "
        "NPR75 2 (7.5 t). No 3.5 t truck at all, and cv_std is 37 units. Nothing to split.",
    ),
    "GERMANY": (
        0.220,
        "helwig_parc_bands",
        "Confirmed. Helwig Schmitt parc overview at 31/12/2025 (mail 2026-06-11 from Sebastian "
        "Mueller; on disk 01_data/90_INBOX/_isd_std_mail_20260818/attachments/"
        "2026-06-11_ISD_Fahrzeugbestand_-_Basis_-_Uebersicht_D_.xlsx): Nfz 787 = <=3.40 t 25 + "
        "3.41-3.50 t 153 + 3.51-5.50 t 79 + 5.51-6.50 t 147 + 6.51-7.50 t 318 + 7.51-12.0 t 35. "
        "The 3.41-7.50 t block is 697 and 153/697 = 0.2195, so 0.220 stands.",
    ),
    "ITUK": (
        0.5051,
        "workbook_2b",
        "Confirmed. Live read from the UIO workbook sheet '2. Vehicle Volume' section B: N35 "
        "10,900 of 21,584 N-series. The live read always overrides this value.",
    ),
    "UTI": (
        0.0,
        "cv_claims_plus_ministry",
        "Confirmed zero. 2,360 distinct CV claim VINs (Dec 2023-Mar 2026): NPR75 895, FRR90 817, "
        "FSR90 627, and zero NLR/NMR/NKR. The Israeli Ministry of Transport band table starts at "
        "6.5-7.5 t. No 3.5 t truck exists in the market.",
    ),
}

after = before.copy()
rows = []
for i, r in before.iterrows():
    code = str(r["distributor_code"]).strip().upper()
    if code not in CORRECTIONS:
        rows.append({"distributor_code": code, "before": r["n35_share"], "after": r["n35_share"],
                     "basis_before": r["basis"], "basis_after": r["basis"],
                     "change": "unchanged - no correction defined"})
        continue
    new_share, new_basis, note = CORRECTIONS[code]
    after.at[i, "n35_share"] = new_share
    after.at[i, "basis"] = new_basis
    after.at[i, "evidence_note"] = note
    rows.append({
        "distributor_code": code,
        "before": r["n35_share"], "after": new_share,
        "basis_before": r["basis"], "basis_after": new_basis,
        "change": ("CHANGED" if abs(float(r["n35_share"]) - new_share) > 1e-12 else
                   "base re-stated (value held)" if r["basis"] != new_basis else "unchanged"),
    })

audit = pd.DataFrame(rows)
audit["cv_std_before"] = [round(0.5 * (1 + b), 4) for b in audit["before"]]
audit["cv_std_after"] = [round(0.5 * (1 + a), 4) for a in audit["after"]]
audit["expected_demand_move_pct"] = (100 * (audit["cv_std_after"] / audit["cv_std_before"] - 1)).round(2)

if not BACKUP.exists():
    shutil.copy2(SHARE_CSV, BACKUP)
    print(f"backup written -> {BACKUP.name}")

after.to_csv(SHARE_CSV, index=False)
audit.to_csv(AUDIT_CSV, index=False)

pd.set_option("display.width", 200)
print(audit[["distributor_code", "before", "after", "basis_before", "basis_after",
             "cv_std_before", "cv_std_after", "expected_demand_move_pct", "change"]]
      .to_string(index=False))
print()
print(f"written -> {SHARE_CSV}")
print(f"audit   -> {AUDIT_CSV}")
print()
print("NOTE the move column above is the cv_std visit-rate move on the cv slice only. The realised")
print("move on total expected demand is smaller, because f_series and LCV are untouched.")
