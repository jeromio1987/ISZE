# -*- coding: utf-8 -*-
"""DPD reman feasibility — thin two-track study (D-Max Euro 6d + ITUK truck)."""
from __future__ import annotations

import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"C:\Users\jerom\Desktop\claude\ISZE")
DER = ROOT / "01_data" / "00_derived"
WARRANTY_XLSX = ROOT / "01_data" / "06_Warranty"
OUT_DIR = ROOT / "02_dashboards" / "sales"
BUILD = OUT_DIR / "_build"
OUT_HTML = OUT_DIR / "ISZE_DPD_Reman_Feasibility_20261006.html"
OUT_CMD = OUT_DIR / "OPEN_ISZE_DPD_Reman_Feasibility.cmd"
OUT_JSON = BUILD / "dpd_reman_feasibility_20261006_payload.json"
OUT_WORKLIST = OUT_DIR / "ISZE_DPD_Reman_Price_Collection_Worklist_20261006.csv"
DPD_PAYLOAD = BUILD / "dpd_full_analysis_20261006_payload.json"

JPY = 163.7
GBP_TO_EUR = 1.12

# Track A
PN_A = "8975359391"
PN_A_REF_CLEAN = "8981776324"  # Euro 5 — cleaning/IAM price reference only

# Track B
PN_B_BILLED = "8975074422"
PN_B_CLAIM = ["8982049420", "8982050610", "8982878080"]
PN_B_GREY = "8982278993"  # CV ASM with KS grey observation

WORKLIST_PNS = [PN_A, PN_A_REF_CLEAN, PN_B_BILLED, PN_B_GREY] + PN_B_CLAIM
WORKLIST_MARKETS = ["IUK", "UMI", "ITUK", "BELGIUM", "GERMANY", "SWEDEN"]
WORKLIST_QUOTE_TYPES = [
    "OEM dealer quote (genuine new)",
    "Reman / cleaning specialist",
    "IAM / aftermarket online",
]

# Named specialist / programme quote targets (refresh worklist; not invented dealer €)
SPECIALIST_TARGETS = [
    {
        "pn": PN_B_BILLED,
        "market": "ITUK",
        "quote_type": "ITUK parts — new-in-lieu dealer €",
        "status": "TO_COLLECT",
        "observed_eur": "",
        "source_url": "https://www.isuzutruck.co.uk/new-initiative-on-dpd-filters/",
        "notes": (
            "Chase 2026-10-06: programme page public; no dealer € on site. "
            "Draft ask to ITUK parts still open. Core return required."
        ),
    },
    {
        "pn": PN_B_BILLED,
        "market": "ITUK",
        "quote_type": "Driveline HGV DPF exchange (IAM/specialist)",
        "status": "ANCHOR_PUBLIC",
        "observed_eur": "",
        "source_url": "https://www.drivelineemissions.com/",
        "notes": (
            "Chase 2026-10-06 reconfirm: from ~£350 exchange on HGV brands — NOT Isuzu-catalogued. "
            "Isuzu PN quote still TO_COLLECT."
        ),
    },
    {
        "pn": PN_B_CLAIM[0],
        "market": "ITUK",
        "quote_type": "Intechnic SCRT reman (IAM/specialist)",
        "status": "ANCHOR_PUBLIC",
        "observed_eur": "",
        "source_url": "https://www.intechnic.co.uk/faq/",
        "notes": (
            "Chase 2026-10-06: public FAQ std DPF cleaning £180+VAT; thermal +£100+VAT. "
            "Not Isuzu full-can reman / not OE. Isuzu N-series reman quote still TO_COLLECT "
            "(enquiries@intechnic.co.uk)."
        ),
    },
    {
        "pn": PN_A,
        "market": "IUK",
        "quote_type": "D-Max DPF cleaner (Ceramex / Optymha path)",
        "status": "QUOTE_NEEDED",
        "observed_eur": "",
        "source_url": "https://www.optym-ha.fr/services/filtre-a-particules/",
        "notes": (
            "Chase 2026-10-06: live site is optym-ha.fr (not optymha.com). "
            "No public € — quote via form / 04 76 22 31 84. "
            "Peter: Optymha (FR) = Ceramex path since Brexit."
        ),
    },
    {
        "pn": PN_A_REF_CLEAN,
        "market": "BELGIUM",
        "quote_type": "Ceramex / Optymha cleaning (Euro 5 ref can)",
        "status": "QUOTE_NEEDED",
        "observed_eur": "",
        "source_url": "https://www.ceramex.com/",
        "notes": (
            "Chase 2026-10-06: Ceramex quote-only (enquiries@ceramex.com). "
            "Industrial pool charges new-unit price when injecting new cores (Peter)."
        ),
    },
    {
        "pn": PN_A,
        "market": "IUK",
        "quote_type": "Greencar PKW DPF cleaning (peer floor)",
        "status": "ANCHOR_PUBLIC",
        "observed_eur": "359",
        "source_url": "https://www.greencar-automotive.de/",
        "notes": (
            "Chase 2026-10-06: €359 incl VAT PKW cleaning + pickup ~€47. Prior ladder had €449 — "
            "peer car DPF, not D-Max Euro 6d OE reman."
        ),
    },
    {
        "pn": PN_A,
        "market": "POLAND",
        "quote_type": "Diesel-Partner truck DPF cleaning (public net)",
        "status": "ANCHOR_PUBLIC",
        "observed_eur": "660",
        "source_url": "https://www.diesel-partner.pl/en/czyszczenie-dpf-fap.html",
        "notes": (
            "Public net list 2026-10-06: cars €90; truck SCR/CAT Euro 5 €375; "
            "truck DPF Euro 6 €660; Euro 6 cartridge €310. Not Isuzu-catalogued; "
            "used as Track A cleaning mid band until Optymha quote."
        ),
    },
    # Freight — Optymha FR hub (COLLECT; not invented)
    {
        "pn": PN_A,
        "market": "UMI",
        "quote_type": "Freight round-trip → Optymha FR (core + return)",
        "status": "TO_COLLECT",
        "observed_eur": "",
        "source_url": "https://www.optym-ha.fr/",
        "notes": "Chase: no public RT rate. Draft internal freight ask. ASSUMPTION bands until quote.",
    },
    {
        "pn": PN_A,
        "market": "IUK",
        "quote_type": "Freight round-trip → Optymha FR (core + return)",
        "status": "TO_COLLECT",
        "observed_eur": "",
        "source_url": "https://www.optym-ha.fr/",
        "notes": "Chase: no public RT rate. UK→FR D-Max can. Draft freight ask.",
    },
    {
        "pn": PN_A,
        "market": "PORTUGAL",
        "quote_type": "Freight round-trip → Optymha FR (core + return)",
        "status": "TO_COLLECT",
        "observed_eur": "",
        "source_url": "https://www.optym-ha.fr/",
        "notes": "Interest gate market — volume thin; freight quote still needed for pool maths.",
    },
    {
        "pn": PN_A,
        "market": "SWEDEN",
        "quote_type": "Freight round-trip → Optymha FR (core + return)",
        "status": "TO_COLLECT",
        "observed_eur": "",
        "source_url": "https://www.optym-ha.fr/",
        "notes": "Chase: no public RT rate. Track A hub lane.",
    },
    {
        "pn": PN_A,
        "market": "BELGIUM",
        "quote_type": "Freight round-trip → Optymha FR (core + return)",
        "status": "TO_COLLECT",
        "observed_eur": "",
        "source_url": "https://www.optym-ha.fr/",
        "notes": "Chase: no public RT rate. Short haul vs Israel/Nordics.",
    },
    {
        "pn": PN_A,
        "market": "GERMANY",
        "quote_type": "Freight round-trip → Optymha FR (core + return)",
        "status": "TO_COLLECT",
        "observed_eur": "",
        "source_url": "https://www.optym-ha.fr/",
        "notes": "Chase: no public RT rate. Track A hub lane.",
    },
    {
        "pn": PN_B_BILLED,
        "market": "ITUK",
        "quote_type": "Freight — UK local (not FR hub primary)",
        "status": "TO_COLLECT",
        "observed_eur": "",
        "source_url": "",
        "notes": "Track B is UK-local; stress vs new-in-lieu, not Optymha FR round-trip.",
    },
]

# Landed-cost cleaning bands — low/mid from Diesel-Partner public net (PL), high = stress ASSUMPTION.
# Still not Optymha/Isuzu dealer €. Mid 660 = truck DPF Euro 6 public net.
CLEANING_ASSUMPTION_EUR = [375.0, 660.0, 900.0]
FREIGHT_RT_ASSUMPTION_EUR = [80.0, 150.0, 250.0]
NG_ASSUMPTION_RATES = [0.10, 0.25, 0.40]
FIXED_HUB_ADMIN_ASSUMPTION_EUR = 2000.0  # annual fixed logistics/admin to test min pcs/yr
THIN_PCS_YR = 10.0  # below this → too thin for own lane


def build_portugal_visit_brief() -> dict:
    """Dealer visit questions — Peter asked Jerome to gauge Portugal interest."""
    return {
        "purpose": (
            "Portugal dealer visit — gauge interest in a vehicle DPD exchange / cleaning path "
            "(Optymha / Ceramex family). Not a price negotiation."
        ),
        "context_one_liner": (
            "Our book on the Euro 6d hero can is thin in Portugal (~12 pcs in the study window) — "
            "interest matters more than volume proof."
        ),
        "questions": [
            {
                "n": 1,
                "ask": "When a D-Max DPD fails, what do you do today — new OE, aftermarket, or off-car cleaning?",
                "why": "Maps the real substitute before we talk programme.",
            },
            {
                "n": 2,
                "ask": "What do you (or the customer) typically pay for cleaning or exchange, all-in, if you use it?",
                "why": "Dealer € floor — COLLECT, do not invent.",
            },
            {
                "n": 3,
                "ask": "Would you send a sealed can to a FR hub (2–3 day turnaround) if collection and return were arranged?",
                "why": "Interest gate Peter set — yes / no / only if € X.",
            },
            {
                "n": 4,
                "ask": "What turnaround and downtime can a workshop accept before they just fit a new unit?",
                "why": "Sets whether Optymha 24–72h return is usable.",
            },
            {
                "n": 5,
                "ask": "Who do you use today for DPF cleaning in PT / ES border, if anyone?",
                "why": "Local cleaner vs FR hub — competitive reality.",
            },
        ],
        "do_not": [
            "Do not promise a programme or a price.",
            "Do not mix ITUK truck new-in-lieu into the pickup conversation.",
            "Do not treat billed pcs as market size in the room.",
        ],
        "report_back": (
            "One line per dealer: today path / rough € if said / yes-no on FR hub / max downtime / local cleaner name."
        ),
    }


