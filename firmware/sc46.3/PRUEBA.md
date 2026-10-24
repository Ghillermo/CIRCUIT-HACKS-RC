# SC46.3 / Beta 3.20 = SC46.2 + el arreglo de RC2.08 + el modo GM con K4 + Jankó + pantalla de acordes

`firmware/sc46.3/circuittracks-4486-SC46.3.syx` — SHA-256 `1ba755af8691304d87f2a487a0684a694ad68544546b2826730b14ad9475dbe2`, marca `SC46.3`.
`firmware/b3.20/circuittracks-4486-B3.20.syx` — SHA-256 `2428a24ceb1a452edf6183632a73bfe8f0c7578fc620b7bf85800558cb5fca08`, marca `B3.20` (**Beta 3.20**, el mismo código).

- **Teclado externo** (`tools/kbin.py`, el arreglo de RC2.08): las notas que entran por MIDI en el canal de MIDI 1 / 2 tocan su sinte propio (ver `firmware/r208/PRUEBA.md`).
- **Modo GM** (`gmdrum.use_v2()`; el usuario, 2026-10-24: «Cuando k4:off, la vista se cierra y vuelve el setup y el funcionamiento normal de drums»): K4 a la izquierda apaga el modo y cierra el número (vuelven los pads de Setup); con el modo apagado K5-K8 no hacen nada y sus luces son las de stock.
- **Jankó** (`tools/janko.py`; el usuario: «janko puede ser un caso especifico de scales (ajustado al root note de stock)», «shift+8 … en vista custom scale», «con janko, octave subiría medio tono»): en el editor de la escala propia (Shift + Scales), **Shift + pad 8** enciende / apaga la disposición isomórfica (pad 8 cian encendida, amarillo con Shift). Cada fila sube un semitono y cada columna un tono; el pad de abajo a la izquierda es la tónica de stock. **Octave = medio tono** (Shift + Octave sigue transponiendo el patrón). Las 12 notas están en la escala (todas se iluminan; random-mutate elige cualquiera de su octava). Se guarda con el proyecto (bloque de la escala propia, `B_ON = 2`).
- **Pantalla de acordes** (`tools/chords.py`; el usuario: «la vista de acordes sería solo en Note Expand … shift+pad8 activa/desactiva acordes», «se pierden al apagar. La interpretación grabada … queda almacenada en el pattern»): Note ampliada de Synth 1 / 2 y MIDI 1 / 2, **Shift + pad 8**. Fila 1 el tipo (Shift + pads 1-7 = segunda página), pads 9-12 la inversión, 13 voicing abierto, 14 la fundamental una octava abajo, 15 diatónico, 16 latch; filas 3-4 las fundamentales (las notas del teclado de la vista Note). Cada nota del acorde por la entrada de notas en vivo de la vista (suena, se graba, el arpegiador la coge).

## Qué probar
1. **Teclado externo:** como `firmware/r208/PRUEBA.md`.
2. **GM:** Setup, K4 a la derecha, K5 un poco (se ve el número), K4 a la izquierda: vuelven los pads de Setup; K5 ya no hace nada; los drums salen con 60 / 62 / 64 / 65.
3. **Jankó:** Shift + Scales, Shift + pad 8 (cian). Synth 1, Note: la fila de abajo = tónica, +2, +4…; la de encima +1 semitono. Note otra vez (ampliada): un acorde mayor tiene la misma forma en cualquier sitio. Octave ▲ / ▼: medio tono. Shift + Octave: transpone el patrón (de stock). Guardar, cargar otro proyecto y volver: sigue en Jankó. Shift + pad 8 en el editor otra vez: vuelve la escala de antes.
4. **Acordes:** Synth 1, Note dos veces, Shift + pad 8 (verde con Shift). Un pad de las filas 3-4 = acorde mayor mientras se mantiene. Probar tipos (y Shift + fila 1), inversiones (pads 9-12), 13-16. Con Record + Play se graba; con el arpegiador encendido se arpegia. Note (vista normal): los pads tocan notas sueltas. MIDI 1 / 2 en modo muestra: la ampliada sigue siendo el selector.
5. Lo de SC46.2 / Beta 3.19 sigue igual.

## Verificación en emulación
- `emu_sc46_3.py` frente a SC46.2: el modo GM con K4; Jankó (tablas, inversa y enlaces en pantalla, Octave = semitono con la octava de stock quieta, Shift + Octave de stock, la ampliada, el cuantizador, random-mutate, apagado = las tablas de stock); los acordes (Shift + pad 8 sin nota, mayor / m7 / 6 / inversión 1 y vuelta / la fundamental abajo / abierto / diatónico con el cuantizador / latch, la velocity del pad, las luces de las filas 1-2 con y sin Shift, la vista normal y apagado = la nota de stock). SC46.2: Shift + pad 8 = de stock en las dos vistas.
- `emu_kbin.py` (ver RC2.08).
- `emu_gmdrum.py` sobre SC46.3: un fallo por diseño (con el modo apagado K5-K8 ya no se iluminan). `emu_arp.py`, `emu_sc44.py`, `emu_sc44_2.py`: los fallos conocidos desde SC45 (orden por altura / pulsan el pad 27). `emu_cscale.py`, `emu_sc46_1.py`, `emu_projsyn.py`, `emu_fmeng.py`: bien.
- Zona libre: `kbin` 0x801321c..0x801331c, `janko` 0x801331c..0x80136cc, `chords` 0x80136cc..0x8013b68; imagen 0x6f6a8.
