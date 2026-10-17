"""The user manual of the mod, from one source: the feature list (README), the short text manual (docs/MANUAL.md) and the illustrated manual
(docs/manual/index.html, colour diagrams of the panel as inline SVG, in the spirit of the original user guide).

    python tools/make_manual.py            (writes docs/MANUAL.md, docs/manual/index.html, the English docs/MANUAL.en.md, docs/manual/en.html
                                            and the feature list blocks of README.md: Spanish, and English when its markers are there)
The English text is in tools/manual_en.py (same section ids and figures).
Every section: (id, group, title, summary bullets, figures, detail in a small markdown: ###, | tables |, - lists, 1. lists, **bold**, `code`).
"""
from __future__ import annotations
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "RC2"

# ---------------------------------------------------------------------------------------------------- colours (approximations of the pad colours)
C = dict(red="#ff3b30", orange="#ff8a00", yellow="#ffd23f", green="#3ddc5a", teal="#00c2a8", blue="#2f7bff", purple="#8e5cff", magenta="#e040fb",
         white="#ffffff", peach="#ffb38a", cream="#fff1c4", grey="#9aa0a6", pink="#ff6fae", lime="#b6f23d")
DIM = 0.35

GROUPS = [("A", "Accesos directos y usabilidad"), ("B", "Controles expuestos"), ("C", "Nuevos modos de control"), ("D", "DSP"), ("E", "Miscelánea")]


def P(**kw): return kw


S = []      # the sections


def sec(sid, group, title, summary, detail, figs=()):
    S.append(dict(id=sid, group=group, title=title, summary=summary, detail=detail.strip("\n"), figs=list(figs)))


# ---------------------------------------------------------------------------------------------------- figures
def fig(caption, pads=None, knobs=None, buttons=None, view="", badges=None):
    """pads: {n (1..32): (colour name, label, dim?)}; knobs: {k (1..8): label}; buttons: {name: colour}; badges: {"Mixer" / "pad8" / "K1": number}."""
    return dict(caption=caption, pads=pads or {}, knobs=knobs or {}, buttons=buttons or {}, view=view, badges=badges or {})


THIN = ["Scales", "Oct ▼", "Oct ▲", "1-16 / 17-32", "Clear", "Duplicate", "Save", "Projects", "Shift"]      # the thin buttons under the knobs
TRACKS = ["Preset", "Synth 1", "Synth 2", "MIDI 1", "MIDI 2", "Drum 1", "Drum 2", "Drum 3", "Drum 4", "Patterns"]   # pad-wide, above the grid
LEFT = ["Note", "Velocity", "Gate", "Pattern\nSettings"]                                                       # under Preset, beside the pad rows
RIGHT = ["Mixer", "FX", "Record", "Play"]                                                                      # under Patterns


