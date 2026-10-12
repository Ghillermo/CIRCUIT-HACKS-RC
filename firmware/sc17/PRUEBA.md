# SC17 — vista de Master FX (Mixer → Mixer)

`circuittracks-4486-SC17.syx` — SHA-256 `90f3684cab43247972c8f1876700d5a28abd5a3c75d13574c4a51eefe6a55d92`
Imagen de 0x58D48 bytes, CRC 0xA1E08308, marca `SC17`.

Se basa en **SC16** (todo lo anterior). **Añade procesado al master en el DSP: primeras pruebas con volumen bajo.**

## Cómo se entra
- Estando en **Mixer**, pulsa **Mixer otra vez** → vista **Master FX**. Otra pulsación → vuelves al Mixer.
- Si entras en Mixer desde otra vista, siempre aparece el Mixer normal.
- **Shift + Mixer no cambia** (sigue haciendo lo que haga en stock).
- Fuera de la vista Master FX, el Mixer funciona exactamente como siempre: pads, knobs y LEDs.

## Pads (fila 1)

| Pad | Efecto | Color |
|---|---|---|
| 1 | **Gater** (corta el volumen a tempo) | Drum 1 |
| 2 | **Auto-Filter LP** (filtro paso bajo que barre a tempo) | Synth 2 |
| 3 | **Auto-Filter HP** (paso alto) | MIDI 1 |
| 4 | **Digitise** (baja frecuencia de muestreo y bits) | MIDI 2 |
| 5 | **Phaser** | Synth 1 |
| 6 | **Vinyl** (crujidos, siseo, tono de disco gastado) | Drum 3 |

- **Mantener** el pad: el efecto suena mientras lo mantienes.
- **Shift + pad:** queda fijado (latch); Shift + pad otra vez lo quita.
- Puedes combinar varios efectos.
- El pad brilla cuando el efecto está activo y queda tenue cuando no.
- El **último pad pulsado queda seleccionado**: se enciende el pad de debajo (fila 2) y los knobs 1–4 editan ese efecto.
- Los efectos fijados siguen sonando aunque salgas de la vista; los mantenidos se paran al salir.

## Knobs 1–4 (del efecto seleccionado)

| Efecto | Knob 1 | Knob 2 | Knob 3 | Knob 4 |
|---|---|---|---|---|
| Gater | ritmo: 1/1 · 1/2 · 1/4 · 1/8 · 1/16 · 1/32 (a tempo) | profundidad del corte | duty (tiempo abierto) | suavidad (anti-clic) |
| Auto-Filter (LP y HP comparten) | ritmo: 4 compases … 1/16 (a tempo) | profundidad del barrido | resonancia | frecuencia central |
| Digitise | reducción de frecuencia de muestreo (×1 … ×32) | bits (24 … 3) | — | — |
| Phaser | velocidad (20 s … 0,1 s por ciclo) | profundidad | realimentación | mezcla seco/efecto |
| Vinyl | cantidad de crujidos | siseo | tono (paso bajo) | desgaste (paso alto) |

- Valores iniciales: Gater 1/8, profundidad máxima, duty 50 %. Auto-Filter: 1 compás. Phaser: ~6 s por ciclo, mezcla 50 %. Vinyl: crujidos medios.
- **No se guarda:** al encender vuelven los valores iniciales y todo apagado.
- Los knobs no muestran su valor en LEDs.

## Cómo está hecho
**DSP (núcleo 0):**
- Inserción en el master en P:$274: después del filtro master y antes del compresor y la ganancia de salida.
- Cadena: Digitise → Vinyl → Phaser → Auto-Filter → Gater, en estéreo.
  - Digitise: sample & hold cada N tramas más cuantización con máscara.
  - Vinyl: crujidos (picos de la tabla de ruido de stock por encima de un umbral) + siseo, paso bajo y paso alto de un polo.
  - Phaser: 4 all-pass de primer orden por canal, con realimentación y mezcla.
  - Auto-Filter: filtro de estado variable (Chamberlin), LP o HP.
  - Gater: ganancia suavizada por muestra.
- Parámetros y estados en X:$3A40–$3A7F (zona libre). El código va tras el de SC16 en el programa ampliado.
- Coste con los cinco activos: unas +5 900 instrucciones por bloque (~7 %); apagados, +9.

**ARM:**
- El botón Mixer se parchea en 0x0803354C. La vista Mixer (vtable 0x0805A5F0) lleva envoltorios en los slots 0, 1, 4 y 7, que solo actúan con el modo Master FX activo.
- La vista activa se lee en [controlador + 0x6C].
- Un tick, encadenado antes del de SC14, calcula los LFO a tempo y escribe en el DSP solo lo que cambia.
- El estado (128 bytes, con búfer de LEDs propio) va en la reserva de lo alto del heap (SC14 + SC16 + SC17 = 168 bytes). Quedan 64 bytes de margen respecto al heap usado.

## Verificación en emulación
- `emu_masterfx_dsp.py`: cada efecto **exacto al bit** frente a un modelo en punto fijo del DSP56300, y la cadena completa también. Respuesta del Auto-Filter: LP deja 150 Hz ×1,04 y 8 kHz ×0,006; HP, al revés.
- `emu_sc17.py` (28 pruebas ARM):
  - el botón Mixer (doble pulsación, entrada desde otra vista, Shift + Mixer intacto);
  - fuera del modo, los slots de Mixer como stock;
  - pads, latch y knobs con sus límites, más los LEDs;
  - el tick: parámetros estáticos desde las tablas, sin reescrituras innecesarias, Gater a tempo correcto, barridos del Auto-Filter y del Phaser;
  - al salir de la vista se sueltan los efectos mantenidos.
- `emu_sc17_core.py` (DSP con núcleo completo):
  - con todo apagado, el master es idéntico a SC16;
  - con los cinco activos, el master se procesa;
  - la tabla de voces queda intacta;
  - solo se toca X:$3A40–$3A7F.
- Regresiones: SC16 ARM, SC15, SC14, SC14.2 y SC10 DSP pasan. SC16 DSP tiene una diferencia intencionada (el init borra ahora también X:$3A34–$3A7F). Las antiguas dan el mismo resultado que SC14.2.

## Pruebas en el aparato (volumen bajo)
1. Envía SC17 y comprueba que arranca y que todo suena como en SC16.
2. Pon un patrón, entra en Mixer y pulsa Mixer otra vez: deben aparecer 6 pads tenues en la fila 1.
3. Mantén cada pad y escucha. Luego gira los knobs 1–4 con ese efecto seleccionado.
4. Shift + pad para fijar; combina varios.
5. Pulsa Mixer: vuelve el Mixer normal (los fijados siguen sonando). Comprueba los mutes y los LEDs del Mixer.
6. Dime qué tal suenan los rangos de los knobs (demasiado sutil o demasiado extremo) para ajustar las curvas.
7. Si no arranca: Scales + Preset + Note y envía SC16.

## Volver atrás
Envía SC16 con el cargador.
