# Beta 1.21 (B1.21) = SC43.1 = SC43 + note-off de los golpes parados de rollers y arpegio de drums

`circuittracks-4486-SC43.1.syx` — SHA-256 `c1eda34f42968c272943f386032344b1e1829bbcb882d8429023b7578ffc4c9f`, marca `SC43.1`.
`firmware/b1.21/circuittracks-4486-B1.21.syx` — SHA-256 `094557f4f6a577204c7061554136fac2f5b285c641316aa3788356401e6e31c0`: el mismo código con la marca `B1.21` (**Beta 1.21**).

El usuario (2026-10-16): «en el roller, la fila inferior se ve parcialmente blanca (pads 27 al 30)».

- El stock pinta en **blanco** los dos cuadros de un drum en la vista Note mientras su nota suena (del note-on al note-off). Los golpes de los rollers y del arpegio de drums **con el transporte parado** no mandaban el note-off: el último se quedaba en blanco (y la nota MIDI del drum, colgada). Pads 27-30 = los drums 1 y 2 en sus dos copias.
- Ahora cada uno de esos golpes se suelta **100 ms** después (o antes, si llega el siguiente golpe del mismo drum). En marcha no cambia nada: el note-off lo manda el secuenciador.

## Qué probar
1. Parado, vista Note de los drums: mantener rollers de los drums 1 y 2 y soltarlos: los cuadros de abajo parpadean en blanco con cada golpe y al soltar vuelven a su color.
2. Parado, arpegio de drums (Pattern Settings: Shift + pad 25; vista Preset: dos pads mantenidos) y soltarlo: igual en la vista Note.
3. Con un aparato MIDI escuchando el canal de drums: ninguna nota se queda colgada.
4. En marcha, rollers y patrón normal: como en Beta 1.20.

## Verificación en emulación
- `emu_sc43_1.py`: con el note-on / note-off reales, un roller del drum 1 mantenido parado pinta sus cuadros (pads 28 / 29) en blanco; cada golpe recibe su note-off 100 ms después; al soltar vuelven a `0x45` y el drum no suena (con SC43: blanco para siempre, el último golpe sin note-off); en marcha una hora pendiente se descarta sin note-off; el arpegio del drum 1 parado (1/8): cada golpe con su note-off a los 100 ms. También `emu_sc43.py`, `emu_sc42_9.py`, `emu_sc42_8.py`, `emu_sc42_7.py` sobre SC43.1.
