"""Ambil screenshot halaman GitHub Webhook Recent Deliveries dan perbarui PDF laporan.

Jalankan di terminal:

    py -3.12 scripts/capture_webhook_screenshot.py

Browser Edge akan terbuka. Login ke GitHub bila diminta; setelah login berhasil,
skrip otomatis membuka tab Recent Deliveries, menyimpan screenshot ke
Bukti/screenshots/09_github_webhook_deliveries.png, memperbarui LAPORAN.md,
dan men-generate ulang ../LAPORAN_Praktikum_CICD.pdf.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = os.environ.get("GITHUB_REPO", "phyxa12/python-crud-api")
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else ROOT / "Bukti" / "screenshots" / "09_github_webhook_deliveries.png"
)
PROFILE = Path.home() / ".cache" / "gh-webhook-screenshot"

REPORT_CSS = """
@page { margin: 15mm 14mm; }
body { font-family: "Segoe UI", Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #1b1b1b; max-width: 100%; }
h1 { font-size: 20pt; border-bottom: 2px solid #2c6fb5; padding-bottom: 4px; }
h2 { font-size: 14pt; margin-top: 22px; border-bottom: 1px solid #d6dde6; padding-bottom: 2px; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin-top: 16px; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 14px; font-size: 9pt; }
th, td { border: 1px solid #b9c3cf; padding: 4px 6px; vertical-align: top; text-align: left; }
th { background: #eaf1f8; }
code { background: #f3f4f6; padding: 1px 4px; border-radius: 3px; font-size: 9pt; }
pre { background: #f6f8fa; border: 1px solid #dde3ea; border-radius: 4px; padding: 8px 10px; overflow-x: auto; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
figure { margin: 4px 0 14px; page-break-inside: avoid; break-inside: avoid; }
figure img { display: block; max-width: 100%; max-height: 135mm; width: auto; height: auto; border: 1px solid #ccd4dd; margin: 0 auto 4px; }
figcaption { font-size: 8.5pt; color: #555; text-align: center; }
img { max-width: 100%; border: 1px solid #ccd4dd; }
blockquote { border-left: 3px solid #2c6fb5; margin-left: 0; padding-left: 10px; color: #444; }
""".strip()


def is_logged_out(page) -> bool:
    url = page.url
    if any(k in url for k in ("/login", "/session", "/two-factor", "accounts.google.com")):
        return True
    title = page.title()
    if "Page not found" in title or "Sign in" in title:
        return True
    if page.locator("a[href*='/login']").count() > 0:
        return True
    return False


def update_report_and_pdf(playwright_instance):
    laporan_md = ROOT / "LAPORAN.md"
    if not laporan_md.exists():
        return
    text = laporan_md.read_text(encoding="utf-8")
    row = "| `Bukti/screenshots/09_github_webhook_deliveries.png` | GitHub Webhook *Recent Deliveries* (response `200 OK`) |"
    if "09_github_webhook_deliveries.png" not in text:
        target_row = "| `Bukti/screenshots/08_jenkins_build8_scm.png` | build #8 dari polling otomatis (\"Started by an SCM change\") |"
        if target_row in text:
            text = text.replace(target_row, f"{target_row}\n{row}")
        text = text + (
            "\n\nGitHub Webhook *Recent Deliveries* dengan response sukses (`200 OK`):\n\n"
            "![GitHub Webhook Recent Deliveries](Bukti/screenshots/09_github_webhook_deliveries.png)\n"
        )
        laporan_md.write_text(text, encoding="utf-8")
        print("LAPORAN.md diperbarui dengan 09_github_webhook_deliveries.png.")

    css_file = ROOT / ".report_tmp.css"
    html_file = ROOT / ".report_tmp.html"
    pdf_file = ROOT.parent / "LAPORAN_Praktikum_CICD.pdf"
    try:
        css_file.write_text(REPORT_CSS, encoding="utf-8")
        subprocess.run(
            ["pandoc", str(laporan_md), "-s", f"--css={css_file}", "-o", str(html_file)],
            cwd=str(ROOT),
            check=True,
        )
        browser = playwright_instance.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        page.goto(html_file.resolve().as_uri(), wait_until="networkidle")
        page.wait_for_function(
            "Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)",
            timeout=60000,
        )
        page.emulate_media(media="print")
        page.pdf(
            path=str(pdf_file),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
            display_header_footer=False,
        )
        browser.close()
        print(f"PDF laporan diperbarui: {pdf_file}")
    finally:
        css_file.unlink(missing_ok=True)
        html_file.unlink(missing_ok=True)


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
                if f"/{REPO}/settings/hooks" in page.url and not is_logged_out(page):
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
            page.screenshot(path=str(OUTPUT), full_page=True)
            print(f"Screenshot disimpan: {OUTPUT}")
            context.close()
            update_report_and_pdf(p)
        else:
            print("Hook belum ditemukan atau belum login ke akun pemilik repo.")
            context.close()


if __name__ == "__main__":
    main()
