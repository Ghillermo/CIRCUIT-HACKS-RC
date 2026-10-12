# SC37.6 — Clear + pad para sustituir por la captura y arreglos de la revisión

`circuittracks-4486-SC37.6.syx` — SHA-256 `c761dc64417bba4c0740be470d7cc694e4f4b3eaf1632dce5666c84c579b6984`
Imagen de 0x65bdc bytes, CRC 0xfc845b31, marca `SC37.6`.

Es SC37.5 (= RC0.2) con:

1. **Sustituir un drum por la captura: Clear + pad** (dos veces: la primera pregunta y el pad parpadea en blanco; la segunda confirma). **Shift + pad vuelve a ser la selección silenciosa de stock.**
2. **Memoria de importación protegida:** si se llena la memoria donde se cargan los samples copiados de otro pack (≈ 44 s en una sesión), una copia nueva ya no pisa un sample que aún suena: no cambia nada (como cuando no cabe). Al recargar el pack se libera.
3. **Vista de la fuente del sinte protegida:** con Duplicate pulsado antes de abrir la vista de la fuente (Synth 1 / 2 otra vez), sus pads ya no copian patches.

## Qué probar
1. Vista Preset de drums: **Clear + pad** → el pad parpadea en blanco; **Clear + el mismo pad** → ese drum suena con la captura. **Shift + pad** selecciona el sample sin sonar, como el original.
2. Vista de pista de Synth 1: mantén Duplicate, pulsa Synth 1 (vista de la fuente) y toca un pad de abajo: cambia la fuente y no se copia ningún patch.
3. Vista Preset de Synth 1 normal: Duplicate + pad sigue copiando patches como en RC0.2.
