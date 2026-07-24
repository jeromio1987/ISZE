# Holiday laptop — GitHub grab bag

**Purpose:** private backup + work from another machine. Not for sharing, Pages, or Streamlit Cloud.

**Last updated:** 2026-07-24

---

## Clone these (essentials)

```bash
git clone https://github.com/jeromio1987/ISZE.git
git clone https://github.com/jeromio1987/mypens.git
git clone https://github.com/jeromio1987/investing-dashboard.git
```

Optional fun side quest:

```bash
git clone https://github.com/jeromio1987/rigged-game.git
```

Optional (rarely needed on holiday):

```bash
git clone https://github.com/jeromio1987/gents-trip-pitch.git
```

After clone of ISZE (post–PRISM fold): **no** `--recurse-submodules` needed. PRISM lives at `03_analytics/Isuzu/prism/`.

---

## What each repo is

| Repo | Use on holiday |
|------|----------------|
| **ISZE** | All work: dashboards (`02_dashboards/`), Jarvis/tools (`04_tools/isze-tools/`), PRISM, docs, allowlisted derived data |
| **mypens** | Personal training/food product |
| **investing-dashboard** | Personal investing app (`Private/investing` locally) |
| **rigged-game** | Accountability / “Rigged Game” environment cockpit (side quest) |
| **gents-trip-pitch** | Trip pitch site — only if you need it |

---

## Intentionally NOT on GitHub

Per ISZE `.gitignore` / `DECISIONS.md`:

- Raw billing / sales `.xlsx` under `01_data/12_raw`, `01_data/04_sales`, etc.
- Living Excel models / planning workbooks
- Secrets (`.env`, tokens)
- Local Claude state (`.claude/`)
- Deploy mirror `07_deploy/**` (source of truth is `02_dashboards/`)

If you need a number that only lives in a raw extract, wait until you’re back on the main machine or copy the file over another channel.

---

## Do not bother cloning (retired / redundant)

| Repo | Why |
|------|-----|
| `jarvis-isze` | Stale Streamlit mirror (last real touch ~2026-03). App is in `ISZE/04_tools/isze-tools/` |
| `isze-dashboard` | Old GitHub Pages deploy mirror. Edit `02_dashboards/` instead |
| Separate `PRISM` clone | After fold, use ISZE only. Archive the old remote |

**Manual archive checklist** (GitHub → Settings → Danger Zone → Archive):

1. [ ] `jeromio1987/jarvis-isze`
2. [ ] `jeromio1987/isze-dashboard`
3. [ ] `jeromio1987/PRISM` (keep archived for history; day-to-day = ISZE)

---

## Day-one on the laptop

1. Clone the three essentials (+ `rigged-game` if you want the side quest).
2. In ISZE: open `INDEX.md` → `00_docs/ROUTING.yaml`.
3. PRISM: `03_analytics/Isuzu/prism/run_prism.ps1` (port **8503**).
4. Jarvis: `cd 04_tools/isze-tools` → `python -m streamlit run app.py` (port **8501**).
5. Before quoting KPIs: check `01_data/00_derived/_verification_report.json` (or legacy `01_data/derived/`).

Pull later:

```bash
cd ISZE && git pull
cd ../mypens && git pull
cd ../investing-dashboard && git pull
```

---

## Push hygiene before you leave

On the main PC, from each essential repo:

```bash
git status
git add -A   # review; never force-add .env / raw xlsx
git commit -m "…"
git push
```

ISZE should be clean enough that a fresh clone is usable without hunting nested remotes.

---

## Holiday-readiness audit (2026-07-24)

### Ready on GitHub

| Repo | Status |
|------|--------|
| `ISZE` | Pushed with PRISM **folded in** (no submodule). Guide: this file. |
| `mypens` | Synced earlier (planner/mobile branch). |
| `investing-dashboard` | Synced earlier. |
| `gents-trip-pitch` | Synced earlier (optional). |

### Blocked / your click needed

| Item | Action |
|------|--------|
| **`rigged-game` (accountability)** | Local git ready at `Private/rigged-game/`. GitHub repo **does not exist yet** (`gh` not logged in). Create empty **private** repo `jeromio1987/rigged-game`, then from that folder: `git push -u origin main`. |
| Archive dead remotes | Archive (don’t delete): `jarvis-isze`, `isze-dashboard`, standalone `PRISM`. |
| `gh auth login` | Needed once if you want agents to create/archive repos for you. |

### Intentionally missing after clone (by design)

- Raw sales / billing `.xlsx` (including local PRISM `data/*.xlsx` — kept on disk, **not** in ISZE git)
- `.env` / API keys for mypens, Jarvis, scrapers — recreate on laptop or copy via password manager
- `07_deploy/Master Dashboard` — use `02_dashboards/` source instead
- `Projects/cockpit` — **not** on GitHub (local only today)

### Workability notes

- **PRISM on holiday:** code + derived CSVs/JSON are in the ISZE clone. Full rebuild from raw billing still needs the main PC’s raw extracts.
- **Jarvis:** run from `ISZE/04_tools/isze-tools/` — do not clone `jarvis-isze`.
- **Quoting KPIs:** prefer `01_data/00_derived/_verification_report.json` / dashboard JSON already in the repo.
