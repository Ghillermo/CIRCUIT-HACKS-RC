"""The two sets of manuals (the user, 2026-11-06: «Separa los manuales de RC y Beta», «Dos juegos con nombre»): docs/manual/rc/ (only what the release
candidate has) and docs/manual/beta/ (everything, the beta's own parts still marked), with a chooser at docs/manual/index.html and the old page names
there redirecting to rc/ (with their #anchor), so old links keep working.

The generators write the same pages as always; with SET = "rc" every markdown text goes through rc() first and every section / view / heading whose
title carries the beta mark is left out.  The mark is the guide's / manual's «solo Beta N» / «Beta N only» (BETA = make_guide.YBETA):
  * a heading with it: the heading and everything under it (to the next heading of its level or above);
  * a list item, a table row or a paragraph with it at its start (before its first «:» / «—» / « | » or in its first 90 characters): left out
    (a list item with its indented lines);
  * further in: the sentence holding it goes (in a table, the sentence of that cell; an emptied cell becomes «—»); a parenthesis that starts
    with it goes whole.

    python tools/docset.py              (both sets, both languages; then the chooser and the redirects)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
SETS = ("rc", "beta")


def beta_name():
    import make_guide as G
    return G.YBETA                                      # «Beta 5.29»


def mark_re():
    """the beta's own mark, of any beta on top of RC4 (5.x: the hand-written «solo Beta 5.12» too)"""
    n = r"5\.\d+"
    return re.compile(r"(?i)\*{0,2}\(?\*{0,2}(?:solo\s+beta\s+%s|beta\s+%s\s+only)\b\)?\*{0,2}[:.]?\*{0,2}" % (n, n))


def beta(text):
    """(the beta set) the marks of older 5.x betas named as the current beta"""
    b = beta_name()
    text = re.sub(r"(?i)\b(solo\s+)Beta 5\.\d+\b", lambda m: m.group(1) + b, text)
    return re.sub(r"(?i)\bBeta 5\.\d+(\s+only)\b", lambda m: b + m.group(1), text)


def titled(title):
    return bool(mark_re().search(title or ""))


SENT = re.compile(r"(?<=[.;!?])\s+(?=[\"«(\[*_A-ZÁÉÍÓÚÑ¿¡0-9])")


def _cut(text, M):
    """text up to the sentence holding the mark (what follows it is the beta's addition); the sentences after it go too"""
    if not M.search(text): return text
    parts = SENT.split(text)
    keep = []
    for p in parts:
        if M.search(p): break
        keep.append(p)
    return " ".join(keep).strip()


OTHER = re.compile(r"\s*\*?\((?![^()]*\bRC)[^()]*\b(?:en la |in )?Beta \d+\.\d+[^()]*\)\*?"         # a parenthesis about a beta (no RC in it)
                   r"|;?\s*(?:en la |in )?Beta \d+\.\d+(?:\s*/\s*\d+\.\d+)?:[^;)|\n]*"              # «Beta 5.28: …» up to ; ) |
                   r"|\s*\((?:no en la|not in) Beta[^()]*\)", re.I)


def others(text):
    """(the RC set) the clauses and parentheses about a beta that are not marked as the beta's own (not next to an RC: «arreglo de RC4.08 y la Beta …» stays)"""
    return OTHER.sub(lambda m: m.group(0) if "RC" in text[max(0, m.start() - 30):m.start()] else "", text)


def _head(line, M):
    """the mark in the line's head: before its first « — » / «:» / «|» after the start, or in its first 90 characters"""
    m = M.search(line)
    if not m: return False
    body = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", line)
    m = M.search(body)
    if m.start() < 90: return True
    stop = min([i for i in (body.find(" — "), body.find(":"), body.find(" | ")) if i > 0] or [len(body)])
    return m.start() <= stop


