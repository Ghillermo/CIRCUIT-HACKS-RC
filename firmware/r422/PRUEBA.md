# RC4.22 (marca `R422`) — pendiente de probar

= RC4.21 + `build_sc17.use_spfix()`. Imagen `0x6f80c`.

**Arreglo del song pointer de Master FX** (`build_sc17.use_spfix`): cada salto (la frase que vuelve al inicio o un paso mantenido que se repite) llamaba a la rutina de stock que coloca la posición, que marca el motor como «recolocado»; en el reloj siguiente el stock repetía esa posición en lugar de avanzar. Se perdía un pulso por salto: el paso de inicio sonaba tarde, el paso de después del final se encendía un instante y el reloj se atrasaba. Ahora la marca se quita tras el salto y la posición enseñada es la del paso que suena.

## Probar
1. Master FX, song pointer: Shift + paso 5 y toca el paso 8 (frase 5..8) con un patrón con notas en cada paso y el metrónomo: la frase vuelve a tiempo, sin destello del paso 9 y sin que el reloj se atrase tras muchas vueltas.
2. Mantén un paso (retrigger): se repite cada 1/16 a tiempo.
3. Prueba en emulación: `python tools/emu_spfix.py firmware/<carpeta>` (frase: 24 relojes por vuelta; paso mantenido: 6).
