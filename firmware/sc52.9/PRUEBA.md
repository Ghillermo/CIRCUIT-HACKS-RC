# SC52.9 = SC52.7 + funciones propias del modo de un oscilador + vista de flip

SHA-256 del `.syx`: `9ac8a1150b5399e25769a96135a46a0b80196a7eeba7dd61cc19d7334b960ca5`.

**Vista de flip (pad 26 de la vista Preset de MIDI 1 / 2):** pad 26 solo abre / cierra la vista (blanco abierta), sin cambiar el modo. **Fila 3:** pad 17 = patch flip (PGM seq), pad 18 = step flip (excluyentes; tocar el encendido = apagado). **Fila 2:** con step flip, las pistas destino (la propia apagada). Step flip sin destino elegido = el último usado (de fábrica Synth 1). La vista se cierra sola al salir; los destinos ya no ocupan la fila 3 con la vista cerrada.

10. **Vista de flip:** MIDI 1, Preset, motor apagado. Pad 26: pad 26 blanco, pads 17 y 18 tenues, filas 2 y resto de la 3 apagadas. Pad 17: patch flip encendido (pad 17 brillante); otra vez: apagado.
11. Pad 18: step flip sobre Synth 1; la fila 2 enseña las pistas. Pad 12 = MIDI 2 de destino; tocar MIDI 1 (pad 11) no hace nada. Pad 18 otra vez: apagado; pad 18 de nuevo: vuelve a MIDI 2. Pad 17 con step flip: pasa a patch flip.
12. Pad 26: la vista se cierra y el modo se queda (con step flip, pad 26 parpadea en el color del destino). Cambiar de vista y volver: la vista está cerrada.


Con **un oscilador** (motor oscilador o wavetable, dos osciladores apagados), la página OSC 1 del sinte propio de MIDI 1 / 2:
**K5 = nivel del sub-oscilador** (una octava por debajo, cuadrada), **Shift + K5 = envolvente → sub**; **K6 = nivel del ruido**, **Shift + K6 = envolvente → ruido**; **K8 = LFO → sub**, **Shift + K8 = LFO → ruido**. Con dos osciladores, K5 / K6 / K8 siguen siendo LFO / envolvente → FM / RING / MIX. Se guarda con el patch y con el proyecto. Para hacer sitio, la tabla del filtro se calcula en la memoria X del DSP (sonido igual). Arreglo: en la página FM, con Shift + K1 (los algoritmos en los pads 1-32), los pads 1 y 4 ya no se intercambian.

1. **Arranque en frío:** instalar, apagar y encender. Todo suena como en la 5.30 (los filtros también: su tabla ha cambiado de sitio).
2. **Sub:** MIDI 1, motor oscilador, un oscilador, página OSC 1 (pad 2). K5 a la derecha: aparece una octava por debajo. LED de K5 más brillante con más nivel. Clear + K5: se apaga.
3. **Ruido:** K6 a la derecha: ruido sobre la nota (pasa por el filtro y el VCA).
4. **Envolvente:** K5 y K6 a 0, Shift + K5 / Shift + K6 a la derecha: el sub / el ruido siguen la envolvente del VCA (con una envolvente percusiva, solo al principio de la nota).
5. **LFO:** K8 a la derecha = el LFO mueve el nivel del sub; Shift + K8 = el del ruido.
6. **Dos osciladores (pad 28):** K5 / K6 / K8 vuelven a ser LFO / envolvente → FM / RING / MIX, con sus valores de antes; el sub y el ruido no suenan. Apagar los dos osciladores: vuelven el sub y el ruido como estaban.
7. **Poly** (pad 32, poly): el sub y el ruido en cada voz.
8. **Guardar:** guardar el patch (Clear + hueco dos veces) y cargarlo; guardar el proyecto, cargar otro y volver: el sub / ruido vuelven. Un patch o proyecto de antes: sin sub ni ruido.
9. **Página FM:** Shift + K1: los algoritmos en los pads 1-32 en su sitio (el primero brillante en el pad 1).
