# SC45.6 / Beta 3.13 = SC45.5 + FM de 4 operadores

`firmware/sc45.6/circuittracks-4486-SC45.6.syx` — SHA-256 `de0ae4a2eb98b2eb68068670918fc3bf0ec0f71728a83ed8079e2550c9c225f7`, marca `SC45.6`.
`firmware/b3.13/circuittracks-4486-B3.13.syx` — SHA-256 `73890089d6b74de061c0756d50b1e6ce00dcc88057f2b2d44311cb17a26e02f5`, marca `B3.13` (**Beta 3.13**, el mismo código).

El usuario (2026-10-21): «FM as another variant for osc», «4op, A/R with fixed sustain. Release could be velocity-dependant», «kick/noise percussive algos, some bell and some strings along with the typical algorithms».

**Cómo se usa:** MIDI 1 / 2, vista Preset, un toque al **pad 27** (la fila de motores) y el **pad 24** (violeta) = FM. El **pad 7** abre su página:
- **K1-K4** = ratio de los operadores 1-4 (0,5 … 16), **K5-K8** = su nivel (el de un portador = volumen; el de un modulador = cuánto modula);
- **Shift + K1-K4** = su ataque; **Shift + K5** = el algoritmo (16, 8 clics cada uno; el LED en el color de la familia: blanco clásicos, rojo percusivos, verde azulado campanas, verde cuerdas); **Shift + K6** = feedback, **Shift + K7** = ruido, **Shift + K8** = release (más largo cuanto más fuerte la nota);
- **Clear + knob** = su valor inicial, **Clear + pad 7** = todos;
- la nota, TUNE / FINE, la envolvente de pitch y el vibrato de la página 2, el VCA-VCF, el efecto y la matriz siguen valiendo; una nota a la vez.
Algoritmos: 1-8 clásicos (pila, ramas, dos pilas, órgano…), 9 bombo (el operador 4 = la caída de pitch: su nivel = cuánto, su release = cuánto tarda), 10 caja (+ ruido), 11 metal / hi-hat, 12 tom / zap, 13 campana, 14 campana tubular, 15 cuerdas, 16 ensemble. La tabla está en la guía (capítulo «FM de 4 operadores»).

## Qué probar
1. MIDI 1 con el motor encendido: pad 27, pad 24: suena FM (el algoritmo 1, la pila). Pad 24 violeta, el pad del oscilador tenue; pad 27 violeta.
2. Pad 7: K5-K8 cambian el timbre (K5 el volumen; K6-K8 el brillo). K1-K4: ratios (con K2 a 2 o 3, más armónicos; a 1,41 / 4,24, metálico).
3. Shift + K1 hacia la derecha: el operador 1 entra despacio. Shift + K8: release más largo; notas fuertes = colas más largas.
4. Shift + K5 por las familias: bombo (algoritmo 9: K8 = la caída de pitch; Shift + K8 cuánto tarda), caja (con Shift + K7 el ruido), campana (13-14), cuerdas (15-16, con un poco de ataque).
5. Varias notas y acordes rápidos sin chasquidos; las dos pistas MIDI en FM a la vez con muchas cosas sonando: sin cortes del audio.
6. Guardar un patch propio en FM, cargar otro y volver: el FM y sus valores vuelven. Elegir otro motor en la fila: el FM se apaga.

## Verificación en emulación
- `emu_fm_dsp.py` en SC45.6 (frente a SC45.5) y B3.13 (frente a B3.12); `emu_fmeng.py` en las dos.
