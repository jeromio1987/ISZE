"""Curated open issues for ITUK, GERMANY (ISD), PORTUGAL (Imotors).

internal only in this file’s comments. open_lead is shared: distributor · country.
Never sold-to, never person names, never “not UMI / not Motolusa / not Ireland”.
"""
from __future__ import annotations


def face_open_lead(display_name: str, country: str) -> str:
    bits = [str(x).strip() for x in (display_name or "", country or "") if str(x).strip()]
    return " · ".join(bits)


def _r(item, owner, asked_by, date, source, lane="mail"):
    return {
        "item": item,
        "owner": owner,
        "asked_by": asked_by,
        "date": date,
        "status": "open",
        "source": source,
        "lane": lane,
    }


def ituk_open_items():
    src_mail = "Outlook mail (ITUK 2575 · isuzutruck.co.uk)"
    src_pms = "Outlook · Duncan Young PMS / IML Japan week"
    src_wrap = "Outlook · Duncan wrap-up 24 Apr 2026"
    src_mar = "Outlook · Duncan PMS data 17 Mar 2026"
    return {
        "F_emails": {
            "available": True,
            "title": "Open issues from mail",
            "open_lead": "Isuzu Truck UK · United Kingdom",
            "source_note": "Open items from mail",
            "rows": [
                _r(
                    "13 Aug: Duncan sent IML meeting packs (iFORS, MDI, lubrication, PMS) and flew to Japan. Jerome to send a draft of how ISZE proceeds (SPA on genuine lines with low PMS %, Best Value where a catalogue alternative exists, or a simple N75 filter pack on existing workshop events). Duncan will review the draft in Japan.",
                    "ISZE (Jerome) then Duncan Young",
                    "Duncan Young",
                    "2026-08-13",
                    src_mail,
                ),
                _r(
                    "Duncan confirmed he is happy with that direction. Draft still to send before the Tuesday IML slot (18 or 19 Aug). This screen does not propose an ISZE price.",
                    "ISZE (Jerome)",
                    "Duncan Young",
                    "2026-08-13",
                    src_mail,
                ),
                _r(
                    "James Marsh: fill the PMS SPA template and share ITUK sales price (and price-to-customer if possible). Asked 17 Jun, chased 23 Jun.",
                    "ITUK (James Marsh)",
                    "Jerome Van Der Pluym",
                    "2026-06-23",
                    src_mail,
                ),
                _r(
                    "Cab enquiry VIN JAANMR88HM7100136: IML said part numbers were not yet set up (expected around August). Keep ITUK posted once numbers exist. Old price can stay in the system.",
                    "ISZE (Jerome) / IML",
                    "Andy West / Duncan Young",
                    "2026-07-22",
                    src_mail,
                ),
                _r(
                    "Charlotte Marston sent July SPI & KPI to Tomoe (6 Aug). Confirm the series is the ITUK operating feed we need, not only the awards pack.",
                    "ISZE",
                    "Charlotte Marston",
                    "2026-08-06",
                    src_mail,
                ),
                _r(
                    "P700 unpriced parts: James Marsh sent the predicted fast-movers list (29 Jul, chasing since 2 Jun) and needs IML base costs. This screen does not propose an ISZE cut.",
                    "ISZE (Jerome) / IML",
                    "James Marsh",
                    "2026-07-29",
                    src_mail,
                ),
                _r(
                    "3+9 BP revision: Duncan sent the parts sales-out-to-dealers plan (9 Jul). Masumi: incentive-trip idea is OK with Nobby if it lifts genuine-share sales and targets are set at the right level. Hadi also asked for the 3+9 sales-to-dealer BP for FY27–28.",
                    "ITUK (Duncan) · ISZE (Hadi / Masumi)",
                    "Hadewijch Tibos / Duncan Young",
                    "2026-07-10",
                    src_mail,
                ),
            ],
        },
        "G_minutes": {
            "available": True,
            "title": "IML / ITUK follow-ups (no named minutes folder)",
            "body": "Follow-ups from the 22 July note and the IML service-schedule slot.",
            "searched": [
                "Local Outlook COM across Sales, Parts, and Jerome mailbox (2521 hits classified; ITUK 1897)",
                "Named Outlook folder archive/customers/ITUK — 0 items",
                "Inbox/Sent Restrict on Duncan Young, Charlotte Marston, James Marsh, Tim Hicks, Stuart Beeton",
                "DASL subject ITUK + to/cc isuzutruck.co.uk",
                "09_meetings IML_ITUK_PMS outlook extracts and 01_data/90_INBOX",
            ],
            "rows": [
                _r(
                    "22 Jul meeting minutes (Bart to Duncan Young and James Marsh, attachment 260722_ITUK.docx). Named folder still empty — file was in Inbox. Ask Duncan/James if anything is still open from that note.",
                    "ITUK (Duncan / James) · ISZE (Bart)",
                    "Bart Symons",
                    "2026-07-22",
                    "Outlook · Bart minutes 22 Jul 2026",
                    "minutes",
                ),
                _r(
                    "PMS promotion meeting with IML while Duncan is in Japan: slot 18 or 19 August. Align SPA vs Best Value vs a narrow N75 filter pack. Duncan asked for the draft in Japan.",
                    "ISZE (Jerome) · ITUK (Duncan)",
                    "Takayoshi Suzuki / Duncan Young",
                    "2026-08-13",
                    src_pms,
                    "minutes",
                ),
                _r(
                    "VIN / production model year / transmission (MT vs AT) still not available in the format IML asked. Duncan sent UIO + CBU master from 2021 instead (17 Mar). Clutch cover stays provisional until a manual-only parc exists.",
                    "ITUK (Duncan)",
                    "IML / ISZE",
                    "2026-03-17",
                    src_mar,
                    "minutes",
                ),
                _r(
                    "24 Apr wrap-up still on file: Duncan’s notes on the Target Study, attrition, stretch, and scepticism on Isuzu IX 76% growth. That pack is the operating model until Tuesday replaces it.",
                    "ISZE · ITUK",
                    "Duncan Young",
                    "2026-04-24",
                    src_wrap,
                    "minutes",
                ),
                _r(
                    "ITUK interval deviations vs official Isuzu standards: Jerome asked Suzuki (15 Jun) for where ITUK differs. Needed before PMS % is argued in the IML room.",
                    "IML (Suzuki) · ISZE",
                    "Jerome Van Der Pluym",
                    "2026-06-15",
                    src_pms,
                    "minutes",
                ),
            ],
        },
    }


