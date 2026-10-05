"""Read-only probe 5: where the three live projects overlap.

AIM master (classification + figure key) x billed tier list x crossref graph x EPC queue.
Nothing written, nothing fetched.
"""
import pandas as pd

pd.set_option("display.width", 260)
ROOT = r"C:\Users\jerom\Desktop\claude\ISZE"


def z(s):
    return s.astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(10)


t = pd.read_csv(ROOT + r"\04_tools\delegation\state\refresh_tiers_LOCAL.csv", dtype={"part_no": str})
t["part_no"] = z(t["part_no"])
t["billed_eur_t12m"] = pd.to_numeric(t["billed_eur_t12m"])
tot = t["billed_eur_t12m"].sum()

m = pd.read_csv(ROOT + r"\01_data\00_derived\AIM_Master_PN_Categories_Figkey_20260924.csv", dtype=str)
m["part_number"] = z(m["part_number"])
m["l12m_billed_eur"] = pd.to_numeric(m["l12m_billed_eur"], errors="coerce")
print("AIM master rows: %d, columns %d" % (len(m), len(m.columns)))
print("   with a figure key : %d (%.1f%%)" % (m.figure_key.notna().sum(), 100 * m.figure_key.notna().mean()))
print("   line_kind values  : %s" % m.line_kind.value_counts(dropna=False).to_dict())
print("   aim_level_1 known : %d (%.1f%%)"
      % ((m.aim_level_1.notna() & ~m.aim_level_1.isin(["Unknown", "Unknown Review"])).sum(),
         100 * (m.aim_level_1.notna() & ~m.aim_level_1.isin(["Unknown", "Unknown Review"])).mean()))
print("   sum of l12m_billed_eur on the master: EUR %s" % f"{m.l12m_billed_eur.sum():,.0f}")

# how much of the billed book does the master actually classify?
onm = t.part_no.isin(set(m.part_number))
print("\ntier list vs master: %d of %d parts on the master (%.1f%%), EUR %s (%.1f%% of billed)"
      % (onm.sum(), len(t), 100 * onm.mean(), f"{t[onm].billed_eur_t12m.sum():,.0f}",
         100 * t[onm].billed_eur_t12m.sum() / tot))
for tr in ["A", "B", "C"]:
    tt = t[t.tier == tr]
    mm = tt.part_no.isin(set(m.part_number))
    print("   tier %s: %4d of %4d (%.1f%%)" % (tr, mm.sum(), len(tt), 100 * mm.mean()))

# crossref availability x master x tier
old = pd.read_csv(ROOT + r"\02_dashboards\Data\01_Pricing\_raw\eucon_crossref_iam_20260329.csv", dtype=str)
old["isze_pn"] = z(old["isze_pn"])
e = pd.read_excel(ROOT + r"\01_data\Eucon_Online28072025.xlsx",
                  sheet_name="Fresh list_Export_28072025_0932", dtype=str)
e["pn"] = z(e["Searched Part Number"])
r = pd.read_excel(ROOT + r"\01_data\Eucon_March.xlsx", sheet_name="RRP MODE", dtype=str)
r["pn"] = z(r["Searched Part Number"])
survey = pd.read_excel(ROOT + r"\01_data\01_Pricing\_raw\Eucon_PriceSurvey_UK_2023_IAM_rawdata_20240109.xlsx",
                      sheet_name=None, dtype=str)
survey_pn = set()
for d in survey.values():
    d.columns = [c.strip() for c in d.columns]
    w = d[d["Competitor Part Number"].fillna("").str.strip() != ""]
    survey_pn |= set(z(w["Isuzu Part Number"]))
b = pd.read_csv(ROOT + r"\01_data\00_derived\genuine_bvp_crossref.csv", dtype=str)
b["genuine_pn"] = z(b["genuine_pn"])

xref = set(old.isze_pn) | set(e.pn) | set(r.pn) | survey_pn | set(b.genuine_pn)
A = t[t.tier == "A"].copy()
A["on_master"] = A.part_no.isin(set(m.part_number))
A["has_xref"] = A.part_no.isin(xref)
print("\nTier A (%d parts) cross-tab: does it have a competitor crossref x is it on the AIM master" % len(A))
print(pd.crosstab(A.on_master, A.has_xref, margins=True).to_string())
print("\n   the quadrant that matters - Tier A, on the master, with NO crossref:")
gap = A[(A.on_master) & (~A.has_xref)]
print("     %d parts, EUR %s (%.1f%% of the billed book)"
      % (len(gap), f"{gap.billed_eur_t12m.sum():,.0f}", 100 * gap.billed_eur_t12m.sum() / tot))
print("     top 12 by billed value:")
print(gap.sort_values("billed_eur_t12m", ascending=False)
      .head(12)[["part_no", "billed_eur_t12m", "tier"]].to_string(index=False))

gap2 = A[(A.has_xref) & (~A.on_master)]
print("\n   Tier A with a crossref but NOT on the master: %d parts, EUR %s"
      % (len(gap2), f"{gap2.billed_eur_t12m.sum():,.0f}"))

# the EPC queue
q = pd.read_csv(ROOT + r"\01_data\91_build\export_aim_eq_20260924\queue.csv", dtype=str)
q["pn"] = z(q["pn"])
q["pr00_value_eur"] = pd.to_numeric(q["pr00_value_eur"], errors="coerce")
print("\nEPC queue (export_aim_eq_20260924/queue.csv): %d rows" % len(q))
print("   union with tier A: %d of the %d queue rows are Tier A parts"
      % (q.pn.isin(set(A.part_no)).sum(), len(q)))
print("   queue rows with a crossref today: %d" % q.pn.isin(xref).sum())
print("   queue rows already on the AIM master: %d" % q.pn.isin(set(m.part_number)).sum())
qt = t[t.part_no.isin(set(q.pn))]
print("   billed value of the queue: EUR %s" % f"{qt.billed_eur_t12m.sum():,.0f}")

# PMS parts inside tier A - the maintenance campaign overlap
fig = m.drop_duplicates("part_number").set_index("part_number")
A["aim_l1"] = A.part_no.map(fig.aim_level_1)
A["aim_l2"] = A.part_no.map(fig.aim_level_2)
A["figure_key"] = A.part_no.map(fig.figure_key)
print("\nTier A by AIM level 1 (top 15), with billed value:")
g = A.groupby(A.aim_l1.fillna("(not on master)")).agg(
    parts=("part_no", "size"), billed=("billed_eur_t12m", "sum"), xref=("has_xref", "sum"))
g = g.sort_values("billed", ascending=False).head(15)
g["billed"] = g.billed.map(lambda v: f"{v:,.0f}")
print(g.to_string())
