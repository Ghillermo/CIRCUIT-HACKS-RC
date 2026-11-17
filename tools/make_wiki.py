"""The wiki pages made from the manual (the user, 2026-10-27: «Make new sections: Views, Data, Features, DSP, Usability, MIDI; keep everything user
level, don't discuss reverse engineering or inner tests»): docs/wiki/{Views,Data,Features,Step-by-step,DSP,Usability,MIDI}.md and their -ES twins,
from the guide by views (make_guide / guide_en), the feature list (make_manual) and the MIDI reference (midi_ref, through the guide's MIDI view).
Home, FAQ and Roadmap are written by hand (Patch-Colours by wiki_colours).  Copy docs/wiki/*.md and docs/wiki/img/ into the wiki repository
(CIRCUIT-HACKS-RC.wiki.git) to publish.

(2026-11-14, the user: «Add pictures to the wiki … Explain each feature, not just name it … Create animated versions of the step-by-step
processes»): Features explains every feature (wiki_explain: what it is for, how, what to keep in mind) under its summary, with its figures and the
animations of the processes that show it (make_anim); it is an index of five pages, one per group of the feature list (Features-Shortcuts,
-Controls, -Modes, -DSP, -Misc), so no page carries every picture.  Views puts under each view its maps (wiki_views) and the animations of what
is done there, with a contents index; Step-by-step lists every animation by view, in the guide's order, with its steps written out; DSP and
Usability show the maps of some of their views.  An animation shows once per page: a second place links to the first.

    python tools/make_wiki.py           (also writes the view maps and the animations into docs/wiki/img; then checks every page, hand-written
                                         ones too: the words of the inner works, the images it links, its tables, lists and emphasis; and every
                                         image: the words in it, colours the wiki cannot resolve, files no page uses)
"""
from __future__ import annotations
import html
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_guide as G  # noqa: E402
import make_manual as M  # noqa: E402
import make_anim as A  # noqa: E402
import wiki_views as WV  # noqa: E402
import wiki_explain as X  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PAGES = "https://ghillermo.github.io/CIRCUIT-HACKS-RC/"
WIKI = "https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/"
GUIDE = dict(en=PAGES + "beta/guide.html", es=PAGES + "beta/guia.html")      # (2026-11-06: the manuals in two sets; the wiki = the beta's)
FEATS = dict(en=PAGES + "beta/en.html", es=PAGES + "beta/index.html")
# words that belong to the inner works, never in a wiki page (checked on every page)
BANNED = re.compile(r"\b(0x[0-9A-Fa-f]+|DSP56|RAM|SPI|ARM|emulat\w*|emulac\w*|revers\w* engineer\w*|ingenier\w* inversa|hook\w*|gancho\w*|"
                    r"firmware's (own )?table|tabla del (propio )?firmware|bytes?|núcleo|cores?|XMEM|registers?|builders?|test suite)\b", re.I)

