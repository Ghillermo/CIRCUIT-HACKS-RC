"""The wiki's view maps (the user, 2026-11-14: «Add pictures to the wiki … Explain each feature, not just name it»): a drawing of the panel for every
view of the guide's chapters 1-10 (the ids are the guide's anchors), each pad, knob and button that does something labelled with a few words and
lit in the colour the guide gives, drawn with the feature list's figure code (make_manual.fig / svg) so they look like the feature list's figures.
A view whose knobs have two layers gets a second map for the Shift layer; what is «Beta 5.56 only» is captioned so.

    python tools/wiki_views.py           (writes docs/wiki/img/view-<id>[-n]-<lang>.svg and checks them)

write_all(img_dir) -> {view id: [(file_en, file_es, caption_en, caption_es)]}, for make_wiki to put under each view.  The colours are the names of
make_manual.C (the LED table) plus sand and steel blue (the same table's codes, as the SD app shows them): the guide's colour words first; where the
guide gives none, the device's own (docs/voces_panels.json, the voices document's panels); grey = lit as on the original, in the original's colours.
"""
from __future__ import annotations
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_manual as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
IMG_DIR = ROOT / "docs/wiki/img"
COL = dict(M.C, violet=M.C["purple"], sand="#ffd966", steel="#5e84cc", none="#3a3d42")
BG = "#17181b"                                  # the panel behind a dim pad (svg's background)
TRACK = {"Synth 1": "magenta", "Synth 2": "pine", "MIDI 1": "blue", "MIDI 2": "pink", "Drum 1": "orange", "Drum 2": "yellow", "Drum 3": "violet",
         "Drum 4": "teal"}
TRACKS = list(TRACK)
BUTTONS = set(M.THIN) | set(M.TRACKS) | {b.replace("\n", " ") for b in M.LEFT} | set(M.RIGHT)


# ---------------------------------------------------------------------------------------------------- the data's helpers
def P(col, en="", es=None, dim=False):
    """a pad: its colour (a COL name), the label in English / Spanish (es = en when the same), dim = lit low"""
    return (col, en, en if es is None else es, dim)


def D(col, en="", es=None):
    return P(col, en, es, True)


def K(en, es=None):
    return (en, en if es is None else es)


def MAP(en, es, title, pads=None, knobs=None, buttons=None, kcol=None):
    """one map: the caption and the view's name (top right) in both languages, pads {n: P}, knobs {k: K}, buttons {name: colour or
    (colour, dim)}, kcol {k: colour or (colour, dim)} = the knob LEDs the guide gives a colour (the others keep the figures' teal ring)"""
    return dict(caption=dict(en=en, es=es), title=dict(en=title[0], es=title[1]), pads=pads or {}, knobs=knobs or {}, buttons=buttons or {},
                kcol=kcol or {})


def steps(col, n=16, first=1, label=None, dim=True):
    out = {first + i: P(col, "", None, dim) for i in range(n)}
    if label: out[first] = P(col, label[0], label[1], dim)
    return out


def knobs8(*labels):
    """knobs8(("Attack", "Ataque"), …) -> {1: K, …}; None leaves a knob unlabelled"""
    return {k + 1: K(*v) if isinstance(v, tuple) else K(v) for k, v in enumerate(labels) if v is not None}


# the MIDI 1 / 2 Preset view (oscillator engine), as the knob-page maps start from it
PAGE_RC = {1: ("amber", "VCA\nVCF", "VCA\nVCF"), 2: ("green", "OSC 1", "OSC 1"), 3: ("teal", "OSC 2", "OSC 2"), 4: ("yellow", "Seq.\nknobs", "Knobs\nsecuen."),
           5: ("magenta", "Mod.", "Mod."), 6: ("sky", "Matrix", "Matriz")}
PAGE_BETA = {1: ("yellow", "Seq.\nknobs", "Knobs\nsecuen."), 2: ("green", "OSC 1", "OSC 1"), 3: ("teal", "OSC 2", "OSC 2"), 4: ("amber", "VCA\nVCF", "VCA\nVCF"),
             5: ("magenta", "Mod.", "Mod."), 6: ("sky", "Matrix", "Matriz")}


def preset(beta=False, page=1, engine=("green", "Engine", "Motor"), osc2=None, patches=True, labels=True, two=False, extra=None):
    """the Preset view's pads: the page row (page = the pad lit bright), the patches (True = an example bank with labels; "calm" = a full bank,
    unlabelled, for the maps about the knobs: dim peach in the RCs, dim white = empty in the beta), the engine's pads (26-32)"""
    rows = PAGE_BETA if beta else PAGE_RC
    pads = {}
    for n, (c, en, es) in rows.items():
        if beta and n == 3 and not two: continue                         # (Beta 5.56) the OSC 2 page dark with one oscillator
        pads[n] = P(c, en if labels else "", es if labels else "", n != page)
    if patches == "calm":
        for n in range(9, 25): pads[n] = D("white" if beta else "peach")
    elif patches:
        if beta:
            for n, (c, en, es) in {9: ("green", "Osc", "Osc"), 10: ("violet", "FM", "FM"), 11: ("sand", "Wave-\ntable", "Wave-\ntable"),
                                   12: ("orange", "VA-drum", "VA-drum"), 14: ("teal", "Sample", "Muestra")}.items():
                pads[n] = D(c, en if labels else "", es if labels else "")
            pads[13] = P("green", "Last" if labels else "", "Último" if labels else "")
            for n in range(15, 25): pads[n] = D("white", "Empty" if labels else "", "Vacío" if labels else "")
        else:
            for n in (9, 10, 11, 13, 14): pads[n] = D("peach", "Patch" if labels else "", "Patch" if labels else "")
            pads[12] = P("peach", "Last" if labels else "", "Último" if labels else "")
            for n in range(15, 25): pads[n] = P("violet", "Empty" if labels else "", "Vacío" if labels else "")
    eng = P(engine[0], engine[1] if labels else "", engine[2] if labels else "")
    pads.update({26: D("magenta", "Flip" if labels else ""), 27: eng, 29: D("amber", "Order" if labels else "", "Orden" if labels else ""),
                 30: D("violet", "Step\ndrum" if labels else ""), 32: P("magenta", "Voice\nmode" if labels else "", "Modo\nde voz" if labels else "")})
    if osc2 is not False: pads[28] = P("green", "2 osc" if labels else "", None, not two)
    if extra: pads.update(extra)
    return pads


MIDI_BTN = {"MIDI 1": "blue", "Preset": "blue", "Oct ▼": "white"}

# ---------------------------------------------------------------------------------------------------- the maps
V = {}

# ===== 1. Setup
V["setup"] = [MAP(
    "Setup view (MIDI 1 selected): pads 1-15 = the track's MIDI channel, pad 16 = channel 16 (project and FX); pads 22 / 23 = the reverb / delay "
    "return through mixer strip 3 / 4 (cream / peach); pads 29 / 30 = the Program Change listen / output channel (since RC2); Record (yellow) = record "
    "the internal routings (since RC2); Note (green) = an external keyboard through the arpeggiator (since RC4); K4 = General MIDI drums (green = on), "
    "K5-K8 = the GM note of Drum 1-4 (since RC4). Beta 5.56 only: Preset (green) = knob hold; K1 / K2 = velocity → amplitude / velocity → filter.",
    "Vista Setup (MIDI 1 elegida): pads 1-15 = el canal MIDI de la pista, pad 16 = canal 16 (proyecto y FX); pads 22 / 23 = el retorno de reverb / "
    "delay por la tira 3 / 4 del mixer (crema / melocotón); pads 29 / 30 = el canal de escucha / salida de los Program Change (desde RC2); Record "
    "(amarillo) = grabar los ruteos internos (desde RC2); Note (verde) = un teclado externo por el arpegiador (desde RC4); K4 = drums General MIDI "
    "(verde = encendido), K5-K8 = la nota GM de Drum 1-4 (desde RC4). Solo Beta 5.56: Preset (verde) = retener knob; K1 / K2 = velocity → amplitud / "
    "velocity → filtro.",
    ("Setup", "Setup"),
    pads={**{n: D("grey", f"Ch {n}", f"Can. {n}") for n in range(1, 17)}, 22: P("cream", "Rev\n→ 3"), 23: D("peach", "Dly\n→ 4", "Del\n→ 4"),
          29: D("grey", "PGM\nRx"), 30: D("grey", "PGM\nTx")},
    knobs=knobs8(("Vel → amp", "Vel → amplitud"), ("Vel → filter", "Vel → filtro"), None, ("GM drums", "Drums GM"), ("Drum 1 note", "Nota Drum 1"),
                 ("Drum 2 note", "Nota Drum 2"), ("Drum 3 note", "Nota Drum 3"), ("Drum 4 note", "Nota Drum 4")),
    buttons={"MIDI 1": "blue", "Record": "yellow", "Note": "green", "Preset": "green"},
    kcol={1: "white", 2: "white", 4: "green", 5: "orange", 6: "yellow", 7: "violet", 8: "teal"})]

V["advanced-setup"] = [MAP(
    "Advanced Setup: Duplicate = the MIDI Thru jack's mode (since RC2): Thru (dim red) → Out 2 (green) → Merge (yellow) → Filter (blue); pad 22 = "
    "delayed save (since RC4.05) and pad 23 = USB merge (since RC4), green on / dim off; K1 = the pads' velocity curve (since RC4, in the RCs); K3 = "
    "the external inputs' gain (Beta 5.56 only). Its stock settings work as on the original.",
    "Advanced Setup: Duplicate = el modo del jack MIDI Thru (desde RC2): Thru (rojo tenue) → Out 2 (verde) → Merge (amarillo) → Filter (azul); pad 22 "
    "= guardado diferido (desde RC4.05) y pad 23 = fusión USB (desde RC4), verde encendido / tenue apagado; K1 = la curva de velocity de los pads "
    "(desde RC4, en las RC); K3 = la ganancia de las entradas externas (solo Beta 5.56). Sus ajustes de stock, como en el original.",
    ("Advanced Setup", "Advanced Setup"),
    pads={22: D("green", "Delayed\nsave", "Guardado\ndiferido"), 23: D("green", "USB\nmerge", "Fusión\nUSB")},
    knobs={1: K("Velocity curve", "Curva velocity"), 3: K("Input gain", "Ganancia entradas")},
    buttons={"Duplicate": "yellow"})]

# ===== 2. Synth 1 / 2
V["synth-nota"] = [
    MAP("Synth 1's Note view: pads 1-16 = the steps, 17-32 = the keyboard (as on the original). Synth 1 again = its source view; Synth 1 held + "
        "Synth 2 = the split keyboard (since RC2); Shift + a key = latch it (since RC4); Clear + Synth 1 = the macros back to the loaded patch's (since "
        "RC2). Beta 5.56 only: Record held + a step = a snapshot of the moved macros into that step (yellow while held); Shift + Preset = the project's "
        "sound back.",
        "Vista Note de Synth 1: pads 1-16 = los pasos, 17-32 = el teclado (como en el original). Synth 1 otra vez = su vista de la fuente; Synth 1 "
        "mantenido + Synth 2 = el teclado partido (desde RC2); Shift + tecla = latch (desde RC4); Clear + Synth 1 = los macros a los del patch cargado "
        "(desde RC2). Solo Beta 5.56: Record mantenido + paso = foto de los macros movidos en ese paso (amarillo mientras lo mantienes); Shift + Preset "
        "= vuelve el sonido del proyecto.",
        ("Synth 1 Note", "Note de Synth 1"),
        pads={**steps("magenta", label=("Steps", "Pasos")), **steps("magenta", first=17, label=("Keys", "Teclas"), dim=False)},
        knobs={k: K(f"Macro {k}") for k in range(1, 9)},
        buttons={"Synth 1": "magenta", "Note": "magenta"}),
    MAP("Velocity view with Shift held (since RC4): the step pads light yellow; Shift + a step marks it (red): there the automation lets go and the "
        "parameters go back to the project's values (again = unmark). Beta 5.56 only: only the steps with automation are yellow; Shift + a yellow step "
        "= its values on the knobs until Shift is let go; a yellow step held + another = a straight sweep between them; Clear + a step erases its knob "
        "automation.",
        "Vista Velocity con Shift (desde RC4): los pads de paso en amarillo; Shift + paso lo marca (rojo): ahí la automatización se suelta y los "
        "parámetros vuelven a los valores del proyecto (otra vez = desmarcar). Solo Beta 5.56: solo los pasos con automatización en amarillo; Shift + un "
        "paso amarillo = sus valores en los knobs hasta soltar Shift; un paso amarillo mantenido + otro = un sweep en línea recta entre ellos; Clear + "
        "paso borra su automatización de knobs.",
        ("Velocity + Shift", "Velocity + Shift"),
        pads={**steps("yellow", dim=False), 3: P("red", "Mark", "Marca"), 11: P("red", "Mark", "Marca"), **steps("grey", first=17)},
        buttons={"Synth 1": "magenta", "Velocity": "magenta", "Shift": "grey"}),
    MAP("Split keyboard (since RC2): hold Synth 1 and press Synth 2 (since RC2.02 any pair of Synth 1, Synth 2, MIDI 1 and MIDI 2): the top two rows "
        "play the track held first, the bottom two the other, each with its scale, octave and velocity. Since RC4, holding a track button gives the "
        "knobs to that track; a short tap or a view button closes it.",
        "Teclado partido (desde RC2): mantén Synth 1 y pulsa Synth 2 (desde RC2.02, cualquier par de Synth 1, Synth 2, MIDI 1 y MIDI 2): las dos filas "
        "de arriba tocan la pista mantenida primero y las dos de abajo la otra, cada una con su escala, octava y velocity. Desde RC4, mantener un botón "
        "de pista da los knobs a esa pista; un toque corto o un botón de vista lo cierra.",
        ("Split keyboard", "Teclado partido"),
        pads={**steps("magenta", 16, 1, ("Synth 1", "Synth 1"), dim=False), **steps("pine", 16, 17, ("Synth 2", "Synth 2"), dim=False)},
        buttons={"Synth 1": "magenta", "Synth 2": "pine"}),
    MAP("Chord screen (since RC4; the expanded Note view, Shift + pad 8): row 1 = the chord type (Shift + pads 1-7: sus2, 6, m6, add9, 9, 7sus4, fifth); "
        "pads 9-12 = the inversion (blue); 13 = open voicing, 14 = the root an octave down, 15 = diatonic (the project's scale), 16 = chord latch (Beta "
        "5.56 only: inverse chord), green on; rows 3-4 = the roots: hold one to play its chord. Shift + a root latches the whole chord.",
        "Pantalla de acordes (desde RC4; Note ampliada, Shift + pad 8): fila 1 = el tipo de acorde (Shift + pads 1-7: sus2, 6, m6, add9, 9, 7sus4, "
        "quinta); pads 9-12 = la inversión (azul); 13 = voicing abierto, 14 = la fundamental una octava abajo, 15 = diatónico (la escala del proyecto), "
        "16 = latch del acorde (solo Beta 5.56: acorde inverso), verde encendido; filas 3-4 = las fundamentales: mantén una para tocar su acorde. Shift + "
        "fundamental fija el acorde entero.",
        ("Chord screen", "Acordes"),
        pads={1: P("white", "Maj", "May"), 2: D("white", "Min", "Men"), 3: D("white", "7"), 4: D("white", "m7"), 5: D("white", "maj7"), 6: D("white", "sus4"),
              7: D("white", "dim"), 8: D("white", "aug", "aum"), 9: P("blue", "Root", "Fund."), 10: D("white", "1st", "1.ª"), 11: D("white", "2nd", "2.ª"),
              12: D("white", "3rd", "3.ª"), 13: D("white", "Open", "Abierto"), 14: D("white", "Root\n−1 oct", "Fund.\n−1 oct"), 15: D("white", "Diat."),
              16: D("white", "Latch"), **steps("magenta", 16, 17, ("Roots", "Fundam."), dim=False)},
        buttons={"Synth 1": "magenta", "Note": "amber"}),
]

