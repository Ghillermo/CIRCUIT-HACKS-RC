# Beta 5.42 = Beta 5.41 (= SC55.6) + los destinos de los instrumentos FM y los patches de ejemplo

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.42/circuittracks-4486-B5.42.syx` | `c3110bf5b5e60bebf76eddd17018020f14b193028818d9c1345dd32476dd8cb2` | `B5.42` |

**Lo nuevo** (el usuario, 2026-11-10: «Build example patches based on traditional and popular synth patches. assign pertinent macro destinations
to new and existing patches»; elegido: el sinte propio de MIDI 1 / 2, los patches como ficheros para la tarjeta):
- **`tools/fm8dest.py`:** al cargar un instrumento del FM de 8 operadores desde la lista del pad 8, la página 4 (knobs secuenciables) y Shift + pad 4
  (no secuenciables) de la pista pasan a los destinos de su familia (`make_examples.FAM_DEST`: teclados, bajos, leads, pads, punteados, percusión,
  campanas, vientos). Los valores no cambian; Clear mantenido + Shift + knob sigue devolviendo el de fábrica.
- **Patches de ejemplo** (no son firmware): `docs/patches/` = 81 ficheros `.ctm` de `tools/make_examples.py` (33 sonidos clásicos y los 48
  instrumentos FM con sus destinos), lista en `docs/patches/LEEME.md`; se suben con la app de la tarjeta (Parches custom → Subir .ctm).

## Qué probar
1. Sube algunos patches de `docs/patches/` con la app de la tarjeta a huecos libres y cárgalos en la vista Preset de MIDI 1 / 2: cada uno debe
   sonar a lo que dice su nombre; en la página 4 y en Shift + pad 4, Shift + knob enseña sus destinos (los de la tabla de `LEEME.md`).
2. MIDI 1 en FM: pad 8 mantenido + un instrumento: la página 4 y Shift + pad 4 cambian a los destinos de su familia (Shift + knob los enseña).

## Verificación en emulación
- `emu_examples.py` (SC55.6): los 81 patches cargados con `c_mpload` y guardados otra vez con `c_mpsave`: cada bloque del fichero vuelve igual
  (motor y códigos 1..34, forma del LFO, destinos de las páginas 4 y 8, modo de voz, bloques de uno / dos osciladores, bloque FM, registro FM de 8
  operadores) y los códigos están en la RAM del motor: 678 comprobaciones.
- `emu_fm8dest.py` contra Beta 5.41: pad 10 (Bright EP), página 2 pad 9 (Grand Piano) y pad 32 (Long Bell) ponen
  los destinos de su familia en MIDI 1, MIDI 2 no cambia; la build anterior deja los de fábrica.
- `emu_inst2.py` y `emu_loadcache.py` (contra SC55.5) pasan en SC55.7.
