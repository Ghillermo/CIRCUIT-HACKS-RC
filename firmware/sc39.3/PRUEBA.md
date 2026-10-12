# SC39.3 — editor de los destinos de los macro knobs del sinte

`circuittracks-4486-SC39.3.syx` — SHA-256 `373bcdf89013ac246192f06351e1e7945ecbfa45fbc83c211112c5d414404326`
Imagen de 0x67978 bytes, CRC 0xf7eeeddc, marca `SC39.3`.

Es SC39.2 con una función nueva (solo ARM): **los destinos de los 8 macro knobs de Synth 1 / 2 se editan desde el aparato**, en la vista de la fuente del sinte. Cada macro tiene 4 ranuras (A-D); cada ranura tiene destino, inicio, fin y profundidad. Los cambios se escriben en el patch en uso (los mismos parámetros que cambian Components o un controlador externo por NRPN) y **se guardan con el proyecto**, como cualquier otro cambio del patch.

## Manejo
1. **Vista de la fuente:** con la vista de pista de Synth 1 (o 2) en pantalla, pulsa su botón otra vez. El **pad 32** está en verde azulado tenue.
2. **Pad 32** = editor encendido (brillante). Los 8 knobs se iluminan tenues: ya no mueven los macros.
3. **Gira un knob** = eliges su macro (LED blanco). Ese primer giro no cambia nada. Los pads dibujan un número.
4. El knob elegido cambia el campo actual; **Octave ▼** pasa al campo siguiente, **Octave ▲** al anterior (los LEDs de Octave indican si hay más):

| Campo | Valor | Color del número |
|---|---|---|
| 1. Ranura | 1-4 (= A-D) | amarillo |
| 2. Inicio | 0-127: posición del knob donde empieza a actuar | verde |
| 3. Fin | 0-127: posición donde termina | naranja |
| 4. Destino | su número de CC o de NRPN (ver abajo) | blanco = CC; NRPN: banco 0, 1, 2 en tres colores |
| 5. Profundidad | 0-63, sin signo | verde azulado = positiva, rojo = negativa, blanco tenue = 0 |

5. **Destino:** el knob recorre primero los 31 destinos que tienen CC, por número de CC ascendente (5, 20, 21, 22, 24 … 91, 93), y después los 39 que solo tienen NRPN, en el orden de los destinos (envolventes 2 y 3, LFO, chorus, profundidades de la matriz). Sin vuelta: los extremos paran. La tabla completa está en `docs/NOTAS.md` («destinos de los macro knobs»).
6. **Cualquier pad** = se suelta el macro elegido y vuelven los pads de la fuente (el editor sigue encendido; el pad 32 lo apaga). Otro knob = su macro, ranura 1.
7. **Cualquier botón de vista** cierra la vista y apaga el editor.

## Qué probar
1. Lo de arriba, paso a paso, en Synth 1 y en Synth 2. Con el editor apagado los knobs mueven los macros como siempre.
2. Elige un macro, ranura 1, destino **74** (corte del filtro), inicio 0, fin 127, profundidad al máximo positivo. Sal del editor y gira ese knob: debe abrir el filtro.
3. Cambia el destino a **71** (resonancia): el mismo knob ahora mueve la resonancia.
4. Estrecha el rango (inicio 40, fin 80): el knob solo actúa entre esas posiciones.
5. Profundidad negativa (rojo): el knob actúa al revés.
6. Guarda el proyecto, apaga, enciende, carga: los destinos editados siguen.
7. **Destinos por confirmar** (deducidos, no leídos de una tabla): LFO 2 rate (NRPN 0:85), LFO 2 rate sync (0:86), LFO 2 slew (0:81), nivel de distorsión (CC 91), nivel de chorus (CC 93). Pon cada uno en un macro y di si el knob mueve lo que dice.
8. Los colores de los tres bancos NRPN y del pad 32: di si se distinguen bien.
9. **Velocidad de los knobs en el editor:** la ranura avanza un paso cada 16 eventos del knob y el destino cada 2. Di si la ranura o el destino van demasiado rápidos o lentos (son dos constantes).
10. Todo lo de `firmware/sc39.2/PRUEBA.md`.

## Verificación en emulación
- `emu_sc39_3.py` (por las rutas reales: botones, pads y knobs del controlador, la tarea de LEDs y el fotograma del panel): entrada por la vista de la fuente, pad 32, elegir macro sin cambiar nada, ranuras 1-4 sin vuelta (un paso cada 16 eventos del knob), el destino cada 2, campos con Octave y sus LEDs, cada campo escribe solo su parámetro (limitado a 0-127), el recorrido entero de los destinos arriba y abajo con su número y color, la profundidad por signo, soltar con un pad, apagar, cierre con un botón de vista, Synth 2 con su propio patch, SC39.2 sin cambios.
- Regresión sobre SC39.3: `emu_sc39_1.py`, `emu_sc39_1_gr.py`, `emu_sc39.py`, `emu_sc38_9.py`, `emu_sc39_1_reg.py`.
- **Sin comprobar en emulación:** que el sonido siga al destino (el motor del sinte no se emula), los colores reales y el guardado en la tarjeta (se usa la escritura de parámetros de stock, la misma del MIDI).
