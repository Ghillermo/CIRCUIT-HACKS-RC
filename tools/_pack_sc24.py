"""One-off packaging of SC24."""
import json
from pathlib import Path
R = Path(__file__).resolve().parents[1]
m = json.loads((R / "firmware/sc24/manifest.json").read_text())
sha = m["syx_sha256"]; size = m["image_size"]
print(sha, size)


def rw(p, f):
    path = R / p
    s = path.read_text(encoding="utf-8")
    n = f(s)
    assert n != s, p
    path.write_text(n, encoding="utf-8", newline="")


def known(s):
    k = s.index('  "6c5b9973'); j = s.index("\n", k)
    return s[:j + 1] + f'  "{sha}": "4486 + SC24: SC23.6 + pad 27 de tres estados, paginas en los pads 1-8, segundo oscilador (mezcla, FM, ring, sync suave, bit a bit), orden de la cadena por pista y parafonia",\n' + s[j + 1:]


rw("tools/ct_uploader.html", known)
rw("tools/verify_builds.py", lambda s: s.replace('    ("sc23.6", "build_sc23_6.py", []),\n', '    ("sc23.6", "build_sc23_6.py", []),\n    ("sc24", "build_sc24.py", []),\n'))
for f in ("tools/emu_sc17.py", "tools/emu_sc17_8.py", "tools/emu_sc19.py", "tools/emu_sc20_1.py"):
    rw(f, lambda s: s.replace('"SC23.5", "SC23.6")', '"SC23.5", "SC23.6", "SC24")'))


def rt(s):
    s = s.replace("F236=firmware/sc23.6\n", "F236=firmware/sc23.6\nF24=firmware/sc24\n")
    k = 'run python3 tools/emu_sc23_6_dsp.py {B} "$F235/circuittracks-4486-SC23.5.bin"\n'.replace("{B}", '"$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"')
    B = '"$F24/circuittracks-4486-SC24.bin" "$F24/manifest.json"'
    add = (f'run python3 tools/emu_sc23_3_fx.py {B}\n'
           f'run python3 tools/emu_sc23_4_notes.py {B}\n'
           f'run python3 tools/emu_sc23_5_gfx.py {B}\n'
           f'run python3 tools/emu_sc23_5_drums.py {B}\n'
           f'run python3 tools/emu_sc23_5_ed.py "$IMG9" "$F24/circuittracks-4486-SC24.bin" "$MAN9" "$F24/manifest.json"\n'
           f'run python3 tools/emu_sc23_5_dsp.py {B}\n'
           f'run python3 tools/emu_sc23_6.py {B}\n'
           f'run python3 tools/emu_sc23_6_dsp.py {B} "$F236/circuittracks-4486-SC23.6.bin"\n'
           f'run python3 tools/emu_sc24.py {B}\n'
           f'run python3 tools/emu_sc24_dsp.py {B} "$F236/circuittracks-4486-SC23.6.bin" "$F236/manifest.json"\n')
    assert k in s, k
    return s.replace(k, k + add)


rw("tools/run_tests.sh", rt)
rw("README.md", lambda s: s[:s.index("| SC23.6 |")] + "| SC24 | SC23.6 + **modo VCA-VCF rediseñado**: pad 27 de tres estados (apagado / entrada de línea / oscilador), fila de páginas en los pads 1-8 (VCA-VCF, OSC1, OSC2), pad 28 = 1 o 2 osciladores, pad 29 = orden de la cadena (VCA → FX → filtro / filtro → VCA → FX); **segundo oscilador** con MIX, FM, Ring, Sync suave (inversión de fase cada N ciclos) y zonas bit a bit (xor, or, nor, and, nand); **parafonía** (una nota = unísono, dos = una por oscilador). Los valores nuevos son volátiles | ⏳ pendiente de probar |\n" + s[s.index("| SC23.6 |"):])


