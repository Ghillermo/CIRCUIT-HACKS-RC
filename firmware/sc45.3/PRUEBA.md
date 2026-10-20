# SC45.3 / Beta 3.10 = SC45.2 + dos arreglos + orden pulsado y random-mutate en el arpegiador

`firmware/sc45.3/circuittracks-4486-SC45.3.syx` — SHA-256 `ac45fbaad9ddbabfd0924da65d22282a32f928d9a9f8148aced663cdcfd7e8e9`, marca `SC45.3`.
`firmware/b3.10/circuittracks-4486-B3.10.syx` — SHA-256 `0ebcf08b3450b6bf4c5acfae2c48e54776cf8f552a8127a06a2d82009b14e690`, marca `B3.10` (**Beta 3.10**, el mismo código).

**Arreglos (también en RC2.04 / RC2.04S):**
- **Notas largas al grabar** (`tools/recfix.py`; el usuario, 2026-10-20: «el arpegiador en compases de más de 16 pasos no recuerda qué notas estaban pulsadas después del 16 (hay que volver a poner las notas en el paso 17 para que siga arpegiando)», «extiende este fix a notas mantenidas durante la grabación aunque no fuera arpegio»). Causa: **el grabador de stock corta toda nota a 16 pasos** (`0x0803F85A`: 16 pasos o más → gate 96, el resto se pierde); un acorde mantenido 20 pasos quedaba de 16 y su arpegio se paraba ahí. Ahora la nota (o cada nota del acorde) queda ligada (bit 7 del gate) y la misma nota se escribe 16 pasos después, con su micropaso y su velocity y lo que queda (ligada otra vez si sigue), dentro del primer..último paso del patrón; en un patrón de 16 pasos o menos, como antes. Synth 1 / 2 y MIDI 1 / 2, con arpegiador o sin él.
- **Selector de samples del modo muestra** (`tools/smhold.py`; «en la pista sample flip del sampler propio, elegir sample+paso no programa el sample (elegir el paso primero y luego el sample sí lo hace)»): **mantener un sample y tocar pasos** = el flip de esos pasos (antes solo funcionaba paso mantenido + sample).

**Arpegiador (solo beta; el usuario, 2026-10-20):**
- **Orden pulsado** (`arp.use_pressord()`; «el orden de reproducción es el orden pulsado. Cuando una pulsación se retira, el slot de esa nota queda vacío, al volver a introducir una nota nueva, ocupa esa misma posición (y todas las posiciones vacías libres para notas sucesivas) antes de ir a una posición posterior»; un hueco vacío se salta; los órdenes recorren los huecos): las notas mantenidas ya no se ordenan por altura; cada una guarda su hueco y una nueva ocupa el primer hueco libre. Un acorde grabado, en el orden de sus notas en el paso (el de la grabación).
- **Random-mutate** (`arp.use_mutarp()`; «los modos mutates también afectan al arpegio si están activados»): el nivel de random-mutate del paso del acorde se aplica a cada nota de su arpegio (las mismas probabilidades que las notas normales; nada se escribe). El arpegio en vivo no tiene paso: no muta.

## Qué probar
1. **Notas largas:** Synth 1, patrón de 32 pasos, Record + Play: mantén una nota (o un acorde) desde el paso 1 hasta el 24 y suéltala. Al reproducir: suena seguida hasta el paso 24 (sin cortarse en el 17 ni volver a atacar). En la vista Note, el paso 17 lleva la misma nota.
2. Lo mismo con el arpegiador encendido (Shift + pad 25 en Pattern Settings): el acorde mantenido del paso 1 al 24 se arpegia hasta el 24 (antes: hasta el 16).
3. Un patrón de 16 pasos: igual que antes (la nota dura el patrón entero).
4. **Selector de samples** (MIDI 1 en modo muestra, Note dos veces): mantén un sample (filas 3-4) y toca los pasos 4 y 6: los dos en melocotón con ese sample. Paso mantenido + sample, y Clear + paso, siguen igual.
5. **Orden pulsado:** arpegiador encendido (orden arriba), mantén E, C, G (en ese orden): suena E C G. Suelta la C y pulsa A: E A G. Suelta E y A, pulsa D y F: D F G. Con abajo, al revés.
6. **Random-mutate:** graba un acorde arpegiado, pon nivel 7 de random-mutate en su paso (Shift + Pattern Settings / modo 2, fila 4): el arpegio cambia de notas en cada vuelta; nivel 0: siempre las del acorde.
7. Lo de SC45.2 / Beta 3.9 sigue igual.

## Verificación en emulación
- `emu_sc45_3.py`: lo de RC2.04 y además las listas (`c_arins` / `c_ardel` sobre el estado de la entrada: 64 60 67; soltar 60 y pulsar 72 → 64 72 67; 40 y 41 ocupan los dos huecos) y la secuencia (acorde en el orden de sus unidades: arriba 64 60 67, abajo 67 60 64; nivel 7 de random-mutate = otras notas, nivel 0 = las del acorde).
- `emu_arp.py` sobre SC45.3: las comprobaciones de la secuencia que esperan las notas ordenadas por altura ya no valen (orden pulsado).
