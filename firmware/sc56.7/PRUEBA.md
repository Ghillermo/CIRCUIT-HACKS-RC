# SC56.7 = SC56.6 + retener knob

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc56.7/circuittracks-4486-SC56.7.syx` | `d843624df3fc381a7d1240afbaf48abea5a794b12dff93ae9fe7b62c155581dd` | `SC56.7` |

**Lo nuevo** (el usuario, 2026-11-12), `tools/knobhold.py`: **retener knob**. En la vista Setup, **Preset** lo enciende (verde) o lo apaga
(rojo tenue, de fábrica). Encendido, un knob que estás girando sigue con lo que hacía aunque cambies de vista, de pista o de página, o pulses o
sueltes Shift, hasta dejarlo quieto 1 s. Clear no se retiene; las luces de los knobs enseñan la vista nueva.

**Arreglo** (issue #22 del repositorio público): desde la Beta 5.48 el aparato se reiniciaba al abrir la vista Preset de MIDI 1 / 2 (la pila de la tarea que dibuja el panel; `fmmap` / `patmut` `use_lrram`).

## Qué probar
0. MIDI 1 → Preset y MIDI 2 → Preset nada más instalar, con el sinte propio apagado y encendido, y el mapa FM abierto: no se reinicia.
1. Setup: Preset verde / rojo tenue al pulsarlo; Shift + Preset no hace nada; apagar y encender el aparato: se conserva.
2. Apagado: todo como antes (un knob cambia de vista al momento).
3. Encendido: girar un knob en el Mixer y, sin dejar de girar, pulsar FX: sigue moviendo el nivel; quieto 1 s y otra vez: los envíos de FX.
4. Synth 1, girar un knob, pulsar Synth 2 sin parar: sigue moviendo Synth 1. Igual entre drums y entre MIDI 1 / 2.
5. Un drum, girar K1, pulsar Shift sin parar: sigue moviendo K1 sin Shift; quieto 1 s: la función con Shift. Soltar Shift a media vuelta: igual al revés.
6. MIDI 1 con el sinte propio: girar un knob y cambiar de página (pads 1-7): sigue en la página anterior. Mixer: nivel / panorama con Octave.
7. Otro knob que no estabas tocando: hace ya lo de la vista nueva.
8. Clear + knob a media vuelta: actúa al momento (no se retiene).
9. Uso normal un rato, sonando: nada se cuelga ni va más lento (la caja negra sigue en su sitio).

## Verificación en emulación
- `emu_knobhold.py`: interruptor y LED 40; apagado = como el stock; Mixer → FX a media vuelta = el Mixer, la pantalla FX y la tarea de LEDs en FX;
  < 1 s entre eventos = sigue; 1 s quieto = FX; otro knob = FX; Synth 1 → Synth 2 = Synth 1; Shift = el manejador lo ve suelto; la página del
  Mixer retenida durante la llamada y repuesta después; SC56.6 cambia al momento.
- `emu_ledstack.py`: la pila de la tarea de LEDs en la Preset de MIDI 1 ≤ 1 792 B (la 5.51: 1 840).
- `emu_fmmap.py`, `emu_patmut.py`, `emu_morph.py --clear --sus --nocur --four --slow`, `emu_blackbox.py`, `emu_notearp.py`, `emu_fwid.py` sobre la beta; `emu_gmdrum.py` da los mismos 2 fallos de diseño que la 5.51 (K1-K3 de Setup son la velocity global).
