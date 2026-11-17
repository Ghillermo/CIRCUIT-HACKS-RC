"""The wiki's feature explanations (the user, 2026-11-14: «Explain each feature, not just name it»): for every section of the feature list
(make_manual's section ids; not the developer tools), in English and Spanish, what it is for (what), how to use it step by step (how) and what to
keep in mind (notes), written for users from the published guide by views (docs/GUIA.md / GUIA.en.md), the feature list (make_manual /
manual_en) and the voices document (docs/VOICES.md / VOCES.md).  make_wiki puts them on the Features pages, under each feature's summary.

Only what the published versions do, with the docs' version marks: «since RCx» / «desde RCx», «Beta 5.56 only» / «solo Beta 5.56».  Links to the
guide are written [text](#view): make_wiki points them at the guide of the page's language.

    python tools/wiki_explain.py         (checks the data: both languages, every section of the feature list, the guide's anchors, the words)
"""
from __future__ import annotations
import re
import sys
from pathlib import Path


def E(what, how, notes=()):
    """one language: what = what it is for (a short paragraph), how = the steps in order, notes = what to keep in mind"""
    return dict(what=what, how=list(how), notes=list(notes))


EXPLAIN = {}

# ---------------------------------------------------------------------------------------------------- A: Shortcuts and usability
# A1 Shortcut map
EXPLAIN["atajos"] = dict(
    en=E("A one-page cheat sheet of every gesture the mod adds, drawn on the device: double presses, Shift + button, Clear + knob and the "
         "special pads of each view, each with what it does and since which version. Keep it at hand while you learn the mod: it tells you "
         "which button to hold and which one to press.",
         ["On the drawing, each numbered badge marks a control; in the table of the illustrated entry (the title's link), the row with "
          "that number gives the gesture and what it does, and the table goes on with the shortcuts that do not fit on the drawing.",
          "**Double presses:** **Mixer** twice = Master FX; **Synth 1 / 2** twice = the synth's source view; *(since RC4)* **MIDI 1 / 2** "
          "again with its Note view on screen = its Preset view, **Scales** twice = the custom scale editor, **Velocity** twice = fixed "
          "velocity (on the drums, *Beta 5.56 only*, the automation view).",
          "**Shift + button:** **Shift + Preset** with a drum = the chromatic view; *(since RC2)* **Shift + Clear** = metronome and "
          "count-in, **Shift + Play** = quantize, **Shift + Scales** = custom scale; *(since RC4)* **Shift + Synth 1 / 2** or **Shift + "
          "MIDI 1 / 2** = the same as pressing them twice.",
          "**Clear + knob:** to the right = the knob's default value; to the left = erase its automation. *(since RC2)* **Clear + Synth 1 "
          "/ 2, MIDI 1 / 2 or a drum's button** = that track's sound back to its starting values (a drum's button also erases its knobs' "
          "automation in the playing pattern).",
          "**Special pads:** in Master FX, **pad 7** plays the capture, **pad 8** switches everything off and **pad 32** records; in the "
          "MIDI 1 / 2 Preset view, **pad 25** = CC editor, **26** = patch flip, **27** = engine, **30** = step-drummer, **32** = voice "
          "mode *(since RC4)*."],
         ["While **Shift** is held, every view lights in **yellow** the shortcuts it offers; the option chosen shows in another colour.",
          "*since RC2 / RC2.02 / RC4 / RC4.05* = in the RCs and in the beta from that version on; *Beta 5.56 only* = only in the beta.",
          "**Scales + Preset + Note** at power-up = Novation's recovery mode: it lets you install any firmware again.",
          "Anything not on the map works as on the original. The gestures that work in every view: [Buttons that work in every "
          "view](#botones)."]),
    es=E("Una chuleta de una página con todos los gestos que añade el mod, dibujados sobre el aparato: botones dobles, Shift + botón, "
         "Clear + knob y los pads especiales de cada vista, cada uno con lo que hace y desde qué versión. Tenla a mano mientras aprendes "
         "el mod: te dice qué botón mantener y cuál pulsar.",
         ["En el dibujo, cada número señala un control; en la tabla de la entrada ilustrada (el enlace del título), la fila con ese "
          "número da el gesto y lo que hace, y la tabla sigue con los atajos que no caben en el dibujo.",
          "**Botones dobles:** **Mixer** dos veces = Master FX; **Synth 1 / 2** dos veces = la vista de la fuente del sinte; *(desde RC4)* "
          "**MIDI 1 / 2** otra vez con su vista Note en pantalla = su vista Preset, **Scales** dos veces = el editor de la escala propia, "
          "**Velocity** dos veces = velocity fija (en los drums, *solo Beta 5.56*, la vista de automatización).",
          "**Shift + botón:** **Shift + Preset** con un drum = la vista cromática; *(desde RC2)* **Shift + Clear** = metrónomo y cuenta "
          "atrás, **Shift + Play** = cuantizar, **Shift + Scales** = escala propia; *(desde RC4)* **Shift + Synth 1 / 2** o **Shift + MIDI "
          "1 / 2** = lo mismo que pulsarlos dos veces.",
          "**Clear + knob:** a la derecha = el valor por defecto del knob; a la izquierda = borrar su automatización. *(desde RC2)* "
          "**Clear + Synth 1 / 2, MIDI 1 / 2 o el botón de un drum** = el sonido de esa pista vuelve a sus valores de partida (el botón de "
          "un drum además borra la automatización de sus knobs en el patrón que suena).",
          "**Pads especiales:** en Master FX, el **pad 7** toca la captura, el **pad 8** lo apaga todo y el **pad 32** graba; en la vista "
          "Preset de MIDI 1 / 2, **pad 25** = editor de CC, **26** = patch flip, **27** = motor, **30** = step-drummer, **32** = modo de "
          "voz *(desde RC4)*."],
         ["Con **Shift** pulsado, cada vista ilumina en **amarillo** los atajos que ofrece; la opción elegida, en otro color.",
          "*desde RC2 / RC2.02 / RC4 / RC4.05* = en las RC y en la beta a partir de esa versión; *solo Beta 5.56* = solo en la beta.",
          "**Scales + Preset + Note** al encender = modo de recuperación de Novation: permite volver a instalar cualquier firmware.",
          "Lo que no está en el mapa funciona como en el original. Los gestos que valen en todas las vistas: [Botones que funcionan en "
          "todas las vistas](#botones)."]))

# A2 Master FX on the Mixer button
EXPLAIN["master-fx-acceso"] = dict(
    en=E("Master FX is the mod's performance page: effects on the whole mix (Gater, Auto-Filter, Digitise, Phaser, Glitch and a mechanical "
         "tape-stop gesture), a song pointer, the captured sample and a row of effects you assign yourself. It sits behind the Mixer "
         "button, two presses away, so you can reach it in the middle of a performance.",
         ["Press **Mixer**.",
          "Press **Mixer** again: Master FX opens.",
          "Any other view button takes you back to the normal views.",
          "*(Beta 5.56 only)* In the Mixer, **hold Mixer** for ½ s or more: Master FX shows only while you hold it and the Mixer comes "
          "back when you let go; in Master FX, holding Mixer shows the Mixer until you let go. A tap switches as always."],
         ["Pads: 1-6 effects, 7 plays the capture, 8 switches off everything latched, 9-24 song pointer, 26-30 assignable slots, 31 "
          "mechanical gesture, 32 records the capture. Every pad in detail: [Master FX](#master-fx).",
          "*(since RC2)* The effects' 20 knobs, the slot assignments and the master compressor's attack / release are saved with each "
          "project; latched effects and the song pointer are not (they are off at power-up)."]),
    es=E("Master FX es la página de directo del mod: efectos sobre toda la mezcla (Gater, Auto-Filter, Digitise, Phaser, Glitch y un gesto "
         "mecánico de parada de cinta), un song pointer, el sample capturado y una fila de efectos que asignas tú. Está detrás del botón "
         "Mixer, a dos pulsaciones, para llegar a ella en plena actuación.",
         ["Pulsa **Mixer**.",
          "Pulsa **Mixer** otra vez: se abre Master FX.",
          "Cualquier otro botón de vista vuelve a las vistas normales.",
          "*(solo Beta 5.56)* En el Mixer, **mantén Mixer** ½ s o más: Master FX se ve solo mientras lo mantienes y al soltar vuelve el "
          "Mixer; en Master FX, mantenerlo enseña el Mixer hasta que lo sueltas. Un toque cambia como siempre."],
         ["Pads: 1-6 efectos, 7 toca la captura, 8 apaga todo lo fijado, 9-24 song pointer, 26-30 huecos asignables, 31 gesto mecánico, 32 "
          "graba la captura. Cada pad en detalle: [Master FX](#master-fx).",
          "*(desde RC2)* Los 20 knobs de los efectos, la asignación de los huecos y el ataque / release del compresor master se guardan "
          "con cada proyecto; los efectos fijados y el song pointer no (al encender, apagados)."]))

# A3 Keys of the FX view
EXPLAIN["vista-fx"] = dict(
    en=E("Turns the FX view into the control page of the device's reverb and delay: besides each track's sends you set the effects "
         "themselves (type, decay, time, feedback…), reset everything with one press, and reach the master filter's resonance and a switch "
         "that turns the master filter off.",
         ["Press **FX**. **Octave ▲** = the knobs are each track's **delay** sends; **Octave ▼** = the **reverb** sends.",
          "**Shift + knob** = the effect's own settings: reverb K1 type, K2 decay, K3 damping; delay K1 time, K2 sync, K3 feedback, K4 "
          "width, K5 ratio, K6 slew. The LED shows the value with its brightness.",
          "**Duplicate** = reset: sends to 0, master filter centred (the resonance untouched), Master FX off.",
          "*(since RC4)* **Shift + Octave ▲ / ▼** = master filter resonance +16 / −16, stopping at 127 / 0 (with Shift, Octave lights "
          "yellow).",
          "*(since RC4)* **Shift + pad 25** = master filter off / on: while off it sounds as if centred even when you move its knob, and "
          "the filter knob's LED is red (with Shift, pad 25 yellow, red while off); on again, the filter comes back at the knob's current "
          "position."],
         ["The reverb and delay settings are saved with the project. The master filter, its resonance and the off state are not: at "
          "power-up they are back at their initial values, with the filter on.",
          "The bottom row is Master FX's: slots 26-30, mechanical gesture (31), record (32). Without Shift, pad 25 is the stock one.",
          "If Setup routes the reverb / delay return through strips 3 / 4, the sends of those strips are capped at half.",
          "*(Beta 5.56 only)* With Shift, the Octave buttons show the resonance as the original shows octaves: Octave ▼ bright in the "
          "upper half, dim in the lower and off at 0; Octave ▲ the other way round, off at 127. Before RC4 the resonance was on **1-16 / "
          "17-32**, which now does what it always did."]),
    es=E("Convierte la vista FX en la página de control de la reverb y el delay del aparato: además de los envíos de cada pista, ajustas "
         "los propios efectos (tipo, decay, tiempo, feedback…), lo reinicias todo con un toque y tienes a mano la resonancia del filtro "
         "master y un interruptor que lo apaga.",
         ["Pulsa **FX**. **Octave ▲** = los knobs son los envíos de **delay** de cada pista; **Octave ▼** = los envíos de **reverb**.",
          "**Shift + knob** = los ajustes del propio efecto: reverb K1 tipo, K2 decay, K3 damping; delay K1 time, K2 sync, K3 feedback, K4 "
          "width, K5 ratio, K6 slew. El LED enseña el valor con su brillo.",
          "**Duplicate** = reset: envíos a 0, filtro master al centro (sin tocar la resonancia), Master FX apagado.",
          "*(desde RC4)* **Shift + Octave ▲ / ▼** = resonancia del filtro master +16 / −16; se para en 127 / 0 (con Shift, Octave en "
          "amarillo).",
          "*(desde RC4)* **Shift + pad 25** = filtro master apagado / encendido: apagado, suena como con el filtro al centro aunque muevas "
          "su knob, y el LED del knob del filtro se ve rojo (con Shift, el pad 25 amarillo, rojo si está apagado); otra vez, el filtro "
          "vuelve en la posición actual del knob."],
         ["Los ajustes de reverb y delay se guardan con el proyecto. El filtro master, su resonancia y el apagado no: al encender vuelven "
          "a sus valores iniciales, con el filtro encendido.",
          "La fila inferior es la de Master FX: huecos 26-30, gesto mecánico (31) y grabar (32). Sin Shift, el pad 25 es el de stock.",
          "Si en Setup el retorno de reverb / delay va por las tiras 3 / 4, los envíos de esas tiras tienen tope a la mitad.",
          "*(solo Beta 5.56)* Con Shift, los Octave enseñan la resonancia como las octavas del original: Octave ▼ brillante en la mitad "
          "alta, tenue en la baja y apagado en 0; Octave ▲ al revés, apagado en 127. Antes de RC4 la resonancia estaba en **1-16 / "
          "17-32**, que ahora hace lo de siempre."]))

# A4 Clear + knob = default value
EXPLAIN["clear-knob"] = dict(
    en=E("A quick way back for any of the mod's knobs: hold Clear and turn a knob right and it jumps to its default value, so you never "
         "hunt for the neutral position; turn it left and it erases what that knob recorded in the playing pattern, as on the original.",
         ["Hold **Clear** and turn a knob **to the right**: it goes back to its default value — on the drums (stock and new knobs), the "
          "MIDI 1 / 2 engine and **Master FX** (the selected effect's knobs). A **lavender** LED = done.",
          "Hold **Clear** and turn a knob **to the left**: its automation in the playing pattern is erased (**red** LED) — on the drums' "
          "stock knobs and, *(since RC2)*, on the MIDI 1 / 2 engine (whichever of the knob's two lanes, with and without Shift, hold "
          "automation).",
          "Let go of **Clear**."],
         ["On the drums and the MIDI engine it resets **both layers** of the knob (with and without Shift). On the drums, **Clear + K3** "
          "to the right zeroes attack, start and cut; *(since RC2)* **Clear + K8** to the right also removes the bitcrush.",
          "**Master FX** has no automation: to the left does nothing. While Clear is held, the knobs of the selected effect that are at "
          "their default show lavender (pads 1-6, the Glitch and the sample).",
          "A whole track at once *(since RC2)*: **Clear + a drum's button** erases its knobs' automation in the playing pattern and puts "
          "its eight knobs to their defaults; **Clear + Synth 1 / 2** puts its eight macros back to the loaded patch's values; **Clear + "
          "MIDI 1 / 2** puts the own synth's values back to their initial ones."]),
    es=E("Una vuelta rápida para cualquier knob del mod: mantén Clear y gira un knob a la derecha y salta a su valor por defecto, sin "
         "buscar a mano el punto neutro; gíralo a la izquierda y borra lo que ese knob grabó en el patrón que suena, como en el original.",
         ["Mantén **Clear** y gira un knob **a la derecha**: vuelve a su valor por defecto — en los drums (knobs de stock y nuevos), el "
          "motor de MIDI 1 / 2 y **Master FX** (los knobs del efecto elegido). LED **lavanda** = hecho.",
          "Mantén **Clear** y gira un knob **a la izquierda**: se borra su automatización en el patrón que suena (LED **rojo**) — en los "
          "knobs de stock de los drums y, *(desde RC2)*, en el motor de MIDI 1 / 2 (los carriles del knob, con y sin Shift, que tengan "
          "automatización).",
          "Suelta **Clear**."],
         ["En los drums y en el motor MIDI restablece **las dos capas** del knob (con y sin Shift). En los drums, **Clear + K3** a la "
          "derecha pone a 0 ataque, inicio y corte; *(desde RC2)* **Clear + K8** a la derecha quita también el bitcrush.",
          "**Master FX** no tiene automatización: a la izquierda no hace nada. Con Clear pulsado, los knobs del efecto elegido que están "
          "en su valor por defecto se ven lavanda (pads 1-6, el Glitch y el sample).",
          "Una pista entera de una vez *(desde RC2)*: **Clear + el botón de un drum** borra la automatización de sus knobs en el patrón "
          "que suena y pone sus ocho knobs por defecto; **Clear + Synth 1 / 2** devuelve sus ocho macros a los valores del patch cargado; "
          "**Clear + MIDI 1 / 2** devuelve los valores del sinte propio a los iniciales."]))

# A5 Switch off latched effects (Master FX pad 8)
EXPLAIN["pad8"] = dict(
    en=E("The panic button of Master FX: one press on pad 8 switches off every effect you latched with Shift, the song pointer and the "
         "sample, so you are back to the plain mix in a single move.",
         ["In Master FX, **hold** an effect pad to play it only while held, or press **Shift + its pad** to latch it; touching a latched "
          "pad again (without Shift) releases just that one.",
          "Press **pad 8** (white): every latched effect is released (the bottom-row slots too), the song pointer switches off, the sample "
          "stops and the FX are bypassed."],
         ["Latched effects, the song pointer and the latched sample are not saved: at power-up they are off (the song pointer at 0).",
          "*(Beta 5.56 only)* A latched sample loop that keeps playing through a project or pack load stops as always: pad 7 or pad 8."]),
    es=E("El botón de pánico de Master FX: un toque al pad 8 apaga todos los efectos que fijaste con Shift, el song pointer y el sample, y "
         "vuelves a la mezcla limpia de un solo gesto.",
         ["En Master FX, **mantén** un pad de efecto para que suene solo mientras lo mantienes, o pulsa **Shift + su pad** para fijarlo; "
          "tocar otra vez un pad fijado (sin Shift) suelta solo ese.",
          "Pulsa el **pad 8** (blanco): se sueltan todos los efectos fijados (también los huecos de la fila inferior), se apaga el song "
          "pointer, se para el sample y se hace bypass de los FX."],
         ["Los efectos fijados, el song pointer y el sample fijado no se guardan: al encender están apagados (el song pointer, a 0).",
          "*(solo Beta 5.56)* Un bucle del sample fijado que sigue sonando al cargar otro proyecto o pack se para como siempre: pad 7 o "
          "pad 8."]))

# A6 Synth source view
EXPLAIN["fuente-sinte"] = dict(
    en=E("Turns Synth 1 / 2 into a processor for an outside sound: the patch's noise is replaced by audio input 1 or 2, so the synth's "
         "filter, envelopes and effects shape your external signal (a drum machine, a voice, another synth) in time with the notes you "
         "play. The same view opens the synth's step-drummer and, since RC2, the macro destination editor.",
         ["With the **Synth 1** or **Synth 2** view on screen, press its button again (*(since RC4)*: or **Shift + Synth 1 / 2** from any "
          "view).",
          "Pick the source of the synth's noise: **pad 25** noise (normal), **26** audio input 1, **27** audio input 2, **28** input 1 "
          "phase-inverted, **29** input 2 phase-inverted.",
          "**Pad 30** opens the synth's step-drummer; **pad 32** *(since RC2)* the editor of the macro knob destinations.",
          "Any button closes the view."],
         ["The patch needs some noise level (CC 56) for the source to be heard. The source is saved with the project.",
          "If Setup routes the reverb / delay returns through strips 3 / 4, that signal is what reaches the synth.",
          "*(since RC2)* Play and Record no longer close the synth's step-drummer: until pad 30 closes it, pressing Synth 1 / 2 opens it "
          "again.",
          "*(Beta 5.56 only)* While a patch morph runs on that synth, its button opens the morph view instead (see the [Synth 1 / 2 Preset "
          "view](#synth-preset))."]),
    es=E("Convierte Synth 1 / 2 en un procesador para un sonido de fuera: el ruido del patch se cambia por la entrada de audio 1 o 2, así "
         "que el filtro, las envolventes y los efectos del sinte moldean tu señal externa (una caja de ritmos, una voz, otro sinte) al "
         "ritmo de las notas que tocas. La misma vista abre el step-drummer del sinte y, desde RC2, el editor de los destinos de los "
         "macros.",
         ["Con la vista de **Synth 1** o **Synth 2** en pantalla, pulsa su botón otra vez (*(desde RC4)*: o **Shift + Synth 1 / 2** desde "
          "cualquier vista).",
          "Elige la fuente del ruido del sinte: **pad 25** ruido (lo normal), **26** entrada de audio 1, **27** entrada de audio 2, **28** "
          "entrada 1 con la fase invertida, **29** entrada 2 con la fase invertida.",
          "El **pad 30** abre el step-drummer del sinte; el **pad 32** *(desde RC2)*, el editor de los destinos de los macro knobs.",
          "Cualquier botón cierra la vista."],
         ["El patch debe tener nivel de ruido (CC 56) para oír la fuente. La fuente se guarda con el proyecto.",
          "Si en Setup los retornos de reverb / delay van por las tiras 3 / 4, esa señal es la que entra al sinte.",
          "*(desde RC2)* Play y Record ya no cierran el step-drummer del sinte: hasta que lo cierras con el pad 30, pulsar Synth 1 / 2 lo "
          "vuelve a abrir.",
          "*(solo Beta 5.56)* Con un morph de patches en marcha en ese sinte, su botón abre la vista del morph en su lugar (ver la [vista "
          "Preset de Synth 1 / 2](#synth-preset))."]))

# A7 Chromatic and scale view of the drums
EXPLAIN["cromatica"] = dict(
    en=E("Plays a drum sample like a keyboard: the pads give the sample transposed along the project's scale, on three rows, so one hit (a "
         "tom, a bass hit, a vocal chop) becomes a melody or a bass line. With Record each pitch is recorded on its step.",
         ["Select a drum (**Drum 1-4**) and press **Shift + Preset** (*(since RC2)*: or **Preset** again in the drum's Preset view).",
          "Three rows of pads play the sample in the scale and root of the **Scales** view.",
          "**K1** = pitch offset in semitones; **Shift + K1** = fine tuning in cents.",
          "To record, play the pads with **Record + Play**: *(since RC4.02)* each pad records a hit with its pitch on its own step (the "
          "micro step and velocity of the press); **Shift + Play** (quantize) moves the pitch with its hit.",
          "*(since RC2)* **Preset** again turns the view off."],
         ["*(since RC2)* The pads transpose in semitones on top of K1's pitch; **Clear + K1** to the left (held) erases the recorded "
          "pitches, with K1's automation. *(Beta 5.56 only)* They are recorded in the drum's extra lane (factory setting), leaving the "
          "pitch lane to K1.",
          "In the drums' **Note** view, pads 25-28 repeat the boxes of drums 4 … 1; *(since RC2)* rows 1-3 are the micro-step rollers.",
          "The chromatic view's semitone is saved with the project."]),
    es=E("Toca un sample de drum como un teclado: los pads dan el sample transpuesto según la escala del proyecto, en tres filas, y un "
         "solo golpe (un tom, un golpe de bajo, un corte de voz) se convierte en una melodía o una línea de bajo. Con Record cada tono se "
         "graba en su paso.",
         ["Elige un drum (**Drum 1-4**) y pulsa **Shift + Preset** (*(desde RC2)*: o **Preset** otra vez en la vista Preset del drum).",
          "Tres filas de pads tocan el sample en la escala y la tónica de la vista **Scales**.",
          "**K1** = sesgo de tono en semitonos; **Shift + K1** = afinación fina en cents.",
          "Para grabar, toca los pads con **Record + Play**: *(desde RC4.02)* cada pad graba un golpe con su tono en su paso (el micropaso "
          "y la velocity de la pulsación); **Shift + Play** (cuantizar) mueve el tono con su golpe.",
          "*(desde RC2)* **Preset** otra vez apaga la vista."],
         ["*(desde RC2)* Los pads transponen en semitonos sobre el pitch de K1; **Clear + K1** a la izquierda (sostenido) borra los tonos "
          "grabados, con la automatización de K1. *(solo Beta 5.56)* Se graban en el carril extra del drum (de fábrica) y el carril de "
          "pitch queda para K1.",
          "En la vista **Note** de los drums, los pads 25-28 repiten los cuadros de los drums 4 … 1; *(desde RC2)* las filas 1-3 son los "
          "rollers de micropasos.",
          "El semitono de la vista cromática se guarda con el proyecto."]))

# A8 Pack management on the device
EXPLAIN["pack"] = dict(
    en=E("Lets you tidy up and move sounds between packs on the device itself, without a computer: swap or copy drum samples and Synth 1 / "
         "2 patches between packs, keep the samples you captured, and delete packs you no longer need.",
         ["**Keep the captures:** save the project as usual (**Save** twice): every drum sample replaced by a capture is written into the "
          "pack too, if it fits in the sample memory.",
          "**Swap two samples:** drum **Preset** view, hold **Duplicate** (it lights in this view), touch pad **A** (it blinks blue), then "
          "pad **B**: they swap and you hear it at once.",
          "**Copy a sample to another pack:** **Duplicate + pad A** in its pack, load the other pack (with Duplicate held, A's number "
          "blinks yellow), then **Duplicate + pad B**: A is copied over B, which may be empty; A's pack does not change.",
          "**Synth patches:** the same gestures in the **Preset** view of **Synth 1 / 2**: Duplicate + A + B swaps within a pack and "
          "copies between packs.",
          "**Delete a pack:** packs view (**Shift + Projects**), touch **Clear** (for ~5 s the packs that can be deleted blink), touch the "
          "pack (only it blinks; it is not loaded), then **Clear** again within 5 s."],
         ["Writes to the card: not in the S builds nor in the internal memory's pack (the Save LED turns red).",
          "A copied sample goes into B's place if it fits, otherwise into the free import memory (about 44 s); it never overwrites a "
          "sample that is playing — with no room, nothing changes.",
          "The loaded pack can never be deleted; a deleted pack's slot can be reused after a restart. Clear lights steady white in the "
          "packs view.",
          "**Duplicate + A** again (in its pack) cancels a waiting copy; it is also forgotten at power-off."]),
    es=E("Ordena y mueve sonidos entre packs desde el propio aparato, sin ordenador: intercambia o copia samples de drums y patches de "
         "Synth 1 / 2 entre packs, conserva los samples que capturaste y borra los packs que ya no usas.",
         ["**Conservar las capturas:** guarda el proyecto como siempre (**Save** dos veces): cada sample de drum sustituido por una "
          "captura se escribe también en el pack, si cabe en la memoria de samples.",
          "**Intercambiar dos samples:** vista **Preset** de drums, mantén **Duplicate** (se ilumina en esta vista), toca el pad **A** "
          "(parpadea en azul) y luego el pad **B**: se intercambian y suena al instante.",
          "**Copiar un sample a otro pack:** **Duplicate + pad A** en su pack, carga el otro pack (con Duplicate mantenido, el número de A "
          "parpadea en amarillo) y **Duplicate + pad B**: A se copia sobre B, que puede estar vacío; el pack de A no cambia.",
          "**Patches de sinte:** los mismos gestos en la vista **Preset** de **Synth 1 / 2**: Duplicate + A + B intercambia dentro de un "
          "pack y copia entre packs.",
          "**Borrar un pack:** vista de packs (**Shift + Projects**), toca **Clear** (durante ~5 s parpadean los packs que se pueden "
          "borrar), toca el pack (solo ese parpadea; no se carga) y **Clear** otra vez antes de 5 s."],
         ["Escribe en la tarjeta: no está en las versiones «S» ni en el pack de la memoria interna (el LED de Save se pone rojo).",
          "Un sample copiado va al sitio de B si cabe; si no, a la memoria libre de importación (unos 44 s); nunca pisa un sample que "
          "suena: si no hay sitio, no cambia nada.",
          "El pack cargado no se puede borrar nunca; el hueco de un pack borrado se reutiliza tras reiniciar. En la vista de packs, Clear "
          "se ve blanco fijo.",
          "**Duplicate + A** otra vez (en su pack) cancela una copia que espera; también se olvida al apagar."]))

# A9 Replace a drum with the capture
EXPLAIN["sustituir"] = dict(
    en=E("Puts the sound you just captured in Master FX on a drum: one drum's sample becomes the capture, so a piece of the mix (a chord, "
         "a vocal, a resampled loop) can be played and sequenced like a drum hit. Saving the project keeps it in the pack.",
         ["Record a capture: in Master FX (**Mixer** twice), hold **pad 32** (red) while the music plays; it records while held (up to "
          "3.46 s).",
          "Select the drum and press **Preset** (the drum Preset view).",
          "**Clear + the pad** of the sample to replace: the pad blinks (a question).",
          "**Clear + the same pad** again: confirmed; that sample now plays the capture.",
          "To keep it, save the project (**Save** twice): the capture is written into the pack, if it fits in the sample memory."],
         ["Any pad without Clear cancels the question; Clear + another pad moves it to that pad.",
          "Until you save, it is temporary: at power-off the drum gets its pack sample back. In the S builds and in the internal memory's "
          "pack nothing is written: it lasts until the pack is loaded again.",
          "**Shift + pad** is still the original's silent selection (picking a sample without hearing it)."]),
    es=E("Pone en un drum el sonido que acabas de capturar en Master FX: el sample de un drum pasa a ser la captura, y un trozo de la "
         "mezcla (un acorde, una voz, un loop remuestreado) se toca y se secuencia como un golpe de drum. Al guardar el proyecto queda en "
         "el pack.",
         ["Graba una captura: en Master FX (**Mixer** dos veces), mantén el **pad 32** (rojo) mientras suena la música; graba mientras lo "
          "mantienes (hasta 3,46 s).",
          "Elige el drum y pulsa **Preset** (vista Preset de drums).",
          "**Clear + el pad** del sample que quieres sustituir: el pad parpadea (pregunta).",
          "**Clear + el mismo pad** otra vez: confirmado; ese sample suena ahora con la captura.",
          "Para conservarlo, guarda el proyecto (**Save** dos veces): la captura se escribe en el pack, si cabe en la memoria de samples."],
         ["Cualquier pad sin Clear anula la pregunta; Clear + otro pad la mueve a ese pad.",
          "Hasta guardar es temporal: al apagar, el drum vuelve a su sample del pack. En las versiones «S» y en el pack de la memoria "
          "interna no se escribe nada: dura hasta que se vuelve a cargar el pack.",
          "**Shift + pad** sigue siendo la selección silenciosa del original (elegir un sample sin que suene)."]))

# A10 CC editor of the MIDI macros
EXPLAIN["editor-cc"] = dict(
    en=E("Changes, on the device, which CC or NRPN each knob of a MIDI track's template sends and over which range, without Components. "
         "Use it to map the knobs to the parameters of your external synth.",
         ["**MIDI 1 / 2**, **Preset**, **pad 25**: it lights.",
          "Move a knob: it is picked and its number is drawn on the pads.",
          "**Octave ▼ / ▲** = next / previous field; turn the knob to change the value. The first field's number sets the type: any number "
          "= a CC (number, start, end); 99, 98 or 6 = a 7-bit NRPN (number, MSB, LSB, start, end); 38 = a 14-bit NRPN (start and end in "
          "MSB and LSB).",
          "**Save:** **pad 26**, or **Octave ▼** up to the save step (pad 26 and Save blink) and Octave ▼ again. Saving leaves the editor, "
          "back to the Preset view.",
          "**Discard:** any view button, **pad 25** or a template pad."],
         ["It edits the track's template (what the knobs send with the own synth off) and saves into it, not into an own-synth patch.",
          "With the own synth on, the knobs send the engine's own CC / NRPN map, never the template; pad 25 is dark and does nothing, and "
          "an open editor closes when the engine turns on.",
          "On the computer, the **CC presets** tab of the [card and device app](#app-sd) reads the 8 templates from the device, edits them "
          "and sends them back."]),
    es=E("Cambia desde el aparato qué CC o NRPN manda cada knob de la plantilla de una pista MIDI y con qué recorrido, sin Components. "
         "Sirve para llevar los knobs a los parámetros de tu sinte externo.",
         ["**MIDI 1 / 2**, **Preset**, **pad 25**: se enciende.",
          "Mueve un knob: queda elegido y su número se dibuja con los pads.",
          "**Octave ▼ / ▲** = campo siguiente / anterior; gira el knob para cambiar el valor. El número del primer campo marca el tipo: "
          "cualquier número = un CC (número, inicio, fin); 99, 98 o 6 = un NRPN de 7 bits (número, MSB, LSB, inicio, fin); 38 = un NRPN de "
          "14 bits (inicio y fin en MSB y LSB).",
          "**Guardar:** el **pad 26**, u **Octave ▼** hasta el paso de guardar (el pad 26 y Save parpadean) y Octave ▼ otra vez. Al "
          "guardar sales del editor a la vista Preset.",
          "**Descartar:** cualquier botón de vista, el **pad 25** o un pad de plantilla."],
         ["Edita la plantilla de la pista (lo que mandan los knobs con el sinte propio apagado) y guarda en ella, no en un patch del sinte "
          "propio.",
          "Con el sinte propio encendido, los knobs mandan los CC / NRPN propios del motor, nunca la plantilla; el pad 25 se apaga y no "
          "hace nada, y un editor abierto se cierra al encenderse el motor.",
          "En el ordenador, la pestaña **Presets CC** de la [app de la tarjeta y del aparato](#app-sd) lee las 8 plantillas del aparato, "
          "las cambia y las vuelve a mandar."]))

