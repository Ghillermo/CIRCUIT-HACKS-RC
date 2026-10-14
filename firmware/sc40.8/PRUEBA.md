# SC40.8 — Nudge y órdenes de reproducción fractal / deconstruido

`circuittracks-4486-SC40.8.syx` — SHA-256 `42278e2644cdfede29754ce9c22116af790c1ba29f119a8d8e64903dcce76b5c`
Imagen de 0x69e58 bytes, CRC 0x92c32acb, marca `SC40.8`.

Es SC40.7 (ver `firmware/sc40.7/PRUEBA.md`) con tres pads más en la vista **Pattern Settings** de las pistas de notas (Synth 1 / 2, MIDI 1 / 2). En los drums esos pads siguen apagados (versión posterior).

| Pad | Color | Qué hace |
|---|---|---|
| 25 | (SC40.3) | fila 3 / 4 de la vista de probabilidad: dinámicas / random-mutate |
| **26** | naranja | **Nudge**: reescribe el patrón de modo que el primer paso elegido pasa a ser el paso 1 |
| **27** | como los pads de dirección | **fractal**: 1 · 1 2 · 1 2 3 · 1 2 3 4 · … hasta el último paso |
| **28** | como los pads de dirección | **deconstruido**: las diagonales 1 6 11 16 · 2 7 12 13 · 3 8 9 14 · 4 5 10 15 |
| 29-32 | stock | dirección de stock |

- **Nudge** rota los pasos completos (notas, probabilidad, frecuencia, dinámicas, mutación y los 12 carriles de automatización de los knobs). Rota 16 pasos si el patrón acaba en el paso 16 o antes y 32 si acaba después. El primer paso queda en 1 y el último se mueve con él (pasos 6-13 → 1-8). Lo que había delante del inicio queda al final.
- **Fractal / deconstruido** son exclusivos entre sí y con los pads 29-32: elegir uno apaga los otros, y un pad de dirección los apaga a ellos.
- **Deconstruido** con un patrón más corto que 16: los pasos de fuera se saltan (pasos 1-8: 1 6 2 7 3 8 4 5). Con más de 16: después de los 16 primeros, lo mismo con 17-32.
- **Fin del patrón** (para las cadenas de patrones, las escenas y la frecuencia): cuando termina el recorrido entero (fractal: tras el grupo 1…último; deconstruido: tras el último de la lista).
- El orden se guarda con el patrón (y viaja con él al duplicarlo). Con el transporte parado el fractal vuelve a empezar.

## Qué probar
1. Synth 1, un patrón de 8 pasos con notas distintas, Pattern Settings: pads 26 naranja, 27 / 28 en el color tenue de los de dirección, 29 encendido.
2. Pad 27: se enciende y el 29 se apaga. Play: 1 · 1 2 · 1 2 3 … 1-8, y vuelve a empezar. Stop y Play: empieza por 1.
3. Pad 28: 1 6 2 7 3 8 4 5. Con 16 pasos: 1 6 11 16 2 7 12 13 3 8 9 14 4 5 10 15. Con 32: sigue con 17 22 27 32 …
4. Pad 30 (reverse): el 28 se apaga, reproducción al revés de stock. Pad 29: normal.
5. Nudge: primer paso = 5 (patrón 5-12). Pad 26: suena igual, pero el patrón está ahora en 1-8; los pasos 1-4 de antes están en 13-16. Compruébalo también con automatización de un knob.
6. Nudge con un patrón de 32 pasos (inicio en la segunda página).
7. Una cadena de patrones (SC40.6) con un patrón en fractal: cambia al siguiente al terminar el recorrido.
8. Guarda, apaga, carga: el orden elegido sigue.
9. Un drum: pads 26-28 apagados y sin efecto.

## Verificación en emulación
- `emu_sc40_8.py`: 1 000 finales de paso por la prueba de final de patrón (`0x0802C4E4`) y el avance de pista de stock (`0x0802CB3C`) en 8 patrones (1-16, 1-8, 3-10, 1-32, uno de un paso, 1-21, 4-9, 17-32) contra un modelo; la llamada de anticipación no cambia nada; adelante y reverse iguales que SC40.7; los pads y sus LEDs por el controlador; Nudge en 5 casos (16 y 32 pasos, inicio > final) comparando el patrón entero byte a byte; drums.
- `emu_sc40_3.py` y `emu_sc40_5.py` sobre SC40.8.
- **Sin comprobar en emulación:** el secuenciador con el reloj real (el sonido), ping-pong / random de stock tras quitar un orden propio (usan la misma ruta de stock que antes).
