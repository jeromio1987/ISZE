# Holiday laptop — easiest sync

**Purpose:** work from another machine with Claude + Cursor. Not for sharing, Pages, or Streamlit Cloud.

**Verdict:** Prefer **GitHub clones** of the three bucket repos. Do **not** copy the whole Claude map as the primary plan.

**Last updated:** 2026-08-01 (repos consolidated to 3)

---

## What you have on GitHub (only these)

| Repo | URL | Use on holiday |
|------|-----|----------------|
| **ISZE** | https://github.com/jeromio1987/ISZE | All work: dashboards, PRISM, tools, docs, allowlisted derived data |
| **mypens** | https://github.com/jeromio1987/mypens | myPENS product |
| **private** | https://github.com/jeromio1987/private | Personal (health, design, backups, side notes) |

Old standalone remotes (`investing-dashboard`, `accountability`, `PRISM`, `jarvis-isze`, …) were **deleted 2026-08-01**. Content that mattered already lives under ISZE / private / mypens locally — push before you leave if it isn’t on GitHub yet.

---

## Can you work “almost full”?

**Yes, for coding / dashboards / myPENS / docs**, if you:

1. Push everything you need from the home PC **before** you leave  
2. Clone the three repos on the laptop  
3. Bring secrets via password manager (never git)  
4. Import a Cursor Profile export  

**No / limited** for:

| Gap | Why |
|-----|-----|
| Raw sales / billing `.xlsx` | Intentionally not in git — rebuild pipelines need the main PC |
| Fresh Autodoc scrape | Cloudflare-blocked; frozen tables only |
| `Projects/cockpit` | Local-only today (not on GitHub) |
| Investing app | Standalone GitHub repo deleted — fold into `private` or `Projects` and **push** if you need it away |
| Local Cursor chat history | Does not follow Pro login — only Cloud Agents do |

Dashboards under `ISZE/02_dashboards/` work offline (local `_ui/` libs). KPI quoting: use `01_data/00_derived/` / dashboard JSON already in the clone.

---

## Simplest stack

| Layer | Method |
|-------|--------|
| Code + dashboards | `git clone` the three repos |
| Cursor Pro | Same account → Cloud Agents work across machines |
| Editor setup | Export Profile on home PC → import on laptop |
| Secrets / `.env` | Password manager or USB — never commit |
| USB full Claude copy | Plan B only (heavy, path mess) |

---

## Friday on the main PC (before you leave)

1. **Push dirty work** (review; never force-add `.env` / raw sales xlsx):

```powershell
cd C:\Users\jerom\Desktop\claude\ISZE
git status
git push   # this machine was ahead of origin — push before travel

cd C:\Users\jerom\Desktop\claude\mypens   # or Projects\mypens
git status
git push

cd C:\Users\jerom\Desktop\claude\Private
git status
git push
```

2. If you need **investing** on holiday: copy/commit it under `Private` or `Projects`, push `private` (or create a folder in mypens — your call). There is **no** `investing-dashboard` remote anymore.

3. **Export Cursor Profile:** Command Palette → `Preferences: Open Profiles (UI)` → Export → USB / OneDrive.

4. **Secrets:** mypens, Jarvis, scrapers, `gh` token if needed — password manager.

5. **Optional USB:** only raw extracts you know you’ll need; otherwise leave them home.

---

## Day-one on the holiday laptop

```powershell
git clone https://github.com/jeromio1987/ISZE.git
git clone https://github.com/jeromio1987/mypens.git
git clone https://github.com/jeromio1987/private.git
```

1. Install Cursor → same Pro account → import Profile.  
2. `gh auth login` (or paste a PAT with `repo`) — needed for push/pull and Cloud Agents that use GitHub.  
3. Open `ISZE` → `INDEX.md`.  
4. Drop `.env` files; re-auth MCP if you use it.  
5. PRISM: `03_analytics\Isuzu\prism\run_prism.ps1` (port **8503**).  
6. Jarvis: `cd 04_tools\isze-tools` → `python -m streamlit run app.py` (port **8501**).  

While away:

```powershell
git pull
# … work …
git push
```

Prefer **Cloud Agents** for threads you might continue from phone/home. Local sidebar chats stay on that laptop only.

---

## Intentionally NOT on GitHub

- Raw billing / sales `.xlsx`  
- Living Excel planning models  
- Secrets (`.env`, tokens)  
- Local Claude state (`.claude/`)  
- Deploy mirror `07_deploy/**` (edit `02_dashboards/` only)  
- `Projects/cockpit` (unless you add it later)

---

## What Cursor syncs vs not

**Follows Pro login:** Cloud Agents, cloud dashboard, GitHub integration for cloud runs.

**Per machine:** local Agent chats, extensions/settings (unless Profile import), `~/.cursor` rules/skills/MCP, memories.

Project `.cursor/` rules inside ISZE/mypens arrive with the **git clone**.
