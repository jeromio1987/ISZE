# -*- coding: utf-8 -*-
"""Pass2: upgrade all category_only rows whose part_no is on the PDP OE list for that SKU."""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
U29B = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b")
PARQUET = U29B / "01_data" / "00_derived" / "price_observations.parquet"
OUT = ROOT / "01_data" / "90_INBOX" / "_uk_ks_pdp_oe_upgrade_20261007"

sys.path.insert(0, str(ROOT / "04_tools" / "delegation" / "parsers"))
from ledger_schema import find_pns  # noqa: E402

DELIVERY_NOTE = (
    "Live KS UK mainland £10 minimum (filter / clutch / muffler / tail pipe) "
    "— UNIVERSE_UK_KS_POLICY_SCOPE_2026-10-07"
)


def oe_pns_from_html(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    found: list[str] = []
    for row in soup.select(
        "#product-attribute-specs-table tr, .additional-attributes tr, table.data.table tr"
    ):
        th = row.select_one("th")
        td = row.select_one("td")
        label = th.get_text(" ", strip=True) if th else ""
        val = td.get_text(" ", strip=True) if td else ""
        lab = label.lower()
        if "oe" in lab or "equivalent" in lab or "oem" in lab:
            found.extend(find_pns(val) or [])
    for script in soup.select('script[type="application/ld+json"]'):
        found.extend(find_pns(script.string or script.get_text()) or [])
    out: list[str] = []
    seen: set[str] = set()
    for p in found:
        if p and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def main() -> int:
    checks = json.loads((OUT / "pdp_checks_20261007.json").read_text(encoding="utf-8"))
    metrics_path = (
        U29B
        / "01_data"
        / "00_derived"
        / "market_data_gap_coverage_uk_wider_exact_20261007.metrics.json"
    )
    before = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
    print("BEFORE eligible_rows", before.get("eligible_rows"), "eligible_pns", before.get("eligible_pns"))

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bak = PARQUET.with_name(f"price_observations.parquet.bak_{ts}_before_ks_pdp_oe_pass2")
    shutil.copy2(PARQUET, bak)
    print("backup2", bak)

    df = pd.read_parquet(PARQUET)
    extra_obs: list[dict] = []
    per_sku: list[dict] = []
    for c in checks:
        if c.get("verdict") != "upgrade_exact_oem":
            continue
        sku = c["competitor_pn"]
        pdp_html = OUT / c["pdp_html"]
        if not pdp_html.exists():
            print("missing html", pdp_html)
            continue
        html = pdp_html.read_text(encoding="utf-8", errors="replace")
        oes = oe_pns_from_html(html)
        per_sku.append({"sku": sku, "oe_pns": oes, "pdp_url": c.get("pdp_url")})
        mask = (
            (df["loader"] == "ks")
            & (df["match_method"].astype(str).str.lower() == "category_only")
            & (df["competitor_pn"].astype(str) == sku)
            & (df["part_no"].astype(str).isin(oes))
        )
        idxs = df.index[mask].tolist()
        if not idxs:
            continue
        quote = ", ".join(oes[:8])
        evid = (
            "PDP OE upgrade 2026-10-07 pass2: Isuzu PN on KS OE Equivalent Part Number "
            f"(«{quote}»). Was category_only."
        )
        for idx in idxs:
            pn = str(df.at[idx, "part_no"])
            df.at[idx, "match_method"] = "exact_oem"
            old = str(df.at[idx, "description"] or "")
            if "PDP OE upgrade" not in old:
                df.at[idx, "description"] = (old + " — " + evid).strip(" —")
            if str(df.at[idx, "vat"]).lower() != "excl":
                df.at[idx, "vat"] = "excl"
            df.at[idx, "delivery_included"] = "no"
            df.at[idx, "delivery_cost_amount"] = 10.0
            df.at[idx, "delivery_cost_currency"] = "GBP"
            df.at[idx, "delivery_note"] = DELIVERY_NOTE
            if c.get("pdp_url"):
                df.at[idx, "source_url"] = c["pdp_url"]
            extra_obs.append({"obs_id": str(df.at[idx, "obs_id"]), "sku": sku, "part_no": pn})
        print(f"SKU {sku}: OE={oes} extra_rows={len(idxs)}")

    print("extra patched", len(extra_obs))
    df.to_parquet(PARQUET, index=False)
    (OUT / "pdp_pass2_extra.json").write_text(
        json.dumps({"backup": str(bak), "extra_obs": extra_obs, "per_sku_oe": per_sku}, indent=2),
        encoding="utf-8",
    )
    m = df["description"].astype(str).str.contains("PDP OE upgrade", na=False)
    print("total PDP upgrade exact_oem rows", int(m.sum()))
    print(
        "ks category_only remaining",
        int(((df["loader"] == "ks") & (df["match_method"] == "category_only")).sum()),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