T = dict(
    en=dict(other="Versión en español", home="Home", guide="Guide by views", full="Full details in the guide", how="How to get there:", about="In this view",
            what="What it is for", steps_how="How", keep="Keep in mind", step="Step by step", contents="Contents", in_guide="Guide",
            in_feats="Features", above="shown above, under",
            views=("Views", "Every view of the device and what it offers, with a map of its pads and knobs and, for what takes several gestures in a "
                            "row, an animation that plays them in order. Each view links to its full chapter in the [guide by views]({g})."),
            data=("Data", "What is saved where, how to make sure it is saved, and what is lost when you switch off."),
            feat=("Features", "Every feature of the mod by topic, in five pages: what it is for, how to use it step by step and what to keep in mind, "
                              "with its pictures and the animations of its processes. Each title links to its section in the "
                              "[guide by views]({g}), the manual, where every feature is in the chapter of its view."),
            part="One of the five pages of [Features]({f}): each feature explained, with its pictures and the animations of its processes. Each title "
                 "links to its section in the [guide by views]({g}), the manual, where every feature is in the chapter of its view.",
            steps=("Step by step", "Everything that takes several gestures in a row, played as an animation of the panel with a caption for each "
                                   "gesture, and written out below it. Grouped by view, in the guide's order; each one links to its view in the "
                                   "[guide by views]({g}) and to its entry on the [Features]({f}) pages.",
                   "**How to read them:** the number in the orange circle under the panel counts the gestures. A white dot ringed in orange "
                   "marks the pad to press or hold; an orange outline, the button; an orange ring, the knob you touch; an orange arc, the knob "
                   "to turn and which way. A pad that blinks in the drawing blinks on the device. Each gesture stays on screen long enough to read "
                   "its caption, and the animation loops; a viewer that does not play animations shows the first gesture."),
            dsp=("DSP", "The sound side of the mod: the synth engines of the MIDI tracks, the new drum controls and the effects.",
                 """The **MIDI 1 / 2** tracks get their own synth inside the device, with several engines on the engine row of their Preset view: an
**oscillator** that morphs between sine, triangle, saw (up to a seven-saw **supersaw**) and pulse, with wavefolding; **two oscillators** with FM, sync,
ring and mix; a **VA-drum** for percussive sounds; a **granular** engine that plays grains of a sample or of the live capture; a **4-operator FM**
engine with 16 algorithms; and a **sample mode** that plays the pack's samples across the keyboard, in stereo if you like. It has a filter with
several types, envelopes, an LFO with seven shapes (synced to the tempo if you want), a **mod matrix**, **polyphony** with eight voice modes, and
eight automation lanes. The **drums** gain envelopes, a ring modulator, an LFO, filter modes, sample start and end, attack, bitcrush and distortion
types. **Master FX** adds performance effects to the whole mix, and the **FX** and **Sidechain** views expose the reverb, delay, side-chain and
master compressor settings. The maps of every view are on the [Views]({v}) page."""),
            usab=("Usability", "The conventions that make the mod predictable, the shortcuts that work in every view, and the playing and recording helpers.",
                  "Playing and recording"),
            midi=("MIDI", "How the mod talks MIDI: its own behaviours, the new CCs and NRPNs, and the mod matrix and macro destinations.")),
    es=dict(other="English version", home="Inicio", guide="Guía por vistas", full="Todo el detalle en la guía", how="Cómo se llega:", about="En esta vista",
            what="Para qué sirve", steps_how="Cómo", keep="A tener en cuenta", step="Paso a paso", contents="Contenido", in_guide="Guía",
            in_feats="Funciones", above="más arriba, en",
            views=("Vistas", "Cada vista del aparato y lo que ofrece, con un mapa de sus pads y knobs y, para lo que lleva varios gestos seguidos, "
                             "una animación que los toca en orden. Cada vista enlaza con su capítulo completo de la [guía por vistas]({g})."),
            data=("Datos", "Qué se guarda y dónde, cómo asegurarte de que se guarda y qué se pierde al apagar."),
            feat=("Funciones", "Cada función del mod por temas, en cinco páginas: para qué sirve, cómo se usa paso a paso y qué tener en cuenta, con "
                               "sus imágenes y las animaciones de sus procesos. Cada título enlaza con su apartado de la "
                               "[guía por vistas]({g}), el manual, donde cada función está en el capítulo de su vista."),
            part="Una de las cinco páginas de [Funciones]({f}): cada función explicada, con sus imágenes y las animaciones de sus procesos. Cada título "
                 "enlaza con su apartado de la [guía por vistas]({g}), el manual, donde cada función está en el capítulo de su vista.",
            steps=("Paso a paso", "Todo lo que lleva varios gestos seguidos, como una animación del panel con un texto para cada gesto, escrito también "
                                  "debajo. Por vistas, en el orden de la guía; cada uno enlaza con su vista de la [guía por vistas]({g}) y con su "
                                  "entrada de las páginas de [Funciones]({f}).",
                   "**Cómo leerlas:** el número del círculo naranja bajo el panel cuenta los gestos. Un punto blanco con borde naranja marca el "
                   "pad que hay que pulsar o mantener; un contorno naranja, el botón; un aro naranja, el knob que tocas; un arco naranja, el knob "
                   "que hay que girar y hacia dónde. Un pad que parpadea en el dibujo parpadea en el aparato. Cada gesto se queda el tiempo de leer "
                   "su texto, y la animación se repite; un visor que no reproduce animaciones enseña el primer gesto."),
            dsp=("DSP", "La parte de sonido del mod: los motores del sinte de las pistas MIDI, los controles nuevos de los drums y los efectos.",
                 """Las pistas **MIDI 1 / 2** tienen un sinte propio dentro del aparato, con varios motores en la fila de motores de su vista Preset: un
**oscilador** que pasa del seno al triángulo, la sierra (hasta una **supersaw** de siete sierras) y el pulso, con wavefold; **dos osciladores** con FM,
sync, ring y mezcla; un **VA-drum** para sonidos percusivos; un motor **granular** que toca granos de un sample o de la captura en directo; un motor
**FM de 4 operadores** con 16 algoritmos; y un **modo muestra** que toca los samples del pack a lo largo del teclado, en estéreo si quieres. Tiene un
filtro de varios tipos, envolventes, un LFO con siete formas (a tempo si quieres), una **matriz de modulación**, **polifonía** con ocho modos de voz y
ocho carriles de automatización. Los **drums** ganan envolventes, ring mod, LFO, modos de filtro, inicio y final del sample, ataque, bitcrush y tipos
de distorsión. **Master FX** añade efectos de directo a toda la mezcla, y las vistas **FX** y **Sidechain** dan acceso a la reverb, el delay, el
sidechain y el compresor master. Los mapas de todas las vistas están en la página [Vistas]({v})."""),
            usab=("Usabilidad", "Las convenciones que hacen el mod previsible, los atajos que valen en todas las vistas y las ayudas para tocar y grabar.",
                  "Tocar y grabar"),
            midi=("MIDI", "Cómo habla MIDI el mod: sus comportamientos propios, los CC y NRPN nuevos, y la matriz de modulación y los destinos de los macros.")))
