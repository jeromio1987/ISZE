# Cursor work file — ISZE Tender Monitor

**Written:** 2026-08-25 · **Repo path:** `04_tools/ISZE_Tender_Monitor_Install/`
**Companion doc:** `CURSOR_TASK_fix_dark_markets.md` (market/source diagnosis)

This file contains **runnable code** for the fixes. Every diagnosis below was probed live on
2026-08-25 — do not trust the existing inline comments, two of them are wrong (T2, T3).

Work in this order. T1, T5, T6 and T7 are self-contained and can be done immediately.

---

## Task index

| # | Task | File | Effort | Blocking? |
|---|------|------|--------|-----------|
| T1 | Source health check — make silent failure impossible | `tender_scraper_v3.py` | Low | No |
| T2 | Israel source is dead — re-point it | `tender_scraper_v3.py` | Medium | Needs endpoint discovery |
| T3 | Belgium source is dead — re-point it | `tender_scraper_v3.py` | Medium | Needs endpoint discovery |
| T4 | Norway + Finland — API keys via env vars | `tender_scraper_v3.py` | Trivial | Needs registration |
| T5 | Expire past-deadline notices | `isze_core_v3.py` | Trivial | No |
| T6 | Multilingual fleet-size extraction | `isze_core_v3.py` | Low | No |
| T7 | Parts-revenue-equivalent sizing (new field) | `isze_core_v3.py` + dashboard | Low | Needs T6 |
| T8 | Surface fleet size + revenue equivalent + health in dashboard | `build_dashboard_v2.py` | Medium | Needs T6, T7, T1 |

---

## T1 — Source health check (do this first)

**Problem.** Every dead source returns `HTTP 200` with a valid-looking body. The scraper cannot tell
*"no tenders matched this week"* from *"this endpoint has been dead for months"*, and the log prints a
reassuring summary either way:

```
  Israel:   0
  Belgium:  0
```

**Fix.** Add a validator and a rolling zero-run counter. Drop this into `tender_scraper_v3.py`:

```python
import json, os
from pathlib import Path

_HEALTH_PATH = Path(__file__).with_name("_source_health.json")


def _load_health() -> dict:
    if _HEALTH_PATH.exists():
        try:
            return json.loads(_HEALTH_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_health(state: dict) -> None:
    _HEALTH_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def validate_feed(name: str, resp, *, expect=("<item", "<entry"), min_bytes: int = 500) -> str | None:
    """Return an error string if the response is clearly not the feed we expect, else None."""
    if resp is None:
        return "no response"
    ctype = (resp.headers.get("Content-Type") or "").lower()
    body = resp.content or b""
    if len(body) < min_bytes:
        return f"body too small ({len(body)} bytes) — endpoint likely retired"
    head = body[:6000].lower()
    if not any(tok.encode() in head for tok in expect):
        # an HTML page served where a feed is expected is the signature of a retired endpoint
        if b"<html" in head or "html" in ctype:
            return f"HTML returned where feed expected (ctype={ctype}) — endpoint retired or moved"
        return f"no {expect} elements found (ctype={ctype})"
    return None


def record_source_result(state: dict, name: str, count: int, error: str | None) -> None:
    entry = state.setdefault(name, {"zero_runs": 0, "last_error": None})
    if error:
        entry["status"] = "BROKEN"
        entry["last_error"] = error
        entry["zero_runs"] = entry.get("zero_runs", 0) + 1
    elif count == 0:
        entry["zero_runs"] = entry.get("zero_runs", 0) + 1
        entry["status"] = "SUSPECT" if entry["zero_runs"] >= 3 else "OK"
        entry["last_error"] = None
    else:
        entry["zero_runs"] = 0
        entry["status"] = "OK"
        entry["last_error"] = None
    entry["last_count"] = count


def print_health_report(state: dict) -> None:
    bad = {k: v for k, v in state.items() if v.get("status") in ("BROKEN", "SUSPECT")}
    print("\n" + "=" * 60)
    if not bad:
        print("SOURCE HEALTH: all sources OK")
    else:
        print(f"!! SOURCE HEALTH: {len(bad)} SOURCE(S) NEED ATTENTION")
        for k, v in bad.items():
            print(f"   [{v['status']}] {k}: {v.get('last_error') or f'{v[chr(34)}zero_runs{chr(34)}]} consecutive empty runs'}")
    print("=" * 60)
    _save_health(state)
```