_PIANO = [None, 13, 15, None, 18, 20, 22, None, 12, 14, 16, 17, 19, 21, 23, 24, None, 1, 3, None, 6, 8, 10, None, 0, 2, 4, 5, 7, 9, 11, 12]
_KEYS = {0: "white", 2: "green", 4: "green", 7: "blue"}          # the example: root, +2, +4, the period +7


def _editor():
    """the editor's two octaves (pad -> interval above the root: tools/cscale.py's keyboard), the example scale lit, pad 8 = Jankó (yellow with Shift)"""
    pads = {}
    for i, iv in enumerate(_PIANO):
        if iv is None: continue
        lab = ("Root", "Tónica") if iv == 0 else (f"+{iv}", f"+{iv}")
        pads[i + 1] = P(_KEYS[iv], *lab) if iv in _KEYS else D("white", *lab)
    pads[8] = P("yellow", "Jankó")
    return pads


_JK3 = ["B", "C♯", "D♯", "F", "G", "A", "B", "C♯"]
_JK4 = ["C", "D", "E", "F♯", "G♯", "A♯", "C", "D"]
V["escalas"] = [
    MAP("Custom scale editor (since RC2; Shift + Scales, since RC4 also Scales twice), here with Shift held: rows 4 / 3 = the white / black keys of the "
        "first octave from the root, rows 2 / 1 = the second octave. A key pressed is a note of the scale (green, up to 7); the highest one is the "
        "period (blue), the root of the next iteration; the root white, free keys dim. This one repeats every 7 semitones: root, +2, +4, period +7. "
        "Shift + pad 8 = Jankó (since RC4; teal while on).",
        "Editor de la escala propia (desde RC2; Shift + Scales, desde RC4 también Scales dos veces), aquí con Shift pulsado: filas 4 / 3 = las teclas "
        "blancas / negras de la primera octava desde la tónica, filas 2 / 1 = la segunda octava. Una tecla pulsada es una nota de la escala (verde, hasta "
        "7); la más alta es el periodo (azul), la tónica de la iteración siguiente; la tónica en blanco, las teclas libres tenues. Esta se repite cada 7 "
        "semitonos: tónica, +2, +4, periodo +7. Shift + pad 8 = Jankó (desde RC4; verde azulado encendido).",
        ("Scale editor", "Escala propia"),
        pads=_editor(), buttons={"Scales": "yellow", "Shift": "grey"}),
    MAP("Jankó layout (since RC4; Shift + pad 8 in the editor) on MIDI 1 with root C, Note view: every column goes up a whole tone and the upper row of "
        "each pair is a semitone lower, so every chord has the same shape in any key; the root pads in the root colour. Octave: a tap = a semitone, "
        "held = an octave.",
        "Disposición Jankó (desde RC4; Shift + pad 8 en el editor) en MIDI 1 con tónica C, vista Note: cada columna sube un tono y la fila de arriba de "
        "cada pareja es medio tono más grave, así que cada acorde tiene la misma forma en cualquier tono; los pads de la tónica, en el color de la "
        "tónica. Octave: un toque = medio tono, mantenido = una octava.",
        ("Jankó", "Jankó"),
        pads={**steps("sky", label=("Steps", "Pasos")), **{17 + i: P("blue", n) for i, n in enumerate(_JK3)},
              **{25 + i: P("steel" if n == "C" else "blue", n) for i, n in enumerate(_JK4)}},
        buttons={"MIDI 1": "blue", "Note": "blue"}),
]

V["synth-fuente"] = [MAP(
    "Synth source view (Synth 1 / 2 pressed again; since RC4 also Shift + Synth 1 / 2): pads 25-29 = the source of the synth's noise (noise; audio "
    "input 1 / 2; input 1 / 2 phase-inverted), the chosen one bright — the patch needs some noise level; pad 30 = the synth's step-drummer; pad 32 = "
    "the macro destination editor (since RC2): a knob picks its macro, Octave ▼ / ▲ = the field (slot, start, end, destination, depth), the pads draw "
    "its number. Any other button closes the view.",
    "Vista de la fuente del sinte (Synth 1 / 2 otra vez; desde RC4 también Shift + Synth 1 / 2): pads 25-29 = la fuente del ruido del sinte (ruido; "
    "entrada de audio 1 / 2; entrada 1 / 2 con la fase invertida), la elegida brillante — el patch necesita algo de nivel de ruido; pad 30 = el "
    "step-drummer del sinte; pad 32 = el editor de los destinos de los macros (desde RC2): un knob elige su macro, Octave ▼ / ▲ = el campo (ranura, "
    "inicio, fin, destino, profundidad), los pads dibujan su número. Cualquier otro botón cierra la vista.",
    ("Synth source", "Fuente del sinte"),
    pads={25: P("magenta", "Noise", "Ruido"), 26: D("magenta", "In 1", "Ent. 1"), 27: D("magenta", "In 2", "Ent. 2"), 28: D("magenta", "In 1\ninv."),
          29: D("magenta", "In 2\ninv."), 30: D("violet", "Step\ndrum"), 32: D("teal", "Macro\neditor", "Editor\nmacros")},
    knobs={k: K(f"Macro {k}") for k in range(1, 9)},
    buttons={"Synth 1": "magenta"})]


def _categories():
    import wiki_colours as WC
    cats, rgb, trk = WC.app_colours()
    pads = {1: (trk[0], cats[0][1], cats[0][0], False)}
    for c in range(1, 15): pads[c + 1] = (rgb[c], cats[c][1], cats[c][0], False)
    pads[16] = D("white", "Empty", "Vacío")
    return pads


V["synth-preset"] = [
    MAP("Synth 1's Preset view (since RC4.10 the original's colours: the patches in the track colour, the chosen one white): Clear + pad, then Clear + "
        "the same pad within 5 s = save the patch as it sounds into that slot (it blinks white while asking; since RC2); Duplicate + pad A + pad B = "
        "swap two patches; Duplicate + A, another pack, Duplicate + B = copy A there. Not in the internal memory's pack.",
        "Vista Preset de Synth 1 (desde RC4.10 los colores del original: los patches en el color de la pista, el elegido en blanco): Clear + pad y "
        "Clear + el mismo pad antes de 5 s = guardar el patch tal como suena en ese hueco (parpadea en blanco mientras pregunta; desde RC2); Duplicate + "
        "pad A + pad B = intercambiar dos patches; Duplicate + A, otro pack, Duplicate + B = copiar A allí. No en el pack de la memoria interna.",
        ("Synth 1 Preset", "Preset de Synth 1"),
        pads={**steps("magenta", 32), 1: P("white", "Chosen", "Elegido"), 6: P("white", "Save?", "¿Guardar?")},
        buttons={"Synth 1": "magenta", "Preset": "magenta", "Duplicate": "white"}),
    MAP("Beta 5.56 only: each patch in the colour of its Components category (here one of each; pad 1 = None, the track colour; pad 16 = an empty slot, "
        "dim white; the chosen one white). While a save asks (Clear + pad), K1 picks the category to save, in its colour.",
        "Solo Beta 5.56: cada patch en el color de su categoría de Components (aquí una de cada; pad 1 = Ninguna, el color de la pista; pad 16 = un "
        "hueco vacío, blanco tenue; el elegido en blanco). Mientras un guardado pregunta (Clear + pad), K1 elige la categoría que se guarda, en su color.",
        ("Patch categories", "Categorías"),
        pads=None, knobs={1: K("Category (save)", "Categoría (guardar)")},
        buttons={"Synth 1": "magenta", "Preset": "magenta"}),
    MAP("Beta 5.56 only: the morph view (hold two to four patches for 0.4 s): K1 = the position along the chain (red, yellow, green, blue = patches "
        "1-4); K2 = square LFO, K3 = both LFOs' rate, K4 = random-step LFO; K5 / K6 = the slow morph's destination / length; K7 / K8 = envelope amount "
        "/ time. Pads 1 / 8 = the envelope (held = sustained); pad 32 (red) = out; Preset = the patches; Clear + knob = 0.",
        "Solo Beta 5.56: la vista del morph (mantén de dos a cuatro patches 0,4 s): K1 = la posición en la cadena (rojo, amarillo, verde, azul = "
        "patches 1-4); K2 = LFO cuadrado, K3 = la velocidad de los dos LFO, K4 = LFO de pasos al azar; K5 / K6 = destino / duración del morph lento; "
        "K7 / K8 = cantidad / tiempo de la envolvente. Pads 1 / 8 = la envolvente (mantenidos = sostenida); pad 32 (rojo) = salir; Preset = los "
        "patches; Clear + knob = 0.",
        ("Morph", "Morph"),
        pads={1: P("magenta", "Env.", "Envolv."), 8: P("magenta", "Env.", "Envolv."), 32: P("red", "Out", "Salir")},
        knobs=knobs8(("Position", "Posición"), ("Square LFO", "LFO cuadrado"), ("LFO rate", "Veloc. LFO"), ("Random LFO", "LFO al azar"),
                     ("Slow: target", "Lento: destino"), ("Slow: length", "Lento: duración"), ("Env. amount", "Cant. envolv."),
                     ("Env. time", "Tiempo envolv.")),
        buttons={"Synth 1": "magenta"}),
]
V["synth-preset"][1]["pads"] = "categories"                       # filled from the SD app's colours when drawn

# ===== 3. MIDI 1 / 2
_K_VCF = knobs8(("Attack", "Ataque"), "Release", ("Env → level", "Env → nivel"), ("Env → filter", "Env → filtro"), ("Filter", "Filtro"),
                ("Resonance", "Resonancia"), ("LFO speed", "Veloc. LFO"), ("Effect", "Efecto"))
_ROW_RC = {17: ("white", "Off", "Apagado"), 18: ("amber", "Line\nin", "Línea"), 19: ("green", "Osc", "Osc"), 20: ("orange", "VA-drum", "VA-drum"),
           21: ("magenta", "Gran.", "Gran."), 22: ("teal", "Sample", "Muestra"), 23: ("blue", "FX seq", "Sec. FX"), 24: ("violet", "FM", "FM")}
_ROW_BETA = {17: ("white", "No\nvoice", "Sin\nvoz"), 18: ("amber", "VCA\nVCF\nFX", "VCA\nVCF\nFX"), 19: ("green", "Osc", "Osc"),
             20: ("orange", "VA-drum", "VA-drum"), 21: ("sand", "Wave-\ntable", "Wave-\ntable"), 22: ("teal", "Sample", "Muestra"),
             23: ("magenta", "Gran.", "Gran."), 24: ("violet", "FM", "FM")}


def _row(row, cur=19):
    return {n: P(c, en, es, n != cur) for n, (c, en, es) in row.items()}


_VM = [("green", "Retrig"), ("yellow", "Legato"), ("teal", "Glide"), ("green", "Uni\nretrig"), ("yellow", "Uni\nlegato"), ("teal", "Uni\nglide"),
       ("violet", "Uni\nalways"), ("magenta", "Poly")]
V["midi-preset"] = [
    MAP("MIDI 1's Preset view with the oscillator engine, in the RCs: pads 1-5 = the engine's knob pages (1 VCA-VCF, 2 OSC 1, 3 OSC 2, 4 sequenceable "
        "knobs — Shift + 4 non-sequenceable —, 5 modulation; held ½ s = only while held), 6 = the mod matrix; 9-24 = own-synth patches (dim peach = "
        "saved, bright = the last used, violet = empty; Octave = 8 pages; a tap loads, Clear + pad twice saves); 26 = patch flip; 27 = the engine (a "
        "tap opens the engine row); 28 = one / two oscillators; 29 = chain order; 30 = step-drummer; 32 = voice mode. Pad 31 lights with the VA-drum "
        "(velocity → its envelopes).",
        "Vista Preset de MIDI 1 con el motor oscilador, en las RC: pads 1-5 = las páginas de knobs del motor (1 VCA-VCF, 2 OSC 1, 3 OSC 2, 4 knobs "
        "secuenciables — Shift + 4 no secuenciables —, 5 modulación; mantenido ½ s = solo mientras lo mantienes), 6 = la matriz de modulación; 9-24 = "
        "patches del sinte propio (melocotón tenue = guardado, brillante = el último usado, violeta = vacío; Octave = 8 páginas; un toque carga, Clear + "
        "pad dos veces guarda); 26 = patch flip; 27 = el motor (un toque abre la fila de motores); 28 = uno / dos osciladores; 29 = orden de la cadena; "
        "30 = step-drummer; 32 = modo de voz. El pad 31 se enciende con el VA-drum (velocity → sus envolventes).",
        ("MIDI 1 Preset", "Preset de MIDI 1"),
        pads=preset(), knobs=_K_VCF, buttons=MIDI_BTN),
    MAP("Beta 5.56 only, the same view: pad 1 = sequenceable knobs (Shift + 1 = non-sequenceable) and pad 4 = filter / VCA swap places; the patches "
        "show their engine's colour (empty = dim white; Duplicate + an empty slot saves there); pad 3 lights with two oscillators; pad 26 opens the "
        "flip view; with «no voice» pad 31 = the FX sequencer; filter → VCA → FX is the default order (pad 29).",
        "Solo Beta 5.56, la misma vista: el pad 1 = knobs secuenciables (Shift + 1 = no secuenciables) y el pad 4 = filtro / VCA cambian de sitio; los "
        "patches en el color de su motor (vacío = blanco tenue; Duplicate + un hueco vacío guarda ahí); el pad 3 se enciende con dos osciladores; el "
        "pad 26 abre la vista de flip; con «sin voz» el pad 31 = el secuenciador de efectos; el orden de fábrica es filtro → VCA → FX (pad 29).",
        ("MIDI 1 Preset", "Preset de MIDI 1"),
        pads=preset(beta=True, page=4), knobs=_K_VCF, buttons=MIDI_BTN),
    MAP("The engine row in the RCs (since RC4; a tap on pad 27): pads 17-24 = off, line input, oscillator, VA-drum, granular, sample, FX sequencer and "
        "FM, the current one bright; a tap picks one, pad 27 again closes the row (meanwhile pads 9-24 load no patches). Shift + pad 27 steps to the "
        "next engine.",
        "La fila de motores en las RC (desde RC4; un toque al pad 27): pads 17-24 = apagado, entrada de línea, oscilador, VA-drum, granular, muestra, "
        "secuenciador de efectos y FM, el actual brillante; un toque elige uno, el pad 27 otra vez cierra la fila (mientras, los pads 9-24 no cargan "
        "patches). Shift + pad 27 pasa al motor siguiente.",
        ("Engine row", "Fila de motores"),
        pads={**preset(patches=False), **_row(_ROW_RC), 27: P("green", "Engine", "Motor")}, knobs=_K_VCF, buttons=MIDI_BTN),
    MAP("Beta 5.56 only, the engine row: no voice, VCA / VCF / FX only (the line input), oscillator, VA-drum, wavetable (sand), sample, granular and FM; "
        "the FX sequencer is pad 31 once «no voice» is chosen (dim blue; a tap turns it on).",
        "Solo Beta 5.56, la fila de motores: sin voz, solo VCA / VCF / FX (la entrada de línea), oscilador, VA-drum, wavetable (arena), muestra, "
        "granular y FM; el secuenciador de efectos es el pad 31 cuando se elige «sin voz» (azul tenue; un toque lo enciende).",
        ("Engine row", "Fila de motores"),
        pads={**preset(beta=True, page=4, patches=False), **_row(_ROW_BETA), 27: P("green", "Engine", "Motor")}, knobs=_K_VCF,
        buttons=MIDI_BTN),
    MAP("Voice modes (since RC4; a tap on pad 32 with the engine on): pads 17-24 = retrigger, legato, glide, uni retrig, uni legato, uni glide, uni "
        "always-glide and poly (modes with the same name share a colour; the current one bright); K1 = the glide's time (teal), K2 = the unison's "
        "detune (blue). Saved with the patch and the project.",
        "Modos de voz (desde RC4; un toque al pad 32 con el motor encendido): pads 17-24 = retrigger, legato, glide, uni retrig, uni legato, uni glide, "
        "uni always-glide y poly (los que se llaman igual, del mismo color; el actual brillante); K1 = el tiempo del glide (verde azulado), K2 = la "
        "desafinación del unísono (azul). Se guardan con el patch y con el proyecto.",
        ("Voice modes", "Modos de voz"),
        pads={**preset(patches=False), **{17 + i: P(c, n, None, i != 7) for i, (c, n) in enumerate(_VM)},
              32: P("magenta", "Voice\nmode", "Modo\nde voz")},
        knobs={1: K("Glide time", "Tiempo de glide"), 2: K("Unison detune", "Desafin. unísono")}, buttons=MIDI_BTN, kcol={1: "teal", 2: "blue"}),
    MAP("Beta 5.56 only: the flip view (pad 26, white while open), MIDI 1 pointing at Drum 1: row 3 = the mode, pad 17 patch flip (PGM seq) or pad 18 "
        "step flip (in the target's colour; the one on bright, a tap on it turns it off); row 2 = the eight tracks in their colours, the target bright, "
        "the track itself dark. While pointing, each note of the track makes Drum 1 jump to the note's step, and the engine is off (pad 27 grey; pads "
        "1-8 = the stock templates).",
        "Solo Beta 5.56: la vista de flip (pad 26, blanco mientras está abierta), MIDI 1 apuntando a Drum 1: fila 3 = el modo, pad 17 patch flip (PGM "
        "seq) o pad 18 step flip (en el color del destino; el encendido brillante, un toque lo apaga); fila 2 = las ocho pistas en sus colores, el destino "
        "brillante, la propia apagada. Mientras apunta, cada nota de la pista hace saltar a Drum 1 al paso de la nota, y el motor está apagado (pad 27 "
        "gris; pads 1-8 = las plantillas de stock).",
        ("Flip view", "Vista de flip"),
        pads={1: P("white", "Tmpl 1", "Plant. 1"), **{n: P("blue", f"Tmpl {n}", f"Plant. {n}") for n in range(2, 9)},
              **{9 + i: P(TRACK[t], t, None, t != "Drum 1") for i, t in enumerate(TRACKS) if t != "MIDI 1"},
              17: D("white", "PGM\nseq"), 18: P("orange", "Step\nflip"), 25: D("magenta", "CC\nedit", "Editor\nCC"), 26: P("white", "Flip\nview", "Vista\nflip"),
              27: D("white", "Engine", "Motor"), 31: D("blue", "FX seq", "Sec. FX")},
        buttons=MIDI_BTN),
]