def rc(s):
    i = s.index("- **SC23.6** (`firmware/sc23.6/`")
    new = ("- **SC24** (`firmware/sc24/`, pendiente de probar) = SC23.6 + (opciones `vcf21.use_dualui()` + `vcf21_dsp.use_dual()`): **DSP** (`CODE7`: mailbox con código de 7 bits, códigos 32..39 → bloque OSC2 `X:OS2B0 = $3960 + 48 t`; `DUAL`: ACT = acto | ruta << 8 | dual << 9, el mailbox los separa (ACT 0..2 y `DFLAGS` = `X:OSB0 + 48 t + 21`), código 14 = NOTE2 (`+20`), BITSYNC = código 37 con zona + posición como los tipos; segundo oscilador por muestra en `channel` (OSC2 → FM a la fase de OSC1, sync suave: cada N-ésimo ciclo de OSC1 invierte el incremento de OSC2, mezcla, ring, bit a bit), el seguimiento de la nota usa la media de las dos notas; `ROUTE`: orden de la cadena por voz con dos tests de bandera, sin código duplicado), **ARM** (`DUALUI`: pad 27 tres estados `vp_tri`, fila de páginas `vp_row` (página en `RT_TAG` bits 1-2, `c_vpage` / `c_vsetpage`), pad 28 `vp_dual` (bit 7 de `RT_VEL`), pad 29 `vp_route` (bit 7 de `RT_NOTE`), tabla de knobs de 3 páginas (`KNOB_CODES_C`), valores nuevos volátiles en el bloque de Master FX (`V2_OFF = 180`, 8 B por pista, `c_vvaddr` mapea código → dirección; **el bloque crece 16 B: reserva 236 B, 4 B de margen**), barrido de los códigos 27..34 por el mailbox (`sd_sw`, un mensaje cada 2 ms por voz cuando no hay nada sucio; cursor en `RT_CNT` bits 4-6), notas parafónicas (`c_vnote_on / off`: n1 = `RT_NOTE`, n2 = el valor del código 14, cuenta en `RT_CNT` bits 0-3, bit 7 = quién es el más antiguo), LEDs por tipo para WAVE2 / BITSYNC (`c_vtype`)); firma `0xAF`. Pruebas `emu_sc24.py`, `emu_sc24_dsp.py`. Modulaciones de OSC2 = las de OSC1 (no hay RAM para otras); la RAM guardada está llena.\n")
    return s[:i] + new + s[i:]


rw("CLAUDE.md", rc)


