# SC19.7 — SC19.6 con el salto instantáneo del song pointer en blanco y con repetición del paso

`circuittracks-4486-SC19.7.syx` — SHA-256 `f89a2f9efb5d77a5e2dcc9e4ae688555f5f390b797d844c71b2f7690c825fe01`
Imagen de 0x5ba98 bytes, CRC 0xe2408d6b, marca `SC19.7`.

Es **SC19.6** (SC19.5 + brillo de los knobs nuevos de drums; ver `firmware/sc19.6/PRUEBA.md`) **más** lo que pediste del modo de salto instantáneo del song pointer (vista Master FX, **pad 7**):

- **El pad 7 es blanco**: blanco tenue con el modo apagado, blanco brillante con el modo encendido (antes llevaba los colores del song pointer).
- **El paso se repite mientras el pad siga activo.** Con el pad 7 **mantenido** (modo momentáneo) o **fijado** (Shift + pad 7, vuelve a apagarse con Shift + pad 7), tocar un paso del song pointer (filas 2–3) salta a ese paso en el siguiente cambio de paso, y **en cada cambio de paso siguiente vuelve a saltar al mismo paso**: el paso suena una y otra vez. Al **soltar** el pad (o apagar el fijado) la reproducción sigue desde donde esté, sin más saltos.
- Si sueltas el pad 7 y el paso **antes** de que llegue el cambio de paso, salta una sola vez (como en SC19.6). Tocar **otro paso** mientras se repite mueve el objetivo. El **pad 8** (apagar todo) también termina el modo.

## Pruebas en el aparato
1. Flashea y enciende: debe arrancar como SC19.6.
2. Vista Master FX con el secuenciador en marcha: el pad 7 está en **blanco tenue**. Mantén el pad 7 y toca el paso 5: pasa a **blanco brillante**, salta al paso 5 y lo **repite** hasta que sueltes el pad 7; al soltarlo la canción sigue con el paso 6, 7…
3. Igual con el modo fijado: **Shift + pad 7** (blanco brillante), toca un paso: se repite sin mantener nada; toca otro paso: pasa a repetir ese; **Shift + pad 7** otra vez: se apaga y la reproducción sigue.
4. **Pad 8** con la repetición activa: todo se apaga y sigue la canción.
5. Anota si al saltar de paso en cada repetición ves (u oyes) notas cortadas o colgadas (el salto reinicia la posición de todas las pistas cada vez) o si las pistas de distinta longitud se descuadran.
6. Todo lo demás es SC19.6: ajustes guardados, retornos del Setup en el sinte, brillo de K1 / K3 / K5 / K7.

## Cómo está hecho
`build_sc17.use_jump(repeat=True, white=True)`:
- el byte `S_JT` del bloque de Master FX guarda el paso objetivo (1–16) y su bit 7 = «repitiendo»; el byte `S_JF` (bit 0 pad mantenido, bit 1 fijado) no cambia;
- `c_sptick` (gancho del tick del secuenciador), al primer tick de cada paso: con `S_JT` activo y el bit 7 puesto, si `S_JF` es 0 borra `S_JT` y no salta (la repetición termina); si no, salta al paso objetivo como antes y, si `S_JF` sigue activo, deja `S_JT = objetivo | 0x80` (si no, lo borra: salto único);
- `c_jmpled`: pad 7 = código 3 (blanco tenue, 74/74/74) / 1 (blanco brillante, 255/255/255) del conversor de colores (`build_sc17.JMP_OFF` / `JMP_ON`).

## Verificación en emulación
`tools/emu_sc19_7.py` (ruta real: pads por el controlador, tick del secuenciador 0x0802C418): LED blanco y resto de pads como SC19.6; mantenido + paso 9 → 21, 22, 23, 48..53, 48..53, 48..53; al soltar en mitad de la segunda pasada sigue 51, 52, 53, 54… sin saltos; fijado (Shift) repite hasta apagarlo; un paso nuevo mueve el objetivo; pad 8 termina el modo; un toque que acaba antes del cambio de paso salta una vez; sin modo el tick cuenta 21, 22, 23…; una marca de repetición suelta con el modo apagado se borra sin saltar. Las pruebas de SC19.6 / SC19.4 y los arneses de SC17.x sobre esta imagen.

## Volver atrás
SC19.6 (salto de un solo disparo, pad 7 con los colores del song pointer), SC19.5, SC19.4, SC17.7 (confirmada).
