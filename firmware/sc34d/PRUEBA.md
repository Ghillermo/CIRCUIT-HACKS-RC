# SC34D — DIAGNÓSTICO: un fichero propio junto a cada sesión en la tarjeta SD

> ❌ **Probado el 2026-10-08: NO USAR.** Escribe y lee sus ficheros, pero rompe el duplicado de packs (los packs copiados se quedan sin sesiones) y copia datos de sesión en los `_SC34D.bin`. Ver «Resultado de SC34D» en `docs/NOTAS.md`.

`circuittracks-4486-SC34D.syx` — SHA-256 `d8fa43d1cf65d94e3d791f8e9f6419d8841fa511058fda0d3c55663a859d248e`
Imagen de 0x623dc bytes, CRC 0xcbae0996, marca `SC34D`. Es **SC34 completo** + esta prueba. Para volver: envía SC34.

## Para qué
Comprobar que podemos escribir y leer **nuestros propios ficheros** en la tarjeta SD al guardar y cargar un proyecto, antes de guardar ahí el sample capturado (SC35).

## Qué hace
- **Al guardar una sesión** (botón Save), además del `NN_SESSION.ncs` de siempre, escribe junto a él un fichero `NN_SC34D.bin` de 16 bytes:
  - el texto `SC34DTST`;
  - un contador de guardados;
  - un contador de cargas.
- **Al cargar una sesión**, suma una carga en su `NN_SC34D.bin`.
- Usa la misma maquinaria de ficheros del stock, en la misma tarea del aparato que guarda la sesión, y justo después de que el stock haya cerrado su fichero.
- **No modifica ningún fichero de stock:** solo crea y actualiza los `_SC34D.bin`.

## Prueba
1. **Haz una copia de seguridad de la tarjeta SD** en un PC (por precaución).
2. Envía SC34D. Carga una sesión de prueba, cambia algo y **guárdala** (Save). Repite el guardado una vez más.
3. Carga otra sesión y vuelve a cargar la primera.
4. Apaga, saca la tarjeta y mírala en el PC:
   - en la carpeta `Sessions` del pack debe haber un `NN_SC34D.bin` junto al `NN_SESSION.ncs` que guardaste;
   - con un editor hexadecimal: `53 43 33 34 44 54 53 54` («SC34DTST»), luego los guardados (`02 00 00 00`) y las cargas (`01 00 00 00` o más) en little-endian;
   - las sesiones deben cargar y sonar igual que antes.
5. Dime qué ves (o mándame los ficheros `_SC34D.bin`). Si algo va mal (no guarda, se cuelga al guardar), vuelve a SC34 y restaura la copia de la tarjeta.

## Verificación en emulación
`emu_sc34d.py`, con un sistema de ficheros en memoria en lugar de la tarjeta, llamando por la vtable real de la clase de ficheros (`0x0805B150`) como la tarea de almacenamiento:
- una escritura en la sesión pasa intacta al stock y la marca;
- al cerrar: cierre de stock, y después abrir / leer / escribir / cerrar nuestro fichero, con los contadores bien;
- segunda escritura, carga y un fichero ajeno en nuestro sitio (empieza de 0);
- otros ficheros (`_PCM.wav`, `_PATCHBANK.cpb`) sin cambios;
- un fallo al abrir: solo el cierre.

## Volver atrás
Envía SC34.
