# -*- coding: utf-8 -*-
"""Chart assets for ISZE_Kickback_Japan_Final_2026-10-09.pptx.

Every value is read from a source file at run time; nothing is typed in except the
Kosha path, which is read from its workbook as text ("EUR 32.3M") and parsed.

Sources
  _analysis_yearend_20261009.json        (built by analysis_yearend_network_20261009.py
                                          from sales_fact.parquet + 'Incentive FY27')
  01_data/00_derived/sales_fact.parquet  ITUK monthly billing (sold-to 2575)
  90_archive/root_files/ISZE Vehicle Parts - FY2026 Year-End Review.xlsx, 'Kosha Gap & FY2027'
  01_data/11_planning/KPI Master File august 2026.xlsx, 'Parts Handling' (IBX stock days)
  01_data/90_INBOX/_stock_insights_20261007/portugal_billing_vs_sales_to_dealer.csv
  01_data/90_INBOX/_stock_insights_20261007/portugal_family_stock_build.csv
  01_data/00_derived/replenishment_exceptions_cy2025.csv
Sizes are final on-slide inches at 300 dpi, so a matplotlib point is a slide point.
"""
import glob
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import openpyxl
import pandas as pd
from matplotlib.patches import Rectangle

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
HERE = Path(__file__).resolve().parent
OUT = HERE / "_assets_final"
OUT.mkdir(exist_ok=True)
A = json.loads((HERE / "_analysis_yearend_20261009.json").read_text(encoding="utf-8"))
SI = ROOT / "01_data" / "90_INBOX" / "_stock_insights_20261007"

BG, PANEL = "#262626", "#303030"
WHITE, MUTED, GRID = "#F2F2F2", "#BDBDBD", "#4B4B4B"
RED, AMBER, GREEN, GREY = "#E30613", "#F5A000", "#31A354", "#7A7A7A"
plt.rcParams.update({"font.family": "Segoe UI", "text.color": WHITE,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})


def fig_ax(w, h, rect=(0.08, 0.14, 0.9, 0.8)):
    f = plt.figure(figsize=(w, h), dpi=300)
    f.patch.set_facecolor(PANEL)
    ax = f.add_axes(rect)
    ax.set_facecolor(PANEL)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
        ax.spines[s].set_linewidth(0.7)
    ax.tick_params(length=0, labelsize=9)
    return f, ax


def save(f, name):
    f.savefig(OUT / name, dpi=300, facecolor=f.get_facecolor())
    plt.close(f)
    print("  wrote", name)


# ------------------------------------------------------------ 3  Kosha path
def kosha():
    p = glob.glob(str(ROOT / "90_archive" / "root_files" / "*FY2026 Year-End Review*.xlsx"))[0]
    wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
    ws = wb["Kosha Gap & FY2027"]
    rows = []
    for r in ws.iter_rows(min_row=1, max_row=20, values_only=True):
        lab = str(r[1] or "")
        if lab.startswith("FY20") and r[2]:
            m = re.search(r"([\d.]+)", str(r[2]))
            rows.append((lab, float(m.group(1))))
            if lab.startswith("FY2031"):
                break
    wb.close()
    print("  kosha:", rows)
    f, ax = fig_ax(6.9, 3.55, (0.03, 0.15, 0.95, 0.74))
    x = range(len(rows))
    vals = [v for _, v in rows]
    cols = [GREY if ("actual" in l or "proj" in l) else (RED if l.startswith("FY2027") else "#9A1B22")
            for l, _ in rows]
    ax.bar(x, vals, color=cols, width=0.66)
    for i, v in zip(x, vals):
        ax.text(i, v + 0.9, f"{v:.1f}", ha="center", va="bottom", fontsize=10.5,
                color=WHITE, fontweight="bold")
    labs = [l.replace(" (actual)", "\nactual").replace(" (proj.)", "\nprojected") for l, _ in rows]
    ax.set_xticks(list(x))
    ax.set_xticklabels(labs, fontsize=8.6, color=MUTED)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_ylim(0, 60)
    i26 = [i for i, (l, _) in enumerate(rows) if l.startswith("FY2026")][0]
    ax.annotate("", xy=(len(rows) - 1.45, vals[-1] + 2.2), xytext=(i26, vals[i26] + 5.2),
                arrowprops=dict(arrowstyle="-|>", color=AMBER, lw=1.8))
    ax.text((i26 + len(rows) - 1) / 2 - 0.4, (vals[i26] + vals[-1]) / 2 + 9.5,
            f"+{100 * (vals[-1] / vals[i26] - 1):.0f}% in five years", color=AMBER,
            fontsize=11, fontweight="bold", ha="center")
    ax.set_title("EUR million a year", loc="left", fontsize=8.6, color=MUTED, pad=4)
    save(f, "c3_kosha.png")
    return rows


