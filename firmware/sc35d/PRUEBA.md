# SC35D — DIAGNÓSTICO: el segundo núcleo del DSP (para la síntesis granular)

`circuittracks-4486-SC35D.syx` — SHA-256 `41ca9e01f29947040e4dab2c10b23e7b86c7323117be04d93c8a1748fbe12326`
Imagen de 0x5c1e4 bytes, CRC 0x1a25bc9e, marca `SC35D`. **No es un build de uso.** Misma cadena que SC32D / SC32D.1 (SC20D.1, que arranca y funcionó en el aparato). **No toca la tarjeta SD** y no guarda nada. Para volver: envía SC34.

## Para qué
El DSP tiene dos núcleos. Todo el sonido lo hace el núcleo 0, que ya está casi lleno. El núcleo 1 solo tiene un pequeño servicio de stock (364 palabras): si podemos meterle código propio, la síntesis granular (y Beat Repeat, Reverser…) tendría sitio de sobra. Este build contesta:
- si el núcleo 1 ejecuta código nuestro sin romper su servicio (el aparato debe sonar igual);
- cuánta RAM de programa tiene;
- si lee y escribe la memoria externa (donde está el sample capturado) y si lo que escribe un núcleo lo ve el otro;
- cuánto tiempo libre tiene por cada bloque de audio.

## Qué hace (todo en la RAM del DSP, volátil)
- **Núcleo 1:** su bucle de stock salta a nuestra rutina en cada vuelta.
  - La primera vez escribe, relee y restaura un patrón en su memoria de programa (`$0400`…`$7FFF`) y en su X / Y internas, con las interrupciones enmascaradas.
  - Lee la palabra que el núcleo 0 dejó en `Y:$640000` y escribe la suya en `Y:$650000` (zona libre de la memoria externa).
  - En cada vuelta cuenta, y mide cuántas vueltas da por cada bloque de audio del núcleo 0.
  - Vuelve a su bucle de stock.
- **Núcleo 0:** cuenta sus bloques y copia las respuestas del núcleo 1 a su memoria Y, de donde las lee el ARM.

## Prueba
1. Envía SC35D. **Comprueba que el aparato suena con normalidad** (los drums y sus samples dependen del servicio del núcleo 1).
2. Abre `tools/sc32d1_reader.html` en Chrome o Edge y pulsa «Permitir MIDI y escuchar». En Windows, cierra antes el monitor MIDI, Components y el DAW, porque un puerto MIDI solo lo puede abrir un programa. Otra opción: graba con tu monitor MIDI y abre el `.log` en la página. El aparato corta cada pulsación a 64 mensajes, así que los valores 12 y 13 no llegan; los importantes son del 0 al 11.
3. Pulsa Synth 1 dos veces (vista de la fuente). El **pad 9** se pone **verde** cuando el núcleo 1 ha respondido.
4. Pulsa el **pad 9**: manda 72 mensajes CC por el canal 16. La página reconoce que es SC35D y explica cada valor; mándame el texto. Púlsalo otra vez al rato: «vueltas / 256» debe subir.

Si el pad 9 sigue **rojo**, el núcleo 1 no ha ejecutado nuestro código: puede que el aparato cargue el otro programa del núcleo 1 (hay dos en la tabla). Eso también es un resultado: dímelo.

## Verificación en emulación
`emu_sc35d.py`:
- en la imagen: el programa del núcleo 1 = las 364 palabras de stock con el salto en `P:$12A`, más las nuestras;
- el núcleo 1 en el intérprete con un conductor de bloques: marca, bits de RAM, memoria externa en los dos sentidos, palabras restauradas, registros intactos, vueltas por bloque y el contador publicado cada 256 vueltas;
- el núcleo 0: copia de las respuestas, marca solo con la respuesta del núcleo 1, contador de bloques.

## Volver atrás
Envía SC34.