def build_db_interest_note() -> dict:
    """Short distributor interest asks — same gate as Portugal, before Optymha volume maths."""
    return {
        "purpose": "Interest first (Peter). Ask IUK / UMI / Sweden — not MIDI.",
        "markets": [
            {"code": "IUK", "label": "Isuzu UK pickup", "angle": "Largest EU LCV book after UMI on the hero PN."},
            {"code": "UMI", "label": "UMI Israel", "angle": "Largest billed book on the hero PN — freight to FR is the stress."},
            {"code": "SWEDEN", "label": "Sweden", "angle": "Next commercial pocket; Nordics freight vs volume."},
        ],
        "questions": [
            "Do dealers already clean or exchange D-Max DPDs, and through whom?",
            "Would they use a FR hub exchange if collection / return and a cleaning € sat under half of what they pay for new?",
            "Rough dealer all-in for cleaning or reman today (COLLECT — one number is enough).",
        ],
        "draft_opener": (
            "Hello,\n\n"
            "We are checking interest in a vehicle DPD cleaning / exchange path (FR hub, Ceramex process family) "
            "before any commercial launch.\n\n"
            "Three short answers help: what dealers do today, whether a 2–3 day FR round-trip is usable, "
            "and a rough all-in cleaning or exchange € if known.\n\n"
            "Kind regards,"
        ),
    }


def build_mail_brief() -> dict:
    """Structured extract from Outlook pull 2026-10-06 (see INBOX md)."""
    return {
        "extracted_at": "2026-10-06",
        "source_file": r"01_data\90_INBOX\DPD_Exchange_mail_extract_20261006.md",
        "name_note": "Mailbox is Osamu Ishikawa (Osamu.Ishikawa@isuzu.de), not Osamy.",
        "mails": [
            {
                "who": "Peter De Clercq",
                "date": "2026-10-06 14:32",
                "subject": "Request for Input on a New Vehicle DPD Exchange Programme",
                "ask": "Feasibility of a vehicle DPD exchange programme; Jerome to gauge interest at Portugal dealer visit. Advice on questions, hurdles, truck vs pickup, success factors.",
                "named_pns_markets": "No PN. Portugal visit. Vehicle DBs vs industrial.",
                "money": None,
                "decision_or_open": "Portugal interest check first. Programme not decided. Hitachi EXU as structural model; industrial Stage V intervals cut cleaning volume.",
            },
            {
                "who": "Osamu Ishikawa",
                "date": "2026-10-06 16:02",
                "subject": "Re: Request for Input on a New Vehicle DPD Exchange Programme",
                "ask": "Distributor/customer survey design + hurdles (NG cores, pickup shape, CERAMEX vs air-blow, ISZJ official proof).",
                "named_pns_markets": "Pickup vs truck DPD shape; CERAMEX; prior exchange programme; no written vehicle DPD inspection interval.",
                "money": None,
                "decision_or_open": "Expect high NG at cleaner → empty core pool → many brand-new units injected. Education vs cheap air-blow. Need Isuzu-official story.",
            },
            {
                "who": "Peter De Clercq (via Parts mailbox)",
                "date": "2026-10-06 16:33",
                "subject": "RE: Request for Input on a New Vehicle DPD Exchange Programme",
                "ask": "Confirm interest assessment first; explain special cleaning tech when promoting.",
                "named_pns_markets": "Optymha (FR Ceramex subsidiary) since Brexit.",
                "money": "Prior vehicle cleaning programme: pricing was the main challenge. Industrial rule: new unit injected into pool → charge equivalent of a new unit.",
                "decision_or_open": "Interest first; keep Osamu informed. Pool economics still the commercial risk.",
            },
        ],
        "coverage_note": (
            "Peter: latest two on this thread (14:32 + 16:33). "
            "Osamu: only one DPD/reman mail in recent from: results; next mails are purchasing/IMG IDs."
        ),
        "study_impact": [
            "Ask is exchange/cleaning (Ceramex/Optymha), not OEM reman list — keep three-way sandwich.",
            "Prior vehicle programme failed mainly on pricing; industrial pool charges new-unit on core injection.",
            "Osamu NG-core / empty-pool hurdle strengthens HOLD / CONDITIONAL caveats.",
            "Portugal interest gauge is the human gate before programme build.",
        ],
    }


def build_web_anchors() -> list[dict]:
    """Public competitive anchors — not dealer transactions. observed_at = research day."""
    observed = "2026-10-06"
    caveat = "Public listing / news page — not a dealer transaction. Do not treat as DB sell price."
    return [
        {
            "label": "ITUK new-in-lieu DPD programme",
            "kind": "oe_programme",
            "country": "UK",
            "currency": None,
            "amount": None,
            "amount_note": "Chase 2026-10-06: programme public; dealer € still not on page — COLLECT",
            "source_url": "https://www.isuzutruck.co.uk/new-initiative-on-dpd-filters/",
            "observed_at": observed,
            "caveat": caveat,
            "implication": "Track B ceiling is Japan/ITUK programme, not full list. Contrasts OE vs reman vs cleaning.",
        },
        {
            "label": "Driveline HGV DPF service exchange",
            "kind": "iam_specialist",
            "country": "UK",
            "currency": "GBP",
            "amount": 350,
            "amount_note": "Chase reconfirm: from ~£350 exchange (various HGV brands) — not Isuzu-catalogued",
            "source_url": "https://www.drivelineemissions.com/",
            "observed_at": observed,
            "caveat": caveat + " IAM/specialist, not OE approval.",
            "implication": "Worklist target for Track B specialist quote on Isuzu PN.",
        },
        {
            "label": "Intechnic UK DPF cleaning (FAQ floor)",
            "kind": "cleaner",
            "country": "UK",
            "currency": "GBP",
            "amount": 180,
            "amount_note": "Std cleaning £180+VAT; thermal +£100+VAT — FAQ, not Isuzu reman list",
            "source_url": "https://www.intechnic.co.uk/faq/",
            "observed_at": observed,
            "caveat": caveat + " Cleaning floor only; SCRT reman for Isuzu PN still quote-only.",
            "implication": "Sets a cleaning floor under Track B; reman/exchange still needs a named Isuzu quote.",
        },
        {
            "label": "Freedom Emissions Isuzu 4JJ1 DPF (US)",
            "kind": "context_us",
            "country": "US",
            "currency": "USD",
            "amount": 869,
            "amount_note": "US$869 new; reman/exchange also offered — refs include 898205061-class",
            "source_url": "https://dalessuperstore.com/i-23921419-isuzu-4jj1-dpfreplacement-898147066-8981470660-2-9408b-300-0-isuzu-4jj1.html",
            "observed_at": observed,
            "caveat": caveat + " Not EU dealer price.",
            "implication": "Context only for insert vs full-can split — not a Europe reman quote.",
        },
        {
            "label": "Directfit UK N-series aftermarket DPF IZF006",
            "kind": "iam_floor",
            "country": "UK",
            "currency": "GBP",
            "amount": 576.75,
            "amount_note": "£576.75 inc VAT listing — Euro 4 N-series fitment window",
            "source_url": "https://www.directfit.co.uk/dpf-fap-isuzu-n-series-izf006",
            "observed_at": observed,
            "caveat": caveat + " Floor check for CV IAM, not D-Max Euro 6d.",
            "implication": "CV IAM floor — do not map to Track A Euro 6d hero.",
        },
        {
            "label": "Greencar Automotive PKW DPF cleaning (DE)",
            "kind": "cleaner",
            "country": "DE",
            "currency": "EUR",
            "amount": 359,
            "amount_note": "€359 incl VAT PKW cleaning; pickup ~€47 — peer car DPF, not D-Max Euro 6d",
            "source_url": "https://www.greencar-automotive.de/",
            "observed_at": observed,
            "caveat": caveat + " Peer PKW cleaner; prior observation €449 may be a different listing.",
            "implication": "Cleaning peer floor for Track A sensitivity — not a dealer reman quote.",
        },
        {
            "label": "Diesel-Partner truck DPF cleaning (PL public net)",
            "kind": "cleaner",
            "country": "PL",
            "currency": "EUR",
            "amount": 660,
            "amount_note": "Truck DPF Euro 6 €660 net; also Euro 5 SCR/CAT €375, cartridge €310, cars €90",
            "source_url": "https://www.diesel-partner.pl/en/czyszczenie-dpf-fap.html",
            "observed_at": observed,
            "caveat": caveat + " Public net price list — not Isuzu PN, not Optymha quote.",
            "implication": "Sets the mid cleaning band on the landed-cost grid until Optymha answers.",
        },
        {
            "label": "Optymha FAP cleaning (FR hub)",
            "kind": "cleaner",
            "country": "FR",
            "currency": None,
            "amount": None,
            "amount_note": "Chase 2026-10-06: quote-only (form / 04 76 22 31 84); site optym-ha.fr",
            "source_url": "https://www.optym-ha.fr/services/filtre-a-particules/",
            "observed_at": observed,
            "caveat": "Named in internal mail 2026-10-06; public site has process + logistics, not €.",
            "implication": "Primary EU cleaning path for vehicle exchange — € stays QUOTE_NEEDED.",
        },
        {
            "label": "Ceramex DPF cleaning (UK)",
            "kind": "cleaner",
            "country": "UK",
            "currency": None,
            "amount": None,
            "amount_note": "Chase 2026-10-06: quote-only enquiries@ceramex.com",
            "source_url": "https://www.ceramex.com/",
            "observed_at": observed,
            "caveat": caveat + " Same process family as Optymha path; not a public price list.",
            "implication": "Euro 5 ref-can / UK cleaning quote target.",
        },
    ]


def norm_pn(x) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    s = str(x).strip()
    s = re.sub(r"\.0$", "", s)
    return "" if s.lower() in ("nan", "none", "") else s


def feur(v, d=0):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(x):
        return "—"
    if d == 0:
        return f"€{x:,.0f}"
    return f"€{x:,.{d}f}"


def fnum(v, d=0):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(x):
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


def load_list_prices(pns: list[str]) -> dict[str, dict]:
    pl = pd.read_parquet(DER / "pricing_pr00_ie40.parquet")
    pl["part_number"] = pl["part_number"].map(norm_pn)
    # Prefer non-superseded current PR00
    out = {}
    for pn in pns:
        rows = pl[pl["part_number"] == pn]
        if rows.empty:
            continue
        live = rows[rows["is_superseded_row"] == False] if "is_superseded_row" in rows.columns else rows
        r = live.iloc[0] if len(live) else rows.iloc[0]
        out[pn] = {
            "list_eur": round(float(r["sp_eur"]), 2),
            "description": str(r.get("description") or ""),
            "newest_pn": norm_pn(r.get("newest_pn")),
            "superseded": bool(r.get("is_superseded_row")),
            "valid_start": str(r.get("valid_start") or ""),
        }
    return out


