# S555D2 (diagnóstico) = S555D + Play en el color del culpable

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s555d2/circuittracks-4486-S555D2.syx` | `92af2ab16be780361d773a9962cafb5ce701d16c03f9b8e09f6549cfa994efba` | `S555D2` |

La Beta 5.40 con tres LEDs que dicen qué se retrasa cuando el reloj se vuelve inestable (el usuario, 2026-11-09: «Clock seems unstable,
specially when loading new FM patches or using morph with FM/custom patches»). Solo ARM: el DSP es el de la 5.40.

| LED | Qué mide | Colores |
|---|---|---|
| **Save** | El tiempo que le sobra al núcleo 0 del DSP (el peor de cada medio segundo) | verde · amarillo · ámbar · **rojo** = un bloque tardó más de lo que dura · **blanco** (2 s) = el audio se quedó sin datos |
| **Duplicate** (1 s) | El bucle principal del ARM (el que sirve el audio y el secuenciador) se paró 6 ms o más; el color = qué corría mientras | **blanco** = la tarjeta leída por el mod · **azul** = la tarjeta, por el original · **melocotón** = el propio servicio del DSP ≥ 5 ms · **naranja** = la tarea de LEDs ≥ 5 ms · **rojo** = un knob ≥ 5 ms · **verde** = un pad ≥ 5 ms · **amarillo** = ninguno de ellos |
| **Play** (0,4 s) | El tick del secuenciador llegó tarde (más de 1,5 veces su intervalo), en marcha; el color = qué corrió ≥ 5 ms (o leyó la tarjeta) entre ese tick y el anterior | los de Duplicate (**blanco** tarjeta del mod, **azul** tarjeta del original, **melocotón**, **naranja**, **rojo**, **verde** = un pad ≥ 5 ms) · **violeta** = ninguno |

Fuera de esos destellos, Duplicate y Play se ven como en la 5.40.

**Por qué S555D2** (el usuario con S555D: «play violet sometimes when loading new patches», «custom engine patches, not Nova», «card seems not involved»): en S555D Duplicate solo mira el bucle del audio; una lectura de la tarjeta o un pad largo en la tarea de los pads no lo paran y no se veían. Ahora Play dice qué retrasó el tick.

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
- `emu_s555d.py` sobre S555D2: Play verde con un pad largo, blanco con la tarjeta del mod, violeta si la marca es de antes del tick anterior.
- Pila: la tarea de LEDs igual que SC55.5 (+0 B en Synth 1 / MIDI 1, Preset y Note); un pad o un knob +8 B.
