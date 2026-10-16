# SC42.4 = SC42.3 + rollers de micropasos (drums), Clear lavanda / rojo y borrado de automatización del sinte propio

`circuittracks-4486-SC42.4.syx` — SHA-256 `b282b80ebc629a6763985931180d8857139ca216ef8badb68fb08776efb8195a`, marca `SC42.4`.
`firmware/b1.14/circuittracks-4486-B1.14.syx` — SHA-256 `035215e7584c0eb86a4106955f5437caaca86a29d9e3b93eba48bdb7393145e8`: el mismo código con la marca `B1.14` (**Beta 1.14**).

Pedidos del usuario (2026-10-16):
- **Rollers de micropasos** en las filas 1-3 de la vista Note de los drums (Drum + Note): cada columna es el drum de su cuadro de abajo (con la copia en espejo: columnas 1-4 = drums 4-1, 5-8 = drums 1-4; «follow the mirrored columns»), tenue en su color; la columna izquierda de un drum = micropasos 1-3 (filas 1-3), la derecha = 4-6 (drum 1 = pads 4, 12, 20 y 5, 13, 21). **Mientras se mantienen**, con el transporte en marcha, el drum suena en cada paso en esos micropasos (velocity del paso, 100 si está vacío); varios a la vez se combinan; en directo, no se graban.
- **Clear + knob:** a la derecha = valor por defecto con el LED **lavanda** (el color de stock, `0x07`); a la izquierda = **borrar la automatización** (LED **rojo**). En el **sinte propio de MIDI 1 / 2** el borrado de automatización es nuevo (los carriles del knob, con y sin Shift, en el patrón que suena; la misma rutina de stock que usan Synth 1 / 2). En **Master FX**, con Clear pulsado, solo se ven lavanda los knobs en su valor por defecto (sin rojo: no hay automatización).

## Qué probar
1. Drum 1, Note: filas 1-3 tenues en los colores de las columnas. Play, mantener el pad 4 (drum 1, micropaso 1) y el 13 (micropaso 5): el drum 1 suena dos veces por paso. Soltar: para.
2. Varios drums a la vez; un paso que ya tiene golpe: no se duplica en su micropaso.
3. MIDI 1 con el motor propio: grabar automatización de un knob (p. ej. el de FILT), Clear + ese knob a la izquierda → rojo y la automatización desaparece; a la derecha → lavanda y el valor por defecto.
4. Master FX: Clear pulsado → solo lavanda en los knobs en su valor por defecto; a la derecha los devuelve.

## Verificación en emulación
- `emu_sc42_4.py`: los colores de los rollers y su máscara por la vista real; la ranura 2 del reproductor de drums (un paso vacío con los rollers 1 y 3 = dos golpes de velocity 100; un paso con golpe en el micropaso 0 = el de stock y el nuestro en el 2; el drum 2 no se entera); otra vista los borra; Clear + knob del motor de MIDI 1 a la izquierda = la rutina de stock `0x0803D3B8` en el editor de MIDI 1 con su carril, el valor se queda, rojo; a la derecha = valor por defecto, lavanda; un knob sin carril no borra nada.