V["midi-voces"] = [MAP(
    "A simpler map (this chapter is mostly tables): the voice modes of pad 32 with how many voices each gives a track — 1 in retrigger, legato and glide; "
    "4 in the unison modes and poly (FM: 6, or 3 each with MIDI 1 and MIDI 2 both in FM; the sample mode's unison: 1; the granular: always 1). Each voice "
    "is turned down by how many sound, so chords do not clip; when the DSP is short of time, the voice limiter switches off the quietest one ringing out.",
    "Un mapa más sencillo (este capítulo es sobre todo tablas): los modos de voz del pad 32 con cuántas voces da cada uno a una pista — 1 en retrigger, "
    "legato y glide; 4 en los unísonos y en poly (FM: 6, o 3 cada una con MIDI 1 y MIDI 2 en FM; el unísono del modo muestra: 1; el granular: siempre 1). "
    "Cada voz baja según cuántas suenan, para que los acordes no recorten; si el DSP va justo de tiempo, el límite de voces apaga la que suena más baja "
    "soltándose.",
    ("Voices", "Voces"),
    pads={**{17 + i: P(c, f"{n}\n{'1' if i < 3 else '4·FM 6'}", None, i != 7) for i, (c, n) in enumerate(_VM)},
          32: P("magenta", "Voice\nmode", "Modo\nde voz")},
    knobs={1: K("Glide"), 2: K("Detune", "Desafinación")}, buttons=MIDI_BTN, kcol={1: "teal", 2: "blue"})]


def kp(en, es, title, knobs, beta=False, page=1, engine=("green", "Engine", "Motor"), two=False, extra=None, buttons=None):
    """a knob-page map: the Preset view with that page's pad bright (the patches drawn as a full bank, unlabelled)"""
    pads = preset(beta=beta, page=page, engine=engine, two=two, extra=extra, patches="calm")
    return MAP(en, es, title, pads=pads, knobs=knobs, buttons=buttons or MIDI_BTN)


V["midi-knobs"] = [
    kp("Page 1, VCA-VCF (pad 1 in the RCs; pad 4 in Beta 5.56): K1 attack, K2 release, K3 / K4 envelope → level / → filter, K5 filter, K6 resonance, "
       "K7 LFO speed (bipolar since RC4: right free, left synced to the tempo), K8 effect amount.",
       "Página 1, VCA-VCF (pad 1 en las RC; pad 4 en la Beta 5.56): K1 ataque, K2 release, K3 / K4 envolvente → nivel / → filtro, K5 filtro, K6 "
       "resonancia, K7 velocidad del LFO (bipolar desde RC4: derecha libre, izquierda a tempo), K8 cantidad de efecto.",
       ("VCA-VCF", "VCA-VCF"), _K_VCF),
    kp("Page 1 with Shift: K1 sustain, K2 decay, K3 / K4 LFO → level / → filter, K5 filter type (DJ, LP 12, HP 12, BP, notch, LP 24, HP 24), K6 VCA "
       "gain (up to +18 dB with saturation), K8 effect type (soft, hard, fold, wavefold, ring, comb, chorus). Type knobs show the type as a colour and "
       "the position within it as brightness.",
       "Página 1 con Shift: K1 sustain, K2 decay, K3 / K4 LFO → nivel / → filtro, K5 tipo de filtro (DJ, LP 12, HP 12, BP, notch, LP 24, HP 24), K6 "
       "gain del VCA (hasta +18 dB con saturación), K8 tipo de efecto (suave, dura, plegado, wavefold, ring, comb, chorus). Los knobs de tipo enseñan el "
       "tipo con el color y la posición dentro de él con el brillo.",
       ("VCA-VCF + Shift", "VCA-VCF + Shift"),
       knobs8("Sustain", "Decay", ("LFO → level", "LFO → nivel"), ("LFO → filter", "LFO → filtro"), ("Filter type", "Tipo de filtro"),
              ("VCA gain", "Gain del VCA"), None, ("Effect type", "Tipo de efecto")),
       buttons={**MIDI_BTN, "Shift": "grey"}),
    kp("Page 2, OSC 1 (oscillator and VA-drum), in the RCs: K1 TUNE, K2 SHAPE, K3 / K4 envelope → pitch / → shape, K5 / K6 LFO → pitch / → shape, K7 "
       "WAVE (the morph sine → triangle → saw → square; since RC4 in the sample mode, the stereo width), K8 LFO → morph. With Shift: K1 FINE, K2 MIX OSC "
       "1 ↔ OSC 2, K3 BITSYNC, K8 envelope → morph.",
       "Página 2, OSC 1 (oscilador y VA-drum), en las RC: K1 TUNE, K2 SHAPE, K3 / K4 envolvente → tono / → forma, K5 / K6 LFO → tono / → forma, K7 "
       "WAVE (el morph seno → triángulo → sierra → cuadrada; desde RC4 en el modo muestra, la anchura estéreo), K8 LFO → morph. Con Shift: K1 FINE, K2 "
       "MIX OSC 1 ↔ OSC 2, K3 BITSYNC, K8 envolvente → morph.",
       ("OSC 1", "OSC 1"),
       knobs8("TUNE", "SHAPE", ("Env → pitch", "Env → tono"), ("Env → shape", "Env → forma"), ("LFO → pitch", "LFO → tono"),
              ("LFO → shape", "LFO → forma"), "WAVE", "LFO → morph"), page=2),
    kp("Beta 5.56 only, page 2 with the oscillator, the VA-drum and the wavetable: K1 TUNE, K2 FINE, K3 WAVE (the wavetable's position; the sample "
       "mode's stereo width), K4 SHAPE (the wavetable's warp), K5 / K6 / K8 = LFO → FM / → ring / → mix (centre = none), K7 LFO → morph. With a single "
       "oscillator K5 = the sub-oscillator's level, K6 = the noise level, K8 = LFO → sub.",
       "Solo Beta 5.56, página 2 con el oscilador, el VA-drum y la wavetable: K1 TUNE, K2 FINE, K3 WAVE (la posición en la wavetable; la anchura "
       "estéreo del modo muestra), K4 SHAPE (el warp de la wavetable), K5 / K6 / K8 = LFO → FM / → ring / → mix (centro = nada), K7 LFO → morph. Con un "
       "solo oscilador K5 = el nivel del sub-oscilador, K6 = el nivel del ruido, K8 = LFO → sub.",
       ("OSC 1", "OSC 1"),
       knobs8("TUNE", "FINE", "WAVE", "SHAPE", "LFO → FM", "LFO → ring", "LFO → morph", "LFO → mix"), beta=True, page=2, two=True),
    kp("Beta 5.56 only, page 2 with Shift: K1 / K2 envelope / LFO → pitch, K3 envelope → morph, K4 envelope → shape, K5 / K6 / K8 envelope → FM / → "
       "ring / → mix, K7 LFO → shape. With a single oscillator: Shift + K5 / K6 = envelope → sub / → noise, Shift + K8 = LFO → noise.",
       "Solo Beta 5.56, página 2 con Shift: K1 / K2 envolvente / LFO → tono, K3 envolvente → morph, K4 envolvente → forma, K5 / K6 / K8 envolvente → FM "
       "/ → ring / → mix, K7 LFO → forma. Con un solo oscilador: Shift + K5 / K6 = envolvente → sub / → ruido, Shift + K8 = LFO → ruido.",
       ("OSC 1 + Shift", "OSC 1 + Shift"),
       knobs8(("Env → pitch", "Env → tono"), ("LFO → pitch", "LFO → tono"), "Env → morph", ("Env → shape", "Env → forma"), "Env → FM", "Env → ring",
              ("LFO → shape", "LFO → forma"), "Env → mix"), beta=True, page=2, two=True, buttons={**MIDI_BTN, "Shift": "grey"}),
    kp("Page 2 with the granular engine (pad 27 magenta): K1 pitch ±24 st, K2 position in the sample, K3 scan (centre = frozen), K4 grain size 5-500 ms, "
       "K5 density 1-16 grains, K6 scan zone, K7 LFO → position, K8 envelope → position.",
       "Página 2 con el motor granular (pad 27 magenta): K1 tono ±24 st, K2 posición en el sample, K3 scan (centro = congelado), K4 tamaño del grano "
       "5-500 ms, K5 densidad 1-16 granos, K6 zona del scan, K7 LFO → posición, K8 envolvente → posición.",
       ("Granular", "Granular"),
       knobs8(("Pitch", "Tono"), ("Position", "Posición"), "Scan", ("Grain size", "Tamaño grano"), ("Density", "Densidad"), ("Scan zone", "Zona scan"),
              ("LFO → position", "LFO → posición"), ("Env → position", "Env → posición")),
       page=2, engine=("magenta", "Engine", "Motor"), extra={2: P("green", "Gran.")}),
    kp("The granular page with Shift: K1 fine ±1 st, K2 position spread, K3 reverse grains (left) / pitch spread (right; bipolar since RC4), K4 stereo "
       "spread (since RC4), K5 window, K6 note mode (pitch / slicer / stretch), K7 LFO → size, K8 the source: the capture or a drum's sample (since RC2).",
       "La página granular con Shift: K1 fino ±1 st, K2 dispersión de la posición, K3 granos al revés (izquierda) / dispersión del tono (derecha; "
       "bipolar desde RC4), K4 dispersión estéreo (desde RC4), K5 ventana, K6 modo de nota (tono / slicer / stretch), K7 LFO → tamaño, K8 la fuente: la "
       "captura o el sample de un drum (desde RC2).",
       ("Granular + Shift", "Granular + Shift"),
       knobs8(("Fine", "Fino"), ("Position spread", "Dispersión pos."), ("Reverse ↔ spread", "Reverso ↔ disp."), ("Stereo spread", "Disp. estéreo"),
              ("Window", "Ventana"), ("Note mode", "Modo de nota"), ("LFO → size", "LFO → tamaño"), ("Source", "Fuente")),
       page=2, engine=("magenta", "Engine", "Motor"), extra={2: P("green", "Gran.")}, buttons={**MIDI_BTN, "Shift": "grey"}),
    kp("Page 3, OSC 2, in the RCs (since RC2 the eight values without Shift): K1 TUNE 2, K2 SHAPE 2, K3 MIX OSC 1 ↔ OSC 2, K4 FM, K5 FINE 2, K6 BITSYNC "
       "(sync and the bitwise modes), K7 WAVE 2, K8 RING.",
       "Página 3, OSC 2, en las RC (desde RC2 los ocho valores sin Shift): K1 TUNE 2, K2 SHAPE 2, K3 MIX OSC 1 ↔ OSC 2, K4 FM, K5 FINE 2, K6 BITSYNC "
       "(sync y los modos bit a bit), K7 WAVE 2, K8 RING.",
       ("OSC 2", "OSC 2"),
       knobs8("TUNE 2", "SHAPE 2", "MIX 1 ↔ 2", "FM", "FINE 2", "BITSYNC", "WAVE 2", "RING"), page=3, two=True),
    kp("Beta 5.56 only, page 3 with the oscillator, the VA-drum and the wavetable: K1 = OSC 2's ratio to its note (centre = 1), K2 detune (±50 cents), K3 "
       "WAVE 2, K4 SHAPE 2, K5 FM (centre = none; right OSC 2 → OSC 1, left the other way), K6 RING, K7 sync + bitwise, K8 MIX OSC 1 ↔ OSC 2.",
       "Solo Beta 5.56, página 3 con el oscilador, el VA-drum y la wavetable: K1 = ratio de OSC 2 respecto a su nota (centro = 1), K2 detune (±50 "
       "cents), K3 WAVE 2, K4 SHAPE 2, K5 FM (centro = nada; derecha OSC 2 → OSC 1, izquierda al revés), K6 RING, K7 sync + bitwise, K8 MIX OSC 1 ↔ OSC 2.",
       ("OSC 2", "OSC 2"),
       knobs8(("Ratio 2", "Ratio 2"), "Detune", "WAVE 2", "SHAPE 2", "FM", "RING", "Sync + bitwise", "MIX 1 ↔ 2"), beta=True, page=3, two=True),
    kp("Page 4, sequenceable knobs (pad 4 in the RCs; pad 1 in Beta 5.56): the eight values recorded as automation with Record + Play, by default TUNE, "
       "release, envelope → level, envelope → filter, filter, resonance, LFO speed and effect. Since RC4, Shift + knob = that knob's destination (any "
       "of the 33 parameters, in its page's colour; Clear held, then Shift + knob = the factory one); Record held + a step = a snapshot of the values "
       "into that step.",
       "Página 4, knobs secuenciables (pad 4 en las RC; pad 1 en la Beta 5.56): los ocho valores que se graban como automatización con Record + Play, "
       "de fábrica TUNE, release, envolvente → nivel, envolvente → filtro, filtro, resonancia, velocidad del LFO y efecto. Desde RC4, Shift + knob = el "
       "destino de ese knob (cualquiera de los 33 parámetros, en el color de su página; Clear mantenido y luego Shift + knob = el de fábrica); Record "
       "mantenido + paso = foto de los valores en ese paso.",
       ("Seq. knobs", "Knobs secuen."),
       knobs8("TUNE", "Release", ("Env → level", "Env → nivel"), ("Env → filter", "Env → filtro"), ("Filter", "Filtro"), ("Resonance", "Resonancia"),
              ("LFO speed", "Veloc. LFO"), ("Effect", "Efecto")), page=4),
    kp("Non-sequenceable knobs (since RC4; Shift + pad 4 in the RCs, Shift + pad 1 in Beta 5.56; pad 4 pink while they are on the knobs): eight knobs "
       "with an assignable destination that are not recorded, by default attack, decay, sustain, SHAPE, LFO → filter, envelope → pitch, MIX OSC 1 / 2 "
       "and VCA gain; Shift + knob = the destination, as on the sequenceable page.",
       "Knobs no secuenciables (desde RC4; Shift + pad 4 en las RC, Shift + pad 1 en la Beta 5.56; el pad 4 en rosa mientras están en los knobs): ocho "
       "knobs de destino asignable que no se graban, de fábrica ataque, decay, sustain, SHAPE, LFO → filtro, envolvente → tono, MIX OSC 1 / 2 y gain "
       "del VCA; Shift + knob = el destino, como en la página secuenciable.",
       ("Non-seq. knobs", "No secuen."),
       knobs8(("Attack", "Ataque"), "Decay", "Sustain", "SHAPE", ("LFO → filter", "LFO → filtro"), ("Env → pitch", "Env → tono"), "MIX 1 / 2",
              ("VCA gain", "Gain del VCA")), page=0, extra={4: P("pink", "Non-seq.", "No\nsecuen.")}),
    kp("Page 5, modulation: K1-K4 = the envelope's attack, decay, sustain and release; K5-K8 = LFO speed, LFO → filter, LFO → level and LFO → pitch. "
       "Shift + K8 = the LFO's shape (since RC2): reverse saw (blue), saw (magenta), triangle (green, the default since RC2.02), square (red), sine "
       "(teal), sample & hold (white), slewed sample & hold (violet).",
       "Página 5, modulación: K1-K4 = ataque, decay, sustain y release de la envolvente; K5-K8 = velocidad del LFO, LFO → filtro, LFO → nivel y LFO → "
       "tono. Shift + K8 = la forma del LFO (desde RC2): diente de sierra inverso (azul), diente de sierra (magenta), triángulo (verde, la de fábrica "
       "desde RC2.02), cuadrada (rojo), seno (verde azulado), sample & hold (blanco), sample & hold suavizado (violeta).",
       ("Modulation", "Modulación"),
       knobs8(("Attack", "Ataque"), "Decay", "Sustain", "Release", ("LFO speed", "Veloc. LFO"), ("LFO → filter", "LFO → filtro"),
              ("LFO → level", "LFO → nivel"), ("LFO → pitch", "LFO → tono")), page=5),
]

