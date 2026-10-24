"""The MIDI reference of the new features (the user, 2026-10-15: «incluye también un documento de referencia MIDI CC / NRPN nuevos»): docs/MIDI.md, docs/MIDI.en.md,
docs/manual/midi.html, docs/manual/midi-en.html.  The engine's numbers come from vcf21.CC_TAB; written by tools/make_guide.py."""
from __future__ import annotations
import html
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
# the MIDI engine's codes: code, es, en, page / knob (the same in both languages)
ENGINE = [
    (1, "Filtro", "Filter", "1 / K5"), (2, "Resonancia", "Resonance", "1 / K6"), (3, "Envolvente → filtro", "Envelope → filter", "1 / K4"),
    (4, "LFO → filtro", "LFO → filter", "1 / Shift + K4"), (5, "Ataque", "Attack", "1 / K1"), (6, "Decay", "Decay", "1 / Shift + K2"),
    (7, "Sustain", "Sustain", "1 / Shift + K1"), (8, "Release", "Release", "1 / K2"), (9, "Cantidad de efecto", "Effect amount", "1 / K8"),
    (10, "Gain del VCA", "VCA gain", "1 / Shift + K6"), (11, "Velocidad del LFO", "LFO speed", "1 / K7"), (12, "LFO → nivel", "LFO → level", "1 / Shift + K3"),
    (13, "Tipo de efecto", "Effect type", "1 / Shift + K8"), (15, "Envolvente → nivel", "Envelope → level", "1 / K3"), (16, "Tipo de filtro", "Filter type", "1 / Shift + K5"),
    (17, "TUNE (granular: tono)", "TUNE (granular: pitch)", "2 / K1"), (18, "FINE (granular: tamaño)", "FINE (granular: size)", "2 / Shift + K1"),
    (19, "WAVE (granular: posición)", "WAVE (granular: position)", "2 / K7"), (20, "SHAPE (granular: densidad)", "SHAPE (granular: density)", "2 / K2"),
    (21, "LFO → tono (granular: scan)", "LFO → pitch (granular: scan)", "2 / K5"), (22, "Envolvente → tono (granular: env → posición)", "Envelope → pitch (granular: env → position)", "2 / K3"),
    (23, "Envolvente → forma (granular: zona)", "Envelope → shape (granular: zone)", "2 / K4"), (24, "LFO → forma (granular: LFO → posición)", "LFO → shape (granular: LFO → position)", "2 / K6"),
    (25, "Envolvente → morph (granular: fuente)", "Envelope → morph (granular: source)", "2 / Shift + K8"), (26, "LFO → morph (granular: modo de nota)", "LFO → morph (granular: note mode)", "2 / K8"),
    (27, "TUNE 2 (granular: LFO → tamaño)", "TUNE 2 (granular: LFO → size)", "3 / K1"), (28, "FINE 2 (granular: fino)", "FINE 2 (granular: fine)", "3 / K5 (RC2) · 3 / Shift + K1 (RC0.9)"),
    (29, "WAVE 2 (granular: dispersión del tono; Beta 3.22: estéreo)", "WAVE 2 (granular: pitch spread; Beta 3.22: stereo)", "3 / K7"), (30, "SHAPE 2 (granular: ventana)", "SHAPE 2 (granular: window)", "3 / K2"),
    (31, "MIX OSC 1 ↔ OSC 2", "MIX OSC 1 ↔ OSC 2", "2 / Shift + K2 · 3 / K3 (RC2)"), (32, "BITSYNC", "BITSYNC", "2 / Shift + K3 · 3 / K6 (RC2)"),
    (33, "FM (granular: dispersión de la posición)", "FM (granular: position spread)", "3 / K4 (RC2) · 3 / Shift + K2 (RC0.9)"), (34, "RING (granular: reverso; Beta 3.22: bipolar, reverso / dispersión del tono)", "RING (granular: reverse; Beta 3.22: bipolar, reverse / pitch spread)", "3 / K8 (RC2) · 3 / Shift + K3 (RC0.9)")]
