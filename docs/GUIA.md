# Guía por vistas — CIRCUIT-HACKS (RC2.02)

Circuit Tracks con el firmware oficial 1.2.1 (build 4486) parcheado. Esta guía recorre las vistas del aparato y explica todo lo que se puede hacer en cada una. La [lista de características](MANUAL.md) resume cada función por temas.

## Vistas

**0. Introducción**

- [0.1 Cómo leer esta guía](#convenciones)
- [0.2 Botones que funcionan en todas las vistas](#botones)

**1. Setup**

- [1.1 Vista Setup](#setup)
- [1.2 Vista Advanced Setup](#advanced-setup)

**2. Sintes de stock (Synth 1 / 2)**

- [2.1 Vista de pista de Synth 1 / 2 (Note, Velocity, Gate)](#synth-nota)
- [2.2 Vista Scales y escala propia](#escalas)
- [2.3 Vista de la fuente del sinte](#synth-fuente)
- [2.4 Vista Preset de Synth 1 / 2](#synth-preset)

**3. Pistas MIDI (MIDI 1 / 2)**

- [3.1 Vista Preset de MIDI 1 / 2](#midi-preset)
- [3.2 Páginas de knobs del motor de MIDI 1 / 2](#midi-knobs)
- [3.3 Matriz de modulación](#midi-matriz)
- [3.4 Editor de CC de los macros MIDI (pad 25)](#midi-cc)
- [3.5 Vista del step-drummer](#step-drummer)
- [3.6 Modo muestra y selector de samples](#midi-muestra)

**4. Pattern Settings**

- [4.1 Vista Pattern Settings](#pattern-settings)
- [4.2 Vista Micro Step (pistas de notas)](#micropasos)
- [4.3 Vista de probabilidad (pistas de notas y drums)](#probabilidad)

**5. Drums**

- [5.1 Vista de pista de un drum (knobs)](#drum-pista)
- [5.2 Vista Preset de drums](#drum-preset)
- [5.3 Vista cromática y de escala de los drums](#drum-cromatica)

**6. Master FX**

- [6.1 Master FX](#master-fx)

**7. FX**

- [7.1 Vista FX](#vista-fx)

**8. Sidechain**

- [8.1 Vista Sidechain](#sidechain)

**9. Escenas y patterns**

- [9.1 Vista Patterns y cadenas de patrones](#patterns)
- [9.2 Vista Mixer y escenas](#mixer)

**10. Projects y packs**

- [10.1 Vista Projects](#projects)
- [10.2 Vista de packs](#packs)

**A. Apéndice**

- [A.1 Qué se guarda y dónde](#guardado)
- [A.2 MIDI de las funciones nuevas](#midi)
- [A.3 Instalar y volver atrás](#instalar)

## 0. Introducción

<a id="convenciones"></a>
### 0.1 Cómo leer esta guía

*Cómo se llega:* Cada capítulo es una vista del aparato: cómo se llega, qué hace cada pad, knob y botón, y los submenús que abre.

- **Pads 1-32** de arriba-izquierda a abajo-derecha: fila 1 = 1-8, fila 2 = 9-16, fila 3 = 17-24, fila 4 = 25-32.
- **Knobs K1-K4** arriba, **K5-K8** abajo. «**Shift + X**» = mantener Shift mientras se usa X; lo mismo con Clear y Duplicate.
- Lo que no aparece aquí funciona como en el aparato original (manual oficial de Novation).
- *(desde RC2)* = nuevo desde RC2 (no está en RC0.9 / RC0.9S). La versión más segura, RC2.02S (y las S anteriores), no escribe nada propio en la tarjeta: lo marcado «escribe en la tarjeta» no hace nada en ella (el LED de Save se pone rojo).
- *(desde RC2.02)* = nuevo en RC2.02 (no está en RC2.01).
- *(solo Beta 3.3)* = solo en la **Beta 3.3**, la versión de prueba con las funciones nuevas (no está en RC2.02).
- La **lista de características** (el manual anterior) resume cada función en una línea, por temas.

<a id="botones"></a>
### 0.2 Botones que funcionan en todas las vistas

*Cómo se llega:* Shift, Clear, Duplicate, Save y Octave ganan funciones según la vista; aquí, las que valen en casi todas.

**En esta vista**

- **Volver un knob a su valor o borrar lo grabado** — Clear + knob, sin buscar el valor a mano ni borrar el patrón entero.
- **Metrónomo y cuenta atrás** *(desde RC2)* — un compás de clics antes de grabar, para entrar a tiempo.
- **Teclado partido** *(desde RC2)* — los dos sintes a la vez, uno con cada mano.
- **Escala propia** *(desde RC2)* — escalas que el aparato no trae, también con periodos que no son la octava.
- **Atajos en amarillo** — con Shift pulsado, la vista enseña lo que ofrece.

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

## 1. Setup

<a id="setup"></a>
### 1.1 Vista Setup

*Cómo se llega:* Ábrela como en el original. Canales MIDI y opciones del aparato como siempre, más:

**En esta vista**

- **Canales compartidos (loopback interno)** — una pista MIDI toca un sinte o los drums del propio aparato.
- **Retornos por las tiras 3 / 4** — la reverb y el delay como canales del mixer.
- **Canales de Program Change** *(desde RC2)* — escucha y manda cambios de programa por canales propios.
- **Grabar los ruteos internos** *(desde RC2)* — lo que la pista MIDI toca en un sinte se graba también en él.

| Control | Qué hace |
|---|---|
| Botones de pista + pads 1-15 | Canal de cada pista; MIDI 1 / 2 pueden usar un canal que ya tenga otra (lo que mandan les llega por dentro: **loopback interno**). Synth 1 / 2 se eligen también si entraste desde su vista. |
| **Pad 16** | Canal 16 (proyecto y FX): recepción y envío de lo que no es Program Change. |
| **Pad 22 / 23** | El retorno de reverb pasa por la tira 3 / el de delay por la tira 4 del mixer (crema / melocotón). |
| **Pad 29 (PGM Rx)** *(desde RC2)* | Primer toque: los pads 1-16 enseñan el **canal de escucha** de los Program Change del proyecto (blanco); un pad lo elige; otra vez = encender / apagar. |
| **Pad 30 (PGM Tx)** *(desde RC2)* | Lo mismo con el **canal de salida**. Por defecto los dos son el 16. Lo recibido en el de escucha se reenvía por el de salida. |
| **Record** *(desde RC2)* | Amarillo = lo que una pista MIDI manda a un sinte por el canal compartido se graba también en ese sinte (cambios de escala u octava en tiempo real). Apagado por defecto; se apaga al reiniciar. |

- El patch flip sale siempre por el canal de su pista MIDI.

<a id="advanced-setup"></a>
### 1.2 Vista Advanced Setup

*Cómo se llega:* Ábrela como en el original. Además de sus ajustes de stock (compresor master, etc.):

**En esta vista**

- **MIDI Thru, Merge y Filter** *(desde RC2)* — el jack Thru puede mezclar el MIDI de entrada con el del aparato o filtrarlo.

- **Duplicate** = modo del jack MIDI Thru *(desde RC2)*: Thru (rojo tenue, el DIN In por hardware) → Out 2 (verde) → **Merge** (amarillo: el DIN In + el MIDI del aparato) → **Filter** (azul: el DIN In sin los canales en los que escucha el aparato). Sin SysEx en Merge / Filter. Se guarda en los ajustes.
- Los pads 22 / 23 no se iluminan aquí (allí no hacen nada).
- El ataque / release del compresor master se ajustan en la vista Sidechain, K7 / K8.

## 2. Sintes de stock (Synth 1 / 2)

<a id="synth-nota"></a>
### 2.1 Vista de pista de Synth 1 / 2 (Note, Velocity, Gate)

*Cómo se llega:* Pulsa **Synth 1** o **Synth 2**. Los pads tocan el sinte como siempre.

**En esta vista**

- **Vista de la fuente** — el sinte puede procesar una entrada de audio en lugar de su ruido.
- **Teclado partido** *(desde RC2)* — arriba un sinte y abajo el otro, cada uno con su escala, octava y velocity; *(desde RC2.02)* con cualquier par de pistas de notas.

- **Pulsar el mismo botón otra vez** (con su vista en pantalla) abre la **vista de la fuente** del sinte (2.3).
- **Synth 1 + Synth 2 a la vez** (mantén uno y pulsa el otro) abre el **teclado partido** *(desde RC2)*; *(desde RC2.02)* **cualquier par de pistas de notas** (Synth 1, Synth 2, MIDI 1, MIDI 2: mantén un botón y pulsa otro):
- las dos filas de arriba tocan la pista que mantuviste primero y las dos de abajo la otra, cada una con su escala, su octava, su velocity y sus colores (en RC2: arriba siempre Synth 1);
- los knobs y Octave son los de la primera pista que pulsaste; un botón de drum no abre el teclado partido;
- cualquier botón de pista o de vista lo cierra (las notas pulsadas se sueltan); Play, Record, Octave y Shift no.
- Los macro knobs funcionan como siempre; sus destinos se pueden editar en el aparato (vista de la fuente, pad 32).

<a id="escalas"></a>
### 2.2 Vista Scales y escala propia

*Cómo se llega:* Pulsa **Scales** como siempre (tónica y escala de stock); **Shift + Scales** para la escala propia.

**En esta vista**

- **Escala propia** *(desde RC2)* — hasta 7 notas sobre la tónica y un periodo libre (por ejemplo, una escala que se repite cada 7 semitonos). La usan los pads de las pistas de notas, el cuantizado y el random-mutate; se guarda con el proyecto.

- **Shift + Scales** abre la vista Scales con el **editor de la escala propia** *(desde RC2)*; con Shift pulsado, el botón Scales se ve amarillo. Scales otra vez, Shift + Scales u otra vista lo cierran.
- **El teclado del editor** son dos octavas en piano a partir de la **tónica** (la de la vista Scales, que se elige como siempre fuera del editor): fila 4 = teclas blancas de la primera octava (tónica, +2, +4, +5, +7, +9, +11, +12), fila 3 = sus negras; filas 2 / 1 = la segunda octava (+12 … +24).
- **Pulsar una tecla** la pone o la quita (hasta **7**). La más alta pulsada es el **periodo**: la tónica de la siguiente iteración (no tiene por qué ser la octava); las demás son las notas de la escala. Colores: tónica blanca, notas verdes, periodo naranja, teclas libres tenues.
- **En las pistas de notas** (Synth 1 / 2, MIDI 1 / 2) cada fila de pads es **una iteración**: sus notas y la nota del periodo al final, como las octavas de una escala de stock. Con **4 notas o menos**, **dos iteraciones por fila** (una en cada mitad). Octave ▼ / ▲ mueven una fila.
- La escala propia también vale para **iluminar las notas** de la secuencia, el cuantizado y el **random-mutate** (otra nota de la misma iteración).
- **Elegir una escala de stock** (pads 17-32 fuera del editor) apaga la escala propia; las teclas se guardan: volver al editor la enciende otra vez. Mientras está encendida, ninguna escala de stock se ve elegida.
- Se guarda **con el proyecto**; un proyecto nuevo empieza sin escala propia.

<a id="synth-fuente"></a>
### 2.3 Vista de la fuente del sinte

*Cómo se llega:* Con la vista de Synth 1 / 2 en pantalla, **pulsa su botón otra vez**. Cualquier botón la cierra.

**En esta vista**

- **Fuente del ruido** — cambia el ruido del patch por la entrada de audio 1 o 2 (normal o invertida): el filtro, las envolventes y los efectos del sinte procesan tu señal externa al ritmo de las notas.
- **Destinos de los macros** *(desde RC2)* — decide qué mueve cada macro knob (hasta 4 destinos por macro, con su tramo y su profundidad) sin pasar por Components.
- **Step-drummer del sinte** — secuencia los macros por pares de pasos: cada knob fija la posición de un macro en dos pasos del patrón.

### Pads 25-30: la fuente
| Pad | Fuente del ruido del sinte |
|---|---|
| 25 | Ruido (lo normal) |
| 26 | Entrada de audio 1 |
| 27 | Entrada de audio 2 |
| 28 | Entrada 1 con la fase invertida |
| 29 | Entrada 2 con la fase invertida |
| 30 | Abre el **step-drummer** del sinte (ver abajo) |

- El patch debe tener nivel de ruido (CC 56) para oír la fuente. La fuente se guarda con el proyecto.
- Si en Setup los retornos de reverb / delay van por las tiras 3 / 4, esa señal es la que entra al sinte.

### Pad 32: editor de los destinos de los macro knobs *(desde RC2)*
Cada macro knob tiene 4 ranuras; cada ranura, un destino, un tramo del recorrido (inicio y fin) y una profundidad.
1. **Pad 32** (verde azulado) = editor encendido; los knobs ya no mueven los macros.
2. **Gira un knob** para elegir su macro (LED blanco); el primer giro no cambia nada.
3. El knob cambia el campo actual; **Octave ▼ / ▲** = campo siguiente / anterior: ranura (1-4, amarillo) → inicio (verde) → fin (naranja) → destino (blanco = CC; azul claro, magenta, violeta = NRPN de los bancos 0, 1, 2) → profundidad (verde azulado positiva, rojo negativa). Los pads dibujan el número.
4. Cualquier pad suelta el macro; el pad 32 apaga el editor.
- El destino recorre primero los 31 parámetros con CC (por número) y luego los 39 que solo tienen NRPN. Los cambios suenan al momento; para dejarlos en el pack, guarda el patch (vista Preset).

### Pad 30: step-drummer del sinte
La vista del step-drummer es la misma que la de las pistas MIDI (3.5): pads 1-16 pasos, 17-24 = **macro 1-8** como destino, K1-K8 = los 8 pares de pasos. El valor de cada par es la posición del macro, escrita como automatización; un par vacío empieza en 0 *(desde RC2)* (antes, en la posición actual del macro).
- *(desde RC2)* Play y Record no cierran el step-drummer del sinte; si vas a otra vista, **pulsar Synth 1 / 2** lo vuelve a abrir (hasta que lo cierras con el pad 30).

<a id="synth-preset"></a>
### 2.4 Vista Preset de Synth 1 / 2

*Cómo se llega:* Pulsa **Preset** con Synth 1 / 2 elegido. Los pads eligen patch como siempre (4 páginas, 128 patches del pack).

**En esta vista**

- **El modo de voz a la vista** *(desde RC2)* — los patches mono, mono con glide y poly se distinguen por el color.
- **Guardar el patch** *(desde RC2)* — guarda en el pack el sonido tal como lo has dejado (el original solo guarda patches desde Components).
- **Intercambiar y copiar** — reordena los patches del pack o lleva uno a otro pack.

| Gesto | Qué hace |
|---|---|
| Colores de los patches *(desde RC2)* | **Azul oscuro** = mono, **lavanda** = mono con glide, color de la pista = poly; el elegido, más claro. |
| **Clear + pad**, **Clear + el mismo pad** antes de ~5 s *(desde RC2)* | **Guarda** en ese hueco el patch tal como suena (knobs, MIDI recibido, destinos de macro). El primer toque pregunta (parpadea en blanco); otro pad mueve la pregunta *(escribe en la tarjeta)*. |
| **Duplicate + pad A + pad B** (mismo pack) | Intercambia los dos patches. |
| **Duplicate + pad A**, cargar otro pack, **Duplicate + pad B** | Copia el patch A sobre B en el otro pack (el pack de A no cambia); B puede estar vacío *(escribe en la tarjeta)*. |

- El original no puede guardar patches desde el aparato. El patch guardado conserva el nombre del que estaba cargado.
- No funciona en el pack de la memoria interna (solo lectura para el mod): el LED de Save se pone rojo.

## 3. Pistas MIDI (MIDI 1 / 2)

<a id="midi-preset"></a>
### 3.1 Vista Preset de MIDI 1 / 2

*Cómo se llega:* Pulsa **MIDI 1** o **MIDI 2** y luego **Preset**. Además de las plantillas de stock, aquí vive el sinte propio de la pista.

**En esta vista**

- **Un sinte en cada pista MIDI** — MIDI 1 y 2 suenan en el propio aparato con su motor (entrada de línea procesada, oscilador, VA-drum o granular) y siguen mandando MIDI.
- **Secuenciador de efectos** — un motor que no suena: dispara efectos de Master FX en los pasos que elijas.
- **Patches del sinte propio** *(desde RC2)* — 64 sonidos por pack para esos motores, a un toque.
- **Matriz de modulación** *(desde RC2.02)* — ocho fuentes (velocity, nota, azar, LFO 2, envolvente 2, golpe de un drum, posición del patrón, azar por pasos) que mueven cualquier parámetro del motor.
- **Patch flip** — cada nota manda un cambio de programa: el aparato externo cambia de sonido paso a paso.
- **Editor de CC** — cambia qué CC manda cada knob de la plantilla sin Components.

### Pads
| Pad | Función |
|---|---|
| 1-5 | Página de knobs del motor: 1 VCA-VCF, 2 OSC 1 (granular en ese motor), 3 OSC 2, 4 secuenciables, 5 modulación. **Clear + el pad** *(desde RC2)*: los valores de esa página (con y sin Shift) a los iniciales. |
| 6 | *(desde RC2.02)* **Matriz de modulación** (azul claro; ver «Matriz de modulación»). **Clear + pad 6**: todas las fuentes apagadas. |
| 9-24 | **Patches del sinte propio** *(desde RC2)*: ver abajo. |
| 25 | **Editor de CC** de los macros MIDI (3.4). |
| 26 | **Patch flip**: cada nota de la pista sale como Program Change (por el canal de la pista; si ese canal es el de un sinte o los drums, también por dentro). Excluyente con el motor. |
| 27 | **Motor** de la pista: apagado → amarillo (entrada de línea) → verde (oscilador) → rojo (VA-drum) → magenta (granular) → cian (muestra *(desde RC2)*) → azul (secuenciador de efectos). |
| 28 | Uno / dos osciladores (oscilador y VA-drum). |
| 29 | Orden de la cadena: VCA → FX → filtro / filtro → VCA → FX (en el color de la página VCA-VCF *(desde RC2)*). |
| **Shift + 29** *(desde RC2)* | **Gate retrigger**: encendido (verde con Shift, por defecto) = cada nota nueva vuelve a disparar la envolvente; apagado (amarillo) = **legato**: con otras notas pulsadas, una nota nueva solo cambia la altura. Se guarda con el proyecto. |
| 30 | Abre el **step-drummer**; **Shift + pad 30** lo desactiva. |
| 31 | Solo en VA-drum: la velocity escala las envolventes de pitch y filtro. |

### Patches del sinte propio (pads 9-24) *(desde RC2)*
- 16 huecos por página; **Octave ▼ / ▲** = 4 páginas (64 huecos por pack, comunes a MIDI 1 y MIDI 2).
- **Tocar** = cargar (suena la tónica mientras mantienes el pad). **Clear + pad** dos veces = guardar. **Duplicate + A + B** = intercambiar; **Duplicate + A**, otro pack, **Duplicate + B** = copiar a otro pack (Duplicate en amarillo mientras hay uno esperando).
- Colores: melocotón tenue = con patch, brillante = el último usado, violeta = vacío.
- Un patch guarda el motor entero: motor elegido, osciladores, orden, todos los valores y el ajuste del step-drummer *(escribe en la tarjeta)*.
- **Clear + el botón de la pista** *(desde RC2)* devuelve todos los valores del motor a los iniciales (el motor elegido se queda).

### Los motores (pad 27)
- **Entrada de línea** (amarillo): la entrada de audio de la pista (línea 1 en MIDI 1, línea 2 en MIDI 2) pasa por el VCA-VCF; las notas de la pista lo disparan.
- **Oscilador** (verde): morph seno → triángulo → sierra → cuadrada, SHAPE, segundo oscilador (pad 28) con FM, ring, sync y modos bit a bit; dos notas = parafonía (con un oscilador, *(desde RC2)*: la última nota manda y al soltarla vuelve la anterior).
- **VA-drum** (rojo): VCA de un disparo, envolventes de decay para pitch (knob Sustain) y filtro (knob Release), ruido blanco (velocidad del LFO) y valores aleatorios en lugar del LFO.
- **Granular** (magenta): hasta 16 granos desde un sample del pack o la captura (página 2, capítulo siguiente).
- **Muestra** (cian) *(desde RC2)*: un sample del pack de un golpe a la altura de la nota (C3 = como se grabó), con sample flips por paso; se elige en la vista Note ampliada (ver «Modo muestra»).
- **Secuenciador de efectos** (azul): el step-drummer de la pista dispara los huecos de la fila inferior de Master FX (6.1).
- La pista sigue mandando su MIDI con cualquier motor.

<a id="midi-knobs"></a>
### 3.2 Páginas de knobs del motor de MIDI 1 / 2

*Cómo se llega:* Con el motor encendido, los pads 1-5 de la vista Preset eligen qué hacen los 8 knobs; Shift da una segunda capa.

**En esta vista**

- **VCA-VCF** — volumen y filtro con su envolvente y su LFO; con Shift, el tipo de filtro y el tipo de efecto.
- **Osciladores** — una forma de onda continua de seno a cuadrada y un segundo oscilador con FM, ring y sync.
- **Granular** — convierte un sample en texturas: granos que lo leen en otra posición, velocidad o dirección para congelarlo, estirarlo o trocearlo.
- **Página 4** — los 8 parámetros que se graban como automatización.

### Página 1 — VCA-VCF
| Knob | Solo | Con Shift |
|---|---|---|
| K1 | Ataque | Sustain |
| K2 | Release | Decay |
| K3 | Envolvente → nivel | LFO → nivel |
| K4 | Envolvente → filtro | LFO → filtro |
| K5 | Filtro | Tipo de filtro (DJ, LP 12, HP 12, BP, notch, LP 24, HP 24) |
| K6 | Resonancia | Gain del VCA (hasta +18 dB con saturación) |
| K7 | Velocidad del LFO | — |
| K8 | Cantidad de efecto | Tipo de efecto (suave, dura, plegado, wavefold, ring, comb, chorus) |

### Página 2 — OSC 1 (oscilador y VA-drum)
| Knob | Solo | Con Shift |
|---|---|---|
| K1 | TUNE | FINE |
| K2 | SHAPE | MIX OSC 1 ↔ OSC 2 |
| K3 | Envolvente → tono | BITSYNC |
| K4 | Envolvente → forma | — |
| K5 | LFO → tono | — |
| K6 | LFO → forma | — |
| K7 | WAVE (morph) | — |
| K8 | LFO → morph | Envolvente → morph |

### Página 2 — granular
| Knob | Solo | Con Shift |
|---|---|---|
| K1 | Tono ±24 st | Fino ±1 st |
| K2 | Posición en el sample | Dispersión de la posición |
| K3 | Scan (centro congelado) | Probabilidad de grano al revés |
| K4 | Tamaño del grano 5-500 ms | Dispersión del tono |
| K5 | Densidad 1-16 granos | Ventana |
| K6 | Zona del scan | Modo de nota: tono / slicer / stretch *(desde RC2)* |
| K7 | LFO → posición | LFO → tamaño |
| K8 | Envolvente → posición | Fuente: la captura o el sample de un drum *(desde RC2)* |

- **Modo de nota (Shift + K6):** **tono** = las notas cambian la altura de los granos; **slicer** = el sample se parte en 16 trozos y cada nota toca uno (la nota 36 el primero, cada nota más arriba el siguiente; cada 16 notas vuelve a empezar); **stretch** *(desde RC2)* = las notas cambian la altura y el tramo desde la posición (K2) hasta el final dura **K3 pasos** (1-64) a cualquier tempo, sin cambiar la altura, alineado con el inicio del transporte; parado, la posición se queda congelada.

### Páginas 3-5
- **Página 3 (OSC 2):** *(desde RC2)*: los ocho valores sin Shift, según la serigrafía: K1 Oscillator TUNE 2, K2 Osc mod SHAPE 2, K3 Amp envelope MIX OSC 1 ↔ OSC 2, K4 Filter envelope FM, K5 Filter frequency FINE 2, K6 Resonance BITSYNC, K7 Modulation WAVE 2, K8 FX RING (en RC0.9: K1 TUNE 2 / FINE 2, K2 SHAPE 2 / FM, Shift + K3 RING, K7 WAVE 2).
- **Página 4:** los 8 valores secuenciables: con Record + Play sus movimientos se graban en el patrón (TUNE, Release, Env → nivel, Env → filtro, Filtro, Resonancia, Velocidad del LFO, Efecto).
- **Página 5:** ADSR arriba, LFO abajo. *(desde RC2)*: **Shift + K8 = forma del LFO**: diente de sierra inverso (naranja, la de siempre), diente de sierra (magenta), triángulo (verde), cuadrada (roja), seno (cian), sample & hold (blanco: un valor al azar en cada vuelta); *(desde RC2.02)*: **sample & hold suavizado** (violeta: se desliza de un valor al azar al siguiente durante cada vuelta), y **sin forma guardada (un proyecto nuevo o de antes) el triángulo** (en RC2: el diente de sierra inverso; un patch propio de antes de las formas sigue cargando el diente de sierra inverso). Un paso cada 4 clics, el LED de K8 con Shift en su color. Se guarda con el proyecto y en el patch propio; con el VA-drum el LFO sigue siendo su ruido.
- **Página 6** *(desde RC2.02)*: la matriz de modulación (capítulo siguiente).
- Los knobs de tipo se ven de color (tipo) y brillo (posición dentro del tipo). Todo sale y entra por CC / NRPN (A.2 y la referencia MIDI).

<a id="midi-matriz"></a>
### 3.3 Matriz de modulación

*Cómo se llega:* *(desde RC2.02)* MIDI 1 / 2 con el motor encendido: vista Preset, **pad 6**. Los 8 knobs pasan a ser 8 fuentes de modulación.

| Knob | Fuente | Con Shift |
|---|---|---|
| K1 | Velocity de la nota | — |
| K2 | Nota (C3 = 0; una octava = un cuarto del recorrido) | — |
| K3 | Azar: un valor nuevo en cada nota | — |
| K4 | LFO 2 | Forma × velocidad: triángulo (verde, la inicial), diente de sierra (magenta), cuadrada (rojo), sample & hold (blanco: escalones), sample & hold suavizado (violeta: deslizándose); los colores del LFO del motor; en cada forma, de 0,05 a 20 Hz |
| K5 | Envolvente 2: ataque y caída desde cada nota | Ataque × caída: ataque 0 (blanco), corto (azul claro), medio (verde azulado), largo (azul); en cada uno, la caída de 20 ms a 4 s |
| K6 | Golpe de un drum: una caída desde cada golpe | Drum 1-4 (naranja, amarillo, violeta, verde azulado) × su caída |
| K7 | Posición en el patrón: de 0 en el primer paso al máximo en el último | — |
| K8 | Azar por pasos: un valor nuevo cada N pasos del secuenciador | N = 1, 2, 4, 8 o 16 pasos |

- **La posición del knob es el destino y la cantidad.** Del todo a la izquierda = apagado. Al girar a la derecha se pasa por **todos los parámetros de las páginas de knobs** (33: los de la página 1, luego los de la 2, la 3 y los de la 5 que no salen antes), cada uno con un tramo: dentro del tramo la cantidad crece de 1/16 a entera; al pasar al tramo siguiente cambia el destino y la cantidad vuelve a empezar.
- **Knobs lentos:** dos clics por paso, 16 pasos por destino.
- **El color del LED es el de la página del destino** (los colores de los pads 1-5: naranja VCA-VCF, verde OSC 1, verde azulado OSC 2), el **brillo** la cantidad; apagado = sin destino.
- **Mientras giras una fuente** (y 1,5 s después), los pads enseñan dónde vive su destino: el pad de su página brilla y los pads 9-16 / 17-24 son los K1-K8 / Shift + K1-K8 de esa página (tenues los que tienen un parámetro, brillante el destino). Mientras se ven, los pads 9-24 no cargan patches.
- **Cantidad entera** = la fuente entera recorre todo el rango del parámetro. Las fuentes bipolares (nota, azar, LFO 2, azar por pasos) suben y bajan; las demás solo suben. El valor guardado del parámetro no cambia: la matriz se suma al enviarlo.
- Varias fuentes pueden ir al mismo destino (se suman). TUNE se mueve en semitonos y FINE en fracciones; con el motor granular, sus rangos; en el modo muestra el parámetro del sample elige sample (de la captura al 64) y solo TUNE cambia la altura.
- **Clear + knob** = esa fuente apagada; **Clear + Shift + knob** = su parámetro al valor inicial; **Clear + pad 6** = todas apagadas.
- **Se guarda con los patches del sinte propio** (pads 9-24: Clear + pad dos veces, también al intercambiarlos o copiarlos entre packs); un patch guardado antes la carga apagada. No se guarda con el proyecto ni al apagar el aparato. No tiene CC / NRPN.
- Las modulaciones llegan al motor unas 100-250 veces por segundo, repartidas entre todo lo que se mueve en la pista: varias fuentes rápidas a la vez se actualizan más despacio.

<a id="midi-cc"></a>
### 3.4 Editor de CC de los macros MIDI (pad 25)

*Cómo se llega:* Vista Preset de MIDI 1 / 2, **pad 25**: cambia desde el aparato qué CC / NRPN manda cada macro knob de la plantilla.

**En esta vista**

- **Controlar otro aparato** — elige el número de CC (o NRPN) y el recorrido de cada knob de la plantilla, y guárdalo en ella.

1. **Pad 25** (se enciende). 2. **Mueve un knob**: queda elegido y su número se dibuja con los pads.
3. **Octave ▼ / ▲**: campo siguiente / anterior. 4. **Gira el knob** para cambiar el valor.
5. **Guardar:** pad 26, o Octave ▼ hasta el paso de guardar (pad 26 y Save parpadean) y Octave ▼ otra vez.
6. **Descartar:** cualquier botón de vista, el pad 25 o un pad de plantilla.

| Número del primer campo | Tipo | Campos |
|---|---|---|
| cualquier otro | CC | número, inicio, fin |
| 99, 98 o 6 | NRPN de 7 bits | número, MSB, LSB, inicio, fin |
| 38 | NRPN de 14 bits | número, MSB, LSB, inicio (MSB, LSB), fin (MSB, LSB) |

<a id="step-drummer"></a>
### 3.5 Vista del step-drummer

*Cómo se llega:* MIDI 1 / 2: vista Preset con el motor encendido, **pad 30**. Synth 1 / 2: vista de la fuente, **pad 30**. Secuencia por pares de pasos sobre el patrón.

**En esta vista**

- **Parámetros por pares de pasos** — los 8 knobs son 8 pares de pasos del patrón: cada uno mueve un destino (tono, forma, FM, filtro…) solo en esos pasos, para melodías, acentos o cambios de timbre sin automatizar a mano.
- **El LED dice cuánto** *(desde RC2)* — tenue sin modulación, más brillante cuanto más se aleja.
- **Segunda página con destino propio** *(desde RC2)* — la página de velocity mueve otro destino a la vez.
- **Toggle pitch-vel** *(desde RC2)* — la página 1 transpone las notas por grados de la escala y la 2 marca su velocity: una melodía a partir de un solo patrón de notas.
- **En tiempo real** — con Record, tocar un paso lo graba.
- **Secuenciador de efectos** — con ese motor, cada par elige qué hueco de Master FX suena.

| Control | Función |
|---|---|
| Pads 1-16 | Los 16 pasos de la mitad mostrada: brillante = con nota, blanco = el que suena. Tocar = escuchar; **Shift + tocar** = poner / quitar nota. |
| Pads 17-24 | Página pitch: destino de la fila de pitch (MIDI: tono, OSC 2, WAVE, FM, MIX, env → filtro, SHAPE, decay) / macro 1-8 (sintes). Página velocity: **destino de la página 2** *(desde RC2)* (el mismo pad otra vez = ninguno). |
| Pad 32 | **Toggle pitch-vel** *(desde RC2)* (verde brillante = activado): además de su destino, la página pitch transpone las notas y la página velocity cambia la velocity. |
| K1-K8 | Los 8 pares de pasos (el que suena, blanco). |
| Octave ▲ / ▼ | Página pitch / velocity. |
| 1-16 / 17-32 | La otra mitad del patrón. |

- El valor del par desplaza el destino desde el centro (64 = sin cambio): suma o resta al valor que tenga el parámetro en la página del motor. *(desde RC2)* **El LED del knob muestra la cantidad**: tenue en el centro, más brillante cuanto más se aleja, hacia arriba o hacia abajo.
- Cada paso conserva la altura de su primera nota.
- *(desde RC2)* **Página velocity con destino:** los knobs escriben su valor en el par (MIDI: desde el centro, 64; sintes: desde 0), sin tocar la velocity si el toggle está apagado. Sin destino ni toggle, la página velocity no hace nada. En MIDI la página 2 usa el carril de automatización de REL: con el step-drummer activado, REL no se reproduce ni se graba.
- *(desde RC2)* **Toggle pitch-vel:** cada nota de la pista sube / baja **un grado de la escala** del proyecto (la de stock o la propia) **cada 8 pasos del knob**: MIDI desde el centro (−8 … +8 grados), sintes desde 0 (0 … +16), entre las notas 0 y 127; también al escuchar un paso. Con el toggle, los destinos de tono de la página pitch (tono de los dos osciladores / del OSC 2) ya no mueven el sinte propio: lo hace la nota. La velocity sigue a la página velocity.
- *(desde RC2)* En MIDI el pad 30 se ve **tenue** con el step-drummer desactivado y **brillante** activado (antes, apagado / tenue).
- Con **Record**, tocar un paso lo graba en el paso que suena (tiempo real).
- Con el motor en **secuenciador de efectos** (azul), cada knob elige un hueco de la fila inferior de Master FX: 0 nada, 1-5 pads 26-30, 6 el pad 31, y al final **random** *(desde RC2)* (LED blanco: uno al azar entre los que tienen efecto). Avanza despacio (un hueco cada ~48 pasos de giro). Un hueco sin efecto asignado no hace nada.

<a id="midi-muestra"></a>
### 3.6 Modo muestra y selector de samples

*Cómo se llega:* *(desde RC2)* MIDI 1 / 2 con el motor en **muestra** (pad 27 cian, tras el granular): **Note dos veces** (vista Note ampliada). La pista toca un sample del pack de un golpe, a la altura de cada nota.

**En esta vista**

- **Drums con altura en una pista MIDI** — cualquier sample del pack suena a la altura de cada nota, como en una caja de ritmos con samples afinables.
- **Un sample distinto por paso** — el sample flip cambia de sample paso a paso sin otra pista; se graba también en vivo.

| Control | Función |
|---|---|
| Pads 17-32 | 16 samples del pack: tocar = el sample de la pista (cian) y suena; los demás tenues. |
| Octave ▼ / ▲ | Página siguiente / anterior de samples (4 páginas = los 64 del pack; encendido si hay más en ese sentido). |
| Pads 1-16 | Los 16 pasos de la mitad mostrada: melocotón = con sample flip, cian tenue (el fondo) = sin, blanco = el que suena. **Mantener un paso + tocar un sample** = su flip (el paso verde, su sample amarillo); **Clear + paso** = quitarlo. |
| 1-16 / 17-32 | La otra mitad del patrón. |

- **La altura:** C3 (nota 60) = el sample como se grabó; una octava arriba = el doble de rápido. Las notas vienen de la vista Note normal, el step-drummer o el MIDI de entrada.
- **Un golpe:** el VCA se queda abierto y el sample suena hasta el final; cada nota nueva lo vuelve a empezar (una voz por pista). Filtro, efecto y LFO de las páginas del motor siguen.
- **En vivo:** con **Record + Play**, tocar un sample graba una nota 60 en el paso que suena con su flip.
- El sample de la pista es la misma fuente que la del granular (Shift + K8 en su página; la captura se elige allí).
- Los flips van en el carril de la automatización de nivel de la pista (Mixer): un flip sustituye el nivel grabado en su paso; grabar el nivel encima borra esos flips.

## 4. Pattern Settings

<a id="pattern-settings"></a>
### 4.1 Vista Pattern Settings

*Cómo se llega:* Botón **Pattern Settings** con una pista elegida: primer / último paso, sync rate y dirección como siempre, más los pads 25-28 y el arpegiador (Shift).

**En esta vista**

- **Nudge** — rota el patrón para que empiece en otro paso.
- **Órdenes fractal y deconstruido** — recorren el patrón de otra forma sin cambiar sus notas.
- **Arpegiador** *(desde RC2)* — los acordes del patrón (y los que tocas) suenan nota a nota, con su orden y su resolución; en los drums, saltando de sample.
- **Dinámicas y random-mutate** (pad 25) — variaciones para que el patrón no suene siempre igual.

| Pad | Función |
|---|---|
| 1-16 | Primer / último paso (stock). |
| 17-24 | Sync rate (stock). |
| 25 | Abre la vista de probabilidad en **modo 2** (dinámicas y random-mutate; en los drums también *(desde RC2)*). **Clear + pad 25** (pistas de notas): borra las dinámicas y el random-mutate de todos los pasos del patrón; la frecuencia se queda *(desde RC2)*. |
| 26 | **Nudge** (naranja): el primer paso elegido pasa a ser el paso 1; lo de delante va al final (pasos y automatización, sobre 16 o 32). |
| 27 | Orden **fractal**: 1 · 1 2 · 1 2 3 · … hasta el último paso. |
| 28 | Orden **deconstruido**: las diagonales de la rejilla (1 6 11 16 · 2 7 12 13 · 3 8 9 14 · 4 5 10 15). |
| 29-32 | Dirección de stock; excluyente con 27 / 28. |

- Nudge y órdenes también en los drums. El orden se guarda con el patrón; Clear del patrón lo quita. *(desde RC2)*

### Arpegiador (pistas de notas) *(desde RC2)*
Con **Shift** pulsado, los pads del arpegiador conservan sus colores de Pattern Settings y lo elegido se ve en verde:

| Gesto | Función |
|---|---|
| **Shift + pad 25** | Arpegiador del patrón que suena en la pista: encendido / apagado. Sin Shift, el pad 25 se ve verde mientras está encendido (y sigue abriendo el modo 2). |
| **Shift + pads 27-32** | Orden del arpegio, independiente de la dirección del patrón: fractal, deconstruido, arriba, abajo, ping-pong, aleatorio. |
| **Shift + pads 17-24** | **Resolución** del arpegio, distinta del sync rate de la pista, en el mismo orden que los pads de sync rate (más lenta a la izquierda): 1/4, 1/4T, 1/8, 1/8T, 1/16, 1/16T, 1/32, 1/32T. El mismo pad otra vez = la de la pista (ningún pad verde). |

- **Secuencia:** cuando en un paso empiezan dos notas o más, suenan de una en una (a la resolución del arpegio), en el orden elegido sobre las notas ordenadas por altura, mientras dura la nota más larga del acorde. Cada nota dura **su propio gate, como mucho un paso de arpegio** (y lo que queda del acorde) y lleva su velocity: un acorde grabado manteniendo las notas suena arpegiado, uno introducido con notas cortas, staccato.
- **Entrada:** la primera nota suena como siempre; al mantener otra a la vez empieza el arpegio de las notas mantenidas, una por paso de arpegio (con el transporte parado, al tempo del proyecto), hasta soltarlas todas; cada nota dura un paso de arpegio. **Con Record se graba el acorde**, no las notas sueltas: el arpegio lo toca después la secuencia.
- Se guarda con el proyecto, por pista y patrón.

### Arpegiador de los drums *(desde RC2)*
Los mismos gestos (**Shift + pad 25 / 27-32 / 17-24**) en el Pattern Settings de un drum encienden su arpegiador para el patrón que suena, con su orden y su resolución. En la **vista Preset del drum**, el primer sample mantenido es el de siempre; **al mantener otro a la vez empieza el arpegio de los samples mantenidos**: el drum va saltando de sample en sample (en el orden elegido, sobre los samples ordenados por número), con la velocity de su pad. En marcha va a la rejilla del drum; parado, al tempo del proyecto. Sigue mientras quede alguno mantenido; al soltarlos todos, el drum vuelve a su sample elegido. **Con Record** (en marcha) cada golpe se graba en el patrón: su micropaso, su sample como sample flip del paso (uno por paso: queda el último) y, en un paso vacío, su velocity.

<a id="micropasos"></a>
### 4.2 Vista Micro Step (pistas de notas)

*Cómo se llega:* Pulsa **Gate dos veces** con una pista de notas elegida (Synth 1 / 2, MIDI 1 / 2).

**En esta vista**

- **Micropasos y Tie (de stock)** — coloca cada nota fuera de la rejilla y enlázala con el paso siguiente.
- **Gate por pulsación** *(desde RC2)* — al introducir notas a mano, lo que mantienes es lo que dura la nota.
- **Longitud fija** *(desde RC2)* — todas las notas que introduces a mano con la misma duración.

- **Lo de stock:** pads 17-22 = los 6 micropasos del paso elegido; **pad 24 = Tie** (un toggle: enlaza las notas elegidas con el paso siguiente); pads 25-30 = las notas del paso: tocar una la elige (a ella se aplican el micropaso y el Tie) y la hace sonar.
- **Un micropaso por nota (de stock):** cada nota guarda una sola posición, así que tocar otro micropaso mueve la nota elegida; no se pueden encender dos a la vez. Para varias en el mismo paso, pon varias notas. En los drums sí se encienden varios micropasos (repeticiones).
- **Gate una vez** es la vista Gate (pads 17-32 = la duración): ahí los pads 31 / 32 son los de stock.
- **Pad 32 = gate por pulsación** *(desde RC2)* de la pista (verde = encendido, tenue = apagado; se guarda con el proyecto): al **introducir notas a mano** (un paso mantenido + un pad de nota, o una nota mantenida + un pad de paso), **el tiempo que mantienes el pad es el gate** de esa nota, al tempo del proyecto y al sync rate de la pista (de 1 micropaso a 16 pasos). Termina al soltar el primero de los dos pads. Apagado: el gate de stock.
- **Pad 31 = longitud fija** *(desde RC2)* de la pista (naranja = encendida): con los dos apagados, abre el **selector** (pads 17-32 = 1 … 16 pasos, como la vista Gate) y **elegir una longitud la enciende** (y cierra el selector). Con ella, toda nota introducida a mano (no la grabada en vivo) lleva ese gate.
- **Los dos toggles** *(desde RC2)*: con uno encendido, **pulsarlo otra vez lo apaga** (sin abrir nada); **pulsar el otro** apaga el primero y enciende el nuevo (el pad 31, abriendo su selector).
- Esos gates los usa también el arpegiador: cada nota del acorde dura el suyo.

<a id="probabilidad"></a>
### 4.3 Vista de probabilidad (pistas de notas y drums)

*Cómo se llega:* **Shift + Pattern Settings** (modo de stock), **Pattern Settings dos veces** (modo 1) o el **pad 25** de Pattern Settings (modo 2). Mantén un paso con notas y toca un pad de las filas 3-4.

**En esta vista**

- **Probabilidad (de stock)** — que un paso suene solo a veces.
- **Frecuencia** *(desde RC2)* — que un paso suene una de cada n vueltas: variaciones que vuelven cada 2, 4 u 8 vueltas.
- **Dinámicas** *(desde RC2)* — pequeñas variaciones de velocity y de posición: un patrón más humano.
- **Random-mutate** *(desde RC2)* — notas que saltan de octava o a otra nota de la escala; en los drums, a otro sample.

| Modo | Fila 3 | Fila 4 |
|---|---|---|
| Stock (Shift + Pattern Settings) | Probabilidad del paso | **Random-mutate** *(desde RC2)* |
| Modo 1 (Pattern Settings dos veces) | Probabilidad del paso | **Frecuencia**: el paso suena en la última de cada n vueltas (1-8), amarillo *(desde RC2)* |
| Modo 2 (pad 25) | **Dinámicas** aleatorias *(desde RC2)* | Random-mutate *(desde RC2)* |

### Random-mutate (fila 4)
| Pad | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 |
|---|---|---|---|---|---|---|---|---|
| Octava | — | 6 % | — | 6 % | — | 12 % | — | 25 % |
| Escala | — | — | 6 % | 6 % | 12 % | — | 25 % | 50 % |

- Escala = otra nota de la escala en la misma octava; octava = una arriba o abajo. Cada nota de un acorde se sortea aparte. Sin Record cambia solo esa vez; con Record se escribe (la secuencia deriva). Las ligadas no cambian.

### Dinámicas (fila 3, modo 2)
| Pad | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Micropasos | — | ±2 | ±2 | — | −1 a +3 | −1 a +3 | — | — |
| Velocity | — | — | 0 a +32 | 0 a +32 | 0 a +32 | — | ±32 | −32 a +64 |

- Con Record y el modo 2 en pantalla, lo que suena (nota mutada, dinámica) se escribe en el patrón. Todo se guarda con el paso.

### En los drums *(desde RC2)*
La misma vista para un drum: **Pattern Settings dos veces** (modo 1) o el **pad 25** de su Pattern Settings (modo 2, melocotón; verde si su arpegiador está encendido). Elige un paso con golpe (pads 1-16) y toca un pad de las filas 3-4.

| Modo | Fila 3 | Fila 4 |
|---|---|---|
| Modo 1 | Probabilidad del paso (stock) | **Frecuencia** (1-8), amarillo |
| Modo 2 | **Dinámicas** (los mismos 8 niveles) | Pads 25-28: **random-mutate del sample** |

| Pad | 25 | 26 | 27 | 28 |
|---|---|---|---|---|
| Random-mutate | — | 25 % ±1 (el sample de al lado en su fila de 8) | 25 % ±8 (el de la misma columna en otra fila) | 12 % de cada uno |

- Las dinámicas solo retrasan el golpe dentro de su paso (un drum no puede sonar antes). El mutate parte del sample flip del paso, o del sample elegido; no se graba.
- Los valores van en bytes del patrón que el stock no usa (viajan al duplicarlo y con Nudge); la primera vez que pones uno se limpian esos bytes en los 32 patrones de drum del proyecto (un pack de fábrica trae basura ahí).

## 5. Drums

<a id="drum-pista"></a>
### 5.1 Vista de pista de un drum (knobs)

*Cómo se llega:* Pulsa **Drum 1-4**. Cada knob hace lo que dice su etiqueta, con una segunda capa en Shift.

**En esta vista**

- **Moldear cada drum** — tono exacto, ring mod, ataque y decay, inicio y corte del sample, filtro con varios modos, LFO y distorsión de varios tipos: de un sample salen muchos sonidos.
- **Todo neutro = el original** — con los knobs nuevos en su punto neutro, el sample suena como en el Circuit original.
- **Volver a empezar** *(desde RC2)* — Clear + el botón del drum deja todos sus knobs por defecto.

| Knob | Solo | Con Shift |
|---|---|---|
| K1 Oscillator | Pitch (*(desde RC2)*: el de stock, continuo como el original; los pads de la vista cromática transponen encima) | Cantidad de la envolvente de tono |
| K2 Osc mod | Frecuencia del ring mod | Cantidad del ring mod |
| K3 Amp envelope | **Izquierda: decay** (el de stock). Pasado el máximo, **derecha: ataque** (fundido de entrada, hasta 1 s). Centro neutro. *(desde RC2)* | **Izquierda: inicio** del sample; **derecha: corte** desde el final (hasta 120/128 cada uno). Centro = el sample entero. *(desde RC2)* |
| K4 Filter envelope | Envolvente → corte | Forma de la envolvente |
| K5 Filter frequency | Filtro / EQ (por defecto, el EQ tilt de stock) | **Modo de filtro**: EQ tilt de stock, paso banda, notch, comb, DJ |
| K6 Resonance | Resonancia | — |
| K7 Modulation | Cantidad del LFO | Velocidad del LFO |
| K8 FX | Distorsión; a la izquierda de 0, **bitcrush** | **Tipo de distorsión**: stock, suave, dura, plegada |

- **K3:** girando a la izquierda el ataque vuelve a 0 antes de que baje el decay; con Shift, uno de los dos (inicio o corte) vuelve a 0 antes de que se mueva el otro. LED: ataque en blanco; con Shift, inicio en el color del drum, corte en blanco.
- **Clear + K3 a la derecha** pone a 0 ataque, inicio y corte; **Clear + K8 a la derecha** quita también el bitcrush *(desde RC2)*. Clear + knob restablece las dos capas en los demás.
- **Clear + el botón del drum** *(desde RC2)* (con una de sus vistas en pantalla): los ocho knobs del drum, con su capa Shift, a sus valores por defecto.
- Con todo en neutro un sample suena como en el original. Todo se guarda con el proyecto y tiene NRPN.
- **Sidechain entre drums:** Shift + FX y Octave ▼ (8.1).

<a id="drum-preset"></a>
### 5.2 Vista Preset de drums

*Cómo se llega:* Pulsa **Preset** con un drum elegido. Los pads eligen el sample como siempre (Shift + pad = elegir sin que suene).

**En esta vista**

- **La captura como drum** — graba lo que suena (Master FX) y úsalo como sample de un drum; al guardar el proyecto queda en el pack.
- **Intercambiar y copiar samples** — reordena los samples o trae uno de otro pack.
- **Arpegio de samples** *(desde RC2)* — al mantener varios samples, el drum salta de uno a otro.

| Gesto | Qué hace |
|---|---|
| **Clear + pad**, **Clear + el mismo pad** | **Sustituye** ese sample por la captura de Master FX. Volátil hasta guardar: al guardar se escribe en el pack si cabe en la memoria de samples. |
| **Duplicate + pad A + pad B** (mismo pack) | Intercambia los dos samples (ficheros y tabla); suena al instante. |
| **Preset otra vez** *(desde RC2)* | Vista cromática / de escala del drum encendida / apagada (lo mismo que Shift + Preset). |
| **Varios pads mantenidos** *(desde RC2)* | Con el arpegiador del drum encendido (Pattern Settings, Shift + pad 25): el arpegio de los samples mantenidos (capítulo de Pattern Settings). |
| **Duplicate + pad A**, cargar otro pack, **Duplicate + pad B** | Copia el sample A sobre B (B puede estar vacío). Va al sitio de B si cabe; si no, a la memoria libre de importación. Nunca pisa un sample que suena. |
| **Shift + Preset** | Vista cromática / de escala (5.3). |

- Duplicate se ilumina en esta vista. Escribe en la tarjeta: no está en las versiones «S» ni en el pack de la memoria interna.

<a id="drum-cromatica"></a>
### 5.3 Vista cromática y de escala de los drums

*Cómo se llega:* **Shift + Preset** con un drum elegido. Los pads tocan el sample transpuesto según la escala.

**En esta vista**

- **Un drum como teclado** — el sample transpuesto en la escala del proyecto.
- **Rollers** *(desde RC2)* — repite el drum en los micropasos que mantengas: redobles y ratchets en directo, también parado, y grabados con Record.

- Tres filas de notas en la escala y la tónica de la vista Scales.
- **K1** = sesgo de tono en semitonos; **Shift + K1** = afinación fina en cents.
- Grabando, cada tono se graba solo en su paso. *(desde RC2)*: los pads transponen en semitonos sobre el pitch de K1 y, grabando, quedan en su paso dentro del carril de pitch del drum (un paso guarda un giro de K1 o una nota cromática); Clear + K1 a la izquierda (sostenido) borra los dos.
- **Vista Note de los drums:** los pads 25-28 repiten los cuadros de los drums 4 … 1.
- **Rollers de micropasos** *(desde RC2)* en las filas 1-3 de la vista Note de los drums: cada columna es el drum de su cuadro de abajo (columnas 1-4 = drums 4-1, columnas 5-8 = drums 1-4), en su color tenue. La columna izquierda de un drum son sus micropasos 1-3 (filas 1-3) y la derecha los 4-6: el drum 1 = pads 4, 12, 20 y 5, 13, 21. **Mientras se mantienen** (uno o varios, de uno o varios drums), el drum suena en **cada paso** en esos micropasos (con la velocity del paso, o 100 si el paso está vacío); se encienden mientras se mantienen. **Con el transporte parado** *(desde RC2)* también: al tempo del proyecto, empezando al pulsar el primero (velocity 100). **Con Record** sus golpes también se graban en el patrón (el micropaso, y velocity 100 en un paso vacío).

## 6. Master FX

<a id="master-fx"></a>
### 6.1 Master FX

*Cómo se llega:* **Mixer** y **Mixer** otra vez. Efectos sobre la salida master, el song pointer, el sample capturado y la fila de efectos asignables. Cualquier otro botón de vista sale.

**En esta vista**

- **Efectos en directo sobre todo el master** — Gater, Auto-Filter, Digitise, Phaser, Glitch y gesto mecánico *(desde RC2)*: mientras mantienes o fijados.
- **Song pointer** — repite o hace bucle de partes del patrón en directo.
- **Captura** — graba hasta 3,5 s de lo que suena para tocarlo, ponerlo en un hueco o usarlo como drum.
- **Huecos** — un efecto con sus ajustes a un toque; el secuenciador de efectos los dispara.
- **Por proyecto** *(desde RC2)* — cada proyecto recuerda sus ajustes de Master FX.

### Pads
| Pad | Función | K1-K4 al pulsarlo |
|---|---|---|
| 1 | Gater | división, profundidad, ancho, suavizado |
| 2 / 3 | Auto-Filter paso bajo / alto | velocidad, profundidad, resonancia, centro |
| 4 | Digitise | muestreo, bits; **K3 = envío momentáneo al delay** mientras mantienes el pad, **K4 = envolvente de la cantidad** *(desde RC2)* |
| 5 | Phaser | velocidad, profundidad, realimentación, mezcla |
| 6 | **Glitch** *(desde RC2)* (en RC0.9, el Vinyl) | Glitch: velocidad, repetición, retraso, caos / sobrecarga |
| 7 | **Sample capturado**: tocar | pitch, modo (one-shot / gate / loop), start, end |
| 8 | Apagar todo lo fijado (efectos, song pointer, sample) y bypass | — |
| 9-24 | **Song pointer**: pasos 1-16 | — |
| 25 | (stock) | — |
| 26-30 | **Huecos asignables** | los del efecto asignado |
| 31 | **Gesto mecánico** *(desde RC2)* (en RC0.9, el Glitch) | gesto: movimientos, tipo, tiempo de parada, tiempo de arranque |
| 32 | **Grabar** la captura | — |

### Efectos (pads 1-6)
- **Mantener** = activo; **Shift + pad** = fijado; tocarlo otra vez lo suelta. El brillo de los LEDs de los knobs enseña el valor.
- **Clear + knob a la derecha** = valor por defecto; con Clear pulsado los knobs que están en su valor por defecto se ven lavanda (Master FX no tiene automatización: no hay rojo).
- **Por sesión** *(desde RC2)*: los 20 knobs de los efectos, la asignación de los huecos y el compresor se guardan con cada proyecto.

### Song pointer (pads 9-24)
- **Un paso mantenido** = retrigger; **dos** = frase momentánea entre ellos; **Shift + dos** = frase fijada (pad 9 blanco; tocarlo la quita).
- **Modo frase:** Shift + paso = inicio (fin 16); un toque = el fin; Shift + otro = nuevo inicio; Shift + el inicio o el pad 9 = salir.

### Sample capturado (pads 7 y 32)
- **Pad 32:** mantener = graba mientras lo mantienes (hasta 3,46 s); toque corto = hasta el siguiente; **Shift + pad 32** = armado (graba el compás siguiente; parado, desde Play). La captura graba la salida sin los efectos de Master FX; el sample que suena sí pasa por ellos. **Desde RC2.01** la captura y el sample van antes del filtro master: el filtro le afecta al sonar y la captura no lo lleva.
- **Pad 7:** tocar; **Shift + pad 7** = bucle enganchado hasta volver a pulsarlo. El modo loop (K2 azul) suena solo mientras mantienes.
- Se puede asignar a un hueco (pad 7 + pad de abajo) y sustituir a un drum (vista Preset de drums). Al guardar el proyecto se guarda en el pack si cabe.

### Fila inferior (pads 26-31)
- **Asignar:** mantén un efecto de arriba (1-6), el pad 7 o el 31 y toca un hueco: guarda el efecto con una copia de sus parámetros.
- **Tocar el hueco** = activo mientras lo mantienes; **Shift + hueco** = fijado. El secuenciador de efectos dispara estos huecos.

### Glitch y gesto mecánico
- **Glitch:** la salida pasa a una cabeza de cinta sobre el audio reciente: K1 velocidad (arriba normal, centro parada, abajo hacia atrás), K2 repetición, K3 retraso (hasta 2,6 s), K4 caos (mitad de abajo) o sobrecarga (mitad de arriba).
- **Gesto mecánico** *(desde RC2)*: al pulsar el audio se frena hasta parar; al soltar arranca. K1 movimientos (1-8), K2 tipo continuo en colores (parada de cinta → baby scratch → tear → back spin → rattle), K3 tiempo de parada, K4 de arranque. Usa el mismo motor que el Glitch: mientras suena, el Glitch espera.

## 7. FX

<a id="vista-fx"></a>
### 7.1 Vista FX

*Cómo se llega:* Botón **FX**: envíos a reverb y delay por pista, como siempre, más:

**En esta vista**

- **La reverb y el delay desde el aparato** — tipo, decay, tiempo, feedback…, guardados con el proyecto.
- **Reset rápido** — Duplicate deja los envíos y los efectos a cero.
- **Resonancia del filtro master** — en Shift + Octave ▲ / ▼, de 16 en 16 *(solo Beta 3.3; en RC2.02, 1-16 / 17-32)*.
- **Filtro master apagado / encendido** — Shift + pad 25, sin perder su posición *(solo Beta 3.3)*.

| Gesto | Qué hace |
|---|---|
| **Octave ▲ / ▼** | Los knobs = envíos de delay / de reverb. |
| **Shift + knob** | Parámetros globales: reverb K1 tipo, K2 decay, K3 damping; delay K1 time, K2 sync, K3 feedback, K4 width, K5 ratio, K6 slew. Se guardan con el proyecto. |
| **Duplicate** | Reset: envíos a 0, filtro master al centro, Master FX apagado. |
| **Shift + Octave ▲ / ▼** *(solo Beta 3.3)* | Resonancia del filtro master +16 / −16; se para en 127 / 0 (con Shift, Octave en amarillo). En RC2.02: **1-16 / 17-32** (LED verde). |
| **Shift + pad 25** *(solo Beta 3.3)* | Filtro master apagado / encendido: apagado, suena como con el filtro al centro aunque muevas su knob (el knob sigue cambiando su posición); otra vez, el filtro vuelve en la posición actual del knob. Apagado, el LED del knob del filtro se ve rojo; con Shift, el pad 25 en amarillo (rojo si está apagado). Sin Shift, el pad 25 es el de stock. |
| Fila inferior | La misma que en Master FX: huecos (26-30), gesto mecánico (31), grabar (32). |

- Si en Setup los retornos van por las tiras 3 / 4, sus envíos tienen tope a la mitad.

## 8. Sidechain

<a id="sidechain"></a>
### 8.1 Vista Sidechain

*Cómo se llega:* **Shift + FX**. Los presets de sidechain de cada pista como siempre, más los knobs:

**En esta vista**

- **El sidechain con knobs** *(desde RC2)* — ataque, hold, decay y profundidad del ducking de cada pista, más allá de los presets.
- **Compresor master** *(desde RC2)* — su ataque y su release.
- **Sidechain entre drums** — que un drum baje el volumen de otro (el bombo al bajo, por ejemplo).
- **Disparado por patrones** *(desde RC2)* — Synth 1 / 2 o MIDI 1 / 2 como fuente: las notas de su patrón agachan otra pista, no solo los drums.

| Control | Qué hace |
|---|---|
| **K1-K4** *(desde RC2)* | Ataque, hold, decay y profundidad del sidechain de la pista del último preset tocado (Synth 1 si ninguno); LEDs del color de la pista. |
| **K7 / K8** *(desde RC2)* | Ataque / release del compresor master (el que se activa en Advanced Setup), en blanco. Se guardan con el proyecto. |
| **Pads 1-4 de la fila 1** *(desde RC2)* | **Synth 1, Synth 2, MIDI 1, MIDI 2 como fuente** del sidechain de la pista elegida (la del último preset tocado), junto a los drums 1-4 de los pads 5-8: cada nota del **patrón** de esa pista dispara la envolvente, como un golpe de drum (las notas tocadas en directo no). La elegida, en el color de la pista; las demás, tenues. Un pad 5-8 vuelve a un drum. Se guarda con el proyecto. |
| **Octave ▼** con los drums | **Sidechain entre drums**: páginas de ducking por drum (filas 3-4) y qué drum dispara (fila 1, pads 5-8). |
| **Pads 1-4 de la fila 1** en una página de drums *(desde RC2)* | **Synth 1, Synth 2, MIDI 1, MIDI 2 como disparo** del drum del último preset tocado: cada nota del **patrón** de esa pista abre su envolvente (las notas tocadas en directo no). La elegida, en el color del drum; las demás, tenues. Un pad 5-8 vuelve a un drum. Como los presets del sidechain entre drums, no se guarda. |
| **K1-K4** en una página de drums *(desde RC2)* | Ataque, hold, decay y profundidad del sidechain del drum del último preset tocado (empiezan en los de su preset; tocar un preset los vuelve a él); LEDs del color del drum. Se guardan con el proyecto. |

## 9. Escenas y patterns

<a id="patterns"></a>
### 9.1 Vista Patterns y cadenas de patrones

*Cómo se llega:* Botón **Patterns**. Columnas = pistas, filas = patrones. Con el **modo cadena** *(desde RC2)*, cada patrón puede llevar una regla «suena n veces, salta a B; la vez siguiente, a C».

**En esta vista**

- **Cadenas de patrones** *(desde RC2)* — un patrón suena n veces y salta a otro, y la vez siguiente a un tercero: estructuras A A A B sin encadenar a mano.

| Gesto | Qué hace |
|---|---|
| **Shift + Octave ▲** | Activa el modo cadena de todo el proyecto (Octave ▲ verde). Con Shift, el Octave útil se ve en amarillo. |
| **Shift + Octave ▼** | Lo desactiva (las reglas quedan guardadas pero no se aplican). |
| En el modo: **patrón** | **A** (amarillo); A otra vez = una repetición más (hasta 8, los LEDs de los knobs las cuentan). |
| En el modo: **otro patrón de la pista** | **B** (verde); el siguiente = **C** (rojo). |
| **Clear + patrón** | En el modo: quita la regla (sin regla, borra el patrón). Fuera: borra el patrón, su regla y su orden. |

- Ejemplos: n = 3 → A A A B A A A C; sin C → A A A B; n = 1 → A B A C. B y C suenan una vez y la pista vuelve a A (salvo que tengan regla).
- Las reglas viajan con el patrón (al duplicarlo); el modo, con el proyecto y con cada escena (9.2).

<a id="mixer"></a>
### 9.2 Vista Mixer y escenas

*Cómo se llega:* Botón **Mixer**: niveles (Octave ▲) y panorama (Octave ▼) como siempre; **Mixer otra vez** = Master FX.

**En esta vista**

- **Nivel a 100 o a 0** — Shift + knob deja una pista a su nivel nominal o en silencio de un gesto.
- **Escenas con cadenas y repeticiones** *(desde RC2)* — una escena puede repetirse n veces y recordar el modo cadena.
- **Entradas y salidas al compás** *(desde RC2)* — Shift + pad de pista silencia o activa la pista justo al empezar el compás siguiente.
- **Modo cue** *(desde RC2)* — la mezcla en mono por la izquierda y, por la derecha, las pistas que quieras escuchar antes de meterlas.

| Gesto | Qué hace |
|---|---|
| **Shift + knob a la derecha / izquierda** | Nivel de esa pista a 100 / a 0 (página de niveles; en la de panorama, *(desde RC2)*: el modo cue). Sale por MIDI y se graba como un giro. |
| **Página de panorama: Shift + knob a la derecha / izquierda** *(desde RC2)* | **Modo cue** encendido / apagado (Octave ▼ rosa / blanco; se guarda en el aparato). |
| **Modo cue: un knob de panorama** *(desde RC2)* | El envío de esa pista al **cue** (salida derecha), del centro a la derecha (a la izquierda nada); Clear + knob = sin cue. Los knobs en rosa, más brillantes cuanto más envío. |
| **Pads de escena** | Como siempre; una escena guardada con el **modo cadena** se ve en **melocotón** y al cargarla vuelve el modo; una normal lo desactiva. *(desde RC2)* |
| **Shift + pads 1-8** *(desde RC2)* | **Silenciar / activar esa pista en el compás siguiente**: el pad parpadea mientras espera; otra vez lo cancela. Parado, al momento. |
| **Shift + pads 9-16** | **Repeticiones** de la escena actual (1-8; con Shift la fila en amarillo, la elegida en verde). *(desde RC2)* |
| Pistas que parpadean | Están siguiendo una regla de cadena. *(desde RC2)* |
| **Mixer** otra vez | Master FX. |

- Una escena termina cuando termina su cadena más larga. Guardar otra vez una escena no cambia sus repeticiones.
- **Modo cue** *(desde RC2)*: la **salida izquierda** lleva la mezcla en mono como siempre y la **derecha** solo las pistas en cue, cada una a su envío. Una pista silenciada en cue suena solo por la derecha, en el paso en que va su patrón; su pad sigue tenue y su pad (o Shift + pad, al compás siguiente) la mete o la saca de la mezcla. Los paneos no se tocan y vuelven al apagar el modo; guardar el proyecto guarda los mutes de la mezcla. La reverb, el delay y Master FX son los de la mezcla: el cue también los oye.

## 10. Projects y packs

<a id="projects"></a>
### 10.1 Vista Projects

*Cómo se llega:* Botón **Projects**: cargar y guardar proyectos como siempre, más copiar.

**En esta vista**

- **Copiar proyectos** *(desde RC2)* — duplica un proyecto en otro hueco o en otro pack.

- **Duplicate + pad A** (un proyecto) = la fuente (amarillo, parpadea); Duplicate + A otra vez la olvida.
- **Duplicate + pad B** = copia. B vacío: se escribe al momento; B ocupado: parpadea en blanco y hay que repetir Duplicate + B antes de ~5 s. Nunca el proyecto cargado. *(desde RC2)*
- **A otro pack:** elige la fuente, carga el otro pack, vuelve a Projects y Duplicate + B.
- Se copia el proyecto guardado en la tarjeta; mientras copia el aparato no responde unos instantes. En otro pack suena con sus patches y samples *(escribe en la tarjeta)*.

<a id="packs"></a>
### 10.2 Vista de packs

*Cómo se llega:* **Shift + Projects**. Cargar packs como siempre, más borrar.

**En esta vista**

- **Borrar packs** — libera huecos de pack desde el aparato.
- **Memoria interna protegida** — el mod nunca escribe en el pack interno.

1. Toca **Clear** (sin Shift): durante ~5 s parpadean los packs que se pueden borrar (nunca el cargado). Clear se ve blanco fijo en esta vista.
2. Toca el pack: solo ese parpadea; no se carga.
3. **Clear** otra vez antes de 5 s: borrado. El hueco se reutiliza tras reiniciar.

- **El pack de la memoria interna** (el primero) es de solo lectura para el mod: no se borra, y no se escribe en él nada del mod (copias, patches, capturas); el LED de Save se pone rojo 1,5 s. Sí se puede leer y copiar desde él a un pack de la tarjeta *(escribe en la tarjeta)*.

## A. Apéndice

<a id="guardado"></a>
### A.1 Qué se guarda y dónde

*Cómo se llega:* Proyecto, patrón, pack o ajustes del aparato.

| Qué | Dónde |
|---|---|
| Knobs nuevos de drums (incluidos ataque, inicio y corte), fuente de los sintes, reverb / delay, huecos y knobs de Master FX, compresor, modo cadena y escenas, cuenta atrás, arpegiador (con su resolución), escala propia, gate por pulsación, gate retrigger y forma del LFO del sinte propio *(desde RC2)* | El proyecto |
| Notas del step-drummer, valores del secuenciador de efectos, random-mutate, frecuencia, dinámicas, reglas de cadena, orden de reproducción, sample flips del modo muestra *(desde RC2)* | El patrón |
| Patches de sinte guardados, patches del sinte propio (con su matriz de modulación *(desde RC2.02)*), capturas usadas como samples | El pack *(escribe en la tarjeta)* |
| Motor de las pistas MIDI (estado y valores; *(desde RC2)*: también OSC 2, los knobs con Shift del granular y del oscilador y los pads 28 / 29), modo de MIDI Thru, canales de PGM | Ajustes del aparato |
| Efectos fijados, song pointer, toggle de Record del Setup, presets y disparos del sidechain entre drums, la matriz de modulación fuera de un patch *(desde RC2.02)* (se apaga al apagar el aparato) | No se guardan |

<a id="midi"></a>
### A.2 MIDI de las funciones nuevas

*Cómo se llega:* Todo lo nuevo sale y entra por CC / NRPN, respetando los filtros CC Tx / Rx del Setup.

- **Motor de las pistas MIDI** (canal de la pista): Filtro CC 74, Resonancia 71, Env → filtro 79, Ataque 73, Decay 75, Sustain 70, Release 72, Efecto 91, Gain 59, TUNE 26, FINE 27, WAVE 20, SHAPE 21, TUNE 2 37, FINE 2 39, WAVE 2 30, SHAPE 2 31, MIX 52, RING 54, velocidad del LFO NRPN 0:76; el resto NRPN MSB 4 con LSB = código.
- **Drums** (canal de drums): NRPN MSB 5-8 = Drum 1-4; LSB 1 env. de tono, 2 ring (frecuencia), 3 LFO, 4 velocidad LFO, 5 env → corte, 6 resonancia, 7 forma de la envolvente, 8 ring (cantidad), 9 modo de filtro, 10 inicio, 11 bitcrush, 12 tipo de distorsión, 13 corte, 14 ataque.
- **Master FX** (canal 16): NRPN MSB 9, LSB = 4 × efecto + knob.
- Tablas completas: la referencia MIDI (`docs/MIDI.md`).

<a id="instalar"></a>
### A.3 Instalar y volver atrás

*Cómo se llega:* `tools/rc_uploader.html` parchea el firmware oficial en el navegador y lo envía por Web MIDI.

1. Descarga el firmware oficial 1.2.1 de Novation, abre `tools/rc_uploader.html` en Chrome y conecta el Circuit Tracks por USB.
2. Elige la versión (RC2.02, la más segura RC2.02S, la Beta 3.3 con las funciones nuevas sin probar, o una anterior) y envía. El bootloader de Novation no se toca.
3. **Haz antes una copia de la tarjeta.** Con las versiones que no acaban en «S», no uses la memoria interna para proyectos.
- **Volver atrás:** envía otra versión o el firmware oficial. Si no arranca: **Scales + Preset + Note** al encender.
