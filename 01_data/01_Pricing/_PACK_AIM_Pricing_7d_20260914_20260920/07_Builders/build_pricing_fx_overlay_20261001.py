# -*- coding: utf-8 -*-
"""
Price revision + FOB exchange-rate overlay (Suzuki 01/10/2026).

Keeps the AIM L3→PN revision pack frozen. This file adds the purchase-side
effect: Japan-sourced spare parts rebased from 172.6 to 178.5 JPY/EUR.

FOB EUR = base price JPY / FX × source discount
  Japan 0.62 · Thailand 0.611 (unchanged — Suzuki rate is Japan-sourced only)

Run:
  python 02_dashboards/pricing/_build/build_pricing_fx_overlay_20261001.py
"""
from __future__ import annotations

import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ISZE = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DERIVED = ISZE / "01_data" / "00_derived"
OUT_DIR = ISZE / "02_dashboards" / "pricing"
XLSX_DIR = ISZE / "01_data" / "01_Pricing"
CHART = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"

HTML_OUT = OUT_DIR / "ISZE_Pricing_Revision_AIM_FX_20261001.html"
XLSX_OUT = XLSX_DIR / "Pricing_Revision_AIM_FX_20261001.xlsx"
META_OUT = OUT_DIR / "_build" / "_fx_overlay_20261001_meta.json"
OPEN_HTML = OUT_DIR / "OPEN_Pricing_Revision_AIM_FX_20261001.cmd"
OPEN_XLSX = XLSX_DIR / "OPEN_Pricing_Revision_AIM_FX_20261001.cmd"

FX_OLD = 172.6  # the previous rate vintage, used for the purchase-side overlay only. It is NOT the
# price list's own base: the list's base is 163.7, and the settled published move is a ratio of two
# prices read from the list, never a historical rate. See the supersession note on the page.
FX_NEW = 178.5  # Suzuki san, Japan-sourced spare parts, 01/10/2026–31/03/2027
DISC_JP = 0.62
DISC_TH = 0.611
SUZUKI_NOTE = (
    "Official exchange rate for Japan-sourced spare parts from Isuzu Motors Limited: "
    "178.5 JPY per EUR, effective 1 October 2026 to 31 March 2027 "
    "(Suzuki san mail, September 2026)."
)


def say(msg: str) -> None:
    print(msg)
    sys.stdout.flush()


def money(x: float) -> str:
    ax = abs(x)
    if ax >= 1_000_000:
        return f"€{x/1_000_000:,.2f}M"
    if ax >= 1_000:
        return f"€{x/1_000:,.0f}k"
    return f"€{x:,.0f}"


def pct(x: float) -> str:
    return f"{100 * x:,.2f}%"


def load_priced() -> pd.DataFrame:
    lines = pd.read_parquet(DERIVED / "pricing_aim_source_lines.parquet")
    pr = lines[lines["priced_both"] == True].copy()  # noqa: E712
    pr["source"] = pr["source"].astype(str)
    pr["qty"] = pd.to_numeric(pr["qty"], errors="coerce").fillna(0.0)
    for c in ("prior_base_jpy", "new_base_jpy", "billed_eur", "step_eur",
              "prior_eur", "new_eur"):
        pr[c] = pd.to_numeric(pr[c], errors="coerce")
    return pr


