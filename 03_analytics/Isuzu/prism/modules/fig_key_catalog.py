"""
Fig-key catalog layer (GPS V2) — PN → EPC fig key + PR00 family/group.

Priority:
  1. fig_key_pn_overrides.csv (hand/EPC basket)
  2. PMS_PN_REGISTRY + category_default_fig_key
  3. bvp_pn_dimension pms_category + defaults
  4. pr00_classification.csv — fig_key from PR00 Fig No. + Key No. (~163k PNs)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from modules.bvp_analytics import normalize_pn_value
from modules.pms_engine import PMS_PN_REGISTRY

_TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "data" / "fig_key_taxonomy.yaml"
_OVERRIDES_PATH = Path(__file__).resolve().parents[1] / "data" / "fig_key_pn_overrides.csv"


def load_taxonomy(path: Path | None = None) -> dict:
    p = path or _TAXONOMY_PATH
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def load_pn_overrides(path: Path | None = None) -> pd.DataFrame:
    p = path or _OVERRIDES_PATH
    if not p.is_file():
        return pd.DataFrame(columns=["part_number", "fig_key", "source"])
    df = pd.read_csv(p, dtype=str)
    df["part_number"] = df["part_number"].map(normalize_pn_value)
    return df.dropna(subset=["part_number"])


def fig_key_for_category(taxonomy: dict, pms_category: str | None) -> str | None:
    if not pms_category:
        return None
    defaults = taxonomy.get("category_default_fig_key") or {}
    return defaults.get(pms_category)


def fig_meta(taxonomy: dict, fig_key: str | None) -> dict:
    if not fig_key:
        return {}
    return (taxonomy.get("pms_fig_keys") or {}).get(fig_key) or {}


def pms_category_from_pr00(
    taxonomy: dict,
    *,
    pr00_group: str | None,
    level3_type: str | None,
    fig_key: str | None,
) -> str | None:
    """Infer PMS category from PR00 group/level3 when not on BVP sheet."""
    fk = (fig_key or "").strip()
    l3 = (level3_type or "").lower()
    grp = (pr00_group or "").lower()

    for rule in taxonomy.get("pr00_pms_category_rules") or []:
        if rule.get("match_fig_key") and fk == rule["match_fig_key"]:
            return rule.get("category")
        m3 = rule.get("match_level3")
        if m3 and m3 in l3:
            return rule.get("category")

    for rule in taxonomy.get("pr00_pms_category_rules") or []:
        mg = (rule.get("match_group") or "").lower()
        if not mg or mg not in grp:
            continue
        for needle, cat in (rule.get("level3_contains") or {}).items():
            if needle in l3:
                return cat
        return rule.get("default")

    return None


def build_parts_catalog_dimension(
    *,
    pr00_csv: Path,
    bvp_dimension_csv: Path,
    taxonomy_path: Path | None = None,
    overrides_path: Path | None = None,
) -> pd.DataFrame:
    """One row per part_number with fig_key + PR00 + PMS tags."""
    tax = load_taxonomy(taxonomy_path)
    pms_keys = tax.get("pms_fig_keys") or {}

    rows: dict[str, dict] = {}

    def upsert(pn: str, **kwargs) -> None:
        pn_n = normalize_pn_value(pn)
        if not pn_n:
            return
        base = rows.setdefault(
            pn_n,
            {
                "part_number": pn_n.zfill(10) if pn_n.isdigit() else pn_n,
                "fig_key": None,
                "fig_key_label": None,
                "pms_category": None,
                "classification_source": None,
                "pr00_family": None,
                "pr00_group": None,
                "pr00_level3_type": None,
                "pms_registry": False,
                "in_bvp_catalog": False,
            },
        )
        for k, v in kwargs.items():
            if v is None:
                continue
            if k == "pms_registry" and v is True:
                base["pms_registry"] = True
                continue
            if k == "in_bvp_catalog" and v is True:
                base["in_bvp_catalog"] = True
                continue
            if k == "fig_key" and v:
                base["fig_key"] = v
                continue
            if base.get(k) is None or k in (
                "fig_key_label",
                "pms_category",
                "classification_source",
                "pr00_family",
                "pr00_group",
                "pr00_level3_type",
            ):
                base[k] = v

    # PR00 (broad catalogue — fig_key for ~all OE PNs)
    if pr00_csv.is_file():
        pr00 = pd.read_csv(pr00_csv, dtype=str)
        pms_keys = tax.get("pms_fig_keys") or {}
        for _, r in pr00.iterrows():
            pn = str(r.get("pn_norm", "")).strip()
            fk = r.get("fig_key")
            fk = str(fk).strip() if pd.notna(fk) and str(fk).strip() else None
            pms_cat = None
            fig_lbl = r.get("level3_type") or r.get("group")
            if fk and fk in pms_keys:
                pms_cat = pms_keys[fk].get("pms_category")
                fig_lbl = pms_keys[fk].get("label") or fig_lbl
            if not pms_cat:
                pms_cat = pms_category_from_pr00(
                    tax,
                    pr00_group=r.get("group"),
                    level3_type=r.get("level3_type"),
                    fig_key=fk,
                )
            upsert(
                pn,
                fig_key=fk,
                fig_key_label=str(fig_lbl) if pd.notna(fig_lbl) and str(fig_lbl).strip() else None,
                pms_category=pms_cat,
                pr00_family=r.get("family"),
                pr00_group=r.get("group"),
                pr00_level3_type=r.get("level3_type"),
                classification_source="pr00",
            )

    # BVP dimension (PMS-flagged catalogue)
    if bvp_dimension_csv.is_file():
        dim = pd.read_csv(bvp_dimension_csv, dtype=str)
        for _, r in dim.iterrows():
            pn = r.get("part_number", "")
            cat = r.get("pms_category")
            if pd.isna(cat) or not str(cat).strip():
                sub = r.get("product_subgroup")
                if str(r.get("pms_flag", "")).lower() in ("true", "1") and pd.notna(sub):
                    cat = sub
            cat = cat if pd.notna(cat) and str(cat).strip() else None
            fk = fig_key_for_category(tax, cat) if cat else None
            meta = fig_meta(tax, fk)
            upsert(
                pn,
                pms_category=cat,
                fig_key=fk,
                fig_key_label=meta.get("label"),
                in_bvp_catalog=str(r.get("in_bvp_catalog", "")).lower() in ("true", "1"),
                classification_source="bvp_dimension",
            )

    # PMS registry (authoritative for pilot PNs)
    for pn, meta in PMS_PN_REGISTRY.items():
        cat = meta.get("category")
        fk = fig_key_for_category(tax, cat)
        fmeta = fig_meta(tax, fk)
        upsert(
            pn,
            pms_category=cat,
            fig_key=fk,
            fig_key_label=fmeta.get("label"),
            pms_registry=True,
            classification_source="pms_registry",
        )

    # Hand overrides (EPC basket) win over PR00 / registry defaults
    overrides = load_pn_overrides(overrides_path)
    for _, r in overrides.iterrows():
        fk = str(r.get("fig_key", "")).strip() or None
        fmeta = fig_meta(tax, fk)
        upsert(
            r["part_number"],
            fig_key=fk,
            fig_key_label=fmeta.get("label"),
            pms_category=fmeta.get("pms_category") or None,
            classification_source=r.get("source") or "fig_key_override",
        )

    # Label any fig_key that matches the 4 PMS EPC keys
    for base in rows.values():
        fk = base.get("fig_key")
        if fk and fk in pms_keys and not base.get("fig_key_label"):
            base["fig_key_label"] = pms_keys[fk].get("label")
        if fk and fk in pms_keys and not base.get("pms_category"):
            base["pms_category"] = pms_keys[fk].get("pms_category")

    df = pd.DataFrame(rows.values())
    if df.empty:
        return df
    return df.sort_values("part_number").reset_index(drop=True)


def load_catalog_index(csv_path: Path | None = None) -> pd.DataFrame:
    """Indexed by normalised PN (no leading zeros) for joins."""
    from config import PARTS_CATALOG_DIMENSION_CSV

    path = csv_path or PARTS_CATALOG_DIMENSION_CSV
    if not path.is_file():
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str)
    df["_pn"] = df["part_number"].map(lambda x: normalize_pn_value(x) or "")
    df = df[df["_pn"] != ""].drop_duplicates("_pn", keep="first")
    return df.set_index("_pn", drop=False)


def category_hint_for_pn(
    pn_norm: str,
    catalog_row: pd.Series | None,
    description: str | None = None,
) -> str:
    """Single-line label for GPS Part Explorer (registry → fig key → PR00 → keywords)."""
    from modules.pms_engine import CATEGORY_LABELS, PMS_PN_REGISTRY

    if catalog_row is not None and not catalog_row.empty:
        reg = str(catalog_row.get("pms_registry", "")).lower() in ("true", "1")
        fk = catalog_row.get("fig_key")
        if pd.notna(fk) and str(fk).strip():
            lbl = catalog_row.get("fig_key_label") or catalog_row.get("pms_category") or fk
            tag = "✅ PMS" if reg else "🔑 FIG"
            model = ""
            if reg and pn_norm in PMS_PN_REGISTRY:
                model = f" ({PMS_PN_REGISTRY[pn_norm]['model']})"
            return f"{tag} {fk}: {lbl}{model}"
        if reg and pn_norm in PMS_PN_REGISTRY:
            m = PMS_PN_REGISTRY[pn_norm]
            cat_label = CATEGORY_LABELS.get(m["category"], m["category"])
            return f"✅ PMS: {cat_label} ({m['model']})"
        grp = catalog_row.get("pr00_group")
        if pd.notna(grp) and str(grp).strip():
            fam = catalog_row.get("pr00_family")
            if pd.notna(fam) and str(fam).strip():
                return f"📘 {fam} / {grp}"
            return f"📘 {grp}"

    if pn_norm in PMS_PN_REGISTRY:
        m = PMS_PN_REGISTRY[pn_norm]
        cat_label = CATEGORY_LABELS.get(m["category"], m["category"])
        return f"✅ PMS: {cat_label} ({m['model']})"

    return _keyword_category_hint(description)


def _keyword_category_hint(description: str | None) -> str:
    if description is None or (isinstance(description, float) and pd.isna(description)):
        return "—"
    desc_u = str(description).upper()
    is_brake = "BRAKE" in desc_u or "BRK" in desc_u
    if "OIL" in desc_u and "FILTER" in desc_u:
        return "🟦 PMS: Oil Filter"
    if "AIR" in desc_u and "FILTER" in desc_u:
        return "🟦 PMS: Air Filter"
    if "FUEL" in desc_u and "FILTER" in desc_u:
        return "🟦 PMS: Fuel Filter"
    if "ADBLUE" in desc_u or "AD BLUE" in desc_u:
        return "🟦 PMS: AdBlue Filter"
    if "FILTER" in desc_u:
        return "🔷 Filter (other)"
    if "PAD" in desc_u and is_brake:
        return "🟧 Wear: Brake Pad"
    if ("DISC" in desc_u or "ROTOR" in desc_u) and is_brake:
        return "🟧 Wear: Brake Disc"
    if "CALIPER" in desc_u:
        return "🟧 Wear: Brake Caliper"
    if "SHOE" in desc_u and is_brake:
        return "🟧 Wear: Brake Shoe"
    if "CLUTCH" in desc_u:
        return "🟧 Wear: Clutch"
    if "WIPER" in desc_u or "BLADE" in desc_u:
        return "🟧 Wear: Wiper"
    if "BELT" in desc_u:
        return "🟧 Wear: Belt"
    return "⬜ Unclassified"


def enrich_top_parts_table(df_parts: pd.DataFrame, catalog: pd.DataFrame | None = None) -> pd.DataFrame:
    """Add fig_key, pms_category, category_hint from parts_catalog_dimension."""
    if df_parts.empty:
        return df_parts
    cat = catalog if catalog is not None else load_catalog_index()
    out = df_parts.copy()
    # sales_fact carries fig_key since 2026-07-02 — drop any incoming copies so
    # the concat below cannot create duplicate columns.
    out = out.drop(columns=[c for c in ("fig_key", "fig_key_source", "pms_category", "category_hint") if c in out.columns])
    out["_pn"] = out["part_number"].astype(str).str.strip().str.lstrip("0")

    if cat.empty:
        out["fig_key"] = None
        out["pms_category"] = None
        out["category_hint"] = out.apply(
            lambda r: category_hint_for_pn(r["_pn"], None, r.get("description")),
            axis=1,
        )
        return out.drop(columns=["_pn"])

    def _row(r):
        pn = r["_pn"]
        row = cat.loc[pn] if pn in cat.index else None
        fk = row["fig_key"] if row is not None and pd.notna(row.get("fig_key")) else None
        pc = row["pms_category"] if row is not None and pd.notna(row.get("pms_category")) else None
        hint = category_hint_for_pn(pn, row, r.get("description"))
        return pd.Series({"fig_key": fk, "pms_category": pc, "category_hint": hint})

    extra = out.apply(_row, axis=1)
    out = pd.concat([out, extra], axis=1)
    return out.drop(columns=["_pn"])
