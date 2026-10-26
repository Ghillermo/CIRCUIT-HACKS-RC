# SC47.7 / Beta 3.34 = SC47.6 / Beta 3.33 con los modos de voz en el orden del usuario y los mismos colores para los mismos nombres

`firmware/sc47.7/circuittracks-4486-SC47.7.syx` — SHA-256 `636989b0609301d081aea49c58af64c6182bede42f0d48da2c54d0f89ffe5471`, marca `SC47.7`.
`firmware/b3.34/circuittracks-4486-B3.34.syx` — SHA-256 `3dbba6e520ec0a49733f0c8fdb2e48d517278e13ff2b61e529fe798786843311`, marca `B3.34` (**Beta 3.34**, el mismo código).

El usuario (2026-10-26): «modes and order: retrigger … legato … glide: same as legato, but notes glide continuosuly into the next (optional param: amount) uni retrig/legato/glide: same behavior with unison. Poly: plyphony» y «añadir uni always-glide: se produce el slide aunque el gate estuviera cerrado previamente. Iguala los colores de los modos que se llaman igual».

## Qué probar
1. **Pad 32**: ocho modos en los pads 17-24: retrigger (verde), legato (amarillo), **glide** (cian), uni retrig (verde), uni legato (amarillo), uni glide (cian), **uni always-glide** (violeta), poly (magenta). Shift + pad 29 los recorre en ese orden.
2. **Glide** (pad 19): con una tecla pulsada, la siguiente se desliza a su altura sin volver a disparar el gate (K1 = la cantidad, con el desplegable abierto); una nota suelta empieza en su altura y dispara el gate.
3. **Uni legato** (pad 21): el unísono sin glide; ligado, las voces solo cambian de altura.
4. **Uni glide** (pad 22): el unísono deslizándose solo entre notas ligadas.
5. **Uni always-glide** (pad 23): el unísono se desliza siempre, también desde la última nota tras soltarlo todo.
6. Retrigger, legato, uni retrig y poly como antes; el teclado externo (sinte propio, al arpegiador con Advanced Setup pad 22) y el latch igual.

## Verificación en emulación
- `emu_vorder.py`: el orden y los colores (iguales por nombre), Shift + pad 29 en ese orden; glide (GK escrito; una nota suelta envía el salto, una ligada no, otra suelta el siguiente); uni legato (GK 0, las voces se mueven sin TRIG ni salto); uni glide (salto en una nota suelta); uni always-glide (el GK del tiempo en el DSP, sin salto, ligado solo mueve las voces); poly (GK 0).
- `emu_vmode.py`, `emu_poly3.py`, `emu_poly2.py`, `emu_glide2_dsp.py`, `emu_fmspi.py`, `emu_kbin.py` (el teclado externo llega al sinte propio; también con Record armado y en marcha), `emu_arpx.py` frente a SC47.1: bien.
