# SC34.1 — SC34 con el búfer fuera de la memoria de samples y el loop solo mientras se mantiene

`circuittracks-4486-SC34.1.syx` — SHA-256 `0d9be5722308df55ce073928a9ac62d2b602b07d9841c533cc756a765f488b46`
Imagen de 0x621c8 bytes, CRC 0x6da02cb, marca `SC34.1`. Probado en emulación; **nada probado en el aparato**. **Sustituye a SC33 / SC34 para grabar.** El programa del DSP termina en `P:$3FF6` (9 palabras libres).

## Qué cambia respecto a SC34
1. **Dónde se guarda el audio.**
   - **El problema:** SC35D2 / SC35D3 mostraron que el aparato carga los samples del pack uno detrás de otro desde `Y:$580000`, hasta un límite de `$E80000`. El búfer de la captura de SC33 / SC34 (`$600000`) y las 8 ranuras de la sustitución de drums (`$640000…`) estaban dentro de esa zona. Por eso grabar estropeaba samples del pack hasta volver a cargarlo.
   - **La solución:** la captura va a **`$E80000`** y las ranuras a **`$EA8800–$FEC7FF`**. Es memoria real, por encima del límite de los samples, y el aparato no la toca.
2. **El loop solo suena mientras se mantiene el pad.** Afecta al modo loop (K2 en azul) y a **Shift + pad 7 / hueco del sample**. Al soltar se para. Shift + pad ya no enciende y apaga un loop infinito. El one-shot sigue sonando hasta el final aunque sueltes el pad.
3. **Start = end ya no apaga el sample para siempre.** Con el pad mantenido, en modo loop o gate, si K3 y K4 coinciden (longitud 0) el sample se calla. Al separarlos vuelve a sonar desde el start, sin soltar el pad. En one-shot, con longitud 0 no hay nada que tocar y se para.

## Funciones (igual que SC34, salvo el punto 2)
**El sample es un efecto asignable** en la fila inferior de Master FX y de la vista FX:
- Mantén el **pad 7** y toca un pad de abajo (**26-31**): ese hueco pasa a ser el sample, con su propia copia de pitch / modo / start / end.
- Tocar el hueco dispara el sample y lo selecciona: los knobs editan los valores de ese hueco. En modo gate o loop suena mientras lo mantienes; **Shift + hueco = loop mientras lo mantienes**.
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
`emu_sc34_1.py` hace 80 comprobaciones:
- **Las pruebas de SC34 sobre la imagen de SC34.1:**
  - las del DSP, que incluyen las de SC33;
  - las del ARM por las rutas reales, con las de esta versión: Shift + hueco y Shift + pad 7 = loop con la compuerta mantenida; al soltar, compuerta y loop caen; una segunda pulsación empieza otro loop en lugar de apagar el anterior.
- **El DSP:**
  - el loop (modo 2 o forzado) se para al soltar y el one-shot sigue;
  - con start = end, en loop, gate o loop forzado: sigue activo, en silencio y aparcado en S; al mover el end vuelve a sonar desde S;
  - en one-shot con start = end, se para.
- **Las direcciones:**
  - la captura está en `$E80000` y las ranuras de `$EA8800` a `$FC4000`;
  - solo cambian las 12 direcciones del búfer, ninguna dentro de `$580000–$E7FFFF`;
  - el programa termina en `P:$3FF6`.

Además, `verify_builds.py` da ALL IDENTICAL.

## Pruebas en el aparato
1. Envía SC34.1. Toca un proyecto con drums que usen samples variados.
2. Graba unos 3 s con el pad 32 en Master FX. **Los drums deben sonar igual que antes de grabar.**
3. Pad 7 en modo loop (K2 azul): suena en bucle mientras lo mantienes y se para al soltarlo. Shift + pad 7 hace lo mismo en cualquier modo. En one-shot (K2 amarillo), un toque suena hasta el final.
4. Manteniendo el pad 7 en loop, gira K3 / K4 hasta que coincidan: el sample se calla. Sepáralos sin soltar el pad: vuelve a sonar.
5. Mantén el pad 7 y toca el pad 27, que se vuelve amarillo. Tocar el pad 27 hace lo mismo que el pad 7, con sus propios knobs.
6. Vista FX: el pad 32 graba y el hueco del sample suena desde ahí.
7. Vista Preset de un drum: Shift + un pad (parpadea), y Shift + el mismo pad otra vez. Ese drum suena con la captura y los demás samples siguen intactos.

## Volver atrás
Envía SC34 o SC33, pero **no grabes con ellos**.
