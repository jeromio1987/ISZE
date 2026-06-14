"""Build MODEL_REFINEMENT_TRACKER.xlsx from v17 / PMS Calc / sources.yaml."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "MODEL_REFINEMENT_TRACKER.xlsx"


def load_sources() -> dict:
    with (ROOT / "sources.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


CANONICAL_ITUK_MODELS = {
    "F110/120",
    "F135",
    "F150/180",
    "N35",
    "N50/55",
    "N62/65",
    "N75",
    "UNSPEC",
    "Total ITUK",
}

# LCV D-Max — primary on IUK / UMI (not ITUK sheet 4 car park)
LCV_DISTRIBUTOR_MODELS = [
    {"model": "LCV D-Max", "primary_distributors": "IUK, UMI", "market": "Ireland / Israel LCV"},
]


def parse_v17_ituk_models(uio_path: Path, year: int = 2024) -> pd.DataFrame:
    """Section G on sheet 4 — 2024A car park by model (PRISM-aligned total)."""
    s4 = pd.read_excel(uio_path, sheet_name="4. ITUK UIO Projection", header=None)
    header_row = None
    headers: list[str] = []
    for i in range(len(s4)):
        row = [str(c).strip() if pd.notna(c) else "" for c in s4.iloc[i]]
        if len(row) > 1 and row[1] == "Model" and "2024A" in row:
            header_row = i
            headers = row
            break
    if header_row is None:
        return pd.DataFrame()

    col = f"{year}A"
    if col not in headers:
        return pd.DataFrame()
    col_idx = headers.index(col)

    rows = []
    for i in range(header_row + 1, min(header_row + 20, len(s4))):
        model = str(s4.iloc[i, 1]).strip() if pd.notna(s4.iloc[i, 1]) else ""
        if model not in CANONICAL_ITUK_MODELS:
            continue
        uio = s4.iloc[i, col_idx]
        try:
            uio_f = float(uio) if pd.notna(uio) else None
        except (TypeError, ValueError):
            uio_f = None
        rows.append(
            {
                "model": model,
                "tonnage_class": _tonnage_from_model(model),
                "ituk_car_park_2024a": uio_f,
                "uio_source_note": "v17 sheet 4 §G 2024A (SMMT via ITUK; PRISM total 22,389)",
            }
        )
    for extra in LCV_DISTRIBUTOR_MODELS:
        rows.append(
            {
                "model": extra["model"],
                "tonnage_class": "LCV",
                "ituk_car_park_2024a": None,
                "uio_source_note": f"Not in ITUK sheet 4 — see v17 sheet 1 ({extra['market']})",
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # Sheet 4 §G lists models twice (historical block + projection); keep row with UIO.
    df = df.sort_values("ituk_car_park_2024a", ascending=False, na_position="last")
    return df.drop_duplicates(subset=["model"], keep="first").reset_index(drop=True)


def _tonnage_from_model(model: str) -> str:
    m = model.upper()
    if "D-MAX" in m or "DMAX" in m or "LCV" in m or "GRAFTER" in m:
        return "LCV"
    if "N35" in m or "3.5" in m:
        return "3.5t (N35)"
    if "N50" in m or "N55" in m or "5.5" in m:
        return "5.5t (N50/55)"
    if "N62" in m or "N65" in m or "6.5" in m:
        return "6.5t (N62/65)"
    if "N75" in m or "7.5" in m or "NPR75" in m or "NPR88" in m:
        return "7.5t (N75)"
    if "F-" in m or "F SERIES" in m or m.startswith("F"):
        return "F-Series"
    if "MD" in m:
        return "MD"
    if "TOTAL" in m:
        return "Fleet total"
    return "Other CV"


def mileage_recommendation(tonnage: str) -> tuple[int, str, str]:
    """Return (recommended_km_yr, rationale, db_check_action)."""
    rec = {
        "LCV": (
            45000,
            "LCV/D-Max UK fleets often 35–55k km/yr vs ISZJ 80k. Use for PMS potential until ITUK VIN mileage.",
            "ITUK + IUK: confirm avg km/yr from service contracts or telematics.",
        ),
        "3.5t (N35)": (
            60000,
            "Urban/light delivery; below 80k but above LCV. PMS Calc uses one 80k default — segment N35.",
            "ITUK: N35 registration cohort + workshop job cards.",
        ),
        "5.5t (N50/55)": (
            70000,
            "Medium CV; between N35 and N75. Align intervals with N75 manual where shared platform.",
            "Per DB with N50/55 UIO: dealer workshop survey.",
        ),
        "6.5t (N62/65)": (
            75000,
            "Heavy light CV; closer to N75 duty cycle.",
            "Per DB: compare to N75 assumptions in PMS Calc.",
        ),
        "7.5t (N75)": (
            80000,
            "Matches PMS Calc / ISZJ Group standard (Jan 2026). PRISM pilot focus.",
            "ITUK + PRISM: validate against N75 VIN/service data.",
        ),
        "F-Series": (
            80000,
            "Long-haul profile; keep 80k unless DB reports lower fleet average.",
            "IE/PT/UK F-series distributors only.",
        ),
        "MD": (
            70000,
            "MIDI / MD markets — often lower volume; confirm with MIDI Europe separately.",
            "Exclude from Pan-EU PMS until UIO in v17 (user policy).",
        ),
        "Fleet total": (0, "Roll-up only — do not use for per-part frequency.", "—"),
        "Other CV": (
            80000,
            "Fallback to ISZJ until model identified.",
            "Map model code in v17 Assumptions sheet.",
        ),
    }
    return rec.get(tonnage, (80000, "Default ISZJ 80k.", "Confirm with distributor."))


def pms_calc_models() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "model": "N35",
                "pms_calc_section": "UIO Data — N35 block",
                "pms_parts_status": "Shared Assumptions sheet (verify N35 manual)",
                "priority": "High — ITUK pilot",
            },
            {
                "model": "N75",
                "pms_calc_section": "UIO Data — N75 block",
                "pms_parts_status": "Shared Assumptions sheet (verify N75 manual)",
                "priority": "High — ITUK pilot + PRISM N75_only",
            },
        ]
    )


def distributor_scope(cfg: dict, uio_path: Path) -> pd.DataFrame:
    aliases = cfg.get("distributor_aliases") or {}
    excluded = {"MIDI Europe", "GERMANY"}  # user: no MIDI / no UIO for PMS pan view

    s1 = pd.read_excel(uio_path, sheet_name="1.UIO Overview", header=None)
    hdr = None
    for i in range(50):
        if str(s1.iloc[i, 1]).strip() == "Distributor":
            hdr = i
            break
    dist_uio = {}
    if hdr is not None:
        for i in range(hdr + 1, min(hdr + 40, len(s1))):
            d = str(s1.iloc[i, 1]).strip() if pd.notna(s1.iloc[i, 1]) else ""
            if not d:
                continue
            try:
                u = float(s1.iloc[i, 2])
            except (TypeError, ValueError):
                u = None
            dist_uio[d] = u

    prism_path = Path(cfg["paths"]["pms_capture_by_db"])
    prism_dbs = set()
    if prism_path.exists():
        pc = pd.read_csv(prism_path)
        prism_dbs = set(pc["distributor_code"].astype(str).str.upper())

    rows = []
    for dist, code in sorted(aliases.items(), key=lambda x: x[0]):
        include = dist not in excluded and code not in ("GERMANY",)
        has_uio = dist in dist_uio and (dist_uio.get(dist) or 0) > 0
        in_prism = str(code).upper() in prism_dbs
        rows.append(
            {
                "distributor_name": dist,
                "db_code": code,
                "include_in_pan_eu_pms": "Yes" if include and (has_uio or in_prism) else "No",
                "exclude_reason": (
                    "MIDI / no ISZE UIO (user policy)"
                    if not include
                    else ("No v17 UIO row" if not has_uio else "")
                ),
                "v17_active_uio": dist_uio.get(dist),
                "in_prism_csv": "Yes" if in_prism else "No",
            }
        )
    return pd.DataFrame(rows)


def refinement_tasks(models: pd.DataFrame) -> pd.DataFrame:
    tasks = []
    for _, r in models.iterrows():
        model = r["model"]
        ton = r.get("tonnage_class", "")
        if ton == "Fleet total":
            continue
        km, why, db = mileage_recommendation(ton)
        refine_uio = (
            "Update ITUK VIN/reg data in PMS Calc UIO Data block"
            if model in ("N35", "N75")
            else (
                "v17 sheet 1 — IUK/UMI UIO for D-Max; confirm with distributor"
                if "D-Max" in model
                else (
                    "Roll-up check vs PRISM 22,389"
                    if model == "Total ITUK"
                    else "v17 sheet 4 §G — validate 2024A with ITUK"
                )
            )
        )
        tasks.append(
            {
                "model": model,
                "tonnage_class": ton,
                "refine_uio": refine_uio,
                "refine_pms_parts": "Get service manual intervals per model; add to pms_parts_config.yaml",
                "refine_actuals": "Map PNs to model in v3 / dealer sales; PRISM category by model when available",
                "recommended_km_yr": km if km else "",
                "mileage_rationale": why,
                "db_to_check": db,
                "brake_qty_rule": "1 qty = 1 brake pad (signed)",
                "prism_scope": "Use N75_only expected_qty for capture; engine tab for what-if only",
                "status": "Open",
                "owner": "Jerome",
                "notes": "",
            }
        )
    return pd.DataFrame(tasks)


def readme_sheet() -> pd.DataFrame:
    lines = [
        ("What is SPEC.md?", "Engine contract: formulas, decisions, inputs. Edit when methodology changes."),
        ("sources.yaml", "Paths to v3, v17 UIO, PMS Calc, PRISM CSV, dealer sales, FX, distributor aliases."),
        ("pms_parts_config.yaml", "PMS intervals (per category) + per-model annual_mileage_km for engine allocation."),
        ("AUDIT_MAP.md", "Where every file lives — start here for file list."),
        ("AUDIT_STATUS.md", "Audit finding register."),
        ("CHANGELOG.md", "What changed in the bundle."),
        ("MODEL_REFINEMENT_TRACKER.xlsx", "This workbook — per-model refinement checklist."),
        ("ISZE_Parts_Intelligence_v3.xlsx", "PN matrix, CY qty (1 qty = 1 pad)."),
        ("ISUZU_UIO_Overview_2026_v17.xlsx", "Distributors, ITUK car park by model (sheet 4)."),
        ("ISZE_PMS_Coverage_Calculator.xlsx", "N35/N75 UIO placeholders, Assumptions intervals."),
        ("pms_capture_by_db_year.csv", "PRISM multi-DB actuals + expected_qty (N75_only)."),
        ("Sales to Dealers_{DB}_{CY|FY}{year}.xlsx", "Per-distributor actuals when present."),
    ]
    return pd.DataFrame(lines, columns=["file_or_topic", "purpose"])


def main() -> int:
    cfg = load_sources()
    uio_path = Path(cfg["paths"]["uio_overview"])
    models = parse_v17_ituk_models(uio_path)
    if models.empty:
        print("WARN: no models parsed from v17 sheet 4", file=sys.stderr)
    tasks = refinement_tasks(models)
    dist = distributor_scope(cfg, uio_path)
    pms_models = pms_calc_models()
    readme = readme_sheet()

    decisions = pd.DataFrame(
        [
            ("Brake pad qty", "1 qty = 1 brake pad"),
            ("PMS by model", "Need more PMS parts data per model — use this tracker"),
            ("Pan-EU scope", "Named distributors from sources.yaml only; exclude MIDI Europe / no UIO"),
            ("PRISM capture", "N75_only expected_qty — same as audit recommendation"),
            ("Mileage", "Segment by tonnage — see Recommended_km_yr column"),
        ],
        columns=["topic", "decision"],
    )

    with pd.ExcelWriter(OUT, engine="openpyxl") as w:
        readme.to_excel(w, sheet_name="Files guide", index=False)
        decisions.to_excel(w, sheet_name="Decisions", index=False)
        tasks.to_excel(w, sheet_name="Model refinement", index=False)
        models.to_excel(w, sheet_name="ITUK car park by model", index=False)
        dist.to_excel(w, sheet_name="Distributor scope", index=False)
        pms_models.to_excel(w, sheet_name="PMS Calc models", index=False)

    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
