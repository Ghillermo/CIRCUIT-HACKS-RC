"""Animated step-by-step processes for the wiki (the user, 2026-11-14: «Create animated versions of the step-by-step processes»): every process
of the guide by views (docs/GUIA.md / GUIA.en.md) that takes two or more gestures in order, drawn frame by frame on the panel of the feature
list's figures (make_manual.svg: the same layout, sizes and colours), with a caption per frame, as one looping SVG per process and language:
docs/wiki/img/anim-<id>-<lang>.svg.

    python tools/make_anim.py            (writes the SVGs into docs/wiki/img; write_all(img_dir) returns [(id, file_en, file_es)])

The files play inside an <img> (the GitHub wiki): CSS @keyframes only, no script, no external fonts or images.  The panel is drawn once; every
element a frame draws appears once in the file, inside a group that is visible during the frames that show it (one step-end keyframe animation
per pattern of frames), so a file stays small.  Blinking and pulsing are CSS animations of their own.  Without animations (a viewer that does
not run them) the first frame shows.

Only what the published versions do: the RCs.  Where Beta 5.56 differs, the caption says so; a process only the beta has is beta=True and its
title says «Beta 5.56 only».  The version marks are the guide's («since RCx»).

A process: dict(id, view (the guide's anchor of the view), features (the feature list's section ids), beta, since, title {en, es}, frames).
A frame: dict(caption {en, es}, pads {n: (colour, label, dim)}, buttons {name: colour}, knobs {k: label}, press [controls], ms) and, optionally,
kcol {k: colour or (colour, dim)}, blink [controls], pulse [controls], turn {k: +1 / -1}, view {en, es} (the label at the top right).
Controls: pad numbers 1-32, the button names of the panel (make_manual.THIN / TRACKS / LEFT / RIGHT; "Pattern Settings"), "K1"-"K8".
Colours: make_manual.C's names (+ "sand"); a pad colour "a|b" alternates between a and b (a blink between two colours); a button colour may be
(colour, dim).  ms = None: from the caption's length (1.6-2.5 s).
"""
from __future__ import annotations
import html
import math
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_manual as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
IMG_DIR = ROOT / "docs/wiki/img"

# ---------------------------------------------------------------------------------------------------- the panel (as make_manual.svg draws it)
C = dict(M.C, sand="#ffd966")            # the guide's sand (the arpeggio's octaves): the LED table's light amber
DIM = M.DIM
PW, PG, X0 = 54, 62, 22                  # pad width, pitch, column 0 (make_manual.svg)
def colx(c): return X0 + c * PG
W = colx(10) + 14                        # 656
CAP_Y = 474                              # the caption box under the panel
LINE_H, WRAP, MAX_LINES = 17, 84, 4
H = CAP_Y + 30 + LINE_H * MAX_LINES + 14
PY0 = 216                                # the first row of pads
FINGER = "#ff6a13"                       # the badges' orange of make_manual.svg: the mark of a pressed control
TC = {"Synth 1": "magenta", "Synth 2": "pine", "MIDI 1": "blue", "MIDI 2": "pink", "Drum 1": "orange", "Drum 2": "yellow", "Drum 3": "purple",
      "Drum 4": "teal"}                  # the track colours (the LED table: Synth 1 magenta, Synth 2 green, MIDI 1 blue, MIDI 2 pink, Drum 1-4)


def _knob_xy(k):
    i = (k - 1) // 2
    return colx(2) + i * 96 + (48 if k % 2 == 0 else 0), (46 if k % 2 == 0 else 96)


def _buttons():
    """name -> (x, y, w, h, label lines) of every button, as make_manual.svg places them"""
    out = {}
    tsp, tw = 66, 60
    span = (len(M.THIN) - 1) * tsp + tw
    tx0 = colx(1) + (8 * PG - (PG - PW) - span) // 2
    for i, b in enumerate(M.THIN): out[b] = (tx0 + i * tsp, 140, tw, 18, [b])
    for c, b in enumerate(M.TRACKS): out[b] = (colx(c), 172, PW, 28, [b])
    for r in range(4):
        out[M.LEFT[r].replace("\n", " ")] = (colx(0), PY0 + r * PG + 8, PW, 38, M.LEFT[r].split("\n"))
        out[M.RIGHT[r].replace("\n", " ")] = (colx(9), PY0 + r * PG + 8, PW, 38, M.RIGHT[r].split("\n"))
    return out


BUTTONS = _buttons()


def _pad_xy(n):
    r, c = (n - 1) // 8, (n - 1) % 8
    return colx(c + 1), PY0 + r * PG


def hexcol(col):
    return C.get(col, col)


def luma(h):
    return (30 * int(h[1:3], 16) + 59 * int(h[3:5], 16) + 11 * int(h[5:7], 16)) // 100


def e(t): return html.escape(t, quote=False)
def ea(t): return html.escape(t, quote=True)


def f1(v): return ("%.1f" % v).rstrip("0").rstrip(".")


# ---------------------------------------------------------------------------------------------------- drawing
def base_panel():
    """the static panel: background, unlit knobs, buttons and pads (make_manual.svg's look)"""
    out = [f'<rect width="{W}" height="{H}" rx="18" fill="#17181b"/>']
    for k in range(1, 9):
        x, y = _knob_xy(k)
        out.append(f'<circle cx="{x}" cy="{y}" r="21" class="kb"/><text x="{x}" y="{y + 4}" class="kt">K{k}</text>')
    for name, (x, y, w, h, lines) in BUTTONS.items():
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" class="u"/>')
        for i, ln in enumerate(lines):
            out.append(f'<text x="{f1(x + w / 2)}" y="{f1(y + h / 2 + 3.5 + 11 * i - 5.5 * (len(lines) - 1))}" class="bt">{e(ln)}</text>')
    for n in range(1, 33):
        x, y = _pad_xy(n)
        out.append(f'<rect x="{x}" y="{y}" width="{PW}" height="{PW}" rx="7" class="u"/>')
    return out


def pad_numbers():
    out = []
    for n in range(1, 33):
        x, y = _pad_xy(n)
        out.append(f'<text x="{x + 4}" y="{y + 50}" class="pn">{n}</text>')
    return out


def pad_snip(n, spec, blink=False, pulse=False):
    col, lab = spec[0], spec[1] if len(spec) > 1 else ""
    dim = len(spec) > 2 and spec[2]
    x, y = _pad_xy(n)
    if not col:                          # a pad whose colour the figure does not claim: its label only
        lines = lab.split("\n")[:3] if lab else []
        return "".join(f'<text x="{x + PW // 2}" y="{f1(y + 26 + 12 * i - 6 * (len(lines) - 1))}" class="pl" fill="#aeb4ba">{e(ln)}</text>'
                       for i, ln in enumerate(lines))
    alt = col.split("|")
    fills = [hexcol(c) for c in alt]
    op = DIM if dim else 0.95
    parts = []
    if len(fills) == 2:                  # a blink between two colours: the second steady, the first blinking over it
        parts.append(f'<rect x="{x}" y="{y}" width="{PW}" height="{PW}" rx="7" fill="{fills[1]}" fill-opacity="{op}" stroke="#000"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="{PW}" height="{PW}" rx="7" fill="{fills[0]}" fill-opacity="{op}" stroke="#000" class="b"/>')
    else:
        parts.append(f'<rect x="{x}" y="{y}" width="{PW}" height="{PW}" rx="7" fill="{fills[0]}" fill-opacity="{op}" stroke="#000"/>')
    lines = lab.split("\n")[:3] if lab else []
    ink = "#e8eaed" if dim or luma(fills[-1]) < 110 else "#111"
    for i, ln in enumerate(lines):
        parts.append(f'<text x="{x + PW // 2}" y="{f1(y + 26 + 12 * i - 6 * (len(lines) - 1))}" class="pl" fill="{ink}">{e(ln)}</text>')
    s = "".join(parts)
    if blink and len(fills) == 1: s = f'<g class="b">{s}</g>'
    if pulse: s = f'<g class="v">{s}</g>'
    return s


def button_snip(name, col, blink=False, pulse=False):
    x, y, w, h, lines = BUTTONS[name]
    dim = False
    if isinstance(col, tuple): col, dim = col
    fill = hexcol(col)
    ink = "#111" if not dim and luma(fill) >= 110 else "#e8eaed"
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}"' + (f' fill-opacity="{DIM}"' if dim else "") + ' stroke="#111"/>'
    for i, ln in enumerate(lines):
        s += f'<text x="{f1(x + w / 2)}" y="{f1(y + h / 2 + 3.5 + 11 * i - 5.5 * (len(lines) - 1))}" class="bt" fill="{ink}">{e(ln)}</text>'
    if blink: s = f'<g class="b">{s}</g>'
    if pulse: s = f'<g class="v">{s}</g>'
    return s


def knob_snip(k, lab, col):
    """a knob's LED (col: a colour, (colour, dim) or None = the figure does not claim a colour: no ring) and its label"""
    x, y = _knob_xy(k)
    dim = False
    if isinstance(col, tuple): col, dim = col
    s = ""
    if col:
        s = (f'<circle cx="{x}" cy="{y}" r="21" fill="none" stroke="{hexcol(col)}" stroke-width="4"' +
             (f' stroke-opacity="{DIM + 0.1}"' if dim else "") + "/>")
    if lab:
        ly = y - 26 if k % 2 == 0 else y + 34
        s += f'<text x="{x}" y="{ly}" class="kl">{e(lab)}</text>'
    return s


def finger_snip(ctl):
    """the mark of a pressed or held control: a fingertip in a pad's free corner, an outline round a button, a ring round a knob (the labels
    stay readable)"""
    if isinstance(ctl, int):
        x, y = _pad_xy(ctl)
        return f'<circle cx="{x + PW - 13}" cy="{y + PW - 13}" r="9" class="fg"/>'
    if re.fullmatch(r"K[1-8]", ctl):
        x, y = _knob_xy(int(ctl[1]))
        return f'<circle cx="{x}" cy="{y}" r="25" class="fo"/>'
    x, y, w, h, _ = BUTTONS[ctl]
    return f'<rect x="{x - 3}" y="{y - 3}" width="{w + 6}" height="{h + 6}" rx="6" class="fo"/><circle cx="{x + w}" cy="{y + h}" r="5" class="fg"/>'


def turn_snip(k, d):
    """an arc arrow around knob k: d > 0 = turned right (clockwise), d < 0 = left"""
    x, y = _knob_xy(k)
    R = 28
    a0, a1 = (-150, -30) if d > 0 else (-30, -150)
    p0 = (x + R * math.cos(math.radians(a0)), y + R * math.sin(math.radians(a0)))
    p1 = (x + R * math.cos(math.radians(a1)), y + R * math.sin(math.radians(a1)))
    sweep = 1 if d > 0 else 0
    t = math.radians(a1)
    tx, ty = (-math.sin(t), math.cos(t)) if d > 0 else (math.sin(t), -math.cos(t))     # the direction of travel at the end
    nx, ny = -ty, tx
    tip = (p1[0] + 7 * tx, p1[1] + 7 * ty)
    b1 = (p1[0] + 4.5 * nx, p1[1] + 4.5 * ny)
    b2 = (p1[0] - 4.5 * nx, p1[1] - 4.5 * ny)
    return (f'<path d="M{f1(p0[0])} {f1(p0[1])}A{R} {R} 0 0 {sweep} {f1(p1[0])} {f1(p1[1])}" class="ta"/>'
            f'<path d="M{f1(tip[0])} {f1(tip[1])}L{f1(b1[0])} {f1(b1[1])}L{f1(b2[0])} {f1(b2[1])}z" fill="{FINGER}"/>')


def wrap(text, width=WRAP):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        if cur and len(cur) + 1 + len(w_) > width: lines.append(cur); cur = w_
        else: cur = (cur + " " + w_) if cur else w_
    if cur: lines.append(cur)
    return lines


def caption_snip(i, n, text):
    lines = wrap(text)
    assert len(lines) <= MAX_LINES, f"caption too long ({len(lines)} lines): {text}"
    y0 = CAP_Y + 44
    s = (f'<circle cx="40" cy="{y0 + 4}" r="17" fill="{FINGER}"/>'
         f'<text x="40" y="{y0 + 8.5}" class="sn">{i + 1}/{n}</text>')
    for j, ln in enumerate(lines):
        s += f'<text x="68" y="{y0 + LINE_H * j}" class="cp">{e(ln)}</text>'
    return s


def view_snip(label):
    return f'<text x="{colx(9)}" y="44" class="vw">{e(label)}</text>' if label else ""


CSS = (".kb{fill:#26282c;stroke:#3a3d42;stroke-width:2}.kt{font-size:11px;fill:#cfd3d8;text-anchor:middle}"
       ".u{fill:#2b2d31;stroke:#111}.bt{font-size:9.5px;fill:#aeb4ba;text-anchor:middle}"
       ".pn{font-size:8px;fill:#7d838a}.pl{font-size:9.5px;font-weight:bold;text-anchor:middle}.kl{font-size:10px;fill:#cfd3d8;text-anchor:middle}"
       f".fg{{fill:#fff;fill-opacity:.7;stroke:{FINGER};stroke-width:3}}.fo{{fill:none;stroke:{FINGER};stroke-width:3}}"
       f".ta{{fill:none;stroke:{FINGER};stroke-width:3}}"
       ".vw{font-size:15px;font-weight:bold;fill:#fff;text-anchor:middle}.ti{font-size:14px;font-weight:bold;fill:#fff}"
       ".cp{font-size:13px;fill:#e8eaed}.sn{font-size:11px;font-weight:bold;fill:#fff;text-anchor:middle}"
       ".b{animation:b .6s step-end infinite}@keyframes b{0%{opacity:1}50%{opacity:0}100%{opacity:0}}"
       ".v{animation:v 1.2s ease-in-out infinite}@keyframes v{0%{opacity:1}50%{opacity:.3}100%{opacity:1}}")

MARK = dict(en=dict(since="since", beta="Beta 5.56 only"), es=dict(since="desde", beta="solo Beta 5.56"))


def duration(f, lang):
    if f.get("ms"): return f["ms"]
    return max(1600, min(2500, 1000 + 9 * len(f["caption"][lang])))


def tr(x, lang):
    """a label: one text for both languages, or {en, es}"""
    return x.get(lang, "") if isinstance(x, dict) else (x or "")


def render(proc, lang):
    """one process in one language -> the SVG text"""
    frames = proc["frames"]
    n = len(frames)
    durs = [duration(f, lang) for f in frames]
    T = sum(durs)
    LAYERS = ("pads", "buttons", "knobs", "view", "marks", "caption")
    seen = {L: {} for L in LAYERS}                       # layer -> {snippet: set of frames}, in the order they come
    def add(layer, snip, i):
        if snip: seen[layer].setdefault(snip, set()).add(i)
    vdef = proc.get("vlabel", {})
    for i, f in enumerate(frames):
        blink, pulse = set(f.get("blink", ())), set(f.get("pulse", ()))
        for p, spec in sorted(f.get("pads", {}).items()):
            spec = (spec[0], tr(spec[1], lang) if len(spec) > 1 else "") + tuple(spec[2:])
            add("pads", pad_snip(p, spec, p in blink, p in pulse), i)
        for b, col in f.get("buttons", {}).items(): add("buttons", button_snip(b, col, b in blink, b in pulse), i)
        kcol, kl = f.get("kcol", {}), f.get("knobs", {})
        for k in sorted(set(kl) | set(kcol)): add("knobs", knob_snip(k, tr(kl.get(k, ""), lang), kcol.get(k)), i)
        add("view", view_snip(tr(f.get("view") or vdef, lang)), i)
        for ctl in f.get("press", ()): add("marks", finger_snip(ctl), i)
        for k, d in f.get("turn", {}).items(): add("marks", turn_snip(k, d), i)
        add("caption", caption_snip(i, n, f["caption"][lang]), i)
    mark = MARK[lang]["beta"] if proc.get("beta") else (f'{MARK[lang]["since"]} {proc["since"]}' if proc.get("since") else "")
    title = proc["title"][lang] + (f" · {mark}" if mark else "")
    classes = {}                                          # frozenset of frames -> class name
    def cls(fs):
        if fs not in classes: classes[fs] = "g%d" % len(classes)
        return classes[fs]
    body = base_panel()
    for L in LAYERS:
        if L == "caption":                                # the caption box: the title (with the version mark), then each frame's text
            body.append(f'<rect x="12" y="{CAP_Y}" width="{W - 24}" height="{H - CAP_Y - 10}" rx="10" fill="#222428" stroke="#3a3d42"/>'
                        f'<text x="24" y="{CAP_Y + 21}" class="ti">{e(title)}</text>')
        groups = {}
        for snip, fs in seen[L].items(): groups.setdefault(frozenset(fs), []).append(snip)
        for fs, snips in groups.items():
            if len(fs) == n: body.extend(snips)
            else: body.append(f'<g class="{cls(fs)}">' + "".join(snips) + "</g>")
        if L == "pads": body.extend(pad_numbers())
    # the CSS: one step-end animation per pattern of frames (opacity 1 while it shows; without animations, the first frame)
    css = [CSS]
    starts = [sum(durs[:i]) for i in range(n)]
    for fs, name in classes.items():
        pts, prev = [], None
        for i in range(n):
            v = 1 if i in fs else 0
            if v != prev: pts.append((100 * starts[i] / T, v)); prev = v
        pts.append((100, prev))
        kf = "".join(f"{('%.3f' % p).rstrip('0').rstrip('.')}%{{opacity:{v}}}" for p, v in pts)
        css.append(f".{name}{{animation:k{name} {T}ms step-end infinite" + ("" if 0 in fs else ";opacity:0") + "}"
                   f"@keyframes k{name}{{{kf}}}")
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Arial, Helvetica, sans-serif" '
            f'role="img" aria-label="{ea(title)}"><title>{e(title)}</title><style>{"".join(css)}</style>')
    return head + "".join(body) + "</svg>\n"


# ---------------------------------------------------------------------------------------------------- data helpers
PROCESSES = []


def F(en, es, pads=None, buttons=None, knobs=None, press=(), ms=None, **kw):
    """a frame (see the module's docstring)"""
    return dict(caption=dict(en=en, es=es), pads=dict(pads or {}), buttons=dict(buttons or {}), knobs=dict(knobs or {}), press=list(press), ms=ms, **kw)


def proc(pid, view, features, title_en, title_es, frames, beta=False, since="", vlabel=None):
    PROCESSES.append(dict(id=pid, view=view, features=list(features), beta=beta, since=since, title=dict(en=title_en, es=title_es),
                          frames=frames, vlabel=dict(en=vlabel[0], es=vlabel[1]) if vlabel else {}))


def V(en, es=None): return dict(en=en, es=es if es is not None else en)


def fill(pads, colour, dim=True, label=""):
    return {p: (colour, label, dim) for p in pads}


def merge(*ds):
    out = {}
    for d in ds: out.update(d)
    return out


# the stock tempo display's digits (3 x 4 pixels, rows top to bottom), as the device draws numbers on the pads (hundreds in columns 1-2,
# without the glyph's first column; tens in columns 3-5; units in columns 6-8)
GLYPH = ["111101101111", "010010010010", "011001010011", "111011001111", "100101111001", "011010001011", "010010011011", "011001001001",
         "111111101111", "011011001001"]


