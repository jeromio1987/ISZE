"""Export AIM master Excel with descriptions filled from best available sources.

Jerome rejected the first cut: Description column was mostly empty because
aim_master_v2.description is blank for ~84% of catalogue PNs. This rebuild
coalesces description from billing, APL, price compare, EQ overnight, and EPC.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
SRC = DER / "aim_master_v2.csv"
OUT = DER / "AIM_Master_PN_Categories_Figkey_20260920.xlsx"
CMD = DER / "OPEN_AIM_Master_PN_Categories_Figkey_20260920.cmd"


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
    # prefer EQ part name, else description from queue if present
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
    df = pd.read_csv(SRC, low_memory=False, dtype=str)
    pn = pn_key(df["part_number"])

    maps = [
        ("sales_fact_euro_top", load_sales_desc()),
        ("apl", load_apl_desc()),
        ("price_revision_billed", load_price_desc()),
        ("eq_session_20260919", load_eq_desc()),
        ("epc_heavy", load_epc_heavy_desc()),
    ]
    for label, m in maps:
        print(f"source {label}: {len(m)} PNs")

    description, desc_source = coalesce_desc(df["description"], pn, maps)

    # fig key label from catalogue dimension
    fig_label = pd.Series([""] * len(df))
    cat = DER / "parts_catalog_dimension.csv"
    if cat.exists():
        c = pd.read_csv(cat, usecols=["part_number", "fig_key_label"], dtype=str, low_memory=False)
        c["pn"] = pn_key(c["part_number"])
        c = c.drop_duplicates("pn", keep="first")
        fig_label = clean(pn.map(c.set_index("pn")["fig_key_label"]))

    out_df = pd.DataFrame(
        {
            "Part number": clean(df["part_number"]),
            "Description": description,
            "Description source": desc_source,
            "AIM level 1": prefer(df["aim_l1_fixed"], df["aim_l1"]),
            "AIM level 2": prefer(df["aim_l2_fixed"], df["aim_l2"]),
            "AIM level 3": clean(df["aim_l3"]),
            "Figure key": clean(df["fig_key"]),
            "Figure no": clean(df["fig_no"]),
            "Key no": clean(df["key_no"]),
            "Figure key label": fig_label,
            "L12M billed EUR": pd.to_numeric(df.get("l12m_billed_eur"), errors="coerce"),
        }
    )

    # Sort: described + euro first so the file is usable top-down
    out_df["_has_desc"] = (out_df["Description"] != "").astype(int)
    out_df = out_df.sort_values(
        ["_has_desc", "L12M billed EUR"], ascending=[False, False]
    ).drop(columns=["_has_desc"])

    with pd.ExcelWriter(OUT, engine="openpyxl") as writer:
        out_df.to_excel(writer, sheet_name="AIM PN", index=False)
        ws = writer.sheets["AIM PN"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

        # Coverage sheet so blank catalogue PNs are explained, not hidden
        n = len(out_df)
        n_desc = int((out_df["Description"] != "").sum())
        cov = pd.DataFrame(
            {
                "Metric": [
                    "Part numbers in file",
                    "With description",
                    "Without description",
                    "Share with description %",
                    "Note",
                ],
                "Value": [
                    n,
                    n_desc,
                    n - n_desc,
                    round(100 * n_desc / n, 1),
                    "Descriptions come from billing / APL / price revision / EQ / EPC where we have them. "
                    "Most catalogue-only PNs were never billed and have no English description in the warehouse.",
                ],
            }
        )
        cov.to_excel(writer, sheet_name="Coverage", index=False)

        # Source mix
        mix = (
            out_df.loc[out_df["Description"] != "", "Description source"]
            .value_counts()
            .rename_axis("Description source")
            .reset_index(name="Part numbers")
        )
        mix.to_excel(writer, sheet_name="Description sources", index=False)

    CMD.write_bytes(
        b'@echo off\r\nstart "" "%~dp0AIM_Master_PN_Categories_Figkey_20260920.xlsx"\r\n'
    )
    print(f"rows={n} with_desc={n_desc} blank={n - n_desc}")
    print(f"out={OUT}")
    print(f"size_mb={OUT.stat().st_size / 1e6:.2f}")


if __name__ == "__main__":
    main()
