# SC13 — Sidechain en los drums — plan de prueba

`circuittracks-4486-SC13.syx` — SHA-256 `817ad7e7aac0cb17ca70ee7b2c823e58d23a8134676ebfc70856f98bbfd5b7b7`
Imagen de 0x4DE90 bytes, CRC 0x911D6025, marca `SC13`.

Incluye todo SC12. **Modifica el programa del DSP: haz las primeras pruebas con el volumen bajo.**

## Qué hace
Cada drum puede duckarse con otro drum, como hacen los sintes en stock. Por ejemplo, el hi-hat se aparta cuando suena el bombo.

**Vista Sidechain (Shift + FX).** Con ▼ ahora hay dos páginas más:

| Página | Fila 3 | Fila 4 |
|---|---|---|
| Sintes (stock) | Synth 1 | Synth 2 |
| MIDI (stock) | MIDI 1 | MIDI 2 |
| **Drums 1-2** | Drum 1 | Drum 2 |
| **Drums 3-4** | Drum 3 | Drum 4 |

En las páginas de drums:
- **Filas 3 y 4:** pad 1 = OFF (rojo); pads 2-8 = los mismos 7 presets que en stock. El pad del preset activo se ilumina brillante, en el color del drum.
- **Fila 1, pads 5-8:** eligen qué drum dispara el sidechain. Se aplica al drum de la última fila que tocaste; al llegar a la página, al primer drum de la página. El pad del drum disparador se ilumina en el color del drum afectado.
- Las filas 1 y 2 no tienen más funciones.
- ▲ / ▼ se iluminan cuando hay página en esa dirección.

**Atajo:** si entras con Shift + FX teniendo seleccionado un drum, se abre directamente su página.

**Funcionamiento:**
- El ducking afecta a todo el drum: el sonido seco y los envíos a reverb y delay.
- La envolvente es la de stock y empieza en el golpe del drum disparador, aunque el drum afectado esté en silencio en ese momento.
- Si silencias el drum disparador, no dispara, igual que en stock.
- **No se guarda:** al apagar, todo vuelve a OFF y el disparador vuelve a ser el drum 1. Cambiar de proyecto no lo reinicia.

## Cómo está hecho
**DSP, núcleo 0:**
- X:$EC + 9·k: un bloque por drum: [disparo, attack, hold, decay, depth, 4 palabras de estado].
- El flag de SC10 pasa de X:$EC a X:$EB.
- Al arrancar el DSP, se ponen a 0 X:$EB–$10F.
- **P:$218E** `jsr mixhook`: si depth ≠ 0, avanza la envolvente con la rutina de stock `func_0012bb` y multiplica la señal mono del drum (X:$2C02) antes de la mezcla.
- **P:$21AB** `jmp idle` (antes era el `rts` final de cada voz): si el drum no sonó en este bloque, avanza igualmente la envolvente.
- El código nuevo ocupa vectores de interrupción no usados: P:$54–$7B (timers / ESAI_1, desactivados) y P:$D9–$FA.

**ARM:**
- El estado está en RAM en 0x2004E000. Esa zona queda por encima del límite del heap (0x20044E58) y por debajo de la pila. En los volcados de stock nunca se escribe.
- Se reutiliza el grupo 5 de parámetros del proyecto (sidechain del Synth 1). Su manejador manda además los 4×4 parámetros de los drums.
- La función de disparo de drums escribe además el disparo en el bloque de cada drum que tenga ese drum como disparador.
- Vista Sidechain:
  - pads y LEDs mediante los slots 0 y 7 de la vtable 0x0805AC2C;
  - ▲ / ▼ (contenedor 0x08043664 / 0x08043702) y sus LEDs (vtable 0x0805AA64);
  - entrada a la vista en 0x0804352A.
- El *store* de página de stock solo guarda 0/1. Las páginas de drums viven en RAM, así que volver a un firmware anterior es seguro.

## Verificación en emulación
**DSP**, intérprete dsp56kEmu, comparado con la rutina de stock:
- Arranque: X:$EB–$10F a 0, sin tocar X:$110.
- Depth 0, los 4 drums: señal y bloque intactos. La mezcla completa del drum es idéntica a stock.
- Depth > 0, los 4 drums, 12 bloques con 2 disparos:
  - la señal es exactamente señal × envolvente del sidechain de stock con los mismos parámetros;
  - estado y consumo del disparo, como stock;
  - el ducking es real: ganancia mínima de 0,01 a 0,64 según los parámetros.
- Mezcla del drum con el sidechain activo = mezcla de stock de la señal duckada.
- Drum en silencio: la salida de voz avanza la envolvente igual que stock, sin tocar la señal.
- Drum que suena: la envolvente avanza una sola vez por bloque.
- `func_00208a` completo con los 4 drums en silencio:
  - con el sidechain apagado, idéntico a stock;
  - con el sidechain encendido y un disparo, la envolvente avanza una vez.
- SC10 (retornos de FX y entradas) con el flag en X:$EB: pasa.

**ARM**, 37 comprobaciones:
- Estado inicializado desde la basura de la RAM.
- Páginas Sintes y MIDI idénticas a stock (pads y LEDs).
- ▼ / ▲: Sintes → MIDI → Drums 1-2 → Drums 3-4 → tope y vuelta. LEDs de ▲ / ▼ correctos. El *store* nunca pasa de 1.
- Pads de presets y de disparador; pads de las filas 1-2 ignorados; LEDs con los colores de cada drum.
- Grupo 5:
  - las escrituras de stock no cambian;
  - después van las de los 4 drums;
  - con el mismo preset, los valores son idénticos a los del Synth 1.
- Disparo de cada drum: escrituras de stock y disparo en los bloques correctos.
- Entrada con un drum seleccionado: abre su página.
- Las vistas FX y Sidechain con otros pads funcionan como stock.

**Regresiones:** SC12, SC10 DSP, SC09, SC06, SC05 y SC04 pasan.

**Fallos que cambian a propósito:**
- SC11: el Pitch del modo cromático es por cents desde SC12;
- SC10: el flag está ahora en X:$EB;
- SC08: el constructor pone a 0 cuatro bytes;
- SC07: el bit 28 se guarda desde SC10.

## Pruebas en el aparato (volumen bajo)
1. Envía SC13 y comprueba que arranca y suena igual que antes.
2. Haz un patrón: bombo en el drum 1 a negras y hi-hat continuo en el drum 3.
3. Shift + FX, y ▼ dos veces (página Drums 1-2) y una más (Drums 3-4). Las filas deben verse en los colores del drum 3 y del drum 4.
4. Fila 3, pad 4 (preset 3): el hi-hat debe duckarse con cada bombo. Prueba los presets 2 a 8: más profundidad y más duración.
5. Fila 1, pad 6: el disparador pasa a ser el drum 2. El hi-hat debe duckarse con el drum 2 y dejar de hacerlo con el bombo.
6. Fila 3, pad 1 (OFF): el hi-hat vuelve a sonar normal.
7. Selecciona el drum 2 y pulsa Shift + FX: debe abrirse la página Drums 1-2.
8. Comprueba que el sidechain de los sintes y los retornos de FX de SC10 (pads 22/23 de Setup) siguen funcionando.
9. **Si oyes clics, cortes o el DSP se cuelga (silencio total), apaga y dime en qué paso pasó.**

## Volver atrás
Envía SC12 (o anterior) con el cargador. Si no arrancara, enciende con Scales + Preset + Note.
