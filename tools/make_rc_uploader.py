"""tools/rc_uploader.html: a web page that takes the OFFICIAL Circuit Tracks firmware from the user, patches it in the browser and sends it (no Novation code inside).

    python tools/make_rc_uploader.py [VERSION ...]          (default: R209 R209S B3.22 R208 R208S R206 R206S R205 R205S R204 R204S R202 R202S R201 R201S RC2 RC2S RC0.9 RC0.9S; needs firmware/<dir>/*.bin and stock/*.bin of a full checkout)
Each version becomes a patch against the official image: COPY (offset, length) from the user's official image, or ADD (our bytes).  The matching is greedy
on 8-byte keys, so an ADD run never holds 8 or more consecutive bytes that also occur in the official image: the page carries only our own work.  The page:
  1. reads the official .syx (Components: https://components.novationmusic.com/api/v2/firmwares/168/file) or its .bin, checks its SHA-256;
  2. applies the patch of the chosen version, checks the SHA-256 of the result against the published one, encodes the update (same format as ct_fw.encode) and
     checks the SHA-256 of that .syx against the published one too;
  3. sends it with the pull protocol of Components (the code of tools/ct_uploader.html).  "Oficial" sends the official file untouched (to go back).
"""
from __future__ import annotations
import base64
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import ct_fw  # noqa: E402
from verify_builds import BUILDS  # noqa: E402

MIN = 8


def make_patch(src: bytes, dst: bytes):
    idx = {}
    for i in range(len(src) - MIN + 1):
        idx.setdefault(src[i:i + MIN], []).append(i)
    ops, lit, i, last = [], bytearray(), 0, -1
    def flush():
        if lit: ops.append([1, base64.b64encode(bytes(lit)).decode()]); lit.clear()
    while i < len(dst):
        best_len, best_off = 0, -1
        cands = []
        if last >= 0: cands.append(last)                      # the copy goes on where the previous one ended
        if i < len(src): cands.append(i)                      # the same place
        cands += idx.get(dst[i:i + MIN], [])[:64]
        for o in cands:
            if o < 0 or o >= len(src) or src[o:o + MIN] != dst[i:i + MIN]: continue
            n = MIN
            while i + n < len(dst) and o + n < len(src) and src[o + n] == dst[i + n]: n += 1
            if n > best_len: best_len, best_off = n, o
        if best_len >= MIN:
            flush(); ops.append([0, best_off, best_len]); i += best_len; last = best_off + best_len
        else:
            lit.append(dst[i]); i += 1; last = -1
    flush()
    return ops


def apply(src: bytes, ops):
    out = bytearray()
    for op in ops:
        out += src[op[1]:op[1] + op[2]] if op[0] == 0 else base64.b64decode(op[1])
    return bytes(out)


def main(versions):
    stock = (ROOT / "stock/circuittracks-firmware-4486-STOCK.bin").read_bytes()
    assert hashlib.sha256(stock).hexdigest() == ct_fw.STOCK_4486["image_sha256"]
    dirs = {json.loads((ROOT / "firmware" / d / "manifest.json").read_text()).get("marker", d): d for d, _, _ in BUILDS if (ROOT / "firmware" / d / "manifest.json").exists()}
    patches = {}
    for v in versions:
        d = dirs[v]; man = json.loads((ROOT / "firmware" / d / "manifest.json").read_text())
        img = next((ROOT / "firmware" / d).glob("*.bin")).read_bytes()
        ops = make_patch(stock, img)
        assert apply(stock, ops) == img
        lit = sum(len(base64.b64decode(o[1])) for o in ops if o[0] == 1)
        assert hashlib.sha256(ct_fw.encode(img)).hexdigest() == man["syx_sha256"]
        patches[v] = dict(dir=d, image_sha256=man["image_sha256"], syx_sha256=man["syx_sha256"], size=len(img), ops=ops)
        print(f"{v}: {len(ops)} ops, {lit} bytes of our own, {len(img) - lit} copied from the official image")
    page = TEMPLATE.replace("__PATCHES__", json.dumps(patches, separators=(",", ":"))).replace("__STOCK_SYX__", ct_fw.STOCK_4486["syx_sha256"]) \
        .replace("__STOCK_IMG__", ct_fw.STOCK_4486["image_sha256"]).replace("__VERSIONS__", ", ".join(versions)) \
        .replace("__SAFER__", next((v for v in versions if v.endswith("S")), versions[0]))
    (ROOT / "tools/rc_uploader.html").write_text(page, encoding="utf-8", newline="")
    print("tools/rc_uploader.html", len(page), "bytes")