PAGE = dict(views="Views", data="Data", feat="Features", steps="Step-by-step", dsp="DSP", usab="Usability", midi="MIDI")
PARTS = {"A": "Features-Shortcuts", "B": "Features-Controls", "C": "Features-Modes", "D": "Features-DSP", "E": "Features-Misc"}  # the Features pages
DSP_VIEWS = ("midi-preset", "midi-knobs", "midi-fm", "midi-fm8", "midi-muestra", "midi-matriz", "synth-fuente", "drum-pista", "drum-cromatica",
             "master-fx", "vista-fx", "sidechain")
DSP_MAPS = ("midi-preset", "midi-fm", "midi-fm8", "midi-muestra")       # the DSP views whose maps the page shows (all of them: on Views)
USAB_VIEWS = ("synth-nota", "escalas", "micropasos", "pattern-settings", "probabilidad")
USAB_MAPS = ("micropasos", "pattern-settings", "probabilidad")
DEV = {"herramientas"}                # the feature list's developer tools: not for the wiki


def name(key, lang): return PAGE[key] + ("-ES" if lang == "es" else "")


def pname(base, lang): return base + ("-ES" if lang == "es" else "")


def absolute(text, lang):
    """the guide's own links (#view) -> the guide's page"""
    return re.sub(r"\]\(#([\w-]+)\)", lambda m: f"]({GUIDE[lang]}#{m.group(1)})", text)


def nav(lang, other, extra=()):
    t = T[lang]
    links = [f"[{t['other']}]({WIKI}{other})", f"[{t['home']}]({WIKI}{'Home' if lang == 'en' else 'Home#en-español'})", *extra,
             f"[{t['guide']}]({GUIDE[lang]})"]
    return "*" + " · ".join(links) + "*"


def head(key, lang):
    t = T[lang]; title, intro = t[key][0], t[key][1].format(g=GUIDE[lang], f=WIKI + name("feat", lang))
    return [f"# {title}", "", nav(lang, name(key, "en" if lang == "es" else "es")), "", intro, ""]


def summary(v, lang, level="###"):
    t = T[lang]
    out = [f"{level} {v['title']}", "", f"*{t['how']}* {v['how']}", ""]
    if v["about"]: out += [v["about"], ""]
    out += [f"→ [{t['full']}]({GUIDE[lang]}#{v['id']})", ""]
    return out


