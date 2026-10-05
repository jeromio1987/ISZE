# -*- coding: utf-8 -*-
"""Build BVDB PBI upload pack 2026-09-23 — UIO + GPS + PMS + AIM only."""
from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
GPT = ROOT / "01_data" / "15_gpt_safe" / "gpt_pack_2026-09-20"
OUT = ROOT / "09_meetings" / "BVDB_PBI_Data_Upload_2026-09-23"
ASOF = "2026-09-22"
ZIP_NAME = f"BVDB_PBI_Data_Upload_{ASOF.replace('-', '')}.zip"

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
for sub in ("00_START_HERE", "01_UIO", "02_GPS", "03_PMS", "04_AIM"):
    (OUT / sub).mkdir()

manifest: list[dict] = []


def write_csv(rel: str, df: pd.DataFrame, purpose: str, grain: str, join_keys: str) -> None:
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    manifest.append(
        {
            "file": rel.replace("\\", "/"),
            "rows": len(df),
            "cols": len(df.columns),
            "kb": round(path.stat().st_size / 1024, 1),
            "purpose": purpose,
            "grain": grain,
            "join_keys": join_keys,
        }
    )
    print(f"  {rel}  {len(df)} rows  {path.stat().st_size // 1024} KB")


MARKET_COUNTRY = {
    "BELGIUM": "Belgium",
    "NETHLDS": "Netherlands",
    "POLAND": "Poland",
    "CYPRUS": "Cyprus",
    "DENMARK": "Denmark",
    "FINLAND": "Finland",
    "GERMANY": "Germany",
    "GREECE": "Greece",
    "HUNGARY": "Hungary",
    "ICELAND": "Iceland",
    "IRELAND": "Ireland",
    "ISRAEL": "Israel",
    "MALTA": "Malta",
    "NORWAY": "Norway",
    "PORTUGL": "Portugal",
    "ROMANIA": "Romania",
    "SWEDEN": "Sweden",
    "U KING": "United Kingdom",
}

# --- UIO ---
uio = pd.read_csv(DER / "uio_by_market_type_year.csv")
uio_fact = uio[
    [
        "distributor_code",
        "market",
        "vehicle_class",
        "model_type",
        "year",
        "uio_units",
        "is_actual",
        "is_estimate",
        "is_forecast",
        "basis",
    ]
].copy()
uio_fact["country"] = uio_fact["market"].map(MARKET_COUNTRY).fillna(uio_fact["market"])
write_csv(
    "01_UIO/fact_uio_by_market_type_year.csv",
    uio_fact,
    "Trucks in service (UIO) by distributor, market, vehicle class, model type, year",
    "distributor_code x market x vehicle_class x model_type x year",
    "distributor_code, year",
)

notes = uio[
    [
        "distributor_code",
        "market",
        "vehicle_class",
        "model_type",
        "year",
        "source_note",
        "band_note",
        "fleet_quality_note",
    ]
].copy()
mask = (
    notes["source_note"].fillna("").astype(str).str.strip().ne("")
    | notes["band_note"].fillna("").astype(str).str.strip().ne("")
    | notes["fleet_quality_note"].fillna("").astype(str).str.strip().ne("")
)
notes = notes.loc[mask]
write_csv(
    "01_UIO/fact_uio_notes_optional.csv",
    notes,
    "Optional long notes for UIO rows — documentation only, not for measures",
    "same as fact_uio (subset with notes)",
    "distributor_code, market, vehicle_class, model_type, year",
)

rollup = (
    uio.groupby(["distributor_code", "year"], as_index=False)
    .agg(
        uio_units=("uio_units", "sum"),
        n_market_rows=("market", "count"),
        basis_modes=("basis", lambda s: "|".join(sorted(s.dropna().astype(str).unique()))),
        is_actual=("is_actual", "max"),
        is_estimate=("is_estimate", "max"),
        is_forecast=("is_forecast", "max"),
    )
)
write_csv(
    "01_UIO/fact_uio_by_distributor_year.csv",
    rollup,
    "UIO rolled up to distributor x year — easiest join to SAP year totals",
    "distributor_code x year",
    "distributor_code, year",
)

