# RC2.02 / RC2.02S (R202 / R202S) = SC44.3 = Beta 3.0 como versión candidata

`firmware/r202/circuittracks-4486-R202.syx` — SHA-256 `b845b267d0e06fdcfa3b20c417d5307416bf53cfefcb3313fa1d450c18e71912`, marca `R202` (**RC2.02**).
`firmware/r202s/circuittracks-4486-R202S.syx` — SHA-256 `234d862b3a246256688b36ff7e15dbf36b21d4d7e9842c4de73a3e162509cf5f`, marca `R202S` (**RC2.02S**: + toda escritura o borrado del mod en la tarjeta rechazados, como RC2.01S).

El usuario (2026-10-18): «Upload to RC2.xx and RC2.xxS» · «publica rc y pasa la nota al readme».

- **RC2.02** = el mismo código que SC44.3 / Beta 3.0 con la marca de la versión candidata: RC2.01 + la **matriz de modulación** del sinte propio de MIDI 1 / 2 (pad 6), el **teclado partido con cualquier par** de Synth 1, Synth 2, MIDI 1, MIDI 2, el **LFO** con triángulo por defecto y **sample & hold suavizado** (también en el LFO 2 de la matriz) y el código del ARM compactado. La Beta 3.0 no se publicó por separado.
- **RC2.02S** = RC2.02 + `rodisk.use_allpacks()`, como RC2.01S.

## Qué probar
1. Lo de `firmware/sc44.2/PRUEBA.md` y `firmware/sc44.3/PRUEBA.md` (matriz de modulación, teclado partido, formas del LFO).
2. Lo de RC2.01 sigue igual (`firmware/r201/PRUEBA.md`).
3. RC2.02S: lo de `firmware/rc2s/PRUEBA.md` (guardar un patch propio, copiar proyectos, borrar packs: LED de Save rojo, nada escrito).

## Verificación en emulación
- `emu_sc44_3.py`, `emu_sc44_2.py`, `emu_sc44.py`, `emu_rodisk.py` en R202 / R202S.
