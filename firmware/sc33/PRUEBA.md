# SC33 — SC32 + sample capturado en Master FX + grabación en tiempo real en el step-drummer

`circuittracks-4486-SC33.syx` — SHA-256 `6b4b2a836792a79dd1dc3f2e1559188e3dd989a36f6fc1831db474203ec12c8f`
Imagen de 0x61f10 bytes, CRC 0xbb1017ac, marca `SC33`. Reserva: **SC32**. Probado en emulación; **nada probado en el aparato**.
Sin RAM nueva del ARM (usa bytes que ya no se usaban); el sample vive en la memoria externa del DSP (volátil: se pierde al apagar).

## Sample capturado (vista Master FX: Mixer dos veces)
**Pad 32 (rojo) = grabar** la salida del aparato **con los efectos** (después de Master FX), en mono, hasta **3,46 s**:
- **Mantenido:** graba mientras lo mantienes.
- **Pulsación corta** (menos de 0,3 s): empieza a grabar; la siguiente pulsación para.
- **Shift + pad 32:** queda **armado** (parpadea): la grabación empieza en la siguiente línea de compás (al pulsar Play, o en el siguiente compás si ya suena) y termina al final de ese compás. Shift + pad 32 otra vez lo desarma.
- Rojo tenue = en reposo, rojo brillante = grabando.

**Pad 7 (amarillo) = el sample:**
- Tocarlo lo dispara y lo **selecciona**: los knobs pasan a ser los suyos.
- **K1 pitch** (centro = original, ±2 octavas), **K2 modo** (izquierda one-shot, centro gate, derecha loop), **K3 start**, **K4 end**. Si end < start, suena **al revés**.
- En modo **gate** suena mientras mantienes el pad.
- **Shift + pad 7 = loop** sea cual sea el modo; Shift + pad 7 otra vez lo para.
- Amarillo tenue = en reposo, brillante = pulsado o en loop.
- Los knobs del sample se guardan con el proyecto (en el hueco del pad 32, que deja de ser un hueco asignable).

**Pad 6 sigue siendo Vinyl.** **Pad 8** (apagar todo) también para el sample y cancela una grabación enganchada o armada.
El sample se oye directamente en la salida (sin pasar por los efectos de Master FX), así que no se graba a sí mismo.

## Step-drummer: grabación en tiempo real
Con el step-drummer abierto y la **grabación del aparato activa** (Record + Play), tocar un pad de las filas 1-2 (los pasos) **graba su nota en el paso que está sonando**, con el micropaso del momento. La nota y la velocity son las que suenan al tocar ese pad. Cada paso guarda una sola nota: sustituye a la que hubiera. El pad sigue sonando como antes. Sin grabar (o durante la cuenta atrás) solo suena. Shift + pad sigue poniendo / quitando la nota de su propio paso.

## Verificación en emulación
- `emu_sc33_dsp.py` (DSP, intérprete): grabación (L+R)/2 por bloques, tope de 3,46 s, nueva grabación desde 0; reproducción adelante / atrás, pitch ×2 / ×0,5, loop (modo y forzado), gate, stop, silencio al acabar, estado inicial limpio; M4 restaurado; el código de la imagen = el probado y `fx_out` saltando a él. Sin saltos dentro de los bucles `do`.
- `emu_sc33.py` (ARM, rutas reales): pad 7 (disparo, gate, loop con Shift), knobs del sample (valores, topes, sin tocar los de los efectos), lo que el tick manda al DSP (estado, parámetros, comando una vez), pad 32 mantenido / corto / armado por compás, salir de la vista, pad 8, LEDs, Vinyl intacto.
- `emu_sc33_sd.py` (step-drummer, MIDI 1 y Synth 1): sin grabar solo suena; grabando escribe nota, velocity y micropaso en el paso que suena (también con 12 ticks por paso); la cuenta atrás no graba; Shift sin cambios.
- Además `verify_builds.py` (ALL IDENTICAL) y las pruebas de SC23.3–SC31 repetidas sobre SC33.

## Pruebas en el aparato
1. Envía SC33. Abre Master FX con una canción sonando.
2. Mantén el pad 32 un par de segundos y suéltalo. Toca el pad 7: debe sonar lo grabado.
3. Gira K1 (pitch), K3 / K4 (start / end; K4 por debajo de K3 = al revés), K2 (gate / loop).
4. Pulsación corta en el pad 32: graba hasta la siguiente pulsación.
5. Para el transporte, Shift + pad 32 (parpadea) y pulsa Play: debe grabar exactamente un compás.
6. Shift + pad 7: loop; otra vez Shift + pad 7 lo para; el pad 8 también.
7. Step-drummer (MIDI 1 o Synth 1, pad 30): con Record + Play, toca pasos al ritmo: deben quedar grabados donde los tocaste.

## Volver atrás
Envía SC32.
