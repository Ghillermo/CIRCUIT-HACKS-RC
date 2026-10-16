# Cambios — CIRCUIT-HACKS

*English version below: [Changelog](#changelog).*

Novedades y arreglos de cada versión candidata (RC). Cada RC tiene una **versión más segura** (sufijo **S**) sin las funciones que escriben en la tarjeta SD por su cuenta (gestión del pack, A8). Las referencias (A4, C6…) son las secciones del [manual](https://ghillermo.github.io/CIRCUITS-HACKS-RC/index.html). El detalle técnico está en [`docs/NOTAS.md`](docs/NOTAS.md).

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
