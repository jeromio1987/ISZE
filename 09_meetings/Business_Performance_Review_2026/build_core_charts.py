"""BPR 2.0 — core charts from the sales / KPI / GPS / PMS backbone."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bpr_charts as C  # noqa: E402

N = json.loads((HERE / "_bpr_numbers.json").read_text(encoding="utf-8"))
K = json.loads((HERE / "_kpi_numbers.json").read_text(encoding="utf-8"))

MONTHLY = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\ISZE_MONTHLY_SALES_REPORT_09.2026.xlsx")


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


# ------------------------------------------------------------------ 1 sales
def chart_sales():
    monthly = pd.read_excel(MONTHLY, sheet_name="14.09.26", header=None)
    rows = monthly.iloc[4:15]
    labels, bill, bp, ly = [], [], [], []
    for _, r in rows.iterrows():
        db = str(r[1]).strip() if not pd.isna(r[1]) else ""
        if not db:
            continue
        labels.append(db.replace("ISZ ", ""))
        bill.append(float(r[5]) if not pd.isna(r[5]) else 0.0)
        bp.append(float(r[6]) if not pd.isna(r[6]) else 0.0)
        ly.append(float(r[8]) if not pd.isna(r[8]) else 0.0)
    C.change_bars(
        labels,
        {"This September to date": bill, "Last September (same point)": ly},
        "_sales_sept_mtd.png",
        title="September to date: who is ahead of the same point last year?",
        subtitle=(
            "Parts billing month to date, EUR. Taken from the 14 Sept 2026 daily sales report. "
            "The month is not closed."
        ),
        value_fmt="{:,.0f}",
        figsize=(9.8, 6.2),
    )
    C.ranked_bar(
        labels,
        bill,
        "_sales_sept_rank.png",
        title="September to date: parts billing by distributor (EUR)",
        subtitle="Month to date at 14 September 2026. Network month-to-date 1.46M of a 3.18M month plan (46%).",
        value_fmt="{:,.0f}",
        hot_below=False,
        figsize=(9.6, 5.6),
    )
    return labels, bill, bp, ly


def chart_fy26_close():
    by = N["fy2026"]["by_db"]
    items = sorted(by.items(), key=lambda kv: -kv[1])[:11]
    C.ranked_bar(
        [k for k, _ in items],
        [v / 1000 for _, v in items],
        "_fy26_close_by_db.png",
        title="Fiscal 2026 close: parts billed by distributor (EUR k)",
        subtitle=(
            f"Distributor billing across the {len(by)} attributed distributors in the billing file. "
            f"Billing file runs to {N['sf_max_date']}, so this is the full fiscal year."
        ),
        value_fmt="{:,.0f}k",
        hot_below=False,
        figsize=(9.6, 5.4),
    )
    other = sum(v for _, v in sorted(by.items(), key=lambda kv: -kv[1])[11:])
    return items, other


# --------------------------------------------------------------- 2 fill rate
def chart_fill():
    ff = K["first_fill_rate"]["by_db"]
    rows = []
    for db, r in ff.items():
        if r.get("latest") is None:
            continue
        v = r["latest"] * 100 if r["latest"] < 1.5 else r["latest"]
        rows.append((db, v, r.get("month_label")))
    rows.sort(key=lambda t: -t[1])
    C.ranked_bar(
        [f"{db}" for db, _, _ in rows],
        [v for _, v, _ in rows],
        "_fill_rate_latest.png",
        title="Parts order fill rate: who is below the 95% standard?",
        subtitle=(
            "Latest reported month per distributor from the KPI return. Standard 95%, floor 92%. "
            "Reported figures only — a market that does not return the file shows nothing, not zero."
        ),
        value_fmt="{:,.1f}%",
        reference=95,
        reference_label="95% standard",
        figsize=(9.6, 5.2),
    )
    C.ranked_bar(
        [f"{db}" for db, _, _ in rows],
        [v for _, v, _ in rows],
        "_fill_rate_vs_standard.png",
        title="Parts fill rate measured against the 95% standard (percentage points)",
        subtitle="Deviation from the reporting standard. Bars to the left are below standard.",
        value_fmt="{:+.1f}",
        hot_below=False,
        figsize=(9.6, 5.2),
    ) if False else None
    vals = [v for _, v, _ in rows]
    dev = [v - 95 for v in vals]
    C.deviation(
        [db for db, _, _ in rows],
        dev,
        "_fill_rate_deviation.png",
        title="Who is short of the 95% parts fill standard, and by how much",
        subtitle="Percentage points against the 95% standard. Left = short of standard.",
        value_fmt="{:+.1f}",
        band=(-3, 3),
        figsize=(9.6, 5.2),
    )
    return rows


def chart_stock():
    st = K["days_of_parts_in_stock"]["by_db"]
    rows = []
    for db, r in st.items():
        if r.get("latest") is None:
            continue
        rows.append((db, r["latest"], r.get("month_label")))
    rows.sort(key=lambda t: -t[1])
    C.ranked_bar(
        [db for db, _, _ in rows],
        [v for _, v, _ in rows],
        "_days_of_stock.png",
        title="Days of parts in stock per distributor, latest reported month",
        subtitle=(
            "Reported inventory cover. Class A road parts band 60–75 days, Class B 75–90, "
            "Class C sea freight 90–120. Above band is working capital; below band is fill risk."
        ),
        value_fmt="{:,.0f}",
        reference=90,
        reference_label="upper road band ~90 days",
        figsize=(9.6, 5.2),
    )
    return rows


# ------------------------------------------------------------------- 3 GPS
def chart_gps():
    g = N["gps_cy2025"]
    items = sorted(g["by_db"].items(), key=lambda kv: -kv[1]["spend_per_unit"])
    C.ranked_bar(
        [k for k, _ in items],
        [v["spend_per_unit"] for _, v in items],
        "_gps_spend_per_truck.png",
        title="Which markets spend most per truck per year?",
        subtitle=(
            f"Parts billed per truck in service, calendar 2025. Network {g['network_spend_per_unit']:,.0f} EUR, "
            f"median {g['network_median_spend_per_unit']:,.0f} EUR on {g['network_uio']:,.0f} trucks."
        ),
        value_fmt="{:,.0f}",
        reference=g["network_median_spend_per_unit"],
        reference_label="network median",
        figsize=(9.6, 5.6),
    )
    c = N["ceiling_cy2025"]
    C.kpi_strip(
        [
            ("Target spend ceiling", eur(c["theoretical_eur"]), "modelled, calendar 2025"),
            ("Parts billed", eur(c["captured_total_eur"]), "what we billed"),
            ("Not captured", eur(c["uncaptured_eur"]), f"of which addressable {eur(c['addressable_uncaptured_eur'])}"),
            ("Coverage", f"{c['capture_pct']:.1f}%", "billed against the ceiling"),
        ],
        "_ceiling_strip.png",
        title="The parts opportunity in one row",
    )
    return items, c


# ------------------------------------------------------------------- 4 PMS
def chart_pms():
    p = N["pms_cy2025"]
    cats = sorted(p["by_category"].items(), key=lambda kv: -kv[1]["gap_eur"])[:10]
    C.ranked_bar(
        [k for k, _ in cats],
        [v["gap_eur"] / 1000 for _, v in cats],
        "_pms_gap_categories.png",
        title="Where the unbought service euro sits, by parts family",
        subtitle=(
            f"Calendar 2025. Network service capture {p['network_capture_pct']:.1f}% of expected units, "
            f"leaving {eur(p['network_gap_eur'])} unbought at the observed selling price."
        ),
        value_fmt="{:,.0f}k",
        hot_below=False,
        figsize=(9.6, 5.4),
    )
    C.kpi_strip(
        [
            ("Service capture", f"{p['network_capture_pct']:.1f}%", "of expected service units billed"),
            ("Unbought value", eur(p["network_gap_eur"]), "calendar 2025, observed prices"),
            ("Families scored", str(len(p["by_category"])), "PMS categories"),
            ("Biggest family gap", cats[0][0] if cats else "—", eur(cats[0][1]["gap_eur"]) if cats else "—"),
        ],
        "_pms_strip.png",
        title="Service parts: the capture picture",
    )
    return cats


# ------------------------------------------------------------- 5 warranty
def chart_warranty():
    w = N["warranty_cy2025"]
    items = sorted(w["by_db"].items(), key=lambda kv: -kv[1])[:10]
    C.ranked_bar(
        [k for k, _ in items],
        [v / 1000 for _, v in items],
        "_warranty_by_db.png",
        title="Warranty parts billed by distributor (EUR k)",
        subtitle=(
            f"Calendar 2025. Network {eur(w['network_eur'])} — "
            f"{w['network_pct_of_billed']:.1f}% of everything we billed."
        ),
        value_fmt="{:,.0f}k",
        hot_below=False,
        figsize=(9.6, 5.0),
    )
    return items, w


# -------------------------------------------------------------- 6 urgency
def chart_urgency():
    u = N.get("urgency_fy2026")
    if not u:
        return None
    C.split_row(
        ["Fiscal 2026"],
        {"Stock orders": [u["stock_pct"]], "Urgent (VOR/RUSH)": [u["urgent_pct"]]},
        "_urgency_fy26.png",
        title="How much of the network runs on stock orders versus urgent requests",
        subtitle=(
            f"Share of matched billing value by order class, fiscal 2026. "
            f"{u['matched_pct_of_all']:.1f}% of billed value carries a usable order code."
        ),
        value_fmt="{:,.1f}%",
    )
    by = N.get("urgency_by_db_fy2026") or {}
    rows = [(k, v["urgent_pct"], v.get("matched_pct_of_all")) for k, v in by.items()
            if v and v.get("urgent_pct") is not None]
    rows.sort(key=lambda t: -t[1])
    if rows:
        C.ranked_bar(
            [r[0] for r in rows],
            [r[1] for r in rows],
            "_urgency_by_db.png",
            title="Which distributors run most on urgent orders?",
            subtitle=(
                "Urgent share of matched billing value, fiscal 2026. A market that looks healthy on "
                "spend per truck can still be running on emergency orders."
            ),
            value_fmt="{:,.1f}%",
            hot_below=False,
            figsize=(9.6, 5.6),
        )
    return u


if __name__ == "__main__":
    labels, bill, bp, ly = chart_sales()
    print("sept MTD network", eur(sum(bill)), "vs last year same point", eur(sum(ly)))
    items, other = chart_fy26_close()
    print("FY2026 total", eur(N["fy2026"]["total_eur"]), "| top", items[0][0], eur(items[0][1]))
    fill = chart_fill()
    print("fill rows", len(fill), "below 95:", [f[0] for f in fill if f[1] < 95])
    stock = chart_stock()
    gps_items, ceiling = chart_gps()
    print("GPS top", gps_items[0][0], round(gps_items[0][1]["spend_per_unit"]))
    cats = chart_pms()
    warranty_items, w = chart_warranty()
    u = chart_urgency()
    print("core charts written")
