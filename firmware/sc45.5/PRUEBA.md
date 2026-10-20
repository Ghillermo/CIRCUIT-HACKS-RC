# SC45.5 / Beta 3.12 = SC45.4 + supersaw y triángulo exponencial

`firmware/sc45.5/circuittracks-4486-SC45.5.syx` — SHA-256 `42c812a64c041577ae4d85fd4f8e2ab419e749e113c99eee56dd4dfbf613aa01`, marca `SC45.5`.
`firmware/b3.12/circuittracks-4486-B3.12.syx` — SHA-256 `55ece086fb6fb614caf7c09bbeeed8af91a9224911080cfbbc299aa46fe5c00e`, marca `B3.12` (**Beta 3.12**, el mismo código).

El usuario (2026-10-20): «Cambia el control de sierra a normal-supersaw»; el triángulo con una curva a la izquierda del centro. Elegido: todo el recorrido del knob, 7 sierras, curva exponencial.

En el motor de MIDI 1 / 2 (página 2, OSC 1; igual SHAPE 2 en el OSC 2):
- **Sierra (WAVE 84):** SHAPE a la izquierda del todo = una sierra normal; hacia la derecha entran 6 sierras desafinadas alrededor de la central, cada vez más fuertes y más separadas; a la derecha del todo, la supersaw entera. El centro del knob ya es media supersaw. La envolvente y el LFO de SHAPE la mueven como antes.
- **Triángulo (WAVE 42):** a la izquierda del centro, las rampas se curvan (exponencial): picos afilados y valles anchos, más armónicos. El centro y la derecha (wavefold) como antes.
- El seno y la cuadrada no cambian. Lo demás, como SC45.4 / Beta 3.11 (`firmware/sc45.4/PRUEBA.md`).

## Qué probar
1. MIDI 1 con el oscilador, WAVE en la sierra (84). SHAPE a la izquierda del todo: sierra limpia. Ve girando a la derecha: se ensancha y «desafina» (coro); a la derecha del todo, la supersaw gruesa.
2. Con dos osciladores (pad 28), la sierra en los dos: los dos con supersaw; el sync suave y el FM siguen funcionando.
3. WAVE en el triángulo (42), SHAPE a la izquierda del centro: más brillante, picos afilados; a la derecha del centro, el wavefold de siempre.
4. Las dos pistas MIDI con dos osciladores en supersaw y muchas cosas sonando: sin cortes ni ralentización del audio (cuesta ≈ 4 % del núcleo 0 del DSP en el peor caso).
5. El seno y la cuadrada suenan como en SC45.4.

## Verificación en emulación
- `emu_sc45_5_dsp.py` en SC45.5 (frente a SC45.4) y B3.12 (frente a B3.11); `emu_sc45_3.py` en las dos.
