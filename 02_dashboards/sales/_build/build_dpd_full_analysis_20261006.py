# -*- coding: utf-8 -*-
"""DPD ASM only — billed rank, emission from Europe editions + billed DB, clickable drill, observed interval."""
from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
OUT_DIR = ROOT / "02_dashboards" / "sales"
OUT_HTML = OUT_DIR / "ISZE_DPD_Full_Analysis_20261006.html"
OUT_CMD = OUT_DIR / "OPEN_ISZE_DPD_Full_Analysis.cmd"
OUT_JSON = OUT_DIR / "_build" / "dpd_full_analysis_20261006_payload.json"

EURO_RE = re.compile(
    r"(EURO\s*6D|EURO6D|EURO\s*VI|EURO\s*6|EURO6|EU6|EURO\s*5B?\+?|EURO5B?\+?|EU5B?\+?|EURO\s*5|EURO5|EU5|EURO\s*4|EURO4|EU4)",
    re.I,
)
YEAR_RE = re.compile(r"\b(20\d{2})\b")

# Network DBs whose billed D-Max / Europe trucks are EU/UK/Israel homologation, not EXP.
EUROPE_LIKE_DB = {
    "IUK", "ITUK", "IRELAND", "BELGIUM", "GERMANY", "PORTUGAL", "GREECE",
    "DENMARK", "SWEDEN", "NORWAY", "FINLAND", "ICELAND", "HUNGARY", "ROMANIA",
    "CYPRUS", "MALTA", "UMI", "UTI",
}
EXP_LIKE_DB = {"UKRAINE", "ARMENIA", "KAZAKHSTAN", "PALESTINE"}

# IUK N35 Grafter measured km/yr (odometer deltas), not the broken Annual Mileage column.
KM_YR_KNOWN = {"IUK": 14494}


def norm_pn(x) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    s = str(x).strip()
    s = re.sub(r"\.0$", "", s)
    if s.lower() in ("nan", "none", ""):
        return ""
    return s


def fy_label(dt: pd.Timestamp) -> str:
    y = int(dt.year)
    if int(dt.month) >= 4:
        return f"FY{y + 1}"
    return f"FY{y}"


def token_euro(text: str) -> str | None:
    hits = EURO_RE.findall(text or "")
    if not hits:
        return None
    found: set[str] = set()
    for hit in hits:
        h = re.sub(r"\s+", "", hit.upper())
        if "6D" in h:
            found.add("Euro 6d")
        elif "6" in h or "VI" in h:
            found.add("Euro 6")
        elif "5B" in h:
            found.add("Euro 5b+")
        elif "5" in h:
            found.add("Euro 5")
        elif "4" in h:
            found.add("Euro 4")
    if "Euro 6d" in found:
        return "Euro 6d"
    if "Euro 6" in found:
        return "Euro 6"
    if "Euro 5b+" in found:
        return "Euro 5b+"
    if "Euro 5" in found:
        return "Euro 5"
    if "Euro 4" in found:
        return "Euro 4"
    return None


def edition_lane(m: str) -> str:
    u = (m or "").upper()
    if "EUROPE" in u or "ISRAEL" in u:
        return "EUROPE"
    if re.search(r"\bEXP\b", u) or " EXPORT" in u:
        return "EXP"
    return "OTHER"


def dmax_europe_euro(year: int) -> str:
    """EU/UK/Israel D-Max homologation by model year. Not read from the EPC token."""
    if year <= 2015:
        return "Euro 5"
    if year <= 2020:
        return "Euro 6"
    return "Euro 6d"


def nseries_europe_euro(year: int) -> str | None:
    if year >= 2014:
        return "Euro 6"
    if year >= 2009:
        return "Euro 5"
    return None


def family_to_segment(families: list[str]) -> str:
    fams = set(families or [])
    light = any("PASSENGER" in f or "PICK UP" in f or "SUV" in f for f in fams)
    truck = any(f.startswith("TRUCKS") for f in fams)
    bus = any(f.startswith("BUSES") for f in fams)
    if light and not truck:
        return "LCV"
    if truck and not light:
        return "CV"
    if light and truck:
        return "Shared LCV+CV"
    if bus:
        return "Bus"
    if fams:
        return "Other"
    return "UNKNOWN"


def series_from_models(models: list[str]) -> list[str]:
    codes: set[str] = set()
    for m in models or []:
        for tok in re.findall(r"\b([A-Z]{2,4})\b", (m or "").upper()):
            if tok in {
                "TFR", "TFS", "NLR", "NMR", "NNR", "NPR", "NQR", "NPS", "NQS",
                "NMS", "NJR", "NKR", "NHR", "NHS", "NRR", "FRR", "FSR", "FTR",
                "FVR", "FXZ", "GVR",
            }:
                codes.add(tok)
        for hit in re.findall(r"\b(NLR|NMR|NNR|NPR|NQR|NPS|NMS85|TFR|TFS)\b", m or "", re.I):
            codes.add(hit.upper())
    return sorted(codes)


def parse_years(models: list[str]) -> tuple[str | None, str | None]:
    years: list[int] = []
    for m in models or []:
        for y in YEAR_RE.findall(m or ""):
            years.append(int(y))
    if not years:
        return None, None
    return str(min(years)), str(max(years))


def load_epc() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for name in ("epc_decode_batch1_20260919.json", "epc_decode_batch2_20260919.json"):
        p = DER / name
        if not p.exists():
            continue
        data = json.loads(p.read_text(encoding="utf-8"))
        rows = data if isinstance(data, list) else list(data.values())
        for r in rows:
            if not isinstance(r, dict):
                continue
            pn = norm_pn(r.get("pn") or r.get("part_number"))
            if not pn:
                continue
            out.setdefault(pn, r)
    return out


