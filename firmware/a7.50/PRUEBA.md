# Alpha 7.50 — prueba

Alpha 7.50 = Alpha 7.49 + `novasec.use_v10()` + `modmx.use_famcol()` + `mixsolo.use_trim2()` (sitio).

**Synth 1 / 2, páginas de sección (el botón del sinte otra vez), como las del sinte propio:** pad 1 Macros (Shift: Macros 2), **2 OSC 1, 3 OSC 2, 4 VCA-VCF-FX, 5 Fuentes de modulación, 6 Matriz, 7 FX**, 8 nada. **Cada página con capa Shift** (Shift + knob):
- OSC 1: semitonos, cents, onda, ancho de pulso, v-sync, densidad, —, nivel osc 1 / bend, portamento, interpolación, —, —, densidad detune, —, ruido.
- OSC 2: semitonos, cents, onda, ancho de pulso, densidad, ring, v-sync, nivel osc 2 / bend, —, interpolación, —, densidad detune.
- VCA-VCF-FX: Env 1 ataque / sustain, release / decay, velocity / nivel pre-FX, Env 2 → frecuencia / tracking, frecuencia / tipo de filtro, resonancia / drive, velocidad LFO 1 / tipo de drive, distorsión / su tipo.
- Fuentes: Env 2 ADSR / Env 3 ADSR, velocidad LFO 1 / slew, onda LFO 1 / fase, velocidad LFO 2 / slew, onda LFO 2 / fase.
- FX: chorus nivel / tipo, velocidad / sync, feedback / profundidad, delay / compensación de la distorsión, EQ graves f / nivel, medios f / nivel; Shift: agudos f / nivel.
- Colores por familia (envolvente rosa, LFO violeta, VCA amarillo, VCF dorado, FX limón; osciladores en el color de la página).

**Matriz (pad 6):** K1 ranura (blanco), K2 / K3 fuente y K4 destino, **cada opción con su color y su escalón de brillo** (directo blanco, MW / AT / expresión blanco más tenue, velocity / teclado verde azulado, LFO + violeta, LFO ± violeta claro, envolventes rosa en tres escalones; destinos: tono en el color de OSC 1, v-sync en el de OSC 2, ancho de pulso blanco, niveles amarillo, filtro dorado, velocidades de LFO violeta, decays de envolvente rosa), K5 profundidad en el color del destino (derecha), su tono claro (izquierda), tenue en el centro. **Pads 9-24 = las ranuras** (1-16; con una de la 17-20 elegida, las 17-20): en uso = el color de su destino, libre blanco tenue, la elegida blanca; un toque la elige.

**Sinte propio de MIDI 1 / 2:** los destinos de la matriz (pad 6) en el color de su familia.

Emulación: `python tools/emu_ns10.py firmware/a7.50`, `emu_mixsolo5.py`, `emu_famcol.py`, `emu_gmgrid.py`, `emu_m2lanes.py`.