def germany_open_items():
    src_mail = "Outlook mail (ISD / Isuzu Sales Deutschland · sold-to 2516+601)"
    src_mins = "Minutes ISZE–ISD 5 Aug 2026 (Koen / Sebastian Müller)"
    src_awd = "Outlook · Aftersales Awards / Tomoe · Sebastian Müller"
    return {
        "F_emails": {
            "available": True,
            "title": "Open issues from mail",
            "open_lead": "Isuzu Sales Deutschland · Germany",
            "source_note": "Open items from mail",
            "rows": [
                _r(
                    "Aftersales Awards 2026: ISD survey submitted via STELLAR after a deadline extension (new close 6 Aug 15:00 JST; 50% incentive cut if a Star is awarded). Evaluation is with the awards office — confirm whether ISZE still needs anything else from Sebastian.",
                    "ISZE / Awards office",
                    "Sebastian Müller / Tomoe Baumann",
                    "2026-08-06",
                    src_awd,
                ),
                _r(
                    "12 Aug: Fabian Thiel (cc Sebastian, teile@isuzu-sales.de) on orders after the system-down check. Jerome replied thanks. Confirm nothing is still missing from that EDI/order day.",
                    "ISD (Fabian / Sebastian)",
                    "Fabian Thiel",
                    "2026-08-12",
                    src_mail,
                ),
                _r(
                    "KPI / SPI Apr–Aug: minutes say ISD sends by end of August, then monthly. Tomoe already has a Jan–July ISD check-sheet mail (3 Aug). Confirm the remaining months land by end August.",
                    "ISD (Sebastian)",
                    "Koen Matheussen",
                    "2026-08-05",
                    src_mail,
                ),
                _r(
                    "11 Aug: Jerome asked ISD for sales-to-dealer data (same ask as Portugal that day). Sebastian’s mailbox sent an automatic reply — no StD file on the registry yet.",
                    "ISD (Sebastian)",
                    "Jerome Van Der Pluym",
                    "2026-08-11",
                    src_mail,
                ),
            ],
        },
        "G_minutes": {
            "available": True,
            "title": "ISD business review 5 Aug 2026",
            "body": "Business review 5 August 2026.",
            "searched": [
                "Local Outlook COM across Sales, Parts, and Jerome mailbox (2521 hits classified; ISD/Germany 332)",
                "Named Outlook folder archive/customers/ISD — 0 items",
                "Inbox/Sent Restrict on Sebastian Müller, Thomas Spenlein, Björn Groß, Tomoe Baumann",
                "DASL subject ISD",
                "09_meetings/ISD_Sales_Review_2026 and 05_memory brief Koen 5–6 Aug",
            ],
            "rows": [
                _r(
                    "FY27 sales-to-dealer proposal about €6.52M is pending Sebastian’s UIO refresh (fleet −2.1% / maybe −3%, +5% price, +1.8% natural). ISZJ uses calendar-year targets — not locked.",
                    "ISD (Sebastian Müller)",
                    "Koen Matheussen",
                    "2026-08-05",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "Genuine capture presented about 65.9% on an ISZJ method that focuses the ≤5-year fleet. Sebastian to share the methodology so ISZE can compare with the GPS spine on this dashboard.",
                    "ISD (Sebastian Müller)",
                    "Koen Matheussen",
                    "2026-08-05",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "SPA: now needs management approval. Koen sends the template; Sebastian lists high-potential part numbers, target prices and quantities. This screen does not propose an ISZE cut.",
                    "ISD (Sebastian) then ISZE",
                    "Koen Matheussen",
                    "2026-08-05",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "Sales-to-dealer: reliable from May 2025 (part number, quantity, date), then monthly. Not on the dealer-sales registry as a filed series.",
                    "ISD (Sebastian)",
                    "Koen Matheussen",
                    "2026-08-05",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "Brakes −€29K with a genuine→Best Value shift; IAM rotor about €80 vs Isuzu about €100. Sebastian to Fabian on order timing and stock. Recalc fuel-filter and brake-pad coverage on a rolling 12 months (fuel-filter IAM about €5.90 accepted as a loss driver).",
                    "ISD (Sebastian / Fabian) · ISZE (Koen)",
                    "Sebastian Müller",
                    "2026-08-05",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "Org: Thomas Spenlein retiring → Björn Groß. Accessories hit by Astara drop-ship loss; stock about €1.5M. Parts target about €4.33M on the 5-year parc.",
                    "ISD",
                    "Sebastian Müller",
                    "2026-08-05",
                    src_mins,
                    "minutes",
                ),
            ],
        },
    }


