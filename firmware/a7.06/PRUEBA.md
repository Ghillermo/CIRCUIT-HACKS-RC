# Alpha 7.06 (marca `A7.06`) — pendiente de probar, sin publicar

= Alpha 7.05 + `tools/xlwin.py` (el usuario, 2026-11-18: «Do xlanes»; la XL-9 de la caza de fallos del 2026-11-14): **los carriles extra del sinte propio (MIDI 1 / 2) usan su propia ventana del DSP.**

Toda copia con la memoria externa del DSP pasa por una ventana de 64 palabras en la Y del núcleo 0 (`Y:$3B40`): copiar a la ventana, esperar, leerla palabra a palabra (o escribirla y copiar). Entre las dos mitades la tarea duerme, y la otra tarea podía usar la misma ventana: la tarea de LEDs (relleno, vuelta al DSP, guardado, carga y recarga de los carriles extra) contra el bucle principal (las escrituras de Components, los intercambios de samples entre packs, el guardado del sample capturado como WAV). Resultado (raro): valores de los carriles cambiados en la ITCM, en el fichero del proyecto o en la cola que se guarda durante una escritura de Components.

Ahora las cinco funciones de la tarea de LEDs usan `Y:$3B80..$3BBF` (libre: centinelas intactos con todo el tráfico del motor en emulación) y el bucle principal sigue con `Y:$3B40`. Sin cerrojo ni esperas: nada cambia de tiempos. Se hace sobre el código de `xlanes` ya construido (mismo tamaño): sus llamadas a la lectura del DSP, `c_copy`, `c_ywin` y `c_copy2` van a cuatro envoltorios (84 B al final de la imagen; quedan 164 B).

+ `tools/dbtoggle.py` (el usuario: «Pages (shift+tracks 1-4) exit wrong when they are opened and shift+any track is pressed again» → «Toggle: exit»): **con la página de una pista en pantalla (la vista de la fuente de Synth 1 / 2, la Preset de MIDI 1 / 2), Shift + el mismo botón = su vista Note**; otra vez = la página; Shift + otro botón = la página de esa pista (como antes). Antes Shift + el mismo botón volvía a abrir la página (no salía). 56 B libres al final de la imagen.

**Lo demás de la lista de xlanes:** el retraso tras un cambio de patrón (XL-5) ya lo arregló la Alpha 7.02 (`xlanes.use_late`); las ediciones sonando sobre un patrón que no suena (XL-4 b) no se dan: sonando, el patrón editado sigue al que suena en el mismo tick (comprobado en emulación con las cadenas del volcado).

## Probar
1. MIDI 1 con el sinte propio y carriles extra grabados (Record + paso con knobs sin carril de stock) en dos patrones encadenados: suenan al pasar de uno a otro.
2. Guardar el proyecto y volver a cargarlo: los carriles extra siguen.
3. Shift + Synth 1: su página; Shift + Synth 1 otra vez: vista Note; otra vez: la página. Lo mismo con Synth 2, MIDI 1, MIDI 2; Shift + otra pista con una página abierta: la página de esa pista.
4. Si se puede: «Send» de Components de una sesión con carriles mientras suena un patrón con carriles.

Pruebas: `emu_xlwin.py` (nueva: con basura del bucle principal en `Y:$3B40` en cada espera, el relleno, la vuelta, el guardado y la carga dan los datos correctos; la 7.05 falla las cuatro), `emu_xlfix.py`, `emu_xlanes.py`, `emu_patrev.py`, `emu_patfollow.py`, `emu_scsave.py`, `emu_sdsysex.py`, `emu_dbtoggle.py` (nueva; la 7.05 falla las cuatro pistas). `emu_dblpress.py`: un fallo igual que en la 7.05 (las páginas de knobs, prueba anterior a SC52.6).