def load_price_obs(pns: list[str]) -> list[dict]:
    po = pd.read_parquet(DER / "price_observations.parquet")
    po["part_no"] = po["part_no"].map(norm_pn)
    hit = po[po["part_no"].isin(pns)].copy()
    rows = []
    for _, r in hit.iterrows():
        pe = r.get("price_eur")
        try:
            pe = float(pe) if pe is not None and not (isinstance(pe, float) and math.isnan(pe)) else None
        except (TypeError, ValueError):
            pe = None
        rows.append(
            {
                "pn": r["part_no"],
                "description": str(r.get("description") or "")[:120] or None,
                "source": str(r.get("source") or ""),
                "country": str(r.get("country") or ""),
                "price_eur": round(pe, 2) if pe is not None else None,
                "currency": str(r.get("currency") or ""),
                "price_type": str(r.get("price_type") or ""),
                "competitor_brand": str(r.get("competitor_brand") or "") or None,
                "competitor_pn": str(r.get("competitor_pn") or "") or None,
                "stock": str(r.get("stock") or ""),
                "observed_at": str(r.get("observed_at") or ""),
            }
        )
    # de-dupe identical pn/source/country/price
    seen = set()
    uniq = []
    for r in rows:
        k = (r["pn"], r["source"], r["country"], r["price_eur"], r["price_type"], r.get("competitor_brand"))
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    return uniq


def stack_for_pn(pn: str, lists: dict, obs: list[dict], wart_eur: float | None, asp: float | None) -> list[dict]:
    """Ordered price ladder rows; missing = collect."""
    ladder = []
    if pn in lists:
        ladder.append(
            {
                "rung": "Our list (IE40 PR00)",
                "eur": lists[pn]["list_eur"],
                "note": lists[pn]["description"]
                + (f" · superseded → {lists[pn]['newest_pn']}" if lists[pn]["superseded"] else ""),
                "status": "observed",
            }
        )
    else:
        ladder.append({"rung": "Our list (IE40 PR00)", "eur": None, "note": "Not on current IE40 pull", "status": "collect"})

    if asp is not None:
        ladder.append(
            {
                "rung": "Billed ASP to distributors (~24m)",
                "eur": round(asp, 2),
                "note": "Transfer price, not dealer / end-customer",
                "status": "observed",
            }
        )
    else:
        ladder.append({"rung": "Billed ASP to distributors (~24m)", "eur": None, "note": "No billed lines", "status": "collect"})

    if wart_eur is not None and wart_eur > 0:
        ladder.append(
            {
                "rung": "Warranty parts € (this PN in extract)",
                "eur": round(wart_eur, 2),
                "note": "Claims book total for this PN — not a unit price",
                "status": "observed",
            }
        )

    pn_obs = [o for o in obs if o["pn"] == pn and o.get("price_eur")]
    cleaning = [o for o in pn_obs if "clean" in (o.get("description") or "").lower() or "clean" in (o.get("price_type") or "").lower()]
    # Greencar descriptions
    cleaning += [
        o
        for o in pn_obs
        if o not in cleaning
        and re.search(r"clean|soot|particulate filter cleaning", (o.get("description") or ""), re.I)
    ]
    iam = [
        o
        for o in pn_obs
        if o not in cleaning
        and o.get("price_type") in ("online_median", "aftermarket_rrp")
        and o.get("competitor_brand")
    ]
    grey = [o for o in pn_obs if o.get("price_type") == "genuine_grey"]

    if cleaning:
        for o in cleaning:
            ladder.append(
                {
                    "rung": f"Cleaning / reman-adjacent ({o.get('competitor_brand') or o['source']})",
                    "eur": o["price_eur"],
                    "note": f"{o['country']} · {o.get('description') or o['price_type']}",
                    "status": "observed",
                }
            )
    else:
        ladder.append(
            {
                "rung": "Cleaning / reman specialist quote",
                "eur": None,
                "note": "No observation on disk — collect",
                "status": "collect",
            }
        )

    if iam:
        for o in sorted(iam, key=lambda x: x["price_eur"] or 0):
            ladder.append(
                {
                    "rung": f"IAM / online ({o.get('competitor_brand')})",
                    "eur": o["price_eur"],
                    "note": f"{o['country']} · {o['source']}",
                    "status": "observed",
                }
            )
    else:
        ladder.append({"rung": "IAM / aftermarket", "eur": None, "note": "No observation — collect", "status": "collect"})

    if grey:
        for o in grey:
            ladder.append(
                {
                    "rung": f"Grey genuine ({o['source']})",
                    "eur": o["price_eur"],
                    "note": f"{o['country']} · stock {o.get('stock') or '?'}",
                    "status": "observed",
                }
            )
    else:
        ladder.append({"rung": "Grey genuine", "eur": None, "note": "No observation — collect", "status": "collect"})

    return ladder


def volume_for_pn(dpd: dict, pn: str) -> dict:
    asm = {r["pn"]: r for r in dpd["assemblies"]}
    total_eur = float(dpd["hero"]["asm_eur"])
    r = asm.get(pn)
    if not r:
        return {
            "pn": pn,
            "found": False,
            "eur": 0,
            "qty": 0,
            "asp": None,
            "share_of_asm": 0,
            "top_dbs": [],
            "segment": None,
            "emission": None,
            "series": [],
            "description": None,
        }
    asp = r["eur"] / r["qty"] if r["qty"] else None
    return {
        "pn": pn,
        "found": True,
        "eur": r["eur"],
        "qty": r["qty"],
        "asp": round(asp, 2) if asp else None,
        "share_of_asm": round(r["eur"] / total_eur, 4) if total_eur else 0,
        "top_dbs": r.get("top_dbs") or [],
        "segment": r.get("segment"),
        "emission": r.get("billed_emission_label") or r.get("euro_norm_label"),
        "series": r.get("series") or [],
        "description": r.get("description"),
        "tonnage": r.get("tonnage"),
    }


def db_cut_for_pns(dpd: dict, pns: list[str], focus_dbs: list[str] | None = None) -> list[dict]:
    rows = []
    for db in dpd["db_matrix"]:
        code = db["distributor_code"]
        if focus_dbs and code not in focus_dbs and not any(
            (db.get("by_pn_all") or {}).get(pn, {}).get("eur", 0) for pn in pns
        ):
            # still include if has any of the pns
            pass
        eur = qty = 0.0
        by_pn = {}
        for pn in pns:
            cell = (db.get("by_pn_all") or {}).get(pn) or (db.get("by_pn") or {}).get(pn) or {"eur": 0, "qty": 0}
            by_pn[pn] = cell
            eur += float(cell.get("eur") or 0)
            qty += float(cell.get("qty") or 0)
        if eur <= 0 and focus_dbs and code not in focus_dbs:
            continue
        if eur <= 0 and not focus_dbs:
            continue
        rows.append(
            {
                "distributor_code": code,
                "label": db.get("label") or code,
                "scope": db.get("scope"),
                "eur": round(eur, 2),
                "qty": round(qty, 2),
                "by_pn": by_pn,
            }
        )
    rows.sort(key=lambda x: -x["eur"])
    return rows


def load_lcv_vin_core() -> dict:
    """D-Max assembly VIN pool for track A (and Euro 5 ref context)."""
    raw = DER / "warranty_fy26_raw.csv"
    if not raw.exists():
        return {"available": False, "reason": "warranty_fy26_raw.csv missing"}
    d = pd.read_csv(raw, low_memory=False)
    op = d["OperationDescription"].fillna("").str.upper()
    asm = d[op.str.contains(r"PARTICULATE DEFUSER ASSEMBLY|PARTICULATE DEFUSER ASSY", regex=True)].copy()
    asm["Mileage"] = pd.to_numeric(asm["Mileage"], errors="coerce")
    asm["PartsNo"] = asm["PartsNo"].map(norm_pn)
    asm["Vinno"] = asm["Vinno"].astype(str).str.upper()

    def bucket(km):
        if pd.isna(km):
            return "unknown"
        if km < 30000:
            return "early"
        if km >= 50000:
            return "wear_out"
        return "mid"

    asm["bucket"] = asm["Mileage"].map(bucket)
    # one VIN = worst/first claim line with lowest km for classification
    vin_first = asm.sort_values("Mileage").groupby("Vinno", as_index=False).first()

    def summary(sub: pd.DataFrame, label: str) -> dict:
        if sub.empty:
            return {"label": label, "vins": 0, "lines": 0}
        vf = sub.sort_values("Mileage").groupby("Vinno", as_index=False).first()
        n = len(vf)
        early = int((vf["bucket"] == "early").sum())
        wear = int((vf["bucket"] == "wear_out").sum())
        mid = int((vf["bucket"] == "mid").sum())
        return {
            "label": label,
            "vins": n,
            "lines": int(len(sub)),
            "median_km": float(vf["Mileage"].median()) if n else None,
            "early_vins": early,
            "mid_vins": mid,
            "wear_out_vins": wear,
            "reman_candidate_share": round(wear / n, 3) if n else None,
            "early_share": round(early / n, 3) if n else None,
            "top_pns": (
                sub["PartsNo"]
                .value_counts()
                .head(5)
                .rename_axis("pn")
                .reset_index(name="lines")
                .to_dict("records")
            ),
            "markets": (
                sub["DistributorName"]
                .value_counts()
                .head(8)
                .rename_axis("market")
                .reset_index(name="lines")
                .to_dict("records")
            ),
        }

    hero = asm[asm["PartsNo"] == PN_A]
    all_asm = asm
    return {
        "available": True,
        "window_note": "LCV / D-Max claim export AssessMonth FY26 window in warranty_fy26_raw.csv",
        "thresholds": {"early_km": 30000, "wear_out_km": 50000},
        "all_assembly": summary(all_asm, "All D-Max DPD assembly claims"),
        "hero_pn": summary(hero, f"PN {PN_A} only"),
        "n_vins_all": int(vin_first["Vinno"].nunique()),
    }


