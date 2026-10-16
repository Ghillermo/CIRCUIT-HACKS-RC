# Beta 1.19 (B1.19) = SC42.9 = SC42.8 + la grabación del arpegio de los drums

`circuittracks-4486-SC42.9.syx` — SHA-256 `a608eb5329fcb4d95e12a9f6fdc18ff235f7e55ec69a666560b64ade2cd9caf1`, marca `SC42.9`.
`firmware/b1.19/circuittracks-4486-B1.19.syx` — SHA-256 `1bfc414c9b2c1db4ba1fc9b5600b98e75aa9272ba278fc214317ea46718d2f90`: el mismo código con la marca `B1.19` (**Beta 1.19**).

El usuario (2026-10-16): «sí, graba los samples con record».

- Con el arpegiador del drum encendido, varios samples mantenidos en su vista Preset, el transporte en marcha y **Record**: cada golpe del arpegio se graba en el patrón del drum: su micropaso, su sample como **sample flip** del paso (uno por paso: si caen dos golpes en el mismo paso, queda el último) y, en un paso vacío, su velocity. En la cuenta atrás no se graba.

## Qué probar
1. Drum 1: arpegiador encendido (Pattern Settings, Shift + pad 25), Play + Record, mantener dos o tres samples en su vista Preset: al soltar, el patrón los repite con sus samples.

## Verificación en emulación
- `emu_sc42_9.py`: en marcha con Record, a 1/8 los pasos 1 y 3 con los samples 0 / 3 y las velocity de sus pads (90 / 100), el micropaso y probabilidad 7; sin Record o en la cuenta atrás nada; a 1/32 los dos micropasos del paso y un sample. `emu_sc42_8.py` sobre SC42.9: igual que en SC42.8.