**Wire it into each fetcher.** Example for Israel:

```python
health = _load_health()          # once, near the top of main()

# inside fetch_israel(), after get_with_retry():
err = validate_feed("Israel", resp)
if err:
    print(f"[IL] SOURCE BROKEN: {err}")
    record_source_result(health, "Israel", 0, err)
    return []
```

and at the very end of the run, after the per-source summary:

```python
print_health_report(health)
```

**Acceptance:** running today must print a `SOURCE HEALTH` block naming Israel and Belgium as BROKEN.

---

## T2 — Israel: the endpoint is dead ⚠️ existing comment is wrong

`fetch_israel()` (~line 727) requests:

```
https://mr.gov.il/ilgstorefront/he/rss/Tenders.xml
```

**Probed 2026-08-25:** `HTTP 200`, `Content-Type: text/html;charset=UTF-8`, **662,850 bytes**, body is an
HTML page (`<!DOCTYPE html><html lang="he">` … `<title>… | ILG Site</title>`). **Zero `<item>` elements** —
confirmed by parsing with `lxml` in `recover=True` mode, which also returned 0 items.

The current `except ET.ParseError` branch sanitises HTML entities and retries. That treats the symptom of
the wrong disease. **A lenient parser will not help — there is no feed at this URL.** The logged error
`mismatched tag: line 53, column 2` is simply the HTML `</head>`.

**Work required:** find the current machine-readable source, in this order of preference —
1. an official API / OpenData tenders dataset on `mr.gov.il` or `data.gov.il`;
2. a current RSS/Atom path (the `/rss/` prefix appears retired in a site rebuild);
3. last resort — HTML scraping of the search-results page, which *is* still served at that URL.

**Also fix while you are in there:** the current implementation hard-codes `"Deadline": ""`, so even when
it worked, Israeli notices could never be triaged by urgency. Populate a real deadline.

**Why it matters:** Israel is **18% of ISZE network revenue** and currently has zero tender visibility.

---

## T3 — Belgium: the endpoint is dead ⚠️ existing comment is wrong

`fetch_belgium()` (~line 1195) requests `https://www.publicprocurement.be/en/rss`.

**Probed 2026-08-25:** `HTTP 200`, `Content-Type: text/html`, **1,196 bytes** — a JavaScript single-page-app
shell (`<html lang="en" translate="no">`). The root domain returns the identical 1,196-byte shell,
confirming a rebuild to an SPA. The inline comment *"TED covers above-threshold BE"* treats 0 results as
normal; it is not — Belgium is the fourth-largest market and below-threshold municipal/utility fleet work
is exactly the Isuzu-sized opportunity.

**Work required:** open the Belgian e-Procurement search in a browser, watch the Network tab, and identify
the JSON/XHR API the SPA calls. Re-point the fetcher at that. Check for a published open-data endpoint first.

---

## T4 — Norway + Finland: keys via environment variables

Both fetchers are already written and early-return on a blank key.

```python
# replace the bare module constants
DOFFIN_API_KEY = os.environ.get("ISZE_DOFFIN_API_KEY", "")
HILMA_API_KEY  = os.environ.get("ISZE_HILMA_API_KEY", "")
```

Register free keys at `docs.doffin.no` and `hankintailmoitukset.fi/en/docs/api`.
**Do not commit keys.** Set them in the scheduled task environment.

---

## T5 — Expire past-deadline notices

**Problem.** The action queue presents opportunities whose deadline has already passed at *Selective* tier.
Live in the 24 Aug 2026 run:

| Buyer | Country | Deadline | Days past |
|---|---|---|---|
| Командване на военноморските сили | Bulgaria | 2026-07-16 | 39 |
| Banca Naţională a României | Romania | 2026-07-18 | 37 |
| A.R.E.S. 118 | Italy | 2026-08-03 | 21 |
| R.A. ROMATSA | Romania | 2026-08-06 | 18 |

**Fix** — in the scoring stage of `isze_core_v3.py`, before the decision is assigned:

```python
from datetime import date

def apply_expiry(row: dict) -> dict:
    """Route past-deadline notices to a terminal Expired decision."""
    dl = row.get("deadline_date") or row.get("Deadline Date")
    if dl:
        try:
            if date.fromisoformat(str(dl)[:10]) < date.today():
                row["decision"] = "Expired"
                row["status_suggested"] = "Expired"
                row["next_action_suggested"] = "Closed — deadline passed"
                row["actionable"] = False
        except ValueError:
            pass
    return row
```

Exclude `Expired` from the action queue and from Attack/Selective counts. **Keep the rows in the dataset**
for history — just stop presenting them as live.

---

## T6 — Multilingual fleet-size extraction

**Problem.** `extract_fleet_size()` (`isze_core_v3.py` ~line 532) is English-language and **title-only**.
Since 605 of 778 notices arrive from TED in national languages, it fires on **1 notice out of 778**.

**Tested result:** the replacement below lifts that to **22 of 778 at roughly 95% precision** on manual
review of every hit. Real recoveries include an 83-vehicle Romanian postal fleet and a 20-vehicle
Stuttgart municipal order.

Replace the function with:

```python
import re

_FLEET_NOUNS = (
    r"vehicles?|trucks?|vans?|lorr(?:y|ies)|buses?|coaches?|pick[\s-]?ups?|minibuses?"
    r"|v[ée]hicules?|camions?|camionnettes?|autobus"
    r"|fahrzeuge?n?|lkw|nkw|pkw|nutzfahrzeuge?n?|kraftfahrzeuge?n?|transporter"
    r"|veicoli?|autoveicoli?|autocarri?|automezzi?|furgoni?"
    r"|veh[íi]culos?|camiones?|furgonetas?|turismos?"
    r"|ve[íi]culos?|carrinhas?"
    r"|voertuigen?|bestelwagens?|vrachtwagens?"
    r"|pojazd[oóyw]*|samochod[oóyw]*|ci[eę][zż]ar[oó]w[a-z]*|ci[aą]gnik[oóyw]*"
    r"|vozidel|vozidla|vozidlo|automobil[uůy]?"
    r"|autovehicule?|autoutilitar[ae]?|automobile?"
    r"|g[ée]pj[aá]rm[uű][a-z]*|fordon|lastbilar?|kj[oø]ret[oø]y|lastebiler?"
    r"|ajoneuvo[a-z]*|kuorma-auto[a-z]*|автомобил[а-я]*|vozila?"
)
_FLEET_COUNTERS = r"st[uü]ck|szt|buc|db|ks|kpl|units?|stk|pcs"

_FLEET_P1 = re.compile(
    rf"(?<![\d/.,-])(\d{{1,4}})\s*(?:{_FLEET_COUNTERS})?\.?\s*(?:{_FLEET_NOUNS})\b", re.I)
_FLEET_P2 = re.compile(
    rf"(?:{_FLEET_NOUNS})\W{{0,12}}?(?<![\d/.,-])(\d{{1,4}})\s*(?:{_FLEET_COUNTERS})\b", re.I)
_FLEET_P3 = re.compile(r"\bfleet\s+of\s+(\d{1,4})\b", re.I)

_FLEET_MAX = 3000


def extract_fleet_size(title: str, description: str = "") -> int:
    """Best-effort fleet size from notice text, multilingual.

    Guards (added after false positives in a first pass):
      - reject 1900-2100 (years, e.g. Hungarian reference '10/2026')
      - reject when '/' abuts the number (dates and reference numbers)
      - cap at 3000 units
      - take the MAXIMUM plausible match, not the first
    """
    text = " ".join(t for t in (title, description) if t)
    if not text:
        return 0
    best = 0
    for pat in (_FLEET_P1, _FLEET_P2, _FLEET_P3):
        for m in pat.finditer(text):
            try:
                n = int(m.group(1))
            except (TypeError, ValueError):
                continue
            if not (1 <= n <= _FLEET_MAX) or 1900 <= n <= 2100:
                continue
            s, e = m.span(1)
            if "/" in text[max(0, s - 2):s] or "/" in text[e:e + 2]:
                continue
            if n > best:
                best = n
    return best
```