_K_MX = knobs8("Velocity", ("Note", "Nota"), ("Random", "Azar"), "LFO 2", ("Envelope 2", "Envolvente 2"), ("Drum hit", "Golpe drum"),
               ("Pattern position", "Posición patrón"), ("Stepped random", "Azar por pasos"))
_MX_SHOW = {**{9 + k: D("amber", f"K{k + 1}") for k in range(8)}, 13: P("amber", "K5\nFilter", "K5\nFiltro"),
            **{17 + k: D("amber", f"Sh+K{k + 1}") for k in range(8) if k != 6}}
V["midi-matriz"] = [
    MAP("Mod matrix (since RC2.02; pad 6, light blue): the eight knobs are sources — K1 velocity, K2 the note, K3 random (a new value each note), K4 LFO "
        "2, K5 envelope 2, K6 a drum hit, K7 the pattern position, K8 stepped random. Each knob's position is its destination and amount: fully left = "
        "off; turning right walks the engine's 33 parameters, one stretch each, the amount growing inside it; the LED in the destination page's "
        "colour, brighter = more. Clear + knob = off; Clear + pad 6 = all off.",
        "Matriz de modulación (desde RC2.02; pad 6, azul claro): los ocho knobs son fuentes — K1 velocity, K2 la nota, K3 azar (un valor nuevo en cada "
        "nota), K4 LFO 2, K5 envolvente 2, K6 golpe de un drum, K7 la posición en el patrón, K8 azar por pasos. La posición de cada knob es su destino y "
        "su cantidad: a la izquierda del todo = apagado; girando a la derecha recorre los 33 parámetros del motor, un tramo cada uno, con la cantidad "
        "creciendo dentro; el LED en el color de la página del destino, más brillo = más cantidad. Clear + knob = apagado; Clear + pad 6 = todas apagadas.",
        ("Mod matrix", "Matriz"),
        pads=preset(page=6, patches="calm"), knobs=_K_MX, buttons=MIDI_BTN),
    MAP("The matrix with Shift: K4 = LFO 2's shape × rate (triangle green, saw magenta, square red, sample & hold white, slewed violet; since RC4 the left "
        "half of each one synced to the tempo), K5 = envelope 2's attack × decay, K6 = which drum (Drum 1-4: orange, yellow, violet, teal) × its decay, "
        "K8 = every how many steps (1, 2, 4, 8, 16). Clear + Shift + knob = its parameter back to the default.",
        "La matriz con Shift: K4 = forma × velocidad del LFO 2 (triángulo verde, diente de sierra magenta, cuadrada rojo, sample & hold blanco, suavizado "
        "violeta; desde RC4 la mitad izquierda de cada una a tempo), K5 = ataque × caída de la envolvente 2, K6 = qué drum (Drum 1-4: naranja, "
        "amarillo, violeta, verde azulado) × su caída, K8 = cada cuántos pasos (1, 2, 4, 8, 16). Clear + Shift + knob = su parámetro al valor inicial.",
        ("Matrix + Shift", "Matriz + Shift"),
        pads=preset(page=6, patches="calm"),
        knobs={4: K("Shape × rate", "Forma × veloc."), 5: K("Attack × decay", "Ataque × caída"), 6: K("Drum × decay", "Drum × caída"),
               8: K("Every N steps", "Cada N pasos")},
        buttons={**MIDI_BTN, "Shift": "grey"}),
    MAP("While a source turns (and 1.5 s after) the pads show where its destination lives — here K1 (velocity) → the filter: page 1's pad bright, pads "
        "9-16 = that page's K1-K8 and 17-24 = its Shift + K1-K8 (dim = has a parameter, bright = the destination); K1's LED in the page's colour "
        "(amber), brighter = more. Meanwhile pads 9-24 load no patches.",
        "Mientras gira una fuente (y 1,5 s después) los pads enseñan dónde vive su destino — aquí K1 (velocity) → el filtro: el pad de la página 1 "
        "brillante, pads 9-16 = los K1-K8 de esa página y 17-24 = sus Shift + K1-K8 (tenue = tiene parámetro, brillante = el destino); el LED de K1 en el "
        "color de la página (ámbar), más brillo = más cantidad. Mientras, los pads 9-24 no cargan patches.",
        ("Matrix: target", "Matriz: destino"),
        pads={**preset(page=6, patches=False), 1: P("amber", "VCA\nVCF"), **_MX_SHOW}, knobs=_K_MX, buttons=MIDI_BTN, kcol={1: "amber"}),
]

_FM_PAD = {7: P("violet", "FM\npage", "Página\nFM"), 8: D("white", "Starter\nsounds", "Sonidos\npartida")}
_ALG_COL = ["white"] * 8 + ["red"] * 4 + ["teal"] * 2 + ["green"] * 2
_STARTERS = [("white", "Piano", "Piano"), ("white", "E-piano", "E-piano"), ("white", "Organ", "Órgano"), ("violet", "Pluck", "Pluck"),
             ("violet", "Harp", "Arpa"), ("violet", "Marimba", "Marimba"), ("amber", "Bass", "Bajo"), ("teal", "Bell", "Campana"),
             ("green", "Strings", "Cuerdas"), ("green", "Pad", "Pad"), ("sky", "Flute", "Flauta"), ("sky", "Clarinet", "Clarin."), ("sky", "Brass", "Metales"),
             ("orange", "Kick", "Bombo"), ("orange", "Snare", "Caja"), ("orange", "Hi-hat", "Hi-hat")]
_FM_BASE = dict(page=0, engine=("violet", "Engine", "Motor"), osc2=False)
V["midi-fm"] = [
    MAP("4-operator FM (since RC4, in the RCs; pad 24 of the engine row, violet; pad 7 = its page): K1-K4 = the ratios of operators 1-4 (green whole, "
        "light blue and a half, teal inharmonic; the clicks after each exact ratio detune it), K5-K8 = their levels (a carrier's loudness, how much a "
        "modulator modulates). Pad 7 held = the 16 algorithms, pad 8 held = 16 starter sounds; Clear + pad 7 = a playable voice of the algorithm.",
        "FM de 4 operadores (desde RC4, en las RC; pad 24 de la fila de motores, violeta; pad 7 = su página): K1-K4 = los ratios de los operadores 1-4 "
        "(verde entero, azul claro y medio, verde azulado inarmónico; los clics tras cada ratio exacto lo desafinan), K5-K8 = sus niveles (el volumen "
        "de un portador, cuánto modula un modulador). Pad 7 mantenido = los 16 algoritmos, pad 8 mantenido = 16 sonidos de partida; Clear + pad 7 = una "
        "voz tocable del algoritmo.",
        ("4-op FM", "FM 4 op"),
        pads=preset(**_FM_BASE, extra=_FM_PAD, patches="calm"),
        knobs={**{k: K(f"Ratio {k}") for k in range(1, 5)}, **{k + 4: K(f"Level {k}", f"Nivel {k}") for k in range(1, 5)}}, buttons=MIDI_BTN,
        kcol={1: "green", 2: "green", 3: "green", 4: "green", 5: "blue", 6: "blue", 7: "blue", 8: "blue"}),
    MAP("4-operator FM with Shift: K1-K4 = each operator's envelope: centre = attack 0, right = its attack (light blue), left = percussive with its own "
        "decay (red); K5 = the algorithm (16, in its family's colour), K6 = feedback (magenta), K7 = noise (white), K8 = release (amber; longer the "
        "harder the note).",
        "FM de 4 operadores con Shift: K1-K4 = la envolvente de cada operador: centro = ataque 0, derecha = su ataque (azul claro), izquierda = "
        "percusivo con su propio decay (rojo); K5 = el algoritmo (16, en el color de su familia), K6 = feedback (magenta), K7 = ruido (blanco), K8 = "
        "release (ámbar; más largo cuanto más fuerte la nota).",
        ("4-op FM + Shift", "FM 4 op + Shift"),
        pads=preset(**_FM_BASE, extra=_FM_PAD, patches="calm"),
        knobs={**{k: K(f"Attack / decay {k}", f"Ataque / decay {k}") for k in range(1, 5)}, 5: K("Algorithm", "Algoritmo"), 6: K("Feedback"),
               7: K("Noise", "Ruido"), 8: K("Release")},
        buttons={**MIDI_BTN, "Shift": "grey"},
        kcol={1: "sky", 2: "sky", 3: "sky", 4: "sky", 5: "white", 6: "magenta", 7: "white", 8: "amber"}),
    MAP("Pad 7 held: the 16 algorithms on pads 9-24, in their family's colour (classic white, percussive red, bells teal, strings green), the current one "
        "bright; press one = chosen, and the tonic sounds while held (Shift + pad: silent). Letting go of pad 7 brings the patches back.",
        "Pad 7 mantenido: los 16 algoritmos en los pads 9-24, en el color de su familia (clásicos blanco, percusivos rojo, campanas verde azulado, "
        "cuerdas verde), el actual brillante; pulsa uno = elegido, y suena la tónica mientras lo mantienes (Shift + pad: sin sonar). Al soltar el pad 7 "
        "vuelven los patches.",
        ("Algorithms", "Algoritmos"),
        pads={**preset(**_FM_BASE, patches=False), 7: P("violet", "Held", "Mantenido"), 8: _FM_PAD[8],
              **{9 + i: P(c, str(i + 1), None, i != 0) for i, c in enumerate(_ALG_COL)}},
        buttons=MIDI_BTN),
    MAP("Pad 8 held (since RC4): 16 starter instruments in their family's colour — keys white, plucked violet, bass amber, bell teal, strings and pad "
        "green, winds light blue, drums orange; press one = it loads whole (algorithm, ratios, levels, envelopes) and the tonic sounds; the one "
        "matching the track bright.",
        "Pad 8 mantenido (desde RC4): 16 instrumentos de partida en el color de su familia — teclados blanco, pulsados violeta, bajo ámbar, campana verde "
        "azulado, cuerdas y pad verde, vientos azul claro, percusión naranja; pulsa uno = se carga entero (algoritmo, ratios, niveles, envolventes) y "
        "suena la tónica; el que coincide con la pista, brillante.",
        ("Starter sounds", "Sonidos partida"),
        pads={**preset(**_FM_BASE, patches=False), 7: _FM_PAD[7], 8: P("white", "Held", "Mantenido"),
              **{9 + i: P(c, en, es, True) for i, (c, en, es) in enumerate(_STARTERS)}},
        buttons=MIDI_BTN),
]

_FM8_PAGE = {1: D("yellow", "Seq.\nknobs", "Knobs\nsecuen."), 2: D("green", "OSC 1"), 3: D("violet", "PEG"), 4: D("amber", "VCA\nVCF"),
             5: D("magenta", "Mod."), 6: D("sky", "Matrix", "Matriz"), 7: D("violet", "Map", "Mapa"), 8: D("white", "Instr."),
             9: P("green", "Op 1"), 10: D("sky", "Op 2"), 11: D("sky", "Op 3"), 12: D("sky", "Op 4"),
             **{n: P(c, en, es, n != 24) for n, (c, en, es) in _ROW_BETA.items()},
             26: D("magenta", "Flip"), 27: P("violet", "Engine", "Motor"), 29: D("amber", "Order", "Orden"), 30: D("violet", "Step\ndrum"),
             32: P("magenta", "Voice\nmode", "Modo\nde voz")}
_INST1 = [("orange", "E.Piano"), ("orange", "Bright\nEP"), ("orange", "Clav"), ("orange", "Organ"), ("orange", "Marimba"), ("orange", "Vibes"),
          ("blue", "FM\nBass"), ("blue", "Synth\nBass"), ("blue", "Deep\nBass"), ("red", "Brass"), ("red", "Sync\nLead"), ("red", "Flute"),
          ("green", "Strings"), ("green", "Warm\nPad"), ("green", "Choir"), ("green", "Glass\nPad"), ("yellow", "Harp"), ("yellow", "Koto"),
          ("yellow", "Nylon"), ("white", "Kick"), ("white", "Snare"), ("white", "Hi-Hat"), ("violet", "Tubular\nBell"), ("violet", "Space\nSweep")]
_INST2 = [("orange", "Grand\nPiano"), ("orange", "Mellow\nPiano"), ("orange", "Honky-\nTonk"), ("orange", "Tine\nPiano"), ("orange", "Toy\nPiano"),
          ("green", "Slow\nStrings"), ("green", "Ensem-\nble"), ("green", "Cello"), ("green", "Violin"), ("yellow", "Pizzi-\ncato"),
          ("green", "String\nSwell"), ("teal", "Clari-\nnet"), ("teal", "Oboe"), ("teal", "Bassoon"), ("teal", "Alto\nSax"), ("teal", "French\nHorn"),
          ("teal", "Trumpet"), ("teal", "Pan\nFlute"), ("teal", "Recorder"), ("teal", "Harmo-\nnica"), ("orange", "Cathe-\ndral"),
          ("green", "Bowed\nGlass"), ("green", "Evolving\nPad"), ("violet", "Long\nBell")]