DRUMS = [  # lsb, es, en, values es, values en
    (1, "Envolvente → tono", "Envelope → pitch", "0-127, 64 = 0", "0-127, 64 = 0"), (2, "Ring mod: frecuencia", "Ring mod: frequency", "0-127", "0-127"),
    (3, "LFO: cantidad (> 64 trémolo; < 64 vibrato, solo Beta 3.22: scan del inicio)", "LFO: amount (> 64 tremolo; < 64 vibrato, Beta 3.22 only: start scan)", "0-127, 64 = 0", "0-127, 64 = 0"), (4, "LFO: velocidad", "LFO: speed", "0-127, 64 = centro", "0-127, 64 = centre"),
    (5, "Envolvente → corte", "Envelope → cutoff", "0-127, 64 = 0", "0-127, 64 = 0"), (6, "Resonancia", "Resonance", "0-127", "0-127"),
    (7, "Forma de la envolvente", "Envelope shape", "0-127, 64 = centro", "0-127, 64 = centre"), (8, "Ring mod: cantidad", "Ring mod: amount", "0-127", "0-127"),
    (9, "Modo de filtro", "Filter mode", "0 EQ tilt de stock, 1 paso banda, 2 notch, 3 comb, 4 DJ", "0 stock tilt EQ, 1 band-pass, 2 notch, 3 comb, 4 DJ"),
    (10, "Inicio del sample", "Sample start", "0-120 (/128; desde RC2.09 todo el sample, antes el final llegaba en 32); RC0.9: 0-15 (/64)", "0-120 (/128; since RC2.09 the whole sample, before it reached the end at 32); RC0.9: 0-15 (/64)"),
    (11, "Bitcrush", "Bitcrush", "0-15", "0-15"), (12, "Tipo de distorsión", "Distortion type", "0 stock, 1 suave, 2 dura, 3 plegada", "0 stock, 1 soft, 2 hard, 3 fold"),
    (13, "Corte desde el final (desde RC2)", "Cut from the end (since RC2)", "0-120 (/128)", "0-120 (/128)"), (14, "Ataque (desde RC2)", "Attack (since RC2)", "0-127", "0-127")]
GFX = [("Gater", "división, profundidad, ancho, suavizado", "division, depth, width, smoothing"),
       ("Auto-Filter (pads 2 / 3)", "velocidad, profundidad, resonancia, centro", "speed, depth, resonance, centre"),
       ("Digitise", "muestreo, bits, envío al delay (RC2), envolvente (RC2)", "sample rate, bits, delay throw (RC2), envelope (RC2)"),
       ("Phaser", "velocidad, profundidad, realimentación, mezcla", "speed, depth, feedback, mix"),
       ("Glitch (RC0.9: Vinyl)", "velocidad, repetición, retraso, caos / sobrecarga (RC0.9: crackle, siseo, tono, desgaste)", "speed, repeat, delay, chaos / overload (RC0.9: crackle, hiss, tone, wear)")]
