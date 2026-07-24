"""
Business-facing product navigation for BVP dashboards (catalog-wide, sales-scoped per DB).
"""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from config import DERIVED_DIR

# Legacy strict-PMS slice (capture tab / PRISM PMS categories only)
FILTERS_SUBCATEGORIES = ["oil_filter", "fuel_filter", "air_filter"]
BRAKES_SUBCATEGORIES = ["brake_pad", "brake_shoe"]
CLUTCH_SUBCATEGORIES = ["clutch_disc", "clutch_pressure_plate"]

PMS_STRICT_SUBCATEGORIES: tuple[str, ...] = (
    *FILTERS_SUBCATEGORIES,
    *BRAKES_SUBCATEGORIES,
    *CLUTCH_SUBCATEGORIES,
)

# Backward compatibility
IN_SCOPE_SUBCATEGORIES = PMS_STRICT_SUBCATEGORIES

SUBGROUP_LABELS: dict[str, str] = {
    "oil_filter": "Oil filter",
    "fuel_filter": "Fuel filter",
    "air_filter": "Air filter",
    "blower_filter": "Cabin / blower filter",
    "urea_filter": "Urea (AdBlue) filter",
    "brake_pad": "Brake pads",
    "brake_shoe": "Brake shoes",
    "brake_lining": "Brake lining",
    "brake_rotor": "Brake rotor",
    "clutch_kit": "Clutch kit",
    "clutch_disc": "Clutch disc",
    "clutch_pressure_plate": "Clutch pressure plate",
    "clutch_booster": "Clutch booster",
    "release_bearing": "Release bearing",
    "pilot_bearing": "Pilot bearing",
    "center_bearing": "Center bearing",
    "shock_absorber": "Shock absorber",
    "leaf_spring": "Leaf spring",
    "bushing": "Bushing",
    "king_pin": "King pin kit",
    "wheel_pin": "Wheel pin",
    "hub_bearing": "Hub bearing",
    "hub_oil_seal": "Hub oil seal",
    "fan_belt": "Fan belt",
    "water_pump": "Water pump",
    "engine_mount": "Engine foot rubber",
    "generator": "Generator",
    "starter": "Starter",
    "wiper_blade": "Wiper blade",
}

PRODUCT_GROUPS: dict[str, dict] = {
    "filters": {
        "label": "Filters",
        "product_family": "PMS_Filters",
        "subcategories": ["oil_filter", "fuel_filter", "air_filter", "blower_filter", "urea_filter"],
        "default_subgroup": "oil_filter",
        "sort": 1,
    },
    "brakes": {
        "label": "Brakes",
        "product_family": "Brakes",
        "subcategories": ["brake_pad", "brake_shoe", "brake_lining", "brake_rotor"],
        "default_subgroup": "brake_pad",
        "sort": 2,
    },
    "clutch": {
        "label": "Clutch & driveline",
        "product_family": "Clutch_Driveline",
        "subcategories": [
            "clutch_kit",
            "clutch_disc",
            "clutch_pressure_plate",
            "clutch_booster",
            "release_bearing",
            "pilot_bearing",
            "center_bearing",
        ],
        "default_subgroup": "clutch_kit",
        "sort": 3,
    },
    "suspension": {
        "label": "Suspension & chassis",
        "product_family": "Suspension_Chassis",
        "subcategories": [
            "shock_absorber",
            "leaf_spring",
            "bushing",
            "king_pin",
            "wheel_pin",
            "hub_bearing",
            "hub_oil_seal",
        ],
        "default_subgroup": "shock_absorber",
        "sort": 4,
    },
    "engine_cooling": {
        "label": "Engine & cooling",
        "product_family": "Belts_Cooling",
        "subcategories": ["fan_belt", "water_pump", "engine_mount"],
        "default_subgroup": "fan_belt",
        "sort": 5,
    },
    "electrical": {
        "label": "Electrical",
        "product_family": "Electrical",
        "subcategories": ["generator", "starter"],
        "default_subgroup": "generator",
        "sort": 6,
    },
    "cab": {
        "label": "Cab",
        "product_family": "Cab_Misc",
        "subcategories": ["wiper_blade"],
        "default_subgroup": "wiper_blade",
        "sort": 7,
    },
}

FAMILY_TO_GROUP: dict[str, str] = {
    meta["product_family"]: gid for gid, meta in PRODUCT_GROUPS.items()
}

GROUP_ORDER: list[str] = sorted(PRODUCT_GROUPS, key=lambda g: PRODUCT_GROUPS[g]["sort"])


def catalog_subcategories() -> tuple[str, ...]:
    """All BVP catalog subgroups represented in PRODUCT_GROUPS."""
    seen: list[str] = []
    for meta in PRODUCT_GROUPS.values():
        for s in meta["subcategories"]:
            if s not in seen:
                seen.append(s)
    return tuple(seen)


@lru_cache(maxsize=1)
def _addressable_basket() -> pd.DataFrame:
    path = DERIVED_DIR / "bvp_addressable_basket.csv"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype={"genuine_pn": str, "bvp_pn": str})


def addressable_for(distributor_code: str) -> set[tuple[str, str]]:
    """Return {(subgroup, bvp_pn)} a distributor can address by lifetime Genuine sales."""
    df = _addressable_basket()
    if df.empty:
        return set()
    d = df[df["distributor_code"] == distributor_code]
    return set(zip(d["product_subgroup"].astype(str), d["bvp_pn"].astype(str)))


def addressable_subgroups_for(distributor_code: str) -> set[str]:
    df = _addressable_basket()
    if df.empty:
        return set()
    return set(df.loc[df["distributor_code"] == distributor_code, "product_subgroup"].astype(str))


