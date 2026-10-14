# SC40.3 — frecuencia por paso y dinámicas aleatorias (vista de probabilidad en dos modos)

`circuittracks-4486-SC40.3.syx` — SHA-256 `69cac0fcbd23d2b03d2d9b91699675ef965d7bf40e7c251f6fb8c7f1eaa63aee`
Imagen de 0x68ed0 bytes, CRC 0x53e6273f, marca `SC40.3`.

**No usar: la frecuencia (fila 4 del modo 1) no funciona en el aparato; usa SC40.4.**

Es SC40.2 más dos modos en las filas 3 y 4 de la vista de probabilidad de las pistas de notas (Synth 1 / 2, MIDI 1 / 2). Los drums no cambian.

| | Cómo se entra | Fila 3 | Fila 4 |
|---|---|---|---|
| **Modo 1** | Pattern Settings dos veces (como siempre) | probabilidad del original | **frecuencia** (amarillo): pad n = el paso suena una de cada n pasadas del patrón, la última de cada n; pad 1 = siempre |
| **Modo 2** | **pad 25** de la vista Pattern Settings (melocotón) | **dinámicas** (verde): cambio aleatorio en cada reproducción | random-mutate de la nota (melocotón), como hasta ahora |

Dinámicas (fila 3 del modo 2), V = velocity, M = micropasos de posición y de duración (sorteados por separado):

| Pad | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| | nada | M −3..0 | M −3..0, V 0..+32 | V 0..+32 | M −2..+2, V 0..+32 | M −2..+2 | M 0..+3 | V −32..+32 |

Los valores se guardan en el paso: suenan con cualquier vista en pantalla y viajan con el patrón y el proyecto.

## Qué probar
1. Synth 1 con un patrón con notas. Pattern Settings: **el pad 25 está encendido** (melocotón). En un drum, apagado.
2. Pattern Settings otra vez (vista de probabilidad, modo 1): con un paso mantenido, la fila 4 es una barra amarilla. Pon el pad 2 en un paso y el 4 en otro: el primero suena una pasada sí y otra no; el segundo, una de cada cuatro (la cuarta). Para y pulsa Play: la cuenta empieza de nuevo.
3. La fila 3 sigue siendo la probabilidad de siempre.
4. Pattern Settings (vuelve a la primera página) y **pad 25**: se abre la misma vista en modo 2 (fila 3 verde, fila 4 melocotón).
5. Con un paso mantenido, prueba los pads 2 a 8 de la fila 3 y escucha: velocity que varía (4, 8), nota que se adelanta / atrasa y cambia de duración (2, 6, 7), las dos cosas (3, 5).
6. La fila 4 del modo 2 es el random-mutate (octava / escala) de antes.
7. **Record + Play con el modo 2 en pantalla:** lo que sale (nota, velocity, duración, posición) se queda escrito en el paso. Con Record pero en otra vista, o sin Record: no se escribe nada.
8. Sal de la vista: los pasos siguen sonando con su frecuencia y sus dinámicas. Guarda, apaga, carga: siguen.
9. Lo demás de SC40.2 (sidechain, compresor) igual.

## Límites
- Una nota no sale de su paso: una nota cuantizada (micropaso 0) no puede adelantarse, y ninguna pasa del micropaso 5.
- La frecuencia cuenta pasadas del patrón desde Play (por el tiempo transcurrido y la longitud del patrón); con cadenas de patrones cuenta el tiempo total, no las veces que ha sonado ese patrón.
- Una nota ligada conserva su duración.

## Verificación en emulación
- `emu_sc40_3.py`: las vistas por el controlador (pad 25, los dos modos, escritura en el byte [3] del paso, LEDs, drum sin efecto); el constructor de máscaras del original con 2 016 casos idénticos a SC40.2 cuando no hay nada puesto; la frecuencia en 2 240 casos (pasadas, longitudes, sync rates); la posición (un solo disparo por paso, el del modelo); velocity y duración en 624 reproducciones; escritura solo con Record y el modo 2 en pantalla.
- **Sin comprobar en emulación:** el secuenciador en marcha (la cuenta de pasadas con el reloj real) y cómo suena.
