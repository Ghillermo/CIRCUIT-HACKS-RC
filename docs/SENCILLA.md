# Guía del mod del Circuit Tracks, en palabras sencillas

Primer borrador de [reddit.com/u/luxurysoft1337](https://www.reddit.com/user/luxurysoft1337/), a quien damos las gracias. Esta guía explica el mod CIRCUIT-HACKS en palabras sencillas, vista por vista, con dibujos del panel. Sigue la estructura y el estilo llano de la guía de la comunidad «Circuit Tracks mod manual, in plain English» de **[reddit.com/u/luxurysoft1337](https://www.reddit.com/user/luxurysoft1337/)**, escrita para RC0.9 y Beta 1.3. Esta edición está reescrita para **RC2.01** y **RC2.01S**, conserva los nombres del manual del mod (captura, step-drummer, huecos…), corrige lo que aquella guía tenía mal o dejaba abierto y añade todas las funciones posteriores a Beta 1.3. Las referencias detalladas son la [guía por vistas](https://ghillermo.github.io/CIRCUIT-HACKS-RC/guia.html) y la [lista de características](https://ghillermo.github.io/CIRCUIT-HACKS-RC/index.html).

Nada de esto está probado en un aparato real salvo que lo diga el [CHANGELOG](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/blob/main/docs/CHANGELOG.md). El mod no tiene relación con Novation.

## Índice

1. [Qué es el mod](#what)
2. [Antes de instalar](#install)
3. [Cómo leer las instrucciones](#read)
4. [Palabras que usa esta guía](#words)
5. [Buscador rápido: quiero…](#finder)
6. [Efectos: envíos y la vista FX](#sends)
7. [Master FX](#masterfx)
8. [Drums](#drums)
9. [Pistas de sinte (Synth 1 y 2)](#synths)
10. [Pistas MIDI como sintes](#midi)
11. [Herramientas de patrón](#patterns)
12. [Escalas y la escala propia](#scales)
13. [Metrónomo y cuenta atrás](#metronome)
14. [Setup y MIDI](#setup)
15. [Proyectos y packs](#projects)
16. [Qué se guarda y dónde](#saved)
17. [Lo que el mod no hace](#not)
18. [Referencia MIDI](#midiref)
19. [Sobre esta edición](#edition)

<a id="what"></a>
## 1. Qué es el mod

El mod es el propio firmware del Circuit Tracks de Novation (1.2.1, build 4486) con funciones añadidas. Lo que esta guía no menciona funciona exactamente igual que en un aparato de stock, así que **la guía de usuario de Novation sigue valiendo**.

- Lo que no lleva marca está en todas las versiones.
- Lo marcado ***(desde RC2)*** es nuevo respecto a RC0.9; *(desde RC2.02)*, respecto a RC2.01; *solo Beta 3.22*, solo en la beta con las funciones nuevas (no en RC2.09). Mucho de ello no se ha probado aún en un aparato real: guarda una copia de la tarjeta.
- El bootloader de Novation (la parte que instala el firmware) nunca se modifica, así que siempre se puede volver atrás.

<a id="install"></a>
## 2. Antes de instalar

1. **Copia la tarjeta SD** en un ordenador. Hazlo antes de instalar cualquier versión.
2. Guarda también tus proyectos con Novation Components.
3. Elige una versión:

| Versión | Qué es |
|---|---|
| **RC2.09** | La versión candidata: todo lo de esta guía (RC2.01 + la matriz de modulación, el teclado partido con cualquier par y las formas nuevas del LFO, y los arreglos de RC2.03-RC2.09). |
| **RC2.09S** | La versión *más segura*: RC2.09, pero nada del mod escribe ficheros en la tarjeta por su cuenta: guardar capturas en el pack, copiar samples, patches o proyectos entre packs, los patches propios y borrar packs no hacen nada (el LED de Save se pone rojo). |
| **RC2.01 / RC2.01S, RC2 / RC2S, RC0.9 / RC0.9S** | Las anteriores: RC2.01 sin lo marcado *(desde RC2.02)*; RC2 con el sample tras el filtro master; RC0.9 sin lo marcado *(desde RC2)*. |
| **Beta 3.22** | La versión de prueba: RC2.09 + las funciones nuevas marcadas *solo Beta 3.22*, sin probar en un aparato. Escribe en la tarjeta como RC2.09. |

### Instalar
1. Descarga el firmware oficial 1.2.1 de Novation (el fichero de actualización de Components).
2. Abre `tools/rc_uploader.html` (en el repositorio del proyecto) en **Chrome**, con el Circuit Tracks conectado por USB.
3. Dale el fichero oficial, elige la versión y envíala. La página parchea el firmware oficial en tu navegador y comprueba el resultado; no contiene código de Novation. También están las versiones anteriores, y «Oficial» envía el firmware sin tocar.
- `tools/ct_uploader.html` envía un `.syx` ya hecho y lo compara con sumas conocidas. El repositorio público no tiene `.syx` de las RC: siempre se hacen a partir del firmware oficial.

### La memoria interna
El pack de la memoria interna del Circuit (el primero) es **de solo lectura para el mod**: nada del mod escribe ni borra ahí (guardar capturas o patches, copiar samples o proyectos, borrar el pack). Se rechaza y la luz de **Save** se pone roja ~1,5 s. Los guardados propios del aparato siguen funcionando. Con cualquier versión que no acabe en «S», guarda tus proyectos en la tarjeta, no en la memoria interna (el instalador pide confirmarlo).

### Volver atrás
Envía «Oficial» (u otra versión) desde la misma página. Si el aparato no arranca, mantén **Scales + Preset + Note** al encenderlo: es el modo bootloader de Novation, donde se puede enviar cualquier firmware otra vez.

<a id="read"></a>
## 3. Cómo leer las instrucciones

- Los **pads** se numeran del 1 al 32 de izquierda a derecha y de arriba abajo: fila 1 = pads 1-8, fila 4 = pads 25-32.
- **Knobs:** K1-K4 arriba, K5-K8 abajo (en el panel van al tresbolillo: K2 K4 K6 K8 arriba, K1 K3 K5 K7 abajo).
- «**Shift + X**» = mantener Shift mientras usas X. Igual con **Clear** y **Duplicate**.
- **Shift señala el camino:** mientras Shift está pulsado, los atajos que ofrece la vista se encienden en **amarillo**, y la opción ya elegida en otro color.
- **Confirmación en dos pasos:** varias acciones preguntan antes. «Clear + pad» hace parpadear el pad (el aparato pregunta «¿seguro?»); «Clear + el mismo pad» otra vez en ~5 s confirma. Otro pad mueve la pregunta ahí; esperar la cancela.
- Los **LEDs de los knobs** muestran el valor de las funciones nuevas con su **brillo** (más brillo = más). Los knobs de dos sentidos están apagados en el centro.
- Un drum, un sinte o una pista MIDI se eligen con su **botón de pista**; «su vista» es la que abre ese botón.

<a id="words"></a>
## 4. Palabras que usa esta guía

Son los nombres del manual del mod.

| Palabra | Significado |
|---|---|
| **Mantenido / fijado** | Un efecto mantenido suena mientras tienes el dedo encima; uno fijado (Shift + pad) sigue hasta que lo vuelves a tocar. |
| **Captura** (sample capturado) | Una grabación corta de la propia salida del Circuit (hasta ~3,5 s), hecha con el pad 32 de Master FX. Se puede tocar, poner en un hueco, sustituir un drum con ella o usarla de fuente del granular. Vive en la memoria: se pierde al apagar salvo que haya sustituido a un drum y hayas guardado el proyecto. |
| **Step-drummer** | Una capa sobre el patrón de una pista: el patrón sigue decidiendo cuándo suenan las notas, y los ocho knobs dan a cada **par de pasos** un valor (un desplazamiento de tono, una velocity, la posición de un macro…). |
| **Envío** | Cuánto de una pista entra en el delay o la reverb compartidos. |
| **Master FX** | Efectos en directo sobre toda la salida; se abre con Mixer dos veces. |
| **Huecos** (fila inferior) | Los pads 26-30 de Master FX y de la vista FX: cada uno guarda un efecto con sus knobs. |
| **Song pointer** | Los pads 9-24 de Master FX = pasos 1-16, para repetir o hacer bucles de partes del patrón en directo. |
| **Motor** | El sonido que puede tener una pista MIDI en el propio Circuit, elegido con el pad 27 de su vista Preset. |
| **Secuenciador de efectos** | Un motor que no suena: cada par de pasos dispara un hueco de Master FX. |
| **Patch del sinte propio** | Un ajuste guardado del motor de una pista MIDI, en el pack. |
| **Modo cadena** | El modo de todo el proyecto en que los patrones siguen sus reglas de cadena (sonar n veces y saltar). |
| **Pack** | El conjunto de samples, patches de sinte y proyectos de Novation. |
| **Tiras 3 y 4** | Las tiras del mixer por donde salen los sonidos propios de las pistas MIDI (y los retornos enviados ahí). |

<a id="finder"></a>
## 5. Buscador rápido: quiero…

| Quiero… | Haz esto |
|---|---|
| Abrir Master FX | **Mixer** y otra vez **Mixer** (círculo 1). |
| Poner un knob en su valor por defecto | Mantén **Clear** y gira el knob a la **derecha** (círculo 2). |
| Borrar la automatización de un knob | Mantén **Clear** y gira el knob a la **izquierda** (drums; motor MIDI *(desde RC2)*). |
| Tocar un drum como un teclado | Elige el drum, **Shift + Preset** (o **Preset otra vez** *(desde RC2)*) (círculo 7). |
| Grabar la propia salida del Circuit | Master FX, **pad 32**. Tócala con el **pad 7**. |
| Sustituir un drum por esa captura | Vista Preset de drums, **Clear + pad** y luego **Clear + el mismo pad**. |
| Intercambiar dos samples de drums | Vista Preset de drums, mantén **Duplicate**, toca el pad A y luego el B (círculo 4). |
| Quitar todos los efectos fijados | Master FX, **pad 8**. |
| Poner el nivel de una pista a 100 o 0 | Mixer, **Shift + girar** el knob a la derecha o a la izquierda. |
| Hacer un bucle de parte del patrón en directo | Master FX, mantén dos pads del song pointer. |
| Dar a una pista MIDI su propio sonido | MIDI 1 / 2, **Preset**, **pad 27**. |
| Rotar un patrón (Nudge) | Pattern Settings: elige el primer paso y luego **pad 26** *(desde RC2)* (círculo 5). |
| Arpegiar una pista | Pattern Settings, **Shift + pad 25** *(desde RC2)*. |
| Cuantizar un patrón grabado | **Shift + Play** *(desde RC2)* (la pista elegida). |
| Usar mi propia escala | **Shift + Scales** *(desde RC2)* (círculo 6). |
| Metrónomo / cuenta atrás | **Shift + Clear** *(desde RC2)* (círculos 3 + 2). |
| Gate = lo que mantengo el pad | **Gate** dos veces (Micro Step), **pad 32** *(desde RC2)* (círculo 8). |
| Volver al firmware de stock | Envía «Oficial» desde el instalador. |

<a id="sends"></a>
## 6. Efectos: envíos y la vista FX

El Circuit tiene **un delay y una reverb** compartidos por todas las pistas; el **envío** de cada pista decide cuánto entra (0 = seco). **Master FX** (sección siguiente) es otro juego de efectos en directo sobre todo a la vez: los envíos fijan lo mojada que suena cada pista, y Master FX sirve para tocar con la mezcla entera.

Pulsa **FX** para abrir la vista FX:

| Gesto | Qué hace |
|---|---|
| **Octave ▲ / ▼** | Los 8 knobs = los envíos de delay / de reverb, uno por pista. |
| **Shift + knob** | El propio efecto, para todas las pistas: reverb K1 tipo, K2 decay, K3 amortiguación; delay K1 tiempo, K2 sincronía, K3 realimentación, K4 anchura, K5 proporción, K6 slew. Se guarda con el proyecto. |
| **Duplicate** | Reset: envíos a 0, filtro master centrado, Master FX apagado. |
| **Shift + Octave ▲ / ▼** | *Solo Beta 3.22:* resonancia del filtro master, 16 más / 16 menos; se para arriba y abajo. En RC2.09 va en **1-16 / 17-32** (LED verde). |
| **Shift + pad 25** | *Solo Beta 3.22:* apaga el filtro master: suena como con el filtro al centro aunque muevas su knob; otra vez, lo enciende donde esté el knob en ese momento. Apagado, la luz del knob del filtro se pone roja. |
| Fila inferior | Lo mismo que en Master FX: huecos, gesto mecánico, grabar la captura. |

- Si el Setup manda el retorno de reverb / delay por la tira 3 o 4 (sección 14), los envíos de esas tiras se quedan a media carrera y van a media velocidad.

<a id="masterfx"></a>
## 7. Master FX

Efectos en directo sobre toda la salida. **Mantén** un pad para oír su efecto; **Shift + pad** lo fija (tócalo otra vez para soltarlo). Se abre con **Mixer, Mixer**; cualquier otro botón de vista sale.

| Pad | Qué es | K1-K4 mientras lo mantienes |
|---|---|---|
| 1 | Gater | división, profundidad, anchura, suavizado |
| 2 / 3 | Auto-Filter, paso bajo / paso alto | velocidad, profundidad, resonancia, centro |
| 4 | Digitise | frecuencia de muestreo, bits; *(desde RC2)*: K3 = envío momentáneo al delay, K4 = envolvente de la cantidad |
| 5 | Phaser | velocidad, profundidad, realimentación, mezcla |
| 6 | **Glitch** *(desde RC2)* (en RC0.9, el Vinyl) | Glitch: velocidad, repetición, retardo, caos / sobrecarga |
| 7 | Tocar la **captura** | tono, modo, inicio, final |
| 8 | Soltar todo lo fijado (efectos, huecos, song pointer, captura) y bypass | — |
| 9-24 | **Song pointer**: pasos 1-16 | — |
| 26-30 | **Huecos** | los del efecto guardado |
| 31 | **Gesto mecánico** *(desde RC2)* (en RC0.9, el Glitch) | gesto: movimientos, tipo, tiempo de parada, tiempo de arranque |
| 32 | **Grabar** la captura | — |

- **Clear + knob a la derecha** = ese knob a su valor por defecto. RC: mientras Clear está pulsado, los knobs se ven lavanda en su valor por defecto y rojos fuera; *(desde RC2)*: solo lavanda (Master FX no tiene automatización que borrar).
- *(desde RC2)* Cada proyecto guarda su propio Master FX: los 20 knobs de los efectos, las asignaciones de los huecos y el compresor. Los efectos fijados no se guardan.

### Song pointer (pads 9-24)
- **Mantener un paso:** se repite mientras lo mantienes.
- **Mantener dos pasos:** el patrón hace un bucle entre ellos mientras los mantienes.
- **Shift + dos pasos:** ese bucle se queda (fijado); el pad 9 se pone blanco y tocarlo quita el bucle.
- **Modo frase:** Shift + un paso = una frase desde ese paso hasta el 16; tocar otro paso mueve el final; Shift + otro paso mueve el inicio; Shift + el paso de inicio (o el pad 9 blanco) sale.
- El paso que suena se ve blanco; el puntero empieza apagado al cargar un proyecto.

### La captura (pads 32 y 7)
- **Pad 32 (rojo):** mantener = graba mientras lo mantienes (hasta ~3,5 s); un toque corto = graba hasta el siguiente toque; **Shift + pad 32** = armado: con el secuenciador en marcha graba el compás siguiente, parado espera a Play y graba el primer compás. Desde RC2.01 la captura y el sample que suena van antes del filtro master: el filtro le afecta y la captura no lo lleva.
- Graba la salida **sin** los efectos de Master FX; al sonar, pasa por ellos.
- El **pad 7 (amarillo)** la toca: K1 tono (±24 semitonos), K2 modo por colores (amarillo one-shot, verde gate, azul bucle: el bucle suena mientras mantienes el pad), K3 inicio, K4 final (final antes del inicio = al revés). **Shift + pad 7** la deja sonando en cualquier modo hasta volver a pulsar el 7 (o el 8).
- Mantén el pad 7 y toca un hueco para guardarla ahí; sustituye un drum con ella (sección 8); úsala de fuente del granular (sección 10).

### Glitch
La salida se convierte en un cabezal de cinta sobre los últimos segundos de audio. K1 velocidad (arriba = normal, más abajo = freno de cinta, centro = parado, por debajo = al revés), K2 tamaño de la repetición (al máximo = sin repetición), K3 retardo (hasta ~2,6 s), K4 mitad inferior = caos (saltos, cortes, inversiones), mitad superior = sobrecarga (bloques tarde y clics, que frena desde los tres cuartos). Mantén el pad del Glitch y toca un hueco para guardar un Glitch con estos ajustes (turquesa).

### Gesto mecánico *(desde RC2)*
Pulsar el pad 31 frena el audio hasta pararlo; soltarlo lo arranca otra vez. K1 = movimientos por gesto (1-8), K2 = el tipo, mezclado de forma continua y en colores (tape stop → baby scratch → desgarro → back spin → traqueteo), K3 = tiempo de parada, K4 = tiempo de arranque. Usa el motor del Glitch: mientras suena un gesto, el Glitch espera.

### Huecos (pads 26-30)
Mantén un efecto (pads 1-6), el pad 7 (la captura) o el pad del Glitch / gesto y toca un hueco: el hueco guarda ese efecto con una copia de sus knobs. Tocar el hueco = encendido mientras lo mantienes; **Shift + hueco** = fijado. Los huecos se guardan con el proyecto. Un hueco vacío es el efecto de actuación de stock de la vista FX. El secuenciador de efectos (sección 10) dispara estos huecos.

<a id="drums"></a>
## 8. Drums

### Los knobs de los drums
Cada knob hace lo que dice su etiqueta del panel, con una segunda capa con Shift. Todo se guarda con el proyecto y sale por MIDI (NRPN, sección 18). Con todos los knobs en neutro, un sample suena como en un aparato de stock.

| Knob | Solo | Con Shift |
|---|---|---|
| K1 Oscillator | Tono (*(desde RC2)*: el de stock, continuo; los pads cromáticos transponen encima) | Cantidad de la envolvente de tono |
| K2 Osc mod | Frecuencia del ring mod | Cantidad del ring mod |
| K3 Amp envelope | RC: decay; a la izquierda del cero, el punto de inicio del sample. *(desde RC2)*: **izquierda = decay** (el de stock), **derecha pasado el máximo = ataque** (entrada gradual de hasta 1 s) | *(desde RC2)*: **izquierda = inicio del sample**, **derecha = corte** desde el final |
| K4 Filter envelope | Envolvente → corte | Forma de la envolvente |
| K5 Filter frequency | Filtro / EQ | Modo del filtro: EQ tilt (stock), paso banda, notch, comb, DJ |
| K6 Resonance | Resonancia | — |
| K7 Modulation | Cantidad del LFO (a la derecha, trémolo; *solo Beta 3.22:* a la izquierda, cada golpe empieza en otro punto del sample, como un scan) | Velocidad del LFO |
| K8 FX | Distorsión; a la izquierda del cero, bitcrush | Tipo de distorsión: stock, suave, dura, plegada |

- **Reset:** Clear + knob a la derecha = por defecto (las dos capas; LED lavanda, como en el original); Clear + knob a la izquierda = borrar la automatización de ese knob (rojo), como en el original. *(desde RC2)*: Clear + K3 a la derecha también pone a 0 ataque, inicio y corte; Clear + K8 a la derecha también quita el bitcrush; **Clear + el botón del drum** (con su vista en pantalla) deja todos sus knobs por defecto.
- **RC0.9:** un proyecto nuevo o sin tocar empieza con el modo de filtro en DJ, que quita el EQ de stock: los drums pueden sonar distinto que en un Circuit de stock. Shift + K5 a «EQ tilt» devuelve el sonido de stock. *(desde RC2)*: arreglado (por defecto, el EQ de stock).

### Tocar un drum como un teclado
Elige el drum y pulsa **Shift + Preset** (*(desde RC2)*: o **Preset otra vez** en su vista Preset). Tres filas de pads tocan su sample a distintas alturas, en la escala y la tónica de la vista Scales. K1 = desplazamiento en semitonos, Shift + K1 = afinación fina en cents. Al grabar, cada altura va solo a su propio paso (*(desde RC2)*: los pads transponen sobre el tono de K1 y, grabando, quedan en su paso; Clear + K1 a la izquierda, sostenido, los borra con la automatización de K1).

### Vista Preset de drums
| Gesto | Qué hace |
|---|---|
| **Clear + pad**, **Clear + el mismo pad** | Ese drum toca ahora la **captura**. Es temporal hasta que guardes el proyecto: al guardar se escribe en el pack (`PCM/NN_PCM.wav`) si cabe en la memoria de samples. No en la versión más segura (ahí dura hasta recargar el pack) ni en el pack de la memoria interna. |
| **Duplicate + pad A + pad B** (mismo pack) | Intercambia los dos samples (ficheros y tabla); se oye al momento. |
| **Duplicate + pad A**, cargar otro pack, **Duplicate + pad B** | Copia el sample A sobre el B del otro pack (el pack de A no cambia; B puede estar vacío). Va al sitio de B si cabe; si no, a la memoria libre de importación; nunca pisa un sample que suena. |
| **Varios pads mantenidos** *(desde RC2)* | Con el arpegiador del drum encendido, el arpegio de los samples mantenidos (sección 11). |

- Intercambiar y copiar escriben en la tarjeta: no en la versión más segura. Los patches de sinte se intercambian y copian igual en la vista Preset de Synth 1 / 2 (los 128 patches de un pack los comparten los dos sintes).

### Rollers de micropasos *(desde RC2)*
En la vista Note de los drums (pulsa **Note** hasta que las filas 1-3 se vean tenues), las filas 1-3 son **rollers**: cada columna es del drum del cuadro de debajo (columnas 1-4 = drums 4-1, columnas 5-8 = drums 1-4); la columna izquierda de un drum son sus micropasos 1-3 y la derecha los 4-6 (drum 1 = pads 4, 12, 20 y 5, 13, 21). Mientras mantienes uno o varios, ese drum suena en **todos los pasos** en esos micropasos. En marcha sigue el patrón; parado suena al tempo del proyecto. **Con Record** los golpes se graban en el patrón.

### Vista Sidechain
Se abre con **Shift + FX**. *(desde RC2)*: **K1-K4** = ataque, hold, decay y profundidad del sidechain de la pista del último preset tocado (Synth 1 si ninguno), en el color de la pista; **K7 / K8** = ataque / release del compresor master (se enciende en Advanced Setup), guardados con el proyecto.

**Sidechain entre drums:** **Shift + FX** y luego **Octave ▼**: las filas 3-4 tienen las páginas de ducking de cada drum, y los pads 5-8 de la fila 1 eligen qué drum provoca el ducking (*(desde RC2)*: los pads 1-4, **Synth 1, Synth 2, MIDI 1 o MIDI 2**: cada nota de su patrón). *(desde RC2)*: en la página de un drum, **K1-K4** fijan ataque, hold, decay y profundidad del drum del último preset tocado (en el color del drum; tocar un preset devuelve los valores del preset). Se guarda con el proyecto.

**Sidechain desde patrones** *(desde RC2)*: en las páginas de Synth y MIDI de la vista Sidechain, los **pads 1-4 de la fila 1** (junto a los drums de los pads 5-8) eligen **Synth 1, Synth 2, MIDI 1 o MIDI 2** como fuente de la pista elegida (la del último preset tocado): cada nota del patrón de esa pista la agacha, como un golpe de drum. Se guarda con el proyecto.

<a id="synths"></a>
## 9. Pistas de sinte (Synth 1 y 2)

### Vista de la fuente
Con la vista de un sinte en pantalla, pulsa **su botón otra vez**. Los pads 25-29 eligen la fuente del ruido del sinte: ruido (normal), entrada 1, entrada 2, entrada 1 invertida, entrada 2 invertida. El patch necesita algo de nivel de ruido (CC 56) para que se oiga la fuente. Se guarda con el proyecto. Si el Setup manda los retornos de reverb / delay por las tiras 3 / 4, eso es lo que llega al sinte. El **pad 30** abre el step-drummer del sinte; *(desde RC2)* el **pad 32** abre el editor de los destinos de los macro knobs. Cualquier botón cierra la vista.

### Step-drummer
Una capa sobre el patrón: el patrón decide qué pasos suenan; los knobs dan a cada par de pasos un valor.
- **Pares:** K1 = pasos 1-2, K2 = pasos 3-4… **1-16 / 17-32** = la otra mitad del patrón.
- **Dos páginas:** Octave ▲ = la página de tono, Octave ▼ = la de velocity.
- **Pads 1-16** = los pasos (brillante = una nota, blanco = el que suena); tocar = escuchar, **Shift + tocar** = poner o quitar una nota. Con Record, los pasos que tocas se graban en tiempo real.
- **Abrirlo:** sinte = pad 30 de la vista de la fuente; pista MIDI = pad 30 de su vista Preset con un motor encendido (**Shift + pad 30** lo apaga). *(desde RC2)*: en MIDI el pad 30 se ve tenue apagado y brillante encendido.
- **Página de tono, sintes:** los pads 17-24 eligen uno de los 8 macros del patch; el valor de cada par es la posición de ese macro, escrita como automatización. *(desde RC2)*: un par vacío empieza en 0.
- **Página de tono, pista MIDI:** los pads 17-24 eligen un destino del motor (tono de los dos osciladores, tono de OSC 2, WAVE, FM, MIX, envolvente → filtro, SHAPE, decay) y el valor (64 = sin cambio) lo desplaza en esos dos pasos, sumando o restando al valor de la página del motor. *(desde RC2)*: el LED del knob muestra la cantidad (tenue en el centro, más brillante cuanto más se aleja, hacia arriba o abajo).
- *(desde RC2)* **Página de velocity con destino propio:** en la página de velocity, los pads 17-24 eligen un destino para la página 2 (el mismo pad otra vez = ninguno); los knobs escriben entonces ese destino (MIDI desde el punto sin modulación del destino, sintes desde 0). En MIDI la página 2 usa el carril de automatización de REL, así que REL no se reproduce ni se graba con el step-drummer encendido.
- *(desde RC2)* **Toggle pitch-vel (pad 32 de la vista, verde):** además de sus destinos, la página de tono mueve las **notas** un grado de la escala del proyecto cada 8 pasos del knob (MIDI −8 … +8 desde el centro, sintes 0 … +16) y la página de velocity fija también la velocity de las notas. Con el toggle, los destinos de tono de la página de tono ya no desafinan el sinte propio (se mueve la nota).

### Extras de RC2
- **Teclado partido:** mantén Synth 1 y pulsa Synth 2 (o al revés): las dos filas de arriba tocan Synth 1 y las dos de abajo Synth 2, cada uno con su escala, octava y velocity. Knobs y Octave siguen al sinte pulsado primero; cualquier botón de pista o de vista sale. *(Desde RC2.02:* con cualquier par de Synth 1, Synth 2, MIDI 1 y MIDI 2; arriba, la pista que mantuviste primero.*)*
- *Solo Beta 3.22:* con el teclado partido, mantén un botón de pista (también de drum): mientras lo mantienes, los knobs son los de esa pista. Un toque corto lo cierra, como siempre.
- **Colores de los patches** en la vista Preset: azul oscuro = mono, lavanda = mono con glide, color de la pista = poly; el elegido más claro.
- **Guardar un patch en el pack:** vista Preset, **Clear + pad** y luego **Clear + el mismo pad** en ~5 s: el patch tal como suena va a ese hueco (el stock no guarda patches desde el aparato). Se rechaza en el pack de la memoria interna.
- **Destinos de los macros:** en la vista de la fuente, el pad 32 abre el editor. Gira un knob para elegir su macro; el knob cambia el campo actual y **Octave ▼ / ▲** recorren los campos (ranura 1-4, inicio, final, destino, profundidad); los pads dibujan el número. Cualquier pad suelta el macro; el pad 32 cierra el editor. Los destinos son los números de CC / NRPN de la Programmer's Reference Guide de Novation (por ejemplo CC 74 = corte del filtro).

<a id="midi"></a>
## 10. Pistas MIDI como sintes

Normalmente una pista MIDI solo envía MIDI. Con el mod, MIDI 1 y MIDI 2 pueden tener cada una su **propio motor** en el Circuit; las notas siguen saliendo por MIDI.

### El motor (pad 27)
En la vista Preset de MIDI 1 / 2, cada pulsación del **pad 27** pasa al motor siguiente; su color dice cuál: apagado (oscuro) → entrada de línea (amarillo) → oscilador (verde) → VA-drum (rojo) → granular (magenta) → muestra (cian, *(desde RC2)*) → secuenciador de efectos (azul) → apagado.
*Solo Beta 3.22:* un toque al pad 27 abre los motores en la tercera fila de pads, en sus colores; tocas el que quieras y el pad 27 otra vez vuelve a los patches. Shift + pad 27 pasa al siguiente como antes.

| Motor | En palabras sencillas |
|---|---|
| Entrada de línea | La entrada de audio (línea 1 para MIDI 1, línea 2 para MIDI 2) por el VCA, el filtro, la envolvente y el LFO de la pista, disparados por sus notas: dar forma a un sonido externo con el Circuit. |
| Oscilador | Un sinte de dos osciladores: WAVE pasa de seno (0) → triángulo (42) → sierra (84) → cuadrada (126); SHAPE (centro = la forma pura) pliega el seno y el triángulo (a la derecha), curva la sierra (*solo Beta 3.22:* la convierte en una **supersaw** de 7 sierras, más gruesa cuanto más a la derecha; y a la izquierda curva el triángulo) o estrecha el pulso de la cuadrada; OSC 2 añade FM, ring y modos de bits. Una nota = unísono, dos notas = una por oscilador (*(desde RC2)*: con un oscilador, la última nota manda). |
| FM | *Solo Beta 3.22:* el pad 24 de la fila de motores (violeta). Un sinte FM de 4 operadores con 16 algoritmos: los típicos, percusivos (bombo, caja, metal, tom), campanas y cuerdas. Sus knobs en el pad 7: K1-K4 la ratio de cada operador, K5-K8 su nivel; con Shift, el ataque, el algoritmo, el feedback, el ruido y el release. |
| VA-drum | El oscilador como voz de percusión de un disparo: Sustain = decay de la envolvente de tono, Release = decay de la de filtro, velocidad del LFO = nivel de ruido. Bombo: seno, Decay ~70, Sustain ~30, envolvente → tono a la derecha; caja: más ruido, Decay corto, paso banda. |
| Granular | Hasta 16 granos de un sample a la vez: texturas, sonidos congelados o estirados (página 2, más abajo). |
| Muestra *(desde RC2)* | Un sample del pack de un golpe, a la altura de cada nota (C3 = como se grabó): drums afinables en una pista MIDI. **Note dos veces** = el selector: filas 3-4 los samples (Octave ▼ / ▲ = 4 páginas, los 64), filas 1-2 los pasos; mantener un paso y tocar un sample = ese paso toca ese sample (sample flip), también al revés (mantener el sample y tocar pasos, desde RC2.04) y en vivo con Record. |
| Secuenciador de efectos | No suena: cada par de pasos de su step-drummer dispara un hueco de Master FX. |

- Todo motor que suena pasa por un VCA, un efecto y un filtro (con envolvente y LFO) antes de la tira 3 o 4 del mixer; el **pad 29** cambia el orden VCA → efecto → filtro / filtro → VCA → efecto (*(desde RC2)*: el pad 29 en el color de la página VCA-VCF).

### Pads de la vista Preset de MIDI
| Pad | Función |
|---|---|
| 1-5 | Página de knobs: 1 VCA-VCF, 2 OSC 1 (los controles del granular en granular), 3 OSC 2, 4 los 8 valores automatizables, 5 modulación. *(desde RC2)*: **Clear + pad de página** = esa página a sus valores iniciales. |
| 6 | *(desde RC2.02)* **Matriz de modulación** (más abajo). |
| 9-24 | *(desde RC2)* **Patches del sinte propio** (más abajo). |
| 25 | Editor de CC de los macros de la plantilla. |
| 26 | Patch flip: cada nota sale como Program Change (*(desde RC2)*: solo por el canal de la pista). Excluyente con el motor. |
| 27 | El motor. |
| 28 | Uno / dos osciladores (oscilador y VA-drum). |
| 29 | Orden de la cadena. |
| Shift + 29 | *(desde RC2)*: gate retrigger; apagado (amarillo) = legato, una nota nueva con otras pulsadas solo cambia la altura. |
| 30 | Step-drummer. |
| 31 | VA-drum: la velocity escala las envolventes de tono y de filtro. |

### Las páginas de knobs
- **Página 1, VCA-VCF:** K1 ataque (Shift sustain), K2 release (Shift decay), K3 envolvente → nivel (Shift LFO → nivel), K4 envolvente → filtro (Shift LFO → filtro), K5 filtro (Shift tipo de filtro: DJ, LP 12, HP 12, paso banda, notch, LP 24, HP 24), K6 resonancia (Shift ganancia del VCA, hasta +18 dB con saturación), K7 velocidad del LFO, K8 cantidad del efecto (Shift tipo de efecto: suave, dura, plegada, wavefold, ring, comb, chorus).
- **Página 2, OSC 1:** K1 afinación (Shift fina), K2 forma (Shift mezcla OSC 1 ↔ OSC 2), K3 envolvente → tono (Shift bitsync), K4 envolvente → forma, K5 LFO → tono, K6 LFO → forma, K7 WAVE, K8 LFO → morph (Shift envolvente → morph).
- **Página 2, granular:** K1 tono ±24 (Shift fino), K2 posición (Shift dispersión de la posición), K3 recorrido: el centro congela, derecha hacia delante, izquierda hacia atrás (Shift probabilidad de un grano al revés; *solo Beta 3.22:* todos los knobs de velocidad de LFO son bipolares: a la derecha libre, a la izquierda a tempo, empezando en el primer tiempo del compás. Shift + K3 a la izquierda = granos al revés, a la derecha = dispersión del tono), K4 tamaño del grano 5-500 ms (Shift dispersión del tono; *solo Beta 3.22:* Shift + K4 = **estéreo**: cada grano sale a un lado, y el panorama de la pista decide cuántos van a cada lado), K5 densidad 1-16 (Shift ventana), K6 zona del recorrido (Shift modo de nota: tono / slicer; *(desde RC2)* stretch = desde la posición hasta el final en un número fijo de pasos, sin cambiar el tono), K7 LFO → posición (Shift LFO → tamaño), K8 envolvente → posición (Shift fuente: RC un sample del pack o, a la izquierda, la captura; *(desde RC2)* la captura o el sample actual de un drum).
- **Página 3, OSC 2:** *(desde RC2)*: K1 afinación 2, K2 forma 2, K3 mezcla OSC 1 / OSC 2, K4 FM, K5 afinación fina 2, K6 BITSYNC, K7 WAVE 2, K8 ring, todos sin Shift (RC0.9: K1 afinación 2 con Shift fina 2, K2 forma 2 con Shift FM, Shift + K3 ring, K7 WAVE 2). **Página 4:** los 8 valores automatizables (afinación, release, envolvente → nivel, envolvente → filtro, filtro, resonancia, velocidad del LFO, efecto). **Página 5:** ADSR arriba, LFO abajo (*(desde RC2)*: **Shift + K8** = la forma del LFO, seis formas en colores; *(desde RC2.02)* siete, con un sample & hold suavizado, y el triángulo de inicio).
- **Automatización:** con Record + Play, los movimientos de los valores de la página 4 se graban en el patrón. *(desde RC2)*: **Clear + knob a la izquierda** borra la automatización de ese knob (rojo), **Clear + knob a la derecha** = por defecto (lavanda). *Solo Beta 3.22:* **Shift + knob** en la página 4 elige qué parámetro graba ese knob (cualquiera de los 33, en los colores de la matriz; se guarda con el patch); **Record mantenido + un paso** guarda en ese paso todos los valores que has cambiado. *Solo Beta 3.22:* en la vista Velocity, **Shift + un paso** hace que ahí la automatización se suelte y todo vuelva a donde están los knobs.
- *Solo Beta 3.22:* el sinte propio de MIDI 1 / 2 se guarda con el proyecto: al cargarlo vuelve como sonaba al guardarlo. Y al elegir con Shift + knob el destino de un knob de la página 4, los pads enseñan dónde está, como en la matriz.

### Secuenciador de efectos
Pon primero efectos en los huecos de Master FX. Luego abre el step-drummer (pad 30) y pon notas en pasos (Shift + pad). Cada knob elige un hueco para su par: 0 ninguno, 1-5 = pads 26-30, 6 = pad 31; en cada paso con nota ese hueco se enciende, y el LED del knob toma el color del efecto. El knob se mueve despacio (~48 pasos de giro por hueco). *(desde RC2)*: al final del recorrido, **aleatorio** (blanco): uno de los huecos asignados al azar en cada nota.

### Editor de CC (pad 25)
Mueve un knob para elegirlo; su número de CC se dibuja en los pads. **Octave ▼ / ▲** recorren los campos; girar el knob cambia el valor. Un CC normal tiene número, inicio y final; 99 / 98 / 6 = NRPN de 7 bits (MSB, LSB…), 38 = NRPN de 14 bits. Se guarda con el pad 26; cualquier botón de vista o el pad 25 descartan.

### Matriz de modulación *(desde RC2.02)*
Con el motor encendido, el **pad 6** de la vista Preset de MIDI convierte los 8 knobs en **8 fuentes**: K1 velocity, K2 nota, K3 azar por nota, K4 LFO 2, K5 envolvente 2, K6 golpe de un drum, K7 posición en el patrón, K8 azar por pasos. **Girar un knob elige a qué parámetro va** (cualquiera de las páginas de knobs, un tramo cada uno, en el color de su página) **y cuánto** (dentro del tramo). Mientras giras, los pads enseñan dónde está ese parámetro. **Shift + K4 / K5 / K6 / K8** = forma y velocidad del LFO, ataque y caída de la envolvente, qué drum, cada cuántos pasos. **Clear + knob** = fuente apagada; **Clear + pad 6** = todas. Se guarda con los patches del sinte propio.

### Patches del sinte propio *(desde RC2)*
Las filas 2-3 de la vista Preset de MIDI son 16 huecos de patch, 4 páginas con Octave ▼ / ▲ (64 por pack, compartidos por MIDI 1 y 2). Tocar = cargar (la tónica suena mientras lo mantienes). **Clear + pad** dos veces = guardar. **Duplicate + A + B** = intercambiar; **Duplicate + A**, otro pack, **Duplicate + B** = copiar. Melocotón tenue = un patch, brillante = el último usado, violeta = vacío. Un patch guarda el motor, los dos osciladores, el orden, todos los valores y el ajuste del step-drummer (los pasos son del patrón). **Clear + el botón de la pista** reinicia todo el motor.

<a id="patterns"></a>
## 11. Herramientas de patrón

### Pattern Settings
Pulsa **Pattern Settings** con una pista elegida. Como en stock: pads 1-16 el primer / último paso, pads 17-24 el sync rate, pads 29-32 la dirección. Añadido *(desde RC2)*:

| Pad | Función |
|---|---|
| 25 | La vista de probabilidad en **modo 2** (más abajo). *(desde RC2)*: **Clear + pad 25** borra las dinámicas y el random-mutate de todo el patrón (pistas de notas). |
| 26 | **Nudge** (naranja). |
| 27 | Orden **fractal**: 1 · 1 2 · 1 2 3 · … hasta el último paso. |
| 28 | Orden **deconstruido**: las diagonales de la rejilla (1 6 11 16 · 2 7 12 13 · 3 8 9 14 · 4 5 10 15, igual para 17-32). |

- **Nudge, paso a paso:** 1. en Pattern Settings, elige el **primer paso** del patrón con los pads 1-16 como en stock; 2. pulsa el **pad 26**: ese paso pasa a ser el paso 1 y lo que había delante va al final (pasos y automatización, sobre 16 o 32 pasos; el último paso se mueve con ellos). Elegir el paso 2 adelanta todo un paso.
- Los pads 27, 28 y los cuatro de dirección se excluyen. El orden se guarda con el patrón; borrar el patrón lo quita. Nudge y los órdenes funcionan también en los drums.

### Arpegiador *(desde RC2)*
- **Shift + pad 25** = el arpegiador del patrón que suena en la pista, encendido / apagado (pad 25 verde encendido). **Shift + pads 27-32** = su orden (fractal, deconstruido, arriba, abajo, ping-pong, aleatorio), aparte de la dirección del patrón. **Shift + pads 17-24** = su propia resolución (de 1/4 en el pad 17 a 1/32T en el 24, como el sync rate; el mismo pad otra vez = la de la pista). Con Shift, los pads conservan sus colores de Pattern Settings y los elegidos se ven verdes.
- **Secuencia:** cuando dos o más notas empiezan en un paso, suenan de una en una en el orden elegido, cada una con su propio gate (como mucho un paso del arpegio).
- **En vivo:** la primera nota suena como siempre; mantener otra empieza el arpegio de las notas mantenidas hasta que las sueltas todas (parado: al tempo del proyecto). Con Record se graba el acorde, y la secuencia lo arpegia.
- *Solo Beta 3.22:* las notas suenan en el orden en que las pulsas; si sueltas una, su hueco se salta y la siguiente que pulses lo ocupa. El random-mutate del paso también cambia las notas del arpegio, también al tocar en vivo (el del paso en que está la pista).
- Desde RC2.04, un acorde (o una nota) que mantienes más de 16 pasos mientras grabas sigue sonando después del paso 16.
- **Drums:** los mismos gestos en el Pattern Settings de un drum. En la vista Preset del drum, el primer sample mantenido es el normal; mantener más hace que el drum **salte de sample en sample** en ese orden. Con Record (en marcha) cada golpe se graba con su sample como sample flip del paso.

### Vista de probabilidad
| Cómo se abre | Fila 3 | Fila 4 |
|---|---|---|
| **Shift + Pattern Settings** | Probabilidad (stock) | **Random-mutate** *(desde RC2)* |
| **Pattern Settings dos veces** (modo 1) | Probabilidad (stock) | **Frecuencia** *(desde RC2)*: el paso suena en la última de cada n pasadas de su patrón (1-8; cuenta desde Play) |
| **Pad 25** de Pattern Settings (modo 2) *(desde RC2)* | **Dinámicas** | Random-mutate |

Elige un paso con notas (pads 1-16) y toca un pad de la fila 3 o 4.
- **Random-mutate** *(desde RC2)* (pads 25-32): nada · 6 % octava · 6 % escala · 6 % ambas · 12 % escala · 12 % octava · 25 % escala · 25 % octava y 50 % escala. «Escala» = otra nota de la escala en la misma octava, «octava» = una arriba o abajo. Sin Record cambia solo esa vez; con Record se escribe (la secuencia deriva). Las notas ligadas no cambian; cada nota de un acorde se sortea aparte.
- **Dinámicas** *(desde RC2)* (pads 17-24): nada · borracho (±2 micropasos) · borracho + acentos · acentos (velocity 0…+32) · arrastrado + acentos (−1…+3) · arrastrado · equilibrado (velocity ±32) · dinámica de acentos (−32…+64). Con Record y el modo 2 en pantalla, lo que suena se escribe en el patrón.
- **Drums** *(desde RC2)*: la misma vista para un drum (Pattern Settings dos veces = modo 1, pad 25 = modo 2). Frecuencia y dinámicas como arriba (un drum solo se puede retrasar dentro de su paso); pads 25-28 = **random-mutate del sample**: nada · 25 % ±1 (el sample de al lado en su fila de 8) · 25 % ±8 (la misma columna en otra fila) · 12 % de cada uno.

### Vista Micro Step *(desde RC2)*
Pulsa **Gate** dos veces (Gate una vez es la vista Gate de stock). Como en stock: pads 17-22 = los 6 micropasos del paso elegido, **pad 24 = Tie** (un toggle: enlaza las notas elegidas con el paso siguiente), pads 25-30 = las notas del paso (tocar una la elige y la hace sonar). **Cada nota tiene un solo micropaso:** tocar otro lo mueve ahí; para varias en el paso, pon varias notas (en los drums sí se encienden varios: repeticiones). Añadido:
- **Pad 32 = gate por pulsación** (verde): al introducir notas a mano, lo que mantienes el pad es la duración de la nota.
- **Pad 31 = longitud fija** (naranja): con los dos apagados abre un selector (pads 17-32 = 1-16 pasos); elegir una longitud lo enciende, y toda nota introducida a mano la toma.
- Con uno encendido, pulsarlo otra vez lo apaga; pulsar el otro cambia.

### Cadenas de patrones y escenas *(desde RC2)*
- **Modo cadena** de todo el proyecto: en la vista Patterns, **Shift + Octave ▲** lo enciende (Octave ▲ verde), **Shift + Octave ▼** lo apaga (las reglas se quedan guardadas).
- **Editar una regla** (modo encendido): un patrón = **A** (amarillo); A otra vez = una reproducción más (hasta 8; los LEDs de los knobs cuentan); otro patrón de la pista = **B** (verde), el siguiente = **C** (rojo). n = 3 toca A A A B A A A C; B y C suenan una vez y la pista vuelve a A.
- **Clear + patrón:** en el modo, quita la regla; fuera, borra el patrón con su regla y su orden.
- **Escenas:** una escena guardada en modo cadena se ve melocotón y al cargarla vuelve el modo. En el Mixer, **Shift + pads 9-16** = 1-8 repeticiones de la escena actual (solo Beta 3.22: sonando, con Shift, la que suena en blanco); las pistas que siguen una regla parpadean.
- **Entradas al compás** *(desde RC2)*: en el Mixer, **Shift + pad de pista (1-8)** la silencia o la activa al empezar el compás siguiente (parpadea mientras espera; otra vez lo cancela).
- **Modo cue** *(desde RC2)*: en la página de panorama del Mixer (Octave ▼), **Shift + knob a la derecha** lo enciende (Octave ▼ rosa) y **a la izquierda** lo apaga. Por la salida izquierda va la mezcla en mono; por la derecha, solo las pistas que mandas al cue con su knob de panorama (del centro a la derecha). Sirve para escuchar una pista silenciada antes de meterla: suena a tempo solo por la derecha.

<a id="scales"></a>
## 12. Escalas y la escala propia

**Scales** funciona como siempre (tónica y escala de stock). *(desde RC2)* **Shift + Scales** abre el **editor de la escala propia** (el botón Scales se ve amarillo con Shift):
- Los pads son dos octavas de un piano desde la tónica: fila 4 = las teclas blancas de la primera octava, fila 3 sus teclas negras, filas 2 / 1 la segunda octava.
- Pulsa una tecla para añadirla o quitarla (hasta 7). La **tecla más alta es el periodo**: la tónica de la iteración siguiente (no tiene por qué ser una octava). La tónica se ve blanca, las notas verdes, el periodo naranja.
- En las pistas de notas cada fila de pads es una iteración (dos por fila con 4 notas o menos). También decide qué notas se encienden, la cuantización y el random-mutate.
- Elegir una escala de stock apaga la escala propia (las teclas se conservan). Se guarda con el proyecto.

<a id="metronome"></a>
## 13. Metrónomo y cuenta atrás

*(desde RC2)* **Shift + Clear** recorre cuatro estados, que muestra el LED de Clear mientras Shift está pulsado: **rojo** = sin metrónomo, **verde** = metrónomo, **magenta** = solo cuenta atrás, **cian** = cuenta atrás y metrónomo.
- **Cuenta atrás:** con Record armado y el transporte parado, **Play** da un compás de cuatro clics al tempo del proyecto (Record parpadea) y luego empieza a grabar. Play durante la cuenta la cancela.
- El volumen del clic es el de stock: pulsa **Tempo / Swing** y gira **K5**. La cuenta atrás se guarda con el proyecto.

<a id="setup"></a>
## 14. Setup y MIDI

| Dónde | Qué hace |
|---|---|
| Setup, **pad 16** | Canal 16 para el proyecto y los FX: recibir y enviar (todo lo que no es Program Change). |
| Setup, **pads 22 / 23** | Mandar el retorno de reverb (crema) por la tira 3 / el de delay (melocotón) por la tira 4. |
| Setup, **canales compartidos** | MIDI 1 / 2 pueden usar el canal de otra pista: lo que envían llega también a esa pista por dentro. |
| Setup, **Record** *(desde RC2)* | Amarillo = lo que una pista MIDI envía a un sinte por un canal compartido se graba también en ese sinte. Apagado por defecto y tras apagar el aparato. *(Solo Beta 3.22)* En amarillo, una pista de notas silenciada en el Mixer no se graba: sus pasos suenan y se graban solo en el sinte (un banco de acordes). |
| Setup, **pads 29 / 30** *(desde RC2)* | Los canales de **Program Change** del proyecto: escucha (29) y envío (30), 16 por defecto. El primer toque enseña el canal en los pads 1-16; un pad lo elige; otra vez = encendido / apagado. Lo que llega se reenvía por el canal de envío. |
| Setup, **K4 / K5-K8** | *Solo Beta 3.22:* **modo General MIDI** de los drums: K4 a la derecha lo enciende; K5-K8 eligen la nota que manda cada drum (35-81; de fábrica 36 bombo, 38 caja, 42 y 46 charles) por el canal de drums. Cada nota nueva suena una vez y su número se ve en los pads; Shift o salir de Setup lo confirma; K4 a la izquierda lo apaga y cierra el número. |
| Advanced Setup, **pad 23** | *Solo Beta 3.22:* **fusión USB**: lo que tocas en un teclado conectado al DIN In sale también por USB al ordenador, junto al MIDI del aparato (verde = encendida). |
| Advanced Setup, **Duplicate** *(desde RC2)* | La toma MIDI Thru: Thru (rojo tenue) → Out 2 (verde) → **Merge** (amarillo: la DIN In más el MIDI del aparato) → **Filter** (azul: la DIN In sin los canales que escucha el aparato). Sin SysEx en Merge / Filter; con Merge, apaga Clock Tx para no tener dos relojes. |

- **Fallo conocido de RC0.9:** abriendo Setup desde la vista de Synth 1 / 2, no se puede elegir el canal de ese sinte: abre Setup desde otra vista. *(desde RC2)*: arreglado.

<a id="projects"></a>
## 15. Proyectos y packs

### Copiar proyectos *(desde RC2)*
En la vista Projects: **Duplicate + pad A** = la fuente (parpadea amarillo; Duplicate + A otra vez la olvida), **Duplicate + pad B** = la copia. Un B vacío se escribe al momento; un B ocupado parpadea blanco y repites Duplicate + B en ~5 s. El hueco del proyecto cargado nunca se escribe. **A otro pack:** elige la fuente, carga el otro pack, vuelve a Projects y Duplicate + B. Guarda antes: copia lo que hay en la tarjeta, y el aparato no responde un momento mientras copia. Un proyecto guarda números de patch y de sample, no los sonidos: en otro pack suena con los patches y samples de ese pack.

### Borrar un pack
En la vista de packs (**Shift + Projects**) toca **Clear**: durante ~5 s parpadean los packs que se pueden borrar (nunca el cargado ni el de la memoria interna). Toca el pack y luego **Clear** otra vez en 5 s. El hueco se puede reutilizar tras reiniciar. No en la versión más segura.

<a id="saved"></a>
## 16. Qué se guarda y dónde

| Dónde | Qué |
|---|---|
| **El proyecto** | Los knobs nuevos de drums, los huecos de Master FX, la fuente del sinte, los ajustes de reverb / delay; *(desde RC2)* también los knobs y el compresor de Master FX, el modo cadena y las escenas, la cuenta atrás, el arpegiador, la escala propia, el gate por pulsación / longitud fija, los knobs del sidechain, la página 2 y el toggle del step-drummer. |
| **El patrón** | Las notas y valores del step-drummer, los valores del secuenciador de efectos; *(desde RC2)* reglas de cadena, orden de reproducción, frecuencia, dinámicas, random-mutate (también de drums), rollers y arpegios de drums grabados. |
| **El pack** (al guardar) | Las capturas usadas como drums; *(desde RC2)* los patches de sinte guardados, los patches del sinte propio. |
| **Ajustes del aparato** | El motor de las pistas MIDI (pad 27, páginas 1-2), el step-drummer encendido / apagado; *(desde RC2)* el modo MIDI Thru, los canales de Program Change. |
| **No se guarda** | Los valores de OSC 2, los parámetros con Shift del granular, los efectos fijados, el song pointer, el toggle Record del Setup, la propia captura (salvo que haya sustituido a un drum). |

<a id="not"></a>
## 17. Lo que el mod no hace

- Los patrones siguen teniendo como mucho 32 pasos, y una pista no puede cambiar de tipo; lo más parecido es una pista MIDI con un motor (sección 10).
- Las herramientas de desarrollo (versiones de diagnóstico, interioridades del DSP) quedan fuera de esta guía: ver las notas técnicas del repositorio.

### Fallos conocidos de RC0.9 (arreglados en RC2)
- Los drums pueden sonar distinto que en un Circuit de stock en proyectos nuevos o sin tocar (modo de filtro DJ): Shift + K5 a EQ tilt.
- Con Setup abierto desde la vista de Synth 1 / 2 no se puede elegir ese sinte: abre Setup desde otra vista.
- La parte izquierda del K3 de drums (inicio del sample) está en estudio.
- En betas anteriores el delay tartamudeaba al mover los knobs o los modos del motor MIDI: arreglado desde Beta 1.12.

<a id="midiref"></a>
## 18. Referencia MIDI

Todo lo nuevo sale y entra por CC / NRPN, según los filtros CC Tx / Rx del Setup. Tablas completas: la [referencia MIDI](https://ghillermo.github.io/CIRCUIT-HACKS-RC/midi.html).
- **Drums** (canal de drums): NRPN MSB 5-8 = Drums 1-4; LSB 1 envolvente de tono, 2 frecuencia del ring, 3 LFO, 4 velocidad del LFO, 5 envolvente → corte, 6 resonancia, 7 forma de la envolvente, 8 cantidad del ring, 9 modo del filtro, 10 punto de inicio, 11 bitcrush, 12 tipo de distorsión; *(desde RC2)* 13 corte, 14 ataque.
- **Master FX** (canal 16): NRPN MSB 9, LSB = 4 × efecto + knob: Gater 0-3, Auto-Filter 4-7, Digitise 8-11, Phaser 12-15, Glitch 16-19 (en RC0.9, Vinyl).
- **Motor de las pistas MIDI** (canal de la pista): filtro CC 74, resonancia 71, envolvente → filtro 79, ataque 73, decay 75, sustain 70, release 72, efecto 91, ganancia 59, afinación 26, fina 27, wave 20, shape 21, afinación 2 37, fina 2 39, wave 2 30, shape 2 31, mezcla 52, ring 54, velocidad del LFO NRPN 0:76; el resto NRPN MSB 4.
- **Program Change** *(desde RC2)*: los canales de escucha / envío del proyecto en el Setup (pads 29 / 30); el patch flip por el canal de la pista.

<a id="edition"></a>
## 19. Sobre esta edición

Corregido respecto a la guía de la comunidad: el instalador no descarga el firmware oficial (se lo das tú); RC0.9S no tiene diagnósticos remotos que quitar (ninguna versión los lleva desde SC36.1); la captura no sobrevive al apagado salvo que haya sustituido a un drum y se haya guardado el proyecto; el Nudge parte del primer paso elegido en Pattern Settings (la guía original no encontraba la secuencia); se distinguen las tres formas de abrir la vista de probabilidad (stock, modo 1, modo 2) y se marca lo que solo está en la beta (random-mutate, Nudge, órdenes); vuelven los nombres originales (captura, step-drummer); se listan los fallos conocidos de RC0.9. Añadido: todo lo posterior a Beta 1.3 (metrónomo y cuenta atrás, arpegiador de notas y de drums, escala propia, gate por pulsación y longitud fija, rollers de drums, el K3 partido de drums, los knobs del sidechain, la página 2 y el toggle pitch-vel del step-drummer, frecuencia / dinámicas / random-mutate en los drums, canales de Program Change, borrar la automatización del motor MIDI, los arreglos de grabación).
