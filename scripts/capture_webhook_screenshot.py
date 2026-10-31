"""Ambil screenshot halaman GitHub Webhook Recent Deliveries.

Jalankan di mesin yang memiliki browser Edge/Chrome dan akses GitHub:

    py -3.12 scripts/capture_webhook_screenshot.py

Browser akan terbuka. Login ke GitHub bila diminta; setelah login berhasil,
skrip otomatis membuka tab Recent Deliveries dan menyimpan screenshot ke
Bukti/screenshots/09_github_webhook_deliveries.png.
"""

import os
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = os.environ.get("GITHUB_REPO", "phyxa12/python-crud-api")
OUTPUT = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "Bukti/screenshots/09_github_webhook_deliveries.png"
)
PROFILE = Path.home() / ".cache" / "gh-webhook-screenshot"


def is_logged_out(page) -> bool:
    url = page.url
    if "/login" in url or "/session" in url or "/two-factor" in url:
        return True
    title = page.title()
    if "Page not found" in title or "Sign in" in title:
        return True
    if page.locator("a[href*='/login']").count() > 0:
        return True
    return False


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    hooks_url = f"https://github.com/{REPO}/settings/hooks"
    login_url = f"https://github.com/login?return_to=%2F{REPO.replace('/', '%2F')}%2Fsettings%2Fhooks"

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE),
            channel="msedge",
            headless=False,
            viewport={"width": 1440, "height": 950},
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(hooks_url, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

        if is_logged_out(page):
            print("Belum login ke GitHub. Membuka halaman login di browser Edge...")
            print("Silakan login ke akun GitHub (phyxa12) pada jendela browser yang terbuka.")
            page.goto(login_url, wait_until="domcontentloaded")
            for _ in range(300):
                page.wait_for_timeout(1000)
                if (
                    f"/{REPO}/settings/hooks" in page.url
                    and not is_logged_out(page)
                ):
                    break
            page.goto(hooks_url, wait_until="networkidle")

        page.wait_for_timeout(1500)

        hook_id = None
        for link in page.locator("a[href*='/settings/hooks/']").all():
            href = link.get_attribute("href") or ""
            m = re.search(r"/settings/hooks/(\d+)", href)
            if m:
                hook_id = m.group(1)
                break

        if hook_id:
            deliveries_url = f"https://github.com/{REPO}/settings/hooks/{hook_id}?tab=deliveries"
            print(f"Membuka Recent Deliveries: {deliveries_url}")
            page.goto(deliveries_url, wait_until="networkidle")
            page.wait_for_timeout(2000)
            summaries = page.locator("details summary")
            for idx in range(summaries.count()):
                item = summaries.nth(idx)
                txt = item.inner_text()
                if "200" in txt or "push" in txt or "ping" in txt:
                    item.click()
                    page.wait_for_timeout(1500)
                    break
        else:
            print("Hook belum ditemukan di halaman Settings -> Webhooks.")

        page.screenshot(path=str(OUTPUT), full_page=True)
        print(f"Screenshot disimpan: {OUTPUT}")
        context.close()


if __name__ == "__main__":
    main()