def portugal_open_items():
    src_mail = "Outlook mail (I-Motors / Astara Portugal · sold-to 519+92)"
    src_mins = "Minutes ISZE–Astara Portugal 29 Jul 2026"
    return {
        "F_emails": {
            "available": True,
            "title": "Open issues from mail",
            "open_lead": "I-Motors · Portugal",
            "source_note": "Open items from mail",
            "rows": [
                _r(
                    "11 Aug: Nuno replied on sales-to-dealer data. Thread also 30 Jul and 2 Jul (June figure). Astara agreed in principle on 29 Jul once extraction is confirmed — the monthly invoice-date / part / qty feed is still the #1 ask. Not on the dealer-sales registry.",
                    "Astara Portugal (Nuno) + ISZE (Jerome)",
                    "Nuno Machado",
                    "2026-08-11",
                    src_mail,
                ),
                _r(
                    "4 Aug: Nuno sent completed SPI & KPI to Tomoe. Confirm this is the Portugal operating series, not only the awards pack.",
                    "ISZE",
                    "Nuno Machado",
                    "2026-08-04",
                    src_mail,
                ),
                _r(
                    "Formal minutes of the 29 Jul meeting: Jerome still to issue (action 16, in progress).",
                    "ISZE (Jerome)",
                    "29 Jul minutes",
                    "2026-07-29",
                    src_mail,
                ),
                _r(
                    "20 Jul overstock campaign sheet sent to Nuno (about 2.5 months). Nuno will analyse on their volumes and come back. Separate from SPA — do not treat as a proposed ISZE list price.",
                    "Astara Portugal (Nuno)",
                    "Jerome Van Der Pluym",
                    "2026-07-20",
                    src_mail,
                ),
            ],
        },
        "G_minutes": {
            "available": True,
            "title": "ISZE / Astara Portugal 29 Jul 2026",
            "body": "Review 29 July 2026.",
            "searched": [
                "Local Outlook COM across Sales, Parts, and Jerome mailbox (2521 hits classified; Portugal/Imotors 292)",
                "Named Outlook folder archive/customers/portugal — 0 items",
                "Inbox/Sent Restrict on Nuno Machado",
                "DASL subject Imotors / Portugal",
                "09_meetings/PORTUGAL_Sales_Review_2026 minutes",
            ],
            "rows": [
                _r(
                    "25 Jun conference minutes (Imotors 25062026.docx) sent 2 Jul to Luís and Nuno. Named folder empty — file was in Inbox. Training date was added on the note. Anything still open there should be read against the later 29 Jul list, not copied from UMI.",
                    "Astara Portugal (Nuno / Luís) · ISZE",
                    "Koen Matheussen / Bart Symons",
                    "2026-07-02",
                    "Outlook · Imotors conference minutes 25 Jun 2026",
                    "minutes",
                ),
                _r(
                    "Clutch sales: check kits vs individual parts and comment on the about 20% drop.",
                    "Nuno Machado (Astara)",
                    "29 Jul minutes",
                    "2026-07-29",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "Share the completed dealer-standards tool, heat map, dealer fiches once finalised. New dealer this quarter stays out of the current pack — next cycle.",
                    "ISZE (Jerome)",
                    "29 Jul minutes",
                    "2026-07-29",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "Propose dates for combined Astara–ISZE dealer visits, mid-September to mid-October 2026 (avoid last week of October).",
                    "ISZE (Jerome) + Nuno Machado",
                    "29 Jul minutes",
                    "2026-07-29",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "Aftersales hours questionnaire — due 31 July. Confirm received.",
                    "Nuno Machado (Astara)",
                    "29 Jul minutes",
                    "2026-07-29",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "Send detailed figures for the extended parts target (UIO / genuine-share stretch) and revisit the genuine-share stretch after Astara feedback. Second incentive pending Japan, expected around end August.",
                    "ISZE (Jerome)",
                    "Nuno Machado",
                    "2026-07-29",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "SPA: Astara prepares part proposals (volume where a better price can raise sales). Contact Jerome. This screen does not propose an ISZE cut.",
                    "Astara (Nuno / parts) then ISZE",
                    "29 Jul minutes",
                    "2026-07-29",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "R&M: Nuno emails main Allianz issues so ISZE can escalate; Bart shares Real Garant contact; flag sizeable tenders where parts pricing matters.",
                    "Nuno Machado · Bart Symons",
                    "29 Jul minutes",
                    "2026-07-29",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "EDI: Bart checks with ISZE IT (Jimmy) what Astara already uses vs full potential; Astara emails exact IT / parts-data requirements (PN ↔ N/F-series, maintenance vs extended, superseded).",
                    "Bart Symons · Astara",
                    "29 Jul minutes",
                    "2026-07-29",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "BCS / radar brackets: N-series adjustable exists; F-series fixed brackets need follow-up. Share part numbers / stock; check an adjustable F-series option.",
                    "Bart Symons + Jerome + technical",
                    "29 Jul minutes",
                    "2026-07-29",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "Obsolete / high scrap-risk stock: Astara sends PN + qty for a manual cross-distributor match. ISZE will not repurchase as a central buyer.",
                    "Nuno Machado (Astara)",
                    "29 Jul minutes",
                    "2026-07-29",
                    src_mins,
                    "minutes",
                ),
            ],
        },
    }


