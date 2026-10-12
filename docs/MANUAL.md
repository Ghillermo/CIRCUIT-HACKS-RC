# Manual resumido — CIRCUIT-HACKS (RC0.5)

Circuit Tracks con el firmware oficial 1.2.1 (build 4486) parcheado. Lo que no aparece aquí funciona como en el aparato original. Versión ilustrada en color: [https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html). English version: [`docs/MANUAL.en.md`](MANUAL.en.md).

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

**B. Controles expuestos**

- [B1 Knobs de los drums según el panel](#b1-knobs-drums)
- [B2 Parámetros de reverb y delay](#b2-rev-delay)
- [B3 MIDI para todo lo nuevo](#b3-midi-io)
- [B4 Automatización del motor MIDI](#b4-automatizacion)
- [B5 Setup y MIDI del aparato](#b5-setup)
- [B6 Patch flip en MIDI 1 / 2](#b6-patch-flip)

**C. Nuevos modos de control**

- [C1 Motor de las pistas MIDI (pad 27)](#c1-motor-midi)
- [C2 Step-drummer](#c2-step-drummer)
- [C3 Secuenciador de efectos](#c3-fx-seq)
- [C4 Song pointer (Master FX)](#c4-song-pointer)
- [C5 Sample capturado](#c5-sample)
- [C6 Glitch (pad 31) y su asignación](#c6-glitch-pad)
- [C7 Fila inferior asignable (Master FX / FX)](#c7-fila-inferior)
- [C8 Random-mutate por paso](#c8-random-mutate)

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
- [E2 Instalar y volver atrás](#e2-instalar)
- [E3 Herramientas de desarrollo y diagnóstico](#e3-herramientas)
- [E4 Tablas MIDI](#e4-tablas-midi)

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
- **Solo BETA4.** Mantén **Synth 1** y pulsa **Synth 2** (o al revés): las dos filas de arriba tocan Synth 1 y las dos de abajo Synth 2.

<a id="a13-colores-patch"></a>
### A13. Patches de sinte por modo de voz
- **Solo BETA4.** En la vista Preset de Synth 1 / 2 cada patch se ve según su modo de voz: **mono azul oscuro**, **glide lavanda**, **poly como siempre**.

<a id="a14-patches-midi"></a>
### A14. Patches del sinte propio (MIDI 1 / 2)
- **Solo BETA4.** En la vista Preset de MIDI 1 / 2 las filas 2 y 3 son 16 huecos de patch del motor de la pista: tocar = cargar (suena la tónica), **Clear + pad** dos veces = guardar, **Duplicate + A + B** = intercambiar; **Octave ▼ / ▲** = 4 páginas (64 huecos por pack).

<a id="a15-guardar-patch"></a>
### A15. Guardar el patch del sinte en el pack
- **Solo BETA4.** En la vista Preset de Synth 1 / 2: **Clear + pad** pregunta (parpadea en blanco) y **Clear + el mismo pad otra vez** guarda en ese hueco el patch tal como suena.

<a id="a16-destinos-macro"></a>
### A16. Destinos de los macro knobs
- **Solo BETA4.** En la vista de la fuente del sinte (A6) el **pad 32** abre el editor: un knob elige su macro, **Octave ▼ / ▲** pasa de campo y los pads dibujan el número.

## B. Controles expuestos

<a id="b1-knobs-drums"></a>
### B1. Knobs de los drums según el panel
- Cada knob hace lo que dice su etiqueta, con una segunda capa en Shift: ring mod, envolventes, filtros (DJ, BP, notch, comb, tilt), LFO, start point, bitcrush y distorsión.

<a id="b2-rev-delay"></a>
### B2. Parámetros de reverb y delay
- Vista FX, **Shift + knob**: reverb (tipo, decay, damping) y delay (time, sync, feedback, width, ratio, slew); se guardan con el proyecto.

<a id="b3-midi-io"></a>
### B3. MIDI para todo lo nuevo
- Los valores nuevos salen y entran por MIDI: CC / NRPN del motor de las pistas MIDI, NRPN de los drums (MSB 5-8) y de Master FX (MSB 9, canal 16).

<a id="b4-automatizacion"></a>
### B4. Automatización del motor MIDI
- Con Record + Play, los 8 valores de la página 4 del motor MIDI se graban en los carriles de macros del patrón.

<a id="b5-setup"></a>
### B5. Setup y MIDI del aparato
- Canal 16 Rx / Tx (pad 16), canales compartidos, **loopback interno** sin cable y **retornos de reverb / delay por las tiras 3 / 4** (pads 22 / 23, en crema / melocotón como la reverb y el delay de la vista FX).
- **Solo BETA4:** MIDI Thru con cuatro modos (Duplicate en Advanced Setup): Thru, Out 2, **Merge** (DIN In + el MIDI del aparato) y **Filter** (DIN In sin los canales en escucha).

<a id="b6-patch-flip"></a>
### B6. Patch flip en MIDI 1 / 2
- Pad 26 de la vista Preset de MIDI: cada nota se envía como Program Change (excluyente con el motor de la pista).

## C. Nuevos modos de control

<a id="c1-motor-midi"></a>
### C1. Motor de las pistas MIDI (pad 27)
- El pad 27 de la vista Preset de MIDI 1 / 2 elige el motor: apagado → **línea** → **oscilador** → **VA-drum** → **granular** → **secuenciador de efectos**.
- Los pads 1-5 eligen la página de knobs; 28 = dos osciladores, 29 = orden de la cadena, 30 = step-drummer, 31 = velocity (VA-drum). **Solo BETA4:** Clear + un pad de página = los valores de esa página a los iniciales; las filas 2-3 guardan patches (A14).

<a id="c2-step-drummer"></a>
### C2. Step-drummer
- Secuenciación por **pares de pasos** sobre el patrón: pads 1-16 pasos, 17-24 destino / macro, los 8 knobs = los 8 pares (pitch u velocity).
- MIDI: vista Preset, pad 30. Sintes: vista de la fuente, pad 30. Grabando, los pasos tocados se graban en tiempo real.

<a id="c3-fx-seq"></a>
### C3. Secuenciador de efectos
- Estado **azul** del pad 27: el step-drummer de la pista elige, en cada par de pasos, **un hueco de la fila inferior de Master FX** (0 = nada); suena en los pasos con nota.
- El knob avanza **un hueco cada ~16 pasos** (gíralo despacio) y se ilumina con el **color del efecto** elegido.

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
- **Solo BETA4.** En la vista de probabilidad (**Shift + Pattern Settings**) la fila 4 da a cada paso una probabilidad de que sus notas salten de octava o cambien a otra nota de la escala al sonar.

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
- K1 tono, K2 posición, K3 scan / freeze, K4 tamaño, K5 densidad, K6 zona, K7 LFO → posición, K8 envolvente → posición; Shift: fino, dispersiones, reverso, ventana, slicer (o stretch, solo BETA4), LFO → tamaño, fuente.

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

<a id="e2-instalar"></a>
### E2. Instalar y volver atrás
- `tools/ct_uploader.html` envía el `.syx` por Web MIDI; solo acepta firmwares verificados. Recuperación: Scales + Preset + Note al encender.

<a id="e3-herramientas"></a>
### E3. Herramientas de desarrollo y diagnóstico
- Builders reproducibles, emuladores ARM / DSP con pruebas por rutas reales, `verify_builds.py`, diagnóstico remoto por USB (`ctremote.py`).

<a id="e4-tablas-midi"></a>
### E4. Tablas MIDI
- Motor MIDI: CC 74/71/79/73/75/70/72/91/59/26/27/20/21/37/39/30/31/52/54 + NRPN 4:x; drums NRPN 5-8:1-12; Master FX NRPN 9:0-19 (canal 16).