RENAME = {"convenciones": dict(en="Conventions", es="Convenciones")}


def full(v, lang, level="##"):
    title = RENAME.get(v["id"], {}).get(lang, v["title"])
    how = v["how"] if v["part"] in ("0", "11") else f"*{T[lang]['how']}* {v['how']}"        # the data / MIDI chapters' first line is not a way in
    return [f"{level} {title}", "", how, "", v["detail"].replace("\n### ", f"\n{level}# "), ""]


IMG_DIR = ROOT / "docs/wiki/img"
# (2026-11-06, the user: «Añade imágenes a la wiki»): the voices document's panels (the LEDs as the device shows them) where no view map shows the
# same (the wavetable lists, Beta 5.56 only), the voices document's diagrams, and the feature list's figures under their features; SVG files in
# the wiki's img/ (relative links: the wiki repository serves them)
VIEW_PANELS = {"midi-preset": ("wt", "wtnova", "wtsmp")}
BETA_PANELS = {"wt", "wtnova", "wtsmp"}
VIEW_FIGS = {"midi-preset": ("ruta",), "midi-knobs": ("mapa",)}
FONT = "Arial, Helvetica, sans-serif"
# the manual's dark theme: the voices document's diagrams take their colours from the page (CSS variables), which an image in the wiki lacks
DARK = {"var(--fg)": "#ececec", "var(--muted)": "#a3a8ae", "var(--card)": "#1c1d20", "var(--accent)": "#ff6a13", "var(--line)": "#2c2e33"}


def img(file, cap, alt=None):
    return [f'<img src="img/{file}" width="640" alt="{(alt or cap).replace(chr(34), "")}">', "", f"*{cap}*", ""]


def for_wiki(svg, diagram=False):
    """an SVG of the manual made to stand alone as an image: its own font (an image does not take the page's) and, for a diagram, its colours
    and background (the page's CSS variables, in the manual's dark theme)"""
    if diagram:
        for k, v in DARK.items(): svg = svg.replace(k, v)
    tag = svg[:svg.index(">") + 1]
    new = tag if "font-family=" in tag else tag[:-1] + f' font-family="{FONT}">'
    if diagram: new += '<rect width="100%" height="100%" rx="14" fill="#121315"/>'
    return new + svg[len(tag):]


def export_images(lang):
    """the SVG files of this language; -> (view id -> image lines, section id -> image lines)"""
    import make_voces as MV
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    k = 1 if lang == "en" else 0
    def svg_of(fig_html):
        i = fig_html.index("<svg"); j = fig_html.index("</svg>") + 6
        return fig_html[i:j]
    views = {}
    for vid, names in VIEW_PANELS.items():
        L = []
        for n in names:
            if n not in MV.PANELS or n not in MV.DATA: continue
            f = f"panel-{n}-{lang}.svg"; (IMG_DIR / f).write_text(for_wiki(svg_of(MV.panel(n, lang))), encoding="utf-8")
            cap = MV.PANELS[n]["cap"][k]
            if n in BETA_PANELS: cap = f'{"Beta 5.56 only" if lang == "en" else "Solo Beta 5.56"}: {cap}'
            L += img(f, cap)
        views[vid] = L
    for vid, names in VIEW_FIGS.items():
        for n in names:
            f = f"fig-{n}-{lang}.svg"; (IMG_DIR / f).write_text(for_wiki(MV.svg(MV.FIGS[n], lang), diagram=True), encoding="utf-8")
            views.setdefault(vid, []).extend(img(f, MV.FIGS[n]["title"][k]))
    M.use(lang)
    feats = {}
    for code, s_ in M.numbered():
        L = []
        for i, fg in enumerate(s_["figs"]):
            f = f"feat-{s_['id']}-{i + 1}-{lang}.svg"; (IMG_DIR / f).write_text(for_wiki(M.svg(fg)), encoding="utf-8")
            L += img(f, html.unescape(fg["caption"]))
        if L: feats[s_["id"]] = L
    return views, feats


