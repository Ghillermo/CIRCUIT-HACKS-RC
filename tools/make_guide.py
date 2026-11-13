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
XBETA = "RC4"                         # the newest release candidate (2026-10-28: the betas up to 3.43 went out as RC4): «desde RC4»
XB = f"*(desde {XBETA})*"
YBETA = "Beta 5.56"                    # the newest beta: «solo Beta 5.3» (3.44-3.49 never went out: 5.0 holds them;
                                      # the user: «betas that expand RC4 get 5.xx version»)
YB = f"*(solo {YBETA})*"
ZBETA = "RC4.05"                      # the newest release candidate's fixes (2026-10-29), in RC4.02 and the beta: «desde RC4.02»
ZB = f"*(desde {ZBETA})*"
PARTS = [("0", "Introducción"), ("1", "Setup"), ("2", "Sintes de stock (Synth 1 / 2)"), ("3", "Pistas MIDI (MIDI 1 / 2)"), ("4", "Pattern Settings"),
         ("5", "Drums"), ("6", "Master FX"), ("7", "FX"), ("8", "Sidechain"), ("9", "Escenas y patterns"), ("10", "Projects y packs"), ("11", "Datos: guardado, MIDI y modulación"), ("A", "Apéndice")]
# the chapters the user listed (2026-10-15): setup, sintes de stock, pistas MIDI, pattern settings, drums, Master FX, FX, sidechain, scenes y patterns, projects y packs
PART_OF = dict(convenciones="0", botones="0", setup="1", **{"advanced-setup": "1"}, **{"synth-nota": "2", "synth-fuente": "2", "synth-preset": "2"},
               **{"midi-preset": "3", "midi-voces": "3", "midi-knobs": "3", "midi-matriz": "3", "midi-fm": "3", "midi-fm8": "3", "midi-cc": "3", "step-drummer": "3", "midi-muestra": "3"}, **{"pattern-settings": "4"}, probabilidad="4", micropasos="4",
               **{"drum-pista": "5", "drum-preset": "5", "drum-cromatica": "5"}, **{"master-fx": "6", "vista-fx": "7"}, sidechain="8",
               escalas="2", patterns="9", mixer="9", projects="10", packs="10", instalar="A", **{"app-sd": "A"},
               **{"datos-patron": "11", "guardado": "11", "datos-perdido": "11", "midi": "11", "destinos": "11"})
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
- {B} = nuevo desde RC2 (no está en RC0.9 / RC0.9S). La versión más segura, RC4S (y las S anteriores), no escribe nada propio en la tarjeta: lo marcado «escribe en la tarjeta» no hace nada en ella (el LED de Save se pone rojo).
- {NB} = nuevo en RC2.02 (no está en RC2.01).
- {XB} = nuevo en **RC4** (no está en RC2.11 ni en las anteriores).
- {ZB} = arreglo de **RC4.05** (también en RC4.08 y en la Beta 5.29; en RC4.02 y antes no).
- {YB} = solo en la **Beta 5.29** (no está en RC4.08).
- La **lista de características** (el manual anterior) resume cada función en una línea, por temas.
""")

view("botones", "I", "Botones que funcionan en todas las vistas",
     "Shift, Clear, Duplicate, Save y Octave ganan funciones según la vista; aquí, las que valen en casi todas.",
     f"""
| Gesto | Dónde | Qué hace |
|---|---|---|
| **Clear + knob a la derecha** | drums, motor de las pistas MIDI, Master FX | El knob vuelve a su valor por defecto (las dos capas, con y sin Shift). LED **lavanda** = hecho, como en el original. |
| **Clear + knob a la izquierda** | drums (knobs de stock), motor de las pistas MIDI {B} | Borra la automatización de ese knob en el patrón que suena, como el original (LED **rojo**). En el motor MIDI, la de los dos carriles del knob (con y sin Shift) que tengan automatización. |
| **Shift** | todas | Con Shift pulsado, los atajos disponibles se iluminan en **amarillo**; la opción elegida, en otro color. {YB} Además, los ocho **botones de pista** (Synth 1 / 2, MIDI 1 / 2, Drum 1-4) destellan en **blanco** durante 100 ms con cada nota que toca su pista, venga del secuenciador, de los pads, del arpegiador o de MIDI. Una nota ligada es una sola nota: un destello. |
| **Save** | todas | Guarda el proyecto como siempre; además escribe en el pack los samples sustituidos por capturas (Preset de drums) si caben en la memoria de samples *(escribe en la tarjeta)*. |
| **Pulsar el botón de la pista otra vez** | Synth 1 / 2 | Abre la vista de la fuente del sinte (2.3). |
| **Clear + Synth 1 / 2** | su vista | {B} Sus ocho macros a los valores del patch cargado. |
| **Shift + Preset** | vistas de Synth 1 / 2 y de MIDI 1 / 2 (con el sinte propio encendido) | {YB} El sonido de esa pista vuelve al del proyecto: Synth 1 / 2, el patch entero tal como está guardado en el proyecto; MIDI 1 / 2, el sinte propio guardado con el proyecto (sin él, sus valores por defecto). Con Shift, Preset se ilumina en **amarillo** donde funciona. |
| **Clear + el botón de un drum** | su vista | {B} Borra la automatización de sus knobs en el patrón que suena y pone sus ocho knobs por defecto. |
| **Dos botones de pista de notas a la vez** | todas | Teclado partido {B}: Synth 1 + Synth 2; {NB} cualquier par de Synth 1, Synth 2, MIDI 1 y MIDI 2. |
| **Shift + Clear** | todas | Metrónomo en cuatro estados {B}: sin metrónomo → metrónomo → solo cuenta atrás → cuenta atrás y metrónomo. Con Shift pulsado, el LED de Clear enseña el estado: rojo (sin metrónomo) / verde (metrónomo) / magenta (solo cuenta atrás) / verde azulado (las dos). El volumen del clic es el de stock: **Tempo/Swing** y **K5**. {XB} Con el modo cue del Mixer, el clic solo en el cue (salida derecha). |
| **Play** con Record armado y la cuenta atrás | parado | Un compás de cuenta atrás (4 clics al tempo del proyecto o, como esclavo, al del reloj externo, sin alinearse con su compás; Record parpadea en rojo) y después arranca la grabación {B}. {YB} Con el volumen del clic a 0 (K5 de Tempo / Swing), Clear destella en naranja en cada clic, también con el metrónomo. Play durante la cuenta la cancela. La cuenta atrás se guarda con el proyecto. |
| **Shift + Play** | todas | {B} **Cuantiza** el patrón que suena en la pista elegida: las notas y los golpes grabados fuera de la rejilla van al paso más cercano (micropasos 1-2 → el inicio de su paso; 3-5 → el del siguiente; los del último paso, al primero). En los drums, un paso con varios golpes (un redoble) se queda. Con Shift el LED de Play se ve amarillo; verde después de cuantizar. Sustituye al Shift + Play del original (otra forma de arrancar). |
| **Shift + Scales** | todas | Editor de la escala propia {B} (2.2). {XB}: también **Scales dos veces**. |
| **Velocity dos veces** {XB} | vista Velocity | **Velocity fija** encendida / apagada, como el Shift + Velocity del original. |
| **Shift + Synth 1 / 2, Shift + MIDI 1 / 2** {XB} | todas | Lo mismo que pulsar el botón dos veces: Synth = la vista de la fuente (2.3), MIDI = su vista Preset. |
| **Mixer dos veces** | todas | Master FX (6.1). {YB} En el Mixer, **Mixer mantenido** ½ s o más = Master FX solo hasta que lo sueltas; en Master FX, mantenido = el Mixer hasta que lo sueltas. |
| **Scales + Preset + Note** al encender | — | Modo de recuperación del bootloader de Novation: permite volver a instalar cualquier firmware. |

- Los LEDs de los knobs enseñan con su **brillo** el valor de las funciones nuevas (más brillo = más valor; en los knobs bipolares, oscuro en el centro). {YB} En los knobs bipolares, **tenue en el centro**, a la derecha su color de siempre y **a la izquierda un tono más claro del mismo color**, cada vez más brillante hacia fuera (motor de MIDI 1 / 2, drums, Digitise K4, la velocidad a tempo de Auto-Filter / Phaser).
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
- **Vista Velocity, Shift + pad de paso** {XB} (Synth 1 / 2 y MIDI 1 / 2): ese paso **suelta la automatización**: ahí no suena ningún carril y los parámetros que la automatización había movido vuelven a **los valores del proyecto** *(desde RC4.01; antes, a la posición de su knob)*: en Synth 1 / 2, los macros del patch tal como está guardado en el proyecto (o como se cargó: lo que se gira después no cuenta); en MIDI 1 / 2, el sinte propio guardado con el proyecto (un proyecto sin él: sus valores por defecto). Un knob girado a mano después de la automatización se queda donde lo dejaste. Otra vez = quitarlo. Con Shift, en la vista Velocity, los pads de paso se ven amarillos y los marcados en rojo; en la página 17-32, los pasos 17-32. Se guarda con el patrón. {YB} Con Shift, los pasos **conservan su color** y solo se ven en **amarillo los que tienen automatización** (los marcados, en rojo); **Shift + un paso amarillo** no lo marca: **pone sus valores de automatización en los knobs y en el sonido** hasta soltar Shift, y al soltarlo todo vuelve a como estaba (Shift + cualquier otro paso lo marca o lo desmarca como siempre); mientras tanto, **los knobs que mueve se encienden en amarillo**, con el brillo de su valor. {YB} **Clear + paso** en la vista Velocity (con o sin Shift; Clear primero, porque Shift + Clear es el metrónomo) **borra la automatización de los knobs de ese paso** y deja sus notas, su marca y la automatización de nivel / panorama / envíos.
- **Sweep entre dos pasos** {YB} (Synth 1 / 2 y MIDI 1 / 2): en la vista Velocity con Shift, **mantén un paso amarillo y pulsa otro paso amarillo**, en cualquier orden: cada carril con valor en los dos queda en línea recta entre ellos, en los pasos de en medio (un valor por paso, el que lee la reproducción). Los dos extremos no cambian; un carril con valor en uno solo de ellos no se toca. Con un paso sin automatización como segundo no pasa nada. Es el gesto de las rampas de los drums.
- **Foto de los macros en un paso** {YB}: en la vista de pista (Note), **Record mantenido + un pad de paso** (pads 1-16; con 17-32, los pasos 17-32) escribe en ese paso los **macros que no están donde los guarda el patch cargado** (donde los devolvería Clear + Synth), cada uno en su carril. El paso no cambia sus notas y Record queda como estaba. Mixer y FX no se tocan (ya los guardan las escenas). {YB} Mientras mantienes el paso, se ve en **amarillo**.
- **Shift + tecla = latch** {XB} (Synth 1 / 2 y MIDI 1 / 2, vista Note y Note ampliada, sin un paso mantenido): la nota suena y **sigue sonando al soltar el pad**; la **siguiente pulsación de esa nota** (en cualquier pad que la tenga, con o sin Shift) la para, y esa pulsación no hace nada más. **Con Shift mantenido, las teclas de las notas fijadas se ven verde azulado brillante**; las demás teclas no cambian de color (sin Shift, la nota que suena se ve blanca como siempre). *(Hasta la Beta 3.39, con Shift las teclas se veían en amarillo y las fijadas en verde; en la Beta 3.40, sin colores.)* Con el **arpegiador** encendido, las notas fijadas siguen en el arpegio: un **latch del arpegio**. **Clear + el botón de la pista** suelta todas sus notas fijadas (y sus acordes fijados). **Shift + un paso** (vista Note, pads 1-16) con notas fijadas en la pista: **las notas fijadas se escriben en ese paso** (las que ya están no se repiten; hasta 6 por paso; un paso de largo, velocity 100); con Shift mantenido y notas fijadas, los pads de paso se ven **amarillos** (en la {YB}, no: los pasos no cambian de color y el paso en que se escribe se ve **verde azulado**, el color del latch, mientras se mantiene, hasta soltarlo); sin notas fijadas, Shift + paso es el de stock. En la pantalla de acordes, **Shift + fundamental** fija el acorde entero (abajo). No en el selector de samples (allí Shift + pad ya hace otra cosa); no se guarda.
- **Pantalla de acordes** {XB} (Synth 1 / 2 y MIDI 1 / 2, solo en la **Note ampliada**: Note dos veces): **Shift + pad 8** la enciende y la apaga (con Shift el pad 8 se ve amarillo, verde con la pantalla encendida).

| Pads | Qué hacen |
|---|---|
| Fila 1 | El tipo de acorde: mayor, menor, 7, m7, maj7, sus4, dim, aum. **Shift + pads 1-7**: sus2, 6, m6, add9, 9, 7sus4, quinta (con Shift la fila en amarillo; el elegido en blanco) |
| Pads 9-12 | La inversión: fundamental, 1.ª, 2.ª, 3.ª (azul; la misma otra vez = fundamental) |
| Pad 13 | Voicing abierto: la segunda nota una octava arriba |
| Pad 14 | La fundamental añadida una octava abajo |
| Pad 15 | Diatónico: el acorde con las terceras de la escala del proyecto (también la propia y Jankó): 3 notas, 4 si el tipo tiene 4 o más |
| Pad 16 | {YB} **Acorde inverso**: el acorde reflejado hacia abajo desde la fundamental, que suena como nota más aguda (Do mayor → Do La♭ Fa = Fa menor; Do menor → Fa mayor; Do7 → Rem7(♭5)). Las notas que caen fuera de la escala se ajustan a ella al sonar. En las RC, el pad 16 sigue siendo el latch del acorde |
| Filas 3-4 | Las fundamentales: las mismas notas que el teclado de la vista Note (escala, tónica, Octave, Jankó). Mientras mantienes el pad suena el acorde, hasta 6 notas, con la velocity del pad |

- Pads 13-16 verdes encendidos, tenues apagados.
- **Dos acordes a la vez**: las notas que comparten suenan una sola vez y siguen sonando hasta soltar el último acorde que las tiene.
- **Con el arpegiador**: el arpegio sigue aunque la pista esté silenciada en el Mixer (la secuencia de esa pista sigue callada), y guarda hasta **6 notas**: si dos acordes suman más, las que no caben no entran y no vuelven al soltar el otro.
- **El acorde cambia al momento**: si cambias el tipo, la inversión o un modificador (pads 13-16) con un acorde sonando (mantenido o fijado), suena el acorde nuevo sin volver a pulsar la fundamental: las notas que salen se apagan, las nuevas suenan y las que se quedan siguen sonando. El **arpegiador** recibe el cambio igual (su arpegio sigue con las notas nuevas).
- **Shift + fundamental = latch del acorde**: el acorde entero sigue sonando al soltar el pad, hasta **volver a pulsar esa fundamental** (que solo lo para), **Clear + el botón de la pista** o apagar la pantalla; puede haber varios fijados a la vez y cambian con el tipo y los modificadores. Con Shift, su fundamental se ve **verde azulado brillante**. En la vista Note, **Shift + paso** escribe sus notas en ese paso. El latch del pad 16 sigue como antes.
- Lo que tocas suena y se graba con Record como **notas normales del patrón**: se reproduce igual sin la pantalla de acordes. Con el **arpegiador** encendido, el acorde se arpegia con un solo dedo.
- El tipo y los modificadores de cada pista **no se guardan** (se pierden al apagar).
- En MIDI 1 / 2 con el modo muestra, la Note ampliada sigue siendo el selector de samples.
""", [("teclado-partido", 0)])

view("escalas", "II", "Vista Scales y escala propia",
     "Pulsa **Scales** como siempre (tónica y escala de stock); **Shift + Scales** para la escala propia.",
     f"""
- **Shift + Scales** abre la vista Scales con el **editor de la escala propia** {B}; con Shift pulsado, el botón Scales se ve amarillo. Scales otra vez, Shift + Scales u otra vista lo cierran. {XB}: **Scales dos veces** = Shift + Scales (con la vista Scales en pantalla, Scales abre y cierra el editor).
- **El teclado del editor** son dos octavas en piano a partir de la **tónica** (la de la vista Scales, que se elige como siempre fuera del editor): fila 4 = teclas blancas de la primera octava (tónica, +2, +4, +5, +7, +9, +11, +12), fila 3 = sus negras; filas 2 / 1 = la segunda octava (+12 … +24).
- **Pulsar una tecla** la pone o la quita (hasta **7**). La más alta pulsada es el **periodo**: la tónica de la siguiente iteración (no tiene por qué ser la octava); las demás son las notas de la escala. Colores: tónica blanca, notas verdes, periodo azul, teclas libres tenues.
- **En las pistas de notas** (Synth 1 / 2, MIDI 1 / 2) cada fila de pads es **una iteración**: sus notas y la nota del periodo al final, como las octavas de una escala de stock. Con **4 notas o menos**, **dos iteraciones por fila** (una en cada mitad). Octave ▼ / ▲ mueven una fila.
- La escala propia también vale para **iluminar las notas** de la secuencia, el cuantizado y el **random-mutate** (otra nota de la misma iteración).
- **Elegir una escala de stock** (pads 17-32 fuera del editor) apaga la escala propia; las teclas se guardan: volver al editor la enciende otra vez. Mientras está encendida, ninguna escala de stock se ve elegida.
- Se guarda **con el proyecto**; un proyecto nuevo empieza sin escala propia.
- **Jankó** {XB}: en el editor, **Shift + pad 8** (arriba a la derecha; con Shift se ve amarillo) enciende la **disposición isomórfica Jankó** (el pad 8 en verde azulado mientras está encendida): en las pistas de notas cada columna sube un **tono** y las filas van **por parejas**, como en el teclado cromático de stock: la de abajo empieza en la **tónica** de la vista Scales (con tónica C: C D E F♯ G♯ A♯ C D) y la de encima es **medio tono más grave** (B C♯ D♯ F G A B C♯). Cada tipo de acorde tiene la misma forma en cualquier tono. Los pads de la **tónica** se ven en el color de la tónica de stock. Están las 12 notas: las que suenan se iluminan en su pad y el random-mutate elige cualquiera de las 12 de su octava. **Octave ▼ / ▲: un toque = medio tono; mantenido casi medio segundo = una octava** desde donde estaba (Shift + Octave sigue transponiendo el patrón una octava). El mismo pad otra vez, una tecla del editor o una escala de stock lo apagan. Se guarda con el proyecto. En las RC, en la Note ampliada la pareja de arriba es la de abajo una octava más aguda y **Shift + pad 24** enciende la disposición anterior (cada fila un semitono más aguda que la de abajo). {YB} **Una sola disposición, Shift + pad 8:** en la Note ampliada la pareja de arriba **repite** la de abajo y el pad 24 no hace nada; un proyecto guardado con cualquiera de las anteriores abre con esta. **Cada pareja se mueve por separado:** en la Note ampliada, con una tecla mantenida, Octave mueve medio tono **solo la pareja a la que no pertenece la tecla** (mantenido casi medio segundo, una octava desde donde estaba); la tecla sigue sonando. Con teclas mantenidas en las dos parejas no se mueve nada. Sin teclas mantenidas, en la vista Note y en la pantalla de acordes, Octave mueve las dos. La distancia entre parejas no se guarda: al apagar vuelve a 0. {YB} **Teclas mantenidas en las filas 2 y 4** (al menos una en cada una, ninguna en las filas 1 / 3): Octave mueve **solo las filas 1 y 3** (la fila de arriba de cada pareja), medio tono por toque, una octava mantenido; tampoco se guarda.
""")

view("synth-fuente", "II", "Vista de la fuente del sinte",
     "Con la vista de Synth 1 / 2 en pantalla, **pulsa su botón otra vez** (*desde RC4*: o **Shift + Synth 1 / 2** desde cualquier vista). Cualquier botón la cierra.",
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
3. El knob cambia el campo actual; **Octave ▼ / ▲** = campo siguiente / anterior: ranura (1-4, amarillo) → inicio (verde) → fin (ámbar) → destino (blanco = CC; azul claro, magenta, violeta = NRPN de los bancos 0, 1, 2) → profundidad (verde azulado positiva, rojo negativa). Los pads dibujan el número.
4. Cualquier pad suelta el macro; el pad 32 apaga el editor.
- El destino recorre primero los 31 parámetros con CC (por número) y luego los 39 que solo tienen NRPN. Los cambios suenan al momento; para dejarlos en el pack, guarda el patch (vista Preset).

### Pad 30: step-drummer del sinte
La vista del step-drummer es la misma que la de las pistas MIDI ([vista del step-drummer](#step-drummer)): pads 1-16 pasos, 17-24 = **macro 1-8** como destino, K1-K8 = los 8 pares de pasos. El valor de cada par es la posición del macro, escrita como automatización; un par vacío empieza en 0 {B} (antes, en la posición actual del macro).
- {B} Play y Record no cierran el step-drummer del sinte; si vas a otra vista, **pulsar Synth 1 / 2** lo vuelve a abrir (hasta que lo cierras con el pad 30).
""", [("fuente-sinte", 0), ("destinos-macro", 0)])

