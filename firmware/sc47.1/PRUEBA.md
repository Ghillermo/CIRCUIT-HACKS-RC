# SC47.1 / Beta 3.28 = SC47 / Beta 3.27 + el estéreo con la ganancia real de la tira

`firmware/sc47.1/circuittracks-4486-SC47.1.syx` — SHA-256 `5ef0412627b99221170275b3ec99809c7acbef532f32b3a8d467503a8b9936d8`, marca `SC47.1`.
`firmware/b3.28/circuittracks-4486-B3.28.syx` — SHA-256 `13af7009af5785cdbcfdd46db43665f5068643d978a77cf0ff092834d11b9439`, marca `B3.28` (**Beta 3.28**, el mismo código).

El usuario (2026-10-26, en el aparato): el sample estéreo «sigue mezclando los dos samples a los dos canales por igual» y el granular con Shift + K4 «tampoco se aprecia gran diferencia». Con S469D / S469D2 leído en el aparato: la parte estéreo llegaba a la mezcla, pero unas 4,5 veces más débil que el centro. La causa: `granular_dsp.S_COEF` se midió en emulación 15 bloques después de fijar el nivel, con la rampa de nivel del mezclador al 22 % (`X:$20C` = `0x16459` frente a los `0x63FBF` del aparato: 4,49 veces). Ahora `core0_sides` toma la ganancia de la propia tira (`X:$20C` / `$24C`, lo que multiplica la entrada de MIDI 1 / 2: nivel, panorama, mute y el ducking del sidechain) × 16.

## Qué probar
1. MIDI 1 en **modo muestra**, un sample y el segundo distintos (p. ej. un bombo y una caja), **WAVE (K7 de OSC 1) a la derecha del todo**, efectos a cero: **el sample elegido solo por la izquierda y el segundo solo por la derecha** (con auriculares). A medio recorrido, abiertos a medias; a la izquierda del todo, mono.
2. El mismo patch con el **panorama** de MIDI 1 a la izquierda del todo en el Mixer: solo el sample elegido, por la izquierda; a la derecha del todo, solo el segundo, por la derecha.
3. **Mute** de MIDI 1 en el Mixer: no se oye nada de la pista (antes la parte estéreo seguía sonando bajita).
4. El **granular** con **Shift + K4** subido: los granos claramente a los dos lados; con el panorama de la pista, la proporción.
5. Lo de SC47 / Beta 3.27 (la polifonía en el oscilador y en el modo muestra) sigue igual.

## Verificación en emulación
- `emu_stripg_dsp.py` frente a SC47 / Beta 3.27, en el núcleo 0 entero con la tira **fijada en la ganancia del aparato** (`Y:$5B` / `$5C` = `0x063FC0` cada bloque; la rampa desde 0 de la emulación tarda más de 250 bloques): WAVE 0 = el primer sample igual a los dos lados (m = −25 596); WAVE 126 solo el primero = L = m, R = −1; solo el segundo = R = m, L = −1; la tira a 0 = nada (−400: el paso de rampa del propio stock); a la izquierda del todo (`Y:$5C` = 0): el primero por la izquierda, el segundo callado; el granular con todos los granos a la derecha = L = −1, R = 2 × el centro. En SC47 el primero salía L 0,61 m / R 0,39 m (el fallo del aparato), con la tira a 0 la parte estéreo seguía (12 %) y el granular ancho daba L = 0,78 × el centro.
- `emu_gstereo_dsp.py` frente a SC47 (con su rampa a medias, como antes): todo bien, y sin voz granular el núcleo 0 igual bloque a bloque.
- `emu_poly_dsp.py` frente a SC46.9: todo bien.
- `emu_smst2_dsp.py`: los 2 fallos de siempre desde SC47 (`use_smswap` cambió los lados), los mismos que en SC47.
