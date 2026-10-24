# RC2.08 / RC2.08S = RC2.07 / RC2.07S + el teclado externo toca el sinte propio de MIDI 1 / 2

`firmware/r208/circuittracks-4486-R208.syx` — SHA-256 `18bd511f00d10fa52fc2a2e1363f15372ca5129fb9865599d1a795d278a4894d`, marca `R208` (**RC2.08**).
`firmware/r208s/circuittracks-4486-R208S.syx` — SHA-256 `5cae0ccb2d56f0a55ad2e892e46a7fbe64edba55ca9319fd6c0dc471f19cefaa`, marca `R208S` (**RC2.08S**, sin escrituras propias en la SD).

RC2.07 / RC2.07S no se publicaron: RC2.08 = RC2.06 + el arreglo de la longitud fija (RC2.07) + este.

**Arreglo** (`tools/kbin.py`; un usuario, traído por el usuario, 2026-10-24: «el teclado externo no reproduce notas en sintes MIDI (aunque sí graba)»): una nota que entra por MIDI (USB o DIN) en el canal de una pista MIDI llega al grabador y nunca al transmisor (el original no la reenvía), y el sinte propio de MIDI 1 / 2 coge sus notas en el transmisor: se grababa y no sonaba. Ahora, con el motor de esa pista encendido, la nota pasa por la cadena del transmisor (el motor, la FM, la matriz) con una marca y la cadena acaba justo antes de la salida MIDI (sin eco); un note-on con velocity 0 solo por su note-off; las inyecciones internas (loopback) no.

## Qué probar
1. MIDI 1 con el oscilador (pad 27), un teclado MIDI externo por el canal de MIDI 1 (3 de fábrica): suena el sinte propio al tocar; con Record + Play se graba como antes.
2. El sinte externo conectado a la salida MIDI no recibe esas notas dos veces (no hay eco).
3. Con el motor apagado (MIDI 1 como pista MIDI normal): igual que antes.
4. Lo tocado en los pads de MIDI 1 y lo grabado: suena y sale por MIDI como siempre.
5. Lo de RC2.07 (`firmware/r207/PRUEBA.md`) sigue igual.

## Verificación en emulación
- `emu_kbin.py` frente a RC2.07 / RC2.07S: una nota por el despachador de entrada `0x08051720` en el canal de MIDI 1 llega al motor (`c_vnon` / `c_vnoff`) y al grabador, no a la salida (`c_non` de SC06 ni `0x08029EFE`); el note-on con velocity 0, solo el note-off; MIDI 2 con el motor apagado y una inyección interna: nada nuevo; una nota de la pista (la entrada del transmisor): el motor y la salida; la marca a cero. RC2.07: el motor no la ve.
- `emu_sc46_1.py`, `emu_sc45_3.py` sobre RC2.08: bien. Imagen 0x6ff08; `kbin` en la zona libre.
