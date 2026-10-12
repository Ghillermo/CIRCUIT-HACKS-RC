# SC39.4 — guardar el patch del sinte en el banco; el mismo gesto para el sinte propio

`circuittracks-4486-SC39.4.syx` — SHA-256 `9626ab9a90b7268e285f52a192855bb65a98eec2e95a44a439613e88d03c1c1e`
Imagen de 0x67f28 bytes, CRC 0xbf64ea28, marca `SC39.4`.

Es SC39.3 con una función nueva (solo ARM) y un cambio de gestos:

- **Guardar el patch de Synth 1 / 2 en el pack.** El aparato original no puede (solo Components). Se guarda el patch tal como suena, con todos sus cambios (los hechos con los knobs, por MIDI y los destinos de macro de SC39.3).
- **El sinte propio de MIDI 1 / 2 usa el mismo gesto**, y Duplicate pasa a intercambiar posiciones.

**Escribe en la tarjeta SD.** Prueba primero en un pack de pruebas.

## Manejo
### Synth 1 / 2 — vista Preset (cualquiera de sus 4 páginas)
1. **Clear + pad** = pregunta: ese hueco parpadea en blanco. No se escribe nada.
2. **Clear + el mismo pad otra vez** (en menos de ~5 s) = el patch del sinte se escribe en ese hueco, sustituyendo lo que hubiera, y el hueco queda elegido.
3. Clear + otro pad mueve la pregunta a ese pad. Pasados ~5 s, o tocando un pad sin Clear, la pregunta se anula.
4. Un hueco más allá del final del banco también vale: los huecos intermedios quedan vacíos.
5. El nombre del patch guardado es el del patch que estaba cargado.

### MIDI 1 / 2 — vista Preset, filas 2-3 (patches del sinte propio)
| Gesto | Antes (BETA2 / BETA3) | Ahora |
|---|---|---|
| pad | cargar | cargar (igual) |
| Clear + pad | vaciar el hueco | **pregunta (parpadea en blanco); Clear + el mismo pad otra vez = guardar** |
| Duplicate + pad | guardar | — |
| Duplicate + pad A + pad B | — | **intercambiar los dos huecos** (A parpadea mientras se mantiene Duplicate) |

| **Clear + MIDI 1 / 2** (el botón de la pista, con una vista de esa pista en pantalla) | — | **todos los valores del motor de esa pista a los iniciales** (el motor elegido se queda) |

- **Los huecos vacíos se ven en violeta** (antes apagados); con patch, melocotón como antes.
- **Escucha:** al cargar un hueco con un toque suena la tónica de la escala en esa pista con el patch recién cargado, mientras mantienes el pad.
- Ya no hay gesto para vaciar un hueco: se sobrescribe, o se mueve con Duplicate a otro sitio (A sobre un hueco vacío B = A queda vacío).
- El intercambio necesita que A tenga un patch y que el hueco B exista en el banco de patches de sinte del pack (en un pack normal, con sus 64 primeros patches de sinte, siempre existe). Si no, no hace nada.
- Clear + pad de página (1-5) sigue reiniciando esa página.

