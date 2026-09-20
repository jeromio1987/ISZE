# -*- coding: utf-8 -*-
"""Build GPT upload pack: all sales, all warranty, all sales-to-dealer (+ layer extras).

Writes under 01_data/15_gpt_safe/gpt_pack_2026-09-20/
Does not touch raw/sales XLSX. Does not rebuild ceilings or dashboards.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "01_data" / "00_derived"
OUT = ROOT / "01_data" / "15_gpt_safe" / "gpt_pack_2026-09-20"
WARR_COMM = DERIVED / "warranty_commercial"


def _write(df: pd.DataFrame, path: Path) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")
    mb = path.stat().st_size / 1e6
    return {"file": path.name, "rows": int(len(df)), "cols": int(df.shape[1]), "mb": round(mb, 2)}


def build_sales() -> dict:
    df = pd.read_parquet(DERIVED / "sales_fact.parquet")
    # Keep sold_to_sap as string codes for Israel split (1797 UMI / 1799 UTI)
    if "sold_to_sap" in df.columns:
        sap = pd.to_numeric(df["sold_to_sap"], errors="coerce")
        df["sold_to_sap"] = sap.apply(lambda x: "" if pd.isna(x) else str(int(x)))
    return _write(df, OUT / "01_all_sales_isze_to_distributor.csv")


def build_warranty() -> dict:
    # Line-level claim grain (currency already on claim_eur where normalised upstream)
    grain = pd.read_csv(DERIVED / "warranty_raw_grain.csv", low_memory=False)
    grain.insert(0, "dataset", "warranty_raw_grain")
    # Stack commercial summary tables for the same GPT session (tagged)
    frames = [grain]
    for f in sorted(WARR_COMM.glob("*.csv")):
        part = pd.read_csv(f, low_memory=False)
        part.insert(0, "dataset", f.stem)
        frames.append(part)
    merged = pd.concat(frames, ignore_index=True, sort=False)
    return _write(merged, OUT / "02_all_warranty.csv")


def build_sales_to_dealer() -> dict:
    files = sorted(DERIVED.glob("dealer_sellout_long_*.csv"))
    if not files:
        raise FileNotFoundError("no dealer_sellout_long_*.csv")
    frames = []
    for f in files:
        part = pd.read_csv(f, low_memory=False)
        part.insert(0, "merge_source_file", f.name)
        frames.append(part)
    merged = pd.concat(frames, ignore_index=True, sort=False)
    return _write(merged, OUT / "03_all_sales_to_dealer.csv")


def copy_layer_extras() -> list[dict]:
    """Extra layers GPT needs for leakage / customer packs — without inventing numbers."""
    extras = [
        ("04_gps_spu_by_distributor.csv", DERIVED / "gps_spu_by_distributor.csv"),
        ("05_pms_opportunity_matrix.csv", DERIVED / "pms_opportunity_matrix.csv"),
        ("06_pms_capture_by_db_year.csv", DERIVED / "pms_capture_by_db_year.csv"),
        ("07_uio_ld_n35_share.csv", ROOT / "03_analytics" / "Isuzu" / "prism" / "data" / "uio_ld_n35_share.csv"),
        ("08_wallet_waterfall.csv", DERIVED / "wallet_waterfall.csv"),
        ("09_aim_pn_classification_v2.csv", DERIVED / "aim_pn_classification_v2.csv"),
        ("10_dealer_sellout_aim_gps_vs_billing_2025.csv", DERIVED / "dealer_sellout_aim_gps_vs_billing_2025.csv"),
        ("11_mix_genuine_bvp_pms.csv", DERIVED / "mix_genuine_bvp_pms.csv"),
        ("12_network_percentile.csv", DERIVED / "network_percentile.csv"),
    ]
    meta = []
    for dest_name, src in extras:
        if not src.exists():
            meta.append({"file": dest_name, "status": "MISSING", "source": str(src)})
            continue
        df = pd.read_csv(src, low_memory=False) if src.suffix.lower() == ".csv" else None
        if df is None:
            meta.append({"file": dest_name, "status": "SKIP", "source": str(src)})
            continue
        info = _write(df, OUT / dest_name)
        info["source"] = str(src.relative_to(ROOT)).replace("\\", "/")
        info["status"] = "OK"
        meta.append(info)
    return meta


def write_readme(core: list[dict], extras: list[dict]) -> None:
    lines = [
        "# GPT pack — sales / warranty / sales-to-dealer",
        "",
        f"**Built:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Folder:** `{OUT}`",
        "",
        "## Why three cores (do not blend them)",
        "",
        "| Layer | File | What it is | Why it matters |",
        "|---|---|---|---|",
        "| **1. ISZE → distributor billing** | `01_all_sales_isze_to_distributor.csv` | What we invoiced distributors (line grain from `sales_fact`) | The euro we actually booked. GPS capture %, mix, and “what we billed” start here. Israel: split on `sold_to_sap` **1797 = UMI**, **1799 = UTI** — never blend. |",
        "| **2. Warranty claims** | `02_all_warranty.csv` | Claim lines (`dataset=warranty_raw_grain`) plus commercial summary tables (other `dataset=` tags) | Quality / loyalty / who-pays. Not a substitute for scheduled service demand (consumables barely appear). |",
        "| **3. Distributor → dealer sales** | `03_all_sales_to_dealer.csv` | What distributors sold into their dealer networks | The only view of sell-through. Needed for leakage vs billing, dealer packs, and “share with customers”. Coverage is partial by market. |",
        "",
        "## Extra layers (advantages for analysis / customer share)",
        "",
        "| File | Role |",
        "|---|---|",
        "| `04_gps_spu_by_distributor.csv` | Target spend per truck vs billed — the GPS denominator |",
        "| `05_pms_opportunity_matrix.csv` | Category gaps in euro (clutch, pads, …) — customer opportunity ranking |",
        "| `06_pms_capture_by_db_year.csv` | PMS total capture by market / year |",
        "| `07_uio_ld_n35_share.csv` | Light vs heavy truck mix inside LD (Portugal **0.6364** from official registrations) |",
        "| `08_wallet_waterfall.csv` | Ceiling build-up (do not silently rebuild; read-only for GPT) |",
        "| `09_aim_pn_classification_v2.csv` | Parts family spine for mix / leakage by family |",
        "| `10_dealer_sellout_aim_gps_vs_billing_2025.csv` | Billing vs sales-to-dealer bridge where coverage exists |",
        "| `11_mix_genuine_bvp_pms.csv` | Genuine vs total mix (total capture stays primary) |",
        "| `12_network_percentile.csv` | Peer ranking context for customer conversations |",
        "",
        "## Hard rules for GPT",
        "",
        "1. Lead findings with **euro + parts family + vehicles in service** — never piece counts alone.",
        "2. Primary PMS lens = **total** sales / capture; genuine is an extra lens.",
        "3. UTI ≠ UMI; IUK ≠ ITUK.",
        "4. Do not invent a price increase narrative; pricing increase figures are out of scope for this pack.",
        "5. Warranty cannot prove maintenance intervals.",
        "",
        "## Build receipt",
        "",
        "```json",
        json.dumps({"core": core, "extras": extras}, indent=2),
        "```",
        "",
    ]
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    core = [build_sales(), build_warranty(), build_sales_to_dealer()]
    extras = copy_layer_extras()
    write_readme(core, extras)
    manifest = {
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "out_dir": str(OUT),
        "core": core,
        "extras": extras,
        "portugal_n35_share": {
            "value": 0.6364,
            "basis": "imotors_parc_bands",
            "source": "Imotors_Portugal_UIO_GPS_PMS_Study.xlsx UIO_Rebuild 2025 N35 1521.31 / N-series 2390.31",
        },
    }
    (OUT / "_MANIFEST.json").write_bytes(
        (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
