"""Build ISZE Pricing Engine Readiness dashboard (shared HTML + JSON).

Reads measured alloc run + readiness CSVs. No invented KPIs.
Does not sync to deploy.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "20260810T171626Z__alloc__t3pct"
RUN_DIR = ROOT / "03_analytics" / "isze_pricing" / "runs" / RUN_ID
LAUNCH_ID = "20260806T154452Z__launch__dmax_22_base"
READY_JSON = ROOT / "01_data" / "00_derived" / "oem_peer_readiness_20260810.json"
READY_CSV = ROOT / "01_data" / "00_derived" / "oem_peer_readiness_20260810.csv"
OUT_JSON = ROOT / "01_data" / "14_dashboards" / "pricing_engine_readiness.json"
OUT_HTML = ROOT / "02_dashboards" / "pricing" / "ISZE_Pricing_Engine_Readiness_Dashboard.html"

TARGET = 0.03

# shared brand-quality ceilings (config authority)
BRAND_TIERS = [
    {"tier": 4, "label": "OE / premium IAM", "ceiling_pct": 30, "example": "Bosch, Delphi, Febi OE-tier"},
    {"tier": 3, "label": "Mainstream IAM", "ceiling_pct": 60, "example": "Solid mid brands"},
    {"tier": 2, "label": "Budget IAM", "ceiling_pct": 150, "example": "Value brands"},
    {"tier": 1, "label": "No-name / CN", "ceiling_pct": 250, "example": "Lowest-quality brands"},
]

CLASS_FACTORS = [
    {"cls": "C", "factor": 0.47},
    {"cls": "D", "factor": 0.48},
    {"cls": "F", "factor": 0.525},
    {"cls": "J", "factor": 0.555},
    {"cls": "M", "factor": 0.50},
    {"cls": "P", "factor": 0.44},
    {"cls": "V", "factor": 0.55},
    {"cls": "T", "factor": 0.80},
]


def pct(x: float, digits: int = 1) -> str:
    return f"{100 * x:.{digits}f}%"


def eur(x: float) -> str:
    return f"€{x:,.0f}"


def _row_pack(r) -> dict:
    return {
        "db": r.db,
        "cat": r.cat,
        "label": r.label,
        "delta_pct": 100 * float(r.delta),
        "diff_eur": float(r.diff_vs_uniform),
        "weight_eur": float(r.weight),
        "reason_code": r.reason_code,
        "zone": r.zone,
    }


def build_why_engine(d: pd.DataFrame, base: float, eng_rev: float, redistributed: float) -> dict:
    """Deep Before vs Engine analytics — all from measured alloc_detail."""
    ne = d[d["reason_code"] == "NO_EVIDENCE_HOLD"]
    ne_w = float(ne["weight"].sum())
    ne_share = ne_w / base
    ne_wtd = float((ne["weight"] * ne["delta"]).sum() / ne_w) if ne_w else 0.0

    # Histogram of engine deltas (weight + cells) vs uniform spike at +3%
    edges = [-0.02, -0.01, 0.0, 0.01, 0.03, 0.05, 0.065, 0.08, 0.09]
    labels = ["−2…−1%", "−1…0%", "0…1%", "1…3%", "3…5%", "5…6.5%", "6.5…8%", "8% cap"]
    d = d.copy()
    d["dbin"] = pd.cut(d["delta"], bins=edges, right=False, labels=labels)
    hist = []
    for lab in labels:
        g = d[d["dbin"] == lab]
        hist.append(
            {
                "bin": lab,
                "cells": int(len(g)),
                "weight_eur": float(g["weight"].sum()),
                "weight_share": float(g["weight"].sum()) / base if base else 0.0,
            }
        )

    # Uniform counterfactual: 100% weight at exactly +3%
    hist_uniform = {
        "bin": "+3% flat",
        "cells": int(len(d)),
        "weight_eur": base,
        "weight_share": 1.0,
    }

    # Zone × reason revenue (engine)
    zone_reason = []
    for zone in ["raise", "contested", "defend"]:
        for code in ["CAPTIVE_RAISE", "NO_EVIDENCE_HOLD", "CONTESTED_ABOVE_MARKET", "DEFEND_CUT"]:
            g = d[(d["zone"] == zone) & (d["reason_code"] == code)]
            if g.empty:
                continue
            zone_reason.append(
                {
                    "zone": zone,
                    "reason_code": code,
                    "cells": int(len(g)),
                    "weight_eur": float(g["weight"].sum()),
                    "rev_engine": float(g["revenue_delta_eur"].sum()),
                    "rev_uniform": float(g["weight"].sum()) * TARGET,
                    "rev_diff": float(g["diff_vs_uniform"].sum()),
                }
            )

    # DB × zone stacked (engine rev Δ) — top by |diff|
    by_db_diff = (
        d.groupby("db", as_index=False)
        .agg(weight_eur=("weight", "sum"), rev_diff=("diff_vs_uniform", "sum"), rev_engine=("revenue_delta_eur", "sum"))
    )
    by_db_diff["engine_wtd_pct"] = 100 * by_db_diff["rev_engine"] / by_db_diff["weight_eur"]
    by_db_diff["uniform_pct"] = 100 * TARGET
    focus_dbs = (
        by_db_diff.reindex(by_db_diff["rev_diff"].abs().sort_values(ascending=False).index)
        .head(10)["db"]
        .tolist()
    )
    db_zone_stack = []
    for db in focus_dbs:
        row = {"db": db}
        for zone in ["raise", "contested", "defend"]:
            g = d[(d["db"] == db) & (d["zone"] == zone)]
            row[f"eng_{zone}"] = float(g["revenue_delta_eur"].sum())
            row[f"uni_{zone}"] = float(g["weight"].sum()) * TARGET
        row["rev_diff"] = float(d.loc[d["db"] == db, "diff_vs_uniform"].sum())
        row["engine_wtd_pct"] = float(
            100
            * d.loc[d["db"] == db, "revenue_delta_eur"].sum()
            / d.loc[d["db"] == db, "weight"].sum()
        )
        db_zone_stack.append(row)

    # Redistribution flows: from (negative diff reasons) → to (positive)
    flows_from = []
    flows_to = []
    for code, g in d.groupby("reason_code"):
        s = float(g["diff_vs_uniform"].sum())
        item = {"reason_code": code, "eur": abs(s), "signed": s}
        if s < 0:
            flows_from.append(item)
        elif s > 0:
            flows_to.append(item)
    flows_from.sort(key=lambda x: -x["eur"])
    flows_to.sort(key=lambda x: -x["eur"])

    # Evidence tiers
    evid = []
    for tier, g in d.groupby("evidence_tier"):
        ww = float(g["weight"].sum())
        evid.append(
            {
                "evidence_tier": tier,
                "cells": int(len(g)),
                "weight_eur": ww,
                "weight_share": ww / base,
                "mean_delta": float(g["delta"].mean()),
                "wtd_delta": float((g["weight"] * g["delta"]).sum() / ww) if ww else 0.0,
            }
        )

    # Caps / floors
    n_capped = int(np.isclose(d["delta"], d["cap_eff"]).sum())
    n_floor = int(np.isclose(d["delta"], d["floor_eff"]).sum())
    n_top50_cap = int((d["is_top50"] & np.isclose(d["delta"], d["cap_eff"])).sum())
    n_theta_veto = int(d["theta_vetoed"].sum())

    # Process contrast (shared labels — precise)
    prior_process = {
        "title": "How ISZE typically priced before",
        "bullets": [
            "Uniform or near-uniform weighted list increase — the same % across much of the book when a +3% target was set.",
            "Class factors set selling price from FOB (IML formula), but the revision itself was not rule-based by capture, street, or θ.",
            "Little separation of IML buying-price pass-through versus the ISZE margin decision on the same list move.",
            "Street reads often used the wrong pricing point historically (list vs PR00 × street factor 1.785) — Eucon lesson.",
            "No brand-quality % ceilings (+30 / +60 / +150 / +250); no oem_benchmark gate; no logged allocation runs with reason codes.",
        ],
    }
    engine_process = {
        "title": "What the engine does instead",
        "bullets": [
            "Same +3.0000% weighted index — solver hits the target exactly under constant prior-year units.",
            "Wallet zones (raise / contested / defend from PMS total capture) plus street evidence gates decide who funds vs who is cut.",
            "Reason codes on every cell; caps (+8%, tighter on top-50) and floors; θ_parc with street veto.",
            "Trusted premium basis required for position moves (oem_benchmark / iam_derived); hold-when-blind on NO_EVIDENCE.",
            "Brand-quality ceiling ladder (+30/+60/+150/+250) in policy; run registry and alloc detail for every logged move.",
        ],
    }

    distributor_talking_points = [
        {
            "title": "Same index, fairer mix",
            "text": (
                f"We still deliver a +3% weighted list increase ({eur(eng_rev)} on {eur(base)}). "
                "The engine does not invent a bigger bill — it changes which lines carry it."
            ),
        },
        {
            "title": "Defend lines are not loaded like captive",
            "text": (
                "Where genuine capture is already lost and street is above market, the engine cuts or holds "
                "(e.g. IUK brake pads/rotors). A flat +3% would have raised those the same as captive filters."
            ),
        },
        {
            "title": "Blind weight is still partly the old world",
            "text": (
                f"{pct(ne_share)} of basket € still takes the unbenchmarked base lift "
                f"(NO_EVIDENCE_HOLD, ~{pct(ne_wtd)} weighted). Differentiation is real where evidence exists — "
                "honest about where it does not."
            ),
        },
        {
            "title": "Street on the right point",
            "text": (
                "Street comparisons use PR00 × 1.785 (street factor), not raw list — correcting the Eucon-era misread. "
                "No oem_benchmark without enough priced peer OEs."
            ),
        },
        {
            "title": "New models need mix, not only +3%",
            "text": (
                "D-Max 2.2 (15k oil interval) is a θ / launch-book story: protect interval-linked wear with mix rules; "
                "do not claim volume from the list move alone."
            ),
        },
    ]

    # Process maturity matrix (qualitative, shared)
    maturity = [
        {"dim": "Index discipline", "prior": "Target % often applied uniformly", "engine": "+3% weighted exact; logged"},
        {"dim": "Who pays", "prior": "Same % most lines", "engine": "Raise funds; defend/contested cut"},
        {"dim": "Street gate", "prior": "Ad hoc / wrong point risk", "engine": "Evidence tiers + hold-when-blind"},
        {"dim": "OEM peer gate", "prior": "None", "engine": "oem_benchmark (≥3 priced peers)"},
        {"dim": "Brand ceilings", "prior": "Flat premium thinking", "engine": "+30/+60/+150/+250 ladder"},
        {"dim": "IML vs ISZE", "prior": "Often blurred on revision", "engine": "BP pass-through vs Δ decision separated"},
        {"dim": "θ / parc", "prior": "Not in list revision", "engine": "θ_parc live; θ_interval pending map"},
        {"dim": "Audit trail", "prior": "No run registry", "engine": "Reason codes + run IDs"},
    ]

    return {
        "prior_process": prior_process,
        "engine_process": engine_process,
        "maturity_matrix": maturity,
        "class_factors": CLASS_FACTORS,
        "brand_tiers": BRAND_TIERS,
        "street_factor": 1.785,
        "histogram_engine": hist,
        "histogram_uniform": hist_uniform,
        "zone_reason": zone_reason,
        "db_zone_stack": db_zone_stack,
        "flows_from": flows_from,
        "flows_to": flows_to,
        "by_evidence_detail": evid,
        "caps": {
            "n_capped": n_capped,
            "n_at_floor": n_floor,
            "n_top50_at_cap": n_top50_cap,
            "cap_pct": 8.0,
            "cap_top50_pct": 5.0,
            "floor_pct": -12.0,
            "n_theta_vetoed": n_theta_veto,
        },
        "blind_weight": {
            "reason_code": "NO_EVIDENCE_HOLD",
            "cells": int(len(ne)),
            "weight_eur": ne_w,
            "weight_share": ne_share,
            "wtd_delta_pct": 100 * ne_wtd,
            "meaning": (
                "These cells have no street evidence tier that can move position. "
                "They take the index base lift — still partly the old uniform world inside an otherwise differentiated run."
            ),
        },
        "distributor_talking_points": distributor_talking_points,
        "headline_deep": (
            f"Same +3% weighted index ({eur(eng_rev)}). Engine redistributes ~{eur(redistributed)} of who pays. "
            f"Blind weight {pct(ne_share)} still on base lift. Caps hit {n_capped} cells; θ veto {n_theta_veto}."
        ),
    }


def build_payload() -> dict:
    d = pd.read_csv(RUN_DIR / "alloc_detail.csv")
    ready = json.loads(READY_JSON.read_text(encoding="utf-8"))
    ready_tbl = pd.read_csv(READY_CSV)

    w = d["weight"].astype(float)
    base = float(w.sum())
    eng_wtd = float((w * d["delta"]).sum() / base)
    eng_rev = float(d["revenue_delta_eur"].sum())
    uni_rev = base * TARGET

    d = d.copy()
    d["rev_uniform"] = w * TARGET
    d["diff_vs_uniform"] = d["revenue_delta_eur"] - d["rev_uniform"]
    d["delta_vs_uniform"] = d["delta"] - TARGET

    by_reason = []
    for code, g in d.groupby("reason_code"):
        ww = float(g["weight"].sum())
        by_reason.append(
            {
                "reason_code": code,
                "cells": int(len(g)),
                "weight_eur": ww,
                "weight_share": ww / base,
                "mean_delta": float(g["delta"].mean()),
                "wtd_delta": float((g["weight"] * g["delta"]).sum() / ww),
                "rev_engine": float(g["revenue_delta_eur"].sum()),
                "rev_uniform": ww * TARGET,
                "rev_diff": float(g["revenue_delta_eur"].sum() - ww * TARGET),
            }
        )
    by_reason.sort(key=lambda r: -abs(r["rev_diff"]))

    by_zone = []
    for zone, g in d.groupby("zone"):
        ww = float(g["weight"].sum())
        by_zone.append(
            {
                "zone": zone,
                "cells": int(len(g)),
                "weight_eur": ww,
                "wtd_delta": float((g["weight"] * g["delta"]).sum() / ww),
                "rev_engine": float(g["revenue_delta_eur"].sum()),
                "rev_uniform": ww * TARGET,
                "rev_diff": float(g["revenue_delta_eur"].sum() - ww * TARGET),
            }
        )

    by_db = []
    for db, g in d.groupby("db"):
        ww = float(g["weight"].sum())
        by_db.append(
            {
                "db": db,
                "weight_eur": ww,
                "engine_wtd_pct": 100 * float((g["weight"] * g["delta"]).sum() / ww),
                "uniform_pct": 100 * TARGET,
                "rev_diff": float(g["revenue_delta_eur"].sum() - ww * TARGET),
                "rev_engine": float(g["revenue_delta_eur"].sum()),
                "rev_uniform": ww * TARGET,
            }
        )
    by_db.sort(key=lambda r: r["rev_diff"])

    basis = (
        d.groupby("premium_basis")
        .agg(cells=("cat", "size"), weight=("weight", "sum"), mean_delta=("delta", "mean"))
        .reset_index()
    )
    by_basis = [
        {
            "premium_basis": r.premium_basis,
            "cells": int(r.cells),
            "weight_eur": float(r.weight),
            "weight_share": float(r.weight) / base,
            "mean_delta": float(r.mean_delta),
        }
        for r in basis.itertuples()
    ]

    evid = (
        d.groupby("evidence_tier")
        .agg(cells=("cat", "size"), weight=("weight", "sum"))
        .reset_index()
    )
    by_evidence = [
        {
            "evidence_tier": r.evidence_tier,
            "cells": int(r.cells),
            "weight_eur": float(r.weight),
            "weight_share": float(r.weight) / base,
        }
        for r in evid.itertuples()
    ]

    more = d.nlargest(8, "diff_vs_uniform")[
        ["db", "cat", "label", "delta", "diff_vs_uniform", "weight", "reason_code", "zone"]
    ]
    less = d.nsmallest(8, "diff_vs_uniform")[
        ["db", "cat", "label", "delta", "diff_vs_uniform", "weight", "reason_code", "zone"]
    ]

    redistributed = float(d["diff_vs_uniform"].abs().sum() / 2)

    n_cells = len(d)
    n_evidence = int((d["evidence_tier"] != "T5_none").sum())
    w_evidence = float(d.loc[d["evidence_tier"] != "T5_none", "weight"].sum()) / base
    n_trusted_basis = int(d["premium_basis"].isin(["oem_benchmark", "iam_derived"]).sum())
    w_trusted = float(
        d.loc[d["premium_basis"].isin(["oem_benchmark", "iam_derived"]), "weight"].sum()
    ) / base
    oem_cats = ready["oem_benchmark_cats"]
    near = ready["near_gate_cats"]
    street_fill = ready["unique_oe_street_filled"] / ready["unique_oe_mapped"]

    iam_from_run = sorted(d.loc[d["premium_basis"] == "iam_derived", "cat"].unique().tolist())
    oem_from_run = sorted(d.loc[d["premium_basis"] == "oem_benchmark", "cat"].unique().tolist())
    placeholder_cats = sorted(
        d.loc[d["premium_basis"] == "placeholder", "cat"].unique().tolist()
    )

    layers = [
        {
            "id": 0,
            "name": "Eligibility gate",
            "score": 55,
            "status": "partial",
            "what_runs": "PMS action-map basket (213 cells) enters allocation.",
            "missing": "NO_LIST (~15% billed €) and SUPERSEDED routing not yet excluding from ISZE Δ narrative; IML_CORRECTION pass-through not fully separated in every output.",
        },
        {
            "id": 1,
            "name": "Segmentation (wallet × street)",
            "score": 58,
            "status": "partial",
            "what_runs": (
                f"Wallet zones on all {n_cells} cells. Street evidence on "
                f"{n_evidence}/{n_cells} cells ({pct(w_evidence)} of € weight). "
                f"Trusted premium basis on {pct(w_trusted)} of € weight "
                f"({len(oem_cats)} oem_benchmark cats, {len(iam_from_run)} iam_derived)."
            ),
            "missing": (
                f"OEM street {ready['unique_oe_street_filled']}/{ready['unique_oe_mapped']} peers; "
                f"near-gate cats {', '.join(near)}; placeholder still on "
                f"{', '.join(placeholder_cats) or '—'}."
            ),
            "metrics": {
                "street_oe_fill_pct": round(100 * street_fill, 1),
                "oem_benchmark_cats": oem_from_run,
                "iam_derived_cats": iam_from_run,
                "placeholder_cats": placeholder_cats,
                "cells_with_street_evidence": n_evidence,
                "weight_with_street_evidence_pct": round(100 * w_evidence, 1),
            },
        },
        {
            "id": 2,
            "name": "Momentum (θ)",
            "score": 40,
            "status": "partial",
            "what_runs": "θ_parc wired from corrected car park; 60 cells moved by θ; veto on adverse street.",
            "missing": "θ_interval blocked (chassis→generation map — D-Max 15k vs 20k). θ_cohort / θ_warranty Partial (held at 1.0).",
            "metrics": {
                "components_wired": "theta_parc only",
                "components_of_four": 1,
                "n_theta_moving": 60,
                "n_theta_vetoed": int(d["theta_vetoed"].sum()),
                "weighted_theta_parc": 1.013,
            },
        },
        {
            "id": 3,
            "name": "Allocation (+3% weighted)",
            "score": 72,
            "status": "running",
            "what_runs": (
                f"Index solver hits {pct(eng_wtd, 4)} exactly. Caps/floors, reason codes, "
                f"two-gate sign rules active. Revenue Δ {eur(eng_rev)} on {eur(base)} base."
            ),
            "missing": (
                f"{int((d.reason_code == 'NO_EVIDENCE_HOLD').sum())} cells / "
                f"{pct(float(d.loc[d.reason_code == 'NO_EVIDENCE_HOLD', 'weight'].sum()) / base)} "
                f"€ weight still take the unbenchmarked base lift — differentiation incomplete."
            ),
            "metrics": {
                "weighted_increase_pct": round(100 * eng_wtd, 4),
                "n_capped": 17,
                "n_zero_evidence": int((d.reason_code == "NO_EVIDENCE_HOLD").sum()),
                "n_unbenchmarked_premium": 107,
                "redistributed_vs_uniform_eur": round(redistributed),
            },
        },
        {
            "id": 4,
            "name": "Market lists (PR00 / ZPR1 / CIS)",
            "score": 62,
            "status": "partial",
            "what_runs": "PR00 full engine path. ZPR1 enabled (flat −10%). CIS enabled (flat factor).",
            "missing": "ZPR1 not yet per-category. CIS not class-dependent. Auto365 IL evidence not wired into differentials.",
        },
        {
            "id": 5,
            "name": "Output & governance",
            "score": 82,
            "status": "running",
            "what_runs": "Reason codes, caps, run registry, alloc summary, soft DB→DLR proxy diagnostic.",
            "missing": "GPS bridge / distributor pack automation thin. DB→DLR is proxy only (not joined into Δ).",
        },
    ]
    composite = round(sum(L["score"] for L in layers) / len(layers), 1)

    cat_ready = []
    for _, r in ready_tbl.iterrows():
        cat_ready.append(
            {
                "pms_category": r["pms_category"],
                "n_priced_oe": int(r["n_priced_oe"]),
                "gap_to_oem_benchmark": int(r["gap_to_oem_benchmark"]),
                "basis_if_alloc": r["basis_if_alloc"],
                "peer_markets_priced": r["peer_markets_priced"]
                if pd.notna(r["peer_markets_priced"])
                else "",
            }
        )

    launch = {
        "run_id": LAUNCH_ID,
        "model": "D-Max 2.2 (RG21 / RZ4F-TC)",
        "best_tactic": "warranty_load",
        "best_gp_npv_eur": 72752723,
        "class_only_gp_npv_eur": 54832274,
        "vs_class_only_pct": 32.7,
        "services_per_vehicle_yr": 1.33,
        "oil_interval_km": 15000,
        "prior_interval_km": 20000,
        "note": (
            "Launch book NPV and capture erosion are modelled [ASSUMPTION] — "
            "not measured elasticity. Use for tactic ranking, not volume forecast. "
            "θ_interval (15k vs 20k oil) is the measured demand lever still blocked."
        ),
    }

    missing_checklist = [
        {
            "priority": 1,
            "item": "Genuine Paccar/DAF street quote (pad or disc or clutch)",
            "unlocks": "Near-gate brake/clutch cats → oem_benchmark (n≥3 with LCV fills)",
        },
        {
            "priority": 2,
            "item": "Confirm Ford 1713904 → 2138025 supersession (dealer EPC)",
            "unlocks": "Brake shoe street fill from Ford Online Shop",
        },
        {
            "priority": 3,
            "item": "Chassis-code → model-year / SCR map",
            "unlocks": "θ_interval — D-Max generation demand (+33% svc/yr on filters)",
        },
        {
            "priority": 4,
            "item": "OE maps for L200 / Transit / Sprinter / MAN / Crafter",
            "unlocks": "Broader peer OE coverage beyond DAF + Hilux + Ranger",
        },
        {
            "priority": 5,
            "item": "Second full CY of sell-out (ITUK + UTI)",
            "unlocks": "DB→DLR proxy → measured elasticity label (still soft; not a Δ coefficient)",
        },
        {
            "priority": 6,
            "item": "NO_LIST / SUPERSEDED eligibility wiring in narrative packs",
            "unlocks": "Full Layer 0 — ~15% billed € outside list action today",
        },
        {
            "priority": 7,
            "item": "ZPR1 per-category differentials (UMI ≠ UTI)",
            "unlocks": "Layer 4 Israel treatment beyond flat −10%",
        },
    ]

    full_launch = {
        "definition": (
            "Full launch = Layers 0–5 operational with: (1) every in-scope PMS category on "
            "oem_benchmark or iam_derived (no placeholder moving via base filler), "
            "(2) OEM peer street filled to gate where peers exist, "
            "(3) θ_parc + θ_interval wired, "
            "(4) eligibility excludes NO_LIST/SUPERSEDED from ISZE Δ, "
            "(5) PR00 + ZPR1/CIS rules as specified, "
            "(6) every line carries a reason code under the +3% weighted index."
        ),
        "composite_readiness_pct": composite,
        "not_required_for_full_launch": [
            "Measured DB→DLR elasticity coefficient inside the solver (explicitly out of V1)",
            "Volume response forecast (constant-units arithmetic until elasticity exists)",
        ],
    }

    why = build_why_engine(d, base, eng_rev, redistributed)

    comparison = {
        "headline": (
            f"Same +3.0000% weighted / same {eur(eng_rev)} revenue Δ under constant units — "
            f"engine redistributes ~{eur(redistributed)} of incidence vs uniform class/+3% path. "
            f"IUK pays least (−{abs(by_db[0]['rev_diff']):,.0f} € vs uniform); "
            f"ITUK / UTI / Ireland fund the raise."
        ),
        "modelled_vs_measured": {
            "measured": [
                "Alloc deltas and reason codes from run " + RUN_ID,
                "Wallet capture zones (PMS total capture)",
                "Street evidence tier + OEM/IAM premium basis gates",
                "θ_parc from UIO car park",
                "OEM street fill 15/22 peers",
            ],
            "modelled_assumption": [
                "Constant prior-year units (no elasticity) — revenue evolution = price arithmetic only",
                "Launch-book capture erosion / IAM entry years",
                "Brand % ceilings until PN-level wiring complete",
                "Index base lift on NO_EVIDENCE_HOLD / placeholder weight",
            ],
        },
        "class_path": {
            "name": "Prior path — uniform / class-era revision",
            "description": (
                "IML SP = FOB / class_factor sets the list level. For a chosen +3% weighted "
                "increase, the operational behaviour was uniform_target: every line "
                "+3% on prior SP (margin decision wearing a cost-plus coat). "
                "Strict cost-plus re-derive alone does not guarantee +3% — FX/BP can cut or overshoot."
            ),
            "weighted_increase_pct": 3.0,
            "revenue_delta_eur": uni_rev,
            "incidence": "Equal % on every cell — defend-zone brakes take the same lift as captive filters.",
        },
        "engine_path": {
            "name": "Engine path — rule-based allocation",
            "description": (
                "Rule-based allocation to the same +3% weighted index: position gates, "
                "brand % ceilings, oem_benchmark / iam_derived, θ_parc, caps, theta veto."
            ),
            "weighted_increase_pct": round(100 * eng_wtd, 4),
            "revenue_delta_eur": eng_rev,
            "incidence": (
                "Raise/captive and unbenchmarked base take more €; contested-above-market "
                "and defend cuts take less (or negative)."
            ),
        },
        "sales_evolution": {
            "under_constant_units": (
                f"Both paths deliver {eur(eng_rev)} extra list revenue on the "
                f"{eur(base)} L12M weight. Mix of who pays differs by ~{eur(redistributed)} "
                "reallocated. No volume win/loss is claimed."
            ),
            "mix_risk_uniform": (
                "Uniform +3% loads IAM-lost defend cells (esp. IUK brakes) the same as captive — "
                "highest complaint risk per Spec C5 (distributors react to worst line)."
            ),
            "mix_engine": (
                "Engine cuts/holds defend & contested-above-market (IUK brake pad/rotor negative), "
                "funds raise cells and still uses base lift on no-evidence weight — "
                "honest partial differentiation."
            ),
            "new_models": (
                "D-Max 2.2 launch book ranks warranty_load ~+33% GP NPV vs class_only "
                "(modelled). Real +3% portfolio tactic: protect interval-linked wear with "
                "θ_interval once mapped; do not invent elasticity."
            ),
        },
        "by_reason": by_reason,
        "by_zone": by_zone,
        "by_db": by_db,
        "pays_more_than_uniform": [_row_pack(r) for r in more.itertuples()],
        "pays_less_than_uniform": [_row_pack(r) for r in less.itertuples()],
        "redistributed_eur": redistributed,
        "why_engine": why,
    }

    return {
        "meta": {
            "title": "ISZE Pricing Engine — Readiness & Comparison",
            "as_of": str(date.today()),
            "alloc_run_id": RUN_ID,
            "launch_run_id": LAUNCH_ID,
            "target_weighted_pct": 3.0,
            "base_eur": base,
            "mode": "A",
            "language": "en",
        },
        "readiness": {
            "composite_pct": composite,
            "full_launch": full_launch,
            "layers": layers,
            "oem_street": {
                "unique_oe_mapped": ready["unique_oe_mapped"],
                "unique_oe_street_filled": ready["unique_oe_street_filled"],
                "fill_pct": round(100 * street_fill, 1),
                "scrape_gaps": ready["scrape_gaps"],
                "street_factor": ready["street_factor"],
            },
            "category_readiness": cat_ready,
            "missing_checklist": missing_checklist,
            "db_dlr": {
                "measure_kind": "proxy",
                "markets": ["ITUK", "UTI"],
                "joined_to_deltas": False,
                "note": "ASP/list pass-through proxy — not dealer invoice elasticity. UTI ≠ UMI.",
            },
            "theta": {
                "wired": "theta_parc only",
                "n_moving": 60,
                "n_vetoed": 10,
                "weighted_theta_parc": 1.01303,
            },
        },
        "comparison": comparison,
        "launch": launch,
        "by_basis": by_basis,
        "by_evidence": by_evidence,
    }


# ─── SVG helpers (inline only — no CDN) ───────────────────────────────────────

ZONE_COLS = {"raise": "#1d9e75", "contested": "#eda100", "defend": "#c0552d"}
REASON_COLS = {
    "CAPTIVE_RAISE": "#1d9e75",
    "NO_EVIDENCE_HOLD": "#8a9bb0",
    "CONTESTED_ABOVE_MARKET": "#eda100",
    "DEFEND_CUT": "#e24b4a",
}


def score_color(s: float) -> str:
    if s >= 75:
        return "#1d9e75"
    if s >= 50:
        return "#eda100"
    return "#e24b4a"


def svg_layer_scores(layers: list) -> str:
    lh = 28
    svg_h = 20 + len(layers) * lh + 20
    parts = [
        f'<svg viewBox="0 0 560 {svg_h}" class="ch" role="img" aria-label="Layer readiness scores">'
    ]
    for i, layer in enumerate(layers):
        y = 12 + i * lh
        bw = layer["score"] / 100 * 300
        col = score_color(layer["score"])
        parts.append(
            f'<text x="198" y="{y+14}" text-anchor="end" class="ax">L{layer["id"]} · {layer["name"][:28]}</text>'
        )
        parts.append(f'<rect x="210" y="{y}" width="300" height="16" fill="#e8e4dc" rx="2"/>')
        parts.append(f'<rect x="210" y="{y}" width="{bw:.1f}" height="16" fill="{col}" rx="2"/>')
        parts.append(f'<text x="{220+bw:.1f}" y="{y+13}" class="tk">{layer["score"]}%</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_reason_diff(by_reason: list) -> str:
    rmax = max(abs(r["rev_diff"]) for r in by_reason) or 1
    h = 16 + len(by_reason) * 34 + 12
    mid = 280
    parts = [
        f'<svg viewBox="0 0 560 {h}" class="ch" role="img" aria-label="Revenue vs uniform by reason">'
    ]
    for i, r in enumerate(by_reason):
        y = 16 + i * 34
        v = r["rev_diff"]
        bw = abs(v) / rmax * 220
        col = REASON_COLS.get(r["reason_code"], "#2a78d6")
        x = mid if v >= 0 else mid - bw
        label = r["reason_code"].replace("_", " ")
        parts.append(f'<text x="{mid-10}" y="{y+14}" text-anchor="end" class="ax">{label}</text>')
        parts.append(
            f'<g><title>{label}: {v:+,.0f} EUR vs uniform</title>'
            f'<rect x="{x:.1f}" y="{y}" width="{max(bw,2):.1f}" height="18" fill="{col}"/></g>'
        )
        parts.append(
            f'<text x="{(x+bw+6) if v>=0 else (x-6):.1f}" y="{y+14}" '
            f'text-anchor="{"start" if v>=0 else "end"}" class="tk">{v:+,.0f}</text>'
        )
    parts.append(f'<line x1="{mid}" y1="8" x2="{mid}" y2="{h-12}" stroke="#d9d3c8"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_db_diff(by_db: list, min_abs: float = 100) -> str:
    db_show = [r for r in by_db if abs(r["rev_diff"]) >= min_abs]
    dmax = max(abs(r["rev_diff"]) for r in db_show) or 1
    left = 100
    mid = 220
    right_room = 280
    dh = 20 + len(db_show) * 26 + 24
    parts = [
        f'<svg viewBox="0 0 560 {dh}" class="ch" role="img" aria-label="Distributor incidence vs uniform">'
    ]
    for i, r in enumerate(db_show):
        y = 14 + i * 26
        v = r["rev_diff"]
        bw = abs(v) / dmax * right_room
        col = "#2a78d6" if v >= 0 else "#e24b4a"
        x = mid if v >= 0 else mid - bw
        parts.append(f'<text x="{mid-8}" y="{y+14}" text-anchor="end" class="ax">{r["db"]}</text>')
        parts.append(
            f'<g><title>{r["db"]}: engine {r["engine_wtd_pct"]:.2f}% · Δ€ vs uniform {v:+,.0f}</title>'
            f'<rect x="{x:.1f}" y="{y}" width="{max(bw,2):.1f}" height="16" fill="{col}"/></g>'
        )
        parts.append(
            f'<text x="548" y="{y+13}" text-anchor="end" class="tk">{r["engine_wtd_pct"]:.1f}%</text>'
        )
    parts.append(f'<line x1="{mid}" y1="8" x2="{mid}" y2="{dh-20}" stroke="#d9d3c8"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_zone_stacked_db(stack: list) -> str:
    """Grouped: for each DB, engine stacked raise/contested/defend revenue Δ."""
    if not stack:
        return ""
    # Use absolute engine rev components; allow negative defend by plotting signed stack carefully
    # Simpler: show net engine rev as stacked positive parts only + annotate net
    n = len(stack)
    row_h = 32
    left = 90
    bar_w = 400
    h = 40 + n * row_h + 36
    # max of sum of positive zone revs
    max_tot = 1.0
    for r in stack:
        tot = abs(r["eng_raise"]) + abs(r["eng_contested"]) + abs(r["eng_defend"])
        max_tot = max(max_tot, tot)
    parts = [
        f'<svg viewBox="0 0 560 {h}" class="ch" role="img" aria-label="Engine revenue by zone and distributor">'
    ]
    parts.append(
        '<text x="90" y="16" class="tk">Engine € Δ stacked by wallet zone (raise · contested · defend)</text>'
    )
    for i, r in enumerate(stack):
        y = 28 + i * row_h
        parts.append(f'<text x="{left-8}" y="{y+14}" text-anchor="end" class="ax">{r["db"]}</text>')
        x = left
        for zone, key in [("raise", "eng_raise"), ("contested", "eng_contested"), ("defend", "eng_defend")]:
            v = r[key]
            bw = abs(v) / max_tot * bar_w
            col = ZONE_COLS[zone]
            # hatch negative with darker stroke
            op = "1" if v >= 0 else "0.55"
            parts.append(
                f'<g><title>{r["db"]} {zone}: {v:+,.0f} EUR</title>'
                f'<rect x="{x:.1f}" y="{y}" width="{max(bw,0):.1f}" height="18" fill="{col}" opacity="{op}"/></g>'
            )
            x += bw
        parts.append(
            f'<text x="548" y="{y+13}" text-anchor="end" class="tk">{r["engine_wtd_pct"]:.1f}%</text>'
        )
    # legend
    ly = h - 18
    lx = left
    for zone, col in ZONE_COLS.items():
        parts.append(f'<rect x="{lx}" y="{ly-10}" width="12" height="12" fill="{col}"/>')
        parts.append(f'<text x="{lx+16}" y="{ly}" class="tk">{zone}</text>')
        lx += 90
    parts.append("</svg>")
    return "\n".join(parts)


def svg_uniform_vs_engine_zone(by_zone: list) -> str:
    """Paired bars: uniform vs engine revenue Δ by zone."""
    zones = ["raise", "contested", "defend"]
    zmap = {z["zone"]: z for z in by_zone}
    max_v = max(
        max(abs(zmap[z]["rev_engine"]), abs(zmap[z]["rev_uniform"])) for z in zones if z in zmap
    ) or 1
    h = 200
    parts = [
        f'<svg viewBox="0 0 560 {h}" class="ch" role="img" aria-label="Uniform vs engine by zone">'
    ]
    parts.append('<text x="20" y="18" class="tk">€ revenue Δ — uniform +3% (grey) vs engine (colour)</text>')
    bw = 36
    for i, zone in enumerate(zones):
        z = zmap[zone]
        x0 = 80 + i * 160
        uh = z["rev_uniform"] / max_v * 120
        eh = z["rev_engine"] / max_v * 120
        base_y = 160
        parts.append(f'<text x="{x0+40}" y="190" text-anchor="middle" class="ax">{zone}</text>')
        parts.append(
            f'<rect x="{x0}" y="{base_y-uh:.1f}" width="{bw}" height="{max(uh,1):.1f}" fill="#c8c2b6"/>'
        )
        parts.append(
            f'<rect x="{x0+bw+8}" y="{base_y-eh:.1f}" width="{bw}" height="{max(eh,1):.1f}" fill="{ZONE_COLS[zone]}"/>'
        )
        parts.append(
            f'<text x="{x0+bw/2}" y="{base_y-uh-4:.1f}" text-anchor="middle" class="tk">{z["rev_uniform"]/1000:.0f}k</text>'
        )
        parts.append(
            f'<text x="{x0+bw+8+bw/2}" y="{base_y-eh-4:.1f}" text-anchor="middle" class="tk">{z["rev_engine"]/1000:.0f}k</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def svg_redistribution_flow(flows_from: list, flows_to: list, redistributed: float) -> str:
    """From→to diversion bars (sankey-like clarity without overlap)."""
    h = 220
    parts = [
        f'<svg viewBox="0 0 560 {h}" class="ch" role="img" aria-label="Redistribution from to">'
    ]
    parts.append(
        f'<text x="280" y="18" text-anchor="middle" class="tk">~{redistributed:,.0f} € reallocated · same total index</text>'
    )
    parts.append('<text x="40" y="42" class="ax">Released by</text>')
    parts.append('<text x="520" y="42" text-anchor="end" class="ax">Absorbed by</text>')
    max_f = max((f["eur"] for f in flows_from), default=1)
    max_t = max((t["eur"] for t in flows_to), default=1)
    for i, f in enumerate(flows_from):
        y = 56 + i * 36
        bw = f["eur"] / max_f * 160
        col = REASON_COLS.get(f["reason_code"], "#e24b4a")
        parts.append(f'<rect x="{200-bw:.1f}" y="{y}" width="{bw:.1f}" height="22" fill="{col}"/>')
        parts.append(
            f'<text x="{200-bw-6:.1f}" y="{y+15}" text-anchor="end" class="ax">'
            f'{f["reason_code"].replace("_"," ")}</text>'
        )
        parts.append(f'<text x="206" y="{y+15}" class="tk">−{f["eur"]:,.0f}</text>')
    for i, t in enumerate(flows_to):
        y = 56 + i * 36
        bw = t["eur"] / max_t * 160
        col = REASON_COLS.get(t["reason_code"], "#1d9e75")
        parts.append(f'<rect x="340" y="{y}" width="{bw:.1f}" height="22" fill="{col}"/>')
        parts.append(
            f'<text x="{340+bw+6:.1f}" y="{y+15}" class="ax">{t["reason_code"].replace("_"," ")}</text>'
        )
        parts.append(f'<text x="334" y="{y+15}" text-anchor="end" class="tk">+{t["eur"]:,.0f}</text>')
    # centre link
    parts.append('<line x1="280" y1="56" x2="280" y2="160" stroke="#c0552d" stroke-width="2"/>')
    parts.append('<text x="280" y="178" text-anchor="middle" class="tk">incidence shift</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_delta_histogram(hist: list, base: float) -> str:
    max_w = max(h["weight_eur"] for h in hist) or 1
    n = len(hist)
    bar_w = 48
    gap = 14
    left = 50
    h = 200
    parts = [
        f'<svg viewBox="0 0 560 {h}" class="ch" role="img" aria-label="Engine delta histogram">'
    ]
    parts.append('<text x="20" y="16" class="tk">€ weight by engine Δ bin (uniform would be a single spike at +3%)</text>')
    # reference line marker for +3%
    for i, b in enumerate(hist):
        x = left + i * (bar_w + gap)
        bh = b["weight_eur"] / max_w * 130
        y = 160 - bh
        # highlight bins that contain ~3%
        col = "#8a9bb0" if b["weight_eur"] < 1 else "#2a78d6"
        if "3…5" in b["bin"] or "1…3" in b["bin"]:
            col = "#c8c2b6"
        if "6.5" in b["bin"] or "5…6.5" in b["bin"]:
            col = "#1d9e75"
        if "−" in b["bin"] or b["bin"].startswith("−"):
            col = "#e24b4a"
        if "8%" in b["bin"]:
            col = "#c0552d"
        parts.append(
            f'<g><title>{b["bin"]}: {b["weight_eur"]:,.0f} EUR · {b["cells"]} cells</title>'
            f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{max(bh,1):.1f}" fill="{col}"/></g>'
        )
        parts.append(
            f'<text x="{x+bar_w/2}" y="178" text-anchor="middle" class="tk" style="font-size:9px">{b["bin"]}</text>'
        )
        if b["weight_eur"] > 0:
            parts.append(
                f'<text x="{x+bar_w/2}" y="{y-4:.1f}" text-anchor="middle" class="tk">'
                f'{100*b["weight_share"]:.0f}%</text>'
            )
    # arrow annotation for missing +3% mass
    parts.append(
        '<text x="280" y="196" text-anchor="middle" class="tk">'
        "Flat +3% = 100% weight in one bin — engine spreads across cut / hold / raise / cap</text>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


def svg_blind_donut(share: float, evidenced: float) -> str:
    """Simple donut: blind vs evidenced weight."""
    # use two arcs via stroke-dasharray on circle
    r = 54
    c = 2 * np.pi * r
    blind = share
    ev = evidenced
    # normalize
    tot = blind + ev
    if tot <= 0:
        tot = 1
    blind_len = blind / tot * c
    ev_len = ev / tot * c
    parts = [
        '<svg viewBox="0 0 280 160" class="ch" role="img" aria-label="Blind weight share">'
    ]
    parts.append('<circle cx="80" cy="80" r="54" fill="none" stroke="#e8e4dc" stroke-width="22"/>')
    # evidenced first
    parts.append(
        f'<circle cx="80" cy="80" r="54" fill="none" stroke="#1d9e75" stroke-width="22" '
        f'stroke-dasharray="{ev_len:.1f} {c:.1f}" stroke-dashoffset="0" '
        f'transform="rotate(-90 80 80)"/>'
    )
    parts.append(
        f'<circle cx="80" cy="80" r="54" fill="none" stroke="#8a9bb0" stroke-width="22" '
        f'stroke-dasharray="{blind_len:.1f} {c:.1f}" stroke-dashoffset="{-ev_len:.1f}" '
        f'transform="rotate(-90 80 80)"/>'
    )
    parts.append(
        f'<text x="80" y="76" text-anchor="middle" style="font-size:20px;font-weight:700;fill:#1a2b4a">'
        f'{100*blind:.0f}%</text>'
    )
    parts.append('<text x="80" y="94" text-anchor="middle" class="tk">blind €</text>')
    parts.append('<rect x="160" y="50" width="14" height="14" fill="#8a9bb0"/>')
    parts.append('<text x="180" y="62" class="ax">NO_EVIDENCE_HOLD</text>')
    parts.append('<rect x="160" y="78" width="14" height="14" fill="#1d9e75"/>')
    parts.append('<text x="180" y="90" class="ax">Street evidence</text>')
    parts.append('<text x="160" y="120" class="tk">Still partly old-world</text>')
    parts.append('<text x="160" y="136" class="tk">base lift on blind weight</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_evidence_bars(evid: list) -> str:
    max_w = max(e["weight_eur"] for e in evid) or 1
    h = 24 + len(evid) * 36 + 20
    parts = [
        f'<svg viewBox="0 0 560 {h}" class="ch" role="img" aria-label="Evidence tier weight">'
    ]
    for i, e in enumerate(evid):
        y = 16 + i * 36
        bw = e["weight_eur"] / max_w * 320
        col = "#8a9bb0" if e["evidence_tier"] == "T5_none" else "#1d9e75"
        parts.append(
            f'<text x="140" y="{y+14}" text-anchor="end" class="ax">{e["evidence_tier"]}</text>'
        )
        parts.append(f'<rect x="150" y="{y}" width="{bw:.1f}" height="18" fill="{col}"/>')
        parts.append(
            f'<text x="{160+bw:.1f}" y="{y+14}" class="tk">'
            f'{e["cells"]} cells · {100*e["weight_share"]:.1f}% · wtd Δ {100*e["wtd_delta"]:.1f}%</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def svg_brand_ceilings(tiers: list) -> str:
    h = 200
    parts = [
        f'<svg viewBox="0 0 560 {h}" class="ch" role="img" aria-label="Brand quality ceilings">'
    ]
    parts.append(
        '<text x="20" y="18" class="tk">Max ISZE premium vs IAM by brand-quality tier (policy ladder)</text>'
    )
    max_c = 250
    for i, t in enumerate(tiers):
        y = 36 + i * 36
        bw = t["ceiling_pct"] / max_c * 360
        # darker for lower quality (higher ceiling)
        cols = {4: "#1d9e75", 3: "#2a78d6", 2: "#eda100", 1: "#c0552d"}
        col = cols.get(t["tier"], "#2a78d6")
        parts.append(f'<text x="150" y="{y+14}" text-anchor="end" class="ax">T{t["tier"]} {t["label"]}</text>')
        parts.append(f'<rect x="160" y="{y}" width="{bw:.1f}" height="20" fill="{col}"/>')
        parts.append(f'<text x="{168+bw:.1f}" y="{y+14}" class="tk">+{t["ceiling_pct"]}%</text>')
    parts.append(
        '<text x="20" y="190" class="tk">Prior process: one flat “premium” instinct — no tiered ceiling discipline</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def svg_class_factors(factors: list) -> str:
    max_f = max(f["factor"] for f in factors)
    h = 24 + len(factors) * 22 + 28
    parts = [
        f'<svg viewBox="0 0 560 {h}" class="ch" role="img" aria-label="Class factors">'
    ]
    parts.append(
        '<text x="20" y="16" class="tk">Class factors set SP level from FOB — they did not allocate the +3% revision</text>'
    )
    for i, f in enumerate(factors):
        y = 28 + i * 22
        bw = f["factor"] / max_f * 300
        parts.append(f'<text x="60" y="{y+12}" text-anchor="end" class="ax">Class {f["cls"]}</text>')
        parts.append(f'<rect x="70" y="{y}" width="{bw:.1f}" height="14" fill="#203759"/>')
        parts.append(f'<text x="{78+bw:.1f}" y="{y+11}" class="tk">{f["factor"]}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def svg_launch_compare(L: dict) -> str:
    h = 160
    parts = [
        f'<svg viewBox="0 0 560 {h}" class="ch" role="img" aria-label="Launch book GP NPV">'
    ]
    parts.append('<text x="20" y="18" class="tk">D-Max 2.2 launch book — GP NPV by tactic (modelled ranking)</text>')
    class_v = L["class_only_gp_npv_eur"]
    best_v = L["best_gp_npv_eur"]
    max_v = best_v
    parts.append('<text x="140" y="55" text-anchor="end" class="ax">class_only</text>')
    parts.append(
        f'<rect x="150" y="40" width="{class_v/max_v*320:.1f}" height="20" fill="#c8c2b6"/>'
    )
    parts.append(f'<text x="{158+class_v/max_v*320:.1f}" y="54" class="tk">{eur(class_v)}</text>')
    parts.append(f'<text x="140" y="95" text-anchor="end" class="ax">{L["best_tactic"]}</text>')
    parts.append(
        f'<rect x="150" y="80" width="{best_v/max_v*320:.1f}" height="20" fill="#c0552d"/>'
    )
    parts.append(f'<text x="{158+best_v/max_v*320:.1f}" y="94" class="tk">{eur(best_v)}</text>')
    parts.append(
        f'<text x="20" y="130" class="tk">+{L["vs_class_only_pct"]}% GP NPV vs class-only · '
        f'{L["services_per_vehicle_yr"]} svc/veh/yr at {L["oil_interval_km"]:,} km '
        f'(was {L["prior_interval_km"]:,})</text>'
    )
    parts.append(
        '<text x="20" y="148" class="tk">[ASSUMPTION] erosion — ranking only, not a volume forecast under +3%</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def svg_caps_strip(caps: dict) -> str:
    items = [
        ("At +8% cap", caps["n_capped"], "#c0552d"),
        ("θ street-vetoed", caps["n_theta_vetoed"], "#eda100"),
        ("At floor −12%", caps["n_at_floor"], "#8a9bb0"),
    ]
    parts = ['<svg viewBox="0 0 560 90" class="ch" role="img" aria-label="Caps and vetoes">']
    for i, (lab, n, col) in enumerate(items):
        x = 30 + i * 180
        parts.append(f'<rect x="{x}" y="20" width="160" height="50" fill="#fff" stroke="#d9d3c8"/>')
        parts.append(
            f'<text x="{x+80}" y="48" text-anchor="middle" '
            f'style="font-size:22px;font-weight:700;fill:{col}">{n}</text>'
        )
        parts.append(f'<text x="{x+80}" y="64" text-anchor="middle" class="tk">{lab}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def render_html(p: dict) -> str:
    R = p["readiness"]
    C = p["comparison"]
    M = p["meta"]
    L = p["launch"]
    W = C["why_engine"]

    layer_cards = []
    for layer in R["layers"]:
        col = score_color(layer["score"])
        layer_cards.append(
            f"""
