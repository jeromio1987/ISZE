"""
PN-level AIM / catalog taxonomy for sell-out and GPS joins.

Sources (priority):
  1. AIM Parts Master (CY2025 workbook) — description → Category L1/L2/L3
  2. PR00 / IE40 GPT export — PN → Level 1 Family / Level 2 Group / Level 3 Type
  3. aim_gap_suggestions_*.csv — high-confidence L1/L2 for residual PNs
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import AIM_PN_CLASSIFICATION_CSV, AIM_WORKBOOK_CANDIDATES, DERIVED_DIR
from modules.bvp_analytics import normalize_pn_value

# Workbook L1 values that mean "not actually classified" — fall through to
# gap suggestions / PR00 catalog instead of letting them win on priority.
PLACEHOLDER_L1 = frozenset({"unknown", "unknown review", "other / review"})

FILTER_SUBGROUPS = frozenset({"oil_filter", "fuel_filter", "air_filter", "urea_filter"})
FILTER_CAPTURE_CATEGORIES = frozenset(
    {"oil_filter", "fuel_filter", "air_filter", "urea_filter", "blower_filter"}
)
FILTER_ELEMENT_FIG_KEYS = frozenset({"041-002", "050-002", "130-006", "873-042"})
FILTER_ASSEMBLY_FIG_KEYS = frozenset({"041-001", "050-001"})


# ─── Genuine DEF filter kits (2026-09-21) ─────────────────────────────────────
# The real AdBlue/DEF filter element is "FILTER KIT; PUMP ASM,DEF DCM S" on fig key
# 146-152 — the filter inside the DEF pump module. Its description contains "KIT" and
# "ASM", so the role inference below reads it as an assembly or a kit, and the capture
# step drops those by design; the category then held nothing that could be counted.
# These part numbers ARE the element, so the role is declared here instead of being
# guessed from the wording. The demand rate is untouched: this decides which parts the
# category covers, not what the category expects.
DEF_FILTER_ELEMENT_PNS = frozenset({
    "1876102340", "1876102341", "8981694030", "8983507160", "8983507161",
})
_DEF_FILTER_NORM = frozenset(p.lstrip("0") for p in DEF_FILTER_ELEMENT_PNS)


def resolve_filter_part_role(pn_norm: object) -> str | None:
    """The role declared for a part number, where someone has declared one.

    None means nothing is declared, so the caller falls back to the
    description-based inference exactly as before.
    """
    pn = normalize_pn_value(pn_norm) or ""
    return "element" if pn in _DEF_FILTER_NORM else None


def _norm_desc(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().str.upper()


def resolve_aim_workbook() -> Path | None:
    for p in AIM_WORKBOOK_CANDIDATES:
        if p.exists():
            return p
    return None


def load_aim_parts_master(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Parts Master", header=1)
    df.columns = [str(c).strip() for c in df.columns]
    desc_col = next(c for c in df.columns if c.lower().startswith("description"))
    out = pd.DataFrame(
        {
            "description_norm": _norm_desc(df[desc_col]),
            "aim_l1": df.get("Category L1", df.get("Category_L1")),
            "aim_l2": df.get("Category L2", df.get("Category_L2")),
            "aim_l3": df.get("Category L3", df.get("Category_L3")),
            "aim_demand_type": df.get("Demand Type", df.get("Demand_Type")),
            "aim_bucket": df.get("Bucket"),
            "aim_pricing_risk": df.get("Pricing Risk", df.get("Pricing_Risk")),
        }
    )
    out = out[out["description_norm"] != ""].drop_duplicates("description_norm")
    return out


def load_pr00_index() -> pd.DataFrame:
    path = DERIVED_DIR / "pr00_classification.csv"
    if not path.is_file():
        return pd.DataFrame()
    pr = pd.read_csv(path, dtype=str)
    pr["_pn"] = pr["pn_norm"].map(lambda x: normalize_pn_value(x) or "")
    pr = pr[pr["_pn"] != ""].drop_duplicates("_pn", keep="first")
    return pr.set_index("_pn", drop=False)


def load_gap_suggestions() -> pd.DataFrame:
    files = sorted(DERIVED_DIR.glob("aim_gap_suggestions_*.csv"))
    if not files:
        return pd.DataFrame()
    gap = pd.read_csv(files[-1], dtype=str)
    gap["_pn"] = gap["pn"].map(lambda x: normalize_pn_value(x) or "")
    gap["confidence"] = pd.to_numeric(gap.get("confidence"), errors="coerce").fillna(0)
    gap = gap[gap["confidence"] >= 3.0]
    return gap.drop_duplicates("_pn", keep="first").set_index("_pn", drop=False)


def infer_filter_part_role(
    *,
    description: object,
    level3_type: object = None,
    fig_key: object = None,
    product_subgroup: object = None,
) -> str | None:
    """element | assembly | kit — for PMS filter subgroups only."""
    sub = str(product_subgroup or "").strip()
    if sub and sub not in FILTER_SUBGROUPS:
        return None

    desc_u = str(description or "").upper()
    l3 = str(level3_type or "").lower()
    fk = str(fig_key or "").strip()

    if "HOSE" in desc_u and "FILTER" in desc_u:
        return None

    if "ELEMENT" in desc_u and "FILTER" in desc_u:
        return "element"
    if "CARTRIDGE" in desc_u:
        return "element"

    if any(tok in desc_u for tok in ("FILTER ASM", "FILTER ASSY", "FILTER; ASSY", "ASM; FILTER")):
        return "assembly"
    if "ASSY" in desc_u or " ASM" in desc_u or desc_u.startswith("ASM"):
        if "FILTER" in desc_u or sub in FILTER_SUBGROUPS:
            return "assembly"

    if "KIT" in desc_u and ("FILTER" in desc_u or sub in FILTER_SUBGROUPS):
        return "kit"

    if fk in FILTER_ELEMENT_FIG_KEYS:
        return "element"
    if fk in FILTER_ASSEMBLY_FIG_KEYS:
        return "assembly"

    if l3 in ("oil filter", "fuel filter", "air filter"):
        if "kit" in desc_u:
            return "kit"
        if "asm" in desc_u or "assy" in desc_u:
            return "assembly"
        if sub in FILTER_SUBGROUPS:
            return "element"

    return None


def filter_report_subgroup(product_subgroup: str | None, role: str | None) -> str | None:
    if not product_subgroup or product_subgroup not in FILTER_SUBGROUPS:
        return product_subgroup
    if role == "assembly":
        return f"{product_subgroup}_asm"
    if role == "kit":
        return f"{product_subgroup}_kit"
    return product_subgroup


def filter_subgroup_label(subgroup: str | None, role: str | None) -> str | None:
    from modules.bvp_product_nav import subgroup_label

    if not subgroup:
        return None
    base = subgroup_label(subgroup.replace("_asm", "").replace("_kit", ""))
    if role == "assembly" or str(subgroup).endswith("_asm"):
        return f"{base} (assembly)"
    if role == "kit" or str(subgroup).endswith("_kit"):
        return f"{base} (kit)"
    if subgroup in FILTER_SUBGROUPS:
        return f"{base} (element)"
    return base


def build_aim_pn_classification(
    part_numbers: pd.Series,
    descriptions: pd.Series | None = None,
) -> pd.DataFrame:
    """Build classification rows for the given part numbers."""
    aim_path = resolve_aim_workbook()
    aim_master = load_aim_parts_master(aim_path) if aim_path else pd.DataFrame()
    pr00 = load_pr00_index()
    gap = load_gap_suggestions()

    rows: list[dict] = []
    desc_s = descriptions if descriptions is not None else pd.Series([""] * len(part_numbers))

    for pn_raw, desc in zip(part_numbers, desc_s, strict=False):
        pn_n = normalize_pn_value(pn_raw) or ""
        if not pn_n:
            continue
        pn_out = pn_n.zfill(10) if pn_n.isdigit() else pn_n

        catalog_l1 = catalog_l2 = catalog_l3 = fig_key = None
        if not pr00.empty and pn_n in pr00.index:
            r = pr00.loc[pn_n]
            catalog_l1 = r.get("family")
            catalog_l2 = r.get("group")
            catalog_l3 = r.get("level3_type")
            fig_key = r.get("fig_key")

        desc_norm = str(desc or "").strip().upper()
        aim_l1 = aim_l2 = aim_l3 = None
        aim_source = None

        if aim_master is not None and not aim_master.empty and desc_norm:
            hit = aim_master[aim_master["description_norm"] == desc_norm]
            if not hit.empty:
                h = hit.iloc[0]
                aim_l1, aim_l2, aim_l3 = h["aim_l1"], h["aim_l2"], h["aim_l3"]
                aim_source = "aim_workbook"

        _l1_str = "" if aim_l1 is None or pd.isna(aim_l1) else str(aim_l1).strip().lower()
        _cat_str = "" if catalog_l1 is None or pd.isna(catalog_l1) else str(catalog_l1).strip().lower()
        needs_fallback = _l1_str in ("", "nan") or _l1_str in PLACEHOLDER_L1
        if needs_fallback:
            if not gap.empty and pn_n in gap.index:
                g = gap.loc[pn_n]
                aim_l1 = g.get("sug1_l1") or catalog_l1
                aim_l2 = g.get("sug1_l2") or catalog_l2
                aim_l3 = catalog_l3
                aim_source = "gap_suggestion"
            elif _cat_str and _cat_str not in PLACEHOLDER_L1:
                # catalog only overrides a workbook placeholder with a real class
                aim_l1, aim_l2, aim_l3 = catalog_l1, catalog_l2, catalog_l3
                aim_source = "pr00_catalog"

        filter_role = infer_filter_part_role(
            description=desc,
            level3_type=catalog_l3,
            fig_key=fig_key,
        )

        rows.append(
            {
                "part_number": pn_out,
                "description_norm": desc_norm,
                "aim_l1": aim_l1 if pd.notna(aim_l1) else None,
                "aim_l2": aim_l2 if pd.notna(aim_l2) else None,
                "aim_l3": aim_l3 if pd.notna(aim_l3) else None,
                "catalog_l1": catalog_l1 if pd.notna(catalog_l1) else None,
                "catalog_l2": catalog_l2 if pd.notna(catalog_l2) else None,
                "catalog_l3": catalog_l3 if pd.notna(catalog_l3) else None,
                "fig_key": fig_key if pd.notna(fig_key) else None,
                "filter_part_role": filter_role,
                "aim_source": aim_source,
            }
        )

    return pd.DataFrame(rows)


def pms_capture_eligible(
    pms_category: str | None,
    filter_part_role: str | None,
    *,
    from_registry: bool = False,
) -> bool:
    """PMS capture actuals: filter categories count service elements only (not asm/kit)."""
    if not pms_category or pms_category not in FILTER_CAPTURE_CATEGORIES:
        return True
    if from_registry:
        return True
    role = (str(filter_part_role or "")).strip().lower()
    if role in ("assembly", "kit"):
        return False
    return role == "element"


def _has_slug(val: object) -> bool:
    return pd.notna(val) and str(val).strip() not in ("", "nan")


def attach_pms_filter_roles(df: pd.DataFrame) -> pd.DataFrame:
    """Add filter_part_role, pms_capture_eligible, mix_subgroup to classified sales rows."""
    from modules.pms_engine import PMS_PN_REGISTRY

    if df.empty:
        return df
    out = df.copy()
    registry_norm = {
        (normalize_pn_value(p) or "").lstrip("0") for p in PMS_PN_REGISTRY
    }
    aim = load_aim_pn_classification()

    roles: list[str | None] = []
    eligible: list[bool] = []
    mix_sg: list[str | None] = []

    for _, row in out.iterrows():
        pn_n = (normalize_pn_value(row.get("part_number")) or "").lstrip("0")
        cat = row.get("pms_category")
        if not cat or (isinstance(cat, float) and pd.isna(cat)):
            cat = None
        else:
            cat = str(cat).strip()

        role = None
        if aim is not None and not aim.empty and pn_n and pn_n in aim.index:
            r = aim.loc[pn_n].get("filter_part_role")
            if pd.notna(r) and str(r).strip():
                role = str(r).strip()

        # A declared role wins over the description: the genuine DEF filter kit reads
        # as a kit/assembly, so the wording alone would keep it out of the count even
        # after it has been filed under the urea category.
        declared = resolve_filter_part_role(pn_n)
        if declared:
            role = declared

        if not role and cat in FILTER_CAPTURE_CATEGORIES:
            role = infer_filter_part_role(
                description=row.get("description"),
                product_subgroup=cat,
            )

        from_reg = bool(pn_n and pn_n in registry_norm)
        if from_reg and cat in FILTER_CAPTURE_CATEGORIES and not role:
            role = "element"

        roles.append(role)
        eligible.append(
            pms_capture_eligible(cat, role, from_registry=from_reg) if cat else True
        )
        sub = row.get("product_subgroup")
        if _has_slug(sub) and str(sub) not in FILTER_SUBGROUPS:
            mix_sg.append(str(sub))
        elif cat in FILTER_SUBGROUPS:
            mix_sg.append(
                filter_report_subgroup(cat, role if role else ("element" if from_reg else None))
                or cat
            )
        elif cat:
            mix_sg.append(filter_report_subgroup(cat, role) or cat)
        else:
            mix_sg.append(sub if _has_slug(sub) else None)

    out["filter_part_role"] = roles
    out["pms_capture_eligible"] = eligible
    out["mix_subgroup"] = mix_sg
    return out


def enrich_dimension_filter_roles(df_dim: pd.DataFrame) -> pd.DataFrame:
    """Add filter_part_role + pms_capture_eligible to bvp_pn_dimension."""
    from modules.pms_engine import PMS_PN_REGISTRY

    if df_dim.empty:
        return df_dim
    out = df_dim.copy()
    registry_norm = {
        (normalize_pn_value(p) or "").lstrip("0") for p in PMS_PN_REGISTRY
    }
    aim = load_aim_pn_classification()

    roles = []
    eligible = []
    for _, row in out.iterrows():
        pn_n = (normalize_pn_value(row.get("part_number")) or "").lstrip("0")
        cat = row.get("pms_category")
        cat = str(cat).strip() if pd.notna(cat) and str(cat).strip() else None
        role = None
        if not aim.empty and pn_n in aim.index:
            r = aim.loc[pn_n].get("filter_part_role")
            if pd.notna(r) and str(r).strip():
                role = str(r).strip()
        from_reg = bool(pn_n in registry_norm)
        # a declared role wins over the description, the same way it does for the
        # capture rows above (see resolve_filter_part_role)
        declared = resolve_filter_part_role(pn_n)
        if declared:
            role = declared
        if not role and cat in FILTER_CAPTURE_CATEGORIES:
            role = "element" if from_reg else None
        roles.append(role)
        eligible.append(pms_capture_eligible(cat, role, from_registry=from_reg))
    out["filter_part_role"] = roles
    out["pms_capture_eligible"] = eligible
    sg = out.get("product_subgroup", out.get("pms_category"))
    out["mix_subgroup"] = [
        filter_report_subgroup(str(c) if pd.notna(c) else "", r)
        or (str(c) if pd.notna(c) else "")
        for c, r in zip(sg, roles, strict=False)
    ]
    return out


def load_aim_pn_classification() -> pd.DataFrame:
    if not AIM_PN_CLASSIFICATION_CSV.is_file():
        return pd.DataFrame()
    df = pd.read_csv(AIM_PN_CLASSIFICATION_CSV, dtype=str)
    df["part_number"] = df["part_number"].str.strip()
    df["_pn"] = df["part_number"].map(lambda x: normalize_pn_value(x) or "")
    return df.drop_duplicates("_pn", keep="first").set_index("_pn", drop=False)
