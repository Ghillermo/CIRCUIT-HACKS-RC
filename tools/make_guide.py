"""The guide by views (the user, 2026-10-15: «un nuevo manual … por funciones, centrándose en todo lo que está disponible desde cada vista y explicando cada
función, opción y submenú»; the old manual stays as the list of features).  Spanish here, English in tools/guide_en.py (same ids, same order).
Writes docs/GUIA.md, docs/GUIA.en.md, docs/manual/guia.html, docs/manual/guide.html; the drawings and the page style are tools/make_manual.py's.

    python tools/make_guide.py
"""
from __future__ import annotations
import html
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_manual as M  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BETA = "RC2"                           # the version the «desde» marks refer to (Beta 1.x until 2026-10-17: «solo Beta 1.x»)
B = f"*(desde {BETA})*"
NBETA = "RC2.02"                    # the newest release: its own «desde» marks (2026-10-18: Beta 3.0 went out as RC2.04; the {B} ones are RC2's)
NB = f"*(desde {NBETA})*"
XBETA = "Beta 3.22"                   # the beta after it (private): «solo Beta 3.22»
XB = f"*(solo {XBETA})*"
PARTS = [("0", "Introducción"), ("1", "Setup"), ("2", "Sintes de stock (Synth 1 / 2)"), ("3", "Pistas MIDI (MIDI 1 / 2)"), ("4", "Pattern Settings"),
         ("5", "Drums"), ("6", "Master FX"), ("7", "FX"), ("8", "Sidechain"), ("9", "Escenas y patterns"), ("10", "Projects y packs"), ("A", "Apéndice")]
# the chapters the user listed (2026-10-15): setup, sintes de stock, pistas MIDI, pattern settings, drums, Master FX, FX, sidechain, scenes y patterns, projects y packs
PART_OF = dict(convenciones="0", botones="0", setup="1", **{"advanced-setup": "1"}, **{"synth-nota": "2", "synth-fuente": "2", "synth-preset": "2"},
               **{"midi-preset": "3", "midi-knobs": "3", "midi-matriz": "3", "midi-fm": "3", "midi-cc": "3", "step-drummer": "3", "midi-muestra": "3"}, **{"pattern-settings": "4"}, probabilidad="4", micropasos="4",
               **{"drum-pista": "5", "drum-preset": "5", "drum-cromatica": "5"}, **{"master-fx": "6", "vista-fx": "7"}, sidechain="8",
               escalas="2", patterns="9", mixer="9", projects="10", packs="10", guardado="A", midi="A", instalar="A")
V = []                                # the views: dict(id, part, title, how, detail, figs = [(old section id, figure index)])


def view(vid, part, title, how, detail, figs=()):
    V.append(dict(id=vid, part=part, title=title, how=how, detail=detail.strip("\n"), figs=list(figs)))


# ===================================================================================================== I
view("convenciones", "I", "Cómo leer esta guía",
     "Cada capítulo es una vista del aparato: cómo se llega, qué hace cada pad, knob y botón, y los submenús que abre.",
     f"""
- **Pads 1-32** de arriba-izquierda a abajo-derecha: fila 1 = 1-8, fila 2 = 9-16, fila 3 = 17-24, fila 4 = 25-32.
- **Knobs K1-K4** arriba, **K5-K8** abajo. «**Shift + X**» = mantener Shift mientras se usa X; lo mismo con Clear y Duplicate.
- Lo que no aparece aquí funciona como en el aparato original (manual oficial de Novation).
- {B} = nuevo desde RC2 (no está en RC0.9 / RC0.9S). La versión más segura, RC2.09S (y las S anteriores), no escribe nada propio en la tarjeta: lo marcado «escribe en la tarjeta» no hace nada en ella (el LED de Save se pone rojo).
- {NB} = nuevo en RC2.02 (no está en RC2.01).
- {XB} = solo en la **Beta 3.22**, la versión de prueba con las funciones nuevas (no está en RC2.09).
- La **lista de características** (el manual anterior) resume cada función en una línea, por temas.
""")

view("botones", "I", "Botones que funcionan en todas las vistas",
     "Shift, Clear, Duplicate, Save y Octave ganan funciones según la vista; aquí, las que valen en casi todas.",
     f"""
| Gesto | Dónde | Qué hace |
|---|---|---|
| **Clear + knob a la derecha** | drums, motor de las pistas MIDI, Master FX | El knob vuelve a su valor por defecto (las dos capas, con y sin Shift). LED **lavanda** = hecho, como en el original. |
| **Clear + knob a la izquierda** | drums (knobs de stock), motor de las pistas MIDI {B} | Borra la automatización de ese knob en el patrón que suena, como el original (LED **rojo**). En el motor MIDI, la de los dos carriles del knob (con y sin Shift) que tengan automatización. |
| **Shift** | todas | Con Shift pulsado, los atajos disponibles se iluminan en **amarillo**; la opción elegida, en otro color. |
| **Save** | todas | Guarda el proyecto como siempre; además escribe en el pack los samples sustituidos por capturas (Preset de drums) si caben en la memoria de samples *(escribe en la tarjeta)*. |
| **Pulsar el botón de la pista otra vez** | Synth 1 / 2 | Abre la vista de la fuente del sinte (2.3). |
| **Clear + Synth 1 / 2** | su vista | {B} Sus ocho macros a los valores del patch cargado. |
| **Clear + el botón de un drum** | su vista | {B} Borra la automatización de sus knobs en el patrón que suena y pone sus ocho knobs por defecto. |
| **Dos botones de pista de notas a la vez** | todas | Teclado partido {B}: Synth 1 + Synth 2; {NB} cualquier par de Synth 1, Synth 2, MIDI 1 y MIDI 2. |
| **Shift + Clear** | todas | Metrónomo en cuatro estados {B}: sin metrónomo → metrónomo → solo cuenta atrás → cuenta atrás y metrónomo. Con Shift pulsado, el LED de Clear enseña el estado: rojo (sin metrónomo) / verde (metrónomo) / magenta (solo cuenta atrás) / cian (las dos). El volumen del clic es el de stock: **Tempo/Swing** y **K5**. |
| **Play** con Record armado y la cuenta atrás | parado | Un compás de cuenta atrás (4 clics al tempo del proyecto, Record parpadea en rojo) y después arranca la grabación {B}. Play durante la cuenta la cancela. La cuenta atrás se guarda con el proyecto. |
| **Shift + Play** | todas | {B} **Cuantiza** el patrón que suena en la pista elegida: las notas y los golpes grabados fuera de la rejilla van al paso más cercano (micropasos 1-2 → el inicio de su paso; 3-5 → el del siguiente; los del último paso, al primero). En los drums, un paso con varios golpes (un redoble) se queda. Con Shift el LED de Play se ve amarillo; verde después de cuantizar. Sustituye al Shift + Play del original (otra forma de arrancar). |
| **Shift + Scales** | todas | Editor de la escala propia {B} (2.2). |
| **Mixer dos veces** | todas | Master FX (6.1). |
| **Scales + Preset + Note** al encender | — | Modo de recuperación del bootloader de Novation: permite volver a instalar cualquier firmware. |

- Los LEDs de los knobs enseñan con su **brillo** el valor de las funciones nuevas (más brillo = más valor; en los knobs bipolares, oscuro en el centro).
- Los colores animados (que pulsan) no se usan para estados fijos.
- **LFO a tempo** {XB}: los knobs de **velocidad de LFO** (K7 de la página VCA-VCF del motor de MIDI 1 / 2, Shift + K4 de la matriz, Shift + K7 de los drums, K1 del Auto-Filter y del Phaser en Master FX) son **bipolares**: al centro, el LED tenue; **a la derecha, LFO libre** (más rápido cuanto más a la derecha); **a la izquierda, a tempo**, del centro hacia fuera 1/16T, 1/16, 1/8T, 1/8, 1/4T, 1/4, 1/2T, 1/2, 1 compás T, 1 compás, 2T, 2, 4T, 4, 8T y 8 compases (4 clics cada una), con cada ciclo empezando en el **primer tiempo del compás** (se recoloca en cada tick del secuenciador; parado sigue al tempo). En la matriz, cada forma de Shift + K4 es un tramo con su propio centro. Lo guardado antes con otra velocidad puede sonar distinto.
""", [("atajos", 0)])

# ===================================================================================================== II
view("synth-nota", "II", "Vista de pista de Synth 1 / 2 (Note, Velocity, Gate)",
     "Pulsa **Synth 1** o **Synth 2**. Los pads tocan el sinte como siempre.",
     f"""
- **Pulsar el mismo botón otra vez** (con su vista en pantalla) abre la **vista de la fuente** del sinte (2.3).
- **Synth 1 + Synth 2 a la vez** (mantén uno y pulsa el otro) abre el **teclado partido** {B}; {NB} **cualquier par de pistas de notas** (Synth 1, Synth 2, MIDI 1, MIDI 2: mantén un botón y pulsa otro):
- las dos filas de arriba tocan la pista que mantuviste primero y las dos de abajo la otra, cada una con su escala, su octava, su velocity y sus colores (en RC2: arriba siempre Synth 1);
- los knobs y Octave son los de la primera pista que pulsaste; un botón de drum no abre el teclado partido;
- {XB} **mantén un botón de pista** (Synth 1 / 2, MIDI 1 / 2, Drum 1-4) con el teclado partido abierto: mientras lo mantienes, **los 8 knobs (y sus luces) son los de esa pista**; al soltarlo vuelven a la primera;
- cualquier botón de pista ({XB} un toque corto, sin girar un knob) o de vista lo cierra (las notas pulsadas se sueltan); Play, Record, Octave y Shift no.
- Los macro knobs funcionan como siempre; sus destinos se pueden editar en el aparato (vista de la fuente, pad 32).
- **Vista Velocity, Shift + pad de paso** {XB} (Synth 1 / 2 y MIDI 1 / 2): ese paso **suelta la automatización**: ahí no suena ningún carril y los parámetros que la automatización había movido vuelven a la posición de su knob (la de antes de la automatización; girar el knob a mano la cambia). Otra vez = quitarlo. Con Shift, en la vista Velocity, los pads de paso se ven amarillos y los marcados en rojo; en la página 17-32, los pasos 17-32. Se guarda con el patrón.
- **Pantalla de acordes** {XB} (Synth 1 / 2 y MIDI 1 / 2, solo en la **Note ampliada**: Note dos veces): **Shift + pad 8** la enciende y la apaga (con Shift el pad 8 se ve amarillo, verde con la pantalla encendida).

| Pads | Qué hacen |
|---|---|
| Fila 1 | El tipo de acorde: mayor, menor, 7, m7, maj7, sus4, dim, aum. **Shift + pads 1-7**: sus2, 6, m6, add9, 9, 7sus4, quinta (con Shift la fila en amarillo; el elegido en blanco) |
| Pads 9-12 | La inversión: fundamental, 1.ª, 2.ª, 3.ª (naranja; la misma otra vez = fundamental) |
| Pad 13 | Voicing abierto: la segunda nota una octava arriba |
| Pad 14 | La fundamental añadida una octava abajo |
| Pad 15 | Diatónico: el acorde con las terceras de la escala del proyecto (también la propia y Jankó): 3 notas, 4 si el tipo tiene 4 o más |
| Pad 16 | Latch: el acorde sigue sonando al soltar el pad, hasta la siguiente fundamental (o hasta apagar latch o la pantalla) |
| Filas 3-4 | Las fundamentales: las mismas notas que el teclado de la vista Note (escala, tónica, Octave, Jankó). Mientras mantienes el pad suena el acorde, hasta 6 notas, con la velocity del pad |

- Pads 13-16 verdes encendidos, tenues apagados.
- Lo que tocas suena y se graba con Record como **notas normales del patrón**: se reproduce igual sin la pantalla de acordes. Con el **arpegiador** encendido, el acorde se arpegia con un solo dedo.
- El tipo y los modificadores de cada pista **no se guardan** (se pierden al apagar).
- En MIDI 1 / 2 con el modo muestra, la Note ampliada sigue siendo el selector de samples.
""", [("teclado-partido", 0)])

