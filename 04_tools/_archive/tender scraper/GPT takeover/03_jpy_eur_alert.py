"""
JPY/EUR Exchange Rate Monitor — ISZE / Isuzu Europe
Fetches live rate, checks against thresholds, sends email alert if triggered.
Also logs history for trend tracking and exports to CSV for Power BI.

Data source: exchangerate-api.com (free tier, no API key needed for basic endpoint)
Fallback: frankfurter.app (ECB data, free, no key needed)

Usage:
    pip install requests --break-system-packages
    python 03_jpy_eur_alert.py

Schedule: Run daily via Windows Task Scheduler or cron.
"""

import json
import csv
import datetime
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

try:
    import requests
except ImportError:
    print("Run: pip install requests --break-system-packages")
    exit()

# ─────────────────────────────────────────────
# CONFIGURATION — edit these
# ─────────────────────────────────────────────

# Rate is expressed as JPY per 1 EUR (e.g. 163.5 means 1 EUR = 163.5 JPY)
# Higher = stronger EUR = better for ISZE (import costs from Japan decrease)
# Lower = weaker EUR / stronger JPY = ISZE pricing pressure

RATE_THRESHOLDS = {
    # Alert when EUR weakens significantly (bad for ISZE — parts get expensive)
    "alert_low":    155.0,   # 🔴 Strong alert: margins under pressure
    "warn_low":     158.0,   # 🟡 Warning: watch closely
    # Alert when EUR strengthens significantly (opportunity window)
    "warn_high":    168.0,   # 🟡 Opportunity: favourable for pricing review
    "alert_high":   172.0,   # 🔴 Strong alert: consider locking in pricing
}

# Baseline rate for ISZE internal pricing reference
ISZE_INTERNAL_RATE = 163.70   # matches Israel pricing formula in ISZE bible

# Email configuration — update with your SMTP settings
EMAIL_CONFIG = {
    "enabled": False,          # Set True to activate
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 465,
    "sender": "your@email.com",
    "password": "your_app_password",   # Use App Password for Gmail
    "recipients": ["jerome@isze.com"],
    "cc": [],
}

# File paths for history log
HISTORY_FILE = Path("jpy_eur_history.json")
CSV_EXPORT_FILE = Path("jpy_eur_history.csv")

# ─────────────────────────────────────────────
# RATE FETCHING
# ─────────────────────────────────────────────

def fetch_rate_primary() -> dict:
    """
    Primary: exchangerate-api.com (free tier)
    Returns EUR/JPY rate + timestamp.
    """
    url = "https://open.er-api.com/v6/latest/EUR"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if data.get("result") != "success":
        raise ValueError(f"API error: {data}")
    jpy_rate = data["rates"]["JPY"]
    return {
        "rate": round(jpy_rate, 4),
        "source": "exchangerate-api.com",
        "timestamp": data.get("time_last_update_utc", datetime.datetime.utcnow().isoformat()),
        "base": "EUR",
        "quote": "JPY",
    }


def fetch_rate_fallback() -> dict:
    """
    Fallback: frankfurter.app (ECB data)
    """
    url = "https://api.frankfurter.app/latest?from=EUR&to=JPY"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    jpy_rate = data["rates"]["JPY"]
    return {
        "rate": round(jpy_rate, 4),
        "source": "frankfurter.app (ECB)",
        "timestamp": data.get("date", datetime.date.today().isoformat()),
        "base": "EUR",
        "quote": "JPY",
    }


def get_rate() -> dict:
    """Try primary source, fall back on error."""
    try:
        return fetch_rate_primary()
    except Exception as e:
        print(f"  Primary source failed ({e}), trying fallback...")
        return fetch_rate_fallback()


# ─────────────────────────────────────────────
# RATE ANALYSIS
# ─────────────────────────────────────────────

