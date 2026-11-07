"""The document «MIDI tracks and voice modes»: docs/VOCES.md + docs/VOICES.md -> docs/manual/voces.html + voices.html (published by publish_rc next to the guide).

The texts live in the two Markdown files; <!--fig:NAME--> marks a diagram, drawn here in the language of the page.
    python tools/make_voces.py
"""
from __future__ import annotations
import html, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_manual as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ACC, INK, QUIET, EDGE, TINT = "var(--accent)", "var(--fg)", "var(--muted)", "var(--muted)", "rgba(127,127,127,.12)"
# (x, y, w, h, main, es name, en name, [(es line, en line), ...])
RUTA = dict(h=628, title=("Cada nota pasa por el modo de voz antes de llegar al motor", "Every note goes through the voice mode before it reaches the engine"),
    paths="M104 128V152H456 M280 128V152 M134 152V176| M456 128V176| M632 128V176| M544 248V368| M104 336V368| M280 336V368| M456 336V368| M632 336V368| M216 436H240| M376 436H400| M536 436H560| M188 516V540| M352 572H384|",
    notes=[(24, 60, "Origen de las notas", "Where notes come from"), (642, 156, "no se reenvía", "not forwarded"), (552, 266, "1, 4 o 6 voces", "1, 4 or 6 voices"), (24, 270, "Modulación", "Modulation"),
           (40, 498, "El pad 29 cambia el orden: VCA, efecto, filtro", "Pad 29 changes the order: VCA, effect, filter")],
    tint=[(24, 368, 688, 148, "Motor de la pista", "The track's engine")],
    boxes=[(24, 72, 160, 56, 0, "Pads y teclado", "Pads and keyboard", [("Notas, acordes, latch", "Notes, chords, latch")]),
           (200, 72, 160, 56, 0, "Secuenciador", "Sequencer", [("Pasos del patrón", "Steps of the pattern")]),
           (376, 72, 160, 56, 0, "Arpegiador", "Arpeggiator", [("Una nota cada vez", "One note at a time")]),
           (552, 72, 160, 56, 0, "MIDI de entrada", "Incoming MIDI", [("USB o DIN", "USB or DIN")]),
           (24, 176, 220, 72, 0, "Salida MIDI", "MIDI output", [("Por el canal de la pista", "On the track's channel"), ("Patch flip: Program Change", "Patch flip: Program Change")]),
           (376, 176, 336, 72, 1, "Modo de voz", "Voice mode", [("Una voz, unísono o poly", "One voice, unison or poly"), ("Decide redisparo, glide y reparto de voces", "Decides retrigger, glide and voice sharing")]),
           (24, 280, 160, 56, 0, "ADSR y LFO", "ADSR and LFO", [("Páginas 1 y 5", "Pages 1 and 5")]),
           (200, 280, 160, 56, 0, "Matriz", "Matrix", [("8 fuentes, 33 destinos", "8 sources, 33 destinations")]),
           (376, 280, 160, 56, 0, "Automatización", "Automation", [("8 carriles del patrón", "8 lanes of the pattern")]),
           (552, 280, 160, 56, 0, "Step-drummer", "Step-drummer", [("Pares de pasos", "Pairs of steps")]),
           (40, 400, 176, 72, 0, "Fuente", "Source", [("Oscilador, VA-drum, FM,", "Oscillator, VA-drum, FM,"), ("granular, muestra, línea", "granular, sample, line")]),
           (240, 400, 136, 72, 0, "Filtro", "Filter", [("7 tipos", "7 types"), ("Resonancia", "Resonance")]),
           (400, 400, 136, 72, 0, "VCA", "VCA", [("ADSR y velocity", "ADSR and velocity"), ("Gain, saturación", "Gain, saturation")]),
           (560, 400, 136, 72, 0, "Efecto", "Effect", [("7 tipos", "7 types"), ("Cantidad", "Amount")]),
           (24, 540, 328, 64, 0, "Tira de la pista en el Mixer", "The track's strip in the Mixer", [("Nivel, panorama, mute, envíos, sidechain", "Level, pan, mute, sends, sidechain")]),
           (384, 540, 328, 64, 0, "Mezcla y salida", "Mix and output", [("Filtro master y Master FX", "Master filter and Master FX")])])
