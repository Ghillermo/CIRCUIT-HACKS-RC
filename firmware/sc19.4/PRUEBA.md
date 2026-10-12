# SC19.4 — SC19.3 con los ajustes guardados que de verdad vuelven

`circuittracks-4486-SC19.4.syx` — SHA-256 `8b4a90b88a7050021511d2381f93c09382d043f9b919d0c5fcd4e56ab5356c57`
Imagen de 0x5b820 bytes, CRC 0x61e0e406, marca `SC19.4`.

SC19.3 arrancó bien, pero **nada de lo guardado volvía** (tampoco al cambiar de sesión). Había dos causas, comprobadas con el código real de stock en emulación (`tools/emu_sc19_4.py`):

1. **Al cargar un proyecto, el stock no restaura los bytes reservados de los sintes** cuando el parche del proyecto es el mismo que ya está cargado (en `0x0802EEFE`, los bytes de bandera de `0x0802F172` / `0x0802F19E` deciden: mismo parche → solo 6 parámetros; parche distinto → el blob entero). 44 de los 65 bytes que guardamos viven en los blobs de los sintes, **entre ellos la firma**: sin firma, el trabajo de arranque daba la zona por vacía y la borraba. Los blobs de los drums y del proyecto sí se restauran siempre. **Arreglo (`persist19.REC_RESTORE`):** tras cada carga, los 65 bytes se copian del **registro de sesión** (`[0x2003D71C + 0x14]` + `REC_BASE[almacén]` + desplazamiento: el búfer que el stock llenó desde el fichero) a los almacenes vivos, antes de comprobar la firma.
2. **Cambiar el parche de un sinte reescribe su blob entero** (la copia de `0x0803BBE2`, vtable de los almacenes, slot 3; por ejemplo el «recargar parche» `0x0802FC82`), con ceros en nuestras posiciones: se perdía parte del estado de los drums (que vive en esos bytes) y las asignaciones. **Arreglo (`persist19.BLOB_KEEP`):** el slot 3 de la vtable apunta a un envoltorio que guarda nuestros 22 bytes del almacén de ese sinte, deja que el stock copie y los restaura.

Todo lo demás es SC19.3 (arranque sin cuelgue) / SC19.1. **SC19.5 y SC19.6 son este mismo build con cosas añadidas** (`firmware/sc19.5/`, `firmware/sc19.6/`); si fallan, este es el mínimo.

## Pruebas en el aparato
1. Flashea y enciende: debe arrancar como SC19.3.
2. **Guardado y carga.** Con un proyecto de prueba: mueve un knob de un drum (K1 o Shift + K1…), asigna un FX a la fila inferior de Master FX y cambia la fuente de un sinte (Synth 1 dos veces, pad 26). **Guarda**, apaga del todo, enciende y **carga** ese proyecto: el drum, la asignación y la fuente deben volver.
3. **Cambio de sesión.** Guarda el proyecto A con esos ajustes. Carga otro proyecto B (distinto): sus ajustes son los suyos (vacíos si no los guardaste). Vuelve a cargar A: los ajustes de A vuelven. Haz el cambio varias veces.
4. **Cambio de parche.** Con ajustes puestos en los drums, cambia el parche del Synth 1 y del Synth 2: los knobs de los drums deben seguir como estaban (antes del arreglo se perdía parte).
5. **Proyecto nuevo:** debe empezar con los drums neutros, los huecos vacíos y los sintes en noise.
6. Anota qué falla, si algo: cuál de los tres tipos (drums / asignación de Master FX / fuente del sinte) y en qué paso.

## Verificación en emulación
`tools/emu_sc19_4.py` con el código real de stock: mismo parche → SC19.3 pierde todo y SC19.4 restaura los 65 bytes, los modos, las asignaciones y los valores de los drums; parche distinto → los dos restauran; proyecto nuevo y registro sin nuestra firma → los dos borran; recarga de parche de cada sinte → SC19.3 borra nuestros 22 bytes y SC19.4 los conserva. Además `emu_sc19.py` (146), `emu_sc19_1.py`, `emu_sc19_dsp.py` y el fuzz sobre esta imagen.

## Volver atrás
SC17.7 (confirmada). SC19.3 arranca pero no guarda; SC19, SC19.1 y SC20D se cuelgan al encender.
