# CIRCUIT-HACKS — guiones de los vídeos tutoriales

Un vídeo por cada vista del aparato, en el orden de la [guía por vistas](GUIA.md). Cada guion dice **qué contiene la vista**, **cómo se usa cada función** (qué enseñar y qué decir) y **qué hay que tener en cuenta**. Si un guion y la guía no coinciden, manda la guía: es la referencia.

**Versiones.** Los guiones siguen la **RC4.11** (la versión publicada actual). Marcas:

- **[Beta]** = solo en la Beta (publicada: Beta 5.56). Déjalo fuera de un vídeo de la RC, o di que es solo de la Beta.
- **[Beta, sin publicar]** = en las betas de desarrollo posteriores a la 5.56, todavía sin publicar. Grábalo solo cuando salga.
- **Las versiones S** (RC4.11S) no escriben nada propio en la tarjeta: lo que un guion marca como *escribe en la tarjeta* no hace nada en ellas (el LED de Save se pone rojo).

**En todos los vídeos**

- Graba en un **pack de la microSD**, no en el pack interno (el primero): el mod nunca escribe en el pack interno.
- Ten un proyecto llamado, por ejemplo, `TUTORIAL`, con un ritmo corto en los drums, una línea de bajo en Synth 1 y acordes en Synth 2. Guárdalo antes de cada vídeo para poder volver a él.
- Filma los pads y los knobs desde arriba, con la luz de la sala baja: los colores de los LEDs llevan casi toda la información. Ayuda superponer un pequeño mapa de los pads (pads 1-32, K1-K8).
- Di las convenciones una vez por vídeo, o ponlas en un rótulo: **pads 1-32** desde arriba a la izquierda (fila 1 = 1-8, fila 2 = 9-16, fila 3 = 17-24, fila 4 = 25-32); **K1-K4**, los knobs de arriba, y **K5-K8**, los de abajo; **Shift + X** = mantener Shift mientras usas X (lo mismo con Clear y Duplicate).
- La vista de efectos del master se llama siempre **Master FX**.
- Las duraciones son aproximadas. Las vistas largas tienen títulos de capítulo: se pueden cortar en partes.

## La serie

