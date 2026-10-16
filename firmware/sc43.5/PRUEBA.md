# Beta 1.25 (B1.25) = SC43.5 = SC43.4 + pitch de drums en dos partes + Clear + Synth

`circuittracks-4486-SC43.5.syx` — SHA-256 `0a1bbf9ae0085c5981695f412b658c08b6fdbc54db061c077ab1487d874d89ca`, marca `SC43.5`.
`firmware/b1.25/circuittracks-4486-B1.25.syx` — SHA-256 `745cb4ab6e537fc2739508a78b78d01354bfa71465bb20f7701e556547944784`: el mismo código con la marca `B1.25` (**Beta 1.25**).

El usuario (2026-10-17): «Keep k1 chromatic, make s+k6 continuous pitch. Stock saved pitch affects continuous pitch, not chromatic»; Clear + Synth = las macros a los valores del patch cargado: «yes».

- **K1 de drums = cromático** (semitonos; propio del mod, se guarda con el proyecto; LED tenue en el centro, más brillante cuanto más se aleja).
- **Shift + K6 = el pitch de stock**, continuo y lineal como el original; es el que se guarda en el proyecto, se automatiza y sale por CC: un proyecto de stock suena igual.
- El tono final = continuo × cromático × los cents de la vista cromática.
- **Vista cromática** (Shift + Preset): los pads fijan el cromático; ya no se graba la altura por paso.
- **Clear + K1** a la derecha = cromático al centro; **Clear + K6** a la derecha = también el continuo al centro.
- **Clear + Synth 1 / 2** (con su vista en pantalla) = sus 8 macros a los valores del patch cargado (leído del pack).

## Qué probar
1. Un drum: K1 cambia el tono a saltos de semitono; Shift + K6, de forma continua; los dos se suman.
2. Un proyecto hecho con el firmware original: los drums suenan igual que en el original.
3. Shift + Preset: los pads tocan las notas de la escala; al salir, K1 sigue donde quedó.
4. Synth 1: mover macros y Clear + Synth 1: vuelven a los del patch.

## Verificación en emulación
- `emu_sc43_5.py`: con el manejador DSP real del drum 1: neutro = la palabra de SC12 de 64; K1 + 5 = S 69 (bloque en la cola), palabra de 69; Shift + K6 + 10 = P 74, palabra × (256 + 30) / 256; LEDs; Clear + K1 / K6; un pad de la vista cromática fija S y no P; Clear + Synth 1: lee el registro de su patch y pone sus 8 macros. También `emu_sc43_2.py`, `emu_sc43_1.py`, `emu_sc43.py`, `emu_sc42_9.py`, `emu_sc42_8.py`, `emu_sc42_7.py`, `emu_k3split.py` sobre SC43.5.