view("synth-preset", "II", "Vista Preset de Synth 1 / 2",
     "Pulsa **Preset** con Synth 1 / 2 elegido. Los pads eligen patch como siempre (4 páginas, 128 patches del pack).",
     f"""
| Gesto | Qué hace |
|---|---|
| Colores de los patches | *Desde RC4.10*: los del original, los patches en el color de la pista y el elegido en blanco (de RC2 a RC4.08, el color del modo de voz: sus lecturas de la tarjeta a veces cargaban el patch inicial). |
| {YB} Colores por **categoría** | Cada patch en el color de su **categoría de Components**: Arp verde azulado, Bass azul acero, Bell azul claro, Classic ámbar, Drum naranja, Keyboard lima claro, Lead amarillo, Movement violeta, Pad azul, Poly verde, SFX rojo, String melocotón, User arena, Voc lavanda; None = el color de la pista, **hueco vacío blanco tenue**, el elegido en blanco. La tarjeta se lee al entrar en la vista, al cambiar de página o de pack y tras guardar o copiar, nunca al tocar un patch. |
| **Clear + pad**, **Clear + el mismo pad** antes de ~5 s {B} | **Guarda** en ese hueco el patch tal como suena (knobs, MIDI recibido, destinos de macro). El primer toque pregunta (parpadea en blanco); otro pad mueve la pregunta *(escribe en la tarjeta)*. |
| {YB} **K1** mientras pregunta | Elige la **categoría** que se guarda (None, Arp, Bass… Voc; 4 clics cada una; empieza en la del patch): K1 y el hueco en su color, los demás knobs apagados y sin efecto. Al confirmar se guarda con esa categoría. |
| **Duplicate + pad A + pad B** (mismo pack) | Intercambia los dos patches. |
| **Duplicate + pad A**, cargar otro pack, **Duplicate + pad B** | Copia el patch A sobre B en el otro pack (el pack de A no cambia); B puede estar vacío *(escribe en la tarjeta)*. |

- El original no puede guardar patches desde el aparato. El patch guardado conserva el nombre del que estaba cargado.
- No funciona en el pack de la memoria interna (solo lectura para el mod): el LED de Save se pone rojo.
- **Morph de patches** {YB}: en la vista Preset, **mantén de dos a cuatro patches** 0,4 s (o mantenidos + Duplicate): se abre la **vista del morph**, que pasa de uno a otro de los patches mantenidos, en el orden de los pads. Solo funcionan los knobs: **K1** = la posición en la cadena; **K2** = LFO cuadrado (cantidad); **K3** = la velocidad de los dos LFO; **K4** = LFO de pasos al azar (cantidad; un valor nuevo en cada medio ciclo); **K5** = destino del **morph lento**; **K6** = su duración (a la izquierda del todo, al momento; luego de ¼ a 32 compases del tempo del proyecto: más a la derecha, más largo); **K7 / K8** = envolvente (cantidad / tiempo); **K8** también suaviza los dos LFO (más a la derecha, cambios más lentos). Las cantidades a la derecha van hacia el final de la cadena. **Morph lento:** gira K5 y déjalo quieto medio segundo: el sonido va de K1 a K5 en el tiempo de K6 y, al llegar, K1 toma el valor de K5; girar K5 otra vez cambia el destino desde donde está el sonido; girar K1 lo para ahí. **K1 y K5 en color:** patch 1 rojo, 2 amarillo, 3 verde, 4 azul, con tonos intermedios entre ellos. **Clear + knob** = 0 (Clear no sale de la vista); **Clear + el botón de la pista** = los knobs a 0. **Pads 1 / 8** = la envolvente desde arriba, **sostenida mientras los mantienes**; K8 marca solo la caída (en Synth 1 / 2, desde la Beta 5.56, el ataque llega a todo el patch a la vez). **Pad 32** (rojo) = salir. **Preset** = los patches, los de la cadena en blanco: un toque carga ese patch y sale; mantener 0,4 s = cadena nueva con los knobs como están. El morph sigue en las otras vistas; el **botón de la pista** vuelve a la vista del morph (desde ella, a la Note). **Un morph a la vez:** mantener patches 0,4 s en la vista Preset de otra pista abre el morph de esa pista y para el anterior (su sonido se queda donde está); un toque en otra pista solo carga ese patch. Los parámetros continuos se mezclan; los de tipo (onda, algoritmo, modo…) toman el del patch más cercano. No se guarda nada.
""", [("colores-patch", 0), ("guardar-patch", 0)])

# ===================================================================================================== III
view("midi-preset", "III", "Vista Preset de MIDI 1 / 2",
     "Pulsa **MIDI 1** o **MIDI 2** y luego **Preset** (*desde RC4*: o **MIDI 1 / MIDI 2 otra vez** con su vista Note en pantalla, o **Shift + MIDI 1 / 2**). Además de las plantillas de stock, aquí vive el sinte propio de la pista.",
     f"""
- **Teclado externo** *(desde RC2.08)*: las notas que entran por MIDI (USB o DIN) en el canal de MIDI 1 / 2 **tocan su sinte propio** (antes solo se grababan); no se reenvían a la salida MIDI.
- **Morph de patches** {YB}: como en la [vista Preset de Synth 1 / 2](#synth-preset), con los huecos del sinte propio (motor encendido; también su FM de 8 operadores). Aquí la vista del morph va sobre la Preset: **Preset** cambia entre el morph y los huecos.
### Pads
| Pad | Función |
|---|---|
| 1-5 | Página de knobs del motor: 1 VCA-VCF, 2 OSC 1 (granular en ese motor), 3 OSC 2, 4 **knobs secuenciables** ({XB} **Shift + pad 4** = knobs no secuenciables), 5 modulación. {YB} **Pad 1 = knobs secuenciables** (Shift + pad 1 = no secuenciables), 2 OSC 1, 3 OSC 2, **pad 4 = Filtro / VCA**, 5 modulación (los pads 1 y 4 cambian de sitio). **Clear + el pad** {B}: los valores de esa página (con y sin Shift) a los iniciales. {XB}: un toque deja la página; **mantener el pad ½ s o más** = esa página solo mientras lo mantienes (al soltar, vuelve la anterior). |
| 6 | {NB} **Matriz de modulación** (azul claro; ver «Matriz de modulación»). **Clear + pad 6**: todas las fuentes apagadas. |
| 9-24 | **Patches del sinte propio** {B}: ver abajo. |
| 25 | **Editor de CC** de los macros MIDI ([editor de CC](#midi-cc)). |
| 26 | **Patch flip**: cada nota de la pista sale como Program Change (por el canal de la pista; si ese canal es el de un sinte o los drums, también por dentro). Excluyente con el motor. |
| 27 | **Motor** de la pista: apagado → ámbar (entrada de línea) → verde (oscilador) → naranja (VA-drum) → magenta (granular) → verde azulado (muestra {B}) → azul (secuenciador de efectos). {XB} Con el motor apagado, el pad se ve gris (blanco tenue). |
| 28 | Uno / dos osciladores (oscilador y VA-drum). |
| 29 | Orden de la cadena: VCA → FX → filtro / filtro → VCA → FX (en el color de la página VCA-VCF {B}). {YB}: **de fábrica filtro → VCA → FX**; encendido, VCA → FX → filtro. Un proyecto o patch guardado conserva el pad, así que su orden se invierte. |
| **Shift + 29** {B} | **Gate retrigger**: encendido (verde con Shift, por defecto) = cada nota nueva vuelve a disparar la envolvente; apagado (amarillo) = **legato**: con otras notas pulsadas, una nota nueva solo cambia la altura. {XB} Pasa por los ocho **modos de voz** del pad 32 (con Shift, en el color del modo). |
| 30 | Abre el **step-drummer**; **Shift + pad 30** lo desactiva. |
| 31 | Solo en VA-drum: la velocity escala las envolventes de pitch y filtro. |
| 32 | {XB} **Modo de voz** (desplegable): ver «Modo de voz» abajo. |

### Modo de voz (pad 32) {XB}
{YB} El pad 32 (y Shift + pad 29) solo se ven y funcionan con un motor que los usa (oscilador, FM, VA-drum, muestra); sin voz, solo VCA / VCF / FX, granular o secuenciador de efectos se apagan. Con el motor encendido, **un toque al pad 32** abre los modos de voz en los **pads 17-24** (los que se llaman igual, del mismo color) (el actual brillante, los demás tenues; los pads 9-24 dejan de cargar patches mientras); tocar uno lo elige; el pad 32 otra vez (o salir de la vista) lo cierra. El pad 32 se ve siempre en el color del modo. Con el desplegable abierto, **K1 = cantidad del glide** (verde azulado: su tiempo; a la izquierda del todo, sin glide; hasta unos 2 s) y **K2 = desafinación del unísono** (azul; hasta ±50 cents entre las voces de los extremos). El modo, el tiempo y la desafinación se guardan con el patch del sinte propio y con el proyecto.

| Pad | Modo |
|---|---|
| 17 (verde) | **Retrigger**: cada nota nueva vuelve a disparar la envolvente. |
| 18 (amarillo) | **Legato**: con otras notas pulsadas, una nota nueva solo cambia la altura. |
| 19 (verde azulado) | **Glide**: como legato (con otras teclas pulsadas no vuelve a disparar el gate), pero la altura **se desliza** de la nota pulsada a la nueva (K1 = la cantidad: el tiempo del glide). Una nota tocada sin otras pulsadas empieza en su altura y vuelve a disparar. En el oscilador (uno o dos), el VA-drum y FM; el modo muestra y el granular no deslizan. |
| 20 (verde) | **Uni retrig**: las voces (4; en FM 6, o 3 con las dos pistas en FM) tocan la misma nota, repartidas con K2 de forma simétrica; cada nota nueva las mueve todas y vuelve a disparar la envolvente; suenan hasta soltar todas las notas. En el oscilador (uno o dos), el VA-drum y FM; en el modo muestra, una voz. |
| 21 (amarillo) | **Uni legato**: el unísono como legato: con otras teclas pulsadas, las voces solo cambian de altura (sin volver a disparar el gate ni, en FM y VA-drum, sus envolventes propias). |
| 22 (verde azulado) | **Uni glide**: el unísono deslizándose solo de una nota pulsada a otra (legato); una nota tocada sin otras pulsadas empieza en su altura, sin glide, y vuelve a disparar la envolvente. |
| 23 (violeta) | **Uni always-glide**: el unísono deslizándose siempre de la nota anterior a la nueva, aunque se hubieran soltado todas las teclas (entonces el gate vuelve a dispararse); con otras teclas pulsadas, las voces solo cambian de altura. |
| 24 (magenta) | **Poly**: En el **oscilador** (uno o **dos osciladores**; también la supersaw), el **VA-drum**, **FM** y el **modo muestra** (también en estéreo), **hasta 4 notas a la vez** (en FM, hasta 6), cada una con su velocity; la envolvente, el filtro y el efecto son los de la pista y cada nota nueva vuelve a dispararlos; soltar una nota con otras pulsadas la apaga y la última suena con el release; una nota de más quita la voz de la más antigua. **En el VA-drum** cada golpe lleva **su propia envolvente de tono y de volumen y su ruido**: un golpe nuevo no reinicia los anteriores y soltar la nota no corta el golpe (el filtro sigue siendo el de la pista). **En FM** cada nota lleva sus cuatro operadores con sus envolventes y su ruido, y suena entera con su release aunque toques otras; **6 voces FM entre las dos pistas**: una pista sola tiene 6; con MIDI 1 y MIDI 2 en FM poly (o unísono), 3 cada una. En granular, una voz. *Desde RC4*: cada voz baja según cuántas suenan (una o dos notas, igual; cuatro, a 0,71; seis, a 0,58), para que los acordes no recorten; **poly es el modo de un proyecto que nunca eligió otro**; y si el DSP se va a quedar sin tiempo (muchas voces FM con releases largos), **se apaga la voz que ya suena más baja soltándose** (o, si no hay ninguna, la nota mantenida más antigua) antes de que se oiga un traqueteo; después toca con las voces que caben y cada 2 s prueba con una más (también en los unísonos, que siguen la misma regla de nivel). Mientras suenan dos voces o más, **Synth 1 y Synth 2 no pierden voces** por el tiempo que ocupan (el aparato quitaba las suyas al quedarse corto: callaban hasta soltar el acorde); si de verdad falta tiempo, las que se apagan son las del sinte propio. |

Cuántas voces da cada modo, el volumen de los acordes y el límite de voces cuando el DSP va justo: [Voces del sinte propio](#midi-voces).

### Secuenciador de saltos {YB}
Una pista MIDI puede mover el patrón de otra: sus notas, en vez de sonar, hacen **saltar esa pista al paso que indican**.

- **Apuntar (step flip)** {YB}: el **pad 26** abre y cierra la **vista de flip** (pad 26 blanco mientras está abierta; no cambia el modo; se cierra sola al salir de la vista y al abrir la fila de motores). En la **fila 3** se elige el modo, uno u otro: **pad 17 = patch flip (PGM seq)**, en el color del pad 26 de siempre; **pad 18 = step flip**, en el color de la pista destino; brillante el que está encendido, tenue el otro; **tocar el encendido lo apaga**. Con step flip, la **fila 2** son las ocho pistas, en el orden de sus botones y en sus colores (la propia sin luz, el destino brillante): un toque cambia el destino. Encender step flip sin elegir destino usa **el último destino** (de fábrica, Synth 1). Con la vista cerrada, en step flip el **pad 26 parpadea** en el color del destino. (El pad 19 queda reservado para un modo morph futuro.)
- **O saltos o motor:** apuntar apaga el motor de la pista, y encender un motor deja de apuntar: solo una de las dos funciones a la vez.
- **Mientras apunta, la pista no toca notas:** ni su motor, ni por MIDI, ni por el canal compartido. Cada nota suya, del secuenciador, de los pads o del arpegiador, es un salto: cae en el mismo paso que la nota y la pista apuntada sigue desde ahí.
- **Qué paso:** en su vista Note, los **pads 17-32 son los pasos 1-16** y con **Octave ▲ los pasos 17-32**; en la **Note ampliada, los 32 pads son los pasos 1-32 en orden**. Al apuntar, la pista pasa a los pasos 1-16 y Octave solo se mueve entre 1-16 y 17-32: el Octave que ya no puede moverse se apaga, y en la ampliada los dos. La escala y la tónica no cambian nada: mientras ves esa pista, su teclado es una disposición Jankó con una nota distinta en cada pad, y las demás pistas conservan el suyo.
- **Vale todo lo de un paso:** probabilidad, 1 de cada N, random-mutate. Una pista silenciada en el Mixer no hace saltar.
- **Pads y otras velocidades:** un pad en marcha salta en el paso siguiente de la pista apuntada; una pista más lenta espera a su paso siguiente. **Parado, un pad hace sonar ese paso de la pista apuntada** mientras lo mantienes, sin saltar (en los drums, su golpe con el sample elegido; un paso vacío no suena). Con Record, los pads se graban y saltan al reproducirse.
- **Misma longitud:** si la pista apuntada y la pista MIDI tienen la misma longitud, un salto solo se nota la primera vez: en las vueltas siguientes la otra pista ya va por ese paso. Para oírlo en cada vuelta, usa longitudes distintas o dos saltos en el patrón: uno que la mueva y otro que la devuelva.
- Un paso fuera del inicio / fin del patrón suena una vez y el patrón termina como siempre. MIDI 1 y MIDI 2 pueden apuntar a la vez. **Se guarda con el proyecto.**

### Patches del sinte propio (pads 9-24) {B}
- 16 huecos por página; **Octave ▼ / ▲** = 4 páginas (64 huecos por pack, comunes a MIDI 1 y MIDI 2); {XB} **8 páginas, 128 huecos**.
- **Tocar** = cargar (suena la tónica mientras mantienes el pad; {XB}: **Shift + pad** = cargar sin que suene). **Clear + pad** dos veces = guardar. {YB} **Duplicate + un hueco vacío** = guardar ahí al momento. **Duplicate + A + B** = intercambiar; **Duplicate + A**, otro pack, **Duplicate + B** = copiar a otro pack (Duplicate en amarillo mientras hay uno esperando).
- Colores: melocotón tenue = con patch, brillante = el último usado, violeta = vacío. {YB}: cada patch en **el color de su motor** (el de la fila del pad 27; FM violeta; {YB} wavetable arena), brillante = el último usado; **vacío = blanco tenue**.
- Un patch guarda el motor entero: motor elegido, osciladores, orden, todos los valores y el ajuste del step-drummer *(escribe en la tarjeta)*.
- **Clear + el botón de la pista** {B} devuelve todos los valores del motor a los iniciales (el motor elegido se queda; {XB}: también los del FM, y la matriz se queda con sus destinos y la cantidad a cero).

### Los motores (pad 27)
- **Elegir el motor** {XB}: un toque al **pad 27** abre la **fila de motores** en los **pads 17-23**: apagado (blanco), entrada de línea, oscilador, VA-drum, granular, muestra y secuenciador de efectos, en sus colores; el actual brillante, los demás tenues. {YB}: **pads 17-24** = sin voz (blanco), solo VCA / VCF / FX (la entrada de línea), oscilador, oscilador VA-drum, oscilador wavetable (arena), muestra, granular y FM; **el secuenciador de efectos sale de la fila: es el pad 31** con «sin voz» (azul tenue; un toque lo enciende, brillante, y la fila sigue marcando «sin voz»; otro toque lo apaga). Tocar uno lo elige y la fila sigue abierta; **pad 27 otra vez** la cierra y vuelve la lista de patches (pads 9-24, que mientras tanto no cargan nada). Shift + pad 27 sigue pasando al motor siguiente (antes de RC4, cada toque del pad 27).
- **Wavetable** {YB} (arena, pad 21): el oscilador leyendo una tabla de hasta 9 cuadros, para los dos osciladores; **K3** de OSC 1 / OSC 2 = la posición (en la Beta 5.24-5.26, K7), K7 de OSC 1 = LFO → posición, Shift + K3 = envolvente → posición, SHAPE (K4) = warp. Con ella sonando (también con la fila de motores abierta), **pad 7 mantenido** = las 16 wavetables del stock (un toque llena la tabla; **Shift** + una tabla = solo el cuadro que señala la posición (K3), con el mismo cuadro de esa tabla) y **pad 8 mantenido** = los samples del pack (Octave = página; un toque pone un ciclo del sample **en el cuadro que señala la posición**). Cada toque en una lista suena la tónica hasta soltar el pad. El pad 27 se ve en arena. {YB} **Clear + pad 7** = el cuadro que señala la posición (K3) vuelve al de su tabla (la tabla del stock que tenía, o la de partida), con la tónica. **Warp** (SHAPE lejos del centro): mucho menos aliasing en los agudos; a cambio, en los extremos suena algo más apagado.
- **Entrada de línea** (amarillo): la entrada de audio de la pista (línea 1 en MIDI 1, línea 2 en MIDI 2) pasa por el VCA-VCF; las notas de la pista lo disparan.
- **Oscilador** (verde): morph seno → triángulo → sierra → cuadrada, SHAPE, segundo oscilador (pad 28) con FM, ring, sync y modos bit a bit; dos notas = parafonía (con un oscilador, {B}: la última nota manda y al soltarla vuelve la anterior).
- **VA-drum** (naranja): VCA de un disparo, envolventes de decay para pitch (knob Sustain) y filtro (knob Release), ruido blanco (velocidad del LFO) y valores aleatorios en lugar del LFO.
- **Granular** (magenta): hasta 16 granos desde un sample del pack o la captura (página 2, capítulo siguiente).
- **Muestra** (verde azulado) {B}: un sample del pack de un golpe a la altura de la nota (C3 = como se grabó), con sample flips por paso; se elige en la vista Note ampliada (ver «Modo muestra»).
- **Secuenciador de efectos** (azul): el step-drummer de la pista dispara los huecos de la fila inferior de Master FX (6.1).
- **FM** (violeta) {XB}: el **pad 24** de la fila: un sinte FM de 4 operadores, variante del oscilador, con 16 algoritmos (clásicos, percusivos, campanas y cuerdas) y sus knobs en la **página 7** (capítulo «FM de 4 operadores»).
- La pista sigue mandando su MIDI con cualquier motor.
""", [("motor-midi", 0), ("patches-midi", 0)])

