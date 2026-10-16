# Lista de características — CIRCUIT-HACKS (RC0.9)

Circuit Tracks con el firmware oficial 1.2.1 (build 4486) parcheado. Lo que no aparece aquí funciona como en el aparato original. Cada función en una línea, por temas. **El manual de uso es la [guía por vistas](GUIA.md)** (en color: [guia.html](https://ghillermo.github.io/CIRCUITS-HACKS-RC/guia.html)); los CC / NRPN, en la [referencia MIDI](MIDI.md). Versión ilustrada de esta lista: [https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html). English version: [`docs/MANUAL.en.md`](MANUAL.en.md).

**Convenciones:** pads 1-32 de arriba-izquierda a abajo-derecha (fila 1 = 1-8 … fila 4 = 25-32); knobs K1-K4 arriba, K5-K8 abajo; «Shift + X» = mantener Shift.

## Índice

**A. Accesos directos y usabilidad**

- [A1 Mapa de atajos](#a1-atajos)
- [A2 Master FX en el botón Mixer](#a2-master-fx-acceso)
- [A3 Teclas de la vista FX](#a3-vista-fx)
- [A4 Clear + knob = valor por defecto](#a4-clear-knob)
- [A5 Apagar efectos fijados (pad 8 de Master FX)](#a5-pad8)
- [A6 Vista de la fuente del sinte](#a6-fuente-sinte)
- [A7 Vista cromática y de escala de los drums](#a7-cromatica)
- [A8 Gestión del pack desde el aparato](#a8-pack)
- [A9 Sustituir un drum por la captura](#a9-sustituir)
- [A10 Editor de CC de los macros MIDI](#a10-editor-cc)
- [A11 Mixer: Shift + knob = nivel a 100 / 0](#a11-mixer-shift)
- [A12 Teclado partido Synth 1 + Synth 2](#a12-teclado-partido)
- [A13 Patches de sinte por modo de voz](#a13-colores-patch)
- [A14 Patches del sinte propio (MIDI 1 / 2)](#a14-patches-midi)
- [A15 Guardar el patch del sinte en el pack](#a15-guardar-patch)
- [A16 Destinos de los macro knobs](#a16-destinos-macro)
- [A17 Copiar proyectos a otro hueco o a otro pack](#a17-copiar-proyectos)
- [A18 Patches del sinte propio a otro pack](#a18-patches-entre-packs)

**B. Controles expuestos**

- [B1 Knobs de los drums según el panel](#b1-knobs-drums)
- [B2 Parámetros de reverb y delay](#b2-rev-delay)
- [B3 Sidechain y compresor master con los knobs](#b3-sidechain-comp)
- [B4 Grabar los ruteos internos de MIDI](#b4-grabar-interno)
- [B5 MIDI para todo lo nuevo](#b5-midi-io)
- [B6 Automatización del motor MIDI](#b6-automatizacion)
- [B7 Setup y MIDI del aparato](#b7-setup)
- [B8 Patch flip en MIDI 1 / 2](#b8-patch-flip)

**C. Nuevos modos de control**

- [C1 Motor de las pistas MIDI (pad 27)](#c1-motor-midi)
- [C2 Step-drummer](#c2-step-drummer)
- [C3 Secuenciador de efectos](#c3-fx-seq)
- [C4 Song pointer (Master FX)](#c4-song-pointer)
- [C5 Sample capturado](#c5-sample)
- [C6 Glitch (pad 31) y su asignación](#c6-glitch-pad)
- [C7 Fila inferior asignable (Master FX / FX)](#c7-fila-inferior)
- [C8 Random-mutate por paso](#c8-random-mutate)
- [C9 Frecuencia y dinámicas por paso](#c9-frecuencia-dinamicas)
- [C10 Cadenas de patrones y escenas](#c10-cadenas)
- [C11 Nudge y órdenes de reproducción](#c11-nudge-ordenes)
- [C12 Arpegiador (solo Beta 1.23)](#c12-arpegiador)
- [C13 Rollers de micropasos de los drums (solo Beta 1.23)](#c13-rollers)
- [C14 Escala propia (solo Beta 1.23)](#c14-escala-propia)
- [C15 Master FX en la beta: gesto mecánico, Glitch, Digitise y guardado por sesión](#c15-master-fx-beta)

**D. DSP**

- [D1 Efectos de Master FX](#d1-efectos-grid)
- [D2 VCA-VCF de las pistas MIDI](#d2-vca-vcf)
- [D3 Osciladores y parafonía](#d3-osciladores)
- [D4 Motor VA-drum](#d4-va-drum)
- [D5 Sinte granular](#d5-granular)
- [D6 Motor del Glitch](#d6-glitch-dsp)
- [D7 DSP de los drums](#d7-drums-dsp)
- [D8 Entradas de audio y retornos](#d8-entradas)

**E. Miscelánea**

- [E1 Qué se guarda y dónde](#e1-guardado)
- [E2 El pack de la memoria interna: solo lectura](#e2-pack-interno)
- [E3 Instalar y volver atrás](#e3-instalar)
- [E4 Herramientas de desarrollo y diagnóstico](#e4-herramientas)
- [E5 Tablas MIDI](#e5-tablas-midi)

## A. Accesos directos y usabilidad

<a id="a1-atajos"></a>
### A1. Mapa de atajos
- Todos los atajos del mod en un dibujo del aparato: botones dobles, Shift + botón, Clear + knob y los pads especiales de cada vista.

<a id="a2-master-fx-acceso"></a>
### A2. Master FX en el botón Mixer
- Desde el Mixer, **Mixer otra vez** abre Master FX; cualquier otro botón de vista sale.

<a id="a3-vista-fx"></a>
### A3. Teclas de la vista FX
- **Octave ▲ / ▼** = envíos de delay / reverb; **Shift + knob** = parámetros de reverb y delay.
- **Duplicate** = reset (envíos a 0, filtro master al centro, Master FX apagado); **1-16 / 17-32** = resonancia del filtro master.

<a id="a4-clear-knob"></a>
### A4. Clear + knob = valor por defecto
- Mantén **Clear** y gira un knob a la derecha: vuelve a su valor por defecto. En drums (LED azul), a la izquierda borra la automatización de los knobs de stock (LED rojo), como en el original. También en el motor de las pistas MIDI y en **Master FX**.

<a id="a5-pad8"></a>
### A5. Apagar efectos fijados (pad 8 de Master FX)
- **Pad 8** apaga todo lo fijado con Shift (efectos y song pointer) y hace bypass de los FX; tocar un efecto fijado lo suelta.

<a id="a6-fuente-sinte"></a>
### A6. Vista de la fuente del sinte
- Con Synth 1 / 2 en pantalla, **pulsa su botón otra vez**: pads 25-29 eligen la fuente (ruido, entradas, invertidas), pad 30 = step-drummer.

<a id="a7-cromatica"></a>
### A7. Vista cromática y de escala de los drums
- **Shift + Preset** con un drum: los pads tocan el sample en la escala; K1 = sesgo de tono, Shift + K1 = cents; vista Note: pads 25-28 = drums 4-1.

<a id="a8-pack"></a>
### A8. Gestión del pack desde el aparato
- **Save** también guarda en la tarjeta los samples sustituidos por capturas.
- **Duplicate + pad A + pad B** (Preset de drums) intercambia dos samples; entre packs **copia** samples y patches de sinte; **Clear**, el pack, **Clear** (vista de packs) borra un pack.

<a id="a9-sustituir"></a>
### A9. Sustituir un drum por la captura
- Vista Preset de drums: **Clear + pad dos veces** = ese sample pasa a ser la captura (hasta guardar o recargar).

<a id="a10-editor-cc"></a>
### A10. Editor de CC de los macros MIDI
- Vista Preset de MIDI 1 / 2, **pad 25**: mueve un knob y cambia su CC / NRPN desde el aparato; pad 26 = guardar.

<a id="a11-mixer-shift"></a>
### A11. Mixer: Shift + knob = nivel a 100 / 0
- Vista Mixer: **Shift + girar un knob a la derecha** pone el nivel de esa pista a **100**; **a la izquierda**, a **0**.

<a id="a12-teclado-partido"></a>
### A12. Teclado partido Synth 1 + Synth 2
- **Solo Beta 1.23.** Mantén **Synth 1** y pulsa **Synth 2** (o al revés): las dos filas de arriba tocan Synth 1 y las dos de abajo Synth 2.

<a id="a13-colores-patch"></a>
### A13. Patches de sinte por modo de voz
- **Solo Beta 1.23.** En la vista Preset de Synth 1 / 2 cada patch se ve según su modo de voz: **mono azul oscuro**, **glide lavanda**, **poly como siempre**.

<a id="a14-patches-midi"></a>
### A14. Patches del sinte propio (MIDI 1 / 2)
- **Solo Beta 1.23.** En la vista Preset de MIDI 1 / 2 las filas 2 y 3 son 16 huecos de patch del motor de la pista: tocar = cargar (suena la tónica), **Clear + pad** dos veces = guardar, **Duplicate + A + B** = intercambiar; **Octave ▼ / ▲** = 4 páginas (64 huecos por pack).

<a id="a15-guardar-patch"></a>
### A15. Guardar el patch del sinte en el pack
- **Solo Beta 1.23.** En la vista Preset de Synth 1 / 2: **Clear + pad** pregunta (parpadea en blanco) y **Clear + el mismo pad otra vez** guarda en ese hueco el patch tal como suena.

<a id="a16-destinos-macro"></a>
### A16. Destinos de los macro knobs
- **Solo Beta 1.23.** En la vista de la fuente del sinte (A6) el **pad 32** abre el editor: un knob elige su macro, **Octave ▼ / ▲** pasa de campo y los pads dibujan el número.

<a id="a17-copiar-proyectos"></a>
### A17. Copiar proyectos a otro hueco o a otro pack
- **Solo Beta 1.23.** En la vista Projects: **Duplicate + pad A** elige el proyecto (parpadea en amarillo) y **Duplicate + pad B** lo copia a ese hueco, del mismo pack o de otro.

<a id="a18-patches-entre-packs"></a>
### A18. Patches del sinte propio a otro pack
- **Solo Beta 1.23.** En la vista Preset de MIDI 1 / 2: **Duplicate + hueco A**, carga otro pack y **Duplicate + hueco B** copia el patch (motor, parámetros y nombre).

## B. Controles expuestos

<a id="b1-knobs-drums"></a>
### B1. Knobs de los drums según el panel
- Cada knob hace lo que dice su etiqueta, con una segunda capa en Shift: ring mod, envolventes, filtros (DJ, BP, notch, comb, tilt), LFO, start point, bitcrush y distorsión.

<a id="b2-rev-delay"></a>
### B2. Parámetros de reverb y delay
- Vista FX, **Shift + knob**: reverb (tipo, decay, damping) y delay (time, sync, feedback, width, ratio, slew); se guardan con el proyecto.

<a id="b3-sidechain-comp"></a>
### B3. Sidechain y compresor master con los knobs
- **Solo Beta 1.23.** En la vista Sidechain (**Shift + FX**): **K1-K4** = ataque, hold, decay y profundidad del sidechain de la pista elegida; **K7 / K8** = ataque y release del compresor master.

<a id="b4-grabar-interno"></a>
### B4. Grabar los ruteos internos de MIDI
- **Solo Beta 1.23.** En la vista Setup, **Record** decide si lo que una pista MIDI manda a un sinte interno por el canal compartido se graba también en ese sinte: **amarillo = sí**, apagado = no (por defecto).

<a id="b5-midi-io"></a>
### B5. MIDI para todo lo nuevo
- Los valores nuevos salen y entran por MIDI: CC / NRPN del motor de las pistas MIDI, NRPN de los drums (MSB 5-8) y de Master FX (MSB 9, canal 16).

<a id="b6-automatizacion"></a>
### B6. Automatización del motor MIDI
- Con Record + Play, los 8 valores de la página 4 del motor MIDI se graban en los carriles de macros del patrón.

<a id="b7-setup"></a>
### B7. Setup y MIDI del aparato
- Canal 16 Rx / Tx (pad 16), canales compartidos, **loopback interno** sin cable y **retornos de reverb / delay por las tiras 3 / 4** (pads 22 / 23, en crema / melocotón como la reverb y el delay de la vista FX).
- **Solo Beta 1.23:** MIDI Thru con cuatro modos (Duplicate en Advanced Setup): Thru, Out 2, **Merge** (DIN In + el MIDI del aparato) y **Filter** (DIN In sin los canales en escucha).
- **Solo Beta 1.23:** canales de **Program Change** propios: pad 29 / 30 enseñan y eligen el canal de escucha / salida (16 por defecto); lo recibido se reenvía por el de salida.
- **Solo Beta 1.23:** **metrónomo con cuenta atrás**: Shift + Clear recorre sin metrónomo, metrónomo, solo cuenta atrás y las dos; la cuenta atrás es un compás antes de grabar.

<a id="b8-patch-flip"></a>
### B8. Patch flip en MIDI 1 / 2
- Pad 26 de la vista Preset de MIDI: cada nota se envía como Program Change (excluyente con el motor de la pista).

## C. Nuevos modos de control

<a id="c1-motor-midi"></a>
### C1. Motor de las pistas MIDI (pad 27)
- El pad 27 de la vista Preset de MIDI 1 / 2 elige el motor: apagado → **línea** → **oscilador** → **VA-drum** → **granular** → **secuenciador de efectos**.
- Los pads 1-5 eligen la página de knobs; 28 = dos osciladores, 29 = orden de la cadena, 30 = step-drummer, 31 = velocity (VA-drum). **Solo Beta 1.23:** Clear + un pad de página = los valores de esa página a los iniciales; las filas 2-3 guardan patches (A14).

<a id="c2-step-drummer"></a>
### C2. Step-drummer
- Secuenciación por **pares de pasos** sobre el patrón: pads 1-16 pasos, 17-24 destino / macro, los 8 knobs = los 8 pares (pitch u velocity).
- MIDI: vista Preset, pad 30. Sintes: vista de la fuente, pad 30. Grabando, los pasos tocados se graban en tiempo real.

<a id="c3-fx-seq"></a>
### C3. Secuenciador de efectos
- Estado **azul** del pad 27: el step-drummer de la pista elige, en cada par de pasos, **un hueco de la fila inferior de Master FX** (0 = nada); suena en los pasos con nota.
- El knob avanza despacio (**un hueco cada ~48 pasos de giro**) y se ilumina con el **color del efecto** elegido. **Un hueco sin efecto asignado no hace nada:** asigna antes los efectos a la fila inferior de Master FX (ver «Fila inferior asignable»). **Solo Beta 1.23:** al final del recorrido está el valor **random** (LED blanco): en cada paso con nota suena uno de la lista al azar (los huecos con efecto asignado y el gesto mecánico del pad 31).

<a id="c4-song-pointer"></a>
### C4. Song pointer (Master FX)
- Pads 9-24 = pasos 1-16: un paso mantenido = retrigger; dos pasos = frase momentánea; Shift + dos = frase fijada.
- **Modo frase:** Shift + paso = inicio (fin 16); un toque = el fin; Shift + otro paso = nuevo inicio; Shift + el inicio o el pad 9 blanco = salir.

<a id="c5-sample"></a>
### C5. Sample capturado
- **Pad 32** (rojo) graba la salida; **pad 7** (amarillo) la toca: K1 pitch, K2 modo (one-shot / gate / loop por color), K3 start, K4 end.
- El sample se asigna a la fila inferior (pad 7 + pad de abajo) y puede sustituir a un drum (A9).

<a id="c6-glitch-pad"></a>
### C6. Glitch (pad 31) y su asignación
- **Mantén el pad 31** (Master FX o vista FX): la salida se rompe y se retrasa como una cinta. K1 velocidad, K2 repetición, K3 retraso, K4 caos (mitad de abajo) o sobrecarga (mitad de arriba).
- **Pad 31 mantenido + otro pad de la fila inferior** = ese hueco también es un Glitch, con su copia de K1-K4.

<a id="c7-fila-inferior"></a>
### C7. Fila inferior asignable (Master FX / FX)
- Mantén un efecto de arriba (o el pad 7, o el pad 31) y toca un pad de abajo: ese hueco guarda el efecto con una copia de sus parámetros. Se guarda con el proyecto.

<a id="c8-random-mutate"></a>
### C8. Random-mutate por paso
- **Solo Beta 1.23.** En la vista de probabilidad (**Shift + Pattern Settings**) la fila 4 da a cada paso una probabilidad de que sus notas salten de octava o cambien a otra nota de la escala al sonar.

<a id="c9-frecuencia-dinamicas"></a>
### C9. Frecuencia y dinámicas por paso
- **Solo Beta 1.23.** En la vista de probabilidad de las pistas de notas: **fila 4 = cada cuántas vueltas del patrón suena el paso** (1-8). Con el **pad 25 de Pattern Settings**: fila 3 = **dinámicas** aleatorias (velocity, posición y duración), fila 4 = random-mutate.

<a id="c10-cadenas"></a>
### C10. Cadenas de patrones y escenas
- **Solo Beta 1.23.** Cada patrón puede llevar una regla «suena n veces, luego salta a B; la vez siguiente, a C». **Shift + Octave ▲ / ▼** en la vista Patterns activa / desactiva el **modo cadena** de todo el proyecto; cada escena recuerda el modo con que se guardó.

<a id="c11-nudge-ordenes"></a>
### C11. Nudge y órdenes de reproducción
- **Solo Beta 1.23.** En la vista Pattern Settings: **pad 26 = Nudge** (el patrón rotado para que el primer paso elegido sea el paso 1), **pad 27 = orden fractal**, **pad 28 = orden deconstruido**. En todas las pistas, drums incluidos.

<a id="c12-arpegiador"></a>
### C12. Arpegiador (solo Beta 1.23)
- **Solo Beta 1.23.** En la vista Pattern Settings de una pista de notas: **Shift + pad 25** = arpegiador del patrón encendido / apagado, **Shift + pads 27-32** = su orden (fractal, deconstruido, arriba, abajo, ping-pong, aleatorio), independiente de la dirección del patrón.

<a id="c13-rollers"></a>
### C13. Rollers de micropasos de los drums (solo Beta 1.23)
- **Solo Beta 1.23.** Filas 1-3 de la vista Note de los drums: mantener un roller hace sonar su drum en cada paso en ese micropaso (dos columnas por drum, micropasos 1-3 y 4-6), en directo; con el transporte parado, al tempo del proyecto.

<a id="c14-escala-propia"></a>
### C14. Escala propia (solo Beta 1.23)
- **Solo Beta 1.23.** **Shift + Scales** = editor de una escala propia para las pistas de notas: hasta 7 notas sobre la tónica y un **periodo** cualquiera (hasta 24 semitonos) que es la tónica de la siguiente iteración; cada fila de pads es una iteración (dos con 4 notas o menos). Se guarda con el proyecto.

<a id="c15-master-fx-beta"></a>
### C15. Master FX en la beta: gesto mecánico, Glitch, Digitise y guardado por sesión
- **Solo Beta 1.23.** El pad 6 de Master FX es el **Glitch** y el pad 31 un **gesto mecánico** (parada de cinta, scratch…); Digitise gana **K3 = envío momentáneo al delay** y **K4 = envolvente**; los knobs y los huecos de Master FX **se guardan con cada proyecto**.

## D. DSP

<a id="d1-efectos-grid"></a>
### D1. Efectos de Master FX
- Gater, Auto-Filter LP / HP, Digitise, Phaser y Vinyl sobre la salida master, con 4 parámetros cada uno.

<a id="d2-vca-vcf"></a>
### D2. VCA-VCF de las pistas MIDI
- Filtros DJ / LP / HP 12 y 24 dB / paso banda / notch, efectos (saturación, plegado, wavefold, ring, comb, chorus), VCA con ADSR y LFO.

<a id="d3-osciladores"></a>
### D3. Osciladores y parafonía
- Morph continuo seno → triángulo → sierra → cuadrada, wavefold / pendiente / ancho, segundo oscilador con FM, ring, sync suave y modos bit a bit; dos notas parafónicas.

<a id="d4-va-drum"></a>
### D4. Motor VA-drum
- Oscilador pensado para percusión: VCA de un disparo, envolventes de decay propias para pitch (knob Sustain) y filtro (knob Release), ruido blanco y valores aleatorios en lugar del LFO.

<a id="d5-granular"></a>
### D5. Sinte granular
- Hasta **16 granos por pista** desde cualquier sample del pack o la captura, con interpolación y ventana; en el segundo núcleo del DSP.
- K1 tono, K2 posición, K3 scan / freeze, K4 tamaño, K5 densidad, K6 zona, K7 LFO → posición, K8 envolvente → posición; Shift: fino, dispersiones, reverso, ventana, slicer (o stretch, solo Beta 1.23), LFO → tamaño, fuente.

<a id="d6-glitch-dsp"></a>
### D6. Motor del Glitch
- Una cabeza de cinta sobre un búfer circular estéreo del master (2,7 s) en la memoria externa del DSP: velocidad variable, repeticiones con fundidos, caos.

<a id="d7-drums-dsp"></a>
### D7. DSP de los drums
- Ring mod, envolventes de tono y filtro, LFO, filtros DJ / paso banda / notch / comb / tilt, bitcrush, start point, distorsiones y sidechain entre drums.

<a id="d8-entradas"></a>
### D8. Entradas de audio y retornos
- Entrada de línea (normal o invertida) como fuente de los sintes; retornos de reverb / delay por las tiras 3 / 4 con realimentación.

## E. Miscelánea

<a id="e1-guardado"></a>
### E1. Qué se guarda y dónde
- Proyecto: drums, huecos de Master FX, fuente de los sintes, parámetros de reverb / delay. Aparato: motor de las pistas MIDI. Volátil: OSC 2, efectos fijados.

<a id="e2-pack-interno"></a>
### E2. El pack de la memoria interna: solo lectura
- Nada del mod escribe ni borra en el pack de la memoria interna del Circuit (el primero de la vista de packs). Se puede leer de él y copiar desde él a un pack de la tarjeta, pero no al revés.

<a id="e3-instalar"></a>
### E3. Instalar y volver atrás
- `tools/ct_uploader.html` envía el `.syx` por Web MIDI; solo acepta firmwares verificados. Recuperación: Scales + Preset + Note al encender.

<a id="e4-herramientas"></a>
### E4. Herramientas de desarrollo y diagnóstico
- Builders reproducibles, emuladores ARM / DSP con pruebas por rutas reales, `verify_builds.py`, diagnóstico remoto por USB (`ctremote.py`).

<a id="e5-tablas-midi"></a>
### E5. Tablas MIDI
- Motor MIDI: CC 74/71/79/73/75/70/72/91/59/26/27/20/21/37/39/30/31/52/54 + NRPN 4:x; drums NRPN 5-8:1-12; Master FX NRPN 9:0-19 (canal 16).
