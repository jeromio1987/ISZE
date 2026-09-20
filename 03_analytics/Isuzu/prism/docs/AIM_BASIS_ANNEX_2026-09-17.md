# Basis annex — AIM classification and the euro figures behind the case

**Internal · 17 September 2026 · read alongside `CASE_AIM_vs_Price_Class_for_Management.md`**

This annex exists because the management case and the audit were built on different windows. They are both correct. They must not be mixed.

---

## 1. Three bases appear in the same conversation. Name them every time.

| Basis | Window | Scope | What it is for |
|---|---|---|---|
| **A — in-scope pricing base** | 1 Jul 2025 – 30 Jun 2026 | in-scope customers, parts priced on both sides of the revision | the price-revision readout |
| **B — full billed window** | 1 Jan 2025 – 30 Jun 2026 | all billed parts lines in `sales_fact` | the audit, coverage, taxonomy checks |
| **C — full billed cross** | 1 Jul 2025 – 30 Jun 2026 | all billed parts lines, gross | the count audit on the classification file |

The management case quotes **A**. The audit quotes **B**. The classification-file audit quotes **C**. A reader who re-derives a figure on the wrong basis will get a different number and conclude someone made an error. This annex is how we prevent that.

### The same family, three numbers

| Figure | Basis A (revision) | Basis B (audit) |
|---|---:|---:|
| Brake parts, billed euro | €3.55M | €5.30M |
| Filters, billed euro | €2.35M | — |
| Competitive parts | €13.16M | €14.4M* |

\* Basis B competitive parts is taken on the governed catalogue axis for the audit window; the revision's €13.16M is on the in-scope priced base.

**Rule that follows:** no euro figure from this work leaves ISZE without the window and the scope in the same sentence or the same footnote.

---

## 2. What the classification audit found, in plain terms

The classification file carried **two different Level-1 vocabularies in one column**. One is the commercial tree (Competitive / Repair / Accident / High value repair / Comfort / Hardware and consumables). The other is a set of 21 system names (Body Exterior, Electrical, Transmission, Engine, Brakes, Intake Exhaust Emission, and so on).

Weighted by billed euro in basis C, the system names carry **79.4%** of the money while being only 9.7% of the rows. So the majority of the value sat on a vocabulary that is not the commercial tree we are proposing to adopt.

**The system itself is not the problem.** The governed catalogue tree is the right shape: 7 Level-1 postures, 25 Level-2 families, 172 Level-3 types. Level 2 reads like a real workshop menu. Part-number keys are perfect (164,667 rows, zero duplicates, all 10 characters). The catalogue columns tie to the PR00 source at 100%.

**What was wrong was the wiring:** one column holding two axes, a description-based join, and a precedence flag that told a reader the wrong thing about which layer governs.

---

## 3. What was corrected on 17 September

1. **A governed file was created.** `01_data/00_derived/aim_pn_classification_v2.csv` carries the catalogue tree and the workbook vocabulary in **separate named columns**, plus flags a consumer can filter on (`catalog_node_present`, `catalog_residual`, `axis_conflict`, `desc_ambiguous`). The original file is untouched; the catalogue columns are copied through byte-identical and verified against PR00 at **100.0%** on 163,014 checked rows.

2. **A safety gate now exists.** `01_data/91_build/verify_aim_classification.py` fails a build when the taxonomy drifts: new Level-1 values, node counts out of range, orphaned hierarchy, lost PR00 tie, growing residual, duplicate or malformed keys, or euro coverage of the governed axis dropping below its floor. Current run: **PASS, 13 of 13 checks.** It also compares each run against the previous one and flags drift above 1% per check.

3. **A false "Captive" label was removed from the pricing simulation.** The build was treating *any part number present in a catalogue* as proof that no competing alternative exists, and rolling those lines up as "Captive". Because almost every billed part number appears in that file, **41,829 lines and €12.96M** were carrying a competitive claim that the data did not support. They are now labelled **"Captive (proxy)"**, and the residual bucket is named **"not classified"** rather than counted as a moat.

The correction moved **no money**. The revision total is unchanged and reconciles exactly: **5.9616%** weighted increase, **€1,652,140.71** step euro, matching the published figure to the cent.

---

## 4. What is still open and must not be presented as solved