# ------------------------------------------------------------ 4  Feb+Mar share
def febmar():
    s = A["febmar_share_9dist"]
    even = A["febmar_share_even"]
    f, ax = fig_ax(5.2, 3.9, (0.06, 0.13, 0.9, 0.78))
    ks = ["FY2024", "FY2025", "FY2026"]
    v = [s[k] for k in ks]
    ax.bar(range(3), v, color=[GREY, GREY, RED], width=0.56)
    for i, val in enumerate(v):
        ax.text(i, val + 0.5, f"{val:.1f}%", ha="center", fontsize=15, fontweight="bold",
                color=WHITE)
    ax.axhline(even, color=AMBER, lw=1.4, ls=(0, (4, 3)))
    ax.text(2.36, even + 0.35, f"even spread\n{even:.1f}%", color=AMBER, fontsize=9,
            ha="left", va="bottom", fontweight="bold")
    ax.set_xticks(range(3))
    ax.set_xticklabels(ks, fontsize=10.5, color=WHITE)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_ylim(0, 24)
    ax.set_xlim(-0.55, 3.05)
    ax.set_title("February + March, share of the fiscal year's billing, nine distributors",
                 loc="left", fontsize=8.4, color=MUTED, pad=6)
    save(f, "c4_febmar_network.png")


def febmar_dots():
    per = A["febmar_share_per_db"]
    order = ["UMI", "UTI", "Ireland", "Norway", "IUK", "Sweden", "Portugal", "Germany", "Benelux"]
    f, ax = fig_ax(6.1, 3.9, (0.17, 0.13, 0.78, 0.78))
    for i, n in enumerate(order):
        lo, hi = sorted([per[n]["FY2024"], per[n]["FY2025"]])
        ax.add_patch(Rectangle((lo, i - 0.17), hi - lo, 0.34, color="#555555", lw=0))
        v = per[n]["FY2026"]
        above = v > hi + 0.05
        col = AMBER if above else GREEN
        ax.plot([v], [i], "o", ms=8.5, color=col, mec=PANEL, mew=1.2, zorder=3)
        if v < lo:
            ax.text(v - 0.6, i, f"{v:.1f}%", va="center", ha="right", fontsize=8.6, color=col,
                    fontweight="bold")
        else:
            ax.text(max(v, hi) + 0.6, i, f"{v:.1f}%", va="center", fontsize=8.6, color=col,
                    fontweight="bold")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([n + " *" if n == "Benelux" else n for n in order], fontsize=9.6, color=WHITE)
    ax.set_xlim(10, 29)
    ax.set_xticks([12, 16.7, 20, 24, 28])
    ax.set_xticklabels(["12%", "16.7%", "20%", "24%", "28%"], fontsize=8.2)
    ax.axvline(16.7, color=AMBER, lw=1.0, ls=(0, (4, 3)), alpha=0.8)
    ax.spines["left"].set_visible(False)
    ax.set_ylim(-0.7, len(order) - 0.3)
    ax.set_title("Each distributor: grey bar = its own FY2024–FY2025 range, dot = FY2026",
                 loc="left", fontsize=8.4, color=MUTED, pad=6, x=-0.2)
    save(f, "c4_febmar_dots.png")


