import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT.parent
LAPORAN_MD = ROOT / "LAPORAN.md"

REPORT_CSS = """
@page { 
    margin: 15mm 14mm; 
    @bottom-center { content: counter(page); }
}
body { 
    font-family: "Segoe UI", Arial, sans-serif; 
    font-size: 10.5pt; 
    line-height: 1.45; 
    color: #1b1b1b; 
    max-width: 100%; 
}
h1 { 
    font-size: 20pt; 
    border-bottom: 2px solid #2c6fb5; 
    padding-bottom: 4px; 
    margin-bottom: 12px;
}
h2 { 
    font-size: 14pt; 
    margin-top: 22px; 
    border-bottom: 1px solid #d6dde6; 
    padding-bottom: 2px; 
    page-break-after: avoid; 
}
h3 { 
    font-size: 11.5pt; 
    margin-top: 16px; 
    page-break-after: avoid; 
}
table { 
    border-collapse: collapse; 
    width: 100%; 
    margin: 8px 0 14px; 
    font-size: 9pt; 
    page-break-inside: avoid;
}
th, td { 
    border: 1px solid #b9c3cf; 
    padding: 5px 7px; 
    vertical-align: top; 
    text-align: left; 
}
th { 
    background: #eaf1f8; 
    font-weight: 600;
}
code { 
    background: #f3f4f6; 
    padding: 1px 4px; 
    border-radius: 3px; 
    font-size: 9pt; 
    font-family: "Consolas", monospace;
}
pre { 
    background: #f6f8fa; 
    border: 1px solid #dde3ea; 
    border-radius: 4px; 
    padding: 8px 10px; 
    overflow-x: auto; 
    page-break-inside: avoid; 
}
pre code { 
    background: none; 
    padding: 0; 
    font-size: 8.5pt;
}
figure { 
    margin: 8px 0 16px; 
    page-break-inside: avoid; 
    break-inside: avoid; 
}
figure img { 
    display: block; 
    max-width: 100%; 
    max-height: 135mm; 
    width: auto; 
    height: auto; 
    border: 1px solid #ccd4dd; 
    margin: 0 auto 4px; 
}
figcaption { 
    font-size: 8.5pt; 
    color: #555; 
    text-align: center; 
}
img { 
    max-width: 100%; 
    border: 1px solid #ccd4dd; 
}
blockquote { 
    border-left: 3px solid #2c6fb5; 
    margin-left: 0; 
    padding-left: 10px; 
    color: #444; 
}
""".strip()

def main():
    css_file = ROOT / ".report_tmp.css"
    html_file = ROOT / ".report_tmp.html"
    pdf_targets = [
        WORKSPACE / "LAPORAN_Praktikum_CICD.pdf",
        WORKSPACE / "LAPORAN_Praktikum_CICD_101012330071_Faiz_Aditia_Zain.pdf",
    ]

    try:
        css_file.write_text(REPORT_CSS, encoding="utf-8")
        print("Menjalankan pandoc...")
        subprocess.run(
            ["pandoc", str(LAPORAN_MD), "-s", f"--css={css_file}", "-o", str(html_file)],
            cwd=str(ROOT),
            check=True,
        )
        print("Pandoc selesai membuat HTML.")

        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page()
            page.goto(html_file.resolve().as_uri(), wait_until="networkidle")
            page.wait_for_function(
                "Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)",
                timeout=60000,
            )
            page.emulate_media(media="print")
            for pdf_file in pdf_targets:
                page.pdf(
                    path=str(pdf_file),
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                    display_header_footer=False,
                )
                print(f"PDF berhasil dibuat: {pdf_file} ({pdf_file.stat().st_size} bytes)")
            browser.close()
    finally:
        css_file.unlink(missing_ok=True)
        html_file.unlink(missing_ok=True)

if __name__ == "__main__":
    main()
