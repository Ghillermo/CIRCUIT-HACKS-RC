# SC41.9 = SC41.8 + arpegiador en las pistas de notas

`circuittracks-4486-SC41.9.syx` — SHA-256 `969c40cb989564d027e9c677142b645ac9c236900be83d17f13e511c488558ae`, marca `SC41.9`.
`firmware/b1.9/circuittracks-4486-B1.9.syx` — SHA-256 `607ee35e0f0e2316001c5564c2b675a53ce3cd208d9b14340cbd3521a8b853ea`: el mismo código con la marca `B1.9` (**Beta 1.9**).

**Arpegiador** (el usuario, 2026-10-15: «sigue la dirección de pattern settings; se aplica tanto a la secuencia como a la entrada, cada vez que se tocan dos notas a la vez»; una nota por paso; Shift + 25; con Record se graba el acorde; «Shift + dirección (pads 27-32) elige el modo del arpeggiator», distinto de la dirección del patrón).
- **Pattern Settings** de Synth 1 / 2 o MIDI 1 / 2, **Shift** pulsado: **pad 25** = arpegiador del patrón que suena encendido / apagado (amarillo / verde); **pads 27-32** = orden: fractal, deconstruido, arriba, abajo, ping-pong, aleatorio (el elegido verde, los demás amarillos). Sin Shift, el pad 25 se ve verde mientras está encendido y sigue abriendo el modo 2.
- **Secuencia:** dos notas o más que empiezan en un paso suenan una por paso (sync rate del patrón), ordenadas por altura y en el orden elegido, mientras dura la nota más larga; cada una dura un paso, con su velocity. El random-mutate y las dinámicas del paso no se aplican a ellas.
- **Entrada:** la primera nota suena como siempre; al mantener otra, arpegio de las mantenidas, una por paso (en marcha, en el micropaso 0 de la pista; parado, al tempo del proyecto y el sync rate de la pista) hasta soltarlas todas. Con Record se graba el acorde.
- Se guarda con el proyecto (bloque `ARP1` con suma en la cola del registro), por pista y patrón.

## Qué probar
1. Synth 1, Pattern Settings, Shift pulsado: el pad 25 amarillo, el 29 verde y 27, 28, 30-32 amarillos. Shift + 25: verde. Soltar Shift: el 25 sigue verde.
2. Un acorde de 3 notas de 4 pasos en el patrón: suena una nota por paso, de la grave a la aguda. Shift + 30: de la aguda a la grave; Shift + 31: ping-pong; Shift + 27 / 28: fractal / deconstruido; Shift + 32: aleatorio.
3. Shift + 25 otra vez: el acorde vuelve a sonar entero.
4. Parado, en la vista Note: una nota suena normal; mantener otra: arpegio al tempo del proyecto; soltar todas: para. Lo mismo en marcha (a tempo con la secuencia).
5. Record + Play, mantener un acorde: se graba el acorde (no las notas sueltas); al reproducir, la secuencia lo arpegia.
6. Guardar, apagar, cargar: el arpegiador y su orden vuelven. MIDI 1 / 2 igual (también con el motor propio).

## Verificación en emulación
- `emu_arp.py`: la vista por el controlador (Shift + 25 / 27-32, colores, pad 25 sin Shift = modo 2); la secuencia con el reproductor de Synth 1 tick a tick por las llamadas de stock (`0x0804A684` / `0x0804A714`): apagado = las tres notas de stock a la vez; arriba, abajo, ping-pong, fractal, deconstruido, un acorde en el micropaso 2, una nota sola; la entrada por los pads de la vista Note (la primera nota normal, la segunda al grabador, el arpegio desde la tarea de LEDs cada 125 ms a 120 BPM, soltar, en marcha por el micropaso 0); la carga de stock pone a cero el estado; un bloque sin firma = apagado.