def is_addressable_subgroup(distributor_code: str, subgroup: str) -> bool:
    df = _addressable_basket()
    if df.empty:
        return False
    return (
        (df["distributor_code"] == distributor_code) & (df["product_subgroup"] == subgroup)
    ).any()


def groups_for_distributor(distributor_code: str) -> list[str]:
    """Product groups with ≥1 addressable subgroup for this distributor."""
    addr = addressable_subgroups_for(distributor_code)
    if not addr:
        return list(GROUP_ORDER)
    out: list[str] = []
    for gid in GROUP_ORDER:
        if any(s in addr for s in PRODUCT_GROUPS[gid]["subcategories"]):
            out.append(gid)
    return out or list(GROUP_ORDER)


def subgroup_label(code: str | None) -> str:
    if not code or (isinstance(code, float) and pd.isna(code)):
        return "—"
    s = str(code)
    if s.endswith("_asm"):
        base = SUBGROUP_LABELS.get(s.replace("_asm", ""), s.replace("_asm", "").replace("_", " ").title())
        return f"{base} (assembly)"
    if s.endswith("_kit"):
        base = SUBGROUP_LABELS.get(s.replace("_kit", ""), s.replace("_kit", "").replace("_", " ").title())
        return f"{base} (kit)"
    return SUBGROUP_LABELS.get(s, s.replace("_", " ").title())


def group_label(group_id: str | None) -> str:
    if not group_id:
        return "—"
    return PRODUCT_GROUPS.get(group_id, {}).get("label", str(group_id))


def family_for_group(group_id: str) -> str | None:
    return PRODUCT_GROUPS.get(group_id, {}).get("product_family")


def subcategories_for_group(group_id: str) -> list[str]:
    return list(PRODUCT_GROUPS.get(group_id, {}).get("subcategories", []))


def group_for_family(product_family: str | None) -> str | None:
    if not product_family or (isinstance(product_family, float) and pd.isna(product_family)):
        return None
    return FAMILY_TO_GROUP.get(str(product_family))


def group_for_subgroup(subgroup: str | None) -> str | None:
    if not subgroup:
        return None
    s = str(subgroup)
    for gid, meta in PRODUCT_GROUPS.items():
        if s in meta["subcategories"]:
            return gid
    return None


def attach_navigation_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add product_group labels; dashboard_scope = full BVP catalog taxonomy."""
    out = df.copy()
    catalog = set(catalog_subcategories())

    if "product_family" in out.columns:
        out["product_group"] = out["product_family"].map(FAMILY_TO_GROUP)
    elif "pms_category" in out.columns:
        out["product_group"] = out["pms_category"].map(
            lambda c: group_for_subgroup(c) if pd.notna(c) else None
        )
    else:
        out["product_group"] = None

    if "product_subgroup" not in out.columns and "pms_category" in out.columns:
        out["product_subgroup"] = out["pms_category"]

    if "pms_category" in out.columns:
        out["product_subgroup"] = out["product_subgroup"].where(
            out["product_subgroup"].notna(),
            out["pms_category"],
        )

    sg = out["product_subgroup"] if "product_subgroup" in out.columns else pd.Series(dtype=object)
    out["dashboard_scope"] = sg.astype(str).isin(catalog) | sg.isna()

    out["product_group_label"] = out["product_group"].map(
        lambda g: group_label(g) if pd.notna(g) else None
    )
    out["subgroup_label"] = out["product_subgroup"].map(subgroup_label)
    return out


def filter_in_scope(
    df: pd.DataFrame,
    distributor_code: str | None = None,
) -> pd.DataFrame:
    """Catalog-wide rows; optional per-distributor addressable filter."""
    if df.empty:
        return df
    if "dashboard_scope" in df.columns:
        out = df[df["dashboard_scope"]].copy()
    elif "product_subgroup" in df.columns:
        out = df[df["product_subgroup"].isin(catalog_subcategories())].copy()
    elif "pms_category" in df.columns:
        out = df[df["pms_category"].isin(catalog_subcategories())].copy()
    else:
        out = df.copy()

    if distributor_code:
        addr = addressable_subgroups_for(distributor_code)
        if addr:
            col = "product_subgroup" if "product_subgroup" in out.columns else "pms_category"
            if col in out.columns:
                out = out[out[col].astype(str).isin(addr)]
    return out


def filter_mix_addressable(df: pd.DataFrame, distributor_code: str) -> pd.DataFrame:
    """Restrict mix/substitution rows to subgroups addressable for one distributor."""
    if df.empty or not distributor_code:
        return df
    addr = addressable_subgroups_for(distributor_code)
    if not addr:
        return df
    col = "product_subgroup" if "product_subgroup" in df.columns else "pms_category"
    if col not in df.columns:
        return df
    return df[df[col].astype(str).isin(addr)].copy()


def rollup_mix_to_group(mix_sub: pd.DataFrame) -> pd.DataFrame:
    """Sum qty/eur from subgroup mix to product_group grain."""
    if mix_sub.empty:
        return pd.DataFrame()
    keys = ["year", "distributor_code", "product_group", "product_group_label"]
    g = (
        mix_sub.groupby(keys, dropna=False)[
            ["bvp_qty", "genuine_qty", "bvp_eur", "genuine_eur", "total_qty", "total_eur"]
        ]
        .sum()
        .reset_index()
    )
    denom_qty = g["genuine_qty"] + g["bvp_qty"]
    denom_eur = g["genuine_eur"] + g["bvp_eur"]
    g["bvp_share_units"] = g["bvp_qty"] / denom_qty.replace(0, pd.NA)
    g["bvp_share_eur"] = g["bvp_eur"] / denom_eur.replace(0, pd.NA)
    return g


def clear_addressable_cache() -> None:
    _addressable_basket.cache_clear()