# A11 Mixer: Shift + knob = level to 100 / 0
EXPLAIN["mixer-shift"] = dict(
    en=E("A one-move fader reset in the Mixer: Shift + a knob to the right puts that track at its nominal level (100), to the left at 0, "
         "without hunting for the exact value — handy to bring a track back in, or out, during a performance.",
         ["Open the **Mixer** on its levels page (**Octave ▲**, the normal one).",
          "Hold **Shift** and turn a track's knob **to the right**: its level jumps to **100**.",
          "**Shift** + the knob **to the left**: the level jumps to **0**."],
         ["The jump works like a turn of the knob: it goes out over MIDI and, while recording, it is written into the automation.",
          "On the pan page (**Octave ▼**), Shift + knob turns the cue mode on / off instead *(since RC2)*.",
          "On the original, Shift + knob did the same as the knob alone: no function is lost. Clear + knob (erase the automation) is "
          "unchanged."]),
    es=E("Un reset de fader de un solo gesto en el Mixer: Shift + un knob a la derecha deja esa pista a su nivel nominal (100) y a la "
         "izquierda a 0, sin buscar el valor exacto; útil para meter o sacar una pista en directo.",
         ["Abre el **Mixer** en su página de niveles (**Octave ▲**, la normal).",
          "Mantén **Shift** y gira el knob de una pista **a la derecha**: su nivel salta a **100**.",
          "**Shift** + el knob **a la izquierda**: el nivel salta a **0**."],
         ["El salto es como un giro del knob: sale por MIDI y, grabando, queda en la automatización.",
          "En la página de panorama (**Octave ▼**), Shift + knob enciende / apaga el modo cue *(desde RC2)*.",
          "En el original, Shift + knob hacía lo mismo que el knob solo: no se pierde ninguna función. Clear + knob (borrar la "
          "automatización) no cambia."]))

# A12 Cue mode, mutes on the bar and quantize (since RC2)
EXPLAIN["mixer-cue"] = dict(
    en=E("Three tools for playing live from the Mixer: a cue on the right output to pre-listen to tracks before you bring them in, mutes "
         "and unmutes that land exactly on the next bar, and a one-press quantize of the playing pattern.",
         ["**Cue mode:** in the **Mixer**, pan page (**Octave ▼**), **Shift + a knob to the right** turns it on (Octave ▼ pink); to the "
          "left, off (white).",
          "With the mode on, each pan knob is that track's send to the cue, from the centre to the right (to the left, nothing); **Clear + "
          "knob** = no cue. The knobs light pink, brighter with more send.",
          "The left output carries the mix in mono, the right one only the cued tracks. A track muted in the Mixer but cued plays only on "
          "the right: unmute it (its pad, or **Shift + pad** on the next bar) to drop it into the mix.",
          "**Mutes on the bar:** **Shift + pads 1-8** = that track mutes or unmutes when the next bar starts; the pad blinks while it "
          "waits, again cancels it; stopped, at once.",
          "**Quantize:** **Shift + Play** moves the notes and hits recorded off the grid in the selected track's playing pattern to the "
          "nearest step (Play yellow with Shift, green after quantizing).",
          "*(Beta 5.56 only)* **Solo:** hold **pad 16** + pads 1-8 = only those tracks sound (pad 16 white); a tap on pad 16 brings the "
          "mutes back. With no solo, a tap on pad 16 = **solo flip** (orange): only the tracks you hold sound, until you let go."],
         ["The cue mode is kept in the device; the cue sends are saved with the project; the pans come back when the mode goes off. "
          "Reverb, delay and Master FX belong to the mix: the cue hears them too.",
          "*(since RC4)* With the cue mode on, choosing a Synth 1 / 2 patch and **Shift + sample** in a drum's Preset view are heard only "
          "in the cue, and the metronome's and the count-in's click sound only there.",
          "Quantize: micro steps 1-2 go to the start of their step, 3-5 to the start of the next one; on the drums a step with several "
          "hits (a roll) stays. It replaces the original's Shift + Play (another way to start playback).",
          "Pending bar mutes are lost at power-off. *(Beta 5.56 only)* Loading another project turns solo and flip off without touching "
          "its mutes."]),
    es=E("Tres herramientas para tocar en directo desde el Mixer: un cue por la salida derecha para escuchar pistas antes de meterlas, "
         "silencios y entradas que caen justo al empezar el compás siguiente, y cuantizar con un toque el patrón que suena.",
         ["**Modo cue:** en el **Mixer**, página de panorama (**Octave ▼**), **Shift + un knob a la derecha** lo enciende (Octave ▼ rosa); "
          "a la izquierda, lo apaga (blanco).",
          "Con el modo encendido, cada knob de panorama es el envío de esa pista al cue, del centro a la derecha (a la izquierda, nada); "
          "**Clear + knob** = sin cue. Los knobs en rosa, más brillantes cuanto más envío.",
          "La salida izquierda lleva la mezcla en mono y la derecha solo las pistas en cue. Una pista silenciada en el Mixer pero en cue "
          "suena solo por la derecha: actívala (su pad, o **Shift + pad** al compás siguiente) para meterla en la mezcla.",
          "**Mutes al compás:** **Shift + pads 1-8** = esa pista se silencia o se activa al empezar el compás siguiente; el pad parpadea "
          "mientras espera, otra vez lo cancela; parado, al momento.",
          "**Cuantizar:** **Shift + Play** lleva al paso más cercano las notas y golpes grabados fuera de la rejilla en el patrón que "
          "suena de la pista elegida (Play amarillo con Shift, verde después de cuantizar).",
          "*(solo Beta 5.56)* **Solo:** **pad 16** mantenido + pads 1-8 = solo suenan esas pistas (pad 16 blanco); un toque al pad 16 "
          "devuelve los mutes de antes. Sin solo, un toque al pad 16 = **solo flip** (naranja): suenan solo las pistas que mantienes, "
          "hasta que las sueltas."],
         ["El modo cue se guarda en el aparato; los envíos al cue, con el proyecto; los paneos vuelven al apagar el modo. La reverb, el "
          "delay y Master FX son los de la mezcla: el cue también los oye.",
          "*(desde RC4)* Con el modo cue encendido, elegir un patch de Synth 1 / 2 y **Shift + sample** en la vista Preset de un drum se "
          "oyen solo en el cue, y el clic del metrónomo y el de la cuenta atrás suenan solo ahí.",
          "Cuantizar: los micropasos 1-2 van al inicio de su paso y los 3-5 al del siguiente; en los drums, un paso con varios golpes (un "
          "redoble) se queda. Sustituye al Shift + Play del original (otra forma de arrancar).",
          "Los mutes al compás pendientes se pierden al apagar. *(solo Beta 5.56)* Cargar otro proyecto apaga el solo y el flip sin tocar "
          "sus mutes."]))

# A13 LFO synced to the tempo (since RC4)
EXPLAIN["lfo-sync"] = dict(
    en=E("Locks an LFO to the song's tempo: with its rate knob to the left, a wobble, tremolo or filter sweep repeats from every 1/16 up "
         "to every 8 bars and starts on the bar's first beat; to the right it stays a free LFO, as before.",
         ["Find an LFO rate knob: **K7** of the VCA-VCF page of the MIDI 1 / 2 engine, **Shift + K4** of the mod matrix (pad 6), **Shift + "
          "K7** of a drum, or **K1** of the Auto-Filter (pads 2 / 3) and of the Phaser (pad 5) in Master FX.",
          "At the centre its LED is dim. Turn it **to the right** for a free LFO (faster further right).",
          "Turn it **to the left** for a rate synced to the tempo; from the centre outwards: 1/16T, 1/16, 1/8T, 1/8, 1/4T, 1/4, 1/2T, 1/2, "
          "1 bar T, 1 bar, 2T, 2, 4T, 4, 8T and 8 bars, 4 clicks each. The LED gets brighter towards both ends.",
          "In the matrix, each LFO 2 shape of Shift + K4 is a stretch of its own: its left half synced, its right half free."],
         ["Synced, each cycle starts on the bar's first beat (it is put back in place on every sequencer tick); stopped, it keeps the "
          "tempo.",
          "What was saved before with another rate may sound different.",
          "*(Beta 5.56 only)* Bipolar knobs show their left side (the synced one) in a lighter shade of their colour, dim at the centre."]),
    es=E("Ata un LFO al tempo de la canción: con su knob de velocidad a la izquierda, un wobble, un trémolo o un barrido de filtro se "
         "repite desde cada 1/16 hasta cada 8 compases y empieza en el primer tiempo del compás; a la derecha sigue siendo un LFO libre, "
         "como antes.",
         ["Busca un knob de velocidad de LFO: **K7** de la página VCA-VCF del motor de MIDI 1 / 2, **Shift + K4** de la matriz de "
          "modulación (pad 6), **Shift + K7** de un drum, o **K1** del Auto-Filter (pads 2 / 3) y del Phaser (pad 5) en Master FX.",
          "Al centro, su LED se ve tenue. Gíralo **a la derecha** para un LFO libre (más rápido cuanto más a la derecha).",
          "Gíralo **a la izquierda** para una velocidad a tempo; del centro hacia fuera: 1/16T, 1/16, 1/8T, 1/8, 1/4T, 1/4, 1/2T, 1/2, 1 "
          "compás T, 1 compás, 2T, 2, 4T, 4, 8T y 8 compases, 4 clics cada una. El LED brilla más hacia los dos extremos.",
          "En la matriz, cada forma del LFO 2 de Shift + K4 es un tramo propio: su mitad izquierda a tempo y la derecha libre."],
         ["A tempo, cada ciclo empieza en el primer tiempo del compás (se recoloca en cada tick del secuenciador); parado, sigue al tempo.",
          "Lo guardado antes con otra velocidad puede sonar distinto.",
          "*(solo Beta 5.56)* Los knobs bipolares enseñan su lado izquierdo (el de tempo) en un tono más claro de su color, tenues en el "
          "centro."]))

# A14 Split keyboard Synth 1 + Synth 2
EXPLAIN["teclado-partido"] = dict(
    en=E("Puts two note tracks on the pads at once, one above the other, so you can play, for instance, a bass with one hand and chords or "
         "a lead with the other, each part in its own scale, octave and colours.",
         ["Hold **Synth 1** and press **Synth 2** (or the other way round). *(since RC2.02)* Any pair of **Synth 1, Synth 2, MIDI 1, MIDI "
          "2** works: hold one button and press another.",
          "The top two rows play the track you held first and the bottom two the other one, each with its scale, octave, velocity and "
          "colours.",
          "The knobs and **Octave** belong to the track you pressed first. *(since RC4)* **Hold a track button** (Synth 1 / 2, MIDI 1 / 2, "
          "Drum 1-4) to have its 8 knobs and their lights while you hold it; let go and they go back.",
          "To leave, press any track button (*(since RC4)* a short tap, no knob turned) or a view button; held notes are released. Play, "
          "Record, Octave and Shift do not close it."],
         ["A drum button does not open the split keyboard; Synth 1 or Synth 2 alone work as always (pressed twice = the source view).",
          "In RC2 Synth 1 was always on top; since RC2.02 the track you held first goes on top.",
          "Not saved: the split keyboard is closed at power-up."]),
    es=E("Pone dos pistas de notas a la vez en los pads, una encima de otra, para tocar por ejemplo un bajo con una mano y acordes o una "
         "melodía con la otra, cada parte con su escala, su octava y sus colores.",
         ["Mantén **Synth 1** y pulsa **Synth 2** (o al revés). *(desde RC2.02)* Vale cualquier par de **Synth 1, Synth 2, MIDI 1, MIDI "
          "2**: mantén un botón y pulsa otro.",
          "Las dos filas de arriba tocan la pista que mantuviste primero y las dos de abajo la otra, cada una con su escala, su octava, su "
          "velocity y sus colores.",
          "Los knobs y **Octave** son los de la primera pista que pulsaste. *(desde RC4)* **Mantén un botón de pista** (Synth 1 / 2, MIDI "
          "1 / 2, Drum 1-4) para tener sus 8 knobs y sus luces mientras lo mantienes; al soltarlo vuelven.",
          "Para salir, pulsa cualquier botón de pista (*(desde RC4)* un toque corto, sin girar un knob) o de vista; las notas pulsadas se "
          "sueltan. Play, Record, Octave y Shift no lo cierran."],
         ["Un botón de drum no abre el teclado partido; Synth 1 o Synth 2 solos funcionan como siempre (dos veces = la vista de la fuente).",
          "En RC2 arriba iba siempre Synth 1; desde RC2.02 va arriba la pista que mantuviste primero.",
          "No se guarda: al encender, el teclado partido está cerrado."]))

# A15 Synth patch colours
EXPLAIN["colores-patch"] = dict(
    en=E("Shows on the pads of the Synth 1 / 2 Preset view what each patch is, so you can find a sound at a glance. The RCs use the "
         "original's colours; Beta 5.56 colours each patch by its Components category (Bass, Lead, Pad…).",
         ["Select **Synth 1** or **Synth 2** and press **Preset**: the pads are the pack's patches (4 pages, 128 patches).",
          "*(since RC4.10)* As on the original: the patches in the track's colour, the chosen one white.",
          "*(Beta 5.56 only)* Each patch in its Components category's colour: Arp teal, Bass steel blue, Bell light blue, Classic amber, "
          "Drum orange, Keyboard pale lime, Lead yellow, Movement violet, Pad blue, Poly green, SFX red, String peach, User sand, Voc "
          "lavender; None = the track's colour; an empty slot dim white; the chosen one white.",
          "*(Beta 5.56 only)* To give a patch a category on the device, save it: **Clear + pad**, turn **K1** while the slot asks (4 "
          "clicks a category, starting at the patch's own; K1 and the slot show its colour), then **Clear + the same pad**."],
         ["From RC2 to RC4.08 the colour showed the voice mode (mono dark blue, mono with glide lavender, poly the track's colour); since "
          "RC4.10 the RCs use the original's colours, because the card reads behind them sometimes loaded the initial patch.",
          "*(Beta 5.56 only)* The card is read on entering the view, on a new page or pack and after a save or a copy, never when you tap "
          "a patch.",
          "The categories are the ones Components gives each patch. On the computer, the **Nova synths** tab of the [card and device "
          "app](#app-sd) shows the same colours, with the colour key on top. The chart with every category: [Patch "
          "colours](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Patch-Colours)."]),
    es=E("Enseña en los pads de la vista Preset de Synth 1 / 2 qué es cada patch, para encontrar un sonido de un vistazo. Las RC usan los "
         "colores del original; la Beta 5.56 colorea cada patch según su categoría de Components (Bass, Lead, Pad…).",
         ["Elige **Synth 1** o **Synth 2** y pulsa **Preset**: los pads son los patches del pack (4 páginas, 128 patches).",
          "*(desde RC4.10)* Como en el original: los patches en el color de la pista y el elegido en blanco.",
          "*(solo Beta 5.56)* Cada patch en el color de su categoría de Components: Arp verde azulado, Bass azul acero, Bell azul claro, "
          "Classic ámbar, Drum naranja, Keyboard lima claro, Lead amarillo, Movement violeta, Pad azul, Poly verde, SFX rojo, String "
          "melocotón, User arena, Voc lavanda; None = el color de la pista; hueco vacío blanco tenue; el elegido en blanco.",
          "*(solo Beta 5.56)* Para darle categoría a un patch desde el aparato, guárdalo: **Clear + pad**, gira **K1** mientras el hueco "
          "pregunta (4 clics por categoría, empezando en la del patch; K1 y el hueco en su color) y **Clear + el mismo pad**."],
         ["De RC2 a RC4.08 el color enseñaba el modo de voz (mono azul oscuro, mono con glide lavanda, poly el color de la pista); desde "
          "RC4.10 las RC usan los colores del original, porque las lecturas de la tarjeta que había detrás a veces cargaban el patch "
          "inicial.",
          "*(solo Beta 5.56)* La tarjeta se lee al entrar en la vista, al cambiar de página o de pack y tras guardar o copiar, nunca al "
          "tocar un patch.",
          "Las categorías son las que Components da a cada patch. En el ordenador, la pestaña **Sintes Nova** de la [app de la tarjeta y "
          "del aparato](#app-sd) enseña los mismos colores, con la clave de colores arriba. La tabla con todas las categorías: [Colores "
          "de los patches](https://github.com/Ghillermo/CIRCUIT-HACKS-RC/wiki/Patch-Colours-ES)."]))


# ---------------------------------------------------------------------------------------------------- C: New control modes
# C1 Patch morph (Beta 5.56 only)
EXPLAIN["morph"] = dict(
    en=E("Hold two to four patches of the same track and one knob blends from one to the next; two LFOs, an envelope and a slow, timed "
         "morph can also move along that chain for you. It turns a few saved sounds into one evolving sound to play live, on Synth 1 / 2 "
         "and on the MIDI 1 / 2 own synth.",
         ["In the **Preset** view of Synth 1 / 2, or of MIDI 1 / 2 with the own synth on, **hold two to four patches** for 0.4 s (or hold "
          "them and press **Duplicate**): the morph view opens, with the chain in pad order.",
          "**K1** = the position along the chain, in colour: patch 1 red, 2 yellow, 3 green, 4 blue, with shades in between. **K2** = "
          "square LFO depth, **K3** = the rate of both LFOs, **K4** = random-step LFO depth (a new value every half cycle); depths to the "
          "right go towards the chain's end.",
          "**Slow morph:** turn **K5** to a destination (in the same colours) and leave it for half a second: the sound travels from K1 to "
          "K5 over **K6**'s time (fully left at once, then ¼ to 32 bars); once there, K1 takes K5's value. Turning K5 again re-aims from "
          "where the sound is; turning K1 stops it.",
          "**K7 / K8** = envelope depth / time (K8 also smooths both LFOs); **pads 1 / 8** fire the envelope from the top and hold it "
          "while you hold them.",
          "**Clear + knob** = 0; **Clear + the track button** = every knob to 0; **pad 32** (red) = out.",
          "**Preset** shows the patches, the chain's in white: a tap loads that patch and leaves, holding 0.4 s makes a new chain. On MIDI "
          "1 / 2, Preset switches between the morph and the slots. The track button brings the morph view back."],
         ["*(Beta 5.56 only)* Nothing is saved: the morph is a performance tool.",
          "Continuous parameters blend; type parameters (wave, algorithm, mode…) take the nearest patch's. On MIDI 1 / 2 the 8-operator FM "
          "blends too.",
          "One morph at a time: holding patches for 0.4 s in another track's Preset view opens that track's morph and stops the previous "
          "one (its sound stays where it is); a tap there only loads that patch.",
          "The morph keeps going in the other views. Full detail: [Synth 1 / 2 Preset view](#synth-preset)."]),
    es=E("Mantén de dos a cuatro patches de la misma pista y un knob pasa de uno a otro; dos LFO, una envolvente y un morph lento medido "
         "en compases también pueden recorrer esa cadena por ti. Convierte unos pocos sonidos guardados en un solo sonido que evoluciona, "
         "para tocar en directo, en Synth 1 / 2 y en el sinte propio de MIDI 1 / 2.",
         ["En la vista **Preset** de Synth 1 / 2, o de MIDI 1 / 2 con el sinte propio encendido, **mantén de dos a cuatro patches** 0,4 s "
          "(o mantenlos y pulsa **Duplicate**): se abre la vista del morph, con la cadena en el orden de los pads.",
          "**K1** = la posición en la cadena, en color: patch 1 rojo, 2 amarillo, 3 verde, 4 azul, con tonos intermedios. **K2** = "
          "cantidad del LFO cuadrado, **K3** = velocidad de los dos LFO, **K4** = cantidad del LFO de pasos al azar (un valor nuevo en "
          "cada medio ciclo); las cantidades a la derecha van hacia el final de la cadena.",
          "**Morph lento:** gira **K5** hasta un destino (en los mismos colores) y déjalo quieto medio segundo: el sonido va de K1 a K5 en "
          "el tiempo de **K6** (a la izquierda del todo, al momento; luego de ¼ a 32 compases); al llegar, K1 toma el valor de K5. Girar "
          "K5 otra vez cambia el destino desde donde está el sonido; girar K1 lo para.",
          "**K7 / K8** = cantidad / tiempo de la envolvente (K8 también suaviza los dos LFO); los **pads 1 / 8** disparan la envolvente "
          "desde arriba y la sostienen mientras los mantienes.",
          "**Clear + knob** = 0; **Clear + el botón de la pista** = todos los knobs a 0; **pad 32** (rojo) = salir.",
          "**Preset** enseña los patches, los de la cadena en blanco: un toque carga ese patch y sale, mantener 0,4 s hace una cadena "
          "nueva. En MIDI 1 / 2, Preset cambia entre el morph y los huecos. El botón de la pista vuelve a la vista del morph."],
         ["*(solo Beta 5.56)* No se guarda nada: el morph es para tocar en directo.",
          "Los parámetros continuos se mezclan; los de tipo (onda, algoritmo, modo…) toman el del patch más cercano. En MIDI 1 / 2 también "
          "se mezcla el FM de 8 operadores.",
          "Un morph a la vez: mantener patches 0,4 s en la vista Preset de otra pista abre el morph de esa pista y para el anterior (su "
          "sonido se queda donde está); un toque allí solo carga ese patch.",
          "El morph sigue sonando en las otras vistas. Todo el detalle: [Vista Preset de Synth 1 / 2](#synth-preset)."]))


# ---------------------------------------------------------------------------------------------------- A: Shortcuts and usability
# A16 Patches of the own synth (MIDI 1 / 2)
EXPLAIN["patches-midi"] = dict(
    en=E("A sound library for the MIDI tracks' own synth: store the whole MIDI 1 / 2 engine (engine, oscillators, every knob) in slots of "
         "the pack and load it again with one touch, on either track and in any project that uses that pack.",
         ["Open the **Preset** view of **MIDI 1 / 2** (*(since RC4)* also MIDI 1 / 2 again with its Note view on screen, or **Shift + MIDI "
          "1 / 2**): pads 9-24 (rows 2-3) are 16 patch slots.",
          "**Octave ▼ / ▲** = next / previous page (lit when there is one that way): 4 pages, 64 slots per pack; *(since RC4)* 8 pages, "
          "128 slots.",
          "**Load:** touch a slot; while you hold it, the scale's root plays with the new patch. *(since RC4)* **Shift + slot** = load "
          "without the sound.",
          "**Save:** **Clear + slot** (it blinks white: a question), then **Clear + the same slot** within ~5 s: the sound as it is now "
          "replaces what was there. *(Beta 5.56 only)* **Duplicate + an empty slot** = save there at once.",
          "**Swap:** hold **Duplicate**, touch slot A (it blinks), then slot B; onto an empty slot the patch moves. No gesture empties a "
          "slot: overwrite it or move it.",
          "**Start from scratch:** **Clear + MIDI 1 / 2** (a view of that track on screen, CC editor closed) puts every engine value back "
          "to its initial one; the engine chosen stays."],
         ["A patch holds the whole engine: the engine chosen, the oscillators, the chain order, every value of every page and the "
          "step-drummer setting (*(since RC2.02)* the mod matrix; *(since RC4)* the FM, the voice mode and the knob destinations). The "
          "step-drummer's and the FX sequencer's steps belong to the pattern.",
          "The slots belong to the pack and are shared by MIDI 1 and MIDI 2. Writes to the card: not in the S builds nor in the internal "
          "memory's pack (the Save LED turns red). They are hidden while the CC editor or the step-drummer is open.",
          "Colours: dim peach = a patch, bright peach = the last one loaded or saved, violet = empty. *(Beta 5.56 only)* Each patch in its "
          "engine's colour (FM violet, wavetable sand), empty slots dim white.",
          "*(Beta 5.56 only)* Components' «Send patches» / «Send pack» no longer erase them (they used to be lost). A copy saved by "
          "Components has no own-synth patches; the Snapshot of the [card and device app](#app-sd) has them, and its **Custom patches** "
          "tab copies, exports and uploads them (81 example patches are published)."]),
    es=E("Una biblioteca de sonidos para el sinte propio de las pistas MIDI: guarda el motor entero de MIDI 1 / 2 (motor, osciladores, "
         "todos los knobs) en huecos del pack y vuelve a cargarlo con un toque, en cualquiera de las dos pistas y en cualquier proyecto "
         "que use ese pack.",
         ["Abre la vista **Preset** de **MIDI 1 / 2** (*(desde RC4)* también MIDI 1 / 2 otra vez con su vista Note en pantalla, o **Shift "
          "+ MIDI 1 / 2**): los pads 9-24 (filas 2-3) son 16 huecos de patch.",
          "**Octave ▼ / ▲** = página siguiente / anterior (encendidos cuando hay página en ese sentido): 4 páginas, 64 huecos por pack; "
          "*(desde RC4)* 8 páginas, 128 huecos.",
          "**Cargar:** toca un hueco; mientras mantienes el pad suena la tónica de la escala con el patch nuevo. *(desde RC4)* **Shift + "
          "hueco** = cargar sin que suene.",
          "**Guardar:** **Clear + hueco** (parpadea en blanco: pregunta) y **Clear + el mismo hueco** antes de ~5 s: el sonido tal como "
          "está sustituye lo que hubiera. *(solo Beta 5.56)* **Duplicate + un hueco vacío** = guardar ahí al momento.",
          "**Intercambiar:** mantén **Duplicate**, toca el hueco A (parpadea) y luego el B; sobre un hueco vacío, el patch se mueve. No "
          "hay gesto para vaciar un hueco: se sobrescribe o se mueve.",
          "**Empezar de cero:** **Clear + MIDI 1 / 2** (con una vista de esa pista en pantalla y el editor de CC cerrado) devuelve todos "
          "los valores del motor a los iniciales; el motor elegido se queda."],
         ["Un patch guarda el motor entero: el motor elegido, los osciladores, el orden de la cadena, todos los valores de todas las "
          "páginas y el ajuste del step-drummer (*(desde RC2.02)* la matriz de modulación; *(desde RC4)* el FM, el modo de voz y los "
          "destinos de los knobs). Los pasos del step-drummer y del secuenciador de efectos son del patrón.",
          "Los huecos son del pack y los comparten MIDI 1 y MIDI 2. Escribe en la tarjeta: no está en las versiones «S» ni en el pack de "
          "la memoria interna (el LED de Save se pone rojo). No se ven con el editor de CC o el step-drummer abiertos.",
          "Colores: melocotón tenue = con patch, melocotón brillante = el último cargado o guardado, violeta = vacío. *(solo Beta 5.56)* "
          "Cada patch en el color de su motor (FM violeta, wavetable arena) y los vacíos en blanco tenue.",
          "*(solo Beta 5.56)* «Send patches» / «Send pack» de Components ya no los borran (antes se perdían). Una copia guardada por "
          "Components no lleva los patches propios; la Snapshot de la [app de la tarjeta y del aparato](#app-sd) sí, y su pestaña "
          "**Parches custom** los copia, exporta y sube (hay 81 patches de ejemplo publicados)."]))

# A17 Saving the synth’s patch into the pack
EXPLAIN["guardar-patch"] = dict(
    en=E("Stores the Synth 1 / 2 sound you have shaped on the device into one of the pack's 128 patch slots, so you can reuse it in other "
         "projects. On the original this was only possible from Components on a computer.",
         ["Select **Synth 1** or **Synth 2** and press **Preset**; go to the page of the slot you want (4 pages, 128 slots).",
          "**Clear + a slot**: it blinks white (a question; nothing is written yet). *(Beta 5.56 only)* While it asks, **K1** picks the "
          "category to save (4 clicks each, starting at the patch's own; the slot blinks in its colour).",
          "**Clear + the same slot** within ~5 s: the patch as it sounds now is saved there and becomes the chosen one.",
          "Clear + another slot moves the question; a touch without Clear, or waiting, drops it."],
         ["What is saved: the patch in use with every change — its knobs, the MIDI it received and its edited macro destinations. It keeps "
          "the name of the patch that was loaded.",
          "A slot past the end of the bank works too; the slots in between stay empty. The own-synth patch that shares the slot is not "
          "touched.",
          "Writes to the card: not in the S builds nor in the internal memory's pack (the Save LED turns red).",
          "**Duplicate + A + B** in this view still swaps two patches, or copies one to another pack."]),
    es=E("Guarda en uno de los 128 huecos de patch del pack el sonido de Synth 1 / 2 que has moldeado en el aparato, para usarlo en otros "
         "proyectos. En el original solo se podía desde Components, en el ordenador.",
         ["Elige **Synth 1** o **Synth 2** y pulsa **Preset**; ve a la página del hueco que quieras (4 páginas, 128 huecos).",
          "**Clear + un hueco**: parpadea en blanco (pregunta; todavía no se escribe nada). *(solo Beta 5.56)* Mientras pregunta, **K1** "
          "elige la categoría que se guarda (4 clics cada una, empezando en la del patch; el hueco parpadea en su color).",
          "**Clear + el mismo hueco** antes de ~5 s: el patch tal como suena se guarda ahí y queda elegido.",
          "Clear + otro hueco mueve la pregunta; un toque sin Clear, o esperar, la anula."],
         ["Qué se guarda: el patch en uso con todos sus cambios — sus knobs, el MIDI recibido y los destinos de macro editados. Conserva "
          "el nombre del patch que estaba cargado.",
          "Vale también un hueco más allá del final del banco; los huecos de en medio quedan vacíos. El patch del sinte propio que "
          "comparte el hueco no se toca.",
          "Escribe en la tarjeta: no está en las versiones «S» ni en el pack de la memoria interna (el LED de Save se pone rojo).",
          "**Duplicate + A + B** en esta vista sigue intercambiando dos patches, o copiando uno a otro pack."]))

# A18 Macro knob destinations
EXPLAIN["destinos-macro"] = dict(
    en=E("Lets you decide on the device what each of the 8 macro knobs of a Synth 1 / 2 patch moves — up to 4 destinations per knob, each "
         "over its own stretch of the knob's travel and with its own depth — without Components. For example, one knob can open the filter "
         "while it raises the filter drive.",
         ["Open the synth's source view: with **Synth 1 / 2** on screen, press its button again (*(since RC4)*: or **Shift + Synth 1 / "
          "2**).",
          "Touch **pad 32** (teal): the editor is on and the knobs stop moving the macros.",
          "Turn a knob to pick its macro (its LED white); the first turn changes nothing.",
          "Turn it to change the current field; **Octave ▼** = next field, **Octave ▲** = previous: slot 1-4 (yellow) → start 0-127 "
          "(green) → end 0-127 (amber) → destination (white = a CC; light blue, magenta, violet = an NRPN of banks 0, 1, 2) → depth (teal "
          "= positive, red = negative). The pads draw the number.",
          "Any pad releases the macro (the source view's pads come back); **pad 32** turns the editor off; any view button closes it.",
          "To keep the result in the pack, save the patch: **Clear + pad** twice in the Synth 1 / 2 Preset view."],
         ["The destination walks first the 31 parameters that have a CC, by CC number (74 = filter cutoff, 71 = resonance…), then the 39 "
          "that only have an NRPN (envelopes 2 and 3, LFOs, chorus, mod matrix depths). The numbers are those of Novation's Programmer's "
          "Reference Guide; the full list: [Mod matrix and macro destinations](#destinos).",
          "The changes sound at once and live in the project's patch: they are saved with the project; save the patch to use them in other "
          "projects.",
          "On the original these slots can only be edited with Components."]),
    es=E("Decide desde el aparato qué mueve cada uno de los 8 macro knobs de un patch de Synth 1 / 2 — hasta 4 destinos por knob, cada uno "
         "en su propio tramo del recorrido y con su profundidad — sin Components. Por ejemplo, un knob puede abrir el filtro a la vez que "
         "sube el drive del filtro.",
         ["Abre la vista de la fuente del sinte: con **Synth 1 / 2** en pantalla, pulsa su botón otra vez (*(desde RC4)*: o **Shift + "
          "Synth 1 / 2**).",
          "Toca el **pad 32** (verde azulado): el editor se enciende y los knobs dejan de mover los macros.",
          "Gira un knob para elegir su macro (su LED en blanco); el primer giro no cambia nada.",
          "Gíralo para cambiar el campo actual; **Octave ▼** = campo siguiente, **Octave ▲** = anterior: ranura 1-4 (amarillo) → inicio "
          "0-127 (verde) → fin 0-127 (ámbar) → destino (blanco = un CC; azul claro, magenta, violeta = un NRPN de los bancos 0, 1, 2) → "
          "profundidad (verde azulado = positiva, rojo = negativa). Los pads dibujan el número.",
          "Cualquier pad suelta el macro (vuelven los pads de la fuente); el **pad 32** apaga el editor; cualquier botón de vista lo "
          "cierra.",
          "Para dejarlo en el pack, guarda el patch: **Clear + pad** dos veces en la vista Preset de Synth 1 / 2."],
         ["El destino recorre primero los 31 parámetros que tienen CC, por número de CC (74 = corte del filtro, 71 = resonancia…), y "
          "después los 39 que solo tienen NRPN (envolventes 2 y 3, LFO, chorus, profundidades de la matriz de modulación). Los números son "
          "los de la Programmer's Reference Guide de Novation; la lista entera: [Matriz de modulación y destinos de los macros](#destinos).",
          "Los cambios suenan al momento y van en el patch del proyecto: se guardan con el proyecto; guarda el patch para usarlos en otros "
          "proyectos.",
          "En el original estas ranuras solo se editan con Components."]))

# A19 Copying projects to another slot or another pack
EXPLAIN["copiar-proyectos"] = dict(
    en=E("Duplicates a whole project into another slot of the same pack or into another pack, from the device. Useful to start a variation "
         "of a song without touching the original, or to take a project to a pack with other sounds.",
         ["Open **Projects**. Save first if you have changed the project: what is copied is the project as saved on the card.",
          "**Duplicate + pad A** (a slot with a project) = the source: it blinks yellow. Duplicate + A again forgets it.",
          "**Duplicate + pad B** = the copy. An empty B is written at once and turns yellow; a B that holds a project blinks white: repeat "
          "**Duplicate + B** within ~5 s to replace it.",
          "**To another pack:** pick the source, load the other pack, open **Projects** again and do **Duplicate + pad B** there."],
         ["The loaded project's slot is never written. While it copies (a few moments) the device does not respond.",
          "A project stores patch and sample numbers, not the sounds: in another pack it plays with that pack's patches and samples.",
          "The source serves several copies; it is forgotten at power-off or when Master FX is opened.",
          "Writes to the card: not in the S builds. The internal memory's pack can be the source but never the target (the Save LED turns "
          "red)."]),
    es=E("Duplica un proyecto entero en otro hueco del mismo pack o en otro pack, desde el aparato. Sirve para empezar una variación de "
         "una canción sin tocar la original, o para llevar un proyecto a un pack con otros sonidos.",
         ["Abre **Projects**. Si has cambiado el proyecto, guárdalo antes: se copia el proyecto tal como está guardado en la tarjeta.",
          "**Duplicate + pad A** (un hueco con proyecto) = la fuente: parpadea en amarillo. Duplicate + A otra vez la olvida.",
          "**Duplicate + pad B** = la copia. Si B está vacío se escribe al momento y queda en amarillo; si tiene un proyecto parpadea en "
          "blanco: repite **Duplicate + B** antes de ~5 s para sustituirlo.",
          "**A otro pack:** elige la fuente, carga el otro pack, vuelve a **Projects** y haz **Duplicate + pad B** allí."],
         ["El hueco del proyecto cargado nunca se escribe. Mientras copia (unos instantes) el aparato no responde.",
          "Un proyecto guarda números de patch y de sample, no los sonidos: en otro pack suena con los patches y samples de ese pack.",
          "La fuente sirve para varias copias; se olvida al apagar o al abrir Master FX.",
          "Escribe en la tarjeta: no está en las versiones «S». El pack de la memoria interna puede ser la fuente, nunca el destino (el "
          "LED de Save se pone rojo)."]))