def classify_rate(rate: float) -> tuple[str, str, str]:
    """
    Returns (level, emoji, message) based on configured thresholds.
    """
    t = RATE_THRESHOLDS
    if rate <= t["alert_low"]:
        return "ALERT_LOW", "🔴", f"EUR critically weak — {rate:.2f} JPY/EUR (threshold: {t['alert_low']})"
    elif rate <= t["warn_low"]:
        return "WARN_LOW", "🟡", f"EUR weakening — {rate:.2f} JPY/EUR (watch threshold: {t['warn_low']})"
    elif rate >= t["alert_high"]:
        return "ALERT_HIGH", "🔴", f"EUR exceptionally strong — {rate:.2f} JPY/EUR (threshold: {t['alert_high']})"
    elif rate >= t["warn_high"]:
        return "WARN_HIGH", "🟡", f"EUR strengthening — {rate:.2f} JPY/EUR (opportunity: {t['warn_high']})"
    else:
        return "NORMAL", "🟢", f"Rate within normal range — {rate:.2f} JPY/EUR"


def calc_vs_baseline(rate: float) -> dict:
    """
    Calculate impact vs. ISZE internal rate baseline.
    Positive delta = EUR stronger than baseline = favourable for ISZE.
    """
    delta = rate - ISZE_INTERNAL_RATE
    delta_pct = delta / ISZE_INTERNAL_RATE * 100
    return {
        "baseline": ISZE_INTERNAL_RATE,
        "delta": round(delta, 2),
        "delta_pct": round(delta_pct, 2),
        "impact": "favourable" if delta > 0 else "unfavourable",
    }


# ─────────────────────────────────────────────
# HISTORY LOG
# ─────────────────────────────────────────────

