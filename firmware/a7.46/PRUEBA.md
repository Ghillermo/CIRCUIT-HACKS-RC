# Alpha 7.46 — prueba

Alpha 7.46 = Alpha 7.45 + `gmview.use_page2()` (hoja de ruta: «segunda página de la vista de macros global»; el usuario: «One page, pads pick»).

En la vista de macros global (Mixer + Patterns):
1. **Octave ▲** = página 2 (Octave ▼ encendido = el camino de vuelta); **Octave ▼** = página 1 (Octave ▲ encendido).
2. Página 2: **knob Kn = la pista n** (K1 Synth 1 … K8 Drum 4), en el color de su pista. **Pads 1-4** eligen qué mueven: 1 = el K5 de la pista (corte), 2 = su panorama (la página de panoramas del Mixer), 3 = su K3 (envolvente), 4 = su K8 (efecto). El elegido blanco, los otros tres tenues, el resto apagados y sin efecto. MIDI 1 / 2 en su página 4 (como en la página 1).
3. Abrir la vista = página 1. Los enlaces de la página 1 no cambian.

Emulación: `python tools/emu_gmview.py firmware/a7.46/circuittracks-4486-A7.46.bin firmware/a7.46/manifest.json`.
