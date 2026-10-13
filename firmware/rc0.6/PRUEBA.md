# RC0.6 — dos arreglos sobre RC0.5

`circuittracks-4486-RC0.6.syx` — SHA-256 `f8b8f764972217e487f86f9c9246716d1c257690952b263632b2068dd2474df9`
Imagen de 0x66014 bytes, CRC 0x74e86342, marca `RC0.6`.

Es RC0.5 con dos arreglos y nada más (cuatro bytes de la imagen cambian, contando la marca; el DSP es el mismo).

1. **El LFO del Auto-Filter y del Phaser arranca al activar el efecto.** Antes solo arrancaba desde la pulsación cuando el Gater se activaba en el mismo instante; si no, seguía desde un arranque anterior y el barrido empezaba en un punto que parecía aleatorio.
2. **El blanco tenue de los pads Clear es fijo.** El código de color anterior (`0x03`) es uno de los que el aparato hace pulsar; ahora es `0x02` (pad 8 de Master FX y Clear en la vista de packs).

## Qué probar
1. Master FX (Mixer → Mixer): pulsa el pad 2 (Auto-Filter) varias veces seguidas con algo sonando: el barrido debe empezar siempre en el mismo punto. Lo mismo con el pad 5 (Phaser).
2. Gater (pad 1) solo, y Gater + Phaser a la vez: como antes.
3. El pad 8 de Master FX sin efectos fijados: blanco tenue, sin pulsar.
4. Vista de packs: Clear en blanco, sin pulsar.
5. Todo lo de `firmware/rc0.5/PRUEBA.md`.

## Verificación en emulación
- `emu_rc0_6.py`: la imagen es RC0.5 salvo esos bytes; con los pads reales de Master FX y el reloj movido a mano, el Auto-Filter y el Phaser activados solos guardan su hora de inicio (RC0.5: no); el Gater, igual en las dos; las palabras del cabezal y del sample no se tocan.
- `emu_sc38_5.py` sobre RC0.6: sin cambios.
- **Sin comprobar en emulación:** cómo suena el barrido en el aparato.
