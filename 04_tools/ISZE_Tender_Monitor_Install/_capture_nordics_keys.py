"""Capture Doffin/HILMA Primary keys from Chrome CDP session (debug port 9222)."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

ENV_PATH = Path(__file__).resolve().parent / "nordics_api_keys.env"
EXAMPLE = Path(__file__).resolve().parent / "nordics_api_keys.env.example"


def mask(s: str) -> str:
    return re.sub(
        r"(?i)([a-f0-9]{20,}|[A-Za-z0-9+/_-]{28,}={0,2})",
        lambda m: m.group(0)[:4] + "…MASK…" + m.group(0)[-4:],
        s,
    )


def attach():
    opts = Options()
    opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    return webdriver.Chrome(options=opts)


def list_pages(driver):
    pages = []
    for h in driver.window_handles:
        driver.switch_to.window(h)
        pages.append({"handle": h, "url": driver.current_url, "title": driver.title})
    return pages


def body_text(driver) -> str:
    try:
        return driver.find_element(By.TAG_NAME, "body").text
    except Exception:
        return ""


def click_by_text(driver, *needles: str) -> bool:
    needles_l = [n.lower() for n in needles]
    for el in driver.find_elements(By.CSS_SELECTOR, "a,button,span,div[role='button']"):
        t = (el.text or "").strip().lower()
        if not t:
            continue
        if any(n in t for n in needles_l):
            try:
                el.click()
                time.sleep(1.2)
                return True
            except Exception:
                continue
    return False


def reveal_keys(driver) -> list[str]:
    """Click Show buttons and collect likely subscription key strings."""
    # Azure APIM portal often has "Show" next to Primary key
    for _ in range(6):
        clicked = False
        for el in driver.find_elements(By.CSS_SELECTOR, "button,a,span"):
            t = (el.text or "").strip().lower()
            if t in {"show", "show key", "show primary key", "copy"}:
                try:
                    el.click()
                    clicked = True
                    time.sleep(0.6)
                except Exception:
                    pass
        if not clicked:
            break

    html = driver.page_source
    text = body_text(driver)
    candidates = set()
    # GUID-like and opaque APIM keys
    for pat in (
        r"\b[0-9a-fA-F]{32}\b",
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        r"\b[A-Za-z0-9]{32,64}\b",
    ):
        for m in re.findall(pat, html + "\n" + text):
            if m.lower() in {"subscription", "primary", "secondary"}:
                continue
            if len(m) >= 32:
                candidates.add(m)
    return sorted(candidates, key=len, reverse=True)


def summarize(driver, label: str, page: dict | None):
    if not page:
        print(label, "MISSING")
        return None
    driver.switch_to.window(page["handle"])
    time.sleep(1.5)
    url = driver.current_url
    title = driver.title
    body = body_text(driver)
    low = body.lower()
    print(f"\n=== {label} ===")
    print("URL:", url)
    print("TITLE:", title)
    print("BODY_LEN:", len(body))
    print("SIGN_IN_HINT:", ("sign in" in low[:800]) or ("sign up" in low[:800]))
    print("SUBSCRIPTIONS_HINT:", "subscription" in low)
    print("PRIMARY_HINT:", "primary" in low)
    print("BODY_SNIP:\n", mask(body[:1600]))
    ui = []
    for el in driver.find_elements(By.CSS_SELECTOR, "a,button,h1,h2,h3")[:50]:
        t = (el.text or "").strip()
        if t:
            ui.append(t[:90])
    print("UI:", ui[:35])
    return {"url": url, "title": title, "body": body, "handle": page["handle"]}


def ensure_profile_subscriptions(driver, label: str):
    """Navigate toward Profile → Subscriptions if needed."""
    cur = driver.current_url
    if "/profile" not in cur:
        base = cur.split("/signin")[0].rstrip("/")
        if "dof-notices" in cur or "dof-notices" in label.lower():
            base = "https://dof-notices-prod-api.developer.azure-api.net"
        elif "hilma" in cur or "hilma" in label.lower():
            base = "https://hns-hilma-prod-apim.developer.azure-api.net"
        driver.get(base + "/profile")
        time.sleep(2)
    click_by_text(driver, "subscriptions", "profile")
    time.sleep(1)


def pick_key(cands: list[str], body: str) -> str | None:
    if not cands:
        return None
    # Prefer keys near "Primary"
    for c in cands:
        idx = body.find(c)
        if idx < 0:
            # maybe only in HTML
            continue
        window = body[max(0, idx - 80) : idx + 80].lower()
        if "primary" in window:
            return c
    # fallback: longest opaque token that isn't a common word
    for c in cands:
        if re.fullmatch(r"[0-9a-fA-F-]{32,}", c) or len(c) >= 40:
            return c
    return cands[0]


def write_env(doffin: str | None, hilma: str | None):
    template = EXAMPLE.read_text(encoding="utf-8") if EXAMPLE.exists() else (
        "ISZE_DOFFIN_API_KEY=\nISZE_HILMA_API_KEY=\n"
    )
    lines = []
    for line in template.splitlines():
        if line.startswith("ISZE_DOFFIN_API_KEY="):
            lines.append(f"ISZE_DOFFIN_API_KEY={doffin or ''}")
        elif line.startswith("ISZE_HILMA_API_KEY="):
            lines.append(f"ISZE_HILMA_API_KEY={hilma or ''}")
        else:
            lines.append(line)
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        "WROTE_ENV",
        ENV_PATH,
        "doffin_len=",
        len(doffin or ""),
        "hilma_len=",
        len(hilma or ""),
    )


def main():
    driver = attach()
    pages = list_pages(driver)
    print("PAGES:", json.dumps([{k: v for k, v in p.items() if k != "handle"} for p in pages], indent=2))

    doffin_page = next((p for p in pages if "dof-notices" in p["url"]), None)
    hilma_page = next((p for p in pages if "hns-hilma" in p["url"] or "hilma" in p["url"]), None)

    dinfo = summarize(driver, "DOFFIN", doffin_page)
    hinfo = summarize(driver, "HILMA", hilma_page)

    doffin_key = hilma_key = None

    if dinfo:
        ensure_profile_subscriptions(driver, "DOFFIN")
        # try products subscribe path if empty
        click_by_text(driver, "products", "apis")
        time.sleep(1)
        # back to profile
        driver.get("https://dof-notices-prod-api.developer.azure-api.net/profile")
        time.sleep(2)
        click_by_text(driver, "subscriptions")
        time.sleep(1)
        cands = reveal_keys(driver)
        print("DOFFIN_CAND_COUNT", len(cands))
        doffin_key = pick_key(cands, body_text(driver) + driver.page_source)
        print("DOFFIN_KEY_FOUND", bool(doffin_key), "len", len(doffin_key or ""))

    if hinfo:
        driver.switch_to.window(hilma_page["handle"])
        ensure_profile_subscriptions(driver, "HILMA")
        driver.get("https://hns-hilma-prod-apim.developer.azure-api.net/profile")
        time.sleep(2)
        click_by_text(driver, "subscriptions")
        time.sleep(1)
        cands = reveal_keys(driver)
        print("HILMA_CAND_COUNT", len(cands))
        hilma_key = pick_key(cands, body_text(driver) + driver.page_source)
        print("HILMA_KEY_FOUND", bool(hilma_key), "len", len(hilma_key or ""))

    if doffin_key or hilma_key:
        # preserve existing if only one found
        existing = {}
        if ENV_PATH.exists():
            for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, _, v = line.partition("=")
                    existing[k.strip()] = v.strip()
        write_env(
            doffin_key or existing.get("ISZE_DOFFIN_API_KEY") or None,
            hilma_key or existing.get("ISZE_HILMA_API_KEY") or None,
        )
    else:
        print("NO_KEYS_CAPTURED — likely signed out in debug profile")


if __name__ == "__main__":
    main()
