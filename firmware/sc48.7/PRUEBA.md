# SC48.7 = SC48.6 + sin editor de CC con el sinte propio encendido (issue #15) + dos arreglos del pad 31

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc48.7/circuittracks-4486-SC48.7.syx` | `b32e9f881678e5f9941f80a9adf7ccdbaf244cf69026e48a0b3d8d47db38e8f6` | `SC48.7` |

El usuario (2026-10-28), tras ver el vídeo de ledlaux en la issue #15 (MIDI 2 con el sinte propio encendido, K1 en el editor de CC):
«CC re-assign cannot be used during voice modes», «Instead, knobs send their assigned custom CC and NRPNs», «The re-assign view pad is off
when a voice is being used», «Unavailable pads are off (no light at all) use that, extend to other unavailable settings».

## Qué cambia
- **`vcf21.use_edlock()`**: con el sinte propio de la pista encendido, sus knobs mandan el mapa de CC / NRPN del sinte propio (K1 = CC 73…),
  nunca los de la plantilla; el editor de CC (que edita la plantilla) queda cerrado: **pad 25 apagado** (sin luz) y un toque no hace nada. Un
  editor abierto cuando se enciende el sinte propio se cierra en el siguiente fotograma (los cambios sin guardar se descartan). Con el sinte
  propio apagado, igual que antes.
- **`vcf21.use_vellock()`** (arreglo): el **pad 31** de la vista Preset (velocity → envolventes del VA-drum) estaba encendido y se podía
  pulsar en el **secuenciador de efectos**, y un toque pasaba el motor al **modo muestra**; ahora solo con el VA-drum (oscilador + su bit):
  apagado y sin efecto en los demás motores.
- **`modesel.use_vdfix()`** (arreglo): el VA-drum con el pad 31 encendido se veía en la fila de motores como **granular**; ahora como VA-drum.

## Qué probar
1. MIDI 1 / 2, vista Preset, motor apagado: pad 25 encendido; abre el editor, cambia un CC, guarda: el knob manda el CC nuevo.
2. Con un motor (oscilador, VA-drum, granular, muestra, FX, FM): pad 25 apagado y sin efecto; los knobs mandan los CC del sinte propio.
3. Editor abierto, elegir un motor en la fila del pad 27: el editor se cierra.
4. Secuenciador de efectos: pad 31 apagado; pulsarlo no cambia el motor. VA-drum: pad 31 tenue / brillante; con él encendido, la fila de
   motores marca el VA-drum.

## Verificación en emulación
`emu_edlock.py` frente a SC48.6: ALL PASS (la build anterior enseña los tres fallos).