UI = dict(
    es=dict(title="Referencia MIDI de las funciones nuevas", md="docs/MIDI.md", html="midi.html", lang="es",
            other='<p class="lang"><a href="midi-en.html">English version</a> · <a href="guia.html">Guía por vistas</a> · <a href="index.html">Lista de características</a></p>',
            intro="Los CC / NRPN que añade el mod. Los parámetros del aparato original (sintes, drums, mixer, FX) siguen con los números de la *Programmer’s Reference Guide* de Novation. Todo respeta los filtros CC Tx / CC Rx de la vista Setup.",
            sel=("Seleccionar un NRPN", "Manda **CC 99** (MSB), **CC 98** (LSB) y **CC 6** (valor), en ese orden. El aparato recuerda el NRPN elegido hasta el siguiente CC 99 / 98."),
            eng=("Motor de las pistas MIDI (MIDI 1 / 2)", "Canal de la pista MIDI. Valores 0-127; los bipolares, 64 = centro. Sale al girar el knob (también con Clear) y entra por el mismo número. «Página / knob» = dónde está en la vista Preset con el motor encendido (pads 1-5 = páginas). En el motor granular la página 2 usa los mismos números con otro significado (entre paréntesis)."),
            eng_cols=("Código", "Parámetro", "Mensaje", "Página / knob"),
            auto="**Página 4** (secuenciables: se graban en el patrón con Record): TUNE, Release, Envolvente → nivel, Envolvente → filtro, Filtro, Resonancia, Velocidad del LFO, Efecto. *Solo Beta 3.22:* los ocho destinos se eligen con Shift + knob.",
            drum=("Drums", "Canal de drums (Setup). **CC 99 = 5, 6, 7, 8** (Drum 1-4), **CC 98 = LSB**, **CC 6 = valor**. Los knobs de stock (pitch, decay, distortion, EQ) siguen con sus CC originales. *Solo Beta 3.22:* con el **modo General MIDI** (vista Setup, K4) las notas de Drum 1-4 salen con la nota GM de cada uno (K5-K8, 35-81; de fábrica 36 / 38 / 42 / 46) en lugar de 60 / 62 / 64 / 65."),
            drum_cols=("LSB", "Parámetro", "Valores"),
            gfx=("Master FX", "Canal 16. **CC 99 = 9**, **CC 98 = 4 × efecto + knob** (knob 0-3 = K1-K4), **CC 6 = valor**."), gfx_cols=("LSB", "Efecto", "K1-K4"),
            pgm=("Program Change", "**Proyecto:** canal de escucha y canal de salida en la vista Setup, pads 29 / 30 (16 por defecto; desde RC2); lo recibido en el de escucha se reenvía por el de salida. **Patch flip:** cada nota de MIDI 1 / 2 sale como Program Change por el canal de la pista (vista Preset de MIDI, pad 26). **Notas de entrada (desde RC2.08):** las notas que llegan por el canal de MIDI 1 / 2 tocan su sinte propio y se graban; no se reenvían a la salida. *Solo Beta 3.22:* con la **fusión USB** (Advanced Setup, pad 23) todo lo que entra por el DIN In sale también por USB (sin su reloj con Clock Tx, sin SysEx).")),
    en=dict(title="MIDI reference of the new features", md="docs/MIDI.en.md", html="midi-en.html", lang="en",
            other='<p class="lang"><a href="midi.html">Versión en español</a> · <a href="guide.html">Guide by views</a> · <a href="en.html">Feature list</a></p>',
            intro="The CCs / NRPNs the mod adds. The original device's parameters (synths, drums, mixer, FX) keep the numbers of Novation’s *Programmer’s Reference Guide*. Everything follows the CC Tx / CC Rx filters of the Setup view.",
            sel=("Selecting an NRPN", "Send **CC 99** (MSB), **CC 98** (LSB) and **CC 6** (value), in that order. The device remembers the chosen NRPN until the next CC 99 / 98."),
            eng=("MIDI track engine (MIDI 1 / 2)", "The MIDI track's channel. Values 0-127; bipolar ones, 64 = centre. Sent when the knob turns (also with Clear) and received on the same number. «Page / knob» = where it is in the Preset view with the engine on (pads 1-5 = pages). In the granular engine page 2 uses the same numbers with another meaning (in brackets)."),
            eng_cols=("Code", "Parameter", "Message", "Page / knob"),
            auto="**Page 4** (sequenceable: recorded into the pattern with Record): TUNE, Release, Envelope → level, Envelope → filter, Filter, Resonance, LFO speed, Effect. *Beta 3.22 only:* the eight destinations are chosen with Shift + knob.",
            drum=("Drums", "The drums channel (Setup). **CC 99 = 5, 6, 7, 8** (Drum 1-4), **CC 98 = LSB**, **CC 6 = value**. The stock knobs (pitch, decay, distortion, EQ) keep their original CCs. *Beta 3.22 only:* with the **General MIDI mode** (Setup view, K4) the notes of Drum 1-4 go out as each one's GM note (K5-K8, 35-81; by default 36 / 38 / 42 / 46) instead of 60 / 62 / 64 / 65."),
            drum_cols=("LSB", "Parameter", "Values"),
            gfx=("Master FX", "Channel 16. **CC 99 = 9**, **CC 98 = 4 × effect + knob** (knob 0-3 = K1-K4), **CC 6 = value**."), gfx_cols=("LSB", "Effect", "K1-K4"),
            pgm=("Program Change", "**Project:** listen and output channel in the Setup view, pads 29 / 30 (16 by default; since RC2); what arrives on the listen channel is sent again on the output one. **Patch flip:** every note of MIDI 1 / 2 goes out as a Program Change on the track's channel (MIDI Preset view, pad 26). **Notes coming in (since RC2.08):** notes arriving on the channel of MIDI 1 / 2 play its own synth and are recorded; they are not sent again to the output. *Beta 3.22 only:* with the **USB merge** (Advanced Setup, pad 23) everything coming in on the DIN In also goes out over USB (without its clock with Clock Tx, without SysEx).")))


