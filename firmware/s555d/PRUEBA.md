# S555D (diagnóstico) = SC55.5 / Beta 5.40 + testigos del reloj

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s555d/circuittracks-4486-S555D.syx` | `239cdebc639440fe8401e6052ade2634260aedc0e07958b2be52e5803e3f2360` | `S555D` |

La Beta 5.40 con tres LEDs que dicen qué se retrasa cuando el reloj se vuelve inestable (el usuario, 2026-11-09: «Clock seems unstable,
specially when loading new FM patches or using morph with FM/custom patches»). Solo ARM: el DSP es el de la 5.40.

| LED | Qué mide | Colores |
|---|---|---|
| **Save** | El tiempo que le sobra al núcleo 0 del DSP (el peor de cada medio segundo) | verde · amarillo · ámbar · **rojo** = un bloque tardó más de lo que dura · **blanco** (2 s) = el audio se quedó sin datos |
| **Duplicate** (1 s) | El bucle principal del ARM (el que sirve el audio y el secuenciador) se paró 6 ms o más; el color = qué corría mientras | **blanco** = la tarjeta leída por el mod · **azul** = la tarjeta, por el original · **melocotón** = el propio servicio del DSP ≥ 5 ms · **naranja** = la tarea de LEDs ≥ 5 ms · **rojo** = un knob ≥ 5 ms · **verde** = un pad ≥ 5 ms · **amarillo** = ninguno de ellos |
| **Play** violeta (0,4 s) | El tick del secuenciador llegó tarde (más de 1,5 veces su intervalo), en marcha | |

Fuera de esos destellos, Duplicate y Play se ven como en la 5.40.

## Qué probar
Con el transporte en marcha (un patrón con drums para oír el reloj):
1. Sin tocar nada, unos segundos: ¿Save verde? ¿Duplicate y Play quietos?
2. Cargar patches FM propios (vista Preset de MIDI 1 / 2) y instrumentos FM (pad 8 mantenido): ¿qué LED salta y en qué color?
3. Entrar en el morph con patches FM / propios, y moverlo (K1, LFO): lo mismo, al entrar y mientras se mueve.
4. Lo mismo con acordes largos de FM.

Dime, cuando el reloj se tambalea, el color de cada LED (o «nada»).

## Verificación en emulación
- `emu_s555d.py`: Save por el margen y blanco con el anillo vacío; Duplicate en el color de cada culpable y como la 5.40 fuera de los huecos; la
  tarjeta llamada desde el mod / desde el original; Play violeta con un tick 50 ms tarde a 120 BPM, nada parado; las envolturas vuelven a quien llama.
- `emu_morph.py --clear --sus --nocur` y `emu_pcat.py --catswap --bassblue --palfix` como SC55.5.
- Pila: la tarea de LEDs igual que SC55.5 (+0 B en Synth 1 / MIDI 1, Preset y Note); un pad o un knob +8 B.
