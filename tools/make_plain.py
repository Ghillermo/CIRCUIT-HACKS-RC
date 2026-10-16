"""The guide in plain words (after the community guide by u/luxurysoft1337), Spanish and English, illustrated with the panel drawings of make_manual.

    python tools/make_plain.py          (writes docs/SENCILLA.md, docs/PLAIN.en.md, docs/manual/sencilla.html, docs/manual/plain.html)
    python tools/make_plain.py --pdf    (also docs/manual/sencilla.pdf and plain.pdf, printed by headless Edge or Chrome)
The text is in tools/plain_es.py and tools/plain_en.py (same section ids and figures).
"""
from __future__ import annotations
import html
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_manual as M  # noqa: E402

ROOT = M.ROOT
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
CREDIT = {"es": 'Primer borrador: <a href="https://www.reddit.com/user/luxurysoft1337/">reddit.com/u/luxurysoft1337</a>',
          "en": 'First draft by <a href="https://www.reddit.com/user/luxurysoft1337/">reddit.com/u/luxurysoft1337</a>'}
PRINT_CSS = """
header.cover a { color:#ffb38a; }
@media print {
  * { -webkit-print-color-adjust:exact; print-color-adjust:exact; }
  body { background:#fff; font-size:11pt; } main { max-width:none; padding:0; }
  p.lang, nav.toc { display:none; } section.feat { border:none; padding:0; margin:14px 0; }
  section.feat h3 { break-after:avoid; } figure, table, tr { break-inside:avoid; } h4 { break-after:avoid; }
  header.cover { padding:40px 24px 28px; }
}
@page { size:A4; margin:14mm 12mm; }
"""
BROWSERS = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"]


def links(h):
    return LINK.sub(r'<a href="\2">\1</a>', h)


def load(lang):
    import plain_es, plain_en
    return plain_es if lang == "es" else plain_en


def write(lang):
    T = load(lang)
    U = T.UI
    secs = list(enumerate(T.S, 1))
    # markdown (no figures: they are in the HTML page)
    md = [f"# {U['title']}", "", T.INTRO, "", f"## {U['toc']}", ""]
    md += [f"{n}. [{s['title']}](#{s['id']})" for n, s in secs] + [f"{len(secs) + 1}. [{T.CHANGES_TITLE}](#edition)", ""]
    for n, s in secs:
        md += [f'<a id="{s["id"]}"></a>', f"## {n}. {s['title']}", "", s["body"], ""]
    md += ['<a id="edition"></a>', f"## {len(secs) + 1}. {T.CHANGES_TITLE}", "", T.CHANGES, ""]
    (ROOT / U["md"]).write_text("\n".join(md), encoding="utf-8", newline="")
    # html
    h = [f'<!doctype html><html lang="{U["lang"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(U["title"])}</title>',
         f"<style>{M.CSS}{PRINT_CSS}</style></head><body>",
         f'<header class="cover"><h1>CIRCUIT-HACKS</h1><p>{U["cover"]}</p><p>{M.VERSION} · {T.BETA}</p><p>{CREDIT[lang]}</p><div class="bar"></div></header><main>',
         U["other"]]
    h += [links(M.md2html(p)) for p in T.INTRO.split("\n\n")]
    h.append(f'<nav class="toc"><h2>{U["toc"]}</h2><ol>')
    h += [f'<li><a href="#{s["id"]}">{html.escape(s["title"])}</a></li>' for n, s in secs]
    h.append(f'<li><a href="#edition">{html.escape(T.CHANGES_TITLE)}</a></li></ol></nav>')
    for n, s in secs:
        h.append(f'<section class="feat" id="{s["id"]}"><h3><span class="code">{n}</span>{html.escape(s["title"])}</h3>')
        for f in s["figs"]:
            h.append(f"<figure>{M.svg(f)}<figcaption>{html.escape(f['caption'])}</figcaption></figure>")
        h.append(links(M.md2html(s["body"])))
        h.append("</section>")
    h.append(f'<section class="feat" id="edition"><h3><span class="code">{len(secs) + 1}</span>{html.escape(T.CHANGES_TITLE)}</h3>{links(M.md2html(T.CHANGES))}</section>')
    h.append(f"<footer>{U['footer']}</footer></main></body></html>")
    out = "\n".join(h)
    for bad in ("{B}", "{BETA}"):
        assert bad not in out, f"{lang}: literal {bad} in the page"
    page = ROOT / "docs/manual" / U["html"]
    page.write_text(out, encoding="utf-8", newline="")
    return page, ROOT / "docs/manual" / U["pdf"], len(secs)


def pdf(page, dest):
    exe = next((b for b in BROWSERS if Path(b).exists()), None)
    if not exe: raise SystemExit("no Edge / Chrome for the PDF")
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf-no-header", f"--print-to-pdf={dest}",
                    page.resolve().as_uri()], check=True, capture_output=True, timeout=180)
    return dest.stat().st_size


if __name__ == "__main__":
    for lang in ("es", "en"):
        page, dest, n = write(lang)
        msg = f"{lang}: {n} sections -> {page.relative_to(ROOT)}"
        if "--pdf" in sys.argv: msg += f", {dest.relative_to(ROOT)} ({pdf(page, dest)} B)"
        print(msg)
