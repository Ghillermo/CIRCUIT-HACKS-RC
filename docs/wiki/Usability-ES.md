# Usabilidad

*[English version](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Usability) · [Inicio](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Home#en-español) · [Guía por vistas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html)*

Las convenciones que hacen el mod previsible, los atajos que valen en todas las vistas y las ayudas para tocar y grabar.

## Convenciones

Cada capítulo es una vista del aparato: cómo se llega, qué hace cada pad, knob y botón, y los submenús que abre.

- **Pads 1-32** de arriba-izquierda a abajo-derecha: fila 1 = 1-8, fila 2 = 9-16, fila 3 = 17-24, fila 4 = 25-32.
- **Knobs K1-K4** arriba, **K5-K8** abajo. «**Shift + X**» = mantener Shift mientras se usa X; lo mismo con Clear y Duplicate.
- Lo que no aparece aquí funciona como en el aparato original (manual oficial de Novation).
- *(desde RC2)* = nuevo desde RC2 (no está en RC0.9 / RC0.9S). La versión más segura, RC2.10S (y las S anteriores), no escribe nada propio en la tarjeta: lo marcado «escribe en la tarjeta» no hace nada en ella (el LED de Save se pone rojo).
- *(desde RC2.02)* = nuevo en RC2.02 (no está en RC2.01).
- *(solo Beta 3.37)* = solo en la **Beta 3.37**, la versión de prueba con las funciones nuevas (no está en RC2.10).
- La **lista de características** (el manual anterior) resume cada función en una línea, por temas.

## Botones que funcionan en todas las vistas

Shift, Clear, Duplicate, Save y Octave ganan funciones según la vista; aquí, las que valen en casi todas.

| Gesto | Dónde | Qué hace |
|---|---|---|
| **Clear + knob a la derecha** | drums, motor de las pistas MIDI, Master FX | El knob vuelve a su valor por defecto (las dos capas, con y sin Shift). LED **lavanda** = hecho, como en el original. |
| **Clear + knob a la izquierda** | drums (knobs de stock), motor de las pistas MIDI *(desde RC2)* | Borra la automatización de ese knob en el patrón que suena, como el original (LED **rojo**). En el motor MIDI, la de los dos carriles del knob (con y sin Shift) que tengan automatización. |
| **Shift** | todas | Con Shift pulsado, los atajos disponibles se iluminan en **amarillo**; la opción elegida, en otro color. |
| **Save** | todas | Guarda el proyecto como siempre; además escribe en el pack los samples sustituidos por capturas (Preset de drums) si caben en la memoria de samples *(escribe en la tarjeta)*. |
| **Pulsar el botón de la pista otra vez** | Synth 1 / 2 | Abre la vista de la fuente del sinte (2.3). |
| **Clear + Synth 1 / 2** | su vista | *(desde RC2)* Sus ocho macros a los valores del patch cargado. |
| **Clear + el botón de un drum** | su vista | *(desde RC2)* Borra la automatización de sus knobs en el patrón que suena y pone sus ocho knobs por defecto. |
| **Dos botones de pista de notas a la vez** | todas | Teclado partido *(desde RC2)*: Synth 1 + Synth 2; *(desde RC2.02)* cualquier par de Synth 1, Synth 2, MIDI 1 y MIDI 2. |
| **Shift + Clear** | todas | Metrónomo en cuatro estados *(desde RC2)*: sin metrónomo → metrónomo → solo cuenta atrás → cuenta atrás y metrónomo. Con Shift pulsado, el LED de Clear enseña el estado: rojo (sin metrónomo) / verde (metrónomo) / magenta (solo cuenta atrás) / cian (las dos). El volumen del clic es el de stock: **Tempo/Swing** y **K5**. |
| **Play** con Record armado y la cuenta atrás | parado | Un compás de cuenta atrás (4 clics al tempo del proyecto, Record parpadea en rojo) y después arranca la grabación *(desde RC2)*. Play durante la cuenta la cancela. La cuenta atrás se guarda con el proyecto. |
| **Shift + Play** | todas | *(desde RC2)* **Cuantiza** el patrón que suena en la pista elegida: las notas y los golpes grabados fuera de la rejilla van al paso más cercano (micropasos 1-2 → el inicio de su paso; 3-5 → el del siguiente; los del último paso, al primero). En los drums, un paso con varios golpes (un redoble) se queda. Con Shift el LED de Play se ve amarillo; verde después de cuantizar. Sustituye al Shift + Play del original (otra forma de arrancar). |
| **Shift + Scales** | todas | Editor de la escala propia *(desde RC2)* (2.2). |
| **Mixer dos veces** | todas | Master FX (6.1). |
| **Scales + Preset + Note** al encender | — | Modo de recuperación del bootloader de Novation: permite volver a instalar cualquier firmware. |

- Los LEDs de los knobs enseñan con su **brillo** el valor de las funciones nuevas (más brillo = más valor; en los knobs bipolares, oscuro en el centro).
- Los colores animados (que pulsan) no se usan para estados fijos.
- **LFO a tempo** *(solo Beta 3.37)*: los knobs de **velocidad de LFO** (K7 de la página VCA-VCF del motor de MIDI 1 / 2, Shift + K4 de la matriz, Shift + K7 de los drums, K1 del Auto-Filter y del Phaser en Master FX) son **bipolares**: al centro, el LED tenue; **a la derecha, LFO libre** (más rápido cuanto más a la derecha); **a la izquierda, a tempo**, del centro hacia fuera 1/16T, 1/16, 1/8T, 1/8, 1/4T, 1/4, 1/2T, 1/2, 1 compás T, 1 compás, 2T, 2, 4T, 4, 8T y 8 compases (4 clics cada una), con cada ciclo empezando en el **primer tiempo del compás** (se recoloca en cada tick del secuenciador; parado sigue al tempo). En la matriz, cada forma de Shift + K4 es un tramo con su propio centro. Lo guardado antes con otra velocidad puede sonar distinto.

## Tocar y grabar

### Vista de pista de Synth 1 / 2 (Note, Velocity, Gate)

*Cómo se llega:* Pulsa **Synth 1** o **Synth 2**. Los pads tocan el sinte como siempre.

- **Vista de la fuente** — el sinte puede procesar una entrada de audio en lugar de su ruido.
- **Teclado partido** *(desde RC2)* — arriba un sinte y abajo el otro, cada uno con su escala, octava y velocity; *(desde RC2.02)* con cualquier par de pistas de notas.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#synth-nota)

### Vista Scales y escala propia

*Cómo se llega:* Pulsa **Scales** como siempre (tónica y escala de stock); **Shift + Scales** para la escala propia.

- **Escala propia** *(desde RC2)* — hasta 7 notas sobre la tónica y un periodo libre (por ejemplo, una escala que se repite cada 7 semitonos). La usan los pads de las pistas de notas, el cuantizado y el random-mutate; se guarda con el proyecto.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#escalas)

### Vista Micro Step (pistas de notas)

*Cómo se llega:* Pulsa **Gate dos veces** con una pista de notas elegida (Synth 1 / 2, MIDI 1 / 2).

- **Micropasos y Tie (de stock)** — coloca cada nota fuera de la rejilla y enlázala con el paso siguiente.
- **Gate por pulsación** *(desde RC2)* — al introducir notas a mano, lo que mantienes es lo que dura la nota.
- **Longitud fija** *(desde RC2)* — todas las notas que introduces a mano con la misma duración.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#micropasos)

### Vista Pattern Settings

*Cómo se llega:* Botón **Pattern Settings** con una pista elegida: primer / último paso, sync rate y dirección como siempre, más los pads 25-28 y el arpegiador (Shift).

- **Nudge** — rota el patrón para que empiece en otro paso.
- **Órdenes fractal y deconstruido** — recorren el patrón de otra forma sin cambiar sus notas.
- **Arpegiador** *(desde RC2)* — los acordes del patrón (y los que tocas) suenan nota a nota, con su orden y su resolución; en los drums, saltando de sample.
- **Dinámicas y random-mutate** (pad 25) — variaciones para que el patrón no suene siempre igual.

→ [Todo el detalle en la guía](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html#pattern-settings)