# A20 Own-synth patches to another pack
EXPLAIN["patches-entre-packs"] = dict(
    en=E("Takes a sound of the MIDI tracks' own synth from one pack to another without a computer, so a favourite bass or lead can travel "
         "with you to a new pack.",
         ["With the source pack loaded: **MIDI 1 / 2**, **Preset**, **Duplicate + slot A**: the patch is remembered.",
          "Load the other pack and go back to the Preset view of MIDI 1 / 2: **Duplicate** lights yellow (a patch is waiting).",
          "**Duplicate + slot B** writes it there, with its engine, parameters and name. It can go into several slots."],
         ["In the same pack, Duplicate + A + B swaps the two patches instead.",
          "Nothing is copied when A is empty or when the destination pack lacks that patch bank.",
          "The waiting patch is forgotten at power-off. Writes to the card: not in the S builds nor in the internal memory's pack (the "
          "Save LED turns red)."]),
    es=E("Lleva un sonido del sinte propio de las pistas MIDI de un pack a otro sin ordenador, para que un bajo o un lead favorito te "
         "acompañe a un pack nuevo.",
         ["Con el pack de origen cargado: **MIDI 1 / 2**, **Preset**, **Duplicate + hueco A**: el patch queda recordado.",
          "Carga el otro pack y vuelve a la vista Preset de MIDI 1 / 2: **Duplicate** se enciende en amarillo (hay un patch esperando).",
          "**Duplicate + hueco B** lo escribe ahí, con su motor, sus parámetros y su nombre. Sirve para varios huecos."],
         ["Dentro del mismo pack, Duplicate + A + B intercambia los dos patches.",
          "No copia si A está vacío o si el pack de destino no tiene ese banco de patches.",
          "El patch que espera se olvida al apagar. Escribe en la tarjeta: no está en las versiones «S» ni en el pack de la memoria "
          "interna (el LED de Save se pone rojo)."]))

# A21 Shift = a flash on every note (Beta 5.56 only)
EXPLAIN["luces-disparo"] = dict(
    en=E("A quick activity monitor: while you hold Shift, each track's button flashes white every time that track plays a note, so you can "
         "see at a glance which tracks are sounding — handy in a busy project, or to check what MIDI or the arpeggiator is playing.",
         ["Hold **Shift**, in any view.",
          "The eight track buttons (Synth 1 / 2, MIDI 1 / 2, Drum 1-4) flash **white** for 100 ms on every note their track plays, from "
          "the sequencer, the pads, the arpeggiator or MIDI.",
          "Let go of Shift: the buttons go back to normal."],
         ["*Beta 5.56 only.* In the RCs, as on the original, the track buttons stay dark while Shift is held.",
          "A note tied to the next one is one note: one flash."]),
    es=E("Un monitor de actividad rápido: mientras mantienes Shift, el botón de cada pista destella en blanco cada vez que esa pista toca "
         "una nota, y ves de un vistazo qué pistas suenan; útil en un proyecto cargado o para comprobar qué tocan el MIDI o el arpegiador.",
         ["Mantén **Shift**, en cualquier vista.",
          "Los ocho botones de pista (Synth 1 / 2, MIDI 1 / 2, Drum 1-4) destellan en **blanco** durante 100 ms con cada nota que toca su "
          "pista, venga del secuenciador, de los pads, del arpegiador o de MIDI.",
          "Suelta Shift: los botones vuelven a lo normal."],
         ["*Solo Beta 5.56.* En las RC, como en el original, los botones de pista se quedan apagados con Shift.",
          "Una nota ligada a la siguiente es una sola nota: un destello."]))

# A22 Shift + Preset = the project's sound (Beta 5.56 only)
EXPLAIN["proyecto-init"] = dict(
    en=E("An undo for sound tweaks: Shift + Preset throws away the knob changes made to a track and brings its sound back to the one saved "
         "in the project — the whole patch for Synth 1 / 2, the own synth for MIDI 1 / 2.",
         ["Go to a view of **Synth 1 / 2**, or of **MIDI 1 / 2** with its own synth on, and hold **Shift**: **Preset** lights yellow where "
          "it works.",
          "Press **Shift + Preset**. Synth 1 / 2: the synth's whole patch goes back to how the project saved it (or how it was loaded). "
          "MIDI 1 / 2: the own synth goes back to the one saved with the project.",
          "A project without an own synth: MIDI 1 / 2 go back to their defaults, as with **Clear + MIDI 1 / 2**."],
         ["What was turned since is lost: if you want to keep it, save the patch or the project first.",
          "*Beta 5.56 only.* In the RCs, as on the original, Shift + Preset does nothing on these tracks.",
          "With a drum, **Shift + Preset** still opens the chromatic view."]),
    es=E("Un deshacer para los retoques de sonido: Shift + Preset tira los cambios de knobs hechos en una pista y devuelve su sonido al "
         "guardado en el proyecto — el patch entero en Synth 1 / 2, el sinte propio en MIDI 1 / 2.",
         ["Ve a una vista de **Synth 1 / 2**, o de **MIDI 1 / 2** con su sinte propio encendido, y mantén **Shift**: **Preset** se ilumina "
          "en amarillo donde funciona.",
          "Pulsa **Shift + Preset**. Synth 1 / 2: el patch entero del sinte vuelve a como está guardado en el proyecto (o como se cargó). "
          "MIDI 1 / 2: el sinte propio vuelve al guardado con el proyecto.",
          "Un proyecto sin sinte propio: MIDI 1 / 2 vuelven a sus valores por defecto, como con **Clear + MIDI 1 / 2**."],
         ["Lo que se ha girado después se pierde: si quieres conservarlo, guarda antes el patch o el proyecto.",
          "*Solo Beta 5.56.* En las RC, como en el original, Shift + Preset no hace nada en estas pistas.",
          "Con un drum, **Shift + Preset** sigue abriendo la vista cromática."]))


# ---------------------------------------------------------------------------------------------------- B: Exposed controls
# B1 Drum knobs as printed on the panel
EXPLAIN["knobs-drums"] = dict(
    en=E("Each drum's eight knobs do what the panel prints under them (Oscillator, Osc mod, Amp envelope, Filter envelope, Filter "
         "frequency, Resonance, Modulation and FX), and holding **Shift** gives each one a second job. From a single sample you get many "
         "sounds: tune it, ring-modulate it, give it an attack or trim its start and end, filter it in several modes, move it with an LFO, "
         "crush it or distort it.",
         ["Press **Drum 1-4**: the knobs work on that drum.",
          "**K1** pitch (*(since RC2)* the stock one, continuous; the chromatic view's pads transpose on top) · **Shift + K1** how much "
          "the pitch envelope bends each hit.",
          "**K2** ring mod frequency · **Shift + K2** ring mod amount.",
          "**K3** left of the centre = decay (the stock one, at its maximum in the centre); right of the centre = **attack**, a fade-in of "
          "up to 1 s; the centre is neutral · **Shift + K3** left = sample **start**, right = **cut** from the end; centre = the whole "
          "sample.",
          "**K4** filter envelope → cutoff · **Shift + K4** the envelope's shape.",
          "**K5** filter / EQ (the stock EQ tilt by default) · **Shift + K5** the **filter mode**, shown by the LED's colour: green = "
          "stock EQ tilt, yellow = band pass, magenta = notch, teal = comb, white = DJ.",
          "**K6** resonance.",
          "**K7** LFO amount: right = tremolo, left = vibrato (*(since RC4)* left = **start scan**: each hit starts where the LFO is, "
          "inside a range that grows the further left you turn, never past the cut) · **Shift + K7** LFO speed (*(since RC4)* bipolar: "
          "right free, left synced to the tempo).",
          "**K8** distortion; left of 0 = **bitcrush** · **Shift + K8** distortion type: stock, soft, hard, fold.",
          "**Clear + knob** to the right = its default (both layers); **Clear + K3** to the right zeroes attack, start and cut; **Clear + "
          "the drum's button** *(since RC2)* = its knobs' automation in the playing pattern erased and all eight knobs back to their "
          "defaults."],
         ["With every new knob at its neutral point the sample sounds as on the original Circuit; the LED's brightness shows the value.",
          "**Clear + knob to the left** erases that knob's automation in the playing pattern (the stock knobs: pitch, decay, distortion "
          "and EQ), as on the original.",
          "Everything is saved with the project, and every new knob has its own NRPN (see «MIDI tables»).",
          "*(Beta 5.56 only)* The comb mode is gone (Shift + K5 skips it), and each drum gains an extra automation lane and state locks: "
          "[Drum track view](#drum-pista)."]),
    es=E("Los ocho knobs de cada drum hacen lo que dice la serigrafía del panel (Oscillator, Osc mod, Amp envelope, Filter envelope, "
         "Filter frequency, Resonance, Modulation y FX), y con **Shift** cada uno tiene una segunda función. De un solo sample salen "
         "muchos sonidos: afinarlo, pasarlo por un ring mod, darle ataque o recortar su inicio y su final, filtrarlo en varios modos, "
         "moverlo con un LFO, triturarlo o distorsionarlo.",
         ["Pulsa **Drum 1-4**: los knobs actúan sobre ese drum.",
          "**K1** pitch (*(desde RC2)* el de stock, continuo; los pads de la vista cromática transponen encima) · **Shift + K1** cuánto "
          "dobla la envolvente de tono cada golpe.",
          "**K2** frecuencia del ring mod · **Shift + K2** cantidad del ring mod.",
          "**K3** a la izquierda del centro = decay (el de stock, en su máximo en el centro); a la derecha = **ataque**, un fundido de "
          "entrada de hasta 1 s; el centro es neutro · **Shift + K3** a la izquierda = **inicio** del sample, a la derecha = **corte** "
          "desde el final; centro = el sample entero.",
          "**K4** envolvente → corte · **Shift + K4** forma de la envolvente.",
          "**K5** filtro / EQ (de fábrica, el EQ tilt de stock) · **Shift + K5** el **modo de filtro**, con el color del LED: verde = EQ "
          "tilt de stock, amarillo = paso banda, magenta = notch, verde azulado = comb, blanco = DJ.",
          "**K6** resonancia.",
          "**K7** cantidad del LFO: derecha = trémolo, izquierda = vibrato (*(desde RC4)* izquierda = **scan del inicio**: cada golpe "
          "empieza donde está el LFO, dentro de un tramo que crece cuanto más a la izquierda, sin pasar el corte) · **Shift + K7** "
          "velocidad del LFO (*(desde RC4)* bipolar: derecha libre, izquierda a tempo).",
          "**K8** distorsión; a la izquierda de 0, **bitcrush** · **Shift + K8** tipo de distorsión: stock, suave, dura, plegada.",
          "**Clear + knob** a la derecha = su valor por defecto (las dos capas); **Clear + K3** a la derecha pone a 0 ataque, inicio y "
          "corte; **Clear + el botón del drum** *(desde RC2)* = borra la automatización de sus knobs en el patrón que suena y pone los ocho "
          "knobs a sus valores por defecto."],
         ["Con todos los knobs nuevos en su punto neutro, el sample suena como en el Circuit original; el brillo del LED enseña el valor.",
          "**Clear + knob a la izquierda** borra la automatización de ese knob en el patrón que suena (los knobs de stock: pitch, decay, "
          "distorsión y EQ), como en el original.",
          "Todo se guarda con el proyecto, y cada knob nuevo tiene su NRPN (ver «Tablas MIDI»).",
          "*(solo Beta 5.56)* El modo comb ya no está (Shift + K5 se lo salta), y cada drum gana un carril extra de automatización y "
          "bloqueos de estado: [Vista de pista de un drum](#drum-pista)."]))

# B2 Reverb and delay parameters
EXPLAIN["rev-delay"] = dict(
    en=E("The project's reverb and delay, the global effects that the FX view's sends feed, get their settings on the device: **Shift + "
         "knob** in the FX view sets the reverb's type, decay and damping and the delay's time, sync, feedback, width, ratio and slew. Use "
         "it to give each project its own room and echoes without a computer.",
         ["Press **FX**.",
          "**Octave ▼** = the reverb page (the knobs = reverb sends); **Octave ▲** = the delay page (the knobs = delay sends).",
          "Hold **Shift** and turn: reverb **K1** type, **K2** decay, **K3** damping; delay **K1** time, **K2** sync, **K3** feedback, "
          "**K4** width, **K5** ratio, **K6** slew.",
          "Let go of Shift: the knobs are the tracks' sends again."],
         ["Saved with the project, as on the original.",
          "The knob's LED shows the value with its brightness.",
          "If Setup routes the returns through strips 3 / 4, those strips' sends are capped at half.",
          "[FX view](#vista-fx)"]),
    es=E("La reverb y el delay del proyecto, los efectos globales que alimentan los envíos de la vista FX, tienen sus ajustes en el "
         "aparato: **Shift + knob** en la vista FX cambia el tipo, el decay y el damping de la reverb y el time, el sync, el feedback, el "
         "width, el ratio y el slew del delay. Sirve para dar a cada proyecto su espacio y sus ecos sin ordenador.",
         ["Pulsa **FX**.",
          "**Octave ▼** = la página de reverb (los knobs = envíos de reverb); **Octave ▲** = la página de delay (los knobs = envíos de "
          "delay).",
          "Mantén **Shift** y gira: reverb **K1** tipo, **K2** decay, **K3** damping; delay **K1** time, **K2** sync, **K3** feedback, "
          "**K4** width, **K5** ratio, **K6** slew.",
          "Suelta Shift: los knobs vuelven a ser los envíos de las pistas."],
         ["Se guardan con el proyecto, como en el original.",
          "El LED del knob enseña el valor con su brillo.",
          "Si en Setup los retornos van por las tiras 3 / 4, los envíos de esas tiras tienen tope a la mitad.",
          "[Vista FX](#vista-fx)"]))

# B3 Side-chain and master compressor on the knobs
EXPLAIN["sidechain-comp"] = dict(
    en=E("*(since RC2)* The Sidechain view is more than its presets: four knobs set the ducking of the chosen track by hand (attack, hold, "
         "decay and depth) and two more set the master compressor's attack and release. Fine-tune how a pad or a bass breathes with the "
         "kick, or how fast the master compressor grabs and lets go.",
         ["Open the Sidechain view: **Shift + FX**.",
          "Touch one of a track's sidechain presets as always: **K1-K4** now work on that track (Synth 1 until you touch one), with their "
          "LEDs in its colour.",
          "**K1** attack, **K2** hold, **K3** decay, **K4** depth of its ducking.",
          "**K7 / K8** = attack / release of the master compressor (white); the compressor is switched on in Advanced Setup.",
          "With **Octave ▼** (the drum pages), **K1-K4** = attack, hold, decay and depth of the side-chain of the drum whose preset you "
          "touched last, in the drum's colour."],
         ["Touching a preset writes its four values again: the knobs start from the preset and refine it.",
          "Saved with the project: the tracks' and the drums' K1-K4 and the compressor's attack / release. Threshold and ratio are fixed.",
          "*(since RC4.07)* The brightness of K1-K4 rises in a curve, so the presets can be told apart by eye.",
          "Row 1 pads 1-4 *(since RC2)* make Synth 1 / 2 or MIDI 1 / 2 the source (the notes of their pattern): [Sidechain "
          "view](#sidechain)."]),
    es=E("*(desde RC2)* La vista Sidechain es algo más que sus presets: cuatro knobs ajustan a mano el ducking de la pista elegida "
         "(ataque, hold, decay y profundidad) y otros dos el ataque y el release del compresor master. Sirve para afinar cómo respira un "
         "pad o un bajo con el bombo, o lo rápido que agarra y suelta el compresor master.",
         ["Abre la vista Sidechain: **Shift + FX**.",
          "Toca un preset de sidechain de la pista que quieras, como siempre: **K1-K4** pasan a actuar sobre esa pista (Synth 1 si no has "
          "tocado ninguno), con sus LEDs en el color de la pista.",
          "**K1** ataque, **K2** hold, **K3** decay, **K4** profundidad de su ducking.",
          "**K7 / K8** = ataque / release del compresor master (en blanco); el compresor se activa en Advanced Setup.",
          "Con **Octave ▼** (las páginas de drums), **K1-K4** = ataque, hold, decay y profundidad del sidechain del drum del último preset "
          "tocado, en el color del drum."],
         ["Tocar un preset vuelve a escribir sus cuatro valores: los knobs parten del preset y lo afinan.",
          "Se guardan con el proyecto: K1-K4 de las pistas y de los drums y el ataque / release del compresor. El umbral y la ratio son "
          "fijos.",
          "*(desde RC4.07)* El brillo de K1-K4 sube en curva, para distinguir los presets a la vista.",
          "Los pads 1-4 de la fila 1 *(desde RC2)* hacen de Synth 1 / 2 o MIDI 1 / 2 la fuente (las notas de su patrón): [Vista "
          "Sidechain](#sidechain)."]))

# B4 Recording the internal MIDI routes
EXPLAIN["grabar-interno"] = dict(
    en=E("When MIDI 1 / 2 shares its channel with Synth 1 / 2, what you play or turn on the MIDI track sounds on that synth without a "
         "cable (internal loopback), but by default it is recorded only into the MIDI track's pattern. *(since RC2)* The Setup view's "
         "**Record** switch also records it into the synth's pattern, as if it came from an external keyboard: useful for recording scale "
         "or octave changes made live from the MIDI track.",
         ["In the Setup view, give MIDI 1 / 2 the channel of Synth 1 or Synth 2 (track button + channel pad).",
          "Still in the Setup view (not Advanced Setup), press **Record**: **yellow** = on, dark = off (the default).",
          "Record on the MIDI track as usual: what it sends to the synth also lands in the synth's pattern.",
          "*(since RC4)* **Chord bank:** mute the note track in the Mixer (its track pad off): with Record yellow nothing is written into "
          "it; the steps you play on it sound, go out on its channel and are recorded only into the synth that shares the channel."],
         ["Not saved: off by default and off again after every restart.",
          "With it on, the auditions of Synth 1 / 2's step-drummer are recorded too.",
          "[Setup view](#setup)"]),
    es=E("Cuando MIDI 1 / 2 comparte canal con Synth 1 / 2, lo que tocas o giras en la pista MIDI suena en ese sinte sin cable (loopback "
         "interno), pero por defecto solo se graba en el patrón de la pista MIDI. *(desde RC2)* El **Record** de la vista Setup hace que "
         "se grabe también en el patrón del sinte, como si llegara de un teclado externo: sirve para grabar cambios de escala u octava "
         "hechos en directo desde la pista MIDI.",
         ["En la vista Setup, da a MIDI 1 / 2 el canal de Synth 1 o Synth 2 (botón de pista + pad de canal).",
          "En la misma vista Setup (no en Advanced Setup), pulsa **Record**: **amarillo** = activado, apagado = desactivado (por defecto).",
          "Graba como siempre en la pista MIDI: lo que manda al sinte queda también en el patrón del sinte.",
          "*(desde RC4)* **Banco de acordes:** silencia la pista de notas en el Mixer (su pad de pista apagado): con Record en amarillo no "
          "se escribe nada en ella; los pasos que tocas en ella suenan, salen por su canal y se graban solo en el sinte que comparte el "
          "canal."],
         ["No se guarda: apagado por defecto y otra vez apagado tras cada reinicio.",
          "Activado, también se graban las escuchas del step-drummer de Synth 1 / 2.",
          "[Vista Setup](#setup)"]))

# B5 MIDI for everything new
EXPLAIN["midi-io"] = dict(
    en=E("Everything the mod adds can be recorded, played back and controlled over MIDI: turning a new knob sends a CC or an NRPN, and "
         "receiving it moves the knob. Map an external controller to the MIDI tracks' engine, the drums' new knobs or Master FX, or record "
         "their moves in a DAW.",
         ["Let the messages through: the mod follows the Setup's **CC Tx / CC Rx** filters.",
          "**MIDI 1 / 2 engine**, on the track's channel: the stock CC where the function matches (filter CC 74, resonance CC 71, attack "
          "CC 73…), the rest as NRPN with MSB 4 and the parameter's code as LSB, except the LFO speed (NRPN 0:76).",
          "**Drums**, on the drums' channel (10 by default): NRPN MSB 5, 6, 7, 8 = Drum 1-4, LSB 1-14 = the new knobs; the stock knobs "
          "keep their original CCs.",
          "**Master FX**, on channel 16: NRPN MSB 9, LSB = 4 × effect + knob (Gater 0-3, Auto-Filter 4-7, Digitise 8-11, Phaser 12-15, "
          "Glitch 16-19).",
          "To send an NRPN: **CC 99** (MSB), **CC 98** (LSB), then **CC 6** (value); the device remembers the chosen NRPN until the next "
          "CC 99 / 98."],
         ["Values 0-127; on bipolar parameters 64 is the centre. Clear + knob also sends the new value, and the Mixer's level to 100 / 0 "
          "(Shift + knob) goes out as a turn.",
          "With the engine on, MIDI 1 / 2's knobs send this map, never the CC template; with the engine off they send the template (CC "
          "editor, pad 25).",
          "Incoming CC / NRPN move the engine but are not recorded into the pattern nor sent on: only the device's knobs write automation.",
          "No MIDI for the own synth's mod matrix, FM, voice mode and knob destinations: they live in the own patches. Full tables: [MIDI: "
          "own behaviours, new CCs and NRPNs](#midi)."]),
    es=E("Todo lo que añade el mod se puede grabar, reproducir y controlar por MIDI: al girar un knob nuevo sale un CC o un NRPN, y al "
         "recibirlo el knob se mueve. Sirve para mapear un controlador externo al motor de las pistas MIDI, a los knobs nuevos de los "
         "drums o a Master FX, o para grabar sus movimientos en un DAW.",
         ["Deja pasar los mensajes: el mod respeta los filtros **CC Tx / CC Rx** del Setup.",
          "**Motor de MIDI 1 / 2**, por el canal de la pista: el CC de stock donde la función coincide (filtro CC 74, resonancia CC 71, "
          "ataque CC 73…), el resto como NRPN con MSB 4 y el código del parámetro como LSB, salvo la velocidad del LFO (NRPN 0:76).",
          "**Drums**, por el canal de drums (el 10 de fábrica): NRPN MSB 5, 6, 7, 8 = Drum 1-4, LSB 1-14 = los knobs nuevos; los knobs de "
          "stock siguen con sus CC originales.",
          "**Master FX**, por el canal 16: NRPN MSB 9, LSB = 4 × efecto + knob (Gater 0-3, Auto-Filter 4-7, Digitise 8-11, Phaser 12-15, "
          "Glitch 16-19).",
          "Para mandar un NRPN: **CC 99** (MSB), **CC 98** (LSB) y después **CC 6** (valor); el aparato recuerda el NRPN elegido hasta el "
          "siguiente CC 99 / 98."],
         ["Valores 0-127; en los parámetros bipolares, 64 = centro. Clear + knob también manda el valor nuevo, y el nivel a 100 / 0 del "
          "Mixer (Shift + knob) sale como un giro.",
          "Con el motor encendido, los knobs de MIDI 1 / 2 mandan este mapa, nunca la plantilla de CC; con el motor apagado mandan la "
          "plantilla (editor de CC, pad 25).",
          "Los CC / NRPN que entran mueven el motor pero no se graban en el patrón ni se reenvían: solo los knobs del aparato escriben "
          "automatización.",
          "Sin MIDI: la matriz de modulación del sinte propio, el FM, el modo de voz y los destinos de los knobs; van en los patches "
          "propios. Tablas completas: [MIDI: comportamientos propios, CC y NRPN nuevos](#midi)."]))

# B6 Automation of the MIDI engine
EXPLAIN["automatizacion"] = dict(
    en=E("The MIDI 1 / 2 own synth records knob moves into the pattern, like the macros of Synth 1 / 2: one knob page holds the eight "
         "**sequenceable knobs**, each tied to an automation lane, so filter sweeps, pitch moves or effect swells play back with the "
         "pattern. *(since RC4)* You also choose what each lane moves, take a snapshot of the sound into a step and mark steps where the "
         "automation lets go.",
         ["With the engine on, open the **sequenceable knobs**: **pad 4** of the MIDI 1 / 2 Preset view (*(Beta 5.56 only)* **pad 1**). By "
          "default: TUNE, Release, Env → level, Env → filter, Filter, Resonance, LFO speed, Effect.",
          "Press **Record** and **Play** and turn them: the moves go into the pattern's lanes and play back from there.",
          "*(since RC4)* **Shift + knob** = that lane's destination: any of the engine's 33 parameters, in the mod matrix's order and "
          "colours (4 clicks each), while pads 9-24 show where it lives; **Clear held, then Shift + knob** = the factory one.",
          "*(since RC4)* **Snapshot:** in the track view (Note), **Record held + a step pad** writes into that step the parameters that "
          "are not at their initial value (one without a lane takes a lane whose parameter is at its initial value, cleared first); Record "
          "stays as it was.",
          "*(since RC4)* **Let go of the automation:** in the **Velocity** view, **Shift + a step pad** marks it (red): no lane plays "
          "there and what the automation moved goes back to the project's values; again = unmark.",
          "*(since RC4)* **Non-sequenceable knobs:** **Shift + pad 4** (pad 4 then lights pink; *(Beta 5.56 only)* Shift + pad 1) = 8 more "
          "knobs with an assignable destination (Shift + knob) that move their parameter without recording it (unless that parameter is "
          "also on a sequenceable knob).",
          "*(Beta 5.56 only)* In the Velocity view with Shift only the steps with automation are yellow: **Shift + a yellow step** = hear "
          "its values until you let go of Shift (the knobs it moves light yellow); **hold a yellow step + press another** = a straight "
          "sweep between them; **Clear + a step** = erase its knob automation and keep its notes."],
         ["With the step-drummer on, its pitch row uses the TUNE lane (and its page 2 the Release lane): those two are neither played nor "
          "recorded as automation.",
          "**Clear + knob to the left** erases that knob's automation in the playing pattern (both its lanes, with and without Shift).",
          "The lanes and the marks live in the pattern; the destinations are saved with the own-synth patches and *(since RC4)* with the "
          "project.",
          "*(Beta 5.56 only)* While recording, turning an engine knob that is not one of the 8 takes the first empty lane; the snapshot "
          "also works on Synth 1 / 2 (their macros) and the drums (pitch, decay, distortion, EQ). [Knob pages of the MIDI 1 / 2 "
          "engine](#midi-knobs)"]),
    es=E("El sinte propio de MIDI 1 / 2 graba movimientos de knobs en el patrón, como los macros de Synth 1 / 2: una página de knobs tiene "
         "los ocho **knobs secuenciables**, cada uno con su carril de automatización, para que barridos de filtro, cambios de tono o "
         "subidas del efecto suenen con el patrón. *(desde RC4)* Además eliges qué mueve cada carril, haces una foto del sonido en un paso "
         "y marcas pasos donde la automatización se suelta.",
         ["Con el motor encendido, abre los **knobs secuenciables**: **pad 4** de la vista Preset de MIDI 1 / 2 (*(solo Beta 5.56)* **pad "
          "1**). De fábrica: TUNE, Release, Env → nivel, Env → filtro, Filtro, Resonancia, Velocidad del LFO, Efecto.",
          "Pulsa **Record** y **Play** y gíralos: los movimientos quedan en los carriles del patrón y se reproducen desde ahí.",
          "*(desde RC4)* **Shift + knob** = el destino de ese carril: cualquiera de los 33 parámetros del motor, en el orden y los colores "
          "de la matriz de modulación (4 clics cada uno), mientras los pads 9-24 enseñan dónde vive; **Clear mantenido, luego Shift + "
          "knob** = el de fábrica.",
          "*(desde RC4)* **Foto:** en la vista de pista (Note), **Record mantenido + un pad de paso** escribe en ese paso los parámetros "
          "que no están en su valor inicial (uno sin carril toma un carril cuyo parámetro está en el inicial, borrado antes); Record queda "
          "como estaba.",
          "*(desde RC4)* **Soltar la automatización:** en la vista **Velocity**, **Shift + un pad de paso** lo marca (rojo): ahí no suena "
          "ningún carril y lo que movió la automatización vuelve a los valores del proyecto; otra vez = quitar la marca.",
          "*(desde RC4)* **Knobs no secuenciables:** **Shift + pad 4** (el pad 4 se ve entonces en rosa; *(solo Beta 5.56)* Shift + pad 1) "
          "= 8 knobs más con destino asignable (Shift + knob) que mueven su parámetro sin grabarlo (salvo que ese parámetro esté también "
          "en un knob secuenciable).",
          "*(solo Beta 5.56)* En la vista Velocity con Shift solo se ven en amarillo los pasos con automatización: **Shift + un paso "
          "amarillo** = oír sus valores hasta soltar Shift (los knobs que mueve, en amarillo); **mantener un paso amarillo + pulsar otro** "
          "= un sweep en línea recta entre los dos; **Clear + un paso** = borrar la automatización de sus knobs sin tocar sus notas."],
         ["Con el step-drummer activado, su fila de pitch usa el carril de TUNE (y su página 2 el de Release): esos dos ni se reproducen "
          "ni se graban como automatización.",
          "**Clear + knob a la izquierda** borra la automatización de ese knob en el patrón que suena (sus dos carriles, con y sin Shift).",
          "Los carriles y las marcas van en el patrón; los destinos se guardan con los patches del sinte propio y *(desde RC4)* con el "
          "proyecto.",
          "*(solo Beta 5.56)* Grabando, girar un knob del motor que no está en los 8 toma el primer carril vacío; la foto vale también en "
          "Synth 1 / 2 (sus macros) y en los drums (pitch, decay, distorsión, EQ). [Páginas de knobs del motor de MIDI 1 / 2](#midi-knobs)"]))