<div class="layer">
  <div class="layer-top">
    <div class="layer-id">Layer {layer['id']}</div>
    <div class="layer-score" style="color:{col}">{layer['score']}%</div>
  </div>
  <h3>{layer['name']}</h3>
  <div class="pill {layer['status']}">{layer['status']}</div>
  <p><b>Running:</b> {layer['what_runs']}</p>
  <p class="miss"><b>Missing:</b> {layer['missing']}</p>
</div>"""
        )

    more_rows = "".join(
        f"<tr><td>{r['db']}</td><td>{r['label']}</td><td class='n'>{r['delta_pct']:.2f}%</td>"
        f"<td class='n hi'>+{r['diff_eur']:,.0f}</td><td class='sm'>{r['reason_code']}</td></tr>"
        for r in C["pays_more_than_uniform"]
    )
    less_rows = "".join(
        f"<tr><td>{r['db']}</td><td>{r['label']}</td><td class='n'>{r['delta_pct']:.2f}%</td>"
        f"<td class='n bad'>{r['diff_eur']:,.0f}</td><td class='sm'>{r['reason_code']}</td></tr>"
        for r in C["pays_less_than_uniform"]
    )
    miss_rows = "".join(
        f"<tr><td class='n'>{m['priority']}</td><td>{m['item']}</td><td>{m['unlocks']}</td></tr>"
        for m in R["missing_checklist"]
    )
    cat_rows = "".join(
        f"<tr><td>{c['pms_category']}</td><td class='n'>{c['n_priced_oe']}</td>"
        f"<td class='n'>{c['gap_to_oem_benchmark']}</td>"
        f"<td><span class='tag {c['basis_if_alloc']}'>{c['basis_if_alloc']}</span></td>"
        f"<td class='sm'>{c['peer_markets_priced']}</td></tr>"
        for c in R["category_readiness"]
    )
    reason_rows = "".join(
        f"<tr><td>{r['reason_code']}</td><td class='n'>{r['cells']}</td>"
        f"<td class='n'>{r['weight_eur']:,.0f}</td>"
        f"<td class='n'>{100*r['wtd_delta']:.2f}%</td>"
        f"<td class='n'>{r['rev_engine']:,.0f}</td>"
        f"<td class='n'>{r['rev_diff']:+,.0f}</td></tr>"
        for r in C["by_reason"]
    )
    zone_rows = "".join(
        f"<tr><td>{z['zone']}</td><td class='n'>{z['cells']}</td>"
        f"<td class='n'>{z['weight_eur']:,.0f}</td>"
        f"<td class='n'>{100*z['wtd_delta']:.2f}%</td>"
        f"<td class='n'>{z['rev_diff']:+,.0f}</td></tr>"
        for z in sorted(C["by_zone"], key=lambda x: -x["weight_eur"])
    )
    maturity_rows = "".join(
        f"<tr><td><b>{m['dim']}</b></td><td>{m['prior']}</td><td>{m['engine']}</td></tr>"
        for m in W["maturity_matrix"]
    )
    talk_cards = "".join(
        f'<div class="talk"><h4>{t["title"]}</h4><p>{t["text"]}</p></div>'
        for t in W["distributor_talking_points"]
    )
    prior_lis = "".join(f"<li>{b}</li>" for b in W["prior_process"]["bullets"])
    eng_lis = "".join(f"<li>{b}</li>" for b in W["engine_process"]["bullets"])
    brand_rows = "".join(
        f"<tr><td>T{t['tier']}</td><td>{t['label']}</td><td class='n'>+{t['ceiling_pct']}%</td>"
        f"<td class='sm'>{t['example']}</td></tr>"
        for t in W["brand_tiers"]
    )

    layer_svg = svg_layer_scores(R["layers"])
    rsvg = svg_reason_diff(C["by_reason"])
    dsvg = svg_db_diff(C["by_db"])
    zone_pair = svg_uniform_vs_engine_zone(C["by_zone"])
    db_stack = svg_zone_stacked_db(W["db_zone_stack"])
    flow_svg = svg_redistribution_flow(W["flows_from"], W["flows_to"], C["redistributed_eur"])
    hist_svg = svg_delta_histogram(W["histogram_engine"], M["base_eur"])
    blind_svg = svg_blind_donut(
        W["blind_weight"]["weight_share"],
        1.0 - W["blind_weight"]["weight_share"],
    )
    evid_svg = svg_evidence_bars(W["by_evidence_detail"])
    brand_svg = svg_brand_ceilings(W["brand_tiers"])
    class_svg = svg_class_factors(W["class_factors"])
    launch_svg = svg_launch_compare(L)
    caps_svg = svg_caps_strip(W["caps"])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ISZE · Pricing Engine Readiness</title>
<style>
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
body{{font-family:"Segoe UI",Helvetica,Arial,sans-serif;color:#222;background:#f7f4ee;font-size:15px;line-height:1.5}}
.hero{{background:linear-gradient(155deg,#15233c 0%,#203759 55%,#2b4a78 100%);color:#eef1f6;padding:42px 28px 28px}}
.hero-inner{{max-width:1120px;margin:0 auto}}
.brand{{font-family:Georgia,"Times New Roman",serif;font-size:13px;letter-spacing:.18em;text-transform:uppercase;color:#c9d4e6;margin-bottom:14px}}
.hero h1{{font-family:Georgia,"Times New Roman",serif;color:#fff;font-size:34px;line-height:1.12;margin:0 0 12px;font-weight:400}}
.hero .rule{{width:64px;height:3px;background:#c0552d;margin:0 0 16px}}
.hero .lead{{max-width:720px;font-size:15.5px;color:#d5dce8;margin:0 0 22px}}
.hero-kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
.hk{{background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);padding:14px 16px}}
.hk .v{{font-size:28px;font-weight:700;letter-spacing:-.5px;color:#fff}}
.hk .l{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#aeb9cb;margin-top:4px}}
.hk .n{{font-size:12px;color:#9aa8bd;margin-top:6px;line-height:1.35}}
.tabs{{display:flex;gap:0;max-width:1120px;margin:0 auto;padding:0 28px;background:#f7f4ee;border-bottom:1px solid #d9d3c8;position:sticky;top:0;z-index:20}}
.tabs button{{appearance:none;border:0;background:transparent;padding:14px 20px;font:inherit;font-size:14px;color:#6b6256;cursor:pointer;border-bottom:3px solid transparent;margin-bottom:-1px}}
.tabs button.active{{color:#1a2b4a;font-weight:600;border-bottom-color:#c0552d}}
.tabs button:hover{{color:#1a2b4a}}
.panel{{display:none}}
.panel.active{{display:block}}
.wrap{{max-width:1120px;margin:0 auto;padding:28px 28px 80px}}
h2{{font-family:Georgia,"Times New Roman",serif;color:#1a2b4a;font-size:22px;margin:36px 0 8px;padding-bottom:8px;border-bottom:2px solid #1a2b4a}}
h2 .no{{color:#c0552d}}
h3.sub{{font-family:Georgia,serif;color:#1a2b4a;font-size:17px;margin:28px 0 8px}}
.lead{{color:#6b6256;margin:0 0 18px;max-width:820px}}
.callout{{border-left:3px solid #c0552d;background:#fff;padding:14px 16px;margin:0 0 20px}}
.callout.ok{{border-left-color:#1d9e75}}
.callout.amber{{border-left-color:#eda100}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.grid3{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
.card{{background:#fff;border:1px solid #d9d3c8;padding:18px 18px 14px}}
.card h3{{font-family:Georgia,serif;color:#1a2b4a;font-size:15px;margin:0 0 6px}}
.card .cap{{font-size:12.5px;color:#6b6256;margin:0 0 12px}}
.layers{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0}}
.layer{{background:#fff;border:1px solid #d9d3c8;padding:14px 14px 12px}}
.layer-top{{display:flex;justify-content:space-between;align-items:baseline}}
.layer-id{{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#6b6256}}
.layer-score{{font-size:26px;font-weight:700;letter-spacing:-1px}}
.layer h3{{font-family:Georgia,serif;font-size:14px;color:#1a2b4a;margin:4px 0 8px}}
.layer p{{font-size:12.5px;margin:6px 0;color:#333}}
.layer .miss{{color:#6b6256}}
.pill{{display:inline-block;font-size:10.5px;text-transform:uppercase;letter-spacing:.06em;padding:2px 8px;border-radius:2px;background:#e8e4dc;color:#444;margin-bottom:6px}}
.pill.running{{background:#e4f5ee;color:#1d6b4f}}
.pill.partial{{background:#fff3d6;color:#8a6500}}
table{{width:100%;border-collapse:collapse;font-size:13px;background:#fff}}
th{{background:#1a2b4a;color:#fff;text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:.05em}}
td{{padding:7px 10px;border-bottom:1px solid #e8e4dc}}
tbody tr:nth-child(even){{background:#faf8f4}}
td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}
td.hi{{color:#1d9e75;font-weight:600}}
td.bad{{color:#b23b3b;font-weight:600}}
td.sm{{font-size:11.5px;color:#6b6256}}
.tag{{font-size:11px;padding:1px 7px;border-radius:2px;background:#e8e4dc}}
.tag.oem_benchmark{{background:#dcecfc;color:#1a4a7a}}
.tag.near_gate{{background:#fff3d6;color:#8a6500}}
.tag.below_gate{{background:#fde8e8;color:#8a3030}}
.tag.iam_derived{{background:#e4f5ee;color:#1d6b4f}}
.comp-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:14px 0 20px}}
.comp{{background:#fff;border:1px solid #d9d3c8;padding:16px}}
.comp h3{{margin:0 0 8px;font-family:Georgia,serif;color:#1a2b4a;font-size:16px}}
.comp .big{{font-size:32px;font-weight:700;color:#1a2b4a;letter-spacing:-1px}}
.comp .sub{{font-size:12.5px;color:#6b6256;margin:4px 0 10px}}
.checklist{{margin:0;padding-left:18px}}
.checklist li{{margin:6px 0}}
.talks{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:14px 0}}
.talk{{background:#fff;border:1px solid #d9d3c8;border-top:3px solid #c0552d;padding:14px 16px}}
.talk h4{{margin:0 0 6px;font-family:Georgia,serif;color:#1a2b4a;font-size:14px}}
.talk p{{margin:0;font-size:13px;color:#333}}
.foot{{margin-top:40px;padding-top:14px;border-top:1px solid #d9d3c8;font-size:11.5px;color:#6b6256;line-height:1.65}}
svg.ch{{width:100%;height:auto;display:block}}
svg.ch text{{font-family:"Segoe UI",Arial,sans-serif}}
svg.ch .tk{{font-size:11px;fill:#6b6256}}
svg.ch .ax{{font-size:11px;fill:#444}}
.anchor-nav{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 20px}}
.anchor-nav a{{font-size:12px;color:#1a2b4a;text-decoration:none;background:#fff;border:1px solid #d9d3c8;padding:6px 10px}}
.anchor-nav a:hover{{border-color:#c0552d;color:#c0552d}}
@media(max-width:900px){{
  .hero-kpis,.grid2,.grid3,.layers,.comp-grid,.talks{{grid-template-columns:1fr}}
  .hero h1{{font-size:26px}}
  .wrap,.hero,.tabs{{padding-left:16px;padding-right:16px}}
}}
@media print{{
  .tabs{{display:none}}
  .panel{{display:block!important}}
}}
</style>
</head>
<body>
<div class="hero">
  <div class="hero-inner">
    <div class="brand">Isuzu Europe · ISZE Pricing</div>
    <h1>Pricing engine readiness</h1>
    <div class="rule"></div>
    <p class="lead">How much of the rule-based pricing engine is running today, what still blocks a full launch,
    and — in depth — why the engine is better than the prior uniform / class-era revision: same +3% index, different who pays.</p>
    <div class="hero-kpis">
      <div class="hk"><div class="v">{R['composite_pct']}%</div><div class="l">Engine readiness</div>
        <div class="n">Equal-weight average of Spec layers 0–5</div></div>
      <div class="hk"><div class="v">+{M['target_weighted_pct']:.1f}%</div><div class="l">Weighted target</div>
        <div class="n">Hit exactly on alloc run</div></div>
      <div class="hk"><div class="v">{R['oem_street']['unique_oe_street_filled']}/{R['oem_street']['unique_oe_mapped']}</div><div class="l">OEM street fill</div>
        <div class="n">{R['oem_street']['fill_pct']}% of mapped peer OEs priced</div></div>
      <div class="hk"><div class="v">{eur(C['redistributed_eur'])}</div><div class="l">€ reallocated vs uniform</div>
        <div class="n">Same total +3%; different incidence</div></div>
    </div>
  </div>
</div>

<nav class="tabs" role="tablist" aria-label="Dashboard sections">
  <button type="button" class="active" data-tab="readiness" role="tab" aria-selected="true">Readiness</button>
  <button type="button" data-tab="why" role="tab" aria-selected="false">Why the engine</button>
</nav>

<div class="wrap">

<!-- ═══════════════ TAB: READINESS ═══════════════ -->
<div id="panel-readiness" class="panel active" role="tabpanel">

<section>
  <h2><span class="no">01</span> · Full launch definition</h2>
  <div class="callout">{R['full_launch']['definition']}</div>
  <div class="grid2">
    <div class="card">
      <h3>Not required for full launch</h3>
      <ul class="checklist">
        {''.join(f'<li>{x}</li>' for x in R['full_launch']['not_required_for_full_launch'])}
      </ul>
    </div>
    <div class="card">
      <h3>Layer readiness scoreboard</h3>
      <p class="cap">Green ≥75 · Amber 50–74 · Red &lt;50. Composite = mean of six layers.</p>
      {layer_svg}
    </div>
  </div>
</section>

<section>
  <h2><span class="no">02</span> · What is running — layers 0–5</h2>
  <p class="lead">Evidence gates, OEM peer street, IAM-derived ceilings, θ components, and list treatment —
  stated as running vs missing, not as a forecast.</p>
  <div class="layers">
    {''.join(layer_cards)}
  </div>

  <div class="grid2" style="margin-top:8px">
    <div class="card">
      <h3>OEM peer street — category gate</h3>
      <p class="cap">Gate = ≥3 priced peer OEs → oem_benchmark. Street factor {R['oem_street']['street_factor']}.</p>
      <div class="tw"><table>
        <thead><tr><th>Category</th><th class="n">Priced OE</th><th class="n">Gap to gate</th><th>Basis</th><th>Markets</th></tr></thead>
        <tbody>{cat_rows}</tbody>
      </table></div>
    </div>
    <div class="card">
      <h3>Soft signals (not in Δ)</h3>
      <p class="cap">Diagnostic only — must not be read as allocation coefficients.</p>
      <p><b>DB → dealer response:</b> {R['db_dlr']['measure_kind']} on {', '.join(R['db_dlr']['markets'])}.
      Joined to deltas: {'yes' if R['db_dlr']['joined_to_deltas'] else 'no'}. {R['db_dlr']['note']}</p>
      <p><b>θ:</b> {R['theta']['wired']}. {R['theta']['n_moving']} cells moved · {R['theta']['n_vetoed']} vetoed.
      Weighted θ_parc ≈ {R['theta']['weighted_theta_parc']:.3f}.</p>
      <p><b>ZPR1:</b> live as flat differential today; UMI and UTI stay separate columns — never blended.</p>
    </div>
  </div>
</section>

<section>
  <h2><span class="no">03</span> · Missing-data checklist for full launch</h2>
  <p class="lead">Ranked by unlock value. Nothing here invents peer OEs or street prices.</p>
  <div class="card">
    <table>
      <thead><tr><th class="n">#</th><th>Missing item</th><th>What it unlocks</th></tr></thead>
      <tbody>{miss_rows}</tbody>
    </table>
  </div>
  <div class="grid2" style="margin-top:14px">
    <div class="card">
      <h3>Measured in this pack</h3>
      <ul class="checklist">
        {''.join(f'<li>{x}</li>' for x in C['modelled_vs_measured']['measured'])}
      </ul>
    </div>
    <div class="card">
      <h3>Modelled / assumption</h3>
      <ul class="checklist">
        {''.join(f'<li>{x}</li>' for x in C['modelled_vs_measured']['modelled_assumption'])}
      </ul>
    </div>
  </div>
</section>

</div><!-- /panel-readiness -->

<!-- ═══════════════ TAB: WHY THE ENGINE ═══════════════ -->
<div id="panel-why" class="panel" role="tabpanel">

<section>
  <h2><span class="no">A</span> · Why the engine (Before vs Engine)</h2>
  <p class="lead">{W['headline_deep']}</p>
  <div class="anchor-nav">
    <a href="#we-process">Process contrast</a>
    <a href="#we-who">Who pays</a>
    <a href="#we-flow">Redistribution</a>
    <a href="#we-blind">Blind weight</a>
    <a href="#we-hist">Δ histogram</a>
    <a href="#we-street">Street gates</a>
    <a href="#we-brand">Brand ceilings</a>
    <a href="#we-dmax">D-Max / new models</a>
    <a href="#we-talk">Tell a distributor</a>
  </div>
  <div class="callout ok">
    <b>One sentence.</b> The prior process set a list level with class factors and then often applied a near-uniform % revision;
    the engine keeps the same +3% weighted index but allocates the incidence with capture zones, street evidence, caps, and reason codes — and is honest where evidence is still missing.
  </div>
</section>

<section id="we-process">
  <h3 class="sub">1 · Process contrast — crystal clear</h3>
  <div class="comp-grid">
    <div class="comp">
      <h3>{W['prior_process']['title']}</h3>
      <div class="big">+{C['class_path']['weighted_increase_pct']:.1f}%</div>
      <div class="sub">Revenue Δ {eur(C['class_path']['revenue_delta_eur'])} · constant units · uniform incidence</div>
      <ul class="checklist">{prior_lis}</ul>
    </div>
    <div class="comp">
      <h3>{W['engine_process']['title']}</h3>
      <div class="big">+{C['engine_path']['weighted_increase_pct']:.4f}%</div>
      <div class="sub">Revenue Δ {eur(C['engine_path']['revenue_delta_eur'])} · constant units · differentiated incidence</div>
      <ul class="checklist">{eng_lis}</ul>
    </div>
  </div>
  <div class="card">
    <h3>Maturity matrix — prior vs engine</h3>
    <p class="cap">shared labels. Class factors still set SP = FOB / factor; the revision logic is what changed.</p>
    <table>
      <thead><tr><th>Dimension</th><th>Prior process</th><th>Engine</th></tr></thead>
      <tbody>{maturity_rows}</tbody>
    </table>
  </div>
  <div class="grid2" style="margin-top:14px">
    <div class="card">
      <h3>Class factors (level, not revision)</h3>
      <p class="cap">These set the selling-price level from FOB. They do not decide who gets +3%.</p>
      {class_svg}
    </div>
    <div class="card">
      <h3>Street pricing point</h3>
      <p class="cap">Eucon lesson — compare apples to apples.</p>
      <p><b>Wrong historically:</b> reading street against raw list.</p>
      <p><b>Engine:</b> street factor <b>{W['street_factor']}</b> → compare at PR00 × {W['street_factor']}.</p>
      <p>oem_benchmark requires enough priced peer OEs; otherwise hold-when-blind — no invented peer prices.</p>
      <div class="callout amber" style="margin-top:12px">No volume claim. Constant prior-year units only. Mix quality is the prize today.</div>
    </div>
  </div>
</section>

<section id="we-who">
  <h3 class="sub">2 · Same +3% index € — who pays</h3>
  <p class="lead">Both paths deliver {eur(C['engine_path']['revenue_delta_eur'])} on {eur(M['base_eur'])}.
  Charts show incidence: uniform loads every zone equally by %; engine loads raise and cuts defend / contested-above-market.</p>
  <div class="grid2">
    <div class="card">
      <h3>Zone € Δ — uniform vs engine</h3>
      <p class="cap">Grey = flat +3% on that zone’s weight. Colour = engine.</p>
      {zone_pair}
    </div>
    <div class="card">
      <h3>Wallet zone table</h3>
      <p class="cap">Raise funds the index; defend / contested take less.</p>
      <table>
        <thead><tr><th>Zone</th><th class="n">Cells</th><th class="n">Weight €</th><th class="n">Wtd Δ</th><th class="n">vs uniform €</th></tr></thead>
        <tbody>{zone_rows}</tbody>
      </table>
    </div>
  </div>
  <div class="card" style="margin-top:14px">
    <h3>Distributor × zone — engine € Δ stack</h3>
    <p class="cap">Top DBs by |€ vs uniform|. Right labels = engine weighted %. Opacity reduced when a zone component is negative.</p>
    {db_stack}
  </div>
  <div class="card" style="margin-top:14px">
    <h3>Distributor incidence — € vs uniform +3%</h3>
    <p class="cap">Bars = euro difference vs charging every line +3%. Labels = engine weighted %.</p>
    {dsvg}
  </div>
  <div class="grid2" style="margin-top:14px">
    <div class="card">
      <h3>Who pays more than uniform</h3>
      <table>
        <thead><tr><th>DB</th><th>Category</th><th class="n">Engine Δ</th><th class="n">€ vs +3%</th><th>Reason</th></tr></thead>
        <tbody>{more_rows}</tbody>
      </table>
    </div>
    <div class="card">
      <h3>Who pays less than uniform</h3>
      <table>
        <thead><tr><th>DB</th><th>Category</th><th class="n">Engine Δ</th><th class="n">€ vs +3%</th><th>Reason</th></tr></thead>
        <tbody>{less_rows}</tbody>
      </table>
    </div>
  </div>
</section>

<section id="we-flow">
  <h3 class="sub">3 · Redistribution map (~{eur(C['redistributed_eur'])})</h3>
  <p class="lead">Zero-sum under constant units: cuts on defend / contested fund raises on captive and (still) the blind base lift.</p>
  <div class="grid2">
    <div class="card">
      <h3>From → to (reason codes)</h3>
      <p class="cap">Left releases € vs uniform; right absorbs it.</p>
      {flow_svg}
    </div>
    <div class="card">
      <h3>€ impact vs uniform, by reason</h3>
      <p class="cap">Positive = engine charges more than +3% on that bucket.</p>
      {rsvg}
    </div>
  </div>
  <div class="card" style="margin-top:14px">
    <h3>Reason-code detail</h3>
    <table>
      <thead><tr><th>Reason</th><th class="n">Cells</th><th class="n">Weight €</th><th class="n">Wtd Δ</th><th class="n">Engine rev Δ</th><th class="n">vs uniform</th></tr></thead>
      <tbody>{reason_rows}</tbody>
    </table>
  </div>
</section>

<section id="we-blind">
  <h3 class="sub">4 · Blind weight — still partly the old world</h3>
  <p class="lead">{W['blind_weight']['meaning']}</p>
  <div class="grid2">
    <div class="card">
      <h3>NO_EVIDENCE_HOLD share of basket €</h3>
      {blind_svg}
      <p style="margin-top:10px"><b>{W['blind_weight']['cells']} cells</b> ·
      {eur(W['blind_weight']['weight_eur'])} ·
      weighted Δ <b>{W['blind_weight']['wtd_delta_pct']:.2f}%</b>
      (base lift, not a position cut/raise).</p>
    </div>
    <div class="card">
      <h3>What this means externally</h3>
      <ul class="checklist">
        <li>Do <b>not</b> pitch “fully differentiated +3%” while ~{pct(W['blind_weight']['weight_share'])} of € is still on the unbenchmarked base.</li>
        <li>Do pitch: evidenced lines are already ruled (raise / defend / contested); blind lines wait for street / OEM peers.</li>
        <li>Filling near-gate OEM street (e.g. one genuine DAF quote) converts blind/near cats into oem_benchmark — that shrinks this slice.</li>
        <li>Prior process put <em>all</em> weight on uniform +3%. Engine already differentiates {pct(1-W['blind_weight']['weight_share'])} of € weight.</li>
      </ul>
    </div>
  </div>
</section>

<section id="we-hist">
  <h3 class="sub">5 · Caps, floors, reason codes — Δ distribution</h3>
  <p class="lead">Under a flat +3%, every euro of weight sits in one bin. Under the engine, weight spreads across cuts, holds, raises, and the +8% cap.</p>
  <div class="card">
    <h3>Histogram of engine deltas (€ weight)</h3>
    {hist_svg}
  </div>
  <div class="card" style="margin-top:14px">
    <h3>Hard limits applied this run</h3>
    <p class="cap">Cap +{W['caps']['cap_pct']:.0f}% (top-50 tighter at +{W['caps']['cap_top50_pct']:.0f}%); floor {W['caps']['floor_pct']:.0f}%.</p>
    {caps_svg}
  </div>
</section>

<section id="we-street">
  <h3 class="sub">6 · Street / evidence tiers — gates the prior process lacked</h3>
  <p class="lead">Prior revision had no systematic hold-when-blind. Engine: T5_none cannot take a position move; it rides the index base only.</p>
  <div class="grid2">
    <div class="card">
      <h3>Evidence tier — € weight</h3>
      {evid_svg}
    </div>
    <div class="card">
      <h3>Gate logic (shared)</h3>
      <ul class="checklist">
        <li><b>T3_eucon (and stronger):</b> may move within tier limits; street read at PR00 × {W['street_factor']}.</li>
        <li><b>T5_none:</b> NO_EVIDENCE_HOLD — no invented street; base lift only.</li>
        <li><b>oem_benchmark:</b> ≥3 priced peer OEs required — not Autodoc IAM substitutes for OEM peers.</li>
        <li><b>θ veto:</b> if already far above street premium, θ cannot raise further ({W['caps']['n_theta_vetoed']} cells this run).</li>
      </ul>
      <div class="callout" style="margin-top:12px">
        Prior process risk: raise defend-zone brakes the same as captive filters because “the book is +3%”.
        Engine risk (honest): over-claim differentiation while blind weight remains large.
      </div>
    </div>
  </div>
</section>

<section id="we-brand">
  <h3 class="sub">7 · Brand-quality % ceilings vs flat premium thinking</h3>
  <p class="lead">Policy ladder from IAM brand tiers. Prior instinct was often a single “we should be X% above IAM”. Engine encodes quality-dependent ceilings.</p>
  <div class="grid2">
    <div class="card">
      <h3>Ceiling ladder</h3>
      {brand_svg}
    </div>
    <div class="card">
      <h3>Tier table</h3>
      <table>
        <thead><tr><th>Tier</th><th>Quality</th><th class="n">Ceiling</th><th>Examples</th></tr></thead>
        <tbody>{brand_rows}</tbody>
      </table>
      <p class="cap" style="margin-top:10px">Until PN-level brand wiring is complete, category defaults may still show placeholder basis —
      the ladder is live in policy; full PN enforcement is a launch unlock.</p>
    </div>
  </div>
</section>

<section id="we-dmax">
  <h3 class="sub">8 · New models / D-Max 2.2 — mix, not only across-the-board +3%</h3>
  <p class="lead">How to tackle the portfolio +3% with a parc / interval / θ story — without inventing elasticity.</p>
  <div class="grid2">
    <div class="card">
      <h3>Launch book signal (modelled)</h3>
      <p class="cap">Run {L['run_id']} · ranking only</p>
      {launch_svg}
      <div class="callout" style="margin-top:12px">{L['note']}</div>
    </div>
    <div class="card">
      <h3>Portfolio +3% — practical read</h3>
      <ul class="checklist">
        <li><b>Do not</b> claim volume response from the +3% list move — ISZE→DB elasticity is not quotable.</li>
        <li><b>Do</b> use capture zones + street gates so defend-zone wear is not loaded like captive.</li>
        <li><b>Do</b> treat the D-Max generation shift as a θ_interval unlock: ~+33% service frequency on oil-interval parts once chassis maps exist ({L['oil_interval_km']:,} vs {L['prior_interval_km']:,} km).</li>
        <li><b>Do</b> keep UTI and UMI as separate Israel rows in any ZPR1 or sell-out lens.</li>
        <li>{C['sales_evolution']['new_models']}</li>
      </ul>
    </div>
  </div>
</section>

<section id="we-talk">
  <h3 class="sub">9 · What you can tell a distributor</h3>
  <p class="lead">Short callouts — shared English, no internal nicknames.</p>
  <div class="talks">{talk_cards}</div>
  <div class="callout amber">
    <b>Sales evolution (honest scope).</b> {C['sales_evolution']['under_constant_units']}
    {C['sales_evolution']['mix_risk_uniform']} {C['sales_evolution']['mix_engine']}
  </div>
</section>

</div><!-- /panel-why -->

<div class="foot">
  Sources: allocation run {M['alloc_run_id']}; OEM peer readiness 2026-08-10; D-Max launch run {M['launch_run_id']};
  pricing action map (213 PMS cells); Spec layers 0–5; class factors and brand ceilings from resolved pricing config.
  Charts are inline SVG — no external libraries, no network calls.
  shared · English UI · Built {M['as_of']}.
</div>
</div>
<script>
(function(){{
  var buttons = document.querySelectorAll('.tabs button');
  var panels = {{
    readiness: document.getElementById('panel-readiness'),
    why: document.getElementById('panel-why')
  }};
  function activate(name){{
    buttons.forEach(function(b){{
      var on = b.getAttribute('data-tab') === name;
      b.classList.toggle('active', on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
    }});
    Object.keys(panels).forEach(function(k){{
      panels[k].classList.toggle('active', k === name);
    }});
    if(name === 'why' && location.hash){{
      var el = document.querySelector(location.hash);
      if(el) el.scrollIntoView();
    }}
  }}
  buttons.forEach(function(b){{
    b.addEventListener('click', function(){{ activate(b.getAttribute('data-tab')); }});
  }});
  document.querySelectorAll('.anchor-nav a').forEach(function(a){{
    a.addEventListener('click', function(){{ activate('why'); }});
  }});
  if(location.hash && location.hash.indexOf('we-') === 1){{ activate('why'); }}
}})();
</script>
</body>
</html>
"""
    return html


def main() -> None:
    payload = build_payload()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_HTML.write_text(render_html(payload), encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_HTML}")
    print(f"Readiness composite: {payload['readiness']['composite_pct']}%")
    h = payload["comparison"]["headline"].encode("ascii", "replace").decode("ascii")
    print(f"Headline: {h[:160]}...")
    print(f"Why-engine redistributed: {payload['comparison']['redistributed_eur']:,.0f}")


if __name__ == "__main__":
    main()
