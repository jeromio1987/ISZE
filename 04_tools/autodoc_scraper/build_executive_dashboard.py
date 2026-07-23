"""
Build standalone ISZE Executive HTML dashboard (10 views + sourced explanation layer).

No Streamlit. Every figure traces to loaded files or editable CSV lookups.
Run:
    cd .../autodoc_scraper
    python build_executive_dashboard.py
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).parent
HANDOFF = SCRIPT_DIR / "_HANDOFF_BUNDLE"
sys.path.insert(0, str(HANDOFF))
OUT_DIR = SCRIPT_DIR / "_html_previews"
OUT_PATH = OUT_DIR / "isze_executive_dashboard.html"
OUT_PATH_PMS = OUT_DIR / "isze_executive_pms.html"
OUT_PATH_IAM = OUT_DIR / "isze_executive_iam.html"

PMS_SECTIONS = frozenset({"explain", "cockpit", "pms", "multidb", "scenario", "geo", "method"})
IAM_SECTIONS = frozenset({"explain", "cockpit_iam", "brands", "threat", "pn", "category", "quality", "geo", "method_iam", "scenario", "pms_bridge", "price_sim"})
# "scenario" added 2026-07-09: DB/DLR margin assumptions table existed in code but was
# excluded from the iam-only build — Jerome couldn't see what margins were assumed.
# "pms_bridge" added 2026-07-09: new section, see pms_iam_bridge_html().

# PMS categories this bridge covers, keyed to iml_v7_ituk_cy2025.yaml `categories[].key`,
# each with a keyword filter over the AM-scraper Description field. Deliberately keyword-based
# (not AIM_Category) because AIM_Category is too coarse (e.g. "Maintenance Service" bundles
# oil+air+more) to line up with the 5 PMS categories.
PMS_BRIDGE_CATEGORIES = [
    ("oil_filter",  "Oil filter",  r"OIL FILTER"),
    ("fuel_filter", "Fuel filter", r"FUEL FILTER|FUEL.*FILTER"),
    ("air_filter",  "Air filter",  r"AIR FILTER|ELEMENT; AIR"),
    ("clutch",      "Clutch",      r"CLUTCH"),
    ("brake",       "Brake",       r"BRAKE|BRK"),
]

sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(HANDOFF))

from html_export import _plotly_div, _quadrant_table_rows  # noqa: E402
from iam_scoring import (  # noqa: E402
    brand_league,
    category_concentration,
    compute_expected_loss,
    compute_lost_sales,
    compute_scores,
    data_quality_report,
    load_brand_tiers,
    load_substitution_table,
)

GBP_EUR = 1.17
SEK_EUR = 0.089

SITES = [
    ("AD_UK", "autodoc_results.csv", "Autodoc_MinPrice_GBP", "Autodoc_AllPrices_GBP", "Autodoc_CheapestBrand", GBP_EUR),
    ("MEK", "mekonomen_results.csv", "MEK_AM_MinPrice_SEK", None, "MEK_AM_Brands", SEK_EUR),
    ("KS_AM", "ks_results.csv", "KS_AM_MinPrice_GBP", None, "KS_AM_SKUs", GBP_EUR),
    ("KS_GEN", "ks_results.csv", "KS_GEN_MinPrice_GBP", None, None, GBP_EUR),
]

# Filled in main() from sources.yaml + CLI
BUILD_OPTS: dict[str, Any] = {}
SOURCES: dict[str, Path] = {}


def load_build_config() -> tuple[dict, dict[str, Path], dict[str, Any]]:
    """Paths and defaults from handoff sources.yaml."""
    from sources_loader import load_sources_config, resolve_paths

    cfg = load_sources_config(HANDOFF / "sources.yaml")
    paths = resolve_paths(cfg)
    yaml_defaults = cfg.get("defaults") or {}
    sources = {
        "v3": paths.get("v3_pn_matrix") or (HANDOFF / "ISZE_Parts_Intelligence_v3.xlsx"),
        "uio": paths.get("uio_overview"),
        "pms_calc": paths.get("pms_coverage_calculator"),
        "pms_capture": paths.get("pms_capture_by_db"),
        "sources_yaml": HANDOFF / "sources.yaml",
        "brand_tiers": SCRIPT_DIR / "iam_brand_tiers.csv",
        "substitution": SCRIPT_DIR / "substitution_probability.csv",
        "pms_intervals": SCRIPT_DIR / "pms_intervals.csv",
    }
    return cfg, paths, {**yaml_defaults, "sources": sources}


def _clean_min(s, floor=3.0):
    if not isinstance(s, str):
        return None
    vals = []
    for p in s.split("|"):
        try:
            v = float(p.strip())
            if v >= floor:
                vals.append(v)
        except ValueError:
            pass
    return min(vals) if vals else None


def load_merged(fx: dict[str, float] | None = None) -> pd.DataFrame:
    gbp = float((fx or {}).get("GBP_EUR", GBP_EUR))
    sek = float((fx or {}).get("SEK_EUR", SEK_EUR))
    loaded = {}
    url_cols = {"AD_UK": "Autodoc_URL", "MEK": "MEK_URL", "KS_AM": "KS_URL", "KS_GEN": "KS_URL"}
    for key, fname, min_col, all_col, brand_col, fx in SITES:
        p = SCRIPT_DIR / fname
        if not p.exists():
            continue
        df = pd.read_csv(p, dtype={"PN": str}, low_memory=False)
        df["PN"] = df["PN"].astype(str).str.zfill(10)
        if all_col and all_col in df.columns:
            df[min_col] = df[all_col].apply(_clean_min)
        elif min_col in df.columns:
            df[min_col] = pd.to_numeric(df[min_col], errors="coerce")
            df.loc[df[min_col] < 3, min_col] = np.nan
        rename = {}
        if min_col in df.columns:
            rename[min_col] = f"{key}_min_native"
        if brand_col and brand_col in df.columns:
            rename[brand_col] = f"{key}_brand"
        url_col = url_cols.get(key)
        if url_col and url_col in df.columns:
            rename[url_col] = f"{key}_url"
        df = df.rename(columns=rename)
        keep = ["PN"] + list(rename.values())
        if key == "AD_UK":
            for extra in ("Autodoc_ResultCount", "Autodoc_AllPrices_GBP"):
                if extra in df.columns:
                    keep.append(extra)
        loaded[key] = df[keep].drop_duplicates("PN")

    base_path = SCRIPT_DIR / "autodoc_results.csv"
    if not base_path.exists():
        base_path = HANDOFF / "autodoc_results.csv"
    base = pd.read_csv(base_path, dtype={"PN": str}, low_memory=False)
    base["PN"] = base["PN"].astype(str).str.zfill(10)
    meta = ["PN", "Description", "PR00_EUR", "Rev_CY2025_EUR"]
    for c in ("Qty_CY2025", "Qty_CY2024", "Class", "AIM_Category", "Source", "AIM_DemandType"):
        if c in base.columns:
            meta.append(c)
    merged = base[meta].drop_duplicates("PN")
    for df in loaded.values():
        merged = merged.merge(df, on="PN", how="left")
    for key, _, min_col, _, _, site_fx in SITES:
        nat = f"{key}_min_native"
        eur = f"{key}_min_eur"
        rate = gbp if site_fx == GBP_EUR else sek
        if nat in merged.columns:
            merged[eur] = pd.to_numeric(merged[nat], errors="coerce") * rate
    eur_cols = [c for c in merged.columns if c.endswith("_min_eur")]
    if eur_cols:
        merged["best_price_eur"] = merged[eur_cols].min(axis=1)
        idx = merged[eur_cols].idxmin(axis=1)
        merged["best_site"] = idx.str.replace("_min_eur", "", regex=False)
    return merged


def load_engine_macro(
    cfg: dict,
    paths: dict[str, Path],
    opts: dict[str, Any],
) -> dict | None:
    """Category-level PMS view from handoff engine (no per-PN UIO double-count)."""
    src = opts.get("sources") or {}
    v3_path = src.get("v3") or HANDOFF / "ISZE_Parts_Intelligence_v3.xlsx"
    if not v3_path.exists():
        v3_path = SCRIPT_DIR / "ISZE_Parts_Intelligence_v3.xlsx"
    if not v3_path.exists():
        return None
    try:
        import openpyxl
        from engine import compute_view

        v3 = pd.read_excel(v3_path, sheet_name="PN_Price_Matrix", dtype={"PN": str})
        v3["PN"] = v3["PN"].astype(str).str.zfill(10)
        uio_path = src.get("uio")
        uio_sheets = {}
        if uio_path and Path(uio_path).exists():
            wb = openpyxl.load_workbook(uio_path, read_only=True, data_only=True)
            uio_sheets = {sh: pd.DataFrame(list(wb[sh].values)) for sh in wb.sheetnames}
            wb.close()
        pms_path = src.get("pms_calc")
        pms_sheets = {}
        if pms_path and Path(pms_path).exists():
            wb = openpyxl.load_workbook(pms_path, read_only=True, data_only=True)
            pms_sheets = {sh: pd.DataFrame(list(wb[sh].values)) for sh in wb.sheetnames}
            wb.close()
        scraped = None
        for prefix, fname in [("AD_UK", "autodoc_results.csv"), ("KS", "ks_results.csv"), ("MEK", "mekonomen_results.csv")]:
            p = SCRIPT_DIR / fname
            if not p.exists():
                p = HANDOFF / fname
            if not p.exists():
                continue
            df = pd.read_csv(p, dtype={"PN": str}, low_memory=False)
            df["PN"] = df["PN"].astype(str).str.zfill(10)
            df = df.rename(columns={c: f"{prefix}__{c}" for c in df.columns if c != "PN"})
            scraped = df if scraped is None else scraped.merge(df, on="PN", how="outer")
        if scraped is None:
            scraped = pd.DataFrame()
        basket = opts.get("pms_basket") or "Maintenance + Wear Repair (PMS pilot)"
        return compute_view(
            v3,
            uio_sheets,
            pms_sheets,
            scraped,
            market_scope=opts.get("market_scope", "ITUK (PMS Calc pilot)"),
            isze_gp_pct=float(opts.get("isze_gp_pct", 0.35)),
            horizon_years=float(opts.get("horizon_years", 1.0)),
            pms_basket=basket,
            period_type=str(opts.get("period_type", "CY")),
            sales_year=int(opts.get("sales_year", 2025)),
            cfg=cfg,
            paths=paths,
            pms_data_mode=str(opts.get("pms_data_mode", "auto")),
            ituk_uio_source=str(opts.get("ituk_uio_source", "pms_calc")),
        )
    except Exception as exc:
        return {"error": pd.DataFrame([{"message": str(exc)}])}


def _eur(v) -> str:
    try:
        f = float(v)
        if pd.isna(f):
            return "—"
        return f"€{f:,.0f}" if abs(f) >= 100 else f"€{f:.2f}"
    except (TypeError, ValueError):
        return "—"


def _prism_source_note(pms_mode: pd.DataFrame) -> str:
    try:
        from bi_display import data_mode_banner

        b = data_mode_banner(pms_mode)
        return f'<p class="note observed">{b}</p>' if b else ""
    except ImportError:
        if pms_mode is None or pms_mode.empty:
            return ""
        return f'<p class="note observed">{html.escape(str(pms_mode.iloc[0].to_dict()))}</p>'


def _pms_cat_html(df: pd.DataFrame) -> pd.DataFrame:
    try:
        from bi_display import format_category_table

        return format_category_table(df)
    except ImportError:
        return df.head(12)


def _pms_pn_html(df: pd.DataFrame) -> pd.DataFrame:
    try:
        from bi_display import format_pn_table

        return format_pn_table(df)
    except ImportError:
        return df.head(12)


def _iam_brand_html(df: pd.DataFrame) -> pd.DataFrame:
    try:
        from iam_display import format_brand_league

        return format_brand_league(df)
    except ImportError:
        return df.head(12)


def _iam_pn_html(df: pd.DataFrame, db_gm: float = 0.37, dlr_gm: float = 0.25) -> pd.DataFrame:
    try:
        from iam_display import format_iam_pn

        return format_iam_pn(df)
    except ImportError:
        # 2026-07-09 fix: iam_display.py doesn't exist in this checkout, so this always
        # fell through to a raw df.head(15) — and _df_table() then truncates to the
        # FIRST 7 columns positionally (PN, Description, PR00_EUR, Rev, Qty, Class,
        # AIM_Category). best_price_eur / dealer_workshop_price / quadrant were never
        # reached — this is why the price comparison looked "missing" on this tab.
        # Build a curated, ordered table instead so the important columns survive
        # _df_table's truncation regardless of max_cols.
        d = df.copy()
        if "PR00_EUR" in d.columns:
            d["DLR_est_EUR"] = d["PR00_EUR"] / (1 - db_gm) / (1 - dlr_gm)
        cols = [c for c in [
            "PN", "Description", "PR00_EUR", "DLR_est_EUR", "best_price_eur",
            "primary_threat_brand", "brand_tier", "threat_score", "quality_score", "quadrant",
        ] if c in d.columns]
        d = d[cols].rename(columns={
            "PR00_EUR": "ISZE ASC €", "DLR_est_EUR": "Est. DLR €", "best_price_eur": "Best AM €",
            "primary_threat_brand": "Brand", "brand_tier": "Tier",
            "threat_score": "T", "quality_score": "Q",
        })
        return d.head(15)


def _iam_cat_html(df: pd.DataFrame) -> pd.DataFrame:
    try:
        from iam_display import format_category_concentration

        return format_category_concentration(df)
    except ImportError:
        return df.head(12)


def _prism_html_table(pms_multi: pd.DataFrame) -> pd.DataFrame:
    if pms_multi is None or pms_multi.empty:
        return pms_multi
    try:
        from bi_display import format_prism_summary

        return format_prism_summary(pms_multi)
    except ImportError:
        work = pms_multi.copy()
        if "total_lost_gp" in work.columns:
            return work.sort_values("total_lost_gp", ascending=False)
        return work


def _pct(v, digits=1) -> str:
    try:
        f = float(v)
        if pd.isna(f):
            return "—"
        return f"{f * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return "—"


def _df_table(df: pd.DataFrame, max_rows: int = 15, max_cols: int = 7) -> str:
    if df is None or df.empty:
        return "<p class='empty'>No rows for this view.</p>"
    d = df.head(max_rows).copy()
    if d.shape[1] > max_cols:
        d = d.iloc[:, :max_cols]
    headers = "".join(f"<th>{html.escape(str(c))}</th>" for c in d.columns)
    rows = []
    for _, r in d.iterrows():
        cells = "".join(f"<td>{html.escape(_fmt_cell(r[c]))}</td>" for c in d.columns)
        rows.append(f"<tr>{cells}</tr>")
    return f"<table class='data'><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def _fmt_cell(v) -> str:
    if isinstance(v, float):
        if pd.isna(v):
            return "—"
        if abs(v) >= 1000:
            return f"{v:,.0f}"
        if abs(v) < 10:
            return f"{v:.2f}"
        return f"{v:,.1f}"
    return str(v) if pd.notna(v) else "—"


def build_narrative(scored: pd.DataFrame, engine: dict | None, meta: dict, opts: dict[str, Any]) -> list[dict]:
    """Sourced sentences only — no free-form generation."""
    lines: list[dict] = []

    def add(text: str, source: str, kind: str):
        lines.append({"text": text, "source": source, "kind": kind})

    add(
        "This dashboard shows three metric families. They are not interchangeable: "
        "use PMS Lost GP for service-part leakage, Threat/Quality for IAM pricing pressure on scraped PNs, "
        "and Expected Loss only where no PMS interval exists.",
        "Dashboard design",
        "guide",
    )

    if engine and "Summary KPIs" in engine and not engine["Summary KPIs"].empty:
        k = engine["Summary KPIs"].iloc[0]
        add(
            f"PMS macro ({k.get('scope_label', 'scope')}): UIO scope {int(k.get('total_uio', 0)):,} vehicles · "
            f"{int(k.get('pms_pns', 0))} mapped PNs · lost ISZE GP {_eur(k.get('total_lost_gp'))}/yr · "
            f"capture {_pct(k.get('overall_capture_rate'))}.",
            "engine.compute_view → Summary KPIs",
            "observed",
        )
        if "Category lost sales" in engine and not engine["Category lost sales"].empty:
            top = engine["Category lost sales"].iloc[0]
            add(
                f"Largest category leak: {top['category']} — lost GP {_eur(top['lost_isze_gp'])} "
                f"at {_pct(top['capture_rate'])} capture.",
                "engine.compute_view → Category lost sales (row 1 by lost_isze_gp)",
                "observed",
            )
        src_actual = str(k.get("actual_data_source", ""))
        if "dealer sales" in src_actual:
            add(
                f"ITUK actuals: {src_actual} (distributor file, not pan-ISZE v3 qty).",
                "sources_loader.load_ituk_dealer_sales",
                "observed",
            )
        else:
            add(
                "ITUK actuals may still use pan-ISZE v3 qty unless Sales to Dealers_ITUK file is present — see sources.yaml.",
                "sources.yaml / SPEC.md",
                "caution",
            )
        ituk_src = k.get("ituk_uio_source")
        if ituk_src:
            add(
                f"ITUK UIO basis for this build: {ituk_src} → scope label «{k.get('scope_label', '')}».",
                "engine.resolve_uio_scope",
                "observed",
            )
        if str(ituk_src) in ("v17_survival", "cohort_survival"):
            add(
                "Sheet 1 is cohort survival math across distributors — not the 2024 SMMT ITUK car park (~22,389). "
                "Use smmt_car_park for PRISM / All distributors alignment.",
                "current UIO workbook, sheet 4 vs sheet 1 / SPEC.md",
                "caution",
            )
        if str(ituk_src) == "smmt_car_park":
            add(
                "SMMT car park (~22,389 for 2024A) matches PRISM All distributors ITUK uio_units — Duncan/SMMT via ITUK, sheet 4.",
                "current UIO workbook «4. ITUK UIO Projection» / PRISM derived",
                "observed",
            )
    elif engine and "error" in engine:
        add(f"Engine macro block unavailable: {engine['error'].iloc[0]['message']}.", "engine.py", "caution")
    else:
        add("Engine macro block not loaded (missing v3 or PMS Calc path).", "build_executive_dashboard.py", "caution")

    total = len(scored)
    with_am = int(scored["best_price_eur"].notna().sum()) if "best_price_eur" in scored.columns else 0
    add(
        f"Scrape panel: {total} PNs in autodoc_results base · {with_am} with at least one AM price "
        f"({with_am / total * 100:.0f}% coverage)." if total else "Scrape panel empty.",
        "Merged autodoc_results.csv + ks + mek",
        "scraped",
    )

    if "quadrant" in scored.columns:
        counts = scored["quadrant"].value_counts().to_dict()
        add(
            f"IAM matrix: {counts.get('Dangerous', 0)} Dangerous · {counts.get('Nuisance', 0)} Nuisance · "
            f"{counts.get('Watch', 0)} Watch · {counts.get('Ignore', 0)} Ignore "
            f"(T≥50 and Q≥50 thresholds from iam_scoring.py).",
            "iam_scoring.compute_scores",
            "lookup",
        )

    el = float(scored["expected_loss"].sum()) if "expected_loss" in scored.columns else 0
    add(
        f"Substitution-model expected loss (breakdown PNs): {_eur(el)} total across scraped set — "
        f"cells from substitution_probability.csv × Rev_CY2025 × {opts.get('isze_gp_pct', 0.35)*100:.0f}% GP.",
        "iam_scoring.compute_expected_loss",
        "lookup",
    )

    add(
        "We do not invent: survival rates, brand tiers, P(sub) cells, or UIO counts — each is read from "
        "the file named in the Methodology tab or labeled on the chart.",
        "Handoff README / SPEC.md",
        "guide",
    )
    return lines


def category_bar_div(cat_df: pd.DataFrame) -> str:
    if cat_df is None or cat_df.empty:
        return "<p class='empty'>No category data.</p>"
    try:
        import plotly.express as px

        d = cat_df.sort_values("lost_isze_gp", ascending=True).copy()
        d["capture_pct"] = d["capture_rate"] * 100
        fig = px.bar(
            d,
            y="category",
            x="lost_isze_gp",
            orientation="h",
            color="capture_pct",
            color_continuous_scale=["#8b1a2e", "#c05010", "#0a6644"],
            labels={"lost_isze_gp": "Lost ISZE GP €", "capture_pct": "Capture %"},
        )
        fig.update_layout(height=max(320, len(d) * 36), margin=dict(l=10, r=10, t=20, b=20),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        return fig.to_html(full_html=False, include_plotlyjs=False)
    except Exception:
        return _df_table(cat_df)


IML_V7_YAML = SCRIPT_DIR.parent.parent / "03_analytics" / "Isuzu" / "prism" / "data" / "iml_v7_ituk_cy2025.yaml"


def pms_iam_bridge(scored: pd.DataFrame, yaml_path: Path = IML_V7_YAML) -> tuple[pd.DataFrame, str]:
    """
    Cross-reference the validated ITUK PMS gap (IML v7 / Model B — the ONLY figures
    cleared for IML/ITUK use) against IAM threat/quality quadrants for scraped PNs in
    the same category.

    Deliberately NOT additive with PMS € — see iam_banner / prism_banner in build_html.
    This answers a different question: "of this category's PMS gap, how much of it looks
    like genuine price/quality-driven substitution (Dangerous+Nuisance) vs a gap with no
    real competitive signal in our scrape (Watch+Ignore, or too few PNs to say)?" A gap
    with no substitution signal is more likely a process/EQ-HIT/ordering gap than a price gap.

    Returns (table, note). Table is empty if the yaml can't be loaded (missing pyyaml or file).
    """
    try:
        import yaml
    except ImportError:
        return pd.DataFrame(), "pyyaml not installed — cannot load iml_v7_ituk_cy2025.yaml. `pip install pyyaml`."
    if not yaml_path.exists():
        return pd.DataFrame(), f"Not found: {yaml_path}"

    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    cats = {c["key"]: c for c in doc.get("categories", [])}

    rows = []
    for key, label, pattern in PMS_BRIDGE_CATEGORIES:
        pms = cats.get(key, {})
        gap_eur = pms.get("revenue_gap_eur")
        cover_pct = pms.get("cover_pct")
        mask = scored["Description"].astype(str).str.contains(pattern, case=False, na=False, regex=True)
        sub = scored[mask]
        n = len(sub)
        qc = sub["quadrant"].value_counts().to_dict() if n else {}
        real_threat_n = qc.get("Dangerous", 0) + qc.get("Nuisance", 0)
        real_threat_pct = (real_threat_n / n * 100) if n else None
        top_brands = [b for b in sub.get("primary_threat_brand", pd.Series(dtype=str)).dropna().unique().tolist() if b][:4]
        # Price-gap magnitude (killer feature #2): counts alone don't say how big the
        # gap is. avg/max _ratio = dealer_workshop_price / best_price_eur per matched PN.
        ratios = pd.to_numeric(sub["_ratio"], errors="coerce").dropna() if n and "_ratio" in sub.columns else pd.Series(dtype=float)
        avg_ratio = float(ratios.mean()) if len(ratios) else None
        max_ratio = float(ratios.max()) if len(ratios) else None
        if n == 0:
            read = "No scraped PNs in this category — no signal either way"
        elif n < 5:
            read = f"Thin sample (n={n}) — directional only"
        elif real_threat_pct >= 70:
            read = "Likely price/quality-driven — genuine substitution competition"
        elif real_threat_pct <= 40:
            read = "Weak substitution signal — more likely a process/awareness gap (EQ-HIT)"
        else:
            read = "Mixed — some real competition, some not"
        # Recommended action (killer feature #1): same n / real_threat_pct rule as
        # `read`, phrased as a next step rather than a description.
        if n == 0:
            action = "No coverage"
        elif n < 5:
            action = "Directional only"
        elif real_threat_pct >= 70:
            action = "Attack — price/quality play"
        elif real_threat_pct <= 40:
            action = "Fix process — price move won't help"
        else:
            action = "Investigate — mixed signal"
        rows.append({
            "PMS category": label,
            "PMS gap €/yr (Model B, ITUK)": gap_eur,
            "Avg price gap (x)": avg_ratio,
            "Max price gap (x)": max_ratio,
            "Cover %": cover_pct,
            "Scraped PNs matched": n,
            "Dangerous": qc.get("Dangerous", 0),
            "Nuisance": qc.get("Nuisance", 0),
            "Watch": qc.get("Watch", 0),
            "Ignore": qc.get("Ignore", 0),
            "Real-threat %": real_threat_pct,
            "Top competing brands": ", ".join(top_brands) if top_brands else "—",
            "Action": action,
            "Read": read,
        })
    df = pd.DataFrame(rows)
    # Priority (killer feature #1): rank by PMS gap size — the magnitude axis — so the
    # table reads top-to-bottom as "what to look at first." Action (above) is the
    # separate qualitative axis (is it price-driven or not); the two are NOT combined
    # into one score — that would imply a false precision neither model supports.
    if not df.empty:
        df = df.sort_values("PMS gap €/yr (Model B, ITUK)", ascending=False, na_position="last").reset_index(drop=True)
        df.insert(0, "Priority", df.index + 1)
    note = f"Source: {yaml_path.name} (Model B, adopted 2026-07-02) × iam_scoring.py on {len(scored)} scraped PNs."
    return df, note


def _fmt_ratio(v) -> str:
    try:
        f = float(v)
        if pd.isna(f):
            return "—"
        return f"{f:.1f}x"
    except (TypeError, ValueError):
        return "—"


def pms_iam_bridge_html(scored: pd.DataFrame) -> str:
    df, note = pms_iam_bridge(scored)
    if df.empty:
        return f"<p class='empty'>{html.escape(note)}</p>"

    action_class = {
        "Attack — price/quality play": "action-attack",
        "Fix process — price move won't help": "action-process",
        "Investigate — mixed signal": "action-mixed",
        "Directional only": "action-thin",
        "No coverage": "action-none",
    }

    def fmt_row(r):
        gap = _eur(r["PMS gap €/yr (Model B, ITUK)"])
        cover = _pct(r["Cover %"] / 100 if pd.notna(r["Cover %"]) else None)
        rt = f"{r['Real-threat %']:.0f}%" if pd.notna(r["Real-threat %"]) else "—"
        avg_gap = _fmt_ratio(r["Avg price gap (x)"])
        max_gap = _fmt_ratio(r["Max price gap (x)"])
        act = str(r["Action"])
        act_cls = action_class.get(act, "")
        return (
            f"<tr><td>{int(r['Priority'])}</td>"
            f"<td><strong>{html.escape(str(r['PMS category']))}</strong></td>"
            f"<td>{gap}</td><td>{avg_gap}</td><td>{max_gap}</td>"
            f"<td>{cover}</td><td>{int(r['Scraped PNs matched'])}</td>"
            f"<td>{int(r['Dangerous'])}</td><td>{int(r['Nuisance'])}</td>"
            f"<td>{int(r['Watch'])}</td><td>{int(r['Ignore'])}</td>"
            f"<td>{rt}</td><td>{html.escape(str(r['Top competing brands']))}</td>"
            f"<td><strong class='{act_cls}'>{html.escape(act)}</strong>"
            f"<br><span class='sub-note'>{html.escape(str(r['Read']))}</span></td></tr>"
        )

    rows_html = "".join(fmt_row(r) for _, r in df.iterrows())
    return f"""
    <p class="note caution"><strong>Two different lenses — do not add these euros together.</strong>
    PMS gap € (Model B) and IAM threat/quality scores use different UIO/demand methodologies
    (see banners on "Read first"). <strong>Priority</strong> ranks rows by PMS gap size only
    (the magnitude axis) — it is NOT a combined score with the threat/quality read. <strong>Action</strong>
    is the separate qualitative axis: does the size of the gap actually line up with real AM
    competitive pressure, or not? Avg/Max price gap = dealer workshop price ÷ cheapest AM price
    across the category's matched PNs (1.0x = no gap).</p>
    <table class="data"><thead><tr>
      <th>#</th><th>PMS category</th><th>PMS gap €/yr</th><th>Avg gap</th><th>Max gap</th>
      <th>Cover %</th><th>PNs matched</th>
      <th>Dangerous</th><th>Nuisance</th><th>Watch</th><th>Ignore</th>
      <th>Real-threat %</th><th>Top competing brands</th><th>Action</th>
    </tr></thead><tbody>{rows_html}</tbody></table>
    <p class="sub-note">{html.escape(note)}</p>
    """


# ── Generalized PMS x scraped-price bridge for non-ITUK distributors ──────────
# Built 2026-07-10 to extend pms_iam_bridge() beyond ITUK. NOT the same depth:
# pms_iam_bridge() has full T(hreat)/Q(uality) quadrant scoring from iam_scoring.py,
# which needs a brand-tier table built for UK aftermarket brands only. No brand-tier
# data exists for other markets, so this reports a lighter signal instead: PMS gap €
# (from the same multi-DB PRISM file used by the "All distributors" tab) next to
# scraped AM price level for that category. It answers "is there a price gap at all",
# NOT "is it brand/quality-driven" — don't present it as equivalent to the ITUK read.
PRISM_CSV_PATH = SCRIPT_DIR.parent.parent / "01_data" / "00_derived" / "pms_capture_by_db_year.csv"

# PRISM's finer categories rolled up to the 5 coarse PMS_BRIDGE_CATEGORIES keys.
# urea_filter/blower_filter/release_bearing/pilot_bearing have no coarse-category
# home and are deliberately dropped, not force-merged into a misleading bucket.
PRISM_TO_COARSE_CATEGORY = {
    "oil_filter": "oil_filter", "fuel_filter": "fuel_filter", "air_filter": "air_filter",
    "brake_pad": "brake", "brake_shoe": "brake", "brake_rotor": "brake",
    "clutch_disc": "clutch", "clutch_pressure_plate": "clutch", "clutch_kit": "clutch",
    "clutch_booster": "clutch",
}


def pms_scrape_bridge(distributor_code: str, scraped_csv: Path, prism_csv: Path = PRISM_CSV_PATH) -> tuple[pd.DataFrame, str]:
    if not prism_csv.exists():
        return pd.DataFrame(), f"Not found: {prism_csv}"
    if not scraped_csv.exists():
        return pd.DataFrame(), f"Not found: {scraped_csv}"

    prism = pd.read_csv(prism_csv)
    dist = prism[(prism["distributor_code"] == distributor_code) & (prism["line_type"] == "total")].copy()
    if dist.empty:
        return pd.DataFrame(), f"No PRISM rows for distributor_code={distributor_code} in {prism_csv.name}"
    dist["coarse_category"] = dist["pms_category"].map(PRISM_TO_COARSE_CATEGORY)
    dist = dist.dropna(subset=["coarse_category"])
    gap_by_cat = dist.groupby("coarse_category")["revenue_gap_eur"].sum()

    def _cover(g):
        exp = g["expected_qty"].sum()
        return (g["actual_qty"].sum() / exp * 100) if exp > 0 else None
    cover_by_cat = dist.groupby("coarse_category").apply(_cover, include_groups=False)

    scraped = pd.read_csv(scraped_csv)
    if "PMS_Category" not in scraped.columns:
        return pd.DataFrame(), f"{scraped_csv.name} has no PMS_Category column"

    rows = []
    for key, label, _pattern in PMS_BRIDGE_CATEGORIES:
        sub = scraped[scraped["PMS_Category"] == key]
        n = len(sub)
        rows.append({
            "PMS category": label,
            "PMS gap €/yr": gap_by_cat.get(key),
            "Cover %": cover_by_cat.get(key),
            "Scraped products": n,
            "Avg AM price (EUR)": sub["Price_EUR"].mean() if n else None,
            "Min AM price (EUR)": sub["Price_EUR"].min() if n else None,
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("PMS gap €/yr", ascending=False, na_position="last").reset_index(drop=True)
        df.insert(0, "Priority", df.index + 1)
    note = (f"Source: {prism_csv.name} (distributor_code={distributor_code}, line_type=total) x "
            f"{scraped_csv.name} — category-level only, no brand-tier/quadrant scoring (see code comment).")
    return df, note


def pms_scrape_bridge_html(distributor_code: str, scraped_csv: Path, section_label: str) -> str:
    df, note = pms_scrape_bridge(distributor_code, scraped_csv)
    if df.empty:
        return f"<h3>{html.escape(section_label)}</h3><p class='empty'>{html.escape(note)}</p>"
    if int(df["Scraped products"].sum()) == 0:
        # 2026-07-10: auto365.co.il (Israel) verified via its own site search to stock
        # zero oil/fuel/air filters, brakes, or clutch parts for anything — a lighting/
        # mirrors/body-parts/accessories retailer, wrong site for this bridge. A
        # permanently-empty-but-present table reads as "checked, found nothing";
        # the honest state is "no working scraped competitor source for this market
        # yet" — say that instead of a misleading zero-filled table.
        return (
            f"<h3>{html.escape(section_label)}</h3>"
            f"<p class='note caution'>PMS gap € data exists for {html.escape(distributor_code)} "
            "(see PMS gap €/yr in the table this replaces), but no scraped competitor-price source "
            "has been found for this market yet — the site originally tried "
            f"(<code>{html.escape(scraped_csv.name)}</code>) doesn't stock PMS-category parts "
            "(verified via its own site search). Not shown as a zero-match table to avoid implying "
            "the check came back negative.</p>"
        )

    def fmt_row(r):
        gap = _eur(r["PMS gap €/yr"])
        cover = _pct(r["Cover %"] / 100 if pd.notna(r["Cover %"]) else None)
        avg_p = _eur(r["Avg AM price (EUR)"])
        min_p = _eur(r["Min AM price (EUR)"])
        return (
            f"<tr><td>{int(r['Priority'])}</td><td><strong>{html.escape(str(r['PMS category']))}</strong></td>"
            f"<td>{gap}</td><td>{cover}</td><td>{int(r['Scraped products'])}</td>"
            f"<td>{avg_p}</td><td>{min_p}</td></tr>"
        )

    rows_html = "".join(fmt_row(r) for _, r in df.iterrows())
    return f"""
    <h3>{html.escape(section_label)}</h3>
    <p class="note caution">Lighter signal than the ITUK bridge above — no brand-tier/quality
    scoring exists for this market yet, just PMS gap € next to scraped AM price level.</p>
    <table class="data"><thead><tr>
      <th>#</th><th>PMS category</th><th>PMS gap €/yr</th><th>Cover %</th>
      <th>Scraped products</th><th>Avg AM price</th><th>Min AM price</th>
    </tr></thead><tbody>{rows_html}</tbody></table>
    <p class="sub-note">{html.escape(note)}</p>
    """


# ── Warranty overlay (roadmap item 4, started 2026-07-10) ─────────────────────
# Real per-category warranty claim data from PRISM's warranty_raw_grain.csv (real
# claim-level data: part_no, part_desc, qty, claim_eur per distributor per year —
# see WARRANTY_KAPSTOK.md). Classified into the same 5 coarse PMS_BRIDGE_CATEGORIES
# keys via the same keyword patterns already used for the PMS bridge. Purpose: a
# "lost sale" flagged by the PMS gap could actually be a part replaced under
# warranty, not aftermarket defection — this shows how much warranty claim volume
# exists in each category so that distinction is visible, not assumed away.
WARRANTY_CSV_PATH = SCRIPT_DIR.parent.parent / "01_data" / "00_derived" / "warranty_raw_grain.csv"


def warranty_by_pms_category(distributor_code: str, warranty_csv: Path = WARRANTY_CSV_PATH, year: int | None = None) -> tuple[pd.DataFrame, str]:
    if not warranty_csv.exists():
        return pd.DataFrame(), f"Not found: {warranty_csv}"
    df = pd.read_csv(warranty_csv)
    df = df[df["db_name"] == distributor_code]
    if year is not None and "year" in df.columns:
        df = df[df["year"] == year]
    if df.empty:
        return pd.DataFrame(), f"No warranty rows for db_name={distributor_code}" + (f", year={year}" if year else "")

    rows = []
    for key, label, pattern in PMS_BRIDGE_CATEGORIES:
        mask = df["part_desc"].astype(str).str.contains(pattern, case=False, na=False, regex=True)
        sub = df[mask]
        rows.append({
            "PMS category": label,
            "Warranty claims (n)": len(sub),
            "Warranty qty": sub["qty"].sum() if len(sub) else 0,
            "Warranty claim €": sub["claim_eur"].sum() if len(sub) else 0.0,
        })
    note = (f"Source: {warranty_csv.name} (db_name={distributor_code}"
            + (f", year={year}" if year else ", all years")
            + f") — claim-price basis, ISZE-net equiv ~×0.74 (see WARRANTY_KAPSTOK.md).")
    return pd.DataFrame(rows), note


def warranty_by_pms_category_html(distributor_code: str, year: int | None = None) -> str:
    df, note = warranty_by_pms_category(distributor_code, year=year)
    if df.empty:
        return f"<p class='empty'>{html.escape(note)}</p>"

    def fmt_row(r):
        return (
            f"<tr><td><strong>{html.escape(str(r['PMS category']))}</strong></td>"
            f"<td>{int(r['Warranty claims (n)'])}</td><td>{r['Warranty qty']:,.0f}</td>"
            f"<td>{_eur(r['Warranty claim €'])}</td></tr>"
        )

    rows_html = "".join(fmt_row(r) for _, r in df.iterrows())
    return f"""
    <h4>Warranty overlay — {html.escape(distributor_code)}</h4>
    <p class="note lookup">A part replaced under warranty is a quality/defect event, not aftermarket
    defection — high warranty volume in a category is a reason the PMS gap there might be smaller
    (or differently caused) than it looks. Claim-price basis, not directly additive with PMS gap €
    (different basis — see note).</p>
    <table class="data"><thead><tr>
      <th>PMS category</th><th>Claims (n)</th><th>Qty</th><th>Warranty claim €</th>
    </tr></thead><tbody>{rows_html}</tbody></table>
    <p class="sub-note">{html.escape(note)}</p>
    """


# ── Price-match simulator (roadmap item 5, started 2026-07-10) ────────────────
# For Dangerous-quadrant PNs (real threat + credible brand): what would matching
# the scraped AM price cost in margin, vs the expected-loss it avoids? Uses
# substitution_probability.csv's own "<1.0" bucket (p_substitution=0.00 for every
# brand tier — see the CSV) as "matched price -> substitution risk drops to 0" —
# not a new assumption, just the already-built model evaluated at ratio=1.0.
def price_match_simulator(scored: pd.DataFrame, *, db_gm: float = 0.37, dlr_gm: float = 0.25, top_n: int = 15) -> tuple[pd.DataFrame, str]:
    total_dangerous = int((scored["quadrant"] == "Dangerous").sum()) if "quadrant" in scored.columns else 0
    d = scored[scored["quadrant"] == "Dangerous"].copy() if "quadrant" in scored.columns else pd.DataFrame()
    if d.empty:
        return pd.DataFrame(), "No PNs in the Dangerous quadrant."

    d["current_PR00"] = pd.to_numeric(d["PR00_EUR"], errors="coerce")
    d["matched_PR00"] = pd.to_numeric(d["best_price_eur"], errors="coerce") * (1 - db_gm) * (1 - dlr_gm)
    d["qty"] = pd.to_numeric(d.get("Qty_CY2025"), errors="coerce").fillna(0)
    d["margin_cost_eur"] = ((d["current_PR00"] - d["matched_PR00"]).clip(lower=0) * d["qty"]).round(0)
    d["expected_loss_avoided_eur"] = pd.to_numeric(d.get("expected_loss"), errors="coerce").fillna(0).round(0)
    d["net_eur"] = d["expected_loss_avoided_eur"] - d["margin_cost_eur"]
    d["recommendation"] = d["net_eur"].apply(lambda v: "Match" if v > 0 else "Don't match")

    d = d.sort_values("expected_loss_avoided_eur", ascending=False).head(top_n)
    cols = ["PN", "Description", "primary_threat_brand", "brand_tier", "current_PR00", "matched_PR00",
            "margin_cost_eur", "expected_loss_avoided_eur", "net_eur", "recommendation"]
    out = d[[c for c in cols if c in d.columns]].copy()
    note = (f"Dangerous-quadrant PNs only (n={total_dangerous} total, top {len(out)} shown by expected "
            f"loss avoided). Matched PR00 assumes DB {db_gm*100:.0f}%/DLR {dlr_gm*100:.0f}% markup "
            "(Scenario lab assumption, reversed — same caveat: not confirmed SPA terms). Margin cost "
            "uses CURRENT Qty_CY2025 only — does not model volume recovered by matching, which would "
            "make 'Match' look better than shown here; this is the conservative, worst-case-for-"
            "matching estimate, not a full elasticity model.")
    return out, note


def price_match_simulator_html(scored: pd.DataFrame, db_gm: float, dlr_gm: float) -> str:
    df, note = price_match_simulator(scored, db_gm=db_gm, dlr_gm=dlr_gm)
    if df.empty:
        return f"<p class='empty'>{html.escape(note)}</p>"

    rec_class = {"Match": "action-attack", "Don't match": "action-process"}

    def fmt_row(r):
        brand = html.escape(str(r.get("primary_threat_brand", "") or "—"))
        tier = int(r["brand_tier"]) if pd.notna(r.get("brand_tier")) else "—"
        rec = str(r["recommendation"])
        cls = rec_class.get(rec, "")
        return (
            f"<tr><td>{html.escape(str(r.get('PN','')))}</td>"
            f"<td>{html.escape(str(r.get('Description',''))[:40])}</td>"
            f"<td>{brand} (T{tier})</td>"
            f"<td>{_eur(r['current_PR00'])}</td><td>{_eur(r['matched_PR00'])}</td>"
            f"<td>{_eur(r['margin_cost_eur'])}</td><td>{_eur(r['expected_loss_avoided_eur'])}</td>"
            f"<td>{_eur(r['net_eur'])}</td>"
            f"<td><strong class='{cls}'>{html.escape(rec)}</strong></td></tr>"
        )

    rows_html = "".join(fmt_row(r) for _, r in df.iterrows())
    return f"""
    <p class="note caution">Simulates matching PR00 to the scraped AM price for each Dangerous-quadrant
    PN — margin given up vs. expected loss avoided (substitution risk model, evaluated at the matched
    price). Conservative: assumes no volume recovery from matching. Not a recommendation to act on
    without confirming real channel margins — see note below the table.</p>
    <table class="data"><thead><tr>
      <th>PN</th><th>Description</th><th>Top AM brand</th><th>Current PR00</th><th>Matched PR00</th>
      <th>Margin cost</th><th>Loss avoided</th><th>Net €</th><th>Recommendation</th>
    </tr></thead><tbody>{rows_html}</tbody></table>
    <p class="sub-note">{html.escape(note)}</p>
    """


def build_html(
    scored: pd.DataFrame,
    engine: dict | None,
    meta: dict,
    opts: dict[str, Any],
    *,
    variant: str = "full",
) -> str:
    variant = (variant or "full").lower()
    ts = datetime.now().strftime("%d %B %Y · %H:%M")
    narrative = build_narrative(scored, engine, meta, opts)
    src = opts.get("sources") or {}
    fx = opts.get("fx") or {"GBP_EUR": GBP_EUR, "SEK_EUR": SEK_EUR}
    gbp_eur = float(fx.get("GBP_EUR", GBP_EUR))
    sek_eur = float(fx.get("SEK_EUR", SEK_EUR))

    prism_banner = """
    <p class="note caution"><strong>PRISM vs engine:</strong> ITUK tab <code>potential_units</code> uses PMS Calc whole-fleet frequencies.
    All distributors <code>expected_qty</code> is usually <strong>N75_only</strong> in PRISM CSV — do not compare (e.g. oil filter ~15× gap).</p>
    """
    iam_banner = """
    <p class="note lookup"><strong>IAM / LOOKUP views only.</strong> T, Q, expected loss, and verdicts use
    <code>iam_scoring.py</code>, <code>iam_brand_tiers.csv</code>, <code>substitution_probability.csv</code> —
    not validated for PMS leakage or ITUK correspondence. Use <code>isze_executive_pms.html</code> for PMS claims.</p>
    """
    full_banner = prism_banner + iam_banner + """
    <p class="note guide">Outputs: <code>isze_executive_pms.html</code> (engine only) ·
    <code>isze_executive_iam.html</code> (lookup lab) · this file (combined).</p>
    """

    validation_banner = ""
    try:
        from pms_validation import format_capture_pct, validate_engine_result

        if engine:
            vdf = validate_engine_result(engine)
            # 2026-07-09 fix: this used to filter to severity=="error" only, so the
            # 165% category-capture bug (raised as "warn", since the *aggregate* was a
            # sane 31.6%) was computed but never shown anywhere. Show warn too.
            flagged = vdf[vdf["severity"].isin(["error", "warn"])] if not vdf.empty else pd.DataFrame()
            if not flagged.empty:
                has_error = (flagged["severity"] == "error").any()
                css_class = "caution" if has_error else "lookup"
                validation_banner = (
                    f'<p class="note {css_class}"><strong>Data checks:</strong> '
                    + html.escape(" · ".join(flagged["message"].astype(str).tolist()))
                    + "</p>"
                )
    except ImportError:
        format_capture_pct = None  # type: ignore

    kpi_pms_lost = kpi_capture = kpi_uio = kpi_coverage = "—"
    if engine and "Summary KPIs" in engine and not engine.get("Summary KPIs", pd.DataFrame()).empty:
        k = engine["Summary KPIs"].iloc[0]
        kpi_pms_lost = _eur(k.get("total_lost_gp"))
        if format_capture_pct:
            kpi_capture = format_capture_pct(k.get("overall_capture_rate"))
        else:
            kpi_capture = _pct(k.get("overall_capture_rate"))
        kpi_uio = f"{int(k.get('total_uio', 0)):,}"

    total_pns = len(scored)
    cov = scored["best_price_eur"].notna().sum() if "best_price_eur" in scored.columns else 0
    kpi_coverage = f"{cov / total_pns * 100:.0f}%" if total_pns else "—"

    qcounts = scored["quadrant"].value_counts().to_dict() if "quadrant" in scored.columns else {}
    bl = brand_league(scored).head(15)
    cat_conc = category_concentration(scored).head(20)
    dq = data_quality_report(SCRIPT_DIR)

    pms_cat = engine.get("Category lost sales", pd.DataFrame()) if engine else pd.DataFrame()
    pms_pn = engine.get("PN drill-down", pd.DataFrame()) if engine else pd.DataFrame()
    eng_brands = engine.get("Brand league", pd.DataFrame()) if engine else pd.DataFrame()
    pms_multi = engine.get("PMS by distributor (summary)", pd.DataFrame()) if engine else pd.DataFrame()
    pms_mode = engine.get("data_mode", pd.DataFrame()) if engine else pd.DataFrame()
    scope_label = ""
    if engine and "Summary KPIs" in engine and not engine["Summary KPIs"].empty:
        scope_label = str(engine["Summary KPIs"].iloc[0].get("scope_label", ""))

    pms_scored = scored[scored["pms_category"].notna()].copy() if "pms_category" in scored.columns else pd.DataFrame()
    top_pn = scored.sort_values("expected_loss", ascending=False).head(40) if "expected_loss" in scored.columns else scored.head(40)
    top_pms_pn = pms_pn.sort_values("allocated_lost_gp", ascending=False).head(25) if not pms_pn.empty and "allocated_lost_gp" in pms_pn.columns else pms_scored.sort_values("lost_isze_gp_eur", ascending=False).head(25) if not pms_scored.empty and "lost_isze_gp_eur" in pms_scored.columns else pd.DataFrame()

    narrative_html = "".join(
        f"<li class='narr {n['kind']}'><span class='pill {n['kind']}'>{n['kind'].upper()}</span>"
        f"{html.escape(n['text'])}<span class='src'>{html.escape(n['source'])}</span></li>"
        for n in narrative
    )

    site_rows = []
    for key, fname, *_ in SITES:
        p = SCRIPT_DIR / fname
        exists = p.exists()
        n = len(pd.read_csv(p, dtype={"PN": str})) if exists else 0
        site_rows.append(f"<tr><td>{html.escape(key)}</td><td>{html.escape(fname)}</td>"
                         f"<td>{'✓' if exists else '✗'}</td><td>{n:,}</td></tr>")

    sub_tbl = load_substitution_table()
    sub_df = pd.read_csv(SOURCES["substitution"]) if SOURCES["substitution"].exists() else pd.DataFrame()
    tiers_df = load_brand_tiers()

    explain_banner = {"pms": prism_banner, "iam": iam_banner, "full": full_banner}.get(variant, full_banner)
    explain_lede = {
        "pms": "PMS lost sales and multi-DB capture from engine.py + PRISM derived CSV only.",
        "iam": "Aftermarket threat / substitution lookup views — not for PMS leakage claims.",
        "full": "Combined build — read banners before citing any number.",
    }.get(variant, "")

    cockpit_pms = f"""
        {validation_banner}
        <div class="kpi-row">
          <div class="kpi"><div class="lbl">PMS Lost ISZE GP/yr</div><div class="val">{kpi_pms_lost}</div><div class="sub">Category-level · engine</div></div>
          <div class="kpi"><div class="lbl">PMS capture</div><div class="val">{kpi_capture}</div><div class="sub">{html.escape(scope_label or '')}</div></div>
          <div class="kpi"><div class="lbl">UIO scope</div><div class="val">{kpi_uio}</div><div class="sub">ITUK engine tab basis</div></div>
          <div class="kpi"><div class="lbl">AM scrape coverage</div><div class="val">{kpi_coverage}</div><div class="sub">{cov:,} / {total_pns:,} PNs</div></div>
        </div>"""

    # 2026-07-09 addition: Jerome couldn't see genuine-vs-AM prices or the DB/DLR margin
    # assumptions anywhere on the IAM cockpit — the "scenario" tab with the margin table
    # existed but wasn't included in the iam-only build, and no view showed the price
    # ladder itself. Both fixed here.
    _db_gm = float(opts.get('db_gm', 0.37))
    _dlr_gm = float(opts.get('dlr_gm', 0.25))
    _median_pr00 = scored["PR00_EUR"].median() if "PR00_EUR" in scored.columns else None
    _median_db = _median_pr00 / (1 - _db_gm) if _median_pr00 is not None else None
    _median_dlr = _median_db / (1 - _dlr_gm) if _median_db is not None else None
    _median_am = scored["best_price_eur"].median() if "best_price_eur" in scored.columns else None
    _rev_at_risk = scored.loc[scored["quadrant"] == "Dangerous", "Rev_CY2025_EUR"].sum() if "Rev_CY2025_EUR" in scored.columns else None

    cockpit_iam = f"""
        <div class="kpi-row quad">
          <div class="kpi d"><div class="lbl">Dangerous</div><div class="val">{qcounts.get('Dangerous', 0)}</div><div class="sub">ISZE rev in these PNs: {_eur(_rev_at_risk)}/yr</div></div>
          <div class="kpi n"><div class="lbl">Nuisance</div><div class="val">{qcounts.get('Nuisance', 0)}</div></div>
          <div class="kpi w"><div class="lbl">Watch</div><div class="val">{qcounts.get('Watch', 0)}</div></div>
          <div class="kpi i"><div class="lbl">Ignore</div><div class="val">{qcounts.get('Ignore', 0)}</div></div>
        </div>
        <p class="note lookup">Quadrants from iam_scoring.py — LOOKUP methodology, not PMS engine.
        "ISZE rev in these PNs" is revenue currently sold on Dangerous-quadrant PNs — not revenue already lost.</p>
        <h3>Price ladder (median across {total_pns} scraped PNs)</h3>
        <table class="data"><tbody>
          <tr><td>ISZE ASC (PR00)</td><td>{_eur(_median_pr00)}</td><td class="sub-note">Genuine, ISZE sell price</td></tr>
          <tr><td>Estimated DB resale</td><td>{_eur(_median_db)}</td><td class="sub-note">PR00 ÷ (1 − {_db_gm*100:.0f}% DB margin)</td></tr>
          <tr><td>Estimated DLR/workshop price</td><td>{_eur(_median_dlr)}</td><td class="sub-note">DB price ÷ (1 − {_dlr_gm*100:.0f}% DLR margin) — this is what "dealer_workshop_price" compares against AM</td></tr>
          <tr><td>Cheapest AM price found</td><td>{_eur(_median_am)}</td><td class="sub-note">Best of Autodoc UK / Mekonomen / KS Int'l, {cov} of {total_pns} PNs have a match</td></tr>
        </table>
        <p class="sub-note">DB/DLR margins are assumptions ({_db_gm*100:.0f}% / {_dlr_gm*100:.0f}%), not confirmed SPA terms — no CLI flag for these yet, edit <code>BUILD_OPTS["db_gm"]</code>/<code>["dlr_gm"]</code> in <code>build_executive_dashboard.py</code> if you have better numbers. Full table: "Scenario lab" tab.</p>"""

    cockpit_full = cockpit_pms + f"""
        <div class="kpi-row quad">
          <div class="kpi d"><div class="lbl">Dangerous</div><div class="val">{qcounts.get('Dangerous', 0)}</div></div>
          <div class="kpi n"><div class="lbl">Nuisance</div><div class="val">{qcounts.get('Nuisance', 0)}</div></div>
          <div class="kpi w"><div class="lbl">Watch</div><div class="val">{qcounts.get('Watch', 0)}</div></div>
          <div class="kpi i"><div class="lbl">Ignore</div><div class="val">{qcounts.get('Ignore', 0)}</div></div>
        </div>"""

    cockpit_body = {"pms": cockpit_pms, "iam": cockpit_iam, "full": cockpit_full}.get(variant, cockpit_full)

    sections = [
        ("explain", "Read first", f"""
        <div class="explain-hero">
          {explain_banner}
          <h2>How to read this dashboard</h2>
          <p class="lede">{explain_lede}</p>
          <div class="legend">
            <span class="pill observed">OBSERVED</span> UIO × interval math from Excel sources
            <span class="pill lookup">LOOKUP</span> T/Q scores &amp; P(sub) from CSV tables you can edit
            <span class="pill scraped">SCRAPED</span> Live AM prices from CSV scrapers only
            <span class="pill caution">CAUTION</span> Known scope mismatch — read before acting
          </div>
          <ul class="narrative">{narrative_html}</ul>
          <div class="glossary">
            <h3>Glossary</h3>
            <dl>
              <dt>T (Threat)</dt><dd>0–100 from price-gap bucket: dealer workshop ÷ cheapest AM. Source: <code>iam_scoring.py</code> + scrape.</dd>
              <dt>Q (Quality)</dt><dd>0–100 from <code>iam_brand_tiers.csv</code> tier (+25 if OE supplier flag).</dd>
              <dt>Lost ISZE GP</dt><dd>Category-level: max(potential−actual,0) × avg PR00 × GP%. Source: <code>engine.py</code> + PMS Calc.</dd>
              <dt>Expected Loss</dt><dd>Rev_CY2025 × GP% × P(sub) from <code>substitution_probability.csv</code>. Fallback for non-PMS parts.</dd>
              <dt>Rev CY25 bubble size</dt><dd>ISZE revenue sold — <strong>not</strong> revenue at risk (label corrected in this build).</dd>
            </dl>
          </div>
        </div>"""),
        ("cockpit", "Cockpit", cockpit_body),
        ("cockpit_iam", "IAM cockpit", cockpit_iam),
        ("pms", "PMS lost sales", f"""
        <p class="note observed">Category aggregation — one demand pool per PMS category (avoids per-PN UIO double-count).</p>
        {category_bar_div(pms_cat)}
        <h3>Category table</h3>
        {_df_table(_pms_cat_html(pms_cat), 12)}
        <h3>Top PNs (allocated within category)</h3>
        {_df_table(_pms_pn_html(top_pms_pn), 12) if not top_pms_pn.empty else '<p class=empty>No PN rows</p>'}"""),
        ("brands", "Brand league", f"""
        <p class="note lookup">Ranked by substitution-model expected loss on scraped PNs with a named AM brand.</p>
        {_df_table(_iam_brand_html(bl), 12)}"""),
        ("threat", "Threat map", f"""
        <p class="note lookup">Bubble size = Rev_CY2025 (actual ISZE sales). T vs Q from iam_scoring.</p>
        <div class="chart">{_plotly_div(scored)}</div>
        <div class="quads">
          <div><h4>Dangerous</h4><table class="data compact"><thead><tr><th>PN</th><th>Brand</th><th>T</th><th>Q</th></tr></thead><tbody>{_quadrant_table_rows(scored, 'Dangerous', 8)}</tbody></table></div>
          <div><h4>Nuisance</h4><table class="data compact"><thead><tr><th>PN</th><th>Brand</th><th>T</th><th>Q</th></tr></thead><tbody>{_quadrant_table_rows(scored, 'Nuisance', 8)}</tbody></table></div>
        </div>"""),
        ("pn", "PN deep dive", f"""
        {_df_table(_iam_pn_html(top_pn, db_gm=float(opts.get('db_gm', 0.37)), dlr_gm=float(opts.get('dlr_gm', 0.25))), 15, max_cols=10)}"""),
        ("category", "Category heatmap", f"""
        <p class="note lookup">AIM_Category × Class — expected loss from substitution model.</p>
        {_df_table(_iam_cat_html(cat_conc), 12)}"""),
        ("pms_bridge", "PMS × IAM bridge", pms_iam_bridge_html(scored)
            + warranty_by_pms_category_html("ITUK", year=2025)
            + pms_scrape_bridge_html("UTI", SCRIPT_DIR / "auto365_results.csv", "UTI (Israel) — PMS gap × Auto 365 scraped prices")
            + warranty_by_pms_category_html("UTI", year=2025)),
        ("price_sim", "Price-match simulator", price_match_simulator_html(scored, _db_gm, _dlr_gm)),
        ("multidb", "All distributors", f"""
        <p class="note caution"><strong>PRISM scope:</strong> <code>expected_qty</code> is usually <strong>N75_only</strong>. Not comparable to ITUK engine potentials.</p>
        {(_prism_source_note(pms_mode))}
        {_df_table(_prism_html_table(pms_multi), 25)}
        <p class="sub-note">Period {html.escape(str(opts.get('period_type', 'CY')))} · year {int(opts.get('sales_year', 2025))} · multi-DB mode {html.escape(str(opts.get('pms_data_mode', 'auto')))}</p>"""),
        ("scenario", "Scenario lab", f"""
        <p class="note">Build settings (CLI flags or <code>_HANDOFF_BUNDLE/sources.yaml</code> defaults).</p>
        <table class="data"><tbody>
          <tr><td>Market scope</td><td>{html.escape(str(opts.get('market_scope', '')))}</td></tr>
          <tr><td>ITUK UIO basis</td><td>{html.escape(str(opts.get('ituk_uio_source', 'pms_calc')))}</td></tr>
          <tr><td>Period / year</td><td>{html.escape(str(opts.get('period_type', 'CY')))} {int(opts.get('sales_year', 2025))}</td></tr>
          <tr><td>Multi-DB actuals</td><td>{html.escape(str(opts.get('pms_data_mode', 'auto')))}</td></tr>
          <tr><td>Horizon (years)</td><td>{opts.get('horizon_years', 1)}</td></tr>
          <tr><td>ISZE GP %</td><td>{float(opts.get('isze_gp_pct', 0.35))*100:.0f}%</td></tr>
          <tr><td>DB gross margin</td><td>{float(opts.get('db_gm', 0.37))*100:.0f}%</td></tr>
          <tr><td>DLR gross margin</td><td>{float(opts.get('dlr_gm', 0.25))*100:.0f}%</td></tr>
          <tr><td>GBP→EUR</td><td>{gbp_eur} (yaml {html.escape(str(fx.get('as_of', '')))})</td></tr>
          <tr><td>SEK→EUR</td><td>{sek_eur}</td></tr>
        </tbody></table>
        <pre>python build_executive_dashboard.py --variant all --help</pre>"""),
        ("geo", "Geography / sites", f"""
        <table class="data"><thead><tr><th>Site</th><th>CSV</th><th>Present</th><th>Rows</th></tr></thead><tbody>{''.join(site_rows)}</tbody></table>
        <p class="note scraped">Only AD_UK, KS, Mekonomen feed this build. EU/MA/Oscaro scrapers excluded (confirmed empty for Isuzu commercial).</p>"""),
        ("quality", "Data quality", f"""
        {_df_table(dq, 30) if not dq.empty else '<p>Run data_quality_report — see Streamlit tab for full detail.</p>'}"""),
        ("method", "Methodology", f"""
        <h3>Source files on disk</h3>
        <ul class="files">
          <li>Config: <code>{html.escape(str(src.get('sources_yaml', HANDOFF / 'sources.yaml')))}</code></li>
          <li>v3 PN matrix: <code>{html.escape(str(src.get('v3', '')))}</code> — {'exists' if src.get('v3') and Path(src['v3']).exists() else 'MISSING'}</li>
          <li>UIO workbook (always latest — resolves to <code>06_uio/_CURRENT/</code>, unversioned): <code>{html.escape(str(src.get('uio', '')))}</code></li>
          <li>PMS Calc: <code>{html.escape(str(src.get('pms_calc', '')))}</code></li>
          <li>PRISM multi-DB: <code>{html.escape(str(src.get('pms_capture', '')))}</code></li>
          <li>Brand tiers: <code>{html.escape(str(src.get('brand_tiers', '')))}</code></li>
          <li>Substitution: <code>{html.escape(str(src.get('substitution', '')))}</code></li>
        </ul>
        <h3>Substitution table (excerpt)</h3>
        {_df_table(sub_df, 10)}
        <h3>Brand tiers (excerpt)</h3>
        {_df_table(tiers_df.head(12), 12)}
        <h3>Rebuild command</h3>
        <pre>python build_executive_dashboard.py --variant all</pre>"""),
        ("method_iam", "IAM methodology", f"""
        <p class="note lookup">Parent-folder lookup tables — editable but not ISZE-validated. Do not use for PMS or ITUK letters.</p>
        <h3>Substitution table (excerpt)</h3>
        {_df_table(sub_df, 10)}
        <h3>Brand tiers (excerpt)</h3>
        {_df_table(tiers_df.head(12), 12)}
        <p>Source: <code>iam_scoring.py</code> in parent <code>autodoc_scraper/</code></p>"""),
    ]

    if variant == "pms":
        sections = [s for s in sections if s[0] in PMS_SECTIONS]
    elif variant == "iam":
        sections = [s for s in sections if s[0] in IAM_SECTIONS]
    else:
        sections = [s for s in sections if s[0] != "cockpit_iam"]

    meta = {
        "pms": ("ISZE PMS Intelligence", "Executive HTML — engine + PRISM only (layer B)"),
        "iam": ("ISZE IAM Lookup Lab", "Threat / quality lookup — not for PMS claims (layer D)"),
        "full": ("ISZE Combined View", "PMS + IAM in one file — read scope banners per section"),
    }
    h1_title, page_title = meta.get(variant, meta["full"])

    nav = "".join(
        f'<button type="button" class="nav-btn" data-section="{sid}">{label}</button>'
        for sid, label, _ in sections
    )
    panels = "".join(
        f'<section id="sec-{sid}" class="panel{" active" if sid == "explain" else ""}">{body}</section>'
        for sid, label, body in sections
    )

    # 2026-07-09 fix: was <script src="https://cdn.plot.ly/...">. Jerome reported charts
    # "not loading" — the entire page depended on a live CDN fetch for Plotly, which
    # silently fails offline / behind a proxy and breaks every chart at once, including
    # category_bar_div's (include_plotlyjs=False, which assumes this head-level load).
    # Inline the local bundle instead — matches the file's own "self-contained, drop
    # into browser" claim. Falls back to the CDN tag only if the local file is missing.
    _plotly_local = SCRIPT_DIR.parent.parent / "02_dashboards" / "_ui" / "plotly.min.js"
    if _plotly_local.exists():
        plotly_script_tag = f"<script>{_plotly_local.read_text(encoding='utf-8')}</script>"
    else:
        plotly_script_tag = '<script src="https://cdn.plot.ly/plotly-3.4.0.min.js"></script>  <!-- local bundle not found, fell back to CDN -->'

    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(page_title)}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fraunces:ital,opsz,wght@0,9..144,600;0,9..144,800;1,9..144,500&display=swap" rel="stylesheet">
{plotly_script_tag}
<style>
:root {{
  --bg:#0f1419; --card:#1a222d; --text:#e8ecf1; --muted:#8b9cb3;
  --red:#e63946; --amber:#f4a261; --blue:#4cc9f0; --green:#2a9d8f;
  --border:#2d3a4d;
}}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:'DM Sans',system-ui,sans-serif; background:var(--bg); color:var(--text); line-height:1.55; }}
header {{ padding:28px 32px 16px; border-bottom:1px solid var(--border);
  background:linear-gradient(135deg,#1a222d 0%,#0f1419 60%); }}
header h1 {{ font-family:'Fraunces',serif; font-size:2rem; font-weight:800; }}
header .sub {{ color:var(--muted); font-size:0.9rem; margin-top:8px; }}
nav.tabs {{ display:flex; flex-wrap:wrap; gap:6px; padding:12px 24px; position:sticky; top:0;
  background:rgba(15,20,25,0.95); backdrop-filter:blur(8px); z-index:100; border-bottom:1px solid var(--border); }}
.nav-btn {{ background:var(--card); border:1px solid var(--border); color:var(--muted);
  padding:8px 14px; border-radius:8px; cursor:pointer; font-size:0.8rem; font-weight:600; }}
.nav-btn:hover,.nav-btn.active {{ color:var(--text); border-color:var(--blue); background:#243044; }}
main {{ padding:24px 32px 80px; max-width:1400px; margin:0 auto; }}
.panel {{ display:none; animation:fade .25s ease; }}
.panel.active {{ display:block; }}
@keyframes fade {{ from{{opacity:0; transform:translateY(6px)}} to{{opacity:1;transform:none}} }}
.explain-hero {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:28px; }}
.explain-hero h2 {{ font-family:'Fraunces',serif; margin-bottom:12px; }}
.lede {{ font-size:1.05rem; color:var(--muted); margin-bottom:20px; }}
.legend {{ display:flex; flex-wrap:wrap; gap:12px; margin-bottom:24px; font-size:0.82rem; }}
.pill {{ display:inline-block; padding:3px 10px; border-radius:20px; font-size:0.68rem;
  font-weight:700; letter-spacing:.06em; margin-right:6px; }}
.pill.observed {{ background:#1e3d38; color:#7dffc8; }}
.pill.lookup {{ background:#2a2848; color:#b8b0ff; }}
.pill.scraped {{ background:#1e3348; color:#7ec8ff; }}
.pill.caution {{ background:#3d2a1e; color:#ffb07e; }}
.pill.guide {{ background:#2d3a4d; color:#aab; }}
ul.narrative {{ list-style:none; }}
ul.narrative li {{ margin-bottom:16px; padding-left:0; }}
ul.narrative .src {{ display:block; font-size:0.75rem; color:var(--muted); margin-top:6px; font-family:ui-monospace,monospace; }}
.glossary {{ margin-top:28px; padding-top:20px; border-top:1px solid var(--border); }}
.glossary dt {{ font-weight:700; color:var(--blue); margin-top:12px; }}
.glossary dd {{ color:var(--muted); margin-left:0; margin-bottom:8px; font-size:0.9rem; }}
.kpi-row {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:20px; }}
.kpi-row.quad {{ grid-template-columns:repeat(4,1fr); }}
.kpi {{ background:var(--card); border:1px solid var(--border); border-radius:10px; padding:18px; }}
.kpi .lbl {{ font-size:0.7rem; text-transform:uppercase; letter-spacing:.12em; color:var(--muted); }}
.kpi .val {{ font-size:1.8rem; font-weight:800; margin-top:6px; font-family:'Fraunces',serif; }}
.kpi .sub {{ font-size:0.78rem; color:var(--muted); margin-top:6px; }}
.kpi.d {{ border-top:3px solid var(--red); }}
.kpi.n {{ border-top:3px solid var(--amber); }}
.kpi.w {{ border-top:3px solid var(--blue); }}
.kpi.i {{ border-top:3px solid var(--muted); }}
.action-attack {{ color:var(--red); }}
.action-process {{ color:var(--blue); }}
.action-mixed {{ color:var(--amber); }}
.action-thin, .action-none {{ color:var(--muted); }}
.note {{ font-size:0.88rem; padding:12px 16px; border-radius:8px; margin-bottom:16px; border-left:4px solid var(--border); }}
.note.observed {{ border-color:var(--green); background:rgba(42,157,143,.12); }}
.note.lookup {{ border-color:#7b6cf0; background:rgba(123,108,240,.1); }}
.note.scraped {{ border-color:var(--blue); background:rgba(76,201,240,.08); }}
.note.caution {{ border-color:var(--amber); background:rgba(244,162,97,.12); }}
.note.guide {{ border-color:var(--muted); background:rgba(45,58,77,.5); }}
table.data {{ width:100%; max-width:100%; border-collapse:collapse; font-size:0.82rem; margin:12px 0 24px; table-layout:fixed; }}
table.data th, table.data td {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:140px; }}
table.data th {{ text-align:left; padding:10px 8px; color:var(--muted); font-size:0.68rem;
  text-transform:uppercase; letter-spacing:.08em; border-bottom:1px solid var(--border); }}
table.data td {{ padding:8px; border-bottom:1px solid var(--border); }}
table.compact td, table.compact th {{ padding:6px; font-size:0.75rem; }}
.chart {{ background:var(--card); border-radius:12px; padding:16px; margin:16px 0; }}
.quads {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; margin-top:20px; }}
.empty {{ color:var(--muted); font-style:italic; }}
pre {{ background:#0a0e12; padding:12px; border-radius:8px; font-size:0.85rem; overflow:auto; }}
ul.files {{ margin:12px 0; padding-left:20px; color:var(--muted); font-size:0.88rem; }}
ul.files code {{ color:var(--blue); font-size:0.8rem; }}
footer {{ text-align:center; padding:32px; color:var(--muted); font-size:0.75rem; border-top:1px solid var(--border); }}
@media (max-width:900px) {{ .kpi-row {{ grid-template-columns:1fr 1fr; }} .quads {{ grid-template-columns:1fr; }} }}
</style></head>
<body>
<header>
  <h1>{html.escape(h1_title)}</h1>
  <p class="sub">{html.escape(page_title)} · {html.escape(ts)} · variant={html.escape(variant)}</p>
</header>
<nav class="tabs">{nav}</nav>
<main>{panels}</main>
<footer>Generated {html.escape(ts)} · No numbers invented in HTML — rebuild from CSV/Excel via build_executive_dashboard.py</footer>
<script>
document.querySelectorAll('.nav-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('sec-' + btn.dataset.section).classList.add('active');
    window.scrollTo({{ top: 0, behavior: 'smooth' }});
  }});
}});
document.querySelector('.nav-btn[data-section="explain"]').classList.add('active');
</script>
</body></html>"""


