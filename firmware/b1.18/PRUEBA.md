# Beta 1.18 (B1.18) = SC42.8 = SC42.7 + el arpegiador de los drums

`circuittracks-4486-SC42.8.syx` — SHA-256 `ff27a337f733d486d6e44019c176fca0c92e36115be73685b9903cfcdccfa7de`, marca `SC42.8`.
`firmware/b1.18/circuittracks-4486-B1.18.syx` — SHA-256 `d8a075e3ad1f864603d96a47c9f25b7881b51411b52df3933a2e680f0159e02b`: el mismo código con la marca `B1.18` (**Beta 1.18**).

El usuario (2026-10-16): «arpeggiator en drums: mismo comportamiento, pero en vez de saltar entre notas salta entre samples», con los samples mantenidos en la vista Preset del drum.

- **Pattern Settings de un drum, con Shift:** pad 25 = arpegiador del patrón que suena encendido / apagado (verde, también sin Shift), pads 27-32 = orden (fractal, deconstruido, arriba, abajo, ping-pong, aleatorio), pads 17-24 = resolución (el mismo pad otra vez = la del drum). Se guarda con el proyecto, por drum y patrón.
- **Vista Preset del drum:** el primer sample mantenido es el de siempre; al mantener otro a la vez, ese no se elige ni suena: empieza el arpegio de los samples mantenidos (hasta 6), ordenados por número, en el orden elegido, cada uno con la velocity de su pad. En marcha va a la rejilla del drum (1/8 = cada dos pasos a 1/16…); parado, al tempo del proyecto. Sigue mientras quede alguno mantenido; al soltarlos todos el drum vuelve a su sample elegido. No se graba. Con Shift, Clear o Duplicate, o en la vista cromática, los pads son los de siempre.

## Qué probar
1. Drum 1 → Pattern Settings, Shift + pad 25 (verde), Shift + pad 29 (arriba), Shift + pad 22 (1/8).
2. Drum 1 → Preset: mantener un sample y luego otro: el drum alterna entre los dos a 1/8 (parado y en marcha). Soltar: vuelve al sample elegido.
3. Con tres o cuatro samples y otros órdenes (aleatorio, ping-pong).
4. Shift + pad 25 otra vez (apagado): mantener dos samples = como siempre.

## Verificación en emulación
- `emu_sc42_8.py`: Pattern Settings de Drum 1 (encendido, orden, resolución, LEDs; el de Synth 1 sigue siendo el de las notas); vista Preset parada: el segundo pad no llega al stock, el arpegio a 1/8 = 250 ms a 120 BPM con los samples 0, 3, 0, 3 y las velocity de sus pads; al soltar, el sample elegido y nada más; en marcha (la ranura 2 micropaso a micropaso): 1/8 = el micropaso 0 cada dos pasos, 1/32 = los micropasos 0 y 3; apagado = el stock; otra vista = terminado a los 200 ms.