# B7 Setup and device MIDI
EXPLAIN["setup"] = dict(
    en=E("The Setup and Advanced Setup views gain MIDI and routing options: MIDI 1 / 2 can share a channel with a synth or the drums and "
         "play them from inside (internal loopback), the reverb and delay returns can go through mixer strips 3 / 4, Program Changes get "
         "channels of their own, the Thru jack can merge or filter, and Shift + Clear gives a metronome with count-in. *(since RC4)* Also: "
         "a General MIDI mode for the drums, USB merge, a velocity curve for the pads and an external keyboard to the arpeggiator.",
         ["**Shared channels:** in Setup, pick a track with its button and its channel on pads 1-15; MIDI 1 / 2 may take the channel of "
          "Synth 1 / 2 or the drums, and what they send reaches it internally, without a cable.",
          "**Pad 16** = channel 16 (project and FX), receiving and sending everything but Program Changes. **Pads 22 / 23** = the reverb "
          "return through strip 3 (cream) / the delay return through strip 4 (peach); dim = off.",
          "**Pads 29 / 30** *(since RC2)*: a first touch shows on pads 1-16 the listen / output channel of the project's Program Changes "
          "(white); a pad picks it; the same pad again = PGM Rx / Tx on / off (both 16 by default).",
          "**Shift + Clear** *(since RC2)*, in any view: no metronome (red) → metronome (green) → count-in only (magenta) → both (teal). "
          "With the count-in, **Record** armed + **Play** from stopped = one bar of clicks, then recording starts.",
          "**Advanced Setup, Duplicate** *(since RC2)*: the Thru jack's mode, Thru (dim red) → Out 2 (green) → Merge (yellow) → Filter "
          "(blue).",
          "**Setup K4** *(since RC4)*: General MIDI drums, right = on (green), left = off; **K5-K8** = the GM note of Drum 1-4 (35-81; 36 "
          "/ 38 / 42 / 46 by default), heard once and drawn on the pads; Shift or leaving Setup confirms. Every hit then goes out on the "
          "drums' channel with that note instead of 60 / 62 / 64 / 65; the internal sound does not change.",
          "**Setup, Note** *(since RC4)* = external keyboard to the arpeggiator (green on / dim red off). **Advanced Setup:** **pad 23** "
          "*(since RC4)* = USB merge; **K1** *(since RC4)* = the pads' velocity curve (−8 … +8); **pad 22** *(since RC4.05)* = delayed "
          "save."],
         ["**Merge** copies the DIN In and adds the device's MIDI; **Filter** passes the DIN In except the channels the device listens to; "
          "neither copies SysEx. In Merge, if the device follows the DIN In clock with Clock Tx on, the Thru jack carries two clocks: "
          "switch Clock Tx off.",
          "**Program Changes:** one on the listen channel picks the project (with a listen channel other than 16, channel 16 no longer "
          "does); on the channel of Synth 1 / 2 or the drums it goes to that track; with PGM Tx it is forwarded on the output channel, "
          "where a project picked on the panel also sends its own.",
          "**Count-in:** 4 clicks at the project's tempo (*(since RC4.07)* as a slave, the external clock's), with Record blinking red; "
          "Play cancels it; saved with the project. Click volume: Tempo/Swing + K5. *(since RC4)* With the Mixer's cue mode, the click is "
          "in the cue only.",
          "Thru mode, Program Change channels, GM mode, USB merge, velocity curve and delayed save are saved in the device settings. "
          "*(Beta 5.56 only)* No velocity curve (Setup K1 / K2 = velocity → amplitude / filter), Setup **Preset** = knob hold, Advanced "
          "Setup **K3** = input gain. [Setup view](#setup) · [Advanced Setup view](#advanced-setup)"]),
    es=E("Las vistas Setup y Advanced Setup ganan opciones de MIDI y de ruteo: MIDI 1 / 2 pueden compartir canal con un sinte o los drums "
         "y tocarlos por dentro (loopback interno), los retornos de reverb y delay pueden pasar por las tiras 3 / 4 del mixer, los Program "
         "Change tienen canales propios, el jack Thru puede mezclar o filtrar y Shift + Clear da un metrónomo con cuenta atrás. *(desde "
         "RC4)* Además: modo General MIDI de los drums, fusión USB, curva de velocity de los pads y teclado externo al arpegiador.",
         ["**Canales compartidos:** en Setup, elige una pista con su botón y su canal en los pads 1-15; MIDI 1 / 2 pueden tomar el canal "
          "de Synth 1 / 2 o de los drums, y lo que mandan les llega por dentro, sin cable.",
          "**Pad 16** = canal 16 (proyecto y FX): recepción y envío de todo lo que no es Program Change. **Pads 22 / 23** = el retorno de "
          "reverb por la tira 3 (crema) / el de delay por la tira 4 (melocotón); tenue = apagado.",
          "**Pads 29 / 30** *(desde RC2)*: un primer toque enseña en los pads 1-16 el canal de escucha / salida de los Program Change del "
          "proyecto (blanco); un pad lo elige; el mismo pad otra vez = PGM Rx / Tx encendido / apagado (los dos, el 16 de fábrica).",
          "**Shift + Clear** *(desde RC2)*, en cualquier vista: sin metrónomo (rojo) → metrónomo (verde) → solo cuenta atrás (magenta) → "
          "las dos (verde azulado). Con la cuenta atrás, **Record** armado + **Play** desde parado = un compás de clics y después arranca "
          "la grabación.",
          "**Advanced Setup, Duplicate** *(desde RC2)*: modo del jack Thru, Thru (rojo tenue) → Out 2 (verde) → Merge (amarillo) → Filter "
          "(azul).",
          "**K4 de Setup** *(desde RC4)*: drums General MIDI, a la derecha encendido (verde), a la izquierda apagado; **K5-K8** = la nota "
          "GM de Drum 1-4 (35-81; de fábrica 36 / 38 / 42 / 46), que suena una vez y se dibuja en los pads; Shift o salir de Setup la "
          "confirma. Cada golpe sale entonces por el canal de drums con esa nota en lugar de 60 / 62 / 64 / 65; el sonido interno no "
          "cambia.",
          "**Setup, Note** *(desde RC4)* = teclado externo al arpegiador (verde encendido / rojo tenue apagado). **Advanced Setup:** **pad "
          "23** *(desde RC4)* = fusión USB; **K1** *(desde RC4)* = curva de velocity de los pads (−8 … +8); **pad 22** *(desde RC4.05)* = "
          "guardado diferido."],
         ["**Merge** copia el DIN In y le suma el MIDI del aparato; **Filter** deja pasar el DIN In salvo los canales en los que escucha "
          "el aparato; ninguno copia SysEx. En Merge, si el aparato sigue el reloj del DIN In con Clock Tx encendido, el jack Thru lleva "
          "dos relojes: apaga Clock Tx.",
          "**Program Change:** uno en el canal de escucha elige el proyecto (con un canal de escucha que no es el 16, el 16 ya no elige "
          "proyectos); en el canal de Synth 1 / 2 o de los drums va a esa pista; con PGM Tx se reenvía por el canal de salida, por el que "
          "también sale el de un proyecto elegido en el panel.",
          "**Cuenta atrás:** 4 clics al tempo del proyecto (*(desde RC4.07)* como esclavo, al del reloj externo), con Record parpadeando "
          "en rojo; Play la cancela; se guarda con el proyecto. Volumen del clic: Tempo/Swing + K5. *(desde RC4)* Con el modo cue del "
          "Mixer, el clic suena solo en el cue.",
          "El modo Thru, los canales de Program Change, el modo GM, la fusión USB, la curva de velocity y el guardado diferido se guardan "
          "en los ajustes del aparato. *(solo Beta 5.56)* Sin curva de velocity (K1 / K2 de Setup = velocity → amplitud / filtro), "
          "**Preset** de Setup = retener knob, **K3** de Advanced Setup = ganancia de las entradas. [Vista Setup](#setup) · [Vista "
          "Advanced Setup](#advanced-setup)"]))

# B8 Patch flip on MIDI 1 / 2
EXPLAIN["patch-flip"] = dict(
    en=E("Turns a MIDI track into a sound changer for outside gear: every note the track plays, from the pattern or the pads, goes out as "
         "a Program Change on the track's channel instead of a note (the note number is the program number), so an external synth or "
         "effect changes its sound step by step with the pattern.",
         ["Open the **MIDI 1 / 2 Preset view**.",
          "Tap **pad 26** to switch patch flip on or off.",
          "Play or sequence notes on the track: each one sends its Program Change on the track's channel.",
          "*(Beta 5.56 only)* Pad 26 opens the **flip view** instead (pad 26 white while it is open): on row 3, **pad 17** = patch flip "
          "(PGM seq), **pad 18** = step flip (the jump sequencer), one or the other; tapping the one that is on turns it off; pad 26 again "
          "closes the view."],
         ["Exclusive with the engine: turning the engine on (pad 27) switches patch flip off, and the other way round.",
          "Always on the MIDI track's own channel, never on the project's Program Change output channel; if that channel is a synth's or "
          "the drums', it also acts inside the device.",
          "Saved in the device settings.",
          "[MIDI 1 / 2 Preset view](#midi-preset)"]),
    es=E("Convierte una pista MIDI en un cambiador de sonidos para el equipo externo: cada nota que toca la pista, del patrón o de los "
         "pads, sale como Program Change por el canal de la pista en lugar de como nota (el número de la nota es el número de programa), y "
         "el sinte o el efecto externo cambia de sonido paso a paso con el patrón.",
         ["Abre la **vista Preset de MIDI 1 / 2**.",
          "Toca el **pad 26** para encender o apagar el patch flip.",
          "Toca o secuencia notas en la pista: cada una manda su Program Change por el canal de la pista.",
          "*(solo Beta 5.56)* El pad 26 abre en su lugar la **vista de flip** (pad 26 blanco mientras está abierta): en la fila 3, **pad "
          "17** = patch flip (PGM seq), **pad 18** = step flip (el secuenciador de saltos), uno u otro; tocar el encendido lo apaga; el "
          "pad 26 otra vez cierra la vista."],
         ["Excluyente con el motor: encender el motor (pad 27) apaga el patch flip, y al revés.",
          "Sale siempre por el canal de su pista MIDI, nunca por el canal de salida de Program Change del proyecto; si ese canal es el de "
          "un sinte o el de los drums, actúa también dentro del aparato.",
          "Se guarda en los ajustes del aparato.",
          "[Vista Preset de MIDI 1 / 2](#midi-preset)"]))


# ---------------------------------------------------------------------------------------------------- C: New control modes
# C2 Engine of the MIDI tracks (pad 27)
EXPLAIN["motor-midi"] = dict(
    en=E("MIDI 1 and MIDI 2 get a synth of their own inside the device: their notes play an internal engine (or the track's audio input) "
         "through a VCA, a filter and an effect with envelope and LFO, before mixer strip 3 / 4. The tracks keep sending their MIDI, so "
         "they can play outside gear and sound on the unit at the same time.",
         ["Press **MIDI 1** or **MIDI 2**, then **Preset**. *(since RC4)* Also: the track button again with its Note view on screen, or "
          "**Shift + MIDI 1 / 2**.",
          "*(since RC4)* A tap on **pad 27** opens the engine row on pads 17-24, the current engine bright: off (white), line input "
          "(amber), oscillator (green), VA-drum (orange), granular (magenta), sample (teal), FX sequencer (blue) and FM (violet). Tap one "
          "to pick it; **pad 27** again brings the patch slots back; **Shift + pad 27** steps to the next engine.",
          "*(Beta 5.56 only)* The row is: no voice (white), VCA / VCF / FX only (the line input), oscillator, VA-drum, wavetable (sand), "
          "sample, granular and FM; the FX sequencer is **pad 31** with «no voice» (dim blue; a tap turns it on).",
          "**Pads 1-5** pick the knob page: 1 VCA-VCF, 2 OSC 1 (the granular's page with that engine), 3 OSC 2, 4 sequenceable knobs "
          "(*(since RC4)* **Shift + pad 4** = non-sequenceable), 5 modulation; **pad 6** = the mod matrix *(since RC2.02)*. **Shift** "
          "gives each page a second layer. *(Beta 5.56 only)* Pads 1 and 4 swap: pad 1 = sequenceable knobs, pad 4 = filter / VCA.",
          "**Pad 28** = one / two oscillators (oscillator and VA-drum); **pad 29** = the chain's order, VCA → FX → filter or filter → VCA "
          "→ FX (*(Beta 5.56 only)* the filter first by default); **pad 30** = step-drummer; **pad 31** = velocity → envelopes (VA-drum); "
          "**pad 32** = voice mode *(since RC4)*.",
          "*(since RC4)* Holding a page pad for ½ s shows that page only while held. **Clear + a page pad** = that page back to its "
          "initial values *(since RC2)*; **Clear + the track button** = every engine value to its default (the engine stays)."],
         ["Saved: the engine and its values in the device settings (the same for every project) and, *(since RC4)*, with the project too "
          "(loading a project that carries it brings its sound back). To reuse a sound anywhere in the pack, save it as an own-synth patch "
          "on pads 9-24 (writes to the card: not in the «S» versions nor in the internal pack).",
          "*(since RC2.08)* A keyboard on the track's MIDI channel (USB or DIN) plays its own synth; those notes are not sent again to the "
          "MIDI out.",
          "The track keeps sending its MIDI with any engine; patch flip (pad 26) excludes the engine.",
          "How many voices each engine gives in each voice mode: [Own-synth voices](#midi-voces); every pad: [MIDI 1 / 2 Preset "
          "view](#midi-preset)."]),
    es=E("MIDI 1 y MIDI 2 tienen un sinte propio dentro del aparato: sus notas tocan un motor interno (o la entrada de audio de la pista) "
         "a través de un VCA, un filtro y un efecto con envolvente y LFO, antes de la tira 3 / 4 del mixer. Las pistas siguen mandando su "
         "MIDI, así que pueden tocar un aparato externo y sonar en el propio aparato a la vez.",
         ["Pulsa **MIDI 1** o **MIDI 2** y luego **Preset**. *(desde RC4)* También: el botón de la pista otra vez con su vista Note en "
          "pantalla, o **Shift + MIDI 1 / 2**.",
          "*(desde RC4)* Un toque al **pad 27** abre la fila de motores en los pads 17-24, el motor actual brillante: apagado (blanco), "
          "entrada de línea (ámbar), oscilador (verde), VA-drum (naranja), granular (magenta), muestra (verde azulado), secuenciador de "
          "efectos (azul) y FM (violeta). Toca uno para elegirlo; el **pad 27** otra vez vuelve a los huecos de patches; **Shift + pad "
          "27** pasa al motor siguiente.",
          "*(solo Beta 5.56)* La fila es: sin voz (blanco), solo VCA / VCF / FX (la entrada de línea), oscilador, VA-drum, wavetable "
          "(arena), muestra, granular y FM; el secuenciador de efectos es el **pad 31** con «sin voz» (azul tenue; un toque lo enciende).",
          "Los **pads 1-5** eligen la página de knobs: 1 VCA-VCF, 2 OSC 1 (la del granular en ese motor), 3 OSC 2, 4 knobs secuenciables "
          "(*(desde RC4)* **Shift + pad 4** = no secuenciables), 5 modulación; el **pad 6** = la matriz de modulación *(desde RC2.02)*. "
          "**Shift** da a cada página una segunda capa. *(solo Beta 5.56)* Los pads 1 y 4 cambian de sitio: pad 1 = knobs secuenciables, "
          "pad 4 = filtro / VCA.",
          "**Pad 28** = uno / dos osciladores (oscilador y VA-drum); **pad 29** = el orden de la cadena, VCA → FX → filtro o filtro → VCA "
          "→ FX (*(solo Beta 5.56)* de fábrica, el filtro primero); **pad 30** = step-drummer; **pad 31** = velocity → envolventes "
          "(VA-drum); **pad 32** = modo de voz *(desde RC4)*.",
          "*(desde RC4)* Mantener un pad de página ½ s la enseña solo mientras lo mantienes. **Clear + un pad de página** = esa página a "
          "sus valores iniciales *(desde RC2)*; **Clear + el botón de la pista** = todos los valores del motor por defecto (el motor "
          "elegido se queda)."],
         ["Se guarda: el motor y sus valores en los ajustes del aparato (los mismos para todos los proyectos) y, *(desde RC4)*, también "
          "con el proyecto (cargar un proyecto que lo lleva devuelve su sonido). Para usar un sonido en todo el pack, guárdalo como patch "
          "del sinte propio en los pads 9-24 (escribe en la tarjeta: no en las versiones «S» ni en el pack interno).",
          "*(desde RC2.08)* Un teclado por el canal MIDI de la pista (USB o DIN) toca su sinte propio; esas notas no se reenvían a la "
          "salida MIDI.",
          "La pista sigue mandando su MIDI con cualquier motor; el patch flip (pad 26) excluye el motor.",
          "Cuántas voces da cada motor en cada modo de voz: [Voces del sinte propio](#midi-voces); todos los pads: [Vista Preset de MIDI 1 "
          "/ 2](#midi-preset)."]))

# C3 Step-drummer
EXPLAIN["step-drummer"] = dict(
    en=E("A second layer of sequencing over a track's pattern: the eight knobs are the eight pairs of steps on screen, and each pair moves "
         "one destination (a pitch offset, the wave, FM, the filter… on MIDI 1 / 2; a macro on Synth 1 / 2) on just those two steps. Quick "
         "melodies, accents and timbre changes on top of the notes, without drawing automation.",
         ["MIDI 1 / 2: the Preset view with the engine on, **pad 30** (*(since RC4)* with the step-drummer on, **Note** goes Note → "
          "expanded Note → step-drummer). Synth 1 / 2: the source view (the synth's button twice), **pad 30**.",
          "**Pads 1-16** = the 16 steps of the half shown (bright = a note, white = playing): a touch listens, **Shift + touch** adds or "
          "removes a note; **1-16 / 17-32** shows the other half.",
          "**Pads 17-24** = the destination: on MIDI the pitch of both oscillators, OSC 2's pitch, WAVE, FM, MIX, env → filter, SHAPE or "
          "decay; on the synths macro 1-8.",
          "**K1-K8** = the 8 pairs of steps (the playing one white). On MIDI the value offsets the destination from the centre (64 = no "
          "change); on the synths it is the macro's position, from 0. *(since RC2)* The LED is dim with no modulation and brighter the "
          "further it goes.",
          "**Octave ▲ / ▼** = pitch / velocity page. *(since RC2)* On the velocity page, pads 17-24 pick page 2's own destination (the "
          "same pad again = none); **pad 32** = the pitch-vel toggle (green): the pitch page transposes every note one degree of the scale "
          "every 8 knob steps and the velocity page sets the velocity.",
          "With **Record**, touching a step records it on the step that is playing, with its micro step."],
         ["The pair values are stored in the pattern as automation: on MIDI in the pitch lane and, for page 2, the Release lane (with the "
          "step-drummer on, those two lanes no longer play or record their knobs); on the synths in the macro's lane.",
          "On MIDI, **Shift + pad 30** turns the step-drummer off (pad 30 dim = off, bright = on). Its on / off and destination are kept "
          "in the device settings and the own-synth patch, *(since RC4)* also in the project; the pitch-vel toggle and page 2's "
          "destination, with the project.",
          "*(since RC2)* On Synth 1 / 2, Play and Record no longer close it, and pressing Synth 1 / 2 reopens it until pad 30 closes it. "
          "Each step keeps the pitch of its first note.",
          "With the FX sequencer engine the same view picks Master FX slots instead. Detail: [Step-drummer view](#step-drummer)."]),
    es=E("Una segunda capa de secuenciación sobre el patrón de una pista: los ocho knobs son los ocho pares de pasos de la pantalla, y "
         "cada par mueve un destino (un desplazamiento de tono, la onda, el FM, el filtro… en MIDI 1 / 2; un macro en Synth 1 / 2) solo en "
         "esos dos pasos. Melodías rápidas, acentos y cambios de timbre sobre las notas, sin dibujar automatización.",
         ["MIDI 1 / 2: la vista Preset con el motor encendido, **pad 30** (*(desde RC4)* con el step-drummer encendido, **Note** pasa por "
          "Note → Note ampliada → step-drummer). Synth 1 / 2: la vista de la fuente (el botón del sinte dos veces), **pad 30**.",
          "**Pads 1-16** = los 16 pasos de la mitad mostrada (brillante = con nota, blanco = el que suena): un toque lo escucha, **Shift + "
          "toque** pone o quita una nota; **1-16 / 17-32** enseña la otra mitad.",
          "**Pads 17-24** = el destino: en MIDI el tono de los dos osciladores, el tono del OSC 2, WAVE, FM, MIX, env → filtro, SHAPE o "
          "decay; en los sintes, el macro 1-8.",
          "**K1-K8** = los 8 pares de pasos (el que suena, blanco). En MIDI el valor desplaza el destino desde el centro (64 = sin "
          "cambio); en los sintes es la posición del macro, desde 0. *(desde RC2)* El LED se ve tenue sin modulación y más brillante "
          "cuanto más se aleja.",
          "**Octave ▲ / ▼** = página pitch / velocity. *(desde RC2)* En la página velocity, los pads 17-24 eligen el destino propio de la "
          "página 2 (el mismo pad otra vez = ninguno); el **pad 32** = toggle pitch-vel (verde): la página pitch transpone cada nota un "
          "grado de la escala cada 8 pasos del knob y la página velocity marca la velocity.",
          "Con **Record**, tocar un paso lo graba en el paso que suena, con su micropaso."],
         ["Los valores de los pares se guardan en el patrón como automatización: en MIDI en el carril de tono y, para la página 2, en el "
          "de Release (con el step-drummer activado, esos dos carriles ya no reproducen ni graban sus knobs); en los sintes, en el carril "
          "del macro.",
          "En MIDI, **Shift + pad 30** desactiva el step-drummer (pad 30 tenue = desactivado, brillante = activado). Su estado y su "
          "destino se guardan en los ajustes del aparato y en el patch del sinte propio, *(desde RC4)* también en el proyecto; el toggle "
          "pitch-vel y el destino de la página 2, con el proyecto.",
          "*(desde RC2)* En Synth 1 / 2, Play y Record ya no lo cierran, y pulsar Synth 1 / 2 lo vuelve a abrir hasta que lo cierras con "
          "el pad 30. Cada paso conserva la altura de su primera nota.",
          "Con el motor secuenciador de efectos, la misma vista elige huecos de Master FX. Detalle: [Vista del "
          "step-drummer](#step-drummer)."]))

# C4 FX sequencer
EXPLAIN["fx-seq"] = dict(
    en=E("An engine for MIDI 1 / 2 that makes no sound: the track's step-drummer picks, for each pair of steps, one of the Master FX "
         "bottom-row slots, and every step with a note switches that slot's effect on. It sequences performance effects (stutters, filter "
         "sweeps, the tape-stop gesture…) in time with the pattern.",
         ["First fill the Master FX bottom row: in Master FX, hold an effect of the top row and touch a slot (pads 26-30).",
          "In the MIDI 1 / 2 Preset view pick the FX sequencer: a tap on **pad 27** and the blue engine of the row. *(Beta 5.56 only)* "
          "Pick «no voice» on the row and tap **pad 31** (dim blue → bright). The track's step-drummer switches on.",
          "Open the step-drummer with **pad 30** and put notes on the steps with **Shift + pad**.",
          "Turn each knob (a pair of steps) to pick its slot: 0 none, 1-5 = pads 26-30, 6 = pad 31 (the mechanical gesture) and, at the "
          "end, **random** *(since RC2)* (white LED: one of the slots with an effect, at random on each note). The knob moves slowly "
          "(about one slot every 48 steps of turning) and lights in the colour of the chosen effect.",
          "Press **Play**: on every step with a note, the pair's slot switches on with its copy of the parameters."],
         ["*(since RC4)* A slot with no effect assigned plays the effect at the top of its column (pad 26 = Master FX pad 1 … pad 30 = pad "
          "5), with its knobs, and the knob LED shows that colour.",
          "The track makes no sound of its own; its notes still go out over MIDI.",
          "Leaving the FX sequencer switches the track's step-drummer off. The knob values live in the pattern; the slot assignments, with "
          "the project.",
          "Detail: [Step-drummer view](#step-drummer) and [Master FX](#master-fx)."]),
    es=E("Un motor de MIDI 1 / 2 que no suena: el step-drummer de la pista elige, en cada par de pasos, uno de los huecos de la fila "
         "inferior de Master FX, y cada paso con nota enciende el efecto de ese hueco. Secuencia efectos de directo (stutters, barridos de "
         "filtro, el gesto de parada de cinta…) a tiempo con el patrón.",
         ["Primero llena la fila inferior de Master FX: en Master FX, mantén un efecto de la fila de arriba y toca un hueco (pads 26-30).",
          "En la vista Preset de MIDI 1 / 2 elige el secuenciador de efectos: un toque al **pad 27** y el motor azul de la fila. *(solo "
          "Beta 5.56)* Elige «sin voz» en la fila y toca el **pad 31** (azul tenue → brillante). Se activa el step-drummer de la pista.",
          "Abre el step-drummer con el **pad 30** y pon notas en los pasos con **Shift + pad**.",
          "Gira cada knob (un par de pasos) para elegir su hueco: 0 nada, 1-5 = pads 26-30, 6 = pad 31 (el gesto mecánico) y, al final, "
          "**random** *(desde RC2)* (LED blanco: uno de los huecos con efecto, al azar en cada nota). El knob avanza despacio (un hueco "
          "cada unos 48 pasos de giro) y se ilumina con el color del efecto elegido.",
          "Pulsa **Play**: en cada paso con nota se enciende el hueco del par, con su copia de parámetros."],
         ["*(desde RC4)* Un hueco sin efecto asignado toca el efecto de arriba de su columna (pad 26 = pad 1 de Master FX … pad 30 = pad "
          "5), con sus knobs, y el LED del knob se ve en ese color.",
          "La pista no suena por sí misma; sus notas siguen saliendo por MIDI.",
          "Al salir del secuenciador de efectos se apaga el step-drummer de la pista. Los valores de los knobs van en el patrón; la "
          "asignación de los huecos, con el proyecto.",
          "Detalle: [Vista del step-drummer](#step-drummer) y [Master FX](#master-fx)."]))

# C5 Song pointer (Master FX)
EXPLAIN["song-pointer"] = dict(
    en=E("Pads 9-24 of Master FX are the 16 steps of the pattern, so you can grab the playhead live: repeat one step, loop the stretch "
         "between two steps while you hold them, or latch a loop. Stutters, fills and breakdowns without touching the patterns.",
         ["Open Master FX (**Mixer** twice): pads 9-24 = steps 1-16, the playhead white while the sequencer runs.",
          "**Hold one step:** it repeats while you hold it (retrigger).",
          "**Hold two steps:** the pattern loops between them while you hold them (a momentary phrase).",
          "**Phrase mode (a latched phrase):** **Shift + a step** enters it with that step as the start and 16 as the end, and pad 9 "
          "turns white; then a touch on another step (without Shift) sets the end, so the phrase loops between the two (a step before the "
          "start swaps them; no retrigger); **Shift + another step** moves the start (an end before it goes back to 16).",
          "**Shift + the start** or the white **pad 9** leaves phrase mode."],
         ["**Pad 8** of Master FX releases everything latched, the song pointer included.",
          "Nothing is saved: the song pointer is off when a project loads and at power-up.",
          "Detail: [Master FX](#master-fx)."]),
    es=E("Los pads 9-24 de Master FX son los 16 pasos del patrón, así que puedes agarrar el cabezal en directo: repetir un paso, hacer "
         "bucle entre dos pasos mientras los mantienes o fijar un bucle. Stutters, redobles y breaks sin tocar los patrones.",
         ["Abre Master FX (**Mixer** dos veces): los pads 9-24 = pasos 1-16, el cabezal en blanco mientras el secuenciador corre.",
          "**Mantén un paso:** se repite mientras lo mantienes (retrigger).",
          "**Mantén dos pasos:** el patrón hace bucle entre ellos mientras los mantienes (frase momentánea).",
          "**Modo frase (una frase fijada):** **Shift + un paso** entra en él con ese paso como inicio y el 16 como fin, y el pad 9 se ve "
          "blanco; luego tocar otro paso (sin Shift) fija el fin, así que la frase hace bucle entre los dos (un paso anterior al inicio los "
          "intercambia; sin retrigger); **Shift + otro paso** cambia el inicio (un fin anterior a él vuelve al 16).",
          "**Shift + el inicio** o el **pad 9** blanco sale del modo frase."],
         ["El **pad 8** de Master FX apaga todo lo fijado, también el song pointer.",
          "No se guarda nada: al cargar un proyecto y al encender, el song pointer empieza apagado.",
          "Detalle: [Master FX](#master-fx)."]))

# C6 Captured sample
EXPLAIN["sample"] = dict(
    en=E("Pad 32 of Master FX records up to 3.46 s of what the device is playing and pad 7 plays it back, with its own pitch, mode "
         "(one-shot, gate or loop), start and end. A live sampler: replay or loop a phrase, put it on a slot, turn it into a drum or use "
         "it as a granular source.",
         ["Open Master FX (the FX view's bottom row records too) and press **pad 32** (red): hold it to record while held, or a short tap "
          "to record until the next tap.",
          "**Shift + pad 32** = armed: playing, it records the next bar; stopped, it starts when you press **Play**, from the first beat, "
          "and records that bar.",
          "Press **pad 7** (yellow) to play it; K1-K4 become **K1** pitch (±24 semitones), **K2** mode (yellow one-shot, green gate, blue "
          "loop), **K3** start, **K4** end (end before start = reversed).",
          "**Shift + pad 7** = a latched loop, in any mode, until you press pad 7 (or pad 8) again. The loop mode (K2 blue) only plays "
          "while you hold the pad.",
          "Hold **pad 7** and touch a bottom-row slot: that slot plays the sample with a copy of its knobs. To use it as a drum: drum "
          "Preset view, **Clear + pad**, then **Clear + the same pad**."],
         ["The sample that plays goes through the Master FX effects; the capture records the output without them. *(since RC2.01)* Both "
          "sit before the master filter: the filter acts on the sample as it plays and the capture does not hold it.",
          "It lives in memory: it is lost at power-off, unless it replaced a drum and you saved the project; then it is written into the "
          "pack if it fits (writes to the card: not in the «S» versions nor in the internal pack).",
          "*(Beta 5.56 only)* With the latched loop playing, loading another project or pack (stopped) does not stop it: **Play** blinks "
          "green and the new project starts when the loop comes round; Play again = start now.",
          "It can also be the source of the MIDI tracks' granular and sample mode (Shift + K8 on the granular's page). Detail: [Master "
          "FX](#master-fx)."]),
    es=E("El pad 32 de Master FX graba hasta 3,46 s de lo que suena en el aparato y el pad 7 lo toca, con su propio pitch, modo (one-shot, "
         "gate o loop), inicio y final. Un sampler de directo: vuelve a tocar o haz bucle de una frase, ponla en un hueco, conviértela en "
         "un drum o úsala como fuente del granular.",
         ["Abre Master FX (la fila inferior de la vista FX también graba) y pulsa el **pad 32** (rojo): mantenlo para grabar mientras lo "
          "mantienes, o un toque corto para grabar hasta el siguiente toque.",
          "**Shift + pad 32** = armado: en marcha, graba el compás siguiente; parado, empieza al pulsar **Play**, desde el primer pulso, y "
          "graba ese compás.",
          "Pulsa el **pad 7** (amarillo) para tocarlo; K1-K4 pasan a ser **K1** pitch (±24 semitonos), **K2** modo (amarillo one-shot, "
          "verde gate, azul loop), **K3** start, **K4** end (end antes que start = al revés).",
          "**Shift + pad 7** = bucle enganchado, en cualquier modo, hasta que vuelvas a pulsar el pad 7 (o el pad 8). El modo loop (K2 "
          "azul) solo suena mientras mantienes el pad.",
          "Mantén el **pad 7** y toca un hueco de la fila inferior: ese hueco toca el sample con una copia de sus knobs. Para usarlo como "
          "drum: vista Preset de drums, **Clear + pad** y luego **Clear + el mismo pad**."],
         ["El sample que suena pasa por los efectos de Master FX; la captura graba la salida sin ellos. *(desde RC2.01)* Los dos van antes "
          "del filtro master: el filtro actúa sobre el sample al sonar y la captura no lo lleva.",
          "Vive en la memoria: se pierde al apagar, salvo que haya sustituido a un drum y hayas guardado el proyecto; entonces se escribe "
          "en el pack si cabe (escribe en la tarjeta: no en las versiones «S» ni en el pack interno).",
          "*(solo Beta 5.56)* Con el bucle enganchado sonando, cargar otro proyecto u otro pack (parado) no lo para: **Play** parpadea en "
          "verde y el proyecto nuevo empieza cuando el bucle da la vuelta; Play otra vez = empezar ya.",
          "También puede ser la fuente del granular y del modo muestra de las pistas MIDI (Shift + K8 en la página del granular). Detalle: "
          "[Master FX](#master-fx)."]))

# C7 Glitch (pad 6) and its assignment
EXPLAIN["glitch-pad"] = dict(
    en=E("Holding pad 6 in Master FX hands the whole output to a tape head that reads the last seconds of audio: it can brake, stop, run "
         "backwards, repeat and break up the mix. A performance effect for tape stops, stutters and glitchy fills, which can also be "
         "stored on the bottom-row slots with its settings.",
         ["Open Master FX and **hold pad 6** *(since RC2)*: the Glitch plays while held and pad 6 lights; **Shift + pad 6** latches it "
          "(touch it again to release it).",
          "Its knobs while pressed: **K1** speed (fully up = normal, lower brakes like a tape, centre = stopped, below = backwards), "
          "**K2** repeat size (at maximum no repeat: a continuous delay), **K3** delay (up to about 2.6 s).",
          "**K4**: lower half = **chaos** (random jumps back, cuts and reversals); upper half = **overload** (late blocks that click at "
          "the normal pitch; from about ¾ of the travel everything also slows down and drops in pitch).",
          "**Assign:** hold pad 6 and touch a bottom-row pad (26-30, without Shift): that slot stores a Glitch with the current K1-K4, and "
          "touching it plays the Glitch with those values.",
          "Two Glitch slots at once: the last one pressed plays; let it go and the other comes back with its own values."],
         ["The mechanical gesture (pad 31) uses the same engine: while it plays, the Glitch waits.",
          "The FX sequencer can trigger a Glitch slot. *(since RC2)* The Glitch's knobs are saved with the project, with the other Master "
          "FX knobs.",
          "Detail: [Master FX](#master-fx)."]),
    es=E("Mantener el pad 6 en Master FX pasa toda la salida a una cabeza de cinta que lee los últimos segundos de audio: puede frenar, "
         "parar, ir hacia atrás, repetir y romper la mezcla. Un efecto de directo para paradas de cinta, stutters y redobles glitch, que "
         "también se guarda en los huecos de la fila inferior con sus ajustes.",
         ["Abre Master FX y **mantén el pad 6** *(desde RC2)*: el Glitch suena mientras lo mantienes y el pad 6 se ilumina; **Shift + pad "
          "6** lo fija (tócalo otra vez para soltarlo).",
          "Sus knobs al pulsarlo: **K1** velocidad (arriba del todo = normal, al bajar frena como una cinta, en el centro parada, por "
          "debajo hacia atrás), **K2** tamaño de la repetición (al máximo, sin repetición: un retraso continuo), **K3** retraso (hasta "
          "unos 2,6 s).",
          "**K4**: mitad de abajo = **caos** (saltos atrás, cortes y cambios de sentido al azar); mitad de arriba = **sobrecarga** "
          "(bloques que llegan tarde, con chasquidos al tono normal; desde unos ¾ del recorrido además todo frena y baja de tono).",
          "**Asignar:** mantén el pad 6 y toca un pad de la fila inferior (26-30, sin Shift): ese hueco guarda un Glitch con los K1-K4 "
          "actuales, y tocarlo hace sonar el Glitch con esos valores.",
          "Dos huecos con Glitch a la vez: suena el último que pulsas; al soltarlo vuelve el otro con sus valores."],
         ["El gesto mecánico (pad 31) usa el mismo motor: mientras suena, el Glitch espera.",
          "El secuenciador de efectos puede disparar un hueco con Glitch. *(desde RC2)* Los knobs del Glitch se guardan con el proyecto, "
          "junto a los demás de Master FX.",
          "Detalle: [Master FX](#master-fx)."]))