def load_history() -> list[dict]:
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def append_history(entry: dict):
    history = load_history()
    history.append(entry)
    # Keep last 365 days only
    cutoff = (datetime.date.today() - datetime.timedelta(days=365)).isoformat()
    history = [h for h in history if h.get("date", "") >= cutoff]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def export_csv():
    """Export history to CSV for Power BI."""
    history = load_history()
    if not history:
        return
    keys = ["date", "rate", "source", "level", "delta_vs_baseline", "delta_pct"]
    with open(CSV_EXPORT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for entry in history:
            writer.writerow({k: entry.get(k, "") for k in keys})
    print(f"  CSV exported: {CSV_EXPORT_FILE}")


def calc_moving_avg(history: list[dict], days: int = 7) -> Optional[float]:
    """Calculate N-day moving average from history."""
    cutoff = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    recent = [h["rate"] for h in history if h.get("date", "") >= cutoff]
    if not recent:
        return None
    return round(sum(recent) / len(recent), 4)


# ─────────────────────────────────────────────
# EMAIL ALERT
# ─────────────────────────────────────────────

def build_email_body(rate_info: dict, level: str, message: str,
                     baseline_info: dict, history: list[dict]) -> str:
    ma7 = calc_moving_avg(history, 7)
    ma30 = calc_moving_avg(history, 30)

    lines = [
        f"ISZE Exchange Rate Alert — JPY/EUR",
        f"{'=' * 45}",
        f"",
        f"Current rate:  {rate_info['rate']:.4f} JPY/EUR",
        f"Status:        {message}",
        f"",
        f"vs. ISZE baseline ({baseline_info['baseline']} JPY/EUR):",
        f"  Delta:       {baseline_info['delta']:+.2f} JPY ({baseline_info['delta_pct']:+.2f}%)",
        f"  Impact:      {baseline_info['impact'].upper()}",
        f"",
        f"Moving averages:",
        f"  7-day avg:   {ma7:.4f}" if ma7 else "  7-day avg:   insufficient data",
        f"  30-day avg:  {ma30:.4f}" if ma30 else "  30-day avg:  insufficient data",
        f"",
        f"Thresholds:",
        f"  Alert low:   {RATE_THRESHOLDS['alert_low']} (EUR critically weak)",
        f"  Warn low:    {RATE_THRESHOLDS['warn_low']}",
        f"  Warn high:   {RATE_THRESHOLDS['warn_high']}",
        f"  Alert high:  {RATE_THRESHOLDS['alert_high']} (EUR strong / opportunity)",
        f"",
        f"Source: {rate_info['source']}",
        f"As of: {rate_info['timestamp']}",
        f"",
        f"{'─' * 45}",
        f"Pricing note: Israel formula uses ROUND(Base / {baseline_info['baseline']} × Factor, 2).",
        f"A rate of {rate_info['rate']:.2f} means parts are "
        f"{'cheaper to import' if baseline_info['delta'] > 0 else 'more expensive to import'} "
        f"vs. baseline by ~{abs(baseline_info['delta_pct']):.1f}%.",
    ]
    return "\n".join(lines)


def send_alert(body: str, level: str, rate: float):
    cfg = EMAIL_CONFIG
    if not cfg["enabled"]:
        print("  Email disabled — set EMAIL_CONFIG['enabled'] = True to activate")
        return

    severity = "⚠️ ACTION REQUIRED" if "ALERT" in level else "ℹ️ Notice"
    subject = f"[ISZE Rate Monitor] {severity} — JPY/EUR = {rate:.2f}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["sender"]
    msg["To"] = ", ".join(cfg["recipients"])
    if cfg["cc"]:
        msg["Cc"] = ", ".join(cfg["cc"])
    msg.attach(MIMEText(body, "plain"))

    all_recipients = cfg["recipients"] + cfg.get("cc", [])
    try:
        with smtplib.SMTP_SSL(cfg["smtp_host"], cfg["smtp_port"]) as server:
            server.login(cfg["sender"], cfg["password"])
            server.sendmail(cfg["sender"], all_recipients, msg.as_string())
        print(f"  Alert email sent to {all_recipients}")
    except Exception as e:
        print(f"  Email failed: {e}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

from typing import Optional

def main():
    today = datetime.date.today().isoformat()
    print(f"\nJPY/EUR Rate Monitor — {today}")
    print(f"ISZE internal baseline: {ISZE_INTERNAL_RATE} JPY/EUR\n")

    # Fetch
    print("  Fetching rate...")
    rate_info = get_rate()
    rate = rate_info["rate"]
    print(f"  Rate: {rate:.4f} JPY/EUR (source: {rate_info['source']})")

    # Classify
    level, emoji, message = classify_rate(rate)
    print(f"  Status: {emoji} {message}")

    # Baseline comparison
    baseline_info = calc_vs_baseline(rate)
    print(f"  vs. baseline ({ISZE_INTERNAL_RATE}): {baseline_info['delta']:+.2f} JPY "
          f"({baseline_info['delta_pct']:+.2f}%) — {baseline_info['impact']}")

    # Load history for moving averages
    history = load_history()
    ma7 = calc_moving_avg(history, 7)
    ma30 = calc_moving_avg(history, 30)
    if ma7:
        print(f"  7-day avg: {ma7:.4f} | 30-day avg: {ma30:.4f}")

    # Append to history
    history_entry = {
        "date": today,
        "rate": rate,
        "source": rate_info["source"],
        "level": level,
        "delta_vs_baseline": baseline_info["delta"],
        "delta_pct": baseline_info["delta_pct"],
    }
    append_history(history_entry)
    print(f"  History updated: {HISTORY_FILE}")

    # Export CSV for Power BI
    export_csv()

    # Send alert if threshold breached
    if level != "NORMAL":
        print(f"\n  {emoji} Threshold breached — sending alert...")
        body = build_email_body(rate_info, level, message, baseline_info, history)
        print("\n" + body)
        send_alert(body, level, rate)
    else:
        print(f"\n  Rate normal. No alert sent.")

    # Print summary
    print(f"\n{'─' * 50}")
    print(f"  Summary for {today}")
    print(f"  JPY/EUR:   {rate:.4f}")
    print(f"  Status:    {emoji} {level}")
    print(f"  vs. ISZE:  {baseline_info['delta']:+.2f} ({baseline_info['impact']})")
    print(f"{'─' * 50}\n")

    return {
        "date": today,
        "rate": rate,
        "level": level,
        "baseline_delta": baseline_info["delta"],
    }


if __name__ == "__main__":
    main()


# ─────────────────────────────────────────────
# WINDOWS TASK SCHEDULER SETUP (copy-paste)
# ─────────────────────────────────────────────
#
# Run this in PowerShell to schedule daily at 08:00:
#
# $action = New-ScheduledTaskAction -Execute "python.exe" `
#     -Argument "C:\path\to\03_jpy_eur_alert.py" `
#     -WorkingDirectory "C:\path\to\scripts"
# $trigger = New-ScheduledTaskTrigger -Daily -At "08:00"
# $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
# Register-ScheduledTask -TaskName "ISZE JPY Rate Monitor" `
#     -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest
#
# To run immediately: Start-ScheduledTask -TaskName "ISZE JPY Rate Monitor"