view("midi-voces", "III", "Voces del sinte propio: polifonía y límite de voces",
     "Con el sinte propio de MIDI 1 / 2 encendido, el **pad 32** de su [vista Preset](#midi-preset) elige el modo de voz {XB}. Con diagramas y todas las tablas de motores, knobs, guardado y MIDI: [Pistas MIDI y modos de voz](https://ghillermo.github.io/CIRCUIT-HACKS-RC/voces.html). Aquí, cuántas voces da cada modo y cada motor, cómo suenan los acordes y qué hace el aparato cuando el DSP va justo de tiempo.",
     f"""
### Cuántas voces
| Modo de voz | Motor | Voces de la pista |
|---|---|---|
| Retrigger, legato, glide | todos | 1 |
| Poly | oscilador (uno o dos, también la supersaw), VA-drum, muestra | **4** |
| Poly | FM | **6**; con MIDI 1 y MIDI 2 las dos en FM poly (o unísono FM), **3 cada una** |
| Uni retrig, uni legato, uni glide, uni always-glide | oscilador, VA-drum, FM | las de poly (4; en FM 6 o 3), todas en la misma nota, repartidas con K2 (con el desplegable del pad 32 abierto) |
| Unísono | muestra | 1 |
| Todos | granular | 1 |

- Es el **máximo de cada pista**: MIDI 1 y MIDI 2 tienen cada una el suyo; solo las voces FM se reparten entre las dos.
- **Una nota de más** (todas las voces ocupadas) quita la voz a la nota más antigua de la pista, con un fundido de 2 ms.
- **Una nota soltada sigue ocupando su voz** mientras suena su release: con releases largos las voces se llenan aunque toques notas sueltas, y la siguiente nota quita la más antigua.
- En poly la envolvente, el filtro y el efecto son los de la pista: cada nota nueva vuelve a dispararlos. En el VA-drum y en FM cada voz lleva además sus propias envolventes y su ruido, y suena entera con su release.

### Volumen de los acordes
Cada voz baja según cuántas suenan, para que la suma no recorte: **1 o 2 notas, a nivel completo; 3, a 0,82; 4, a 0,71; 5, a 0,63; 6, a 0,58**. Los unísonos siguen la misma regla. Un acorde suena más fuerte que una nota sola, pero no el doble.

### Cuando el DSP va justo: el límite de voces
El audio se calcula en el DSP por bloques, y todo lo que suena comparte su tiempo: el sinte propio, Synth 1 / 2, los drums, los efectos y Master FX. Cada voz del sinte propio gasta tiempo; **FM es el motor que más**, y los releases largos mantienen muchas voces sonando a la vez. Si un bloque no llega a tiempo se oye un **traqueteo**. Para que no pase:
- Con **dos voces propias o más** sonando, el aparato mira cada 2 ms cuánto tiempo le sobra al DSP. Si se va a quedar sin él, **apaga una voz del sinte propio**: la que ya se está soltando y suena más bajo (las de FM antes que las de los otros motores); si no hay ninguna soltándose, **la nota mantenida más antigua**, que se corta como en un robo de voz. Como mucho una voz cada 12 ms (cada 4 ms si va muy justo).
- Después la pista toca **con las voces que caben** (como mínimo 2): una nota nueva apaga antes la que se suelta más baja, y el unísono usa como mucho esas voces. **Cada 2 s sin problemas prueba con una voz más**, hasta volver al máximo de la tabla.
- **Lo que se oye:** un release largo que termina antes de tiempo, o la nota más antigua de un acorde que se apaga cuando hay mucho sonando. Cuántas voces caben depende de todo el proyecto: con Master FX, muchos drums o Synth 1 / 2 con patches pesados caben menos.
- **Synth 1 y Synth 2 no pierden voces por el sinte propio.** El aparato tiene su propio límite para ellos (cuando el DSP va justo, apaga voces de Synth 1 / 2); mientras suenan dos voces propias o más no lo usa, y si falta tiempo las que se apagan son las del sinte propio. Con el DSP muy justo, una nota nueva de Synth 1 / 2 puede usar una voz de su mismo sinte en lugar de una libre (lo que hace el aparato con carga): un acorde de Synth 1 / 2 puede sonar con menos notas, pero no se calla.
- Con **una sola voz propia** (los modos mono, o poly con una nota) el límite no actúa: el DSP lo reparte el aparato como siempre.

### Consejos
- Para tener más voces a la vez: releases más cortos, en FM menos operadores con nivel alto, o una sola pista en FM poly (6 voces en lugar de 3 + 3). {YB} Las voces FM las calcula el **otro núcleo del DSP**: 6 por pista también con MIDI 1 y MIDI 2 en FM poly (12 en total) y no quitan tiempo a lo demás; si ese núcleo no llega a tiempo (unas 10 voces FM, unas 8 con el granular sonando), el límite apaga una voz FM igual que arriba. El FM suena 1,3 ms más tarde que el resto, como el granular.
- Si un acorde largo pierde notas, prueba el patch con un release más corto o con un motor más ligero (un oscilador, VA-drum, muestra).
- Los modos mono (retrigger, legato, glide) usan una sola voz: nunca entran en el límite.
""")

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
| K7 | WAVE (morph); {XB} en el modo muestra, la anchura estéreo | — |
| K8 | LFO → morph | Envolvente → morph |

{YB} Con el oscilador, el VA-drum y la wavetable la página es otra (tus parámetros se conservan, solo cambian de knob):

| Knob | Solo | Con Shift |
|---|---|---|
| K1 | TUNE | Envolvente → tono |
| K2 | FINE | LFO → tono |
| K3 | WAVE (morph); en la wavetable, la posición (el cuadro); en el modo muestra, la anchura estéreo | Envolvente → morph |
| K4 | SHAPE (en la wavetable, warp) | Envolvente → forma |
| K5 | **LFO → FM** | **Envolvente → FM** |
| K6 | **LFO → ring** | **Envolvente → ring** |
| K7 | LFO → morph | LFO → forma |
| K8 | **LFO → mix** | **Envolvente → mix** |

K5, K6 y K8 son nuevos: cuánto mueven el LFO y la envolvente del motor el FM, el ring y el mix de la página 3 (centro = nada, a cada lado en un sentido; Clear + knob = 0). Se guardan con el patch y con el proyecto.

{YB} **Con un solo oscilador** (motor oscilador o wavetable, sin los dos osciladores) K5, K6 y K8 tienen funciones propias, con sus valores aparte (al encender los dos osciladores vuelven las de arriba con los suyos):

| Knob | Solo | Con Shift |
|---|---|---|
| K5 | **Nivel del sub-oscilador** (una cuadrada una octava por debajo) | Envolvente → sub |
| K6 | **Nivel del ruido** | Envolvente → ruido |
| K8 | LFO → sub | LFO → ruido |

Los niveles van de apagado (a la izquierda del todo; Clear + knob) al del oscilador; su LED brilla más cuanto más nivel. Las profundidades son bipolares (centro = nada). El sub y el ruido pasan por el filtro y el VCA, y en poly cada voz lleva los suyos. Se guardan con el patch y con el proyecto.

**Qué hace SHAPE en cada forma de onda** (K2; {YB} K4; SHAPE 2 en el OSC 2, igual). El centro del knob es la forma pura (en la sierra *(desde RC4)*, la izquierda del todo); la envolvente (K4) y el LFO (K6) mueven SHAPE desde la posición del knob. Con WAVE entre dos formas, SHAPE actúa sobre las dos a la vez, cada una a su manera:

| Forma (WAVE) | SHAPE a la izquierda del centro | Centro | SHAPE a la derecha del centro |
|---|---|---|---|
| Seno (0) | Nada: la forma pura | Pura | **Wavefold**: la onda se amplifica (hasta unas 8 veces a la derecha del todo) y se pliega sobre sí misma: más armónicos cuanto más a la derecha. *(desde RC4)* En las notas agudas la amplificación máxima baja para no generar aliasing: unas 6,7 veces en la nota 72, 3,9 una octava más arriba, 2,4 dos octavas más arriba |
| Triángulo (42) | *(desde RC4)* **Rampas exponenciales**: picos afilados y valles anchos, más armónicos cuanto más a la izquierda (antes de RC4, nada) | Puro | **Wavefold**, como el seno |
| Sierra (84) | *(desde RC4)* Todo el recorrido: a la izquierda del todo una sierra normal; hacia la derecha, **supersaw** de 7 sierras (la central y 6 desafinadas que suben de nivel y se separan; a la derecha del todo, la supersaw entera) | Media supersaw | Supersaw entera a la derecha del todo |
| Sierra antes de RC4 | La rampa se curva hacia arriba (sube rápido al principio y se aplana) | Rampa recta | La rampa se curva hacia abajo (empieza plana y sube al final) |
| Cuadrada (126) | Pulso cada vez más estrecho (hasta un 3 % aprox.) | Cuadrada (50 %) | Pulso cada vez más estrecho por el otro lado (hasta un 97 % aprox.; suena igual que el de la izquierda) |

**Menos aliasing** *(desde RC4)*: la sierra, las siete sierras de la supersaw y la cuadrada / el pulso se generan con PolyBLEP: en las notas agudas desaparecen los tonos metálicos que no pertenecen a la nota (unos 40 dB menos); en las graves suenan igual. El seno y el triángulo sin pliegue no cambian. *(Arreglo de RC4.08 y la Beta 5.28)* El pulso con un ancho distinto del 50 % (SHAPE fuera del centro, o la envolvente / el LFO moviéndolo) solo tenía corregido un flanco: ahora los dos (nota 96: de −22 a −73 dB de aliasing por debajo de 8 kHz). {YB} El antialias es un **BLEP de 4 muestras** (antes de 2): por debajo de 8 kHz, en las notas 72 y 96, sierra y pulso pasan de unos −60 a unos −87 dB y la supersaw de −65 a −95; el agudo queda un poco más apagado (unos −2,5 dB a 10 kHz).

### Página 2 — granular
| Knob | Solo | Con Shift |
|---|---|---|
| K1 | Tono ±24 st | Fino ±1 st |
| K2 | Posición en el sample | Dispersión de la posición |
| K3 | Scan (centro congelado) | {XB} **Bipolar**: a la izquierda, probabilidad de grano al revés (hasta 100 %); a la derecha, dispersión del tono (hasta ±24 st). Antes de RC4: probabilidad de grano al revés |
| K4 | Tamaño del grano 5-500 ms | {XB} **Dispersión estéreo** (ver abajo). Antes de RC4: dispersión del tono |
| K5 | Densidad 1-16 granos | Ventana |
| K6 | Zona del scan | Modo de nota: tono / slicer / stretch {B} |
| K7 | LFO → posición | LFO → tamaño |
| K8 | Envolvente → posición | Fuente: la captura o el sample de un drum {B} |

- **Modo de nota (Shift + K6):** **tono** = las notas cambian la altura de los granos; **slicer** = el sample se parte en 16 trozos y cada nota toca uno (la nota 36 el primero, cada nota más arriba el siguiente; cada 16 notas vuelve a empezar); **stretch** {B} = las notas cambian la altura y el tramo desde la posición (K2) hasta el final dura **K3 pasos** (1-64) a cualquier tempo, sin cambiar la altura, alineado con el inicio del transporte; parado, la posición se queda congelada.

- **Granular en estéreo** {XB}: con **Shift + K4** por encima de 0, cada grano sale a un lado al azar, tanto más separado cuanto más alto; el **panorama de la pista** (Mixer) decide la proporción: al centro, mitad y mitad; a la derecha, más granos a la derecha. La parte estéreo (lo que difiere entre los lados) sigue el VCA, el nivel, el panorama, el mute y el sidechain de la pista; el filtro y el efecto del motor y los envíos actúan solo sobre el centro.

### Páginas 3-5
- **Página 3 (OSC 2):** {B}: los ocho valores sin Shift, según la serigrafía: K1 Oscillator TUNE 2, K2 Osc mod SHAPE 2, K3 Amp envelope MIX OSC 1 ↔ OSC 2, K4 Filter envelope FM, K5 Filter frequency FINE 2, K6 Resonance BITSYNC, K7 Modulation WAVE 2, K8 FX RING (en RC0.9: K1 TUNE 2 / FINE 2, K2 SHAPE 2 / FM, Shift + K3 RING, K7 WAVE 2). {YB} Con el oscilador, el VA-drum y la wavetable: **K1 = ratio de OSC 2 respecto a su nota** (centro = 1; a la izquierda ½ y ¼; a la derecha 2, 3, 4 … 31, unos dos clics por ratio), **K2 = detune** (±50 cents, centro = afinado), K3 WAVE 2, K4 SHAPE 2, **K5 FM**, **K6 RING**, **K7 sync + bitwise**, **K8 MIX OSC 1 ↔ OSC 2** (en la Beta 5.25 / 5.26: K3 SHAPE 2, K4 MIX, K5 FM, K6 BITSYNC, K7 WAVE 2, K8 RING). Con el granular la página 3 sigue como antes. Con dos notas pulsadas, OSC 2 toca la segunda nota × su ratio.
  - **K5 FM con centro** {YB}: su LED: tenue en el centro, en el color de la pista hacia la derecha y en su tono claro hacia la izquierda; pasado el máximo (el recíproco, hacia 50 / 50), **violeta**. En el centro, sin FM; a la derecha **OSC 2 modula a OSC 1** (más fino al principio: la primera mitad del recorrido llega al máximo); pasado el máximo, OSC 2 → OSC 1 baja mientras **OSC 1 → OSC 2** sube, hasta 50 / 50 a la derecha del todo. A la izquierda, lo mismo con los papeles cambiados. Los patches y proyectos anteriores se cargan con la misma cantidad de FM en su sitio nuevo.
  - **K7 sync** {YB}: la zona sync es ahora el **sync clásico**: OSC 2 vuelve a empezar en cada ciclo de OSC 1; dentro de la zona, el knob sube OSC 2 hasta unos 32 semitonos (el barrido típico del sync; el timbre también cambia con el ratio / detune de K1 / K2). El de antes (OSC 2 al revés cada 1-8 ciclos) daba subarmónicos que no casaban con la nota: sonaba a ruido. Las zonas bitwise (xor, or, nor, and, nand) siguen igual, con un **paso bajo suave** sobre lo que añaden (menos ruido blanco).
  - **Menos ruido en las interacciones** {YB}: el antialias de OSC 1 tiene en cuenta el FM (antes corregía en el sitio equivocado y crepitaba). Medido en emulación (nota 84, ruido por debajo de 8 kHz): FM sierra ← seno de −37 a −63 dB, FM al máximo de −18 a −57 dB, sync de −5 a −36 dB. **Arreglo:** en poly (el modo de fábrica) con dos osciladores, el ratio de OSC 2 (K1) distinto de 1 lo mandaba al tope de afinación.
