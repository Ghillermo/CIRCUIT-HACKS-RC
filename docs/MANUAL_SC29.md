# Manual de uso — Circuit Tracks con SC29

Todo lo que el firmware **SC29** añade al Circuit Tracks (firmware oficial 1.2.1, build 4486) y cómo se maneja. Lo que no aparece aquí funciona como en el aparato original.

> **Estado:** SC27, SC28 y SC29 están probadas solo en emulación. Las funciones de SC23.6 y anteriores se han usado en el aparato; SC25 y SC26, por encima. Si algo no se comporta como dice este manual es un fallo de este firmware, no de Novation. Instalación, recuperación y plan de prueba: `README.md`, `LEEME.md` y `firmware/sc29/PRUEBA.md`.

**Convenciones**
- Los **pads** se numeran 1-32, de arriba-izquierda a abajo-derecha (fila 1 = 1-8, fila 2 = 9-16, fila 3 = 17-24, fila 4 = 25-32).
- Los **knobs** son K1-K8 (K1-K4 fila superior, K5-K8 fila inferior).
- **Shift + knob / pad** = mantener Shift mientras se gira o se toca.
- **Clear + knob** = mantener Clear y girar el knob: vuelve a su valor por defecto (el LED se pone rojo).
- El LED de cada knob enseña el valor con el **brillo**; en los knobs de «tipo», el **color** indica el modo.

