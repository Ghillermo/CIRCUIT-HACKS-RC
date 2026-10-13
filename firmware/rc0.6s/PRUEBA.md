# RC0.6S — dos arreglos sobre RC0.5S

`circuittracks-4486-RC0.6S.syx` — SHA-256 `59e3cca7142e85c5881ce59c9793a5847c854b93962510307b7179fad6f04dc9`
Imagen de 0x6447c bytes, CRC 0x06c7e0ad, marca `RC0.6S`.

Es RC0.5S con dos arreglos y nada más (tres bytes de la imagen cambian, contando la marca; el DSP es el mismo). Versión más segura: nada del mod escribe ficheros en la SD.

1. **El LFO del Auto-Filter y del Phaser arranca al activar el efecto.** Antes solo arrancaba desde la pulsación cuando el Gater se activaba en el mismo instante; si no, seguía desde un arranque anterior y el barrido empezaba en un punto que parecía aleatorio.
2. **El blanco tenue de los pads Clear es fijo.** El código de color anterior (`0x03`) es uno de los que el aparato hace pulsar; ahora es `0x02`.

## Qué probar
1. Master FX (Mixer → Mixer): pulsa el pad 2 (Auto-Filter) varias veces seguidas con algo sonando: el barrido debe empezar siempre en el mismo punto. Lo mismo con el pad 5 (Phaser).
2. Gater (pad 1) solo, y Gater + Phaser a la vez: como antes.
3. El pad 8 de Master FX sin efectos fijados: blanco tenue, sin pulsar.
4. Todo lo de `firmware/rc0.5s/PRUEBA.md`.

## Verificación en emulación
- `emu_rc0_6.py`: la imagen es RC0.5S salvo esos bytes; con los pads reales de Master FX y el reloj movido a mano, el Auto-Filter y el Phaser activados solos guardan su hora de inicio (RC0.5S: no); el Gater, igual en las dos; las palabras del cabezal y del sample no se tocan.
- `emu_sc38_5.py` sobre RC0.6S: sin cambios.
- **Sin comprobar en emulación:** cómo suena el barrido en el aparato.