def rc(text):
    M = mark_re()
    text = re.sub(r"(?m)^(\s*)\*{0,2}(%s)\b" % re.escape(beta_name()), r"\1\2 only", text)   # a paragraph that starts with «Beta N»: the beta's
    text = re.sub(r"Este documento describe la \*\*Beta [\d.]+\*\*[^\n]*",
                  "Este documento describe la versión candidata **" + rc_name() + "**; la beta tiene su propio documento.", text)
    text = re.sub(r"This document describes \*\*Beta [\d.]+\*\*[^\n]*",
                  "This document describes the release candidate **" + rc_name() + "**; the beta has its own document.", text)
    if not M.search(text): return others(text)
    out, skip_level, skip_item = [], 0, None
    for line in text.split("\n"):
        h = re.match(r"^(#{1,6})\s", line)
        if h:
            lvl = len(h.group(1))
            if skip_level and lvl > skip_level: continue
            skip_level = 0
            if M.search(line): skip_level = lvl; continue
            out.append(line); continue
        if skip_level: continue
        if skip_item is not None:                                   # an item left out: its indented lines too
            if line.strip() and (len(line) - len(line.lstrip())) > skip_item: continue
            skip_item = None
        if not M.search(line): out.append(line); continue
        if line.lstrip().startswith("|"):                           # a table row
            cells = line.split("|")
            if any(M.search(c) and _head(c, M) for c in cells[1:3]): continue
            cells = [_cut(c, M) if M.search(c) else c for c in cells]
            if any(not c.strip() for c in cells[1:-1]): continue           # a cell that was only the beta's: the row is the beta's
            out.append("|".join(cells)); continue
        if _head(line, M):
            if re.match(r"^\s*(?:[-*]|\d+\.)\s", line): skip_item = len(line) - len(line.lstrip())
            continue
        lead = re.match(r"^(\s*(?:[-*]|\d+\.)\s+)?", line).group(0)
        c = _cut(line[len(lead):], M)
        if c: out.append(lead + c)
    t = others("\n".join(out))
    while "\n\n\n" in t: t = t.replace("\n\n\n", "\n\n")
    return t


def chooser():
    """docs/manual/index.html: the two sets; the old page names redirect to rc/"""
    import make_manual as Mm
    d = ROOT / "docs/manual"
    rcn, bn = rc_name(), beta_name()
    page = f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>CIRCUIT-HACKS</title>
<style>{Mm.CSS} .sets {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:16px; }} .sets div {{ border:1px solid var(--line); border-radius:10px; padding:12px 16px; background:var(--card); }}</style></head><body>
<header class="cover"><h1>CIRCUIT-HACKS</h1><p>Manuales · Manuals</p><div class="bar"></div></header><main>
<div class="sets">
<div><h2>{rcn}</h2><p>La versión candidata: solo lo que ya está en ella. · The release candidate: only what it has.</p><ul>
<li><a href="rc/guia.html">Guía por vistas</a> · <a href="rc/guide.html">Guide by views</a></li>
<li><a href="rc/index.html">Lista de características</a> · <a href="rc/en.html">Feature list</a></li>
<li><a href="rc/voces.html">Pistas MIDI y modos de voz</a> · <a href="rc/voices.html">MIDI tracks and voice modes</a></li>
<li><a href="rc/midi.html">Referencia MIDI</a> · <a href="rc/midi-en.html">MIDI reference</a></li></ul></div>
<div><h2>{bn}</h2><p>La beta: todo, con lo que aún no está en la RC marcado. · The beta: everything, with what is not in the RC yet marked.</p><ul>
<li><a href="beta/guia.html">Guía por vistas</a> · <a href="beta/guide.html">Guide by views</a></li>
<li><a href="beta/index.html">Lista de características</a> · <a href="beta/en.html">Feature list</a></li>
<li><a href="beta/voces.html">Pistas MIDI y modos de voz</a> · <a href="beta/voices.html">MIDI tracks and voice modes</a></li>
<li><a href="beta/midi.html">Referencia MIDI</a> · <a href="beta/midi-en.html">MIDI reference</a></li></ul></div>
</div>
<p><a href="sencilla.html">Guía en palabras sencillas</a> · <a href="plain.html">Guide in plain words</a></p>
</main></body></html>'''
    (d / "index.html").write_text(page, encoding="utf-8", newline="")
    for n in ("en.html", "guia.html", "guide.html", "midi.html", "midi-en.html", "voces.html", "voices.html"):
        (d / n).write_text(f'<!doctype html><html><head><meta charset="utf-8"><title>CIRCUIT-HACKS</title>'
                           f'<script>location.replace("rc/{n}" + location.hash)</script><meta http-equiv="refresh" content="0; url=rc/{n}"></head>'
                           f'<body><a href="rc/{n}">rc/{n}</a></body></html>', encoding="utf-8", newline="")


def rc_name():
    return "RC4.08"                                    # the release candidate the rc set describes


def build():
    import make_manual as Mm
    import make_guide as G
    import midi_ref
    import make_voces as MV
    for st in SETS:
        Mm.SET, Mm.OUT = st, f"docs/manual/{st}"
        (ROOT / Mm.OUT).mkdir(parents=True, exist_ok=True)
        for lang in Mm.LANGS: Mm.use(lang); Mm.write_html()
        for lang in ("es", "en"): G.write(lang, md=False)
        for lang in ("es", "en"): midi_ref.write(lang, Mm.VERSION, Mm, md=False)
        for lang in ("es", "en"): MV.page(lang)
    Mm.SET, Mm.OUT = None, "docs/manual"
    chooser()


if __name__ == "__main__":
    build()
    print("rc / beta sets, the chooser and the redirects")
