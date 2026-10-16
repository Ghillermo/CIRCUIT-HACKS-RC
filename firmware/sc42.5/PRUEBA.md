# SC42.5 = SC42.4 + arreglos tras probarla en el aparato + Preset otra vez (drums) + sidechain de drums con los knobs

`circuittracks-4486-SC42.5.syx` — SHA-256 `fd52b1b5a04c6158d843735f782551bd9b7691caa29b4bfb6ff6cd0ac9361914`, marca `SC42.5`.
`firmware/b1.15/circuittracks-4486-B1.15.syx` — SHA-256 `7b0e0c731ac745a95bfe1eaffbcb968641bdece7a7f223f8d069cff9d4a018a9`: el mismo código con la marca `B1.15` (**Beta 1.15**).

El usuario (2026-10-16) sobre SC42.4: «arpeggiator doesn't work anymore, fixed gate won't let you select length, input length works, roller worked just once but wasn't recorded, won't work anymore, clear automation works, metronome colors are ok»; «pads 31 and 32 are lit during Gate view»; «sidechain parameter knobs on drums don't show the right color or respond»; pedidos: «preset again (in drum preset mode) enables / disables chromatic», «arpeggiator parameters keep their pattern settings color (selection still green)».

- **Arpegiador:** desde SC42.3 cada nota duraba su gate: un acorde grabado manteniendo las notas las sostenía todas hasta el final (sonaba a acorde rasgueado). Ahora cada nota dura su gate **como mucho un paso de arpegio**.
- **Colores del arpegiador:** con Shift los pads conservan sus colores de Pattern Settings; lo elegido, verde.
- **Vista Gate / Micro Step:** son el mismo objeto (Gate una vez / dos veces). Los pads 31 / 32 (y el selector) actuaban también en la vista Gate, donde son las duraciones 15 / 16. Ahora solo en la Micro Step. El selector ya no depende de los números de subvista para cerrarse. (Pad 24 = Tie y pads 25-30 = las notas del paso: de stock.)
- **Rollers:** la comprobación de «vista en pantalla» usaba subvistas equivocadas para los drums 2-4 (las de los drums van de 8 en 8: Preset 36 + 8 d, Note 37 + 8 d, Note ampliada 42 + 8 d) y los borraba en cada fotograma. Ahora se borran si su vista no se ha dibujado en 200 ms. **Con Record se graban** en el patrón.
- **Sidechain de drums (páginas de drums de la vista Sidechain):** K1-K4 = ataque, hold, decay y profundidad del drum del último preset tocado, en su color; se guardan con el proyecto; tocar un preset los devuelve a los suyos. Antes movían los valores de la última pista de notas.
- **Preset otra vez** en la vista Preset de un drum = vista cromática encendida / apagada (como Shift + Preset).
- **Knob 1 rojo al grabar en la vista cromática:** es el aviso de stock de que se graba automatización (la cromática graba el tono como automatización del knob 1).

## Qué probar
1. Arpegiador con un acorde grabado manteniendo las notas: suena arpegiado. Shift en Pattern Settings: colores de stock, lo elegido verde.
2. Gate una vez: los pads 31 / 32 eligen duración como en stock. Gate dos veces: pad 31 → selector → elegir longitud; introducir notas a mano.
3. Rollers en los drums 1-4 (Note hasta la vista con las filas 1-3 tenues); con Record, quedan grabados.
4. Sidechain (Shift + FX) con un drum: página de drums, K1-K4 mueven su ducking; LEDs del color del drum.
5. Vista Preset de un drum: Preset otra vez → cromática; otra vez → normal.

## Verificación en emulación
- `emu_sc42_5.py` (con la tarea de LEDs completa entre pasos y el reloj avanzando): arpegio de un acorde mantenido a 1/16 y 1/32 (un paso de arpegio por nota), notas cortas con su gate; la vista Gate deja los pads 31 / 32 al stock; el selector sobrevive 300 ms de tarea de LEDs y se cierra 200 ms después de otra vista; los rollers de los drums 1 y 2 sobreviven 300 ms; con Record se escriben en el patrón; Preset otra vez; sidechain de drums (K1, el manejador del grupo escribe `X:$3A11..$3A14`, un preset los devuelve); colores del arpegiador.
