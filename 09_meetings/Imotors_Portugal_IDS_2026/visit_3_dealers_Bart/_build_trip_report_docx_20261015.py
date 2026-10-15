# -*- coding: utf-8 -*-
"""Build Portugal IDS dealer visit trip report (Word) — compact, Jerome style."""
from pathlib import Path

from docx import Document
from docx.shared import Pt

OUT = Path(__file__).resolve().parent / (
    "TripReport_IMotors_Portugal_IDS_Dealer_Visits_2026-10.docx"
)
# Fallback if Word has the main file open
OUT_FALLBACK = Path(__file__).resolve().parent / (
    "TripReport_IMotors_Portugal_IDS_Dealer_Visits_2026-10_EDIT.docx"
)


def main() -> None:
    d = Document()
    style = d.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    def h1(t: str) -> None:
        d.add_heading(t, level=1)

    def h2(t: str) -> None:
        d.add_heading(t, level=2)

    def h3(t: str) -> None:
        d.add_heading(t, level=3)

    def p(t: str) -> None:
        d.add_paragraph(t)

    def bullet(t: str) -> None:
        d.add_paragraph(t, style="List Bullet")

    def table(rows: list[tuple[str, ...]]) -> None:
        t = d.add_table(rows=len(rows), cols=len(rows[0]))
        t.style = "Table Grid"
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                t.rows[i].cells[j].text = val

    title = d.add_paragraph()
    run = title.add_run(
        "ISZE · I-Motors Portugal · IDS dealer visits · October 2026"
    )
    run.bold = True
    run.font.size = Pt(16)
    p(
        "Trip report  ·  ~12–16 October 2026  ·  "
        "Rolmax · Auto Reno Paços de Ferreira · Socarros Caldas"
    )

    h1("Trip participants")
    table(
        [
            ("Name", "Company / role"),
            ("Jerome Van Der Pluym", "ISZE — Vehicle Parts"),
            ("Uematsu san", "IMG"),
            ("Nuno Machado", "Astara / I-Motors"),
        ]
    )

    h1("IDS approach on this trip")
    p(
        "The IDS sheet has 196 questions. A full re-score was not possible in the "
        "time available. We used the April 2026 weak points (zeros) as the walk list, "
        "especially at Auto Reno, and checked what had improved."
    )

    h1("Executive summary — dealer visits")
    p(
        "Maintenance is the core of aftersales at these dealers. BVP is used a lot. "
        "R&M is hard unless it sits at fleet level. Extended warranty is more "
        "interesting to the dealers we met. Warranty labour and diagnosis cost are a "
        "real issue for them."
    )
    p(
        "Portugal already scores high on IDS versus the European network. The visit "
        "did not re-open all 196 questions. Several April zeros still matter: R&M / "
        "extended warranty offer, workshop volume reported to the distributor, 24/7 "
        "roadside, and outside-hours parts access."
    )
    p("Main points to take forward with I-Motors:")
    bullet("Brief dealers clearly on R&M vs extended warranty; R&M mainly at fleet level.")
    bullet(
        "Protect genuine where it counts (brakes, OTC margin, warranty diagnosis). "
        "BVP stays useful after warranty."
    )
    bullet(
        "Get workshop volume reported to the distributor (IDS C.4-20). Socarros already "
        "shares DMS data."
    )
    bullet("ISZE to prepare an SPA part shortlist; deeper fill-rate study needed.")
    bullet(
        "If next month ISZE sales still lag, MOS still low and back orders still high: "
        "hold a follow-up with I-Motors."
    )

    # ----- Rolmax -----
    h1("Dealer Visit: Rolmax — Vila Nova de Gaia")
    p("Monday afternoon  ·  Vila Nova de Gaia  ·  IDS 90.7% (April 2026)")
    p(
        "Official Isuzu / Maxus / Piaggio site under the Rolcar group "
        "(Rua Dr. Ribeiro Magalhães 168, Vila Nova de Gaia)."
    )

    h3("Business profile")
    bullet("About 70% of aftersales is maintenance.")
    bullet("Parts: they always go for BVP where it fits.")
    bullet('Fill rate: described as "simple" — no real complaint on the day.')
    bullet("Diagnosis: about €350 if there is no repair afterwards.")
    bullet("Parts stock: about €700k.")
    bullet("R&M: difficult unless set at fleet level.")

    h3("IDS weak points (April 2026)")
    bullet("C.4-20 — workshop / maintenance volume not sent to the distributor.")
    bullet("A.2-4 — aftersales promo (service contract / health report) not visible.")
    bullet("D.2-16 — R&M / extended warranty offer.")
    bullet("Also zeros: name badge (A.3-2), AED (B.5-11), van / 24/7 roadside (C.1-19/20).")

    h3("What can improve")
    bullet(
        "R&M / extended warranty: I-Motors to brief the dealer on what is available and "
        "when fleet-level contracts make sense."
    )
    bullet("Put aftersales promo at reception (A.2-4) — low effort.")
    bullet("Start sending workshop volume to the distributor (C.4-20).")
    bullet(
        "Agree with I-Motors which families stay genuine and where BVP is accepted "
        "after warranty."
    )

    h3("Key observations")
    bullet(
        "High maintenance share and €700k stock fit a strong aftersales dealer."
    )
    bullet(
        "BVP-first and fleet-only R&M limit genuine capture and contract penetration."
    )
    bullet(
        "Dealer fill rate felt fine locally. That is not the same as the "
        "distributor fill / MOS picture in the September review."
    )

    # ----- Auto Reno -----
    h1("Dealer Visit: Auto Reno — Paços de Ferreira")
    p(
        "Tuesday morning  ·  Paços de Ferreira  ·  "
        "IDS 96.1% (April 2026; top of Portugal, country avg 86.7%)"
    )
    p(
        "Multi-brand northern group (founded 1993), Isuzu among other marques. "
        "Astara named Auto Reno Best Isuzu Dealer in Portugal for 2025. Sites include "
        "Paços de Ferreira, Penafiel, Póvoa de Varzim, Viana do Castelo and Maia."
    )

    h3("Business profile")
    bullet("Opel partner since 2003; about four years with Stellantis. Opel is the main brand.")
    bullet("Three sites today; still expanding. About 11 brands on the group.")
    bullet("Site about 13,000 m²; peaks around 100 vehicles per day; two chill rooms.")
    bullet("Group turnover about €7M, of which roughly 7–10% Isuzu.")
    bullet("At this site about 50% Isuzu. Strong Isuzu volume dealer; mix ~70–80% CV.")
    bullet("Stellantis EV station coming; car wash and body paint on site.")
    bullet("Five marketing people for all brands.")

    h3("Workshop")
    bullet("Diagnosis tools OK; no dedicated Isuzu tools.")
    bullet("About 11 mechanics. Strong competition from informal workshops.")
    bullet("More gearbox issues recently.")
    bullet(
        "Warranty labour rates very strict. Diagnosis often not paid — dealer raises "
        "labour rates as diagnosis work grows."
    )

    h3("Parts, warranty and programmes")
    bullet("No OTC parts sales — margin too low.")
    bullet("Brake parts expensive; sometimes sells aftermarket.")
    bullet("Not aware of Isuzu R&M contracts.")
    bullet("Extended warranty much more interesting than R&M.")
    bullet("Warranty customers growing; two people continuously calling customers (since ~2010).")
    bullet("Customers can stock more parts. Maintenance report can be arranged.")
    bullet("S1–S4 classification: dealer did not know what it was.")

    h3("IDS weak points (April 2026)")
    bullet("C.4-20 — workshop volume to distributor.")
    bullet("A.1-22 — 24/7 roadside contact.")
    bullet("D.1-10 — outside-hours parts access.")
    bullet("B.5-11 — AED. Also S-classification in database (B.6-5) — unknown on the day.")

    h3("What can improve")
    bullet("I-Motors to brief R&M vs extended warranty. Dealer preference is extended warranty.")
    bullet("Brakes: price pressure and aftermarket — add to ISZE SPA shortlist.")
    bullet("Warranty diagnosis not paid — raise with I-Motors / warranty policy.")
    bullet("Explain S1–S4 once if I-Motors wants it in the DMS.")
    bullet("Close remaining zeros if still open: C.4-20, 24/7 roadside, AED, outside-hours parts.")

    h3("Key observations")
    bullet(
        "Highest IDS score in Portugal and Astara best-dealer 2025, but R&M unknown "
        "and brakes leak to aftermarket."
    )
    bullet("Outbound calling and extended warranty interest are strengths.")
    bullet("Multi-site stock: secondary sites may look weak if stock sits centrally.")

    # ----- Socarros -----
    h1("Dealer Visit: Socarros — Caldas da Rainha")
    p("Tuesday afternoon  ·  Caldas da Rainha  ·  IDS 82.1% (April 2026)")
    p(
        "Socarros (Grupo NOV) covers Isuzu / Maxus in Santarém, Tomar and Caldas da "
        "Rainha. Caldas site shares the address with LizDrive Ford — matches the note "
        "that a mobile Ford branch is also used for Isuzu."
    )

    h3("Business profile")
    bullet("13 brands in the group.")
    bullet("Mobile Ford unit also used for Isuzu roadside and maintenance.")
    bullet("Dedicated Isuzu bay. Mix more D-Max than CV.")
    bullet("No SST in these sites.")

    h3("Workshop, warranty and programmes")
    bullet("R&M contracts very difficult.")
    bullet("Isuzu warranty: no margin for the dealer.")
    bullet("More warranty cases on D-Max.")
    bullet(
        "Warranty system hard to use: English poorly translated, code-based; other "
        "brands work with part numbers. GIDSS update raised."
    )
    bullet("Sell quite a lot of BVP.")
    bullet("Customer follow-up difficult — vehicles move nationwide.")
    bullet("Already claim improvements on IDS sections A and B.")
    bullet("Salesforce for leads. DMS data shared with the distributor.")

    h3("IDS weak points (April 2026)")
    bullet("A.1-22 — 24/7 roadside (mobile Ford helps; confirm Isuzu contact).")
    bullet("B.1-2 — local UIO used for parts / service planning.")
    bullet("C.1-19/20 — van + roadside.")
    bullet("D.1-10 — outside-hours parts.")
    bullet("E.1-5 — lead response tracking (Salesforce may help — check).")

    h3("What can improve")
    bullet("Warranty tooling / language / part numbers (GIDSS) — real friction on D-Max.")
    bullet('Warranty "no margin" needs a commercial answer from I-Motors / ISZE.')
    bullet("R&M only where fleet-level works — same as Rolmax.")
    bullet("SST plan if D-Max warranty / service keep rising.")
    bullet("Check A/B improvements against April zeros, then push D/E and roadside / parts hours.")

    h3("Key observations")
    bullet("Bay and mobile capacity exist; warranty process and R&M economics are the block.")
    bullet("BVP active; genuine under warranty not attractive for the dealer.")
    bullet("Lowest IDS of the three — useful check on whether A/B fixes landed.")

    # ----- BPR -----
    h1("I-Motors FY2027 Business Performance Review — September closed")
    p(
        "Presented during the visit; shared with Uematsu san. Data through September "
        "2026, updated 6 October 2026 (35 slides)."
    )
    p(
        "Headline: dealer demand is up, but I-Motors is running stock down. ISZE "
        "billing is behind plan and MOS is below target."
    )
    table(
        [
            ("Topic", "Figure"),
            ("ISZE sales Apr–Sep 2026", "€836K vs €924K budget (−9.6%)"),
            ("Orders Apr–Sep 2026", "€849K vs budget (−8.2%)"),
            ("Sales to dealer Apr–Sep 2026", "€2.281M vs €1.816M LY (+25.6%)"),
            ("Fill rate Sep", "ISZE→I-Motors 87% (tgt 93%); I-Motors→dealer 81% (tgt 85%)"),
            ("MOS Sep", "2.5 vs target 3.0 (3.7 in Sep 2025)"),
            ("Back-order lines Sep", "495 (282 in Aug)"),
            ("Genuine parts share FY2026", "57.7% scrap-rate model (GPS lock 63.3% where used)"),
        ]
    )
    bullet("Gap to plan is mainly August–September, not a weak FY27 start.")
    bullet(
        "Sales to dealer up vs last year while ISZE billing lags fits stock destock at "
        "I-Motors, not a collapse in dealer demand."
    )
    bullet(
        "Dealer visits match the same story: BVP / brakes / R&M difficulty are network "
        "points, not one dealer."
    )

    h1("Action points")
    p(
        "Updated after the dealer visits and the September-closed review "
        "(also carrying open items from the 29 July ISZE–Astara meeting)."
    )
    table(
        [
            ("#", "Action", "Owner", "Due / trigger"),
            (
                "1",
                "ISZE to provide the parts / families where an SPA is needed "
                "(brakes flagged at dealers; align with Astara SPA ask from 29 Jul).",
                "ISZE",
                "ASAP / next SPA cycle",
            ),
            (
                "2",
                "Deeper fill-rate study (ISZE→I-Motors and I-Motors→dealer) — "
                "part numbers behind the gap, not only headline %.",
                "ISZE + I-Motors",
                "Before next monthly review",
            ),
            (
                "3",
                "If next month ISZE sales still lag, MOS still low and back orders "
                "still high: dedicated follow-up with I-Motors.",
                "ISZE + I-Motors",
                "Next monthly KPI after Sep",
            ),
            (
                "4",
                "Brief dealers on R&M vs extended warranty; R&M mainly fleet level; "
                "aftersales promo at reception.",
                "I-Motors",
                "ASAP",
            ),
            (
                "5",
                "Workshop volume to distributor (C.4-20) at Rolmax and Auto Reno.",
                "I-Motors + dealers",
                "Next IDS cycle",
            ),
            (
                "6",
                "Warranty: GIDSS / language / usability; unpaid diagnosis; "
                "no-margin feedback.",
                "I-Motors + ISZE",
                "Follow-up",
            ),
            (
                "7",
                "Keep monthly sales-to-dealer file; add monthly stock snapshot (29 Jul).",
                "I-Motors",
                "Ongoing",
            ),
        ]
    )

    h1("Sources")
    bullet("Visit notes — Jerome, October 2026.")
    bullet("IDS 2026 Portugal self-assessment (April 2026).")
    bullet("I-Motors FY2027 BPR — September closed (6 Oct 2026).")
    bullet("ISZE–Astara minutes 29 July 2026.")
    bullet("Public: rolmax.pt, autoreno.pt, novautomoveis.pt, lizdrive.pt (Oct 2026).")

    try:
        d.save(OUT)
        path = OUT
    except PermissionError:
        d.save(OUT_FALLBACK)
        path = OUT_FALLBACK
    print(f"wrote {path} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
