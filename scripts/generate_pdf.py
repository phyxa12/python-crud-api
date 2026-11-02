"""Render LAPORAN.md menjadi PDF bergaya dokumen CD-1 Universitas Telkom.

Gaya: Times New Roman 12 pt, rata kiri-kanan, spasi 1,5, indentasi paragraf,
nomor halaman di kanan atas, kop kaki institusi, dan halaman sampul.
"""
import base64
import re
import subprocess
from pathlib import Path

import fitz
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
WORKSPACE = ROOT.parent
LAPORAN_MD = ROOT / "LAPORAN.md"
ASSETS = Path(__file__).resolve().parent / "assets"

TITLE = (
    "LAPORAN PRAKTIKUM CI/CD — JENKINS, GITHUB, DOCKER, DAN NGROK "
    "PADA PROYEK PYTHON-CRUD-API"
)

CSS = """
@page { size: A4; margin: 25mm 25mm 25mm 25mm; }
html, body { margin: 0; padding: 0; }
body {
  font-family: "Times New Roman", Times, serif;
  font-size: 12pt; line-height: 1.5; color: #000;
  text-align: justify;
}
p { margin: 0; text-indent: 1.25cm; }
hr { display: none; }
h2, h3 {
  font-size: 12pt; font-weight: bold; margin: 12pt 0 0 0;
  text-align: left; border: none; page-break-after: avoid; break-after: avoid;
}
h2 { margin-top: 18pt; }
h2 strong, h3 strong { font-weight: bold; }
.hnum { display: inline-block; min-width: 1.25cm; }
p.caption { text-indent: 1.25cm; margin-top: 8pt; text-align: left;
  page-break-after: avoid; break-after: avoid; }
p.source { text-indent: 1.25cm; margin: 3pt 0 8pt 0; font-size: 11pt; line-height: 1.3; }
table {
  border-collapse: collapse; width: 100%; margin: 2pt 0 2pt 0;
  font-size: 10.5pt; line-height: 1.3; text-align: left;
}
tr { page-break-inside: avoid; break-inside: avoid; }
th, td { border: 0.75pt solid #000; padding: 4pt 6pt; vertical-align: top; }
th { font-weight: bold; text-align: left; background: #fff; }
thead { display: table-header-group; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9.5pt; }
td code { font-size: 9pt; word-break: break-word; }
pre {
  margin: 6pt 0 8pt 0; padding: 6pt 8pt; text-align: left; text-indent: 0;
  border: 0.75pt solid #777; background: #f7f7f7;
  font-size: 8.5pt; line-height: 1.25; white-space: pre-wrap; word-break: break-all;
}
pre code { font-size: 8.5pt; }
figure { margin: 8pt 0 10pt 0; text-align: center; page-break-inside: avoid; break-inside: avoid; }
figure img { max-width: 100%; max-height: 115mm; border: 0.75pt solid #999; }
figcaption { font-size: 11pt; line-height: 1.3; text-align: center; margin-top: 3pt; text-indent: 0; }
a { color: #000; text-decoration: none; }
/* sampul */
.cover { height: 236mm; text-align: center; page-break-after: always; break-after: page;
  position: relative; }
.cover p { text-indent: 0; text-align: center; line-height: 1.25; margin: 0; }
.cover .doc { font-weight: bold; margin-top: 6mm; }
.cover img.logo { width: 90mm; margin-top: 38mm; }
.cover .title { font-weight: bold; font-size: 14pt; margin-top: 22mm; }
.cover .by { margin-top: 20mm; }
.cover .who { font-weight: bold; margin-top: 4mm; }
.cover .inst { font-weight: bold; position: absolute; bottom: 0; left: 0; right: 0; }
.cover .meta { text-align: left; margin: 10mm auto 0 auto; width: 120mm; font-size: 11pt; }
.cover .meta td { border: none; padding: 0 4pt; }
"""


def b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def split_md(text: str):
    """Pisahkan identitas (untuk sampul) dari isi laporan."""
    lines = text.splitlines()
    ident, body_start = {}, 0
    for i, ln in enumerate(lines):
        m = re.match(r"\*\*(Nama|NIM|Mata Kuliah|Kelas|Proyek|Sumber tugas|Repository):\*\*\s*(.*)", ln)
        if m:
            ident[m.group(1)] = m.group(2).replace("`", "")
        if ln.strip() == "---":
            body_start = i + 1
            break
        if ln.startswith("# ") or not ln.strip():
            continue
    # paragraf pengantar lingkungan eksekusi berada sebelum '---' pertama
    intro = [ln for ln in lines[:body_start] if ln.strip() and not ln.startswith("#") and not ln.startswith("**")]
    body = "\n".join(intro) + "\n\n---\n\n" + "\n".join(lines[body_start:])
    return ident, body


