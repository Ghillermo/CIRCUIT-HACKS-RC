# Alpha 7.03 (marca `A7.03`) — pendiente de probar

= Alpha 7.02 + la caché de instrucciones + sitio, sin la entrada externa en Synth 1 / 2. Builder `tools/build_a7_03.py`.

- **Caché de instrucciones** (`tools/icache.py`): encendida en el arranque (S702D3 en el aparato: el arrastre del tempo con 6 voces del FM de 8 operadores desaparece).
- **Sin entrada externa en los Nova** (el usuario, 2026-11-18): en la vista de la fuente (Synth 1 / 2 dos veces) los pads 25-29 apagados y sin efecto; fuera su código ARM (`srcview`, `build_sc15` `c_h9b`) y DSP (el gancho `P:$9C3` vuelve al del stock). La captura de los retornos de FX del Setup (realimentación del VCA-VCF de MIDI 1 / 2) se queda. Pad 30 (step-drummer) y pad 32 (destinos de macros) siguen.
- **Sitio:** `morphz.use_trimnc()` (120 B de código del morph que `use_nocur` ya no ejecuta); `dspz.use_spill()` (`patrev` al final de la imagen). Libres: ≈ 369 B en el hueco 0, 128 B al final.

## Probar
1. Arranca; tempo estable con 6 voces de FM de 8 operadores.
2. Synth 1 dos veces: pads 25-29 apagados, no hacen nada; pad 30 y pad 32 funcionan.
3. Setup con los retornos en las tiras 3 / 4: la realimentación de MIDI 1 / 2 como antes.
4. Morph (2-4 patches), chain / mutate de patrones, Clear + Duplicate (patrev).

Emulación: `emu_icache.py`, `emu_nosrc.py`, `emu_nosrc_dsp.py` (núcleo 0 igual a Alpha 7.02 con modos 0 y con los retornos), `emu_morph.py --clear --sus --nocur --four --slow`, `emu_patrev.py`, `emu_patfollow.py`: pasan.
