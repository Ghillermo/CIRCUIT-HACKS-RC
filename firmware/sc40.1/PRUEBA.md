# SC40.1 — knobs del sidechain

`circuittracks-4486-SC40.1.syx` — SHA-256 `d2c04ac0f10069fa927c97b57d9fb12532ffe0b26d3e35a06dd96eb4bdcae3cd`
Imagen de 0x689c4 bytes, CRC 0xd69d6535, marca `SC40.1`.

Es SC40 con una función nueva (solo ARM): **en la vista Sidechain (Shift + FX) los knobs editan el sidechain de la pista elegida.**

| Knob | Parámetro |
|---|---|
| K1 | Ataque |
| K2 | Hold |
| K3 | Decay |
| K4 | Profundidad |

- **La pista elegida** es la del último pad de preset que tocaste (Synth 1, Synth 2, MIDI 1 o MIDI 2); hasta que toques uno, Synth 1. Los LEDs de K1-K4 toman el color de esa pista y el brillo del valor.
- La fuente se sigue eligiendo con los pads 5-8. Tocar un preset vuelve a escribir sus cuatro valores.
- Los cambios se guardan con el proyecto.

## Qué probar
1. Shift + FX. Toca un preset de Synth 1 con profundidad y gira K4: el bombeo cambia. K1-K3 cambian la forma.
2. Octave ▼ (página de MIDI 1 / 2), toca un preset de MIDI 2: los LEDs cambian de color y los knobs editan MIDI 2.
3. Guarda, apaga, carga: los valores siguen.
4. Fuera de la vista los knobs hacen lo de siempre.
5. Todo lo de `firmware/sc40/PRUEBA.md`.

## Verificación en emulación
- `emu_sc40_1.py`: los knobs reales mueven ataque / hold / decay / profundidad de la pista elegida, con topes; la fuente y las otras pistas no cambian; LEDs; fuera de la vista nada; SC40 sin cambios.
- **Sin comprobar en emulación:** el sonido.
