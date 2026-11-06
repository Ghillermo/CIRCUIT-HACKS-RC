# SC52.4 = SC52.3 + los dos osciladores reordenados y más limpios

SHA-256 del `.syx`: `2bccfaf8845a846c267f31d4b345f72c6b9788cf3443b3cdb8a1f72deb0fe166`. El resto: [`firmware/sc52.3/PRUEBA.md`](../sc52.3/PRUEBA.md).

MIDI 1, motor oscilador (o wavetable), **pad 28 encendido** (dos osciladores).

1. **Página OSC 2 (pad 3):** K1 ratio, K2 detune, K3 onda, K4 shape, K5 FM, K6 ring, K7 sync / bitwise, K8 mix. Los valores de un patch guardado antes siguen ahí (solo cambian de knob).
2. **K5 (FM):** en el centro, sin FM (LED tenue). A la derecha OSC 2 modula a OSC 1 (con MIX a la izquierda se oye OSC 1 modulado); a la izquierda, al revés (con MIX a la derecha se oye OSC 2 modulado); en los extremos, los dos. Las cantidades bajas, más finas que antes.
3. **Un patch / proyecto anterior con FM:** suena con la misma cantidad de FM (K5 a la derecha del centro).
4. **K7, zona sync:** sync clásico; al girar dentro de la zona, el barrido típico (sin ruido). Con una sierra en OSC 2 y MIX a la derecha.
5. **Ruido:** FM con OSC 1 en sierra, en notas agudas: mucho menos crepitar que en la Beta 5.26. Xor: menos ruido blanco.
6. **Poly (de fábrica) con dos osciladores y K1 de OSC 2 en ratio 2:** OSC 2 una octava arriba (antes, al tope).
7. **Página OSC 1 (pad 2):** K1 pitch, K2 fino, K3 onda (en la wavetable, el cuadro), K4 shape / warp, K7 LFO → onda; Shift: K1 env → pitch, K2 LFO → pitch, K3 env → onda, K4 env → shape, K7 LFO → shape. **K5 / K6 / K8 = LFO → FM / ring / mix; con Shift, la envolvente.** Clear + knob = 0. Guardar el patch y el proyecto, apagar y volver: siguen.
8. **Grabar:** Record + Play, girar un knob del sinte propio que no esté en la página 4 (p. ej. K4 shape): pasa a un carril vacío y se graba; Shift en la página 4 enseña el destino nuevo. Con los 8 carriles con algo, no se graba.
9. **Wavetable:** las listas de los pads 7 / 8 cambian el cuadro que señala K3 (antes K7).
