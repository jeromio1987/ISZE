"""Fix 04_DATA_TABLES into a valid single-schema CSV (+ MD fallback if CSV still blocked)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
OUT = ROOT / "01_data/15_gpt_safe/gpt_review_3_big_2026-09-20"
OUT.mkdir(parents=True, exist_ok=True)

chunks: list[pd.DataFrame] = []


def add(table: str, df: pd.DataFrame) -> None:
    body = df.copy()
    body.insert(0, "table", table)
    chunks.append(body)


ww = pd.read_csv(ROOT / "01_data/00_derived/wallet_waterfall.csv")
ww["rate_per_uio"] = ww["theoretical_wallet_eur"] / ww["uio_units"]
add("wallet_all_years", ww)

w25 = ww[ww["year"] == 2025]
ceil = float(w25["theoretical_wallet_eur"].sum())
capt = float(w25["captured_total_eur"].sum())
flat = w25[(w25["rate_per_uio"] - 250).abs() < 0.05]
add(
    "wallet_rollup_2025",
    pd.DataFrame(
        [
            {"metric": "network_ceiling_eur", "value": ceil, "note": "year=2025"},
            {"metric": "network_captured_total_eur", "value": capt, "note": ""},
            {
                "metric": "network_gps_pct",
                "value": 100 * capt / ceil,
                "note": "captured/ceiling",
            },
            {
                "metric": "fleet_uio_units",
                "value": float(w25["uio_units"].sum()),
                "note": "",
            },
            {
                "metric": "flat250_market_count",
                "value": float(len(flat)),
                "note": ",".join(flat["distributor_code"].astype(str)),
            },
            {
                "metric": "flat250_share_of_ceiling_pct",
                "value": 100 * float(flat["theoretical_wallet_eur"].sum()) / ceil,
                "note": "",
            },
        ]
    ),
)

add("gps_spu_by_distributor", pd.read_csv(ROOT / "01_data/00_derived/gps_spu_by_distributor.csv"))
om = pd.read_csv(ROOT / "01_data/00_derived/pms_opportunity_matrix.csv")
add("opportunity_matrix_full", om)
om_net = om.groupby(["year", "pms_category"], as_index=False).agg(
    revenue_gap_eur=("revenue_gap_eur", "sum"),
    tam_eur=("tam_eur", "sum"),
    markets=("distributor_code", "nunique"),
    avg_capture_total=("capture_rate_total", "mean"),
)
add("opportunity_network_by_category_year", om_net)
add("pms_capture_by_db_year", pd.read_csv(ROOT / "01_data/00_derived/pms_capture_by_db_year.csv"))
mix = ROOT / "01_data/00_derived/mix_genuine_bvp_pms.csv"
if mix.exists():
    add("mix_genuine_bvp_pms", pd.read_csv(mix))
add("n35_share", pd.read_csv(ROOT / "03_analytics/Isuzu/prism/data/uio_ld_n35_share.csv"))
bench = ROOT / "01_data/90_INBOX/_classification_benchmark_tables_20260920.csv"
if bench.exists():
    add("benchmark_tables", pd.read_csv(bench))

ps = json.loads(
    (ROOT / "01_data/00_derived/pricing_stack_applied_2026-09-19.json").read_text(
        encoding="utf-8"
    )
)
prows = [
    {
        "section": "whole_book",
        "label": "weighted_increase_pct",
        "value": ps["whole_book"]["weighted_increase"] * 100,
        "note": f"{ps['method']['recipe_rows']} rows",
    },
    {
        "section": "whole_book",
        "label": "japan_pct",
        "value": ps["whole_book"]["japan"] * 100,
        "note": "",
    },
    {
        "section": "whole_book",
        "label": "thailand_pct",
        "value": ps["whole_book"]["thailand"] * 100,
        "note": "",
    },
    {
        "section": "live_inputs",
        "label": "fx",
        "value": ps["live_inputs"]["fx"],
        "note": "applied not chosen",
    },
    {
        "section": "live_inputs",
        "label": "discount_J_pct",
        "value": ps["live_inputs"]["discount_live"]["J"] * 100,
        "note": "vehicle parts",
    },
    {
        "section": "live_inputs",
        "label": "discount_T_pct",
        "value": ps["live_inputs"]["discount_live"]["T"] * 100,
        "note": "",
    },
    {
        "section": "figure_replaced",
        "label": "earlier_thailand_pct_WRONG",
        "value": ps["figure_replaced"]["earlier_thailand"] * 100,
        "note": "factor chain",
    },
]
for src in ps["by_source"]:
    prows.append(
        {
            "section": "by_source",
            "label": src["label"],
            "value": src["weighted_increase"] * 100,
            "rows": src["rows"],
            "billed_eur": src["billed_eur"],
            "weight_share_pct": src["weight_share"] * 100,
            "note": src["source"],
        }
    )
for mkt, body in ps["markets"].items():
    prows.append(
        {
            "section": "by_market",
            "label": mkt,
            "value": body["weighted_increase"] * 100,
            "rows": body["rows"],
            "billed_eur": body["billed_eur"],
            "part_numbers": body.get("part_numbers", ""),
            "note": body.get("note", ""),
        }
    )
prows.extend(
    [
        {
            "section": "proposals",
            "label": "flat_5pct_paper_eur",
            "value": 1749680.47,
            "note": "paper only",
        },
        {
            "section": "proposals",
            "label": "published_step_eur",
            "value": 1652140.71,
            "note": "5.9616%",
        },
        {
            "section": "proposals",
            "label": "in_scope_billed_eur",
            "value": 34993609.39,
            "note": "48653 lines",
        },
        {
            "section": "proposals",
            "label": "competitor_cover_pct",
            "value": 16.47,
            "note": "T1-T3",
        },
        {
            "section": "proposals",
            "label": "max_points_at_8pct_cap",
            "value": 1.32,
            "note": "",
        },
    ]
)
add("pricing_stack", pd.DataFrame(prows))

facts = [
    ("jp_codes", "zkk_distinct", 142, "3 chars"),
    ("jp_codes", "zuk_distinct", 359, "5 chars"),
    ("jp_codes", "hkk_distinct", 125, "4 chars"),
    ("jp_codes", "zkk_euro_cover_pct", 88.11, ""),
    ("jp_codes", "zkk_hit_eur", 46183083.72, ""),
    ("jp_codes", "spine_l12m_eur", 52414407.82, ""),
    ("jp_codes", "blank_jp_rows", 25689, ""),
    ("jp_codes", "blank_jp_eur", 6231324, ""),
    ("jp_codes", "zkk_equals_full_hkk", 0, "of 142"),
    ("jp_codes", "zkk_match_hkk_prefix_live", 5, "of 142"),
    ("jp_codes", "zuk_equals_hkk_or_zkk", 0, "of 359"),
    ("jp_codes", "zkk_114_XC_pct", 77.4, "not 100"),
    ("jp_codes", "zkk_275_share_covered_pct", 46.77, ""),
    ("jp_codes", "zkk_fragmented_share_pct", 97.86, ""),
    ("jp_codes", "benchmark_purity_published", 82.59, "UNUSABLE"),
    ("jp_codes", "benchmark_purity_jp_desc_zkk", 12.32, "remeasured"),
    ("classification", "gate_pass", 18, "of 18"),
    ("classification", "residual_share_pct", 5.74, ""),
    ("classification", "classification_rows", 164667, ""),
    ("classification", "true_open_pns", 9164, ""),
    ("classification", "true_open_l12m_eur", 114516, ""),
    ("classification", "eq_needs_human_pns", 360, "of 744"),
    ("classification", "switch_today", 0, "do not"),
]
add(
    "classification_jp_claims",
    pd.DataFrame(
        [{"domain": a, "metric": b, "value": c, "note": d} for a, b, c, d in facts]
    ),
)

# --- Valid single CSV (one header, three columns) ---
rows = []
for df in chunks:
    t = str(df["table"].iloc[0])
    body = df.drop(columns=["table"])
    for i, rec in enumerate(body.to_dict(orient="records")):
        clean = {}
        for k, v in rec.items():
            if v is None or (isinstance(v, float) and pd.isna(v)):
                continue
            if hasattr(v, "item"):
                try:
                    v = v.item()
                except Exception:
                    v = str(v)
            clean[str(k)] = v
        rows.append(
            {
                "table": t,
                "row_id": i,
                "payload_json": json.dumps(clean, ensure_ascii=False, default=str),
            }
        )

valid = pd.DataFrame(rows)
csv_path = OUT / "04_DATA_TABLES.csv"
valid.to_csv(csv_path, index=False, encoding="utf-8", lineterminator="\n")
print(f"CSV  {csv_path.stat().st_size/1024:.1f} KB  rows={len(valid)}  cols=3")

# --- MD fallback (ChatGPT already accepts MD) — replace 5th file if needed ---
# Keep pack at 5 uploadable files: use MD as the fifth deliverable name
# and keep CSV on disk as twin with different name? User max 5 in folder for upload.
# Strategy: write 04_DATA_TABLES.md as primary upload twin; keep valid CSV too
# would be 6 files. So: rename pack to MD for upload, leave CSV as
# 04_DATA_TABLES.csv for local Excel, and update ASK to say:
# "Upload 04_DATA_TABLES.md if CSV fails; same content summary + key tables."

def as_fence(df: pd.DataFrame) -> str:
    return "```csv\n" + df.to_csv(index=False) + "```"


parts: list[str] = [
    "# Data tables for the multi-hour review",
    "",
    "ChatGPT rejected the earlier multi-section `.csv` (comment lines + mixed schemas).",
    "This markdown carries the tables ChatGPT needs for the hour-scale review.",
    "If you also got `04_DATA_TABLES.csv` to upload: it is a valid 3-column file",
    "`table,row_id,payload_json` — filter by `table`, parse JSON per row.",
    "",
    "Tables in this file:",
    "",
]
for df in chunks:
    t = df["table"].iloc[0]
    parts.append(f"- `{t}` — {len(df)} rows")
parts.append("")

by_name = {df["table"].iloc[0]: df.drop(columns=["table"]) for df in chunks}

for name in [
    "wallet_rollup_2025",
    "n35_share",
    "pricing_stack",
    "classification_jp_claims",
    "opportunity_network_by_category_year",
    "wallet_all_years",
    "gps_spu_by_distributor",
    "opportunity_matrix_full",
    "benchmark_tables",
]:
    if name not in by_name:
        continue
    df = by_name[name]
    parts.append(f"## TABLE `{name}` ({len(df)} rows)")
    parts.append("")
    parts.append(as_fence(df))
    parts.append("")

# large capture/mix: sample in MD (full in CSV)
for name in ["pms_capture_by_db_year", "mix_genuine_bvp_pms"]:
    if name not in by_name:
        continue
    df = by_name[name]
    parts.append(
        f"## TABLE `{name}` — sample 60 of {len(df)} rows (full set in CSV)"
    )
    parts.append("")
    parts.append(as_fence(df.head(60)))
    parts.append("")
md_path = OUT / "04_DATA_TABLES.md"
md_path.write_text("\n".join(parts), encoding="utf-8", newline="\n")
print(f"MD   {md_path.stat().st_size/1024:.1f} KB")

# Patch ASK: mention CSV format + MD fallback
ask = OUT / "00_ASK.md"
text = ask.read_text(encoding="utf-8")
needle = "| `04_DATA_TABLES.csv` | Checkable multi-table extract (`table` column) | large |"
repl = (
    "| `04_DATA_TABLES.csv` | Valid 3-col file: `table,row_id,payload_json` | large |\n"
    "| `04_DATA_TABLES.md` | Same data for upload if CSV is blocked (upload this instead) | large |"
)
if needle in text:
    ask.write_text(text.replace(needle, repl), encoding="utf-8", newline="\n")
    print("ASK patched for MD fallback")
else:
    print("ASK table row not found — check manually")

print("Pack files:")
for p in sorted(OUT.iterdir()):
    if p.is_file():
        print(f"  {p.name:28s} {p.stat().st_size/1024:8.1f} KB")