def digits(value, colour):
    out = {}
    def draw(g, c0, skip_first=False):
        for r in range(4):
            for c in range(3):
                if skip_first and c == 0: continue
                if GLYPH[g][3 * r + c] == "1":
                    col = c0 + c
                    if 0 <= col < 8: out[8 * r + col + 1] = (colour, "", False)
    h, t, u = value // 100, value // 10 % 10, value % 10
    if h: draw(h, -1, True)
    if h or t: draw(t, 2)
    draw(u, 5)
    return out


# ---------------------------------------------------------------------------------------------------- the views the processes use
def patches(track, chosen=None, extra=None):
    """a Preset view of patches or samples: every pad in the track's colour (dim), the chosen one white (as the original draws them)"""
    p = fill(range(1, 33), TC[track])
    if chosen: p[chosen] = ("white", "", False)
    p.update(extra or {})
    return p


def packs(loaded=1, extra=None):
    """the Packs view: some packs (each in its own colour on the device: grey here), the loaded one white"""
    p = fill(range(1, 7), "grey")
    p[loaded] = ("white", V("loaded", "cargado"), False)
    p.update(extra or {})
    return p


LOAD_PACK = dict(view=V("Packs", "Packs"))


def mfx(extra=None, head=None):
    """Master FX: the effects dim in their colours (bright while on), pad 7 the sample, pad 8 off, the song pointer's steps (dim violet;
    the playing one white), pad 32 the capture"""
    p = {1: ("orange", "Gater", True), 2: ("pine", "AF LP", True), 3: ("blue", "AF HP", True), 4: ("pink", "Digitise", True),
         5: ("magenta", "Phaser", True), 6: ("peach", "Glitch", True), 7: ("yellow", "Sample", True), 8: ("white", V("Off", "Apagar"), True)}
    p.update(fill(range(9, 25), "purple"))
    if head: p[head] = ("white", "", False)
    p[32] = ("red", V("Record", "Grabar"), True)
    p.update(extra or {})
    return p


MFX_V = V("Master FX")
ENGINE = {"off": ("white", V("Engine", "Motor"), True), "osc": ("green", V("Engine", "Motor"), False), "vadrum": ("orange", V("Engine", "Motor"), False),
          "sample": ("teal", V("Engine", "Motor"), False), "fm": ("purple", V("Engine", "Motor"), False)}


def mpre(page=1, engine="osc", extra=None):
    """MIDI 1's Preset view with its own synth: pads 1-5 the knob pages (the chosen one bright), 6 the matrix, 27 the engine"""
    p = {1: ("amber", "VCA\nVCF", page != 1), 2: ("green", "OSC 1", page != 2), 3: ("teal", "OSC 2", page != 3), 4: ("yellow", V("Seq.", "Sec."), page != 4),
         5: ("magenta", "Mod.", page != 5), 6: ("sky", V("Matrix", "Matriz"), page != 6), 27: ENGINE[engine]}
    p.update(extra or {})
    return p


SLOTS = "ppPpppeeppeeeeee"                  # pads 9-24: p = a patch (dim peach), P = the last used (bright peach), e = empty (violet)


def slots(spec=SLOTS, extra=None):
    p = {}
    for i, c in enumerate(spec):
        p[9 + i] = ("peach", "", True) if c == "p" else ("peach", "", False) if c == "P" else ("purple", "", False)
    p.update(extra or {})
    return p


def keys(rows=(3, 4), colour="magenta"):
    """a scale keyboard: rows of 8 notes, the roots (columns 1 and 8) bright"""
    p = {}
    for r in rows:
        for c in range(1, 9): p[8 * (r - 1) + c] = (colour, "", c not in (1, 8))
    return p


B1 = {"Synth 1": "magenta", "Preset": "magenta"}
BM = {"MIDI 1": "blue", "Preset": "blue"}
BD = {"Drum 1": "orange", "Preset": "orange"}


# ---------------------------------------------------------------------------------------------------- the processes
# ===== Synth 1 / 2 Preset view
SPV = ("Synth 1 Preset", "Preset de Synth 1")
proc("guardar-patch", "synth-preset", ["guardar-patch"], "Save a Synth 1 / 2 patch", "Guardar un patch de Synth 1 / 2", since="RC2", vlabel=SPV, frames=[
    F("With Synth 1 selected, press Preset: the pads are the pack's patches (4 pages), the chosen one white. Shape the sound first: the patch is "
      "saved as it sounds (knobs, MIDI received, macro destinations).",
      "Con Synth 1 elegido, pulsa Preset: los pads son los patches del pack (4 páginas), el elegido en blanco. Ajusta antes el sonido: se guarda "
      "el patch tal como suena (knobs, MIDI recibido, destinos de macro).",
      pads=patches("Synth 1", 1), buttons=B1, press=["Preset"]),
    F("Hold Clear and touch the slot to save into (pad 6): it asks, and the pad blinks white. Nothing is written yet; Clear + another pad moves "
      "the question. (Beta 5.56 only: meanwhile K1 picks the patch's category.)",
      "Mantén Clear y toca el hueco donde guardar (pad 6): pregunta, y el pad parpadea en blanco. Aún no se escribe nada; Clear + otro pad mueve "
      "la pregunta. (Solo Beta 5.56: mientras, K1 elige la categoría del patch.)",
      pads=patches("Synth 1", 1, {6: ("white", V("save?", "¿guardar?"), False)}), buttons=dict(B1, Clear="white"), press=["Clear", 6], blink=[6]),
    F("Clear + the same pad again within about 5 s: saved into that slot, which is now the chosen one (writes to the card). A tap without Clear, "
      "or the time running out, cancels it. Not in the internal memory's pack: there the Save LED turns red.",
      "Clear + el mismo pad otra vez antes de unos 5 s: guardado en ese hueco, que queda elegido (escribe en la tarjeta). Un toque sin Clear, o "
      "que pase el tiempo, lo anula. No en el pack de la memoria interna: ahí el LED de Save se pone rojo.",
      pads=patches("Synth 1", 6), buttons=dict(B1, Clear="white"), press=["Clear", 6]),
])

proc("intercambiar-patches", "synth-preset", ["pack"], "Swap two Synth 1 / 2 patches", "Intercambiar dos patches de Synth 1 / 2", vlabel=SPV, frames=[
    F("Synth 1's Preset view: hold Duplicate (it lights in this view).",
      "Vista Preset de Synth 1: mantén Duplicate (se ilumina en esta vista).",
      pads=patches("Synth 1", 1), buttons=dict(B1, Duplicate="white"), press=["Duplicate"]),
    F("Still holding Duplicate, touch patch A (pad 3): it is copied and blinks blue. Duplicate + A again cancels.",
      "Sin soltar Duplicate, toca el patch A (pad 3): queda copiado y parpadea en azul. Duplicate + A otra vez cancela.",
      pads=patches("Synth 1", 1, {3: ("blue", "A", False)}), buttons=dict(B1, Duplicate="white"), press=["Duplicate", 3], blink=[3]),
    F("Then touch patch B (pad 12): the two patches change places in the pack and B is chosen, so it sounds at once (writes to the card).",
      "Después toca el patch B (pad 12): los dos patches cambian de sitio en el pack y B queda elegido, así que suena al instante (escribe en "
      "la tarjeta).",
      pads=patches("Synth 1", 12, {3: ("magenta", "B", True), 12: ("white", "A", False)}), buttons=dict(B1, Duplicate="white"), press=["Duplicate", 12]),
])

proc("copiar-patch-pack", "synth-preset", ["pack"], "Copy a Synth 1 / 2 patch to another pack", "Copiar un patch de Synth 1 / 2 a otro pack",
     vlabel=SPV, frames=[
    F("In the pack that has the patch: Synth 1's Preset view, Duplicate + patch A (pad 5). It stays copied (blue while Duplicate is held), "
      "even after you let go of Duplicate.",
      "En el pack que tiene el patch: vista Preset de Synth 1, Duplicate + patch A (pad 5). Queda copiado (azul con Duplicate mantenido), "
      "aunque sueltes Duplicate.",
      pads=patches("Synth 1", 1, {5: ("blue", "A", False)}), buttons=dict(B1, Duplicate="white"), press=["Duplicate", 5], blink=[5]),
    F("Load the other pack, as always (the Packs view: Shift + Projects).",
      "Carga el otro pack, como siempre (la vista de packs: Shift + Projects).",
      pads=packs(1, {3: ("grey", V("other", "otro"), False)}), buttons={}, press=["Shift", "Projects"], **LOAD_PACK),
    F("Back in Synth 1's Preset view, hold Duplicate: the pad with A's number blinks yellow (a patch from another pack is waiting).",
      "De vuelta en la vista Preset de Synth 1, mantén Duplicate: el pad con el número de A parpadea en amarillo (espera un patch de otro pack).",
      pads=patches("Synth 1", 2, {5: ("yellow", "A", False)}), buttons=dict(B1, Duplicate="white"), press=["Duplicate"], blink=[5]),
    F("Duplicate + patch B (pad 14): A is copied over B in this pack and B is chosen, so it sounds at once. A's pack does not change; "
      "B may be empty (writes to the card).",
      "Duplicate + patch B (pad 14): A se copia sobre B en este pack y B queda elegido, así que suena al instante. El pack de A no cambia; "
      "B puede estar vacío (escribe en la tarjeta).",
      pads=patches("Synth 1", 14, {14: ("white", "A", False)}), buttons=dict(B1, Duplicate="white"), press=["Duplicate", 14]),
])

# ===== Drum Preset view
DPV = ("Drum 1 Preset", "Preset de Drum 1")
proc("intercambiar-samples", "drum-preset", ["pack"], "Swap two drum samples", "Intercambiar dos samples de drum", vlabel=DPV, frames=[
    F("With Drum 1 selected, press Preset: the pads are the pack's samples, the chosen one white. Hold Duplicate (it lights in this view).",
      "Con Drum 1 elegido, pulsa Preset: los pads son los samples del pack, el elegido en blanco. Mantén Duplicate (se ilumina en esta vista).",
      pads=patches("Drum 1", 1), buttons=dict(BD, Duplicate="white"), press=["Duplicate"]),
    F("Still holding Duplicate, touch sample A (pad 3): it blinks blue. Duplicate + A again cancels.",
      "Sin soltar Duplicate, toca el sample A (pad 3): parpadea en azul. Duplicate + A otra vez cancela.",
      pads=patches("Drum 1", 1, {3: ("blue", "A", False)}), buttons=dict(BD, Duplicate="white"), press=["Duplicate", 3], blink=[3]),
    F("Then touch sample B (pad 12): the two samples change places (files and table) and sound swapped at once (writes to the card).",
      "Después toca el sample B (pad 12): los dos samples cambian de sitio (ficheros y tabla) y suenan intercambiados al instante (escribe en "
      "la tarjeta).",
      pads=patches("Drum 1", 1, {3: ("orange", "B", True), 12: ("orange", "A", True)}), buttons=dict(BD, Duplicate="white"), press=["Duplicate", 12]),
])

proc("copiar-sample-pack", "drum-preset", ["pack"], "Copy a drum sample to another pack", "Copiar un sample de drum a otro pack", vlabel=DPV, frames=[
    F("In the sample's pack: Drum 1's Preset view, Duplicate + sample A (pad 3). It stays copied (it blinks blue while Duplicate is held), "
      "even after you let go.",
      "En el pack del sample: vista Preset de Drum 1, Duplicate + sample A (pad 3). Queda copiado (parpadea en azul con Duplicate mantenido), "
      "aunque lo sueltes.",
      pads=patches("Drum 1", 1, {3: ("blue", "A", False)}), buttons=dict(BD, Duplicate="white"), press=["Duplicate", 3], blink=[3]),
    F("Load the other pack, as always (the Packs view: Shift + Projects).",
      "Carga el otro pack, como siempre (la vista de packs: Shift + Projects).",
      pads=packs(1, {3: ("grey", V("other", "otro"), False)}), buttons={}, press=["Shift", "Projects"], **LOAD_PACK),
    F("Back in Drum 1's Preset view, hold Duplicate: the pad with A's number blinks yellow.",
      "De vuelta en la vista Preset de Drum 1, mantén Duplicate: el pad con el número de A parpadea en amarillo.",
      pads=patches("Drum 1", 1, {3: ("yellow", "A", False)}), buttons=dict(BD, Duplicate="white"), press=["Duplicate"], blink=[3]),
    F("Duplicate + sample B (pad 20): A is copied over B and sounds at once; B may be empty. It goes into B's place if it fits, otherwise into "
      "the free import memory: it never overwrites a sample that plays. A's pack does not change.",
      "Duplicate + sample B (pad 20): A se copia sobre B y suena al instante; B puede estar vacío. Va al sitio de B si cabe; si no, a la memoria "
      "libre de importación: nunca pisa un sample que suena. El pack de A no cambia.",
      pads=patches("Drum 1", 1, {20: ("orange", "A", True)}), buttons=dict(BD, Duplicate="white"), press=["Duplicate", 20]),
])

proc("captura-drum", "drum-preset", ["sample", "sustituir"], "Capture a sample and replace a drum with it",
     "Capturar un sample y sustituir un drum por él", frames=[
    F("Mixer, then Mixer again: Master FX. Pad 32 (red) records the capture, pad 7 (yellow) plays it.",
      "Mixer y otra vez Mixer: Master FX. El pad 32 (rojo) graba la captura y el pad 7 (amarillo) la toca.",
      pads=mfx(head=12), buttons={"Mixer": "white", "Play": "green"}, press=["Mixer"], view=MFX_V),
    F("Hold pad 32 while it plays: it records what is playing while you hold it (up to 3.46 s), without Master FX's effects. A short tap records "
      "until the next tap; Shift + pad 32 = armed: the next bar (stopped, from Play).",
      "Mantén el pad 32 mientras suena: graba lo que suena mientras lo mantienes (hasta 3,46 s), sin los efectos de Master FX. Un toque corto "
      "graba hasta el siguiente; Shift + pad 32 = armado: el compás siguiente (parado, desde Play).",
      pads=mfx({32: ("red", V("Record", "Grabar"), False)}, head=13), buttons={"Play": "green"}, press=[32], view=MFX_V),
    F("Touch pad 7: the capture plays. Its knobs: K1 pitch, K2 mode (yellow one-shot, green gate, blue loop), K3 start, K4 end. "
      "Shift + pad 7 = a latched loop, until you press it again.",
      "Toca el pad 7: suena la captura. Sus knobs: K1 tono, K2 modo (amarillo one-shot, verde gate, azul loop), K3 inicio, K4 final. "
      "Shift + pad 7 = bucle enganchado, hasta volver a pulsarlo.",
      pads=mfx({7: ("yellow", "Sample", False)}, head=14), buttons={"Play": "green"}, press=[7], view=MFX_V,
      knobs={1: V("Pitch", "Tono"), 2: V("Mode", "Modo"), 3: V("Start", "Inicio"), 4: V("End", "Final")}, kcol={2: "yellow"}),
    F("Drum 1, Preset (the drum to replace): hold Clear and touch one of its samples (pad 6): it asks, and the pad blinks white.",
      "Drum 1, Preset (el drum que quieres sustituir): mantén Clear y toca uno de sus samples (pad 6): pregunta, y el pad parpadea en blanco.",
      pads=patches("Drum 1", 1, {6: ("white", V("capture?", "¿captura?"), False)}), buttons=dict(BD, Clear="white"), press=["Clear", 6], blink=[6],
      view=V(*DPV)),
    F("Clear + the same pad again: confirmed: that sample is now the capture, and it sounds. It is volatile until you save the project (Save): "
      "then it is written into the pack, if it fits in the sample memory (writes to the card).",
      "Clear + el mismo pad otra vez: confirmado: ese sample es ahora la captura, y suena. Es volátil hasta que guardas el proyecto (Save): "
      "entonces se escribe en el pack, si cabe en la memoria de samples (escribe en la tarjeta).",
      pads=patches("Drum 1", 1, {6: ("orange", V("capture", "captura"), True)}), buttons=dict(BD, Clear="white"), press=["Clear", 6], view=V(*DPV)),
])

# ===== MIDI 1 / 2 Preset view: own-synth patches
MPV = ("MIDI 1 Preset", "Preset de MIDI 1")
proc("patches-propios", "midi-preset", ["patches-midi"], "Load, save and swap own-synth patches", "Cargar, guardar e intercambiar patches del sinte propio",
     since="RC2", vlabel=MPV, frames=[
    F("MIDI 1, Preset, with its own engine on (pad 27): pads 9-24 are 16 slots of own-synth patches: dim peach = a patch, bright = the last "
      "used, violet = empty. Octave ▼ / ▲ = the pages (since RC4, 8 pages: 128 slots a pack, shared by MIDI 1 and 2).",
      "MIDI 1, Preset, con su motor encendido (pad 27): los pads 9-24 son 16 huecos de patches del sinte propio: melocotón tenue = con patch, "
      "brillante = el último usado, violeta = vacío. Octave ▼ / ▲ = las páginas (desde RC4, 8 páginas: 128 huecos por pack, de MIDI 1 y 2).",
      pads=mpre(extra=slots()), buttons=dict(BM, **{"Oct ▼": "white"}), press=["Preset"]),
    F("Touch a slot = load it: the tonic sounds while you hold the pad (since RC4, Shift + pad = load it without the sound).",
      "Tocar un hueco = cargarlo: suena la tónica mientras mantienes el pad (desde RC4, Shift + pad = cargarlo sin que suene).",
      pads=mpre(extra=slots("pPppppeeppeeeeee")), buttons=dict(BM, **{"Oct ▼": "white"}), press=[10]),
    F("To save the sound: hold Clear and touch a slot (pad 15): it asks, and blinks white.",
      "Para guardar el sonido: mantén Clear y toca un hueco (pad 15): pregunta, y parpadea en blanco.",
      pads=mpre(extra=slots("pPppppeeppeeeeee", {15: ("white", V("save?", "¿guardar?"), False)})), buttons=dict(BM, Clear="white"), press=["Clear", 15],
      blink=[15]),
    F("Clear + the same slot again within about 5 s: saved, replacing what was there: the engine, its values, the matrix and the step-drummer "
      "setting (writes to the card). Beta 5.56 only: Duplicate + an empty slot saves there at once.",
      "Clear + el mismo hueco otra vez antes de unos 5 s: guardado, sustituyendo lo que hubiera: el motor, sus valores, la matriz y el ajuste "
      "del step-drummer (escribe en la tarjeta). Solo Beta 5.56: Duplicate + un hueco vacío guarda ahí al momento.",
      pads=mpre(extra=slots("ppppppPeppeeeeee")), buttons=dict(BM, Clear="white"), press=["Clear", 15]),
    F("To swap two: hold Duplicate and touch slot A (pad 9): it blinks.",
      "Para intercambiar dos: mantén Duplicate y toca el hueco A (pad 9): parpadea.",
      pads=mpre(extra=slots("ppppppPeppeeeeee", {9: ("peach", "A", False)})), buttons=dict(BM, Duplicate="white"), press=["Duplicate", 9], blink=[9]),
    F("Then slot B (pad 18): the two change places (onto an empty slot, the patch moves). There is no gesture to empty a slot: it is overwritten "
      "or moved.",
      "Después el hueco B (pad 18): los dos cambian de sitio (sobre un hueco vacío, el patch se mueve). No hay gesto para vaciar un hueco: se "
      "sobrescribe o se mueve.",
      pads=mpre(extra=slots("ppppppPeppeeeeee", {9: ("peach", "B", True), 18: ("peach", "A", True)})), buttons=dict(BM, Duplicate="white"),
      press=["Duplicate", 18]),
])