- **Página 4 — knobs secuenciables:** los 8 valores secuenciables: con Record + Play sus movimientos se graban en el patrón (TUNE, Release, Env → nivel, Env → filtro, Filtro, Resonancia, Velocidad del LFO, Efecto). {YB} **Grabando** (Record armado y sonando), girar un knob del motor que **no está en estos 8** lo añade: toma el primer carril que no tiene nada grabado en el patrón que suena, y se graba ahí (ese carril cambia de destino, como con Shift + knob). Si los 8 tienen algo, no se graba, como antes. {XB}: **Shift + knob** = el **destino** de ese knob: los 33 parámetros del motor en el orden y los colores de la matriz de modulación (el LED en el color de su página; 4 clics por parámetro); con **Clear mantenido antes de Shift**, el de fábrica. Mientras eliges, **los pads 9-24 enseñan dónde está el destino**, como al girar un knob de la matriz: el pad de su página brillante y los knobs de esa página (K1-K8 arriba, Shift + K1-K8 abajo; el destino brillante). El carril graba y reproduce el destino nuevo (lo que ya tenía grabado mueve ahora ese parámetro). Se guardan con los patches del sinte propio (vista Preset de MIDI 1 / 2); un patch sin ellos carga los de fábrica.
- **Knobs no secuenciables** {XB} (**Shift + pad 4**; el pad 4 en rosa mientras están en los knobs, rosa tenue con Shift): 8 knobs con **destino asignable** como los secuenciables (**Shift + knob** = el destino entre los 33 parámetros, en el color de su página; **Clear mantenido, luego Shift + knob** = el de fábrica; mientras eliges, los pads 9-24 enseñan dónde vive). De fábrica: Ataque, Decay, Sustain, SHAPE, LFO → filtro, Env → tono, MIX OSC 1 / 2, Gain del VCA. Mueven el valor de ese parámetro **sin grabarlo** (un destino que también esté en los knobs secuenciables sí se graba, como desde cualquier página). Sus destinos se guardan con los patches propios.
- **Foto de los valores en un paso** {XB}: con la vista de pista de MIDI 1 / 2 (motor encendido), **Record mantenido + un pad de paso** (pads 1-16; con 17-32, los pasos 17-32) escribe en los carriles de ese paso los parámetros que **no están en su valor inicial** (el de Clear + knob a la derecha), y solo esos. Un parámetro que no tiene carril toma uno cuyo parámetro sí está en el inicial (en orden de carril), y ese carril se borra antes en el patrón; si no caben, los primeros en el orden de la matriz. El paso no cambia sus notas y Record queda como estaba. {YB} También en **Synth 1 / 2** (sus macros) y en los **drums** (pitch, decay, distorsión y EQ): [vista de pista de Synth 1 / 2](#synth-nota), [vista de pista de un drum](#drum-pista). {YB} Mientras mantienes el paso, se ve en **amarillo**.
- **Página 5:** ADSR arriba, LFO abajo. {B}: **Shift + K8 = forma del LFO**: diente de sierra inverso (azul, la de siempre), diente de sierra (magenta), triángulo (verde), cuadrada (roja), seno (verde azulado), sample & hold (blanco: un valor al azar en cada vuelta); {NB}: **sample & hold suavizado** (violeta: se desliza de un valor al azar al siguiente durante cada vuelta), y **sin forma guardada (un proyecto nuevo o de antes) el triángulo** (en RC2: el diente de sierra inverso; un patch propio de antes de las formas sigue cargando el diente de sierra inverso). {ZB}: seno, sample & hold y sample & hold suavizado suenan (antes dejaban el motor callado). Un paso cada 4 clics ({YB}: cada 16), el LED de K8 con Shift en su color. Se guarda con el proyecto y en el patch propio; con el VA-drum el LFO sigue siendo su ruido.
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

- **La posición del knob es el destino y la cantidad.** Del todo a la izquierda = apagado. Al girar a la derecha se pasa por **todos los parámetros de las páginas de knobs** (33: los de la página 1, luego los de la 2, la 3 y los de la 5 que no salen antes), cada uno con un tramo: dentro del tramo la cantidad crece de 1/16 a entera ({XB}: de 0 a entera: el primer paso del tramo es el destino sin cantidad, con el LED tenue); al pasar al tramo siguiente cambia el destino y la cantidad vuelve a empezar.
- **Knobs lentos:** dos clics por paso, 16 pasos por destino.
- **El color del LED es el de la página del destino** (los colores de los pads 1-5: ámbar VCA-VCF, verde OSC 1, verde azulado OSC 2), el **brillo** la cantidad; apagado = sin destino.
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
| K1-K4 | Ratio de los operadores 1-4: 0,5 … 16 (verde = entero, azul claro = y medio, verde azulado = inarmónico: 0,71, 1,41, 4,24). Cada ratio ocupa 5-6 clics: el primero es exacto y cada uno de los siguientes **desafina** +2,5 cents (hasta unos +12; LED a media luz) | Centro = ataque 0. **A la derecha:** el ataque del operador (0 … unos 3 s; azul claro). **A la izquierda:** el operador es **percusivo** con su propio decay, más corto cuanto más a la izquierda (3 ms … 8 s; rojo) |
| K5 | Nivel del operador 1 (azul) | Algoritmo (16, 8 clics cada uno, {YB}: 16; el color de su familia) |
| K6 | Nivel del operador 2 | Feedback (magenta) |
| K7 | Nivel del operador 3 | Ruido (blanco) |
| K8 | Nivel del operador 4 | Release (ámbar) |

- **Elegir el algoritmo con los pads:** en la página FM, **mantén el pad 7**: los pads 9-24 enseñan los 16 algoritmos (el color de su familia; el actual brillante). **Pulsa uno**: queda elegido y suena la tónica mientras lo mantienes (**Shift + pad**: sin sonar). Al soltar el pad 7 vuelven los patches.
- **Sonidos de partida** {XB}: con el FM encendido, **un toque al pad 8** abre la página FM (como el pad 7) y **mantener el pad 8** enseña en los pads 9-24 **16 instrumentos** listos para tocar, en el color de su familia: **fila 2** piano, piano eléctrico, órgano (teclados, blanco), pluck, arpa, marimba (pulsados, violeta), bajo (ámbar), campana (verde azulado); **fila 3** cuerdas, pad (verde), flauta, clarinete, metales (vientos, azul claro), bombo, caja, hi-hat (percusión, naranja). **Pulsa uno**: se carga entero (algoritmo, ratios, niveles, envolventes, feedback, ruido y release) y suena la tónica mientras lo mantienes (**Shift + pad**: sin sonar); el que coincide con lo que suena se ve brillante. Son puntos de partida: luego se retocan con los knobs y se guardan como cualquier patch. El pad 8 se ve blanco tenue con el FM encendido y brillante mientras lo mantienes.
- **Al girar un ratio** (K1-K4) los pads 9-32 enseñan los 24 ratios durante 1,5 s (el actual brillante, en blanco si está desafinado); al girar el algoritmo (Shift + K5), los pads 9-24 enseñan los algoritmos. Mientras se ven, esos pads no cargan patches.
- **Es una variante del oscilador:** la nota, TUNE / FINE, la envolvente de pitch y el vibrato de la página 2 siguen valiendo; detrás, el filtro, el efecto y la matriz como con el oscilador. Una nota a la vez (la última manda); con el retrigger apagado (Shift + pad 29) una nota ligada no vuelve a disparar los ataques.
- **El volumen lo dan las envolventes de los operadores**: el VCA del motor se queda abierto (la velocity sigue dando el volumen) y la ADSR de la página 1 mueve el filtro, el tono y el brillo.
- **El brillo:** SHAPE (K2 de la página OSC 1; {YB} K4), Env → forma (K4; {YB} Shift + K4) y LFO → forma (K6; {YB} Shift + K7) cambian cuánto modulan los moduladores (× 0,27 … × 3,7; SHAPE 50 = sin cambio), y también el feedback. Así la ADSR del motor, su LFO, la matriz, los carriles de la página 4 y el step-drummer mueven el timbre del FM.
- **La velocity** da también el brillo (cuánto, según el algoritmo) y cuánto cae el bombo. **Las notas agudas** modulan menos y caen antes (según el algoritmo, como en un DX7). En notas y ratios muy altos el motor limita la modulación para que no haya aliasing (salvo en los percusivos, donde forma parte del sonido).
- **El nivel** de un portador es su volumen; el de un modulador, cuánto modula.
- **Envolventes A/R con sustain fijo:** con la nota pulsada, un operador **sostenido** se queda arriba después de su ataque; uno **percusivo** (lo dice el algoritmo, o su Shift + knob a la izquierda) cae aunque la nota siga. Al soltar, todos caen con el release (uno percusivo por su knob, con lo más corto de su decay y el release). **El release es uno para todos y más largo cuanto más fuerte la nota**; el algoritmo lo acorta o alarga en cada operador.
- **El feedback** es como el del DX7 (la media de las dos últimas salidas): una sierra limpia en más recorrido; el knob es más fino abajo.
- Los algoritmos percusivos y de campana empiezan cada golpe con las fases a cero: todos los golpes suenan igual.
- **Ruido:** blanco, con la envolvente del operador que diga el algoritmo (el 1, salvo la caja), sumado después del FM, en cualquier algoritmo.
- **Clear + pad 7** = una **voz tocable del algoritmo elegido** (la columna «Voz» de la tabla); **Clear + knob** = su valor en esa voz (Clear + Shift + K5: la pila). **Clear + MIDI 1 / 2** = todo el motor a los valores iniciales (el FM, a la pila).
- **Se guarda con los patches del sinte propio** (con el motor en FM). Un patch de la Beta 3.22 o anterior se adapta al cargarlo (los ataques a la mitad derecha de su knob, el mismo feedback, los ratios exactos); una beta anterior carga uno nuevo con el FM apagado. No tiene CC / NRPN. Otro motor de la fila (o Shift + pad 27) lo apaga.

| # | Algoritmo | Familia | Voz (Clear + pad 7) |
|---|---|---|---|
| 1 | 4 → 3 → 2 → 1 (pila) | clásicos (blanco) | la inicial |
| 2 | 3 y 4 → 2 → 1 | | metales |
| 3 | 4 → 1 y 3 → 2 → 1 | | piano eléctrico |
| 4 | 4 → 3 → 1 y 2 → 1 | | bajo |
| 5 | dos pilas: 4 → 3 y 2 → 1 (portadores 1 y 3) | | piano eléctrico 2 |
| 6 | 4 → 1, 2 y 3 (tres portadores) | | pad |
| 7 | 4 → 3; 2 y 1 solos (tres portadores) | | clave |
| 8 | órgano: los cuatro portadores | | órgano (registros 16', 8', 4', 2 2/3') |
| 9 | bombo: 2 → 1; el 4 es la caída de pitch (su nivel = cuánto cae, hasta 3 octavas; su release = cuánto tarda) | percusivos (rojo) | bombo (unas 3 octavas de caída, rápida) |
| 10 | caja: 2 → 1 + ruido con la envolvente del 3; caída de pitch del 4 | | caja |
| 11 | metal / hi-hat: 2, 3 y 4 → 1 con ratios inarmónicos (× 1,41, 2,71, 3,49) | | hi-hat |
| 12 | tom / zap: 3 → 2 → 1; caída de pitch del 4 | | tom |
| 13 | campana: 2 → 1 y 4 → 3, ratios inarmónicos (× 3,5, × 2,76) | campanas (verde azulado) | campana |
| 14 | campana tubular: 2 y 3 → 1 (× 2,76, × 5,4), el 4 portador | | campana tubular |
| 15 | cuerdas: dos pilas (2 → 1, 4 → 3) desafinadas entre sí | cuerdas (verde) | cuerdas (ataque lento) |
| 16 | ensemble: 4 → 1, 2 y 3, tres portadores desafinados | | ensemble |

{YB} Este FM de 4 operadores se sustituye por el **FM de 8 operadores** (capítulo siguiente); sus patches se cargan en él con el mismo sonido.
""", [])

view("midi-fm8", "III", "FM de 8 operadores",
     f"{YB} MIDI 1 / 2: vista Preset, un toque al **pad 27** y el **pad 24** de la fila de motores (violeta); cierra la fila (pad 27) y el **pad 7** abre su página.",
     """
Sustituye al FM de 4 operadores: **hasta 8 operadores** con **envolventes como las del DX7** (4 rates y 4 niveles) en cada uno. **56 algoritmos**: los 16 del FM de 4 operadores, los 32 del DX7 y 8 de 8 operadores (dos pilas de 4, cuatro parejas, una pila de 8, siete moduladores sobre un portador, ocho portadores, tres pilas 3-3-2, dos parejas y una pila de 4, el algoritmo 1 del DX7 más una pareja). El motor calcula solo los operadores que usa el algoritmo: con 4, unas 10 voces; con 6 (los del DX7), unas 6-7; con 8, unas 5.

**Pads de la página FM** (con la fila de motores cerrada):

| Pad | Qué hace |
|---|---|
| 9-16 | Elige el **operador 1-8**: los que usa el algoritmo encendidos (portadores verdes, moduladores azul claro; el elegido brillante), los demás apagados |
| 3 | La **envolvente de pitch** (violeta, el color del FM; brillante mientras la editas), como un noveno operador. Desde cualquier página de knobs abre la página FM con ella elegida |
| 17-24 | **La fila de motores**: sin voz, solo VCA / VCF / FX, oscilador, VA-drum, wavetable (arena), muestra, granular y FM (brillante); un toque cambia de motor (no cargan patches) |
| 7 | {YB} Un toque: el **mapa del algoritmo** (abajo); mantenido ½ s: el mapa mientras lo mantienes |
| Shift + 7 mantenido | (Brillante solo mientras lo mantienes; {YB} antes, el pad 7 mantenido.) **Los 56 algoritmos** en los pads 9-32, en tres páginas: **Octave ▼ / ▲** mientras lo mantienes (encendido = hay otra página). Página 1: los 16 de 4 operadores (verde azulado) y los 8 de 8 (ámbar); página 2: los del DX7 1-24 (blanco); página 3: los del DX7 25-32. El actual brillante; pulsa uno: elegido y suena |
| 8 mantenido | **24 instrumentos** en los pads 9-32, en el color de su tipo: teclados naranja (E.Piano, Bright EP, Clav, Organ, Marimba, Vibes), bajos azul (FM Bass, Synth Bass, Deep Bass), leads y metales rojo (Brass, Sync Lead, Flute), pads y cuerdas verde (Strings, Warm Pad, Choir, Glass Pad), punteados amarillo (Harp, Koto, Nylon), percusión blanco (Kick, Snare, Hi-Hat), campanas y efectos violeta (Tubular Bell, Space Sweep); el cargado brillante. Pulsa uno: se carga y suena. {YB} **Segunda página: Octave ▼ con el pad 8 mantenido** (Octave ▲ vuelve; el Octave que lleva a la otra página se enciende): pianos naranja (Grand Piano, Mellow Piano, Honky-Tonk, Tine Piano, Toy Piano), cuerdas verde (Slow Strings, Ensemble, Cello, Violin, String Swell; Pizzicato amarillo), **vientos verde azulado** (Clarinet, Oboe, Bassoon, Alto Sax, French Horn, Trumpet, Pan Flute, Recorder, Harmonica) y sonidos largos (Cathedral, Bowed Glass, Evolving Pad, Long Bell). Los de la página 1 tienen el release más largo (pianos eléctricos, cuerdas, pads, coro, flauta, metales, arpa, nylon, campana, bajos). {YB} **Al cargar uno, la página 4 (knobs secuenciables) y Shift + pad 4 pasan a los knobs que convienen a su familia** (teclados: Filtro, Resonancia, Env > filtro, Efecto, LFO > tono, Velocidad LFO, Tono, Ganancia; pads y vientos: el LFO y el filtro; percusión: Tono y Decay primero…); los valores no cambian. |

Con la página FM en pantalla, los pads 9-24 no cargan patches: cárgalos desde la página de otro knob. Con el FM, el **pad 28** (dos osciladores) se apaga y no hace nada (el ajuste se queda para cuando el FM se apaga), y el **pad 3** deja la página OSC 2 y es la envolvente de pitch. Las listas del pad 7 / 8 se ven también con la fila de motores abierta o un modo flip encendido.

**El mapa del algoritmo** {YB}: en la página FM, **un toque al pad 7** fija el mapa (otro toque lo quita; el pad 7 brillante mientras se ve) y **mantenerlo ½ s** lo enseña solo mientras lo mantienes; desde otra página, un toque abre la página FM. El mapa usa los pads 9-32:

- **Cada fila se lee de izquierda a derecha: la onda de la izquierda modula a la de su derecha**, y la última de la derecha es una **portadora** (la que se oye). **Un hueco oscuro = no interactúan**. Un operador que modula a varios aparece en cada cadena (copias). Las cadenas largas van primero.
- **El color dice la relación armónica del ratio**: **verde** = entero (armónico: 1, 2, 3…), **verde azulado** = x,5 (media octava de los enteros: 0,5, 1,5…), **naranja** = cualquier otro (inarmónico, de campana), **rojo** = frecuencia fija; el operador con **feedback**, **violeta**. **Brillante** = nivel de salida de la mitad o más (el feedback, de la mitad o más); **tenue** = menos.
- **Un toque a un operador lo elige** (los knobs lo editan, como los pads 9-16): **todas sus copias laten**.
- **Shift + operador** = callado mientras ves el mapa (apagado; para oír qué aporta). No se guarda: al cerrar el mapa vuelve a sonar.
- **Mantén un operador**: late, a los que modula se ven en **blanco**, los que le modulan normales y el resto tenue. **Mantén uno y toca otro** (cualquier copia) = **el primero modula al segundo, o deja de hacerlo**: un **algoritmo propio** del patch (el mapa se redibuja al soltar). Un operador que no modula a ninguno pasa a ser portadora; un enlace que cerraría un bucle no se hace. El algoritmo propio se guarda con el patch y con el proyecto; **Shift + K1** (o la lista) vuelve a uno de los 56 (el propio se pierde).

**Knobs con un operador elegido:**

| Knob | Solo | Con Shift |
|---|---|---|
| K1 | **Ratio**: 0,5, 1 … 31, después fijo 1 / 10 / 100 / 1000 Hz (rojo); 3 clics por paso | **Algoritmo** (56, de todo el motor; 16 clics por paso). Al girarlo los pads enseñan los algoritmos 1,5 s (los 16 antiguos en los pads 9-24, los 32 del DX7 en los 32 pads, los 8 de 8 operadores en los pads 1-8) |
| K2 | **Fino** (0-99) | **Feedback** (0-127, de todo el motor) |
| K3 | **Nivel de salida** (0-99) | **Rate scaling** (0-7: las notas agudas más rápidas) |
| K4 | **Sensibilidad a la velocity** (0-7, 4 clics) | **Level scaling** (centro = ninguno; derecha = las notas agudas más bajas, izquierda = las graves) |
| K5-K8 | **Rates R1-R4** de su envolvente (0-99) | **Niveles L1-L4** (0-99) |

**Knobs con la envolvente de pitch (pad 3):** K1 transposición (0-48, 24 = ninguna), K3 ruido (0-127), K4 el operador del ruido (1-8, 16 clics), K5-K8 R1-R4; con Shift K1 / K2 como arriba y K5-K8 L1-L4 (50 = sin desplazamiento).

- **La envolvente** sube por R1 a L1, R2 a L2, R3 a L3 y se queda en L3 mientras la nota sigue; al soltar va por R4 a L4. Como en el DX7: rate 99 = inmediato.
- **Clear + knob** = el valor inicial; **Clear + pad 7** = una voz tocable del algoritmo elegido; **Clear + MIDI 1 / 2** = todo el motor a los valores iniciales.
- **Los patches de la Beta 5.19 o anterior** (FM de 4 operadores) se cargan convertidos: mismos algoritmos, ratios, niveles y envolventes, el mismo sonido.
- **Se guarda con los patches del sinte propio**: el FM de cada patch va en una ranura extra del mismo banco de la tarjeta (`Patches/NN_PATCHBANK.cpb`), después de los 8 patches de stock; el banco crece hasta 8 KB. Intercambiar patches (Duplicate + A + B) o copiarlos de otro pack lleva el FM con ellos.
- **Se guarda con el proyecto**: el FM de MIDI 1 / 2 va en los ajustes de los patrones de Synth 1 / 2 (sin cambiar nada de ellos); al cargar un proyecto vuelve su sonido.
- **Patches de ejemplo**: [81 patches del sinte propio listos](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/tree/main/docs/patches) (33 sonidos clásicos y los 48 instrumentos FM), cada uno con los destinos de la página 4 y de Shift + pad 4 elegidos para su sonido; súbelos con la app de la tarjeta (**Parches custom → Subir .ctm**) y cárgalos aquí.
- **Components**: leer el pack y mandar un patch no tocan el FM. **«Send patches» / «Send pack»** cambian los patches de stock como siempre y **el aparato devuelve los patches propios y el FM** a cada banco (antes se perdían); si Components borra un banco que tiene patches propios, queda con los 8 patches de stock vacíos. No en el pack interno. Una copia guardada por Components (su zip) no lleva los patches propios: la copia de la app de la tarjeta (Snapshot) sí.
- Polifonía, unísono y glide como el FM de 4 operadores (capítulo «Voces»). No tiene CC / NRPN.
""", [])

view("midi-cc", "III", "Editor de CC de los macros MIDI (pad 25)",
     "Vista Preset de MIDI 1 / 2, **pad 25**: cambia desde el aparato qué CC / NRPN manda cada macro knob de la plantilla.",
     """
1. **Pad 25** (se enciende). 2. **Mueve un knob**: queda elegido y su número se dibuja con los pads.
3. **Octave ▼ / ▲**: campo siguiente / anterior. 4. **Gira el knob** para cambiar el valor.
5. **Guardar:** pad 26, o Octave ▼ hasta el paso de guardar (pad 26 y Save parpadean) y Octave ▼ otra vez. Al guardar sales del editor a la vista Preset.
6. **Descartar:** cualquier botón de vista, el pad 25 o un pad de plantilla.

| Número del primer campo | Tipo | Campos |
|---|---|---|
| cualquier otro | CC | número, inicio, fin |
| 99, 98 o 6 | NRPN de 7 bits | número, MSB, LSB, inicio, fin |
| 38 | NRPN de 14 bits | número, MSB, LSB, inicio (MSB, LSB), fin (MSB, LSB) |
""")

view("step-drummer", "III", "Vista del step-drummer",
     "MIDI 1 / 2: vista Preset con el motor encendido, **pad 30** (*desde RC4*: con el step-drummer encendido, **Note** pasa por Note → Note ampliada → step-drummer). Synth 1 / 2: vista de la fuente, **pad 30**. Secuencia por pares de pasos sobre el patrón.",
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
- Con el motor en **secuenciador de efectos** (azul), cada knob elige un hueco de la fila inferior de Master FX: 0 nada, 1-5 pads 26-30, 6 el pad 31, y al final **random** {B} (LED blanco: uno al azar entre los que tienen efecto). Avanza despacio (un hueco cada ~48 pasos de giro). Un hueco sin efecto asignado no hace nada; *desde RC4*: toca **el efecto de arriba de su columna** (pad 26 = pad 1 de Master FX … pad 30 = pad 5), con sus knobs, y su LED se ve en ese color.
""".replace("{B}", B), [("step-drummer", 0), ("fx-seq", 0)])

view("midi-muestra", "III", "Modo muestra y selector de samples",
     f"{B} MIDI 1 / 2 con el motor en **muestra** (pad 27 verde azulado, tras el granular): **Note dos veces** (vista Note ampliada). La pista toca un sample del pack de un golpe, a la altura de cada nota.",
     """
| Control | Función |
|---|---|
| Pads 17-32 | 16 samples del pack: tocar = el sample de la pista (verde azulado) y suena; los demás tenues. {XB} **Shift + sample** = elegirlo sin que suene; **Shift + el ya elegido** = elegir el segundo sample (estéreo; ver abajo). |
| Octave ▼ / ▲ | Página siguiente / anterior de samples (4 páginas = los 64 del pack; encendido si hay más en ese sentido). |
| Pads 1-16 | Los 16 pasos de la mitad mostrada: melocotón = con sample flip, verde azulado tenue (el fondo) = sin, blanco = el que suena. **Mantener un paso + tocar un sample** = su flip (el paso verde, su sample amarillo); también **mantener un sample + tocar pasos** (desde RC2.04); **Clear + paso** = quitarlo. {XB}: un flip en un paso **sin nota** añade allí **la última nota que tocaste** en la pista (60 si aún ninguna; un paso de largo, velocity 100), para que suene; los pasos se ven **melocotón** = nota con flip, **verde azulado** = nota sin flip, **violeta** = flip sin nota, verde azulado tenue = nada. {XB} En la **vista Note** la nota añadida se ve al momento y los pasos con nota y flip se ven en **melocotón** (un flip sin nota solo se ve aquí). |
| 1-16 / 17-32 | La otra mitad del patrón. |

- **La altura:** C3 (nota 60) = el sample como se grabó; una octava arriba = el doble de rápido. Las notas vienen de la vista Note normal, el step-drummer o el MIDI de entrada.
- **Un golpe:** el VCA se queda abierto y el sample suena hasta el final; cada nota nueva lo vuelve a empezar (una voz por pista). Filtro, efecto y LFO de las páginas del motor siguen.
- **Estéreo** {XB}: **K7 de la página OSC 1** ({YB} K3; WAVE, que en este modo no hacía nada) = la **anchura estéreo**. A la izquierda del todo, mono como siempre; al girarlo, cada nota toca el sample elegido a la **izquierda** y el **segundo** a la **derecha** (de entrada el siguiente, N + 1; el 64 sigue con el 1): un sample estéreo son dos huecos del pack (los samples del aparato son mono). **El segundo se elige en el selector:** **Shift + el sample ya elegido** pasa a elegir el segundo (parpadea en verde azulado; el primero se ve violeta): tocar un sample = el segundo y suena; **Shift + el segundo** vuelve al primero. Se guarda la **distancia** entre los dos: al cambiar el primero (o con un flip en un paso) el segundo lo sigue. Con la anchura subida, el segundo se ve violeta. La nota dura lo que el **más largo**: el corto se calla al acabar. Con la misma altura los dos. El centro sigue el camino de la pista (filtro, efecto, nivel, panorama, envíos); la parte estéreo pasa por el mismo filtro y sigue el VCA, el nivel, el panorama, el mute y el sidechain de la pista, pero no el efecto ni los envíos. Se enciende con cada nota: girar el K7 desde 0 durante una nota vale para la siguiente. La captura suena siempre en mono.
- **En vivo:** con **Record + Play**, tocar un sample graba una nota 60 en el paso que suena con su flip.
- **Borrar la nota de un paso con flip** {XB} (en la vista Note: Clear + paso, o el paso mantenido + la tecla de su nota) borra la nota y **deja el flip**, que solo se ve aquí (violeta); Clear + paso en este selector quita el flip.
- El sample de la pista es la misma fuente que la del granular (Shift + K8 en su página; la captura se elige allí).
- Los flips van en el carril de la automatización de nivel de la pista (Mixer): un flip sustituye el nivel grabado en su paso; grabar el nivel encima borra esos flips.
""".replace("{B}", B).replace("{XB}", XB), [("modo-muestra", 0)])