# the algorithm map of the Tubular Bell instrument (the DX7's algorithm 5), as the device lays it out: (pad, operator, colour, bright)
_MAP_TB = [(9, 6, "violet", False), (10, 5, "green", False), (12, 4, "orange", True), (13, 3, "green", True), (15, 2, "teal", True), (16, 1, "green", True)]
V["midi-fm8"] = [
    MAP("Beta 5.56 only: the 8-operator FM page (pad 7 with the engine row closed): pads 9-16 = operators 1-8 (carriers green, modulators light blue, "
        "the picked one bright; here the four-operator stack), pad 3 = the pitch envelope, pads 17-24 = the engine row; K1 ratio, K2 fine, K3 output "
        "level, K4 velocity sensitivity, K5-K8 the envelope's rates R1-R4. Pad 7 = the algorithm map, Shift + pad 7 held = the 56 algorithms, pad 8 held "
        "= the instruments.",
        "Solo Beta 5.56: la página del FM de 8 operadores (pad 7 con la fila de motores cerrada): pads 9-16 = los operadores 1-8 (portadores verdes, "
        "moduladores azul claro, el elegido brillante; aquí la pila de cuatro), pad 3 = la envolvente de pitch, pads 17-24 = la fila de motores; K1 "
        "ratio, K2 fino, K3 nivel de salida, K4 sensibilidad a la velocity, K5-K8 los rates R1-R4 de la envolvente. Pad 7 = el mapa del algoritmo, Shift "
        "+ pad 7 mantenido = los 56 algoritmos, pad 8 mantenido = los instrumentos.",
        ("8-op FM", "FM 8 op"),
        pads=_FM8_PAGE,
        knobs=knobs8("Ratio", ("Fine", "Fino"), ("Level", "Nivel"), "Velocity", "Rate 1", "Rate 2", "Rate 3", "Rate 4"), buttons=MIDI_BTN),
    MAP("Beta 5.56 only, the FM page with Shift: K1 = the algorithm (56, for the whole engine; the pads show them for 1.5 s), K2 = feedback, K3 = rate "
        "scaling (higher notes faster), K4 = level scaling (centre = none), K5-K8 = the envelope's levels L1-L4. The envelope rises at R1 to L1, R2 to "
        "L2, R3 to L3, stays at L3 while the note is held and on release goes at R4 to L4.",
        "Solo Beta 5.56, la página FM con Shift: K1 = el algoritmo (56, de todo el motor; los pads los enseñan 1,5 s), K2 = feedback, K3 = rate scaling "
        "(las notas agudas más rápidas), K4 = level scaling (centro = ninguno), K5-K8 = los niveles L1-L4 de la envolvente. La envolvente sube por R1 a "
        "L1, R2 a L2, R3 a L3, se queda en L3 mientras la nota sigue y al soltar va por R4 a L4.",
        ("8-op FM + Shift", "FM 8 op + Shift"),
        pads=_FM8_PAGE,
        knobs=knobs8(("Algorithm", "Algoritmo"), "Feedback", "Rate scaling", "Level scaling", ("Level 1", "Nivel 1"), ("Level 2", "Nivel 2"),
                     ("Level 3", "Nivel 3"), ("Level 4", "Nivel 4")),
        buttons={**MIDI_BTN, "Shift": "grey"}),
    MAP("Beta 5.56 only, the pitch envelope (pad 3, violet, bright while edited — like a ninth operator): K1 transpose (24 = none), K3 noise, K4 the "
        "noise's operator, K5-K8 rates R1-R4; with Shift K1 / K2 = algorithm / feedback and K5-K8 = levels L1-L4 (50 = no shift).",
        "Solo Beta 5.56, la envolvente de pitch (pad 3, violeta, brillante mientras la editas — como un noveno operador): K1 transposición (24 = "
        "ninguna), K3 ruido, K4 el operador del ruido, K5-K8 rates R1-R4; con Shift K1 / K2 = algoritmo / feedback y K5-K8 = niveles L1-L4 (50 = sin "
        "desplazamiento).",
        ("Pitch envelope", "Envolvente pitch"),
        pads={**_FM8_PAGE, 3: P("violet", "PEG"), 9: D("green", "Op 1")},
        knobs=knobs8(("Transpose", "Transposición"), None, ("Noise", "Ruido"), ("Noise op.", "Op. del ruido"), "Rate 1", "Rate 2", "Rate 3", "Rate 4"),
        buttons=MIDI_BTN),
    MAP("Beta 5.56 only: the algorithm map (a tap on pad 7), here of the Tubular Bell instrument (the DX7's algorithm 5): each row reads left to right — "
        "a wave modulates the one on its right and the last on the right is a carrier, the one you hear; a dark gap = no interaction. Colour = the "
        "ratio (green whole, teal x.5, orange other, red fixed), violet = the feedback operator; dim = level under half. A tap picks an operator, Shift "
        "+ operator mutes it, one held + a tap on another = link or unlink them (an own algorithm).",
        "Solo Beta 5.56: el mapa del algoritmo (un toque al pad 7), aquí del instrumento Tubular Bell (el algoritmo 5 del DX7): cada fila se lee de "
        "izquierda a derecha — una onda modula a la de su derecha y la última de la derecha es una portadora, la que se oye; un hueco oscuro = no "
        "interactúan. Color = el ratio (verde entero, verde azulado x,5, naranja otro, rojo fijo), violeta = el operador con feedback; tenue = nivel por "
        "debajo de la mitad. Un toque elige un operador, Shift + operador lo calla, uno mantenido + un toque a otro = enlazarlos o desenlazarlos (un "
        "algoritmo propio).",
        ("Algorithm map", "Mapa algoritmo"),
        pads={**{n: v for n, v in _FM8_PAGE.items() if n <= 8}, 7: P("violet", "Map", "Mapa"),
              **{n: P(c, f"Op {o}", None, not b) for n, o, c, b in _MAP_TB}},
        knobs=knobs8("Ratio", ("Fine", "Fino"), ("Level", "Nivel"), "Velocity", "Rate 1", "Rate 2", "Rate 3", "Rate 4"), buttons=MIDI_BTN),
    MAP("Beta 5.56 only, pad 8 held: 24 instruments in their type's colour (keys orange, basses blue, leads and brass red, pads and strings green, plucks "
        "yellow, percussion white, bells and fx violet), the loaded one bright; press one = loaded, and it sounds. Loading one also sets page 4 and "
        "Shift + pad 4 to the knobs that suit its family.",
        "Solo Beta 5.56, pad 8 mantenido: 24 instrumentos en el color de su tipo (teclados naranja, bajos azul, leads y metales rojo, pads y cuerdas "
        "verde, punteados amarillo, percusión blanco, campanas y efectos violeta), el cargado brillante; pulsa uno = se carga y suena. Al cargar uno, la "
        "página 4 y Shift + pad 4 pasan a los knobs que convienen a su familia.",
        ("Instruments 1", "Instrumentos 1"),
        pads={**{n: v for n, v in _FM8_PAGE.items() if n <= 8}, 8: P("white", "Held", "Mantenido"),
              **{9 + i: P(c, n, None, i != 0) for i, (c, n) in enumerate(_INST1)}},
        buttons={**MIDI_BTN, "Oct ▼": "white"}),
    MAP("Beta 5.56 only, pad 8 held + Octave ▼ = the second page: pianos orange, strings green (Pizzicato yellow), winds teal and four long sounds; "
        "Octave ▲ goes back.",
        "Solo Beta 5.56, pad 8 mantenido + Octave ▼ = la segunda página: pianos naranja, cuerdas verde (Pizzicato amarillo), vientos verde azulado y "
        "cuatro sonidos largos; Octave ▲ vuelve.",
        ("Instruments 2", "Instrumentos 2"),
        pads={**{n: v for n, v in _FM8_PAGE.items() if n <= 8}, 8: P("white", "Held", "Mantenido"),
              **{9 + i: P(c, n, None, True) for i, (c, n) in enumerate(_INST2)}},
        buttons={"MIDI 1": "blue", "Preset": "blue", "Oct ▲": "white"}),
]

V["midi-cc"] = [MAP(
    "CC editor of the MIDI macros (pad 25, magenta; shown with the track's engine off, pad 27 grey): move a knob to pick it (its number is drawn on "
    "the pads); Octave ▼ / ▲ = next / previous field (number, start, end; for an NRPN also MSB and LSB); turn the knob to change the field; pad 26 "
    "(or Octave ▼ up to the save step, when pad 26 and Save blink) saves and goes back to the Preset view; pad 25, a template pad or a view button "
    "discards.",
    "Editor de CC de los macros MIDI (pad 25, magenta; con el motor de la pista apagado, pad 27 gris): mueve un knob para elegirlo (su número se dibuja "
    "con los pads); Octave ▼ / ▲ = campo siguiente / anterior (número, inicio, fin; en un NRPN también MSB y LSB); gira el knob para cambiar el campo; "
    "el pad 26 (u Octave ▼ hasta el paso de guardar, cuando parpadean el pad 26 y Save) guarda y vuelve a la vista Preset; el pad 25, un pad de "
    "plantilla o un botón de vista descarta.",
    ("CC editor", "Editor de CC"),
    pads={25: P("magenta", "CC\nedit", "Editor\nCC"), 26: D("green", "Save", "Guardar"), 27: D("white", "Engine\noff", "Motor\napagado")},
    knobs={k: K("CC / NRPN") for k in range(1, 9)},
    buttons={"MIDI 1": "blue", "Preset": "blue"})]


def _sd_steps():
    out = {}
    for n in range(1, 17):
        c = "sky" if (n - 1) // 2 % 2 == 0 else "orange"
        out[n] = P(c, "", None, n not in (1, 5, 9, 13))
    return out


_SD_DEST = [("green", "Pitch", "Tono"), ("teal", "OSC 2", "OSC 2"), ("yellow", "WAVE", "WAVE"), ("magenta", "FM", "FM"), ("sky", "MIX", "MIX"),
            ("amber", "Env F", "Env F"), ("orange", "SHAPE", "SHAPE"), ("violet", "Decay", "Decay")]
V["step-drummer"] = [
    MAP("Step-drummer of MIDI 1 (pad 30 of the Preset view, violet), pitch page: pads 1-16 = the steps by pairs (alternating colours; bright = has a "
        "note, white = playing; Shift + pad = set / clear a note), pads 17-24 = the pitch row's destination (pitch, OSC 2, WAVE, FM, MIX, envelope → "
        "filter, SHAPE, decay), K1-K8 = the 8 step pairs (centre = no change; since RC2 brighter = further from it). Octave ▲ / ▼ = pitch / velocity "
        "page; 1-16 / 17-32 = the other half; pad 32 = the pitch-vel toggle (since RC2). With Record, touching a step records it.",
        "Step-drummer de MIDI 1 (pad 30 de la vista Preset, violeta), página pitch: pads 1-16 = los pasos por pares (colores alternos; brillante = con "
        "nota, blanco = el que suena; Shift + pad = poner / quitar nota), pads 17-24 = el destino de la fila de pitch (tono, OSC 2, WAVE, FM, MIX, "
        "envolvente → filtro, SHAPE, decay), K1-K8 = los 8 pares de pasos (centro = sin cambio; desde RC2 más brillo = más lejos de él). Octave ▲ / ▼ = "
        "página pitch / velocity; 1-16 / 17-32 = la otra mitad; pad 32 = el toggle pitch-vel (desde RC2). Con Record, tocar un paso lo graba.",
        ("Step-drummer", "Step-drummer"),
        pads={**_sd_steps(), **{17 + i: P(c, en, es, i != 0) for i, (c, en, es) in enumerate(_SD_DEST)}, 26: D("magenta", ""), 27: P("green", "Engine", "Motor"),
              28: D("green", ""), 29: D("amber", ""), 30: P("violet", "Step\ndrum"), 32: D("green", "Pitch-\nvel")},
        knobs={k: K(f"Pair {k}", f"Par {k}") for k in range(1, 9)},
        buttons={"MIDI 1": "blue", "Preset": "blue", "Oct ▲": "violet", "Oct ▼": ("violet", True), "1-16 / 17-32": ("violet", True)}),
    MAP("With the FX sequencer engine (pad 27 blue), each knob picks the Master FX bottom-row slot its pair of steps triggers: none, pads 26-30, pad 31 "
        "(the gesture) and random (white, since RC2); it moves slowly and its LED shows the effect's colour. A slot with no effect plays the effect at "
        "the top of its column (since RC4); the track sends its MIDI as always.",
        "Con el motor secuenciador de efectos (pad 27 azul), cada knob elige el hueco de la fila inferior de Master FX que dispara su par de pasos: nada, "
        "pads 26-30, pad 31 (el gesto) y random (blanco, desde RC2); avanza despacio y su LED enseña el color del efecto. Un hueco sin efecto toca el "
        "efecto de arriba de su columna (desde RC4); la pista manda su MIDI como siempre.",
        ("FX sequencer", "Secuenciador FX"),
        pads={**_sd_steps(), 27: P("blue", "FX seq", "Sec. FX"), 30: P("violet", "Step\ndrum")},
        knobs=knobs8(("Pad 26", "Pad 26"), ("None", "Nada"), ("Pad 28", "Pad 28"), ("Pad 31", "Pad 31"), "Random", ("Pad 27", "Pad 27"),
                     ("None", "Nada"), ("Pad 30", "Pad 30")),
        buttons={"MIDI 1": "blue", "Preset": "blue", "Play": "green"},
        kcol={1: "orange", 2: "none", 3: "blue", 4: "teal", 5: "white", 6: "pine", 7: "none", 8: "magenta"}),
]

V["midi-muestra"] = [MAP(
    "Sample picker (since RC2; MIDI 1 / 2 with the sample engine, Note twice): pads 17-32 = 16 of the pack's 64 samples (Octave = the page; teal = "
    "the track's sample, a touch picks it and it sounds; since RC4 Shift + sample = silently, Shift + the chosen one = pick the second, stereo sample); "
    "pads 1-16 = the steps: teal = a note, peach = a note with a sample flip, violet = a flip without a note (since RC4), white = playing. Hold a step + "
    "touch a sample = its flip; Clear + step = remove it; 1-16 / 17-32 = the other half.",
    "Selector de samples (desde RC2; MIDI 1 / 2 con el motor muestra, Note dos veces): pads 17-32 = 16 de los 64 samples del pack (Octave = la página; "
    "verde azulado = el sample de la pista, un toque lo elige y suena; desde RC4 Shift + sample = sin sonar, Shift + el elegido = elegir el segundo, "
    "sample estéreo); pads 1-16 = los pasos: verde azulado = una nota, melocotón = una nota con sample flip, violeta = un flip sin nota (desde RC4), "
    "blanco = el que suena. Mantén un paso + toca un sample = su flip; Clear + paso = quitarlo; 1-16 / 17-32 = la otra mitad.",
    ("Sample picker", "Selector"),
    pads={**steps("teal"), 1: P("white", "Playing", "Suena"), 3: P("teal", "Note", "Nota"), 5: P("peach", "Flip"), 9: P("teal", "Note", "Nota"),
          12: P("violet", "Flip\nonly", "Solo\nflip"), 17: P("teal", "S1"), **{17 + i: D("white", f"S{i + 1}") for i in range(1, 16)}},
    buttons={"MIDI 1": "blue", "Note": "amber", "Oct ▼": "white", "1-16 / 17-32": ("white", True)})]

