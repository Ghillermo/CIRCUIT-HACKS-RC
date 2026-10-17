# Cambios — CIRCUIT-HACKS

*English version below: [Changelog](#changelog).*

Novedades y arreglos de cada versión candidata (RC). Cada RC tiene una **versión más segura** (sufijo **S**) sin las funciones que escriben en la tarjeta SD por su cuenta (gestión del pack, A8). Las referencias (A4, C6…) son las secciones del [manual](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html). El detalle técnico está en [`docs/NOTAS.md`](docs/NOTAS.md).

## RC2 / RC2S — 2026-10-17

**RC2** (marca `RC2`) = **Beta 1.30** (SC44) como segunda versión candidata: RC0.9 + todo lo de las betas 1.0-1.30 (sus entradas, abajo). **RC2S** (marca `RC2S`) = la versión más segura: RC2, pero nada del mod escribe ni borra en la tarjeta o en la memoria interna: esas peticiones se rechazan en cualquier pack (el LED de Save en rojo) y los guardados del original pasan. En RC2S no hacen nada guardar la captura con el proyecto, intercambiar o copiar samples y patches entre packs, los patches del sinte propio, guardar el patch del sinte, copiar proyectos y borrar packs. Lo marcado «solo Beta 1.x» en los manuales anteriores es ahora «desde RC2».

### Cambios
- Modo muestra: las filas 1-2 del selector (los pasos) tienen fondo cian.

## Beta 1.30 — 2026-10-17

**Beta 1.30** (marca `B1.30`; = SC44) = Beta 1.29 + lo siguiente. Las RC siguen en RC0.9 / RC0.9S.

### Novedades (solo Beta 1.30)
- **Modo muestra del sinte propio de MIDI 1 / 2 (C15):** un estado nuevo del pad 27 (cian, entre el granular y el secuenciador de efectos): la pista toca **un sample del pack de un golpe** a la altura de cada nota (**C3 = como se grabó**), por el filtro, el efecto y el LFO del motor; el VCA se queda abierto y el sample suena hasta el final (una voz por pista: cada nota lo vuelve a empezar).
- **Selector de samples en la vista Note ampliada** (Note dos veces, en ese modo): filas 3-4 = 16 samples, **Octave ▼ / ▲** = 4 páginas (los 64 del pack); tocar uno = el sample de la pista (y suena). Filas 1-2 = los pasos: **mantener un paso y tocar un sample** = **sample flip** de ese paso; **Clear + paso** lo quita; **1-16 / 17-32** = la otra mitad. Con **Record + Play**, tocar un sample graba la nota y su flip.

### Cambios (solo Beta 1.30)
- El pad 27 llega al secuenciador de efectos una pulsación más tarde (el modo muestra va antes).
- Los flips van en el carril de la automatización de nivel de la pista MIDI: un flip sustituye el nivel grabado en su paso.

## Beta 1.29 — 2026-10-17

**Beta 1.29** (marca `B1.29`; = SC43.9) = Beta 1.28 + lo siguiente. Las RC siguen en RC0.9 / RC0.9S.

### Novedades (solo Beta 1.29)
- **Formas del LFO del sinte propio de MIDI 1 / 2:** en la página 5 de knobs, **Shift + K8** elige la forma del LFO: diente de sierra inverso (naranja, la de siempre), diente de sierra (magenta), triángulo (verde), cuadrada (roja), seno (cian) y sample & hold (blanco: un valor al azar en cada vuelta). Un paso cada 4 clics, sin dar la vuelta. Con Shift, el LED de K8 enseña la forma en su color. Se guarda con el proyecto y en los patches propios (los guardados antes cargan la de siempre). Con el motor VA-drum el LFO sigue siendo su ruido.

### Interno (solo Beta 1.29)
- **El programa del DSP, más corto:** el código propio del núcleo 0 usa la forma de una palabra de las lecturas y escrituras de memoria con desplazamiento (la que usan las voces del original): 441 palabras menos y el mismo sonido (comprobado en emulación, memoria idéntica bloque a bloque). Deja sitio para lo siguiente: 372 palabras libres tras las formas del LFO (antes 8).

## Beta 1.28 — 2026-10-17

**Beta 1.28** (marca `B1.28`; = SC43.8) = Beta 1.27 + lo siguiente. Las RC siguen en RC0.9 / RC0.9S.

### Novedades (solo Beta 1.28)
- **Sidechain de los drums con Synth 1 / 2 y MIDI 1 / 2:** en las páginas de drums de la vista Sidechain (**Shift + FX**, luego **Octave ▼**), los **pads 1-4 de la fila 1** eligen **Synth 1, Synth 2, MIDI 1 o MIDI 2** como disparo del drum del último preset tocado: cada nota del **patrón** de esa pista abre su envolvente, como un golpe de drum (las notas tocadas en directo no). La elegida se ve en el color del drum; un pad 5-8 vuelve a un drum. Como el resto del sidechain entre drums, no se guarda con el proyecto.

### Arreglos (solo Beta 1.28)
- **El sinte propio de MIDI 1 / 2 al apagar:** los valores de la página OSC 2, los knobs con Shift del granular (Shift + K1-K5 y K7) y del oscilador (Shift + K2 / K3), los pads 28 (dos osciladores) y 29 (orden de la cadena) y la página de knobs volvían a sus valores iniciales en cada encendido. Ahora se guardan en el aparato con el resto del motor. La primera vez que enciendas con Beta 1.28 salen todavía los iniciales: lo guardado antes no los tenía.

## Beta 1.27 — 2026-10-17

**Beta 1.27** (marca `B1.27`; = SC43.7) = Beta 1.26 + lo siguiente. Las RC siguen en RC0.9 / RC0.9S.

### Cambios (solo Beta 1.27)
- **Pitch de los drums:** **K1 vuelve a ser el pitch de stock**, continuo y lineal como en el original (se guarda, se automatiza, sale por CC). Los **pads de la vista cromática transponen encima** en semitonos (los dos se multiplican) y, grabando, cada pad queda en su paso dentro del **mismo carril de pitch** del drum: un paso guarda un movimiento del knob o una nota cromática. Shift + K6 vuelve a ser el de stock.
- **Clear + K1:** a la izquierda (sostenido, como en el original) borra la automatización de pitch, pasos cromáticos incluidos; a la derecha, el pitch al centro. Las dos ponen además el cromático al centro.
- **Clear + el botón de un drum:** borra la automatización de sus knobs en el patrón que suena y pone sus ocho knobs a los valores por defecto.
- **Resolución del arpegiador** (Shift + pads 17-24 de Pattern Settings, en las pistas de notas y en los drums): ahora en el orden de los pads de sync rate de stock, **más lenta a la izquierda y más rápida a la derecha**: pad 17 = 1/4 … pad 21 = 1/16 … pad 24 = 1/32T (antes iba al revés). Lo guardado en los proyectos conserva su resolución.

### Novedades (solo Beta 1.27)
- **Shift + Play = cuantizar** el patrón que suena en la pista elegida (la de la vista en pantalla): las notas y los golpes grabados fuera de la rejilla van al paso más cercano (en los micropasos 1-2, al inicio de su paso; en los 3-5, al inicio del siguiente; los del último paso, al primero). En los drums, un paso con varios golpes (un redoble) se queda como está. Con Shift pulsado el LED de Play se ve amarillo, y verde después de cuantizar. Sustituye al Shift + Play del original (otra forma de arrancar la reproducción).
- **Gate retrigger del sinte propio de MIDI 1 / 2:** en su vista Preset, **Shift + pad 29** lo enciende / apaga (con Shift: verde = encendido, por defecto; amarillo = apagado). Apagado = **legato**: con otras notas pulsadas, una nota nueva cambia la altura sin volver a disparar la envolvente. Se guarda con el proyecto.

### Arreglos (solo Beta 1.27)
- **Arpegiador en MIDI 1 / 2:** al empezar el arpegio de las notas mantenidas, la primera nota no se apagaba: en MIDI 1 / 2 seguía sonando debajo de todo el arpegio (por la salida MIDI y en el sinte propio, cuya puerta no se cerraba); en Synth 1 / 2, hasta que el arpegio volvía a ella. Ahora se apaga al empezar el arpegio.
- **Step-drummer de Synth 1 / 2:** Play y Record ya no sacan de su vista; al volver al sinte (su botón) vuelve a salir el step-drummer si estaba abierto (se cierra con su pad 30).
- **Rollers:** sonando, los rollers de un drum silenciado en el Mixer no sonaban (el original no ejecuta el paso de una pista silenciada); ahora suenan.
- **Panorama de los drums:** en Beta 1.26 los pasos cromáticos iban al carril de automatización de panorama y el original también los aplicaba como panorama. Ahora el carril de panorama vuelve a ser solo del panorama (se graba y se reproduce como en el original). Los pasos cromáticos grabados con Beta 1.26 sonarán como movimientos de panorama: bórralos con Clear + K5 de ese drum en el Mixer (página de panorama, a la izquierda) o vuelve a grabarlos.

## Beta 1.26 — 2026-10-17

**Beta 1.26** (marca `B1.26`; = SC43.6) = Beta 1.25 + lo siguiente. Las RC siguen en RC0.9 / RC0.9S.

### Novedades (solo Beta 1.26)
- **Modo cue en el Mixer:** en la página de panorama (Octave ▼), **Shift + un knob a la derecha** lo enciende y **a la izquierda** lo apaga (Octave ▼ rosa encendido, blanco apagado; se guarda en el aparato). En el modo, la **salida izquierda** lleva la mezcla en mono como siempre y la **derecha** solo las pistas que mandas al cue: cada knob de panorama es el envío de esa pista al cue, desde el centro hacia la derecha (a la izquierda no hace nada; Clear + knob = sin cue). Una pista silenciada también se puede escuchar en el cue: sigue el patrón en el paso en que está y suena solo por la derecha; su pad sigue tenue y los pads de pista (también Shift + pad, al compás siguiente) la sacan o la meten en la mezcla. Los paneos de las pistas no se tocan y vuelven al salir; la reverb, el delay y Master FX son los de la mezcla (el cue los oye).
- **Vista cromática de los drums:** grabando, cada pad vuelve a quedar en su paso (el valor cromático de K1); Clear + K1 a la izquierda borra los pasos cromáticos del patrón que suena.

### Cambios (solo Beta 1.26)
- Los drums ya no graban ni reproducen automatización de **panorama**: ese carril del patrón guarda ahora sus pasos cromáticos (ninguna de las 173 sesiones de la copia lo usaba).
- **Sinte propio de MIDI 1 / 2, página 3 (OSC 2):** sus ocho valores en los ocho knobs, sin Shift, según la serigrafía: K1 Oscillator = TUNE 2, K2 Osc mod = SHAPE 2, K3 Amp envelope = MIX OSC 1 ↔ OSC 2, K4 Filter envelope = FM, K5 Filter frequency = FINE 2, K6 Resonance = BITSYNC, K7 Modulation = WAVE 2, K8 FX = RING.

### Arreglos (solo Beta 1.26)
- **Un oscilador:** con una nota pulsada, otra nota disparaba la puerta pero no cambiaba la altura (iba al segundo oscilador, que no suena). Ahora **la última nota manda**; al soltarla vuelve la anterior, sin volver a disparar.
- **Granular:** el primer grano de cada nota sonaba a la altura de la nota anterior (la nota del segundo oscilador llegaba después del disparo); ahora llega antes y cada nota empieza en su altura.

## Beta 1.25 — 2026-10-17

**Beta 1.25** (marca `B1.25`; = SC43.5) = Beta 1.24 + lo siguiente. Las RC siguen en RC0.9 / RC0.9S.

### Cambios (solo Beta 1.25)
- **Pitch de los drums en dos partes:** **K1 = cromático** (un semitono por paso del knob, propio del mod; se guarda con el proyecto; LED tenue en el centro) y **Shift + K6 = el pitch de stock**, continuo y lineal como en el Circuit original. El pitch guardado en los proyectos, su automatización y su CC son el continuo, así que un proyecto de stock suena igual. Clear + K1 a la derecha = cromático al centro; Clear + K6 a la derecha = también el continuo al centro.
- **Vista cromática de los drums:** los pads fijan el valor cromático (K1); ya no se graba la altura por paso.

### Novedades (solo Beta 1.25)
- **Clear + Synth 1 / 2** (con su vista en pantalla): sus ocho macros vuelven a los valores del patch cargado (leído otra vez del pack).

## Beta 1.24 — 2026-10-16

**Beta 1.24** (marca `B1.24`; = SC43.4) = Beta 1.23 + lo siguiente. Las RC siguen en RC0.9 / RC0.9S.

### Novedades (solo Beta 1.24)
- **Sidechain disparado por patrones de Synth 1 / 2 y MIDI 1 / 2:** en la vista Sidechain (Shift + FX), los pads 1-4 de la fila 1 (antes apagados) eligen Synth 1, Synth 2, MIDI 1 o MIDI 2 como fuente del ducking de la pista elegida, junto a los drums 1-4 (pads 5-8). Cada nota del patrón de esa pista dispara la envolvente, como un golpe de drum. Se guarda con el proyecto.
- **Mixer, Shift + pad de pista (1-8):** silencia / activa esa pista **en el compás siguiente**; el pad parpadea mientras espera; otra vez lo cancela. Parado, al momento.
- **Clear + botón de un drum** (con su vista en pantalla): sus ocho knobs (las dos capas) vuelven a sus valores por defecto.

### Cambios (solo Beta 1.24)
- **Step-drummer de MIDI 1 / 2:** todos los destinos son bipolares: un par vacío está en el centro (64, LED tenue) y el knob suma o resta al valor que tenga el parámetro en la página del motor; el LED se ilumina más cuanto más se aleja, hacia los dos lados (Beta 1.23 dejaba WAVE, FM, MIX, SHAPE y decay en 0).

### Arreglos (solo Beta 1.24)
- **Clear + K8 de drums** ya pone a 0 el bitcrush (la zona a la izquierda del 0), no solo la distorsión.

## Beta 1.23 — 2026-10-16

**Beta 1.23** (marca `B1.23`; = SC43.3) = Beta 1.22 + un cambio en el step-drummer. Las RC siguen en RC0.9 / RC0.9S.

### Cambios (solo Beta 1.23)
- **Step-drummer de MIDI 1 / 2:** el punto sin modulación de cada knob depende de su destino: el centro (64) para los bipolares (tono de los dos osciladores, tono del OSC 2, envolvente → filtro) y 0 para los unipolares (WAVE, FM, MIX, SHAPE, decay, que solo suman). Un par vacío empieza ahí, y el LED del knob enseña la cantidad: tenue = sin modulación, más brillante cuanto más se aleja (hacia arriba o hacia abajo). Antes todos empezaban en 64 y el LED enseñaba el valor (a media luz sin modulación). Lo mismo en la página 2 con destino y en el toggle pitch-vel (la transposición cuenta desde ese punto).

## Beta 1.22 — 2026-10-16

**Beta 1.22** (marca `B1.22`; = SC43.2) = Beta 1.21 + un arreglo. Las RC siguen en RC0.9 / RC0.9S.

### Arreglos (solo Beta 1.22)
- **Grabar con el arpegiador:** la segunda nota de un acorde (y las siguientes) llegaba al grabador pero nunca su note-off, así que el grabador la daba por mantenida y la ignoraba cuando se volvía a tocar, hasta pulsar Record otra vez: en un patrón de 32 pasos los acordes de la segunda página se grababan solo con su primera nota y el arpegiador no los arpegiaba. Ahora al soltar esas notas el grabador también recibe su note-off.

## Beta 1.21 — 2026-10-16

**Beta 1.21** (marca `B1.21`; = SC43.1) = Beta 1.20 + un arreglo. Las RC siguen en RC0.9 / RC0.9S.

### Arreglos (solo Beta 1.21)
- **Rollers y arpegio de drums con el transporte parado:** sus golpes no recibían el note-off, así que los cuadros del drum en la vista Note (pads 27-30 para los drums 1 y 2) se quedaban en blanco y la nota MIDI del drum colgada. Ahora cada golpe se suelta 100 ms después.

## Beta 1.20 — 2026-10-16

**Beta 1.20** (marca `B1.20`; = SC43) = Beta 1.19 + las funciones de Pattern Settings en los drums y tres arreglos de grabación. Las RC siguen en RC0.9 / RC0.9S.

### Novedades (solo Beta 1.20)
- **Frecuencia, dinámicas y random-mutate en los drums**, en su vista de probabilidad (Pattern Settings dos veces = modo 1; pad 25 de su Pattern Settings = modo 2), como en las pistas de notas. El random-mutate cambia el sample del golpe: 25 % de ±1 (el de al lado en su fila), 25 % de ±8 (otra fila), 12 % de cada uno. Las dinámicas solo retrasan el golpe dentro de su paso.

### Arreglos (solo Beta 1.20)
- **Los golpes grabados por los rollers y por el arpegio de los drums ya no se pierden** en la siguiente edición del patrón (el stock volvía a escribir su propia copia de los pasos).
- **El Nudge de los drums** ya no se deshace con la siguiente edición, y mueve también los valores nuevos de cada paso.

## Beta 1.19 — 2026-10-16

**Beta 1.19** (marca `B1.19`; = SC42.9) = Beta 1.18 + la grabación del arpegiador de los drums. Las RC siguen en RC0.9 / RC0.9S.

### Novedades (solo Beta 1.19)
- **El arpegio de los drums se graba con Record** (en marcha, no en la cuenta atrás): cada golpe escribe en el patrón su micropaso, su sample como sample flip del paso (uno por paso: queda el último) y, en un paso vacío, su velocity.

## Beta 1.18 — 2026-10-16

**Beta 1.18** (marca `B1.18`; = SC42.8) = Beta 1.17 + el arpegiador de los drums. Las RC siguen en RC0.9 / RC0.9S.

### Novedades (solo Beta 1.18)
- **Arpegiador de los drums:** en el Pattern Settings de un drum, **Shift + pad 25** lo enciende para el patrón que suena, **Shift + pads 27-32** = orden, **Shift + pads 17-24** = resolución (como en las pistas de notas). En la vista Preset del drum, al mantener varios samples a la vez el drum salta de sample en sample en ese orden (a la rejilla del drum en marcha, al tempo parado); al soltarlos vuelve a su sample elegido. No se graba.

## Beta 1.17 — 2026-10-16

**Beta 1.17** (marca `B1.17`; = SC42.7) = Beta 1.16 + lo pedido tras probarla. Las RC siguen en RC0.9 / RC0.9S.

### Cambios (solo Beta 1.17)
- **Step-drummer:** en Synth 1 / 2 un par vacío empieza en 0 (empezaba en la posición del macro: con el macro arriba, todos los knobs al máximo). La transposición del toggle pitch-vel es de un grado cada 8 pasos del knob (MIDI −8 … +8 desde el centro, sintes 0 … +16) y, con el toggle, los destinos de tono de la página pitch ya no mueven además el sinte propio (la nota salía de la escala).
- **Vista Micro Step, pads 31 / 32:** con los dos apagados, el pad 31 abre el selector y elegir una longitud enciende la longitud fija; el pad 32 enciende el gate por pulsación. Con uno encendido, pulsarlo otra vez lo apaga y pulsar el otro cambia de uno a otro. Ya no hay pulsación larga.
- **Rollers de los drums con el transporte parado:** suenan al tempo del proyecto mientras se mantienen.
- **Pad 29 de MIDI 1 / 2** (orden de la cadena) en el color de la página VCA-VCF.

## Beta 1.16 — 2026-10-16

**Beta 1.16** (marca `B1.16`; = SC42.6) sustituye a Beta 1.3: lleva todo lo nuevo desde entonces (Beta 1.4-1.15 no se publicaron). Las RC siguen en RC0.9 / RC0.9S. En el manual, lo de la beta va marcado **solo Beta 1.16**.

### Novedades (solo Beta 1.16)
- **Arpegiador por patrón** (C, Pattern Settings): **Shift + pad 25** lo enciende, **Shift + pads 27-32** = orden (fractal, deconstruido, arriba, abajo, ping-pong, aleatorio), **Shift + pads 17-24** = su resolución, distinta del tempo de la pista. Arpegia los acordes de la secuencia y las notas mantenidas en vivo.
- **Escala propia** (**Shift + Scales**): hasta 7 notas y un periodo en un piano de dos octavas desde la tónica; se guarda con el proyecto.
- **Metrónomo con cuenta atrás** (**Shift + Clear**): sin metrónomo (rojo), metrónomo (verde), solo cuenta atrás (magenta), las dos (cian); con la cuenta atrás, Record + Play = un compás antes de grabar.
- **Vista Micro Step** (Gate dos veces): **pad 32** = la duración de una nota introducida a mano es lo que se mantiene el pad; **pad 31** = longitud fija con selector.
- **Rollers de micropasos** en las filas 1-3 de la vista Note ampliada de los drums; con Record se graban.
- **Step-drummer:** destino propio de la página velocity (pads 17-24) y **toggle pitch-vel** (pad 32): la página pitch transpone las notas en grados de la escala y la página velocity cambia la velocity, además de sus destinos.
- **K3 de los drums partido:** izquierda = decay de stock, derecha (pasado 127) = ataque; **Shift + K3**: izquierda = inicio del sample, derecha = corte.
- **Sidechain de los drums con los knobs:** en las páginas de drums de la vista Sidechain, K1-K4 = ataque, hold, decay y profundidad del drum del último preset tocado.
- **Canales de Program Change** del proyecto en Setup (pads 29 / 30): escucha y salida, 16 por defecto; lo recibido se reenvía por el de salida.
- **Clear + pad 25** en Pattern Settings borra las dinámicas y el random-mutate del patrón; **Clear + knob** del sinte propio: derecha = valor por defecto (lavanda), izquierda = borrar su automatización (rojo).
- **Preset otra vez** en la vista Preset de un drum = vista cromática encendida / apagada.

### Arreglos (solo Beta 1.16)
- **El stutter del delay** al mover los knobs o cambiar de modo del motor de MIDI 1 / 2: el mod guardaba los ajustes del aparato en la tarjeta en cada cambio y releía la tarjeta cada pocos segundos en las vistas Preset; ahora el guardado espera al transporte parado y la relectura también.
- **Samples de drums como en el Circuit de stock** en proyectos nuevos o sin tocar (el modo de filtro guardado 0 es el EQ de stock).
- **Setup abierto desde la vista de Synth 1 / 2**: ese sinte ya se puede elegir.
- **El patch flip** sale solo por el canal de su pista MIDI.
- **Random-mutate con la escala propia** cuenta los grados desde la tónica.

## RC0.9 / RC0.9S y Beta 1.3 — 2026-10-14

RC0.9 = RC0.8 + una protección. RC0.9S = RC0.8S con el nombre nuevo (no escribe nada por su cuenta: no la necesita). **Beta 1.3** (marca `B1.3`; = SC41.3) = Beta 1.2 + la misma protección.

### Novedades (RC0.9 y Beta 1.3)
- **El pack de la memoria interna es de solo lectura para el mod.** Nada del mod escribe ni borra en él (guardar el sample capturado, copiar o intercambiar samples y patches hacia él, guardar patches del sinte o del sinte propio, copiar proyectos, borrar el pack): se niega y el LED de Save se enciende en rojo un momento. Se puede leer de él y copiar desde él a un pack de la tarjeta. Los guardados del propio aparato no cambian.

## Beta 1.2 — 2026-10-14

**Beta 1.2** (marca `B1.2`; = SC41.2) = Beta 1.1 + un arreglo encontrado al revisar. Las RC siguen en RC0.8 / RC0.8S.

### Arreglos (solo Beta 1.2)
- **Una regla de cadena pedida para una pista o un patrón fuera de rango ya no lee fuera de la memoria.** Con un estado inesperado del secuenciador, las cadenas y los órdenes fractal / deconstruido podían leer una dirección inexistente y bloquear el aparato; ahora ese patrón suena como en el original.

## RC0.8 / RC0.8S y Beta 1.1 — 2026-10-14

RC0.8 = RC0.7 + un arreglo. RC0.8S = RC0.7S + el mismo (**S**). **Beta 1.1** (marca `B1.1` en el aparato; = SC41.1) sustituye a Beta 1.0.

### Arreglos (RC0.8, RC0.8S y Beta 1.1)
- **Los knobs de pitch del step-drummer conservan su valor** (**S**). Desde RC0 cada giro escribía en el par de pasos solo su incremento: el knob no avanzaba, su LED se quedaba casi apagado y el tono saltaba al mínimo.

### Arreglos (solo Beta 1.1)
- **La vista Master FX ya no pisa el estado de otras funciones.** Con la vista en pantalla y muchas cosas sonando, Synth 2 dejaba de sonar, las cadenas de patrones y el orden fractal se reiniciaban y la frecuencia por paso contaba mal.

### Novedades (solo Beta 1.1)
- **Secuenciador de efectos: valor random** (LED blanco, al final del recorrido del knob): en cada paso con nota suena uno de la lista al azar (los huecos con efecto asignado y el gesto mecánico del pad 31).

## RC0.7 / RC0.7S y Beta 1.0 — 2026-10-14

RC0.7 = RC0.6 + dos arreglos. RC0.7S = RC0.6S + los mismos (**S**). **Beta 1.0** (marca `B1.0` en el aparato; = SC40.9) sustituye a BETA5: lleva los arreglos y todo lo nuevo desde entonces. En el manual, lo de la beta va marcado **solo Beta 1.0**.

### Arreglos (RC0.7, RC0.7S y Beta 1.0)
- **El step-drummer, el secuenciador de efectos y el stretch del granular siguen el patrón de su propia pista** (**S**). Leían el patrón, el paso y los ticks de otra pista; no se notaba mientras todas tenían la misma longitud. La captura armada con el transporte en marcha vuelve a esperar al siguiente compás.
- **Knob selector del secuenciador de efectos, tres veces más lento** (**S**): un hueco cada ~48 pasos de giro.
- Manual: el secuenciador de efectos dispara los huecos de la fila inferior de Master FX; **un hueco sin efecto asignado no hace nada**.

### Novedades de la Beta 1.0 (desde BETA5)
- **Cadenas de patrones** con un **modo cadena** de todo el proyecto (Shift + Octave ▲ / ▼ en Patterns) que cada escena recuerda; escenas encadenadas en otro color, pistas que parpadean, **repeticiones de escena** (Shift + pads 9-16 del Mixer).
- **Nudge** y **órdenes de reproducción fractal y deconstruido** (pads 26-28 de Pattern Settings), en todas las pistas.
- **Frecuencia** del paso (cada n vueltas) y **dinámicas** aleatorias (velocity, posición, duración) en la vista de probabilidad.
- **Master FX:** gesto mecánico en el pad 31 y Glitch en el pad 6; Digitise K3 = envío momentáneo al delay, K4 = envolvente; **los 20 knobs, los huecos y el compresor se guardan con cada proyecto**.
- **Knobs en la vista Sidechain:** K1-K4 = ataque, hold, decay y profundidad; K7 / K8 = ataque y release del compresor master.
- **Patches del sinte propio de MIDI 1 / 2 de un pack a otro** (Duplicate + A, otro pack, Duplicate + B).
- **Record en la vista Setup** = grabar también en el sinte lo que le manda una pista MIDI por el canal compartido.
- El LFO del Auto-Filter y del Phaser arranca al activar el efecto (ya en RC0.6).

### Probado en el aparato (2026-10-14)
Frecuencia y dinámicas, cadenas de patrones y escenas, Nudge y órdenes (pistas de notas), gesto mecánico, Glitch en el pad 6, Digitise K3 / K4, knobs de tipo en color, knobs del sidechain, guardar el patch del sinte, patches del sinte propio (también entre packs) y copiar proyectos. Sin probar: lo añadido en la Beta 1.0 sobre eso (modo cadena global, drums, Master FX por sesión, compresor en Sidechain, Record en Setup) y los dos arreglos.

## RC0.6 / RC0.6S — 2026-10-14

RC0.6 = RC0.5 + dos arreglos. RC0.6S = RC0.5S + los mismos (**S**). La beta sigue siendo **BETA5**, que no cambia (lleva el segundo arreglo; el primero, aún no).

### Arreglos
- **El LFO del Auto-Filter y del Phaser arranca al activar el efecto** (C5, **S**). El barrido solo empezaba desde la pulsación cuando el Gater se activaba en el mismo instante; si no, seguía desde un arranque anterior y cada pulsación empezaba en un punto distinto.
- **Blanco tenue fijo en Clear** (**S**). El pad 8 de Master FX sin efectos fijados, y Clear en la vista de packs, usaban un código de color que el aparato hace pulsar.

### Manual
- La tabla de knobs de Master FX corregida según el código: Auto-Filter = velocidad, profundidad, resonancia, frecuencia central; Digitise = muestreo y bits (K3 y K4 no hacen nada); Vinyl = crackle, siseo, tono, desgaste.

## BETA5 — 2026-10-12

Versión beta (= SC39.6): BETA4 + más funciones nuevas aún sin probar en el aparato. Sin versión «S». Acompaña a RC0.5 / RC0.5S, que no cambian. En el manual van marcadas **solo BETA5** (también las de las betas anteriores).

### Novedades
- **Copiar proyectos a otro hueco o a otro pack** (A17). En la vista Projects, Duplicate + pad A elige el proyecto y Duplicate + pad B lo copia; sobre un hueco ocupado pregunta antes.
- **Knobs de tipo en colores.** Con Shift, el modo de filtro de drums (K5), el tipo de distorsión de drums (K8) y el modo de nota del granular (K6) enseñan el tipo elegido como un color, no como un brillo.

### Arreglos
- El blanco tenue del pad 8 de Master FX (sin nada que apagar) y de los huecos sin asignar pulsaba despacio: ahora es fijo.

### Cambios
- La vista de efectos del master se llama **Master FX** en toda la documentación.

## BETA4 — 2026-10-12

Versión beta (= SC39.4): BETA3 + más funciones nuevas aún sin probar en el aparato. Sin versión «S». Acompaña a RC0.5 / RC0.5S, que no cambian. En el manual van marcadas **solo BETA4** (también las de las betas anteriores).

### Novedades
- **Guardar el patch del sinte en el pack** (A15). En la vista Preset de Synth 1 / 2, Clear + pad pregunta (el hueco parpadea en blanco) y Clear + el mismo pad otra vez guarda el patch tal como suena, con sus cambios. El original solo puede con Components.
- **Destinos de los macro knobs** (A16). En la vista de la fuente del sinte el pad 32 abre un editor: un knob elige su macro y Octave ▼ / ▲ recorre ranura, inicio, fin, destino y profundidad; los pads dibujan el número (el destino por su CC / NRPN).
- **`tools/patchtool.py`** (A14): en el PC, los patches del sinte propio de un pack (Components no los conoce): cada patch es un fichero `.ctm`: lista los 64 huecos con su índice, sube y baja patches, los copia entre huecos y packs, lee y edita el motor y los parámetros, crea patches nuevos, los nombra y vacía huecos.
- **Escucha al cargar un patch del sinte propio** (A14): mientras mantienes el pad suena la tónica de la escala.
- **Clear + botón MIDI 1 / 2** (A14): los valores del motor de esa pista a los iniciales.

### Cambios
- **Patches del sinte propio de MIDI 1 / 2** (A14): el guardado pasa a **Clear + pad dos veces** (como el del sinte); **Duplicate + A + B intercambia** dos huecos; los huecos vacíos se ven en violeta. Ya no existen Duplicate + pad = guardar ni Clear + pad = vaciar (BETA2 / BETA3).
- **rc_uploader:** las versiones que escriben en la tarjeta (todas menos las «S») piden marcar una casilla antes de enviar: copia de la microSD hecha y no usar la memoria interna para guardar proyectos.

## RC0.5 / RC0.5S — 2026-10-12

RC0.5 = RC0.4 + un cambio. RC0.5S = RC0.4S + el mismo cambio (**S**). La beta que la acompaña es **BETA3** (= SC39.2: RC0.5 + las funciones de BETA2).

### Cambios
- **El sample capturado pasa por los efectos de Master FX** (C5, **S**). El sample que se dispara con el pad 7 (o desde un hueco de la fila inferior) sonaba sin los efectos de Master FX; ahora pasa por todos. A cambio, la captura (pad 32) graba la salida **sin** los efectos de Master FX (antes los llevaba). El Glitch queda también delante de los otros efectos.

## BETA2 — 2026-10-12

Versión beta (= SC39.1): BETA1 + más funciones nuevas aún sin probar en el aparato. Sin versión «S». En el manual van marcadas **solo BETA2** (también las de las betas anteriores).

### Novedades
- **Patches del sinte propio de MIDI 1 / 2** (A14). En la vista Preset de MIDI 1 / 2 las filas 2 y 3 son 16 huecos de patch del motor de la pista: tocar carga, Duplicate + pad guarda, Clear + pad vacía; Octave ▼ / ▲ cambia entre 4 páginas (64 huecos por pack, compartidos por las dos pistas). Un patch guarda el motor elegido y todos sus valores. Se guardan en la tarjeta, en el espacio libre que hay detrás de los patches de sinte del pack.
- **Selector de fuente del granular** (D5). Shift + K8 de la página granular recorre la captura (rojo) y el sample que tiene en ese momento cada drum (naranja, amarillo, violeta, verde azulado); el elegido queda fijado aunque el drum cambie después.

### Cambios
- **Clear + pad de página** (C1). En la vista Preset de MIDI 1 / 2, Clear + un pad de página (1-5) devuelve a los valores iniciales los knobs de esa página. Clear + pad 27 (BETA0 / BETA1: todo el motor a la vez) ya no reinicia nada.

## BETA1 — 2026-10-12

Versión beta (= SC39): BETA0 + más funciones nuevas aún sin probar en el aparato. Sin versión «S». En el manual van marcadas **solo BETA1** (también las de BETA0).

### Novedades
- **Random-mutate por paso** (C8). En la vista de probabilidad (Shift + Pattern Settings) la fila 4 (pads 25-32, melocotón) da a cada paso una probabilidad de que sus notas salten de octava y / o cambien a otra nota de la escala del proyecto al sonar: apagado, octava 6 %, escala 6 %, las dos 6 %, escala 12 %, octava 12 %, escala 25 %, octava 25 % + escala 50 %. Sin Record la nota cambiada suena esa vez; con Record se escribe en el paso. En Synth 1 / 2 y MIDI 1 / 2. La fila 3 sigue siendo la probabilidad del original.
- **Teclado partido Synth 1 + Synth 2** (A12). Mantén un Synth y pulsa el otro: las dos filas de arriba tocan Synth 1 y las dos de abajo Synth 2, cada uno con su escala, octava y velocity.
- **Patches de sinte por modo de voz** (A13). En la vista Preset de Synth 1 / 2: mono azul oscuro, glide lavanda, poly como siempre.

### Arreglos
- **Advanced Setup:** los pads 22 / 23 ya no se encienden (allí no hacían nada).

## BETA0 — 2026-10-11

Versión beta (= SC38.7): RC0.4 + funciones nuevas aún sin probar en el aparato. Sin versión «S». En el manual van marcadas **solo BETA0**.

### Novedades
- **Stretch del granular** (D5). Shift + K6 tiene un tercer modo de nota, **stretch**: el tramo de K2 al final del sample dura K3 pasos (1 a 64) a cualquier tempo sin cambiar el tono, alineado con el inicio del transporte.
- **MIDI Thru: Merge y Filter** (B5). Duplicate en Advanced Setup pasa por Thru → Out 2 → **Merge** (el DIN In y el MIDI del aparato por el jack Thru, LED amarillo) → **Filter** (el DIN In sin los canales en los que escucha el aparato, LED azul). Se guarda en los ajustes.
- **Clear + pad 27 = el motor de la pista a sus valores iniciales** (C1). En la vista Preset de MIDI 1 / 2, todos los valores de todas las páginas (con y sin Shift) vuelven a los iniciales de una vez; el motor elegido no cambia.

## RC0.4 / RC0.4S — 2026-10-11

RC0.4 = RC0.3 + arreglos (SC38.2-SC38.6, sin sus funciones nuevas). RC0.4S = RC0.3S + los arreglos que no tocan la SD (marcados con **S**).

### Arreglos
- **Captura armada desde parado** (C5, **S**). Shift + pad 32 y Play empezaba a grabar un compás tarde y terminaba al final del segundo; ahora empieza en el primer pulso de Play y graba ese compás.
- **Shift + pad 7 = bucle enganchado** (C5, **S**). Desde SC34.1 el bucle de Shift + 7 sonaba solo mientras se mantenía el pad (como el modo loop); ahora sigue, en cualquier modo, hasta volver a pulsar el 7 (o el pad 8). Igual con Shift + un hueco del sample. El modo loop (K2) sigue sonando solo mientras se mantiene.
- **Duplicate entre packs a un hueco vacío** (A8). Copiar un sample o un patch de sinte a un pad vacío no hacía nada; ahora se copia. Un patch más allá del final de su banco deja vacíos los huecos de en medio, como el guardado del original.
- **Vista de packs:** Clear parpadeaba al abrirla; ahora se ve blanco fijo (A8).

## RC0.3 / RC0.3S — 2026-10-11

RC0.3 = SC38. RC0.3S = RC0.2S + todo lo de esta versión que no toca la SD (marcado con **S**).

### Novedades
- **Mixer: Shift + knob = nivel a 100 / 0** (A11, **S**). En la página de niveles, Shift + girar a la derecha pone la pista a 100 y a la izquierda a 0. Funciona como un giro del knob (sale por MIDI y se graba en la automatización). En el original Shift + knob hacía lo mismo que el knob solo; panorama, Clear + knob y Master FX no cambian.
- **Clear + knob en Master FX** (A4, **S**). Con Clear pulsado, girar a la derecha un knob del efecto elegido lo devuelve a su valor por defecto (efectos 1-6, Glitch y sample); mientras Clear está pulsado, esos knobs se ven azules en su valor por defecto y rojos si no.
- **Copias entre packs en su sitio** (A8). Si el sample copiado cabe en el sitio del sample sustituido, va ahí y no gasta la memoria de importación (≈ 44 s), que además vuelve a empezar cuando ningún sample la usa.

### Cambios
- **Sustituir un drum por la captura = Clear + pad dos veces** (A9, **S**). Antes era Shift + pad, que en el original es la selección silenciosa de un sample: Shift + pad vuelve a hacer eso.

### Arreglos
- **Clear + knob en drums:** el LED a la derecha es el **azul** del original; antes salía un rojo anaranjado tenue (A4, **S**).
- **Borrar un pack:** Clear se queda blanco fijo mientras pregunta (antes parpadeaba) y los packs vuelven a su color al terminar o cancelar (antes podían quedarse apagados hasta salir de la vista) (A8).
- **Memoria de importación:** cuando estaba llena, una copia entre packs podía escribirse encima de un sample que aún sonaba (sonaba mal hasta recargar el pack; los ficheros estaban bien). Ahora no cambia nada si no hay sitio (A8).
- **Patches en la vista de la fuente:** con Duplicate pulsado antes de abrir la vista de la fuente del sinte, sus pads copiaban o intercambiaban patches; ya no (A8).

## RC0.2 / RC0.2S — 2026-10-10

RC0.2 = SC37.5. RC0.2S = RC0.1S + la sobrecarga del Glitch.

### Novedades
- **Sobrecarga en el Glitch** (C6, D6, **S**). K4 en la mitad de arriba imita un DSP sobrecargado: bloques que llegan tarde (chasquidos) y, desde ~3/4, todo más grave y lento. Es una simulación: no carga el DSP de verdad.

### Arreglos
- **Borrar un pack:** el LED de Clear no se encendía en la vista de packs (A8).

## RC0.1 / RC0.1S — 2026-10-10

RC0.1 = SC37.4. RC0.1S = RC0S + lo de esta versión que no toca la SD.

### Novedades
- **Copiar samples y patches de sinte entre packs** (A8): Duplicate + A en un pack, Duplicate + B en otro; el pack de origen no cambia. Dentro del mismo pack, Duplicate + A + B intercambia (también los patches de sinte).

### Cambios
- **Borrar un pack = Clear, el pack, Clear** (A8). En RC0 era Clear mantenido + pack, que no funcionaba en el aparato.

### Arreglos
- **Duplicate en las vistas Preset de drums y de sinte:** no se encendía ni hacía nada en el aparato (A8).
- **Intercambio de samples dentro del pack:** dejaba un clic al final (el fichero se reescribía desde la memoria del DSP); ahora los ficheros se mueven tal cual (A8).
- **Cambio de motor del pad 27 con una nota sostenida:** sin clic (C1, **S**).
- **Pad 28** de MIDI 1 / 2 oculto mientras no hay osciladores (C1, **S**).
- **Dos huecos con Glitch a la vez:** ya no se copian los knobs (C6, **S**).
- **Colores:** Vinyl en melocotón y los retornos de reverb / delay del Setup en sus colores (**S**).

## RC0 / RC0S — 2026-10-09

Primera versión candidata (= SC36.2; RC0S = SC362S, sin escrituras propias en la SD): todo lo descrito en el manual hasta entonces, entre otras cosas el sinte granular, el Glitch, el secuenciador de efectos, Master FX, el motor de las pistas MIDI, el step-drummer, los knobs nuevos de drums y la gestión del pack.

---

<a id="changelog"></a>
# Changelog — CIRCUIT-HACKS

New features and fixes of every release candidate (RC). Every RC has a **safer build** (suffix **S**) without the features that write to the SD card on their own (pack management, A8). The references (A4, C6…) are the sections of the [manual](https://ghillermo.github.io/CIRCUITS-HACKS-RC/en.html). The technical detail is in [`docs/NOTAS.md`](docs/NOTAS.md) (Spanish).

## RC2 / RC2S — 2026-10-17

**RC2** (marker `RC2`) = **Beta 1.30** (SC44) as the second release candidate: RC0.9 + everything of betas 1.0-1.30 (their entries, below). **RC2S** (marker `RC2S`) = the safer build: RC2, but nothing of the mod writes or deletes on the card or in the internal memory: those requests are refused on every pack (the Save LED red) and the original's saves pass. In RC2S saving the capture with the project, exchanging or copying samples and patches between packs, the own-synth patches, saving the synth patch, copying projects and deleting packs do nothing. What the earlier manuals marked «Beta 1.x only» is now «since RC2».

### Changes
- Sample mode: rows 1-2 of the picker (the steps) have a cyan background.

## Beta 1.30 — 2026-10-17

**Beta 1.30** (marker `B1.30`; = SC44) = Beta 1.29 + the following. The RCs stay RC0.9 / RC0.9S.

### New (Beta 1.30 only)
- **Sample mode of the own synth of MIDI 1 / 2 (C15):** a new state of pad 27 (cyan, between the granular and the FX sequencer): the track plays **a pack sample one-shot** at the pitch of each note (**C3 = as recorded**), through the engine's filter, effect and LFO; the VCA stays open and the sample plays to its end (one voice per track: every note restarts it).
- **Sample picker in the expanded Note view** (Note twice, in that mode): rows 3-4 = 16 samples, **Octave ▼ / ▲** = 4 pages (all 64 of the pack); touching one = the track's sample (and it sounds). Rows 1-2 = the steps: **hold a step and touch a sample** = that step's **sample flip**; **Clear + step** removes it; **1-16 / 17-32** = the other half. With **Record + Play**, touching a sample records the note and its flip.

### Changes (Beta 1.30 only)
- Pad 27 reaches the FX sequencer one press later (the sample mode comes first).
- The flips live in the MIDI track's level automation lane: a flip replaces the level recorded on its step.

## Beta 1.29 — 2026-10-17

**Beta 1.29** (marker `B1.29`; = SC43.9) = Beta 1.28 + the following. The RCs stay RC0.9 / RC0.9S.

### New (Beta 1.29 only)
- **LFO shapes of the own synth of MIDI 1 / 2:** on knob page 5, **Shift + K8** picks the LFO's shape: reverse saw (orange, the one it always had), saw (magenta), triangle (green), square (red), sine (cyan) and sample & hold (white: a random value each cycle). One step every 4 clicks, no wrap. With Shift, K8's LED shows the shape in its colour. Saved with the project and in the own-synth patches (patches saved before load the usual one). With the VA-drum engine the LFO stays its noise.

### Internal (Beta 1.29 only)
- **A shorter DSP program:** the mod's code on core 0 uses the one-word form of the memory reads and writes with a displacement (the one the original's voices use): 441 words fewer and the same sound (checked in emulation: the memory identical block by block). It leaves room for what comes next: 372 words free after the LFO shapes (8 before).

## Beta 1.28 — 2026-10-17

**Beta 1.28** (marker `B1.28`; = SC43.8) = Beta 1.27 + the following. The RCs stay RC0.9 / RC0.9S.

### New (Beta 1.28 only)
- **Drum side-chain from Synth 1 / 2 and MIDI 1 / 2:** on the drum pages of the Sidechain view (**Shift + FX**, then **Octave ▼**), **row 1 pads 1-4** pick **Synth 1, Synth 2, MIDI 1 or MIDI 2** as the trigger of the drum whose preset was touched last: every **pattern** note of that track opens its envelope, as a drum hit does (notes played live do not). The chosen one shows in the drum's colour; a pad 5-8 goes back to a drum. Like the rest of the side-chain between drums, it is not saved with the project.

### Fixes (Beta 1.28 only)
- **The own synth of MIDI 1 / 2 over a power cycle:** the OSC 2 page's values, the Shift knobs of the granular (Shift + K1-K5 and K7) and of the oscillator (Shift + K2 / K3), pads 28 (two oscillators) and 29 (chain order) and the knob page went back to their defaults at every power-up. Now they are saved in the unit with the rest of the engine. The first power-up with Beta 1.28 still shows the defaults: what was saved before did not hold them.

## Beta 1.27 — 2026-10-17

**Beta 1.27** (marker `B1.27`; = SC43.7) = Beta 1.26 + the following. The RCs stay RC0.9 / RC0.9S.

### Changes (Beta 1.27 only)
- **Drum pitch:** **K1 is the stock pitch again**, continuous and linear as on the original (saved, automated, sent as CC). The **pads of the chromatic view transpose on top** in semitones (the two multiply) and, while recording, each pad stays on its step inside the drum's **own pitch lane**: a step holds a knob movement or a chromatic note. Shift + K6 is the stock one again.
- **Clear + K1:** to the left (held, as on the original) deletes the pitch automation, chromatic steps included; to the right, the pitch to the centre. Both also put the chromatic value back to the centre.
- **Clear + a drum's button:** deletes the automation of its knobs in the playing pattern and puts its eight knobs back to their defaults.
- **Arpeggiator resolution** (Shift + pads 17-24 of Pattern Settings, on the note tracks and the drums): now in the order of the stock's sync rate pads, **slower to the left and faster to the right**: pad 17 = 1/4 … pad 21 = 1/16 … pad 24 = 1/32T (it was the other way round). What projects hold keeps its resolution.

### New (Beta 1.27 only)
- **Shift + Play = quantize** the pattern the selected track plays (the one whose view is on the screen): notes and hits recorded off the grid go to the nearest step (on micro steps 1-2, to the start of their step; on 3-5, to the start of the next one; the last step's, to the first). On the drums, a step with several hits (a roll) stays as it is. While Shift is held the Play LED is yellow, and green after quantizing. It replaces the original's Shift + Play (another way to start playback).
- **Gate retrigger of the own synth of MIDI 1 / 2:** in its Preset view, **Shift + pad 29** turns it on / off (with Shift: green = on, the default; yellow = off). Off = **legato**: with other notes held, a new note changes the pitch without restarting the envelope. Saved with the project.

### Fixes (Beta 1.27 only)
- **Arpeggiator on MIDI 1 / 2:** when the arpeggio of the held notes started, the first note was not stopped: on MIDI 1 / 2 it kept sounding under the whole arpeggio (on the MIDI out and in the own synth, whose gate never closed); on Synth 1 / 2, until the arpeggio came back to it. Now it stops when the arpeggio starts.
- **Step-drummer of Synth 1 / 2:** Play and Record no longer take you out of its view; going back to the synth (its button) shows the step-drummer again if it was open (pad 30 closes it).
- **Rollers:** while playing, the rollers of a drum muted in the Mixer did not sound (the original firmware skips the step of a muted track); now they do.
- **Drum pan:** in Beta 1.26 the chromatic steps went to the pan automation lane and the original firmware also applied them as the pan. Now the pan lane is the pan's alone again (recorded and played as on the original). Chromatic steps recorded with Beta 1.26 will play as pan moves: delete them with Clear + that drum's knob on the Mixer's pan page (to the left) or record them again.

## Beta 1.26 — 2026-10-17

**Beta 1.26** (marker `B1.26`; = SC43.6) = Beta 1.25 + the following. The RCs stay RC0.9 / RC0.9S.

### New (Beta 1.26 only)
- **Cue mode in the Mixer:** on the pan page (Octave ▼), **Shift + a knob turned right** turns it on and **turned left** turns it off (Octave ▼ pink on, white off; stored in the unit). In the mode the **left output** carries the mix in mono as always and the **right** one only the tracks you send to the cue: each pan knob is that track's cue send, from the centre to the right (to the left it does nothing; Clear + knob = no cue). A muted track can be heard in the cue too: it follows the pattern at the step it is on and plays only on the right; its pad stays dim and the track pads (Shift + pad too, on the next bar) take it out of or into the mix. The tracks' pans are not touched and come back when you leave; reverb, delay and Master FX are the mix's (the cue hears them).
- **The drums' chromatic view:** while recording, each pad is written to its step again (K1's chromatic value); Clear + K1 to the left deletes the chromatic steps of the playing pattern.

### Changes (Beta 1.26 only)
- The drums no longer record or play **pan** automation: that lane of the pattern now holds their chromatic steps (none of the 173 sessions of the card's copy used it).
- **The own synth of MIDI 1 / 2, page 3 (OSC 2):** its eight values on the eight knobs, no Shift, following the printed labels: K1 Oscillator = TUNE 2, K2 Osc mod = SHAPE 2, K3 Amp envelope = MIX OSC 1 ↔ OSC 2, K4 Filter envelope = FM, K5 Filter frequency = FINE 2, K6 Resonance = BITSYNC, K7 Modulation = WAVE 2, K8 FX = RING.

### Fixes (Beta 1.26 only)
- **One oscillator:** with a note held, another note triggered the gate but did not change the pitch (it went to the second oscillator, which is silent). Now **the last note has priority**; releasing it goes back to the previous one, without a new trigger.
- **Granular:** the first grain of every note played at the previous note's pitch (the second oscillator's note arrived after the trigger); now it arrives first and every note starts at its pitch.

## Beta 1.25 — 2026-10-17

**Beta 1.25** (marker `B1.25`; = SC43.5) = Beta 1.24 + the following. The RCs stay RC0.9 / RC0.9S.

### Changes (Beta 1.25 only)
- **Drum pitch in two parts:** **K1 = chromatic** (one semitone per knob step, the mod's own; saved with the project; LED dim at the centre) and **Shift + K6 = the stock pitch**, continuous and linear as on the original Circuit. The pitch saved in projects, its automation and its CC are the continuous one, so a stock project sounds the same. Clear + K1 right = chromatic back to the centre; Clear + K6 right = the continuous one back to the centre too.
- **The drums' chromatic view:** the pads set the chromatic value (K1); the pitch is no longer recorded per step.

### New (Beta 1.25 only)
- **Clear + Synth 1 / 2** (with its view on screen): its eight macros go back to the values of the loaded patch (read again from the pack).

## Beta 1.24 — 2026-10-16

**Beta 1.24** (marker `B1.24`; = SC43.4) = Beta 1.23 + the following. The RCs stay RC0.9 / RC0.9S.

### New (Beta 1.24 only)
- **Sidechain triggered by Synth 1 / 2 and MIDI 1 / 2 patterns:** in the Sidechain view (Shift + FX), row 1 pads 1-4 (dark before) pick Synth 1, Synth 2, MIDI 1 or MIDI 2 as the ducking source of the chosen track, next to drums 1-4 (pads 5-8). Every pattern note of that track fires the envelope, as a drum hit does. Saved with the project.
- **Mixer, Shift + a track pad (1-8):** mutes / unmutes that track **on the next bar**; the pad blinks while it waits; again cancels it. Stopped, at once.
- **Clear + a drum's button** (with its view on screen): its eight knobs (both layers) back to their defaults.

### Changes (Beta 1.24 only)
- **MIDI 1 / 2 step-drummer:** every destination is bipolar: an empty pair sits at the centre (64, LED dim) and the knob adds to or takes from the value the parameter has on the engine's page; the LED gets brighter the further it goes, either way (Beta 1.23 had WAVE, FM, MIX, SHAPE and decay at 0).

### Fixes (Beta 1.24 only)
- **Drums' Clear + K8** now puts the bitcrush (the zone left of 0) back to 0 too, not only the distortion.

## Beta 1.23 — 2026-10-16

**Beta 1.23** (marker `B1.23`; = SC43.3) = Beta 1.22 + a change to the step-drummer. The RCs stay RC0.9 / RC0.9S.

### Changes (Beta 1.23 only)
- **MIDI 1 / 2 step-drummer:** each knob's point of no modulation follows its destination: the centre (64) for the bipolar ones (pitch of both oscillators, OSC 2 pitch, envelope → filter) and 0 for the unipolar ones (WAVE, FM, MIX, SHAPE, decay, which only add). An empty pair starts there, and the knob LED shows the amount: dim = no modulation, brighter the further it goes (up or down). Before, every pair started at 64 and the LED showed the value (half lit with no modulation). The same on page 2 with a destination and for the pitch-vel toggle (the transposition counts from that point).

## Beta 1.22 — 2026-10-16

**Beta 1.22** (marker `B1.22`; = SC43.2) = Beta 1.21 + one fix. The RCs stay RC0.9 / RC0.9S.

### Fixes (Beta 1.22 only)
- **Recording with the arpeggiator:** a chord's second note (and the later ones) reached the recorder but its note-off never did, so the recorder took it as still held and ignored it when it was played again, until Record was pressed again: in a 32-step pattern the chords of the second page were recorded with their first note only, and the arpeggiator did not arpeggiate them. Now letting go of those notes also gives the recorder their note-off.

## Beta 1.21 — 2026-10-16

**Beta 1.21** (marker `B1.21`; = SC43.1) = Beta 1.20 + one fix. The RCs stay RC0.9 / RC0.9S.

### Fixes (Beta 1.21 only)
- **Drum rollers and drum arpeggio with the transport stopped:** their hits never got a note-off, so the drum's boxes in the Note view (pads 27-30 for drums 1 and 2) stayed white and the drum's MIDI note hung. Now each hit is released 100 ms later.

## Beta 1.20 — 2026-10-16

**Beta 1.20** (marker `B1.20`; = SC43) = Beta 1.19 + the Pattern Settings features on the drums and three recording fixes. The RCs stay RC0.9 / RC0.9S.

### New (Beta 1.20 only)
- **Frequency, dynamics and random-mutate on the drums**, in their probability view (Pattern Settings twice = mode 1; pad 25 of their Pattern Settings = mode 2), as on the note tracks. The random-mutate changes the hit's sample: 25 % of ±1 (the next one in its row), 25 % of ±8 (another row), 12 % of each. The dynamics only delay the hit inside its step.

### Fixes (Beta 1.20 only)
- **Hits recorded by the rollers and by the drums' arpeggio are no longer lost** at the next edit of the pattern (the stock wrote its own copy of the steps back).
- **Drum Nudge** is no longer undone by the next edit, and it moves the new per-step values too.

## Beta 1.19 — 2026-10-16

**Beta 1.19** (marker `B1.19`; = SC42.9) = Beta 1.18 + recording the drums' arpeggiator. The RCs stay RC0.9 / RC0.9S.

### New (Beta 1.19 only)
- **The drums' arpeggio is recorded with Record** (playing, not in the count-in): every hit writes its micro step into the pattern, its sample as the step's sample flip (one a step: the last one stays) and, on an empty step, its velocity.

## Beta 1.18 — 2026-10-16

**Beta 1.18** (marker `B1.18`; = SC42.8) = Beta 1.17 + the drums' arpeggiator. The RCs stay RC0.9 / RC0.9S.

### New (Beta 1.18 only)
- **The drums' arpeggiator:** in a drum's Pattern Settings, **Shift + pad 25** turns it on for the pattern it plays, **Shift + pads 27-32** = order, **Shift + pads 17-24** = resolution (as on the note tracks). In the drum's Preset view, holding several samples at once makes the drum jump from sample to sample in that order (on the drum's grid while playing, at the tempo when stopped); when they are let go it goes back to its chosen sample. Not recorded.

## Beta 1.17 — 2026-10-16

**Beta 1.17** (marker `B1.17`; = SC42.7) = Beta 1.16 + what was asked after testing it. The RCs stay RC0.9 / RC0.9S.

### Changed (Beta 1.17 only)
- **Step-drummer:** on Synth 1 / 2 an empty pair starts at 0 (it started at the macro's position: with the macro at the top, every knob at maximum). The pitch-vel toggle's transposition is one degree every 8 knob steps (MIDI −8 … +8 from the centre, synths 0 … +16) and, with the toggle, the pitch page's pitch destinations no longer move the own synth too (the note left the scale).
- **Micro Step view, pads 31 / 32:** with both off, pad 31 opens the selector and picking a length turns the fixed length on; pad 32 turns the gate by holding on. With one on, pressing it again turns it off and pressing the other one switches. No long press any more.
- **Drum rollers with the transport stopped:** they play at the project's tempo while held.
- **Pad 29 of MIDI 1 / 2** (the chain order) in the VCA-VCF page's colour.

## Beta 1.16 — 2026-10-16

**Beta 1.16** (marker `B1.16`; = SC42.6) replaces Beta 1.3: it carries everything new since then (Beta 1.4-1.15 were not published). The RCs stay RC0.9 / RC0.9S. In the manual, the beta's features are marked **Beta 1.16 only**.

### New (Beta 1.16 only)
- **Per-pattern arpeggiator** (C, Pattern Settings): **Shift + pad 25** turns it on, **Shift + pads 27-32** = order (fractal, deconstructed, up, down, ping-pong, random), **Shift + pads 17-24** = its own resolution, independent of the track's tempo. It arpeggiates the sequence's chords and notes held live.
- **Custom scale** (**Shift + Scales**): up to 7 notes and a period on a two-octave piano from the root; saved with the project.
- **Metronome with count-in** (**Shift + Clear**): no metronome (red), metronome (green), count-in only (magenta), both (cyan); with the count-in, Record + Play = one bar before recording.
- **Micro Step view** (Gate twice): **pad 32** = a note entered by hand lasts as long as its pad is held; **pad 31** = fixed length with a selector.
- **Micro-step rollers** on rows 1-3 of the drums' expanded Note view; recorded with Record.
- **Step-drummer:** the velocity page gets its own destination (pads 17-24) and a **pitch-vel toggle** (pad 32): the pitch page transposes the notes in degrees of the scale and the velocity page sets the velocity, on top of their destinations.
- **Split drum K3:** left = stock decay, right (past 127) = attack; **Shift + K3**: left = sample start, right = cut.
- **Drum sidechain on the knobs:** on the Sidechain view's drum pages, K1-K4 = attack, hold, decay and depth of the drum whose preset was touched last.
- **Program Change channels** of the project in Setup (pads 29 / 30): listen and send, 16 by default; what comes in is forwarded on the send channel.
- **Clear + pad 25** in Pattern Settings clears the pattern's dynamics and random-mutate; **Clear + knob** of the own synth: right = default value (lavender), left = clear its automation (red).
- **Preset again** in a drum's Preset view = chromatic view on / off.

### Fixes (Beta 1.16 only)
- **The delay stutter** when moving the MIDI 1 / 2 engine's knobs or modes: the mod saved the device settings to the card on every change and re-read the card every few seconds in the Preset views; now the save waits for the transport to stop, and so does the re-read.
- **Drum samples sound like a stock Circuit** in new or untouched projects (the saved filter mode 0 is the stock EQ).
- **Setup opened from the Synth 1 / 2 view**: that synth can be selected again.
- **The patch flip** goes out only on its MIDI track's channel.
- **Random-mutate with the custom scale** counts the degrees from the root.

## RC0.9 / RC0.9S and Beta 1.3 — 2026-10-14

RC0.9 = RC0.8 + one safeguard. RC0.9S = RC0.8S under the new name (it writes nothing of its own: it does not need it). **Beta 1.3** (marker `B1.3`; = SC41.3) = Beta 1.2 + the same safeguard.

### New (RC0.9 and Beta 1.3)
- **The internal memory pack is read only for the mod.** Nothing of the mod writes or deletes in it (saving the captured sample, copying or exchanging samples and patches into it, saving synth or own-synth patches, copying projects, deleting the pack): it is refused and the Save LED lights red for a moment. You can read it and copy from it to a pack of the card. The device’s own saves are unchanged.

## Beta 1.2 — 2026-10-14

**Beta 1.2** (marker `B1.2`; = SC41.2) = Beta 1.1 + one fix found in a review. The RCs stay RC0.8 / RC0.8S.

### Fixes (Beta 1.2 only)
- **A chain rule asked for a track or a pattern out of range no longer reads outside the memory.** With an unexpected sequencer state, the chains and the fractal / deconstructed orders could read an address that does not exist and freeze the device; now that pattern plays as on the original.

## RC0.8 / RC0.8S and Beta 1.1 — 2026-10-14

RC0.8 = RC0.7 + one fix. RC0.8S = RC0.7S + the same one (**S**). **Beta 1.1** (marker `B1.1` on the device; = SC41.1) replaces Beta 1.0.

### Fixes (RC0.8, RC0.8S and Beta 1.1)
- **The pitch knobs of the step-drummer keep their value** (**S**). Since RC0 every turn wrote only its own delta into the pair of steps: the knob did not move, its LED stayed almost dark and the pitch jumped to the bottom.

### Fixes (Beta 1.1 only)
- **The Master FX view no longer overwrites the state of other features.** With the view on the screen and much playing, Synth 2 went silent, the pattern chains and the fractal order restarted and the step frequency miscounted.

### New (Beta 1.1 only)
- **FX sequencer: random value** (white LED, at the end of the knob’s travel): on every step with a note one of the list plays at random (the slots with an effect assigned and the mechanical gesture of pad 31).

## RC0.7 / RC0.7S and Beta 1.0 — 2026-10-14

RC0.7 = RC0.6 + two fixes. RC0.7S = RC0.6S + the same ones (**S**). **Beta 1.0** (marker `B1.0` on the device; = SC40.9) replaces BETA5: it carries the fixes and everything new since then. In the manual, what only the beta has is marked **Beta 1.0 only**.

### Fixes (RC0.7, RC0.7S and Beta 1.0)
- **The step-drummer, the FX sequencer and the granular stretch follow the pattern of their own track** (**S**). They read the pattern, the step and the ticks of another track; it went unnoticed while every track had the same length. The armed capture with the transport running waits for the next bar again.
- **Selector knob of the FX sequencer three times slower** (**S**): one slot every ~48 steps of the turn.
- Manual: the FX sequencer fires the slots of the Master FX bottom row; **a slot with no effect assigned does nothing**.

### New in Beta 1.0 (since BETA5)
- **Pattern chains** with a project-wide **chain mode** (Shift + Octave ▲ / ▼ in Patterns) that every scene remembers; chained scenes in another colour, blinking tracks, **scene repeats** (Shift + pads 9-16 of the Mixer).
- **Nudge** and the **fractal and deconstructed play orders** (pads 26-28 of Pattern Settings), on every track.
- Step **frequency** (every n plays) and random **dynamics** (velocity, position, length) in the probability view.
- **Master FX:** mechanical gesture on pad 31 and Glitch on pad 6; Digitise K3 = momentary send to the delay, K4 = envelope; **the 20 knobs, the slots and the compressor are saved with every project**.
- **Knobs in the Sidechain view:** K1-K4 = attack, hold, decay and depth; K7 / K8 = attack and release of the master compressor.
- **Own-synth patches of MIDI 1 / 2 from one pack to another** (Duplicate + A, another pack, Duplicate + B).
- **Record in the Setup view** = also record into the synth what a MIDI track sends it over the shared channel.
- The LFO of the Auto-Filter and of the Phaser starts when the effect comes on (already in RC0.6).

### Tested on the device (2026-10-14)
Frequency and dynamics, pattern chains and scenes, Nudge and the orders (note tracks), mechanical gesture, Glitch on pad 6, Digitise K3 / K4, type knobs as colours, side-chain knobs, saving the synth patch, own-synth patches (between packs too) and copying projects. Untested: what Beta 1.0 adds on top (project-wide chain mode, drums, Master FX per session, compressor in the Sidechain view, Record in Setup) and the two fixes.

## RC0.6 / RC0.6S — 2026-10-14

RC0.6 = RC0.5 + two fixes. RC0.6S = RC0.5S + the same (**S**). The beta is still **BETA5**, unchanged (it has the second fix; the first one, not yet).

### Fixed
- **The LFO of the Auto-Filter and of the Phaser starts when the effect comes on** (C5, **S**). The sweep only started from the press when the Gater came on at the same instant; otherwise it went on from an older start and every press began at a different point.
- **A steady dim white on Clear** (**S**). Pad 8 of Master FX with no effect latched, and Clear in the packs view, used a colour code that the device pulses.

### Manual
- The Master FX knob table corrected from the code: Auto-Filter = rate, depth, resonance, centre frequency; Digitise = sample rate and bits (K3 and K4 do nothing); Vinyl = crackle, hiss, tone, wear.

## BETA5 — 2026-10-12

Beta (= SC39.6): BETA4 + more new features not yet tested on the device. No “S” build. It goes with RC0.5 / RC0.5S, which do not change. The manual marks them **BETA5 only** (the earlier betas’ too).

### New
- **Copying projects to another slot or another pack** (A17). In the Projects view, Duplicate + pad A picks the project and Duplicate + pad B copies it; onto a slot in use it asks first.
- **Type knobs as colours.** With Shift, the drums’ filter mode (K5), the drums’ distortion type (K8) and the granular note mode (K6) show the chosen type as a colour, not as a brightness.

### Fixed
- The dim white of pad 8 of Master FX (nothing to switch off) and of the unassigned slots pulsed slowly: it is steady now.

### Changed
- The master effects view is called **Master FX** throughout the documentation.

## BETA4 — 2026-10-12

Beta (= SC39.4): BETA3 + more new features not yet tested on the device. No “S” build. It goes with RC0.5 / RC0.5S, which do not change. The manual marks them **BETA4 only** (the earlier betas’ too).

### New
- **Saving the synth’s patch into the pack** (A15). In the Preset view of Synth 1 / 2, Clear + pad asks (the slot blinks white) and Clear + the same pad again saves the patch as it sounds, with its changes. The original can only do it with Components.
- **Macro knob destinations** (A16). In the synth source view, pad 32 opens an editor: a knob picks its macro and Octave ▼ / ▲ steps slot, start, end, destination and depth; the pads draw the number (the destination by its CC / NRPN).
- **`tools/patchtool.py`** (A14): on the PC, the own-synth patches of a pack (Components does not know them): each patch is a `.ctm` file: lists the 64 slots with their index, uploads and downloads patches, copies them between slots and packs, reads and edits the engine and the parameters, makes new patches, names them and empties slots.
- **Audition when loading an own-synth patch** (A14): while you hold the pad, the root of the scale sounds.
- **Clear + the MIDI 1 / 2 button** (A14): the values of that track’s engine back to the initial ones.

### Changed
- **Patches of the MIDI 1 / 2 own synth** (A14): saving is now **Clear + pad twice** (like the synth’s); **Duplicate + A + B exchanges** two slots; empty slots are violet. Duplicate + pad = save and Clear + pad = empty (BETA2 / BETA3) are gone.
- **rc_uploader:** the versions that write to the card (all but the “S” ones) ask for a tick box before sending: the microSD backed up, and the internal memory not used to save projects.

## RC0.5 / RC0.5S — 2026-10-12

RC0.5 = RC0.4 + one change. RC0.5S = RC0.4S + the same change (**S**). The beta that goes with it is **BETA3** (= SC39.2: RC0.5 + BETA2’s features).

### Changed
- **The captured sample goes through the Master FX effects** (C5, **S**). The sample triggered with pad 7 (or from a slot of the bottom row) played without the Master FX effects; now it goes through all of them. In exchange, the capture (pad 32) records the output **without** the Master FX effects (it used to hold them). The Glitch also sits in front of the other effects now.

## BETA2 — 2026-10-12

Beta (= SC39.1): BETA1 + more new features not yet tested on the device. No “S” build. The manual marks them **BETA2 only** (the earlier betas’ too).

### New
- **Patches of the MIDI 1 / 2 own synth** (A14). In the Preset view of MIDI 1 / 2, rows 2 and 3 are 16 patch slots of the track engine: touch loads, Duplicate + pad saves, Clear + pad empties; Octave ▼ / ▲ steps through 4 pages (64 slots per pack, shared by both tracks). A patch holds the chosen engine and all its values. They are kept on the card, in the free space behind the pack’s synth patches.
- **Granular source selector** (D5). Shift + K8 of the granular page travels over the capture (red) and the sample each drum has at that moment (orange, yellow, violet, teal); the chosen one stays fixed even if the drum changes later.

### Changed
- **Clear + page pad** (C1). In the Preset view of MIDI 1 / 2, Clear + a page pad (1-5) puts the knobs of that page back to their initial values. Clear + pad 27 (BETA0 / BETA1: the whole engine at once) no longer resets anything.

## BETA1 — 2026-10-12

Beta (= SC39): BETA0 + more new features not yet tested on the device. No “S” build. The manual marks them **BETA1 only** (BETA0’s too).

### New
- **Random-mutate per step** (C8). In the probability view (Shift + Pattern Settings) row 4 (pads 25-32, peach) gives each step a chance of its notes jumping an octave and / or moving to another note of the project’s scale when they play: off, octave 6 %, scale 6 %, both 6 %, scale 12 %, octave 12 %, scale 25 %, octave 25 % + scale 50 %. Without Record the changed note plays that once; with Record it is written into the step. On Synth 1 / 2 and MIDI 1 / 2. Row 3 is still the original’s probability.
- **Split keyboard Synth 1 + Synth 2** (A12). Hold one Synth and press the other: the two top rows play Synth 1 and the two bottom rows Synth 2, each with its scale, octave and velocity.
- **Synth patches by voice mode** (A13). In the Preset view of Synth 1 / 2: mono dark blue, glide lavender, poly as always.

### Fixed
- **Advanced Setup:** pads 22 / 23 no longer light up (they did nothing there).

## BETA0 — 2026-10-11

Beta (= SC38.7): RC0.4 + new features not yet tested on the device. No “S” build. The manual marks them **BETA0 only**.

### New
- **Granular stretch** (D5). Shift + K6 gets a third note mode, **stretch**: the stretch from K2 to the end of the sample lasts K3 steps (1 to 64) at any tempo without changing the pitch, in step with the start of the transport.
- **MIDI Thru: Merge and Filter** (B5). Duplicate in Advanced Setup steps Thru → Out 2 → **Merge** (DIN In and the device’s MIDI out of the Thru jack, yellow LED) → **Filter** (DIN In without the channels the device listens to, blue LED). Saved in the settings.
- **Clear + pad 27 = the track engine back to its initial values** (C1). In the MIDI 1 / 2 Preset view, every value of every page (with and without Shift) goes back to its initial value at once; the selected engine stays.

## RC0.4 / RC0.4S — 2026-10-11

RC0.4 = RC0.3 + fixes (SC38.2-SC38.6, without their new features). RC0.4S = RC0.3S + the fixes that do not touch the SD card (marked **S**).

### Fixed
- **Armed capture from stop** (C5, **S**). Shift + pad 32 then Play started recording a bar late and stopped at the end of the second bar; now it starts on Play’s first beat and records that bar.
- **Shift + pad 7 = latched loop** (C5, **S**). Since SC34.1 the Shift + 7 loop only played while the pad was held (like the loop mode); now it goes on, in any mode, until pad 7 (or pad 8) is pressed again. The same with Shift + a slot of the sample. The loop mode (K2) still only plays while held.
- **Duplicate between packs to an empty slot** (A8). Copying a sample or a synth patch to an empty pad did nothing; now it copies. A patch past the end of its bank leaves the slots in between empty, as the original’s save does.
- **Packs view:** Clear blinked when it opened; now it shows steady white (A8).

## RC0.3 / RC0.3S — 2026-10-11

RC0.3 = SC38. RC0.3S = RC0.2S + everything of this version that does not touch the SD card (marked **S**).

### New
- **Mixer: Shift + knob = level to 100 / 0** (A11, **S**). On the levels page, Shift + turning right sets the track to 100 and turning left to 0. It works like a turn of the knob (it goes out over MIDI and is recorded into the automation). On the original Shift + knob did the same as the plain knob; pan, Clear + knob and Master FX do not change.
- **Clear + knob in Master FX** (A4, **S**). With Clear held, turning a knob of the selected effect right takes it back to its default (effects 1-6, Glitch and sample); while Clear is held those knobs show blue at their default and red elsewhere.
- **Copies between packs in place** (A8). If the copied sample fits in the place of the replaced sample, it goes there and uses none of the import memory (≈ 44 s), which also starts again once no sample uses it.

### Changed
- **Replace a drum with the capture = Clear + pad twice** (A9, **S**). It was Shift + pad, which on the original is the silent selection of a sample: Shift + pad does that again.

### Fixed
- **Clear + knob on the drums:** the LED turned right is the original’s **blue**; a dim red-orange showed before (A4, **S**).
- **Deleting a pack:** Clear stays steady white while it asks (it blinked) and the packs get their colours back when it ends or is cancelled (they could stay dark until leaving the view) (A8).
- **Import memory:** when it was full, a copy between packs could be written over a sample that still played (it sounded wrong until the pack was loaded again; the files were right). Now nothing changes when there is no room (A8).
- **Patches in the source view:** with Duplicate held before the synth source view opened, its pads copied or swapped patches; not any more (A8).

## RC0.2 / RC0.2S — 2026-10-10

RC0.2 = SC37.5. RC0.2S = RC0.1S + the Glitch overload.

### New
- **Overload in the Glitch** (C6, D6, **S**). K4 in the upper half imitates an overloaded DSP: late blocks (clicks) and, from ~3/4, everything lower and slower. It is a simulation: the DSP is not really loaded.

### Fixed
- **Deleting a pack:** the Clear LED did not light in the packs view (A8).

## RC0.1 / RC0.1S — 2026-10-10

RC0.1 = SC37.4. RC0.1S = RC0S + what this version adds outside the SD card.

### New
- **Copy samples and synth patches between packs** (A8): Duplicate + A in one pack, Duplicate + B in another; the source pack does not change. Inside one pack, Duplicate + A + B swaps (synth patches too).

### Changed
- **Delete a pack = Clear, the pack, Clear** (A8). In RC0 it was Clear held + pack, which did not work on the device.

### Fixed
- **Duplicate in the drum and synth Preset views:** it did not light or do anything on the device (A8).
- **Swapping samples inside a pack:** it left a click at the end (the file was rewritten from the DSP memory); the files are now moved as they are (A8).
- **Engine change of pad 27 with a held note:** no click (C1, **S**).
- **Pad 28** of MIDI 1 / 2 hidden while there are no oscillators (C1, **S**).
- **Two Glitch slots at once:** the knobs are no longer copied (C6, **S**).
- **Colours:** Vinyl in peach and the Setup reverb / delay returns in their colours (**S**).

## RC0 / RC0S — 2026-10-09

First release candidate (= SC36.2; RC0S = SC362S, no writes of its own to the SD card): everything in the manual up to then, among other things the granular synth, the Glitch, the FX sequencer, Master FX, the MIDI track engine, the step-drummer, the new drum knobs and the pack management.
