# SC44.3 / Beta 1.32 (B1.32) = SC44.2 + el LFO del sinte propio con el triángulo por defecto y sample & hold suavizado; el LFO 2 de la matriz con sample & hold suavizado

`circuittracks-4486-SC44.3.syx` — SHA-256 `9c16279a2be0f3acbd792f106ac3ad90cfe38c20ea9725775c275936c7debffd`, marca `SC44.3`.
`firmware/b1.32/circuittracks-4486-B1.32.syx` — SHA-256 `a29350b9a3ea69f74aa438a0fc008b206f730430811273f3c59a0f692609e8e4`: el mismo código con la marca `B1.32` (**Beta 1.32**).

El usuario (2026-10-18): «Fix: set triangle as default waveshape for the lfo, add s&h (stepped random) and slewed s&h (glided random) as waveshapes».

- **LFO del motor** (página 5, Shift + K8): siete formas: diente de sierra inverso (naranja), diente de sierra (magenta), triángulo (verde), cuadrada (roja), seno (cian), sample & hold (blanco), **sample & hold suavizado (violeta)**; **sin forma guardada, el triángulo**.
- **LFO 2 de la matriz** (Shift + K4): triángulo (verde, el inicial), diente de sierra (magenta), cuadrada (roja), sample & hold (blanco), **sample & hold suavizado (violeta)**; 5 zonas de 32 (hasta 159).

## Qué probar
1. Un proyecto nuevo: MIDI 1 con el oscilador, el LFO al filtro o al tono (página 5): suena en triángulo; Shift + K8: el LED verde.
2. Shift + K8 hasta el final: tras el blanco (sample & hold: escalones) viene el violeta: el mismo azar pero deslizándose de un valor al siguiente. Velocidad del LFO (K5 de la página 5) lenta para oírlo.
3. Un proyecto guardado con otra forma: la conserva. Un patch propio de antes de las formas: diente de sierra inverso.
4. Matriz: K4 a un destino, Shift + K4: verde → magenta → rojo → blanco → violeta; con el violeta el destino se desliza, con el blanco salta.

## Verificación en emulación
- `emu_sc44_3.py`: sin la marca del proyecto, la forma 2 (el ACT de MIDI 1 con 2 en los bits 13-15); Shift + K8 de la página 5 desde el triángulo hasta 6 (LED violeta), sin vuelta; el patch: versión 1 = diente de sierra inverso, versión 2 con la forma 6 = 6; LFO 2 de la matriz: los 5 colores, hasta 159; la resonancia con el sample & hold de escalones: 5 valores y saltos de hasta 68; con el suavizado: 93 valores, pasos de como mucho 10.
- `emu_sc44_3_dsp.py` (frente a SC44.2): el núcleo 0 entero igual bloque a bloque con el mismo tráfico; las formas 1-5 como sus modelos; la forma 6 como el modelo en coma fija en 405 / 405 bloques (5 vueltas: el valor anterior a OSC1 + 26 y uno nuevo del generador de ruido; en medio, el deslizamiento).
- `emu_sc44_2.py` (la matriz y el teclado partido) sobre SC44.3; `compact_check.py build_sc44_3.py`.
