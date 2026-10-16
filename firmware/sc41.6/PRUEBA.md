# SC41.6 = SC41.5 + el patch flip solo por el canal de su pista MIDI

`circuittracks-4486-SC41.6.syx` — SHA-256 `8e7cefe75e1f38c01a1ac31db25415bb72446a3bcd90515ef0cf2cb276bf1e79`, marca `SC41.6`.
`firmware/b1.6/circuittracks-4486-B1.6.syx` — SHA-256 `4f6a13b7987172cad8220236608bd330ee2b3ee0e7f023d553786156548da28e`: el mismo código con la marca `B1.6` (**Beta 1.6**).

El usuario: «el patch flipper envía por el canal asignado a la pista MIDI, no el general».

El patch flip de MIDI 1 / 2 (pad 26 de su vista Preset) manda cada nota como Program Change **por el canal de su pista MIDI** (con PGM Tx) y, si ese canal es el de Synth 1, Synth 2 o los drums, también por dentro a esa pista. Los canales de PGM de SC41.5 no lo cambian. Lo único que se cruzaba: si el **canal de escucha** de PGM era el mismo que el de la pista MIDI, el Program Change que el flipper inyecta por dentro se reenviaba además por el **canal de salida general**. Ahora lo que llega por la inyección interna no se reenvía; sigue yendo a su pista. Un Program Change externo en el canal de escucha se reenvía como en SC41.5.

Lo demás de SC41.5 (canales de Program Change, Synth 1 / 2 en Setup): `firmware/sc41.5/PRUEBA.md`.

## Qué probar
1. Setup: canal de escucha de PGM = el canal de MIDI 1 (y de Synth 1, compartido), canal de salida = 10, PGM Tx encendido.
2. MIDI 1 en patch flip: cada nota cambia el patch de Synth 1 y sale un Program Change **solo** por el canal de MIDI 1 (nada por el 10).
3. Un Program Change externo por el canal de escucha: llega a Synth 1 y sale otra vez por el 10.

## Verificación en emulación
- `emu_pgmch_pf.py`: una nota de MIDI 1 en patch flip por el método de nota del transmisor (`0x08059FC4`): sale solo `C0 05` y va a Synth 1; sin PGM Tx no sale nada y va a Synth 1; un PC externo en el canal de escucha va a Synth 1 y se reenvía por el 10; SC41.5: el flipper salía también por el 10.
- `emu_pgmch.py` sobre SC41.6: todo lo de SC41.5 igual.