class_roll = (
    uio.groupby(["distributor_code", "vehicle_class", "model_type", "year"], as_index=False)
    .agg(uio_units=("uio_units", "sum"), basis=("basis", "first"))
)
write_csv(
    "01_UIO/fact_uio_by_class_year.csv",
    class_roll,
    "UIO by distributor x vehicle class x model type x year",
    "distributor_code x vehicle_class x model_type x year",
    "distributor_code, year",
)

dim = pd.read_csv(DER / "distributor_dimension.csv")
write_csv(
    "01_UIO/dim_distributor.csv",
    dim,
    "Sold-to / payer to distributor_code bridge for SAP joins. UTI≠UMI; IUK≠ITUK.",
    "one row per sold_to_sap",
    "sold_to_sap <-> SAP Sold-to; distributor_code <-> pack facts",
)

n35_path = GPT / "07_uio_ld_n35_share.csv"
if n35_path.exists():
    n35 = pd.read_csv(n35_path)
    keep = [c for c in ["distributor_code", "market", "n35_share", "basis", "units_2025e"] if c in n35.columns]
    write_csv(
        "01_UIO/uio_ld_n35_share.csv",
        n35[keep].copy(),
        "Share of light CV (~3.5 t / N35) within LD fleets",
        "distributor_code (one row)",
        "distributor_code",
    )
    if "evidence_note" in n35.columns:
        write_csv(
            "01_UIO/uio_ld_n35_share_notes_optional.csv",
            n35[["distributor_code", "market", "evidence_note"]],
            "Evidence notes for N35 share — documentation only",
            "distributor_code",
            "distributor_code",
        )

overrides = pd.DataFrame(
    [
        {
            "distributor_code": "IUK",
            "year": 2026,
            "field": "uio_units",
            "csv_value": 49280.0,
            "locked_value": 44926.0,
            "status": "LOCKED_V20_2026-07-30",
            "note": (
                "Jerome locked IUK LCV CY2026F at 44,926. "
                "The fact CSV still carries the V19 forecast 49,280. "
                "Prefer locked_value for 2026 IUK until the workbook is rebuilt."
            ),
        }
    ]
)
write_csv(
    "01_UIO/uio_overrides_known.csv",
    overrides,
    "Known corrections that override fact_uio until the source workbook is updated",
    "distributor_code x year x field",
    "distributor_code, year",
)

# --- GPS ---
gps_specs = [
    (
        "gps_spu_by_distributor.csv",
        "02_GPS/gps_spu_by_distributor.csv",
        "Parts billed euro and spend per truck (UIO) by distributor x year",
        "distributor_code x year",
        "distributor_code, year",
    ),
    (
        "gps_spu_by_family.csv",
        "02_GPS/gps_spu_by_family.csv",
        "Parts billed euro and spend per truck by distributor x part family x year",
        "distributor_code x product_family x year x line_type",
        "distributor_code, year",
    ),
    (
        "gps_spu_pms.csv",
        "02_GPS/gps_spu_pms.csv",
        "Parts billed euro and spend per truck by PMS service category",
        "distributor_code x pms_category x year x line_type",
        "distributor_code, year, pms_category",
    ),
]
for src, rel, purpose, grain, keys in gps_specs:
    write_csv(rel, pd.read_csv(DER / src), purpose, grain, keys)

waterfall = pd.read_csv(DER / "wallet_waterfall.csv")
friendly = {
    "theoretical_wallet_eur": "target_spend_ceiling_eur",
    "captured_total_eur": "parts_billed_total_eur",
    "captured_genuine_eur": "parts_billed_genuine_eur",
    "captured_bvp_eur": "parts_billed_bvp_eur",
    "uncaptured_eur": "gap_vs_target_eur",
    "gps_pct": "parts_billed_vs_target_pct",
}
for old, new in friendly.items():
    if old in waterfall.columns and new not in waterfall.columns:
        waterfall[new] = waterfall[old]
