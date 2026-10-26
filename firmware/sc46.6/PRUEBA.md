# SC46.6 / Beta 3.23 = SC46.5 / Beta 3.22 + el motor FM mejorado

`firmware/sc46.6/circuittracks-4486-SC46.6.syx` — SHA-256 `89c993b6455e159e73775dc4875bd017530503fbe7b4ad91f3c293b658e21bd0`, marca `SC46.6`.
`firmware/b3.23/circuittracks-4486-B3.23.syx` — SHA-256 `bebf4f17318dd4eedec3d16de3f4b906c13032f02fd292d0d940f0f579918dc2`, marca `B3.23` (**Beta 3.23**, el mismo código).

El estudio del motor FM (el usuario, 2026-10-24: «Mejora el motor FM») y sus respuestas del 2026-10-25. Todo en el FM del sinte propio de MIDI 1 / 2 (vista Preset, pad 27 → pad 24; pad 7 = su página), salvo lo de los patches y la matriz.

## Qué probar
1. **El volumen y las colas:** el FM con la pila y release largo (Shift + K8 a la derecha): al soltar la nota la cola suena entera (antes se cortaba en ~2 ms) y el principio de cada golpe tiene su clic (el bombo de Clear + pad 7 con el algoritmo 9).
2. **Elegir algoritmo con los pads:** en la página FM, mantener el pad 7: los pads 9-24 en los colores de las familias (el actual brillante); pulsar uno = elegido y suena la tónica mientras se mantiene; Shift + pad = sin sonar; soltar el pad 7 = vuelven los patches.
3. **Clear + pad 7** con cada algoritmo: una voz tocable (bombo, caja, hi-hat, tom, campana, tubular, cuerdas, ensemble, piano eléctrico, bajo, metales, órgano…). Clear + knob = el valor de esa voz.
4. **Ratios:** al girar K1-K4 los pads 9-32 enseñan los 24 ratios 1,5 s (el actual brillante, blanco si está desafinado) y no cargan patches; entre ratio y ratio, los clics desafinan (+2,5 cents; el LED a media luz): batido lento con dos operadores casi iguales.
5. **Shift + K1-K4:** a la derecha el ataque como antes; a la izquierda el operador cae solo con la nota pulsada (más a la izquierda, más rápido; LED rojo): un modulador así sobre un portador sostenido = piano eléctrico / pluck.
6. **Brillo:** SHAPE (K2 de la página OSC 1) a izquierda / derecha = menos / más modulación; Env → forma (K4) con la ADSR de la página 1 = una envolvente de brillo; LFO → forma (K6) = wah. La velocity también cambia el brillo; las notas agudas suenan menos brillantes y caen antes.
7. **Feedback** (Shift + K6) en un operador solo: de seno a sierra limpia; arriba del todo, ruido (para el hi-hat).
8. **Agudos:** notas altas con ratios altos: sin el ruido metálico de aliasing de antes (salvo en los percusivos).
9. **Legato:** Shift + pad 29 (retrigger apagado) con el bombo: notas ligadas no vuelven a disparar el golpe.
10. **Patches:** un patch FM guardado con la Beta 3.22 o antes se carga con su sonido (los ataques a la mitad derecha del knob); guardar y volver a cargar uno nuevo. **Shift + pad de patch** (9-24) = cargar sin la nota de escucha (cualquier motor).
11. **Clear + MIDI 1 / 2** = el motor entero a los valores iniciales, el FM incluido; la matriz (pad 6) se queda con sus destinos y la cantidad a cero (los LED de los knobs tenues en el color del destino).
12. Lo de SC46.5 / Beta 3.22 sigue igual (los motores sin FM suenan como antes: el DSP fuera del FM es idéntico).

## Verificación en emulación
- `emu_shortimm_dsp.py` (una build con solo `use_shortimm` frente a la Beta 3.22): el núcleo 0 entero, con el tráfico del motor, FM y el modo muestra, X / Y idénticos en cuatro puntos; 106 palabras menos.
- `emu_fm2_dsp.py` frente a la Beta 3.22: con la bandera FM a 0, el oscilador y los dos osciladores bit a bit; el FM contra un modelo exacto del bucle nuevo (4 → 1, R × 128, AMP suavizado, feedback promediado, seno refinado) en cuatro casos y dos notas; el AMP suavizado llega al objetivo y a 0; el armónico 3 a −47,1 dB (antes −28,6); el VCA abierto tras la puerta en FM y como antes sin FM; la pila del sistema igual.
- `emu_fmeng2.py`: todo lo de la lista de arriba por el controlador real y la tarea de LEDs (la lectura del DSP sustituida).
- `emu_fm_dsp.py` / `emu_fmeng.py` son de SC45.6 (el bucle y los ataques de antes): no valen sobre SC46.6. `emu_sc44_2.py` sobre SC46.6: pasa salvo el modo muestra, que ya fallaba en la Beta 3.22 (no vale desde SC45).
