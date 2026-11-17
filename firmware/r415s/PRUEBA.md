# RC4.15S = RC4.14S + el arreglo de la ranura 7 de la vista Note de drums + los recortes de SC49 / SC49.3 (RC4.15S: nada propio escribe en la tarjeta)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/r415s/circuittracks-4486-R415S.syx` | `cf487e5654fe1475bc0eeee76ed4f46473d676bf4e08aa75d55d718eac5121c1` | `R415S` |

`tools/fixes564.rc()`: `rollers.use_vtguard()` + `drumnote.use_vtguard()` (la ranura 7 de la vista Note de drums no toca nada con un objeto ajeno: el
cuelgue de la Beta 5.63, que en una RC haría lo mismo si una palabra de la barra de velocity cambiara) y el código inalcanzable que las RC no habían
recortado (`packio.use_trimx`, `drums18.use_trim`, `vcf21.use_trimed`, `playmode.use_trimnu`, `build_sc15.use_trim`; `fullwalk` sobre RC4.14 los da
inalcanzables; ≈ 2 KB de flash; nada cambia en el uso). Detalle en `docs/NOTAS.md` («SC57.9 / Beta 5.64») y `docs/CHANGELOG.md`.

## Qué probar
1. Las vistas Note de los drums: los rollers (filas 1-3), los cuadros 25-28 copiando los 29-32, los pads de los drums 29-32.
2. Lo que tocaban los recortes (no debe cambiar nada): la vista Preset de drums con Duplicate entre packs (samples y patches) y Clear + pack en la
   vista de packs; los knobs de drums (K1-K8, con y sin Shift) y sus LEDs; el editor de CC de los macros MIDI (pad 25 de la Preset de MIDI 1 / 2:
   Octave cicla los campos, guardar / descartar); el Nudge de Pattern Settings (pad 26: el tramo un paso atrás, Shift adelante); la entrada de
   línea del Setup y el teclado partido de Synth 1 + Synth 2.
3. Lo de RC4.14 (`firmware/r414/PRUEBA.md`), si no se probó.

## Verificación en emulación
`emu_vtguard.py`, `emu_arptime.py --ext`, `emu_capkeep.py`, `emu_nudge2.py`, `emu_fsel.py`, `emu_edscratch.py`, `emu_rodisk.py` sobre esta imagen;
`verify_builds.py` → ALL IDENTICAL.