view("escalas", "II", "Vista Scales y escala propia",
     "Pulsa **Scales** como siempre (tónica y escala de stock); **Shift + Scales** para la escala propia.",
     f"""
- **Shift + Scales** abre la vista Scales con el **editor de la escala propia** {B}; con Shift pulsado, el botón Scales se ve amarillo. Scales otra vez, Shift + Scales u otra vista lo cierran.
- **El teclado del editor** son dos octavas en piano a partir de la **tónica** (la de la vista Scales, que se elige como siempre fuera del editor): fila 4 = teclas blancas de la primera octava (tónica, +2, +4, +5, +7, +9, +11, +12), fila 3 = sus negras; filas 2 / 1 = la segunda octava (+12 … +24).
- **Pulsar una tecla** la pone o la quita (hasta **7**). La más alta pulsada es el **periodo**: la tónica de la siguiente iteración (no tiene por qué ser la octava); las demás son las notas de la escala. Colores: tónica blanca, notas verdes, periodo naranja, teclas libres tenues.
- **En las pistas de notas** (Synth 1 / 2, MIDI 1 / 2) cada fila de pads es **una iteración**: sus notas y la nota del periodo al final, como las octavas de una escala de stock. Con **4 notas o menos**, **dos iteraciones por fila** (una en cada mitad). Octave ▼ / ▲ mueven una fila.
- La escala propia también vale para **iluminar las notas** de la secuencia, el cuantizado y el **random-mutate** (otra nota de la misma iteración).
- **Elegir una escala de stock** (pads 17-32 fuera del editor) apaga la escala propia; las teclas se guardan: volver al editor la enciende otra vez. Mientras está encendida, ninguna escala de stock se ve elegida.
- Se guarda **con el proyecto**; un proyecto nuevo empieza sin escala propia.
- **Jankó** {XB}: en el editor, **Shift + pad 8** (arriba a la derecha; con Shift se ve amarillo) enciende la **disposición isomórfica Jankó** (el pad 8 en cian mientras está encendida): en las pistas de notas cada fila sube un **semitono** y cada columna un **tono**, y el pad de abajo a la izquierda es la **tónica** de la vista Scales. Cada tipo de acorde tiene la misma forma en cualquier tono (en la Note ampliada, con cuatro filas, caben todas las tríadas y cuatríadas). Están las 12 notas: las que suenan se iluminan en su pad y el random-mutate elige cualquiera de las 12 de su octava. **Octave ▼ / ▲ = medio tono** (Shift + Octave sigue transponiendo el patrón una octava). Shift + pad 8 otra vez, una tecla del editor o una escala de stock lo apagan. Se guarda con el proyecto.
""")

view("synth-fuente", "II", "Vista de la fuente del sinte",
     "Con la vista de Synth 1 / 2 en pantalla, **pulsa su botón otra vez**. Cualquier botón la cierra.",
     f"""
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

### Pad 32: editor de los destinos de los macro knobs {B}
Cada macro knob tiene 4 ranuras; cada ranura, un destino, un tramo del recorrido (inicio y fin) y una profundidad.
1. **Pad 32** (verde azulado) = editor encendido; los knobs ya no mueven los macros.
2. **Gira un knob** para elegir su macro (LED blanco); el primer giro no cambia nada.
3. El knob cambia el campo actual; **Octave ▼ / ▲** = campo siguiente / anterior: ranura (1-4, amarillo) → inicio (verde) → fin (naranja) → destino (blanco = CC; azul claro, magenta, violeta = NRPN de los bancos 0, 1, 2) → profundidad (verde azulado positiva, rojo negativa). Los pads dibujan el número.
4. Cualquier pad suelta el macro; el pad 32 apaga el editor.
- El destino recorre primero los 31 parámetros con CC (por número) y luego los 39 que solo tienen NRPN. Los cambios suenan al momento; para dejarlos en el pack, guarda el patch (vista Preset).

### Pad 30: step-drummer del sinte
La vista del step-drummer es la misma que la de las pistas MIDI (3.5): pads 1-16 pasos, 17-24 = **macro 1-8** como destino, K1-K8 = los 8 pares de pasos. El valor de cada par es la posición del macro, escrita como automatización; un par vacío empieza en 0 {B} (antes, en la posición actual del macro).
- {B} Play y Record no cierran el step-drummer del sinte; si vas a otra vista, **pulsar Synth 1 / 2** lo vuelve a abrir (hasta que lo cierras con el pad 30).
""", [("fuente-sinte", 0), ("destinos-macro", 0)])

view("synth-preset", "II", "Vista Preset de Synth 1 / 2",
     "Pulsa **Preset** con Synth 1 / 2 elegido. Los pads eligen patch como siempre (4 páginas, 128 patches del pack).",
     f"""
| Gesto | Qué hace |
|---|---|
| Colores de los patches {B} | **Azul oscuro** = mono, **lavanda** = mono con glide, color de la pista = poly; el elegido, más claro. |
| **Clear + pad**, **Clear + el mismo pad** antes de ~5 s {B} | **Guarda** en ese hueco el patch tal como suena (knobs, MIDI recibido, destinos de macro). El primer toque pregunta (parpadea en blanco); otro pad mueve la pregunta *(escribe en la tarjeta)*. |
| **Duplicate + pad A + pad B** (mismo pack) | Intercambia los dos patches. |
| **Duplicate + pad A**, cargar otro pack, **Duplicate + pad B** | Copia el patch A sobre B en el otro pack (el pack de A no cambia); B puede estar vacío *(escribe en la tarjeta)*. |

- El original no puede guardar patches desde el aparato. El patch guardado conserva el nombre del que estaba cargado.
- No funciona en el pack de la memoria interna (solo lectura para el mod): el LED de Save se pone rojo.
""", [("colores-patch", 0), ("guardar-patch", 0)])

# ===================================================================================================== III
view("midi-preset", "III", "Vista Preset de MIDI 1 / 2",
     "Pulsa **MIDI 1** o **MIDI 2** y luego **Preset**. Además de las plantillas de stock, aquí vive el sinte propio de la pista.",
     f"""
- **Teclado externo** *(desde RC2.08)*: las notas que entran por MIDI (USB o DIN) en el canal de MIDI 1 / 2 **tocan su sinte propio** (antes solo se grababan); no se reenvían a la salida MIDI.
### Pads
| Pad | Función |
|---|---|
| 1-5 | Página de knobs del motor: 1 VCA-VCF, 2 OSC 1 (granular en ese motor), 3 OSC 2, 4 secuenciables, 5 modulación. **Clear + el pad** {B}: los valores de esa página (con y sin Shift) a los iniciales. |
| 6 | {NB} **Matriz de modulación** (azul claro; ver «Matriz de modulación»). **Clear + pad 6**: todas las fuentes apagadas. |
| 9-24 | **Patches del sinte propio** {B}: ver abajo. |
| 25 | **Editor de CC** de los macros MIDI (3.4). |
| 26 | **Patch flip**: cada nota de la pista sale como Program Change (por el canal de la pista; si ese canal es el de un sinte o los drums, también por dentro). Excluyente con el motor. |
| 27 | **Motor** de la pista: apagado → amarillo (entrada de línea) → verde (oscilador) → rojo (VA-drum) → magenta (granular) → cian (muestra {B}) → azul (secuenciador de efectos). |
| 28 | Uno / dos osciladores (oscilador y VA-drum). |
| 29 | Orden de la cadena: VCA → FX → filtro / filtro → VCA → FX (en el color de la página VCA-VCF {B}). |
| **Shift + 29** {B} | **Gate retrigger**: encendido (verde con Shift, por defecto) = cada nota nueva vuelve a disparar la envolvente; apagado (amarillo) = **legato**: con otras notas pulsadas, una nota nueva solo cambia la altura. Se guarda con el proyecto. |
| 30 | Abre el **step-drummer**; **Shift + pad 30** lo desactiva. |
| 31 | Solo en VA-drum: la velocity escala las envolventes de pitch y filtro. |

### Patches del sinte propio (pads 9-24) {B}
- 16 huecos por página; **Octave ▼ / ▲** = 4 páginas (64 huecos por pack, comunes a MIDI 1 y MIDI 2).
- **Tocar** = cargar (suena la tónica mientras mantienes el pad). **Clear + pad** dos veces = guardar. **Duplicate + A + B** = intercambiar; **Duplicate + A**, otro pack, **Duplicate + B** = copiar a otro pack (Duplicate en amarillo mientras hay uno esperando).
- Colores: melocotón tenue = con patch, brillante = el último usado, violeta = vacío.
- Un patch guarda el motor entero: motor elegido, osciladores, orden, todos los valores y el ajuste del step-drummer *(escribe en la tarjeta)*.
- **Clear + el botón de la pista** {B} devuelve todos los valores del motor a los iniciales (el motor elegido se queda).

### Los motores (pad 27)
- **Elegir el motor** {XB}: un toque al **pad 27** abre la **fila de motores** en los **pads 17-23**: apagado (blanco), entrada de línea, oscilador, VA-drum, granular, muestra y secuenciador de efectos, en sus colores; el actual brillante, los demás tenues. Tocar uno lo elige y la fila sigue abierta; **pad 27 otra vez** la cierra y vuelve la lista de patches (pads 9-24, que mientras tanto no cargan nada). Shift + pad 27 sigue pasando al motor siguiente (en RC2.09, cada toque del pad 27).
- **Entrada de línea** (amarillo): la entrada de audio de la pista (línea 1 en MIDI 1, línea 2 en MIDI 2) pasa por el VCA-VCF; las notas de la pista lo disparan.
- **Oscilador** (verde): morph seno → triángulo → sierra → cuadrada, SHAPE, segundo oscilador (pad 28) con FM, ring, sync y modos bit a bit; dos notas = parafonía (con un oscilador, {B}: la última nota manda y al soltarla vuelve la anterior).
- **VA-drum** (rojo): VCA de un disparo, envolventes de decay para pitch (knob Sustain) y filtro (knob Release), ruido blanco (velocidad del LFO) y valores aleatorios en lugar del LFO.
- **Granular** (magenta): hasta 16 granos desde un sample del pack o la captura (página 2, capítulo siguiente).
- **Muestra** (cian) {B}: un sample del pack de un golpe a la altura de la nota (C3 = como se grabó), con sample flips por paso; se elige en la vista Note ampliada (ver «Modo muestra»).
- **Secuenciador de efectos** (azul): el step-drummer de la pista dispara los huecos de la fila inferior de Master FX (6.1).
- **FM** (violeta) {XB}: el **pad 24** de la fila: un sinte FM de 4 operadores, variante del oscilador, con 16 algoritmos (clásicos, percusivos, campanas y cuerdas) y sus knobs en la **página 7** (capítulo «FM de 4 operadores»).
- La pista sigue mandando su MIDI con cualquier motor.
""", [("motor-midi", 0), ("patches-midi", 0)])