# ===================================================================================================== IV
view("drum-pista", "IV", "Vista de pista de un drum (knobs)",
     "Pulsa **Drum 1-4**. Cada knob hace lo que dice su etiqueta, con una segunda capa en Shift.",
     f"""
| Knob | Solo | Con Shift |
|---|---|---|
| K1 Oscillator | Pitch ({B}: el de stock, continuo como el original; los pads de la vista cromática transponen encima) | Cantidad de la envolvente de tono |
| K2 Osc mod | Frecuencia del ring mod | Cantidad del ring mod |
| K3 Amp envelope | **Izquierda: decay** (el de stock). Pasado el máximo, **derecha: ataque** (fundido de entrada, hasta 1 s). Centro neutro. {B} | **Izquierda: inicio** del sample; **derecha: corte** desde el final (hasta 120/128 cada uno; *desde RC2.10* el inicio recorre todo el sample: antes llegaba al final a un cuarto del recorrido y más allá el golpe no sonaba). Centro = el sample entero. {B} |
| K4 Filter envelope | Envolvente → corte | Forma de la envolvente |
| K5 Filter frequency | Filtro / EQ (por defecto, el EQ tilt de stock) | **Modo de filtro**: EQ tilt de stock, paso banda, notch, comb (no en la {YBETA}: ahí suena el EQ tilt), DJ |
| K6 Resonance | Resonancia | — |
| K7 Modulation | Cantidad del LFO: derecha = trémolo; izquierda = vibrato ({XB}: izquierda = **scan del inicio**: cada golpe empieza donde está el LFO, desde el inicio de Shift + K3 hasta un 64avo del sample más allá por cada paso del knob (a la izquierda del todo, todo el sample), sin pasar el corte; el LFO ya no vuelve a empezar con cada golpe) | Velocidad del LFO (bipolar {XB}: derecha libre, izquierda a tempo; 0.2; a tempo, el scan empieza en el inicio en el primer tiempo) |
| K8 FX | Distorsión; a la izquierda de 0, **bitcrush** | **Tipo de distorsión**: stock, suave, dura, plegada |

- **K3:** girando a la izquierda el ataque vuelve a 0 antes de que baje el decay; con Shift, uno de los dos (inicio o corte) vuelve a 0 antes de que se mueva el otro. LED: ataque en blanco; con Shift, inicio en el color del drum, corte en blanco.
- **Clear + K3 a la derecha** pone a 0 ataque, inicio y corte; **Clear + K8 a la derecha** quita también el bitcrush {B}. Clear + knob restablece las dos capas en los demás.
- **Clear + el botón del drum** {B} (con una de sus vistas en pantalla): los ocho knobs del drum, con su capa Shift, a sus valores por defecto.
- **Foto de los knobs en un paso** {YB}: en la vista de pista del drum (Note), **Record mantenido + un pad de paso** (pads 1-16; con 17-32, los pasos 17-32) escribe en ese paso el **pitch, el decay, la distorsión y el EQ** que no estén en su valor por defecto (el de Clear + knob a la derecha), cada uno en su carril. Los knobs nuevos del mod no tienen carril y no entran. El golpe del paso no cambia y Record queda como estaba. {YB} También el valor del **carril extra** si no está en su valor por defecto. {YB} Mientras mantienes el paso, se ve en **amarillo**.
- **Carril extra** {YB}: cada drum tiene **un carril de automatización más**, guardado en el propio patrón (viaja con Duplicate, Nudge y Shift + Play). De fábrica lleva el **pitch cromático**: los pads de la vista cromática graban ahí y el carril de pitch queda para K1. **Record mantenido + un knob** le asigna ese parámetro: K2 (frecuencia del ring mod), K4 (envolvente → corte), K6 (resonancia), K7 (cantidad del LFO), Shift + K1 (envolvente de tono), Shift + K2 (cantidad del ring mod), Shift + K4 (forma de la envolvente) o Shift + K7 (velocidad del LFO); **Record mantenido + un pad de la vista cromática** = otra vez el pitch cromático. Record queda como estaba. Mientras mantienes Record, el knob asignado se ve **blanco** (con el pitch cromático, **Preset parpadea** en blanco). Grabando, girar ese knob escribe el paso que suena (un valor por paso); **Clear + ese knob a la izquierda** borra el carril en el patrón que suena (el pitch cromático: Clear + K1). La asignación se guarda con el proyecto; los valores, con el patrón.
- **Bloqueos de estado** {YB}: **Record mantenido + 1-16/17-32** en cualquier vista de un drum cambia su carril extra entre el **carril** (lo de arriba) y los **bloqueos de estado**; al cambiar, el carril se borra en los 8 patrones del drum (al volver lleva el pitch cromático). En bloqueos de estado, cada paso puede guardar un **estado**, los **14 valores de los knobs nuevos** del drum a la vez (los ocho que puede llevar el carril, el modo de filtro, el bitcrush, el tipo de distorsión y el ataque, el inicio y el corte de K3) a 16 niveles cada uno (0, 64 y 127 exactos), o quedar **dentro de una rampa**: los valores pasan poco a poco del estado de antes al de después, micropaso a micropaso (el modo de filtro y el tipo de distorsión cambian al llegar). Grabando, girar uno de esos knobs guarda un estado en el paso que suena; cuando tres seguidos quedan en línea recta, el del medio y los pasos entre ellos se vuelven rampa: de un barrido quedan el inicio, las paradas y los giros. **Record mantenido + un paso** = un estado con los valores de ahora; **Clear + un knob del carril a la izquierda** borra el carril del patrón que suena. Mientras mantienes Record, los **8 knobs en blanco**. Hasta 80 estados por proyecto (se guardan con él; los que ya no usa ningún paso se reutilizan).
- **Vista de automatización** {YB}: la **vista Velocity de un drum con Shift** mantenido, o fijada pulsando **Velocity otra vez** en ella (otra vez = se quita; también al salir de la vista). Los pasos con **automatización** se ven en **amarillo**: algo en los carriles de pitch, decay, distorsión o EQ, o en el carril extra; en bloqueos de estado, los de rampa en **amarillo tenue**; los **marcados, en rojo**; los demás conservan su color. En los drums, la velocity fija queda en **Shift + Velocity** (Velocity dos veces fija esta vista).
  - **Shift + un paso amarillo** = sus valores en los knobs y en el sonido (los carriles de stock por la misma ruta que la reproducción; el pitch cromático; el parámetro del carril extra; un estado, los 14 valores), y **los knobs que mueve en amarillo**, hasta soltar Shift: al soltarlo todo vuelve exactamente a como estaba. Pulsar otro paso amarillo mientras tanto escucha ese.
  - **Shift + un paso sin automatización** = lo **marca** (rojo; otra vez = lo desmarca): al sonar ese paso, el **pitch, el decay, la distorsión, el EQ** y el parámetro del carril extra (si lleva un knob) **vuelven a los valores guardados en el proyecto**. La marca va en el carril extra del paso (sus valores llegan ahora hasta 124 de 126).
  - **Clear + un paso** (con la vista fijada, o Clear antes que Shift, porque Shift + Clear es el metrónomo) = **borra su automatización** (los cuatro carriles y el extra, también la marca) y **deja el golpe**.
  - En **bloqueos de estado**: **mantener un paso** lo escucha (con Shift o con la vista fijada) y **tocar otro** mientras tanto = una **rampa** entre los dos (la escucha se quita antes, así el extremo sin estado toma los valores de los knobs); Shift + un paso sin estado lo marca y queda mantenido.
- Con todo en neutro un sample suena como en el original. Todo se guarda con el proyecto y tiene NRPN.
- **Sidechain entre drums:** Shift + FX y Octave ▼ (8.1).

### Pareja estéreo {XB}
**Mantén Drum 1 y pulsa Drum 2** (o al revés; Drum 3 + Drum 4 igual): los dos drums pasan a ser una **pareja estéreo**; el mismo gesto la deshace. No con Shift, Clear o Duplicate pulsados, ni en Setup.
- **Drum 1 / 3** suena a la izquierda y **Drum 2 / 4** a la derecha con el **sample siguiente** del pack (un sample estéreo = dos huecos seguidos; tras el 64, el 1).
- **Todo lo de Drum 1 / 3 vale para los dos:** sus knobs (también con Shift), su patrón (pasos, sample flips, micropasos, automatización, arpegio, rollers), su nivel, sus envíos y su sidechain. Su panorama es el centro de la pareja.
- **El patrón de Drum 2 / 4 no suena** mientras dura la pareja (se queda guardado). Sus pads y sus notas MIDI lo tocan solo, a la derecha.
- **Elegir otro sample en Drum 2 / 4** (su vista Preset) fija la distancia entre los dos; después sigue los cambios de sample de Drum 1 / 3.
- **Los knobs de Drum 2 / 4** son desviaciones sobre Drum 1 / 3 (sus propios valores no cambian y vuelven al deshacer la pareja):

| Knob | Solo | Con Shift |
|---|---|---|
| K1 | Desafinación (± 100 cents) | Cantidad de la envolvente de tono |
| K2 | **Apertura estéreo** (de fábrica, del todo: izquierda / derecha; a la izquierda del todo, los dos al centro) | Cantidad del ring mod |
| K3 | Decay | Inicio del sample |
| K4 | Envolvente → corte | Forma de la envolvente |
| K5 | Filtro / EQ | — (el modo de Drum 1 / 3) |
| K6 | Resonancia | Frecuencia del ring mod |
| K7 | Cantidad del LFO | — (la velocidad de Drum 1 / 3) |
| K8 | — (la distorsión de Drum 1 / 3) | — |

- LEDs: las desviaciones en el color de Drum 1 / 3 (más brillo = más desviación), la apertura en blanco. **Clear + knob** = sin desviación (la apertura, del todo).
- El botón de Drum 2 / 4 late en el color de Drum 1 / 3 mientras dura la pareja.
- **Se guarda con el proyecto** (encendida, distancia, apertura y desviaciones).
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
- Grabando, cada tono se graba solo en su paso. {B}: los pads transponen en semitonos sobre el pitch de K1 y, grabando, quedan en su paso dentro del carril de pitch del drum (un paso guarda un giro de K1 o una nota cromática); Clear + K1 a la izquierda (sostenido) borra los dos. {YB} Con el **carril extra** en el pitch cromático (de fábrica), los pasos grabados van a ese carril y el carril de pitch queda para K1 ([vista de pista de un drum](#drum-pista)). {ZB} Grabando (Record + Play), **cada pad graba un golpe con su tono** en su paso, como un pad de la vista Note: el micropaso de la pulsación y su velocity (en un paso vacío, probabilidad 7); en un paso que ya tiene golpe, se suma el micropaso y el tono pasa a ser este. Los pasos sin tono grabado suenan con el pitch de K1. **Shift + Play** (cuantizar) mueve el tono con su golpe. (Antes solo se guardaba el tono, en el paso que sonaba: caía en el golpe de otro paso o en un paso sin golpe.)
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
| 26 | **Nudge** (azul): el primer paso elegido pasa a ser el paso 1; lo de delante va al final (pasos y automatización, sobre 16 o 32). {XB}: un toque = el tramo un paso atrás, Shift + pad 26 adelante, con el primer y el último paso. {ZB} **Un toque = el contenido del tramo elegido (primer a último paso) un paso atrás**, **Shift + pad 26 = un paso adelante**: lo que sale por un extremo del tramo entra por el otro y **el primer y el último paso no se mueven**. |
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
- **Entrada:** la primera nota suena como siempre; al mantener otra a la vez empieza el arpegio de las notas mantenidas, una por paso de arpegio (con el transporte parado, al tempo del proyecto; desde RC2.10: antes, parado, iba siempre a unos 120 BPM), hasta soltarlas todas; cada nota dura un paso de arpegio. **Con Record se graba el acorde**, no las notas sueltas: el arpegio lo toca después la secuencia.
- **Orden pulsado** {XB}: las notas se arpegian en el orden en que se pulsaron (un acorde grabado, en el orden de sus notas en el paso), no por altura; arriba, abajo, ping-pong, aleatorio, fractal y deconstruido recorren ese orden. Al soltar una nota su hueco queda vacío y se salta; la siguiente nota que pulses ocupa el primer hueco vacío antes de ir al final.
- **Paso mantenido** {XB}: con el transporte parado, **mantener un paso** con varias notas las arpegia, como si mantuvieras sus pads (antes sonaban a la vez), hasta soltarlo; si arrancas el transporte con el paso mantenido, el arpegio se para al soltarlo.
- **Teclado externo** {XB}: con el **botón Note de la vista Setup** encendido, las notas que llegan por MIDI al canal de una pista de notas con el arpegiador encendido se arpegian como los pads (la primera suena como siempre; con Record se graba el acorde). **Apagada de fábrica**, para no chocar con un teclado que tenga su propio arpegiador.
- **Random-mutate** {XB}: si el paso del acorde tiene nivel de random-mutate, cada nota del arpegio pasa por él (otro grado de la escala, una octava arriba o abajo) como las notas normales; no se escribe nada en el paso. El arpegio en vivo (las notas mantenidas) usa el nivel del paso en que está la pista (en marcha, el que suena; parado, donde se quedó).
- **Notas largas al grabar** (desde RC2.04): el grabador de stock corta las notas a 16 pasos; ahora una nota o un acorde mantenido más tiempo sigue, ligado, 16 pasos después (en patrones de más de 16 pasos), así que el arpegio de un acorde mantenido no se para en el paso 16. Vale para toda nota de Synth 1 / 2 y MIDI 1 / 2, con arpegiador o sin él.
- Se guarda con el proyecto, por pista y patrón.

#### Modificadores del arpegio {XB}
Con el arpegiador del patrón **encendido**, **Shift + pads 1-16** eligen cuatro modificadores (con el arpegiador apagado, Shift + pad sigue siendo el primer paso de stock). Cada grupo tiene su color; la opción elegida brillante, las otras tenues:

| Pads | Grupo (color) | Opciones |
|---|---|---|
| 1-4 | **Octavas** (arena) | sin ampliar · +1 octava · +1 arriba y 1 abajo · +2 arriba y 1 abajo (con el orden abajo, de agudo a grave; con los demás, de grave a agudo) |
| 5-8 | **Cuándo cambia la octava** (azul cielo) | al terminar cada vuelta · en cada nota · cada 3 notas · cada 4 notas |
| 9-12 | **Groove** (ámbar) | ninguno · nota / nota con puntillo (1 y 1,5 pasos) · swing (2:1) · cada nota dos veces |
| 13-16 | **Reinicio** (rosa) | sin reinicio · tras una vuelta entera, 1 / 3 / 5 notas más y vuelve al principio (y otra vuelta entera) |

- Las octavas se cuentan sobre lo que sale del groove y del reinicio (con «dos veces», cada repetición cuenta como una nota).
- Valen para el arpegio de un paso, de las notas mantenidas y del teclado externo, parado o en marcha. Se guardan con el proyecto, por pista y patrón.

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
- **Pad 31 = longitud fija** {B} de la pista (azul = encendida): con los dos apagados, abre el **selector** (pads 17-32 = 1 … 16 pasos, como la vista Gate) y **elegir una longitud la enciende** (y cierra el selector). Con ella, toda nota introducida a mano (no la grabada en vivo) lleva ese gate, también todas las de un acorde y sueltes antes el paso o la nota (desde RC2.08: antes solo si se soltaba primero la nota).
- **Los dos toggles** {B}: con uno encendido, **pulsarlo otra vez lo apaga** (sin abrir nada); **pulsar el otro** apaga el primero y enciende el nuevo (el pad 31, abriendo su selector).
- Esos gates los usa también el arpegiador: cada nota del acorde dura el suyo.
""")