# ===== 4. Pattern Settings
_RATES = ["1/4", "1/4T", "1/8", "1/8T", "1/16", "1/16T", "1/32", "1/32T"]
V["pattern-settings"] = [
    MAP("Pattern Settings (MIDI 1): pads 1-16 = first / last step, 17-24 = sync rate, 29-32 = direction (as on the original); pad 25 = the probability "
        "view in mode 2 (dynamics and random-mutate; Clear + 25 clears them), 26 = Nudge (blue: the selected range's content a step back, Shift + 26 a "
        "step forward), 27 / 28 = fractal / deconstructed order (exclusive with 29-32; saved with the pattern).",
        "Pattern Settings (MIDI 1): pads 1-16 = primer / último paso, 17-24 = sync rate, 29-32 = dirección (como en el original); pad 25 = la vista de "
        "probabilidad en modo 2 (dinámicas y random-mutate; Clear + 25 las borra), 26 = Nudge (azul: el contenido del tramo elegido un paso atrás, "
        "Shift + 26 un paso adelante), 27 / 28 = orden fractal / deconstruido (excluyentes con 29-32; se guardan con el patrón).",
        ("Pattern Settings", "Pattern Settings"),
        pads={**steps("sky"), 1: P("sky", "First", "Primero"), 16: P("yellow", "Last", "Último"),
              **{17 + i: P("amber", r, None, i != 4) for i, r in enumerate(_RATES)}, 25: P("peach", "Mode 2", "Modo 2"), 26: P("blue", "Nudge"),
              27: D("pink", "Fractal"), 28: D("pink", "Decon.", "Decons."), 29: P("pink", "Fwd", "Adel."), 30: D("pink", "Back", "Atrás"),
              31: D("pink", "Ping\npong"), 32: D("pink", "Random", "Azar")},
        buttons={"MIDI 1": "blue", "Pattern Settings": "blue"}),
    MAP("With Shift held (since RC2): Shift + pad 25 = the pattern's arpeggiator on / off (green), Shift + 27-32 = the arpeggio's order (fractal, "
        "deconstructed, up, down, ping-pong, random), Shift + 17-24 = its resolution (the chosen ones green). Since RC4, with the arpeggiator on, Shift + "
        "pads 1-16 = its modifiers: octaves (sand), when the octave moves (sky blue), groove (amber), reset (pink), the chosen option bright. Shift + pad "
        "26 = Nudge one step forward.",
        "Con Shift pulsado (desde RC2): Shift + pad 25 = el arpegiador del patrón sí / no (verde), Shift + 27-32 = el orden del arpegio (fractal, "
        "deconstruido, arriba, abajo, ping-pong, aleatorio), Shift + 17-24 = su resolución (lo elegido en verde). Desde RC4, con el arpegiador "
        "encendido, Shift + pads 1-16 = sus modificadores: octavas (arena), cuándo cambia la octava (azul cielo), groove (ámbar), reinicio (rosa), la "
        "opción elegida brillante. Shift + pad 26 = Nudge un paso adelante.",
        ("Arpeggiator", "Arpegiador"),
        pads={1: P("sand", "No\noct.", "Sin\noct."), 2: D("sand", "+1 oct"), 3: D("sand", "+1 / −1"), 4: D("sand", "+2 / −1"),
              5: P("sky", "Each\npass", "Cada\nvuelta"), 6: D("sky", "Each\nnote", "Cada\nnota"), 7: D("sky", "Every\n3", "Cada\n3"),
              8: D("sky", "Every\n4", "Cada\n4"), 9: P("amber", "No\ngroove", "Sin\ngroove"), 10: D("amber", "Dotted", "Puntillo"), 11: D("amber", "Swing"),
              12: D("amber", "Twice", "Dos\nveces"), 13: P("pink", "No\nreset", "Sin\nreinicio"), 14: D("pink", "+1"), 15: D("pink", "+3"), 16: D("pink", "+5"),
              **{17 + i: D("amber", r) for i, r in enumerate(_RATES)}, 25: P("green", "Arp\non", "Arp\nsí"), 26: P("blue", "Nudge\nfwd", "Nudge\nadel."),
              27: D("pink", "Fractal"), 28: D("pink", "Decon.", "Decons."), 29: P("green", "Up", "Arriba"), 30: D("pink", "Down", "Abajo"),
              31: D("pink", "Ping\npong"), 32: D("pink", "Random", "Azar")},
        buttons={"MIDI 1": "blue", "Pattern Settings": "blue", "Shift": "grey"}),
]

V["micropasos"] = [MAP(
    "Micro Step view (Gate twice, note tracks): pads 1-16 = the steps (the chosen one bright), 17-22 = its 6 micro steps, 24 = Tie, 25-30 = the "
    "step's notes (as on the original); pad 31 = fixed length (blue = on; with both off it opens a selector, pads 17-32 = 1-16 steps), pad 32 = gate "
    "by holding (green = on: how long you hold the pads is the note's gate). Since RC2; with one on, pressing it again turns it off, pressing the "
    "other swaps them.",
    "Vista Micro Step (Gate dos veces, pistas de notas): pads 1-16 = los pasos (el elegido brillante), 17-22 = sus 6 micropasos, 24 = Tie, 25-30 = "
    "las notas del paso (como en el original); pad 31 = longitud fija (azul = encendida; con los dos apagados abre un selector, pads 17-32 = 1-16 "
    "pasos), pad 32 = gate por pulsación (verde = encendido: lo que mantienes los pads es el gate de la nota). Desde RC2; con uno encendido, pulsarlo "
    "otra vez lo apaga, pulsar el otro los cambia.",
    ("Micro Step", "Micro Step"),
    pads={**steps("sky"), 1: P("sky", "Step", "Paso"), 17: P("yellow", "μ1"), **{17 + i: D("sand", f"μ{i + 1}") for i in range(1, 6)},
          24: D("orange", "Tie"), 25: P("blue", "Note", "Nota"), 31: D("white", "Fixed\nlength", "Long.\nfija"), 32: D("white", "Hold\ngate", "Gate\npulsar")},
    buttons={"MIDI 1": "blue", "Gate": "amber"})]

_DYN_RC = [("—", "—"), ("μ ±2", "μ ±2"), ("μ ±2\nv +32", "μ ±2\nv +32"), ("v +32", "v +32"), ("μ −1/+3\nv +32", "μ −1/+3\nv +32"),
           ("μ −1/+3", "μ −1/+3"), ("v ±32", "v ±32"), ("v −32\n/ +64", "v −32\n/ +64")]
_MUT_RC = [("—", "—"), ("Oct\n6%", "Oct\n6%"), ("Scale\n6%", "Escala\n6%"), ("Oct 6%\nScl 6%", "Oct 6%\nEsc 6%"), ("Scale\n12%", "Escala\n12%"),
           ("Oct\n12%", "Oct\n12%"), ("Scale\n25%", "Escala\n25%"), ("Oct 25%\nScl 50%", "Oct 25%\nEsc 50%")]
V["probabilidad"] = [
    MAP("Probability view, mode 1 (Pattern Settings twice): hold a step (pads 1-16) and touch row 3 = its probability (as on the original) or row 4 = "
        "its frequency (since RC2, yellow): the step plays on the last of every n passes (1-8), here 1 of 4. On the drums the same.",
        "Vista de probabilidad, modo 1 (Pattern Settings dos veces): mantén un paso (pads 1-16) y toca la fila 3 = su probabilidad (como en el original) "
        "o la fila 4 = su frecuencia (desde RC2, amarillo): el paso suena en la última de cada n vueltas (1-8), aquí 1 de 4. En los drums igual.",
        ("Probability", "Probabilidad"),
        pads={**steps("sky"), 1: P("sky", "Step", "Paso"), **steps("grey", 8, 17), **{25 + i: D("white", f"1 of {i + 1}", f"1 de {i + 1}") for i in range(8)},
              28: P("yellow", "1 of 4", "1 de 4")},
        buttons={"MIDI 1": "blue", "Pattern Settings": "amber"}),
    MAP("Mode 2 in the RCs (pad 25 of Pattern Settings): row 3 = dynamics (since RC2, green: random micro-step and velocity changes in 8 levels), row 4 "
        "= random-mutate (since RC2, peach: the chance that the step's notes jump an octave or to another note of the scale). With Record and this view "
        "on screen, what sounds is written into the pattern. On the drums, row 4's pads 25-28 mutate the sample.",
        "Modo 2 en las RC (pad 25 de Pattern Settings): fila 3 = dinámicas (desde RC2, verde: cambios al azar de micropasos y velocity en 8 niveles), "
        "fila 4 = random-mutate (desde RC2, melocotón: la probabilidad de que las notas del paso salten una octava o a otra nota de la escala). Con Record "
        "y esta vista en pantalla, lo que suena se escribe en el patrón. En los drums, los pads 25-28 de la fila 4 mutan el sample.",
        ("Mode 2 (RC)", "Modo 2 (RC)"),
        pads={**steps("sky"), 1: P("sky", "Step", "Paso"), **{17 + i: D("white", en, es) for i, (en, es) in enumerate(_DYN_RC)},
              19: P("green", *_DYN_RC[2]), **{25 + i: D("peach", en, es) for i, (en, es) in enumerate(_MUT_RC)}, 28: P("peach", *_MUT_RC[3])},
        buttons={"MIDI 1": "blue", "Pattern Settings": "amber"}),
    MAP("Beta 5.56 only, mode 2: one set of pads per step — 17 no note change (white), 18-20 another note of the scale (×1, ×2, ×4; peach), 21 / 22 an "
        "octave up (low / high; sand), 23 / 24 an octave up or down (sand), 25 no dynamics (white), 26 ghost, 27 accent staccato, 28 length (green), 32 "
        "micro steps (teal). Octave ▼ / ▲ = the track's factor (×0, ×1, ×2, ×4, ×8), which multiplies every chance. On the drums: another sample "
        "instead of another note.",
        "Solo Beta 5.56, modo 2: una sola botonera por paso — 17 sin cambio de nota (blanco), 18-20 otra nota de la escala (×1, ×2, ×4; melocotón), 21 "
        "/ 22 una octava arriba (baja / alta; arena), 23 / 24 una octava arriba o abajo (arena), 25 sin dinámicas (blanco), 26 ghost, 27 accent "
        "staccato, 28 longitud (verde), 32 micropasos (verde azulado). Octave ▼ / ▲ = el factor de la pista (×0, ×1, ×2, ×4, ×8), que multiplica todas "
        "las probabilidades. En los drums: otro sample en lugar de otra nota.",
        ("Mode 2 (Beta)", "Modo 2 (Beta)"),
        pads={**steps("sky"), 1: P("sky", "Step", "Paso"), 17: D("white", "Off", "No"), 18: D("peach", "Note\n×1", "Nota\n×1"), 19: D("peach", "Note\n×2", "Nota\n×2"),
              20: D("peach", "Note\n×4", "Nota\n×4"), 21: D("sand", "Oct ↑\nlow", "Oct ↑\nbaja"), 22: P("sand", "Oct ↑\nhigh", "Oct ↑\nalta"),
              23: D("sand", "Oct ↕\nlow", "Oct ↕\nbaja"), 24: D("sand", "Oct ↕\nhigh", "Oct ↕\nalta"), 25: D("white", "No\ndyn.", "Sin\ndin."),
              26: P("green", "Ghost"), 27: D("green", "Accent\nstacc.", "Acento\nstacc."), 28: D("green", "Length", "Long."), 32: P("teal", "Micro")},
        buttons={"MIDI 1": "blue", "Pattern Settings": "amber", "Oct ▼": "peach", "Oct ▲": "peach"}),
]

# ===== 5. Drums
_K_DRUM = knobs8("Pitch", ("Ring freq.", "Frec. ring"), ("Decay ↔ attack", "Decay ↔ ataque"), ("Env → cutoff", "Env → corte"), ("Filter / EQ", "Filtro / EQ"),
                 ("Resonance", "Resonancia"), ("LFO amount", "Cant. LFO"), ("Dist. / crush", "Dist. / crush"))
V["drum-pista"] = [
    MAP("Drum 1's track view, the knobs (as printed on the panel): K1 pitch, K2 ring mod frequency, K3 decay (left) / attack (right; since RC2), K4 "
        "envelope → cutoff, K5 filter / EQ (the stock tilt EQ by default), K6 resonance, K7 LFO amount (right tremolo; left, since RC4, start scan), K8 "
        "distortion (left of 0: bitcrush). All neutral = the original sound. Clear + Drum 1 = its knobs' automation in the playing pattern erased and all "
        "its knobs to their defaults (since RC2). Pads 1-16 = the drum's steps.",
        "Vista de pista de Drum 1, los knobs (según la serigrafía): K1 pitch, K2 frecuencia del ring mod, K3 decay (izquierda) / ataque (derecha; desde "
        "RC2), K4 envolvente → corte, K5 filtro / EQ (de fábrica el EQ tilt de stock), K6 resonancia, K7 cantidad del LFO (derecha trémolo; izquierda, "
        "desde RC4, scan del inicio), K8 distorsión (a la izquierda de 0: bitcrush). Todo neutro = el sonido original. Clear + Drum 1 = borra la "
        "automatización de sus knobs en el patrón que suena y pone todos sus knobs por defecto (desde RC2). Pads 1-16 = los pasos del drum.",
        ("Drum 1", "Drum 1"),
        pads=steps("orange", label=("Steps", "Pasos")), knobs=_K_DRUM, buttons={"Drum 1": "orange"}),
    MAP("The drum knobs with Shift: K1 pitch envelope amount, K2 ring mod amount, K3 sample start (left) / cut from the end (right; since RC2), K4 "
        "envelope shape, K5 filter mode (the LED's colour: green stock EQ tilt, yellow band pass, magenta notch, teal comb, white DJ; Beta 5.56 skips the "
        "comb), K7 LFO speed (bipolar since RC4: right free, left synced), K8 distortion type (stock, soft, hard, fold).",
        "Los knobs del drum con Shift: K1 cantidad de la envolvente de tono, K2 cantidad del ring mod, K3 inicio del sample (izquierda) / corte desde el "
        "final (derecha; desde RC2), K4 forma de la envolvente, K5 modo de filtro (el color del LED: verde EQ tilt de stock, amarillo paso banda, "
        "magenta notch, verde azulado comb, blanco DJ; la Beta 5.56 se salta el comb), K7 velocidad del LFO (bipolar desde RC4: derecha libre, izquierda "
        "a tempo), K8 tipo de distorsión (stock, suave, dura, plegada).",
        ("Drum 1 + Shift", "Drum 1 + Shift"),
        pads=steps("orange", label=("Steps", "Pasos")),
        knobs=knobs8(("Pitch env.", "Env. de tono"), ("Ring amount", "Cant. ring"), ("Start ↔ cut", "Inicio ↔ corte"), ("Env. shape", "Forma env."),
                     ("Filter mode", "Modo de filtro"), None, ("LFO speed", "Veloc. LFO"), ("Dist. type", "Tipo de dist.")),
        buttons={"Drum 1": "orange", "Shift": "grey"}, kcol={5: "green"}),
    MAP("Stereo pair (since RC4; hold Drum 1 and press Drum 2, the same to undo): Drum 1 plays the left side and drives both — knobs, pattern, level, "
        "sends; Drum 2 plays the next sample on the right and its knobs become deviations: K1 detune (±100 cents), K2 stereo width (white), K3 decay, K4 "
        "envelope → cutoff, K5 filter / EQ, K6 resonance, K7 LFO amount. Drum 2's button pulses in Drum 1's colour; saved with the project.",
        "Pareja estéreo (desde RC4; mantén Drum 1 y pulsa Drum 2, igual para deshacerla): Drum 1 suena a la izquierda y manda en los dos — knobs, patrón, "
        "nivel, envíos; Drum 2 toca el sample siguiente a la derecha y sus knobs pasan a ser desviaciones: K1 desafinación (±100 cents), K2 apertura "
        "estéreo (blanco), K3 decay, K4 envolvente → corte, K5 filtro / EQ, K6 resonancia, K7 cantidad del LFO. El botón de Drum 2 late en el color de "
        "Drum 1; se guarda con el proyecto.",
        ("Stereo pair", "Pareja estéreo"),
        pads=steps("orange", label=("Steps", "Pasos")),
        knobs=knobs8(("Detune", "Desafinación"), ("Stereo width", "Apertura"), "Decay", ("Env → cutoff", "Env → corte"), ("Filter / EQ", "Filtro / EQ"),
                     ("Resonance", "Resonancia"), ("LFO amount", "Cant. LFO"), None),
        buttons={"Drum 1": "orange", "Drum 2": "orange"},
        kcol={1: "orange", 2: "white", 3: "orange", 4: "orange", 5: "orange", 6: "orange", 7: "orange"}),
    MAP("Beta 5.56 only: the drum's automation view (its Velocity view with Shift held, or Velocity again to latch it): steps with automation yellow, "
        "ramp steps dim yellow, marked steps red, the others their colour. Shift + a yellow step = its values on the knobs until Shift is let go; Shift + "
        "another step = mark it (there the pitch, decay, distortion and EQ go back to the project's values); Clear + a step = erase its automation, "
        "keeping the hit.",
        "Solo Beta 5.56: la vista de automatización del drum (su vista Velocity con Shift, o Velocity otra vez para fijarla): los pasos con "
        "automatización en amarillo, los de rampa en amarillo tenue, los marcados en rojo, los demás en su color. Shift + un paso amarillo = sus valores "
        "en los knobs hasta soltar Shift; Shift + otro paso = marcarlo (ahí pitch, decay, distorsión y EQ vuelven a los valores del proyecto); Clear + "
        "paso = borrar su automatización, dejando el golpe.",
        ("Automation", "Automatización"),
        pads={**{n: D("orange") for n in (1, 2, 4, 6, 10, 12, 14)}, 3: P("yellow", "Auto"), 5: P("red", "Mark", "Marca"), 7: D("yellow", "Ramp", "Rampa"),
              8: D("yellow", "Ramp", "Rampa"), 9: P("yellow", "Auto"), 13: P("red", "Mark", "Marca")},
        buttons={"Drum 1": "orange", "Velocity": "orange", "Shift": "grey"}),
]

