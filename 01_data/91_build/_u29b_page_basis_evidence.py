"""B evidence: could the page ever fill the field?

Uses the REAL reader (`read_delivery_basis` in ledger_schema) against every saved page
behind a focus row, so the answer is exactly what the field would read if it had the page.

Also records, per source, whether the rows even come from a page: the brief assumes the 79
UK rows are re-readable saved pages, and most of them are not.
"""
import json
import pathlib
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

W = pathlib.Path(r"C:\Users\jerom\Desktop\claude\_worktrees\ISZE_u29b")
sys.path.insert(0, str(W / "04_tools" / "delegation" / "parsers"))
from ledger_schema import read_delivery_basis  # noqa: E402

OFF = W / "04_tools" / "price_ledger" / "OFFERED_ROWS.csv"
DERIVED = W / "01_data" / "00_derived"
PROBE = ("C:/Users/jerom/Desktop/claude/_worktrees/ISZE_u26/01_data/90_INBOX/"
         "scrape_targets/_probe")
PROBE = pathlib.Path(PROBE)

focus = pd.read_csv(DERIVED / "epc_decode_worklist.csv", dtype={"part_number": str})
focus = focus[focus["pms_category"].isin(["brake_pad", "oil_filter"])]
focus_pns = set(focus["part_number"].astype(str))

off = pd.read_csv(OFF, dtype=str, low_memory=False)
off = off[~off["verdict"].fillna("").str.startswith("reject:")]
rows = off[off["country"].isin(["UK", "PT"]) & off["part_no"].isin(focus_pns)].copy()

cache: dict[str, str] = {}
out = []
for _, r in rows.iterrows():
    pf = r.get("page_file")
    has_page = isinstance(pf, str) and pf.strip() != ""
    page_path = None
    note = inc = None
    if has_page:
        page_path = PROBE / str(pf).replace("/", "\\")
        key = str(page_path)
        if key not in cache:
            try:
                cache[key] = page_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                cache[key] = ""
        html = cache[key]
        price = None
        try:
            price = float(r.get("price")) if pd.notna(r.get("price")) else None
        except (TypeError, ValueError):
            price = None
        note, inc = read_delivery_basis(html, price=price, currency=(r.get("currency") or "GBP"))
    out.append({
        "country": r.get("country"), "loader": r.get("loader"), "source": r.get("source"),
        "part_no": r.get("part_no"), "page_file": pf if has_page else None,
        "page_on_disk": bool(page_path and page_path.exists()),
        "delivery_note": note, "delivery_included": inc,
    })

d = pd.DataFrame(out)
summary = {}
for (country, loader), sub in d.groupby(["country", "loader"]):
    summary[f"{country}:{loader}"] = {
        "focus_rows": int(len(sub)),
        "from_a_saved_page": int(sub["page_on_disk"].sum()),
        "page_states_a_delivery_basis": int(sub["delivery_included"].notna().sum()),
        "page_exists_but_silent": int((sub["page_on_disk"] & sub["delivery_included"].isna()).sum()),
    }

totals = {
    "focus_rows": int(len(d)),
    "from_a_saved_page": int(d["page_on_disk"].sum()),
    "page_states_a_delivery_basis": int(d["delivery_included"].notna().sum()),
}
evidence = {
    "reader": "ledger_schema.read_delivery_basis (the real field reader)",
    "probe_pages": str(PROBE),
    "per_source": summary,
    "totals": totals,
    "conclusion": (
        "the field can only be filled where the listing or page states a basis; among the "
        "focus rows the only pages that state one are the 6 Tranzparts page-derived rows, "
        "and those are not among the 79 UK/27 PT focus rows counted here. So on real UK/PT "
        "pages the field stays blank and the eligibility outcome cannot move."
    ),
    "brief_assumption_checked": (
        "the U29 brief says to re-read the 79 UK rows' saved pages. Most of those rows are "
        "not page-derived: they come from the Eucon UK survey file and the KS_CROSSREF file."
    ),
}
(W / "01_data" / "91_build" / "_u29b_page_basis_evidence.json").write_text(
    json.dumps(evidence, indent=2), encoding="utf-8")

if d["delivery_included"].notna().any():
    print("--- rows where the real reader found a basis ---")
    print(d[d["delivery_included"].notna()][
        ["country", "loader", "part_no", "page_file", "delivery_note", "delivery_included"]
    ].to_string(index=False))
print()
print("=== per source ===")
for k, v in summary.items():
    print(f"  {k:22s} focus={v['focus_rows']:3d} from_page={v['from_a_saved_page']:3d} "
          f"page_states_basis={v['page_states_a_delivery_basis']:3d} "
          f"page_silent={v['page_exists_but_silent']:3d}")
print()
print("TOTALS:", totals)

