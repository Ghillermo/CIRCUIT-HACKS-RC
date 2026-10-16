# Beta 1.20 (B1.20) = SC43 = SC42.9 + Pattern Settings en los drums + arreglos de grabación

`circuittracks-4486-SC43.syx` — SHA-256 `8eaa45d492dee434d31b7d85154c3d5bd228691e216c982a47fee2578857567d`, marca `SC43`.
`firmware/b1.20/circuittracks-4486-B1.20.syx` — SHA-256 `d0ba51f049447797d69eace9a1b97b47bb1abfd505270c76bbf1f12af6a12d0e`: el mismo código con la marca `B1.20` (**Beta 1.20**).

El usuario (2026-10-16): «incluir también el resto de funciones de pattern settings (dynamics, pitch mutate, each N iterations…) en vez de modificar el pitch, modifica el sample elegido»; mutate: «25 % ± 1, 25 % ± 8, 12 % de ambas».

- **Vista de probabilidad de un drum** (Pattern Settings dos veces = modo 1; **pad 25** de su Pattern Settings = modo 2): modo 1, fila 4 = **frecuencia** (el paso suena en la última de cada n vueltas, 1-8); modo 2, fila 3 = **dinámicas** (los 8 niveles de las notas; los golpes solo se retrasan dentro de su paso), pads 25-28 = **random-mutate del sample**: nada / 25 % ±1 (el de al lado en su fila de 8) / 25 % ±8 (la misma columna en otra fila) / 12 % de cada uno. Hay que elegir antes un paso con golpe.
- Los valores van en bytes del patrón que el stock no usa: viajan al duplicar el patrón y con Nudge. La primera vez que pones uno en un proyecto se limpian esos bytes en sus 32 patrones de drum (un pack de fábrica trae basura ahí).
- **Arreglos:** los golpes grabados por los rollers y por el arpegio de los drums, y el Nudge de los drums, ya no se pierden con la siguiente edición del patrón.

## Qué probar
1. Drum 1 con golpes: Pattern Settings, pad 25 → elegir un paso → fila 3 (dinámicas) y pads 25-28 (mutate); en marcha, cambian la velocity / el momento / el sample.
2. Pattern Settings dos veces → fila 4: frecuencia; el paso suena cada n vueltas.
3. Grabar con rollers o el arpegio de drums y luego cambiar la probabilidad de un paso: lo grabado sigue ahí.
4. Nudge en un drum y luego editar un paso: sigue rotado.

## Verificación en emulación
- `emu_sc43.py`: el arpegio y un roller grabados sobreviven a una edición de probabilidad (con SC42.9 se perdían); Pattern Settings pad 25 = modo 2 (dinámica 3 y mutate 2, el proyecto marcado y la basura limpia, LEDs), dos veces = modo 1 (frecuencia, fila 3 de stock); en marcha micropaso a micropaso: cada 4 vueltas (vueltas 4 y 8), velocity 68-127, retrasos de 0 a 3 micropasos y nunca antes, mutate ±8 / ±1 / ambos con sus probabilidades, un proyecto sin marcar = el stock; Nudge desde el paso 3 y una edición después. También `emu_sc42_9.py`, `emu_sc42_8.py`, `emu_sc42_7.py` sobre SC43.
