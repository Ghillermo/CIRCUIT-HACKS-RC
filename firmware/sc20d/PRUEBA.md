# SC20D (DIAGNÓSTICO) — por qué los modos 5 / 6 (retorno de delay / reverb como fuente del sinte) no se oían

`circuittracks-4486-SC20D.syx` — SHA-256 `5db8bbd72f02c207b080db57823cd28e878c07d4a796492978513086a4206b15`
Imagen de 0x5b850 bytes, CRC 0xfb1a56ac, marca `SC20D`.

Es **SC19.1** con los modos 5 y 6 de vuelta y un **medidor** que enseña si el DSP está capturando señal de delay y de reverb. **Úsalo con un proyecto de prueba.** No es un build de uso normal.

## Qué trae
- En la vista de la fuente del sinte (pulsar Synth 1 / Synth 2 dos veces, como en SC19.1) la fila de abajo tiene **siete** pads:

  | Pad | Fuente |
  |---|---|
  | 25 | Noise |
  | 26 | Entrada 1 |
  | 27 | Entrada 2 |
  | 28 | Entrada 1 invertida |
  | 29 | Entrada 2 invertida |
  | **30** | **Retorno del delay** (modo 5) |
  | **31** | **Retorno del reverb** (modo 6) |

  Ganancia de la captura ×8 sobre L + R, como SC17.7. Los modos 5 y 6 **no se recuerdan** al cargar un proyecto (vuelven a noise).
- **Medidor** en esa misma vista, dos barras de 8 pads:
  - **fila 2** (pads 9–16, color melocotón): nivel de la captura del **delay**;
  - **fila 3** (pads 17–24, color crema): nivel de la captura del **reverb**.
  Cada pad más son **12 dB** (el primero ≈ −102 dB de la escala completa; el octavo, −18 dB o más). Mide la media de |L + R| (×8) de cada bloque de audio, **siempre**, aunque ningún sinte esté en modo 5 / 6.
- **Comprobación del medidor:** si el DSP no devuelve la constante de control que el ARM le lee, las dos filas se ponen **rojas** enteras: la lectura DSP→ARM no funciona y las barras no valen nada (dímelo).

## Pruebas en el aparato
1. Envía SC20D y abre la vista de la fuente (Synth 1 dos veces). Sin sonido y con los envíos de FX a cero, las filas 2 y 3 deben estar apagadas.
2. **¿Hay señal en las salidas de delay y reverb?** Haz sonar algo con envío a **delay** alto (tiras 1/2 o drums, en la vista del mixer o la vista FX) y mira la fila 2; repite con el envío a **reverb** y la fila 3. Anota cuántos pads se encienden con envío al máximo y con un envío medio.
3. **¿Lo oye el sinte?** En la vista de la fuente pulsa el pad 30 (delay) y toca una nota del Synth 1 con el nivel de **noise** subido (knob de noise o la matriz); repite con el pad 31 (reverb). Con el delay o el reverb sonando por otra pista, ¿se oye el efecto a través del sinte?
4. Cierra con cualquier botón y comprueba que la vista Preset vuelve a ser normal.

## Cómo leer el resultado
| Lo que ves / oyes | Qué significa |
|---|---|
| Filas 2 / 3 **rojas** | La lectura del DSP no funciona (formato o dirección). Habrá que corregir el diagnóstico. |
| Barras **apagadas** con efectos claramente audibles en la mezcla | El DSP no deja señal en las salidas de delay / reverb en P:$D21 (hipótesis 2 o 3 del estudio): la captura está vacía. |
| Barras **suben** con los envíos, pero el sinte **no suena** con el pad 30 / 31 | La captura funciona; falla la lectura de la voz o la escala (hipótesis 4). |
| Barras **suben** y el sinte **suena** | Los modos 5 / 6 funcionan: el problema de SC17.x eran los envíos o la ganancia. |

## Cómo está hecho
- **DSP** (`tools/linein3.py`, opción `METER`): `fx_cap` (gancho de P:$D21, SC17.5) captura ahora en **todos** los bloques, no solo si hay un sinte en modo 5 / 6, y deja en Y:$3B00 (delay) / Y:$3B01 (reverb) la media de |L + R| × 32 tramas / 32, y en Y:$3B02 una constante (0x5A3C69). Cuesta unas 580 instrucciones más por bloque (de ~55 000). El audio no cambia (salidas finales idénticas a SC19.1 en 24 bloques para los modos 0–4).
- **ARM** (`tools/meter20.py`): con la vista de la fuente abierta, el gancho del servicio del DSP (la cabeza de la cadena de SC19) lee las tres palabras con la lectura de stock `0x08029344(núcleo 0, 0x8000 | dirección Y)` y pinta las barras en el búfer de LEDs de la vista Preset de los sintes. Con la vista cerrada no lee nada.
- Los umbrales son potencias de 4 (2^(6+2k), k = 0..7) sobre el valor de 24 bits.

## Verificación en emulación
`tools/emu_sc20d_dsp.py` (palabras del medidor exactas al bit para varios patrones, constante de control, captura en todos los bloques, voces que siguen tocando la captura, audio idéntico a SC19.1, accesos nuevos solo en Y:$3A80..$3ADF e Y:$3B00..$3B02) y `tools/emu_sc20d.py` (lectura simulada del DSP: orden de las tres lecturas, niveles 0..8 en las dos vistas, umbrales, fila roja, guarda por vtable, pads 30 / 31, cierre con repintado de stock).
La emulación **no puede** decir si la lectura real del DSP funciona en el aparato: para eso está la comprobación en rojo.

## Volver atrás
Envía SC19.1 (o la anterior).
