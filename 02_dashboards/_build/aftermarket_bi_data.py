"""Aftermarket BI data layer — replenishment + revision + Book B aggregates.

internal internal. UTI≠UMI · IUK≠ITUK · IRELAND≠IUK.
Reference dealer price = PR00 × 1.785 (field: reference_sellout_eur).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from tier_a_dashboard_common import (
    DB_ORDER,
    aim_chip,
    load_aim_by_pn,
    norm_pn_scalar,
    safe_float,
    signal_pill_class,
    action_pill_class,
)

PIPELINE_LABEL = {
    "balanced": "Balanced",
    "leakage_high_sellthrough": "Leakage — high sales to dealer",
    "leakage_no_bill": "Leakage — sales to dealer without bill",
    "overstock_low_sellthrough": "Overstock — low sales to dealer",
    "overstock_no_sellout": "Overstock — no sales to dealer",
    "no_activity": "No activity",
}

# Table and chart column labels. Centralised so a label change is made once, not
# in every builder that renders the same column. The JSON field names stay as
# they are (sellout_qty etc.) — only the label a person reads is written here.
COL_LABELS = {
    "sales_to_dealer_eur": "Sales to dealer €",
    "sales_to_dealer_qty": "Sales to dealer qty",
    "ref_dealer_price_eur": "Reference dealer price €",
}

DB_NOTES = {
    "ITUK": "ITUK — dealer grain available separately",
    "UTI": "UTI sold_to 1799 only — not UMI 1797",
    "IUK": "IUK — not ITUK",
    "IRELAND": "IRELAND (Harris) — not IUK",
    "GREECE": "GREECE (Petros) — network PN grain",
}

GUARDRAIL_ACTIONS = {
    "HOLD_DEFAULT",
    "REVIEW_PROXY_ADVERSE",
    "REVIEW_IAM_UNDERCUT",
    "REVIEW_HIGH_LIST_EXPOSURE",
    "REVIEW_LEAKAGE",
}


def _unit_eur(row: pd.Series) -> float | None:
    ref = safe_float(row.get("reference_sellout_eur"))
    if ref is not None:
        return ref
    bill_qty = safe_float(row.get("bill_qty"), ndigits=None)
    bill_eur = safe_float(row.get("bill_eur"), ndigits=None)
    if bill_qty and bill_qty > 0 and bill_eur is not None:
        return safe_float(bill_eur / bill_qty)
    return None


def enrich_revision_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["bill_qty_n"] = pd.to_numeric(out.get("bill_qty"), errors="coerce").fillna(0)
    out["sellout_qty_n"] = pd.to_numeric(out.get("sellout_qty"), errors="coerce").fillna(0)
    out["qty_gap"] = out["sellout_qty_n"] - out["bill_qty_n"]
    out["unit_eur"] = out.apply(_unit_eur, axis=1)
    out["gap_eur"] = (out["qty_gap"].clip(lower=0) * out["unit_eur"].fillna(0)).astype(float)
    over_qty = (-out["qty_gap"]).clip(lower=0)
    out["overstock_eur"] = (over_qty * out["unit_eur"].fillna(0)).astype(float)
    out["sellout_eur_est"] = (out["sellout_qty_n"] * out["unit_eur"].fillna(0)).astype(float)
    out["pn_norm"] = out["part_number"].map(norm_pn_scalar) if "part_number" in out.columns else ""
    return out


def pipeline_bucket(signal: str) -> str:
    s = (signal or "").lower()
    if "leakage" in s:
        return "leakage"
    if "overstock" in s:
        return "overstock"
    if "balanced" in s:
        return "balanced"
    return "other"


def load_revision_queue(derived: Any) -> pd.DataFrame:
    path = derived / "revision_exception_queue.csv"
    if not path.is_file():
        return pd.DataFrame()
    return enrich_revision_df(pd.read_csv(path, low_memory=False))


def load_replenishment_summary(derived: Any) -> pd.DataFrame:
    path = derived / "replenishment_summary_cy2025.parquet"
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_parquet(path)


def load_replenishment_bridge(derived: Any) -> pd.DataFrame:
    path = derived / "replenishment_bridge.parquet"
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_parquet(path)


def load_replenishment_bridge_ituk_dealer(derived: Any) -> pd.DataFrame:
    path = derived / "replenishment_bridge_ituk_dealer.parquet"
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_parquet(path)


def load_replenishment_exceptions(derived: Any) -> pd.DataFrame:
    path = derived / "replenishment_exceptions_cy2025.csv"
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def load_book_b_top(derived: Any) -> pd.DataFrame:
    path = derived / "revision_book_b_top_review.csv"
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def load_book_b_weights(derived: Any) -> pd.DataFrame:
    path = derived / "book_b_provisional_weights.csv"
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def load_book_b_bucket_summary(derived: Any) -> pd.DataFrame:
    path = derived / "book_b_bucket_summary.csv"
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def load_pn_descriptions(derived: Any) -> dict[str, str]:
    """PN → description from pricing parts master / IE40; fallback book_b weights."""
    out: dict[str, str] = {}
    for name in ("pricing_parts_master.parquet", "pricing_pr00_ie40.parquet"):
        path = derived / name
        if not path.is_file():
            continue
        df = pd.read_parquet(path)
        if "part_number" not in df.columns or "description" not in df.columns:
            continue
        for _, r in df.iterrows():
            pn = norm_pn_scalar(str(r.get("part_number") or ""))
            desc = str(r.get("description") or "").strip()
            if pn and desc and desc.lower() not in ("nan", "none") and pn not in out:
                out[pn] = desc
    bb = derived / "book_b_provisional_weights.csv"
    if bb.is_file():
        bdf = pd.read_csv(bb, low_memory=False)
        if "pn" in bdf.columns and "description" in bdf.columns:
            for _, r in bdf.iterrows():
                pn = norm_pn_scalar(str(r.get("pn") or ""))
                desc = str(r.get("description") or "").strip()
                if pn and desc and pn not in out:
                    out[pn] = desc
    return out


BUCKET_PLAIN: dict[str, str] = {
    "p700_launch": "P700 launch parts",
    "rg21_2_2l": "RG21 2.2L engine parts",
    "uti_p700_rec_x1_25": "UTI P700 recommended ×1.25",
    "dmax_lcv": "D-Max LCV parc",
    "n75_truck_wear": "N75 truck wear parts",
    "other_gf_1_0": "Other growth factor 1.0",
    "carryover_1_0": "Carryover baseline",
}


def vehicle_plain_label(
    db: str,
    pn: str,
    aim_l1: str,
    bucket: str,
    hint: str,
    *,
    desc_map: dict[str, str] | None = None,
) -> str:
    """Plain vehicle/parc label from price list bucket + AIM — not VIN-level."""
    parts: list[str] = []
    b = (bucket or "").lower()
    h = (hint or "").lower()
    a = (aim_l1 or "").lower()
    if b:
        plain = BUCKET_PLAIN.get(b)
        if plain:
            parts.append(plain)
        elif "p700" in b:
            parts.append("P700 launch parts")
        elif "rg21" in b:
            parts.append("RG21 2.2L engine parts")
        elif "uti" in b and "1.25" in b:
            parts.append("UTI P700 recommended ×1.25")
        elif "dmax" in b or "lcv" in b:
            parts.append("D-Max LCV parc")
        else:
            parts.append(f"Price list bucket: {bucket.replace('_', ' ')}")
    if db == "ITUK" and ("n75" in h or "truck" in a or "intake" in a):
        parts.append("Likely N75/truck wear (AIM proxy)")
    if db == "IUK" and ("lcv" in b or "d-max" in h or "dmax" in h):
        parts.append("D-Max LCV parc")
    if db == "GREECE":
        parts.append("No dealer sales in CY2025 file")
    if not parts and a:
        parts.append(f"AIM family: {aim_l1}")
    if not parts:
        parts.append("Launch bucket / AIM family proxy")
    note = " · ".join(parts)
    return f"{note} — not VIN-level unless dealer grain says otherwise"


def build_monday_actions_csv(
    rev: pd.DataFrame,
    aim_map: dict[str, dict[str, str]],
    derived: Any,
    out_path: Any,
    *,
    top_per_db: int = 10,
    bucket_map: dict[str, str] | None = None,
    hint_map: dict[str, str] | None = None,
) -> int:
    """Export top leakage rows per DB for Monday stand-up."""
    if rev.empty:
        return 0
    bucket_map = bucket_map or {}
    hint_map = hint_map or {}
    rows_out: list[dict[str, Any]] = []
    for db in DB_ORDER:
        g = rev.loc[(rev["distributor_code"] == db) & (rev["gap_eur"] > 0)].copy()
        if g.empty:
            continue
        g = g.nlargest(top_per_db, "gap_eur")
        for pri, (_, r) in enumerate(g.iterrows(), start=1):
            pn = str(r.get("part_number") or "")
            aim = aim_chip(pn, aim_map)
            sig = str(r.get("pipeline_signal") or "")
            rows_out.append(
                {
                    "db": db,
                    "pn": pn,
                    "aim_l1": aim,
                    "gap_eur": round(float(r.get("gap_eur") or 0)),
                    "gap_qty": round(float(r.get("qty_gap") or 0)),
                    "pipeline": PIPELINE_LABEL.get(sig, sig),
                    "recommended_action": str(r.get("recommended_action") or ""),
                    "vehicle_note": vehicle_plain_label(
                        db, pn, aim, bucket_map.get(pn, ""), hint_map.get(pn, "")
                    ),
                    "monday_priority": pri,
                }
            )
    if not rows_out:
        return 0
    out = pd.DataFrame(rows_out)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    return len(out)


def build_monthly_trend(bridge: pd.DataFrame, rev: pd.DataFrame) -> list[dict[str, Any]]:
    if bridge.empty:
        return []
    b = bridge.copy()
    b["bill_eur_n"] = pd.to_numeric(b.get("bill_eur"), errors="coerce").fillna(0)
    b["bill_qty_n"] = pd.to_numeric(b.get("bill_qty"), errors="coerce").fillna(0)
    b["sellout_qty_n"] = pd.to_numeric(b.get("sellout_qty"), errors="coerce").fillna(0)

    unit_lookup: dict[tuple[str, str], float] = {}
    if not rev.empty:
        for _, r in rev.iterrows():
            u = safe_float(r.get("unit_eur"))
            if u:
                unit_lookup[(str(r.get("distributor_code")), str(r.get("part_number")))] = u

    def _sellout_eur(row: pd.Series) -> float:
        db = str(row.get("distributor_code") or "")
        pn = str(row.get("part_number") or "")
        u = unit_lookup.get((db, pn))
        if u is None and row["bill_qty_n"] > 0:
            u = float(row["bill_eur_n"]) / float(row["bill_qty_n"])
        return float(row["sellout_qty_n"]) * float(u or 0)

    b["sellout_eur_est"] = b.apply(_sellout_eur, axis=1)
    g = (
        b.groupby("year_month", dropna=False)
        .agg(bill_eur=("bill_eur_n", "sum"), sellout_eur=("sellout_eur_est", "sum"))
        .reset_index()
        .sort_values("year_month")
    )
    out: list[dict[str, Any]] = []
    for _, r in g.iterrows():
        ym = str(r["year_month"])
        label = ym[5:7] + "/" + ym[:4] if len(ym) >= 7 else ym
        out.append(
            {
                "month": ym,
                "label": label,
                "bill_eur": safe_float(r["bill_eur"], ndigits=0),
                "sellout_eur": safe_float(r["sellout_eur"], ndigits=0),
            }
        )
    return out


def build_ituk_dealer_top(dealer: pd.DataFrame, rev: pd.DataFrame, top_n: int = 10) -> list[dict[str, Any]]:
    if dealer.empty:
        return []
    d = dealer.copy()
    d["sellout_qty_n"] = pd.to_numeric(d.get("sellout_qty"), errors="coerce").fillna(0)
    d["bill_qty_n"] = pd.to_numeric(d.get("bill_qty"), errors="coerce").fillna(0)
    d["bill_eur_n"] = pd.to_numeric(d.get("bill_eur"), errors="coerce").fillna(0)
    d["qty_gap"] = d["sellout_qty_n"] - d["bill_qty_n"]

    unit_lookup: dict[str, float] = {}
    if not rev.empty:
        ituk = rev.loc[rev["distributor_code"] == "ITUK"]
        for _, r in ituk.iterrows():
            u = safe_float(r.get("unit_eur"))
            if u:
                unit_lookup[str(r.get("part_number"))] = u

    def _gap_eur(row: pd.Series) -> float:
        u = unit_lookup.get(str(row.get("part_number")))
        if u is None and row["bill_qty_n"] > 0:
            u = float(row["bill_eur_n"]) / float(row["bill_qty_n"])
        return max(float(row["qty_gap"]), 0) * float(u or 0)

    d["gap_eur"] = d.apply(_gap_eur, axis=1)
    g = (
        d.groupby("dealer_name", dropna=False)
        .agg(gap_eur=("gap_eur", "sum"), sellout_qty=("sellout_qty_n", "sum"), bill_eur=("bill_eur_n", "sum"))
        .reset_index()
        .sort_values("gap_eur", ascending=False)
        .head(top_n)
    )
    return [
        {
            "dealer": str(r["dealer_name"] or "—"),
            "gap_eur": safe_float(r["gap_eur"], ndigits=0),
            "sellout_qty": safe_float(r["sellout_qty"], ndigits=0),
            "bill_eur": safe_float(r["bill_eur"], ndigits=0),
        }
        for _, r in g.iterrows()
    ]


def build_book_b_bucket_chart(summary: pd.DataFrame) -> list[dict[str, Any]]:
    if summary.empty:
        return []
    s = summary.copy()
    s["forecast_weight_eur_n"] = pd.to_numeric(s.get("forecast_weight_eur"), errors="coerce").fillna(0)
    s = s.sort_values("forecast_weight_eur_n", ascending=False)
    return [
        {
            "bucket": str(r.get("book_b_bucket") or ""),
            "pn_count": int(r.get("pn_count") or 0),
            "weight_eur": safe_float(r.get("forecast_weight_eur"), ndigits=0),
            "share": safe_float(r.get("share_of_book_b_weight"), ndigits=4),
        }
        for _, r in s.iterrows()
    ]


def build_db_panel(rev: pd.DataFrame, aim_map: dict[str, dict[str, str]], db: str) -> dict[str, Any]:
    g = rev.loc[rev["distributor_code"] == db].copy()
    if g.empty:
        return {
            "db": db,
            "leakage_eur": 0,
            "overstock_eur": 0,
            "balanced_eur": 0,
            "leakage_pn": 0,
            "overstock_pn": 0,
            "top15": [],
            "aim_mix": [],
            "monday_fix": [],
        }
    g["pipe_bucket"] = g["pipeline_signal"].map(pipeline_bucket)
    g["aim_l1"] = g["pn_norm"].map(lambda p: aim_chip(p, aim_map))

    leakage = g.loc[g["pipe_bucket"] == "leakage"]
    overstock = g.loc[g["pipe_bucket"] == "overstock"]
    balanced = g.loc[g["pipe_bucket"] == "balanced"]

    top15 = g.nlargest(15, "gap_eur")
    aim_mix = (
        g.loc[g["gap_eur"] > 0]
        .groupby("aim_l1", dropna=False)["gap_eur"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )
    monday = g.loc[g["gap_eur"] > 0].nlargest(12, "gap_eur")

    def _pn_row(r: pd.Series) -> dict[str, Any]:
        pn = str(r.get("part_number") or "")
        sig_raw = str(r.get("pipeline_signal") or "")
        return {
            "pn": pn,
            "gap_eur": safe_float(r.get("gap_eur"), ndigits=0),
            "qty_gap": safe_float(r.get("qty_gap"), ndigits=0),
            "aim": str(r.get("aim_l1") or "—"),
            "action": str(r.get("recommended_action") or ""),
            "signal": PIPELINE_LABEL.get(sig_raw, sig_raw),
        }

    return {
        "db": db,
        "leakage_eur": safe_float(leakage["gap_eur"].sum(), ndigits=0),
        "overstock_eur": safe_float(overstock["overstock_eur"].sum(), ndigits=0),
        "balanced_eur": safe_float(balanced["sellout_eur_est"].sum(), ndigits=0),
        "leakage_pn": int(len(leakage)),
        "overstock_pn": int(len(overstock)),
        "top15": [_pn_row(r) for _, r in top15.iterrows()],
        "aim_mix": [{"aim": str(k), "gap_eur": safe_float(v, ndigits=0)} for k, v in aim_mix.items()],
        "monday_fix": [_pn_row(r) for _, r in monday.iterrows()],
    }


def build_network_aggregates(rev: pd.DataFrame, aim_map: dict[str, dict[str, str]]) -> dict[str, Any]:
    built_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if rev.empty:
        return {"built_at": built_at, "by_db": [], "pipeline_mix": {}, "aim_l1_gap": [], "top_pn": [], "hero": {}}

    rev = rev.copy()
    rev["pipe_bucket"] = rev["pipeline_signal"].map(pipeline_bucket)
    rev["aim_l1"] = rev["pn_norm"].map(lambda p: aim_chip(p, aim_map))

    by_db = []
    for db in DB_ORDER:
        g = rev.loc[rev["distributor_code"] == db]
        if g.empty:
            continue
        by_db.append(
            {
                "db": db,
                "note": DB_NOTES.get(db, ""),
                "gap_eur": safe_float(g["gap_eur"].sum(), ndigits=0),
                "overstock_eur": safe_float(g["overstock_eur"].sum(), ndigits=0),
                "leakage_pn": int((g["pipe_bucket"] == "leakage").sum()),
                "overstock_pn": int((g["pipe_bucket"] == "overstock").sum()),
                "balanced_pn": int((g["pipe_bucket"] == "balanced").sum()),
                "pn_count": int(len(g)),
                "bill_qty": safe_float(g["bill_qty_n"].sum(), ndigits=0),
                "sellout_qty": safe_float(g["sellout_qty_n"].sum(), ndigits=0),
                "bill_eur": safe_float(pd.to_numeric(g.get("bill_eur"), errors="coerce").fillna(0).sum(), ndigits=0),
                "sellout_eur": safe_float(g["sellout_eur_est"].sum(), ndigits=0),
                "sell_through": safe_float(g["sellout_qty_n"].sum() / max(g["bill_qty_n"].sum(), 1), ndigits=3),
            }
        )

    pipeline_mix = {
        "leakage": int((rev["pipe_bucket"] == "leakage").sum()),
        "overstock": int((rev["pipe_bucket"] == "overstock").sum()),
        "balanced": int((rev["pipe_bucket"] == "balanced").sum()),
    }
    pipeline_mix_eur = {
        "leakage": safe_float(rev.loc[rev["pipe_bucket"] == "leakage", "gap_eur"].sum(), ndigits=0),
        "overstock": safe_float(rev.loc[rev["pipe_bucket"] == "overstock", "overstock_eur"].sum(), ndigits=0),
        "balanced": safe_float(
            rev.loc[rev["pipe_bucket"] == "balanced", "sellout_eur_est"].sum(), ndigits=0
        ),
    }

    aim_gap = (
        rev.loc[rev["gap_eur"] > 0]
        .groupby("aim_l1", dropna=False)["gap_eur"]
        .sum()
        .sort_values(ascending=False)
        .head(15)
    )
    aim_l1_gap = [{"aim": str(k), "gap_eur": safe_float(v, ndigits=0)} for k, v in aim_gap.items()]

    top = rev.nlargest(20, "gap_eur")
    top_pn = []
    for _, r in top.iterrows():
        pn = str(r.get("part_number") or "")
        top_pn.append(
            {
                "pn": pn,
                "db": str(r.get("distributor_code") or ""),
                "gap_eur": safe_float(r.get("gap_eur"), ndigits=0),
                "qty_gap": safe_float(r.get("qty_gap"), ndigits=0),
                "aim": str(r.get("aim_l1") or "—"),
                "action": str(r.get("recommended_action") or ""),
                "unit_eur": safe_float(r.get("unit_eur")),
            }
        )

    total_gap = safe_float(rev["gap_eur"].sum(), ndigits=0)
    total_overstock = safe_float(rev["overstock_eur"].sum(), ndigits=0)
    biggest = rev.nlargest(1, "gap_eur").iloc[0]
    net_bill = rev["bill_qty_n"].sum()
    net_sell = rev["sellout_qty_n"].sum()

    # Two distinct sides of the price index, reported separately.
    # ks_price_index = peer shop price / our reference dealer price.
    #   < 1 -> the peer shop is cheaper than us -> we look expensive   -> guardrail.
    #   > 1 -> the peer shop is dearer than us  -> we hold the premium -> raise defensible.
    # Do not union these into one number: they call for opposite commercial action.
    ks_index = pd.to_numeric(rev.get("ks_price_index"), errors="coerce")
    iam_mask = rev["recommended_action"] == "REVIEW_IAM_UNDERCUT"
    iam_count = int((iam_mask | (ks_index < 1).fillna(False)).sum())
    raise_mask = rev["recommended_action"] == "RAISE_OK_ROOM_VS_IAM"
    raise_count = int((raise_mask | (ks_index > 1).fillna(False)).sum())

    high_list = rev.loc[pd.to_numeric(rev.get("category_list_exposure_pct"), errors="coerce").fillna(0) >= 5]
    high_list_eur = safe_float(high_list["gap_eur"].sum(), ndigits=0)

    hero = {
        "total_gap_eur": total_gap,
        "total_overstock_eur": total_overstock,
        "biggest_db": str(biggest.get("distributor_code") or "—"),
        "biggest_pn": str(biggest.get("part_number") or "—"),
        "biggest_pn_gap_eur": safe_float(biggest.get("gap_eur"), ndigits=0),
        "biggest_pn_qty_gap": safe_float(biggest.get("qty_gap"), ndigits=0),
        "leakage_pn_count": int((rev["pipe_bucket"] == "leakage").sum()),
        "overstock_pn_count": int((rev["pipe_bucket"] == "overstock").sum()),
        "network_sell_through": safe_float(net_sell / max(net_bill, 1), ndigits=3),
        "db_count": len(by_db),
        "pn_count": int(len(rev)),
        "iam_undercut_count": iam_count,
        "raise_defensible_count": raise_count,
        "high_list_exposure_eur": high_list_eur,
        "book_b_weighted_eur": None,
    }

    return {
        "built_at": built_at,
        "year": 2025,
        "hero": hero,
        "by_db": by_db,
        "pipeline_mix": pipeline_mix,
        "pipeline_mix_eur": pipeline_mix_eur,
        "aim_l1_gap": aim_l1_gap,
        "top_pn": top_pn,
    }


def revision_row_dict(r: pd.Series, aim_map: dict[str, dict[str, str]]) -> dict[str, Any]:
    pn = str(r.get("part_number") or "")
    sig_raw = str(r.get("pipeline_signal") or "")
    sig = PIPELINE_LABEL.get(sig_raw, sig_raw)
    action = str(r.get("recommended_action") or "")
    aim_l1 = aim_chip(pn, aim_map)
    aim_hit = aim_map.get(norm_pn_scalar(pn), {})
    return {
        "pn": pn,
        "db": str(r.get("distributor_code") or ""),
        "signal": sig,
        "signal_class": signal_pill_class(sig),
        "action": action,
        "action_class": action_pill_class(action),
        "aim": aim_l1,
        "aim_l2": str(aim_hit.get("subgroup") or aim_hit.get("pms") or "—"),
        "bill_qty": safe_float(r.get("bill_qty_n"), ndigits=0),
        "sellout_qty": safe_float(r.get("sellout_qty_n"), ndigits=0),
        "qty_gap": safe_float(r.get("qty_gap"), ndigits=0),
        "gap_eur": safe_float(r.get("gap_eur"), ndigits=0),
        "overstock_eur": safe_float(r.get("overstock_eur"), ndigits=0),
        "unit_eur": safe_float(r.get("unit_eur")),
        "bill_eur": safe_float(r.get("bill_eur"), ndigits=0),
        "sellout_eur": safe_float(r.get("sellout_eur_est"), ndigits=0),
        "ks_index": safe_float(r.get("ks_price_index")),
        "ks_has_quote": bool(str(r.get("ks_has_quote") or "").lower() in ("true", "1", "yes")),
        "proxy_adverse": bool(str(r.get("proxy_adverse") or "").lower() in ("true", "1", "yes")),
        "list_exposure_pct": safe_float(r.get("category_list_exposure_pct")),
    }


def revision_rows_for_table(rev: pd.DataFrame, aim_map: dict[str, dict[str, str]], limit: int | None = None) -> list[dict]:
    df = rev.sort_values("gap_eur", ascending=False)
    if limit:
        df = df.head(limit)
    return [revision_row_dict(r, aim_map) for _, r in df.iterrows()]


def replenishment_rows_for_table(exc: pd.DataFrame, aim_map: dict[str, dict[str, str]]) -> list[dict]:
    if exc.empty:
        return []
    exc = exc.copy()
    exc["qty_gap"] = pd.to_numeric(exc["sellout_qty"], errors="coerce").fillna(0) - pd.to_numeric(
        exc["bill_qty"], errors="coerce"
    ).fillna(0)
    rows: list[dict] = []
    for _, r in exc.iterrows():
        pn = str(r.get("part_number") or "")
        sig_raw = str(r.get("pipeline_signal") or "")
        sig = PIPELINE_LABEL.get(sig_raw, sig_raw)
        rows.append(
            {
                "pn": pn,
                "db": str(r.get("distributor_code") or ""),
                "signal": sig,
                "signal_class": signal_pill_class(sig),
                "aim": aim_chip(pn, aim_map),
                "bill_qty": safe_float(r.get("bill_qty"), ndigits=0),
                "sellout_qty": safe_float(r.get("sellout_qty"), ndigits=0),
                "qty_gap": safe_float(r.get("qty_gap"), ndigits=0),
                "bill_eur": safe_float(r.get("bill_eur"), ndigits=0),
                "ratio": safe_float(r.get("sell_through_ratio")),
            }
        )
    return rows


def book_b_rows_for_table(bb: pd.DataFrame, aim_map: dict[str, dict[str, str]]) -> list[dict]:
    rows: list[dict] = []
    for _, r in bb.iterrows():
        pn = str(r.get("pn") or "")
        bill = safe_float(r.get("bill_qty"), ndigits=0)
        sell = safe_float(r.get("sellout_qty"), ndigits=0)
        gap = (sell - bill) if sell is not None and bill is not None else None
        action = str(r.get("recommended_action") or "")
        pipe_raw = str(r.get("pipeline_signal") or "")
        pipe = PIPELINE_LABEL.get(pipe_raw, pipe_raw)
        cat = str(r.get("category") or "")
        rows.append(
            {
                "pn": pn,
                "db": str(r.get("distributor_code") or ""),
                "action": action,
                "action_class": action_pill_class(action),
                "pipeline": pipe,
                "pipeline_class": signal_pill_class(pipe),
                "aim": aim_chip(pn, aim_map, fallback=cat),
                "bill_qty": bill,
                "sellout_qty": sell,
                "qty_gap": safe_float(gap, ndigits=0) if gap is not None else None,
                "bill_eur": safe_float(r.get("bill_eur"), ndigits=0),
                "ks_index": safe_float(r.get("ks_price_index")),
                "bucket": str(r.get("book_b_bucket") or ""),
                "forecast_eur": safe_float(r.get("forecast_weight_eur"), ndigits=0),
                "description": str(r.get("description") or "")[:80],
            }
        )
    return rows


def book_b_aggregates(bb: pd.DataFrame, rev: pd.DataFrame | None = None) -> dict[str, Any]:
    if bb.empty:
        return {
            "bucket_action": [],
            "heatmap": [],
            "iam_undercut": [],
            "high_list": [],
            "share_gain_top20": [],
            "conflict_count": 0,
            "conflict_blocked_eur": 0,
            "conflict_summary": [],
        }

    bb = bb.copy()
    bb["bucket"] = bb["book_b_bucket"].fillna("").astype(str)
    bb["action"] = bb["recommended_action"].fillna("").astype(str)
    bb["forecast_weight_eur_n"] = pd.to_numeric(bb.get("forecast_weight_eur"), errors="coerce").fillna(0)

    bucket_action: dict[tuple[str, str], dict[str, float]] = {}
    for _, r in bb.iterrows():
        key = (r["bucket"], r["action"])
        hit = bucket_action.setdefault(key, {"count": 0, "eur": 0.0})
        hit["count"] += 1
        hit["eur"] += float(r["forecast_weight_eur_n"])

    ba_list = [
        {"bucket": k[0], "action": k[1], "count": int(v["count"]), "eur": safe_float(v["eur"], ndigits=0)}
        for k, v in sorted(bucket_action.items())
    ]

    growth_buckets = bb["bucket"].str.contains("x1_25|rg21|carryover", case=False, na=False)
    conflicts = bb.loc[growth_buckets & bb["action"].isin(GUARDRAIL_ACTIONS)]
    conflict_count = len(conflicts)
    conflict_blocked_eur = safe_float(conflicts["forecast_weight_eur_n"].sum(), ndigits=0)

    conflict_summary: list[dict[str, Any]] = []
    for action, g in conflicts.groupby("action"):
        conflict_summary.append(
            {
                "action": str(action),
                "count": int(len(g)),
                "blocked_eur": safe_float(g["forecast_weight_eur_n"].sum(), ndigits=0),
            }
        )
    conflict_summary.sort(key=lambda x: x["blocked_eur"] or 0, reverse=True)

    iam_bb = bb.loc[bb["action"] == "REVIEW_IAM_UNDERCUT"]
    if rev is not None and not rev.empty:
        iam_rev = rev.loc[rev["recommended_action"] == "REVIEW_IAM_UNDERCUT"].copy()
        iam_rev = iam_rev.drop_duplicates(subset=["part_number", "distributor_code"])
        iam_source = iam_rev if len(iam_rev) >= len(iam_bb) else iam_bb
    else:
        iam_source = iam_bb

    high_list = bb.loc[bb["action"] == "REVIEW_HIGH_LIST_EXPOSURE"].nlargest(30, "forecast_weight_eur_n")
    share_gain = bb.nlargest(20, "forecast_weight_eur_n")

    def _bb_row(r: pd.Series) -> dict[str, Any]:
        pn = str(r.get("pn") or r.get("part_number") or "")
        bill = safe_float(r.get("bill_qty"), ndigits=0)
        sell = safe_float(r.get("sellout_qty"), ndigits=0)
        gap = (sell - bill) if sell is not None and bill is not None else None
        action = str(r.get("recommended_action") or r.get("action") or "")
        guardrail = action in GUARDRAIL_ACTIONS and bool(
            str(r.get("book_b_bucket") or r.get("bucket") or "").find("x1_25") >= 0
            or "carryover" in str(r.get("book_b_bucket") or r.get("bucket") or "").lower()
            or "rg21" in str(r.get("book_b_bucket") or r.get("bucket") or "").lower()
        )
        return {
            "pn": pn,
            "db": str(r.get("distributor_code") or r.get("db") or ""),
            "bucket": str(r.get("book_b_bucket") or r.get("bucket") or ""),
            "action": action,
            "action_class": action_pill_class(action),
            "forecast_eur": safe_float(r.get("forecast_weight_eur"), ndigits=0),
            "l12m_eur": safe_float(r.get("l12m_eur"), ndigits=0),
            "growth_factor": safe_float(r.get("growth_factor")),
            "ks_index": safe_float(r.get("ks_price_index")),
            "qty_gap": safe_float(gap, ndigits=0) if gap is not None else None,
            "description": str(r.get("description") or "")[:80],
            "guardrail_flag": guardrail,
        }

    iam_rows = [_bb_row(r) for _, r in iam_source.iterrows()]
    if rev is not None and len(iam_rows) < 26:
        # Top-up rows must come from the guardrail side only (peer shop cheaper than us).
        # Do NOT union in ks_price_index < 1 here: that would pull the raise-defensible
        # band into a register whose whole point is to list where we look expensive.
        extra = rev.loc[
            rev["recommended_action"] == "REVIEW_IAM_UNDERCUT"
        ].head(80)
        seen = {(r["pn"], r["db"]) for r in iam_rows}
        for _, r in extra.iterrows():
            key = (str(r.get("part_number")), str(r.get("distributor_code")))
            if key in seen:
                continue
            iam_rows.append(
                {
                    "pn": key[0],
                    "db": key[1],
                    "bucket": "—",
                    "action": str(r.get("recommended_action") or "REVIEW_IAM_UNDERCUT"),
                    "action_class": action_pill_class(str(r.get("recommended_action") or "")),
                    "forecast_eur": None,
                    "l12m_eur": safe_float(r.get("bill_eur"), ndigits=0),
                    "growth_factor": None,
                    "ks_index": safe_float(r.get("ks_price_index")),
                    "qty_gap": safe_float(r.get("qty_gap"), ndigits=0),
                    "description": str(r.get("category") or "")[:80],
                    "guardrail_flag": False,
                }
            )
            seen.add(key)

    return {
        "bucket_action": ba_list,
        "heatmap": ba_list,
        "iam_undercut": iam_rows[:100],
        "high_list": [_bb_row(r) for _, r in high_list.iterrows()],
        "share_gain_top20": [_bb_row(r) for _, r in share_gain.iterrows()],
        "conflict_count": conflict_count,
        "conflict_blocked_eur": conflict_blocked_eur,
        "conflict_summary": conflict_summary,
        "row_count": len(bb),
    }


def build_full_payload(derived: Any) -> dict[str, Any]:
    aim_map = load_aim_by_pn()
    rev = load_revision_queue(derived)
    exc = load_replenishment_exceptions(derived)
    bb = load_book_b_top(derived)
    bridge = load_replenishment_bridge(derived)
    dealer = load_replenishment_bridge_ituk_dealer(derived)
    bb_summary = load_book_b_bucket_summary(derived)
    bb_weights = load_book_b_weights(derived)

    net = build_network_aggregates(rev, aim_map)
    bb_agg = book_b_aggregates(bb, rev)

    book_b_weighted = 0.0
    if not bb_summary.empty:
        book_b_weighted = safe_float(
            pd.to_numeric(bb_summary.get("forecast_weight_eur"), errors="coerce").fillna(0).sum(), ndigits=0
        ) or 0.0
    net["hero"]["book_b_weighted_eur"] = book_b_weighted
    net["hero"]["book_b_conflicts"] = bb_agg.get("conflict_count", 0)
    net["hero"]["book_b_blocked_eur"] = bb_agg.get("conflict_blocked_eur", 0)
    net["hero"]["iam_undercut_count"] = len(bb_agg.get("iam_undercut", []))
    net["hero"]["high_list_count"] = len(bb_agg.get("high_list", []))

    net["book_b"] = bb_agg
    net["monthly_trend"] = build_monthly_trend(bridge, rev)
    net["book_b_buckets"] = build_book_b_bucket_chart(bb_summary)
    net["ituk_dealers_top10"] = build_ituk_dealer_top(dealer, rev, top_n=10)
    net["ituk_dealers_top5"] = net["ituk_dealers_top10"][:5]
    net["db_panels"] = {db: build_db_panel(rev, aim_map, db) for db in DB_ORDER if not rev.empty}
    net["network_top50"] = revision_rows_for_table(rev, aim_map, limit=50)
    net["revision_rows"] = revision_rows_for_table(rev, aim_map, limit=500)
    net["revision_row_total"] = int(len(rev))
    net["replenishment_exception_count"] = int(len(exc))
    net.update(build_genius_charts(rev, aim_map, bridge, bb_agg, net))
    return net


def build_genius_charts(
    rev: pd.DataFrame,
    aim_map: dict[str, dict[str, str]],
    bridge: pd.DataFrame,
    bb_agg: dict[str, Any],
    net: dict[str, Any],
) -> dict[str, Any]:
    """Aggregates for Command Center genius SSR charts."""
    out: dict[str, Any] = {
        "waterfall_steps": [],
        "pipeline_db_heatmap": [],
        "iam_scatter": [],
        "db_radar": [],
        "sparkline_by_db": [],
        "money_top5": [],
    }
    if rev.empty:
        return out

    rev = rev.copy()
    rev["pipe_bucket"] = rev["pipeline_signal"].map(pipeline_bucket)
    rev["aim_l1"] = rev["pn_norm"].map(lambda p: aim_chip(p, aim_map))

    hero = net.get("hero") or {}
    total_gap = float(hero.get("total_gap_eur") or rev["gap_eur"].sum())
    biggest = rev.nlargest(1, "gap_eur").iloc[0]
    out["waterfall_steps"] = [{"label": "Network leakage", "eur": total_gap, "is_total": True, "color": "#c0552d"}]
    for db in DB_ORDER:
        g = rev.loc[rev["distributor_code"] == db]
        if g.empty:
            continue
        out["waterfall_steps"].append(
            {"label": db, "eur": safe_float(g["gap_eur"].sum(), ndigits=0), "color": "#15233c"}
        )
    out["waterfall_steps"].append(
        {
            "label": f"Top PN {biggest.get('part_number')}",
            "eur": safe_float(biggest.get("gap_eur"), ndigits=0),
            "color": "#c0552d",
        }
    )

    heat_rows: list[dict[str, Any]] = []
    for db in DB_ORDER:
        g = rev.loc[rev["distributor_code"] == db]
        if g.empty:
            continue
        for cls in ("leakage", "overstock", "balanced"):
            sub = g.loc[g["pipe_bucket"] == cls]
            if cls == "leakage":
                eur = safe_float(sub["gap_eur"].sum(), ndigits=0)
            elif cls == "overstock":
                eur = safe_float(sub["overstock_eur"].sum(), ndigits=0)
            else:
                eur = safe_float(sub["sellout_eur_est"].sum(), ndigits=0)
            heat_rows.append({"db": db, "pipe_class": cls, "eur": eur or 0})
    out["pipeline_db_heatmap"] = heat_rows

    scatter_src = rev.loc[
        pd.to_numeric(rev.get("ks_price_index"), errors="coerce").notna()
        & (rev["gap_eur"] > 0)
    ].nlargest(30, "gap_eur")
    out["iam_scatter"] = [
        {
            "pn": str(r.get("part_number") or ""),
            "db": str(r.get("distributor_code") or ""),
            "ks_index": safe_float(r.get("ks_price_index")),
            "gap_eur": safe_float(r.get("gap_eur"), ndigits=0),
        }
        for _, r in scatter_src.iterrows()
    ]

    by_db = net.get("by_db") or []
    max_gap = max(float(d.get("gap_eur") or 0) for d in by_db) or 1.0
    max_over = max(float(d.get("overstock_eur") or 0) for d in by_db) or 1.0
    max_pn = max(float(d.get("pn_count") or 0) for d in by_db) or 1.0
    radar: list[dict[str, Any]] = []
    for d in by_db:
        leak = float(d.get("gap_eur") or 0)
        over = float(d.get("overstock_eur") or 0)
        st = float(d.get("sell_through") or 0)
        radar.append(
            {
                "db": d.get("db"),
                "leakage_pct": min(100.0, 100.0 * leak / max_gap),
                "overstock_pct": min(100.0, 100.0 * over / max_over),
                "sell_through": min(100.0, st * 100),
                "pn_density": min(100.0, 100.0 * float(d.get("pn_count") or 0) / max_pn),
                "gap_share": min(100.0, 100.0 * leak / max(total_gap, 1)),
            }
        )
    out["db_radar"] = radar

    top5 = rev.nlargest(5, "gap_eur")
    out["money_top5"] = [
        {
            "pn": str(r.get("part_number") or ""),
            "db": str(r.get("distributor_code") or ""),
            "gap_eur": safe_float(r.get("gap_eur"), ndigits=0),
            "aim": str(r.get("aim_l1") or "—"),
            "action": str(r.get("recommended_action") or ""),
            "signal": PIPELINE_LABEL.get(str(r.get("pipeline_signal") or ""), ""),
        }
        for _, r in top5.iterrows()
    ]

    if not bridge.empty:
        b = bridge.copy()
        b["bill_eur_n"] = pd.to_numeric(b.get("bill_eur"), errors="coerce").fillna(0)
        b["sellout_qty_n"] = pd.to_numeric(b.get("sellout_qty"), errors="coerce").fillna(0)
        unit_lookup: dict[tuple[str, str], float] = {}
        for _, r in rev.iterrows():
            u = safe_float(r.get("unit_eur"))
            if u:
                unit_lookup[(str(r.get("distributor_code")), str(r.get("part_number")))] = u

        def _so_eur(row: pd.Series) -> float:
            db = str(row.get("distributor_code") or "")
            pn = str(row.get("part_number") or "")
            u = unit_lookup.get((db, pn))
            bq = float(row.get("bill_qty") or 0) if pd.notna(row.get("bill_qty")) else 0
            be = float(row.get("bill_eur_n") or 0)
            if u is None and bq > 0:
                u = be / bq
            return float(row.get("sellout_qty_n") or 0) * float(u or 0)

        b["sellout_eur_est"] = b.apply(_so_eur, axis=1)
        strips: list[dict[str, Any]] = []
        for db in DB_ORDER:
            sub = b.loc[b["distributor_code"] == db]
            if sub.empty:
                continue
            g = (
                sub.groupby("year_month", dropna=False)
                .agg(sellout_eur=("sellout_eur_est", "sum"))
                .reset_index()
                .sort_values("year_month")
            )
            pts = [{"sellout_eur": safe_float(r["sellout_eur"], ndigits=0)} for _, r in g.iterrows()]
            strips.append({"label": db, "points": pts})
        out["sparkline_by_db"] = strips

    weighted = float((net.get("hero") or {}).get("book_b_weighted_eur") or 0)
    blocked = float(bb_agg.get("conflict_blocked_eur") or 0)
    out["book_b_bullets"] = [
        {"label": "Price list weighted ambition", "actual_eur": weighted, "blocked_eur": blocked},
        {"label": "Growth bucket conflicts", "actual_eur": blocked, "blocked_eur": blocked},
    ]
    return out