# C8 Assignable bottom row (Master FX / FX)
EXPLAIN["fila-inferior"] = dict(
    en=E("Pads 26-30 of Master FX (and of the FX view) are five slots you fill yourself: each one keeps an effect together with a copy of "
         "its knob settings, so a ready-made effect is one touch away. The FX sequencer of the MIDI tracks can trigger them in time.",
         ["Open Master FX (**Mixer** twice).",
          "Hold an effect of the top row (pads 1-6), **pad 7** (the captured sample) or **pad 31** (the mechanical gesture) and touch a "
          "slot (pads 26-30): it stores that effect with a copy of its parameters.",
          "Touch the slot: its parameters load and the effect plays while you hold it; **Shift + slot** latches it (pad 8 releases "
          "everything latched).",
          "In the FX view the bottom row is the same: slots 26-30, the mechanical gesture on 31 and the capture's record on 32."],
         ["A slot with nothing assigned keeps the original performance effect of the FX view.",
          "*(since RC2)* The assignments are saved with each project, with the 20 effect knobs, and come back when it loads; a project "
          "saved without them leaves the device as it is. Latched effects are not saved.",
          "*(since RC4)* In the FX sequencer, an empty slot plays the effect at the top of its column.",
          "Detail: [Master FX](#master-fx)."]),
    es=E("Los pads 26-30 de Master FX (y de la vista FX) son cinco huecos que llenas tú: cada uno guarda un efecto con una copia de sus "
         "knobs, así que un efecto ya ajustado queda a un toque. El secuenciador de efectos de las pistas MIDI puede dispararlos a tiempo.",
         ["Abre Master FX (**Mixer** dos veces).",
          "Mantén un efecto de la fila de arriba (pads 1-6), el **pad 7** (el sample capturado) o el **pad 31** (el gesto mecánico) y toca "
          "un hueco (pads 26-30): guarda ese efecto con una copia de sus parámetros.",
          "Toca el hueco: carga sus parámetros y el efecto suena mientras lo mantienes; **Shift + hueco** lo fija (el pad 8 apaga todo lo "
          "fijado).",
          "En la vista FX la fila inferior es la misma: huecos 26-30, el gesto mecánico en el 31 y grabar la captura en el 32."],
         ["Un hueco sin nada asignado sigue siendo el efecto de actuación de la vista FX del original.",
          "*(desde RC2)* Las asignaciones se guardan con cada proyecto, junto a los 20 knobs de los efectos, y vuelven al cargarlo; un "
          "proyecto guardado sin ellas deja el aparato como esté. Los efectos fijados no se guardan.",
          "*(desde RC4)* En el secuenciador de efectos, un hueco vacío toca el efecto de arriba de su columna.",
          "Detalle: [Master FX](#master-fx)."]))

# C9 Random-mutate per step
EXPLAIN["random-mutate"] = dict(
    en=E("Each step of a note track can carry a chance that its notes change when they play: an octave jump or another note of the scale "
         "(in the beta also ghost notes, accents, length and timing). It keeps a pattern alive with small surprises; with Record the "
         "changes are written in and the sequence drifts.",
         ["On Synth 1 / 2 or MIDI 1 / 2 open **Pattern Settings** and touch **pad 25**: the probability view in mode 2.",
          "Hold a step that has notes (pads 1-16) and touch a pad of **row 4** (peach): 25 off; 26 octave 6 %; 27 scale 6 %; 28 both 6 %; "
          "29 scale 12 %; 30 octave 12 %; 31 scale 25 %; 32 octave 25 % and scale 50 %.",
          "*(Beta 5.56 only)* Rows 3-4 are one set of pads per step: 17 no change; 18-20 another note of the scale (×1, ×2, ×4); 21 / 22 "
          "an octave up (low / high); 23 / 24 an octave up or down (low / high); 25 no dynamics; 26 ghost (velocity −32 to 0); 27 accent "
          "staccato (velocity up to +64, the note shorter); 28 length (a half to double); 32 micro steps on / off.",
          "*(Beta 5.56 only)* **Octave ▼ / ▲** with this view open = the track's factor (×0, ×1, ×2, ×4, ×8; ×1 from the factory), which "
          "multiplies every chance: at ×1, note and octave 6 % for each ×1 of the pad, dynamics and micro steps 25 %.",
          "Play: each note of a chord is drawn separately, every time the step plays. Without **Record** the change sounds once; with "
          "Record (and this view on screen) it is written into the step."],
         ["*(since RC2)* Saved in the step, with the pattern and the project; tied notes do not change. «Another note of the scale» "
          "follows the project's scale, the custom one and Jankó too.",
          "**Clear + pad 25** in Pattern Settings clears the dynamics and the random-mutate of every step of the pattern (the frequency "
          "stays).",
          "On the drums the same view changes the sample instead of the note (see «Step frequency and dynamics»). *(Beta 5.56 only)* The "
          "factor is saved with the project; at ×8, pad 24 changes every note.",
          "Detail: [Probability view](#probabilidad)."]),
    es=E("Cada paso de una pista de notas puede llevar una probabilidad de que sus notas cambien al sonar: un salto de octava u otra nota "
         "de la escala (en la beta también notas fantasma, acentos, longitud y desplazamiento). Mantiene vivo un patrón con pequeñas "
         "sorpresas; con Record los cambios se escriben y la secuencia va derivando.",
         ["En Synth 1 / 2 o MIDI 1 / 2 abre **Pattern Settings** y toca el **pad 25**: la vista de probabilidad en modo 2.",
          "Mantén un paso con notas (pads 1-16) y toca un pad de la **fila 4** (melocotón): 25 apagado; 26 octava 6 %; 27 escala 6 %; 28 "
          "las dos 6 %; 29 escala 12 %; 30 octava 12 %; 31 escala 25 %; 32 octava 25 % y escala 50 %.",
          "*(solo Beta 5.56)* Las filas 3-4 son una sola botonera por paso: 17 sin cambios; 18-20 otra nota de la escala (×1, ×2, ×4); 21 "
          "/ 22 una octava arriba (baja / alta); 23 / 24 una octava arriba o abajo (baja / alta); 25 sin dinámicas; 26 ghost (velocity de "
          "−32 a 0); 27 accent staccato (velocity hasta +64, la nota más corta); 28 longitud (de la mitad al doble); 32 micropasos sí / no.",
          "*(solo Beta 5.56)* **Octave ▼ / ▲** con esta vista abierta = el factor de la pista (×0, ×1, ×2, ×4, ×8; de fábrica ×1), que "
          "multiplica todas las probabilidades: con ×1, nota y octava 6 % por cada ×1 del pad, dinámicas y micropasos 25 %.",
          "Al sonar, cada nota de un acorde se sortea aparte, cada vez que suena el paso. Sin **Record** el cambio suena esa vez; con "
          "Record (y esta vista en pantalla) se escribe en el paso."],
         ["*(desde RC2)* Se guarda en el paso, con el patrón y el proyecto; las notas ligadas no cambian. «Otra nota de la escala» sigue "
          "la escala del proyecto, también la propia y Jankó.",
          "**Clear + pad 25** en Pattern Settings borra las dinámicas y el random-mutate de todos los pasos del patrón (la frecuencia se "
          "queda).",
          "En los drums la misma vista cambia el sample en lugar de la nota (ver «Frecuencia y dinámicas por paso»). *(solo Beta 5.56)* El "
          "factor se guarda con el proyecto; con ×8, el pad 24 cambia todas las notas.",
          "Detalle: [Vista de probabilidad](#probabilidad)."]))

# C10 Step frequency and dynamics
EXPLAIN["frecuencia-dinamicas"] = dict(
    en=E("Two more per-step variations for every track: **frequency** makes a step play only on the last of every n passes of its pattern "
         "(1-8), and **dynamics** add random changes of velocity, position and length. Variations that come back every 2, 4 or 8 passes, "
         "and a more human feel.",
         ["**Frequency:** press **Pattern Settings** twice (mode 1); hold a step with notes and touch a pad of **row 4** (yellow): n from "
          "1 to 8, the step plays on the last of every n passes.",
          "**Dynamics:** in Pattern Settings touch **pad 25** (mode 2); hold a step and touch a pad of **row 3**, left to right: no "
          "change; drunk (±2 micro steps); drunk and accents; accents (velocity 0 to +32); dragging and accents (−1 to +3 micro steps); "
          "dragging; balanced dynamics (±32); accent dynamics (−32 to +64).",
          "*(Beta 5.56 only)* In mode 2 the dynamics are pads 25-28 of the shared set (none, ghost, accent staccato, length) and pad 32 "
          "the micro steps (see «Random-mutate per step»).",
          "**Drums** *(since RC2)*: the same view for a drum (Pattern Settings twice = mode 1, the frequency on row 4; **pad 25** of its "
          "Pattern Settings = mode 2); pick a step with a hit. On the RCs, mode 2's row 3 = dynamics (they only delay the hit inside its "
          "step) and pads 25-28 = random-mutate of the sample (none, 25 % ±1 in its row of 8, 25 % ±8 to another row, 12 % of each).",
          "**Clear + pad 25** in a note track's Pattern Settings clears the dynamics and the random-mutate of every step of the pattern; "
          "the frequency stays."],
         ["*(since RC2)* Everything is saved with the step (pattern and project) and travels when the pattern is duplicated and with Nudge.",
          "Each pattern counts its passes from Play; the counters start again when stopped.",
          "With **Record** and mode 2 on screen, what sounds (the mutated note, the dynamics) is written into that track's pattern *(since "
          "RC4.05)*.",
          "*(Beta 5.56 only)* A drum's mode 2 uses the shared set: pads 18-20 another sample of its row (±1), 21-24 another row (+8 or "
          "±8), pad 26 lowers the velocity and adds a roller at random, pad 27 raises it, pad 32 moves the whole step up to 2 micro steps. "
          "Detail: [Probability view](#probabilidad)."]),
    es=E("Dos variaciones más por paso para todas las pistas: la **frecuencia** hace que un paso suene solo en la última de cada n vueltas "
         "de su patrón (1-8), y las **dinámicas** añaden cambios al azar de velocity, posición y duración. Variaciones que vuelven cada 2, "
         "4 u 8 vueltas, y un toque más humano.",
         ["**Frecuencia:** pulsa **Pattern Settings** dos veces (modo 1); mantén un paso con notas y toca un pad de la **fila 4** "
          "(amarillo): n de 1 a 8, el paso suena en la última de cada n vueltas.",
          "**Dinámicas:** en Pattern Settings toca el **pad 25** (modo 2); mantén un paso y toca un pad de la **fila 3**, de izquierda a "
          "derecha: sin cambios; drunk (±2 micropasos); drunk y acentos; acentos (velocity de 0 a +32); arrastre y acentos (de −1 a +3 "
          "micropasos); arrastre; dinámica equilibrada (±32); dinámica de acentos (de −32 a +64).",
          "*(solo Beta 5.56)* En el modo 2 las dinámicas son los pads 25-28 de la botonera común (sin dinámicas, ghost, accent staccato, "
          "longitud) y el pad 32 los micropasos (ver «Random-mutate por paso»).",
          "**Drums** *(desde RC2)*: la misma vista para un drum (Pattern Settings dos veces = modo 1, la frecuencia en la fila 4; **pad "
          "25** de su Pattern Settings = modo 2); elige un paso con golpe. En las RC, la fila 3 del modo 2 = dinámicas (solo retrasan el "
          "golpe dentro de su paso) y los pads 25-28 = random-mutate del sample (nada, 25 % ±1 en su fila de 8, 25 % ±8 a otra fila, 12 % "
          "de cada uno).",
          "**Clear + pad 25** en el Pattern Settings de una pista de notas borra las dinámicas y el random-mutate de todos los pasos del "
          "patrón; la frecuencia se queda."],
         ["*(desde RC2)* Todo se guarda con el paso (patrón y proyecto) y viaja al duplicar el patrón y con Nudge.",
          "Cada patrón cuenta sus vueltas desde Play; los contadores vuelven a empezar al parar.",
          "Con **Record** y el modo 2 en pantalla, lo que suena (la nota mutada, la dinámica) se escribe en el patrón de esa pista *(desde "
          "RC4.05)*.",
          "*(solo Beta 5.56)* El modo 2 de un drum usa la botonera común: los pads 18-20 otro sample de su fila (±1), los 21-24 otra fila "
          "(+8 o ±8), el pad 26 baja la velocity y añade un roller al azar, el 27 la sube y el pad 32 mueve el paso entero hasta 2 "
          "micropasos. Detalle: [Vista de probabilidad](#probabilidad)."]))

# C11 Pattern chains and scenes
EXPLAIN["cadenas"] = dict(
    en=E("Every pattern can carry a rule «play n times, then jump to B; the next time, to C», and every scene can repeat 1-8 times, so the "
         "tracks play A A A B A A A C structures on their own. Song structure without chaining patterns by hand, switched on and off for "
         "the whole project.",
         ["In the **Patterns** view, **Shift + Octave ▲** switches the chain mode of the whole project on (Octave ▲ green) and **Shift + "
          "Octave ▼** off; with Shift, the Octave that does something lights yellow.",
          "In the mode, press a pattern = **A** (yellow; it is selected as usual); **A again** = one more play (up to 8; the knob LEDs "
          "count them).",
          "Press **another pattern of the track** = **B** (green), and the next one = **C** (red). Examples: n = 3 → A A A B A A A C; no C "
          "→ A A A B; n = 1 → A B A C.",
          "**Clear + pattern** in the mode removes its rule (with no rule, it clears the pattern as usual).",
          "In the **Mixer**, **Shift + pads 9-16** = 1-8 repeats of the current scene (the row yellow with Shift, the chosen one green); "
          "*(since RC4)* while playing, with Shift, the repeat now playing is white.",
          "Save a scene (as always) with the mode on: it remembers it and shows **peach**; loading it brings the mode back, and loading a "
          "normal scene switches it off."],
         ["*(since RC2)* B and C play once and the track returns to A, unless they carry a rule of their own; tracks following a rule "
          "blink in the Mixer. A scene ends when its longest chain ends.",
          "The rules are saved with the pattern (they travel when it is duplicated); the mode and the scene data, with the project. With "
          "the mode off the rules stay stored but are not followed.",
          "Out of the mode, **Clear + pattern** clears the pattern, its rule and its play order. The mode stays on when you leave the "
          "Patterns view.",
          "Detail: [Patterns view and pattern chains](#patterns), [Mixer view and scenes](#mixer)."]),
    es=E("Cada patrón puede llevar una regla «suena n veces, luego salta a B; la vez siguiente, a C», y cada escena puede repetirse de 1 a "
         "8 veces, así que las pistas tocan solas estructuras A A A B A A A C. Estructura de canción sin encadenar patrones a mano, "
         "activada o desactivada para todo el proyecto.",
         ["En la vista **Patterns**, **Shift + Octave ▲** activa el modo cadena de todo el proyecto (Octave ▲ en verde) y **Shift + Octave "
          "▼** lo desactiva; con Shift, el Octave que hace algo se ve en amarillo.",
          "En el modo, pulsa un patrón = **A** (amarillo; se selecciona como siempre); **A otra vez** = una repetición más (hasta 8; los "
          "LEDs de los knobs las cuentan).",
          "Pulsa **otro patrón de la pista** = **B** (verde), y el siguiente = **C** (rojo). Ejemplos: n = 3 → A A A B A A A C; sin C → A "
          "A A B; n = 1 → A B A C.",
          "**Clear + patrón** en el modo quita su regla (si no tiene regla, borra el patrón como siempre).",
          "En el **Mixer**, **Shift + pads 9-16** = de 1 a 8 repeticiones de la escena actual (la fila en amarillo con Shift, la elegida "
          "en verde); *(desde RC4)* sonando, con Shift, la repetición que suena se ve en blanco.",
          "Guarda una escena (como siempre) con el modo activo: lo recuerda y se ve en **melocotón**; al cargarla vuelve el modo, y al "
          "cargar una escena normal se desactiva."],
         ["*(desde RC2)* B y C suenan una vez y la pista vuelve a A, salvo que tengan su propia regla; las pistas que siguen una regla "
          "parpadean en el Mixer. Una escena termina cuando termina su cadena más larga.",
          "Las reglas se guardan con el patrón (viajan al duplicarlo); el modo y lo de las escenas, con el proyecto. Con el modo "
          "desactivado las reglas siguen guardadas pero no se aplican.",
          "Fuera del modo, **Clear + patrón** borra el patrón, su regla y su orden de reproducción. El modo sigue activo al salir de la "
          "vista Patterns.",
          "Detalle: [Vista Patterns y cadenas de patrones](#patterns), [Vista Mixer y escenas](#mixer)."]))

# C12 Pattern mutate (Beta 5.56 only)
EXPLAIN["mutate-patrones"] = dict(
    en=E("Each selected track gets a short list of patterns taken from its chain, in another order, that loops instead of the chain; the "
         "patterns themselves do not change. Instant variations of an arrangement that come back with the scenes; it is ported from the "
         "Pattern Mutate of mefisme's Rhythm Plus (MIT licence).",
         ["In the **Patterns** view or the **Mixer**, **Shift + a tap on Duplicate** (yellow with Shift): each selected track loops its "
          "list. Another tap = another seed, another list.",
          "**Shift + Duplicate held** in the Patterns view opens the settings (peach, the chosen value bright): column 1 **Length** 1-4, "
          "column 2 Length 5-8, column 3 the length type (as the chain / exact / random up to Length).",
          "Columns 4-5 = **Amount** in eight steps, how many of the chain's slots change (column 4 top to bottom: all, 7/8, 6/8, 5/8; "
          "column 5: half, 3/8, 2/8, 1/8); column 6 **Repeats** (on / off: two neighbours never the same); column 7 **Keep slot 1** (off / "
          "on).",
          "On that page the **track buttons** pick the tracks (bright = selected); with lists playing, switching one on gives it its list "
          "and switching it off sends it back to its chain. **Duplicate** (or another view button) closes the page.",
          "**Clear + Duplicate**, in any view, ends every list; a pattern pad ends its track's list (and does its usual job)."],
         ["*(Beta 5.56 only)* In the Patterns view, the patterns that are not in a mutating track's list go dark (the playing one keeps "
          "its colour). A new setting is heard at once, and going back to a value brings the same list back.",
          "With pattern chains, a mutating track plays its list and the others follow their rules; for a mutating track the chain ends "
          "with the last pattern of its list, so chained scenes move on when the lists are over.",
          "Saved with the project and in each scene (which tracks mutate, the seed, the settings): going back to a scene brings the same "
          "list back; a scene saved without lists ends them.",
          "In the track views Shift + Duplicate is still the original's. Detail: [Patterns view and pattern chains](#patterns)."]),
    es=E("Cada pista elegida recibe una lista corta de patrones sacados de su cadena, en otro orden, que suena en bucle en lugar de la "
         "cadena; los patrones no cambian. Variaciones del arreglo al momento que vuelven con las escenas; está portado del Pattern Mutate "
         "de Rhythm Plus de mefisme (licencia MIT).",
         ["En la vista **Patterns** o en el **Mixer**, **Shift + un toque a Duplicate** (amarillo con Shift): cada pista elegida toca su "
          "lista en bucle. Otro toque = otra semilla, otra lista.",
          "**Shift + Duplicate mantenido** en la vista Patterns abre los ajustes (melocotón, el valor elegido brillante): columna 1 "
          "**Length** 1-4, columna 2 Length 5-8, columna 3 el tipo de longitud (como la cadena / exacta / al azar hasta Length).",
          "Columnas 4-5 = **Amount** en ocho pasos, cuántos huecos de la cadena cambian (columna 4 de arriba abajo: todo, 7/8, 6/8, 5/8; "
          "columna 5: la mitad, 3/8, 2/8, 1/8); columna 6 **Repeats** (sí / no: dos vecinos nunca iguales); columna 7 **Keep slot 1** (no "
          "/ sí).",
          "En esa página los **botones de pista** eligen las pistas (brillante = elegida); con listas sonando, encender una le da su lista "
          "y apagarla la devuelve a su cadena. **Duplicate** (u otro botón de vista) cierra la página.",
          "**Clear + Duplicate**, en cualquier vista, termina todas las listas; un pad de patrón termina la lista de su pista (y hace lo "
          "de siempre)."],
         ["*(solo Beta 5.56)* En la vista Patterns se apagan los patrones que no están en la lista de una pista que muta (el que suena "
          "conserva su color). Un ajuste nuevo se oye al momento, y volver a un valor devuelve la misma lista.",
          "Con las cadenas de patrones, una pista que muta toca su lista y las demás siguen sus reglas; para una pista que muta la cadena "
          "termina con el último patrón de su lista, así que las escenas encadenadas cambian cuando las listas terminan.",
          "Se guarda con el proyecto y en cada escena (qué pistas mutan, la semilla, los ajustes): al volver a una escena vuelve la misma "
          "lista; una escena guardada sin listas las termina.",
          "En las vistas de pista, Shift + Duplicate sigue siendo lo del original. Detalle: [Vista Patterns y cadenas de "
          "patrones](#patterns)."]))

# C13 Nudge and play orders
EXPLAIN["nudge-ordenes"] = dict(
    en=E("Three extra tools of the Pattern Settings view, on every track and the drums: **Nudge** shifts the content of the selected steps "
         "one step back or forward, and the **fractal** and **deconstructed** orders walk through the pattern in another order without "
         "changing its steps. Quick rhythmic variations of a pattern you already have.",
         ["Open **Pattern Settings** and set the range with the first / last step pads (1-16), as always.",
          "**Pad 26** (blue) = **Nudge**: a tap moves the content of the range one step back, **Shift + pad 26** one step forward; what "
          "leaves at one end comes in at the other, and the first and last steps do not move *(since RC4.05)*.",
          "**Pad 27** = **fractal** order: 1 · 1 2 · 1 2 3 · 1 2 3 4 … up to the last step, then again.",
          "**Pad 28** = **deconstructed** order: the grid's diagonals, 1 6 11 16 · 2 7 12 13 · 3 8 9 14 · 4 5 10 15 (the same with 17-32); "
          "steps outside the pattern are skipped (with 8 steps: 1 6 2 7 3 8 4 5).",
          "Pads 27 / 28 and the four direction pads (29-32) exclude each other: a direction pad brings back a normal direction."],
         ["*(since RC2)* Nudge moves whole steps with their automation (on the drums with their own values too), and the view shows it at "
          "once.",
          "The order is saved with the pattern; clearing the pattern removes it.",
          "For chains, scenes and the frequency, the pattern ends when the whole run of its order ends.",
          "Detail: [Pattern Settings view](#pattern-settings)."]),
    es=E("Tres herramientas más de la vista Pattern Settings, en todas las pistas y en los drums: **Nudge** mueve el contenido de los "
         "pasos elegidos un paso atrás o adelante, y los órdenes **fractal** y **deconstruido** recorren el patrón en otro orden sin "
         "cambiar sus pasos. Variaciones rítmicas rápidas de un patrón que ya tienes.",
         ["Abre **Pattern Settings** y fija el tramo con los pads de primer / último paso (1-16), como siempre.",
          "**Pad 26** (azul) = **Nudge**: un toque mueve el contenido del tramo un paso atrás, **Shift + pad 26** un paso adelante; lo que "
          "sale por un extremo entra por el otro, y el primer y el último paso no se mueven *(desde RC4.05)*.",
          "**Pad 27** = orden **fractal**: 1 · 1 2 · 1 2 3 · 1 2 3 4 … hasta el último paso, y vuelve a empezar.",
          "**Pad 28** = orden **deconstruido**: las diagonales de la rejilla, 1 6 11 16 · 2 7 12 13 · 3 8 9 14 · 4 5 10 15 (y lo mismo con "
          "17-32); los pasos de fuera del patrón se saltan (con 8 pasos: 1 6 2 7 3 8 4 5).",
          "Los pads 27 / 28 y los cuatro de dirección (29-32) se excluyen entre sí: un pad de dirección vuelve a una dirección normal."],
         ["*(desde RC2)* Nudge mueve los pasos completos con su automatización (en los drums también sus valores propios), y la vista lo "
          "enseña al momento.",
          "El orden se guarda con el patrón; borrar el patrón lo quita.",
          "Para las cadenas, las escenas y la frecuencia, el patrón termina al acabar el recorrido entero de su orden.",
          "Detalle: [Vista Pattern Settings](#pattern-settings)."]))

# C14 Arpeggiator (since RC2)
EXPLAIN["arpegiador"] = dict(
    en=E("Each pattern of a note track can have its own arpeggiator: the pattern's chords and the notes you hold (*(since RC4)* also a "
         "held step or an external keyboard) play one note at a time, in the order and resolution you choose. On the drums it jumps "
         "between the samples you hold.",
         ["In a note track's **Pattern Settings**, **Shift + pad 25** = the arpeggiator of the pattern that plays, on / off (without "
          "Shift, pad 25 green while it is on).",
          "**Shift + pads 27-32** = its order: fractal, deconstructed, up, down, ping-pong, random (apart from the pattern's direction); "
          "**Shift + pads 17-24** = its resolution, 1/4, 1/4T, 1/8, 1/8T, 1/16, 1/16T, 1/32, 1/32T (the same pad again = the track's sync "
          "rate).",
          "*(since RC4)* With it on, **Shift + pads 1-16** = modifiers: 1-4 octaves (sand), 5-8 when the octave moves (sky blue), 9-12 "
          "groove (amber), 13-16 reset (pink).",
          "Play: the first note sounds as always; hold another with it and the held notes are arpeggiated until you let go. With "
          "**Record** the chord is recorded and the sequence arpeggiates it.",
          "*(since RC4)* Stopped, holding a step with several notes arpeggiates them; **Shift + a key** (Note view) latches a note into "
          "the arpeggio; pressing that key again lets it go, and **Clear + the track button** lets go of all (it also resets the track: "
          "Synth 1 / 2's macros to the loaded patch, the MIDI 1 / 2 own synth to its initial values).",
          "**Drums:** the same gestures in a drum's Pattern Settings; in its **Preset** view hold several samples and the drum jumps from "
          "one to the next (with Record, each hit is recorded with its sample as the step's sample flip)."],
         ["*(since RC2)* Saved with the project, per track and pattern number: duplicating a pattern does not copy it.",
          "*(since RC4)* With the **Note** button of the Setup view on (off by default), notes coming in over MIDI on the track's channel "
          "are arpeggiated too. The notes go in the order they were pressed, and the step's random-mutate applies to them.",
          "Each note lasts its own gate, at most one arpeggio step. The **Micro Step** view (Gate twice) adds gate by holding (pad 32) and "
          "a fixed length (pad 31) for notes entered by hand; the arpeggio uses those gates.",
          "*(since RC2.04)* A note or chord held for more than 16 steps while recording goes on, tied, 16 steps later. Detail: [Pattern "
          "Settings view](#pattern-settings)."]),
    es=E("Cada patrón de una pista de notas puede tener su propio arpegiador: los acordes del patrón y las notas que mantienes (*(desde "
         "RC4)* también un paso mantenido o un teclado externo) suenan de una en una, con el orden y la resolución que elijas. En los "
         "drums salta entre los samples que mantienes.",
         ["En el **Pattern Settings** de una pista de notas, **Shift + pad 25** = el arpegiador del patrón que suena, encendido / apagado "
          "(sin Shift, el pad 25 se ve verde mientras está encendido).",
          "**Shift + pads 27-32** = su orden: fractal, deconstruido, arriba, abajo, ping-pong, aleatorio (aparte de la dirección del "
          "patrón); **Shift + pads 17-24** = su resolución, 1/4, 1/4T, 1/8, 1/8T, 1/16, 1/16T, 1/32, 1/32T (el mismo pad otra vez = el "
          "sync rate de la pista).",
          "*(desde RC4)* Encendido, **Shift + pads 1-16** = modificadores: 1-4 octavas (arena), 5-8 cuándo cambia la octava (azul cielo), "
          "9-12 groove (ámbar), 13-16 reinicio (rosa).",
          "Al tocar: la primera nota suena como siempre; mantén otra a la vez y las notas mantenidas se arpegian hasta que las sueltas. "
          "Con **Record** se graba el acorde y la secuencia lo arpegia después.",
          "*(desde RC4)* Parado, mantener un paso con varias notas las arpegia; **Shift + tecla** (vista Note) fija una nota en el "
          "arpegio; pulsar esa tecla otra vez la suelta, y **Clear + el botón de la pista** las suelta todas (además reinicia la pista: "
          "los macros de Synth 1 / 2 a los del patch cargado, el sinte propio de MIDI 1 / 2 a sus valores iniciales).",
          "**Drums:** los mismos gestos en el Pattern Settings de un drum; en su vista **Preset** mantén varios samples y el drum salta de "
          "uno a otro (con Record, cada golpe se graba con su sample como sample flip del paso)."],
         ["*(desde RC2)* Se guarda con el proyecto, por pista y número de patrón: duplicar un patrón no lo copia.",
          "*(desde RC4)* Con el botón **Note** de la vista Setup encendido (apagado de fábrica), también se arpegian las notas que llegan "
          "por MIDI al canal de la pista. Las notas van en el orden en que se pulsaron, y el random-mutate del paso se les aplica.",
          "Cada nota dura su propio gate, como mucho un paso de arpegio. La vista **Micro Step** (Gate dos veces) añade el gate por "
          "pulsación (pad 32) y la longitud fija (pad 31) para las notas introducidas a mano; el arpegio usa esos gates.",
          "*(desde RC2.04)* Una nota o un acorde mantenido más de 16 pasos al grabar sigue, ligado, 16 pasos después. Detalle: [Vista "
          "Pattern Settings](#pattern-settings)."]))

# C15 Drums micro-step rollers (since RC2)
EXPLAIN["rollers"] = dict(
    en=E("Rows 1-3 of the drums' Note view become rollers: while you hold one, its drum plays on every step at that micro step. Rolls and "
         "ratchets played live (stopped too) and recorded with Record.",
         ["Select a drum and open the drums' **Note** view (press **Note** until rows 1-3 show dim pads): rows 1-3 are the rollers, row 4 "
          "the drum boxes.",
          "Each column belongs to the drum of the box below it (columns 1-4 = drums 4-1, columns 5-8 = drums 1-4): a drum's left column is "
          "its micro steps 1-3 (rows 1-3), the right one 4-6; drum 1 = pads 4, 12, 20 and 5, 13, 21.",
          "Hold one or several rollers (of one or several drums): the drum plays on every step at those micro steps, with the step's "
          "velocity (100 on an empty step); they light while held.",
          "Stopped, they play at the project's tempo, starting when you press the first one.",
          "With **Record** (playing), their hits are recorded into the pattern (the micro step; velocity 100 on an empty step)."],
         ["*(since RC2)* Several rollers at once combine.",
          "Pads 25-28 of the same view repeat the boxes of drums 4 … 1 (a mirrored copy).",
          "In a stereo pair, Drum 1 / 3's rollers drive both drums. Detail: [Chromatic and scale view of the drums](#drum-cromatica)."]),
    es=E("Las filas 1-3 de la vista Note de los drums pasan a ser rollers: mientras mantienes uno, su drum suena en cada paso en ese "
         "micropaso. Redobles y ratchets en directo (también parado) y grabados con Record.",
         ["Elige un drum y abre la vista **Note** de los drums (pulsa **Note** hasta que las filas 1-3 se vean tenues): las filas 1-3 son "
          "los rollers y la fila 4 los cuadros de los drums.",
          "Cada columna es del drum del cuadro de debajo (columnas 1-4 = drums 4-1, columnas 5-8 = drums 1-4): la columna izquierda de un "
          "drum son sus micropasos 1-3 (filas 1-3) y la derecha los 4-6; el drum 1 = pads 4, 12, 20 y 5, 13, 21.",
          "Mantén uno o varios rollers (de uno o varios drums): el drum suena en cada paso en esos micropasos, con la velocity del paso "
          "(100 en un paso vacío); se encienden mientras los mantienes.",
          "Parado, suenan al tempo del proyecto, empezando al pulsar el primero.",
          "Con **Record** (en marcha), sus golpes se graban en el patrón (el micropaso; velocity 100 en un paso vacío)."],
         ["*(desde RC2)* Varios rollers a la vez se combinan.",
          "Los pads 25-28 de la misma vista repiten los cuadros de los drums 4 … 1 (una copia en espejo).",
          "En una pareja estéreo, los rollers de Drum 1 / 3 mueven los dos drums. Detalle: [Vista cromática y de escala de los "
          "drums](#drum-cromatica)."]))

