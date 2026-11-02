# RC4.05 / RC4.05S = RC4.04 / RC4.04S + los tres modos del LFO que no sonaban + el pad 23 tenue

| SHA-256 del `.syx` | Marca |
|---|---|
| `fb8b3ee77d4a61bab94d5c87ca13af745fc01a30a2481ced908d15d03c69b78a` | `R405` |
| `431243629211d6eaa4182d0692e478763cfa494a8d0c6c570000481ee56c8a0b` | `R405S` |

- `vcf21_dsp.use_actfix()`: con las formas seno, sample & hold y sample & hold suavizado del LFO, la ranura ACT del motor saturaba a `$800000`. Fallo desde SC43.9, también en todas las RC publicadas desde RC2.
- `modesel.use_bluedim()`: el pad 23 de la fila de motores (secuenciador de efectos) apagado en `0x0F`; con `0x0A` parecía siempre encendido.

## Qué probar

MIDI 1 con el oscilador, página 5, Shift + K8: las siete formas suenan. Fila de motores: el pad 23 se distingue encendido de apagado.

## Pruebas en emulación

`emu_actfix_dsp.py`.