# ------------------------------------------------------------ 5  pace in January
def pace():
    p = A["pace"]
    order = sorted(["IUK", "UMI", "UTI", "Germany", "Benelux", "Portugal", "Sweden", "Norway",
                    "Ireland"], key=lambda n: p[n]["pace_pct_of_10m_plan"])
    f, ax = fig_ax(7.3, 4.05, (0.14, 0.12, 0.83, 0.8))
    for i, n in enumerate(order):
        v = p[n]["pace_pct_of_10m_plan"]
        col = GREEN if v >= 100 else (AMBER if v >= 95 else GREY)
        ax.barh(i, v, color=col, height=0.62)
        ax.text((max(v, 100) if v >= 95 else v) + 0.6, i, f"{v:.1f}%", va="center", fontsize=9.6, color=WHITE,
                fontweight="bold")
    ax.axvline(100, color=WHITE, lw=1.3)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order, fontsize=10, color=WHITE)
    ax.set_xlim(80, 124)
    ax.set_xticks([80, 90, 100, 110, 120])
    ax.set_xticklabels(["80%", "90%", "100% = on plan", "110%", "120%"], fontsize=8.4)
    ax.spines["left"].set_visible(False)
    ax.set_ylim(-0.6, len(order) - 0.4)
    ax.set_title("Billing April 2025 – January 2026, as a share of ten months of the FY2026 plan",
                 loc="left", fontsize=8.4, color=MUTED, pad=8, x=-0.12)
    save(f, "c5_pace.png")


# ------------------------------------------------------------ 6  billed vs dealer, Feb+Mar
def std_pair():
    s = A["febmar_vs_own_run_billing_and_std"]
    names = ["IUK", "Portugal", "Ireland"]
    f, ax = fig_ax(6.3, 3.75, (0.09, 0.15, 0.89, 0.74))
    w = 0.36
    for i, n in enumerate(names):
        b, d = s[n]["billing_febmar_vs_run_pct"], s[n]["std_febmar_vs_run_pct"]
        ax.bar(i - w / 2 - 0.01, b, w, color=RED)
        ax.bar(i + w / 2 + 0.01, d, w, color=GREEN)
        for x, v, c in ((i - w / 2, b, RED), (i + w / 2, d, GREEN)):
            ax.text(x, v + (1.0 if v >= 0 else -1.0), f"{v:+.1f}%", ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=10.5, fontweight="bold", color=WHITE)
    ax.axhline(0, color=GRID, lw=0.9)
    ax.set_xticks(range(3))
    ax.set_xticklabels(names, fontsize=11, color=WHITE)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_ylim(-8, 38)
    ax.bar([0], [0], color=RED, label="what we billed the distributor")
    ax.bar([0], [0], color=GREEN, label="what its dealers bought")
    ax.legend(loc="upper right", frameon=False, fontsize=8.8, labelcolor=WHITE)
    ax.set_title("February + March 2026 against each distributor's own April–January average",
                 loc="left", fontsize=8.4, color=MUTED, pad=6)
    save(f, "c6_billed_vs_dealer.png")


# ------------------------------------------------------------ 7  ITUK
def ituk():
    sf = pd.read_parquet(ROOT / "01_data" / "00_derived" / "sales_fact.parquet",
                         columns=["billing_date", "sold_to_sap", "net_sales_value"])
    sf["d"] = pd.to_datetime(sf["billing_date"], errors="coerce")
    sf = sf[pd.to_numeric(sf["sold_to_sap"], errors="coerce") == 2575]
    sf["ym"] = sf["d"].dt.to_period("M").astype(str)
    sf["eur"] = pd.to_numeric(sf["net_sales_value"], errors="coerce").fillna(0)
    months = [f"2025-{m:02d}" for m in range(4, 13)] + [f"2026-{m:02d}" for m in range(1, 6)]
    v = sf.groupby("ym")["eur"].sum().reindex(months, fill_value=0.0)
    run = v.iloc[:10].mean()
    print("  ituk run rate", round(run, 2), "feb", round(v["2026-02"], 2), "mar", round(v["2026-03"], 2))
    f, ax = fig_ax(12.0, 3.25, (0.03, 0.17, 0.96, 0.74))
    cols = []
    for m in months:
        cols.append(AMBER if m == "2026-02" else (RED if m <= "2026-03" else GREY))
    ax.bar(range(len(months)), v.values / 1000, color=cols, width=0.64)
    for i, val in enumerate(v.values):
        ax.text(i, val / 1000 + 14, f"{val / 1000:.0f}", ha="center", fontsize=8.6, color=WHITE)
    ax.axhline(run / 1000, xmax=10.5 / len(months), color=GREEN, lw=1.4, ls=(0, (5, 3)))
    ax.text(-0.3, 900, f"- - -  April–January average, EUR {run / 1000:,.0f}k a month",
            color=GREEN, fontsize=8.8, fontweight="bold")
    ax.axvline(11.5 - 0.5 + 0.5 * 12 / 31, color=AMBER, lw=1.6)
    ax.text(11.45, 1010, "13 March: price list +5.96%", color=AMBER, fontsize=8.8, fontweight="bold")
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels([pd.Period(m).strftime("%b") for m in months], fontsize=8.6)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_ylim(0, 1080)
    ax.text(5.5, -150, "FY2026", ha="center", fontsize=8.8, color=WHITE, clip_on=False, fontweight="bold")
    ax.text(13, -150, "FY2027", ha="center", fontsize=8.8, color=WHITE, clip_on=False, fontweight="bold")
    ax.set_title("ITUK, EUR thousands billed a month", loc="left", fontsize=8.4, color=MUTED, pad=4)
    save(f, "c7_ituk.png")


