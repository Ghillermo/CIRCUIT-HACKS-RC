# SC32D.1 — DIAGNÓSTICO: valores en bruto de la memoria externa del DSP, por MIDI

`circuittracks-4486-SC32D.1.syx` — SHA-256 `ccbffb8f3bf7e93392d163571594155d59df64ae70bd72e13941d4e71f7706d8`
Imagen de 0x5b9dc bytes, CRC 0xaeb05580, marca `SC32D.1`. **No es un build de uso.** Misma cadena que SC32D (SC20D.1 + diagnóstico). Úsalo con un proyecto de prueba; no guarda nada. Para volver: envía SC32 (o SC31).

## Por qué
SC32D dijo que solo la zona 0 (`Y:$100000`) se escribe y se relee, con contenido fijo (no parecía un retardo), y que todas las demás zonas fallan. Pero el stock carga samples en las zonas 14-29, así que ahí tiene que haber memoria. Este build apunta los valores exactos de unos pocos accesos para saber qué pasa:

| # | Valor |
|---|---|
| 0 | `C0FFEE` = el sondeo corrió |
| 1-3 | SR en el gancho, OMR, M0 (registro de módulo de r0) |
| 4 | r0 tras cargar `$128800` (¿guarda el registro 24 bits?) |
| 5-8 | zona 1: palabra encontrada; releída por r0 tras escribir `5A5A01`; releída con dirección absoluta; releída tras ~1000 ciclos |
| 9 | zona 1: escrita `5A5A11` y releída, las dos con dirección absoluta |
| 10-11 | zona 0: releída tras escribir `5A5A00`; `Y:$000000` (interna) en ese momento (si sale `5A5A00`, la «zona 0» era la RAM interna) |
| 12-13 | zona 14 (samples, `$337000`): palabra encontrada; releída tras escribir `5A5A0E` |

El sondeo corre **una sola vez**, unos segundos después de encender. Cada palabra escrita se restaura al instante, con las interrupciones enmascaradas.

**Corrección de SC32D:** el color que llamé «rojo» (código 0x05) es en realidad **gris** (la tabla RGB está guardada en orden B, G, R). Lo que viste blanco era «la escritura no se relee». Este build usa el rojo de verdad (0x53).

## Prueba
1. Envía SC32D.1, conecta el aparato por **USB** y enciende con un proyecto de prueba (mejor con un patrón sonando y delay / reverb, como antes).
2. Abre `tools/sc32d1_reader.html` en Chrome o Edge y pulsa «Permitir MIDI y escuchar». También vale cualquier monitor MIDI o tu debugger.
3. Synth 1 dos veces → vista de la fuente. El **pad 9** está rojo hasta que el sondeo corre y luego **verde** (unos segundos).
4. Con el pad 9 verde, **púlsalo**: el aparato manda 72 mensajes CC por el **canal 16**:
   - CC 20 = 127 (inicio);
   - por cada valor i = 0..13: CC 21 = i, CC 22 = bits 23..21, CC 23 = bits 20..14, CC 24 = bits 13..7, CC 25 = bits 6..0;
   - CC 20 = 0 (fin).
5. La página muestra la tabla y un texto para copiar: mándamelo. Si usas otro monitor, pega su salida en la página o mándamela tal cual.

Si no llega nada, mira en el Setup que la salida MIDI de CC esté activa. Se puede pulsar el pad 9 las veces que quieras.

## Volver atrás
Envía SC32 (o SC31).