view("midi-knobs", "III", "Páginas de knobs del motor de MIDI 1 / 2",
     "Con el motor encendido, los pads 1-5 de la vista Preset eligen qué hacen los 8 knobs; Shift da una segunda capa.",
     f"""
### Página 1 — VCA-VCF
| Knob | Solo | Con Shift |
|---|---|---|
| K1 | Ataque | Sustain |
| K2 | Release | Decay |
| K3 | Envolvente → nivel | LFO → nivel |
| K4 | Envolvente → filtro | LFO → filtro |
| K5 | Filtro | Tipo de filtro (DJ, LP 12, HP 12, BP, notch, LP 24, HP 24) |
| K6 | Resonancia | Gain del VCA (hasta +18 dB con saturación) |
| K7 | Velocidad del LFO (bipolar {XB}: derecha libre, izquierda a tempo; 0.2) | — |
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

**Qué hace SHAPE en cada forma de onda** (K2; SHAPE 2 en el OSC 2, igual). El centro del knob es la forma pura (en la sierra *(solo Beta 3.22)*, la izquierda del todo); la envolvente (K4) y el LFO (K6) mueven SHAPE desde la posición del knob. Con WAVE entre dos formas, SHAPE actúa sobre las dos a la vez, cada una a su manera:

| Forma (WAVE) | SHAPE a la izquierda del centro | Centro | SHAPE a la derecha del centro |
|---|---|---|---|
| Seno (0) | Nada: la forma pura | Pura | **Wavefold**: la onda se amplifica (hasta unas 8 veces a la derecha del todo) y se pliega sobre sí misma: más armónicos cuanto más a la derecha |
| Triángulo (42) | *(solo Beta 3.22)* **Rampas exponenciales**: picos afilados y valles anchos, más armónicos cuanto más a la izquierda (en RC2.09, nada) | Puro | **Wavefold**, como el seno |
| Sierra (84) | *(solo Beta 3.22)* Todo el recorrido: a la izquierda del todo una sierra normal; hacia la derecha, **supersaw** de 7 sierras (la central y 6 desafinadas que suben de nivel y se separan; a la derecha del todo, la supersaw entera) | Media supersaw | Supersaw entera a la derecha del todo |
| Sierra en RC2.09 | La rampa se curva hacia arriba (sube rápido al principio y se aplana) | Rampa recta | La rampa se curva hacia abajo (empieza plana y sube al final) |
| Cuadrada (126) | Pulso cada vez más estrecho (hasta un 3 % aprox.) | Cuadrada (50 %) | Pulso cada vez más estrecho por el otro lado (hasta un 97 % aprox.; suena igual que el de la izquierda) |

### Página 2 — granular
| Knob | Solo | Con Shift |
|---|---|---|
| K1 | Tono ±24 st | Fino ±1 st |
| K2 | Posición en el sample | Dispersión de la posición |
| K3 | Scan (centro congelado) | {XB} **Bipolar**: a la izquierda, probabilidad de grano al revés (hasta 100 %); a la derecha, dispersión del tono (hasta ±24 st). En RC2.09: probabilidad de grano al revés |
| K4 | Tamaño del grano 5-500 ms | {XB} **Dispersión estéreo** (ver abajo). En RC2.09: dispersión del tono |
| K5 | Densidad 1-16 granos | Ventana |
| K6 | Zona del scan | Modo de nota: tono / slicer / stretch {B} |
| K7 | LFO → posición | LFO → tamaño |
| K8 | Envolvente → posición | Fuente: la captura o el sample de un drum {B} |

- **Modo de nota (Shift + K6):** **tono** = las notas cambian la altura de los granos; **slicer** = el sample se parte en 16 trozos y cada nota toca uno (la nota 36 el primero, cada nota más arriba el siguiente; cada 16 notas vuelve a empezar); **stretch** {B} = las notas cambian la altura y el tramo desde la posición (K2) hasta el final dura **K3 pasos** (1-64) a cualquier tempo, sin cambiar la altura, alineado con el inicio del transporte; parado, la posición se queda congelada.

- **Granular en estéreo** {XB}: con **Shift + K4** por encima de 0, cada grano sale a un lado al azar, tanto más separado cuanto más alto; el **panorama de la pista** (Mixer) decide la proporción: al centro, mitad y mitad; a la derecha, más granos a la derecha. La parte estéreo (lo que difiere entre los lados) solo sigue el VCA y el nivel de la pista: el filtro y el efecto del motor, el panorama, los envíos y el sidechain actúan sobre el centro.

### Páginas 3-5
- **Página 3 (OSC 2):** {B}: los ocho valores sin Shift, según la serigrafía: K1 Oscillator TUNE 2, K2 Osc mod SHAPE 2, K3 Amp envelope MIX OSC 1 ↔ OSC 2, K4 Filter envelope FM, K5 Filter frequency FINE 2, K6 Resonance BITSYNC, K7 Modulation WAVE 2, K8 FX RING (en RC0.9: K1 TUNE 2 / FINE 2, K2 SHAPE 2 / FM, Shift + K3 RING, K7 WAVE 2).
- **Página 4:** los 8 valores secuenciables: con Record + Play sus movimientos se graban en el patrón (TUNE, Release, Env → nivel, Env → filtro, Filtro, Resonancia, Velocidad del LFO, Efecto). {XB}: **Shift + knob** = el **destino** de ese knob: los 33 parámetros del motor en el orden y los colores de la matriz de modulación (el LED en el color de su página; 4 clics por parámetro); con **Clear mantenido antes de Shift**, el de fábrica. Mientras eliges, **los pads 9-24 enseñan dónde está el destino**, como al girar un knob de la matriz: el pad de su página brillante y los knobs de esa página (K1-K8 arriba, Shift + K1-K8 abajo; el destino brillante). El carril graba y reproduce el destino nuevo (lo que ya tenía grabado mueve ahora ese parámetro). Se guardan con los patches del sinte propio (vista Preset de MIDI 1 / 2); un patch sin ellos carga los de fábrica.
- **Foto de los valores en un paso** {XB}: con la vista de pista de MIDI 1 / 2 (motor encendido), **Record mantenido + un pad de paso** (pads 1-16; con 17-32, los pasos 17-32) escribe en los carriles de ese paso los parámetros que **no están en su valor inicial** (el de Clear + knob a la derecha), y solo esos. Un parámetro que no tiene carril toma uno cuyo parámetro sí está en el inicial (en orden de carril), y ese carril se borra antes en el patrón; si no caben, los primeros en el orden de la matriz. El paso no cambia sus notas y Record queda como estaba.
- **Página 5:** ADSR arriba, LFO abajo. {B}: **Shift + K8 = forma del LFO**: diente de sierra inverso (naranja, la de siempre), diente de sierra (magenta), triángulo (verde), cuadrada (roja), seno (cian), sample & hold (blanco: un valor al azar en cada vuelta); {NB}: **sample & hold suavizado** (violeta: se desliza de un valor al azar al siguiente durante cada vuelta), y **sin forma guardada (un proyecto nuevo o de antes) el triángulo** (en RC2: el diente de sierra inverso; un patch propio de antes de las formas sigue cargando el diente de sierra inverso). Un paso cada 4 clics, el LED de K8 con Shift en su color. Se guarda con el proyecto y en el patch propio; con el VA-drum el LFO sigue siendo su ruido.
- **Página 6** {NB}: la matriz de modulación (capítulo siguiente).
- **Página 7** {XB}: con el motor FM, sus operadores y su algoritmo (capítulo «FM de 4 operadores»).
- Los knobs de tipo se ven de color (tipo) y brillo (posición dentro del tipo). Todo sale y entra por CC / NRPN (A.2 y la referencia MIDI).
""", [("granular", 0)])

view("midi-matriz", "III", "Matriz de modulación",
     f"{NB} MIDI 1 / 2 con el motor encendido: vista Preset, **pad 6**. Los 8 knobs pasan a ser 8 fuentes de modulación.",
     """
| Knob | Fuente | Con Shift |
|---|---|---|
| K1 | Velocity de la nota | — |
| K2 | Nota (C3 = 0; una octava = un cuarto del recorrido) | — |
| K3 | Azar: un valor nuevo en cada nota | — |
| K4 | LFO 2 | Forma × velocidad: triángulo (verde, la inicial), diente de sierra (magenta), cuadrada (rojo), sample & hold (blanco: escalones), sample & hold suavizado (violeta: deslizándose); los colores del LFO del motor; en cada forma, de 0,05 a 20 Hz ; {XB}: en cada forma, la mitad izquierda de su tramo a tempo y la derecha libre (0.2) |
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
- **Se guarda con los patches del sinte propio** (pads 9-24: Clear + pad dos veces, también al intercambiarlos o copiarlos entre packs); un patch guardado antes la carga apagada. {XB} también **se guarda con el proyecto** (con el resto del sinte propio); antes no se guardaba con el proyecto ni al apagar el aparato. No tiene CC / NRPN.
- Las modulaciones llegan al motor unas 100-250 veces por segundo, repartidas entre todo lo que se mueve en la pista: varias fuentes rápidas a la vez se actualizan más despacio.
""", [])