def parse_args(yaml_defaults: dict[str, Any]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build ISZE executive HTML from sources.yaml + engine.")
    p.add_argument("--period", choices=["CY", "FY"], default=yaml_defaults.get("period_type", "CY"))
    p.add_argument("--year", type=int, default=int(yaml_defaults.get("sales_year", 2025)))
    p.add_argument(
        "--ituk-uio",
        # 2026-07-09: "v17_survival" renamed "cohort_survival" — it was never about
        # reading an old v17 FILE (UIO_FILE always resolves to the current canonical
        # _CURRENT workbook), just a leftover label from when the cohort-projection
        # methodology was introduced. engine.py still accepts the old string too, so
        # nothing that already has "v17_survival" saved anywhere breaks.
        choices=["pms_calc", "smmt_car_park", "cohort_survival", "v17_survival"],
        default=yaml_defaults.get("ituk_uio_source", "smmt_car_park"),
        help="ITUK pilot UIO: PMS fleet exercise, SMMT 2024 car park (sheet 4/PRISM), or cohort_survival (sheet 1) — all read from the current UIO workbook, never a pinned old version",
    )
    p.add_argument(
        "--pms-data-mode",
        choices=["auto", "prism", "computed"],
        default=yaml_defaults.get("pms_data_mode", "auto"),
    )
    p.add_argument("--gp", type=float, default=float(yaml_defaults.get("isze_gp_pct", 0.35)) * 100,
                   help="ISZE GP %% on PR00 (e.g. 35)")
    p.add_argument(
        "--market-scope",
        # 2026-07-09: reverted to ITUK default same day it was flipped — Pan-European
        # produces a >100x-inflated network UIO (MIDI included at 667K vs its own
        # documented 98,654, and MIDI should be EXCLUDED entirely per the existing
        # canonical GPS decision — see distributor_master_mapping.csv). Fix that
        # before defaulting to this scope. Still selectable via --market-scope.
        default=yaml_defaults.get("market_scope", "ITUK (PMS Calc pilot)"),
        help="ITUK (PMS Calc pilot) | Pan-European (all distributors) | <distributor name>",
    )
    p.add_argument("--horizon", type=float, default=float(yaml_defaults.get("horizon_years", 1.0)))
    p.add_argument(
        "--variant",
        choices=["pms", "iam", "full", "all"],
        default="all",
        help="pms=engine only; iam=lookup lab; full=combined; all=write three HTML files",
    )
    p.add_argument("-o", "--output", type=Path, default=None, help="Single output path (only if variant is pms/iam/full)")
    return p.parse_args()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    cfg, paths, yaml_defaults = load_build_config()
    args = parse_args(yaml_defaults)

    from sources_loader import load_fx_rates

    global BUILD_OPTS, SOURCES
    src = dict((yaml_defaults.get("sources") or {}))
    SOURCES = {k: Path(v) if v else Path(".") for k, v in src.items()}
    fx = load_fx_rates(cfg)
    BUILD_OPTS = {
        # 2026-07-09: flipped default from ITUK-only to network-wide per Jerome —
        # ITUK was the pilot scope, not meant to stay the default view. Override
        # with --market-scope if you need ITUK-only again.
        "market_scope": args.market_scope,
        "period_type": args.period.upper(),
        "sales_year": args.year,
        "ituk_uio_source": args.ituk_uio,
        "pms_data_mode": args.pms_data_mode,
        "isze_gp_pct": args.gp / 100.0,
        "horizon_years": args.horizon,
        "pms_basket": yaml_defaults.get("pms_basket", "Maintenance + Wear Repair (PMS pilot)"),
        "db_gm": 0.37,
        "dlr_gm": 0.25,
        "sources": src,
        "fx": fx,
    }

    print("Loading merged scraper data...")
    merged = load_merged(fx)
    print(f"  {len(merged)} PNs")

    scored = compute_scores(merged, db_gm=BUILD_OPTS["db_gm"], dlr_gm=BUILD_OPTS["dlr_gm"])
    scored = compute_expected_loss(
        scored,
        isze_gp_pct=BUILD_OPTS["isze_gp_pct"],
        horizon_years=BUILD_OPTS["horizon_years"],
    )

    print("Loading engine macro (category-level PMS)...")
    engine = load_engine_macro(cfg, paths, BUILD_OPTS)
    uio_potential = 11_900.0
    if engine and "Summary KPIs" in engine and not engine.get("Summary KPIs", pd.DataFrame()).empty:
        uio_potential = float(engine["Summary KPIs"].iloc[0].get("total_uio", uio_potential))

    scored = compute_lost_sales(
        scored,
        uio_potential=uio_potential,
        isze_gp_pct=BUILD_OPTS["isze_gp_pct"],
        horizon_years=BUILD_OPTS["horizon_years"],
    )

    meta = {
        "generated": datetime.now().isoformat(),
        "pn_count": len(scored),
        "build_opts": {k: v for k, v in BUILD_OPTS.items() if k != "sources"},
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    targets: list[tuple[str, Path]] = []
    if args.variant == "all":
        targets = [
            ("pms", OUT_PATH_PMS),
            ("iam", OUT_PATH_IAM),
            ("full", OUT_PATH),
        ]
    else:
        path_map = {"pms": OUT_PATH_PMS, "iam": OUT_PATH_IAM, "full": OUT_PATH}
        targets = [(args.variant, args.output or path_map[args.variant])]

    for var, out_path in targets:
        html_out = build_html(scored, engine, meta, BUILD_OPTS, variant=var)
        out_path.write_text(html_out, encoding="utf-8")
        print(f"Wrote {out_path} ({out_path.stat().st_size:,} bytes) [{var}]")

    print(f"  ITUK UIO: {BUILD_OPTS['ituk_uio_source']} · {BUILD_OPTS['period_type']} {BUILD_OPTS['sales_year']}")
    print(f"Open PMS: file:///{OUT_PATH_PMS.as_posix()}")


if __name__ == "__main__":
    main()