def greece_open_items():
    src_mins = "Business review 6 Aug 2026"
    return {
        "F_emails": {
            "available": True,
            "title": "Next actions",
            "open_lead": "Petros Petropoulos · Greece",
            "source_note": "Business review 6 August 2026",
            "rows": [
                _r(
                    "Monthly sales-to-dealer from January 2025: invoice date, part number, quantity.",
                    "Distributor",
                    "ISZE",
                    "2026-08-06",
                    src_mins,
                ),
                _r(
                    "Resume KPI / SPI reporting (SPI is now inside the KPI file).",
                    "Distributor",
                    "ISZE",
                    "2026-08-06",
                    src_mins,
                ),
                _r(
                    "FY27 draft about +11.9%. Confirm the +5.1% parc assumption and mileage with the sales department before the target is locked.",
                    "Distributor sales",
                    "Distributor",
                    "2026-08-06",
                    src_mins,
                ),
                _r(
                    "Special prices on strategic part numbers for the older fleet — management approval, ISZE template.",
                    "Distributor / ISZE",
                    "Distributor",
                    "2026-08-06",
                    src_mins,
                ),
                _r(
                    "EDI folder to be opened with ISZE logistics.",
                    "ISZE",
                    "Distributor",
                    "2026-08-06",
                    src_mins,
                ),
            ],
        },
        "G_minutes": {
            "available": True,
            "title": "Review follow-ups",
            "body": "April–July sales recovered after a weak first quarter. Brakes were down because a warranty and technical case closed. Dealer visits start with the lower IDS scores.",
            "searched": [],
            "rows": [
                _r(
                    "IDS visits: start with the dealers on the hit list.",
                    "Distributor",
                    "Distributor",
                    "2026-08-06",
                    src_mins,
                    "minutes",
                ),
                _r(
                    "Repair and maintenance: follow up the Real Garand meeting with the service manager.",
                    "Distributor",
                    "ISZE",
                    "2026-08-06",
                    src_mins,
                    "minutes",
                ),
            ],
        },
    }


def open_items_for(db: str):
    if db == "ITUK":
        return ituk_open_items()
    if db == "GERMANY":
        return germany_open_items()
    if db == "PORTUGAL":
        return portugal_open_items()
    if db == "GREECE":
        return greece_open_items()
    return None
