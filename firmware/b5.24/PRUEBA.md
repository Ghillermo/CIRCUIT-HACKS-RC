# Beta 5.24 = SC52.1 con la marca de la beta (incluye las 5.17-5.23)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.24/circuittracks-4486-B5.24.syx` | `a73f4ebed56dc50debe553870d5081e6c0ef0826ba75af3136d9dbaa50c4cd9d` | `B5.24` |

**Qué cambia** respecto a la 5.23 / SC52 (el usuario, 2026-11-05: «Select wavetables in engine mode. Knob layout on osc1 and osc2 views»): **motor wavetable en el pad 21 de la fila de motores** (arena). El oscilador lee una tabla de hasta 9 cuadros (los dos osciladores; FM / ring / sync, filtro, poly igual). **K7** de las páginas OSC 1 / OSC 2 = la posición de cada oscilador, K8 = LFO → posición, Shift + K8 = envolvente → posición, **SHAPE** (K2, K4 / K6) = warp. Con la wavetable sonando: **pad 7 mantenido** = las 16 wavetables del sinte de stock en los pads 9-24 (un toque llena la tabla con sus 9 cuadros); **pad 8 mantenido** = los samples del pack en los pads 9-32 (Octave = página; un toque añade / quita un ciclo del sample, extraído a su altura). Se guarda con los patches propios y con el proyecto. Además, **arreglo**: el intercambio de dos patches propios (Duplicate + A + B en la vista Preset de MIDI 1 / 2) estropeaba los bytes 128-141 del relleno (páginas de knobs no secuenciables, modo de voz) desde SC47.5.

**Usar con una copia de la tarjeta.**

## Qué probar
1. MIDI 1, pad 27 → pad 21: suena la wavetable (Nova «digital saw-square»); el pad 21 arena brillante, el 19 tenue. K7 (página OSC 1) barre los cuadros; K2 la dobla.
2. Pad 27 para cerrar la fila; mantén el pad 7: pads 9-24 = las 16 tablas; toca otras. Al cambiar, un momento de mezcla mientras se copian los cuadros.
3. Mantén el pad 8: los samples; toca uno (añade su ciclo al final; tarda un momento). Octave = página. Tócalo otra vez para quitarlo.
4. Dos osciladores (pad 28) con la tabla: K7 de OSC 2 = su posición.
5. Guarda el patch (Clear + pad dos veces), cárgalo; guarda el proyecto, apaga y carga: la tabla vuelve.
6. Notas agudas: sin aliasing (cada cuadro en 18 niveles de banda limitada).
7. Intercambia dos patches propios (Duplicate + A + B): sus páginas de knobs y modo de voz siguen bien.

## Verificación en emulación
`emu_wt_dsp.py` (lector del núcleo 0, tabla sintética; sin tabla igual bit a bit que SC52), `emu_wtcopy_core1.py` (copia y extracción de un ciclo en el núcleo 1), `emu_wtui.py` (panel, tick, patch), `emu_gentab_dsp.py --xtab`, `emu_fm8.py`, `emu_fm8v2.py`, `emu_fm8store.py`, `emu_fm8poly.py`, `emu_dx7imp.py`: ALL PASS. Sin probar en emulación: el guardado en el proyecto y la polifonía con wavetable.
