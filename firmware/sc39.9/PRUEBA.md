# SC39.9 — Glitch arriba, gesto mecánico abajo; Digitise con cuatro knobs

`circuittracks-4486-SC39.9.syx` — SHA-256 `adcbaad8528adf9ebd6ea076aa9fb44e89911175eb5c1197dc97557708667dba`
Imagen de 0x68888 bytes, CRC 0xa637f83, marca `SC39.9`.

Es SC39.8 con tres cambios en Master FX (solo ARM):

## 1. Glitch y gesto mecánico intercambiados
- **Pad 6 (fila superior) = Glitch**, como un efecto más: mantener, Shift + pad = fijado, asignable a un hueco, secuenciador de efectos. Sus knobs: K1 velocidad, K2 repetición, K3 retraso, K4 caos / sobrecarga.
- **Pad 31 = gesto mecánico**: mantener = parada, soltar = arranque. Sus knobs: K1 movimiento, K2 tipo, K3 tiempo de parada, K4 tiempo de arranque. Pad 31 + un pad de la fila inferior lo asigna a ese hueco.
- **Ojo con proyectos anteriores:** traen en el pad 31 los knobs del Glitch (127, 127, 0, 0), que para el gesto son un rattle instantáneo. Gira los knobs o usa Clear + knob (valores de fábrica: 40, 0, 60, 30).

## 2. Digitise con cuatro knobs
| K1 | K2 | K3 | K4 |
|---|---|---|---|
| reducción de muestreo | reducción de bits | envío al delay mientras se mantiene (SC39.8) | **envolvente** de la cantidad de efecto |

- **K4 en el centro** (apagado): Digitise como siempre.
- **K4 a la derecha:** al activar el efecto empieza entero y se desvanece hasta quedar limpio; cuanto más a la derecha, más tarda (hasta ~4 s).
- **K4 a la izquierda:** empieza limpio y crece hasta entero.
- Los cuatro LEDs se encienden ahora (antes solo K1 y K2).

## 3. El tipo del gesto en colores
Con el pad 31 elegido, el LED de K2 cambia de color en cada tramo: blanco (tape stop → baby scratch), amarillo (baby → tear), naranja (tear → back spin), rojo (back spin → rattle), y sube de brillo a lo largo del tramo.

## Qué probar
1. Pad 6: el Glitch de siempre, ahora arriba; fíjalo con Shift; cambia un knob mientras suena.
2. Pad 31: el gesto (parada / arranque) con sus cuatro knobs; el pad se ilumina mientras dura.
3. Los dos a la vez: manda el gesto; al terminar vuelve el Glitch.
4. Digitise: K4 a la derecha y pulsa el pad 4 → se desvanece; a la izquierda → crece; en el centro → fijo. Con K3 > 0, además, el envío al delay.
5. K2 del gesto: cuatro colores, más brillo hacia el final de cada tramo.
6. Todo lo de `firmware/sc39.8/PRUEBA.md` (con los pads 6 y 31 cambiados).

## Verificación en emulación
- `emu_sc39_9.py`: pad 6 = Glitch (sus knobs, reenvío al cambiar uno, apagado al soltar); pad 31 = gesto tick a tick contra el modelo; la envolvente de Digitise en los tres casos contra las tablas; los LEDs. `emu_sc39_8.py`, `emu_sc39_6.py`, `emu_sc39_4.py` pasan sobre SC39.9.
- **Sin comprobar en emulación:** el sonido.
