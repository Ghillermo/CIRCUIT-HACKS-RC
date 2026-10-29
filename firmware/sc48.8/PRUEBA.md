# SC48.8 / Beta 3.44 = SC48.7 + Shift = las pistas que suenan + la vista Velocity con Shift (soltar la automatización)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc48.8/circuittracks-4486-SC48.8.syx` | `5c6f97a48a3c5bcd260093c3b500449874abb9536590acb74dc7da43b80cb0d9` | `SC48.8` |
| `firmware/b3.44/circuittracks-4486-B3.44.syx` (**Beta 3.44**) | `931ecbbf97914dd0a34dfcbc8adcb37db6c22a77604c4b071ba8a5a9f358d84f` | `B3.44` |

El usuario (2026-10-28): «When you hold shift, you can see on each channel's top pad light (white) whenever they trigger and back off when gate
is no longer held» («top pad labeled synth, midi, drum... lights on all views while shift is held»); «de-automation view (shift view in velocity
view) keeps base cyan color and is no longer yellow» («yellow on steps with automation. touching the step in this view (and only this view)
allows to preview, on yellow, the automation value on the knob. yellow goes away and knob back to normal when shift is released»; la escucha
también en el sonido). Solo en la beta por ahora.

## Qué cambia
- **Shift = las pistas que suenan** (`trigled`): con Shift mantenido, en cualquier vista, los ocho botones de pista (Synth 1 / 2, MIDI 1 / 2,
  Drum 1-4) se encienden en **blanco** mientras su pista tiene una nota sonando y se apagan cuando termina (con Shift el original los deja
  apagados). Los drums, del golpe a su note-off (en marcha, el paso siguiente).
- **Vista Velocity con Shift** (`autorel.use_v2`): los pasos conservan su color (cian…); **amarillo solo en los pasos con automatización**
  (los marcados para soltarla, en rojo). **Shift + un paso amarillo** no lo marca: pone sus valores de automatización en los knobs y en el
  sonido, como la escucha del original al mantener un paso, **hasta soltar Shift**; al soltarlo, todo vuelve a como estaba. Shift + cualquier
  otro paso lo marca / desmarca como antes.

## Qué probar
1. Shift mantenido con el secuenciador en marcha (o tocando pads, o el arpegiador): cada botón de pista blanco mientras suena su nota, apagado
   entre notas; sin Shift, como siempre. En otras vistas (Mixer, Master FX, Setup…) igual.
2. Synth 1 / 2 y MIDI 1 / 2 con notas largas: el botón sigue blanco toda la nota. Drums: un destello por golpe.
3. Vista Velocity de Synth 1 con automatización grabada en algún paso: con Shift, los pasos sin automatización con su color normal, los que
   tienen en amarillo, los marcados en rojo.
4. Parado, Shift + un paso amarillo: los knobs (y el sonido) toman sus valores; tocar otro paso amarillo, los suyos; soltar Shift: vuelven los
   de antes. Shift + un paso no amarillo: lo marca / desmarca (rojo).
5. Lo mismo en MIDI 1 / 2 con el sinte propio encendido y apagado.

## Verificación en emulación
`emu_sc48_8.py` frente a SC48.7: ALL PASS (la build anterior: con Shift todos los pasos amarillos); sobre B3.44: ALL PASS. `emu_gmdrum.py`:
el mismo fallo de LEDs que en SC48.7; `emu_autorel.py`: el amarillo en todos los pasos ya no vale.
