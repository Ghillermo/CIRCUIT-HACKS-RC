# SC48.3 / Beta 3.40 / RC2.11 / RC2.11S = SC48.2 / RC2.10 / RC2.10S + arreglo del editor de CC

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc48.3/circuittracks-4486-SC48.3.syx` | `fb9e7c63c50ce29066827dc1b64bcb2c75a8d86117dfb0c9e7f4e277ba4b0b53` | `SC48.3` |
| `firmware/b3.40/circuittracks-4486-B3.40.syx` (**Beta 3.40**) | `9f12501d1488723d62aece05b21f4e82acd6126e7b293d09e64061e6dc26b483` | `B3.40` |
| `firmware/r211/circuittracks-4486-R211.syx` (**RC2.11**) | `0b514ad7fa332a15a9ab342790850b7711b5c27af5d0ce87c6992ccfd4fc1dff` | `R211` |
| `firmware/r211s/circuittracks-4486-R211S.syx` (**RC2.11S**) | `d5f751b80857c3ca959f2aac40fd838f2d494772d189de42dada8fa026f7d1c5` | `R211S` |

El usuario, en el aparato (2026-10-28): «knobs 4 and 5 update fine, but all the other knobs turned leds off and stopped working»; y «after hitting
save, the view must go back to default (exit to preset view)». La copia de deshacer del editor de CC estaba en una memoria que usan otras funciones:
al descartar un cambio la plantilla recibía sus bytes y los knobs quedaban muertos. Ahora tiene su propia memoria, y al guardar se sale del editor.

**Si los knobs ya están muertos:** apaga y enciende (vuelve la plantilla guardada), salvo que guardaras después; si guardaste, vuelve a enviar la
plantilla con Components.

## Qué probar
1. MIDI 1, vista Preset, una plantilla. Pad 25 (editor), gira K1 (elige), gira más (cambia el CC). **Sal con pad 25 sin guardar** (o un botón de
   vista): los 8 knobs con su LED y mandando sus CC de antes (monitor MIDI). Repetir con K3, K6, K8.
2. Pad 25, K1 a otro CC, **pad 26 (Save)**: el editor se cierra solo y estás en la vista Preset; K1 manda el CC nuevo, en la vista Preset, en la de
   pista y en la Note. Lo mismo guardando con Octave ▼ hasta el paso de guardar y Octave ▼ otra vez.
3. Apagar y encender: K1 sigue con el CC nuevo.
4. Con el editor abierto y cambios, usar cadenas de patrones, patches del sinte propio (Preset de MIDI 1 / 2), frecuencia de pasos: nada de eso se
   reinicia (antes la copia del editor pisaba su estado).

5. **Solo SC48.3 / Beta 3.40 — 128 patches del sinte propio:** vista Preset de MIDI 1 / 2, Octave ▼ siete veces = página 8 (Octave ▼ apagado,
   Octave ▲ encendido); Clear + pad dos veces guarda ahí; cargar, apagar / encender, volver a la página 8: sigue. En la vista Preset de Synth 1 / 2
   los patches de sinte del pack siguen igual (un hueco tras el final de un banco crea patches iniciales hasta él, como antes).

## Verificación en emulación
- `emu_edscratch.py` (por el controlador, con la tarea de LEDs y el servicio del DSP entre medias) frente a SC48.2 / RC2.10 / RC2.10S / Beta 3.39:
  la copia en `0x20046B00`; tras descartar, los 8 registros como antes y K1..K8 con su CC; Save = una escritura, el editor cerrado (vista Preset),
  K1 con el CC nuevo. Las builds anteriores enseñan el fallo (B3.38: solo K4 / K5 mandan; RC2.10: K1, K2, K4).
- `emu_mp128.py` (SC48.3 / Beta 3.40) frente a SC48.2: 8 páginas, los LEDs de Octave, el hueco 127 escrito en el banco 15, registro 7; SC48.2 con 4 páginas.
