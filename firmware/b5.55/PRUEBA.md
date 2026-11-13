# Beta 5.55 = SC57 con la marca de la beta

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.55/circuittracks-4486-B5.55.syx` | `557a0c79ec9304035c28f00f7861874bc5fde4b52bdd265a4b57a033cad46bde` | `B5.55` |

**Lo nuevo** (el usuario, 2026-11-12, tras probar la 5.54: «morph seems fixed. one change: either several morphs co-exist or enabling a new morph stops the old one»):
- **Un morph a la vez.** Con un morph sonando, mantener patches 0,4 s en la vista Preset de otra pista abre el morph de esa pista y para el anterior (su sonido se queda donde está). Antes esos patches solo se cargaban. Un toque en otra pista sigue cargando solo ese patch, y el morph que suena sigue.

## Qué probar
1. Synth 1 → Preset, mantener tres patches: morph de Synth 1. Mover K1.
2. Synth 2 → Preset, un toque a un patch: se carga; el morph de Synth 1 sigue sonando.
3. Mantener dos patches de Synth 2 medio segundo: se abre el morph de Synth 2; Synth 1 se queda donde estaba.
4. Lo mismo entre Synth y MIDI 1 / 2 (sinte propio encendido, huecos de los pads 9-24) y de MIDI a Synth.
5. Si algo se cuelga: **Caja negra… → Guardar…** sin quitar la corriente.

## Verificación en emulación
- `emu_mzswitch.py` (nuevo): Synth 1 en morph, un toque en Synth 2 no lo cambia, pads 3 / 4 de Synth 2 mantenidos 0,6 s = el morph de Synth 2; la Beta 5.54 se queda en Synth 1.
- `emu_morph.py --clear --sus --nocur --four --slow`, `emu_mzrr.py`, `emu_ledstack.py` (1 768 B).