write_csv(
    "02_GPS/target_spend_waterfall.csv",
    waterfall,
    "Target spend per truck ceiling vs parts billed — use friendly columns for report labels",
    "distributor_code x year",
    "distributor_code, year",
)

# --- PMS ---
write_csv(
    "03_PMS/pms_summary_by_db.csv",
    pd.read_csv(DER / "pms_summary_by_db.csv"),
    "PMS headline: total capture (primary) and genuine capture (secondary) by distributor x year",
    "distributor_code x year",
    "distributor_code, year",
)

pms_cap = pd.read_csv(DER / "pms_capture_by_db_year.csv")
write_csv(
    "03_PMS/pms_capture_by_db_year.csv",
    pms_cap,
    "PMS capture by category. Filter line_type=total for primary; genuine is secondary",
    "distributor_code x pms_category x year x line_type",
    "distributor_code, year, pms_category",
)

write_csv(
    "03_PMS/pms_opportunity_matrix.csv",
    pd.read_csv(DER / "pms_opportunity_matrix.csv"),
    "Category gap ranking — revenue gap vs expected service demand",
    "distributor_code x pms_category x year",
    "distributor_code, year, pms_category",
)

# --- AIM ---
aim_specs = [
    (
        "aim_gps_matrix.csv",
        "04_AIM/aim_gps_matrix.csv",
        "AIM match coverage vs GPS billed euro by distributor x year",
        "distributor_code x year",
        "distributor_code, year",
    ),
    (
        "aim_exposure_by_db_year.csv",
        "04_AIM/aim_exposure_by_db_year.csv",
        "AIM exposure / classification coverage by distributor x year",
        "distributor_code x year",
        "distributor_code, year",
    ),
    (
        "aim_bvp_family_risk.csv",
        "04_AIM/aim_bvp_family_risk.csv",
        "BVP risk by AIM family",
        "family grain (see columns)",
        "distributor_code if present; else family keys",
    ),
    (
        "mix_genuine_bvp_by_family.csv",
        "04_AIM/mix_genuine_bvp_by_family.csv",
        "Genuine vs BVP mix by product family",
        "distributor_code x product_family x year",
        "distributor_code, year",
    ),
    (
        "mix_genuine_bvp_by_group.csv",
        "04_AIM/mix_genuine_bvp_by_group.csv",
        "Genuine vs BVP mix by AIM group",
        "distributor_code x group x year",
        "distributor_code, year",
    ),
    (
        "mix_genuine_bvp_by_subgroup.csv",
        "04_AIM/mix_genuine_bvp_by_subgroup.csv",
        "Genuine vs BVP mix by AIM subgroup",
        "distributor_code x subgroup x year",
        "distributor_code, year",
    ),
    (
        "mix_genuine_bvp_pms.csv",
        "04_AIM/mix_genuine_bvp_pms.csv",
        "Genuine vs BVP mix by PMS category",
        "distributor_code x pms_category x year",
        "distributor_code, year, pms_category",
    ),
]
for src, rel, purpose, grain, keys in aim_specs:
    write_csv(rel, pd.read_csv(DER / src), purpose, grain, keys)

cat_a = pms_cap[["pms_category", "category_label"]].drop_duplicates().sort_values("pms_category")
write_csv(
    "04_AIM/dim_pms_category.csv",
    cat_a,
    "Slim PMS / service-category dimension — not the full AIM master PN file",
    "pms_category",
    "pms_category",
)

man_df = pd.DataFrame(manifest)
man_df.to_csv(OUT / "00_START_HERE" / "MANIFEST.csv", index=False, encoding="utf-8-sig")

