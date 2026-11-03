# SC50.8

SC50.7 / Beta 5.10 + los programas del DSP comprimidos en la flash (`tools/dspz.py`). SHA-256 del `.syx`: `abd6d34331fc9366a789e201b2cfba73d2437a86e3aac2eeeaa2e4fe36e9a7d5`.

No cambia ninguna función: el firmware descomprime los dos programas del DSP mientras los envía al arrancar, con la ITCM (`0x2000-0x3FFF`) como ventana. Libera 21 988 B de flash para lo que venga.

1. **Arranque:** el aparato arranca como siempre, sin pausa nueva visible (la descompresión tarda unos milisegundos).
2. **Sonido:** Synth 1 / 2, drums, Master FX (Glitch, captura de sample), FX (reverb / delay) suenan igual que en la Beta 5.10.
3. **Motores del DSP propios:** MIDI 1 / 2 con oscilador, FM, modo muestra y **granular** (el granular usa el núcleo 1, que también va comprimido).
4. **Apagar y encender 2-3 veces:** arranca siempre (la ITCM vuelve con ruido en cada arranque; la ventana no depende de lo que haya).
5. Si no arranca o el DSP no suena: recuperación con Scales + Preset + Note y reinstalar la Beta 5.10. Decirme qué se ve (LEDs, si el panel responde).