def view_maps(v, lang, vmaps):
    """a view's maps (wiki_views) as image lines; the alt text: the view (and the map's name when it has several), with the beta mark"""
    k = 0 if lang == "en" else 1
    maps, L = vmaps.get(v["id"], []), []
    for i, m in enumerate(maps):
        alt = v["title"] if len(maps) == 1 else f'{v["title"]}: {WV.VIEW_MAPS[v["id"]][i]["title"][lang]}'
        if m[2 + k].startswith(("Beta 5.56 only", "Solo Beta 5.56")): alt += f' ({A.MARK[lang]["beta"]})'
        L += img(m[k], m[2 + k], alt)
    return L


# ---------------------------------------------------------------------------------------------------- the animations and the anchors
def mark(p, lang):
    """a process's version mark, as the guide writes it («since RC2», «Beta 5.56 only»)"""
    m = A.MARK[lang]
    return m["beta"] if p["beta"] else (f'{m["since"]} {p["since"]}' if p["since"] else "")


def ptitle(p, lang):
    mk = mark(p, lang)
    return p["title"][lang] + (f" ({mk})" if mk else "")


def anim(p, lang, steps):
    """an animated process under a feature or a view: the image and its caption, which links to its steps written out on Step by step"""
    t = f"{T[lang]['step']}: {ptitle(p, lang)}"
    cap = f"[{t}]({steps[p['id']]})" if p["id"] in steps else t
    return [f'<img src="img/{A.file_name(p["id"], lang)}" width="640" alt="{t.replace(chr(34), "")}">', "", f"*{cap}*", ""]


def slug(text, seen):
    """the anchor GitHub gives a heading: its text (a link's text, no emphasis) in lower case, without punctuation but «-» and «_», spaces
    turned into «-»; a repeated anchor gets -1, -2…"""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    s = re.sub(r"[^\w\- ]", "", text.strip().lower()).replace(" ", "-")
    n = seen.get(s, 0); seen[s] = n + 1
    return s if not n else f"{s}-{n}"


def anchors(lines):
    """line number -> the anchor of every heading of a page, in order"""
    seen, out = {}, {}
    for i, ln in enumerate(lines):
        m = re.match(r"#{1,6} (.+)", ln)
        if m: out[i] = slug(m.group(1), seen)
    return out


def contents(t, entries):
    """a page's index: [(heading, its URL, [(title, URL)])] -> one line per group"""
    L = [f"**{t['contents']}**", ""]
    for gtitle, gurl, items in entries:
        L.append(f"- **[{gtitle}]({gurl})** — " + " · ".join(f"[{it}]({u})" for it, u in items))
    return L + [""]


def by_feature():
    out = {}
    for p in A.PROCESSES:
        for f in p["features"]: out.setdefault(f, []).append(p)
    return out


def by_view():
    out = {}
    for p in A.PROCESSES: out.setdefault(p["view"], []).append(p)
    return out


class Shown:
    """the animations already on a page: a second place gets a link to the first (its feature or view heading), filled in once the page's
    anchors are known"""
    def __init__(self): self.first, self.later = {}, []

    def add(self, p, lang, steps, body, title, pos):
        if p["id"] in self.first:
            self.later.append((len(body), p["id"]))
            body += ["", ""]                              # filled by fill()
        else:
            self.first[p["id"]] = (title, pos)
            body += anim(p, lang, steps)

    def fill(self, body, lang, url, a, steps):
        t = T[lang]
        for at, pid in self.later:
            p = next(q for q in A.PROCESSES if q["id"] == pid)
            title, pos = self.first[pid]
            st = f"{t['step']}: {ptitle(p, lang)}"
            st = f"[{st}]({steps[pid]})" if pid in steps else st
            body[at] = f"→ {st} — {t['above']} [{title}]({url}#{a(pos)})"


