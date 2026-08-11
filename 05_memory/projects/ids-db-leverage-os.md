# DB leverage OS — Mode B one-pager

**Status:** v0.4 rollup is the working primary artefact (2026-08-11). Proposal discipline blijft: geen mail, geen silent overwrite, packs alleen op expliciete rebuild/ship.  
**Anchors:** Feedback Sheet **v0.4** · scan `ids_correlation_scan_2026-08-10.md` · Baumann FR/ES in `CHANGELOG.md`.

---

## 1. Job (één zin)

**DB leverage OS = de DB als hefboom: diagnose → contract → maandelijkse pull — niet “IDS omhoog → sales omhoog”.**

---

## 2. Primair artefact = rollup; dealer sheet = annex

| Artefact | Rol |
|----------|-----|
| **DB rollup (layer C)** | **Wat de DB opent eerst** — triage + netwerkacties + Pull-scorecard op één overview |
| **Dealer exec / workshop (A/B)** | **Annex voor het bezoek** — print/open per dealer op de hit list |
| **Commitments (D)** | Contract dat terugkomt; consolidate = maandelijkse pull-input |

**Open eerst (voorbeeld):**  
`C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IDS_2026_DB_Feedback_Sheet_v0.4\Greece\IDS_2026_DB_Rollup_Greece_v0.4.html`

---

## 3. Diagnose / Contract / Pull → rollup-blokken

| OS-fase | Rollup-sectie (v0.4) | Wat de DB doet |
|---------|----------------------|----------------|
| **Diagnose** | **Hit list** + network KPIs / bands | Wie eerst bezoeken (onder avg en/of Needs improvement); incomplete **niet** als “slechte score” |
| **Diagnose** | **Incomplete / not-completed lane** | FR/ES: Baumann reds; andere markten: zeros of **None** |
| **Contract** | **Suggested DB-level next steps** (+ dealer annex Kaizen) | 3–5 netwerkacties; Owner/datum/bewijs blank → invullen in DB planning meeting |
| **Pull** | **Pull scorecard** (leeg scaffold) | % visited YTD · % actions closed · # incomplete cleared · # escalations open |

IDS opent de deur. De OS houdt de deur open tot acties dicht zijn.

---

## 4. Versies (geen silent overwrite)

| Map | Rol |
|-----|-----|
| `…_Feedback_Sheet_v0.1/` … `v0.3/` | **Onaangeraakt** — historie |
| **`…_Feedback_Sheet_v0.4/`** | Hit list · incomplete lane · DB next steps · Pull scaffold · dealer annexes |
| Compare / country packs **v1.3** | Live Mode A — **niet aanraken** zonder rebuild/ship-OK |
| Future compare **v1.4** | Pending: Baumann avg-exclude locked; list/HTML-drop = Jerome-besluit |

Generator: `04_tools/ids_dealer_ranking/build_db_feedback_sheet.py` (`VERSION = v0.4`).

---

## 5. Wat correlatie faalde (kort)

Scan 2026-08-10: **geen** verdedigbare IDS ↔ parts-correlatie. Secties B–E ≈ één factor → geen “section D voorspelt sales”. Kaizen uit **checklist-gaps**, niet uit sectiestempels. Wallet = parallel (prijs/SPA/sell-out), niet via IDS.

---

## 6. Cadence

```
DB planning (rollup: hit list + DB actions + Pull blanks)
  → dealer bezoek (annex A/B + Commitments D)
    → maandelijkse Pull (scorecard invullen; consolidate commitments)
      → re-score alleen bij volgende IDS-cyclus
```

---

## 7. Pilot

**Eerst Greece (Petros)** — IDS al als visit triage; v0.4 rollup klaar. Belgium #2 na hygiene-check (duplicate rows). UK LCV / PL / NL / BE / FR (Baumann-lane demo) ook in v0.4.

---

## 8. Hard rules

1. Draft only, never Send.  
2. Geen silent version overwrite.  
3. Rebuild/ship alleen op expliciete woorden.  
4. Mode A buiten de deur; Mode B hier.  
5. UTI ≠ UMI · UK CV ≠ UK LCV.  
6. Baumann FR/ES: reds uit *averages*; IT/CH all-in; pilotmarkten all-in.  
7. Geen fake “IDS→€”.

---

## 9. Open beslissingen

- [ ] Pilot ship: Greece eerst, of Belgium?  
- [ ] v0.4 naar DB: ship / wacht / eerst hygiene (BE dup / Adam / Odyssey)?  
- [ ] v1.4 compare: alleen avg-exclude of ook uit list/HTML?  
- [ ] PIC-matrix Incomplete-lane + maandelijkse Pull per land?  
- [ ] Price wedge in dezelfde Pull-call of parallel?  
- [ ] Pull-metrics OK of strippen tot 2–3?

---

*Detailcorrelaties → `01_data/00_derived/ids_correlation_scan_2026-08-10.md`. Baumann → `04_tools/ids_dealer_ranking/CHANGELOG.md`.*