view("probabilidad", "V", "Vista de probabilidad (pistas de notas y drums)",
     "**Pattern Settings dos veces** o **Shift + Pattern Settings** (modo 1), o el **pad 25** de Pattern Settings (modo 2). Mantén un paso con notas y toca un pad de las filas 3-4.",
     f"""
| Modo | Fila 3 | Fila 4 |
|---|---|---|
| Modo 1 | Probabilidad del paso | **Frecuencia**: el paso suena en la última de cada n vueltas (1-8), amarillo {B} |
| Modo 2 (pad 25) | **Dinámicas** aleatorias {B} | Random-mutate {B} |

### Modo 2 {YB}
Las dos filas son una sola botonera, por paso:

| Pad | Qué hace |
|---|---|
| 17 | Sin cambios de nota ni de octava (blanco) |
| 18 / 19 / 20 | **Otra nota de la escala**, en la misma octava: probabilidad ×1 / ×2 / ×4 (melocotón) |
| 21 / 22 | **Una octava arriba**: probabilidad baja / alta, ×1 / ×2 (arena) |
| 23 / 24 | **Una octava arriba o abajo**, al azar: probabilidad baja / alta, ×1 / ×2 (arena) |
| 25 | **Sin dinámicas** (blanco) |
| 26 | **Dynamics lo (ghost)**: velocity de −32 a 0; la longitud no cambia {YB} |
| 27 | **Dynamics hi + longitud (accent staccato)**: velocity de 0 a +64 y la nota se acorta en proporción (+64 = la mitad) {YB} |
| 28 | **Longitud**: el gate de la mitad al doble, al azar; la velocity no cambia {YB} |
| 29-31 | Sin función (apagados) |
| 32 | **Micropasos** encendidos / apagados (verde azulado): la nota se adelanta o se atrasa 0, 1 o 2 micropasos, sin salir de su paso |

- **Octave ▼ / ▲ con esta vista abierta = el factor de la pista**: ×0, ×1, ×2, ×4 u ×8 (de fábrica ×1; Octave lo dobla o lo parte por la mitad) {YB}, que multiplica todas sus probabilidades. Los pads enseñan el número 0,6 s; el Octave que ya no puede moverse se apaga. Se guarda con el proyecto.
- **Probabilidades con el factor ×1:** nota y octava, 6 % por cada ×1 del pad; dinámicas y micropasos, 25 %. Con ×4: 25 % y 100 %. Con ×0 no cambia nada.
- **Con ×8, el pad 24 cambia todas las notas:** la del paso ya no suena nunca y solo quedan una octava arriba y una abajo. El sorteo es mitad y mitad, pero sin la nota original de referencia el oído toma la de abajo como base y parece que casi todas suben. Con el pad 22 suben todas.
- Nota, dinámicas y micropasos se sortean aparte, y cada nota de un acorde aparte; los micropasos, una vez por paso. Una nota en el primer micropaso no puede adelantarse, ni en el último atrasarse. Sin Record cambia solo esa vez; con Record y esta vista en pantalla se escribe en el patrón de esa pista (la secuencia deriva). Las ligadas no cambian de nota, longitud ni micropaso.
- Un proyecto de una versión anterior conserva los valores de sus pasos, que ahora significan lo de esta tabla; un factor guardado de ×3 suena como ×2, y ×5-×7 como ×4.

### Modo 2 en los drums {YB}
La misma botonera sobre el paso elegido (pads 1-16) y el mismo Octave (el factor del drum):

- **Pads 18-20:** otro sample de su fila de 8 (±1). **Pads 21 / 22:** la fila siguiente (+8), probabilidad baja / alta. **Pads 23 / 24:** una fila más o menos (±8), probabilidad baja / alta. Parte del sample flip del paso, o del sample elegido; no se graba.
- **Pads 25-27:** {YB} uno de los tres a la vez por paso (el mismo otra vez lo quita), con probabilidad de 25 % × factor. **Pad 25 = sin dinámicas.** **Pad 26 = dynamics lo**: el golpe baja su velocity de 0 a −32 y se repite con un roller, uno de los dos al azar: en el micropaso 4, o en los 3 y 6. **Pad 27 = dynamics hi**: la velocity sube de 0 a +64, sin roller. Las repeticiones llevan la velocity y el sample del golpe y solo suenan las que caben en el paso. El pad 28 está apagado.
- **Pad 32:** micropasos de **todo el drum**, no del paso (el paso no tiene bits libres): {YB} con la misma probabilidad, el paso entero se adelanta o se atrasa 1 o 2 micropasos sin salir de él (un golpe en el primer micropaso solo se atrasa, en el último solo se adelanta; un paso con golpes en el primero y el último no se mueve). Funciona también en un paso sin nada elegido.

### Random-mutate en las RC (fila 4)
| Pad | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 |
|---|---|---|---|---|---|---|---|---|
| Octava | — | 6 % | — | 6 % | — | 12 % | — | 25 % |
| Escala | — | — | 6 % | 6 % | 12 % | — | 25 % | 50 % |

- Escala = otra nota de la escala en la misma octava; octava = una arriba o abajo. Cada nota de un acorde se sortea aparte. Sin Record cambia solo esa vez; con Record se escribe (la secuencia deriva). Las ligadas no cambian.

### Dinámicas en las RC (fila 3, modo 2)
| Pad | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| Micropasos | — | ±2 | ±2 | — | −1 a +3 | −1 a +3 | — | — |
| Velocity | — | — | 0 a +32 | 0 a +32 | 0 a +32 | — | ±32 | −32 a +64 |

- Con Record y el modo 2 en pantalla, lo que suena (nota mutada, dinámica) se escribe en el patrón de esa pista {ZB} *(antes, también en las demás pistas de notas)*. Todo se guarda con el paso.

### En los drums {B}
La misma vista para un drum: **Pattern Settings dos veces** (modo 1) o el **pad 25** de su Pattern Settings (modo 2, melocotón; verde si su arpegiador está encendido). Elige un paso con golpe (pads 1-16) y toca un pad de las filas 3-4.

| Modo | Fila 3 | Fila 4 |
|---|---|---|
| Modo 1 | Probabilidad del paso (stock) | **Frecuencia** (1-8), amarillo |
| Modo 2, en las RC | **Dinámicas** (los mismos 8 niveles) | Pads 25-28: **random-mutate del sample** |

| Pad | 25 | 26 | 27 | 28 |
|---|---|---|---|---|
| Random-mutate en las RC | — | 25 % ±1 (el sample de al lado en su fila de 8) | 25 % ±8 (el de la misma columna en otra fila) | 12 % de cada uno |

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
| **Shift + toque a Duplicate** {YB} | **Mutate de patrones** (de [Rhythm Plus de mefisme](https://github.com/mefisme/rhythm-plus)): cada pista elegida toca en bucle una lista corta de patrones de su cadena en otro orden; los patrones no cambian. En su columna se apagan los que no están en la lista (el que suena, con su color). Otro toque = otra lista. También en el Mixer. Con Shift, Duplicate en amarillo. |
| **Shift + Duplicate mantenido** {YB} | **Ajustes del mutate** (melocotón: el elegido brillante): columna 1 Length 1-4, 2 Length 5-8, 3 tipo de longitud (como la cadena / exacta / al azar hasta Length), 4 y 5 Amount en ocho pasos (columna 4 de arriba abajo todo, 7/8, 6/8, 5/8; columna 5 la mitad, 3/8, 2/8, 1/8 de los huecos de la cadena cambian), 6 Repeats (sí / no: dos vecinos nunca iguales), 7 Keep slot 1 (no / sí). Botones de pista: brillante = elegida. Duplicate cierra. Un ajuste nuevo se oye al momento; volver al valor de antes devuelve la misma lista. |
| **Clear + Duplicate** {YB} | En cualquier vista: las listas terminan y las pistas vuelven a sus cadenas. Un pad de patrón también termina la lista de su pista. |

- Ejemplos: n = 3 → A A A B A A A C; sin C → A A A B; n = 1 → A B A C. B y C suenan una vez y la pista vuelve a A (salvo que tengan regla).
- Las reglas viajan con el patrón (al duplicarlo); el modo, con el proyecto y con cada escena (9.2).
- **Mutate y escenas** {YB}: guardar una escena guarda qué pistas mutan, la semilla y los ajustes; al volver a la escena (sonando o parado desde el Mixer) vuelve la misma lista. Una pista que muta no sigue las reglas de cadena; las demás sí. Cambiar la cadena de una pista sonando rehace su lista con la misma semilla. **Para una pista que muta, la cadena termina con el último patrón de su lista**: con escenas encadenadas, la escena cambia al acabar la lista entera.
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
| **Pad 16 mantenido + pads 1-8** {YB} | **Solo**: se guardan los mutes del Mixer, las pistas que pulses siguen sonando y se silencian todas las demás. El pad 16 queda en **blanco** mientras el solo está activo; mantenerlo otra vez con otras pistas las pone en solo a ellas. **Un toque al pad 16** solo (sin pistas) vuelve a los mutes de antes del solo. |
| **Toque al pad 16 sin solo** {YB} | **Solo flip**: el pad 16 en **naranja**. Mientras mantienes una o varias pistas (silenciadas o no), suenan solo ellas; al soltarlas, el Mixer vuelve a como estaba. Pad 16 mantenido + pistas = solo (sale del flip); otro toque al pad 16 sale. Cargar otro proyecto apaga el solo y el flip sin tocar sus mutes. |
| **Shift + pads 1-8** {B} | **Silenciar / activar esa pista en el compás siguiente**: el pad parpadea mientras espera; otra vez lo cancela. Parado, al momento. |
| **Shift + pads 9-16** | **Repeticiones** de la escena actual (1-8; con Shift la fila en amarillo, la elegida en verde). {B} Sonando, con Shift, **la repetición que suena en blanco** (pad 9 = la primera vez; en la última, el pad verde parpadea blanco / verde). {XB} |
| Pistas que parpadean | Están siguiendo una regla de cadena. {B} |
| **Mixer** otra vez | Master FX. {YB} Mantenido ½ s o más: Master FX solo mientras lo mantienes, al soltar vuelve el Mixer (y desde Master FX, al revés). |

- Una escena termina cuando termina su cadena más larga. Guardar otra vez una escena no cambia sus repeticiones.
- **Modo cue** {B}: la **salida izquierda** lleva la mezcla en mono como siempre y la **derecha** solo las pistas en cue, cada una a su envío. Una pista silenciada en cue suena solo por la derecha, en el paso en que va su patrón; su pad sigue tenue y su pad (o Shift + pad, al compás siguiente) la mete o la saca de la mezcla. Los paneos no se tocan y vuelven al apagar el modo; guardar el proyecto guarda los mutes de la mezcla. La reverb, el delay y Master FX son los de la mezcla: el cue también los oye.
- **Escucha previa en el cue** {XB}: con el modo cue encendido, elegir un patch de Synth 1 / 2 en su vista Preset (toque normal o con Shift) y **Shift + sample** en la vista Preset de un drum (en el original, la selección silenciosa) se oyen **solo en el cue** (derecha): mientras mantienes el pad y 0,8 s después, esa pista va solo al cue (también su patrón, en ese momento). El toque normal de un drum sigue sonando en la mezcla, y cualquier golpe en vivo de ese drum (sus pads, MIDI, el patrón) lo devuelve a la mezcla antes de sonar.
- **Metrónomo en el cue** {XB}: con el modo cue encendido, el clic del metrónomo (Shift + Clear) y el de la cuenta atrás suenan **solo en el cue** (salida derecha): la mezcla de la izquierda sale sin clic. Sin el modo cue, por las dos salidas, como siempre.
""", [("mixer-shift", 0)])

view("master-fx", "VI", "Master FX",
     "**Mixer** y **Mixer** otra vez. Efectos sobre la salida master, el song pointer, el sample capturado y la fila de efectos asignables. Cualquier otro botón de vista sale.",
     f"""
### Pads
| Pad | Función | K1-K4 al pulsarlo |
|---|---|---|
| 1 | Gater | división, profundidad, ancho, suavizado |
| 2 / 3 | Auto-Filter paso bajo / alto | velocidad (bipolar {XB}: derecha libre, izquierda a tempo), profundidad, resonancia, centro |
| 4 | Digitise | muestreo, bits; **K3 = envío momentáneo al delay** mientras mantienes el pad, **K4 = envolvente de la cantidad** {B} (*desde RC4.02* arreglada: en RC4 y antes no arrancaba) |
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
- **El bucle sigue al cambiar de proyecto o de pack** {YB}: con el bucle enganchado sonando, carga otro proyecto u otro pack (con el transporte parado, como siempre): el bucle sigue sonando, con su tono y sus puntos. **Play** no arranca enseguida: parpadea en verde y el proyecto nuevo empieza justo cuando el bucle da la vuelta, a tiempo con él; **el bucle sigue sonando** (con sus knobs) y se para como siempre (pad 7, pad 8). **Play otra vez** mientras parpadea = empieza ya. El sample capturado no se borra. Sin un bucle enganchado, cargar funciona como siempre. Los samples capturados que un pack guardó (los drums sustituidos por una captura) se cargan como drums y no tocan el bucle.
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
| **Shift + Octave ▲ / ▼** *(desde RC4)* | Resonancia del filtro master +16 / −16; se para en 127 / 0 (con Shift, Octave en amarillo). {YB} Con Shift, los Octave enseñan el valor como las octavas del original: Octave ▼ brillante en la mitad alta, tenue en la baja y apagado en 0; Octave ▲ al revés, apagado en 127. Antes de RC4: **1-16 / 17-32** (LED verde). |
| **Shift + pad 25** *(desde RC4)* | Filtro master apagado / encendido: apagado, suena como con el filtro al centro aunque muevas su knob (el knob sigue cambiando su posición); otra vez, el filtro vuelve en la posición actual del knob. Apagado, el LED del knob del filtro se ve rojo; con Shift, el pad 25 en amarillo (rojo si está apagado). Sin Shift, el pad 25 es el de stock. |
| Fila inferior | La misma que en Master FX: huecos (26-30), gesto mecánico (31), grabar (32). |

- Si en Setup los retornos van por las tiras 3 / 4, sus envíos tienen tope a la mitad.
""", [("vista-fx", 0)])

view("sidechain", "VI", "Vista Sidechain",
     "**Shift + FX**. Los presets de sidechain de cada pista como siempre, más los knobs:",
     f"""
| Control | Qué hace |
|---|---|
| **K1-K4** {B} | Ataque, hold, decay y profundidad del sidechain de la pista del último preset tocado (Synth 1 si ninguno); LEDs del color de la pista. Desde RC4.07 su brillo sube en curva, para que los presets se distingan a la vista. |
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
| **Note** {XB} | **Teclado externo al arpegiador**: las notas que llegan por MIDI (DIN o USB) al canal de Synth 1 / 2 o MIDI 1 / 2 pasan por su arpegiador (si está encendido en el patrón que suena) como los pads. Verde = encendido, rojo tenue = apagado (de fábrica); se guarda en los ajustes. {YB} Encendido, con un **paso mantenido** en la vista de esa pista, las notas del teclado externo **entran en ese paso** como los pads. |
| **K4** {XB} | Modo **General MIDI** de los drums: a la derecha encendido (verde), a la izquierda apagado (tenue): **apagarlo cierra el número** y los drums vuelven a salir como en stock. Encendido, cada golpe de Drum 1-4 sale por MIDI con **su nota GM** en lugar de la de stock (60 / 62 / 64 / 65), por el canal de drums (el 10 de fábrica, el que elijas aquí). Dentro del aparato suena igual. |
| **K5-K8** {XB} | Con el modo encendido, la nota GM de Drum 1-4 (los knobs sobre las pistas de drums; apagado no hacen nada): 35-81, dos clics por nota; de fábrica 36 bombo, 38 caja, 42 charles cerrado, 46 charles abierto. **Cada nota nueva suena** una vez por el canal de drums y **su número se ve en los pads**, en el color del drum; **Shift** o salir de Setup lo confirma (se guarda en los ajustes) y vuelven los pads de Setup. Mientras se ve el número, los pads de Setup no hacen nada. Luces: el color de cada drum, más brillante cuanto más alta la nota (apagadas con el modo apagado). |
| **Preset** {YB} | **Retener knob**: verde = encendido, rojo tenue = apagado (de fábrica). Encendido, un knob que estás girando **sigue con lo que hacía** aunque cambies de vista, de pista, de página (las páginas de knobs de MIDI 1 / 2, nivel / panorama del Mixer, delay / reverb de FX, Master FX, Sidechain, el step-drummer) o pulses o sueltes **Shift** a media vuelta, hasta que lo dejas quieto **un segundo**; entonces pasa a lo que hay en pantalla. Cada knob por su cuenta: uno que no estabas tocando hace ya lo de la vista nueva. Clear no se retiene (Clear + knob actúa al momento). La luz del knob retenido se queda como estaba antes del cambio (color y brillo); las demás enseñan la vista nueva. Se guarda en los ajustes. |
| **K1 / K2** {YB} | **velocity → amplitud / velocity → filtro**: de 0 (apagado, de fábrica: como el original) a 127, para Synth 1 / 2 y el sinte propio de MIDI 1 / 2. **K1** da velocity al volumen de los patches que no la tienen (velocity del amp a 0): a la derecha, las notas suaves suenan más bajo (al máximo, unos 22 dB entre velocity 20 y 120). **K2** da velocity a la frecuencia del filtro de los patches sin velocity en su matriz: las notas fuertes, más brillantes (en Synth 1 / 2 ocupa el último hueco libre de la matriz). En el sinte propio valen cuando su fuente velocity (página 6, K1) está a 0: las notas suaves, más bajas y más oscuras. Un patch que ya usa velocity no cambia. Sus LEDs en blanco, más brillantes cuanto más alto; se guardan en los ajustes. |

- El patch flip sale siempre por el canal de su pista MIDI.
""", [("setup", 0)])

view("advanced-setup", "VII", "Vista Advanced Setup",
     "Ábrela como en el original. Además de sus ajustes de stock (compresor master, etc.):",
     f"""
- **Duplicate** = modo del jack MIDI Thru {B}: Thru (rojo tenue, el DIN In por hardware) → Out 2 (verde) → **Merge** (amarillo: el DIN In + el MIDI del aparato) → **Filter** (azul: el DIN In sin los canales en los que escucha el aparato). Sin SysEx en Merge / Filter. Se guarda en los ajustes.
- **K1 = curva de velocity de los pads** {XB} (en las RC; en la beta no hay curva: K1 / K2 de la [vista Setup](#setup) son la velocity global): de −8 a +8 (2 clics por paso); el centro (0) es la respuesta del original, de fábrica. **A la derecha, más sensible** (los golpes suaves suenan más fuerte); **a la izquierda, más dura** (hay que golpear más). Al girarlo, los pads enseñan el número (verde a la derecha, naranja a la izquierda, blanco en el centro) y **Velocity** se enciende 1,5 s. Vale para todos los pads en todas las vistas; la velocity fija (Shift + Velocity = 96) no cambia. Se guarda en los ajustes.
- **Pad 23 = fusión USB** {XB}: lo que entra por el **DIN In** (un teclado conectado con cable MIDI) sale también por **USB** hacia el ordenador, junto al MIDI del propio aparato. Verde encendida, tenue apagada; se guarda en los ajustes. Con Clock Tx encendido no se copian el reloj ni el transporte del DIN In (el ordenador recibiría dos relojes); el SysEx no se copia; lo que entra por USB no se reenvía.
- **K3 = ganancia de las entradas externas** {YB}: de **0 a +24 dB** (2 clics por dB); 0 = como el original, de fábrica. Sube el volumen máximo de lo que entra por las entradas de audio (las de MIDI 1 / 2 en el Mixer), también lo que llega al sinte propio y al granular; con mucha ganancia satura. Al girarlo, los pads enseñan los dB 1,5 s y el LED de K3 brilla más cuanta más ganancia. Se guarda en los ajustes.
- **Pad 22 = guardado diferido** {ZB}: apagado (de fábrica), Save guarda al momento, como el original. Encendido, guardar con el secuenciador en marcha espera a que pares, para no descompasar el reloj ([qué pasa mientras espera](#guardado)). Verde encendido, tenue apagado; se guarda en los ajustes.
- El ataque / release del compresor master se ajustan en la vista Sidechain, K7 / K8.
""")

# ===================================================================================================== XI
# the data chapter (the user, 2026-10-27: «what's saved in a pattern and how to make sure your set parameters are saved; what is saved after reboot
# and where (pattern, project, pack, global); what is lost after reboot; MIDI: custom behaviors, new CCs and NRPNs; mod matrix and macro destinations
# (stock, quoting and linking the official MIDI reference, and custom)»)
OFFICIAL_REF = "https://fael-downloads-prod.focusrite.com/customer/prod/downloads/circuit_tracks_programmer_s_reference_guide_v3.pdf"
OFFICIAL_UG = "https://fael-downloads-prod.focusrite.com/customer/prod/downloads/circuit_tracks_user_guide_v3_en.pdf"
OFFICIAL_DL = "https://downloads.novationmusic.com/novation/circuit/circuit-tracks"

