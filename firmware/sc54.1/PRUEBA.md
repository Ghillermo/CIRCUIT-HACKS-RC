# SC54.1 = SC54 con la segunda versión del morph de patches

**SC54 / Beta 5.34 reinician el aparato en la vista Preset de MIDI 1 / 2.** La primera reconstrucción con el arreglo conservó la marca «SC54» / «B5.34» y el bootloader no la instaló (salta una imagen con el mismo bloque de versión): esta lleva la marca «SC54.1». Instalarla sobre SC54 / Beta 5.34.

SHA-256 del `.syx`: `34ff26349b3c64fede5e797e15c010bc9127f413d4c07da34cda017894181cdd`.

Morph de patches en Synth 1 / 2 y en el sinte propio de MIDI 1 / 2 (también su FM de 8 operadores). Uno a la vez; no se guarda nada.

1. **Entrar:** vista Preset de Synth 1. **Mantener dos patches** (p. ej. los pads 5 y 6) **0,4 s** (o mantenerlos y pulsar Duplicate). Se abre la vista alternativa de Synth 1 con el morph: pads apagados salvo **1 y 8** (color de Synth 1, tenue) y **32** (rojo). **Un solo patch mantenido no abre el morph.**
2. **K1 = posición en la cadena:** cadena = el sonido de antes de tocar los pads + los mantenidos, en orden de pad. K1 a la izquierda = el sonido de antes, a la derecha = el último patch; en medio se mezclan (los parámetros continuos se interpolan, los de tipo a tipo cambian a mitad).
3. **Moduladores** (los de profundidad, bipolares: derecha hacia el final de la cadena): K2 / K3 LFO 1 profundidad / velocidad, K4 / K5 LFO 2 (pasos al azar) profundidad / velocidad, K6 azar en cada paso de la pista, K7 / K8 envolvente profundidad / tiempo. **Pads 1 y 8** disparan la envolvente (brillan mientras suena). **Clear + knob** = 0. Los LEDs de los knobs en el color de la pista.
4. **Octave ▼ / ▲:** mueve el sonido inicial un sitio antes / después en la cadena (cada Octave encendido si se puede mover). Duplicate no hace nada en esta vista.
5. **Preset:** enseña los patches, los de la cadena en blanco. **Preset otra vez = vuelve a la vista del morph.** Mantener **dos o más** patches 0,4 s = la cadena pasa a ser el sonido inicial + esos (los knobs se quedan). Tocar un patch = lo carga y sale del morph.
6. **Volver a la vista:** ir al Mixer (u otra vista) y pulsar **Synth 1**: vuelve a la vista del morph. Desde la vista del morph, Synth 1 = la vista Note; Synth 1 otra vez = la vista del morph.
7. **Salir:** **pad 32** (vuelve a los patches, que deben verse como siempre: nada del morph se queda en los pads) o tocar un patch. El sonido se queda donde estaba.
8. **Preset dos veces** (sin morph): abre la vista alternativa de Synth 1, la misma que Synth 1 dos veces.
9. **MIDI 1** con el motor encendido (oscilador o FM): lo mismo con los huecos del sinte propio (pads 9-24); la vista del morph está sobre su vista Preset, y Preset cambia entre el morph y los huecos. Con FM en los dos patches, también se mezcla el FM. **Comprobar que la vista Preset de MIDI 1 / 2 ya no reinicia el aparato** (con y sin morph).
10. Repetir en Synth 2 y MIDI 2.
11. **Con el morph encendido en Synth 1:** Clear + Synth 1 (desde su Note) no abre la vista del morph; Synth 2 mantenido + Synth 1 = el teclado partido de siempre (Synth 1 solo lo termina; otra vez = la vista del morph); Shift + Synth 1 / Shift + MIDI 1 (con su morph) acaban en la vista del morph; Clear + un patch en los patches = el guardado de siempre (el morph sigue); con el morph de MIDI 1 en sus huecos, Clear + pad 30 no hace nada.
12. **Instalar con un morph encendido** (o reiniciar sin apagar): al arrancar el morph está apagado y el proyecto suena como siempre.

Además, **teclado externo a un paso**: en Setup, Note encendido (verde, el teclado externo al arpegiador). En la vista Note de Synth 1, mantener un paso vacío y tocar dos notas en un teclado MIDI externo por el canal de Synth 1: las dos quedan en ese paso (con su velocity), como al tocar pads con el paso mantenido; suenan igual que siempre. Con Note apagado, o sin paso mantenido, no se escribe nada. Probar también en MIDI 1.

Además, sin cambios a la vista: las tablas de knobs de Master FX que son escalones o rectas se calculan al arrancar (Gater, Auto-Filter, Phaser, Digitise y la sincronía de LFO deben sonar igual que en la 5.33).
