# Jarvis — ISZE Internal Tool

Streamlit multi-page app for Isuzu Motors Europe (ISZE) sales work. Claude-powered drafting, SPA evaluation, and project tracking.

**Canonical location:** `C:\Users\jerom\Desktop\claude\ISZE\Tools\isze-tools\`
This is the single source of truth. The old `Prive\jarvis\` copy is deprecated (superseded by this folder).

---

## Run

```powershell
cd "C:\Users\jerom\Desktop\claude\ISZE\Tools\isze-tools"
python -m streamlit run app.py
```

> Use `python -m streamlit`, **not** bare `streamlit` — the `streamlit` shim is not on PATH on this machine.

App opens at http://localhost:8501.

## Setup

```powershell
pip install -r requirements.txt
copy .env.example .env   # then fill in your keys
```

`.env` keys (see `.env.example`):

| Key | Required | Used for |
|-----|----------|----------|
| `ANTHROPIC_API_KEY` | yes | Email Drafter, SPA Assistant (Claude) |
| `OPENAI_API_KEY` | optional | fallback / secondary model |

`.env` is git-ignored — never commit keys.

## Pages

| Page | File | What it does |
|------|------|-------------|
| Home | `app.py` | Landing / navigation |
| Stack | `pages/1_Stack.py` | ISZE project tracker — status, risk, owner per initiative |
| Email Drafter | `pages/2_Email_Drafter.py` | Claude-drafted emails to IML / ITUK / distributors |
| SPA Assistant | `pages/3_SPA_Assistant.py` | Special Price Agreement evaluator — ROI, margin floor, FX, approval routing |
| Opportunity Radar | `pages/4_Opportunity_Radar.py` | Opportunity surfacing |
| NOx SPA Optimizer | `pages/5_NOx_SPA_Optimizer.py` | NOx sensor SPA — entity margin split, breakeven qty/price per PN |
| Competitive Parts | `pages/6_Competitive_Parts.py` | Competitive parts view |

## Deploy

`deploy_to_github.py` pushes the app to a GitHub repo (`jeromio1987/jarvis-isze`) for Streamlit Cloud.

```powershell
python deploy_to_github.py <GITHUB_PAT>
```

> ⚠️ The repo is currently created **public** (`private: False`) for a tool marked "not for external distribution." Review before deploying — see `ROADMAP.md`.

## Notes

- `ROADMAP.md` holds the forward plan (data-out-of-code, SPA history, integration).
- Not for external distribution.
