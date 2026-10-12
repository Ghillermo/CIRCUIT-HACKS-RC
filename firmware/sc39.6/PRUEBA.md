# SC39.6 — copiar proyectos a otro hueco o a otro pack

`circuittracks-4486-SC39.6.syx` — SHA-256 `4969dd842f75c09e3c7f7fc5327e2f0a78db7d31f871e2f386793aaf85d8af8e`
Imagen de 0x682f0 bytes, CRC 0x19319632, marca `SC39.6`.

Es SC39.5 con una función nueva (solo ARM): **copiar un proyecto entero a otro hueco**, del mismo pack o de otro. **Escribe en la tarjeta SD: usa packs de prueba y ten copia.**

## Manejo (vista Projects)
1. **Duplicate + pad A** (un hueco con proyecto) = A es la fuente: parpadea en amarillo. Duplicate + A otra vez la olvida.
2. **Duplicate + pad B** = copia A en B.
   - B vacío: se copia al momento; B queda en amarillo fijo.
   - B con un proyecto: parpadea en blanco (pregunta). **Duplicate + B otra vez** en menos de ~5 s lo sustituye.
   - El hueco del proyecto que está cargado nunca se escribe.
3. **A otro pack:** elige la fuente, carga el otro pack, entra en Projects y Duplicate + pad B. La fuente se conserva (aunque no se vea: es de otro pack).
4. La fuente sirve para varias copias. Se pierde al apagar o al abrir la vista Master FX.

## Qué probar
1. Projects: Duplicate + un proyecto → parpadea amarillo. Duplicate + un hueco vacío → queda amarillo. Cárgalo: debe ser idéntico al original.
2. Duplicate + un hueco ocupado → blanco; espera 6 s → no pasa nada. Repite y confirma → sustituido.
3. Duplicate + el proyecto cargado → nada.
4. **Entre packs:** fuente en el pack A, carga el pack B, Duplicate + hueco vacío. Carga ese proyecto en B. Ojo: los patches y samples son los del pack B en los mismos números (un proyecto guarda números, no los sonidos).
5. Apunta: cuánto tarda la copia (el aparato no responde mientras), y si el proyecto copiado se ve en su color normal al salir y volver a entrar en Projects, o solo tras cargar el pack de nuevo / reiniciar.
6. Sin Duplicate, la vista Projects funciona como siempre (cargar, Clear, guardar en otro hueco).
7. Todo lo de `firmware/sc39.5/PRUEBA.md`.

## Verificación en emulación
- `emu_sc39_6.py` (botón Duplicate y pads por el controlador, tarea de LEDs, API de contenido sobre el modelo de la SD): la fuente, la copia byte a byte (160 780 B en 40 trozos de 4 KB), la pregunta y su caducidad, el proyecto cargado intocable, olvidar la fuente, copia del pack 31 al pack 7 con la tarea de almacenamiento de vuelta en el pack cargado, SC39.5 sin cambios.
- **Sin comprobar en emulación:** que el original cargue y muestre el proyecto copiado (su lista de huecos en uso vive en RAM), el tiempo de la copia y la escritura real en la tarjeta.
