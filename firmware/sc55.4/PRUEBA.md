# SC55.4 / Beta 5.39 — arreglo del morph de Synth 1 / 2 (Play se paraba y el aparato se reiniciaba)

= SC55.3 / Beta 5.38 + dos cambios.

- **Arreglo:** el morph de Synth 1 / 2 escribía sus parámetros desde la tarea de LEDs por el setter del firmware (hasta 40 por fotograma), y cada
  uno esperaba el semáforo del servicio del DSP (`MARK_DIRTY`): el bucle principal se quedaba parado (sin audio ni secuenciador) y el aparato
  se reiniciaba. Ahora la tarea de LEDs solo deja la posición y las escrituras se hacen en la cabeza de la cadena del servicio del DSP, que ya
  tiene el semáforo, marcando con `0x08021FDC` (la regla de siempre para ese tick).
- **Colores:** Bass y SFX se intercambian: Bass en rosa-magenta (`0x3B`), SFX en rojo (`0x53`).

Prueba:
1. Synth 1 con Play: mantener dos patches 0,4 s → la vista del morph; Play sigue, nada se reinicia; mover K1 y los demás knobs un rato.
2. Lo mismo en Synth 2 y con el transporte parado; salir con el pad 32 y volver a entrar.
3. MIDI 1 / 2 con el sinte propio: el morph como en la 5.38.
4. Vista Preset de Synth 1 / 2: los patches Bass en rosa-magenta, los SFX en rojo.