proc("copiar-patch-propio", "midi-preset", ["patches-entre-packs"], "Copy an own-synth patch to another pack", "Copiar un patch del sinte propio a otro pack",
     since="RC2", vlabel=MPV, frames=[
    F("With the source pack loaded: MIDI 1's Preset view, Duplicate + slot A (pad 11): the patch is remembered.",
      "Con el pack de origen cargado: vista Preset de MIDI 1, Duplicate + hueco A (pad 11): el patch queda recordado.",
      pads=mpre(extra=slots(extra={11: ("peach", "A", False)})), buttons=dict(BM, Duplicate="white"), press=["Duplicate", 11], blink=[11]),
    F("Load the other pack, as always (the Packs view: Shift + Projects).",
      "Carga el otro pack, como siempre (la vista de packs: Shift + Projects).",
      pads=packs(1, {3: ("grey", V("other", "otro"), False)}), buttons={}, press=["Shift", "Projects"], **LOAD_PACK),
    F("Back in MIDI 1's Preset view, Duplicate lights yellow: a patch is waiting.",
      "De vuelta en la vista Preset de MIDI 1, Duplicate se enciende en amarillo: hay un patch esperando.",
      pads=mpre(extra=slots("pPpppeeeeeeeeeee")), buttons=dict(BM, Duplicate="yellow")),
    F("Duplicate + slot B (pad 19): the patch is written there (engine, values and name); it works for several slots (writes to the card). "
      "Within one pack, Duplicate + A + B swaps instead.",
      "Duplicate + hueco B (pad 19): el patch se escribe ahí (motor, valores y nombre); sirve para varios huecos (escribe en la tarjeta). "
      "Dentro de un mismo pack, Duplicate + A + B intercambia.",
      pads=mpre(extra=slots("ppppppeeeePeeeee", {19: ("peach", "A", False)})), buttons=dict(BM, Duplicate="yellow"), press=["Duplicate", 19]),
])

# ===== the editors
SRC = {25: ("magenta", V("Noise", "Ruido"), False), 26: ("magenta", "In 1", True), 27: ("magenta", "In 2", True), 28: ("magenta", "In 1\ninv", True),
       29: ("magenta", "In 2\ninv", True), 30: ("purple", "Step\ndrum", True)}
DIMTEAL = {k: ("teal", True) for k in range(1, 9)}
proc("editor-macros", "synth-fuente", ["destinos-macro"], "Edit the macro knobs' destinations", "Editar los destinos de los macro knobs", since="RC2",
     vlabel=("Synth source", "Fuente del sinte"), frames=[
    F("With Synth 1's view on screen, press Synth 1 again: the source view. Pad 32 (teal) turns the macro destination editor on: the knobs no "
      "longer move the macros.",
      "Con la vista de Synth 1 en pantalla, pulsa Synth 1 otra vez: la vista de la fuente. El pad 32 (verde azulado) enciende el editor de "
      "destinos: los knobs ya no mueven los macros.",
      pads=merge(SRC, {32: ("teal", "Macros", False)}), buttons={"Synth 1": "magenta"}, press=[32]),
    F("Turn a knob (K4) to pick its macro: its LED turns white; the first turn changes nothing. The pads draw the current field's number: "
      "the slot, 1-4, in yellow.",
      "Gira un knob (K4) para elegir su macro: su LED se pone blanco; el primer giro no cambia nada. Los pads dibujan el número del campo "
      "actual: la ranura, 1-4, en amarillo.",
      pads=digits(1, "yellow"), buttons={"Synth 1": "magenta"}, kcol=merge(DIMTEAL, {4: "white"}), turn={4: 1}),
    F("The knob changes the field; Octave ▼ = the next field, Octave ▲ = the previous one: slot → start (green) → end (amber) → destination → "
      "depth. Start, here 0.",
      "El knob cambia el campo; Octave ▼ = el campo siguiente, Octave ▲ = el anterior: ranura → inicio (verde) → fin (ámbar) → destino → "
      "profundidad. El inicio, aquí 0.",
      pads=digits(0, "green"), buttons={"Synth 1": "magenta"}, kcol=merge(DIMTEAL, {4: "white"}), press=["Oct ▼"]),
    F("Destination: its CC number in white (74 = filter cutoff), or an NRPN in light blue, magenta or violet (banks 0, 1, 2). The knob walks "
      "the 31 parameters with a CC by number, then the 39 that only have an NRPN.",
      "Destino: su número de CC en blanco (74 = corte del filtro), o un NRPN en azul claro, magenta o violeta (bancos 0, 1, 2). El knob "
      "recorre los 31 parámetros con CC por número y luego los 39 que solo tienen NRPN.",
      pads=digits(74, "white"), buttons={"Synth 1": "magenta"}, kcol=merge(DIMTEAL, {4: "white"}), press=["Oct ▼"], turn={4: 1}),
    F("Depth: teal = positive, red = negative (here +40). The changes sound at once.",
      "Profundidad: verde azulado = positiva, rojo = negativa (aquí +40). Los cambios suenan al momento.",
      pads=digits(40, "teal"), buttons={"Synth 1": "magenta"}, kcol=merge(DIMTEAL, {4: "white"}), press=["Oct ▼"], turn={4: 1}),
    F("Any pad releases the macro; pad 32 turns the editor off. To keep the destinations in the pack, save the patch (Preset view: Clear + pad, "
      "twice).",
      "Cualquier pad suelta el macro; el pad 32 apaga el editor. Para dejar los destinos en el pack, guarda el patch (vista Preset: Clear + pad, "
      "dos veces).",
      pads=merge(SRC, {32: ("teal", "Macros", True)}), buttons={"Synth 1": "magenta"}, press=[32]),
])

CCP = {25: ("magenta", "CC", False), 27: ENGINE["off"]}
proc("editor-cc", "midi-cc", ["editor-cc"], "Change the CC a MIDI macro knob sends", "Cambiar el CC que manda un macro knob MIDI", vlabel=MPV, frames=[
    F("MIDI 1, Preset, with the own engine off (pad 27 grey): touch pad 25 (magenta): the CC editor is on.",
      "MIDI 1, Preset, con el motor propio apagado (pad 27 gris): toca el pad 25 (magenta): el editor de CC se enciende.",
      pads=CCP, buttons=BM, press=[25]),
    F("Move a knob (K5): it is picked, and the pads draw the number it sends: the CC, in magenta (here 74). 99, 98 or 6 = a 7-bit NRPN and "
      "38 = a 14-bit NRPN: they have more fields (MSB, LSB).",
      "Mueve un knob (K5): queda elegido, y los pads dibujan el número que manda: el CC, en magenta (aquí 74). 99, 98 o 6 = NRPN de 7 bits y "
      "38 = NRPN de 14 bits: tienen más campos (MSB, LSB).",
      pads=digits(74, "magenta"), buttons=dict(BM, **{"Oct ▼": "magenta"}), turn={5: 1}),
    F("Octave ▼ = the next field, Octave ▲ = the previous one; turn the knob to change the value. For a CC: number → start (amber) → end.",
      "Octave ▼ = el campo siguiente, Octave ▲ = el anterior; gira el knob para cambiar el valor. Con un CC: número → inicio (ámbar) → fin.",
      pads=digits(0, "amber"), buttons=dict(BM, **{"Oct ▼": "amber", "Oct ▲": "amber"}), press=["Oct ▼"]),
    F("The end, in light blue: the knob sends its CC from start to end.",
      "El fin, en azul claro: el knob manda su CC del inicio al fin.",
      pads=digits(127, "sky"), buttons=dict(BM, **{"Oct ▼": "sky", "Oct ▲": "sky"}), press=["Oct ▼"], turn={5: 1}),
    F("Octave ▼ once more: the save step (pad 26 and Save blink green); Octave ▼ again saves (pad 26 saves at any time). Saving leaves the "
      "editor, back to the Preset view.",
      "Octave ▼ una vez más: el paso de guardar (el pad 26 y Save parpadean en verde); Octave ▼ otra vez guarda (el pad 26 guarda en "
      "cualquier momento). Al guardar sales del editor a la vista Preset.",
      pads=merge(CCP, {26: ("green", "Save", False)}), buttons=dict(BM, Save="green", **{"Oct ▼": "green", "Oct ▲": "green"}), press=["Oct ▼"],
      blink=[26, "Save"]),
    F("To discard instead: any view button, pad 25 or a template pad leaves without saving.",
      "Para descartar: cualquier botón de vista, el pad 25 o un pad de plantilla salen sin guardar.",
      pads={25: ("magenta", "CC", True), 27: ENGINE["off"]}, buttons=BM, press=[25]),
])

# ===== Projects and packs
PKV = ("Packs", "Packs")
proc("borrar-pack", "packs", ["pack", "pack-interno"], "Delete a pack", "Borrar un pack", vlabel=PKV, frames=[
    F("Shift + Projects: the Packs view (here the first pack, the internal memory's, is the loaded one, white). In this view Clear lights "
      "steady white.",
      "Shift + Projects: la vista de packs (aquí el primero, el de la memoria interna, es el cargado, en blanco). En esta vista Clear se ve "
      "blanco fijo.",
      pads=packs(1), buttons={"Clear": "white"}, press=["Shift", "Projects"]),
    F("Touch Clear (no Shift: Shift + Clear is the metronome): for about 5 s the packs that can be deleted blink, never the loaded one.",
      "Toca Clear (sin Shift: Shift + Clear es el metrónomo): durante unos 5 s parpadean los packs que se pueden borrar, nunca el cargado.",
      pads=packs(1, fill(range(2, 7), "red", False)), buttons={"Clear": "white"}, press=["Clear"], blink=[2, 3, 4, 5, 6]),
    F("Touch the pack to delete (pad 4): only that one blinks; it is not loaded.",
      "Toca el pack que quieres borrar (pad 4): solo ese parpadea; no se carga.",
      pads=packs(1, {4: ("red", "", False)}), buttons={"Clear": "white"}, press=[4], blink=[4]),
    F("Clear again within 5 s: deleted; the slot can be used again after a restart. The internal memory's pack (the first one) is read-only "
      "for the mod: it is never deleted (writes to the card).",
      "Clear otra vez antes de 5 s: borrado; el hueco se reutiliza tras reiniciar. El pack de la memoria interna (el primero) es de solo "
      "lectura para el mod: nunca se borra (escribe en la tarjeta).",
      pads=packs(1), buttons={"Clear": "white"}, press=["Clear"]),
])

PJ = merge(fill(range(1, 7), "blue"), {4: ("white", V("loaded", "cargado"), False)})
proc("copiar-proyecto", "projects", ["copiar-proyectos"], "Copy a project", "Copiar un proyecto", since="RC2", vlabel=("Projects", "Projects"), frames=[
    F("The Projects view: hold Duplicate and touch a saved project, A (pad 5): it is the source, blinking yellow. Duplicate + A again forgets it.",
      "La vista Projects: mantén Duplicate y toca un proyecto guardado, A (pad 5): es la fuente, y parpadea en amarillo. Duplicate + A otra vez "
      "la olvida.",
      pads=merge(PJ, {5: ("yellow", "A", False)}), buttons={"Projects": "white", "Duplicate": "white"}, press=["Duplicate", 5], blink=[5]),
    F("Duplicate + an empty slot B (pad 7): copied at once, and it shows yellow. The source stays chosen for more copies.",
      "Duplicate + un hueco vacío B (pad 7): copiado al momento, y se ve en amarillo. La fuente sigue elegida para más copias.",
      pads=merge(PJ, {5: ("yellow", "A", False), 7: ("yellow", "B", False)}), buttons={"Projects": "white", "Duplicate": "white"},
      press=["Duplicate", 7], blink=[5]),
    F("Duplicate + a slot in use (pad 2): it blinks white: Duplicate + the same slot again within about 5 s replaces it. The loaded project's "
      "slot (white) is never written.",
      "Duplicate + un hueco ocupado (pad 2): parpadea en blanco: Duplicate + el mismo hueco otra vez antes de unos 5 s lo sustituye. El hueco "
      "del proyecto cargado (blanco) nunca se escribe.",
      pads=merge(PJ, {5: ("yellow", "A", False), 7: ("yellow", "B", False), 2: ("white", "?", False)}), buttons={"Projects": "white", "Duplicate": "white"},
      press=["Duplicate", 2], blink=[5, 2]),
    F("To another pack: pick the source, load the other pack, go back to Projects and Duplicate + B. The project saved on the card is copied "
      "(save first); for a moment the device does not respond (writes to the card).",
      "A otro pack: elige la fuente, carga el otro pack, vuelve a Projects y Duplicate + B. Se copia el proyecto guardado en la tarjeta "
      "(guarda antes); unos instantes el aparato no responde (escribe en la tarjeta).",
      pads=merge(PJ, {5: ("yellow", "A", False), 7: ("yellow", "B", False), 2: ("yellow", "B", False)}), buttons={"Projects": "white", "Duplicate": "white"},
      press=["Duplicate", 2], blink=[5]),
])

# ===== buttons of every view
proc("cuenta-atras", "botones", ["setup"], "Record with the count-in", "Grabar con la cuenta atrás", since="RC2", frames=[
    F("Hold Shift: Clear's LED shows the metronome state. Shift + Clear steps through four: no metronome (red) …",
      "Mantén Shift: el LED de Clear enseña el estado del metrónomo. Shift + Clear pasa por cuatro: sin metrónomo (rojo) …",
      buttons={"Clear": "red"}, press=["Shift", "Clear"], ms=1700),
    F("… metronome (green) …", "… metrónomo (verde) …", buttons={"Clear": "green"}, press=["Shift", "Clear"], ms=1600),
    F("… count-in only (magenta) …", "… solo cuenta atrás (magenta) …", buttons={"Clear": "magenta"}, press=["Shift", "Clear"], ms=1600),
    F("… count-in and metronome (teal). The click's volume is the stock's: Tempo/Swing and K5.",
      "… cuenta atrás y metrónomo (verde azulado). El volumen del clic es el de stock: Tempo/Swing y K5.",
      buttons={"Clear": "teal"}, press=["Shift", "Clear"]),
    F("With the transport stopped, press Record: armed (red).", "Con el transporte parado, pulsa Record: armado (rojo).", buttons={"Record": "red"}, press=["Record"], ms=1700),
    F("Press Play: one bar of count-in, 4 clicks at the project's tempo (as a slave, the external clock's), while Record blinks red. Play "
      "during the count cancels it.",
      "Pulsa Play: un compás de cuenta atrás, 4 clics al tempo del proyecto (como esclavo, al del reloj externo), mientras Record parpadea "
      "en rojo. Play durante la cuenta la cancela.",
      buttons={"Record": "red"}, press=["Play"], blink=["Record"]),
    F("Then the recording starts. The count-in is saved with the project; with the Mixer's cue mode (since RC4) the click is heard in the cue "
      "only.",
      "Después arranca la grabación. La cuenta atrás se guarda con el proyecto; con el modo cue del Mixer (desde RC4) el clic suena solo en "
      "el cue.",
      buttons={"Record": "red", "Play": "green"}),
])

proc("cuantizar", "botones", ["mixer-cue"], "Quantize a pattern", "Cuantizar un patrón", since="RC2", frames=[
    F("Select the track to quantize (here Synth 1): its playing pattern has notes recorded off the grid.",
      "Elige la pista que quieres cuantizar (aquí Synth 1): su patrón que suena tiene notas grabadas fuera de la rejilla.",
      buttons={"Synth 1": "magenta", "Note": "magenta"}, press=["Synth 1"]),
    F("Hold Shift: Play lights yellow (it is available).",
      "Mantén Shift: Play se ilumina en amarillo (está disponible).",
      buttons={"Synth 1": "magenta", "Note": "magenta", "Play": "yellow"}, press=["Shift"]),
    F("Shift + Play: quantized. Notes and hits on micro steps 1-2 go to the start of their step, on 3-5 to the start of the next one (the last "
      "step's, to the first); Play turns green. On the drums a step with several hits (a roll) stays.",
      "Shift + Play: cuantizado. Las notas y los golpes en los micropasos 1-2 van al inicio de su paso, en los 3-5 al del siguiente (los del "
      "último paso, al primero); Play se pone verde. En los drums, un paso con varios golpes (un redoble) se queda.",
      buttons={"Synth 1": "magenta", "Note": "magenta", "Play": "green"}, press=["Shift", "Play"]),
])

# ===== Synth 1 / 2 track view
NV = ("Note", "Note")
proc("teclado-partido", "synth-nota", ["teclado-partido"], "Split the keyboard between two tracks", "Partir el teclado entre dos pistas", since="RC2",
     vlabel=NV, frames=[
    F("Synth 1's Note view: its keyboard on the lower rows. Hold Synth 1 …",
      "La vista Note de Synth 1: su teclado en las filas de abajo. Mantén Synth 1 …",
      pads=keys(), buttons={"Synth 1": "magenta", "Note": "magenta"}, press=["Synth 1"]),
    F("… and press Synth 2: the split keyboard. The top two rows play the track held first (Synth 1), the bottom two the other one (Synth 2), "
      "each with its scale, octave, velocity and colours. Since RC2.02, any pair of Synth 1, Synth 2, MIDI 1 and MIDI 2.",
      "… y pulsa Synth 2: el teclado partido. Las dos filas de arriba tocan la pista que mantuviste primero (Synth 1) y las dos de abajo la otra "
      "(Synth 2), cada una con su escala, su octava, su velocity y sus colores. Desde RC2.02, cualquier par de Synth 1, Synth 2, MIDI 1 y MIDI 2.",
      pads=merge(keys((1, 2)), keys((3, 4), "pine")), buttons={"Synth 1": "magenta", "Synth 2": "pine", "Note": "magenta"},
      press=["Synth 1", "Synth 2"], view=V("Split", "Partido")),
    F("The knobs and Octave are those of the track pressed first. Since RC4, hold another track button (here MIDI 1): while you hold it, the "
      "8 knobs and their lights are that track's.",
      "Los knobs y Octave son los de la primera pista que pulsaste. Desde RC4, mantén otro botón de pista (aquí MIDI 1): mientras lo "
      "mantienes, los 8 knobs y sus luces son los de esa pista.",
      pads=merge(keys((1, 2)), keys((3, 4), "pine")), buttons={"Synth 1": "magenta", "Synth 2": "pine", "MIDI 1": "blue", "Note": "magenta"},
      press=["MIDI 1"], kcol={k: ("blue", k % 3 != 0) for k in range(1, 9)}, view=V("Split", "Partido")),
    F("A short tap on a track button (no knob turned) or a view button closes it; the held notes are released. Play, Record, Octave and Shift "
      "do not close it.",
      "Un toque corto a un botón de pista (sin girar un knob) o un botón de vista lo cierra; las notas pulsadas se sueltan. Play, Record, "
      "Octave y Shift no lo cierran.",
      pads=keys(), buttons={"Synth 1": "magenta", "Note": "magenta"}, press=["Note"]),
])

