# Alpha 7.47 — prueba

Alpha 7.47 = Alpha 7.45 + `gmview.use_page2col()` (la 7.46 rehecha; el usuario: «Each knob gets their own column. The lit pads signal wether that knob adresses same track's k5, pan, k3 and k8»).

En la vista de macros global (Mixer + Patterns), **Octave ▲** = página 2, **Octave ▼** = página 1:
1. Página 2 = cuadrícula: **columna n = knob Kn = pista n** (K1 Synth 1 … K8 Drum 4). **Fila 1 = el K5 de la pista (corte), fila 2 = su panorama, fila 3 = su K3 (envolvente), fila 4 = su K8 (efecto).** Pad encendido (color de la pista) = ese knob mueve ese parámetro; tenue = no; un toque cambia.
2. Girar Kn mueve a la vez todo lo encendido de su columna. MIDI 1 / 2 en su página 4.
3. La cuadrícula se guarda en RAM (se mantiene al cargar proyectos; no va con el proyecto). Los enlaces de la página 1 no cambian. Ya no se leen los enlaces del formato de la 7.16.

Emulación: `python tools/emu_gmview.py firmware/a7.47/circuittracks-4486-A7.47.bin firmware/a7.47/manifest.json`.
