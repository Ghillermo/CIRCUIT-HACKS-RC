# Beta 1.30 (B1.30) = SC44 = SC43.9 + modo muestra del sinte propio de MIDI 1 / 2

`circuittracks-4486-SC44.syx` — SHA-256 `db0850d2c8b90e90c0094413f3edfcb86c965e1ad24527d59563c724333251ac`, marca `SC44`.
`firmware/b1.30/circuittracks-4486-B1.30.syx` — SHA-256 `3cc0b68f0fdc76d068041ea6d4bb761077a84da8e7c6eb1613872ae3d480c1cb`: el mismo código con la marca `B1.30` (**Beta 1.30**).

El usuario (2026-10-17): «A, but instead of Sk8, sample selection mode overtakes the note expand view, and the available samples are the whole library. Ideally, sample flipping (recorded live or sequenced) will be available too» · «since samples are one-hit, the vca will default to full open during sample mode».

- **Modo muestra** (pad 27 cian, tras el magenta del granular): la pista MIDI toca un sample del pack de un golpe a la altura de la nota (C3 = como se grabó), por el filtro, el efecto y el LFO del motor, con el VCA abierto.
- **Selector** en la vista Note ampliada (Note dos veces): filas 3-4 = samples (Octave ▼ / ▲ = 4 páginas), filas 1-2 = pasos (mantener un paso + tocar un sample = sample flip; Clear + paso lo quita).

## Qué probar
1. MIDI 1, Preset, pad 27 hasta el cian (después del magenta). Note dos veces: las filas 3-4 tenues; tocar uno: suena y queda cian. Octave ▼ / ▲ por las 4 páginas (el botón encendido si hay más páginas en ese sentido).
2. Tocar notas (vista Note normal o MIDI de entrada): el sample a distintas alturas; C3 = el original; cada nota lo vuelve a empezar; suena entero aunque se suelte la nota. El filtro (página 1) y el LFO (página 5) actúan.
3. Flips: en el selector (filas 1-2 en cian tenue), mantener un paso con nota y tocar otro sample; Play: ese paso suena con ese sample (el paso melocotón). Clear + paso lo quita. 1-16 / 17-32 = la otra mitad.
4. Record + Play: tocar samples en el selector graba las notas con su flip.
5. **El nivel de la pista no debe moverse** al sonar los pasos con flip (van en su carril de automatización de nivel); una automatización de nivel grabada en otros pasos sigue sonando.
6. Los otros motores como antes (la envolvente sigue cerrando el VCA); el secuenciador de efectos queda una pulsación más tarde.
7. Guardar, apagar, cargar: el modo, el sample elegido y los flips vuelven.

## Verificación en emulación
- `emu_sc44_dsp.py` (frente a SC43.9): nota 60 = 32 por bloque (como se grabó), 72 = 64, 48 = 16; el sample 0 desde su inicio; TRIG `$105` = el sample 5; para al final; el VCA abierto con la envolvente a 0; sin el modo, el núcleo 0 entero igual que SC43.9 bloque a bloque (salvo `X:$38CF`, donde se guarda `n4`).
- `emu_sc44.py`: el pad 27 desde el oscilador (VA-drum, granular, muestra), ACT = 3; el selector (código 25, nota 60, flip pendiente, note-off), páginas y LEDs; flips `0x80 | s` en los 6 micropasos, Clear + paso, la otra mitad; el reproductor de carriles de stock: el nivel `0x27` sale, un flip no; el TRIG `$100 | s`; la ranura 2 del reproductor; Record + Play; fuera del modo, la vista de stock; el secuenciador de efectos con 6 pulsaciones.