def load_cv_vin_core() -> dict:
    files = [
        ("Warranty_CV_2025.xlsx", "Sheet1"),
        ("Warranty_CV_2025.xlsx", "DATA WITHOUT MIDI"),
        ("CV Warranty.xlsx", "10_25-12_2025"),
        ("CV Warranty.xlsx", "2024"),
        ("CV warranty01_03_2026.xlsx", "Sheet1"),
    ]
    frames = []
    for fn, sh in files:
        p = WARRANTY_XLSX / fn
        if not p.exists():
            continue
        frames.append(pd.read_excel(p, sheet_name=sh))
    if not frames:
        return {"available": False, "reason": "CV warranty xlsx missing"}
    cv = pd.concat(frames, ignore_index=True)
    cv = cv.drop_duplicates(subset=["VIN17", "BILLYMD", "PARTNBR", "DOCNBR"], keep="first")
    op = cv["OPE_Name"].fillna("").astype(str).str.upper()
    cv["MILE"] = pd.to_numeric(cv["MILE"], errors="coerce")
    cv["PARTNBR"] = cv["PARTNBR"].map(norm_pn)
    cv["VIN17"] = cv["VIN17"].astype(str).str.upper()

    asm = cv[op.str.contains(r"PARTICULATE DEFUSER ASSEMBLY|PARTICULATE DEFUSER ASSY", regex=True)].copy()
    filt = cv[op.str.contains(r"PARTICULATE DEFUSER FILTER", regex=True)].copy()

    def bucket(km):
        if pd.isna(km):
            return "unknown"
        if km < 30000:
            return "early"
        if km >= 80000:
            return "wear_out"
        return "mid"

    def summarise(sub: pd.DataFrame, label: str, market_filter: str | None = None) -> dict:
        s = sub.copy()
        if market_filter:
            s = s[s["CTY_Name"].astype(str).str.upper() == market_filter.upper()]
        if s.empty:
            return {"label": label, "vins": 0, "lines": 0}
        s["bucket"] = s["MILE"].map(bucket)
        vf = s.sort_values("MILE").groupby("VIN17", as_index=False).first()
        n = len(vf)
        early = int((vf["bucket"] == "early").sum())
        wear = int((vf["bucket"] == "wear_out").sum())
        mid = int((vf["bucket"] == "mid").sum())
        series = vf["VIN17"].str[3:6].value_counts().head(6)
        return {
            "label": label,
            "vins": n,
            "lines": int(len(s)),
            "median_km": float(vf["MILE"].median()) if n else None,
            "early_vins": early,
            "mid_vins": mid,
            "wear_out_vins": wear,
            "reman_candidate_share": round(wear / n, 3) if n else None,
            "early_share": round(early / n, 3) if n else None,
            "series": series.rename_axis("series").reset_index(name="vins").to_dict("records"),
            "top_pns": (
                s["PARTNBR"].value_counts().head(8).rename_axis("pn").reset_index(name="lines").to_dict("records")
            ),
            "markets": (
                s["CTY_Name"].value_counts().head(10).rename_axis("market").reset_index(name="lines").to_dict("records")
            ),
        }

    # UK = ITUK book for trucks
    uk_asm = summarise(asm, "UK truck — DPD assembly", "UK")
    uk_filt = summarise(filt, "UK truck — DPD filter R&R", "UK")
    all_asm = summarise(asm, "All markets — DPD assembly (context)")
    israel_filt = summarise(filt, "Israel — filter R&R (UTI context)", "ISRAEL")

    # claim vs billed PN
    billed_share = None
    if len(asm):
        billed_share = round(float((asm["PARTNBR"] == PN_B_BILLED).mean()), 4)

    return {
        "available": True,
        "window_note": "CV claim sheets Dec 2023–Mar 2026 (currency-mixed source; counts/medians only here)",
        "thresholds": {"early_km": 30000, "wear_out_km": 80000},
        "uk_assembly": uk_asm,
        "uk_filter": uk_filt,
        "all_assembly": all_asm,
        "israel_filter_footnote": israel_filt,
        "billed_pn_share_of_asm_claims": billed_share,
        "overlap_filter_and_asm_vins": int(len(set(asm["VIN17"]) & set(filt["VIN17"]))),
    }


def warranty_pn_eur(pn: str) -> float | None:
    total = 0.0
    found = False
    for name in ("warranty_part_turnover.csv", "warranty_cv_part_turnover.csv"):
        p = DER / "warranty_commercial" / name
        if not p.exists():
            continue
        df = pd.read_csv(p, dtype={"part_number": str})
        df["part_number"] = df["part_number"].map(norm_pn)
        hit = df[df["part_number"] == pn]
        if len(hit):
            found = True
            total += float(hit["parts_turnover_eur"].sum())
    return round(total, 2) if found else None


def warranty_pn_detail(pn: str) -> dict:
    """Sum claim € and lines for a PN across LCV + CV commercial extracts."""
    eur = 0.0
    lines = 0
    med_km = None
    bags = []
    for name, bag in (
        ("warranty_part_turnover.csv", "LCV"),
        ("warranty_cv_part_turnover.csv", "CV"),
    ):
        p = DER / "warranty_commercial" / name
        if not p.exists():
            continue
        df = pd.read_csv(p, dtype={"part_number": str})
        df["part_number"] = df["part_number"].map(norm_pn)
        hit = df[df["part_number"] == pn]
        if not len(hit):
            continue
        bags.append(bag)
        eur += float(hit["parts_turnover_eur"].sum())
        if "claim_lines" in hit.columns:
            lines += int(hit["claim_lines"].sum())
        elif "n_lines" in hit.columns:
            lines += int(hit["n_lines"].sum())
        else:
            lines += len(hit)
        if "median_odometer_km" in hit.columns and med_km is None:
            vals = pd.to_numeric(hit["median_odometer_km"], errors="coerce").dropna()
            if len(vals):
                med_km = float(vals.iloc[0])
    return {
        "eur": round(eur, 2) if eur else None,
        "claim_lines": lines or None,
        "median_odometer_km": med_km,
        "bags": bags,
    }


def build_worklist() -> list[dict]:
    rows = []
    for pn in WORKLIST_PNS:
        for mkt in WORKLIST_MARKETS:
            for qt in WORKLIST_QUOTE_TYPES:
                # ITUK × D-Max Euro 6d less relevant; still list for completeness
                rows.append(
                    {
                        "pn": pn,
                        "market": mkt,
                        "quote_type": qt,
                        "status": "TO_COLLECT",
                        "observed_eur": "",
                        "source_url": "",
                        "notes": "",
                    }
                )
    # Named specialists / programme quotes first in CSV mental model
    return list(SPECIALIST_TARGETS) + rows


def _pipe_read(code: str, pcs_yr: float, pcs_1000, early_share) -> str:
    """One-line read — never 'no market' from billed alone."""
    c = (code or "").upper()
    if c == "NETWORK":
        return "Captured commercial book — not market size; fleet density unresolved"
    if c in ("PORTUGAL", "IMOTORS"):
        return "Thin in our book + interest gate — do not read as no market"
    if pcs_1000 is not None and pcs_1000 < 2.0 and pcs_yr < THIN_PCS_YR:
        return "Thin in our book; low pcs/1,000 UIO — under-service, long life, or price-out (unresolved)"
    if pcs_yr >= THIN_PCS_YR:
        return "Captured book supports pooled FR logistics if cleaning+freight clear vs ASP"
    return "Thin in our book — pool only; not a market-size no"


