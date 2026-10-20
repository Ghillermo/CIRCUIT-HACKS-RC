# SC45.2 / Beta 3.9 = SC45.1 + la repetición de escena que suena, en la fila con Shift del Mixer

`firmware/sc45.2/circuittracks-4486-SC45.2.syx` — SHA-256 `014c09868c44566585875040e5e6da2fa992702a59f2127afeef8f46b5e36924`, marca `SC45.2`.
`firmware/b3.9/circuittracks-4486-B3.9.syx` — SHA-256 `831074dc60113f721f911221d0f0c7cb71ff270fcb085ad06ffbc9f3178bf098`, marca `B3.9` (**Beta 3.9**, el mismo código).

El usuario (2026-10-20), sobre el puerto al Circuit Rhythm: «during scene repeat, i want a led to point the current iteration inside shift view»; «port this feature back to tracks».

**Qué hace:** en el **Mixer**, con **Shift** mantenido, la fila 2 (pads 9-16) ya mostraba las repeticiones de la escena actual (amarilla, la elegida en verde). Ahora, **mientras suena una escena con 2 repeticiones o más**, el pad de la vuelta que suena se ve **blanco** (pad 9 = la primera vez, pad 10 = la segunda…) y en la **última** el pad verde **parpadea blanco / verde**. Parado, o con una escena que suena una vez, como antes. Es una función nueva: solo en la beta (las RC siguen igual).

## Qué probar
1. Mixer: guarda una escena (Shift + pad de escena) y ponla a sonar.
2. **Shift + pad 12**: 4 repeticiones (pad 12 verde con Shift).
3. Play. Mantén Shift: pad 9 blanco en la primera vuelta, el 10 en la segunda, el 11 en la tercera; en la cuarta el 12 parpadea blanco / verde; luego la escena siguiente.
4. Parado, con Shift: fila amarilla con el 12 verde, sin blanco.
5. **Shift + pad 9** (una vez): sonando, pad 9 verde sin blanco.

## Verificación en emulación
- `emu_iterled.py` frente a SC45.1 (y Beta 3.9 frente a Beta 3.8): parado = igual; sonando, repeticiones 1-3 = blanco en los pads 9-11 con el 12 verde y todo lo demás del fotograma igual; la cuarta parpadea blanco / verde; un contador fuera de rango, sin Shift y una escena de una vez = igual.
