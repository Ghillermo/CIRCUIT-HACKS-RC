# SC32 — SC31 + song pointer nuevo en Master FX

`circuittracks-4486-SC32.syx` — SHA-256 `67e23e3e418594ec3fe01cdbea853ba9a8a3dac578fefe1530b5171e7b2e3595`
Imagen de 0x61494 bytes, CRC 0xe550743b, marca `SC32`. Reserva: **SC31**. Probado en emulación; **nada probado en el aparato**.
Sin RAM nueva, sin cambios en el DSP. Es el primer paso del sample capturado (rediseño del 2026-10-08): el song pointer queda como pediste y el **pad 7 se libera** para la captura.

## Qué cambia (vista Master FX, pads 9-24 = pasos 1-16)
- **El pad 7 (modo salto) desaparece:** queda apagado y no hace nada. Será el pad de captura.
- **Un paso mantenido = retrigger:** el paso suena en el siguiente paso y se repite en cada paso mientras lo mantienes. Al soltar, la canción sigue con normalidad. Un toque corto salta una sola vez.
- **Dos pasos mantenidos = frase:** la reproducción hace bucle entre los dos (el más bajo es el inicio, da igual el orden). Al soltar cualquiera de los dos se acaba la frase; el que sigue pulsado ya no hace nada.
- **Shift + paso = inicio de frase:** mientras esperas el segundo, el bucle va del inicio al paso 16 (como antes).
- **Shift + un segundo paso = la frase queda fijada** (el más bajo es el inicio). Shift + el mismo inicio, antes de elegir el final, la quita. Shift + un paso con una frase fijada empieza una frase nueva desde ese paso.
- **Con una frase fijada el pad 9 (paso 1) se ve blanco;** tocarlo (sin Shift) quita la frase.
- Dentro de una frase fijada, los pasos mantenidos siguen funcionando (retrigger y frase momentánea); al soltar se vuelve a la frase fijada.
- El pad 8 sigue apagándolo todo, incluida la frase.
- El pad 6 sigue siendo Vinyl hasta que el reproductor del sample lo sustituya.

## Verificación en emulación
`emu_sc32.py`, por las rutas reales (pads del controlador, el tick del secuenciador enganchado, los LEDs de la vista):
- pad 7 con y sin Shift: sin cambios de estado, LED apagado;
- un paso mantenido: salta a ese paso en cada uno de los dos cambios de paso siguientes; al soltar, nada más; un toque: un solo salto;
- dos pasos (9 y 3): bucle 3..9 (del paso 10 al 3), sin retrigger; al soltar uno se acaba;
- Shift: inicio (bucle 5..16), final (5..12, del 13 al 5), pad 9 blanco, inicio nuevo, quitar con Shift + inicio, orden normalizado (10 y 4 → 4..10), Shift + paso mientras otro está pulsado;
- pasos mantenidos dentro de la frase fijada (gana la momentánea, al soltar vuelve la fijada); el pad 9 sin Shift quita la frase; sin frase el pad 9 es un retrigger normal; el pad 8 la quita.

Además, `verify_builds.py` (ALL IDENTICAL) y las pruebas de SC23.3–SC31 repetidas sobre SC32.

## Pruebas en el aparato
1. Envía SC32 y abre Master FX (Mixer dos veces) con un patrón en marcha.
2. Mantén un paso: debe repetirse mientras lo mantienes; suéltalo y la canción sigue.
3. Mantén dos pasos: bucle entre ellos; suelta uno y vuelve a la normalidad.
4. Shift + un paso, Shift + otro: la frase queda fijada y el pad 9 se ve blanco. Toca el pad 9: se quita.
5. El pad 7 debe estar apagado y no hacer nada.

## Volver atrás
Envía SC31.
