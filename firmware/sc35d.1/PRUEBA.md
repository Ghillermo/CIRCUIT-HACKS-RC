# SC35D.1 — DIAGNÓSTICO: el segundo núcleo del DSP, segunda vuelta

`circuittracks-4486-SC35D.1.syx`, SHA-256 `887a6026ddf443b58172ac337c3791abbf492ae97beee3d8201c073a381c6237`.
Imagen de 0x5c2e4 bytes, CRC 0x935225dc, marca `SC35D.`.

**No es un build de uso.** Usa la misma cadena que SC35D, el mismo pad 9 y el mismo lector. **No toca la tarjeta SD** y no guarda nada. Para volver, envía SC34.

## Qué cambia respecto a SC35D
SC35D demostró que el núcleo 1 ejecuta nuestro código y que comparte la memoria externa con el núcleo 0. También mostró que su memoria interna es pequeña. Las variables del diagnóstico estaban en una dirección que no existe, así que parte del volcado no servía. SC35D.1:
- **Guarda las variables en la memoria compartida entre núcleos**, que funciona, y no en la memoria interna del núcleo 1.
- **Mide con más detalle cuánta memoria tiene el núcleo 1**:
  - de programa: `$0400`, `$0600`, `$0800`, `$0A00`, `$0C00`, `$0E00`, `$0FFF` y `$1000`;
  - de datos X / Y: `$0800`, `$1800`, `$2000`, `$2800` y `$2FFF`.
- **Mide el tiempo libre del núcleo 1:** cuántas vueltas da su bucle por cada bloque de audio. Eso dirá cuántos granos podría procesar.
- **Prueba la memoria externa todo el rato:**
  - el núcleo 0 escribe en `Y:$640000` en cada bloque;
  - el núcleo 1 lo relee y escribe en `Y:$650000`.
- **Pone un centinela en `Y:$600000`**, donde SC33 / SC34 guardan el sample capturado. El núcleo 0 lo escribe una sola vez al arrancar. Si al rato ha cambiado, es que el aparato también usa esa zona.

## Prueba
1. Envía SC35D.1 y comprueba que el aparato suena con normalidad.
2. **Carga un proyecto o cambia de pack**, y deja el aparato encendido un minuto. Así, si el aparato escribe en la memoria externa al cargar samples, el centinela lo detecta.
3. Abre `tools/sc32d1_reader.html` en Chrome o Edge y pulsa «Permitir MIDI y escuchar».
   - En Windows, cierra antes el monitor MIDI, Components y el DAW, porque un puerto MIDI solo lo puede abrir un programa.
   - Otra opción: graba con tu monitor MIDI y abre el `.log` en la página.
4. Pulsa Synth 1 dos veces para abrir la vista de la fuente. El **pad 9** se pone **verde** cuando el núcleo 1 ha respondido.
5. Pulsa el **pad 9**. La página reconoce SC35D.1. Mándame el texto de «Texto para copiar y mandar».
6. Pulsa el pad 9 otra vez al rato. El valor 1 («vueltas / 256») debe subir.

Valores que importan:
- **2 y 3:** cuánta memoria tiene el núcleo 1.
- **6 y 7:** tiempo libre del núcleo 1.
- **4 y 5:** la memoria externa en los dos sentidos. Deben salir `5A6400` y `5A6500`.
- **9 y 10:** el centinela. El 10 debe seguir en `5A6600`.

El aparato corta cada pulsación a 64 mensajes, así que los valores 12 y 13 no llegan. Son secundarios.

## Verificación en emulación
`emu_sc35d_1.py` comprueba:
- **En la imagen:** el núcleo 1 lleva las 364 palabras de stock, con el salto, más las nuestras, y todo acaba antes de la primera dirección probada (`$0400`).
- **El núcleo 1 en el intérprete:**
  - la parte «una vez» corre una sola vez;
  - pone los bits de memoria y restaura las palabras probadas;
  - no toca `r5` / `m5`, que el bucle de stock necesita;
  - cuenta las vueltas por bloque, la última y la mínima;
  - cada 256 vueltas publica el contador, relee la memoria externa y escribe su patrón.
- **El núcleo 0:**
  - lee el centinela antes de escribirlo y lo escribe una sola vez;
  - escribe su patrón en cada bloque;
  - deja el volcado completo y solo pone la marca cuando el núcleo 1 ha respondido.

## Volver atrás
Envía SC34.