| Item | Status |
|---|---|
| Two Level-1 vocabularies in the **original** file | **Open.** v2 separates them; the original still holds both. Consumers migrate deliberately. |
| Workbook layer joined on description | **Open.** 71 descriptions still map to more than one Level 1. A part-number-keyed rebuild is needed. |
| Precedence flag semantics | **Open.** The flag still describes which vocabulary won the label, not which layer governs. |
| Euro coverage of the governed axis | **90.6%** of billed euro in the audit window sits on a real catalogue node. Roughly one euro in ten is on a residual or unclassified node and must be shown as such. |
| CY2026 measurement basis | **Open, separately.** The true end date of the 2026 sales column is not reconcilable to a clean quarter, and SaTy netting for Apr–Jun 2026 is sign-based only. |
| Consumer sweep | **Not completed.** Other packs that group by the old `aim_l1` have not all been checked. |

---

## 5. Why the management case still stands

The argument in the case — that a product tree beats a pricing letter for managing mix, capture, and a price revision — does not depend on any euro figure being large. It depends on the tree being real, and it is: 25 families, 172 types, 100% tied to the pricing catalogue.

The audit changes one thing about how the case should be presented: **state the basis, and state the residual.** A management pack that says "competitive parts, €13.16M on the in-scope revision base, with 90.6% of billed euro on a governed catalogue node and the remainder named" cannot be broken by a sharp reader. A pack that quotes the number bare can.

---

## 6. Files

| Artifact | Path |
|---|---|
| Management case | `01_data/90_INBOX/CASE_AIM_vs_Price_Class_for_Management.md` |
| Management HTML (10 sections) | `02_dashboards/sales/ISZE_AIM_vs_Price_Class_Case.html` |
| Classification audit | `03_analytics/Isuzu/prism/docs/AIM_CLASSIFICATION_AUDIT_2026-09-17.md` |
| This annex | `03_analytics/Isuzu/prism/docs/AIM_BASIS_ANNEX_2026-09-17.md` |
| Governed classification (v2) | `01_data/00_derived/aim_pn_classification_v2.csv` |
| v2 build script | `01_data/91_build/build_aim_classification_v2.py` |
| Safety gate | `01_data/91_build/verify_aim_classification.py` |
| Gate report | `01_data/00_derived/aim_classification_gate.json` |
| Pricing simulation (corrected) | `02_dashboards/pricing/ISZE_Pricing_Simulation_Spec_Basis.xlsx` |

---

## 7. Addendum — finding from the Isuzu EPC (17 September, later the same day)

Jerome opened the Isuzu Snapon EPC (electronic parts catalogue) in the browser, so a live check was possible against the manufacturer's own system.

### What was tested

Part number `8983767550` was searched in the EPC. The EPC returned:

- **28 catalogue results** across model codes (TFR/TFS pick-up, UCR/UCS SUV, including the 2026 LHD Europe/Israel catalogues)
- figure and part name: **`4-11 · FRONT HUB AND DRUM OR ROTOR`**, part name **`ROTOR; DISC BRK,FRT`**

### Why this matters — we already hold the join key

The EPC groups parts under a **figure key** (`4-11`). Our own pricing extract carries the same information in a different format:

| Source | Column | Value for `8983767550` |
|---|---|---|
| Isuzu EPC | figure | `4-11` |
| `pr00_classification.csv` | `fig_no` | `411` |
| `pr00_classification.csv` | `key_no` | `025` |
| `pr00_classification.csv` | `fig_key` | `411-025` |

The documented filter mapping confirms the same shape: `050-002` oil filter, `041-002` fuel filter, `130-006` air filter, `873-042` urea filter. So `fig_no` is the EPC figure with a zero pad, and `key_no` is the item within that figure.

**Figure-key coverage in our data is 97.9%** (161,129 of 164,667 part numbers carry a `fig_key`), across 13,847 distinct figure keys.

### What this unlocks (not yet built)

1. **An authoritative cross-check for the 71 ambiguous descriptions.** The EPC returns the manufacturer's own part name for a part number. Where our description-based join is ambiguous, the EPC name settles it by part number rather than by free text.
2. **A better competitive proxy than "the part number appears in a file".** Parts sharing one figure key belong to the same assembly group (for example two brake discs under `411-025`). That is a far stronger signal than mere existence in a catalogue.
3. **A route to closing the residual.** The `FILTER ASM` case (`8982878080`, 44.6% of the Other-filter block) is still unresolved in our data, and the EPC is the system that can name it.

### Honest limits on the above

- Two parts sharing a figure key are **not automatically competitors** — they may be left and right, or components of one assembly. The figure key is a strong *structural* signal, not a measured competitive position. It must not be labelled "Contested" without a human or further rule.
- The EPC session was a **spot check on one part number**, not a bulk extract. No catalogue coverage figure can be claimed from it.
- The EPC showed **no price** for the part in this session (`Price Source: None`), so it is a naming and structure source here, not a price source.
- Nothing in our data was changed as a result of this check. It is recorded as a capability finding.

