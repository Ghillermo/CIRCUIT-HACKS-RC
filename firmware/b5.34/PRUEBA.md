# Beta 5.34 = Beta 5.33 (= SC53) + morph de patches

SHA-256 del `.syx`: `22cae45b9358837eb2677aac0043bc08b2662e8d21bc9333f151fee82ad8a569`.

Morph de patches en Synth 1 / 2 y en el sinte propio de MIDI 1 / 2 (también su FM de 8 operadores). Uno a la vez; no se guarda nada.

1. **Entrar:** vista Preset de Synth 1. Mantener dos patches (p. ej. los pads 5 y 6) y pulsar **Duplicate**. Los pads se apagan salvo **1 y 8** (color de Synth 1, tenue) y **32** (rojo).
2. **K1 = posición en la cadena:** cadena = el sonido de antes de tocar los pads + los mantenidos, en orden de pad. K1 a la izquierda = el sonido de antes, a la derecha = el último patch; en medio se mezclan (los parámetros continuos se interpolan, los de tipo a tipo cambian a mitad).
3. **Moduladores** (los de profundidad, bipolares: derecha hacia el final de la cadena): K2 / K3 LFO 1 profundidad / velocidad, K4 / K5 LFO 2 (pasos al azar) profundidad / velocidad, K6 azar en cada paso de la pista, K7 / K8 envolvente profundidad / tiempo. **Pads 1 y 8** disparan la envolvente (brillan mientras suena). **Clear + knob** = 0. Los LEDs de los knobs en el color de la pista.
4. **Octave ▼ / ▲:** mueve el sonido inicial un sitio antes / después en la cadena (cada Octave encendido si se puede mover). Duplicate no hace nada.
5. **Preset:** enseña los patches, los de la cadena en blanco. Preset otra vez = vuelve a la vista del morph. **Mantener patches 0,4 s** = la cadena pasa a ser el sonido inicial + esos (los knobs se quedan). **Tocar un patch** = lo carga y sale del morph.
6. **Salir:** pad 32, el botón de Synth 1 o tocar un patch. El sonido se queda donde estaba.
7. **MIDI 1** con el motor encendido (oscilador o FM): lo mismo con los huecos del sinte propio (pads 9-24). Con FM en los dos patches, también se mezcla el FM.
8. Repetir en Synth 2 y MIDI 2.

Además, **teclado externo a un paso**: en Setup, Note encendido (verde, el teclado externo al arpegiador). En la vista Note de Synth 1, mantener un paso vacío y tocar dos notas en un teclado MIDI externo por el canal de Synth 1: las dos quedan en ese paso (con su velocity), como al tocar pads con el paso mantenido; suenan igual que siempre. Con Note apagado, o sin paso mantenido, no se escribe nada. Probar también en MIDI 1.

Además, sin cambios a la vista: las tablas de knobs de Master FX que son escalones o rectas se calculan al arrancar (Gater, Auto-Filter, Phaser, Digitise y la sincronía de LFO deben sonar igual que en la 5.33).
