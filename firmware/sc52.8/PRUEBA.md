# SC52.8 = SC52.7 + funciones propias del modo de un oscilador (= Beta 5.31 sin la marca)

SHA-256 del `.syx`: `79bc9ac08ec3fac82aeb579590197e242e57f0364e9bc0063af9345be75adea3`.

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
