> **Recovery note:** reconstructed from the assistant's chat summary plus a real follow-up exchange (session `local_49179af0`), not the original file. Filename at the time was `ISZE_Feedback_May2026.md`. Date approximate: ~May 2026, after run 1.

# ISZE Feedback — May 2026 (run 2, reconstructed summary)

**Doing well:** strategic framing (Kosha execution-credibility play correct), the ITUK dispute (well-calibrated, don't over-engineer), catching the UIO data gap (17K → 22K, a 31% correction to the universe), AIM progress, and building institutional memory into the skills/context system. Also praised for using AI in the right mode — sparring, not just transcription.

**The problems, ranked by cost at the time:**
1. **CLAUDE.md had four wrong data points for 6+ weeks already** (oil filter capture rate, lubricants margin, AIM CY2024 status, UIO version) — every automated session was running on stale data. Called "your most expensive maintenance failure" and noted it takes ~15 minutes to fix.
2. **Operational closure named as the structural pattern to break** — analysis consistently excellent, but the email doesn't get sent, the meeting doesn't get booked. 6–9 weeks of open items (ITUK response, Yoshimoto, lubricants decision) described as solved-but-unsent.
3. **Infrastructure building flagged as a possible displacement activity** — new dashboards/automations tending to appear at the point where uncomfortable operational action is due.
4. Tender scraper had returned zero results for months due to a sandbox proxy block — called worse than no scraper, since it creates a false impression of coverage.
5. Lubricants — "awaiting IML go-ahead" since February, nothing left to analyze, needs a written deadline to Tanaka/Hiratsuka rather than another review.

**Closing line at the time:** *"The gap is not in knowing what to do. It's in doing it."*

## Follow-up exchange (real, from the same session)

Jérôme pushed back: *"well I already asked multiple times to fix it"* regarding the CLAUDE.md staleness.

The assistant tried to fix it live and hit a structural wall: no workspace folder was connected in that automated session, so neither bash nor the file tools could reach the CLAUDE.md file on disk. Conclusion reached in that session: **this is the actual reason the fix never lands** — every automated run that finds the stale data also can't write the correction, because scheduled/automated sessions never have a workspace folder mounted (that has to be connected manually by Jérôme in an interactive session). The four specific corrections identified at the time:
1. Oil filter capture rate: `0.3%` → confirmed CY2024/CY2025 figures (~9.8% CY2024 / 17.3% CY2025 at that point)
2. Lubricants margin: `unverified` → 13% (per March confirmation)
3. AIM status: remove "CY2024 still needed" — cross-validated in March 2026
4. UIO version: `v9` → `v17` (canonical since 20 April at that point)

*(Note: today's run, 17 Jul 2026, confirms this general class of drift — different specific numbers now — is still present roughly ten weeks later. See `feedback_history_00_INDEX.md`.)*
