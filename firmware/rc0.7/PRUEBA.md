# RC0.7 = RC0.6 + dos arreglos

`circuittracks-4486-RC0.7.syx` — SHA-256 `940108b1e92c2c59ad8fd57d7be3fdb7dc7bb054ce49f0e06c73471c817c2ef1`, marca `RC0.7`.

1. **El step-drummer, el secuenciador de efectos, el stretch del granular y la captura armada leen su propia pista.** Leían el patrón, el paso y los ticks de otra pista (una dirección base equivocada, 12 bytes más allá): no se notaba mientras todas las pistas tenían la misma longitud. Visto en el aparato: la secuencia de efectos de MIDI 1 se cortaba con la longitud de otra pista.
2. **El knob selector del secuenciador de efectos va tres veces más lento** (un hueco cada ~48 pasos de giro). Los valores guardados en los patrones no cambian.

## Qué probar
- MIDI 1 con un patrón de 32 pasos y Synth 1 / drums de 16: el step-drummer y el secuenciador de efectos de MIDI 1 recorren los 32 pasos.
- El knob de un par en el secuenciador de efectos: más lento, sin saltos.
- Captura armada (Shift + pad 32) con el transporte en marcha: empieza en el siguiente compás, no al momento.
- Stretch del granular: el tramo dura los pasos de K3.

## Verificación en emulación
`emu_rc0_7.py`: el paso que lee el step-drummer de MIDI 1 (el suyo; RC0.6: el de Drum 2) y el knob (una unidad cada tres eventos, el resto se conserva).
