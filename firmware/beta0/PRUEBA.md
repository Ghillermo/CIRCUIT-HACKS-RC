# BETA0 — versión beta

`circuittracks-4486-BETA0.syx` — SHA-256 `add68b146f2b530c3618a5ec6fa0e87a82d01431ff94041f98fc500908f7ea6c`
Imagen de 0x663d0 bytes, CRC 0x28e264a9, marca `BETA0`.

Es **SC38.7 con otro nombre** (mismo código; solo cambia la marca) = RC0.4 + funciones nuevas sin probar en el aparato. **Haz una copia de la SD antes de instalarla.**

## Qué probar
1. Todo lo de `firmware/rc0.4/PRUEBA.md`.
2. **Stretch del granular** (MIDI 1 / 2, motor granular, página 2): Shift + K6 a la derecha del todo (tercer nivel del LED); K3 = duración en pasos; con Play el tramo de K2 al final del sample dura esos pasos sin cambiar el tono (`firmware/sc38.1/PRUEBA.md`).
3. **MIDI Thru** (Advanced Setup, Duplicate): Thru (rojo tenue) → Out 2 (verde) → Merge (amarillo) → Filter (azul); Merge: el DIN In y el MIDI del aparato por el jack Thru; Filter: el DIN In sin los canales en escucha (`firmware/sc38.3/PRUEBA.md`).
4. **Clear + pad 27** (vista Preset de MIDI 1 / 2): todos los valores del motor vuelven a los iniciales; el motor no cambia (`firmware/sc38.7/PRUEBA.md`).