V["drum-preset"] = [MAP(
    "Drum 1's Preset view: the pads pick the sample (Shift + pad = silently). Clear + pad, then Clear + the same pad = that sample becomes Master FX's "
    "capture (written into the pack when the project is saved, if it fits in the sample memory); Duplicate (lit in this view) + A + B = swap two "
    "samples (A blinks blue), or copy A into another pack (they write to the card: not in the «S» versions nor in the internal memory's pack); Preset "
    "again (since RC2) or Shift + Preset = the chromatic view; with the drum's arpeggiator on, several samples held = the sample arpeggio (since RC2).",
    "Vista Preset de Drum 1: los pads eligen el sample (Shift + pad = sin sonar). Clear + pad y Clear + el mismo pad = ese sample pasa a ser la captura "
    "de Master FX (se escribe en el pack al guardar el proyecto, si cabe en la memoria de samples); Duplicate (encendido en esta vista) + A + B = "
    "intercambiar dos samples (A parpadea en azul), o copiar A a otro pack (escriben en la tarjeta: no en las versiones «S» ni en el pack de la memoria "
    "interna); Preset otra vez (desde RC2) o Shift + Preset = la vista cromática; con el arpegiador del drum encendido, varios samples mantenidos = el "
    "arpegio de samples (desde RC2).",
    ("Drum 1 Preset", "Preset de Drum 1"),
    pads={**steps("orange", 32), 3: P("orange", "Chosen", "Elegido"), 10: P("blue", "A")},
    buttons={"Drum 1": "orange", "Preset": "orange", "Duplicate": "white"})]

_MAJOR = ["C", "D", "E", "F", "G", "A", "B", "C"]
_ROLL = {}
for _d, (_l, _r) in enumerate(((4, 5), (3, 6), (2, 7), (1, 8))):              # drum 1-4: its left / right column
    _c = TRACK[f"Drum {_d + 1}"]
    for _y in range(3):
        _ROLL[_l + 8 * _y] = D(_c, f"μ{_y + 1}")
        _ROLL[_r + 8 * _y] = D(_c, f"μ{_y + 4}")
V["drum-cromatica"] = [
    MAP("Drum 1's chromatic / scale view (Shift + Preset, or Preset again since RC2): three rows of notes in the project's scale and root (here C major; "
        "the roots bright); each pad plays the sample transposed. K1 = pitch offset in semitones, Shift + K1 = fine tuning in cents. Since RC4.02, "
        "while recording each pad records a hit with its pitch on its own step.",
        "Vista cromática / de escala de Drum 1 (Shift + Preset, o Preset otra vez desde RC2): tres filas de notas en la escala y la tónica del proyecto "
        "(aquí C mayor; las tónicas brillantes); cada pad toca el sample transpuesto. K1 = sesgo de tono en semitonos, Shift + K1 = afinación fina en "
        "cents. Desde RC4.02, grabando, cada pad graba un golpe con su tono en su paso.",
        ("Chromatic", "Cromática"),
        pads={9 + 8 * r + i: P("orange", n, None, i not in (0, 7)) for r in range(3) for i, n in enumerate(_MAJOR)},
        knobs={1: K("Pitch offset", "Sesgo de tono")}, buttons={"Drum 1": "orange"}),
    MAP("The drums' expanded Note view (Note twice with a drum): pads 29-32 = Drum 1-4 and pads 25-28 repeat them mirrored (Drum 4 … 1); rows 1-3 = "
        "micro-step rollers (since RC2): each column is the drum of its pad below, its left column micro steps 1-3 and its right one 4-6. While held, "
        "the drum plays on every step at those micro steps — stopped too, at the project's tempo — and with Record they are recorded.",
        "Vista Note ampliada de los drums (Note dos veces con un drum): pads 29-32 = Drum 1-4 y pads 25-28 los repiten en espejo (Drum 4 … 1); filas 1-3 "
        "= rollers de micropasos (desde RC2): cada columna es el drum de su pad de abajo, su columna izquierda los micropasos 1-3 y la derecha los 4-6. "
        "Mientras se mantienen, el drum suena en cada paso en esos micropasos — también parado, al tempo del proyecto — y con Record se graban.",
        ("Drum rollers", "Rollers drums"),
        pads={**_ROLL, **{25 + i: P(TRACK[f"Drum {4 - i}"], f"Drum {4 - i}") for i in range(4)},
              **{29 + i: P(TRACK[f"Drum {i + 1}"], f"Drum {i + 1}") for i in range(4)}},
        buttons={"Drum 1": "orange", "Note": "amber"}),
]

# ===== 6. Master FX, 7. FX, 8. Sidechain
V["master-fx"] = [MAP(
    "Master FX (Mixer twice), here with pad 1 held: pads 1-6 = the effects, hold = on, Shift + pad = latched — Gater, Auto-Filter low / high pass, "
    "Digitise, Phaser, Glitch (since RC2); K1-K4 = the held effect's settings (Gater: division, depth, width, smoothing); pad 7 = play the captured "
    "sample (Shift + 7 = a latched loop), pad 32 = record it; pad 8 = release everything latched; pads 9-24 = the song pointer (steps 1-16: one held = "
    "retrigger, two = a loop between them); 26-30 = assignable slots (hold an effect + touch a slot); 31 = the mechanical gesture (since RC2). Any "
    "other view button leaves.",
    "Master FX (Mixer dos veces), aquí con el pad 1 mantenido: pads 1-6 = los efectos, mantener = activo, Shift + pad = fijado — Gater, Auto-Filter "
    "paso bajo / alto, Digitise, Phaser, Glitch (desde RC2); K1-K4 = los ajustes del efecto mantenido (Gater: división, profundidad, ancho, "
    "suavizado); pad 7 = tocar el sample capturado (Shift + 7 = un bucle enganchado), pad 32 = grabarlo; pad 8 = apagar todo lo fijado; pads 9-24 = el "
    "song pointer (pasos 1-16: uno mantenido = retrigger, dos = un bucle entre ellos); 26-30 = huecos asignables (mantén un efecto + toca un hueco); "
    "31 = el gesto mecánico (desde RC2). Cualquier otro botón de vista sale.",
    ("Master FX", "Master FX"),
    pads={1: P("orange", "Gater"), 2: D("pine", "AF LP"), 3: D("blue", "AF HP"), 4: D("pink", "Digitise"), 5: D("magenta", "Phaser"), 6: D("peach", "Glitch"),
          7: D("yellow", "Sample"), 8: D("white", "Off", "Apagar"), **{n: D("grey", f"Step\n{n - 8}", f"Paso\n{n - 8}") for n in range(9, 25)},
          **{n: D("cream", "Slot", "Hueco") for n in range(26, 31)}, 31: D("teal", "Gesture", "Gesto"), 32: D("red", "Rec.", "Grabar")},
    knobs={1: K("Division", "División"), 2: K("Depth", "Profundidad"), 3: K("Width", "Ancho"), 4: K("Smoothing", "Suavizado")},
    buttons={"Mixer": "white"})]

_FX_ROW = {**{n: D("cream", "Slot", "Hueco") for n in range(26, 31)}, 31: D("teal", "Gesture", "Gesto"), 32: D("red", "Rec.", "Grabar")}
V["vista-fx"] = [
    MAP("FX view (the FX button), delay page: Octave ▲ / ▼ = the knobs are the tracks' delay / reverb sends; Duplicate = reset (sends to 0, master "
        "filter centred, Master FX off); pads 1-24 as on the original; the bottom row as in Master FX: slots 26-30, the mechanical gesture (31), "
        "record the capture (32).",
        "Vista FX (botón FX), página de delay: Octave ▲ / ▼ = los knobs son los envíos de delay / reverb de las pistas; Duplicate = reset (envíos a 0, "
        "filtro master al centro, Master FX apagado); los pads 1-24 como en el original; la fila inferior como en Master FX: huecos 26-30, el gesto "
        "mecánico (31), grabar la captura (32).",
        ("FX", "FX"),
        pads={**steps("peach", 16), **steps("cream", 8, 17), **_FX_ROW},
        knobs={k + 1: K(t) for k, t in enumerate(TRACKS)},
        buttons={"FX": "white", "Oct ▲": ("peach", True), "Oct ▼": ("cream", True), "Duplicate": "white"}),
    MAP("The FX view with Shift (delay page): Shift + knob = the delay's settings — K1 time, K2 sync, K3 feedback, K4 width, K5 ratio, K6 slew (on the "
        "reverb page: K1 type, K2 decay, K3 damping); saved with the project. Shift + Octave ▲ / ▼ = master filter resonance ±16 (since RC4; yellow); "
        "Shift + pad 25 = master filter off / on (since RC4; yellow, red while off).",
        "La vista FX con Shift (página de delay): Shift + knob = los ajustes del delay — K1 time, K2 sync, K3 feedback, K4 width, K5 ratio, K6 slew (en "
        "la página de reverb: K1 tipo, K2 decay, K3 damping); se guardan con el proyecto. Shift + Octave ▲ / ▼ = resonancia del filtro master ±16 "
        "(desde RC4; amarillo); Shift + pad 25 = filtro master apagado / encendido (desde RC4; amarillo, rojo apagado).",
        ("FX + Shift", "FX + Shift"),
        pads={**steps("peach", 16), **steps("cream", 8, 17), **_FX_ROW, 25: P("yellow", "Filter\noff / on", "Filtro\nno / sí")},
        knobs=knobs8("Time", "Sync", "Feedback", "Width", "Ratio", "Slew"),
        buttons={"FX": "white", "Oct ▲": "yellow", "Oct ▼": "yellow", "Shift": "grey"}),
]

V["sidechain"] = [
    MAP("Sidechain view (Shift + FX), Synth 1's sidechain: K1-K4 = attack, hold, decay and depth of the sidechain of the track whose preset was touched "
        "last (in its colour; since RC2); K7 / K8 = the master compressor's attack / release (white; since RC2). Row 1: pads 1-4 = Synth 1, Synth 2, "
        "MIDI 1, MIDI 2 as the source (since RC2: their pattern notes fire the ducking), pads 5-8 = Drum 1-4: the chosen source in the colour of the "
        "ducked track (here MIDI 1, in Synth 1's magenta), the others dim; rows 3-4 = the presets, as on the original.",
        "Vista Sidechain (Shift + FX), el sidechain de Synth 1: K1-K4 = ataque, hold, decay y profundidad del sidechain de la pista del último preset "
        "tocado (en su color; desde RC2); K7 / K8 = ataque / release del compresor master (blanco; desde RC2). Fila 1: pads 1-4 = Synth 1, Synth 2, MIDI "
        "1, MIDI 2 como fuente (desde RC2: las notas de su patrón disparan el ducking), pads 5-8 = Drum 1-4: la fuente elegida en el color de la pista "
        "del sidechain (aquí MIDI 1, en el magenta de Synth 1), las demás tenues; filas 3-4 = los presets, como en el original.",
        ("Sidechain", "Sidechain"),
        pads={**{i + 1: D("white", t) for i, t in enumerate(TRACKS)}, 3: P(TRACK["Synth 1"], "MIDI 1"), **steps("grey", 16, 17)},
        knobs={1: K("Attack", "Ataque"), 2: K("Hold"), 3: K("Decay"), 4: K("Depth", "Profundidad"), 7: K("Comp. attack", "Ataque comp."),
               8: K("Comp. release", "Release comp.")},
        buttons={"FX": "white"}, kcol={1: "magenta", 2: "magenta", 3: "magenta", 4: "magenta", 7: "white", 8: "white"}),
    MAP("The drum pages (Octave ▼): the sidechain between drums — row 1 pads 5-8 = which drum triggers, rows 3-4 = the ducking presets per drum, as on "
        "the original; pads 1-4 = Synth 1, Synth 2, MIDI 1, MIDI 2 as the trigger of the drum whose preset was touched last (since RC2; the chosen one "
        "in the drum's colour, here Drum 2 by Synth 1; not saved); K1-K4 = that drum's attack, hold, decay and depth (in its colour; saved with the "
        "project).",
        "Las páginas de drums (Octave ▼): el sidechain entre drums — fila 1, pads 5-8 = qué drum dispara, filas 3-4 = los presets de ducking de cada "
        "drum, como en el original; pads 1-4 = Synth 1, Synth 2, MIDI 1, MIDI 2 como disparo del drum del último preset tocado (desde RC2; el elegido en "
        "el color del drum, aquí Drum 2 por Synth 1; no se guarda); K1-K4 = ataque, hold, decay y profundidad de ese drum (en su color; se guardan con el "
        "proyecto).",
        ("Sidechain drums", "Sidechain drums"),
        pads={1: P("yellow", "Synth 1"), **{i + 1: D(TRACK[t], t) for i, t in enumerate(TRACKS) if t != "Synth 1"}, **steps("grey", 16, 17)},
        knobs={1: K("Attack", "Ataque"), 2: K("Hold"), 3: K("Decay"), 4: K("Depth", "Profundidad")},
        buttons={"FX": "white"}, kcol={1: "yellow", 2: "yellow", 3: "yellow", 4: "yellow"}),
]

# ===== 9. Scenes and patterns
_PAT = {}
for _i, _t in enumerate(TRACKS):
    for _r in range(4): _PAT[1 + _i + 8 * _r] = D(TRACK[_t])
# the mutate settings page: (pad, label en, label es, bright)
_MUT = [(1, "L4", "L4", True), (9, "L3", "L3", False), (17, "L2", "L2", False), (25, "L1", "L1", False),
        (2, "L8", "L8", False), (10, "L7", "L7", False), (18, "L6", "L6", False), (26, "L5", "L5", False),
        (3, "Chain", "Cadena", True), (11, "Exact", "Exacta", False), (19, "Random", "Azar", False),
        (4, "All", "Todo", True), (12, "7/8", "7/8", False), (20, "6/8", "6/8", False), (28, "5/8", "5/8", False),
        (5, "1/2", "1/2", False), (13, "3/8", "3/8", False), (21, "2/8", "2/8", False), (29, "1/8", "1/8", False),
        (6, "Rep.\non", "Rep.\nsí", True), (14, "Rep.\noff", "Rep.\nno", False), (7, "Keep 1\noff", "Keep 1\nno", True), (15, "Keep 1\non", "Keep 1\nsí", False)]
