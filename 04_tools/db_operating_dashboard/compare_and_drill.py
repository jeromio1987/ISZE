"""LCV-peer compare + genuine/BVP mix drill.

RENDER, NEVER COMPUTE in the HTML. All series live on the ledger.

LCV share is euro-weighted parc (V19 CY2025 UIO × ISZE-net rate), not a SKU split —
sales_fact has no vehicle segment. Peer = share ≥ 90%. Turkey / MIDI are not in the
registry and never enter the set. UMI 1797 and UTI 1799 stay separate sold-tos.
"""
from __future__ import annotations

import os

import pandas as pd

ISZE = r"C:\Users\jerom\Desktop\claude\ISZE"
DERIVED = os.path.join(ISZE, "01_data", "00_derived")
LCV_PEER_THRESHOLD = 90.0

# Family → leaf. Cabin = blower_filter. Pads/shoes collapse front/rear.
FILTER_LEAVES = (
    ("oil_filter", "Oil filter"),
    ("air_filter", "Air filter"),
    ("fuel_filter", "Fuel filter"),
    ("blower_filter", "Cabin filter"),
    ("urea_filter", "Urea filter"),
)
BRAKE_LEAVES = (
    ("pads", "Pads"),
    ("shoes", "Shoes"),
    ("rotors", "Rotors"),
    ("linings", "Linings"),
)
OTHER_LEAVES = (
    ("clutch_kit", "Clutch kit"),
    ("clutch_disc", "Clutch disc"),
    ("clutch_pressure_plate", "Clutch pressure plate"),
    ("clutch_booster", "Clutch booster"),
    ("rest", "Rest of book"),
)
PAD_CATS = {"brake_pad", "brake_pad_front", "brake_pad_rear"}
SHOE_CATS = {"brake_shoe", "brake_shoe_front", "brake_shoe_rear"}
ROTOR_CATS = {"brake_rotor"}
LINING_CATS = {"brake_lining_front", "brake_lining_rear"}
FILTER_CATS = {k for k, _ in FILTER_LEAVES}
BRAKE_CATS = PAD_CATS | SHOE_CATS | ROTOR_CATS | LINING_CATS
NAMED_OTHER = {k for k, _ in OTHER_LEAVES if k != "rest"}

_CACHE = None


def _r2(x):
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    return round(float(x), 2)


def _pct(num, den, d=1):
    if not den:
        return None
    return round(100.0 * float(num) / float(den), d)


def sold_to_map(registry):
    out = {}
    for db, reg in registry.items():
        for st in reg["sold_to"]:
            out[int(st)] = db
    return out


def leaf_of(pms_cat: str) -> tuple[str, str]:
    """Return (family_key, leaf_key). Unclassified → other/rest."""
    cat = str(pms_cat or "")
    if cat in FILTER_CATS:
        return "filters", cat
    if cat in PAD_CATS:
        return "brakes", "pads"
    if cat in SHOE_CATS:
        return "brakes", "shoes"
    if cat in ROTOR_CATS:
        return "brakes", "rotors"
    if cat in LINING_CATS:
        return "brakes", "linings"
    if cat in NAMED_OTHER:
        return "other", cat
    return "other", "rest"


def family_options():
    return [
        {"key": "all", "label": "Whole book", "children": []},
        {"key": "filters", "label": "Filters",
         "children": [{"key": k, "label": lab} for k, lab in FILTER_LEAVES]},
        {"key": "brakes", "label": "Brakes",
         "children": [{"key": k, "label": lab} for k, lab in BRAKE_LEAVES]},
        {"key": "other", "label": "Other (clutch etc.)",
         "children": [{"key": k, "label": lab} for k, lab in OTHER_LEAVES]},
    ]


def drill_keys():
    keys = ["all", "filters", "brakes", "other"]
    keys += [f"filters.{k}" for k, _ in FILTER_LEAVES]
    keys += [f"brakes.{k}" for k, _ in BRAKE_LEAVES]
    keys += [f"other.{k}" for k, _ in OTHER_LEAVES]
    return keys


