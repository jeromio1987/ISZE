# -*- coding: utf-8 -*-
from pathlib import Path

OUT = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\_uk_ks_pilot_20261007")
OUT.mkdir(parents=True, exist_ok=True)

accepted_hdr = (
    "obs_id,part_no,match_method,competitor_brand,competitor_pn,description,source,"
    "source_url,country,observed_at,vintage,price,price_avg,currency,price_eur,fx_note,"
    "vat,price_type,stock,n_obs,loader,delivery_note,delivery_included,"
    "delivery_cost_amount,delivery_cost_currency,family,pilot_verdict\n"
)
(OUT / "staging_exact_oem_accepted_20261007.csv").write_text(accepted_hdr, encoding="utf-8")

rejects = [
    ("5876150170", "fuel_filter"),
    ("1876100934", "fuel_filter"),
    ("1876101132", "air_filter"),
    ("8975488420", "blower_filter"),
    ("8975425390", "fuel_filter"),
    ("8982120690", "clutch_disc"),
    ("8975056801", "brake_pad"),
    ("8978279610", "brake_pad"),
]
lines = ["part_no,family,reject_class,reject_reason,search_url,html_path\n"]
for pn, fam in rejects:
    lines.append(
        f"{pn},{fam},no_product_cards,"
        '"KS search: Your search returned no results",'
        f"https://www.ks-international.com/catalogsearch/result/?q={pn},"
        f"search_{pn}.html\n"
    )
(OUT / "pilot_rejects_20261007.csv").write_text("".join(lines), encoding="utf-8")
print("wrote", OUT / "staging_exact_oem_accepted_20261007.csv")
print("wrote", OUT / "pilot_rejects_20261007.csv")
