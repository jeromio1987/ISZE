"""Build the ITUK leakage + BVP-cliff charts straight from the shipped dashboard payload."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bpr_charts as C  # noqa: E402

PAY = json.loads((HERE / "_leakage_payload.json").read_text(encoding="utf-8"))
ITUK = PAY["ITUK"]


def eur(v):
    if v is None:
        return "—"
    a = abs(v)
    s = "-" if v < 0 else ""
    if a >= 1_000_000:
        return f"{s}EUR {a/1_000_000:,.2f}M"
    if a >= 1_000:
        return f"{s}EUR {a/1_000:,.0f}k"
    return f"{s}EUR {a:,.0f}"


def build_ituk_leakage():
    # 1. demand capture: billed vs not bought, CY vs FY
    cy, fy = ITUK["demand"]["cy"], ITUK["demand"]["fy"]
    C.split_row(
        ["Calendar 2025", "Fiscal 2025/26"],
        {
            "Billed (units)": [cy["cap"], fy["cap"]],
            "Not bought": [cy["nb"], fy["nb"]],
        },
        "_ituk_demand_split.png",
        title="ITUK service demand: how much of the expected service volume was billed",
        subtitle=(
            f"Expected {cy['exp']:,.0f} units on {ITUK['uio']:,.0f} trucks in service. "
            f"Calendar gap {eur(cy['gap'])} · fiscal gap {eur(fy['gap'])}."
        ),
        value_fmt="{:,.1f}%",
    )

    # 2. gap by family, fiscal year (the quotable one)
    fams = [f for f in ITUK["fam"] if f["fy_gap"] and f["fy_gap"] > 0]
    fams.sort(key=lambda f: -f["fy_gap"])
    fams = fams[:9]
    C.ranked_bar(
        [f["label"] for f in fams],
        [f["fy_gap"] / 1000 for f in fams],
        "_ituk_gap_by_family_fy.png",
        title="ITUK: where the unbought service euro sits, fiscal 2025/26",
        subtitle="Uncaptured parts value = expected units minus billed units, at the observed average selling price.",
        value_fmt="{:,.0f}k",
        reference=None,
        hot_below=False,
    )

    # 3. capture rate by family vs 100% expectation
    caps = [f for f in ITUK["fam"] if f["exp_qty"] > 0 and 0 <= f["cap"] <= 200]
    caps.sort(key=lambda f: f["cap"])
    C.deviation(
        [f["label"] for f in caps],
        [f["cap"] - 100 for f in caps],
        "_ituk_capture_vs_full.png",
        title="ITUK: capture against the modelled full-service expectation, by family",
        subtitle="Deviation from 100% of the service parts the model expects. Below the line = under-served; above = over the modelled rate (fleet or interval effect).",
        value_fmt="{:+.1f}%",
        band=None,
    )

    # 4. dealer layer vs ISZE billing layer (only where a sales-to-dealer file exists)
    dl = ITUK.get("dealer", {}).get("cy")
    if dl:
        C.split_row(
            ["ISZE to distributor", "Distributor to dealer"],
            {
                "Billed": [cy["cap"], dl["cap"]],
                "Not bought": [cy["nb"], dl["nb"]],
            },
            "_ituk_two_layers.png",
            title="ITUK: the gap looks different at each layer of the chain",
            subtitle=(
                f"Inner layer (distributor to dealer) carries {eur(dl['eur'])} of billed euro across "
                f"{dl['months']} months of sales-to-dealer file. Outer layer is our billing to ITUK."
            ),
            value_fmt="{:,.1f}%",
        )


def build_bvp_cliff():
    """Germany same-reference BVP cliff, computed from the crossref sales file."""
    import pandas as pd

    p = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\00_derived\sales_with_crossref.parquet")
    swx = pd.read_parquet(
        p,
        columns=["billing_date", "distributor_code", "billed_qty", "crossref_role", "crossref_id", "product_subgroup"],
    )
    swx = swx[swx.crossref_id.notna() & swx.crossref_role.isin(["genuine", "bvp"])]
    swx["bd"] = pd.to_datetime(swx["billing_date"])
    swx["fy"] = swx["bd"].dt.year.where(swx["bd"].dt.month >= 4, swx["bd"].dt.year - 1)

    def share_for(df):
        bq = df.loc[df.crossref_role == "bvp", "billed_qty"].sum()
        gq = df.loc[df.crossref_role == "genuine", "billed_qty"].sum()
        return (bq / (bq + gq) * 100) if (bq + gq) else None

    labels, vals = [], []
    for fy in (2023, 2024, 2025):
        labels.append(f"{fy}/{str(fy+1)[2:]}")
        vals.append(share_for(swx[(swx.fy == fy) & (swx.distributor_code == "GERMANY")]))
    net = [share_for(swx[swx.fy == fy]) for fy in (2023, 2024, 2025)]

    C.line_years(
        labels,
        {"Germany": vals, "Network": net},
        "_de_bvp_cliff.png",
        title="Germany: genuine vs best-value on the same reference part number",
        subtitle="Best-value share of paired units. Fiscal years, April to March.",
        value_fmt="{:,.1f}%",
        annotation=(2, vals[2] + 6, "fuel-filter best-value volume\nstops being billed"),
    )

    # the driver, per family
    de25 = swx[(swx.fy == 2025) & (swx.distributor_code == "GERMANY")]
    de24 = swx[(swx.fy == 2024) & (swx.distributor_code == "GERMANY")]

    def fam_table(df):
        out = {}
        for sg, g in df.groupby("product_subgroup"):
            bq = g.loc[g.crossref_role == "bvp", "billed_qty"].sum()
            gq = g.loc[g.crossref_role == "genuine", "billed_qty"].sum()
            if bq + gq >= 200:
                out[sg] = (bq, gq, bq + gq)
        return out

    t24, t25 = fam_table(de24), fam_table(de25)
    keys = sorted(set(t24) | set(t25), key=lambda k: -((t24.get(k, (0, 0, 0))[2]) + (t25.get(k, (0, 0, 0))[2])))
    keys = keys[:7]
    C.ranked_bar(
        [k.replace("_", " ") for k in keys],
        [-((t25.get(k, (0, 0, 0))[2]) - (t24.get(k, (0, 0, 0))[2])) for k in keys],
        "_de_bvp_driver.png",
        title="Germany: which families the best-value volume came out of",
        subtitle="Change in paired units billed, fiscal 2024/25 to 2025/26. Bars to the right = volume lost.",
        value_fmt="{:,.0f}",
        hot_below=False,
    )
    return {"fy_labels": labels, "de": vals, "net": net}


if __name__ == "__main__":
    build_ituk_leakage()
    info = build_bvp_cliff()
    print("ITUK + DE charts written")
    print(json.dumps(info, indent=1))
