"""Ambil screenshot halaman GitHub Webhook Recent Deliveries.

Jalankan di mesin yang memiliki browser Edge/Chrome dan akses GitHub:

    python3 scripts/capture_webhook_screenshot.py

Browser akan terbuka. Login ke GitHub bila diminta, lalu tekan Enter di terminal.
Skrip menyimpan screenshot ke Bukti/screenshots/09_github_webhook_deliveries.png.
"""

import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = os.environ.get("GITHUB_REPO", "phyxa12/python-crud-api")
OUTPUT = Path(sys.argv[1] if len(sys.argv) > 1 else
              "Bukti/screenshots/09_github_webhook_deliveries.png")
PROFILE = Path.home() / ".cache" / "gh-webhook-screenshot"


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    hooks_url = f"https://github.com/{REPO}/settings/hooks"

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE),
            channel="msedge",
            headless=False,
            viewport={"width": 1440, "height": 1000},
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(hooks_url, wait_until="domcontentloaded")

        if "/login" in page.url:
            print("Silakan login ke GitHub pada browser yang terbuka.")
            input("Tekan Enter setelah login selesai... ")
            page.goto(hooks_url, wait_until="networkidle")

        page.wait_for_timeout(1500)
        delivery_links = page.locator("a[href*='/deliveries']")
        if delivery_links.count() > 0:
            href = delivery_links.first.get_attribute("href")
            page.goto(f"https://github.com{href}", wait_until="networkidle")
            page.wait_for_timeout(1500)
        else:
            print("Hook belum ada: buat webhook lalu ulangi skrip ini.")

        page.screenshot(path=str(OUTPUT), full_page=True)
        print(f"Screenshot disimpan: {OUTPUT}")
        context.close()


if __name__ == "__main__":
    main()