view("midi-fm", "III", "FM de 4 operadores",
     f"{XB} MIDI 1 / 2: vista Preset, un toque al **pad 27** y el **pad 24** de la fila de motores (violeta). El **pad 7** abre su página de knobs (violeta brillante en ella).",
     """
| Knob | Solo | Con Shift |
|---|---|---|
| K1-K4 | Ratio de los operadores 1-4: 0,5 … 16 (verde = entero, azul claro = y medio, verde azulado = inarmónico: 0,71, 1,41, 4,24) | Ataque de los operadores 1-4 (0 … unos 3 s; azul claro) |
| K5 | Nivel del operador 1 (naranja) | Algoritmo (16, 8 clics cada uno; el color de su familia) |
| K6 | Nivel del operador 2 | Feedback (magenta) |
| K7 | Nivel del operador 3 | Ruido (blanco) |
| K8 | Nivel del operador 4 | Release (azul) |

- **Es una variante del oscilador:** la nota, TUNE / FINE, la envolvente de pitch y el vibrato de la página 2 siguen valiendo; detrás, el VCA-VCF, el efecto y la matriz como con el oscilador. Una nota a la vez (la última manda).
- **El nivel** de un portador es su volumen; el de un modulador, cuánto modula (hasta 4π).
- **Envolventes A/R con sustain fijo:** con la nota pulsada, un operador **sostenido** se queda arriba después de su ataque; uno **percusivo** (lo dice el algoritmo) cae con el release aunque la nota siga. Al soltar, todos caen con el release. **El release es uno para todos y más largo cuanto más fuerte la nota**; el algoritmo lo acorta o alarga en cada operador.
- **Ruido:** blanco, con la envolvente del operador que diga el algoritmo (el 1, salvo la caja), sumado después del FM, en cualquier algoritmo.
- **Clear + knob** = su valor inicial; **Clear + pad 7** = todos.
- **Se guarda con los patches del sinte propio** (con el motor en FM); un patch de antes lo carga apagado. No tiene CC / NRPN. Otro motor de la fila (o Shift + pad 27) lo apaga.

| # | Algoritmo | Familia |
|---|---|---|
| 1 | 4 → 3 → 2 → 1 (pila) | clásicos (blanco) |
| 2 | 3 y 4 → 2 → 1 | |
| 3 | 4 → 1 y 3 → 2 → 1 | |
| 4 | 4 → 3 → 1 y 2 → 1 | |
| 5 | dos pilas: 4 → 3 y 2 → 1 (portadores 1 y 3) | |
| 6 | 4 → 1, 2 y 3 (tres portadores) | |
| 7 | 4 → 3; 2 y 1 solos (tres portadores) | |
| 8 | órgano: los cuatro portadores | |
| 9 | bombo: 2 → 1; el 4 es la caída de pitch (su nivel = cuánto cae, hasta 3 octavas; su release = cuánto tarda) | percusivos (rojo) |
| 10 | caja: 2 → 1 + ruido con la envolvente del 3; caída de pitch del 4 | |
| 11 | metal / hi-hat: 2, 3 y 4 → 1 con ratios inarmónicos (× 1,41, 2,71, 3,49) | |
| 12 | tom / zap: 3 → 2 → 1; caída de pitch del 4 | |
| 13 | campana: 2 → 1 y 4 → 3, ratios inarmónicos (× 3,5, × 2,76) | campanas (verde azulado) |
| 14 | campana tubular: 2 y 3 → 1 (× 2,76, × 5,4), el 4 portador | |
| 15 | cuerdas: dos pilas (2 → 1, 4 → 3) desafinadas entre sí | cuerdas (verde) |
| 16 | ensemble: 4 → 1, 2 y 3, tres portadores desafinados | |
""", [])

view("midi-cc", "III", "Editor de CC de los macros MIDI (pad 25)",
     "Vista Preset de MIDI 1 / 2, **pad 25**: cambia desde el aparato qué CC / NRPN manda cada macro knob de la plantilla.",
     """
1. **Pad 25** (se enciende). 2. **Mueve un knob**: queda elegido y su número se dibuja con los pads.
3. **Octave ▼ / ▲**: campo siguiente / anterior. 4. **Gira el knob** para cambiar el valor.
5. **Guardar:** pad 26, o Octave ▼ hasta el paso de guardar (pad 26 y Save parpadean) y Octave ▼ otra vez.
6. **Descartar:** cualquier botón de vista, el pad 25 o un pad de plantilla.

| Número del primer campo | Tipo | Campos |
|---|---|---|
| cualquier otro | CC | número, inicio, fin |
| 99, 98 o 6 | NRPN de 7 bits | número, MSB, LSB, inicio, fin |
| 38 | NRPN de 14 bits | número, MSB, LSB, inicio (MSB, LSB), fin (MSB, LSB) |
""")

view("step-drummer", "III", "Vista del step-drummer",
     "MIDI 1 / 2: vista Preset con el motor encendido, **pad 30**. Synth 1 / 2: vista de la fuente, **pad 30**. Secuencia por pares de pasos sobre el patrón.",
     """
| Control | Función |
|---|---|
| Pads 1-16 | Los 16 pasos de la mitad mostrada: brillante = con nota, blanco = el que suena. Tocar = escuchar; **Shift + tocar** = poner / quitar nota. |
| Pads 17-24 | Página pitch: destino de la fila de pitch (MIDI: tono, OSC 2, WAVE, FM, MIX, env → filtro, SHAPE, decay) / macro 1-8 (sintes). Página velocity: **destino de la página 2** {B} (el mismo pad otra vez = ninguno). |
| Pad 32 | **Toggle pitch-vel** {B} (verde brillante = activado): además de su destino, la página pitch transpone las notas y la página velocity cambia la velocity. |
| K1-K8 | Los 8 pares de pasos (el que suena, blanco). |
| Octave ▲ / ▼ | Página pitch / velocity. |
| 1-16 / 17-32 | La otra mitad del patrón. |

- El valor del par desplaza el destino desde el centro (64 = sin cambio): suma o resta al valor que tenga el parámetro en la página del motor. {B} **El LED del knob muestra la cantidad**: tenue en el centro, más brillante cuanto más se aleja, hacia arriba o hacia abajo.
- Cada paso conserva la altura de su primera nota.
- {B} **Página velocity con destino:** los knobs escriben su valor en el par (MIDI: desde el centro, 64; sintes: desde 0), sin tocar la velocity si el toggle está apagado. Sin destino ni toggle, la página velocity no hace nada. En MIDI la página 2 usa el carril de automatización de REL: con el step-drummer activado, REL no se reproduce ni se graba.
- {B} **Toggle pitch-vel:** cada nota de la pista sube / baja **un grado de la escala** del proyecto (la de stock o la propia) **cada 8 pasos del knob**: MIDI desde el centro (−8 … +8 grados), sintes desde 0 (0 … +16), entre las notas 0 y 127; también al escuchar un paso. Con el toggle, los destinos de tono de la página pitch (tono de los dos osciladores / del OSC 2) ya no mueven el sinte propio: lo hace la nota. La velocity sigue a la página velocity.
- {B} En MIDI el pad 30 se ve **tenue** con el step-drummer desactivado y **brillante** activado (antes, apagado / tenue).
- Con **Record**, tocar un paso lo graba en el paso que suena (tiempo real).
- Con el motor en **secuenciador de efectos** (azul), cada knob elige un hueco de la fila inferior de Master FX: 0 nada, 1-5 pads 26-30, 6 el pad 31, y al final **random** {B} (LED blanco: uno al azar entre los que tienen efecto). Avanza despacio (un hueco cada ~48 pasos de giro). Un hueco sin efecto asignado no hace nada.
""".replace("{B}", B), [("step-drummer", 0), ("fx-seq", 0)])

view("midi-muestra", "III", "Modo muestra y selector de samples",
     f"{B} MIDI 1 / 2 con el motor en **muestra** (pad 27 cian, tras el granular): **Note dos veces** (vista Note ampliada). La pista toca un sample del pack de un golpe, a la altura de cada nota.",
     """
| Control | Función |
|---|---|
| Pads 17-32 | 16 samples del pack: tocar = el sample de la pista (cian) y suena; los demás tenues. |
| Octave ▼ / ▲ | Página siguiente / anterior de samples (4 páginas = los 64 del pack; encendido si hay más en ese sentido). |
| Pads 1-16 | Los 16 pasos de la mitad mostrada: melocotón = con sample flip, cian tenue (el fondo) = sin, blanco = el que suena. **Mantener un paso + tocar un sample** = su flip (el paso verde, su sample amarillo); también **mantener un sample + tocar pasos** (desde RC2.04); **Clear + paso** = quitarlo. |
| 1-16 / 17-32 | La otra mitad del patrón. |

- **La altura:** C3 (nota 60) = el sample como se grabó; una octava arriba = el doble de rápido. Las notas vienen de la vista Note normal, el step-drummer o el MIDI de entrada.
- **Un golpe:** el VCA se queda abierto y el sample suena hasta el final; cada nota nueva lo vuelve a empezar (una voz por pista). Filtro, efecto y LFO de las páginas del motor siguen.
- **En vivo:** con **Record + Play**, tocar un sample graba una nota 60 en el paso que suena con su flip.
- El sample de la pista es la misma fuente que la del granular (Shift + K8 en su página; la captura se elige allí).
- Los flips van en el carril de la automatización de nivel de la pista (Mixer): un flip sustituye el nivel grabado en su paso; grabar el nivel encima borra esos flips.
""".replace("{B}", B), [("modo-muestra", 0)])

# ===================================================================================================== IV
view("drum-pista", "IV", "Vista de pista de un drum (knobs)",
     "Pulsa **Drum 1-4**. Cada knob hace lo que dice su etiqueta, con una segunda capa en Shift.",
     f"""
| Knob | Solo | Con Shift |
|---|---|---|
| K1 Oscillator | Pitch ({B}: el de stock, continuo como el original; los pads de la vista cromática transponen encima) | Cantidad de la envolvente de tono |
| K2 Osc mod | Frecuencia del ring mod | Cantidad del ring mod |
| K3 Amp envelope | **Izquierda: decay** (el de stock). Pasado el máximo, **derecha: ataque** (fundido de entrada, hasta 1 s). Centro neutro. {B} | **Izquierda: inicio** del sample; **derecha: corte** desde el final (hasta 120/128 cada uno; *desde RC2.09* el inicio recorre todo el sample: antes llegaba al final a un cuarto del recorrido y más allá el golpe no sonaba). Centro = el sample entero. {B} |
| K4 Filter envelope | Envolvente → corte | Forma de la envolvente |
| K5 Filter frequency | Filtro / EQ (por defecto, el EQ tilt de stock) | **Modo de filtro**: EQ tilt de stock, paso banda, notch, comb, DJ |
| K6 Resonance | Resonancia | — |
| K7 Modulation | Cantidad del LFO: derecha = trémolo; izquierda = vibrato ({XB}: izquierda = **scan del inicio**: cada golpe empieza donde está el LFO, desde el inicio de Shift + K3 hasta un 64avo del sample más allá por cada paso del knob (a la izquierda del todo, todo el sample), sin pasar el corte; el LFO ya no vuelve a empezar con cada golpe) | Velocidad del LFO (bipolar {XB}: derecha libre, izquierda a tempo; 0.2; a tempo, el scan empieza en el inicio en el primer tiempo) |
| K8 FX | Distorsión; a la izquierda de 0, **bitcrush** | **Tipo de distorsión**: stock, suave, dura, plegada |

- **K3:** girando a la izquierda el ataque vuelve a 0 antes de que baje el decay; con Shift, uno de los dos (inicio o corte) vuelve a 0 antes de que se mueva el otro. LED: ataque en blanco; con Shift, inicio en el color del drum, corte en blanco.
- **Clear + K3 a la derecha** pone a 0 ataque, inicio y corte; **Clear + K8 a la derecha** quita también el bitcrush {B}. Clear + knob restablece las dos capas en los demás.
- **Clear + el botón del drum** {B} (con una de sus vistas en pantalla): los ocho knobs del drum, con su capa Shift, a sus valores por defecto.
- Con todo en neutro un sample suena como en el original. Todo se guarda con el proyecto y tiene NRPN.
- **Sidechain entre drums:** Shift + FX y Octave ▼ (8.1).
""", [("knobs-drums", 0)])