# ---------------------------------------------------------------------------------------------------- the pages
def feature(code, s_, lang, figs, level="##"):
    """one feature: the title (linked to its section in the guide by views, 2026-11-15), the summary, the explanation, the figures (its animations: features_pages)"""
    t = T[lang]
    summ = re.sub(r" \([A-E]\d{1,2}\)", "", " ".join(s_["summary"]))     # the feature list's codes («(A6)»): the wiki shows no codes
    L = [f'{level} [{s_["title"]}]({GUIDE[lang]}#f-{s_["id"]})', "", summ, ""]
    e = X.EXPLAIN.get(s_["id"], {}).get(lang)
    if e:
        L += [f"**{t['what']}:** {e['what']}", ""]
        L += [f"**{t['steps_how']}:**", ""] + [f"{i + 1}. {s}" for i, s in enumerate(e["how"])] + [""]
        if e["notes"]: L += [f"**{t['keep']}:**", ""] + [f"- {n}" for n in e["notes"]] + [""]
    L += figs
    return L


def features_pages(lang, fimg, steps):
    """-> ({page: lines}: the index and one page per group, section id -> (title, the URL of its entry))"""
    M.use(lang)
    t = T[lang]
    procs = by_feature()
    other = "en" if lang == "es" else "es"
    out, where, index = {}, {}, []
    for g, gname in M.CUR["GROUPS"]:
        page = pname(PARTS[g], lang); url = WIKI + page
        top = [f"# {gname}", "", nav(lang, pname(PARTS[g], other), [f"[{t['feat'][0]}]({WIKI}{name('feat', lang)})"]), "",
               t["part"].format(f=WIKI + name("feat", lang), g=GUIDE[lang]), ""]
        body, items, shown = [], [], Shown()
        for code, s_ in M.numbered():
            if s_["group"] != g or s_["id"] in DEV: continue
            pos = len(body)
            items.append((s_["id"], s_["title"], pos))
            body += feature(code, s_, lang, fimg.get(s_["id"], []))
            for p in procs.get(s_["id"], []): shown.add(p, lang, steps, body, s_["title"], pos)
        anc = anchors(top + body)
        a = lambda pos: anc[len(top) + pos]
        shown.fill(body, lang, url, a, steps)
        out[page] = top + contents(t, [(gname, url, [(title, f"{url}#{a(pos)}") for _, title, pos in items])]) + body
        for sid, title, pos in items: where[sid] = (title, f"{url}#{a(pos)}")
        index.append((gname, url, [(title, f"{url}#{a(pos)}") for _, title, pos in items]))
    out[name("feat", lang)] = head("feat", lang) + contents(t, index)
    return out, where


def steps_page(lang, views, parts, feats):
    """Step by step: every animated process, grouped by view in the guide's order, its steps written out; -> (lines, process id -> URL)"""
    t, url = T[lang], WIKI + name("steps", lang)
    byv = by_view()
    top, body, groups = head("steps", lang) + [t["steps"][2], ""], [], []
    pos_of = {}
    for v in (v for p, _ in parts for v in views if v["part"] == p):
        if v["id"] not in byv: continue
        vpos, items = len(body), []
        body += [f"## {v['title']}", ""]
        for p in byv[v["id"]]:
            items.append((ptitle(p, lang), len(body)))
            pos_of[p["id"]] = len(body)
            links = [f"{t['in_guide']}: [{v['title']}]({GUIDE[lang]}#{v['id']})"]
            fl = [f"[{feats[f][0]}]({feats[f][1]})" for f in p["features"] if f in feats]
            if fl: links.append(f"{t['in_feats']}: " + " · ".join(fl))
            body += [f"### {ptitle(p, lang)}", "",
                     f'<img src="img/{A.file_name(p["id"], lang)}" width="640" alt="{ptitle(p, lang).replace(chr(34), "")}">', ""]
            body += [f"{i + 1}. {f['caption'][lang]}" for i, f in enumerate(p["frames"])] + [""]
            body += ["→ " + " · ".join(links), ""]
        groups.append((v["title"], vpos, items))
    anc = anchors(top + body)
    a = lambda pos: anc[len(top) + pos]
    toc = contents(t, [(vt, f"{url}#{a(vpos)}", [(it, f"{url}#{a(pos)}") for it, pos in items]) for vt, vpos, items in groups])
    return top + toc + body, {pid: f"{url}#{a(pos)}" for pid, pos in pos_of.items()}