def rn(s):
    i = s.index("### SC23.6 = SC23.5 + ")
    t = ("### SC24 = SC23.6 + **pad 27 de tres estados, páginas en los pads 1-8, segundo oscilador, interacciones, orden de la cadena y parafonía** — ⏳ pendiente de probar\n"
         "- Diseño acordado con el usuario en la conversación (2026-10-06 / 07): pad 27 por pista = apagado → entrada de línea con VCA-VCF (naranja) → oscilador con VCA-VCF (verde) → apagado; apagado = los knobs son los macros de stock; los pads 1-8 (primera fila de la vista Preset) = selector de página con el modo encendido (1 VCA-VCF, 2 OSC1, 3 OSC2 solo con dos osciladores), siempre empieza en VCA-VCF; mientras el editor de CC está abierto son las plantillas; pad 28 = 1 / 2 osciladores; pad 29 = orden VCA → FX → VCF / VCF → VCA → FX; OSC1 página: MIX + knob lento BITSYNC (nada, Sync, xor, or, nor, and, nand); OSC2 página: FM (OSC2 modula a OSC1) y Ring; Sync = OSC1 maestro, **sync suave con inversión de fase**, la posición elige cada cuántos ciclos (1..8); parafonía: una nota = unísono, dos = una por oscilador, la tercera sustituye a la más antigua; la envolvente se reinicia con cada nota, la velocidad es la de la última.\n"
         "- **Presupuesto de RAM (lo que decide el diseño).** Tail de ajustes (75 B): lleno (flags 1 + valores 52 + RT 16 + guardado 1 + firma 1 + editor 4). Reserva del heap: 220 B + 16 B nuevos = **236 B, margen 4 B** (el heap del aparato termina en `0x20044D68`, la reserva empieza en `0x20044D6C`; `c_gst` la rechaza si el heap actual la supera: Master FX, VCA-VCF y sidechain se apagarían a la vez). Bytes encontrados sin RAM nueva: bits libres (bit 7 de `RT_NOTE` / `RT_VEL` = ruta / dos osciladores; `RT_TAG` bits 1-2 = página; `RT_CNT` bits 4-7 = cursor del barrido + «el más antiguo»), el valor muerto de FXMOD (código 14) = la nota del segundo oscilador. Los 8 valores nuevos por pista (TUNE2, FINE2, WAVE2, PW2, MIX, BITSYNC, FM, RING) van al bloque de Master FX (16 B) y **no se guardan**; las 6 modulaciones de OSC2 serían 12 B más (no caben): **comparten las de OSC1**. Alternativas descartadas: llevar los valores en la memoria del DSP (hace falta una caché en el ARM y la lectura de vuelta desde la hebra de la interfaz no está comprobada), tomar prestado el búfer de LEDs de otra vista (riesgo de regresión de Master FX).\n"
         "- **Transporte.** El barrido (`sd_sw`): cuando no hay nada sucio ni ventana de latido, un mensaje cada 2 ms por voz con uno de los 8 valores nuevos (códigos de ARM 27..34 → mailbox 32..39), por turnos; sin bits sucios para ellos (RAM). Nota del segundo oscilador: el código 14 (la byte muerta de FXMOD) con su bit sucio de siempre. ACT: `act | ruta << 8 | dual << 9` (el DSP lo separa). El primer mensaje tras el arranque (etiqueta 0) lo ignora el DSP: el latido repite ACT (en las pruebas hay que pasar las ventanas del latido).\n"
         "- **DSP.** `CODE7`, `DUAL`, `ROUTE` (`vcf21_dsp.use_dual()`): el código del oscilador de `control` y `channel` se generó parametrizado por el bloque (`r3` = OSC1, `r4` = OSC2: las SC22.3-SC23.6 salen **idénticas**); lazo `dual` por muestra (`do` de 32 tramas): fase de OSC2 → ondas → muestra guardada; fase de OSC1 (detección de vuelta: nueva < vieja) → sync suave cada N vueltas (invierte el incremento con signo de OSC2 y la bandera de dirección) → FM (fase + 8 · FM · o2) → ondas de OSC1 → mezcla → ring → bit a bit (eor / or / and / not: zonas 2..6, la posición de la zona = el peso). Programa del DSP: termina en `P:$3DFE` (514 palabras libres de `$4000`); coste con dos osciladores en las dos pistas **+8,1k instrucciones por bloque** (≈ 4,9 % de las ~166k estimadas; con un oscilador +62); pila 6. Tabla del corte del filtro: 8 pasos por octava (seguimiento 1:1 = f ≈ 85).\n"
         "- **Pruebas.** `emu_sc24_dsp.py` (buzón, ruta bit a bit contra SC23.6, oscilador doble: el mismo sonido con MIX = 0, OSC2 solo, mezcla, ring, FM, bit a bit con dos osciladores iguales, sync contra un modelo de la fase del maestro, media del seguimiento, coste), `emu_sc24.py` (pad 27, 28 / 29, fila de páginas, knobs, barrido, Clear, notas parafónicas, y el recorrido completo ARM → DSP con 244 mensajes), y las de SC23.5 / SC23.6 sobre esta imagen (adaptadas con la marca `SC24`).\n"
         "- **Limitaciones conocidas:** valores nuevos volátiles; modulaciones compartidas; las notas sustituidas no vuelven al soltar; margen de RAM 4 B. Ideas aparcadas para conversar: **step-drummer** (los 8 knobs = 8 pares de pasos del secuenciador, página arriba = pitch, abajo = velocity; depende del formato de paso del secuenciador de stock, sin estudiar).\n"
         f"- Marca `SC24`, `firmware/sc24/` ({size} B), SHA-256 `{sha}`. Reserva SC23.6.\n\n")
    return s[:i] + t + s[i:]


rw("docs/NOTAS.md", rn)