STEPS_Y = fill(range(1, 17), "yellow", False)
proc("latch", "synth-nota", ["arpegiador", "atajos"], "Latch notes and write them into a step", "Fijar notas (latch) y escribirlas en un paso",
     since="RC4", vlabel=NV, frames=[
    F("Synth 1's Note view. Hold Shift and press a key (pad 27): the note sounds and keeps sounding when you let go (a latch).",
      "La vista Note de Synth 1. Mantén Shift y pulsa una tecla (pad 27): la nota suena y sigue sonando al soltarla (un latch).",
      pads=merge(keys(), STEPS_Y, {27: ("teal", "", False)}), buttons={"Synth 1": "magenta", "Note": "magenta"}, press=["Shift", 27]),
    F("Shift + another key (pad 29): latched too. While Shift is held, the latched keys light bright teal and, with notes latched, the step "
      "pads yellow.",
      "Shift + otra tecla (pad 29): también fijada. Con Shift mantenido, las teclas fijadas se ven verde azulado brillante y, con notas "
      "fijadas, los pads de paso en amarillo.",
      pads=merge(keys(), STEPS_Y, {27: ("teal", "", False), 29: ("teal", "", False)}), buttons={"Synth 1": "magenta", "Note": "magenta"},
      press=["Shift", 29]),
    F("Let go of Shift: both notes keep sounding (a sounding note lights white). With the arpeggiator on, the latched notes are arpeggiated.",
      "Suelta Shift: las dos notas siguen sonando (la nota que suena se ve blanca). Con el arpegiador encendido, las notas fijadas se arpegian.",
      pads=merge(keys(), {27: ("white", "", False), 29: ("white", "", False)}), buttons={"Synth 1": "magenta", "Note": "magenta"}),
    F("Shift + a step (pad 5): the latched notes are written into that step (up to 6, one step long, velocity 100). Beta 5.56 only: the steps "
      "keep their colours and the step being written lights teal while held.",
      "Shift + un paso (pad 5): las notas fijadas se escriben en ese paso (hasta 6, un paso de largo, velocity 100). Solo Beta 5.56: los pasos "
      "no cambian de color y el que se escribe se ve verde azulado mientras lo mantienes.",
      pads=merge(keys(), STEPS_Y, {27: ("teal", "", False), 29: ("teal", "", False)}), buttons={"Synth 1": "magenta", "Note": "magenta"},
      press=["Shift", 5]),
    F("Press a latched key again (pad 27): it stops, and that press does nothing else. Clear + Synth 1 lets go of every latched note. Not saved.",
      "Pulsa otra vez una tecla fijada (pad 27): se para, y esa pulsación no hace nada más. Clear + Synth 1 suelta todas las notas fijadas. "
      "No se guarda.",
      pads=merge(keys(), {29: ("white", "", False)}), buttons={"Synth 1": "magenta", "Note": "magenta"}, press=[27]),
])

XN = ("Expanded Note", "Note ampliada")
CH_BASE = merge(keys((3, 4)), fill(range(1, 9), "white"), {9: ("blue", V("Root", "Fund."), False)}, fill(range(10, 13), "white"),
                {10: ("white", V("1st", "1.ª"), True), 11: ("white", V("2nd", "2.ª"), True), 12: ("white", V("3rd", "3.ª"), True), 13: ("white", V("Open", "Abierto"), True),
                 14: ("white", V("Root\n−8ve", "Fund.\n−8va"), True), 15: ("white", V("Diat.", "Diat."), True), 16: ("white", "Latch", True)})
CH_TYPES = {1: V("Maj", "May"), 2: V("Min", "Men"), 3: "7", 4: "m7", 5: "maj7", 6: "sus4", 7: "dim", 8: V("Aug", "Aum")}
def chords(chosen=1, shift=False, extra=None):
    p = dict(CH_BASE)
    for k, lab in CH_TYPES.items(): p[k] = ("white", lab, k != chosen)
    if chosen: p[chosen] = ("white", CH_TYPES[chosen], False)
    if shift:
        for k in range(1, 8): p[k] = ("yellow", "", False)
        p[8] = ("green", V("Chords", "Acordes"), False)
    p.update(extra or {})
    return p
proc("acordes", "synth-nota", ["acordes"], "Play chords from one pad", "Tocar acordes con un pad", since="RC4", vlabel=XN, frames=[
    F("Synth 1 (or Synth 2, MIDI 1 / 2): press Note twice: the expanded Note view, every pad a key.",
      "Synth 1 (o Synth 2, MIDI 1 / 2): pulsa Note dos veces: la vista Note ampliada, cada pad una tecla.",
      pads=keys((1, 2, 3, 4)), buttons={"Synth 1": "magenta", "Note": "amber"}, press=["Note"]),
    F("Shift + pad 8: the chord screen on (with Shift, pad 8 is yellow; green once on). With Shift, row 1 shows the other chord types in "
      "yellow: sus2, 6, m6, add9, 9, 7sus4, fifth.",
      "Shift + pad 8: la pantalla de acordes se enciende (con Shift el pad 8 se ve amarillo; verde encendida). Con Shift, la fila 1 enseña en "
      "amarillo los otros tipos: sus2, 6, m6, add9, 9, 7sus4, quinta.",
      pads=chords(1, True), buttons={"Synth 1": "magenta", "Note": "amber"}, press=["Shift", 8]),
    F("Row 1 = the chord type (major, minor, 7, m7, maj7, sus4, dim, aug), the chosen one white. Pads 9-12 = the inversion (blue); 13 open "
      "voicing, 14 the root an octave down, 15 diatonic (green when on).",
      "Fila 1 = el tipo de acorde (mayor, menor, 7, m7, maj7, sus4, dim, aum), el elegido en blanco. Pads 9-12 = la inversión (azul); 13 voicing "
      "abierto, 14 la fundamental una octava abajo, 15 diatónico (verdes encendidos).",
      pads=chords(2), buttons={"Synth 1": "magenta", "Note": "amber"}, press=[2]),
    F("Hold a root on rows 3-4 (pad 25): its chord sounds, up to 6 notes with the pad's velocity; with Record it is recorded as plain notes of "
      "the pattern. Changing the type or a modifier changes the sounding chord at once.",
      "Mantén una fundamental de las filas 3-4 (pad 25): suena su acorde, hasta 6 notas con la velocity del pad; con Record se graba como "
      "notas normales del patrón. Cambiar el tipo o un modificador cambia al momento el acorde que suena.",
      pads=chords(2, extra={25: ("white", "", False)}), buttons={"Synth 1": "magenta", "Note": "amber"}, press=[25]),
    F("Shift + a root = the chord latched (its root bright teal with Shift): it sounds until you press that root again or Clear + the track "
      "button. In the RCs pad 16 is the chord latch too. Type and modifiers are not saved.",
      "Shift + fundamental = el acorde fijado (su fundamental verde azulado brillante con Shift): suena hasta volver a pulsar esa fundamental "
      "o Clear + el botón de la pista. En las RC el pad 16 también fija el acorde. El tipo y los modificadores no se guardan.",
      pads=chords(2, True, {27: ("teal", "", False)}), buttons={"Synth 1": "magenta", "Note": "amber"}, press=["Shift", 27]),
])

# ===== Scales: the custom scale and Jankó
ED_KEYS = [25, 26, 27, 28, 29, 30, 31, 32, 18, 19, 21, 22, 23, 9, 10, 11, 12, 13, 14, 15, 16, 2, 3, 5, 6, 7]
def editor(notes=(), period=None, extra=None):
    p = fill(ED_KEYS, "white")
    p[25] = ("white", V("Root", "Tónica"), False)
    for k in notes: p[k] = ("green", "", False)
    if period: p[period] = ("blue", V("Period", "Periodo"), False)
    p.update(extra or {})
    return p
SCV = ("Scales", "Scales")
proc("escala-propia", "escalas", ["escala-propia"], "Make a custom scale", "Hacer una escala propia", since="RC2", vlabel=SCV, frames=[
    F("Shift + Scales (Scales lights yellow while Shift is held): the custom scale editor: two octaves of a piano from the root (white). Row 4 = "
      "the first octave's white keys, row 3 its black keys; rows 2 / 1 the second octave. Free keys dim.",
      "Shift + Scales (Scales se ve amarillo con Shift pulsado): el editor de la escala propia: dos octavas de piano desde la tónica (blanca). "
      "Fila 4 = las teclas blancas de la primera octava, fila 3 sus negras; filas 2 / 1 la segunda octava. Teclas libres, tenues.",
      pads=editor(), buttons={"Scales": "yellow"}, press=["Shift", "Scales"]),
    F("Press a key to add it (pad 26, +2): the highest key pressed is the period (blue): the root of the next iteration, which need not be the "
      "octave.",
      "Pulsa una tecla para añadirla (pad 26, +2): la tecla más alta pulsada es el periodo (azul): la tónica de la siguiente iteración, que no "
      "tiene por qué ser la octava.",
      pads=editor(period=26), buttons={"Scales": "white"}, press=[26]),
    F("Another one above (pad 28, +5): it is the new period and the previous key becomes a note of the scale (green).",
      "Otra más arriba (pad 28, +5): pasa a ser el periodo y la anterior queda como nota de la escala (verde).",
      pads=editor((26,), 28), buttons={"Scales": "white"}, press=[28]),
    F("A key below the period (pad 19, +3) is one more note. Pressing a key again removes it; up to 7.",
      "Una tecla por debajo del periodo (pad 19, +3) es una nota más. Pulsar una tecla otra vez la quita; hasta 7.",
      pads=editor((26, 19), 28), buttons={"Scales": "white"}, press=[19]),
    F("+7 (pad 29) as the period: a scale of root, +2, +3, +5 that repeats every 7 semitones.",
      "+7 (pad 29) como periodo: una escala de tónica, +2, +3, +5 que se repite cada 7 semitonos.",
      pads=editor((26, 19, 28), 29), buttons={"Scales": "white"}, press=[29]),
    F("On the note tracks every row of pads is one iteration (with 4 notes or fewer, two a row); the quantising and random-mutate use it too. "
      "Saved with the project; a stock scale (pads 17-32 out of the editor) turns it off.",
      "En las pistas de notas cada fila de pads es una iteración (con 4 notas o menos, dos por fila); también la usan el cuantizado y el "
      "random-mutate. Se guarda con el proyecto; una escala de stock (pads 17-32 fuera del editor) la apaga.",
      pads=editor((26, 19, 28), 29), buttons={"Scales": "white"}, press=["Scales"]),
])

JK_ROW_LOW = ["C", "D", "E", "F♯", "G♯", "A♯", "C", "D"]
JK_ROW_UP = ["B", "C♯", "D♯", "F", "G", "A", "B", "C♯"]
NOTES = ["C", "C♯", "D", "D♯", "E", "F", "F♯", "G", "G♯", "A", "A♯", "B"]
def janko(shift=0):
    p = {}
    for r, row in ((4, JK_ROW_LOW), (3, JK_ROW_UP), (2, JK_ROW_LOW), (1, JK_ROW_UP)):
        for c, nm in enumerate(row):
            nm = NOTES[(NOTES.index(nm) + shift) % 12]
            p[8 * (r - 1) + c + 1] = ("magenta", nm, nm != "C")
    return p
proc("janko", "escalas", ["escala-propia"], "Switch on the Jankó layout", "Encender la disposición Jankó", since="RC4", vlabel=SCV, frames=[
    F("In the custom scale editor (Shift + Scales), hold Shift: pad 8, top right, lights yellow.",
      "En el editor de la escala propia (Shift + Scales), mantén Shift: el pad 8, arriba a la derecha, se ve amarillo.",
      pads=editor(extra={8: ("yellow", "Jankó", False)}), buttons={"Scales": "yellow"}, press=["Shift"]),
    F("Shift + pad 8: the isomorphic Jankó layout on (pad 8 teal while on). The same pad again, an editor key or a stock scale turn it off.",
      "Shift + pad 8: la disposición isomórfica Jankó se enciende (el pad 8 en verde azulado mientras está encendida). El mismo pad otra vez, "
      "una tecla del editor o una escala de stock la apagan.",
      pads=editor(extra={8: ("teal", "Jankó", False)}), buttons={"Scales": "yellow"}, press=["Shift", 8]),
    F("On the note tracks the rows come in pairs: the lower one starts on the root and goes up in whole tones, the one above is a semitone "
      "lower. Every chord type has the same shape in any key; the roots in the root colour.",
      "En las pistas de notas las filas van por parejas: la de abajo empieza en la tónica y sube por tonos, la de encima es medio tono más "
      "grave. Cada tipo de acorde tiene la misma forma en cualquier tono; las tónicas en el color de la tónica.",
      pads=janko(), buttons={"Synth 1": "magenta", "Note": "amber"}, view=V(*XN)),
    F("Octave ▼ / ▲: a tap = a semitone, held about half a second = an octave (Shift + Octave still transposes the pattern). In the RCs the "
      "upper pair is the lower one an octave up; Shift + pad 24 = the earlier layout. Beta 5.56 only: one layout, the upper pair repeats.",
      "Octave ▼ / ▲: un toque = medio tono, mantenido casi medio segundo = una octava (Shift + Octave sigue transponiendo el patrón). En las RC "
      "la pareja de arriba es la de abajo una octava más aguda; Shift + pad 24 = la disposición anterior. Solo Beta 5.56: una disposición, la "
      "pareja de arriba repite.",
      pads=janko(1), buttons={"Synth 1": "magenta", "Note": "amber"}, press=["Oct ▲"], view=V(*XN)),
])

# ===== Master FX
MFXL = ("Master FX", "Master FX")
proc("hueco-master-fx", "master-fx", ["fila-inferior", "glitch-pad"], "Put an effect on a slot of Master FX", "Poner un efecto en un hueco de Master FX",
     vlabel=MFXL, frames=[
    F("Master FX (Mixer, then Mixer again). Hold an effect on top (pad 5, the Phaser): it sounds while held, and K1-K4 are its knobs: speed, "
      "depth, feedback, mix.",
      "Master FX (Mixer y otra vez Mixer). Mantén un efecto de arriba (pad 5, el Phaser): suena mientras lo mantienes, y K1-K4 son sus knobs: "
      "velocidad, profundidad, realimentación, mezcla.",
      pads=mfx({5: ("magenta", "Phaser", False)}), buttons={"Mixer": "white"}, press=[5],
      knobs={1: V("Speed", "Velocidad"), 2: V("Depth", "Profund."), 3: V("Feedback", "Realim."), 4: V("Mix", "Mezcla")}),
    F("Still holding it, touch a slot of the bottom row (pad 27): the slot stores the effect with a copy of its four knobs. Pad 7 (the sample) "
      "and pad 31 (the mechanical gesture) are assigned the same way.",
      "Sin soltarlo, toca un hueco de la fila de abajo (pad 27): el hueco guarda el efecto con una copia de sus cuatro knobs. El pad 7 (el "
      "sample) y el 31 (el gesto mecánico) se asignan igual.",
      pads=mfx({5: ("magenta", "Phaser", False), 27: ("magenta", "Phaser", False)}), buttons={"Mixer": "white"}, press=[5, 27],
      knobs={1: V("Speed", "Velocidad"), 2: V("Depth", "Profund."), 3: V("Feedback", "Realim."), 4: V("Mix", "Mezcla")}),
    F("Touch the slot: the effect sounds with its copy while you hold it. The FX sequencer triggers these slots; since RC2 they are saved with "
      "the project.",
      "Toca el hueco: el efecto suena con su copia mientras lo mantienes. El secuenciador de efectos dispara estos huecos; desde RC2 se "
      "guardan con el proyecto.",
      pads=mfx({27: ("magenta", "Phaser", False)}), buttons={"Mixer": "white"}, press=[27]),
    F("Shift + the slot = latched; touch it again to release it. Pad 8 (white while something is latched) releases everything.",
      "Shift + el hueco = fijado; tócalo otra vez para soltarlo. El pad 8 (blanco mientras hay algo fijado) lo suelta todo.",
      pads=mfx({27: ("magenta", "Phaser", False), 8: ("white", V("Off", "Apagar"), False)}), buttons={"Mixer": "white"}, press=["Shift", 27]),
])

SP_S, SP_E = ("orange", "", False), ("pine", "", False)          # the song pointer's start and end
proc("song-pointer", "master-fx", ["song-pointer"], "Repeat steps live with the song pointer", "Repetir pasos en directo con el song pointer",
     vlabel=MFXL, frames=[
    F("Master FX while the patterns play: pads 9-24 = steps 1-16, the song pointer; the step playing is white.",
      "Master FX mientras suenan los patrones: los pads 9-24 = los pasos 1-16, el song pointer; el paso que suena, en blanco.",
      pads=mfx(head=12), buttons={"Play": "green"}),
    F("Hold one step (pad 14, step 6): retrigger: that step plays at the next step and repeats while you hold it.",
      "Mantén un paso (pad 14, el paso 6): retrigger: ese paso suena en el paso siguiente y se repite mientras lo mantienes.",
      pads=mfx(head=14), buttons={"Play": "green"}, press=[14]),
    F("Hold two steps (pads 11 and 16, steps 3 and 8): the patterns loop between them while you hold them.",
      "Mantén dos pasos (pads 11 y 16, los pasos 3 y 8): los patrones hacen bucle entre ellos mientras los mantienes.",
      pads=mfx({11: SP_S, 16: SP_E}, head=13), buttons={"Play": "green"}, press=[11, 16]),
    F("Let go: the patterns go on as before. Pad 8 releases everything latched (effects, song pointer, sample).",
      "Suelta: los patrones siguen como antes. El pad 8 suelta todo lo fijado (efectos, song pointer, sample).",
      pads=mfx(head=17), buttons={"Play": "green"}),
])

proc("modo-frase", "master-fx", ["song-pointer"], "Loop a phrase with phrase mode", "Repetir una frase con el modo frase", vlabel=MFXL, frames=[
    F("Master FX while it plays: Shift + a step (pad 11, step 3) = phrase mode: that step is the start and step 16 the end; pad 9 lights white.",
      "Master FX mientras suena: Shift + un paso (pad 11, el paso 3) = modo frase: ese paso es el inicio y el 16 el fin; el pad 9 se ve blanco.",
      pads=mfx({11: SP_S, 24: SP_E, 9: ("white", "", False)}, head=15), buttons={"Play": "green"}, press=["Shift", 11]),
    F("In phrase mode a touch = the end (pad 18, step 10): the patterns loop steps 3-10. A touch does not retrigger.",
      "En el modo frase un toque = el fin (pad 18, el paso 10): los patrones hacen bucle en los pasos 3-10. Un toque no hace retrigger.",
      pads=mfx({11: SP_S, 18: SP_E, 9: ("white", "", False)}, head=13), buttons={"Play": "green"}, press=[18]),
    F("Shift + another step = a new start (pad 13, step 5); an end before it goes back to 16.",
      "Shift + otro paso = un inicio nuevo (pad 13, el paso 5); un fin anterior a él vuelve al 16.",
      pads=mfx({13: SP_S, 18: SP_E, 9: ("white", "", False)}, head=16), buttons={"Play": "green"}, press=["Shift", 13]),
    F("Shift + the start, or pad 9 (white), leaves phrase mode: the patterns play whole again.",
      "Shift + el inicio, o el pad 9 (blanco), sale del modo frase: los patrones vuelven a sonar enteros.",
      pads=mfx(head=20), buttons={"Play": "green"}, press=[9]),
])

