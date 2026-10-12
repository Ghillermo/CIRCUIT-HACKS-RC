# SC15 — entrada de línea en lugar del noise del sinte

`circuittracks-4486-SC15.syx` — SHA-256 `3612b83e37109436af9aff0252eeee0d819db12c3cb954c865e8974824f35065`
Imagen de 0x4DFC8 bytes, CRC 0x958C60AD, marca `SC15`.

Se basa en **SC14.2** (todo lo anterior, con el flag de retorno de FX ya corregido).

## Qué hace
En cada sinte puedes cambiar la fuente de **noise** por la **entrada de audio 1** o la **2** (las de las tiras 3/4 del mezclador; mono, nivel de línea). La entrada pasa por la voz exactamente igual que el noise: nivel de noise del mezclador del patch, modulación, **filtro, envolventes** y FX. Así suena solo mientras tocas notas, filtrada y con la forma de la envolvente.

- Vista **Preset** del sinte (botón Preset con Synth 1 o 2 seleccionado), manteniendo **Shift**:
  - pad 25 (fila 4, el 1.º) = **Noise** (stock);
  - pad 26 (fila 4, el 2.º) = **Entrada 1**;
  - pad 27 (fila 4, el 3.º) = **Entrada 2**.
- Mientras mantienes Shift, esos 3 pads muestran el modo: el elegido brillante, los otros tenues, con el color del sinte. Al soltar Shift la vista vuelve a ser la normal.
- Sin Shift, los pads de la vista Preset funcionan como siempre (elegir patch). Shift + cualquier otro pad, también.
- Cada sinte tiene su propio modo. Todas las voces de ese sinte oyen la misma entrada.
- **No se guarda:** al encender, los dos sintes vuelven a Noise.

## Importante para oírlo
- El patch tiene que tener **nivel de noise** en su mezclador. En muchos patches está a 0, y en el panel no hay mando para el noise. Súbelo con el editor de Components o por MIDI: **CC 56** en el canal del sinte (127 = máximo).
- Para oír solo la entrada, baja los niveles de los osciladores 1 y 2 en el mezclador del patch (editor de Components).
- La entrada sigue sonando también por su tira del mezclador (3 o 4). Si solo la quieres a través del sinte, baja el nivel de esa tira.

## Cómo está hecho
**DSP núcleo 0:**
- El mezclador de cada voz (P:$9C6) suma osciladores × nivel y noise × nivel. El noise se lee de una tabla (Y:$F7F…) que se regenera en cada bloque, con un desfase por voz y paso 4.
- En P:$9C3 se sustituyen dos instrucciones por un salto a código nuevo (P:$E3, sin usar pila). Si el sinte de la voz (X:$CC) está en modo entrada, el puntero de lectura pasa a ser el anillo de entrada: y:$FFD + 0/1, paso 2 (tramas [in1, in2] del bloque actual). Si no, hace lo de stock.
- Modos en X:$3A01 (Synth 1) y X:$3A02 (Synth 2), en la zona de memoria libre comprobada. El init del DSP los pone a 0.

**ARM:**
- La vista Preset de los sintes (vtable 0x0805AC9C) tiene sustituidos el slot 0 (pads) y el slot 7 (LEDs).
- Los modos se guardan en los bytes libres del bloque de RAM que ya reservó SC14 (no se usa RAM nueva).
- Al cambiar de modo se marca el grupo Audio In. Su manejador (H9) escribe los modos en el DSP desde la tarea de parámetros, y también tras cualquier recarga del DSP.

## Verificación en emulación
- `emu_sc15.py`:
  - pads con y sin Shift, los dos sintes, independencia entre sintes;
  - LEDs: sin Shift idénticos a stock; con Shift, pads 25–27 en tenue/brillante/tenue; al soltar, repintado de stock;
  - H9 escribe los modos;
  - **DSP de núcleo completo** con una señal de prueba en el anillo de entrada: en modo Noise, la mezcla de la voz es **idéntica a stock**; en modo In 1 / In 2, la mezcla es exactamente entrada × nivel de noise (error 0) en los dos sintes, y el otro sinte no cambia.
- SC14.2, SC14 (ARM y DSP) y SC10 DSP pasan. SC10 ARM tiene 4 diferencias intencionadas (H9 escribe además los dos modos). Las regresiones antiguas dan el mismo resultado que SC14.2.
- Limitación: el audio de los osciladores (que pasa por el núcleo 1) no está emulado. La parte de noise/entrada sí.

## Pruebas en el aparato (volumen bajo)
1. Envía SC15. Comprueba que **arranca bien** y que todo suena igual que SC14.2.
2. Conecta una fuente de línea a la **entrada 1** (por ejemplo, una caja de ritmos o música).
3. Synth 1 → Preset. Mantén **Shift**: los pads 25–27 deben encenderse (el 25 brillante = Noise).
4. Shift + **pad 26** (Entrada 1). Sube el noise del patch (CC 56 = 127) y baja los osciladores.
5. Toca notas en el Synth 1: debes oír la entrada 1 solo mientras suena la nota, pasando por el filtro y la envolvente del patch. Mueve el filtro.
6. Shift + **pad 27** (Entrada 2): con la fuente en la entrada 1, el Synth 1 debe quedarse sin esa señal.
7. Shift + **pad 25**: vuelve el noise normal.
8. Repite con el Synth 2 y comprueba que cada sinte guarda su modo por separado.
9. Pulsa pads de la vista Preset sin Shift: deben seguir cambiando de patch.
10. Dime qué tal el **nivel**: si la entrada queda muy baja o muy alta respecto al noise, se puede añadir ganancia.

## Volver atrás
Envía SC14.2 con el cargador. Si no arranca: Scales + Preset + Note y SC14.2.
