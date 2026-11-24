# Alpha 7.49 — prueba

Alpha 7.49 = Alpha 7.48 + `vcf21.use_famcol()` + `novasec.use_famcol()` (el usuario: colores por familia; «Pink + violet / yellow family»).

Los LEDs de los knobs de las páginas de los sintes, por familia:
- **Envolvente** y lo que modula (ataque, decay, sustain, release, env → filtro / nivel / tono / forma / morph): **rosa** (`0x5F`).
- **LFO** y lo que modula (velocidad, LFO → filtro / nivel / tono / forma / morph): **violeta** (`0x49`).
- **VCA** amarillo (`0x2D`), **VCF** dorado (`0x6D`), **FX** limón (`0x63`).
- Sinte propio de MIDI 1 / 2: todas las páginas, las dos capas (con Shift, la misma familia); los knobs de tipo (tipo de filtro / efecto, ondas) siguen con sus colores por tipo; los de oscilador, en el color de la pista. El brillo y el tono claro de la izquierda de los bipolares, como antes.
- Synth 1 / 2, páginas de sección: VCA (envolvente 1 rosa; velocity y niveles amarillo), VCF (dorado; env 2 → frecuencia y ataque de la env 2 rosa), FX (limón), Fuentes de modulación (LFO violeta, envolvente 3 rosa); OSC, matriz y Macros como antes.

Emulación: `python tools/emu_famcol.py firmware/a7.49`, `python tools/emu_nsfam.py firmware/a7.49`.
