# Holiday laptop — easiest sync

**Purpose:** private backup + work from another machine. Not for sharing, Pages, or Streamlit Cloud.

**Verdict:** Prefer **GitHub clones** over copying the whole Claude map. Cursor Pro login does **not** sync local chats/settings.

**Last updated:** 2026-07-26

---

## Simplest stack

| Layer | Method | Why |
|-------|--------|-----|
| **ISZE / mypens / investing** | `git clone` from GitHub | Clean history, push/pull while away, Cloud Agents can use remotes |
| **Cursor Pro** | Same account login | Plan + Cloud Agents (cloud icons in Agents sidebar) |
| **Editor setup** | Export Profile once, import on laptop | Settings/extensions do **not** follow the account |
| **Secrets / .env** | Password manager or USB stick | Never in git |
| **Whole Claude map USB copy** | Optional Plan B only | Heavy, messy paths, includes stuff git ignores on purpose |

Copying the whole Claude tree works as a **one-shot dump**, but it is worse for holiday work: huge size, wrong paths break agent chat reattachment, and you still need GitHub for day-to-day sync. Keep USB as Plan B, not primary.

---

## Clone these (essentials)

```bash
git clone https://github.com/jeromio1987/ISZE.git
git clone https://github.com/jeromio1987/mypens.git
git clone https://github.com/jeromio1987/investing-dashboard.git
```

Optional fun side quest:

```bash
git clone https://github.com/jeromio1987/accountability.git
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
| **accountability** | Rigged Game environment cockpit (side quest; local folder `Private/rigged-game`) |
| **gents-trip-pitch** | Trip pitch site — only if you need it |

---

## What Cursor does / does not sync

**Follows Pro login**

- Cloud Agents (cloud icon in Agents sidebar)
- Cloud agent dashboard / secrets / spend limits
- GitHub integration for cloud runs ([cursor.com/dashboard/integrations](https://cursor.com/dashboard/integrations))

**Stays per machine** (Profile / copy / recreate)

- Local Agent chats (no cloud icon)
- Editor settings, keybindings, extensions
- User Rules / Skills under `~/.cursor`
- Local `mcp.json` (re-auth OAuth / API keys)
- Memories / local AI context

Project rules/skills under `.cursor/` in ISZE arrive with the **Git clone**.

Do **not** rely on VS Code–style Settings Sync. Prefer one **Profile export** from the home machine → import on the holiday laptop.

---

## Friday on the main PC (before you leave)

1. **Push dirty work** in each essential repo (review; never force-add `.env` / raw sales xlsx):
   - `ISZE`
   - `mypens`
   - `investing-dashboard`
   - optional: `accountability`
2. **Export Cursor Profile:** Command Palette → `Preferences: Open Profiles (UI)` → Export (or File → Share → Export Profile). Put the `.code-profile` on USB / OneDrive.
3. **Secrets:** copy or recreate `.env` / API tokens via password manager (mypens, Jarvis, scrapers, `$ISZE_GH_TOKEN` if you use upload scripts).
4. **Optional USB extras** (only if you need them on holiday — not in git by design):
   - Derived numbers already in the repo are enough for most KPI quoting
   - Raw billing / PRISM `data/*.xlsx` stay on main PC unless you explicitly copy a small set
   - `Projects/cockpit` is local-only today

Push hygiene per repo:

```bash
git status
git add -A   # review; never force-add .env / raw xlsx
git commit -m "…"
git push
```

ISZE should be clean enough that a fresh clone is usable without hunting nested remotes.

---

## Day-one on the holiday laptop

1. Clone the three essentials (+ `accountability` if you want the side quest).
2. Install Cursor → sign in (same Pro account).
3. Import the Profile export.
4. Open `ISZE` → `INDEX.md` → `00_docs/ROUTING.yaml`.
5. Drop `.env` files where needed; re-auth local MCP if you use it.
6. PRISM: `03_analytics/Isuzu/prism/run_prism.ps1` (port **8503**).
7. Jarvis: `cd 04_tools/isze-tools` → `python -m streamlit run app.py` (port **8501**).
8. Before quoting KPIs: check `01_data/00_derived/_verification_report.json` (or legacy `01_data/derived/`). Full pipeline rebuild from raw billing still needs the main PC.

Pull later:

```bash
cd ISZE && git pull
cd ../mypens && git pull
cd ../investing-dashboard && git pull
```

While away: `git pull` / `git push` as usual. Prefer **Cloud Agents** for work you may continue from phone/home PC; treat local sidebar chats (no cloud icon) as **this-laptop-only**.

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

Also do not:

- Rely on VS Code–style “Settings Sync” as the strategy
- Expect Agents sidebar local chats from the main PC to appear automatically

---

## Holiday-readiness audit (2026-07-26)

### Ready on GitHub

| Repo | Status |
|------|--------|
| `ISZE` | On GitHub with PRISM **folded in** (no submodule). Guide: this file. |
| `mypens` | Remote exists; **local tree dirty** — push before travel if you need current work |
| `investing-dashboard` | Clean vs `origin/main` (synced) |
| `accountability` | On GitHub: https://github.com/jeromio1987/accountability |
| `gents-trip-pitch` | Optional; synced earlier |

### Your clicks still needed (Friday)

| Item | Action |
|------|--------|
| **ISZE dirty** | Many IDS/ranking + dashboard changes uncommitted on branch `cursor/loops-package-allowlist-self-patch` — commit + push (or merge to `main` + push) before leave |
| **mypens dirty** | Continental mobile / food feed / audit screens etc. not committed — push before leave if needed on holiday |
| **Cursor Profile** | Export from main PC → USB / OneDrive → import on laptop |
| **Secrets** | `.env` / API keys via password manager (not git) |
| Archive dead remotes | GitHub → Settings → Danger Zone → Archive: `jarvis-isze`, `isze-dashboard`, standalone `PRISM` |

### Intentionally missing after clone (by design)

- Raw sales / billing `.xlsx` (including local PRISM `data/*.xlsx` — kept on disk, **not** in ISZE git)
- `.env` / API keys for mypens, Jarvis, scrapers — recreate on laptop or copy via password manager
- `07_deploy/Master Dashboard` — use `02_dashboards/` source instead
- `Projects/cockpit` — **not** on GitHub (local only today)

### Workability notes

- **PRISM on holiday:** code + derived CSVs/JSON are in the ISZE clone. Full rebuild from raw billing still needs the main PC’s raw extracts.
- **Jarvis:** run from `ISZE/04_tools/isze-tools/` — do not clone `jarvis-isze`.
- **Quoting KPIs:** prefer `01_data/00_derived/_verification_report.json` / dashboard JSON already in the repo.
