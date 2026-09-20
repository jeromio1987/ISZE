"""Build short OE-PN scrape list + cheat sheet from oem_peer_basket.csv."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT_DIR = Path(__file__).resolve().parent
SRC = OUT_DIR / "oem_peer_basket.csv"

FILTER_BRAKE = {
    "oil_filter",
    "fuel_filter",
    "air_filter",
    "blower_filter",
    "urea_filter",
    "brake_pad",
    "brake_rotor",
    "brake_shoe",
}
# Categories already iam_derived in latest resolved alloc run (filters/brakes subset).
IAM_DERIVED = {
    "fuel_filter",
    "air_filter",
    "blower_filter",
    "brake_pad",
    "brake_rotor",
}
MARKET_RANK = {"IUK": 0, "GERMANY": 1, "LCV": 2}


def main() -> None:
    df = pd.read_csv(SRC)
    oe = (
        df["peer_oe_pn"].notna()
        & (df["peer_oe_pn"].astype(str).str.strip() != "")
        & (df["peer_oe_pn"].astype(str).str.lower() != "nan")
    )
    street_blank = (
        df["peer_street_eur"].isna()
        | (df["peer_street_eur"].astype(str).str.strip() == "")
        | (df["peer_street_eur"].astype(str).str.lower() == "nan")
    )
    status_ok = df["status"].isin(["needs_scrape", "mapped_oe_pn"])
    sub = df[oe & street_blank & status_ok].copy()

    sub["peer_oe_pn"] = sub["peer_oe_pn"].astype(str).str.strip()
    sub["_mkt"] = sub["peer_market"].map(MARKET_RANK).fillna(9)
    sub["_cat"] = sub["pms_category"].map(lambda c: 0 if c in FILTER_BRAKE else 1)
    sub["_rev"] = pd.to_numeric(sub["isze_rev_cy2025_eur"], errors="coerce").fillna(0)
    sub = sub.sort_values(["_cat", "_mkt", "_rev"], ascending=[True, True, False])
    uniq = sub.drop_duplicates(subset=["peer_oe_pn"], keep="first").copy()

    def pri(r: pd.Series) -> int:
        fb = r["pms_category"] in FILTER_BRAKE
        m = r["peer_market"]
        if fb and m in ("IUK", "GERMANY"):
            return 1
        if fb and m == "LCV":
            return 2
        if m in ("IUK", "GERMANY"):
            return 3
        return 4

    uniq["priority"] = uniq.apply(pri, axis=1)
    uniq = uniq.sort_values(["priority", "_rev"], ascending=[True, False]).reset_index(
        drop=True
    )

    def short_notes(r: pd.Series) -> str:
        bits = []
        if r["pms_category"] in IAM_DERIVED:
            bits.append("cat iam_derived")
        elif r["pms_category"] in FILTER_BRAKE:
            bits.append("filter/brake")
        bits.append(f"basket status={r['status']}")
        bits.append("fill peer_street_eur retail/street EUR; no invent")
        return "; ".join(bits)

    out = pd.DataFrame(
        {
            "isze_pn": uniq["isze_pn"].astype(str),
            "pms_category": uniq["pms_category"],
            "peer_market": uniq["peer_market"],
            "peer_oem": uniq["peer_oem"],
            "peer_model": uniq["peer_model"],
            "peer_oe_pn": uniq["peer_oe_pn"],
            "peer_street_eur": "",
            "peer_street_native": "",
            "currency": "EUR",
            "fx_rate_to_eur": "",
            "fx_as_of": "",
            "source": "manual_scrape",
            "notes": uniq.apply(short_notes, axis=1),
            "priority": uniq["priority"],
        }
    )

    csv_path = OUT_DIR / "oem_peer_scrape_list.csv"
    out.to_csv(csv_path, index=False, encoding="utf-8")

    md = """# OEM peer street — manual scrape cheat sheet

**As of:** 2026-08-10  
**List:** `oem_peer_scrape_list.csv` (same folder)  
**Basket:** `oem_peer_basket.csv`  
**Arrange runbook:** `OEM_STREET_ARRANGE.md`  
**Ingest:** `ingest_oem_peer_street.py`  
**Audience:** internal / internal fill only — not a dashboard ship.

---

## What to fill

| Column | Rule |
|--------|------|
| `peer_oe_pn` | Already mapped — search key (do not invent / swap) |
| `peer_street_eur` | **Retail / street EUR** (preferred) |
| `peer_street_native` | Alt: price in local currency |
| `currency` | `EUR` or e.g. `GBP` when using native |
| `fx_rate_to_eur` | If native: multiply factor (native × rate → EUR); label source |
| `fx_as_of` | FX date (ISO) when converting |
| `source` | Where you got it (dealer site, parts portal, phone quote, …) |
| `priority` | 1 = IUK/DE filters·brakes · 2 = LCV filters·brakes · 3–4 = clutch / other |

After fill, run `ingest_oem_peer_street.py` (do not hand-edit basket unless you must). Leave blanks if not found — **never invent**.

---

## Isuzu compare side (not the scrape target)

When you compare peer street to Isuzu:

- Isuzu genuine street = **PR00 × 1.785** (= 1.40 × 1.275).
- Do **not** compare peer street to raw PR00/IE40 list.

---

## Do not use as street

| Bad source | Why |
|------------|-----|
| Eucon 2023 OEM survey **list GBP / OEM list** | List price, not street — see `_raw/Eucon_PriceSurvey_2023_QA.md` |
| Eucon IAM competitor PN | IAM lens — not `peer_oe_pn` / not OEM peer street |
| Autodoc/KS on **Isuzu PN** | Feeds `iam_derived`, not peer OE street |
| Invented / guessed OE or EUR | Blocks `oem_benchmark` upgrade |

---

## Scope of this list

- Rows with `peer_oe_pn` filled and `peer_street_eur` blank (`needs_scrape`).
- **Deduped by unique `peer_oe_pn`** (one scrape per OE).
- Prefer filters/brakes (several already `iam_derived`) and approved peers: IUK/GERMANY DAF, LCV Toyota Hilux / Ford Ranger.
- Unique OEs available today: see CSV row count (all included; under the ~30–60 target).

After fill (≥3 peers/category with street), engine can upgrade category `basis` → `oem_benchmark` via `premiums.load_oem_benchmark_from_basket()`.
"""
    md_path = OUT_DIR / "oem_peer_scrape_list.md"
    md_path.write_text(md, encoding="utf-8")

    print(f"CSV: {csv_path}")
    print(f"MD:  {md_path}")
    print(f"unique_oe: {out['peer_oe_pn'].nunique()}")
    print(f"rows: {len(out)}")


if __name__ == "__main__":
    main()
