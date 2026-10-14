# SC40 — el LFO del Auto-Filter y del Phaser arranca al activar el efecto

`circuittracks-4486-SC40.syx` — SHA-256 `fc2212d165a9bd98e93269bd54efcfd9d59a08c3c1fe8466f5bd596bb0e8d17c`
Imagen de 0x68888 bytes, CRC 0x6b3bdcc5, marca `SC40`.

Es SC39.9 con un arreglo en Master FX (solo ARM): el barrido del **Auto-Filter** (pads 2 / 3) y del **Phaser** (pad 5) empieza en el momento de activar el efecto. Antes solo ocurría si el Gater se activaba en el mismo instante; si no, el barrido seguía desde una fase antigua y cada pulsación empezaba en un punto distinto.

(El nombre: «SC39.10» se cortaría a «SC39.1», una build anterior.)

## Qué probar
1. Auto-Filter con una velocidad lenta: púlsalo varias veces seguidas. El barrido debe empezar siempre en el mismo punto.
2. Lo mismo con el Phaser.
3. El Gater: como antes.
4. Todo lo de `firmware/sc39.9/PRUEBA.md`.

## Verificación en emulación
- `emu_sc40.py`: la hora de inicio del conjunto del Auto-Filter y del Phaser = la del tick en que se activan (en SC39.9 no); el Gater igual en las dos; las palabras del cabezal y del sample intactas. `emu_sc39_9.py` pasa sobre SC40.
