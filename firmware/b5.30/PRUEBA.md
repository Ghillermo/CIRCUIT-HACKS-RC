# Beta 5.30 = Beta 5.29 (= SC52.6) + el BLEP de 4 puntos

SHA-256 del `.syx`: `c9c420bdaf631e0391b8618d2e8df99764eb2bdfac80c7cd3ca77e72951c8031`.

`vcf21_dsp.use_blep4()`: el antialiasing de las formas de onda con salto (sierra, supersaw, pulso) pasa del polyBLEP de 2 muestras al BLEP de 4 de RYTHM (RD43). En emulación, por debajo de 8 kHz, sierra / pulso de −58…−67 dB a ≈ −87 dB en las notas 72 y 96; supersaw de −65 a −95 en la 96. El agudo baja un poco (≈ −2,5 dB a 10 kHz). Por voz y oscilador cuesta un 4-31 % más de DSP según la nota (más en notas agudas). `mixsolo` v1 (código muerto desde la v2) pasa al hueco de los programas antiguos del DSP para hacer sitio.

1. **Arranque en frío:** instalar, apagar y encender. Todo suena como en la 5.29.
2. **Sierra, pulso (SHAPE 20 / 50 / 80) y supersaw** en el sinte propio de MIDI 1 / 2: tocar notas agudas (dos octavas por encima del Do central y más). Menos chisporroteo / tonos inarmónicos que en la 5.29; el timbre igual salvo un pelo más apagado arriba.
3. **Seno y triángulo:** exactamente igual que antes.
4. **Dos osciladores:** sync duro con barrido, FM a la derecha y a la izquierda, bitwise: suenan como antes (el FM a la derecha algo más limpio).
5. **Carga:** 8 voces de supersaw en notas agudas con el resto del proyecto sonando: sin cortes ni ruidos.
6. **Mixer, pad 16 (solo / flip):** sigue funcionando (su código se ha movido).
