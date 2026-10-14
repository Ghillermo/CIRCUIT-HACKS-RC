# SC40.4 — frecuencia por paso (contando las vueltas de cada patrón) y dinámicas aleatorias

`circuittracks-4486-SC40.4.syx` — SHA-256 `9359e80283935faf3871f2f2c54d8cf3fa497c99df2f91d0a76bd7ef2f15b9a2`
Imagen de 0x68f98 bytes, CRC 0x83408516, marca `SC40.4`.

**Sustituye a SC40.3**, cuya frecuencia no funciona en el aparato (leía una dirección que no es el reloj del secuenciador). Aquí la frecuencia cuenta las vueltas de cada patrón: «cada 7» es la 7.ª, 14.ª… vez que suena **ese** patrón, con cualquier cadena de patrones; la cuenta vuelve a cero al parar.

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
   Con una cadena de dos patrones y el pad 2 en un paso de cada uno: los dos suenan en su segunda vuelta, cuarta, sexta…
3. La fila 3 sigue siendo la probabilidad de siempre.
4. Pattern Settings (vuelve a la primera página) y **pad 25**: se abre la misma vista en modo 2 (fila 3 verde, fila 4 melocotón).
5. Con un paso mantenido, prueba los pads 2 a 8 de la fila 3 y escucha: velocity que varía (4, 8), nota que se adelanta / atrasa y cambia de duración (2, 6, 7), las dos cosas (3, 5).
6. La fila 4 del modo 2 es el random-mutate (octava / escala) de antes.
7. **Record + Play con el modo 2 en pantalla:** lo que sale (nota, velocity, duración, posición) se queda escrito en el paso. Con Record pero en otra vista, o sin Record: no se escribe nada.
8. Sal de la vista: los pasos siguen sonando con su frecuencia y sus dinámicas. Guarda, apaga, carga: siguen.
9. Lo demás de SC40.2 (sidechain, compresor) igual.

## Límites
- Una nota no sale de su paso: una nota cuantizada (micropaso 0) no puede adelantarse, y ninguna pasa del micropaso 5.
- La frecuencia cuenta las veces que el patrón ha terminado desde que se paró el secuenciador; un cambio de escena a mitad de patrón cuenta como una vuelta. Si se usa el editor de CC de MIDI 1 / 2 mientras suena, las cuentas vuelven a cero.
- Una nota ligada conserva su duración.

## Verificación en emulación
- `emu_sc40_3.py` sobre SC40.4: lo de SC40.3 (vistas, pad 25, máscaras idénticas a SC40.2 sin nada puesto, posición, velocity y duración, escritura) y los contadores: 32 de 10 bits independientes (0..839), la frecuencia por las vueltas del patrón que suena (248 casos, sin depender del tiempo), el avance de pista del original cuenta una vuelta al acabar el patrón (no a mitad, ni en la llamada de previsión, ni en drums), a cero al parar y cuando otro usa esos bytes.
- **Sin comprobar en emulación:** el secuenciador en marcha y cómo suena.
