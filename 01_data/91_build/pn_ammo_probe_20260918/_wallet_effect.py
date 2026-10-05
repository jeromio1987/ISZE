"""What the corrected shares would do to each market's target wallet — computed, not written.

wallet_waterfall.csv is locked (Jerome 2026-09-17) and known overstated, so this does NOT rebuild it.
It only states the direction and size of the change so the effect is on the record.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
PD = ROOT / "03_analytics" / "Isuzu" / "prism" / "data"
DER = ROOT / "01_data" / "00_derived"

R = pd.read_csv(PD / "gps_model_targets.csv").set_index("model_group")["target_eur_per_vehicle"]
R35, R75, RF, RLCV = (float(R["N35_Grafter"]), float(R["N75_N50_N62"]),
                      float(R["F_Series_MD"]), float(R["LCV_D_Max"]))
b = pd.read_csv(PD / "uio_by_model_bucket.csv").set_index("distributor_code")
sh = pd.read_csv(PD / "uio_ld_n35_share.csv")
new = dict(zip(sh.distributor_code, sh.n35_share))

# the shares that were in place before this session's correction
OLD = {"ITUK": 0.5051, "UTI": 0.0, "PORTUGAL": 0.62, "MALTA": 0.369, "GERMANY": 0.22,
       "IRELAND": 0.063, "BELGIUM": 0.918, "CYPRUS": 0.053, "GREECE": 0.0}


def wallet(db: str, s: float) -> float:
    cv = float(b.loc[db, "cv_std_uio"]); fs = float(b.loc[db, "f_series_uio"])
    lcv = float(b.loc[db, "lcv_uio"])
    return cv * s * R35 + cv * (1 - s) * R75 + fs * RF + lcv * RLCV


rows = []
w = pd.read_csv(DER / "wallet_waterfall.csv")
w25 = w[w.year == 2025].set_index("distributor_code")
for db, s_old in OLD.items():
    if db not in b.index:
        continue
    s_new = float(new.get(db, s_old))
    wo, wn = wallet(db, s_old), wallet(db, s_new)
    cap = float(w25.loc[db, "captured_total_eur"]) if db in w25.index else float("nan")
    rows.append({
        "market": db, "share_old": s_old, "share_new": round(s_new, 4),
        "wallet_old": round(wo), "wallet_new": round(wn),
        "wallet_move_pct": round(100 * (wn / wo - 1), 2) if wo else 0,
        "cover_old_pct": round(100 * cap / wo, 1) if wo else None,
        "cover_new_pct": round(100 * cap / wn, 1) if wn else None,
    })
d = pd.DataFrame(rows).sort_values("wallet_move_pct")
print("Target-wallet effect of the corrected shares (locked waterfall NOT rebuilt):")
print(d.to_string(index=False))
print()
print("network wallet old:", f"{d.wallet_old.sum():,.0f}", "-> new:", f"{d.wallet_new.sum():,.0f}",
      f"({100*(d.wallet_new.sum()/d.wallet_old.sum()-1):.2f}%)")