MAPA = dict(h=620, title=("La vista Preset concentra el sonido; las demás, el patrón", "The Preset view holds the sound; the others, the pattern"),
    paths="M140 330H156 M156 92V568 M156 92H172| M156 262H172| M156 432H172| M156 500H172| M156 568H172| M320 262H336 M336 160V364 M336 160H352| M336 228H352| M336 296H352| M336 364H352| M320 92H352| M552 92H584| M320 432H352| M320 500H352| M320 568H352|",
    notes=[], tint=[],
    boxes=[(24, 298, 116, 64, 0, "MIDI 1 / 2", "MIDI 1 / 2", [("Botón", "Button")]),
           (172, 64, 148, 56, 0, "Note", "Note", [("Tocar y escribir", "Play and write")]),
           (352, 64, 200, 56, 0, "Note ampliada", "Expanded Note", [("Note otra vez", "Note again")]),
           (584, 64, 152, 56, 0, "Step-drummer", "Step-drummer", [("Si está encendido", "If it is on")]),
           (172, 226, 148, 72, 1, "Preset", "Preset", [("O MIDI 1 / 2", "Or MIDI 1 / 2"), ("otra vez", "again")]),
           (352, 132, 200, 56, 0, "Fila de motores", "Engine row", [("Pad 27", "Pad 27")]),
           (352, 200, 200, 56, 0, "Modos de voz", "Voice modes", [("Pad 32; K1 glide, K2 unísono", "Pad 32; K1 glide, K2 unison")]),
           (352, 268, 200, 56, 0, "Editor de CC", "CC editor", [("Pad 25, con el motor apagado", "Pad 25, with the engine off")]),
           (352, 336, 200, 56, 0, "Step-drummer", "Step-drummer", [("Pad 30", "Pad 30")]),
           (172, 404, 148, 56, 0, "Velocity", "Velocity", [("Por paso", "Per step")]),
           (352, 404, 200, 56, 0, "Automatización del paso", "The step's automation", [("Shift + paso", "Shift + step")]),
           (172, 472, 148, 56, 0, "Gate", "Gate", [("Duración", "Length")]),
           (352, 472, 200, 56, 0, "Micro Step", "Micro Step", [("Gate otra vez", "Gate again")]),
           (172, 540, 148, 56, 0, "Pattern Settings", "Pattern Settings", [("Pasos y arpegiador", "Steps and arpeggiator")]),
           (352, 540, 200, 56, 0, "Probabilidad", "Probability", [("Pattern Settings otra vez", "Pattern Settings again")])])