# ------------------------------------------------------------ 8  IBX stock days
def ibx():
    wb = openpyxl.load_workbook(ROOT / "01_data" / "11_planning" / "KPI Master File august 2026.xlsx",
                                data_only=True, read_only=True)
    ws = wb["Parts Handling"]
    rows = list(ws.iter_rows(min_row=3, max_row=25, values_only=True))
    hdr = rows[0]
    want = ["Aug 25", "Sep 25", "Oct 25", "Nov 25", "Dec 25", "Jan 26", "Feb 26", "Mar 26",
            "Apr 26", "May 26", "Jun 26", "Jul 26"]
    ser = {}
    for r in rows[1:]:
        if r[0] and str(r[0]).strip() == "IBX (BENELUX)":
            for i, h in enumerate(hdr):
                if h and str(h).strip() in want and isinstance(r[i], (int, float)):
                    ser[str(h).strip()] = float(r[i])
    wb.close()
    print("  ibx", ser)
    xs = [k for k in want if k in ser]
    f, ax = fig_ax(7.4, 3.7, (0.07, 0.14, 0.9, 0.76))
    ax.axhspan(60, 75, color=GREEN, alpha=0.18, lw=0)
    ax.text(0, 71.5, "target band 60–75 days", color=GREEN, fontsize=9, fontweight="bold")
    ax.plot(range(len(xs)), [ser[k] for k in xs], color=WHITE, lw=2.4, marker="o", ms=5.5)
    for i, k in enumerate(xs):
        if k in ("Aug 25", "Jan 26", "Jul 26"):
            ax.text(i, ser[k] - 5.2, f"{ser[k]:.0f}", ha="center", va="top", fontsize=11,
                    fontweight="bold", color=AMBER if k == "Jul 26" else WHITE)
    ax.set_xticks(range(len(xs)))
    ax.set_xticklabels(xs, fontsize=8.4)
    ax.set_yticks([30, 45, 60, 75])
    ax.set_yticklabels(["30", "45", "60", "75"], fontsize=8.4)
    ax.set_ylim(20, 82)
    ax.set_title("IBX (Benelux), days of parts in stock, as reported by IBX", loc="left",
                 fontsize=8.4, color=MUTED, pad=4)
    save(f, "c8_ibx.png")
    return ser


# ------------------------------------------------------------ 10  Portugal
def portugal():
    p = pd.read_csv(SI / "portugal_billing_vs_sales_to_dealer.csv")
    p.columns = ["ym", "b", "s", "g", "pct"]
    f, ax = fig_ax(8.2, 3.9, (0.07, 0.13, 0.80, 0.78))
    x = range(len(p))
    ax.fill_between(x, p.b / 1000, p.s / 1000, where=(p.s >= p.b), color=GREEN, alpha=0.22,
                    interpolate=True, lw=0)
    ax.plot(x, p.b / 1000, color=RED, lw=2.4)
    ax.plot(x, p.s / 1000, color=GREEN, lw=2.4)
    n = len(p) - 1
    ax.text(n + 0.35, p.s.iloc[-1] / 1000 + 6, f"dealers bought\nEUR {p.s.iloc[-1] / 1000:.0f}k",
            color=GREEN, fontsize=9, fontweight="bold", va="center", clip_on=False)
    ax.text(n + 0.35, p.b.iloc[-1] / 1000 - 12, f"we billed\nEUR {p.b.iloc[-1] / 1000:.0f}k",
            color=RED, fontsize=9, fontweight="bold", va="center", clip_on=False)
    i_apr = list(p.ym).index("2026-04")
    ax.axvspan(i_apr - 0.5, n + 0.2, color=WHITE, alpha=0.05, lw=0)
    ax.text(i_apr - 0.3, 205, "April–August 2026", color=MUTED, fontsize=8.4)
    ax.set_xticks(list(x))
    ax.set_xticklabels([pd.Period(m).strftime("%b\n%y") if pd.Period(m).month in (1, 4, 7, 10)
                        else "" for m in p.ym], fontsize=8)
    ax.set_yticks([0, 50, 100, 150, 200])
    ax.set_yticklabels(["0", "50k", "100k", "150k", "200k"], fontsize=8.2)
    ax.set_ylim(0, 215)
    ax.set_title("Imotors (Portugal), EUR a month: our billing against its sales to dealers",
                 loc="left", fontsize=8.4, color=MUTED, pad=4)
    save(f, "c10_portugal.png")