def views_page(lang, views, parts, vmaps, steps):
    """Views: parts 1-10 (setup to packs), the summaries, each with its maps and its animations, and a contents index"""
    t, url = T[lang], WIKI + name("views", lang)
    byv = by_view()
    top, body, groups = head("views", lang), [], []
    shown = Shown()
    for p, pn in parts:
        if p in ("0", "11", "A"): continue
        gpos, items = len(body), []
        body += [f"## {pn}", ""]
        for v in views:
            if v["part"] != p: continue
            pos = len(body)
            items.append((v["title"], pos))
            body += summary(v, lang) + view_maps(v, lang, vmaps)
            for pr in byv.get(v["id"], []): shown.add(pr, lang, steps, body, v["title"], pos)
        groups.append((pn, gpos, items))
    anc = anchors(top + body)
    a = lambda pos: anc[len(top) + pos]
    shown.fill(body, lang, url, a, steps)
    return top + contents(t, [(gn, f"{url}#{a(gpos)}", [(it, f"{url}#{a(pos)}") for it, pos in items]) for gn, gpos, items in groups]) + body


def pages(lang, vmaps):
    """-> {page name: lines} of this language"""
    views, parts, _ = G.data(lang)
    vimg, fimg = export_images(lang)
    by = {v["id"]: v for v in views}
    byv = by_view()
    out = {}
    # Step by step first (its anchors), then Features (which links to them), then Step by step again (which links to the features)
    _, steps = steps_page(lang, views, parts, {})
    fpages, feats = features_pages(lang, fimg, steps)
    out[name("views", lang)] = views_page(lang, views, parts, vmaps, steps)
    # Data: the data chapter's first three views in full
    L = head("data", lang)
    for vid in ("datos-patron", "guardado", "datos-perdido"): L += full(by[vid], lang)
    out[name("data", lang)] = L
    out.update(fpages)
    out[name("steps", lang)] = steps_page(lang, views, parts, feats)[0]
    # DSP: the overview, then the sound views' summaries (in full when the view has no summary), with some of their maps and diagrams
    L = head("dsp", lang) + [T[lang]["dsp"][2].format(v=WIKI + name("views", lang)), ""]
    for vid in DSP_VIEWS:
        v = by[vid]
        L += summary(v, lang, "##") if v["about"] else full(v, lang)
        if vid in DSP_MAPS: L += view_maps(v, lang, vmaps)
        L += vimg.get(vid, [])
    out[name("dsp", lang)] = L
    # Usability: the conventions, the buttons of every view (with their animations: that view is not on Views), then the playing / recording
    # views' summaries, some with their maps
    L = head("usab", lang)
    for vid in ("convenciones", "botones"):
        L += full(by[vid], lang)
        for pr in byv.get(vid, []): L += anim(pr, lang, steps)
    L += [f"## {T[lang]['usab'][2]}", ""]
    for vid in USAB_VIEWS:
        L += summary(by[vid], lang)
        if vid in USAB_MAPS: L += view_maps(by[vid], lang, vmaps)
    out[name("usab", lang)] = L
    # MIDI: the MIDI view (with the reference's tables) and the mod matrix / macro destinations view
    L = head("midi", lang)
    for vid in ("midi", "destinos"): L += full(by[vid], lang)
    out[name("midi", lang)] = L
    return out


# ---------------------------------------------------------------------------------------------------- checks
def cells(row):
    """the cells of a table row: «|» inside `code` or escaped does not split"""
    out, cur, code, i = [], "", False, 0
    while i < len(row):
        c = row[i]
        if c == "\\" and i + 1 < len(row): cur += row[i:i + 2]; i += 2; continue
        if c == "`": code = not code
        if c == "|" and not code: out.append(cur); cur = ""
        else: cur += c
        i += 1
    out.append(cur)
    return out[1:-1] if row.strip().startswith("|") and row.strip().endswith("|") else out


