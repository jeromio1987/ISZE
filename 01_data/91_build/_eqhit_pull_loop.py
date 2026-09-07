"""EQ-HIT pull helper: write harvest txt + rebuild playbook extract CSV."""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

DERIVED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived")
OUT = DERIVED / "eqhit_extract_priority_cy2025.csv"
COLS = [
    "pull_date",
    "rank",
    "pms_category",
    "part_number",
    "description",
    "vehicle_model",
    "engine_code",
    "chassis_family",
    "lcv_generation",
    "bucket",
    "applicable",
    "eqhit_source",
    "status",
    "notes",
]


def classify(cat_line: str) -> dict:
    m = re.match(r"^(\d+)\s*-\s*(.+)$", cat_line.strip())
    if not m:
        return {
            "vehicle_model": cat_line,
            "engine_code": "",
            "chassis_family": "unknown",
            "lcv_generation": "unknown",
            "bucket": "unknown",
            "notes": cat_line,
        }
    cat_id, rest = m.group(1), m.group(2)
    u = rest.upper()
    if "TFR/TFS" in u or re.search(r"\bTFR\b", u) or re.search(r"\bTFS\b", u):
        chassis, gen, bucket = "TFR/TFS", "dmax_rt", "lcv"
        if re.search(r"\b202[0-9]\b", rest):
            gen = "dmax_rg"
    elif "UBS" in u or "TROOPER" in u:
        chassis, gen, bucket = "UBS", "trooper", "lcv"
    elif any(
        x in u
        for x in [
            "NHR",
            "NLR",
            "NMR",
            "NNR",
            "NPR",
            "NQR",
            "NPS",
            "NLS",
            "NMS",
            "NJR",
            "NKR",
            "ELF",
            "NHS",
            "NJS",
            "NKS",
            "NNS",
        ]
    ):
        chassis, gen, bucket = "N-series", "unknown", "cv_std"
    elif any(x in u for x in ["FVR", "FSR", "FTR"]):
        chassis, gen, bucket = "F-series", "unknown", "f_series"
    else:
        chassis, gen, bucket = "unknown", "unknown", "unknown"
    return {
        "vehicle_model": rest.strip(),
        "engine_code": "",
        "chassis_family": chassis,
        "lcv_generation": gen,
        "bucket": bucket,
        "notes": f"catalog_id={cat_id}",
    }


def save_harvest(pn: str, catalogues: list[str], meta: dict) -> None:
    (DERIVED / f"_eqhit_harvest_{pn}.txt").write_text("\n".join(catalogues) + ("\n" if catalogues else ""), encoding="utf-8")
    meta_lines = [f"{k}={v}" for k, v in meta.items()]
    (DERIVED / f"_eqhit_harvest_meta_{pn}.txt").write_text("\n".join(meta_lines) + "\n", encoding="utf-8")


def rows_for(pn, rank, cat, desc, catalogues, parent, status="ok", applicable="true", extra_notes=""):
    out = []
    if not catalogues:
        out.append(
            {
                "pull_date": "2026-09-05",
                "rank": rank,
                "pms_category": cat,
                "part_number": pn,
                "description": desc,
                "vehicle_model": "",
                "engine_code": "",
                "chassis_family": "unknown",
                "lcv_generation": "unknown",
                "bucket": "unknown",
                "applicable": applicable,
                "eqhit_source": "part_search_across_catalogues",
                "status": status,
                "notes": extra_notes or "no catalogue hits",
            }
        )
        return out
    for cat_line in catalogues:
        meta = classify(cat_line)
        note = meta["notes"]
        if parent:
            note += f"; parent={parent}"
        if extra_notes:
            note += f"; {extra_notes}"
        out.append(
            {
                "pull_date": "2026-09-05",
                "rank": rank,
                "pms_category": cat,
                "part_number": pn,
                "description": desc,
                "vehicle_model": meta["vehicle_model"],
                "engine_code": meta["engine_code"],
                "chassis_family": meta["chassis_family"],
                "lcv_generation": meta["lcv_generation"],
                "bucket": meta["bucket"],
                "applicable": "true",
                "eqhit_source": "part_search_across_catalogues",
                "status": status,
                "notes": note,
            }
        )
    return out


