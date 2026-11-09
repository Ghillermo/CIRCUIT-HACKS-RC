# RC4.11S = RC4.10S + arreglo: cargar un patch propio sin una docena de lecturas de la tarjeta

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/r411s/circuittracks-4486-R411S.syx` | `85a8aa61ac25092ea2b7153b15dbb072133e5e80349000a0ca06fab50b9e14a1` | `R411S` |

**El fallo** (el usuario, 2026-11-09, con S555D / S555D2: «play violet sometimes when loading new patches», «custom engine patches, not Nova»,
Play **blanco** = el tick del secuenciador llegó tarde mientras el mod leía la tarjeta): cargar un patch propio de MIDI 1 / 2 leía la tarjeta una
vez por cada parte del patch (el patch, la matriz, la página 4, los knobs no secuenciables, el FM, el registro del FM de 8 operadores, el estéreo, el
modo de voz, la wavetable, el oscilador único…), todas seguidas dentro de la pulsación del pad. El reloj del secuenciador esperaba.

**El arreglo** (`tools/loadcache.py`): al cargar, el registro del hueco se lee una vez a RAM y las partes leen de ahí: de 7 lecturas a 1 (el relleno). Lo demás va a la
tarjeta como antes.

## Qué probar
Con el transporte en marcha, cargar patches propios del motor (también con FM) una y otra vez: el reloj ya no debería tambalearse. Cada patch
debe sonar igual que antes al cargarlo (FM, matriz, página 4, modo de voz, wavetable).

## Verificación en emulación
- `emu_loadcache.py` contra RC4.10S: de 7 lecturas a 1 (el relleno); el sonido tras la carga idéntico (la RAM propia, los códigos 1..34); después de la carga nada sale de la copia.
- `emu_projsyn.py` (el sinte propio del proyecto carga por el mismo camino, hueco virtual: no se toca).