def _s(v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    s = str(v).strip()
    return "" if s.lower() in ("nan", "none") else s


def load_bands() -> dict[str, dict]:
    p = DER / "vehicle_band_applicability.csv"
    df = pd.read_csv(p, dtype=str)
    out = {}
    for _, r in df.iterrows():
        pn = norm_pn(r.get("pn"))
        if not pn:
            continue
        out[pn] = {
            "vehicle_bands": _s(r.get("vehicle_bands")),
            "exclusive_band": _s(r.get("exclusive_band")),
            "band_status": _s(r.get("band_status")),
            "band_labels": _s(r.get("band_labels")),
            "codes_named": _s(r.get("codes_named")),
        }
    return out


def band_label(b: dict | None, segment: str) -> tuple[str, str]:
    if not b:
        if segment == "LCV":
            return "LCV / D-Max (no band row)", "unknown"
        return "UNKNOWN", "unknown"
    status = b.get("band_status") or ""
    exclusive = b.get("exclusive_band") or ""
    bands = b.get("vehicle_bands") or ""
    labels = b.get("band_labels") or ""
    if exclusive:
        pretty = {
            "LCV_D-Max": "LCV / D-Max",
            "3.5t_N35": "3.5 t (N35)",
            "5.5t_N50_N55": "5.5 t (N55)",
            "7.5t_N50_N62_N75": "7.5 t (N75 class)",
            "F_series_MD_heavy": "F-series / heavy",
        }.get(exclusive, exclusive)
        return pretty, "single_band"
    if bands and "|" in bands:
        return (labels or bands.replace("|", " + ")), "shared_across_bands"
    if bands:
        return (labels or bands), status or "single_band"
    return "UNKNOWN", status or "unknown"


def is_asm_desc(desc: str) -> bool:
    u = (desc or "").upper()
    return bool(re.search(r"\bDPD\s*ASM\b|\bDPF\s*ASM\b|DPD\s*FILT\.?\s*ASM", u))


def emit_from_editions(models: list[str], series: list[str]) -> dict:
    """Split EPC editions EUROPE vs EXP and attach homologation where the token is missing."""
    europe: list[str] = []
    exp: list[str] = []
    other: list[str] = []
    token_hits: set[str] = set()
    eu_years: list[int] = []
    exp_years: list[int] = []
    for m in models or []:
        tok = token_euro(m)
        if tok:
            token_hits.add(tok)
        lane = edition_lane(m)
        ys = [int(y) for y in YEAR_RE.findall(m or "")]
        if lane == "EUROPE":
            europe.append(m)
            eu_years.extend(ys)
        elif lane == "EXP":
            exp.append(m)
            exp_years.extend(ys)
        else:
            other.append(m)
            if tok:
                europe.append(m)  # token present, keep as stated

    is_dmax = any(c in series for c in ("TFR", "TFS")) or any(
        "TFR" in (m or "").upper() or "TFS" in (m or "").upper() for m in models or []
    )
    is_n = any(c in series for c in ("NLR", "NMR", "NNR", "NPR", "NQR", "NPS", "NKR"))

    homolog: dict[str, list[int]] = defaultdict(list)
    for y in eu_years:
        if is_dmax:
            homolog[dmax_europe_euro(y)].append(y)
        elif is_n:
            e = nseries_europe_euro(y)
            if e:
                homolog[e].append(y)

    bits = []
    for e, ys in sorted(homolog.items(), key=lambda kv: min(kv[1])):
        bits.append(f"{e} ({min(ys)}–{max(ys)} Europe/Israel)")
    europe_label = " + ".join(bits) if bits else None
    token_label = " + ".join(sorted(token_hits)) if token_hits else None

    if europe_label:
        method = "Europe/Israel homologation by model year (EPC string has no EURO token on these D-Max editions)" if not token_label else "EPC token plus Europe/Israel year"
        label = europe_label
        if token_label and token_label not in label:
            label = f"{europe_label} · EPC token {token_label}"
    elif token_label:
        method = "EURO token in EPC model string"
        label = token_label
    elif exp and not europe:
        method = "EPC lists EXP only — no Europe edition, no EURO token"
        label = "EXP only — emission not stated"
    elif models:
        method = "EPC has editions but neither EURO token nor Europe/Israel year map"
        label = "Not stated"
    else:
        method = "No EPC decode"
        label = "UNKNOWN"

    return {
        "europe_editions_n": len(europe),
        "exp_editions_n": len(exp),
        "other_editions_n": len(other),
        "europe_editions": europe[:20],
        "exp_editions": exp[:12],
        "euro_token": token_label,
        "euro_europe_homologation": europe_label,
        "euro_norm_label": label,
        "euro_method": method,
        "europe_year_from": str(min(eu_years)) if eu_years else None,
        "europe_year_to": str(max(eu_years)) if eu_years else None,
        "exp_year_from": str(min(exp_years)) if exp_years else None,
        "exp_year_to": str(max(exp_years)) if exp_years else None,
        "is_dmax": is_dmax,
    }


def billed_emission(pn_attr: dict, by_db: pd.DataFrame) -> dict:
    """Where we billed it decides the live emission mix: Europe-like DB vs CIS/EXP."""
    eu_eur = exp_eur = other_eur = 0.0
    eu_qty = exp_qty = 0.0
    for db, r in by_db.iterrows():
        e = float(r.eur)
        q = float(r.qty)
        if db in EUROPE_LIKE_DB:
            eu_eur += e
            eu_qty += q
        elif db in EXP_LIKE_DB:
            exp_eur += e
            exp_qty += q
        else:
            other_eur += e
    total = eu_eur + exp_eur + other_eur
    share_eu = eu_eur / total if total else 0.0
    base = pn_attr.get("euro_europe_homologation") or pn_attr.get("euro_token")
    # EPC may list EXP only while we billed the PN into EU/UK/Israel D-Max books.
    if share_eu >= 0.8 and not base and pn_attr.get("is_dmax") and pn_attr.get("exp_year_from"):
        y0 = int(pn_attr["exp_year_from"])
        y1 = int(pn_attr.get("exp_year_to") or y0)
        labs = sorted({dmax_europe_euro(y) for y in (y0, y1)})
        base = " + ".join(f"{lab} ({y0}–{y1} billed in EU/UK/Israel, EPC lists EXP only)" for lab in labs)
    if share_eu >= 0.8 and base:
        billed_label = base
        billed_note = (
            f"{share_eu*100:.0f}% of this PN’s billed euros went to EU/UK/Israel distributors, "
            "so the live mix follows Europe/Israel homologation, not the EXP line in EPC."
        )
    elif share_eu >= 0.8 and not base:
        billed_label = pn_attr.get("euro_norm_label") or "Not stated"
        billed_note = "Billed to Europe-like DBs, but year/homologation could not be set (no EPC decode)."
    elif exp_eur > eu_eur:
        billed_label = "EXP / CIS billed — emission not stated"
        billed_note = "Most billed euros went to CIS / EXP-like distributors."
    else:
        billed_label = pn_attr.get("euro_norm_label") or "Mix"
        billed_note = (
            f"Split: EU/UK/Israel {eu_eur:,.0f} € · CIS/EXP {exp_eur:,.0f} € · other {other_eur:,.0f} €."
        )
    return {
        "billed_europe_like_eur": round(eu_eur, 2),
        "billed_exp_like_eur": round(exp_eur, 2),
        "billed_other_eur": round(other_eur, 2),
        "billed_europe_like_share": round(share_eu, 4),
        "billed_emission_label": billed_label,
        "billed_emission_note": billed_note,
    }


def load_uio_2024() -> dict[str, dict]:
    u = pd.read_csv(DER / "uio_by_market_type_year.csv")
    u = u[(u["year"] == 2024) & (u["is_actual"] == True)]
    out: dict[str, dict] = {}
    for code, g in u.groupby("distributor_code"):
        lcv = float(g.loc[g["vehicle_class"] == "LCV", "uio_units"].sum())
        cv = float(g.loc[g["vehicle_class"] == "CV", "uio_units"].sum())
        out[str(code)] = {"uio_lcv": lcv, "uio_cv": cv, "uio_total": lcv + cv}
    return out


def main() -> None:
    print("loading sales…")
    sf = pd.read_parquet(DER / "sales_fact.parquet")
    sf["billing_date"] = pd.to_datetime(sf["billing_date"])
    sf["part_number"] = sf["part_number"].map(norm_pn)
    sf["sold_to_sap"] = pd.to_numeric(sf["sold_to_sap"], errors="coerce")
    max_dt = sf["billing_date"].max()
    window_start = pd.Timestamp(year=(max_dt - pd.DateOffset(months=24)).year, month=(max_dt - pd.DateOffset(months=24)).month, day=1)
    d = sf[sf["billing_date"] >= window_start].copy()
    window_years = max((max_dt - window_start).days / 365.25, 1 / 12)

    asm = d[d["description"].map(is_asm_desc)].copy()
    print("DPD ASM lines", len(asm), "eur", float(asm["net_sales_value"].sum()))

    dim = pd.read_csv(DER / "distributor_dimension.csv")
    dim["sold_to_sap"] = pd.to_numeric(dim["sold_to_sap"], errors="coerce")
    network = dim[
        (dim["network_role"] == "network_db")
        & dim["distributor_code"].notna()
        & (dim["distributor_code"].astype(str).str.len() > 0)
    ].copy()
    sap_to_db = {}
    for _, r in dim.iterrows():
        code = str(r.get("distributor_code") or "").strip()
        if not code:
            continue
        sap = r["sold_to_sap"]
        if pd.isna(sap):
            continue
        sap_to_db[int(sap)] = {
            "distributor_code": code,
            "gps_db_label": str(r.get("gps_db_label") or code),
            "scope": str(r.get("scope") or ""),
            "region": str(r.get("region") or ""),
        }

    def map_db(sap):
        if pd.isna(sap):
            return None
        return sap_to_db.get(int(sap))

    mapped = asm["sold_to_sap"].map(map_db)
    asm["distributor_code"] = mapped.map(lambda x: x["distributor_code"] if x else "UNMAPPED")
    asm["distributor_code"] = asm["distributor_code"].fillna("UNMAPPED").replace({"nan": "UNMAPPED", "None": "UNMAPPED"})
    asm["db_label"] = mapped.map(lambda x: x["gps_db_label"] if x else "Unmapped")
    asm["db_scope"] = mapped.map(lambda x: x["scope"] if x else "")

    print("loading EPC + bands + UIO…")
    epc = load_epc()
    bands = load_bands()
    uio = load_uio_2024()

    sup_path = DER / "pn_supersession_map.csv"
    supersedes: dict[str, str] = {}
    superseded_by: dict[str, str] = {}
    if sup_path.exists():
        s = pd.read_csv(sup_path, dtype=str)
        cols = {c.lower(): c for c in s.columns}
        a = cols.get("from_pn") or cols.get("old_pn") or cols.get("pn_from") or list(s.columns)[0]
        b = cols.get("to_pn") or cols.get("new_pn") or cols.get("pn_to") or list(s.columns)[1]
        for _, r in s.iterrows():
            old, new = norm_pn(r.get(a)), norm_pn(r.get(b))
            if old and new:
                supersedes[old] = new
                superseded_by[new] = old

    def attrs_for(pn: str) -> dict:
        r = epc.get(pn) or {}
        models = r.get("models") or []
        families = r.get("families") or []
        segment = family_to_segment(families)
        b = bands.get(pn)
        tonnage, band_status = band_label(b, segment)
        y0, y1 = parse_years(models)
        series = series_from_models(models)
        if b and b.get("codes_named"):
            extra = [c.strip() for c in b["codes_named"].split(";") if c.strip() and c.strip() != "NAN"]
            series = sorted(set(series) | set(extra))
        emit = emit_from_editions(models, series)
        return {
            "in_epc": bool(r.get("found") or models or families),
            "families": families,
            "models": models[:24],
            "models_n": len(models),
            "segment": segment,
            "tonnage": tonnage,
            "band_status": band_status,
            "year_from": y0,
            "year_to": y1,
            "series": series,
            "supersedes": supersedes.get(pn),
            "superseded_by": superseded_by.get(pn),
            **emit,
        }

    asm_rows = []
    for pn, g in asm.groupby("part_number"):
        atr = attrs_for(pn)
        desc = g["description"].mode().iloc[0] if len(g) else "DPD ASM"
        eur = float(g["net_sales_value"].sum())
        qty = float(g["billed_qty"].sum())
        first = g["billing_date"].min()
        last = g["billing_date"].max()
        span_days = int((last - first).days) + 1 if pd.notna(first) else 0
        years = max(span_days / 365.25, 1 / 12)
        by_db_df = (
            g.groupby("distributor_code")
            .agg(eur=("net_sales_value", "sum"), qty=("billed_qty", "sum"))
            .sort_values("eur", ascending=False)
        )
        top_dbs = [
            {"db": i, "eur": round(float(r.eur), 2), "qty": round(float(r.qty), 2)}
            for i, r in by_db_df.iterrows()
        ]
        billed = billed_emission(atr, by_db_df)
        fy = {}
        g2 = g.copy()
        g2["fy"] = g2["billing_date"].map(fy_label)
        for fy_name, gg in g2.groupby("fy"):
            fy[fy_name] = {
                "eur": round(float(gg["net_sales_value"].sum()), 2),
                "qty": round(float(gg["billed_qty"].sum()), 2),
            }
        asm_rows.append(
            {
                "pn": pn,
                "description": str(desc),
                "eur": round(eur, 2),
                "qty": round(qty, 2),
                "n_lines": int(len(g)),
                "n_dbs": int(g["distributor_code"].nunique()),
                "first_sale": first.strftime("%Y-%m-%d") if pd.notna(first) else None,
                "last_sale": last.strftime("%Y-%m-%d") if pd.notna(last) else None,
                "span_days": span_days,
                "pcs_per_year": round(qty / years, 2),
                "top_dbs": top_dbs,
                "by_fy": fy,
                **atr,
                **billed,
            }
        )
    asm_rows.sort(key=lambda x: -x["eur"])

    code_meta = {}
    for _, r in network.iterrows():
        c = str(r["distributor_code"]).strip()
        if c and c not in code_meta:
            code_meta[c] = {
                "label": str(r.get("gps_db_label") or c),
                "scope": str(r.get("scope") or ""),
                "region": str(r.get("region") or ""),
            }

    top_asm_pns = [r["pn"] for r in asm_rows[:8]]
    pn_index = {r["pn"]: r for r in asm_rows}

    db_matrix = []
    for code in code_meta:
        g = asm[asm["distributor_code"] == code]
        eur = float(g["net_sales_value"].sum()) if len(g) else 0.0
        qty = float(g["billed_qty"].sum()) if len(g) else 0.0
        by_pn = {}
        lcv_eur = cv_eur = unk_eur = 0.0
        lcv_qty = cv_qty = 0.0
        if len(g):
            for pn, gg in g.groupby("part_number"):
                pe = float(gg["net_sales_value"].sum())
                pq = float(gg["billed_qty"].sum())
                by_pn[pn] = {"eur": round(pe, 2), "qty": round(pq, 2)}
                seg = pn_index.get(pn, {}).get("segment") or attrs_for(pn)["segment"]
                if seg == "LCV":
                    lcv_eur += pe
                    lcv_qty += pq
                elif seg == "CV":
                    cv_eur += pe
                    cv_qty += pq
                else:
                    unk_eur += pe
        u = uio.get(code) or {"uio_lcv": None, "uio_cv": None, "uio_total": None}
        # Denominator: UIO of the segment we actually billed DPD into. Mixed books use both.
        denom = 0.0
        denom_note = ""
        if lcv_qty and not cv_qty:
            denom = float(u["uio_lcv"] or 0)
            denom_note = "LCV trucks in service 2024"
        elif cv_qty and not lcv_qty:
            denom = float(u["uio_cv"] or 0)
            denom_note = "CV trucks in service 2024"
        else:
            denom = float(u["uio_total"] or 0)
            denom_note = "LCV+CV trucks in service 2024"
        rate = (qty / window_years / denom) if denom and qty else None
        interval_yr = (1 / rate) if rate and rate > 0 else None
        km_yr = KM_YR_KNOWN.get(code)
        interval_km = round(interval_yr * km_yr) if interval_yr and km_yr else None
        pcs_per_1000 = round(rate * 1000, 2) if rate else None
        if qty <= 0:
            interval_txt = "No DPD ASM billed in the window"
        elif not denom:
            interval_txt = "UIO missing — cannot set an interval"
        else:
            interval_txt = (
                f"{pcs_per_1000} billed DPD ASM per 1,000 vehicles per year"
                f" · implied {interval_yr:.0f} years if every truck used one"
            )
        db_matrix.append(
            {
                "distributor_code": code,
                "label": code_meta[code]["label"],
                "scope": code_meta[code]["scope"],
                "region": code_meta[code]["region"],
                "asm_eur": round(eur, 2),
                "asm_qty": round(qty, 2),
                "lcv_eur": round(lcv_eur, 2),
                "cv_eur": round(cv_eur, 2),
                "unknown_eur": round(unk_eur, 2),
                "lcv_qty": round(lcv_qty, 2),
                "cv_qty": round(cv_qty, 2),
                "uio_lcv": u["uio_lcv"],
                "uio_cv": u["uio_cv"],
                "uio_used": denom or None,
                "uio_note": denom_note,
                "pcs_per_uio_per_year": round(rate, 4) if rate else None,
                "pcs_per_1000_uio_per_year": pcs_per_1000,
                "observed_interval_years": round(interval_yr, 1) if interval_yr else None,
                "observed_interval_km": interval_km,
                "interval_txt": interval_txt,
                "by_pn": {pn: by_pn.get(pn, {"eur": 0, "qty": 0}) for pn in top_asm_pns},
                "by_pn_all": by_pn,
                "has_sales": eur > 0,
            }
        )
    db_matrix.sort(key=lambda x: (-x["asm_eur"], x["label"]))

    def cut_sum(key_fn):
        buckets: dict[str, dict] = defaultdict(lambda: {"eur": 0.0, "qty": 0.0, "n_pn": set()})
        for r in asm_rows:
            k = key_fn(r)
            buckets[k]["eur"] += r["eur"]
            buckets[k]["qty"] += r["qty"]
            buckets[k]["n_pn"].add(r["pn"])
        out = []
        for k, v in buckets.items():
            out.append({"key": k, "eur": round(v["eur"], 2), "qty": round(v["qty"], 2), "n_pn": len(v["n_pn"])})
        out.sort(key=lambda x: -x["eur"])
        return out

    cut_segment = cut_sum(lambda r: r["segment"])
    cut_tonnage = cut_sum(
        lambda r: r["tonnage"] if r["band_status"] != "shared_across_bands" else f"Shared: {r['tonnage']}"
    )
    cut_euro = cut_sum(lambda r: r["billed_emission_label"])

    print("loading warranty…")
    wart = DER / "warranty_commercial"
    def_pn_set = {r["pn"] for r in asm_rows}

    def load_wart_ops(path: Path, bag: str):
        if not path.exists():
            return []
        df = pd.read_csv(path)
        hit = df[df["operation"].fillna("").str.contains(r"PARTICULATE|DEFUSER|\bDPD\b|\bDPF\b", case=False, regex=True)]
        hit = hit[~hit["operation"].fillna("").str.contains(r"SENSOR|GASKET|HOSE", case=False, regex=True)]
        rows = []
        for _, r in hit.iterrows():
            rows.append(
                {
                    "bag": bag,
                    "operation": str(r.get("operation") or ""),
                    "claim_lines": int(float(r.get("claim_lines") or 0)),
                    "parts_turnover_eur": round(float(r.get("parts_turnover_eur") or 0), 2),
                    "median_odometer_km": float(r["median_odometer_km"]) if pd.notna(r.get("median_odometer_km")) else None,
                    "median_age_years": float(r["median_age_years"]) if pd.notna(r.get("median_age_years")) else None,
                    "markets_present": int(float(r.get("markets_present") or 0)),
                    "outside_limits_eur": round(float(r["outside_limits_eur"]), 2)
                    if "outside_limits_eur" in r and pd.notna(r.get("outside_limits_eur"))
                    else None,
                    "outside_limits_share": float(r["outside_limits_share"])
                    if "outside_limits_share" in r and pd.notna(r.get("outside_limits_share"))
                    else None,
                }
            )
        rows.sort(key=lambda x: -x["parts_turnover_eur"])
        return rows

    wart_ops_lcv = load_wart_ops(wart / "warranty_top_repair_lines.csv", "LCV")
    wart_ops_cv = load_wart_ops(wart / "warranty_cv_top_repair_lines.csv", "CV")

    def load_wart_pns(path: Path, bag: str):
        if not path.exists():
            return []
        df = pd.read_csv(path, dtype={"part_number": str})
        df["part_number"] = df["part_number"].map(norm_pn)
        hit = df[df["part_number"].isin(def_pn_set)].copy()
        hit["parts_turnover_eur"] = pd.to_numeric(hit["parts_turnover_eur"], errors="coerce")
        rows = []
        for _, r in hit.sort_values("parts_turnover_eur", ascending=False).iterrows():
            pn = norm_pn(r["part_number"])
            atr = pn_index.get(pn) or {}
            rows.append(
                {
                    "bag": bag,
                    "pn": pn,
                    "claim_lines": int(float(r.get("claim_lines") or 0)),
                    "parts_turnover_eur": round(float(r.get("parts_turnover_eur") or 0), 2),
                    "markets_present": int(float(r.get("markets_present") or 0)),
                    "median_odometer_km": float(r["median_odometer_km"]) if pd.notna(r.get("median_odometer_km")) else None,
                    "median_age_years": float(r["median_age_years"]) if "median_age_years" in r and pd.notna(r.get("median_age_years")) else None,
                    "family": str(r.get("family") or ""),
                    "in_billed_asm": True,
                    "segment": atr.get("segment"),
                    "tonnage": atr.get("tonnage"),
                }
            )
        return rows

    wart_pn_lcv = load_wart_pns(wart / "warranty_part_turnover.csv", "LCV")
    wart_pn_cv = load_wart_pns(wart / "warranty_cv_part_turnover.csv", "CV")

    cv_markets = []
    cmp = wart / "warranty_cv_by_market.csv"
    if cmp.exists():
        mdf = pd.read_csv(cmp)
        for _, r in mdf.iterrows():
            cv_markets.append(
                {
                    "market": str(r["market"]),
                    "claim_lines": int(r["claim_lines"]),
                    "parts_turnover_eur": round(float(r["parts_turnover_eur"]), 2),
                    "part_number_coverage": float(r["part_number_coverage"]) if pd.notna(r.get("part_number_coverage")) else None,
                    "median_odometer_km": float(r["median_odometer_km"]) if pd.notna(r.get("median_odometer_km")) else None,
                }
            )

    opp = pd.read_csv(DER / "pms_opportunity_matrix.csv")
    pms_cats = sorted(opp["pms_category"].dropna().unique().tolist())
    dpd_in_pms = any(re.search(r"dpd|dpf|particulate|aftertreat", c, re.I) for c in pms_cats)
    capture = {
        "dpd_in_pms_categories": bool(dpd_in_pms),
        "pms_categories": pms_cats,
        "verdict": (
            "There is no IML service interval for DPD assemblies, and they are not in the PMS capture list. "
            "The per-distributor year figure on this page is observed billed pieces versus trucks in service — "
            "not a scheduled interval and not a capture %."
        ),
        "source": "pms_opportunity_matrix.csv + billed DPD ASM ÷ 2024 UIO",
    }

    asm_eur = sum(r["eur"] for r in asm_rows)
    asm_qty = sum(r["qty"] for r in asm_rows)
    lcv_eur = sum(r["eur"] for r in asm_rows if r["segment"] == "LCV")
    cv_eur = sum(r["eur"] for r in asm_rows if r["segment"] == "CV")
    shared_eur = sum(r["eur"] for r in asm_rows if r["band_status"] == "shared_across_bands")
    dbs_with = sum(1 for r in db_matrix if r["has_sales"])
    wart_cv_ops_eur = sum(r["parts_turnover_eur"] for r in wart_ops_cv)
    wart_lcv_ops_eur = sum(r["parts_turnover_eur"] for r in wart_ops_lcv)

    payload = {
        "meta": {
            "title": "DPD assemblies — billed rank, emission, interval",
            "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "window_start": window_start.strftime("%Y-%m-%d"),
            "window_end": max_dt.strftime("%Y-%m-%d"),
            "window_years": round(window_years, 3),
            "window_note": "Rolling ~24 months from latest billing date. DPD ASM / DPF ASM only.",
            "audience": "internal",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "uti_umi": "UTI 1799 and UMI 1797 stay separate",
            "emission_rule": (
                "D-Max Europe/Israel: model year ≤2015 Euro 5, 2016–2020 Euro 6, 2021+ Euro 6d. "
                "N-series Europe 2014+ treated as Euro 6 when the EPC string has no token. "
                "Billed mix uses who bought the PN: EU/UK/Israel vs CIS."
            ),
            "interval_rule": (
                "Observed rate = DPD ASM pcs in the window ÷ years ÷ trucks in service 2024 of the billed segment, "
                "shown per 1,000 vehicles. Destock and old fleet move this number — it is not an IML service interval."
            ),
        },
        "hero": {
            "asm_eur": round(asm_eur, 2),
            "asm_qty": round(asm_qty, 2),
            "asm_pns": len(asm_rows),
            "lcv_eur": round(lcv_eur, 2),
            "cv_eur": round(cv_eur, 2),
            "shared_band_eur": round(shared_eur, 2),
            "dbs_with_asm": dbs_with,
            "dbs_total_network": len(db_matrix),
            "warranty_cv_ops_eur": round(wart_cv_ops_eur, 2),
            "warranty_lcv_ops_eur": round(wart_lcv_ops_eur, 2),
            "capture_one_liner": capture["verdict"],
        },
        "assemblies": asm_rows,
        "cuts": {"segment": cut_segment, "tonnage": cut_tonnage, "euro_norm": cut_euro},
        "db_matrix": db_matrix,
        "top_asm_pns": top_asm_pns,
        "warranty": {
            "ops_lcv": wart_ops_lcv,
            "ops_cv": wart_ops_cv,
            "pn_lcv": wart_pn_lcv[:40],
            "pn_cv": wart_pn_cv[:40],
            "cv_markets": cv_markets,
            "notes": [
                "Claims book only — not a fleet failure rate.",
                "PN coverage is thin in several CV markets.",
            ],
        },
        "capture": capture,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT_JSON, "asm_eur", asm_eur)
    print("euro cut", cut_euro[:6])

    html = render_html(payload)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CMD.write_text(
        '@echo off\r\nstart "" "%~dp0ISZE_DPD_Full_Analysis_20261006.html"\r\n',
        encoding="utf-8",
        newline="",
    )
    print("wrote", OUT_HTML, "bytes", OUT_HTML.stat().st_size)
    print("wrote", OUT_CMD)


def feur(v, d=0):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "—"
    if d == 0:
        return f"€{x:,.0f}"
    return f"€{x:,.{d}f}"


def fnum(v, d=0):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "—"
    if d == 0:
        return f"{x:,.0f}"
    return f"{x:,.{d}f}"


def esc(s):
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def bar_rows(items, max_eur=None, label_key="key", eur_key="eur"):
    if not items:
        return "<p class='muted'>No rows.</p>"
    mx = max_eur or max(float(i[eur_key]) for i in items) or 1
    bits = []
    for i in items:
        w = 100 * float(i[eur_key]) / mx if mx else 0
        bits.append(
            f"<div class='bar-row'><div class='bar-lab'>{esc(i[label_key])}"
            f"<div class='sub'>{fnum(i.get('qty', 0))} pcs · {i.get('n_pn', '—')} PN</div></div>"
            f"<div class='bar-track'><div class='bar-fill' style='width:{w:.1f}%'></div></div>"
            f"<div class='bar-val'>{feur(i[eur_key])}</div></div>"
        )
    return "\n".join(bits)


def render_html(p: dict) -> str:
    h = p["hero"]
    m = p["meta"]
    top = p["assemblies"][:12]
    mx = top[0]["eur"] if top else 1
    top_bars = [
        {"key": f"{r['pn']} · {r['segment']}", "eur": r["eur"], "qty": r["qty"], "n_pn": 1}
        for r in top
    ]
    top_bars_html = bar_rows(top_bars, mx)

    asm_table_rows = []
    for r in p["assemblies"]:
        shared = " shared" if r["band_status"] == "shared_across_bands" else ""
        series = ", ".join(r.get("series") or []) or "—"
        years = "–".join(x for x in [r.get("year_from"), r.get("year_to")] if x) or "—"
        asm_table_rows.append(
            f"<tr class='clickrow{shared}' data-kind='pn' data-id='{esc(r['pn'])}' tabindex='0'>"
            f"<td class='mono'>{esc(r['pn'])}</td>"
            f"<td>{esc(r['description'])}</td>"
            f"<td class='num'>{feur(r['eur'])}</td>"
            f"<td class='num'>{fnum(r['qty'])}</td>"
            f"<td>{esc(r['segment'])}</td>"
            f"<td>{esc(r['tonnage'])}</td>"
            f"<td>{esc(r['billed_emission_label'])}<div class='sub'>{esc(r.get('euro_method') or '')}</div></td>"
            f"<td>{esc(series)}</td>"
            f"<td>{esc(years)}</td>"
            f"<td class='num'>{fnum(r['pcs_per_year'],1)}/yr</td>"
            f"</tr>"
        )

    pn_heads = "".join(f"<th class='mono small'>{esc(pn)}</th>" for pn in p["top_asm_pns"])
    db_rows = []
    for r in p["db_matrix"]:
        cells = "".join(
            f"<td class='num'>{feur(r['by_pn'][pn]['eur']) if r['by_pn'][pn]['eur'] else '—'}</td>"
            for pn in p["top_asm_pns"]
        )
        zero = " zero" if not r["has_sales"] else ""
        iv = r.get("pcs_per_1000_uio_per_year")
        ivs = f"{iv} / 1,000 / yr" if iv is not None else "—"
        db_rows.append(
            f"<tr class='clickrow{zero}' data-kind='db' data-id='{esc(r['distributor_code'])}' tabindex='0'>"
            f"<td><strong>{esc(r['label'])}</strong><div class='sub'>{esc(r['distributor_code'])} · {esc(r['scope'])}</div></td>"
            f"<td class='num'>{feur(r['asm_eur'])}</td>"
            f"<td class='num'>{fnum(r['asm_qty'])}</td>"
            f"<td class='num'>{feur(r['lcv_eur'])}</td>"
            f"<td class='num'>{feur(r['cv_eur'])}</td>"
            f"<td>{esc(ivs)}<div class='sub'>{esc(r.get('interval_txt') or '')}</div></td>"
            f"{cells}</tr>"
        )

    def ops_table(rows):
        if not rows:
            return "<p class='muted'>No matching operations.</p>"
        body = []
        for r in rows:
            lim = ""
            if r.get("outside_limits_share") is not None:
                lim = f"<div class='sub'>Outside stated limits: {r['outside_limits_share']*100:.0f}% ({feur(r.get('outside_limits_eur'))})</div>"
            body.append(
                f"<tr><td>{esc(r['operation'])}{lim}</td>"
                f"<td class='num'>{r['claim_lines']}</td>"
                f"<td class='num'>{feur(r['parts_turnover_eur'])}</td>"
                f"<td class='num'>{fnum(r['median_odometer_km']) if r.get('median_odometer_km') is not None else '—'} km</td>"
                f"<td class='num'>{fnum(r['median_age_years'],1) if r.get('median_age_years') is not None else '—'} yr</td>"
                f"<td class='num'>{r['markets_present']}</td></tr>"
            )
        return (
            "<table><thead><tr><th>Operation</th><th>Lines</th><th>Parts €</th>"
            "<th>Median km</th><th>Median age</th><th>Markets</th></tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table>"
        )

    def wart_pn_table(rows):
        if not rows:
            return "<p class='muted'>No billed DPD ASM PNs in this warranty extract.</p>"
        body = []
        for r in rows[:25]:
            body.append(
                f"<tr class='clickrow' data-kind='pn' data-id='{esc(r['pn'])}' tabindex='0'>"
                f"<td class='mono'>{esc(r['pn'])}</td>"
                f"<td class='num'>{feur(r['parts_turnover_eur'])}</td>"
                f"<td class='num'>{r['claim_lines']}</td>"
                f"<td class='num'>{fnum(r['median_odometer_km']) if r.get('median_odometer_km') is not None else '—'} km</td>"
                f"<td>{esc(r.get('segment') or '—')}</td></tr>"
            )
        return (
            "<table><thead><tr><th>PN</th><th>Parts €</th><th>Lines</th><th>Median km</th>"
            "<th>LCV/CV</th></tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table>"
        )

    mkt_rows = "".join(
        f"<tr><td>{esc(r['market'])}</td><td class='num'>{feur(r['parts_turnover_eur'])}</td>"
        f"<td class='num'>{r['claim_lines']}</td>"
        f"<td class='num'>{(r['part_number_coverage'] or 0)*100:.0f}%</td></tr>"
        for r in p["warranty"]["cv_markets"][:20]
    )

    payload_json = json.dumps(p, ensure_ascii=False).replace("NaN", "null")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{esc(m['title'])}</title>
<style>
:root {{
  --navy:#15233c; --ink:#1a2332; --paper:#f7f4ee; --line:#d9d2c5;
  --terra:#c0552d; --ok:#2f6b4f; --amber:#b45309; --muted:#5c6570;
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; font-family: "Segoe UI", system-ui, sans-serif; color:var(--ink); background:var(--paper); }}
header {{ background:var(--navy); color:#f7f4ee; padding:24px 28px 20px; }}
header h1 {{ margin:0 0 8px; font-family: Georgia, "Times New Roman", serif; font-weight:600; font-size:26px; }}
header .meta {{ color:#c8d0dc; font-size:13px; line-height:1.45; max-width:980px; }}
.toolbar {{ display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:14px; }}
.toolbar input {{ padding:8px 10px; border:1px solid #3a4a63; background:#0f1a2c; color:#f7f4ee; min-width:220px; }}
.chip {{ border:1px solid #6a778a; background:transparent; color:#f7f4ee; padding:6px 10px; cursor:pointer; font-size:12px; }}
.chip.on {{ background:var(--terra); border-color:var(--terra); }}
main {{ padding:20px 28px 80px; max-width:1320px; margin:0 auto; }}
h2 {{ font-family: Georgia, serif; color:var(--navy); margin:32px 0 10px; font-size:22px; }}
h3 {{ color:var(--navy); margin:18px 0 8px; font-size:16px; }}
.kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin:12px 0; }}
.kpi {{ background:#fff; border:1px solid var(--line); border-left:4px solid var(--terra); padding:12px 14px; }}
.kpi .v {{ font-size:20px; font-weight:700; color:var(--navy); }}
.kpi .l {{ font-size:12px; color:var(--muted); margin-top:4px; }}
.callout {{ background:#fff; border:1px solid var(--line); border-left:4px solid var(--amber); padding:12px 14px; margin:12px 0; font-size:14px; line-height:1.45; }}
.callout.bad {{ border-left-color:var(--terra); }}
.bar-row {{ display:grid; grid-template-columns:240px 1fr 90px; gap:10px; align-items:center; margin:6px 0; }}
.bar-lab {{ font-size:13px; }}
.bar-lab .sub, .sub {{ font-size:11px; color:var(--muted); }}
.bar-track {{ background:#e8e2d6; height:14px; border-radius:2px; overflow:hidden; }}
.bar-fill {{ background:var(--terra); height:100%; }}
.bar-val {{ text-align:right; font-variant-numeric:tabular-nums; font-size:13px; font-weight:600; }}
table {{ width:100%; border-collapse:collapse; background:#fff; font-size:13px; }}
th, td {{ border-bottom:1px solid var(--line); padding:8px 10px; text-align:left; vertical-align:top; }}
th {{ background:var(--navy); color:#f7f4ee; font-weight:600; position:sticky; top:0; z-index:1; }}
td.num, th.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
tr.shared td {{ background:#fff8ef; }}
tr.zero td {{ color:#8a9098; }}
tr.clickrow {{ cursor:pointer; }}
tr.clickrow:hover td {{ background:#efe8dc; }}
tr.clickrow.active td {{ background:#e4d5c4; }}
.mono {{ font-family: ui-monospace, Consolas, monospace; font-size:12px; }}
.small {{ font-size:11px; }}
.muted {{ color:var(--muted); }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
@media (max-width:900px) {{ .grid2 {{ grid-template-columns:1fr; }} .bar-row {{ grid-template-columns:1fr; }} }}
.scroll {{ overflow:auto; max-height:560px; border:1px solid var(--line); }}
footer {{ margin-top:40px; font-size:12px; color:var(--muted); }}
.drawer {{ position:fixed; top:0; right:0; width:min(460px,100%); height:100%; background:#fff; border-left:4px solid var(--terra);
  box-shadow:-8px 0 24px rgba(21,35,60,.18); padding:18px 18px 40px; overflow:auto; z-index:20; display:none; }}
.drawer.open {{ display:block; }}
.drawer h2 {{ margin-top:8px; }}
.drawer .x {{ float:right; border:0; background:var(--navy); color:#f7f4ee; padding:6px 10px; cursor:pointer; }}
.ed {{ font-size:12px; margin:4px 0; padding-left:8px; border-left:3px solid var(--line); }}
</style>
</head>
<body>
<header>
  <h1>DPD assemblies — billed, emission, observed interval</h1>
  <div class="meta">
    {esc(m['window_start'])} → {esc(m['window_end'])}. DPD ASM / DPF ASM only — no sensors, gaskets, hoses, no FILTER ASM 150-558.
    Click a part number or a distributor. {esc(m['uti_umi'])}.
  </div>
  <div class="toolbar">
    <input id="q" type="search" placeholder="Search PN, distributor, Euro 6d…"/>
    <button class="chip on" data-f="all" type="button">All</button>
    <button class="chip" data-f="LCV" type="button">LCV / D-Max</button>
    <button class="chip" data-f="CV" type="button">CV truck</button>
    <button class="chip" data-f="e6d" type="button">Euro 6d</button>
    <button class="chip" data-f="e6" type="button">Euro 6</button>
    <button class="chip" data-f="e5" type="button">Euro 5</button>
  </div>
</header>
<main>
<section>
  <div class="kpis">
    <div class="kpi"><div class="v">{feur(h['asm_eur'])}</div><div class="l">DPD ASM billed · {fnum(h['asm_qty'])} pcs · {h['asm_pns']} PNs</div></div>
    <div class="kpi"><div class="v">{feur(h['lcv_eur'])}</div><div class="l">LCV / D-Max</div></div>
    <div class="kpi"><div class="v">{feur(h['cv_eur'])}</div><div class="l">CV truck</div></div>
    <div class="kpi"><div class="v">{h['dbs_with_asm']} / {h['dbs_total_network']}</div><div class="l">network DBs with DPD ASM</div></div>
    <div class="kpi"><div class="v">{feur(h['warranty_cv_ops_eur'])}</div><div class="l">CV warranty ops (particulate / DPD)</div></div>
    <div class="kpi"><div class="v">{feur(h['warranty_lcv_ops_eur'])}</div><div class="l">LCV warranty ops (particulate / DPD)</div></div>
  </div>
  <div class="callout bad">{esc(h['capture_one_liner'])}</div>
  <div class="callout">{esc(m['emission_rule'])}</div>
</section>

<section>
  <h2>1. Ranked DPD assemblies — click a row</h2>
  {top_bars_html}
  <div class="scroll" style="margin-top:16px">
  <table id="pn-table">
    <thead><tr>
      <th>PN</th><th>Desc</th><th class="num">€</th><th class="num">Pcs</th>
      <th>LCV/CV</th><th>Tonnage</th><th>Emission (billed mix)</th><th>Series</th><th>Years</th><th class="num">Pcs/yr</th>
    </tr></thead>
    <tbody>{''.join(asm_table_rows)}</tbody>
  </table>
  </div>
</section>

<section>
  <h2>2. Emission of the billed euros</h2>
  <p class="muted">This cut uses who we billed, plus Europe/Israel model year — not a blank “not in EPC string”.</p>
  {bar_rows(p['cuts']['euro_norm'], label_key='key')}
  <div class="grid2">
    <div>
      <h3>LCV vs CV</h3>
      {bar_rows(p['cuts']['segment'], label_key='key')}
    </div>
    <div>
      <h3>Tonnage</h3>
      {bar_rows(p['cuts']['tonnage'], label_key='key')}
    </div>
  </div>
</section>

<section>
  <h2>3. Every distributor — click for interval and mix</h2>
  <p class="muted">{esc(m['interval_rule'])}</p>
  <div class="scroll">
  <table id="db-table">
    <thead><tr>
      <th>Distributor</th><th class="num">ASM €</th><th class="num">Pcs</th>
      <th class="num">LCV €</th><th class="num">CV €</th><th>Observed interval</th>
      {pn_heads}
    </tr></thead>
    <tbody>{''.join(db_rows)}</tbody>
  </table>
  </div>
</section>

<section>
  <h2>4. Warranty — DPD / particulate operations only</h2>
  <h3>CV truck</h3>
  {ops_table(p['warranty']['ops_cv'])}
  <h3>LCV / D-Max</h3>
  {ops_table(p['warranty']['ops_lcv'])}
  <div class="grid2">
    <div><h3>CV — billed DPD ASM in claims</h3>{wart_pn_table(p['warranty']['pn_cv'])}</div>
    <div><h3>LCV — billed DPD ASM in claims</h3>{wart_pn_table(p['warranty']['pn_lcv'])}</div>
  </div>
  <h3>CV claim book — markets</h3>
  <div class="scroll"><table><thead><tr><th>Market</th><th class="num">Parts €</th><th class="num">Lines</th><th class="num">PN coverage</th></tr></thead>
  <tbody>{mkt_rows}</tbody></table></div>
</section>
<footer>Double-click OPEN_ISZE_DPD_Full_Analysis.cmd next to this file. Internal.</footer>
</main>
<aside class="drawer" id="drawer" hidden>
  <button class="x" type="button" id="dx">Close</button>
  <div id="dbody"></div>
</aside>
<script type="application/json" id="payload">{payload_json}</script>
<script>
(function(){{
  const P = JSON.parse(document.getElementById('payload').textContent);
  const byPn = Object.fromEntries(P.assemblies.map(r => [r.pn, r]));
  const byDb = Object.fromEntries(P.db_matrix.map(r => [r.distributor_code, r]));
  const drawer = document.getElementById('drawer');
  const dbody = document.getElementById('dbody');
  const eur = n => '€' + Math.round(n||0).toLocaleString('en-GB');
  function openDrawer(html){{
    dbody.innerHTML = html;
    drawer.hidden = false;
    drawer.classList.add('open');
  }}
  function closeDrawer(){{
    drawer.classList.remove('open');
    drawer.hidden = true;
    document.querySelectorAll('tr.active').forEach(t => t.classList.remove('active'));
  }}
  document.getElementById('dx').onclick = closeDrawer;
  document.addEventListener('keydown', e => {{ if(e.key==='Escape') closeDrawer(); }});

  function pnHtml(r){{
    const dbs = (r.top_dbs||[]).map(d => '<div>'+d.db+' · '+eur(d.eur)+' · '+(d.qty)+' pcs</div>').join('');
    const eu = (r.europe_editions||[]).map(m => '<div class="ed">'+m+'</div>').join('') || '<div class="muted">None</div>';
    const ex = (r.exp_editions||[]).map(m => '<div class="ed">'+m+'</div>').join('') || '<div class="muted">None</div>';
    return '<h2>'+r.pn+'</h2><p>'+r.description+'</p>'
      +'<p><strong>'+eur(r.eur)+'</strong> · '+r.qty+' pcs · '+r.segment+' · '+r.tonnage+'</p>'
      +'<p><strong>Billed emission:</strong> '+r.billed_emission_label+'</p>'
      +'<p class="muted">'+r.billed_emission_note+'</p>'
      +'<p class="muted">'+r.euro_method+'</p>'
      +'<h3>Who bought it</h3>'+dbs
      +'<h3>Europe / Israel editions</h3>'+eu
      +'<h3>EXP editions</h3>'+ex;
  }}
  function dbHtml(r){{
    const pns = Object.entries(r.by_pn_all||{{}}).sort((a,b)=>b[1].eur-a[1].eur)
      .map(([pn,v]) => '<div class="clickpn" data-id="'+pn+'" style="cursor:pointer;padding:4px 0">'+pn+' · '+eur(v.eur)+' · '+v.qty+' pcs</div>').join('')
      || '<p class="muted">No DPD ASM in the window.</p>';
    return '<h2>'+r.label+'</h2><p>'+r.distributor_code+' · '+r.scope+'</p>'
      +'<p><strong>'+eur(r.asm_eur)+'</strong> · '+r.asm_qty+' pcs</p>'
      +'<p><strong>Observed interval:</strong> '+(r.interval_txt||'—')+'</p>'
      +'<p class="muted">Trucks in service used: '+(r.uio_used||'—')+' ('+ (r.uio_note||'') +'). LCV UIO '+(r.uio_lcv||'—')+' · CV UIO '+(r.uio_cv||'—')+'.</p>'
      +'<h3>Parts billed here</h3>'+pns;
  }}

  document.body.addEventListener('click', e => {{
    const row = e.target.closest('tr.clickrow');
    const pnlink = e.target.closest('.clickpn');
    if(pnlink){{
      const r = byPn[pnlink.getAttribute('data-id')];
      if(r) openDrawer(pnHtml(r));
      return;
    }}
    if(!row) return;
    document.querySelectorAll('tr.active').forEach(t => t.classList.remove('active'));
    row.classList.add('active');
    const kind = row.getAttribute('data-kind');
    const id = row.getAttribute('data-id');
    if(kind==='pn' && byPn[id]) openDrawer(pnHtml(byPn[id]));
    if(kind==='db' && byDb[id]) openDrawer(dbHtml(byDb[id]));
  }});

  let filter = 'all';
  document.querySelectorAll('.chip').forEach(ch => {{
    ch.onclick = () => {{
      document.querySelectorAll('.chip').forEach(x => x.classList.remove('on'));
      ch.classList.add('on');
      filter = ch.getAttribute('data-f');
      apply();
    }};
  }});
  const q = document.getElementById('q');
  q.addEventListener('input', apply);
  function apply(){{
    const s = (q.value||'').toLowerCase();
    document.querySelectorAll('#pn-table tbody tr').forEach(tr => {{
      const id = tr.getAttribute('data-id');
      const r = byPn[id];
      if(!r) return;
      let ok = true;
      if(filter==='LCV' || filter==='CV') ok = r.segment === filter;
      if(filter==='e6d') ok = /6d/i.test(r.billed_emission_label||'');
      if(filter==='e6') ok = /Euro 6(?!d)/i.test(r.billed_emission_label||'') || /Euro 6 \\(/i.test(r.billed_emission_label||'');
      if(filter==='e5') ok = /Euro 5/i.test(r.billed_emission_label||'');
      const hay = (r.pn+' '+r.description+' '+(r.billed_emission_label||'')+' '+(r.series||[]).join(' ')+' '+(r.top_dbs||[]).map(d=>d.db).join(' ')).toLowerCase();
      if(s && hay.indexOf(s)<0) ok = false;
      tr.style.display = ok ? '' : 'none';
    }});
    document.querySelectorAll('#db-table tbody tr').forEach(tr => {{
      const id = tr.getAttribute('data-id');
      const r = byDb[id];
      if(!r) return;
      const hay = (r.label+' '+r.distributor_code+' '+(r.interval_txt||'')).toLowerCase();
      tr.style.display = (!s || hay.indexOf(s)>=0) ? '' : 'none';
    }});
  }}
}})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
