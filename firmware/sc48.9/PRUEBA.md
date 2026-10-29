# SC48.9 / Beta 3.45 = SC48.8 + la foto (Record mantenido + paso) también en Synth 1 / 2 y los drums

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc48.9/circuittracks-4486-SC48.9.syx` | `8c866052ce5af719e7f2c7f36860ccb38f72c2b97f363d977ce12842319e8320` | `SC48.9` |
| `firmware/b3.45/circuittracks-4486-B3.45.syx` (**Beta 3.45**) | `70d441dd030bd75a645268982702190b432860224c01c7bf5300c100315a0144` | `B3.45` |

El usuario (2026-10-28): «how do we save all changed parameters into automation step?», «is it the same for stock synt/drums?» → «yes»;
«mixer and fx are already stored in scenes, keep them, don't add or subtract them». La Beta 3.44 no se publicó: la 3.45 la incluye.

## Qué cambia (`tools/snapall.py`, al final de la imagen)
- **Synth 1 / 2, vista de pista (Note):** **Record mantenido + un pad de paso** (pads 1-16; con 17-32, los pasos 17-32) escribe en ese paso los
  **macros que no están donde los guarda el patch cargado** (el registro del patch leído otra vez del pack, como Clear + Synth), cada uno en su
  carril (macro m = carril m), en los 6 micropasos.
- **Drums, vista de pista (Note):** lo mismo con **pitch, decay, distorsión y EQ** que no estén en su valor por defecto (64, 127, 0, 64: los de
  Clear + knob a la derecha), carriles 0-3 del patrón del drum. Los knobs nuevos del mod no tienen carril.
- El toque del paso se traga (el paso no cambia sus notas / su golpe) y Record vuelve a como estaba al soltarlo, como en MIDI 1 / 2.

## Qué probar
1. Synth 1: carga un patch, mueve dos macros, Record mantenido + un paso: al reproducir, en ese paso los dos macros saltan a esos valores; los
   demás macros no se automatizan. Igual en la página 17-32.
2. Drum 1: sube el pitch y baja el decay, Record mantenido + un paso: ese paso los lleva; distorsión y EQ en su valor por defecto no se escriben.
3. Sin Record, los pasos hacen lo de siempre; Record solo (sin paso) arma la grabación como siempre.

## Verificación en emulación
`emu_snapall.py` frente a SC48.8: ALL PASS (la lectura del patch del pack respondida por la prueba con macros a 64). `emu_risig.py` y la foto
de MIDI 1 / 2 de `emu_p4dest.py`: bien (los tres fallos estructurales de `emu_p4dest.py` salen igual en SC48.8).