def svg(f):
    """The panel as it is laid out: staggered knobs (K1 K3 K5 K7 below, K2 K4 K6 K8 above, in between), the thin buttons, the row Preset / tracks / Patterns,
    then the 4 x 8 pads between the columns Note / Velocity / Gate / Pattern Settings and Mixer / FX / Record / Play.  f["badges"]: {control: number}."""
    PW, PG = 54, 62                                   # pad width, pitch
    X0 = 22                                           # column 0 (Preset / Note ...)
    colx = lambda c: X0 + c * PG                      # c = 0 .. 9
    W, H = colx(10) + 14, 490
    badges = f.get("badges", {})
    out = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{html.escape(f["caption"])}">',
           f'<rect x="0" y="0" width="{W}" height="{H}" rx="18" fill="#17181b"/>']
    def badge(key, cx, cy):
        if key in badges:
            out.append(f'<circle cx="{cx}" cy="{cy}" r="10" fill="#ff6a13" stroke="#fff" stroke-width="1.5"/>')
            out.append(f'<text x="{cx}" y="{cy + 4}" font-size="11" font-weight="bold" fill="#fff" text-anchor="middle">{badges[key]}</text>')
    # knobs: bottom row K1 K3 K5 K7, top row K2 K4 K6 K8 in between
    kx0, ksp = colx(2), 96
    for k in range(1, 9):
        i = (k - 1) // 2
        x = kx0 + i * ksp + (ksp // 2 if k % 2 == 0 else 0)
        y = 46 if k % 2 == 0 else 96
        lab = f["knobs"].get(k)
        ring = C["teal"] if lab else "#3a3d42"
        out.append(f'<circle cx="{x}" cy="{y}" r="21" fill="#26282c" stroke="{ring}" stroke-width="{4 if lab else 2}"/>')
        out.append(f'<text x="{x}" y="{y + 4}" font-size="11" fill="#cfd3d8" text-anchor="middle">K{k}</text>')
        if lab:
            ly = y - 26 if k % 2 == 0 else y + 34
            out.append(f'<text x="{x}" y="{ly}" font-size="10" fill="{C["teal"]}" text-anchor="middle">{html.escape(lab)}</text>')
        badge(f"K{k}", x + 18, y - 18)
    if f["view"]:
        out.append(f'<text x="{colx(9)}" y="44" font-size="15" font-weight="bold" fill="#ffffff" text-anchor="middle">{html.escape(f["view"])}</text>')
    def btn(x, y, name, w, h):
        key = name.replace("\n", " ")
        col = f["buttons"].get(key)
        fill = C.get(col, col) if col else "#2b2d31"
        tc = "#111" if col else "#aeb4ba"
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" stroke="#111"/>')
        lines = name.split("\n")
        for i, ln in enumerate(lines):
            out.append(f'<text x="{x + w / 2}" y="{y + h / 2 + 3.5 + 11 * i - 5.5 * (len(lines) - 1)}" font-size="9.5" fill="{tc}" text-anchor="middle">{html.escape(ln)}</text>')
        badge(key, x + w - 3, y + 3)
    # the thin buttons
    tsp = 66; tw = 60
    span = (len(THIN) - 1) * tsp + tw
    tx0 = colx(1) + (8 * PG - (PG - PW) - span) // 2
    for i, b in enumerate(THIN): btn(tx0 + i * tsp, 140, b, tw, 18)
    # the row of track buttons
    for c, b in enumerate(TRACKS): btn(colx(c), 172, b, PW, 28)
    # the pads and the two columns
    py0 = 216
    for r in range(4):
        btn(colx(0), py0 + r * PG + 8, LEFT[r], PW, 38)
        btn(colx(9), py0 + r * PG + 8, RIGHT[r], PW, 38)
    for n in range(1, 33):
        r, c = (n - 1) // 8, (n - 1) % 8
        x, y = colx(c + 1), py0 + r * PG
        spec = f["pads"].get(n)
        if spec:
            col = C.get(spec[0], spec[0]); dim = len(spec) > 2 and spec[2]
            out.append(f'<rect x="{x}" y="{y}" width="{PW}" height="{PW}" rx="7" fill="{col}" fill-opacity="{DIM if dim else 0.95}" stroke="#000" stroke-width="1"/>')
            lines = spec[1].split("\n") if spec[1] else []
            for i, ln in enumerate(lines[:3]):
                out.append(f'<text x="{x + PW / 2}" y="{y + 26 + 12 * i - 6 * (len(lines[:3]) - 1)}" font-size="9.5" fill="#111" text-anchor="middle" font-weight="bold">{html.escape(ln)}</text>')
        else:
            out.append(f'<rect x="{x}" y="{y}" width="{PW}" height="{PW}" rx="7" fill="#2b2d31" stroke="#111"/>')
        out.append(f'<text x="{x + 4}" y="{y + 50}" font-size="8" fill="#7d838a">{n}</text>')
        badge(f"pad{n}", x + PW - 4, y + 4)
    out.append("</svg>")
    return "\n".join(out)


# ---------------------------------------------------------------------------------------------------- content
# ===== A. Accesos directos y usabilidad
sec("atajos", "A", "Mapa de atajos",
    ["Todos los atajos del mod en un dibujo del aparato: botones dobles, Shift + botón, Clear + knob y los pads especiales de cada vista."],
    """
| N.º | Atajo | Función |
|---|---|---|
| 1 | **Mixer**, **Mixer** | Master FX (A2) |
| 2 | **Synth 1 / 2** con su vista en pantalla, otra vez | Vista de la fuente del sinte y su step-drummer (A6) |
| 3 | **Shift + Preset** con un drum | Vista cromática / de escala (A7) |
| 4 | **Clear + knob** | Valor por defecto del knob, también en Master FX; en drums, a la izquierda borra la automatización (A4) |
| 5 | **Octave ▲ / ▼** en la vista FX | Envíos de delay / reverb; **Shift + knob** = sus parámetros (A3, B2) |
| 6 | **Duplicate** / **1-16 / 17-32** en la vista FX | Reset de envíos y Master FX / resonancia del filtro master (A3) |
| 7 | **Shift + FX**, luego **Octave ▼**, con los drums | Sidechain entre drums (D7) |
| 8 | **MIDI 1 / 2**, **Preset** | Pad 27 motor, 25 editor de CC, 26 patch flip, 30 step-drummer (C1) |
| 9 | Master FX: **pad 8** | Apagar todo lo fijado (A5) |
| 10 | Master FX: **pad 7** / **pad 32** / **pad 31** | Tocar / grabar el sample (C5), Glitch (C6) |
| 11 | Preset de drums / de sinte: **Clear + pad dos veces** / **Duplicate + pad + pad** | Sustituir por la captura / intercambiar o copiar entre packs samples y patches (A9, A8) |
| 12 | Vista de packs: **Clear**, el pack, **Clear** | Borrar un pack (A8) |
| 13 | **Save** | Guarda también las capturas usadas como samples (A8) |
| 14 | **Scales + Preset + Note** al encender | Modo de recuperación del bootloader (E2) |
| 15 | Mixer: **Shift + knob** | Nivel de la pista a 100 (derecha) / 0 (izquierda) (A11) |
| 16 | Master FX: **Shift + pad 7** | Sample en bucle enganchado hasta volver a pulsar el 7 (C5) |
| 17 | Preset de MIDI 1 / 2: **Clear + pad de página (1-5)** | Los valores de esa página de knobs a los iniciales (C1, **desde RC2**) |
| 18 | Advanced Setup: **Duplicate** | MIDI Thru: Thru → Out 2 → Merge → Filter (B7, **desde RC2**) |
| 19 | **Synth 1 + Synth 2** a la vez | Teclado partido: arriba Synth 1, abajo Synth 2 (A12, **desde RC2**) |
| 20 | **Shift + Pattern Settings**, un paso, **fila 4** | Random-mutate del paso: octava / escala al azar (C8, **desde RC2**) |
| 21 | Preset de MIDI 1 / 2: **pads 9-24**, **Clear + pad** dos veces, **Duplicate + A + B**, **Octave ▼ / ▲** | Patches del sinte propio: cargar, guardar, intercambiar, página (A14, **desde RC2**) |
| 22 | MIDI 1 / 2: **Clear + el botón de la pista** | El motor de la pista a sus valores iniciales (A14, **desde RC2**) |
| 23 | Preset de Synth 1 / 2: **Clear + pad** dos veces | Guarda el patch del sinte en ese hueco del pack (A15, **desde RC2**) |
| 24 | Vista de la fuente del sinte: **pad 32** | Editor de los destinos de los macro knobs (A16, **desde RC2**) |
| 25 | Projects: **Duplicate + pad A**, **Duplicate + pad B** | Copia el proyecto A al hueco B, también en otro pack (A17, **desde RC2**) |
| 26 | Preset de MIDI 1 / 2: **Duplicate + hueco A**, otro pack, **Duplicate + hueco B** | Copia un patch del sinte propio a otro pack (**desde RC2**) |
| 27 | Sidechain (**Shift + FX**): **K1-K4**, **K7 / K8** | Sidechain de la pista elegida; ataque / release del compresor master (**desde RC2**) |
| 28 | Setup: **Record** | Grabar en el sinte lo que le manda la pista MIDI: amarillo = sí (**desde RC2**) |
| 29 | **Pattern Settings** dos veces, **fila 4** | Frecuencia del paso: suena cada n vueltas del patrón (**desde RC2**) |
| 30 | Pattern Settings: **pad 25** | Dinámicas (fila 3) y random-mutate (fila 4); **Clear + pad 25** los borra del patrón (**desde RC2**) |
| 31 | Pattern Settings: **pads 26 / 27 / 28** | Nudge, orden fractal, orden deconstruido (**desde RC2**) |
| 32 | Patterns: **Shift + Octave ▲ / ▼** | Modo cadena de patrones activado / desactivado (**desde RC2**) |
| 33 | Mixer: **Shift + pads 9-16** | Repeticiones de la escena actual (**desde RC2**) |
| 34 | Setup: **pad 29 / pad 30**, luego un pad de canal | Canal de escucha / salida de los Program Change del proyecto (B7, **desde RC2**) |
| 35 | **Shift + Clear** | Metrónomo / cuenta atrás en cuatro estados; con la cuenta atrás, Record + Play = un compás antes de grabar (**desde RC2**) |
| 36 | Pattern Settings: **Shift + pad 25**, **Shift + pads 27-32** | Arpegiador del patrón encendido / apagado y su orden; acordes de la secuencia y notas mantenidas juntas, una por paso (**desde RC2**) |
| 37 | **Shift + Scales** | Editor de la escala propia: hasta 7 notas y un periodo; una iteración por fila (**desde RC2**) |
| 38 | Step-drummer: **pad 32**; página velocity: **pads 17-24** | Toggle pitch-vel (transponer en la escala / velocity) y destino propio de la página 2 (**desde RC2**) |
| 39 | **Shift + Play** | Cuantizar el patrón que suena en la pista elegida (**desde RC2**) |
| 40 | MIDI 1 / 2 en modo muestra: **Note dos veces**; **paso mantenido + sample** | Selector de los 64 samples del pack (Octave ▼ / ▲) y sample flip por paso, también en vivo con Record (**desde RC2**) |
""", [fig("Mapa de atajos: los números remiten a la tabla.", pads={7: ("yellow", "Sample"), 8: ("white", "Apagar"), 27: ("magenta", "Motor"), 31: ("teal", "Glitch"), 32: ("red", "Grabar")},
          knobs={k_: "Clear+" for k_ in range(1, 9)},
          buttons={"Mixer": "white", "Synth 1": "white", "Preset": "white", "Clear": "red", "Oct ▲": "peach", "Oct ▼": "cream", "Duplicate": "white", "1-16 / 17-32": "green",
                   "FX": "white", "MIDI 1": "orange", "Drum 1": "white", "Save": "white", "Projects": "white", "Scales": "yellow", "Note": "yellow", "Shift": "grey"},
          badges={"Mixer": 1, "Synth 1": 2, "Preset": 3, "Clear": 4, "Oct ▲": 5, "Duplicate": 6, "FX": 7, "MIDI 1": 8, "pad8": 9, "pad7": 10, "Drum 1": 11, "Projects": 12, "Save": 13, "Scales": 14, "Shift": 15},
          view="Atajos")])

sec("master-fx-acceso", "A", "Master FX en el botón Mixer",
    ["Desde el Mixer, **Mixer otra vez** abre Master FX; cualquier otro botón de vista sale."],
    """
Master FX es una vista de actuación con efectos sobre la salida master, un song pointer y una fila de efectos asignables (secciones C4, C5, C6, C7 y D1).

1. Pulsa **Mixer**.
2. Pulsa **Mixer** otra vez: se abre Master FX.
3. Cualquier otro botón de vista vuelve a la vista normal.
""", [fig("Master FX: pads 1-6 efectos, 7 sample, 8 apagar todo, 9-24 song pointer, fila inferior asignable, 31 Glitch, 32 grabar.",
          pads={1: ("red", "Gater"), 2: ("orange", "AF LP"), 3: ("blue", "AF HP"), 4: ("lime", "Digitise"), 5: ("magenta", "Phaser"), 6: ("peach", "Vinyl"),
                7: ("yellow", "Sample"), 8: ("white", "Apagar"), **{n: ("grey", "paso\n" + str(n - 8), True) for n in range(9, 25)}, 25: ("white", "FX off", True),
                **{n: ("cream", "hueco", True) for n in range(26, 31)}, 31: ("teal", "Glitch"), 32: ("red", "Grabar")},
          knobs={1: "P1", 2: "P2", 3: "P3", 4: "P4"}, buttons={"Mixer": "white"}, view="Master FX")])

sec("vista-fx", "A", "Teclas de la vista FX",
    ["**Octave ▲ / ▼** = envíos de delay / reverb; **Shift + knob** = parámetros de reverb y delay.",
     "**Duplicate** = reset (envíos a 0, filtro master al centro, Master FX apagado); **1-16 / 17-32** = resonancia del filtro master."],
    """
| Control | Función |
|---|---|
| **Octave ▲** | Los knobs controlan los **envíos de delay** (color del pad 1) |
| **Octave ▼** | Los knobs controlan los **envíos de reverb** (color del pad 17) |
| **Shift + knob** | **Parámetros del efecto**. Reverb: tipo, decay, damping. Delay: time, sync, feedback, width, ratio, slew. Se guardan con el proyecto |
| **Duplicate** | Reset: envíos a 0, filtro master al centro (sin tocar la resonancia), Master FX apagado |
| **1-16 / 17-32** | Sube la resonancia del filtro master (LED verde) |

- La fila inferior (pads 25-32) es la misma que la de Master FX: huecos asignables, el Glitch (31) y grabar (32).
- Si en Setup el retorno de reverb / delay va a la tira 3 / 4, los envíos de esas tiras tienen tope a la mitad y van a media velocidad.
""", [fig("Vista FX: Octave elige delay / reverb; la fila inferior es la de Master FX.", pads={**{n: ("peach", "", True) for n in range(1, 17)}, **{n: ("cream", "", True) for n in range(17, 25)},
                                                                                                     31: ("teal", "Glitch"), 32: ("red", "Grabar")},
          knobs={k: "envío" for k in range(1, 9)}, buttons={"FX": "white", "Oct ▲": "peach", "Oct ▼": "cream", "Duplicate": "white", "1-16 / 17-32": "green"}, view="FX")])

sec("clear-knob", "A", "Clear + knob = valor por defecto",
    ["Mantén **Clear** y gira un knob a la derecha: vuelve a su valor por defecto. En drums (LED azul), a la izquierda borra la automatización de los knobs de stock (LED rojo), como en el original. También en el motor de las pistas MIDI y en **Master FX**."],
    """
| Dónde | Clear + knob a la derecha | Clear + knob a la izquierda |
|---|---|---|
| Drums (knobs de stock y nuevos) | Valor por defecto; LED **azul** | Knobs de stock: borra su automatización; LED **rojo** (como el original) |
| Motor de las pistas MIDI y oscilador | Valor por defecto; LED rojo mientras Clear | Igual |
| **Master FX** (desde RC0.3) | El knob del efecto elegido vuelve a su valor por defecto | Nada (Master FX no tiene automatización) |

- En drums y en el motor MIDI restablece **las dos capas** del knob: la normal y la de Shift.
- **Master FX:** mientras Clear está pulsado, los knobs del efecto elegido se ven **azules** si están en su valor por defecto y **rojos** si no. Vale para los efectos de los pads 1-6, el Glitch (velocidad normal, sin repetición, sin retraso ni caos) y el sample (sin transposición, one-shot, inicio 0, final al máximo).
- RC0.3: el azul de los drums es el del original (antes salía un rojo anaranjado tenue).
""")

sec("pad8", "A", "Apagar efectos fijados (pad 8 de Master FX)",
    ["**Pad 8** apaga todo lo fijado con Shift (efectos y song pointer) y hace bypass de los FX; tocar un efecto fijado lo suelta."],
    """
- **Shift + pad de efecto** deja el efecto fijado. Tocarlo otra vez (sin Shift) lo suelta.
- **Pad 8** (blanco) suelta todos los efectos fijados, también los de la fila inferior, apaga el song pointer y para el sample.
""")

sec("fuente-sinte", "A", "Vista de la fuente del sinte",
    ["Con Synth 1 / 2 en pantalla, **pulsa su botón otra vez**: pads 25-29 eligen la fuente (ruido, entradas, invertidas), pad 30 = step-drummer."],
    """
1. Con la vista de Synth 1 o Synth 2 en pantalla, pulsa su botón otra vez.
2. Elige la fuente:

| Pad | Fuente |
|---|---|
| 25 | Ruido (lo normal) |
| 26 | Entrada 1 |
| 27 | Entrada 2 |
| 28 | Entrada 1 con la fase invertida |
| 29 | Entrada 2 con la fase invertida |
| 30 | Step-drummer del sinte (C2) |

3. Cualquier botón cierra la vista.

- El parche debe tener nivel de ruido (CC 56) para que la fuente se oiga.
- Si en Setup el retorno de reverb / delay va a la tira 3 / 4, esa es la señal que recibe el sinte.
- La fuente se guarda con el proyecto.
""", [fig("Vista de la fuente del sinte (Synth 1 / 2 pulsado dos veces).", pads={25: ("white", "Ruido"), 26: ("green", "In 1", True), 27: ("green", "In 2", True), 28: ("orange", "In 1\ninv", True),
                                                                                  29: ("orange", "In 2\ninv", True), 30: ("purple", "Step\ndrum", True)}, buttons={"Synth 1": "white"}, view="Fuente del sinte")])

sec("cromatica", "A", "Vista cromática y de escala de los drums",
    ["**Shift + Preset** con un drum: los pads tocan el sample en la escala; K1 = sesgo de tono, Shift + K1 = cents; vista Note: pads 25-28 = drums 4-1."],
    """
- **Shift + Preset** con un drum seleccionado: los pads tocan el sample transpuesto según la escala y la tónica de la vista Scales (tres filas).
- **K1** = sesgo de tono en semitonos; **Shift + K1** = afinación fina en cents.
- Grabando, cada tono se graba solo en su paso.
- Vista **Note** de los drums: los pads 25-28 repiten los cuadros de los drums 4 … 1.
- **Desde RC2:** en la vista Preset de un drum, **Preset otra vez** enciende / apaga la vista cromática (como Shift + Preset).
""")

sec("pack", "A", "Gestión del pack desde el aparato",
    ["**Save** también guarda en la tarjeta los samples sustituidos por capturas.",
     "**Duplicate + pad A + pad B** (Preset de drums) intercambia dos samples; entre packs **copia** samples y patches de sinte; **Clear**, el pack, **Clear** (vista de packs) borra un pack."],
    """
No está en las versiones más seguras (RC0.3S, RC0.2S, RC0.1S, RC0S). Novedades: RC0.1, Duplicate se ilumina y funciona en las vistas Preset de drums y de sinte, copiar samples y patches entre packs y borrar packs con pulsaciones; RC0.2, el LED de Clear durante el borrado; RC0.3, las copias van al sitio del sample sustituido cuando caben, la memoria de importación nunca pisa un sample que suena y el borrado se ve mejor (Clear blanco fijo, los packs vuelven a su color); RC0.4, copias a huecos vacíos y Clear blanco fijo desde que se abre la vista de packs.

### Guardar las capturas en el pack
Al guardar el proyecto, cada sample de drum sustituido por una captura (A9) se escribe en el pack como `PCM/NN_PCM.wav`, si cabe en la memoria de samples.

### Intercambiar dos samples
Vista Preset de drums: mantén **Duplicate** (se ilumina en esta vista), toca el pad **A** (parpadea en azul) y luego el pad **B**. Los dos ficheros y la tabla de samples se intercambian: suena al instante.

### Copiar samples entre packs
1. En el pack del sample: vista Preset de drums, **Duplicate + pad A**. Queda copiado (parpadea en azul con Duplicate mantenido), aunque sueltes Duplicate.
2. Carga el otro pack. Con Duplicate mantenido, el pad con el número de A parpadea en amarillo.
3. **Duplicate + pad B**: el sample A se copia sobre B en este pack y suena al instante. **El pack de A no cambia.**
4. Duplicate + A otra vez (en su pack) cancela.
5. Dentro del mismo pack, Duplicate + A + B sigue **intercambiando** los dos samples.
6. **Dónde va la copia** (desde RC0.3): si el sample cabe en el sitio de B, va ahí y no gasta memoria. Si no, va a la memoria libre de importación (≈ 44 s), que vuelve a empezar cuando ningún sample la usa (por ejemplo, al cargar otra vez el pack). Si no queda sitio, no cambia nada: la copia nunca pisa un sample que suena.
7. **B vacío** (desde RC0.4): se puede copiar a un pad sin sample; su fichero se crea en el pack.

### Copiar patches de sinte entre packs
1. Vista Preset de Synth 1 o 2, en el pack del patch: **Duplicate + pad A** (Duplicate se ilumina en esta vista). Queda copiado (azul con Duplicate mantenido).
2. Carga el otro pack: con Duplicate mantenido, el pad de A (en su página) parpadea en amarillo.
3. **Duplicate + pad B**: el patch A se copia sobre B en este pack y B vuelve a elegirse, así que suena al instante. El pack de A no cambia. En el mismo pack los dos patches se **intercambian**; Duplicate + A otra vez cancela.
4. Los 128 patches del pack son comunes a los dos sintes. No funciona en la vista de la fuente ni en la del step-drummer (desde RC0.3, tampoco con Duplicate pulsado antes de abrirlas).
5. **Hueco vacío** (desde RC0.4): B puede ser un pad apagado. Si está más allá del último patch de su banco, los huecos vacíos de en medio siguen vacíos, como al guardar un patch en el original.

### Borrar un pack
1. Vista de packs (**Shift + Projects**): toca **Clear** (sin Shift). Durante ~5 s parpadean los packs que se pueden borrar (nunca el cargado).
2. Toca el pack: solo ese parpadea; no se carga.
3. Toca **Clear** otra vez antes de 5 s: el pack se borra. El hueco se puede reutilizar tras reiniciar.
4. Así desde RC0.1; en RC0 (Clear mantenido + pack) no funcionaba en el aparato. Clear se ve **blanco fijo** desde que se abre la vista de packs (desde RC0.4; antes tenue) y mientras el borrado espera confirmación; al terminar o cancelar, los packs vuelven a su color (desde RC0.3; en RC0.2 Clear parpadeaba y los packs podían quedarse apagados; en RC0.1 Clear no se encendía).
""", [fig("Vista Preset de drums: Duplicate + A + B intercambia los samples.", pads={3: ("blue", "A"), 12: ("yellow", "B")}, buttons={"Duplicate": "white", "Preset": "white"}, view="Preset de drums"),
      fig("Vista Preset de Synth 1: Duplicate + A copia el patch (azul); en otro pack, el de A parpadea en amarillo y Duplicate + B lo copia ahí.",
          pads={5: ("yellow", "A"), 14: ("magenta", "B", True)}, buttons={"Duplicate": "white", "Preset": "white", "Synth 1": "magenta"}, view="Preset de sinte")])

sec("sustituir", "A", "Sustituir un drum por la captura",
    ["Vista Preset de drums: **Clear + pad dos veces** = ese sample pasa a ser la captura (hasta guardar o recargar)."],
    """
- **Clear + pad**: pregunta (el pad parpadea). **Clear + el mismo pad** otra vez: confirmado; el sample suena con la captura de Master FX (C5).
- Cualquier pad sin Clear cancela la pregunta; Clear + otro pad la mueve a ese pad.
- Es volátil hasta que guardes el proyecto: entonces se escribe en el pack (A8). En las versiones más seguras dura hasta que se vuelve a cargar el pack.
- Hasta RC0.2 era **Shift + pad**; desde RC0.3 Shift + pad vuelve a ser la selección silenciosa del original (elegir un sample sin que suene).
""")

sec("editor-cc", "A", "Editor de CC de los macros MIDI",
    ["Vista Preset de MIDI 1 / 2, **pad 25**: mueve un knob y cambia su CC / NRPN desde el aparato; pad 26 = guardar."],
    """
1. Vista Preset de MIDI 1 / 2, **pad 25** (se enciende).
2. **Mueve un knob**: queda elegido y su número de CC se dibuja con los 32 pads.
3. **Octave ▼ / ▲**: siguiente / anterior campo.
4. **Gira el knob** para cambiar el valor.
5. **Guardar:** el pad **26** (Save), o avanza con Octave ▼ hasta el paso de guardar (el pad 26 y el botón Save parpadean) y pulsa Octave ▼ otra vez.
6. **Descartar:** cualquier botón de vista, el pad 25 o un pad de plantilla.

| El número del primer campo | Tipo | Campos |
|---|---|---|
| Cualquier otro | CC | número, inicio, fin |
| 99, 98 o 6 | NRPN de 7 bits | número, MSB, LSB, inicio, fin |
| 38 | NRPN de 14 bits | número, MSB, LSB, inicio (MSB, LSB), fin (MSB, LSB) |
""")

sec("mixer-shift", "A", "Mixer: Shift + knob = nivel a 100 / 0",
    ["Vista Mixer: **Shift + girar un knob a la derecha** pone el nivel de esa pista a **100**; **a la izquierda**, a **0**."],
    """
- En la página de niveles del Mixer (la normal, Octave ▲). En la de panorama (Octave ▼), Shift + knob mueve el panorama como siempre (**desde RC2**: enciende / apaga el modo cue, ver la guía por vistas).
- El salto es como un giro del knob: sale por MIDI y, grabando, queda en la automatización.
- En el original, Shift + knob hacía lo mismo que el knob solo: no se pierde ninguna función. Clear + knob (borrar la automatización) y Master FX (Mixer dos veces) no cambian.
- Desde RC0.3 (también en RC0.3S).
""", [fig("Mixer: Shift + knob a la derecha = nivel 100, a la izquierda = 0.", knobs={k: "100 / 0" for k in range(1, 9)}, buttons={"Mixer": "white", "Shift": "grey"},
          view="Mixer")])

sec("teclado-partido", "A", "Teclado partido Synth 1 + Synth 2",
    ["**Desde RC2.** Mantén **Synth 1** y pulsa **Synth 2** (o al revés): las dos filas de arriba tocan Synth 1 y las dos de abajo Synth 2."],
    """
- Cada mitad es el teclado de su sinte: su escala, su octava y su velocity (las mismas teclas que la mitad de abajo de su vista Note), con sus colores.
- Los knobs y Octave son los del primer sinte que pulsaste.
- **Salir:** cualquier botón de pista o de vista (Note, Preset, Mixer, FX, un Synth solo…). Las notas pulsadas se sueltan. Play, Record, Octave y Shift no la cierran.
- Synth 1 o Synth 2 solos siguen como siempre (dos veces = la vista de la fuente, A6).
""", [fig("Teclado partido: filas 1-2 = Synth 1, filas 3-4 = Synth 2.", pads={**{n: ("magenta", "", n not in (1, 8, 9, 16)) for n in range(1, 17)}, **{n: ("green", "", n not in (17, 24, 25, 32)) for n in range(17, 33)}},
          buttons={"Synth 1": "white", "Synth 2": "white"}, view="Synth 1 + Synth 2")])

sec("colores-patch", "A", "Patches de sinte por modo de voz",
    ["**Desde RC2.** En la vista Preset de Synth 1 / 2 cada patch se ve según su modo de voz: **mono azul oscuro**, **glide lavanda**, **poly como siempre**."],
    """
- Mono = azul oscuro; mono con glide (Mono AG) = lavanda; poly = el color de la pista, como en el original. El patch elegido se ve más claro.
- Los modos se leen de la tarjeta al cambiar de pack, de página o de patch, y cada 4 s.
- En Advanced Setup los pads 22 / 23 ya no se encienden (allí nunca hacían nada).
""", [fig("Vista Preset de Synth 1: mono azul oscuro, glide lavanda, poly el color de la pista.", pads={**{n: ("magenta", "", True) for n in range(1, 33)}, 2: ("blue", "mono", True), 5: ("blue", "mono", True),
                                                                                                          3: ("purple", "glide"), 6: ("purple", "glide"), 1: ("white", "")},
          buttons={"Synth 1": "white", "Preset": "white"}, view="Preset de Synth 1")])

sec("patches-midi", "A", "Patches del sinte propio (MIDI 1 / 2)",
    ["**Desde RC2.** En la vista Preset de MIDI 1 / 2 las filas 2 y 3 son 16 huecos de patch del motor de la pista: tocar = cargar (suena la tónica), **Clear + pad** dos veces = guardar, **Duplicate + A + B** = intercambiar; **Octave ▼ / ▲** = 4 páginas (64 huecos por pack)."],
    """
- Un patch guarda el motor de la pista entero: el motor elegido (línea, oscilador, VA-drum, granular, secuenciador de efectos), dos osciladores, el orden de la cadena, todos los valores de todas las páginas y el ajuste del step-drummer (activado y destino). Los pasos del step-drummer y del secuenciador de efectos son del patrón: van con el proyecto.
- Los 64 huecos son del pack y los comparten MIDI 1 y MIDI 2: un patch guardado desde una pista se puede cargar en la otra.
- **Cargar:** toca un hueco. Mientras mantienes el pad suena la tónica de la escala en esa pista con el patch recién cargado.
- **Guardar:** **Clear + pad** = el hueco parpadea en blanco (pregunta); **Clear + el mismo pad otra vez** antes de ~5 s = guardado, sustituyendo lo que hubiera. Clear + otro pad mueve la pregunta.
- **Intercambiar:** mantén **Duplicate**, toca el hueco A (parpadea) y después el B: cambian de sitio. Sobre un hueco vacío, el patch se mueve. No hay gesto para vaciar un hueco: se sobrescribe o se mueve.
- **Valores iniciales:** **Clear + el botón de la pista** (MIDI 1 o MIDI 2, con una vista de esa pista en pantalla y el editor de CC cerrado) devuelve todos los valores del motor a los iniciales; el motor elegido se queda.
- Colores: melocotón tenue = hueco con patch; melocotón brillante = el último cargado o guardado; **violeta = vacío** (tocarlo no hace nada).
- **En el PC:** `tools/patchtool.py` (en el PC, con la tarjeta en un lector) trata cada patch como un fichero `.ctm`: `list` enseña los 64 huecos con su índice, nombre y motor; `copy` sube un fichero a un hueco, lo baja o lo copia entre huecos y packs; `show` lee el motor y todos los parámetros y `set` los cambia (`set bajo.ctm filt=90 engine=granular`); `new` crea un patch con los valores iniciales; `name` le da nombre y `clear` vacía un hueco. El aparato no tiene pantalla: el nombre es para la herramienta; Duplicate + A + B lo mueve con el patch, guardar encima lo borra.
- En BETA2 / BETA3 los gestos eran otros: Duplicate + pad guardaba, Clear + pad vaciaba y los vacíos estaban apagados.
- **Octave ▼** = página siguiente, **Octave ▲** = la anterior (encendidos cuando hay página en ese sentido). Al volver de Master FX o de la vista Preset de un sinte se empieza en la página 1.
- Dónde se guardan: en el hueco libre que hay detrás de cada uno de los 64 primeros patches de sinte del pack (`Patches/`). Si ese patch de sinte no existe todavía, se crea con el Initial Patch (y los anteriores del banco que falten).
- No están a la vista con el editor de CC o el step-drummer abiertos (usan esos pads y Octave).
- En la versión más segura (RC2S) no escribe en la SD: el LED de Save se pone rojo.
""", [fig("Vista Preset de MIDI 1: filas 2-3 = patches del sinte propio.", pads={**{n: ("peach", "", True) for n in (9, 10, 11, 14, 17)}, 12: ("peach", "último"),
                                                                              27: ("magenta", "Motor")},
          buttons={"MIDI 1": "white", "Preset": "white", "Duplicate": "white", "Clear": "white", "Oct ▼": "white", "Oct ▲": "white"}, view="Preset de MIDI 1")])

sec("guardar-patch", "A", "Guardar el patch del sinte en el pack",
    ["**Desde RC2.** En la vista Preset de Synth 1 / 2: **Clear + pad** pregunta (parpadea en blanco) y **Clear + el mismo pad otra vez** guarda en ese hueco el patch tal como suena."],
    """
- El aparato original no puede guardar patches (solo Components). Se guarda el patch en uso con todos sus cambios: los knobs, lo recibido por MIDI y los destinos de macro (A16).
- **Clear + pad** = pregunta, no escribe nada. **Clear + el mismo pad** antes de ~5 s = guardado: sustituye el patch que hubiera y el hueco queda elegido. Clear + otro pad mueve la pregunta; un toque sin Clear o el tiempo la anulan.
- Vale cualquiera de las 4 páginas (128 huecos). Un hueco más allá del final del banco también: los huecos intermedios quedan vacíos.
- El patch guardado conserva el nombre del que estaba cargado. Los patches de sinte se gestionan con Components; `tools/patchtool.py slist / sname` los lista y les cambia el nombre en la tarjeta.
- El patch del sinte propio que comparta ese hueco (A14) no se toca.
- Duplicate + A + B sigue copiando / intercambiando patches (A8).
- En la versión más segura (RC2S) no escribe en la SD: el LED de Save se pone rojo.
""", [fig("Vista Preset de Synth 1: Clear + pad pregunta (parpadea), Clear + el mismo pad guarda.", pads={**{n: ("magenta", "", True) for n in range(1, 33)}, 6: ("white", "¿guardar?")},
          buttons={"Synth 1": "white", "Preset": "white", "Clear": "white"}, view="Preset de Synth 1")])

sec("destinos-macro", "A", "Destinos de los macro knobs",
    ["**Desde RC2.** En la vista de la fuente del sinte (A6) el **pad 32** abre el editor: un knob elige su macro, **Octave ▼ / ▲** pasa de campo y los pads dibujan el número."],
    """
Cada uno de los 8 macro knobs de un patch tiene 4 ranuras, y cada ranura un destino, un tramo del recorrido del knob (inicio y fin) y una profundidad. En el original solo se editan con Components.

1. Vista de la fuente: con Synth 1 / 2 en pantalla, pulsa su botón otra vez. **Pad 32** (verde azulado) = editor encendido; los knobs ya no mueven los macros.
2. **Gira un knob** = eliges su macro (su LED en blanco). El primer giro no cambia nada.
3. El knob cambia el campo actual; **Octave ▼** = campo siguiente, **Octave ▲** = el anterior:

| Campo | Valor | Color del número |
|---|---|---|
| Ranura | 1-4 | amarillo |
| Inicio | 0-127 | verde |
| Fin | 0-127 | naranja |
| Destino | su número de CC o de NRPN | blanco = CC; azul claro, magenta, violeta = NRPN de los bancos 0, 1, 2 |
| Profundidad | 0-63 | verde azulado = positiva, rojo = negativa |

4. **Cualquier pad** suelta el macro (vuelven los pads de la fuente); el pad 32 apaga el editor; cualquier botón de vista lo cierra.

- **Destino:** el knob recorre primero los 31 parámetros que tienen CC, por número de CC (5, 20, 21 … 91, 93), y después los 39 que solo tienen NRPN (envolventes 2 y 3, LFO, chorus, profundidades de la matriz de modulación). Los números son los de la *Programmer’s Reference Guide* de Novation: p. ej. 74 = corte del filtro, 71 = resonancia.
- Los cambios se oyen al momento y van en el patch del proyecto. Para dejarlos en el pack, guarda el patch (A15).
""", [fig("Vista de la fuente con el editor de macros: pad 32 encendido, el knob elegido en blanco.", pads={25: ("white", "Ruido"), 32: ("teal", "Macros")},
          knobs={4: "macro 4"}, buttons={"Synth 1": "white", "Oct ▼": "white", "Oct ▲": "white"}, view="Fuente del sinte")])

sec("copiar-proyectos", "A", "Copiar proyectos a otro hueco o a otro pack",
    ["**Desde RC2.** En la vista Projects: **Duplicate + pad A** elige el proyecto (parpadea en amarillo) y **Duplicate + pad B** lo copia a ese hueco, del mismo pack o de otro."],
    """
- **Duplicate + pad A** (un hueco con proyecto) = la fuente. Duplicate + A otra vez la olvida.
- **Duplicate + pad B** = copia. Si B está vacío se escribe al momento y queda en amarillo; si tiene un proyecto parpadea en blanco y hay que repetir **Duplicate + B** antes de ~5 s para sustituirlo. El hueco del proyecto cargado nunca se escribe.
- **A otro pack:** elige la fuente, carga el otro pack, entra en Projects y Duplicate + pad B. La fuente sirve para varias copias; se pierde al apagar o al abrir Master FX.
- Se copia el proyecto guardado en la tarjeta (guarda antes si has hecho cambios). Mientras copia (unos instantes) el aparato no responde.
- Un proyecto guarda números de patch y de sample, no los sonidos: en otro pack sonará con los patches y samples de ese pack.
- En la versión más segura (RC2S) no escribe en la SD: el LED de Save se pone rojo.
""", [fig("Vista Projects: Duplicate + A = fuente (amarillo, parpadea), Duplicate + B = copia.", pads={1: ("blue", ""), 2: ("blue", ""), 5: ("yellow", "A"), 7: ("yellow", "B"), 4: ("white", "cargado")},
          buttons={"Projects": "white", "Duplicate": "white"}, view="Projects")])

# ===== B. Controles expuestos
sec("patches-entre-packs", "A", "Patches del sinte propio a otro pack",
    ["**Desde RC2.** En la vista Preset de MIDI 1 / 2: **Duplicate + hueco A**, carga otro pack y **Duplicate + hueco B** copia el patch (motor, parámetros y nombre)."],
    """
- **Duplicate + hueco A** con el pack de origen cargado: el patch queda recordado.
- Carga el otro pack y vuelve a la vista Preset de MIDI 1 / 2: **Duplicate se enciende en amarillo** (hay un patch esperando).
- **Duplicate + hueco B** lo escribe ahí. Sirve para varios huecos.
- Dentro del mismo pack, Duplicate + A + B sigue intercambiando los dos patches.
- No copia si A está vacío o si el pack de destino no tiene ese banco de patches.
- En la versión más segura (RC2S) no escribe en la SD: el LED de Save se pone rojo.
""")

sec("knobs-drums", "B", "Knobs de los drums según el panel",
    ["Cada knob hace lo que dice su etiqueta, con una segunda capa en Shift: ring mod, envolventes, filtros (DJ, BP, notch, comb, tilt), LFO, start point, bitcrush y distorsión."],
    """
| Knob | Solo | Con Shift |
|---|---|---|
| K1 Oscillator | Pitch (semitonos exactos; **desde RC2**: el de stock, continuo, con la vista cromática encima) | Cantidad de la envolvente de tono |
| K2 Osc mod | Frecuencia del ring mod | Cantidad del ring mod |
| K3 Amp envelope | Izquierda: decay; pasado el máximo, **ataque** (centro neutro) | Izquierda: **inicio** del sample; derecha: **corte** (centro = entero) |
| K4 Filter envelope | Envolvente → corte | Forma de la envolvente |
| K5 Filter frequency | Filtro / EQ (por defecto, el EQ tilt de stock) | **Modo de filtro**: EQ tilt de stock (por defecto), paso banda, notch, comb, DJ |
| K6 Resonance | Resonancia | — |
| K7 Modulation | Cantidad del LFO | Velocidad del LFO |
| K8 FX | Distorsión; a la izquierda de 0, **bitcrush** | **Tipo de distorsión**: stock, suave, dura, plegada |

- El brillo del LED enseña el valor; Clear + knob restablece las dos capas.
- Todo se guarda con el proyecto y tiene NRPN (E4).
""", [fig("Knobs de un drum.", knobs={1: "Pitch", 2: "Ring", 3: "Decay", 4: "Env→F", 5: "Filtro", 6: "Reso", 7: "LFO", 8: "Dist"}, buttons={"Drum 1": "white"}, view="Drum")])

sec("rev-delay", "B", "Parámetros de reverb y delay",
    ["Vista FX, **Shift + knob**: reverb (tipo, decay, damping) y delay (time, sync, feedback, width, ratio, slew); se guardan con el proyecto."],
    """
- En la vista FX, con Octave ▲ (delay) u Octave ▼ (reverb), **Shift + knob** ajusta el efecto global.
- Reverb: K1 tipo, K2 decay, K3 damping. Delay: K1 time, K2 sync, K3 feedback, K4 width, K5 ratio, K6 slew.
- El LED enseña el valor con el brillo.
""")

sec("sidechain-comp", "B", "Sidechain y compresor master con los knobs",
    ["**Desde RC2.** En la vista Sidechain (**Shift + FX**): **K1-K4** = ataque, hold, decay y profundidad del sidechain de la pista elegida; **K7 / K8** = ataque y release del compresor master."],
    """
- **K1-K4** actúan sobre la pista del último preset de sidechain que tocaste (Synth 1 si no has tocado ninguno); sus LEDs llevan el color de esa pista. Un pad de preset sigue escribiendo sus cuatro valores.
- **K7** = ataque y **K8** = release del compresor master (el que se activa en Advanced Setup), en blanco con su valor. El umbral y la ratio son fijos.
- El ataque y el release del compresor se guardan con el proyecto (ver «Master FX desde RC2»).
- **Desde RC2:** en las páginas de drums (Octave ▼), **K1-K4** = ataque, hold, decay y profundidad del sidechain del drum del último preset tocado, en el color del drum; se guardan con el proyecto y un preset los vuelve a los suyos.
""")

sec("grabar-interno", "B", "Grabar los ruteos internos de MIDI",
    ["**Desde RC2.** En la vista Setup, **Record** decide si lo que una pista MIDI manda a un sinte interno por el canal compartido se graba también en ese sinte: **amarillo = sí**, apagado = no (por defecto)."],
    """
- Cuando MIDI 1 / 2 comparte canal con Synth 1 / 2, lo que tocas o giras en la pista MIDI suena en el sinte sin cable. Por defecto eso **no** se graba en el patrón del sinte, solo en el de la pista MIDI.
- Con **Record en amarillo** (vista Setup, no Advanced Setup) se graba también en el sinte, como si llegara por MIDI externo: sirve para grabar en tiempo real cambios de escala u octava hechos desde la pista MIDI.
- Se desactiva al apagar el aparato. Con el toggle activado también se graban las escuchas del step-drummer de Synth 1 / 2.
""")

sec("midi-io", "B", "MIDI para todo lo nuevo",
    ["Los valores nuevos salen y entran por MIDI: CC / NRPN del motor de las pistas MIDI, NRPN de los drums (MSB 5-8) y de Master FX (MSB 9, canal 16)."],
    """
- Motor de las pistas MIDI: CC de stock donde la función coincide y NRPN 4:código para el resto, por el canal de la pista.
- Drums: NRPN MSB 5-8 = Drum 1-4, LSB 1-12, por el canal de drums.
- Master FX: NRPN MSB 9, LSB = 4 × conjunto + knob, canal 16.
- Respetan los filtros CC Tx / Rx del Setup. Tablas completas en E4.
""")

sec("automatizacion", "B", "Automatización del motor MIDI",
    ["Con Record + Play, los 8 valores de la página 4 del motor MIDI se graban en los carriles de macros del patrón."],
    """
- Página 4 del motor (pad 4 de la fila de páginas): TUNE, Release, Env → nivel, Env → filtro, Filtro, Resonancia, Velocidad del LFO, Cantidad de efecto.
- Grabando, mover esos knobs graba su movimiento; al reproducir, el patrón los mueve.
- Con el step-drummer activado, el carril de TUNE lo usa la fila de pitch.
""")

sec("setup", "B", "Setup y MIDI del aparato",
    ["Canal 16 Rx / Tx (pad 16), canales compartidos, **loopback interno** sin cable y **retornos de reverb / delay por las tiras 3 / 4** (pads 22 / 23, en crema / melocotón como la reverb y el delay de la vista FX).",
     "**Desde RC2:** MIDI Thru con cuatro modos (Duplicate en Advanced Setup): Thru, Out 2, **Merge** (DIN In + el MIDI del aparato) y **Filter** (DIN In sin los canales en escucha).",
     "**Desde RC2:** canales de **Program Change** propios: pad 29 / 30 enseñan y eligen el canal de escucha / salida (16 por defecto); lo recibido se reenvía por el de salida.",
     "**Desde RC2:** **metrónomo con cuenta atrás**: Shift + Clear recorre sin metrónomo, metrónomo, solo cuenta atrás y las dos; la cuenta atrás es un compás antes de grabar."],
    """
| Dónde | Función |
|---|---|
| Setup, pad 16 | Canal 16 (proyecto y FX): recepción y envío |
| Setup, pad 22 | El retorno de reverb pasa por la tira 3 del mixer |
| Setup, pad 23 | El retorno de delay pasa por la tira 4 |
| Setup, canales | MIDI 1 / 2 pueden usar un canal que ya tenga otra pista |
| Advanced Setup, Duplicate | MIDI Thru: Thru → Out 2 → **Merge** → **Filter** (**desde RC2**) |
| Setup, pad 29 / 30 | Canal de escucha / salida de los Program Change del proyecto (**desde RC2**) |
| Cualquier vista, Shift + Clear | Metrónomo: sin / con / solo cuenta atrás / cuenta atrás y metrónomo (**desde RC2**) |

- **Loopback interno:** si una pista MIDI comparte canal con un sinte o los drums, lo que envía les llega por dentro.
- Los pads 22 / 23 se iluminan en crema (reverb) y melocotón (delay), los colores de la vista FX; tenues = apagados.

### Metrónomo y cuenta atrás (desde RC2)
**Shift + Clear**, en cualquier vista, recorre cuatro estados (el original solo encendía y apagaba el metrónomo):

| Estado | LED de Clear con Shift pulsado |
|---|---|
| Sin metrónomo | rojo |
| Metrónomo | verde |
| Solo cuenta atrás | magenta |
| Cuenta atrás y metrónomo | cian |

- Con la cuenta atrás, **Record armado y Play desde parado**: suena un compás de cuenta atrás (4 clics, el sonido del metrónomo de stock, al tempo del proyecto) con Record parpadeando en rojo; después arranca la grabación. **Play** durante la cuenta la cancela.
- Sin Record armado, Play arranca al momento, como siempre.
- El metrónomo es el ajuste de stock; la cuenta atrás se guarda con el proyecto.
- **Volumen del clic:** el de stock, pulsando **Tempo/Swing** y girando **K5**.

### MIDI Thru: Merge y Filter (desde RC2)
El original solo deja elegir el jack Thru como **Thru** (copia del DIN In por hardware, Duplicate rojo tenue) o **Out 2** (segunda salida MIDI, verde). Duplicate en la vista Advanced Setup ahora pasa por cuatro modos:

| Modo | LED de Duplicate | Sale por el jack Thru |
|---|---|---|
| Thru | rojo tenue | El DIN In, por hardware |
| Out 2 | verde | El MIDI del aparato |
| **Merge** | amarillo | El DIN In y el MIDI del aparato |
| **Filter** | azul | El DIN In salvo los mensajes de los canales en los que escucha el aparato |

- El SysEx del DIN In no se copia en Merge / Filter. En Merge, si el aparato sigue el reloj del DIN In y tiene Clock Tx, el jack Thru lleva dos relojes: desactiva Clock Tx.
- Se guarda en los ajustes. Con el firmware original, Merge / Filter vuelven a Out 2.

### Canales de Program Change (desde RC2)
En la vista Setup (no en Advanced Setup):

1. **Pad 29 (PGM Rx)**: los pads 1-16 enseñan el **canal de escucha** (blanco = el elegido, blanco tenue = el resto). Ese primer toque no cambia PGM Rx.
2. Toca un pad de canal para elegirlo.
3. **Pad 29 otra vez** = PGM Rx encendido / apagado, como siempre.
4. **Pad 30 (PGM Tx)**: lo mismo con el **canal de salida**.
5. Un botón de pista u otro pad: los pads 1-16 vuelven a los canales de las pistas.

- Por defecto los dos son el **16**, como el original. Se guardan en los ajustes; con el firmware original vuelven a 16.
- **Recibir** (PGM Rx): un Program Change en el canal de escucha elige el proyecto. Si el canal de escucha no es el 16, el 16 ya no elige proyectos. Si coincide con el de Synth 1, Synth 2 o los drums, va a esa pista.
- **Reenviar**: con PGM Tx, lo recibido en el canal de escucha sale otra vez por el canal de salida.
- **Enviar** (PGM Tx): el proyecto elegido en el panel manda su Program Change por el canal de salida. Los CC del proyecto siguen en el 16.
- En Setup, Synth 1 / 2 eligen su pista también si entraste en Setup desde su vista (antes llegaban como Preset).
- El patch flip (B8) sigue saliendo por el canal de su pista MIDI, nunca por el canal de salida general.
""", [fig("Setup: pad 22 = retorno de reverb por la tira 3 (crema), pad 23 = retorno de delay por la tira 4 (melocotón).",
          pads={16: ("white", "Ch 16", True), 22: ("cream", "Rev\n→ 3"), 23: ("peach", "Dly\n→ 4", True)}, view="Setup")])

sec("patch-flip", "B", "Patch flip en MIDI 1 / 2",
    ["Pad 26 de la vista Preset de MIDI: cada nota se envía como Program Change (excluyente con el motor de la pista)."],
    """
- Vista Preset de MIDI 1 / 2, **pad 26**: las notas de la pista mandan Program Change.
- Se apaga al encender el motor de la pista (pad 27), y viceversa.
""")

# ===== C. Nuevos modos de control
sec("motor-midi", "C", "Motor de las pistas MIDI (pad 27)",
    ["El pad 27 de la vista Preset de MIDI 1 / 2 elige el motor: apagado → **línea** → **oscilador** → **VA-drum** → **granular** → **muestra** (desde RC2) → **secuenciador de efectos**.",
     "Los pads 1-5 eligen la página de knobs; 28 = dos osciladores, 29 = orden de la cadena, 30 = step-drummer, 31 = velocity (VA-drum). **Desde RC2:** Clear + un pad de página = los valores de esa página a los iniciales; las filas 2-3 guardan patches (A14)."],
    """
Cada pista MIDI tiene un «sinte» propio: la **entrada de audio** de la pista (línea 1 para MIDI 1, línea 2 para MIDI 2) o un **motor interno** pasa por VCA, efecto y filtro, con envolvente y LFO, antes de la tira 3 / 4 del mixer. Lo disparan las notas de la pista. La pista sigue mandando su MIDI.

### Estados del pad 27

| Color | Motor |
|---|---|
| apagado | los knobs son los macros MIDI normales |
| amarillo | **entrada de línea** por el VCA-VCF |
| verde | **oscilador** (D3) |
| rojo | **VA-drum** (D4) |
| magenta | **granular** (D5) |
| cian | **muestra**: un sample del pack de un golpe, a la altura de la nota (C15, desde RC2) |
| azul | **secuenciador de efectos** (C3) |

### Pads de la vista Preset

| Pad | Función |
|---|---|
| 1-5 | Página de knobs: 1 VCA-VCF, 2 OSC 1 (granular en ese motor), 3 OSC 2, 4 secuenciables, 5 modulación |
| 25 | Editor de CC (A10) |
| 26 | Patch flip (B8) |
| 27 | Motor |
| 1-5 | Página de knobs. **Clear + el pad** (desde RC2): los valores de esa página (con y sin Shift) vuelven a los iniciales; el motor no cambia |
| 28 | Uno / dos osciladores (solo con los osciladores o VA-drum; apagado en los demás motores) |
| 29 | Orden de la cadena: VCA → FX → filtro / filtro → VCA → FX (**desde RC2**: Shift + 29 = gate retrigger; apagado = legato) |
| 30 | Step-drummer (C2) |
| 31 | Solo en VA-drum: la velocity escala las envolventes de pitch y filtro |

### Página 1 — VCA-VCF

| Knob | Solo | Con Shift |
|---|---|---|
| K1 | Ataque | Sustain |
| K2 | Release | Decay |
| K3 | Envolvente → nivel | LFO → nivel |
| K4 | Envolvente → filtro | LFO → filtro |
| K5 | Filtro | Tipo de filtro (DJ, LP 12, HP 12, BP, notch, LP 24, HP 24) |
| K6 | Resonancia | Gain del VCA (hasta +18 dB con saturación) |
| K7 | Velocidad del LFO | — |
| K8 | Cantidad de efecto | Tipo de efecto (suave, dura, plegado, wavefold, ring, comb, chorus) |

Los knobs de tipo: color = tipo, brillo = posición dentro del tipo.

### Página 2 — OSC 1 (con el oscilador / VA-drum)

| Knob | Solo | Con Shift |
|---|---|---|
| K1 | TUNE | FINE |
| K2 | SHAPE | MIX OSC 1 ↔ OSC 2 |
| K3 | Envolvente → tono | BITSYNC |
| K4 | Envolvente → forma | — |
| K5 | LFO → tono | — |
| K6 | LFO → forma | — |
| K7 | WAVE (morph seno → triángulo → sierra → cuadrada) | — |
| K8 | LFO → morph | Envolvente → morph |

Página 3 (OSC 2): K1 TUNE 2 / FINE 2, K2 SHAPE 2 / FM, Shift + K3 RING, K7 WAVE 2 (**desde RC2**: los ocho sin Shift, K1 TUNE 2, K2 SHAPE 2, K3 MIX, K4 FM, K5 FINE 2, K6 BITSYNC, K7 WAVE 2, K8 RING). Página 4: los 8 valores secuenciables (B6). Página 5: ADSR arriba, LFO abajo (**desde RC2**: Shift + K8 = forma del LFO, seis formas).

- Los valores del motor se guardan en el aparato (no con el proyecto); los del OSC 2, los knobs con Shift del granular y del oscilador y los pads 28 / 29 también desde Beta 1.28 (antes volvían a los iniciales al encender).
""", [fig("Vista Preset de MIDI 1 con el oscilador (pad 27 verde): fila de páginas y pads del motor; el pad 28 solo se ve con oscilador o VA-drum.",
          pads={1: ("orange", "VCA\nVCF"), 2: ("green", "OSC1", True), 3: ("teal", "OSC2", True), 4: ("yellow", "Sec.", True), 5: ("magenta", "Mod.", True),
                25: ("magenta", "CC", True), 26: ("yellow", "Flip", True), 27: ("green", "Motor"), 28: ("green", "2 osc", True), 29: ("yellow", "Orden", True),
                30: ("purple", "Step\ndrum", True), 31: ("teal", "Vel", True)},
          knobs={1: "Ataque", 2: "Release", 3: "Env→A", 4: "Env→F", 5: "Filtro", 6: "Reso", 7: "LFO", 8: "FX"}, buttons={"MIDI 1": "orange", "Preset": "white"}, view="Preset de MIDI 1")])

sec("step-drummer", "C", "Step-drummer",
    ["Secuenciación por **pares de pasos** sobre el patrón: pads 1-16 pasos, 17-24 destino / macro, los 8 knobs = los 8 pares (pitch u velocity).",
     "MIDI: vista Preset, pad 30. Sintes: vista de la fuente, pad 30. Grabando, los pasos tocados se graban en tiempo real."],
    """
### Entrar y salir

| Pista | Cómo se abre |
|---|---|
| MIDI 1 / 2 | Vista Preset con el motor encendido, **pad 30** |
| Synth 1 / 2 | Vista de la fuente (botón del sinte dos veces), **pad 30** |

- Pad 30 brillante = vista abierta; tenue = cerrada. En MIDI, **Shift + pad 30** desactiva el step-drummer. **Desde RC2:** en MIDI, tenue = desactivado, brillante = activado.

### Controles

| Control | Función |
|---|---|
| Pads 1-16 | Los 16 pasos de la mitad mostrada; brillante = hay nota, blanco = el que suena. Tocar = escuchar; **Shift + tocar** = poner / quitar la nota |
| Pads 17-24 | Destino de la fila de pitch (MIDI) / macro 1-8 (sintes) |
| K1-K8 | Los 8 pares de pasos (el que suena, blanco) |
| Octave ▲ / ▼ | Página pitch / velocity |
| 1-16 / 17-32 | La otra mitad del patrón |

- **Pitch en MIDI:** el valor del par desplaza el destino: tono de los dos osciladores, tono del OSC 2, WAVE, FM, MIX, env → filtro, SHAPE, decay (64 = sin cambio: suma o resta al valor de la página del motor; **desde RC2**: el LED del knob tenue en el centro y más brillante cuanto más se aleja).
- **Pitch en los sintes:** el valor es la posición del macro, escrita como automatización.
- Cada paso conserva la altura de su primera nota; una nota nueva toma la del par o la anterior.
- **Grabación en tiempo real:** con Record activo, tocar un paso también lo graba en el paso que suena, con su micropaso.

### Página 2 y toggle pitch-vel (desde RC2)

- **Página velocity, pads 17-24** = destino propio de la página 2 (el mismo pad otra vez = ninguno). Con destino, los knobs escriben el valor del par (MIDI: desde 64, en el carril de REL, que con el step-drummer activado no se reproduce ni se graba; sintes: la automatización de ese macro, desde 0). Sin destino ni toggle, la página 2 no hace nada.
- **Pad 32** = toggle **pitch-vel** (verde): además de sus destinos, la página pitch transpone cada nota de la pista un grado de la escala del proyecto (la de stock o la propia) cada 8 pasos del knob (MIDI −8 … +8 desde el centro, sintes 0 … +16 desde 0) y la página velocity cambia también la velocity, como antes. Con el toggle, los destinos de tono de la página pitch no mueven el sinte propio. Se guarda con el proyecto.
- En los sintes un par vacío empieza en 0.
""", [fig("Vista del step-drummer (MIDI 1).", pads={**{n: (("yellow" if (n - 1) // 2 % 2 == 0 else "red"), "", n not in (1, 2, 5, 9, 13)) for n in range(1, 17)}, 7: ("white", "▶"),
                                                     **{n: ("green", ["Tono", "OSC2", "WAVE", "FM", "MIX", "Env F", "SHAPE", "DEC"][n - 17], n != 17) for n in range(17, 25)}},
          knobs={k: f"par {k}" for k in range(1, 9)}, buttons={"Oct ▲": "yellow", "Oct ▼": "grey", "1-16 / 17-32": "grey"}, view="Step-drummer")])

sec("fx-seq", "C", "Secuenciador de efectos",
    ["Estado **azul** del pad 27: el step-drummer de la pista elige, en cada par de pasos, **un hueco de la fila inferior de Master FX** (0 = nada); suena en los pasos con nota.",
     "El knob avanza despacio (**un hueco cada ~48 pasos de giro**) y se ilumina con el **color del efecto** elegido. **Un hueco sin efecto asignado no hace nada:** asigna antes los efectos a la fila inferior de Master FX (ver «Fila inferior asignable»). **Desde RC2:** al final del recorrido está el valor **random** (LED blanco): en cada paso con nota suena uno de la lista al azar (los huecos con efecto asignado y el gesto mecánico del pad 31)."],
    """
1. En MIDI 1 / 2, pasa el **pad 27** a **azul**. Se activa el step-drummer de la pista.
2. Abre la vista con el **pad 30**. Pon notas en los pasos con **Shift + pad**.
3. Cada **knob** (un par de pasos) elige un hueco de la fila inferior de Master FX:

| Valor | Hueco |
|---|---|
| 0 | nada |
| 1 | pad 26 |
| 2 | pad 27 |
| 3 | pad 28 |
| 4 | pad 29 |
| 5 | pad 30 |
| 6 | pad 31 (el Glitch) |

4. Con el secuenciador en marcha, en cada paso con nota se enciende lo que tenga ese hueco: un efecto (con su copia de parámetros) o el Glitch. El LED del knob toma el color de ese efecto; apagado = nada.

- Asigna antes los efectos a la fila inferior en Master FX (C7).
- La pista no suena en el DSP; sus notas siguen saliendo por MIDI.
- Al salir del estado azul, el step-drummer de la pista se apaga.
""", [fig("Secuenciador de efectos: cada knob = el hueco de la fila inferior de Master FX para su par de pasos.",
          pads={1: ("yellow", ""), 3: ("yellow", ""), 4: ("yellow", ""), 9: ("red", ""), 11: ("red", ""), 27: ("blue", "FX seq"), 30: ("purple", "Step\ndrum")},
          knobs={1: "Gater", 2: "nada", 3: "Phaser", 4: "Glitch", 5: "nada", 6: "Vinyl", 7: "nada", 8: "Glitch"}, buttons={"MIDI 1": "orange", "Play": "green"}, view="Secuenciador FX")])

sec("song-pointer", "C", "Song pointer (Master FX)",
    ["Pads 9-24 = pasos 1-16: un paso mantenido = retrigger; dos pasos = frase momentánea; Shift + dos = frase fijada.",
     "**Modo frase:** Shift + paso = inicio (fin 16); un toque = el fin; Shift + otro paso = nuevo inicio; Shift + el inicio o el pad 9 blanco = salir."],
    """
- **Un paso mantenido:** retrigger, el paso se repite mientras lo mantienes.
- **Dos pasos mantenidos:** el patrón hace bucle entre ellos mientras los mantienes.
- **Shift + dos pasos:** frase fijada; el pad 9 se ve blanco y tocarlo la quita.
- **Modo frase (SC34.2):** Shift + un paso entra en el modo con ese paso como inicio y el 16 como fin. En el modo, tocar un paso cambia el fin (sin retrigger); Shift + otro paso cambia el inicio; Shift + el inicio o el pad 9 blanco sale.
- El cabezal se ve en blanco mientras el secuenciador corre. Al cargar un proyecto empieza apagado.
""", [fig("Song pointer: frase entre los pasos 3 y 10.", pads={**{n: ("grey", str(n - 8), True) for n in range(9, 25)}, 11: ("yellow", "inicio"), 18: ("yellow", "fin"), 9: ("white", "salir")},
          view="Song pointer")])

sec("sample", "C", "Sample capturado",
    ["**Pad 32** (rojo) graba la salida; **pad 7** (amarillo) la toca: K1 pitch, K2 modo (one-shot / gate / loop por color), K3 start, K4 end.",
     "El sample se asigna a la fila inferior (pad 7 + pad de abajo) y puede sustituir a un drum (A9)."],
    """
### Grabar (pad 32, Master FX y vista FX)
- **Mantener:** graba mientras se mantiene (hasta 3,46 s).
- **Pulsación corta:** graba hasta la siguiente pulsación.
- **Efectos de Master FX (desde RC0.5):** el sample que suena pasa por los efectos de Master FX; la captura graba la salida sin ellos (en RC0-RC0.4 era al revés: la captura llevaba los efectos y el sample sonaba sin ellos).
- **Shift + pad 32:** armado: con el transporte en marcha graba el compás siguiente; parado, empieza al pulsar **Play**, desde el primer pulso, y graba ese compás (desde RC0.4; antes empezaba un compás tarde).

### Tocar (pad 7)
- Pulsa el **pad 7**: suena y sus knobs pasan a K1-K4: **K1** pitch (±24 semitonos), **K2** modo (amarillo one-shot, verde gate, azul loop), **K3** start, **K4** end (end < start = al revés).
- **Shift + pad 7:** bucle **enganchado**, en cualquier modo, hasta que vuelvas a pulsar el 7 (o el pad 8); igual con Shift + un hueco del sample (desde RC0.4; en RC0-RC0.3 sonaba solo mientras se mantenía).
- El modo **loop** (K2 azul) es otra cosa: suena solo mientras mantienes el pad y para al soltarlo.

### Asignar
Mantén el pad 7 y toca un pad de la fila inferior: ese hueco toca el sample con una copia de sus knobs.
""", [fig("Sample capturado.", pads={7: ("yellow", "Tocar"), 32: ("red", "Grabar"), 27: ("yellow", "sample", True)}, knobs={1: "Pitch", 2: "Modo", 3: "Start", 4: "End"}, view="Master FX")])

sec("glitch-pad", "C", "Glitch (pad 31) y su asignación",
    ["**Mantén el pad 31** (Master FX o vista FX): la salida se rompe y se retrasa como una cinta. K1 velocidad, K2 repetición, K3 retraso, K4 caos (mitad de abajo) o sobrecarga (mitad de arriba).",
     "**Pad 31 mantenido + otro pad de la fila inferior** = ese hueco también es un Glitch, con su copia de K1-K4."],
    """
- **Mantener el pad 31:** la salida master se sustituye por una cabeza de cinta que lee el audio reciente (D6). Al soltar vuelve el audio normal.
- Al pulsarlo en Master FX, K1-K4 son sus parámetros:

| Knob | Función |
|---|---|
| K1 | Velocidad: arriba del todo = normal; al bajar frena como una cinta; en el centro, parada; por debajo, hacia atrás |
| K2 | Tamaño de la repetición; al máximo, sin repetición (retraso continuo) |
| K3 | Retraso, hasta unos 2,6 s |
| K4 | Mitad de abajo: **caos** (saltos atrás, cortes y cambios de sentido al azar). Mitad de arriba: **sobrecarga** — bloques que llegan tarde (se repiten 32 muestras y luego se recupera: chasquidos con el tono normal); desde ~3/4 del recorrido además frena: todo más grave y lento, como el DSP sobrecargado (desde RC0.2) |

- **Asignar:** mantén el pad 31 y toca otro pad de la fila inferior (sin Shift): ese hueco guarda un Glitch con la copia actual de K1-K4 y se ilumina en turquesa. Tocar ese hueco lo hace sonar con sus valores.
- **Dos huecos con Glitch a la vez:** suena el último que pulsas; al soltarlo vuelve el otro con sus valores. Ninguno copia los valores del otro (en RC0, pulsar uno mientras sonaba otro le copiaba los knobs).
- El pad 31 se ilumina mientras el Glitch suena.
""", [fig("Glitch: pad 31; asignado también al pad 28.", pads={31: ("teal", "Glitch"), 28: ("teal", "Glitch", True)}, knobs={1: "Veloc.", 2: "Repet.", 3: "Retraso", 4: "Caos"}, view="Master FX")])

sec("fila-inferior", "C", "Fila inferior asignable (Master FX / FX)",
    ["Mantén un efecto de arriba (o el pad 7, o el pad 31) y toca un pad de abajo: ese hueco guarda el efecto con una copia de sus parámetros. Se guarda con el proyecto."],
    """
- **Pads 26-30** (y el 31 como Glitch): huecos asignables. Un hueco sin asignar es el efecto de actuación de la vista FX de stock.
- **Asignar:** mantén el efecto de arriba (pads 1-6), el pad 7 (sample) o el pad 31 (Glitch) y toca el hueco.
- **Tocar el hueco:** carga su copia de parámetros y activa el efecto mientras se mantiene. **Shift + hueco** lo fija.
- Las asignaciones van con el proyecto y vuelven al encender; al cambiar de sesión se mantienen las de la RAM.
- El secuenciador de efectos (C3) dispara estos huecos.
""")

sec("random-mutate", "C", "Random-mutate por paso",
    ["**Desde RC2.** En la vista de probabilidad (**Shift + Pattern Settings**) la fila 4 da a cada paso una probabilidad de que sus notas salten de octava o cambien a otra nota de la escala al sonar."],
    """
1. En Synth 1 / 2 o MIDI 1 / 2, pulsa **Shift + Pattern Settings**: la vista de probabilidad del original. La fila 3 sigue siendo la probabilidad de que el paso suene.
2. Mantén un paso con notas y toca un pad de la **fila 4** (melocotón):

| Pad | Octava | Escala |
|---|---|---|
| 25 | — (apagado) | — |
| 26 | 6 % | — |
| 27 | — | 6 % |
| 28 | 6 % | 6 % |
| 29 | — | 12 % |
| 30 | 12 % | — |
| 31 | — | 25 % |
| 32 | 25 % | 50 % |

- **Escala:** la nota cambia a otra nota de la escala del proyecto, dentro de la misma octava. **Octava:** sube o baja una octava (al azar). Cada nota de un acorde se sortea por separado, cada vez que el paso suena.
- **Sin Record** la nota cambiada suena esa vez y el paso no cambia. **Con Record** la nota cambiada se escribe en el paso (la secuencia va derivando).
- Las notas ligadas (tie) no se cambian.
- El valor se guarda en el paso, con el patrón y el proyecto. Los drums no lo tienen.
""", [fig("Vista de probabilidad: fila 3 = probabilidad del paso (original), fila 4 = random-mutate.",
          pads={1: ("red", "paso"), **{16 + k: ("blue" if k < 5 else "green", "") for k in range(1, 9)},
                25: ("peach", "off"), 26: ("peach", "oct\n6", True), 27: ("peach", "esc\n6", True), 28: ("peach", "oct 6\nesc 6", True), 29: ("peach", "esc\n12", True),
                30: ("peach", "oct\n12", True), 31: ("peach", "esc\n25", True), 32: ("peach", "oct 25\nesc 50", True)},
          buttons={"Pattern\nSettings": "white", "Shift": "grey"}, view="Probabilidad")])

# ===== D. DSP
sec("frecuencia-dinamicas", "C", "Frecuencia y dinámicas por paso",
    ["**Desde RC2.** En la vista de probabilidad de las pistas de notas: **fila 4 = cada cuántas vueltas del patrón suena el paso** (1-8). Con el **pad 25 de Pattern Settings**: fila 3 = **dinámicas** aleatorias (velocity, posición y duración), fila 4 = random-mutate."],
    """
- **Modo 1** (pulsa **Pattern Settings** dos veces): fila 3 = la probabilidad de siempre; **fila 4 = frecuencia**, en amarillo: con n el paso suena en la última de cada n vueltas del patrón. Cada patrón cuenta sus vueltas desde Play.
- **Modo 2** (**pad 25** de la vista Pattern Settings): fila 3 = dinámicas, fila 4 = random-mutate.
- **Clear + pad 25** (desde RC2): borra las dinámicas y el random-mutate de todos los pasos del patrón; la frecuencia se queda.

| Pad (fila 3) | Micropasos (posición y duración) | Velocity | |
|---|---|---|---|
| 1 | — | — | sin cambios |
| 2 | −2 a +2 | — | drunk |
| 3 | −2 a +2 | 0 a +32 | drunk y acentos |
| 4 | — | 0 a +32 | acentos |
| 5 | −1 a +3 | 0 a +32 | arrastre y acentos |
| 6 | −1 a +3 | — | arrastre |
| 7 | — | −32 a +32 | dinámica equilibrada |
| 8 | — | −32 a +64 | dinámica de acentos |

- Todo se guarda con el paso. Con **Record** y el modo 2 en pantalla, lo que suena (la nota mutada, la dinámica) se escribe en el patrón.

### En los drums (desde RC2)

- La misma vista para un drum (Pattern Settings dos veces = modo 1; pad 25 de su Pattern Settings = modo 2): fila 4 del modo 1 = frecuencia; modo 2: fila 3 = dinámicas (solo retrasan el golpe dentro de su paso), pads 25-28 = **random-mutate del sample**: nada, 25 % de ±1 (el de al lado en su fila de 8), 25 % de ±8 (otra fila), 12 % de cada uno.
- Van en bytes del patrón que el stock no usa: viajan al duplicar y con Nudge; la primera vez se limpian en los 32 patrones de drum del proyecto.
""")

sec("cadenas", "C", "Cadenas de patrones y escenas",
    ["**Desde RC2.** Cada patrón puede llevar una regla «suena n veces, luego salta a B; la vez siguiente, a C». **Shift + Octave ▲ / ▼** en la vista Patterns activa / desactiva el **modo cadena** de todo el proyecto; cada escena recuerda el modo con que se guardó."],
    """
- **Modo cadena:** en la vista Patterns, **Shift + Octave ▲** lo activa (Octave ▲ en verde) y **Shift + Octave ▼** lo desactiva. Con Shift pulsado, el Octave que hace algo se ve en amarillo. El modo sigue activo al salir de la vista.
- **Editar una regla** (con el modo activo): pulsa un patrón = **A** (amarillo; se selecciona como siempre). **A otra vez** = una repetición más (hasta 8; los LEDs de los knobs las cuentan). **Otro patrón de la pista** = **B** (verde) y el siguiente = **C** (rojo). Ejemplos: n = 3 → A A A B A A A C; sin C → A A A B; n = 1 → A B A C.
- B y C suenan una vez y la pista vuelve a A (salvo que tengan su propia regla).
- **Clear + patrón** en el modo: quita la regla; si no tiene regla, borra el patrón como siempre. Fuera del modo, Clear borra el patrón, su regla y su orden de reproducción.
- **Con el modo desactivado** las reglas siguen guardadas pero no se aplican: los patrones suenan como en el aparato original.
- **Escenas** (vista Mixer): una escena guardada con el modo cadena activo lo recuerda y se ve en **melocotón**; al cargarla vuelve el modo, y al cargar una escena normal se desactiva. Así se mezclan escenas con cadenas y escenas normales. Las pistas que están siguiendo una regla **parpadean** en el Mixer.
- Una escena termina cuando termina su cadena más larga (al volver de C, o de B si no hay C).
- **Repeticiones de escena:** en el Mixer, **Shift + pads 9-16** fijan 1-8 repeticiones de la escena actual (con Shift la fila se ve en amarillo y la elegida en verde). Durante las repeticiones los mutes son los que hayas dejado y las cadenas siguen por donde iban.
- Las reglas se guardan con el patrón (viajan al duplicarlo); el modo y lo de las escenas, con el proyecto.
""")

sec("nudge-ordenes", "C", "Nudge y órdenes de reproducción",
    ["**Desde RC2.** En la vista Pattern Settings: **pad 26 = Nudge** (el patrón rotado para que el primer paso elegido sea el paso 1), **pad 27 = orden fractal**, **pad 28 = orden deconstruido**. En todas las pistas, drums incluidos."],
    """
- **Nudge (pad 26, naranja):** reescribe el patrón de modo que el primer paso elegido pasa a ser el paso 1; lo que había delante queda al final. Rota los pasos completos con su automatización, sobre 16 pasos (un patrón de hasta 16) o sobre 32. El último paso se mueve con él (pasos 6-13 → 1-8).
- **Fractal (pad 27):** 1 · 1 2 · 1 2 3 · 1 2 3 4 … hasta el último paso, y vuelve a empezar.
- **Deconstruido (pad 28):** las diagonales de la rejilla: 1 6 11 16 · 2 7 12 13 · 3 8 9 14 · 4 5 10 15 (y lo mismo con 17-32). Los pasos de fuera del patrón se saltan: con 8 pasos, 1 6 2 7 3 8 4 5.
- Los pads 27 / 28 y los cuatro de dirección (29-32) se excluyen entre sí y comparten colores.
- El patrón «termina» (para las cadenas, las escenas y la frecuencia) al acabar el recorrido entero.
- El orden se guarda con el patrón. Borrar el patrón con Clear lo quita.
""")

sec("arpegiador", "C", "Arpegiador (desde RC2)",
    ["**Desde RC2.** En la vista Pattern Settings de una pista de notas: **Shift + pad 25** = arpegiador del patrón encendido / apagado, **Shift + pads 27-32** = su orden (fractal, deconstruido, arriba, abajo, ping-pong, aleatorio), independiente de la dirección del patrón."],
    """
- Con Shift, el pad 25 y los pads 27-32 se ven en amarillo y lo elegido en verde; sin Shift, el pad 25 se ve verde mientras el arpegiador está encendido.
- **Secuencia:** cuando en un paso empiezan dos notas o más, suenan una por paso (al sync rate del patrón) en el orden elegido, sobre las notas ordenadas por altura, mientras dura la nota más larga del acorde. Cada nota dura un paso y lleva su velocity. El random-mutate y las dinámicas del paso no se aplican a esas notas.
- **Entrada:** la primera nota suena como siempre; al mantener otra a la vez empieza el arpegio de las notas mantenidas, una por paso (parado, al tempo del proyecto y al sync rate de la pista), hasta soltarlas todas. **Con Record se graba el acorde**: el arpegio lo toca después la secuencia.
- Se guarda con el proyecto, por pista y patrón.
- **Shift + pads 17-24** = resolución propia del arpegio (1/4 … 1/32T, en el orden del sync rate; el mismo pad otra vez = la de la pista). Cada nota del acorde dura su propio gate.
- **Drums** (desde RC2): los mismos gestos en el Pattern Settings de un drum; en su vista Preset, mantener varios samples = el arpegio de los samples (el drum salta de uno a otro), a la rejilla del drum en marcha y al tempo parado; con Record se graba (micropaso y sample flip).
- **Gate por pulsación** (vista Micro Step = Gate dos veces, pad 32, por pista): al introducir notas a mano, el tiempo que mantienes el pad es el gate. **Pad 31** = longitud fija (con los dos apagados abre el selector; elegir una longitud la enciende). Un toggle encendido se apaga al pulsarlo otra vez; pulsar el otro cambia de uno a otro.
""")

sec("rollers", "C", "Rollers de micropasos de los drums (desde RC2)",
    ["**Desde RC2.** Filas 1-3 de la vista Note de los drums: mantener un roller hace sonar su drum en cada paso en ese micropaso (dos columnas por drum, micropasos 1-3 y 4-6), en directo; con el transporte parado, al tempo del proyecto."],
    """
- Cada columna es el drum de su cuadro de abajo (con la copia en espejo: columnas 1-4 = drums 4-1, 5-8 = drums 1-4); tenues en el color del drum, encendidos al mantenerlos.
- Varios a la vez se combinan; con la velocity del paso (100 en un paso vacío); con Record se graban en el patrón.
""")

sec("escala-propia", "C", "Escala propia (desde RC2)",
    ["**Desde RC2.** **Shift + Scales** = editor de una escala propia para las pistas de notas: hasta 7 notas sobre la tónica y un **periodo** cualquiera (hasta 24 semitonos) que es la tónica de la siguiente iteración; cada fila de pads es una iteración (dos con 4 notas o menos). Se guarda con el proyecto."],
    """
- Teclado del editor: dos octavas en piano desde la tónica (filas 4 / 3 la primera octava, blancas / negras; filas 2 / 1 la segunda). La tecla más alta pulsada es el periodo (naranja), las demás las notas (verdes).
- Vale para tocar, iluminar las notas de la secuencia, cuantizar y el random-mutate. Una escala de stock la apaga; el editor la enciende otra vez.
""")

sec("modo-muestra", "C", "Modo muestra de las pistas MIDI (desde RC2)",
    ["**Desde RC2.** Un estado nuevo del pad 27 (cian, tras el granular): la pista MIDI toca **un sample del pack de un golpe**, a la altura de la nota (**C3 = nota 60 = como se grabó**), por el filtro, el efecto y el LFO del motor; el VCA se queda abierto y el sample suena entero.",
     "La **vista Note ampliada** (Note dos veces) es el selector: filas 3-4 = 16 samples × 4 páginas (Octave ▼ / ▲: los 64 del pack), filas 1-2 = los pasos; **paso mantenido + sample** = sample flip de ese paso, también en vivo con Record."],
    """
- **Elegir el sample:** en la vista Note ampliada, filas 3-4 = 16 samples del pack; **Octave ▼** = página siguiente, **▲** = anterior (4 páginas, los 64 samples; el botón se enciende si hay más páginas en ese sentido). Tocar un sample = el de la pista (cian) y suena (nota 60). Es el mismo valor que la fuente del granular (Shift + K8 en su página): cambiar uno cambia el otro; la captura se elige desde allí.
- **Sample flip:** filas 1-2 = los 16 pasos de la mitad mostrada (**1-16 / 17-32** = la otra mitad). **Mantén un paso y toca un sample** = ese paso toca ese sample (melocotón; el paso mantenido verde, su sample amarillo); **Clear + paso** = sin flip (cian tenue, el fondo de las filas 1-2). El paso que suena, blanco. Un flip en un paso sin nota no hace nada.
- **En vivo:** con **Record + Play**, tocar un sample graba una nota 60 en el paso que suena y su flip.
- **La altura** la dan las notas de la pista (la vista Note normal, el step-drummer, el MIDI de entrada): C3 = como se grabó, una octava arriba = el doble de rápido. Una voz por pista, como un drum: cada nota vuelve a empezar el sample; el note-off no lo corta, suena hasta el final.
- **El VCA abierto:** en este modo la envolvente no cierra el VCA (ganancia, velocity y LFO → nivel siguen); los demás motores, como antes.
- **Se guarda:** el sample de la pista con los valores del motor (ajustes del aparato); los flips en el patrón: viajan con el patrón y el proyecto. Van en el carril de la automatización de **nivel** de la pista (Mixer): un flip sustituye la automatización de nivel de su paso (la de los demás pasos sigue sonando) y grabar el nivel encima borra los flips de esos pasos.
- Sin el modo muestra, la vista Note ampliada es la de siempre.
""", [fig("Vista Note ampliada de MIDI 1 en modo muestra: pasos arriba, samples abajo.",
          pads={**{n: ("teal", "", True) for n in range(1, 17)}, 4: ("peach", "flip"), 10: ("peach", "flip"), 1: ("white", "suena"),
                **{n: ("grey", "", True) for n in range(17, 33)}, 22: ("teal", "sample")},
          buttons={"MIDI 1": "white", "Note": "white", "Oct ▼": "white", "1-16 / 17-32": "white"}, view="Note")])

sec("master-fx-beta", "C", "Master FX desde RC2: gesto mecánico, Glitch, Digitise y guardado por sesión",
    ["**Desde RC2.** El pad 6 de Master FX es el **Glitch** y el pad 31 un **gesto mecánico** (parada de cinta, scratch…); Digitise gana **K3 = envío momentáneo al delay** y **K4 = envolvente**; los knobs y los huecos de Master FX **se guardan con cada proyecto**."],
    """
- **Pad 6 = Glitch** (sustituye al Vinyl): mantenido, fijado, asignable a los huecos y al secuenciador de efectos como los demás efectos; sus K1-K4 son los del Glitch.
- **Pad 31 = gesto mecánico:** al pulsar, el audio se frena hasta parar; al soltar, arranca. **K1** = movimientos por gesto (1-8), **K2** = tipo, mezclado de forma continua y en colores (parada de cinta → baby scratch → tear → back spin → rattle), **K3** = tiempo de parada, **K4** = tiempo de arranque.
- **Digitise:** K1 muestreo, K2 bits, **K3 = envío al delay mientras mantienes el pad 4** (todas las pistas; al soltar vuelven sus envíos), **K4 = envolvente de la cantidad** (a la derecha: de entero a limpio; a la izquierda: crece).
- **Por sesión:** los 20 knobs de la fila superior, la asignación de los huecos de la fila inferior y el ataque / release del compresor master se guardan al guardar el proyecto y vuelven al cargarlo. Un proyecto que no los tiene (antiguo o nuevo) deja el aparato como esté. Los efectos fijados no se guardan.
""")

sec("efectos-grid", "D", "Efectos de Master FX",
    ["Gater, Auto-Filter LP / HP, Digitise, Phaser y Vinyl sobre la salida master, con 4 parámetros cada uno."],
    """
| Pad | Efecto | K1-K4 |
|---|---|---|
| 1 | Gater | división, profundidad, ancho, suavizado |
| 2 / 3 | Auto-Filter paso bajo / alto | velocidad, profundidad, resonancia, frecuencia central |
| 4 | Digitise | reducción de muestreo, reducción de bits (K3 y K4 no hacen nada) |
| 5 | Phaser | velocidad, profundidad, realimentación, mezcla |
| 6 | Vinyl | crackle, siseo, tono (paso bajo), desgaste (paso alto) |

- Mantener = activo; Shift = fijado. El brillo de los LED de los knobs enseña el valor.
""")

sec("vca-vcf", "D", "VCA-VCF de las pistas MIDI",
    ["Filtros DJ / LP / HP 12 y 24 dB / paso banda / notch, efectos (saturación, plegado, wavefold, ring, comb, chorus), VCA con ADSR y LFO."],
    """
- Cadena por voz: VCA → efecto → filtro, o filtro → VCA → efecto (pad 29).
- Filtro de estado variable con seguimiento de la nota; LP / HP de 24 dB = dos etapas.
- VCA con ADSR, velocity, ganancia hasta +18 dB con saturación suave.
- LFO en rampa inversa hacia nivel, filtro, tono, forma y morph.
- Los valores por defecto dejan pasar la entrada limpia.
""")

sec("osciladores", "D", "Osciladores y parafonía",
    ["Morph continuo seno → triángulo → sierra → cuadrada, wavefold / pendiente / ancho, segundo oscilador con FM, ring, sync suave y modos bit a bit; dos notas parafónicas."],
    """
- **OSC 1:** WAVE es un morph continuo (0 seno, 42 triángulo, 84 sierra, 126 cuadrada); SHAPE pliega el seno / triángulo, curva la sierra o cambia el ancho de la cuadrada. Envolvente y LFO mueven tono, forma y morph.
- **OSC 2 (pad 28):** su propio TUNE / FINE / WAVE / SHAPE; MIX, FM (OSC 2 → fase de OSC 1), RING y BITSYNC (sync suave cada N ciclos, xor, or, nor, and, nand).
- **Parafonía:** una nota = unísono; dos = una por oscilador (**desde RC2**: con un oscilador la última nota manda; al soltarla vuelve la anterior).
""")

sec("va-drum", "D", "Motor VA-drum",
    ["Oscilador pensado para percusión: VCA de un disparo, envolventes de decay propias para pitch (knob Sustain) y filtro (knob Release), ruido blanco y valores aleatorios en lugar del LFO."],
    """
| Knob | En VA-drum |
|---|---|
| Ataque / Decay | ataque y decay del VCA (de un solo disparo) |
| Sustain | decay de la envolvente de pitch |
| Release | decay de la envolvente de filtro |
| Velocidad del LFO | nivel de ruido blanco |
| LFO → destino | valor aleatorio por bloque hacia ese destino |

- Pad 31: la velocity también fija el nivel de las envolventes de pitch y filtro.
- *Bombo:* seno, Decay ~70, Sustain ~30, Env → tono a la derecha. *Caja:* más ruido, Decay corto, paso banda.
""")

sec("granular", "D", "Sinte granular",
    ["Hasta **16 granos por pista** desde cualquier sample del pack o la captura, con interpolación y ventana; en el segundo núcleo del DSP.",
     "K1 tono, K2 posición, K3 scan / freeze, K4 tamaño, K5 densidad, K6 zona, K7 LFO → posición, K8 envolvente → posición; Shift: fino, dispersiones, reverso, ventana, slicer (o stretch, desde RC2), LFO → tamaño, fuente."],
    """
Estado **magenta** del pad 27; **pad 2** de la fila de páginas = página del granular.

| Knob | Solo | Con Shift |
|---|---|---|
| K1 | Tono, ±24 semitonos | Fino, ±1 semitono |
| K2 | Posición en el sample | Dispersión de la posición |
| K3 | Scan: centro = congelado, derecha avanza, izquierda retrocede | Probabilidad de grano al revés |
| K4 | Tamaño del grano, 5-500 ms | Dispersión del tono (±12 st) |
| K5 | Densidad, 1-16 granos solapados | Ventana: rectangular → triangular → percusiva |
| K6 | Longitud de la zona del scan | Modo de nota: tono / slicer / stretch (stretch desde RC2) |
| K7 | LFO → posición | LFO → tamaño |
| K8 | Envolvente → posición | **Fuente**: sample 1-64 del pack, a la izquierda la captura. **Desde RC2:** recorrido largo por cinco zonas: la captura (rojo) y el sample que tiene ahora Drum 1 (naranja), 2 (amarillo), 3 (violeta) y 4 (verde azulado); queda fijado aunque el drum cambie de sample; blanco tenue = ningún drum tiene ya ese sample |

- **Modo tono:** la nota cambia la altura de los granos; con dos notas se reparten entre las dos.
- **Modo slicer:** la nota elige una de 16 porciones del sample.
- **Modo stretch (desde RC2):** el tramo de K2 al final del sample dura **K3** pasos (1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48 o 64; el LED de K3 lo enseña) a cualquier tempo, sin cambiar el tono, y vuelve a empezar alineado con el inicio del transporte; las notas cambian el tono como en el modo tono. Con el transporte parado se queda quieto. K7 / K8 casi no actúan en este modo.
- Pasa por el VCA-VCF de la página 1. Comparte los valores guardados con la página del oscilador.
""", [fig("Página del granular (pad 2, motor magenta).", pads={2: ("green", "Gran."), 27: ("magenta", "Motor")},
          knobs={1: "Tono", 2: "Posición", 3: "Scan", 4: "Tamaño", 5: "Densidad", 6: "Zona", 7: "LFO→pos", 8: "Env→pos"}, buttons={"MIDI 1": "orange"}, view="Granular")])

sec("glitch-dsp", "D", "Motor del Glitch",
    ["Una cabeza de cinta sobre un búfer circular estéreo del master (2,7 s) en la memoria externa del DSP: velocidad variable, repeticiones con fundidos, caos."],
    """
- El master se graba sin parar en un anillo estéreo de 2,7 s.
- Al pulsar, la cabeza empieza en «ahora − retraso» con una entrada gradual corta.
- Velocidad negativa = hacia atrás; cerca de 0 = frenada de cinta.
- Repetición: al acabar cada segmento vuelve a su inicio; al máximo, retraso continuo sin fundidos.
- Caos: saltos aleatorios atrás, silencios y cambios de sentido.
- Sobrecarga (K4 en la mitad de arriba, desde RC0.2): imita lo que se oyó al cargar de verdad la memoria de samples del DSP (SC35DB): en cada bloque de 32 muestras, con una probabilidad que sube con K4, el bloque «llega tarde» (la cabeza vuelve 32 muestras y, en el siguiente bloque tarde, recupera); desde K4 ≈ 96 la cabeza además frena hasta 0,43 ×. Es una simulación: no carga el DSP, así que el secuenciador, el reloj MIDI y el resto del audio no se ven afectados.
""")

sec("drums-dsp", "D", "DSP de los drums",
    ["Ring mod, envolventes de tono y filtro, LFO, filtros DJ / paso banda / notch / comb / tilt, bitcrush, start point, distorsiones y sidechain entre drums."],
    """
- Filtro de estado variable por drum (DJ, paso banda, notch), comb con realimentación y el EQ tilt de stock.
- Ring mod con oscilador propio, LFO trémolo / vibrato, distorsión suave / dura / plegada, bitcrush.
- **Sidechain entre drums:** Shift + FX y Octave ▼: páginas de ducking por drum (filas 3-4) y qué drum dispara (fila 1, pads 5-8). **Desde RC2:** los pads 1-4 de la fila 1 = Synth 1, Synth 2, MIDI 1, MIDI 2 como disparo (cada nota de su patrón).
""")

sec("entradas", "D", "Entradas de audio y retornos",
    ["Entrada de línea (normal o invertida) como fuente de los sintes; retornos de reverb / delay por las tiras 3 / 4 con realimentación."],
    """
- Los sintes pueden usar la entrada 1 / 2 (o invertidas) en lugar del ruido (A6).
- Con los retornos del Setup en las tiras 3 / 4, los envíos de esas tiras vuelven a mandar el retorno, ya procesado por el VCF / FX de la pista, al reverb y al delay.
""")

# ===== E. Miscelánea
sec("guardado", "E", "Qué se guarda y dónde",
    ["Proyecto: drums, huecos de Master FX, fuente de los sintes, parámetros de reverb / delay. Aparato: motor de las pistas MIDI. Volátil: OSC 2, efectos fijados."],
    """
| Qué | Dónde |
|---|---|
| Knobs nuevos de drums, huecos de Master FX, fuente de los sintes, reverb / delay | El proyecto |
| Motor de las pistas MIDI (pad 27, granular, secuenciador), valores de las páginas 1-2, step-drummer activado | Ajustes del aparato |
| Notas y fila de pitch del step-drummer, valores del secuenciador de efectos | El patrón |
| Capturas sustituidas en drums | El pack, al guardar (A8) |
| OSC 2, MIX, FM, RING, parámetros con Shift del granular, efectos fijados, song pointer | No se guardan |
""")

sec("pack-interno", "E", "El pack de la memoria interna: solo lectura",
    ["Nada del mod escribe ni borra en el pack de la memoria interna del Circuit (el primero de la vista de packs). Se puede leer de él y copiar desde él a un pack de la tarjeta, pero no al revés."],
    """
- **Se niega** (el LED de Save se enciende en rojo 1,5 s): guardar el sample capturado con el proyecto, intercambiar o copiar samples y patches hacia el pack interno, guardar patches del sinte o del sinte propio en él, copiar proyectos a él y borrarlo desde la vista de packs.
- **Funciona:** tocar y cargar lo que hay en el pack interno, y copiar de él a un pack de la tarjeta (Duplicate + A en el pack interno, cargar el otro pack, Duplicate + B).
- **No cambia:** los guardados del propio aparato (Save de un proyecto). Lo que el mod guarda dentro del proyecto (cadenas, Master FX por sesión…) va dentro de ese guardado normal, también en la memoria interna. Aun así, con las versiones que no acaban en «S» es mejor no usar la memoria interna para proyectos: es lo que pide el instalador.
- Las versiones «S» no escriben nada por su cuenta en ninguna memoria.
""")

sec("instalar", "E", "Instalar y volver atrás",
    ["`tools/ct_uploader.html` envía el `.syx` por Web MIDI; solo acepta firmwares verificados. Recuperación: Scales + Preset + Note al encender."],
    """
0. **Sin compilar:** `tools/rc_uploader.html` parchea el firmware oficial ([descarga de Novation](https://components.novationmusic.com/api/v2/firmwares/168/file)) en el navegador y lo envía. Elige RC2, RC2S (o las anteriores RC0.9 / RC0.9S) u «Oficial».
1. Abre `tools/ct_uploader.html` en Chrome y conecta el Circuit Tracks por USB.
2. Elige el `.syx` de `firmware/<versión>/`: el uploader comprueba su SHA-256.
3. Envía. El bootloader de Novation no se modifica.
- **Volver atrás:** envía otra versión o el firmware oficial. Si el aparato no arranca: mantén **Scales + Preset + Note** al encender (modo de recuperación del bootloader).
- En la rama RC los `.syx` no se publican: se generan con `tools/patch_official.py` a partir del firmware oficial.
- **RC2** (versión candidata 2, marca `RC2`) = SC44 = RC0.9 + todo lo marcado **desde RC2** en este manual: lo de las betas 1.0-1.30 (gesto mecánico y Glitch en el pad 6, Digitise K3 / K4, Master FX por sesión, knobs del sidechain y del compresor, frecuencia, dinámicas y random-mutate por paso, cadenas de patrones y escenas, Nudge y órdenes de reproducción, patches del sinte propio, arpegiadores, rollers, escala propia, cuenta atrás, modo cue, sidechain desde las pistas de notas, cuantizar, formas del LFO, modo muestra…) y sus arreglos. Gran parte está sin probar en el aparato: úsala con una copia de la SD.
- **RC0.9** (décima versión candidata) = RC0.8 + el pack de la memoria interna, de solo lectura para el mod; RC0.8 = RC0.7 + un arreglo (los knobs de pitch del step-drummer conservan su valor: desde RC0 cada giro escribía solo su incremento); RC0.7 = RC0.6 + dos arreglos (el step-drummer, el secuenciador de efectos y el stretch siguen el patrón de su propia pista, antes el de otra; el knob selector del secuenciador de efectos, más lento); RC0.6 = RC0.5 + dos arreglos (el LFO del Auto-Filter y del Phaser arranca al activar el efecto; el blanco tenue de Clear ya no pulsa); RC0.5 = RC0.4 + el sample capturado delante de los efectos de Master FX; RC0.4 = RC0.3 + los arreglos de SC38.2-SC38.6; RC0.3 = SC38, RC0.2 = SC37.5, RC0.1 = SC37.4, RC0 = SC36.2.
- **Versión más segura:** RC2S = RC2, pero todo lo que el mod pediría escribir o borrar en la tarjeta o en la memoria interna se rechaza (el LED de Save se pone rojo): no hacen nada guardar la captura con el proyecto (A8), los intercambios y copias de samples y patches entre packs, los patches del sinte propio, guardar el patch del sinte, copiar proyectos ni borrar packs; los guardados del original (proyectos, patches, ajustes) sí. Las anteriores: RC0.9S = RC0.9 sin esas funciones. **Haz una copia de la SD antes de instalar** cualquier versión.
- Novedades y arreglos de cada versión: `CHANGELOG.md`.
""")

sec("herramientas", "E", "Herramientas de desarrollo y diagnóstico",
    ["Builders reproducibles, emuladores ARM / DSP con pruebas por rutas reales, `verify_builds.py`, diagnóstico remoto por USB (`ctremote.py`)."],
    """
- `tools/build_scNN.py`: cada versión se construye desde el firmware oficial; `verify_builds.py` comprueba que todas dan el mismo SHA-256.
- `tools/emu_*.py`: pruebas en emulación (Unicorn para el ARM, dsp56300 para el DSP).
- `tools/ctremote.py` + `rdiag`: el PC lee memoria, elementos de la tarjeta y la captura del aparato por SysEx. Solo en las builds de diagnóstico y en SC35 / SC36: **SC36.1, SC36.2, las RC (RC0 … RC2 y sus versiones más seguras) y las betas no lo llevan**, para no tocar el protocolo USB.
- `docs/NOTAS.md`: mapa técnico de todo lo descubierto.
""")

sec("tablas-midi", "E", "Tablas MIDI",
    ["Motor MIDI: CC 74/71/79/73/75/70/72/91/59/26/27/20/21/37/39/30/31/52/54 + NRPN 4:x; drums NRPN 5-8:1-12; Master FX NRPN 9:0-19 (canal 16)."],
    """
### Motor de las pistas MIDI — canal de la pista

| Valor | Mensaje | Valor | Mensaje |
|---|---|---|---|
| Filtro | CC 74 | TUNE | CC 26 |
| Resonancia | CC 71 | FINE | CC 27 |
| Env → filtro | CC 79 | WAVE | CC 20 |
| Ataque | CC 73 | SHAPE | CC 21 |
| Decay | CC 75 | TUNE 2 | CC 37 |
| Sustain | CC 70 | FINE 2 | CC 39 |
| Release | CC 72 | WAVE 2 | CC 30 |
| Efecto | CC 91 | SHAPE 2 | CC 31 |
| Gain | CC 59 | MIX | CC 52 |
| Velocidad LFO | NRPN 0:76 | RING | CC 54 |

El resto, NRPN MSB 4 con LSB = código (4, 12, 13, 15, 16, 21-26, 32, 33).

### Drums — NRPN MSB 5 / 6 / 7 / 8 = Drum 1-4
LSB 1 env. de tono, 2 ring (frecuencia), 3 LFO, 4 velocidad LFO, 5 env → corte, 6 resonancia, 7 forma de la envolvente, 8 ring (cantidad), 9 modo de filtro, 10 inicio (0-120; antes 0-15), 11 bitcrush, 12 tipo de distorsión, 13 corte (0-120), 14 ataque.

### Master FX — canal 16, NRPN MSB 9
LSB = 4 × conjunto + knob: Gater 0-3, Auto-Filter 4-7, Digitise 8-11, Phaser 12-15, Vinyl 16-19.
""")


# ---------------------------------------------------------------------------------------------------- languages
UI_ES = dict(
    md_title="Lista de características — CIRCUIT-HACKS ({v})",
    md_intro="Circuit Tracks con el firmware oficial 1.2.1 (build 4486) parcheado. Lo que no aparece aquí funciona como en el aparato original. "
             "Cada función en una línea, por temas. **El manual de uso es la [guía por vistas](GUIA.md)** (en color: [guia.html](https://ghillermo.github.io/CIRCUITS-HACKS-RC/guia.html)); los CC / NRPN, en la [referencia MIDI](MIDI.md). Versión ilustrada de esta lista: [https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html). English version: [`docs/MANUAL.en.md`](MANUAL.en.md).",
    conventions="**Convenciones:** pads 1-32 de arriba-izquierda a abajo-derecha (fila 1 = 1-8 … fila 4 = 25-32); knobs K1-K4 arriba, K5-K8 abajo; «Shift + X» = mantener Shift.",
    index="Índice",
    html_title="Lista de características — CIRCUIT-HACKS",
    cover="Lista de características del mod para Circuit Tracks",
    cover_fw="Firmware oficial 1.2.1 (build 4486) + {v}",
    html_conv="<strong>Convenciones.</strong> Pads 1-32 de arriba-izquierda a abajo-derecha (fila 1 = 1-8 … fila 4 = 25-32). Knobs K1-K4 arriba y K5-K8 abajo. «Shift + X» = mantener Shift mientras se usa X. "
              "Los colores de los diagramas son aproximados; un pad tenue se dibuja translúcido. Lo que no aparece aquí funciona como en el aparato original (consulta el manual oficial de Novation).",
    toc="Índice de funciones",
    other='<p class="lang"><a href="en.html">English version</a> · <a href="guia.html"><strong>Guía por vistas (manual de uso)</strong></a> · <a href="midi.html">Referencia MIDI</a></p>',
    footer="CIRCUIT-HACKS {v} · Este mod no está afiliado a Novation. Circuit Tracks es una marca de Focusrite Audio Engineering Ltd.",
    features="Características ({v})",
    features_manual="Manual de uso: [guía por vistas](https://ghillermo.github.io/CIRCUITS-HACKS-RC/guia.html) ([`docs/GUIA.md`](docs/GUIA.md)) · [referencia MIDI](docs/MIDI.md) · esta lista: [ilustrada en color](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html) · [resumida](docs/MANUAL.md) · **guía en palabras sencillas, ilustrada** ([web](https://ghillermo.github.io/CIRCUITS-HACKS-RC/sencilla.html), [PDF](https://ghillermo.github.io/CIRCUITS-HACKS-RC/sencilla.pdf); primer borrador de [reddit.com/u/luxurysoft1337](https://www.reddit.com/user/luxurysoft1337/), [su guía original](https://files.catbox.moe/xgogqy.pdf)). Novedades y arreglos de cada versión: [`CHANGELOG.md`](CHANGELOG.md). Lo marcado **desde RC2** es nuevo en RC2 / RC2S (no está en RC0.9).",
)
LANGS = {"es": dict(md="docs/MANUAL.md", html="index.html", lang="es"), "en": dict(md="docs/MANUAL.en.md", html="en.html", lang="en")}
PAGES = "https://ghillermo.github.io/CIRCUITS-HACKS-RC/"                                   # GitHub Pages of the public repository (branch gh-pages)
PAGES_URL = {"es": PAGES + "index.html", "en": PAGES + "en.html"}
CUR = dict(S=S, GROUPS=GROUPS, UI=UI_ES, lang="es")


def english():
    """The sections with the English text of tools/manual_en.py (figures translated through its LABEL table)."""
    import manual_en as EN
    out = []
    for s_ in S:
        title, summary, detail, caps = EN.SEC[s_["id"]]
        assert len(caps) == len(s_["figs"]), s_["id"]
        tr = lambda t: EN.LABEL.get(t, t)
        figs = [dict(f, caption=c, view=tr(f["view"]), pads={n: (v[0], tr(v[1])) + tuple(v[2:]) for n, v in f["pads"].items()},
                     knobs={k: tr(v) for k, v in f["knobs"].items()}) for f, c in zip(s_["figs"], caps)]
        out.append(dict(s_, title=title, summary=summary, detail=detail.strip("\n"), figs=figs))
    assert set(EN.SEC) == {s_["id"] for s_ in S}
    return dict(S=out, GROUPS=[(g, EN.GROUPS[g]) for g, _ in GROUPS], UI=EN.UI, lang="en")


def use(lang):
    CUR.update(dict(S=S, GROUPS=GROUPS, UI=UI_ES, lang="es") if lang == "es" else english())


# ---------------------------------------------------------------------------------------------------- outputs
def numbered():
    out, cnt = [], {}
    for s_ in CUR["S"]:
        cnt[s_["group"]] = cnt.get(s_["group"], 0) + 1
        out.append((f'{s_["group"]}{cnt[s_["group"]]}', s_))
    return out


def anchor(code, s_): return f'{code.lower()}-{s_["id"]}'


def md_inline(t):
    return t


def feature_list_md(link_base):
    lines = []
    for g, gname in CUR["GROUPS"]:
        lines.append(f"### {g}. {gname}")
        for code, s_ in numbered():
            if s_["group"] != g: continue
            lines.append(f'- **[{code} {s_["title"]}]({PAGES_URL[CUR["lang"]]}#{anchor(code, s_)})** — ' + " ".join(s_["summary"]))
        lines.append("")
    return "\n".join(lines)


def write_md():
    U = CUR["UI"]
    out = [f"# {U['md_title'].format(v=VERSION)}", "", U["md_intro"], "", U["conventions"], "", f"## {U['index']}", ""]
    for g, gname in CUR["GROUPS"]:
        out.append(f"**{g}. {gname}**")
        out.append("")
        for code, s_ in numbered():
            if s_["group"] == g: out.append(f'- [{code} {s_["title"]}](#{anchor(code, s_)})')
        out.append("")
    for g, gname in CUR["GROUPS"]:
        out.append(f"## {g}. {gname}")
        out.append("")
        for code, s_ in numbered():
            if s_["group"] != g: continue
            out.append(f'<a id="{anchor(code, s_)}"></a>')
            out.append(f'### {code}. {s_["title"]}')
            for b_ in s_["summary"]: out.append(f"- {b_}")
            out.append("")
    (ROOT / LANGS[CUR["lang"]]["md"]).write_text("\n".join(out), encoding="utf-8", newline="")


def inline(t):
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def md2html(text):
    out, lines, i = [], text.split("\n"), 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("### "):
            out.append(f"<h4>{inline(l[4:])}</h4>"); i += 1
        elif l.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")]); i += 1
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in rows[0]) + "</tr></thead><tbody>")
            for r in rows[2:]: out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            out.append("</tbody></table>")
        elif l.startswith("- "):
            out.append("<ul>")
            while i < len(lines) and lines[i].startswith("- "): out.append(f"<li>{inline(lines[i][2:])}</li>"); i += 1
            out.append("</ul>")
        elif re.match(r"\d+\. ", l):
            out.append("<ol>")
            while i < len(lines) and re.match(r"\d+\. ", lines[i]): out.append(f"<li>{inline(re.sub(r'^\\d+\\. ', '', lines[i]))}</li>"); i += 1
            out.append("</ol>")
        elif l.strip() == "":
            i += 1
        else:
            out.append(f"<p>{inline(l)}</p>"); i += 1
    return "\n".join(out)


CSS = """
:root { --bg:#f6f4ef; --fg:#1d1d1f; --muted:#5b5f66; --card:#ffffff; --accent:#ff6a13; --line:#e1ddd3; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#121315; --fg:#ececec; --muted:#a3a8ae; --card:#1c1d20; --line:#2c2e33; } }
:root[data-theme="dark"] { --bg:#121315; --fg:#ececec; --muted:#a3a8ae; --card:#1c1d20; --line:#2c2e33; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.55 "Helvetica Neue", Arial, sans-serif; }
header.cover { background:#17181b; color:#fff; padding:56px 24px 40px; text-align:center; }
header.cover h1 { font-size:40px; margin:0 0 8px; letter-spacing:.5px; } header.cover p { color:#c9cdd2; margin:4px 0; }
header.cover .bar { height:6px; width:180px; margin:18px auto 0; background:linear-gradient(90deg,#ff3b30,#ff8a00,#ffd23f,#3ddc5a,#00c2a8,#2f7bff,#8e5cff,#e040fb); border-radius:3px; }
main { max-width:980px; margin:0 auto; padding:24px 16px 64px; }
nav.toc { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px 22px; }
nav.toc h2 { margin-top:0; } nav.toc ol { padding-left:20px; } nav.toc a { color:var(--fg); }
h2.group { margin-top:48px; padding-bottom:6px; border-bottom:3px solid var(--accent); }
section.feat { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:20px 24px; margin:22px 0; }
section.feat h3 { margin-top:0; } section.feat .code { color:var(--accent); font-weight:bold; margin-right:6px; }
.summary { color:var(--muted); border-left:4px solid var(--accent); padding-left:12px; }
figure { margin:16px 0; } figure svg { width:100%; height:auto; border-radius:14px; } figcaption { color:var(--muted); font-size:14px; margin-top:6px; text-align:center; }
table { border-collapse:collapse; width:100%; margin:12px 0; font-size:14.5px; display:block; overflow-x:auto; }
body { overflow-x:hidden; } th, td { border:1px solid var(--line); padding:6px 8px; text-align:left; vertical-align:top; }
th { background:rgba(255,106,19,.10); } code { background:rgba(127,127,127,.15); padding:1px 4px; border-radius:4px; }
footer { color:var(--muted); text-align:center; font-size:13px; padding:24px; }
p.lang { text-align:right; margin:0 0 8px; } p.lang a { color:var(--accent); font-weight:bold; }
"""


def write_html():
    U, L_ = CUR["UI"], LANGS[CUR["lang"]]
    parts = [f'<!doctype html><html lang="{L_["lang"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{U["html_title"]}</title>',
             f"<style>{CSS}</style></head><body>",
             f'<header class="cover"><h1>CIRCUIT-HACKS</h1><p>{U["cover"]}</p><p>{U["cover_fw"].format(v=VERSION)}</p><div class="bar"></div></header><main>',
             U["other"], f'<p>{U["html_conv"]}</p>',
             f'<nav class="toc"><h2>{U["toc"]}</h2>']
    for g, gname in CUR["GROUPS"]:
        parts.append(f"<h3>{g}. {html.escape(gname)}</h3><ol>")
        for code, s_ in numbered():
            if s_["group"] == g: parts.append(f'<li><a href="#{anchor(code, s_)}">{code} {html.escape(s_["title"])}</a></li>')
        parts.append("</ol>")
    parts.append("</nav>")
    for g, gname in CUR["GROUPS"]:
        parts.append(f'<h2 class="group">{g}. {html.escape(gname)}</h2>')
        for code, s_ in numbered():
            if s_["group"] != g: continue
            parts.append(f'<section class="feat" id="{anchor(code, s_)}"><h3><span class="code">{code}</span>{html.escape(s_["title"])}</h3>')
            parts.append('<div class="summary">' + "".join(f"<p>{inline(b_)}</p>" for b_ in s_["summary"]) + "</div>")
            for f in s_["figs"]:
                parts.append(f"<figure>{svg(f)}<figcaption>{html.escape(f['caption'])}</figcaption></figure>")
            parts.append(md2html(s_["detail"]))
            parts.append("</section>")
    parts.append(f"<footer>{U['footer'].format(v=VERSION)}</footer></main></body></html>")
    d = ROOT / "docs/manual"; d.mkdir(parents=True, exist_ok=True)
    (d / L_["html"]).write_text("\n".join(parts), encoding="utf-8", newline="")


BEGIN, END = "<!-- FEATURES:BEGIN -->", "<!-- FEATURES:END -->"
BEGIN_EN, END_EN = "<!-- FEATURES-EN:BEGIN -->", "<!-- FEATURES-EN:END -->"


def write_readme():
    """The Spanish feature list between BEGIN / END (inserted before «## Estado rápido» the first time); the English one between BEGIN_EN / END_EN, only where those markers are."""
    p = ROOT / "README.md"; s = p.read_text(encoding="utf-8")
    for lang, b, e in (("es", BEGIN, END), ("en", BEGIN_EN, END_EN)):
        use(lang); U = CUR["UI"]
        block = f"{b}\n## {U['features'].format(v=VERSION)}\n\n{U['features_manual']}\n\n{feature_list_md(LANGS[lang]['md'])}\n{e}"
        if b in s and e in s:
            s = s[:s.index(b)] + block + s[s.index(e) + len(e):]
        elif lang == "es":
            k = s.index("## Estado rápido")
            s = s[:k] + block + "\n\n" + s[k:].replace("## Estado rápido", "## Historial de versiones", 1)
    p.write_text(readme_links(s), encoding="utf-8", newline="")


TOP = "<!-- LANG-NOTICE -->"
SEC_LINK = {"es": f"📖 [Manual ilustrado en color]({PAGES_URL['es']})", "en": f"📖 [Illustrated colour manual]({PAGES_URL['en']})"}


def readme_links(s):
    """An English notice right under the title, and under every section heading (## / ###, outside the feature lists and code) the colour manual on Pages,
    in the language of that part of the README (English from the «english» anchor on)."""
    lines = [l for l in s.split("\n") if not (l.startswith("📖 [") and "ghillermo.github.io" in l) and TOP not in l
             and not l.startswith("> **English:** the English version of this README") and not l.startswith("**English:** [see below](#english)")]
    out, lang, code, feat = [], "es", False, False
    for i, l in enumerate(lines):
        out.append(l)
        if i == 0 and l.startswith("# "):
            out.append(f"\n{TOP}\n> **English:** the English version of this README is [further below](#english). "
                       f"Illustrated colour manual: [English]({PAGES_URL['en']}) · [Español]({PAGES_URL['es']}).")
            continue
        if '<a id="english"></a>' in l: lang = "en"
        if l.startswith("```"): code = not code
        if l.startswith("<!-- FEATURES"): feat = l.endswith(":BEGIN -->")
        if l.strip() in ("## Licencia", "### License"): continue                       # no manual link under the licence
        if not code and not feat and (l.startswith("## ") or l.startswith("### ") or (lang == "en" and l.startswith("# "))):
            out.append(""); out.append(SEC_LINK[lang])
    s = "\n".join(out)
    while "\n\n\n" in s: s = s.replace("\n\n\n", "\n\n")
    return s


if __name__ == "__main__":
    for lang in LANGS:
        use(lang); write_md(); write_html()
    write_readme()
    print(len(S), "sections,", ", ".join(LANGS))