def sections(lang):
    """-> [(heading, markdown)]"""
    import vcf21
    U = UI[lang]; es = lang == "es"
    eng = ["| " + " | ".join(U["eng_cols"]) + " |", "|---|---|---|---|"]
    for code, n_es, n_en, where in ENGINE:
        t, n = vcf21.CC_TAB[code]
        eng.append(f"| {code} | {n_es if es else n_en} | {'CC %d' % n if t == 0 else 'NRPN %d:%d' % (t & 0x7F, n)} | {where} |")
    drum = ["| " + " | ".join(U["drum_cols"]) + " |", "|---|---|---|"] + [f"| {l} | {a if es else b} | {c if es else d} |" for l, a, b, c, d in DRUMS]
    gfx = ["| " + " | ".join(U["gfx_cols"]) + " |", "|---|---|---|"] + [f"| {4 * i}-{4 * i + 3} | {n} | {a if es else b} |" for i, (n, a, b) in enumerate(GFX)]
    return [(U["sel"][0], U["sel"][1]), (U["eng"][0], U["eng"][1] + "\n\n" + "\n".join(eng) + "\n\n" + U["auto"]),
            (U["drum"][0], U["drum"][1] + "\n\n" + "\n".join(drum)), (U["gfx"][0], U["gfx"][1] + "\n\n" + "\n".join(gfx)), (U["pgm"][0], U["pgm"][1])]


def write(lang, version, M):
    U = UI[lang]
    secs = sections(lang)
    md = [f"# {U['title']} — CIRCUIT-HACKS ({version})", "", U["intro"], ""]
    for h, t in secs: md += [f"## {h}", "", t, ""]
    (ROOT / U["md"]).write_text("\n".join(md), encoding="utf-8", newline="")
    parts = [f'<!doctype html><html lang="{U["lang"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(U["title"])}</title>',
             f"<style>{M.CSS}</style></head><body>", f'<header class="cover"><h1>CIRCUIT-HACKS</h1><p>{html.escape(U["title"])}</p><p>{html.escape(version)}</p><div class="bar"></div></header><main>',
             U["other"], M.md2html(U["intro"])]
    for h, t in secs: parts.append(f'<section class="feat"><h3>{html.escape(h)}</h3>{M.md2html(t)}</section>')
    parts.append("</main></body></html>")
    (ROOT / "docs/manual" / U["html"]).write_text("\n".join(parts), encoding="utf-8", newline="")
