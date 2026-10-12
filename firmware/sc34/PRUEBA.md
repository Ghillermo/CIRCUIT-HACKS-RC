# SC34 — SC33 + correcciones del sample capturado + sustituir un drum por la captura

`circuittracks-4486-SC34.syx` — SHA-256 `74ef1023691b37cbede33787e53750787cd92491e2445ecf865b1b7d7e47f753`
Imagen de 0x621c0 bytes, CRC 0xc20f4c5c, marca `SC34`. Reserva: **SC33**. Probado en emulación; **nada probado en el aparato**.
Sin RAM nueva del ARM. El programa del DSP termina en `P:$3FE9` (22 palabras libres).

## Qué cambia
**El sample es un efecto asignable** en la fila inferior de Master FX y de la vista FX:
- Mantén el **pad 7** y toca un pad de abajo (**26-31**): ese hueco pasa a ser el sample, con su propia copia de pitch / modo / start / end.
- Tocar el hueco dispara el sample y lo selecciona: los knobs editan los valores de ese hueco. En modo gate suena mientras lo mantienes; **Shift + hueco = loop**.
- El pad 31 sigue siendo un hueco asignable.
- En la fila inferior, los huecos del sample se ven en amarillo: tenue en reposo, brillante mientras lo mantienes.

**Pad 32 = captura también en la vista FX**, igual que en Master FX:
- mantener para grabar mientras lo mantienes;
- pulsación corta para empezar y parar con la siguiente;
- Shift + pad 32 para grabar el siguiente compás.

Una grabación mantenida sigue aunque pases de Master FX a la vista FX.

**K2 (modo) con un color por modo** y brillo fijo: **amarillo** one-shot, **verde** gate, **azul** loop.

**Sustituir un drum por la captura** (volátil: hasta apagar o cambiar de pack):
1. Abre la vista Preset de drums (Drum 1-4 + Preset), donde los pads eligen el sample.
2. **Shift + un pad:** el pad parpadea en blanco (¿confirmar?).
3. **Shift + el mismo pad otra vez:** confirmado. Ese sample (pad + 32 × página) suena a partir de ahora con lo capturado, en cualquier drum que lo use.
4. Un pad sin Shift cancela la pregunta y selecciona como siempre. Shift + otro pad mueve la pregunta a ese pad.
5. Con el teclado cromático de drums encendido no se pregunta nada.

La captura se copia a una ranura propia (hay 8, que se reutilizan en rueda). Así una captura nueva no cambia los drums ya sustituidos.

## Verificación en emulación
- `emu_sc34_dsp.py` (DSP):
  - las pruebas de SC33 sobre el código nuevo;
  - la orden 4: entrada de la tabla `X:$1D8D + 4N` = ranura y longitud, el incremento base intacto;
  - la copia por bloques de 1024 palabras, la rotación de las 8 ranuras, nada si no hay captura;
  - r2 / M2 / M4 / M5 restaurados;
  - el direccionamiento corto `x:(r2+d)`, comprobado con el desensamblador.
- `emu_sc34.py` (ARM, rutas reales):
  - asignar el sample a un hueco con su copia de knobs; tocar el hueco (gate, loop, LEDs); el pad 31 sigue asignable;
  - pad 32 en la vista FX (mantenido, corto, LEDs);
  - K2 por modo;
  - sustitución: preguntar, parpadeo, confirmar, la orden al DSP, cancelar, página 2, el modo cromático;
  - el manejador de stock sigue recibiendo los pads sin Shift.
- Además, `verify_builds.py` (ALL IDENTICAL) y las pruebas de SC23.3–SC33 repetidas sobre SC34.

## Pruebas en el aparato
1. Envía SC34. Graba algo con el pad 32 en Master FX.
2. Mantén el pad 7 y toca el pad 27: el pad 27 se vuelve amarillo. Tócalo: suena el sample. Cambia sus knobs y comprueba que el pad 7 conserva los suyos.
3. Gira K2: el LED cambia de color por modo (amarillo / verde / azul).
4. Vista FX: el pad 32 graba igual que en Master FX; el hueco del sample suena desde ahí.
5. Vista Preset de un drum: Shift + un pad (parpadea), Shift + el mismo pad: ese drum suena con la captura. Graba otra captura: el drum sustituido debe seguir con la anterior.

## Volver atrás
Envía SC33.
