# SC37.9 — Clear + knob: azul como el original y Master FX

`circuittracks-4486-SC37.9.syx` — SHA-256 `1960b2d484060b1a56c604d73a711bb91309fb3c23df4f37231296c2b80306b5`
Imagen de 0x65e2c bytes, CRC 0xe3cf5743, marca `SC37.9`.

Es SC37.8 con:
1. **Drums:** Clear + knob a la derecha enciende el LED en el **azul del original** (antes salía un rojo anaranjado muy tenue).
2. **Master FX:** con Clear mantenido, girar a la derecha un knob del efecto elegido lo devuelve a su valor por defecto. Mientras Clear está pulsado, esos knobs se ven **azules** si están en su valor por defecto y **rojos** si no. Girar a la izquierda no hace nada (Master FX no tiene automatización que borrar).

## Qué probar
1. Drum 1: mantén Clear y gira K2 a la derecha: LED azul y el valor vuelve al de fábrica. K3 (decay): 40 pasos a la izquierda = rojo (automatización borrada), 40 a la derecha = azul.
2. Master FX: elige un efecto (pad 1-6), mueve sus knobs, mantén Clear: los knobs movidos en rojo; gira uno a la derecha: vuelve a su valor y se pone azul. Igual con el Glitch (pad 31) y el sample (pad 7).
