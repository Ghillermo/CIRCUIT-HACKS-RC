# SC37 — intercambio de samples entre packs

`circuittracks-4486-SC37.syx` — SHA-256 `e6dd8c70d334b19545d71d6c28e1f79eb4cb1b7f13e145564237f996b2e20c77`
Imagen de 0x64d10 bytes, CRC 0x1319b50c, marca `SC37`.

Es **RC0** (= SC36.2) con el intercambio de samples **entre packs** que pediste. Escribe en la tarjeta SD: **haz antes una copia de la SD** y prueba con packs de prueba.

## Cómo se usa
1. En el pack que tiene el sample: vista **Preset de drums**, mantén **Duplicate** y toca el pad del sample **A**. Queda «copiado»: mientras mantienes Duplicate parpadea en **azul**.
2. Suelta Duplicate y carga el otro pack (Projects → packs). El sample sigue copiado.
3. En el otro pack: vista Preset de drums, **Duplicate + pad B**. Mientras mantienes Duplicate, el pad con el número de A parpadea en **magenta** (es de otro pack).
4. Al tocar B se intercambian los dos ficheros: B pasa a ser el sample A del otro pack, y el otro pack recibe el B antiguo. **El nuevo B suena al instante.**

- En el mismo pack, Duplicate + A + B intercambia como en SC35; **Duplicate + A otra vez** cancela.
- Si alguno de los dos packs no tiene sitio en su memoria de samples para el sample nuevo, no cambia nada.
- Si el sample copiado ya no existe, no cambia nada.
- El sample nuevo se carga en la memoria libre del DSP (≈ 43 s en total). Si no es un WAV mono de 16 bits normal, el intercambio se hace en la tarjeta igual, pero suena cuando vuelvas a cargar el pack.
- Mientras se copian los ficheros la interfaz se para un momento (unos segundos con samples largos).

## Qué probar
1. Copia un sample corto del pack 30 (Duplicate + pad) y cárgalo en el pack 31; Duplicate + otro pad: suena el del pack 30 en ese pad.
2. Vuelve al pack 30 (cárgalo): el pad del sample copiado suena ahora como el antiguo B del pack 31.
3. Guarda, apaga y enciende: los dos packs mantienen el intercambio.
4. Duplicate + A dos veces en el mismo pack: cancelado (sin parpadeo, sin cambios).
5. Comprueba en el PC (copia de la SD) que los `PCM/NN_PCM.wav` nuevos se abren.

---

# SC37 — swap samples between packs (English)

RC0 (= SC36.2) plus **swapping samples between packs**. It writes to the SD card: back it up first. Drum Preset view: **Duplicate + pad A** copies sample A (it stays copied while you load another pack; blue while Duplicate is held); in the other pack **Duplicate + pad B** swaps the two files (the copied pad blinks magenta there) and the new B sounds at once. Same pack = the old swap; Duplicate + A again = cancel; nothing changes if either pack would run out of sample memory.
