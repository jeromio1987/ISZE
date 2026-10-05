#!/usr/bin/env python3
"""Build shared scatter: aftermarket shop vs reference dealer sell-out vs CY2025 billed.

Derived CSVs + sales_fact.parquet only. No raw sales XLSX.
"""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(__file__).resolve().parents[3]
DERIVED = ISZE / "01_data" / "00_derived"
PRICING_ANALYTICS = ISZE / "03_analytics" / "isze_pricing"
OUT_DIR = ISZE / "02_dashboards" / "pricing"
HTML_PATH = OUT_DIR / "ISZE_IAM_Price_vs_Billed_PN.html"
CMD_PATH = OUT_DIR / "OPEN_ISZE_IAM_Price_vs_Billed_PN.cmd"
CHART_JS = ISZE / "02_dashboards" / "_ui" / "chart.umd.min.js"

REF_DB = 1.40
REF_DLR = 1.275
REF_FACTOR = REF_DB * REF_DLR  # 1.785

NON_PART = {
    "TRANSPORT",
    "REBATE",
    "LATE PAYMENT INTEREST",
    "DISRACK01",
    "5874123810",
    "5874123811",
    "5874123812",
}

PMS_WEAR = {
    "oil_filter",
    "fuel_filter",
    "air_filter",
    "blower_filter",
    "urea_filter",
    "brake_pad",
    "brake_pad_front",
    "brake_pad_rear",
    "brake_rotor",
    "brake_shoe",
    "brake_shoe_front",
    "brake_shoe_rear",
    "clutch_disc",
    "clutch_kit",
    "clutch_pressure_plate",
    "clutch_booster",
    "release_bearing",
    "pilot_bearing",
}

VINTAGE_META = {
    "ks_uk_202608": {
        "label": "KS UK shop (Aug 2026)",
        "color": "#c0552d",
        "uk": True,
        "kind": "aftermarket shop",
    },
    "eucon_uk_workshop_2023": {
        "label": "Eucon UK workshop (2023)",
        "color": "#15233c",
        "uk": True,
        "kind": "aftermarket workshop quote",
    },
    "autodoc_de_no_20260329": {
        "label": "Autodoc DE/NO online (29 Mar 2026)",
        "color": "#2e7d54",
        "uk": False,
        "kind": "aftermarket shop",
    },
    "autodoc_min_undated": {
        "label": "Autodoc min (undated file; junk SKUs dropped)",
        "color": "#6b6256",
        "uk": False,
        "kind": "aftermarket shop",
    },
    "oem_peer_retail_202608": {
        "label": "OEM peer retail (Aug 2026 basket)",
        "color": "#c9a227",
        "uk": False,
        "kind": "OEM peer retail (not aftermarket shop)",
    },
}