# C16 Custom scale (since RC2)
EXPLAIN["escala-propia"] = dict(
    en=E("Build your own scale for the note tracks: up to 7 notes over the root and a free period, the interval after which the scale "
         "repeats (not necessarily the octave), drawn on a piano keyboard. *(since RC4)* The same editor turns on the isomorphic Jankó "
         "layout, where every chord has the same shape in any key.",
         ["Press **Shift + Scales** (yellow with Shift; *(since RC4)* also **Scales** twice): the editor opens on two octaves of a piano "
          "from the root (row 4 the first octave's white keys, row 3 its black keys, rows 2 / 1 the second octave).",
          "Press keys to add or remove them (up to 7): the highest one pressed is the **period** (blue), the others the notes (green), the "
          "root white.",
          "Play the note tracks (Synth 1 / 2, MIDI 1 / 2): each row of pads is one iteration, its notes and the period at the end (two "
          "iterations a row with 4 notes or fewer); **Octave ▼ / ▲** move one row.",
          "Scales again, Shift + Scales or another view close the editor; picking a stock scale switches the custom one off (its keys are "
          "kept) and the editor switches it on again.",
          "*(since RC4)* **Jankó:** in the editor, **Shift + pad 8** (teal while on): every column a whole tone up, the rows in pairs (the "
          "upper one a semitone lower); Octave = a semitone per tap, an octave when held about half a second. On the RCs, **Shift + pad "
          "24** = the earlier layout (each row a semitone above the one below)."],
         ["*(since RC2)* Saved with the project; a new project starts without a custom scale. The root is the Scales view's, picked as "
          "always.",
          "It drives playing, the lit notes of the sequence, quantising and random-mutate (another note of the same iteration).",
          "*(Beta 5.56 only)* One Jankó layout: in the expanded Note view the upper pair repeats the lower one, and with a key held Octave "
          "moves only the other pair (not saved: back to 0 at power-off).",
          "Detail: [Scales view and custom scale](#escalas)."]),
    es=E("Crea tu propia escala para las pistas de notas: hasta 7 notas sobre la tónica y un periodo libre, el intervalo tras el que la "
         "escala se repite (no tiene por qué ser la octava), dibujadas en un teclado de piano. *(desde RC4)* El mismo editor enciende la "
         "disposición isomórfica Jankó, en la que cada acorde tiene la misma forma en cualquier tono.",
         ["Pulsa **Shift + Scales** (amarillo con Shift; *(desde RC4)* también **Scales** dos veces): el editor se abre con dos octavas de "
          "piano desde la tónica (fila 4 las blancas de la primera octava, fila 3 sus negras, filas 2 / 1 la segunda octava).",
          "Pulsa teclas para ponerlas o quitarlas (hasta 7): la más alta pulsada es el **periodo** (azul), las demás las notas (verdes), "
          "la tónica blanca.",
          "Toca las pistas de notas (Synth 1 / 2, MIDI 1 / 2): cada fila de pads es una iteración, sus notas y el periodo al final (dos "
          "iteraciones por fila con 4 notas o menos); **Octave ▼ / ▲** mueven una fila.",
          "Scales otra vez, Shift + Scales u otra vista cierran el editor; elegir una escala de stock apaga la propia (sus teclas se "
          "guardan) y el editor la vuelve a encender.",
          "*(desde RC4)* **Jankó:** en el editor, **Shift + pad 8** (verde azulado mientras está encendida): cada columna sube un tono, "
          "las filas por parejas (la de encima medio tono más grave); Octave = medio tono por toque, una octava mantenido casi medio "
          "segundo. En las RC, **Shift + pad 24** = la disposición anterior (cada fila medio tono más aguda que la de abajo)."],
         ["*(desde RC2)* Se guarda con el proyecto; un proyecto nuevo empieza sin escala propia. La tónica es la de la vista Scales, que "
          "se elige como siempre.",
          "Vale para tocar, para las notas que se iluminan en la secuencia, el cuantizado y el random-mutate (otra nota de la misma "
          "iteración).",
          "*(solo Beta 5.56)* Una sola disposición Jankó: en la Note ampliada la pareja de arriba repite la de abajo, y con una tecla "
          "mantenida Octave mueve solo la otra pareja (no se guarda: al apagar vuelve a 0).",
          "Detalle: [Vista Scales y escala propia](#escalas)."]))

# C17 Chord screen (since RC4)
EXPLAIN["acordes"] = dict(
    en=E("In the expanded Note view of Synth 1 / 2 and MIDI 1 / 2, the chord screen turns each pad of rows 3-4 into a whole chord: pick "
         "its type, inversion and voicing on rows 1-2 and play chords with one finger. What you play is recorded as plain notes, and the "
         "arpeggiator can arpeggiate it.",
         ["Open the expanded Note view (**Note** twice) and press **Shift + pad 8** (yellow with Shift, green while on); the same gesture "
          "turns it off.",
          "**Row 1** = the type: major, minor, 7, m7, maj7, sus4, dim, aug; **Shift + pads 1-7**: sus2, 6, m6, add9, 9, 7sus4, fifth "
          "(yellow with Shift, the chosen one white).",
          "**Row 2:** pads 9-12 the inversion (root position, 1st, 2nd, 3rd; blue), pad 13 open voicing, pad 14 the root an octave down, "
          "pad 15 diatonic (the thirds of the project's scale), pad 16 the chord latch (*(Beta 5.56 only)* the inverse chord, mirrored "
          "downwards from the root); pads 13-16 green when on.",
          "**Rows 3-4** = the roots, the same notes as the Note view's keyboard: hold one and its chord sounds (up to 6 notes, with the "
          "pad's velocity).",
          "**Shift + a root** = chord latch: it keeps sounding until you press that root again, **Clear + the track button** (which also "
          "resets the track: Synth 1 / 2's macros to the loaded patch, the MIDI 1 / 2 own synth to its initial values) or the screen goes "
          "off (with Shift, its root bright teal)."],
         ["*(since RC4)* Changing the type, the inversion or a modifier while a chord sounds changes it at once; two chords at once share "
          "their common notes.",
          "Recorded with Record as plain notes of the pattern: it plays back the same without the screen. With the arpeggiator on, one "
          "finger plays an arpeggiated chord.",
          "The type and the modifiers are not saved (lost at power-off). On MIDI 1 / 2 in the sample mode, the expanded Note view stays "
          "the sample picker.",
          "Detail: [Synth 1 / 2 track view](#synth-nota)."]),
    es=E("En la Note ampliada de Synth 1 / 2 y MIDI 1 / 2, la pantalla de acordes convierte cada pad de las filas 3-4 en un acorde entero: "
         "elige su tipo, su inversión y su voicing en las filas 1-2 y toca acordes con un dedo. Lo que tocas se graba como notas normales, "
         "y el arpegiador puede arpegiarlo.",
         ["Abre la Note ampliada (**Note** dos veces) y pulsa **Shift + pad 8** (amarillo con Shift, verde mientras está encendida); el "
          "mismo gesto la apaga.",
          "**Fila 1** = el tipo: mayor, menor, 7, m7, maj7, sus4, dim, aum; **Shift + pads 1-7**: sus2, 6, m6, add9, 9, 7sus4, quinta "
          "(amarillos con Shift, el elegido blanco).",
          "**Fila 2:** pads 9-12 la inversión (fundamental, 1.ª, 2.ª, 3.ª; azul), pad 13 voicing abierto, pad 14 la fundamental una octava "
          "abajo, pad 15 diatónico (las terceras de la escala del proyecto), pad 16 el latch del acorde (*(solo Beta 5.56)* el acorde "
          "inverso, reflejado hacia abajo desde la fundamental); los pads 13-16 en verde encendidos.",
          "**Filas 3-4** = las fundamentales, las mismas notas que el teclado de la vista Note: mantén una y suena su acorde (hasta 6 "
          "notas, con la velocity del pad).",
          "**Shift + fundamental** = latch del acorde: sigue sonando hasta que vuelves a pulsar esa fundamental, **Clear + el botón de la "
          "pista** (que además reinicia la pista: los macros de Synth 1 / 2 a los del patch cargado, el sinte propio de MIDI 1 / 2 a sus "
          "valores iniciales) o se apaga la pantalla (con Shift, su fundamental en verde azulado brillante)."],
         ["*(desde RC4)* Cambiar el tipo, la inversión o un modificador con un acorde sonando lo cambia al momento; dos acordes a la vez "
          "comparten sus notas comunes.",
          "Se graba con Record como notas normales del patrón: se reproduce igual sin la pantalla. Con el arpegiador encendido, un dedo "
          "toca un acorde arpegiado.",
          "El tipo y los modificadores no se guardan (se pierden al apagar). En MIDI 1 / 2 con el modo muestra, la Note ampliada sigue "
          "siendo el selector de samples.",
          "Detalle: [Vista de pista de Synth 1 / 2](#synth-nota)."]))

# C18 Stereo drum pairs (since RC4)
EXPLAIN["pareja-estereo"] = dict(
    en=E("Two drums can play one stereo sample: Drum 1 / 3 sounds on the left and Drum 2 / 4 on the right with the pack's next sample, "
         "both driven by Drum 1 / 3's knobs and pattern. The device's samples are mono, so a stereo loop or hit stored as two pack slots "
         "in a row plays as one.",
         ["**Hold Drum 1 and press Drum 2** (or the other way round; **Drum 3 + Drum 4** the same): the pair is made; the same gesture "
          "undoes it.",
          "Program **Drum 1 / 3** as usual: its knobs (with Shift too), its pattern, level, sends and side-chain drive both; its pan is "
          "the pair's centre.",
          "**Drum 2 / 4's knobs** are deviations from Drum 1 / 3: **K1** detune (±100 cents), **K2** stereo width (full by default; fully "
          "left, both centred), the others offset Drum 1 / 3's decay, sample start, filter, resonance, LFO amount…; **Clear + knob** = no "
          "deviation.",
          "For another second sample, pick it in **Drum 2 / 4's Preset view**: that sets the distance between the two, and it then follows "
          "Drum 1 / 3's sample changes."],
         ["*(since RC4)* Not with Shift, Clear or Duplicate held, nor in Setup. Drum 2 / 4's button pulses in Drum 1 / 3's colour while "
          "the pair lasts.",
          "Drum 2 / 4's own pattern does not play during the pair (it stays saved); its pads and MIDI notes play it alone, on the right. "
          "Its own knob values come back when the pair is undone.",
          "Saved with the project (on, distance, width and deviations).",
          "Every knob of the pair: [Drum track view](#drum-pista)."]),
    es=E("Dos drums pueden tocar un sample estéreo: Drum 1 / 3 suena a la izquierda y Drum 2 / 4 a la derecha con el sample siguiente del "
         "pack, los dos con los knobs y el patrón de Drum 1 / 3. Los samples del aparato son mono, así que un loop o un golpe estéreo "
         "guardado en dos huecos seguidos del pack suena como uno solo.",
         ["**Mantén Drum 1 y pulsa Drum 2** (o al revés; **Drum 3 + Drum 4** igual): se forma la pareja; el mismo gesto la deshace.",
          "Programa **Drum 1 / 3** como siempre: sus knobs (también con Shift), su patrón, su nivel, sus envíos y su sidechain valen para "
          "los dos; su panorama es el centro de la pareja.",
          "**Los knobs de Drum 2 / 4** son desviaciones sobre Drum 1 / 3: **K1** desafinación (±100 cents), **K2** apertura estéreo (de "
          "fábrica, del todo; a la izquierda del todo, los dos al centro), los demás desvían el decay, el inicio del sample, el filtro, la "
          "resonancia, la cantidad del LFO… de Drum 1 / 3; **Clear + knob** = sin desviación.",
          "Para otro segundo sample, elígelo en la **vista Preset de Drum 2 / 4**: fija la distancia entre los dos, y después sigue los "
          "cambios de sample de Drum 1 / 3."],
         ["*(desde RC4)* No con Shift, Clear o Duplicate pulsados, ni en Setup. El botón de Drum 2 / 4 late en el color de Drum 1 / 3 "
          "mientras dura la pareja.",
          "El patrón propio de Drum 2 / 4 no suena mientras dura la pareja (se queda guardado); sus pads y sus notas MIDI lo tocan solo, a "
          "la derecha. Sus propios valores de knobs vuelven al deshacer la pareja.",
          "Se guarda con el proyecto (encendida, distancia, apertura y desviaciones).",
          "Todos los knobs de la pareja: [Vista de pista de un drum](#drum-pista)."]))

# C19 The drums' extra lane (Beta 5.56 only)
EXPLAIN["carril-extra"] = dict(
    en=E("Each drum gets one more automation lane, stored inside its pattern: from the factory it holds the chromatic pitch of the "
         "chromatic view's pads, and it can carry one of the drum's new knobs instead or switch to state locks (all 14 new knob values per "
         "step, with ramps between them). An automation view shows, previews and edits it all.",
         ["**Record held + a knob** assigns that parameter to the lane: K2, K4, K6, K7, Shift + K1, Shift + K2, Shift + K4 or Shift + K7; "
          "**Record held + a chromatic view pad** = the chromatic pitch again. While Record is held, the assigned knob lights white (with "
          "the chromatic pitch, Preset blinks white).",
          "While recording, turning the assigned knob writes the step that plays (one value a step); **Clear + that knob to the left** "
          "erases the lane in the playing pattern (the chromatic pitch: Clear + K1).",
          "**State locks:** **Record held + 1-16/17-32** in any of the drum's views switches between the lane and state locks (the lane is "
          "erased in the drum's 8 patterns). While recording, turning one of the 14 knobs stores a state in the step that plays; three in "
          "a straight line become a ramp. **Record held + a step** = a state of the values now.",
          "**Automation view:** the drum's **Velocity** view with **Shift** held, or latched by pressing **Velocity** again: steps with "
          "automation yellow, ramps dim yellow, marked steps red.",
          "There, **Shift + a yellow step** = its values on the knobs (yellow) and in the sound until you let go of Shift; **Shift + a "
          "step without automation** = a mark (red: the project's values come back on it); **Clear + a step** = its automation erased, the "
          "hit kept; in state locks, hold a step and tap another = a ramp."],
         ["*(Beta 5.56 only)* The assignment (lane or state locks) is saved with the project, the values with the pattern; up to 80 states "
          "per project. The lane travels with Duplicate, Nudge and Shift + Play.",
          "On the drums fixed velocity stays on Shift + Velocity (Velocity twice latches the automation view).",
          "*(since RC4.02)* With Record + Play, each chromatic view pad records a hit with its pitch on its own step (its micro step and "
          "velocity); Shift + Play moves the pitch with its hit.",
          "Detail: [Drum track view](#drum-pista), [Chromatic and scale view of the drums](#drum-cromatica)."]),
    es=E("Cada drum tiene un carril de automatización más, guardado en su propio patrón: de fábrica lleva el pitch cromático de los pads "
         "de la vista cromática, y puede llevar en su lugar uno de los knobs nuevos del drum o pasar a bloqueos de estado (los 14 valores "
         "de los knobs nuevos por paso, con rampas entre ellos). Una vista de automatización lo enseña, lo escucha y lo edita todo.",
         ["**Record mantenido + un knob** le asigna ese parámetro: K2, K4, K6, K7, Shift + K1, Shift + K2, Shift + K4 o Shift + K7; "
          "**Record mantenido + un pad de la vista cromática** = otra vez el pitch cromático. Mientras mantienes Record, el knob asignado "
          "se ve blanco (con el pitch cromático, Preset parpadea en blanco).",
          "Grabando, girar el knob asignado escribe el paso que suena (un valor por paso); **Clear + ese knob a la izquierda** borra el "
          "carril en el patrón que suena (el pitch cromático: Clear + K1).",
          "**Bloqueos de estado:** **Record mantenido + 1-16/17-32** en cualquier vista del drum cambia entre el carril y los bloqueos de "
          "estado (el carril se borra en los 8 patrones del drum). Grabando, girar uno de los 14 knobs guarda un estado en el paso que "
          "suena; tres en línea recta se vuelven rampa. **Record mantenido + un paso** = un estado con los valores de ahora.",
          "**Vista de automatización:** la vista **Velocity** del drum con **Shift** mantenido, o fijada pulsando **Velocity** otra vez: "
          "pasos con automatización en amarillo, rampas en amarillo tenue, marcados en rojo.",
          "Ahí, **Shift + un paso amarillo** = sus valores en los knobs (en amarillo) y en el sonido hasta soltar Shift; **Shift + un paso "
          "sin automatización** = una marca (rojo: ahí vuelven los valores del proyecto); **Clear + un paso** = borra su automatización y "
          "deja el golpe; en bloqueos de estado, mantén un paso y toca otro = una rampa."],
         ["*(solo Beta 5.56)* La asignación (carril o bloqueos de estado) se guarda con el proyecto, los valores con el patrón; hasta 80 "
          "estados por proyecto. El carril viaja con Duplicate, Nudge y Shift + Play.",
          "En los drums la velocity fija queda en Shift + Velocity (Velocity dos veces fija la vista de automatización).",
          "*(desde RC4.02)* Con Record + Play, cada pad de la vista cromática graba un golpe con su tono en su propio paso (su micropaso y "
          "su velocity); Shift + Play mueve el tono con su golpe.",
          "Detalle: [Vista de pista de un drum](#drum-pista), [Vista cromática y de escala de los drums](#drum-cromatica)."]))

# C20 Sample mode of the MIDI tracks (since RC2)
EXPLAIN["modo-muestra"] = dict(
    en=E("A MIDI track plays any sample of the pack one-shot at the pitch of each note (C3 = as recorded), through the engine's filter, "
         "effect and LFO: pitched drums or a simple sampler on a MIDI track. Each step can play a different sample (sample flip), and "
         "*(since RC4)* two samples can play as a stereo pair.",
         ["In the MIDI 1 / 2 Preset view tap **pad 27** and pick the **sample** engine (teal).",
          "Press **Note** twice: the expanded Note view is the picker. **Pads 17-32** = 16 of the pack's samples (**Octave ▼ / ▲** = the 4 "
          "pages, all 64): a touch picks the track's sample and plays it; *(since RC4)* **Shift + sample** picks it silently.",
          "**Pads 1-16** = the steps of the half shown (**1-16 / 17-32** = the other half): **hold a step and touch a sample** = that "
          "step's sample flip (peach); you can also hold a sample and touch steps; **Clear + step** = no flip.",
          "Play notes from the Note view, the step-drummer or incoming MIDI: C3 (note 60) = as recorded, an octave up = twice as fast; "
          "every note restarts the sample, which plays to its end.",
          "With **Record + Play**, touching a sample records a note 60 on the playing step, with its flip.",
          "*(since RC4)* **Stereo:** K7 of the OSC 1 page (WAVE; *(Beta 5.56 only)* K3) = the width: the chosen sample on the left, the "
          "second on the right (the next one at first); **Shift + the chosen sample** in the picker switches to picking the second."],
         ["The VCA stays open (the envelope does not close it; gain, velocity and LFO → level still work). *(since RC4)* In the poly voice "
          "mode up to 4 notes sound at once.",
          "The flips live in the track's level automation lane (Mixer): a flip replaces the level recorded on its step, and recording the "
          "level over it erases those flips. *(since RC4)* A flip on a step without a note adds the last note played there (peach = note "
          "and flip, teal = note only, violet = flip only).",
          "The track's sample is the granular's source too (Shift + K8 on its page): changing one changes the other, and the capture is "
          "picked there. The sample is saved with the engine values; the flips, with the pattern.",
          "Detail: [Sample mode and sample picker](#midi-muestra)."]),
    es=E("Una pista MIDI toca cualquier sample del pack de un golpe, a la altura de cada nota (C3 = como se grabó), por el filtro, el "
         "efecto y el LFO del motor: drums con altura o un sampler sencillo en una pista MIDI. Cada paso puede tocar un sample distinto "
         "(sample flip), y *(desde RC4)* dos samples pueden sonar como una pareja estéreo.",
         ["En la vista Preset de MIDI 1 / 2, un toque al **pad 27** y elige el motor **muestra** (verde azulado).",
          "Pulsa **Note** dos veces: la Note ampliada es el selector. **Pads 17-32** = 16 samples del pack (**Octave ▼ / ▲** = las 4 "
          "páginas, los 64): un toque elige el sample de la pista y suena; *(desde RC4)* **Shift + sample** lo elige sin que suene.",
          "**Pads 1-16** = los pasos de la mitad mostrada (**1-16 / 17-32** = la otra mitad): **mantén un paso y toca un sample** = el "
          "sample flip de ese paso (melocotón); también puedes mantener un sample y tocar pasos; **Clear + paso** = sin flip.",
          "Toca notas desde la vista Note, el step-drummer o el MIDI de entrada: C3 (nota 60) = como se grabó, una octava arriba = el "
          "doble de rápido; cada nota vuelve a empezar el sample, que suena hasta el final.",
          "Con **Record + Play**, tocar un sample graba una nota 60 en el paso que suena, con su flip.",
          "*(desde RC4)* **Estéreo:** el K7 de la página OSC 1 (WAVE; *(solo Beta 5.56)* K3) = la anchura: el sample elegido a la "
          "izquierda y el segundo a la derecha (de entrada, el siguiente); **Shift + el sample elegido** en el selector pasa a elegir el "
          "segundo."],
         ["El VCA se queda abierto (la envolvente no lo cierra; la ganancia, la velocity y el LFO → nivel siguen). *(desde RC4)* Con el "
          "modo de voz poly suenan hasta 4 notas a la vez.",
          "Los flips van en el carril de automatización de nivel de la pista (Mixer): un flip sustituye el nivel grabado en su paso, y "
          "grabar el nivel encima borra esos flips. *(desde RC4)* Un flip en un paso sin nota añade allí la última nota tocada (melocotón "
          "= nota y flip, verde azulado = solo nota, violeta = solo flip).",
          "El sample de la pista es también la fuente del granular (Shift + K8 en su página): cambiar uno cambia el otro, y la captura se "
          "elige allí. El sample se guarda con los valores del motor; los flips, con el patrón.",
          "Detalle: [Modo muestra y selector de samples](#midi-muestra)."]))

# C21 Mod matrix of the own synth (since RC2.02)
EXPLAIN["matriz-mod"] = dict(
    en=E("Eight modulation sources for the MIDI 1 / 2 own synth (velocity, note, a random value per note, a second LFO, a second envelope, "
         "a drum hit, the pattern position and stepped random), each sent with a single knob to any of the engine's 33 parameters. "
         "Movement and expression without automating by hand.",
         ["With the engine on, press **pad 6** of the MIDI 1 / 2 Preset view (light blue): **K1-K8** are the sources: K1 velocity, K2 "
          "note, K3 random on each note, K4 LFO 2, K5 envelope 2, K6 a drum hit, K7 pattern position, K8 stepped random.",
          "Turn a knob to the right: its position picks the **destination** (33 parameters, one stretch each: 16 steps of two clicks) and, "
          "inside the stretch, the **amount**; fully left = off.",
          "The LED takes the colour of the destination's page (amber VCA-VCF, green OSC 1, teal OSC 2) and its brightness is the amount; "
          "while you turn (and 1.5 s after), the pads show where the destination lives (its page pad, and pads 9-16 / 17-24 = that page's "
          "K1-K8 / Shift + K1-K8).",
          "**With Shift:** K4 = LFO 2's shape × rate (*(since RC4)* the left half of each shape synced to the tempo), K5 = attack × decay, "
          "K6 = which drum (1-4) × decay, K8 = N steps (1, 2, 4, 8, 16).",
          "**Clear + knob** = that source off; **Clear + Shift + knob** = its parameter back to its default; **Clear + pad 6** = all off."],
         ["A full amount sweeps the parameter's whole range; it is added when the value is sent (the stored value does not change), and "
          "several sources on one destination add up. Note, random, LFO 2 and stepped random go up and down; the others only up.",
          "*(since RC2.02)* Saved with the own-synth patches (pads 9-24) and, *(since RC4)*, with the project. No CC / NRPN.",
          "The modulations reach the engine about 100-250 times a second, shared among everything that moves on the track.",
          "Detail: [Mod matrix](#midi-matriz)."]),
    es=E("Ocho fuentes de modulación para el sinte propio de MIDI 1 / 2 (velocity, nota, un valor al azar por nota, un segundo LFO, una "
         "segunda envolvente, un golpe de drum, la posición en el patrón y azar por pasos), cada una llevada con un solo knob a cualquiera "
         "de los 33 parámetros del motor. Movimiento y expresión sin automatizar a mano.",
         ["Con el motor encendido, pulsa el **pad 6** de la vista Preset de MIDI 1 / 2 (azul claro): **K1-K8** son las fuentes: K1 "
          "velocity, K2 nota, K3 azar en cada nota, K4 LFO 2, K5 envolvente 2, K6 golpe de un drum, K7 posición en el patrón, K8 azar por "
          "pasos.",
          "Gira un knob a la derecha: su posición elige el **destino** (33 parámetros, un tramo cada uno: 16 pasos de dos clics) y, dentro "
          "del tramo, la **cantidad**; a la izquierda del todo = apagado.",
          "El LED toma el color de la página del destino (ámbar VCA-VCF, verde OSC 1, verde azulado OSC 2) y su brillo es la cantidad; "
          "mientras giras (y 1,5 s después), los pads enseñan dónde vive el destino (el pad de su página, y los pads 9-16 / 17-24 = los "
          "K1-K8 / Shift + K1-K8 de esa página).",
          "**Con Shift:** K4 = forma × velocidad del LFO 2 (*(desde RC4)* la mitad izquierda de cada forma a tempo), K5 = ataque × caída, "
          "K6 = qué drum (1-4) × caída, K8 = N pasos (1, 2, 4, 8, 16).",
          "**Clear + knob** = esa fuente apagada; **Clear + Shift + knob** = su parámetro al valor inicial; **Clear + pad 6** = todo "
          "apagado."],
         ["La cantidad entera recorre todo el rango del parámetro; se suma al enviar el valor (el valor guardado no cambia), y varias "
          "fuentes en un destino se suman. Nota, azar, LFO 2 y azar por pasos suben y bajan; las demás solo suben.",
          "*(desde RC2.02)* Se guarda con los patches del sinte propio (pads 9-24) y, *(desde RC4)*, con el proyecto. No tiene CC / NRPN.",
          "Las modulaciones llegan al motor unas 100-250 veces por segundo, repartidas entre todo lo que se mueve en la pista.",
          "Detalle: [Matriz de modulación](#midi-matriz)."]))

# C22 Jump sequencer of MIDI 1 / 2 (Beta 5.56 only)
EXPLAIN["saltos"] = dict(
    en=E("A MIDI track can stop sounding and move another track's pattern instead: each of its notes makes that track jump to the step the "
         "note stands for, on the very same step. A way to rearrange or stutter a drum loop or a phrase from a sequence of notes.",
         ["In the MIDI 1 / 2 Preset view, **pad 26** opens the flip view (pad 26 white while it is open).",
          "On row 3, **pad 18** = step flip (**pad 17** = patch flip; tapping the one that is on turns it off).",
          "On row 2, tap the **target** among the eight tracks (in their colours, the target bright); with none picked, the last one used "
          "(Synth 1 from the factory). With the view closed, pad 26 blinks in the target's colour.",
          "Write or play the track's notes: in its Note view **pads 17-32 = steps 1-16** and **Octave ▲** = steps 17-32; in the expanded "
          "Note view the 32 pads = steps 1-32. Each note makes the target jump to that step.",
          "Stopped, a pad sounds that step of the target while you hold it, without jumping."],
         ["*(Beta 5.56 only)* While pointing, the track plays no notes (no engine, no MIDI); pointing turns the engine off, and turning an "
          "engine on stops pointing.",
          "A step's probability, 1 in N and random-mutate still apply; a track muted in the Mixer makes no jump. MIDI 1 and MIDI 2 can "
          "point at the same time.",
          "With the same length on both tracks a jump is only noticeable the first time: use different lengths, or two jumps (one to move "
          "it, one to bring it back).",
          "Saved with the project. Detail: [MIDI 1 / 2 Preset view](#midi-preset)."]),
    es=E("Una pista MIDI puede dejar de sonar y mover el patrón de otra pista: cada una de sus notas hace saltar esa pista al paso que "
         "indica, en ese mismo paso. Una forma de reordenar o hacer stutter de un loop de drums o de una frase con una secuencia de notas.",
         ["En la vista Preset de MIDI 1 / 2, el **pad 26** abre la vista de flip (pad 26 blanco mientras está abierta).",
          "En la fila 3, **pad 18** = step flip (**pad 17** = patch flip; tocar el encendido lo apaga).",
          "En la fila 2, toca el **destino** entre las ocho pistas (en sus colores, el destino brillante); sin elegir, el último usado (de "
          "fábrica, Synth 1). Con la vista cerrada, el pad 26 parpadea en el color del destino.",
          "Escribe o toca las notas de la pista: en su vista Note **pads 17-32 = pasos 1-16** y **Octave ▲** = pasos 17-32; en la Note "
          "ampliada los 32 pads = pasos 1-32. Cada nota hace saltar al destino a ese paso.",
          "Parado, un pad hace sonar ese paso del destino mientras lo mantienes, sin saltar."],
         ["*(solo Beta 5.56)* Mientras apunta, la pista no toca notas (ni motor ni MIDI); apuntar apaga el motor, y encender un motor deja "
          "de apuntar.",
          "Valen la probabilidad, el 1 de cada N y el random-mutate del paso; una pista silenciada en el Mixer no hace saltar. MIDI 1 y "
          "MIDI 2 pueden apuntar a la vez.",
          "Con la misma longitud en las dos pistas, un salto solo se nota la primera vez: usa longitudes distintas, o dos saltos (uno que "
          "la mueva y otro que la devuelva).",
          "Se guarda con el proyecto. Detalle: [Vista Preset de MIDI 1 / 2](#midi-preset)."]))

# C23 4-operator FM (since RC4)
EXPLAIN["fm4"] = dict(
    en=E("A 4-operator FM synth as a variant of the own synth's oscillator, with 16 algorithms (classic, percussive, bells and strings) "
         "for electric pianos, basses, bells, metallic hits and drums. Each operator has an attack / release envelope with a fixed "
         "sustain, and 16 starter sounds are one press away.",
         ["In the MIDI 1 / 2 Preset view tap **pad 27** and pick **pad 24** of the engine row (violet); **pad 7** opens its knob page.",
          "**K1-K4** = the ratio of operators 1-4 (the extra clicks of each ratio detune it slightly); **K5-K8** = their level.",
          "**Shift + K1-K4** = to the right the operator's attack, to the left it becomes percussive with its own decay; **Shift + K5** = "
          "algorithm (16); **Shift + K6** feedback; **Shift + K7** noise; **Shift + K8** release (longer the harder the note).",
          "**Hold pad 7:** pads 9-24 = the 16 algorithms in their family's colour; press one to pick it and hear it (**Shift + pad** = "
          "silent).",
          "**Hold pad 8:** pads 9-24 = 16 starter instruments (piano, electric piano, organ, pluck, harp, marimba, bass, bell, strings, "
          "pad, flute, clarinet, brass, kick, snare, hi-hat); press one to load its whole FM.",
          "**Clear + pad 7** = a playable voice of the chosen algorithm; **Clear + knob** = its value in that voice; **Clear + MIDI 1 / "
          "2** = everything to the defaults."],
         ["The loudness comes from the operators (the engine's VCA stays open); SHAPE, envelope → shape and LFO → shape of the OSC 1 page "
          "set the brightness, so the ADSR, the LFO, the matrix and the lanes move the timbre. Velocity and higher notes change it too.",
          "*(since RC4)* In the poly voice mode up to 6 FM voices, shared by MIDI 1 and MIDI 2 (3 each with both in FM poly); *(Beta 5.56 "
          "only)* 6 each, computed apart from the rest of the sound. See [Own-synth voices](#midi-voces).",
          "Saved with the own-synth patches and with the project; no CC / NRPN.",
          "*(Beta 5.56 only)* Replaced by the 8-operator FM: 4-operator patches load into it with the same sound. Detail: [4-operator "
          "FM](#midi-fm)."]),
    es=E("Un sinte FM de 4 operadores como variante del oscilador del sinte propio, con 16 algoritmos (clásicos, percusivos, campanas y "
         "cuerdas) para pianos eléctricos, bajos, campanas, golpes metálicos y percusión. Cada operador tiene una envolvente de ataque / "
         "release con sustain fijo, y 16 sonidos de partida están a un toque.",
         ["En la vista Preset de MIDI 1 / 2, un toque al **pad 27** y elige el **pad 24** de la fila de motores (violeta); el **pad 7** "
          "abre su página de knobs.",
          "**K1-K4** = el ratio de los operadores 1-4 (los clics de más de cada ratio lo desafinan un poco); **K5-K8** = su nivel.",
          "**Shift + K1-K4** = a la derecha el ataque del operador, a la izquierda pasa a ser percusivo con su propio decay; **Shift + "
          "K5** = algoritmo (16); **Shift + K6** feedback; **Shift + K7** ruido; **Shift + K8** release (más largo cuanto más fuerte la "
          "nota).",
          "**Mantén el pad 7:** los pads 9-24 = los 16 algoritmos en el color de su familia; pulsa uno para elegirlo y oírlo (**Shift + "
          "pad** = sin sonar).",
          "**Mantén el pad 8:** los pads 9-24 = 16 instrumentos de partida (piano, piano eléctrico, órgano, pluck, arpa, marimba, bajo, "
          "campana, cuerdas, pad, flauta, clarinete, metales, bombo, caja, hi-hat); pulsa uno para cargar todo su FM.",
          "**Clear + pad 7** = una voz tocable del algoritmo elegido; **Clear + knob** = su valor en esa voz; **Clear + MIDI 1 / 2** = "
          "todo a los valores iniciales."],
         ["El volumen lo dan los operadores (el VCA del motor se queda abierto); SHAPE, envolvente → forma y LFO → forma de la página OSC "
          "1 marcan el brillo, así que la ADSR, el LFO, la matriz y los carriles mueven el timbre. La velocity y las notas agudas también "
          "lo cambian.",
          "*(desde RC4)* Con el modo de voz poly, hasta 6 voces FM repartidas entre MIDI 1 y MIDI 2 (3 cada una con las dos en FM poly); "
          "*(solo Beta 5.56)* 6 cada una, calculadas aparte del resto del sonido. Ver [Voces del sinte propio](#midi-voces).",
          "Se guarda con los patches del sinte propio y con el proyecto; no tiene CC / NRPN.",
          "*(solo Beta 5.56)* Lo sustituye el FM de 8 operadores: los patches de 4 operadores se cargan en él con el mismo sonido. "
          "Detalle: [FM de 4 operadores](#midi-fm)."]))

