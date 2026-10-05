import pandas as pd

path = r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\PUBLISHED_BAND_PN_DIFF_44_2026-09-23.csv"
c = pd.read_csv(path, dtype=str).fillna("")
need = ["pn", "pms_category", "published_band_list", "corrected_band", "why_they_disagree",
        "eur_published_band_list_basis", "eur_corrected_mapping_basis",
        "published_band_file_band", "hidden_nmr_token"]
print("rows", len(c), "cols", len(c.columns))
print("required cols non-blank:", not (c[need] == "").any().any())
eur = pd.to_numeric(c.eur_corrected_mapping_basis)
free = c.hidden_nmr_token == "no"
print("euro total        ", round(eur.sum(), 2))
print("free rows         ", int(free.sum()), "eur", round(eur[free].sum(), 2))
print("parked rows       ", int((~free).sum()), "eur", round(eur[~free].sum(), 2))
print()
print("no-band rows:")
nb = c[c.corrected_band.str.startswith("(no band")]
print(nb[["pn", "published_band_list", "published_band_file_band", "corrected_band",
          "hidden_nmr_token"]].to_string(index=False))
print()
print("columns:", list(c.columns))