SEED_8982120690 = [
    "51412 - 2012 TFR/TFS(RHD)EXP 12.0 - 12.0",
    "51474 - 2013 TFR/TFS(RHD)EXP 13.0 - 13.0",
    "51580 - 2015 TFR/TFS(RHD)EXP 15.0 - 15.0",
    "51639 - 2016 TFR/TFS(RHD)EXP 16.0 - 16.0",
    "51680 - 2017 TFR/TFS(RHD)EXP 17.0 - 17.0",
    "51411 - 2012 TFR/TFS(LHD)EXP 12.0 - 12.0",
    "51473 - 2013 TFR/TFS(LHD)EXP 13.0 - 13.0",
    "51583 - 2014-2015 TFR/TFS(LHD)EXP 14.0 - 15.0",
    "51647 - 2016 TFR/TFS(LHD)EXP 16.0 - 16.0",
    "51690 - 2017 TFR/TFS(LHD)EXP 17.0 - 17.0",
    "51745 - 2018 TFR/TFS(LHD)EXP 18.0 - 18.0",
    "51801 - 2019 TFR/TFS(LHD)EXP 19.0 - 19.0",
    "51375 - 2012 TFR/TFS-RHD(EUROPE) 12.0 - 12.0",
    "51477 - 2013 TFR/TFS-RHD(EUROPE) 13.0 - 13.0",
    "51582 - 2014 TFR/TFS(RHD)EUROPE 14.0 - 16.0",
    "51374 - 2012 TFR/TFS-LHD(EUROPE) 12.0 - 12.0",
    "51476 - 2013 TFR/TFS-LHD(EUROPE) 13.0 - 13.0",
    "51581 - 2014 TFR/TFS(LHD)EUROPE 14.0 - 16.0",
]


def rebuild() -> int:
    # ensure first PN harvest exists
    save_harvest(
        "8982120690",
        SEED_8982120690,
        {
            "rank": "1",
            "pms_category": "clutch_disc",
            "description": "DISC; CLUTCH",
            "parent": "PASSENGER VEHICLE PICK UP",
            "status": "ok",
            "applicable": "true",
            "extra_notes": "total_results=18",
        },
    )
    save_harvest(
        "5876100771",
        [],
        {
            "rank": "1",
            "pms_category": "clutch_disc",
            "description": "DISC;CLUTCH 300",
            "parent": "",
            "status": "partial",
            "applicable": "false",
            "extra_notes": "EQ-HIT global search Total Results: 0",
        },
    )

    all_rows: list[dict] = []
    seen = set()
    for meta_path in sorted(DERIVED.glob("_eqhit_harvest_meta_*.txt")):
        pn = meta_path.stem.replace("_eqhit_harvest_meta_", "")
        if pn in seen:
            continue
        seen.add(pn)
        meta = {}
        for line in meta_path.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                meta[k.strip()] = v.strip()
        harvest = DERIVED / f"_eqhit_harvest_{pn}.txt"
        cats = []
        if harvest.exists():
            cats = [ln.strip() for ln in harvest.read_text(encoding="utf-8").splitlines() if ln.strip()]
        all_rows += rows_for(
            pn,
            int(meta.get("rank", "0") or 0),
            meta.get("pms_category", "unknown"),
            meta.get("description", ""),
            cats,
            meta.get("parent", ""),
            status=meta.get("status", "ok"),
            applicable=meta.get("applicable", "true" if cats else "false"),
            extra_notes=meta.get("extra_notes", ""),
        )

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(all_rows)
    return len(all_rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--save-pn")
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--pms-category", default="")
    ap.add_argument("--description", default="")
    ap.add_argument("--parent", default="")
    ap.add_argument("--status", default="ok")
    ap.add_argument("--applicable", default="true")
    ap.add_argument("--extra-notes", default="")
    ap.add_argument("--catalogues-file", default="")
    args = ap.parse_args()

    if args.save_pn:
        cats = []
        if args.catalogues_file:
            cats = [
                ln.strip()
                for ln in Path(args.catalogues_file).read_text(encoding="utf-8").splitlines()
                if ln.strip()
            ]
        save_harvest(
            args.save_pn,
            cats,
            {
                "rank": str(args.rank),
                "pms_category": args.pms_category,
                "description": args.description,
                "parent": args.parent,
                "status": args.status,
                "applicable": args.applicable,
                "extra_notes": args.extra_notes or (f"total_results={len(cats)}" if cats else "no catalogue hits"),
            },
        )
        print(f"saved harvest {args.save_pn} cats={len(cats)}")

    if args.rebuild or args.save_pn:
        n = rebuild()
        print(f"rebuilt extract rows={n} -> {OUT}")


if __name__ == "__main__":
    main()