## Índice
1. [Pistas MIDI 1 / 2: VCA-VCF, osciladores y VA-drum](#1-pistas-midi-1--2-vca-vcf-osciladores-y-va-drum)
2. [Step-drummer](#2-step-drummer)
3. [Editor de CC de los macros MIDI](#3-editor-de-cc-de-los-macros-midi)
4. [Drums](#4-drums)
5. [Master FX y song pointer](#5-master-fx-y-song-pointer)
6. [Vista FX](#6-vista-fx)
7. [Sintes: fuente externa](#7-sintes-fuente-externa)
8. [Setup y MIDI](#8-setup-y-midi)
9. [Tablas MIDI](#9-tablas-midi)
10. [Qué se guarda y dónde](#10-qué-se-guarda-y-dónde)
11. [Resumen por vista](#11-resumen-por-vista)

---

## 1. Pistas MIDI 1 / 2: VCA-VCF, osciladores y VA-drum

Cada pista MIDI tiene un «sinte» propio dentro del aparato: la **entrada de audio** de la pista (línea 1 para MIDI 1, línea 2 para MIDI 2) o un **oscilador interno** pasa por VCA, efecto y filtro, con envolvente y LFO, antes de la tira 3 / 4 del mixer. Lo disparan las **notas de la pista** (secuenciadas o tocadas). La pista sigue mandando su MIDI como siempre.

### 1.1 Pads de la vista Preset
Selecciona MIDI 1 o MIDI 2 y pulsa **Preset**.

| Pad | Función |
|---|---|
| **27** | **Motor de la pista**, cuatro estados: **apagado** → **entrada de línea** (naranja) → **oscilador** (verde) → **VA-drum** → apagado. Apagado = los knobs son los macros MIDI normales. |
| **1-5** | Con el pad 27 encendido: **página de knobs** (ver 1.2). Con el pad 27 apagado: las plantillas de CC de siempre (pads 1-8). |
| **28** | Uno o **dos osciladores** (encendido = dos). |
| **29** | **Orden de la cadena**: apagado = VCA → FX → filtro; encendido = filtro → VCA → FX. |
| **30** | **Step-drummer** (sección 2). |
| **31** | Solo en VA-drum: la **velocity** también escala las envolventes de pitch y de filtro. |
| 25 | **Editor de CC** (sección 3). |
| 26 | **Patch flip**: cada nota se envía como Program Change. Se apaga al encender el motor, y viceversa. |

Con los valores por defecto, la entrada de línea pasa limpia (bypass).

### 1.2 Páginas de knobs

| Pad | Página |
|---|---|
| 1 | VCA-VCF |
| 2 | OSC 1 |
| 3 | OSC 2 (solo con dos osciladores) |
| 4 | Secuenciables: los 8 valores que el secuenciador puede automatizar |
| 5 | Modulación: envolvente arriba, LFO abajo |

Las páginas 4 y 5 no añaden valores: son otra disposición de los mismos.

**Página 1 — VCA-VCF**

| Knob | Solo | Con Shift |
|---|---|---|
| K1 | Ataque | Sustain |
| K2 | Release | Decay |
| K3 | Envolvente → nivel (bipolar) | LFO → nivel, trémolo (bipolar) |
| K4 | Envolvente → filtro (bipolar) | LFO → filtro (bipolar) |
| K5 | Filtro (izquierda paso bajo, derecha paso alto, centro abierto) | **Tipo de filtro**: DJ, LP 12, HP 12, paso banda, notch, LP 24, HP 24. Dentro de cada tipo, la posición es el seguimiento de la nota |
| K6 | Resonancia | Gain del VCA (por encima del centro, hasta +18 dB con saturación) |
| K7 | Velocidad del LFO | — |
| K8 | Cantidad de efecto | **Tipo de efecto**: saturación suave, dura, plegado, wavefold, ring mod, comb, chorus. Dentro de cada tipo, la posición es su parámetro |

Los knobs de tipo van de 0 a 127 con tope (unos 18 pasos por tipo): color = tipo, brillo = posición dentro del tipo.

**Página 2 — OSC 1**

| Knob | Solo | Con Shift |
|---|---|---|
| K1 | TUNE (semitonos) | FINE |
| K2 | SHAPE (wavefold en seno / triángulo, pendiente en sierra, ancho en cuadrada) | **MIX** OSC 1 ↔ OSC 2 |
| K3 | Envolvente → tono | **BITSYNC**: nada, sync suave, xor, or, nor, and, nand |
| K4 | Envolvente → forma | — |
| K5 | LFO → tono | — |
| K6 | LFO → forma | — |
| K7 | WAVE: morph continuo seno → triángulo → sierra → cuadrada | — |
| K8 | LFO → morph | Envolvente → morph |

En BITSYNC, la posición dentro de la zona es: en Sync, cada cuántos ciclos de OSC 1 se invierte OSC 2 (1 a 8); en las zonas bit a bit, la cantidad.

**Página 3 — OSC 2**

| Knob | Solo | Con Shift |
|---|---|---|
| K1 | TUNE 2 | FINE 2 |
| K2 | SHAPE 2 | **FM** (OSC 2 modula la fase de OSC 1) |
| K3 | — | **RING** |
| K7 | WAVE 2 | — |

Las modulaciones de envolvente y LFO son las de OSC 1 y valen para los dos.

**Página 4 — Secuenciables** (Shift no hace nada)

| K1 | K2 | K3 | K4 | K5 | K6 | K7 | K8 |
|---|---|---|---|---|---|---|---|
| TUNE | Release | Env → nivel | Env → filtro | Filtro | Resonancia | Velocidad del LFO | Cantidad de efecto |

**Página 5 — Modulación**

| | K1 | K2 | K3 | K4 | K5 | K6 | K7 | K8 |
|---|---|---|---|---|---|---|---|---|
| Solo | Ataque | Decay | Sustain | Release | Velocidad LFO | LFO → filtro | LFO → nivel | LFO → tono |
| Shift | Env → nivel | Env → filtro | Env → tono | Env → forma | LFO → forma | LFO → morph | Env → morph | — |

### 1.3 Dos osciladores y parafonía
Con el pad 28 encendido:
- una nota = los dos osciladores al unísono (cada uno con su TUNE / FINE);
- dos notas = una por oscilador;
- la tercera sustituye a la más antigua. Las notas sustituidas no vuelven al soltar.

La envolvente se reinicia con cada nota; la velocity es la de la última. El seguimiento de la nota del filtro usa la media de las dos.

### 1.4 Motor VA-drum
Cuarto estado del pad 27. Es el oscilador (con todo lo anterior: uno o dos osciladores, FM, ring, sync, efecto, filtro) pensado para percusión; inspirado en otros sintetizadores percusivos por pasos. **Los knobs son los mismos y guardan los mismos valores; cambia su significado:**

| Knob | En el oscilador normal | En VA-drum |
|---|---|---|
| Ataque | ataque | ataque del VCA (0 = golpe inmediato) |
| **Decay** | decay | **decay del VCA**, hasta el silencio |
| **Sustain** | nivel de sustain | **decay de la envolvente de pitch** |
| **Release** | release | **decay de la envolvente de filtro** |
| Env → nivel / → filtro / → tono | una envolvente para todo | cada una usa **su** envolvente (VCA / filtro / pitch) |
| **Velocidad del LFO** | velocidad del LFO | **nivel de ruido blanco** sumado al oscilador |
| LFO → filtro / nivel / tono / forma / morph | LFO en diente de sierra | **valor aleatorio** (sample & hold) hacia ese destino |

- El VCA es de **un solo disparo**: la duración de la nota no importa y soltar no corta el sonido. Cada nota nueva vuelve a disparar las tres envolventes.
- **Pad 31**: con él encendido, los golpes suaves tienen menos barrido de tono y de filtro. La velocity escala el nivel siempre.
- Al entrar en VA-drum, Sustain, Release y Velocidad del LFO conservan su valor: ajústalos.

*Punto de partida para un bombo:* un oscilador, WAVE en seno; Ataque 0, Decay ~70, Sustain ~30, Env → nivel al máximo, Env → tono hacia la derecha, ruido a 0. *Caja:* sube el ruido, baja el Decay, filtro paso alto o paso banda.

### 1.5 Automatización y MIDI de estos valores
- **Secuenciador:** con Record + Play, mover uno de los 8 knobs de la página 4 graba su movimiento en el patrón. Los demás valores no se automatizan. Son los mismos carriles que los de los macros MIDI de la pista.
- **Salida MIDI:** cada cambio de knob sale como CC o NRPN por el canal de la pista (tabla en 9.1).
- **Entrada MIDI:** los mismos CC / NRPN, recibidos por el canal de la pista con el motor encendido, ponen los valores.

---

## 2. Step-drummer

Un modo de secuenciación por **pares de pasos**, sobre el patrón normal de la pista: los 8 knobs son los 8 pares de pasos de la mitad del patrón que se ve. Funciona en MIDI 1 / 2 y en Synth 1 / 2.

> **Desde SC31:** al abrir la vista y al editar, cada paso **conserva la altura de su primera nota** (con su duración y velocity); de un acorde queda solo la primera nota. Una nota nueva toma la nota de su par o la de la nota anterior más cercana (la tónica si no hay ninguna), y la escucha suena con la nota del paso.
>
> **Hasta SC30 (destructivo):** todas las notas del patrón pasaban a ser la tónica de la escala en la octava 2, una por paso; se perdían acordes y alturas.

### 2.1 Entrar y salir

| Pista | Cómo se abre |
|---|---|
| MIDI 1 / 2 | Vista Preset, motor encendido (pad 27), **pad 30** |
| Synth 1 / 2 | Con la vista del sinte en pantalla, **pulsa su botón otra vez** (vista de la fuente) y ahí **pad 30** |

- Pad 30 brillante = vista abierta; tenue = cerrada. Otra pulsación la cierra.
- En MIDI, **Shift + pad 30** desactiva el step-drummer (pad apagado). Con la vista cerrada pero activado (tenue), los knobs vuelven a ser los del motor y la fila de pitch sigue sonando.
- Pulsar un botón Synth cierra la vista.

### 2.2 Controles de la vista

| Control | Función |
|---|---|
| **Pads 1-16** | Los 16 pasos de la mitad mostrada. Dos colores alternos por pares; brillante = hay nota, tenue = vacío, **blanco** = el paso que suena. **Tocar** = escuchar el paso. **Shift + tocar** = poner / quitar su nota. |
| **Pads 17-24** | **Destino de la fila de pitch** (uno encendido). |
| **K1-K8** | Los 8 pares de pasos. El knob del par que suena se ve **blanco**. |
| **Octave ▲** | Página de **pitch** (brillante cuando está elegida). |
| **Octave ▼** | Página de **velocity**. |
| **1-16 / 17-32** | La otra mitad del patrón (brillante = pasos 17-32). |

- **Página velocity:** la velocity de las notas del par. A 0 el par se queda sin notas; al subir desde 0 se crea una nota en el primer paso del par.
- **Nota nueva** (Shift + pad): toma la velocity de su par; si está vacío, la de la nota anterior más cercana; si no hay ninguna, 64. Dura un paso.

### 2.3 Página pitch en las pistas MIDI
El valor del par (0-127, **64 = sin cambio**) es un **desplazamiento** que se suma al destino mientras suena ese paso. El knob normal del motor sigue siendo la base.

| Pad | Destino | Rango |
|---|---|---|
| 17 | Tono de los dos osciladores | ±12 semitonos |
| 18 | Tono solo de OSC 2 | ±12 semitonos |
| 19 | WAVE | ±64 pasos |
| 20 | FM | ±64 |
| 21 | MIX | ±64 |
| 22 | Envolvente → filtro | ±64 |
| 23 | SHAPE | ±64 |
| 24 | Decay | ±64 |

Con el step-drummer activado, el carril de TUNE (K1 de la página 4) queda ocupado por la fila de pitch: TUNE ya no se graba ni se reproduce como automatización.

### 2.4 Página pitch en los sintes
- **Pads 17-24 = macro 1 … macro 8** del sinte.
- El valor del par es la **posición absoluta** de ese macro (0-127), escrita como automatización normal del macro. Un par sin valor muestra la posición actual del macro.
- Lo que suena depende del parche (a qué está asignado el macro).
- Para borrar la automatización: Clear + knob del macro en la vista normal del sinte.
- Los pads 25-29 (fuente del sinte, sección 7) siguen funcionando con la vista abierta.

---

## 3. Editor de CC de los macros MIDI

Cambia desde el aparato qué CC manda cada macro de una plantilla MIDI (antes solo con Components).

1. Vista Preset de MIDI 1 / 2, **pad 25** (se enciende).
2. **Mueve un knob**: queda elegido y su número de CC se dibuja con los 32 pads.
3. **Octave ▼ / ▲**: siguiente / anterior campo del knob elegido.
4. **Gira el knob** para cambiar el valor del campo que se muestra.
5. **Guardar:** el pad **26** (Save) en cualquier momento, o avanza con Octave ▼ hasta el paso de guardar (el pad 26 y el botón Save parpadean) y pulsa Octave ▼ una vez más.
6. **Descartar:** cualquier botón de vista (también el de la propia pista), el pad 25 o un pad de plantilla.

| El número del primer campo | Tipo | Campos |
|---|---|---|
| Cualquier otro | CC | número, inicio, fin |
| 99, 98 o 6 | NRPN de 7 bits | número, MSB, LSB, inicio, fin |
| 38 | NRPN de 14 bits | número, MSB, LSB, inicio (MSB, LSB), fin (MSB, LSB) |

---

## 4. Drums

### 4.1 Knobs (drum seleccionado)
Los knobs siguen las etiquetas del panel. Los parámetros de stock conservan su MIDI y su valor.

| Knob | Solo | Con Shift |
|---|---|---|
| K1 Oscillator | Pitch (en semitonos exactos) | Cantidad de la envolvente de tono |
| K2 Osc mod | Frecuencia del ring mod | Cantidad del ring mod |
| K3 Amp envelope | Decay; a la izquierda de 0, **punto de inicio** del sample | — |
| K4 Filter envelope | Envolvente → corte | Forma de la envolvente |
| K5 Filter frequency | Filtro / EQ | **Modo de filtro**: DJ, paso banda, notch, comb, EQ tilt |
| K6 Resonance | Resonancia | — |
| K7 Modulation | Cantidad del LFO | Velocidad del LFO |
| K8 FX | Distorsión; a la izquierda de 0, **bitcrush** | **Tipo de distorsión**: stock, suave, dura, plegada |

- **Clear + knob** restablece las dos capas del knob (sola y con Shift).
- Todo se guarda con el proyecto.
- Los parámetros nuevos tienen NRPN de entrada y salida (tabla 9.2).

### 4.2 Vista cromática / de escala
- **Shift + Preset** con un drum seleccionado: los pads tocan el sample transpuesto según la escala y la tónica de la vista Scales.
- En esa vista, **K1** = sesgo de tono en semitonos y **Shift + K1** = afinación fina en cents.
- Con el secuenciador grabando, se graba por paso el tono tocado.
- En la vista **Note**, los pads 25-28 repiten los cuadros de los drums 4 … 1.

### 4.3 Sidechain entre drums
**Shift + FX** y **Octave ▼**: dos páginas nuevas (drums 1-2 y drums 3-4).
- Filas 3 y 4: preset de ducking de cada drum.
- Fila 1, pads 5-8: qué drum dispara.

---

## 5. Master FX y song pointer

**Entrar:** estando en el Mixer, pulsa **Mixer otra vez**. Cualquier otro botón de vista sale.

### 5.1 Efectos

| Pad | Efecto |
|---|---|
| 1 | Gater |
| 2 | Auto-Filter paso bajo |
| 3 | Auto-Filter paso alto |
| 4 | Digitise |
| 5 | Phaser |
| 6 | Vinyl |
| 7 | **Saltar** (song pointer, ver 5.2) |
| 8 | **Apagar todo** lo fijado (efectos y song pointer); también hace bypass de los FX |

- **Mantener** un pad = activo mientras se pulsa. **Shift + pad** = queda fijo. Tocar un efecto fijo lo suelta.
- **K1-K4** = los cuatro parámetros del último efecto tocado (los dos Auto-Filter comparten parámetros). El brillo del LED es el valor.
- **Fila inferior (pads 25-32):** los efectos de actuación de la vista FX (Gater por divisiones, Auto-Filter) y **huecos asignables**: un hueco guarda un efecto con una copia de sus cuatro parámetros.
- Los 20 parámetros tienen NRPN de entrada y salida (tabla 9.3).

### 5.2 Song pointer (pads 9-24 = pasos 1-16)
- **Mantener un paso:** el bucle retoma ahí mientras se pulsa.
- **Shift + paso:** queda fijado. Con dos pasos, el anterior es el inicio y el posterior el fin del bucle, se pulsen en el orden que sea.
- **Pad 7 (saltar):** mantenido, o fijado con Shift, el paso que toques suena en el siguiente paso y **se repite mientras su pad siga pulsado**. Tocar el pad 7 fijado lo suelta.
- El cabezal se ve en blanco mientras el secuenciador corre.
- Al cargar un proyecto, Master FX y el song pointer empiezan apagados.
- **Desde SC30:** al cambiar de sesión o empezar un proyecto nuevo se mantienen las asignaciones de la fila inferior y los parámetros de los efectos. Las asignaciones se guardan con el proyecto y vuelven al encender; los parámetros de la fila superior no sobreviven al apagado.

---

## 6. Vista FX

Botón **FX**.

| Control | Función |
|---|---|
| **Octave ▲ / ▼** | Eligen si los knobs controlan los envíos de reverb o los de delay |
| **Shift + knob** | **Parámetros del efecto.** Reverb: tipo, decay, damping. Delay: time, sync, feedback, width, ratio, slew |
| **Duplicate** | Reset de envíos, filtro master y Master FX |
| **1-16 / 17-32** | Sube un paso la resonancia del filtro master |

Si en Setup el retorno de reverb / delay va a la tira 3 / 4 (sección 8), los envíos de esas tiras (K3 / K4) tienen tope a la mitad y van a media velocidad, para que la realimentación no se dispare.

---

## 7. Sintes: fuente externa

En lugar del ruido del parche, el sinte puede usar la **entrada de línea**, que pasa por sus filtros y envolventes.

1. Con la vista de Synth 1 o Synth 2 en pantalla, **pulsa su botón otra vez**: se abre la vista de la fuente.
2. Elige con los pads 25-29:

| Pad | Fuente |
|---|---|
| 25 | Ruido (lo normal) |
| 26 | Entrada 1 |
| 27 | Entrada 2 |
| 28 | Entrada 1 con la fase invertida |
| 29 | Entrada 2 con la fase invertida |
| 30 | Step-drummer (sección 2) |

3. Cualquier botón cierra la vista.

- El parche debe tener **nivel de ruido** (CC 56) para que la fuente se oiga.
- Si en Setup el retorno de reverb / delay va a la tira 3 / 4, esa es la señal que recibe el sinte al elegir la entrada correspondiente.
- La fuente se guarda con el proyecto.

---

## 8. Setup y MIDI

| Dónde | Función |
|---|---|
| Setup, pad 16 | Canal 16 (el de proyecto y FX): activar / desactivar recepción y envío |
| Setup, pad 22 | El **retorno de reverb** pasa por la tira 3 del mixer (nivel, pan, mute y sidechain actúan sobre él) |
| Setup, pad 23 | El **retorno de delay** pasa por la tira 4 |
| Setup, canales | MIDI 1 / MIDI 2 pueden usar un canal que ya tenga otra pista |

- **Loopback interno:** si una pista MIDI comparte canal con un sinte o con los drums, lo que envía (notas y CC) les llega por dentro, sin cable MIDI OUT → IN.
- Todos los CC / NRPN nuevos respetan los filtros **CC Tx** y **CC Rx** de Setup.

---

## 9. Tablas MIDI

Un NRPN son tres mensajes: CC 99 (MSB), CC 98 (LSB), CC 6 (valor de 7 bits). Los valores bipolares van con +64 (64 = centro).

### 9.1 Motor de las pistas MIDI — canal de la pista

| Valor | Mensaje | | Valor | Mensaje |
|---|---|---|---|---|
| Filtro | CC 74 | | TUNE | CC 26 |
| Resonancia | CC 71 | | FINE | CC 27 |
| Env → filtro | CC 79 | | WAVE | CC 20 |
| Ataque | CC 73 | | SHAPE | CC 21 |
| Decay | CC 75 | | TUNE 2 | CC 37 |
| Sustain | CC 70 | | FINE 2 | CC 39 |
| Release | CC 72 | | WAVE 2 | CC 30 |
| Cantidad de efecto | CC 91 | | SHAPE 2 | CC 31 |
| Gain | CC 59 | | MIX | CC 52 |
| Velocidad del LFO | NRPN 0:76 | | RING | CC 54 |

El resto, como NRPN con **MSB 4** y este LSB:

| LSB | Valor | | LSB | Valor |
|---|---|---|---|---|
| 4 | LFO → filtro | | 22 | Env → tono |
| 12 | LFO → nivel | | 23 | Env → forma |
| 13 | Tipo de efecto | | 24 | LFO → forma |
| 15 | Env → nivel | | 25 | Env → morph |
| 16 | Tipo de filtro | | 26 | LFO → morph |
| 21 | LFO → tono | | 32 | BITSYNC |
| | | | 33 | FM |

Los estados de los pads (27, 28, 29, 30, 31) no tienen MIDI.

### 9.2 Drums — canal de drums
**NRPN MSB 5 / 6 / 7 / 8 = Drum 1 / 2 / 3 / 4**

| LSB | Parámetro | Valor |
|---|---|---|
| 1 | Envolvente de tono, cantidad | 0-127, 64 = centro |
| 2 | Ring mod, frecuencia | 0-127 |
| 3 | LFO, cantidad | 0-127, 64 = centro |
| 4 | LFO, velocidad | 0-127, 64 = centro |
| 5 | Envolvente → corte | 0-127, 64 = centro |
| 6 | Resonancia | 0-127 |
| 7 | Forma de la envolvente | 0-127, 64 = centro |
| 8 | Ring mod, cantidad | 0-127 |
| 9 | Modo de filtro | 0-4 |
| 10 | Punto de inicio | 0-15 |
| 11 | Bitcrush | 0-15 |
| 12 | Tipo de distorsión | 0-3 |

### 9.3 Master FX — canal 16
**NRPN MSB 9**, LSB = 4 × conjunto + knob (K1-K4 = 0-3), valor 0-127.

| Efecto | LSB |
|---|---|
| Gater | 0-3 |
| Auto-Filter (los dos pads) | 4-7 |
| Digitise | 8-11 |
| Phaser | 12-15 |
| Vinyl | 16-19 |

---

## 10. Qué se guarda y dónde

| Qué | Dónde | Notas |
|---|---|---|
| Motor de cada pista MIDI (pad 27, incluido VA-drum), pad 31, los valores de las páginas 1 y 2 | Ajustes del aparato (global) | Sobrevive al apagado; no va con el proyecto |
| Step-drummer activado y su destino (MIDI), macro elegido (sintes), página de knobs | Ajustes del aparato | La vista arranca siempre cerrada |
| Las notas y la fila de pitch del step-drummer | El patrón, en el proyecto | Guarda el proyecto |
| Plantillas de CC editadas | Como las plantillas de stock | Al guardar en el editor |
| Knobs nuevos de drums, huecos de Master FX, fuente de los sintes | El proyecto | Guarda el proyecto. **Hasta SC29 el guardado no los escribía** (arreglado en SC30). Desde SC30 los huecos no cambian al cargar otra sesión: vienen del proyecto solo al encender |
| Parámetros de los efectos de Master FX (K1-K4) | RAM | Se mantienen entre sesiones; vuelven a sus valores iniciales al apagar |
| **OSC 2 (TUNE 2, FINE 2, WAVE 2, SHAPE 2), MIX, BITSYNC, FM, RING, pads 28 y 29** | **No se guardan** | Vuelven al valor neutro al apagar |
| Efectos fijados de Master FX, song pointer | No se guardan | Empiezan apagados |

**Al volver a una build anterior a SC29** con una pista en VA-drum, los valores del motor arrancan por defecto: saca las dos pistas de VA-drum antes.

---

## 11. Resumen por vista

**Vista Preset de MIDI 1 / 2**

| Pad | 1-5 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
|---|---|---|---|---|---|---|---|---|
| Función | Página de knobs | Editor de CC | Patch flip / Save | Motor | 1 / 2 osciladores | Orden de la cadena | Step-drummer | Velocity → envolventes |

**Vista de la fuente del sinte** (botón del sinte dos veces): pads 25-29 fuente, pad 30 step-drummer.

**Vista del step-drummer:** pads 1-16 pasos, 17-24 destino / macro, knobs = pares, Octave ▲ pitch, Octave ▼ velocity, 1-16/17-32 la otra mitad.

**Master FX** (Mixer dos veces): pads 1-6 efectos, 7 saltar, 8 apagar todo, 9-24 song pointer, 25-32 fila de actuación y huecos, K1-K4 parámetros.

**Vista FX:** Octave ▲ / ▼ envíos de reverb o de delay, Shift + knob parámetros, Duplicate reset, 1-16/17-32 resonancia master.

**Drums:** knobs según el panel (4.1), Shift + Preset vista cromática, Shift + FX + Octave ▼ sidechain.

**Setup:** pad 16 canal 16, pad 22 reverb → tira 3, pad 23 delay → tira 4.

**En todas partes:** Clear + knob = valor por defecto.
