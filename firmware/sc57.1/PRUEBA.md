# SC57.1 = SC57 + Master FX mantenido + ataque del morph

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc57.1/circuittracks-4486-SC57.1.syx` | `bec055061b2ba6611b80834beb19e92333e2a59f4bec033ca1d24a9e4f5d2745` | `SC57.1` |

**Lo nuevo** (el usuario, 2026-11-12 / 13):
- **Master FX mantenido.** En el Mixer, Mixer mantenido medio segundo o más = Master FX solo hasta soltarlo, y al soltar vuelve el Mixer; en Master FX, mantenido = el Mixer hasta soltarlo. Un toque cambia como siempre.
- **Ataque del morph al momento.** Pads 1 / 8: en Synth 1 / 2 todo el patch salta en el mismo fotograma (antes 40 parámetros por fotograma). K8 sigue marcando solo la caída; mantenidos, la envolvente se queda arriba.

## Qué probar
1. Mixer → Mixer (toque): Master FX se queda. Mixer (toque): el Mixer se queda.
2. En el Mixer, mantener Mixer un segundo: Master FX mientras lo mantienes; al soltar, el Mixer. En Master FX, mantener Mixer: el Mixer mientras lo mantienes; al soltar, Master FX.
3. Morph de Synth 1 con K7 arriba y K8 largo: el pad 1 suena de golpe y cae despacio; mantenido, se queda arriba hasta soltarlo. Con K8 corto, cae rápido.
4. Reloj y sonido estables al disparar la envolvente varias veces seguidas.

## Verificación en emulación
- `emu_mfxhold.py` (nuevo): toques, mantenido en el Mixer y en Master FX; la Beta 5.55 lo deja como un toque.
- `emu_fastatk.py` (nuevo): tras el pad 1, una pasada con 244 escrituras, luego 40; la Beta 5.55, 40.
- `emu_mzswitch.py`, `emu_morph.py --clear --sus --nocur --four --slow`, `emu_mzrr.py`, `emu_blackbox.py`, `emu_blackbox2.py`, `emu_knobhold.py`, `emu_ledstack.py`, `emu_fmmap.py`, `emu_patmut.py`.
