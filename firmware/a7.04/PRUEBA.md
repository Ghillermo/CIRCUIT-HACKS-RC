# Alpha 7.04 (marca `A7.04`) — pendiente de probar

= Alpha 7.03 + **overdub del sample capturado** (`sampler_dsp.use_overdub()`; el usuario: «Overdub in all cases (even if the sample is mangled)» → «1 with decay»).

- Grabar con el pad 32 ya no para el sample del pad 7: sigue sonando como esté (pitch, reverso, zona de loop, gate) con la longitud de la toma anterior.
- La toma nueva = la mezcla en vivo + 0,7 × el sample tal como suena. Un solo búfer: un loop que suena sobre lo que se graba repite sus ecos, cada vuelta × 0,7.
- El pad 7 mientras graba arranca la toma anterior (se graba encima).

## Probar
1. Captura un loop, ponlo en loop (Shift + pad 7) y graba con el pad 32: la toma nueva lleva el loop + lo que suene; el loop no se para.
2. Con pitch / reverso: se graba como suena; ecos que bajan, sin saturar.
3. Sin sample sonando: la captura como antes.

Prueba: `emu_overdub_dsp.py` (pasa).

## Arreglos pendientes (`tools/fixes704.py`)
- **Clear + escena** borra también el modo de cadena y las repeticiones de esa escena, y las listas de pattern mutate (`sclear2.py`).
- `patchain`: nada propio en la pila de la tarea de LEDs mientras corre la cadena (`use_lrram`); una escena solo se ve encadenada con su bit en el mapa de scrules (`use_ccmap`).
- `jumpseq`: firma más fuerte (0xA7 + destinos 0..8 + byte 363 = 0; el formato no cambia) (`use_sig2`).
- Sitio: `jsaflip` y algunos módulos pequeños al final de la imagen (`dspz.use_spill`).

Pruebas: `emu_sclear2.py`, `emu_ledstack.py`, `emu_jumpfix.py`, `emu_jumprnd.py`, `emu_pgroups.py`, `emu_scnclear.py`, `emu_capkeep.py`, `emu_paintguard.py`, `emu_patrev.py`, `emu_morph.py`, `emu_icache.py` (pasan).