**Update every call site** to pass the description — currently `fetch_israel()` and others call
`extract_fleet_size(title)` only:

```python
"FleetSize": extract_fleet_size(title, description),
```

**Set expectations honestly.** Only **168 of 778 notices (22%) carry any description text at all**, and
vehicle counts normally live in the tender documents behind the notice. ~3% populated is the realistic
ceiling for text extraction. This turns 1 usable figure into ~22 — it is not a route to a full column.

---

## T7 — Parts-revenue-equivalent sizing (new field)

**Why.** A notice is not a business case; a euro figure is. Converting fleet units into the parts revenue
they will generate is how opportunities should be ranked and how leads should reach distributors.

```python
# ISZE-derived average annual parts spend per unit (Poland SPA study, 29-07-2026).
# NOTE: market-specific. Do not silently apply a UK benchmark to a CEE market.
PARTS_SPEND_PER_UNIT_YEAR_EUR = 291.20


def parts_revenue_equivalent(fleet_size: int, years: int = 3) -> dict:
    """Annual and multi-year parts-revenue equivalent for a sized opportunity."""
    if not fleet_size:
        return {"per_year_eur": 0, "term_eur": 0, "term_years": years, "basis": None}
    per_year = round(fleet_size * PARTS_SPEND_PER_UNIT_YEAR_EUR)
    return {
        "per_year_eur": per_year,
        "term_eur": per_year * years,
        "term_years": years,
        "basis": f"{fleet_size} units x EUR {PARTS_SPEND_PER_UNIT_YEAR_EUR:.2f}/unit/yr",
    }
```

Add `parts_revenue_per_year` and `parts_revenue_term` to each opportunity in the output JSON.
Where `fleet_size` is 0, emit `null` rather than 0 so the dashboard can distinguish
*"no fleet size known"* from *"zero value"*.

**Sanity check on current data:** 22 sized notices → 210 units → **≈ €61,000/year**, ≈ €183,000 over three
years. The largest single one (83-unit Romanian postal fleet) is ≈ €24,170/year on its own.

---

## T8 — Surface it in the dashboard

`build_dashboard_v2.py`:

1. Add **Fleet size** and **Parts revenue / yr** columns to the opportunity table; leave blank (not zero)
   when unknown.
2. Add a **sort by parts-revenue equivalent** option — this becomes the default prioritisation.
3. Add a **source health banner** at the top of the page driven by `_source_health.json` from T1, so a
   dead source is visible to whoever reviews the weekly output instead of buried in a text log.
4. Exclude `Expired` (T5) from the action queue and the headline counts.

---

## Out of scope

- **The UK zero.** The UK returns 125 notices and **0 at action tier**. That is a *scoring* question, being
  handled separately by manual review of a notice sample. **Do not re-tune the Fit/Win/Econ weightings as
  part of this work.**
- The dashboard's visual design beyond the four additions in T8.

---

## Verification checklist

Run `run_tender_monitor.bat`, then confirm:

- [ ] A `SOURCE HEALTH` block prints, naming Israel and Belgium as BROKEN
- [ ] Israel returns >0 notices, each carrying a real deadline
- [ ] Belgium returns >0 notices
- [ ] Norway and Finland return >0 notices; no `No API key set` line remains
- [ ] No notice with a past deadline appears at Attack or Selective tier
- [ ] Fleet size populated on ~20+ notices; spot-check 10 and confirm no year-values (2026 etc.)
- [ ] `parts_revenue_per_year` present and plausible on every sized opportunity
- [ ] Dashboard sorts by parts-revenue equivalent and shows the health banner
- [ ] No API key appears in any committed file
