# R0902S = RC0.9.1S (`R0901S`) + Synth 1 / 2 en la vista Setup

`circuittracks-4486-R0902S.syx` — SHA-256 `d313c18f6dedf23a61cd3f381c7fc25cfbbb42248856be8c9c1c3adc9ccf5b25`, marca `R0902S`.
Es **RC0.9.2S** (ficheros y marca `R0902S`).

## Arreglo: Synth 1 / 2 en la vista Setup
Desde SC19.1, pulsar Synth 1 / 2 con su vista en pantalla abre la vista de la fuente del sinte (la «segunda pulsación»). La vista Setup no cambia la vista de pista que se veía antes: si se entraba en Setup desde la vista de Synth 1 (o Synth 2), su botón llegaba a Setup como Preset y **ese sinte no se podía elegir para ver o cambiar su canal MIDI**. Ahora en Setup los botones Synth 1 / 2 eligen la pista como en el original; fuera de Setup la segunda pulsación sigue abriendo la vista de la fuente.

## Qué probar
1. Entra en Setup desde la vista de Synth 1 (o Synth 2). Pulsa Synth 1 (o Synth 2): los pads enseñan su canal y se puede cambiar.
2. Fuera de Setup: con la vista de Synth 1 en pantalla, pulsar Synth 1 otra vez sigue abriendo la vista de la fuente.

## Verificación en emulación
- `emu_setupfix.py`: en Setup, Synth 1 / 2 llegan a la vista como pistas 0 / 1 (la anterior: Preset); fuera de Setup la segunda pulsación sigue siendo Preset.