# ===== Patterns and Mixer
T8 = ["Synth 1", "Synth 2", "MIDI 1", "MIDI 2", "Drum 1", "Drum 2", "Drum 3", "Drum 4"]
def pats(extra=None):
    """the Patterns view: a column per track, a row per pattern (patterns 1-2 of every track and pattern 3 of Synth 1 with notes)"""
    p = {}
    for c, t in enumerate(T8):
        for r in (0, 1): p[8 * r + c + 1] = (TC[t], "", True)
    p[17] = ("magenta", "", True)
    p.update(extra or {})
    return p
PTV = ("Patterns", "Patterns")
BP = {"Patterns": "white"}
proc("cadenas", "patterns", ["cadenas"], "Chain patterns: A A A B A A A C", "Encadenar patrones: A A A B A A A C", since="RC2", vlabel=PTV, frames=[
    F("The Patterns view: a column per track, a row per pattern. Hold Shift: the Octave that does something lights yellow.",
      "La vista Patterns: una columna por pista, una fila por patrón. Mantén Shift: el Octave que hace algo se ve amarillo.",
      pads=pats(), buttons=dict(BP, **{"Oct ▲": "yellow"}), press=["Shift"]),
    F("Shift + Octave ▲: the whole project's chain mode on (Octave ▲ green).",
      "Shift + Octave ▲: el modo cadena de todo el proyecto, activado (Octave ▲ verde).",
      pads=pats(), buttons=dict(BP, **{"Oct ▲": "green"}), press=["Shift", "Oct ▲"]),
    F("Touch a pattern of Synth 1 (pattern 1): it is A (yellow), played once; the knob LEDs count the repeats.",
      "Toca un patrón de Synth 1 (el patrón 1): es A (amarillo), una vez; los LEDs de los knobs cuentan las repeticiones.",
      pads=pats({1: ("yellow", "A", False)}), buttons=dict(BP, **{"Oct ▲": "green"}), press=[1], kcol={1: "white"}),
    F("A again = one more repeat (up to 8): twice more = 3 times.",
      "A otra vez = una repetición más (hasta 8): dos veces más = 3 veces.",
      pads=pats({1: ("yellow", "A", False)}), buttons=dict(BP, **{"Oct ▲": "green"}), press=[1], kcol={1: "white", 2: "white", 3: "white"}),
    F("Another pattern of the same track (pattern 2) = B (green) …",
      "Otro patrón de la misma pista (el patrón 2) = B (verde) …",
      pads=pats({1: ("yellow", "A", False), 9: ("green", "B", False)}), buttons=dict(BP, **{"Oct ▲": "green"}), press=[9],
      kcol={1: "white", 2: "white", 3: "white"}),
    F("… and the next one (pattern 3) = C (red): the track plays A A A B A A A C. B and C play once and the track goes back to A.",
      "… y el siguiente (el patrón 3) = C (rojo): la pista toca A A A B A A A C. B y C suenan una vez y la pista vuelve a A.",
      pads=pats({1: ("yellow", "A", False), 9: ("green", "B", False), 17: ("red", "C", False)}), buttons=dict(BP, **{"Oct ▲": "green"}), press=[17],
      kcol={1: "white", 2: "white", 3: "white"}),
    F("Shift + Octave ▼ turns the mode off: the rules stay saved but are not applied. In the mode, Clear + pattern removes its rule; each scene "
      "remembers the mode.",
      "Shift + Octave ▼ desactiva el modo: las reglas quedan guardadas pero no se aplican. En el modo, Clear + patrón quita su regla; cada "
      "escena recuerda el modo.",
      pads=pats({1: ("white", "A", True)}), buttons=dict(BP, **{"Oct ▼": "yellow"}), press=["Shift", "Oct ▼"]),
])

def mixer(extra=None, muted=()):
    """the Mixer: row 1 the tracks (lit = sounding, dim = muted), rows 3-4 the scenes (scene 1 the current one)"""
    p = {i + 1: (TC[t], "", (i + 1) in muted) for i, t in enumerate(T8)}
    p.update(fill(range(17, 21), "white"))
    p[17] = ("white", V("Scene 1", "Escena 1"), False)
    p.update(extra or {})
    return p
MXV = ("Mixer", "Mixer")
REP = {9 + i: ("yellow", "", False) for i in range(8)}
proc("repeticiones-escena", "mixer", ["cadenas"], "Repeat a scene", "Repetir una escena", since="RC2", vlabel=MXV, frames=[
    F("The Mixer: row 1 = the tracks, rows 3-4 = the scenes (scene 1 playing). Hold Shift: pads 9-16 = the repeats of the current scene: the row "
      "yellow, the chosen number green (1).",
      "El Mixer: fila 1 = las pistas, filas 3-4 = las escenas (suena la escena 1). Mantén Shift: los pads 9-16 = las repeticiones de la escena "
      "actual: la fila en amarillo, el número elegido en verde (1).",
      pads=mixer(merge(REP, {9: ("green", "1", False)})), buttons={"Mixer": "white", "Play": "green"}, press=["Shift"]),
    F("Shift + pad 11 = 3 repeats (green).",
      "Shift + pad 11 = 3 repeticiones (verde).",
      pads=mixer(merge(REP, {11: ("green", "3", False)})), buttons={"Mixer": "white", "Play": "green"}, press=["Shift", 11]),
    F("While it plays, with Shift, the repeat now playing is white (pad 9 = the first time; here the second, pad 10). Since RC4.",
      "Mientras suena, con Shift, la repetición que suena se ve blanca (pad 9 = la primera vez; aquí la segunda, el pad 10). Desde RC4.",
      pads=mixer(merge(REP, {10: ("white", "", False), 11: ("green", "3", False)})), buttons={"Mixer": "white", "Play": "green"}, press=["Shift"]),
    F("On the last one the green pad blinks white / green; then the next scene comes. A scene ends when its longest chain ends; saving it again "
      "does not change its repeats.",
      "En la última, el pad verde parpadea blanco / verde; después llega la escena siguiente. Una escena termina cuando termina su cadena más "
      "larga; guardarla otra vez no cambia sus repeticiones.",
      pads=mixer(merge(REP, {11: ("white|green", "3", False)})), buttons={"Mixer": "white", "Play": "green"}, press=["Shift"]),
])

proc("mute-compas", "mixer", ["mixer-cue"], "Mute a track on the next bar", "Silenciar una pista en el compás siguiente", since="RC2", vlabel=MXV, frames=[
    F("The Mixer while it plays: row 1 = the eight tracks, lit = sounding.",
      "El Mixer mientras suena: la fila 1 = las ocho pistas, encendidas = suenan.",
      pads=mixer(), buttons={"Mixer": "white", "Play": "green"}),
    F("Shift + pad 6 (Drum 2): it will be muted when the next bar starts; the pad blinks while it waits (again = cancel).",
      "Shift + pad 6 (Drum 2): se silenciará al empezar el compás siguiente; el pad parpadea mientras espera (otra vez = cancelar).",
      pads=mixer(), buttons={"Mixer": "white", "Play": "green"}, press=["Shift", 6], blink=[6]),
    F("On the next bar it is muted (dim). Shift + pad 6 again brings it back on the following bar; with the transport stopped it happens at once.",
      "En el compás siguiente queda silenciada (tenue). Shift + pad 6 otra vez la devuelve en el compás siguiente; con el transporte parado, "
      "al momento.",
      pads=mixer(muted=(6,)), buttons={"Mixer": "white", "Play": "green"}),
])

PANK = {i + 1: t for i, t in enumerate(T8)}
proc("modo-cue", "mixer", ["mixer-cue"], "Prepare tracks in the cue", "Preparar pistas en el cue", since="RC2", vlabel=MXV, frames=[
    F("The Mixer, Octave ▼: the pan page (each knob is a track's pan).",
      "El Mixer, Octave ▼: la página de panorama (cada knob, el panorama de una pista).",
      pads=mixer(), buttons={"Mixer": "white", "Oct ▼": "white"}, press=["Oct ▼"], knobs=PANK),
    F("Shift + a knob to the right: the cue mode on (Octave ▼ pink). The left output carries the mix in mono, the right one only the cued tracks.",
      "Shift + un knob a la derecha: el modo cue, encendido (Octave ▼ rosa). La salida izquierda lleva la mezcla en mono y la derecha solo las "
      "pistas en cue.",
      pads=mixer(), buttons={"Mixer": "white", "Oct ▼": "pink"}, press=["Shift"], turn={1: 1}, knobs=PANK),
    F("Now each pan knob is its track's send to the cue (right output), from the centre to the right: pink, brighter with more send. Clear + "
      "knob = no cue.",
      "Ahora cada knob de panorama es el envío de su pista al cue (salida derecha), del centro a la derecha: rosa, más brillante cuanto más "
      "envío. Clear + knob = sin cue.",
      pads=mixer(), buttons={"Mixer": "white", "Oct ▼": "pink"}, turn={5: 1}, knobs=PANK,
      kcol=merge({k: ("pink", True) for k in range(1, 9)}, {5: "pink"})),
    F("Since RC4 the metronome's click and the previews (a patch chosen, Shift + a drum sample) are heard in the cue only. Shift + a knob to the "
      "left: the mode off (Octave ▼ white), the pans come back. Stored in the unit.",
      "Desde RC4 el clic del metrónomo y las escuchas previas (un patch elegido, Shift + un sample de drum) suenan solo en el cue. Shift + un "
      "knob a la izquierda: el modo, apagado (Octave ▼ blanco); vuelven los paneos. Se guarda en el aparato.",
      pads=mixer(), buttons={"Mixer": "white", "Oct ▼": "white"}, press=["Shift"], turn={1: -1}, knobs=PANK),
])

# ===== Drums
DK = {1: V("Pitch", "Pitch"), 2: "Ring", 3: "Decay", 4: V("Env → F", "Env → F"), 5: V("Filter", "Filtro"), 6: "Reso", 7: "LFO", 8: "Dist"}
DV = ("Drum 1", "Drum 1")
proc("pareja-estereo", "drum-pista", ["pareja-estereo"], "Make a stereo drum pair", "Hacer una pareja estéreo de drums", since="RC4", vlabel=DV, frames=[
    F("Drum 1's view. Hold Drum 1 …",
      "La vista de Drum 1. Mantén Drum 1 …",
      buttons={"Drum 1": "orange"}, press=["Drum 1"], knobs=DK),
    F("… and press Drum 2: a stereo pair. Drum 1 plays on the left and Drum 2 on the right with the pack's next sample; Drum 2's button pulses in "
      "Drum 1's colour.",
      "… y pulsa Drum 2: una pareja estéreo. Drum 1 suena a la izquierda y Drum 2 a la derecha con el sample siguiente del pack; el botón de "
      "Drum 2 late en el color de Drum 1.",
      buttons={"Drum 1": "orange", "Drum 2": "orange"}, press=["Drum 1", "Drum 2"], pulse=["Drum 2"], knobs=DK),
    F("Everything of Drum 1 drives both: its knobs (with Shift too), pattern, level, sends and side-chain. Drum 2's pattern does not play; its "
      "pads and MIDI notes play it alone, on the right.",
      "Todo lo de Drum 1 vale para los dos: sus knobs (también con Shift), su patrón, su nivel, sus envíos y su sidechain. El patrón de Drum 2 "
      "no suena; sus pads y sus notas MIDI lo tocan solo, a la derecha.",
      buttons={"Drum 1": "orange", "Drum 2": "orange"}, pulse=["Drum 2"], knobs=DK),
    F("In Drum 2's view its knobs are deviations from Drum 1, in Drum 1's colour (brighter = more): K1 detune, K2 the stereo width (white), "
      "K3 decay … Clear + knob = no deviation.",
      "En la vista de Drum 2 sus knobs son desviaciones sobre Drum 1, en el color de Drum 1 (más brillo = más): K1 desafinación, K2 la "
      "apertura estéreo (blanco), K3 decay … Clear + knob = sin desviación.",
      buttons={"Drum 1": "orange", "Drum 2": "orange"}, pulse=["Drum 2"], press=["Drum 2"], view=V("Drum 2"),
      knobs={1: V("Detune", "Desafin."), 2: V("Width", "Apertura"), 3: "Decay", 4: V("Env → F", "Env → F"), 5: V("Filter", "Filtro"), 6: "Reso", 7: "LFO"},
      kcol=merge({k: ("orange", True) for k in range(1, 8)}, {2: "white"})),
    F("The same gesture (hold Drum 1, press Drum 2) undoes the pair and Drum 2's own values come back. Drum 3 + Drum 4 the same. Saved with the "
      "project.",
      "El mismo gesto (mantén Drum 1, pulsa Drum 2) deshace la pareja y vuelven los valores propios de Drum 2. Drum 3 + Drum 4, igual. Se "
      "guarda con el proyecto.",
      buttons={"Drum 1": "orange"}, press=["Drum 1", "Drum 2"], knobs=DK),
])

# ===== Pattern Settings
def ps(extra=None):
    """Pattern Settings: pads 1-16 the steps (the first and the last marked), 17-24 the sync rate (1/16 chosen), 25 mode 2, 26 Nudge,
    27 / 28 the orders, 29-32 the direction (forward chosen)"""
    p = fill(range(1, 17), "sky")
    p[1], p[16] = ("grey", "", False), ("yellow", "", False)
    p.update(fill(range(17, 25), "amber"))
    p[21] = ("amber", "1/16", False)
    p.update({25: ("peach", V("Mode 2", "Modo 2"), False), 26: ("blue", "Nudge", False), 27: ("pink", "Fractal", True), 28: ("pink", V("Decon.", "Decons."), True),
              29: ("pink", V("Fwd", "Adel."), False), 30: ("pink", V("Back", "Atrás"), True), 31: ("pink", "Ping\npong", True), 32: ("pink", V("Rnd", "Azar"), True)})
    p.update(extra or {})
    return p
PSV = ("Pattern Settings", "Pattern Settings")
BPS = {"Synth 1": "magenta", "Pattern Settings": "magenta"}
proc("arpegiador", "pattern-settings", ["arpegiador"], "Switch the arpeggiator on", "Encender el arpegiador", since="RC2", vlabel=PSV, frames=[
    F("Synth 1, Pattern Settings: first / last step (pads 1-16), sync rate (17-24) and direction (29-32) as always; pads 25-28 are new.",
      "Synth 1, Pattern Settings: primer / último paso (pads 1-16), sync rate (17-24) y dirección (29-32) como siempre; los pads 25-28 son nuevos.",
      pads=ps(), buttons=BPS, press=["Pattern Settings"]),
    F("Shift + pad 25: the arpeggiator of the pattern that plays, on. With Shift the arpeggiator's pads keep their colours and the chosen "
      "options show green.",
      "Shift + pad 25: el arpegiador del patrón que suena, encendido. Con Shift los pads del arpegiador conservan sus colores y lo elegido se "
      "ve en verde.",
      pads=ps({25: ("green", "Arp", False)}), buttons=BPS, press=["Shift", 25]),
    F("Shift + pads 27-32 = the arpeggio's order, apart from the pattern's direction: fractal, deconstructed, up, down, ping-pong, random "
      "(here up, pad 29).",
      "Shift + pads 27-32 = el orden del arpegio, aparte de la dirección del patrón: fractal, deconstruido, arriba, abajo, ping-pong, aleatorio "
      "(aquí arriba, el pad 29).",
      pads=ps({25: ("green", "Arp", False), 29: ("green", V("Up", "Arriba"), False)}), buttons=BPS, press=["Shift", 29]),
    F("Shift + pads 17-24 = its resolution, slower to the left: 1/4, 1/4T, 1/8, 1/8T, 1/16, 1/16T, 1/32, 1/32T (here 1/8); the same pad again = "
      "the track's sync rate.",
      "Shift + pads 17-24 = su resolución, más lenta a la izquierda: 1/4, 1/4T, 1/8, 1/8T, 1/16, 1/16T, 1/32, 1/32T (aquí 1/8); el mismo pad "
      "otra vez = el sync rate de la pista.",
      pads=ps({25: ("green", "Arp", False), 29: ("green", V("Up", "Arriba"), False), 19: ("green", "1/8", False)}), buttons=BPS, press=["Shift", 19]),
    F("Without Shift, pad 25 shows green while it is on. Two or more notes starting on a step now play one at a time, and two keys or more held "
      "are arpeggiated; with Record the chord is recorded. Saved per track and pattern.",
      "Sin Shift, el pad 25 se ve verde mientras está encendido. Dos o más notas que empiezan en un paso suenan ahora de una en una, y dos "
      "teclas o más mantenidas se arpegian; con Record se graba el acorde. Se guarda por pista y patrón.",
      pads=ps({25: ("green", V("Mode 2", "Modo 2"), False)}), buttons=BPS),
])

def mods(o=1, w=5, g=9, r=13):
    p = {}
    for base, col, ch in ((1, "sand", o), (5, "sky", w), (9, "amber", g), (13, "pink", r)):
        for k in range(base, base + 4): p[k] = (col, "", k != ch)
    return p
proc("modificadores-arpegio", "pattern-settings", ["arpegiador"], "Shape the arpeggio with its modifiers", "Dar forma al arpegio con sus modificadores",
     since="RC4", vlabel=PSV, frames=[
    F("With the pattern's arpeggiator on (pad 25 green), hold Shift in Pattern Settings: pads 1-16 = four groups of modifiers, the chosen option "
      "bright: octaves (sand), when the octave moves (sky blue), groove (amber), reset (pink).",
      "Con el arpegiador del patrón encendido (pad 25 verde), mantén Shift en Pattern Settings: los pads 1-16 = cuatro grupos de modificadores, "
      "la opción elegida brillante: octavas (arena), cuándo cambia la octava (azul cielo), groove (ámbar), reinicio (rosa).",
      pads=ps(merge(mods(), {25: ("green", "Arp", False)})), buttons=BPS, press=["Shift"]),
    F("Shift + pad 2 = one octave more (pads 1-4: no spread, +1 octave, +1 up and 1 down, +2 up and 1 down).",
      "Shift + pad 2 = una octava más (pads 1-4: sin ampliar, +1 octava, +1 arriba y 1 abajo, +2 arriba y 1 abajo).",
      pads=ps(merge(mods(2), {25: ("green", "Arp", False)})), buttons=BPS, press=["Shift", 2]),
    F("Shift + pad 7 = the octave moves every 3 notes (pads 5-8: after each pass, every note, every 3 notes, every 4 notes).",
      "Shift + pad 7 = la octava cambia cada 3 notas (pads 5-8: al terminar cada vuelta, en cada nota, cada 3 notas, cada 4 notas).",
      pads=ps(merge(mods(2, 7), {25: ("green", "Arp", False)})), buttons=BPS, press=["Shift", 7]),
    F("Shift + pad 11 = swing, 2:1 (pads 9-12: none, note / dotted note, swing, every note twice).",
      "Shift + pad 11 = swing, 2:1 (pads 9-12: ninguno, nota / nota con puntillo, swing, cada nota dos veces).",
      pads=ps(merge(mods(2, 7, 11), {25: ("green", "Arp", False)})), buttons=BPS, press=["Shift", 11]),
    F("Shift + pad 14 = after a whole pass, 1 note more and back to the start (pads 13-16: no reset, 1, 3, 5). They apply to a step's "
      "arpeggio, held notes and the external keyboard; saved per track and pattern.",
      "Shift + pad 14 = tras una vuelta entera, 1 nota más y vuelta al principio (pads 13-16: sin reinicio, 1, 3, 5). Valen para el arpegio de "
      "un paso, las notas mantenidas y el teclado externo; se guardan por pista y patrón.",
      pads=ps(merge(mods(2, 7, 11, 14), {25: ("green", "Arp", False)})), buttons=BPS, press=["Shift", 14]),
])

