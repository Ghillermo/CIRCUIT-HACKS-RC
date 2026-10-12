# SC32D — DIAGNÓSTICO: qué zonas de la memoria externa del DSP están libres

`circuittracks-4486-SC32D.syx` — SHA-256 `6169e8e6ac669c7a658ca014ba72695d1e4337b9890cb411f9a8c32112ead92b`
Imagen de 0x5c154 bytes, CRC 0x86922d93, marca `SC32D`. **No es un build de uso.** Es la cadena de SC21D (SC20D.1, que arranca y funcionó en el aparato) con el sondeo cambiado por uno de la memoria externa del DSP y sin el monitor de NRPN. Úsalo con un proyecto de prueba; no guarda nada. Para volver: envía SC32 (o SC31).

## Para qué
El sample capturado (pad 7 de Master FX) necesita un búfer de unos 3,4 s en la memoria externa del DSP (SDRAM de 32 MB, desde `Y:$100000`). El stock la reparte en **30 zonas de `$28800` palabras** (≈ 3,46 s cada una):
- zonas 0, 1, 2 y 13: retardos de delay / reverb;
- zonas 14-29: samples;
- zonas 3-12: **uso sin identificar**.

Este build dice qué zonas están libres, y si hay memoria utilizable después del final del mapa de stock (`Y:$5BF000`).

## Qué hace, y por qué es reversible
- El DSP mira **una zona por bloque de audio**, en rueda: las 30 zonas y 8 direcciones más allá (`$5BF000`, `$5C0000`, `$600000`, `$680000`, `$700000`, `$780000`, `$880000`, `$8FF000`).
- De cada zona **lee** 32 palabras repartidas por toda la zona. Con ellas sabe si hay algo distinto de cero y si el contenido **cambia** de una vuelta a la siguiente (un búfer vivo, como un retardo).
- **Escribe una sola palabra por zona, una sola vez:** guarda la palabra que había, escribe un patrón, lo relee, mira si el patrón aparece también 4 M u 8 M palabras más abajo (memoria «espejo») y **devuelve la palabra original**. Todo esto ocurre con las interrupciones enmascaradas, en unos pocos ciclos.
  - El núcleo 1 no se para. Si usara esa misma palabra en esos ciclos, una muestra de un retardo o de un sample quedaría mal hasta que se vuelva a escribir: en la práctica, inaudible.
- No toca la flash, ni las option bytes, ni la configuración de la memoria externa. Todo lo que escribe es RAM del DSP, que se borra al apagar.

## Cómo se lee
Abre la **vista de la fuente del sinte** (pulsa Synth 1 o Synth 2 dos veces). Las filas 2 y 3 (pads 9-24) pasan por **cuatro páginas de 4 s**.

**Al empezar cada página, durante medio segundo, solo se enciende un pad blanco que marca su número:** pad 9 = página 0, pad 10 = página 1, pad 11 = página 2, pad 12 = página 3.

| Página | Pads |
|---|---|
| 0 | pads 9-24 = zonas 0-15 (pad 9 = zona 0) |
| 1 | pads 9-22 = zonas 16-29; pad 23 = `$5BF000`; pad 24 = `$5C0000` |
| 2 | pads 9-14 = `$600000`, `$680000`, `$700000`, `$780000`, `$880000`, `$8FF000`; el resto apagado |
| 3 | número de vueltas completas, 16 bits en blanco (pad 9 = el bit más alto). Si avanza, el sondeo sigue vivo. |

En las páginas 0-2, cada pad es una zona y su color dice qué contiene:

| Color | Significado |
|---|---|
| **verde** | **libre**: todo a cero, sin cambios, se escribe y relee bien |
| amarillo | contenido fijo (samples, por ejemplo) |
| magenta | contenido que cambia (un búfer en uso: delay, reverb…) |
| azul | espejo: el patrón aparece también en otra dirección (no hay memoria propia ahí) |
| rojo | la escritura no se relee (no hay memoria) |
| apagado | todavía sin visitar |

Si **todo sale rojo** (después del pad blanco de la página), el DSP no devolvió la constante de control: el sondeo no corrió o la lectura no funciona.

## Prueba
1. Envía SC32D y enciende con un **proyecto de prueba** que use samples en los drums.
2. **Pon audio por el delay y la reverb:** un patrón en marcha con envíos de reverb y delay altos. Un retardo sin audio contiene ceros y parecería libre. Déjalo sonar al menos 30 s y cambia de sesión una vez (carga otro proyecto) para que se carguen samples.
3. Synth 1 dos veces → vista de la fuente. Fotografía o graba las páginas 0, 1 y 2 (fíjate en el pad blanco de cada una) y la 3 dos veces separadas unos segundos (el contador debe subir).
4. Mándame las fotos o dime los colores. Lo esperable: zonas 0-2 y 13 en **magenta** (con audio), 14-29 en **amarillo**; lo interesante son las zonas 3-12 y las de más allá.

**Si el sonido se para o el aparato se queda colgado:** alguna dirección de más allá del mapa no tiene memoria detrás y el bus no responde. Apágalo, enciende en modo bootloader (**Scales + Preset + Note**) y envía SC32 o SC31. Dime en qué página estaba.

## Volver atrás
Envía SC32 (o SC31).
