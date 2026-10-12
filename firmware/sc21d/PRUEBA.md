# SC21D — DIAGNÓSTICO: sondeo de la memoria de programa del DSP y monitor de NRPN

`circuittracks-4486-SC21D.syx` — SHA-256 `f73a02e76fc7b3c6931534d7fdcd8806e08adbdd6a800a53f5e9e39c674c9cdc`
Imagen de 0x5bb08 bytes, CRC 0x843ecefd, marca `SC21D`. **No es un build de uso**: es SC20D.1 (la cadena que arranca y ya funcionó en el aparato) con el medidor de captura sustituido por un sondeo del DSP y un monitor del MIDI entrante. Úsalo con un proyecto de prueba; no guarda nada. Para volver: flashea SC20.1 o SC21.

## Para qué
1. ¿Hay RAM de programa del DSP por encima de `P:$3800` (el límite que nos hemos puesto) y hasta dónde? Decide si la fase 2 del VCF (comb, ring mod, chorus…) cabe.
2. ¿Qué ve el núcleo 0 en la memoria compartida, el registro OMR y el estado del puente entre núcleos (ICC)? Orienta el uso del segundo núcleo.
3. ¿Qué NRPN / CC llegan por el MIDI de entrada y por qué función pasan? Confirma el gancho `0x08052854` para añadir NRPN propios.

## Qué hace, y por qué es reversible
- El DSP ejecuta el sondeo **una sola vez** tras arrancar (desde el gancho `P:$23C`, como el VCF de SC20). **Lee** OMR, SR, un word de la memoria compartida (`X:$030000`) y dos registros de estado del ICC (`ICPR1`, `ICCR1`; no lee `ICDR`, porque leerlo borra una interrupción entre núcleos). **Escribe** un patrón `$5A5A5A` en 8 direcciones de programa a partir de `P:$3800` (por encima de todo lo que cargamos), lo relee y **restaura** la palabra original, con las interrupciones enmascaradas durante la prueba.
- No toca la flash interna, ni las option bytes, ni el EMC (memoria externa), ni arranca el núcleo 1. Todo lo que escribe es RAM del DSP, que se borra al apagar.
- Resultado en `Y:$3B10..$3B18`. El ARM solo lee esas palabras con la lectura de stock (la misma del medidor de SC20D, probada en el aparato).
- El monitor de NRPN solo **anota** el último CC / NRPN que llega (gancho en los 4 primeros bytes de `0x08052854`, que ejecuta enseguida las instrucciones desplazadas) en los primeros bytes de la cola de los ajustes; no cambia lo que hace el MIDI.

## Cómo se lee
Abre la **vista de la fuente del sinte** (pulsa Synth 1 o Synth 2 dos veces). Las filas 2 y 3 (pads 9-24) rotan por cuatro páginas de 4 s, cada una de un color:

| Color | Página | Qué muestra |
|---|---|---|
| amarillo | hechos del DSP | un pad por hecho, encendido = cierto: **pad 9** = el sondeo se ejecutó; **pads 10-17** = escritura y relectura correcta en `P:$3800, $3C00, $3FFF, $4000, $5000, $6000, $7000, $7FFF`; **pad 18** = `P:$3800` valía 0; **pad 19** = valía `$FFFFFF`; **pad 20** = la palabra `X:$030000` vale 0; **pad 21** = `ICPR1 ≠ 0`; **pad 22** = `ICCR1 ≠ 0` |
| azul | OMR | los 16 bits bajos del registro OMR (pad 9 = bit 15) |
| verde | último NRPN | fila 2 = MSB (CC 99), fila 3 = LSB (CC 98), en binario (pad 9 = bit 7 de la fila 2) |
| magenta | último CC | fila 2 = número de CC, fila 3 = su valor |

Si el DSP no devuelve la constante de control, las páginas amarilla y azul salen **todas rojas** (el sondeo no se ejecutó o la lectura no funciona).

## Interpretación esperada
- Pads 10-17 todos encendidos: hay RAM de programa hasta `$7FFF` como mínimo → la fase 2 cabe de sobra. Solo los primeros encendidos: la RAM acaba en esa dirección. Ninguno: el límite real es `$3800` (hay que comprimir tablas o usar el núcleo 1).
- Pad 18 o 19 encendido (valía 0 o `$FFFFFF`) con el pad 10 encendido: esa zona está libre, sin uso del stock.

## Prueba
1. Flashea SC21D, enciende y espera unos segundos.
2. Synth 1 dos veces → vista de la fuente. Anota o fotografía el patrón de cada página (cuatro colores). Con la página roja, mira el aviso de arriba.
3. Para el NRPN: desde un secuenciador o un monitor MIDI, manda al Circuit Tracks un NRPN (CC 99 = MSB, CC 98 = LSB, CC 6 = valor) en un canal que escuche (los parámetros del sinte, por ejemplo) y mira las páginas verde y magenta.
4. Dime lo que lees y decido la fase 2 con datos.