def nud(order):
    p = ps()
    for k in range(9, 17): p.pop(k, None)
    for i, ch in enumerate(order): p[i + 1] = ("sky", ch, i not in (0, 7))
    p[1] = ("grey", order[0], False)
    p[8] = ("yellow", order[7], False)
    return p
proc("nudge", "pattern-settings", ["nudge-ordenes"], "Nudge the steps of a pattern", "Mover los pasos de un patrón (Nudge)", since="RC4.05",
     vlabel=PSV, frames=[
    F("Pattern Settings: the selected range runs from the first to the last step (here steps 1 to 8; the letters stand for what each step holds).",
      "Pattern Settings: el tramo elegido va del primer al último paso (aquí los pasos 1 a 8; las letras son lo que lleva cada paso).",
      pads=nud("ABCDEFGH"), buttons=BPS, press=["Pattern Settings"]),
    F("Tap pad 26 (Nudge, blue): the content of the range moves one step back; what leaves at the start comes in at the end. The first and "
      "last steps do not move.",
      "Toca el pad 26 (Nudge, azul): el contenido del tramo va un paso atrás; lo que sale por el principio entra por el final. El primer y el "
      "último paso no se mueven.",
      pads=nud("BCDEFGHA"), buttons=BPS, press=[26]),
    F("Shift + pad 26: one step forward. Whole steps move, with their automation; on the drums too, with their own values. The view shows it at "
      "once.",
      "Shift + pad 26: un paso adelante. Se mueven los pasos enteros, con su automatización; en los drums también, con sus valores propios. La "
      "vista lo enseña al momento.",
      pads=nud("ABCDEFGH"), buttons=BPS, press=["Shift", 26]),
])

# ===== the step-drummer and the sample picker
SD_DEST = [(V("Pitch", "Tono"), "green"), ("OSC 2", "teal"), ("WAVE", "yellow"), ("FM", "magenta"), ("MIX", "sky"), ("Env F", "amber"),
           ("SHAPE", "orange"), ("Decay", "purple")]
