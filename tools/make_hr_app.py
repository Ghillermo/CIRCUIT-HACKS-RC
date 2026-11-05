"""The Hacks + Remix app (the user, 2026-11-05: «make a new app based on Hacks. It allows to manage both Hacks and Remix, and copy (adapted) patches,
adapted patterns (root note for Track patterns into mono Rhythm sequences) and samples into eachother or saved folders and snapshots»).

    python tools/make_hr_app.py [path/to/rm_sd_app.html]      -> tools/hr_app.html

One page, both data layers inlined as they are in their own apps: the Tracks core of tools/sd_app.html as SDT, the Rhythm core of the RYTHM
repository's tools/rm_sd_app.html (default ../RYTHM/tools/rm_sd_app.html) as SDR; the page's own part is tools/hr_ui.js.  Rebuild after either
app's core changes."""
from __future__ import annotations
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RM = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent.parent / "RYTHM" / "tools" / "rm_sd_app.html"


def core(path, name):
    html = path.read_text(encoding="utf-8")
    m = re.search(r'<script id="core">([\s\S]*?)</script>', html)
    js = m.group(1)
    assert js.count("const SD = (() => {") == 1 and js.count('if (typeof window !== "undefined") window.SD = SD;') == 1, path
    js = js.replace("const SD = (() => {", f"const {name} = (() => {{").replace('if (typeof window !== "undefined") window.SD = SD;', f'window.{name} = {name};')
    return js, html


def main():
    t_js, t_html = core(HERE / "sd_app.html", "SDT")
    r_js, _ = core(RM, "SDR")
    style = re.search(r"<style>([\s\S]*?)</style>", t_html).group(1)
    ui = (HERE / "hr_ui.js").read_text(encoding="utf-8")
    page = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hacks + Remix</title>
<style>{style}
  .kind {{ font-size:.75rem; padding:1px 6px; border-radius:4px; border:1px solid var(--line); color:var(--dim); }}
  .kind.t {{ color:#79c0ff; border-color:#79c0ff; }} .kind.r {{ color:#ffb86b; border-color:#ffb86b; }} .kind.f {{ color:#7ee787; border-color:#7ee787; }}
</style>
</head>
<body>
<header>
  <h1>Hacks + Remix</h1>
  <span class="sub" id="sub"></span>
  <div class="right">
    <button id="bBackup" type="button"></button>
    <div class="lang" role="group" aria-label="Idioma / Language"><button type="button" data-lang="es">Español</button><button type="button" data-lang="en">English</button></div>
  </div>
</header>
<nav id="tabs" role="tablist"></nav>
<div id="notice"></div>
<main><section class="pane" id="pane0"></section><section class="pane" id="pane1"></section></main>
<footer><progress id="prog" hidden></progress><div id="progtxt" hidden></div><div id="log" role="log"></div></footer>
<dialog id="dlg"></dialog>
<script id="core-tracks">{t_js}</script>
<script id="core-rhythm">{r_js}</script>
<script id="ui">
{ui}
</script>
</body>
</html>
"""
    (HERE / "hr_app.html").write_text(page, encoding="utf-8", newline="")
    print("hr_app.html", len(page))


if __name__ == "__main__":
    main()