howto = f"""# BVDB Power BI data pack — how to load

**Meeting:** BVDB x Jerome — Power BI enrichment
**Pack date:** {ASOF}
**What this is:** trucks in service (UIO) plus GPS, PMS and AIM tables that hang off your existing SAP sales / order / pricing model.
**What this is not:** no SAP line billing dump, no order detail, no price-list or pricing-simulation files. You already have those from SAP.

---

## 1. Load order (Get Data → Text / CSV)

1. `01_UIO/dim_distributor.csv` — bridge from SAP **Sold-to** (`sold_to_sap`) to `distributor_code`
2. `01_UIO/fact_uio_by_distributor_year.csv` — start here for euro-per-truck measures
3. `01_UIO/fact_uio_by_market_type_year.csv` — detail when you need class / market split
4. `01_UIO/uio_overrides_known.csv` — **apply before publishing IUK 2026**
5. Then GPS (`02_GPS/`), PMS (`03_PMS/`), AIM (`04_AIM/`)

Encoding is UTF-8 with BOM. First row = headers.

Optional (documentation only, do not put in the model relationship path):
- `fact_uio_notes_optional.csv`
- `uio_ld_n35_share_notes_optional.csv`

---

## 2. Relationships (star)

| From | To | Keys |
|------|-----|------|
| Your SAP sales (already in PBI) | `dim_distributor` | Sold-to → `sold_to_sap` |
| `dim_distributor` | all pack facts | `distributor_code` |
| UIO / GPS / PMS / AIM facts | each other | `distributor_code` + `year` |
| PMS / GPS PMS / AIM mix PMS | `dim_pms_category` | `pms_category` |

Cardinality tip: `fact_uio_by_distributor_year` is one row per distributor x year — safe many-to-one from sales if you aggregate sales to the same grain first.

---

## 3. Entity rules (do not blend)

- **UTI ≠ UMI** — two Israel distributors. Separate `distributor_code`, separate Sold-to (1799 vs 1797). Never average into one "Israel".
- **IUK ≠ ITUK** — LCV vs CV UK. Separate fleets, separate sales.
- **IBX / BELGIUM** — Sold-to 90 maps to `BELGIUM` in this pack; GPS label may say IBX.

---

## 4. UIO — what you did not have

**UIO = trucks in service** (parc / units in operation), not registrations alone.

- Source extract: ISZE UIO workbook v19 → derived `uio_by_market_type_year`
- Years: 1990–2030. Use `basis` / `is_actual` / `is_estimate` / `is_forecast` to filter.
- `uio_ld_n35_share.csv` — share of ~3.5 t trucks inside LD fleets (matters for spend-per-truck rates).

### Hard caveat — IUK 2026

| | Value |
|--|------:|
| Value in the fact CSV (V19 forecast) | **49,280** |
| Jerome locked figure (V20, 2026-07-30) | **44,926** |

Until the workbook is rebuilt, for IUK x 2026 use `uio_overrides_known.csv` (`locked_value`). Do not publish 49,280 as the official IUK 2026 fleet.

---

## 5. GPS — labels for the model

In Power BI **display names**, use:

| Prefer | Avoid |
|--------|--------|
| trucks in service / UIO | — |
| parts billed (€) | wallet |
| target spend per truck / target spend ceiling | wallet € |
| price index / reference dealer price | street |

File `02_GPS/target_spend_waterfall.csv` still has technical column names like `theoretical_wallet_eur` for lineage. Friendly copies are also present (`target_spend_ceiling_eur`, `parts_billed_total_eur`, …). Hide the technical names in the report view.

Primary GPS grain: `gps_spu_by_distributor.csv`
`spend_per_unit_eur` = parts billed ÷ UIO for that year.

---

## 6. PMS — total first

- **Primary:** `line_type = total` (or `capture_rate_total_wtd` on the summary).
- **Secondary:** genuine share / genuine capture — mix quality, not a substitute for total volume.
- `pms_opportunity_matrix.csv` ranks category euro gaps.

---

## 7. AIM — enrichment only

AIM tables here are **coverage and mix** at distributor / family / group level.
There is **no** full AIM master PN dump (that file is ~12 MB and is a parts catalogue, not a PBI fact for this meeting).

Use:
- `aim_gps_matrix` — how much billed euro has AIM class attached
- `mix_genuine_bvp_*` — genuine vs BVP mix
- `dim_pms_category` — slim category list

---

## 8. Starter measures (DAX sketch)

Assuming you have a sales measure `[Parts billed €]` already, and UIO on `fact_uio_by_distributor_year[uio_units]`:

```
UIO trucks :=
SUM ( fact_uio_by_distributor_year[uio_units] )

// After override table applied for IUK 2026 — or use a calculated column that prefers locked_value

Euro per truck :=
DIVIDE ( [Parts billed €], [UIO trucks] )

GPS pct vs target :=
DIVIDE ( [Parts billed €], SUM ( target_spend_waterfall[target_spend_ceiling_eur] ) )

PMS total capture :=
AVERAGE ( pms_summary_by_db[capture_rate_total_wtd] )
// or better: weighted by expected euro if you bring expected into the model
```

Prefer importing GPS/PMS pre-aggregated files for the first dashboard; add custom DAX later.

---

## 9. Suggested first visuals for the meeting

1. UIO by distributor, CY2025 (and CY2024) — stacked CV vs LCV from `fact_uio_by_class_year`
2. Parts billed € / UIO vs prior year — join your SAP sales to UIO rollup
3. PMS total capture by distributor — `pms_summary_by_db`
4. Top category gaps — `pms_opportunity_matrix` filtered to one year
5. Genuine vs BVP mix — `mix_genuine_bvp_by_family`

---

## 10. Refresh

These CSVs are a **point-in-time export** ({ASOF}). They are not a live SAP feed. When ISZE refreshes derived tables, ask for a new dated pack rather than editing cells by hand (except the IUK 2026 override, which is intentional).

---

## Folder map

| Folder | Contents |
|--------|----------|
| `00_START_HERE` | This file + MANIFEST.csv |
| `01_UIO` | Fleet / trucks in service + Sold-to bridge |
| `02_GPS` | Spend per truck and target-spend waterfall |
| `03_PMS` | Service capture and opportunity gaps |
| `04_AIM` | Classification coverage and genuine/BVP mix |
"""

