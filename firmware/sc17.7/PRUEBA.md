# SC17.7 — song pointer, retornos de delay/reverb más fuertes y modos en Shift + Scale

`circuittracks-4486-SC17.7.syx` — SHA-256 `58f699842f445a8ab8a1e74de02ca480c7290db9e5a238eb3222761973af52e7`
Imagen de 0x599a4 bytes, CRC 0x7bcf20db, marca `SC17.7`.

Es **SC17.6** (la que ya probaste) más tres cambios. La reserva de RAM no crece: sigue en 220 bytes (unos 20 de margen).

## 1. Delay y reverb como fuente del sinte: ahora con nivel
En SC17.6 no se apreciaban. Los retornos de delay y reverb viven en el dominio del mezclador (la ganancia de las tiras vale 0,0615, unos −24 dB), muy por debajo de la entrada de línea. Ahora la señal capturada es **(L + R) × 8**, es decir, **×16 de la media**. Eso los pone al nivel de la entrada de línea.
- Si ahora satura, dímelo: se baja con una constante (`linein3.FX_GAIN_SHIFT`, hoy 3).
- Si aún se oye bajo, también.

## 2. Los modos de la fuente del sinte pasan a Shift + Scale
Antes: mantener Shift en la vista Preset del sinte. **Ahora la vista Preset es la de stock.**
- **Shift + Scales** abre la vista de stock «7» (el firmware solo la abre con el transporte **parado**, como ya hacía). Es un selector de 15 pads en las columnas 3–6; sus pads siguen haciendo lo suyo.
- Los **7 modos** están en las **columnas 1 y 2** (libres en esa vista), de arriba abajo:

| Pad (fila, columna) | Modo |
|---|---|
| 1.ª fila, columna 1 | Noise (stock) |
| 1.ª fila, columna 2 | Entrada 1 |
| 2.ª fila, columna 1 | Entrada 2 |
| 2.ª fila, columna 2 | Entrada 1 (el otro signo) |
| 3.ª fila, columna 1 | Entrada 2 (el otro signo) |
| 3.ª fila, columna 2 | **Retorno del delay** |
| 4.ª fila, columna 1 | **Retorno de la reverb** |

- Se aplican al sinte de la **pista seleccionada** (Synth 1 o Synth 2; con otra pista, los pads se apagan y no hacen nada).
- El modo activo está **brillante** y los demás **tenues**, con el color de cada sinte.
- No se guarda: al encender, Noise.

## 3. Song pointer en la vista Master FX (filas 2 y 3, pads 9–24)
Los 16 pads de las filas 2 y 3 son los **pasos 1–16** (paso 1 = pad 9, paso 16 = pad 24). El marcador de «efecto seleccionado» de la fila 2 desaparece de la vista (los knobs 1–4 siguen con el color del efecto).
- **Sin tocar, no hace nada.** Si suena, el **pad brillante** sigue el paso en curso, según el beat general de la canción (el contador del secuenciador, 16 pasos).
- **Mantener un paso:** cuando el song pointer llega al final (por defecto el paso 16 = pad 24), la canción **retoma en ese paso en lugar de en el 1**.
- **Mantener dos pasos:** el primero es el inicio y **el segundo el final**.
- **Shift + paso:** ese paso pasa a ser el **inicio fijo**. Volver a pulsar el mismo paso con Shift lo desactiva; Shift + otro paso lo mueve.
- **Con un inicio fijo activo**, tocar otro paso (sin Shift) **coloca ahí el final**. Un paso anterior al inicio se ignora. Al desactivar el inicio vuelve el final por defecto.
- Si el segundo paso mantenido queda antes del primero, no se hace bucle.
- Colores: pads de paso tenues, **inicio** y **final** marcados, **paso en curso** brillante (colores de los efectos de Master FX: el Vinyl, el Gater y el Auto-Filter LP).
- No se guarda.
- El salto vale para **todos los tracks** a la vez (posición global). Afecta al ciclo de 16 pasos de la canción. Con patrones de 32 pasos el bucle se queda dentro de la mitad en que esté la reproducción.

