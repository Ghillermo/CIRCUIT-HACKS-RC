# SC52.3 = SC52.2 + la wavetable tras el aparato

SHA-256 del `.syx`: `6b0f3a768d0ffd1fc5f1ccce68085b97c40ac78db4da0adfa718d5c6833108c8`. El resto: [`firmware/sc52.2/PRUEBA.md`](../sc52.2/PRUEBA.md).

1. Vista Preset de MIDI 1 / 2, pad 27 (fila de motores), pad 21: **el pad 27 se ve arena**, no verde, con la fila abierta y cerrada.
2. Con la fila abierta: **mantén el pad 7** → la lista de las 16 tablas Nova tapa la fila; un toque cambia la tabla y **suena la tónica hasta soltar**; al soltar el pad 7 vuelve la fila.
3. Fila cerrada, página OSC 1: K7 en el centro. **Pad 8 mantenido + un sample** → el cuadro del centro pasa a ser el ciclo de ese sample (suena la tónica); mueve K7 y oye que solo ese cuadro cambió.
4. K7 al principio: **pad 7 mantenido + Shift + otra tabla** → solo el primer cuadro cambia (por el primer cuadro de esa tabla); sin Shift, la tabla entera.
5. Octave ▼ / ▲ con el pad 8 mantenido = página de samples, como antes.
6. Guardar el patch y el proyecto, apagar y volver: la tabla con sus cuadros cambiados vuelve.
7. El bucle del sample capturado (Shift + pad 7 en Master FX) al cargar otro proyecto, como en SC51.3 (`loopcarry` está en otro sitio de la flash).
