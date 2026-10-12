# SC37.1 — intercambio de patches de sinte entre packs

`circuittracks-4486-SC37.1.syx` — SHA-256 `b65f1a2ca15e89818bc125756a50295d46c1529562b07551c25edd5b79f9cd24`
Imagen de 0x64ff0 bytes, CRC 0x2404bcd2, marca `SC37.1`.

Es **SC37** (intercambio de samples entre packs) con dos cambios que pediste:
1. **Intercambio de patches de sinte entre packs**, con el mismo gesto.
2. Un sample o patch copiado de **otro pack parpadea en amarillo** (antes magenta, que es el color de Synth 1).

Escribe en la tarjeta SD: **haz antes una copia de la SD** y prueba con packs de prueba.

## Cómo se usa (vista Preset de Synth 1 o Synth 2)
1. En el pack del patch: **Duplicate + pad A**. Queda «copiado» aunque sueltes Duplicate o cargues otro pack. Con Duplicate pulsado parpadea en **azul**.
2. Carga el otro pack. Con Duplicate pulsado, el pad con el número de A (en su página) parpadea en **amarillo**.
3. **Duplicate + pad B**: los dos patches se intercambian entre los packs y B se vuelve a elegir, así que **suena al instante** el patch nuevo.
- En el mismo pack también funciona (intercambia A y B del pack). **Duplicate + A otra vez** cancela.
- Los patches de los 2 sintes son los mismos 128 del pack (4 páginas de 32): da igual en qué sinte copies o pegues.
- No funciona en la vista de la fuente ni en la del step-drummer del sinte.
- Las sesiones guardan su propia copia de los patches: una sesión ya guardada sigue sonando igual hasta que vuelvas a elegir el patch.

## Detalle
Cada pack guarda sus 128 patches en `Patches/00_PATCHBANK.cpb` … `15_PATCHBANK.cpb`: 8 patches por fichero, 340 bytes cada 512. El intercambio lee los dos patches y escribe cada uno en el sitio del otro, sin cambiar el tamaño de los ficheros. El aparato solo tiene en RAM los patches en uso, así que al volver a elegir B lo lee de la tarjeta.

## Qué probar
1. Pack 30, Synth 1, vista Preset: Duplicate + un patch. Carga el pack 31, Duplicate + otro patch: debe sonar el del pack 30.
2. Vuelve al pack 30 y elige el patch copiado: ahora es el antiguo del pack 31.
3. Apaga y enciende: los cambios se mantienen. Comprueba en Components que los nombres de los patches están intercambiados.
4. Intercambio de samples (SC37) en otro pack: el pad copiado parpadea en amarillo.

---

# SC37.1 — swap synth patches between packs (English)

SC37 plus **swapping synth patches between packs** and **yellow** for an item copied in another pack (Synth 1 is magenta). Synth Preset view: **Duplicate + pad A** copies patch A (it stays copied while you load another pack); in the other pack **Duplicate + pad B** swaps the two patches in their `NN_PATCHBANK.cpb` files and chooses B again, so the new patch sounds at once. Same pack works too; Duplicate + A again cancels. It writes to the SD card: back it up first.
