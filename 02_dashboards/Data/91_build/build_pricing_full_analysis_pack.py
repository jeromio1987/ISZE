"""Full shared pricing + AIM + PMS/GPS + MOS + VPACC mega-pack.

Synthesizes year-matched PR00 findings with PRISM derived tables into one
self-contained HTML (inline SVG charts — no CDN). Integrity score prominent.
Provisional / not externally quotable while integrity band is weak.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ISZE = Path(__file__).resolve().parents[2]
DER = ISZE / "01_data" / "00_derived"
DASH = ISZE / "02_dashboards" / "pricing"
UTC_NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def eur(x, millions_threshold: float = 1_000_000.0) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    ax = abs(float(x))
    if ax >= millions_threshold:
        return f"€{float(x) / 1_000_000:,.1f}M"
    return f"€{float(x):,.0f}"


def pct(x, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{float(x):.{digits}f}%"


def pct_frac(x, digits: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{100.0 * float(x):.{digits}f}%"


def safe_float(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def load_json(path: Path, default=None):
    if not path.is_file():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8"))


def bar_svg(labels, values, width=980, height=280, unit="", color="#CC0E1E", max_v=None) -> str:
    """Simple horizontal-friendly vertical bar chart as inline SVG."""
    n = max(1, len(labels))
    pad_l, pad_r, pad_t, pad_b = 48, 16, 18, 72
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    vmax = max_v if max_v is not None else (max(values) if values else 1.0)
    vmax = vmax if vmax and vmax > 0 else 1.0
    bar_w = plot_w / n * 0.62
    gap = plot_w / n
    ticks = 4
    parts = [
        f'<svg class="ch" viewBox="0 0 {width} {height}" role="img" aria-label="bar chart">'
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fff"/>'
    ]
    for i in range(ticks + 1):
        y = pad_t + plot_h * (1 - i / ticks)
        val = vmax * i / ticks
        parts.append(
            f'<line x1="{pad_l}" y1="{y:.1f}" x2="{width-pad_r}" y2="{y:.1f}" '
            f'stroke="#E4E4E7" stroke-width="1"/>'
            f'<text class="tk" x="{pad_l-8}" y="{y+4:.1f}" text-anchor="end">'
            f"{val:,.0f}{unit}</text>"
        )
    for i, (lab, v) in enumerate(zip(labels, values)):
        x = pad_l + i * gap + (gap - bar_w) / 2
        h = plot_h * (float(v) / vmax)
        y = pad_t + plot_h - h
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" fill="{color}"/>'
            f'<text class="lab" x="{x + bar_w/2:.1f}" y="{height-12}" text-anchor="middle">{lab}</text>'
            f'<text class="val" x="{x + bar_w/2:.1f}" y="{y-6:.1f}" text-anchor="middle">'
            f"{float(v):,.1f}{unit}</text>"
        )
    parts.append("</svg>")
    return "".join(parts)


def scatter_svg(points, width=980, height=360, x_lab="GPS €/UIO", y_lab="PMS total capture") -> str:
    """points: list of dict {x,y,label,color}"""
    pts = [p for p in points if p.get("x") is not None and p.get("y") is not None]
    if not pts:
        return '<p class="lead">No scatter points available.</p>'
    pad_l, pad_r, pad_t, pad_b = 64, 24, 24, 56
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    xs = [p["x"] for p in pts]
    ys = [p["y"] for p in pts]
    xmin, xmax = min(xs) * 0.9, max(xs) * 1.08
    ymin, ymax = 0.0, max(ys) * 1.12
    if xmax <= xmin:
        xmax = xmin + 1
    if ymax <= ymin:
        ymax = ymin + 0.1
    # medians as quadrant guides
    mx = sorted(xs)[len(xs) // 2]
    my = sorted(ys)[len(ys) // 2]

    def sx(x):
        return pad_l + (x - xmin) / (xmax - xmin) * plot_w

    def sy(y):
        return pad_t + (1 - (y - ymin) / (ymax - ymin)) * plot_h

    parts = [
        f'<svg class="ch" viewBox="0 0 {width} {height}" role="img" aria-label="scatter">'
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fff"/>'
        f'<line x1="{sx(mx):.1f}" y1="{pad_t}" x2="{sx(mx):.1f}" y2="{pad_t+plot_h}" '
        f'stroke="#B45309" stroke-dasharray="4 4" stroke-width="1.2"/>'
        f'<line x1="{pad_l}" y1="{sy(my):.1f}" x2="{pad_l+plot_w}" y2="{sy(my):.1f}" '
        f'stroke="#B45309" stroke-dasharray="4 4" stroke-width="1.2"/>'
        f'<text class="tk" x="{width/2}" y="{height-10}" text-anchor="middle">{x_lab}</text>'
        f'<text class="tk" x="14" y="{height/2}" text-anchor="middle" '
        f'transform="rotate(-90 14 {height/2})">{y_lab}</text>'
    ]
    # axis ticks
    for i in range(5):
        xv = xmin + (xmax - xmin) * i / 4
        yv = ymin + (ymax - ymin) * i / 4
        parts.append(
            f'<text class="tk" x="{sx(xv):.1f}" y="{pad_t+plot_h+18}" text-anchor="middle">{xv:.0f}</text>'
            f'<text class="tk" x="{pad_l-8}" y="{sy(yv)+4:.1f}" text-anchor="end">{yv:.0%}</text>'
        )
    # place labels with simple N/S alternation to reduce overlap
    for i, p in enumerate(pts):
        cx, cy = sx(p["x"]), sy(p["y"])
        col = p.get("color", "#CC0E1E")
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6" fill="{col}" opacity="0.85"/>')
        dy = -10 if i % 2 == 0 else 16
        parts.append(
            f'<text class="lab" x="{cx:.1f}" y="{cy+dy:.1f}" text-anchor="middle">{p["label"]}</text>'
        )
    parts.append("</svg>")
    return "".join(parts)


def synthesize() -> dict:
    findings = load_json(DER / "pricing_history_findings.meta.json")
    if not findings.get("network"):
        raise SystemExit("Missing pricing_history_findings.meta.json — run build_pricing_history_findings.py first")

    aim_win = load_json(DER / "aim_billing_windows.json")
    aim_db = pd.read_csv(DER / "aim_billing_by_db_window.csv")
    pms = pd.read_csv(DER / "pms_capture_by_db_year.csv")
    gps = pd.read_csv(DER / "gps_spu_by_distributor.csv")
    aim_gps = pd.read_csv(DER / "aim_gps_matrix.csv")
    mix = pd.read_csv(DER / "mix_genuine_bvp_pms.csv")
    by_db = pd.read_csv(DER / "pr00_realization_by_db_cy.csv")
    zlev = pd.read_csv(DER / "zpr1_vs_pr00_by_payer_year.csv")
    zyoy = pd.read_csv(DER / "zpr1_yoy_by_payer.csv")
    mos = pd.read_csv(DER / "kpi_mos_response_summary_2025_2026.csv")
    gap = pd.read_csv(DER / "no_pr00_gap_cy2025_ranked.csv")
    vr = load_json(DER / "_verification_report.json")
    snap = load_json(DER / "metrics_snapshot.json")

    # --- PMS total capture (primary) by DB year ---
    pms_tot = pms[(pms["line_type"] == "total")].copy()
    pms_db_year = (
        pms_tot.groupby(["year", "distributor_code"], as_index=False)
        .agg(
            actual_qty=("actual_qty", "sum"),
            expected_qty=("expected_qty", "sum"),
            actual_rev_eur=("actual_rev_eur", "sum"),
        )
    )
    pms_db_year["capture_rate"] = pms_db_year["actual_qty"] / pms_db_year["expected_qty"].replace(0, pd.NA)
    pms_net = (
        pms_tot.groupby("year", as_index=False)
        .agg(actual_qty=("actual_qty", "sum"), expected_qty=("expected_qty", "sum"), actual_rev_eur=("actual_rev_eur", "sum"))
    )
    pms_net["capture_rate"] = pms_net["actual_qty"] / pms_net["expected_qty"]

    pms25 = pms_db_year[pms_db_year["year"] == 2025].sort_values("capture_rate", ascending=False)
    # UTI / UMI separate rows
    uti_umi_pms = pms25[pms25["distributor_code"].isin(["UTI", "UMI"])].to_dict(orient="records")

    # genuine share as EXTRA lens (not headline)
    pms_g = pms[(pms["line_type"] == "genuine") & (pms["year"] == 2025)]
    pms_b = pms[(pms["line_type"] == "bvp") & (pms["year"] == 2025)]
    gen_rev = float(pms_g["actual_rev_eur"].sum())
    bvp_rev = float(pms_b["actual_rev_eur"].sum())
    tot_lens_rev = gen_rev + bvp_rev

    # --- GPS SPU 2025 ---
    gps25 = gps[gps["year"] == 2025].copy()
    gps25 = gps25.sort_values("spend_per_unit_eur", ascending=False)

    # --- AIM × GPS quadrant 2025 ---
    ag25 = aim_gps[aim_gps["year"] == 2025].copy()
    q_counts = ag25["quadrant"].value_counts().to_dict()
    # never blend Israel
    israel = ag25[ag25["distributor_code"].isin(["UTI", "UMI"])][
        ["distributor_code", "gps_spu_eur", "pms_capture_all", "quadrant", "quadrant_label", "net_sales_eur"]
    ].to_dict(orient="records")

    # --- Mix genuine/BVP by family 2025 ---
    mix25 = mix[mix["year"] == 2025].copy()
    fam = (
        mix25.groupby("product_family", as_index=False)
        .agg(bvp_eur=("bvp_eur", "sum"), genuine_eur=("genuine_eur", "sum"), total_eur=("total_eur", "sum"))
    )
    fam["bvp_share_eur"] = fam["bvp_eur"] / (fam["bvp_eur"] + fam["genuine_eur"]).replace(0, pd.NA)
    fam = fam.sort_values("bvp_share_eur", ascending=False)
    net_bvp_share = float(mix25["bvp_eur"].sum() / max(1e-9, mix25["bvp_eur"].sum() + mix25["genuine_eur"].sum()))

    # --- AIM billing windows ---
    aim_windows = aim_win.get("windows", [])
    aim_cy25 = aim_db[aim_db["window"] == "CY2025"].sort_values("net_sales_eur", ascending=False)
    aim_fy25 = aim_db[aim_db["window"] == "FY2025"].sort_values("net_sales_eur", ascending=False)

    # --- PR00 by DB CY2025 ---
    db25 = by_db[by_db["year"] == 2025].sort_values("parts_eur", ascending=False)

    # --- ZPR1 UMI jump flag ---
    umi_yoy = zyoy[(zyoy["payer"] == "UMI") & (zyoy["from_year"] == 2025) & (zyoy["to_year"] == 2026)]
    uti_yoy = zyoy[(zyoy["payer"] == "UTI") & (zyoy["from_year"] == 2025) & (zyoy["to_year"] == 2026)]
    umi_jump = float(umi_yoy.iloc[0]["median_zpr1_yoy_pct"]) if len(umi_yoy) else None
    uti_jump = float(uti_yoy.iloc[0]["median_zpr1_yoy_pct"]) if len(uti_yoy) else None
    # vs PR00 levels 2025 vs 2026
    def z_med(payer, year):
        r = zlev[(zlev["payer"] == payer) & (zlev["year"] == year)]
        return float(r.iloc[0]["median_zpr1_vs_pr00_pct"]) if len(r) else None

    zpr1_flags = {
        "umi_yoy_2025_2026_median_pct": umi_jump,
        "uti_yoy_2025_2026_median_pct": uti_jump,
        "umi_vs_pr00_2025": z_med("UMI", 2025),
        "umi_vs_pr00_2026": z_med("UMI", 2026),
        "uti_vs_pr00_2025": z_med("UTI", 2025),
        "uti_vs_pr00_2026": z_med("UTI", 2026),
        "suspicion": (
            "UMI ZPR1 median YoY +20.2% (2025→2026) with vs-PR00 gap narrowing from −15.3% to −5.2%. "
            "Treat as list-composition / coverage change until PN-level audit — do not blend with UTI."
            if umi_jump and umi_jump > 12
            else "No extreme UMI YoY flag beyond normal list moves."
        ),
        "uti_umi_never_blend": True,
    }

    # --- MOS (not elasticity) ---
    mos_clean = mos.replace({float("nan"): None}).to_dict(orient="records")
    mos_movers = (
        mos.dropna(subset=["delta_days_2026_vs_2025"])
        .sort_values("delta_days_2026_vs_2025")
        .head(8)
        .to_dict(orient="records")
    )

    # --- VPACC thin hooks ---
    vp = findings.get("vpacc", {})
    vpacc_hooks = [
        {
            "stream": "VP",
            "n_actions": int(vp.get("by_stream", {}).get("VP", 0)),
            "metric_hooks": "PR00 realization coverage · NO_LIST gap · ZPR1 vs PR00 (UTI/UMI separate)",
            "join_quality": "thin — PIC/stream keyed, not dealer",
        },
        {
            "stream": "ACC",
            "n_actions": int(vp.get("by_stream", {}).get("ACC", 0)),
            "metric_hooks": "PMS total capture · AIM×GPS quadrant · genuine/BVP mix (extra lens)",
            "join_quality": "thin — status snapshot only",
        },
    ]

    # --- Integrity: reuse findings score + add synthesis deductions if needed ---
    integ = dict(findings.get("integrity", {}))
    # Add note that pack now includes PRISM lenses; do not silently inflate score
    extra_deds = []
    # UMI suspicious jump → integrity caution
    if umi_jump and umi_jump > 12:
        extra_deds.append(
            {
                "item": "UMI ZPR1 YoY anomaly",
                "deduction": 3,
                "detail": f"UMI median ZPR1 YoY {umi_jump:+.1f}% (2025→2026) — composition/coverage risk until PN audit",
            }
        )
    # Open PRISM flags (note only — small deduction for open assumptions)
    extra_deds.append(
        {
            "item": "Open PRISM assumptions (note)",
            "deduction": 2,
            "detail": "Air-filter interval provisional (IML confirm open); brake pad/shoe factors pending IML/ITUK",
        }
    )
    score = int(integ.get("score", 53))
    deds = list(integ.get("deductions", []))
    for ed in extra_deds:
        # avoid double-count if already present
        if any(d["item"] == ed["item"] for d in deds):
            continue
        score -= ed["deduction"]
        deds.append(ed)
    score = max(0, min(100, score))
    band = "weak" if score < 55 else ("provisional" if score < 75 else "usable_internal")
    integ = {
        "score": score,
        "band": band,
        "quotable_externally": False,
        "label": "Internal QA / provisional — do not quote list-to-pocket externally",
        "deductions": deds,
        "deduction_sum": sum(d["deduction"] for d in deds),
        "start": 100,
        "built_at_utc": UTC_NOW,
    }

    # verification / snapshot anchors
    ver_ok = False
    if isinstance(vr.get("summary"), dict):
        ver_ok = bool(vr["summary"].get("ok"))
    elif "ok" in vr:
        ver_ok = bool(vr["ok"])

    # risks / next asks
    risks = [
        f"List-to-pocket integrity {score}/100 ({band}) — not externally quotable.",
        f"CY2025 NO_LIST ≈ {eur(findings.get('nolist', {}).get('gap_eur', 0))} "
        f"({100 * findings.get('nolist', {}).get('gap_share_of_parts', 0):.1f}% of parts) — "
        "steering/DPD/oil SKUs dominate.",
        zpr1_flags["suspicion"],
        "UTI and UMI remain separate Israel distributors — never blend for IDS/GPS/pricing.",
        "PMS headline uses total capture; genuine/BVP is an extra mix lens only.",
        "KPI MOS = Days of Parts in Stock (warehouse response) — not market elasticity; "
        "ISZE→DB volume elasticity remains non-quotable.",
        "VPACC→metric join is thin (PIC/stream, not dealer).",
        "Open: air-filter interval provisional; brake factors pending IML/ITUK (note only).",
        "2026 YTD PR00 uses current IE40 extract (not Jan-2026 snapshot) — coverage depressed.",
        "Year-end PR00 stamps: intra-year list changes not dated.",
    ]
    next_asks = [
        "QA year-matched PR00 joins (spot-check top NO_LIST PNs + UTI/UMI realization).",
        "PN-level audit of UMI ZPR1 2025→2026 (+20% median) — list rebuild vs true price move?",
        "Confirm air-filter interval with IML; confirm brake pad/shoe factors with IML/ITUK.",
        "Decide whether 2026 list-vintage needs a frozen Jan snapshot for YTD realization.",
        "Map priority VPACC PIC items to NO_LIST / capture / GPS SPU owners.",
    ]

    # write helper CSVs
    outs = {}
    pms_path = DER / "pricing_pack_pms_total_by_db_year.csv"
    pms_db_year.to_csv(pms_path, index=False)
    outs[pms_path.name] = str(pms_path.relative_to(ISZE)).replace("\\", "/")

    fam_path = DER / "pricing_pack_mix_family_cy2025.csv"
    fam.to_csv(fam_path, index=False)
    outs[fam_path.name] = str(fam_path.relative_to(ISZE)).replace("\\", "/")

    ag_path = DER / "pricing_pack_aim_gps_cy2025.csv"
    ag25.to_csv(ag_path, index=False)
    outs[ag_path.name] = str(ag_path.relative_to(ISZE)).replace("\\", "/")

    aim_top_path = DER / "pricing_pack_aim_billing_top_cy2025.csv"
    aim_cy25.head(25).to_csv(aim_top_path, index=False)
    outs[aim_top_path.name] = str(aim_top_path.relative_to(ISZE)).replace("\\", "/")

    payload = {
        "built_at_utc": UTC_NOW,
        "status": "provisional_qa_pending",
        "quotable_externally": False,
        "mode": "A",
        "title": "ISZE Pricing · Full Analysis Pack",
        "integrity": integ,
        "findings_core": {
            "network": findings.get("network"),
            "realization_details": findings.get("realization_details"),
            "nolist": findings.get("nolist"),
            "nolist_top": findings.get("nolist_top", [])[:25],
            "zpr1_level": findings.get("zpr1_level"),
            "zpr1_yoy": findings.get("zpr1_yoy"),
            "mos_summary": findings.get("mos_summary"),
            "mos_meta": findings.get("mos_meta"),
            "vpacc": findings.get("vpacc"),
        },
        "aim": {
            "meta": aim_win.get("meta", {}),
            "windows": aim_windows,
            "top_db_cy2025": aim_cy25.head(15).to_dict(orient="records"),
            "top_db_fy2025": aim_fy25.head(15).to_dict(orient="records"),
            "note": "Actual SAP net sales by CY/FY window — billing only, not AIM Qty×PR00 scoring",
        },
        "pms": {
            "primary": "total",
            "network_by_year": pms_net.to_dict(orient="records"),
            "top_db_cy2025": pms25.head(15).to_dict(orient="records"),
            "uti_umi_cy2025": uti_umi_pms,
            "genuine_bvp_extra_lens_cy2025": {
                "genuine_rev_eur": round(gen_rev, 2),
                "bvp_rev_eur": round(bvp_rev, 2),
                "bvp_share_of_lens_eur": round(bvp_rev / tot_lens_rev, 4) if tot_lens_rev else None,
                "note": "Extra mix lens only — headline remains PMS total capture",
            },
        },
        "gps": {
            "cy2025_top": gps25.head(18)[
                ["distributor_code", "country", "total_sales_eur", "uio_units", "spend_per_unit_eur", "traffic_light"]
            ].to_dict(orient="records"),
            "uti_spu": safe_float(gps25.loc[gps25["distributor_code"] == "UTI", "spend_per_unit_eur"].iloc[0])
            if (gps25["distributor_code"] == "UTI").any()
            else None,
            "umi_spu": safe_float(gps25.loc[gps25["distributor_code"] == "UMI", "spend_per_unit_eur"].iloc[0])
            if (gps25["distributor_code"] == "UMI").any()
            else None,
        },
        "aim_gps": {
            "quadrant_counts_cy2025": q_counts,
            "rows_cy2025": ag25[
                ["distributor_code", "gps_spu_eur", "pms_capture_all", "quadrant", "quadrant_label", "net_sales_eur"]
            ].to_dict(orient="records"),
            "israel_uti_umi": israel,
        },
        "mix": {
            "network_bvp_share_eur_cy2025": round(net_bvp_share, 4),
            "by_family_cy2025": fam.to_dict(orient="records"),
        },
        "pr00_by_db_cy2025": db25.head(20).to_dict(orient="records"),
        "zpr1_flags": zpr1_flags,
        "mos_movers": mos_movers,
        "vpacc_hooks": vpacc_hooks,
        "prism_flags_open": [
            {
                "id": "C_air_interval",
                "status": "provisional",
                "note": "Air-filter consumable_factor 0.5 provisional — IML-confirmed ratio still open",
            },
            {
                "id": "brake_factors",
                "status": "pending",
                "note": "Brake pad/shoe interval factors pending IML/ITUK — do not treat as locked",
            },
            {
                "id": "H_credit_notes",
                "status": "acted_judgment",
                "note": "CR/RE exclusion is documented judgment, not ERP-confirmed",
            },
        ],
        "verification": {
            "ok": ver_ok,
            "summary": vr.get("summary"),
            "metrics_snapshot_as_of": snap.get("as_of"),
            "note": "Green verification anchors PRISM KPIs; list-to-pocket remains provisional",
        },
        "risks": risks,
        "next_asks": next_asks,
        "outputs": outs,
        "html": "02_dashboards/pricing/ISZE_Pricing_Full_Analysis_Pack.html",
        "related_html": [
            "02_dashboards/pricing/ISZE_Pricing_History_Findings_Dashboard.html",
            "02_dashboards/pricing/ISZE_Pricing_BI_Dashboard.html",
        ],
    }
    return payload


def write_html(payload: dict, path: Path) -> None:
    integ = payload["integrity"]
    net = payload["findings_core"]["network"]
    cy25 = next((r for r in net if r["year"] == 2025), {})
    gap = payload["findings_core"]["nolist"]
    pms_net = payload["pms"]["network_by_year"]
    pms25_cap = next((r for r in pms_net if int(r["year"]) == 2025), {})
    zf = payload["zpr1_flags"]

    # charts
    net_years = [str(r["year"]) for r in net]
    cov_vals = [float(r["coverage_pct"] or 0) for r in net]
    real_vals = [float(r["realization_pct"] or 0) for r in net]
    cov_chart = bar_svg(net_years, cov_vals, height=260, unit="%", color="#B45309", max_v=100)
    real_chart = bar_svg(net_years, real_vals, height=260, unit="%", color="#CC0E1E", max_v=100)

    aim_labels = [w["window"] for w in payload["aim"]["windows"] if w.get("status") != "empty_future"]
    aim_vals = [float(w["eur"]) / 1e6 for w in payload["aim"]["windows"] if w.get("status") != "empty_future"]
    aim_chart = bar_svg(aim_labels, aim_vals, height=260, unit="M", color="#1A1A1A")

    scatter_pts = []
    q_colors = {
        "defend": "#15803D",
        "priority_target": "#CC0E1E",
        "attach_gap": "#B45309",
        "wallet_gap": "#2563EB",
        "insufficient_data": "#9CA3AF",
    }
    for r in payload["aim_gps"]["rows_cy2025"]:
        if r.get("gps_spu_eur") is None or (isinstance(r.get("gps_spu_eur"), float) and math.isnan(r["gps_spu_eur"])):
            continue
        if r.get("pms_capture_all") is None or (
            isinstance(r.get("pms_capture_all"), float) and math.isnan(r["pms_capture_all"])
        ):
            continue
        scatter_pts.append(
            {
                "x": float(r["gps_spu_eur"]),
                "y": float(r["pms_capture_all"]),
                "label": r["distributor_code"],
                "color": q_colors.get(r.get("quadrant"), "#CC0E1E"),
            }
        )
    scatter = scatter_svg(scatter_pts)

    # tables
    def rows_net():
        return "".join(
            f"<tr><td>{r['year']}</td><td>{r['period']}</td><td class='n'>{eur(r['parts_eur'])}</td>"
            f"<td class='n'>{pct(r['coverage_pct'])}</td><td class='n'>{pct(r['realization_pct'])}</td>"
            f"<td class='n'>{eur(r['no_list_eur'])}</td><td class='sm'>{r.get('billing_end') or ''}</td></tr>"
            for r in net
        )

    def rows_db():
        return "".join(
            f"<tr><td>{r['db']}</td><td class='n'>{eur(r['parts_eur'])}</td>"
            f"<td class='n'>{pct(r['coverage_pct'])}</td><td class='n'>{pct(r['realization_pct'])}</td>"
            f"<td class='n'>{eur(r['no_list_eur'])}</td></tr>"
            for r in payload["pr00_by_db_cy2025"][:16]
        )

    def rows_z():
        return "".join(
            f"<tr><td>{r['year']}</td><td><b>{r['payer']}</b> ({r['customer']})</td>"
            f"<td class='n'>{int(r['n_vs_pr00']):,}</td>"
            f"<td class='n'>{float(r['median_zpr1_vs_pr00_pct']):+.1f}%</td>"
            f"<td class='n'>{float(r['p25_zpr1_vs_pr00_pct']):+.1f}% … {float(r['p75_zpr1_vs_pr00_pct']):+.1f}%</td></tr>"
            for r in payload["findings_core"]["zpr1_level"]
        )

    def rows_zy():
        return "".join(
            f"<tr><td>{r['from_year']}→{r['to_year']}</td><td><b>{r['payer']}</b></td>"
            f"<td class='n'>{int(r['n_common_pns']):,}</td>"
            f"<td class='n'>{float(r['median_zpr1_yoy_pct']):+.1f}%</td></tr>"
            for r in payload["findings_core"]["zpr1_yoy"]
        )

    def rows_aim_top():
        return "".join(
            f"<tr><td>{r['distributor_code']}</td><td class='n'>{eur(r['net_sales_eur'])}</td></tr>"
            for r in payload["aim"]["top_db_cy2025"][:12]
        )

    def rows_pms():
        return "".join(
            f"<tr><td>{r['distributor_code']}</td>"
            f"<td class='n'>{pct_frac(r['capture_rate'])}</td>"
            f"<td class='n'>{float(r['actual_qty']):,.0f}</td>"
            f"<td class='n'>{float(r['expected_qty']):,.0f}</td>"
            f"<td class='n'>{eur(r['actual_rev_eur'])}</td></tr>"
            for r in payload["pms"]["top_db_cy2025"][:14]
        )

    def rows_gps():
        return "".join(
            f"<tr><td>{r['distributor_code']}</td><td>{r['country']}</td>"
            f"<td class='n'>{eur(r['total_sales_eur'])}</td>"
            f"<td class='n'>{float(r['uio_units'] or 0):,.0f}</td>"
            f"<td class='n'>{float(r['spend_per_unit_eur']):,.0f}</td>"
            f"<td class='sm'>{r.get('traffic_light') or ''}</td></tr>"
            for r in payload["gps"]["cy2025_top"]
            if r.get("spend_per_unit_eur") == r.get("spend_per_unit_eur")
        )

    def rows_quad():
        return "".join(
            f"<tr><td>{r['distributor_code']}</td>"
            f"<td class='n'>{float(r['gps_spu_eur']):,.0f}</td>"
            f"<td class='n'>{pct_frac(r['pms_capture_all'])}</td>"
            f"<td>{r.get('quadrant_label') or r.get('quadrant')}</td></tr>"
            for r in payload["aim_gps"]["rows_cy2025"]
            if r.get("quadrant") != "insufficient_data"
        )

    def rows_mix():
        return "".join(
            f"<tr><td>{r['product_family']}</td>"
            f"<td class='n'>{eur(r['genuine_eur'])}</td>"
            f"<td class='n'>{eur(r['bvp_eur'])}</td>"
            f"<td class='n'>{pct_frac(r['bvp_share_eur'])}</td></tr>"
            for r in payload["mix"]["by_family_cy2025"]
        )

    def rows_gap():
        return "".join(
            f"<tr><td class='mono'>{r['part_number']}</td><td>{r.get('description','')}</td>"
            f"<td class='n'>{eur(float(r['cy2025_eur']))}</td>"
            f"<td class='sm'>{r.get('gap_reason','')}</td></tr>"
            for r in payload["findings_core"]["nolist_top"][:18]
        )

    def rows_mos():
        out = []
        for r in payload["findings_core"]["mos_summary"][:16]:
            d25 = r.get("avg_mos_days_2025")
            d26 = r.get("avg_mos_days_2026_ytd")
            dlt = r.get("delta_days_2026_vs_2025")
            out.append(
                "<tr><td>{dist}</td><td class='n'>{n25}</td><td class='n'>{a25}</td>"
                "<td class='n'>{n26}</td><td class='n'>{a26}</td><td class='n'>{dlt}</td></tr>".format(
                    dist=r["distributor"],
                    n25=r.get("n_months_2025") or 0,
                    a25="—" if d25 is None or (isinstance(d25, float) and math.isnan(d25)) else f"{float(d25):.0f}",
                    n26=r.get("n_months_2026_ytd") or 0,
                    a26="—" if d26 is None or (isinstance(d26, float) and math.isnan(d26)) else f"{float(d26):.0f}",
                    dlt="—" if dlt is None or (isinstance(dlt, float) and math.isnan(dlt)) else f"{float(dlt):+.0f}",
                )
            )
        return "".join(out)

    def rows_ded():
        return "".join(
            f"<tr><td>−{d['deduction']}</td><td>{d['item']}</td><td class='sm'>{d['detail']}</td></tr>"
            for d in integ["deductions"]
        )

    def rows_risk():
        return "".join(f"<li>{x}</li>" for x in payload["risks"])

    def rows_asks():
        return "".join(f"<li>{x}</li>" for x in payload["next_asks"])

    def rows_flags():
        return "".join(
            f"<tr><td class='mono'>{f['id']}</td><td>{f['status']}</td><td class='sm'>{f['note']}</td></tr>"
            for f in payload["prism_flags_open"]
        )

    def rows_vp():
        return "".join(
            f"<tr><td>{h['stream']}</td><td class='n'>{h['n_actions']}</td>"
            f"<td class='sm'>{h['metric_hooks']}</td><td class='sm'>{h['join_quality']}</td></tr>"
            for h in payload["vpacc_hooks"]
        )

    israel_note = "".join(
        f"<tr><td><b>{r['distributor_code']}</b></td>"
        f"<td class='n'>{float(r['gps_spu_eur']):,.0f}</td>"
        f"<td class='n'>{pct_frac(r['pms_capture_all'])}</td>"
        f"<td>{r.get('quadrant_label')}</td></tr>"
        for r in payload["aim_gps"]["israel_uti_umi"]
    )

    conclusion = (
        f"Integrity {integ['score']}/100 ({integ['band']}) — provisional, not externally quotable. "
        f"CY2025 matched realization {pct(cy25.get('realization_pct'))} on "
        f"{pct(cy25.get('coverage_pct'))} list coverage; NO_LIST {eur(gap.get('gap_eur', 0))} "
        f"({100 * gap.get('gap_share_of_parts', 0):.1f}% of parts). "
        f"Network PMS total capture CY2025 ≈ {pct_frac(pms25_cap.get('capture_rate'))}. "
        f"UMI ZPR1 YoY 2025→2026 median {zf.get('umi_yoy_2025_2026_median_pct')}% "
        f"(investigate; UTI separate at {zf.get('uti_yoy_2025_2026_median_pct')}%). "
        f"PRISM verification green: {payload['verification']['ok']}."
    )

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE · Pricing Full Analysis Pack</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#fff;color:#1A1A1A;font:15px/1.55 "Segoe UI",Arial,sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 28px 90px}}
header{{border-bottom:3px solid #CC0E1E;padding:38px 0 20px;margin-bottom:28px}}
.brand{{font:800 13px/1 Arial Black,Arial;letter-spacing:.22em;color:#CC0E1E;margin-bottom:14px}}
h1{{font-size:32px;margin:0 0 8px;letter-spacing:-.35px}}
.sub{{color:#5A5A5A;max-width:900px}}
.stamp{{color:#5A5A5A;font-size:12.5px;margin-top:12px}}
.badge{{display:inline-block;padding:4px 10px;background:#FEF8F0;color:#B45309;font-weight:700;font-size:12px;border:1px solid #F0D7B0}}
.callout{{border-left:4px solid #B45309;background:#FEF8F0;padding:14px 16px;margin:0 0 22px}}
.callout b{{color:#B45309}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:0 0 28px}}
.kpi{{border:1px solid #E4E4E7;border-top:3px solid #CC0E1E;padding:14px}}
.kpi .v{{font-size:26px;font-weight:800;letter-spacing:-1px}}
.kpi .l{{font-size:11px;color:#5A5A5A;text-transform:uppercase;letter-spacing:.06em;margin-top:6px;font-weight:600}}
.kpi.amber{{border-top-color:#B45309}}.kpi.amber .v{{color:#B45309}}
.kpi.ok{{border-top-color:#15803D}}.kpi.ok .v{{color:#15803D}}
h2{{font-size:20px;margin:40px 0 8px}}
h2 .num{{color:#CC0E1E;font-weight:800;margin-right:8px}}
.lead{{color:#5A5A5A;font-size:14px;margin:0 0 14px;max-width:920px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:10px}}
th{{background:#CC0E1E;color:#fff;text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:.04em}}
td{{padding:7px 10px;border-bottom:1px solid #F0F0F0}}
tbody tr:nth-child(even){{background:#FAFAFA}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}
td.sm{{font-size:12px;color:#5A5A5A}} td.mono{{font-family:Consolas,monospace;font-size:12px}}
ul.bul{{margin:0 0 12px 18px;padding:0}} ul.bul li{{margin:0 0 6px}}
.toc a{{color:#CC0E1E;text-decoration:none;margin-right:14px;font-size:13px;font-weight:600}}
.foot{{margin-top:48px;padding-top:16px;border-top:1px solid #E4E4E7;font-size:11.5px;color:#5A5A5A;line-height:1.7}}
svg.ch{{width:100%;height:auto;display:block}}
svg.ch .tk{{font-size:11px;fill:#5A5A5A}}
svg.ch .lab{{font-size:10.5px;fill:#1A1A1A}}
svg.ch .val{{font-size:10px;fill:#5A5A5A}}
.card{{border:1px solid #E4E4E7;padding:14px 16px;margin:0 0 14px}}
@media(max-width:900px){{.grid2{{grid-template-columns:1fr}}}}
</style></head><body>
<div class="wrap">
<header>
  <div class="brand">ISUZU · ISZE</div>
  <h1>Pricing full analysis pack</h1>
  <div class="sub">Year-matched PR00 realization, ZPR1 (UTI ≠ UMI), AIM billing windows,
  PMS <b>total</b> capture, GPS €/UIO, AIM×GPS quadrants, genuine/BVP mix (extra),
  KPI MOS stock days (not elasticity), NO_LIST gap, VPACC hooks, and integrity score.</div>
  <div class="stamp">Built {UTC_NOW} · Integrity <b>{integ['score']}/100</b> ({integ['band']}) ·
  <span class="badge">Provisional — not externally quotable</span> ·
  PRISM verification {'green' if payload['verification']['ok'] else 'check'}</div>
  <div class="toc" style="margin-top:14px">
    <a href="#s1">1 Realization</a>
    <a href="#s2">2 ZPR1</a>
    <a href="#s3">3 AIM</a>
    <a href="#s4">4 PMS/GPS</a>
    <a href="#s5">5 Mix</a>
    <a href="#s6">6 MOS</a>
    <a href="#s7">7 NO_LIST</a>
    <a href="#s8">8 VPACC</a>
    <a href="#s9">9 Integrity</a>
    <a href="#s10">10 Risks</a>
  </div>
</header>

<div class="callout"><b>Conclusion.</b> {conclusion}</div>

<div class="kpis">
  <div class="kpi amber"><div class="v">{integ['score']}</div><div class="l">Integrity / 100</div></div>
  <div class="kpi"><div class="v">{pct(cy25.get('realization_pct'))}</div><div class="l">CY2025 realization</div></div>
  <div class="kpi amber"><div class="v">{pct(cy25.get('coverage_pct'))}</div><div class="l">CY2025 list coverage</div></div>
  <div class="kpi amber"><div class="v">{eur(gap.get('gap_eur',0))}</div><div class="l">NO_LIST gap CY2025</div></div>
  <div class="kpi"><div class="v">{pct_frac(pms25_cap.get('capture_rate'))}</div><div class="l">PMS total capture CY2025</div></div>
  <div class="kpi"><div class="v">{eur(payload['gps'].get('uti_spu'))} / {eur(payload['gps'].get('umi_spu'))}</div><div class="l">GPS SPU UTI / UMI</div></div>
  <div class="kpi amber"><div class="v">{zf.get('umi_yoy_2025_2026_median_pct')}%</div><div class="l">UMI ZPR1 YoY 25→26</div></div>
  <div class="kpi"><div class="v">{payload['findings_core']['vpacc'].get('open_or_in_progress','—')}</div><div class="l">VPACC open actions</div></div>
</div>

<h2 id="s1"><span class="num">01</span>Year-matched PR00 realization</h2>
<p class="lead">Billing net ÷ (qty × year PR00 list) on matched lines only. Coverage = matched € / all parts €.
2026 YTD uses current IE40 PR00 extract. Status: provisional QA pending. € figures are euros (M = millions).</p>
<div class="grid2">
  <div class="card"><h3 style="margin:0 0 8px;font-size:13px">List coverage %</h3>{cov_chart}</div>
  <div class="card"><h3 style="margin:0 0 8px;font-size:13px">Realization % (matched)</h3>{real_chart}</div>
</div>
<table><thead><tr><th>Year</th><th>Period</th><th class="n">Parts €</th><th class="n">Coverage</th>
<th class="n">Realization</th><th class="n">NO_LIST €</th><th>Billing end</th></tr></thead>
<tbody>{rows_net()}</tbody></table>
<p class="lead">By distributor (CY2025, top by parts €) — UTI and UMI shown as separate rows when present.</p>
<table><thead><tr><th>DB</th><th class="n">Parts €</th><th class="n">Coverage</th><th class="n">Realization</th><th class="n">NO_LIST €</th></tr></thead>
<tbody>{rows_db()}</tbody></table>

<h2 id="s2"><span class="num">02</span>ZPR1 vs PR00 (UTI ≠ UMI — never blend)</h2>
<p class="lead">Customer-condition list vs network PR00 for the same year. Payer 2372 included when present.
<strong>Flag:</strong> {zf['suspicion']}</p>
<table><thead><tr><th>Year</th><th>Payer</th><th class="n">PNs vs PR00</th><th class="n">Median vs PR00</th><th class="n">P25–P75</th></tr></thead>
<tbody>{rows_z()}</tbody></table>
<table><thead><tr><th>YoY</th><th>Payer</th><th class="n">Common PNs</th><th class="n">Median ZPR1 YoY</th></tr></thead>
<tbody>{rows_zy()}</tbody></table>

<h2 id="s3"><span class="num">03</span>AIM lens — billing CY + FY windows</h2>
<p class="lead">{payload['aim']['note']}. Fiscal rule: FY = Apr–Mar.
Max billing date: {payload['aim']['meta'].get('max_billing_date','—')}.</p>
{aim_chart}
<table><thead><tr><th>Window</th><th class="n">€</th><th class="n">Rows</th><th>Status</th></tr></thead>
<tbody>{''.join(f"<tr><td>{w['window']}</td><td class='n'>{eur(w.get('eur'))}</td><td class='n'>{w.get('rows',0):,}</td><td class='sm'>{w.get('status')}</td></tr>" for w in payload['aim']['windows'])}</tbody></table>
<p class="lead">Top distributors CY2025 billing €</p>
<table><thead><tr><th>DB</th><th class="n">Net sales €</th></tr></thead>
<tbody>{rows_aim_top()}</tbody></table>

<h2 id="s4"><span class="num">04</span>PMS total capture + GPS SPU + AIM×GPS</h2>
<p class="lead"><b>Primary = PMS total capture</b> (genuine + BVP). Genuine-only is not the headline.
GPS €/UIO from PRISM derived. Scatter: GPS SPU vs PMS total capture (CY2025). Dashed lines = sample medians.
Israel: UTI and UMI plotted as two points — never averaged.</p>
<div class="card">{scatter}</div>
<p class="lead">Network PMS total capture by year (qty actual ÷ expected, all categories rolled).</p>
<table><thead><tr><th>Year</th><th class="n">Capture</th><th class="n">Actual qty</th><th class="n">Expected qty</th><th class="n">Rev €</th></tr></thead>
<tbody>{''.join(f"<tr><td>{int(r['year'])}</td><td class='n'>{pct_frac(r['capture_rate'])}</td><td class='n'>{float(r['actual_qty']):,.0f}</td><td class='n'>{float(r['expected_qty']):,.0f}</td><td class='n'>{eur(r['actual_rev_eur'])}</td></tr>" for r in pms_net)}</tbody></table>
<div class="grid2">
<div>
<p class="lead">Top DB by PMS total capture CY2025</p>
<table><thead><tr><th>DB</th><th class="n">Capture</th><th class="n">Actual</th><th class="n">Expected</th><th class="n">Rev €</th></tr></thead>
<tbody>{rows_pms()}</tbody></table>
</div>
<div>
<p class="lead">GPS €/UIO CY2025 (top)</p>
<table><thead><tr><th>DB</th><th>Country</th><th class="n">Sales €</th><th class="n">UIO</th><th class="n">€/UIO</th><th>TL</th></tr></thead>
<tbody>{rows_gps()}</tbody></table>
</div>
</div>
<p class="lead">Israel side-by-side (never blend)</p>
<table><thead><tr><th>DB</th><th class="n">GPS €/UIO</th><th class="n">PMS total capture</th><th>Quadrant</th></tr></thead>
<tbody>{israel_note}</tbody></table>
<p class="lead">AIM×GPS quadrant table CY2025</p>
<table><thead><tr><th>DB</th><th class="n">GPS SPU</th><th class="n">PMS capture</th><th>Quadrant</th></tr></thead>
<tbody>{rows_quad()}</tbody></table>

<h2 id="s5"><span class="num">05</span>Mix genuine / BVP (extra lens)</h2>
<p class="lead">Network BVP share of PMS-family € CY2025: <b>{pct_frac(payload['mix']['network_bvp_share_eur_cy2025'])}</b>.
This is a mix quality lens — not a substitute for total capture.</p>
<table><thead><tr><th>Family</th><th class="n">Genuine €</th><th class="n">BVP €</th><th class="n">BVP share</th></tr></thead>
<tbody>{rows_mix()}</tbody></table>
<p class="lead">PMS genuine/BVP revenue lens CY2025 (extra): genuine {eur(payload['pms']['genuine_bvp_extra_lens_cy2025']['genuine_rev_eur'])} ·
BVP {eur(payload['pms']['genuine_bvp_extra_lens_cy2025']['bvp_rev_eur'])} ·
BVP share {pct_frac(payload['pms']['genuine_bvp_extra_lens_cy2025']['bvp_share_of_lens_eur'])}.</p>

<h2 id="s6"><span class="num">06</span>MOS response 2025–26 (not elasticity)</h2>
<p class="lead"><b>Not market elasticity.</b> KPI “Days of Parts in Stock” is a warehouse / ordering response signal.
ISZE→DB volume elasticity remains non-quotable. Source: KPI Master File June 2026 · Parts Handling.</p>
<table><thead><tr><th>Distributor</th><th class="n">n 2025</th><th class="n">Avg MOS 2025</th>
<th class="n">n 2026 YTD</th><th class="n">Avg MOS 2026</th><th class="n">Δ days</th></tr></thead>
<tbody>{rows_mos()}</tbody></table>

<h2 id="s7"><span class="num">07</span>NO_LIST gap CY2025</h2>
<p class="lead">{gap.get('pn_count')} part numbers · {eur(gap.get('gap_eur',0))} ·
{100*gap.get('gap_share_of_parts',0):.1f}% of CY2025 parts without usable PR00 price.
Top SKU includes oil mislabelled as “Rim” in master description (known SKU issue — oil, not rim).</p>
<table><thead><tr><th>Part</th><th>Description</th><th class="n">CY2025 €</th><th>Reason</th></tr></thead>
<tbody>{rows_gap()}</tbody></table>

<h2 id="s8"><span class="num">08</span>VPACC actions → metric hooks</h2>
<p class="lead">FY2027 July update — {payload['findings_core']['vpacc'].get('total_actions')} actions;
open/in progress <b>{payload['findings_core']['vpacc'].get('open_or_in_progress')}</b>;
completed &amp; eval <b>{payload['findings_core']['vpacc'].get('completed_and_eval')}</b>.
Join quality is thin.</p>
<table><thead><tr><th>Stream</th><th class="n">Actions</th><th>Metric hooks</th><th>Join</th></tr></thead>
<tbody>{rows_vp()}</tbody></table>

<h2 id="s9"><span class="num">09</span>Integrity score</h2>
<p class="lead">Start {integ.get('start',100)}; deductions sum −{integ.get('deduction_sum')};
score <b>{integ['score']}</b>; band <b>{integ['band']}</b>; external quote: <b>no</b>.</p>
<table><thead><tr><th>Pts</th><th>Item</th><th>Detail</th></tr></thead>
<tbody>{rows_ded()}</tbody></table>
<p class="lead">Open PRISM data notes (not silently “fixed” here)</p>
<table><thead><tr><th>Flag</th><th>Status</th><th>Note</th></tr></thead>
<tbody>{rows_flags()}</tbody></table>

<h2 id="s10"><span class="num">10</span>Top risks &amp; next asks</h2>
<div class="grid2">
<div class="card"><h3 style="margin:0 0 8px;font-size:14px">Risks</h3><ul class="bul">{rows_risk()}</ul></div>
<div class="card"><h3 style="margin:0 0 8px;font-size:14px">Next asks</h3><ul class="bul">{rows_asks()}</ul></div>
</div>

<div class="foot">
shared pack · English · No internal model nicknames · UTI and UMI kept separate ·
PMS total capture is primary · MOS labelled not elasticity · Integrity provisional.<br>
Sources: sales_fact / PR00 &amp; ZPR1 year parquets · aim_billing_windows · pms_capture_by_db_year ·
gps_spu_by_distributor · aim_gps_matrix · mix_genuine_bvp_pms · no_pr00_gap_cy2025_ranked ·
KPI Master File · vpacc_fy2027_action_plan_july · green _verification_report where applicable.<br>
Built {UTC_NOW} · Related: Pricing History Findings · Pricing BI
</div>
</div>
</body></html>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def main() -> int:
    print("Synthesizing full pricing analysis pack…")
    payload = synthesize()
    meta_path = DER / "pricing_full_analysis_pack.meta.json"
    meta_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(f"  wrote {meta_path}")

    dash_json = DASH / "pricing_full_analysis_pack.json"
    DASH.mkdir(parents=True, exist_ok=True)
    # compact for dashboard folder — drop huge nested duplicates if needed
    dash_json.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    html_path = DASH / "ISZE_Pricing_Full_Analysis_Pack.html"
    write_html(payload, html_path)
    print(f"HTML -> {html_path} ({html_path.stat().st_size:,} bytes)")

    # Also refresh the thin findings HTML with fixed € formatting + pointer
    findings_html = DASH / "ISZE_Pricing_History_Findings_Dashboard.html"
    stub = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE · Pricing History Findings</title>
<style>
body{{margin:0;font:15px/1.55 "Segoe UI",Arial,sans-serif;color:#1A1A1A}}
.wrap{{max-width:720px;margin:40px auto;padding:0 24px}}
.brand{{font:800 13px/1 Arial Black,Arial;letter-spacing:.22em;color:#CC0E1E;margin-bottom:14px}}
a{{color:#CC0E1E;font-weight:700}}
.callout{{border-left:4px solid #B45309;background:#FEF8F0;padding:14px 16px}}
</style></head><body><div class="wrap">
<div class="brand">ISUZU · ISZE</div>
<h1>Pricing history findings</h1>
<div class="callout">This stub is superseded by the full analysis pack.<br>
Open: <a href="ISZE_Pricing_Full_Analysis_Pack.html">ISZE_Pricing_Full_Analysis_Pack.html</a><br>
Integrity: <b>{payload['integrity']['score']}/100</b> ({payload['integrity']['band']}) · Built {UTC_NOW}
</div></div></body></html>
"""
    findings_html.write_text(stub, encoding="utf-8")
    print(f"Stub pointer -> {findings_html}")
    print(f"INTEGRITY SCORE: {payload['integrity']['score']}/100 ({payload['integrity']['band']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