## Qué probar
1. Synth 1, Preset: Clear + un hueco libre → parpadea blanco. Espera 6 s → deja de parpadear y no se ha guardado nada.
2. Cambia el sonido (knobs, o un destino de macro con el editor de SC39.3). Clear + hueco, Clear + el mismo hueco → el hueco queda elegido. Carga otro patch y vuelve a ese hueco: **suena como lo guardaste**.
3. Apaga, enciende, carga el pack: el patch sigue ahí. Mira el pack en Components si puedes: el patch aparece en ese hueco.
4. Guarda sobre un hueco ocupado: lo sustituye. Los patches vecinos no cambian.
5. Lo mismo en Synth 2 y en otra página de patches.
6. **El sinte propio no se pierde:** guarda un patch del sinte propio en el hueco N de MIDI 1 (Clear + pad dos veces) y después guarda un patch de sinte en el hueco N de Synth 1. El del sinte propio debe seguir en MIDI 1.
7. MIDI 1: Clear + hueco dos veces guarda; un toque carga; MIDI 2 carga el mismo hueco.
8. MIDI 1: Duplicate + A + B intercambia; sobre un hueco vacío, mueve.
9. MIDI 1: los huecos vacíos en violeta. Toca un hueco con patch y mantenlo: suena la tónica con ese patch; al soltar, calla. Un hueco vacío no suena. (La nota tarda un instante: antes se guarda el estado.)
10. MIDI 1: Clear + botón MIDI 1 → el sonido vuelve al inicial (todas las páginas). Clear + MIDI 2 con MIDI 1 en pantalla no hace nada. Con el editor de CC abierto tampoco.
11. Duplicate + A + B en la Preset de Synth 1 / 2 (copiar / intercambiar patches de sinte) y el borrado de packs: como antes.
12. Todo lo de `firmware/sc39.3/PRUEBA.md`.

## En el PC
`tools/patchtool.py` (la tarjeta en un lector; `E:/29_PACK` = la carpeta del pack):
- `python tools/patchtool.py list E:/29_PACK` — los 64 huecos del sinte propio con índice, nombre y motor.
- `python tools/patchtool.py copy E:/29_PACK:3 bajo.ctm` — baja el hueco 3 a un fichero; al revés lo sube; `PACK:A PACK:B` copia entre huecos o packs.
- `python tools/patchtool.py show bajo.ctm` — motor y parámetros; `set bajo.ctm filt=90 res=20 engine=granular` los cambia; `new`, `name`, `clear`.

Prueba: baja un patch, cambia un parámetro que se oiga (p. ej. `filt`), súbelo a otro hueco y cárgalo en el aparato. Nombra un hueco, intercámbialo en el aparato con Duplicate y comprueba con `list` que el nombre fue con él.

## Verificación en emulación
- `emu_sc39_4.py` (rutas reales: el botón Clear y los pads por el controlador, la tarea de LEDs, la API de contenido sobre el modelo de la SD):
  - sinte: pregunta sin escribir, parpadeo, la pregunta se mueve, una sola escritura de 340 B = el patch de la RAM en `512 × (patch % 8)` del banco `patch / 8`, relleno y demás registros intactos, el stock elige el hueco después, una edición por la ruta del MIDI entra en el guardado, caducidad a los ~5 s, hueco tras el final y banco inexistente (`0xFF` hasta el hueco), Clear + Duplicate nada, puntero de comprobación, Synth 2, SC39.3 sin cambios;
  - sinte propio: Duplicate + pad ya no escribe, Clear + pad pregunta y la segunda vez guarda, la pregunta de MIDI 1 no vale en MIDI 2, intercambio (dos escrituras de 64 B: el patch y el nombre que le da `tools/patchtool.py`; los patches de sinte intactos), mover a un hueco vacío, casos sin efecto, cargar y reiniciar página como antes, huecos vacíos en violeta, la escucha (nota de la tónica al cargar, fin al soltar o con cualquier botón, nada en un hueco vacío), Clear + botón de la pista (valores iniciales, todo marcado para reenviar; no con el botón de la otra pista ni con el editor de CC).
- Regresión sobre SC39.4: `emu_sc39_3.py`, `emu_sc39_1_gr.py`, `emu_sc39.py`, `emu_sc38_9.py`, `emu_sc39_1_reg.py`, `emu_sc35.py`. `emu_sc39_1.py` espera los gestos antiguos del sinte propio (Duplicate + pad guarda, Clear + pad vacía): sus comprobaciones de esos dos gestos fallan en SC39.4, a propósito.
- **Sin comprobar en emulación:** la escritura real en la tarjeta, que el stock cargue bien el hueco recién escrito, y que la dirección del patch en la RAM (`0x20010044`, Synth 2 344 B después) sea la misma en el aparato: está sacada del volcado de RAM del aparato y el código comprueba antes de escribir un puntero que el stock deja delante; si no coincide, no escribe nada.