view("drum-preset", "IV", "Vista Preset de drums",
     "Pulsa **Preset** con un drum elegido. Los pads eligen el sample como siempre (Shift + pad = elegir sin que suene).",
     f"""
| Gesto | Qué hace |
|---|---|
| **Clear + pad**, **Clear + el mismo pad** | **Sustituye** ese sample por la captura de Master FX. Volátil hasta guardar: al guardar se escribe en el pack si cabe en la memoria de samples. |
| **Duplicate + pad A + pad B** (mismo pack) | Intercambia los dos samples (ficheros y tabla); suena al instante. |
| **Preset otra vez** {B} | Vista cromática / de escala del drum encendida / apagada (lo mismo que Shift + Preset). |
| **Varios pads mantenidos** {B} | Con el arpegiador del drum encendido (Pattern Settings, Shift + pad 25): el arpegio de los samples mantenidos (capítulo de Pattern Settings). |
| **Duplicate + pad A**, cargar otro pack, **Duplicate + pad B** | Copia el sample A sobre B (B puede estar vacío). Va al sitio de B si cabe; si no, a la memoria libre de importación. Nunca pisa un sample que suena. |
| **Shift + Preset** | Vista cromática / de escala (5.3). |

- Duplicate se ilumina en esta vista. Escribe en la tarjeta: no está en las versiones «S» ni en el pack de la memoria interna.
""", [("pack", 0)])

view("drum-cromatica", "IV", "Vista cromática y de escala de los drums",
     "**Shift + Preset** con un drum elegido. Los pads tocan el sample transpuesto según la escala.",
     f"""
- Tres filas de notas en la escala y la tónica de la vista Scales.
- **K1** = sesgo de tono en semitonos; **Shift + K1** = afinación fina en cents.
- Grabando, cada tono se graba solo en su paso. {B}: los pads transponen en semitonos sobre el pitch de K1 y, grabando, quedan en su paso dentro del carril de pitch del drum (un paso guarda un giro de K1 o una nota cromática); Clear + K1 a la izquierda (sostenido) borra los dos.
- **Vista Note de los drums:** los pads 25-28 repiten los cuadros de los drums 4 … 1.
- **Rollers de micropasos** {B} en las filas 1-3 de la vista Note de los drums: cada columna es el drum de su cuadro de abajo (columnas 1-4 = drums 4-1, columnas 5-8 = drums 1-4), en su color tenue. La columna izquierda de un drum son sus micropasos 1-3 (filas 1-3) y la derecha los 4-6: el drum 1 = pads 4, 12, 20 y 5, 13, 21. **Mientras se mantienen** (uno o varios, de uno o varios drums), el drum suena en **cada paso** en esos micropasos (con la velocity del paso, o 100 si el paso está vacío); se encienden mientras se mantienen. **Con el transporte parado** {B} también: al tempo del proyecto, empezando al pulsar el primero (velocity 100). **Con Record** sus golpes también se graban en el patrón (el micropaso, y velocity 100 en un paso vacío).
""")

# ===================================================================================================== V
view("pattern-settings", "V", "Vista Pattern Settings",
     "Botón **Pattern Settings** con una pista elegida: primer / último paso, sync rate y dirección como siempre, más los pads 25-28 y el arpegiador (Shift).",
     f"""
| Pad | Función |
|---|---|
| 1-16 | Primer / último paso (stock). |
| 17-24 | Sync rate (stock). |
| 25 | Abre la vista de probabilidad en **modo 2** (dinámicas y random-mutate; en los drums también {B}). **Clear + pad 25** (pistas de notas): borra las dinámicas y el random-mutate de todos los pasos del patrón; la frecuencia se queda {B}. |
| 26 | **Nudge** (naranja): el primer paso elegido pasa a ser el paso 1; lo de delante va al final (pasos y automatización, sobre 16 o 32). |
| 27 | Orden **fractal**: 1 · 1 2 · 1 2 3 · … hasta el último paso. |
| 28 | Orden **deconstruido**: las diagonales de la rejilla (1 6 11 16 · 2 7 12 13 · 3 8 9 14 · 4 5 10 15). |
| 29-32 | Dirección de stock; excluyente con 27 / 28. |

- Nudge y órdenes también en los drums. El orden se guarda con el patrón; Clear del patrón lo quita. {B}

### Arpegiador (pistas de notas) {B}
Con **Shift** pulsado, los pads del arpegiador conservan sus colores de Pattern Settings y lo elegido se ve en verde:

| Gesto | Función |
|---|---|
| **Shift + pad 25** | Arpegiador del patrón que suena en la pista: encendido / apagado. Sin Shift, el pad 25 se ve verde mientras está encendido (y sigue abriendo el modo 2). |
| **Shift + pads 27-32** | Orden del arpegio, independiente de la dirección del patrón: fractal, deconstruido, arriba, abajo, ping-pong, aleatorio. |
| **Shift + pads 17-24** | **Resolución** del arpegio, distinta del sync rate de la pista, en el mismo orden que los pads de sync rate (más lenta a la izquierda): 1/4, 1/4T, 1/8, 1/8T, 1/16, 1/16T, 1/32, 1/32T. El mismo pad otra vez = la de la pista (ningún pad verde). |

- **Secuencia:** cuando en un paso empiezan dos notas o más, suenan de una en una (a la resolución del arpegio), en el orden elegido sobre las notas ordenadas por altura, mientras dura la nota más larga del acorde. Cada nota dura **su propio gate, como mucho un paso de arpegio** (y lo que queda del acorde) y lleva su velocity: un acorde grabado manteniendo las notas suena arpegiado, uno introducido con notas cortas, staccato.
- **Entrada:** la primera nota suena como siempre; al mantener otra a la vez empieza el arpegio de las notas mantenidas, una por paso de arpegio (con el transporte parado, al tempo del proyecto), hasta soltarlas todas; cada nota dura un paso de arpegio. **Con Record se graba el acorde**, no las notas sueltas: el arpegio lo toca después la secuencia.
- **Orden pulsado** {XB}: las notas se arpegian en el orden en que se pulsaron (un acorde grabado, en el orden de sus notas en el paso), no por altura; arriba, abajo, ping-pong, aleatorio, fractal y deconstruido recorren ese orden. Al soltar una nota su hueco queda vacío y se salta; la siguiente nota que pulses ocupa el primer hueco vacío antes de ir al final.
- **Random-mutate** {XB}: si el paso del acorde tiene nivel de random-mutate, cada nota del arpegio pasa por él (otro grado de la escala, una octava arriba o abajo) como las notas normales; no se escribe nada en el paso. El arpegio en vivo (las notas mantenidas) usa el nivel del paso en que está la pista (en marcha, el que suena; parado, donde se quedó).
- **Notas largas al grabar** (desde RC2.04): el grabador de stock corta las notas a 16 pasos; ahora una nota o un acorde mantenido más tiempo sigue, ligado, 16 pasos después (en patrones de más de 16 pasos), así que el arpegio de un acorde mantenido no se para en el paso 16. Vale para toda nota de Synth 1 / 2 y MIDI 1 / 2, con arpegiador o sin él.
- Se guarda con el proyecto, por pista y patrón.

### Arpegiador de los drums {B}
Los mismos gestos (**Shift + pad 25 / 27-32 / 17-24**) en el Pattern Settings de un drum encienden su arpegiador para el patrón que suena, con su orden y su resolución. En la **vista Preset del drum**, el primer sample mantenido es el de siempre; **al mantener otro a la vez empieza el arpegio de los samples mantenidos**: el drum va saltando de sample en sample (en el orden elegido, sobre los samples ordenados por número), con la velocity de su pad. En marcha va a la rejilla del drum; parado, al tempo del proyecto. Sigue mientras quede alguno mantenido; al soltarlos todos, el drum vuelve a su sample elegido. **Con Record** (en marcha) cada golpe se graba en el patrón: su micropaso, su sample como sample flip del paso (uno por paso: queda el último) y, en un paso vacío, su velocity.
""", [("nudge-ordenes", 0)] if False else [])

view("micropasos", "V", "Vista Micro Step (pistas de notas)",
     "Pulsa **Gate dos veces** con una pista de notas elegida (Synth 1 / 2, MIDI 1 / 2).",
     f"""
- **Lo de stock:** pads 17-22 = los 6 micropasos del paso elegido; **pad 24 = Tie** (un toggle: enlaza las notas elegidas con el paso siguiente); pads 25-30 = las notas del paso: tocar una la elige (a ella se aplican el micropaso y el Tie) y la hace sonar.
- **Un micropaso por nota (de stock):** cada nota guarda una sola posición, así que tocar otro micropaso mueve la nota elegida; no se pueden encender dos a la vez. Para varias en el mismo paso, pon varias notas. En los drums sí se encienden varios micropasos (repeticiones).
- **Gate una vez** es la vista Gate (pads 17-32 = la duración): ahí los pads 31 / 32 son los de stock.
- **Pad 32 = gate por pulsación** {B} de la pista (verde = encendido, tenue = apagado; se guarda con el proyecto): al **introducir notas a mano** (un paso mantenido + un pad de nota, o una nota mantenida + un pad de paso), **el tiempo que mantienes el pad es el gate** de esa nota, al tempo del proyecto y al sync rate de la pista (de 1 micropaso a 16 pasos). Termina al soltar el primero de los dos pads. Apagado: el gate de stock.
- **Pad 31 = longitud fija** {B} de la pista (naranja = encendida): con los dos apagados, abre el **selector** (pads 17-32 = 1 … 16 pasos, como la vista Gate) y **elegir una longitud la enciende** (y cierra el selector). Con ella, toda nota introducida a mano (no la grabada en vivo) lleva ese gate, también todas las de un acorde y sueltes antes el paso o la nota (desde RC2.08: antes solo si se soltaba primero la nota).
- **Los dos toggles** {B}: con uno encendido, **pulsarlo otra vez lo apaga** (sin abrir nada); **pulsar el otro** apaga el primero y enciende el nuevo (el pad 31, abriendo su selector).
- Esos gates los usa también el arpegiador: cada nota del acorde dura el suyo.
""")

view("probabilidad", "V", "Vista de probabilidad (pistas de notas y drums)",
     "**Shift + Pattern Settings** (modo de stock), **Pattern Settings dos veces** (modo 1) o el **pad 25** de Pattern Settings (modo 2). Mantén un paso con notas y toca un pad de las filas 3-4.",
     f"""
| Modo | Fila 3 | Fila 4 |
|---|---|---|
| Stock (Shift + Pattern Settings) | Probabilidad del paso | **Random-mutate** {B} |
| Modo 1 (Pattern Settings dos veces) | Probabilidad del paso | **Frecuencia**: el paso suena en la última de cada n vueltas (1-8), amarillo {B} |
| Modo 2 (pad 25) | **Dinámicas** aleatorias {B} | Random-mutate {B} |

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

### En los drums {B}
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
""", [("random-mutate", 0)])

view("patterns", "V", "Vista Patterns y cadenas de patrones",
     "Botón **Patterns**. Columnas = pistas, filas = patrones. Con el **modo cadena** {B}, cada patrón puede llevar una regla «suena n veces, salta a B; la vez siguiente, a C».".replace("{B}", B),
     """
| Gesto | Qué hace |
|---|---|
| **Shift + Octave ▲** | Activa el modo cadena de todo el proyecto (Octave ▲ verde). Con Shift, el Octave útil se ve en amarillo. |
| **Shift + Octave ▼** | Lo desactiva (las reglas quedan guardadas pero no se aplican). |
| En el modo: **patrón** | **A** (amarillo); A otra vez = una repetición más (hasta 8, los LEDs de los knobs las cuentan). |
| En el modo: **otro patrón de la pista** | **B** (verde); el siguiente = **C** (rojo). |
| **Clear + patrón** | En el modo: quita la regla (sin regla, borra el patrón). Fuera: borra el patrón, su regla y su orden. |

- Ejemplos: n = 3 → A A A B A A A C; sin C → A A A B; n = 1 → A B A C. B y C suenan una vez y la pista vuelve a A (salvo que tengan regla).
- Las reglas viajan con el patrón (al duplicarlo); el modo, con el proyecto y con cada escena (9.2).
""")