def mask_for(frame, key: str):
    if key == "all":
        return pd.Series(True, index=frame.index)
    if key in ("filters", "brakes", "other"):
        return frame["family"] == key
    if "." in key:
        fam, leaf = key.split(".", 1)
        return (frame["family"] == fam) & (frame["leaf"] == leaf)
    return pd.Series(False, index=frame.index)


def lcv_share_row(db, reg, cy_latest, lcv_rate_base, cv_rates, read_v19):
    segs = read_v19(db) or {}
    cy = segs.get(cy_latest) or segs.get(cy_latest - 1) or {}
    lcv_u = float(cy.get("LCV") or 0)
    ld_u = float(cy.get("LD") or 0)
    md_u = float(cy.get("MD") or 0)
    f_u = float(cy.get("F-Series") or 0)
    cv_u = ld_u + md_u + f_u
    ttl_u = lcv_u + cv_u
    lcv_e = lcv_u * float(lcv_rate_base)
    cv_e = ld_u * cv_rates["LD"][0] + md_u * cv_rates["MD"][0] + f_u * cv_rates["F-Series"][0]
    ttl_e = lcv_e + cv_e
    method = "v19_uio_x_isze_net_rate"
    if ttl_e <= 0:
        # No V19 rows (Denmark / Norway mapping holes). Registry segment is the fallback.
        seg = (reg.get("segment") or "").upper()
        if seg == "LCV":
            share = 100.0
            method = "registry_segment_lcv_no_v19_uio"
        elif seg == "CV":
            share = 0.0
            method = "registry_segment_cv_no_v19_uio"
        else:
            share = None
            method = "unavailable_no_v19_uio"
        return {
            "distributor_code": db,
            "display": reg["display"],
            "gps_label": reg["gps_label"],
            "sold_to_sap": list(reg["sold_to"]),
            "registry_segment": reg["segment"],
            "lcv_share_pct": share,
            "lcv_uio_units": _r2(lcv_u),
            "cv_uio_units": _r2(cv_u),
            "lcv_wallet_eur": None,
            "cv_wallet_eur": None,
            "method": method,
            "in_peer_set": bool(share is not None and share >= LCV_PEER_THRESHOLD),
        }
    share = _pct(lcv_e, ttl_e, 1)
    return {
        "distributor_code": db,
        "display": reg["display"],
        "gps_label": reg["gps_label"],
        "sold_to_sap": list(reg["sold_to"]),
        "registry_segment": reg["segment"],
        "lcv_share_pct": share,
        "lcv_uio_units": _r2(lcv_u),
        "cv_uio_units": _r2(cv_u),
        "lcv_wallet_eur": _r2(lcv_e),
        "cv_wallet_eur": _r2(cv_e),
        "method": method,
        "in_peer_set": bool(share is not None and share >= LCV_PEER_THRESHOLD),
    }


def _mix_slice(g, bvp_pns):
    if g is None or not len(g):
        return None
    tot = float(g.net_sales_value.sum())
    if tot == 0:
        return None
    is_bvp = g.part_number.astype(str).isin(bvp_pns)
    bvp_e = float(g.loc[is_bvp, "net_sales_value"].sum())
    pns = g.part_number.astype(str)
    n_all = int(pns.nunique())
    n_b = int(pns[is_bvp].nunique())
    return {
        "total_eur": _r2(tot),
        "genuine_eur": _r2(tot - bvp_e),
        "bvp_eur": _r2(bvp_e),
        "genuine_share_pct": _pct(tot - bvp_e, tot, 1),
        "bvp_share_pct": _pct(bvp_e, tot, 1),
        "n_pns": n_all,
        "n_pns_bvp": n_b,
        "n_pns_genuine": n_all - n_b,
    }


