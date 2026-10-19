# -*- coding: utf-8 -*-
"""Parse eForms contract-award notices already fetched into 01_data/90_INBOX/tender_result_notices_20261015/raw.
One output row per lot: notice, buyer, lot title, winner(s), tender value, result code, tenders received, framework flag.
A field is filled only when the file states it. Run with python -I."""
import csv, json, re, sys
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\tender_result_notices_20261015")
RAW = BASE / "raw"
FEED = Path(r"C:\Users\jerom\Desktop\claude\ISZE\01_data\14_dashboards\tender_data.json")


def ln(t): return t.rsplit("}", 1)[-1]
def kids(e, name): return [c for c in e if ln(c.tag) == name]
def kid(e, name):
    k = kids(e, name); return k[0] if k else None
def txt(e, *path):
    for p in path:
        e = kid(e, p) if e is not None else None
    return (e.text or "").strip() if e is not None and e.text else ""
def walk(e, name):
    return [x for x in e.iter() if ln(x.tag) == name]


def parse(path: Path) -> dict:
    root = ET.parse(path).getroot()
    out = {"form": ln(root.tag), "notice_id": txt(root, "ID"), "issue": txt(root, "IssueDate")[:10]}
    # organisations by id
    orgs = {}
    for o in walk(root, "Organization"):
        c = kid(o, "Company")
        if c is None: continue
        oid = txt(c, "PartyIdentification", "ID")
        name = txt(c, "PartyName", "Name")
        city = txt(c, "PostalAddress", "CityName")
        country = txt(c, "PostalAddress", "Country", "IdentificationCode")
        orgs[oid] = {"name": name, "city": city, "country": country}
    # buyer
    buyer = ""
    for cp in kids(root, "ContractingParty"):
        oid = txt(cp, "Party", "PartyIdentification", "ID")
        if oid in orgs: buyer = orgs[oid]["name"]; break
    if not buyer and orgs: buyer = next(iter(orgs.values()))["name"]
    out["buyer"] = buyer
    # lots: id -> title
    lots = {}
    for pl in kids(root, "ProcurementProjectLot"):
        lid = txt(pl, "ID")
        lots[lid] = txt(pl, "ProcurementProject", "Name")
    out["project"] = txt(root, "ProcurementProject", "Name")
    # tendering parties: id -> list of tenderer org ids
    tparty = {}
    for tp in walk(root, "TenderingParty"):
        tid = txt(tp, "ID")
        t_ids = [txt(t, "ID") for t in walk(tp, "Tenderer")]
        if t_ids or tid not in tparty:       # references inside LotTender carry only the ID: never overwrite
            tparty[tid] = t_ids
    # lot tenders
    ltend = {}
    for lt in walk(root, "LotTender"):
        tid = txt(lt, "ID")
        amt_e = kid(lt, "LegalMonetaryTotal")
        amt = ""; cur = ""
        if amt_e is not None:
            a = kid(amt_e, "PayableAmount")
            if a is not None: amt = (a.text or "").strip(); cur = a.attrib.get("currencyID", "")
        lotref = ""
        for tl in kids(lt, "TenderLot"):
            lotref = txt(tl, "ID")
        party = txt(lt, "TenderingParty", "ID")
        if party or amt or tid not in ltend:   # the copy inside LotResult carries only the ID: never overwrite
            ltend[tid] = {"amount": amt, "currency": cur, "lot": lotref, "party": party}
    # settled contracts: contract id -> lot tender ids
    contracts = {}
    for sc in walk(root, "SettledContract"):
        cid = txt(sc, "ID")
        contracts[cid] = {"lt": [txt(x, "ID") for x in kids(sc, "LotTender")], "title": txt(sc, "Title"), "date": txt(sc, "IssueDate")[:10]}
    lt2contract = {t: cid for cid, c in contracts.items() for t in c["lt"]}
    # lot results
    rows = []
    for lr in walk(root, "LotResult"):
        lot = txt(lr, "TenderLot", "ID")
        code = txt(lr, "TenderResultCode")
        winners = []
        for lt in kids(lr, "LotTender"):
            t = ltend.get(txt(lt, "ID"), {})
            winners.append(t)
        rec = {"lot": lot, "result_code": code}
        # tenders received
        rec["tenders_received"] = ""
        for st in walk(lr, "ReceivedSubmissionsStatistics"):
            if txt(st, "StatisticsCode") in ("tenders", "t-sme", "") and not rec["tenders_received"]:
                rec["tenders_received"] = txt(st, "StatisticsNumeric")
        names = []; amts = []; cur = ""
        for w in winners:
            for oid in tparty.get(w.get("party", ""), []):
                if oid in orgs: names.append(orgs[oid]["name"])
            if w.get("amount"): amts.append(w["amount"]); cur = w.get("currency") or cur
        rec["winner"] = "; ".join(dict.fromkeys(names))
        rec["winner_country"] = "; ".join(dict.fromkeys(orgs[o]["country"] for w in winners for o in tparty.get(w.get("party", ""), []) if o in orgs))
        rec["value"] = amts[0] if len(amts) == 1 else ("; ".join(amts) if amts else "")
        rec["currency"] = cur
        rec["value_note"] = ""
        try:
            if amts and all(float(a) <= 1 for a in amts):
                rec["value_note"] = "source states 1, a placeholder"; rec["value"] = ""
        except ValueError:
            pass
        rec["lot_title"] = lots.get(lot, "")
        rows.append(rec)
    # notice-level total
    tot = ""
    for nr in walk(root, "NoticeResult"):
        t = kid(nr, "TotalAmount")
        if t is not None and t.text: tot = f'{t.text.strip()} {t.attrib.get("currencyID", "")}'
    out["total_amount"] = tot
    out["lots"] = rows
    out["n_orgs"] = len(orgs)
    return out