# ===================================================================================================== VI
view("mixer", "VI", "Vista Mixer y escenas",
     "Botón **Mixer**: niveles (Octave ▲) y panorama (Octave ▼) como siempre; **Mixer otra vez** = Master FX.",
     f"""
| Gesto | Qué hace |
|---|---|
| **Shift + knob a la derecha / izquierda** | Nivel de esa pista a 100 / a 0 (página de niveles; en la de panorama, {B}: el modo cue). Sale por MIDI y se graba como un giro. |
| **Página de panorama: Shift + knob a la derecha / izquierda** {B} | **Modo cue** encendido / apagado (Octave ▼ rosa / blanco; se guarda en el aparato). |
| **Modo cue: un knob de panorama** {B} | El envío de esa pista al **cue** (salida derecha), del centro a la derecha (a la izquierda nada); Clear + knob = sin cue. Los knobs en rosa, más brillantes cuanto más envío. |
| **Pads de escena** | Como siempre; una escena guardada con el **modo cadena** se ve en **melocotón** y al cargarla vuelve el modo; una normal lo desactiva. {B} |
| **Shift + pads 1-8** {B} | **Silenciar / activar esa pista en el compás siguiente**: el pad parpadea mientras espera; otra vez lo cancela. Parado, al momento. |
| **Shift + pads 9-16** | **Repeticiones** de la escena actual (1-8; con Shift la fila en amarillo, la elegida en verde). {B} Sonando, con Shift, **la repetición que suena en blanco** (pad 9 = la primera vez; en la última, el pad verde parpadea blanco / verde). {XB} |
| Pistas que parpadean | Están siguiendo una regla de cadena. {B} |
| **Mixer** otra vez | Master FX. |

- Una escena termina cuando termina su cadena más larga. Guardar otra vez una escena no cambia sus repeticiones.
- **Modo cue** {B}: la **salida izquierda** lleva la mezcla en mono como siempre y la **derecha** solo las pistas en cue, cada una a su envío. Una pista silenciada en cue suena solo por la derecha, en el paso en que va su patrón; su pad sigue tenue y su pad (o Shift + pad, al compás siguiente) la mete o la saca de la mezcla. Los paneos no se tocan y vuelven al apagar el modo; guardar el proyecto guarda los mutes de la mezcla. La reverb, el delay y Master FX son los de la mezcla: el cue también los oye.
""", [("mixer-shift", 0)])

view("master-fx", "VI", "Master FX",
     "**Mixer** y **Mixer** otra vez. Efectos sobre la salida master, el song pointer, el sample capturado y la fila de efectos asignables. Cualquier otro botón de vista sale.",
     f"""
### Pads
| Pad | Función | K1-K4 al pulsarlo |
|---|---|---|
| 1 | Gater | división, profundidad, ancho, suavizado |
| 2 / 3 | Auto-Filter paso bajo / alto | velocidad (bipolar {XB}: derecha libre, izquierda a tempo), profundidad, resonancia, centro |
| 4 | Digitise | muestreo, bits; **K3 = envío momentáneo al delay** mientras mantienes el pad, **K4 = envolvente de la cantidad** {B} |
| 5 | Phaser | velocidad (bipolar {XB}: derecha libre, izquierda a tempo), profundidad, realimentación, mezcla |
| 6 | **Glitch** {B} (en RC0.9, el Vinyl) | Glitch: velocidad, repetición, retraso, caos / sobrecarga |
| 7 | **Sample capturado**: tocar | pitch, modo (one-shot / gate / loop), start, end |
| 8 | Apagar todo lo fijado (efectos, song pointer, sample) y bypass | — |
| 9-24 | **Song pointer**: pasos 1-16 | — |
| 25 | (stock) | — |
| 26-30 | **Huecos asignables** | los del efecto asignado |
| 31 | **Gesto mecánico** {B} (en RC0.9, el Glitch) | gesto: movimientos, tipo, tiempo de parada, tiempo de arranque |
| 32 | **Grabar** la captura | — |

### Efectos (pads 1-6)
- **Mantener** = activo; **Shift + pad** = fijado; tocarlo otra vez lo suelta. El brillo de los LEDs de los knobs enseña el valor.
- **Clear + knob a la derecha** = valor por defecto; con Clear pulsado los knobs que están en su valor por defecto se ven lavanda (Master FX no tiene automatización: no hay rojo).
- **Por sesión** {B}: los 20 knobs de los efectos, la asignación de los huecos y el compresor se guardan con cada proyecto.

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
- **Gesto mecánico** {B}: al pulsar el audio se frena hasta parar; al soltar arranca. K1 movimientos (1-8), K2 tipo continuo en colores (parada de cinta → baby scratch → tear → back spin → rattle), K3 tiempo de parada, K4 de arranque. Usa el mismo motor que el Glitch: mientras suena, el Glitch espera.
""", [("master-fx-acceso", 0), ("sample", 0), ("song-pointer", 0)])

view("vista-fx", "VI", "Vista FX",
     "Botón **FX**: envíos a reverb y delay por pista, como siempre, más:",
     """
| Gesto | Qué hace |
|---|---|
| **Octave ▲ / ▼** | Los knobs = envíos de delay / de reverb. |
| **Shift + knob** | Parámetros globales: reverb K1 tipo, K2 decay, K3 damping; delay K1 time, K2 sync, K3 feedback, K4 width, K5 ratio, K6 slew. Se guardan con el proyecto. |
| **Duplicate** | Reset: envíos a 0, filtro master al centro, Master FX apagado. |
| **Shift + Octave ▲ / ▼** *(solo Beta 3.22)* | Resonancia del filtro master +16 / −16; se para en 127 / 0 (con Shift, Octave en amarillo). En RC2.09: **1-16 / 17-32** (LED verde). |
| **Shift + pad 25** *(solo Beta 3.22)* | Filtro master apagado / encendido: apagado, suena como con el filtro al centro aunque muevas su knob (el knob sigue cambiando su posición); otra vez, el filtro vuelve en la posición actual del knob. Apagado, el LED del knob del filtro se ve rojo; con Shift, el pad 25 en amarillo (rojo si está apagado). Sin Shift, el pad 25 es el de stock. |
| Fila inferior | La misma que en Master FX: huecos (26-30), gesto mecánico (31), grabar (32). |

- Si en Setup los retornos van por las tiras 3 / 4, sus envíos tienen tope a la mitad.
""", [("vista-fx", 0)])

view("sidechain", "VI", "Vista Sidechain",
     "**Shift + FX**. Los presets de sidechain de cada pista como siempre, más los knobs:",
     f"""
| Control | Qué hace |
|---|---|
| **K1-K4** {B} | Ataque, hold, decay y profundidad del sidechain de la pista del último preset tocado (Synth 1 si ninguno); LEDs del color de la pista. |
| **K7 / K8** {B} | Ataque / release del compresor master (el que se activa en Advanced Setup), en blanco. Se guardan con el proyecto. |
| **Pads 1-4 de la fila 1** {B} | **Synth 1, Synth 2, MIDI 1, MIDI 2 como fuente** del sidechain de la pista elegida (la del último preset tocado), junto a los drums 1-4 de los pads 5-8: cada nota del **patrón** de esa pista dispara la envolvente, como un golpe de drum (las notas tocadas en directo no). La elegida, en el color de la pista; las demás, tenues. Un pad 5-8 vuelve a un drum. Se guarda con el proyecto. |
| **Octave ▼** con los drums | **Sidechain entre drums**: páginas de ducking por drum (filas 3-4) y qué drum dispara (fila 1, pads 5-8). |
| **Pads 1-4 de la fila 1** en una página de drums {B} | **Synth 1, Synth 2, MIDI 1, MIDI 2 como disparo** del drum del último preset tocado: cada nota del **patrón** de esa pista abre su envolvente (las notas tocadas en directo no). La elegida, en el color del drum; las demás, tenues. Un pad 5-8 vuelve a un drum. Como los presets del sidechain entre drums, no se guarda. |
| **K1-K4** en una página de drums {B} | Ataque, hold, decay y profundidad del sidechain del drum del último preset tocado (empiezan en los de su preset; tocar un preset los vuelve a él); LEDs del color del drum. Se guardan con el proyecto. |
""")

# ===================================================================================================== VII
view("projects", "VII", "Vista Projects",
     "Botón **Projects**: cargar y guardar proyectos como siempre, más copiar.",
     f"""
- **Duplicate + pad A** (un proyecto) = la fuente (amarillo, parpadea); Duplicate + A otra vez la olvida.
- **Duplicate + pad B** = copia. B vacío: se escribe al momento; B ocupado: parpadea en blanco y hay que repetir Duplicate + B antes de ~5 s. Nunca el proyecto cargado. {B}
- **A otro pack:** elige la fuente, carga el otro pack, vuelve a Projects y Duplicate + B.
- Se copia el proyecto guardado en la tarjeta; mientras copia el aparato no responde unos instantes. En otro pack suena con sus patches y samples *(escribe en la tarjeta)*.
""", [("copiar-proyectos", 0)])

view("packs", "VII", "Vista de packs",
     "**Shift + Projects**. Cargar packs como siempre, más borrar.",
     """
1. Toca **Clear** (sin Shift): durante ~5 s parpadean los packs que se pueden borrar (nunca el cargado). Clear se ve blanco fijo en esta vista.
2. Toca el pack: solo ese parpadea; no se carga.
3. **Clear** otra vez antes de 5 s: borrado. El hueco se reutiliza tras reiniciar.

- **El pack de la memoria interna** (el primero) es de solo lectura para el mod: no se borra, y no se escribe en él nada del mod (copias, patches, capturas); el LED de Save se pone rojo 1,5 s. Sí se puede leer y copiar desde él a un pack de la tarjeta *(escribe en la tarjeta)*.
""")

