"""One-shot aggregator for IBX Body parts H1 canvas — writes JSON next to itself."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
CSV = ROOT / "09_meetings/IBX_Sales_Review_2026/IBX_Body_parts_all_purchases_H1_2025_2026.csv"
DER = ROOT / "01_data/00_derived"
OUT = ROOT / "09_meetings/IBX_Sales_Review_2026/_body_canvas_data.json"

KW_RULES = [
    ("Glass / window", r"GLASS|WINDSHIELD"),
    ("Bumper", r"BUMPER"),
    ("Fender", r"FENDER"),
    ("Panel", r"PANEL|HOOD|SIDE GATE|DEFLECTOR"),
    ("Door", r"DOOR"),
    ("Trim / molding", r"MOLDING|MOULDING|WEATHERSTRIP"),
    ("Grille", r"GRILLE|GRILL"),
    ("Step / guard", r"STEP"),
    ("Handle / lock", r"HANDLE|LATCH|LOCK|HINGE"),
    ("Body structure", r"RAIL|FRAME"),
]


def norm_pn(x) -> str:
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def kw_kind(desc: str) -> str:
    d = (desc or "").upper()
    for kind, pat in KW_RULES:
        if re.search(pat, d):
            return kind
    return "Other body"


def main() -> None:
    df = pd.read_csv(CSV)
    df["pn"] = df["PN"].map(norm_pn)
    df["desc"] = df["description"].fillna("").astype(str)
    for c in ["H1'25 EUR", "H1'25 qty", "H1'26 EUR", "H1'26 qty", "Delta EUR", "Delta qty"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    cat = pd.read_csv(DER / "parts_catalog_dimension.csv", dtype=str, low_memory=False)
    cat["pn"] = cat["part_number"].map(norm_pn)
    l3 = cat.drop_duplicates("pn").set_index("pn")["pr00_level3_type"].fillna("").to_dict()
    df["kind"] = df["pn"].map(lambda p: (l3.get(p) or "").strip() or "Other body")
    mask = df["kind"].eq("Other body")
    df.loc[mask, "kind"] = df.loc[mask, "desc"].map(kw_kind)

    # Model join attempt (expected sparse / empty for Body)
    model_map: dict[str, set[str]] = {}
    for fname, pn_col in [
        ("genuine_bvp_crossref.csv", "genuine_pn"),
        ("bvp_addressable_basket.csv", "genuine_pn"),
    ]:
        src = pd.read_csv(DER / fname, dtype=str, low_memory=False, usecols=[pn_col, "vehicle_model"])
        for _, r in src.iterrows():
            pn = norm_pn(r[pn_col])
            vm = str(r.get("vehicle_model") or "").strip()
            if not vm or vm.lower() in {"nan", "none", "null"}:
                continue
            model_map.setdefault(pn, set()).add(vm)

    def model_label(pn: str) -> str:
        ms = sorted(model_map.get(pn, set()))
        return ", ".join(ms)[:80] if ms else "model unknown"

    df["model"] = df["pn"].map(model_label)
    mapped = df["model"] != "model unknown"

    e25 = float(df["H1'25 EUR"].sum())
    e26 = float(df["H1'26 EUR"].sum())
    q25 = float(df["H1'25 qty"].sum())
    q26 = float(df["H1'26 qty"].sum())
    de = e26 - e25

    by = (
        df.groupby("kind", as_index=False)
        .agg(
            e25=("H1'25 EUR", "sum"),
            e26=("H1'26 EUR", "sum"),
            q26=("H1'26 qty", "sum"),
            n_pn=("pn", "nunique"),
        )
        .sort_values("e26", ascending=False)
    )
    by["de"] = by["e26"] - by["e25"]
    by_de = by.sort_values("de", ascending=False)

    top = df.sort_values("H1'26 EUR", ascending=False).head(15)
    by_model = (
        df.groupby("model", as_index=False)
        .agg(e25=("H1'25 EUR", "sum"), e26=("H1'26 EUR", "sum"), n_pn=("pn", "nunique"))
        .sort_values("e26", ascending=False)
    )
    by_model["de"] = by_model["e26"] - by_model["e25"]
    known = by_model[by_model["model"] != "model unknown"].head(10)

    out = {
        "kpi": {
            "e25": round(e25, 2),
            "e26": round(e26, 2),
            "de": round(de, 2),
            "dpct": round(100.0 * de / e25, 1) if e25 else None,
            "q25": int(round(q25)),
            "q26": int(round(q26)),
            "pn_any": int(len(df)),
            "pn_active_26": int(((df["H1'26 EUR"] > 0) | (df["H1'26 qty"] > 0)).sum()),
            "model_cov_pn_pct": round(float(mapped.mean() * 100), 1),
            "model_cov_eur26_pct": round(float(df.loc[mapped, "H1'26 EUR"].sum() / e26 * 100), 1)
            if e26 and mapped.any()
            else 0.0,
            "n_mapped_pn": int(mapped.sum()),
        },
        "by_kind": [
            {
                "kind": str(r.kind),
                "e25": int(round(r.e25)),
                "e26": int(round(r.e26)),
                "de": int(round(r.de)),
                "q26": int(round(r.q26)),
                "n_pn": int(r.n_pn),
            }
            for r in by.itertuples()
        ],
        "delta_kind": [
            {"kind": str(r.kind), "de": int(round(r.de))} for r in by_de.itertuples()
        ],
        "top15": [
            {
                "pn": str(r["pn"]),
                "desc": str(r["desc"])[:50],
                "kind": str(r["kind"]),
                "model": str(r["model"]),
                "e25": int(round(r["H1'25 EUR"])),
                "e26": int(round(r["H1'26 EUR"])),
                "de": int(round(r["Delta EUR"])),
                "q26": int(round(r["H1'26 qty"])),
            }
            for _, r in top.iterrows()
        ],
        "by_model_known": [
            {
                "model": str(r.model),
                "e25": int(round(r.e25)),
                "e26": int(round(r.e26)),
                "de": int(round(r.de)),
                "n_pn": int(r.n_pn),
            }
            for r in known.itertuples()
        ],
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(json.dumps(out["kpi"], indent=2))
    print("kinds", len(out["by_kind"]), "mapped", out["kpi"]["n_mapped_pn"])


if __name__ == "__main__":
    main()