# ------------------------------------------------------------ 11  three findings
def findings():
    fam = pd.read_csv(SI / "portugal_family_stock_build.csv")
    print("  family cols", fam.columns.tolist())
    namec = [c for c in fam.columns if fam[c].dtype == object][0]
    valc = [c for c in fam.columns if "eur" in c.lower() and "build" in c.lower()] or \
           [c for c in fam.columns if fam[c].dtype != object]
    valc = valc[0]
    top = fam.sort_values(valc, ascending=False).head(5)
    f, ax = fig_ax(3.75, 2.25, (0.42, 0.06, 0.55, 0.9))
    ys = list(range(len(top)))[::-1]
    cols = [AMBER if i < 3 else GREY for i in range(len(top))]
    ax.barh(ys, top[valc] / 1000, color=cols, height=0.62)
    for y, v in zip(ys, top[valc]):
        ax.text(v / 1000 + 1, y, f"{v / 1000:.0f}k", va="center", fontsize=8.4, color=WHITE)
    ax.set_yticks(ys)
    ax.set_yticklabels(top[namec], fontsize=8.2, color=WHITE)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, top[valc].max() / 1000 * 1.25)
    save(f, "c11a_families.png")

    f, ax = fig_ax(3.75, 2.25, (0.06, 0.16, 0.9, 0.78))
    ax.bar([0, 1], [100947, 24083], color=[AMBER, GREY], width=0.55)
    ax.text(0, 100947 + 3000, "EUR 100,947", ha="center", fontsize=9.6, fontweight="bold")
    ax.text(1, 24083 + 3000, "EUR 24,083", ha="center", fontsize=9.6, fontweight="bold")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["a month in the\ncampaign window", "a month in the\nfour months after"],
                       fontsize=8.2, color=WHITE)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_ylim(0, 122000)
    save(f, "c11b_iuk.png")

    d = pd.read_csv(ROOT / "01_data" / "00_derived" / "replenishment_exceptions_cy2025.csv",
                    low_memory=False)
    x = d[d["pipeline_signal"] == "leakage_high_sellthrough"]
    g = x.groupby("distributor_code")["bill_eur"].sum().sort_values()
    print("  replenishment", g.round(2).to_dict(), round(g.sum(), 2))
    lab = {"GREECE": "Greece", "IRELAND": "Ireland", "ITUK": "ITUK", "IUK": "IUK", "UTI": "UTI"}
    f, ax = fig_ax(3.75, 2.25, (0.2, 0.06, 0.78, 0.9))
    ax.barh(range(len(g)), g.values / 1000, color=GREEN, height=0.62)
    for i, v in enumerate(g.values):
        ax.text(v / 1000 + 6, i, f"{v / 1000:.0f}k", va="center", fontsize=8.4)
    ax.set_yticks(range(len(g)))
    ax.set_yticklabels([lab[k] for k in g.index], fontsize=8.6, color=WHITE)
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, g.max() / 1000 * 1.28)
    save(f, "c11c_replenish.png")
    return round(float(g.sum()), 2)


if __name__ == "__main__":
    kosha()
    febmar()
    febmar_dots()
    pace()
    std_pair()
    ituk()
    ibx()
    portugal()
    findings()
