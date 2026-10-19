# SC44.6 / Beta 3.3 = SC44.5 + el filtro master apagado se queda apagado aunque se mueva su knob

`firmware/sc44.6/circuittracks-4486-SC44.6.syx` — SHA-256 `03626f2325e529e21a3da1d746a9242c4c77b8c28f0971008ad67fa108204a67`, marca `SC44.6`.
`firmware/b3.3/circuittracks-4486-B3.3.syx` — SHA-256 `d21604126d176db7a4da7e53275f40c79749612de8771ff208d8d84f98d229c2`, marca `B3.3` (**Beta 3.3**, el mismo código).

El usuario (2026-10-19): «cuando se desactiva el filtro con s25, mantener desactivado aunque se mueva. Recuperar posición actual del filtro al togglear s25 otra vez».

`mfbyp.use_hold()`: con el filtro master apagado (vista FX, **Shift + pad 25**), el DSP recibe el centro (sin filtro) haga lo que haga el knob; el knob, el MIDI o un proyecto siguen cambiando la posición guardada del filtro. **Shift + pad 25 otra vez** = el filtro vuelve en la posición actual del knob. Antes (SC44.5) mover el knob lo volvía a encender.

## Qué probar
1. Vista FX: gira el filtro master a un lado (se oye), **Shift + pad 25**: el filtro desaparece y el LED de su knob se pone rojo.
2. Gira el knob del filtro: no se oye nada distinto y el LED sigue rojo.
3. **Shift + pad 25** otra vez: el filtro vuelve donde dejaste el knob en el paso 2.
4. Apagado, cambia a otra vista (Mixer) y gira el knob: sigue apagado; al volver a la vista FX, Shift + pad 25 lo enciende en la posición nueva.
5. Lo de SC44.4 / SC44.5 sigue igual (resonancia en Shift + Octave ▲ / ▼; `firmware/sc44.4/PRUEBA.md`, `firmware/sc44.5/PRUEBA.md`).

## Verificación en emulación
- `emu_mfhold.py` en SC44.6 (frente a SC44.5) y B3.3 (frente a B3.2); `emu_fxres.py` en SC44.6.