# C24 8-operator FM (Beta 5.56 only)
EXPLAIN["fm8"] = dict(
    en=E("In the beta the FM engine grows to up to 8 operators, each with a DX7-style envelope (4 rates and 4 levels), and 56 algorithms: "
         "the 4-operator FM's 16, the DX7's 32 and 8 with eight operators. 4-operator patches load with the same sound, DX7 voices can be "
         "imported with the card app, and an algorithm map shows and edits the routing on the pads.",
         ["MIDI 1 / 2 Preset view: tap **pad 27**, pick **pad 24** (violet), close the row with **pad 27** and press **pad 7**: the FM "
          "page.",
          "**Pads 9-16** pick operator 1-8 (the ones the algorithm uses lit: carriers green, modulators light blue); **pad 3** = the pitch "
          "envelope (violet).",
          "With an operator picked: **K1** ratio (0.5 … 31, or fixed 1 / 10 / 100 / 1000 Hz in red), **K2** fine, **K3** output level, "
          "**K4** velocity sensitivity, **K5-K8** rates R1-R4; with **Shift**: K1 algorithm (56), K2 feedback, K3 rate scaling, K4 level "
          "scaling, K5-K8 levels L1-L4.",
          "**Shift + pad 7 held** = the 56 algorithms on pads 9-32, in three pages (**Octave ▼ / ▲**); **pad 8 held** = 24 instruments in "
          "their type's colour (**Octave ▼** = a second page of 24); press one to load it and hear it.",
          "A tap on **pad 7** = the **algorithm map** (held ½ s: only while held): each row reads left (modulator) to right (carrier), a "
          "dark gap = no interaction; the colour tells the ratio (green integer, teal x.5, orange inharmonic, red fixed; violet the "
          "feedback). Tap = pick, **Shift + operator** = silence it while the map shows, **hold one and tap another** = link or unlink "
          "them (an own algorithm)."],
         ["*(Beta 5.56 only)* Only the algorithm's operators take DSP time: about 10 voices with 4 operators, 6-7 with 6, 5 with 8.",
          "Saved with the own-synth patches (an extra slot of the same bank on the card, which grows up to 8 KB) and with the project; "
          "swapping or copying patches between packs takes the FM along. Components' «Send patches» / «Send pack» no longer erase them "
          "(not on the internal pack).",
          "Loading an instrument from the pad 8 list also sets page 4 and Shift + pad 4 to the knobs that suit its family; the values do "
          "not change.",
          "No CC / NRPN. DX7 voices: the card app turns a 32-voice or single-voice .syx into custom patches with this FM ([Card and device "
          "app](#app-sd)). Detail: [8-operator FM](#midi-fm8)."]),
    es=E("En la beta el motor FM pasa a tener hasta 8 operadores, cada uno con una envolvente como la del DX7 (4 rates y 4 niveles), y 56 "
         "algoritmos: los 16 del FM de 4 operadores, los 32 del DX7 y 8 de 8 operadores. Los patches de 4 operadores se cargan con el "
         "mismo sonido, las voces del DX7 se importan con la app de la tarjeta y un mapa del algoritmo enseña y edita el enrutado en los "
         "pads.",
         ["Vista Preset de MIDI 1 / 2: un toque al **pad 27**, elige el **pad 24** (violeta), cierra la fila con el **pad 27** y pulsa el "
          "**pad 7**: la página FM.",
          "Los **pads 9-16** eligen el operador 1-8 (encendidos los que usa el algoritmo: portadores verdes, moduladores azul claro); el "
          "**pad 3** = la envolvente de pitch (violeta).",
          "Con un operador elegido: **K1** ratio (0,5 … 31, o fijo 1 / 10 / 100 / 1000 Hz en rojo), **K2** fino, **K3** nivel de salida, "
          "**K4** sensibilidad a la velocity, **K5-K8** rates R1-R4; con **Shift**: K1 algoritmo (56), K2 feedback, K3 rate scaling, K4 "
          "level scaling, K5-K8 niveles L1-L4.",
          "**Shift + pad 7 mantenido** = los 56 algoritmos en los pads 9-32, en tres páginas (**Octave ▼ / ▲**); **pad 8 mantenido** = 24 "
          "instrumentos en el color de su tipo (**Octave ▼** = una segunda página de 24); pulsa uno para cargarlo y oírlo.",
          "Un toque al **pad 7** = el **mapa del algoritmo** (mantenido ½ s: solo mientras lo mantienes): cada fila se lee de izquierda "
          "(moduladora) a derecha (portadora), un hueco oscuro = no interactúan; el color dice el ratio (verde entero, verde azulado x,5, "
          "naranja inarmónico, rojo fijo; violeta el feedback). Toque = elegir, **Shift + operador** = callarlo mientras ves el mapa, "
          "**mantén uno y toca otro** = enlazarlos o desenlazarlos (un algoritmo propio)."],
         ["*(solo Beta 5.56)* Solo los operadores del algoritmo gastan tiempo del DSP: unas 10 voces con 4 operadores, 6-7 con 6, 5 con 8.",
          "Se guarda con los patches del sinte propio (una ranura extra del mismo banco de la tarjeta, que crece hasta 8 KB) y con el "
          "proyecto; intercambiar o copiar patches entre packs lleva el FM. «Send patches» / «Send pack» de Components ya no los borran "
          "(no en el pack interno).",
          "Cargar un instrumento de la lista del pad 8 también pone la página 4 y Shift + pad 4 en los knobs que convienen a su familia; "
          "los valores no cambian.",
          "No tiene CC / NRPN. Voces del DX7: la app de la tarjeta convierte un .syx de 32 voces o de una en parches custom con este FM "
          "([App de la tarjeta y del aparato](#app-sd)). Detalle: [FM de 8 operadores](#midi-fm8)."]))

# C25 Wavetable (Beta 5.56 only)
EXPLAIN["wavetable"] = dict(
    en=E("A wavetable engine for the own synth: the oscillator reads a table of up to 9 frames per patch and moves through it with a "
         "position knob, an LFO or the envelope, while both oscillators, FM / ring / sync, the filter, the VCA and polyphony work as "
         "usual. Fill the table with the stock synth's 16 wavetables or with single cycles cut from the pack's samples.",
         ["In the MIDI 1 / 2 Preset view tap **pad 27** and pick **pad 21** of the engine row (sand); pad 27 then shows sand.",
          "On the OSC 1 / OSC 2 page, **K3** = the position (the frame); OSC 1's **K7** = LFO → position and **Shift + K3** = envelope → "
          "position; **SHAPE (K4)** = warp, a bend of the phase.",
          "**Hold pad 7:** pads 9-24 = the stock synth's 16 wavetables (sand, the loaded one bright): a tap fills the table with its 9 "
          "frames; **Shift + a table** changes only the frame the position (K3) points at.",
          "**Hold pad 8:** the pack's samples on pads 9-32 (**Octave ▼ / ▲** = page): a tap puts one cycle of that sample into the frame "
          "the position points at (it takes a moment).",
          "**Clear + pad 7** = that frame back to its table's. Every tap on a list sounds the tonic until you let go of the pad."],
         ["*(Beta 5.56 only)* One table per patch, for both oscillators: saved with the own-synth patches and with the project; wavetable "
          "patches show sand in the patch list.",
          "Every frame has 18 band-limited versions, so high notes do not alias; with the warp away from the centre the ends sound a "
          "little duller.",
          "The first time, the table comes filled with the 7th (digital saw-square). On a table change the new frames come in one by one "
          "(a short blend meanwhile).",
          "Detail: [MIDI 1 / 2 Preset view](#midi-preset), [Knob pages of the MIDI 1 / 2 engine](#midi-knobs)."]),
    es=E("Un motor wavetable para el sinte propio: el oscilador lee una tabla de hasta 9 cuadros por patch y la recorre con un knob de "
         "posición, un LFO o la envolvente, mientras los dos osciladores, el FM / ring / sync, el filtro, el VCA y la polifonía funcionan "
         "como siempre. Llena la tabla con las 16 wavetables del sinte de stock o con ciclos sueltos cortados de los samples del pack.",
         ["En la vista Preset de MIDI 1 / 2, un toque al **pad 27** y elige el **pad 21** de la fila de motores (arena); el pad 27 se ve "
          "entonces en arena.",
          "En la página OSC 1 / OSC 2, **K3** = la posición (el cuadro); el **K7** de OSC 1 = LFO → posición y **Shift + K3** = envolvente "
          "→ posición; **SHAPE (K4)** = warp, una doblez de la fase.",
          "**Mantén el pad 7:** los pads 9-24 = las 16 wavetables del sinte de stock (arena, brillante la cargada): un toque llena la "
          "tabla con sus 9 cuadros; **Shift + una tabla** cambia solo el cuadro que señala la posición (K3).",
          "**Mantén el pad 8:** los samples del pack en los pads 9-32 (**Octave ▼ / ▲** = página): un toque pone un ciclo de ese sample en "
          "el cuadro que señala la posición (tarda un momento).",
          "**Clear + pad 7** = ese cuadro vuelve al de su tabla. Cada toque en una lista suena la tónica hasta soltar el pad."],
         ["*(solo Beta 5.56)* Una tabla por patch, para los dos osciladores: se guarda con los patches del sinte propio y con el proyecto; "
          "los patches de wavetable se ven en arena en la lista de patches.",
          "Cada cuadro tiene 18 versiones de banda limitada, así que los agudos no hacen aliasing; con el warp lejos del centro, los "
          "extremos suenan algo más apagados.",
          "La primera vez la tabla viene llena con la 7.ª (digital saw-square). Al cambiar de tabla, los cuadros nuevos entran uno a uno "
          "(un momento de mezcla mientras tanto).",
          "Detalle: [Vista Preset de MIDI 1 / 2](#midi-preset), [Páginas de knobs del motor de MIDI 1 / 2](#midi-knobs)."]))

# C26 Master FX since RC2: mechanical gesture, Glitch, Digitise and saving per session
EXPLAIN["master-fx-beta"] = dict(
    en=E("Since RC2 Master FX has the Glitch on pad 6 and a mechanical gesture on pad 31 (tape stop, scratches, back spin…), Digitise "
         "gains a momentary throw to the delay and an envelope, and the Master FX settings are saved with every project. Each project "
         "keeps its own performance setup.",
         ["**Pad 31 = mechanical gesture:** press it and the audio slows down to a stop; release it and the audio starts again. **K1** = "
          "moves per gesture (1-8), **K2** = the kind, blended continuously and shown in colours (tape stop → baby scratch → tear → back "
          "spin → rattle), **K3** = stop time, **K4** = start time.",
          "**Pad 6 = Glitch:** held, latched (Shift + pad 6), assignable to the slots and to the FX sequencer like the other effects; its "
          "K1-K4 are the Glitch's.",
          "**Digitise (pad 4):** K1 sample rate, K2 bits, **K3** = sends every track to the delay while you hold pad 4 (on release their "
          "sends come back), **K4** = envelope of the amount (to the right it goes from full to clean, to the left it grows).",
          "Save the project (**Save** twice): the 20 knobs of the top row, the slot assignments and the master compressor's attack / "
          "release are stored, and they come back when it loads."],
         ["A project without them (an older or a new one) leaves the device as it is. Latched effects are not saved.",
          "The gesture uses the Glitch's engine: while it plays, the Glitch waits. Pad 31 can be stored on a slot too (hold pad 31 + a "
          "slot).",
          "*(since RC4.02)* Digitise's K4 envelope starts properly (in RC4 and before it never started).",
          "Detail: [Master FX](#master-fx)."]),
    es=E("Desde RC2, Master FX tiene el Glitch en el pad 6 y un gesto mecánico en el pad 31 (parada de cinta, scratches, back spin…), "
         "Digitise gana un envío momentáneo al delay y una envolvente, y los ajustes de Master FX se guardan con cada proyecto. Cada "
         "proyecto conserva su propia preparación para el directo.",
         ["**Pad 31 = gesto mecánico:** al pulsarlo el audio se frena hasta parar; al soltarlo arranca otra vez. **K1** = movimientos por "
          "gesto (1-8), **K2** = el tipo, mezclado de forma continua y en colores (parada de cinta → baby scratch → tear → back spin → "
          "rattle), **K3** = tiempo de parada, **K4** = tiempo de arranque.",
          "**Pad 6 = Glitch:** mantenido, fijado (Shift + pad 6), asignable a los huecos y al secuenciador de efectos como los demás "
          "efectos; sus K1-K4 son los del Glitch.",
          "**Digitise (pad 4):** K1 muestreo, K2 bits, **K3** = manda todas las pistas al delay mientras mantienes el pad 4 (al soltar "
          "vuelven sus envíos), **K4** = envolvente de la cantidad (a la derecha va de entero a limpio, a la izquierda crece).",
          "Guarda el proyecto (**Save** dos veces): los 20 knobs de la fila de arriba, la asignación de los huecos y el ataque / release "
          "del compresor master quedan guardados y vuelven al cargarlo."],
         ["Un proyecto que no los tiene (antiguo o nuevo) deja el aparato como esté. Los efectos fijados no se guardan.",
          "El gesto usa el motor del Glitch: mientras suena, el Glitch espera. El pad 31 también se puede guardar en un hueco (pad 31 "
          "mantenido + un hueco).",
          "*(desde RC4.02)* La envolvente de K4 de Digitise arranca bien (en RC4 y antes no arrancaba).",
          "Detalle: [Master FX](#master-fx)."]))


# ---------------------------------------------------------------------------------------------------- D: DSP
# D1 Master FX effects
EXPLAIN["efectos-master-fx"] = dict(
    en=E("Live effects on the whole master output, on pads 1-6 of Master FX: the **Gater** chops the mix in rhythm, the **Auto-Filter** "
         "sweeps a low-pass or high-pass filter, **Digitise** lowers the sample rate and the bits for a lo-fi crunch, the **Phaser** adds "
         "a moving swirl and the **Glitch** turns the output into a tape head over the last seconds of audio. Hold a pad for a moment of "
         "effect or latch it, and shape each one with four knobs.",
         ["Open Master FX: **Mixer**, then **Mixer** again.",
          "**Hold** an effect pad = on while held; **Shift + pad** = latched, touch it again to release it; **pad 8** releases everything "
          "latched.",
          "Turn **K1-K4** for the effect whose pad you press: pad 1 Gater: division, depth, width, smoothing; pads 2 / 3 Auto-Filter low / "
          "high pass: speed, depth, resonance, centre.",
          "Pad 4 Digitise: sample rate, bits, **K3** = a momentary throw to the delay while you hold the pad, **K4** = an envelope on the "
          "amount; pad 5 Phaser: speed, depth, feedback, mix; pad 6 Glitch: speed, repeat, delay, chaos / overload.",
          "**Clear + knob to the right** = the knob's default (lavender while Clear is held)."],
         ["The knob LEDs show the value with their brightness. Master FX has no automation (no red with Clear).",
          "*(since RC4)* The Auto-Filter's and the Phaser's speed (K1) is bipolar: right free, left synced to the tempo, each cycle "
          "starting on the bar's first beat. *(since RC4.02)* Digitise's K4 envelope works (in RC4 it never started).",
          "*(since RC2)* The effects' 20 knobs and the slot assignments are saved with each project; latched effects are off at power-up.",
          "An effect can also be stored in a slot of the bottom row (hold it + touch a slot) and triggered by the FX sequencer. [Master "
          "FX](#master-fx)"]),
    es=E("Efectos de directo sobre toda la salida master, en los pads 1-6 de Master FX: el **Gater** trocea la mezcla a ritmo, el "
         "**Auto-Filter** barre un filtro paso bajo o paso alto, **Digitise** baja el muestreo y los bits para un sonido lo-fi, el "
         "**Phaser** añade un remolino que se mueve y el **Glitch** convierte la salida en una cabeza de cinta sobre los últimos segundos "
         "de audio. Mantén un pad para un momento de efecto o fíjalo, y moldea cada uno con cuatro knobs.",
         ["Abre Master FX: **Mixer** y **Mixer** otra vez.",
          "**Mantener** un pad de efecto = activo mientras lo mantienes; **Shift + pad** = fijado, tocarlo otra vez lo suelta; el **pad "
          "8** suelta todo lo fijado.",
          "Gira **K1-K4** para el efecto cuyo pad pulsas: pad 1 Gater: división, profundidad, ancho, suavizado; pads 2 / 3 Auto-Filter "
          "paso bajo / alto: velocidad, profundidad, resonancia, centro.",
          "Pad 4 Digitise: muestreo, bits, **K3** = envío momentáneo al delay mientras mantienes el pad, **K4** = envolvente de la "
          "cantidad; pad 5 Phaser: velocidad, profundidad, realimentación, mezcla; pad 6 Glitch: velocidad, repetición, retraso, caos / "
          "sobrecarga.",
          "**Clear + knob a la derecha** = su valor por defecto (en lavanda con Clear pulsado)."],
         ["El brillo de los LEDs de los knobs enseña el valor. Master FX no tiene automatización (no hay rojo con Clear).",
          "*(desde RC4)* La velocidad (K1) del Auto-Filter y del Phaser es bipolar: derecha libre, izquierda a tempo, con cada ciclo "
          "empezando en el primer tiempo del compás. *(desde RC4.02)* La envolvente de K4 de Digitise funciona (en RC4 no arrancaba).",
          "*(desde RC2)* Los 20 knobs de los efectos y la asignación de los huecos se guardan con cada proyecto; los efectos fijados se "
          "apagan al encender.",
          "Un efecto también se puede guardar en un hueco de la fila inferior (mantenlo + toca un hueco) y dispararlo con el secuenciador "
          "de efectos. [Master FX](#master-fx)"]))

# D2 VCA-VCF of the MIDI tracks
EXPLAIN["vca-vcf"] = dict(
    en=E("Every engine of the MIDI 1 / 2 own synth goes through the same shaping section: an amplifier (VCA) with an ADSR envelope and "
         "velocity, a filter (VCF) with seven types and an effect stage with seven types, all moved by the envelope and an LFO. With the "
         "**line input** engine it shapes an outside instrument plugged into the track's audio input, opened by the track's notes.",
         ["Turn the engine on (MIDI 1 / 2 Preset view, **pad 27**) and open page 1, **VCA-VCF** (**pad 1**; *(Beta 5.56 only)* **pad 4**, "
          "Filter / VCA).",
          "**K1** attack · **K2** release · **Shift + K1** sustain · **Shift + K2** decay.",
          "**K3 / K4** envelope → level / → filter · **Shift + K3 / K4** LFO → level / → filter.",
          "**K5** filter · **Shift + K5** filter type: DJ, LP 12, HP 12, band pass, notch, LP 24, HP 24.",
          "**K6** resonance · **Shift + K6** VCA gain, up to +18 dB with soft saturation.",
          "**K7** LFO speed (*(since RC4)* right free, left synced to the tempo); its shape on page 5, **Shift + K8**, shown by the LED's "
          "colour: reverse saw (blue), saw (magenta), triangle (green), square (red), sine (teal), sample & hold (white), slewed sample & "
          "hold (violet).",
          "**K8** effect amount · **Shift + K8** effect type: soft, hard, fold, wavefold, ring, comb, chorus.",
          "**Pad 29** = the chain's order: VCA → effect → filter or filter → VCA → effect."],
         ["The defaults let the input through clean; the filter follows the note (key tracking) and the 24 dB types are two stages in a "
          "row.",
          "Type knobs: colour = the type, brightness = the position inside it. **Clear + the page's pad** *(since RC2)* = the page back to "
          "its initial values.",
          "*(Beta 5.56 only)* The factory order is filter → VCA → effect (pad 29 on = VCA → effect → filter); a project or patch saved "
          "before keeps its pad, so its order swaps.",
          "*(since RC2.02)* With no shape saved, the LFO is a triangle; the LFO also moves pitch, shape and morph from page 2. [Knob pages "
          "of the MIDI 1 / 2 engine](#midi-knobs)"]),
    es=E("Todos los motores del sinte propio de MIDI 1 / 2 pasan por la misma sección: un amplificador (VCA) con envolvente ADSR y "
         "velocity, un filtro (VCF) de siete tipos y una etapa de efecto de siete tipos, movidos por la envolvente y un LFO. Con el motor "
         "**entrada de línea** procesa un instrumento externo conectado a la entrada de audio de la pista, abierto por las notas de la "
         "pista.",
         ["Enciende el motor (vista Preset de MIDI 1 / 2, **pad 27**) y abre la página 1, **VCA-VCF** (**pad 1**; *(solo Beta 5.56)* **pad "
          "4**, Filtro / VCA).",
          "**K1** ataque · **K2** release · **Shift + K1** sustain · **Shift + K2** decay.",
          "**K3 / K4** envolvente → nivel / → filtro · **Shift + K3 / K4** LFO → nivel / → filtro.",
          "**K5** filtro · **Shift + K5** tipo de filtro: DJ, LP 12, HP 12, paso banda, notch, LP 24, HP 24.",
          "**K6** resonancia · **Shift + K6** gain del VCA, hasta +18 dB con saturación suave.",
          "**K7** velocidad del LFO (*(desde RC4)* derecha libre, izquierda a tempo); su forma en la página 5, **Shift + K8**, con el "
          "color del LED: diente de sierra inverso (azul), diente de sierra (magenta), triángulo (verde), cuadrada (rojo), seno (verde "
          "azulado), sample & hold (blanco), sample & hold suavizado (violeta).",
          "**K8** cantidad de efecto · **Shift + K8** tipo de efecto: suave, dura, plegado, wavefold, ring, comb, chorus.",
          "**Pad 29** = orden de la cadena: VCA → efecto → filtro o filtro → VCA → efecto."],
         ["Los valores por defecto dejan pasar la entrada limpia; el filtro sigue la nota y los tipos de 24 dB son dos etapas seguidas.",
          "Knobs de tipo: color = el tipo, brillo = la posición dentro de él. **Clear + el pad de la página** *(desde RC2)* = la página a "
          "sus valores iniciales.",
          "*(solo Beta 5.56)* El orden de fábrica es filtro → VCA → efecto (pad 29 encendido = VCA → efecto → filtro); un proyecto o patch "
          "guardado antes conserva el pad, así que su orden se invierte.",
          "*(desde RC2.02)* Sin forma guardada, el LFO es un triángulo; el LFO también mueve tono, forma y morph desde la página 2. "
          "[Páginas de knobs del motor de MIDI 1 / 2](#midi-knobs)"]))

# D3 Oscillators and paraphony
EXPLAIN["osciladores"] = dict(
    en=E("The oscillator engine of the MIDI 1 / 2 own synth: one waveform that morphs smoothly from sine to triangle, saw and square, a "
         "SHAPE control that folds, bends or narrows it (and *(since RC4)* turns the saw into a seven-saw supersaw), and an optional "
         "second oscillator that modulates the first with FM, ring, sync or bitwise modes. With two oscillators, two notes at once go one "
         "to each oscillator (paraphony).",
         ["MIDI 1 / 2 Preset view: tap **pad 27** and pick the **oscillator** (green) on the engine row; page 2 (**pad 2**) = OSC 1.",
          "**K7 WAVE** = the morph: 0 sine, 42 triangle, 84 saw, 126 square (*(Beta 5.56 only)* K3). **K1 TUNE**, **Shift + K1** FINE.",
          "**K2 SHAPE** (*(Beta 5.56 only)* K4): on the sine and the triangle, right of the centre = **wavefold** (more harmonics); on the "
          "triangle, left = exponential ramps *(since RC4)*; on the saw, from a plain saw fully left to a 7-saw **supersaw** fully right "
          "*(since RC4)*; on the square, the pulse width, 3 % to 97 %.",
          "Envelope and LFO move pitch, shape and morph: **K3** env → pitch, **K4** env → shape, **K5** LFO → pitch, **K6** LFO → shape, "
          "**K8** LFO → morph, **Shift + K8** env → morph.",
          "**Pad 28** = two oscillators; page 3 (**pad 3**) = OSC 2: K1 TUNE 2, K2 SHAPE 2, K3 MIX, K4 FM, K5 FINE 2, K6 BITSYNC, K7 WAVE "
          "2, K8 RING.",
          "**FM** = OSC 2 modulates OSC 1's phase; **BITSYNC** walks a soft sync (every N cycles) and the bitwise modes xor, or, nor, and, "
          "nand.",
          "In the mono voice modes (retrigger, legato, glide): one note = both oscillators on it; two notes = one each (paraphony)."],
         ["*(since RC4)* Less aliasing: the saw, the supersaw and the pulse are made with PolyBLEP (about 40 dB fewer tones foreign to the "
          "note on high notes), and the wavefold limits its gain on high notes.",
          "*(since RC2)* With one oscillator the last note has priority; releasing it brings the previous one back. *(since RC4)* The "
          "oscillator also plays in poly (up to 4 voices; the mode of a project that never chose another) and in the unison modes: voice "
          "mode, pad 32.",
          "*(Beta 5.56 only)* Page 2 is rearranged (K1 TUNE, K2 FINE, K3 WAVE, K4 SHAPE; K5 / K6 / K8 = LFO / envelope → FM, ring, mix); "
          "page 3 gives K1 = OSC 2's ratio (¼ … 31), K2 detune, K5 FM with a centre (right OSC 2 → OSC 1, left the other way), K7 classic "
          "sync + bitwise; with one oscillator, a sub-oscillator and noise; a 4-sample BLEP.",
          "[Knob pages of the MIDI 1 / 2 engine](#midi-knobs)"]),
    es=E("El motor oscilador del sinte propio de MIDI 1 / 2: una forma de onda que pasa sin saltos del seno al triángulo, la sierra y la "
         "cuadrada, un control SHAPE que la pliega, la curva o la estrecha (y *(desde RC4)* convierte la sierra en una supersaw de siete "
         "sierras), y un segundo oscilador opcional que modula al primero con FM, ring, sync o modos bit a bit. Con dos osciladores, dos "
         "notas a la vez van una a cada oscilador (parafonía).",
         ["Vista Preset de MIDI 1 / 2: toca el **pad 27** y elige el **oscilador** (verde) en la fila de motores; la página 2 (**pad 2**) "
          "= OSC 1.",
          "**K7 WAVE** = el morph: 0 seno, 42 triángulo, 84 sierra, 126 cuadrada (*(solo Beta 5.56)* K3). **K1 TUNE**, **Shift + K1** FINE.",
          "**K2 SHAPE** (*(solo Beta 5.56)* K4): en el seno y el triángulo, a la derecha del centro = **wavefold** (más armónicos); en el "
          "triángulo, a la izquierda = rampas exponenciales *(desde RC4)*; en la sierra, de una sierra normal a la izquierda del todo a "
          "una **supersaw** de 7 sierras a la derecha del todo *(desde RC4)*; en la cuadrada, el ancho del pulso, del 3 % al 97 %.",
          "La envolvente y el LFO mueven tono, forma y morph: **K3** env → tono, **K4** env → forma, **K5** LFO → tono, **K6** LFO → "
          "forma, **K8** LFO → morph, **Shift + K8** env → morph.",
          "**Pad 28** = dos osciladores; página 3 (**pad 3**) = OSC 2: K1 TUNE 2, K2 SHAPE 2, K3 MIX, K4 FM, K5 FINE 2, K6 BITSYNC, K7 "
          "WAVE 2, K8 RING.",
          "**FM** = OSC 2 modula la fase de OSC 1; **BITSYNC** recorre un sync suave (cada N ciclos) y los modos bit a bit xor, or, nor, "
          "and, nand.",
          "En los modos de voz mono (retrigger, legato, glide): una nota = los dos osciladores en ella; dos notas = una en cada uno "
          "(parafonía)."],
         ["*(desde RC4)* Menos aliasing: la sierra, la supersaw y el pulso se generan con PolyBLEP (unos 40 dB menos de tonos ajenos a la "
          "nota en las notas agudas), y el wavefold limita su amplificación en las notas agudas.",
          "*(desde RC2)* Con un oscilador la última nota manda; al soltarla vuelve la anterior. *(desde RC4)* El oscilador también toca en "
          "poly (hasta 4 voces; el modo de un proyecto que nunca eligió otro) y en los modos unísono: modo de voz, pad 32.",
          "*(solo Beta 5.56)* La página 2 cambia (K1 TUNE, K2 FINE, K3 WAVE, K4 SHAPE; K5 / K6 / K8 = LFO / envolvente → FM, ring, mix); "
          "la página 3 da K1 = ratio de OSC 2 (¼ … 31), K2 detune, K5 FM con centro (derecha OSC 2 → OSC 1, izquierda al revés), K7 sync "
          "clásico + bitwise; con un oscilador, sub-oscilador y ruido; BLEP de 4 muestras.",
          "[Páginas de knobs del motor de MIDI 1 / 2](#midi-knobs)"]))

# D4 VA-drum engine
EXPLAIN["va-drum"] = dict(
    en=E("A variant of the oscillator made for synthetic percussion (kicks, toms, snares, blips): every note fires a one-shot hit with its "
         "own decaying pitch and filter envelopes and a dose of white noise, instead of a held sound. The page-1 knobs keep their places, "
         "but some take a percussive job.",
         ["MIDI 1 / 2 Preset view: tap **pad 27** and pick **VA-drum** (orange) on the engine row.",
          "On the VCA-VCF page (pad 1; *(Beta 5.56 only)* pad 4): **Attack** (K1) and **Decay** (Shift + K2) = the one-shot VCA's attack "
          "and decay; **Sustain** (Shift + K1) = the decay of the **pitch** envelope; **Release** (K2) = the decay of the **filter** "
          "envelope.",
          "**LFO speed** (K7) = the **white noise** level; each **LFO → …** knob sends a random value to its destination instead of the "
          "LFO.",
          "Shape the tone on page 2 as on the oscillator (WAVE, SHAPE, env → pitch for the drop) and with **pad 28** for two oscillators.",
          "**Pad 31** on = velocity also sets the level of the pitch and filter envelopes."],
         ["*Kick:* sine, Decay about 70, Sustain about 30, Env → pitch to the right. *Snare:* more noise, a short Decay, band pass.",
          "*(since RC4)* In poly every hit has its own pitch and level envelopes and its own noise: a new hit does not restart the earlier "
          "ones, and letting go of the note does not cut the hit (the filter is still the track's).",
          "With the VA-drum the LFO stays its noise: page 5's LFO shape does not change it.",
          "[MIDI 1 / 2 Preset view](#midi-preset)"]),
    es=E("Una variante del oscilador pensada para percusión sintética (bombos, toms, cajas, blips): cada nota dispara un golpe de un solo "
         "disparo con sus propias envolventes de tono y de filtro que caen y una dosis de ruido blanco, en lugar de un sonido sostenido. "
         "Los knobs de la página 1 siguen en su sitio, pero algunos pasan a tener una función percusiva.",
         ["Vista Preset de MIDI 1 / 2: toca el **pad 27** y elige **VA-drum** (naranja) en la fila de motores.",
          "En la página VCA-VCF (pad 1; *(solo Beta 5.56)* pad 4): **Ataque** (K1) y **Decay** (Shift + K2) = ataque y decay del VCA de un "
          "disparo; **Sustain** (Shift + K1) = el decay de la envolvente de **tono**; **Release** (K2) = el decay de la envolvente de "
          "**filtro**.",
          "**Velocidad del LFO** (K7) = el nivel de **ruido blanco**; cada knob **LFO → …** manda un valor aleatorio a su destino en lugar "
          "del LFO.",
          "Da forma al timbre en la página 2 como en el oscilador (WAVE, SHAPE, env → tono para la caída) y con el **pad 28** para dos "
          "osciladores.",
          "**Pad 31** encendido = la velocity también fija el nivel de las envolventes de tono y de filtro."],
         ["*Bombo:* seno, Decay unos 70, Sustain unos 30, Env → tono a la derecha. *Caja:* más ruido, Decay corto, paso banda.",
          "*(desde RC4)* En poly cada golpe lleva su propia envolvente de tono y de volumen y su ruido: un golpe nuevo no reinicia los "
          "anteriores, y soltar la nota no corta el golpe (el filtro sigue siendo el de la pista).",
          "Con el VA-drum el LFO sigue siendo su ruido: la forma del LFO de la página 5 no lo cambia.",
          "[Vista Preset de MIDI 1 / 2](#midi-preset)"]))

# D5 Granular synth
EXPLAIN["granular"] = dict(
    en=E("An engine that plays a sample as a cloud of up to 16 short overlapping grains per track: you choose where they read, how long "
         "and how dense they are, and whether the reading moves forward, freezes or runs backwards. It turns a drum's sample or the Master "
         "FX capture into pads, textures, frozen drones, time-stretched loops or sliced beats, played from the track's notes.",
         ["MIDI 1 / 2 Preset view: tap **pad 27** and pick **granular** (magenta); **pad 2** = its page.",
          "**Shift + K8** = the source: the capture (red) or the sample that Drum 1, 2, 3 or 4 has now (orange, yellow, violet, teal).",
          "**K2** position in the sample · **K3** scan: centre frozen, right forward, left backwards · **K6** length of the scan zone.",
          "**K4** grain size, 5-500 ms · **K5** density, 1-16 grains · **K1** pitch ±24 semitones (**Shift + K1** fine ±1).",
          "**K7** LFO → position · **K8** envelope → position · **Shift + K7** LFO → size.",
          "**Shift + K2** position spray · **Shift + K3** *(since RC4)* left = chance of reversed grains, right = pitch spray · **Shift + "
          "K4** *(since RC4)* stereo spread · **Shift + K5** window: rectangular → triangular → percussive.",
          "**Shift + K6** = what the notes do: **pitch** (they change the grains' pitch), **slicer** (16 slices, note 36 plays the first) "
          "or **stretch** *(since RC2)*."],
         ["**Stretch:** the stretch from the position (K2) to the end lasts **K3** steps (1-64) at any tempo without changing the pitch, "
          "starting in step with the transport; stopped, it stands still; K7 / K8 do little here.",
          "**Stereo** *(since RC4)*: each grain goes to one side at random and the track's pan (Mixer) sets the proportion; the stereo "
          "part follows the track's VCA, level, pan, mute and side-chain.",
          "It goes through the VCA-VCF of page 1 and plays one voice. It shares its saved values (and their CCs) with the oscillator page.",
          "The source stays fixed even if the drum later changes sample; dim white = no drum has that sample any more. [Knob pages of the "
          "MIDI 1 / 2 engine](#midi-knobs)"]),
    es=E("Un motor que toca un sample como una nube de hasta 16 granos cortos y solapados por pista: eliges dónde leen, cuánto duran y "
         "cuántos hay, y si la lectura avanza, se congela o va hacia atrás. Convierte el sample de un drum o la captura de Master FX en "
         "pads, texturas, drones congelados, bucles estirados o ritmos troceados, tocados con las notas de la pista.",
         ["Vista Preset de MIDI 1 / 2: toca el **pad 27** y elige **granular** (magenta); el **pad 2** = su página.",
          "**Shift + K8** = la fuente: la captura (rojo) o el sample que tiene ahora Drum 1, 2, 3 o 4 (naranja, amarillo, violeta, verde "
          "azulado).",
          "**K2** posición en el sample · **K3** scan: centro congelado, derecha avanza, izquierda retrocede · **K6** longitud de la zona "
          "del scan.",
          "**K4** tamaño del grano, 5-500 ms · **K5** densidad, 1-16 granos · **K1** tono ±24 semitonos (**Shift + K1** fino ±1).",
          "**K7** LFO → posición · **K8** envolvente → posición · **Shift + K7** LFO → tamaño.",
          "**Shift + K2** dispersión de la posición · **Shift + K3** *(desde RC4)* izquierda = probabilidad de granos al revés, derecha = "
          "dispersión del tono · **Shift + K4** *(desde RC4)* dispersión estéreo · **Shift + K5** ventana: rectangular → triangular → "
          "percusiva.",
          "**Shift + K6** = qué hacen las notas: **tono** (cambian la altura de los granos), **slicer** (16 trozos, la nota 36 toca el "
          "primero) o **stretch** *(desde RC2)*."],
         ["**Stretch:** el tramo desde la posición (K2) hasta el final dura **K3** pasos (1-64) a cualquier tempo sin cambiar la altura, "
          "alineado con el inicio del transporte; parado, se queda quieto; K7 / K8 casi no actúan.",
          "**Estéreo** *(desde RC4)*: cada grano sale a un lado al azar y el panorama de la pista (Mixer) decide la proporción; la parte "
          "estéreo sigue el VCA, el nivel, el panorama, el mute y el sidechain de la pista.",
          "Pasa por el VCA-VCF de la página 1 y toca una sola voz. Comparte sus valores guardados (y sus CC) con la página del oscilador.",
          "La fuente queda fijada aunque el drum cambie después de sample; blanco tenue = ningún drum tiene ya ese sample. [Páginas de "
          "knobs del motor de MIDI 1 / 2](#midi-knobs)"]))

