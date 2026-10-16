# Beta 1.22 (B1.22) = SC43.2 = SC43.1 + note-off del grabador para las notas del arpegiador

`circuittracks-4486-SC43.2.syx` — SHA-256 `94f1aca87a3901fea711be7b1f8b320e6d8c75963c10ad1e12eb9380a318cff9`, marca `SC43.2`.
`firmware/b1.22/circuittracks-4486-B1.22.syx` — SHA-256 `d89ecf65ff3e0619d97151d6d914457fbc9f8c92907cf431a3ce9b5055a9328a`: el mismo código con la marca `B1.22` (**Beta 1.22**).

El usuario (2026-10-16): «al grabar un patrón con arpegiador de 32 pasos, sólo se aplica el arpegiador a la página donde se pulsó grabar … grabar una segunda vez pulsando record en la página que falta sí que aplica el arpegiador, pero solo a las notas nuevas».

- La segunda nota de un acorde (y las siguientes) llegaba al grabador pero nunca su note-off: el grabador la daba por mantenida y la ignoraba cuando se volvía a tocar, hasta pulsar Record otra vez. Por eso los acordes de la segunda página se grababan solo con su primera nota (sin acorde no hay arpegio).
- Ahora al soltar esas notas el grabador recibe también su note-off.
- Incluye Beta 1.21 (rollers y arpegio de drums parados: sus cuadros ya no se quedan en blanco).

## Qué probar
1. Synth 1, patrón de 32 pasos, arpegiador encendido (Pattern Settings: Shift + pad 25). Record + Play, tocar el mismo acorde en la página 1 y en la página 2. Parar y escuchar: los acordes de las dos páginas se arpegian.
2. Varios acordes distintos y repetidos en una sola pasada: todos quedan grabados con todas sus notas.
3. Sin arpegiador: grabar acordes como siempre.

## Verificación en emulación
- `emu_sc43_2.py`: con el tick real del secuenciador, el grabador real y Record / Play por el controlador, un acorde de dos pads en el paso 3 y otra vez en el 19 de un patrón de 32 pasos: la segunda nota recibe el note-off del grabador al soltarla (pasos 5 y 21), su entrada queda soltada y el grabador la vuelve a tomar en el paso 19 (con SC43.1: mantenida para siempre, ignorada en el 19); ningún note-off nuestro para la primera nota. También `emu_sc43_1.py`, `emu_sc43.py`, `emu_sc42_9.py`, `emu_sc42_8.py`, `emu_arp.py`, `emu_arprate.py` sobre SC43.2.