def pn10(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    digits = re.sub(r"\D", "", str(value).strip())
    if len(digits) < 8:
        token = str(value).strip().upper()
        if token in NON_PART:
            return token
        return None
    return digits.zfill(10)


def finite(x, default=None):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(v):
        return default
    return v


def chart_js_inline() -> str:
    raw = CHART_JS.read_text(encoding="utf-8")
    return "\n".join(ln for ln in raw.splitlines() if "sourceMappingURL" not in ln)


def load_billed_cy2025() -> pd.DataFrame:
    path = DERIVED / "sales_fact.parquet"
    import pyarrow.parquet as pq

    names = set(pq.read_schema(path).names)
    pn_col = next(c for c in ("part_number", "Material", "material") if c in names)
    eur_col = next(
        c
        for c in (
            "net_sales_value",
            "Net value",
            "Net Value",
            "net_value",
        )
        if c in names
    )
    qty_col = next(
        c for c in ("billed_qty", "Billed Quantity", "quantity", "Quantity") if c in names
    )
    cols = [pn_col, eur_col, qty_col]
    year_col = "year" if "year" in names else None
    date_col = next(
        (c for c in ("billing_date", "Billing Date") if c in names),
        None,
    )
    if year_col:
        cols.append(year_col)
    elif date_col:
        cols.append(date_col)
    else:
        raise SystemExit("sales_fact.parquet has no year or billing date")

    df = pq.read_table(path, columns=cols).to_pandas()
    if year_col:
        year = pd.to_numeric(df[year_col], errors="coerce")
        df = df.loc[year == 2025].copy()
    else:
        dt = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")
        df = df.loc[dt.dt.year == 2025].copy()

    df["pn"] = df[pn_col].map(pn10)
    df = df.dropna(subset=["pn"])
    df = df[~df["pn"].isin(NON_PART)]
    df["billed_eur"] = pd.to_numeric(df[eur_col], errors="coerce").fillna(0)
    df["billed_qty"] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
    out = (
        df.groupby("pn", as_index=False)
        .agg(billed_eur=("billed_eur", "sum"), billed_qty=("billed_qty", "sum"))
    )
    return out[(out["billed_eur"] > 0) | (out["billed_qty"] > 0)].copy()


def load_pms_labels() -> pd.DataFrame:
    path = DERIVED / "parts_catalog_dimension.csv"
    cat = pd.read_csv(
        path,
        usecols=["part_number", "pms_category", "fig_key_label"],
        dtype={"part_number": str},
        low_memory=False,
    )
    cat["pn"] = cat["part_number"].map(pn10)
    cat = cat.dropna(subset=["pn"])
    cat["pms_category"] = cat["pms_category"].fillna("").astype(str)
    cat = cat[cat["pms_category"].isin(PMS_WEAR)]
    return cat.drop_duplicates("pn")[["pn", "pms_category", "fig_key_label"]]


def iam_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(
            columns=["pn", "description", "pr00_eur", "shop_eur", "source_id"]
        )
    return pd.DataFrame(rows)


def load_ks() -> pd.DataFrame:
    path = DERIVED / "iam_ks_price_gap.csv"
    df = pd.read_csv(path, dtype={"pn": str}, low_memory=False)
    rows = []
    for _, r in df.iterrows():
        pn = pn10(r.get("pn"))
        shop = finite(r.get("ks_am_min_eur"))
        pr00 = finite(r.get("isze_price_eur"))
        if not pn or shop is None or shop <= 0 or pr00 is None or pr00 <= 0:
            continue
        rows.append(
            {
                "pn": pn,
                "description": str(r.get("description") or ""),
                "pr00_eur": pr00,
                "shop_eur": shop,
                "source_id": "ks_uk_202608",
            }
        )
    out = iam_frame(rows)
    if out.empty:
        return out
    return out.sort_values("shop_eur").drop_duplicates("pn", keep="first")


def load_eucon_2023() -> pd.DataFrame:
    path = DERIVED / "eucon_uk_survey_2023_price_gap.csv"
    df = pd.read_csv(path, dtype={"pn": str}, low_memory=False)
    rows = []
    for _, r in df.iterrows():
        pn = pn10(r.get("pn"))
        shop = finite(r.get("competitor_avg_eur"))
        pr00 = finite(r.get("isze_price_eur"))
        if not pn or shop is None or shop <= 0 or pr00 is None or pr00 <= 0:
            continue
        rows.append(
            {
                "pn": pn,
                "description": str(r.get("description") or ""),
                "pr00_eur": pr00,
                "shop_eur": shop,
                "source_id": "eucon_uk_workshop_2023",
            }
        )
    out = iam_frame(rows)
    if out.empty:
        return out
    return out.drop_duplicates("pn", keep="first")


def load_autodoc_deno() -> pd.DataFrame:
    path = DERIVED / "eucon_price_gap.csv"
    df = pd.read_csv(path, dtype={"pn": str}, low_memory=False)
    rows = []
    for _, r in df.iterrows():
        pn = pn10(r.get("pn"))
        shop = finite(r.get("Avg_Competitor_EUR"))
        pr00 = finite(r.get("ISZE_IE40_Price_EUR"))
        if not pn or shop is None or shop <= 0 or pr00 is None or pr00 <= 0:
            continue
        rows.append(
            {
                "pn": pn,
                "description": str(r.get("description") or ""),
                "pr00_eur": pr00,
                "shop_eur": shop,
                "source_id": "autodoc_de_no_20260329",
            }
        )
    return iam_frame(rows).drop_duplicates("pn", keep="first")


def load_autodoc_undated() -> tuple[pd.DataFrame, int]:
    path = DERIVED / "competitiveness_autodoc_risk.csv"
    df = pd.read_csv(path, dtype={"part_number": str}, low_memory=False)
    kept = []
    junk = 0
    for _, r in df.iterrows():
        pn = pn10(r.get("part_number"))
        shop = finite(r.get("autodoc_min_eur"))
        pr00 = finite(r.get("pr00_eur"))
        if not pn or shop is None or shop <= 0 or pr00 is None or pr00 <= 0:
            junk += 1
            continue
        if shop / pr00 < 0.05 and shop < 15:
            junk += 1
            continue
        if shop / pr00 > 8:
            junk += 1
            continue
        kept.append(
            {
                "pn": pn,
                "description": str(r.get("description") or ""),
                "pr00_eur": pr00,
                "shop_eur": shop,
                "source_id": "autodoc_min_undated",
            }
        )
    return iam_frame(kept).drop_duplicates("pn", keep="first"), junk


def load_oem_peer() -> pd.DataFrame:
    path = PRICING_ANALYTICS / "oem_peer_basket.csv"
    df = pd.read_csv(path, dtype={"isze_pn": str}, low_memory=False)
    rows = []
    for _, r in df.iterrows():
        if str(r.get("status") or "") != "priced":
            continue
        pn = pn10(r.get("isze_pn"))
        shop = finite(r.get("peer_street_eur"))
        if not pn or shop is None or shop <= 0:
            continue
        rows.append(
            {
                "pn": pn,
                "description": str(r.get("description") or ""),
                "shop_eur": shop,
                "source_id": "oem_peer_retail_202608",
            }
        )
    out = iam_frame(rows)
    if out.empty:
        return out
    g = out.groupby("pn", as_index=False).agg(
        description=("description", "first"),
        shop_eur=("shop_eur", "median"),
        source_id=("source_id", "first"),
    )
    return g


def load_competitor_margin() -> dict[str, dict]:
    """competitor_price_panel.csv (Jerome's go, 2026-09-25) -- 43 PNs, a separate KS/AIM-based
    competitor read (not any of the vintages above). gm_if_matched_pct is the gross margin ISZE
    would keep if it matched that file's competitor price; cost_est in that file is 50% of list
    (a book average, not an actual purchase cost) -- see competitor_price_panel_meta.json.
    Returned dict is keyed by 10-digit pn; only PNs actually present in the file get an entry.
    """
    path = DERIVED / "competitor_price_panel.csv"
    df = pd.read_csv(path, dtype={"pn": str}, low_memory=False)
    out: dict[str, dict] = {}
    for _, r in df.iterrows():
        pn = pn10(r.get("pn"))
        if not pn:
            continue
        gm = finite(r.get("gm_if_matched_pct"))
        if gm is None:
            continue
        out[pn] = {
            "gm_if_matched_pct": round(gm, 1),
            "cpp_iam_eur": finite(r.get("iam")),
            "cpp_cost_est_eur": finite(r.get("cost_est")),
        }
    return out


def is_junk(pr00: float, shop: float) -> bool:
    if pr00 <= 0 or shop <= 0:
        return True
    if shop / pr00 < 0.05 and shop < 15:
        return True
    if shop / pr00 > 8:
        return True
    return False


def build_points() -> tuple[list[dict], dict]:
    billed = load_billed_cy2025()
    billed_map = billed.set_index("pn")
    pms = load_pms_labels()
    pms_map = pms.set_index("pn")

    ks = load_ks()
    eu2023 = load_eucon_2023()
    deno = load_autodoc_deno()
    auto_u, auto_junk = load_autodoc_undated()
    oem = load_oem_peer()
    margin_map = load_competitor_margin()

    pr00_lookup: dict[str, float] = {}
    for frame in (ks, eu2023, deno, auto_u):
        for _, r in frame.iterrows():
            pr00_lookup.setdefault(r["pn"], float(r["pr00_eur"]))

    frames = [ks, eu2023, deno, auto_u, oem]
    iam = pd.concat([f for f in frames if not f.empty], ignore_index=True)

    dropped_junk = auto_junk
    points: list[dict] = []
    for _, r in iam.iterrows():
        pn = r["pn"]
        if pn not in billed_map.index:
            continue
        shop = finite(r["shop_eur"])
        pr00 = finite(r.get("pr00_eur")) or pr00_lookup.get(pn)
        pr00 = finite(pr00)
        if shop is None or pr00 is None:
            continue
        if is_junk(pr00, shop):
            dropped_junk += 1
            continue
        ref = pr00 * REF_FACTOR
        idx = shop / ref
        if not math.isfinite(idx) or idx <= 0:
            continue
        b = billed_map.loc[pn]
        billed_eur = finite(b["billed_eur"], 0.0) or 0.0
        billed_qty = finite(b["billed_qty"], 0.0) or 0.0
        if billed_eur <= 0 and billed_qty <= 0:
            continue
        pms_cat = ""
        pms_lab = ""
        if pn in pms_map.index:
            rowp = pms_map.loc[pn]
            if isinstance(rowp, pd.DataFrame):
                rowp = rowp.iloc[0]
            pms_cat = str(rowp.get("pms_category") or "")
            pms_lab = str(rowp.get("fig_key_label") or "")
        sid = str(r["source_id"])
        meta = VINTAGE_META[sid]
        margin = margin_map.get(pn)
        points.append(
            {
                "pn": pn,
                "description": str(r.get("description") or "")[:80],
                "source_id": sid,
                "vintage": meta["label"],
                "kind": meta["kind"],
                "color": meta["color"],
                "uk_centric": meta["uk"],
                "pr00_eur": round(pr00, 2),
                "reference_sellout_eur": round(ref, 2),
                "shop_eur": round(shop, 2),
                "price_index": round(idx, 3),
                "shop_below_reference": bool(idx < 1),
                "billed_eur": round(billed_eur, 2),
                "billed_qty": round(billed_qty, 2),
                "pms_category": pms_cat,
                "pms_label": pms_lab,
                "gm_if_matched_pct": margin["gm_if_matched_pct"] if margin else None,
            }
        )

    unique_pns = sorted({p["pn"] for p in points})
    by_source = {}
    for p in points:
        by_source[p["source_id"]] = by_source.get(p["source_id"], 0) + 1
    unique_by_source = {}
    for p in points:
        unique_by_source.setdefault(p["source_id"], set()).add(p["pn"])
    unique_by_source = {k: len(v) for k, v in unique_by_source.items()}

    n = len(unique_pns)
    n_points = len(points)
    below = len({p["pn"] for p in points if p["shop_below_reference"]})
    indices = [p["price_index"] for p in points]
    billed_set = billed.loc[billed["pn"].isin(unique_pns), "billed_eur"].sum() if n else 0.0
    pms_rows = []
    seen = set()
    for p in sorted(points, key=lambda x: -x["billed_eur"]):
        if not p["pms_category"] or p["pn"] in seen:
            continue
        seen.add(p["pn"])
        pms_rows.append(
            {
                "pn": p["pn"],
                "description": p["description"],
                "pms_category": p["pms_category"].replace("_", " "),
                "pms_label": p["pms_label"],
                "billed_eur": p["billed_eur"],
                "price_index": p["price_index"],
                "vintage": p["vintage"],
            }
        )

    uk_points = sum(1 for p in points if p["uk_centric"])
    n_margin_matched = len({p["pn"] for p in points if p["gm_if_matched_pct"] is not None})
    stats = {
        "n_parts": n,
        "n_points": n_points,
        "n_margin_matched": n_margin_matched,
        "n_shop_below_reference": below,
        "median_price_index": round(float(pd.Series(indices).median()), 3) if indices else None,
        "billed_eur_on_set": round(float(billed_set), 0),
        "billed_pn_universe_cy2025": int(len(billed)),
        "dropped_junk": int(dropped_junk),
        "by_source_points": by_source,
        "by_source_parts": unique_by_source,
        "uk_point_share": round(uk_points / n_points, 3) if n_points else 0,
        "pms_n": len(pms_rows),
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "small_n": n < 40,
    }
    return points, stats, pms_rows


def esc(s) -> str:
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def fmt_eur(n) -> str:
    n = finite(n, 0) or 0
    if abs(n) >= 1_000_000:
        return f"€{n/1_000_000:.1f}m"
    if abs(n) >= 1000:
        return f"€{n/1000:.0f}k"
    return f"€{n:,.0f}"


def fmt_n(n) -> str:
    return f"{int(n):,}"


def write_cmd() -> None:
    body = (
        "@echo off\r\n"
        "setlocal\r\n"
        'cd /d "%~dp0"\r\n'
        f'set "HTML=%~dp0{HTML_PATH.name}"\r\n'
        'if not exist "%HTML%" (\r\n'
        "  echo HTML is not next to this launcher:\r\n"
        "  echo %HTML%\r\n"
        "  pause\r\n"
        "  exit /b 1\r\n"
        ")\r\n"
        'start "" "%HTML%"\r\n'
        "if errorlevel 1 (\r\n"
        "  echo Browser did not start. Opening the folder instead.\r\n"
        '  explorer.exe "%~dp0"\r\n'
        "  pause\r\n"
        ")\r\n"
        "endlocal\r\n"
    )
    CMD_PATH.write_bytes(body.encode("ascii"))


def render(points: list[dict], stats: dict, pms_rows: list[dict]) -> str:
    payload = {
        "question": (
            "On parts where we already have an aftermarket shop price, "
            "is our reference dealer sell-out higher, and did we bill more or less?"
        ),
        "points": points,
        "stats": stats,
        "pms_rows": pms_rows,
        "reference_note": (
            "Reference dealer sell-out is the ISZE list price times 1.40 to the dealer "
            "times 1.275 to the customer price we use as the dealer sell-out we compare to shops."
        ),
        "price_index_note": "Price index = aftermarket quote or shop price divided by that reference dealer sell-out.",
    }
    data_json = json.dumps(payload, ensure_ascii=True, allow_nan=False)

    n = stats["n_parts"]
    n_pts = stats["n_points"]
    amber = ""
    if stats["small_n"]:
        amber = (
            f'<div class="amber">Small overlap. {fmt_n(n)} parts have both a billed line '
            "and a dated aftermarket price. This is not the whole book. No invented "
            "aftermarket unit share. 100% minus PMS capture is not aftermarket share.</div>"
        )
    else:
        amber = (
            f'<div class="note-bar">{fmt_n(n)} parts with both a billed line and a dated '
            "aftermarket price. This is not the whole book. Points are coloured by scrape "
            "vintage — 2023 UK workshop quotes are not mixed into the 2026 online series.</div>"
        )

    by_pn: dict[str, dict] = {}
    for p in sorted(points, key=lambda x: -x["billed_eur"]):
        by_pn.setdefault(p["pn"], p)
    top = list(by_pn.values())[:25]
    max_eur = max((p["billed_eur"] for p in top), default=1) or 1
    bars = []
    for p in top:
        w = max(2, round(100 * p["billed_eur"] / max_eur))
        below = "below" if p["shop_below_reference"] else "above"
        bars.append(
            f'<div class="bar-row"><span class="fb-lb">{esc(p["pn"])}</span>'
            f'<span class="fb-track"><span class="fb-bar {below}" style="width:{w}%"></span></span>'
            f'<span class="fb-val">{fmt_eur(p["billed_eur"])} · idx {p["price_index"]:.2f}</span></div>'
        )
    bar_html = "\n".join(bars) or "<p>No overlap points after junk filter.</p>"

    table_pts = sorted(points, key=lambda x: -x["billed_eur"])[:80]
    trs = []
    for p in table_pts:
        pms = esc(p["pms_category"].replace("_", " ")) if p["pms_category"] else "—"
        cls = "lo" if p["shop_below_reference"] else ""
        gm = p.get("gm_if_matched_pct")
        if gm is None:
            gm_cell = "<td class='num'>—</td>"
        else:
            gm_cls = "gm-neg" if gm < 0 else ("gm-slim" if gm < 20 else "gm-ok")
            gm_cell = f"<td class='num {gm_cls}'>{gm:.1f}%</td>"
        trs.append(
            "<tr class='" + cls + "'>"
            f"<td>{esc(p['pn'])}</td>"
            f"<td>{esc(p['description'])}</td>"
            f"<td>{esc(p['vintage'])}</td>"
            f"<td class='num'>{p['pr00_eur']:.2f}</td>"
            f"<td class='num'>{p['reference_sellout_eur']:.2f}</td>"
            f"<td class='num'>{p['shop_eur']:.2f}</td>"
            f"<td class='num'>{p['price_index']:.2f}</td>"
            f"<td class='num'>{p['billed_qty']:,.0f}</td>"
            f"<td class='num'>{fmt_eur(p['billed_eur'])}</td>"
            f"<td>{pms}</td>"
            f"{gm_cell}"
            "</tr>"
        )
    tbody = "\n".join(trs) or "<tr><td colspan='11'>No rows. Overlap is empty after filters.</td></tr>"

    pms_trs = []
    for r in pms_rows[:40]:
        pms_trs.append(
            "<tr>"
            f"<td>{esc(r['pn'])}</td>"
            f"<td>{esc(r['description'])}</td>"
            f"<td>{esc(r['pms_category'])}</td>"
            f"<td class='num'>{fmt_eur(r['billed_eur'])}</td>"
            f"<td class='num'>{r['price_index']:.2f}</td>"
            f"<td>{esc(r['vintage'])}</td>"
            "</tr>"
        )
    pms_tbody = "\n".join(pms_trs) or (
        "<tr><td colspan='6'>None of the overlap parts sit in a PMS wear category in the catalogue.</td></tr>"
    )

    med = stats["median_price_index"]
    med_s = f"{med:.2f}" if med is not None else "—"
    below_s = fmt_n(stats["n_shop_below_reference"])
    billed_s = fmt_eur(stats["billed_eur_on_set"])

    src_bits = []
    for sid, meta in VINTAGE_META.items():
        n_src = stats["by_source_parts"].get(sid, 0)
        if not n_src:
            continue
        src_bits.append(
            f"<li><span class='sw' style='background:{meta['color']}'></span>"
            f"{esc(meta['label'])} — {fmt_n(n_src)} parts · {esc(meta['kind'])}</li>"
        )
    src_html = "\n".join(src_bits) or "<li>No sources survived the join.</li>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aftermarket shop vs what we billed — by part number</title>
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;background:#f7f4ee;font-size:15px;line-height:1.5}}
h1,h2,h3{{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;margin:0}}
.hero{{background:linear-gradient(155deg,#15233c 0%,#203759 55%,#2b4a78 100%);color:#eef1f6;padding:42px 28px 28px}}
.hero-inner{{max-width:1180px;margin:0 auto}}
.brand{{font-family:Georgia,serif;font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:#c9d4e6;margin-bottom:14px}}
.hero h1{{color:#fff;font-size:30px;line-height:1.15;margin:0 0 12px;font-weight:400}}
.hero .rule{{width:64px;height:3px;background:#c0552d;margin:0 0 16px}}
.hero .lead{{max-width:820px;font-size:16px;color:#d5dce8;margin:0 0 10px}}
.hero .sub{{max-width:820px;font-size:13.5px;color:#9fb0ca;margin:0 0 22px}}
.hero-kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.hk{{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);padding:14px 16px;position:relative;cursor:help}}
.hk .v{{font-size:28px;font-weight:700;letter-spacing:-.5px;color:#fff;font-family:Georgia,serif}}
.hk .l{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#aeb9cb;margin-top:4px}}
.hk .n{{font-size:12px;color:#9aa8bd;margin-top:6px;line-height:1.35}}
.hk .tip{{display:none;position:absolute;left:0;top:calc(100% + 8px);width:min(340px,70vw);
  background:#15233c;color:#f7f4ee;border-top:3px solid #c0552d;padding:12px 14px;
  font-size:12.5px;line-height:1.45;z-index:50;box-shadow:0 8px 24px rgba(0,0,0,.25)}}
.hk:hover .tip,.hk:focus-within .tip{{display:block}}
.wrap{{max-width:1180px;margin:0 auto;padding:28px 28px 80px}}
.amber{{background:#f8e4dc;border-left:4px solid #c0552d;color:#222;padding:14px 16px;margin:0 0 18px}}
.note-bar{{background:#fff;border-left:4px solid #15233c;color:#222;padding:14px 16px;margin:0 0 18px}}
h2{{font-size:22px;margin:8px 0 8px;padding-bottom:8px;border-bottom:2px solid #1a2b4a}}
h2 .no{{color:#c0552d}}
.lead{{color:#6b6256;margin:0 0 18px;max-width:860px}}
.card{{background:#fff;border:1px solid #d9d3c8;padding:18px 18px 14px;margin:0 0 18px}}
.card h3{{font-size:15px;margin:0 0 6px}}
.chart-wrap{{position:relative;width:100%;min-height:420px;height:440px}}
.chart-wrap canvas{{display:block;width:100%!important;min-height:400px}}
.controls{{display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin:0 0 10px;font-size:13px;color:#52514e}}
.controls label{{display:flex;gap:6px;align-items:center;cursor:pointer}}
.fallback{{margin-top:14px}}
.bar-row{{display:grid;grid-template-columns:minmax(90px,22%) 1fr minmax(140px,28%);gap:8px;align-items:center;font-size:12px;margin:5px 0}}
.fb-lb{{color:#52514e;font-variant-numeric:tabular-nums}}
.fb-track{{background:#eceae4;height:16px;border-radius:2px;overflow:hidden}}
.fb-bar{{display:block;height:100%;min-width:2px;background:#15233c}}
.fb-bar.below{{background:#c0552d}}
.fb-val{{text-align:right;font-variant-numeric:tabular-nums;color:#222;font-size:11.5px}}
table{{width:100%;border-collapse:collapse;font-size:12.5px;background:#fff}}
thead th{{background:#1a2b4a;color:#f7f4ee;text-align:left;padding:8px 9px;font-size:11px;text-transform:uppercase;letter-spacing:.04em}}
td{{padding:7px 9px;border-bottom:1px solid #e8e4dc;color:#222}}
tbody tr:nth-child(even) td{{background:#faf8f4;color:#222}}
td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}
tr.lo td:nth-child(7){{color:#c0552d;font-weight:700}}
td.gm-neg{{color:#b23b3b;font-weight:700}} td.gm-slim{{color:#c0552d}} td.gm-ok{{color:#2e7d54}}
.table-scroll{{overflow:auto;max-height:420px;border:1px solid #d9d3c8}}
ul.src{{list-style:none;padding:0;margin:8px 0}}
ul.src li{{margin:4px 0}}
.sw{{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:8px;vertical-align:-1px}}
.foot{{margin-top:36px;padding-top:12px;border-top:1px solid #d9d3c8;font-size:12px;color:#6b6256;max-width:980px}}
.chart-status{{display:none;margin-top:10px;padding:10px 14px;background:#f8e4dc;border-left:3px solid #c0552d;color:#8a3030;font-size:13px}}
.chart-status.show{{display:block}}
@media (max-width:900px){{.hero-kpis{{grid-template-columns:repeat(2,1fr)}}.hero h1{{font-size:24px}}}}
</style>
</head>
<body>
<div class="hero">
  <div class="hero-inner">
    <div class="brand">ISZE aftermarket pricing · CY2025 billed</div>
    <h1>On parts where we already have an aftermarket shop price, is our reference dealer sell-out higher, and did we bill more or less?</h1>
    <div class="rule"></div>
    <p class="lead">{fmt_n(n)} parts with both a billed line and a dated aftermarket price. This is not the whole book.</p>
    <p class="sub">Reference dealer sell-out is the ISZE list price times 1.40 to the dealer times 1.275 to the customer price we use as the dealer sell-out we compare to shops. Price index = shop or aftermarket quote ÷ that reference. Below 1 means the shop is cheaper than our reference.</p>
    <div class="hero-kpis">
      <div class="hk" tabindex="0">
        <div class="v">{fmt_n(n)}</div>
        <div class="l">Parts in the overlap</div>
        <div class="n">{fmt_n(n_pts)} dated quotes on those parts</div>
        <div class="tip">A part is in this set only if CY2025 billing has a line and we have a dated shop or workshop quote. {fmt_n(stats['billed_pn_universe_cy2025'])} part numbers billed in CY2025 in total. This chart is the intersection, not the catalogue.</div>
      </div>
      <div class="hk" tabindex="0">
        <div class="v">{below_s}</div>
        <div class="l">Shop below our reference</div>
        <div class="n">Unique parts with at least one quote cheaper than reference</div>
        <div class="tip">Counted at part level if any dated quote on that part has price index below 1. KS UK and Eucon 2023 are UK-centric. Autodoc DE/NO is a 29 Mar 2026 online panel.</div>
      </div>
      <div class="hk" tabindex="0">
        <div class="v">{med_s}</div>
        <div class="l">Median price index</div>
        <div class="n">Across every dated quote in the scatter</div>
        <div class="tip">Price index = aftermarket quote ÷ reference dealer sell-out. Reference dealer sell-out is the ISZE list × 1.40 to the dealer × 1.275 to the customer price we use as the dealer sell-out we compare to shops.</div>
      </div>
      <div class="hk" tabindex="0">
        <div class="v">{billed_s}</div>
        <div class="l">What we billed on this set</div>
        <div class="n">CY2025 network billed € on the {fmt_n(n)} overlap parts</div>
        <div class="tip">Network billed in calendar 2025 from the derived sales fact. UTI and UMI are separate Israel distributors; IUK is not ITUK. This is not GPS target spend per truck and not a PMS score.</div>
      </div>
    </div>
  </div>
</div>
<div class="wrap">
{amber}

<h2><span class="no">1 ·</span> Scatter — price index vs billed €</h2>
<p class="lead">Each point is one part number × one dated quote. Colour is vintage. Vertical line at 1.0: shop equals our reference dealer sell-out. Higher on the chart means we billed more of that part in 2025. Switch the axis to billed quantity if you want units, not euros. PMS wear parts are labelled in the small table below — they are not blended into the Y axis.</p>
<div class="card">
  <div class="controls">
    <label><input type="radio" name="yaxis" value="eur" checked> Y = billed €</label>
    <label><input type="radio" name="yaxis" value="qty"> Y = billed quantity</label>
    <span>Left of 1.0 = shop cheaper than our reference. Terracotta bars below = same idea in the fallback list.</span>
  </div>
  <div class="chart-wrap"><canvas id="scatter" width="1100" height="420"></canvas></div>
  <div id="chartStatus" class="chart-status">Chart library did not paint. The ranked bars and the table below are the page.</div>
  <div class="fallback">
    <h3>Largest billed parts in the overlap (paints without the chart)</h3>
    {bar_html}
  </div>
</div>

<h2><span class="no">2 ·</span> Vintage on this chart</h2>
<div class="card">
  <ul class="src">{src_html}</ul>
  <p class="lead" style="margin:8px 0 0">KS and the 2023 Eucon workshop file are UK-centric (GBP converted at 1.17). Autodoc DE/NO is a 29 Mar 2026 online panel. OEM peer retail is not an aftermarket shop — it is a separate colour so it is not mixed with workshop 2023 or KS 2026. {fmt_n(stats['dropped_junk'])} junk Autodoc matches were dropped (wrong SKU / €2-class hits on engines). We do not invent an aftermarket unit share from this n.</p>
</div>

<h2><span class="no">3 ·</span> Overlap table</h2>
<p class="lead">Up to 80 points, largest billed € first. Price index below 1 is marked. Full scatter uses every dated quote in the embedded data.</p>
<p class="note-bar">"Margin if matched to competitor price" (last column) comes from a separate file, <code>competitor_price_panel.csv</code> (43 PNs, a KS/AIM-based competitor read — not any of the vintages in section 2 above): the gross margin ISZE would keep if it matched THAT file's competitor price. Its cost is estimated at 50% of list (a book average, not an actual purchase cost) — see <code>competitor_price_panel_meta.json</code>. Populated for {fmt_n(stats['n_margin_matched'])} of the {fmt_n(n)} overlap parts; blank means that part has no row in the file, not a zero margin.</p>
<div class="table-scroll">
<table>
<thead>
<tr>
  <th>Part</th><th>Description</th><th>Vintage</th>
  <th class="num">ISZE list €</th><th class="num">Reference dealer sell-out €</th>
  <th class="num">Shop / quote €</th><th class="num">Price index</th>
  <th class="num">Billed qty</th><th class="num">Billed €</th><th>PMS wear?</th>
  <th class="num">Margin if matched (competitor)</th>
</tr>
</thead>
<tbody>
{tbody}
</tbody>
</table>
</div>

<h2><span class="no">4 ·</span> PMS wear parts in this overlap (label only)</h2>
<p class="lead">{fmt_n(stats['pms_n'])} overlap parts sit in a PMS wear category in the catalogue. That is a label, not a second Y axis and not a blended GPS/PMS score.</p>
<div class="table-scroll">
<table>
<thead>
<tr><th>Part</th><th>Description</th><th>PMS category</th><th class="num">Billed €</th><th class="num">Price index</th><th>Vintage shown</th></tr>
</thead>
<tbody>
{pms_tbody}
</tbody>
</table>
</div>

<div class="foot">
  Snapshot {esc(stats['built_at'])}. Billed = derived sales fact, calendar 2025, network (not one distributor). UTI ≠ UMI. IUK ≠ ITUK.
  Aftermarket sources: KS UK shop Aug 2026; Eucon UK IAM workshop 2023; PartsPool Autodoc DE/NO 29 Mar 2026; Autodoc min file after junk filter; OEM peer retail basket Aug 2026 as its own series.
  Reference dealer sell-out = ISZE list × 1.40 × 1.275. Open this file from Explorer (or the sibling OPEN cmd). Built for file open — data is embedded.
</div>
</div>
<script type="application/json" id="scatter-data">{data_json}</script>
<script>
{chart_js_inline()}
</script>
<script>
(function(){{
  function payload(){{
    var el = document.getElementById('scatter-data');
    try {{ return JSON.parse(el.textContent); }} catch (e) {{ return {{points:[]}}; }}
  }}
  var data = payload();
  var points = data.points || [];
  var status = document.getElementById('chartStatus');
  function yKey(){{
    var r = document.querySelector('input[name="yaxis"]:checked');
    return (r && r.value === 'qty') ? 'billed_qty' : 'billed_eur';
  }}
  function paint(){{
    if (typeof Chart === 'undefined') {{
      if (status) status.classList.add('show');
      return;
    }}
    var yk = yKey();
    var groups = {{}};
    points.forEach(function(p){{
      var id = p.source_id;
      if (!groups[id]) groups[id] = {{label: p.vintage, color: p.color, pts: []}};
      groups[id].pts.push({{x: p.price_index, y: p[yk], pn: p.pn, shop: p.shop_eur, ref: p.reference_sellout_eur, billed: p.billed_eur, qty: p.billed_qty}});
    }});
    var ys = points.map(function(p){{ return p[yk]; }}).filter(function(v){{ return v > 0; }});
    var yMin = ys.length ? Math.min.apply(null, ys) : 1;
    var yMax = ys.length ? Math.max.apply(null, ys) : 10;
    if (yMin <= 0) yMin = 1;
    var datasets = Object.keys(groups).map(function(id){{
      var g = groups[id];
      return {{
        label: g.label,
        data: g.pts,
        backgroundColor: g.color,
        borderColor: g.color,
        pointRadius: 5,
        pointHoverRadius: 7
      }};
    }});
    datasets.push({{
      label: 'Shop = our reference',
      data: [{{x:1, y:yMin}}, {{x:1, y:yMax}}],
      type: 'line',
      borderColor: '#c0552d',
      borderDash: [6,4],
      pointRadius: 0,
      fill: false,
      order: 0
    }});
    var canvas = document.getElementById('scatter');
    if (!canvas) return;
    if (window._iamScatter) window._iamScatter.destroy();
    window._iamScatter = new Chart(canvas.getContext('2d'), {{
      type: 'scatter',
      data: {{ datasets: datasets }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ position: 'bottom', labels: {{ color: '#222', boxWidth: 12 }} }},
          tooltip: {{
            callbacks: {{
              label: function(ctx){{
                var p = ctx.raw || {{}};
                if (p.pn) {{
                  return p.pn + ' · index ' + ctx.parsed.x.toFixed(2) + ' · billed €' + Math.round(p.billed).toLocaleString('en-GB');
                }}
                return 'Reference line (index = 1)';
              }}
            }}
          }}
        }},
        scales: {{
          x: {{
            title: {{ display: true, text: 'Price index (shop ÷ reference dealer sell-out)', color: '#222' }},
            ticks: {{ color: '#222' }},
            grid: {{ color: '#e8e4dc' }}
          }},
          y: {{
            type: 'logarithmic',
            title: {{ display: true, text: yk === 'billed_qty' ? 'Billed quantity CY2025 (log)' : 'Billed € CY2025 (log)', color: '#222' }},
            ticks: {{ color: '#222' }},
            grid: {{ color: '#e8e4dc' }}
          }}
        }}
      }}
    }});
  }}
  document.querySelectorAll('input[name="yaxis"]').forEach(function(el){{
    el.addEventListener('change', paint);
  }});
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', paint);
  else paint();
}})();
</script>
</body>
</html>
"""


def main() -> None:
    if not CHART_JS.is_file():
        raise SystemExit(f"missing Chart.js: {CHART_JS}")
    points, stats, pms_rows = build_points()
    html = render(points, stats, pms_rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_PATH.write_text(html, encoding="utf-8")
    write_cmd()
    print("HTML", HTML_PATH)
    print("CMD", CMD_PATH)
    print("n_parts", stats["n_parts"], "n_points", stats["n_points"])
    print("by_source_parts", stats["by_source_parts"])
    print("dropped_junk", stats["dropped_junk"])
    print("small_n", stats["small_n"])
    print("n_margin_matched", stats["n_margin_matched"])


if __name__ == "__main__":
    main()