view("setup", "VII", "Vista Setup",
     "Ábrela como en el original. Canales MIDI y opciones del aparato como siempre, más:",
     f"""
| Control | Qué hace |
|---|---|
| Botones de pista + pads 1-15 | Canal de cada pista; MIDI 1 / 2 pueden usar un canal que ya tenga otra (lo que mandan les llega por dentro: **loopback interno**). Synth 1 / 2 se eligen también si entraste desde su vista. |
| **Pad 16** | Canal 16 (proyecto y FX): recepción y envío de lo que no es Program Change. |
| **Pad 22 / 23** | El retorno de reverb pasa por la tira 3 / el de delay por la tira 4 del mixer (crema / melocotón). |
| **Pad 29 (PGM Rx)** {B} | Primer toque: los pads 1-16 enseñan el **canal de escucha** de los Program Change del proyecto (blanco); un pad lo elige; otra vez = encender / apagar. |
| **Pad 30 (PGM Tx)** {B} | Lo mismo con el **canal de salida**. Por defecto los dos son el 16. Lo recibido en el de escucha se reenvía por el de salida. |
| **Record** {B} | Amarillo = lo que una pista MIDI manda a un sinte por el canal compartido se graba también en ese sinte (cambios de escala u octava en tiempo real). Apagado por defecto; se apaga al reiniciar. {XB}: en amarillo, nada se graba en una pista de notas silenciada en el Mixer: sus pasos suenan y se graban solo en el sinte del canal compartido (un banco de acordes). |
| **K4** {XB} | Modo **General MIDI** de los drums: a la derecha encendido (verde), a la izquierda apagado (tenue): **apagarlo cierra el número** y los drums vuelven a salir como en stock. Encendido, cada golpe de Drum 1-4 sale por MIDI con **su nota GM** en lugar de la de stock (60 / 62 / 64 / 65), por el canal de drums (el 10 de fábrica, el que elijas aquí). Dentro del aparato suena igual. |
| **K5-K8** {XB} | Con el modo encendido, la nota GM de Drum 1-4 (los knobs sobre las pistas de drums; apagado no hacen nada): 35-81, dos clics por nota; de fábrica 36 bombo, 38 caja, 42 charles cerrado, 46 charles abierto. **Cada nota nueva suena** una vez por el canal de drums y **su número se ve en los pads**, en el color del drum; **Shift** o salir de Setup lo confirma (se guarda en los ajustes) y vuelven los pads de Setup. Mientras se ve el número, los pads de Setup no hacen nada. Luces: el color de cada drum, más brillante cuanto más alta la nota (apagadas con el modo apagado). |

- El patch flip sale siempre por el canal de su pista MIDI.
""", [("setup", 0)])

view("advanced-setup", "VII", "Vista Advanced Setup",
     "Ábrela como en el original. Además de sus ajustes de stock (compresor master, etc.):",
     f"""
- **Duplicate** = modo del jack MIDI Thru {B}: Thru (rojo tenue, el DIN In por hardware) → Out 2 (verde) → **Merge** (amarillo: el DIN In + el MIDI del aparato) → **Filter** (azul: el DIN In sin los canales en los que escucha el aparato). Sin SysEx en Merge / Filter. Se guarda en los ajustes.
- Los pads 22 / 23 no se iluminan aquí (allí no hacen nada).
- **Pad 23 = fusión USB** {XB}: lo que entra por el **DIN In** (un teclado conectado con cable MIDI) sale también por **USB** hacia el ordenador, junto al MIDI del propio aparato. Verde encendida, tenue apagada; se guarda en los ajustes. Con Clock Tx encendido no se copian el reloj ni el transporte del DIN In (el ordenador recibiría dos relojes); el SysEx no se copia; lo que entra por USB no se reenvía.
- El ataque / release del compresor master se ajustan en la vista Sidechain, K7 / K8.
""")

# ===================================================================================================== VIII
view("guardado", "VIII", "Qué se guarda y dónde",
     "Proyecto, patrón, pack o ajustes del aparato.",
     f"""
| Qué | Dónde |
|---|---|
| Knobs nuevos de drums (incluidos ataque, inicio y corte), fuente de los sintes, reverb / delay, huecos y knobs de Master FX, compresor, modo cadena y escenas, cuenta atrás, arpegiador (con su resolución), escala propia, gate por pulsación, gate retrigger y forma del LFO del sinte propio {B} | El proyecto |
| Notas del step-drummer, valores del secuenciador de efectos, random-mutate, frecuencia, dinámicas, reglas de cadena, orden de reproducción, sample flips del modo muestra {B} | El patrón |
| Patches de sinte guardados, patches del sinte propio (con su matriz de modulación {NB}), capturas usadas como samples | El pack *(escribe en la tarjeta)* |
| Motor de las pistas MIDI (estado y valores; {B}: también OSC 2, los knobs con Shift del granular y del oscilador y los pads 28 / 29), modo de MIDI Thru, canales de PGM, {XB} el modo GM de los drums y sus notas | Ajustes del aparato |
| {XB} **El sinte propio de MIDI 1 / 2 entero** (motor, valores, matriz, página 4, FM): al guardar el proyecto va con él y vuelve al cargarlo (un proyecto de antes no lo lleva: el sonido se queda como estaba) | El proyecto (en los patrones 1-5 de MIDI 1 / 2, sin cambiar lo que suenan) |
| Efectos fijados, song pointer, toggle de Record del Setup, presets y disparos del sidechain entre drums, la matriz de modulación fuera de un patch {NB} (se apaga al apagar el aparato; {XB} va con el proyecto) | No se guardan |
""")

view("midi", "VIII", "MIDI de las funciones nuevas",
     "Todo lo nuevo sale y entra por CC / NRPN, respetando los filtros CC Tx / Rx del Setup.",
     """
- **Motor de las pistas MIDI** (canal de la pista): Filtro CC 74, Resonancia 71, Env → filtro 79, Ataque 73, Decay 75, Sustain 70, Release 72, Efecto 91, Gain 59, TUNE 26, FINE 27, WAVE 20, SHAPE 21, TUNE 2 37, FINE 2 39, WAVE 2 30, SHAPE 2 31, MIX 52, RING 54, velocidad del LFO NRPN 0:76; el resto NRPN MSB 4 con LSB = código.
- **Drums** (canal de drums): NRPN MSB 5-8 = Drum 1-4; LSB 1 env. de tono, 2 ring (frecuencia), 3 LFO, 4 velocidad LFO, 5 env → corte, 6 resonancia, 7 forma de la envolvente, 8 ring (cantidad), 9 modo de filtro, 10 inicio, 11 bitcrush, 12 tipo de distorsión, 13 corte, 14 ataque. {XB}: con el modo GM (Setup, K4) las notas de Drum 1-4 salen con las notas GM elegidas (K5-K8).
- **Master FX** (canal 16): NRPN MSB 9, LSB = 4 × efecto + knob.
- Tablas completas: la referencia MIDI (`docs/MIDI.md`).
""")

view("instalar", "VIII", "Instalar y volver atrás",
     "`tools/rc_uploader.html` parchea el firmware oficial en el navegador y lo envía por Web MIDI.",
     """
1. Descarga el firmware oficial 1.2.1 de Novation, abre `tools/rc_uploader.html` en Chrome y conecta el Circuit Tracks por USB.
2. Elige la versión (RC2.09, la más segura RC2.09S, la Beta 3.22 con las funciones nuevas sin probar, o una anterior) y envía. El bootloader de Novation no se toca.
3. **Haz antes una copia de la tarjeta.** Con las versiones que no acaban en «S», no uses la memoria interna para proyectos.
- **Volver atrás:** envía otra versión o el firmware oficial. Si no arranca: **Scales + Preset + Note** al encender.
""")