MODOS = dict(h=492, title=("El modo de voz elige entre una voz, unísono o poly", "The voice mode chooses between one voice, unison or poly"),
    paths="M124 220H144V132H176| M124 220H176| M124 220H144V308H176| M552 156H584| M660 192V232| M356 392V364|",
    notes=[], tint=[(160, 56, 392, 308, "Modo de voz (pad 32)", "Voice mode (pad 32)")],
    boxes=[(24, 192, 100, 56, 0, "Nota", "Note", [("y su velocity", "and its velocity")]),
           (176, 96, 360, 72, 0, "Una voz", "One voice", [("Retrigger, legato, glide", "Retrigger, legato, glide"), ("La última nota manda; al soltarla vuelve la anterior", "The last note rules; on release the previous one returns")]),
           (176, 184, 360, 72, 0, "Todas las voces en la misma nota", "All voices on the same note", [("Uni retrig, uni legato, uni glide, uni always-glide", "Uni retrig, uni legato, uni glide, uni always-glide"), ("4 voces (FM 6 o 3), desafinadas con K2", "4 voices (FM 6 or 3), detuned with K2")]),
           (176, 272, 360, 72, 1, "Una voz por nota (de fábrica)", "One voice per note (default)", [("Poly", "Poly"), ("4 voces (FM 6 o 3); una nota de más quita la más antigua", "4 voices (FM 6 or 3); one note too many takes the oldest")]),
           (584, 120, 152, 72, 0, "Nivel", "Level", [("Cada voz × √(2 / n)", "Each voice × √(2 / n)"), ("1 o 2 voces: entero", "1 or 2 voices: whole")]),
           (584, 232, 152, 72, 0, "VCA de la pista", "The track's VCA", [("Filtro y efecto", "Filter and effect"), ("siempre de la pista", "always the track's")]),
           (160, 392, 392, 72, 0, "Límite de voces", "Voice limit", [("Con dos voces o más, cada 2 ms mira el tiempo del DSP.", "With two voices or more, it checks the DSP's time every 2 ms."), ("Apaga la voz soltada más baja, o la mantenida más antigua.", "It turns off the lowest released voice, or the oldest held one.")])])
FIGS = dict(ruta=RUTA, mapa=MAPA, modos=MODOS)

# The drawings of the views: the LEDs come from docs/voces_panels.json (tools/capture_voces.py, the firmware itself); here only the words.
BTN_LED = {"Scales": 50, "Oct ▼": 51, "Oct ▲": 52, "1-16 / 17-32": 53, "Clear": 55, "Duplicate": 56, "Save": 57, "Preset": 40, "Synth 1": 32, "Synth 2": 33, "MIDI 1": 34, "MIDI 2": 35,
           "Drum 1": 36, "Drum 2": 37, "Drum 3": 38, "Drum 4": 39, "Patterns": 45, "Note": 41, "Velocity": 42, "Gate": 43, "Pattern Settings": 44, "Mixer": 46, "FX": 47, "Record": 48, "Play": 49}
K1 = (("Ataque", "Release", "Env → nivel", "Env → filtro", "Filtro", "Reso", "Vel. LFO", "Efecto"), ("Attack", "Release", "Env → level", "Env → filter", "Filter", "Reso", "LFO speed", "Effect"))
ENG = (("Sin voz", "VCA\nVCF", "Osc", "VA-drum", "WT", "Muestra", "Gran.", "FM"), ("No voice", "VCA\nVCF", "Osc", "VA-drum", "WT", "Sample", "Gran.", "FM"))   # (Beta 5.21: the new row)
TRK = ("Synth 1", "Synth 2", "MIDI 1", "MIDI 2", "Drum 1", "Drum 2", "Drum 3", "Drum 4")
VM = ("Retrig", "Legato", "Glide", "Uni\nretrig", "Uni\nlegato", "Uni\nglide", "Uni\nalways", "Poly")
PRE_PADS = {1: ("Sec.", "Seq."), 2: ("OSC 1", "OSC 1"), 3: ("OSC 2", "OSC 2"), 4: ("VCA\nVCF", "VCA\nVCF"), 5: ("Mod.", "Mod."), 6: ("Matriz", "Matrix"), 7: ("FM", "FM"), 8: ("FM", "FM"),
            26: ("Flip", "Flip"), 27: ("Motor", "Engine"), 28: ("2 osc", "2 osc"), 29: ("Orden", "Order"), 30: ("Step\ndrum", "Step\ndrum"), 31: ("Vel", "Vel"), 32: ("Modo\nvoz", "Voice\nmode")}
