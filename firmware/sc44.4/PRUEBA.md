# SC44.4 / Beta 3.1 = SC44.3 + resonancia del filtro master en Shift + Octave

`firmware/sc44.4/circuittracks-4486-SC44.4.syx` — SHA-256 `f2d3fe749737ce5ebfcbd51d4235c2cd5f819f6cf5b655d6d1edb4cdc170f128`, marca `SC44.4`.
`firmware/b3.1/circuittracks-4486-B3.1.syx` — SHA-256 `bdc4b21b61409510c91c2e385c46add3f3b8a5445c513eb8c2037bdf82fb0665`, marca `B3.1` (**Beta 3.1**, el mismo código).

El usuario (2026-10-19): «cambia master reso a shift+octave up/down, saltos de 16 en 16» · «sin ciclar en max/min».

`tools/fxres.py`: en la **vista FX**, **Shift + Octave ▲** = resonancia del filtro master + 16 (se para en 127), **Shift + Octave ▼** = − 16 (se para en 0). Sin Shift, Octave ▲ / ▼ siguen eligiendo los envíos de delay / reverb. El botón **1-16 / 17-32** vuelve a hacer lo de stock (antes subía la resonancia de 32 en 32 y volvía a 0) y ya no se enciende en verde. Con Shift, Octave ▲ / ▼ se encienden en amarillo.

## Qué probar
1. Vista FX, Shift + Octave ▲ varias veces: la resonancia del filtro master sube (se oye con el filtro master girado); tras 8 pulsaciones desde 0 está al máximo y más pulsaciones no hacen nada.
2. Shift + Octave ▼: baja de 16 en 16 hasta 0 y se queda ahí.
3. Sin Shift: Octave ▲ / ▼ = envíos de delay / reverb, como antes; la resonancia no cambia.
4. Con Shift pulsado en la vista FX: Octave ▲ / ▼ amarillos. 1-16 / 17-32 ya no está en verde ni toca la resonancia.
5. Fuera de la vista FX (Patterns: Shift + Octave = cadenas de patrones; el resto) todo igual que en SC44.3.

## Verificación en emulación
- `emu_fxres.py` en SC44.4 y B3.1 (frente a SC44.3 fuera de la vista FX), `emu_sc44_3.py` en SC44.4.
