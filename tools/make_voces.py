"""The document «MIDI tracks and voice modes»: docs/VOCES.md + docs/VOICES.md -> docs/manual/voces.html + voices.html (published by publish_rc next to the guide).

The texts live in the two Markdown files; <!--fig:NAME--> marks a diagram, drawn here in the language of the page.
    python tools/make_voces.py
"""
from __future__ import annotations
import html, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_manual as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ACC, INK, QUIET, EDGE, TINT = "var(--accent)", "var(--fg)", "var(--muted)", "var(--muted)", "rgba(127,127,127,.12)"
# (x, y, w, h, main, es name, en name, [(es line, en line), ...])
RUTA = dict(h=628, title=("Cada nota pasa por el modo de voz antes de llegar al motor", "Every note goes through the voice mode before it reaches the engine"),
    paths="M104 128V152H456 M280 128V152 M134 152V176| M456 128V176| M632 128V176| M544 248V368| M104 336V368| M280 336V368| M456 336V368| M632 336V368| M216 436H240| M376 436H400| M536 436H560| M188 516V540| M352 572H384|",
    notes=[(24, 60, "Origen de las notas", "Where notes come from"), (642, 156, "no se reenvía", "not forwarded"), (552, 266, "1, 4 o 6 voces", "1, 4 or 6 voices"), (24, 270, "Modulación", "Modulation"),
           (40, 498, "El pad 29 cambia el orden: filtro, VCA, efecto", "Pad 29 changes the order: filter, VCA, effect")],
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
           (240, 400, 136, 72, 0, "VCA", "VCA", [("ADSR y velocity", "ADSR and velocity"), ("Gain, saturación", "Gain, saturation")]),
           (400, 400, 136, 72, 0, "Efecto", "Effect", [("7 tipos", "7 types"), ("Cantidad", "Amount")]),
           (560, 400, 136, 72, 0, "Filtro", "Filter", [("7 tipos", "7 types"), ("Resonancia", "Resonance")]),
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


def page(lang):
    U = UI[lang]
    text = (ROOT / U["src"]).read_text(encoding="utf-8")
    assert "<!--fig:" in text and "@" not in text.split("\n## ")[0], "no figures, or a mention in the header"
    head, *secs = re.split(r"^## ", text, flags=re.M)
    title = head.strip().lstrip("# ").strip()
    h = [f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title><style>{M.CSS}'
         ".feat h4 { margin-bottom:6px; } figure svg { background:var(--card); border:1px solid var(--line); }</style></head><body>",
         f'<header class="cover"><h1>{html.escape(title)}</h1><p>CIRCUIT-HACKS · Beta 5.4</p><p><a style="color:#fff" href="{U["other"]}">{U["other_name"]}</a> · <a style="color:#fff" href="{U["guide"]}">{U["guide_name"]}</a></p><div class="bar"></div></header><main>',
         f'<nav class="toc"><h2>{U["toc"]}</h2><ol>']
    parts = []
    for i, s in enumerate(secs, 1):
        name, _, body = s.partition("\n")
        h.append(f'<li><a href="#s{i}">{html.escape(name)}</a></li>')
        chunks = re.split(r"<!--fig:(\w+)-->", body)
        o = [f'<section class="feat" id="s{i}"><h3>{html.escape(name)}</h3>']
        for k, c in enumerate(chunks):
            o.append(f"<figure>{svg(FIGS[c], lang)}</figure>" if k % 2 else M.md2html(c.strip("\n")))
        o.append("</section>")
        parts.append("\n".join(o))
    h.append("</ol></nav>")
    out = "\n".join(h + parts + ["</main></body></html>"])
    (ROOT / "docs/manual" / U["page"]).write_text(out, encoding="utf-8", newline="")
    return U["page"], len(out)


if __name__ == "__main__":
    for lang in ("es", "en"): print(*page(lang))
