"""P2a local MAPI collector — deterministic, read-only, zero network egress.

Roadmap: 00_docs/roadmaps/ai_sales_intelligence.md §7.4 (task 2a.2 / 2a.3)
Gate    : G0a — see 00_docs/G0A_LOCAL_MAIL_SCOPE.md. Own mailbox only.

WHAT THIS DOES
    Reads the local Outlook profile over MAPI/COM, keeps only messages that touch a
    distributor domain on the allow-list, and writes DERIVED FIELDS to parquet.

WHAT THIS NEVER DOES
    - never stores a body, a subject, or an attachment
    - never sends, moves, deletes, marks-read or otherwise modifies anything in Outlook
    - never sends anything off this machine: remote TCP connects are blocked at runtime
      (see _forbid_remote_network; localhost stays open because MAPI/COM RPC needs it)
    - never touches the shared 'Sales' / 'Parts' stores (refused; those need G0b)

USAGE
    python collect_mapi.py --since 2024-01-01 --dry-run
    python collect_mapi.py --since 2024-01-01
    python collect_mapi.py --since 2024-01-01 --folders inbox,sent --limit 500

    --folders inbox,sent walks each root AND its subfolders (own store only).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import pyarrow  # noqa: F401  - imported early so the network guard cannot break it
import yaml

ROOT = os.environ.get("ISZE_ROOT", r"C:\Users\jerom\Desktop\claude\ISZE")
OUT_DIR = os.path.join(ROOT, "01_data", "17_interactions")
ALLOWLIST = os.path.join(ROOT, "04_tools", "interactions", "db_domains.yaml")
CATALOGUE = os.path.join(ROOT, "01_data", "00_derived", "parts_catalog_dimension.csv")
SALT_FILE = os.path.join(os.environ.get("LOCALAPPDATA", ""), "ISZE", "interactions_salt.txt")

EXTRACTOR_VERSION = "det-v2"
RETENTION_MONTHS = 24
CHECKPOINT_EVERY = 250

OL_FOLDER = {"inbox": 6, "sent": 5}
OL_MAIL_CLASS = 43
PR_SMTP_ADDRESS = "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"
# Shared stores named in G0a — refuse if they ever appear as the walk root.
REFUSED_STORE_TOKENS = ("sales", "parts")


# --------------------------------------------------------------------------- guards
def _forbid_remote_network() -> None:
    """Block remote TCP egress. Local sockets stay open — Outlook COM/RPC needs them.

    G0a requirement is 'no company text leaves the machine', not 'no localhost IPC'.
    A blanket socket.socket monkeypatch kills MAPI mid-iteration (RPC unavailable).
    """
    import socket

    _real_create_connection = socket.create_connection

    def _guarded_create_connection(address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        host_s = str(host).lower().strip("[]")
        if host_s in {"127.0.0.1", "::1", "localhost"}:
            return _real_create_connection(address, *args, **kwargs)
        raise RuntimeError(
            f"collect_mapi.py is egress-free by design (G0a). "
            f"Blocked remote connect to {host_s!r}."
        )

    socket.create_connection = _guarded_create_connection  # type: ignore[assignment]


# --------------------------------------------------------------------------- helpers
def _salt() -> str:
    """Pseudonymisation salt. Lives outside the repo and is never committed."""
    os.makedirs(os.path.dirname(SALT_FILE), exist_ok=True)
    if not os.path.exists(SALT_FILE):
        with open(SALT_FILE, "w", encoding="utf-8") as fh:
            fh.write(os.urandom(32).hex())
    with open(SALT_FILE, encoding="utf-8") as fh:
        return fh.read().strip()


def _h(value: str, salt: str, length: int = 32) -> str:
    return hashlib.sha256((salt + value.lower()).encode("utf-8")).hexdigest()[:length]


def _safe(getter, default=None):
    try:
        return getter()
    except Exception:
        return default


def _smtp(entry) -> str:
    """Resolve an Exchange DN to a real SMTP address; pass through plain SMTP."""
    if entry is None:
        return ""
    addr = _safe(lambda: entry.Address, "") or ""
    if "@" in addr:
        return addr.lower()
    smtp = _safe(lambda: entry.PropertyAccessor.GetProperty(PR_SMTP_ADDRESS), "") or ""
    if "@" in smtp:
        return smtp.lower()
    smtp = _safe(lambda: entry.AddressEntry.GetExchangeUser().PrimarySmtpAddress, "") or ""
    return smtp.lower() if "@" in smtp else ""


def _sender_smtp(msg) -> str:
    if (_safe(lambda: msg.SenderEmailType, "") or "").upper() == "EX":
        sender = _safe(lambda: msg.Sender)
        if sender is not None:
            smtp = _safe(lambda: sender.GetExchangeUser().PrimarySmtpAddress, "") or ""
            if "@" in smtp:
                return smtp.lower()
            smtp = _safe(lambda: sender.PropertyAccessor.GetProperty(PR_SMTP_ADDRESS), "") or ""
            if "@" in smtp:
                return smtp.lower()
    addr = _safe(lambda: msg.SenderEmailAddress, "") or ""
    return addr.lower() if "@" in addr else ""


def _domain(address: str) -> str:
    return address.rsplit("@", 1)[-1].lower() if "@" in address else ""


# --------------------------------------------------------------------------- extract
TOPIC_LEXICON = {
    "pricing": ["price", "pricing", "prijs", "preis", "discount", "korting", "rabatt",
                "quotation", "quote", "tarif", "price list", "prijslijst"],
    "availability": ["stock", "availability", "backorder", "back order", "lead time",
                     "voorraad", "levertijd", "eta", "out of stock", "shortage"],
    "warranty": ["warranty", "garantie", "claim", "goodwill", "defect"],
    "tender": ["tender", "rfq", "request for quotation", "bid", "aanbesteding"],
    "logistics": ["shipment", "shipping", "delivery", "freight", "transport",
                  "levering", "verzending", "awb", "container", "pallet"],
    "order": ["order", "purchase order", "bestelling", "po number", "confirm order"],
    "payment": ["invoice", "payment", "credit note", "factuur", "betaling", "overdue",
                "rechnung", "remittance"],
    "technical": ["technical", "fault", "diagnos", "torque", "spec", "drawing",
                  "storing", "engine", "chassis"],
    "pms": ["service schedule", "maintenance", "pms", "interval", "onderhoud",
            "service kit", "oil filter", "air filter"],
}

# Explicit promise cues — EN / NL / DE commercial mail (ISZE ↔ DB).
# Keep phrases long-first when matching; short tokens use word-boundary checks.
MODALS = [
    # English
    "we will", "we'll", "i will", "i'll", "we shall", "we can deliver", "we can ship",
    "we ship", "will be shipped", "will be delivered", "will be sent", "will send",
    "we confirm", "i confirm", "we commit", "we promise", "we aim to", "expect to ship",
    "expect to deliver", "planned to ship", "planned delivery", "eta is", "eta:",
    "ready to ship", "ready for collection", "will arrange", "will provide",
    "will share", "will send over", "will come back", "get back to you by",
    "as agreed", "as promised", "by end of", "no later than", "latest by",
    # Dutch
    "wij zullen", "ik zal", "we zullen", "zal worden", "wordt geleverd", "wordt verstuurd",
    "wordt verzonden", "kunnen leveren", "gaan leveren", "leveren we", "sturen we",
    "wij bevestigen", "ik bevestig", "bevestigen wij", "uiterlijk", "ten laatste",
    "zoals afgesproken", "zoals beloofd", "verwacht te", "planning is",
    # German
    "wir werden", "ich werde", "wir liefern", "wir senden", "wir schicken",
    "wird geliefert", "wird versendet", "wir bestätigen", "ich bestätige",
    "spätestens", "bis spätestens", "wie vereinbart", "wie zugesagt",
    "liefertermin", "versandtermin", "wir sichern zu",
]

RE_PN_PLAIN = re.compile(r"(?<!\d)(\d{8,10})(?!\d)")
RE_PN_DASHED = re.compile(r"(?<![\w-])(\d{1,2}-\d{4,6}-\d{2,4}(?:-\d)?)(?![\w-])")
RE_AMOUNT = re.compile(
    r"(?:(?:EUR|GBP|USD|CHF|SEK|NOK|DKK|ILS)\s?|[€£$])\s?\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{1,2})?"
    r"|\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d{1,2})?\s?(?:EUR|GBP|USD|€|£)",
    re.IGNORECASE,
)
# ISO, EU slash/dash, EU dots (14.09.2025), and "14 Sep 2025" / "14 september 2025"
RE_DATE = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}"
    r"|\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
    r"|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|"
    r"januari|februari|maart|mei|juni|juli|augustus|oktober|"
    r"januar|februar|märz|marz|mai|juni|juli|oktober|dezember)"
    r"[a-zäöü]*\s+\d{2,4})\b",
    re.IGNORECASE,
)
# Relative / soft deadlines — resolved against message date when absolute date absent
RE_RELATIVE = re.compile(
    r"\b(?:"
    r"tomorrow|today|next week|this week|end of (?:this )?week|end of (?:the )?month|"
    r"end of (?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*|"
    r"by friday|by monday|by tuesday|by wednesday|by thursday|"
    r"morgen|vandaag|volgende week|deze week|eind van de week|eind van de maand|"
    r"uiterlijk vrijdag|uiterlijk maandag|"
    r"morgen|heute|nächste woche|diese woche|ende der woche|ende des monats|"
    r"spätestens freitag|spätestens montag"
    r")\b",
    re.IGNORECASE,
)


def _normalise_pn(token: str) -> str:
    digits = re.sub(r"\D", "", token)
    return digits.zfill(10) if 0 < len(digits) <= 10 else ""


def extract_part_numbers(text: str, catalogue: set[str]) -> list[str]:
    """Candidates are validated against the catalogue — an unvalidated token is discarded.

    This is the rule that keeps invoice numbers, phone numbers and order references out
    of the part-number column.
    """
    found: set[str] = set()
    for match in RE_PN_PLAIN.findall(text) + RE_PN_DASHED.findall(text):
        pn = _normalise_pn(match)
        if pn and pn in catalogue:
            found.add(pn)
    return sorted(found)


def extract_topics(text: str) -> list[str]:
    low = text.lower()
    return sorted(t for t, words in TOPIC_LEXICON.items() if any(w in low for w in words))


def explicit_commitment(text: str) -> bool:
    return bool(find_commitments(text))


# Commitment typing — first meaningful match wins (specificity order).
# Phrases first; short tokens matched with word boundaries to avoid "order"⊂"border".
COMMITMENT_TYPES = [
    ("price_quote", [
        "price list", "prijslijst", "quotation", "quote", "pricing", "discount",
        "korting", "rabatt", "offer price", "unit price", "net price",
        "price", "prijs", "preis", "tarif", "offerte",
    ]),
    ("stock_confirm", [
        "out of stock", "in stock", "backorder", "back order", "availability",
        "allocate", "reserve", "allocation", "voorraad", "beschikbaar", "lagerbestand",
        "stock", "eta for",
    ]),
    ("delivery", [
        "will be shipped", "will be delivered", "will be sent", "ready to ship",
        "ready for collection", "dispatch", "shipment", "shipping", "freight",
        "collection", "awb", "tracking", "deliver", "delivery", "ship", "send",
        "levering", "leveren", "verzending", "verzend", "versturen", "sturen",
        "lieferung", "liefern", "versand", "versenden", "schicken", "senden",
    ]),
    ("data_delivery", [
        "spreadsheet", "workbook", "excel", "forecast", "figures", "overview",
        "dashboard", "report", "file", "export", "data", "cijfers", "overzicht",
        "bericht", "auswertung",
    ]),
    ("meeting", [
        "teams call", "conference call", "video call", "site visit", "meeting",
        "agenda", "afspraak", "bespreking", "besuch", "termin", "call", "visit",
        "review",
    ]),
    ("order_volume", [
        "purchase order", "bestelling", "bestellen", "order confirmation",
        "po number", "quantity", "volume", "units", "order", "auftrag", "stück",
    ]),
]

_MONTH_ALIASES = {
    "jan": 1, "january": 1, "januari": 1, "januar": 1,
    "feb": 2, "february": 2, "februari": 2, "februar": 2,
    "mar": 3, "march": 3, "maart": 3, "märz": 3, "marz": 3,
    "apr": 4, "april": 4,
    "may": 5, "mei": 5, "mai": 5,
    "jun": 6, "june": 6, "juni": 6,
    "jul": 7, "july": 7, "juli": 7,
    "aug": 8, "august": 8, "augustus": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "oktober": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12, "dezember": 12,
}


def _month_num(token: str) -> int | None:
    t = re.sub(r"[^a-z]", "", token.lower())
    if t in _MONTH_ALIASES:
        return _MONTH_ALIASES[t]
    if len(t) >= 3 and t[:3] in _MONTH_ALIASES:
        return _MONTH_ALIASES[t[:3]]
    # NL/DE stems that don't share English 3-letter codes
    for key, num in _MONTH_ALIASES.items():
        if len(key) >= 4 and t.startswith(key[:4]):
            return num
    return None


def _parse_date(token: str, ref: datetime | None = None):
    """Parse absolute date tokens. Day-first — European correspondence."""
    token = token.strip().lower().replace(",", " ")
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", token):
            return datetime.strptime(token, "%Y-%m-%d").date()
        m = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})", token)
        if m:
            day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if month > 12:  # clearly month-first, swap
                day, month = month, day
            year = year + 2000 if year < 100 else year
            return datetime(year, month, day).date()
        m = re.fullmatch(r"(\d{1,2})\s+([a-zäöü]{3,})\s+(\d{2,4})", token)
        if m:
            mon = _month_num(m.group(2))
            if mon is None:
                return None
            year = int(m.group(3))
            year = year + 2000 if year < 100 else year
            return datetime(year, mon, int(m.group(1))).date()
    except (ValueError, KeyError):
        return None
    return None


def _parse_relative(token: str, ref: datetime | None):
    """Map soft deadlines onto a calendar date using the message timestamp."""
    if ref is None:
        return None
    t = token.strip().lower()
    base = ref.date() if hasattr(ref, "date") else ref
    # weekday helpers
    weekdays = {
        "monday": 0, "maandag": 0, "montag": 0,
        "tuesday": 1, "dinsdag": 1, "dienstag": 1,
        "wednesday": 2, "woensdag": 2, "mittwoch": 2,
        "thursday": 3, "donderdag": 3, "donnerstag": 3,
        "friday": 4, "vrijdag": 4, "freitag": 4,
    }
    if t in {"tomorrow", "morgen"}:
        return base + timedelta(days=1)
    if t in {"today", "vandaag", "heute"}:
        return base
    if "next week" in t or "volgende week" in t or "nächste woche" in t or "nachste woche" in t:
        return base + timedelta(days=7)
    if "this week" in t or "deze week" in t or "diese woche" in t or "end of week" in t or "eind van de week" in t or "ende der woche" in t:
        # upcoming Sunday
        return base + timedelta(days=(6 - base.weekday()) % 7 or 7)
    if "end of the month" in t or "end of month" in t or "eind van de maand" in t or "ende des monats" in t:
        if base.month == 12:
            return base.replace(year=base.year + 1, month=1, day=1) - timedelta(days=1)
        return base.replace(month=base.month + 1, day=1) - timedelta(days=1)
    m = re.search(r"end of ([a-z]+)", t)
    if m:
        mon = _MONTH_ALIASES.get(m.group(1)[:3]) or _MONTH_ALIASES.get(m.group(1))
        if mon:
            year = base.year if mon >= base.month else base.year + 1
            nxt = datetime(year + (1 if mon == 12 else 0), 1 if mon == 12 else mon + 1, 1).date()
            return nxt - timedelta(days=1)
    for name, wd in weekdays.items():
        if name in t:
            delta = (wd - base.weekday()) % 7
            return base + timedelta(days=delta or 7)
    return None


def _has_cue(sentence: str, cue: str) -> bool:
    """Substring for multi-word cues; word-boundary for short single tokens."""
    if " " in cue or len(cue) >= 6:
        return cue in sentence
    return re.search(rf"\b{re.escape(cue)}\b", sentence) is not None


def _type_commitment(sentence: str, nearby: str = "") -> str:
    blob = f"{sentence} {nearby}".strip()
    for name, words in COMMITMENT_TYPES:
        if any(_has_cue(blob, w) for w in words):
            return name
    return "unspecified"


def _split_paragraphs(text: str) -> list[list[str]]:
    """Split into paragraphs, then sentences — keeps nearby-sentence date lookup local."""
    paras = re.split(r"\n\s*\n+", text.lower())
    out: list[list[str]] = []
    for para in paras:
        sents = [s.strip() for s in re.split(r"(?<=[.!?\n])\s+", para) if s.strip()]
        if sents:
            out.append(sents)
    return out


def find_commitments(text: str, ref: datetime | None = None) -> list[dict]:
    """Explicit, dated promises. Deterministic subset only — implicit prose is P2b.

    A commitment needs a modal/cue AND a due date. The date may sit in the same
    sentence or an adjacent sentence in the same paragraph (common in NL/DE mail).
    The sentence itself is NEVER returned or stored — only its sha256.
    """
    low = text.lower()
    if not any(m in low for m in MODALS):
        return []

    out: list[dict] = []
    seen_hash: set[str] = set()

    for sents in _split_paragraphs(low):
        for i, sentence in enumerate(sents):
            if not any(m in sentence for m in MODALS):
                continue

            due = None
            dates = RE_DATE.findall(sentence)
            for t in dates:
                due = _parse_date(t, ref)
                if due is not None:
                    break
            if due is None:
                for t in RE_RELATIVE.findall(sentence):
                    due = _parse_relative(t, ref)
                    if due is not None:
                        break
            # Nearby sentence in same paragraph (prev / next)
            neighbours = []
            if i > 0:
                neighbours.append(sents[i - 1])
            if i + 1 < len(sents):
                neighbours.append(sents[i + 1])
            if due is None:
                for nb in neighbours:
                    for t in RE_DATE.findall(nb):
                        due = _parse_date(t, ref)
                        if due is not None:
                            break
                    if due is not None:
                        break
                    for t in RE_RELATIVE.findall(nb):
                        due = _parse_relative(t, ref)
                        if due is not None:
                            break
                    if due is not None:
                        break
            if due is None:
                continue

            ctype = _type_commitment(sentence, " ".join(neighbours))
            amounts = RE_AMOUNT.findall(sentence) or RE_AMOUNT.findall(" ".join(neighbours))
            digest = hashlib.sha256(sentence.encode("utf-8", "ignore")).hexdigest()
            if digest in seen_hash:
                continue
            seen_hash.add(digest)
            out.append(
                {
                    "commitment_type": ctype,
                    "due_date": due,
                    "has_amount": bool(amounts),
                    "sentence_sha256": digest,
                }
            )
    return out


def _iter_folder_items(items):
    """Index-based walk — more stable than COM enumerator under long Restrict scans."""
    n = int(_safe(lambda: items.Count, 0) or 0)
    for i in range(1, n + 1):
        msg = _safe(lambda i=i: items.Item(i))
        if msg is not None:
            yield msg


def _recipient_list(msg) -> list[tuple[str, int]]:
    out = []
    recipients = _safe(lambda: msg.Recipients)
    if recipients is None:
        return out
    n = int(_safe(lambda: recipients.Count, 0) or 0)
    for i in range(1, n + 1):
        rcp = _safe(lambda i=i: recipients.Item(i))
        if rcp is None:
            continue
        addr = _smtp(rcp)
        if addr:
            out.append((addr, int(_safe(lambda: rcp.Type, 1) or 1)))
    return out


def _checkpoint(rows: list[dict], commitment_rows: list[dict], stats: dict, args, store_name: str) -> None:
    """Flush partial parquet so a mid-run COM death does not lose the scan."""
    if not rows:
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.DataFrame(rows).drop_duplicates(subset="interaction_id")
    assert "subject" not in df.columns and "body" not in df.columns
    df.to_parquet(os.path.join(OUT_DIR, "interaction_fact.parquet"), index=False)
    cdf = pd.DataFrame(commitment_rows)
    if not cdf.empty:
        cdf = cdf.drop_duplicates(subset="commitment_id")
        cdf.to_parquet(os.path.join(OUT_DIR, "commitment_fact.parquet"), index=False)
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "extractor_version": EXTRACTOR_VERSION,
        "gate": "G0a — own mailbox, local only, no egress",
        "store": store_name,
        "folders": args.folders,
        "since": args.since,
        "rows": int(len(df)),
        "commitment_rows": int(len(cdf)),
        "distributors_seen": int(df["db_code"].nunique()),
        "date_range": [str(df["occurred_at"].min()), str(df["occurred_at"].max())],
        "stats": stats,
        "contains_message_content": False,
        "retention_months": RETENTION_MONTHS,
        "partial": True,
    }
    with open(os.path.join(OUT_DIR, "interaction_fact.meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    print(f"  checkpoint {len(df):,} interactions | {len(cdf):,} commitments")


def load_allowlist(path: str) -> tuple[dict[str, str], set[str]]:
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    domain_to_db: dict[str, str] = {}
    for db, cfg in doc.get("distributors", {}).items():
        for dom in cfg.get("domains", []) or []:
            domain_to_db[dom.lower()] = db
    ambiguous = {d.lower() for d in doc.get("ambiguous_domains", []) or []}
    return domain_to_db, ambiguous


def load_catalogue(path: str) -> set[str]:
    if not os.path.exists(path):
        print(f"WARN catalogue missing ({path}); part numbers will not be validated -> none kept")
        return set()
    col = pd.read_csv(path, usecols=["part_number"], dtype=str)["part_number"]
    return set(col.dropna().str.strip().str.zfill(10))


def open_own_store(namespace):
    """Return (inbox_store_name, own_smtp). Refuses anything but the default store."""
    own = ""
    # Prefer Account.SmtpAddress — CurrentUser Exchange DN often has no '@'
    accounts = _safe(lambda: namespace.Accounts)
    if accounts is not None:
        n = int(_safe(lambda: accounts.Count, 0) or 0)
        for i in range(1, n + 1):
            smtp = (_safe(lambda i=i: accounts.Item(i).SmtpAddress, "") or "").lower()
            if "@" in smtp:
                own = smtp
                break
    if not own:
        own = (
            _safe(
                lambda: namespace.CurrentUser.AddressEntry.GetExchangeUser().PrimarySmtpAddress,
                "",
            )
            or _safe(lambda: namespace.CurrentUser.Address, "")
            or ""
        ).lower()
    store_name = _safe(lambda: namespace.GetDefaultFolder(OL_FOLDER["inbox"]).Store.DisplayName, "") or ""
    store_l = store_name.lower()
    if any(tok == store_l or tok in store_l.split() for tok in REFUSED_STORE_TOKENS):
        raise SystemExit(
            f"REFUSED: store '{store_name}' looks like a shared Sales/Parts mailbox.\n"
            "G0a is own-mailbox only — shared stores need G0b."
        )
    if own and store_name and "@" in store_l and own not in store_l:
        raise SystemExit(
            f"REFUSED: default store '{store_name}' does not match current user '{own}'.\n"
            "Shared Sales/Parts mailboxes are out of scope until G0b."
        )
    return store_name, own


def _safe_folder_slug(name: str) -> str:
    slug = re.sub(r"[^\w\-]+", "_", (name or "").strip(), flags=re.UNICODE)
    return slug.strip("_") or "folder"


def _walk_mail_folders(root_folder, root_key: str):
    """Yield (folder_path, folder) for root + all nested Folders. Own-store only."""
    yield root_key, root_folder

    def _recurse(folder, path: str):
        folders = _safe(lambda: folder.Folders)
        if folders is None:
            return
        n = int(_safe(lambda: folders.Count, 0) or 0)
        for i in range(1, n + 1):
            sub = _safe(lambda i=i: folders.Item(i))
            if sub is None:
                continue
            # Never descend into another store / shared mailbox root
            store = (_safe(lambda: sub.Store.DisplayName, "") or "").lower()
            if any(tok == store or tok in store.split() for tok in REFUSED_STORE_TOKENS):
                print(f"  SKIP refused store under {path}: {store}")
                continue
            name = _safe_folder_slug(_safe(lambda: sub.Name, "") or f"sub{i}")
            subpath = f"{path}/{name}"
            yield subpath, sub
            yield from _recurse(sub, subpath)

    yield from _recurse(root_folder, root_key)


_APP = None  # module-level so Outlook is not torn down between windows


def _connect():
    """Dispatch Outlook and keep the reference alive for the life of the process."""
    global _APP
    import win32com.client

    _APP = win32com.client.Dispatch("Outlook.Application")
    return _APP, _APP.GetNamespace("MAPI")


def _list_folder_tree(folder_key: str) -> list[str]:
    """Discover folder paths under Inbox/Sent (for logging / dry inventory)."""
    _, ns = _connect()
    root = ns.GetDefaultFolder(OL_FOLDER[folder_key])
    return [path for path, _f in _walk_mail_folders(root, folder_key)]


def _iter_messages(folder_key: str, since: datetime, until: datetime, chunk_days: int,
                   on_window_end=None):
    """Yield (folder_path, msg) across root + subfolders, date-windowed.

    Recurses Inbox/Sent Folders collections (G0a proceed 2026-08-12). A single
    enumerator held across tens of thousands of items dies with RPC unavailable —
    windowing + re-acquire bounds each pass. Caller de-duplicates on interaction_id.
    """
    # Snapshot paths + EntryIDs once; resolve via GetFolderFromID after reconnect.
    _, ns0 = _connect()
    root0 = ns0.GetDefaultFolder(OL_FOLDER[folder_key])
    tree: list[tuple[str, str]] = []
    for path, folder in _walk_mail_folders(root0, folder_key):
        eid = _safe(lambda: folder.EntryID, "") or ""
        if eid:
            tree.append((path, eid))
        else:
            print(f"  WARN no EntryID for {path} - skipped")
    print(f"  {folder_key}: {len(tree)} folder(s) incl. subfolders -> {', '.join(p for p, _ in tree)}")

    for folder_path, entry_id in tree:
        cur = since
        while cur < until:
            nxt = min(cur + timedelta(days=chunk_days), until)
            clause = (
                f"[ReceivedTime] >= '{cur.strftime('%m/%d/%Y')} 12:00 AM' AND "
                f"[ReceivedTime] < '{nxt.strftime('%m/%d/%Y')} 12:00 AM'"
            )
            for attempt in range(1, 4):
                try:
                    _, ns = _connect()
                    target = _safe(lambda: ns.GetFolderFromID(entry_id))
                    if target is None:
                        print(f"  {folder_path}: GetFolderFromID failed - skip window")
                        break
                    items = target.Items
                    items.Sort("[ReceivedTime]", True)
                    items = items.Restrict(clause)
                    for msg in _iter_folder_items(items):
                        yield folder_path, msg
                    break
                except Exception as exc:
                    print(f"  {folder_path} {cur:%Y-%m-%d} attempt {attempt}/3 failed: {exc}")
                    time.sleep(3)
            else:
                print(f"  {folder_path} {cur:%Y-%m-%d} ABANDONED - window incomplete")
            if on_window_end is not None:
                on_window_end(folder_path, cur, nxt)
            cur = nxt


def collect(args: argparse.Namespace) -> int:
    import win32com.client

    salt = _salt()
    domain_to_db, ambiguous = load_allowlist(ALLOWLIST)
    catalogue = load_catalogue(CATALOGUE)
    print(f"allow-list: {len(domain_to_db)} DB domains | catalogue: {len(catalogue):,} part numbers")

    outlook = win32com.client.Dispatch("Outlook.Application")
    ns = outlook.GetNamespace("MAPI")
    store_name, own_smtp = open_own_store(ns)
    print(f"store: {store_name}  (user {own_smtp or 'unknown'})")

    _forbid_remote_network()

    since = datetime.strptime(args.since, "%Y-%m-%d")
    until = datetime.now() + timedelta(days=1)

    rows: list[dict] = []
    commitment_rows: list[dict] = []
    stats = {
        "seen": 0,
        "not_mail": 0,
        "no_db_match": 0,
        "kept": 0,
        "errors": 0,
        "by_folder": {},
    }
    rpc_died = False

    for folder_name in [f.strip() for f in args.folders.split(",") if f.strip()]:
        if folder_name not in OL_FOLDER:
            print(f"unknown folder '{folder_name}' - skipped")
            continue
        if rpc_died:
            break
        print(f"scanning {folder_name} (+subfolders) ... ({args.chunk_days}-day windows from {args.since})")

        def _window_done(folder_path, w_start, w_end):
            print(
                f"  {folder_path} {w_start:%Y-%m-%d} done | "
                f"kept {stats['kept']:,} / seen {stats['seen']:,}"
            )

        for folder_path, msg in _iter_messages(
            folder_name, since, until, args.chunk_days, _window_done
        ):
            stats["seen"] += 1
            if args.limit and stats["kept"] >= args.limit:
                break
            try:
                if _safe(lambda: msg.Class, 0) != OL_MAIL_CLASS:
                    stats["not_mail"] += 1
                    continue

                sender = _sender_smtp(msg)
                recipients = _recipient_list(msg)

                addresses = [sender] + [a for a, _ in recipients]
                domains = {_domain(a) for a in addresses if a}
                matched = sorted(domains & set(domain_to_db))
                if not matched:
                    stats["no_db_match"] += 1
                    continue

                db_code = domain_to_db[matched[0]]
                subject = _safe(lambda: msg.Subject, "") or ""
                body = _safe(lambda: msg.Body, "") or ""
                text = f"{subject}\n{body}"

                received = _safe(lambda: msg.ReceivedTime) or _safe(lambda: msg.SentOn)
                occurred = pd.Timestamp(str(received)) if received is not None else pd.NaT
                ref_dt = None
                if occurred is not pd.NaT and not pd.isna(occurred):
                    ref_dt = occurred.to_pydatetime().replace(tzinfo=None)

                entry_id = _safe(lambda: msg.EntryID, "") or ""
                internet_id = _safe(
                    lambda: msg.PropertyAccessor.GetProperty(
                        "http://schemas.microsoft.com/mapi/proptag/0x1035001E"
                    ),
                    "",
                ) or ""

                root_key = folder_path.split("/", 1)[0]
                if root_key == "sent":
                    direction = "out"
                elif own_smtp and sender == own_smtp:
                    direction = "out"
                else:
                    direction = "in"

                if direction == "out":
                    cp_domain = ""
                    for addr, _t in recipients:
                        d = _domain(addr)
                        if d in domain_to_db:
                            cp_domain = d
                            break
                    if not cp_domain and matched:
                        cp_domain = matched[0]
                else:
                    cp_domain = _domain(sender) if sender else ""

                interaction_id = _h(internet_id or entry_id, salt)
                commitments = find_commitments(text, ref=ref_dt)
                for seq, c in enumerate(commitments):
                    commitment_rows.append(
                        {
                            "commitment_id": _h(f"{interaction_id}:{seq}", salt),
                            "interaction_id": interaction_id,
                            "thread_id": _safe(lambda: msg.ConversationID, "") or "",
                            "db_code": db_code,
                            "owner_side": "isze" if direction == "out" else "db",
                            "commitment_type": c["commitment_type"],
                            "due_date": c["due_date"],
                            "has_amount": c["has_amount"],
                            "made_at": occurred,
                            "sentence_sha256": c["sentence_sha256"],
                            "extractor_version": EXTRACTOR_VERSION,
                        }
                    )

                rows.append(
                    {
                        "interaction_id": interaction_id,
                        "thread_id": _safe(lambda: msg.ConversationID, "") or "",
                        "occurred_at": occurred,
                        "direction": direction,
                        "folder": folder_path,
                        "db_code": db_code,
                        "db_domains_matched": ",".join(matched),
                        "ambiguous_domain_present": bool(domains & ambiguous),
                        "stakeholder_id": _h(
                            sender if direction == "in" else (recipients[0][0] if recipients else ""),
                            salt,
                        )
                        if (sender if direction == "in" else recipients)
                        else "",
                        "counterparty_domain": cp_domain,
                        "n_to": sum(1 for _, t in recipients if t == 1),
                        "n_cc": sum(1 for _, t in recipients if t == 2),
                        "topics": ",".join(extract_topics(text)),
                        "part_numbers": ",".join(extract_part_numbers(text, catalogue)),
                        "n_part_numbers": len(extract_part_numbers(text, catalogue)),
                        "n_amounts": len(RE_AMOUNT.findall(text)),
                        "n_dates": len(RE_DATE.findall(text)),
                        "explicit_commitment": bool(commitments),
                        "has_attachments": bool(_safe(lambda: msg.Attachments.Count, 0)),
                        "n_attachments": int(_safe(lambda: msg.Attachments.Count, 0) or 0),
                        "subject_len": len(subject),
                        "body_len": len(body),
                        "body_sha256": hashlib.sha256(body.encode("utf-8", "ignore")).hexdigest(),
                        "extractor_version": EXTRACTOR_VERSION,
                        "retention_expires": (
                            (occurred + pd.DateOffset(months=RETENTION_MONTHS)).date()
                            if occurred is not pd.NaT
                            else None
                        ),
                    }
                )
                stats["kept"] += 1
                stats["by_folder"][folder_path] = stats["by_folder"].get(folder_path, 0) + 1
                if stats["kept"] % CHECKPOINT_EVERY == 0:
                    print(f"  kept {stats['kept']:,} (seen {stats['seen']:,})")
                    if not args.dry_run:
                        _checkpoint(rows, commitment_rows, stats, args, store_name)
            except Exception as exc:
                stats["errors"] += 1
                err = str(exc)
                if stats["errors"] <= 5:
                    print(f"  item error: {exc}")
                # Outlook COM died mid-run — keep what we have
                if "RPC server is unavailable" in err or "-2147023174" in err:
                    print("COM/RPC died - writing checkpoint and stopping")
                    if not args.dry_run:
                        _checkpoint(rows, commitment_rows, stats, args, store_name)
                    rpc_died = True
                    break

    print(f"\nseen {stats['seen']:,} | kept {stats['kept']:,} | "
          f"no DB match {stats['no_db_match']:,} | non-mail {stats['not_mail']:,} | "
          f"errors {stats['errors']:,}")
    if stats["by_folder"]:
        print("by folder_path:")
        for path, n in sorted(stats["by_folder"].items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {path}: {n:,}")

    if not rows:
        print("nothing to write")
        return 0

    df = pd.DataFrame(rows).drop_duplicates(subset="interaction_id")
    assert "subject" not in df.columns and "body" not in df.columns, "content leaked into output"

    cdf = pd.DataFrame(commitment_rows)
    if not cdf.empty:
        cdf = cdf.drop_duplicates(subset="commitment_id")

    if args.dry_run:
        print("\nDRY RUN - nothing written. Shape:", df.shape)
        print("by DB:\n", df["db_code"].value_counts().to_string())
        print("by topic:\n", df["topics"].str.split(",").explode().value_counts().head(10).to_string())
        print(f"commitments detected: {len(cdf):,}")
        if not cdf.empty:
            print("by type:\n", cdf["commitment_type"].value_counts().to_string())
            print("by owner:\n", cdf["owner_side"].value_counts().to_string())
        return 0

    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "interaction_fact.parquet")
    df.to_parquet(out, index=False)
    if not cdf.empty:
        cdf.to_parquet(os.path.join(OUT_DIR, "commitment_fact.parquet"), index=False)
    elif os.path.exists(os.path.join(OUT_DIR, "commitment_fact.parquet")):
        # Full re-collect with zero commitments should not leave a stale file
        os.remove(os.path.join(OUT_DIR, "commitment_fact.parquet"))

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "extractor_version": EXTRACTOR_VERSION,
        "gate": "G0a — own mailbox, local only, no egress",
        "store": store_name,
        "folders": args.folders,
        "since": args.since,
        "rows": int(len(df)),
        "commitment_rows": int(len(cdf)),
        "distributors_seen": int(df["db_code"].nunique()),
        "date_range": [str(df["occurred_at"].min()), str(df["occurred_at"].max())],
        "stats": stats,
        "folder_paths": stats["by_folder"],
        "contains_message_content": False,
        "retention_months": RETENTION_MONTHS,
        "partial": bool(rpc_died),
        "rpc_died": bool(rpc_died),
    }
    with open(os.path.join(OUT_DIR, "interaction_fact.meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2, default=str)

    print(f"\nwrote {out}  ({len(df):,} rows, {df['db_code'].nunique()} distributors"
          f", {len(cdf):,} commitments"
          f"{' | PARTIAL (RPC died)' if rpc_died else ''})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", default=(datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d"))
    ap.add_argument("--folders", default="inbox,sent")
    ap.add_argument("--limit", type=int, default=0, help="stop after N kept messages (0 = all)")
    ap.add_argument("--chunk-days", type=int, default=30,
                    help="scan window size; smaller = more resilient to RPC drops")
    ap.add_argument("--dry-run", action="store_true", help="count and summarise, write nothing")
    args = ap.parse_args()

    if sys.platform != "win32":
        print("MAPI collector runs on Windows with classic Outlook only.")
        return 2
    return collect(args)


if __name__ == "__main__":
    raise SystemExit(main())
