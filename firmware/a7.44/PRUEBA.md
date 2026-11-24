# Alpha 7.44 — prueba

Alpha 7.44 = Alpha 7.43 + `tools/mixsolo4.py` (el usuario, 2026-11-24, hoja de ruta: «un solo modo de solo en el pad 16; el flip pasa a ser un interruptor en el pad 15»; «Toggle in / out, tap 16 ends», «Held tracks invert mute»).

En el Mixer:
1. **Pad 16 tocado** = solo preparado (blanco; los mutes guardados, nada cambia). Cada pad de pista tocado después mete / saca esa pista del grupo, que suena sola; el grupo vacío = los mutes guardados (sigue preparado). **Pad 16 otra vez** = los mutes de antes, tenue.
2. **Pad 16 mantenido + pads de pista** = el grupo de nuevo (los tocados mientras se mantiene); el solo sigue al soltar.
3. **Pad 15 tocado** = flip encendido (naranja): un pad de pista mantenido invierte su mute (callada ↔ suena) mientras se mantiene. Pad 15 otra vez = apagado.
4. Solo y flip se excluyen; cargar un proyecto apaga los dos sin restaurar nada. Con Shift, la fila de repeticiones de siempre; en la página de Master FX, sus pads.

Emulación: `python tools/emu_mixsolo4.py firmware/a7.44` (23 comprobaciones).