def build_feasibility_economics(
    vol_a: dict,
    vol_b: dict,
    window_years: float,
    list_eur_a: float | None,
    dpd: dict,
    core_a: dict,
    core_b: dict,
    wart_a_detail: dict,
    claim_lists: list[dict],
) -> dict:
    """Multi-pipe feasibility: warranty + billed + fleet density + price. No invented first-DPD %."""
    wy = float(window_years) or 1.0
    asp = vol_a.get("asp")
    injection = float(list_eur_a) if list_eur_a else (float(asp) if asp else None)
    billed_eur = float(vol_a.get("eur") or 0)
    wart_eur = float(wart_a_detail.get("eur") or 0) if wart_a_detail.get("eur") else 0.0
    wart_share_of_billed = round(wart_eur / billed_eur, 4) if billed_eur else None

    # DB matrix lookup for UIO density
    db_by = {r["distributor_code"]: r for r in (dpd.get("db_matrix") or [])}

    hero_core = (core_a.get("hero_pn") or {}) if core_a.get("available") else {}
    early_share = hero_core.get("early_share")
    wear_share = hero_core.get("reman_candidate_share")
    mid_share = None
    if early_share is not None and wear_share is not None:
        mid_share = max(0.0, 1.0 - float(early_share) - float(wear_share))

    focus_codes = ["NETWORK", "UMI", "IUK", "PORTUGAL", "SWEDEN"]
    pipe_rows = []
    markets_billed = []
    for d in vol_a.get("top_dbs") or []:
        qty = float(d.get("qty") or 0)
        eur = float(d.get("eur") or 0)
        pcs_yr = round(qty / wy, 2)
        eur_yr = round(eur / wy, 2)
        markets_billed.append(
            {
                "market": d.get("db"),
                "qty_window": qty,
                "eur_window": round(eur, 2),
                "pcs_yr": pcs_yr,
                "eur_yr": eur_yr,
            }
        )
    total_pcs_yr = sum(m["pcs_yr"] for m in markets_billed) or 1.0
    for m in markets_billed:
        m["share_pcs_yr"] = round(m["pcs_yr"] / total_pcs_yr, 4)

    network_pcs_yr = round(float(vol_a.get("qty") or 0) / wy, 2)
    network_eur_yr = round(float(vol_a.get("eur") or 0) / wy, 2)
    umi_iuk = sum(m["pcs_yr"] for m in markets_billed if (m["market"] or "").upper() in ("UMI", "IUK"))
    pt = next((m for m in markets_billed if (m["market"] or "").upper() in ("PORTUGAL", "IMOTORS")), None)

    for code in focus_codes:
        if code == "NETWORK":
            pcs_yr = network_pcs_yr
            eur_yr = network_eur_yr
            # Network density: not a single UIO — leave null
            pcs_1000 = None
            uio = None
            label = "Network (Track A hero)"
            # Warranty is network-level for hero PN (not split by DB in commercial extract)
            w_eur = wart_a_detail.get("eur")
            w_lines = wart_a_detail.get("claim_lines")
            w_early = early_share
            w_vins = hero_core.get("vins")
            w_med = hero_core.get("median_km")
        else:
            hit = next((m for m in markets_billed if (m["market"] or "").upper() == code), None)
            pcs_yr = hit["pcs_yr"] if hit else 0.0
            eur_yr = hit["eur_yr"] if hit else 0.0
            db = db_by.get(code) or {}
            # Portugal may be labelled IMOTORS in db_matrix
            if not db and code == "PORTUGAL":
                db = db_by.get("IMOTORS") or next(
                    (r for r in db_by.values() if "PORTUGAL" in (r.get("label") or "").upper()),
                    {},
                )
            pcs_1000 = db.get("pcs_per_1000_uio_per_year")
            uio = db.get("uio_used")
            label = code
            # Per-DB warranty split not available honestly — leave blank except network
            w_eur = None
            w_lines = None
            w_early = None
            w_vins = None
            w_med = None
        pipe_rows.append(
            {
                "cut": label,
                "warranty_eur": w_eur,
                "warranty_lines": w_lines,
                "warranty_vins": w_vins,
                "warranty_early_share": w_early,
                "warranty_median_km": w_med,
                "commercial_pcs_yr": pcs_yr,
                "commercial_eur_yr": eur_yr,
                "pcs_per_1000_uio_per_year": pcs_1000,
                "uio_used": uio,
                "read": _pipe_read(code, pcs_yr, pcs_1000, early_share),
            }
        )

    # Mid NG for break-even freight table
    ng_mid = NG_ASSUMPTION_RATES[1]
    break_even_freight = []
    if asp is not None and injection is not None:
        for clean in CLEANING_ASSUMPTION_EUR:
            be = asp - clean - ng_mid * injection
            break_even_freight.append(
                {
                    "cleaning_assumption_eur": clean,
                    "ng_rate_assumption": ng_mid,
                    "injection_eur": round(injection, 2),
                    "break_even_freight_rt_eur": round(be, 2),
                    "clears_at_zero_freight": be >= 0,
                }
            )

    grid = []
    if asp is not None and injection is not None:
        for ng in NG_ASSUMPTION_RATES:
            for clean in CLEANING_ASSUMPTION_EUR:
                for fr in FREIGHT_RT_ASSUMPTION_EUR:
                    landed = clean + fr + ng * injection
                    headroom = asp - landed
                    grid.append(
                        {
                            "cleaning_assumption_eur": clean,
                            "freight_rt_assumption_eur": fr,
                            "ng_rate_assumption": ng,
                            "landed_eur": round(landed, 2),
                            "headroom_vs_asp_eur": round(headroom, 2),
                            "positive": headroom >= 0,
                        }
                    )

    base_clean = CLEANING_ASSUMPTION_EUR[1]
    base_fr = FREIGHT_RT_ASSUMPTION_EUR[1]
    base_ng = NG_ASSUMPTION_RATES[1]
    base_headroom = None
    if asp is not None and injection is not None:
        base_headroom = round(asp - (base_clean + base_fr + base_ng * injection), 2)

    # Track B product split
    filter_eur = sum(float(c.get("warranty_eur") or 0) for c in claim_lists)
    filter_n = len([c for c in claim_lists if c.get("warranty_eur")])
    uk_a = (core_b.get("uk_assembly") or {}) if core_b.get("available") else {}
    uk_f = (core_b.get("uk_filter") or {}) if core_b.get("available") else {}
    billed_share_asm_claims = core_b.get("billed_pn_share_of_asm_claims") if core_b.get("available") else None
    track_b = {
        "pn": vol_b.get("pn"),
        "pcs_yr": round(float(vol_b.get("qty") or 0) / wy, 2),
        "eur_yr": round(float(vol_b.get("eur") or 0) / wy, 2),
        "asp": vol_b.get("asp"),
        "lane": "UK-local — FR transport secondary; stress vs new-in-lieu; FILTER insert ≠ full can",
        "filter_claim_eur": round(filter_eur, 2),
        "filter_claim_pn_count": filter_n,
        "filter_claim_pns": claim_lists,
        "uk_assembly_vins": uk_a.get("vins"),
        "uk_filter_vins": uk_f.get("vins"),
        "uk_assembly_median_km": uk_a.get("median_km"),
        "uk_filter_median_km": uk_f.get("median_km"),
        "billed_pn_share_of_asm_claims": billed_share_asm_claims,
        "top_dbs": [
            {
                "market": d.get("db"),
                "pcs_yr": round(float(d.get("qty") or 0) / wy, 2),
                "eur_yr": round(float(d.get("eur") or 0) / wy, 2),
            }
            for d in (vol_b.get("top_dbs") or [])
        ],
    }

    prose = [
        (
            "Billed pcs are our commercial book only — not market size. "
            "We cannot compute % of first DPD sold in warranty: no non-warranty first-fail denominator exists."
        ),
        (
            f"Track A hero: commercial ~{network_pcs_yr:.0f} pcs/yr · {feur(network_eur_yr)}/yr; "
            f"warranty on same PN {feur(wart_eur)} / {wart_a_detail.get('claim_lines') or '—'} lines "
            f"(~{(wart_share_of_billed or 0)*100:.0f}% of billed € on this PN). "
            f"VIN-first early &lt;30k = {(early_share or 0)*100:.0f}% on N={hero_core.get('vins') or 0} "
            f"(directional only)."
        ),
        (
            f"UMI+IUK hold ~{umi_iuk/network_pcs_yr*100:.0f}% of our Track A pcs/yr. "
            f"Portugal ~{(pt['pcs_yr'] if pt else 0):.1f} pcs/yr in our book — interest gate, not 'no market'."
            if network_pcs_yr
            else "Track A commercial volume missing."
        ),
        (
            "Fleet pcs/1,000 UIO is an unresolved-gap flag (under-service, long can life, or price-out) — "
            "not an IML interval and not capture %."
        ),
        (
            f"Landed-cost ASSUMPTION vs our ASP only: base headroom ~{feur(base_headroom)}/unit "
            f"(cleaning €{base_clean:.0f} + freight €{base_fr:.0f} RT + {base_ng*100:.0f}% NG). "
            "Not a market-size proof — replace with Optymha + freight COLLECT."
            if base_headroom is not None
            else "Cannot compute headroom without ASP."
        ),
        (
            f"Track B: billed full ASM ~{track_b['pcs_yr']:.0f} pcs/yr · {feur(track_b['eur_yr'])}; "
            f"FILTER claim PNs ~{feur(filter_eur)} — insert R&R dwarfs full-can commercial. "
            f"UK VIN assembly {uk_a.get('vins') or 0} vs filter {uk_f.get('vins') or 0}."
        ),
    ]

    return {
        "title": "Demand we can see — three pipes + price",
        "hub": "Optymha / Ceramex (FR) for Track A pool; Track B UK-local",
        "window_years": wy,
        "identity": (
            "landed = cleaning_or_reman + freight_round_trip + (NG_rate × new_unit_injection); "
            "headroom = ASP_to_DB − landed (transfer ASP — not dealer €, not market size)"
        ),
        "caveats": [
            "Billed pcs ≠ market size.",
            "First-DPD warranty % cannot be computed — we only see warranty claims, not every first DPD.",
            "Fleet pcs/1,000 UIO ≠ IML service interval and ≠ capture %.",
            "FILTER ASM claim volume ≠ full-can reman pool.",
            "ASSUMPTION freight bands and high cleaning (€900) are not observed dealer €.",
            "Cleaning mid €660 / low €375 = Diesel-Partner public net (PL truck E6 / E5) — not Optymha, not Isuzu PN.",
        ],
        "labels": {
            "cleaning": "COLLECT (Optymha) — grid mid = Diesel-Partner truck E6 €660 public net",
            "freight": "COLLECT — grid uses ASSUMPTION bands",
            "ng_rate": "ASSUMPTION (Osamu NG risk — not measured)",
            "injection": "list (IE40) or ASP when list missing — Peter: pool charges new when new core injected",
            "asp": "Observed billed ASP to distributors — transfer, not dealer",
        },
        "assumptions": {
            "cleaning_eur": CLEANING_ASSUMPTION_EUR,
            "freight_rt_eur": FREIGHT_RT_ASSUMPTION_EUR,
            "ng_rates": NG_ASSUMPTION_RATES,
            "fixed_hub_admin_eur_yr": FIXED_HUB_ADMIN_ASSUMPTION_EUR,
            "thin_pcs_yr": THIN_PCS_YR,
            "base_cleaning_eur": base_clean,
            "base_freight_rt_eur": base_fr,
            "base_ng_rate": base_ng,
            "cleaning_band_note": (
                "Low €375 = Diesel-Partner truck SCR/CAT Euro 5 public net; "
                "mid €660 = truck DPF Euro 6 public net; high €900 = stress ASSUMPTION until Optymha quote."
            ),
        },
        "warranty_pipe": {
            "pn": vol_a.get("pn"),
            "eur": wart_a_detail.get("eur"),
            "claim_lines": wart_a_detail.get("claim_lines"),
            "share_of_billed_eur": wart_share_of_billed,
            "vins": hero_core.get("vins"),
            "median_km": hero_core.get("median_km"),
            "early_share": early_share,
            "mid_share": mid_share,
            "wear_share": wear_share,
            "note": "First warranty assembly claim per VIN (lowest km) — not share of all first DPDs",
        },
        "observed": {
            "pn": vol_a.get("pn"),
            "asp": asp,
            "list_eur": list_eur_a,
            "injection_eur": round(injection, 2) if injection is not None else None,
            "network_pcs_yr": network_pcs_yr,
            "network_eur_yr": network_eur_yr,
            "umi_iuk_pcs_yr": round(umi_iuk, 2),
            "umi_iuk_share": round(umi_iuk / network_pcs_yr, 4) if network_pcs_yr else 0,
            "portugal_pcs_yr": pt["pcs_yr"] if pt else 0,
            "markets": markets_billed,
        },
        "pipe_rows": pipe_rows,
        "break_even_freight": break_even_freight,
        "sensitivity_grid": grid,
        "base_headroom_eur": base_headroom,
        "track_b": track_b,
        "prose": prose,
    }


def verdict_track_a(vol: dict, stack: list[dict], core: dict, fe: dict | None = None) -> dict:
    list_eur = next((r["eur"] for r in stack if r["rung"].startswith("Our list") and r["eur"]), None)
    asp = vol.get("asp")
    clean = [r for r in stack if "Cleaning" in r["rung"] and r.get("eur")]
    grey = [r for r in stack if "Grey" in r["rung"] and r.get("eur")]
    iam = [r for r in stack if "IAM" in r["rung"] and r.get("eur")]
    hero_core = (core.get("hero_pn") or {}) if core.get("available") else {}
    reman_share = hero_core.get("reman_candidate_share")
    early_share = hero_core.get("early_share")
    wp = (fe or {}).get("warranty_pipe") or {}
    obs = (fe or {}).get("observed") or {}

    go = "CONDITIONAL"
    reasons = []
    reasons.append(
        f"Commercial book is real: {feur(vol['eur'])} / {fnum(vol['qty'])} pcs "
        f"({vol['share_of_asm']*100:.0f}% of network DPD ASM), mainly UMI + IUK — "
        "this is captured sales, not market size."
    )
    if wp.get("eur") is not None:
        reasons.append(
            f"Warranty on same PN: {feur(wp.get('eur'))} / {wp.get('claim_lines') or '—'} lines "
            f"(~{(wp.get('share_of_billed_eur') or 0)*100:.0f}% of billed € on this PN). "
            "That is not % of first DPD in warranty — we have no non-warranty first-fail denominator."
        )
    if reman_share is not None:
        reasons.append(
            f"VIN-first warranty pool: {hero_core.get('vins', 0)} vehicles; "
            f"{reman_share*100:.0f}% at ≥50k km (wear), "
            f"{(early_share or 0)*100:.0f}% early (&lt;30k km). N is small — directional only."
        )
    if obs.get("portugal_pcs_yr") is not None:
        reasons.append(
            f"Portugal ~{obs.get('portugal_pcs_yr')} pcs/yr in our book — interest gate; "
            "do not conclude 'no market' from billed pcs alone. Fleet pcs/1,000 UIO stays unresolved "
            "(under-service, long life, or price-out)."
        )
    if not grey and not iam and not clean:
        reasons.append("Peer ladder on this PN is almost empty — collect OEM / reman / IAM before a go.")
        go = "HOLD — collect prices"
    else:
        reasons.append("Some peer rungs exist on related cans; Euro 6d hero still needs dedicated quotes.")
    reasons.append("Return rate, reman unit cost, and yield % are UNKNOWN — no go without those.")
    reasons.append(
        "Reman only clears if it sits above cleaning and below grey/new. "
        "Cleaning € is COLLECT (Optymha/Ceramex) — ASSUMPTION sensitivity is vs our ASP only, "
        "not a market-size proof. Euro 6d sandwich not yet measured."
    )
    reasons.append(
        "Mail 2026-10-06 (Peter/Osamu): prior vehicle cleaning failed mainly on pricing; "
        "industrial pool charges new-unit price when a new core is injected; "
        "Osamu flags high NG / cracked cores emptying the pool — HOLD stays until Portugal interest "
        "and Ceramex/Optymha quotes land."
    )
    return {"call": go, "reasons": reasons, "list_eur": list_eur, "asp": asp}