ROWS = {n: (ENG[0][n - 17], ENG[1][n - 17]) for n in range(17, 25)}
PANELS = {
    "preset": dict(cap=("Vista Preset con el oscilador: los pads 9-24 son patches (violeta = vacío); el pad 3 y el 7 se apagan si no aplican.", "Preset view with the oscillator: pads 9-24 are patches (violet = empty); pads 3 and 7 go dark when they do not apply."),
                   view=("Preset", "Preset"), pads={**PRE_PADS, **{n: ("Patch", "Patch") for n in range(9, 25)}}, knobs=K1),
    "motores": dict(cap=("Fila de motores abierta (toque al pad 27): pads 17-24 los motores; pads 9-16 las pistas del secuenciador de saltos.", "Engine row open (tap pad 27): pads 17-24 the engines; pads 9-16 the tracks of the jump sequencer."),
                    view=("Motores", "Engines"), pads={**PRE_PADS, **ROWS, **{9 + i: (t, t) for i, t in enumerate(TRK)}}, knobs=K1),
    "voz": dict(cap=("Modos de voz abiertos (toque al pad 32): poly brillante, el modo de fábrica. K1 glide, K2 desafinación.", "Voice modes open (tap pad 32): poly bright, the default mode. K1 glide, K2 detune."),
                view=("Modos de voz", "Voice modes"), pads={**PRE_PADS, **{17 + i: (v, v) for i, v in enumerate(VM)}}, knobs=(("Glide", "Unísono"), ("Glide", "Unison"))),
    "fm": dict(cap=("Página FM (pad 7): K1-K4 ratios, K5-K8 niveles; el pad 27 en violeta.", "FM page (pad 7): K1-K4 ratios, K5-K8 levels; pad 27 violet."),
               view=("FM", "FM"), pads={**PRE_PADS, **{n: ("Patch", "Patch") for n in range(9, 25)}}, knobs=(("Ratio 1", "Ratio 2", "Ratio 3", "Ratio 4", "Nivel 1", "Nivel 2", "Nivel 3", "Nivel 4"), ("Ratio 1", "Ratio 2", "Ratio 3", "Ratio 4", "Level 1", "Level 2", "Level 3", "Level 4"))),
    "algos": dict(cap=("Pad 7 mantenido: los 16 algoritmos, por familias; el elegido brillante.", "Pad 7 held: the 16 algorithms, by family; the chosen one bright."),
                  view=("Algoritmos", "Algorithms"), pads={**PRE_PADS, **{9 + i: (str(i + 1), str(i + 1)) for i in range(16)}}, knobs=(("Ratio 1", "Ratio 2", "Ratio 3", "Ratio 4", "Nivel 1", "Nivel 2", "Nivel 3", "Nivel 4"), ("Ratio 1", "Ratio 2", "Ratio 3", "Ratio 4", "Level 1", "Level 2", "Level 3", "Level 4"))),
    "partida": dict(cap=("Pad 8 mantenido: los 16 sonidos de partida, por familias.", "Pad 8 held: the 16 starter sounds, by family."),
                    view=("Sonidos de partida", "Starter sounds"), pads={**PRE_PADS, **{9 + i: (a, b) for i, (a, b) in enumerate(zip(("Piano", "E-piano", "Órgano", "Pluck", "Arpa", "Marimba", "Bajo", "Campana", "Cuerdas", "Pad", "Flauta", "Clarin.", "Metales", "Bombo", "Caja", "Hi-hat"), ("Piano", "E-piano", "Organ", "Pluck", "Harp", "Marimba", "Bass", "Bell", "Strings", "Pad", "Flute", "Clarin.", "Brass", "Kick", "Snare", "Hi-hat")))}}, knobs=()),
    "fm8": dict(cap=("FM de 8 operadores, su página (pad 7): pads 9-16 los operadores (portadores verdes, moduladores azul claro), pad 3 la envolvente de pitch; K1 ratio, K2 fino, K3 nivel, K4 velocity, K5-K8 rates; con Shift algoritmo, feedback, escalados y niveles.", "8-operator FM, its page (pad 7): pads 9-16 the operators (carriers green, modulators light blue), pad 3 the pitch envelope; K1 ratio, K2 fine, K3 level, K4 velocity, K5-K8 rates; with Shift algorithm, feedback, scalings and levels."),
                view=("FM 8 op", "FM 8 op"), pads={**PRE_PADS, 3: ("PEG", "PEG"), **{9 + i: ("Op " + str(i + 1), "Op " + str(i + 1)) for i in range(8)}, **ROWS},
                knobs=(("Ratio", "Fino", "Nivel", "Veloc.", "R1", "R2", "R3", "R4"), ("Ratio", "Fine", "Level", "Veloc.", "R1", "R2", "R3", "R4"))),
    "algos8": dict(cap=("Pad 7 mantenido: los 56 algoritmos en tres páginas (Octave ▼ / ▲), 24 por página; el elegido brillante.", "Pad 7 held: the 56 algorithms in three pages (Octave ▼ / ▲), 24 a page; the chosen one bright."),
                   view=("Algoritmos", "Algorithms"), pads={**PRE_PADS, **{9 + i: (str(i + 1), str(i + 1)) for i in range(24)}}, knobs=()),
    "inst8": dict(cap=("Pad 8 mantenido: los 24 instrumentos, en el color de su tipo (teclas, bajos, leads, pads, pulsados, percusión, campanas).", "Pad 8 held: the 24 instruments, in their type's colour (keys, basses, leads, pads, plucks, percussion, bells)."),
                  view=("Instrumentos", "Instruments"), pads={**PRE_PADS, **{9 + i: (n, n) for i, n in enumerate(('E.Piano', 'Bright\nEP', 'Clav', 'Organ', 'Marimba', 'Vibes', 'FM\nBass', 'Synth\nBass', 'Deep\nBass', 'Brass', 'Sync\nLead', 'Flute', 'Strings', 'Warm\nPad', 'Choir', 'Glass\nPad', 'Harp', 'Koto', 'Nylon', 'Kick', 'Snare', 'Hi-Hat', 'Tubular\nBell', 'Space\nSweep'))}}, knobs=()),
    "wt": dict(cap=("Wavetable (pad 21 de la fila de motores): el pad 27 en arena; los pads 7 y 8, las dos listas.", "Wavetable (pad 21 of the engine row): pad 27 in sand; pads 7 and 8, the two lists."),
               view=("Wavetable", "Wavetable"), pads={**PRE_PADS, 7: ("Tablas", "Tables"), 8: ("Samples", "Samples"), **{n: ("Patch", "Patch") for n in range(9, 25)}}, knobs=()),
    "wtnova": dict(cap=("Pad 7 mantenido: las 16 wavetables de stock (pads 9-24, la cargada brillante). Un toque = la tabla entera; Shift + toque = solo el cuadro que señala K3 de OSC 1.", "Pad 7 held: the stock's 16 wavetables (pads 9-24, the loaded one bright). A tap = the whole table; Shift + tap = only the frame OSC 1's K3 points at."),
                   view=("Tablas Nova", "Nova tables"), pads={**PRE_PADS, **{9 + i: (str(i + 1), str(i + 1)) for i in range(16)}}, knobs=()),
    "wtsmp": dict(cap=("Pad 8 mantenido: los samples del pack (pads 9-32; Octave ▼ / ▲ = página). Un toque pone un ciclo de ese sample en el cuadro que señala K3 de OSC 1.", "Pad 8 held: the pack's samples (pads 9-32; Octave ▼ / ▲ = page). A tap puts a cycle of that sample in the frame OSC 1's K3 points at."),
                  view=("Samples", "Samples"), pads={**PRE_PADS, **{9 + i: ("S" + str(i + 1), "S" + str(i + 1)) for i in range(24)}}, knobs=()),
    "step": dict(cap=("Step-drummer: pads 1-16 los pasos por pares, pads 17-24 los destinos, K1-K8 los pares.", "Step-drummer: pads 1-16 the steps by pairs, pads 17-24 the destinations, K1-K8 the pairs."),
                 view=("Step-drummer", "Step-drummer"), pads={**{n: (str(n), str(n)) for n in range(1, 17)}, **{17 + i: (d, e) for i, (d, e) in enumerate(zip(("Tono", "OSC 2", "WAVE", "FM", "MIX", "Env F", "SHAPE", "Decay"), ("Pitch", "OSC 2", "WAVE", "FM", "MIX", "Env F", "SHAPE", "Decay")))}, 26: ("Flip", "Flip"), 27: ("Motor", "Engine"), 28: ("2 osc", "2 osc"), 29: ("Orden", "Order"), 30: ("Step\ndrum", "Step\ndrum"), 32: ("Pitch\nvel", "Pitch\nvel")},
                 knobs=(tuple("Par %d" % k for k in range(1, 9)), tuple("Pair %d" % k for k in range(1, 9)))),
    "muestra": dict(cap=("Note ampliada en modo muestra: pads 1-16 los pasos (brillante = con nota), pads 17-32 los samples (el elegido, verde azulado).", "Expanded Note in sample mode: pads 1-16 the steps (bright = with a note), pads 17-32 the samples (the chosen one teal)."),
                    view=("Selector de samples", "Sample picker"), pads={**{n: (str(n), str(n)) for n in range(1, 17)}, **{17 + i: ("S%d" % (i + 1), "S%d" % (i + 1)) for i in range(16)}}, knobs=()),
    "saltos": dict(cap=("Vista de flip (pad 26, blanco) con step flip hacia Drum 1: fila 3, pad 17 patch flip (PGM seq) y pad 18 step flip en el color del destino; fila 2, las pistas (Drum 1 brillante, MIDI 1 apagada).", "Flip view (pad 26, white) with step flip to Drum 1: row 3, pad 17 patch flip (PGM seq) and pad 18 step flip in the target's colour; row 2, the tracks (Drum 1 bright, MIDI 1 dark)."),
                   view=("Flip", "Flip"), pads={**PRE_PADS, 17: ("PGM\nseq", "PGM\nseq"), 18: ("Step\nflip", "Step\nflip"), 26: ("Flip", "Flip"), **{9 + i: (t, t) for i, t in enumerate(TRK)}}, knobs=()),
    "saltosnote": dict(cap=("Vista Note apuntando a otra pista: los pads 17-32 son los pasos 1-16 de esa pista.", "Note view pointing at another track: pads 17-32 are steps 1-16 of that track."),
                       view=("Note: saltos", "Note: jumps"), pads={**{n: (str(n), str(n)) for n in range(1, 17)}, **{17 + i: ("→%d" % (i + 1), "→%d" % (i + 1)) for i in range(16)}}, knobs=()),
    "ps": dict(cap=("Pattern Settings: pads 1-16 primer y último paso, 17-24 sync rate, 25 modo 2, 26 Nudge, 27 / 28 órdenes, 29-32 dirección.", "Pattern Settings: pads 1-16 first and last step, 17-24 sync rate, 25 mode 2, 26 Nudge, 27 / 28 orders, 29-32 direction."),
               view=("Pattern Settings", "Pattern Settings"), pads={**{n: (str(n), str(n)) for n in range(1, 17)}, **{17 + i: (r, r) for i, r in enumerate(("1/4", "1/4T", "1/8", "1/8T", "1/16", "1/16T", "1/32", "1/32T"))}, 25: ("Modo 2", "Mode 2"), 26: ("Nudge", "Nudge"), 27: ("Fractal", "Fractal"), 28: ("Decons.", "Decon."), 29: ("Adel.", "Fwd"), 30: ("Atrás", "Back"), 31: ("Ping\npong", "Ping\npong"), 32: ("Azar", "Random")}, knobs=()),
    "mutate": dict(cap=("Random-mutate (modo 2) con un paso elegido: el pad 22, las dinámicas (pad 26) y los micropasos (pad 32) encendidos.", "Random-mutate (mode 2) with a step chosen: pad 22, the dynamics (pad 26) and the micro steps (pad 32) on."),
                   view=("Random-mutate", "Random-mutate"), pads={**{n: (str(n), str(n)) for n in range(1, 17)}, 17: ("Off", "Off"), 18: ("×1", "×1"), 19: ("×2", "×2"), 20: ("×4", "×4"), 21: ("Oct ↑\nbaja", "Oct ↑\nlow"), 22: ("Oct ↑\nalta", "Oct ↑\nhigh"), 23: ("Oct ↕\nbaja", "Oct ↕\nlow"), 24: ("Oct ↕\nalta", "Oct ↕\nhigh"), 25: ("Din.", "Dyn."), 26: ("Acent.", "Accent"), 27: ("Acent.\nlong.", "Accent\nlength"), 28: ("Long.", "Length"), 32: ("Micro", "Micro")}, knobs=()),
    "micro": dict(cap=("Micro Step: micropasos y Tie; pad 31 longitud fija, pad 32 gate por pulsación.", "Micro Step: micro steps and Tie; pad 31 fixed length, pad 32 gate by press."),
                  view=("Micro Step", "Micro Step"), pads={**{n: (str(n), str(n)) for n in range(1, 17)}, **{17 + i: ("μ%d" % (i + 1), "μ%d" % (i + 1)) for i in range(6)}, 24: ("Tie", "Tie"), 25: ("Nota", "Note"), 31: ("Fija", "Fixed"), 32: ("Pulsar", "Hold")}, knobs=()),
}
DATA = json.loads((ROOT / "docs/voces_panels.json").read_text(encoding="utf-8")) if (ROOT / "docs/voces_panels.json").exists() else {}


