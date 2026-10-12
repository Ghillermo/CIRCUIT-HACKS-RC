# SC19.5 — SC19.4 con los retornos de FX del Setup también en la entrada del sinte

`circuittracks-4486-SC19.5.syx` — SHA-256 `a097637abe77fd9676e75372f355e85121eff6fa4c74fa2818a520abb8b5f2df`
Imagen de 0x5b984 bytes, CRC 0xe82bfaa3, marca `SC19.5`.

Es **SC19.4** (arranque sin cuelgue, ajustes guardados que vuelven, parches que no los borran) **más** lo que pediste: cuando el modo de línea de entrada del Setup lee reverb o delay, ese retorno también llega a la entrada de línea / línea invertida del sinte.

En **Setup** hay dos toggles de SC10: **pad 22** = el retorno de **reverb** pasa por la tira 3 del mixer (en lugar de la entrada de audio 1) y **pad 23** = el retorno de **delay** pasa por la tira 4 (en lugar de la entrada 2). Con SC19.5, mientras uno de ellos está encendido, la **fuente del sinte** que lee esa entrada recibe ese retorno en vez de la entrada de línea:

| Fuente del sinte (pads 25–29 de la vista de la fuente) | Pad 22 de Setup apagado | Pad 22 encendido (reverb → tira 3) | Pad 23 encendido (delay → tira 4) |
|---|---|---|---|
| 26 · Entrada 1 | línea 1 | **retorno de reverb** | línea 1 |
| 27 · Entrada 2 | línea 2 | línea 2 | **retorno de delay** |
| 28 · Entrada 1 invertida | línea 1 invertida | **retorno de reverb invertido** | línea 1 invertida |
| 29 · Entrada 2 invertida | línea 2 invertida | línea 2 invertida | **retorno de delay invertido** |

El nivel es el del ruido del sinte (el mismo mando que para la entrada de línea). La captura del retorno se amplifica ×8 (`linein3.FX_GAIN_SHIFT = 3`, el valor que funcionó en SC20D.1); si suena demasiado fuerte o flojo, es esa constante. **Los modos 5 / 6 (retorno de delay / reverb como fuente propia) no están**: los quitaste; la fuente sigue siendo 0..4.

SC19.3 arrancó bien, pero **nada de lo guardado volvía** (tampoco al cambiar de sesión). Había dos causas, comprobadas con el código real de stock en emulación (`tools/emu_sc19_4.py`):

1. **Al cargar un proyecto, el stock no restaura los bytes reservados de los sintes** cuando el parche del proyecto es el mismo que ya está cargado (en `0x0802EEFE`, los bytes de bandera de `0x0802F172` / `0x0802F19E` deciden: mismo parche → solo 6 parámetros; parche distinto → el blob entero). 44 de los 65 bytes que guardamos viven en los blobs de los sintes, **entre ellos la firma**: sin firma, el trabajo de arranque daba la zona por vacía y la borraba. Los blobs de los drums y del proyecto sí se restauran siempre. **Arreglo (`persist19.REC_RESTORE`):** tras cada carga, los 65 bytes se copian del **registro de sesión** (`[0x2003D71C + 0x14]` + `REC_BASE[almacén]` + desplazamiento: el búfer que el stock llenó desde el fichero) a los almacenes vivos, antes de comprobar la firma.
2. **Cambiar el parche de un sinte reescribe su blob entero** (la copia de `0x0803BBE2`, vtable de los almacenes, slot 3; por ejemplo el «recargar parche» `0x0802FC82`), con ceros en nuestras posiciones: se perdía parte del estado de los drums (que vive en esos bytes) y las asignaciones. **Arreglo (`persist19.BLOB_KEEP`):** el slot 3 de la vtable apunta a un envoltorio que guarda nuestros 22 bytes del almacén de ese sinte, deja que el stock copie y los restaura.

## Pruebas en el aparato
1. Flashea y enciende: debe arrancar como SC19.4.
2. **Retornos en el sinte.** Pon el sinte (Synth 1, dos veces → vista de la fuente) en el pad 26 (entrada 1), activa en Setup el pad 22 (reverb → tira 3), y envía algo a la reverb (envíos de FX altos en una pista): el sinte debe oír el retorno de reverb; con el pad 22 apagado, la entrada de línea. Repite con el pad 28 (invertida: con la entrada de línea fuera de fase debe sonar distinto), y con el pad 23 / delay en los pads 27 / 29.
3. **Sin Setup activo** todo debe sonar como SC19.4 (entradas de línea normales).
4. **Guardado** (como SC19.4): guardar, apagar, cargar; cambio de sesión; cambio de parche; proyecto nuevo.
5. Anota qué falla y con qué pads (Setup 22 / 23, fuente 26–29).

## Verificación en emulación
- `tools/emu_sc19_5_dsp.py` (núcleo 0 del DSP completo): con cada combinación de flags y modos 1–4 el sinte toca el retorno (o su negado) × nivel del ruido, o sigue con la línea de entrada; los modos 0–4 con los flags apagados salen idénticos a SC19.4; el otro sinte no cambia; coste con flags apagados +9 instrucciones por bloque.
- Las pruebas de SC19.4 (`emu_sc19_4.py`, `emu_sc19.py`, `emu_sc19_1.py`, el fuzz, `emu_sc17*.py`, `emu_sc19_dsp.py`) sobre esta imagen.

## Volver atrás
SC19.4 (sin los retornos en el sinte), SC17.7 (confirmada).