V["patterns"] = [
    MAP("Patterns view (columns = tracks, rows = patterns) in chain mode (since RC2; Shift + Octave ▲, Octave ▲ green; Shift + Octave ▼ = off): in "
        "Synth 1's column, A (yellow) plays n times (A again = one more, up to 8; the knob LEDs count them), then jumps to B (green), the next time to C "
        "(red): A A A B A A A C. Clear + pattern removes the rule. The mode is saved with the project and each scene. Beta 5.56 only: Shift + a "
        "Duplicate tap = pattern mutate.",
        "Vista Patterns (columnas = pistas, filas = patrones) en modo cadena (desde RC2; Shift + Octave ▲, Octave ▲ verde; Shift + Octave ▼ = apagado): "
        "en la columna de Synth 1, A (amarillo) suena n veces (A otra vez = una más, hasta 8; los LEDs de los knobs las cuentan), luego salta a B (verde) "
        "y la vez siguiente a C (rojo): A A A B A A A C. Clear + patrón quita la regla. El modo se guarda con el proyecto y con cada escena. Solo Beta "
        "5.56: Shift + toque a Duplicate = mutate de patrones.",
        ("Pattern chains", "Cadenas"),
        pads={**_PAT, 1: P("yellow", "A"), 9: P("green", "B"), 17: P("red", "C")},
        knobs={k: K(f"×{k}") for k in range(1, 9)},
        buttons={"Patterns": "white", "Oct ▲": "green"}),
    MAP("Beta 5.56 only: pattern mutate's settings (Shift + Duplicate held in Patterns; peach, the chosen value bright): column 1 Length 4 to 1 and "
        "column 2 Length 8 to 5 (from the top), 3 the length type (as the chain / exact / random), 4-5 Amount (all, 7/8 … 1/8 of the chain's slots "
        "change), 6 Repeats on / off, 7 Keep slot 1 off / on; the track buttons bright = selected. Duplicate closes.",
        "Solo Beta 5.56: los ajustes del mutate de patrones (Shift + Duplicate mantenido en Patterns; melocotón, el valor elegido brillante): columna 1 "
        "Length 4 a 1 y columna 2 Length 8 a 5 (de arriba abajo), 3 el tipo de longitud (como la cadena / exacta / al azar), 4-5 Amount (todo, 7/8 … 1/8 "
        "de los huecos de la cadena cambian), 6 Repeats sí / no, 7 Keep slot 1 no / sí; los botones de pista brillantes = elegidas. Duplicate cierra.",
        ("Mutate settings", "Ajustes mutate"),
        pads={p: P("peach", en, es, not b) for p, en, es, b in _MUT},
        buttons={"Patterns": "white", "Duplicate": "peach", "Synth 1": "peach", **{t: ("peach", True) for t in TRACKS[1:]}}),
]

_MIX = {**{i + 1: P(TRACK[t], t) for i, t in enumerate(TRACKS)}, **{17 + s: D("grey", f"Scene\n{s + 1}", f"Escena\n{s + 1}") for s in range(16)}}
V["mixer"] = [
    MAP("Mixer view (levels page): pads 1-8 = the tracks' mutes, pads 17-32 = the 16 scenes (as on the original; a scene saved in chain mode shows peach "
        "and brings the mode back, since RC2); Shift + knob right / left = that track's level to 100 / 0; Mixer again = Master FX. Beta 5.56 only: pad "
        "16 held + track pads = solo (pad 16 white), a tap on pad 16 with no solo = solo flip (orange); Mixer held ½ s = Master FX only while held.",
        "Vista Mixer (página de niveles): pads 1-8 = los mutes de las pistas, pads 17-32 = las 16 escenas (como en el original; una escena guardada en "
        "modo cadena se ve melocotón y al cargarla vuelve el modo, desde RC2); Shift + knob a la derecha / izquierda = el nivel de esa pista a 100 / 0; "
        "Mixer otra vez = Master FX. Solo Beta 5.56: pad 16 mantenido + pads de pista = solo (pad 16 blanco), un toque al pad 16 sin solo = solo flip "
        "(naranja); Mixer mantenido ½ s = Master FX solo mientras lo mantienes.",
        ("Mixer", "Mixer"),
        pads={**_MIX, 16: P("white", "Solo"), 19: P("peach", "Chain", "Cadena")},
        knobs={k + 1: K(t) for k, t in enumerate(TRACKS)}, buttons={"Mixer": "white", "Oct ▲": "white"}),
    MAP("The Mixer with Shift: Shift + pads 1-8 = mute / unmute that track on the next bar (since RC2; the pad blinks while it waits; stopped, at once); "
        "Shift + pads 9-16 = the current scene's repeats (yellow, the chosen one green; since RC4, while playing the repeat now playing is white); "
        "Shift + knob = level 100 / 0.",
        "El Mixer con Shift: Shift + pads 1-8 = silenciar / activar esa pista en el compás siguiente (desde RC2; el pad parpadea mientras espera; "
        "parado, al momento); Shift + pads 9-16 = las repeticiones de la escena actual (amarillo, la elegida en verde; desde RC4, sonando, la "
        "repetición que suena en blanco); Shift + knob = nivel 100 / 0.",
        ("Mixer + Shift", "Mixer + Shift"),
        pads={**_MIX, 9: P("white", "×1"), 10: P("yellow", "×2"), 11: P("green", "×3"), **{9 + i: P("yellow", f"×{i + 1}") for i in range(3, 8)}},
        knobs={k: K("100 / 0") for k in range(1, 9)}, buttons={"Mixer": "white", "Shift": "grey"}),
    MAP("Cue mode (since RC2; on the pan page, Octave ▼, Shift + knob right / left = on / off; Octave ▼ pink): the pan knobs become each track's send to "
        "the cue (the right output), from the centre to the right, pink and brighter with more send; the left output keeps the mix in mono. Clear + "
        "knob = no cue; since RC4 the metronome and the previews sound in the cue only.",
        "Modo cue (desde RC2; en la página de panorama, Octave ▼, Shift + knob a la derecha / izquierda = encendido / apagado; Octave ▼ rosa): los knobs "
        "de panorama pasan a ser el envío de cada pista al cue (la salida derecha), del centro a la derecha, en rosa y más brillantes con más envío; la "
        "salida izquierda sigue con la mezcla en mono. Clear + knob = sin cue; desde RC4 el metrónomo y las escuchas previas suenan solo en el cue.",
        ("Cue mode", "Modo cue"),
        pads=_MIX, knobs={k + 1: K(f"{t} cue") for k, t in enumerate(TRACKS)},
        buttons={"Mixer": "white", "Oct ▼": "pink"},
        kcol={1: "pink", 2: ("pink", True), 3: "pink", 4: ("pink", True), 5: ("pink", True), 6: "pink", 7: ("pink", True), 8: ("pink", True)}),
]

# ===== 10. Projects and packs
V["projects"] = [MAP(
    "Projects view (copying since RC2): Duplicate + pad A = the source (yellow, blinks; again = forget it); Duplicate + pad B = copy it there — an empty "
    "B is written at once, a used B blinks white and needs Duplicate + B again within ~5 s; never over the loaded project. To another pack: pick the "
    "source, load the other pack, come back to Projects and Duplicate + B. What is copied is the project as saved on the card (save it first); it "
    "writes to the card. Loading and saving as on the original.",
    "Vista Projects (copiar desde RC2): Duplicate + pad A = la fuente (amarillo, parpadea; otra vez = olvidarla); Duplicate + pad B = copiarlo ahí — un "
    "B vacío se escribe al momento, un B ocupado parpadea en blanco y hay que repetir Duplicate + B antes de ~5 s; nunca sobre el proyecto cargado. A "
    "otro pack: elige la fuente, carga el otro pack, vuelve a Projects y Duplicate + B. Se copia el proyecto tal como está guardado en la tarjeta "
    "(guárdalo antes); escribe en la tarjeta. Cargar y guardar como en el original.",
    ("Projects", "Projects"),
    pads={**{n: D("blue") for n in range(1, 9)}, 4: P("white", "Loaded", "Cargado"), 5: P("yellow", "A"), 7: P("white", "B")},
    buttons={"Projects": "white", "Duplicate": "white"})]

V["packs"] = [MAP(
    "Packs view (Shift + Projects): Clear (steady white in this view), then a pack (only that one blinks; it is not loaded), then Clear again within 5 s "
    "= that pack is deleted — never the loaded one; the slot can be reused after a restart. The first pack, the internal memory's, is read-only for the "
    "mod: it cannot be deleted and nothing of the mod is written into it.",
    "Vista de packs (Shift + Projects): Clear (blanco fijo en esta vista), luego un pack (solo ese parpadea; no se carga) y Clear otra vez antes de 5 s "
    "= ese pack se borra — nunca el cargado; el hueco se reutiliza tras reiniciar. El primer pack, el de la memoria interna, es de solo lectura para el "
    "mod: no se borra y no se escribe en él nada del mod.",
    ("Packs", "Packs"),
    pads={**{n: D("grey") for n in range(1, 13)}, 1: D("grey", "Internal", "Interno"), 6: P("grey", "Delete?", "¿Borrar?")},
    buttons={"Projects": "white", "Clear": "white", "Shift": "grey"})]

VIEW_MAPS = V


# ---------------------------------------------------------------------------------------------------- drawing
def hexcol(c):
    if isinstance(c, tuple): return blend(hexcol(c[0])) if c[1] else hexcol(c[0])
    if c.startswith("#"): return c
    return COL[c]


def blend(h, a=M.DIM, bg=BG):
    """a colour at a (0..1) over the panel"""
    rgb = [int(h[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(bg[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join("%02x" % round(a * x + (1 - a) * y) for x, y in zip(rgb, b))


def luma(h): return (30 * int(h[1:3], 16) + 59 * int(h[3:5], 16) + 11 * int(h[5:7], 16)) // 100


def pads_of(m):
    p = m["pads"]
    return _categories() if p == "categories" else p


def figure(m, lang):
    """a map -> make_manual's figure dict in that language"""
    k = 0 if lang == "en" else 1
    pads = {}
    for n, (c, en, es, dim) in pads_of(m).items():
        h = hexcol(c)
        seen = blend(h) if dim else h
        pads[n] = (h, en if k == 0 else es, dim, "#111" if luma(seen) >= 110 else "#e8eaed")
    f = M.fig(m["caption"][lang], pads=pads, knobs={n: v[k] for n, v in m["knobs"].items()},
              buttons={b: hexcol(c) for b, c in m["buttons"].items()}, view=m["title"][lang])
    f["kcol"] = {n: hexcol(c) for n, c in m["kcol"].items()}
    return f


FONT = "Arial, Helvetica, sans-serif"


def with_font(svg):
    """the figure's root tag with its own font: an image in the wiki does not take the page's (without it, a serif)"""
    i = svg.index(">")
    return svg if "font-family=" in svg[:i] else svg[:i] + f' font-family="{FONT}"' + svg[i:]


def write_all(img_dir=IMG_DIR):
    """writes every view's maps as view-<id>[-n]-<lang>.svg in img_dir; -> {view id: [(file_en, file_es, caption_en, caption_es)]}"""
    img_dir = Path(img_dir)
    img_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    for vid, maps in VIEW_MAPS.items():
        L = []
        for i, m in enumerate(maps):
            stem = f"view-{vid}" + (f"-{i + 1}" if len(maps) > 1 else "")
            files = []
            for lang in ("en", "es"):
                f = f"{stem}-{lang}.svg"
                (img_dir / f).write_text(with_font(M.svg(figure(m, lang))) + "\n", encoding="utf-8", newline="\n")
                files.append(f)
            L.append((files[0], files[1], m["caption"]["en"], m["caption"]["es"]))
        out[vid] = L
    return out


# ---------------------------------------------------------------------------------------------------- checks
# Helvetica widths (1/1000 em) to see that a label fits its pad (54 px, bold 9.5) or its knob's space (96 px between knobs, 10)
_W = dict(zip(" !\"#$%&'()*+,-./0123456789:;<=>?", [278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278] + [556] * 10 +
              [333, 333, 584, 584, 584, 611]))
_W.update(dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", [722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778, 667, 778, 722, 667, 611,
                                                  722, 667, 944, 667, 667, 611])))
_W.update(dict(zip("abcdefghijklmnopqrstuvwxyz", [556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611, 611, 611, 389, 556, 333,
                                                  611, 556, 778, 556, 556, 500])))
_PLAIN = "áéíóúñÁÉÍÓÚÑ¿ª"


def width(s, size, bold=True):
    total = 0
    for ch in s:
        base = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n", "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N", "¿": "?",
                "ª": "a"}.get(ch, ch)
        w = _W.get(base, 1000 if ch in "→↔↑↕" else 600)
        total += w if bold else w * 0.93
    return total * size / 1000


def check(maps=VIEW_MAPS):
    """-> a list of problems: labels that do not fit, unknown colours / buttons, words of the inner works"""
    import make_wiki as MW
    bad = []
    for vid, ms in maps.items():
        for i, m in enumerate(ms):
            where = f"{vid}[{i + 1}]"
            for lang in ("en", "es"):
                t = m["title"][lang]
                if width(t, 15) > 136: bad.append(f"{where} {lang}: the view name «{t}» is too long")
                for word in MW.BANNED.finditer(m["caption"][lang] + " " + t): bad.append(f"{where} {lang}: «{word.group(0)}»")
            for n, (c, en, es, dim) in pads_of(m).items():
                if not 1 <= n <= 32: bad.append(f"{where}: pad {n}")
                if not c.startswith("#") and c not in COL: bad.append(f"{where}: colour {c}")
                for lab in (en, es):
                    lines = lab.split("\n") if lab else []
                    if len(lines) > 3: bad.append(f"{where}: pad {n} «{lab}» has more than 3 lines")
                    for ln in lines:
                        if width(ln, 9.5) > 50: bad.append(f"{where}: pad {n} «{ln}» ({width(ln, 9.5):.0f} px)")
                    if MW.BANNED.search(lab): bad.append(f"{where}: pad {n} «{lab}»")
            for k, (en, es) in m["knobs"].items():
                if not 1 <= k <= 8: bad.append(f"{where}: knob {k}")
                for lab in (en, es):
                    if width(lab, 10, False) > 90: bad.append(f"{where}: K{k} «{lab}» ({width(lab, 10, False):.0f} px)")
            for b, c in m["buttons"].items():
                if b not in BUTTONS: bad.append(f"{where}: button {b}")
                cc = c[0] if isinstance(c, tuple) else c
                if not cc.startswith("#") and cc not in COL: bad.append(f"{where}: colour {cc}")
            for k, c in m["kcol"].items():
                cc = c[0] if isinstance(c, tuple) else c
                if not cc.startswith("#") and cc not in COL: bad.append(f"{where}: knob colour {cc}")
    return bad


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bad = check()
    written = write_all(IMG_DIR)
    n = 0
    for vid, L in written.items():
        for fe, fs, ce, cs in L:
            for f in (fe, fs):
                try: ET.fromstring((IMG_DIR / f).read_text(encoding="utf-8"))
                except ET.ParseError as e: bad.append(f"{f}: {e}")
                n += 1
    from make_guide import data
    ids = [v["id"] for v in data("en")[0] if v["part"] not in ("0", "11", "A")]
    missing = [v for v in ids if v not in written]
    extra = [v for v in written if v not in ids]
    if missing: bad.append(f"views without a map: {missing}")
    if extra: bad.append(f"maps of no view: {extra}")
    for b in bad: print("!", b)
    print(f"{len(written)} views, {sum(len(L) for L in written.values())} maps, {n} SVG files; {len(bad)} problems")
    return len(bad)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
