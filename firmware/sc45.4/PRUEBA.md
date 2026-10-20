# SC45.4 / Beta 3.11 = SC45.3 + random-mutate en el arpegio en vivo

`firmware/sc45.4/circuittracks-4486-SC45.4.syx` — SHA-256 `01974049305f1c94e04b00a04a33cb5b99326c0efe1fb516c68e2de973f1924a`, marca `SC45.4`.
`firmware/b3.11/circuittracks-4486-B3.11.syx` — SHA-256 `ea44e18bc816125e134be46f7a27adc6adf3934f6d15c44153e5f64cb2dc28c2`, marca `B3.11` (**Beta 3.11**, el mismo código).

El usuario (2026-10-20): «Random-mutate: afecta también al nivel en vivo». `arp.use_mutlive()`: el arpegio de las notas mantenidas pasa cada nota por el nivel de random-mutate del **paso en que está la pista** (en marcha, el que suena; parado, el paso donde se quedó). No se escribe nada. Lo demás, como SC45.3 / Beta 3.10 (`firmware/sc45.3/PRUEBA.md`).

## Qué probar
1. Synth 1 con el arpegiador encendido; pon nivel 7 de random-mutate en todos los pasos del patrón (o en el paso donde está parado). Mantén tres notas: el arpegio cambia de notas (otro grado de la escala, ± octava). Nivel 0: solo las mantenidas.
2. En marcha: el nivel sigue al paso que suena (pasos con nivel 0 = las notas tal cual).
3. Lo de SC45.3 (`firmware/sc45.3/PRUEBA.md`).

## Verificación en emulación
- `emu_sc45_3.py` sobre SC45.4: lo de SC45.3 y el arpegio en vivo (`c_arlstep` con tres notas mantenidas y la pista en el paso 6: nivel 0 = las tres, nivel 7 = otras también, en marcha (note-on del reproductor) y parado (la interfaz de notas)).
