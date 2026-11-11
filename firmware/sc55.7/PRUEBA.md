# SC55.7 = SC55.6 + los destinos de los instrumentos FM y los patches de ejemplo

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc55.7/circuittracks-4486-SC55.7.syx` | `3ce4dd46fed84489becae318c09bc748fd52a00420c9549caed8b0020dd874df` | `SC55.7` |

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
- `emu_fm8dest.py` contra SC55.6: pad 10 (Bright EP), página 2 pad 9 (Grand Piano) y pad 32 (Long Bell) ponen
  los destinos de su familia en MIDI 1, MIDI 2 no cambia; la build anterior deja los de fábrica.
- `emu_inst2.py` y `emu_loadcache.py` (contra SC55.5) pasan en SC55.7.
