"""Subscribe Doffin Public Api + HILMA AVP-Read via Chrome CDP; write nordics_api_keys.env.

Attaches to chrome --remote-debugging-port=9222 (Default profile).
Does NOT use Cursor's isolated browser.
Never prints full key values.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

DIR = Path(__file__).resolve().parent
ENV_PATH = DIR / "nordics_api_keys.env"
EXAMPLE = DIR / "nordics_api_keys.env.example"
RUNLOG = DIR / "_OVERNIGHT_RUNLOG.md"

DOFFIN = "https://dof-notices-prod-api.developer.azure-api.net"
HILMA = "https://hns-hilma-prod-apim.developer.azure-api.net"


def log(msg: str) -> None:
    line = f"- {time.strftime('%H:%M:%S')} {msg}"
    print(msg)
    try:
        if not RUNLOG.exists():
            RUNLOG.write_text(
                "# Overnight runlog — Nordics keys + scrape\n\n", encoding="utf-8"
            )
        with RUNLOG.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


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


def body(driver) -> str:
    try:
        return driver.find_element(By.TAG_NAME, "body").text
    except Exception:
        return ""


def click_text(driver, *needles: str, exact: bool = False) -> bool:
    needles_l = [n.lower() for n in needles]
    for sel in ("button", "a", "span", "div[role='button']", "label", "li"):
        for el in driver.find_elements(By.CSS_SELECTOR, sel):
            t = (el.text or "").strip()
            if not t:
                continue
            tl = t.lower()
            hit = any(tl == n if exact else n in tl for n in needles_l)
            if not hit:
                continue
            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", el
                )
                time.sleep(0.3)
                el.click()
                time.sleep(1.0)
                return True
            except Exception:
                try:
                    driver.execute_script("arguments[0].click();", el)
                    time.sleep(1.0)
                    return True
                except Exception:
                    continue
    return False


def click_product(driver, want: str, avoid: list[str]) -> bool:
    """Click a product card/link matching want, skipping avoid substrings."""
    want_l = want.lower()
    avoid_l = [a.lower() for a in avoid]
    candidates = []
    for el in driver.find_elements(By.CSS_SELECTOR, "a,button,h1,h2,h3,h4,div,span,li"):
        t = (el.text or "").strip()
        if not t or len(t) > 200:
            continue
        tl = t.lower()
        if want_l not in tl:
            continue
        if any(a in tl for a in avoid_l):
            continue
        candidates.append((len(t), el, t))
    candidates.sort(key=lambda x: x[0])
    for _, el, t in candidates:
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", el
            )
            time.sleep(0.2)
            el.click()
            time.sleep(1.2)
            log(f"clicked product-ish: {t[:80]!r}")
            return True
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", el)
                time.sleep(1.2)
                log(f"js-clicked product-ish: {t[:80]!r}")
                return True
            except Exception:
                continue
    return False


def reveal_and_collect_keys(driver) -> list[str]:
    for _ in range(8):
        clicked = False
        for el in driver.find_elements(By.CSS_SELECTOR, "button,a,span"):
            t = (el.text or "").strip().lower()
            if t in {"show", "show key", "show primary key", "copy", "reveal"}:
                try:
                    el.click()
                    clicked = True
                    time.sleep(0.5)
                except Exception:
                    pass
        if not clicked:
            break
    blob = driver.page_source + "\n" + body(driver)
    cands = set()
    for pat in (
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        r"\b[0-9a-fA-F]{32}\b",
        r"\b[A-Za-z0-9_\-]{32,64}\b",
    ):
        for m in re.findall(pat, blob):
            low = m.lower()
            if low in {"subscription", "primary", "secondary", "public-api", "avp-read"}:
                continue
            if len(m) >= 32:
                cands.add(m)
    return sorted(cands, key=len, reverse=True)


def pick_primary(cands: list[str], text: str) -> str | None:
    if not cands:
        return None
    for c in cands:
        idx = text.find(c)
        if idx < 0:
            continue
        window = text[max(0, idx - 100) : idx + 100].lower()
        if "primary" in window:
            return c
    for c in cands:
        if re.fullmatch(r"[0-9a-fA-F-]{32,}", c) or len(c) >= 40:
            return c
    return cands[0]


def write_env(doffin: str | None, hilma: str | None) -> None:
    template = (
        EXAMPLE.read_text(encoding="utf-8")
        if EXAMPLE.exists()
        else "ISZE_DOFFIN_API_KEY=\nISZE_HILMA_API_KEY=\n"
    )
    existing: dict[str, str] = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()
    d = doffin or existing.get("ISZE_DOFFIN_API_KEY") or ""
    h = hilma or existing.get("ISZE_HILMA_API_KEY") or ""
    lines = []
    for line in template.splitlines():
        if line.startswith("ISZE_DOFFIN_API_KEY="):
            lines.append(f"ISZE_DOFFIN_API_KEY={d}")
        elif line.startswith("ISZE_HILMA_API_KEY="):
            lines.append(f"ISZE_HILMA_API_KEY={h}")
        else:
            lines.append(line)
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"WROTE_ENV doffin_len={len(d)} hilma_len={len(h)}")


def ensure_signed_in(driver, base: str) -> bool:
    driver.get(base + "/profile")
    time.sleep(2.5)
    b = body(driver).lower()
    if "sign in" in b[:1200] and "sign out" not in b and "add subscription" not in b:
        log(f"SIGN_IN_REQUIRED at {base}")
        return False
    log(f"profile ok at {base} body_len={len(b)}")
    return True


def subscribe_doffin(driver) -> str | None:
    log("=== DOFFIN subscribe Public Api ===")
    if not ensure_signed_in(driver, DOFFIN):
        return None

    # Prefer Add subscription from profile when empty
    if "don't have subscriptions" in body(driver).lower() or "do not have subscriptions" in body(driver).lower() or "add subscription" in body(driver).lower():
        click_text(driver, "add subscription")
        time.sleep(1.5)

    # Product page fallback
    if "public" not in body(driver).lower():
        driver.get(DOFFIN + "/products")
        time.sleep(2)
    if not click_product(
        driver,
        "public api",
        avoid=["notices api", "esender", "publication", "publish"],
    ):
        # try Products nav then Public Api
        click_text(driver, "products")
        time.sleep(1)
        if not click_product(
            driver,
            "public",
            avoid=["notices api", "esender", "publication to doffin"],
        ):
            log("DOFFIN: could not click Public Api product")
            log("BODY: " + mask(body(driver)[:1200]))
            return None

    # Subscribe button
    for needle in ("subscribe", "add subscription", "confirm", "yes"):
        if click_text(driver, needle):
            log(f"DOFFIN clicked: {needle}")
            time.sleep(1.2)

    # Back to profile subscriptions
    driver.get(DOFFIN + "/profile")
    time.sleep(2)
    click_text(driver, "subscriptions")
    time.sleep(1)
    b = body(driver)
    log("DOFFIN profile snip: " + mask(b[:900]))
    if "public" not in b.lower() and "don't have" in b.lower():
        log("DOFFIN still no subscription — may need Jerome confirm click")
        return None

    cands = reveal_and_collect_keys(driver)
    log(f"DOFFIN cand_count={len(cands)}")
    key = pick_primary(cands, b + driver.page_source)
    log(f"DOFFIN key_found={bool(key)} len={len(key or '')}")
    return key


def subscribe_hilma(driver) -> str | None:
    log("=== HILMA subscribe AVP-Read ===")
    if not ensure_signed_in(driver, HILMA):
        return None

    if "add subscription" in body(driver).lower() or "don't have subscriptions" in body(driver).lower():
        click_text(driver, "add subscription")
        time.sleep(1.5)

    driver.get(HILMA + "/products")
    time.sleep(2)
    if not click_product(driver, "avp-read", avoid=["ets-write", "write"]):
        if not click_product(driver, "avp", avoid=["write", "ets"]):
            log("HILMA: could not click AVP-Read")
            log("BODY: " + mask(body(driver)[:1200]))
            return None

    for needle in ("subscribe", "add subscription", "confirm", "yes"):
        if click_text(driver, needle):
            log(f"HILMA clicked: {needle}")
            time.sleep(1.2)

    driver.get(HILMA + "/profile")
    time.sleep(2)
    click_text(driver, "subscriptions")
    time.sleep(1)
    b = body(driver)
    log("HILMA profile snip: " + mask(b[:900]))
    cands = reveal_and_collect_keys(driver)
    log(f"HILMA cand_count={len(cands)}")
    key = pick_primary(cands, b + driver.page_source)
    log(f"HILMA key_found={bool(key)} len={len(key or '')}")
    return key


def main() -> int:
    try:
        driver = attach()
    except Exception as exc:
        log(f"ATTACH_FAIL: {exc}")
        return 2

    pages = []
    for h in driver.window_handles:
        driver.switch_to.window(h)
        pages.append(driver.current_url)
    log("tabs=" + json.dumps(pages)[:500])

    doffin_key = subscribe_doffin(driver)
    hilma_key = subscribe_hilma(driver)

    if doffin_key or hilma_key:
        write_env(doffin_key, hilma_key)
    else:
        log("NO_KEYS — need Jerome to click Confirm/Subscribe if modal blocked")
        return 1

    # reload check lengths only
    text = ENV_PATH.read_text(encoding="utf-8")
    d_ok = bool(re.search(r"^ISZE_DOFFIN_API_KEY=.+$", text, re.M))
    h_ok = bool(re.search(r"^ISZE_HILMA_API_KEY=.+$", text, re.M))
    # empty values still match .+? no — .+$ requires non-empty after =
    d_ok = bool(re.search(r"^ISZE_DOFFIN_API_KEY=\S+", text, re.M))
    h_ok = bool(re.search(r"^ISZE_HILMA_API_KEY=\S+", text, re.M))
    log(f"env_check doffin_set={d_ok} hilma_set={h_ok}")
    return 0 if (d_ok and h_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
