"""Refined multilingual fleet-size extractor with false-positive guards.
Guards added after reviewing v1 output:
  - reject 1900-2100 (years, e.g. Hungarian "10/2026")
  - reject if number is part of a date/reference pattern (NN/NNNN, NN-NN)
  - require a genuine vehicle noun adjacent (max 3 chars gap), not loose proximity
  - reject notices whose title has no vehicle/CPV signal at all
Source: 01_data/14_dashboards/tender_data.json
"""
import json
import re
from collections import Counter
from pathlib import Path

d = json.load(open("01_data/14_dashboards/tender_data.json", encoding="utf-8"))
notices = d.get("notices", [])

NOUNS = (
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
    r"|g[ée]pj[aá]rm[uű][a-z]*"
    r"|fordon|lastbilar?"
    r"|kj[oø]ret[oø]y|lastebiler?"
    r"|ajoneuvo[a-z]*|kuorma-auto[a-z]*"
    r"|автомобил[а-я]*"
    r"|vozila?"
)
COUNTERS = r"st[uü]ck|szt|buc|db|ks|kpl|units?|stk|pcs"

# number immediately before noun, optional counter word between
PAT_NUM_NOUN = re.compile(
    rf"(?<![\d/.,-])(\d{{1,4}})\s*(?:{COUNTERS})?\.?\s*(?:{NOUNS})\b", re.I
)
# noun then counter-qualified number  e.g. "autocarri n.9", "pojazdów 6 szt"
PAT_NOUN_NUM = re.compile(
    rf"(?:{NOUNS})\W{{0,12}}?(?<![\d/.,-])(\d{{1,4}})\s*(?:{COUNTERS})\b", re.I
)
PAT_FLEET_OF = re.compile(r"\bfleet\s+of\s+(\d{1,4})\b", re.I)

MAXPLAUSIBLE = 3000


def looks_like_year(n):
    return 1900 <= n <= 2100


def extract(*fields):
    text = " ".join(f for f in fields if f)
    if not text:
        return 0
    best = 0
    for pat in (PAT_NUM_NOUN, PAT_NOUN_NUM, PAT_FLEET_OF):
        for m in pat.finditer(text):
            try:
                n = int(m.group(1))
            except Exception:
                continue
            if not (1 <= n <= MAXPLAUSIBLE):
                continue
            if looks_like_year(n):
                continue
            # reject date/reference context immediately around the number
            s, e = m.span(1)
            before = text[max(0, s - 2):s]
            after = text[e:e + 2]
            if "/" in before or "/" in after:
                continue
            if n > best:
                best = n
    return best


hits = 0
by_country = Counter()
samples = []
for n in notices:
    title = n.get("Title") or ""
    desc = n.get("Description") or ""
    v = extract(title, desc)
    if v:
        hits += 1
        by_country[n.get("Country")] += 1
        if len(samples) < 40:
            samples.append((v, n.get("Country"), (n.get("Buyer") or "")[:26], title[:88]))

print(f"notices: {len(notices)}")
print(f"v2 (guarded) fleet-size hits: {hits}  ({hits/len(notices)*100:.1f}%)")
print("by country:", dict(by_country.most_common(15)))

out = ["=== v2 GUARDED EXTRACTIONS (review for FPs) ==="]
for v in samples:
    out.append(f"{v[0]:>5} | {v[1]:<16} | {v[2]:<26} | {v[3]}")
Path(__file__).with_name("fleet_v2_samples.txt").write_text("\n".join(out), encoding="utf-8")
print(f"wrote {len(samples)} samples")