## Cómo está hecho
- **Retornos:** `linein3.FX_GAIN_SHIFT = 3` añade un `asl #3` a la suma L + R capturada (la saturación del DSP la limita). El resto del DSP es el de SC17.6.
- **Modos:** `tools/modeview.py`. Ganchos en la vista 7 (`ctrl+0x34`, vtable 0x0805A6A4: pad 0x08044006 y LEDs 0x08047592). Los pads fuera de la lista pasan al manejador de stock. La vista Preset recupera sus manejadores de stock. El mecanismo del modo (bytes de SC14+18/19 y el grupo Audio In) es el de SC15.
- **Song pointer:** `build_sc17.songptr_code`.
  - Estado en 4 bytes que sobraban: SC14+21 (inicio fijo), +22 (final fijo), +23 (primer paso mantenido) y el byte 31 del bloque de Master FX (segundo paso).
  - La posición se lee del contador de ticks del motor del secuenciador (`[[motor+0x90]]`, 6 ticks por paso). El motor está en `0x20038ECC` (`[[X+0x2C]+4]`, con `X = [[ctx+0x10]]`).
  - El gancho está en el comienzo de su función de tick (`0x0802C418`). Cuando el tick que va a ejecutarse es el primero del paso final + 1, llama a la rutina de stock «fijar posición» (`0x0802BFE0`, la que usa el Song Position Pointer MIDI: escribe los ticks y resincroniza todos los tracks) con el tick del paso de inicio menos 1, y el tick siguiente cae justo en el inicio.
  - Si se vuelve al tick 0 se usa un tick equivalente más alto (múltiplo de 6 × mcm(1..16) × 2) para no necesitar el tick −1.

## Verificación en emulación
- `emu_sc17_7.py`:
  - modos por Shift + Scales: la vista de stock se abre, los pads fijan el modo del sinte de la pista, los LEDs brillante / tenue, pista de batería → apagado e ignorado, los pads de stock llegan al manejador de stock, Preset en stock;
  - máquina de estados del song pointer (mantener, mantener dos, Shift, final fijo, ignorados) y LEDs (inicio, final, cabeza, parado);
  - el tick: sin rango no cambia nada, bucles 5–12, 1–8, inicio con final por defecto, en ciclos posteriores, con pulsaciones mantenidas = inicio y final fijos, rango invertido ignorado, bloque de Master FX sin crear = tick de stock; cada salto es una llamada de stock «fijar posición» con la resincronización.
- `emu_sc17_5_dsp.py`: la captura es (L + R) << 3 saturada, la mezcla de la voz = captura × nivel, y todo lo demás idéntico a SC17.4.
- `emu_sc17.py`, `emu_sc17_5.py`, `emu_sc17_6.py`, `emu_sc17_core.py`: pasan. Todos los builds anteriores se siguen generando idénticos.
- **Límite de la emulación:** el motor del secuenciador solo se ha podido ejecutar con su función de tick. La resincronización de los tracks (`0x0802C008`) necesita los datos de patrones, que el volcado de RAM no tiene; en las pruebas se registra la llamada. En el aparato es el mismo camino que usa el Song Position Pointer MIDI de stock.

## Pruebas en el aparato
1. Envía SC17.7. Comprueba que arranca y que todo lo de SC17.6 sigue igual (Mixer, Master FX, FX, filas de FX).
2. **Modos:** transporte parado → pista del Synth 1 → Shift + Scales: aparecen los pads de modo en las columnas 1–2. Elige delay (3.ª fila, columna 2) con un patch con noise al máximo (CC 56 = 127), envía algo al delay y toca. Debe oírse. Prueba la reverb. Si satura o se oye poco, dímelo.
3. Vista Preset del sinte con Shift: debe ser como siempre.
4. **Song pointer:** Mixer → Mixer (Master FX), con el secuenciador sonando: el pad de la cabeza recorre los pads 9–24 al ritmo de la canción.
   - Mantén un paso: cuando llegue al final retoma en ese paso.
   - Mantén dos pasos.
   - Shift + paso, y luego otro paso suelto para el final.
   - Comprueba que no se quedan notas colgadas al saltar y que los tracks de distinta longitud no se descuadran.
5. Si el salto suena mal o cuelga notas, vuelve a SC17.6 y dímelo.

## Volver atrás
Envía SC17.6 (o SC17.5).
