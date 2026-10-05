#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the IDS 2026 country action board — one self-contained page per country.

Folds the separate study pages into a pairing view plus a short action list, so a
distributor sees one page for a country instead of eight studies.

Sources (all on disk, all read at build time, nothing invented):
  * 02_dashboards/ids/IDS_2026_dealer_compare.html  -- File A, its embedded dealer spine
    (sections A-E per dealer with country + network averages). File A is NOT rebuilt.
  * 01_data/00_derived/pms_capture_by_db_year.csv   -- PMS capture. Total leads; genuine is a
    second lens. Aggregated at build time exactly as the existing parts-Kaizen builder does.
  * 01_data/00_derived/wallet_waterfall.csv         -- GPS euro ceiling and captured euro.
  * 01_data/00_derived/gps_spu_by_distributor.csv   -- GPS euro billed, fleet units, fleet source.
  * 01_data/00_derived/dealer_sellout_gps_2025.csv  -- what the distributor sells on to dealers.
  * 01_data/08_Distributor/IDS_2026/reports/kaizen_ids/study_payload.json -- Kaizen action shape.

Fleet honesty: a GPS percentage is printed only where the two fleet files agree for that
market in 2025. Where they disagree (Ireland, Portugal, UK CV, Germany) the euro is shown and
the page says the percentage is not shown and why.