view("datos-patron", "XI", "Qué guarda un patrón y cómo asegurarte de que se guarda",
     "Cada pista tiene 8 patrones por proyecto. Lo que está en un patrón viaja con él (Duplicate, cadenas, escenas) y llega a la tarjeta al **guardar el proyecto**.",
     f"""
### Lo que lleva cada patrón
| Qué | Pistas | Cómo se pone |
|---|---|---|
| Notas, velocity, gate, micropasos y probabilidad de cada paso | todas | Como en el original |
| Automatización de los knobs: macros de Synth 1 / 2, knobs de la plantilla MIDI, knobs de stock de los drums, nivel y panorama del Mixer, envíos de reverb / delay | todas | Como en el original: **Record** y girar, o mantener un paso y girar |
| Sample flips | drums | Como en el original |
| Primer y último paso, sync rate y dirección | todas | Pattern Settings, como en el original |
| **Random-mutate, frecuencia y dinámicas** de cada paso {B} | todas | [Vista de probabilidad](#probabilidad) |
| **Orden fractal / deconstruido** y **regla de cadena** (n vueltas, salto a B / C) {B} | todas | [Pattern Settings](#pattern-settings), [Patterns](#patterns) |
| **Paso que suelta la automatización** {XB} | Synth 1 / 2, MIDI 1 / 2 | Vista Velocity, Shift + pad de paso ([vista de pista](#synth-nota)) |
| **Carriles del sinte propio** (los 8 knobs secuenciables) {B}; {XB} la **foto** de Record + paso | MIDI 1 / 2 | Record y girar ([páginas de knobs](#midi-knobs)) |
| **Notas del step-drummer**: en carriles de automatización (MIDI 1 / 2: el del tono y, para su página 2, el de Release; Synth 1 / 2: el de su macro) | Synth, MIDI | [Step-drummer](#step-drummer) |
| **Valores del secuenciador de efectos** | MIDI 1 / 2 | [Step-drummer](#step-drummer) |
| **Sample flips del modo muestra** (en el carril de nivel de la pista) {B} | MIDI 1 / 2 | [Selector de samples](#midi-muestra) |
| **Pasos cromáticos de los drums** (en el carril de pitch del drum) {B} | drums | [Vista cromática](#drum-cromatica) con Record |
| {YB} **Carril extra de los drums** (el pitch cromático o el knob asignado; en los bits libres de cada paso; el código 126 = la **marca** de la vista de automatización) | drums | [Vista de pista de un drum](#drum-pista) con Record; la vista de automatización |
| {YB} **Estados y rampas de los drums** (bloqueos de estado: en los mismos bits, el número de estado o «rampa»; los estados, en el proyecto) | drums | [Vista de pista de un drum](#drum-pista) con Record; la vista de automatización |
| Golpes de los **rollers** y del **arpegio de drums** | drums | Con Record, como golpes normales |
| {XB} La **copia del sinte propio** de MIDI 1 / 2 (en los ajustes de los patrones 1-5, sin cambiar lo que suenan) | MIDI 1 / 2 | Sola, al guardar el proyecto |

- **No están en el patrón** aunque se elijan con él en pantalla: el **arpegiador** (encendido, orden y resolución; {XB} sus **modificadores**) y el **gate por pulsación** se guardan en el **proyecto** por pista (el arpegiador, por pista y número de patrón: **no se copia al duplicar el patrón**).
- **Duplicar un patrón** copia todo lo de la tabla. **Clear + patrón** en la vista Patterns (fuera del modo cadena) lo borra con su regla y su orden.

### Cómo asegurarte de que se guarda
1. **Un knob girado sin Record** cambia el sonido de todo el proyecto (el patch, los knobs de drums, el Mixer…), no el patrón. Para que cambie **en un paso o a lo largo del patrón**, grábalo: **Record** con el secuenciador en marcha, o **mantén un paso y gira** (como en el original).
2. **Guarda el proyecto: Save dos veces** (el primer toque parpadea en blanco; el segundo, verde rápido). Se guarda en el último hueco usado; para otro hueco, en la vista Projects: **Save + el pad del hueco** (como en el original). Todo lo marcado «proyecto» o «patrón» en esta guía solo llega a la tarjeta así.
3. **Cargar otro proyecto o apagar sin guardar** pierde los cambios desde el último Save (como en el original). Al encender se carga el último proyecto usado, tal como se guardó.
4. **Save apagado siempre** = **Save Lock** activado (Shift + Save al encender, función del original): repite el gesto para quitarlo.
5. **El sinte propio de MIDI 1 / 2** guarda sus valores **en los ajustes del aparato** (iguales para todos los proyectos): {XB} también **con el proyecto** al guardarlo. Para conservar un sonido entre proyectos o packs, **guárdalo como patch** ([vista Preset de MIDI 1 / 2](#midi-preset), Clear + pad dos veces). Para que cambie dentro del patrón, usa la página 4 (carriles) o el step-drummer.
6. **Un patch de Synth 1 / 2** tal como suena (knobs, destinos de macro editados, MIDI recibido) va con el proyecto; para tenerlo en el pack y usarlo en otros proyectos, **guárdalo** en la [vista Preset](#synth-preset) (Clear + pad dos veces) {B}.
7. **Antes de apagar:** para el secuenciador y espera **2 s** sin tocar el motor de MIDI 1 / 2 (sus ajustes se escriben en la tarjeta solo con el transporte parado, para no cortar el audio), y apaga con el **botón de encendido**.
8. **Sin tarjeta (pack de la memoria interna)** y con las versiones **S**, el mod no escribe nada propio: patches, samples y copias no se guardan (el LED de Save se pone rojo). Los proyectos, sí, como en el original.
9. {ZB} **Guardar mientras suena:** de fábrica el proyecto se guarda al momento, como en el original, aunque el reloj puede descompasarse un instante. Con el **guardado diferido** ([Advanced Setup](#advanced-setup), pad 22) encendido, Save dos veces con el secuenciador en marcha deja el guardado **pendiente** (Save parpadea en amarillo) y lo escribe **al parar**; si antes pides otra cosa del proyecto (cargar uno, guardar en otro hueco) o apagas el pad 22, se guarda en ese momento. Si cambias de pack antes de parar, ese guardado se descarta. Con un guardado pendiente, para el transporte antes de apagar.
""")

view("guardado", "XI", "Qué vuelve tras reiniciar y dónde se guarda",
     "Cinco sitios: el **patrón**, el **proyecto** (los dos, al guardar el proyecto), el **pack** (al momento, en la tarjeta), los **ajustes del aparato** (solos, para todos los proyectos) y ninguno (se pierde al apagar).",
     f"""
### El proyecto (Save dos veces)
| Qué | Dónde se usa |
|---|---|
| Como en el original: los patches de Synth 1 / 2 tal como suenan, los samples elegidos y knobs de los drums, Mixer, envíos y parámetros de reverb / delay, sidechain, escenas y cadenas, tempo, swing, escala y tónica | — |
| **Knobs nuevos de los drums**: envolvente, ring mod, LFO, filtro y su modo, inicio, corte, ataque, bitcrush, tipo de distorsión; el semitono de la vista cromática | [Drums](#drum-pista) |
| **Fuente del ruido** de Synth 1 / 2 (entradas de audio) | [Vista de la fuente](#synth-fuente) |
| **Master FX**: los 20 knobs, los efectos asignados a los huecos, ataque / release del compresor | [Master FX](#master-fx), [Sidechain](#sidechain) |
| **Sidechain**: Synth 1 / 2 y MIDI 1 / 2 como fuente; K1-K4 de las páginas de drums | [Sidechain](#sidechain) |
| **Modo cadena** (y en cada escena), **repeticiones de escena**, envíos del **modo cue** | [Patterns](#patterns), [Mixer](#mixer) |
| {YB} **Mutate de patrones**: qué pistas mutan, la semilla y los ajustes (y en cada escena) | [Patterns](#patterns) |
| **Cuenta atrás** (el metrónomo, como en el original, no se guarda) | [Botones](#botones) |
| **Arpegiador** de notas y de drums (por pista y patrón; {XB} con sus modificadores), **gate por pulsación**, **longitud fija** | [Pattern Settings](#pattern-settings), [Micro Step](#micropasos) |
| **Escala propia** y {XB} **Jankó** | [Scales](#escalas) |
| Sinte propio de MIDI 1 / 2: **gate retrigger**, **forma del LFO**, el toggle pitch-vel y el destino de la página 2 del step-drummer | [Páginas de knobs](#midi-knobs), [Step-drummer](#step-drummer) |
| {XB} **Parejas estéreo de drums**: encendidas, distancia, apertura y desviaciones | [Drums](#drum-pista) |
| {YB} **Factor del random-mutate** de cada pista y **micropasos** de cada drum (modo 2) | [Vista de probabilidad](#probabilidad) |
| {YB} **Secuenciador de saltos** de MIDI 1 / 2: a qué pista apunta cada una | [Vista Preset de MIDI](#midi-preset) |
| {YB} **Qué lleva el carril extra** de cada drum (carril o bloqueos de estado) | [Drums](#drum-pista) |
| {YB} **Los estados de los drums** (hasta 80, con sus 14 valores; guardados con el proyecto y sus escenas) | [Drums](#drum-pista) |
| {XB} **El sinte propio entero** de MIDI 1 / 2: motor, valores, matriz, destinos de los knobs secuenciables y {XB} no secuenciables, FM, modo de voz, estéreo (al cargar un proyecto que lo lleva manda el del proyecto; uno anterior deja el sonido como estaba); {YB} el FM de 8 operadores, en los ajustes de los patrones de Synth 1 / 2 | [Vista Preset de MIDI](#midi-preset), [FM de 8 operadores](#midi-fm8) |

### El pack (se escribe en la tarjeta al hacer el gesto)
| Qué | Dónde se usa |
|---|---|
| **Patches de Synth 1 / 2 guardados** {B} (Clear + pad dos veces); intercambios y copias entre packs | [Vista Preset de Synth](#synth-preset) |
| **Patches del sinte propio** de MIDI 1 / 2 (64 por pack, {XB} 128; comunes a las dos pistas: motor, valores, step-drummer, {NB} matriz, {XB} FM, destinos de los knobs secuenciables y {XB} no secuenciables, modo de voz; {YB} sub-oscilador y ruido del modo de un oscilador; el FM de 8 operadores en una ranura extra del mismo banco, después de sus 8 patches; «Send patches» de Components ya no los borra) | [Vista Preset de MIDI](#midi-preset), [FM de 8 operadores](#midi-fm8) |
| **Samples**: intercambios, copias entre packs y la **captura** que sustituye a un drum (esta, al guardar el proyecto, si cabe) | [Vista Preset de drums](#drum-preset) |
| **Proyectos copiados** a otro hueco o pack; **packs borrados** | [Projects](#projects), [Packs](#packs) |

### Los ajustes del aparato (solos, para todos los proyectos)
| Qué | Dónde se usa |
|---|---|
| Como en el original: canales, filtros de CC / notas / Program Change, reloj, compresor master encendido, brillo, Save Lock | [Setup](#setup), [Advanced Setup](#advanced-setup) |
| **Motor de MIDI 1 / 2**: motor elegido, todos sus valores, osciladores y orden (pads 28 / 29), step-drummer encendido y su destino, secuenciador de efectos, patch flip | [Vista Preset de MIDI](#midi-preset) |
| **Modo del jack MIDI Thru** (Thru, Out 2, Merge, Filter), **canales de Program Change** del proyecto, **modo cue** | [Advanced Setup](#advanced-setup), [Setup](#setup), [Mixer](#mixer) |
| {XB} **Modo General MIDI** de los drums y sus notas; **fusión USB**; **teclado externo al arpegiador**; **curva de velocity** de los pads; {YB} **velocity → amplitud / filtro** (K1 / K2 de Setup), **ganancia de las entradas** (K3 de Advanced Setup) | [Setup](#setup), [Advanced Setup](#advanced-setup) |
| {ZB} **Guardado diferido** | [Advanced Setup](#advanced-setup) |
| {YB} **Retener knob** | [Setup](#setup) |
""")

view("datos-perdido", "XI", "Qué se pierde al reiniciar",
     "Lo que no está en ninguna de las tablas anteriores vive solo en la memoria y desaparece al apagar (o al instalar otra versión).",
     f"""
| Qué | Al encender |
|---|---|
| **Todo lo cambiado desde el último Save** del proyecto (como en el original) | Vuelve el proyecto tal como se guardó |
| **Filtro master** y su **resonancia** (como en el original); {XB} el filtro master apagado con Shift + pad 25 | En sus valores iniciales; el filtro, encendido |
| **Metrónomo** encendido / apagado y **View Lock** (como en el original) | Apagados |
| **Efectos fijados**, **song pointer** y sample fijado de Master FX | Apagados; el song pointer, a 0 |
| **Record de la vista Setup** (grabar los ruteos internos) | Apagado |
| {YB} **Retener knob** (Preset de Setup) | Apagado |
| En la vista Sidechain, los **disparos de un drum** por otro drum o por un patrón (pads de las páginas de drums) | Los del preset del drum |
| **Mutes en el compás siguiente** pendientes (Mixer, Shift + pad) | — |
| **Notas y acordes en latch** (Shift + tecla, Shift + fundamental), **pantalla de acordes** (tipo y modificadores) y el medio tono de **Octave con Jankó** {XB} | Sin latch; los de fábrica; Octave a 0 |
| **Teclado partido** y vistas abiertas (step-drummer, editor de macros, selector, {YB} la vista de flip); {YB} el **último destino** del step flip | Cerrados; el destino, Synth 1 |
| Un **sample o patch esperando** a copiarse en otro pack (Duplicate + A) | Nada esperando |
| La **captura** de Master FX sin usar, o usada en un drum sin guardar el proyecto | Vacía; el drum, con su sample del pack |
| **Matriz de modulación** del sinte propio sin guardar en un patch {NB} ({XB}: guardada también con el proyecto) | Apagada |
| Los contadores de vueltas de la **frecuencia** y del orden **fractal** (se reinician al parar) | Desde la primera vuelta |

- **Instalar otra versión** reinicia el aparato: lo que no se guardó se pierde; el proyecto, el pack y los ajustes se quedan.
- **Volver al firmware oficial:** los proyectos y packs guardados con el mod se abren en el original; lo propio del mod va en partes de los ficheros que el original no usa, y el original no lo lee.
""")

view("midi", "XI", "MIDI: comportamientos propios, CC y NRPN nuevos",
     "Todo lo nuevo sale y entra por CC / NRPN, respetando los filtros CC Tx / CC Rx del Setup. Los parámetros del aparato original siguen con los números de la guía de Novation (ver la sección siguiente).",
     f"""
### Canales (como en el original, cambiables en Setup)
Synth 1 = canal 1, Synth 2 = canal 2, drums = canal 10, proyecto y Master FX = canal 16 (los de la guía de Novation); MIDI 1 / 2 = los canales elegidos para ellas en Setup.

### Comportamientos propios
| Qué | Cómo |
|---|---|
| **Teclado externo en MIDI 1 / 2** {B} | Las notas que entran por el canal de MIDI 1 / 2 (USB o DIN) tocan su sinte propio y se graban; no se reenvían a la salida. |
| **Teclado externo al arpegiador** {XB} | Setup, botón Note: las notas que entran por el canal de Synth 1 / 2 o MIDI 1 / 2 pasan por su arpegiador. |
| **Patch flip** | Vista Preset de MIDI 1 / 2, pad 26: cada nota de la pista sale como Program Change por el canal de la pista. |
| **Secuenciador de saltos** {YB} | Vista Preset de MIDI 1 / 2, pads 9-16 de la fila de motores: mientras apunta a otra pista, la pista MIDI no manda notas; sus notas hacen saltar esa pista. El pad 27 parpadea. Apuntar apaga el motor y encender un motor deja de apuntar. |
| **Program Change del proyecto** {B} | Setup, pads 29 / 30: canal de escucha y canal de salida (16 de fábrica); lo recibido en el de escucha se reenvía por el de salida. |
| **MIDI Thru: Merge y Filter** | Advanced Setup, Duplicate: Thru (hardware), Out 2, Merge (DIN In + el MIDI del aparato), Filter (DIN In sin los canales del aparato). Sin SysEx. |
| **Fusión USB** {XB} | Advanced Setup, pad 23: lo que entra por el DIN In sale también por USB (sin el reloj con Clock Tx, sin SysEx). |
| **Guardado diferido** {ZB} | Advanced Setup, pad 22: guardar el proyecto mientras suena espera a que pares (Save parpadea en amarillo). De fábrica, apagado: como el original. |
| **Modo General MIDI de los drums** {XB} | Setup, K4 / K5-K8: los golpes de Drum 1-4 salen con la nota GM elegida en lugar de 60 / 62 / 64 / 65. Dentro suena igual. |
| **Pareja estéreo de drums** {XB} | Las notas de Drum 2 / 4 lo tocan solo, a la derecha; su patrón no suena ni sale por MIDI mientras dura la pareja. |
| **Grabar los ruteos internos** {B} | Setup, Record: lo que una pista MIDI manda a un sinte por el mismo canal se graba también en el sinte; {XB} nada se graba en una pista silenciada en el Mixer. |
| **Knobs nuevos** | Al girarlos (también con Clear) sale su CC / NRPN; al recibirlo, el knob se mueve. El nivel a 100 / 0 del Mixer (Shift + knob) sale como un giro. |
| **Sin MIDI** | La matriz de modulación del sinte propio, el FM, el modo de voz y los destinos de los knobs secuenciables y {XB} no secuenciables no tienen CC / NRPN: se guardan en los patches propios. |
| **Seleccionar un NRPN** | CC 99 (MSB), CC 98 (LSB), CC 6 (valor), en ese orden; el aparato recuerda el NRPN elegido hasta el siguiente CC 99 / 98. |
""")

view("destinos", "XI", "Matriz de modulación y destinos de los macros",
     "Los sintes de stock (Synth 1 / 2) tienen la matriz y los macros de Novation; el sinte propio de MIDI 1 / 2 tiene su matriz y sus carriles.",
     f"""
La referencia oficial es la **Programmer's Reference Guide** de Novation, versión 3 ([PDF]({OFFICIAL_REF}), en la [página de descargas del Circuit Tracks]({OFFICIAL_DL})). Para cada ranura de macro da: «macro knob 1 destination A NRPN 3:0 0 – 70 0» (Novation, *Circuit Tracks Programmer's Reference Guide* v3, «Macro Knobs»).

### Matriz de modulación de Synth 1 / 2 (stock, sin cambios)
- Se edita desde Components o por MIDI (canal del sinte); el aparato no tiene vista para ella. Cada ranura: fuente 1, fuente 2, profundidad (−64..63) y destino. La guía oficial lista 12 ranuras desde **NRPN 1:83** (fuente 1, fuente 2, —, profundidad, destino: 5 números por ranura); el firmware tiene 20, con el mismo patrón.
- **Fuentes (0-12):** 0 directa, 4 velocity, 5 teclado (nota), 6 / 7 LFO 1 (unipolar / bipolar), 8 / 9 LFO 2 (unipolar / bipolar), 10 envolvente de amplitud, 11 envolvente del filtro, 12 envolvente 3.
- **Destinos (0-17):** 0 tono de los dos osciladores, 1 / 2 tono del oscilador 1 / 2, 3 / 4 v-sync 1 / 2, 5 / 6 ancho de pulso / índice 1 / 2, 7 / 8 nivel del oscilador 1 / 2, 9 nivel de ruido, 10 nivel del ring mod, 11 drive del filtro, 12 frecuencia del filtro, 13 resonancia, 14 / 15 velocidad del LFO 1 / 2, 16 decay de la envolvente de amplitud, 17 decay de la envolvente del filtro.

### Macros de Synth 1 / 2 (stock) y su editor {B}
- 8 macros por patch, posición = **CC 80-87**; cada macro, 4 ranuras A-D. Ranura r (0-3) del macro k (1-8): **NRPN 3:(16 (k − 1) + 4 r)** = destino, + 1 inicio, + 2 fin (el tramo del recorrido del knob, 0 / 127 de fábrica), + 3 profundidad (64 = 0).
- La guía oficial da el destino como «0 – 70» sin nombrarlos: la lista de abajo nombra cada uno (70 destinos, 0-69).
- **En el aparato:** [vista de la fuente](#synth-fuente), pad 32 = editor (ranura, inicio, fin, destino, profundidad). Lo editado va en el patch del proyecto; Clear + pad dos veces en la [vista Preset](#synth-preset) lo guarda en el pack.
- El knob del editor recorre primero los destinos con CC (por número de CC) y después los que solo tienen NRPN; en los pads, blanco = CC, azul claro / magenta / violeta = NRPN de los bancos 0 / 1 / 2.

### Matriz del sinte propio de MIDI 1 / 2 (propia) {NB}
- [Vista Preset de MIDI](#midi-preset) con el motor encendido, **pad 6**: los 8 knobs son 8 **fuentes**: K1 velocity, K2 nota, K3 azar por nota, K4 LFO 2, K5 envolvente 2, K6 golpe de un drum, K7 posición en el patrón, K8 azar por pasos ({XB} el LFO 2 también a tempo).
- **La posición del knob es el destino y la cantidad:** a la izquierda apagado; girando a la derecha recorre todos los parámetros de las páginas de knobs (los de la página 1, luego la 2, la 3 y los de la 5 que no salen antes), 16 pasos por destino, la cantidad creciendo dentro de cada tramo. LED = color de la página del destino; brillo = cantidad.
- Varias fuentes al mismo destino se suman; el valor guardado del parámetro no cambia. Detalle: [Matriz de modulación](#midi-matriz).

### Destinos de los knobs secuenciables (página 4) y no secuenciables del sinte propio {XB}
- Los 8 knobs secuenciables (página 4) son los carriles de automatización (de fábrica: TUNE, Release, Env → nivel, Env → filtro, Filtro, Resonancia, Velocidad del LFO, Efecto). **Shift + knob** = su destino, entre los mismos parámetros y colores que la matriz; **Clear mantenido, luego Shift + knob** = el de fábrica. Se guarda con el patch propio y con el proyecto. Detalle: [Páginas de knobs](#midi-knobs).
- **Knobs no secuenciables** (Shift + pad 4): la misma elección de destino, en 8 knobs que no son carriles; de fábrica Ataque, Decay, Sustain, SHAPE, LFO → filtro, Env → tono, MIX OSC 1 / 2, Gain del VCA; se guardan con los patches propios.

### Destinos del step-drummer
- MIDI 1 / 2: pads 17-24 de su vista = el parámetro del motor que mueve cada paso; Synth 1 / 2: los macros 1-8. Detalle: [Step-drummer](#step-drummer).
""")

