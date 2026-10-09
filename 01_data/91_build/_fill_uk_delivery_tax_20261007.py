# -*- coding: utf-8 -*-
import csv
from pathlib import Path

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
INBOX = ROOT / "01_data" / "90_INBOX"
src = INBOX / "UNIVERSE_UK_DELIVERY_TAX_HAND_COLLECT_20261007.csv"
out_csv = INBOX / "UNIVERSE_UK_DELIVERY_TAX_FILLED_20261007.csv"
out_md = INBOX / "UNIVERSE_UK_DELIVERY_TAX_FILLED_20261007.md"

KS_NOTE = (
    'KS Delivery Information: "There is a minimum charge of UK Pounds £10.00 '
    'e.g. Filter kits, clutch kit, exhaust muffler, tail pipe etc" '
    "(Delivery & Carriage Charge Information / UK Mainland Delivery). "
    "Live page https://www.ks-international.com/delivery-information 2026-10-07."
)
KS_COST = "GBP 10.00"
TMC_NOTE = (
    'TMC Delivery page: "For UK Mainland* customers, we offer a free delivery option on '
    'qualifying orders over £150." Also: "The appropriate delivery charge will be added '
    'automatically at checkout." Listed prices on this sheet are under £150, so delivery '
    "is not included in the listing price. Live https://www.tmcgroup.co.uk/delivery/ 2026-10-07."
)

rows = list(csv.DictReader(src.open(encoding="utf-8-sig")))
filled = []
attempted = []
for r in rows:
    url = (r.get("url") or "").strip()
    host = (r.get("host") or "").lower()
    loader = (r.get("loader") or "").lower()
    source = (r.get("source") or "").lower()
    if not url.startswith("http"):
        continue
    attempted.append(r["obs_id"])
    is_ks = ("ks-international" in host) or loader.startswith("ks") or ("ks international" in source)
    is_tmc = ("tmcgroup" in host) or (loader == "tmc") or ("t & m" in source) or ("t&m" in source)
    out = dict(r)
    if is_ks:
        out["delivery_basis"] = "no"
        out["delivery_note_hand"] = KS_NOTE
        out["delivery_cost_if_stated"] = KS_COST
        out["tax_basis"] = "excluded"
        out["notes"] = (out.get("notes") or "") + " | FILLED from live KS Delivery Information + Excl. VAT price label"
        filled.append(out)
    elif is_tmc:
        try:
            price = float(out.get("price") or 0)
        except ValueError:
            price = 0.0
        if price > 0 and price < 150:
            out["delivery_basis"] = "no"
            out["delivery_note_hand"] = TMC_NOTE
            out["delivery_cost_if_stated"] = ""
            out["tax_basis"] = ""
            out["notes"] = (out.get("notes") or "") + " | FILLED delivery from live TMC /delivery/ (under £150 threshold); tax not stated on PDP"
            filled.append(out)

fields = list(rows[0].keys())
with out_csv.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(filled)

p1 = [x for x in filled if str(x.get("priority")) == "1"]
p2 = [x for x in filled if str(x.get("priority")) == "2"]
ks_n = sum(1 for x in filled if "ks-international" in (x.get("host") or "").lower() or str(x.get("loader") or "").startswith("ks"))
tmc_n = sum(1 for x in filled if "tmcgroup" in (x.get("host") or "").lower() or (x.get("loader") or "") == "tmc")

md_lines = [
    "# UK delivery/tax filled — 2026-10-07",
    "",
    "## Counts",
    f"- URL rows attempted: {len(attempted)}",
    f"- Rows filled (in this file): {len(filled)} (priority 1: {len(p1)}; priority 2: {len(p2)})",
    f"- KS International: {ks_n}",
    f"- T & M Commercials: {tmc_n}",
    "- Eucon survey / no-URL rows: skipped (no shop page)",
    "",
    "## Evidence (not invented)",
    "",
    "### KS International",
    "- Live page: https://www.ks-international.com/delivery-information (HTTP 200)",
    "- Saved under `01_data/90_INBOX/_uk_delivery_live_20261007/`",
    "- Quote: minimum UK mainland carriage charge GBP 10.00 for filter kits → delivery_basis=no, cost GBP 10.00",
    "- Tax: listing wrappers `data-label=\"Excl. VAT\"` → tax_basis=excluded",
    "",
    "### T & M Commercials",
    "- Live page: https://www.tmcgroup.co.uk/delivery/ (HTTP 200)",
    "- Quote: free delivery option on UK Mainland orders over £150; otherwise charge at checkout",
    "- Filled TMC rows priced under £150 → delivery_basis=no; cost blank (no fixed amount)",
    "- Product pages: bare £ price only → tax_basis left blank",
    "",
    "### Not filled",
    "- Eucon UK IAM survey rows (no source_url)",
    "",
    "## Parquet mapping",
    "- delivery_basis no → delivery_included=no",
    "- delivery_note_hand → delivery_note",
    "- tax_basis excluded → vat=excl (KS only)",
]
out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
print("filled", len(filled), "p1", len(p1), "p2", len(p2), "ks", ks_n, "tmc", tmc_n)
print("wrote", out_csv)