Output: 02_dashboards/ids/IDS_2026_Country_Action.html (UTF-8, no BOM, no CDN, no fetch).
"""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "04_tools" / "ids_dealer_ranking"))

DERIVED = ROOT / "01_data" / "00_derived"
IDS_REPORTS = ROOT / "01_data" / "08_Distributor" / "IDS_2026" / "reports"
FILE_A = ROOT / "02_dashboards" / "ids" / "IDS_2026_dealer_compare.html"
OUT = ROOT / "02_dashboards" / "ids" / "IDS_2026_Country_Action.html"

SOURCE_NOTE_IDS = "Assessment: dealer self-assessment, one round, August 2026 snapshot"


# --------------------------------------------------------------------------- helpers

def _f(v):
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _money_short(v):
    if v is None:
        return None
    a = abs(v)
    if a >= 1_000_000:
        return f"EUR {v/1_000_000:.2f}M"
    if a >= 1_000:
        return f"EUR {v/1_000:.0f}k"
    return f"EUR {v:,.0f}"


def _eur(v):
    return None if v is None else f"EUR {v:,.0f}"


BANNED = ["AIM", "PRISM", "DLOD", "IDS", "GPS", "BVP", "IML", "ITUK", "IUK",
          "UMI", "UTI", "campaign", "goed", "slecht"]


def banned_hits(text: str) -> dict:
    out = {}
    for b in BANNED:
        n = len(re.findall(r"\b" + re.escape(b) + r"\b", text, re.I))
        if n:
            out[b] = n
    for ext in (".csv", ".json", ".py"):
        if ext in text:
            out[ext] = text.count(ext)
    return out


def strip_tokens(text: str) -> str:
    """Remove the banned words from a copied question string, keeping it readable.

    The question text is evidence, not label. We keep it and drop only the internal token.
    """
    t = text
    t = re.sub(r"\s+and/or\s+Dealer participates in all centrally-organized programs and activities "
               r"from the Distributor with the aim of improving the customer satisfaction of the "
               r"individual repairer\.?", ".", t, flags=re.I)
    t = re.sub(r"\brecall or service campaign\b", "recall or service action", t, flags=re.I)
    t = re.sub(r"\bGenuine and BVP parts\b", "genuine and alternative parts", t, flags=re.I)
    t = re.sub(r"\bpart of the Distributor['\u2019]s organized activities\b",
               "part of the distributor's organised activities", t, flags=re.I)
    t = re.sub(r"\s{2,}", " ", t).strip()
    if t and not t.endswith((".", "?", "!")):
        t += "."
    return t


def truncate(text: str, n: int) -> str:
    t = " ".join(text.split())
    if len(t) <= n:
        return t
    cut = t[: n - 1].rsplit(" ", 1)[0]
    return cut + "\u2026"


# --------------------------------------------------------------------------- File A spine

def load_file_a(path: Path) -> dict:
    """Extract the `const DATA = {...}` object File A embeds. Read-only."""
    html = path.read_text(encoding="utf-8")
    i = html.index("const DATA")
    j = html.index("{", i)
    depth = 0
    in_str = None
    esc = False
    k = j
    while k < len(html):
        c = html[k]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == in_str:
                in_str = None
        else:
            if c in "\"'`":
                in_str = c
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
        k += 1
    return json.loads(html[j:k + 1])


def file_a_country_to_db(country: str) -> list[str]:
    """Which distributor books feed this assessment country.

    'Benelux' is a roll-up of Belgium + Netherlands + Luxembourg across the one
    Belgium parts book; its own programme covers the three markets.
    """
    c = country.strip().lower()
    if c in ("belgium", "netherlands", "luxembourg"):
        return ["BELGIUM"]
    if c == "benelux":
        return ["BELGIUM"]
    if c in ("uk cv",):
        return ["ITUK"]
    if c in ("uk lcv",):
        return ["IUK"]
    if c == "israel lcv":
        return ["UMI"]
    if c == "norway":
        return ["NORWAY"]
    if c == "switzerland":
        return ["SWITZERLAND"]  # no parts book row; honest gap
    return [country.upper()]


# --------------------------------------------------------------------------- data loaders

def load_pms() -> dict:
    """Total capture per book for 2025. Total leads. Genuine is a second lens."""
    exp_t, act_t, rev_t, gap_t = {}, {}, {}, {}
    exp_g, act_g = {}, {}
    path = DERIVED / "pms_capture_by_db_year.csv"
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("year") != "2025":
                continue
            db = row.get("distributor_code")
            lt = (row.get("line_type") or "").lower()
            exp = _f(row.get("expected_qty")) or 0.0
            act = _f(row.get("actual_qty")) or 0.0
            gap = _f(row.get("revenue_gap_eur")) or 0.0
            rev = _f(row.get("actual_rev_eur")) or 0.0
            if lt == "total":
                exp_t[db] = exp_t.get(db, 0.0) + exp
                act_t[db] = act_t.get(db, 0.0) + act
                rev_t[db] = rev_t.get(db, 0.0) + rev
                gap_t[db] = gap_t.get(db, 0.0) + gap
            elif lt == "genuine":
                exp_g[db] = exp_g.get(db, 0.0) + exp
                act_g[db] = act_g.get(db, 0.0) + act
    out = {}
    for db in exp_t:
        tot = act_t[db] / exp_t[db] if exp_t[db] > 0 else None
        gen = act_g.get(db, 0.0) / exp_g[db] if exp_g.get(db, 0.0) > 0 else None
        out[db] = {
            "capture_total_pct": tot,
            "capture_genuine_pct": gen,
            "capture_billed_eur": rev_t.get(db),
            "capture_gap_eur": gap_t.get(db),
        }
    return out


FLEET_BASIS_TEXT = {
    "v18_actual": "the fleet workbook",
    "ituk_dvla_2026": "the UK vehicle register (2026)",
    "v18_proxy_2025": "an estimate, no register held",
}


def load_fleet() -> dict:
    """Parts billed euro, fleet units and where the fleet came from, per book for 2025.

    `billed_eur` is what we BILLED (spend per unit x units), not the distributor's
    sales to its dealers.
    """
    out = {}
    path = DERIVED / "gps_spu_by_distributor.csv"
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("year") != "2025":
                continue
            db = row.get("distributor_code")
            units = _f(row.get("uio_units"))
            spu = _f(row.get("spend_per_unit_eur"))
            src = row.get("uio_source") or ""
            out[db] = {
                "units": units,
                "spend_per_unit_eur": spu,
                "billed_eur": (units * spu) if (units and spu) else None,
                "target_eur": _f(row.get("max_spend_eur")),
                "fleet_basis": FLEET_BASIS_TEXT.get(src, "a recorded fleet figure"),
                "period_basis": row.get("period_basis") or "",
            }
    return out
def load_wallet() -> dict:
    """Target spend ceiling and captured euro per book for 2025, plus fleet."""
    out = {}
    path = DERIVED / "wallet_waterfall.csv"
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("year") != "2025":
                continue
            db = row.get("distributor_code")
            out[db] = {
                "units": _f(row.get("uio_units")),
                "target_eur": _f(row.get("theoretical_wallet_eur")),
                "captured_total_eur": _f(row.get("captured_total_eur")),
                "uncaptured_eur": _f(row.get("uncaptured_eur")),
                "capture_pct": _f(row.get("gps_pct")),
            }
    return out


def load_sellout() -> dict:
    """What the distributor sells on to its dealers, 2025, per book."""
    out = {}
    path = DERIVED / "dealer_sellout_gps_2025.csv"
    if not path.is_file():
        return out
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            db = row.get("distributor_code")
            out.setdefault(db, {"rows": [], "eur": 0.0, "qty": 0.0})
            out[db]["rows"].append(row)
            out[db]["eur"] += _f(row.get("total_eur")) or 0.0
            out[db]["qty"] += _f(row.get("sellout_qty")) or 0.0
    return out


def load_kaizen() -> dict:
    """Action shape and the dealer pick list from the existing Kaizen study."""
    path = IDS_REPORTS / "kaizen_ids" / "study_payload.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Country assembly

DB_LABEL = {
    "BELGIUM": "the Benelux parts book (covers Belgium, Netherlands, Luxembourg)",
    "CYPRUS": "the Cyprus parts book",
    "DENMARK": "the Denmark parts book",
    "GERMANY": "the Germany parts book",
    "GREECE": "the Greece parts book",
    "HUNGARY": "the Hungary parts book",
    "IRELAND": "the Ireland parts book",
    "ITUK": "the UK truck parts book",
    "IUK": "the UK pickup parts book",
    "MALTA": "the Malta parts book",
    "NORWAY": "the Norway parts book",
    "PORTUGAL": "the Portugal parts book",
    "ROMANIA": "the Romania parts book",
    "UMI": "the Israel light commercial parts book",
    "UTI": "the Israel light commercial book (separate distributor, never blended)",
}


def build_countries(file_a, pms, fleet, wallet, sellout, kaizen) -> dict:
    countries = []
    dealer_by_country = {}
    for d in file_a["dealers"]:
        dealer_by_country.setdefault(d["country"], []).append(d)

    kaizen_by_db = {}
    for fd in kaizen.get("focus_dealers", []):
        kaizen_by_db.setdefault(fd["country"], []).append({
            "name": fd["name"],
            "total_pct": fd.get("ids_total_pct"),
        })

    section_labels = {s["id"]: s["label"] for s in file_a["sections"]}
    questions = file_a["questions"]
    q_index = {q["id"]: q for q in questions}

    for country in file_a["countries"]:
        rows = dealer_by_country.get(country, [])
        prof = file_a["country_profiles"].get(country, {})
        dbs = file_a_country_to_db(country)

        # ---- PMS chip: total leads
        pms_rec = None
        for db in dbs:
            if db in pms:
                pms_rec = dict(pms[db])
                break

        # ---- what we billed the book, and the fleet it rests on
        billed_rec = None
        for db in dbs:
            if db in fleet:
                billed_rec = dict(fleet[db])
                billed_rec["wallet"] = wallet.get(db)
                break
        percent_shown = False
        percent_note = None
        if billed_rec and billed_rec.get("wallet"):
            wu = billed_rec["wallet"].get("units")
            gu = billed_rec.get("units")
            if gu and wu:
                agree = abs(gu - wu) <= max(2.0, 0.005 * max(gu, wu))
                if agree:
                    percent_shown = True
                    percent_note = "The fleet figure for this market is signed off."
                else:
                    percent_note = (
                        f"Two fleet figures are in circulation for this market, "
                        f"{gu:,.0f} and {wu:,.0f}, so the percentage is not shown."
                    )
            elif not gu:
                percent_note = "No fleet figure is signed off for this market, so the percentage is not shown."

        # ---- dealer hit list (this country only), below the country average on parts + service
        avg = prof.get("total_pct")
        below = []
        for x in rows:
            sec = x.get("sections") or {}
            dd = sec.get("D") or {}
            cc = sec.get("C") or {}
            total = x.get("total_pct")
            if total is None or avg is None:
                continue
            if total < avg:
                below.append({
                    "name": x["name"],
                    "total_pct": total,
                    "vs_country_pp": (total - avg) * 100,
                    "d_pct": dd.get("pct"),
                    "d_avg": dd.get("country_avg_pct"),
                    "c_pct": cc.get("pct"),
                    "c_avg": cc.get("country_avg_pct"),
                    "totals_only": bool(x.get("totals_only")),
                })
        below.sort(key=lambda r: r["total_pct"])

        # ---- section comparison bars, per section
        sections = []
        for sid in ("A", "B", "C", "D", "E"):
            v = (prof.get("sections_pct") or {}).get(sid)
            net = (file_a["network"]["sections_pct"] or {}).get(sid)
            # the country may not have sat this section at all
            not_scored = v is None
            sections.append({
                "id": sid,
                "label": section_labels.get(sid, sid),
                "country_pct": v,
                "network_pct": net,
                "not_scored": not_scored,
            })

        # ---- country-level softest parts items (points lost on the whole country)
        qavg = []
        for i, q in enumerate(questions):
            if q["section"] != "D":
                continue
            vals = [x["q"][i] for x in rows
                    if isinstance(x.get("q"), list) and i < len(x["q"]) and x["q"][i] is not None]
            if vals:
                qavg.append((sum(vals) / len(vals), q["id"]))
        qavg.sort()
        soft_items = []
        for val, qid in qavg[:4]:
            qi = q_index[qid]
            soft_items.append({
                "ref": qid,
                "text": truncate(strip_tokens(qi["text"]), 150),
                "country_pct": val,
                "max": qi["max"],
            })

        # ---- assessment n and coverage per section
        n_dealers = len(rows)
        sec_sat = {}
        for sid in ("A", "B", "C", "D", "E"):
            sat = sum(1 for x in rows
                      if isinstance((x.get("sections") or {}).get(sid), dict)
                      and (x["sections"][sid].get("pct") is not None))
            sec_sat[sid] = sat

        country_rec = {
            "code": country,
            "name": country,
            "book_labels": [DB_LABEL.get(db, db) for db in dbs],
            "dealer_count": n_dealers,
            "avg_basis_count": prof.get("avg_basis_count"),
            "excluded_from_average_count": prof.get("excluded_from_average_count"),
            "total_pct": avg,
            "network_total_pct": file_a["network"]["total_pct"],
            "network_basis_count": file_a["network"].get("avg_basis_count"),
            "sections": sections,
            "section_sat": sec_sat,
            "pms": pms_rec,
            "billed": billed_rec,
            "percent_shown": percent_shown,
            "percent_note": percent_note,
            "hit_list": below[:14],
            "hit_list_total": len(below),
            "soft_items": soft_items,
            "sellout": _sellout_for(sellout, dbs, country),            "kaizen_focus": kaizen_by_db.get(_kaizen_key(country), []),
            "flags": [
                {
                    "section_label": f["section_label"],
                    "country_pct": f["country_pct"],
                    "vs_network_pp": f["vs_network_pp"],
                }
                for f in kaizen.get("country_flags", [])
                if _flag_key(f["country"]) == _kaizen_key(country)
            ],
        }
        countries.append(country_rec)
    return countries


def _kaizen_key(country: str) -> str:
    c = country.strip().lower()
    return {
        "belgium": "BE", "netherlands": "NL", "uk cv": "ITUK", "uk lcv": "IUK",
        "israel lcv": "ISRAEL", "norway": "RSA", "greece": "PETROS",
        "switzerland": "MIDI_CH", "spain": "MIDI_ES", "france": "MIDI_FR",
        "italy": "MIDI_IT",
    }.get(c, country.upper())


def _flag_key(k: str) -> str:
    return (k or "").strip().upper()


def _sellout_for(sellout, dbs, country):
    for db in dbs:
        rec = sellout.get(db)
        if not rec:
            continue
        rows = rec["rows"]
        if len(rows) == 1:
            r = rows[0]
            return {
                "kind": "network_total",
                "eur": _f(r.get("total_eur")),
                "qty": _f(r.get("sellout_qty")),
                "units": _f(r.get("uio_units")),
                "per_unit": _f(r.get("sellout_spu_eur")),
                "unvalued_share": _f(r.get("qty_unvalued_share")),
            }
        top = sorted(rows, key=lambda r: -(_f(r.get("total_eur")) or 0.0))
        return {
            "kind": "by_dealer",
            "dealers": len(rows),
            "eur": rec["eur"],
            "qty": rec["qty"],
            "top": [
                {"name": r.get("entity"), "eur": _f(r.get("total_eur")),
                 "share": _f(r.get("share_of_network"))}
                for r in top[:10]
            ],
        }
    return None


# ---------------------------------------------------------------------------
# Actions — every action is a real recorded gap, nothing invented

def action_set(c) -> list[dict]:
    """Three to five actions for this distributor, each tied to a real recorded gap.

    Owner and confirm-by date are left blank on purpose: the workspace holds the
    assessment, not the meeting minutes. The one owner we can source is the ISZE
    programme owner recorded on the IDS 26 follow-up summary.
    """
    acts = []

    secs = {s["id"]: s for s in c["sections"]}
    d = secs.get("D", {})

    soft = c["soft_items"]
    if soft and d.get("country_pct") is not None:
        refs = ", ".join(i["ref"] for i in soft[:3])
        items = "; ".join(f'{i["ref"]} {truncate(i["text"], 96)}' for i in soft[:2])
        net_txt = (f'against {d["network_pct"]*100:.1f}% for the network'
                   if d.get("network_pct") is not None else "with no network figure to compare against")
        acts.append({
            "action": f"Close the country-softest parts checklist items: {refs}.",
            "why": (f'Section D parts sits at {d["country_pct"]*100:.1f}% for {c["name"]}, '
                    f'{net_txt}. Softest items: {items}'),
            "source": "Parts assessment, country average per checklist item",
        })

    hit = c["hit_list"]
    if hit:
        worst = hit[0]
        if worst["totals_only"]:
            why = (f'{worst["name"]} is {abs(worst["vs_country_pp"]):.1f} points below the '
                   f'{c["name"]} average ({c["total_pct"]*100:.1f}%). This dealer filed totals only, '
                   f'so no section detail exists — visit before setting anything.')
        else:
            parts = []
            if worst["d_pct"] is not None and worst["d_avg"] is not None:
                parts.append(f'Parts {worst["d_pct"]*100:.1f}% vs country {worst["d_avg"]*100:.1f}%')
            if worst["c_pct"] is not None and worst["c_avg"] is not None:
                parts.append(f'Service {worst["c_pct"]*100:.1f}% vs country {worst["c_avg"]*100:.1f}%')
            why = (f'{worst["name"]} is {abs(worst["vs_country_pp"]):.1f} points below the '
                   f'{c["name"]} average ({c["total_pct"]*100:.1f}%). ' + "; ".join(parts) + ".")
        acts.append({
            "action": f'Agree the development plan with {worst["name"]} (hit list #1).',
            "why": why,
            "source": "Dealer assessment, this country only",
        })

    billed = c["billed"]
    if billed and billed.get("wallet") and billed["wallet"].get("uncaptured_eur"):
        unc = billed["wallet"]["uncaptured_eur"]
        tgt = billed["wallet"].get("target_eur")
        acts.append({
            "action": "Agree the parts billed target for next year against the recorded ceiling.",
            "why": (f'{_money_short(unc)} of the {_money_short(tgt)} target spend per truck is not '
                    f'billed today ({_money_short(billed["billed_eur"])} billed). '
                    f'The assessment does not say why; this is the commercial gap to work.'),
            "source": "Parts billed vs target spend per truck, calendar 2025",
        })

    pms = c["pms"]
    if pms and pms.get("capture_total_pct") is not None:
        gen = pms.get("capture_genuine_pct")
        gen_txt = f" Genuine only is {gen*100:.1f}%." if gen is not None else ""
        acts.append({
            "action": "Agree one action on the maintenance basket, then measure it monthly.",
            "why": (f'Total parts capture is {pms["capture_total_pct"]*100:.1f}% of the expected '
                    f'maintenance basket, on {_money_short(pms.get("capture_billed_eur"))} billed.{gen_txt} '
                    f'A 100% score on the parts checklist is not a capture result — keep the two apart.'),
            "source": "Parts capture, calendar 2025, total lens",
        })

    if c["flags"]:
        f = c["flags"][0]
        acts.append({
            "action": f'Discuss why {c["name"]} scores {f["section_label"]} '
                      f'{f["country_pct"]*100:.1f}% against a network {abs(f["vs_network_pp"]):.1f} '
                      f'points higher.',
            "why": "The section gap is the largest recorded for this country against the network.",
            "source": "Section comparison, this country vs network",
        })

    if c["excluded_from_average_count"]:
        acts.append({
            "action": "Confirm the dealers left out of the country average before quoting it.",
            "why": (f'{c["excluded_from_average_count"]} dealer(s) are outside the average used here '
                    f'({c["avg_basis_count"]} of {c["dealer_count"]} dealers set the {c["name"]} figure).'),
            "source": "Assessment average basis",
        })

    # Where we hold no commercial data at all, the recorded gap is the missing file itself.
    # The ask is real and the page already says the data is not held, so it is named here too.
    no_capture = not c["pms"] or c["pms"].get("capture_total_pct") is None
    no_billed = not c["billed"] or c["billed"].get("billed_eur") is None
    if no_capture and no_billed and len(acts) < 3:
        acts.append({
            "action": "Ask the distributor for its parts sales to dealers, calendar 2025.",
            "why": ("No parts capture row and no parts billed extract exist for this market in the workspace, "
                    "so the two commercial chips are empty. Until the distributor sends the file, the "
                    "conversation can only be about the assessment, not about what the parts business did."),
            "source": "Missing source, stated on the Other data tab",
        })

    return acts[:5]


# ---------------------------------------------------------------------------
# Render

def render(countries, built_at, source_note) -> str:
    payload = json.dumps(countries, ensure_ascii=False, separators=(",", ":"))
    return TEMPLATE.replace("__BUILT_AT__", built_at) \
                   .replace("__SOURCE_NOTE__", source_note) \
                   .replace("__DATA_JSON__", payload)


def main() -> int:
    if not FILE_A.is_file():
        print(f"File A not found: {FILE_A}", file=sys.stderr)
        return 1

    file_a = load_file_a(FILE_A)
    pms = load_pms()
    fleet = load_fleet()
    wallet = load_wallet()
    sellout = load_sellout()
    kaizen = load_kaizen()

    countries = build_countries(file_a, pms, fleet, wallet, sellout, kaizen)
    for c in countries:
        c["actions"] = action_set(c)

    built_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    # Build the source line from what the page actually shows, not from a fixed string.
    ns_gps = sum(1 for c in countries if c["billed"] and c["billed"]["billed_eur"] is not None)
    ns_pct = sum(1 for c in countries if c["percent_shown"])
    source_note = (
        f"Assessment: dealer self-assessment, one round, August 2026 snapshot, "
        f"{file_a['dealer_count']} dealers in {len(countries)} countries. "
        f"Parts capture: network parts basket, calendar 2025, total lens (genuine as a second lens). "
        f"Parts billed: {ns_gps} of {len(countries)} countries hold an extract; the target-spend percentage "
        f"is shown for {ns_pct} where the fleet figure is signed off, and withheld elsewhere."
    )
    html = render(countries, built_at, source_note)
    OUT.write_text(html, encoding="utf-8")

    hits = banned_hits(html)
    print(f"Wrote {OUT}")
    print(f"  countries: {len(countries)}  dealers: {file_a['dealer_count']}")
    print(f"  size: {OUT.stat().st_size/1024:.0f} KB")
    print(f"  banned-term hits: {hits if hits else 'NONE (0)'}")
    for c in countries:
        pm = "-" if not c["pms"] or c["pms"]["capture_total_pct"] is None else f"{c['pms']['capture_total_pct']*100:.1f}%"
        print(f"  {c['name']:14s} actions={len(c['actions'])} hitlist={c['hit_list_total']:>3} "
              f"pms={pm:>6s} gps_eur={'yes' if c['billed'] and c['billed']['billed_eur'] is not None else 'no ':>3s} "
              f"percent_shown={str(c['percent_shown']):5s} soft={len(c['soft_items'])}")
    return 0


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Isuzu dealer standards 2026 - country action board</title>
<style>
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#e8e4dc;color:#222;font-family:"Segoe UI",Helvetica,Arial,sans-serif;font-size:14px;line-height:1.45}
h1,h2,h3{font-family:Georgia,"Times New Roman",serif;font-weight:400;margin:0;color:#1a2b4a}
.banner{background:#15233c;color:#f7f4ee;padding:22px 30px 26px}
.banner .k{font-size:11px;letter-spacing:.08em;text-transform:uppercase;opacity:.78}
.banner h1{color:#f7f4ee;font-size:28px;margin:7px 0 9px;max-width:34ch}
.banner .rule{width:56px;height:3px;background:#c0552d;margin:0 0 11px}
.banner p{margin:0;max-width:84ch;color:#f7f4ee;opacity:.95}
.wrap{max-width:1180px;margin:0 auto;padding:16px 20px 46px}
.pick{background:#f7f4ee;border-left:3px solid #1a2b4a;padding:11px 14px;margin:0 0 14px;display:flex;flex-wrap:wrap;gap:12px;align-items:center}
.pick label{font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:#6b6256}
select{font-family:inherit;font-size:14px;padding:7px 10px;border:1px solid #9aa8bc;background:#fff;color:#222;min-width:290px}
.pick .who{margin-left:auto;font-size:12px;color:#6b6256}
.relink{background:#eef3f9;border-left:3px solid #9aa8bc;padding:9px 13px;margin:0 0 14px;font-size:12.5px;color:#1a2b4a}
.relink a{color:#c0552d;font-weight:700}
.relink a:hover{color:#15233c}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:0 0 14px}
.kpi{background:#f7f4ee;border-top:3px solid #1a2b4a;padding:11px 13px;position:relative;cursor:help}
.kpi.gap{border-top-color:#c0552d}
.kpi.warn{border-top-color:#c48a1a}
.kpi .l{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:#6b6256}
.kpi .v{font-family:Georgia,serif;font-size:23px;color:#1a2b4a;margin-top:5px}
.kpi.gap .v{color:#c0552d}
.kpi .s{font-size:12px;color:#6b6256;margin-top:4px}
.tip{display:none;position:absolute;left:10px;right:10px;top:100%;z-index:30;margin-top:8px;background:#15233c;color:#f7f4ee;padding:10px 12px;font-size:12px;line-height:1.45;border-top:3px solid #c0552d;box-shadow:0 4px 14px rgba(0,0,0,.3)}
.kpi:hover .tip,.kpi:focus .tip{display:block}
.panels{background:#fff;box-shadow:0 1px 6px rgba(0,0,0,.08)}
.tabs{display:flex;gap:0;border-bottom:2px solid #1a2b4a;background:#fff}
.tabs button{background:transparent;border:0;border-bottom:2px solid transparent;margin-bottom:-2px;padding:10px 18px;font-size:13px;color:#1a2b4a;cursor:pointer;font-family:inherit}
.tabs button.on{border-bottom-color:#c0552d;font-weight:700}
.room{display:none;padding:16px 18px 22px}
.room.on{display:block}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.card{background:#f7f4ee;padding:13px 15px}
.card.white{background:#fff;border:1px solid #d9d3c8}
.card h3{font-size:15px;margin:0 0 6px}
.card .lead{color:#6b6256;font-size:12px;margin:0 0 10px}
.barrow{display:flex;align-items:center;gap:9px;margin:8px 0}
.barrow .n{width:150px;font-size:12px;color:#1a2b4a}
.barrow .track{flex:1;height:20px;background:#eeeae3;position:relative}
.barrow .fill{height:20px;position:absolute;top:0;left:0;z-index:1}
.barrow .fill.net{background:#15233c;opacity:.32;z-index:0}
.barrow .v{width:56px;text-align:right;font-variant-numeric:tabular-nums;font-size:12px}
.barrow .ns{flex:1;height:20px;background:repeating-linear-gradient(45deg,#eef3f9,#eef3f9 6px,#e4ebf4 6px,#e4ebf4 12px);border:1px dashed #9aa8bc;font-size:10px;color:#1a2b4a;display:flex;align-items:center;justify-content:center;letter-spacing:.04em;text-transform:uppercase}
table{width:100%;border-collapse:collapse;margin:10px 0 4px;font-size:13px}
th{background:#1a2b4a;color:#f7f4ee;text-align:left;padding:8px 10px;font-size:11px;text-transform:uppercase;letter-spacing:.03em}
td{padding:7px 10px;border-bottom:1px solid #d9d3c8;color:#222;vertical-align:top}
tbody tr:nth-child(even){background:#f7f4ee}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.pill{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;padding:2px 7px}
.pill.weak{background:#f3d4d0;color:#8a2a22}
.pill.medium{background:#f8e6c0;color:#8a5a00}
.pill.good{background:#d7efe4;color:#1d6b4a}
.pill.navy{background:#dde4ee;color:#1a2b4a}
.muted{color:#6b6256;font-size:12px}
.tight{margin:6px 0 0;padding-left:18px}
.tight li{margin:5px 0}
.hoverable{border-bottom:1px dotted #6b6256;cursor:help;position:relative}
.hoverable .htip{display:none;position:absolute;left:0;bottom:100%;z-index:40;margin-bottom:6px;width:300px;background:#15233c;color:#f7f4ee;padding:9px 11px;font-size:11.5px;line-height:1.45;border-top:3px solid #c0552d;box-shadow:0 4px 14px rgba(0,0,0,.3)}
.hoverable:hover .htip,.hoverable:focus .htip{display:block}
.blank{background:#fff !important}
.blank td{height:34px;background:#fff}
.askcard{background:#fff;border:1px dashed #9aa8bc;padding:13px 15px}
.askcard h3{color:#1a2b4a}
.emptystate{background:#eef3f9;border:1px dashed #9aa8bc;padding:13px 15px;color:#1a2b4a}
.foot{margin-top:20px;padding-top:11px;border-top:1px solid #d9d3c8;font-size:11px;color:#6b6256}
.foot p{margin:4px 0}
@media(max-width:960px){.kpis,.g2{grid-template-columns:1fr}.barrow .n{width:110px}}
</style>
</head>
<body>
<div class="banner">
  <div class="k">Dealer standards &middot; country action board &middot; snapshot __BUILT_AT__</div>  <h1>One page per country: pair it, then act on it</h1>
  <div class="rule"></div>
  <p>The network picture and the map stay on the dealer comparison page. This page is the country view:
  how the country sits against its own dealers and against the network, how parts capture and parts billed
  compare with the assessment, and the short list to agree in the room. Blank owner and date stay blank
  until the meeting fills them.</p>
</div>
<div class="wrap">

<div class="pick">
  <label for="countryPick">Country</label>
  <select id="countryPick" aria-label="Country"></select>
  <span class="who" id="pickerNote"></span>
</div>
<p class="relink">Full network, map and the complete checklist for every dealer:
<a href="IDS_2026_dealer_compare.html">open the dealer comparison page</a>. This page is the country view
of the same assessment; it does not repeat the map.</p>

<div class="kpis" id="kpis"></div>

<div class="panels">
  <div class="tabs" role="tablist">
    <button class="on" type="button" data-tab="pair" role="tab" aria-selected="true">Pair</button>
    <button type="button" data-tab="act" role="tab" aria-selected="false">Act</button>
    <button type="button" data-tab="other" role="tab" aria-selected="false">Other data</button>
  </div>

  <div class="room on" id="pair">
    <div class="g2">
      <div class="card">
        <h3>Parts score against parts capture</h3>
        <p class="lead">Every market we hold both figures for. This country is the terracotta dot.</p>
        <div id="scatter"></div>
      </div>
      <div class="card">
        <h3>Sections against the country and the network</h3>
        <p class="lead">Solid bar is the country average. Pale navy is the network. A section the country did not sit reads not scored, never zero.</p>
        <div id="sectionBars"></div>
      </div>
    </div>
    <p class="muted" id="scatterNote"></p>
  </div>

  <div class="room" id="act">
    <h3 style="margin:0 0 4px">Actions for this distributor</h3>
    <p class="muted" style="margin:0 0 10px">Each action is a recorded gap, not a proposal. Owner and confirm-by are blank because the workspace holds the assessment, not the meeting minutes.</p>
    <div id="actions"></div>
    <h3 style="margin:20px 0 4px">Dealer hit list &mdash; this country only</h3>
    <p class="muted" style="margin:0 0 8px" id="hitNote"></p>
    <div id="hitList"></div>
    <div id="softItems" style="margin-top:16px"></div>
  </div>

  <div class="room" id="other">
    <div class="g2" id="otherGrid"></div>
  </div>
</div>

<div class="foot">
  <p id="sourceLine">__SOURCE_NOTE__</p>
  <p>Parts billed is what we invoiced the distributor. Sales to dealer is what the distributor invoiced its
  dealers. They are different measures and are never added together. Either measure can be stated per truck
  in service; a per-truck figure is not a target and not a score.</p>
  <p>Country names are spelled out. Where a market is served by a distributor book that covers more than one
  country, the book is named on the chip.</p>
  <p>Confidential &mdash; internal working page for the country conversation.</p>
</div>
</div>

<script>
const COUNTRIES = __DATA_JSON__;
const BUILT_AT = "__BUILT_AT__";

const $ = (s, r) => (r || document).querySelector(s);
const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
/* Section labels arrive as "A. Premises, Facility and Clothing"; the letter is enough on screen. */
const secShort = l => String(l || "").replace(/^[A-E]\.\s*/, "").replace(/\s*&\s*Accessories$/, "");
const lbl = s => { const t = String(s || ""); return esc(t.charAt(0).toUpperCase() + t.slice(1)); };
const pct1 = v => v == null ? "\u2014" : (v * 100).toFixed(1) + "%";
const pp1 = v => v == null ? "\u2014" : (v >= 0 ? "+" : "") + v.toFixed(1) + " pp";
const eur = v => v == null ? "\u2014" : "EUR " + Math.round(v).toLocaleString("en-GB");
const eurShort = v => {
  if (v == null) return "\u2014";
  const a = Math.abs(v);
  if (a >= 1e6) return "EUR " + (v/1e6).toFixed(2) + "M";
  if (a >= 1e3) return "EUR " + (v/1e3).toFixed(0) + "k";
  return "EUR " + Math.round(v).toLocaleString("en-GB");
};

/* Read the country name so no sentence starts with a lower-case word. */
const cap = s => { const t = String(s || ""); return t.charAt(0).toUpperCase() + t.slice(1); };
function findCountry(code){ return COUNTRIES.find(c => c.code === code) || COUNTRIES[0]; }

/* ---------- chips ---------- */
function chip(label, value, sub, tip, cls){
  return '<div class="kpi ' + (cls||"") + '" tabindex="0"><div class="l">' + esc(label) + '</div>' +
    '<div class="v">' + value + '</div><div class="s">' + sub + '</div>' +
    '<div class="tip">' + tip + '</div></div>';
}

function renderChips(c){
  const D = c.sections.find(s => s.id === "D");
  const netD = D ? D.network_pct : null;
  const dCls = D && !D.not_scored && netD != null ? (D.country_pct >= netD ? "" : "gap") : "warn";
  const dVal = D && !D.not_scored ? pct1(D.country_pct) : "not scored";
  const dSub = D && !D.not_scored && netD != null
      ? "parts section &middot; network " + pct1(netD)
      : "parts section &middot; not assessed for " + esc(c.name);
  const dTip = "The Parts &amp; Accessories section average for " + esc(c.name) + ", its own dealers only, " +
    (c.avg_basis_count != null ? c.avg_basis_count + " of " + c.dealer_count + " dealers in the average" : "the same dealer set") +
    ". Snapshot " + BUILT_AT + ". It does NOT include a parts-book result, does not include a market size, " +
    "and is not a capture figure.";

  let pmsVal = "\u2014", pmsSub = "no parts book row for this market", pmsCls = "warn", pmsTip;
  if (c.pms && c.pms.capture_total_pct != null){
    pmsVal = pct1(c.pms.capture_total_pct);
    pmsSub = "total lens &middot; calendar 2025";
    pmsCls = "";
    const gen = c.pms.capture_genuine_pct != null
      ? " Genuine only is " + pct1(c.pms.capture_genuine_pct) + " \u2014 a second lens, never the headline." : "";
    pmsTip = "Total parts capture = total parts sold divided by the total maintenance basket the fleet expects, " +
      "calendar 2025, " + esc(c.book_labels.join(", ")) + ". " + (c.pms.capture_billed_eur != null ? eur(c.pms.capture_billed_eur) + " billed. " : "") +
      gen + " It does NOT prove that a higher assessment score lifts capture, and it is not dealer-level.";
  } else {
    pmsTip = "No parts book row exists for this market in the capture file, so no capture figure is shown. " +
      "Empty on purpose, not zero.";
  }

  let gpsVal = "\u2014", gpsSub = "no parts billed extract for this market", gpsCls = "warn", gpsTip;
  if (c.billed && c.billed.billed_eur != null){
    gpsVal = eurShort(c.billed.billed_eur);
    if (c.percent_shown && c.billed.wallet && c.billed.wallet.capture_pct != null){
      gpsSub = pct1(c.billed.wallet.capture_pct / 100) + " of target spend per truck";
      gpsCls = "";
    } else {
      gpsSub = "percentage not shown";
      gpsCls = "warn";
    }
    gpsTip = "Parts we billed the distributor in calendar 2025: " + eur(c.billed.billed_eur) + ", " +
      (c.billed.units != null ? Math.round(c.billed.units).toLocaleString("en-GB") + " trucks in service, from " +
        esc(c.billed.fleet_basis) : "fleet not held") +
      "." + (c.percent_note ? " " + esc(c.percent_note) : "") +
      " It does NOT include the distributor's sales to its dealers, and it is not a forecast.";
  } else {
    gpsTip = "No parts billed extract for this market. Empty on purpose, not zero.";
  }

  const nHit = c.hit_list_total;
  const acts = c.actions ? c.actions.length : 0;
  const actVal = acts + " proposed";
  const actSub = nHit + " dealer" + (nHit === 1 ? "" : "s") + " below the country average";
  const actTip = "Actions are derived from this country's recorded gaps: " + acts + " at the moment. " +
    "Owner and confirm-by date are blank where the workspace holds no minutes. " + nHit +
    " dealer(s) sit below the " + esc(c.name) + " average of " + pct1(c.total_pct) + " and appear on the hit list.";

  $("#kpis").innerHTML =
    chip("Parts (D) vs country", dVal, dSub, dTip, dCls) +
    chip("Parts capture", pmsVal, pmsSub, pmsTip, pmsCls) +
    chip("Parts billed", gpsVal, gpsSub, gpsTip, gpsCls) +
    chip("Open actions", actVal, actSub, actTip, nHit ? "gap" : "");
}

/* ---------- pairing scatter ---------- */
function renderScatter(c){
  const W = 520, H = 320, pad = 44;
  const pts = COUNTRIES.filter(x => x.sections.find(s => s.id === "D" && !s.not_scored) &&
                                   x.pms && x.pms.capture_total_pct != null && x.code !== "Benelux")
    .map(x => ({ code: x.code, name: x.name,
                 d: x.sections.find(s => s.id === "D").country_pct,
                 p: x.pms.capture_total_pct }));
  if (pts.length < 2){
    $("#scatter").innerHTML = '<div class="emptystate">Not enough markets hold both a parts score and a ' +
      'capture figure to draw the pairing. Nothing is plotted rather than a misleading single point.</div>';
    $("#scatterNote").textContent = "";
    return;
  }
  const xs = pts.map(p => p.d), ys = pts.map(p => p.p);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const xpad = Math.max(0.03, (x1 - x0) * 0.12), ypad = Math.max(0.04, (y1 - y0) * 0.15);
  const X = v => pad + (v - (x0 - xpad)) / ((x1 + xpad) - (x0 - xpad)) * (W - pad - 14);
  const Y = v => H - pad - (v - (y0 - ypad)) / ((y1 + ypad) - (y0 - ypad)) * (H - pad - 16);
  let s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" height="auto" role="img" aria-label="Parts score against parts capture">';
  s += '<rect x="0" y="0" width="' + W + '" height="' + H + '" fill="#fff"/>';
  // gridlines from the data range only
  for (let i = 0; i <= 4; i++){
    const v = (x0 - xpad) + ((x1 + xpad) - (x0 - xpad)) * i / 4;
    const x = X(v);
    s += '<line x1="' + x + '" y1="16" x2="' + x + '" y2="' + (H - pad) + '" stroke="#e8e4dc" stroke-width="1"/>';
    s += '<text x="' + x + '" y="' + (H - pad + 16) + '" font-size="10" fill="#6b6256" text-anchor="middle">' + (v*100).toFixed(0) + '%</text>';
  }
  for (let i = 0; i <= 4; i++){
    const v = (y0 - ypad) + ((y1 + ypad) - (y0 - ypad)) * i / 4;
    const y = Y(v);
    s += '<line x1="' + pad + '" y1="' + y + '" x2="' + (W - 14) + '" y2="' + y + '" stroke="#e8e4dc" stroke-width="1"/>';
    s += '<text x="' + (pad - 7) + '" y="' + (y + 3.5) + '" font-size="10" fill="#6b6256" text-anchor="end">' + (v*100).toFixed(0) + '%</text>';
  }
  s += '<text x="' + (W/2) + '" y="' + (H - 6) + '" font-size="11" fill="#1a2b4a" text-anchor="middle">Section D parts score, country average</text>';
  s += '<text transform="translate(12,' + (H/2) + ') rotate(-90)" font-size="11" fill="#1a2b4a" text-anchor="middle">Parts capture, total lens</text>';
  pts.forEach(p => {
    const cur = p.code === c.code;
    const cx = X(p.d), cy = Y(p.p);
    s += '<circle cx="' + cx + '" cy="' + cy + '" r="' + (cur ? 7 : 4.5) + '" fill="' + (cur ? "#c0552d" : "#9aa8bc") +
         '"' + (cur ? ' stroke="#15233c" stroke-width="2"' : "") + '><title>' + esc(p.name) + ': parts score ' +
         pct1(p.d) + ', capture ' + pct1(p.p) + (cur ? " — this country" : "") + '</title></circle>';
    if (cur) s += '<text x="' + (cx + 11) + '" y="' + (cy + 4) + '" font-size="11.5" font-weight="700" fill="#15233c">' + esc(p.name) + '</text>';
  });
  s += '</svg>';
  $("#scatter").innerHTML = s;
  $("#scatterNote").textContent = pts.length + " markets hold both a parts score and a capture figure. " +
    "The pairing is context, not cause: a high parts score has not been shown to lift capture.";
}

/* ---------- sections vs country and network ---------- */
function renderSections(c){
  let s = "";
  c.sections.forEach(sec => {
    if (sec.not_scored){
      s += '<div class="barrow"><div class="n">' + esc(secShort(sec.label)) + '</div><div class="ns">not scored</div><div class="v">\u2014</div></div>';
      return;    }
    const cp = sec.country_pct * 100, np = sec.network_pct == null ? null : sec.network_pct * 100;
    const col = np == null ? "#c0552d" : (cp >= np ? "#1d9e75" : "#c0552d");
    s += '<div class="barrow"><div class="n">' + esc(secShort(sec.label)) + '</div><div class="track">' +
      (np != null ? '<div class="fill net" style="width:' + np + '%"></div>' : "") +
      '<div class="fill" style="width:' + cp + '%;background:' + col + '"></div></div>' +
      '<div class="v">' + cp.toFixed(1) + '</div></div>';
  });
  s += '<p class="muted" style="margin-top:8px">Solid bar = ' + esc(c.name) + ' average, on ' +
       (c.avg_basis_count != null ? c.avg_basis_count : c.dealer_count) + ' of ' + c.dealer_count +
       ' dealers. Pale navy = anonymous network average (' + (c.network_basis_count != null ? c.network_basis_count : "\u2014") +
       ' dealers, all markets). Green is above the network, terracotta below.</p>';
  $("#sectionBars").innerHTML = s;
}

/* ---------- actions ---------- */
function renderActions(c){
  const acts = c.actions || [];
  if (!acts.length){
    $("#actions").innerHTML = '<div class="emptystate">No action could be derived from recorded gaps for ' +
      esc(c.name) + '. Blank rather than invented.</div>';
    return;
  }
  let html = '<table><thead><tr><th style="width:34%">Action</th><th style="width:40%">Why</th>' +
    '<th style="width:13%">Owner</th><th style="width:13%">Confirm by</th></tr></thead><tbody>';
  acts.forEach(a => {
    html += '<tr><td><b>' + esc(a.action) + '</b><div class="muted">' + esc(a.source) + '</div></td>' +
      '<td>' + esc(a.why) + '</td>' +
      '<td class="muted" style="background:#fff">to be agreed in the room</td>' +
      '<td class="muted" style="background:#fff">to be agreed in the room</td></tr>';
  });
  html += '</tbody></table>';
  html += '<p class="muted">Owner and confirm-by are left blank on purpose. The assessment is on disk; the ' +
    'meeting minutes that name people and dates are not, so nothing is filled in.</p>';
  $("#actions").innerHTML = html;
}

/* ---------- dealer hit list ---------- */
function renderHitList(c){
  if (!c.hit_list_total){
    $("#hitNote").textContent = "Every dealer in " + c.name + " sits at or above the country average.";
    $("#hitList").innerHTML = '<div class="emptystate">No dealer is below the ' + esc(c.name) +
      ' average of ' + pct1(c.total_pct) + '.</div>';
    return;
  }
  $("#hitNote").textContent = c.hit_list_total + " of " + c.dealer_count + " dealers sit below the " +
    c.name + " average of " + pct1(c.total_pct) + ". Nearest to furthest below.";
  let html = '<table><thead><tr><th>Dealer</th><th class="num">Total</th><th class="num">vs country</th>' +
    '<th class="num">Parts</th><th class="num">Service</th><th>Read</th></tr></thead><tbody>';
  c.hit_list.forEach(d => {
    const tag = '<span class="hoverable">' + esc(d.name) + '<span class="htip">' + esc(d.name) + ': total ' +
      pct1(d.total_pct) + ' against the national (' + esc(c.name) + ') average ' + pct1(c.total_pct) +
      ' = ' + pp1(d.vs_country_pp) + '.</span></span>';
    const parts = d.d_pct == null ? '<span class="muted">not scored</span>'
      : '<span class="hoverable">' + pct1(d.d_pct) + '<span class="htip">Parts score ' + pct1(d.d_pct) +
        ' against the national average ' + pct1(d.d_avg) + '.</span></span>';
    const svc = d.c_pct == null ? '<span class="muted">not scored</span>'
      : '<span class="hoverable">' + pct1(d.c_pct) + '<span class="htip">Service score ' + pct1(d.c_pct) +
        ' against the national average ' + pct1(d.c_avg) + '.</span></span>';
    const read = d.totals_only ? '<span class="pill navy">totals only</span>'
      : (d.total_pct < 0.6 ? '<span class="pill weak">needs improvement</span>'
         : (d.total_pct < 0.8 ? '<span class="pill medium">medium</span>' : '<span class="pill good">good</span>'));
    html += '<tr><td>' + tag + '</td><td class="num">' + pct1(d.total_pct) + '</td>' +
      '<td class="num">' + pp1(d.vs_country_pp) + '</td><td class="num">' + parts + '</td>' +
      '<td class="num">' + svc + '</td><td>' + read + '</td></tr>';
  });
  html += '</tbody></table>';
  html += '<p class="muted">Hover any dealer or score for its standing against the national average. ' +
    '"Totals only" means the dealer filed a total and no section detail \u2014 not scored, never zero. ' +
    'The bands are good at 80% and above, medium 60% to 80%, needs improvement below 60%.</p>';
  $("#hitList").innerHTML = html;
}

function renderSoftItems(c){
  if (!c.soft_items.length){
    $("#softItems").innerHTML = "";
    return;
  }
  let html = '<h3 style="margin:0 0 4px">Softest parts items, whole ' + esc(c.name) + '</h3>' +
    '<p class="muted" style="margin:0 0 8px">Checklist items where the country as a whole scores lowest. ' +
    'Useful if the distributor wants one network-level action on top of the dealer visits.</p><ul class="tight">';
  c.soft_items.forEach(i => {
    html += '<li><b>' + esc(i.ref) + '</b> \u2014 country ' + pct1(i.country_pct) + ' \u00b7 ' + esc(i.text) + '</li>';
  });
  html += '</ul>';
  $("#softItems").innerHTML = html;
}

/* ---------- other data ---------- */
function renderOther(c){
  const cards = [];
  const so = c.sellout;
  if (so && so.kind === "by_dealer"){
    let rows = so.top.map(t => '<tr><td>' + esc(t.name) + '</td><td class="num">' + eur(t.eur) +
      '</td><td class="num">' + pct1(t.share) + '</td></tr>').join("");
    cards.push('<div class="card white"><h3>What the distributor sells on to dealers</h3>' +
      '<p class="lead">Calendar 2025, ' + so.dealers + ' dealers, ' + eurShort(so.eur) + ' in total. Top ten by value.</p>' +
      '<table><thead><tr><th>Dealer</th><th class="num">Value</th><th class="num">Share</th></tr></thead>' +
      '<tbody>' + rows + '</tbody></table>' +
      '<p class="muted">Sales to dealer is what the distributor invoices its dealers. It is a different measure ' +
      'from parts billed and the two are never added.</p></div>');
  } else if (so && so.kind === "network_total"){
    cards.push('<div class="card white"><h3>What the distributor sells on to dealers</h3>' +
      '<p class="lead">Calendar 2025, network total for ' + esc(c.name) + '.</p>' +
      '<div class="barrow"><div class="n">Sales to dealer</div><div class="track">' +
      '<div class="fill" style="width:72%;background:#15233c;opacity:.75"></div></div>' +
      '<div class="v">' + eurShort(so.eur) + '</div></div>' +
      '<p class="muted">' + eur(so.eur) + ' over ' + Math.round(so.qty).toLocaleString("en-GB") + ' parts' +
      (so.units ? ', on ' + Math.round(so.units).toLocaleString("en-GB") + ' trucks in service' : "") + '. ' +
      (so.per_unit != null ? 'That is ' + eur(so.per_unit) + ' per truck. ' : "") +
      (so.unvalued_share ? (so.unvalued_share*100).toFixed(1) + "% of the parts carry no parts-list price, so the euro understates the volume. " : "") +
      'Dealer-level split is not held for this market \u2014 the file carries a network total only.</p></div>');
  } else {
    cards.push('<div class="askcard"><h3>Sales to dealer</h3><p class="lead">Not held for this market.</p></div>' +
      '<p class="muted">Ask the distributor for calendar-2025 parts sales to its dealers, by dealer if they hold it.</p>');
  }

  cards.push('<div class="askcard"><h3>What we need from the distributor</h3>' +
    '<p class="lead">Two files would let this page carry the commercial picture, not just the assessment.</p>' +
    '<ul class="tight"><li>Parts sales to their dealers for calendar 2025, by dealer if it exists at that grain.</li>' +
    '<li>Their own view of what an assessed item is worth: which checklist points actually move their parts ' +
    'business, so the action list starts from their numbers and not only ours.</li></ul>' +
    '<p class="muted">Send the two files, or say which of the two they cannot produce. Nothing here is a data dump.</p></div>');

  if (c.kaizen_focus && c.kaizen_focus.length){
    const names = c.kaizen_focus.map(f => f.name + " (" + pct1(f.ids_total_pct) + ")").join(", ");
    cards.push('<div class="card"><h3>Dealers already picked in the study</h3><p class="lead">' + esc(names) +
      '</p><p class="muted">These are the dealers the existing study already picked for this market. The hit list ' +
      'above is the wider bottom set.</p></div>');
  }

  $("#otherGrid").innerHTML = cards.join("");
}

/* ---------- country switch ---------- */
function paint(code){
  const c = findCountry(code);
  renderChips(c);
  renderScatter(c);
  renderSections(c);
  renderActions(c);
  renderHitList(c);
  renderSoftItems(c);
  renderOther(c);
  const books = c.book_labels && c.book_labels.length ? " &middot; " + esc(c.book_labels.join("; ")) : "";
  const nD = c.dealer_count === 1 ? "1 dealer" : c.dealer_count + " dealers";
  $("#pickerNote").innerHTML = nD + " assessed" + books;
  document.title = "Isuzu dealer standards 2026 \u2014 " + c.name + " country action board";
}

const sel = $("#countryPick");
COUNTRIES.forEach(c => {
  const o = document.createElement("option");
  o.value = c.code; o.textContent = c.name;
  sel.appendChild(o);
});
/* Match a country however it is written in a link: spaces, underscores, case. */
function normaliseKey(s){
  try { s = decodeURIComponent(s); } catch(e){}
  return String(s || "").toLowerCase().replace(/[^a-z0-9]+/g, "");
}
function requestedCountry(){
  const q = new URLSearchParams(location.search).get("country");
  const h = location.hash ? location.hash.slice(1) : null;
  const want = normaliseKey(q || h || "");
  if (!want) return null;
  return COUNTRIES.find(c => normaliseKey(c.name) === want || normaliseKey(c.code) === want) || null;
}
const preferred = ["Greece", "Belgium", "Malta", "Cyprus", "Portugal"];
const req = requestedCountry();
const start = req ? req.name
  : (preferred.find(n => COUNTRIES.some(c => c.name === n)) || COUNTRIES[0].name);
sel.value = COUNTRIES.find(c => c.name === start).code;
sel.addEventListener("change", () => paint(sel.value));
window.addEventListener("hashchange", () => {
  const c = requestedCountry();
  if (c){ sel.value = c.code; paint(c.code); }
});

document.querySelectorAll(".tabs button").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tabs button").forEach(b => { b.classList.remove("on"); b.setAttribute("aria-selected","false"); });
    document.querySelectorAll(".room").forEach(r => r.classList.remove("on"));
    btn.classList.add("on"); btn.setAttribute("aria-selected","true");
    document.getElementById(btn.getAttribute("data-tab")).classList.add("on");
  });
});

/* A tab can be linked directly too: ...html?country=Greece&tab=act */
function requestedTab(){
  const t = (new URLSearchParams(location.search).get("tab") || "").trim().toLowerCase();
  return ["pair", "act", "other"].includes(t) ? t : null;
}

paint(sel.value);
const wantTab = requestedTab();
if (wantTab){
  const btn = document.querySelector('.tabs button[data-tab="' + wantTab + '"]');
  if (btn) btn.click();
}
</script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
