# A7PROT (marca `A7PROT`, prototipo) — pendiente de probar, sin publicar

= Alpha 7.07 + `tools/mixsolo3.py` (el usuario, 2026-11-19, «Make a prototype build (A7PROT)»): los pads 15 / 16 de la vista Mixer. Sustituye a `mixsolo` v2 (b.w en sus tres entradas; usa sus `c_soget` / `c_soset`).

- **Pad 16**: como antes (mantenido + pads de pista = solo fijado, blanco; un toque = los mutes de antes), pero **su flip (un toque sin solo, naranja) invierte el mute**: una pista mantenida silenciada suena y una que suena se calla mientras se mantiene; las no tocadas no cambian; al soltar vuelve.
- **Pad 15 tocado = grupo de solo** (blanco; se guardan los mutes): el primer pad de pista = solo de esa pista; los siguientes entran / salen del grupo (sacar la última = todo en silencio). **Pad 15 otra vez = los mutes de antes**, tenue.
- **Pad 15 mantenido + pads de pista = el solo flip de la Beta 5** (solo suenan las mantenidas, mientras se mantienen; la última soltada = el mixer como estaba); **al soltar el pad 15 termina** (el mixer como estaba). Mantenido con una pista no cuenta como toque. Dentro del grupo, el grupo vuelve tras el flip.
- Los modos se excluyen (entrar en uno sale del otro; los mutes guardados de un solo o grupo vuelven antes); cargar un proyecto los apaga sin restaurar. Con Shift la fila sigue siendo la de las repeticiones; en la página de Master FX, sus pads.
- Decidido por mí (el pedido no lo decía): el pad 15 tocado otra vez sale del grupo con los mutes de antes; «al soltar el 16» del pedido = el 15; un toque al 16 dentro del grupo = sale del grupo con los mutes de antes; el grupo vacío = todo en silencio.

RAM `MXR + 0x2220` (firma `SOL3`): + 4 modo (0, 1 solo, 2 mute flip, 3 grupo), + 5 mutes guardados, + 6 pad 16, + 7 pistas del mute flip, + 8 elección del solo, + 9 / + 10 flip del pad 15 (mutes de antes, pistas), + 11 pad 15, + 12 grupo.

## Probar
En el Mixer (sin Shift):
1. Pad 16 mantenido + pads 1 / 3 → solo de esas pistas, pad 16 blanco; pad 16 tocado → los mutes de antes.
2. Pad 16 tocado solo → naranja; mantén una pista que suena → se calla; mantén una silenciada → suena; las demás no cambian; al soltar vuelven.
3. Pad 15 tocado → blanco; pad 6 → solo Drum 2; pad 1 → entra Synth 1; pad 6 otra vez → sale; pad 15 tocado → los mutes de antes.
4. Pad 15 mantenido + pads → solo esas suenan mientras las mantienes; suelta el 15 → el mixer como estaba (el pad 15 no queda encendido).
5. Cargar otro proyecto con un modo puesto → los modos se apagan.

Pruebas: `emu_mixsolo3.py` (31 comprobaciones, ALL PASS); `emu_mixsolo.py` pasa; `emu_mixsolo2.py` falla en lo del flip por diseño (y en la comprobación de la carga, igual que en la 7.07); `emu_patmut.py` igual que la 7.07.
