"""Probe: UK next-harvest PN shortlist from ledger + epc euros. Read-only."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
WT = Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b")
DERIVED = WT / "01_data" / "00_derived"
MAIN_D = ROOT / "01_data" / "00_derived"
OUT = ROOT / "01_data" / "90_INBOX"

ELIGIBLE_PNS = {
    "8970622940",
    "8974995480",
    "8975546610",
    "8976739570",
    "8981394280",
    "8981402650",
    "8981596930",
    "8981941190",
    "8982399830",
    "8982705240",
    "8982831940",
    "8983214130",
}

# Families that already unlock on KS exact_oem + £10, or focus walls
TARGET_FAMS = [
    "brake_pad",
    "oil_filter",
    "air_filter",
    "fuel_filter",
    "blower_filter",
    "clutch_pressure_plate",
    "brake_shoe",
    "clutch_disc",
    "cabin_filter",
]


def host(u: object) -> str:
    s = str(u or "")
    if "://" not in s:
        return ""
    return s.split("://", 1)[1].split("/", 1)[0].lower()


def main() -> None:
    epc = pd.read_csv(MAIN_D / "epc_decode_worklist.csv", dtype={"part_number": str})
    ledger = pd.read_parquet(DERIVED / "price_observations.parquet")
    uk = ledger[ledger["country"] == "UK"].copy()
    uk["host"] = uk["source_url"].map(host)
    uk["part_no"] = uk["part_no"].astype(str)

    exact = uk[uk["match_method"] == "exact_oem"]
    cat = uk[uk["match_method"] == "category_only"]
    exact_pns = set(exact["part_no"])
    cat_pns = set(cat["part_no"])
    any_uk = set(uk["part_no"])

    # Host yield table
    host_rows = []
    for h, g in exact.groupby("host"):
        ready = g[
            g["delivery_included"].notna()
            & g["delivery_cost_amount"].notna()
            & g["vat"].notna()
        ]
        host_rows.append(
            {
                "host": h or "(no url / eucon survey)",
                "exact_oem_rows": int(len(g)),
                "exact_oem_pns": int(g["part_no"].nunique()),
                "delivery_tax_cost_ready": int(len(ready)),
                "loaders": sorted(g["loader"].dropna().astype(str).unique().tolist()),
            }
        )
    host_df = pd.DataFrame(host_rows).sort_values(
        "exact_oem_rows", ascending=False
    )

    # KS exact without £10 cost (body/rotor wall — not harvest)
    ks_exact = exact[exact["host"].str.contains("ks-international", na=False)]
    ks_no_cost = ks_exact[ks_exact["delivery_cost_amount"].isna()]

    sub = epc[epc["pms_category"].isin(TARGET_FAMS)].copy()
    sub["part_number"] = sub["part_number"].astype(str)
    sub = sub.drop_duplicates("part_number")
    sub["eur_all"] = pd.to_numeric(sub["eur_all"], errors="coerce").fillna(0.0)
    sub = sub.sort_values("eur_all", ascending=False)

    def status(pn: str) -> str:
        if pn in ELIGIBLE_PNS:
            return "already_eligible"
        if pn in exact_pns:
            return "has_uk_exact_oem_not_eligible"
        if pn in cat_pns and pn not in exact_pns:
            return "uk_category_only_wall"
        if pn in any_uk:
            return "uk_other_match"
        return "no_uk_ledger_row"

    sub["uk_status"] = sub["part_number"].map(status)

    # Prefer harvest targets: no UK row yet, or only category_only wall
    # (need a DIFFERENT page that prints OE — not more search relevance)
    # Also include high-billed exact_oem-not-eligible on TMC (blocked delivery — secondary)
    harvest = sub[sub["uk_status"] != "already_eligible"].copy()

    # Prioritize: no_uk_ledger_row first among high EUR, then category_only wall
    # (category_only means search failed OE-on-card — still need OE-on-card pages elsewhere)
    # then has_uk_exact not eligible (mostly TMC/eucon — not first harvest)
    prio = {
        "no_uk_ledger_row": 0,
        "uk_category_only_wall": 1,
        "uk_other_match": 2,
        "has_uk_exact_oem_not_eligible": 3,
    }
    harvest["prio"] = harvest["uk_status"].map(prio).fillna(9)
    harvest = harvest.sort_values(["prio", "eur_all"], ascending=[True, False])

    # Cap worklist: top 40 by the sort above, require eur_all > 0
    work = harvest[harvest["eur_all"] > 0].head(40).copy()

    # Annotate known hosts that already have exact_oem for this PN
    def hosts_for(pn: str) -> str:
        g = exact[exact["part_no"] == pn]
        if g.empty:
            return ""
        return ";".join(sorted({h for h in g["host"] if h}))

    def cat_hosts(pn: str) -> str:
        g = cat[cat["part_no"] == pn]
        if g.empty:
            return ""
        return ";".join(sorted({h for h in g["host"] if h}))

    work["uk_exact_oem_hosts"] = work["part_number"].map(hosts_for)
    work["uk_category_only_hosts"] = work["part_number"].map(cat_hosts)
    work["recommended_first_host"] = "www.ks-international.com"
    work["query_method"] = (
        "search Isuzu PN; accept ONLY if PN printed on product title/SKU/OE field; "
        "reject relevance-only category hits"
    )
    work["success_needs"] = "exact_oem + delivery stated + tax excl/incl + cost if delivery=no"

    # Write CSV
    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "UNIVERSE_UK_NEXT_HARVEST_PNS_20261007.csv"
    out_cols = [
        "part_number",
        "pms_category",
        "eur_all",
        "uk_status",
        "uk_exact_oem_hosts",
        "uk_category_only_hosts",
        "recommended_first_host",
        "query_method",
        "success_needs",
    ]
    # rename eur for clarity
    work_out = work[out_cols].rename(
        columns={"eur_all": "eur_all_billed_all_markets"}
    )
    work_out.to_csv(csv_path, index=False)

    summary = {
        "eligible_pns_baseline": sorted(ELIGIBLE_PNS),
        "eligible_count_baseline": len(ELIGIBLE_PNS),
        "wider_eligible_offers_baseline": 17,
        "note": "Baseline only — this probe does not claim growth",
        "host_exact_oem_yield": host_df.to_dict(orient="records"),
        "ks_exact_without_delivery_cost_rows": int(len(ks_no_cost)),
        "ks_exact_without_delivery_cost_pns": int(ks_no_cost["part_no"].nunique()),
        "status_counts_target_families": sub["uk_status"].value_counts().to_dict(),
        "worklist_n": int(len(work_out)),
        "worklist_path": str(csv_path),
        "worklist_top10": work_out.head(10).to_dict(orient="records"),
        "recommended_first_host": "www.ks-international.com",
        "why_first_host": (
            "Only UK host with exact_oem rows that already pass delivery+tax+cost "
            "(17 eligible offers). TMC has 55 exact_oem but no flat under-£150 carriage."
        ),
    }
    sum_path = OUT / "_uk_next_harvest_probe_summary_20261007.json"
    sum_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2)[:4000])
    print("WROTE", csv_path)
    print("WROTE", sum_path)


if __name__ == "__main__":
    main()
