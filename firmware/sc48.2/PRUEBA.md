# SC48.2 / Beta 3.39 = SC48.1 / Beta 3.38 + Jankó como el teclado cromático

`firmware/sc48.2/circuittracks-4486-SC48.2.syx` — SHA-256 `c2f6c512ff732584a4f981a8d9fc03a6e8c6ac5706c722074349163f7c2e4d68`, marca `SC48.2`.
`firmware/b3.39/circuittracks-4486-B3.39.syx` — SHA-256 `93e744cae7975c22475dd11809f1e349ea42f49bb5f98d23ca34399c0add51d3`, marca `B3.39` (**Beta 3.39**, el mismo código).

Un probador (traído por el usuario, 2026-10-28): en el teclado cromático de stock el pad de encima es más grave; en Jankó era más agudo. El usuario:
la disposición del probador en el pad 8, la anterior en el pad 24, la tónica en otro color, Octave: un toque = medio tono, mantenido = una octava.

## Qué probar
1. **Editor de la escala propia** (Shift + Scales). Con Shift, los pads 8 y 24 en amarillo. **Shift + pad 8** = la disposición nueva (pad 8 cian).
2. **Vista Note de una pista de notas** (tónica C en la vista Scales): fila de abajo **C D E F♯ G♯ A♯ C D**, fila de encima **B C♯ D♯ F G A B C♯**
   (medio tono más grave). **Note ampliada:** las dos filas de arriba = las dos de abajo una octava más agudas.
3. **Color de la tónica:** los pads de la tónica (C) en el color de tónica de stock; los demás en el color normal (antes, con Jankó, se veían como
   tónicas las notas repetidas). Probar otra tónica en la vista Scales.
4. **Octave ▲ / ▼:** un toque = medio tono (la tónica se mueve un pad); **mantenido medio segundo = una octava** desde donde estaba (la tónica vuelve
   a su pad); soltar antes del medio segundo = solo el medio tono. Shift + Octave sigue transponiendo el patrón una octava (stock).
5. **Shift + pad 24** en el editor = la disposición anterior (cada fila medio tono más aguda), al momento, también desde la nueva (pad 24 cian, pad
   8 apagado). El mismo pad otra vez = apagado (vuelve la escala de antes). Un proyecto guardado con Jankó en la Beta 3.37 o anterior se abre con la
   disposición anterior.
6. Tocar y grabar con las dos: las notas que suenan se encienden en su pad (y en el repetido); acordes en la Note ampliada.

## Verificación en emulación
- `emu_janko2.py` frente a SC48.1: las dos disposiciones (Note y ampliada), los enlaces de las notas repetidas, el color de la tónica (la función de
  color de stock `0x0804AD78`), Octave corto / mantenido / soltado antes, apagar; SC48.1: Shift + pad 24 no hace nada.
- `emu_cscale`, `emu_kbguard`, `emu_splitknob`, `emu_stpair`, `emu_cueclk` sobre SC48.2: bien. `emu_sc46_3` (Jankó de SC46.3 en el pad 8) no vale
  sobre SC48.2 en lo de Jankó (cuatro fallos por diseño).
