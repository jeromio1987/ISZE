"""Export AIM + figure-key table for Power BI (and Excel browse).

Primary deliverable for BVDV / Power BI: flat UTF-8 CSV, one row per part number.
Excel twin is the same table (one sheet) plus a short Coverage sheet.

Spine = aim_master_v2 (full catalogue). AIM labels prefer the latest
aim_pn_classification_20260920 overlay where the part is present.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
STAMP = date.today().strftime("%Y%m%d")
SRC_MASTER = DER / "aim_master_v2.csv"
SRC_CLASS = DER / "aim_pn_classification_20260920.csv"
OUT_XLSX = DER / f"AIM_Master_PN_Categories_Figkey_{STAMP}.xlsx"
OUT_CSV = DER / f"AIM_Master_PN_Categories_Figkey_{STAMP}.csv"
CMD = DER / f"OPEN_AIM_Master_PN_Categories_Figkey_{STAMP}.cmd"

# Stable names for Power BI relationships / DAX (no spaces).
COLS = [
    "part_number",
    "description",
    "description_source",
    "aim_level_1",
    "aim_level_2",
    "aim_level_3",
    "figure_key",
    "figure_no",
    "key_no",
    "figure_key_label",
    "line_kind",
    "aim_source",
    "l12m_billed_eur",
]


def clean(s: pd.Series) -> pd.Series:
    x = s.fillna("").astype(str).str.strip()
    return x.where(~x.str.lower().isin(["", "nan", "none", "null"]), "")


def prefer(fixed: pd.Series, raw: pd.Series) -> pd.Series:
    f = clean(fixed)
    r = clean(raw)
    return f.where(f != "", r)


def pn_key(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().str.upper()


def load_sales_desc() -> pd.Series:
    sf = pd.read_parquet(
        DER / "sales_fact.parquet",
        columns=["part_number", "description", "net_sales_value"],
    )
    sf["pn"] = pn_key(sf["part_number"])
    sf["description"] = clean(sf["description"])
    sf = sf[sf["description"] != ""]
    sf["eur"] = pd.to_numeric(sf["net_sales_value"], errors="coerce").fillna(0.0)
    g = (
        sf.groupby(["pn", "description"], as_index=False)["eur"]
        .sum()
        .sort_values("eur", ascending=False)
        .drop_duplicates("pn", keep="first")
    )
    return g.set_index("pn")["description"]


def load_apl_desc() -> pd.Series:
    frames = []
    for name in ("apl_pn_list_unique_20260812.csv", "apl_pn_list_long_20260812.csv"):
        p = DER / name
        if not p.exists():
            continue
        d = pd.read_csv(p, usecols=["part_number", "description"], dtype=str, low_memory=False)
        d["pn"] = pn_key(d["part_number"])
        d["description"] = clean(d["description"])
        d = d[d["description"] != ""].drop_duplicates("pn", keep="first")
        frames.append(d)
    if not frames:
        return pd.Series(dtype=str)
    all_ = pd.concat(frames, ignore_index=True).drop_duplicates("pn", keep="first")
    return all_.set_index("pn")["description"]


def load_price_desc() -> pd.Series:
    p = DER / "price_bp_weighted_compare_pn.csv"
    if not p.exists():
        return pd.Series(dtype=str)
    d = pd.read_csv(
        p,
        usecols=["part_number", "billed_description", "net_sales_value"],
        dtype=str,
        low_memory=False,
    )
    d["pn"] = pn_key(d["part_number"])
    d["description"] = clean(d["billed_description"])
    d["eur"] = pd.to_numeric(d["net_sales_value"], errors="coerce").fillna(0.0)
    d = d[d["description"] != ""].sort_values("eur", ascending=False).drop_duplicates(
        "pn", keep="first"
    )
    return d.set_index("pn")["description"]


def load_eq_desc() -> pd.Series:
    p = ROOT / "01_data" / "90_INBOX" / "_EQ_HIT_SESSION_20260919_RESULTS.csv"
    if not p.exists():
        return pd.Series(dtype=str)
    d = pd.read_csv(p, dtype=str, low_memory=False)
    if "pn" not in d.columns:
        return pd.Series(dtype=str)
    d["pn"] = pn_key(d["pn"])
    part = clean(d["eq_part_name"]) if "eq_part_name" in d.columns else pd.Series([""] * len(d))
    desc = clean(d["description"]) if "description" in d.columns else pd.Series([""] * len(d))
    d["description"] = part.where(part != "", desc)
    d = d[d["description"] != ""].drop_duplicates("pn", keep="first")
    return d.set_index("pn")["description"]


def load_epc_heavy_desc() -> pd.Series:
    p = DER / "epc_catalogue_heavy_20260919.csv"
    if not p.exists():
        return pd.Series(dtype=str)
    d = pd.read_csv(p, usecols=["part_number", "part_name"], dtype=str, low_memory=False)
    d["pn"] = pn_key(d["part_number"])
    d["description"] = clean(d["part_name"])
    d = d[d["description"] != ""].drop_duplicates("pn", keep="first")
    return d.set_index("pn")["description"]


def load_classification_norm_desc() -> pd.Series:
    """Normalised descriptions from the classification overlay."""
    p = SRC_CLASS
    if not p.exists():
        return pd.Series(dtype=str)
    d = pd.read_csv(p, usecols=["part_number", "description_norm"], dtype=str, low_memory=False)
    d["pn"] = pn_key(d["part_number"])
    d["description"] = clean(d["description_norm"])
    d = d[d["description"] != ""].drop_duplicates("pn", keep="first")
    return d.set_index("pn")["description"]


def coalesce_desc(
    base: pd.Series, pn: pd.Series, maps: list[tuple[str, pd.Series]]
) -> tuple[pd.Series, pd.Series]:
    desc = clean(base)
    src = pd.Series([""] * len(desc), index=desc.index, dtype=object)
    src = src.mask(desc != "", "aim_master")
    for label, m in maps:
        need = desc == ""
        if not need.any() or m.empty:
            continue
        got = clean(pn.map(m).fillna(""))
        take = need & (got != "")
        desc = desc.mask(take, got)
        src = src.mask(take, label)
    return desc, src


def main() -> None:
    master = pd.read_csv(SRC_MASTER, low_memory=False, dtype=str)
    pn = pn_key(master["part_number"])

    maps = [
        ("sales_fact_euro_top", load_sales_desc()),
        ("apl", load_apl_desc()),
        ("price_revision_billed", load_price_desc()),
        ("eq_session_20260919", load_eq_desc()),
        ("epc_heavy", load_epc_heavy_desc()),
        ("classification_norm", load_classification_norm_desc()),
    ]
    for label, m in maps:
        print(f"source {label}: {len(m)} PNs")

    description, desc_source = coalesce_desc(master["description"], pn, maps)

    cls = pd.DataFrame()
    if SRC_CLASS.exists():
        cls = pd.read_csv(SRC_CLASS, dtype=str, low_memory=False)
        cls["pn"] = pn_key(cls["part_number"])
        cls = cls.drop_duplicates("pn", keep="first").set_index("pn")

    aim_l1 = prefer(
        master.get("aim_l1_fixed", pd.Series([""] * len(master))), master["aim_l1"]
    )
    aim_l2 = prefer(master.get("aim_l2_fixed", pd.Series([""] * len(master))), master["aim_l2"])
    aim_l3 = clean(master["aim_l3"])
    fig_key = clean(master["fig_key"])
    line_kind = pd.Series(["part"] * len(master), dtype=object)
    aim_source = clean(master.get("aim_source", pd.Series([""] * len(master))))
    l12m = pd.to_numeric(master.get("l12m_billed_eur"), errors="coerce")

    if not cls.empty:
        if "aim_l1_fixed" in cls.columns:
            got = clean(pn.map(cls["aim_l1_fixed"]).fillna(""))
            aim_l1 = got.where(got != "", aim_l1)
        if "aim_l2_fixed" in cls.columns:
            got = clean(pn.map(cls["aim_l2_fixed"]).fillna(""))
            aim_l2 = got.where(got != "", aim_l2)
        if "aim_l3_fixed" in cls.columns:
            got = clean(pn.map(cls["aim_l3_fixed"]).fillna(""))
            aim_l3 = got.where(got != "", aim_l3)
        if "fig_key" in cls.columns:
            got = clean(pn.map(cls["fig_key"]).fillna(""))
            fig_key = fig_key.where(fig_key != "", got)
        if "line_kind" in cls.columns:
            got = clean(pn.map(cls["line_kind"]).fillna(""))
            line_kind = got.where(got != "", line_kind)
        if "aim_source" in cls.columns:
            got = clean(pn.map(cls["aim_source"]).fillna(""))
            aim_source = got.where(got != "", aim_source)
        if "l12m_billed_eur" in cls.columns:
            got = pd.to_numeric(pn.map(cls["l12m_billed_eur"]), errors="coerce")
            l12m = l12m.where(l12m.notna(), got)

    # Figure-key label, looked up by part number from the catalogue dimension.
    # The dimension's own labels were corrected on 2026-09-21 (key 873-042 said
    # "Urea (AdBlue) filter" for a cabin blower filter key). On top of that, a row
    # whose OWN figure key is a curated taxonomy key may never wear another key's
    # label — see modules_figkey_labels.py for why this override stays narrow.
    from modules_figkey_labels import label_for_own_fig_key  # noqa: E402

    fig_label = pd.Series([""] * len(master), dtype=object)
    cat = DER / "parts_catalog_dimension.csv"
    if cat.exists():
        c = pd.read_csv(cat, usecols=["part_number", "fig_key_label"], dtype=str, low_memory=False)
        c["pn"] = pn_key(c["part_number"])
        c = c.drop_duplicates("pn", keep="first")
        dim_label = clean(pn.map(c.set_index("pn")["fig_key_label"]))
        fig_label = label_for_own_fig_key(clean(master["part_number"]), fig_key, dim_label)

    out_df = pd.DataFrame(
        {
            "part_number": clean(master["part_number"]),
            "description": description,
            "description_source": desc_source,
            "aim_level_1": aim_l1,
            "aim_level_2": aim_l2,
            "aim_level_3": aim_l3,
            "figure_key": fig_key,
            "figure_no": clean(master["fig_no"]),
            "key_no": clean(master["key_no"]),
            "figure_key_label": fig_label,
            "line_kind": line_kind,
            "aim_source": aim_source,
            "l12m_billed_eur": l12m,
        }
    )[COLS]

    out_df["_has_desc"] = (out_df["description"] != "").astype(int)
    out_df = out_df.sort_values(
        ["_has_desc", "l12m_billed_eur"], ascending=[False, False]
    ).drop(columns=["_has_desc"])

    # CSV first — this is what Power BI should load.
    out_df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        out_df.to_excel(writer, sheet_name="AIM_PN", index=False)
        ws = writer.sheets["AIM_PN"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        n = len(out_df)
        n_desc = int((out_df["description"] != "").sum())
        n_fig = int((out_df["figure_key"] != "").sum())
        n_aim = int((out_df["aim_level_1"] != "").sum())
        cov = pd.DataFrame(
            {
                "metric": [
                    "as_of",
                    "part_numbers",
                    "with_description",
                    "without_description",
                    "with_figure_key",
                    "with_aim_level_1",
                    "power_bi_file",
                    "note",
                ],
                "value": [
                    STAMP,
                    n,
                    n_desc,
                    n - n_desc,
                    n_fig,
                    n_aim,
                    OUT_CSV.name,
                    "Load the CSV into Power BI (Get data > Text/CSV). "
                    "One row = one part number. Filter line_kind = part to drop fees/tools. "
                    "Excel is the same table for browsing only.",
                ],
            }
        )
        cov.to_excel(writer, sheet_name="Coverage", index=False)

        mix = (
            out_df.loc[out_df["description"] != "", "description_source"]
            .value_counts()
            .rename_axis("description_source")
            .reset_index(name="part_numbers")
        )
        mix.to_excel(writer, sheet_name="Description_sources", index=False)

    CMD.write_bytes(
        (
            "@echo off\r\n"
            f'start "" "%~dp0{OUT_XLSX.name}"\r\n'
        ).encode("ascii")
    )
    print(f"rows={n} with_desc={n_desc} with_fig={n_fig} with_aim={n_aim}")
    print(f"csv={OUT_CSV} size_mb={OUT_CSV.stat().st_size / 1e6:.2f}")
    print(f"xlsx={OUT_XLSX} size_mb={OUT_XLSX.stat().st_size / 1e6:.2f}")


if __name__ == "__main__":
    main()
