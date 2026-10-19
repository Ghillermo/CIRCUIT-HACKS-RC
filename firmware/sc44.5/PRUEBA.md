# SC44.5 / Beta 3.2 = SC44.4 + filtro master apagado / encendido en Shift + pad 25

`firmware/sc44.5/circuittracks-4486-SC44.5.syx` — SHA-256 `76767dd37735e127b110550572a779f47c4ca4b6fd9c8070b716779bfb9c122f`, marca `SC44.5`.
`firmware/b3.2/circuittracks-4486-B3.2.syx` — SHA-256 `64cd1db79baf713ec779dc0138205f08813eeec44767e8789aec174e7f761197`, marca `B3.2` (**Beta 3.2**, el mismo código).

El usuario (2026-10-19): «add shift25 on FX view: master filter disable/enable».

`tools/mfbyp.py`: en la **vista FX**, **Shift + pad 25** apaga el filtro master (lo lleva al centro y guarda dónde estaba) y, otra vez, lo enciende (la posición vuelve). Mientras está apagado el LED del knob del filtro master se ve **rojo**, en cualquier vista. Con Shift pulsado en la vista FX el pad 25 está **amarillo** (encendido) o **rojo** (apagado). Mover el knob del filtro con el filtro apagado lo vuelve a encender desde ahí. Sin Shift el pad 25 hace lo de stock. Incluye lo de SC44.4 (resonancia en Shift + Octave ▲ / ▼).

## Qué probar
1. Gira el filtro master a un lado (que se oiga). Vista FX, Shift + pad 25: el sonido queda sin filtro y el LED del knob del filtro se pone rojo.
2. Shift + pad 25 otra vez: el filtro vuelve donde estaba; el LED del knob, como siempre.
3. Con Shift pulsado en la vista FX: pad 25 amarillo (encendido) / rojo (apagado).
4. Apagado, cambia de vista: el LED del knob sigue rojo. Gira el knob del filtro: se enciende desde ahí (el LED deja el rojo).
5. Sin Shift, el pad 25 de la vista FX hace lo de siempre; Shift + pad 25 en otras vistas, lo de siempre.
6. La resonancia en Shift + Octave ▲ / ▼ (SC44.4) sigue igual.

## Verificación en emulación
- `emu_mfbyp.py` en SC44.5 (frente a SC44.4) y B3.2 (frente a B3.1); `emu_fxres.py` en SC44.5.
