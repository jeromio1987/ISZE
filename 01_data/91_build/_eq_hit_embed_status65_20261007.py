"""Embed the 65 status-only hits harvested 2026-10-07 and finalize partial results."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DER = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
MERGE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\91_build\_eq_hit_merge_harvest_20261007.py")

# pn, eq_total, catalog  (all FOUND / ui_status)
ROWS = [
    ("0281612900", 99, "11113 - 080-CXY(AUSTRALIA)JNLT05/EURO5 08.0 -"),
    ("0402108280", 68, "11145 - 2008- FXZ (RHD) 08.0 - 16.0"),
    ("0410106200", 71, "11102 - 2008- FRR(RHD)SPACECAB EURO2/4 08.0 - 12.0"),
    ("5095031110", 246, "10510 - CXK/CXL/CXM/CXZ 86.0 - 88.0"),
    ("5096300240", 42, "50330 - 1985-19923KA1/3KB1/3KC1DOM/EXP 85.0 - 92.0"),
    ("5098200170", 313, "11395 - 2011- FRR(RHD)EURO1 11.0 -"),
    ("5132120681", 8, "51052 - 1977-1991 4BA1 ENG DOM/EXP 77.0 - 91.0"),
    ("5132600090", 11, "10503 - HTS/HTW 84.0 - 92.0"),
    ("5136711400", 1, "50798 - 1994- 4LB1/C1/E1/E2 DOM/EXP 93.0 -"),
    ("5137130111", 6, "51053 - 1977-1980 C330 ENG DOM/EXP 77.0 - 80.0"),
    ("5154190360", 29, "10510 - CXK/CXL/CXM/CXZ 86.0 - 88.0"),
    ("5863019370", 1, "50844 - 95- 3YA1/B1/C1/E1 95.0 -"),
    ("5873111094", 4, "51505 - 2014- 4HK1 TIER4/STAGE 4 14.0 -"),
    ("5873112423", 2, "52029 - 2022- 4HK1 EGR-FREE STAGE 2 22.0 -"),
    ("5878156420", 1, "50798 - 1994- 4LB1/C1/E1/E2 DOM/EXP 93.0 -"),
    ("5878177930", 3, "51585 - 2015- 4JJ1 TIER4/STAGE 4 15.0 -"),
    ("5878184120", 1, "51427 - 12- 4LE2 TIER4/STAGE 3B 51658 12.0 -"),
    ("7474997754", 4, "12149 - 2024 FRR/FSR(LHD)EU 24.0 - 25.0"),
    ("7475007390", 36, "52096 - 2025 NPR-HD/XD DIESEL USA 25.0 -"),
    ("7475007934", 11, "52122 - 2024 NPR RHD EUROPE 24.0 -"),
    ("7475031480", 47, "12192 - FSR 25.0 -"),
    ("7475034281", 5, "12149 - 2024 FRR/FSR(LHD)EU 24.0 - 25.0"),
    ("7475407401", 3, "52210 - 2026 NPR LHD EUROPE 26.0 -"),
    ("7551812540", 47, "12191 - FRR 25.0 -"),
    ("7551830780", 40, "12149 - 2024 FRR/FSR(LHD)EU 24.0 - 25.0"),
    ("7551844050", 4, "52120 - 2024 NLR/NMR RHD EUROPE 24.0 -"),
    ("7551884350", None, "52122 - 2024 NPR RHD EUROPE 24.0 -"),
    ("7551930810", None, "52120 - 2024 NLR/NMR RHD EUROPE 24.0 -"),
    ("7551934310", 8, "52122 - 2024 NPR RHD EUROPE 24.0 -"),
    ("7551939210", 7, "52120 - 2024 NLR/NMR RHD EUROPE 24.0 -"),
    ("7551950511", 20, "12191 - FRR 25.0 -"),
    ("7551993760", 5, "12149 - 2024 FRR/FSR(LHD)EU 24.0 - 25.0"),
    ("7552005290", 54, "12191 - FRR 25.0 -"),
    ("7552006820", 49, "12149 - 2024 FRR/FSR(LHD)EU 24.0 - 25.0"),
    ("7552029903", 4, "12149 - 2024 FRR/FSR(LHD)EU 24.0 - 25.0"),
    ("7552029913", 4, "12149 - 2024 FRR/FSR(LHD)EU 24.0 - 25.0"),
    ("7552034870", 2, "50798 - 1994- 4LB1/C1/E1/E2 DOM/EXP 93.0 -"),
    ("7552072640", 11, "52122 - 2024 NPR RHD EUROPE 24.0 -"),
    ("7552072720", 11, "52122 - 2024 NPR RHD EUROPE 24.0 -"),
    ("7552072730", 11, "52122 - 2024 NPR RHD EUROPE 24.0 -"),
    ("7552072760", 11, "52122 - 2024 NPR RHD EUROPE 24.0 -"),
    ("7552084830", 32, "12218 - CVR 25.0 -"),
    ("7552084840", 14, "52120 - 2024 NLR/NMR RHD EUROPE 24.0 -"),
    ("7552097700", 9, "52122 - 2024 NPR RHD EUROPE 24.0 -"),
    ("7552132490", 4, "12149 - 2024 FRR/FSR(LHD)EU 24.0 - 25.0"),
    ("7552162303", 2, "52122 - 2024 NPR RHD EUROPE 24.0 -"),
    ("7552190830", 3, "51585 - 2015- 4JJ1 TIER4/STAGE 4 15.0 -"),
    ("7552230151", 4, "52207 - 2026 NLR/NMR RHD EUROPE 26.0 -"),
    ("7552230152", 18, "12230 - 2026 FRR/FSR(LHD)EUROPE 26.0 -"),
    ("7552243771", 7, "52122 - 2024 NPR RHD EUROPE 24.0 -"),
    ("7552243781", 7, "52122 - 2024 NPR RHD EUROPE 24.0 -"),
    ("7552252960", 18, "12149 - 2024 FRR/FSR(LHD)EU 24.0 - 25.0"),
    ("7552263460", None, ""),
    ("7552361070", 6, "52209 - 2026 NPR RHD EUROPE 26.0 -"),
    ("7552441340", None, "12019 - CYL CNG 21.0 -"),
    ("7552479090", None, "52193 - 2026 NMS AUST/NZ 26.0 -"),
    ("7552479100", None, "52193 - 2026 NMS AUST/NZ 26.0 -"),
    ("7552479130", 7, "52194 - 2026 NPS/NQS AUST/NZ 26.0 -"),
    ("7552479220", 18, "52120 - 2024 NLR/NMR RHD EUROPE 24.0 -"),
    ("7552703560", 16, "12157 - 2024 FRR/FSR(RHD)EU 24.0 - 25.0"),
    ("7552703610", 16, "12157 - 2024 FRR/FSR(RHD)EU 24.0 - 25.0"),
    ("7552703630", 16, "12157 - 2024 FRR/FSR(RHD)EU 24.0 - 25.0"),
    ("7552709410", 7, "12149 - 2024 FRR/FSR(LHD)EU 24.0 - 25.0"),
    ("7552727270", 30, "52145 - 2025 NNR/NPR/NQR AUST/NZ 25.0 -"),
    ("7552760730", 3, "52209 - 2026 NPR RHD EUROPE 26.0 -"),
]


def main() -> int:
    status = [
        {
            "pn": pn,
            "eq_status": "FOUND",
            "eq_total": tot,
            "eq_fig_name": "",
            "eq_part_name": "",
            "eq_catalog": cat,
            "error": "",
            "method": "ui_status",
        }
        for pn, tot, cat in ROWS
    ]
    (DER / "_eq_hit_harvest_status_batch_20261007.json").write_text(
        json.dumps(status, ensure_ascii=False), encoding="utf-8"
    )
    prior_path = DER / "_eq_hit_harvest_raw_20261007.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8")) if prior_path.exists() else []
    by = {h["pn"]: h for h in prior}
    for h in status:
        old = by.get(h["pn"])
        if old and (old.get("eq_fig_name") or old.get("eq_part_name")) and not (
            h.get("eq_fig_name") or h.get("eq_part_name")
        ):
            continue
        by[h["pn"]] = h
    out = list(by.values())
    prior_path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print("total_harvest", len(out), "status_added", len(status))
    return subprocess.call([sys.executable, str(MERGE), "partial_ui_slow_stopped"])


if __name__ == "__main__":
    raise SystemExit(main())