def lit(c):
    return (30 * int(c[1:3], 16) + 59 * int(c[3:5], 16) + 11 * int(c[5:7], 16)) // 100        # luma


def panel(name, lang):
    k = 1 if lang == "en" else 0
    P, D = PANELS[name], DATA[name]
    pads = {}
    for n in range(1, 33):
        if D["codes"][n - 1] == 0: continue                                                # dark on the device: drawn dark, no label
        col = D["rgb"][n - 1]
        lab = P["pads"].get(n, ("", ""))[k]
        pads[n] = (col, lab, False, "#111" if lit(col) > 110 else "#e8eaed")
    kl = {i + 1: t for i, t in enumerate(P["knobs"][k])} if P["knobs"] else {}
    kcol = {}
    for i in range(8):
        c, b = D["codes"][60 + i], max(D["bright"][60 + i] - 2, 0)
        if c: kcol[i + 1] = D["rgb"][60 + i] if b == 0 or b > 60 else "#" + "".join("%02x" % (int(D["rgb"][60 + i][j:j + 2], 16) * (20 + b) // 90) for j in (1, 3, 5))
    btn = {nm: D["rgb"][led] for nm, led in BTN_LED.items() if D["codes"][led]}
    fig = M.fig(P["cap"][k], pads=pads, knobs=kl, buttons=btn, view=P["view"][k])
    fig["kcol"] = kcol
    return f"<figure>{M.svg(fig)}<figcaption>{html.escape(P['cap'][k])}</figcaption></figure>"


def svg(fig, lang):
    k = 1 if lang == "en" else 0
    e = html.escape
    title = fig["title"][k]
    out = [f'<svg viewBox="0 0 760 {fig["h"]}" role="img" aria-label="{e(title)}" font-size="13" xmlns="http://www.w3.org/2000/svg">',
           f'<defs><marker id="arr-{fig["h"]}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{EDGE}"/></marker></defs>',
           f'<text x="24" y="28" font-size="15" font-weight="600" fill="{INK}">{e(title)}</text>']
    for x, y, w, h, es, en in fig["tint"]:
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{TINT}" stroke="{EDGE}" stroke-width="1.25"/>')
        out.append(f'<text x="{x + 16}" y="{y + 22}" font-weight="600" fill="{INK}">{e(en if k else es)}</text>')
    for p in fig["paths"].split(" M"):
        p = p if p.startswith("M") else "M" + p
        arrow = p.endswith("|")
        p = p.rstrip("|")
        out.append(f'<path d="{p}" fill="none" stroke="{EDGE}" stroke-width="1.25"' + (f' marker-end="url(#arr-{fig["h"]})"' if arrow else "") + "/>")
    for x, y, w, h, main, es, en, lines in fig["boxes"]:
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{ACC if main else "var(--card)"}" fill-opacity="{0.12 if main else 1}" stroke="{ACC if main else EDGE}" stroke-width="{2 if main else 1.25}"/>')
        out.append(f'<text x="{x + 16}" y="{y + 24}" font-weight="600" fill="{INK}">{e(en if k else es)}</text>')
        for i, ln in enumerate(lines):
            out.append(f'<text x="{x + 16}" y="{y + 40 + 16 * i}" font-size="11.5" fill="{INK if main else QUIET}">{e(ln[k])}</text>')
    for x, y, es, en in fig["notes"]:
        out.append(f'<text x="{x}" y="{y}" font-size="11.5" fill="{QUIET}">{e(en if k else es)}</text>')
    out.append("</svg>")
    return "".join(out)


UI = dict(es=dict(src="docs/VOCES.md", page="voces.html", other="voices.html", other_name="English", guide="guia.html", guide_name="Guía por vistas", toc="Contenido", lang="es"),
          en=dict(src="docs/VOICES.md", page="voices.html", other="voces.html", other_name="Español", guide="guide.html", guide_name="Guide by views", toc="Contents", lang="en"))


COVER = {"rc": "RC4.08", "beta": "Beta 5.32"}


def page(lang):
    U = UI[lang]
    text = (ROOT / U["src"]).read_text(encoding="utf-8")
    assert "<!--fig:" in text and "@" not in text.split("\n## ")[0], "no figures, or a mention in the header"
    head, *secs = re.split(r"^## ", text, flags=re.M)
    title = head.strip().lstrip("# ").strip()
    h = [f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title><style>{M.CSS}'
         ".feat h4 { margin-bottom:6px; } figure svg { background:var(--card); border:1px solid var(--line); }</style></head><body>",
         f'<header class="cover"><h1>{html.escape(title)}</h1><p>CIRCUIT-HACKS · {COVER.get(M.SET, "Beta 5.32")}</p><p><a style="color:#fff" href="{U["other"]}">{U["other_name"]}</a> · <a style="color:#fff" href="{U["guide"]}">{U["guide_name"]}</a></p><div class="bar"></div></header><main>',
         f'<nav class="toc"><h2>{U["toc"]}</h2><ol>']
    parts = []
    if M.SET == "rc":                                                       # (docset.py) the release candidate's set: no beta-only section
        import docset
        secs = [s for s in secs if not docset.titled(s.partition("\n")[0])]
    for i, s in enumerate(secs, 1):
        name, _, body = s.partition("\n")
        h.append(f'<li><a href="#s{i}">{html.escape(name)}</a></li>')
        body = re.sub(r"<!--panel:(\w+)-->", lambda m: "<!--fig:panel_" + m.group(1) + "-->", body)
        chunks = re.split(r"<!--fig:(\w+)-->", body)
        o = [f'<section class="feat" id="s{i}"><h3>{html.escape(name)}</h3>']
        for k, c in enumerate(chunks):
            if k % 2: o.append(panel(c[6:], lang) if c.startswith("panel_") else f"<figure>{svg(FIGS[c], lang)}</figure>")
            else: o.append(M.md2html(c.strip("\n")))
        o.append("</section>")
        parts.append("\n".join(o))
    h.append("</ol></nav>")
    out = "\n".join(h + parts + ["</main></body></html>"])
    (ROOT / M.OUT / U["page"]).write_text(out, encoding="utf-8", newline="")
    return U["page"], len(out)


if __name__ == "__main__":
    for lang in ("es", "en"): print(*page(lang))