def check_page(text):
    """-> problems of a page: images it links that do not exist, broken tables, lists and emphasis"""
    bad = []
    for f in sorted(set(re.findall(r'<img src="img/([^"]+)"', text) + re.findall(r"\]\(img/([^)]+)\)", text))):
        if not (IMG_DIR / f).is_file(): bad.append(f"no image img/{f}")
    lines = text.split("\n")
    i = 0
    while i < len(lines):                                     # tables: a header, its separator, rows of the same width
        if lines[i].startswith("|"):
            j = i
            while j < len(lines) and lines[j].startswith("|"): j += 1
            block = lines[i:j]
            if len(block) < 2 or not re.fullmatch(r"\|(\s*:?-{3,}:?\s*\|)+", block[1].strip()):
                bad.append(f"table without its separator: {block[0][:60]}")
            else:
                n = len(cells(block[0]))
                for r in block:
                    if len(cells(r)) != n: bad.append(f"table row of {len(cells(r))} cells, not {n}: {r[:60]}")
            if i and lines[i - 1].strip() and not lines[i - 1].startswith("#"): bad.append(f"no blank line before the table: {lines[i - 1][:60]}")
            i = j
        else: i += 1
    item = re.compile(r"([-*+]|\d+\.) ")                     # nested items and indented lines only inside a list
    in_list = False
    for ln in lines:
        if not ln.strip(): continue
        if item.match(ln): in_list = True
        elif ln.startswith(" "):
            if not in_list: bad.append(f"an indented line outside a list (it would show as code): {ln[:60]}")
        else: in_list = False
    for para in re.split(r"\n\s*\n", text):                   # emphasis and code closed within each paragraph
        body = re.sub(r"`[^`]*`", "", para)
        if para.count("`") % 2: bad.append(f"an unclosed `: {para[:60]}")
        if body.count("**") % 2: bad.append(f"an unclosed **: {para[:60]}")
    return bad


def banned(text):
    """-> the words of the inner works in a text, each with its context"""
    return ["inner works? …" + text[max(0, m.start() - 60):m.end() + 40].replace("\n", " ") + "…" for m in BANNED.finditer(text)]


def check_image(path):
    """-> problems of an image: the words of the inner works in its texts (title, labels, captions), page colours it cannot resolve"""
    s = path.read_text(encoding="utf-8")
    bad = [f"a page colour (var(--…)) an image cannot resolve"] if "var(--" in s else []
    words = re.findall(r'aria-label="([^"]*)"', s) + re.findall(r"<title>(.*?)</title>", s, re.S) + re.findall(r"<text[^>]*>(.*?)</text>", s, re.S)
    bad += banned(html.unescape(" · ".join(re.sub(r"<[^>]+>", "", w) for w in words)))
    return bad


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    A.write_all(IMG_DIR)                                      # the animations and the view maps, in both languages
    vmaps = WV.write_all(IMG_DIR)
    bad, sizes = [], []
    for lang in ("en", "es"):
        for page, lines in pages(lang, vmaps).items():
            text = absolute("\n".join(lines), lang)
            text = G.marks(text, G.B, G.NB, G.XB) if lang == "es" else text
            while "\n\n\n" in text: text = text.replace("\n\n\n", "\n\n")
            (ROOT / "docs/wiki" / f"{page}.md").write_text(text.rstrip() + "\n", encoding="utf-8", newline="")
            sizes.append((page, len(text.encode("utf-8")), len(re.findall(r"<img ", text))))
    used = set()
    for f in sorted((ROOT / "docs/wiki").glob("*.md")):          # every page, the ones written by hand too: words, images, tables and lists
        text = f.read_text(encoding="utf-8").replace("\r\n", "\n")
        bad += [(f.stem, b) for b in banned(text) + check_page(text)]
        used |= set(re.findall(r'<img src="img/([^"]+)"', text) + re.findall(r"\]\(img/([^)]+)\)", text))
    for f in sorted(IMG_DIR.glob("*.svg")):                    # every image: its words and colours, and that some page shows it
        bad += [(f"img/{f.name}", b) for b in check_image(f)]
        if f.name not in used: bad.append((f"img/{f.name}", "no page shows it"))
    for p, ctx in bad: print(f"{p}: {ctx}")
    for n, size, imgs in sizes: print(f"  {n}: {size / 1024:.0f} KB, {imgs} images")
    print(f"{len(sizes)} pages,", len(bad), "flags")
    return len(bad)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