# ---------------------------------------------------------------------------------------------------- what each view offers, in user terms
# (the user, 2026-10-16: «Make the sections manual (the one with chapters per view) extended, with concise user-level descriptions of the features»)
ABOUT = dict(
    botones=f"""
- **Volver un knob a su valor o borrar lo grabado** — Clear + knob, sin buscar el valor a mano ni borrar el patrón entero.
- **Metrónomo y cuenta atrás** {B} — un compás de clics antes de grabar, para entrar a tiempo.
- **Teclado partido** {B} — los dos sintes a la vez, uno con cada mano.
- **Escala propia** {B} — escalas que el aparato no trae, también con periodos que no son la octava.
- **Atajos en amarillo** — con Shift pulsado, la vista enseña lo que ofrece.
""",
    **{"synth-nota": f"""
- **Vista de la fuente** — el sinte puede procesar una entrada de audio en lugar de su ruido.
- **Teclado partido** {B} — arriba un sinte y abajo el otro, cada uno con su escala, octava y velocity; {NB} con cualquier par de pistas de notas.
"""},
    escalas=f"""
- **Escala propia** {B} — hasta 7 notas sobre la tónica y un periodo libre (por ejemplo, una escala que se repite cada 7 semitonos). La usan los pads de las pistas de notas, el cuantizado y el random-mutate; se guarda con el proyecto.
""",
    **{"synth-fuente": f"""
- **Fuente del ruido** — cambia el ruido del patch por la entrada de audio 1 o 2 (normal o invertida): el filtro, las envolventes y los efectos del sinte procesan tu señal externa al ritmo de las notas.
- **Destinos de los macros** {B} — decide qué mueve cada macro knob (hasta 4 destinos por macro, con su tramo y su profundidad) sin pasar por Components.
- **Step-drummer del sinte** — secuencia los macros por pares de pasos: cada knob fija la posición de un macro en dos pasos del patrón.
""",
       "synth-preset": f"""
- **El modo de voz a la vista** {B} — los patches mono, mono con glide y poly se distinguen por el color.
- **Guardar el patch** {B} — guarda en el pack el sonido tal como lo has dejado (el original solo guarda patches desde Components).
- **Intercambiar y copiar** — reordena los patches del pack o lleva uno a otro pack.
""",
       "midi-preset": f"""
- **Un sinte en cada pista MIDI** — MIDI 1 y 2 suenan en el propio aparato con su motor (entrada de línea procesada, oscilador, VA-drum o granular) y siguen mandando MIDI.
- **Secuenciador de efectos** — un motor que no suena: dispara efectos de Master FX en los pasos que elijas.
- **Patches del sinte propio** {B} — 64 sonidos por pack para esos motores, a un toque.
- **Matriz de modulación** {NB} — ocho fuentes (velocity, nota, azar, LFO 2, envolvente 2, golpe de un drum, posición del patrón, azar por pasos) que mueven cualquier parámetro del motor.
- **Patch flip** — cada nota manda un cambio de programa: el aparato externo cambia de sonido paso a paso.
- **Editor de CC** — cambia qué CC manda cada knob de la plantilla sin Components.
""",
       "midi-knobs": """
- **VCA-VCF** — volumen y filtro con su envolvente y su LFO; con Shift, el tipo de filtro y el tipo de efecto.
- **Osciladores** — una forma de onda continua de seno a cuadrada y un segundo oscilador con FM, ring y sync.
- **Granular** — convierte un sample en texturas: granos que lo leen en otra posición, velocidad o dirección para congelarlo, estirarlo o trocearlo.
- **Página 4** — los 8 parámetros que se graban como automatización ({XB}: con Shift + knob, cualquiera de los 33; Record + paso = foto de los valores).
""",
       "midi-cc": """
- **Controlar otro aparato** — elige el número de CC (o NRPN) y el recorrido de cada knob de la plantilla, y guárdalo en ella.
""",
       "step-drummer": f"""
- **Parámetros por pares de pasos** — los 8 knobs son 8 pares de pasos del patrón: cada uno mueve un destino (tono, forma, FM, filtro…) solo en esos pasos, para melodías, acentos o cambios de timbre sin automatizar a mano.
- **El LED dice cuánto** {B} — tenue sin modulación, más brillante cuanto más se aleja.
- **Segunda página con destino propio** {B} — la página de velocity mueve otro destino a la vez.
- **Toggle pitch-vel** {B} — la página 1 transpone las notas por grados de la escala y la 2 marca su velocity: una melodía a partir de un solo patrón de notas.
- **En tiempo real** — con Record, tocar un paso lo graba.
- **Secuenciador de efectos** — con ese motor, cada par elige qué hueco de Master FX suena.
""",
       "midi-muestra": f"""
- **Drums con altura en una pista MIDI** — cualquier sample del pack suena a la altura de cada nota, como en una caja de ritmos con samples afinables.
- **Un sample distinto por paso** — el sample flip cambia de sample paso a paso sin otra pista; se graba también en vivo.
""",
       "drum-pista": f"""
- **Moldear cada drum** — tono exacto, ring mod, ataque y decay, inicio y corte del sample, filtro con varios modos, LFO y distorsión de varios tipos: de un sample salen muchos sonidos.
- **Todo neutro = el original** — con los knobs nuevos en su punto neutro, el sample suena como en el Circuit original.
- **Volver a empezar** {B} — Clear + el botón del drum deja todos sus knobs por defecto.
""",
       "drum-preset": f"""
- **La captura como drum** — graba lo que suena (Master FX) y úsalo como sample de un drum; al guardar el proyecto queda en el pack.
- **Intercambiar y copiar samples** — reordena los samples o trae uno de otro pack.
- **Arpegio de samples** {B} — al mantener varios samples, el drum salta de uno a otro.
""",
       "drum-cromatica": f"""
- **Un drum como teclado** — el sample transpuesto en la escala del proyecto.
- **Rollers** {B} — repite el drum en los micropasos que mantengas: redobles y ratchets en directo, también parado, y grabados con Record.
"""},
    **{"pattern-settings": f"""
- **Nudge** — rota el patrón para que empiece en otro paso.
- **Órdenes fractal y deconstruido** — recorren el patrón de otra forma sin cambiar sus notas.
- **Arpegiador** {B} — los acordes del patrón (y los que tocas) suenan nota a nota, con su orden y su resolución; en los drums, saltando de sample.
- **Dinámicas y random-mutate** (pad 25) — variaciones para que el patrón no suene siempre igual.
"""},
    micropasos=f"""
- **Micropasos y Tie (de stock)** — coloca cada nota fuera de la rejilla y enlázala con el paso siguiente.
- **Gate por pulsación** {B} — al introducir notas a mano, lo que mantienes es lo que dura la nota.
- **Longitud fija** {B} — todas las notas que introduces a mano con la misma duración.
""",
    probabilidad=f"""
- **Probabilidad (de stock)** — que un paso suene solo a veces.
- **Frecuencia** {B} — que un paso suene una de cada n vueltas: variaciones que vuelven cada 2, 4 u 8 vueltas.
- **Dinámicas** {B} — pequeñas variaciones de velocity y de posición: un patrón más humano.
- **Random-mutate** {B} — notas que saltan de octava o a otra nota de la escala; en los drums, a otro sample.
""",
    patterns=f"""
- **Cadenas de patrones** {B} — un patrón suena n veces y salta a otro, y la vez siguiente a un tercero: estructuras A A A B sin encadenar a mano.
""",
    mixer=f"""
- **Nivel a 100 o a 0** — Shift + knob deja una pista a su nivel nominal o en silencio de un gesto.
- **Escenas con cadenas y repeticiones** {B} — una escena puede repetirse n veces y recordar el modo cadena.
- **Entradas y salidas al compás** {B} — Shift + pad de pista silencia o activa la pista justo al empezar el compás siguiente.
- **Modo cue** {B} — la mezcla en mono por la izquierda y, por la derecha, las pistas que quieras escuchar antes de meterlas.
""",
    **{"master-fx": f"""
- **Efectos en directo sobre todo el master** — Gater, Auto-Filter, Digitise, Phaser, Glitch y gesto mecánico {B}: mientras mantienes o fijados.
- **Song pointer** — repite o hace bucle de partes del patrón en directo.
- **Captura** — graba hasta 3,5 s de lo que suena para tocarlo, ponerlo en un hueco o usarlo como drum.
- **Huecos** — un efecto con sus ajustes a un toque; el secuenciador de efectos los dispara.
- **Por proyecto** {B} — cada proyecto recuerda sus ajustes de Master FX.
""",
       "vista-fx": """
- **La reverb y el delay desde el aparato** — tipo, decay, tiempo, feedback…, guardados con el proyecto.
- **Reset rápido** — Duplicate deja los envíos y los efectos a cero.
- **Resonancia del filtro master** — en Shift + Octave ▲ / ▼, de 16 en 16 *(solo Beta 3.22; en RC2.09, 1-16 / 17-32)*.
- **Filtro master apagado / encendido** — Shift + pad 25, sin perder su posición *(solo Beta 3.22)*.
"""},
    sidechain=f"""
- **El sidechain con knobs** {B} — ataque, hold, decay y profundidad del ducking de cada pista, más allá de los presets.
- **Compresor master** {B} — su ataque y su release.
- **Sidechain entre drums** — que un drum baje el volumen de otro (el bombo al bajo, por ejemplo).
- **Disparado por patrones** {B} — Synth 1 / 2 o MIDI 1 / 2 como fuente: las notas de su patrón agachan otra pista, no solo los drums.
""",
    projects=f"""
- **Copiar proyectos** {B} — duplica un proyecto en otro hueco o en otro pack.
""",
    packs="""
- **Borrar packs** — libera huecos de pack desde el aparato.
- **Memoria interna protegida** — el mod nunca escribe en el pack interno.
""",
    setup=f"""
- **Canales compartidos (loopback interno)** — una pista MIDI toca un sinte o los drums del propio aparato.
- **Retornos por las tiras 3 / 4** — la reverb y el delay como canales del mixer.
- **Canales de Program Change** {B} — escucha y manda cambios de programa por canales propios.
- **Grabar los ruteos internos** {B} — lo que la pista MIDI toca en un sinte se graba también en él; {XB} una pista silenciada en el Mixer no se graba (banco de acordes).
""",
    **{"advanced-setup": f"""
- **MIDI Thru, Merge y Filter** {B} — el jack Thru puede mezclar el MIDI de entrada con el del aparato o filtrarlo.
"""},
)


for _v in V: _v["part"] = PART_OF[_v["id"]]
assert {v["id"] for v in V} == set(PART_OF)
assert set(ABOUT) <= set(PART_OF)


# ---------------------------------------------------------------------------------------------------- output
UI = dict(es=dict(title="Guía por vistas — CIRCUIT-HACKS ({v})", cover="Guía de uso por vistas", how="Cómo se llega:", about="En esta vista", toc="Vistas",
                  intro="Circuit Tracks con el firmware oficial 1.2.1 (build 4486) parcheado. Esta guía recorre las vistas del aparato y explica todo lo que se puede hacer en cada una. "
                        "La [lista de características](MANUAL.md) resume cada función por temas.",
                  other='<p class="lang"><a href="guide.html">English version</a> · <a href="index.html">Lista de características</a> · <a href="midi.html">Referencia MIDI</a></p>',
                  md="docs/GUIA.md", html="guia.html", lang="es", list_link="MANUAL.md"),
          en=None)


def figures(lang):
    """(old section id, index) -> the figure dict in that language"""
    M.use(lang)
    return {s_["id"]: s_["figs"] for s_ in M.CUR["S"]}


def marks(s, b, nb, xb):
    """the version marks left as {B} / {NB} / {XB} in texts that are not f-strings"""
    return s.replace("{XB}", xb).replace("{NB}", nb).replace("{B}", b)


def data(lang):
    if lang == "es":
        m = lambda s: marks(s, B, NB, XB)
        return [dict(v, how=m(v["how"]), detail=m(v["detail"]), about=m(ABOUT.get(v["id"], "").strip("\n"))) for v in V], PARTS, UI["es"]
    import guide_en as EN
    m = lambda s: marks(s, EN.B, EN.NB, EN.XB)
    out = []
    for v in V:
        title, how, detail = EN.VIEWS[v["id"]]
        out.append(dict(v, title=title, how=m(how), detail=m(detail.strip("\n")), about=m(EN.ABOUT.get(v["id"], "").strip("\n"))))
    assert set(EN.VIEWS) == {v["id"] for v in V} and set(EN.ABOUT) == set(ABOUT)
    return out, EN.PARTS, EN.UI


def numbered(views, parts):
    out = []
    for p, _ in parts:
        n = 0
        for v in views:
            if v["part"] == p:
                n += 1; out.append((f"{p}.{n}", v))
    return out


def write(lang):
    views, parts, U = data(lang)
    figs = figures(lang)
    num = numbered(views, parts)
    # markdown
    out = [f"# {U['title'].format(v=M.VERSION)}", "", U["intro"], "", f"## {U['toc']}", ""]
    for p, pname in parts:
        out.append(f"**{p}. {pname}**"); out.append("")
        for code, v in num:
            if v["part"] == p: out.append(f"- [{code} {v['title']}](#{v['id']})")
        out.append("")
    for p, pname in parts:
        out.append(f"## {p}. {pname}"); out.append("")
        for code, v in num:
            if v["part"] != p: continue
            out += [f'<a id="{v["id"]}"></a>', f"### {code} {v['title']}", "", f"*{U['how']}* {v['how']}", ""]
            if v["about"]: out += [f"**{U['about']}**", "", v["about"], ""]
            out += [v["detail"], ""]
    (ROOT / U["md"]).write_text("\n".join(out), encoding="utf-8", newline="")
    # html
    parts_h = [f'<!doctype html><html lang="{U["lang"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(U["title"].format(v=M.VERSION))}</title>',
               f"<style>{M.CSS}</style></head><body>",
               f'<header class="cover"><h1>CIRCUIT-HACKS</h1><p>{U["cover"]}</p><p>{M.VERSION}</p><div class="bar"></div></header><main>',
               U["other"], f'<p>{M.inline(U["intro"].split("[")[0])}</p>', f'<nav class="toc"><h2>{U["toc"]}</h2>']
    for p, pname in parts:
        parts_h.append(f"<h3>{p}. {html.escape(pname)}</h3><ol>")
        for code, v in num:
            if v["part"] == p: parts_h.append(f'<li><a href="#{v["id"]}">{code} {html.escape(v["title"])}</a></li>')
        parts_h.append("</ol>")
    parts_h.append("</nav>")
    for p, pname in parts:
        parts_h.append(f'<h2 class="group">{p}. {html.escape(pname)}</h2>')
        for code, v in num:
            if v["part"] != p: continue
            parts_h.append(f'<section class="feat" id="{v["id"]}"><h3><span class="code">{code}</span>{html.escape(v["title"])}</h3>')
            about = f'<p class="about-h"><strong>{html.escape(U["about"])}</strong></p>{M.md2html(v["about"])}' if v["about"] else ""
            parts_h.append(f'<div class="summary"><p><strong>{html.escape(U["how"])}</strong> {M.inline(v["how"])}</p>{about}</div>')
            for sid, k in v["figs"]:
                f = figs[sid][k]
                parts_h.append(f"<figure>{M.svg(f)}<figcaption>{html.escape(f['caption'])}</figcaption></figure>")
            parts_h.append(M.md2html(v["detail"]))
            parts_h.append("</section>")
    parts_h.append(f"<footer>{M.CUR['UI']['footer'].format(v=M.VERSION)}</footer></main></body></html>")
    (ROOT / "docs/manual" / U["html"]).write_text("\n".join(parts_h), encoding="utf-8", newline="")
    return len(views)


if __name__ == "__main__":
    n = [write(lang) for lang in ("es", "en")]
    import midi_ref
    for lang in ("es", "en"): midi_ref.write(lang, M.VERSION, M)
    print(n[0], "views, es, en; MIDI reference es, en")
