"""Compare billed lines with sales to dealer, warranty kept on its own line.

The caller passes the tables. This module does not read a billing file, post
a credit, or score company performance.

Sums use Decimal, then round to cents (half up). Order type text is kept as
given: PRD stays PRD, and any other text stays its own bucket.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")
READING = "stock, not lost sales"
NOTE_NO_EURO = "sales-to-dealer line had no euro amount"
NOTE_WARRANTY_UNKNOWN = "warranty split unknown, stock not computed"


def compare(
    billed_lines,
    sales_to_dealer_lines,
    warranty_lines,
    tolerance=None,
) -> dict:
    """Reconcile one pair of tables per distributor and month.

    stock_eur = billed_eur_total - warranty_eur - sales_to_dealer_eur.
    That remainder is stock movement. It is not lost sales.

    warranty_lines None means the split is unknown: warranty_eur and stock_eur
    are null, and stock is not guessed from stock orders. tolerance None does
    not pass or fail the gap. A number passes when abs(stock_eur) <= tolerance.
    """
    warranty_unknown = warranty_lines is None
    billed_seq = billed_lines or []
    std_seq = sales_to_dealer_lines or []
    warranty_seq = [] if warranty_unknown else warranty_lines

    billed_exact: dict[tuple, dict] = {}
    std_exact: dict[tuple, Decimal] = {}
    warranty_exact: dict[tuple, Decimal] = {}
    notes_for: dict[tuple, list[str]] = {}
    gap_notes: list[str] = []

    def ensure(key: tuple) -> None:
        if key not in billed_exact:
            billed_exact[key] = {}
            std_exact[key] = Decimal(0)
            warranty_exact[key] = Decimal(0)
            notes_for[key] = []

    for line in billed_seq:
        key = _key(line)
        if key is None or not _has_euros(line):
            continue
        ensure(key)
        order_type = line.get("order_type")
        bucket = "" if order_type is None else order_type
        buckets = billed_exact[key]
        buckets[bucket] = buckets.get(bucket, Decimal(0)) + _decimal(line["euros"])

    for line in std_seq:
        if not _has_euros(line):
            gap_notes.append(NOTE_NO_EURO)
            key = _key(line)
            if key is not None:
                ensure(key)
                notes_for[key].append(NOTE_NO_EURO)
            continue
        key = _key(line)
        if key is None:
            continue
        ensure(key)
        std_exact[key] = std_exact[key] + _decimal(line["euros"])

    if not warranty_unknown:
        for line in warranty_seq:
            key = _key(line)
            if key is None or not _has_euros(line):
                continue
            ensure(key)
            warranty_exact[key] = warranty_exact[key] + _decimal(line["euros"])

    rows = []
    for key in sorted(billed_exact, key=lambda item: (str(item[0]), str(item[1]))):
        distributor_id, period = key
        raw_buckets = billed_exact[key]
        billed_eur = {
            order_type: _cents(amount)
            for order_type, amount in sorted(raw_buckets.items(), key=lambda item: str(item[0]))
        }
        billed_eur_total = _cents(sum(raw_buckets.values(), Decimal(0)))
        sales_to_dealer_eur = _cents(std_exact[key])
        row_notes = list(notes_for[key])
        if warranty_unknown:
            warranty_eur = None
            stock_eur = None
            row_notes.append(NOTE_WARRANTY_UNKNOWN)
        else:
            warranty_eur = _cents(warranty_exact[key])
            stock_eur = _cents(billed_eur_total - warranty_eur - sales_to_dealer_eur)
        rows.append(
            {
                "distributor_id": distributor_id,
                "period": period,
                "billed_eur": billed_eur,
                "billed_eur_total": billed_eur_total,
                "warranty_eur": warranty_eur,
                "sales_to_dealer_eur": sales_to_dealer_eur,
                "stock_eur": stock_eur,
                "reading": READING,
                "match": _match(stock_eur, tolerance),
                "notes": row_notes,
            }
        )

    notes = []
    if warranty_unknown:
        notes.append(NOTE_WARRANTY_UNKNOWN)
    notes.extend(gap_notes)
    return {
        "reading": READING,
        "notes": notes,
        "rows": rows,
    }


def _key(line) -> tuple | None:
    if not isinstance(line, dict):
        return None
    if "distributor_id" not in line or "period" not in line:
        return None
    distributor_id = line["distributor_id"]
    period = line["period"]
    if distributor_id is None or period is None:
        return None
    return (distributor_id, period)


def _has_euros(line) -> bool:
    if not isinstance(line, dict) or "euros" not in line:
        return False
    amount = line["euros"]
    if amount is None:
        return False
    if isinstance(amount, str) and amount.strip() == "":
        return False
    return True


def _decimal(value) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, Decimal, float, str)):
        raise TypeError("euros must be a number")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    return Decimal(value)


def _cents(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def _match(stock_eur, tolerance) -> str | None:
    """Inside or outside only when stock was computed and a tolerance was given."""
    if tolerance is None or stock_eur is None:
        if tolerance is None:
            return "tolerance not set"
        return None
    limit = _decimal(tolerance)
    if abs(stock_eur) <= limit:
        return "inside"
    return "outside"