# ===================================================================================================== VIII
view("instalar", "VIII", "Instalar y volver atrás",
     "`tools/rc_uploader.html` parchea el firmware oficial en el navegador y lo envía por Web MIDI.",
     """
1. Descarga el firmware oficial 1.2.1 de Novation, abre `tools/rc_uploader.html` en Chrome y conecta el Circuit Tracks por USB.
2. Elige la versión (RC4, la más segura RC4S, o una anterior) y envía. El bootloader de Novation no se toca.
3. **Haz antes una copia de la tarjeta.** Con las versiones que no acaban en «S», no uses la memoria interna para proyectos.
- **Volver atrás:** envía otra versión o el firmware oficial. Si no arranca: **Scales + Preset + Note** al encender.
- **Versiones nuevas:** en el paso 2, **Buscar versiones nuevas** consulta las publicadas (hace falta internet) y añade a la lista las que tu instalador no lleva; se eligen y se envían como las demás.
""")

view("app-sd", "VIII", "App de la tarjeta y del aparato",
     "[Descarga `sd_app.zip`](https://ghillermo.github.io/CIRCUIT-HACKS-RC/sd_app.zip), descomprímelo y abre `sd_app.html` en Chrome o Edge. No necesita instalación ni servidor. Para pasar samples, patrones y parches FM entre un Circuit Tracks y un Circuit Rhythm: la app **Hacks + Remix**: [descarga `hr_app.zip`](https://ghillermo.github.io/CIRCUIT-HACKS-RC/hr_app.zip), descomprímelo y abre `hr_app.html` en Chrome o Edge.",
     """
Ordena desde el ordenador lo que hay en la microSD o en el aparato conectado por USB. También funciona con el firmware oficial; los parches custom son lo único propio del mod.

### Abrir
- **Abrir carpeta…**: elige la carpeta `Tracks` de la tarjeta o de una copia en el ordenador.
- **Aparato…**: el Circuit Tracks por USB. Cierra Components y acepta el permiso de MIDI. Guarda antes el proyecto. El transporte se para y el panel queda bloqueado hasta **Desconectar aparato**; si cierras la página sin desconectar, también se libera.
- **↻** vuelve a leer lo abierto. **Copias:** elige la carpeta del ordenador donde se guarda lo que la app sustituye o borra.
- **Firmware** (arriba) {YB}: **automático** = con el aparato conectado, la app le pregunta qué firmware lleva. La Beta 5.47 y las posteriores contestan con su nombre (sale en el aviso de arriba) y la app ofrece todo. Si no contesta (el firmware oficial o una versión anterior), solo quedan las funciones que entiende el firmware oficial: sin **Parches custom** (ni **Importar DX7…**), sin el sinte propio en **Sonidos del proyecto…** y, al editar un patrón, sin el orden, el random-mutate, la frecuencia, las dinámicas ni la marca de soltar la automatización. Con una carpeta (sin aparato) está todo. **Solo stock** / **Hacks** lo fijan a mano: elige **Hacks** si el aparato lleva una versión de Hacks anterior a la Beta 5.47. El **Editor de patches** de la app Hacks + Remix hace la misma pregunta: si no hay respuesta no envía nada al aparato (botón **Es Hacks: enviar igualmente**).
- **Versión antigua** {YB}: con conexión a internet, la app mira las versiones publicadas. Si el aparato no contesta, o lleva una Beta o una RC más antigua que la última publicada de su serie, el aviso de arriba enlaza el **instalador**; el Editor de patches enseña el mismo enlace junto al estado.

- **Caja negra…** {YB}: si el panel se queda colgado mientras suena (la música sigue, pero ni los pads ni los botones responden ni cambian las luces), a los 15 s el aparato apunta lo último que pasó y se reinicia solo; al volver, **Save parpadea en violeta** 30 s. Entonces conecta el aparato, pulsa **Caja negra…**, **Guardar…** y manda el fichero `.json` (lleva las últimas pulsaciones, la vista y dónde estaba el programa parado). Después, **Vaciar**: mientras tenga algo guardado no apunta nada más. **Capturar ahora** guarda lo de ese momento sin reiniciar. No hace falta abrir la conexión: el panel no se bloquea. Con la música parada no reinicia nunca. Beta 5.51 y posteriores. **Desde la Beta 5.53 también apunta los reinicios**: un **fallo del procesador** (dónde estaba el programa y qué falló), un **bloqueo** del aparato (más de 1,5 s sin que corra el bucle principal, hasta que el aparato se reinicia solo) y un reinicio por el **vigilante** (las últimas pulsaciones de antes); al volver, Save violeta. Lo apuntado se conserva aunque sigas usando el aparato: **solo se pierde si se queda sin corriente** antes de leerlo.

### Las dos columnas
Cada columna abre una carpeta, una tarjeta o el aparato, con su propio pack. Un clic elige una fila; Ctrl añade y Shift elige un tramo.
- **Copiar** y **Mover** pasan lo elegido a la otra columna: al hueco elegido allí o, sin elegir, al primero libre. Si está ocupado, pregunta: sobrescribir o, al mover, intercambiar.
- **Eliminar** borra lo elegido, tras preguntar. **Editar** abre lo elegido en **Parches custom**, **Patrones** y **Presets CC**; también con doble clic.
- **Renombrar / orden…** cambia el nombre o el número de una fila elegida en **Packs**, **Sintes Nova**, **Drums** y **Parches custom** (en **Presets CC**, solo el nombre: los proyectos de todos los packs eligen los presets por su número). **Un número ocupado = los dos se intercambian.** Un nombre nuevo solo cambia el nombre. **Un número nuevo de un sample o un sinte Nova que usan proyectos del pack pregunta qué hacer con ellos: «Mover sus referencias»** reescribe esos proyectos para que cada uno siga sonando igual; **«Dejarlos»** los deja apuntando al número de antes, que ahora tiene otro contenido. Lo que se reescribe: el sample de cada drum y sus sample flips, el sample del sinte propio de MIDI 1 / 2 y sus flips, y el patch de Synth 1 / 2 (el registro dice qué proyectos se han actualizado). Los parches custom los encuentran los proyectos por su sonido y los packs no los nombra ningún proyecto: solo se mueven. La app solo acepta nombres que el aparato y la tarjeta admiten: letras, números, espacios y signos ASCII (sin acentos ni ñ); en packs y samples, sin `\\ / : * ? " < > |` ni espacio o punto al final, y como mucho 27 caracteres un pack y 23 un sample (con el número y la extensión, 30); los patches, 16; los presets CC, 32. Por USB no se renombra ni se mueve el pack que el aparato tiene cargado (recargaría el proyecto); en el pack cargado, la app avisa antes de reescribir sus proyectos.

### Las pestañas
| Pestaña | Qué hay | Qué se hace |
|---|---|---|
| **Packs** | Los packs de la tarjeta o del aparato | Copiar, mover, eliminar y exportar packs enteros. El pack interno no aparece |
| **Sintes Nova** | Los patches de Synth 1 / 2 de cada pack | Copiar, mover, eliminar, exportar |
| **Drums** | Los samples del pack y la memoria de samples que ocupan | Escuchar con ▶ o doble clic, copiar, mover, eliminar, exportar |
| **Parches custom** | Los patches del sinte propio de MIDI 1 / 2 | Editar el motor, sus parámetros y el nombre; copiar, mover, eliminar, exportar; **Importar DX7…** |
| **Patrones** | Los 64 patrones de una sesión: 8 por pista | Ver, copiar, mover, borrar, exportar; editar las pistas de notas |
| **Presets CC** | Las 8 plantillas de CC de las pistas MIDI | **Leer del aparato**, cambiar, **Enviar al aparato**; **Abrir…** y **Guardar…** como `.ctcc`; **De fábrica** |

### Qué proyectos usan cada cosa
En **Sintes Nova**, **Drums** y **Parches custom**, antes del nombre: **● n** = lo usan n proyectos del pack; **○** = ninguno. Al pasar el ratón, o al elegir una sola fila, aparece la lista: proyecto y pista. Al eliminar algo en uso, la app lo avisa.
- **Sintes Nova:** el patch al que apunta Synth 1 / 2 en cada proyecto. El proyecto lleva su propia copia, que es la que suena al cargarlo; si ya no se llama igual que el hueco, la lista da su nombre.
- **Drums:** el sample de cada drum, los sample flips de sus pasos y, con el sinte propio de MIDI 1 / 2, el sample del granular o del modo muestra y sus flips.
- **Parches custom:** un proyecto no guarda el número del parche. Cuenta cuando el sinte propio guardado con el proyecto suena igual: mismo motor y mismos valores, aunque el nombre cambie.
- Con el aparato conectado, la lista no se lee sola: pulsa **Ver qué proyectos los usan** (lee todas las sesiones del pack por USB).

### Importar voces del DX7
En **Parches custom**, **Importar DX7…** abre un `.syx` del DX7: un banco de 32 voces (4104 bytes), una voz suelta (163 bytes), varios mensajes en un fichero o un banco de 4096 bytes sin cabecera. La lista enseña cada voz con el hueco al que irá: **Desde el hueco** elige el primero (de fábrica, la fila elegida o el primer hueco libre), **Saltar los ocupados** no pisa ningún parche (sin marcarlo, los que se sustituyen llevan ⚠), **Todas** / **Ninguna** y las casillas eligen las voces.
- Cada voz pasa a un parche custom: el oscilador con el **FM de 8 operadores** encendido (los 6 operadores del DX7; el 7 y el 8 callados), modo de voz poly y el nombre de la voz. Envolventes, niveles, ratios, escalado, velocity, algoritmo, feedback y transposición, en las unidades del DX7. El LFO del DX7 se guarda en el parche, pero aún no suena.
- Necesita la Beta 5.20 o posterior en el aparato: guarda el FM de 8 operadores en un registro propio al final del banco de patches. Copiar, mover, eliminar y exportar llevan ese registro con el parche; en el **Editor**, un parche así dice su algoritmo y sus operadores se editan en el aparato.
- Un byte de comprobación mal no impide la importación: la app lo avisa.

### Patrones
- Arriba eliges el pack y la sesión. El tercer selector filtra: **Con contenido**, **Todas** o una pista.
- Cada fila dice pista y patrón (`Synth 1·3`), lo que contiene y sus pasos, con una cuadrícula de sus notas. Con el aparato conectado, también el **canal** de la pista; el canal se guarda en el aparato, no en la sesión.
- Al elegir una fila, debajo aparece el patrón en grande: piano roll en las pistas de notas, barras de velocity en los drums, con los sample flips en ámbar y los rollers divididos.
- Doble clic edita una pista de notas: primer y último paso, sync rate, dirección, orden, notas y carriles de automatización. **Los patrones de drums se ven, se copian y se exportan, pero aún no se editan.**
- **Sonidos del proyecto…** (arriba, con la sesión elegida): lo que carga ese proyecto. **Synth 1 / 2** = el hueco Nova al que apunta y la copia que suena al cargarlo (su estado inicial: **Tomar la del hueco** la sustituye por el patch de ese hueco); **MIDI 1 / 2** = el sinte propio del proyecto (desde un parche custom, con su FM de 8 operadores y su wavetable; **Editar su estado inicial…** abre el editor de parches sobre la copia del proyecto); **Drum 1-4** = el sample de cada uno. **Guardar en el proyecto** escribe solo esa sesión; los huecos del pack no cambian.
- Un patrón de drums solo se copia a otra pista de drums. Al copiar se quedan en el destino las reglas de cadena y los datos del proyecto guardados en los ajustes del patrón; en los drums, también la frecuencia y el random-mutate por paso.

### Exportar
**Exportar…** guarda en el ordenador lo elegido, sin carpeta de tarjeta ni volcado completo. Sin nada elegido, exporta todo lo que hay en la lista (en **Packs** hay que elegir). Un elemento pide nombre de fichero; varios, una carpeta.

| Pestaña | Fichero |
|---|---|
| **Sintes Nova** | `.syx` de 350 B, el formato de un patch en los packs de Components |
| **Parches custom** | `.ctm` (172 bytes; 396 con el FM de 8 operadores) |
| **Drums** | `.wav` |
| **Patrones** | `.mid` y `.ctpat` (los datos exactos); con uno solo, eliges cuál |
| **Presets CC** | Un `.ctcc` con los 8; con el aparato conectado, los lee antes de él |
| **Packs** | Una carpeta por pack, con todos sus ficheros |

- El `.mid` es una vuelta del patrón, hacia delante, del primer paso al último, en el canal de la pista. No lleva dirección, sample flips ni automatización, y una nota larga se corta al final.
- Lo exportado todavía no se vuelve a cargar desde la app, salvo los `.ctcc`.

### Snapshot y Restaurar
Con el aparato conectado:
- **Snapshot…** crea una carpeta `Circuit_<fecha>` con todos los packs, el pack interno y los presets de CC. Esa carpeta se abre también con **Abrir carpeta…**, como una tarjeta.
- **Restaurar…** pide esa carpeta, compara cada fichero por tamaño y CRC y enseña un plan: qué escribe, qué borra y qué ya es igual. Solo cambia lo que difiere, y lo que sustituye va antes a tu carpeta de copias.
- El pack interno no se escribe de vuelta y los packs que no están en el snapshot se quedan.
- **No entran:** los ajustes del aparato, porque no se pueden escribir, y lo que no hayas guardado del proyecto.

La barra de abajo enseña el avance: porcentaje, MB, velocidad, tiempo restante y fichero. Con parches y patrones avanza por elementos.

### Precauciones
- **Haz antes un snapshot o una copia de la tarjeta.** La escritura por USB está probada en un aparato real, pero puede haber fallos aún sin descubrir.
- **Por USB, cada escritura borra primero el fichero antiguo.** Por eso con el aparato la carpeta de copias es obligatoria.
- **Nunca dejes copias dentro de un pack:** el aparato busca los ficheros por su prefijo `NN_` y una copia puede ocupar el lugar del original. Si la app avisa de ficheros que pueden tapar a los del pack, quítalos desde el ordenador.
- **El pack cargado:** si escribes en él, se recarga al desconectar y se pierde lo no guardado.
- Conectar pisa unos 1,7 s del sample capturado sin guardar. No uses Components a la vez.
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
- **Los patches por categoría** {YB} — cada patch en el color de su categoría de Components; la categoría se elige al guardar.
- **Morph de patches** {YB} — mantén varios patches y pasa de uno a otro con un knob, LFO y envolvente.
- **Guardar el patch** {B} — guarda en el pack el sonido tal como lo has dejado (el original solo guarda patches desde Components).
- **Intercambiar y copiar** — reordena los patches del pack o lleva uno a otro pack.
""",
       "midi-preset": f"""
- **Un sinte en cada pista MIDI** — MIDI 1 y 2 suenan en el propio aparato con su motor (entrada de línea procesada, oscilador, dos osciladores, VA-drum, granular, modo muestra; {XB} FM) y siguen mandando MIDI.
- **Secuenciador de efectos** — un motor que no suena: dispara efectos de Master FX en los pasos que elijas.
- **Patches del sinte propio** {B} — 64 sonidos por pack para esos motores, a un toque.
- **Matriz de modulación** {NB} — ocho fuentes (velocity, nota, azar, LFO 2, envolvente 2, golpe de un drum, posición del patrón, azar por pasos) que mueven cualquier parámetro del motor.
- **Patch flip** — cada nota manda un cambio de programa: el aparato externo cambia de sonido paso a paso.
- **Secuenciador de saltos** {YB} — las notas de la pista hacen saltar el patrón de otra pista al paso que indican.
- **Editor de CC** — cambia qué CC manda cada knob de la plantilla sin Components.
""",
       "midi-knobs": """
- **VCA-VCF** — volumen y filtro con su envolvente y su LFO; con Shift, el tipo de filtro y el tipo de efecto.
- **Osciladores** — una forma de onda continua de seno a cuadrada y un segundo oscilador con FM, ring y sync.
- **Granular** — convierte un sample en texturas: granos que lo leen en otra posición, velocidad o dirección para congelarlo, estirarlo o trocearlo.
- **Página 4, knobs secuenciables** — los 8 parámetros que se graban como automatización ({XB}: con Shift + knob, cualquiera de los 33; Record + paso = foto de los valores).
- {XB} **Shift + pad 4, knobs no secuenciables** — 8 knobs de destino asignable que no se graban.
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
- **Pareja estéreo** {XB} — Drum 1 + Drum 2 (o 3 + 4) tocan un sample estéreo: el de la izquierda manda en los dos y el de la derecha solo matiza.
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
- **Nudge** — mueve el contenido de los pasos elegidos un paso atrás o adelante.
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
- **Mutate de patrones** {YB} — Shift + Duplicate: cada pista toca sus patrones en otro orden, y vuelve a la misma lista con la escena.
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
- **Resonancia del filtro master** — en Shift + Octave ▲ / ▼, de 16 en 16 *(desde RC4; antes, 1-16 / 17-32)*.
- **Filtro master apagado / encendido** — Shift + pad 25, sin perder su posición *(desde RC4)*.
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
- **Retener knob** {YB} — un knob que giras sigue con lo que hacía aunque cambies de vista o pulses Shift, hasta dejarlo quieto un segundo.
""",
    **{"advanced-setup": f"""
- **MIDI Thru, Merge y Filter** {B} — el jack Thru puede mezclar el MIDI de entrada con el del aparato o filtrarlo.
- **Curva de velocity** {XB} — K1 hace los pads más sensibles o más duros.
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


def marks(s, b, nb, xb, yb=YB):
    """the version marks left as {B} / {NB} / {XB} / {YB} in texts that are not f-strings"""
    return s.replace("{YB}", yb).replace("{XB}", xb).replace("{NB}", nb).replace("{B}", b)


def tables(vid, lang):
    """the generated tables some views end with: the MIDI reference's (midi) and the firmware's 70 macro destinations (destinos)"""
    es = lang == "es"
    if vid == "midi":
        import midi_ref
        return "".join(f"\n\n### {h}\n\n{t}" for h, t in midi_ref.sections(lang)[1:4])
    if vid == "destinos":
        import macroed
        rows = ["### " + ("Los 70 destinos de los macros" if es else "The 70 macro destinations"), "",
                "| " + " | ".join(("Destino", "Parámetro", "CC / NRPN") if es else ("Destination", "Parameter", "CC / NRPN")) + " |", "|---|---|---|"]
        rows += [f"| {d} | {name} | {'CC %d' % num if bank == 'CC' else 'NRPN %d:%d' % (bank, num)} |" for d, (name, bank, num) in enumerate(macroed.DEST)]
        return "\n\n" + "\n".join(rows)
    return ""


def data(lang):
    if lang == "es":
        m = lambda s: marks(s, B, NB, XB)
        return [dict(v, how=m(v["how"]), detail=m(v["detail"]) + tables(v["id"], lang), about=m(ABOUT.get(v["id"], "").strip("\n"))) for v in V], PARTS, UI["es"]
    import guide_en as EN
    m = lambda s: marks(s, EN.B, EN.NB, EN.XB, EN.YB)
    out = []
    for v in V:
        title, how, detail = EN.VIEWS[v["id"]]
        out.append(dict(v, title=title, how=m(how), detail=m(detail.strip("\n")) + tables(v["id"], lang), about=m(EN.ABOUT.get(v["id"], "").strip("\n"))))
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


def write(lang, md=True):
    views, parts, U = data(lang)
    figs = figures(lang)
    if M.SET == "rc":                                                       # (docset.py) the release candidate's set: no beta-only view
        import docset
        views = [v for v in views if not (docset.titled(v["title"]) or docset.titled(v["how"][:60]))]
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
    if md: (ROOT / U["md"]).write_text("\n".join(out), encoding="utf-8", newline="")
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
    (ROOT / M.OUT / U["html"]).write_text("\n".join(parts_h), encoding="utf-8", newline="")
    return len(views)


if __name__ == "__main__":
    n = [write(lang) for lang in ("es", "en")]
    import midi_ref
    for lang in ("es", "en"): midi_ref.write(lang, M.VERSION, M)
    print(n[0], "views, es, en; MIDI reference es, en")