def attach_fob(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    disc = out["source"].map({
        "JP - Japan": DISC_JP,
        "TH - Thailand": DISC_TH,
    })
    # Baseline model FX for every sourced line
    out["fob_prior_old"] = out["prior_base_jpy"] / FX_OLD * disc
    out["fob_newbp_old"] = out["new_base_jpy"] / FX_OLD * disc
    # Suzuki rate applies to Japan only; TH / Not held keep old FX
    fx_line = out["source"].map({
        "JP - Japan": FX_NEW,
        "TH - Thailand": FX_OLD,
    }).fillna(FX_OLD)
    out["fob_prior_new"] = out["prior_base_jpy"] / fx_line * disc
    out["fob_newbp_new"] = out["new_base_jpy"] / fx_line * disc
    out["fx_save_prior"] = (out["fob_prior_old"] - out["fob_prior_new"]) * out["qty"]
    out["fx_save_newbp"] = (out["fob_newbp_old"] - out["fob_newbp_new"]) * out["qty"]
    out["fob_prior_old_eur"] = out["fob_prior_old"] * out["qty"]
    out["fob_prior_new_eur"] = out["fob_prior_new"] * out["qty"]
    out["fob_newbp_old_eur"] = out["fob_newbp_old"] * out["qty"]
    out["fob_newbp_new_eur"] = out["fob_newbp_new"] * out["qty"]
    out["japan_fx"] = out["source"].eq("JP - Japan")
    return out


def roll(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    g = (df.groupby(keys, dropna=False)
           .agg(
               lines=("part_number", "size"),
               qty=("qty", "sum"),
               billed_eur=("billed_eur", "sum"),
               step_eur=("step_eur", "sum"),
               fob_prior_old_eur=("fob_prior_old_eur", "sum"),
               fob_prior_new_eur=("fob_prior_new_eur", "sum"),
               fx_save_prior=("fx_save_prior", "sum"),
               fob_newbp_old_eur=("fob_newbp_old_eur", "sum"),
               fob_newbp_new_eur=("fob_newbp_new_eur", "sum"),
               fx_save_newbp=("fx_save_newbp", "sum"),
           )
           .reset_index())
    g["cheaper_pct"] = g.apply(
        lambda r: (1 - r["fob_prior_new_eur"] / r["fob_prior_old_eur"])
        if r["fob_prior_old_eur"] else 0.0, axis=1)
    return g.sort_values("fx_save_prior", ascending=False)


def build_payload(pr: pd.DataFrame) -> dict:
    jp = pr[pr["japan_fx"]].copy()
    th = pr[pr["source"].eq("TH - Thailand")].copy()

    cheaper = 1 - FX_OLD / FX_NEW
    kpis = {
        "fx_old": FX_OLD,
        "fx_new": FX_NEW,
        "cheaper_pct": cheaper,
        "list_step_all_eur": float(pr["step_eur"].sum()),
        "list_step_jp_eur": float(jp["step_eur"].sum()),
        "list_step_th_eur": float(th["step_eur"].sum()),
        "billed_all_eur": float(pr["billed_eur"].sum()),
        "billed_jp_eur": float(jp["billed_eur"].sum()),
        "billed_th_eur": float(th["billed_eur"].sum()),
        "fob_prior_old_jp_eur": float(jp["fob_prior_old_eur"].sum()),
        "fob_prior_new_jp_eur": float(jp["fob_prior_new_eur"].sum()),
        "fx_save_prior_jp_eur": float(jp["fx_save_prior"].sum()),
        "fob_newbp_old_jp_eur": float(jp["fob_newbp_old_eur"].sum()),
        "fob_newbp_new_jp_eur": float(jp["fob_newbp_new_eur"].sum()),
        "fx_save_newbp_jp_eur": float(jp["fx_save_newbp"].sum()),
        "jp_lines": int(len(jp)),
        "th_lines": int(len(th)),
        "priced_lines": int(len(pr)),
        "net_list_vs_fx_prior": float(pr["step_eur"].sum() - jp["fx_save_prior"].sum()),
    }

    by_source = roll(pr, ["source"])
    by_l1_jp = roll(jp, ["aim_l1"]).head(25)
    by_db_jp = roll(jp, ["db"])
    top_pn = (jp.groupby(["part_number", "description", "aim_l1", "price_class"],
                         dropna=False)
                .agg(
                    qty=("qty", "sum"),
                    billed_eur=("billed_eur", "sum"),
                    step_eur=("step_eur", "sum"),
                    fx_save_prior=("fx_save_prior", "sum"),
                    fx_save_newbp=("fx_save_newbp", "sum"),
                    fob_prior_old_eur=("fob_prior_old_eur", "sum"),
                    fob_prior_new_eur=("fob_prior_new_eur", "sum"),
                )
                .reset_index()
                .sort_values("fx_save_prior", ascending=False)
                .head(40))

    def recs(frame: pd.DataFrame) -> list[dict]:
        out = []
        for _, r in frame.iterrows():
            d = {}
            for k, v in r.items():
                if pd.isna(v):
                    d[k] = None
                elif isinstance(v, (int, float)) and not isinstance(v, bool):
                    d[k] = float(v) if not float(v).is_integer() else int(v)
                else:
                    d[k] = v if not hasattr(v, "item") else v.item()
            out.append(d)
        return out

    return {
        "generated": datetime.now(timezone.utc).isoformat(),
        "title": "Price revision + Japan FOB exchange rate (01/10/2026)",
        "suzuki_note": SUZUKI_NOTE,
        "method": (
            "FOB EUR = base price JPY ÷ FX × source discount. "
            f"Japan discount {DISC_JP:.3f}; Thailand {DISC_TH:.3f}. "
            f"Model baseline FX {FX_OLD}; Suzuki Japan rate {FX_NEW} from 1 Oct 2026. "
            "FX relief applies only to Japan-sourced lines. "
            "List step (selling side) is unchanged by FX — it is the JPY base-price move "
            f"converted at the model rate. Purchase-side saving is qty × (FOB@{FX_OLD} − FOB@{FX_NEW})."
        ),
        "frozen_sibling": "ISZE_Pricing_Revision_AIM_Source_L3PN_20260918.html",
        "kpis": kpis,
        "by_source": recs(by_source),
        "by_l1_japan": recs(by_l1_jp),
        "by_db_japan": recs(by_db_jp),
        "top_pn_japan": recs(top_pn),
    }


def write_excel(pr: pd.DataFrame, payload: dict) -> None:
    XLSX_DIR.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    navy = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
    title = Font(name="Calibri", bold=True, size=14, color="15233C")
    dial_fill = PatternFill("solid", fgColor="FFF2CC")
    head_fill = PatternFill("solid", fgColor="15233C")
    thin = Border(
        left=Side(style="thin", color="D9D3C8"),
        right=Side(style="thin", color="D9D3C8"),
        top=Side(style="thin", color="D9D3C8"),
        bottom=Side(style="thin", color="D9D3C8"),
    )

    # --- Legend (same shape as the old simulation dial sheet)
    ws = wb.active
    ws.title = "Legend"
    ws["A1"] = "Legend — FX dials for the FOB overlay"
    ws["A1"].font = title
    ws["A2"] = SUZUKI_NOTE
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws.merge_cells("A2:D2")
    ws.row_dimensions[2].height = 48

    rows = [
        (4, "A. Foreign exchange (JPY per EUR)", None, None, True),
        (5, "Rate used in the AIM revision model (baseline)", FX_OLD, "Every prior FOB column reads this", False),
        (6, "Suzuki rate Japan-sourced spare parts from 01/10/2026", FX_NEW, "Applies to Japan only", True),
        (7, "Cheaper purchase in EUR (1 − baseline ÷ Suzuki)", f"=1-B5/B6", "Japan FOB euro falls by this share", False),
        (9, "B. Source discounts (FOB = BP ÷ FX × discount)", None, None, True),
        (10, "Japan source discount", DISC_JP, "margin 38%", True),
        (11, "Thailand source discount", DISC_TH, "margin 38.9% — FX unchanged", True),
        (13, "C. What moves", None, None, True),
        (14, "List step (selling side, all priced AIM)", payload["kpis"]["list_step_all_eur"], "Unchanged by FX", False),
        (15, "Japan FOB save on prior BP × qty", payload["kpis"]["fx_save_prior_jp_eur"], "Buy cheaper", False),
        (16, "Japan FOB save on new BP × qty", payload["kpis"]["fx_save_newbp_jp_eur"], "After list BP move", False),
    ]
    for rr, lab, val, note, dial in rows:
        ws.cell(rr, 1, lab)
        if val is not None:
            cell = ws.cell(rr, 2, val)
            if dial:
                cell.fill = dial_fill
            if isinstance(val, float) and val > 1:
                cell.number_format = '#,##0.00'
            elif isinstance(val, float):
                cell.number_format = '0.000'
            if isinstance(val, str) and val.startswith("="):
                cell.number_format = '0.00%'
        if note:
            ws.cell(rr, 4, note)
        if val is None and lab.startswith(("A.", "B.", "C.")):
            ws.cell(rr, 1).font = Font(bold=True, color="15233C")

    ws["B7"].number_format = "0.00%"
    for col, w in zip("ABCD", (62, 18, 14, 48)):
        ws.column_dimensions[col].width = w

    def sheet_from_frame(name: str, frame: pd.DataFrame, money_cols: set[str]):
        w = wb.create_sheet(name)
        cols = list(frame.columns)
        for c, h in enumerate(cols, 1):
            cell = w.cell(1, c, h)
            cell.fill = head_fill
            cell.font = navy
        for r_i, row in enumerate(frame.itertuples(index=False), 2):
            for c_i, val in enumerate(row, 1):
                cell = w.cell(r_i, c_i, None if pd.isna(val) else val)
                cell.border = thin
                h = cols[c_i - 1]
                if h in money_cols and isinstance(val, (int, float)):
                    cell.number_format = '#,##0.00'
                elif h.endswith("_pct") or h == "cheaper_pct":
                    if isinstance(val, (int, float)):
                        cell.number_format = "0.00%"
        for c in range(1, len(cols) + 1):
            w.column_dimensions[get_column_letter(c)].width = 16
        w.auto_filter.ref = w.dimensions
        w.freeze_panes = "A2"

    money_cols = {
        "billed_eur", "step_eur", "fob_prior_old_eur", "fob_prior_new_eur",
        "fx_save_prior", "fob_newbp_old_eur", "fob_newbp_new_eur", "fx_save_newbp",
    }
    sheet_from_frame("By source", roll(pr, ["source"]), money_cols)
    sheet_from_frame("Japan by L1", roll(pr[pr["japan_fx"]], ["aim_l1"]), money_cols)
    sheet_from_frame("Japan by distributor", roll(pr[pr["japan_fx"]], ["db"]), money_cols)

    jp = pr[pr["japan_fx"]].copy()
    pn = (jp.groupby(["part_number", "description", "aim_l1", "aim_l2", "aim_l3",
                      "price_class", "db"], dropna=False)
            .agg(
                qty=("qty", "sum"),
                billed_eur=("billed_eur", "sum"),
                step_eur=("step_eur", "sum"),
                prior_base_jpy=("prior_base_jpy", "first"),
                new_base_jpy=("new_base_jpy", "first"),
                fob_prior_old_eur=("fob_prior_old_eur", "sum"),
                fob_prior_new_eur=("fob_prior_new_eur", "sum"),
                fx_save_prior=("fx_save_prior", "sum"),
                fx_save_newbp=("fx_save_newbp", "sum"),
            )
            .reset_index()
            .sort_values("fx_save_prior", ascending=False))
    # Cap PN sheet for Excel usability — full Japan roll still in By L1 / By DB
    sheet_from_frame("Japan PN top 500", pn.head(500), money_cols)

    overview = wb.create_sheet("Overview", 1)
    overview["A1"] = "Overview — list step vs Japan FOB FX relief"
    overview["A1"].font = title
    ov = [
        ("Priced AIM lines", payload["kpis"]["priced_lines"]),
        ("List step (selling, all sources)", payload["kpis"]["list_step_all_eur"]),
        ("of which Japan list step", payload["kpis"]["list_step_jp_eur"]),
        ("of which Thailand list step", payload["kpis"]["list_step_th_eur"]),
        (f"Japan FOB @ {FX_OLD} (prior BP × qty)", payload["kpis"]["fob_prior_old_jp_eur"]),
        (f"Japan FOB @ {FX_NEW} (prior BP × qty)", payload["kpis"]["fob_prior_new_jp_eur"]),
        ("Japan buy-cheaper save (prior BP)", payload["kpis"]["fx_save_prior_jp_eur"]),
        ("Japan buy-cheaper save (new BP)", payload["kpis"]["fx_save_newbp_jp_eur"]),
        ("Cheaper share on Japan FOB", payload["kpis"]["cheaper_pct"]),
        ("List step minus prior-BP FX save", payload["kpis"]["net_list_vs_fx_prior"]),
    ]
    overview["A3"] = "Metric"
    overview["B3"] = "Value"
    overview["A3"].fill = head_fill
    overview["B3"].fill = head_fill
    overview["A3"].font = navy
    overview["B3"].font = navy
    for i, (lab, val) in enumerate(ov, 4):
        overview.cell(i, 1, lab)
        cell = overview.cell(i, 2, val)
        if isinstance(val, float) and val < 1:
            cell.number_format = "0.00%"
        elif isinstance(val, float):
            cell.number_format = '#,##0.00'
    overview.column_dimensions["A"].width = 48
    overview.column_dimensions["B"].width = 18
    overview["A15"] = (
        "Thailand FOB is unchanged by the Suzuki rate. The L3→PN revision HTML stays "
        "as a separate frozen file; this workbook is the FX overlay only."
    )
    overview["A15"].alignment = Alignment(wrap_text=True)
    overview.merge_cells("A15:B16")

    wb.save(XLSX_OUT)
    say(f"Wrote {XLSX_OUT}")


def write_html(payload: dict) -> None:
    chart_js = CHART.read_text(encoding="utf-8") if CHART.exists() else ""
    # strip source map comment if present
    if "//# sourceMappingURL" in chart_js:
        chart_js = chart_js.split("//# sourceMappingURL")[0]
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    k = payload["kpis"]
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Price revision + Japan FOB exchange rate (01/10/2026)</title>
<style>
:root{{
  --navy:#15233c; --navy2:#1d3054; --terra:#c0552d; --paper:#f7f4ee;
  --ink:#22262e; --muted:#6b6459; --line:#d9d3c8; --band:#eef3f9;
  --good:#1e6b4f; --amber:#a8721f;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
  font-size:14px;line-height:1.5}}
h1,h2{{font-family:Georgia,"Times New Roman",serif;color:var(--navy);margin:0}}
h1{{font-size:26px;letter-spacing:-.2px}}
h2{{font-size:18px;margin-bottom:4px}}
.wrap{{max-width:1180px;margin:0 auto;padding:22px 22px 60px}}
header.top{{border-bottom:3px solid var(--navy);padding-bottom:14px;margin-bottom:18px}}
.sub{{color:var(--muted);font-size:13px;margin-top:6px;max-width:920px}}
.badge{{display:inline-block;background:var(--navy);color:var(--paper);
  font-size:11px;letter-spacing:.6px;text-transform:uppercase;
  padding:3px 9px;border-radius:2px;margin-right:8px}}
.badge.g{{background:var(--good)}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
  gap:12px;margin-bottom:20px}}
.kpi{{background:#fff;border:1px solid var(--line);padding:13px 15px;
  border-top:3px solid var(--navy);position:relative}}
.kpi.t{{border-top-color:var(--terra)}}
.kpi.g{{border-top-color:var(--good)}}
.kpi .lab{{font-size:11px;letter-spacing:.6px;text-transform:uppercase;color:var(--muted);
  display:flex;align-items:center;gap:5px}}
.kpi .val{{font-size:24px;font-weight:600;color:var(--navy);margin-top:5px;
  font-variant-numeric:tabular-nums}}
.kpi .note{{font-size:11.5px;color:var(--muted);margin-top:3px}}
.info{{display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;
  border-radius:50%;background:var(--navy);color:#fff;font-size:9.5px;cursor:help;
  position:relative;flex:0 0 auto}}
.info .tip{{display:none;position:absolute;bottom:22px;left:50%;transform:translateX(-50%);
  width:280px;background:var(--navy);color:var(--paper);font-size:12px;line-height:1.45;
  padding:9px 11px;border-radius:3px;z-index:60;text-transform:none;letter-spacing:0;
  font-weight:400;box-shadow:0 4px 14px rgba(0,0,0,.25)}}
.info:hover .tip,.info:focus .tip{{display:block}}
.card{{background:#fff;border:1px solid var(--line);padding:15px 16px 12px;margin-bottom:16px}}
.card .q{{font-size:13px;color:var(--muted);margin:2px 0 12px}}
.grid{{display:grid;gap:16px;margin-bottom:8px}}
.g2{{grid-template-columns:1fr 1fr}}
@media(max-width:900px){{.g2{{grid-template-columns:1fr}}}}
.chartbox{{position:relative;height:320px}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th{{background:var(--navy);color:var(--paper);text-align:left;padding:8px 9px;
  font-weight:600;font-size:11.5px;letter-spacing:.4px;text-transform:uppercase;
  position:sticky;top:0}}
th.n,td.n{{text-align:right;font-variant-numeric:tabular-nums}}
td{{padding:6px 9px;border-bottom:1px solid var(--line)}}
tbody tr:nth-child(even){{background:var(--band)}}
.tblwrap{{max-height:420px;overflow:auto;border:1px solid var(--line)}}
.story{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--good);
  padding:14px 16px;margin-bottom:18px}}
.story p{{margin:0 0 8px}}
.story p:last-child{{margin:0}}
.amber{{background:#fff;border:1px solid var(--line);border-left:4px solid var(--amber);
  padding:12px 14px;margin-bottom:18px;font-size:13px;color:var(--muted)}}
footer{{margin-top:28px;padding-top:12px;border-top:1px solid var(--line);
  font-size:12px;color:var(--muted)}}
</style>
</head>
<body>
<div class="wrap">
<header class="top">
  <div><span class="badge">FX overlay</span>
       <span class="badge g">Japan 178.5 from 01/10/2026</span></div>
  <h1 style="margin-top:10px">Price revision + Japan FOB exchange rate</h1>
  <p class="sub">{payload["suzuki_note"]} The AIM L3→PN revision pack stays as a separate frozen file.
  This page only adds the purchase-side effect: we buy Japan parts cheaper in euro.</p>
</header>

<div class="story">
  <p><b>What changes.</b> The selling-side list step is still {money(k["list_step_all_eur"])}
  ({pct(k["list_step_all_eur"]/k["billed_all_eur"])} on billed). That number does not move with FX —
  it is the JPY base-price revision converted at the model rate.</p>
  <p><b>What the new rate does.</b> Japan FOB in euro falls by {pct(k["cheaper_pct"])}
  ({FX_OLD} → {FX_NEW}). This is a <b>purchase-side</b> figure for Japan-sourced parts only. It is
  not the published list move and must not be read as one: the published move is
  <b>+1.8001%</b> on the whole priced book and <b>+5.7369%</b> on Japan, and it is a ratio of two
  prices read from the price list, so no historical exchange rate is an input to it. On the same
  billed quantities, that is
  {money(k["fx_save_prior_jp_eur"])} less purchase cost at the prior base price, or
  {money(k["fx_save_newbp_jp_eur"])} if you reprice FOB on the new base price.
  Thailand is unchanged — Suzuki’s rate is Japan-sourced only.</p>
</div>

<div class="amber">Thailand FOB stays on {FX_OLD}. Lines with no source label are left on the baseline rate.
Sibling frozen pack: {payload["frozen_sibling"]}.</div>

<div class="kpis">
  <div class="kpi g">
    <div class="lab">Japan buy cheaper (purchase side only)<span class="info">i<span class="tip">1 − {FX_OLD} ÷ {FX_NEW}.
      Japan FOB euro per part falls by this share when the Suzuki rate replaces the previous rate
      vintage. This is what we pay, not what we charge: the published list move is +1.8001% on the
      whole priced book and +5.7369% on Japan. The two are different measures and are never swapped.
      </span></span></div>
    <div class="val">{pct(k["cheaper_pct"])}</div>
    <div class="note">{FX_OLD} → {FX_NEW} JPY/EUR</div>
  </div>
  <div class="kpi g">
    <div class="lab">Japan FOB save (prior BP)<span class="info">i<span class="tip">Qty × (FOB at {FX_OLD} − FOB at {FX_NEW})
      using the prior Japan base price and Japan’s 38% margin (FOB = BP ÷ FX × 0.62).</span></span></div>
    <div class="val">{money(k["fx_save_prior_jp_eur"])}</div>
    <div class="note">{money(k["fob_prior_old_jp_eur"])} → {money(k["fob_prior_new_jp_eur"])}</div>
  </div>
  <div class="kpi g">
    <div class="lab">Japan FOB save (new BP)<span class="info">i<span class="tip">Same FX relief, but on the new
      Japan base price after the list revision.</span></span></div>
    <div class="val">{money(k["fx_save_newbp_jp_eur"])}</div>
    <div class="note">After the JPY list move</div>
  </div>
  <div class="kpi t">
    <div class="lab">List step (selling)<span class="info">i<span class="tip">Unchanged by FX. Same AIM priced book
      as the revision pack: {money(k["list_step_all_eur"])} on {money(k["billed_all_eur"])} billed.</span></span></div>
    <div class="val">{money(k["list_step_all_eur"])}</div>
    <div class="note">{pct(k["list_step_all_eur"]/k["billed_all_eur"])} · JP {money(k["list_step_jp_eur"])}</div>
  </div>
  <div class="kpi">
    <div class="lab">List step − prior FX save<span class="info">i<span class="tip">Selling-side step minus Japan
      purchase-cost relief at prior BP. Not a P&amp;L forecast — volume and mix held flat.</span></span></div>
    <div class="val">{money(k["net_list_vs_fx_prior"])}</div>
    <div class="note">Flat-qty commercial gap</div>
  </div>
</div>

<div class="grid g2">
  <div class="card">
    <h2>Where does the Japan FOB save sit?</h2>
    <p class="q">Ranked by purchase-cost relief at the prior base price (Japan only).</p>
    <div class="chartbox"><canvas id="cL1"></canvas></div>
  </div>
  <div class="card">
    <h2>Japan vs Thailand — does FX touch both?</h2>
    <p class="q">List step still hits both sources. FX relief is Japan only.</p>
    <div class="chartbox"><canvas id="cSrc"></canvas></div>
  </div>
</div>

<div class="card">
  <h2>Japan FOB save by distributor</h2>
  <p class="q">Same purchase-cost relief, rolled to the trading entity on the AIM priced book.</p>
  <div class="tblwrap">
    <table id="tblDb">
      <thead><tr>
        <th>Distributor</th><th class="n">Billed</th><th class="n">List step</th>
        <th class="n">FOB @{FX_OLD}</th><th class="n">FOB @{FX_NEW}</th>
        <th class="n">FX save (prior)</th><th class="n">FX save (new BP)</th>
      </tr></thead>
      <tbody></tbody>
    </table>
  </div>
</div>

<div class="card">
  <h2>Biggest Japan part numbers by FX save</h2>
  <p class="q">Top 40 Japan lines by prior-BP purchase-cost relief.</p>
  <div class="tblwrap">
    <table id="tblPn">
      <thead><tr>
        <th>Part</th><th>Description</th><th>Family</th>
        <th class="n">Qty</th><th class="n">Billed</th>
        <th class="n">FX save (prior)</th><th class="n">FX save (new BP)</th>
      </tr></thead>
      <tbody></tbody>
    </table>
  </div>
</div>

<footer>
  <p>{payload["method"]}</p>
  <p>Generated {payload["generated"]} · sibling frozen pack left untouched.</p>
</footer>
</div>

<script type="application/json" id="payload">{data_json}</script>
<script>{chart_js}</script>
<script>
(function(){{
  const P = JSON.parse(document.getElementById('payload').textContent);
  const eur = v => {{
    const a = Math.abs(v||0);
    if (a >= 1e6) return '€' + (v/1e6).toFixed(2) + 'M';
    if (a >= 1e3) return '€' + Math.round(v/1e3).toLocaleString() + 'k';
    return '€' + Math.round(v||0).toLocaleString();
  }};
  const num = v => Math.round(v||0).toLocaleString();
  const navy = '#15233c', terra = '#c0552d', good = '#1e6b4f', muted = '#9aa3b2';

  // L1 bars
  const l1 = (P.by_l1_japan || []).slice(0, 12);
  new Chart(document.getElementById('cL1'), {{
    type: 'bar',
    data: {{
      labels: l1.map(r => r.aim_l1 || '(blank)'),
      datasets: [{{
        label: 'Japan FOB save (prior BP)',
        data: l1.map(r => r.fx_save_prior),
        backgroundColor: good
      }}]
    }},
    options: {{
      indexAxis: 'y',
      responsive: true, maintainAspectRatio: false,
      plugins: {{ legend: {{ display: false }},
        tooltip: {{ callbacks: {{ label: c => eur(c.raw) }} }} }},
      scales: {{
        x: {{ ticks: {{ callback: v => eur(v) }}, grid: {{ color: '#eee' }} }},
        y: {{ grid: {{ display: false }} }}
      }}
    }}
  }});

  // Source paired — Japan vs Thailand only (skip Not held)
  const src = (P.by_source || []).filter(r =>
    String(r.source || '').indexOf('Japan') >= 0 ||
    String(r.source || '').indexOf('Thailand') >= 0);
  new Chart(document.getElementById('cSrc'), {{
    type: 'bar',
    data: {{
      labels: src.map(r => (r.source || '').replace(' - ', ' · ')),
      datasets: [
        {{ label: 'List step', data: src.map(r => r.step_eur), backgroundColor: terra }},
        {{ label: 'FX save (prior BP)', data: src.map(r => r.fx_save_prior), backgroundColor: good }}
      ]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ position: 'bottom' }},
        tooltip: {{ callbacks: {{ label: c => c.dataset.label + ': ' + eur(c.raw) }} }}
      }},
      scales: {{
        x: {{ grid: {{ display: false }} }},
        y: {{ ticks: {{ callback: v => eur(v) }}, grid: {{ color: '#eee' }} }}
      }}
    }}
  }});

  const tb = (id, rows, cols) => {{
    const body = document.querySelector('#' + id + ' tbody');
    body.innerHTML = rows.map(r => '<tr>' + cols.map(c => {{
      const v = r[c.k];
      const cls = (c.n || c.q) ? ' class="n"' : '';
      let t;
      if (c.n) t = eur(v);
      else if (c.q) t = num(v);
      else t = (v == null ? '' : String(v));
      return '<td' + cls + '>' + t + '</td>';
    }}).join('') + '</tr>').join('');
  }};
  tb('tblDb', P.by_db_japan || [], [
    {{k:'db'}}, {{k:'billed_eur', n:1}}, {{k:'step_eur', n:1}},
    {{k:'fob_prior_old_eur', n:1}}, {{k:'fob_prior_new_eur', n:1}},
    {{k:'fx_save_prior', n:1}}, {{k:'fx_save_newbp', n:1}}
  ]);
  tb('tblPn', P.top_pn_japan || [], [
    {{k:'part_number'}}, {{k:'description'}}, {{k:'aim_l1'}},
    {{k:'qty', q:1}}, {{k:'billed_eur', n:1}},
    {{k:'fx_save_prior', n:1}}, {{k:'fx_save_newbp', n:1}}
  ]);
}})();
</script>
</body>
</html>
"""
    HTML_OUT.write_text(html, encoding="utf-8")
    say(f"Wrote {HTML_OUT} ({HTML_OUT.stat().st_size:,} bytes)")


def write_launchers() -> None:
    OPEN_HTML.write_text(
        '@echo off\r\nstart "" "%~dp0ISZE_Pricing_Revision_AIM_FX_20261001.html"\r\n',
        encoding="utf-8", newline="")
    OPEN_XLSX.write_text(
        '@echo off\r\nstart "" "%~dp0Pricing_Revision_AIM_FX_20261001.xlsx"\r\n',
        encoding="utf-8", newline="")
    say(f"Wrote {OPEN_HTML.name} and {OPEN_XLSX.name}")


def main() -> None:
    say("Loading AIM priced lines …")
    pr = attach_fob(load_priced())
    payload = build_payload(pr)
    META_OUT.parent.mkdir(parents=True, exist_ok=True)
    META_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    k = payload["kpis"]
    say(f"  cheaper {100*k['cheaper_pct']:.2f}% · "
        f"FX save prior {k['fx_save_prior_jp_eur']:,.0f} · "
        f"list step {k['list_step_all_eur']:,.0f}")
    write_html(payload)
    write_excel(pr, payload)
    write_launchers()
    say("DONE")


if __name__ == "__main__":
    main()