def cover_html(ident: dict) -> str:
    logo = b64(ASSETS / "logo.png")
    rows = "".join(
        f"<tr><td>{k}</td><td>:</td><td>{v}</td></tr>"
        for k, v in ident.items()
        if k != "Sumber tugas"
    )
    return f"""
<div class="cover">
  <p class="doc">DOKUMEN LAPORAN PRAKTIKUM</p>
  <img class="logo" src="data:image/png;base64,{logo}">
  <p class="title">{TITLE}</p>
  <p class="by">Oleh :</p>
  <p class="who">{ident.get('Nama', '')} / {ident.get('NIM', '')}</p>
  <table class="meta">{rows}</table>
  <p class="inst">PRODI S1 TEKNIK TELEKOMUNIKASI<br>FAKULTAS TEKNIK ELEKTRO<br>UNIVERSITAS TELKOM<br>BANDUNG<br>2026</p>
</div>
"""


def postprocess(html: str) -> str:
    # nomor judul bab/subbab diberi jarak tab
    def head(m):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        inner = re.sub(r"^<strong>(\d+(?:\.\d+)*)\s+", r'<strong><span class="hnum">\1</span>', inner)
        return f"<{tag}{attrs}>{inner}</{tag}>"
    html = re.sub(r"<(h[23])([^>]*)>(.*?)</\1>", head, html, flags=re.S)
    # judul tabel: tanpa cetak tebal
    html = re.sub(r"<p><strong>(Tabel [\d.]+)</strong>(.*?)</p>", r'<p class="caption">\1\2</p>', html, flags=re.S)
    # keterangan sumber: tanpa miring
    html = re.sub(r"<p><em>(Sumber:.*?)</em></p>", r'<p class="source">\1</p>', html, flags=re.S)
    # gambar: beri penomoran
    counter = {"n": 0}

    def fig(m):
        counter["n"] += 1
        return f'<figcaption>Gambar 13.{counter["n"]} {m.group(1)}</figcaption>'
    html = re.sub(r"<figcaption[^>]*>(.*?)</figcaption>", fig, html, flags=re.S)
    return html


def main():
    ident, body_md = split_md(LAPORAN_MD.read_text(encoding="utf-8"))
    md_tmp = ROOT / ".report_body_tmp.md"
    html_tmp = ROOT / ".report_tmp.html"
    css_tmp = ROOT / ".report_tmp.css"
    pdf_tmp = ROOT / ".report_tmp.pdf"
    targets = [
        WORKSPACE / "LAPORAN_Praktikum_CICD.pdf",
        WORKSPACE / "LAPORAN_Praktikum_CICD_101012330071_Faiz_Aditia_Zain.pdf",
    ]
    try:
        md_tmp.write_text(body_md, encoding="utf-8")
        css_tmp.write_text(CSS, encoding="utf-8")
        body_html_file = ROOT / ".report_body_tmp.html"
        subprocess.run(
            ["pandoc", "-f", "markdown-fancy_lists-task_lists-smart", "-t", "html5",
             "--wrap=none", str(md_tmp), "-o", str(body_html_file)],
            cwd=str(ROOT), check=True,
        )
        body_html = postprocess(body_html_file.read_text(encoding="utf-8"))
        body_html_file.unlink(missing_ok=True)
        html_tmp.write_text(
            f"<!DOCTYPE html><html lang='id'><head><meta charset='utf-8'>"
            f"<link rel='stylesheet' href='{css_tmp.name}'></head>"
            f"<body>{cover_html(ident)}{body_html}</body></html>",
            encoding="utf-8",
        )

        footer_img = b64(ASSETS / "footer.png")
        header = (
            "<div style=\"width:100%;font-family:'Times New Roman',serif;font-size:12px;"
            "text-align:right;padding-right:25mm;margin-top:8mm;\">"
            "<span class='pageNumber'></span></div>"
        )
        footer = "<div></div>"
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page()
            page.goto(html_tmp.resolve().as_uri(), wait_until="networkidle")
            page.wait_for_function(
                "Array.from(document.images).every(i => i.complete && i.naturalWidth > 0)",
                timeout=60000,
            )
            page.emulate_media(media="print")
            page.pdf(
                path=str(pdf_tmp), format="A4", print_background=True,
                display_header_footer=True, header_template=header,
                footer_template=footer,
                margin={"top": "25mm", "bottom": "25mm", "left": "25mm", "right": "25mm"},
            )
            browser.close()

        # halaman sampul: hapus nomor halaman dan kop kaki
        doc = fitz.open(str(pdf_tmp))
        pg = doc[0]
        r = pg.rect
        pg.draw_rect(fitz.Rect(0, 0, r.width, 60), color=None, fill=(1, 1, 1))
        doc.set_metadata({"title": "Laporan Praktikum CI/CD — python-crud-api",
                          "author": ident.get("Nama", "")})
        for t in targets:
            doc.save(str(t), garbage=3, deflate=True)
            print(f"PDF berhasil dibuat: {t} ({t.stat().st_size} bytes), {len(doc)} halaman")
        doc.close()
    finally:
        for f in (md_tmp, html_tmp, css_tmp, pdf_tmp):
            f.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