DESC = {"R209": ("RC2.09 — la versión candidata 2.09: RC2.08 + un arreglo (el inicio del sample de los drums recorre todo el sample)",
                 "RC2.09 — release candidate 2.09: RC2.08 + a fix (the drums' sample start covers the whole sample)"),
        "R209S": ("RC2.09S — versión más segura: RC2.09, pero nada del mod escribe ni borra ficheros en la SD ni en la memoria interna (esas funciones no hacen nada)",
                  "RC2.09S — safer build: RC2.09, but nothing of the mod writes or deletes files on the SD card or in the internal memory (those features do nothing)"),
        "B3.22": ("Beta 3.22 — beta (= SC46.5): RC2.09 + lo de la Beta 3.21 + el K7 de los drums a la izquierda = scan del inicio; sin probar en el aparato",
                  "Beta 3.22 — beta (= SC46.5): RC2.09 + what Beta 3.21 has + the drums' K7 to the left = start scan; not tested on the device"),
        "R208": ("RC2.08 — la versión candidata 2.08: RC2.06 + dos arreglos (la longitud fija de la vista Micro Step; un teclado externo toca el sinte propio de MIDI 1 / 2)",
                 "RC2.08 — release candidate 2.08: RC2.06 + two fixes (the Micro Step view's fixed length; an external keyboard plays the MIDI 1 / 2 own synth)"),
        "R208S": ("RC2.08S — versión más segura: RC2.08, pero nada del mod escribe ni borra ficheros en la SD ni en la memoria interna (esas funciones no hacen nada)",
                  "RC2.08S — safer build: RC2.08, but nothing of the mod writes or deletes files on the SD card or in the internal memory (those features do nothing)"),
        "B3.21": ("Beta 3.21 — beta (= SC46.4): RC2.08 + lo de la Beta 3.20 (modo GM de los drums, Jankó, pantalla de acordes…) + el DIN In mezclado en la salida USB; sin probar en el aparato",
                  "Beta 3.21 — beta (= SC46.4): RC2.08 + what Beta 3.20 has (GM mode of the drums, Jankó, chord screen…) + the DIN In merged into the USB out; not tested on the device"),
        "B3.20": ("Beta 3.20 — beta (= SC46.3): RC2.08 + lo de la Beta 3.17 + modo General MIDI de los drums, disposición Jankó, pantalla de acordes y el S&H del LFO a tempo arreglado; sin probar en el aparato",
                  "Beta 3.20 — beta (= SC46.3): RC2.08 + what Beta 3.17 has + General MIDI mode of the drums, Jankó layout, chord screen and the synced LFO's S&H fixed; not tested on the device"),
        "R206": ("RC2.06 — la versión candidata 2.06: RC2.05 + un arreglo (dos pads de la misma nota mantenidos a la vez ya no dejan la nota colgada)",
                 "RC2.06 — release candidate 2.06: RC2.05 + a fix (two pads of the same note held together no longer leave the note hanging)"),
        "R206S": ("RC2.06S — versión más segura: RC2.06, pero nada del mod escribe ni borra ficheros en la SD ni en la memoria interna (esas funciones no hacen nada)",
                  "RC2.06S — safer build: RC2.06, but nothing of the mod writes or deletes files on the SD card or in the internal memory (those features do nothing)"),
        "B3.15": ("Beta 3.15 — beta (= SC45.8): RC2.06 + lo de la Beta 3.14 (FM de 4 operadores…) + en el teclado partido, un botón de pista mantenido = sus knobs; sin probar en el aparato",
                  "Beta 3.15 — beta (= SC45.8): RC2.06 + what Beta 3.14 has (4-operator FM…) + on the split keyboard, a track button held = its knobs; not tested on the device"),
        "B3.17": ("Beta 3.17 — beta (= SC46): RC2.06 + lo de la Beta 3.15 + el sinte propio de MIDI 1 / 2 guardado con el proyecto + los destinos de la página 4 en los pads; sin probar en el aparato",
                  "Beta 3.17 — beta (= SC46): RC2.06 + what Beta 3.15 has + the MIDI 1 / 2 own synth saved with the project + the page 4 destinations on the pads; not tested on the device"),
        "R205": ("RC2.05 — la versión candidata 2.05: RC2.04 + un arreglo (cambiar la escala propia con el transporte en marcha ya no cuelga el aparato)",
                 "RC2.05 — release candidate 2.05: RC2.04 + a fix (changing the custom scale with the transport running no longer hangs the device)"),
        "R205S": ("RC2.05S — versión más segura: RC2.05, pero nada del mod escribe ni borra ficheros en la SD ni en la memoria interna (esas funciones no hacen nada)",
                  "RC2.05S — safer build: RC2.05, but nothing of the mod writes or deletes files on the SD card or in the internal memory (those features do nothing)"),
        "B3.14": ("Beta 3.14 — beta (= SC45.7): RC2.05 + lo de la Beta 3.12 + FM de 4 operadores en el sinte propio de MIDI 1 / 2 (16 algoritmos: clásicos, percusivos, campanas, cuerdas), sin probar en el aparato",
                  "Beta 3.14 — beta (= SC45.7): RC2.05 + what Beta 3.12 has + 4-operator FM in the MIDI 1 / 2 own synth (16 algorithms: classic, percussive, bells, strings), not tested on the device"),
        "R204": ("RC2.04 — la versión candidata 2.04: RC2.02 + arreglos (la cuenta atrás al tempo del proyecto, notas grabadas de más de 16 pasos sin cortar, sample mantenido + paso en el selector de samples)",
                 "RC2.04 — release candidate 2.04: RC2.02 + fixes (the count-in at the project tempo, recorded notes longer than 16 steps not cut, held sample + step in the sample picker)"),
        "R204S": ("RC2.04S — versión más segura: RC2.04, pero nada del mod escribe ni borra ficheros en la SD ni en la memoria interna (esas funciones no hacen nada)",
                  "RC2.04S — safer build: RC2.04, but nothing of the mod writes or deletes files on the SD card or in the internal memory (those features do nothing)"),
        "R202": ("RC2.02 — la versión candidata 2.02 (= SC44.3): RC2.01 + matriz de modulación del sinte propio de MIDI 1 / 2, teclado partido con cualquier par de pistas de notas, LFO con triángulo por defecto y sample & hold suavizado",
                 "RC2.02 — release candidate 2.02 (= SC44.3): RC2.01 + mod matrix of the MIDI 1 / 2 own synth, split keyboard with any pair of note tracks, LFO with a triangle by default and slewed sample & hold"),
        "R202S": ("RC2.02S — versión más segura: RC2.02, pero nada del mod escribe ni borra ficheros en la SD ni en la memoria interna (esas funciones no hacen nada)",
                  "RC2.02S — safer build: RC2.02, but nothing of the mod writes or deletes files on the SD card or in the internal memory (those features do nothing)"),
        "R201": ("RC2.01 — la versión candidata 2.01 (= SC44.1): RC2 + el sample capturado antes del filtro master",
                 "RC2.01 — release candidate 2.01 (= SC44.1): RC2 + the captured sample before the master filter"),
        "R201S": ("RC2.01S — versión más segura: RC2.01, pero nada del mod escribe ni borra ficheros en la SD ni en la memoria interna (esas funciones no hacen nada)",
                  "RC2.01S — safer build: RC2.01, but nothing of the mod writes or deletes files on the SD card or in the internal memory (those features do nothing)"),
        "B3.12": ("Beta 3.12 — beta (= SC45.5): RC2.04 + granular en estéreo, LFO a tempo, destinos de la página 4 y Record + paso, soltar la automatización por paso, fila de motores, banco de acordes, arpegiador en orden pulsado y con random-mutate, supersaw y triángulo exponencial. Funciones nuevas sin probar",
                  "Beta 3.12 — beta (= SC45.5): RC2.04 + stereo granular, tempo-synced LFO, page 4 destinations and Record + step, per-step automation release, engine row, chord bank, arpeggiator in pressed order and with random-mutate, supersaw and exponential triangle. New features not yet tested"),
        "B3.3": ("Beta 3.3 — beta (= SC44.6): RC2.02 + vista FX: Shift + Octave ▲ / ▼ = resonancia del filtro master de 16 en 16; Shift + pad 25 = filtro master apagado / encendido. Funciones nuevas sin probar",
                 "Beta 3.3 — beta (= SC44.6): RC2.02 + FX view: Shift + Octave ▲ / ▼ = master filter resonance in steps of 16; Shift + pad 25 = master filter off / on. New features not yet tested"),
        "B3.0": ("Beta 3.0 — beta (= SC44.3): RC2.01 + matriz de modulación del sinte propio de MIDI 1 / 2 (pad 6: K1-K8 = ocho fuentes, la posición del knob = destino y cantidad), teclado partido con cualquier par de pistas de notas, LFO con triángulo por defecto y sample & hold suavizado",
                 "Beta 3.0 — beta (= SC44.3): RC2.01 + mod matrix of the own synth of MIDI 1 / 2 (pad 6: K1-K8 = eight sources, the knob position = destination and amount), split keyboard with any pair of note tracks, LFO with triangle by default and smoothed sample & hold"),
        "RC2": ("RC2 — la versión candidata 2 (= Beta 1.30 / SC44): RC0.9 + todo lo de las betas 1.0-1.30",
                "RC2 — release candidate 2 (= Beta 1.30 / SC44): RC0.9 + everything of betas 1.0-1.30"),
        "RC2S": ("RC2S — versión más segura: RC2, pero nada del mod escribe ni borra ficheros en la SD ni en la memoria interna (esas funciones no hacen nada)",
                 "RC2S — safer build: RC2, but nothing of the mod writes or deletes files on the SD card or in the internal memory (those features do nothing)"),
        "RC0.9": ("RC0.9 — la versión completa: RC0.8 + el pack de la memoria interna, de solo lectura para el mod",
                  "RC0.9 — full version: RC0.8 + the internal memory pack, read only for the mod"),
        "RC0.9S": ("RC0.9S — versión más segura (= RC0.8S): nada del mod escribe ficheros en la SD ni en la memoria interna",
                   "RC0.9S — safer build (= RC0.8S): nothing of the mod writes files to the SD card or to the internal memory"),
        "B1.30": ("Beta 1.30 — beta (= SC44): Beta 1.29 + modo muestra del sinte propio de MIDI 1 / 2: un sample del pack a la altura de la nota, selector en la vista Note ampliada y sample flips por paso",
                  "Beta 1.30 — beta (= SC44): Beta 1.29 + sample mode of the own synth of MIDI 1 / 2: a pack sample at the note's pitch, a picker in the expanded Note view and sample flips per step"),
        "B1.29": ("Beta 1.29 — beta (= SC43.9): Beta 1.28 + seis formas del LFO del sinte propio (página 5, Shift + K8), el programa del DSP compactado",
                  "Beta 1.29 — beta (= SC43.9): Beta 1.28 + six LFO shapes for the own synth (page 5, Shift + K8), the DSP program compacted"),
        "B1.28": ("Beta 1.28 — beta (= SC43.8): Beta 1.27 + sidechain de drums con Synth 1 / 2 y MIDI 1 / 2, el sinte propio guardado entero al apagar",
                  "Beta 1.28 — beta (= SC43.8): Beta 1.27 + drum side-chain from Synth 1 / 2 and MIDI 1 / 2, the own synth fully saved over a power cycle"),
        "B1.27": ("Beta 1.27 — beta (= SC43.7): Beta 1.26 + pitch de drums continuo (K1) y cromático (pads) a la vez, el panorama de drums de vuelta, Clear + Drum, Shift + Play = cuantizar, arpegiador en MIDI 1 / 2",
                  "Beta 1.27 — beta (= SC43.7): Beta 1.26 + drum pitch continuous (K1) and chromatic (pads) together, the drums' pan back, Clear + Drum, Shift + Play = quantize, arpeggiator on MIDI 1 / 2"),
        "B1.26": ("Beta 1.26 — beta (= SC43.6): Beta 1.25 + modo cue en el Mixer (mezcla mono a la izquierda, cue a la derecha), la vista cromática de drums graba por paso",
                  "Beta 1.26 — beta (= SC43.6): Beta 1.25 + cue mode in the Mixer (mono mix on the left, cue on the right), the drums' chromatic view records per step"),
        "B1.25": ("Beta 1.25 — beta (= SC43.5): Beta 1.24 + pitch de drums cromático (K1) y continuo de stock (Shift + K6), Clear + Synth = macros del patch",
                  "Beta 1.25 — beta (= SC43.5): Beta 1.24 + drum pitch chromatic (K1) and the stock continuous one (Shift + K6), Clear + Synth = the patch's macros"),
        "B1.24": ("Beta 1.24 — beta (= SC43.4): Beta 1.23 + sidechain disparado por patrones de Synth / MIDI, mute al compás siguiente, Clear + botón de drum, step-drummer bipolar",
                  "Beta 1.24 — beta (= SC43.4): Beta 1.23 + sidechain triggered by Synth / MIDI patterns, mute on the next bar, Clear + drum button, bipolar step-drummer"),
        "B1.23": ("Beta 1.23 — beta (= SC43.3): Beta 1.22 + step-drummer de MIDI: cada knob desde el punto sin modulación de su destino, con el LED según la cantidad",
                  "Beta 1.23 — beta (= SC43.3): Beta 1.22 + MIDI step-drummer: each knob from its destination's point of no modulation, the LED showing the amount"),
        "B1.22": ("Beta 1.22 — beta (= SC43.2): Beta 1.21 + arreglo: con el arpegiador, los acordes se graban enteros en todo el patrón",
                  "Beta 1.22 — beta (= SC43.2): Beta 1.21 + fix: with the arpeggiator, chords are recorded whole across the pattern"),
        "B1.21": ("Beta 1.21 — beta (= SC43.1): Beta 1.20 + arreglo: los golpes de los rollers y del arpegio de drums con el transporte parado ya no dejan sus cuadros en blanco ni la nota MIDI colgada",
                  "Beta 1.21 — beta (= SC43.1): Beta 1.20 + fix: the drum rollers' and drum arpeggio's hits with the transport stopped no longer leave their boxes white or the MIDI note hanging"),
        "B1.20": ("Beta 1.20 — beta (= SC43): Beta 1.19 + frecuencia, dinámicas y random-mutate del sample en los drums, y los golpes grabados por rollers / arpegio ya no se pierden",
                  "Beta 1.20 — beta (= SC43): Beta 1.19 + frequency, dynamics and sample random-mutate on the drums, and hits recorded by rollers / arpeggio are no longer lost"),
        "B1.19": ("Beta 1.19 — beta (= SC42.9): Beta 1.18 + el arpegio de los drums se graba con Record",
                  "Beta 1.19 — beta (= SC42.9): Beta 1.18 + the drums' arpeggio recorded with Record"),
        "B1.18": ("Beta 1.18 — beta (= SC42.8): Beta 1.17 + el arpegiador de los drums (salta entre los samples mantenidos en la vista Preset)",
                  "Beta 1.18 — beta (= SC42.8): Beta 1.17 + the drums' arpeggiator (it jumps between the samples held in the Preset view)"),
        "B1.17": ("Beta 1.17 — beta (= SC42.7): Beta 1.16 + step-drummer desde 0 y transposición más gruesa, toggles de la vista Micro Step, rollers con el transporte parado",
                  "Beta 1.17 — beta (= SC42.7): Beta 1.16 + step-drummer from 0 and a coarser transposition, the Micro Step view's toggles, rollers with the transport stopped"),
        "B1.16": ("Beta 1.16 — beta (= SC42.6): Beta 1.3 + arpegiador, escala propia, metrónomo con cuenta atrás, gate por pulsación y longitud fija, rollers de drums, página 2 y toggle pitch-vel del step-drummer, sidechain de drums con knobs, canales de Program Change, sin el stutter del delay",
                  "Beta 1.16 — beta (= SC42.6): Beta 1.3 + arpeggiator, custom scale, metronome with count-in, gate by holding and fixed length, drum rollers, the step-drummer's page 2 and pitch-vel toggle, drum sidechain on the knobs, Program Change channels, no delay stutter"),
        "B1.3": ("Beta 1.3 — beta (= SC41.3): Beta 1.2 + el pack de la memoria interna, de solo lectura para el mod",
                 "Beta 1.3 — beta (= SC41.3): Beta 1.2 + the internal memory pack, read only for the mod"),
        "RC0.8": ("RC0.8 — la versión completa: RC0.7 + un arreglo (los knobs de pitch del step-drummer conservan su valor)",
                  "RC0.8 — full version: RC0.7 + one fix (the pitch knobs of the step-drummer keep their value)"),
        "RC0.8S": ("RC0.8S — versión más segura (= RC0.7S + el arreglo de RC0.8): nada del mod escribe ficheros en la SD",
                   "RC0.8S — safer build (= RC0.7S + the RC0.8 fix): nothing of the mod writes files to the SD card"),
        "B1.2": ("Beta 1.2 — beta (= SC41.2): Beta 1.1 + una regla de cadena fuera de rango ya no lee fuera de la memoria",
                 "Beta 1.2 — beta (= SC41.2): Beta 1.1 + a chain rule out of range no longer reads outside the memory"),
        "B1.1": ("Beta 1.1 — beta (= SC41.1): Beta 1.0 + los arreglos de RC0.8, la vista Master FX ya no pisa el estado de otras funciones, valor random del secuenciador de efectos",
                 "Beta 1.1 — beta (= SC41.1): Beta 1.0 + the RC0.8 fix, the Master FX view no longer overwrites the state of other features, random value of the FX sequencer"),
        "RC0.7": ("RC0.7 — la versión completa: RC0.6 + dos arreglos (el step-drummer y el secuenciador de efectos siguen el patrón de su propia pista; knob selector del secuenciador de efectos más lento)",
                  "RC0.7 — full version: RC0.6 + two fixes (the step-drummer and the FX sequencer follow the pattern of their own track; slower selector knob of the FX sequencer)"),
        "RC0.7S": ("RC0.7S — versión más segura (= RC0.6S + los arreglos de RC0.7): nada del mod escribe ficheros en la SD",
                   "RC0.7S — safer build (= RC0.6S + the RC0.7 fixes): nothing of the mod writes files to the SD card"),
        "B1.0": ("Beta 1.0 — beta (= SC40.9): RC0.7 + cadenas de patrones y escenas, Nudge y órdenes fractal / deconstruido, frecuencia y dinámicas por paso, gesto mecánico, Master FX por sesión, knobs de sidechain y compresor, patches propios entre packs y lo de las betas anteriores",
                 "Beta 1.0 — beta (= SC40.9): RC0.7 + pattern chains and scenes, Nudge and the fractal / deconstructed orders, step frequency and dynamics, mechanical gesture, Master FX per session, side-chain and compressor knobs, own-synth patches between packs and what the earlier betas had"),
        "RC0.6": ("RC0.6 — la versión completa: RC0.5 + dos arreglos (el LFO del Auto-Filter y del Phaser arranca al activar el efecto; el blanco tenue de Clear ya no pulsa)",
                  "RC0.6 — full version: RC0.5 + two fixes (the LFO of the Auto-Filter and of the Phaser starts when the effect comes on; the dim white of Clear no longer pulses)"),
        "RC0.6S": ("RC0.6S — versión más segura (= RC0.5S + los arreglos de RC0.6): nada del mod escribe ficheros en la SD",
                   "RC0.6S — safer build (= RC0.5S + the RC0.6 fixes): nothing of the mod writes files to the SD card"),
        "RC0.5": ("RC0.5 — la versión completa: RC0.4 + el sample capturado pasa por los efectos de Master FX (la captura ya no los graba)",
                  "RC0.5 — full version: RC0.4 + the captured sample goes through the Master FX effects (the capture no longer records them)"),
        "RC0.5S": ("RC0.5S — versión más segura (= RC0.4S + el arreglo de RC0.5): nada del mod escribe ficheros en la SD",
                   "RC0.5S — safer build (= RC0.4S + the RC0.5 fix): nothing of the mod writes files to the SD card"),
        "BETA5": ("BETA5 — beta, sin probar en el aparato (= SC39.6): BETA4 + copiar proyectos a otro hueco o a otro pack, knobs de tipo en colores",
                  "BETA5 — beta, not tested on the device (= SC39.6): BETA4 + copying projects to another slot or another pack, type knobs as colours"),
        "BETA4": ("BETA4 — beta, sin probar en el aparato (= SC39.4): BETA3 + guardar el patch del sinte en el pack, destinos de los macro knobs, gestos nuevos de los patches del sinte propio",
                  "BETA4 — beta, not tested on the device (= SC39.4): BETA3 + saving the synth’s patch into the pack, macro knob destinations, new gestures for the own-synth patches"),
        "BETA3": ("BETA3 — beta, sin probar en el aparato (= SC39.2): RC0.5 + lo de BETA2 (patches del sinte propio de MIDI 1 / 2, Clear + pad de página, selector de fuente del granular, random-mutate, teclado partido…)",
                  "BETA3 — beta, not tested on the device (= SC39.2): RC0.5 + what BETA2 has (patches of the MIDI 1 / 2 own synth, Clear + page pad, granular source selector, random-mutate, split keyboard…)"),
        "RC0.4": ("RC0.4 — la versión completa: RC0.3 + arreglos (captura armada desde el primer pulso de Play, Shift + pad 7 = bucle enganchado, Duplicate entre packs a huecos vacíos, Clear blanco fijo en la vista de packs)",
                  "RC0.4 — full version: RC0.3 + fixes (armed capture from the first beat of Play, Shift + pad 7 = latched loop, Duplicate between packs to empty slots, Clear steady white in the packs view)"),
        "RC0.4S": ("RC0.4S — versión más segura (= RC0.3S + los arreglos de RC0.4 fuera de la SD): nada del mod escribe ficheros en la SD",
                   "RC0.4S — safer build (= RC0.3S + the RC0.4 fixes outside the SD card): nothing of the mod writes files to the SD card"),
        "BETA2": ("BETA2 — beta (= SC39.1): BETA1 + patches del sinte propio de MIDI 1 / 2 (64 huecos en el pack), Clear + pad de página, selector de fuente del granular",
                  "BETA2 — beta (= SC39.1): BETA1 + patches of the MIDI 1 / 2 own synth (64 slots in the pack), Clear + page pad, granular source selector"),
        "BETA1": ("BETA1 — beta (= SC39): BETA0 + random-mutate por paso (fila 4 de la vista de probabilidad), teclado partido Synth 1 + Synth 2, patches de sinte por modo de voz",
                  "BETA1 — beta (= SC39): BETA0 + random-mutate per step (row 4 of the probability view), split keyboard Synth 1 + Synth 2, synth patches by voice mode"),
        "BETA0": ("BETA0 — beta, sin probar en el aparato (= SC38.7): RC0.4 + stretch del granular, MIDI Thru Merge / Filter, Clear + pad 27 = valores iniciales del motor",
                  "BETA0 — beta, not tested on the device (= SC38.7): RC0.4 + granular stretch, MIDI Thru Merge / Filter, Clear + pad 27 = engine initial values"),
        "RC0.3": ("RC0.3 — la versión completa (= SC38): RC0.2 + Shift + knob en el Mixer (nivel 100 / 0), Clear + knob en Master FX, Clear + pad para sustituir un drum por la captura, copias entre packs en su sitio y arreglos",
                  "RC0.3 — full version (= SC38): RC0.2 + Shift + knob in the Mixer (level 100 / 0), Clear + knob in Master FX, Clear + pad to replace a drum with the capture, copies between packs in place and fixes"),
        "RC0.3S": ("RC0.3S — versión más segura (= RC0.2S + lo de RC0.3 fuera de la SD): nada del mod escribe ficheros en la SD",
                   "RC0.3S — safer build (= RC0.2S + what RC0.3 adds outside the SD card): nothing of the mod writes files to the SD card"),
        "RC0.2": ("RC0.2 — la versión completa (= SC37.5): RC0.1 + sobrecarga simulada en el Glitch (K4 arriba) y LED de Clear al borrar packs",
                  "RC0.2 — full version (= SC37.5): RC0.1 + simulated overload in the Glitch (K4 up) and the Clear LED when deleting packs"),
        "RC0.2S": ("RC0.2S — versión más segura (= RC0.1S + la sobrecarga del Glitch): nada del mod escribe ficheros en la SD",
                   "RC0.2S — safer build (= RC0.1S + the Glitch overload): nothing of the mod writes files to the SD card"),
        "RC0.1": ("RC0.1 — la versión completa (= SC37.4): RC0 + Duplicate en la Preset de sinte, copiar samples y patches entre packs, cambio de motor sin clic, dos Glitch independientes",
                  "RC0.1 — full version (= SC37.4): RC0 + Duplicate in the synth Preset view, copy samples and patches between packs, engine change without a click, two independent Glitches"),
        "RC0.1S": ("RC0.1S — versión más segura (= RC0S + lo de SC37.4 fuera de la SD): nada del mod escribe ficheros en la SD",
                   "RC0.1S — safer build (= RC0S + what SC37.4 adds outside the SD card): nothing of the mod writes files to the SD card"),
        "RC0": ("RC0 — la versión completa (= SC36.2): sinte granular, Glitch, secuenciador de efectos, gestión del pack en la SD",
                "RC0 — full version (= SC36.2): granular synth, Glitch, FX sequencer, pack management on the SD card"),
        "RC0S": ("RC0S — versión más segura (= SC362S): nada del mod escribe ficheros en la SD",
                 "RC0S — safer build (= SC362S): nothing of the mod writes files to the SD card")}

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CIRCUIT-HACKS RC Uploader</title>
<style>
  :root { --bg:#111317; --panel:#1a1d23; --line:#2b2f38; --ink:#e8e9ec; --dim:#9aa0ab; --ok:#7ee787; --warn:#ffb86b; --bad:#ff7b72; --acc:#79c0ff; }
  * { box-sizing:border-box; }
  body { margin:0; padding:24px 16px 64px; background:var(--bg); color:var(--ink); font:15px/1.55 system-ui,"Segoe UI",sans-serif; }
  main { max-width:760px; margin:0 auto; }
  h1 { font-size:1.4rem; margin:0 0 4px; }
  .sub { color:var(--dim); margin:0 0 20px; }
  section { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:14px 16px; margin-bottom:12px; }
  h2 { font-size:.8rem; letter-spacing:.08em; text-transform:uppercase; color:var(--dim); margin:0 0 10px; }
  button { font:inherit; font-weight:600; background:var(--acc); color:#0b0d10; border:0; border-radius:7px; padding:8px 14px; cursor:pointer; }
  button:disabled { background:#363b45; color:#7c838f; cursor:not-allowed; }
  select, input[type=file] { font:inherit; color:var(--ink); background:#0f1114; border:1px solid var(--line); border-radius:7px; padding:6px; width:100%; }
  .row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
  .mono { font-family:ui-monospace,Consolas,monospace; font-size:.82rem; word-break:break-all; }
  .ok { color:var(--ok); } .bad { color:var(--bad); } .warn { color:var(--warn); }
  #log { height:220px; overflow:auto; background:#0b0d10; border:1px solid var(--line); border-radius:7px; padding:8px; white-space:pre-wrap; }
  progress { width:100%; height:14px; }
  ol { margin:0; padding-left:20px; } a { color:var(--acc); }
  .note { border-left:4px solid var(--warn); padding-left:10px; }
  .sub-steps { margin:4px 0 0; }
  html[lang="es"] .en, html[lang="en"] .es { display:none !important; }
  .top { display:flex; justify-content:space-between; align-items:baseline; gap:12px; flex-wrap:wrap; }
  .lang { display:flex; gap:4px; }
  .lang button { font-size:.8rem; padding:4px 10px; background:#2b2f38; color:var(--ink); }
  .lang button.on { background:var(--acc); color:#0b0d10; }
</style>
</head>
<body>
<main>
  <div class="top"><h1>CIRCUIT-HACKS · RC Uploader</h1>
    <div class="lang" role="group" aria-label="Idioma / Language"><button type="button" data-lang="es">Español</button><button type="button" data-lang="en">English</button></div></div>
  <p class="sub"><span class="es">Parchea en tu navegador el firmware oficial del Circuit Tracks con el mod CIRCUIT-HACKS (__VERSIONS__) y lo envía al aparato. Esta página no contiene código de Novation: solo el trabajo del mod.</span><span class="en">Patches the official Circuit Tracks firmware with the CIRCUIT-HACKS mod (__VERSIONS__) in your browser and sends it to the device. This page contains no Novation code: only the mod’s own work.</span></p>

  <section>
    <h2><span class="es">Antes de empezar</span><span class="en">Before you start</span></h2>
    <ol>
      <li class="note"><span class="es"><b>Haz una copia de seguridad de la tarjeta SD</b> (proyectos, packs y samples) y no trabajes con proyectos importantes mientras pruebas el mod. No se han reportado fallos, pero las versiones están en prueba. Si no quieres arriesgar la SD, elige __SAFER__.</span><span class="en"><b>Back up the SD card</b> (projects, packs and samples) and do not work on important projects while you test the mod. No failures have been reported, but the versions are being tested. If you do not want to risk the card, pick __SAFER__.</span></li>
      <li><span class="es">Descarga el firmware oficial <b>Circuit Tracks 1.2.1 (build 4486)</b> desde Novation: <a href="https://components.novationmusic.com/api/v2/firmwares/168/file" target="_blank" rel="noopener">circuittracks-firmware-4486.syx</a> (descarga directa de Novation Components: el navegador guarda el <code>.syx</code>, 432 961 bytes). Novation Components: <a href="https://components.novationmusic.com/" target="_blank" rel="noopener">components.novationmusic.com</a>.</span><span class="en">Download the official <b>Circuit Tracks 1.2.1 (build 4486)</b> firmware from Novation: <a href="https://components.novationmusic.com/api/v2/firmwares/168/file" target="_blank" rel="noopener">circuittracks-firmware-4486.syx</a> (Novation Components’ direct download: the browser saves the <code>.syx</code>, 432,961 bytes). Novation Components: <a href="https://components.novationmusic.com/" target="_blank" rel="noopener">components.novationmusic.com</a>.</span></li>
      <li><span class="es">Cierra Novation Components y cualquier DAW o programa MIDI (en Windows, un puerto MIDI solo lo puede abrir una aplicación).</span><span class="en">Close Novation Components and any DAW or MIDI program (on Windows a MIDI port can only be opened by one application).</span></li>
      <li><span class="es">Conecta el Circuit Tracks por USB y enciéndelo de forma normal (o en modo bootloader: Scales + Preset + Note al encender). No lo desconectes durante el envío.</span><span class="en">Connect the Circuit Tracks over USB and power it on normally (or in bootloader mode: Scales + Preset + Note at power-on). Do not disconnect it while sending.</span></li>
      <li><span class="es">Usa Chrome o Edge (Web MIDI con SysEx).</span><span class="en">Use Chrome or Edge (Web MIDI with SysEx).</span></li>
      <li class="note"><div class="es"><b>En caso de brick</b> (el aparato no arranca):<ol class="sub-steps"><li>Desconéctalo de la corriente.</li><li>Pulsa el botón de apagado 15-30 s.</li><li>Mantén <b>Scales + Preset + Note</b> mientras lo enciendes.</li><li>Sube la última versión estable o el firmware de stock («Oficial») a través de esta misma página.</li></ol></div><div class="en"><b>If the device is bricked</b> (it does not start):<ol class="sub-steps"><li>Unplug it from power.</li><li>Press the power button for 15-30 s.</li><li>Hold <b>Scales + Preset + Note</b> while you power it on.</li><li>Send the latest stable version or the stock firmware (“Official”) with this same page.</li></ol></div></li>
    </ol>
  </section>

  <section>
    <h2><span class="es">1 · Firmware oficial</span><span class="en">1 · Official firmware</span></h2>
    <input type="file" id="file" accept=".syx,.bin">
    <div id="fileInfo" class="mono" style="margin-top:8px"></div>
  </section>

  <section>
    <h2><span class="es">2 · Versión</span><span class="en">2 · Version</span></h2>
    <select id="ver"></select>
    <div id="verInfo" class="mono" style="margin-top:8px"></div>
    <label id="ackRow" class="row" style="margin-top:10px;align-items:flex-start;display:none"><input type="checkbox" id="ack" style="margin-top:3px"><span><span class="es">He copiado los datos de la tarjeta microSD a otro almacenamiento y no usaré la memoria interna de Circuit para guardar proyectos.</span><span class="en">I have copied the data of the microSD card to another storage and I will not use the Circuit’s internal memory to save projects.</span></span></label>
  </section>

  <section>
    <h2>3 · MIDI</h2>
    <div class="row"><button id="btnMidi"><span class="es">Permitir acceso MIDI</span><span class="en">Allow MIDI access</span></button><span id="midiState" class="warn"></span></div>
    <p><span class="es">Salida hacia el Tracks</span><span class="en">Output to the Tracks</span></p><select id="outSel"></select>
    <p><span class="es">Entrada desde el Tracks</span><span class="en">Input from the Tracks</span></p><select id="inSel"></select>
    <div class="row" style="margin-top:10px"><button id="btnId" disabled><span class="es">Identificar</span><span class="en">Identify</span></button><span id="idState"></span></div>
  </section>

  <section>
    <h2><span class="es">4 · Envío</span><span class="en">4 · Send</span></h2>
    <div class="row"><button id="btnSend" disabled><span class="es">Enviar</span><span class="en">Send</span></button><button id="btnAbort" disabled><span class="es">Cancelar</span><span class="en">Cancel</span></button></div>
    <p id="phase" class="warn"></p>
    <progress id="prog" value="0" max="100"></progress>
    <p class="sub"><span class="es">Durante el envío el Circuit Tracks pide confirmación: pulsa <b>Play</b> en el aparato. Para volver al firmware oficial, elige «Oficial» y envíalo, o usa Novation Components.</span><span class="en">While sending, the Circuit Tracks asks for confirmation: press <b>Play</b> on the device. To go back to the official firmware, pick “Official” and send it, or use Novation Components.</span></p>
  </section>

  <section>
    <h2><span class="es">Registro</span><span class="en">Log</span></h2>
    <div id="log" class="mono"></div>
  </section>
  <p class="sub"><span class="es">CIRCUIT-HACKS no está afiliado a Novation. Circuit Tracks, Components y Novation son marcas de Focusrite Audio Engineering Ltd. Proyecto desarrollado usando Claude (Anthropic).</span><span class="en">CIRCUIT-HACKS is not affiliated with Novation. Circuit Tracks, Components and Novation are trademarks of Focusrite Audio Engineering Ltd. Developed using Claude (Anthropic).</span></p>
</main>
<script>
"use strict";
const PATCHES = __PATCHES__;
const STOCK_SYX = "__STOCK_SYX__", STOCK_IMG = "__STOCK_IMG__";
const DESC = """ + json.dumps(DESC, ensure_ascii=False) + r""";
const NOV = [0xF0, 0x00, 0x20, 0x29, 0x00];
const $ = id => document.getElementById(id);
// ---------- the language: ?lang=, then the last choice, then the browser's
let LANG = (() => { const q = new URLSearchParams(location.search).get("lang"); if (q === "es" || q === "en") return q;
  try { const s = localStorage.getItem("ch-lang"); if (s === "es" || s === "en") return s; } catch (e) {}
  return /^es\b/i.test(navigator.language || "") ? "es" : "en"; })();
const t = (es, en) => LANG === "en" ? en : es;
const log = (m, cls) => { const d = document.createElement("div"); if (cls) d.className = cls;
  d.textContent = new Date().toLocaleTimeString() + "  " + m; $("log").appendChild(d); $("log").scrollTop = 1e9; };
// Text that goes into innerHTML is escaped: a file name like "<img onerror=…>.syx" must not run script on a page with SysEx access.
const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const hex = a => Array.from(a, b => b.toString(16).padStart(2, "0")).join(" ");
let midi = null, packets = null, stockImg = null, stockSyx = null, xfer = null, idPending = null;

// ---------- the versions ("Oficial" = the official firmware, its value in either language)
const verLabel = v => v === "Oficial" ? t("Oficial — el firmware de Novation sin cambios (para volver atrás)", "Official — Novation’s firmware unchanged (to go back)")
  : (DESC[v] ? DESC[v][LANG === "en" ? 1 : 0] : v);
for (const v of [...Object.keys(PATCHES), "Oficial"]) { const o = document.createElement("option"); o.value = v; o.textContent = verLabel(v); $("ver").appendChild(o); }
let midiNote = null;                                       // the MIDI state shown, [es, en, class]
function setMidiState(es, en, cls) { midiNote = [es, en, cls]; $("midiState").textContent = t(es, en); $("midiState").className = cls; }
function setLang(l) {
  LANG = l; document.documentElement.lang = l; try { localStorage.setItem("ch-lang", l); } catch (e) {}
  for (const b of document.querySelectorAll(".lang button")) b.classList.toggle("on", b.dataset.lang === l);
  for (const o of $("ver").options) o.textContent = verLabel(o.value);
  if (midiNote) setMidiState(...midiNote);
  if (!stockImg) $("verInfo").textContent = t("Primero elige el firmware oficial.", "Pick the official firmware first.");
  fillPorts();
}
for (const b of document.querySelectorAll(".lang button")) b.onclick = () => setLang(b.dataset.lang);

// ---------- CRC-32/MPEG-2, 7-bit blocks
const CRC_T = (() => { const t = new Uint32Array(256); for (let i = 0; i < 256; i++) { let c = i << 24;
  for (let k = 0; k < 8; k++) c = (c & 0x80000000) ? ((c << 1) ^ 0x04C11DB7) : (c << 1); t[i] = c >>> 0; } return t; })();
function crc32mpeg(u8) { let c = 0xFFFFFFFF; for (const b of u8) c = ((c << 8) ^ CRC_T[((c >>> 24) ^ b) & 0xFF]) >>> 0; return c >>> 0; }
function nib(arr) { let v = 0; for (const b of arr) { if (b > 15) throw Error("nibble"); v = v * 16 + b; } return v; }
function nibbles(v, n) { const o = []; for (let i = n - 1; i >= 0; i--) o.push(Math.floor(v / 16 ** i) % 16); return o; }
function unpackBlock(p) { if (p.length !== 37) throw Error(t("bloque de longitud ", "block of length ") + p.length);
  let bits = 0n; for (const b of p) { if (b & 0x80) throw Error(t("byte no MIDI", "not a MIDI byte")); bits = (bits << 7n) | BigInt(b); }
  bits >>= 3n; const out = new Uint8Array(32); for (let i = 31; i >= 0; i--) { out[i] = Number(bits & 0xFFn); bits >>= 8n; } return out; }
function packBlock(b) { let bits = 0n; for (const x of b) bits = (bits << 8n) | BigInt(x); bits <<= 3n;
  const o = new Array(37); for (let i = 36; i >= 0; i--) { o[i] = Number(bits & 0x7Fn); bits >>= 7n; } return o; }
function splitSyx(u) { const msgs = []; for (let i = 0; i < u.length;) { const s = u.indexOf(0xF0, i); if (s < 0) break; const e = u.indexOf(0xF7, s); if (e < 0) throw Error(t("SysEx sin terminar", "unterminated SysEx"));
  const m = u.slice(s, e + 1); for (let k = 0; k < 5; k++) if (m[k] !== NOV[k]) throw Error(t("cabecera no Novation", "not a Novation header")); msgs.push(m); i = e + 1; } return msgs; }
function decodeSyx(buf) {
  const msgs = splitSyx(new Uint8Array(buf)), cmd = msgs.map(m => m[5]);
  if (cmd[0] !== 0x71 || cmd[1] !== 0x7C || cmd[cmd.length - 1] !== 0x73 || cmd.slice(2, -1).some(c => c !== 0x72)) throw Error(t("orden de mensajes inesperado", "unexpected message order"));
  const init = msgs[0].slice(6, -1); if (init[0] !== 0x01 || init[1] !== 0x64) throw Error(t("no es un firmware de Circuit Tracks", "not a Circuit Tracks firmware"));
  const hdr = msgs[1].slice(6, -1); const size = nib(hdr.slice(7, 15)), crc = nib(hdr.slice(15, 23));
  const blocks = [unpackBlock(msgs[msgs.length - 1].slice(6, -1))]; for (const m of msgs.slice(2, -1)) blocks.push(unpackBlock(m.slice(6, -1)));
  const img = new Uint8Array(blocks.length * 32); blocks.forEach((b, i) => img.set(b, i * 32));
  if (size > img.length || size > 0x70000) throw Error(t("tamaño inválido", "invalid size"));
  const im = img.slice(0, size); if (crc32mpeg(im) !== crc) throw Error(t("CRC no coincide", "CRC mismatch")); return { msgs, img: im };
}
function encodeSyx(img) {                               // = ct_fw.encode (protocol 0x572, product 0x64)
  const pad = new Uint8Array(Math.ceil(img.length / 32) * 32).fill(0xFF); pad.set(img);
  const msgs = [], H = NOV;
  msgs.push(Uint8Array.from([...H, 0x71, 0x01, 0x64, 0x00, 0x00, ...nibbles(0x572, 4), 0xF7]));
  msgs.push(Uint8Array.from([...H, 0x7C, 0x00, ...nibbles(0x572, 6), ...nibbles(img.length, 8), ...nibbles(crc32mpeg(img), 8), 0xF7]));
  for (let i = 32; i < pad.length; i += 32) msgs.push(Uint8Array.from([...H, 0x72, ...packBlock(pad.subarray(i, i + 32)), 0xF7]));
  msgs.push(Uint8Array.from([...H, 0x73, ...packBlock(pad.subarray(0, 32)), 0xF7]));
  return msgs;
}
function applyPatch(src, ops) {
  let n = 0; for (const o of ops) n += o[0] === 0 ? o[2] : atob(o[1]).length;
  const out = new Uint8Array(n); let p = 0;
  for (const o of ops) {
    if (o[0] === 0) { if (o[1] + o[2] > src.length) throw Error(t("parche fuera de rango", "patch out of range")); out.set(src.subarray(o[1], o[1] + o[2]), p); p += o[2]; }
    else { const s = atob(o[1]); for (let i = 0; i < s.length; i++) out[p++] = s.charCodeAt(i); }
  }
  return out;
}
async function sha256(buf) { const h = await crypto.subtle.digest("SHA-256", buf); return hex(new Uint8Array(h)).replace(/ /g, ""); }
function concat(msgs) { let n = 0; for (const m of msgs) n += m.length; const u = new Uint8Array(n); let p = 0; for (const m of msgs) { u.set(m, p); p += m.length; } return u; }

// ---------- the official file and the version
$("file").onchange = async () => {
  stockImg = stockSyx = null; packets = null; updateSend();
  const f = $("file").files[0]; if (!f) return;
  const buf = await f.arrayBuffer(); const h = await sha256(buf);
  let html = `${esc(f.name)} · ${buf.byteLength} bytes<br>SHA-256 ${h}<br>`;
  try {
    if (h === STOCK_SYX) { const d = decodeSyx(buf); stockImg = d.img; stockSyx = d.msgs; }
    else if (h === STOCK_IMG) { stockImg = new Uint8Array(buf); stockSyx = encodeSyx(stockImg); }
    else if (new Uint8Array(buf)[0] === 0xF0) { const d = decodeSyx(buf); if (await sha256(d.img) === STOCK_IMG) { stockImg = d.img; stockSyx = d.msgs; } }
    if (!stockImg) { $("fileInfo").innerHTML = html + `<span class="bad">${t("No es el firmware oficial Circuit Tracks 1.2.1 (build 4486). Descárgalo con el enlace de arriba.", "This is not the official Circuit Tracks 1.2.1 (build 4486) firmware. Download it with the link above.")}</span>`; return; }
    $("fileInfo").innerHTML = html + `<span class="ok">✔ ${t("firmware oficial Circuit Tracks 1.2.1 (build 4486), imagen", "official Circuit Tracks 1.2.1 (build 4486) firmware, image")} ${stockImg.length} bytes</span>`;
    log(t("Firmware oficial verificado", "Official firmware verified")); await prepare();
  } catch (e) { $("fileInfo").innerHTML = html + `<span class="bad">${t("Archivo inválido", "Invalid file")}: ${esc(e.message)}</span>`; }
};
$("ver").onchange = () => { updateAck(true); prepare(); updateSend(); };
async function prepare() {
  packets = null; updateSend(); if (!stockImg) { $("verInfo").textContent = t("Primero elige el firmware oficial.", "Pick the official firmware first."); return; }
  const v = $("ver").value;
  try {
    if (v === "Oficial") { packets = stockSyx; $("verInfo").innerHTML = `<span class="ok">✔ ${t("firmware oficial sin cambios", "official firmware unchanged")} · ${packets.length} ${t("mensajes", "messages")}</span>`; updateSend(); return; }
    const P = PATCHES[v]; const img = applyPatch(stockImg, P.ops);
    const hi = await sha256(img); if (hi !== P.image_sha256) throw Error(t("la imagen parcheada no coincide con la publicada (", "the patched image does not match the published one (") + hi.slice(0, 16) + "…)");
    const msgs = encodeSyx(img); const hs = await sha256(concat(msgs)); if (hs !== P.syx_sha256) throw Error(t("el .syx no coincide con el publicado (", "the .syx does not match the published one (") + hs.slice(0, 16) + "…)");
    packets = msgs;
    $("verInfo").innerHTML = `<span class="ok">✔ ${v}: ${t("imagen", "image")} ${img.length} bytes, SHA-256 ${hs} ${t("idéntico al publicado", "identical to the published one")} · ${msgs.length} ${t("mensajes", "messages")}</span>`;
    log(`${v} ${t("preparado y verificado", "prepared and verified")} (${hs.slice(0, 16)}…)`, "ok");
  } catch (e) { $("verInfo").innerHTML = `<span class="bad">${esc(e.message)}</span>`; }
  updateSend();
}
$("verInfo").textContent = t("Primero elige el firmware oficial.", "Pick the official firmware first.");

// ---------- MIDI (as tools/ct_uploader.html)
function closePort(p) {
  if (!p) return;
  try { if (p.type === "input") p.onmidimessage = null; } catch (e) {}
  if (p.state === "disconnected") return;
  try { if (p.type === "output" && p.clear) p.clear(); } catch (e) {}
  try { if (p.connection !== "closed") Promise.resolve(p.close()).catch(() => {}); } catch (e) {}
}
function openPorts(inp, out, ms = 6000) {
  return Promise.race([Promise.all([inp.open(), out.open()]),
    new Promise((_, rej) => setTimeout(() => rej(new Error(t("el puerto no responde (¿se está reiniciando el aparato?)", "the port does not respond (is the device restarting?)"))), ms))]);
}
function dropMidi(es, en) { releaseAll(); midi = null; for (const id of ["outSel", "inSel"]) $(id).innerHTML = "";
  $("btnId").disabled = true; setMidiState(es, en, "warn"); $("btnMidi").disabled = false; updateSend(); }
function releaseAll() {
  if (idPending) { clearTimeout(idPending.t); idPending.inp.removeEventListener("midimessage", idPending.h); idPending = null; }
  if (xfer) { clearTimeout(xfer.timer); xfer.inp.removeEventListener("midimessage", onMsg); xfer = null; }
  if (!midi) return; midi.onstatechange = null;
  for (const p of midi.inputs.values()) closePort(p); for (const p of midi.outputs.values()) closePort(p);
}
window.addEventListener("pagehide", () => { try { releaseAll(); } catch (e) {} midi = null; });
window.addEventListener("beforeunload", e => { if (xfer) { e.preventDefault(); e.returnValue = ""; return; } releaseAll(); });
$("btnMidi").onclick = async () => {
  if (midi) releaseAll();
  try { midi = await navigator.requestMIDIAccess({ sysex: true }); }
  catch (e) { setMidiState("acceso denegado: " + e.message, "access denied: " + e.message, "bad"); return; }
  setMidiState("acceso concedido", "access granted", "ok");
  midi.onstatechange = onState; fillPorts(); $("btnId").disabled = false; updateSend();
};
let portsTimer = null;
function onState(ev) {
  const p = ev.port; log(`MIDI: ${p.type} «${p.name}» ${p.state} / ${p.connection}`);
  if (p.state === "disconnected") {
    if (xfer && (p === xfer.out || p === xfer.inp)) { finish(t("el puerto del Circuit Tracks ha desaparecido (¿se ha reiniciado o desconectado?)", "the Circuit Tracks port has gone (restarted or disconnected?)"), "warn"); dropMidi("el aparato se está reiniciando: espera a que arranque y pulsa «Permitir acceso MIDI»", "the device is restarting: wait until it starts and press “Allow MIDI access”"); return; }
    if (idPending && (p === idPending.out || p === idPending.inp)) idDone(t("dispositivo desconectado", "device disconnected"), "bad");
    closePort(p);
    if (/circuit tracks/i.test(p.name || "")) { dropMidi("el Circuit Tracks se ha desconectado o reiniciado: cuando esté listo, pulsa «Permitir acceso MIDI»", "the Circuit Tracks was disconnected or restarted: when it is ready, press “Allow MIDI access”"); return; }
  }
  clearTimeout(portsTimer); portsTimer = setTimeout(() => { if (midi) fillPorts(); }, 400);
}
function score(name) { if (!/circuit tracks/i.test(name)) return -1; if (/midi ?[23]|midiin2|midiout2|midiin3|midiout3|din|daw/i.test(name)) return 0; return 2; }
function fillPorts() {
  if (!midi) return;
  for (const [sel, map] of [[$("outSel"), midi.outputs], [$("inSel"), midi.inputs]]) {
    const prev = sel.value; sel.innerHTML = "";
    const ports = [...map.values()].sort((a, b) => score(b.name) - score(a.name));
    for (const p of ports) { const o = document.createElement("option"); o.value = p.id; o.textContent = p.name + (score(p.name) === 2 ? t("  ← recomendado", "  ← recommended") : ""); sel.appendChild(o); }
    if ([...sel.options].some(o => o.value === prev)) sel.value = prev;
  }
  updateSend();
}
const outPort = () => midi && midi.outputs.get($("outSel").value);
const inPort = () => midi && midi.inputs.get($("inSel").value);
function idDone(msg, cls) { if (!idPending) return; const { t, inp, out, h } = idPending; idPending = null;
  clearTimeout(t); inp.removeEventListener("midimessage", h); closePort(inp); closePort(out); if (msg) { $("idState").textContent = msg; $("idState").className = cls; } }
$("btnId").onclick = () => {
  const out = outPort(), inp = inPort(); if (!out || !inp || idPending || xfer) return;
  $("idState").textContent = t("esperando respuesta…", "waiting for an answer…"); $("idState").className = "";
  function h(ev) { const d = ev.data;
    if (d.length === 17 && d[0] === 0xF0 && d[1] === 0x7E && d[3] === 0x06 && d[4] === 0x02) {
      const mode = d[9] === 1 ? "firmware" : d[9] === 17 ? "bootloader" : t("modo ", "mode ") + d[9]; const build = d[14] * 128 + d[15];
      idDone(`Circuit Tracks · ${mode} · build ${build}`, "ok"); } }
  idPending = { inp, out, h, t: setTimeout(() => idDone(t("sin respuesta", "no answer"), "bad"), 2000) };
  inp.addEventListener("midimessage", h);
  openPorts(inp, out).then(() => { if (idPending && idPending.h === h) out.send([0xF0, 0x7E, 0x7F, 0x06, 0x01, 0xF7]); }).catch(e => idDone(t("no se pudo abrir el puerto: ", "could not open the port: ") + e.message, "bad"));
};
// ---------- the versions that write to the SD card (every one but the safer "…S" builds and the official firmware) ask for a tick first
const needsAck = v => v !== "Oficial" && !/S$/.test(v);
function updateAck(reset) { const need = needsAck($("ver").value); $("ackRow").style.display = need ? "flex" : "none"; if (reset || !need) $("ack").checked = false; }
$("ack").onchange = () => updateSend();
function updateSend() { updateAck(false); $("ack").disabled = !!xfer;
  $("btnSend").disabled = !(packets && outPort() && inPort() && !xfer && !idPending && (!needsAck($("ver").value) || $("ack").checked)); }

// ---------- transfer (pull protocol, as Components does)
const STATUS = { 0: ["inicio de actualización", "update started"], 1: ["esperando confirmación: PULSA PLAY en el Circuit Tracks", "waiting for confirmation: PRESS PLAY on the Circuit Tracks"],
  16: ["cancelado en el dispositivo", "cancelled on the device"], 17: ["se agotó el tiempo de confirmación", "the confirmation timed out"], 124: ["FALLO (composición no viable)", "FAILED (composition not viable)"],
  125: ["recibido (composición no viable)", "received (composition not viable)"], 126: ["FALLO (CRC)", "FAILED (CRC)"], 127: ["ÉXITO", "SUCCESS"] };
$("btnSend").onclick = () => {
  const name = $("outSel").selectedOptions[0].textContent;
  if (!confirm(t(`Se enviará ${$("ver").value} al puerto: ${name}\n\n¿Has hecho la copia de seguridad de la SD? No desconectes el Circuit Tracks hasta que termine. ¿Continuar?`,
    `${$("ver").value === "Oficial" ? "The official firmware" : $("ver").value} will be sent to the port: ${name}\n\nHave you backed up the SD card? Do not disconnect the Circuit Tracks until it ends. Continue?`))) return;
  start();
};
$("btnAbort").onclick = () => finish(t("cancelado por el usuario (el dispositivo descartará la actualización incompleta)", "cancelled by the user (the device will discard the incomplete update)"), "warn");
function start() {
  const out = outPort(), inp = inPort(); if (!out || !inp || xfer) return;
  if (idPending) idDone("", "");
  xfer = { out, inp, next: 0, last: -1, timer: null };
  $("btnSend").disabled = true; $("btnAbort").disabled = false; $("file").disabled = $("ver").disabled = true;
  inp.addEventListener("midimessage", onMsg);
  const me = xfer;
  openPorts(inp, out).then(() => { if (xfer !== me) return;
    log(`${t("Inicio", "Start")}: ${packets.length} ${t("mensajes", "messages")} → ${out.name}`); sendNext(); if (packets[xfer.next] && packets[xfer.next][5] === 0x7C) sendNext(); arm(25000);
  }).catch(e => finish(t("no se pudo abrir el puerto: ", "could not open the port: ") + e.message, "bad"));
}
function arm(ms) { clearTimeout(xfer.timer); xfer.timer = setTimeout(() => finish(t("tiempo de espera agotado; no se envió nada más", "timed out; nothing more was sent"), "bad"), ms); }
function sendNext() {
  const p = packets[xfer.next++]; xfer.out.send(p);
  $("prog").value = Math.round(100 * xfer.next / packets.length);
  if (xfer.next === packets.length) { $("phase").textContent = t("Transferido; esperando el informe del dispositivo…", "Transferred; waiting for the device’s report…"); arm(30000); }
}
function onMsg(ev) {
  const d = ev.data; if (!xfer || d[0] !== 0xF0) return;
  for (let k = 0; k < 5; k++) if (d[k] !== NOV[k]) return;
  if (d[5] === 0x72) {
    let n = null;
    if (d.length === 10) n = d[6] + (d[7] << 7) + (d[8] << 14);
    else if (d.length === 15) { const s = d.slice(6, 14); n = s[7] + (s[6] << 4) + (s[5] << 8); }
    if (n === null) return;
    if ((n > xfer.last || n === 0) && xfer.next < packets.length) { xfer.last = n; $("phase").textContent = t("Transfiriendo…", "Transferring…"); sendNext(); if (xfer.next < packets.length) arm(10000); }
  } else if (d[5] === 0x73 && d.length === 10) {
    const c = d[6]; log(`← ${t("estado", "status")} ${c}: ${STATUS[c] ? t(...STATUS[c]) : "?"}`, c === 127 ? "ok" : (c >= 124 || c === 16 || c === 17) ? "bad" : "");
    if (c === 1) { $("phase").textContent = t("PULSA PLAY en el Circuit Tracks para confirmar", "PRESS PLAY on the Circuit Tracks to confirm"); arm(25000); }
    else if (c === 0) arm(25000);
    else if (c === 127) { finish(t("Actualización recibida correctamente. El Circuit Tracks se reiniciará e instalará el firmware: espera a que arranque.", "Update received correctly. The Circuit Tracks restarts and installs the firmware: wait until it starts."), "ok"); dropMidi("el aparato se reinicia: cuando haya arrancado, pulsa «Permitir acceso MIDI»", "the device restarts: once it has started, press “Allow MIDI access”"); }
    else if (c === 125) arm(30000);
    else if (c === 16 || c === 17 || c === 124 || c === 126) finish(t("El dispositivo rechazó la actualización; el firmware actual no se modifica.", "The device refused the update; the current firmware is left unchanged."), "bad");
  }
}
function finish(msg, cls) {
  if (!xfer) return; const { inp, out } = xfer;
  clearTimeout(xfer.timer); inp.removeEventListener("midimessage", onMsg); xfer = null; closePort(inp); closePort(out);
  $("phase").textContent = msg; $("phase").className = cls; log(msg, cls);
  $("btnAbort").disabled = true; $("file").disabled = $("ver").disabled = false; updateSend();
}
$("outSel").onchange = $("inSel").onchange = updateSend;
setMidiState("sin acceso", "no access", "warn");
if (!navigator.requestMIDIAccess) setMidiState("este navegador no soporta Web MIDI: usa Chrome o Edge", "this browser does not support Web MIDI: use Chrome or Edge", "bad");
setLang(LANG); updateSend();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main(sys.argv[1:] or ["R209", "R209S", "B3.22", "R208", "R208S", "R206", "R206S", "R205", "R205S", "R204", "R204S", "R202", "R202S", "R201", "R201S", "RC2", "RC2S", "RC0.9", "RC0.9S"])
