# SC38 — Mixer: Shift + knob = nivel a 100 / 0

`circuittracks-4486-SC38.syx` — SHA-256 `569c35175d8e6b9450c30708ed9950f914697c23f79c4300882a2d435c714c51`
Imagen de 0x65e8c bytes, CRC 0x3cdaebac, marca `SC38`.

Es SC37.9 con un atajo nuevo en la vista Mixer (página de niveles):
- **Shift + girar un knob a la derecha:** el nivel de esa pista pasa a **100**.
- **Shift + girar a la izquierda:** el nivel pasa a **0**.

Antes, Shift + knob en el Mixer hacía lo mismo que el knob solo: no se pierde ninguna función. No cambia: la página de panorama (Octave ▼), Clear + knob (borrar automatización) ni Master FX (Mixer dos veces).

## Qué probar
1. Mixer: Shift + K1 a la derecha → el nivel de Synth 1 salta a 100; a la izquierda → 0.
2. Grabando, Shift + knob deja el salto grabado como un giro normal.
3. Octave ▼ (panorama): Shift + knob mueve el panorama como siempre.
4. Clear + knob en el Mixer sigue borrando la automatización.