def sd(dest=17, notes=(1, 5, 9, 13), toggle=False, extra=None):
    p = {}
    for n in range(1, 17): p[n] = ("sky" if (n - 1) // 2 % 2 == 0 else "orange", "", n not in notes)
    for i, (lab, col) in enumerate(SD_DEST): p[17 + i] = (col, lab, 17 + i != dest)
    p[27] = ENGINE["osc"]
    p[30] = ("purple", "Step\ndrum", False)
    p[32] = ("green", "Pitch\nvel", not toggle)
    p.update(extra or {})
    return p
SDV = ("Step-drummer", "Step-drummer")
BSD = {"MIDI 1": "blue", "Preset": "blue", "Oct ▲": "purple", "Oct ▼": ("purple", True), "1-16 / 17-32": ("purple", True)}
PAIRS = {k: f"{2 * k - 1}-{2 * k}" for k in range(1, 9)}
proc("step-drummer", "step-drummer", ["step-drummer"], "Sequence a destination with the step-drummer", "Secuenciar un destino con el step-drummer",
     vlabel=SDV, frames=[
    F("MIDI 1, Preset, with the engine on: pad 30 opens the step-drummer (Synth 1 / 2: the source view, pad 30). Pads 1-16 = the steps of the "
      "half shown, in pairs; bright = has a note.",
      "MIDI 1, Preset, con el motor encendido: el pad 30 abre el step-drummer (Synth 1 / 2: la vista de la fuente, pad 30). Los pads 1-16 = los "
      "pasos de la mitad que se ve, por pares; brillante = con nota.",
      pads=sd(), buttons=BSD, press=[30], knobs=PAIRS, kcol=merge({k: ("green", True) for k in range(1, 9)}, {1: "white"})),
    F("Shift + a step = set or clear its note (pad 7); a touch = listen to it.",
      "Shift + un paso = poner o quitar su nota (pad 7); un toque = escucharlo.",
      pads=sd(notes=(1, 5, 7, 9, 13)), buttons=BSD, press=["Shift", 7], knobs=PAIRS,
      kcol=merge({k: ("green", True) for k in range(1, 9)}, {2: "white"})),
    F("Pads 17-24 = the destination of the pitch row: pitch, OSC 2, WAVE, FM, MIX, env → filter, SHAPE, decay (here WAVE, yellow).",
      "Pads 17-24 = el destino de la fila de pitch: tono, OSC 2, WAVE, FM, MIX, env → filtro, SHAPE, decay (aquí WAVE, amarillo).",
      pads=sd(19, (1, 5, 7, 9, 13)), buttons=BSD, press=[19], knobs=PAIRS,
      kcol=merge({k: ("yellow", True) for k in range(1, 9)}, {3: "white"})),
    F("K1-K8 = the 8 step pairs: each moves the destination on its two steps up or down from the centre (no change); since RC2 the LED is "
      "dim there and brighter further out. The pair playing is white.",
      "K1-K8 = los 8 pares de pasos: cada uno mueve el destino en sus dos pasos, arriba o abajo desde el centro (sin cambio); desde RC2 el LED "
      "se ve tenue ahí y más brillante cuanto más lejos. El par que suena, en blanco.",
      pads=sd(19, (1, 5, 7, 9, 13)), buttons=BSD, turn={4: 1}, knobs=PAIRS,
      kcol=merge({k: ("yellow", True) for k in range(1, 9)}, {4: "yellow", 5: "white"})),
    F("Octave ▲ / ▼ = the pitch / velocity page (since RC2 the velocity page can have a destination of its own); 1-16 / 17-32 = the other "
      "half. Pad 32 = the pitch-vel toggle (since RC2; bright green): the pitch page also moves the notes by degrees of the scale.",
      "Octave ▲ / ▼ = la página pitch / velocity (desde RC2 la de velocity puede tener su propio destino); 1-16 / 17-32 = la otra mitad. El "
      "pad 32 = el toggle pitch-vel (desde RC2; verde brillante): la página pitch también mueve las notas por grados de la escala.",
      pads=sd(19, (1, 5, 7, 9, 13), True), buttons=BSD, press=[32], knobs=PAIRS,
      kcol=merge({k: ("yellow", True) for k in range(1, 9)}, {4: "yellow", 6: "white"})),
    F("With Record, touching a step records it on the step that plays. On MIDI 1 / 2, Shift + pad 30 turns the step-drummer off (pad 30 dim).",
      "Con Record, tocar un paso lo graba en el paso que suena. En MIDI 1 / 2, Shift + pad 30 desactiva el step-drummer (pad 30 tenue).",
      pads=mpre(extra=merge(slots(), {30: ("purple", "Step\ndrum", True)})), buttons=BM, press=["Shift", 30], view=V(*MPV)),
])

def picker(sample=17, notes=(1, 5, 9, 13), extra=None):
    p = {n: ("teal", "", n not in notes) for n in range(1, 17)}
    p.update(fill(range(17, 33), "white"))
    p[sample] = ("teal", "", False)
    p.update(extra or {})
    return p
PKR = ("Sample picker", "Selector de samples")
BPK = {"MIDI 1": "blue", "Note": "amber", "Oct ▼": "white", "1-16 / 17-32": ("white", True)}
proc("sample-flip", "midi-muestra", ["modo-muestra"], "Pick samples and flip them by step", "Elegir samples y cambiarlos por paso (sample flip)",
     since="RC2", vlabel=PKR, frames=[
    F("MIDI 1 with the engine on sample (pad 27 teal): press Note twice: the sample picker. Pads 17-32 = 16 of the pack's samples (the track's, "
      "teal); Octave ▼ / ▲ = the 4 pages, 64 samples.",
      "MIDI 1 con el motor en muestra (pad 27 verde azulado): pulsa Note dos veces: el selector de samples. Pads 17-32 = 16 samples del pack (el "
      "de la pista, verde azulado); Octave ▼ / ▲ = las 4 páginas, 64 samples.",
      pads=picker(), buttons=BPK, press=["Note"]),
    F("Touch a sample = the track's sample, and it sounds (since RC4, Shift + sample = pick it silently).",
      "Tocar un sample = el sample de la pista, y suena (desde RC4, Shift + sample = elegirlo sin que suene).",
      pads=picker(22), buttons=BPK, press=[22]),
    F("Pads 1-16 = the steps: teal = a note, dim teal = nothing. Hold a step (pad 5) and touch a sample (pad 26): that step's sample flip; "
      "meanwhile the step shows green and its sample yellow.",
      "Pads 1-16 = los pasos: verde azulado = con nota, verde azulado tenue = nada. Mantén un paso (pad 5) y toca un sample (pad 26): el sample "
      "flip de ese paso; mientras, el paso se ve verde y su sample amarillo.",
      pads=picker(22, extra={5: ("green", "", False), 26: ("yellow", "", False)}), buttons=BPK, press=[5, 26]),
    F("Let go: the step shows peach = a note with a flip (since RC2.04 you can also hold a sample and touch steps). Since RC4 a flip on a step "
      "without a note adds the last note played there.",
      "Suelta: el paso se ve melocotón = nota con flip (desde RC2.04 también puedes mantener un sample y tocar pasos). Desde RC4 un flip en un "
      "paso sin nota añade ahí la última nota tocada.",
      pads=picker(22, extra={5: ("peach", "", False)}), buttons=BPK),
    F("Clear + a step removes its flip. With Record + Play, touching a sample records a note on the step that plays, with its flip.",
      "Clear + paso quita su flip. Con Record + Play, tocar un sample graba una nota en el paso que suena, con su flip.",
      pads=picker(22), buttons=dict(BPK, Clear="white"), press=["Clear", 5]),
])

# ===== the engine row, automation, the matrix
ROW = {17: ("white", V("Off", "Apagado"), True), 18: ("amber", V("Line", "Línea"), True), 19: ("green", "Osc", True), 20: ("orange", "VA-drum", True),
       21: ("magenta", "Gran.", True), 22: ("teal", V("Sample", "Muestra"), True), 23: ("blue", V("FX seq", "Sec. FX"), True), 24: ("purple", "FM", True)}
def row(cur):
    p = dict(ROW)
    c = p[cur]
    p[cur] = (c[0], c[1], False)
    return p
proc("fila-motores", "midi-preset", ["motor-midi", "fm4"], "Choose an engine on the engine row", "Elegir un motor en la fila de motores", since="RC4",
     vlabel=MPV, frames=[
    F("MIDI 1's Preset view: a tap on pad 27 (the engine) opens the engine row, each in its colour, the current one bright: off, line input, "
      "oscillator, VA-drum, granular, sample, FX sequencer and, on pad 24, FM.",
      "La vista Preset de MIDI 1: un toque al pad 27 (el motor) abre la fila de motores, cada uno en su color, el actual brillante: apagado, "
      "entrada de línea, oscilador, VA-drum, granular, muestra, secuenciador de efectos y, en el pad 24, FM.",
      pads=mpre(extra=row(19)), buttons=BM, press=[27]),
    F("Tap one to choose it (pad 20, the VA-drum, orange): the row stays open and pad 27 takes its colour.",
      "Toca uno para elegirlo (pad 20, el VA-drum, naranja): la fila sigue abierta y el pad 27 toma su color.",
      pads=mpre(engine="vadrum", extra=row(20)), buttons=BM, press=[20]),
    F("Pad 24 = the FM (violet): a 4-operator FM engine, with its knob page on pad 7.",
      "El pad 24 = el FM (violeta): un motor FM de 4 operadores, con su página de knobs en el pad 7.",
      pads=mpre(engine="fm", extra=merge(row(24), {7: ("purple", "FM", True)})), buttons=BM, press=[24]),
    F("Pad 27 again closes the row and the patch list comes back (while the row is open, pads 9-24 load nothing). Shift + pad 27 still steps to "
      "the next engine. Beta 5.56 only: another row, and the FX sequencer on pad 31.",
      "El pad 27 otra vez cierra la fila y vuelve la lista de patches (con la fila abierta, los pads 9-24 no cargan nada). Shift + pad 27 sigue "
      "pasando al motor siguiente. Solo Beta 5.56: otra fila, y el secuenciador de efectos en el pad 31.",
      pads=mpre(engine="fm", extra=merge(slots(), {7: ("purple", "FM", True)})), buttons=BM, press=[27]),
])

VELV = ("Velocity", "Velocity")
proc("soltar-automatizacion", "synth-nota", ["automatizacion"], "Make a step let go of the automation", "Hacer que un paso suelte la automatización",
     since="RC4", vlabel=VELV, frames=[
    F("Synth 1 (or Synth 2, MIDI 1 / 2), the Velocity view. Hold Shift: the step pads light yellow, the marked ones red.",
      "Synth 1 (o Synth 2, MIDI 1 / 2), la vista Velocity. Mantén Shift: los pads de paso se ven amarillos y los marcados en rojo.",
      pads=fill(range(1, 17), "yellow", False), buttons={"Synth 1": "magenta", "Velocity": "magenta"}, press=["Shift"]),
    F("Shift + a step (pad 9): marked, red: no lane plays on that step, and what the automation had moved goes back to the project's values "
      "(since RC4.01). A knob turned by hand afterwards stays where you left it.",
      "Shift + un paso (pad 9): marcado, en rojo: en ese paso no suena ningún carril, y lo que la automatización había movido vuelve a los "
      "valores del proyecto (desde RC4.01). Un knob girado a mano después se queda donde lo dejes.",
      pads=merge(fill(range(1, 17), "yellow", False), {9: ("red", "", False)}), buttons={"Synth 1": "magenta", "Velocity": "magenta"},
      press=["Shift", 9]),
    F("Shift + the same step again = unmarked. Saved with the pattern; on the 17-32 page, steps 17-32. Beta 5.56 only: with Shift only the steps "
      "with automation are yellow, and Shift + a yellow step previews its values.",
      "Shift + el mismo paso otra vez = desmarcado. Se guarda con el patrón; en la página 17-32, los pasos 17-32. Solo Beta 5.56: con Shift solo "
      "se ven amarillos los pasos con automatización, y Shift + un paso amarillo escucha sus valores.",
      pads=fill(range(1, 17), "yellow", False), buttons={"Synth 1": "magenta", "Velocity": "magenta"}, press=["Shift", 9]),
])

EK = {1: V("Attack", "Ataque"), 2: "Release", 3: V("Env → A", "Env → A"), 4: V("Env → F", "Env → F"), 5: V("Filter", "Filtro"), 6: "Reso",
      7: "LFO", 8: "FX"}
MNOTE = merge(keys((3, 4), "blue"), {1: ("blue", "", True), 5: ("blue", "", True), 9: ("blue", "", True), 13: ("blue", "", True)})
proc("foto-paso", "midi-knobs", ["automatizacion"], "Snapshot the sound into a step", "Hacer una foto del sonido en un paso", since="RC4", vlabel=NV,
     frames=[
    F("MIDI 1 with its own engine on, the Note view: shape the sound with the knobs; some parameters are now away from their initial value.",
      "MIDI 1 con su motor encendido, la vista Note: ajusta el sonido con los knobs; algunos parámetros ya no están en su valor inicial.",
      pads=MNOTE, buttons={"MIDI 1": "blue", "Note": "blue"}, turn={5: 1}, knobs=EK,
      kcol={1: ("blue", True), 2: ("blue", True), 3: "blue", 4: "blue", 5: "blue", 6: ("blue", True), 7: ("blue", True), 8: ("blue", True)}),
    F("Hold Record and touch a step pad (pad 5): the parameters that are not at their initial value (the one of Clear + knob to the right) are "
      "written into that step's lanes, and only those. Record stays as it was.",
      "Mantén Record y toca un pad de paso (pad 5): los parámetros que no están en su valor inicial (el de Clear + knob a la derecha) se "
      "escriben en los carriles de ese paso, y solo esos. Record queda como estaba.",
      pads=MNOTE, buttons={"MIDI 1": "blue", "Note": "blue"}, press=["Record", 5], knobs=EK,
      kcol={1: ("blue", True), 2: ("blue", True), 3: "blue", 4: "blue", 5: "blue", 6: ("blue", True), 7: ("blue", True), 8: ("blue", True)}),
    F("A parameter with no lane takes one whose parameter is at its initial value (that lane is cleared first); the step keeps its notes. Beta "
      "5.56 only: also on Synth 1 / 2 and the drums, and the step lights yellow while held.",
      "Un parámetro sin carril toma uno cuyo parámetro está en su valor inicial (antes se borra ese carril); el paso conserva sus notas. Solo "
      "Beta 5.56: también en Synth 1 / 2 y los drums, y el paso se ve amarillo mientras lo mantienes.",
      pads=MNOTE, buttons={"MIDI 1": "blue", "Note": "blue"}, knobs=EK,
      kcol={1: ("blue", True), 2: ("blue", True), 3: "blue", 4: "blue", 5: "blue", 6: ("blue", True), 7: ("blue", True), 8: ("blue", True)}),
])

MXK = {1: "Velocity", 2: V("Note", "Nota"), 3: V("Random", "Azar"), 4: "LFO 2", 5: "Env 2", 6: "Drum", 7: V("Position", "Posición"), 8: V("Steps", "Pasos")}
PG1 = merge(fill(range(9, 17), "amber"), fill([17, 18, 19, 20, 21, 22, 24], "amber"))      # page 1's knobs: K1-K8, Shift + K1-K8 (Shift + K7 has none)
def mx(dest=None, page_pad=True):
    p = mpre(page=6)
    if dest:
        p.update(PG1)
        p[dest] = ("amber", "", False)
        if page_pad: p[1] = ("amber", "VCA\nVCF", False)
    return p
proc("matriz", "midi-matriz", ["matriz-mod"], "Send a mod matrix source to a destination", "Llevar una fuente de la matriz a un destino", since="RC2.02",
     vlabel=MPV, frames=[
    F("MIDI 1, Preset, with the engine on: pad 6 (light blue) = the mod matrix: the 8 knobs are 8 sources: velocity, note, random, LFO 2, "
      "envelope 2, a drum hit, the pattern position and stepped random.",
      "MIDI 1, Preset, con el motor encendido: el pad 6 (azul claro) = la matriz de modulación: los 8 knobs son 8 fuentes: velocity, nota, "
      "azar, LFO 2, envolvente 2, golpe de un drum, posición en el patrón y azar por pasos.",
      pads=mx(), buttons=BM, press=[6], knobs=MXK),
    F("Turn a source to the right (K4, LFO 2): its position is the destination and the amount. While it turns, the pads show where the "
      "destination lives: its page (pad 1, VCA-VCF) and its knob on pads 9-16 (bright: K5, the filter).",
      "Gira una fuente a la derecha (K4, LFO 2): su posición es el destino y la cantidad. Mientras giras, los pads enseñan dónde vive el destino: "
      "su página (pad 1, VCA-VCF) y su knob en los pads 9-16 (brillante: K5, el filtro).",
      pads=mx(13), buttons=BM, turn={4: 1}, knobs=MXK, kcol={4: ("amber", True)}),
    F("Further right the amount grows: the LED brighter, in the colour of the destination's page (amber = page 1).",
      "Más a la derecha crece la cantidad: el LED más brillante, en el color de la página del destino (ámbar = página 1).",
      pads=mx(13), buttons=BM, turn={4: 1}, knobs=MXK, kcol={4: "amber"}),
    F("Then comes the next destination (pad 14, the resonance) and the amount starts again: two clicks a step, 16 steps a destination, 33 "
      "destinations.",
      "Luego llega el destino siguiente (pad 14, la resonancia) y la cantidad vuelve a empezar: dos clics por paso, 16 pasos por destino, "
      "33 destinos.",
      pads=mx(14), buttons=BM, turn={4: 1}, knobs=MXK, kcol={4: ("amber", True)}),
    F("Clear + knob = that source off; Clear + pad 6 = all off; Shift + K4 = LFO 2's shape and rate. Saved with the own-synth patches and, "
      "since RC4, with the project.",
      "Clear + knob = esa fuente apagada; Clear + pad 6 = todas apagadas; Shift + K4 = forma y velocidad del LFO 2. Se guarda con los patches "
      "del sinte propio y, desde RC4, con el proyecto.",
      pads=mx(), buttons=dict(BM, Clear="white"), press=["Clear"], turn={4: 1}, knobs=MXK),
])

# ===== Sidechain
def sc(src=5, target=26, extra=None):
    p = merge(fill(range(17, 25), "magenta"), fill(range(25, 33), "pine"))
    p[19] = ("magenta", "", False)
    p[target] = ("pine", "", False)
    for i, t in enumerate(T8):
        p[i + 1] = ("white", t, True)
    if src <= 4: p[src] = ("pine", T8[src - 1], False)
    else: p[src] = (TC[T8[src - 1]], T8[src - 1], False)
    p.update(extra or {})
    return p
SCV = ("Sidechain", "Sidechain")
SCK = {1: V("Attack", "Ataque"), 2: "Hold", 3: "Decay", 4: V("Depth", "Profund.")}
proc("sidechain-patron", "sidechain", ["sidechain-comp", "drums-dsp"], "Duck a track with another track's pattern",
     "Sidechain de una pista con el patrón de otra", since="RC2", vlabel=SCV, frames=[
    F("Shift + FX: the Sidechain view. Rows 3 / 4 = the presets of this page's two tracks (Synth 1, Synth 2); row 1 pads 5-8 = the drum that "
      "triggers the chosen track.",
      "Shift + FX: la vista Sidechain. Filas 3 / 4 = los presets de las dos pistas de esta página (Synth 1, Synth 2); los pads 5-8 de la fila 1 = "
      "el drum que dispara la pista elegida.",
      pads=sc(), buttons={"FX": "white"}, press=["Shift", "FX"]),
    F("Touch a preset of Synth 2 (row 4): Synth 2 is the chosen track; K1-K4 = its attack, hold, decay and depth, in its colour.",
      "Toca un preset de Synth 2 (fila 4): Synth 2 es la pista elegida; K1-K4 = su ataque, hold, decay y profundidad, en su color.",
      pads=sc(target=27), buttons={"FX": "white"}, press=[27], knobs=SCK, kcol={1: "pine", 2: ("pine", True), 3: "pine", 4: "pine"}),
    F("Row 1 pads 1-4 = Synth 1, Synth 2, MIDI 1, MIDI 2 as the source: touch pad 3 (MIDI 1): every note of MIDI 1's pattern now ducks Synth 2, "
      "as a drum hit does (notes played live do not).",
      "Pads 1-4 de la fila 1 = Synth 1, Synth 2, MIDI 1, MIDI 2 como fuente: toca el pad 3 (MIDI 1): cada nota del patrón de MIDI 1 hace ahora "
      "sidechain a Synth 2, como un golpe de drum (las notas tocadas en directo no).",
      pads=merge(sc(target=27), {3: ("pine", "MIDI 1", False), 5: ("white", "Drum 1", True)}), buttons={"FX": "white"}, press=[3], knobs=SCK,
      kcol={1: "pine", 2: ("pine", True), 3: "pine", 4: "pine"}),
    F("A pad 5-8 gives it back to a drum. Saved with the project. On the drum pages (Octave ▼) the same pads trigger a drum's envelope.",
      "Un pad 5-8 lo devuelve a un drum. Se guarda con el proyecto. En las páginas de drums (Octave ▼) los mismos pads disparan la envolvente "
      "de un drum.",
      pads=sc(target=27), buttons={"FX": "white"}, press=[5], knobs=SCK, kcol={1: "pine", 2: ("pine", True), 3: "pine", 4: "pine"}),
])

# ===== Setup and Advanced Setup
SETP = {16: ("white", "Ch 16", True), 22: ("cream", "Rev\n→ 3", True), 23: ("peach", "Dly\n→ 4", True)}
GMK = {4: "GM", 5: "Drum 1", 6: "Drum 2", 7: "Drum 3", 8: "Drum 4"}
DRK = {5: ("orange", True), 6: ("yellow", True), 7: ("purple", True), 8: ("teal", True)}
STV = ("Setup", "Setup")
proc("gm-drums", "setup", ["setup"], "Send the drums as General MIDI notes", "Mandar los drums como notas General MIDI", since="RC4", vlabel=STV, frames=[
    F("The Setup view: turn K4 to the right: the drums' General MIDI mode on (K4 green). Off by default.",
      "La vista Setup: gira K4 a la derecha: el modo General MIDI de los drums, encendido (K4 verde). Apagado de fábrica.",
      pads=SETP, turn={4: 1}, knobs=GMK, kcol=merge({4: "green"}, DRK)),
    F("K5 = Drum 1's GM note, 35-81, two clicks a note (36, the kick, by default): each new note sounds once and its number shows on the pads, "
      "in the drum's colour.",
      "K5 = la nota GM de Drum 1, 35-81, dos clics por nota (36, el bombo, de fábrica): cada nota nueva suena una vez y su número se ve en los "
      "pads, en el color del drum.",
      pads=digits(36, "orange"), turn={5: 1}, knobs=GMK, kcol=merge({4: "green"}, DRK)),
    F("K6-K8 = Drum 2-4 (38 snare, 42 closed hat, 46 open hat by default), each in its colour; a higher note, a brighter knob. While a number "
      "shows, the Setup pads do nothing.",
      "K6-K8 = Drum 2-4 (38 caja, 42 charles cerrado, 46 charles abierto de fábrica), cada uno en su color; nota más alta, knob más brillante. "
      "Mientras se ve un número, los pads de Setup no hacen nada.",
      pads=digits(38, "yellow"), turn={6: 1}, knobs=GMK, kcol=merge({4: "green"}, DRK)),
    F("Shift (or leaving Setup) confirms it, saved in the settings, and the Setup pads come back. Each hit of Drum 1-4 now goes out over MIDI "
      "with its GM note on the drums' channel; inside it sounds the same.",
      "Shift (o salir de Setup) lo confirma, guardado en los ajustes, y vuelven los pads de Setup. Cada golpe de Drum 1-4 sale ahora por MIDI "
      "con su nota GM por el canal de drums; dentro suena igual.",
      pads=SETP, press=["Shift"], knobs=GMK, kcol=merge({4: "green"}, DRK)),
    F("K4 to the left: off (dim), and the drums go out as on stock again.",
      "K4 a la izquierda: apagado (tenue), y los drums vuelven a salir como en stock.",
      pads=SETP, turn={4: -1}, knobs=GMK, kcol={4: ("green", True)}),
])

CH = fill(range(1, 17), "white")
proc("canales-pgm", "setup", ["setup"], "Choose the Program Change channels", "Elegir los canales de Program Change", since="RC2", vlabel=STV, frames=[
    F("The Setup view (not Advanced Setup): touch pad 29 (PGM Rx): pads 1-16 show the listen channel of the project's Program Changes: white = "
      "the chosen one (16 by default), dim white = the rest. This first touch does not change PGM Rx.",
      "La vista Setup (no Advanced Setup): toca el pad 29 (PGM Rx): los pads 1-16 enseñan el canal de escucha de los Program Change del proyecto: "
      "blanco = el elegido (el 16 de fábrica), blanco tenue = el resto. Ese primer toque no cambia PGM Rx.",
      pads=merge(CH, {16: ("white", "16", False), 29: ("", "PGM\nRx"), 30: ("", "PGM\nTx")}), press=[29]),
    F("Touch a channel pad to pick it (pad 10 = channel 10).",
      "Toca un pad de canal para elegirlo (pad 10 = canal 10).",
      pads=merge(CH, {10: ("white", "10", False), 29: ("", "PGM\nRx"), 30: ("", "PGM\nTx")}), press=[10]),
    F("Pad 29 again = PGM Rx on / off, as always.",
      "El pad 29 otra vez = PGM Rx encendido / apagado, como siempre.",
      pads=merge(CH, {10: ("white", "10", False), 29: ("", "PGM\nRx"), 30: ("", "PGM\nTx")}), press=[29]),
    F("Pad 30 (PGM Tx): the same with the output channel. What arrives on the listen channel is sent again on the output one.",
      "El pad 30 (PGM Tx): lo mismo con el canal de salida. Lo que llega por el canal de escucha sale otra vez por el de salida.",
      pads=merge(CH, {16: ("white", "16", False), 29: ("", "PGM\nRx"), 30: ("", "PGM\nTx")}), press=[30]),
    F("A track button or another pad: pads 1-16 show the tracks' channels again. Saved in the settings.",
      "Un botón de pista u otro pad: los pads 1-16 vuelven a los canales de las pistas. Se guarda en los ajustes.",
      pads=merge(SETP, {29: ("", "PGM\nRx"), 30: ("", "PGM\nTx")}), buttons={"Synth 1": "magenta"}, press=["Synth 1"]),
])

ADV = ("Advanced Setup", "Advanced Setup")
proc("midi-thru", "advanced-setup", ["setup"], "Choose the MIDI Thru jack's mode", "Elegir el modo del jack MIDI Thru", since="RC2", vlabel=ADV, frames=[
    F("Advanced Setup (open it as on the original): Duplicate = the mode of the MIDI Thru jack. Thru (Duplicate dim red): the DIN In, by hardware.",
      "Advanced Setup (ábrela como en el original): Duplicate = el modo del jack MIDI Thru. Thru (Duplicate rojo tenue): el DIN In, por hardware.",
      buttons={"Duplicate": ("red", True)}),
    F("Duplicate: Out 2 (green): the device's own MIDI.",
      "Duplicate: Out 2 (verde): el MIDI del propio aparato.",
      buttons={"Duplicate": "green"}, press=["Duplicate"]),
    F("Duplicate: Merge (yellow): the DIN In and the device's MIDI together.",
      "Duplicate: Merge (amarillo): el DIN In y el MIDI del aparato juntos.",
      buttons={"Duplicate": "yellow"}, press=["Duplicate"]),
    F("Duplicate: Filter (blue): the DIN In without the channels the device listens to. Once more = Thru. No SysEx in Merge / Filter; saved in "
      "the settings.",
      "Duplicate: Filter (azul): el DIN In sin los canales en los que escucha el aparato. Otra vez = Thru. Sin SysEx en Merge / Filter; se "
      "guarda en los ajustes.",
      buttons={"Duplicate": "blue"}, press=["Duplicate"]),
])

# ===== Beta 5.56 only
MK = {1: V("Position", "Posición"), 2: V("Square", "Cuadrado"), 3: V("LFO rate", "Vel. LFO"), 4: V("Random", "Azar"), 5: V("Slow →", "Lento →"),
      6: V("Length", "Duración"), 7: "Env", 8: V("Time", "Tiempo")}
MV = {1: ("magenta", "Env", True), 8: ("magenta", "Env", True), 32: ("red", V("Out", "Salir"), False)}
proc("morph", "synth-preset", ["morph"], "Morph between patches", "Hacer morph entre patches", beta=True, vlabel=SPV, frames=[
    F("Synth 1's Preset view: hold two to four patches (here pads 2, 5 and 11) for 0.4 s …",
      "La vista Preset de Synth 1: mantén de dos a cuatro patches (aquí los pads 2, 5 y 11) 0,4 s …",
      pads=patches("Synth 1", 1, {2: ("white", "1", False), 5: ("white", "2", False), 11: ("white", "3", False)}), buttons=B1, press=[2, 5, 11]),
    F("… the morph view opens: K1 = the position along the chain, coloured by patch (1 red, 2 yellow, 3 green, 4 blue); K2 square LFO, K3 the "
      "LFOs' rate, K4 random-step LFO.",
      "… se abre la vista del morph: K1 = la posición en la cadena, en el color del patch (1 rojo, 2 amarillo, 3 verde, 4 azul); K2 LFO "
      "cuadrado, K3 velocidad de los LFO, K4 LFO de pasos al azar.",
      pads=MV, buttons={"Synth 1": "magenta"}, turn={1: 1}, knobs=MK, kcol={1: "yellow"}, view=V("Morph")),
    F("K5 = the slow morph's destination, K6 its length (at once … 32 bars): turn K5 and leave it for half a second: the sound moves from K1 "
      "to K5, and once there K1 takes K5's value.",
      "K5 = el destino del morph lento, K6 su duración (al momento … 32 compases): gira K5 y déjalo quieto medio segundo: el sonido va de K1 a "
      "K5, y al llegar K1 toma el valor de K5.",
      pads=MV, buttons={"Synth 1": "magenta"}, turn={5: 1}, knobs=MK, kcol={1: "yellow", 5: "green"}, view=V("Morph")),
    F("K7 / K8 = the envelope (depth / time); pads 1 / 8 fire it, held while you hold them (bright while it runs). Clear + knob = 0; Clear + "
      "the track button = every knob to 0.",
      "K7 / K8 = la envolvente (cantidad / tiempo); los pads 1 / 8 la disparan, sostenida mientras los mantienes (brillantes mientras corre). "
      "Clear + knob = 0; Clear + el botón de la pista = todos a 0.",
      pads=merge(MV, {1: ("magenta", "Env", False)}), buttons={"Synth 1": "magenta"}, press=[1], knobs=MK, kcol={1: "green", 5: "green"},
      view=V("Morph")),
    F("Pad 32 (red) = out. The morph goes on in the other views; the track button brings its view back. One morph at a time; nothing is saved.",
      "Pad 32 (rojo) = salir. El morph sigue en las otras vistas; el botón de la pista vuelve a su vista. Un morph a la vez; no se guarda nada.",
      pads=MV, buttons={"Synth 1": "magenta"}, press=[32], knobs=MK, kcol={1: "green", 5: "green"}, view=V("Morph")),
    F("Preset = the patches, those of the chain in white: a tap loads that patch and leaves; holding patches 0.4 s = a new chain.",
      "Preset = los patches, los de la cadena en blanco: un toque carga ese patch y sale; mantener patches 0,4 s = una cadena nueva.",
      pads=patches("Synth 1", 1, {2: ("white", "1", False), 5: ("white", "2", False), 11: ("white", "3", False)}), buttons=B1, press=["Preset"],
      view=V(*SPV)),
])


# ===== more processes of the guide (probability view, voice mode, FM lists, drum arpeggio, gate, delayed save)
PRV = ("Probability", "Probabilidad")
BPR = {"Synth 1": "magenta", "Pattern Settings": "magenta"}
def bar(level, colour, row=4, rest="white"):
    """a bar on a row: pads up to the level (0-7) bright in the colour, the rest dim"""
    base = 8 * (row - 1)
    p = {}
    for k in range(8): p[base + k + 1] = (colour, "", False) if k <= level else (rest, "", True)
    return p
proc("random-mutate", "probabilidad", ["random-mutate", "frecuencia-dinamicas"], "Let a step's notes mutate", "Hacer que las notas de un paso muten",
     since="RC2", vlabel=PRV, frames=[
    F("Synth 1, Pattern Settings: pad 25 (peach) opens the probability view in mode 2: row 3 = dynamics, row 4 = random-mutate.",
      "Synth 1, Pattern Settings: el pad 25 (melocotón) abre la vista de probabilidad en modo 2: fila 3 = dinámicas, fila 4 = random-mutate.",
      pads=ps(), buttons=BPS, press=[25], view=V(*PSV)),
    F("Hold a step with notes (pad 3) and touch a pad of row 4 (pad 28): the step's random-mutate level, a peach bar. Pad 28 = 6 % octave and "
      "6 % scale.",
      "Mantén un paso con notas (pad 3) y toca un pad de la fila 4 (pad 28): el nivel de random-mutate del paso, una barra melocotón. Pad 28 = "
      "6 % octava y 6 % escala.",
      pads=merge({3: ("white", "", False)}, bar(3, "peach", rest="peach")), buttons=BPR, press=[3, 28]),
    F("Row 4: off, octave 6 %, scale 6 %, both 6 %, scale 12 %, octave 12 %, scale 25 %, octave 25 % + scale 50 %. Octave = one up or down; "
      "scale = another note of the scale in its octave. Each note of a chord is drawn apart.",
      "Fila 4: nada, octava 6 %, escala 6 %, las dos 6 %, escala 12 %, octava 12 %, escala 25 %, octava 25 % + escala 50 %. Octava = una arriba "
      "o abajo; escala = otra nota de la escala en su octava. Cada nota de un acorde se sortea aparte.",
      pads=merge({3: ("white", "", False)}, bar(7, "peach", rest="peach")), buttons=BPR, press=[3, 32]),
    F("Row 3 = the step's dynamics (the chosen one green): pad 17 none … pad 24 accents (velocity −32 to +64); some also move the micro steps.",
      "Fila 3 = las dinámicas del paso (la elegida en verde): pad 17 nada … pad 24 acentos (velocity −32 a +64); algunas mueven también los "
      "micropasos.",
      pads=merge({3: ("white", "", False)}, bar(7, "peach", rest="peach"), fill(range(17, 25), "white"), {20: ("green", "", False)}), buttons=BPR, press=[3, 20]),
    F("Without Record the change sounds that time only; with Record and this view on screen it is written (the sequence drifts). Clear + pad 25 "
      "in Pattern Settings clears the pattern's. Beta 5.56 only: rows 3-4 are one set of pads, with a factor on Octave.",
      "Sin Record el cambio suena solo esa vez; con Record y esta vista en pantalla se escribe (la secuencia va derivando). Clear + pad 25 en "
      "Pattern Settings borra los del patrón. Solo Beta 5.56: las filas 3-4 son un solo juego de pads, con un factor en Octave.",
      pads=merge(bar(7, "peach", rest="peach"), fill(range(17, 25), "white"), {20: ("green", "", False)}), buttons=BPR),
])

proc("frecuencia", "probabilidad", ["frecuencia-dinamicas"], "Play a step every n passes", "Hacer que un paso suene cada n vueltas", since="RC2",
     vlabel=PRV, frames=[
    F("Synth 1: Pattern Settings twice (or Shift + Pattern Settings): the probability view, mode 1. Row 3 is the stock step probability.",
      "Synth 1: Pattern Settings dos veces (o Shift + Pattern Settings): la vista de probabilidad, modo 1. La fila 3 es la probabilidad de stock.",
      buttons=BPR, press=["Pattern Settings"]),
    F("Hold a step with notes (pad 3) and touch row 4 (pad 28 = 4): a yellow bar: the step plays on the last of every 4 passes of the pattern.",
      "Mantén un paso con notas (pad 3) y toca la fila 4 (pad 28 = 4): una barra amarilla: el paso suena en la última de cada 4 vueltas del patrón.",
      pads=merge({3: ("white", "", False)}, bar(3, "yellow")), buttons=BPR, press=[3, 28]),
    F("1-8 passes (pad 25 = every pass). Each pattern counts its passes from Play: variations that come back every 2, 4 or 8. Also on the drums.",
      "De 1 a 8 vueltas (pad 25 = todas). Cada patrón cuenta sus vueltas desde Play: variaciones que vuelven cada 2, 4 u 8. También en los drums.",
      pads=merge({3: ("white", "", False)}, bar(7, "yellow")), buttons=BPR, press=[3, 32]),
])

VM_ROW = {17: ("green", "Retrig", True), 18: ("yellow", "Legato", True), 19: ("teal", "Glide", True), 20: ("green", "Uni\nretrig", True),
          21: ("yellow", "Uni\nlegato", True), 22: ("teal", "Uni\nglide", True), 23: ("purple", V("Uni\nalways", "Uni\nalways"), True),
          24: ("magenta", "Poly", True)}
def vrow(cur):
    p = dict(VM_ROW)
    c = p[cur]
    p[cur] = (c[0], c[1], False)
    return p
VMV = V("Voice mode", "Modo de voz")
proc("modo-voz", "midi-preset", ["motor-midi"], "Choose the own synth's voice mode", "Elegir el modo de voz del sinte propio", since="RC4", vlabel=MPV,
     frames=[
    F("MIDI 1, Preset, with the engine on: a tap on pad 32 opens the voice modes on pads 17-24, the current one bright (poly, the factory mode); "
      "modes with the same name share a colour.",
      "MIDI 1, Preset, con el motor encendido: un toque al pad 32 abre los modos de voz en los pads 17-24, el actual brillante (poly, el de "
      "fábrica); los que se llaman igual, del mismo color.",
      pads=mpre(extra=merge(vrow(24), {32: ("magenta", V("Voice", "Voz"), False)})), buttons=BM, press=[32], view=VMV),
    F("Touch one to pick it (pad 19, glide, teal): the pitch slides from a held note to the new one. Pad 32 always shows the mode's colour.",
      "Toca uno para elegirlo (pad 19, glide, verde azulado): la altura se desliza de la nota mantenida a la nueva. El pad 32 se ve siempre en el "
      "color del modo.",
      pads=mpre(extra=merge(vrow(19), {32: ("teal", V("Voice", "Voz"), False)})), buttons=BM, press=[19], view=VMV),
    F("With the row open, K1 = the glide's amount (teal: its time, up to about 2 s; fully left, no glide) and K2 = the unison's detune (blue).",
      "Con la fila abierta, K1 = la cantidad del glide (verde azulado: su tiempo, hasta unos 2 s; a la izquierda del todo, sin glide) y K2 = la "
      "desafinación del unísono (azul).",
      pads=mpre(extra=merge(vrow(19), {32: ("teal", V("Voice", "Voz"), False)})), buttons=BM, turn={1: 1}, view=VMV,
      knobs={1: "Glide", 2: V("Detune", "Desafin.")}, kcol={1: "teal", 2: ("blue", True)}),
    F("Pad 32 again (or leaving the view) closes it and the patches come back. Shift + pad 29 also steps through the modes. Saved with the "
      "own-synth patch and the project.",
      "El pad 32 otra vez (o salir de la vista) lo cierra y vuelven los patches. Shift + pad 29 también pasa por los modos. Se guarda con el "
      "patch del sinte propio y con el proyecto.",
      pads=mpre(extra=merge(slots(), {32: ("teal", V("Voice", "Voz"), False)})), buttons=BM, press=[32]),
])

FMK = {1: "Ratio 1", 2: "Ratio 2", 3: "Ratio 3", 4: "Ratio 4", 5: V("Level 1", "Nivel 1"), 6: V("Level 2", "Nivel 2"), 7: V("Level 3", "Nivel 3"),
       8: V("Level 4", "Nivel 4")}
FMV = V("FM", "FM")
def algos(cur=1):
    p = {}
    for i in range(16):
        col = "white" if i < 8 else "red" if i < 12 else "teal" if i < 14 else "green"
        p[9 + i] = (col, str(i + 1), i + 1 != cur)
    return p
FMPAGE = {7: ("purple", "FM", False), 8: ("white", "", True)}
proc("fm-algoritmos", "midi-fm", ["fm4"], "Pick an FM algorithm from the pads", "Elegir un algoritmo FM con los pads", since="RC4", vlabel=MPV, frames=[
    F("MIDI 1 with the FM engine (pad 27 violet): pad 7 opens its knob page (bright violet): K1-K4 the operators' ratios, K5-K8 their levels.",
      "MIDI 1 con el motor FM (pad 27 violeta): el pad 7 abre su página de knobs (violeta brillante): K1-K4 la ratio de los operadores, K5-K8 su "
      "nivel.",
      pads=mpre(engine="fm", page=0, extra=merge(slots(), FMPAGE)), buttons=BM, press=[7], knobs=FMK, view=FMV),
    F("Hold pad 7: pads 9-24 show the 16 algorithms in their family's colour (classic white, percussive red, bells teal, strings green), the "
      "current one bright.",
      "Mantén el pad 7: los pads 9-24 enseñan los 16 algoritmos en el color de su familia (clásicos blanco, percusivos rojo, campanas verde "
      "azulado, cuerdas verde), el actual brillante.",
      pads=mpre(engine="fm", page=0, extra=merge(algos(1), FMPAGE)), buttons=BM, press=[7], knobs=FMK, view=FMV),
    F("Still holding it, press one (pad 21 = algorithm 13, a bell): it is chosen and the tonic sounds while you hold it (Shift + pad: no sound).",
      "Sin soltarlo, pulsa uno (pad 21 = algoritmo 13, una campana): queda elegido y suena la tónica mientras lo mantienes (Shift + pad: sin "
      "sonido).",
      pads=mpre(engine="fm", page=0, extra=merge(algos(13), FMPAGE)), buttons=BM, press=[7, 21], knobs=FMK, view=FMV),
    F("Let go of pad 7: the patches come back. Clear + pad 7 = a playable voice of the chosen algorithm. Beta 5.56 only: the 8-operator FM, its "
      "56 algorithms on Shift + pad 7 held (Alpha 7.09: pad 8 held).",
      "Suelta el pad 7: vuelven los patches. Clear + pad 7 = una voz tocable del algoritmo elegido. Solo Beta 5.56: el FM de 8 operadores, sus "
      "56 algoritmos con Shift + pad 7 mantenido (Alpha 7.09: pad 8 mantenido).",
      pads=mpre(engine="fm", page=0, extra=merge(slots(), FMPAGE)), buttons=BM, knobs=FMK, view=FMV),
])

STARTERS = [("white", V("Piano", "Piano")), ("white", "E-piano"), ("white", V("Organ", "Órgano")), ("purple", "Pluck"), ("purple", V("Harp", "Arpa")),
            ("purple", "Marimba"), ("amber", V("Bass", "Bajo")), ("teal", V("Bell", "Campana")), ("green", V("Strings", "Cuerdas")), ("green", "Pad"),
            ("sky", V("Flute", "Flauta")), ("sky", V("Clarinet", "Clarin.")), ("sky", V("Brass", "Metales")), ("orange", V("Kick", "Bombo")),
            ("orange", V("Snare", "Caja")), ("orange", "Hi-hat")]
def starters(cur=None):
    return {9 + i: (c, lab, 9 + i != cur) for i, (c, lab) in enumerate(STARTERS)}
proc("fm-partida", "midi-fm", ["fm4"], "Load an FM starter sound", "Cargar un sonido de partida del FM", since="RC4", vlabel=MPV, frames=[
    F("MIDI 1 with the FM engine: hold pad 8 (bright while held): pads 9-24 = 16 ready-to-play instruments in their family's colour: keys white, "
      "plucked violet, bass amber, bell teal, strings and pad green, winds light blue, drums orange.",
      "MIDI 1 con el motor FM: mantén el pad 8 (brillante mientras lo mantienes): los pads 9-24 = 16 instrumentos listos para tocar en el color "
      "de su familia: teclados blanco, punteados violeta, bajo ámbar, campana verde azulado, cuerdas y pad verde, vientos azul claro, percusión "
      "naranja.",
      pads=mpre(engine="fm", page=0, extra=merge(starters(), {7: ("purple", "FM", False), 8: ("white", "", False)})), buttons=BM, press=[8],
      view=FMV),
    F("Still holding it, press one (pad 16, the bell): it loads whole (algorithm, ratios, levels, envelopes, feedback, noise, release) and the "
      "tonic sounds while you hold it; it shows bright.",
      "Sin soltarlo, pulsa uno (pad 16, la campana): se carga entero (algoritmo, ratios, niveles, envolventes, feedback, ruido, release) y suena "
      "la tónica mientras lo mantienes; se ve brillante.",
      pads=mpre(engine="fm", page=0, extra=merge(starters(16), {7: ("purple", "FM", False), 8: ("white", "", False)})), buttons=BM, press=[8, 16],
      view=FMV),
    F("They are starting points: tweak them with the knobs and save them as any own-synth patch (Clear + pad, twice). Beta 5.56 only: 24 "
      "instruments of the 8-operator FM, in two pages.",
      "Son puntos de partida: retócalos con los knobs y guárdalos como cualquier patch del sinte propio (Clear + pad, dos veces). Solo Beta 5.56: "
      "24 instrumentos del FM de 8 operadores, en dos páginas.",
      pads=mpre(engine="fm", page=0, extra=merge(slots(), FMPAGE)), buttons=BM, view=FMV),
])

BDPS = {"Drum 1": "orange", "Pattern Settings": "orange"}
proc("arpegio-drums", "drum-preset", ["arpegiador"], "Arpeggiate a drum's samples", "Arpegiar los samples de un drum", since="RC2", vlabel=PSV, frames=[
    F("Drum 1, Pattern Settings: Shift + pad 25 = the drum's arpeggiator on for the pattern it plays (Shift + pads 27-32 its order, 17-24 its "
      "resolution).",
      "Drum 1, Pattern Settings: Shift + pad 25 = el arpegiador del drum encendido para el patrón que suena (Shift + pads 27-32 su orden, 17-24 su "
      "resolución).",
      pads=ps({25: ("green", "Arp", False)}), buttons=BDPS, press=["Shift", 25]),
    F("Drum 1, Preset: hold one sample (pad 3): the drum plays it as usual …",
      "Drum 1, Preset: mantén un sample (pad 3): el drum lo toca como siempre …",
      pads=patches("Drum 1", 1, {3: ("white", "", False)}), buttons=BD, press=[3], view=V(*DPV)),
    F("… hold another one with it (pad 12): the arpeggio of the samples held: the drum jumps from sample to sample in the chosen order, with its "
      "pad's velocity (playing, on the drum's grid; stopped, at the project's tempo).",
      "… mantén otro a la vez (pad 12): el arpegio de los samples mantenidos: el drum salta de sample en sample en el orden elegido, con la "
      "velocity de su pad (en marcha, a la rejilla del drum; parado, al tempo del proyecto).",
      pads=patches("Drum 1", 1, {3: ("white", "", False), 12: ("white", "", False)}), buttons=BD, press=[3, 12], view=V(*DPV)),
    F("Let go of all: the drum goes back to its chosen sample. With Record (playing) every hit is recorded, its sample as the step's sample flip.",
      "Suéltalos todos: el drum vuelve a su sample elegido. Con Record (en marcha) se graba cada golpe, con su sample como sample flip del paso.",
      pads=patches("Drum 1", 1), buttons=BD, view=V(*DPV)),
])

MSV = ("Micro Step", "Micro Step")
BG = {"Synth 1": "magenta", "Gate": "amber"}
MS = merge(fill(range(17, 23), "yellow"), {17: ("yellow", "", False), 24: ("orange", "Tie", True), 25: ("blue", "", False)})
proc("longitud-gate", "micropasos", ["arpegiador"], "Set the gate by holding, or a fixed length", "Gate por pulsación o longitud fija", since="RC2",
     vlabel=MSV, frames=[
    F("Synth 1: Gate twice = the Micro Step view. Pad 32 = gate by holding (green): entering notes by hand, how long you hold the pad is the "
      "note's gate. Pressing it again turns it off.",
      "Synth 1: Gate dos veces = la vista Micro Step. El pad 32 = gate por pulsación (verde): al introducir notas a mano, lo que mantienes el "
      "pad es el gate de la nota. Pulsarlo otra vez lo apaga.",
      pads=merge(MS, {31: ("white", V("Fixed", "Fija"), True), 32: ("green", V("Hold", "Pulsar"), False)}), buttons=BG, press=[32]),
    F("Pad 31 = fixed length: with both off it opens the selector: pads 17-32 = 1 … 16 steps (the length in green) …",
      "El pad 31 = longitud fija: con los dos apagados abre el selector: los pads 17-32 = 1 … 16 pasos (la longitud en verde) …",
      pads=merge(bar(0, "green", 3), bar(-1, "green", 4)), buttons=BG, press=[31]),
    F("… picking a length (pad 20 = 4 steps) turns it on and closes the selector.",
      "… elegir una longitud (pad 20 = 4 pasos) la enciende y cierra el selector.",
      pads=merge(bar(3, "green", 3), bar(-1, "green", 4)), buttons=BG, press=[20]),
    F("Pad 31 blue = on: every note entered by hand gets that gate (not those recorded live). With one on, the other switches to it. The "
      "arpeggiator uses these gates too; saved with the project, per track.",
      "Pad 31 azul = encendido: cada nota introducida a mano toma ese gate (no las grabadas en directo). Con uno encendido, el otro cambia a ese. "
      "El arpegiador también usa estos gates; se guarda con el proyecto, por pista.",
      pads=merge(MS, {31: ("blue", V("Fixed", "Fija"), False), 32: ("white", V("Hold", "Pulsar"), True)}), buttons=BG),
])

proc("guardado-diferido", "advanced-setup", ["setup"], "Save while playing without a stumble", "Guardar mientras suena sin tropiezos", since="RC4.05",
     vlabel=ADV, frames=[
    F("Advanced Setup: pad 22 = delayed save on (green; off by default, dim: Save saves at once, as the original).",
      "Advanced Setup: el pad 22 = guardado diferido encendido (verde; apagado de fábrica, tenue: Save guarda al momento, como el original).",
      pads={22: ("green", V("Delay", "Diferido"), False)}, press=[22]),
    F("With the sequencer running, Save twice: the save waits, and Save blinks yellow.",
      "Con el secuenciador en marcha, Save dos veces: el guardado espera, y Save parpadea en amarillo.",
      buttons={"Save": "yellow", "Play": "green"}, press=["Save"], blink=["Save"]),
    F("Stop: the project is written then, so the clock does not stumble. Loading another project or saving into another slot first saves it at "
      "once; changing pack before stopping drops that save.",
      "Para: el proyecto se escribe entonces, sin descompasar el reloj. Cargar otro proyecto o guardar en otro hueco antes lo guarda al momento; "
      "cambiar de pack antes de parar descarta ese guardado.",
      press=["Play"]),
])


# ---------------------------------------------------------------------------------------------------- writing and checking
def file_name(pid, lang): return f"anim-{pid}-{lang}.svg"


def write_all(img_dir=IMG_DIR):
    """every process in both languages -> img_dir/anim-<id>-<lang>.svg; returns [(id, file_en, file_es)]"""
    img_dir = Path(img_dir)
    img_dir.mkdir(parents=True, exist_ok=True)
    out = []
    for p in PROCESSES:
        files = []
        for lang in ("en", "es"):
            f = file_name(p["id"], lang)
            (img_dir / f).write_text(render(p, lang), encoding="utf-8", newline="\n")
            files.append(f)
        out.append((p["id"], files[0], files[1]))
    return out


def check(path):
    """an SVG of this module: XML, no script or external reference, each frame's caption visible in its own slot of the loop, in turn;
    -> a list of problems"""
    import xml.etree.ElementTree as ET
    text = Path(path).read_text(encoding="utf-8")
    bad = []
    try: root = ET.fromstring(text)
    except ET.ParseError as ex: return [f"not XML: {ex}"]
    ns = "{http://www.w3.org/2000/svg}"
    if any(True for _ in root.iter(ns + "script")): bad.append("script")
    if re.search(r"<script|href=|@import|url\(|javascript:", text, re.I): bad.append("an external reference or script")
    css = "".join(st.text or "" for st in root.iter(ns + "style"))
    anim = {m.group(1): int(m.group(2)) for m in re.finditer(r"\.(g\d+)\{animation:k\1 (\d+)ms step-end infinite", css)}
    keys = {m.group(1): [(float(a), float(b)) for a, b in re.findall(r"([\d.]+)%\{opacity:([01])\}", m.group(2))]
            for m in re.finditer(r"@keyframes k(g\d+)\{((?:[\d.]+%\{opacity:[01]\})+)\}", css)}
    if set(anim) != set(keys): bad.append("a group without its keyframes")
    if len(set(anim.values())) > 1: bad.append("groups with different loop lengths")
    def shown(name, pct):                 # the step-end value at pct
        v = None
        for p, o in keys[name]:
            if p <= pct: v = o
        return v == 1
    caps = []                             # (group, "i/n") of the captions
    for g in root.iter(ns + "g"):
        for t in g.iter(ns + "text"):
            if t.get("class") == "sn": caps.append((g.get("class"), t.text))
    if not caps: return bad + ["no captions"]
    n = int(caps[0][1].split("/")[1])
    if sorted(int(c.split("/")[0]) for _, c in caps) != list(range(1, n + 1)): bad.append("captions missing or repeated")
    starts = {}
    for name, step in caps:                # the slot of every frame: where its caption is visible
        i = int(step.split("/")[0]) - 1
        on = [p for p in [x / 10 for x in range(1000)] if shown(name, p)]
        if not on: bad.append(f"frame {i + 1} never shows"); continue
        starts[i] = (min(on), max(on))
    order = [starts[i] for i in sorted(starts)]
    for (a0, a1), (b0, b1) in zip(order, order[1:]):
        if not b0 > a1: bad.append("frames out of order or overlapping")
    if order and order[0][0] != 0: bad.append("the loop does not start with frame 1")
    for i in range(len(order)):          # exactly one caption at every moment of the loop
        mid = (order[i][0] + order[i][1]) / 2
        if sum(shown(nm, mid) for nm, _ in caps) != 1: bad.append(f"frame {i + 1}: not exactly one caption")
    return bad


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import make_wiki as MW
    done = write_all(IMG_DIR)
    problems, total = 0, 0
    for p in PROCESSES:
        for lang in ("en", "es"):
            f = IMG_DIR / file_name(p["id"], lang)
            size = f.stat().st_size
            total += size
            bad = check(f)
            words = " ".join([p["title"][lang]] + [fr["caption"][lang] for fr in p["frames"]])
            bad += [f"inner-works word: {m.group(0)}" for m in MW.BANNED.finditer(words)]
            if size > 40_000: bad.append(f"{size} bytes")
            for b in bad: print(f"{f.name}: {b}")
            problems += len(bad)
    print(f"{len(done)} processes, {2 * len(done)} SVG files, {total // 1024} KB, {problems} problems")
    return problems


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
