# IDS atlas — platform and access plan

**Prepared:** 2026-09-20 · internal / private · read-only inspection, nothing built or changed
**Companion:** `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\IDS_NETWORK_ATLAS_CONCEPT_2026-09-20.md`

Build the demonstration first and keep every reader inside ISZE. Distributor access is a second,
separate project, because restriction per distributor is a data-separation problem before it is a
login problem. The host he believes he already has does not exist, and that has to be fixed before
anything is put behind a password.

## 1. What his three answers imply

He wants it shared behind a login, the main purpose is to impress peers, distributors may have it,
and it must be both a demonstration and a working tool. Those are three different projects sharing
one screen.

The tension is real and it is about ordering. A demonstration has one reader: him, plus ISZE
colleagues. A working tool for distributors has as many readers as distributors, and every one of
them must be prevented from seeing the others. The second is not the first with a password added —
it needs data separated per recipient before it is ever sent, and permission checked somewhere the
viewer cannot reach.

Demonstration first protects him for three reasons. It can be built from data that already exists,
so it produces something to show next month rather than next quarter. It puts the visible risk on
ISZE data rather than on a distributor's data. And it settles the design questions that distributor
access would otherwise force early, because he will see which parts of the screen he actually uses.

## 2. The access options, honestly

**(a) A static file, one copy per distributor.** This is what runs today. It is not access control —
it is sending the right file to the right person. It cannot revoke anything, and a copy that is
forwarded cannot be recalled. It breaks when the same file holds more than one market: the country
packs are cut per market by hand (`09_meetings\IDS_2026_Country_Packs_v1.3\`), and every correction
means re-cutting and re-sending every market. Cash cost is nil; the cost is hours per market, per
update. It enforces nothing.

**(b) Hosted behind logins.** Verified, and this is the important finding: **there is no GitHub Pages
site.** `gh api repos/jeromio1987/{ISZE,mypens,Alps-Sep2026,private}/pages` returns 404 for all four
repositories, all four are private, and the address documented in
`C:\Users\jerom\Desktop\claude\ISZE\00_docs\README.md` — https://jeromio1987.github.io/isze-dashboard/
— returns HTTP 404 with no repository of that name in existence. `C:\Users\jerom\Desktop\claude\ISZE\00_docs\UI_STACK.md`
(decided 2026-06-13) states that GitHub Pages is the external share surface; that statement is stale.
`C:\Users\jerom\Desktop\claude\ISZE\07_deploy\Master Dashboard\deploy.sh` is written to create a
private repository and switch Pages on, and appears never to have been run.

Even if it were run, Pages is the wrong tool here: it serves files, it does not authenticate readers,
so per-distributor logins cannot be done on it. (Whether his account's plan would even allow Pages on
a private repository: not verified.)

The folder documented for publishing is worse. `C:\Users\jerom\Desktop\claude\ISZE\07_deploy\publish-site\README_SYNC.md`
says publishing is done by dragging the folder onto Netlify Drop. That folder today contains the
whole IDS country set **and** `ISZE_DB_Leakage_Review_CY2025.html`, `ISZE_Leakage_Cockpit.html`, the
pricing pages, and five dealer-sales pages whose filenames still carry the old word for that data
(list them from the folder itself, not from here). Netlify Drop produces a public site with no login;
password protection is a paid feature. Dropped as it stands, dealer-level and leakage pages would be
open on the internet. (Whether that Netlify site exists and what plan it is on: not verified.)

**(c) PRISM, the analysis app already on port 8503.** `C:\Users\jerom\Desktop\claude\ISZE\03_analytics\Isuzu\prism\run_prism.ps1`
runs Streamlit on localhost with a normal and an internal window. There is no authentication in it at
all — a search across the app for login, password and secrets handling returned nothing. Cost is
already paid. Adding atlas views for internal use is small work. Making it safe for several
distributors is large work, because the app reads one local data folder and has no built-in idea of
who is looking. It also needs a machine that is always on.

**(d) Microsoft / SharePoint — what ISZE already does.** `C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IDS_2026_SharePoint_drop\IDS_dealer_sheets\`
holds one folder per market, each with a workbook per named dealer plus the distributor rollup. The
split is done by folder and file. `C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IDS_2026_MIDI_Packs\INDEX.md`
shows the same pattern as per-market zips drafted to named recipients, with one master zip holding
twelve country zips. Cost is already licensed (which tenant and plan: not verified). It can issue
access to named people, which is a real login — the recipient's own Microsoft account — and access
can be revoked. Its limit is that it is file-level, not row-level: it cannot let one distributor see
one row of a shared table.

**Front-runner: SharePoint/OneDrive per-distributor folders.** ISZE already splits IDS that way, the
recipient already has a Microsoft login, access can be taken back, and it needs no new hosting
decision.

## 3. Who may see what — the decision he actually owns

| Data layer | Jerome | ISZE colleagues | Each distributor, about itself | Distributors about each other |
|---|---|---|---|---|
| Our billing to each distributor (`01_data\00_derived\distributor_dimension.csv`) | yes | yes | market averages already shared; named euro **his call** | no |
| Distributor-to-dealer sales | yes | yes | dealer names already shared for the market; five markets only | **his call** — today only an anonymous network average |
| Dealer-to-end-customer sales | not held | not held | — | — |
| IDS dealer scores | yes | yes | yes — named per dealer today | anonymous average only; keep it so |
| IDS checklist answers and evidence | yes | yes | per market today | **his call** |
| Trucks in service | yes | yes | network totals already in shared pages | **his call** |
| Target spend / goal | yes | yes | network average shared | **his call** |
| Price and reference price | yes | yes | no | no |
| Another distributor's identity | yes | yes | kept anonymous today | no |

Sources for the "already shared" cells: `C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IDS_2026_DB_Feedback_Sheet_v0.4\README.md`,
`C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IDS_2026_Country_Packs_v1.3\`, and
`C:\Users\jerom\Desktop\claude\ISZE\09_meetings\IDS_2026_MIDI_Packs\INDEX.md`. Dealer-name coverage
per market comes from `C:\Users\jerom\Desktop\claude\ISZE\01_data\90_INBOX\PPT_GPT_commercial_pack_2026-09-19\02_sales_to_dealer\sales_to_dealer_coverage.csv`,
which shows 64 named dealers for one market and none for the rest.

## 4. What one file, opened by double-click, can and cannot do

It does everything one reader needs, provided the file contains only what that reader may see. It
breaks in this order. First, one file cannot serve several audiences: it must be cut per recipient
before sending, or it leaks. Second, if dealer names and euro sit in the same file, leaving one
country in gives that distributor's dealers away. Third, if the page reads a shared data file beside
it — the published pages fetch `../Data/...` — the restriction disappears, because anyone who can
open the page can open the data. Fourth, every correction means re-sending every copy, and no copy
already opened can be recalled.

It also cannot show what does not exist: there is no earlier IDS round, so no time series; and there
is no distributor-to-dealer link, so a distributor cannot be coloured by its dealers' commercial
results outside the markets that have dealer names.

## 5. The minimum that makes the demonstration land

What would impress a peer in parts sales is continuity, not motion: pick a market, and in one view
see what we billed, how that stands against the target spend, which service families are behind it,
and what the dealers in that market were assessed on — with the data basis stated on the screen and
one click to the evidence underneath. Add one view that shows honestly where evidence is missing.
That is the proposal's best idea already, and it is the part worth building.

What reads as a toy: animated dot migrations, a fly-through, a rotating dealership cutaway, a
drive-time map drawn on city-centre coordinates, and anything in 3D. Three limits should be said out
loud on the screen itself so no peer can catch him out — one assessment round only, no per-dealer
commercial link outside the markets with dealer names, and dealer scores that are annual snapshots,
never "today".

## 6. Build list, in order

1. **Clear the publish folder** of dealer-level and leakage pages. Work, no decision beyond approving
   it. This is a live exposure, so it comes first — ahead of any atlas work.
2. **Decide the host.** SharePoint/OneDrive per-distributor, an internal-only surface, or a paid
   private site. **Blocked on him.** Logins, revocation and cost all follow from this.
3. **Decide the sharing rule** from the table in section 3. **Blocked on him.**
4. **Confirm the IDS sources** — what sits inside `C:\Users\jerom\Desktop\claude\ISZE\01_data\08_Distributor\IDS_2026\`
   beyond the rankings folder, and whether per-question answers with dates exist. Work; not yet
   inspected.
5. **Build the demonstration** — one market, linked views, evidence basis visible, internal only.
   Work, needs no decision.
6. **Only then, per-distributor files or a hosted version**, cut to whatever 2 and 3 produced.
   **Blocked on 2 and 3.**
