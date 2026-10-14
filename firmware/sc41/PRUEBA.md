# SC41 / Beta 1.1 — los knobs del step-drummer vuelven a funcionar

`circuittracks-4486-SC41.syx` — SHA-256 `67b8426c011be0ccdef087ac265a21c65958091527c108e1f53f32ab05325774` (marca `SC41`; «SC40.10» se cortaría a «SC40.1»).
`firmware/b1.1/circuittracks-4486-B1.1.syx` — SHA-256 `d292b8ed0ea6c196130a15e1fead3683b0bb2a0836086d020b2e47f9d8cf3720`: el mismo código con la marca `B1.1` (**Beta 1.1**).

Es SC40.9 / Beta 1.0 (ver `firmware/sc40.9/PRUEBA.md`) con un arreglo:

**Los knobs de pitch del step-drummer conservan su valor.** Desde SC36.2 (es decir, en todas las RC y betas) cada giro escribía en el par de pasos solo el incremento de ese instante (0-5) en vez de sumarlo al valor que había: el knob no avanzaba, su LED se quedaba casi apagado y el tono saltaba al mínimo. La comprobación «¿esta pista es el secuenciador de efectos?» dejaba su respuesta en el registro donde se acababa de cargar el valor del par. La página de velocity y el secuenciador de efectos no estaban afectados.

## Qué probar
1. MIDI 1 con el motor propio activado (pad 27), **pad 30** = vista del step-drummer. Pon una nota en un paso (Shift + pad).
2. Gira el knob de ese par: el LED sube y baja de brillo de forma continua y el tono del paso cambia semitono a semitono (el centro = sin cambio).
3. Octave ▲ (página de velocity): como antes.
4. Lo mismo en el step-drummer de Synth 1 / 2 (vista de la fuente, pad 30).

## Verificación en emulación
`emu_sc41.py`: knob 1 por el controlador con la vista abierta: 255 (vacío) → 69 → 74 → 71 → 127 → 0 → 0 → 1 y su LED lo sigue (la versión anterior: 5, 5, 0, 100, 0, 0, 1); el knob selector del secuenciador de efectos, igual que antes.