def verdict_track_b(vol: dict, stack: list[dict], core: dict, claim_vols: list[dict], fe: dict | None = None) -> dict:
    reasons = []
    go = "CONDITIONAL — stress-test vs new-in-lieu"
    tb = (fe or {}).get("track_b") or {}
    reasons.append(
        f"Billed full-can ASM {PN_B_BILLED}: {feur(vol['eur'])} / {fnum(vol['qty'])} pcs — mostly ITUK. "
        "Thin commercial book; not the FILTER claim market."
    )
    filt = sum(float(c.get("warranty_eur") or 0) for c in claim_vols)
    if filt:
        reasons.append(
            f"FILTER ASM claim PNs total ~{feur(filt)} parts € in the claim book vs "
            f"{feur(vol['eur'])} billed full ASM — insert R&R dwarfs full-can commercial. "
            "Reman of the insert ≠ reman of the full can."
        )
    if core.get("available"):
        share = core.get("billed_pn_share_of_asm_claims")
        if share is not None:
            reasons.append(
                f"On truck assembly claims network-wide, billed PN is only {share*100:.0f}% of lines."
            )
        uk_a = core.get("uk_assembly") or {}
        uk_f = core.get("uk_filter") or {}
        reasons.append(
            f"UK VIN: {uk_a.get('vins', 0)} assembly (median {fnum(uk_a.get('median_km'))} km) vs "
            f"{uk_f.get('vins', 0)} filter R&R (median {fnum(uk_f.get('median_km'))} km)."
        )
        il = core.get("israel_filter_footnote") or {}
        if il.get("vins"):
            reasons.append(
                f"Footnote: Israel filter R&R alone is {il['vins']} VINs — UTI context, not UMI; "
                "different product from full ASM reman."
            )
    reasons.append(
        "ITUK new-in-lieu is the ceiling (dealer € COLLECT). FR transport is secondary for Track B — "
        "stress vs programme price, not Optymha round-trip scale."
    )
    reasons.append("Reman dealer price, return rate, and yield remain UNKNOWN.")
    reasons.append(
        "Mail 2026-10-06: Peter routes vehicle exchange via Optymha/Ceramex and will only proceed "
        "after customer interest; Osamu expects truck vs pickup interval differences and CERAMEX "
        "vs air-blow education — CONDITIONAL stays, now with an explicit interest gate."
    )
    reasons.append(
        "Do not copy Spain/Italy assembly claim geography into an ISZE action list — MIDI context only."
    )
    return {"call": go, "reasons": reasons, "claim_pn_note": claim_vols}


def feasibility_section_html(fe: dict | None) -> str:
    """Shared HTML: three pipes + price (reman page + case study)."""
    if not fe:
        return "<p class='muted'>Feasibility economics missing — rebuild reman payload.</p>"
    obs = fe.get("observed") or {}
    wp = fe.get("warranty_pipe") or {}
    tb = fe.get("track_b") or {}
    caveats = "".join(f"<li>{esc(x)}</li>" for x in fe.get("caveats") or [])
    prose = "".join(f"<li>{esc(x)}</li>" for x in fe.get("prose") or [])

    def pct(x):
        return f"{(x or 0)*100:.0f}%" if x is not None else "—"

    pipe_rows = "".join(
        f"<tr><td><strong>{esc(r['cut'])}</strong></td>"
        f"<td class='num'>{feur(r['warranty_eur']) if r.get('warranty_eur') is not None else '—'}</td>"
        f"<td class='num'>{fnum(r['warranty_lines']) if r.get('warranty_lines') is not None else '—'}</td>"
        f"<td class='num'>{pct(r.get('warranty_early_share'))}</td>"
        f"<td class='num'>{fnum(r['commercial_pcs_yr'],1)}</td>"
        f"<td class='num'>{feur(r['commercial_eur_yr'])}</td>"
        f"<td class='num'>{fnum(r['pcs_per_1000_uio_per_year'],2) if r.get('pcs_per_1000_uio_per_year') is not None else '—'}</td>"
        f"<td class='small'>{esc(r.get('read') or '')}</td></tr>"
        for r in fe.get("pipe_rows") or []
    )

    be_rows = "".join(
        f"<tr><td class='num'>{feur(r['cleaning_assumption_eur'])}</td>"
        f"<td class='num'>{(r['ng_rate_assumption']*100):.0f}%</td>"
        f"<td class='num'>{feur(r['injection_eur'])}</td>"
        f"<td class='num'>{feur(r['break_even_freight_rt_eur'])}</td>"
        f"<td>{'yes' if r.get('clears_at_zero_freight') else 'no'}</td></tr>"
        for r in fe.get("break_even_freight") or []
    )
    ng_mid = (fe.get("assumptions") or {}).get("base_ng_rate", 0.25)
    grid_mid = [g for g in (fe.get("sensitivity_grid") or []) if abs(g["ng_rate_assumption"] - ng_mid) < 1e-9]
    cleans = sorted({g["cleaning_assumption_eur"] for g in grid_mid})
    freights = sorted({g["freight_rt_assumption_eur"] for g in grid_mid})
    by_key = {(g["cleaning_assumption_eur"], g["freight_rt_assumption_eur"]): g for g in grid_mid}
    head_fr = "".join(f"<th class='num'>Freight RT {feur(f)}</th>" for f in freights)
    grid_body = []
    for c in cleans:
        cells = []
        for f in freights:
            g = by_key.get((c, f))
            if not g:
                cells.append("<td class='num'>—</td>")
                continue
            cls = "pos" if g.get("positive") else "neg"
            cells.append(f"<td class='num {cls}'>{feur(g['headroom_vs_asp_eur'])}</td>")
        grid_body.append(f"<tr><td class='num'>{feur(c)}</td>{''.join(cells)}</tr>")

    filt_share = ""
    if tb.get("eur_yr") and tb.get("filter_claim_eur"):
        filt_share = f" · FILTER claim € ~{feur(tb.get('filter_claim_eur'))} vs billed full ASM ~{feur(tb.get('eur_yr'))}/yr"

    return f"""
<section id="sec-feasibility" class="band">
  <h2>{esc(fe.get('title') or 'Demand we can see — three pipes + price')}</h2>
  <p class="muted">Hub: {esc(fe.get('hub') or '')}. {esc(fe.get('identity') or '')}.
  Optymha cleaning € stays <strong>COLLECT</strong>. Grid mid cleaning = Diesel-Partner truck Euro 6
  <strong>€660</strong> public net (PL) — not an Isuzu quote. Freight bands remain <strong>ASSUMPTION</strong>.</p>
  <div class="callout bad">
    <strong>Honest limits</strong>
    <ul>{caveats}</ul>
  </div>
  <div class="callout">
    <ul>{prose}</ul>
  </div>
  <div class="kpis">
    <div class="kpi"><div class="v">{feur(wp.get('eur'))}</div><div class="l">Warranty on hero PN (claims book)</div></div>
    <div class="kpi"><div class="v">{pct(wp.get('early_share'))}</div><div class="l">Early &lt;30k in VIN-first claims (N={fnum(wp.get('vins'))})</div></div>
    <div class="kpi"><div class="v">{fnum(obs.get('network_pcs_yr'),1)}</div><div class="l">Commercial pcs / yr (our book)</div></div>
    <div class="kpi"><div class="v">{feur(obs.get('network_eur_yr'))}</div><div class="l">Commercial € / yr (our book)</div></div>
    <div class="kpi"><div class="v">{pct(wp.get('share_of_billed_eur'))}</div><div class="l">Warranty € as share of billed € on PN</div></div>
    <div class="kpi"><div class="v">{feur(fe.get('base_headroom_eur'))}</div><div class="l">Base headroom / unit vs ASP (ASSUMPTION)</div></div>
  </div>
  <h3>Track A — three pipes by cut</h3>
  <p class="muted">Warranty columns are network-level for the hero PN (commercial extract is not split by DB).
  pcs/1,000 UIO is a gap flag, not capture. Portugal thin in our book ≠ no market.</p>
  <div class="scroll">
  <table>
    <thead><tr>
      <th>Cut</th><th class="num">Warranty €</th><th class="num">Claim lines</th><th class="num">Early %</th>
      <th class="num">Comm. pcs/yr</th><th class="num">Comm. €/yr</th><th class="num">Pcs/1,000 UIO</th><th>Read</th>
    </tr></thead>
    <tbody>{pipe_rows or "<tr><td colspan='8' class='muted'>No rows</td></tr>"}</tbody>
  </table>
  </div>
  <h3>Track B — full can vs FILTER insert</h3>
  <p class="muted">{esc(tb.get('lane') or '')}{filt_share}</p>
  <div class="kpis tiny">
    <div class="kpi"><div class="v">{fnum(tb.get('pcs_yr'),1)}</div><div class="l">Billed full ASM pcs/yr</div></div>
    <div class="kpi"><div class="v">{feur(tb.get('eur_yr'))}</div><div class="l">Billed full ASM €/yr</div></div>
    <div class="kpi"><div class="v">{feur(tb.get('filter_claim_eur'))}</div><div class="l">FILTER claim PNs parts €</div></div>
    <div class="kpi"><div class="v">{fnum(tb.get('uk_assembly_vins'))} / {fnum(tb.get('uk_filter_vins'))}</div><div class="l">UK VIN assembly / filter</div></div>
    <div class="kpi"><div class="v">{pct(tb.get('billed_pn_share_of_asm_claims'))}</div><div class="l">Billed PN share of ASM claim lines</div></div>
  </div>
  <h3>Landed cost vs our ASP only (ASSUMPTION — not market size)</h3>
  <p class="muted">Break-even round-trip freight after ASSUMPTION cleaning + mid NG × injection. Replace with Optymha + freight COLLECT.</p>
  <table>
    <thead><tr><th class="num">Cleaning ASSUMPTION</th><th class="num">NG</th><th class="num">Injection</th><th class="num">Break-even freight RT</th><th>Clears at €0 freight?</th></tr></thead>
    <tbody>{be_rows or "<tr><td colspan='5' class='muted'>Need ASP</td></tr>"}</tbody>
  </table>
  <h3>Sensitivity — headroom €/unit at {(ng_mid*100):.0f}% NG (ASSUMPTION)</h3>
  <p class="muted">Positive = clears vs ASP under that band. Not a price recommendation.</p>
  <div class="scroll">
  <table class="sens">
    <thead><tr><th class="num">Cleaning ↓ \\ Freight →</th>{head_fr}</tr></thead>
    <tbody>{''.join(grid_body) or "<tr><td class='muted'>Need ASP</td></tr>"}</tbody>
  </table>
  </div>
</section>
"""


