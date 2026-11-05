# Beta 5.21 = SC51.8 con la marca de la beta (incluye las 5.17-5.20)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.21/circuittracks-4486-B5.21.syx` | `0329fde6cd823ecf7db681f2750df5822c9fa5dccbc9e2ce43609083fef0e43f` | `B5.21` |

**Qué cambia** respecto a la 5.20 (el usuario, 2026-11-05, probando la 5.20):
- **Pad 8 mantenido** = **24 instrumentos** en los pads 9-32, en el color de su tipo (teclados naranja, bajos azul, leads / metales rojo, pads / cuerdas verde, punteados amarillo, percusión blanco, campanas / efectos violeta); ya no los 16 sonidos de partida (casi todos campanas).
- **Pad 7 mantenido** = los **56 algoritmos** en los pads 9-32, en tres páginas con **Octave ▼ / ▲** (página 1: los 16 de 4 operadores verde azulado + los 8 nuevos de 8 operadores ámbar; página 2: los del DX7 1-24 blanco; página 3: los del DX7 25-32).
- **8 algoritmos de 8 operadores** (49-56): hasta ahora ningún algoritmo usaba los operadores 7-8.
- Las listas del pad 7 / 8 se ven y funcionan también con la fila de motores abierta o un modo flip (antes los pads 9-16 salían apagados).
- En la página FM, **pads 18-24 apagados** y sin cargar patches; **pad 28** (dos osciladores) y la página **OSC 2 (pad 3)** apagados y sin efecto con FM.
- **Fila de motores** (pad 27): sin voz, solo VCA / VCF / FX, oscilador, VA-drum, wavetable (apagado: aún no existe), muestra, granular, FM. **El secuenciador de efectos pasa al pad 31** con «sin voz» (azul tenue; un toque = encendido, brillante).
- **Pad 32** (modos de voz) y Shift + pad 29 solo con oscilador, FM, VA-drum o muestra (apagados con sin voz, VCA / VCF / FX, granular o el secuenciador de efectos).
- **Patches propios en el color de su motor** (FM violeta, oscilador verde…), brillante = el último cargado; **vacíos en blanco tenue** (antes violeta, el color del FM).

**Usar con una copia de la tarjeta.**

## Qué probar
1. MIDI 1, Preset, **pad 27**: la fila nueva (pad 21 apagado; tocarlo no hace nada). Pad 24 = FM.
2. Con la fila **abierta**, mantén **pad 8**: 24 pads de colores (9-32); toca varios: cada uno suena distinto. Lo mismo con la fila cerrada.
3. Mantén **pad 7**: página 1; **Octave ▼** = página 2 (blanco, el actual brillante), otra vez = página 3; Octave encendido solo si hay otra página. Elige un algoritmo de 8 operadores (página 1, pads 25-32): en la página FM se encienden los pads 9-16.
4. Página FM (fila cerrada): pads 18-24 apagados, tocarlos no carga nada; pad 28 y pad 3 apagados.
5. Pad 32 con FM: encendido. Elige «solo VCA / VCF / FX» (pad 18 de la fila): pad 32 apagado. Elige «sin voz» (pad 17): **pad 31 azul tenue**; tócalo = secuenciador de efectos (brillante, la fila marca «sin voz»); otra vez = apagado.
6. Lista de patches (pads 9-24): cada patch guardado en el color de su motor; los vacíos blanco tenue; el último cargado brillante.
7. Todo lo de la 5.20 sigue (guardado del FM, proyecto, Components).

## Verificación en emulación
`emu_fm8v2.py` (fila, pad 31, listas del pad 7 / 8 con la fila abierta, páginas con Octave, página FM, pad 28 / 3 / 32, colores de los huecos), `emu_fm8.py`, `emu_fm8poly.py`, `emu_fm8store.py`, `emu_fm8_core0.py`, `emu_fm8_core1.py`, `emu_fm8arm.py`, `emu_jumpflip.py`, `emu_vorder.py`, `emu_midipre.py`: ALL PASS. `emu_vmode.py` / `emu_unimode.py` / `emu_autorel.py` fallan igual que en SC51.7 (diseños anteriores); `emu_autorel.py` además por el orden nuevo de la fila.