def _order_slice(g, rush, stock, non_order=None):
    if g is None or not len(g):
        return None
    if non_order:
        g = g[~g.saty.isin(list(non_order))]
    if not len(g):
        return None
    tot = float(g.net_sales_value.sum())
    if tot == 0:
        return None
    rush_e = float(g.loc[g.saty.isin(rush), "net_sales_value"].sum())
    stock_e = float(g.loc[g.saty.isin(stock), "net_sales_value"].sum())
    other_e = tot - rush_e - stock_e
    return {
        "total_eur": _r2(tot),
        "stock_eur": _r2(stock_e),
        "rush_eur": _r2(rush_e),
        "other_coded_eur": _r2(other_e),
        "stock_pct": _pct(stock_e, tot, 1),
        "rush_class_pct": _pct(rush_e, tot, 1),
        "other_coded_pct": _pct(other_e, tot, 1),
    }


def _pn_table(g, bvp_pns, n=20):
    if g is None or not len(g):
        return []
    t = g.copy()
    t["pn"] = t.part_number.astype(str)
    t["is_bvp"] = t.pn.isin(bvp_pns)
    agg = (t.groupby(["pn", "description", "is_bvp", "family", "leaf"], dropna=False)
           .agg(eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"))
           .reset_index().sort_values("eur", ascending=False).head(n))
    rows = []
    for _, rw in agg.iterrows():
        eur = float(rw.eur)
        bvp_e = eur if bool(rw.is_bvp) else 0.0
        gen_e = 0.0 if bool(rw.is_bvp) else eur
        rows.append({
            "pn": str(rw.pn),
            "description": None if pd.isna(rw.description) else str(rw.description),
            "family": rw.family,
            "leaf": rw.leaf,
            "tier": "Best Value" if bool(rw.is_bvp) else "Genuine",
            "genuine_eur": _r2(gen_e),
            "bvp_eur": _r2(bvp_e),
            "eur": _r2(eur),
            "qty": _r2(rw.qty),
        })
    return rows


def _load_tagged_sales(registry, fy_end_year, cy_latest, fy_latest, rush, stock, non_order):
    sf = pd.read_parquet(
        os.path.join(DERIVED, "sales_fact.parquet"),
        columns=["billing_date", "sold_to_sap", "part_number", "description",
                 "billed_qty", "net_sales_value", "saty", "year"],
    )
    st_map = sold_to_map(registry)
    sf["sold_to_sap"] = pd.to_numeric(sf.sold_to_sap, errors="coerce")
    sf = sf[sf.sold_to_sap.isin(st_map)].copy()
    sf["db"] = sf.sold_to_sap.map(st_map)
    sf["cy"] = sf.billing_date.dt.year
    sf["fy"] = sf.billing_date.map(fy_end_year)
    sf = sf[sf.saty != "CR"].copy()

    xref = pd.read_csv(os.path.join(DERIVED, "genuine_bvp_crossref.csv"), dtype=str)
    bvp_pns = set(xref.bvp_pn.dropna().astype(str))
    pms_map = {}
    if "pms_category" in xref.columns:
        for _, rw in xref.iterrows():
            cat = rw.get("pms_category")
            if pd.isna(cat) or not str(cat).strip():
                continue
            for col in ("bvp_pn", "genuine_pn"):
                pn = str(rw.get(col) or "")
                if pn:
                    pms_map[pn] = str(cat)
    cat_path = os.path.join(DERIVED, "parts_catalog_dimension.csv")
    if os.path.exists(cat_path):
        cat = pd.read_csv(cat_path, dtype={"part_number": str},
                          usecols=["part_number", "pms_category"], low_memory=False)
        cat = cat.dropna(subset=["pms_category"])
        cat = cat[cat.pms_category.astype(str).str.strip() != ""]
        for _, rw in cat.iterrows():
            pms_map.setdefault(str(rw.part_number), str(rw.pms_category))
    pms_cat = sf.part_number.astype(str).map(pms_map)
    fam_leaf = pms_cat.map(leaf_of)
    sf["pms_cat"] = pms_cat.fillna("not_pms")
    sf["family"] = [x[0] for x in fam_leaf]
    sf["leaf"] = [x[1] for x in fam_leaf]
    return sf, bvp_pns


def build_network_bundle():
    """Once per process. Registry only — never Turkey / MIDI."""
    from build_ledger import (
        REGISTRY, CY_LATEST, FY_LATEST, fy_end_year, LCV_RATE_BASE, CV_RATES,
        read_v19_cy_segments, RUSH, STOCK_AS_SOR, NON_ORDER_SATY,
    )
    sf, bvp_pns = _load_tagged_sales(
        REGISTRY, fy_end_year, CY_LATEST, FY_LATEST, RUSH, STOCK_AS_SOR, NON_ORDER_SATY)

    members = []
    billed = (sf[sf.cy == CY_LATEST]
              .groupby("db").net_sales_value.sum())
    for db, reg in sorted(REGISTRY.items()):
        rec = lcv_share_row(db, reg, CY_LATEST, LCV_RATE_BASE, CV_RATES, read_v19_cy_segments)
        rec["billed_cy_eur"] = _r2(float(billed.get(db, 0.0)))
        rec["grain"] = f"complete CY{CY_LATEST}, credits excluded"
        members.append(rec)
    peer_keys = [m["distributor_code"] for m in members if m["in_peer_set"]]
    net_keys = [m["distributor_code"] for m in members]

    cy_years = sorted(int(y) for y in sf.cy.unique() if int(y) <= CY_LATEST)
    fy_years = sorted(int(y) for y in sf.fy.unique() if int(y) <= FY_LATEST and int(y) != 2023)
    keys = drill_keys()

    def pool_mix(dbs, year_col, years):
        sub = sf[sf.db.isin(dbs)]
        out = {k: [] for k in keys}
        for y in years:
            gy = sub[sub[year_col] == y]
            for k in keys:
                sl = _mix_slice(gy[mask_for(gy, k)], bvp_pns)
                if sl:
                    sl[year_col] = int(y)
                    sl["complete"] = True
                    out[k].append(sl)
        return out

    mix_peer_cy = pool_mix(peer_keys, "cy", cy_years)
    mix_net_cy = pool_mix(net_keys, "cy", cy_years)
    mix_peer_fy = pool_mix(peer_keys, "fy", fy_years)
    mix_net_fy = pool_mix(net_keys, "fy", fy_years)

    def pool_ord(dbs, year_col, years):
        sub = sf[sf.db.isin(dbs)]
        rows = []
        for y in years:
            sl = _order_slice(sub[sub[year_col] == y], RUSH, STOCK_AS_SOR, NON_ORDER_SATY)
            if sl:
                sl[year_col] = int(y)
                sl["complete"] = True
                rows.append(sl)
        return rows

    pms_path = os.path.join(DERIVED, "pms_capture_by_db_year.csv")
    pms_peer = {"available": False}
    pms_net = {"available": False}
    pms_peer_by_cat = {}
    pms_net_by_cat = {}
    if os.path.exists(pms_path):
        pms = pd.read_csv(pms_path)
        ptot = pms[(pms.line_type == "total") & (pms.year == CY_LATEST)]
        p_peer = ptot[ptot.distributor_code.isin(peer_keys)]
        p_net = ptot[ptot.distributor_code.isin(net_keys)]

        def cap_block(frame):
            if not len(frame) or float(frame.expected_qty.sum() or 0) == 0:
                return {"available": False}
            return {
                "available": True,
                "capture_pct": round(100.0 * float(frame.actual_qty.sum())
                                     / float(frame.expected_qty.sum()), 2),
                "actual_qty": _r2(frame.actual_qty.sum()),
                "expected_qty": _r2(frame.expected_qty.sum()),
                "n_dbs": int(frame.distributor_code.nunique()),
            }

        pms_peer = cap_block(p_peer)
        pms_net = cap_block(p_net)
        for cat, g in p_peer.groupby("pms_category"):
            if float(g.expected_qty.sum() or 0):
                pms_peer_by_cat[str(cat)] = round(
                    100.0 * float(g.actual_qty.sum()) / float(g.expected_qty.sum()), 2)
        for cat, g in p_net.groupby("pms_category"):
            if float(g.expected_qty.sum() or 0):
                pms_net_by_cat[str(cat)] = round(
                    100.0 * float(g.actual_qty.sum()) / float(g.expected_qty.sum()), 2)

    return {
        "sf": sf,
        "bvp_pns": bvp_pns,
        "members": members,
        "peer_keys": peer_keys,
        "cy_years": cy_years,
        "fy_years": fy_years,
        "mix_peer_cy": mix_peer_cy,
        "mix_net_cy": mix_net_cy,
        "mix_peer_fy": mix_peer_fy,
        "mix_net_fy": mix_net_fy,
        "ord_peer_cy": pool_ord(peer_keys, "cy", cy_years),
        "ord_net_cy": pool_ord(net_keys, "cy", cy_years),
        "ord_peer_fy": pool_ord(peer_keys, "fy", fy_years),
        "ord_net_fy": pool_ord(net_keys, "fy", fy_years),
        "pms_peer": pms_peer,
        "pms_net": pms_net,
        "pms_peer_by_cat": pms_peer_by_cat,
        "pms_net_by_cat": pms_net_by_cat,
        "cy_latest": CY_LATEST,
        "fy_latest": FY_LATEST,
    }


def network_bundle():
    global _CACHE
    if _CACHE is None:
        _CACHE = build_network_bundle()
    return _CACHE


def _align_mix(this_rows, peer_rows, net_rows, year_col):
    by_p = {r[year_col]: r for r in (peer_rows or [])}
    by_n = {r[year_col]: r for r in (net_rows or [])}
    out = []
    for r in this_rows or []:
        y = r.get(year_col)
        p, n = by_p.get(y) or {}, by_n.get(y) or {}
        rec = dict(r)
        rec["lcv_peer_bvp_share_pct"] = p.get("bvp_share_pct")
        rec["lcv_peer_genuine_share_pct"] = p.get("genuine_share_pct")
        rec["network_bvp_share_pct"] = n.get("bvp_share_pct")
        rec["network_genuine_share_pct"] = n.get("genuine_share_pct")
        rec["lcv_peer_bvp_eur"] = p.get("bvp_eur")
        rec["network_bvp_eur"] = n.get("bvp_eur")
        out.append(rec)
    return out


def _peer_member_label(m):
    key = str(m.get("distributor_code") or m.get("key") or "")
    lab = str(m.get("gps_label") or key)
    pretty = key.replace("_", " ").title()
    if lab.upper() == key.upper():
        return lab
    if pretty.lower() in lab.lower():
        return lab
    return f"{lab}/{pretty}"


def _legend_line(peer_members):
    labels = [_peer_member_label(m) for m in peer_members]
    n = len(labels)
    shown = ", ".join(labels[:4]) + (", …" if n > 4 else "")
    return f"LCV peer (≥90% LCV euros): {shown} ({n} DBs)"


def _this_book_note(me):
    if me.get("in_peer_set"):
        return "This book is in the LCV-peer set."
    share = me.get("lcv_share_pct")
    if share is None:
        return "Compared to LCV peer — this book is not in the set."
    return f"Compared to LCV peer — this book is {share}% LCV, not in the set."


def _align_ord(this_rows, peer_rows, net_rows, year_col):
    by_p = {r[year_col]: r for r in (peer_rows or [])}
    by_n = {r[year_col]: r for r in (net_rows or [])}
    out = []
    for r in this_rows or []:
        if not r.get("complete") and not r.get("complete_cy"):
            continue
        y = r.get(year_col)
        p, n = by_p.get(y) or {}, by_n.get(y) or {}
        rec = {
            year_col: y,
            "complete": True,
            "stock_pct": r.get("stock_pct"),
            "rush_class_pct": r.get("rush_class_pct"),
            "other_coded_pct": r.get("other_coded_pct"),
            "lcv_peer_stock_pct": p.get("stock_pct"),
            "lcv_peer_rush_pct": p.get("rush_class_pct"),
            "network_stock_pct": n.get("stock_pct"),
            "network_rush_pct": n.get("rush_class_pct"),
        }
        out.append(rec)
    return out


def attach_compare_and_drill(L, db):
    """Stamp mix drill + LCV-peer overlays. Self is excluded from the peer average."""
    B = network_bundle()
    sf = B["sf"]
    mine = sf[sf.db == db].copy()
    peer_others = [k for k in B["peer_keys"] if k != db]

    # Rebuild peer mix excluding this DB so the overlay is a true compare.
    from build_ledger import RUSH, STOCK_AS_SOR, NON_ORDER_SATY
    keys = drill_keys()
    cy_years, fy_years = B["cy_years"], B["fy_years"]

    def pool_mix(dbs, year_col, years):
        out = {k: [] for k in keys}
        if not dbs:
            return out
        sub = sf[sf.db.isin(dbs)]
        for y in years:
            gy = sub[sub[year_col] == y]
            for k in keys:
                sl = _mix_slice(gy[mask_for(gy, k)], B["bvp_pns"])
                if sl:
                    sl[year_col] = int(y)
                    sl["complete"] = True
                    out[k].append(sl)
        return out

    def pool_ord(dbs, year_col, years):
        if not dbs:
            return []
        sub = sf[sf.db.isin(dbs)]
        rows = []
        for y in years:
            sl = _order_slice(sub[sub[year_col] == y], RUSH, STOCK_AS_SOR, NON_ORDER_SATY)
            if sl:
                sl[year_col] = int(y)
                sl["complete"] = True
                rows.append(sl)
        return rows

    mix_this_cy = {}
    mix_this_fy = {}
    pns_cy = {}
    pns_fy = {}
    for k in keys:
        mix_this_cy[k] = []
        mix_this_fy[k] = []
        for y in cy_years:
            g = mine[(mine.cy == y) & mask_for(mine, k)]
            sl = _mix_slice(g, B["bvp_pns"])
            if sl:
                sl["cy"] = int(y)
                sl["complete"] = True
                mix_this_cy[k].append(sl)
        for y in fy_years:
            g = mine[(mine.fy == y) & mask_for(mine, k)]
            sl = _mix_slice(g, B["bvp_pns"])
            if sl:
                sl["fy"] = int(y)
                sl["complete"] = True
                mix_this_fy[k].append(sl)
        last_cy = mix_this_cy[k][-1]["cy"] if mix_this_cy[k] else None
        last_fy = mix_this_fy[k][-1]["fy"] if mix_this_fy[k] else None
        pns_cy[k] = _pn_table(mine[(mine.cy == last_cy) & mask_for(mine, k)], B["bvp_pns"]) if last_cy else []
        pns_fy[k] = _pn_table(mine[(mine.fy == last_fy) & mask_for(mine, k)], B["bvp_pns"]) if last_fy else []

    mix_peer_cy = pool_mix(peer_others, "cy", cy_years)
    mix_peer_fy = pool_mix(peer_others, "fy", fy_years)

    series_cy = {k: _align_mix(mix_this_cy[k], mix_peer_cy[k], B["mix_net_cy"][k], "cy") for k in keys}
    series_fy = {k: _align_mix(mix_this_fy[k], mix_peer_fy[k], B["mix_net_fy"][k], "fy") for k in keys}

    # Drop empty children from the dropdown (this book has no euros there).
    opts = family_options()
    for fam in opts:
        if fam["key"] == "all":
            continue
        fam["children"] = [
            c for c in fam["children"]
            if series_cy.get(f"{fam['key']}.{c['key']}") or series_fy.get(f"{fam['key']}.{c['key']}")
        ]

    me = next(m for m in B["members"] if m["distributor_code"] == db)
    peer_members = sorted(
        [m for m in B["members"] if m["in_peer_set"]],
        key=lambda m: (-(m.get("billed_cy_eur") or 0), m.get("gps_label") or ""),
    )
    L["sections"]["genuine_vs_bvp"]["drill"] = {
        "family_options": opts,
        "default_family": "all",
        "default_leaf": None,
        "series": {"cy": series_cy, "fy": series_fy},
        "pns": {"cy": pns_cy, "fy": pns_fy},
        "one_grain_note": (
            "One evolution pair plus the part-number table. Changing the dropdown re-filters "
            "the same charts — it does not add a chart per family."
        ),
    }

    ord_peer_cy = pool_ord(peer_others, "cy", cy_years)
    ord_peer_fy = pool_ord(peer_others, "fy", fy_years)
    hist = (L["sections"].get("order_pattern") or {}).get("history") or {}
    L["sections"]["order_pattern"]["compare"] = {
        "cy": _align_ord(hist.get("rows") or [], ord_peer_cy, B["ord_net_cy"], "cy"),
        "fy": _align_ord(hist.get("fy_rows") or [], ord_peer_fy, B["ord_net_fy"], "fy"),
        "label_lcv_peer": "LCV peer average",
        "label_network": "All-network average",
        "peer_excludes_self": True,
    }
    peer_fam_cy = {}
    if peer_others:
        sub = sf[(sf.db.isin(peer_others)) & (sf.cy == B["cy_latest"])]
        for cat, g in sub.groupby("pms_cat"):
            sl = _order_slice(g, RUSH, STOCK_AS_SOR, NON_ORDER_SATY)
            if sl:
                peer_fam_cy[str(cat)] = sl
    mr = (L["sections"].get("order_pattern") or {}).get("meeting_read") or {}
    for row in mr.get("by_pms_family") or []:
        p = peer_fam_cy.get(str(row.get("pms_category") or "")) or {}
        row["lcv_peer_stock_pct"] = p.get("stock_pct")
        row["lcv_peer_rush_pct"] = p.get("rush_class_pct")
        row["lcv_peer_other_coded_pct"] = p.get("other_coded_pct")
    if mr:
        mr["lcv_peer_overlay"] = (
            "LCV peer stock/rush % on the same PMS family, pooled billed euros of the "
            "named ≥90% LCV set excluding this book. Not all-network."
        )
        L["sections"]["order_pattern"]["meeting_read"] = mr

    pms = L["sections"].get("pms") or {}
    if pms.get("available"):
        pms_path = os.path.join(DERIVED, "pms_capture_by_db_year.csv")
        peer_cap = None
        peer_by_cat = dict(B["pms_peer_by_cat"])
        if os.path.exists(pms_path) and peer_others:
            ptot = pd.read_csv(pms_path)
            ptot = ptot[(ptot.line_type == "total") & (ptot.year == B["cy_latest"])]
            p_peer = ptot[ptot.distributor_code.isin(peer_others)]
            if len(p_peer) and float(p_peer.expected_qty.sum() or 0):
                peer_cap = round(100.0 * float(p_peer.actual_qty.sum())
                                 / float(p_peer.expected_qty.sum()), 2)
                peer_by_cat = {}
                for cat, g in p_peer.groupby("pms_category"):
                    if float(g.expected_qty.sum() or 0):
                        peer_by_cat[str(cat)] = round(
                            100.0 * float(g.actual_qty.sum()) / float(g.expected_qty.sum()), 2)
        elif B["pms_peer"].get("available"):
            peer_cap = B["pms_peer"].get("capture_pct")
        this_cap = pms.get("capture_pct_total")
        pms["lcv_peer_capture_pct"] = peer_cap
        pms["vs_lcv_peer_pp"] = (
            round(this_cap - peer_cap, 1) if this_cap is not None and peer_cap is not None else None
        )
        for cat in pms.get("by_category") or []:
            key = cat.get("pms_category")
            pc = peer_by_cat.get(key)
            cat["lcv_peer_capture_pct"] = pc
            if cat.get("capture_pct") is not None and pc is not None:
                cat["vs_lcv_peer_pp"] = round(cat["capture_pct"] - pc, 1)
            else:
                cat["vs_lcv_peer_pp"] = None
        pms["compare_note"] = (
            "LCV peer is the meaningful compare (DBs whose parc euro-mix is ≥90% LCV). "
            "All-network stays as a thinner reference. GPS% is not invented on calendar year."
        )
        L["sections"]["pms"] = pms

    member_labels = [_peer_member_label(m) for m in peer_members]
    legend_line = _legend_line(peer_members)
    this_note = _this_book_note(me)

    strat = L["sections"].get("lost_sales_strategy") or {}
    pms_by = {c.get("pms_category"): c for c in (pms.get("by_category") or [])}
    for f in strat.get("family_rows") or []:
        cat = pms_by.get(f.get("family")) or {}
        f["pms_lcv_peer_capture_pct"] = cat.get("lcv_peer_capture_pct")
        f["pms_vs_lcv_peer_pp"] = cat.get("vs_lcv_peer_pp")
        f["pms_network_capture_pct"] = cat.get("network_capture_pct")
        vs = f.get("pms_vs_lcv_peer_pp")
        peer_bit = ""
        if vs is not None:
            side = "behind" if vs < 0 else "ahead of"
            peer_bit = f" PMS capture is {abs(vs)} pp {side} LCV peer."
        base = f.get("action") or f.get("first_lever") or ""
        if peer_bit and "LCV peer" not in base:
            f["action"] = (base.rstrip(".") + "." + peer_bit).strip()
        elif not f.get("action"):
            f["action"] = base
    if strat:
        L["sections"]["lost_sales_strategy"] = strat

    L["compare"] = {
        "lcv_peer_set": {
            "threshold_pct": LCV_PEER_THRESHOLD,
            "formula": (
                "LCV share = (V19 CY2025 LCV units × €250 ISZE-net rate) ÷ "
                "(that LCV wallet + LD/MD/F-Series × v9 base rates). "
                "Peer = share ≥ 90%. IBX is BELGIUM / sold-to 90 — included when it qualifies. "
                "Complete-CY billed euros (credits out) stamp book size; sales lines have no "
                "vehicle segment so SKU-level LCV billed cannot be split. "
                "Turkey and MIDI are not ISZE distributors and are not in the set. "
                "UMI 1797 is never blended with UTI 1799."
            ),
            "this_db": me,
            "members": [
                {"key": m["distributor_code"], "gps_label": m["gps_label"],
                 "display": m["display"], "lcv_share_pct": m["lcv_share_pct"],
                 "billed_cy_eur": m["billed_cy_eur"], "registry_segment": m["registry_segment"],
                 "method": m["method"], "legend_label": _peer_member_label(m)}
                for m in peer_members
            ],
            "member_labels": member_labels,
            "legend_line": legend_line,
            "this_book_note": this_note,
            "n": len(peer_members),
            "this_in_set": bool(me["in_peer_set"]),
            "peer_average_excludes_self": True,
            "tooltip": {
                "formula": (
                    "Peer set = registry DBs with LCV euro-share ≥ 90%. "
                    "Share uses V19 CY2025 UIO × ISZE-net rate (LCV €250 / CV v9 base). "
                    "Named set, not an anonymous line. Overlay on mix, orders, PMS and "
                    "lost-sales is the pooled book of those DBs excluding this one."
                ),
                "snapshot": f"Complete CY{B['cy_latest']} · credits excluded · registry only",
                "not_included": (
                    "Turkey, MIDI Europe. Incomplete years. Not a calendar-year GPS%. "
                    "Not the PMS-by-DB year-to-date file. UTI is not UMI."
                ),
            },
        }
    }
    return L
