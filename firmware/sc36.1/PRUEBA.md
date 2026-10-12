# SC36.1 — Glitch asignable y secuenciador de efectos con la fila inferior

`circuittracks-4486-SC36.1.syx` — SHA-256 `f4cfad46d7cffda4791eb4d2c1988c01ad44ba144f32cd9bf37d4e18b4ac2ba0`
Imagen de 0x64848 bytes, CRC 0xfeeafe62, marca `SC36.1`.

Es SC36 con tres cambios que pediste:

1. **El Glitch se puede asignar como cualquier efecto de Master FX.**
   - Mantén el pad 31 y toca otro pad de la fila inferior (26-30), sin Shift. Ese hueco queda como Glitch con la copia actual de K1-K4 y se ilumina en turquesa.
   - Tocar el hueco hace sonar el Glitch con esos valores mientras lo mantienes.
2. **El secuenciador de efectos usa la fila inferior de Master FX.**
   - Cada knob (par de pasos) avanza **un valor por giro**: 0 = nada, 1-6 = los pads 26-31 (el 31 es el Glitch).
   - El LED del knob toma el **color del efecto** que tiene ese hueco. Apagado = nada; blanco tenue = hueco vacío.
   - Al sonar, carga la copia de parámetros del hueco.

3. **Sin el diagnóstico remoto por USB:** SC36.1 ya no engancha la entrada de SysEx (`rdiag`). Nada propio interviene en el protocolo USB: Components y el envío de firmware van como en el stock.

Todo lo demás es igual que en SC36: sigue su [PRUEBA.md](../sc36/PRUEBA.md) para el granular y el resto.

## Qué probar
1. **Asignar:** en Master FX, asigna efectos a los pads 26-29 (mantén el efecto de arriba y toca el de abajo). Mantén el pad 31 y toca el pad 30: el pad 30 queda turquesa. Tócalo y suena el Glitch.
2. **Secuenciador:**
   - MIDI 1: lleva el pad 27 a azul, abre el pad 30 y pon notas con Shift + pad.
   - Gira los knobs: un valor por giro, con el color del efecto de cada hueco.
   - Dale a Play: en cada paso con nota se enciende el efecto de su hueco.
3. **Que no cambia nada más.**

## Verificación en emulación
- **`emu_sc36_1.py`** comprueba:
  - asignar el Glitch (y que con Shift no se asigna);
  - el hueco con sus knobs y su color;
  - el knob a pasos de 0 a 6;
  - los huecos que pide el secuenciador;
  - que el Gater carga su copia de parámetros y el Glitch la suya, y el color de cada hueco.
- **Pruebas de SC36 sobre SC36.1:** pasan todas salvo las zonas del secuenciador de SC36, que cambian a propósito.
- **Regresiones:** SC25, SC28, SC30, SC31, SC33 (step-drummer) y el DSP de SC36.

## Volver atrás
Envía SC36 o SC35.
