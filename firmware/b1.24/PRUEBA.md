# Beta 1.24 (B1.24) = SC43.4 = SC43.3 + sidechain por patrones, mute al compás, Clear + drum, step-drummer bipolar

`circuittracks-4486-SC43.4.syx` — SHA-256 `b888d1878f814c79ed5c2273bfdbda4b8d7f493d56f07c04109582da2d95f2e6`, marca `SC43.4`.
`firmware/b1.24/circuittracks-4486-B1.24.syx` — SHA-256 `b208d2835b7e6c31a342469746d29c784c4db989a005fc6a40c0d35fd19efd2b`: el mismo código con la marca `B1.24` (**Beta 1.24**).

- **Step-drummer de MIDI 1 / 2:** todos los destinos bipolares: par vacío = centro (64), LED tenue; el knob suma o resta al valor de la página del motor; más brillante cuanto más se aleja.
- **Sidechain desde patrones:** vista Sidechain (Shift + FX), fila 1 pads 1-4 = Synth 1 / Synth 2 / MIDI 1 / MIDI 2 como fuente del ducking de la pista elegida (la del último preset tocado), junto a los drums (pads 5-8). Cada nota del patrón de esa pista dispara la envolvente. Se guarda con el proyecto.
- **Mixer:** Shift + pad de pista (1-8) = silenciar / activar en el compás siguiente (parpadea mientras espera; otra vez lo cancela; parado, al momento).
- **Clear + botón de drum** (con su vista en pantalla): sus 8 knobs y su capa Shift por defecto.
- **Clear + K8 de drums:** también quita el bitcrush.

## Qué probar
1. MIDI 1 con un motor, step-drummer, destino FM (pad 20): knobs tenues en el centro; girar a los dos lados = más FM / menos FM.
2. Sidechain: Shift + FX, tocar un preset de Synth 2 (fila 4), pad 1 de la fila 1 (Synth 1): con un patrón de Synth 1 sonando, Synth 2 se agacha en cada nota. Pad 5-8 = vuelve a un drum. Guardar y cargar el proyecto: sigue.
3. Mixer en marcha: Shift + pad 2: parpadea y Synth 2 se silencia al empezar el compás siguiente; Shift + pad 3 dos veces = nada.
4. Drum 1: mover varios knobs (también con Shift) y Clear + botón Drum 1: todo vuelve a sus valores por defecto.
5. Drum: K8 a la izquierda (bitcrush) y Clear + K8 a la derecha: sin bitcrush.

## Verificación en emulación
- `emu_sc43_4.py`: step-drummer FM desde 64 (brillo 2, +5 = 69 a 12); sidechain: pad 1 = fuente Synth 1 (bloque en la cola), el grupo escribe `X:$3F2 = $3BF2 − $99`, una nota de patrón de Synth 1 escribe `X:$3BF2 = $F` y una de MIDI 1 nada, LEDs, pad 6 = vuelta a stock; el DSP (`dsp_session`): con `X:$3BF2 = $F` la envolvente de Synth 1 arranca (`Y:$2008` = 2) y su bit se borra; mute: parado al momento, en marcha a los 95 ticks (el compás siguiente con un tick de adelanto), parpadeo, cancelar; Clear + K8 bitcrush 15 → 0; Clear + Drum 1: decay 97 → 127, pitch 84 → 64, ring 15 → 0. También `emu_sc43_2.py`, `emu_sc43_1.py`, `emu_sc43.py`, `emu_sc42_9.py`, `emu_sc42_8.py`, `emu_sc42_7.py`, `emu_sc40_1.py`, `emu_sc40_5.py`, `emu_sc38.py` sobre SC43.4.
