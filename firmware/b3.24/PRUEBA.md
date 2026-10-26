# SC46.7 / Beta 3.24 = SC46.6 / Beta 3.23 + el modo muestra de MIDI 1 / 2 en estéreo

`firmware/sc46.7/circuittracks-4486-SC46.7.syx` — SHA-256 `0e67228c15e050c7f37c8edc356176e87b170e88b43955a0b978bdd6e571b973`, marca `SC46.7`.
`firmware/b3.24/circuittracks-4486-B3.24.syx` — SHA-256 `ccee6121b9858f760be2e8a1400e3f76e12bcedb424899cf1c6fe24429d321d3`, marca `B3.24` (**Beta 3.24**, el mismo código).

El usuario (2026-10-25): «haz midi 1_2 stereo, sin pareja» (tras el estudio: estéreo en las pistas del sinte propio en lugar de los drums; el modo pareja de drums, descartado).

## Qué probar
1. MIDI 1 en el modo muestra (pad 27 cian), un sample estéreo partido en dos huecos seguidos del pack (izquierda en N, derecha en N + 1; por ejemplo con `patchtool` o Components). Elegir N en la Note ampliada.
2. **K7 de la página OSC 1 (WAVE) a la izquierda del todo:** suena como siempre (solo N, mono).
3. **K7 hacia la derecha:** con la siguiente nota, N a la izquierda y N + 1 a la derecha; más a la derecha, más ancho. Con auriculares: la imagen estéreo del sample.
4. **El filtro** (página 1, K5 / Shift + K5): filtra los dos lados por igual (sin que la parte estéreo suene más brillante).
5. **Nivel / mute / panorama de la pista en el Mixer:** el nivel y el mute afectan a todo; el panorama mueve el centro (la parte estéreo se queda). Los envíos a reverb / delay llevan solo el centro.
6. **Prueba de fase:** el mismo sample mono en N y en N + 1: con el K7 a la derecha no debe cambiar nada (izquierda = derecha: sin parte estéreo).
7. Flips por paso (el selector), el último hueco (el 64 con el 1), la captura (siempre mono).
8. Lo de SC46.6 / Beta 3.23 sigue igual (el FM, los demás motores).

## Verificación en emulación
- `emu_smstereo_dsp.py` frente a SC46.6 / Beta 3.23: con WAVE 0, el anillo y el bloque OSC1 como antes, bit a bit; con WAVE 100, cuatro bloques exactos contra el modelo: centro (L + R) / 2 en el anillo, lado (L − R) / 2 × la anchura en la mitad `RDOFS` del búfer de lados del granular (`SOUT`); el sample 64 con el 1; la captura en mono; con el paso bajo, el centro y el lado por el mismo SVF con sus estados.
- `emu_shortimm_dsp.py` (una build con solo `use_oscsub` frente a SC46.6): el núcleo entero idéntico bloque a bloque (también con FM y el modo muestra); 174 palabras menos.
