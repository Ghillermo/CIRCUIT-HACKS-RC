# SC46.4 / Beta 3.21 = SC46.3 / Beta 3.20 + el DIN In mezclado en la salida USB

`firmware/sc46.4/circuittracks-4486-SC46.4.syx` — SHA-256 `3ff1a8311a3591154bb866f4a1187836733a5ec026d2e0760a1decb43f12e510`, marca `SC46.4`.
`firmware/b3.21/circuittracks-4486-B3.21.syx` — SHA-256 `41c1e50319b06417776df945e885b9e3b44328e9365b87a2ba3ff2227bc105d3`, marca `B3.21` (**Beta 3.21**, el mismo código).

**Fusión USB** (`tools/usbmerge.py`; issue #10 del repositorio público (ledlaux, 2026-10-24): «Is there a way that midi merge works when device is connected to usb? … i connect midi keyboard to CT using midi cable, i want then that device is outputting both midi combined to a computer»; el usuario: «compruébalo y si es correcto y seguro, súbelo junto a la versión»): el original nunca manda al USB lo que entra por el DIN In. Con la fusión encendida, cada mensaje corto del DIN In sale también por el puerto USB, junto al MIDI del propio aparato (así el ordenador recibe el teclado conectado por cable y el Circuit Tracks a la vez).
- **Advanced Setup, pad 23** (el original no usa los pads ahí): un toque = encendida / apagada; verde encendida, tenue apagada. Se guarda en los ajustes del aparato (bit 1 del byte de banderas del modo GM, con su firma).
- Con **Clock Tx** encendido no se copian el reloj ni el transporte del DIN In (0xF8, 0xFA, 0xFB, 0xFC): el ordenador recibiría dos relojes. Lo demás sí (notas, CC, Program Change, pitch bend, aftertouch, active sensing). El SysEx no se copia (como en Merge). Lo que entra por USB no se reenvía (sin bucles con el ordenador).
- Independiente del modo del jack Thru (Thru / Out 2 / Merge / Filter).
- **`gmdrum.use_v3()`:** K4 del modo GM cambia solo el bit 0 de ese byte (antes lo escribía entero y habría borrado la fusión).

## Qué probar
1. Un teclado MIDI en el DIN In, el Circuit Tracks por USB a un ordenador con un monitor MIDI. Advanced Setup, pad 23 (verde). Las notas del teclado llegan al ordenador junto a las del Circuit Tracks.
2. Clock Tx encendido y un reloj en el DIN In: al ordenador llega un solo reloj (el del Circuit Tracks). Clock Tx apagado: llega el del DIN In.
3. Pad 23 otra vez: ya no llegan. Apagar y encender: el ajuste se conserva.
4. Encender / apagar el modo GM (Setup, K4): la fusión sigue como estaba.
5. Lo de SC46.3 / Beta 3.20 sigue igual.

## Verificación en emulación
- `emu_usbmerge.py` frente a SC46.3: por el controlador (pad 23 de Advanced Setup), la tarea de LEDs y el post de un mensaje de entrada (el `bl` de `0x08021024`): apagada, una nota del DIN In solo a `c_thin`; encendida (las dos copias del almacén, el guardado pedido; pad 23 tenue / verde), notas y CC al puerto USB y a `c_thin`; lo del USB In no; el reloj / start con Clock Tx encendido no, apagado sí; active sensing sí; el K4 del GM conserva el bit; pad 23 otra vez = apagada. SC46.3: nada.
- Zona libre: `usbmerge` 0x8013b88..0x8013c6c.