def main() -> int:
    feed = json.loads(FEED.read_text(encoding="utf-8"))
    meta = {n["Source Notice ID"]: n for n in feed["notices"]}
    rows, per = [], []
    for f in sorted(RAW.glob("*.xml")):
        src, nid = f.stem.split("_", 1)
        try:
            p = parse(f)
        except Exception as ex:
            per.append({"src": src, "id": nid, "error": f"{type(ex).__name__}: {ex}"}); continue
        m = meta.get(nid, {})
        per.append({"src": src, "id": nid, "form": p["form"], "lots": len(p["lots"]), "with_winner": sum(1 for r in p["lots"] if r["winner"]),
                    "with_value": sum(1 for r in p["lots"] if r["value"]), "total": p["total_amount"]})
        if not p["lots"]:
            rows.append({"src": src, "notice_id": nid, "published": m.get("Published Date", ""), "buyer": p["buyer"] or m.get("Buyer", ""), "title": m.get("Title", ""),
                         "notice_type": m.get("Notice Type", ""), "lot": "", "lot_title": "", "result_code": "", "winner": "", "winner_country": "", "value": "", "currency": "",
                         "tenders_received": "", "notice_total": p["total_amount"], "url": m.get("URL", "")})
        for r in p["lots"]:
            rows.append({"src": src, "notice_id": nid, "published": m.get("Published Date", ""), "buyer": p["buyer"] or m.get("Buyer", ""), "title": m.get("Title", ""),
                         "notice_type": m.get("Notice Type", ""), **r, "notice_total": p["total_amount"], "url": m.get("URL", "")})
    SERVICE = re.compile(r"instandsetz|reparatur|wartung|service|inspektion|vedlikehold|reparasjon|drift av|rahmenvertrag.*(instand|wart)", re.I)
    SUPPLY = re.compile(r"lieferung|kauf|beschaff|anschaff|fahrzeug|fahrgestell|anskaff|kj[oø]p|lastebil|skapbil|bil\b", re.I)
    for r in rows:
        s = " ".join([str(r.get("title", "")), str(r.get("lot_title", ""))])
        r["kind"] = "repair or service" if SERVICE.search(s) else ("vehicle or equipment supply" if SUPPLY.search(s) else "other")
    cols = ["src", "notice_id", "published", "buyer", "title", "notice_type", "lot", "lot_title", "result_code", "winner", "winner_country", "value", "value_note", "currency", "tenders_received", "notice_total", "kind", "url"]
    out = BASE / "tender_result_notices_parsed.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
        for r in rows: w.writerow({c: r.get(c, "") for c in cols})
    (BASE / "parse_summary.json").write_text(json.dumps(per, ensure_ascii=False, indent=1), encoding="utf-8")
    print("notices parsed", len(per), "rows", len(rows), "errors", sum(1 for p in per if "error" in p))
    print("notices with >=1 winner", sum(1 for p in per if p.get("with_winner")), "with >=1 value", sum(1 for p in per if p.get("with_value")))
    from collections import Counter
    print(Counter(p.get("form") for p in per))
    print("rows with winner", sum(1 for r in rows if r["winner"]), "with value", sum(1 for r in rows if r["value"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
