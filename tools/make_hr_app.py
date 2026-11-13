"""The Hacks + Remix app (the user, 2026-11-05: «make a new app based on Hacks. It allows to manage both Hacks and Remix, and copy (adapted) patches,
adapted patterns (root note for Track patterns into mono Rhythm sequences) and samples into eachother or saved folders and snapshots»).

    python tools/make_hr_app.py [path/to/rm_sd_app.html]      -> tools/hr_app.html

One page, both data layers inlined as they are in their own apps: the Tracks core of tools/sd_app.html as SDT, the Rhythm core of the RYTHM
repository's tools/rm_sd_app.html (default ../RYTHM/tools/rm_sd_app.html) as SDR; the page's own part is tools/hr_ui.js.  Rebuild after either
app's core changes.
The two device apps whole as well (the user, 2026-11-06: «añade snapshot y las funciones de las apps específicas»): tools/sd_app.html (Hacks: packs,
Nova synths, drums, custom patches, CC presets, DX7, the device over USB with its snapshot / restore) and the RYTHM repository's tools/rm_app.html
(Remix: packs, projects, samples, patterns, the device over USB with its snapshot / restore, modules, the firmware installer; make it first with
RYTHM's tools/make_rm_app.py), as strings opened in a same-origin frame (srcdoc: folders and Web MIDI work there) by the «Hacks» / «Remix» views.
(2026-11-10, the user: «añádelo a la app maestra, junto a los parches demo») the patch editor (tools/make_patch_editor.py, rebuilt here) as a third
view, and the demo patches of docs/patches as window.HR_DEMOS: a read-only source of the Patches tab («Parches demo»).
(2026-11-13, the user: «add Remix to the master app … under firmware options», «Both») a Firmware view with the two installers (tools/rc_uploader.html
for the Tracks, the Remix app on its Firmware tab for the Rhythm) and two firmware selectors in the header (Tracks: automatic / stock only / Hacks, the
Hacks app's own setting; Rhythm: automatic / stock only / Remix): stock only = no own patches on that side.  The Remix app is the published one
(RYTHM's build/public/rm_app.html, only Circuit Remix versions) when it exists; rebuild after tools/make_rc_uploader.py too."""
from __future__ import annotations
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RM = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent.parent / "RYTHM" / "tools" / "rm_sd_app.html"
RM_APP = RM.parent / "rm_app.html"
RM_PUB = RM.parent.parent / "build" / "public" / "rm_app.html"     # (2026-11-13) the published Remix app: only the Circuit Remix versions in its installer


def js_string(html):
    """an HTML page as a JS string literal that can sit in a <script> (no "</" nor "<!--" left)"""
    import json
    return json.dumps(html, ensure_ascii=False).replace("</", "<\\/").replace("<!--", "<\\!--").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


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
    a_hacks, a_remix = js_string(t_html), js_string((RM_PUB if RM_PUB.exists() else RM_APP).read_text(encoding="utf-8"))
    a_hinst = js_string((HERE / "rc_uploader.html").read_text(encoding="utf-8"))   # (2026-11-13) the Firmware view: the Hacks installer
    import json
    import make_patch_editor as PE                     # (2026-11-10) the patch editor view and the demo patches (docs/patches)
    PE.main()
    a_editor = js_string(PE.OUT.read_text(encoding="utf-8"))
    demos = json.dumps(PE.data()["examples"], separators=(",", ":"))
    page = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hacks + Remix</title>
<style>{style}
  .kind {{ font-size:.75rem; padding:1px 6px; border-radius:4px; border:1px solid var(--line); color:var(--dim); }}
  .kind.t {{ color:#79c0ff; border-color:#79c0ff; }} .kind.r {{ color:#ffb86b; border-color:#ffb86b; }} .kind.f {{ color:#7ee787; border-color:#7ee787; }}
  #views {{ display:flex; gap:6px; padding:6px 12px 0; }} #views button.on {{ background:var(--acc, #1f6feb); color:#fff; }}
  body.appmode {{ display:flex; flex-direction:column; height:100vh; margin:0; overflow:hidden; }}
  body.appmode #tabs, body.appmode #notice, body.appmode main, body.appmode footer, body.appmode #bBackup, body.appmode #sub, body.appmode header .lang, body.appmode header .fw {{ display:none; }}
  #appview:not([hidden]) {{ flex:1; min-height:0; display:flex; flex-direction:column; }} #appview iframe {{ flex:1; min-height:0; width:100%; border:0; display:block; }} #appview iframe[hidden] {{ display:none; }}
  #fwnav {{ display:flex; gap:6px; padding:6px 12px; }} #fwnav[hidden] {{ display:none; }} #fwnav button.on {{ background:var(--acc, #1f6feb); color:#fff; }}
  header .fw {{ display:flex; gap:6px; }}
</style>
</head>
<body>
<header>
  <h1>Hacks + Remix</h1>
  <span class="sub" id="sub"></span>
  <div class="right">
    <div class="fw"><select id="fwT" aria-label="Firmware · Circuit Tracks"></select><select id="fwR" aria-label="Firmware · Circuit Rhythm"></select></div>
    <button id="bBackup" type="button"></button>
    <div class="lang" role="group" aria-label="Idioma / Language"><button type="button" data-lang="es">Español</button><button type="button" data-lang="en">English</button></div>
  </div>
</header>
<nav id="views" role="tablist"></nav>
<nav id="tabs" role="tablist"></nav>
<div id="notice"></div>
<main><section class="pane" id="pane0"></section><section class="pane" id="pane1"></section></main>
<footer><progress id="prog" hidden></progress><div id="progtxt" hidden></div><div id="log" role="log"></div></footer>
<div id="appview" hidden><nav id="fwnav" hidden></nav></div>
<dialog id="dlg"></dialog>
<script id="core-tracks">{t_js}</script>
<script id="core-rhythm">{r_js}</script>
<script id="apps">window.HR_APPS = {{hacks: {a_hacks}, remix: {a_remix}, editor: {a_editor}, hinst: {a_hinst}}};</script>
<script id="demos">window.HR_DEMOS = {demos};</script>
<script id="ui">
{ui}
</script>
</body>
</html>
"""
    # the old name of the master effects view never goes in (CLAUDE.md;
    for x, y in (("Gr" + "id FX", "Master FX"), ("GR" + "ID FX", "MASTER FX"), ("gr" + "id fx", "master fx")):   # Remix's installer list names it)
        page = page.replace(x, y)
    assert not re.search("gr" + r"id[ _.-]?fx", page, re.I)
    (HERE / "hr_app.html").write_text(page, encoding="utf-8", newline="")
    print("hr_app.html", len(page))


if __name__ == "__main__":
    main()
