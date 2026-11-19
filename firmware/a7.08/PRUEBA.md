# Alpha 7.08 (marca `A7.08`) — pendiente de probar, sin publicar

= Alpha 7.07 + `tools/fxstep.py` (el usuario, 2026-11-19: «FX sequencer change. The current FX sequencer is discarded. Instead, we make a new step sequencer on the Master FX view» → «All, including sample», «Add», «With the project»). El prototipo A7PROT queda aparte (no está aquí).

- **Efecto mantenido + paso del song pointer** (pads 9-24 = pasos 1-16) = ese efecto suena en ese paso en cada vuelta. Valen los pads 1-6 (efectos), 7 (el sample) y 26-31 (los huecos, el gesto mecánico en el 31); los pads mantenidos a la vez o uno tras otro se **suman**; un paso en silencio pierde el silencio. Esa pulsación no llega al song pointer.
- **Clear + paso vacío** = el paso en silencio (el master entero, el `B_MUTE` de la 5.64); **Clear + paso con efectos o en silencio** = vacío.
- **Duplicate + paso = aleatorio** (el usuario: «Also add random step … duplicate + step: random»), otra vez = fuera (quita el silencio): cada vez que llega el paso suena uno de sus efectos elegido al azar (un paso aleatorio vacío: uno de los seis efectos de arriba); violeta (`0x49`). Bit 14 de la máscara; en el bloque, bit 7 del byte 16 + i (la firma queda en los 16 primeros bytes).
- Sonando: los efectos de arriba del paso se suman a los mantenidos / fijados (envoltorio de las 3 llamadas a `c_fsqfx`); los huecos y el silencio pasan por `c_fxsq` (el gancho del secuenciador antiguo, ahora `c_fqsq`: bits 0-5 = pads 26-31, bit 7 = silencio); el sample: al entrar en su paso, inicio + gate (como pulsar el pad 7); al salir, el gate fuera (un bucle fijado lo conserva). Fuera de la vista de Master FX, `c_smtick` quita el gate cada tick: el sample suena como one-shot. Parado: nada.
- LEDs: un paso con efectos en el color del LED de su primer pad, en silencio rojo (`0x53`), el que suena blanco como siempre.
- **Guardado con el proyecto**: 32 B en los bytes 8..39 de los ajustes del patrón 8 de MIDI 1 (projsyn usa 0..4, stpair 5 / 6, wtui los 5 / 6 de MIDI 2): byte i = los bits de arriba del paso i, byte 16 + i = los de abajo | silencio en el bit 6 | aleatorio en el bit 7; bit 7 del byte i (i < 16) = i & 1 (firma: la basura de fábrica, todo 0 o todo 0xFF, no pasa). Lo escribe una cabeza de la llamada de guardado (si hay algo o el bloque ya es nuestro) y lo lee una cabeza del reenvío de la carga (carga, proyecto nuevo, encendido; sin bloque = vacío).
- **El secuenciador de efectos de MIDI 1 / 2 se descarta y su código sale** (`vcf21.use_nofsq()`, que pone también `build_sc17.NOFSQ` / `modesel.NOFSQ`; `sdpv` lo sigue): `c_fsq` / `c_fsqbits`, el knob selector y sus LEDs, la base del par vacío, el azar de `c_fsqfx`, el pad 31 de la fila de motores; el ciclo de motores (Shift + pad 27) pasa de muestra a apagado. Un proyecto con el estado antiguo: la voz apagada como antes. (El usuario: «Yes» a la limpieza.)

RAM `0x2004FB10` (48 B, libre bajo el `CNT` de drumpat): + 0 `FXS1`, + 4 el paso visto, + 5 el gate del sample es nuestro, + 6 lo elegido por el paso aleatorio, + 8 el estado del azar, + 16 las 16 máscaras (bits 0-6 pads 1-7, 8-13 pads 26-31, 14 aleatorio, 15 silencio). Imagen `0x6FBB0`: **flash libre 1 162 B** (final 1 104, huecos de `dspz` 37 + 3, `hole` 18; sin la limpieza del secuenciador antiguo serían ≈ 550 B).

## Probar
En Master FX (Mixer, Mixer), con Play:
1. Mantén el pad 1 y toca el paso 3 (pad 11): el Gater suena en el paso 3 en cada vuelta; el pad 11 en el color del pad 1.
2. Mantén el pad 26 (un hueco) y toca el paso 5: ese hueco en el paso 5. Mantén los pads 2 y 4 y toca el paso 3: se suman al Gater.
3. Mantén el pad 7 y toca el paso 1: el sample suena al empezar cada vuelta.
4. Clear + un paso vacío: rojo, el master en silencio en ese paso; Clear + ese paso: vuelve. Clear + el paso 3: vacío.
4b. Duplicate + un paso con varios efectos: violeta, cada vuelta suena uno de ellos al azar; Duplicate + un paso vacío: uno de los seis efectos de arriba al azar; Duplicate otra vez: fuera.
5. Un paso sin nada mantenido: el song pointer como siempre (retrigger / frase).
6. Guarda el proyecto, carga otro, vuelve: los pasos siguen; un proyecto que no los tenía: vacío.

Pruebas: `emu_fxstep.py` (20 comprobaciones); la batería de 73 pruebas frente a la 7.07.
