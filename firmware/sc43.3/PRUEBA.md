# Beta 1.23 (B1.23) = SC43.3 = SC43.2 + step-drummer de MIDI desde el punto sin modulación de su destino

`circuittracks-4486-SC43.3.syx` — SHA-256 `5bdecb997ed029542a6a7b4f03f25781a0192646ca2ba3b10fca54d3d6d5f210`, marca `SC43.3`.
`firmware/b1.23/circuittracks-4486-B1.23.syx` — SHA-256 `47da7f38c383ed975103b932ec3fef10c4cc1d419992a98a226449b4419db1c6`: el mismo código con la marca `B1.23` (**Beta 1.23**).

El usuario (2026-10-16), en una pista MIDI de un proyecto nuevo: «Set center for bipolar parameters and 0 for unipolar, both with dimmer = no modulation, brighter = positive or negative modulation» (los knobs de los pares, no los pads).

- **Destinos bipolares** (pads 17, 18 y 22: tono de los dos osciladores, tono del OSC 2, envolvente → filtro): sin modulación = el centro (64); el knob sube o baja.
- **Destinos unipolares** (pads 19, 20, 21, 23 y 24: WAVE, FM, MIX, SHAPE, decay): sin modulación = 0; el knob solo suma.
- Un par vacío empieza en ese punto, y **el LED del knob enseña la cantidad**: tenue = sin modulación, más brillante cuanto más se aleja (en los bipolares, hacia arriba o hacia abajo).
- Igual en la página 2 con destino, y la transposición del toggle pitch-vel cuenta desde ese punto (destino unipolar: solo hacia arriba).
- Synth 1 / 2 y el secuenciador de efectos, como antes. Incluye Beta 1.22.

## Qué probar
1. MIDI 1 con un motor, proyecto nuevo, pad 30 = step-drummer: los 8 knobs tenues (destino tono). Girar uno: más brillante hacia los dos lados.
2. Pad 20 (FM): los pares vacíos tenues; girar = solo hacia arriba, más brillante cuanto más FM.
3. Octave ▼ (página 2), elegir un destino: lo mismo.

## Verificación en emulación
- `emu_sc43_3.py`: página 1 tono = 64 y LEDs a brillo 2; +5 / −10 = 69 / 59 a brillo 12; FM = 0 tenue, +5 = 5 a brillo 7, el par a 69 = 71; `c_sdfx` de FM 40 + 5 / 40 + 69; página 2 WAVE desde 0, tono del OSC 2 desde 64 (brillo 12, el par a 5 = 120), su desplazamiento 69 − 64; toggle: FM 5 / 16 = 1 / 2 grados, tono 69 / 59 = 1 / −1. También `emu_sc43_2.py`, `emu_sc43_1.py`, `emu_sc43.py`, `emu_sc42_7.py` sobre SC43.3.
