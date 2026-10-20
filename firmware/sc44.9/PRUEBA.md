# SC44.9 / Beta 3.6 = SC44.8 + destinos de la página 4 + foto de los valores en un paso

`firmware/sc44.9/circuittracks-4486-SC44.9.syx` — SHA-256 `6484d0f5559a024c7c46b582965713b6ed12f2d3b2a9e2ab365bc6a63bb58aa5`, marca `SC44.9`.
`firmware/b3.6/circuittracks-4486-B3.6.syx` — SHA-256 `6abb9ffae4fde8fc36622bd303a50f040eaed2bd6af2342d5b30d3b8c536c964`, marca `B3.6` (**Beta 3.6**, el mismo código).

El usuario (2026-10-19): «permite reasignar los destinos de la vista de secuenciables (mismo layout que mod matrix)», «guardados por parche» (elegido: Shift + knob = destino); «Add a shortcut to "record instance" into the sequencers. This fills the automation rails with all the parameters that differ from the init» (elegido: Record mantenido + paso, solo los valores cambiados, reasignar carriles).

**Página 4 del motor de MIDI 1 / 2 (los 8 carriles de automatización):**
- **Shift + K1..K8** = el destino de ese knob / carril: los 33 parámetros del motor, en el orden y con los colores de página de la matriz de modulación (4 clics por parámetro, con tope en los extremos). Con Shift, los LEDs de K1-K8 = el color de la página de cada destino.
- **Clear mantenido, luego Shift + knob** = el destino de fábrica (TUNE, Release, Env → nivel, Env → filtro, Filtro, Resonancia, Velocidad del LFO, Efecto). (Shift + Clear es el metrónomo / cuenta atrás: por eso Clear va antes.)
- El knob sin Shift mueve el destino nuevo; con Record + Play se graba en su carril y el patrón lo reproduce. Lo que el carril ya tenía grabado mueve ahora el destino nuevo.
- Clear + knob a la izquierda borra el carril de ese knob.
- Los destinos se guardan con los **patches del sinte propio** (vista Preset de MIDI 1 / 2: Clear + pad dos veces); cargar un patch sin ellos = los de fábrica. El intercambio y la copia entre packs de patches los llevan.

**Foto de los valores en un paso:**
- Vista de pista de MIDI 1 / 2 con el motor encendido: **Record mantenido + un pad de paso** (pads 1-16; con 1-16 / 17-32 en la segunda página, los pasos 17-32).
- Se escriben en ese paso (sus 6 micropasos) los parámetros que **no están en su valor inicial** (el de Clear + knob a la derecha), y solo esos.
- Un parámetro sin carril toma uno cuyo parámetro sí está en el inicial (en orden de carril); ese carril se borra antes en el patrón. Si no caben, los primeros en el orden de la matriz.
- El paso no cambia sus notas; al soltar Record, la grabación queda como estaba antes de pulsarlo.

## Qué probar
1. MIDI 1 con el motor, página 4 (pad 4): Shift + K1 girando despacio: el LED cambia de color por páginas; suelta Shift y gira K1: se mueve el parámetro elegido (se oye).
2. Record + Play girando K1: se graba; al reproducir el patrón se mueve el parámetro nuevo.
3. Clear mantenido, luego Shift + K1: vuelve a TUNE.
4. Guarda el patch del sinte propio (Clear + pad dos veces en la vista Preset), cambia los destinos, carga el patch: vuelven.
5. Cambia FILT y la forma de onda (u otros) desde sus valores iniciales; vista de pista de MIDI 1, mantén Record y toca el pad 5: el paso 5 lleva esos valores (Play: al pasar por el paso 5 saltan a ellos); Record queda como estaba; las notas del paso 5 no cambian.
6. Lo de SC44.8 (LFO a tempo) sigue igual.

## Verificación en emulación
- `emu_p4dest.py`: filas iniciales = los carriles de fábrica; Shift + K1 lento (4 clics) por la lista de la matriz, tope en los extremos; LEDs con Shift; K1 mueve el destino nuevo y graba en el carril 0 (puerta de automatización id 20), el código viejo ya no graba; `c_vapply` del carril 0 mueve el nuevo; Clear + K1 a la izquierda borra el carril 0; Clear y Shift + K1 = TUNE; el patch guarda «P4» + los 8 códigos + suma en el relleno + 88 y los devuelve (sin ellos = de fábrica; un código que no es destino = el suyo de fábrica); psave / xpatch con 100 B. **Foto:** con todo en el inicial no escribe nada y Record vuelve a como estaba; con FILT / RES y dos parámetros sin carril cambiados: los dos sin carril toman los carriles 0 / 1 (borrados antes), cada valor en los 6 micropasos del paso 4, el carril 2 intacto, las notas del paso intactas; en la página 17-32 el pad 3 = paso 19; sin Record los pads van al stock.
- `emu_sc44_2.py`, `emu_lfosync.py`, `emu_sc43_8.py`: igual que SC44.8. `emu_sc42_6.py`, `emu_sc42_4.py`, `emu_sc43_6.py`: los mismos fallos que sobre SC44.8 (diseños anteriores).