def render_html(p: dict) -> str:
    a = p["track_a"]
    b = p["track_b"]
    m = p["meta"]
    fe_html = feasibility_section_html(p.get("feasibility_economics"))

    def stack_table(stack):
        body = []
        for r in stack:
            cls = "collect" if r["status"] == "collect" else ""
            body.append(
                f"<tr class='{cls}'><td>{esc(r['rung'])}</td>"
                f"<td class='num'>{feur(r['eur'], 0) if r.get('eur') is not None else 'COLLECT'}</td>"
                f"<td class='small'>{esc(r.get('note') or '')}</td></tr>"
            )
        return (
            "<table><thead><tr><th>Rung</th><th class='num'>€</th><th>Note</th></tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table>"
        )

    def db_table(rows, pns):
        heads = "".join(f"<th class='mono small'>{esc(pn)}</th>" for pn in pns)
        body = []
        for r in rows[:12]:
            cells = "".join(
                f"<td class='num'>{feur(r['by_pn'].get(pn, {}).get('eur')) if r['by_pn'].get(pn, {}).get('eur') else '—'}</td>"
                for pn in pns
            )
            body.append(
                f"<tr><td><strong>{esc(r['label'])}</strong><div class='sub'>{esc(r['distributor_code'])}</div></td>"
                f"<td class='num'>{feur(r['eur'])}</td><td class='num'>{fnum(r['qty'])}</td>{cells}</tr>"
            )
        return (
            f"<table><thead><tr><th>DB</th><th class='num'>€</th><th class='num'>Pcs</th>{heads}</tr></thead>"
            f"<tbody>{''.join(body)}</tbody></table>"
        )

    def core_box(c, title):
        if not c or not c.get("vins"):
            return f"<p class='muted'>{esc(title)}: no VINs in cut.</p>"
        return (
            f"<div class='core'>"
            f"<strong>{esc(c.get('label') or title)}</strong>"
            f"<div class='kpis tiny'>"
            f"<div class='kpi'><div class='v'>{c['vins']}</div><div class='l'>VINs</div></div>"
            f"<div class='kpi'><div class='v'>{fnum(c.get('median_km'))}</div><div class='l'>Median km</div></div>"
            f"<div class='kpi'><div class='v'>{(c.get('reman_candidate_share') or 0)*100:.0f}%</div><div class='l'>Wear-out pool</div></div>"
            f"<div class='kpi'><div class='v'>{(c.get('early_share') or 0)*100:.0f}%</div><div class='l'>Early &lt;30k</div></div>"
            f"</div>"
            f"<p class='sub'>Wear-out = reman-candidate clock. Early fails are poor reman cores. Claims book only — not a fleet rate.</p>"
            f"</div>"
        )

    def verdict_box(v):
        bits = "".join(f"<li>{r}</li>" for r in v["reasons"])
        # reasons may contain &lt; from earlier — already escaped in call sites? use as HTML for early share we used &lt;
        return f"<div class='verdict'><div class='call'>{esc(v['call'])}</div><ul>{bits}</ul></div>"

    wl_rows = "".join(
        f"<tr><td class='mono'>{esc(r['pn'])}</td><td>{esc(r['market'])}</td>"
        f"<td>{esc(r['quote_type'])}</td><td class='amber'>{esc(r['status'])}</td>"
        f"<td class='small'>{esc(r.get('notes') or '')}</td></tr>"
        for r in p["worklist"][:40]
    )

    mb = p.get("mail_brief") or {}
    mail_cards = "".join(
        (
            f"<div class='mail'>"
            f"<div class='who'>{esc(mail['who'])} · {esc(mail['date'])}</div>"
            f"<div class='subj'>{esc(mail['subject'])}</div>"
            f"<p><strong>Ask:</strong> {esc(mail['ask'])}</p>"
            f"<p><strong>Markets / names:</strong> {esc(mail['named_pns_markets'])}</p>"
            + (
                f"<p><strong>€ / £:</strong> {esc(mail['money'])}</p>"
                if mail.get("money")
                else "<p class='muted'>No € / £ in body.</p>"
            )
            + f"<p><strong>Open:</strong> {esc(mail['decision_or_open'])}</p>"
            f"</div>"
        )
        for mail in mb.get("mails") or []
    )
    impact = "".join(f"<li>{esc(x)}</li>" for x in (mb.get("study_impact") or []))

    pt = p.get("portugal_visit") or {}
    pt_qs = "".join(
        f"<li><strong>Q{q['n']}.</strong> {esc(q['ask'])}"
        f"<div class='muted'>{esc(q['why'])}</div></li>"
        for q in (pt.get("questions") or [])
    )
    pt_dont = "".join(f"<li>{esc(x)}</li>" for x in (pt.get("do_not") or []))
    pt_html = ""
    if pt:
        pt_html = f"""
<section class="band" id="sec-portugal">
  <h2>Portugal dealer visit — interest questions</h2>
  <p>{esc(pt.get('purpose') or '')}</p>
  <p class="muted">{esc(pt.get('context_one_liner') or '')}</p>
  <ol>{pt_qs}</ol>
  <div class="callout bad"><strong>Do not</strong><ul>{pt_dont}</ul></div>
  <p class="small"><strong>Report back:</strong> {esc(pt.get('report_back') or '')}</p>
</section>
"""

    dbi = p.get("db_interest") or {}
    db_mkts = "".join(
        f"<li><strong>{esc(mkt['label'])}</strong> ({esc(mkt['code'])}) — {esc(mkt['angle'])}</li>"
        for mkt in (dbi.get("markets") or [])
    )
    db_qs = "".join(f"<li>{esc(q)}</li>" for q in (dbi.get("questions") or []))
    db_html = ""
    if dbi:
        db_html = f"""
<section class="band" id="sec-db-interest">
  <h2>Distributor interest (IUK / UMI / Sweden)</h2>
  <p class="muted">{esc(dbi.get('purpose') or '')}</p>
  <ul>{db_mkts}</ul>
  <h3>Ask</h3>
  <ul>{db_qs}</ul>
</section>
"""

    anchors = p.get("web_anchors") or []
    anchor_rows = "".join(
        (
            f"<tr><td>{esc(a['label'])}</td>"
            f"<td>{esc(a['country'])}</td>"
            f"<td class='num'>"
            + (
                f"{esc(a['currency'])} {a['amount']:,.2f}"
                if a.get("amount") is not None and a.get("currency")
                else esc(a.get("amount_note") or "—")
            )
            + f"</td>"
            f"<td class='small'>{esc(a.get('implication') or '')}</td>"
            f"<td class='small'><a href=\"{esc(a['source_url'])}\" target=\"_blank\" rel=\"noopener\">{esc(a['source_url'][:48])}…</a>"
            f"<div class='muted'>{esc(a.get('caveat') or '')} · observed {esc(a.get('observed_at') or '')}</div></td></tr>"
        )
        for a in anchors
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
body {{ margin:0; font-family:"Segoe UI", system-ui, sans-serif; color:var(--ink); background:var(--paper); }}
header {{ background:var(--navy); color:#f7f4ee; padding:24px 28px; }}
header h1 {{ margin:0 0 8px; font-family:Georgia, serif; font-size:26px; font-weight:600; }}
header .meta {{ color:#c8d0dc; font-size:13px; line-height:1.45; max-width:980px; }}
main {{ padding:20px 28px 64px; max-width:1280px; margin:0 auto; }}
h2 {{ font-family:Georgia, serif; color:var(--navy); margin:28px 0 10px; font-size:22px; }}
h3 {{ color:var(--navy); margin:14px 0 8px; font-size:15px; }}
.grid2 {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; }}
.grid3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; }}
@media (max-width:980px) {{ .grid2, .grid3 {{ grid-template-columns:1fr; }} }}
.card {{ background:#fff; border:1px solid var(--line); padding:14px 16px; }}
.card h2 {{ margin-top:0; font-size:18px; border-bottom:3px solid var(--terra); padding-bottom:6px; }}
.kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(110px,1fr)); gap:8px; margin:10px 0; }}
.kpis.tiny .kpi .v {{ font-size:16px; }}
.kpi {{ background:#f7f4ee; border-left:3px solid var(--terra); padding:8px 10px; }}
.kpi .v {{ font-size:18px; font-weight:700; color:var(--navy); }}
.kpi .l {{ font-size:11px; color:var(--muted); margin-top:2px; }}
table {{ width:100%; border-collapse:collapse; font-size:12px; }}
th, td {{ border-bottom:1px solid var(--line); padding:6px 8px; text-align:left; vertical-align:top; }}
th {{ background:var(--navy); color:#f7f4ee; }}
td.num, th.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
tr.collect td {{ background:#fff8ef; }}
.amber {{ color:var(--amber); font-weight:600; }}
.mono {{ font-family:ui-monospace, Consolas, monospace; font-size:11px; }}
.small, .sub, .muted {{ font-size:11px; color:var(--muted); }}
.callout {{ background:#fff; border:1px solid var(--line); border-left:4px solid var(--amber); padding:12px 14px; margin:12px 0; font-size:14px; line-height:1.45; }}
.callout.bad {{ border-left-color:var(--terra); }}
.verdict {{ background:#15233c; color:#f7f4ee; padding:12px 14px; margin-top:12px; }}
.verdict .call {{ font-family:Georgia, serif; font-size:18px; color:#f0c9b8; margin-bottom:8px; }}
.verdict ul {{ margin:0; padding-left:18px; font-size:13px; line-height:1.4; }}
.verdict li {{ margin:4px 0; }}
.core {{ border:1px dashed var(--line); padding:10px; margin:8px 0; }}
.scroll {{ overflow:auto; max-height:320px; border:1px solid var(--line); }}
.mail {{ background:#fff; border:1px solid var(--line); padding:10px 12px; font-size:13px; line-height:1.4; }}
.mail .who {{ font-weight:700; color:var(--navy); }}
.mail .subj {{ font-size:12px; color:var(--muted); margin:2px 0 8px; }}
.mail p {{ margin:4px 0; }}
.band {{ margin:16px 0 8px; }}
table.sens td.pos {{ background:#e8f2ea; }}
table.sens td.neg {{ background:#fff0e8; color:var(--terra); font-weight:600; }}
footer {{ margin-top:36px; font-size:12px; color:var(--muted); }}
a {{ color:var(--terra); }}
</style>
</head>
<body>
<header>
  <h1>DPD reman feasibility — two tracks</h1>
  <div class="meta">
    Internal. Window {esc(m['window_start'])} → {esc(m['window_end'])}.
    Track A: D-Max Euro 6d ({esc(PN_A)}) for UMI + IUK.
    Track B: ITUK truck assemblies vs claim/filter PNs and new-in-lieu.
    Enriched with Peter / Osamu mail (2026-10-06) and public competitive anchors.
    Not a full-market scrape. Generated {esc(m['as_of'])}.
  </div>
</header>
<main>

<div class="callout bad">
  Reman clears only if it sits <strong>above cleaning</strong> and <strong>below grey / new</strong>
  (and on trucks, beside or under ITUK <strong>new-in-lieu</strong>).
  Return rate, reman unit cost and yield % are <strong>UNKNOWN</strong> until collected.
  Mail confirms prior vehicle cleaning failed on <strong>pricing</strong> and NG cores empty the pool.
</div>

<section class="band">
  <h2>What Peter / Osamu asked</h2>
  <p class="muted">{esc(mb.get('name_note') or '')} {esc(mb.get('coverage_note') or '')}</p>
  <div class="grid3">{mail_cards}</div>
  <div class="callout" style="margin-top:12px">
    <strong>How this moves the study</strong>
    <ul>{impact}</ul>
  </div>
</section>

{pt_html}
{db_html}

<section class="band">
  <h2>Public competitive anchors</h2>
  <p class="muted">Not dealer transactions. Source URL + country + observed date on every row. Prefer COLLECT for live dealer €.</p>
  <div class="scroll">
  <table>
    <thead><tr><th>Anchor</th><th>Country</th><th class="num">Observed</th><th>Implication</th><th>Source</th></tr></thead>
    <tbody>{anchor_rows}</tbody>
  </table>
  </div>
</section>

{fe_html}

<div class="grid2">
  <!-- TRACK A -->
  <section class="card">
    <h2>Track A — D-Max Euro 6d</h2>
    <p class="muted">Hero PN {esc(PN_A)}. Euro 5 {esc(PN_A_REF_CLEAN)} is price reference only (cleaning / IAM on disk).</p>
    <div class="kpis">
      <div class="kpi"><div class="v">{feur(a['volume']['eur'])}</div><div class="l">Billed · {fnum(a['volume']['qty'])} pcs</div></div>
      <div class="kpi"><div class="v">{feur(a['volume']['asp'],0)}</div><div class="l">ASP to DB</div></div>
      <div class="kpi"><div class="v">{a['volume']['share_of_asm']*100:.0f}%</div><div class="l">of network DPD ASM €</div></div>
      <div class="kpi"><div class="v">{feur(a.get('list_eur'))}</div><div class="l">IE40 list</div></div>
    </div>
    <p class="small">{esc(a['volume'].get('emission') or '')} · {esc(', '.join(a['volume'].get('series') or []) or '—')}</p>
    <h3>Who billed it</h3>
    {db_table(a['db_cut'], [PN_A])}
    <h3>Price stack</h3>
    {stack_table(a['stack'])}
    <h3>Euro 5 reference ladder ({esc(PN_A_REF_CLEAN)})</h3>
    <p class="muted">Cleaning / IAM observations live on this older can — use as the floor sandwich, not as Track A volume.</p>
    {stack_table(a['ref_stack'])}
    <h3>Core pool (VIN warranty)</h3>
    {core_box(a['core'].get('hero_pn'), 'Hero PN')}
    {core_box(a['core'].get('all_assembly'), 'All D-Max assembly')}
    <p class="sub">{esc(a['core'].get('window_note') or '')}</p>
    {verdict_box(a['verdict'])}
  </section>

  <!-- TRACK B -->
  <section class="card">
    <h2>Track B — ITUK truck</h2>
    <p class="muted">Billed ASM {esc(PN_B_BILLED)}. Claim-heavy PNs often FILTER ASM — separate product from full can reman.</p>
    <div class="kpis">
      <div class="kpi"><div class="v">{feur(b['volume']['eur'])}</div><div class="l">Billed ASM · {fnum(b['volume']['qty'])} pcs</div></div>
      <div class="kpi"><div class="v">{feur(b['volume']['asp'],0)}</div><div class="l">ASP to DB</div></div>
      <div class="kpi"><div class="v">{feur(b.get('list_eur'))}</div><div class="l">IE40 list (ASM)</div></div>
      <div class="kpi"><div class="v">{(b['core'].get('billed_pn_share_of_asm_claims') or 0)*100:.0f}%</div><div class="l">billed PN share of ASM claims</div></div>
    </div>
    <h3>Who billed the ASM</h3>
    {db_table(b['db_cut'], [PN_B_BILLED])}
    <h3>Claim PN list prices (filter / insert)</h3>
    <table><thead><tr><th>PN</th><th>Desc</th><th class="num">IE40 €</th></tr></thead><tbody>
    {''.join(
      f"<tr><td class='mono'>{esc(c['pn'])}</td><td>{esc(c.get('description') or '')}</td>"
      f"<td class='num'>{feur(c.get('list_eur'))}</td></tr>"
      for c in b['claim_lists']
    )}
    </tbody></table>
    <h3>Price stack — billed ASM</h3>
    {stack_table(b['stack'])}
    <div class="callout">
      <strong>ITUK new-in-lieu (public):</strong> reman was approved but shorter life;
      common filters now offered as <em>brand new priced like reman</em> with failed unit returned.
      Reman dealer € on this page = <span class="amber">COLLECT / UNKNOWN</span> — do not invent one under list.
    </div>
    <h3>Grey reference CV ASM ({esc(PN_B_GREY)})</h3>
    {stack_table(b['grey_stack'])}
    <h3>Core pool (VIN)</h3>
    {core_box(b['core'].get('uk_assembly'), 'UK assembly')}
    {core_box(b['core'].get('uk_filter'), 'UK filter')}
    {core_box(b['core'].get('israel_filter_footnote'), 'Israel filter footnote')}
    <p class="sub">{esc(b['core'].get('window_note') or '')}. MIDI ES/IT assembly claims = context only.</p>
    {verdict_box(b['verdict'])}
  </section>
</div>

<section>
  <h2>Price collection worklist</h2>
  <p class="muted">
    {len(p['worklist'])} rows (named specialists first, then PN × market × quote-type grid).
    First 40 shown. Full CSV beside this file.
  </p>
  <div class="scroll">
  <table>
    <thead><tr><th>PN</th><th>Market</th><th>Quote type</th><th>Status</th><th>Notes</th></tr></thead>
    <tbody>{wl_rows}</tbody>
  </table>
  </div>
</section>

<footer>
  Double-click <code>OPEN_ISZE_DPD_Reman_Feasibility.cmd</code>.
  Worklist: <code>ISZE_DPD_Reman_Price_Collection_Worklist_20261006.csv</code>.
  Mail extract: <code>01_data\\90_INBOX\\DPD_Exchange_mail_extract_20261006.md</code>.
  Companion popularity page remains separate.
</footer>
</main>
<script type="application/json" id="payload">{payload_json}</script>
</body>
</html>
"""


def main() -> None:
    print("loading DPD payload…")
    dpd = json.loads(DPD_PAYLOAD.read_text(encoding="utf-8"))
    window_start = dpd["meta"]["window_start"]
    window_end = dpd["meta"]["window_end"]

    all_pns = list(dict.fromkeys(WORKLIST_PNS))
    print("list prices…")
    lists = load_list_prices(all_pns)
    print("price observations…")
    obs = load_price_obs(all_pns)

    # Track A volume
    vol_a = volume_for_pn(dpd, PN_A)
    db_a = db_cut_for_pns(dpd, [PN_A], focus_dbs=["UMI", "IUK", "SWEDEN", "PORTUGAL", "GERMANY", "BELGIUM"])
    # keep any DB with sales of PN_A
    db_a = db_cut_for_pns(dpd, [PN_A])

    wart_a = warranty_pn_eur(PN_A)
    wart_ref = warranty_pn_eur(PN_A_REF_CLEAN)
    stack_a = stack_for_pn(PN_A, lists, obs, wart_a, vol_a.get("asp"))
    vol_ref = volume_for_pn(dpd, PN_A_REF_CLEAN)
    stack_ref = stack_for_pn(PN_A_REF_CLEAN, lists, obs, wart_ref, vol_ref.get("asp"))

    print("VIN LCV core…")
    core_a = load_lcv_vin_core()

    # Track B
    vol_b = volume_for_pn(dpd, PN_B_BILLED)
    db_b = db_cut_for_pns(dpd, [PN_B_BILLED])
    wart_b = warranty_pn_eur(PN_B_BILLED)
    stack_b = stack_for_pn(PN_B_BILLED, lists, obs, wart_b, vol_b.get("asp"))
    # inject new-in-lieu rung
    stack_b.append(
        {
            "rung": "ITUK new-in-lieu (public programme)",
            "eur": None,
            "note": "Brand new priced like reman + core return — dealer € UNKNOWN / collect from ITUK parts",
            "status": "collect",
        }
    )
    vol_grey = volume_for_pn(dpd, PN_B_GREY)
    stack_grey = stack_for_pn(PN_B_GREY, lists, obs, warranty_pn_eur(PN_B_GREY), vol_grey.get("asp"))

    claim_lists = []
    for pn in PN_B_CLAIM:
        claim_lists.append(
            {
                "pn": pn,
                "description": (lists.get(pn) or {}).get("description") or "FILTER ASM / claim PN",
                "list_eur": (lists.get(pn) or {}).get("list_eur"),
                "warranty_eur": warranty_pn_eur(pn),
            }
        )

    print("VIN CV core…")
    core_b = load_cv_vin_core()

    window_years = float(dpd["meta"].get("window_years") or 2.081)
    list_a = (lists.get(PN_A) or {}).get("list_eur")
    wart_a_detail = warranty_pn_detail(PN_A)
    feasibility = build_feasibility_economics(
        vol_a, vol_b, window_years, list_a, dpd, core_a, core_b, wart_a_detail, claim_lists
    )

    verdict_a = verdict_track_a(vol_a, stack_a, core_a, feasibility)
    verdict_b = verdict_track_b(vol_b, stack_b, core_b, claim_lists, feasibility)

    worklist = build_worklist()
    mail_brief = build_mail_brief()
    web_anchors = build_web_anchors()
    portugal_visit = build_portugal_visit_brief()
    db_interest = build_db_interest_note()

    payload = {
        "meta": {
            "title": "DPD reman feasibility — D-Max Euro 6d + ITUK truck",
            "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "window_start": window_start,
            "window_end": window_end,
            "window_years": window_years,
            "audience": "internal",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": {
                "dpd_payload": str(DPD_PAYLOAD),
                "list": "pricing_pr00_ie40.parquet",
                "peer": "price_observations.parquet",
                "warranty_lcv": "warranty_fy26_raw.csv",
                "warranty_cv": "01_data/06_Warranty/*.xlsx",
                "mail_extract": r"01_data\90_INBOX\DPD_Exchange_mail_extract_20261006.md",
            },
        },
        "mail_brief": mail_brief,
        "portugal_visit": portugal_visit,
        "db_interest": db_interest,
        "web_anchors": web_anchors,
        "feasibility_economics": feasibility,
        "track_a": {
            "volume": vol_a,
            "db_cut": db_a,
            "list_eur": list_a,
            "stack": stack_a,
            "ref_stack": stack_ref,
            "core": core_a,
            "verdict": verdict_a,
        },
        "track_b": {
            "volume": vol_b,
            "db_cut": db_b,
            "list_eur": (lists.get(PN_B_BILLED) or {}).get("list_eur"),
            "stack": stack_b,
            "grey_stack": stack_grey,
            "claim_lists": claim_lists,
            "core": core_b,
            "verdict": verdict_b,
        },
        "worklist": worklist,
        "obs_count": len(obs),
    }

    BUILD.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT_JSON)

    pd.DataFrame(worklist).to_csv(OUT_WORKLIST, index=False, encoding="utf-8")
    print("wrote", OUT_WORKLIST, "rows", len(worklist))

    html = render_html(payload)
    OUT_HTML.write_text(html, encoding="utf-8")
    OUT_CMD.write_text(
        '@echo off\r\nstart "" "%~dp0ISZE_DPD_Reman_Feasibility_20261006.html"\r\n',
        encoding="utf-8",
        newline="",
    )
    print("wrote", OUT_HTML, OUT_HTML.stat().st_size)
    print("A", verdict_a["call"], "B", verdict_b["call"])


if __name__ == "__main__":
    main()