(OUT / "00_START_HERE" / "HOW_TO.md").write_text(howto, encoding="utf-8")
(OUT / "00_START_HERE" / "README.txt").write_text(
    "Start with HOW_TO.md and MANIFEST.csv.\n"
    "UIO is the main gap vs your SAP model.\n"
    "Do not load optional *_notes_* into the relationship path.\n"
    "IUK 2026: use uio_overrides_known.csv (44,926), not 49,280.\n",
    encoding="utf-8",
)

brief = f"""# Meeting brief — BVDB PBI ({ASOF})

Hand him the zip. He already has pricing + sales/order from SAP.

**Lead with UIO.** That is what he does not have. Then GPS (euro per truck), PMS (total capture first), AIM mix/coverage.

**Say out loud:**
- IUK 2026 fleet in the CSV is still 49,280; you locked 44,926 — use the override file until the workbook is rebuilt.
- UTI and UMI stay separate; IUK and ITUK stay separate.
- PMS primary = total, not genuine-only.
- No wallet/street wording on the report labels — parts billed / target spend per truck.

**Do not hand:** sales_fact, order detail, AIM master PN (12 MB), pricing simulation CSVs.

**Zip:** sibling of this folder, `{ZIP_NAME}`
"""
(OUT / "00_START_HERE" / "MEETING_BRIEF_Jerome.md").write_text(brief, encoding="utf-8")

zip_path = OUT.parent / ZIP_NAME
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in sorted(OUT.rglob("*")):
        if f.is_file():
            zf.write(f, f"BVDB_PBI_Data_Upload_2026-09-23/{f.relative_to(OUT).as_posix()}")

meta = {
    "as_of": ASOF,
    "folder": str(OUT),
    "zip": str(zip_path),
    "zip_kb": round(zip_path.stat().st_size / 1024, 1),
    "files": len(manifest),
    "excluded": [
        "sales_fact / line billing",
        "order detail",
        "AIM master PN (~12MB)",
        "pricing / BP simulation CSVs",
    ],
}
(OUT / "00_START_HERE" / "_pack_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
print("ZIP", zip_path, zip_path.stat().st_size // 1024, "KB")
print(json.dumps(meta, indent=2))
print("DONE files", len(manifest))
