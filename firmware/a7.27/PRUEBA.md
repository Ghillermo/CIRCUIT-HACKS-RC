# Alpha 7.27 (marca `A7.27`) — instalada en el aparato (2026-11-22), lo demás sin probar

= Alpha 7.22 + las 7.23-7.26 (sin publicar) + `build_sc17.use_spfix()`. Imagen `0x6f524`.

- **7.23-7.25:** código repetido convertido en bucles y tablas (≈ 0,6 KB de flash libre más), sin cambios de uso (`emu_fold4` / `emu_fold5` / `emu_fold6`: los mismos cambios de RAM que antes).
- **7.26:** Easy Start apagado de verdad (`msdcut.use_midionly`): las Alpha 7.21 / 7.22 lo dejaban encendido (MIDI + una unidad USB que no funcionaba); ahora solo USB MIDI. Comprobado en el aparato con el diagnóstico S725D4.
- **7.27:** el song pointer a tiempo.

**El song pointer de Master FX** (`build_sc17.use_spfix`): cada salto (la frase que vuelve al inicio o un paso mantenido que se repite) llamaba a la rutina de stock que coloca la posición, que marca el motor como «recolocado»; en el reloj siguiente el stock repetía esa posición en lugar de avanzar. Se perdía un pulso por salto: el paso de inicio sonaba tarde, el paso de después del final se encendía un instante y el reloj se atrasaba. Ahora la marca se quita tras el salto y la posición enseñada es la del paso que suena.

## Probar
1. Master FX, song pointer: Shift + paso 5 y toca el paso 8 (frase 5..8) con un patrón con notas en cada paso y el metrónomo: la frase vuelve a tiempo, sin destello del paso 9 y sin que el reloj se atrase tras muchas vueltas.
2. Mantén un paso (retrigger): se repite cada 1/16 a tiempo.
3. Prueba en emulación: `python tools/emu_spfix.py firmware/<carpeta>` (frase: 24 relojes por vuelta; paso mantenido: 6).