# D6 Glitch engine
EXPLAIN["glitch-dsp"] = dict(
    en=E("How the Glitch (Master FX pad 6) works: the mod records the last 2.7 seconds of the master all the time, and pressing the Glitch "
         "replaces the output with a tape head playing that recording: faster, slower, stopped, backwards, stuttering or jumping around. "
         "Tape stops, stutters, rewinds and controlled chaos for the end of a phrase.",
         ["In Master FX **hold pad 6** (**Shift + pad 6** = latched): the head starts a little in the past, now minus the delay (K3), with "
          "a short fade-in.",
          "**K1** speed: at the top normal, in the middle stopped, at the bottom backwards; near 0 = a tape stop.",
          "**K2** repeat: at the end of each segment the head goes back to its start; at the maximum, a continuous delay without fades.",
          "**K3** delay: how far back the head starts, up to 2.6 s.",
          "**K4** lower half = **chaos** (random jumps back, silences and reversals); upper half = **overload**."],
         ["**Overload** imitates an overloaded machine: with a chance that grows with K4, short blocks of sound arrive late (the head "
          "jumps back and catches up), and from K4 ≈ 96 the head also slows down to 0.43 ×. It is a simulation: the sequencer, the MIDI "
          "clock and the rest of the audio are not affected.",
          "The mechanical gesture (pad 31) uses the same engine: while it plays, the Glitch waits.",
          "The Glitch can go into a bottom-row slot (hold pad 6 + touch a slot); *(since RC2)* its knobs are saved with the project; over "
          "MIDI it is NRPN 9:16-19 on channel 16.",
          "[Master FX](#master-fx)"]),
    es=E("Cómo funciona el Glitch (pad 6 de Master FX): el mod graba sin parar los últimos 2,7 segundos del master, y al pulsar el Glitch "
         "la salida pasa a una cabeza de cinta que toca esa grabación: más rápido, más lento, parada, hacia atrás, repitiendo o saltando. "
         "Frenadas de cinta, tartamudeos, rebobinados y caos controlado para el final de una frase.",
         ["En Master FX **mantén el pad 6** (**Shift + pad 6** = fijado): la cabeza empieza un poco en el pasado, ahora menos el retraso "
          "(K3), con una entrada gradual corta.",
          "**K1** velocidad: arriba normal, en el centro parada, abajo hacia atrás; cerca de 0 = frenada de cinta.",
          "**K2** repetición: al acabar cada segmento la cabeza vuelve a su inicio; al máximo, retraso continuo sin fundidos.",
          "**K3** retraso: cuánto atrás empieza la cabeza, hasta 2,6 s.",
          "**K4** mitad de abajo = **caos** (saltos atrás al azar, silencios y cambios de sentido); mitad de arriba = **sobrecarga**."],
         ["La **sobrecarga** imita una máquina sobrecargada: con una probabilidad que sube con K4, bloques cortos de sonido llegan tarde "
          "(la cabeza vuelve atrás y luego recupera), y desde K4 ≈ 96 la cabeza además frena hasta 0,43 ×. Es una simulación: el "
          "secuenciador, el reloj MIDI y el resto del audio no se ven afectados.",
          "El gesto mecánico (pad 31) usa el mismo motor: mientras suena, el Glitch espera.",
          "El Glitch se puede poner en un hueco de la fila inferior (mantén el pad 6 + toca un hueco); *(desde RC2)* sus knobs se guardan "
          "con el proyecto; por MIDI es el NRPN 9:16-19 por el canal 16.",
          "[Master FX](#master-fx)"]))

# D7 Drum DSP
EXPLAIN["drums-dsp"] = dict(
    en=E("The sound processing behind each drum's new knobs: every drum gets its own filter with several modes, a ring modulator with its "
         "own oscillator, a tremolo / vibrato LFO, pitch and filter envelopes, sample start, cut and attack, bitcrush and distortion "
         "types. Drums can also duck each other through the side-chain, and *(since RC2)* so can a note track's pattern.",
         ["Shape each drum with its knobs (**Drum 1-4**; see «Drum knobs as printed on the panel»): **Shift + K5** filter mode, **K2 / "
          "Shift + K2** ring mod, **K7 / Shift + K7** LFO, **K8 / Shift + K8** distortion, bitcrush and type.",
          "**Side-chain between drums:** **Shift + FX**, then **Octave ▼**: on the drum pages, rows 3-4 = the ducking of each drum, row 1 "
          "pads 5-8 = which drum triggers it.",
          "*(since RC2)* On a drum page, **row 1 pads 1-4** = Synth 1, Synth 2, MIDI 1, MIDI 2 as the trigger: every note of their pattern "
          "opens the drum's ducking (notes played live do not).",
          "*(since RC2)* **K1-K4** on a drum page = attack, hold, decay and depth of that drum's side-chain, in the drum's colour."],
         ["Filter modes: the stock EQ tilt (the default), band pass, notch, comb with feedback (not in Beta 5.56) and DJ. Distortion "
          "types: stock, soft, hard, fold; left of 0 on K8 = bitcrush.",
          "With every knob neutral the drum sounds as on the original.",
          "The drum pages' triggers (another drum or a pattern) are not saved: at power-up they are those of the drum's preset. The drum "
          "pages' K1-K4 are saved with the project.",
          "[Drum track view](#drum-pista) · [Sidechain view](#sidechain)"]),
    es=E("El proceso de sonido que hay detrás de los knobs nuevos de cada drum: cada drum tiene su propio filtro con varios modos, un ring "
         "mod con oscilador propio, un LFO de trémolo / vibrato, envolventes de tono y de filtro, inicio, corte y ataque del sample, "
         "bitcrush y tipos de distorsión. Además, un drum puede agachar a otro con el sidechain y, *(desde RC2)*, también el patrón de una "
         "pista de notas.",
         ["Moldea cada drum con sus knobs (**Drum 1-4**; ver «Knobs de los drums según el panel»): **Shift + K5** modo de filtro, **K2 / "
          "Shift + K2** ring mod, **K7 / Shift + K7** LFO, **K8 / Shift + K8** distorsión, bitcrush y tipo.",
          "**Sidechain entre drums:** **Shift + FX** y luego **Octave ▼**: en las páginas de drums, las filas 3-4 = el ducking de cada "
          "drum, los pads 5-8 de la fila 1 = qué drum lo dispara.",
          "*(desde RC2)* En una página de drums, los **pads 1-4 de la fila 1** = Synth 1, Synth 2, MIDI 1, MIDI 2 como disparo: cada nota "
          "de su patrón abre el ducking del drum (las notas tocadas en directo no).",
          "*(desde RC2)* **K1-K4** en una página de drums = ataque, hold, decay y profundidad del sidechain de ese drum, en el color del "
          "drum."],
         ["Modos de filtro: el EQ tilt de stock (de fábrica), paso banda, notch, comb con realimentación (no en la Beta 5.56) y DJ. Tipos "
          "de distorsión: stock, suave, dura, plegada; a la izquierda de 0 en K8 = bitcrush.",
          "Con todos los knobs en neutro, el drum suena como en el original.",
          "Los disparos de las páginas de drums (otro drum o un patrón) no se guardan: al encender son los del preset del drum. K1-K4 de "
          "las páginas de drums se guardan con el proyecto.",
          "[Vista de pista de un drum](#drum-pista) · [Vista Sidechain](#sidechain)"]))

# D8 Audio inputs and returns
EXPLAIN["entradas"] = dict(
    en=E("Two ways to bring outside or effect audio into the mod's sound. Synth 1 / 2 can take audio input 1 or 2 (normal or "
         "phase-inverted) in place of their noise, so the patch's filter, envelopes and effects shape your outside signal in time with the "
         "notes. And the reverb and delay returns can go through mixer strips 3 / 4, where the track processes them and its sends can feed "
         "them back into the effects.",
         ["**Synth source:** with Synth 1 / 2's view on screen, press its button again (*(since RC4)* or **Shift + Synth 1 / 2**); **pads "
          "25-29** = noise (normal), input 1, input 2, input 1 inverted, input 2 inverted.",
          "Give the patch some **noise level** (CC 56): the input replaces the noise, so with no noise nothing is heard.",
          "**Returns:** in Setup, **pad 22** = the reverb return through mixer strip 3 (cream), **pad 23** = the delay return through "
          "strip 4 (peach); dim = off.",
          "With a return on strip 3 / 4, that strip's reverb / delay sends (FX view) send the return again, already processed by the "
          "track's VCF / FX: a feedback loop."],
         ["With the returns on strips 3 / 4, those strips' sends are capped at half; and the return is what reaches a synth whose source "
          "is that input.",
          "The MIDI tracks' **line input** engine (pad 27, amber) runs the track's audio input (line 1 on MIDI 1, line 2 on MIDI 2) "
          "through the VCA-VCF, opened by the track's notes.",
          "The synths' noise source is saved with the project. *(Beta 5.56 only)* Advanced Setup **K3** raises the external inputs' gain "
          "up to +24 dB (also what reaches the own synth and the granular).",
          "[Synth source view](#synth-fuente) · [Setup view](#setup)"]),
    es=E("Dos formas de meter audio externo o de los efectos en el sonido del mod. Synth 1 / 2 pueden usar la entrada de audio 1 o 2 "
         "(normal o con la fase invertida) en lugar de su ruido, y así el filtro, las envolventes y los efectos del patch procesan tu "
         "señal externa al ritmo de las notas. Y los retornos de reverb y delay pueden pasar por las tiras 3 / 4 del mixer, donde la pista "
         "los procesa y sus envíos pueden devolverlos a los efectos.",
         ["**Fuente del sinte:** con la vista de Synth 1 / 2 en pantalla, pulsa su botón otra vez (*(desde RC4)* o **Shift + Synth 1 / "
          "2**); **pads 25-29** = ruido (normal), entrada 1, entrada 2, entrada 1 invertida, entrada 2 invertida.",
          "Da al patch algo de **nivel de ruido** (CC 56): la entrada sustituye al ruido, así que sin ruido no se oye nada.",
          "**Retornos:** en Setup, **pad 22** = el retorno de reverb por la tira 3 del mixer (crema), **pad 23** = el de delay por la tira "
          "4 (melocotón); tenue = apagado.",
          "Con un retorno en la tira 3 / 4, los envíos de reverb / delay de esa tira (vista FX) vuelven a mandar el retorno, ya procesado "
          "por el VCF / FX de la pista: un bucle de realimentación."],
         ["Con los retornos en las tiras 3 / 4, los envíos de esas tiras tienen tope a la mitad; y el retorno es lo que llega a un sinte "
          "cuya fuente es esa entrada.",
          "El motor **entrada de línea** de las pistas MIDI (pad 27, ámbar) pasa la entrada de audio de la pista (línea 1 en MIDI 1, línea "
          "2 en MIDI 2) por el VCA-VCF, abierto por las notas de la pista.",
          "La fuente del ruido de los sintes se guarda con el proyecto. *(solo Beta 5.56)* **K3** de Advanced Setup sube la ganancia de "
          "las entradas externas hasta +24 dB (también lo que llega al sinte propio y al granular).",
          "[Vista de la fuente del sinte](#synth-fuente) · [Vista Setup](#setup)"]))


# ---------------------------------------------------------------------------------------------------- E: Miscellaneous
# E1 What is saved and where
EXPLAIN["guardado"] = dict(
    en=E("The mod keeps its data in five places: the **pattern** and the **project** (both reach the card when you save the project), the "
         "**pack** (written to the card at once, when you do the gesture), the **device settings** (on their own, the same for every "
         "project) and nowhere (lost at power-off). Knowing which is which tells you what to save before switching off and what follows "
         "you to another project.",
         ["To make a knob change part of a pattern, record it: **Record** with the sequencer running, or hold a step and turn. A knob "
          "turned without Record changes the project's sound, not the pattern.",
          "Save the project: **Save twice** (white flash, then fast green); for another slot, **Save + the slot's pad** in the Projects "
          "view. Everything marked «project» or «pattern» only reaches the card this way.",
          "To keep a sound for other projects or packs, save it as a patch: Synth 1 / 2 in their Preset view, the MIDI 1 / 2 own synth in "
          "its Preset view (**Clear + pad** twice) *(writes to the card)*.",
          "Before switching off, stop the sequencer, wait **2 s** without touching the MIDI 1 / 2 engine and switch off with the power "
          "button.",
          "If Save never lights, **Save Lock** is on (Shift + Save at power-up, an original feature): repeat the gesture to remove it.",
          "*(since RC4.05)* With the **delayed save** on (Advanced Setup, pad 22), Save while playing stays pending (Save blinks yellow) "
          "and is written when you stop; stop the transport before switching off."],
         ["**Pattern:** notes and automation (own-synth lanes, step-drummer pairs, automation-release marks), sample flips, random-mutate, "
          "frequency, dynamics, play orders and chain rules. **Project:** the drums' new knobs, the synths' noise source, Master FX "
          "(knobs, slots, compressor), side-chain sources, chains and scene repeats, count-in, arpeggiators, custom scale, stereo drum "
          "pairs and *(since RC4)* the whole own synth.",
          "**Pack (card):** saved Synth 1 / 2 patches, own-synth patches, samples and captures, copied projects. **Device settings:** the "
          "MIDI 1 / 2 engine and patch flip, Thru mode, Program Change channels, cue mode, GM drums, USB merge, keyboard to the "
          "arpeggiator, velocity curve, delayed save.",
          "**Lost at power-off:** latched effects and the song pointer, Setup's Record, latched notes and chords, the chord screen, the "
          "split keyboard and open views, the master filter and its off switch, an unused capture.",
          "Without a card (the internal pack) and in the «S» builds the mod writes nothing of its own: patches, samples and copies are not "
          "saved (Save turns red); projects are. [What comes back after a restart and where it is saved](#guardado)"]),
    es=E("El mod guarda sus datos en cinco sitios: el **patrón** y el **proyecto** (los dos llegan a la tarjeta al guardar el proyecto), "
         "el **pack** (se escribe en la tarjeta al momento, al hacer el gesto), los **ajustes del aparato** (solos, iguales para todos los "
         "proyectos) y ninguno (se pierde al apagar). Saber qué va en cada sitio te dice qué guardar antes de apagar y qué te acompaña a "
         "otro proyecto.",
         ["Para que el cambio de un knob forme parte de un patrón, grábalo: **Record** con el secuenciador en marcha, o mantén un paso y "
          "gira. Un knob girado sin Record cambia el sonido del proyecto, no el patrón.",
          "Guarda el proyecto: **Save dos veces** (el primer toque parpadea en blanco; el segundo, verde rápido); para otro hueco, **Save "
          "+ el pad del hueco** en la vista Projects. Todo lo marcado «proyecto» o «patrón» solo llega a la tarjeta así.",
          "Para conservar un sonido en otros proyectos o packs, guárdalo como patch: Synth 1 / 2 en su vista Preset, el sinte propio de "
          "MIDI 1 / 2 en la suya (**Clear + pad** dos veces) *(escribe en la tarjeta)*.",
          "Antes de apagar, para el secuenciador, espera **2 s** sin tocar el motor de MIDI 1 / 2 y apaga con el botón de encendido.",
          "Si Save no se enciende nunca, está activado el **Save Lock** (Shift + Save al encender, función del original): repite el gesto "
          "para quitarlo.",
          "*(desde RC4.05)* Con el **guardado diferido** encendido (Advanced Setup, pad 22), Save mientras suena queda pendiente (Save "
          "parpadea en amarillo) y se escribe al parar; para el transporte antes de apagar."],
         ["**Patrón:** notas y automatización (carriles del sinte propio, pares del step-drummer, marcas de soltar la automatización), "
          "sample flips, random-mutate, frecuencia, dinámicas, órdenes de reproducción y reglas de cadena. **Proyecto:** los knobs nuevos "
          "de los drums, la fuente del ruido de los sintes, Master FX (knobs, huecos, compresor), las fuentes del sidechain, cadenas y "
          "repeticiones de escena, cuenta atrás, arpegiadores, escala propia, parejas estéreo de drums y *(desde RC4)* el sinte propio "
          "entero.",
          "**Pack (tarjeta):** los patches de Synth 1 / 2 guardados, los patches del sinte propio, los samples y las capturas, los "
          "proyectos copiados. **Ajustes del aparato:** el motor de MIDI 1 / 2 y el patch flip, modo Thru, canales de Program Change, modo "
          "cue, drums GM, fusión USB, teclado al arpegiador, curva de velocity, guardado diferido.",
          "**Se pierde al apagar:** los efectos fijados y el song pointer, el Record de Setup, las notas y acordes en latch, la pantalla "
          "de acordes, el teclado partido y las vistas abiertas, el filtro master y su apagado, una captura sin usar.",
          "Sin tarjeta (el pack interno) y con las versiones «S» el mod no escribe nada propio: patches, samples y copias no se guardan "
          "(Save se pone rojo); los proyectos, sí. [Qué vuelve tras reiniciar y dónde se guarda](#guardado)"]))

# E2 The internal memory pack: read only
EXPLAIN["pack-interno"] = dict(
    en=E("The pack in the Circuit's internal memory (the first one in the Packs view) is protected: nothing of the mod writes to it or "
         "deletes it. You can still play it, load from it and copy things out of it to a pack on the microSD card, so a mod gesture made "
         "by mistake cannot spoil it.",
         ["Load and play the internal pack as always.",
          "To take something out of it: in the internal pack, **Duplicate + pad A** (a sample, a patch or a project, in its view), load a "
          "pack on the card, then **Duplicate + pad B** *(writes to the card)*.",
          "Anything the mod would write into it is refused: the **Save** LED turns red for 1.5 s and nothing changes."],
         ["Refused: saving the captured sample with the project, swapping or copying samples and patches into it, saving Synth 1 / 2 or "
          "own-synth patches in it, copying projects into it and deleting it from the Packs view.",
          "The device's own saves still work there (Save of a project), and what the mod keeps inside a project goes with that normal "
          "save. Even so, with the builds that do not end in «S», do not use the internal memory for projects: the installer asks for that.",
          "The «S» builds write nothing of their own to any memory.",
          "[Packs view](#packs)"]),
    es=E("El pack de la memoria interna del Circuit (el primero de la vista de packs) está protegido: nada del mod escribe en él ni lo "
         "borra. Se puede tocar, cargar y copiar desde él a un pack de la microSD, así que un gesto del mod hecho por error no puede "
         "estropearlo.",
         ["Carga y toca el pack interno como siempre.",
          "Para sacar algo de él: en el pack interno, **Duplicate + pad A** (un sample, un patch o un proyecto, en su vista), carga un "
          "pack de la tarjeta y luego **Duplicate + pad B** *(escribe en la tarjeta)*.",
          "Todo lo que el mod escribiría en él se rechaza: el LED de **Save** se pone rojo 1,5 s y no cambia nada."],
         ["Se rechaza: guardar el sample capturado con el proyecto, intercambiar o copiar samples y patches hacia él, guardar en él "
          "patches de Synth 1 / 2 o del sinte propio, copiar proyectos a él y borrarlo desde la vista de packs.",
          "Los guardados del propio aparato siguen funcionando ahí (Save de un proyecto), y lo que el mod guarda dentro del proyecto va en "
          "ese guardado normal. Aun así, con las versiones que no acaban en «S», no uses la memoria interna para proyectos: es lo que pide "
          "el instalador.",
          "Las versiones «S» no escriben nada por su cuenta en ninguna memoria.",
          "[Vista de packs](#packs)"]))

# E3 Installing and going back
EXPLAIN["instalar"] = dict(
    en=E("The mod is installed from a web page: the installer takes Novation's official Circuit Tracks firmware 1.2.1, applies the mod's "
         "changes in the browser and sends the result to the device over USB (Web MIDI). Novation's bootloader is never touched, so you "
         "can always go back to the official firmware.",
         ["**Back up the microSD card first.** With the builds that do not end in «S», do not use the internal memory for projects.",
          "Download Novation's official firmware 1.2.1 for the Circuit Tracks (the installer only accepts that one).",
          "Download the installer, [`rc_uploader.zip`](https://ghillermo.github.io/CIRCUIT-HACKS-RC/rc_uploader.zip), unzip it, open "
          "`rc_uploader.html` in Chrome or Edge and connect the Circuit Tracks over USB.",
          "Pick the official file and the version: the release candidate (RC), its safer «S» twin, a beta, or «Official» to go back. "
          "**Check for new builds** adds published versions your copy does not carry (it needs the internet).",
          "Send.",
          "**Going back:** send another version or the official firmware. If the device does not start, hold **Scales + Preset + Note** "
          "while you power it on (the bootloader's recovery mode) and send again."],
         ["The **«S»** build is the RC with everything the mod would write or delete on the card or in the internal memory refused (Save "
          "turns red): saving the capture with the project, swaps and copies between packs, own-synth patches, saving the synth patch, "
          "copying projects and deleting packs. The original's saves work.",
          "The **RC** has everything marked «since RCx» in the docs; the **beta** adds what is marked «Beta 5.56 only».",
          "Installing restarts the device: what was not saved is lost; projects, packs and settings stay. Projects and packs saved with "
          "the mod also open on the official firmware, which ignores the mod's data.",
          "The **card and device app** organises the card and the device from a computer: open it "
          "[online](https://ghillermo.github.io/CIRCUIT-HACKS-RC/app.html) in Chrome or Edge, or download "
          "[`hr_app.zip`](https://ghillermo.github.io/CIRCUIT-HACKS-RC/hr_app.zip) (it also moves samples, patterns and FM patches to a "
          "Circuit Rhythm). [Card and device app](#app-sd) · [Installing and going back](#instalar)"]),
    es=E("El mod se instala desde una página web: el instalador toma el firmware oficial 1.2.1 de Novation para el Circuit Tracks, le "
         "aplica los cambios del mod en el navegador y envía el resultado al aparato por USB (Web MIDI). El bootloader de Novation no se "
         "toca nunca, así que siempre se puede volver al firmware oficial.",
         ["**Haz antes una copia de la microSD.** Con las versiones que no acaban en «S», no uses la memoria interna para proyectos.",
          "Descarga el firmware oficial 1.2.1 de Novation para el Circuit Tracks (el instalador solo acepta ese).",
          "Descarga el instalador, [`rc_uploader.zip`](https://ghillermo.github.io/CIRCUIT-HACKS-RC/rc_uploader.zip), descomprímelo, abre "
          "`rc_uploader.html` en Chrome o Edge y conecta el Circuit Tracks por USB.",
          "Elige el fichero oficial y la versión: la versión candidata (RC), su gemela más segura «S», una beta, u «Oficial» para volver. "
          "**Buscar versiones nuevas** añade las publicadas que tu copia no lleva (hace falta internet).",
          "Envía.",
          "**Volver atrás:** envía otra versión o el firmware oficial. Si el aparato no arranca, mantén **Scales + Preset + Note** al "
          "encenderlo (el modo de recuperación del bootloader) y vuelve a enviar."],
         ["La versión **«S»** es la RC con todo lo que el mod escribiría o borraría en la tarjeta o en la memoria interna rechazado (Save "
          "se pone rojo): guardar la captura con el proyecto, intercambios y copias entre packs, los patches del sinte propio, guardar el "
          "patch del sinte, copiar proyectos y borrar packs. Los guardados del original funcionan.",
          "La **RC** tiene todo lo marcado «desde RCx» en la documentación; la **beta** añade lo marcado «solo Beta 5.56».",
          "Instalar reinicia el aparato: lo que no se guardó se pierde; proyectos, packs y ajustes se quedan. Los proyectos y packs "
          "guardados con el mod también se abren en el firmware oficial, que no lee los datos del mod.",
          "La **app de la tarjeta y del aparato** organiza la tarjeta y el aparato desde el ordenador: ábrela "
          "[en línea](https://ghillermo.github.io/CIRCUIT-HACKS-RC/app.html) en Chrome o Edge, o descarga "
          "[`hr_app.zip`](https://ghillermo.github.io/CIRCUIT-HACKS-RC/hr_app.zip) (también pasa samples, patrones y parches FM a un "
          "Circuit Rhythm). [App de la tarjeta y del aparato](#app-sd) · [Instalar y volver atrás](#instalar)"]))

# E5 MIDI tables
EXPLAIN["tablas-midi"] = dict(
    en=E("The reference of the MIDI numbers the mod adds, for mapping an external controller or a DAW to the new parameters: the MIDI "
         "tracks' engine on the track's channel (stock CCs where they fit, NRPN MSB 4 for the rest), the drums' new knobs as NRPN MSB 5-8 "
         "on the drums' channel, and Master FX as NRPN MSB 9 on channel 16.",
         ["**MIDI 1 / 2 engine** (the track's channel): Filter CC 74, Resonance CC 71, Env → filter CC 79, Attack CC 73, Decay CC 75, "
          "Sustain CC 70, Release CC 72, Effect CC 91, Gain CC 59, LFO speed NRPN 0:76.",
          "TUNE CC 26, FINE CC 27, WAVE CC 20, SHAPE CC 21, TUNE 2 CC 37, FINE 2 CC 39, WAVE 2 CC 30, SHAPE 2 CC 31, MIX CC 52, RING CC "
          "54; the rest NRPN MSB 4 with the code as LSB: 4 LFO → filter, 12 LFO → level, 13 effect type, 15 env → level, 16 filter type, "
          "21-26 LFO / envelope → pitch, shape and morph, 32 BITSYNC, 33 FM.",
          "**Drums** (the drums' channel): CC 99 = 5 / 6 / 7 / 8 for Drum 1-4, CC 98 = the LSB, CC 6 = the value: 1 env → pitch, 2 ring "
          "frequency, 3 LFO amount, 4 LFO speed, 5 env → cutoff, 6 resonance, 7 envelope shape, 8 ring amount, 9 filter mode, 10 start, 11 "
          "bitcrush, 12 distortion type, 13 cut, 14 attack.",
          "**Master FX** (channel 16): CC 99 = 9, CC 98 = 4 × effect + knob (K1-K4 = 0-3), CC 6 = the value: Gater 0-3, Auto-Filter 4-7, "
          "Digitise 8-11, Phaser 12-15, Glitch 16-19.",
          "Send an NRPN as CC 99, CC 98, CC 6, in that order; the device keeps the chosen NRPN until the next CC 99 / 98."],
         ["Values 0-127; bipolar parameters have 64 at the centre. Filter mode: 0 stock EQ tilt, 1 band pass, 2 notch, 3 comb, 4 DJ; "
          "distortion type: 0 stock, 1 soft, 2 hard, 3 fold; bitcrush 0-15; start and cut 0-120.",
          "In the granular engine, page 2's numbers mean other things (TUNE = pitch, FINE = size, WAVE = position…). The drums' stock "
          "knobs and the device's own parameters keep the numbers of Novation's Programmer's Reference Guide.",
          "*(Beta 5.56 only)* The page and knob of several engine numbers change, and TUNE 2 (CC 37) becomes OSC 2's ratio, ¼ … 31.",
          "The full table, with the page and knob of every number: [MIDI: own behaviours, new CCs and NRPNs](#midi)."]),
    es=E("La referencia de los números MIDI que añade el mod, para mapear un controlador externo o un DAW a los parámetros nuevos: el "
         "motor de las pistas MIDI por el canal de la pista (los CC de stock donde encajan, NRPN MSB 4 para el resto), los knobs nuevos de "
         "los drums como NRPN MSB 5-8 por el canal de drums, y Master FX como NRPN MSB 9 por el canal 16.",
         ["**Motor de MIDI 1 / 2** (canal de la pista): Filtro CC 74, Resonancia CC 71, Env → filtro CC 79, Ataque CC 73, Decay CC 75, "
          "Sustain CC 70, Release CC 72, Efecto CC 91, Gain CC 59, Velocidad del LFO NRPN 0:76.",
          "TUNE CC 26, FINE CC 27, WAVE CC 20, SHAPE CC 21, TUNE 2 CC 37, FINE 2 CC 39, WAVE 2 CC 30, SHAPE 2 CC 31, MIX CC 52, RING CC "
          "54; el resto NRPN MSB 4 con el código como LSB: 4 LFO → filtro, 12 LFO → nivel, 13 tipo de efecto, 15 env → nivel, 16 tipo de "
          "filtro, 21-26 LFO / envolvente → tono, forma y morph, 32 BITSYNC, 33 FM.",
          "**Drums** (canal de drums): CC 99 = 5 / 6 / 7 / 8 para Drum 1-4, CC 98 = el LSB, CC 6 = el valor: 1 env → tono, 2 frecuencia "
          "del ring, 3 cantidad del LFO, 4 velocidad del LFO, 5 env → corte, 6 resonancia, 7 forma de la envolvente, 8 cantidad del ring, "
          "9 modo de filtro, 10 inicio, 11 bitcrush, 12 tipo de distorsión, 13 corte, 14 ataque.",
          "**Master FX** (canal 16): CC 99 = 9, CC 98 = 4 × efecto + knob (K1-K4 = 0-3), CC 6 = el valor: Gater 0-3, Auto-Filter 4-7, "
          "Digitise 8-11, Phaser 12-15, Glitch 16-19.",
          "Manda un NRPN como CC 99, CC 98, CC 6, en ese orden; el aparato recuerda el NRPN elegido hasta el siguiente CC 99 / 98."],
         ["Valores 0-127; los parámetros bipolares tienen el 64 en el centro. Modo de filtro: 0 EQ tilt de stock, 1 paso banda, 2 notch, 3 "
          "comb, 4 DJ; tipo de distorsión: 0 stock, 1 suave, 2 dura, 3 plegada; bitcrush 0-15; inicio y corte 0-120.",
          "En el motor granular, los números de la página 2 significan otras cosas (TUNE = tono, FINE = tamaño, WAVE = posición…). Los "
          "knobs de stock de los drums y los parámetros propios del aparato siguen con los números de la Programmer's Reference Guide de "
          "Novation.",
          "*(solo Beta 5.56)* Cambian la página y el knob de varios números del motor, y TUNE 2 (CC 37) pasa a ser el ratio de OSC 2, ¼ … "
          "31.",
          "La tabla completa, con la página y el knob de cada número: [MIDI: comportamientos propios, CC y NRPN nuevos](#midi)."]))


def missing(ids):
    """the ids (sections of the feature list) without an explanation in both languages"""
    return [i for i in ids if not (i in EXPLAIN and {"en", "es"} <= set(EXPLAIN[i]))]


def check():
    """-> a list of problems: missing sections or languages, links to no view of the guide, unbalanced bold, words of the inner works"""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import make_guide as G
    import make_manual as M
    import make_wiki as W
    M.use("en")
    ids = [s_["id"] for _, s_ in M.numbered() if s_["id"] not in W.DEV]
    views = {v["id"] for v in G.data("en")[0]}
    bad = [f"no explanation: {i}" for i in missing(ids)] + [f"not in the feature list: {i}" for i in EXPLAIN if i not in ids]
    for sid, d in EXPLAIN.items():
        for lang in ("en", "es"):
            e = d.get(lang)
            if not e or not e["what"] or not e["how"]: bad.append(f"{sid} {lang}: incomplete"); continue
            for t in [e["what"]] + e["how"] + e["notes"]:
                for a in re.findall(r"\]\(#([\w-]+)\)", t):
                    if a not in views: bad.append(f"{sid} {lang}: #{a} is no view of the guide")
                if t.count("**") % 2: bad.append(f"{sid} {lang}: unbalanced bold: {t[:60]}")
                if "\n" in t: bad.append(f"{sid} {lang}: a line break")
                for m in W.BANNED.finditer(t): bad.append(f"{sid} {lang}: «{m.group(0)}»")
    return bad


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    bad = check()
    for b in bad: print("!", b)
    print(f"{len(EXPLAIN)} sections explained; {len(bad)} problems")
    return len(bad)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