| # | Vídeo | Guía |
|---|---|---|
| 00 | Primeros pasos: versiones, instalación y convenciones | [A.1](GUIA.md#instalar), [0.1](GUIA.md#convenciones) |
| 01 | Botones que funcionan en todas las vistas | [0.2](GUIA.md#botones) |
| 02 | Vista Setup | [1.1](GUIA.md#setup) |
| 03 | Vista Advanced Setup | [1.2](GUIA.md#advanced-setup) |
| 04 | Vista de pista de Synth 1 / 2: Note, Velocity, Gate | [2.1](GUIA.md#synth-nota) |
| 05 | Vista Scales, escala propia y Jankó | [2.2](GUIA.md#escalas) |
| 06 | Vista de la fuente del sinte | [2.3](GUIA.md#synth-fuente) |
| 07 | Vista Preset de Synth 1 / 2 | [2.4](GUIA.md#synth-preset) |
| 08 | Vista Preset de MIDI 1 / 2: el sinte propio | [3.1](GUIA.md#midi-preset) |
| 09 | Voces del sinte propio: polifonía y límite de voces | [3.2](GUIA.md#midi-voces) |
| 10 | Las páginas de knobs del motor | [3.3](GUIA.md#midi-knobs) |
| 11 | Matriz de modulación | [3.4](GUIA.md#midi-matriz) |
| 12 | FM de 4 operadores | [3.5](GUIA.md#midi-fm) |
| 13 | FM de 8 operadores [Beta] | [3.6](GUIA.md#midi-fm8) |
| 14 | Editor de CC de los macros MIDI | [3.7](GUIA.md#midi-cc) |
| 15 | Vista del step-drummer | [3.8](GUIA.md#step-drummer) |
| 16 | Modo muestra y selector de samples | [3.9](GUIA.md#midi-muestra) |
| 17 | Vista Pattern Settings | [4.1](GUIA.md#pattern-settings) |
| 18 | Vista Micro Step | [4.2](GUIA.md#micropasos) |
| 19 | Vista de probabilidad | [4.3](GUIA.md#probabilidad) |
| 20 | Vista de pista de un drum | [5.1](GUIA.md#drum-pista) |
| 21 | Vista Preset de drums | [5.2](GUIA.md#drum-preset) |
| 22 | La vista cromática de los drums y los rollers | [5.3](GUIA.md#drum-cromatica) |
| 23 | Master FX | [6.1](GUIA.md#master-fx) |
| 24 | Vista FX | [7.1](GUIA.md#vista-fx) |
| 25 | Vista Sidechain | [8.1](GUIA.md#sidechain) |
| 26 | Vista Patterns y cadenas de patrones | [9.1](GUIA.md#patterns) |
| 27 | Vista Mixer y escenas | [9.2](GUIA.md#mixer) |
| 28 | Vista Projects | [10.1](GUIA.md#projects) |
| 29 | Vista de packs | [10.2](GUIA.md#packs) |
| 30 | Guardar: qué se conserva y dónde | [11](GUIA.md#datos-patron) |

Los vídeos 00, 01 y 30 no son vistas: abren y cierran la serie.

---

## 00 · Primeros pasos: versiones, instalación y convenciones

**Guía:** [A.1](GUIA.md#instalar), [0.1](GUIA.md#convenciones) · **Duración:** unos 5 min

**Antes de grabar**
- Un ordenador con Chrome, el Circuit Tracks conectado por USB, el firmware oficial 1.2.1 de Novation descargado y la página del instalador abierta.
- Una copia de la tarjeta ya hecha (enséñala; no la hagas delante de la cámara).

**En este vídeo**
- Qué es CIRCUIT-HACKS y qué se queda como en el original.
- Las versiones: RC, RC…S y Beta.
- Instalar, y volver atrás.
- Cómo llama la serie a los pads, los knobs y los gestos.

**Guion**

1. **Gancho.** *Muestra:* un montaje rápido: el sinte propio en MIDI 1, el gesto mecánico de Master FX, la pantalla de acordes. *Di:* «Esto es un Circuit Tracks, pero con más cosas dentro. En esta serie lo recorremos vista a vista: qué hace cada vista, cómo se usa y qué hay que tener en cuenta.»
2. **Qué es.** *Muestra:* el panel frontal del aparato. *Di:* «CIRCUIT-HACKS parchea el firmware oficial 1.2.1 de Novation. Todo lo que hace el original sigue ahí y funciona igual. Los parches añaden funciones a las vistas que ya conoces: lo que no salga en esta serie funciona como dice el manual de Novation.»
3. **Versiones.** *Muestra:* la lista de versiones del instalador. *Di:* «Hay tres tipos de versión. La RC es la estable, la que debes usar para hacer música. La RC con una S al final es su gemela más segura: no escribe nada propio en la tarjeta, así que las funciones que guardan patches, samples o copias no hacen nada ahí. La Beta trae antes que nadie lo más nuevo, y está menos probada. Cuando algo de esta serie sea solo de la Beta, lo verás en pantalla.»
4. **Primero, una copia.** *Muestra:* la copia de la tarjeta en el ordenador. *Di:* «Antes de instalar, copia tu tarjeta. Y con las versiones sin S, ten tus proyectos en un pack de la tarjeta, no en la memoria interna: de todas formas, el mod nunca escribe en el pack interno.»
5. **Instalar.** *Muestra:* el instalador: elegir el fichero del firmware oficial, elegir la versión, enviar; el aparato se reinicia. *Di:* «El instalador parchea el firmware oficial ahí mismo, en el navegador, y lo envía por USB. Elige la versión y envía. El bootloader de Novation no se toca nunca. *Buscar versiones nuevas* añade las versiones publicadas después de tu copia de la página.»
6. **Volver atrás.** *Muestra:* enviar el firmware oficial; después, los tres botones. *Di:* «Para volver atrás, envía otra versión o el firmware oficial. Si algún día el aparato no arranca, mantén Scales, Preset y Note mientras lo enciendes: es el modo de recuperación de la propia Novation, y desde ahí puedes instalar cualquier firmware.»
7. **Convenciones.** *Muestra:* el mapa de pads superpuesto. *Di:* «En esta serie, los pads van del 1 al 32 desde arriba a la izquierda, ocho por fila. K1 a K4 son los knobs de arriba, y K5 a K8, los de abajo. “Shift más pad” quiere decir: mantén Shift y pulsa el pad. Y una regla que vale en todas partes: mientras mantienes Shift, lo que Shift te ofrece se ilumina en amarillo.»
8. **Cierre.** *Di:* «En el siguiente: los botones que funcionan en todas las vistas.»

**A tener en cuenta**
- Instalar reinicia el aparato: lo que no esté guardado se pierde; el proyecto, el pack y los ajustes se quedan.
- Los proyectos y packs guardados con el mod se abren con el firmware oficial: los datos del mod van en partes de los ficheros que el original no lee.
- Una versión S es lo adecuado para quien solo quiere las funciones nuevas para tocar y nada escrito en la tarjeta.

---

## 01 · Botones que funcionan en todas las vistas

**Guía:** [0.2](GUIA.md#botones) · **Duración:** unos 7 min

**Antes de grabar**
- El proyecto `TUTORIAL` sonando; automatización grabada en un knob de un drum y en un macro de Synth 1.

**En este vídeo**
- Clear + knob: volver al valor por defecto, o borrar la automatización.
- Clear + un botón de pista.
- Metrónomo y cuenta atrás (Shift + Clear).
- Cuantizar (Shift + Play).
- Dobles pulsaciones y el teclado partido.
- [Beta] Los botones de pista destellan con las notas; Shift + Preset; [Beta, sin publicar] devolver un patrón a como está en la tarjeta.

**Guion**

1. **Intro.** *Di:* «Hay unos cuantos gestos que funcionan casi en todas partes. Apréndetelos y el resto de la serie será más fácil.»
2. **Clear + knob.** *Muestra:* en la vista de un drum, mantén Clear y gira K1 a la derecha: lavanda; gira K5 a la izquierda: rojo. *Di:* «Mantén Clear y gira un knob a la derecha: vuelve a su valor por defecto y el LED se pone lavanda, como en el original. A la izquierda, en un knob con automatización, borras la automatización de ese knob en el patrón que suena: el LED se pone rojo. Esto funciona en los drums, en el motor de sinte de las pistas MIDI y, solo hacia la derecha, en Master FX.»
3. **Clear + un botón de pista.** *Muestra:* mueve los macros de Synth 1 y luego Clear + Synth 1; después, Clear + Drum 1. *Di:* «Clear más Synth 1 o 2 devuelve sus ocho macros a los del patch cargado. Clear más el botón de un drum borra la automatización de sus knobs en el patrón que suena y deja sus ocho knobs en su valor por defecto.»
4. **Metrónomo y cuenta atrás.** *Muestra:* Shift + Clear cuatro veces, mirando el LED de Clear; después, Record armado + Play. *Di:* «Shift más Clear pasa por cuatro estados: sin metrónomo, en rojo; metrónomo, en verde; solo cuenta atrás, en magenta; y las dos cosas, en verde azulado. Con la cuenta atrás encendida, arma Record y pulsa Play: oyes un compás de clics, Record parpadea y la grabación empieza en el primer tiempo. Si pulsas Play durante la cuenta, la cancelas. El volumen del clic es el de stock: Tempo/Swing, K5.» [Beta] *Di:* «Con el volumen del clic a cero, Clear destella en naranja en cada clic: una cuenta atrás en silencio.»
5. **Cuantizar.** *Muestra:* graba unas notas un poco tarde; mantén Shift (Play amarillo) y pulsa Play (Play verde). *Di:* «Shift más Play cuantiza el patrón de la pista elegida: las notas grabadas en los dos primeros micropasos van al principio de su paso, y las de después, al paso siguiente. En los drums, un paso con varios golpes, un redoble, se queda como está.»
6. **Dobles pulsaciones.** *Muestra:* Scales dos veces; Velocity dos veces; Synth 1 dos veces; MIDI 1 dos veces; Mixer dos veces. *Di:* «Pulsa un botón dos veces y tienes su segunda función: Scales abre el editor de la escala propia, Velocity enciende o apaga la velocity fija, Synth abre la vista de la fuente del sinte, MIDI abre su vista Preset y Mixer abre Master FX. Shift más Synth o MIDI hace lo mismo desde cualquier vista.» [Beta] *Muestra:* mantén Mixer en el Mixer. *Di:* «En la Beta, si mantienes Mixer medio segundo, verás Master FX solo hasta que lo sueltes.»
7. **Teclado partido.** *Muestra:* mantén Synth 1 y pulsa Synth 2; toca las dos mitades; mantén Drum 1 y gira un knob. *Di:* «Mantén el botón de una pista de notas y pulsa el de otra: las dos filas de arriba tocan la primera y las de abajo, la otra, cada una con su escala y su octava. Los knobs son de la primera, pero si mantienes cualquier botón de pista, los knobs son de esa pista hasta que lo sueltas. Un toque corto en un botón de pista cierra el teclado partido.»
8. **[Beta] Shift enseña lo que suena.** *Muestra:* mantén Shift mientras suena el patrón. *Di:* «En la Beta, al mantener Shift, cada botón de pista destella en blanco con cada nota que toca su pista.»
9. **[Beta] Volver al sonido del proyecto.** *Muestra:* retoca Synth 1 y luego Shift + Preset. *Di:* «Shift más Preset devuelve el sonido de esa pista al que guardó el proyecto.»
10. **[Beta, sin publicar] Volver al patrón guardado.** *Muestra:* edita un patrón, Clear + Duplicate (Duplicate parpadea en blanco), Clear + Duplicate otra vez. *Di:* «En cualquier vista de una pista, Clear más Duplicate pregunta, y Clear más Duplicate otra vez devuelve el patrón a como está en la tarjeta desde el último Save. Si Save destella en rojo, no se ha hecho nada: el proyecto no se había guardado nunca, o todavía hay un guardado pendiente.»
11. **Cierre.** *Di:* «Ahora, las vistas, empezando por Setup.»

**A tener en cuenta**
- Primero Clear, luego Shift: Shift + Clear es el metrónomo.
- La cuenta atrás se guarda con el proyecto; el clic encendido / apagado no, como en el original.
- Shift + Play sustituye al Shift + Play del original (otra forma de arrancar la reproducción).
- Scales + Preset + Note al encender es el modo de recuperación de Novation, no un gesto del mod.

---

## 02 · Vista Setup

**Guía:** [1.1](GUIA.md#setup) · **Duración:** unos 6 min

**Antes de grabar**
- Un sinte externo o un ordenador que reciba MIDI, para enseñar los Program Change y las notas General MIDI.

**En esta vista**
- Canales compartidos: una pista MIDI que toca los sintes o los drums del propio aparato.
- Los retornos de reverb y delay por las tiras 3 / 4 del mixer.
- Canales de Program Change (pads 29 / 30).
- Grabar los ruteos internos (Record).
- El teclado externo al arpegiador (Note).
- Drums General MIDI (K4-K8).
- [Beta] Retener knob (Preset) y velocity → amplitud / filtro (K1 / K2).

**Guion**

1. **Abrirla.** *Muestra:* abre Setup como en el original. *Di:* «Setup tiene los canales MIDI y las opciones del aparato, como siempre, y además unas cuantas cosas nuevas.»
2. **Canales compartidos.** *Muestra:* el botón de MIDI 1 y luego el pad del canal de Synth 2; toca el patrón de MIDI 1. *Di:* «Dale a MIDI 1 o 2 el mismo canal que a un sinte o a los drums, y lo que mande la pista MIDI le llega a esa pista por dentro del aparato: una pista MIDI puede tocar Synth 2, por ejemplo. El pad 16 es el canal 16, el del proyecto y los efectos.»
3. **Retornos por las tiras 3 / 4.** *Muestra:* el pad 22 (crema) y el pad 23 (melocotón); después, el Mixer. *Di:* «Los pads 22 y 23 mandan el retorno de la reverb por la tira 3 del mixer y el del delay por la tira 4: los efectos pasan a ser canales con su nivel y su panorama.»
4. **Canales de Program Change.** *Muestra:* toca el pad 29: los pads 1-16 en blanco, elige uno; lo mismo con el pad 30. *Di:* «El pad 29 es el canal en el que el proyecto escucha los Program Change: el primer toque lo enseña en los pads 1 a 16, un pad lo elige y otro toque lo enciende o lo apaga. El pad 30 hace lo mismo con el canal de salida. Los dos empiezan en el 16, y lo que llega por el canal de escucha sale por el de salida.»
5. **Grabar los ruteos.** *Muestra:* Record en amarillo; una pista MIDI cambiando las notas de un sinte por un canal compartido. *Di:* «Con Record en amarillo aquí, lo que una pista MIDI le manda a un sinte por un canal compartido se graba también en ese sinte. Viene apagado y se apaga al reiniciar. Mientras está encendido, una pista de notas silenciada en el Mixer no graba nada: puedes tener ahí un banco de acordes que solo toca el sinte.»
6. **Teclado externo al arpegiador.** *Muestra:* Note en verde; toca un acorde en un teclado externo. *Di:* «Note en verde quiere decir que las notas de un teclado externo, por el canal de una pista, pasan por el arpegiador de esa pista igual que los pads. Viene apagado para no chocar con un teclado que tenga su propio arpegiador.» [Beta] *Di:* «En la Beta, con un paso mantenido, las notas del teclado externo entran en ese paso.»
7. **Drums General MIDI.** *Muestra:* K4 a la derecha (verde); gira K5: el número en los pads y suena el drum; pulsa Shift para confirmar. *Di:* «K4 enciende el General MIDI de los drums: cada golpe sale por MIDI con una nota GM en lugar de la de stock. K5 a K8 eligen la nota de Drum 1 a 4: cada nota nueva suena una vez y su número se ve en los pads. Shift, o salir de Setup, la confirma. Dentro del aparato, los drums suenan igual.»
8. **[Beta] Retener knob.** *Muestra:* Preset en verde; gira un knob del Mixer y cambia de vista a media vuelta. *Di:* «En la Beta, Preset enciende aquí la retención de knobs: un knob que estás girando sigue haciendo lo que hacía, aunque cambies de vista o pulses Shift, hasta que lo dejas quieto un segundo.»
9. **[Beta] Velocity global.** *Muestra:* K1 arriba; notas suaves y fuertes en un patch sin velocity en el amp. *Di:* «K1 da velocity al volumen de los patches que no la tienen, y K2, a su filtro. A cero, el comportamiento del original. Un patch que ya usa velocity no cambia.»
10. **Cierre.** *Di:* «En el siguiente: Advanced Setup.»

**A tener en cuenta**
- Todo lo de aquí es un **ajuste del aparato**: el mismo para todos los proyectos.
- El General MIDI solo cambia lo que sale por MIDI.
- El patch flip sale siempre por el canal de su propia pista MIDI.
- Record (los ruteos internos) vuelve a estar apagado tras cada reinicio.

---

## 03 · Vista Advanced Setup

**Guía:** [1.2](GUIA.md#advanced-setup) · **Duración:** unos 4 min

**Antes de grabar**
- El aparato apagado. Advanced Setup solo se abre al encender (mantén Shift mientras lo enciendes, como en el original).

**En esta vista**
- El jack MIDI Thru: Thru, Out 2, Merge, Filter (Duplicate).
- Fusión USB (pad 23).
- Guardado diferido (pad 22).
- La curva de velocity de los pads (K1; solo en las RC).
- [Beta] Ganancia de las entradas externas (K3).

**Guion**

1. **Abrirla.** *Muestra:* enciende con Shift mantenido. *Di:* «Advanced Setup solo se abre al encender. Además de los ajustes de stock, trae cuatro cosas nuevas.»
2. **Jack Thru.** *Muestra:* Duplicate cuatro veces: rojo tenue, verde, amarillo, azul. *Di:* «Duplicate cambia el modo del jack MIDI Thru: Thru, un thru normal por hardware; Out 2, una segunda salida; Merge, el MIDI que entra más el del propio aparato; y Filter, el MIDI que entra sin los canales que escucha el aparato. Merge y Filter no dejan pasar el SysEx.»
3. **Fusión USB.** *Muestra:* el pad 23 en verde; un teclado por DIN que llega al ordenador. *Di:* «El pad 23 manda también al ordenador, por USB, lo que entra por la entrada DIN, junto con el MIDI del propio aparato. Con Clock Tx encendido no se copia el reloj del DIN, para que el ordenador no reciba dos relojes.»
4. **Guardado diferido.** *Muestra:* el pad 22 en verde; Save dos veces mientras suena: Save parpadea en amarillo; para el transporte: guardado. *Di:* «Guardar con el secuenciador en marcha puede descompasar el reloj un instante. Con el pad 22 encendido, un guardado mientras suena espera a que pares. Si cargas otro proyecto o guardas en otro hueco, se guarda en ese momento.»
5. **Curva de velocity (RC).** *Muestra:* gira K1: el número en los pads y Velocity encendido. *Di:* «En las RC, K1 ajusta la curva de velocity de los pads, de menos 8 a más 8: a la derecha, más sensible; a la izquierda, más dura. El cero es la respuesta del original.»
6. **[Beta] Ganancia de entrada.** *Muestra:* gira K3: los dB en los pads. *Di:* «En la Beta, K3 sube las entradas externas hasta 24 dB, también lo que llega al sinte propio y al granular. Con mucha ganancia, satura. En la Beta ya no hay curva de velocity: la velocity está en K1 y K2 de Setup.»
7. **Cierre.** *Di:* «El ataque y el release del compresor master están en la vista Sidechain, en el vídeo 25.»

**A tener en cuenta**
- Todo esto son ajustes del aparato, que se guardan solos.
- Con un guardado pendiente, para el transporte antes de apagar. Si cambias de pack antes de parar, ese guardado se descarta.

---

## 04 · Vista de pista de Synth 1 / 2: Note, Velocity, Gate

**Guía:** [2.1](GUIA.md#synth-nota) · **Duración:** unos 9 min (capítulos: tocar / la pantalla de acordes / herramientas de automatización)

**Antes de grabar**
- Synth 2 con un patch de pad o de teclado; Synth 1 con una línea de bajo que tenga automatización de macros en algunos pasos.

**En esta vista**
- El teclado partido con cualquier pareja de pistas de notas.
- Fijar notas (Shift + tecla) y escribirlas en un paso.
- La pantalla de acordes.
- Vista Velocity: pasos que sueltan la automatización.
- [Beta] Escuchar y borrar la automatización de un paso, sweeps y la foto de los macros en un paso.

**Guion**

*Capítulo 1: tocar*

1. **Intro.** *Di:* «La vista de pista del sinte se toca como siempre. Esto es lo nuevo.»
2. **Atajo a la vista de la fuente.** *Muestra:* pulsa Synth 1 otra vez. *Di:* «Si vuelves a pulsar el botón de la pista, se abre la vista de la fuente del sinte. Eso lo vemos en el vídeo 6.»
3. **Teclado partido.** *Muestra:* mantén Synth 1 y pulsa MIDI 1; toca; mantén Drum 2 y gira un knob. *Di:* «Mantén el botón de una pista de notas y pulsa otro: Synth 1, Synth 2, MIDI 1 o MIDI 2, cualquier pareja. La pista que mantuviste primero toca arriba. Y cualquier botón de pista que mantengas te presta sus knobs mientras no lo sueltes.»
4. **Latch.** *Muestra:* Shift + una tecla; suéltala: sigue sonando; vuelve a pulsarla: se para. *Di:* «Shift más una tecla fija la nota: sigue sonando cuando la sueltas. La siguiente vez que pulses esa nota, se para. Mientras mantienes Shift, las notas fijadas se ven en verde azulado brillante.»
5. **Notas fijadas en un paso.** *Muestra:* dos notas fijadas; Shift + paso 5 en la vista Note. *Di:* «Con notas fijadas, Shift más un paso las escribe en ese paso: un paso de largo, velocity 100. Clear más el botón de la pista suelta todo lo fijado.»

*Capítulo 2: la pantalla de acordes*

6. **Abrirla.** *Muestra:* Note dos veces (vista Note ampliada), Shift + pad 8: verde. *Di:* «En la vista Note ampliada, Shift más el pad 8 abre la pantalla de acordes.»
7. **Las filas.** *Muestra:* los tipos de la fila 1; Shift + fila 1 para ver más; pads 9-12, inversiones; pads 13-15, modificadores; filas 3-4, fundamentales. *Di:* «La fila 1 es el tipo de acorde: mayor, menor, séptima y más; con Shift, siete más, como sus2 o add9. Los pads 9 a 12 son la inversión. El pad 13 abre el voicing, el 14 añade la fundamental una octava abajo y el 15 construye el acorde con la escala del proyecto. Las filas 3 y 4 son las fundamentales, colocadas como el teclado de la vista Note.»
8. **Cambios al momento.** *Muestra:* mantén una fundamental y cambia el tipo y la inversión. *Di:* «Si cambias el tipo o la inversión mientras suena un acorde, cambia al momento: no hace falta volver a pulsar la fundamental. Y dos acordes a la vez comparten las notas que tienen en común.»
9. **Latch del acorde y grabación.** *Muestra:* Shift + una fundamental (verde azulado); graba unos acordes con Record; reprodúcelos sin la pantalla. *Di:* «Shift más una fundamental fija el acorde entero. Lo que tocas se graba como notas normales, así que suena igual sin la pantalla de acordes. Con el arpegiador encendido, tocas un acorde arpegiado con un solo dedo.» [Beta] *Muestra:* el pad 16. *Di:* «En la Beta, el pad 16 es el acorde inverso: el acorde reflejado hacia abajo desde la fundamental.»

*Capítulo 3: herramientas de automatización*

10. **Pasos que sueltan la automatización.** *Muestra:* vista Velocity, mantén Shift: los pads de paso en amarillo; Shift + un paso: rojo. *Di:* «En la vista Velocity, Shift más un paso lo marca en rojo: en ese paso no suena ninguna automatización, y todo lo que la automatización había movido vuelve a los valores del proyecto: los macros del patch tal como los guardó el proyecto. Púlsalo otra vez para desmarcarlo. Se guarda con el patrón.»
11. **[Beta] Escuchar y borrar.** *Muestra:* mantén Shift: solo los pasos con automatización en amarillo; Shift + un paso amarillo; suelta Shift; Clear + un paso. *Di:* «En la Beta, con Shift, solo se ven en amarillo los pasos que tienen automatización. Shift más un paso amarillo pone su automatización en los knobs y en el sonido, y al soltar Shift todo vuelve a como estaba. Clear más un paso borra la automatización de sus knobs y deja sus notas.»
12. **[Beta] Sweep.** *Muestra:* mantén un paso amarillo y pulsa otro paso amarillo. *Di:* «Mantén un paso amarillo y pulsa otro: cada carril con valor en los dos extremos se convierte en una línea recta entre ellos.»
13. **[Beta] Foto.** *Muestra:* mueve dos macros; Record mantenido + paso 9 (se ilumina en amarillo). *Di:* «Record mantenido más un paso escribe en ese paso los macros que no están donde los guarda el patch, cada uno en su carril.»
14. **Cierre.** *Di:* «En el siguiente: las escalas, y cómo hacer la tuya.»

**A tener en cuenta**
- El tipo y los modificadores de la pantalla de acordes, las notas fijadas y el teclado partido no se guardan.
- «Los valores del proyecto» son el patch tal como lo guardó el proyecto: girar knobs después no lo cambia; elegir otro patch, sí.
- En MIDI 1 / 2 con el modo muestra, la vista Note ampliada es el selector de samples, no la pantalla de acordes.

---

## 05 · Vista Scales, escala propia y Jankó

**Guía:** [2.2](GUIA.md#escalas) · **Duración:** unos 6 min

**Antes de grabar**
- Una melodía corta en Synth 1 y random-mutate en algunos pasos (para enseñar que la escala lo manda).

**En esta vista**
- La escala propia: hasta 7 notas y un periodo libre.
- Cómo la colocan las pistas de notas.
- Jankó, un teclado isomórfico.

**Guion**

1. **Abrir el editor.** *Muestra:* Scales dos veces (o Shift + Scales). *Di:* «Scales funciona como siempre: tónica y escalas de stock. Púlsalo dos veces, o Shift más Scales, y tienes el editor de la escala propia.»
2. **El teclado.** *Muestra:* el mapa de pads: fila 4, teclas blancas; fila 3, teclas negras; filas 2 / 1, la segunda octava. *Di:* «El editor son dos octavas de piano a partir de la tónica: la fila de abajo son las teclas blancas de la primera octava; la de encima, sus negras; y las dos filas de arriba, la segunda octava.»
3. **Hacer una escala.** *Muestra:* pulsa teclas: notas en verde, tónica en blanco, periodo en azul. *Di:* «Pulsa hasta siete teclas. La más alta es el periodo: donde la escala vuelve a empezar. No tiene por qué ser la octava. Una escala que se repite cada siete semitonos, por ejemplo, vale.»
4. **En las pistas de notas.** *Muestra:* la vista Note de Synth 1. *Di:* «En las pistas de notas, cada fila es una vuelta de la escala, que termina en la nota del periodo. Con cuatro notas o menos caben dos vueltas por fila. Octave mueve una fila.»
5. **Qué controla.** *Muestra:* la secuencia iluminando las teclas correctas; el random-mutate dentro de la escala. *Di:* «La escala propia también decide qué teclas se iluminan mientras suena la secuencia, el cuantizado y qué notas puede elegir el random-mutate.»
6. **Volver a stock.** *Muestra:* elige una escala de stock; vuelve al editor: las teclas siguen ahí. *Di:* «Elegir una escala de stock apaga la propia, pero conserva tus teclas: abre el editor y ahí está otra vez. Se guarda con el proyecto.»
7. **Jankó.** *Muestra:* en el editor, Shift + pad 8 (verde azulado); después, la vista Note; toca la misma forma de acorde en dos tonos. *Di:* «Shift más el pad 8 en el editor enciende Jankó: cada columna sube un tono, y las filas van por parejas, la de arriba medio tono más grave. Un acorde tiene la misma forma en cualquier tono. Octave: un toque mueve el teclado medio tono; si lo mantienes medio segundo, una octava.»
8. **[Beta] Mover una sola pareja.** *Muestra:* vista Note ampliada, mantén una tecla y pulsa Octave. *Di:* «En la Note ampliada de la Beta, la pareja de arriba repite la de abajo, y con una tecla mantenida, Octave mueve solo la otra pareja. Si mantienes teclas en las filas 2 y 4, se mueven solo las filas 1 y 3.»
9. **Cierre.** *Di:* «En el siguiente: la vista de la fuente del sinte.»

**A tener en cuenta**
- Un proyecto nuevo empieza sin escala propia.
- En las RC, Shift + pad 24 en el editor enciende una disposición anterior (cada fila un semitono más aguda que la de abajo).
- La distancia entre las parejas de Jankó no se guarda: tras reiniciar, es 0.

---

## 06 · Vista de la fuente del sinte

**Guía:** [2.3](GUIA.md#synth-fuente) · **Duración:** unos 5 min

**Antes de grabar**
- Una guitarra, una voz o un loop de batería en la entrada de audio 1. Un patch de Synth 1 con algo de nivel de ruido (CC 56) y envolvente de filtro.

**En esta vista**
- Las entradas de audio como fuente de ruido del sinte (pads 25-29).
- El editor de los destinos de los macros (pad 32).
- El step-drummer del sinte (pad 30).

**Guion**

1. **Abrirla.** *Muestra:* la vista de Synth 1; pulsa Synth 1 otra vez (o Shift + Synth 1 desde cualquier vista). *Di:* «Pulsa dos veces el botón de un sinte y estás en su vista de la fuente. Cualquier botón la cierra.»
2. **La entrada de audio como ruido.** *Muestra:* el pad 26; toca notas: la entrada, con gate y filtrada. *Di:* «Los pads 25 a 29 sustituyen el ruido del patch: el 25 es el propio ruido; el 26 y el 27, las dos entradas de audio; y el 28 y el 29, las mismas entradas invertidas. Ahora el filtro, las envolventes y los efectos del sinte moldean tu señal externa, al ritmo de las notas.»
3. **La pega.** *Muestra:* el macro de nivel de ruido a cero: silencio; arriba: suena. *Di:* «Para que esto se oiga, el patch necesita algo de nivel de ruido. La elección se guarda con el proyecto. Si en Setup los retornos de reverb o de delay van por las tiras 3 y 4, eso es lo que le llega aquí al sinte.»
4. **Destinos de los macros.** *Muestra:* el pad 32 (verde azulado); gira el macro K1 (LED blanco); Octave ▼ por los campos; los pads dibujando números. *Di:* «El pad 32 abre el editor de macros. Gira un knob para elegir su macro: el primer giro no cambia nada. Cada macro tiene cuatro ranuras, y cada ranura tiene un destino, un inicio, un fin y una profundidad. Octave te mueve entre los campos: ranura, inicio, fin, destino y profundidad. Los pads dibujan el número.»
5. **Oírlo y conservarlo.** *Muestra:* gira el macro: se mueve el destino nuevo. *Di:* «Los cambios suenan al momento. Para conservarlos en el pack, guarda el patch desde la vista Preset: eso lo vemos en el siguiente vídeo.»
6. **El step-drummer del sinte.** *Muestra:* el pad 30; pad 17 = macro 1; gira K1-K8. *Di:* «El pad 30 abre el step-drummer del sinte: los pads 17 a 24 eligen qué macro mueve, y los ocho knobs fijan ese macro en ocho pares de pasos. Play y Record no lo cierran, y si te vas a otra vista, al pulsar Synth 1 vuelve. Funciona como el step-drummer de las pistas MIDI, el del vídeo 15.»
7. **Cierre.** *Di:* «En el siguiente: la vista Preset del sinte.»

**A tener en cuenta**
- La lista de destinos recorre primero los 31 parámetros con CC y luego los 39 que solo tienen NRPN.
- El step-drummer escribe sus valores como automatización: son parte del patrón.

---

## 07 · Vista Preset de Synth 1 / 2

**Guía:** [2.4](GUIA.md#synth-preset) · **Duración:** unos 7 min (capítulos: guardar y copiar / [Beta] categorías / [Beta] morph de patches)

**Antes de grabar**
- Un pack de la tarjeta con huecos de patch libres, y un segundo pack al que copiar.

**En esta vista**
- Guardar un patch desde el aparato.
- Intercambiar y copiar patches, también a otro pack.
- [Beta] Colores por categoría de Components.
- [Beta] Morph de patches.

**Guion**

*Capítulo 1: guardar y copiar*

1. **Intro.** *Di:* «El original solo puede guardar patches desde Components. Aquí los guardas en el propio aparato.»
2. **Guardar.** *Muestra:* retoca el sonido; Clear + un pad: parpadea en blanco; Clear + el mismo pad: guardado. *Di:* «Clear más un pad pregunta; Clear más el mismo pad antes de cinco segundos guarda el sonido tal como está ahora: knobs, MIDI recibido y destinos de los macros. Otro pad mueve la pregunta.»
3. **Intercambiar.** *Muestra:* Duplicate + pad A + pad B. *Di:* «Duplicate más dos pads intercambia dos patches de este pack.»
4. **Copiar a otro pack.** *Muestra:* Duplicate + A; carga otro pack; Duplicate + B. *Di:* «Para copiar un patch a otro pack: Duplicate más el patch, carga el otro pack y luego Duplicate más el hueco. El pack de origen no cambia.»

*Capítulo 2: [Beta] categorías*

5. **Colores.** *Muestra:* la vista Preset en color. *Di:* «En la Beta, cada patch se ve en el color de su categoría de Components: Bass en azul acero, Lead en amarillo, Pad en azul, y así con todas. Los huecos vacíos, en blanco tenue.»
6. **Elegir la categoría al guardar.** *Muestra:* Clear + pad; gira K1 por las categorías; confirma. *Di:* «Mientras un guardado pregunta, K1 elige la categoría. Confirma y se guarda con ella.»

*Capítulo 3: [Beta] morph de patches*

7. **Entrar.** *Muestra:* mantén tres patches medio segundo. *Di:* «Mantén de dos a cuatro patches un momento y se abre la vista del morph: el sonido pasa por los patches que has mantenido, en el orden de los pads.»
8. **Los knobs.** *Muestra:* barrido con K1; K2 y K3; K4; K7 / K8 con los pads 1 / 8. *Di:* «K1 es la posición en la cadena. K2 añade un LFO cuadrado y K3 marca la velocidad de los dos LFO; K4 es un LFO de pasos al azar. K7 y K8 son una envolvente: los pads 1 y 8 la disparan y, si los mantienes, la sostienen.»
9. **Morph lento.** *Muestra:* gira K5 y déjalo; K6 para la duración. *Di:* «K5 es el destino de un morph lento: déjalo quieto medio segundo y el sonido viaja hasta ahí en el tiempo de K6, que va de instantáneo a 32 compases. K1 y K5 enseñan los patches como colores: rojo, amarillo, verde y azul.»
10. **Salir y volver.** *Muestra:* el pad 32; Preset; el botón de la pista. *Di:* «El pad 32 sale. Preset enseña los patches, con la cadena en blanco. El morph sigue en las otras vistas; el botón de la pista te devuelve a la vista del morph. Un morph a la vez: si empiezas uno en otra pista, el primero se para.»
11. **Cierre.** *Di:* «Hasta aquí los sintes de stock. En el siguiente: el sinte propio de las pistas MIDI.»

**A tener en cuenta**
- Guardar *escribe en la tarjeta*: no en las versiones S ni en el pack interno (Save se pone rojo).
- Un patch guardado conserva el nombre del patch que estaba cargado.
- En las RC, los colores de los patches son los del original: el color de la pista, y el elegido en blanco.
- [Beta] El morph no se guarda; los parámetros continuos se mezclan, y los de tipo (onda, modo) toman los del patch más cercano.

---

## 08 · Vista Preset de MIDI 1 / 2: el sinte propio

**Guía:** [3.1](GUIA.md#midi-preset) · **Duración:** unos 12 min (capítulos: motores y páginas / patches / modos de voz / patch flip y el secuenciador de saltos)

**Antes de grabar**
- MIDI 1 con una melodía corta. Un pack con algunos patches del sinte propio guardados, un hueco vacío y un segundo pack.
- Un teclado externo en el canal de MIDI 1, para el último capítulo.

**En esta vista**
- Un sinte dentro de cada pista MIDI, con varios motores.
- Las páginas de knobs, el modo de voz y el orden de la cadena.
- Patches del sinte propio: 128 huecos por pack.
- Patch flip; [Beta] el secuenciador de saltos.
- Tocar el sinte propio desde un teclado externo.

**Guion**

*Capítulo 1: motores y páginas*

1. **Intro.** *Di:* «MIDI 1 y MIDI 2 siguen mandando MIDI a tus aparatos. Pero ahora cada una tiene además un sinte dentro del aparato, y vive en esta vista.»
2. **Abrirla.** *Muestra:* MIDI 1 y luego Preset; después, MIDI 1 dos veces desde su vista Note. *Di:* «Pulsa MIDI 1 y luego Preset. O pulsa MIDI 1 dos veces, o Shift más MIDI 1 desde cualquier vista.»
3. **La fila de motores.** *Muestra:* toca el pad 27: la fila en los pads 17-24; elige el oscilador (verde); el pad 27 otra vez cierra la fila. *Di:* «Un toque al pad 27 abre la fila de motores: apagado, entrada de línea, oscilador, VA-drum, granular, muestra, secuenciador de efectos y, en el pad 24, FM. Elige uno; el pad 27 otra vez te devuelve la lista de patches.» [Beta] *Di:* «En la Beta, la fila es: sin voz, solo VCA / VCF / FX, oscilador, VA-drum, wavetable, muestra, granular y FM. El secuenciador de efectos pasa al pad 31.»
4. **Qué es cada motor.** *Muestra:* unas notas con cada motor. *Di:* «La entrada de línea pasa tu entrada de audio por el filtro y el VCA, y las notas la disparan. El oscilador pasa poco a poco de seno a cuadrada, con un segundo oscilador. El VA-drum es para golpes de percusión. El granular toca granos de un sample. El modo muestra toca un sample del pack a la altura de la nota. FM es un sinte FM de cuatro operadores. Y el secuenciador de efectos no suena: dispara huecos de Master FX en sus pasos.»
5. **Páginas de knobs.** *Muestra:* los pads 1-5 y el 6; mantén el pad 3 medio segundo y suéltalo. *Di:* «Los pads 1 a 5 eligen qué hacen los knobs: filtro y VCA, oscilador 1, oscilador 2, los knobs secuenciables y la modulación. El pad 6 es la matriz de modulación. Si mantienes un pad de página medio segundo, esa página se ve solo hasta que lo sueltas. Clear más un pad de página devuelve esa página a sus valores por defecto.» [Beta] *Di:* «En la Beta, los pads 1 y 4 cambian de sitio: el pad 1 son los knobs secuenciables.»
6. **Pads 28-31.** *Muestra:* cada pad. *Di:* «El pad 28 añade el segundo oscilador. El pad 29 cambia el orden de la cadena: VCA, efecto y filtro, o el filtro primero. El pad 30 abre el step-drummer, y Shift más el pad 30 lo desactiva. El pad 31, en el VA-drum, hace que la velocity mueva sus envolventes de tono y de filtro.»

*Capítulo 2: patches del sinte propio*

7. **Cargar.** *Muestra:* toca pads de las filas 2-3: suena la tónica; Octave por las páginas; Shift + un pad. *Di:* «Las filas 2 y 3 son huecos de patch para este sinte: dieciséis por página, ocho páginas con Octave, 128 por pack, compartidos por MIDI 1 y MIDI 2. Toca un hueco para cargarlo; la tónica suena mientras lo mantienes. Shift más un hueco lo carga sin que suene.»
8. **Guardar.** *Muestra:* Clear + un hueco vacío, Clear + el mismo hueco. *Di:* «Clear más un hueco, dos veces, guarda ahí el sonido: el motor, todos los valores, el modo de voz y la matriz.»
9. **Intercambiar y copiar.** *Muestra:* Duplicate + A + B; después, Duplicate + A, otro pack, Duplicate + B. *Di:* «Duplicate más dos huecos los intercambia. Para copiar un patch a otro pack: Duplicate más el patch, carga el otro pack y Duplicate más un hueco. Duplicate se queda en amarillo mientras hay una copia esperando.»
10. **Empezar de cero.** *Muestra:* Clear + MIDI 1. *Di:* «Clear más MIDI 1 devuelve todos los valores del motor a los de por defecto; el motor elegido se queda.»

*Capítulo 3: modos de voz*

11. **La fila.** *Muestra:* toca el pad 32: los modos en los pads 17-24. *Di:* «El pad 32 abre los modos de voz: retrigger, legato, glide, cuatro modos de unísono y poly. Los modos que se llaman igual comparten color.»
12. **Escucharlos.** *Muestra:* legato; glide con K1; uni retrig con K2; poly con un acorde. *Di:* «Legato solo cambia la altura mientras mantienes notas. Glide se desliza entre las notas mantenidas; K1 marca el tiempo. Los modos de unísono apilan las voces en una sola nota; K2 las separa. Poly toca hasta cuatro notas, seis en FM.»
13. **Se guarda.** *Di:* «El modo, el tiempo del glide y la desafinación se guardan con el patch y con el proyecto. Shift más el pad 29 pasa por los modos desde la vista principal.»

*Capítulo 4: patch flip y el secuenciador de saltos*

14. **Patch flip.** *Muestra:* el pad 26 encendido; toca notas hacia un sinte externo. *Di:* «El pad 26 convierte cada nota de la pista en un Program Change por el canal de la pista: tu aparato externo cambia de sonido paso a paso. No funciona a la vez que el motor.»
15. **[Beta] Secuenciador de saltos.** *Muestra:* el pad 26 abre la vista de flip; pad 18 (step flip); elige Synth 1 en la fila 2; en la vista Note de MIDI 1, pads 17-32 = pasos. *Di:* «En la Beta, el pad 26 abre la vista de flip: el pad 17 es el patch flip, y el 18, el step flip. Con step flip, la fila 2 elige la pista destino. Ahora las notas de MIDI 1 no suenan: cada una hace saltar el patrón del destino a un paso. En la vista Note de MIDI 1, los pads 17 a 32 son los pasos 1 a 16. Con el transporte parado, un pad te deja oír ese paso del destino.»
16. **[Beta, sin publicar] Saltos al azar.** *Di:* «Con varias notas en un paso, el salto va a uno de sus pasos al azar, todos con la misma probabilidad.»
17. **Teclado externo.** *Muestra:* toca el teclado externo en el canal de MIDI 1. *Di:* «Un teclado externo en el canal de MIDI 1 toca directamente el sinte propio.»
18. **Cierre.** *Di:* «En el siguiente: cuántas voces tiene el sinte propio y qué pasa cuando se queda sin tiempo.»

**A tener en cuenta**
- Los ajustes del motor se guardan en los ajustes del aparato y, desde RC4, con cada proyecto. Para usar un sonido en cualquier sitio, guárdalo como patch.
- Guardar y copiar patches *escribe en la tarjeta*.
- Con cualquier motor encendido, la pista sigue mandando su MIDI.
- El patch flip y el motor se excluyen; [Beta] el secuenciador de saltos y el motor, también.
- [Beta] El morph de patches funciona aquí también, con los huecos del sinte propio (vídeo 07).

---

## 09 · Voces del sinte propio: polifonía y límite de voces

**Guía:** [3.2](GUIA.md#midi-voces) · **Duración:** unos 5 min

**Antes de grabar**
- El sinte propio de MIDI 1 en FM y en poly, con un patch de release largo; Synth 1 tocando acordes.

**En este vídeo**
- Cuántas voces tiene cada modo y cada motor.
- El robo de voces y el volumen de los acordes.
- El límite de voces, y por qué Synth 1 / 2 conservan las suyas.

**Guion**

1. **Intro.** *Di:* «El sinte propio puede tocar acordes. Vamos a ver cuántas notas, y qué hace el aparato cuando el motor de sonido se queda sin tiempo.»
2. **Las cuentas.** *Muestra:* una tabla en pantalla. *Di:* «Retrigger, legato y glide: una voz. Poly: cuatro voces en el oscilador, el VA-drum y el modo muestra; seis en FM, o tres cada una si MIDI 1 y MIDI 2 están las dos en FM poly. Los modos de unísono usan esas mismas voces en una sola nota. El granular: siempre una voz.»
3. **Robo de voces.** *Muestra:* toca cinco notas en poly. *Di:* «Una nota de más le quita la voz a la nota más antigua, con un fundido de 2 milisegundos. Una nota soltada conserva su voz mientras suena su release: con releases largos, las voces se llenan aunque toques notas sueltas.»
4. **Volumen de los acordes.** *Muestra:* una nota sola y luego un acorde de cuatro notas. *Di:* «Cada voz baja según cuántas suenan, para que los acordes no recorten: una o dos notas, a nivel completo; cuatro, a más o menos 0,7. Un acorde suena más fuerte que una nota, pero no cuatro veces más.»
5. **El límite.** *Muestra:* un pad FM con releases largos y muchas notas; un release que termina antes de tiempo. *Di:* «Todo lo que suena comparte el tiempo del DSP. Si está a punto de acabarse, oirías un traqueteo. Así que, con dos voces propias o más sonando, el aparato lo comprueba cada 2 milisegundos; cuando va justo, apaga la voz que ya se está soltando y suena más bajo o, si no hay ninguna, la nota mantenida más antigua. Después toca con las voces que caben y prueba con una más cada dos segundos.»
6. **Synth 1 y 2 están a salvo.** *Muestra:* acordes de Synth 1 por debajo del sinte propio. *Di:* «Synth 1 y Synth 2 no pierden voces por culpa del sinte propio: cuando falta tiempo, las voces que se van son las del sinte propio.»
7. **Consejos.** *Di:* «Para tener más voces: releases más cortos, menos operadores fuertes en FM, o una sola pista en FM poly. Los modos mono nunca llegan al límite.» [Beta] *Di:* «En la Beta, las voces FM se calculan aparte del resto: seis por pista aunque las dos pistas estén en FM, unas diez voces FM en total.»

**A tener en cuenta**
- Lo que oyes del límite es un release largo que termina antes de tiempo, o la nota más antigua de un acorde que se apaga cuando suena mucho a la vez.
- Cuántas voces caben depende de todo el proyecto: Master FX, muchos drums y patches pesados en Synth 1 / 2 dejan menos tiempo.

---

## 10 · Las páginas de knobs del motor

**Guía:** [3.3](GUIA.md#midi-knobs) · **Duración:** unos 10 min (capítulos: VCA-VCF / osciladores / granular / página 4 y automatización / página 5)

**Antes de grabar**
- El sinte propio de MIDI 1 en el oscilador, con un patrón corto sonando; un sample del pack para el granular.

**En esta vista**
- Página 1: el VCA y el filtro, con su envolvente y su LFO.
- Páginas 2 y 3: los dos osciladores; SHAPE en cada forma de onda.
- La página 2 en el granular.
- Página 4: los knobs que se pueden grabar y, con Shift + pad 4, los que no.
- Página 5: la envolvente, el LFO y la forma del LFO.

**Guion**

*Capítulo 1: VCA-VCF*

1. **Página 1.** *Muestra:* el pad 1; K1-K8, y luego con Shift. *Di:* «La página 1 es el VCA y el filtro. K1 y K2 son el ataque y el release; con Shift, el sustain y el decay. K3 y K4 mandan la envolvente al nivel y al filtro; con Shift, el LFO. K5 es el filtro, y K6, la resonancia; Shift más K5 elige el tipo de filtro, y Shift más K6 es una ganancia del VCA con saturación. K7 es la velocidad del LFO; K8, la cantidad de efecto; y Shift más K8, el tipo de efecto: suave, dura, plegado, wavefold, ring, comb y chorus.»
2. **LFO a tempo.** *Muestra:* K7 a la derecha y luego a la izquierda. *Di:* «K7 es bipolar: a la derecha, un LFO libre; a la izquierda, a tempo, desde tresillos de semicorchea hasta ocho compases, y vuelve a empezar en el primer tiempo del compás.»

*Capítulo 2: osciladores*

3. **Página 2.** *Muestra:* el pad 2; WAVE (K7) por seno, triángulo, sierra y cuadrada; SHAPE (K2). *Di:* «La página 2 es el oscilador 1: TUNE y FINE, después WAVE, que pasa de seno a triángulo, a sierra y a cuadrada, y SHAPE, que hace algo distinto en cada onda.» [Beta] *Di:* «En la Beta, los knobs están colocados de otra forma: WAVE es K3, SHAPE es K4, y K5, K6 y K8 mandan el LFO y la envolvente al FM, al ring y al mix.»
4. **SHAPE.** *Muestra:* SHAPE en el seno (wavefold), en la sierra (supersaw) y en la cuadrada (ancho de pulso). *Di:* «En el seno, SHAPE a la derecha pliega la onda: más armónicos. En el triángulo, a la izquierda, rampas exponenciales afiladas. En la sierra, va de una sierra normal, a la izquierda del todo, a una supersaw de siete sierras, a la derecha del todo. En la cuadrada, el pulso se estrecha hacia los dos lados.»
5. **Página 3, oscilador 2.** *Muestra:* el pad 28 encendido; el pad 3; FM, ring y sync. *Di:* «Con el pad 28 encendido, la página 3 es el oscilador 2: su afinación, su forma, su onda, la mezcla entre los dos y cómo interactúan: FM, ring y una zona de sync. Con dos notas mantenidas, el oscilador 2 toca la segunda.»

*Capítulo 3: granular*

6. **La página del granular.** *Muestra:* el motor granular; K2 posición, K3 scan, K4 tamaño del grano, K5 densidad; Shift + K8, la fuente. *Di:* «En el motor granular, la página 2 controla los granos: K1, el tono; K2, en qué punto del sample; K3, el scan, que se congela en el centro; K4, el tamaño del grano; y K5, cuántos granos. Shift más K8 elige la fuente: la captura o el sample de un drum.»
7. **Modos de nota.** *Muestra:* Shift + K6: tono, slicer, stretch. *Di:* «Shift más K6 elige qué hacen las notas: cambiar el tono, tocar uno de dieciséis trozos, o stretch: el sample dura los pasos que marque K3, a cualquier tempo, sin cambiar de tono.»
8. **Granos en estéreo.** *Muestra:* Shift + K4 arriba; el panorama de la pista. *Di:* «Shift más K4 reparte los granos en estéreo; el panorama de la pista en el Mixer decide el equilibrio.»

*Capítulo 4: página 4 y automatización*

9. **Knobs secuenciables.** *Muestra:* el pad 4; graba movimientos de los knobs con Record + Play. *Di:* «La página 4 tiene los ocho knobs que se pueden grabar en el patrón: afinación, release, las dos cantidades de envolvente, filtro, resonancia, velocidad del LFO y efecto.»
10. **Elegir qué mueven.** *Muestra:* Shift + K5; los pads enseñando dónde vive el destino. *Di:* «Shift más un knob cambia su destino, a cualquiera de los 33 parámetros del motor, en el color de la página de ese parámetro. Mientras eliges, los pads 9 a 24 enseñan dónde vive. Mantener Clear y luego Shift más el knob vuelve al de fábrica.» [Beta, sin publicar] *Di:* «En las betas más nuevas, esto se hace con Duplicate más un knob de otra página.»
11. **Knobs no secuenciables.** *Muestra:* Shift + pad 4 (rosa). *Di:* «Shift más el pad 4 es otro juego de ocho knobs asignables que no se graban: práctico para el ataque, el sustain o la ganancia del VCA.»
12. **Foto.** *Muestra:* en la vista Note de MIDI 1, Record mantenido + paso 5. *Di:* «En la vista de pista, Record mantenido más un paso escribe en ese paso todos los parámetros que no están en su valor inicial. Una forma rápida de hacer que un paso suene distinto.»
13. **[Beta, sin publicar] Carriles extra.** *Di:* «En las betas más nuevas, todos los demás parámetros del motor tienen también su propio carril, con dos valores por paso, guardado en el fichero del proyecto.»

*Capítulo 5: página 5*

14. **Envolvente y LFO.** *Muestra:* el pad 5; Shift + K8 por las formas. *Di:* «La página 5 tiene la envolvente arriba y el LFO abajo. Shift más K8 elige la forma del LFO: diente de sierra inverso, diente de sierra, triángulo, cuadrada, seno, sample & hold y sample & hold suavizado, cada una con su color.»
15. **Cierre.** *Di:* «Los knobs de tipo enseñan el tipo con el color, y la posición dentro de él, con el brillo. Todo lo de aquí sale y entra también por MIDI. En el siguiente: la matriz de modulación.»

**A tener en cuenta**
- Los valores del motor se guardan con los ajustes del aparato y, desde RC4, con el proyecto; los destinos de los knobs y la forma del LFO van también con el patch del sinte propio.
- Para grabar la página 4 hace falta Record + Play, o mantener un paso mientras giras, como en el original.
- Los knobs de cantidad de efecto y de filtro actúan sobre toda la pista, también en poly.

---

## 11 · Matriz de modulación

**Guía:** [3.4](GUIA.md#midi-matriz) · **Duración:** unos 6 min

**Antes de grabar**
- El sinte propio de MIDI 1 en el oscilador, con un patrón de velocities y notas variadas.

**En esta vista**
- Ocho fuentes de modulación, cada una con un destino y una cantidad.

**Guion**

1. **Abrirla.** *Muestra:* la vista Preset de MIDI 1, el pad 6 (azul claro). *Di:* «El pad 6 convierte los ocho knobs en ocho fuentes de modulación: la velocity, la nota, un valor al azar en cada nota, un segundo LFO, una segunda envolvente, el golpe de un drum, la posición en el patrón y un valor al azar por pasos.»
2. **Un knob: destino y cantidad.** *Muestra:* gira K1 despacio a la derecha: el LED cambia de color, el brillo crece y vuelve a empezar. *Di:* «Aquí está el truco: la posición del knob es a la vez el destino y la cantidad. Al girar a la derecha recorres los 33 parámetros del motor, un tramo cada uno. Dentro de un tramo, la cantidad crece de cero a entera; en el tramo siguiente, cambia el destino.»
3. **Adónde va.** *Muestra:* los pads 9-24 iluminándose mientras gira K1. *Di:* «El LED toma el color de la página del destino y, mientras giras, los pads te enseñan exactamente qué knob es: se enciende el pad de su página, y su sitio en los pads 9 a 24 brilla.»
4. **Ejemplos.** *Muestra:* K1, velocity → filtro; K6, golpe de un drum → tono; K7, posición en el patrón → onda. *Di:* «La velocity abriendo el filtro. Los golpes de Drum 1 curvando el tono. La posición en el patrón barriendo la forma de onda a lo largo del compás.»
5. **La capa de Shift.** *Muestra:* Shift + K4 (forma × velocidad del LFO 2); Shift + K5; Shift + K6; Shift + K8. *Di:* «Con Shift, K4 ajusta la forma y la velocidad del LFO 2, a tempo en la mitad izquierda de cada forma. K5 ajusta el ataque y la caída de la envolvente 2; K6, qué drum y su caída; y K8, cuántos pasos hay entre un valor al azar y el siguiente.»
6. **Borrar.** *Muestra:* Clear + K1; Clear + pad 6. *Di:* «Clear más un knob apaga esa fuente; Clear más el pad 6 las apaga todas.»
7. **Cierre.** *Di:* «La matriz se guarda con el patch del sinte propio y con el proyecto.»

**A tener en cuenta**
- Knobs lentos: dos clics por paso, 16 pasos por destino.
- Varias fuentes pueden ir al mismo destino: se suman. El valor propio del parámetro no cambia; la matriz se suma al enviarlo.
- La matriz no tiene CC / NRPN.
- Muchas fuentes rápidas a la vez se actualizan un poco más despacio: comparten las actualizaciones de la pista.

---

## 12 · FM de 4 operadores

**Guía:** [3.5](GUIA.md#midi-fm) · **Duración:** unos 6 min

**Antes de grabar**
- El sinte propio de MIDI 1; una versión RC (la Beta cambia este motor por el FM de 8 operadores, vídeo 13).

**En esta vista**
- Un sinte FM con 4 operadores y 16 algoritmos.
- Sonidos de partida en el pad 8.
- Ataque o caída percusiva por operador; un release para todos.

**Guion**

1. **Encenderlo.** *Muestra:* el pad 27, el pad 24 (violeta) y luego el pad 7. *Di:* «FM es el pad 24 de la fila de motores. El pad 7 abre su página.»
2. **Sonidos de partida.** *Muestra:* mantén el pad 8: 16 instrumentos; pulsa unos cuantos. *Di:* «Mantén el pad 8 y tienes dieciséis sonidos listos: piano, piano eléctrico, órgano, sonidos pulsados, bajo, campana, cuerdas, pad, vientos y percusión. Pulsa uno para cargarlo entero; es un punto de partida que puedes guardar como patch.»
3. **Algoritmos.** *Muestra:* mantén el pad 7: los 16 algoritmos; pulsa uno. *Di:* «Mantén el pad 7 para ver los dieciséis algoritmos: pilas clásicas, percusivos para bombo, caja y hi-hat, campanas y cuerdas. Al pulsar uno, lo eliges y lo oyes.»
4. **Los knobs.** *Muestra:* K1-K4, los ratios (colores de los LEDs); K5-K8, los niveles. *Di:* «K1 a K4 son los ratios de los cuatro operadores: verde es un ratio entero; azul claro, uno acabado en coma cinco; verde azulado, uno inarmónico. K5 a K8 son sus niveles: en un portador, cuánto suena; en un modulador, cuánto modula.»
5. **La capa de Shift.** *Muestra:* Shift + K1 a la derecha (ataque) y a la izquierda (percusivo). *Di:* «Con Shift, K1 a K4 dan forma a cada operador: a la derecha, un ataque; a la izquierda, el operador se vuelve percusivo, con su propia caída. Shift más K5 es el algoritmo; K6, el feedback; K7, el ruido; y K8, el release, que es más largo cuanto más fuerte tocas.»
6. **Brillo.** *Muestra:* SHAPE de la página 2 moviendo el timbre. *Di:* «SHAPE en la página 2, con su envolvente y su LFO, hace que los moduladores pesen más o menos: así la envolvente, el LFO y la matriz del motor mueven el timbre del FM.»
7. **Clear.** *Muestra:* Clear + pad 7. *Di:* «Clear más el pad 7 te da una voz tocable del algoritmo elegido.»
8. **Cierre.** *Di:* «El FM se guarda con los patches del sinte propio.»

**A tener en cuenta**
- El volumen sale de las envolventes de los operadores: el VCA del motor se queda abierto; la velocity sigue dando el nivel.
- Las notas agudas modulan menos y caen antes, como en los sintes FM clásicos.
- Los parámetros del FM no tienen CC / NRPN.

---

## 13 · FM de 8 operadores [Beta]

**Guía:** [3.6](GUIA.md#midi-fm8) · **Duración:** unos 9 min (capítulos: operadores y envolventes / algoritmos y el mapa / sonidos y guardado)

**Antes de grabar**
- La Beta. El sinte propio de MIDI 1 en FM. Un banco del DX7 (`.syx`) en el ordenador, para mencionar la importación.

**En esta vista**
- Hasta 8 operadores, cada uno con una envolvente como la del DX7; 56 algoritmos.
- El mapa del algoritmo: quién modula a quién, de un vistazo; tus propios enlaces.
- Instrumentos y patches de ejemplo.

**Guion**

*Capítulo 1: operadores y envolventes*

1. **Abrir la página.** *Muestra:* el pad 24 de la fila de motores, cierra la fila (pad 27), el pad 7. *Di:* «En la Beta, el FM tiene hasta ocho operadores. Elige FM en la fila de motores, cierra la fila, y el pad 7 abre su página.»
2. **Elegir un operador.** *Muestra:* los pads 9-16: portadores en verde, moduladores en azul claro. *Di:* «Los pads 9 a 16 son los operadores: los portadores en verde, los moduladores en azul claro y el elegido, brillante.»
3. **Sus knobs.** *Muestra:* K1, ratio (3 clics por paso); K3, nivel; K5-K8, rates; Shift + K5-K8, niveles. *Di:* «Con un operador elegido: K1 es su ratio, hasta 31, y después frecuencias fijas, en rojo. K2, el ajuste fino; K3, el nivel de salida; K4, la sensibilidad a la velocity. K5 a K8 son los cuatro rates de su envolvente y, con Shift, sus cuatro niveles.»
4. **Cómo se mueve la envolvente.** *Di:* «Como en un DX7: sube con el rate 1 hasta el nivel 1, luego con el rate 2 hasta el nivel 2 y con el rate 3 hasta el nivel 3, y se queda ahí mientras mantienes la nota. Al soltarla, va con el rate 4 hasta el nivel 4. Un rate de 99 es instantáneo.»
5. **Envolvente de pitch.** *Muestra:* el pad 3 (violeta). *Di:* «El pad 3 es la envolvente de pitch, como un noveno operador, y además el ruido.»

*Capítulo 2: algoritmos y el mapa*

6. **La lista.** *Muestra:* Shift + pad 7 mantenido: tres páginas con Octave. *Di:* «Shift más el pad 7 mantenido enseña los 56 algoritmos en tres páginas: los de cuatro operadores, ocho nuevos de ocho operadores y los 32 del DX7.»
7. **El mapa.** *Muestra:* un toque al pad 7: el mapa en los pads 9-32. *Di:* «Un toque al pad 7 enseña el mapa del algoritmo. Cada fila se lee de izquierda a derecha: el operador de la izquierda modula al de su derecha, y el último es un portador. Un hueco oscuro quiere decir que no hay conexión.»
8. **Los colores del mapa.** *Di:* «El color dice el ratio: verde, un número entero; verde azulado, uno acabado en coma cinco; naranja, uno inarmónico; rojo, una frecuencia fija; y el feedback, en violeta. Brillante quiere decir un nivel de salida alto.»
9. **Callar y enlazar.** *Muestra:* Shift + un operador (se oscurece); mantén uno y toca otro. *Di:* «Shift más un operador lo calla mientras miras el mapa: así oyes lo que aporta. Mantén un operador y toca otro: el primero pasa a modular al segundo, o deja de hacerlo. Ese es tu propio algoritmo, y se guarda con el patch.»

*Capítulo 3: sonidos y guardado*

10. **Instrumentos.** *Muestra:* mantén el pad 8: instrumentos; Octave ▼ para la página 2. *Di:* «Beta 5.56: mantén el pad 8 para ver 24 instrumentos y, con Octave, una segunda página de pianos, cuerdas, vientos y sonidos largos. Al cargar uno, los knobs secuenciables pasan también a los que convienen a su familia.» [Beta, sin publicar] *Di:* «En las próximas betas, los instrumentos salen del firmware: llegan como patches de ejemplo para la app de la tarjeta.»
11. **Guardado.** *Di:* «El FM de cada patch se guarda con los patches del sinte propio en la tarjeta, y con el proyecto. Los patches antiguos de cuatro operadores se cargan convertidos, con el mismo sonido.»
12. **Importar de un DX7.** *Muestra:* la app de la tarjeta, Parches custom, Importar DX7…. *Di:* «La app de la tarjeta puede importar un banco del DX7: cada voz se convierte en un parche custom para este motor.»
13. **Cierre.** *Di:* «Hasta aquí el FM. En el siguiente: el editor de CC de las plantillas MIDI.»

**A tener en cuenta**
- El motor solo calcula los operadores que usa el algoritmo: con 4, unas 10 voces; con 6, unas 6-7; con 8, unas 5.
- Tras «Send patches» / «Send pack» de Components, el aparato devuelve los patches propios a cada banco; una copia de seguridad de Components (su zip) no los lleva: usa el Snapshot de la app.
- El FM no tiene CC / NRPN.

---

## 14 · Editor de CC de los macros MIDI

**Guía:** [3.7](GUIA.md#midi-cc) · **Duración:** unos 4 min

**Antes de grabar**
- Un sinte externo en MIDI 1, con un parámetro que se vea cambiar (un filtro).

**En esta vista**
- Cambiar desde el aparato qué CC (o NRPN) manda cada knob de una plantilla MIDI, y su recorrido.

**Guion**

1. **Para qué.** *Di:* «Las plantillas MIDI mandan CC fijos, que se configuran en Components. Aquí los cambias en el propio aparato.»
2. **Abrirlo.** *Muestra:* la vista Preset de MIDI 1, el pad 25 (encendido); mueve K1: su número dibujado en los pads. *Di:* «El pad 25 abre el editor. Mueve un knob: queda elegido y su número de CC se dibuja en los pads.»
3. **Campos.** *Muestra:* Octave ▼ / ▲; gira K1 para cambiar el valor. *Di:* «Octave te mueve entre los campos: el número, el inicio y el fin del recorrido. Gira el knob para cambiar cada uno.»
4. **NRPN.** *Di:* «Pon el número en 99, 98 o 6 y el knob manda un NRPN de 7 bits, con campos de MSB y LSB; con 38, un NRPN de 14 bits.»
5. **Guardar o descartar.** *Muestra:* el pad 26 (Save parpadea); o un botón de vista para descartar. *Di:* «El pad 26 guarda; también puedes seguir pulsando Octave abajo hasta el paso de guardar. Cualquier botón de vista, el pad 25 o un pad de plantilla descartan los cambios.»
6. **Cierre.** *Di:* «Con el sinte propio encendido, los knobs mandan en cambio sus propios parámetros, y el pad 25 se queda apagado.»

**A tener en cuenta**
- Las asignaciones de CC viven en la memoria del aparato, con sus plantillas, no en la tarjeta.
- La app de la tarjeta lee, edita y envía las ocho plantillas como un fichero `.ctcc`.

---

## 15 · Vista del step-drummer

**Guía:** [3.8](GUIA.md#step-drummer) · **Duración:** unos 6 min

**Antes de grabar**
- El sinte propio de MIDI 1 con un patrón de 16 pasos de notas sueltas.

**En esta vista**
- Ocho pares de pasos en los ocho knobs, cada uno moviendo un destino.
- Una segunda página con su propio destino; el toggle pitch-vel.
- Grabar en tiempo real; el secuenciador de efectos.

**Guion**

1. **Abrirla.** *Muestra:* la vista Preset de MIDI 1, el pad 30 (o Note → Note ampliada → step-drummer, desde RC4). *Di:* «El pad 30 abre el step-drummer. En lugar de dibujar automatización, fijas un parámetro en pares de pasos con los knobs.»
2. **La disposición.** *Muestra:* los pads 1-16 son los pasos; K1-K8 = los pares (el que suena, en blanco). *Di:* «Los pads 1 a 16 son los pasos: brillantes con nota y blancos mientras suenan. Toca uno para oírlo; Shift más un toque pone o quita una nota. Cada knob es un par de pasos: K1 son los pasos 1 y 2; K2, los pasos 3 y 4; y así. 1-16 / 17-32 enseña la otra mitad.»
3. **Destino.** *Muestra:* el pad 17, tono; gira K3: la nota se mueve en los pasos 5-6. *Di:* «Los pads 17 a 24 eligen qué mueve la página pitch: el tono, el oscilador 2, WAVE, FM, MIX, la envolvente al filtro, SHAPE o el decay. El knob lo desplaza desde el centro: en el medio, no cambia nada. El LED está tenue sin cambio y brilla más cuanto más te alejas.»
4. **Página 2.** *Muestra:* Octave ▼ (página velocity); elige un destino; gira knobs. *Di:* «Octave cambia a la página velocity, que tiene su propio destino: puedes mover el filtro y el tono en los mismos pasos a la vez.»
5. **Toggle pitch-vel.** *Muestra:* el pad 32 (verde brillante); una melodía a partir de una sola nota. *Di:* «El pad 32 es el toggle pitch-vel: ahora la página 1 transpone las notas en grados de tu escala, un grado cada ocho pasos del knob, y la página 2 marca su velocity. Una melodía a partir de una sola nota repetida.»
6. **Tiempo real.** *Muestra:* Record + Play; toca pasos. *Di:* «Con Record encendido, tocar un paso lo graba en el paso que está sonando.»
7. **Secuenciador de efectos.** *Muestra:* motor = secuenciador de efectos; los knobs eligen huecos de Master FX (colores). *Di:* «Con el motor secuenciador de efectos, cada knob elige un hueco de Master FX para su par de pasos: ninguno, un hueco o, al final del recorrido, uno al azar. Un hueco vacío toca el efecto de arriba de su columna.» [Beta, sin publicar] *Di:* «Y un valor más, al final del todo: mute, en rojo. En ese paso el master entero se queda en silencio.»
8. **Cierre.** *Di:* «En Synth 1 y 2, la misma vista se abre desde la vista de la fuente y mueve los macros.»

**A tener en cuenta**
- Los valores se escriben como automatización: pertenecen al patrón.
- En MIDI 1 / 2, la página 2 usa el carril del release: con el step-drummer encendido, el release no se reproduce ni se graba.
- Cada paso conserva la altura de su primera nota.

---

## 16 · Modo muestra y selector de samples

**Guía:** [3.9](GUIA.md#midi-muestra) · **Duración:** unos 6 min

**Antes de grabar**
- El sinte propio de MIDI 1 en el motor muestra (verde azulado); un pack con samples de drums y one-shots; un sample estéreo guardado en dos huecos seguidos.

**En esta vista**
- Un sample del pack tocado a la altura de cada nota.
- Un sample distinto en cada paso (sample flip).
- Estéreo con dos huecos.

**Guion**

1. **El motor.** *Muestra:* la fila de motores: muestra (verde azulado); toca el teclado. *Di:* «El modo muestra toca un sample del pack de un golpe, a la altura de cada nota: la nota 60, el do central, es el sample tal como se grabó; una octava más arriba suena el doble de rápido.»
2. **El selector.** *Muestra:* Note dos veces: las filas 3-4 son samples; Octave pasa las páginas. *Di:* «Pulsa Note dos veces para el selector de samples: las filas 3 y 4 son dieciséis samples, y Octave recorre los 64 del pack. Toca uno: pasa a ser el sample de la pista, y suena. Shift más un sample lo elige sin que suene.»
3. **Sample flip.** *Muestra:* mantén el paso 3 + toca un sample: el paso se pone melocotón. *Di:* «Las filas 1 y 2 son los pasos. Mantén un paso y toca un sample: ese paso toca ese sample, un sample flip. O mantén un sample y toca varios pasos. Clear más un paso lo quita.»
4. **Flips en pasos sin nota.** *Muestra:* un flip en un paso sin nota: violeta → se añade una nota. *Di:* «Un flip en un paso sin nota añade ahí la última nota que tocaste, para que suene. Melocotón: una nota con flip; verde azulado: una nota sin flip; violeta: un flip sin nota.»
5. **En directo.** *Muestra:* Record + Play; toca samples. *Di:* «Con Record encendido, tocar un sample graba una nota con su flip en el paso que suena.»
6. **Estéreo.** *Muestra:* la página 2, K7 (WAVE) arriba; Shift + el sample elegido (parpadea en verde azulado); elige el segundo. *Di:* «K7 de la página OSC 1 es la anchura estéreo: al subirla, cada nota toca el sample elegido a la izquierda y un segundo sample a la derecha. Shift más el sample elegido pasa a elegir el segundo. Los samples del aparato son mono: un sample estéreo son dos huecos seguidos.» [Beta] *Di:* «En la Beta, la anchura está en K3.»
7. **Cierre.** *Di:* «El filtro, el efecto y el LFO del motor siguen funcionando. En el siguiente: Pattern Settings.»

**A tener en cuenta**
- Una voz por pista en los modos mono; poly da hasta 4 notas.
- Los flips viven en el carril de automatización de nivel de la pista: grabar el nivel encima los borra.
- La fuente del sample es la misma que la del motor granular (Shift + K8 en su página).
- La captura suena siempre en mono.

---

## 17 · Vista Pattern Settings

**Guía:** [4.1](GUIA.md#pattern-settings) · **Duración:** unos 9 min (capítulos: Nudge y órdenes / el arpegiador / sus modificadores / el arpegiador de los drums)

**Antes de grabar**
- Synth 2 con un patrón de acordes mantenidos; Drum 1 con un pack cuyos primeros samples sean un kit (bombo, caja, charles).

**En esta vista**
- Nudge: mueve el contenido de los pasos elegidos.
- Los órdenes de reproducción fractal y deconstruido.
- El arpegiador de las pistas de notas y sus modificadores.
- El arpegiador de los drums.

**Guion**

*Capítulo 1: Nudge y órdenes*

1. **Intro.** *Muestra:* Pattern Settings con Synth 2: primer / último paso, sync rate, dirección. *Di:* «Pattern Settings funciona como siempre: primer y último paso, sync rate y dirección. Lo nuevo está en los pads 25 a 28, y el arpegiador vive bajo Shift.»
2. **Nudge.** *Muestra:* toca el pad 26 (azul) unas cuantas veces; Shift + pad 26. *Di:* «El pad 26 es Nudge: un toque mueve el contenido de los pasos elegidos un paso atrás; Shift más el pad 26, un paso adelante. Lo que sale por un extremo entra por el otro, y el primer y el último paso se quedan donde están.»
3. **Órdenes.** *Muestra:* el pad 27, luego el pad 28; los pads 29-32 los apagan. *Di:* «El pad 27 toca el patrón en orden fractal: 1; 1 2; 1 2 3; y así. El pad 28 es el deconstruido: las diagonales de la rejilla. Sustituyen a los pads de dirección de stock, y las notas en sí no cambian.»

*Capítulo 2: el arpegiador*

4. **Encenderlo.** *Muestra:* Shift + pad 25 (verde con Shift); el pad 25 en verde sin Shift. *Di:* «Shift más el pad 25 enciende el arpegiador del patrón que está tocando esta pista. Mientras está encendido, el pad 25 se ve verde.»
5. **Orden y resolución.** *Muestra:* Shift + pads 27-32; Shift + pads 17-24. *Di:* «Shift más los pads 27 a 32 eligen el orden del arpegio: fractal, deconstruido, arriba, abajo, ping-pong o aleatorio. Shift más los pads 17 a 24 eligen su resolución, de negras a tresillos de fusa, distinta del sync rate de la pista. El mismo pad otra vez vuelve al de la pista.»
6. **Qué hace.** *Muestra:* el patrón de acordes, ahora arpegiado; mantén dos teclas en directo. *Di:* «Los acordes del patrón suenan ahora nota a nota, mientras dura el acorde, cada nota con su propio gate y su velocity. En directo, la primera nota suena como siempre; mantén otra y las notas mantenidas se arpegian. Con Record se graba el acorde, no las notas sueltas: la secuencia lo arpegia al reproducirlo.»
7. **Orden de las notas.** *Di:* «Las notas van en el orden en que las pulsaste, no por altura; arriba, abajo y los demás recorren ese orden.»
8. **Paso mantenido y teclado.** *Muestra:* parado, mantén un paso con un acorde. *Di:* «Con el transporte parado, mantener un paso con varias notas las arpegia. Con el botón Note de Setup encendido, un teclado externo pasa también por el arpegiador.»

*Capítulo 3: sus modificadores*

9. **Los cuatro grupos.** *Muestra:* Shift + pads 1-16 con el arpegiador encendido: arena, azul cielo, ámbar, rosa. *Di:* «Con el arpegiador encendido, Shift más los pads 1 a 16 eligen cuatro modificadores. Arena: el rango de octavas. Azul cielo: cuándo cambia la octava, tras cada vuelta o cada pocas notas. Ámbar: el groove, con puntillo, swing o cada nota dos veces. Rosa: un reinicio tras una vuelta y unas pocas notas más, para patrones que se van desplazando.»

*Capítulo 4: el arpegiador de los drums*

10. **Drums.** *Muestra:* el Pattern Settings de Drum 1, Shift + pad 25; la vista Preset de Drum 1: mantén tres samples. *Di:* «Los mismos gestos en el Pattern Settings de un drum encienden su arpegiador. Luego, en la vista Preset del drum, mantén varios samples: el drum salta de sample en sample al ritmo del arpegio. Con Record, cada golpe se graba con su sample como sample flip.»
11. **Cierre.** *Di:* «En el siguiente: la vista Micro Step.»

**A tener en cuenta**
- Los ajustes del arpegiador se guardan en el proyecto por pista y número de patrón: duplicar un patrón no los copia.
- Nudge y los órdenes también funcionan en los drums; el orden se guarda con el patrón, y Clear del patrón lo quita.
- Clear + pad 25 borra las dinámicas y el random-mutate de todos los pasos del patrón (pistas de notas); la frecuencia se queda.

---

## 18 · Vista Micro Step

**Guía:** [4.2](GUIA.md#micropasos) · **Duración:** unos 4 min

**Antes de grabar**
- Synth 1 con unas cuantas notas; el transporte parado.

**En esta vista**
- Micropasos y Tie, como en el original.
- Gate por pulsación: las notas que introduces a mano duran lo que las mantienes.
- Longitud fija para todas las notas que introduces a mano.

**Guion**

1. **Abrirla.** *Muestra:* Gate dos veces. *Di:* «Pulsa Gate dos veces para la vista Micro Step. Los pads 17 a 22 son los seis micropasos del paso elegido, el pad 24 es Tie y los pads 25 a 30 son las notas del paso, como en el original.»
2. **Gate por pulsación.** *Muestra:* el pad 32 en verde; mantén un paso + un pad de nota un rato y suéltalos. *Di:* «El pad 32 enciende el gate por pulsación: cuando introduces una nota a mano, con un paso y una nota mantenidos a la vez, lo que tardas en soltarlos es lo que dura la nota, desde un micropaso hasta dieciséis pasos.»
3. **Longitud fija.** *Muestra:* el pad 31 → el selector en los pads 17-32; elige 4; introduce notas. *Di:* «El pad 31 es la longitud fija: con los dos apagados abre un selector, dieciséis longitudes como en la vista Gate; elige una y cada nota que introduzcas a mano tendrá esa longitud, también todas las notas de un acorde.»
4. **Cambiar de uno a otro.** *Muestra:* el pad 31 otra vez (apagado); el pad 32 con el 31 encendido. *Di:* «Pulsa el que está encendido para apagarlo. Pulsa el otro y se intercambian.»
5. **Cierre.** *Di:* «El arpegiador usa también estos gates: cada nota de un acorde dura lo suyo.»

**A tener en cuenta**
- Ninguno de los dos toggles cambia las notas grabadas en directo.
- Los dos toggles se guardan con el proyecto, por pista.
- Un micropaso por nota, como en el original: para dos posiciones dentro de un paso, introduce dos notas.

---

## 19 · Vista de probabilidad

**Guía:** [4.3](GUIA.md#probabilidad) · **Duración:** unos 8 min (capítulos: frecuencia / dinámicas y random-mutate / [Beta] el nuevo modo 2 / drums)

**Antes de grabar**
- Synth 1 con una melodía de 16 pasos; Drum 3 con charles en todos los pasos.

**En esta vista**
- Frecuencia: un paso que suena una vez cada n vueltas.
- Dinámicas aleatorias y random-mutate.
- [Beta] El modo 2 rediseñado, con un factor por pista.
- Lo mismo en los drums.

**Guion**

*Capítulo 1: frecuencia*

1. **Modo 1.** *Muestra:* Pattern Settings dos veces; mantén el paso 4; la fila 3 (probabilidad), la fila 4 (amarillo). *Di:* «Pulsa Pattern Settings dos veces para la vista de probabilidad. Mantén un paso con notas: la fila 3 es la probabilidad de stock. La fila 4 es nueva: la frecuencia. Elige 4 y el paso solo suena en la última de cada cuatro vueltas. Variaciones que vuelven cada cierto ciclo.»

*Capítulo 2: dinámicas y random-mutate*

2. **Modo 2.** *Muestra:* Pattern Settings, el pad 25 (melocotón). *Di:* «El pad 25 de Pattern Settings abre el modo 2. En las RC, la fila 3 son las dinámicas aleatorias: pequeños cambios de velocity y de posición, en ocho niveles. La fila 4 es el random-mutate: la probabilidad de que la nota salte una octava o a otra nota de la escala.»
3. **Grabar o no.** *Muestra:* toca con Record y sin él. *Di:* «Sin Record, una mutación solo cambia esa vuelta. Con Record y esta vista en pantalla, lo que suena se escribe en el patrón: la secuencia va derivando, un poco en cada vuelta.»

*Capítulo 3: [Beta] el nuevo modo 2*

4. **Una sola botonera.** *Muestra:* Beta, modo 2: los pads 17-24 (blanco, melocotón, arena), 25-28 y 32. *Di:* «En la Beta, las filas 3 y 4 funcionan como una sola botonera por paso. Pad 17: sin cambios. Pads 18 a 20: otra nota de la escala, más probable cuanto más a la derecha. Pads 21 y 22: una octava arriba. 23 y 24: una octava arriba o abajo. Pad 25: sin dinámicas; 26: notas fantasma, más suaves; 27: accent staccato, más fuertes y más cortas; 28: longitud al azar. Pad 32: desplazamientos de micropaso.»
5. **El factor.** *Muestra:* Octave ▲ / ▼: el número en los pads. *Di:* «Con esta vista abierta, Octave ajusta el factor de la pista: por 0, 1, 2, 4 u 8, que multiplica todas las probabilidades. Con el factor en 8, el pad 24 cambia todas las notas.»

*Capítulo 4: drums*

6. **Drums.** *Muestra:* Drum 3: Pattern Settings dos veces; el pad 25 de su Pattern Settings. *Di:* «Los drums tienen la misma vista. Modo 1: probabilidad y frecuencia. Modo 2, en las RC: dinámicas y, en los pads 25 a 28, random-mutate del sample: el sample de al lado en su fila, o el de la misma columna en otra fila.»
7. **Cierre.** *Di:* «En el siguiente: los drums.»

**A tener en cuenta**
- Los contadores de la frecuencia vuelven a empezar cada vez que se para el transporte.
- Las notas ligadas conservan su nota y su longitud.
- En los drums, las dinámicas solo pueden retrasar un golpe dentro de su paso (un drum no puede sonar antes), y la mutación del sample no se graba nunca.
- Los valores se guardan con cada paso; viajan al duplicar el patrón o al hacer Nudge.

---

## 20 · Vista de pista de un drum

**Guía:** [5.1](GUIA.md#drum-pista) · **Duración:** unos 9 min (capítulos: los knobs / volver a empezar / la pareja estéreo / [Beta] herramientas de automatización)

**Antes de grabar**
- Drum 1 con un sample de bombo y Drum 2 con una caja; un sample estéreo en dos huecos seguidos del pack.

**En esta vista**
- Cada knob hace lo que dice su etiqueta, con una segunda capa en Shift.
- Clear + el botón del drum para volver a empezar.
- Parejas estéreo (Drum 1 + 2, Drum 3 + 4).
- [Beta] La foto, el carril extra, los bloqueos de estado y la vista de automatización.

**Guion**

*Capítulo 1: los knobs*

1. **Intro.** *Di:* «En el original, los knobs de los drums hacen cuatro cosas. Aquí cada knob hace lo que dice su etiqueta, y Shift da una segunda capa. Con los knobs nuevos en su punto neutro, el sample suena como en el original.»
2. **K1 / K2.** *Muestra:* K1, pitch; Shift + K1; K2 / Shift + K2. *Di:* «K1 es el pitch; con Shift, la cantidad de la envolvente de tono. K2 es la frecuencia de un ring mod; con Shift, su cantidad.»
3. **K3, en los dos sentidos.** *Muestra:* K3 a la izquierda (decay) y, pasado el centro, a la derecha (ataque, blanco); Shift + K3 a la izquierda (inicio) y a la derecha (corte). *Di:* «K3 a la izquierda es el decay; pasado el centro, a la derecha, es un ataque, un fundido de entrada. Con Shift: a la izquierda, dónde empieza el sample; a la derecha, un corte desde el final.»
4. **Filtro.** *Muestra:* K4; K5; los colores de Shift + K5; K6. *Di:* «K4 manda la envolvente al filtro; con Shift, la forma de la envolvente. K5 es el filtro o el EQ; Shift más K5 elige su modo, que se ve por el color: verde, el EQ tilt de stock; amarillo, paso banda; magenta, notch; verde azulado, comb; y blanco, el filtro DJ. K6 es la resonancia.» [Beta] *Di:* «En la Beta ya no está el modo comb.»
5. **K7 / K8.** *Muestra:* K7 a la derecha (trémolo) y a la izquierda (scan del inicio); Shift + K7; K8, a la izquierda de cero (bitcrush); Shift + K8. *Di:* «K7 a la derecha es un trémolo; a la izquierda, cada golpe empieza en un sitio distinto del sample, siguiendo al LFO. Shift más K7 es la velocidad del LFO: a la derecha, libre; a la izquierda, a tempo. K8 es la distorsión y, a la izquierda de cero, un bitcrush; Shift más K8 elige el tipo de distorsión.»

*Capítulo 2: volver a empezar*

6. **Clear.** *Muestra:* Clear + K3 a la derecha; Clear + Drum 1. *Di:* «Clear más un knob a la derecha reinicia las dos capas de ese knob. Clear más el botón del drum devuelve sus ocho knobs a los valores por defecto y borra su automatización en el patrón que suena.»

*Capítulo 3: la pareja estéreo*

7. **Hacer una pareja.** *Muestra:* mantén Drum 1 y pulsa Drum 2; el botón de Drum 2 late. *Di:* «Mantén Drum 1 y pulsa Drum 2: pasan a ser una pareja estéreo. Drum 1 suena a la izquierda y Drum 2 a la derecha, con el sample siguiente del pack: un sample estéreo son dos huecos seguidos.»
8. **Quién manda.** *Muestra:* los knobs y el patrón de Drum 1; K1 de Drum 2 (desafinación) y K2 (apertura). *Di:* «Drum 1 manda en los dos: sus knobs, su patrón, su nivel y sus envíos. Los knobs de Drum 2 pasan a ser pequeñas desviaciones: K1 desafina el lado derecho y K2 marca la apertura estéreo. El patrón propio de Drum 2 descansa mientras dura la pareja. El mismo gesto deshace la pareja.»

*Capítulo 4: [Beta] herramientas de automatización*

9. **Foto.** *Muestra:* Record mantenido + paso 7. *Di:* «En la Beta, Record mantenido más un paso escribe en ese paso el pitch, el decay, la distorsión y el EQ que no estén en su valor por defecto.»
10. **Carril extra.** *Muestra:* Record mantenido + K6. *Di:* «Cada drum tiene un carril de automatización más. De fábrica lleva el pitch cromático; Record mantenido más un knob le asigna otro parámetro, como la resonancia.»
11. **Vista de automatización.** *Muestra:* la vista Velocity con Shift: pasos amarillos; Shift + un paso amarillo. *Di:* «Mantén Shift en la vista Velocity de un drum: los pasos con automatización se encienden en amarillo. Shift más un paso amarillo lo escucha; Shift más otro paso lo marca en rojo, y en ese paso los knobs vuelven a los valores del proyecto.»
12. **Cierre.** *Di:* «En el siguiente: la vista Preset del drum.»

**A tener en cuenta**
- Todo lo de aquí se guarda con el proyecto y tiene NRPN.
- Los knobs nuevos del mod no tienen carril de automatización propio (los de stock, sí).
- El sidechain entre drums está en la vista Sidechain (vídeo 25).
- La pareja estéreo se guarda con el proyecto.

---

## 21 · Vista Preset de drums

**Guía:** [5.2](GUIA.md#drum-preset) · **Duración:** unos 5 min

**Antes de grabar**
- Una captura ya grabada en Master FX (vídeo 23); dos packs en la tarjeta.

**En esta vista**
- Un drum sustituido por la captura de Master FX.
- Intercambiar y copiar samples, también entre packs.
- El arpegio de samples.

**Guion**

1. **Intro.** *Muestra:* Drum 1, Preset: los samples; Shift + pad (selección sin sonido, de stock). *Di:* «La vista Preset del drum elige su sample, como siempre. Hay tres cosas nuevas.»
2. **Sustituir por la captura.** *Muestra:* Clear + pad, Clear + el mismo pad: la captura suena en ese drum. *Di:* «Clear más un pad, dos veces, sustituye ese sample por la captura de Master FX. Hasta que guardes el proyecto, solo está en la memoria; al guardar, se escribe en el pack si cabe en la memoria de samples.»
3. **Intercambiar.** *Muestra:* Duplicate + pad A + pad B. *Di:* «Duplicate más dos pads intercambia dos samples, con sus ficheros y todo; lo oyes al momento.»
4. **Copiar de otro pack.** *Muestra:* Duplicate + A; carga otro pack; Preset; Duplicate + B. *Di:* «Duplicate más un sample, carga otro pack y luego Duplicate más un hueco: el sample se copia ahí. Nunca pisa un sample que esté sonando.»
5. **Arpegio de samples.** *Muestra:* el arpegiador del drum encendido; mantén tres samples. *Di:* «Con el arpegiador del drum encendido, mantener varios samples hace que el drum salte de uno a otro.»
6. **Atajo.** *Muestra:* Preset otra vez. *Di:* «Preset otra vez, o Shift más Preset, abre la vista cromática, la del siguiente vídeo.»

**A tener en cuenta**
- Todo lo de aquí *escribe en la tarjeta*: no en las versiones S ni en el pack interno.
- Una captura usada en un drum y sin guardar se pierde al apagar; el drum vuelve a su sample del pack.

---

## 22 · La vista cromática de los drums y los rollers

**Guía:** [5.3](GUIA.md#drum-cromatica) · **Duración:** unos 5 min

**Antes de grabar**
- Drum 2 con un sample con tono (un tom o un golpe de bajo); la vista Note de los drums lista.

**En esta vista**
- Un drum tocado como un teclado, en la escala del proyecto.
- Rollers de micropasos en la vista Note de los drums.

**Guion**

1. **Abrirla.** *Muestra:* Drum 2, Shift + Preset. *Di:* «Shift más Preset convierte el drum en un teclado: tres filas de notas en la escala y la tónica de la vista Scales.»
2. **Afinación.** *Muestra:* K1; Shift + K1. *Di:* «K1 desplaza el tono en semitonos; Shift más K1 lo afina en cents.»
3. **Grabarlo.** *Muestra:* Record + Play; toca pads. *Di:* «Mientras grabas, cada pad graba un golpe con su tono en su propio paso. Shift más Play cuantiza, y el tono se mueve con su golpe.»
4. **La vista Note de los drums.** *Muestra:* Note con un drum elegido: los pads 25-28. *Di:* «En la vista Note de los drums, los pads 25 a 28 repiten los cuadros de los drums, de Drum 4 a Drum 1.»
5. **Rollers.** *Muestra:* las filas 1-3: mantén un pad, y luego dos de la misma columna. *Di:* «Las filas 1 a 3 son rollers de micropasos: cada columna es de un drum; la columna izquierda, sus micropasos 1 a 3, y la derecha, del 4 al 6. Mientras mantienes uno, el drum suena en cada paso en ese micropaso: redobles y ratchets, en directo.»
6. **Parado y grabado.** *Muestra:* parado, mantén un roller; Record + Play. *Di:* «También funcionan con el transporte parado, al tempo del proyecto. Con Record, sus golpes se graban en el patrón.»
7. **Cierre.** *Di:* «En el siguiente: Master FX.»

**A tener en cuenta**
- Los pasos sin un tono grabado suenan con el pitch de K1.
- El pitch cromático se guarda con el patrón; el semitono de K1, con el proyecto.

---

## 23 · Master FX

**Guía:** [6.1](GUIA.md#master-fx) · **Duración:** unos 12 min (capítulos: los efectos / el song pointer / la captura / los huecos / el Glitch y el gesto mecánico)

**Antes de grabar**
- El proyecto `TUTORIAL` tocando un bucle completo; los knobs de cada efecto en sus valores por defecto.

**En esta vista**
- Efectos en directo sobre toda la mezcla: Gater, Auto-Filter, Digitise, Phaser, Glitch y el gesto mecánico.
- El song pointer: retriggers y bucles del patrón.
- La captura: graba hasta 3,5 s de lo que suena, tócalo, ponlo en un hueco o úsalo como drum.
- Huecos asignables en la fila de abajo.

**Guion**

*Capítulo 1: los efectos*

1. **Abrirla.** *Muestra:* Mixer y Mixer otra vez. *Di:* «Pulsa Mixer dos veces para Master FX: efectos sobre toda la salida, y además unas cuantas herramientas para tocar en directo. Cualquier otro botón de vista sale.» [Beta] *Di:* «En la Beta, mantén Mixer y verás Master FX solo hasta que lo sueltes.»
2. **Mantener y fijar.** *Muestra:* mantén el pad 1 (Gater); Shift + pad 2; toca el pad 2 otra vez. *Di:* «Los pads 1 a 6 son los efectos: Gater, Auto-Filter paso bajo y paso alto, Digitise, Phaser y Glitch. Mantén uno y estará activo hasta que lo sueltes. Shift más el pad lo fija; tócalo otra vez para soltarlo.»
3. **Sus knobs.** *Muestra:* con el pad 1 mantenido, K1-K4; el brillo de los LEDs. *Di:* «Mientras mantienes un efecto, K1 a K4 son sus controles: en el Gater, división, profundidad, ancho y suavizado; en el Auto-Filter y el Phaser, la velocidad, a tempo en el lado izquierdo del knob. Los LEDs enseñan los valores con su brillo.»
4. **Los extras de Digitise.** *Muestra:* mantén el pad 4, sube K3, suelta el pad; K4. *Di:* «Digitise tiene dos extras: K3 lanza las pistas al delay mientras mantienes el pad, y K4 es una envolvente sobre la cantidad: a la derecha pasa de destrozado a limpio, y a la izquierda, al revés.»
5. **Todo apagado.** *Muestra:* fija dos efectos; el pad 8. *Di:* «El pad 8 suelta todo lo fijado, efectos, song pointer y sample, y deja los efectos en bypass.»

*Capítulo 2: el song pointer*

6. **Retrigger y bucles.** *Muestra:* mantén uno de los pads 9-24; mantén dos; Shift + dos (el pad 9 en blanco). *Di:* «Los pads 9 a 24 son los pasos 1 a 16 del patrón. Mantén uno: el patrón vuelve a empezar desde ese paso. Mantén dos: hace un bucle entre ellos hasta que los sueltes. Shift más dos: el bucle se queda; el pad 9 se pone blanco y, al tocarlo, se quita el bucle.»
7. **Modo frase.** *Muestra:* Shift + paso 5; toca el paso 8; Shift + pad 9 para salir. *Di:* «Shift más un paso entra en el modo frase con ese inicio; a partir de ahí, cada toque marca el final, sin volver a empezar. Shift más el inicio, o el pad 9, sale.»

*Capítulo 3: la captura*

8. **Grabar.** *Muestra:* mantén el pad 32 durante dos tiempos; toca el pad 32 dos veces; Shift + pad 32 con el transporte parado, y luego Play. *Di:* «El pad 32 graba la salida: mientras lo mantienes, graba, hasta unos tres segundos y medio; un toque corto graba hasta el siguiente toque. Shift más el pad 32 la arma: graba el compás siguiente o, parado, desde Play.»
9. **Tocarla.** *Muestra:* el pad 7; K1-K4; los colores de K2; Shift + pad 7. *Di:* «El pad 7 toca la captura: K1, el pitch; K2, el modo, one-shot, gate o loop; K3, el inicio; y K4, el final. Shift más el pad 7 fija un bucle hasta que lo vuelvas a pulsar.»
10. **Qué graba.** *Di:* «La captura graba la mezcla sin los efectos de Master FX, y antes del filtro master; lo que suena al reproducirla sí pasa por los efectos. Para conservarla, ponla en un drum (vídeo 21) y guarda el proyecto.»
11. **[Beta] A través de un cambio de proyecto.** *Muestra:* un bucle fijado; carga otro proyecto; Play parpadea en verde. *Di:* «En la Beta, un bucle fijado sigue sonando cuando cargas otro proyecto: Play parpadea, y el proyecto nuevo empieza justo cuando el bucle da la vuelta.»

*Capítulo 4: los huecos*

12. **Asignar.** *Muestra:* mantén el pad 1 y toca el pad 26; toca el pad 26 solo. *Di:* «La fila de abajo, los pads 26 a 30, guarda efectos con sus ajustes. Mantén un efecto, o el pad 7, o el 31, y toca un hueco: el hueco lo guarda con una copia de sus knobs. Toca el hueco para activarlo, y Shift más el hueco para fijarlo.»
13. **El secuenciador de efectos.** *Di:* «Estos huecos son lo que toca, paso a paso, el motor secuenciador de efectos de las pistas MIDI.»

*Capítulo 5: el Glitch y el gesto mecánico*

14. **Glitch.** *Muestra:* mantén el pad 6; K1 de arriba abajo; K4, mitad de abajo y mitad de arriba. *Di:* «El Glitch convierte la salida en una cabeza de cinta sobre los últimos segundos: K1 es la velocidad, normal arriba, parada en el medio y hacia atrás abajo; K2 repite; K3 es el retraso; y K4, caos en su mitad de abajo y sobrecarga en la de arriba.»
15. **Gesto mecánico.** *Muestra:* pulsa y suelta el pad 31; K2 por sus colores. *Di:* «El pad 31 es un gesto mecánico: al pulsarlo, la música se frena hasta pararse; al soltarlo, vuelve a arrancar. K1 marca cuántos movimientos; K2, el tipo, de la parada de cinta al scratch, el tear, el back spin y el rattle; y K3 y K4, los tiempos de parada y de arranque.»
16. **Cierre.** *Di:* «Cada proyecto recuerda sus ajustes de Master FX: los veinte knobs, los huecos y el compresor.»

**A tener en cuenta**
- Clear + knob a la derecha = valor por defecto; Master FX no tiene automatización, así que aquí no hay rojo.
- Los efectos fijados, el song pointer y el sample fijado están apagados tras reiniciar.
- Una captura sin usar se pierde al apagar.
- El gesto mecánico usa el motor del Glitch: mientras suena el gesto, el Glitch espera.

---

## 24 · Vista FX

**Guía:** [7.1](GUIA.md#vista-fx) · **Duración:** unos 4 min

**Antes de grabar**
- Un proyecto con algo de envío a la reverb y al delay.

**En esta vista**
- Los parámetros propios de la reverb y del delay.
- Un reset rápido.
- La resonancia del filtro master y un interruptor para apagarlo.

**Guion**

1. **Envíos.** *Muestra:* FX; Octave ▲ / ▼. *Di:* «La vista FX ajusta los envíos de reverb y de delay de cada pista, como siempre; Octave elige delay o reverb.»
2. **Parámetros de los efectos.** *Muestra:* Shift + K1-K3 (reverb); Octave, Shift + K1-K6 (delay). *Di:* «Shift más un knob llega a los propios efectos: en la reverb, tipo, decay y damping; en el delay, time, sync, feedback, width, ratio y slew. Se guardan con el proyecto.»
3. **Reset.** *Muestra:* Duplicate. *Di:* «Duplicate hace un reset: envíos a cero, el filtro master al centro y Master FX apagado.»
4. **Resonancia del filtro master.** *Muestra:* Shift + Octave ▲ / ▼ (en amarillo con Shift). *Di:* «Shift más Octave sube o baja la resonancia del filtro master de 16 en 16.»
5. **Apagar el filtro master.** *Muestra:* Shift + pad 25; el LED del knob del filtro en rojo; mueve el knob del filtro; Shift + pad 25 otra vez. *Di:* «Shift más el pad 25 apaga el filtro master: suena como si estuviera centrado aunque muevas su knob, y el LED del knob se pone rojo. Vuelve a encenderlo y regresa a donde esté el knob.»
6. **La fila de abajo.** *Di:* «La fila de abajo es la de Master FX: los huecos, el gesto mecánico y la captura.»

**A tener en cuenta**
- Si en Setup los retornos van por las tiras 3 / 4 del mixer, sus envíos aquí tienen tope a la mitad.
- El filtro master, su resonancia y su interruptor de apagado no se guardan: tras reiniciar empiezan de cero, como en el original.

---

## 25 · Vista Sidechain

**Guía:** [8.1](GUIA.md#sidechain) · **Duración:** unos 5 min

**Antes de grabar**
- Un bombo en Drum 1 y un bajo sostenido en Synth 1; el compresor master encendido en Advanced Setup.

**En esta vista**
- La envolvente del sidechain en los knobs, más allá de los presets.
- El ataque y el release del compresor master.
- Patrones de Synth o de MIDI como fuentes del sidechain; sidechain entre drums.

**Guion**

1. **Abrirla.** *Muestra:* Shift + FX; toca un preset para Synth 1. *Di:* «Shift más FX abre la vista Sidechain. Los presets funcionan como siempre.»
2. **La envolvente.** *Muestra:* K1-K4 en el color de Synth 1. *Di:* «K1 a K4 moldean el ducking de la pista cuyo preset tocaste por última vez: ataque, hold, decay y profundidad. Ya no tienes que elegir entre presets fijos.»
3. **Compresor master.** *Muestra:* K7 / K8 (en blanco). *Di:* «K7 y K8 son el ataque y el release del compresor master, y se guardan con el proyecto.»
4. **Patrones como fuente.** *Muestra:* fila 1, pad 1 (Synth 1 como fuente para otra pista). *Di:* «En la fila 1, los pads 1 a 4 añaden Synth 1, Synth 2, MIDI 1 y MIDI 2 como fuentes, junto a los drums de los pads 5 a 8: cada nota del patrón de esa pista agacha la pista elegida, como lo haría un golpe de drum. Las notas tocadas en directo, no.»
5. **Entre drums.** *Muestra:* Octave ▼; una página de drums; K1-K4 en el color del drum. *Di:* «Octave abajo enseña las páginas del sidechain entre drums: un drum agachando a otro. En una página de drums, K1 a K4 ajustan también la envolvente de ese drum.»
6. **Cierre.** *Di:* «En el siguiente: los patrones y las cadenas.»

**A tener en cuenta**
- El brillo de los knobs sube en curva, para que los presets se distingan a simple vista.
- Los disparos de un drum por otro drum o por un patrón (en las páginas de drums) no se guardan, igual que los presets del sidechain entre drums.

---

## 26 · Vista Patterns y cadenas de patrones

**Guía:** [9.1](GUIA.md#patterns) · **Duración:** unos 7 min (capítulos: reglas de cadena / [Beta] mutate de patrones / [Beta, sin publicar] cadenas de grupos)

**Antes de grabar**
- Synth 1 y Drum 1 con tres o cuatro patrones distintos cada uno.

**En esta vista**
- Reglas de cadena: «toca A n veces y luego B; la vez siguiente, C».
- [Beta] Mutate de patrones.

**Guion**

*Capítulo 1: reglas de cadena*

1. **Modo cadena.** *Muestra:* Patterns; mantén Shift (Octave en amarillo); Shift + Octave ▲ (verde). *Di:* «En la vista Patterns, Shift más Octave arriba enciende el modo cadena de todo el proyecto. Shift más Octave abajo lo apaga; las reglas siguen guardadas.»
2. **Una regla.** *Muestra:* toca el patrón 1 (amarillo), otra vez dos veces (los LEDs de los knobs cuentan 3); toca el patrón 2 (verde); toca el patrón 3 (rojo). *Di:* «En el modo cadena, toca un patrón: ese es A, en amarillo. Tócalo otra vez para añadir repeticiones, hasta ocho; los LEDs de los knobs las cuentan. Toca otro patrón de la pista: ese es B, en verde; el siguiente es C, en rojo.»
3. **Qué toca.** *Muestra:* reproduce: A A A B A A A C. *Di:* «Con tres repeticiones, la pista toca A tres veces y luego B; otra vez A tres veces, y luego C. Sin C: A A A B. B y C suenan una vez y la pista vuelve a A.»
4. **Clear.** *Muestra:* en el modo, Clear + patrón. *Di:* «Clear más un patrón quita su regla. Fuera del modo cadena, borra el patrón, como siempre, con su regla incluida.»

*Capítulo 2: [Beta] mutate de patrones*

5. **Mutate.** *Muestra:* Shift + toque a Duplicate; patrones que se apagan en una columna. *Di:* «En la Beta, Shift más un toque a Duplicate le da a cada pista elegida una lista corta de sus patrones en otro orden, que suena en bucle en lugar de la cadena. Los patrones en sí no cambian. Otro toque, otra lista.»
6. **Ajustes.** *Muestra:* Shift + Duplicate mantenido: la página de ajustes en melocotón. *Di:* «Mantén Shift más Duplicate para ver los ajustes: la longitud de la lista, cuánto cambia, si se permiten repeticiones y si se conserva el primer hueco. Clear más Duplicate termina las listas.»

*Capítulo 3: [Beta, sin publicar] cadenas de grupos*

7. **Grupos.** *Muestra:* Shift + un pad de inicio + un pad de final; K1 para las repeticiones. *Di:* «En las betas más nuevas, las reglas pasan a ser grupos: cada pista toca un tramo de patrones A unas cuantas veces, luego B, luego C, y vuelve a A. En el modo cadena, Shift más un pad de inicio y uno de final forma el grupo siguiente, y K1 fija sus repeticiones. Cada escena guarda sus propias cadenas.»
8. **Cierre.** *Di:* «Las reglas viajan con el patrón cuando lo duplicas; el modo se guarda con el proyecto y con cada escena: eso, en el siguiente vídeo.»

**A tener en cuenta**
- Una escena termina cuando termina su cadena más larga.
- Los pads de pista que parpadean en el Mixer indican que esa pista está siguiendo una regla.

---

## 27 · Vista Mixer y escenas

**Guía:** [9.2](GUIA.md#mixer) · **Duración:** unos 7 min (capítulos: niveles y mutes / escenas / modo cue)

**Antes de grabar**
- Las ocho pistas sonando; dos escenas guardadas, una de ellas en modo cadena; unos auriculares en la salida derecha para el capítulo del cue.

**En esta vista**
- Nivel a 100 o a 0 de un solo gesto.
- Mutes en el compás siguiente.
- Escenas con modo cadena y repeticiones.
- El modo cue: escucha pistas por la salida derecha antes de meterlas.

**Guion**

*Capítulo 1: niveles y mutes*

1. **A tope o en silencio.** *Muestra:* Shift + un knob de nivel a la derecha / a la izquierda. *Di:* «En el Mixer, Shift más un knob de nivel girado a la derecha deja esa pista a 100, y a la izquierda, a cero, de un solo gesto. Sale por MIDI y se graba como un giro.»
2. **Mute al compás.** *Muestra:* Shift + pad 3 (parpadea); empieza el compás: silenciada. *Di:* «Shift más un pad de pista la silencia o la activa justo en el compás siguiente; el pad parpadea mientras espera, y otra vez lo cancela. Con el transporte parado, pasa al momento.»
3. **[Beta] Solo.** *Muestra:* el pad 16 mantenido + los pads 1 y 5; un toque al pad 16. *Di:* «En la Beta, mantén el pad 16 y pulsa pistas: solo. Un toque al pad 16 devuelve los mutes de antes. Un toque al pad 16 sin ningún solo activo es el solo flip: las pistas que mantienes suenan solas hasta que las sueltas.»

*Capítulo 2: escenas*

4. **El modo cadena en las escenas.** *Muestra:* los pads de escena: melocotón = guardada en modo cadena. *Di:* «Los pads de escena funcionan como siempre. Una escena guardada en modo cadena se ve en melocotón y, al cargarla, recupera el modo.»
5. **Repeticiones.** *Muestra:* Shift: la fila 2 en amarillo; Shift + pad 11 (3 repeticiones); sonando: la repetición actual en blanco. *Di:* «Shift más los pads 9 a 16 fijan cuántas veces se repite la escena actual, de una a ocho. Mientras suena, al mantener Shift ves en blanco qué repetición está sonando.»

*Capítulo 3: modo cue*

6. **Encenderlo.** *Muestra:* la página de panorama (Octave ▼); Shift + un knob (Octave en rosa). *Di:* «En la página de panorama, Shift más un knob enciende el modo cue: la salida izquierda lleva la mezcla en mono, y la derecha es tu cue.»
7. **Envíos al cue.** *Muestra:* gira knobs de panorama a la derecha (rosa, más brillantes). *Di:* «Ahora los knobs de panorama son el envío de cada pista al cue. Una pista silenciada en el cue suena solo por la derecha, a tiempo: métela en la mezcla cuando esté lista.»
8. **Escucha previa y clic.** *Muestra:* elige un patch de Synth 1: se oye solo por la derecha. *Di:* «Con el modo cue encendido, elegir un patch de sinte, o Shift más un sample de drum, se oye solo en el cue. El metrónomo también va solo al cue.»
9. **Cierre.** *Di:* «Mixer otra vez: Master FX. En el siguiente: los proyectos.»

**A tener en cuenta**
- El modo cue se guarda en el aparato; los envíos al cue, con el proyecto.
- La reverb, el delay y Master FX son los de la mezcla: el cue también los oye.
- Guardar otra vez una escena no cambia sus repeticiones.

---

## 28 · Vista Projects

**Guía:** [10.1](GUIA.md#projects) · **Duración:** unos 3 min

**Antes de grabar**
- Un proyecto guardado en el hueco 1; un hueco vacío; un segundo pack.

**En esta vista**
- Copiar un proyecto a otro hueco o a otro pack.

**Guion**

1. **Elegir la fuente.** *Muestra:* Projects; Duplicate + pad 1 (amarillo, parpadeando). *Di:* «En la vista Projects, Duplicate más un proyecto lo elige como fuente: parpadea en amarillo. Duplicate más ese proyecto otra vez lo olvida.»
2. **Copiar.** *Muestra:* Duplicate + un pad vacío: copiado. *Di:* «Duplicate más un hueco vacío lo copia ahí al momento.»
3. **Sobre un hueco ocupado.** *Muestra:* Duplicate + un hueco ocupado: parpadea en blanco; Duplicate + ese hueco otra vez. *Di:* «Sobre un hueco ocupado, primero pregunta: el hueco parpadea en blanco, y Duplicate más ese hueco otra vez, antes de cinco segundos, lo sobrescribe. El proyecto cargado no se sobrescribe nunca.»
4. **Otro pack.** *Muestra:* elige la fuente, carga otro pack, Projects, Duplicate + hueco. *Di:* «Para copiarlo a otro pack: elige la fuente, carga el otro pack, vuelve a Projects y Duplicate más el hueco. Allí suena con los patches y los samples de ese pack.»
5. **Cierre.** *Di:* «Mientras copia, el aparato se queda en pausa un momento.»

**A tener en cuenta**
- Lo que se copia es el proyecto tal como está guardado en la tarjeta: guárdalo antes.
- Copiar *escribe en la tarjeta*.

---

## 29 · Vista de packs

**Guía:** [10.2](GUIA.md#packs) · **Duración:** unos 3 min

**Antes de grabar**
- Un pack de sobra que no te importe borrar.

**En esta vista**
- Borrar packs desde el aparato.
- El pack interno está protegido.

**Guion**

1. **Abrirla.** *Muestra:* Shift + Projects; Clear encendido en blanco. *Di:* «Shift más Projects abre los packs, como siempre.»
2. **Borrar.** *Muestra:* Clear: parpadean los packs que se pueden borrar; toca uno: solo parpadea ese; Clear: borrado. *Di:* «Para borrar un pack: Clear, y durante cinco segundos parpadean los packs que puedes borrar. Toca uno: ahora solo parpadea ese, y no se carga. Clear otra vez antes de cinco segundos: borrado.»
3. **El pack interno.** *Di:* «El primer pack, el de la memoria interna, es de solo lectura para el mod: no se puede borrar, y no se escribe en él nada del mod. Aun así, puedes copiar desde él a un pack de la tarjeta.»
4. **Cierre.** *Di:* «El hueco de un pack borrado se puede volver a usar después de reiniciar.»

**A tener en cuenta**
- El pack cargado no se puede borrar nunca.
- Borrar es definitivo: haz antes una copia de la tarjeta.

---

## 30 · Guardar: qué se conserva y dónde

**Guía:** [11](GUIA.md#datos-patron) · **Duración:** unos 6 min

**Antes de grabar**
- Nada especial: este vídeo es sobre todo explicación, con unos pocos gestos.

**En este vídeo**
- Qué viaja con un patrón.
- Los cuatro sitios donde se guardan las cosas.
- Qué se pierde al reiniciar.
- Guardar sin riesgos.

**Guion**

1. **Intro.** *Di:* «Último vídeo: adónde va tu trabajo y cómo asegurarte de que se guarda.»
2. **Save dos veces.** *Muestra:* Save (destella en blanco), Save (verde). *Di:* «Save dos veces guarda el proyecto en su hueco; Save más el pad de un hueco, en Projects, lo guarda en otro. Todo lo que en esta serie hemos llamado “se guarda con el proyecto” o “con el patrón” solo llega a la tarjeta así.»
3. **El patrón.** *Di:* «Un patrón lleva sus notas, su automatización, sus sample flips, sus ajustes y los datos de los pasos que añade el mod: frecuencia, dinámicas, random-mutate, órdenes, reglas de cadena y los pasos que sueltan la automatización. Duplicar un patrón copia todo eso. La excepción es el arpegiador: se guarda en el proyecto por número de patrón.»
4. **Knobs frente a automatización.** *Di:* «Un knob girado sin Record cambia el sonido del proyecto, no el patrón. Para que cambie en un paso, grábalo.»
5. **Los cuatro sitios.** *Muestra:* rótulos: patrón / proyecto / pack / ajustes del aparato. *Di:* «El proyecto guarda el sonido de los sintes, los knobs de los drums, los ajustes de Master FX, las escalas y las cadenas. El pack guarda lo que guardas a propósito: patches, samples y copias, y se escribe al momento. Los ajustes del aparato guardan lo que eliges en Setup y en Advanced Setup, y el motor de las pistas MIDI. Y algunas cosas viven solo en la memoria.»
6. **Lo que se pierde al reiniciar.** *Di:* «Tras reiniciar: el filtro master y su resonancia vuelven a su valor inicial, el clic está apagado, los efectos fijados y el song pointer están apagados, los latch y las pantallas de acordes desaparecen, y una captura sin usar está vacía.»
7. **Apagar.** *Di:* «Antes de apagar: para el secuenciador, espera dos segundos y usa el botón de encendido. Si hay un guardado diferido pendiente, para primero.»
8. **Las versiones S y el pack interno.** *Di:* «Con una versión S, o en el pack interno, el mod no escribe nada propio: los patches, los samples y las copias no se guardan, y Save se pone rojo. Los proyectos se guardan como en el original.»
9. **[Beta, sin publicar] Volver al patrón guardado.** *Di:* «En las betas más nuevas, Clear más Duplicate dos veces en la vista de una pista devuelve ese patrón a como está en la tarjeta.»
10. **Cierre.** *Di:* «Y hasta aquí la serie. La guía por vistas tiene todos los detalles; la lista de características lo resume todo.»

**A tener en cuenta**
- [Beta, sin publicar] Los carriles extra del sinte propio y las cadenas de grupos viven en el fichero del proyecto: una copia de seguridad de Components no los lleva; el Snapshot de la app de la tarjeta, sí.
- Los proyectos guardados con el mod se abren con el firmware oficial, sin los extras del mod.
